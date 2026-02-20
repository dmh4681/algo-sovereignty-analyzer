"""
Tests for sovereignty score calculation, tier assignment, and model integrity.

These tests verify:
- The sovereignty ratio formula: portfolio_usd / (monthly_expenses * 12)
- All 5 tier boundaries (Vulnerable, Fragile, Robust, Antifragile, Gen. Sovereign)
- The get_sovereignty_status() function with and without emojis
- Edge cases: zero expenses, huge portfolios, fractional ratios
- Portfolio value summation across all 4 categories
- SovereigntyData model validation
- Quick sovereignty summary structure
- Different wallet compositions producing correct tiers

Uses fixtures from tests/fixtures/sovereignty_fixtures.py for deterministic data.
"""

import pytest
from unittest.mock import patch, MagicMock

from core.models import (
    SovereigntyData,
    get_sovereignty_status,
    SOVEREIGNTY_THRESHOLDS,
    AssetCategory,
    QuickSovereigntyData,
)
from core.analyzer import AlgorandSovereigntyAnalyzer

from tests.fixtures.sovereignty_fixtures import (
    TIER_WALLETS,
    EXPECTED_RESULTS,
    BOUNDARY_CASES,
    EXPENSE_SCENARIOS,
    WALLET_BITCOIN_ONLY,
    WALLET_STABLECOINS_ONLY,
    WALLET_ALGO_ONLY,
    WALLET_GOLD_ONLY,
    WALLET_SHITCOINS_ONLY,
    WALLET_EMPTY,
    WALLET_DEFI_USER,
    make_wallet_with_portfolio,
    make_sovereignty_result,
    calculate_portfolio_total,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def analyzer():
    """Create analyzer with mocked Algorand node."""
    with patch("core.analyzer.requests.get"):
        return AlgorandSovereigntyAnalyzer(use_local_node=False)


# ============================================================================
# get_sovereignty_status() Tests
# ============================================================================

class TestGetSovereigntyStatus:
    """Test the centralized sovereignty status function."""

    def test_vulnerable_below_one(self):
        """Ratio < 1 should return Vulnerable."""
        assert get_sovereignty_status(0.0) == "Vulnerable"
        assert get_sovereignty_status(0.5) == "Vulnerable"
        assert get_sovereignty_status(0.99) == "Vulnerable"

    def test_fragile_one_to_three(self):
        """1 <= ratio < 3 should return Fragile."""
        assert get_sovereignty_status(1.0) == "Fragile"
        assert get_sovereignty_status(1.5) == "Fragile"
        assert get_sovereignty_status(2.99) == "Fragile"

    def test_robust_three_to_six(self):
        """3 <= ratio < 6 should return Robust."""
        assert get_sovereignty_status(3.0) == "Robust"
        assert get_sovereignty_status(4.5) == "Robust"
        assert get_sovereignty_status(5.99) == "Robust"

    def test_antifragile_six_to_twenty(self):
        """6 <= ratio < 20 should return Antifragile."""
        assert get_sovereignty_status(6.0) == "Antifragile"
        assert get_sovereignty_status(10.0) == "Antifragile"
        assert get_sovereignty_status(19.99) == "Antifragile"

    def test_generationally_sovereign_above_twenty(self):
        """ratio >= 20 should return Generationally Sovereign."""
        assert get_sovereignty_status(20.0) == "Generationally Sovereign"
        assert get_sovereignty_status(50.0) == "Generationally Sovereign"
        assert get_sovereignty_status(1000.0) == "Generationally Sovereign"

    def test_with_emoji(self):
        """include_emoji=True should append the appropriate emoji."""
        result = get_sovereignty_status(0.5, include_emoji=True)
        assert "Vulnerable" in result

        result = get_sovereignty_status(1.5, include_emoji=True)
        assert "Fragile" in result

        result = get_sovereignty_status(4.0, include_emoji=True)
        assert "Robust" in result

        result = get_sovereignty_status(10.0, include_emoji=True)
        assert "Antifragile" in result

        result = get_sovereignty_status(25.0, include_emoji=True)
        assert "Generationally Sovereign" in result

    def test_without_emoji(self):
        """include_emoji=False (default) should not include emoji characters."""
        # Emoji characters are multi-byte, status labels are ASCII
        result = get_sovereignty_status(4.0, include_emoji=False)
        assert result == "Robust"
        # No emoji should be present
        assert len(result) == len("Robust")

    def test_negative_ratio(self):
        """Negative ratio should still return Vulnerable."""
        assert get_sovereignty_status(-1.0) == "Vulnerable"
        assert get_sovereignty_status(-100.0) == "Vulnerable"


# ============================================================================
# SOVEREIGNTY_THRESHOLDS Tests
# ============================================================================

class TestSovereigntyThresholds:
    """Test the threshold constants."""

    def test_thresholds_are_descending(self):
        """Thresholds must be in descending order for correct matching."""
        values = [t[0] for t in SOVEREIGNTY_THRESHOLDS]
        assert values == sorted(values, reverse=True)

    def test_threshold_count(self):
        """Should have exactly 4 thresholds (Vulnerable is the default)."""
        assert len(SOVEREIGNTY_THRESHOLDS) == 4

    def test_threshold_values(self):
        """Verify the specific threshold values."""
        expected = [(20, "Generationally Sovereign"), (6, "Antifragile"), (3, "Robust"), (1, "Fragile")]
        assert SOVEREIGNTY_THRESHOLDS == expected


# ============================================================================
# Sovereignty Ratio Calculation Tests
# ============================================================================

class TestSovereigntyRatioCalculation:
    """Test the sovereignty ratio formula: portfolio / (monthly * 12)."""

    def test_basic_calculation(self, analyzer):
        """Test basic ratio calculation."""
        categories = {
            "hard_money": [{"ticker": "goBTC", "name": "goBTC", "amount": 1, "usd_value": 48000}],
            "algo": [],
            "dollars": [],
            "shitcoin": [],
        }

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)

        # 48000 / (4000 * 12) = 48000 / 48000 = 1.0
        assert metrics.sovereignty_ratio == 1.0
        assert "Fragile" in metrics.sovereignty_status

    def test_all_categories_contribute(self, analyzer):
        """All four categories should contribute to the portfolio total."""
        categories = {
            "hard_money": [{"ticker": "goBTC", "name": "goBTC", "amount": 1, "usd_value": 10000}],
            "algo": [{"ticker": "ALGO", "name": "Algorand", "amount": 1000, "usd_value": 5000}],
            "dollars": [{"ticker": "USDC", "name": "USDC", "amount": 3000, "usd_value": 3000}],
            "shitcoin": [{"ticker": "RNDM", "name": "Random", "amount": 100, "usd_value": 2000}],
        }

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)

        # Total = 10000 + 5000 + 3000 + 2000 = 20000
        assert metrics.portfolio_usd == 20000

    def test_zero_expenses_returns_none(self, analyzer):
        """Zero monthly expenses should return None (division by zero guard)."""
        categories = {"hard_money": [], "algo": [], "dollars": [], "shitcoin": []}
        result = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=0)
        assert result is None

    def test_negative_expenses_returns_none(self, analyzer):
        """Negative expenses should return None."""
        categories = {"hard_money": [], "algo": [], "dollars": [], "shitcoin": []}
        result = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=-500)
        assert result is None

    def test_empty_portfolio_returns_zero_ratio(self, analyzer):
        """Empty portfolio should give ratio of 0."""
        categories = {"hard_money": [], "algo": [], "dollars": [], "shitcoin": []}
        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)

        assert metrics.portfolio_usd == 0
        assert metrics.sovereignty_ratio == 0
        assert "Vulnerable" in metrics.sovereignty_status

    def test_annual_expenses_calculation(self, analyzer):
        """Annual expenses should be monthly * 12."""
        categories = {
            "hard_money": [{"ticker": "goBTC", "name": "goBTC", "amount": 1, "usd_value": 100000}],
            "algo": [],
            "dollars": [],
            "shitcoin": [],
        }

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=5000)

        assert metrics.monthly_fixed_expenses == 5000
        assert metrics.annual_fixed_expenses == 60000


# ============================================================================
# Tier-Specific Wallet Tests
# ============================================================================

class TestTierWallets:
    """Test that pre-built tier wallets produce the correct sovereignty status."""

    @pytest.mark.parametrize("tier_name,expected_status", [
        ("vulnerable", "Vulnerable"),
        ("fragile", "Fragile"),
        ("robust", "Robust"),
        ("antifragile", "Antifragile"),
        ("generationally_sovereign", "Generationally Sovereign"),
    ])
    def test_tier_wallet_status(self, analyzer, tier_name, expected_status):
        """Each tier wallet should produce the expected status at $4,000/mo expenses."""
        categories = TIER_WALLETS[tier_name]

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)

        assert expected_status in metrics.sovereignty_status

    @pytest.mark.parametrize("tier_name", list(TIER_WALLETS.keys()))
    def test_tier_wallet_portfolio_total(self, analyzer, tier_name):
        """Verify portfolio totals match expected values."""
        categories = TIER_WALLETS[tier_name]
        expected = EXPECTED_RESULTS[tier_name]

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)

        assert metrics.portfolio_usd == expected["portfolio_usd"]


# ============================================================================
# Boundary Case Tests
# ============================================================================

class TestBoundaryCases:
    """Test exact boundary values for tier transitions."""

    @pytest.mark.parametrize("portfolio,expenses,expected_ratio,expected_status", BOUNDARY_CASES)
    def test_boundary_values(self, analyzer, portfolio, expenses, expected_ratio, expected_status):
        """Verify tier assignment at exact boundary values."""
        categories = {
            "hard_money": [{"ticker": "goBTC", "name": "goBTC", "amount": 1, "usd_value": portfolio}] if portfolio > 0 else [],
            "algo": [],
            "dollars": [],
            "shitcoin": [],
        }

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=expenses)

        assert metrics.sovereignty_ratio == expected_ratio
        assert expected_status in metrics.sovereignty_status


# ============================================================================
# Wallet Composition Variant Tests
# ============================================================================

class TestWalletCompositions:
    """Test sovereignty calculation with different wallet compositions."""

    def test_bitcoin_only_wallet(self, analyzer):
        """All-Bitcoin wallet should work correctly."""
        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(WALLET_BITCOIN_ONLY, monthly_fixed_expenses=4000)

        assert metrics.portfolio_usd == 95000
        # 95000 / 48000 = 1.98 -> Fragile
        assert "Fragile" in metrics.sovereignty_status

    def test_stablecoins_only_wallet(self, analyzer):
        """All-stablecoin wallet should have full portfolio counted."""
        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(WALLET_STABLECOINS_ONLY, monthly_fixed_expenses=4000)

        assert metrics.portfolio_usd == 85000
        # 85000 / 48000 = 1.77 -> Fragile
        assert "Fragile" in metrics.sovereignty_status

    def test_algo_only_wallet(self, analyzer):
        """ALGO-only wallet should count toward portfolio."""
        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(WALLET_ALGO_ONLY, monthly_fixed_expenses=4000)

        assert metrics.portfolio_usd == 213000
        # 213000 / 48000 = 4.44 -> Robust
        assert "Robust" in metrics.sovereignty_status

    def test_gold_only_wallet(self, analyzer):
        """Gold-only wallet classified as hard money."""
        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(WALLET_GOLD_ONLY, monthly_fixed_expenses=4000)

        assert metrics.portfolio_usd == 102000
        # 102000 / 48000 = 2.12 -> Fragile
        assert "Fragile" in metrics.sovereignty_status

    def test_shitcoins_only_wallet(self, analyzer):
        """Shitcoin-only wallet still counted in portfolio."""
        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(WALLET_SHITCOINS_ONLY, monthly_fixed_expenses=4000)

        assert metrics.portfolio_usd == 850
        # 850 / 48000 = 0.02 -> Vulnerable
        assert "Vulnerable" in metrics.sovereignty_status

    def test_empty_wallet(self, analyzer):
        """Empty wallet should be Vulnerable with zero portfolio."""
        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(WALLET_EMPTY, monthly_fixed_expenses=4000)

        assert metrics.portfolio_usd == 0
        assert metrics.sovereignty_ratio == 0
        assert "Vulnerable" in metrics.sovereignty_status

    def test_defi_user_wallet(self, analyzer):
        """Realistic DeFi user wallet with liquid staking and wrapped assets."""
        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(WALLET_DEFI_USER, monthly_fixed_expenses=4000)

        expected_total = calculate_portfolio_total(WALLET_DEFI_USER)
        assert metrics.portfolio_usd == expected_total


# ============================================================================
# Expense Scenario Tests
# ============================================================================

class TestExpenseScenarios:
    """Test the same portfolio at different expense levels."""

    PORTFOLIO_100K = make_wallet_with_portfolio(100000)

    @pytest.mark.parametrize("scenario,monthly", [
        ("low", 1000),
        ("modest", 2500),
        ("average", 4000),
        ("comfort", 6000),
        ("high", 10000),
    ])
    def test_same_portfolio_different_expenses(self, analyzer, scenario, monthly):
        """Same portfolio value should produce different tiers at different expenses."""
        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(self.PORTFOLIO_100K, monthly_fixed_expenses=monthly)

        expected = make_sovereignty_result(100000, monthly)
        assert metrics.sovereignty_ratio == expected["sovereignty_ratio"]
        assert expected["sovereignty_status"] in metrics.sovereignty_status


# ============================================================================
# Dynamic Wallet Builder Tests
# ============================================================================

class TestWalletBuilder:
    """Test the make_wallet_with_portfolio helper."""

    def test_default_allocation(self):
        """Default allocation should put everything in hard_money."""
        wallet = make_wallet_with_portfolio(100000)
        total = calculate_portfolio_total(wallet)
        assert total == 100000
        assert len(wallet["hard_money"]) == 1
        assert len(wallet["algo"]) == 0

    def test_split_allocation(self):
        """Split allocation should distribute correctly."""
        wallet = make_wallet_with_portfolio(100000, {
            "hard_money": 0.5,
            "algo": 0.2,
            "dollars": 0.2,
            "shitcoin": 0.1,
        })

        assert len(wallet["hard_money"]) == 1
        assert len(wallet["algo"]) == 1
        assert len(wallet["dollars"]) == 1
        assert len(wallet["shitcoin"]) == 1

        # Check values are approximately correct (rounding may vary)
        assert abs(wallet["hard_money"][0]["usd_value"] - 50000) < 1
        assert abs(wallet["algo"][0]["usd_value"] - 20000) < 1
        assert abs(wallet["dollars"][0]["usd_value"] - 20000) < 1
        assert abs(wallet["shitcoin"][0]["usd_value"] - 10000) < 1

    def test_zero_portfolio(self):
        """Zero portfolio should produce empty categories."""
        wallet = make_wallet_with_portfolio(0)
        total = calculate_portfolio_total(wallet)
        assert total == 0


# ============================================================================
# SovereigntyData Model Tests
# ============================================================================

class TestSovereigntyDataModel:
    """Test the Pydantic SovereigntyData model."""

    def test_model_creation(self):
        """Should create a valid SovereigntyData instance."""
        data = SovereigntyData(
            monthly_fixed_expenses=4000,
            annual_fixed_expenses=48000,
            algo_price=0.35,
            portfolio_usd=100000,
            sovereignty_ratio=2.08,
            sovereignty_status="Fragile",
            years_of_runway=2.08,
        )
        assert data.monthly_fixed_expenses == 4000
        assert data.sovereignty_status == "Fragile"

    def test_model_serialization(self):
        """Should serialize to dict correctly."""
        data = SovereigntyData(
            monthly_fixed_expenses=4000,
            annual_fixed_expenses=48000,
            algo_price=0.35,
            portfolio_usd=100000,
            sovereignty_ratio=2.08,
            sovereignty_status="Fragile",
            years_of_runway=2.08,
        )
        d = data.model_dump()
        assert isinstance(d, dict)
        assert d["sovereignty_ratio"] == 2.08

    def test_model_json_round_trip(self):
        """Should survive JSON serialization and deserialization."""
        data = SovereigntyData(
            monthly_fixed_expenses=4000,
            annual_fixed_expenses=48000,
            algo_price=0.35,
            portfolio_usd=100000,
            sovereignty_ratio=2.08,
            sovereignty_status="Fragile",
            years_of_runway=2.08,
        )
        json_str = data.model_dump_json()
        restored = SovereigntyData.model_validate_json(json_str)
        assert restored == data


# ============================================================================
# QuickSovereigntyData Tests
# ============================================================================

class TestQuickSovereigntySummary:
    """Test the quick sovereignty summary for progressive loading."""

    def test_quick_summary_structure(self, analyzer):
        """Quick summary should have all required fields."""
        categories = {
            "hard_money": [{"ticker": "goBTC", "name": "goBTC", "amount": 1, "usd_value": 95000}],
            "algo": [{"ticker": "ALGO", "name": "Algorand", "amount": 10000, "usd_value": 3500}],
            "dollars": [{"ticker": "USDC", "name": "USDC", "amount": 5000, "usd_value": 5000}],
            "shitcoin": [{"ticker": "RNDM", "name": "Random", "amount": 100, "usd_value": 100}],
        }

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            summary = analyzer.get_quick_sovereignty_summary(categories, monthly_fixed_expenses=4000)

        assert "portfolio_usd" in summary
        assert "sovereignty_ratio" in summary
        assert "sovereignty_status" in summary
        assert "hard_money_total_usd" in summary
        assert "algo_total_usd" in summary
        assert "dollars_total_usd" in summary
        assert "shitcoin_total_usd" in summary
        assert "asset_counts" in summary

    def test_quick_summary_category_totals(self, analyzer):
        """Quick summary should compute per-category USD totals."""
        categories = {
            "hard_money": [
                {"ticker": "goBTC", "name": "goBTC", "amount": 1, "usd_value": 50000},
                {"ticker": "GOLD$", "name": "Gold", "amount": 100, "usd_value": 8500},
            ],
            "algo": [{"ticker": "ALGO", "name": "Algorand", "amount": 5000, "usd_value": 1750}],
            "dollars": [],
            "shitcoin": [],
        }

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            summary = analyzer.get_quick_sovereignty_summary(categories, monthly_fixed_expenses=4000)

        assert summary["hard_money_total_usd"] == 58500
        assert summary["algo_total_usd"] == 1750
        assert summary["dollars_total_usd"] == 0
        assert summary["shitcoin_total_usd"] == 0
        assert summary["portfolio_usd"] == 60250

    def test_quick_summary_asset_counts(self, analyzer):
        """Quick summary should count assets per category."""
        categories = {
            "hard_money": [
                {"ticker": "goBTC", "name": "goBTC", "amount": 1, "usd_value": 50000},
                {"ticker": "GOLD$", "name": "Gold", "amount": 100, "usd_value": 8500},
            ],
            "algo": [{"ticker": "ALGO", "name": "Algorand", "amount": 5000, "usd_value": 1750}],
            "dollars": [
                {"ticker": "USDC", "name": "USDC", "amount": 1000, "usd_value": 1000},
                {"ticker": "DAI", "name": "DAI", "amount": 500, "usd_value": 500},
                {"ticker": "USDt", "name": "Tether", "amount": 2000, "usd_value": 2000},
            ],
            "shitcoin": [],
        }

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            summary = analyzer.get_quick_sovereignty_summary(categories, monthly_fixed_expenses=4000)

        assert summary["asset_counts"]["hard_money"] == 2
        assert summary["asset_counts"]["algo"] == 1
        assert summary["asset_counts"]["dollars"] == 3
        assert summary["asset_counts"]["shitcoin"] == 0


# ============================================================================
# Large Number / Precision Tests
# ============================================================================

class TestLargeNumbers:
    """Test handling of very large and very small values."""

    def test_whale_portfolio(self, analyzer):
        """Test with a very large portfolio (whale)."""
        categories = {
            "hard_money": [{"ticker": "goBTC", "name": "goBTC", "amount": 100, "usd_value": 9_500_000_000}],
            "algo": [],
            "dollars": [],
            "shitcoin": [],
        }

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)

        assert metrics.portfolio_usd == 9_500_000_000
        assert metrics.sovereignty_ratio > 0
        assert "Generationally Sovereign" in metrics.sovereignty_status

    def test_very_small_expenses(self, analyzer):
        """Test with minimal expenses ($1/month)."""
        categories = {
            "hard_money": [{"ticker": "goBTC", "name": "goBTC", "amount": 0.001, "usd_value": 95}],
            "algo": [],
            "dollars": [],
            "shitcoin": [],
        }

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=1)

        # 95 / 12 = 7.92 -> Antifragile
        assert metrics.sovereignty_ratio == 7.92
        assert "Antifragile" in metrics.sovereignty_status

    def test_very_small_portfolio(self, analyzer):
        """Test with a tiny portfolio value."""
        categories = {
            "hard_money": [],
            "algo": [],
            "dollars": [{"ticker": "USDC", "name": "USDC", "amount": 0.01, "usd_value": 0.01}],
            "shitcoin": [],
        }

        with patch("core.analyzer.get_algo_price", return_value=0.35):
            metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_fixed_expenses=4000)

        assert metrics.portfolio_usd == 0.01
        assert metrics.sovereignty_ratio == 0.0
        assert "Vulnerable" in metrics.sovereignty_status


# ============================================================================
# AssetCategory Enum Tests
# ============================================================================

class TestAssetCategoryEnum:
    """Test the AssetCategory enum values."""

    def test_all_categories_defined(self):
        """All four categories should be defined."""
        assert AssetCategory.HARD_MONEY.value == "hard_money"
        assert AssetCategory.ALGO.value == "algo"
        assert AssetCategory.DOLLARS.value == "dollars"
        assert AssetCategory.SHITCOIN.value == "shitcoin"

    def test_category_count(self):
        """Should have exactly 4 categories."""
        assert len(AssetCategory) == 4
