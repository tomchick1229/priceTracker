"""SQLite storage for snapshots and alerts."""

import sqlite3
from typing import List, Optional
from pathlib import Path
from src.models import OfferSnapshot, PriceEvent


class Storage:
    """SQLite storage for price tracking data."""
    
    def __init__(self, db_path: str = "data/pricecheck.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables and indexes."""
        with sqlite3.connect(self.db_path) as conn:
            # Create snapshots table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    retailer_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    price REAL NOT NULL,
                    currency TEXT NOT NULL,
                    list_price REAL,
                    in_stock INTEGER,
                    parse_source TEXT NOT NULL,
                    raw_signature TEXT NOT NULL
                )
            """)
            
            # Create alerts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    retailer_id TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    old_price REAL NOT NULL,
                    new_price REAL NOT NULL,
                    pct_change REAL NOT NULL,
                    reason TEXT NOT NULL
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_product_ts ON snapshots(product_id, ts)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_product_ts ON alerts(product_id, ts)")
    
    def save_snapshot(self, snapshot: OfferSnapshot) -> int:
        """Save a price snapshot and return the row ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO snapshots (
                    product_id, retailer_id, url, ts, price, currency,
                    list_price, in_stock, parse_source, raw_signature
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.product_id,
                snapshot.retailer_id,
                snapshot.url,
                snapshot.ts,
                snapshot.price,
                snapshot.currency,
                snapshot.list_price,
                snapshot.in_stock,
                snapshot.parse_source,
                snapshot.raw_signature
            ))
            return cursor.lastrowid or 0
    
    def save_alert(self, alert: PriceEvent) -> int:
        """Save a price alert and return the row ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO alerts (
                    product_id, retailer_id, ts, event_type,
                    old_price, new_price, pct_change, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.product_id,
                alert.retailer_id,
                alert.ts,
                alert.event_type,
                alert.old_price,
                alert.new_price,
                alert.pct_change,
                alert.reason
            ))
            return cursor.lastrowid or 0
    
    def get_last_price(self, product_id: str) -> Optional[float]:
        """Get the most recent price for a product (excluding current run)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT price FROM snapshots 
                WHERE product_id = ? 
                ORDER BY ts DESC 
                LIMIT 1 OFFSET 1
            """, (product_id,))
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_snapshots_history(self, product_id: str, limit: int = 20) -> List[dict]:
        """Get recent snapshots for a product."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT ts, price, currency, parse_source, retailer_id, url
                FROM snapshots 
                WHERE product_id = ? 
                ORDER BY ts DESC 
                LIMIT ?
            """, (product_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def check_recent_alert(self, product_id: str, new_price: float, hours: int = 12) -> bool:
        """Check if we already alerted for this price recently."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM alerts 
                WHERE product_id = ? 
                AND new_price = ? 
                AND datetime(ts) > datetime('now', '-{} hours')
            """.format(hours), (product_id, new_price))
            count = cursor.fetchone()[0]
            return count > 0
    
    def get_lowest_price(self, product_id: str) -> Optional[float]:
        """Get the lowest price ever seen for a product."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT MIN(price) FROM snapshots 
                WHERE product_id = ?
            """, (product_id,))
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else None
    
    def get_current_price(self, product_id: str) -> Optional[float]:
        """Get the most recent price for a product."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT price FROM snapshots 
                WHERE product_id = ? 
                ORDER BY ts DESC 
                LIMIT 1
            """, (product_id,))
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_all_products_summary(self) -> List[dict]:
        """Get summary of all products with lowest and current prices."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    product_id,
                    MIN(price) as lowest_price,
                    MAX(ts) as latest_ts
                FROM snapshots 
                GROUP BY product_id
            """)
            products = []
            for row in cursor.fetchall():
                # Get the current (most recent) price
                cursor2 = conn.execute("""
                    SELECT price FROM snapshots 
                    WHERE product_id = ? AND ts = ?
                """, (row['product_id'], row['latest_ts']))
                current_row = cursor2.fetchone()
                current_price = current_row[0] if current_row else None
                
                products.append({
                    'product_id': row['product_id'],
                    'lowest_price': row['lowest_price'],
                    'current_price': current_price
                })
            return products
