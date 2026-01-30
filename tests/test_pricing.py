"""
Tests for core/pricing.py - Error handling, edge cases, and fallback behavior.

Covers:
- API timeout returns graceful fallback
- Invalid/unknown asset ID returns None
- Rate limited (429) response triggers retry or fallback
- Zero/negative prices are rejected
- Fallback from Vestige to CoinGecko/hardcoded works
"""
import pytest
import requests
from unittest.mock import patch, MagicMock

from core.pricing import (
    _fetch_price,
    _fetch_vestige_price_raw,
    _fetch_coinbase_btc_price,
    fetch_vestige_price,
    get_algo_price,
    get_bitcoin_spot_price,
    get_asset_price,
    get_gobtc_price,
    get_hardcoded_price,
    get_gold_price_per_oz,
    get_silver_price_per_oz,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear price cache before each test to avoid stale state."""
    from core.cache import get_cache
    cache = get_cache()
    cache.invalidate_prices()
    yield
    cache.invalidate_prices()


class TestAPITimeout:
    """API timeout should return None or graceful fallback."""

    @patch("core.pricing.requests.get")
    def test_coingecko_timeout_returns_none(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("timed out")
        assert _fetch_price("algorand") is None

    @patch("core.pricing.requests.get")
    def test_vestige_timeout_returns_none(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("timed out")
        assert _fetch_vestige_price_raw(31566704) is None

    @patch("core.pricing.requests.get")
    def test_coinbase_timeout_returns_none(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("timed out")
        assert _fetch_coinbase_btc_price() is None

    @patch("core.pricing.requests.get")
    def test_algo_price_falls_back_on_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        result = get_algo_price()
        assert result == get_hardcoded_price("ALGO")
        assert result is not None


class TestInvalidAsset:
    """Invalid or unknown asset IDs should return None without crashing."""

    @patch("core.pricing.requests.get")
    def test_unknown_asset_id_empty_response(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        assert _fetch_vestige_price_raw(999999999) is None

    @patch("core.pricing.requests.get")
    def test_unknown_coingecko_coin_id(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        assert _fetch_price("nonexistent-coin-xyz") is None

    def test_get_asset_price_unknown_ticker_no_asset_id(self):
        assert get_asset_price("ZZZZNOTREAL") is None

    def test_hardcoded_price_unknown_ticker(self):
        assert get_hardcoded_price("DOESNOTEXIST") is None


class TestRateLimiting:
    """429 rate-limited responses should be handled gracefully."""

    @patch("core.pricing.requests.get")
    def test_coingecko_429_retries_then_none(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "429 Too Many Requests", response=mock_resp
        )
        mock_get.return_value = mock_resp
        assert _fetch_price("bitcoin") is None
        assert mock_get.call_count == 3

    @patch("core.pricing.requests.get")
    def test_vestige_429_returns_none(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "429 Too Many Requests", response=mock_resp
        )
        mock_get.return_value = mock_resp
        assert _fetch_vestige_price_raw(31566704) is None


class TestZeroAndNegativePrice:
    """Zero and negative prices should be rejected."""

    @patch("core.pricing.requests.get")
    def test_vestige_zero_price_rejected(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"price": 0}]
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        assert _fetch_vestige_price_raw(31566704) is None

    @patch("core.pricing.requests.get")
    def test_vestige_negative_price_rejected(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"price": -5.0}]
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        assert _fetch_vestige_price_raw(31566704) is None

    @patch("core.pricing.requests.get")
    def test_vestige_null_price_rejected(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"price": None}]
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        assert _fetch_vestige_price_raw(31566704) is None


class TestFallbackBehavior:
    """Fallback chains should work when primary source fails."""

    @patch("core.pricing.requests.get")
    def test_bitcoin_spot_coinbase_fails_falls_to_coingecko(self, mock_get):
        def side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            if "coinbase" in url:
                raise requests.exceptions.ConnectionError("down")
            resp = MagicMock()
            resp.json.return_value = {"bitcoin": {"usd": 95000.0}}
            resp.raise_for_status = MagicMock()
            return resp

        mock_get.side_effect = side_effect
        assert get_bitcoin_spot_price() == 95000.0

    @patch("core.pricing.requests.get")
    def test_bitcoin_spot_all_apis_fail_hardcoded(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("down")
        assert get_bitcoin_spot_price() == get_hardcoded_price("BTC")

    @patch("core.pricing.requests.get")
    def test_gold_price_api_fail_returns_hardcoded(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("down")
        assert get_gold_price_per_oz() == 4500.0

    @patch("core.pricing.requests.get")
    def test_silver_price_api_fail_returns_hardcoded(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("down")
        assert get_silver_price_per_oz() == 70.0

    @patch("core.pricing.requests.get")
    def test_asset_price_vestige_fails_falls_to_ticker(self, mock_get):
        def side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            if "vestige" in url:
                raise requests.exceptions.ConnectionError("down")
            resp = MagicMock()
            resp.json.return_value = {"algorand": {"usd": 0.40}}
            resp.raise_for_status = MagicMock()
            return resp

        mock_get.side_effect = side_effect
        assert get_asset_price("ALGO", asset_id=0) is not None

    @patch("core.pricing.requests.get")
    def test_gobtc_vestige_fails_falls_to_btc_spot(self, mock_get):
        def side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            if "vestige" in url:
                raise requests.exceptions.ConnectionError("down")
            if "coinbase" in url:
                resp = MagicMock()
                resp.json.return_value = {"data": {"amount": "97000.00"}}
                resp.raise_for_status = MagicMock()
                return resp
            resp = MagicMock()
            resp.json.return_value = {"bitcoin": {"usd": 97000.0}}
            resp.raise_for_status = MagicMock()
            return resp

        mock_get.side_effect = side_effect
        result = get_gobtc_price()
        assert result is not None
        assert result > 0
