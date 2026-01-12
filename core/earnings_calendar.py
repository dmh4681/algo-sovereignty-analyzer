"""
Miner Earnings Calendar Module

Tracks quarterly earnings events for gold and silver mining companies.
Includes historical beat/miss data, price reactions, and upcoming events.
"""

import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "earnings_calendar.db"


@dataclass
class EarningsEvent:
    """Represents a single quarterly earnings event."""
    id: Optional[int]
    ticker: str
    metal: str  # 'gold' or 'silver'
    company_name: str
    quarter: str  # 'Q1 2024', 'Q2 2024', etc.

    # Timing
    earnings_date: str  # ISO format date
    time_of_day: str  # 'pre-market', 'after-hours', 'during-market'
    is_confirmed: bool  # vs estimated

    # Results (null until reported)
    eps_actual: Optional[float] = None
    eps_estimate: Optional[float] = None
    revenue_actual: Optional[float] = None  # in millions
    revenue_estimate: Optional[float] = None

    # Mining-specific
    production_actual: Optional[int] = None  # oz
    production_guidance: Optional[int] = None
    aisc_actual: Optional[float] = None
    aisc_guidance: Optional[float] = None

    # Post-earnings price data
    price_before: Optional[float] = None
    price_1d_after: Optional[float] = None
    price_5d_after: Optional[float] = None
    price_30d_after: Optional[float] = None

    # Metadata
    transcript_url: Optional[str] = None
    press_release_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'ticker': self.ticker,
            'metal': self.metal,
            'company_name': self.company_name,
            'quarter': self.quarter,
            'earnings_date': self.earnings_date,
            'time_of_day': self.time_of_day,
            'is_confirmed': self.is_confirmed,
            'eps_actual': self.eps_actual,
            'eps_estimate': self.eps_estimate,
            'revenue_actual': self.revenue_actual,
            'revenue_estimate': self.revenue_estimate,
            'production_actual': self.production_actual,
            'production_guidance': self.production_guidance,
            'aisc_actual': self.aisc_actual,
            'aisc_guidance': self.aisc_guidance,
            'price_before': self.price_before,
            'price_1d_after': self.price_1d_after,
            'price_5d_after': self.price_5d_after,
            'price_30d_after': self.price_30d_after,
            'transcript_url': self.transcript_url,
            'press_release_url': self.press_release_url,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            # Computed fields
            'eps_beat': self._calc_beat(self.eps_actual, self.eps_estimate),
            'revenue_beat': self._calc_beat(self.revenue_actual, self.revenue_estimate),
            'production_beat': self._calc_beat(self.production_actual, self.production_guidance),
            'aisc_beat': self._calc_aisc_beat(),
            'price_reaction_1d': self._calc_price_change(self.price_before, self.price_1d_after),
            'price_reaction_5d': self._calc_price_change(self.price_before, self.price_5d_after),
            'price_reaction_30d': self._calc_price_change(self.price_before, self.price_30d_after),
        }

    def _calc_beat(self, actual: Optional[float], estimate: Optional[float]) -> Optional[bool]:
        """Calculate if actual beat estimate."""
        if actual is None or estimate is None:
            return None
        return actual >= estimate

    def _calc_aisc_beat(self) -> Optional[bool]:
        """For AISC, lower is better so beat means actual < guidance."""
        if self.aisc_actual is None or self.aisc_guidance is None:
            return None
        return self.aisc_actual <= self.aisc_guidance

    def _calc_price_change(self, before: Optional[float], after: Optional[float]) -> Optional[float]:
        """Calculate percentage price change."""
        if before is None or after is None or before == 0:
            return None
        return round(((after - before) / before) * 100, 2)


@dataclass
class BeatMissStats:
    """Beat/miss statistics for a company."""
    ticker: str
    company_name: str
    metal: str
    quarters_tracked: int
    eps_beats: int
    eps_misses: int
    eps_beat_rate: float
    revenue_beats: int
    revenue_misses: int
    revenue_beat_rate: float
    production_beats: int
    production_misses: int
    production_beat_rate: float
    aisc_beats: int
    aisc_misses: int
    aisc_beat_rate: float
    avg_price_reaction_1d: Optional[float]
    avg_price_reaction_on_beat: Optional[float]
    avg_price_reaction_on_miss: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'ticker': self.ticker,
            'company_name': self.company_name,
            'metal': self.metal,
            'quarters_tracked': self.quarters_tracked,
            'eps': {
                'beats': self.eps_beats,
                'misses': self.eps_misses,
                'beat_rate': self.eps_beat_rate,
            },
            'revenue': {
                'beats': self.revenue_beats,
                'misses': self.revenue_misses,
                'beat_rate': self.revenue_beat_rate,
            },
            'production': {
                'beats': self.production_beats,
                'misses': self.production_misses,
                'beat_rate': self.production_beat_rate,
            },
            'aisc': {
                'beats': self.aisc_beats,
                'misses': self.aisc_misses,
                'beat_rate': self.aisc_beat_rate,
            },
            'price_reactions': {
                'avg_1d': self.avg_price_reaction_1d,
                'avg_on_beat': self.avg_price_reaction_on_beat,
                'avg_on_miss': self.avg_price_reaction_on_miss,
            }
        }


@dataclass
class SectorEarningsStats:
    """Sector-wide earnings statistics."""
    metal: str
    upcoming_count: int
    next_earnings_ticker: Optional[str]
    next_earnings_date: Optional[str]
    sector_avg_eps_beat_rate: float
    sector_avg_revenue_beat_rate: float
    sector_avg_1d_reaction: Optional[float]
    total_companies: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'metal': self.metal,
            'upcoming_count': self.upcoming_count,
            'next_earnings': {
                'ticker': self.next_earnings_ticker,
                'date': self.next_earnings_date,
            },
            'sector_avg_eps_beat_rate': self.sector_avg_eps_beat_rate,
            'sector_avg_revenue_beat_rate': self.sector_avg_revenue_beat_rate,
            'sector_avg_1d_reaction': self.sector_avg_1d_reaction,
            'total_companies': self.total_companies,
        }


class EarningsCalendarDB:
    """Database interface for earnings calendar data."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_conn()
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS earnings_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    metal TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    quarter TEXT NOT NULL,
                    earnings_date TEXT NOT NULL,
                    time_of_day TEXT DEFAULT 'pre-market',
                    is_confirmed INTEGER DEFAULT 0,
                    eps_actual REAL,
                    eps_estimate REAL,
                    revenue_actual REAL,
                    revenue_estimate REAL,
                    production_actual INTEGER,
                    production_guidance INTEGER,
                    aisc_actual REAL,
                    aisc_guidance REAL,
                    price_before REAL,
                    price_1d_after REAL,
                    price_5d_after REAL,
                    price_30d_after REAL,
                    transcript_url TEXT,
                    press_release_url TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, quarter)
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_earnings_date ON earnings_events(earnings_date)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_ticker ON earnings_events(ticker)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_metal ON earnings_events(metal)
            ''')
            conn.commit()

            # Check if we need to seed
            cursor = conn.execute('SELECT COUNT(*) FROM earnings_events')
            count = cursor.fetchone()[0]
            if count == 0:
                self._seed_data(conn)
        finally:
            conn.close()

    def _seed_data(self, conn: sqlite3.Connection):
        """Seed database with historical earnings data."""
        # Historical earnings data for gold miners (2023-2024)
        gold_earnings = [
            # Newmont (NEM)
            ('NEM', 'gold', 'Newmont', 'Q1 2023', '2023-04-27', 'pre-market', 1, 0.38, 0.35, 3100, 3050, 1580000, 1600000, 1276, 1300, 45.50, 46.20, 47.10, 44.80),
            ('NEM', 'gold', 'Newmont', 'Q2 2023', '2023-07-20', 'pre-market', 1, 0.29, 0.32, 2800, 2900, 1420000, 1500000, 1388, 1350, 44.20, 43.50, 44.10, 43.20),
            ('NEM', 'gold', 'Newmont', 'Q3 2023', '2023-10-26', 'pre-market', 1, 0.36, 0.34, 3050, 3000, 1510000, 1480000, 1305, 1320, 40.10, 39.20, 38.80, 37.50),
            ('NEM', 'gold', 'Newmont', 'Q4 2023', '2024-02-22', 'pre-market', 1, 0.41, 0.38, 3200, 3100, 1620000, 1580000, 1260, 1280, 35.80, 36.50, 37.20, 38.10),
            ('NEM', 'gold', 'Newmont', 'Q1 2024', '2024-04-25', 'pre-market', 1, 0.55, 0.48, 4100, 3900, 1680000, 1650000, 1185, 1220, 37.90, 38.60, 39.80, 41.20),
            ('NEM', 'gold', 'Newmont', 'Q2 2024', '2024-07-24', 'pre-market', 1, 0.72, 0.62, 4600, 4300, 1750000, 1700000, 1120, 1150, 45.30, 47.80, 49.10, 52.40),
            ('NEM', 'gold', 'Newmont', 'Q3 2024', '2024-10-23', 'pre-market', 1, 0.88, 0.78, 5100, 4800, 1820000, 1780000, 1050, 1100, 53.20, 55.40, 54.80, 52.10),

            # Barrick Gold (GOLD)
            ('GOLD', 'gold', 'Barrick Gold', 'Q1 2023', '2023-05-03', 'pre-market', 1, 0.14, 0.16, 2640, 2700, 952000, 980000, 1380, 1350, 17.20, 16.80, 16.50, 15.90),
            ('GOLD', 'gold', 'Barrick Gold', 'Q2 2023', '2023-08-07', 'pre-market', 1, 0.19, 0.18, 2830, 2800, 1010000, 1000000, 1320, 1340, 15.60, 15.90, 16.30, 15.80),
            ('GOLD', 'gold', 'Barrick Gold', 'Q3 2023', '2023-11-02', 'pre-market', 1, 0.24, 0.22, 2980, 2900, 1050000, 1020000, 1260, 1290, 15.20, 15.80, 16.10, 15.40),
            ('GOLD', 'gold', 'Barrick Gold', 'Q4 2023', '2024-02-14', 'pre-market', 1, 0.27, 0.25, 3100, 3050, 1080000, 1060000, 1220, 1250, 16.10, 16.70, 17.20, 17.80),
            ('GOLD', 'gold', 'Barrick Gold', 'Q1 2024', '2024-05-01', 'pre-market', 1, 0.32, 0.28, 3250, 3100, 1100000, 1080000, 1180, 1200, 17.50, 18.10, 18.60, 19.40),
            ('GOLD', 'gold', 'Barrick Gold', 'Q2 2024', '2024-08-12', 'pre-market', 1, 0.42, 0.36, 3600, 3400, 1150000, 1120000, 1090, 1120, 18.20, 19.40, 20.10, 21.30),
            ('GOLD', 'gold', 'Barrick Gold', 'Q3 2024', '2024-11-07', 'pre-market', 1, 0.52, 0.45, 4100, 3800, 1200000, 1160000, 1020, 1060, 20.80, 21.90, 22.50, 21.80),

            # Agnico Eagle (AEM)
            ('AEM', 'gold', 'Agnico Eagle', 'Q1 2023', '2023-04-27', 'pre-market', 1, 0.68, 0.62, 1630, 1580, 878000, 860000, 1145, 1160, 52.30, 53.80, 55.10, 54.20),
            ('AEM', 'gold', 'Agnico Eagle', 'Q2 2023', '2023-07-26', 'pre-market', 1, 0.75, 0.70, 1720, 1680, 915000, 900000, 1095, 1120, 50.10, 51.60, 52.40, 51.80),
            ('AEM', 'gold', 'Agnico Eagle', 'Q3 2023', '2023-10-26', 'pre-market', 1, 0.82, 0.76, 1810, 1750, 952000, 930000, 1050, 1080, 48.20, 49.80, 50.90, 49.10),
            ('AEM', 'gold', 'Agnico Eagle', 'Q4 2023', '2024-02-15', 'pre-market', 1, 0.88, 0.81, 1920, 1850, 985000, 960000, 1015, 1050, 52.40, 54.10, 55.80, 57.20),
            ('AEM', 'gold', 'Agnico Eagle', 'Q1 2024', '2024-04-25', 'pre-market', 1, 1.02, 0.92, 2050, 1980, 1020000, 1000000, 965, 1000, 58.80, 61.20, 63.50, 66.40),
            ('AEM', 'gold', 'Agnico Eagle', 'Q2 2024', '2024-07-31', 'pre-market', 1, 1.18, 1.05, 2280, 2150, 1080000, 1050000, 920, 960, 68.50, 71.80, 74.20, 78.10),
            ('AEM', 'gold', 'Agnico Eagle', 'Q3 2024', '2024-10-30', 'pre-market', 1, 1.32, 1.18, 2480, 2350, 1140000, 1100000, 875, 910, 82.40, 85.90, 88.30, 86.20),

            # Kinross Gold (KGC)
            ('KGC', 'gold', 'Kinross Gold', 'Q1 2023', '2023-05-10', 'pre-market', 1, 0.08, 0.10, 1020, 1080, 480000, 500000, 1280, 1250, 4.80, 4.60, 4.40, 4.20),
            ('KGC', 'gold', 'Kinross Gold', 'Q2 2023', '2023-08-02', 'pre-market', 1, 0.12, 0.11, 1150, 1120, 520000, 510000, 1220, 1240, 4.50, 4.70, 4.90, 5.10),
            ('KGC', 'gold', 'Kinross Gold', 'Q3 2023', '2023-11-08', 'pre-market', 1, 0.15, 0.13, 1280, 1220, 560000, 540000, 1160, 1190, 4.30, 4.50, 4.80, 5.20),
            ('KGC', 'gold', 'Kinross Gold', 'Q4 2023', '2024-02-14', 'pre-market', 1, 0.18, 0.15, 1380, 1320, 590000, 570000, 1100, 1140, 5.40, 5.80, 6.20, 6.80),
            ('KGC', 'gold', 'Kinross Gold', 'Q1 2024', '2024-05-08', 'pre-market', 1, 0.22, 0.18, 1480, 1400, 620000, 600000, 1040, 1080, 6.50, 7.10, 7.60, 8.20),
            ('KGC', 'gold', 'Kinross Gold', 'Q2 2024', '2024-07-31', 'pre-market', 1, 0.28, 0.24, 1620, 1550, 680000, 650000, 980, 1020, 8.40, 9.20, 9.80, 10.50),
            ('KGC', 'gold', 'Kinross Gold', 'Q3 2024', '2024-11-06', 'pre-market', 1, 0.35, 0.30, 1780, 1700, 720000, 690000, 920, 960, 10.20, 11.10, 11.80, 11.40),

            # B2Gold (BTG)
            ('BTG', 'gold', 'B2Gold', 'Q1 2023', '2023-05-03', 'pre-market', 1, 0.06, 0.07, 420, 450, 230000, 250000, 1320, 1280, 3.20, 3.10, 3.00, 2.85),
            ('BTG', 'gold', 'B2Gold', 'Q2 2023', '2023-08-08', 'pre-market', 1, 0.08, 0.08, 480, 470, 260000, 255000, 1260, 1290, 2.90, 2.95, 3.05, 2.80),
            ('BTG', 'gold', 'B2Gold', 'Q3 2023', '2023-11-07', 'pre-market', 1, 0.09, 0.08, 510, 490, 275000, 265000, 1200, 1240, 2.70, 2.85, 2.95, 2.60),
            ('BTG', 'gold', 'B2Gold', 'Q4 2023', '2024-02-21', 'pre-market', 1, 0.10, 0.09, 550, 520, 290000, 280000, 1140, 1180, 2.80, 2.95, 3.10, 3.30),
            ('BTG', 'gold', 'B2Gold', 'Q1 2024', '2024-05-07', 'pre-market', 1, 0.11, 0.10, 580, 550, 300000, 290000, 1080, 1120, 3.10, 3.30, 3.50, 3.75),
            ('BTG', 'gold', 'B2Gold', 'Q2 2024', '2024-08-06', 'pre-market', 1, 0.14, 0.12, 640, 600, 330000, 310000, 1020, 1060, 3.60, 3.90, 4.15, 4.40),
            ('BTG', 'gold', 'B2Gold', 'Q3 2024', '2024-11-05', 'pre-market', 1, 0.17, 0.14, 720, 670, 360000, 340000, 960, 1000, 4.20, 4.55, 4.80, 4.50),
        ]

        # Historical earnings for silver miners
        silver_earnings = [
            # Pan American Silver (PAAS)
            ('PAAS', 'silver', 'Pan American Silver', 'Q1 2023', '2023-05-10', 'pre-market', 1, 0.12, 0.15, 680, 720, 5200000, 5500000, 18.50, 18.00, 15.20, 14.80, 14.50, 13.90),
            ('PAAS', 'silver', 'Pan American Silver', 'Q2 2023', '2023-08-09', 'pre-market', 1, 0.18, 0.16, 750, 730, 5600000, 5400000, 17.20, 17.50, 14.50, 14.90, 15.30, 14.80),
            ('PAAS', 'silver', 'Pan American Silver', 'Q3 2023', '2023-11-08', 'pre-market', 1, 0.22, 0.19, 820, 780, 5900000, 5700000, 16.40, 16.80, 13.80, 14.30, 14.80, 14.20),
            ('PAAS', 'silver', 'Pan American Silver', 'Q4 2023', '2024-02-21', 'pre-market', 1, 0.25, 0.21, 880, 840, 6200000, 6000000, 15.80, 16.20, 14.60, 15.20, 15.80, 16.40),
            ('PAAS', 'silver', 'Pan American Silver', 'Q1 2024', '2024-05-08', 'pre-market', 1, 0.30, 0.26, 940, 900, 6500000, 6300000, 15.00, 15.50, 17.20, 18.10, 18.80, 19.60),
            ('PAAS', 'silver', 'Pan American Silver', 'Q2 2024', '2024-08-07', 'pre-market', 1, 0.38, 0.32, 1080, 1000, 7000000, 6700000, 14.20, 14.80, 20.40, 21.80, 22.60, 24.10),
            ('PAAS', 'silver', 'Pan American Silver', 'Q3 2024', '2024-11-06', 'pre-market', 1, 0.45, 0.38, 1200, 1120, 7500000, 7100000, 13.50, 14.20, 25.80, 27.40, 28.60, 27.20),

            # First Majestic (AG)
            ('AG', 'silver', 'First Majestic Silver', 'Q1 2023', '2023-05-04', 'pre-market', 1, -0.08, -0.05, 145, 160, 3100000, 3400000, 22.50, 21.80, 6.20, 5.90, 5.60, 5.30),
            ('AG', 'silver', 'First Majestic Silver', 'Q2 2023', '2023-08-02', 'pre-market', 1, -0.04, -0.03, 165, 170, 3400000, 3500000, 21.20, 21.50, 5.40, 5.50, 5.70, 5.40),
            ('AG', 'silver', 'First Majestic Silver', 'Q3 2023', '2023-11-01', 'pre-market', 1, 0.02, -0.01, 190, 180, 3700000, 3600000, 19.80, 20.20, 4.80, 5.10, 5.40, 5.00),
            ('AG', 'silver', 'First Majestic Silver', 'Q4 2023', '2024-02-22', 'pre-market', 1, 0.06, 0.03, 215, 200, 3900000, 3800000, 18.60, 19.20, 5.20, 5.60, 5.90, 6.30),
            ('AG', 'silver', 'First Majestic Silver', 'Q1 2024', '2024-05-02', 'pre-market', 1, 0.10, 0.07, 245, 230, 4100000, 4000000, 17.50, 18.20, 6.40, 6.90, 7.30, 7.80),
            ('AG', 'silver', 'First Majestic Silver', 'Q2 2024', '2024-08-01', 'pre-market', 1, 0.16, 0.12, 290, 270, 4500000, 4300000, 16.20, 17.00, 8.20, 8.90, 9.50, 10.20),
            ('AG', 'silver', 'First Majestic Silver', 'Q3 2024', '2024-10-31', 'pre-market', 1, 0.22, 0.17, 340, 310, 4900000, 4600000, 15.00, 15.80, 10.80, 11.60, 12.30, 11.70),

            # Hecla Mining (HL)
            ('HL', 'silver', 'Hecla Mining', 'Q1 2023', '2023-05-09', 'pre-market', 1, 0.02, 0.03, 180, 195, 3800000, 4000000, 16.80, 16.20, 4.90, 4.70, 4.50, 4.20),
            ('HL', 'silver', 'Hecla Mining', 'Q2 2023', '2023-08-08', 'pre-market', 1, 0.04, 0.04, 210, 210, 4100000, 4100000, 15.90, 16.00, 4.30, 4.35, 4.50, 4.20),
            ('HL', 'silver', 'Hecla Mining', 'Q3 2023', '2023-11-07', 'pre-market', 1, 0.06, 0.05, 235, 225, 4400000, 4300000, 14.80, 15.20, 3.90, 4.10, 4.30, 4.00),
            ('HL', 'silver', 'Hecla Mining', 'Q4 2023', '2024-02-21', 'pre-market', 1, 0.08, 0.06, 260, 245, 4600000, 4500000, 13.90, 14.40, 4.10, 4.40, 4.70, 5.00),
            ('HL', 'silver', 'Hecla Mining', 'Q1 2024', '2024-05-09', 'pre-market', 1, 0.10, 0.08, 285, 270, 4800000, 4700000, 13.20, 13.80, 5.30, 5.70, 6.10, 6.50),
            ('HL', 'silver', 'Hecla Mining', 'Q2 2024', '2024-08-07', 'pre-market', 1, 0.14, 0.11, 330, 305, 5200000, 5000000, 12.40, 13.00, 6.80, 7.40, 7.90, 8.50),
            ('HL', 'silver', 'Hecla Mining', 'Q3 2024', '2024-11-05', 'pre-market', 1, 0.18, 0.14, 380, 350, 5600000, 5400000, 11.60, 12.20, 8.90, 9.60, 10.20, 9.80),

            # Coeur Mining (CDE)
            ('CDE', 'silver', 'Coeur Mining', 'Q1 2023', '2023-05-03', 'pre-market', 1, -0.05, -0.03, 195, 210, 2900000, 3100000, 19.20, 18.60, 3.10, 2.90, 2.70, 2.50),
            ('CDE', 'silver', 'Coeur Mining', 'Q2 2023', '2023-08-02', 'pre-market', 1, -0.02, -0.01, 225, 230, 3200000, 3300000, 18.40, 18.80, 2.60, 2.70, 2.85, 2.60),
            ('CDE', 'silver', 'Coeur Mining', 'Q3 2023', '2023-11-01', 'pre-market', 1, 0.03, 0.01, 260, 250, 3500000, 3400000, 17.20, 17.80, 2.40, 2.55, 2.70, 2.45),
            ('CDE', 'silver', 'Coeur Mining', 'Q4 2023', '2024-02-21', 'pre-market', 1, 0.06, 0.04, 290, 275, 3700000, 3600000, 16.00, 16.60, 2.80, 3.00, 3.25, 3.50),
            ('CDE', 'silver', 'Coeur Mining', 'Q1 2024', '2024-05-01', 'pre-market', 1, 0.09, 0.07, 320, 305, 3900000, 3800000, 15.00, 15.60, 3.60, 3.90, 4.20, 4.55),
            ('CDE', 'silver', 'Coeur Mining', 'Q2 2024', '2024-07-31', 'pre-market', 1, 0.14, 0.11, 380, 350, 4300000, 4100000, 13.80, 14.40, 4.80, 5.30, 5.70, 6.20),
            ('CDE', 'silver', 'Coeur Mining', 'Q3 2024', '2024-10-30', 'pre-market', 1, 0.19, 0.15, 440, 400, 4700000, 4500000, 12.60, 13.20, 6.50, 7.10, 7.60, 7.20),
        ]

        # Upcoming earnings (2026) - Q4 2025 results
        upcoming_2026 = [
            # Gold Q4 2025
            ('NEM', 'gold', 'Newmont', 'Q4 2025', '2026-02-19', 'pre-market', 0, None, 1.05, None, 5800, None, 1950000, None, 980, None, None, None, None),
            ('GOLD', 'gold', 'Barrick Gold', 'Q4 2025', '2026-02-11', 'pre-market', 0, None, 0.62, None, 4600, None, 1280000, None, 960, None, None, None, None),
            ('AEM', 'gold', 'Agnico Eagle', 'Q4 2025', '2026-02-12', 'pre-market', 0, None, 1.52, None, 2800, None, 1220000, None, 840, None, None, None, None),
            ('KGC', 'gold', 'Kinross Gold', 'Q4 2025', '2026-02-11', 'pre-market', 0, None, 0.42, None, 2000, None, 780000, None, 860, None, None, None, None),
            ('BTG', 'gold', 'B2Gold', 'Q4 2025', '2026-02-18', 'pre-market', 0, None, 0.21, None, 820, None, 400000, None, 900, None, None, None, None),

            # Silver Q4 2025
            ('PAAS', 'silver', 'Pan American Silver', 'Q4 2025', '2026-02-18', 'pre-market', 0, None, 0.55, None, 1400, None, 8000000, None, 12.50, None, None, None, None),
            ('AG', 'silver', 'First Majestic Silver', 'Q4 2025', '2026-02-19', 'pre-market', 0, None, 0.32, None, 420, None, 5400000, None, 14.00, None, None, None, None),
            ('HL', 'silver', 'Hecla Mining', 'Q4 2025', '2026-02-18', 'pre-market', 0, None, 0.24, None, 460, None, 6100000, None, 10.50, None, None, None, None),
            ('CDE', 'silver', 'Coeur Mining', 'Q4 2025', '2026-02-18', 'pre-market', 0, None, 0.26, None, 520, None, 5200000, None, 11.50, None, None, None, None),
        ]

        # Insert all data
        all_earnings = gold_earnings + silver_earnings + upcoming_2026

        for event in all_earnings:
            conn.execute('''
                INSERT OR IGNORE INTO earnings_events (
                    ticker, metal, company_name, quarter, earnings_date, time_of_day,
                    is_confirmed, eps_actual, eps_estimate, revenue_actual, revenue_estimate,
                    production_actual, production_guidance, aisc_actual, aisc_guidance,
                    price_before, price_1d_after, price_5d_after, price_30d_after
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', event)

        conn.commit()

    def get_calendar(self, month: str = None) -> List[EarningsEvent]:
        """
        Get earnings events for a specific month (YYYY-MM format).
        If no month specified, returns current month.
        """
        if month is None:
            month = datetime.now().strftime('%Y-%m')

        conn = self._get_conn()
        try:
            cursor = conn.execute('''
                SELECT * FROM earnings_events
                WHERE earnings_date LIKE ?
                ORDER BY earnings_date ASC
            ''', (f'{month}%',))

            return [self._row_to_event(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_upcoming(self, days: int = 30) -> List[EarningsEvent]:
        """Get earnings events in the next N days."""
        today = datetime.now().date()
        end_date = today + timedelta(days=days)

        conn = self._get_conn()
        try:
            cursor = conn.execute('''
                SELECT * FROM earnings_events
                WHERE DATE(earnings_date) >= DATE(?)
                AND DATE(earnings_date) <= DATE(?)
                ORDER BY earnings_date ASC
            ''', (today.isoformat(), end_date.isoformat()))

            return [self._row_to_event(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_by_ticker(self, ticker: str) -> List[EarningsEvent]:
        """Get all earnings events for a specific ticker."""
        conn = self._get_conn()
        try:
            cursor = conn.execute('''
                SELECT * FROM earnings_events
                WHERE ticker = ?
                ORDER BY earnings_date DESC
            ''', (ticker.upper(),))

            return [self._row_to_event(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_stats(self, ticker: str) -> Optional[BeatMissStats]:
        """Calculate beat/miss statistics for a company."""
        events = self.get_by_ticker(ticker)
        if not events:
            return None

        # Filter to completed earnings only
        completed = [e for e in events if e.eps_actual is not None]
        if not completed:
            return None

        # Calculate beat/miss counts
        eps_beats = sum(1 for e in completed if e.eps_actual and e.eps_estimate and e.eps_actual >= e.eps_estimate)
        eps_misses = sum(1 for e in completed if e.eps_actual and e.eps_estimate and e.eps_actual < e.eps_estimate)
        eps_total = eps_beats + eps_misses

        rev_beats = sum(1 for e in completed if e.revenue_actual and e.revenue_estimate and e.revenue_actual >= e.revenue_estimate)
        rev_misses = sum(1 for e in completed if e.revenue_actual and e.revenue_estimate and e.revenue_actual < e.revenue_estimate)
        rev_total = rev_beats + rev_misses

        prod_beats = sum(1 for e in completed if e.production_actual and e.production_guidance and e.production_actual >= e.production_guidance)
        prod_misses = sum(1 for e in completed if e.production_actual and e.production_guidance and e.production_actual < e.production_guidance)
        prod_total = prod_beats + prod_misses

        aisc_beats = sum(1 for e in completed if e.aisc_actual and e.aisc_guidance and e.aisc_actual <= e.aisc_guidance)
        aisc_misses = sum(1 for e in completed if e.aisc_actual and e.aisc_guidance and e.aisc_actual > e.aisc_guidance)
        aisc_total = aisc_beats + aisc_misses

        # Calculate price reactions
        reactions_1d = [
            ((e.price_1d_after - e.price_before) / e.price_before * 100)
            for e in completed
            if e.price_before and e.price_1d_after and e.price_before > 0
        ]

        # Reactions on beat vs miss
        beat_reactions = []
        miss_reactions = []
        for e in completed:
            if e.price_before and e.price_1d_after and e.price_before > 0:
                reaction = (e.price_1d_after - e.price_before) / e.price_before * 100
                if e.eps_actual and e.eps_estimate:
                    if e.eps_actual >= e.eps_estimate:
                        beat_reactions.append(reaction)
                    else:
                        miss_reactions.append(reaction)

        return BeatMissStats(
            ticker=ticker.upper(),
            company_name=events[0].company_name,
            metal=events[0].metal,
            quarters_tracked=len(completed),
            eps_beats=eps_beats,
            eps_misses=eps_misses,
            eps_beat_rate=round(eps_beats / eps_total * 100, 1) if eps_total > 0 else 0,
            revenue_beats=rev_beats,
            revenue_misses=rev_misses,
            revenue_beat_rate=round(rev_beats / rev_total * 100, 1) if rev_total > 0 else 0,
            production_beats=prod_beats,
            production_misses=prod_misses,
            production_beat_rate=round(prod_beats / prod_total * 100, 1) if prod_total > 0 else 0,
            aisc_beats=aisc_beats,
            aisc_misses=aisc_misses,
            aisc_beat_rate=round(aisc_beats / aisc_total * 100, 1) if aisc_total > 0 else 0,
            avg_price_reaction_1d=round(sum(reactions_1d) / len(reactions_1d), 2) if reactions_1d else None,
            avg_price_reaction_on_beat=round(sum(beat_reactions) / len(beat_reactions), 2) if beat_reactions else None,
            avg_price_reaction_on_miss=round(sum(miss_reactions) / len(miss_reactions), 2) if miss_reactions else None,
        )

    def get_sector_stats(self, metal: str = None) -> SectorEarningsStats:
        """Get sector-wide earnings statistics."""
        conn = self._get_conn()
        try:
            # Get upcoming earnings
            today = datetime.now().date().isoformat()

            if metal:
                cursor = conn.execute('''
                    SELECT * FROM earnings_events
                    WHERE metal = ? AND DATE(earnings_date) >= DATE(?)
                    ORDER BY earnings_date ASC
                ''', (metal, today))
            else:
                cursor = conn.execute('''
                    SELECT * FROM earnings_events
                    WHERE DATE(earnings_date) >= DATE(?)
                    ORDER BY earnings_date ASC
                ''', (today,))

            upcoming = [self._row_to_event(row) for row in cursor.fetchall()]

            # Get historical data for beat rates
            if metal:
                cursor = conn.execute('''
                    SELECT * FROM earnings_events
                    WHERE metal = ? AND eps_actual IS NOT NULL
                ''', (metal,))
            else:
                cursor = conn.execute('''
                    SELECT * FROM earnings_events
                    WHERE eps_actual IS NOT NULL
                ''')

            completed = [self._row_to_event(row) for row in cursor.fetchall()]

            # Calculate sector averages
            eps_beats = sum(1 for e in completed if e.eps_actual and e.eps_estimate and e.eps_actual >= e.eps_estimate)
            eps_total = sum(1 for e in completed if e.eps_actual and e.eps_estimate)

            rev_beats = sum(1 for e in completed if e.revenue_actual and e.revenue_estimate and e.revenue_actual >= e.revenue_estimate)
            rev_total = sum(1 for e in completed if e.revenue_actual and e.revenue_estimate)

            reactions = [
                ((e.price_1d_after - e.price_before) / e.price_before * 100)
                for e in completed
                if e.price_before and e.price_1d_after and e.price_before > 0
            ]

            # Count unique companies
            if metal:
                cursor = conn.execute('SELECT COUNT(DISTINCT ticker) FROM earnings_events WHERE metal = ?', (metal,))
            else:
                cursor = conn.execute('SELECT COUNT(DISTINCT ticker) FROM earnings_events')
            company_count = cursor.fetchone()[0]

            return SectorEarningsStats(
                metal=metal or 'all',
                upcoming_count=len(upcoming),
                next_earnings_ticker=upcoming[0].ticker if upcoming else None,
                next_earnings_date=upcoming[0].earnings_date if upcoming else None,
                sector_avg_eps_beat_rate=round(eps_beats / eps_total * 100, 1) if eps_total > 0 else 0,
                sector_avg_revenue_beat_rate=round(rev_beats / rev_total * 100, 1) if rev_total > 0 else 0,
                sector_avg_1d_reaction=round(sum(reactions) / len(reactions), 2) if reactions else None,
                total_companies=company_count,
            )
        finally:
            conn.close()

    def create_event(self, event: EarningsEvent) -> Optional[int]:
        """Create a new earnings event."""
        conn = self._get_conn()
        try:
            cursor = conn.execute('''
                INSERT INTO earnings_events (
                    ticker, metal, company_name, quarter, earnings_date, time_of_day,
                    is_confirmed, eps_actual, eps_estimate, revenue_actual, revenue_estimate,
                    production_actual, production_guidance, aisc_actual, aisc_guidance,
                    price_before, price_1d_after, price_5d_after, price_30d_after,
                    transcript_url, press_release_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.ticker.upper(), event.metal, event.company_name, event.quarter,
                event.earnings_date, event.time_of_day, 1 if event.is_confirmed else 0,
                event.eps_actual, event.eps_estimate, event.revenue_actual, event.revenue_estimate,
                event.production_actual, event.production_guidance, event.aisc_actual, event.aisc_guidance,
                event.price_before, event.price_1d_after, event.price_5d_after, event.price_30d_after,
                event.transcript_url, event.press_release_url
            ))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    def update_event(self, event_id: int, updates: Dict[str, Any]) -> bool:
        """Update an existing earnings event."""
        conn = self._get_conn()
        try:
            # Build dynamic update query
            allowed_fields = [
                'eps_actual', 'eps_estimate', 'revenue_actual', 'revenue_estimate',
                'production_actual', 'production_guidance', 'aisc_actual', 'aisc_guidance',
                'price_before', 'price_1d_after', 'price_5d_after', 'price_30d_after',
                'earnings_date', 'time_of_day', 'is_confirmed', 'transcript_url', 'press_release_url'
            ]

            set_clauses = []
            values = []
            for field, value in updates.items():
                if field in allowed_fields:
                    set_clauses.append(f'{field} = ?')
                    values.append(value)

            if not set_clauses:
                return False

            set_clauses.append('updated_at = CURRENT_TIMESTAMP')
            values.append(event_id)

            query = f"UPDATE earnings_events SET {', '.join(set_clauses)} WHERE id = ?"
            cursor = conn.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def reseed(self) -> int:
        """Clear all data and reseed from scratch."""
        conn = self._get_conn()
        try:
            conn.execute('DELETE FROM earnings_events')
            conn.commit()
            self._seed_data(conn)

            cursor = conn.execute('SELECT COUNT(*) FROM earnings_events')
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def _row_to_event(self, row: sqlite3.Row) -> EarningsEvent:
        """Convert database row to EarningsEvent object."""
        return EarningsEvent(
            id=row['id'],
            ticker=row['ticker'],
            metal=row['metal'],
            company_name=row['company_name'],
            quarter=row['quarter'],
            earnings_date=row['earnings_date'],
            time_of_day=row['time_of_day'],
            is_confirmed=bool(row['is_confirmed']),
            eps_actual=row['eps_actual'],
            eps_estimate=row['eps_estimate'],
            revenue_actual=row['revenue_actual'],
            revenue_estimate=row['revenue_estimate'],
            production_actual=row['production_actual'],
            production_guidance=row['production_guidance'],
            aisc_actual=row['aisc_actual'],
            aisc_guidance=row['aisc_guidance'],
            price_before=row['price_before'],
            price_1d_after=row['price_1d_after'],
            price_5d_after=row['price_5d_after'],
            price_30d_after=row['price_30d_after'],
            transcript_url=row['transcript_url'],
            press_release_url=row['press_release_url'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )


# Singleton instance
_db_instance: Optional[EarningsCalendarDB] = None

def get_earnings_db() -> EarningsCalendarDB:
    """Get singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = EarningsCalendarDB()
    return _db_instance
