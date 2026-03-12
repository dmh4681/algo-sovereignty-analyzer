"""
Miner Earnings Calendar Module

Tracks quarterly earnings events for gold and silver mining companies.
Includes historical beat/miss data, price reactions, and upcoming events.

Data Source: SEC EDGAR XBRL API (real filings) — not fabricated.
  - EPS and revenue are sourced from actual 10-Q / 10-K / 40-F SEC filings.
  - Production (oz) and AISC data are NOT in SEC filings; those fields require
    manual entry from company press releases and are left null until populated.
  - Stock price data is not sourced here; populate via the update_event() API.
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

    # Mining-specific (from press releases / earnings calls — not in SEC filings)
    production_actual: Optional[int] = None  # oz
    production_guidance: Optional[int] = None
    aisc_actual: Optional[float] = None
    aisc_guidance: Optional[float] = None

    # Post-earnings price data (populated separately via market data)
    price_before: Optional[float] = None
    price_1d_after: Optional[float] = None
    price_5d_after: Optional[float] = None
    price_30d_after: Optional[float] = None

    # Metadata
    transcript_url: Optional[str] = None
    press_release_url: Optional[str] = None
    data_source: Optional[str] = None  # 'sec_edgar', 'manual', 'estimated'
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
            'data_source': self.data_source,
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
        if actual is None or estimate is None:
            return None
        return actual >= estimate

    def _calc_aisc_beat(self) -> Optional[bool]:
        """For AISC, lower is better so beat means actual < guidance."""
        if self.aisc_actual is None or self.aisc_guidance is None:
            return None
        return self.aisc_actual <= self.aisc_guidance

    def _calc_price_change(self, before: Optional[float], after: Optional[float]) -> Optional[float]:
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
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema and populate from SEC EDGAR on first run."""
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
                    data_source TEXT DEFAULT 'unknown',
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

            # Run schema migration to add data_source if it doesn't exist (for existing DBs)
            self._migrate_schema(conn)

            # Populate from SEC EDGAR on first run
            cursor = conn.execute('SELECT COUNT(*) FROM earnings_events')
            count = cursor.fetchone()[0]
            if count == 0:
                populated = self._populate_from_edgar(conn)
                if not populated:
                    print("SEC EDGAR unavailable — earnings calendar will be empty until refreshed")
                    print("Run POST /api/v1/earnings/refresh to populate from SEC EDGAR")
        finally:
            conn.close()

    def _migrate_schema(self, conn: sqlite3.Connection):
        """Add new columns to existing databases without losing data."""
        try:
            conn.execute("ALTER TABLE earnings_events ADD COLUMN data_source TEXT DEFAULT 'unknown'")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

    def _populate_from_edgar(self, conn: sqlite3.Connection) -> bool:
        """
        Fetch real earnings data from SEC EDGAR and populate the database.

        Returns True if any records were inserted, False if SEC EDGAR was unavailable.
        """
        try:
            from core.sec_edgar import (
                SECEdgarClient, TICKER_METAL_MAP, TICKER_NAME_MAP, build_upcoming_stubs
            )
        except ImportError:
            print("sec_edgar module not available")
            return False

        client = SECEdgarClient()
        print("Fetching real earnings data from SEC EDGAR...")

        total_inserted = 0

        all_records = client.fetch_all_miners(min_year=2022)
        for ticker, records in all_records.items():
            metal = TICKER_METAL_MAP.get(ticker, "unknown")
            company_name = TICKER_NAME_MAP.get(ticker, ticker)

            for rec in records:
                try:
                    conn.execute('''
                        INSERT OR IGNORE INTO earnings_events (
                            ticker, metal, company_name, quarter, earnings_date,
                            time_of_day, is_confirmed,
                            eps_actual, revenue_actual,
                            press_release_url, data_source
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        ticker, metal, company_name, rec.quarter, rec.filed_date,
                        'pre-market', 1,
                        rec.eps_actual, rec.revenue_actual,
                        rec.edgar_url, 'sec_edgar',
                    ))
                    total_inserted += 1
                except sqlite3.IntegrityError:
                    pass  # Skip duplicates

        # Add upcoming stub records (estimated dates, no financial data)
        stubs = build_upcoming_stubs(quarters=2)
        for stub in stubs:
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO earnings_events (
                        ticker, metal, company_name, quarter, earnings_date,
                        time_of_day, is_confirmed, data_source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stub["ticker"], stub["metal"], stub["company_name"],
                    stub["quarter"], stub["earnings_date"], stub["time_of_day"],
                    0, stub["data_source"],
                ))
            except sqlite3.IntegrityError:
                pass  # Upcoming stub already exists

        conn.commit()
        print(f"Populated {total_inserted} earnings records from SEC EDGAR")
        return total_inserted > 0

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

        completed = [e for e in events if e.eps_actual is not None]
        if not completed:
            return None

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

        reactions_1d = [
            ((e.price_1d_after - e.price_before) / e.price_before * 100)
            for e in completed
            if e.price_before and e.price_1d_after and e.price_before > 0
        ]

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

            eps_beats = sum(1 for e in completed if e.eps_actual and e.eps_estimate and e.eps_actual >= e.eps_estimate)
            eps_total = sum(1 for e in completed if e.eps_actual and e.eps_estimate)

            rev_beats = sum(1 for e in completed if e.revenue_actual and e.revenue_estimate and e.revenue_actual >= e.revenue_estimate)
            rev_total = sum(1 for e in completed if e.revenue_actual and e.revenue_estimate)

            reactions = [
                ((e.price_1d_after - e.price_before) / e.price_before * 100)
                for e in completed
                if e.price_before and e.price_1d_after and e.price_before > 0
            ]

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

    def create_event(self, event: 'EarningsEvent') -> Optional[int]:
        """Create a new earnings event."""
        conn = self._get_conn()
        try:
            cursor = conn.execute('''
                INSERT INTO earnings_events (
                    ticker, metal, company_name, quarter, earnings_date, time_of_day,
                    is_confirmed, eps_actual, eps_estimate, revenue_actual, revenue_estimate,
                    production_actual, production_guidance, aisc_actual, aisc_guidance,
                    price_before, price_1d_after, price_5d_after, price_30d_after,
                    transcript_url, press_release_url, data_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.ticker.upper(), event.metal, event.company_name, event.quarter,
                event.earnings_date, event.time_of_day, 1 if event.is_confirmed else 0,
                event.eps_actual, event.eps_estimate, event.revenue_actual, event.revenue_estimate,
                event.production_actual, event.production_guidance, event.aisc_actual, event.aisc_guidance,
                event.price_before, event.price_1d_after, event.price_5d_after, event.price_30d_after,
                event.transcript_url, event.press_release_url,
                event.data_source or 'manual',
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
            allowed_fields = [
                'eps_actual', 'eps_estimate', 'revenue_actual', 'revenue_estimate',
                'production_actual', 'production_guidance', 'aisc_actual', 'aisc_guidance',
                'price_before', 'price_1d_after', 'price_5d_after', 'price_30d_after',
                'earnings_date', 'time_of_day', 'is_confirmed', 'transcript_url',
                'press_release_url', 'data_source',
            ]

            set_clauses = []
            values = []
            for f, v in updates.items():
                if f in allowed_fields:
                    set_clauses.append(f'{f} = ?')
                    values.append(v)

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

    def refresh_from_edgar(self) -> Dict[str, int]:
        """
        Re-fetch data from SEC EDGAR and update the database.

        Existing records are updated with fresh SEC data (eps_actual, revenue_actual,
        press_release_url, data_source). New quarters are inserted. Records already
        in the DB with manual corrections are preserved for non-SEC fields.

        Returns dict with 'inserted' and 'updated' counts.
        """
        try:
            from core.sec_edgar import (
                SECEdgarClient, TICKER_METAL_MAP, TICKER_NAME_MAP, build_upcoming_stubs
            )
        except ImportError:
            raise RuntimeError("sec_edgar module not available")

        client = SECEdgarClient()
        print("Refreshing earnings data from SEC EDGAR...")

        inserted = 0
        updated = 0

        conn = self._get_conn()
        try:
            all_records = client.fetch_all_miners(min_year=2022)
            for ticker, records in all_records.items():
                metal = TICKER_METAL_MAP.get(ticker, "unknown")
                company_name = TICKER_NAME_MAP.get(ticker, ticker)

                for rec in records:
                    # Try insert first
                    try:
                        conn.execute('''
                            INSERT INTO earnings_events (
                                ticker, metal, company_name, quarter, earnings_date,
                                time_of_day, is_confirmed,
                                eps_actual, revenue_actual,
                                press_release_url, data_source
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            ticker, metal, company_name, rec.quarter, rec.filed_date,
                            'pre-market', 1,
                            rec.eps_actual, rec.revenue_actual,
                            rec.edgar_url, 'sec_edgar',
                        ))
                        inserted += 1
                    except sqlite3.IntegrityError:
                        # Record exists — update SEC-sourced fields only
                        conn.execute('''
                            UPDATE earnings_events
                            SET eps_actual = ?,
                                revenue_actual = ?,
                                press_release_url = ?,
                                data_source = 'sec_edgar',
                                updated_at = CURRENT_TIMESTAMP
                            WHERE ticker = ? AND quarter = ?
                              AND data_source != 'manual'
                        ''', (rec.eps_actual, rec.revenue_actual, rec.edgar_url, ticker, rec.quarter))
                        updated += 1

            # Refresh upcoming stubs (don't overwrite confirmed events)
            stubs = build_upcoming_stubs(quarters=2)
            for stub in stubs:
                try:
                    conn.execute('''
                        INSERT OR IGNORE INTO earnings_events (
                            ticker, metal, company_name, quarter, earnings_date,
                            time_of_day, is_confirmed, data_source
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        stub["ticker"], stub["metal"], stub["company_name"],
                        stub["quarter"], stub["earnings_date"], stub["time_of_day"],
                        0, stub["data_source"],
                    ))
                except sqlite3.IntegrityError:
                    pass

            conn.commit()
        finally:
            conn.close()

        print(f"SEC EDGAR refresh: {inserted} inserted, {updated} updated")
        return {"inserted": inserted, "updated": updated}

    def reseed(self) -> int:
        """
        Clear all earnings data and re-populate from SEC EDGAR.

        This is a destructive operation that replaces all data with real
        SEC EDGAR filings data. Manual corrections will be lost.
        """
        conn = self._get_conn()
        try:
            conn.execute('DELETE FROM earnings_events')
            conn.commit()
            populated = self._populate_from_edgar(conn)
            if not populated:
                raise RuntimeError(
                    "SEC EDGAR unavailable — could not reseed. "
                    "Check network connectivity and try again."
                )
            cursor = conn.execute('SELECT COUNT(*) FROM earnings_events')
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def _row_to_event(self, row: sqlite3.Row) -> EarningsEvent:
        """Convert database row to EarningsEvent object."""
        # Handle both old schema (no data_source) and new schema
        try:
            data_source = row['data_source']
        except (IndexError, KeyError):
            data_source = 'unknown'

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
            data_source=data_source,
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
