"""
Gold Miner Metrics Tracking

Stores quarterly reports for gold mining companies including AISC, production,
financial metrics, and jurisdictional risk data for sector analysis.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict


# Database path - uses DATA_DIR env var for Railway/production
def _get_data_dir() -> str:
    """Get data directory from env var or default to project data folder."""
    env_data_dir = os.environ.get('DATA_DIR')
    if env_data_dir:
        return env_data_dir
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


DATA_DIR = _get_data_dir()
DB_PATH = os.path.join(DATA_DIR, 'miner_metrics.db')


# Seed data for initial population
SEED_DATA = [
    # Q3 2023 Data
    {'company': 'Newmont', 'ticker': 'NEM', 'period': '2023-Q3', 'aisc': 1400, 'production': 1.3, 'revenue': 2.9, 'fcf': 0.2, 'dividend_yield': 4.1, 'market_cap': 45, 'tier1': 45, 'tier2': 35, 'tier3': 20},
    {'company': 'Barrick', 'ticker': 'GOLD', 'period': '2023-Q3', 'aisc': 1280, 'production': 1.0, 'revenue': 2.8, 'fcf': 0.15, 'dividend_yield': 2.5, 'market_cap': 28, 'tier1': 30, 'tier2': 20, 'tier3': 50},
    {'company': 'Agnico Eagle', 'ticker': 'AEM', 'period': '2023-Q3', 'aisc': 1100, 'production': 0.85, 'revenue': 1.6, 'fcf': 0.25, 'dividend_yield': 3.1, 'market_cap': 32, 'tier1': 95, 'tier2': 5, 'tier3': 0},
    # Q4 2023 Data
    {'company': 'Newmont', 'ticker': 'NEM', 'period': '2023-Q4', 'aisc': 1450, 'production': 1.4, 'revenue': 3.1, 'fcf': 0.1, 'dividend_yield': 3.8, 'market_cap': 48.5, 'tier1': 45, 'tier2': 35, 'tier3': 20},
    {'company': 'Barrick', 'ticker': 'GOLD', 'period': '2023-Q4', 'aisc': 1335, 'production': 1.05, 'revenue': 2.9, 'fcf': 0.12, 'dividend_yield': 2.3, 'market_cap': 29.2, 'tier1': 30, 'tier2': 20, 'tier3': 50},
    {'company': 'Agnico Eagle', 'ticker': 'AEM', 'period': '2023-Q4', 'aisc': 1150, 'production': 0.88, 'revenue': 1.75, 'fcf': 0.3, 'dividend_yield': 2.8, 'market_cap': 34.8, 'tier1': 95, 'tier2': 5, 'tier3': 0},
    {'company': 'Gold Fields', 'ticker': 'GFI', 'period': '2023-Q4', 'aisc': 1295, 'production': 0.58, 'revenue': 1.1, 'fcf': 0.08, 'dividend_yield': 2.5, 'market_cap': 14.5, 'tier1': 40, 'tier2': 40, 'tier3': 20},
    {'company': 'Alamos Gold', 'ticker': 'AGI', 'period': '2023-Q4', 'aisc': 1125, 'production': 0.15, 'revenue': 0.25, 'fcf': 0.05, 'dividend_yield': 0.9, 'market_cap': 6.5, 'tier1': 90, 'tier2': 10, 'tier3': 0},
]


@dataclass
class MinerMetric:
    """Single quarterly report for a gold miner."""
    id: Optional[int]
    company: str
    ticker: str
    period: str  # e.g., "2024-Q1"
    aisc: float  # All-In Sustaining Cost ($/oz)
    production: float  # Million ounces
    revenue: float  # Billions USD
    fcf: float  # Free Cash Flow (Billions USD)
    dividend_yield: float  # Percentage
    market_cap: float  # Billions USD
    tier1: int  # Tier 1 jurisdiction exposure (%)
    tier2: int  # Tier 2 jurisdiction exposure (%)
    tier3: int  # Tier 3 jurisdiction exposure (%)
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        if self.timestamp:
            d['timestamp'] = self.timestamp.isoformat()
        return d


class MinerMetricsDB:
    """Manages gold miner metrics storage and retrieval."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        print(f"[MinerMetricsDB] Using database: {self.db_path}")
        self._init_db()

    def _init_db(self):
        """Initialize the database and create tables if needed."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS miner_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    period TEXT NOT NULL,
                    aisc REAL NOT NULL,
                    production REAL NOT NULL,
                    revenue REAL NOT NULL,
                    fcf REAL NOT NULL,
                    dividend_yield REAL NOT NULL,
                    market_cap REAL NOT NULL,
                    tier1 INTEGER NOT NULL DEFAULT 0,
                    tier2 INTEGER NOT NULL DEFAULT 0,
                    tier3 INTEGER NOT NULL DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, period)
                )
            ''')

            # Index for efficient queries
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_miner_metrics_period
                ON miner_metrics(period DESC)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_miner_metrics_ticker
                ON miner_metrics(ticker)
            ''')

            conn.commit()

            # Seed with initial data if empty
            cursor = conn.execute('SELECT COUNT(*) FROM miner_metrics')
            if cursor.fetchone()[0] == 0:
                self._seed_data(conn)

    def _seed_data(self, conn: sqlite3.Connection):
        """Populate database with initial seed data."""
        print("[MinerMetricsDB] Seeding initial data...")
        for data in SEED_DATA:
            conn.execute('''
                INSERT OR IGNORE INTO miner_metrics
                (company, ticker, period, aisc, production, revenue, fcf,
                 dividend_yield, market_cap, tier1, tier2, tier3)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['company'], data['ticker'], data['period'],
                data['aisc'], data['production'], data['revenue'], data['fcf'],
                data['dividend_yield'], data['market_cap'],
                data['tier1'], data['tier2'], data['tier3']
            ))
        conn.commit()
        print(f"[MinerMetricsDB] Seeded {len(SEED_DATA)} records")

    def create_metric(self, metric: MinerMetric) -> Optional[int]:
        """
        Create a new miner metric entry.

        Returns the new record ID if successful, None if duplicate.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO miner_metrics
                    (company, ticker, period, aisc, production, revenue, fcf,
                     dividend_yield, market_cap, tier1, tier2, tier3)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metric.company, metric.ticker, metric.period,
                    metric.aisc, metric.production, metric.revenue, metric.fcf,
                    metric.dividend_yield, metric.market_cap,
                    metric.tier1, metric.tier2, metric.tier3
                ))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Duplicate ticker+period
            return None

    def get_all_metrics(self, limit: int = 100) -> List[MinerMetric]:
        """
        Get all metrics ordered by period (newest first) then ticker.

        Args:
            limit: Maximum records to return

        Returns:
            List of MinerMetric objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, company, ticker, period, aisc, production, revenue,
                       fcf, dividend_yield, market_cap, tier1, tier2, tier3, timestamp
                FROM miner_metrics
                ORDER BY period DESC, ticker ASC
                LIMIT ?
            ''', (limit,))

            return [self._row_to_metric(row) for row in cursor.fetchall()]

    def get_metrics_by_ticker(self, ticker: str) -> List[MinerMetric]:
        """Get all metrics for a specific company."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, company, ticker, period, aisc, production, revenue,
                       fcf, dividend_yield, market_cap, tier1, tier2, tier3, timestamp
                FROM miner_metrics
                WHERE ticker = ?
                ORDER BY period DESC
            ''', (ticker,))

            return [self._row_to_metric(row) for row in cursor.fetchall()]

    def get_latest_by_company(self) -> List[MinerMetric]:
        """
        Get the most recent metric for each company.
        Useful for dashboard KPIs.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, company, ticker, period, aisc, production, revenue,
                       fcf, dividend_yield, market_cap, tier1, tier2, tier3, timestamp
                FROM miner_metrics m1
                WHERE period = (
                    SELECT MAX(period) FROM miner_metrics m2
                    WHERE m2.ticker = m1.ticker
                )
                ORDER BY aisc ASC
            ''')

            return [self._row_to_metric(row) for row in cursor.fetchall()]

    def get_sector_stats(self) -> Dict[str, Any]:
        """
        Calculate sector-wide statistics from latest data.
        """
        latest = self.get_latest_by_company()
        if not latest:
            return {
                'avg_aisc': 0,
                'total_production': 0,
                'avg_yield': 0,
                'tier1_exposure': 0,
                'company_count': 0
            }

        total_market_cap = sum(m.market_cap for m in latest)
        weighted_tier1 = sum(m.tier1 * m.market_cap for m in latest) / total_market_cap if total_market_cap > 0 else 0

        return {
            'avg_aisc': round(sum(m.aisc for m in latest) / len(latest), 0),
            'total_production': round(sum(m.production for m in latest), 2),
            'avg_yield': round(sum(m.dividend_yield for m in latest) / len(latest), 1),
            'tier1_exposure': round(weighted_tier1, 0),
            'company_count': len(latest)
        }

    def _row_to_metric(self, row: tuple) -> MinerMetric:
        """Convert database row to MinerMetric object."""
        timestamp = None
        if row[13]:
            try:
                timestamp = datetime.fromisoformat(row[13])
            except (ValueError, TypeError):
                pass

        return MinerMetric(
            id=row[0],
            company=row[1],
            ticker=row[2],
            period=row[3],
            aisc=row[4],
            production=row[5],
            revenue=row[6],
            fcf=row[7],
            dividend_yield=row[8],
            market_cap=row[9],
            tier1=row[10],
            tier2=row[11],
            tier3=row[12],
            timestamp=timestamp
        )


# Singleton instance
_miner_db: Optional[MinerMetricsDB] = None


def get_miner_metrics_db() -> MinerMetricsDB:
    """Get or create the MinerMetricsDB singleton."""
    global _miner_db
    if _miner_db is None:
        _miner_db = MinerMetricsDB()
    return _miner_db
