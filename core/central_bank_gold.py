"""
Central Bank Gold Tracker Module

Tracks global central bank gold holdings, purchases/sales, and de-dollarization metrics.

Data Sources:
- World Gold Council (WGC) monthly reports
- IMF International Financial Statistics
- Individual central bank bulletins
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
DB_PATH = os.path.join(DATA_DIR, 'central_bank_gold.db')


# Country metadata for display
COUNTRY_METADATA = {
    'US': {'name': 'United States', 'flag': '🇺🇸', 'region': 'Americas'},
    'DE': {'name': 'Germany', 'flag': '🇩🇪', 'region': 'Europe'},
    'IT': {'name': 'Italy', 'flag': '🇮🇹', 'region': 'Europe'},
    'FR': {'name': 'France', 'flag': '🇫🇷', 'region': 'Europe'},
    'RU': {'name': 'Russia', 'flag': '🇷🇺', 'region': 'Europe'},
    'CN': {'name': 'China', 'flag': '🇨🇳', 'region': 'Asia'},
    'CH': {'name': 'Switzerland', 'flag': '🇨🇭', 'region': 'Europe'},
    'JP': {'name': 'Japan', 'flag': '🇯🇵', 'region': 'Asia'},
    'IN': {'name': 'India', 'flag': '🇮🇳', 'region': 'Asia'},
    'NL': {'name': 'Netherlands', 'flag': '🇳🇱', 'region': 'Europe'},
    'TR': {'name': 'Turkey', 'flag': '🇹🇷', 'region': 'Europe'},
    'TW': {'name': 'Taiwan', 'flag': '🇹🇼', 'region': 'Asia'},
    'PT': {'name': 'Portugal', 'flag': '🇵🇹', 'region': 'Europe'},
    'PL': {'name': 'Poland', 'flag': '🇵🇱', 'region': 'Europe'},
    'SA': {'name': 'Saudi Arabia', 'flag': '🇸🇦', 'region': 'Middle East'},
    'GB': {'name': 'United Kingdom', 'flag': '🇬🇧', 'region': 'Europe'},
    'KZ': {'name': 'Kazakhstan', 'flag': '🇰🇿', 'region': 'Asia'},
    'LB': {'name': 'Lebanon', 'flag': '🇱🇧', 'region': 'Middle East'},
    'ES': {'name': 'Spain', 'flag': '🇪🇸', 'region': 'Europe'},
    'AT': {'name': 'Austria', 'flag': '🇦🇹', 'region': 'Europe'},
    'BE': {'name': 'Belgium', 'flag': '🇧🇪', 'region': 'Europe'},
    'PH': {'name': 'Philippines', 'flag': '🇵🇭', 'region': 'Asia'},
    'VE': {'name': 'Venezuela', 'flag': '🇻🇪', 'region': 'Americas'},
    'HU': {'name': 'Hungary', 'flag': '🇭🇺', 'region': 'Europe'},
    'SG': {'name': 'Singapore', 'flag': '🇸🇬', 'region': 'Asia'},
    'CZ': {'name': 'Czech Republic', 'flag': '🇨🇿', 'region': 'Europe'},
    'UZ': {'name': 'Uzbekistan', 'flag': '🇺🇿', 'region': 'Asia'},
    'TH': {'name': 'Thailand', 'flag': '🇹🇭', 'region': 'Asia'},
    'IQ': {'name': 'Iraq', 'flag': '🇮🇶', 'region': 'Middle East'},
    'AE': {'name': 'UAE', 'flag': '🇦🇪', 'region': 'Middle East'},
}


# Historical central bank gold holdings data (tonnes)
# Source: World Gold Council, IMF IFS
# Data as of end of each year
HOLDINGS_SEED_DATA = [
    # Format: (country_code, date, tonnes, pct_of_reserves)
    # 2020 Data
    ('US', '2020-12', 8133.5, 79.0),
    ('DE', '2020-12', 3362.4, 75.0),
    ('IT', '2020-12', 2451.8, 70.0),
    ('FR', '2020-12', 2436.0, 66.0),
    ('RU', '2020-12', 2298.5, 23.0),
    ('CN', '2020-12', 1948.3, 3.3),
    ('CH', '2020-12', 1040.0, 6.0),
    ('JP', '2020-12', 765.2, 3.0),
    ('IN', '2020-12', 676.6, 6.5),
    ('NL', '2020-12', 612.5, 67.0),
    ('TR', '2020-12', 527.4, 42.0),
    ('TW', '2020-12', 423.6, 4.0),
    ('PL', '2020-12', 228.7, 8.0),
    ('SA', '2020-12', 323.1, 3.5),
    ('GB', '2020-12', 310.3, 10.0),
    ('KZ', '2020-12', 381.7, 65.0),
    ('HU', '2020-12', 94.5, 12.0),
    ('SG', '2020-12', 127.4, 2.0),
    ('CZ', '2020-12', 31.4, 2.0),
    ('UZ', '2020-12', 331.5, 55.0),

    # 2021 Data
    ('US', '2021-12', 8133.5, 78.0),
    ('DE', '2021-12', 3359.1, 74.0),
    ('IT', '2021-12', 2451.8, 68.0),
    ('FR', '2021-12', 2436.4, 65.0),
    ('RU', '2021-12', 2301.6, 22.0),
    ('CN', '2021-12', 1948.3, 3.2),
    ('CH', '2021-12', 1040.0, 5.5),
    ('JP', '2021-12', 765.2, 2.8),
    ('IN', '2021-12', 754.1, 7.0),
    ('NL', '2021-12', 612.5, 65.0),
    ('TR', '2021-12', 394.2, 25.0),
    ('TW', '2021-12', 423.6, 3.8),
    ('PL', '2021-12', 228.7, 8.5),
    ('SA', '2021-12', 323.1, 3.3),
    ('GB', '2021-12', 310.3, 9.5),
    ('KZ', '2021-12', 380.8, 62.0),
    ('HU', '2021-12', 94.5, 10.0),
    ('SG', '2021-12', 153.8, 2.2),
    ('CZ', '2021-12', 31.4, 1.8),
    ('UZ', '2021-12', 362.5, 60.0),

    # 2022 Data
    ('US', '2022-12', 8133.5, 69.0),
    ('DE', '2022-12', 3355.1, 70.0),
    ('IT', '2022-12', 2451.8, 66.0),
    ('FR', '2022-12', 2436.8, 64.0),
    ('RU', '2022-12', 2298.5, 24.0),
    ('CN', '2022-12', 2010.5, 3.6),
    ('CH', '2022-12', 1040.0, 5.2),
    ('JP', '2022-12', 846.0, 3.8),
    ('IN', '2022-12', 785.3, 8.0),
    ('NL', '2022-12', 612.5, 62.0),
    ('TR', '2022-12', 542.6, 28.0),
    ('TW', '2022-12', 423.6, 3.5),
    ('PL', '2022-12', 228.7, 9.0),
    ('SA', '2022-12', 323.1, 3.2),
    ('GB', '2022-12', 310.3, 9.0),
    ('KZ', '2022-12', 352.4, 58.0),
    ('HU', '2022-12', 94.5, 9.0),
    ('SG', '2022-12', 153.8, 2.0),
    ('CZ', '2022-12', 41.5, 2.5),
    ('UZ', '2022-12', 395.4, 62.0),

    # 2023 Data
    ('US', '2023-12', 8133.5, 72.0),
    ('DE', '2023-12', 3352.6, 71.0),
    ('IT', '2023-12', 2451.8, 68.0),
    ('FR', '2023-12', 2436.9, 67.0),
    ('RU', '2023-12', 2332.7, 26.0),
    ('CN', '2023-12', 2235.4, 4.3),
    ('CH', '2023-12', 1040.0, 5.8),
    ('JP', '2023-12', 846.0, 4.2),
    ('IN', '2023-12', 803.6, 8.5),
    ('NL', '2023-12', 612.5, 64.0),
    ('TR', '2023-12', 479.8, 26.0),
    ('TW', '2023-12', 423.6, 3.8),
    ('PL', '2023-12', 334.0, 12.0),
    ('SA', '2023-12', 323.1, 3.5),
    ('GB', '2023-12', 310.3, 9.2),
    ('KZ', '2023-12', 291.8, 52.0),
    ('HU', '2023-12', 94.5, 8.5),
    ('SG', '2023-12', 228.7, 3.5),
    ('CZ', '2023-12', 41.8, 2.8),
    ('UZ', '2023-12', 372.5, 58.0),

    # 2024 Data (Q3 estimates)
    ('US', '2024-09', 8133.5, 71.0),
    ('DE', '2024-09', 3351.5, 70.0),
    ('IT', '2024-09', 2451.8, 67.0),
    ('FR', '2024-09', 2437.0, 66.0),
    ('RU', '2024-09', 2335.9, 27.0),
    ('CN', '2024-09', 2264.3, 4.9),
    ('CH', '2024-09', 1040.0, 5.5),
    ('JP', '2024-09', 846.0, 4.5),
    ('IN', '2024-09', 854.7, 9.2),
    ('NL', '2024-09', 612.5, 62.0),
    ('TR', '2024-09', 584.2, 30.0),
    ('TW', '2024-09', 423.6, 3.6),
    ('PL', '2024-09', 420.0, 15.0),
    ('SA', '2024-09', 323.1, 3.8),
    ('GB', '2024-09', 310.3, 9.0),
    ('KZ', '2024-09', 282.5, 50.0),
    ('HU', '2024-09', 110.0, 10.0),
    ('SG', '2024-09', 236.5, 4.0),
    ('CZ', '2024-09', 46.2, 3.2),
    ('UZ', '2024-09', 380.0, 60.0),
]


# Net purchases by year (global totals in tonnes)
NET_PURCHASES_SEED = [
    ('2010', 77),
    ('2011', 457),
    ('2012', 544),
    ('2013', 409),
    ('2014', 584),
    ('2015', 577),
    ('2016', 389),
    ('2017', 375),
    ('2018', 656),
    ('2019', 668),
    ('2020', 273),  # COVID slowdown
    ('2021', 463),
    ('2022', 1082),  # Record year
    ('2023', 1037),
    ('2024', 800),  # Estimate
]


@dataclass
class CentralBankHolding:
    """A central bank's gold holding at a point in time."""
    id: Optional[int]
    country_code: str
    country_name: str
    date: str  # YYYY-MM format
    tonnes: float
    pct_of_reserves: float
    region: str
    flag: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NetPurchase:
    """Global net gold purchases for a period."""
    year: str
    tonnes: float
    is_buying: bool  # True if net buyer, False if net seller

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CountryRanking:
    """Country ranking by gold holdings."""
    rank: int
    country_code: str
    country_name: str
    flag: str
    tonnes: float
    pct_of_reserves: float
    change_12m: Optional[float]  # Change vs 12 months ago in tonnes
    region: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeDollarizationScore:
    """De-dollarization composite score."""
    date: str
    score: float  # 0-100
    components: Dict[str, float]
    interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CentralBankGoldDB:
    """Manages central bank gold holdings data."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        print(f"[CentralBankGoldDB] Using database: {self.db_path}")
        self._init_db()

    def _init_db(self):
        """Initialize the database and create tables if needed."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Holdings table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS holdings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    country_code TEXT NOT NULL,
                    date TEXT NOT NULL,
                    tonnes REAL NOT NULL,
                    pct_of_reserves REAL NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(country_code, date)
                )
            ''')

            # Net purchases table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS net_purchases (
                    year TEXT PRIMARY KEY,
                    tonnes REAL NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Indexes
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_holdings_date
                ON holdings(date DESC)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_holdings_country
                ON holdings(country_code)
            ''')

            conn.commit()

            # Seed if empty
            cursor = conn.execute('SELECT COUNT(*) FROM holdings')
            if cursor.fetchone()[0] == 0:
                self._seed_data(conn)

    def _seed_data(self, conn: sqlite3.Connection):
        """Populate database with seed data."""
        print("[CentralBankGoldDB] Seeding data...")

        # Seed holdings
        for country_code, date, tonnes, pct in HOLDINGS_SEED_DATA:
            conn.execute('''
                INSERT OR REPLACE INTO holdings (country_code, date, tonnes, pct_of_reserves)
                VALUES (?, ?, ?, ?)
            ''', (country_code, date, tonnes, pct))

        # Seed net purchases
        for year, tonnes in NET_PURCHASES_SEED:
            conn.execute('''
                INSERT OR REPLACE INTO net_purchases (year, tonnes)
                VALUES (?, ?)
            ''', (year, tonnes))

        conn.commit()
        print(f"[CentralBankGoldDB] Seeded {len(HOLDINGS_SEED_DATA)} holdings, {len(NET_PURCHASES_SEED)} net purchases")

    def reseed(self) -> int:
        """Clear and reseed the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM holdings')
            conn.execute('DELETE FROM net_purchases')
            self._seed_data(conn)
        return len(HOLDINGS_SEED_DATA)

    def get_latest_holdings(self) -> List[CentralBankHolding]:
        """Get the most recent holding for each country."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT h.id, h.country_code, h.date, h.tonnes, h.pct_of_reserves
                FROM holdings h
                INNER JOIN (
                    SELECT country_code, MAX(date) as max_date
                    FROM holdings
                    GROUP BY country_code
                ) latest ON h.country_code = latest.country_code AND h.date = latest.max_date
                ORDER BY h.tonnes DESC
            ''')

            results = []
            for row in cursor.fetchall():
                meta = COUNTRY_METADATA.get(row[1], {
                    'name': row[1], 'flag': '🏳️', 'region': 'Unknown'
                })
                results.append(CentralBankHolding(
                    id=row[0],
                    country_code=row[1],
                    country_name=meta['name'],
                    date=row[2],
                    tonnes=row[3],
                    pct_of_reserves=row[4],
                    region=meta['region'],
                    flag=meta['flag']
                ))
            return results

    def get_country_history(self, country_code: str) -> List[CentralBankHolding]:
        """Get historical holdings for a specific country."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, country_code, date, tonnes, pct_of_reserves
                FROM holdings
                WHERE country_code = ?
                ORDER BY date ASC
            ''', (country_code.upper(),))

            results = []
            meta = COUNTRY_METADATA.get(country_code.upper(), {
                'name': country_code, 'flag': '🏳️', 'region': 'Unknown'
            })
            for row in cursor.fetchall():
                results.append(CentralBankHolding(
                    id=row[0],
                    country_code=row[1],
                    country_name=meta['name'],
                    date=row[2],
                    tonnes=row[3],
                    pct_of_reserves=row[4],
                    region=meta['region'],
                    flag=meta['flag']
                ))
            return results

    def get_leaderboard(self, limit: int = 20) -> List[CountryRanking]:
        """Get country rankings by gold holdings with 12-month change."""
        latest = self.get_latest_holdings()

        # Get holdings from ~12 months ago for change calculation
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT country_code, tonnes
                FROM holdings
                WHERE date LIKE '2023-%'
                ORDER BY date DESC
            ''')
            prev_holdings = {}
            for row in cursor.fetchall():
                if row[0] not in prev_holdings:
                    prev_holdings[row[0]] = row[1]

        rankings = []
        for i, h in enumerate(latest[:limit]):
            prev_tonnes = prev_holdings.get(h.country_code)
            change = round(h.tonnes - prev_tonnes, 1) if prev_tonnes else None

            rankings.append(CountryRanking(
                rank=i + 1,
                country_code=h.country_code,
                country_name=h.country_name,
                flag=h.flag,
                tonnes=h.tonnes,
                pct_of_reserves=h.pct_of_reserves,
                change_12m=change,
                region=h.region
            ))

        return rankings

    def get_net_purchases(self) -> List[NetPurchase]:
        """Get global net purchases by year."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT year, tonnes FROM net_purchases
                ORDER BY year ASC
            ''')

            return [
                NetPurchase(
                    year=row[0],
                    tonnes=row[1],
                    is_buying=row[1] > 0
                )
                for row in cursor.fetchall()
            ]

    def get_top_buyers(self, n: int = 10) -> List[CountryRanking]:
        """Get top gold buyers based on 12-month change."""
        rankings = self.get_leaderboard(limit=50)

        # Filter to those with positive change and sort by change
        buyers = [r for r in rankings if r.change_12m and r.change_12m > 0]
        buyers.sort(key=lambda x: x.change_12m or 0, reverse=True)

        return buyers[:n]

    def get_top_sellers(self, n: int = 10) -> List[CountryRanking]:
        """Get top gold sellers based on 12-month change."""
        rankings = self.get_leaderboard(limit=50)

        # Filter to those with negative change and sort by change (most negative first)
        sellers = [r for r in rankings if r.change_12m and r.change_12m < 0]
        sellers.sort(key=lambda x: x.change_12m or 0)

        return sellers[:n]

    def calculate_dedollarization_score(self) -> DeDollarizationScore:
        """
        Calculate a composite de-dollarization score (0-100).

        Components:
        1. Gold as % of global reserves (higher = higher score)
        2. Years of consecutive net buying (more = higher score)
        3. Rate of gold accumulation (faster = higher score)
        4. Non-USD reserve growth (BRICS, etc.)
        """
        # Get latest data
        latest = self.get_latest_holdings()
        net_purchases = self.get_net_purchases()

        # Calculate global totals
        total_tonnes = sum(h.tonnes for h in latest)
        avg_pct_reserves = sum(h.pct_of_reserves for h in latest) / len(latest) if latest else 0

        # Count consecutive years of net buying
        consecutive_buying = 0
        for np in reversed(net_purchases):
            if np.tonnes > 0:
                consecutive_buying += 1
            else:
                break

        # Recent purchase volume (last 3 years avg vs historical)
        recent_purchases = [np.tonnes for np in net_purchases[-3:]]
        avg_recent = sum(recent_purchases) / len(recent_purchases) if recent_purchases else 0
        historical_avg = sum(np.tonnes for np in net_purchases[:-3]) / max(1, len(net_purchases) - 3)
        purchase_acceleration = avg_recent / historical_avg if historical_avg > 0 else 1

        # Calculate component scores
        gold_pct_score = min(30, avg_pct_reserves * 1.5)  # Max 30 points
        buying_streak_score = min(25, consecutive_buying * 2)  # Max 25 points
        acceleration_score = min(25, purchase_acceleration * 10)  # Max 25 points
        volume_score = min(20, (avg_recent / 100))  # Max 20 points

        total_score = gold_pct_score + buying_streak_score + acceleration_score + volume_score
        total_score = round(min(100, max(0, total_score)), 1)

        # Interpretation
        if total_score >= 70:
            interpretation = "Strong de-dollarization trend - central banks aggressively accumulating gold"
        elif total_score >= 50:
            interpretation = "Moderate de-dollarization - steady gold accumulation continues"
        elif total_score >= 30:
            interpretation = "Early stages of de-dollarization - some diversification away from USD"
        else:
            interpretation = "Weak de-dollarization signal - USD remains dominant"

        return DeDollarizationScore(
            date=datetime.utcnow().strftime('%Y-%m'),
            score=total_score,
            components={
                'gold_pct_score': round(gold_pct_score, 1),
                'buying_streak_score': round(buying_streak_score, 1),
                'acceleration_score': round(acceleration_score, 1),
                'volume_score': round(volume_score, 1),
                'consecutive_buying_years': consecutive_buying,
                'avg_recent_purchases': round(avg_recent, 0),
                'total_global_tonnes': round(total_tonnes, 0),
            },
            interpretation=interpretation
        )

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the dashboard."""
        latest = self.get_latest_holdings()
        net_purchases = self.get_net_purchases()
        dedollarization = self.calculate_dedollarization_score()

        # Calculate totals
        total_tonnes = sum(h.tonnes for h in latest)
        total_countries = len(latest)

        # Recent purchase data
        recent = net_purchases[-1] if net_purchases else None
        prev_year = net_purchases[-2] if len(net_purchases) > 1 else None

        return {
            'total_holdings_tonnes': round(total_tonnes, 0),
            'total_countries': total_countries,
            'latest_year_purchases': recent.tonnes if recent else 0,
            'previous_year_purchases': prev_year.tonnes if prev_year else 0,
            'yoy_change_tonnes': round(recent.tonnes - prev_year.tonnes, 0) if recent and prev_year else 0,
            'consecutive_buying_years': dedollarization.components.get('consecutive_buying_years', 0),
            'dedollarization_score': dedollarization.score,
            'dedollarization_interpretation': dedollarization.interpretation,
            'top_holder': latest[0].country_name if latest else None,
            'top_holder_tonnes': latest[0].tonnes if latest else 0,
        }


# Singleton instance
_cb_gold_db: Optional[CentralBankGoldDB] = None


def get_cb_gold_db() -> CentralBankGoldDB:
    """Get or create the CentralBankGoldDB singleton."""
    global _cb_gold_db
    if _cb_gold_db is None:
        _cb_gold_db = CentralBankGoldDB()
    return _cb_gold_db
