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


def scan_product(product_spec: ProductSpec, storage: Storage, engine: PriceEngine, enable_email: bool = False) -> dict:
    """
    Scan a single product across all its configured URLs.
    Finds the lowest price among all URLs and compares with last checked price.
    
    Args:
        product_spec: Product configuration
        storage: Storage instance for database operations
        engine: Price engine for drop detection
        enable_email: Whether to send email notifications
        
    Returns:
        Dictionary summarizing the scanned product
    """
    # print(f"{product_spec = }")
    summary = {
        "product_id": product_spec.id,
        "urls": product_spec.links,
        "best_price": None,
        "previous_price": None,
        "price_drop": None,
        "savings": None,
        "savings_pct": None,
        "best_url": None,
        "owner": product_spec.owner,
        "snapshots": []
    }
    
    print(f"\n📦 Scanning product: {product_spec.id}")
    print(f"   URLs: {len(product_spec.links)}")
    
    snapshots = []
    snapshot_snippets = []
    best_deal = None  # Track the best price drop found
    
    # Check each URL individually
    for url in product_spec.links:
        try:
            print(f"   🔍 Checking: {url}")
            
            # Create price snapshot
            snapshot = create_snapshot(url, product_spec)
            print(f"      Price: ${snapshot.price:.2f} {snapshot.currency} from {snapshot.retailer_id}")

            snapshot_snippet = {
                "url": snapshot.url,
                "price": snapshot.price,
                "currency": snapshot.currency,
                "retailer_id": snapshot.retailer_id
            }
            
            # Store snapshot for historical tracking
            storage.save_snapshot(snapshot)
            snapshots.append(snapshot)
            snapshot_snippets.append(snapshot_snippet)

            # Get the last price for this specific URL
            last_price = storage.get_top_price(product_spec.id, snapshot.retailer_id)
            
            if last_price is not None:
                abs_drop = last_price - snapshot.price
                pct_drop = abs_drop / last_price if last_price > 0 else 0
                
                print(f"      📊 Previous price for this URL: ${last_price:.2f}")
                print(f"      📊 Current price: ${snapshot.price:.2f}")
                
                # Update best deal if this is better than what we've seen
                if best_deal is None or (abs_drop > best_deal['abs_drop'] and pct_drop > best_deal['pct_drop']):
                    best_deal = {
                        'snapshot': snapshot,
                        'last_price': last_price,
                        'abs_drop': abs_drop,
                        'pct_drop': pct_drop
                    }

        except Exception as e:
            print(f"      ❌ Error scanning {url}: {e}")
            continue
    
    if not snapshots:
        print(f"   ❌ No valid prices found for {product_spec.id}")
        return summary

    summary["snapshots"] = snapshot_snippets
    
    # If we found no price drops, return early
    if not best_deal:
        print(f"   📝 No previous prices to compare against")
        return summary

    # Now we know we have a valid best_deal
    lowest_snapshot = best_deal['snapshot']
    last_price = best_deal['last_price']
    lowest_price = lowest_snapshot.price
    
    print(f"   💰 Best price drop found at {lowest_snapshot.retailer_id}")
    print(f"      Previous: ${last_price:.2f}")
    print(f"      Current:  ${lowest_price:.2f}")
    
    # Get thresholds
    thresholds = product_spec.thresholds or {"min_abs": 20, "min_pct": 0.15}
    min_abs = thresholds.get("min_abs", 20)
    min_pct = thresholds.get("min_pct", 0.15)

    abs_drop = last_price - lowest_price
    pct_drop = abs_drop / last_price if last_price > 0 else 0


    if last_price is not None:
        abs_drop = last_price - lowest_price
        pct_drop = abs_drop / last_price if last_price > 0 else 0
        
        print(f"   📊 Price comparison: ${last_price:.2f} → ${lowest_price:.2f}")
        
        # Check if both thresholds are met
        if abs_drop >= min_abs and pct_drop >= min_pct:
            # Check if we already alerted for this price recently
            if not storage.check_recent_alert(product_spec.id, lowest_price):
                summary.update({
                    "best_url": lowest_snapshot.url,
                    "previous_price": round(last_price, 2),
                    "best_price": round(lowest_price, 2),
                    "price_drop": round(abs_drop, 2),
                    "savings": round(abs_drop, 2),
                    "savings_pct": round(pct_drop * 100, 2)
                })
                
                print(f"   🔥 PRICE DROP DETECTED!")
                print(f"      Previous: ${last_price:.2f}")
                print(f"      Current:  ${lowest_price:.2f}")
                print(f"      Savings:  ${abs_drop:.2f} ({pct_drop * 100:.1f}%)")
                
                # Send email if enabled and email agent is available
                # (Email sending logic can be added here)
        else:
            change = lowest_price - last_price
            if abs(change) > 0.01:
                change_str = f"(${change:+.2f})" if change != 0 else ""
                print(f"   📈 No significant drop. {change_str}")
            else:
                print(f"   ✅ Price unchanged from ${last_price:.2f}")
    else:
        print(f"   📝 First time tracking this product")
    
    return summary


def ensure_database_directory(db_path: Path) -> None:
    """Ensure the database directory exists."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"✅ Database directory ensured: {db_path.parent}")

def load_configuration(config_path: str) -> List[ProductSpec]:
    """Load product configuration from the specified file."""
    try:
        products = load_products_config(config_path)
        print(f"Loaded {len(products)} products")
        return products
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)

def initialize_storage(db_path: str) -> Storage:
    """Initialize the storage with the given database path."""
    try:
        storage = Storage(db_path)
        print(f"✅ Database initialized: {db_path}")
        return storage
    except Exception as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)

def determine_email_recipients(args: argparse.Namespace) -> List[str]:
    """Determine email recipients based on command line arguments or environment variables."""
    email_recipients = []
    if args.email:
        if args.recipients:
            email_recipients = args.recipients
        else:
            email_env = os.getenv('ADMIN_EMAIL_LIST') if args.test else os.getenv('EMAIL_RECIPIENTS')
            if email_env:
                email_recipients = [email.strip() for email in email_env.split(',')]
            else:
                print("⚠️  No email recipients specified. Use --recipients or set EMAIL_RECIPIENTS environment variable.")
                print("   Continuing without email notifications...")
                args.email = False

    if args.email and email_recipients:
        print(f"📧 Email notifications will be sent to: {', '.join(email_recipients)}")
    
    return email_recipients

def initialize_price_engine(storage: Storage, email_recipients: List[str], args: argparse.Namespace) -> PriceEngine:
    """Initialize the price engine and verify email connection if enabled."""
    try:
        engine = PriceEngine(storage, email_recipients if args.email else [])
        print("✅ Price engine initialized")
        
        if args.email and engine.email_agent:
            if engine.email_agent.test_connection():
                print("✅ Email connection verified")
            else:
                print("❌ Email connection failed - continuing without email alerts")
                args.email = False
                
        return engine
    except Exception as e:
        print(f"❌ Engine initialization error: {e}")
        if args.email:
            print("   Continuing without email notifications...")
            args.email = False
        return PriceEngine(storage, [])

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
    
    parser.add_argument(
        "--test",
        action="store_true",
        default=False,
        help="Run in test mode"
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Send a summary email after the scan"
    )

    args = parser.parse_args()
    
    # Print banner
    print("🔍 Price Tracker Scanner")
    print("=" * 50)
    print(f"Config: {args.config}")
    print(f"Database: {args.db}")
    print(f"Email alerts: {'ENABLED' if args.email else 'DISABLED'}")
    
    db_path = Path(args.db)
    ensure_database_directory(db_path)

    products = load_configuration(args.config)
    if not products:
        print("⚠️  No products configured")
        return 0

    storage = initialize_storage(args.db)
    email_recipients = determine_email_recipients(args)
    engine = initialize_price_engine(storage, email_recipients, args)

    email_recipients = "general" if not args.test else "admin"

    # Scan all products
    print("\n🚀 Starting price scan...")
    total_drops = 0
    product_summaries = []

    for i, product in enumerate(products, 1):
        print(f"\n[{i}/{len(products)}] ", end="")
        try:
            if args.test and i==3: break # DEBUG
            summary = scan_product(product, storage, engine, args.email)
            product_summaries.append(summary)

            # Count this as a detected drop when price_drop is present and positive
            price_drop = summary.get("price_drop")
            if price_drop is not None and price_drop > 0:
                total_drops += 1
        except Exception as e:
            print(f"❌ Failed to scan {product.id}: {e}")
            continue
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🏁 Scan complete!")
    print(f"   Products scanned: {len(products)}")
    print(f"   Price drops detected: {total_drops}")

    if (args.test or args.summary) and not args.email:
        print("   🧪 Running in test mode")
        
        print("\nProduct summary:")
        for product in product_summaries:
            print(f"• {product['product_id']}:")
            for key, value in product.items():
                print(f"\t- {key}: {value}")
            
        engine.email_agent.send_template_email(
            type="summary",
            recipients="admin",
            summary=product_summaries,
        )
        
        if total_drops >0:
            print("Price drop detected!")
        else:
            print("No price drops detected.")

    if args.email:
        if total_drops > 0:
            engine.email_agent.send_template_email(
                type="positive",
                recipients=email_recipients,
                summary=product_summaries,
            )
        else:
            engine.email_agent.send_template_email(
                type="negative",
                recipients=email_recipients,
                summary=product_summaries,
            )
    else:
        print("📧 Email notifications are disabled")

    # if total_drops > 0:
    #     print(f"   🔥 {total_drops} price drop(s) found!")
    # else:
    #     print("   💤 No price drops detected")
    
    return 0


if __name__ == "__main__":
    exit(main())
    
# 0 15 * * * /bin/bash -c 'cd /home/tomchick/priceTracker && sudo mkdir -p /log  && uv run src/scan.py --email >> /log/$(date +\%Y\%m\%d).log 2>&1'