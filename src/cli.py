#!/usr/bin/env python3
"""CLI interface for price tracking system."""

import argparse
import sys
from urllib.parse import urlparse
from pathlib import Path

# Add the project root to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import load_products_config
from src.storage import Storage
from src.engine import PriceEngine
from src.extract_simple import SkipException
from src.adapter_generic import create_snapshot
from src.adapter_canadacomputers import create_canadacomputers_snapshot
from src.adapter_amazon_stub import create_amazon_snapshot


def select_adapter(url: str):
    """Select appropriate adapter based on URL domain."""
    parsed_url = urlparse(url)
    host = parsed_url.netloc.lower()
    
    if 'canadacomputers.com' in host:
        return create_canadacomputers_snapshot
    elif 'amazon.ca' in host:
        return create_amazon_snapshot
    else:
        return create_snapshot


def cmd_list(args):
    """List products from config."""
    try:
        products = load_products_config(args.config)
        print(f"Found {len(products)} products:")
        for product in products:
            print(f"  {product.id}: {len(product.links)} links")
            for link in product.links:
                print(f"    - {link}")
    except Exception as e:
        print(f"Error loading config: {e}")
        return 1
    return 0


def cmd_test_url(args):
    """Test URL extraction."""
    try:
        # Create a dummy product spec for testing
        from src.models import ProductSpec
        product_spec = ProductSpec(
            id="test",
            links=[args.url],
            currency=args.currency
        )
        
        adapter = select_adapter(args.url)
        snapshot = adapter(args.url, product_spec)
        
        print(f"[OK] fetched url={args.url} price={snapshot.price} currency={snapshot.currency} src={snapshot.parse_source}")
        if snapshot.list_price:
            print(f"  list_price={snapshot.list_price}")
        if snapshot.in_stock is not None:
            print(f"  in_stock={snapshot.in_stock}")
        
        return 0
    except SkipException as e:
        print(f"[SKIP] {e}")
        return 0
    except Exception as e:
        print(f"[ERROR] Failed to extract from {args.url}: {e}")
        return 1


def cmd_scan(args):
    """Scan all products for price changes."""
    try:
        products = load_products_config(args.config)
        storage = Storage(args.db)
        engine = PriceEngine(storage, email_recipients=args.email_recipients)
        
        for product in products:
            thresholds = product.thresholds or {"min_abs": 20, "min_pct": 0.08}
            min_abs = thresholds.get("min_abs", 20)
            min_pct = thresholds.get("min_pct", 0.08)
            
            for link in product.links:
                try:
                    adapter = select_adapter(link)
                    snapshot = adapter(link, product)
                    
                    print(f"[OK] fetched url={link} price={snapshot.price} src={snapshot.parse_source}")
                    
                    # Process snapshot and check for drops
                    drop_event = engine.process_snapshot(snapshot, min_abs, min_pct)
                    
                    if drop_event:
                        print(f"[DROP] {product.id} {snapshot.retailer_id} {snapshot.price} {drop_event.reason}")
                
                except SkipException:
                    # Already printed warning in adapter
                    continue
                except Exception as e:
                    print(f"[ERROR] Failed to process {link}: {e}")
                    continue
        
        # Print summary at the end
        print("\n" + "="*60)
        print("PRICE SUMMARY")
        print("="*60)
        print(f"{'Product':<20} {'Lowest Seen':<15} {'Current Price':<15}")
        print("-" * 60)
        
        summary = storage.get_all_products_summary()
        for item in summary:
            product_id = item['product_id']
            lowest = f"${item['lowest_price']:.2f}" if item['lowest_price'] else "N/A"
            current = f"${item['current_price']:.2f}" if item['current_price'] else "N/A"
            print(f"{product_id:<20} {lowest:<15} {current:<15}")
        
        if not summary:
            print("No price data available yet.")
        
        print("="*60)
        
        return 0
    except Exception as e:
        print(f"Error during scan: {e}")
        return 1


def cmd_history(args):
    """Show price history for a product."""
    try:
        storage = Storage(args.db)
        snapshots = storage.get_snapshots_history(args.product_id, args.limit)
        
        if not snapshots:
            print(f"No history found for product: {args.product_id}")
            return 1
        
        print(f"Price history for {args.product_id} (latest {len(snapshots)} entries):")
        for snapshot in snapshots:
            print(f"  {snapshot['ts']} | {snapshot['price']} {snapshot['currency']} | {snapshot['parse_source']} | {snapshot['retailer_id']}")
        
        return 0
    except Exception as e:
        print(f"Error retrieving history: {e}")
        return 1


def cmd_test_email(args):
    """Test email configuration by sending a test email."""
    try:
        from src.email_agent import EmailAgent
        
        agent = EmailAgent()
        
        # Test connection first
        print("Testing email connection...")
        if not agent.test_connection():
            return 1
        
        # Send test email
        print(f"Sending test email to {args.recipient}...")
        success = agent.send_email(
            recipients=[args.recipient],
            content="This is a test email from the Price Tracker CLI. If you receive this, your email configuration is working correctly!",
            title="Price Tracker - CLI Email Test"
        )
        
        if success:
            print("✅ Test email sent successfully!")
            return 0
        else:
            print("❌ Failed to send test email!")
            return 1
            
    except ImportError:
        print("❌ Email agent not available. Make sure python-dotenv is installed.")
        return 1
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Price tracking CLI")
    parser.add_argument('--config', default='config/products.yaml', help='Config file path')
    parser.add_argument('--db', default='data/pricecheck.db', help='Database file path')
    parser.add_argument('--email-recipients', nargs='*', help='Email addresses for price alerts')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List products from config')
    
    # Test URL command
    test_parser = subparsers.add_parser('test-url', help='Test URL extraction')
    test_parser.add_argument('url', help='URL to test')
    test_parser.add_argument('--currency', default='CAD', help='Default currency')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan all products for changes')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show price history')
    history_parser.add_argument('product_id', help='Product ID to show history for')
    history_parser.add_argument('--limit', type=int, default=20, help='Number of entries to show')
    
    # Email test command
    email_parser = subparsers.add_parser('test-email', help='Test email configuration')
    email_parser.add_argument('recipient', help='Email address to send test to')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        return cmd_list(args)
    elif args.command == 'test-url':
        return cmd_test_url(args)
    elif args.command == 'scan':
        return cmd_scan(args)
    elif args.command == 'history':
        return cmd_history(args)
    elif args.command == 'test-email':
        return cmd_test_email(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
