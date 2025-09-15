"""Simple price extraction from web pages using JSON-LD and DOM fallback."""

import httpx
import extruct
from lxml import html
import re
from typing import Dict, Optional
from w3lib.html import get_base_url


class SkipException(Exception):
    """Exception to signal that a URL should be skipped."""
    pass


def fetch(url: str) -> str:
    """Fetch HTML content from URL with simple user agent."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.text


def extract_from_jsonld(html_content: str, url: str) -> Optional[Dict]:
    """Extract price from JSON-LD structured data."""
    try:
        base_url = get_base_url(html_content, url)
        data = extruct.extract(html_content, base_url=base_url)
        
        # Look for Product schema in JSON-LD
        jsonld_list = data.get('json-ld', [])
        for item in jsonld_list:
            if isinstance(item, dict):
                # Handle both single items and lists
                if item.get('@type') == 'Product':
                    return _extract_product_price(item)
                elif isinstance(item.get('@graph'), list):
                    for graph_item in item['@graph']:
                        if graph_item.get('@type') == 'Product':
                            return _extract_product_price(graph_item)
        
        return None
    except Exception:
        return None


def _extract_product_price(product: Dict) -> Optional[Dict]:
    """Extract price from a Product JSON-LD object."""
    offers = product.get('offers')
    if not offers:
        return None
    
    # Handle both single offer and list of offers
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    
    price = offers.get('price')
    currency = offers.get('priceCurrency')
    
    if price:
        try:
            price_float = float(str(price).replace(',', ''))
            return {
                'price': price_float,
                'currency': currency,
                'source': 'jsonld'
            }
        except (ValueError, TypeError):
            pass
    
    return None


def extract_from_dom(html_content: str) -> Optional[Dict]:
    """Extract price using DOM selectors as fallback."""
    try:
        tree = html.fromstring(html_content)
        
        # Try microdata first
        price_elem = tree.xpath('//*[@itemprop="price"]/@content')
        if price_elem:
            try:
                price = float(price_elem[0].replace(',', ''))
                return {'price': price, 'source': 'dom'}
            except (ValueError, TypeError):
                pass
        
        # Try Open Graph meta tags
        og_price = tree.xpath('//meta[@property="product:price:amount"]/@content')
        if og_price:
            try:
                price = float(og_price[0].replace(',', ''))
                currency = None
                og_currency = tree.xpath('//meta[@property="product:price:currency"]/@content')
                if og_currency:
                    currency = og_currency[0]
                return {'price': price, 'currency': currency, 'source': 'dom'}
            except (ValueError, TypeError):
                pass
        
        # Fallback: look for elements with "price" in class name
        price_elements = tree.xpath('//*[contains(@class, "price") and not(contains(@class, "compare"))]')
        for elem in price_elements:
            text = elem.text_content().strip()
            price_match = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
            if price_match:
                try:
                    price = float(price_match.group().replace(',', ''))
                    if price > 0:
                        return {'price': price, 'source': 'dom'}
                except (ValueError, TypeError):
                    continue
        
        return None
    except Exception:
        return None


def extract_price(url: str) -> Dict:
    """Main extraction function that tries JSON-LD first, then DOM fallback."""
    html_content = fetch(url)
    
    # Try JSON-LD first
    result = extract_from_jsonld(html_content, url)
    if result:
        return result
    
    # Fallback to DOM extraction
    result = extract_from_dom(html_content)
    if result:
        return result
    
    raise ValueError(f"Could not extract price from {url}")
