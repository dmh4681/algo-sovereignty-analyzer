"""
Tests for core/pricing.py - Price fetching and error handling

These tests cover:
- Price caching
- API fallback chains
- Error handling for network failures
- Hardcoded price fallbacks
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import requests

from core.pricing import (
    get_hardcoded_price,
    get_algo_price,
    get_bitcoin_price,
    get_bitcoin_spot_price,
    get_gobtc_price,
    get_wbtc_price,
    get_gold_price,
    get_silver_price,
    get_gold_price_per_oz,
    get_silver_price_per_oz,
    get_asset_price,
    fetch_vestige_price,
    _meld_price_cache,
    MELD_CACHE_TTL_SECONDS,
)


class TestHardcodedPrices:
    """Tests for hardcoded fallback prices."""

    def test_stablecoin_prices(self):
        """Stablecoins should return $1."""
        stablecoins = ['USDC', 'USDT', 'DAI', 'STBL', 'FUSDC', 'FUSDT', 'FUSD']
        for coin in stablecoins:
            assert get_hardcoded_price(coin) == 1.0

    def test_algo_derivatives(self):
        """ALGO and derivatives should have fallback price."""
        algo_tokens = ['ALGO', 'FALGO', 'XALGO']
        for token in algo_tokens:
            price = get_hardcoded_price(token)
            assert price is not None
            assert price > 0

    def test_bitcoin_tokens(self):
        """Bitcoin tokens should have fallback price."""
        btc_tokens = ['BTC', 'WBTC', 'GOBTC', 'FGOBTC']
        for token in btc_tokens:
            price = get_hardcoded_price(token)
            assert price is not None
            assert price > 50000  # BTC should be > $50k

    def test_ethereum_tokens(self):
        """Ethereum tokens should have fallback price."""
        eth_tokens = ['ETH', 'WETH', 'GOETH', 'FGOETH']
        for token in eth_tokens:
            price = get_hardcoded_price(token)
            assert price is not None
            assert price > 1000  # ETH should be > $1k

    def test_precious_metals(self):
        """Gold and silver should have fallback prices."""
        assert get_hardcoded_price('GOLD$') is not None
        assert get_hardcoded_price('SILVER$') is not None

    def test_unknown_token(self):
        """Unknown tokens should return None."""
        assert get_hardcoded_price('RANDOMTOKEN') is None

    def test_case_insensitivity(self):
        """Price lookup should be case-insensitive."""
        assert get_hardcoded_price('usdc') == get_hardcoded_price('USDC')
        assert get_hardcoded_price('Algo') == get_hardcoded_price('ALGO')


class TestCoinGeckoFetching:
    """Tests for CoinGecko price fetching."""

    def test_algo_price_success(self):
        """Should return price on successful API call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'algorand': {'usd': 0.42}}
        mock_response.raise_for_status = MagicMock()

        with patch('core.pricing.requests.get', return_value=mock_response):
            price = get_algo_price()

        assert price == 0.42

    def test_algo_price_fallback_on_failure(self):
        """Should fall back to hardcoded price on API failure."""
        with patch('core.pricing.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            price = get_algo_price()

        # Should return hardcoded fallback
        assert price is not None
        assert price > 0

    def test_bitcoin_price_success(self):
        """Should return BTC price on success."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'bitcoin': {'usd': 95000}}
        mock_response.raise_for_status = MagicMock()

        with patch('core.pricing.requests.get', return_value=mock_response):
            price = get_bitcoin_price()

        assert price == 95000


class TestCoinbaseIntegration:
    """Tests for Coinbase BTC price fetching."""

    def test_bitcoin_spot_price_success(self):
        """Should return BTC spot price from Coinbase."""
        # Clear cache first
        _meld_price_cache['btc_spot'] = {'price': None, 'expires': None}

        mock_response = MagicMock()
        mock_response.json.return_value = {'data': {'amount': '98500.00'}}
        mock_response.raise_for_status = MagicMock()

        with patch('core.pricing.requests.get', return_value=mock_response):
            price = get_bitcoin_spot_price()

        assert price == 98500.0

    def test_bitcoin_spot_caching(self):
        """Should use cached price within TTL."""
        cached_price = 97000.0
        _meld_price_cache['btc_spot'] = {
            'price': cached_price,
            'expires': datetime.now() + timedelta(seconds=100)
        }

        # Should not make API call, return cached value
        price = get_bitcoin_spot_price()
        assert price == cached_price

    def test_bitcoin_spot_fallback_chain(self):
        """Should fall back to CoinGecko then hardcoded on Coinbase failure."""
        _meld_price_cache['btc_spot'] = {'price': None, 'expires': None}

        with patch('core.pricing.requests.get') as mock_get:
            # Coinbase fails
            mock_get.side_effect = requests.exceptions.Timeout("Timeout")

            # Mock CoinGecko fallback
            with patch('core.pricing.get_bitcoin_price', return_value=None):
                price = get_bitcoin_spot_price()

        # Should return hardcoded fallback
        assert price is not None
        assert price > 50000


class TestVestigePricing:
    """Tests for Vestige API price fetching."""

    def test_vestige_price_success(self):
        """Should return price from Vestige API."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{'price': 0.35}]
        mock_response.raise_for_status = MagicMock()

        with patch('core.pricing.requests.get', return_value=mock_response):
            price = fetch_vestige_price(31566704)  # USDC ASA ID

        assert price == 0.35

    def test_vestige_timeout_handling(self):
        """Should handle timeout gracefully."""
        with patch('core.pricing.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Timeout")
            price = fetch_vestige_price(12345)

        assert price is None

    def test_vestige_network_error_handling(self):
        """Should handle network errors gracefully."""
        with patch('core.pricing.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            price = fetch_vestige_price(12345)

        assert price is None

    def test_vestige_empty_response(self):
        """Should handle empty response."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        with patch('core.pricing.requests.get', return_value=mock_response):
            price = fetch_vestige_price(12345)

        assert price is None

    def test_vestige_zero_price(self):
        """Should handle zero price as invalid."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{'price': 0}]
        mock_response.raise_for_status = MagicMock()

        with patch('core.pricing.requests.get', return_value=mock_response):
            price = fetch_vestige_price(12345)

        assert price is None


class TestGoBTCPricing:
    """Tests for goBTC price with fallback chain."""

    def test_gobtc_vestige_success(self):
        """Should use Vestige price when available."""
        _meld_price_cache['gobtc'] = {'price': None, 'expires': None}

        with patch('core.pricing.fetch_vestige_price', return_value=97500.0):
            price = get_gobtc_price()

        assert price == 97500.0

    def test_gobtc_fallback_to_spot(self):
        """Should fall back to BTC spot price on Vestige failure."""
        _meld_price_cache['gobtc'] = {'price': None, 'expires': None}

        with patch('core.pricing.fetch_vestige_price', return_value=None):
            with patch('core.pricing.get_bitcoin_spot_price', return_value=98000.0):
                price = get_gobtc_price()

        assert price == 98000.0

    def test_gobtc_caching(self):
        """Should cache goBTC price."""
        cached_price = 96000.0
        _meld_price_cache['gobtc'] = {
            'price': cached_price,
            'expires': datetime.now() + timedelta(seconds=100)
        }

        price = get_gobtc_price()
        assert price == cached_price


class TestYahooFinancePricing:
    """Tests for Yahoo Finance commodity prices."""

    def test_gold_price_success(self):
        """Should return gold price per gram."""
        with patch('core.pricing.get_gold_price_per_oz', return_value=2650.0):
            price = get_gold_price()

        # Should convert oz to gram
        expected = 2650.0 / 31.1035
        assert abs(price - expected) < 0.01

    def test_silver_price_success(self):
        """Should return silver price per gram."""
        with patch('core.pricing.get_silver_price_per_oz', return_value=30.0):
            price = get_silver_price()

        expected = 30.0 / 31.1035
        assert abs(price - expected) < 0.01

    def test_gold_oz_fallback(self):
        """Should fall back to hardcoded price on API failure."""
        with patch('core.pricing._fetch_yahoo_finance_price', return_value=None):
            price = get_gold_price_per_oz()

        # Should return hardcoded fallback
        assert price is not None
        assert price > 2000  # Gold should be > $2000/oz

    def test_silver_oz_fallback(self):
        """Should fall back to hardcoded price on API failure."""
        with patch('core.pricing._fetch_yahoo_finance_price', return_value=None):
            price = get_silver_price_per_oz()

        assert price is not None
        assert price > 20  # Silver should be > $20/oz


class TestAssetPriceRouter:
    """Tests for the main get_asset_price router function."""

    def test_stablecoin_no_api_call(self):
        """Stablecoins should return $1 without API call."""
        stablecoins = ['USDC', 'USDT', 'DAI', 'STBL']
        for coin in stablecoins:
            price = get_asset_price(coin)
            assert price == 1.0

    def test_vestige_priority_with_asset_id(self):
        """Should try Vestige first when asset_id is provided."""
        with patch('core.pricing.fetch_vestige_price', return_value=0.50) as mock_vestige:
            price = get_asset_price('RANDOM', asset_id=12345)

        mock_vestige.assert_called_once_with(12345)
        assert price == 0.50

    def test_fallback_when_no_asset_id(self):
        """Should use fallback pricing when no asset_id."""
        with patch('core.pricing.get_algo_price', return_value=0.40):
            price = get_asset_price('ALGO')

        assert price == 0.40

    def test_gold_routing(self):
        """Should route gold tokens to gold price."""
        gold_tokens = ['GOLD$', 'XAUT', 'PAXG']

        with patch('core.pricing.get_gold_price', return_value=85.0):
            for token in gold_tokens:
                price = get_asset_price(token)
                assert price == 85.0

    def test_silver_routing(self):
        """Should route SILVER$ to silver price."""
        with patch('core.pricing.get_silver_price', return_value=1.0):
            price = get_asset_price('SILVER$')
            assert price == 1.0

    def test_hardcoded_last_resort(self):
        """Should return hardcoded price as last resort."""
        # Unknown token without asset_id
        price = get_asset_price('ALGO', asset_id=None)

        # Should fall through to get_algo_price or hardcoded
        assert price is not None


class TestCacheTTL:
    """Tests for cache time-to-live behavior."""

    def test_cache_ttl_constant(self):
        """Cache TTL should be 5 minutes (300 seconds)."""
        assert MELD_CACHE_TTL_SECONDS == 300

    def test_expired_cache_triggers_refresh(self):
        """Expired cache should trigger API call."""
        _meld_price_cache['gold'] = {
            'price': 80.0,
            'expires': datetime.now() - timedelta(seconds=1)  # Expired
        }

        mock_response = MagicMock()
        mock_response.json.return_value = [{'price': 85.0}]
        mock_response.raise_for_status = MagicMock()

        with patch('core.pricing.fetch_vestige_price', return_value=85.0):
            from core.pricing import get_meld_gold_price
            price = get_meld_gold_price()

        # Should get new price, not cached
        assert price == 85.0
