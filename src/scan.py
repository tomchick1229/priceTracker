#!/usr/bin/env python3
"""
End-to-end price scanning pipeline.

This script scans all products in the configuration file, checks for price drops
compared to previous scans stored in SQLite, and optionally sends email notifications
when drops are detected.

Usage:
    uv run src/scan.py               # Scan without email notifications (using uv)
    uv run src/scan.py --email      # Scan and send email alerts on drops
    python src/scan.py              # Alternative: using python directly
    python src/scan.py --config custom.yaml  # Use custom config file
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import load_products_config
from src.models import ProductSpec, OfferSnapshot, PriceEvent
from src.storage import Storage
from src.engine import PriceEngine
from src.adapter_generic import create_snapshot


def scan_product(product_spec: ProductSpec, storage: Storage, engine: PriceEngine, enable_email: bool = False) -> List[PriceEvent]:
    """
    Scan a single product across all its configured URLs.
    Finds the lowest price among all URLs and compares with last checked price.
    
    Args:
        product_spec: Product configuration
        storage: Storage instance for database operations
        engine: Price engine for drop detection
        enable_email: Whether to send email notifications
        
    Returns:
        List of price drop events detected
    """
    print(f"\n📦 Scanning product: {product_spec.id}")
    print(f"   URLs: {len(product_spec.links)}")
    
    snapshots = []
    valid_prices = []
    
    # First, collect all prices from all URLs
    for url in product_spec.links:
        try:
            print(f"   🔍 Checking: {url}")
            
            # Create price snapshot
            snapshot = create_snapshot(url, product_spec)
            print(f"      Price: ${snapshot.price:.2f} {snapshot.currency} from {snapshot.retailer_id}")
            
            # Store snapshot for later processing
            snapshots.append(snapshot)
            valid_prices.append(snapshot.price)
            
        except Exception as e:
            print(f"      ❌ Error scanning {url}: {e}")
            continue
    
    if not snapshots:
        print(f"   ❌ No valid prices found for {product_spec.id}")
        return []
    
    # Find the lowest price among all URLs
    lowest_price = min(valid_prices)
    lowest_snapshot = None
    
    # Find the snapshot with the lowest price
    for snapshot in snapshots:
        if snapshot.price == lowest_price:
            lowest_snapshot = snapshot
            break
    
    if not lowest_snapshot:
        print(f"   ❌ Could not determine lowest price snapshot for {product_spec.id}")
        return []
    
    print(f"   💰 Best price: ${lowest_price:.2f} {lowest_snapshot.currency} from {lowest_snapshot.retailer_id}")
    
    # Save all snapshots to database for historical tracking
    for snapshot in snapshots:
        storage.save_snapshot(snapshot)
    
    # Get thresholds
    thresholds = product_spec.thresholds or {"min_abs": 20, "min_pct": 0.08}
    min_abs = thresholds.get("min_abs", 20)
    min_pct = thresholds.get("min_pct", 0.08)
    
    # Check for price drop using the lowest price snapshot
    last_price = storage.get_last_price(product_spec.id)
    drop_event = None
    
    if last_price is not None:
        abs_drop = last_price - lowest_price
        pct_drop = abs_drop / last_price if last_price > 0 else 0
        
        print(f"   📊 Price comparison: ${last_price:.2f} → ${lowest_price:.2f}")
        
        # Check if both thresholds are met
        if abs_drop >= min_abs and pct_drop >= min_pct:
            # Check if we already alerted for this price recently
            if not storage.check_recent_alert(product_spec.id, lowest_price):
                reason = f"last {last_price:.2f} → {lowest_price:.2f} (-{pct_drop*100:.1f}%)"
                
                drop_event = PriceEvent(
                    product_id=product_spec.id,
                    retailer_id=lowest_snapshot.retailer_id,
                    event_type="drop",
                    old_price=last_price,
                    new_price=lowest_price,
                    pct_change=pct_drop,
                    reason=reason
                )
                
                # Save the alert to database
                storage.save_alert(drop_event)
                
                savings = abs_drop
                savings_pct = pct_drop * 100
                
                print(f"   🔥 PRICE DROP DETECTED!")
                print(f"      Previous: ${last_price:.2f}")
                print(f"      Current:  ${lowest_price:.2f}")
                print(f"      Savings:  ${savings:.2f} ({savings_pct:.1f}%)")
                
                # Send email if enabled and email agent is available
                if enable_email and engine.email_agent and engine.email_recipients:
                    try:
                        success = engine.email_agent.send_price_alert(
                            recipients=engine.email_recipients,
                            product_id=lowest_snapshot.product_id,
                            old_price=last_price,
                            new_price=lowest_price,
                            retailer=lowest_snapshot.retailer_id,
                            url=lowest_snapshot.url
                        )
                        if success:
                            print(f"      📧 Email alert sent to {len(engine.email_recipients)} recipients")
                        else:
                            print(f"      ❌ Failed to send email alert")
                    except Exception as e:
                        print(f"      ❌ Email error: {e}")
            else:
                print(f"   ⚠️  Price drop detected but already alerted recently")
        else:
            change = lowest_price - last_price
            if abs(change) > 0.01:
                change_str = f"(${change:+.2f})" if change != 0 else ""
                print(f"   📈 No significant drop. {change_str}")
            else:
                print(f"   ✅ Price unchanged from ${last_price:.2f}")
    else:
        print(f"   📝 First time tracking this product")
    
    return [drop_event] if drop_event else []


def main():
    """Main scanning pipeline."""
    parser = argparse.ArgumentParser(
        description="Price tracking scanner with optional email alerts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scan.py                     # Scan without email notifications
  python scan.py --email            # Scan and send email alerts
  python scan.py --config custom.yaml # Use custom config file
        """.strip()
    )
    
    parser.add_argument(
        "--config", "-c",
        default="config/products.yaml",
        help="Path to products configuration file (default: config/products.yaml)"
    )
    
    parser.add_argument(
        "--email", "-e",
        action="store_true",
        help="Send email notifications when price drops are detected"
    )
    
    parser.add_argument(
        "--recipients", "-r",
        nargs="+",
        help="Email recipients (overrides environment settings)"
    )
    
    parser.add_argument(
        "--db",
        default="data/pricecheck.db",
        help="SQLite database path (default: data/pricecheck.db)"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print("🔍 Price Tracker Scanner")
    print("=" * 50)
    print(f"Config: {args.config}")
    print(f"Database: {args.db}")
    print(f"Email alerts: {'ENABLED' if args.email else 'DISABLED'}")
    
    # Ensure database directory exists
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"✅ Database directory ensured: {db_path.parent}")
    
    # Load configuration
    try:
        products = load_products_config(args.config)
        print(f"Loaded {len(products)} products")
    except FileNotFoundError:
        print(f"❌ Config file not found: {args.config}")
        return 1
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return 1
    
    if not products:
        print("⚠️  No products configured")
        return 0
    
    # Initialize storage
    try:
        storage = Storage(args.db)
        print(f"✅ Database initialized: {args.db}")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return 1
    
    # Determine email recipients
    email_recipients = []
    if args.email:
        if args.recipients:
            email_recipients = args.recipients
        else:
            # Try to get from environment
            email_env = os.getenv('EMAIL_RECIPIENTS')
            if email_env:
                email_recipients = [email.strip() for email in email_env.split(',')]
            else:
                print("⚠️  No email recipients specified. Use --recipients or set EMAIL_RECIPIENTS environment variable.")
                print("   Continuing without email notifications...")
                args.email = False
    
    if args.email and email_recipients:
        print(f"📧 Email notifications will be sent to: {', '.join(email_recipients)}")
    
    # Initialize price engine
    try:
        engine = PriceEngine(storage, email_recipients if args.email else [])
        print("✅ Price engine initialized")
        
        # Test email connection if enabled
        if args.email and engine.email_agent:
            if engine.email_agent.test_connection():
                print("✅ Email connection verified")
            else:
                print("❌ Email connection failed - continuing without email alerts")
                args.email = False
                
    except Exception as e:
        print(f"❌ Engine initialization error: {e}")
        if args.email:
            print("   Continuing without email notifications...")
            args.email = False
        engine = PriceEngine(storage, [])
    
    # Scan all products
    print("\n🚀 Starting price scan...")
    total_drops = 0
    
    for i, product in enumerate(products, 1):
        print(f"\n[{i}/{len(products)}] ", end="")
        try:
            drops = scan_product(product, storage, engine, args.email)
            total_drops += len(drops)
        except Exception as e:
            print(f"❌ Failed to scan {product.id}: {e}")
            continue
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🏁 Scan complete!")
    print(f"   Products scanned: {len(products)}")
    print(f"   Price drops detected: {total_drops}")
    
    if total_drops > 0:
        print(f"   🔥 {total_drops} price drop(s) found!")
        if args.email and email_recipients:
            print(f"   📧 Email alerts sent to {len(email_recipients)} recipients")
    else:
        print("   💤 No price drops detected")
    
    return 0


if __name__ == "__main__":
    exit(main())