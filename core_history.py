"""
Historical tracking for sovereignty snapshots.
Stores wallet analysis history in SQLite for progress tracking.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class Snapshot:
    """A point-in-time sovereignty snapshot."""
    id: Optional[int]
    address: str
    timestamp: datetime
    sovereignty_ratio: float
    sovereignty_status: str
    hard_money_usd: float
    total_portfolio_usd: float
    hard_money_pct: float
    algo_balance: float
    annual_expenses: float
    asset_breakdown: dict


@dataclass
class ProgressMetrics:
    """Progress metrics calculated from historical data."""
    current_ratio: float
    previous_ratio: Optional[float]  # 30 days ago
    change_absolute: Optional[float]
    change_pct: Optional[float]
    trend: str  # "improving", "declining", "stable", "new"
    days_tracked: int
    snapshots_count: int
    projected_next_status: Optional[dict]  # {status, ratio_needed, projected_date}


@dataclass
class AllTimeStats:
    """All-time statistics for an address."""
    high: float
    low: float
    average: float
    first_tracked: datetime
    last_tracked: datetime


class SovereigntyHistory:
    """
    Manages historical sovereignty snapshots using SQLite.
    
    Usage:
        history = SovereigntyHistory()
        history.save_snapshot(address, analysis_result)
        progress = history.get_progress(address)
    """
    
    # Status thresholds for projections
    STATUS_THRESHOLDS = [
        (1.0, "Fragile"),
        (3.0, "Robust"),
        (6.0, "Antifragile"),
        (20.0, "Generationally Sovereign"),
    ]
    
    def __init__(self, db_path: str = "data/sovereignty_history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sovereignty_ratio REAL,
                    sovereignty_status TEXT,
                    hard_money_usd REAL,
                    total_portfolio_usd REAL,
                    hard_money_pct REAL,
                    algo_balance REAL,
                    annual_expenses REAL,
                    asset_breakdown TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_address_timestamp 
                ON snapshots(address, timestamp DESC)
            """)
            conn.commit()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def save_snapshot(self, address: str, analysis_result: dict) -> Optional[int]:
        """
        Save analysis result as a historical snapshot.
        
        Args:
            address: Algorand wallet address
            analysis_result: Full analysis response from analyzer
            
        Returns:
            Snapshot ID if saved, None if deduplicated (too recent)
        """
        # Check for recent snapshot (dedupe within 1 hour)
        with self._get_connection() as conn:
            recent = conn.execute("""
                SELECT id FROM snapshots 
                WHERE address = ? 
                AND timestamp > datetime('now', '-1 hour')
                ORDER BY timestamp DESC LIMIT 1
            """, (address,)).fetchone()
            
            if recent:
                return None  # Skip - too recent
            
            # Extract data from analysis result
            sovereignty = analysis_result.get("sovereignty", {})
            summary = analysis_result.get("summary", {})
            
            # Calculate hard money percentage
            hard_money_usd = sovereignty.get("hard_money_usd", 0)
            total_usd = sovereignty.get("portfolio_usd", 0)
            hard_money_pct = (hard_money_usd / total_usd * 100) if total_usd > 0 else 0
            
            cursor = conn.execute("""
                INSERT INTO snapshots (
                    address, sovereignty_ratio, sovereignty_status,
                    hard_money_usd, total_portfolio_usd, hard_money_pct,
                    algo_balance, annual_expenses, asset_breakdown
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                address,
                sovereignty.get("sovereignty_ratio", 0),
                sovereignty.get("sovereignty_status", "Unknown"),
                hard_money_usd,
                total_usd,
                hard_money_pct,
                summary.get("total_algo", 0),
                sovereignty.get("annual_fixed_expenses", 0),
                json.dumps(analysis_result.get("assets", {}))
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_history(self, address: str, days: int = 90) -> list[dict]:
        """
        Get historical snapshots for an address.
        
        Args:
            address: Algorand wallet address
            days: Number of days of history (default 90, max 365)
            
        Returns:
            List of snapshot dictionaries, newest first
        """
        days = min(days, 365)  # Cap at 1 year
        
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM snapshots
                WHERE address = ?
                AND timestamp > datetime('now', ?)
                ORDER BY timestamp DESC
            """, (address, f'-{days} days')).fetchall()
            
            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "sovereignty_ratio": row["sovereignty_ratio"],
                    "sovereignty_status": row["sovereignty_status"],
                    "hard_money_usd": row["hard_money_usd"],
                    "total_portfolio_usd": row["total_portfolio_usd"],
                    "hard_money_pct": row["hard_money_pct"],
                    "algo_balance": row["algo_balance"],
                }
                for row in rows
            ]
    
    def get_progress(self, address: str) -> ProgressMetrics:
        """
        Calculate progress metrics for an address.
        
        Returns:
            ProgressMetrics with trend analysis and projections
        """
        with self._get_connection() as conn:
            # Get current (most recent) snapshot
            current = conn.execute("""
                SELECT * FROM snapshots
                WHERE address = ?
                ORDER BY timestamp DESC LIMIT 1
            """, (address,)).fetchone()
            
            if not current:
                return ProgressMetrics(
                    current_ratio=0,
                    previous_ratio=None,
                    change_absolute=None,
                    change_pct=None,
                    trend="new",
                    days_tracked=0,
                    snapshots_count=0,
                    projected_next_status=None
                )
            
            # Get snapshot from ~30 days ago
            previous = conn.execute("""
                SELECT * FROM snapshots
                WHERE address = ?
                AND timestamp < datetime('now', '-25 days')
                ORDER BY timestamp DESC LIMIT 1
            """, (address,)).fetchone()
            
            # Get total count and first snapshot
            stats = conn.execute("""
                SELECT 
                    COUNT(*) as count,
                    MIN(timestamp) as first_ts,
                    MAX(timestamp) as last_ts
                FROM snapshots WHERE address = ?
            """, (address,)).fetchone()
            
            current_ratio = current["sovereignty_ratio"]
            previous_ratio = previous["sovereignty_ratio"] if previous else None
            
            # Calculate change
            if previous_ratio is not None:
                change_absolute = current_ratio - previous_ratio
                change_pct = (change_absolute / previous_ratio * 100) if previous_ratio > 0 else 0
                
                if change_pct > 5:
                    trend = "improving"
                elif change_pct < -5:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                change_absolute = None
                change_pct = None
                trend = "new" if stats["count"] == 1 else "stable"
            
            # Calculate days tracked
            if stats["first_ts"]:
                first_date = datetime.fromisoformat(stats["first_ts"].replace('Z', '+00:00') if 'Z' in stats["first_ts"] else stats["first_ts"])
                days_tracked = (datetime.now() - first_date).days
            else:
                days_tracked = 0
            
            # Project next status if improving
            projected_next_status = None
            if trend == "improving" and change_absolute and change_absolute > 0:
                next_threshold = self._get_next_status_threshold(current_ratio)
                if next_threshold:
                    ratio_needed, status_name = next_threshold
                    gap = ratio_needed - current_ratio
                    # Project based on 30-day rate
                    days_to_reach = int(gap / change_absolute * 30) if change_absolute > 0 else None
                    if days_to_reach and days_to_reach < 365:
                        projected_date = datetime.now() + timedelta(days=days_to_reach)
                        projected_next_status = {
                            "status": status_name,
                            "ratio_needed": ratio_needed,
                            "projected_date": projected_date.strftime("%Y-%m-%d")
                        }
            
            return ProgressMetrics(
                current_ratio=current_ratio,
                previous_ratio=previous_ratio,
                change_absolute=round(change_absolute, 2) if change_absolute else None,
                change_pct=round(change_pct, 1) if change_pct else None,
                trend=trend,
                days_tracked=days_tracked,
                snapshots_count=stats["count"],
                projected_next_status=projected_next_status
            )
    
    def _get_next_status_threshold(self, current_ratio: float) -> Optional[tuple]:
        """Get the next status threshold above current ratio."""
        for threshold, status in self.STATUS_THRESHOLDS:
            if current_ratio < threshold:
                return (threshold, status)
        return None
    
    def get_all_time_stats(self, address: str) -> Optional[AllTimeStats]:
        """Get all-time high, low, average for an address."""
        with self._get_connection() as conn:
            stats = conn.execute("""
                SELECT 
                    MAX(sovereignty_ratio) as high,
                    MIN(sovereignty_ratio) as low,
                    AVG(sovereignty_ratio) as average,
                    MIN(timestamp) as first_ts,
                    MAX(timestamp) as last_ts
                FROM snapshots WHERE address = ?
            """, (address,)).fetchone()
            
            if not stats or stats["high"] is None:
                return None
            
            return AllTimeStats(
                high=round(stats["high"], 2),
                low=round(stats["low"], 2),
                average=round(stats["average"], 2),
                first_tracked=stats["first_ts"],
                last_tracked=stats["last_ts"]
            )
    
    def delete_history(self, address: str) -> int:
        """Delete all history for an address. Returns count deleted."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM snapshots WHERE address = ?",
                (address,)
            )
            conn.commit()
            return cursor.rowcount
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """Remove snapshots older than N days. Returns count deleted."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM snapshots 
                WHERE timestamp < datetime('now', ?)
            """, (f'-{days_to_keep} days',))
            conn.commit()
            return cursor.rowcount


# Convenience function for quick access
_default_history: Optional[SovereigntyHistory] = None

def get_history_tracker() -> SovereigntyHistory:
    """Get the default history tracker instance."""
    global _default_history
    if _default_history is None:
        _default_history = SovereigntyHistory()
    return _default_history


if __name__ == "__main__":
    # Quick test
    history = SovereigntyHistory(db_path="data/test_history.db")
    
    # Fake analysis result for testing
    test_result = {
        "sovereignty": {
            "sovereignty_ratio": 2.5,
            "sovereignty_status": "Fragile 🔴",
            "hard_money_usd": 100000,
            "portfolio_usd": 125000,
            "annual_fixed_expenses": 48000
        },
        "summary": {
            "total_algo": 50000
        },
        "assets": {}
    }
    
    # Save a snapshot
    snapshot_id = history.save_snapshot("TEST_ADDRESS_123", test_result)
    print(f"Saved snapshot: {snapshot_id}")
    
    # Get progress
    progress = history.get_progress("TEST_ADDRESS_123")
    print(f"Progress: {progress}")
    
    # Get history
    hist = history.get_history("TEST_ADDRESS_123")
    print(f"History entries: {len(hist)}")
