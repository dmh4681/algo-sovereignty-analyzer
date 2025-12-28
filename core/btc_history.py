"""
Bitcoin Price History Tracking

Stores historical snapshots of Bitcoin prices (Coinbase spot, goBTC, WBTC)
for arbitrage analysis and charting.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from .pricing import get_bitcoin_spot_price, get_gobtc_price, get_wbtc_price


# Database path (same directory as sovereignty history)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_PATH = os.path.join(DATA_DIR, 'btc_price_history.db')


@dataclass
class BTCPriceSnapshot:
    """Single point-in-time Bitcoin price snapshot."""
    timestamp: datetime
    spot_btc: float
    gobtc_price: float
    wbtc_price: Optional[float]
    gobtc_premium_pct: float
    wbtc_premium_pct: Optional[float]


class BTCPriceHistory:
    """Manages Bitcoin price history storage and retrieval."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database and create tables if needed."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS btc_price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    spot_btc REAL NOT NULL,
                    gobtc_price REAL NOT NULL,
                    wbtc_price REAL,
                    gobtc_premium_pct REAL NOT NULL,
                    wbtc_premium_pct REAL
                )
            ''')

            # Index for efficient time-range queries
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_btc_history_timestamp
                ON btc_price_history(timestamp)
            ''')

            conn.commit()

    def save_snapshot(self, snapshot: BTCPriceSnapshot) -> bool:
        """
        Save a price snapshot to the database.

        Returns True if saved, False if duplicate (within 10 minutes).
        """
        # Check for recent duplicate (within 10 minutes)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM btc_price_history
                WHERE timestamp > datetime('now', '-10 minutes')
            ''')
            if cursor.fetchone()[0] > 0:
                return False  # Skip duplicate

            conn.execute('''
                INSERT INTO btc_price_history
                (timestamp, spot_btc, gobtc_price, wbtc_price, gobtc_premium_pct, wbtc_premium_pct)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                snapshot.timestamp.isoformat(),
                snapshot.spot_btc,
                snapshot.gobtc_price,
                snapshot.wbtc_price,
                snapshot.gobtc_premium_pct,
                snapshot.wbtc_premium_pct
            ))
            conn.commit()
            return True

    def get_history(self, hours: int = 24) -> List[BTCPriceSnapshot]:
        """
        Get price history for the specified time range.

        Args:
            hours: Number of hours to look back (default 24)

        Returns:
            List of BTCPriceSnapshot objects, oldest first
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT timestamp, spot_btc, gobtc_price, wbtc_price,
                       gobtc_premium_pct, wbtc_premium_pct
                FROM btc_price_history
                WHERE timestamp > datetime('now', ?)
                ORDER BY timestamp ASC
            ''', (f'-{hours} hours',))

            results = []
            for row in cursor.fetchall():
                results.append(BTCPriceSnapshot(
                    timestamp=datetime.fromisoformat(row[0]),
                    spot_btc=row[1],
                    gobtc_price=row[2],
                    wbtc_price=row[3],
                    gobtc_premium_pct=row[4],
                    wbtc_premium_pct=row[5]
                ))
            return results

    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Calculate statistics for the time range.

        Returns dict with avg/min/max for each premium.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT
                    AVG(gobtc_premium_pct) as avg_gobtc,
                    MIN(gobtc_premium_pct) as min_gobtc,
                    MAX(gobtc_premium_pct) as max_gobtc,
                    AVG(wbtc_premium_pct) as avg_wbtc,
                    MIN(wbtc_premium_pct) as min_wbtc,
                    MAX(wbtc_premium_pct) as max_wbtc,
                    COUNT(*) as data_points
                FROM btc_price_history
                WHERE timestamp > datetime('now', ?)
            ''', (f'-{hours} hours',))

            row = cursor.fetchone()
            if row and row[6] > 0:
                return {
                    'gobtc': {
                        'avg_premium_pct': round(row[0], 2) if row[0] else 0,
                        'min_premium_pct': round(row[1], 2) if row[1] else 0,
                        'max_premium_pct': round(row[2], 2) if row[2] else 0,
                    },
                    'wbtc': {
                        'avg_premium_pct': round(row[3], 2) if row[3] else None,
                        'min_premium_pct': round(row[4], 2) if row[4] else None,
                        'max_premium_pct': round(row[5], 2) if row[5] else None,
                    },
                    'data_points': row[6],
                    'hours': hours
                }
            return {
                'gobtc': {'avg_premium_pct': 0, 'min_premium_pct': 0, 'max_premium_pct': 0},
                'wbtc': {'avg_premium_pct': None, 'min_premium_pct': None, 'max_premium_pct': None},
                'data_points': 0,
                'hours': hours
            }

    def cleanup_old_data(self, days: int = 30):
        """Remove data older than specified days."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                DELETE FROM btc_price_history
                WHERE timestamp < datetime('now', ?)
            ''', (f'-{days} days',))
            conn.commit()


def capture_btc_snapshot() -> Optional[BTCPriceSnapshot]:
    """
    Capture current Bitcoin prices and create a snapshot.

    Returns BTCPriceSnapshot if successful, None if prices unavailable.
    """
    spot_btc = get_bitcoin_spot_price()
    gobtc_price = get_gobtc_price()
    wbtc_price = get_wbtc_price()

    if not spot_btc or not gobtc_price or spot_btc <= 0:
        return None

    gobtc_premium_pct = ((gobtc_price - spot_btc) / spot_btc) * 100
    wbtc_premium_pct = None
    if wbtc_price and wbtc_price > 0:
        wbtc_premium_pct = ((wbtc_price - spot_btc) / spot_btc) * 100

    return BTCPriceSnapshot(
        timestamp=datetime.utcnow(),
        spot_btc=spot_btc,
        gobtc_price=gobtc_price,
        wbtc_price=wbtc_price,
        gobtc_premium_pct=gobtc_premium_pct,
        wbtc_premium_pct=wbtc_premium_pct
    )


def save_current_prices() -> bool:
    """
    Convenience function to capture and save current prices.

    Returns True if saved, False otherwise.
    """
    snapshot = capture_btc_snapshot()
    if snapshot:
        history = BTCPriceHistory()
        return history.save_snapshot(snapshot)
    return False


# Singleton instance
_btc_history: Optional[BTCPriceHistory] = None


def get_btc_history_manager() -> BTCPriceHistory:
    """Get or create the BTCPriceHistory singleton."""
    global _btc_history
    if _btc_history is None:
        _btc_history = BTCPriceHistory()
    return _btc_history
