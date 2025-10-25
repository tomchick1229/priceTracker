"""Generic adapter for price extraction from any retailer."""

from urllib.parse import urlparse
import hashlib
from src.models import OfferSnapshot, ProductSpec
from src.extract_simple import extract_price


def create_snapshot(url: str, product_spec: ProductSpec) -> OfferSnapshot:
    """Extract price and create snapshot for generic retailer."""
    # Determine retailer ID from URL
    parsed_url = urlparse(url)
    retailer_id = parsed_url.netloc.lower()
    if retailer_id.startswith('www.'):
        retailer_id = retailer_id[4:]
    
    # Extract price data
    price_data = extract_price(url)
    
    # Use detected currency or fall back to product's preferred currency
    currency = price_data.get('currency') or product_spec.currency or 'CAD'
    if currency == "USD":
        currency = "CAD"  # Force to CAD for generic adapter
        price_data['price'] = price_data['price'] * 1.4
    
    # Create snapshot
    snapshot = OfferSnapshot(
        product_id=product_spec.id,
        retailer_id=retailer_id,
        url=url,
        price=price_data['price'],
        currency=currency,
        list_price=price_data.get('list_price'),
        in_stock=price_data.get('in_stock'),
        parse_source=price_data['source']
    )
    
    # Generate signature
    sig_data = f"{url}|{snapshot.price}|{currency}|{snapshot.list_price or ''}"
    snapshot.raw_signature = hashlib.sha1(sig_data.encode()).hexdigest()
    
    return snapshot
