"""
SEC EDGAR API Integration for Miner Earnings Data

Fetches real quarterly earnings data from the SEC EDGAR XBRL API for gold and
silver mining companies listed on US exchanges.

Reference:
  Company Facts: https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
  Company Tickers: https://www.sec.gov/files/company_tickers.json

SEC API Terms: Free to use. Requires User-Agent header with contact info.
Rate limit: ~10 requests/second max. We use 0.15s delay between requests.
"""

import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# SEC requires a User-Agent with app name + contact
SEC_USER_AGENT = "AlgoSovereigntyAnalyzer/1.0 contact@algosovereignty.com"
SEC_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# Known CIK numbers for tracked miners (verified via SEC EDGAR company_tickers.json)
# US companies file 10-K/10-Q; Canadian companies file 40-F annually
MINER_CIK_MAP: Dict[str, str] = {
    "NEM":  "0001164727",   # Newmont Corp /DE/ (US, 10-K/10-Q)
    "GOLD": "0000756894",   # Barrick Gold Corp (Canada, 40-F)
    "AEM":  "0000002809",   # Agnico Eagle Mines Ltd (Canada, 40-F)
    "KGC":  "0000701818",   # Kinross Gold Corp (Canada, 40-F)
    "BTG":  "0001429937",   # B2Gold Corp (Canada, 40-F)
    "PAAS": "0000771992",   # Pan American Silver Corp (Canada, 40-F)
    "AG":   "0001308648",   # First Majestic Silver Corp (Canada, 40-F)
    "HL":   "0000719413",   # Hecla Mining Co /DE/ (US, 10-K/10-Q)
    "CDE":  "0000215466",   # Coeur Mining, Inc. (US, 10-K/10-Q)
}

TICKER_METAL_MAP: Dict[str, str] = {
    "NEM": "gold", "GOLD": "gold", "AEM": "gold", "KGC": "gold", "BTG": "gold",
    "PAAS": "silver", "AG": "silver", "HL": "silver", "CDE": "silver",
}

TICKER_NAME_MAP: Dict[str, str] = {
    "NEM":  "Newmont",
    "GOLD": "Barrick Gold",
    "AEM":  "Agnico Eagle",
    "KGC":  "Kinross Gold",
    "BTG":  "B2Gold",
    "PAAS": "Pan American Silver",
    "AG":   "First Majestic Silver",
    "HL":   "Hecla Mining",
    "CDE":  "Coeur Mining",
}

# Quarterly earnings report months by ticker (typical schedule)
# Used to estimate report timing when not yet in SEC EDGAR
EARNINGS_MONTHS: Dict[str, List[int]] = {
    "NEM":  [2, 4, 7, 10],
    "GOLD": [2, 5, 8, 11],
    "AEM":  [2, 4, 7, 10],
    "KGC":  [2, 5, 8, 11],
    "BTG":  [3, 5, 8, 11],
    "PAAS": [2, 5, 8, 11],
    "AG":   [2, 5, 8, 11],
    "HL":   [2, 5, 8, 11],
    "CDE":  [2, 5, 8, 11],
}


@dataclass
class SECEarningsRecord:
    """Single quarterly earnings record sourced from SEC EDGAR."""
    ticker: str
    cik: str
    quarter: str            # e.g. "Q1 2023"
    fiscal_period: str      # "Q1" | "Q2" | "Q3" | "Q4"
    fiscal_year: int
    period_end: str         # "2023-03-31"
    filed_date: str         # "2023-04-27" — actual SEC filing date
    form_type: str          # "10-Q" | "10-K" | "40-F" | "20-F"
    eps_actual: Optional[float]
    revenue_actual: Optional[float]   # in millions USD
    accession_number: str

    @property
    def edgar_url(self) -> str:
        """URL to the SEC filing index page."""
        acc = self.accession_number.replace("-", "")
        cik_int = int(self.cik)
        return (
            f"https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcompany&CIK={cik_int}"
            f"&type={self.form_type}&dateb=&owner=include&count=10"
        )


class SECEdgarClient:
    """
    Fetches real earnings data from SEC EDGAR XBRL API.

    Uses the companyfacts endpoint which returns structured financial data
    for all SEC filers. Handles both US GAAP (10-K/10-Q) and IFRS (40-F/20-F).
    """

    # XBRL concepts to try for EPS, in priority order
    _EPS_CONCEPTS = [
        ("us-gaap", "EarningsPerShareDiluted"),
        ("us-gaap", "EarningsPerShareBasic"),
        ("ifrs-full", "DilutedEarningsLossPerShare"),
        ("ifrs-full", "BasicEarningsLossPerShare"),
    ]

    # XBRL concepts for revenue/sales
    _REVENUE_CONCEPTS = [
        ("us-gaap", "Revenues"),
        ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
        ("us-gaap", "SalesRevenueNet"),
        ("us-gaap", "RevenueFromContractWithCustomerIncludingAssessedTax"),
        ("ifrs-full", "Revenue"),
        ("ifrs-full", "RevenueFromContractsWithCustomers"),
    ]

    def __init__(self, rate_limit_delay: float = 0.15):
        self._delay = rate_limit_delay
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": SEC_USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
        })

    def _get(self, url: str) -> Optional[Dict]:
        """Make a rate-limited GET request."""
        time.sleep(self._delay)
        try:
            resp = self._session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"  SEC EDGAR request failed ({url}): {e}")
            return None

    def _fetch_company_facts(self, cik: str) -> Optional[Dict]:
        url = SEC_FACTS_URL.format(cik=cik)
        return self._get(url)

    @staticmethod
    def _duration_days(start: Optional[str], end: Optional[str]) -> Optional[int]:
        """Calculate calendar days between two ISO date strings."""
        if not start or not end:
            return None
        try:
            s = datetime.strptime(start, "%Y-%m-%d")
            e = datetime.strptime(end, "%Y-%m-%d")
            return (e - s).days
        except ValueError:
            return None

    @staticmethod
    def _is_quarterly(start: Optional[str], end: Optional[str]) -> bool:
        """Return True if the period spans ~3 months (standalone quarterly)."""
        days = SECEdgarClient._duration_days(start, end)
        return days is not None and 75 <= days <= 105

    @staticmethod
    def _is_annual(start: Optional[str], end: Optional[str]) -> bool:
        """Return True if the period spans ~12 months."""
        days = SECEdgarClient._duration_days(start, end)
        return days is not None and 340 <= days <= 380

    def _extract_eps(self, facts: Dict) -> Dict[Tuple[str, int], Tuple[float, str, str, str]]:
        """
        Extract standalone quarterly EPS from XBRL facts.

        EDGAR filings include current-period and prior-year comparison data.
        We use the `end` date month to infer which fiscal quarter is being reported,
        and prefer ~90-day standalone quarterly figures over annual FY figures.

        Returns dict: (fiscal_period, calendar_year) -> (eps, filed_date, accession, form_type)
        """
        result: Dict[Tuple[str, int], Tuple[float, str, str, str]] = {}

        for namespace, concept in self._EPS_CONCEPTS:
            ns_data = facts.get("facts", {}).get(namespace, {})
            concept_data = ns_data.get(concept, {}).get("units", {})

            for unit_key in ("USD/shares", "shares"):
                entries = concept_data.get(unit_key, [])
                for entry in entries:
                    form = entry.get("form", "")
                    if form not in ("10-Q", "10-K", "40-F", "20-F"):
                        continue

                    fp = entry.get("fp", "")
                    val = entry.get("val")
                    filed = entry.get("filed", "")
                    accn = entry.get("accn", "")
                    start = entry.get("start")
                    end = entry.get("end")

                    if fp not in ("Q1", "Q2", "Q3", "Q4", "FY") or val is None:
                        continue

                    if not end:
                        continue

                    try:
                        end_dt = datetime.strptime(end, "%Y-%m-%d")
                    except ValueError:
                        continue

                    end_year = end_dt.year
                    days = self._duration_days(start, end) or 0

                    # Determine fiscal period from end date month
                    month_to_fp = {3: "Q1", 6: "Q2", 9: "Q3", 12: "Q4"}
                    inferred_fp = month_to_fp.get(end_dt.month, fp if fp != "FY" else "Q4")

                    # For annual reports (40-F, 10-K), fp=FY means the full-year EPS
                    # which we map to Q4 only if no quarterly Q4 data is available
                    is_qtr = 75 <= days <= 105
                    is_ann = 340 <= days <= 380

                    key = (inferred_fp, end_year)

                    if key not in result:
                        result[key] = (val, filed, accn, form)
                    else:
                        # Prefer quarterly standalone (90-day) over cumulative/annual
                        existing_val, existing_filed, _, existing_form = result[key]
                        if is_qtr and existing_form in ("10-K", "40-F", "20-F"):
                            result[key] = (val, filed, accn, form)

                # Only keep this unit type if it has recent data (2022+)
                recent = {k: v for k, v in result.items() if k[1] >= 2022}
                if recent:
                    result = recent
                    break  # Use first unit type with recent data
                else:
                    result = {}  # Discard old-only data, try next unit type

            # Only accept this concept if it has recent data
            recent = {k: v for k, v in result.items() if k[1] >= 2022}
            if recent:
                return recent
            result = {}  # Discard, try next EPS concept

        return result

    def _extract_revenue(self, facts: Dict) -> Dict[Tuple[str, int], float]:
        """
        Extract standalone quarterly revenue in millions USD.

        EDGAR filings include both current-period and prior-year comparison data,
        so we use the `end` date year to identify the correct fiscal year entries.
        Quarterly standalone figures are identified by ~90-day duration.
        Q4 standalone is computed as FY_total - (Q1 + Q2 + Q3).

        Returns dict: (fiscal_period, fiscal_year) -> revenue_millions
        """
        for namespace, concept in self._REVENUE_CONCEPTS:
            ns_data = facts.get("facts", {}).get(namespace, {})
            raw_entries = ns_data.get(concept, {}).get("units", {}).get("USD", [])

            if not raw_entries:
                continue

            # Filter to SEC filings only
            filings = [
                e for e in raw_entries
                if e.get("form") in ("10-Q", "10-K", "40-F", "20-F")
                and e.get("val") is not None
            ]

            if not filings:
                continue

            # Quarterly standalone: ~90-day periods with `end` year matching fiscal year
            # We key by the calendar year of the `end` date, not the EDGAR `fy` label,
            # because companies file prior-year comparisons with the same `fp`/`fy` tags.
            standalone: Dict[Tuple[str, int], float] = {}
            annual: Dict[int, float] = {}   # calendar_year -> annual revenue

            for e in filings:
                start = e.get("start")
                end = e.get("end")
                val = e.get("val", 0)
                fp = e.get("fp", "")

                if not end:
                    continue

                try:
                    end_dt = datetime.strptime(end, "%Y-%m-%d")
                except ValueError:
                    continue

                end_year = end_dt.year
                days = self._duration_days(start, end) or 0

                # Standalone quarterly: ~90 days ending in the expected month
                if 75 <= days <= 105:
                    # Determine which quarter based on end month
                    month_to_fp = {3: "Q1", 6: "Q2", 9: "Q3", 12: "Q4"}
                    inferred_fp = month_to_fp.get(end_dt.month)
                    if inferred_fp:
                        key = (inferred_fp, end_year)
                        # Keep the most recent filing's value if duplicated
                        if key not in standalone:
                            standalone[key] = round(val / 1_000_000, 1)

                # Full annual: ~365 days
                elif 340 <= days <= 380 and fp in ("FY", "Q4"):
                    if end_year not in annual:
                        annual[end_year] = round(val / 1_000_000, 1)

            # Fill in Q4 from FY - (Q1+Q2+Q3) where Q4 standalone isn't directly available
            result: Dict[Tuple[str, int], float] = dict(standalone)
            for cal_year, fy_rev in annual.items():
                if ("Q4", cal_year) not in result:
                    q1 = standalone.get(("Q1", cal_year))
                    q2 = standalone.get(("Q2", cal_year))
                    q3 = standalone.get(("Q3", cal_year))
                    if q1 is not None and q2 is not None and q3 is not None:
                        q4 = round(fy_rev - q1 - q2 - q3, 1)
                        if q4 > 0:  # Sanity check: Q4 shouldn't be negative
                            result[("Q4", cal_year)] = q4

            # Only use this concept if it has recent data (2022+)
            recent_result = {k: v for k, v in result.items() if k[1] >= 2022}
            if recent_result:
                return recent_result
            # else: this concept only has old data, try the next concept

        return {}

    def fetch_miner_earnings(
        self,
        ticker: str,
        min_year: int = 2022,
    ) -> List[SECEarningsRecord]:
        """
        Fetch real quarterly earnings records for a mining company from SEC EDGAR.

        Args:
            ticker: Company ticker symbol (e.g. "NEM")
            min_year: Only return records from this fiscal year onwards

        Returns:
            List of SECEarningsRecord sorted newest-first.
            Returns empty list if ticker not found or API unavailable.
        """
        ticker = ticker.upper()
        cik = MINER_CIK_MAP.get(ticker)
        if not cik:
            print(f"  [{ticker}] No CIK mapping found")
            return []

        print(f"  [{ticker}] Fetching from SEC EDGAR (CIK={cik})...")
        facts = self._fetch_company_facts(cik)
        if not facts:
            return []

        entity_name = facts.get("entityName", ticker)
        print(f"  [{ticker}] Entity: {entity_name}")

        eps_data = self._extract_eps(facts)
        rev_data = self._extract_revenue(facts)

        now = datetime.now()
        records: List[SECEarningsRecord] = []

        for (fp, fy), (eps, filed_date, accn, form) in eps_data.items():
            if fy < min_year:
                continue

            # Skip future filings
            try:
                filed_dt = datetime.strptime(filed_date, "%Y-%m-%d")
                if filed_dt > now:
                    continue
            except ValueError:
                continue

            quarter_label = f"{fp} {fy}"
            rev = rev_data.get((fp, fy))

            records.append(SECEarningsRecord(
                ticker=ticker,
                cik=cik,
                quarter=quarter_label,
                fiscal_period=fp,
                fiscal_year=fy,
                period_end=_quarter_end_date(fp, fy),
                filed_date=filed_date,
                form_type=form,
                eps_actual=eps,
                revenue_actual=rev,
                accession_number=accn,
            ))

        records.sort(key=lambda r: r.filed_date, reverse=True)
        print(f"  [{ticker}] Found {len(records)} quarters of real data")
        return records

    def fetch_all_miners(self, min_year: int = 2022) -> Dict[str, List[SECEarningsRecord]]:
        """Fetch earnings records for all tracked mining companies."""
        all_data: Dict[str, List[SECEarningsRecord]] = {}
        for ticker in MINER_CIK_MAP:
            records = self.fetch_miner_earnings(ticker, min_year=min_year)
            if records:
                all_data[ticker] = records
        return all_data


def _quarter_end_date(fp: str, fy: int) -> str:
    """Return the typical fiscal quarter end date for calendar-year companies."""
    ends = {"Q1": f"{fy}-03-31", "Q2": f"{fy}-06-30", "Q3": f"{fy}-09-30", "Q4": f"{fy}-12-31"}
    return ends.get(fp, f"{fy}-12-31")


def build_upcoming_stubs(
    after_date: Optional[str] = None,
    quarters: int = 2,
) -> List[Dict]:
    """
    Build stub records for expected upcoming earnings dates.

    These are ESTIMATES only — exact dates are not confirmed until companies
    announce them. Marked with is_confirmed=False and no financial data.

    Args:
        after_date: Only generate stubs after this date (ISO format). Defaults to today.
        quarters: How many future quarters to generate per company.

    Returns:
        List of dicts compatible with EarningsCalendarDB.create_event().
    """
    if after_date:
        cutoff = datetime.strptime(after_date, "%Y-%m-%d")
    else:
        cutoff = datetime.now()

    stubs = []
    for ticker, report_months in EARNINGS_MONTHS.items():
        generated = 0
        # Check a rolling 12-month window
        for month_offset in range(1, 13):
            if generated >= quarters:
                break
            target = cutoff + timedelta(days=30 * month_offset)
            # Is this a typical earnings month?
            if target.month not in report_months:
                continue

            # Estimate earnings date: ~15th of the reporting month
            est_date = target.replace(day=15)
            if est_date <= cutoff:
                continue

            # Figure out which quarter this corresponds to
            # Report month → fiscal quarter that just ended
            month_to_quarter = {2: "Q4", 3: "Q4", 4: "Q1", 5: "Q1", 7: "Q2", 8: "Q2", 10: "Q3", 11: "Q3"}
            fp = month_to_quarter.get(target.month, "Q?")
            fy = est_date.year if target.month > 3 else est_date.year - 1

            stubs.append({
                "ticker": ticker,
                "metal": TICKER_METAL_MAP[ticker],
                "company_name": TICKER_NAME_MAP[ticker],
                "quarter": f"{fp} {fy}",
                "earnings_date": est_date.strftime("%Y-%m-%d"),
                "time_of_day": "pre-market",
                "is_confirmed": False,
                "data_source": "estimated",
            })
            generated += 1

    return stubs
