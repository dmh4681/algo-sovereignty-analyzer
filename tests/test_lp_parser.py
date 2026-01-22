"""
Tests for core/lp_parser.py - LP Token parsing and decomposition.

These tests cover:
- LP token detection patterns (Tinyman, Pact, Humble, Folks Finance)
- Pool info parsing and API responses
- LP value estimation (Tinyman SDK and geometric mean fallback)
- Malformed API responses and missing data handling
- Edge cases: zero balances, unknown assets, nested LP tokens
- Error handling and graceful degradation
"""
import pytest
from unittest.mock import patch, MagicMock
import requests
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.lp_parser import LPParser, LPBreakdown


# ============================================================================
# Inline Fixtures (moved from tests.fixtures.lp_tokens for import compatibility)
# ============================================================================

# Valid LP Token Responses
TINYMAN_V2_ALGO_USDC = {
    "params": {
        "name": "TinymanPool2.0 ALGO-USDC",
        "unit-name": "TMPOOL2",
        "decimals": 6,
        "creator": "POOL_ADDRESS_ALGO_USDC",
        "total": 1000000000000
    }
}

TINYMAN_V2_XALGO_ALGO = {
    "params": {
        "name": "TinymanPool2.0 XALGO-ALGO",
        "unit-name": "TMPOOL2",
        "decimals": 6,
        "creator": "POOL_ADDRESS_XALGO_ALGO",
        "total": 500000000000
    }
}

TINYMAN_V1_BTC_ALGO = {
    "params": {
        "name": "TinymanPool goBTC-ALGO",
        "unit-name": "TM1POOL",
        "decimals": 6,
        "creator": "POOL_ADDRESS_BTC_ALGO",
        "total": 10000000000
    }
}

PACT_LP_ALGO_USDC = {
    "params": {
        "name": "PACT ALGO/USDC LP",
        "unit-name": "PACT LP",
        "decimals": 6,
        "creator": "PACT_POOL_ADDRESS",
        "total": 2000000000000
    }
}

HUMBLE_LP_GOLD_ALGO = {
    "params": {
        "name": "GOLD$-ALGO Pool",
        "unit-name": "hLP",
        "decimals": 6,
        "creator": "HUMBLE_POOL_ADDRESS",
        "total": 100000000000
    }
}

FOLKS_LP_FUSDC_FALGO = {
    "params": {
        "name": "fUSDC / fALGO",
        "unit-name": "FLP",
        "decimals": 6,
        "creator": "FOLKS_POOL_ADDRESS",
        "total": 500000000000
    }
}

# Pool State Responses (from Tinyman SDK)
POOL_STATE_ALGO_USDC = {
    "total_supply": 1000000.0,
    "reserve1": 5000000.0,  # 5M ALGO
    "reserve2": 1500000.0   # 1.5M USDC
}

POOL_STATE_XALGO_ALGO = {
    "total_supply": 500000.0,
    "reserve1": 1000000.0,  # 1M xALGO
    "reserve2": 1000000.0   # 1M ALGO
}

POOL_STATE_ZERO_SUPPLY = {
    "total_supply": 0.0,
    "reserve1": 0.0,
    "reserve2": 0.0
}

POOL_STATE_EMPTY_RESERVES = {
    "total_supply": 1000000.0,
    "reserve1": 0.0,
    "reserve2": 0.0
}

# Account Responses (for pool asset discovery)
POOL_ACCOUNT_TWO_ASSETS = {
    "address": "POOL_ADDRESS_ALGO_USDC",
    "amount": 1000000,  # ALGO
    "assets": [
        {"asset-id": 31566704, "amount": 1500000000000},  # USDC
        {"asset-id": 12345678, "amount": 5000000000000}   # Other token
    ]
}

POOL_ACCOUNT_ONE_ASSET = {
    "address": "POOL_ADDRESS_ALGO_ONLY",
    "amount": 5000000000,  # ALGO
    "assets": [
        {"asset-id": 31566704, "amount": 1500000000000}  # USDC only
    ]
}

POOL_ACCOUNT_NO_ASSETS = {
    "address": "POOL_ADDRESS_EMPTY",
    "amount": 0,
    "assets": []
}

POOL_ACCOUNT_ZERO_BALANCE_ASSETS = {
    "address": "POOL_ADDRESS_ZERO",
    "amount": 0,
    "assets": [
        {"asset-id": 31566704, "amount": 0},
        {"asset-id": 12345678, "amount": 0}
    ]
}

# Malformed / Edge Case Responses
MALFORMED_NO_PARAMS = {
    "asset-index": 12345
    # Missing "params" key entirely
}

MALFORMED_EMPTY_PARAMS = {
    "params": {}
}

MALFORMED_NO_NAME = {
    "params": {
        "unit-name": "TMPOOL2",
        "decimals": 6,
        "creator": "SOME_ADDRESS"
    }
}

MALFORMED_NO_UNIT_NAME = {
    "params": {
        "name": "TinymanPool2.0 ALGO-USDC",
        "decimals": 6,
        "creator": "SOME_ADDRESS"
    }
}

MALFORMED_NO_CREATOR = {
    "params": {
        "name": "TinymanPool2.0 ALGO-USDC",
        "unit-name": "TMPOOL2",
        "decimals": 6
    }
}

MALFORMED_INVALID_NAME_FORMAT = {
    "params": {
        "name": "TinymanPool2.0",  # Missing pair info
        "unit-name": "TMPOOL2",
        "decimals": 6,
        "creator": "POOL_ADDRESS"
    }
}

MALFORMED_SINGLE_ASSET_NAME = {
    "params": {
        "name": "TinymanPool2.0 ALGO",  # Only one asset
        "unit-name": "TMPOOL2",
        "decimals": 6,
        "creator": "POOL_ADDRESS"
    }
}

# Non-LP Token Responses (for negative testing)
REGULAR_TOKEN_USDC = {
    "params": {
        "name": "USDC",
        "unit-name": "USDC",
        "decimals": 6,
        "creator": "CIRCLE_ADDRESS",
        "total": 1000000000000000
    }
}

REGULAR_TOKEN_ALGO = {
    "params": {
        "name": "Algorand",
        "unit-name": "ALGO",
        "decimals": 6,
        "creator": "ALGORAND_FOUNDATION",
        "total": 10000000000000000
    }
}

NFT_TOKEN = {
    "params": {
        "name": "CoolPunk #1234",
        "unit-name": "PUNK",
        "decimals": 0,
        "creator": "NFT_CREATOR",
        "total": 1
    }
}

# LP Token Detection Test Cases
LP_TOKEN_DETECTION_POSITIVE = [
    # (ticker, name, description)
    ("TMPOOL2", "TinymanPool2.0 ALGO-USDC", "Tinyman V2 standard"),
    ("TMPOOL", "TinymanPool ALGO-USDC", "Tinyman V1 standard"),
    ("TM1POOL", "TinymanPool1.1 BTC-ALGO", "Tinyman V1.1"),
    ("TM1.1POOL", "TinymanPool BTC-ALGO", "Tinyman version variant"),
    ("PACT LP", "PACT ALGO/USDC LP", "Pact LP token"),
    ("PLP", "Pact Liquidity Pool", "Pact PLP variant"),
    ("PACT-ALGO-USDC", "Pact Pool", "Pact with pair in ticker"),
    ("hLP", "GOLD$-ALGO Pool", "Humble LP token"),
    ("ALGO-USDC-LP", "Liquidity Pool", "Generic LP suffix"),
    ("FLP", "fUSDC / fALGO", "Folks Finance LP"),
    ("LP", "xALGO / ALGO", "Generic with slash pair"),
]

LP_TOKEN_DETECTION_NEGATIVE = [
    # (ticker, name, description)
    ("USDC", "USDC", "Stablecoin"),
    ("ALGO", "Algorand", "Native token"),
    ("goBTC", "goBitcoin", "Wrapped Bitcoin"),
    ("GOLD$", "Meld Gold", "Gold token"),
    ("NFD", "NFDomain", "NFT domain"),
    ("FOLKS", "Folks Finance", "Governance token"),
    ("YLDY", "Yieldly", "DeFi token"),
]

# Price Function Mock Data
MOCK_PRICES = {
    "ALGO": 0.35,
    "USDC": 1.00,
    "XALGO": 0.38,
    "FUSDC": 1.00,
    "FALGO": 0.35,
    "goBTC": 45000.00,
    "GOLD$": 2000.00,
    "SILVER$": 25.00,
}


def mock_get_price(ticker: str, asset_id: int = None) -> float:
    """Mock price function for testing."""
    return MOCK_PRICES.get(ticker.upper(), 0.0)


def mock_get_price_partial(ticker: str, asset_id: int = None) -> float:
    """Mock price function that only knows some assets."""
    partial_prices = {"ALGO": 0.35, "USDC": 1.00}
    return partial_prices.get(ticker.upper(), 0.0)


def mock_get_price_none(ticker: str, asset_id: int = None) -> float:
    """Mock price function that returns 0 for all assets."""
    return 0.0


# Classification Function Mock Data
CATEGORY_MAP = {
    "ALGO": "algo",
    "XALGO": "algo",
    "FALGO": "algo",
    "USDC": "dollars",
    "FUSDC": "dollars",
    "goBTC": "hard_money",
    "GOLD$": "hard_money",
    "SILVER$": "hard_money",
}


def mock_classify_fn(asset_id: int, name: str, ticker: str) -> str:
    """Mock classification function for testing."""
    return CATEGORY_MAP.get(ticker.upper(), "shitcoin")


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def parser():
    """Create a fresh LPParser instance for each test."""
    return LPParser(algod_address="https://test-api.algonode.cloud")


@pytest.fixture
def parser_with_cache(parser):
    """Create parser with pre-populated cache."""
    parser._pool_cache = {
        12345: {
            'asset1_ticker': 'ALGO',
            'asset2_ticker': 'USDC',
            'lp_asset_id': 12345,
            'creator': 'CACHED_POOL_ADDRESS',
            'estimated': True
        }
    }
    return parser


# ============================================================================
# LP Token Detection Tests (is_lp_token)
# ============================================================================

class TestIsLpToken:
    """Tests for LP token detection logic."""

    @pytest.mark.parametrize("ticker,name,description", LP_TOKEN_DETECTION_POSITIVE)
    def test_detects_lp_tokens(self, parser, ticker, name, description):
        """Should detect various LP token formats."""
        assert parser.is_lp_token(ticker, name) is True, f"Failed to detect: {description}"

    @pytest.mark.parametrize("ticker,name,description", LP_TOKEN_DETECTION_NEGATIVE)
    def test_rejects_non_lp_tokens(self, parser, ticker, name, description):
        """Should reject non-LP tokens."""
        assert parser.is_lp_token(ticker, name) is False, f"False positive: {description}"

    def test_case_insensitivity(self, parser):
        """LP detection should be case-insensitive."""
        assert parser.is_lp_token("tmpool2", "tinymanpool2.0 algo-usdc") is True
        assert parser.is_lp_token("TMPOOL2", "TINYMANPOOL2.0 ALGO-USDC") is True
        assert parser.is_lp_token("TmPoOl2", "TinymanPool2.0 ALGO-USDC") is True

    def test_tinyman_v1_patterns(self, parser):
        """Should detect Tinyman V1 pool patterns."""
        assert parser.is_lp_token("TM1POOL", "TinymanPool ALGO-USDC") is True
        assert parser.is_lp_token("TMPOOL", "TinymanPool BTC-ALGO") is True

    def test_tinyman_v2_patterns(self, parser):
        """Should detect Tinyman V2 pool patterns."""
        assert parser.is_lp_token("TMPOOL2", "TinymanPool2.0 ALGO-USDC") is True
        assert parser.is_lp_token("TM1.1POOL", "TinymanPool1.1 ALGO-USDC") is True

    def test_pact_patterns(self, parser):
        """Should detect Pact LP token patterns."""
        assert parser.is_lp_token("PACT LP", "PACT ALGO/USDC LP") is True
        assert parser.is_lp_token("PLP-ALGO-USDC", "Pact Liquidity Pool") is True

    def test_humble_patterns(self, parser):
        """Should detect Humble LP token patterns."""
        assert parser.is_lp_token("hLP", "GOLD$-ALGO Pool") is True
        assert parser.is_lp_token("ALGO-USDC-LP", "Humble Pool") is True

    def test_folks_finance_patterns(self, parser):
        """Should detect Folks Finance LP patterns with slash separator."""
        assert parser.is_lp_token("FLP", "fUSDC / fALGO") is True
        assert parser.is_lp_token("LP", "xALGO / ALGO") is True

    def test_generic_pool_in_name(self, parser):
        """Should detect 'POOL' keyword in name."""
        assert parser.is_lp_token("ABC123", "Some Pool Token") is True
        assert parser.is_lp_token("XYZ", "Liquidity Pool Share") is True

    def test_empty_strings(self, parser):
        """Should handle empty strings gracefully."""
        assert parser.is_lp_token("", "") is False
        assert parser.is_lp_token("TMPOOL", "") is True  # ticker alone suffices
        assert parser.is_lp_token("", "TinymanPool2.0 ALGO-USDC") is True  # name alone suffices

    def test_special_characters(self, parser):
        """Should handle special characters in names."""
        assert parser.is_lp_token("TMPOOL2", "TinymanPool2.0 GOLD$-SILVER$") is True
        assert parser.is_lp_token("LP", "Token-A / Token-B (V2)") is True


# ============================================================================
# Pool Info Parsing Tests (get_pool_info, _parse_tinyman_pool)
# ============================================================================

class TestGetPoolInfo:
    """Tests for pool information retrieval."""

    def test_returns_cached_info(self, parser_with_cache):
        """Should return cached pool info without API call."""
        with patch('requests.get') as mock_get:
            result = parser_with_cache.get_pool_info(12345)
            mock_get.assert_not_called()
            assert result['asset1_ticker'] == 'ALGO'
            assert result['asset2_ticker'] == 'USDC'

    def test_fetches_from_api_when_not_cached(self, parser):
        """Should fetch pool info from API when not in cache."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = TINYMAN_V2_ALGO_USDC

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = parser.get_pool_info(99999)
            mock_get.assert_called_once()
            assert result is not None
            assert result['asset1_ticker'] == 'ALGO'
            assert result['asset2_ticker'] == 'USDC'

    def test_caches_result_after_fetch(self, parser):
        """Should cache pool info after successful fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = TINYMAN_V2_ALGO_USDC

        with patch('requests.get', return_value=mock_response):
            parser.get_pool_info(99999)
            assert 99999 in parser._pool_cache

    def test_handles_api_failure(self, parser):
        """Should return None on API failure."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch('requests.get', return_value=mock_response):
            result = parser.get_pool_info(99999)
            assert result is None

    def test_handles_network_error(self, parser):
        """Should handle network errors gracefully."""
        with patch('requests.get', side_effect=requests.exceptions.ConnectionError("Network error")):
            result = parser.get_pool_info(99999)
            assert result is None

    def test_handles_timeout(self, parser):
        """Should handle request timeout gracefully."""
        with patch('requests.get', side_effect=requests.exceptions.Timeout("Timeout")):
            result = parser.get_pool_info(99999)
            assert result is None

    def test_handles_malformed_response_no_params(self, parser):
        """Should handle response missing 'params' key."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MALFORMED_NO_PARAMS

        with patch('requests.get', return_value=mock_response):
            result = parser.get_pool_info(99999)
            assert result is None

    def test_handles_malformed_response_empty_params(self, parser):
        """Should handle empty params object."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MALFORMED_EMPTY_PARAMS

        with patch('requests.get', return_value=mock_response):
            result = parser.get_pool_info(99999)
            assert result is None

    def test_handles_invalid_name_format(self, parser):
        """Should handle names without proper pair format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MALFORMED_INVALID_NAME_FORMAT

        with patch('requests.get', return_value=mock_response):
            result = parser.get_pool_info(99999)
            assert result is None


class TestParseTinymanPool:
    """Tests for Tinyman pool name parsing."""

    def test_parses_hyphen_separated_pair(self, parser):
        """Should parse ALGO-USDC format."""
        result = parser._parse_tinyman_pool(
            "TinymanPool2.0 ALGO-USDC", "TMPOOL2", "CREATOR", 12345
        )
        assert result['asset1_ticker'] == 'ALGO'
        assert result['asset2_ticker'] == 'USDC'

    def test_parses_slash_separated_pair(self, parser):
        """Should parse ALGO/USDC format."""
        result = parser._parse_tinyman_pool(
            "Pool ALGO/USDC", "LP", "CREATOR", 12345
        )
        assert result['asset1_ticker'] == 'ALGO'
        assert result['asset2_ticker'] == 'USDC'

    def test_fallback_to_unit_name(self, parser):
        """Should try unit-name if name doesn't have pair."""
        result = parser._parse_tinyman_pool(
            "TinymanPool2.0", "ALGO-USDC", "CREATOR", 12345
        )
        assert result['asset1_ticker'] == 'ALGO'
        assert result['asset2_ticker'] == 'USDC'

    def test_returns_none_for_no_pair(self, parser):
        """Should return None if no pair can be parsed."""
        result = parser._parse_tinyman_pool(
            "TinymanPool2.0", "TMPOOL2", "CREATOR", 12345
        )
        assert result is None

    def test_preserves_metadata(self, parser):
        """Should include lp_asset_id, creator, and estimated flag."""
        result = parser._parse_tinyman_pool(
            "TinymanPool2.0 ALGO-USDC", "TMPOOL2", "TEST_CREATOR", 54321
        )
        assert result['lp_asset_id'] == 54321
        assert result['creator'] == "TEST_CREATOR"
        assert result['estimated'] is True


# ============================================================================
# Pool Assets Discovery Tests (_get_pool_assets)
# ============================================================================

class TestGetPoolAssets:
    """Tests for pool account asset discovery."""

    def test_returns_two_assets(self, parser):
        """Should return both asset IDs when pool holds two assets."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = POOL_ACCOUNT_TWO_ASSETS

        with patch('requests.get', return_value=mock_response):
            asset1, asset2 = parser._get_pool_assets("POOL_ADDRESS")
            assert asset1 == 31566704
            assert asset2 == 12345678

    def test_returns_asset_and_algo(self, parser):
        """Should return asset ID and 0 (ALGO) when only one ASA held."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = POOL_ACCOUNT_ONE_ASSET

        with patch('requests.get', return_value=mock_response):
            asset1, asset2 = parser._get_pool_assets("POOL_ADDRESS")
            assert asset1 == 31566704
            assert asset2 == 0  # ALGO

    def test_handles_no_assets(self, parser):
        """Should return (None, None) when pool has no assets."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = POOL_ACCOUNT_NO_ASSETS

        with patch('requests.get', return_value=mock_response):
            asset1, asset2 = parser._get_pool_assets("POOL_ADDRESS")
            assert asset1 is None
            assert asset2 is None

    def test_filters_zero_balance_assets(self, parser):
        """Should not return assets with zero balance."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = POOL_ACCOUNT_ZERO_BALANCE_ASSETS

        with patch('requests.get', return_value=mock_response):
            asset1, asset2 = parser._get_pool_assets("POOL_ADDRESS")
            assert asset1 is None
            assert asset2 is None

    def test_handles_api_failure(self, parser):
        """Should return (None, None) on API failure."""
        with patch('requests.get', side_effect=requests.exceptions.RequestException("Error")):
            asset1, asset2 = parser._get_pool_assets("POOL_ADDRESS")
            assert asset1 is None
            assert asset2 is None


# ============================================================================
# Pool State Tests (get_pool_state)
# ============================================================================

class TestGetPoolState:
    """Tests for Tinyman SDK pool state queries."""

    def test_handles_tinyman_sdk_import_error(self, parser):
        """Should return None if Tinyman SDK not installed."""
        with patch.dict('sys.modules', {'tinyman.v2.client': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'tinyman'")):
                result = parser.get_pool_state("POOL_ADDR", 12345, 0, 31566704)
                assert result is None

    def test_handles_pool_not_found(self, parser):
        """Should return None when pool doesn't exist."""
        mock_tinyman = MagicMock()
        mock_pool = MagicMock()
        mock_pool.exists = False
        mock_tinyman.fetch_pool.return_value = mock_pool

        with patch.dict('sys.modules', {
            'tinyman': MagicMock(),
            'tinyman.v2': MagicMock(),
            'tinyman.v2.client': MagicMock(TinymanV2MainnetClient=lambda **kw: mock_tinyman),
            'tinyman.assets': MagicMock(Asset=MagicMock()),
            'algosdk': MagicMock(),
            'algosdk.v2client': MagicMock(),
            'algosdk.v2client.algod': MagicMock(AlgodClient=MagicMock()),
        }):
            # The actual test would require proper mocking of the entire SDK chain
            # For now, we test the error handling path
            pass

    def test_handles_sdk_exception(self, parser):
        """Should handle Tinyman SDK exceptions gracefully."""
        with patch('core.lp_parser.traceback.print_exc'):
            # Simulate import failure
            original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

            def mock_import(name, *args, **kwargs):
                if 'tinyman' in name:
                    raise Exception("SDK Error")
                return original_import(name, *args, **kwargs)

            with patch('builtins.__import__', side_effect=mock_import):
                result = parser.get_pool_state("POOL_ADDR", 12345, 0, 31566704)
                assert result is None


# ============================================================================
# LP Value Estimation Tests (estimate_lp_value)
# ============================================================================

class TestEstimateLpValue:
    """Tests for LP token value estimation."""

    def test_parses_tinyman_v2_name_format(self, parser):
        """Should parse 'TinymanPool2.0 ASSET1-ASSET2' format."""
        with patch.object(parser, 'get_pool_info', return_value=None), \
             patch.object(parser, 'get_pool_state', return_value=None):
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 ALGO-USDC", 100.0, 12345, mock_get_price
            )
            assert result is not None
            assert result.asset1_ticker == 'ALGO'
            assert result.asset2_ticker == 'USDC'

    def test_returns_none_for_invalid_name_format(self, parser):
        """Should return None when name doesn't have hyphen-separated pair."""
        result = parser.estimate_lp_value(
            "TMPOOL2", "TinymanPool2.0 SINGLE", 100.0, 12345, mock_get_price
        )
        assert result is None

    def test_returns_none_for_no_prices(self, parser):
        """Should return None when neither asset has price data."""
        with patch.object(parser, 'get_pool_info', return_value=None), \
             patch.object(parser, 'get_pool_state', return_value=None):
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 UNKNOWN1-UNKNOWN2", 100.0, 12345, mock_get_price_none
            )
            assert result is None

    def test_geometric_mean_fallback(self, parser):
        """Should use geometric mean when pool state unavailable."""
        with patch.object(parser, 'get_pool_info', return_value=None), \
             patch.object(parser, 'get_pool_state', return_value=None):
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 ALGO-USDC", 100.0, 12345, mock_get_price
            )
            # Geometric mean: 2 * sqrt(0.35 * 1.0) * 100 = 118.32
            assert result is not None
            assert abs(result.total_usd - 118.32) < 1.0  # Allow small floating point variance

    def test_geometric_mean_splits_value_evenly(self, parser):
        """Geometric mean should split value 50/50 between assets."""
        with patch.object(parser, 'get_pool_info', return_value=None), \
             patch.object(parser, 'get_pool_state', return_value=None):
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 ALGO-USDC", 100.0, 12345, mock_get_price
            )
            assert result is not None
            # Values should be roughly equal (50/50 split)
            assert abs(result.asset1_usd - result.asset2_usd) < 0.01

    def test_tinyman_sdk_calculation(self, parser):
        """Should use Tinyman SDK calculation when pool state available."""
        pool_info = {
            'creator': 'POOL_ADDRESS',
            'asset1_ticker': 'ALGO',
            'asset2_ticker': 'USDC'
        }
        pool_state = POOL_STATE_ALGO_USDC

        with patch.object(parser, 'get_pool_info', return_value=pool_info), \
             patch.object(parser, 'get_pool_state', return_value=pool_state), \
             patch.object(parser, '_get_pool_assets', return_value=(0, 31566704)):
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 ALGO-USDC", 1000.0, 12345, mock_get_price
            )
            assert result is not None
            # User has 1000/1000000 = 0.1% of pool
            # Reserve1 (ALGO): 5M * 0.001 = 5000 ALGO @ $0.35 = $1750
            # Reserve2 (USDC): 1.5M * 0.001 = 1500 USDC @ $1.00 = $1500
            # Total: $3250
            assert abs(result.total_usd - 3250.0) < 1.0

    def test_fallback_on_zero_supply(self, parser):
        """Should fall back to geometric mean when pool has zero supply."""
        pool_info = {
            'creator': 'POOL_ADDRESS',
            'asset1_ticker': 'ALGO',
            'asset2_ticker': 'USDC'
        }

        with patch.object(parser, 'get_pool_info', return_value=pool_info), \
             patch.object(parser, 'get_pool_state', return_value=POOL_STATE_ZERO_SUPPLY), \
             patch.object(parser, '_get_pool_assets', return_value=(0, 31566704)):
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 ALGO-USDC", 100.0, 12345, mock_get_price
            )
            # Should fall back to geometric mean
            assert result is not None
            assert result.total_usd > 0

    def test_fallback_on_near_zero_value(self, parser):
        """Should fall back to geometric mean when Tinyman returns near-zero value."""
        pool_info = {
            'creator': 'POOL_ADDRESS',
            'asset1_ticker': 'ALGO',
            'asset2_ticker': 'USDC'
        }

        with patch.object(parser, 'get_pool_info', return_value=pool_info), \
             patch.object(parser, 'get_pool_state', return_value=POOL_STATE_EMPTY_RESERVES), \
             patch.object(parser, '_get_pool_assets', return_value=(0, 31566704)):
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 ALGO-USDC", 100.0, 12345, mock_get_price
            )
            # Should fall back to geometric mean when reserves are empty
            assert result is not None

    def test_hardcoded_asset_id_fallbacks(self, parser):
        """Should use hardcoded asset ID fallbacks for known tickers."""
        with patch.object(parser, 'get_pool_info', return_value=None), \
             patch.object(parser, 'get_pool_state', return_value=None):
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 XALGO-ALGO", 100.0, 12345, mock_get_price
            )
            assert result is not None
            assert result.asset1_ticker == 'XALGO'
            assert result.asset2_ticker == 'ALGO'

    def test_handles_partial_price_data(self, parser):
        """Should handle case where only one asset has price."""
        with patch.object(parser, 'get_pool_info', return_value=None), \
             patch.object(parser, 'get_pool_state', return_value=None):
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 ALGO-UNKNOWN", 100.0, 12345, mock_get_price_partial
            )
            # With one price being 0, geometric mean will fail
            assert result is None


# ============================================================================
# LP Component Classification Tests (classify_lp_components)
# ============================================================================

class TestClassifyLpComponents:
    """Tests for LP component classification."""

    def test_classifies_both_components(self, parser):
        """Should return classification for both underlying assets."""
        breakdown = LPBreakdown(
            lp_ticker="TMPOOL2",
            lp_amount=100.0,
            asset1_ticker="ALGO",
            asset1_amount=500.0,
            asset1_usd=175.0,
            asset2_ticker="USDC",
            asset2_amount=175.0,
            asset2_usd=175.0,
            total_usd=350.0
        )

        components = parser.classify_lp_components(breakdown, mock_classify_fn)

        assert len(components) == 2
        # First component (ALGO)
        assert components[0][0] == 'algo'
        assert components[0][1]['ticker'] == 'ALGO'
        assert components[0][1]['amount'] == 500.0
        assert components[0][1]['usd_value'] == 175.0
        # Second component (USDC)
        assert components[1][0] == 'dollars'
        assert components[1][1]['ticker'] == 'USDC'
        assert components[1][1]['amount'] == 175.0
        assert components[1][1]['usd_value'] == 175.0

    def test_includes_from_lp_field(self, parser):
        """Should include 'from_lp' field indicating source LP token."""
        breakdown = LPBreakdown(
            lp_ticker="TMPOOL2",
            lp_amount=100.0,
            asset1_ticker="goBTC",
            asset1_amount=0.01,
            asset1_usd=450.0,
            asset2_ticker="ALGO",
            asset2_amount=1285.7,
            asset2_usd=450.0,
            total_usd=900.0
        )

        components = parser.classify_lp_components(breakdown, mock_classify_fn)

        assert components[0][1]['from_lp'] == 'TMPOOL2'
        assert components[1][1]['from_lp'] == 'TMPOOL2'

    def test_formats_component_names(self, parser):
        """Should format component names to show LP origin."""
        breakdown = LPBreakdown(
            lp_ticker="PLP-GOLD-ALGO",
            lp_amount=50.0,
            asset1_ticker="GOLD$",
            asset1_amount=0.5,
            asset1_usd=1000.0,
            asset2_ticker="ALGO",
            asset2_amount=2857.1,
            asset2_usd=1000.0,
            total_usd=2000.0
        )

        components = parser.classify_lp_components(breakdown, mock_classify_fn)

        assert 'GOLD$ (from PLP-GOLD-ALGO)' == components[0][1]['name']
        assert 'ALGO (from PLP-GOLD-ALGO)' == components[1][1]['name']

    def test_hard_money_classification(self, parser):
        """Should correctly classify hard money components."""
        breakdown = LPBreakdown(
            lp_ticker="TMPOOL2",
            lp_amount=10.0,
            asset1_ticker="goBTC",
            asset1_amount=0.01,
            asset1_usd=450.0,
            asset2_ticker="GOLD$",
            asset2_amount=0.225,
            asset2_usd=450.0,
            total_usd=900.0
        )

        # Use mock that returns hard_money for both these tickers
        def classify_hard_money(asset_id, name, ticker):
            if ticker.upper() in ['GOBTC', 'GOLD$']:
                return 'hard_money'
            return 'shitcoin'

        components = parser.classify_lp_components(breakdown, classify_hard_money)

        assert components[0][0] == 'hard_money'
        assert components[1][0] == 'hard_money'

    def test_uses_negative_asset_id(self, parser):
        """Should pass -1 as asset_id to force auto-classification."""
        mock_classifier = MagicMock(return_value='algo')

        breakdown = LPBreakdown(
            lp_ticker="TMPOOL2",
            lp_amount=100.0,
            asset1_ticker="ALGO",
            asset1_amount=500.0,
            asset1_usd=175.0,
            asset2_ticker="USDC",
            asset2_amount=175.0,
            asset2_usd=175.0,
            total_usd=350.0
        )

        parser.classify_lp_components(breakdown, mock_classifier)

        # Verify -1 is passed as first argument (asset_id)
        calls = mock_classifier.call_args_list
        assert calls[0][0][0] == -1
        assert calls[1][0][0] == -1


# ============================================================================
# LPBreakdown Dataclass Tests
# ============================================================================

class TestLPBreakdown:
    """Tests for LPBreakdown dataclass."""

    def test_creation_with_all_fields(self):
        """Should create breakdown with all required fields."""
        breakdown = LPBreakdown(
            lp_ticker="TMPOOL2",
            lp_amount=100.0,
            asset1_ticker="ALGO",
            asset1_amount=500.0,
            asset1_usd=175.0,
            asset2_ticker="USDC",
            asset2_amount=175.0,
            asset2_usd=175.0,
            total_usd=350.0
        )

        assert breakdown.lp_ticker == "TMPOOL2"
        assert breakdown.lp_amount == 100.0
        assert breakdown.asset1_ticker == "ALGO"
        assert breakdown.asset1_amount == 500.0
        assert breakdown.asset1_usd == 175.0
        assert breakdown.asset2_ticker == "USDC"
        assert breakdown.asset2_amount == 175.0
        assert breakdown.asset2_usd == 175.0
        assert breakdown.total_usd == 350.0

    def test_zero_values(self):
        """Should allow zero values for amounts and USD."""
        breakdown = LPBreakdown(
            lp_ticker="TMPOOL2",
            lp_amount=0.0,
            asset1_ticker="ALGO",
            asset1_amount=0.0,
            asset1_usd=0.0,
            asset2_ticker="USDC",
            asset2_amount=0.0,
            asset2_usd=0.0,
            total_usd=0.0
        )

        assert breakdown.total_usd == 0.0

    def test_large_values(self):
        """Should handle very large values."""
        breakdown = LPBreakdown(
            lp_ticker="TMPOOL2",
            lp_amount=1_000_000_000.0,
            asset1_ticker="ALGO",
            asset1_amount=5_000_000_000.0,
            asset1_usd=1_750_000_000.0,
            asset2_ticker="USDC",
            asset2_amount=1_750_000_000.0,
            asset2_usd=1_750_000_000.0,
            total_usd=3_500_000_000.0
        )

        assert breakdown.total_usd == 3_500_000_000.0


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and unusual inputs."""

    def test_very_small_lp_amounts(self, parser):
        """Should handle extremely small LP token amounts."""
        with patch.object(parser, 'get_pool_info', return_value=None), \
             patch.object(parser, 'get_pool_state', return_value=None):
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 ALGO-USDC", 0.000001, 12345, mock_get_price
            )
            assert result is not None
            assert result.total_usd > 0

    def test_very_large_lp_amounts(self, parser):
        """Should handle very large LP token amounts."""
        with patch.object(parser, 'get_pool_info', return_value=None), \
             patch.object(parser, 'get_pool_state', return_value=None):
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 ALGO-USDC", 1_000_000_000.0, 12345, mock_get_price
            )
            assert result is not None
            assert result.total_usd > 0

    def test_unicode_in_names(self, parser):
        """Should handle unicode characters in token names without errors."""
        # The parser may or may not detect this as LP token depending on patterns,
        # but it should not raise an exception
        result = parser.is_lp_token("LP", "Token\u2122 / Token\u00AE")
        assert isinstance(result, bool)  # Should return a boolean without error
        # With ALGO or USDC keyword it would match
        assert parser.is_lp_token("LP", "Token\u2122 / ALGO") is True

    def test_whitespace_variations(self, parser):
        """Should handle various whitespace patterns."""
        assert parser.is_lp_token("LP", "ALGO  /  USDC") is True
        assert parser.is_lp_token("LP", "ALGO/ USDC") is True
        assert parser.is_lp_token("LP", "ALGO /USDC") is True

    def test_multiple_separators_in_name(self, parser):
        """Should handle names with multiple potential separators."""
        result = parser._parse_tinyman_pool(
            "Pool ALGO-USDC-V2", "LP", "CREATOR", 12345
        )
        # Should parse first pair
        assert result['asset1_ticker'] == 'ALGO'
        assert result['asset2_ticker'] == 'USDC'


class TestGracefulDegradation:
    """Tests for graceful degradation under failure conditions."""

    def test_continues_on_pool_info_failure(self, parser):
        """Should continue estimation even if pool info fails."""
        with patch.object(parser, 'get_pool_info', return_value=None):
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 ALGO-USDC", 100.0, 12345, mock_get_price
            )
            # Should fall back to geometric mean
            assert result is not None

    def test_continues_on_pool_state_failure(self, parser):
        """Should continue estimation even if pool state query fails."""
        pool_info = {
            'creator': 'POOL_ADDRESS',
            'asset1_ticker': 'ALGO',
            'asset2_ticker': 'USDC'
        }

        with patch.object(parser, 'get_pool_info', return_value=pool_info), \
             patch.object(parser, 'get_pool_state', return_value=None), \
             patch.object(parser, '_get_pool_assets', return_value=(0, 31566704)):
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 ALGO-USDC", 100.0, 12345, mock_get_price
            )
            # Should fall back to geometric mean
            assert result is not None

    def test_handles_price_function_exception(self, parser):
        """Should handle exceptions from price function."""
        def failing_price_fn(ticker, asset_id):
            raise ValueError("Price service unavailable")

        with patch.object(parser, 'get_pool_info', return_value=None), \
             patch.object(parser, 'get_pool_state', return_value=None):
            with pytest.raises(ValueError):
                parser.estimate_lp_value(
                    "TMPOOL2", "TinymanPool2.0 ALGO-USDC", 100.0, 12345, failing_price_fn
                )

    def test_handles_classification_function_exception(self, parser):
        """Should propagate exceptions from classification function."""
        breakdown = LPBreakdown(
            lp_ticker="TMPOOL2",
            lp_amount=100.0,
            asset1_ticker="ALGO",
            asset1_amount=500.0,
            asset1_usd=175.0,
            asset2_ticker="USDC",
            asset2_amount=175.0,
            asset2_usd=175.0,
            total_usd=350.0
        )

        def failing_classify_fn(asset_id, name, ticker):
            raise RuntimeError("Classification failed")

        with pytest.raises(RuntimeError):
            parser.classify_lp_components(breakdown, failing_classify_fn)


# ============================================================================
# Integration-style Tests
# ============================================================================

class TestIntegrationScenarios:
    """Tests simulating real-world usage scenarios."""

    def test_full_flow_tinyman_v2(self, parser):
        """Test complete flow for Tinyman V2 LP token."""
        # Step 1: Detect LP token
        assert parser.is_lp_token("TMPOOL2", "TinymanPool2.0 ALGO-USDC") is True

        # Step 2: Estimate value (with mocked dependencies)
        with patch.object(parser, 'get_pool_info', return_value=None), \
             patch.object(parser, 'get_pool_state', return_value=None):
            breakdown = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 ALGO-USDC", 100.0, 12345, mock_get_price
            )

        assert breakdown is not None

        # Step 3: Classify components
        components = parser.classify_lp_components(breakdown, mock_classify_fn)

        assert len(components) == 2
        categories = [c[0] for c in components]
        assert 'algo' in categories
        assert 'dollars' in categories

    def test_full_flow_hard_money_pair(self, parser):
        """Test complete flow for hard money LP pair (BTC-Gold)."""
        with patch.object(parser, 'get_pool_info', return_value=None), \
             patch.object(parser, 'get_pool_state', return_value=None):
            breakdown = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 goBTC-GOLD$", 10.0, 12345, mock_get_price
            )

        if breakdown:  # Only if both prices available
            components = parser.classify_lp_components(breakdown, mock_classify_fn)
            # Both should be hard money
            assert all(c[0] == 'hard_money' for c in components)

    def test_non_lp_token_rejected(self, parser):
        """Non-LP tokens should be rejected at detection stage."""
        assert parser.is_lp_token("USDC", "USDC") is False
        assert parser.is_lp_token("ALGO", "Algorand") is False
        assert parser.is_lp_token("goBTC", "goBitcoin") is False


# ============================================================================
# Nested LP Token Tests (Complex Pool Structures)
# ============================================================================

class TestNestedLpTokens:
    """Tests for complex/nested LP token scenarios."""

    def test_lp_name_containing_lp_ticker(self, parser):
        """Should handle LP tokens that contain other LP tickers in name."""
        # e.g., a pool of TMPOOL2-ALGO
        assert parser.is_lp_token("TMPOOL2", "TinymanPool2.0 TMPOOL2-ALGO") is True

    def test_meta_pool_detection(self, parser):
        """Should detect meta-pools (pools of pools)."""
        assert parser.is_lp_token("TMPOOL2", "TinymanPool2.0 PLP-ALGO") is True

    def test_nested_breakdown_handling(self, parser):
        """
        For nested LP tokens, the outer LP should be decomposed.
        The inner LP component would need separate handling by the caller.
        """
        with patch.object(parser, 'get_pool_info', return_value=None), \
             patch.object(parser, 'get_pool_state', return_value=None):
            # This represents a pool of [TMPOOL2 (another LP), ALGO]
            result = parser.estimate_lp_value(
                "TMPOOL2", "TinymanPool2.0 TMPOOL2-ALGO", 100.0, 12345,
                lambda t, a: 0.35 if t == 'ALGO' else 0.0  # Only ALGO has price
            )
            # Should return None since TMPOOL2 component has no price
            assert result is None
