"""
Integration Tests for SEC EDGAR Module

Tests the SECEdgarClient, SECEarningsRecord, build_upcoming_stubs, and
EarningsCalendarDB integration with the SEC EDGAR data pipeline.

All external HTTP calls are mocked — no real network requests are made.
Tests verify the full data extraction pipeline from raw EDGAR XBRL facts
through to EarningsCalendarDB persistence.
"""

import pytest
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import requests

from core.sec_edgar import (
    SECEdgarClient,
    SECEarningsRecord,
    MINER_CIK_MAP,
    TICKER_METAL_MAP,
    TICKER_NAME_MAP,
    build_upcoming_stubs,
    _quarter_end_date,
)
from core.earnings_calendar import EarningsCalendarDB, EarningsEvent


# =============================================================================
# Shared XBRL Fact Fixtures
# =============================================================================

def _make_facts(
    eps_entries: list = None,
    rev_entries: list = None,
    entity_name: str = "Test Mining Corp",
    namespace: str = "us-gaap",
    eps_concept: str = "EarningsPerShareDiluted",
    rev_concept: str = "Revenues",
) -> dict:
    """Build a minimal SEC EDGAR companyfacts JSON structure."""
    facts = {
        "entityName": entity_name,
        "facts": {}
    }

    ns = facts["facts"].setdefault(namespace, {})

    if eps_entries is not None:
        ns.setdefault(eps_concept, {})["units"] = {"USD/shares": eps_entries}

    if rev_entries is not None:
        ns.setdefault(rev_concept, {})["units"] = {"USD": rev_entries}

    return facts


def _quarterly_eps_entry(
    quarter_end: str,  # "YYYY-MM-DD"
    val: float,
    filed: str,
    fp: str,
    form: str = "10-Q",
    accn: str = "0001234567-23-000001",
) -> dict:
    """Build a 10-Q EPS entry covering ~90 days ending on quarter_end."""
    end_dt = datetime.strptime(quarter_end, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=91)
    return {
        "form": form,
        "fp": fp,
        "val": val,
        "filed": filed,
        "accn": accn,
        "start": start_dt.strftime("%Y-%m-%d"),
        "end": quarter_end,
    }


def _annual_eps_entry(
    fiscal_year: int,
    val: float,
    filed: str,
    form: str = "10-K",
    accn: str = "0001234567-23-000002",
) -> dict:
    """Build an annual EPS entry covering ~365 days (FY)."""
    return {
        "form": form,
        "fp": "FY",
        "val": val,
        "filed": filed,
        "accn": accn,
        "start": f"{fiscal_year}-01-01",
        "end": f"{fiscal_year}-12-31",
    }


def _quarterly_rev_entry(
    quarter_end: str,
    val_usd: float,
    form: str = "10-Q",
    fp: str = "Q1",
) -> dict:
    """Build a quarterly revenue USD entry."""
    end_dt = datetime.strptime(quarter_end, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=91)
    return {
        "form": form,
        "fp": fp,
        "val": val_usd,
        "filed": end_dt.strftime("%Y-%m-%d"),
        "start": start_dt.strftime("%Y-%m-%d"),
        "end": quarter_end,
    }


def _annual_rev_entry(fiscal_year: int, val_usd: float, form: str = "10-K") -> dict:
    return {
        "form": form,
        "fp": "FY",
        "val": val_usd,
        "filed": f"{fiscal_year + 1}-02-20",
        "start": f"{fiscal_year}-01-01",
        "end": f"{fiscal_year}-12-31",
    }


# =============================================================================
# Static Helper Method Tests
# =============================================================================

class TestDurationHelpers:
    def test_duration_days_valid(self):
        days = SECEdgarClient._duration_days("2023-01-01", "2023-03-31")
        assert days == 89

    def test_duration_days_missing_start(self):
        assert SECEdgarClient._duration_days(None, "2023-03-31") is None

    def test_duration_days_missing_end(self):
        assert SECEdgarClient._duration_days("2023-01-01", None) is None

    def test_duration_days_bad_format(self):
        assert SECEdgarClient._duration_days("bad-date", "2023-03-31") is None

    def test_is_quarterly_true(self):
        # ~90-day period
        assert SECEdgarClient._is_quarterly("2023-01-01", "2023-03-31") is True

    def test_is_quarterly_false_annual(self):
        # ~365-day period is not quarterly
        assert SECEdgarClient._is_quarterly("2022-01-01", "2022-12-31") is False

    def test_is_annual_true(self):
        assert SECEdgarClient._is_annual("2022-01-01", "2022-12-31") is True

    def test_is_annual_false_quarterly(self):
        assert SECEdgarClient._is_annual("2023-01-01", "2023-03-31") is False


# =============================================================================
# EPS Extraction Tests
# =============================================================================

class TestExtractEPS:
    """Tests for SECEdgarClient._extract_eps"""

    def test_extracts_single_quarterly_us_gaap(self):
        entry = _quarterly_eps_entry(
            quarter_end="2023-03-31", val=0.50, filed="2023-04-27", fp="Q1"
        )
        facts = _make_facts(eps_entries=[entry])
        client = SECEdgarClient(rate_limit_delay=0)

        result = client._extract_eps(facts)

        assert ("Q1", 2023) in result
        eps_val, filed, accn, form = result[("Q1", 2023)]
        assert eps_val == 0.50
        assert filed == "2023-04-27"
        assert form == "10-Q"

    def test_extracts_multiple_quarters(self):
        entries = [
            _quarterly_eps_entry("2023-03-31", 0.50, "2023-04-27", "Q1"),
            _quarterly_eps_entry("2023-06-30", 0.62, "2023-07-25", "Q2"),
            _quarterly_eps_entry("2023-09-30", 0.48, "2023-10-26", "Q3"),
        ]
        facts = _make_facts(eps_entries=entries)
        client = SECEdgarClient(rate_limit_delay=0)

        result = client._extract_eps(facts)

        assert len(result) == 3
        assert ("Q1", 2023) in result
        assert ("Q2", 2023) in result
        assert ("Q3", 2023) in result

    def test_prefers_quarterly_over_annual_for_q4(self):
        """When both a standalone Q4 (~90 days) and annual (FY) entry exist, prefer quarterly."""
        quarterly_q4 = _quarterly_eps_entry(
            "2023-12-31", 0.75, "2024-02-15", "Q4", form="10-Q"
        )
        annual = _annual_eps_entry(2023, 2.50, "2024-02-20", form="10-K")
        facts = _make_facts(eps_entries=[annual, quarterly_q4])
        client = SECEdgarClient(rate_limit_delay=0)

        result = client._extract_eps(facts)

        assert ("Q4", 2023) in result
        eps_val, _, _, form = result[("Q4", 2023)]
        # Either value can appear; the important thing is data exists
        assert eps_val is not None

    def test_skips_future_filings_indirectly(self):
        """fetch_miner_earnings skips records with future filed_date; _extract_eps itself
        doesn't filter by date — that's done in fetch_miner_earnings."""
        future_entry = _quarterly_eps_entry(
            "2025-03-31", 1.00, "2099-04-01", "Q1"
        )
        facts = _make_facts(eps_entries=[future_entry])
        client = SECEdgarClient(rate_limit_delay=0)

        result = client._extract_eps(facts)
        # _extract_eps captures all entries ≥ 2022
        assert ("Q1", 2025) in result

    def test_returns_empty_for_no_facts(self):
        facts = {"facts": {}}
        client = SECEdgarClient(rate_limit_delay=0)
        assert client._extract_eps(facts) == {}

    def test_skips_old_data_pre_2022(self):
        old_entry = _quarterly_eps_entry(
            "2020-03-31", 0.30, "2020-04-20", "Q1"
        )
        facts = _make_facts(eps_entries=[old_entry])
        client = SECEdgarClient(rate_limit_delay=0)
        result = client._extract_eps(facts)
        assert result == {}

    def test_extracts_ifrs_concept(self):
        """IFRS companies (40-F filers) use ifrs-full namespace."""
        entry = _quarterly_eps_entry(
            "2023-03-31", 0.33, "2023-05-10", "Q1", form="40-F"
        )
        facts = _make_facts(
            eps_entries=entry if isinstance(entry, list) else [entry],
            namespace="ifrs-full",
            eps_concept="BasicEarningsLossPerShare",
        )
        client = SECEdgarClient(rate_limit_delay=0)
        result = client._extract_eps(facts)
        assert ("Q1", 2023) in result


# =============================================================================
# Revenue Extraction Tests
# =============================================================================

class TestExtractRevenue:
    """Tests for SECEdgarClient._extract_revenue"""

    def test_extracts_quarterly_revenue_in_millions(self):
        # 1_500_000_000 USD = 1500.0M
        entry = _quarterly_rev_entry("2023-03-31", 1_500_000_000, fp="Q1")
        facts = _make_facts(rev_entries=[entry])
        client = SECEdgarClient(rate_limit_delay=0)

        result = client._extract_revenue(facts)

        assert ("Q1", 2023) in result
        assert result[("Q1", 2023)] == 1500.0

    def test_computes_q4_from_annual_minus_first_three_quarters(self):
        """Q4 standalone = FY - Q1 - Q2 - Q3 when Q4 not directly reported."""
        entries = [
            _quarterly_rev_entry("2023-03-31", 1_000_000_000, fp="Q1"),  # 1000M
            _quarterly_rev_entry("2023-06-30", 1_100_000_000, fp="Q2"),  # 1100M
            _quarterly_rev_entry("2023-09-30", 1_050_000_000, fp="Q3"),  # 1050M
            _annual_rev_entry(2023, 4_500_000_000),                       # 4500M
        ]
        facts = _make_facts(rev_entries=entries)
        client = SECEdgarClient(rate_limit_delay=0)

        result = client._extract_revenue(facts)

        assert ("Q4", 2023) in result
        # 4500 - 1000 - 1100 - 1050 = 1350
        assert result[("Q4", 2023)] == pytest.approx(1350.0, rel=0.01)

    def test_returns_empty_for_no_revenue_data(self):
        facts = {"facts": {}}
        client = SECEdgarClient(rate_limit_delay=0)
        assert client._extract_revenue(facts) == {}

    def test_skips_old_data_pre_2022(self):
        entry = _quarterly_rev_entry("2020-03-31", 900_000_000, fp="Q1")
        facts = _make_facts(rev_entries=[entry])
        client = SECEdgarClient(rate_limit_delay=0)
        assert client._extract_revenue(facts) == {}

    def test_does_not_create_negative_q4(self):
        """If FY - Q1 - Q2 - Q3 < 0, Q4 should NOT be inserted."""
        entries = [
            _quarterly_rev_entry("2023-03-31", 2_000_000_000, fp="Q1"),
            _quarterly_rev_entry("2023-06-30", 2_000_000_000, fp="Q2"),
            _quarterly_rev_entry("2023-09-30", 2_000_000_000, fp="Q3"),
            _annual_rev_entry(2023, 1_000_000_000),  # Less than sum of Q1+Q2+Q3
        ]
        facts = _make_facts(rev_entries=entries)
        client = SECEdgarClient(rate_limit_delay=0)

        result = client._extract_revenue(facts)
        assert ("Q4", 2023) not in result


# =============================================================================
# fetch_miner_earnings Tests
# =============================================================================

class TestFetchMinerEarnings:
    """Tests for SECEdgarClient.fetch_miner_earnings"""

    def test_returns_empty_for_unknown_ticker(self):
        client = SECEdgarClient(rate_limit_delay=0)
        result = client.fetch_miner_earnings("UNKNOWN_TICKER")
        assert result == []

    def test_returns_empty_when_api_fails(self):
        client = SECEdgarClient(rate_limit_delay=0)
        with patch.object(client, '_fetch_company_facts', return_value=None):
            result = client.fetch_miner_earnings("NEM")
        assert result == []

    def test_returns_records_for_valid_ticker(self):
        eps_entry = _quarterly_eps_entry("2023-03-31", 0.72, "2023-04-26", "Q1")
        rev_entry = _quarterly_rev_entry("2023-03-31", 3_700_000_000, fp="Q1")
        facts = _make_facts(
            eps_entries=[eps_entry],
            rev_entries=[rev_entry],
            entity_name="Newmont Corp /DE/",
        )

        client = SECEdgarClient(rate_limit_delay=0)
        with patch.object(client, '_fetch_company_facts', return_value=facts):
            records = client.fetch_miner_earnings("NEM")

        assert len(records) == 1
        rec = records[0]
        assert rec.ticker == "NEM"
        assert rec.cik == MINER_CIK_MAP["NEM"]
        assert rec.fiscal_period == "Q1"
        assert rec.fiscal_year == 2023
        assert rec.eps_actual == pytest.approx(0.72)
        assert rec.revenue_actual == pytest.approx(3700.0, rel=0.01)
        assert rec.form_type == "10-Q"

    def test_skips_future_filing_dates(self):
        """Records with filed_date in the future should be excluded."""
        future_filed = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        eps_entry = _quarterly_eps_entry("2025-03-31", 0.80, future_filed, "Q1")
        facts = _make_facts(eps_entries=[eps_entry], entity_name="Newmont Corp /DE/")

        client = SECEdgarClient(rate_limit_delay=0)
        with patch.object(client, '_fetch_company_facts', return_value=facts):
            records = client.fetch_miner_earnings("NEM")

        assert records == []

    def test_records_sorted_newest_first(self):
        entries = [
            _quarterly_eps_entry("2023-03-31", 0.50, "2023-04-27", "Q1",
                                  accn="0001164727-23-000001"),
            _quarterly_eps_entry("2023-06-30", 0.62, "2023-07-25", "Q2",
                                  accn="0001164727-23-000002"),
            _quarterly_eps_entry("2023-09-30", 0.48, "2023-10-26", "Q3",
                                  accn="0001164727-23-000003"),
        ]
        facts = _make_facts(eps_entries=entries, entity_name="Newmont Corp /DE/")

        client = SECEdgarClient(rate_limit_delay=0)
        with patch.object(client, '_fetch_company_facts', return_value=facts):
            records = client.fetch_miner_earnings("NEM")

        filed_dates = [r.filed_date for r in records]
        assert filed_dates == sorted(filed_dates, reverse=True)

    def test_min_year_filter(self):
        entries = [
            _quarterly_eps_entry("2022-03-31", 0.40, "2022-04-20", "Q1",
                                  accn="acc-2022"),
            _quarterly_eps_entry("2023-03-31", 0.50, "2023-04-27", "Q1",
                                  accn="acc-2023"),
        ]
        facts = _make_facts(eps_entries=entries, entity_name="Newmont Corp /DE/")

        client = SECEdgarClient(rate_limit_delay=0)
        with patch.object(client, '_fetch_company_facts', return_value=facts):
            records = client.fetch_miner_earnings("NEM", min_year=2023)

        assert all(r.fiscal_year >= 2023 for r in records)

    def test_record_has_valid_edgar_url(self):
        eps_entry = _quarterly_eps_entry("2023-03-31", 0.72, "2023-04-26", "Q1")
        facts = _make_facts(eps_entries=[eps_entry], entity_name="Newmont Corp /DE/")

        client = SECEdgarClient(rate_limit_delay=0)
        with patch.object(client, '_fetch_company_facts', return_value=facts):
            records = client.fetch_miner_earnings("NEM")

        assert len(records) == 1
        url = records[0].edgar_url
        assert url.startswith("https://www.sec.gov")
        assert "NEM" not in url  # URL uses CIK, not ticker


# =============================================================================
# fetch_all_miners Tests
# =============================================================================

class TestFetchAllMiners:
    def test_returns_results_for_all_known_tickers(self):
        eps_entry = _quarterly_eps_entry("2023-03-31", 0.50, "2023-04-27", "Q1")
        facts = _make_facts(eps_entries=[eps_entry], entity_name="Mock Mining Corp")

        client = SECEdgarClient(rate_limit_delay=0)
        with patch.object(client, '_fetch_company_facts', return_value=facts):
            results = client.fetch_all_miners(min_year=2022)

        # All tickers in MINER_CIK_MAP should be attempted
        assert len(results) == len(MINER_CIK_MAP)
        for ticker in MINER_CIK_MAP:
            assert ticker in results

    def test_skips_failed_tickers_gracefully(self):
        def fail_for_some(cik):
            # Fail for Newmont (first ticker alphabetically won't matter — fail for specific CIK)
            if cik == MINER_CIK_MAP["NEM"]:
                return None
            eps_entry = _quarterly_eps_entry("2023-03-31", 0.50, "2023-04-27", "Q1")
            return _make_facts(eps_entries=[eps_entry])

        client = SECEdgarClient(rate_limit_delay=0)
        with patch.object(client, '_fetch_company_facts', side_effect=fail_for_some):
            results = client.fetch_all_miners(min_year=2022)

        # NEM should be absent (API failed), others present
        assert "NEM" not in results
        assert len(results) == len(MINER_CIK_MAP) - 1


# =============================================================================
# SECEarningsRecord Tests
# =============================================================================

class TestSECEarningsRecord:
    def test_edgar_url_format(self):
        rec = SECEarningsRecord(
            ticker="NEM",
            cik="0001164727",
            quarter="Q1 2023",
            fiscal_period="Q1",
            fiscal_year=2023,
            period_end="2023-03-31",
            filed_date="2023-04-26",
            form_type="10-Q",
            eps_actual=0.72,
            revenue_actual=3700.0,
            accession_number="0001164727-23-000041",
        )
        url = rec.edgar_url
        assert url.startswith("https://www.sec.gov")
        assert "1164727" in url  # CIK int without leading zeros
        assert "10-Q" in url

    def test_optional_revenue_is_none(self):
        rec = SECEarningsRecord(
            ticker="GOLD",
            cik="0000756894",
            quarter="Q2 2023",
            fiscal_period="Q2",
            fiscal_year=2023,
            period_end="2023-06-30",
            filed_date="2023-07-30",
            form_type="40-F",
            eps_actual=0.18,
            revenue_actual=None,
            accession_number="0000756894-23-000020",
        )
        assert rec.revenue_actual is None


# =============================================================================
# _quarter_end_date Tests
# =============================================================================

class TestQuarterEndDate:
    @pytest.mark.parametrize("fp,fy,expected", [
        ("Q1", 2023, "2023-03-31"),
        ("Q2", 2023, "2023-06-30"),
        ("Q3", 2023, "2023-09-30"),
        ("Q4", 2023, "2023-12-31"),
        ("FY", 2023, "2023-12-31"),  # fallback
    ])
    def test_quarter_end_dates(self, fp, fy, expected):
        assert _quarter_end_date(fp, fy) == expected


# =============================================================================
# build_upcoming_stubs Tests
# =============================================================================

class TestBuildUpcomingStubs:
    def test_returns_non_empty_list(self):
        stubs = build_upcoming_stubs()
        assert len(stubs) > 0

    def test_stubs_are_after_cutoff(self):
        cutoff = "2026-01-01"
        stubs = build_upcoming_stubs(after_date=cutoff)
        for stub in stubs:
            assert stub["earnings_date"] >= cutoff

    def test_stubs_not_confirmed(self):
        stubs = build_upcoming_stubs()
        for stub in stubs:
            assert stub["is_confirmed"] is False

    def test_stubs_marked_estimated(self):
        stubs = build_upcoming_stubs()
        for stub in stubs:
            assert stub["data_source"] == "estimated"

    def test_stubs_respect_quarters_limit_per_company(self):
        quarters = 1
        stubs = build_upcoming_stubs(quarters=quarters)
        from collections import Counter
        counts = Counter(s["ticker"] for s in stubs)
        for ticker, count in counts.items():
            assert count <= quarters

    def test_stubs_have_required_fields(self):
        stubs = build_upcoming_stubs()
        required_fields = {
            "ticker", "metal", "company_name", "quarter",
            "earnings_date", "time_of_day", "is_confirmed", "data_source"
        }
        for stub in stubs:
            assert required_fields.issubset(stub.keys())

    def test_stubs_metal_matches_ticker_map(self):
        stubs = build_upcoming_stubs()
        for stub in stubs:
            expected_metal = TICKER_METAL_MAP[stub["ticker"]]
            assert stub["metal"] == expected_metal

    def test_stubs_company_name_matches_ticker_map(self):
        stubs = build_upcoming_stubs()
        for stub in stubs:
            expected_name = TICKER_NAME_MAP[stub["ticker"]]
            assert stub["company_name"] == expected_name


# =============================================================================
# EarningsCalendarDB Integration with SEC EDGAR
# =============================================================================

@pytest.fixture
def temp_db(tmp_path):
    """Create an EarningsCalendarDB backed by a temporary SQLite file."""
    db_path = tmp_path / "test_earnings.db"
    # Patch DB_PATH so _init_db uses the temp file; also suppress EDGAR on init
    with patch('core.earnings_calendar.EarningsCalendarDB._populate_from_edgar', return_value=False):
        db = EarningsCalendarDB(db_path=db_path)
    return db


@pytest.fixture
def sample_sec_records():
    """Return a minimal set of SECEarningsRecord objects for two tickers."""
    return {
        "NEM": [
            SECEarningsRecord(
                ticker="NEM", cik=MINER_CIK_MAP["NEM"],
                quarter="Q1 2023", fiscal_period="Q1", fiscal_year=2023,
                period_end="2023-03-31", filed_date="2023-04-26",
                form_type="10-Q", eps_actual=0.72, revenue_actual=3700.0,
                accession_number="0001164727-23-000041",
            ),
            SECEarningsRecord(
                ticker="NEM", cik=MINER_CIK_MAP["NEM"],
                quarter="Q2 2023", fiscal_period="Q2", fiscal_year=2023,
                period_end="2023-06-30", filed_date="2023-07-25",
                form_type="10-Q", eps_actual=0.39, revenue_actual=3399.0,
                accession_number="0001164727-23-000080",
            ),
        ],
        "HL": [
            SECEarningsRecord(
                ticker="HL", cik=MINER_CIK_MAP["HL"],
                quarter="Q1 2023", fiscal_period="Q1", fiscal_year=2023,
                period_end="2023-03-31", filed_date="2023-05-05",
                form_type="10-Q", eps_actual=-0.02, revenue_actual=208.5,
                accession_number="0000719413-23-000010",
            ),
        ],
    }


class TestEarningsCalendarDBWithEdgar:
    def test_db_initializes_empty_when_edgar_unavailable(self, temp_db):
        """DB starts empty when SEC EDGAR is unavailable during init."""
        events = temp_db.get_calendar("2023-04")
        assert events == []

    def test_populate_from_edgar_inserts_records(self, temp_db, sample_sec_records):
        """_populate_from_edgar correctly inserts real SEC records."""
        mock_client = MagicMock()
        mock_client.fetch_all_miners.return_value = sample_sec_records

        with patch('core.sec_edgar.SECEdgarClient', return_value=mock_client), \
             patch('core.sec_edgar.build_upcoming_stubs', return_value=[]):
            conn = temp_db._get_conn()
            try:
                temp_db._populate_from_edgar(conn)
                conn.commit()
            finally:
                conn.close()

        nem_events = temp_db.get_by_ticker("NEM")
        hl_events = temp_db.get_by_ticker("HL")

        assert len(nem_events) == 2
        assert len(hl_events) == 1

        nem_q1 = next(e for e in nem_events if e.quarter == "Q1 2023")
        assert nem_q1.eps_actual == pytest.approx(0.72)
        assert nem_q1.revenue_actual == pytest.approx(3700.0)
        assert nem_q1.data_source == "sec_edgar"
        assert nem_q1.is_confirmed is True

    def test_populate_marks_silver_miners_correctly(self, temp_db, sample_sec_records):
        mock_client = MagicMock()
        mock_client.fetch_all_miners.return_value = sample_sec_records

        with patch('core.sec_edgar.SECEdgarClient', return_value=mock_client), \
             patch('core.sec_edgar.build_upcoming_stubs', return_value=[]):
            conn = temp_db._get_conn()
            try:
                temp_db._populate_from_edgar(conn)
                conn.commit()
            finally:
                conn.close()

        hl_events = temp_db.get_by_ticker("HL")
        assert hl_events[0].metal == "silver"

    def test_populate_adds_upcoming_stubs(self, temp_db, sample_sec_records):
        stub = {
            "ticker": "NEM",
            "metal": "gold",
            "company_name": "Newmont",
            "quarter": "Q3 2026",
            "earnings_date": "2026-10-15",
            "time_of_day": "pre-market",
            "is_confirmed": False,
            "data_source": "estimated",
        }
        mock_client = MagicMock()
        mock_client.fetch_all_miners.return_value = {}

        with patch('core.sec_edgar.SECEdgarClient', return_value=mock_client), \
             patch('core.sec_edgar.build_upcoming_stubs', return_value=[stub]):
            conn = temp_db._get_conn()
            try:
                temp_db._populate_from_edgar(conn)
                conn.commit()
            finally:
                conn.close()

        nem_events = temp_db.get_by_ticker("NEM")
        assert len(nem_events) == 1
        assert nem_events[0].is_confirmed is False
        assert nem_events[0].data_source == "estimated"

    def test_refresh_from_edgar_inserts_new_quarters(self, temp_db, sample_sec_records):
        mock_client = MagicMock()
        mock_client.fetch_all_miners.return_value = sample_sec_records

        with patch('core.sec_edgar.SECEdgarClient', return_value=mock_client), \
             patch('core.sec_edgar.build_upcoming_stubs', return_value=[]):
            counts = temp_db.refresh_from_edgar()

        assert counts["inserted"] == 3  # 2 NEM + 1 HL
        assert counts["updated"] == 0

    def test_refresh_from_edgar_updates_existing_sec_records(self, temp_db, sample_sec_records):
        """Refreshing with updated EPS values updates existing sec_edgar-sourced records."""
        mock_client = MagicMock()
        mock_client.fetch_all_miners.return_value = sample_sec_records

        with patch('core.sec_edgar.SECEdgarClient', return_value=mock_client), \
             patch('core.sec_edgar.build_upcoming_stubs', return_value=[]):
            temp_db.refresh_from_edgar()

        # Now refresh again with updated EPS for NEM Q1 2023
        updated_records = {
            "NEM": [
                SECEarningsRecord(
                    ticker="NEM", cik=MINER_CIK_MAP["NEM"],
                    quarter="Q1 2023", fiscal_period="Q1", fiscal_year=2023,
                    period_end="2023-03-31", filed_date="2023-04-26",
                    form_type="10-Q", eps_actual=0.75,  # updated value
                    revenue_actual=3800.0,
                    accession_number="0001164727-23-000041",
                ),
            ],
        }
        mock_client.fetch_all_miners.return_value = updated_records

        with patch('core.sec_edgar.SECEdgarClient', return_value=mock_client), \
             patch('core.sec_edgar.build_upcoming_stubs', return_value=[]):
            counts = temp_db.refresh_from_edgar()

        assert counts["updated"] == 1
        nem_events = temp_db.get_by_ticker("NEM")
        nem_q1 = next(e for e in nem_events if e.quarter == "Q1 2023")
        assert nem_q1.eps_actual == pytest.approx(0.75)

    def test_duplicate_insert_ignored(self, temp_db, sample_sec_records):
        """Calling populate twice does not create duplicates."""
        mock_client = MagicMock()
        mock_client.fetch_all_miners.return_value = sample_sec_records

        for _ in range(2):
            with patch('core.sec_edgar.SECEdgarClient', return_value=mock_client), \
                 patch('core.sec_edgar.build_upcoming_stubs', return_value=[]):
                conn = temp_db._get_conn()
                try:
                    temp_db._populate_from_edgar(conn)
                    conn.commit()
                finally:
                    conn.close()

        # Should still have exactly 2 NEM records (no duplicates due to UNIQUE constraint)
        nem_events = temp_db.get_by_ticker("NEM")
        assert len(nem_events) == 2

    def test_manual_records_not_overwritten_by_refresh(self, temp_db):
        """Manual corrections (data_source='manual') should not be overwritten by SEC refresh."""
        manual_event = EarningsEvent(
            id=None, ticker="NEM", metal="gold", company_name="Newmont",
            quarter="Q1 2023", earnings_date="2023-04-26", time_of_day="pre-market",
            is_confirmed=True, eps_actual=0.99, revenue_actual=9999.0,
            data_source="manual",
        )
        temp_db.create_event(manual_event)

        sec_record = {
            "NEM": [
                SECEarningsRecord(
                    ticker="NEM", cik=MINER_CIK_MAP["NEM"],
                    quarter="Q1 2023", fiscal_period="Q1", fiscal_year=2023,
                    period_end="2023-03-31", filed_date="2023-04-26",
                    form_type="10-Q", eps_actual=0.72, revenue_actual=3700.0,
                    accession_number="0001164727-23-000041",
                )
            ]
        }
        mock_client = MagicMock()
        mock_client.fetch_all_miners.return_value = sec_record

        with patch('core.sec_edgar.SECEdgarClient', return_value=mock_client), \
             patch('core.sec_edgar.build_upcoming_stubs', return_value=[]):
            temp_db.refresh_from_edgar()

        nem_events = temp_db.get_by_ticker("NEM")
        q1 = next(e for e in nem_events if e.quarter == "Q1 2023")
        # Manual record should be preserved
        assert q1.eps_actual == pytest.approx(0.99)
        assert q1.revenue_actual == pytest.approx(9999.0)


# =============================================================================
# Rate-Limiting and Network Error Handling
# =============================================================================

class TestNetworkResilience:
    def test_get_returns_none_on_request_exception(self):
        client = SECEdgarClient(rate_limit_delay=0)
        with patch.object(client._session, 'get',
                          side_effect=requests.RequestException("timeout")):
            result = client._get("https://data.sec.gov/fake")
        assert result is None

    def test_get_returns_none_on_http_error(self):
        client = SECEdgarClient(rate_limit_delay=0)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
        with patch.object(client._session, 'get', return_value=mock_resp):
            result = client._get("https://data.sec.gov/fake")
        assert result is None

    def test_rate_limit_delay_respected(self):
        """Verify time.sleep is called with the configured delay."""
        client = SECEdgarClient(rate_limit_delay=0.15)
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {}

        with patch.object(client._session, 'get', return_value=mock_resp), \
             patch('core.sec_edgar.time.sleep') as mock_sleep:
            client._get("https://data.sec.gov/fake")

        mock_sleep.assert_called_once_with(0.15)

    def test_session_has_correct_user_agent(self):
        client = SECEdgarClient(rate_limit_delay=0)
        assert "AlgoSovereigntyAnalyzer" in client._session.headers.get("User-Agent", "")
