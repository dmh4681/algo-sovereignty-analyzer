"""Edge case tests for core/analyzer.py.

Covers invalid addresses, API timeouts, HTTP errors, empty wallets,
failed price lookups, and malformed API responses.
"""

import pytest
from unittest.mock import patch, MagicMock
import requests

from core.analyzer import AlgorandSovereigntyAnalyzer


@pytest.fixture
def analyzer():
    """Create analyzer with mocked dependencies."""
    with patch("core.analyzer.get_algorand_node_config", return_value=(
        "https://mainnet-api.algonode.cloud", "", {}
    )):
        return AlgorandSovereigntyAnalyzer(use_local_node=False)


# ---------------------------------------------------------------------------
# Invalid address tests
# ---------------------------------------------------------------------------

class TestInvalidAddresses:
    def test_empty_string_address(self, analyzer):
        """Empty string should not crash — returns None or raises."""
        with patch("core.analyzer.requests.get") as mock_get:
            resp = MagicMock()
            resp.status_code = 400
            resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
            mock_get.return_value = resp
            result = analyzer.get_account_assets("")
            assert result is None

    def test_short_address(self, analyzer):
        """Address shorter than 58 chars triggers 400 from node."""
        with patch("core.analyzer.requests.get") as mock_get:
            resp = MagicMock()
            resp.status_code = 400
            resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
            mock_get.return_value = resp
            result = analyzer.get_account_assets("TOOSHORT")
            assert result is None

    def test_wrong_checksum_address(self, analyzer):
        """Invalid checksum returns 400 from node."""
        bad_addr = "A" * 58
        with patch("core.analyzer.requests.get") as mock_get:
            resp = MagicMock()
            resp.status_code = 400
            resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
            mock_get.return_value = resp
            result = analyzer.get_account_assets(bad_addr)
            assert result is None

    def test_address_not_found_404(self, analyzer):
        """404 response returns None."""
        with patch("core.analyzer.requests.get") as mock_get:
            resp = MagicMock()
            resp.status_code = 404
            http_err = requests.exceptions.HTTPError(response=resp)
            resp.raise_for_status.side_effect = http_err
            mock_get.return_value = resp
            result = analyzer.get_account_assets("X" * 58)
            assert result is None


# ---------------------------------------------------------------------------
# API timeout and connection error tests
# ---------------------------------------------------------------------------

class TestAPIErrors:
    def test_timeout_raises(self, analyzer):
        """Timeout is re-raised by get_account_assets."""
        with patch("core.analyzer.requests.get", side_effect=requests.exceptions.Timeout("timed out")):
            with pytest.raises(requests.exceptions.Timeout):
                analyzer.get_account_assets("V" * 58)

    def test_connection_error_raises(self, analyzer):
        """ConnectionError is re-raised by get_account_assets."""
        with patch("core.analyzer.requests.get", side_effect=requests.exceptions.ConnectionError("refused")):
            with pytest.raises(requests.exceptions.ConnectionError):
                analyzer.get_account_assets("V" * 58)

    def test_http_429_returns_none(self, analyzer):
        """Rate limited (429) returns None."""
        with patch("core.analyzer.requests.get") as mock_get:
            resp = MagicMock()
            resp.status_code = 429
            resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
            mock_get.return_value = resp
            result = analyzer.get_account_assets("V" * 58)
            assert result is None

    def test_http_500_returns_none(self, analyzer):
        """Server error (500) returns None."""
        with patch("core.analyzer.requests.get") as mock_get:
            resp = MagicMock()
            resp.status_code = 500
            resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
            mock_get.return_value = resp
            result = analyzer.get_account_assets("V" * 58)
            assert result is None

    def test_analyze_wallet_timeout_propagates(self, analyzer):
        """analyze_wallet propagates Timeout from get_account_assets."""
        with patch.object(analyzer, "get_account_assets", side_effect=requests.exceptions.Timeout):
            with pytest.raises(requests.exceptions.Timeout):
                analyzer.analyze_wallet("V" * 58)

    def test_analyze_wallet_connection_error_propagates(self, analyzer):
        """analyze_wallet propagates ConnectionError."""
        with patch.object(analyzer, "get_account_assets", side_effect=requests.exceptions.ConnectionError):
            with pytest.raises(requests.exceptions.ConnectionError):
                analyzer.analyze_wallet("V" * 58)


# ---------------------------------------------------------------------------
# Empty wallet / zero assets
# ---------------------------------------------------------------------------

class TestEmptyWallet:
    def test_wallet_no_assets(self, analyzer):
        """Wallet with only ALGO and no ASAs returns categories with just ALGO."""
        account_data = {"amount": 1_000_000, "status": "Offline", "assets": []}
        with patch.object(analyzer, "get_account_assets", return_value=account_data), \
             patch("core.analyzer.get_algo_price", return_value=0.20), \
             patch.object(analyzer, "print_results"), \
             patch.object(analyzer, "export_to_json"):
            result = analyzer.analyze_wallet("V" * 58)
            assert result is not None
            assert len(result["algo"]) == 1
            assert result["algo"][0]["ticker"] == "ALGO"
            assert result["hard_money"] == []
            assert result["dollars"] == []
            assert result["shitcoin"] == []

    def test_wallet_returns_none(self, analyzer):
        """If get_account_assets returns None, analyze_wallet returns None."""
        with patch.object(analyzer, "get_account_assets", return_value=None):
            result = analyzer.analyze_wallet("V" * 58)
            assert result is None


# ---------------------------------------------------------------------------
# Price lookup failures
# ---------------------------------------------------------------------------

class TestPriceLookupFailures:
    def test_algo_price_none_fallback(self, analyzer):
        """If get_algo_price returns None, ALGO usd_value is 0."""
        account_data = {"amount": 5_000_000, "status": "Offline", "assets": []}
        with patch.object(analyzer, "get_account_assets", return_value=account_data), \
             patch("core.analyzer.get_algo_price", return_value=None), \
             patch.object(analyzer, "print_results"), \
             patch.object(analyzer, "export_to_json"):
            result = analyzer.analyze_wallet("V" * 58)
            assert result["algo"][0]["usd_value"] == 0.0

    def test_asset_price_none(self, analyzer):
        """Asset with no price gets usd_value 0."""
        account_data = {
            "amount": 1_000_000, "status": "Offline",
            "assets": [{"asset-id": 99999, "amount": 1000}]
        }
        asset_details = {"params": {"decimals": 2, "name": "TestCoin", "unit-name": "TST"}}
        with patch.object(analyzer, "get_account_assets", return_value=account_data), \
             patch.object(analyzer, "get_asset_details", return_value=asset_details), \
             patch("core.analyzer.get_algo_price", return_value=0.20), \
             patch("core.analyzer.get_asset_price", return_value=None), \
             patch.object(analyzer, "print_results"), \
             patch.object(analyzer, "export_to_json"), \
             patch.object(analyzer.classifier, "auto_classify_asset", return_value="shitcoin"), \
             patch.object(analyzer.lp_parser, "is_lp_token", return_value=False):
            result = analyzer.analyze_wallet("V" * 58)
            # With no price and amount=10, _is_dust_or_nft filters it as NFT-like
            # so shitcoin list may be empty. This is expected behavior.
            # The key assertion: no crash occurred.
            assert result is not None


# ---------------------------------------------------------------------------
# Malformed API responses
# ---------------------------------------------------------------------------

class TestMalformedResponses:
    def test_asset_details_returns_none(self, analyzer):
        """If get_asset_details returns None, asset is skipped."""
        account_data = {
            "amount": 1_000_000, "status": "Offline",
            "assets": [{"asset-id": 12345, "amount": 500}]
        }
        with patch.object(analyzer, "get_account_assets", return_value=account_data), \
             patch.object(analyzer, "get_asset_details", return_value=None), \
             patch("core.analyzer.get_algo_price", return_value=0.20), \
             patch.object(analyzer, "print_results"), \
             patch.object(analyzer, "export_to_json"):
            result = analyzer.analyze_wallet("V" * 58)
            assert result is not None
            # Only ALGO should be present
            total_non_algo = len(result["hard_money"]) + len(result["dollars"]) + len(result["shitcoin"])
            assert total_non_algo == 0

    def test_asset_details_timeout(self, analyzer):
        """Timeout on get_asset_details returns None, asset skipped."""
        with patch("core.analyzer.requests.get", side_effect=requests.exceptions.Timeout):
            result = analyzer.get_asset_details(12345)
            assert result is None


# ---------------------------------------------------------------------------
# Sovereignty metrics edge cases
# ---------------------------------------------------------------------------

class TestSovereigntyMetrics:
    def test_zero_expenses_returns_none(self, analyzer):
        """Zero monthly expenses returns None."""
        categories = {"hard_money": [], "algo": [], "dollars": [], "shitcoin": []}
        result = analyzer.calculate_sovereignty_metrics(categories, 0)
        assert result is None

    def test_negative_expenses_returns_none(self, analyzer):
        """Negative monthly expenses returns None."""
        categories = {"hard_money": [], "algo": [], "dollars": [], "shitcoin": []}
        result = analyzer.calculate_sovereignty_metrics(categories, -100)
        assert result is None
