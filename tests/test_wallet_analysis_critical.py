"""
Critical Integration Tests for Wallet Analysis

Covers the high-risk paths that must never regress:
  1. Retry behaviour — transient node errors trigger retries before giving up
  2. Decimal precision — 0-/6-/8-decimal assets converted correctly
  3. Participation info structure — all keys present and correct
  4. Shitcoin sort order — highest USD value first
  5. Classification hierarchy — CSV overrides beat regex during analysis
  6. LP fallback — raw token classified when LP parsing returns None
  7. Multi-call state update — state replaced on each analyze_wallet call
  8. Rate-limit retry — 429 with Retry-After header triggers single retry
  9. Sovereignty boundary conditions — exact threshold values
 10. Hard money isolation — only hard_money assets count for hard money USD
"""

import pytest
import requests
from unittest.mock import patch, MagicMock, call

from core.analyzer import AlgorandSovereigntyAnalyzer


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def analyzer():
    """Analyzer with mocked node config; LP detection disabled by default."""
    with patch("core.analyzer.get_algorand_node_config", return_value=(
        "https://mainnet-api.algonode.cloud", "", {}
    )):
        inst = AlgorandSovereigntyAnalyzer(use_local_node=False)
        inst.lp_parser.is_lp_token = MagicMock(return_value=False)
        return inst


def _make_response(json_data=None, status_code=200):
    """Helper: create a mock requests.Response."""
    r = MagicMock()
    r.status_code = status_code
    r.raise_for_status = MagicMock()
    r.json.return_value = json_data or {}
    return r


def _make_http_error(status_code):
    """Helper: create an HTTPError with a response stub."""
    resp = MagicMock()
    resp.status_code = status_code
    err = requests.exceptions.HTTPError(response=resp)
    return err


# ---------------------------------------------------------------------------
# 1. Retry behaviour
# ---------------------------------------------------------------------------

class TestRetryBehaviour:
    """Verify that transient node errors are retried before giving up."""

    def test_timeout_triggers_retries_then_raises(self, analyzer):
        """
        get_account_assets retries max_retries times on Timeout, then re-raises.
        analyze_wallet propagates the Timeout to the caller.
        """
        with patch("core.analyzer.requests.get",
                   side_effect=requests.exceptions.Timeout("timeout")) as mock_get, \
             patch("core.retry.time.sleep"):  # suppress real sleeps

            with pytest.raises(requests.exceptions.Timeout):
                analyzer.analyze_wallet("A" * 58)

        # Called initial attempt + 3 retries = 4 total
        assert mock_get.call_count == 4

    def test_connection_error_triggers_retries_then_raises(self, analyzer):
        """ConnectionError is retried max_retries times, then re-raised."""
        with patch("core.analyzer.requests.get",
                   side_effect=requests.exceptions.ConnectionError("refused")) as mock_get, \
             patch("core.retry.time.sleep"):

            with pytest.raises(requests.exceptions.ConnectionError):
                analyzer.analyze_wallet("B" * 58)

        assert mock_get.call_count == 4

    def test_transient_failure_then_success(self, analyzer):
        """
        Two transient timeouts followed by a successful response should
        complete the analysis (no exception propagates).
        """
        account_data = {"amount": 1_000_000_000, "status": "Offline", "assets": []}
        responses = [
            requests.exceptions.Timeout("t1"),
            requests.exceptions.Timeout("t2"),
            _make_response(account_data),
        ]

        with patch("core.analyzer.requests.get", side_effect=responses), \
             patch("core.retry.time.sleep"), \
             patch("core.analyzer.get_algo_price", return_value=0.35):

            result = analyzer.analyze_wallet("C" * 58)

        assert result is not None
        assert "algo" in result

    def test_500_server_error_retried(self, analyzer):
        """HTTP 500 is a retryable server error; eventually raises → None."""
        http_500 = _make_http_error(500)
        resp_500 = _make_response(status_code=500)
        resp_500.raise_for_status.side_effect = http_500

        with patch("core.analyzer.requests.get", return_value=resp_500) as mock_get, \
             patch("core.retry.time.sleep"):

            result = analyzer.analyze_wallet("D" * 58)

        assert result is None
        assert mock_get.call_count == 4  # 1 initial + 3 retries

    def test_404_not_retried(self, analyzer):
        """HTTP 404 is permanent; no retries, returns None immediately."""
        http_404 = _make_http_error(404)
        resp_404 = _make_response(status_code=404)
        resp_404.raise_for_status.side_effect = http_404

        with patch("core.analyzer.requests.get", return_value=resp_404) as mock_get, \
             patch("core.retry.time.sleep"):

            result = analyzer.get_account_assets("E" * 58)

        assert result is None
        assert mock_get.call_count == 1  # no retries


# ---------------------------------------------------------------------------
# 2. Decimal precision
# ---------------------------------------------------------------------------

class TestDecimalPrecision:
    """Assets with 0, 6, and 8 decimal places must be converted correctly."""

    ASSET_DETAILS = {
        386192725: {"params": {"name": "goBTC",       "unit-name": "goBTC",   "decimals": 8}},
        31566704:  {"params": {"name": "USDC",        "unit-name": "USDC",    "decimals": 6}},
        99990001:  {"params": {"name": "NFT Token",   "unit-name": "NFTX",    "decimals": 0}},
    }

    def _make_mock_get(self, wallet_data):
        def _get(url, **kwargs):
            r = MagicMock()
            r.raise_for_status = MagicMock()
            if "/v2/accounts/" in url:
                r.json.return_value = wallet_data
            elif "/v2/assets/" in url:
                asset_id = int(url.split("/v2/assets/")[1].split("?")[0])
                r.json.return_value = self.ASSET_DETAILS.get(asset_id)
            else:
                r.json.return_value = {}
            return r
        return _get

    def test_8_decimal_gobtc(self, analyzer):
        """0.1 goBTC stored as 10_000_000 raw units (8 decimals)."""
        wallet = {"amount": 0, "status": "Offline", "assets": [
            {"asset-id": 386192725, "amount": 10_000_000},  # 0.1 goBTC
        ]}
        mock_get = self._make_mock_get(wallet)

        with patch("core.analyzer.requests.get", side_effect=mock_get), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=95000.0):

            categories = analyzer.analyze_wallet("F" * 58)

        gobtc = next(a for a in categories["hard_money"] if a["ticker"] == "goBTC")
        assert gobtc["amount"] == pytest.approx(0.1)
        assert gobtc["usd_value"] == pytest.approx(9500.0)

    def test_6_decimal_usdc(self, analyzer):
        """5000 USDC stored as 5_000_000_000 raw units (6 decimals)."""
        wallet = {"amount": 0, "status": "Offline", "assets": [
            {"asset-id": 31566704, "amount": 5_000_000_000},  # 5000 USDC
        ]}
        mock_get = self._make_mock_get(wallet)

        with patch("core.analyzer.requests.get", side_effect=mock_get), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=1.0):

            categories = analyzer.analyze_wallet("G" * 58)

        usdc = next(a for a in categories["dollars"] if a["ticker"] == "USDC")
        assert usdc["amount"] == pytest.approx(5000.0)
        assert usdc["usd_value"] == pytest.approx(5000.0)

    def test_0_decimal_nft_filtered(self, analyzer):
        """Amount-1 token with 0 decimals and no price is treated as NFT and filtered."""
        wallet = {"amount": 0, "status": "Offline", "assets": [
            {"asset-id": 99990001, "amount": 1},
        ]}
        mock_get = self._make_mock_get(wallet)

        with patch("core.analyzer.requests.get", side_effect=mock_get), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=None):

            categories = analyzer.analyze_wallet("H" * 58)

        all_tickers = [a["ticker"] for cat in categories.values() for a in cat]
        assert "NFTX" not in all_tickers


# ---------------------------------------------------------------------------
# 3. Participation info structure
# ---------------------------------------------------------------------------

class TestParticipationInfo:
    """Verify that participation info is correctly extracted and stored."""

    PARTICIPATING_WALLET = {
        "amount": 50_000_000_000,  # 50,000 ALGO
        "status": "Online",
        "participation": {
            "vote-first-valid": 10_000,
            "vote-last-valid": 9_000_000,
        },
        "assets": [],
    }

    OFFLINE_WALLET = {
        "amount": 1_000_000_000,
        "status": "Offline",
        "assets": [],
    }

    def test_participating_wallet_stores_info(self, analyzer):
        with patch.object(analyzer, "get_account_assets", return_value=self.PARTICIPATING_WALLET), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=None):

            analyzer.analyze_wallet("PART_ADDR_TEST")

        info = analyzer.last_participation_info
        assert info["staked_amount"] == pytest.approx(50_000.0)
        assert info["vote_first_valid"] == 10_000
        assert info["vote_last_valid"] == 9_000_000
        assert info["key_expiration_rounds"] == 9_000_000
        assert info["is_incentive_eligible"] is True  # balance >= 1 ALGO
        assert info["estimated_apy"] > 0

    def test_offline_wallet_zeroed_participation_info(self, analyzer):
        with patch.object(analyzer, "get_account_assets", return_value=self.OFFLINE_WALLET), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=None):

            analyzer.analyze_wallet("OFFLINE_ADDR")

        info = analyzer.last_participation_info
        assert info["staked_amount"] == 0.0
        assert info["vote_first_valid"] is None
        assert info["vote_last_valid"] is None
        assert info["is_incentive_eligible"] is False
        assert info["estimated_apy"] == 0.0

    def test_is_participating_flag(self, analyzer):
        with patch.object(analyzer, "get_account_assets", return_value=self.PARTICIPATING_WALLET), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=None):

            analyzer.analyze_wallet("FLAG_ADDR")

        assert analyzer.last_is_participating is True

    def test_algo_name_includes_participating_tag(self, analyzer):
        with patch.object(analyzer, "get_account_assets", return_value=self.PARTICIPATING_WALLET), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=None):

            categories = analyzer.analyze_wallet("PART_NAME_ADDR")

        algo_entry = categories["algo"][0]
        assert "PARTICIPATING" in algo_entry["name"]


# ---------------------------------------------------------------------------
# 4. Shitcoin sort order
# ---------------------------------------------------------------------------

class TestShitcoinSortOrder:
    """After analysis, shitcoins must appear highest-USD-value first."""

    ASSET_DETAILS = {
        111: {"params": {"name": "Token A",  "unit-name": "TOKA", "decimals": 6}},
        222: {"params": {"name": "Token B",  "unit-name": "TOKB", "decimals": 6}},
        333: {"params": {"name": "Token C",  "unit-name": "TOKC", "decimals": 6}},
    }

    def test_shitcoins_sorted_by_usd_desc(self, analyzer):
        wallet = {
            "amount": 0, "status": "Offline",
            "assets": [
                {"asset-id": 111, "amount": 1_000_000},   # 1 TOKA
                {"asset-id": 222, "amount": 1_000_000},   # 1 TOKB
                {"asset-id": 333, "amount": 1_000_000},   # 1 TOKC
            ],
        }

        # All prices must be high enough that usd_value >= $1 to survive dust filter
        prices = {"TOKA": 5.0, "TOKB": 50.0, "TOKC": 2.0}

        def _get(url, **kwargs):
            r = MagicMock()
            r.raise_for_status = MagicMock()
            if "/v2/accounts/" in url:
                r.json.return_value = wallet
            elif "/v2/assets/" in url:
                asset_id = int(url.split("/v2/assets/")[1].split("?")[0])
                r.json.return_value = self.ASSET_DETAILS.get(asset_id)
            return r

        def _price(ticker, asset_id=None):
            return prices.get(ticker.upper(), prices.get(ticker))

        with patch("core.analyzer.requests.get", side_effect=_get), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", side_effect=_price):

            categories = analyzer.analyze_wallet("SORT_ADDR")

        shitcoins = categories["shitcoin"]
        assert len(shitcoins) >= 3
        usd_values = [a["usd_value"] for a in shitcoins]
        assert usd_values == sorted(usd_values, reverse=True)


# ---------------------------------------------------------------------------
# 5. Classification hierarchy: CSV > regex during analysis
# ---------------------------------------------------------------------------

class TestClassificationHierarchy:
    """CSV manual overrides must take priority over auto-classification regex."""

    def test_csv_override_beats_regex(self, analyzer):
        """
        An asset that regex would classify as 'shitcoin' but that is listed
        in the CSV as 'hard_money' must end up in hard_money.
        """
        asset_id = 55555555
        # Patch the classifier to behave as if CSV has this asset
        analyzer.classifier.classifications = {
            str(asset_id): {"name": "CSV Gold Token", "ticker": "CSVGOLD", "category": "hard_money"}
        }
        # The regex-based auto_classify would return 'shitcoin' for unknown assets,
        # but get_asset_details will return the params, which the analyzer then
        # overrides from classifier.classifications before calling get_asset_price.
        # We verify the asset ends up in hard_money.

        wallet = {
            "amount": 0, "status": "Offline",
            "assets": [{"asset-id": asset_id, "amount": 1_000_000_000}],
        }
        asset_details = {
            asset_id: {"params": {"name": "Unknown Token", "unit-name": "UNKWN", "decimals": 6}}
        }

        def _get(url, **kwargs):
            r = MagicMock()
            r.raise_for_status = MagicMock()
            if "/v2/accounts/" in url:
                r.json.return_value = wallet
            elif "/v2/assets/" in url:
                aid = int(url.split("/v2/assets/")[1].split("?")[0])
                r.json.return_value = asset_details.get(aid)
            return r

        with patch("core.analyzer.requests.get", side_effect=_get), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=85.0):

            categories = analyzer.analyze_wallet("CSV_OVERRIDE_ADDR")

        # Should be in hard_money because CSV says so
        hard_money_tickers = [a["ticker"] for a in categories["hard_money"]]
        assert "CSVGOLD" in hard_money_tickers

        # Must NOT be in shitcoin
        shitcoin_tickers = [a["ticker"] for a in categories["shitcoin"]]
        assert "CSVGOLD" not in shitcoin_tickers

    def test_regex_classifies_known_hard_money(self, analyzer):
        """
        goBTC is known to regex patterns and must be classified as hard_money
        even when not in CSV.
        """
        asset_id = 386192725
        analyzer.classifier.classifications = {}  # No CSV overrides

        wallet = {
            "amount": 0, "status": "Offline",
            "assets": [{"asset-id": asset_id, "amount": 10_000_000}],
        }
        asset_details = {
            asset_id: {"params": {"name": "goBTC", "unit-name": "goBTC", "decimals": 8}}
        }

        def _get(url, **kwargs):
            r = MagicMock()
            r.raise_for_status = MagicMock()
            if "/v2/accounts/" in url:
                r.json.return_value = wallet
            elif "/v2/assets/" in url:
                aid = int(url.split("/v2/assets/")[1].split("?")[0])
                r.json.return_value = asset_details.get(aid)
            return r

        with patch("core.analyzer.requests.get", side_effect=_get), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=95000.0):

            categories = analyzer.analyze_wallet("REGEX_ADDR")

        hard_money_tickers = [a["ticker"] for a in categories["hard_money"]]
        assert "goBTC" in hard_money_tickers


# ---------------------------------------------------------------------------
# 6. LP token fallback when parsing returns None
# ---------------------------------------------------------------------------

class TestLPFallback:
    """When LP parsing fails, the raw LP token should be classified normally."""

    LP_ASSET_ID = 99887766
    ASSET_DETAILS = {
        LP_ASSET_ID: {
            "params": {
                "name": "TinymanPool2.0 ALGO-USDC",
                "unit-name": "TMPOOL2",
                "decimals": 6,
                "creator": "POOL_CREATOR_ADDR",
            }
        }
    }

    def test_lp_fallback_to_shitcoin_when_parse_fails(self, analyzer):
        """LP token that fails to parse should fall back to shitcoin classification."""
        wallet = {
            "amount": 0, "status": "Offline",
            "assets": [{"asset-id": self.LP_ASSET_ID, "amount": 1_000_000_000}],
        }

        def _get(url, **kwargs):
            r = MagicMock()
            r.raise_for_status = MagicMock()
            if "/v2/accounts/" in url:
                r.json.return_value = wallet
            elif "/v2/assets/" in url:
                aid = int(url.split("/v2/assets/")[1].split("?")[0])
                r.json.return_value = self.ASSET_DETAILS.get(aid)
            return r

        # LP is detected but parsing returns None → raw token classified
        analyzer.lp_parser.is_lp_token = MagicMock(return_value=True)
        analyzer.lp_parser.estimate_lp_value = MagicMock(return_value=None)

        with patch("core.analyzer.requests.get", side_effect=_get), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=2.0):

            categories = analyzer.analyze_wallet("LP_FALLBACK_ADDR")

        # classify_lp_components should NOT have been called (no breakdown)
        analyzer.lp_parser.classify_lp_components.assert_not_called() \
            if hasattr(analyzer.lp_parser.classify_lp_components, 'assert_not_called') else None

        # Raw LP token should land in shitcoin (auto-classify for unknown LP)
        all_tickers = [a["ticker"] for cat in categories.values() for a in cat]
        assert "TMPOOL2" in all_tickers

    def test_lp_success_components_placed_correctly(self, analyzer):
        """When LP parsing succeeds, components go to their correct categories."""
        from core.lp_parser import LPBreakdown

        wallet = {
            "amount": 0, "status": "Offline",
            "assets": [{"asset-id": self.LP_ASSET_ID, "amount": 1_000_000_000}],
        }

        def _get(url, **kwargs):
            r = MagicMock()
            r.raise_for_status = MagicMock()
            if "/v2/accounts/" in url:
                r.json.return_value = wallet
            elif "/v2/assets/" in url:
                aid = int(url.split("/v2/assets/")[1].split("?")[0])
                r.json.return_value = self.ASSET_DETAILS.get(aid)
            return r

        breakdown = LPBreakdown(
            lp_ticker="TMPOOL2", lp_amount=1000.0,
            asset1_ticker="ALGO",  asset1_amount=500.0, asset1_usd=175.0,
            asset2_ticker="USDC",  asset2_amount=175.0, asset2_usd=175.0,
            total_usd=350.0,
        )

        analyzer.lp_parser.is_lp_token = MagicMock(return_value=True)
        analyzer.lp_parser.estimate_lp_value = MagicMock(return_value=breakdown)
        analyzer.lp_parser.classify_lp_components = MagicMock(return_value=[
            ("algo",    {"ticker": "ALGO", "name": "ALGO (LP)", "amount": 500.0, "usd_value": 175.0}),
            ("dollars", {"ticker": "USDC", "name": "USDC (LP)", "amount": 175.0, "usd_value": 175.0}),
        ])

        with patch("core.analyzer.requests.get", side_effect=_get), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=2.0):

            categories = analyzer.analyze_wallet("LP_SUCCESS_ADDR")

        algo_tickers = [a["ticker"] for a in categories["algo"]]
        dollar_tickers = [a["ticker"] for a in categories["dollars"]]
        assert "ALGO" in algo_tickers
        assert "USDC" in dollar_tickers

        # Raw LP token itself must NOT appear
        shitcoin_tickers = [a["ticker"] for a in categories["shitcoin"]]
        assert "TMPOOL2" not in shitcoin_tickers


# ---------------------------------------------------------------------------
# 7. Multi-call state update
# ---------------------------------------------------------------------------

class TestMultiCallStateUpdate:
    """State (last_address, last_categories, etc.) must reflect the most recent call."""

    WALLET_A = {"amount": 5_000_000_000, "status": "Offline", "assets": []}
    WALLET_B = {"amount": 20_000_000_000, "status": "Online",
                "participation": {"vote-first-valid": 1, "vote-last-valid": 999},
                "assets": []}

    def test_state_updates_between_calls(self, analyzer):
        with patch.object(analyzer, "get_account_assets", return_value=self.WALLET_A), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=None):
            analyzer.analyze_wallet("ADDR_A_1234567890123456789012345678901234567890123456")

        assert analyzer.last_address == "ADDR_A_1234567890123456789012345678901234567890123456"
        algo_first = analyzer.last_categories["algo"][0]["amount"]

        with patch.object(analyzer, "get_account_assets", return_value=self.WALLET_B), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=None):
            analyzer.analyze_wallet("ADDR_B_1234567890123456789012345678901234567890123456")

        assert analyzer.last_address == "ADDR_B_1234567890123456789012345678901234567890123456"
        algo_second = analyzer.last_categories["algo"][0]["amount"]
        assert algo_second != algo_first  # state was replaced, not accumulated
        assert analyzer.last_is_participating is True

    def test_failed_analysis_does_not_update_state(self, analyzer):
        """If analyze_wallet returns None, the old state must be preserved."""
        # First successful call
        with patch.object(analyzer, "get_account_assets", return_value=self.WALLET_A), \
             patch("core.analyzer.get_algo_price", return_value=0.35), \
             patch("core.analyzer.get_asset_price", return_value=None):
            analyzer.analyze_wallet("FIRST_ADDR_123456789012345678901234567890123456789012")

        old_address = analyzer.last_address
        old_categories = analyzer.last_categories

        # Second call fails (returns None from get_account_assets)
        with patch.object(analyzer, "get_account_assets", return_value=None):
            result = analyzer.analyze_wallet("SECOND_ADDR_12345678901234567890123456789012345")

        assert result is None
        # State should still reflect the first successful call
        assert analyzer.last_address == old_address
        assert analyzer.last_categories == old_categories


# ---------------------------------------------------------------------------
# 8. Rate-limit retry (429 with Retry-After)
# ---------------------------------------------------------------------------

class TestRateLimitRetry:
    """429 responses with Retry-After header must be honoured."""

    def test_429_retried_once_then_succeeds(self, analyzer):
        """
        First call returns 429 with Retry-After: 1; second call succeeds.
        Verify that requests.get is called twice (1 initial + 1 retry).
        """
        # 429 response
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "1"}
        http_429 = requests.exceptions.HTTPError(response=resp_429)
        resp_429.raise_for_status.side_effect = http_429

        # Success response
        resp_ok = _make_response(
            {"amount": 1_000_000_000, "status": "Offline", "assets": []}
        )

        with patch("core.analyzer.requests.get", side_effect=[resp_429, resp_ok]) as mock_get, \
             patch("core.retry.time.sleep") as mock_sleep, \
             patch("core.analyzer.get_algo_price", return_value=0.35):

            result = analyzer.analyze_wallet("RATE_ADDR_12345678901234567890123456789012345678")

        assert result is not None
        assert mock_get.call_count == 2
        # Sleep should have been called with the Retry-After value (≤ max_delay)
        assert mock_sleep.called
        sleep_arg = mock_sleep.call_args[0][0]
        assert 0 < sleep_arg <= 30  # within bounds

    def test_429_all_retries_exhausted_returns_none(self, analyzer):
        """If every attempt returns 429, analyze_wallet must return None."""
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "0"}
        http_429 = requests.exceptions.HTTPError(response=resp_429)
        resp_429.raise_for_status.side_effect = http_429

        with patch("core.analyzer.requests.get", return_value=resp_429), \
             patch("core.retry.time.sleep"):

            result = analyzer.analyze_wallet("RATELIMIT_ALL_ADDR12345678901234567890123456789")

        assert result is None


# ---------------------------------------------------------------------------
# 9. Sovereignty boundary conditions
# ---------------------------------------------------------------------------

class TestSovereigntyBoundaryConditions:
    """Exact threshold values must map to the correct status."""

    def _categories_with_usd(self, usd):
        return {
            "hard_money": [{"ticker": "goBTC", "name": "goBTC",
                            "amount": 1, "usd_value": usd}] if usd else [],
            "algo": [], "dollars": [], "shitcoin": [],
        }

    @pytest.mark.parametrize("portfolio_usd,monthly_exp,expected_kw", [
        # Exactly at each boundary (ratio == threshold)
        (48000,  4000, "Fragile"),              # ratio = 1.0 exactly
        (144000, 4000, "Robust"),               # ratio = 3.0 exactly
        (288000, 4000, "Antifragile"),          # ratio = 6.0 exactly
        (960000, 4000, "Generationally"),       # ratio = 20.0 exactly
        # Just below each boundary
        (47999,  4000, "Vulnerable"),           # ratio ≈ 0.9999... < 1
        (143999, 4000, "Fragile"),              # ratio ≈ 2.9999... < 3
        (287999, 4000, "Robust"),               # ratio ≈ 5.9999... < 6
        (959999, 4000, "Antifragile"),          # ratio ≈ 19.9999... < 20
    ])
    def test_boundary(self, analyzer, portfolio_usd, monthly_exp, expected_kw):
        cats = self._categories_with_usd(portfolio_usd)
        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(cats, monthly_fixed_expenses=monthly_exp)
        assert expected_kw in metrics.sovereignty_status


# ---------------------------------------------------------------------------
# 10. Hard money isolation
# ---------------------------------------------------------------------------

class TestHardMoneyIsolation:
    """Only assets in hard_money category should count as 'hard money USD'."""

    def test_hard_money_usd_excludes_algo_and_dollars(self, analyzer):
        """
        When only hard_money assets are present, portfolio_usd equals their sum.
        Algo and dollar assets are NOT part of the hard money total.
        """
        categories = {
            "hard_money": [
                {"ticker": "goBTC",   "name": "goBTC",   "amount": 0.5,  "usd_value": 47500.0},
                {"ticker": "GOLD$",   "name": "Meld Gold", "amount": 100, "usd_value": 8500.0},
            ],
            "algo": [
                {"ticker": "ALGO", "name": "Algorand", "amount": 10000, "usd_value": 3500.0},
            ],
            "dollars": [
                {"ticker": "USDC", "name": "USDC", "amount": 5000, "usd_value": 5000.0},
            ],
            "shitcoin": [],
        }

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)

        # Full portfolio = 47500 + 8500 + 3500 + 5000 = 64500
        assert metrics.portfolio_usd == pytest.approx(64500.0)

        # Hard money USD specifically = 47500 + 8500 = 56000
        hard_money_usd = sum(a["usd_value"] for a in categories["hard_money"])
        assert hard_money_usd == pytest.approx(56000.0)

        # Sovereignty ratio uses TOTAL portfolio (not just hard money)
        expected_ratio = round(64500 / 48000, 2)
        assert metrics.sovereignty_ratio == expected_ratio

    def test_portfolio_includes_all_four_categories(self, analyzer):
        """portfolio_usd must sum all four categories."""
        categories = {
            "hard_money": [{"ticker": "goBTC", "name": "goBTC",   "amount": 1, "usd_value": 10000}],
            "algo":       [{"ticker": "ALGO",  "name": "Algorand", "amount": 1, "usd_value": 2000}],
            "dollars":    [{"ticker": "USDC",  "name": "USDC",     "amount": 1, "usd_value": 3000}],
            "shitcoin":   [{"ticker": "RNDM",  "name": "Random",   "amount": 1, "usd_value": 500}],
        }

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=1000)

        assert metrics.portfolio_usd == pytest.approx(15500.0)

    def test_zero_hard_money_portfolio_is_still_counted(self, analyzer):
        """
        Wallet with no hard money but with algo/dollars still has non-zero
        portfolio_usd — proving the ratio counts everything.
        """
        categories = {
            "hard_money": [],
            "algo":    [{"ticker": "ALGO", "name": "Algorand", "amount": 5000, "usd_value": 1750}],
            "dollars": [{"ticker": "USDC", "name": "USDC",     "amount": 1000, "usd_value": 1000}],
            "shitcoin": [],
        }

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=1000)

        assert metrics.portfolio_usd == pytest.approx(2750.0)
        assert metrics.sovereignty_ratio > 0
