"""
Pytest configuration and shared fixtures.

This module provides:
- Automatic API mocking to prevent external network calls during tests
- Reusable fixtures for pricing, analyzer, and other modules
- Cache management helpers for deterministic tests
- Mock response factories for various external APIs

All tests should be fully isolated and deterministic, with no dependencies
on external services (CoinGecko, Coinbase, Yahoo Finance, Vestige, etc.).
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import requests

# Add the project root to path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    make_empty_cache_entry,
    url_matches_coingecko,
    url_matches_coinbase,
    url_matches_yahoo,
    url_matches_vestige_main,
    url_matches_vestige_free,
)


# ============================================================================
# Rate Limiter Bypass for Tests
# ============================================================================

@pytest.fixture(autouse=True)
def bypass_rate_limits():
    """
    Prevent rate limiter from blocking tests by raising the per-IP limits
    to a value that no test suite will exhaust.

    The SlidingWindowRateLimitMiddleware reads EXPENSIVE_LIMIT and
    STANDARD_LIMIT from module-level constants at call time, so patching
    them here is sufficient for the duration of each test.
    """
    with patch("api.middleware.rate_limit.EXPENSIVE_LIMIT", 1000), \
         patch("api.middleware.rate_limit.STANDARD_LIMIT", 1000):
        yield


# ============================================================================
# Cache Management Fixtures
# ============================================================================

@pytest.fixture
def clear_price_cache():
    """
    Clear all pricing caches before and after each test.

    This ensures tests don't interfere with each other through
    cached price data.
    """
    from core.pricing import _meld_price_cache

    # Store original cache state
    original_cache = _meld_price_cache.copy()

    # Clear all caches
    for key in _meld_price_cache:
        _meld_price_cache[key] = {'price': None, 'expires': None}

    yield

    # Restore original cache (optional: keeps test isolation)
    for key in original_cache:
        _meld_price_cache[key] = original_cache[key]


@pytest.fixture(autouse=True)
def reset_price_cache_before_each_test():
    """
    Automatically reset price caches before each test.

    This fixture runs automatically for all tests to ensure
    consistent starting conditions.
    """
    try:
        from core.pricing import _meld_price_cache
        for key in _meld_price_cache:
            _meld_price_cache[key] = {'price': None, 'expires': None}
    except ImportError:
        pass  # Module not available, skip
    yield


# ============================================================================
# Mock Response Factories
# ============================================================================

@pytest.fixture
def mock_response_factory():
    """
    Factory for creating mock HTTP responses.

    Usage:
        response = mock_response_factory(json_data={'price': 100})
    """
    def _create_response(
        json_data=None,
        status_code=200,
        raise_for_status_error=None
    ):
        response = MagicMock()
        response.json.return_value = json_data
        response.status_code = status_code
        if raise_for_status_error:
            response.raise_for_status.side_effect = raise_for_status_error
        else:
            response.raise_for_status = MagicMock()
        return response

    return _create_response


# ============================================================================
# CoinGecko API Mocking
# ============================================================================

@pytest.fixture
def mock_coingecko_success():
    """
    Mock CoinGecko API to return successful responses for common cryptos.

    Returns prices for ALGO, BTC, and ETH based on the coin_id in the URL.
    """
    def _side_effect(url, **kwargs):
        response = MagicMock()
        response.raise_for_status = MagicMock()

        if 'algorand' in url:
            response.json.return_value = COINGECKO_ALGO_SUCCESS
        elif 'bitcoin' in url:
            response.json.return_value = COINGECKO_BTC_SUCCESS
        elif 'ethereum' in url:
            response.json.return_value = COINGECKO_ETH_SUCCESS
        else:
            response.json.return_value = {}

        return response

    with patch('core.pricing.requests.get', side_effect=_side_effect):
        yield


@pytest.fixture
def mock_coingecko_failure():
    """Mock CoinGecko API to simulate network failures."""
    with patch('core.pricing.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        yield mock_get


@pytest.fixture
def mock_coingecko_timeout():
    """Mock CoinGecko API to simulate timeout."""
    with patch('core.pricing.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
        yield mock_get


# ============================================================================
# Coinbase API Mocking
# ============================================================================

@pytest.fixture
def mock_coinbase_success():
    """Mock Coinbase API to return successful BTC price."""
    response = MagicMock()
    response.json.return_value = COINBASE_BTC_SUCCESS
    response.raise_for_status = MagicMock()

    with patch('core.pricing.requests.get', return_value=response):
        yield


@pytest.fixture
def mock_coinbase_failure():
    """Mock Coinbase API to simulate timeout failure."""
    with patch('core.pricing.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        yield mock_get


# ============================================================================
# Yahoo Finance API Mocking
# ============================================================================

@pytest.fixture
def mock_yahoo_finance_success():
    """Mock Yahoo Finance API for gold and silver futures."""
    def _side_effect(url, **kwargs):
        response = MagicMock()
        response.raise_for_status = MagicMock()

        if 'GC=F' in url:  # Gold futures
            response.json.return_value = YAHOO_GOLD_SUCCESS
        elif 'SI=F' in url:  # Silver futures
            response.json.return_value = YAHOO_SILVER_SUCCESS
        else:
            response.json.return_value = {}

        return response

    with patch('core.pricing.requests.get', side_effect=_side_effect):
        yield


@pytest.fixture
def mock_yahoo_finance_failure():
    """Mock Yahoo Finance API to simulate failures."""
    with patch('core.pricing.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        yield mock_get


# ============================================================================
# Vestige API Mocking
# ============================================================================

@pytest.fixture
def mock_vestige_success():
    """
    Mock Vestige API to return prices for common ASAs.

    Maps asset IDs to appropriate price responses.
    """
    from core.pricing import GOBTC_ASA, WBTC_ASA, MELD_GOLD_ASA, MELD_SILVER_ASA

    def _side_effect(url, **kwargs):
        response = MagicMock()
        response.raise_for_status = MagicMock()

        # Parse asset ID from URL
        if 'asset_ids=' in url:
            if str(GOBTC_ASA) in url:
                response.json.return_value = VESTIGE_GOBTC_SUCCESS
            elif str(WBTC_ASA) in url:
                response.json.return_value = VESTIGE_WBTC_SUCCESS
            elif str(MELD_GOLD_ASA) in url:
                response.json.return_value = VESTIGE_GOLD_SUCCESS
            elif str(MELD_SILVER_ASA) in url:
                response.json.return_value = VESTIGE_SILVER_SUCCESS
            else:
                # Default price for unknown ASAs
                response.json.return_value = make_vestige_price_response(1.0)
        else:
            response.json.return_value = []

        return response

    with patch('core.pricing.requests.get', side_effect=_side_effect):
        yield


@pytest.fixture
def mock_vestige_failure():
    """Mock Vestige API to simulate timeout."""
    with patch('core.pricing.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        yield mock_get


# ============================================================================
# Combined API Mocking (Multi-source)
# ============================================================================

@pytest.fixture
def mock_all_price_apis_success():
    """
    Mock all external price APIs to return successful responses.

    This fixture routes requests to appropriate mock responses based on URL:
    - CoinGecko for crypto prices
    - Coinbase for BTC spot
    - Yahoo Finance for commodities
    - Vestige for ASA prices
    """
    from core.pricing import GOBTC_ASA, WBTC_ASA, MELD_GOLD_ASA, MELD_SILVER_ASA

    def _side_effect(url, **kwargs):
        response = MagicMock()
        response.raise_for_status = MagicMock()

        # Route to appropriate mock based on URL
        if url_matches_coingecko(url):
            if 'algorand' in url:
                response.json.return_value = COINGECKO_ALGO_SUCCESS
            elif 'bitcoin' in url:
                response.json.return_value = COINGECKO_BTC_SUCCESS
            elif 'ethereum' in url:
                response.json.return_value = COINGECKO_ETH_SUCCESS
            else:
                response.json.return_value = {}

        elif url_matches_coinbase(url):
            response.json.return_value = COINBASE_BTC_SUCCESS

        elif url_matches_yahoo(url):
            if 'GC=F' in url:
                response.json.return_value = YAHOO_GOLD_SUCCESS
            elif 'SI=F' in url:
                response.json.return_value = YAHOO_SILVER_SUCCESS
            else:
                response.json.return_value = {}

        elif url_matches_vestige_main(url):
            if str(GOBTC_ASA) in url:
                response.json.return_value = VESTIGE_GOBTC_SUCCESS
            elif str(WBTC_ASA) in url:
                response.json.return_value = VESTIGE_WBTC_SUCCESS
            elif str(MELD_GOLD_ASA) in url:
                response.json.return_value = VESTIGE_GOLD_SUCCESS
            elif str(MELD_SILVER_ASA) in url:
                response.json.return_value = VESTIGE_SILVER_SUCCESS
            else:
                response.json.return_value = make_vestige_price_response(1.0)

        elif url_matches_vestige_free(url):
            # Free API returns prices in ALGO, not USD
            response.json.return_value = {"price": 100.0}

        else:
            response.json.return_value = {}

        return response

    with patch('core.pricing.requests.get', side_effect=_side_effect):
        yield


@pytest.fixture
def mock_all_price_apis_failure():
    """Mock all external price APIs to simulate failures."""
    with patch('core.pricing.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Network unavailable")
        yield mock_get


# ============================================================================
# Analyzer Fixtures
# ============================================================================

@pytest.fixture
def mock_algod_client():
    """Mock Algorand node client for analyzer tests."""
    with patch('core.analyzer.requests.get') as mock_get:
        mock_get.return_value = MagicMock()
        yield mock_get


@pytest.fixture
def analyzer_instance(mock_algod_client):
    """Create an analyzer instance with mocked node connection."""
    from core.analyzer import AlgorandSovereigntyAnalyzer
    return AlgorandSovereigntyAnalyzer(use_local_node=False)


# ============================================================================
# Time Mocking
# ============================================================================

@pytest.fixture
def mock_time_sleep():
    """Mock time.sleep to avoid delays in retry logic."""
    with patch('time.sleep', return_value=None):
        yield


@pytest.fixture
def mock_pricing_time_sleep():
    """Mock time.sleep specifically in the pricing module."""
    with patch('core.pricing.time.sleep', return_value=None):
        yield


# ============================================================================
# Network Isolation Guard
# ============================================================================

@pytest.fixture(autouse=False)
def block_all_network_requests():
    """
    Block all HTTP requests to ensure test isolation.

    Use this fixture when you want to guarantee no network calls
    are made during a test. Any unmocked request will raise an error.
    """
    def _block_request(*args, **kwargs):
        raise RuntimeError(
            f"Attempted to make unmocked network request: {args[0] if args else 'unknown URL'}"
        )

    with patch('requests.get', side_effect=_block_request), \
         patch('requests.post', side_effect=_block_request), \
         patch('requests.put', side_effect=_block_request), \
         patch('requests.delete', side_effect=_block_request):
        yield


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_wallet_address():
    """Provide a sample Algorand wallet address for testing."""
    return "I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4"


@pytest.fixture
def sample_asset_ids():
    """Provide sample ASA IDs for common assets."""
    return {
        "USDC": 31566704,
        "goBTC": 386192725,
        "WBTC": 1058926737,
        "GOLD$": 246516580,
        "SILVER$": 246519683,
        "xALGO": 1134696561,
    }
