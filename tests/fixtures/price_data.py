"""
Test fixtures for pricing API responses.

This module provides mock API response data and helper functions for testing
the pricing module without making actual network calls. All tests using these
fixtures will be deterministic and won't depend on external services.

Mock data sources covered:
- CoinGecko API (ALGO, BTC, ETH prices)
- Coinbase API (BTC spot price)
- Yahoo Finance API (gold/silver futures)
- Vestige API (Algorand ASA prices)
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional


# ============================================================================
# CoinGecko API Mock Responses
# ============================================================================

COINGECKO_ALGO_SUCCESS = {
    "algorand": {"usd": 0.42}
}

COINGECKO_BTC_SUCCESS = {
    "bitcoin": {"usd": 97500.00}
}

COINGECKO_ETH_SUCCESS = {
    "ethereum": {"usd": 3250.00}
}

COINGECKO_ALPHA_SUCCESS = {
    "alpha-finance": {"usd": 0.085}
}

COINGECKO_MULTI_SUCCESS = {
    "algorand": {"usd": 0.42},
    "bitcoin": {"usd": 97500.00},
    "ethereum": {"usd": 3250.00}
}

COINGECKO_EMPTY_RESPONSE = {}

COINGECKO_MALFORMED_RESPONSE = {
    "algorand": {}  # Missing 'usd' key
}


# ============================================================================
# Coinbase API Mock Responses
# ============================================================================

COINBASE_BTC_SUCCESS = {
    "data": {
        "base": "BTC",
        "currency": "USD",
        "amount": "98500.00"
    }
}

COINBASE_BTC_DIFFERENT_PRICE = {
    "data": {
        "base": "BTC",
        "currency": "USD",
        "amount": "99000.00"
    }
}

COINBASE_EMPTY_RESPONSE = {
    "data": {}
}

COINBASE_MALFORMED_RESPONSE = {
    "error": "Service unavailable"
}


# ============================================================================
# Yahoo Finance API Mock Responses
# ============================================================================

def make_yahoo_chart_response(price: float, symbol: str = "GC=F") -> Dict[str, Any]:
    """Create a Yahoo Finance chart API response."""
    return {
        "chart": {
            "result": [{
                "meta": {
                    "currency": "USD",
                    "symbol": symbol,
                    "regularMarketPrice": price,
                    "previousClose": price - 10,
                },
                "timestamp": [1704067200],
                "indicators": {
                    "quote": [{
                        "close": [price]
                    }]
                }
            }],
            "error": None
        }
    }


YAHOO_GOLD_SUCCESS = make_yahoo_chart_response(2650.00, "GC=F")
YAHOO_SILVER_SUCCESS = make_yahoo_chart_response(31.50, "SI=F")

YAHOO_GOLD_HIGH = make_yahoo_chart_response(3000.00, "GC=F")
YAHOO_SILVER_HIGH = make_yahoo_chart_response(35.00, "SI=F")

YAHOO_EMPTY_RESPONSE = {
    "chart": {
        "result": [],
        "error": None
    }
}

YAHOO_ERROR_RESPONSE = {
    "chart": {
        "result": None,
        "error": {
            "code": "Not Found",
            "description": "No data found"
        }
    }
}

YAHOO_MALFORMED_RESPONSE = {
    "chart": {
        "result": [{
            "meta": {}  # Missing regularMarketPrice
        }]
    }
}


# ============================================================================
# Vestige API Mock Responses
# ============================================================================

def make_vestige_price_response(price: float) -> list:
    """Create a Vestige API price response."""
    return [{"price": price}]


# Common ASA prices
VESTIGE_USDC_SUCCESS = make_vestige_price_response(1.0)  # ASA 31566704
VESTIGE_ALGO_SUCCESS = make_vestige_price_response(0.42)
VESTIGE_GOBTC_SUCCESS = make_vestige_price_response(97000.00)  # ASA 386192725
VESTIGE_WBTC_SUCCESS = make_vestige_price_response(97200.00)  # ASA 1058926737
VESTIGE_GOLD_SUCCESS = make_vestige_price_response(85.25)  # ASA 246516580 (per gram)
VESTIGE_SILVER_SUCCESS = make_vestige_price_response(1.02)  # ASA 246519683 (per gram)
VESTIGE_XALGO_SUCCESS = make_vestige_price_response(0.44)

VESTIGE_EMPTY_RESPONSE = []

VESTIGE_ZERO_PRICE = [{"price": 0}]

VESTIGE_NEGATIVE_PRICE = [{"price": -1.0}]

VESTIGE_MALFORMED_RESPONSE = [{"value": 100}]  # Wrong key name

VESTIGE_NULL_PRICE = [{"price": None}]


# ============================================================================
# Vestige Free API Mock Responses (fallback endpoint)
# ============================================================================

def make_vestige_free_response(price_in_algo: float) -> Dict[str, Any]:
    """Create a Vestige free API response (prices in ALGO, not USD)."""
    return {
        "price": price_in_algo,
        "volume_24h": 50000.0,
        "change_24h": 2.5
    }


VESTIGE_FREE_GOLD_SUCCESS = make_vestige_free_response(243.57)  # ~$85/g at $0.35 ALGO
VESTIGE_FREE_SILVER_SUCCESS = make_vestige_free_response(2.91)  # ~$1/g at $0.35 ALGO

VESTIGE_FREE_EMPTY = {}
VESTIGE_FREE_ZERO_PRICE = {"price": 0}


# ============================================================================
# Price Constants for Testing
# ============================================================================

# Standard test prices (use these for consistent test assertions)
MOCK_PRICES = {
    # Crypto
    "ALGO": 0.42,
    "BTC": 97500.00,
    "ETH": 3250.00,
    "GOBTC": 97000.00,
    "WBTC": 97200.00,
    "XALGO": 0.44,
    "FALGO": 0.42,

    # Stablecoins (always $1)
    "USDC": 1.00,
    "USDT": 1.00,
    "DAI": 1.00,
    "STBL": 1.00,
    "FUSDC": 1.00,
    "FUSDT": 1.00,
    "FUSD": 1.00,

    # Precious metals (per gram)
    "GOLD$": 85.25,
    "SILVER$": 1.02,
    "XAUT": 85.25,
    "PAXG": 85.25,

    # Precious metals (per troy oz)
    "GOLD_OZ": 2650.00,
    "SILVER_OZ": 31.50,
}


# ASA IDs for reference
ASA_IDS = {
    "USDC": 31566704,
    "GOBTC": 386192725,
    "WBTC": 1058926737,
    "GOLD$": 246516580,
    "SILVER$": 246519683,
    "XALGO": 1134696561,  # Folks xALGO
}


# ============================================================================
# Cache State Helpers
# ============================================================================

def make_expired_cache_entry(price: float) -> Dict[str, Any]:
    """Create an expired cache entry."""
    return {
        "price": price,
        "expires": datetime.now() - timedelta(seconds=1)
    }


def make_valid_cache_entry(price: float, ttl_seconds: int = 300) -> Dict[str, Any]:
    """Create a valid (non-expired) cache entry."""
    return {
        "price": price,
        "expires": datetime.now() + timedelta(seconds=ttl_seconds)
    }


def make_empty_cache_entry() -> Dict[str, Any]:
    """Create an empty cache entry."""
    return {
        "price": None,
        "expires": None
    }


# ============================================================================
# Mock Request Helpers
# ============================================================================

class MockResponse:
    """A mock requests.Response object for testing."""

    def __init__(
        self,
        json_data: Any = None,
        status_code: int = 200,
        raise_for_status_error: Optional[Exception] = None
    ):
        self._json_data = json_data
        self.status_code = status_code
        self._raise_error = raise_for_status_error

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self._raise_error:
            raise self._raise_error


def mock_successful_response(json_data: Any) -> MockResponse:
    """Create a successful mock response."""
    return MockResponse(json_data=json_data, status_code=200)


def mock_timeout_response():
    """Create a response that simulates a timeout."""
    import requests
    return MockResponse(
        status_code=408,
        raise_for_status_error=requests.exceptions.Timeout("Connection timed out")
    )


def mock_server_error_response():
    """Create a response that simulates a server error."""
    import requests
    return MockResponse(
        status_code=500,
        raise_for_status_error=requests.exceptions.HTTPError("500 Server Error")
    )


def mock_rate_limit_response():
    """Create a response that simulates rate limiting."""
    import requests
    return MockResponse(
        json_data={"error": "Rate limit exceeded"},
        status_code=429,
        raise_for_status_error=requests.exceptions.HTTPError("429 Too Many Requests")
    )


# ============================================================================
# URL Pattern Matchers
# ============================================================================

COINGECKO_URL_PATTERN = "api.coingecko.com"
COINBASE_URL_PATTERN = "api.coinbase.com"
YAHOO_URL_PATTERN = "query1.finance.yahoo.com"
VESTIGE_API_URL_PATTERN = "api.vestigelabs.org"
VESTIGE_FREE_URL_PATTERN = "free-api.vestige.fi"


def url_matches_coingecko(url: str) -> bool:
    """Check if URL is for CoinGecko API."""
    return COINGECKO_URL_PATTERN in url


def url_matches_coinbase(url: str) -> bool:
    """Check if URL is for Coinbase API."""
    return COINBASE_URL_PATTERN in url


def url_matches_yahoo(url: str) -> bool:
    """Check if URL is for Yahoo Finance API."""
    return YAHOO_URL_PATTERN in url


def url_matches_vestige(url: str) -> bool:
    """Check if URL is for Vestige API (main or free)."""
    return VESTIGE_API_URL_PATTERN in url or VESTIGE_FREE_URL_PATTERN in url


def url_matches_vestige_main(url: str) -> bool:
    """Check if URL is for main Vestige API."""
    return VESTIGE_API_URL_PATTERN in url


def url_matches_vestige_free(url: str) -> bool:
    """Check if URL is for free Vestige API."""
    return VESTIGE_FREE_URL_PATTERN in url
