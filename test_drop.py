#!/usr/bin/env python3
"""Test script to simulate a price drop and verify alert generation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.models import OfferSnapshot, ProductSpec
from src.storage import Storage
from src.engine import PriceEngine

def test_price_drop():
    """Test price drop detection by creating two snapshots."""
    # Initialize storage and engine
    storage = Storage("data/pricecheck.db")
    engine = PriceEngine(storage)
    
    # Create a product spec
    product_spec = ProductSpec(
        id="TEST_DROP",
        links=["https://example.com/product"],
        currency="CAD",
        thresholds={"min_abs": 10, "min_pct": 0.05}  # 5% threshold for testing
    )
    
    # Create first snapshot (higher price)
    snapshot1 = OfferSnapshot(
        product_id="TEST_DROP",
        retailer_id="example.com",
        url="https://example.com/product",
        price=100.0,
        currency="CAD",
        parse_source="test"
    )
    
    # Process first snapshot
    result1 = engine.process_snapshot(snapshot1, 10, 0.05)
    print(f"First snapshot: {snapshot1.price} CAD - Alert: {result1}")
    
    # Create second snapshot (lower price - should trigger alert)
    snapshot2 = OfferSnapshot(
        product_id="TEST_DROP",
        retailer_id="example.com",
        url="https://example.com/product",
        price=80.0,  # 20% drop, should trigger
        currency="CAD",
        parse_source="test"
    )
    
    # Process second snapshot
    result2 = engine.process_snapshot(snapshot2, 10, 0.05)
    print(f"Second snapshot: {snapshot2.price} CAD - Alert: {result2}")
    
    if result2:
        print(f"DROP DETECTED: {result2.reason}")
    else:
        print("No drop detected")

if __name__ == "__main__":
    test_price_drop()
