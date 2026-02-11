"""
SQLite persistence layer for sovereignty analysis caching.

Provides disk-backed storage with longer TTLs than the in-memory cache,
acting as a second-level cache that survives process restarts.

Storage location: data/sovereignty_cache.db
"""

import hashlib
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from core.history import get_data_directory

logger = logging.getLogger("core.persistence")


class PersistenceDB:
    """SQLite-backed persistence for analysis results and price data."""

    # Default TTLs (seconds)
    ANALYSIS_TTL = 3600       # 1 hour (vs 15 min in-memory)
    PRICE_TTL = 300           # 5 minutes

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = get_data_directory()
            data_dir.mkdir(parents=True, exist_ok=True)
            self._db_path = str(data_dir / "sovereignty_cache.db")
        else:
            self._db_path = db_path

        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self._db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS analysis_cache (
                address_hash TEXT PRIMARY KEY,
                result_json TEXT NOT NULL,
                sovereignty_ratio REAL,
                portfolio_usd REAL,
                expires_at REAL NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS price_cache (
                ticker TEXT PRIMARY KEY,
                price REAL NOT NULL,
                source TEXT,
                expires_at REAL NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_analysis_expires
                ON analysis_cache(expires_at);

            CREATE INDEX IF NOT EXISTS idx_analysis_ratio
                ON analysis_cache(sovereignty_ratio);

            CREATE INDEX IF NOT EXISTS idx_price_expires
                ON price_cache(expires_at);
        """)
        conn.commit()

    @staticmethod
    def _hash_address(address: str) -> str:
        """Hash an address for use as a cache key."""
        return hashlib.sha256(address.encode()).hexdigest()[:16]

    # =========================================================================
    # Analysis cache
    # =========================================================================

    def get_analysis(self, address: str) -> Optional[dict]:
        """Get cached analysis result if not expired."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT result_json FROM analysis_cache WHERE address_hash = ? AND expires_at > ?",
            (self._hash_address(address), time.time()),
        ).fetchone()

        if row:
            try:
                return json.loads(row["result_json"])
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    def set_analysis(self, address: str, result: dict, ttl: Optional[int] = None) -> None:
        """Store analysis result with TTL."""
        ttl = ttl or self.ANALYSIS_TTL
        now = datetime.now(timezone.utc).isoformat()

        # Extract metrics for queryable columns
        sov_data = result.get("sovereignty_data") or {}
        ratio = sov_data.get("sovereignty_ratio")
        portfolio = sov_data.get("portfolio_usd")

        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO analysis_cache
               (address_hash, result_json, sovereignty_ratio, portfolio_usd, expires_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                self._hash_address(address),
                json.dumps(result, default=str),
                ratio,
                portfolio,
                time.time() + ttl,
                now,
            ),
        )
        conn.commit()

    # =========================================================================
    # Price cache
    # =========================================================================

    def get_price(self, ticker: str) -> Optional[float]:
        """Get cached price if not expired."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT price FROM price_cache WHERE ticker = ? AND expires_at > ?",
            (ticker.upper(), time.time()),
        ).fetchone()

        return row["price"] if row else None

    def set_price(self, ticker: str, price: float, source: str = "unknown", ttl: Optional[int] = None) -> None:
        """Store price with TTL."""
        ttl = ttl or self.PRICE_TTL
        now = datetime.now(timezone.utc).isoformat()

        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO price_cache
               (ticker, price, source, expires_at, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (ticker.upper(), price, source, time.time() + ttl, now),
        )
        conn.commit()

    # =========================================================================
    # History / progress queries
    # =========================================================================

    def get_recent_analyses(self, limit: int = 20) -> list[dict]:
        """Get most recent cached analyses (even if expired)."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT address_hash, sovereignty_ratio, portfolio_usd, created_at
               FROM analysis_cache
               ORDER BY created_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()

        return [dict(row) for row in rows]

    # =========================================================================
    # Maintenance
    # =========================================================================

    def cleanup_expired(self) -> dict:
        """Remove all expired entries. Returns counts of deleted rows."""
        conn = self._get_conn()
        now = time.time()

        analysis_result = conn.execute("DELETE FROM analysis_cache WHERE expires_at < ?", (now,))
        price_result = conn.execute("DELETE FROM price_cache WHERE expires_at < ?", (now,))
        conn.commit()

        return {
            "analysis_deleted": analysis_result.rowcount,
            "price_deleted": price_result.rowcount,
        }

    def get_stats(self) -> dict:
        """Get persistence layer statistics."""
        conn = self._get_conn()
        now = time.time()

        analysis_total = conn.execute("SELECT COUNT(*) as c FROM analysis_cache").fetchone()["c"]
        analysis_active = conn.execute(
            "SELECT COUNT(*) as c FROM analysis_cache WHERE expires_at > ?", (now,)
        ).fetchone()["c"]

        price_total = conn.execute("SELECT COUNT(*) as c FROM price_cache").fetchone()["c"]
        price_active = conn.execute(
            "SELECT COUNT(*) as c FROM price_cache WHERE expires_at > ?", (now,)
        ).fetchone()["c"]

        return {
            "analysis_cache": {"total": analysis_total, "active": analysis_active},
            "price_cache": {"total": price_total, "active": price_active},
            "db_path": self._db_path,
        }


# Singleton
_persistence: Optional[PersistenceDB] = None


def get_persistence() -> PersistenceDB:
    """Get the singleton PersistenceDB instance."""
    global _persistence
    if _persistence is None:
        _persistence = PersistenceDB()
    return _persistence
