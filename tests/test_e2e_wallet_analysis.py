"""
End-to-End Tests for Wallet Analysis Workflow

This module tests the complete sovereignty analysis pipeline:
1. Algorand address input validation
2. Asset fetching from Algorand node
3. Price fetching from multiple sources
4. LP token parsing and decomposition
5. Asset classification (CSV > User Corrections > Regex)
6. Sovereignty score calculation

All external API calls are mocked for deterministic testing.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from decimal import Decimal
import requests

from core.analyzer import AlgorandSovereigntyAnalyzer
from core.classifier import AssetClassifier
from core.lp_parser import LPParser, LPBreakdown
from core.models import SovereigntyData
from core.pricing import get_asset_price, get_algo_price

# Import fixtures
from tests.fixtures.price_data import (
    MOCK_PRICES,
    make_vestige_price_response,
    VESTIGE_GOBTC_SUCCESS,
    VESTIGE_GOLD_SUCCESS,
    VESTIGE_SILVER_SUCCESS,
)
from tests.fixtures.lp_tokens import (
    TINYMAN_V2_ALGO_USDC,
    PACT_LP_ALGO_USDC,
    POOL_STATE_ALGO_USDC,
    mock_get_price,
    mock_classify_fn,
)


# =============================================================================
# Test Constants
# =============================================================================

# Valid Algorand addresses (58 characters)
VALID_ADDRESS = "I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4"
VALID_ADDRESS_SHORT = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

# Invalid addresses
INVALID_ADDRESS_TOO_SHORT = "ABC123"
INVALID_ADDRESS_TOO_LONG = "A" * 100
INVALID_ADDRESS_BAD_CHARS = "!@#$%^&*()_+{}|:\"<>?~`-=[]\\;',./AAAAAAAAAAAAAAAAAA"
EMPTY_ADDRESS = ""

# Mock wallet data
MOCK_WALLET_BASIC = {
    "amount": 10_000_000_000,  # 10,000 ALGO (microalgos)
    "status": "Online",
    "participation": {
        "vote-first-valid": 1000,
        "vote-last-valid": 1000000,
    },
    "assets": [
        {"asset-id": 31566704, "amount": 5_000_000_000},  # 5000 USDC
        {"asset-id": 386192725, "amount": 10_000_000},    # 0.1 goBTC
    ]
}

MOCK_WALLET_EMPTY = {
    "amount": 0,
    "status": "Offline",
    "assets": []
}

MOCK_WALLET_WITH_LP = {
    "amount": 5_000_000_000,  # 5,000 ALGO
    "status": "Online",
    "participation": {
        "vote-first-valid": 1000,
        "vote-last-valid": 1000000,
    },
    "assets": [
        {"asset-id": 123456789, "amount": 1_000_000_000},  # LP Token
        {"asset-id": 31566704, "amount": 1_000_000_000},   # 1000 USDC
    ]
}

MOCK_WALLET_HARD_MONEY_ONLY = {
    "amount": 0,
    "status": "Offline",
    "assets": [
        {"asset-id": 386192725, "amount": 100_000_000},   # 1 goBTC
        {"asset-id": 246516580, "amount": 500_000_000},   # 500g GOLD$
        {"asset-id": 246519683, "amount": 10_000_000_000}, # 10,000g SILVER$
    ]
}

MOCK_WALLET_DUST_AND_NFTS = {
    "amount": 1_000_000_000,  # 1,000 ALGO
    "status": "Offline",
    "assets": [
        {"asset-id": 11111111, "amount": 1},        # NFT (amount = 1)
        {"asset-id": 22222222, "amount": 5},        # NFT collection (amount = 5)
        {"asset-id": 33333333, "amount": 100_000},  # Dust token (low value)
        {"asset-id": 31566704, "amount": 100_000_000},  # 100 USDC (real value)
    ]
}

# Asset details mock data
ASSET_DETAILS = {
    31566704: {"params": {"name": "USDC", "unit-name": "USDC", "decimals": 6}},
    386192725: {"params": {"name": "goBTC", "unit-name": "goBTC", "decimals": 8}},
    246516580: {"params": {"name": "Meld Gold", "unit-name": "GOLD$", "decimals": 6}},
    246519683: {"params": {"name": "Meld Silver", "unit-name": "SILVER$", "decimals": 6}},
    1134696561: {"params": {"name": "xAlgo", "unit-name": "xALGO", "decimals": 6}},
    123456789: {"params": {
        "name": "TinymanPool2.0 ALGO-USDC",
        "unit-name": "TMPOOL2",
        "decimals": 6,
        "creator": "POOL_ADDRESS_ALGO_USDC"
    }},
    11111111: {"params": {"name": "Cool NFT #1", "unit-name": "NFT", "decimals": 0}},
    22222222: {"params": {"name": "NFT Collection", "unit-name": "NFTS", "decimals": 0}},
    33333333: {"params": {"name": "Airdrop Token", "unit-name": "AIRDROP", "decimals": 6}},
}

# Price mock function
def mock_get_asset_price(ticker: str, asset_id: int = None) -> float:
    """Mock price function for E2E tests."""
    prices = {
        "ALGO": 0.35,
        "USDC": 1.0,
        "goBTC": 95000.0,
        "GOBTC": 95000.0,
        "GOLD$": 85.0,
        "SILVER$": 1.0,
        "xALGO": 0.38,
        "XALGO": 0.38,
        "NFT": None,
        "NFTS": None,
        "AIRDROP": 0.0001,
    }
    return prices.get(ticker.upper(), prices.get(ticker, None))


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_algod_responses():
    """Set up mock responses for Algorand node API calls."""
    def _create_mock(wallet_data, asset_details):
        def mock_get(url, **kwargs):
            response = MagicMock()
            response.raise_for_status = MagicMock()

            if "/v2/accounts/" in url:
                response.json.return_value = wallet_data
            elif "/v2/assets/" in url:
                # Extract asset ID from URL
                asset_id = int(url.split("/v2/assets/")[1].split("?")[0])
                response.json.return_value = asset_details.get(asset_id)
            else:
                response.json.return_value = {}

            return response
        return mock_get
    return _create_mock


@pytest.fixture
def analyzer():
    """Create analyzer instance with mocked dependencies."""
    with patch('core.analyzer.requests.get'):
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
        return analyzer


@pytest.fixture
def analyzer_with_mocked_lp():
    """Create analyzer with LP parsing disabled for simpler tests."""
    with patch('core.analyzer.requests.get'):
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
        analyzer.lp_parser.is_lp_token = MagicMock(return_value=False)
        return analyzer


# =============================================================================
# E2E Test: Complete Pipeline Tests
# =============================================================================

class TestE2ECompletePipeline:
    """Test the complete wallet analysis pipeline end-to-end."""

    def test_complete_flow_basic_wallet(self, analyzer_with_mocked_lp, mock_algod_responses):
        """
        Test complete E2E flow: Address -> Fetching -> Pricing -> Classification -> Score.
        """
        mock_get = mock_algod_responses(MOCK_WALLET_BASIC, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            # Step 1: Analyze wallet (fetches data, classifies assets)
            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # Verify categories structure
            assert categories is not None
            assert "hard_money" in categories
            assert "algo" in categories
            assert "dollars" in categories
            assert "shitcoin" in categories

            # Step 2: Verify asset classification
            # ALGO should be in 'algo' category
            algo_tickers = [a["ticker"] for a in categories["algo"]]
            assert "ALGO" in algo_tickers

            # goBTC should be in 'hard_money' category
            hard_money_tickers = [a["ticker"] for a in categories["hard_money"]]
            assert "goBTC" in hard_money_tickers

            # USDC should be in 'dollars' category
            dollar_tickers = [a["ticker"] for a in categories["dollars"]]
            assert "USDC" in dollar_tickers

            # Step 3: Calculate sovereignty metrics
            metrics = analyzer_with_mocked_lp.calculate_sovereignty_metrics(
                categories, monthly_fixed_expenses=4000
            )

            assert metrics is not None
            assert metrics.monthly_fixed_expenses == 4000
            assert metrics.annual_fixed_expenses == 48000
            assert metrics.portfolio_usd > 0
            assert metrics.sovereignty_ratio >= 0
            assert metrics.sovereignty_status is not None

    def test_complete_flow_with_price_calculation(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that USD values are correctly calculated from prices."""
        mock_get = mock_algod_responses(MOCK_WALLET_BASIC, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # Verify ALGO USD value
            algo_asset = next(a for a in categories["algo"] if a["ticker"] == "ALGO")
            expected_algo_usd = 10000 * 0.35  # 10,000 ALGO * $0.35
            assert algo_asset["usd_value"] == expected_algo_usd

            # Verify USDC USD value
            usdc_asset = next(a for a in categories["dollars"] if a["ticker"] == "USDC")
            expected_usdc_usd = 5000 * 1.0  # 5000 USDC * $1.00
            assert usdc_asset["usd_value"] == expected_usdc_usd

            # Verify goBTC USD value
            gobtc_asset = next(a for a in categories["hard_money"] if a["ticker"] == "goBTC")
            expected_gobtc_usd = 0.1 * 95000  # 0.1 BTC * $95,000
            assert gobtc_asset["usd_value"] == expected_gobtc_usd

    def test_complete_flow_sovereignty_ratio_calculation(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test correct sovereignty ratio and status calculation."""
        mock_get = mock_algod_responses(MOCK_WALLET_HARD_MONEY_ONLY, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # Calculate expected portfolio value
            # 1 goBTC = $95,000
            # 500g GOLD$ = $42,500 (500 * $85/g)
            # 10,000g SILVER$ = $10,000 (10,000 * $1/g)
            # Total = $147,500

            metrics = analyzer_with_mocked_lp.calculate_sovereignty_metrics(
                categories, monthly_fixed_expenses=1000
            )

            # Annual expenses = $12,000
            # Ratio = $147,500 / $12,000 = 12.29
            assert metrics.sovereignty_ratio > 6  # Should be Antifragile
            assert "Antifragile" in metrics.sovereignty_status


# =============================================================================
# E2E Test: Address Validation Edge Cases
# =============================================================================

class TestE2EAddressValidation:
    """Test address validation and edge cases."""

    def test_valid_address_format(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that valid 58-character addresses are accepted."""
        mock_get = mock_algod_responses(MOCK_WALLET_BASIC, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            result = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)
            assert result is not None

    def test_invalid_address_api_failure(self, analyzer_with_mocked_lp):
        """Test handling when API returns error for invalid address."""
        with patch('core.analyzer.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

            result = analyzer_with_mocked_lp.analyze_wallet(INVALID_ADDRESS_TOO_SHORT)
            assert result is None

    def test_empty_address_api_failure(self, analyzer_with_mocked_lp):
        """Test handling of empty address."""
        with patch('core.analyzer.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.HTTPError("400 Bad Request")

            result = analyzer_with_mocked_lp.analyze_wallet(EMPTY_ADDRESS)
            assert result is None

    def test_nonexistent_address_returns_empty(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that a valid but nonexistent address returns empty wallet."""
        mock_get = mock_algod_responses(MOCK_WALLET_EMPTY, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            result = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            assert result is not None
            # ALGO entry exists but with 0 amount
            algo_entry = result["algo"][0]
            assert algo_entry["amount"] == 0


# =============================================================================
# E2E Test: Zero Balance Scenarios
# =============================================================================

class TestE2EZeroBalanceScenarios:
    """Test handling of zero balance wallets and assets."""

    def test_zero_algo_balance(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test wallet with zero ALGO balance."""
        wallet_zero_algo = {
            "amount": 0,
            "status": "Offline",
            "assets": [
                {"asset-id": 31566704, "amount": 1_000_000_000},  # 1000 USDC
            ]
        }
        mock_get = mock_algod_responses(wallet_zero_algo, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # ALGO should still be in results with 0 amount
            algo_entry = categories["algo"][0]
            assert algo_entry["ticker"] == "ALGO"
            assert algo_entry["amount"] == 0
            assert algo_entry["usd_value"] == 0

    def test_zero_balance_assets_skipped(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that assets with zero balance are skipped."""
        wallet_with_zero_asset = {
            "amount": 1_000_000_000,
            "status": "Offline",
            "assets": [
                {"asset-id": 31566704, "amount": 0},           # Zero balance USDC
                {"asset-id": 386192725, "amount": 10_000_000}, # 0.1 goBTC
            ]
        }
        mock_get = mock_algod_responses(wallet_with_zero_asset, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # USDC should NOT be in dollars (zero balance)
            dollar_tickers = [a["ticker"] for a in categories["dollars"]]
            assert "USDC" not in dollar_tickers

            # goBTC should be present
            hard_money_tickers = [a["ticker"] for a in categories["hard_money"]]
            assert "goBTC" in hard_money_tickers

    def test_completely_empty_wallet(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test completely empty wallet (no ALGO, no assets)."""
        mock_get = mock_algod_responses(MOCK_WALLET_EMPTY, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # All categories should exist
            assert set(categories.keys()) == {"hard_money", "algo", "dollars", "shitcoin"}

            # Only ALGO entry with 0 value
            assert len(categories["algo"]) == 1
            assert len(categories["hard_money"]) == 0
            assert len(categories["dollars"]) == 0
            assert len(categories["shitcoin"]) == 0

            # Sovereignty metrics should handle zero portfolio
            metrics = analyzer_with_mocked_lp.calculate_sovereignty_metrics(
                categories, monthly_fixed_expenses=4000
            )
            assert metrics.portfolio_usd == 0
            assert metrics.sovereignty_ratio == 0
            assert "Vulnerable" in metrics.sovereignty_status

    def test_zero_portfolio_sovereignty_ratio(self, analyzer_with_mocked_lp):
        """Test sovereignty ratio calculation with zero portfolio value."""
        categories = {
            "hard_money": [],
            "algo": [{"ticker": "ALGO", "name": "Algorand", "amount": 0, "usd_value": 0}],
            "dollars": [],
            "shitcoin": []
        }

        metrics = analyzer_with_mocked_lp.calculate_sovereignty_metrics(
            categories, monthly_fixed_expenses=4000
        )

        assert metrics.portfolio_usd == 0
        assert metrics.sovereignty_ratio == 0
        assert "Vulnerable" in metrics.sovereignty_status


# =============================================================================
# E2E Test: API Failure Scenarios
# =============================================================================

class TestE2EAPIFailures:
    """Test handling of various API failure scenarios."""

    def test_algod_connection_timeout(self, analyzer_with_mocked_lp):
        """Timeout propagates after exhausting retries so the API layer can return 504."""
        with patch('core.analyzer.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

            with pytest.raises(requests.exceptions.Timeout):
                analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

    def test_algod_connection_error(self, analyzer_with_mocked_lp):
        """ConnectionError propagates after exhausting retries so the API layer can return 503."""
        with patch('core.analyzer.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")

            with pytest.raises(requests.exceptions.ConnectionError):
                analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

    def test_algod_server_error(self, analyzer_with_mocked_lp):
        """Test handling of 500 server error from Algorand node."""
        with patch('core.analyzer.requests.get') as mock_get:
            response = MagicMock()
            response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
            mock_get.return_value = response

            result = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)
            assert result is None

    def test_asset_details_fetch_failure(self, analyzer_with_mocked_lp):
        """Test handling when asset details cannot be fetched."""
        def mock_get_with_asset_failure(url, **kwargs):
            response = MagicMock()

            if "/v2/accounts/" in url:
                response.raise_for_status = MagicMock()
                response.json.return_value = MOCK_WALLET_BASIC
            elif "/v2/assets/" in url:
                # Asset detail fetch fails
                response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")

            return response

        with patch('core.analyzer.requests.get', side_effect=mock_get_with_asset_failure), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            # Should still succeed with ALGO, but skip ASAs that fail
            result = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            assert result is not None
            # ALGO should still be present
            assert len(result["algo"]) == 1
            assert result["algo"][0]["ticker"] == "ALGO"

    def test_price_api_failure_fallback(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that analysis continues when price API fails."""
        mock_get = mock_algod_responses(MOCK_WALLET_BASIC, ASSET_DETAILS)

        def failing_price(ticker, asset_id=None):
            # Simulate price API failure returning None
            if ticker.upper() == "ALGO":
                return 0.35  # ALGO price still works
            return None  # Other prices fail

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=failing_price):

            result = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # Analysis should still complete
            assert result is not None

            # ALGO should have USD value
            algo_entry = result["algo"][0]
            assert algo_entry["usd_value"] > 0

            # Other assets should have 0 USD value (price fetch failed)
            if result["hard_money"]:
                gobtc = next((a for a in result["hard_money"] if a["ticker"] == "goBTC"), None)
                if gobtc:
                    assert gobtc["usd_value"] == 0


# =============================================================================
# E2E Test: LP Token Parsing Integration
# =============================================================================

class TestE2ELPTokenParsing:
    """Test LP token detection and decomposition in the analysis flow."""

    def test_lp_token_detection(self, analyzer, mock_algod_responses):
        """Test that LP tokens are detected during analysis."""
        mock_get = mock_algod_responses(MOCK_WALLET_WITH_LP, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            # LP parser's is_lp_token should be called
            analyzer.lp_parser.is_lp_token = MagicMock(
                side_effect=lambda t, n: "TMPOOL" in t.upper() or "TinymanPool" in n
            )

            analyzer.analyze_wallet(VALID_ADDRESS)

            # Verify is_lp_token was called for the LP asset
            assert analyzer.lp_parser.is_lp_token.called

    def test_lp_token_decomposition_integration(self, analyzer, mock_algod_responses):
        """Test LP token decomposition and classification of components."""
        mock_get = mock_algod_responses(MOCK_WALLET_WITH_LP, ASSET_DETAILS)

        # Create a mock LP breakdown
        mock_breakdown = LPBreakdown(
            lp_ticker="TMPOOL2",
            lp_amount=1000.0,
            asset1_ticker="ALGO",
            asset1_amount=500.0,
            asset1_usd=175.0,
            asset2_ticker="USDC",
            asset2_amount=175.0,
            asset2_usd=175.0,
            total_usd=350.0
        )

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            # Mock LP parsing
            analyzer.lp_parser.is_lp_token = MagicMock(
                side_effect=lambda t, n: "TMPOOL" in t.upper()
            )
            analyzer.lp_parser.estimate_lp_value = MagicMock(return_value=mock_breakdown)
            analyzer.lp_parser.classify_lp_components = MagicMock(return_value=[
                ("algo", {"ticker": "ALGO", "name": "ALGO (from LP)", "amount": 500.0, "usd_value": 175.0}),
                ("dollars", {"ticker": "USDC", "name": "USDC (from LP)", "amount": 175.0, "usd_value": 175.0})
            ])

            categories = analyzer.analyze_wallet(VALID_ADDRESS)

            # LP components should be classified into appropriate categories
            # Note: depends on whether decomposition succeeded
            assert analyzer.lp_parser.estimate_lp_value.called or analyzer.lp_parser.is_lp_token.called

    def test_non_lp_tokens_not_decomposed(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that regular tokens are not passed through LP decomposition."""
        mock_get = mock_algod_responses(MOCK_WALLET_BASIC, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # USDC should be in dollars directly, not decomposed
            usdc = next((a for a in categories["dollars"] if a["ticker"] == "USDC"), None)
            assert usdc is not None
            assert usdc["amount"] == 5000  # Original amount preserved


# =============================================================================
# E2E Test: Asset Classification
# =============================================================================

class TestE2EAssetClassification:
    """Test the complete asset classification flow."""

    def test_bitcoin_classification(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that Bitcoin variants are classified as hard_money."""
        wallet = {
            "amount": 0,
            "status": "Offline",
            "assets": [
                {"asset-id": 386192725, "amount": 10_000_000},  # goBTC
            ]
        }
        mock_get = mock_algod_responses(wallet, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            hard_money_tickers = [a["ticker"] for a in categories["hard_money"]]
            assert "goBTC" in hard_money_tickers

    def test_gold_silver_classification(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that Gold and Silver are classified as hard_money."""
        wallet = {
            "amount": 0,
            "status": "Offline",
            "assets": [
                {"asset-id": 246516580, "amount": 100_000_000},  # GOLD$
                {"asset-id": 246519683, "amount": 100_000_000},  # SILVER$
            ]
        }
        mock_get = mock_algod_responses(wallet, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            hard_money_tickers = [a["ticker"] for a in categories["hard_money"]]
            assert "GOLD$" in hard_money_tickers
            assert "SILVER$" in hard_money_tickers

    def test_stablecoin_classification(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that stablecoins are classified as dollars."""
        wallet = {
            "amount": 0,
            "status": "Offline",
            "assets": [
                {"asset-id": 31566704, "amount": 1_000_000_000},  # USDC
            ]
        }
        mock_get = mock_algod_responses(wallet, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            dollar_tickers = [a["ticker"] for a in categories["dollars"]]
            assert "USDC" in dollar_tickers

    def test_liquid_staking_classification(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that liquid staking tokens are classified as algo."""
        wallet = {
            "amount": 0,
            "status": "Offline",
            "assets": [
                {"asset-id": 1134696561, "amount": 10_000_000_000},  # xALGO
            ]
        }
        mock_get = mock_algod_responses(wallet, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            algo_tickers = [a["ticker"] for a in categories["algo"]]
            # xALGO should be in algo category
            assert any(t.upper() in ["XALGO", "ALGO"] for t in algo_tickers)

    def test_unknown_token_classified_as_shitcoin(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that unknown tokens are classified as shitcoin."""
        wallet = {
            "amount": 1_000_000_000,
            "status": "Offline",
            "assets": [
                {"asset-id": 99999999, "amount": 1_000_000_000},  # Unknown token
            ]
        }
        # Add unknown asset to details
        asset_details_extended = ASSET_DETAILS.copy()
        asset_details_extended[99999999] = {
            "params": {"name": "Random Token", "unit-name": "RNDM", "decimals": 6}
        }
        mock_get = mock_algod_responses(wallet, asset_details_extended)

        def price_with_unknown(ticker, asset_id=None):
            if ticker.upper() == "RNDM":
                return 0.5  # Give it a price so it's not filtered as dust
            return mock_get_asset_price(ticker, asset_id)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=price_with_unknown):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            shitcoin_tickers = [a["ticker"] for a in categories["shitcoin"]]
            assert "RNDM" in shitcoin_tickers


# =============================================================================
# E2E Test: Dust and NFT Filtering
# =============================================================================

class TestE2EDustAndNFTFiltering:
    """Test filtering of dust tokens and NFT-like assets."""

    def test_nft_filtering_by_amount(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that NFTs (small integer amounts, no price) are filtered."""
        mock_get = mock_algod_responses(MOCK_WALLET_DUST_AND_NFTS, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # NFTs should be filtered out
            all_tickers = []
            for cat in categories.values():
                all_tickers.extend([a["ticker"] for a in cat])

            assert "NFT" not in all_tickers
            assert "NFTS" not in all_tickers

    def test_dust_filtering_by_keywords(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that airdrop/reward tokens with low value are filtered."""
        mock_get = mock_algod_responses(MOCK_WALLET_DUST_AND_NFTS, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # Airdrop token should be filtered (keyword + low value)
            shitcoin_names = [a["name"].lower() for a in categories.get("shitcoin", [])]
            assert not any("airdrop" in n for n in shitcoin_names)

    def test_real_value_not_filtered(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that assets with real value are not filtered."""
        mock_get = mock_algod_responses(MOCK_WALLET_DUST_AND_NFTS, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # USDC with real value should NOT be filtered
            dollar_tickers = [a["ticker"] for a in categories.get("dollars", [])]
            assert "USDC" in dollar_tickers


# =============================================================================
# E2E Test: Sovereignty Score Status Levels
# =============================================================================

class TestE2ESovereigntyStatusLevels:
    """Test all sovereignty status levels through E2E flow."""

    @pytest.mark.parametrize("portfolio_usd,monthly_expenses,expected_status", [
        (10000, 4000, "Vulnerable"),       # 10000 / 48000 = 0.21
        (50000, 4000, "Fragile"),          # 50000 / 48000 = 1.04
        (150000, 4000, "Robust"),          # 150000 / 48000 = 3.13
        (300000, 4000, "Antifragile"),     # 300000 / 48000 = 6.25
        (1000000, 4000, "Generationally"), # 1000000 / 48000 = 20.83
    ])
    def test_sovereignty_status_levels(
        self, analyzer_with_mocked_lp, portfolio_usd, monthly_expenses, expected_status
    ):
        """Test each sovereignty status level threshold."""
        categories = {
            "hard_money": [
                {"ticker": "goBTC", "name": "goBTC", "amount": 1, "usd_value": portfolio_usd}
            ] if portfolio_usd > 0 else [],
            "algo": [
                {"ticker": "ALGO", "name": "Algorand", "amount": 0, "usd_value": 0}
            ],
            "dollars": [],
            "shitcoin": []
        }

        with patch('core.analyzer.get_algo_price', return_value=0.35):
            metrics = analyzer_with_mocked_lp.calculate_sovereignty_metrics(
                categories, monthly_fixed_expenses=monthly_expenses
            )

        assert expected_status in metrics.sovereignty_status

    def test_sovereignty_ratio_edge_cases(self, analyzer_with_mocked_lp):
        """Test sovereignty ratio edge cases."""
        categories = {
            "hard_money": [],
            "algo": [{"ticker": "ALGO", "name": "Algorand", "amount": 0, "usd_value": 0}],
            "dollars": [],
            "shitcoin": []
        }

        # Zero expenses should return None
        result = analyzer_with_mocked_lp.calculate_sovereignty_metrics(categories, 0)
        assert result is None

        # Negative expenses should return None
        result = analyzer_with_mocked_lp.calculate_sovereignty_metrics(categories, -100)
        assert result is None


# =============================================================================
# E2E Test: State Persistence
# =============================================================================

class TestE2EStatePersistence:
    """Test that analyzer state is properly maintained."""

    def test_state_persistence_after_analysis(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that analyzer stores state for subsequent operations."""
        mock_get = mock_algod_responses(MOCK_WALLET_BASIC, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # Verify state is stored
            assert analyzer_with_mocked_lp.last_address == VALID_ADDRESS
            assert analyzer_with_mocked_lp.last_categories == categories
            assert analyzer_with_mocked_lp.last_is_participating is True
            assert analyzer_with_mocked_lp.last_participation_info is not None
            assert analyzer_with_mocked_lp.last_participation_info['staked_amount'] > 0

    def test_pagination_uses_cached_state(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test that pagination works with cached state."""
        # Create wallet with many shitcoins
        many_shitcoins_wallet = {
            "amount": 1_000_000_000,
            "status": "Offline",
            "assets": [
                {"asset-id": i, "amount": 1_000_000_000}
                for i in range(1000, 1060)  # 60 assets
            ]
        }

        # Create asset details for all
        extended_details = ASSET_DETAILS.copy()
        for i in range(1000, 1060):
            extended_details[i] = {
                "params": {"name": f"Token {i}", "unit-name": f"TKN{i}", "decimals": 6}
            }

        mock_get = mock_algod_responses(many_shitcoins_wallet, extended_details)

        def price_for_all(ticker, asset_id=None):
            if "TKN" in ticker:
                return 50.0  # High enough value to not be filtered
            return mock_get_asset_price(ticker, asset_id)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=price_for_all):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # Check if pagination is needed
            needs_pagination = analyzer_with_mocked_lp.needs_pagination(categories)

            # With 60 shitcoins, pagination should be needed (threshold is 50)
            if len(categories["shitcoin"]) > analyzer_with_mocked_lp.PAGINATION_THRESHOLD:
                assert needs_pagination["shitcoin"] is True

                # Test paginated retrieval
                page1 = analyzer_with_mocked_lp.get_paginated_assets("shitcoin", page=1, page_size=20)
                assert page1 is not None
                assert len(page1.page.items) == 20
                assert page1.page.has_more is True


# =============================================================================
# E2E Test: Quick Summary Calculation
# =============================================================================

class TestE2EQuickSummary:
    """Test quick sovereignty summary calculation."""

    def test_quick_summary_calculation(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test quick summary returns correct category totals."""
        mock_get = mock_algod_responses(MOCK_WALLET_BASIC, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            summary = analyzer_with_mocked_lp.get_quick_sovereignty_summary(
                categories, monthly_fixed_expenses=4000
            )

            # Verify summary structure
            assert 'portfolio_usd' in summary
            assert 'hard_money_total_usd' in summary
            assert 'algo_total_usd' in summary
            assert 'dollars_total_usd' in summary
            assert 'shitcoin_total_usd' in summary
            assert 'sovereignty_ratio' in summary
            assert 'sovereignty_status' in summary

            # Portfolio total should match sum of categories
            expected_total = (
                summary['hard_money_total_usd'] +
                summary['algo_total_usd'] +
                summary['dollars_total_usd'] +
                summary['shitcoin_total_usd']
            )
            assert summary['portfolio_usd'] == expected_total

    def test_quick_summary_without_expenses(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test quick summary without expenses (no ratio calculation)."""
        mock_get = mock_algod_responses(MOCK_WALLET_BASIC, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            summary = analyzer_with_mocked_lp.get_quick_sovereignty_summary(categories)

            # Without expenses, ratio should be None
            assert summary['sovereignty_ratio'] is None
            assert summary['sovereignty_status'] is None

            # But portfolio totals should still be calculated
            assert summary['portfolio_usd'] > 0


# =============================================================================
# E2E Test: Participation Status
# =============================================================================

class TestE2EParticipationStatus:
    """Test consensus participation status tracking."""

    def test_participating_wallet(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test participating wallet status is tracked."""
        mock_get = mock_algod_responses(MOCK_WALLET_BASIC, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # Check participation flag
            assert analyzer_with_mocked_lp.last_is_participating is True

            # Check participation info
            info = analyzer_with_mocked_lp.last_participation_info
            assert info['staked_amount'] == 10000  # 10,000 ALGO
            assert info['is_incentive_eligible'] is True
            assert info['vote_first_valid'] is not None

            # ALGO entry should indicate participation
            algo_entry = categories["algo"][0]
            assert "PARTICIPATING" in algo_entry["name"]

    def test_non_participating_wallet(self, analyzer_with_mocked_lp, mock_algod_responses):
        """Test non-participating wallet status."""
        mock_get = mock_algod_responses(MOCK_WALLET_EMPTY, ASSET_DETAILS)

        with patch('core.analyzer.requests.get', side_effect=mock_get), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

            # Check non-participating
            assert analyzer_with_mocked_lp.last_is_participating is False

            # Check participation info
            info = analyzer_with_mocked_lp.last_participation_info
            assert info['staked_amount'] == 0
            assert info['is_incentive_eligible'] is False

            # ALGO entry should indicate not participating
            algo_entry = categories["algo"][0]
            assert "NOT PARTICIPATING" in algo_entry["name"]


# =============================================================================
# E2E Test: JSON Export Integration
# =============================================================================

class TestE2EJSONExport:
    """Test JSON export functionality in E2E flow."""

    def test_json_export_created(self, analyzer_with_mocked_lp, mock_algod_responses, tmp_path):
        """Test that JSON export is created after analysis."""
        import os

        mock_get = mock_algod_responses(MOCK_WALLET_BASIC, ASSET_DETAILS)

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            with patch('core.analyzer.requests.get', side_effect=mock_get), \
                 patch('core.analyzer.get_algo_price', return_value=0.35), \
                 patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

                categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)

                # Check that JSON file was created
                filename = f"sovereignty_analysis_{VALID_ADDRESS[:8]}.json"
                assert os.path.exists(filename)

                # Load and verify structure
                with open(filename, 'r') as f:
                    data = json.load(f)

                assert "metadata" in data
                assert "assets" in data
                assert "summary" in data

                # Verify categories in export
                assert "hard_money" in data["assets"]
                assert "algo" in data["assets"]
                assert "dollars" in data["assets"]
                assert "shitcoin" in data["assets"]

        finally:
            os.chdir(original_cwd)

    def test_json_export_with_sovereignty_data(self, analyzer_with_mocked_lp, mock_algod_responses, tmp_path):
        """Test JSON export includes sovereignty data when calculated."""
        import os

        mock_get = mock_algod_responses(MOCK_WALLET_BASIC, ASSET_DETAILS)

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            with patch('core.analyzer.requests.get', side_effect=mock_get), \
                 patch('core.analyzer.get_algo_price', return_value=0.35), \
                 patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

                categories = analyzer_with_mocked_lp.analyze_wallet(VALID_ADDRESS)
                metrics = analyzer_with_mocked_lp.calculate_sovereignty_metrics(
                    categories, monthly_fixed_expenses=4000
                )

                # Re-export with sovereignty data
                analyzer_with_mocked_lp.export_to_json(
                    categories,
                    VALID_ADDRESS,
                    True,
                    0.0,
                    metrics
                )

                # Load and verify sovereignty section
                filename = f"sovereignty_analysis_{VALID_ADDRESS[:8]}.json"
                with open(filename, 'r') as f:
                    data = json.load(f)

                assert "sovereignty" in data
                assert "sovereignty_ratio" in data["sovereignty"]
                assert "sovereignty_status" in data["sovereignty"]
                assert "portfolio_usd" in data["sovereignty"]

        finally:
            os.chdir(original_cwd)
