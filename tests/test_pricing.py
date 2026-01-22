"""
Tests for core/pricing.py - Price fetching and error handling

These tests cover:
- Price caching
- API fallback chains
- Error handling for network failures
- Hardcoded price fallbacks
- Retry logic with exponential backoff
- Timeout handling

All tests are fully mocked to avoid external API dependencies.
Tests use fixtures from conftest.py for consistent mocking.
"""
import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
import requests

from core.pricing import (
    get_hardcoded_price,
    get_algo_price,
    get_bitcoin_price,
    get_ethereum_price,
    get_bitcoin_spot_price,
    get_gobtc_price,
    get_wbtc_price,
    get_gold_price,
    get_silver_price,
    get_gold_price_per_oz,
    get_silver_price_per_oz,
    get_meld_gold_price,
    get_meld_silver_price,
    get_asset_price,
    fetch_vestige_price,
    _fetch_price,
    _fetch_yahoo_finance_price,
    _fetch_meld_price_from_vestige,
    _meld_price_cache,
    MELD_CACHE_TTL_SECONDS,
    GOBTC_ASA,
    WBTC_ASA,
    MELD_GOLD_ASA,
    MELD_SILVER_ASA,
)

from tests.fixtures.price_data import (
    MOCK_PRICES,
    COINGECKO_ALGO_SUCCESS,
    COINGECKO_BTC_SUCCESS,
    COINGECKO_ETH_SUCCESS,
    COINBASE_BTC_SUCCESS,
    YAHOO_GOLD_SUCCESS,
    YAHOO_SILVER_SUCCESS,
    VESTIGE_GOBTC_SUCCESS,
    VESTIGE_WBTC_SUCCESS,
    VESTIGE_GOLD_SUCCESS,
    VESTIGE_SILVER_SUCCESS,
    make_vestige_price_response,
    make_valid_cache_entry,
    make_expired_cache_entry,
    make_empty_cache_entry,
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

    def test_algo_price_fallback_on_failure(self, mock_pricing_time_sleep):
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


class TestRetryLogic:
    """Tests for retry logic with exponential backoff."""

    def test_coingecko_retry_on_failure(self, mock_pricing_time_sleep):
        """Should retry up to 3 times on CoinGecko API failure."""
        with patch('core.pricing.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            result = _fetch_price('algorand')

        # Should have attempted 3 times
        assert mock_get.call_count == 3
        assert result is None

    def test_coingecko_retry_success_on_second_attempt(self, mock_pricing_time_sleep):
        """Should succeed if API works on retry."""
        mock_success = MagicMock()
        mock_success.json.return_value = COINGECKO_ALGO_SUCCESS
        mock_success.raise_for_status = MagicMock()

        with patch('core.pricing.requests.get') as mock_get:
            # Fail first, succeed second
            mock_get.side_effect = [
                requests.exceptions.RequestException("Temporary failure"),
                mock_success
            ]
            result = _fetch_price('algorand')

        assert mock_get.call_count == 2
        assert result == 0.42

    def test_yahoo_retry_on_failure(self, mock_pricing_time_sleep):
        """Should retry up to 3 times on Yahoo Finance API failure."""
        with patch('core.pricing.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            result = _fetch_yahoo_finance_price('GC=F')

        # Should have attempted 3 times
        assert mock_get.call_count == 3
        assert result is None

    def test_exponential_backoff_timing(self, mock_pricing_time_sleep):
        """Should use exponential backoff between retries."""
        with patch('core.pricing.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            with patch('core.pricing.time.sleep') as mock_sleep:
                _fetch_price('algorand')

        # Verify backoff: 1s, 2s (exponential)
        assert mock_sleep.call_count == 2  # Sleep after 1st and 2nd failure
        mock_sleep.assert_any_call(1)  # First backoff
        mock_sleep.assert_any_call(2)  # Second backoff


class TestTimeoutHandling:
    """Tests for timeout handling across all APIs."""

    def test_coingecko_timeout(self, mock_pricing_time_sleep):
        """CoinGecko should handle timeout gracefully."""
        with patch('core.pricing.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
            result = _fetch_price('bitcoin')

        assert result is None

    def test_coinbase_timeout(self):
        """Coinbase should handle timeout and fall back."""
        _meld_price_cache['btc_spot'] = make_empty_cache_entry()

        with patch('core.pricing.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Timeout")
            with patch('core.pricing.get_bitcoin_price', return_value=97500.0):
                result = get_bitcoin_spot_price()

        # Should fall back to CoinGecko
        assert result == 97500.0

    def test_vestige_timeout(self):
        """Vestige should handle timeout gracefully."""
        with patch('core.pricing.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Timeout")
            result = fetch_vestige_price(GOBTC_ASA)

        assert result is None

    def test_yahoo_timeout(self, mock_pricing_time_sleep):
        """Yahoo Finance should handle timeout gracefully."""
        with patch('core.pricing.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Timeout")
            result = _fetch_yahoo_finance_price('GC=F')

        assert result is None


class TestMeldPricing:
    """Tests for Meld Gold and Silver pricing."""

    def test_meld_gold_vestige_success(self):
        """Should return Vestige price for Meld Gold."""
        _meld_price_cache['gold'] = make_empty_cache_entry()

        with patch('core.pricing._fetch_meld_price_from_vestige', return_value=85.25):
            price = get_meld_gold_price()

        assert price == 85.25

    def test_meld_gold_fallback_to_spot(self):
        """Should fall back to spot gold price on Vestige failure."""
        _meld_price_cache['gold'] = make_empty_cache_entry()

        with patch('core.pricing._fetch_meld_price_from_vestige', return_value=None):
            with patch('core.pricing.get_gold_price_per_oz', return_value=2650.0):
                price = get_meld_gold_price()

        # Should be approximately 2650/31.1035
        expected = 2650.0 / 31.1035
        assert abs(price - expected) < 0.1

    def test_meld_gold_hardcoded_fallback(self):
        """Should fall back to hardcoded price as last resort."""
        _meld_price_cache['gold'] = make_empty_cache_entry()

        with patch('core.pricing._fetch_meld_price_from_vestige', return_value=None):
            with patch('core.pricing.get_gold_price_per_oz', return_value=None):
                price = get_meld_gold_price()

        assert price is not None
        assert price > 0

    def test_meld_silver_vestige_success(self):
        """Should return Vestige price for Meld Silver."""
        _meld_price_cache['silver'] = make_empty_cache_entry()

        with patch('core.pricing._fetch_meld_price_from_vestige', return_value=1.02):
            price = get_meld_silver_price()

        assert price == 1.02

    def test_meld_silver_fallback_to_spot(self):
        """Should fall back to spot silver price on Vestige failure."""
        _meld_price_cache['silver'] = make_empty_cache_entry()

        with patch('core.pricing._fetch_meld_price_from_vestige', return_value=None):
            with patch('core.pricing.get_silver_price_per_oz', return_value=31.50):
                price = get_meld_silver_price()

        # Should be approximately 31.5/31.1035
        expected = 31.50 / 31.1035
        assert abs(price - expected) < 0.1

    def test_meld_price_caching(self):
        """Should use cached Meld price within TTL."""
        _meld_price_cache['gold'] = make_valid_cache_entry(88.0)
        _meld_price_cache['silver'] = make_valid_cache_entry(1.10)

        gold_price = get_meld_gold_price()
        silver_price = get_meld_silver_price()

        assert gold_price == 88.0
        assert silver_price == 1.10


class TestWBTCPricing:
    """Tests for WBTC (Wormhole-bridged) pricing."""

    def test_wbtc_vestige_success(self):
        """Should use Vestige price when available."""
        _meld_price_cache['wbtc'] = make_empty_cache_entry()

        with patch('core.pricing.fetch_vestige_price', return_value=97200.0):
            price = get_wbtc_price()

        assert price == 97200.0

    def test_wbtc_fallback_to_spot(self):
        """Should fall back to BTC spot price on Vestige failure."""
        _meld_price_cache['wbtc'] = make_empty_cache_entry()

        with patch('core.pricing.fetch_vestige_price', return_value=None):
            with patch('core.pricing.get_bitcoin_spot_price', return_value=98000.0):
                price = get_wbtc_price()

        assert price == 98000.0

    def test_wbtc_caching(self):
        """Should cache WBTC price."""
        _meld_price_cache['wbtc'] = make_valid_cache_entry(96500.0)

        price = get_wbtc_price()
        assert price == 96500.0


class TestVestigeFreeAPIFallback:
    """Tests for Vestige free API fallback."""

    def test_vestige_free_api_used_when_main_fails(self):
        """Should try free API when main API fails."""
        _meld_price_cache['gold'] = make_empty_cache_entry()

        def mock_get(url, **kwargs):
            response = MagicMock()
            response.raise_for_status = MagicMock()

            if 'api.vestigelabs.org' in url:
                # Main API fails (returns nothing)
                response.json.return_value = []
            elif 'free-api.vestige.fi' in url:
                # Free API returns price in ALGO
                response.json.return_value = {'price': 243.57}
            return response

        with patch('core.pricing.requests.get', side_effect=mock_get):
            with patch('core.pricing.get_algo_price', return_value=0.35):
                price = _fetch_meld_price_from_vestige(MELD_GOLD_ASA)

        # Price should be converted from ALGO to USD
        # 243.57 ALGO * 0.35 USD/ALGO = ~85.25 USD
        assert price is not None
        assert abs(price - 85.25) < 1


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_negative_price_rejected(self):
        """Negative prices should be treated as invalid."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{'price': -1.0}]
        mock_response.raise_for_status = MagicMock()

        with patch('core.pricing.requests.get', return_value=mock_response):
            price = fetch_vestige_price(12345)

        assert price is None

    def test_null_price_rejected(self):
        """Null prices should be treated as invalid."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{'price': None}]
        mock_response.raise_for_status = MagicMock()

        with patch('core.pricing.requests.get', return_value=mock_response):
            price = fetch_vestige_price(12345)

        assert price is None

    def test_malformed_json_handled(self):
        """Should handle malformed JSON responses gracefully."""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = MagicMock()

        with patch('core.pricing.requests.get', return_value=mock_response):
            price = fetch_vestige_price(12345)

        assert price is None

    def test_http_500_error_handled(self):
        """Should handle HTTP 500 errors gracefully."""
        with patch('core.pricing.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
            mock_get.return_value = mock_response
            price = fetch_vestige_price(12345)

        assert price is None

    def test_http_429_rate_limit_handled(self, mock_pricing_time_sleep):
        """Should handle HTTP 429 rate limit errors gracefully."""
        with patch('core.pricing.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")
            mock_get.return_value = mock_response
            price = _fetch_price('algorand')

        assert price is None


class TestEthereumPricing:
    """Tests for Ethereum price fetching."""

    def test_ethereum_price_success(self):
        """Should return ETH price on success."""
        mock_response = MagicMock()
        mock_response.json.return_value = COINGECKO_ETH_SUCCESS
        mock_response.raise_for_status = MagicMock()

        with patch('core.pricing.requests.get', return_value=mock_response):
            price = get_ethereum_price()

        assert price == 3250.0

    def test_ethereum_routing_in_asset_price(self):
        """Should route ETH tokens to ethereum price."""
        eth_tokens = ['ETH', 'WETH', 'GOETH', 'FGOETH']

        with patch('core.pricing.get_ethereum_price', return_value=3250.0):
            for token in eth_tokens:
                price = get_asset_price(token)
                assert price == 3250.0


class TestFullFallbackChains:
    """Tests for complete fallback chains across multiple APIs."""

    def test_gobtc_full_fallback_chain(self):
        """goBTC should fall through Vestige -> BTC Spot -> Hardcoded."""
        _meld_price_cache['gobtc'] = make_empty_cache_entry()
        _meld_price_cache['btc_spot'] = make_empty_cache_entry()

        with patch('core.pricing.fetch_vestige_price', return_value=None):
            with patch('core.pricing.requests.get') as mock_get:
                mock_get.side_effect = requests.exceptions.Timeout("All APIs down")
                with patch('core.pricing.get_bitcoin_price', return_value=None):
                    price = get_gobtc_price()

        # Should return hardcoded fallback
        assert price is not None
        assert price >= 50000

    def test_meld_gold_full_fallback_chain(self, mock_pricing_time_sleep):
        """Meld Gold should fall through Vestige -> Yahoo -> Hardcoded."""
        _meld_price_cache['gold'] = make_empty_cache_entry()

        with patch('core.pricing._fetch_meld_price_from_vestige', return_value=None):
            with patch('core.pricing._fetch_yahoo_finance_price', return_value=None):
                price = get_meld_gold_price()

        # Should return hardcoded fallback
        assert price is not None
        assert price > 0


class TestDeterministicBehavior:
    """Tests ensuring deterministic behavior for CI/CD."""

    def test_no_network_call_for_stablecoins(self):
        """Stablecoins should never trigger network calls."""
        stablecoins = ['USDC', 'USDT', 'FUSDC', 'FUSDT', 'DAI', 'FUSD', 'STBL']

        with patch('core.pricing.requests.get') as mock_get:
            for coin in stablecoins:
                price = get_asset_price(coin)
                assert price == 1.0

            # Should never have made a network call
            mock_get.assert_not_called()

    def test_cache_prevents_repeated_api_calls(self):
        """Cached prices should prevent additional API calls."""
        _meld_price_cache['btc_spot'] = make_valid_cache_entry(97000.0)

        with patch('core.pricing.requests.get') as mock_get:
            # Call multiple times
            for _ in range(5):
                price = get_bitcoin_spot_price()
                assert price == 97000.0

            # Should not have made any API calls
            mock_get.assert_not_called()

    def test_fixtures_provide_consistent_prices(self):
        """Test fixtures should provide consistent, deterministic prices."""
        # Verify MOCK_PRICES fixture consistency
        assert MOCK_PRICES['ALGO'] == 0.42
        assert MOCK_PRICES['BTC'] == 97500.00
        assert MOCK_PRICES['ETH'] == 3250.00
        assert MOCK_PRICES['USDC'] == 1.00
        assert MOCK_PRICES['GOLD$'] == 85.25
        assert MOCK_PRICES['SILVER$'] == 1.02
