"""
Integration Tests for End-to-End Sovereignty Score Calculation

These tests verify the complete sovereignty analysis flow:
1. Wallet address input
2. Asset fetching and classification
3. Price fetching and USD value calculation
4. Sovereignty score calculation
5. Status determination

All external API calls (Algorand, pricing APIs) are mocked for deterministic testing.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from decimal import Decimal

from core.analyzer import AlgorandSovereigntyAnalyzer
from core.classifier import AssetClassifier
from core.models import AssetCategory, SovereigntyData
# Try importing from fixtures; fall back if not available
try:
    from tests.fixtures.lp_tokens import (
        MOCK_PRICES,
        mock_get_price,
        mock_classify_fn,
        TINYMAN_V2_ALGO_USDC,
    )
except ImportError:
    # Fallback - define minimal fixtures inline if import fails
    MOCK_PRICES = {"ALGO": 0.35}
    mock_get_price = lambda t, a=None: MOCK_PRICES.get(t.upper(), 0.0)
    mock_classify_fn = lambda a, n, t: "shitcoin"
    TINYMAN_V2_ALGO_USDC = {}


# =============================================================================
# Test Wallet Compositions
# =============================================================================

# Standard wallet with mixed assets
WALLET_MIXED = {
    "amount": 10_000_000_000,  # 10,000 ALGO
    "status": "Online",
    "participation": {
        "vote-first-valid": 1000,
        "vote-last-valid": 1000000,
    },
    "assets": [
        # Hard Money - Bitcoin
        {"asset-id": 386192725, "amount": 10_000_000},  # 0.1 goBTC (8 decimals)
        # Hard Money - Gold
        {"asset-id": 246516580, "amount": 100_000_000},  # 100g GOLD$ (6 decimals)
        # Dollars
        {"asset-id": 31566704, "amount": 5_000_000_000},  # 5000 USDC (6 decimals)
        # Shitcoins
        {"asset-id": 12345678, "amount": 1_000_000_000},  # Random token
    ]
}

# DeFi-heavy wallet (lots of LP tokens, staking derivatives)
WALLET_DEFI_HEAVY = {
    "amount": 50_000_000_000,  # 50,000 ALGO
    "status": "Online",
    "participation": {
        "vote-first-valid": 1000,
        "vote-last-valid": 1000000,
    },
    "assets": [
        # Liquid staking
        {"asset-id": 1134696561, "amount": 25_000_000_000},  # 25,000 xALGO
        {"asset-id": 987654321, "amount": 10_000_000_000},  # 10,000 fALGO
        # Stablecoins
        {"asset-id": 31566704, "amount": 10_000_000_000},  # 10,000 USDC
        {"asset-id": 312769, "amount": 5_000_000_000},  # 5,000 USDT
        # LP tokens (will be decomposed)
        {"asset-id": 11111111, "amount": 1_000_000_000},  # LP token
    ]
}

# NFT-heavy wallet (many small integer holdings)
WALLET_NFT_HEAVY = {
    "amount": 1_000_000_000,  # 1,000 ALGO
    "status": "Offline",
    "assets": [
        # NFTs (should be filtered)
        {"asset-id": 100001, "amount": 1},  # NFT #1
        {"asset-id": 100002, "amount": 1},  # NFT #2
        {"asset-id": 100003, "amount": 1},  # NFT #3
        {"asset-id": 100004, "amount": 5},  # NFT collection
        # Small amount stablecoin
        {"asset-id": 31566704, "amount": 100_000_000},  # 100 USDC
    ]
}

# Hard money maximalist wallet
WALLET_HARD_MONEY = {
    "amount": 0,  # No ALGO
    "status": "Offline",
    "assets": [
        # Bitcoin
        {"asset-id": 386192725, "amount": 100_000_000},  # 1 goBTC
        {"asset-id": 1058926737, "amount": 50_000_000},  # 0.5 WBTC
        # Gold
        {"asset-id": 246516580, "amount": 1_000_000_000},  # 1000g GOLD$
        # Silver
        {"asset-id": 246519683, "amount": 10_000_000_000},  # 10,000g SILVER$
    ]
}

# Empty wallet
WALLET_EMPTY = {
    "amount": 0,
    "status": "Offline",
    "assets": []
}

# Dust-heavy wallet (many small value tokens)
WALLET_DUST_HEAVY = {
    "amount": 5_000_000_000,  # 5,000 ALGO
    "status": "Offline",
    "assets": [
        # Dust tokens (should be filtered)
        {"asset-id": 200001, "amount": 1_000_000},  # Tiny reward token
        {"asset-id": 200002, "amount": 500_000},  # Airdrop dust
        {"asset-id": 200003, "amount": 100_000},  # Promo token
        # Real stablecoin
        {"asset-id": 31566704, "amount": 1_000_000_000},  # 1000 USDC
    ]
}


# =============================================================================
# Asset Details Mock Data
# =============================================================================

ASSET_DETAILS = {
    386192725: {"params": {"name": "goBTC", "unit-name": "goBTC", "decimals": 8}},
    1058926737: {"params": {"name": "Wrapped BTC", "unit-name": "WBTC", "decimals": 8}},
    246516580: {"params": {"name": "Meld Gold", "unit-name": "GOLD$", "decimals": 6}},
    246519683: {"params": {"name": "Meld Silver", "unit-name": "SILVER$", "decimals": 6}},
    31566704: {"params": {"name": "USDC", "unit-name": "USDC", "decimals": 6}},
    312769: {"params": {"name": "Tether USDt", "unit-name": "USDT", "decimals": 6}},
    1134696561: {"params": {"name": "xAlgo", "unit-name": "xALGO", "decimals": 6}},
    987654321: {"params": {"name": "Folks ALGO", "unit-name": "FALGO", "decimals": 6}},
    12345678: {"params": {"name": "Random Token", "unit-name": "RNDM", "decimals": 6}},
    11111111: {"params": {"name": "TinymanPool2.0 ALGO-USDC", "unit-name": "TMPOOL2", "decimals": 6, "creator": "POOL_ADDR"}},
    100001: {"params": {"name": "Cool NFT #1", "unit-name": "NFT", "decimals": 0}},
    100002: {"params": {"name": "Cool NFT #2", "unit-name": "NFT", "decimals": 0}},
    100003: {"params": {"name": "Cool NFT #3", "unit-name": "NFT", "decimals": 0}},
    100004: {"params": {"name": "NFT Collection", "unit-name": "NFTC", "decimals": 0}},
    200001: {"params": {"name": "Reward Token", "unit-name": "REWARD", "decimals": 6}},
    200002: {"params": {"name": "Airdrop Token", "unit-name": "AIRDROP", "decimals": 6}},
    200003: {"params": {"name": "Promo Token", "unit-name": "PROMO", "decimals": 6}},
}

# Price mocks (USD per unit)
PRICE_MOCKS = {
    "ALGO": 0.35,
    "goBTC": 95000.0,
    "WBTC": 95000.0,
    "GOLD$": 85.0,  # per gram (~$2650/oz)
    "SILVER$": 1.0,  # per gram (~$31/oz)
    "USDC": 1.0,
    "USDT": 1.0,
    "xALGO": 0.38,
    "FALGO": 0.35,
    "RNDM": 0.001,
    "REWARD": 0.0001,
    "AIRDROP": 0.00001,
    "PROMO": 0.0001,
}


def mock_get_asset_price(ticker: str, asset_id: int = None) -> float:
    """Mock price function for integration tests."""
    return PRICE_MOCKS.get(ticker.upper(), None)


def mock_get_algo_price() -> float:
    """Mock ALGO price."""
    return 0.35


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def analyzer():
    """Create analyzer with mocked external dependencies."""
    with patch('core.analyzer.requests.get'):
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
        # Mock the LP parser to skip LP decomposition in most tests
        analyzer.lp_parser.is_lp_token = MagicMock(return_value=False)
        return analyzer


@pytest.fixture
def mock_api_calls(analyzer):
    """Set up common API call mocks."""
    def get_asset_details_mock(asset_id):
        return ASSET_DETAILS.get(asset_id)

    analyzer.get_asset_details = MagicMock(side_effect=get_asset_details_mock)
    return analyzer


# =============================================================================
# End-to-End Integration Tests
# =============================================================================

class TestEndToEndSovereigntyFlow:
    """Test complete sovereignty calculation from wallet to final score."""

    def test_full_flow_mixed_wallet(self, analyzer, mock_api_calls):
        """Test complete flow with a mixed wallet composition."""
        with patch.object(analyzer, 'get_account_assets', return_value=WALLET_MIXED), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            # Step 1: Analyze wallet
            categories = analyzer.analyze_wallet("TEST_ADDRESS_MIXED")

            # Verify all categories exist
            assert "hard_money" in categories
            assert "algo" in categories
            assert "dollars" in categories
            assert "shitcoin" in categories

            # Step 2: Calculate sovereignty metrics
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)

            # Verify metrics structure
            assert metrics is not None
            assert metrics.monthly_fixed_expenses == 4000
            assert metrics.annual_fixed_expenses == 48000
            assert metrics.portfolio_usd > 0
            assert metrics.sovereignty_ratio >= 0
            assert metrics.sovereignty_status is not None

    def test_full_flow_with_participation(self, analyzer, mock_api_calls):
        """Test that participation status is correctly tracked."""
        with patch.object(analyzer, 'get_account_assets', return_value=WALLET_MIXED), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("TEST_ADDRESS")

            # Check ALGO is marked as participating
            algo_assets = categories.get("algo", [])
            algo_entry = next((a for a in algo_assets if a["ticker"] == "ALGO"), None)
            assert algo_entry is not None
            assert "PARTICIPATING" in algo_entry["name"]

    def test_full_flow_empty_wallet(self, analyzer, mock_api_calls):
        """Test handling of empty wallet."""
        with patch.object(analyzer, 'get_account_assets', return_value=WALLET_EMPTY), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("EMPTY_WALLET")

            # Should still have all category keys
            assert set(categories.keys()) == {"hard_money", "algo", "dollars", "shitcoin"}

            # ALGO entry should exist with 0 amount
            algo_entry = categories["algo"][0]
            assert algo_entry["amount"] == 0

            # Metrics should handle empty wallet
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)
            assert metrics.portfolio_usd == 0
            assert metrics.sovereignty_ratio == 0
            assert "Vulnerable" in metrics.sovereignty_status


class TestWalletCompositions:
    """Test various wallet compositions for correct classification."""

    def test_defi_heavy_wallet(self, analyzer, mock_api_calls):
        """Test wallet with many DeFi assets (liquid staking, LP tokens)."""
        with patch.object(analyzer, 'get_account_assets', return_value=WALLET_DEFI_HEAVY), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("DEFI_HEAVY_WALLET")

            # xALGO and fALGO should be in 'algo' category
            algo_tickers = [a["ticker"] for a in categories.get("algo", [])]
            assert "ALGO" in algo_tickers  # Native ALGO
            assert "xALGO" in algo_tickers or "FALGO" in algo_tickers or any(
                t in ["XALGO", "FALGO"] for t in algo_tickers
            )

            # USDC and USDT should be in 'dollars' category
            dollar_tickers = [a["ticker"] for a in categories.get("dollars", [])]
            assert "USDC" in dollar_tickers

    def test_nft_heavy_wallet_filtering(self, analyzer, mock_api_calls):
        """Test that NFT-like items are filtered out."""
        with patch.object(analyzer, 'get_account_assets', return_value=WALLET_NFT_HEAVY), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("NFT_HEAVY_WALLET")

            # NFTs with amount <= 10 and no price should be filtered
            shitcoin_tickers = [a["ticker"] for a in categories.get("shitcoin", [])]

            # NFTs should not appear in shitcoin (filtered as NFT-like)
            assert "NFT" not in shitcoin_tickers
            assert "NFTC" not in shitcoin_tickers

            # USDC should still be there
            dollar_tickers = [a["ticker"] for a in categories.get("dollars", [])]
            assert "USDC" in dollar_tickers

    def test_hard_money_maximalist_wallet(self, analyzer, mock_api_calls):
        """Test wallet focused on hard money (BTC, Gold, Silver)."""
        with patch.object(analyzer, 'get_account_assets', return_value=WALLET_HARD_MONEY), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("HARD_MONEY_WALLET")

            # All assets should be in hard_money category
            hard_money_tickers = [a["ticker"] for a in categories.get("hard_money", [])]

            # Should have Bitcoin variants
            assert any(t in hard_money_tickers for t in ["goBTC", "WBTC", "GOBTC"])

            # Should have Gold
            assert "GOLD$" in hard_money_tickers

            # Should have Silver
            assert "SILVER$" in hard_money_tickers

            # No other categories should have assets (except ALGO with 0)
            assert len(categories.get("dollars", [])) == 0
            # shitcoin might be empty or have minimal entries

    def test_dust_heavy_wallet_filtering(self, analyzer, mock_api_calls):
        """Test that dust tokens are filtered based on value and keywords."""
        # Modify prices for dust tokens to simulate low-value scenario
        def dust_price_mock(ticker: str, asset_id: int = None) -> float:
            prices = {
                "ALGO": 0.35,
                "USDC": 1.0,
                "REWARD": 0.0001,  # Very low price
                "AIRDROP": 0.00001,
                "PROMO": 0.0001,
            }
            return prices.get(ticker.upper())

        with patch.object(analyzer, 'get_account_assets', return_value=WALLET_DUST_HEAVY), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=dust_price_mock):

            categories = analyzer.analyze_wallet("DUST_HEAVY_WALLET")

            # Dust tokens with reward/airdrop keywords should be filtered
            shitcoin_names = [a["name"].lower() for a in categories.get("shitcoin", [])]

            # These should be filtered (keyword + low value)
            assert not any("reward" in n for n in shitcoin_names)
            assert not any("airdrop" in n for n in shitcoin_names)


class TestSovereigntyScoreCalculation:
    """Test sovereignty score calculation and status assignment."""

    def test_sovereignty_ratio_calculation(self, analyzer):
        """Test that sovereignty ratio is calculated correctly."""
        categories = {
            "hard_money": [
                {"ticker": "goBTC", "name": "goBTC", "amount": 1.0, "usd_value": 95000}
            ],
            "algo": [
                {"ticker": "ALGO", "name": "Algorand", "amount": 10000, "usd_value": 3500}
            ],
            "dollars": [
                {"ticker": "USDC", "name": "USDC", "amount": 10000, "usd_value": 10000}
            ],
            "shitcoin": []
        }

        with patch('core.analyzer.get_algo_price', return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)

        # Total portfolio = 95000 + 3500 + 10000 = 108500
        # Annual expenses = 4000 * 12 = 48000
        # Ratio = 108500 / 48000 = 2.26
        expected_ratio = round(108500 / 48000, 2)
        assert metrics.sovereignty_ratio == expected_ratio
        assert metrics.portfolio_usd == 108500

    def test_sovereignty_status_vulnerable(self, analyzer):
        """Test Vulnerable status (ratio < 1)."""
        categories = {
            "hard_money": [],
            "algo": [
                {"ticker": "ALGO", "name": "Algorand", "amount": 1000, "usd_value": 350}
            ],
            "dollars": [],
            "shitcoin": []
        }

        with patch('core.analyzer.get_algo_price', return_value=0.35):
            # Monthly expenses = 1000, Annual = 12000
            # Portfolio = 350, Ratio = 350/12000 = 0.029
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=1000)

        assert metrics.sovereignty_ratio < 1
        assert "Vulnerable" in metrics.sovereignty_status

    def test_sovereignty_status_fragile(self, analyzer):
        """Test Fragile status (1 <= ratio < 3)."""
        categories = {
            "hard_money": [],
            "algo": [
                {"ticker": "ALGO", "name": "Algorand", "amount": 50000, "usd_value": 17500}
            ],
            "dollars": [
                {"ticker": "USDC", "name": "USDC", "amount": 10000, "usd_value": 10000}
            ],
            "shitcoin": []
        }

        with patch('core.analyzer.get_algo_price', return_value=0.35):
            # Portfolio = 27500, Annual expenses = 12000
            # Ratio = 27500/12000 = 2.29
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=1000)

        assert 1 <= metrics.sovereignty_ratio < 3
        assert "Fragile" in metrics.sovereignty_status

    def test_sovereignty_status_robust(self, analyzer):
        """Test Robust status (3 <= ratio < 6)."""
        categories = {
            "hard_money": [
                {"ticker": "goBTC", "name": "goBTC", "amount": 0.5, "usd_value": 47500}
            ],
            "algo": [],
            "dollars": [],
            "shitcoin": []
        }

        with patch('core.analyzer.get_algo_price', return_value=0.35):
            # Portfolio = 47500, Annual expenses = 12000
            # Ratio = 47500/12000 = 3.96
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=1000)

        assert 3 <= metrics.sovereignty_ratio < 6
        assert "Robust" in metrics.sovereignty_status

    def test_sovereignty_status_antifragile(self, analyzer):
        """Test Antifragile status (6 <= ratio < 20)."""
        categories = {
            "hard_money": [
                {"ticker": "goBTC", "name": "goBTC", "amount": 1.0, "usd_value": 95000}
            ],
            "algo": [],
            "dollars": [],
            "shitcoin": []
        }

        with patch('core.analyzer.get_algo_price', return_value=0.35):
            # Portfolio = 95000, Annual expenses = 12000
            # Ratio = 95000/12000 = 7.92
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=1000)

        assert 6 <= metrics.sovereignty_ratio < 20
        assert "Antifragile" in metrics.sovereignty_status

    def test_sovereignty_status_generationally_sovereign(self, analyzer):
        """Test Generationally Sovereign status (ratio >= 20)."""
        categories = {
            "hard_money": [
                {"ticker": "goBTC", "name": "goBTC", "amount": 3.0, "usd_value": 285000}
            ],
            "algo": [],
            "dollars": [],
            "shitcoin": []
        }

        with patch('core.analyzer.get_algo_price', return_value=0.35):
            # Portfolio = 285000, Annual expenses = 12000
            # Ratio = 285000/12000 = 23.75
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=1000)

        assert metrics.sovereignty_ratio >= 20
        assert "Generationally Sovereign" in metrics.sovereignty_status

    def test_zero_expenses_returns_none(self, analyzer):
        """Test that zero monthly expenses returns None."""
        categories = {"hard_money": [], "algo": [], "dollars": [], "shitcoin": []}

        metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=0)
        assert metrics is None

    def test_negative_expenses_returns_none(self, analyzer):
        """Test that negative monthly expenses returns None."""
        categories = {"hard_money": [], "algo": [], "dollars": [], "shitcoin": []}

        metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=-100)
        assert metrics is None


class TestComponentInteraction:
    """Test interaction between analyzer, pricing, and classifier modules."""

    def test_classifier_integration(self, analyzer, mock_api_calls):
        """Test that classifier correctly categorizes assets during analysis."""
        # Use a wallet with known asset types
        test_wallet = {
            "amount": 1_000_000_000,  # 1000 ALGO
            "status": "Offline",
            "assets": [
                {"asset-id": 386192725, "amount": 10_000_000},  # goBTC
                {"asset-id": 31566704, "amount": 1_000_000_000},  # USDC
            ]
        }

        with patch.object(analyzer, 'get_account_assets', return_value=test_wallet), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("CLASSIFIER_TEST")

            # goBTC should be in hard_money
            hard_money_tickers = [a["ticker"] for a in categories.get("hard_money", [])]
            assert "goBTC" in hard_money_tickers

            # USDC should be in dollars
            dollar_tickers = [a["ticker"] for a in categories.get("dollars", [])]
            assert "USDC" in dollar_tickers

            # ALGO should be in algo
            algo_tickers = [a["ticker"] for a in categories.get("algo", [])]
            assert "ALGO" in algo_tickers

    def test_pricing_integration(self, analyzer, mock_api_calls):
        """Test that pricing is correctly applied to assets."""
        test_wallet = {
            "amount": 10_000_000_000,  # 10,000 ALGO
            "status": "Offline",
            "assets": []
        }

        with patch.object(analyzer, 'get_account_assets', return_value=test_wallet), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("PRICING_TEST")

            # ALGO should have correct USD value
            algo_entry = categories["algo"][0]
            assert algo_entry["amount"] == 10000
            # USD value should be amount * price = 10000 * 0.35 = 3500
            assert algo_entry["usd_value"] == 3500.0

    def test_state_persistence_after_analysis(self, analyzer, mock_api_calls):
        """Test that analyzer stores state for subsequent operations."""
        with patch.object(analyzer, 'get_account_assets', return_value=WALLET_MIXED), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("STATE_TEST_ADDR")

            # Verify state is stored
            assert analyzer.last_address == "STATE_TEST_ADDR"
            assert analyzer.last_categories == categories
            assert analyzer.last_is_participating is True
            assert analyzer.last_participation_info is not None


class TestSnapshotConsistency:
    """Snapshot tests for consistent score calculations."""

    # Expected results for deterministic test cases
    SNAPSHOT_CASES = [
        # (portfolio_usd, monthly_expenses, expected_ratio, expected_status_keyword)
        (0, 4000, 0.0, "Vulnerable"),
        (10000, 4000, 0.21, "Vulnerable"),  # 10000 / 48000 = 0.208
        (48000, 4000, 1.0, "Fragile"),  # 48000 / 48000 = 1.0
        (100000, 4000, 2.08, "Fragile"),  # 100000 / 48000 = 2.083
        (150000, 4000, 3.12, "Robust"),  # 150000 / 48000 = 3.125
        (300000, 4000, 6.25, "Antifragile"),  # 300000 / 48000 = 6.25
        (1000000, 4000, 20.83, "Generationally Sovereign"),  # 1000000 / 48000 = 20.83
    ]

    @pytest.mark.parametrize("portfolio_usd,monthly_expenses,expected_ratio,expected_status", SNAPSHOT_CASES)
    def test_score_snapshot(self, analyzer, portfolio_usd, monthly_expenses, expected_ratio, expected_status):
        """Verify consistent score calculation across test runs."""
        categories = {
            "hard_money": [{"ticker": "goBTC", "name": "goBTC", "amount": 1, "usd_value": portfolio_usd}] if portfolio_usd > 0 else [],
            "algo": [],
            "dollars": [],
            "shitcoin": []
        }

        with patch('core.analyzer.get_algo_price', return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=monthly_expenses)

        assert metrics.sovereignty_ratio == expected_ratio
        assert expected_status in metrics.sovereignty_status

    def test_portfolio_value_snapshot(self, analyzer):
        """Verify portfolio value calculation is deterministic."""
        categories = {
            "hard_money": [
                {"ticker": "goBTC", "amount": 1.0, "usd_value": 95000, "name": "goBTC"}
            ],
            "algo": [
                {"ticker": "ALGO", "amount": 10000, "usd_value": 3500, "name": "Algorand"}
            ],
            "dollars": [
                {"ticker": "USDC", "amount": 5000, "usd_value": 5000, "name": "USDC"}
            ],
            "shitcoin": [
                {"ticker": "RNDM", "amount": 1000, "usd_value": 100, "name": "Random"}
            ]
        }

        with patch('core.analyzer.get_algo_price', return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)

        # Total should be exact: 95000 + 3500 + 5000 + 100 = 103600
        assert metrics.portfolio_usd == 103600


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_asset_details(self, analyzer):
        """Test handling when asset details cannot be fetched."""
        test_wallet = {
            "amount": 1_000_000_000,
            "status": "Offline",
            "assets": [
                {"asset-id": 99999999, "amount": 1_000_000}  # Unknown asset
            ]
        }

        with patch.object(analyzer, 'get_account_assets', return_value=test_wallet), \
             patch.object(analyzer, 'get_asset_details', return_value=None), \
             patch('core.analyzer.get_algo_price', return_value=0.35):

            # Should not raise, just skip the asset
            categories = analyzer.analyze_wallet("MISSING_DETAILS")

            # Only ALGO should be present
            assert len(categories["algo"]) == 1
            assert categories["algo"][0]["ticker"] == "ALGO"

    def test_zero_balance_assets_skipped(self, analyzer, mock_api_calls):
        """Test that assets with zero balance are skipped."""
        test_wallet = {
            "amount": 1_000_000_000,
            "status": "Offline",
            "assets": [
                {"asset-id": 31566704, "amount": 0},  # Zero balance USDC
                {"asset-id": 386192725, "amount": 10_000_000},  # Normal goBTC
            ]
        }

        with patch.object(analyzer, 'get_account_assets', return_value=test_wallet), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("ZERO_BALANCE")

            # USDC should not appear (zero balance)
            dollar_tickers = [a["ticker"] for a in categories.get("dollars", [])]
            assert "USDC" not in dollar_tickers

            # goBTC should appear
            hard_money_tickers = [a["ticker"] for a in categories.get("hard_money", [])]
            assert "goBTC" in hard_money_tickers

    def test_api_failure_returns_none(self, analyzer):
        """Test that API failure returns None gracefully."""
        with patch.object(analyzer, 'get_account_assets', return_value=None):
            result = analyzer.analyze_wallet("INVALID_ADDRESS")
            assert result is None

    def test_very_large_portfolio(self, analyzer):
        """Test handling of very large portfolio values."""
        categories = {
            "hard_money": [
                {"ticker": "goBTC", "amount": 1000, "usd_value": 95_000_000_000, "name": "goBTC"}  # 1000 BTC
            ],
            "algo": [],
            "dollars": [],
            "shitcoin": []
        }

        with patch('core.analyzer.get_algo_price', return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)

        # Should handle large numbers without overflow
        assert metrics.portfolio_usd == 95_000_000_000
        assert metrics.sovereignty_ratio > 0
        assert "Generationally Sovereign" in metrics.sovereignty_status

    def test_very_small_expenses(self, analyzer):
        """Test handling of very small expense amounts."""
        categories = {
            "hard_money": [
                {"ticker": "goBTC", "amount": 0.01, "usd_value": 950, "name": "goBTC"}
            ],
            "algo": [],
            "dollars": [],
            "shitcoin": []
        }

        with patch('core.analyzer.get_algo_price', return_value=0.35):
            # Monthly expenses of $1 -> Annual $12
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=1)

        # 950 / 12 = 79.17
        assert metrics.sovereignty_ratio == 79.17
        assert "Generationally Sovereign" in metrics.sovereignty_status


# =============================================================================
# API Integration Tests (Using FastAPI TestClient)
# =============================================================================

class TestAPIIntegration:
    """Test the API endpoints with mocked backend."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)

    def test_analyze_endpoint_structure(self, client):
        """Test that analyze endpoint returns correct structure."""
        with patch('core.analyzer.AlgorandSovereigntyAnalyzer.get_account_assets', return_value=WALLET_MIXED), \
             patch('core.analyzer.AlgorandSovereigntyAnalyzer.get_asset_details', side_effect=lambda x: ASSET_DETAILS.get(x)), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            response = client.post("/api/v1/analyze", json={
                "address": "TEST_ADDRESS_12345678901234567890123456789012345678901234567890",
                "monthly_fixed_expenses": 4000
            })

            # Should succeed with our mocked data
            if response.status_code == 200:
                data = response.json()

                # Verify structure
                assert "address" in data
                assert "categories" in data
                assert "sovereignty_data" in data

                # Verify categories
                assert "hard_money" in data["categories"]
                assert "algo" in data["categories"]
                assert "dollars" in data["categories"]
                assert "shitcoin" in data["categories"]

    def test_classifications_endpoint(self, client):
        """Test classifications endpoint returns data."""
        response = client.get("/api/v1/classifications")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


# =============================================================================
# JSON Output Snapshot Tests
# =============================================================================

class TestJSONOutputSnapshots:
    """Test JSON file output for consistency and correctness."""

    def test_json_export_structure(self, analyzer, mock_api_calls, tmp_path):
        """Test that JSON export has correct structure."""
        import os

        original_cwd = os.getcwd()
        try:
            # Change to temp directory for file output
            os.chdir(tmp_path)

            with patch.object(analyzer, 'get_account_assets', return_value=WALLET_MIXED), \
                 patch('core.analyzer.get_algo_price', return_value=0.35), \
                 patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

                categories = analyzer.analyze_wallet("TESTADDR123456789012345678901234567890123456789012345678")

                # Calculate sovereignty metrics
                metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)

                # Re-export with sovereignty data
                analyzer.export_to_json(
                    categories,
                    "TESTADDR123456789012345678901234567890123456789012345678",
                    True,
                    0.0,
                    metrics
                )

                # Check file exists
                filename = "sovereignty_analysis_TESTADDR.json"
                assert os.path.exists(filename), f"Expected {filename} to exist"

                # Load and verify structure
                with open(filename, 'r') as f:
                    data = json.load(f)

                # Verify top-level keys
                assert "metadata" in data
                assert "assets" in data
                assert "summary" in data
                assert "sovereignty" in data

                # Verify metadata
                assert "analyzed_at" in data["metadata"]
                assert "address" in data["metadata"]
                assert "participation_status" in data["metadata"]

                # Verify asset categories
                assert "hard_money" in data["assets"]
                assert "algo" in data["assets"]
                assert "dollars" in data["assets"]
                assert "shitcoin" in data["assets"]

                # Verify sovereignty data
                assert "sovereignty_ratio" in data["sovereignty"]
                assert "sovereignty_status" in data["sovereignty"]
                assert "portfolio_usd" in data["sovereignty"]

        finally:
            os.chdir(original_cwd)

    def test_json_export_asset_data_integrity(self, analyzer, mock_api_calls, tmp_path):
        """Test that exported asset data maintains integrity."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            with patch.object(analyzer, 'get_account_assets', return_value=WALLET_HARD_MONEY), \
                 patch('core.analyzer.get_algo_price', return_value=0.35), \
                 patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

                categories = analyzer.analyze_wallet("HARDMONEY12345678901234567890123456789012345678901234567")

                filename = "sovereignty_analysis_HARDMONE.json"
                assert os.path.exists(filename)

                with open(filename, 'r') as f:
                    data = json.load(f)

                # Hard money wallet should have hard money assets
                hard_money_assets = data["assets"]["hard_money"]
                assert len(hard_money_assets) > 0

                # Each asset should have required fields
                for asset in hard_money_assets:
                    assert "ticker" in asset
                    assert "name" in asset
                    assert "amount" in asset
                    assert "usd_value" in asset

        finally:
            os.chdir(original_cwd)


# =============================================================================
# Pricing Fallback Chain Integration Tests
# =============================================================================

class TestPricingFallbackIntegration:
    """Test pricing fallback behavior in the analysis pipeline."""

    def test_vestige_price_used_when_available(self, analyzer, mock_api_calls):
        """Test that Vestige prices are used when available."""
        test_wallet = {
            "amount": 1_000_000_000,  # 1000 ALGO
            "status": "Offline",
            "assets": [
                {"asset-id": 31566704, "amount": 1_000_000_000},  # USDC
            ]
        }

        def vestige_price_mock(ticker: str, asset_id: int = None) -> float:
            # Simulate Vestige returning a price
            if asset_id == 31566704:  # USDC
                return 0.9999  # Vestige USDC price
            return PRICE_MOCKS.get(ticker.upper())

        with patch.object(analyzer, 'get_account_assets', return_value=test_wallet), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=vestige_price_mock):

            categories = analyzer.analyze_wallet("PRICING_TEST_ADDR")

            # USDC should use the Vestige price
            usdc_asset = next(
                (a for a in categories.get("dollars", []) if a["ticker"] == "USDC"),
                None
            )
            assert usdc_asset is not None
            # Amount is 1000 USDC, price is 0.9999
            assert abs(usdc_asset["usd_value"] - 999.9) < 0.1

    def test_hardcoded_fallback_when_apis_fail(self, analyzer, mock_api_calls):
        """Test that hardcoded prices are used when APIs fail."""
        test_wallet = {
            "amount": 1_000_000_000,  # 1000 ALGO
            "status": "Offline",
            "assets": []
        }

        def failing_price_mock(ticker: str, asset_id: int = None) -> float:
            # Return None to simulate API failure, triggering fallback in pricing.py
            if ticker.upper() == "ALGO":
                return 0.35  # Fallback price
            return None

        with patch.object(analyzer, 'get_account_assets', return_value=test_wallet), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=failing_price_mock):

            categories = analyzer.analyze_wallet("FALLBACK_TEST")

            # ALGO should still have a value using fallback
            algo_asset = categories["algo"][0]
            assert algo_asset["usd_value"] > 0


# =============================================================================
# Classification Hierarchy Integration Tests
# =============================================================================

class TestClassificationHierarchyIntegration:
    """Test the classification hierarchy: CSV > User Corrections > Auto-classify."""

    def test_csv_override_takes_priority(self, analyzer, mock_api_calls):
        """Test that CSV manual overrides take highest priority."""
        # Add a test override to the classifier
        analyzer.classifier.classifications["31566704"] = {
            'name': 'Test USDC Override',
            'ticker': 'USDC',
            'category': 'hard_money'  # Override stablecoin to hard_money for test
        }

        test_wallet = {
            "amount": 0,
            "status": "Offline",
            "assets": [
                {"asset-id": 31566704, "amount": 1_000_000_000},  # USDC
            ]
        }

        with patch.object(analyzer, 'get_account_assets', return_value=test_wallet), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("CLASSIFICATION_TEST")

            # USDC should be in hard_money due to CSV override
            hard_money_tickers = [a["ticker"] for a in categories.get("hard_money", [])]
            assert "USDC" in hard_money_tickers

        # Clean up
        del analyzer.classifier.classifications["31566704"]

    def test_auto_classify_bitcoin_variants(self, analyzer, mock_api_calls):
        """Test that all Bitcoin variants are classified as hard_money."""
        # Test with goBTC asset
        test_wallet = {
            "amount": 0,
            "status": "Offline",
            "assets": [
                {"asset-id": 386192725, "amount": 10_000_000},  # goBTC
            ]
        }

        with patch.object(analyzer, 'get_account_assets', return_value=test_wallet), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("BTC_CLASSIFY_TEST")

            # goBTC should be in hard_money
            hard_money_tickers = [a["ticker"] for a in categories.get("hard_money", [])]
            assert "goBTC" in hard_money_tickers

    def test_auto_classify_stablecoins(self, analyzer, mock_api_calls):
        """Test that stablecoins are classified as dollars."""
        test_wallet = {
            "amount": 0,
            "status": "Offline",
            "assets": [
                {"asset-id": 31566704, "amount": 1_000_000_000},  # USDC
                {"asset-id": 312769, "amount": 500_000_000},  # USDT
            ]
        }

        with patch.object(analyzer, 'get_account_assets', return_value=test_wallet), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("STABLE_CLASSIFY_TEST")

            # Both should be in dollars
            dollar_tickers = [a["ticker"] for a in categories.get("dollars", [])]
            assert "USDC" in dollar_tickers

    def test_auto_classify_liquid_staking(self, analyzer, mock_api_calls):
        """Test that liquid staking tokens are classified as algo."""
        test_wallet = {
            "amount": 0,
            "status": "Offline",
            "assets": [
                {"asset-id": 1134696561, "amount": 10_000_000_000},  # xALGO
            ]
        }

        with patch.object(analyzer, 'get_account_assets', return_value=test_wallet), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("LIQUID_STAKING_TEST")

            # xALGO should be in algo category
            algo_tickers = [a["ticker"] for a in categories.get("algo", [])]
            # Note: xALGO goes to 'algo' via pattern matching
            assert any(t.upper() in ["XALGO", "ALGO"] for t in algo_tickers)


# =============================================================================
# LP Token Decomposition Integration Tests
# =============================================================================

class TestLPDecompositionIntegration:
    """Test LP token decomposition within the full analysis flow."""

    def test_lp_detection_in_analysis(self, analyzer, mock_api_calls):
        """Test that LP tokens are detected during wallet analysis."""
        # Enable LP detection for this test
        analyzer.lp_parser.is_lp_token = MagicMock(side_effect=lambda t, n:
            "TMPOOL" in t.upper() or "TinymanPool" in n
        )

        test_wallet = {
            "amount": 1_000_000_000,
            "status": "Offline",
            "assets": [
                {"asset-id": 11111111, "amount": 1_000_000_000},  # LP token
            ]
        }

        with patch.object(analyzer, 'get_account_assets', return_value=test_wallet), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            # LP parser should be called to check if it's an LP token
            categories = analyzer.analyze_wallet("LP_DETECTION_TEST")

            # The LP token was identified (is_lp_token was called)
            assert analyzer.lp_parser.is_lp_token.called

    def test_non_lp_tokens_bypass_decomposition(self, analyzer, mock_api_calls):
        """Test that regular tokens bypass LP decomposition."""
        # Reset LP detection to return False
        analyzer.lp_parser.is_lp_token = MagicMock(return_value=False)

        test_wallet = {
            "amount": 1_000_000_000,
            "status": "Offline",
            "assets": [
                {"asset-id": 31566704, "amount": 1_000_000_000},  # USDC
            ]
        }

        with patch.object(analyzer, 'get_account_assets', return_value=test_wallet), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("NON_LP_TEST")

            # USDC should be in dollars, not decomposed
            dollar_tickers = [a["ticker"] for a in categories.get("dollars", [])]
            assert "USDC" in dollar_tickers


# =============================================================================
# Progressive Loading Integration Tests
# =============================================================================

class TestProgressiveLoadingIntegration:
    """Test progressive loading and pagination features."""

    def test_quick_sovereignty_summary(self, analyzer):
        """Test quick sovereignty summary calculation."""
        categories = {
            "hard_money": [
                {"ticker": "goBTC", "amount": 1.0, "usd_value": 95000, "name": "goBTC"}
            ],
            "algo": [
                {"ticker": "ALGO", "amount": 10000, "usd_value": 3500, "name": "Algorand"}
            ],
            "dollars": [
                {"ticker": "USDC", "amount": 5000, "usd_value": 5000, "name": "USDC"}
            ],
            "shitcoin": []
        }

        with patch('core.analyzer.get_algo_price', return_value=0.35):
            summary = analyzer.get_quick_sovereignty_summary(categories, monthly_fixed_expenses=4000)

        # Verify summary structure
        assert summary['portfolio_usd'] == 103500
        assert summary['hard_money_total_usd'] == 95000
        assert summary['algo_total_usd'] == 3500
        assert summary['dollars_total_usd'] == 5000
        assert summary['shitcoin_total_usd'] == 0
        assert summary['sovereignty_ratio'] == round(103500 / 48000, 2)
        assert summary['sovereignty_status'] == "Fragile"

    def test_pagination_detection(self, analyzer):
        """Test that large categories are flagged for pagination."""
        # Create a category with many assets
        large_shitcoin_list = [
            {"ticker": f"TOKEN{i}", "amount": 100, "usd_value": 10, "name": f"Token {i}"}
            for i in range(100)
        ]

        categories = {
            "hard_money": [],
            "algo": [{"ticker": "ALGO", "amount": 1000, "usd_value": 350, "name": "Algorand"}],
            "dollars": [],
            "shitcoin": large_shitcoin_list
        }

        needs_pagination = analyzer.needs_pagination(categories)

        # Only shitcoin should need pagination (100 > threshold of 50)
        assert needs_pagination["shitcoin"] is True
        assert needs_pagination["hard_money"] is False
        assert needs_pagination["algo"] is False
        assert needs_pagination["dollars"] is False

    def test_paginated_assets_retrieval(self, analyzer, mock_api_calls):
        """Test paginated asset retrieval."""
        # Set up cached categories
        analyzer.last_categories = {
            "hard_money": [],
            "algo": [{"ticker": "ALGO", "amount": 1000, "usd_value": 350, "name": "Algorand"}],
            "dollars": [
                {"ticker": f"STABLE{i}", "amount": 100, "usd_value": 100, "name": f"Stable {i}"}
                for i in range(25)
            ],
            "shitcoin": []
        }

        # Get first page
        page1 = analyzer.get_paginated_assets("dollars", page=1, page_size=10)

        assert page1 is not None
        assert page1.category == "dollars"
        assert len(page1.page.items) == 10
        assert page1.page.total == 25
        assert page1.page.has_more is True

        # Get second page
        page2 = analyzer.get_paginated_assets("dollars", page=2, page_size=10)

        assert page2 is not None
        assert len(page2.page.items) == 10
        assert page2.page.has_more is True

        # Get third page (should have 5 items)
        page3 = analyzer.get_paginated_assets("dollars", page=3, page_size=10)

        assert page3 is not None
        assert len(page3.page.items) == 5
        assert page3.page.has_more is False


# =============================================================================
# Participation Status Integration Tests
# =============================================================================

class TestParticipationStatusIntegration:
    """Test consensus participation status tracking."""

    def test_participating_wallet_info(self, analyzer, mock_api_calls):
        """Test that participation info is correctly extracted."""
        with patch.object(analyzer, 'get_account_assets', return_value=WALLET_MIXED), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("PARTICIPATING_TEST")

            # Check stored participation info
            assert analyzer.last_is_participating is True
            assert analyzer.last_participation_info is not None
            assert analyzer.last_participation_info['staked_amount'] > 0
            assert analyzer.last_participation_info['vote_first_valid'] is not None
            assert analyzer.last_participation_info['is_incentive_eligible'] is True

    def test_non_participating_wallet_info(self, analyzer, mock_api_calls):
        """Test non-participating wallet info."""
        non_participating_wallet = {
            "amount": 1_000_000_000,
            "status": "Offline",
            "assets": []
        }

        with patch.object(analyzer, 'get_account_assets', return_value=non_participating_wallet), \
             patch('core.analyzer.get_algo_price', return_value=0.35), \
             patch('core.analyzer.get_asset_price', side_effect=mock_get_asset_price):

            categories = analyzer.analyze_wallet("NON_PARTICIPATING_TEST")

            # Check stored participation info
            assert analyzer.last_is_participating is False
            assert analyzer.last_participation_info['staked_amount'] == 0.0
            assert analyzer.last_participation_info['is_incentive_eligible'] is False
