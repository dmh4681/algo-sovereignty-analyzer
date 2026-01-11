"""
Inflation-Adjusted Price Data Module

Provides historical CPI, M2 money supply, and gold/silver price data
for inflation-adjusted charting and purchasing power analysis.

Data Sources:
- FRED API (Federal Reserve Economic Data) for CPI and M2
- Historical gold/silver prices seeded from LBMA/Kitco data
"""

import sqlite3
import os
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
import json

# Try to import requests for FRED API calls
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# Database path - uses DATA_DIR env var for Railway/production
def _get_data_dir() -> str:
    """Get data directory from env var or default to project data folder."""
    env_data_dir = os.environ.get('DATA_DIR')
    if env_data_dir:
        return env_data_dir
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


DATA_DIR = _get_data_dir()
DB_PATH = os.path.join(DATA_DIR, 'inflation_data.db')

# FRED API configuration
FRED_API_KEY = os.environ.get('FRED_API_KEY', '')
FRED_BASE_URL = 'https://api.stlouisfed.org/fred/series/observations'

# FRED Series IDs
FRED_CPI_SERIES = 'CPIAUCSL'  # Consumer Price Index for All Urban Consumers
FRED_M2_SERIES = 'M2SL'  # M2 Money Stock (Billions of Dollars)


# Historical seed data - Monthly CPI values (1970-2025)
# CPI-U Index (1982-84 = 100)
CPI_SEED_DATA = [
    # 1970
    ('1970-01', 37.8), ('1970-06', 38.8), ('1970-12', 39.8),
    # 1971
    ('1971-06', 40.6), ('1971-12', 41.1),
    # 1972
    ('1972-06', 41.7), ('1972-12', 42.5),
    # 1973
    ('1973-06', 44.2), ('1973-12', 46.2),
    # 1974
    ('1974-06', 49.0), ('1974-12', 52.5),
    # 1975
    ('1975-06', 53.6), ('1975-12', 55.5),
    # 1976
    ('1976-06', 56.8), ('1976-12', 58.2),
    # 1977
    ('1977-06', 60.4), ('1977-12', 62.1),
    # 1978
    ('1978-06', 65.2), ('1978-12', 68.3),
    # 1979
    ('1979-06', 72.3), ('1979-12', 76.7),
    # 1980 - Gold/Silver peak year
    ('1980-01', 77.8), ('1980-03', 80.1), ('1980-06', 82.7), ('1980-12', 86.3),
    # 1981
    ('1981-06', 90.6), ('1981-12', 94.0),
    # 1982
    ('1982-06', 97.0), ('1982-12', 97.6),
    # 1983
    ('1983-06', 99.5), ('1983-12', 101.3),
    # 1984
    ('1984-06', 103.7), ('1984-12', 105.3),
    # 1985
    ('1985-06', 107.6), ('1985-12', 109.3),
    # 1986
    ('1986-06', 109.5), ('1986-12', 110.5),
    # 1987
    ('1987-06', 113.5), ('1987-12', 115.4),
    # 1988
    ('1988-06', 118.0), ('1988-12', 120.5),
    # 1989
    ('1989-06', 124.1), ('1989-12', 126.1),
    # 1990
    ('1990-06', 129.9), ('1990-12', 133.8),
    # 1991
    ('1991-06', 136.0), ('1991-12', 137.9),
    # 1992
    ('1992-06', 140.2), ('1992-12', 141.9),
    # 1993
    ('1993-06', 144.4), ('1993-12', 145.8),
    # 1994
    ('1994-06', 148.0), ('1994-12', 149.7),
    # 1995
    ('1995-06', 152.5), ('1995-12', 153.5),
    # 1996
    ('1996-06', 156.7), ('1996-12', 158.6),
    # 1997
    ('1997-06', 160.3), ('1997-12', 161.3),
    # 1998
    ('1998-06', 163.0), ('1998-12', 163.9),
    # 1999
    ('1999-06', 166.2), ('1999-12', 168.3),
    # 2000
    ('2000-06', 172.4), ('2000-12', 174.0),
    # 2001 - Gold bear market bottom
    ('2001-04', 176.2), ('2001-06', 178.0), ('2001-12', 177.4),
    # 2002
    ('2002-06', 179.8), ('2002-12', 180.9),
    # 2003
    ('2003-06', 183.7), ('2003-12', 184.3),
    # 2004
    ('2004-06', 189.1), ('2004-12', 190.3),
    # 2005
    ('2005-06', 194.5), ('2005-12', 196.8),
    # 2006
    ('2006-06', 202.9), ('2006-12', 201.8),
    # 2007
    ('2007-06', 208.4), ('2007-12', 210.0),
    # 2008 - Financial crisis
    ('2008-06', 218.8), ('2008-12', 210.2),
    # 2009
    ('2009-06', 215.7), ('2009-12', 216.7),
    # 2010
    ('2010-06', 217.2), ('2010-12', 219.2),
    # 2011 - Gold peak
    ('2011-06', 225.7), ('2011-09', 226.9), ('2011-12', 225.7),
    # 2012
    ('2012-06', 229.5), ('2012-12', 231.1),
    # 2013
    ('2013-06', 233.5), ('2013-12', 234.8),
    # 2014
    ('2014-06', 238.3), ('2014-12', 236.2),
    # 2015
    ('2015-06', 238.6), ('2015-12', 237.8),
    # 2016
    ('2016-06', 241.0), ('2016-12', 242.8),
    # 2017
    ('2017-06', 244.9), ('2017-12', 247.8),
    # 2018
    ('2018-06', 251.9), ('2018-12', 252.0),
    # 2019
    ('2019-06', 256.1), ('2019-12', 257.9),
    # 2020 - COVID / Gold ATH
    ('2020-01', 258.7), ('2020-06', 257.8), ('2020-08', 259.9), ('2020-12', 261.6),
    # 2021
    ('2021-06', 271.7), ('2021-12', 280.1),
    # 2022 - High inflation
    ('2022-06', 296.3), ('2022-12', 298.0),
    # 2023
    ('2023-06', 305.1), ('2023-12', 308.7),
    # 2024
    ('2024-06', 314.2), ('2024-12', 315.6),
    # 2025 - Data from FRED CPIAUCSL (1982-84=100)
    ('2025-01', 316.2), ('2025-06', 320.5), ('2025-09', 324.4), ('2025-11', 325.0),
    # 2026 - Estimated based on recent trend (~2.5% annual inflation)
    ('2026-01', 327.0),
]

# Historical M2 Money Supply (Billions USD)
M2_SEED_DATA = [
    # 1970
    ('1970-01', 587), ('1970-06', 601), ('1970-12', 628),
    # 1975
    ('1975-01', 1017), ('1975-06', 1043), ('1975-12', 1092),
    # 1980
    ('1980-01', 1543), ('1980-06', 1612), ('1980-12', 1660),
    # 1985
    ('1985-01', 2495), ('1985-06', 2557), ('1985-12', 2644),
    # 1990
    ('1990-01', 3222), ('1990-06', 3278), ('1990-12', 3339),
    # 1995
    ('1995-01', 3562), ('1995-06', 3706), ('1995-12', 3850),
    # 2000
    ('2000-01', 4662), ('2000-06', 4765), ('2000-12', 4945),
    # 2005
    ('2005-01', 6412), ('2005-06', 6529), ('2005-12', 6695),
    # 2008 - Financial crisis
    ('2008-01', 7531), ('2008-06', 7690), ('2008-12', 8200),
    # 2010
    ('2010-01', 8480), ('2010-06', 8582), ('2010-12', 8836),
    # 2015
    ('2015-01', 11694), ('2015-06', 11876), ('2015-12', 12348),
    # 2020 - COVID money printing
    ('2020-01', 15447), ('2020-06', 18306), ('2020-12', 19402),
    # 2021
    ('2021-01', 19631), ('2021-06', 20376), ('2021-12', 21638),
    # 2022
    ('2022-01', 21688), ('2022-06', 21576), ('2022-12', 21210),
    # 2023
    ('2023-01', 21090), ('2023-06', 20867), ('2023-12', 20896),
    # 2024
    ('2024-01', 20836), ('2024-06', 21027), ('2024-12', 21437),
    # 2025 - Data from FRED M2SL
    ('2025-01', 21560), ('2025-06', 21800), ('2025-09', 22100), ('2025-11', 22322),
    # 2026 - Estimated based on recent trend
    ('2026-01', 22500),
]

# Historical Gold Prices (USD per troy oz) - Monthly averages
GOLD_SEED_DATA = [
    # 1970 - Before Nixon shock
    ('1970-01', 35.0), ('1970-06', 35.5), ('1970-12', 37.4),
    # 1971 - Nixon ends gold standard August 15
    ('1971-06', 40.1), ('1971-08', 43.0), ('1971-12', 43.5),
    # 1972
    ('1972-06', 63.8), ('1972-12', 64.9),
    # 1973
    ('1973-06', 120.0), ('1973-12', 112.0),
    # 1974
    ('1974-06', 160.0), ('1974-12', 183.0),
    # 1975
    ('1975-06', 166.0), ('1975-12', 140.0),
    # 1976
    ('1976-06', 126.0), ('1976-12', 134.0),
    # 1977
    ('1977-06', 142.0), ('1977-12', 165.0),
    # 1978
    ('1978-06', 185.0), ('1978-12', 208.0),
    # 1979
    ('1979-06', 280.0), ('1979-12', 512.0),
    # 1980 - All-time high (nominal) - Peak was $850 on Jan 21, 1980
    ('1980-01', 850.0), ('1980-03', 550.0), ('1980-06', 650.0), ('1980-09', 674.0), ('1980-12', 590.0),
    # 1981
    ('1981-06', 460.0), ('1981-12', 400.0),
    # 1982
    ('1982-06', 315.0), ('1982-12', 448.0),
    # 1983
    ('1983-06', 413.0), ('1983-12', 382.0),
    # 1984
    ('1984-06', 377.0), ('1984-12', 320.0),
    # 1985
    ('1985-06', 317.0), ('1985-12', 325.0),
    # 1986
    ('1986-06', 343.0), ('1986-12', 391.0),
    # 1987
    ('1987-06', 450.0), ('1987-12', 485.0),
    # 1988
    ('1988-06', 451.0), ('1988-12', 418.0),
    # 1989
    ('1989-06', 368.0), ('1989-12', 401.0),
    # 1990
    ('1990-06', 352.0), ('1990-12', 378.0),
    # 1991
    ('1991-06', 366.0), ('1991-12', 361.0),
    # 1992
    ('1992-06', 340.0), ('1992-12', 334.0),
    # 1993
    ('1993-06', 372.0), ('1993-12', 383.0),
    # 1994
    ('1994-06', 386.0), ('1994-12', 383.0),
    # 1995
    ('1995-06', 387.0), ('1995-12', 387.0),
    # 1996
    ('1996-06', 385.0), ('1996-12', 369.0),
    # 1997
    ('1997-06', 340.0), ('1997-12', 290.0),
    # 1998
    ('1998-06', 292.0), ('1998-12', 291.0),
    # 1999
    ('1999-06', 261.0), ('1999-12', 290.0),
    # 2000
    ('2000-06', 286.0), ('2000-12', 272.0),
    # 2001 - Bear market bottom
    ('2001-04', 256.0), ('2001-06', 271.0), ('2001-12', 276.0),
    # 2002
    ('2002-06', 322.0), ('2002-12', 332.0),
    # 2003
    ('2003-06', 356.0), ('2003-12', 416.0),
    # 2004
    ('2004-06', 394.0), ('2004-12', 435.0),
    # 2005
    ('2005-06', 430.0), ('2005-12', 510.0),
    # 2006
    ('2006-06', 596.0), ('2006-12', 629.0),
    # 2007
    ('2007-06', 655.0), ('2007-12', 803.0),
    # 2008 - Financial crisis
    ('2008-06', 889.0), ('2008-12', 816.0),
    # 2009
    ('2009-06', 945.0), ('2009-12', 1135.0),
    # 2010
    ('2010-06', 1233.0), ('2010-12', 1390.0),
    # 2011 - Pre-2020 peak
    ('2011-06', 1529.0), ('2011-09', 1895.0), ('2011-12', 1652.0),
    # 2012
    ('2012-06', 1597.0), ('2012-12', 1684.0),
    # 2013
    ('2013-06', 1342.0), ('2013-12', 1225.0),
    # 2014
    ('2014-06', 1281.0), ('2014-12', 1201.0),
    # 2015
    ('2015-06', 1182.0), ('2015-12', 1068.0),
    # 2016
    ('2016-06', 1276.0), ('2016-12', 1159.0),
    # 2017
    ('2017-06', 1256.0), ('2017-12', 1291.0),
    # 2018
    ('2018-06', 1279.0), ('2018-12', 1249.0),
    # 2019
    ('2019-06', 1359.0), ('2019-12', 1481.0),
    # 2020 - COVID ATH
    ('2020-01', 1560.0), ('2020-06', 1771.0), ('2020-08', 2067.0), ('2020-12', 1887.0),
    # 2021
    ('2021-06', 1780.0), ('2021-12', 1798.0),
    # 2022
    ('2022-06', 1837.0), ('2022-12', 1800.0),
    # 2023
    ('2023-06', 1940.0), ('2023-12', 2050.0),
    # 2024 - New ATHs
    ('2024-06', 2350.0), ('2024-09', 2650.0), ('2024-12', 2625.0),
    # 2025 - Rally to new highs (gold surged past $4,000)
    ('2025-01', 2800.0), ('2025-03', 3050.0), ('2025-06', 3400.0),
    ('2025-09', 4000.0), ('2025-12', 4400.0),
    # 2026 - Current (verified Jan 2026 ~$4,523/oz from Kitco)
    ('2026-01', 4523.0),
]

# Historical Silver Prices (USD per troy oz) - Monthly averages
SILVER_SEED_DATA = [
    # 1970
    ('1970-01', 1.80), ('1970-06', 1.77), ('1970-12', 1.64),
    # 1975
    ('1975-01', 4.40), ('1975-06', 4.50), ('1975-12', 4.10),
    # 1980 - Hunt brothers spike - Peak was $49.45 on Jan 18, 1980
    ('1980-01', 49.45), ('1980-03', 21.0), ('1980-06', 17.0), ('1980-12', 16.0),
    # 1985
    ('1985-06', 6.10), ('1985-12', 5.90),
    # 1990
    ('1990-06', 4.95), ('1990-12', 4.15),
    # 1995
    ('1995-06', 5.40), ('1995-12', 5.20),
    # 2000
    ('2000-06', 5.00), ('2000-12', 4.60),
    # 2001
    ('2001-06', 4.35), ('2001-12', 4.50),
    # 2005
    ('2005-06', 7.30), ('2005-12', 8.80),
    # 2008
    ('2008-06', 17.0), ('2008-12', 10.5),
    # 2010
    ('2010-06', 18.5), ('2010-12', 29.0),
    # 2011 - Near $50
    ('2011-04', 48.0), ('2011-06', 36.0), ('2011-12', 29.0),
    # 2015
    ('2015-06', 16.0), ('2015-12', 14.0),
    # 2020
    ('2020-01', 18.0), ('2020-06', 18.0), ('2020-08', 28.0), ('2020-12', 26.5),
    # 2021
    ('2021-06', 26.0), ('2021-12', 23.0),
    # 2022
    ('2022-06', 22.0), ('2022-12', 24.0),
    # 2023
    ('2023-06', 24.0), ('2023-12', 24.5),
    # 2024
    ('2024-06', 29.0), ('2024-09', 31.5), ('2024-12', 29.0),
    # 2025 - Silver rally following gold
    ('2025-01', 32.0), ('2025-03', 36.0), ('2025-06', 45.0),
    ('2025-09', 60.0), ('2025-12', 75.0),
    # 2026 - Current (verified Jan 2026 ~$80.65/oz from Kitco)
    ('2026-01', 80.65),
]


@dataclass
class InflationDataPoint:
    """A single month's economic data."""
    date: str  # YYYY-MM format
    cpi: Optional[float]  # CPI-U index value
    m2: Optional[float]  # M2 in billions
    gold_price: Optional[float]  # USD per oz
    silver_price: Optional[float]  # USD per oz

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AdjustedPrice:
    """Price adjusted to a base year."""
    date: str
    nominal_price: float
    real_price: float  # Adjusted to base year dollars
    base_year: int
    cpi_at_date: float
    cpi_at_base: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class M2Comparison:
    """Gold/Silver price vs M2 money supply."""
    date: str
    gold_price: float
    silver_price: float
    m2_billions: float
    gold_m2_ratio: float  # (gold_price * 1000) / m2 - normalized
    silver_m2_ratio: float
    gold_m2_ratio_pct_of_peak: float  # Current ratio as % of 1980 peak

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InflationDataDB:
    """Manages inflation and monetary data storage."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        print(f"[InflationDataDB] Using database: {self.db_path}")
        self._init_db()

    def _init_db(self):
        """Initialize the database and create tables if needed."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS inflation_data (
                    date TEXT PRIMARY KEY,
                    cpi REAL,
                    m2 REAL,
                    gold_price REAL,
                    silver_price REAL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Index for range queries
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_inflation_date
                ON inflation_data(date DESC)
            ''')

            conn.commit()

            # Seed with initial data if empty
            cursor = conn.execute('SELECT COUNT(*) FROM inflation_data')
            if cursor.fetchone()[0] == 0:
                self._seed_data(conn)

    def _seed_data(self, conn: sqlite3.Connection):
        """Populate database with historical seed data."""
        print("[InflationDataDB] Seeding historical data...")

        # Combine all data into unified records
        all_dates = set()
        cpi_map = {d: v for d, v in CPI_SEED_DATA}
        m2_map = {d: v for d, v in M2_SEED_DATA}
        gold_map = {d: v for d, v in GOLD_SEED_DATA}
        silver_map = {d: v for d, v in SILVER_SEED_DATA}

        all_dates.update(cpi_map.keys())
        all_dates.update(m2_map.keys())
        all_dates.update(gold_map.keys())
        all_dates.update(silver_map.keys())

        count = 0
        for date_str in sorted(all_dates):
            conn.execute('''
                INSERT OR REPLACE INTO inflation_data (date, cpi, m2, gold_price, silver_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                date_str,
                cpi_map.get(date_str),
                m2_map.get(date_str),
                gold_map.get(date_str),
                silver_map.get(date_str)
            ))
            count += 1

        conn.commit()
        print(f"[InflationDataDB] Seeded {count} data points")

    def reseed(self) -> int:
        """Clear and reseed the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM inflation_data')
            self._seed_data(conn)
        return len(set(d for d, _ in CPI_SEED_DATA) |
                   set(d for d, _ in M2_SEED_DATA) |
                   set(d for d, _ in GOLD_SEED_DATA) |
                   set(d for d, _ in SILVER_SEED_DATA))

    def get_all_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[InflationDataPoint]:
        """Get all inflation data, optionally filtered by date range."""
        query = 'SELECT date, cpi, m2, gold_price, silver_price FROM inflation_data'
        params = []

        conditions = []
        if start_date:
            conditions.append('date >= ?')
            params.append(start_date)
        if end_date:
            conditions.append('date <= ?')
            params.append(end_date)

        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)

        query += ' ORDER BY date ASC'

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return [
                InflationDataPoint(
                    date=row[0],
                    cpi=row[1],
                    m2=row[2],
                    gold_price=row[3],
                    silver_price=row[4]
                )
                for row in cursor.fetchall()
            ]

    def get_cpi_at_date(self, date_str: str) -> Optional[float]:
        """Get CPI value for a specific date (or closest prior)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT cpi FROM inflation_data
                WHERE date <= ? AND cpi IS NOT NULL
                ORDER BY date DESC LIMIT 1
            ''', (date_str,))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_cpi_for_year(self, year: int) -> Optional[float]:
        """Get CPI value for January of a given year."""
        date_str = f"{year}-01"
        return self.get_cpi_at_date(date_str)

    def get_latest_data(self) -> Optional[InflationDataPoint]:
        """Get the most recent data point."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT date, cpi, m2, gold_price, silver_price
                FROM inflation_data
                ORDER BY date DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            if row:
                return InflationDataPoint(
                    date=row[0],
                    cpi=row[1],
                    m2=row[2],
                    gold_price=row[3],
                    silver_price=row[4]
                )
            return None

    def calculate_inflation_adjusted_prices(
        self,
        metal: str,
        base_year: int = 2024
    ) -> List[AdjustedPrice]:
        """
        Calculate inflation-adjusted prices for gold or silver.

        Args:
            metal: 'gold' or 'silver'
            base_year: Year to adjust prices to (in that year's dollars)

        Returns:
            List of AdjustedPrice objects with both nominal and real prices
        """
        if metal not in ('gold', 'silver'):
            raise ValueError("metal must be 'gold' or 'silver'")

        # Get base year CPI
        cpi_base = self.get_cpi_for_year(base_year)
        if not cpi_base:
            raise ValueError(f"No CPI data for base year {base_year}")

        # Get all data points
        data = self.get_all_data()
        price_field = 'gold_price' if metal == 'gold' else 'silver_price'

        results = []
        last_cpi = None

        for point in data:
            price = point.gold_price if metal == 'gold' else point.silver_price
            if price is None:
                continue

            # Get CPI for this date (use last known if not available)
            cpi = point.cpi if point.cpi else last_cpi
            if cpi:
                last_cpi = cpi
            else:
                continue

            # Adjust price: real_price = nominal_price × (CPI_base / CPI_date)
            real_price = price * (cpi_base / cpi)

            results.append(AdjustedPrice(
                date=point.date,
                nominal_price=round(price, 2),
                real_price=round(real_price, 2),
                base_year=base_year,
                cpi_at_date=round(cpi, 1),
                cpi_at_base=round(cpi_base, 1)
            ))

        return results

    def get_m2_comparison(self) -> List[M2Comparison]:
        """
        Get gold/silver prices compared to M2 money supply.

        The gold/M2 ratio shows if gold is cheap or expensive relative to
        money printing. Higher ratio = gold is expensive vs M2.

        1980 peak ratio is used as benchmark (gold was expensive then).
        """
        data = self.get_all_data()

        # Calculate 1980 peak ratio for reference
        peak_ratio = None
        for point in data:
            if point.date.startswith('1980-01') and point.gold_price and point.m2:
                peak_ratio = (point.gold_price * 1000) / point.m2
                break

        if not peak_ratio:
            peak_ratio = 550  # Fallback: ~$850 gold / $1.54T M2 ≈ 552

        results = []
        last_m2 = None

        for point in data:
            if point.gold_price is None:
                continue

            m2 = point.m2 if point.m2 else last_m2
            if m2:
                last_m2 = m2
            else:
                continue

            gold_ratio = (point.gold_price * 1000) / m2  # Normalize
            silver_ratio = ((point.silver_price or 0) * 1000) / m2

            results.append(M2Comparison(
                date=point.date,
                gold_price=round(point.gold_price, 2),
                silver_price=round(point.silver_price or 0, 2),
                m2_billions=round(m2, 0),
                gold_m2_ratio=round(gold_ratio, 2),
                silver_m2_ratio=round(silver_ratio, 4),
                gold_m2_ratio_pct_of_peak=round((gold_ratio / peak_ratio) * 100, 1)
            ))

        return results

    def calculate_purchasing_power(self, from_year: int = 1970) -> Dict[str, Any]:
        """
        Calculate dollar purchasing power decline from a given year.

        Returns stats on how much value the dollar has lost.
        """
        cpi_from = self.get_cpi_for_year(from_year)
        latest = self.get_latest_data()

        if not cpi_from or not latest or not latest.cpi:
            return {'error': 'Insufficient data'}

        cpi_now = latest.cpi

        # $1 from {from_year} is worth this much today (in purchasing power)
        dollar_value_now = cpi_from / cpi_now

        # Cumulative inflation
        cumulative_inflation = ((cpi_now - cpi_from) / cpi_from) * 100

        # Years
        current_year = int(latest.date[:4])
        years = current_year - from_year

        # Average annual inflation
        avg_annual = (cumulative_inflation / years) if years > 0 else 0

        return {
            'from_year': from_year,
            'to_date': latest.date,
            'dollar_value_today': round(dollar_value_now, 4),
            'purchasing_power_lost_pct': round((1 - dollar_value_now) * 100, 1),
            'cumulative_inflation_pct': round(cumulative_inflation, 1),
            'average_annual_inflation_pct': round(avg_annual, 2),
            'cpi_from': round(cpi_from, 1),
            'cpi_now': round(cpi_now, 1)
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the dashboard."""
        latest = self.get_latest_data()
        purchasing_power = self.calculate_purchasing_power(1970)

        # Get 1980 gold peak for comparison
        cpi_1980 = self.get_cpi_for_year(1980)
        gold_1980 = 850  # January 1980 peak ($850 on Jan 21, 1980)

        if latest and latest.cpi and cpi_1980:
            # What is 1980 gold peak in today's dollars?
            gold_1980_in_todays_dollars = gold_1980 * (latest.cpi / cpi_1980)

            # Has gold beaten its 1980 high in real terms?
            current_gold = latest.gold_price or 0
            real_vs_1980_peak = (current_gold / gold_1980_in_todays_dollars) * 100 if gold_1980_in_todays_dollars > 0 else 0
        else:
            gold_1980_in_todays_dollars = 0
            real_vs_1980_peak = 0

        return {
            'latest_date': latest.date if latest else None,
            'current_cpi': round(latest.cpi, 1) if latest and latest.cpi else None,
            'current_m2_billions': round(latest.m2, 0) if latest and latest.m2 else None,
            'current_gold': round(latest.gold_price, 2) if latest and latest.gold_price else None,
            'current_silver': round(latest.silver_price, 2) if latest and latest.silver_price else None,
            'gold_1980_peak_in_todays_dollars': round(gold_1980_in_todays_dollars, 0),
            'current_gold_vs_1980_real_pct': round(real_vs_1980_peak, 1),
            'purchasing_power': purchasing_power
        }


# Singleton instance
_inflation_db: Optional[InflationDataDB] = None


def get_inflation_db() -> InflationDataDB:
    """Get or create the InflationDataDB singleton."""
    global _inflation_db
    if _inflation_db is None:
        _inflation_db = InflationDataDB()
    return _inflation_db
