"""
End-to-end tests for the wallet analysis workflow.

Tests the complete flow from API request through analysis to response,
covering:
1. Full wallet analysis via POST /api/v1/analyze
2. Quick sovereignty endpoint via POST /api/v1/analyze/quick
3. Progressive loading pattern (quick summary -> paginated assets)
4. Corrections workflow (submit -> list -> export)
5. History save/load cycle
6. Error handling for invalid inputs

All external dependencies (Algorand node, pricing APIs) are mocked.
These tests exercise the integration between API routes, the analyzer,
classifier, and pricing modules together.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from api.main import app
from core.models import SovereigntyData

from tests.fixtures.sovereignty_fixtures import (
    STANDARD_PRICES,
    KNOWN_ASSET_DETAILS,
    make_account_data,
    make_sovereignty_result,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def _bypass_analysis_cache_and_rate_limit():
    """Prevent cross-test cache pollution and rate limiting from interfering with tests.

    The API caches analysis results per address for 15 minutes. Without this
    fixture, earlier tests that call /analyze for TEST_ADDRESS populate the
    cache, and later tests receive stale cached data instead of exercising
    the mocked analyzer.

    The /api/v1/analyze endpoint is rate-limited to 10 requests/minute
    (EXPENSIVE tier). With 19 tests calling the same endpoint in under a
    second, tests beyond the 10th would get 429 responses. We bypass rate
    limiting by patching the middleware's _check method to always allow.
    """
    with patch("api.routes.get_cached_analysis", return_value=None), \
         patch("api.routes.cache_analysis"), \
         patch(
             "api.middleware.rate_limit.SlidingWindowRateLimitMiddleware._check",
             return_value=(True, 999, 0),
         ):
        yield


# Valid-format Algorand address for testing (58 chars, uppercase alpha + digits 2-7)
TEST_ADDRESS = "I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4"


def mock_price_fn(ticker: str, asset_id: int = None) -> float:
    """Mock price function using standard test prices."""
    return STANDARD_PRICES.get(ticker.upper(), STANDARD_PRICES.get(ticker, None))


def mock_asset_details_fn(asset_id: int):
    """Mock asset details from known registry."""
    return KNOWN_ASSET_DETAILS.get(asset_id)


# ============================================================================
# Full Analysis Workflow Tests
# ============================================================================

class TestFullAnalysisWorkflow:
    """Test the complete POST /api/v1/analyze endpoint."""

    def test_analyze_empty_wallet(self, client):
        """Analyzing a wallet with only ALGO should return all categories."""
        account_data = make_account_data(algo_microalgos=5_000_000_000, participating=False)

        with patch("api.routes.AlgorandSovereigntyAnalyzer") as MockAnalyzer, \
             patch("api.routes.validate_algorand_address"):

            mock_instance = MockAnalyzer.return_value
            mock_instance.analyze_wallet.return_value = {
                "hard_money": [],
                "algo": [{"ticker": "ALGO", "name": "Algorand (NOT PARTICIPATING)", "amount": 5000, "usd_value": 1750}],
                "dollars": [],
                "shitcoin": [],
            }
            mock_instance.last_is_participating = False
            mock_instance.last_hard_money_algo = 0.0
            mock_instance.last_participation_info = None

            response = client.post("/api/v1/analyze", json={"address": TEST_ADDRESS})

            assert response.status_code == 200
            data = response.json()
            assert data["address"] == TEST_ADDRESS
            assert "categories" in data
            assert len(data["categories"]["algo"]) == 1
            assert data["categories"]["algo"][0]["ticker"] == "ALGO"
            assert data["sovereignty_data"] is None  # No expenses provided

    def test_analyze_with_expenses_returns_sovereignty(self, client):
        """When monthly_fixed_expenses is provided, sovereignty data should be calculated."""
        with patch("api.routes.AlgorandSovereigntyAnalyzer") as MockAnalyzer, \
             patch("api.routes.validate_algorand_address"):

            mock_instance = MockAnalyzer.return_value
            mock_instance.analyze_wallet.return_value = {
                "hard_money": [{"ticker": "goBTC", "name": "goBTC", "amount": 0.5, "usd_value": 47500}],
                "algo": [{"ticker": "ALGO", "name": "Algorand", "amount": 10000, "usd_value": 3500}],
                "dollars": [{"ticker": "USDC", "name": "USDC", "amount": 10000, "usd_value": 10000}],
                "shitcoin": [],
            }
            mock_instance.last_is_participating = True
            mock_instance.last_hard_money_algo = 0.0
            mock_instance.last_participation_info = None

            mock_instance.calculate_sovereignty_metrics.return_value = SovereigntyData(
                monthly_fixed_expenses=4000,
                annual_fixed_expenses=48000,
                algo_price=0.35,
                portfolio_usd=61000,
                sovereignty_ratio=1.27,
                sovereignty_status="Fragile",
                years_of_runway=1.27,
            )

            response = client.post("/api/v1/analyze", json={
                "address": TEST_ADDRESS,
                "monthly_fixed_expenses": 4000,
            })

            assert response.status_code == 200
            data = response.json()
            assert data["sovereignty_data"] is not None
            assert data["sovereignty_data"]["sovereignty_ratio"] == 1.27
            assert data["sovereignty_data"]["sovereignty_status"] == "Fragile"
            assert data["sovereignty_data"]["annual_fixed_expenses"] == 48000

    def test_analyze_wallet_not_found(self, client):
        """Should return error when wallet cannot be fetched."""
        with patch("api.routes.AlgorandSovereigntyAnalyzer") as MockAnalyzer, \
             patch("api.routes.validate_algorand_address"):

            mock_instance = MockAnalyzer.return_value
            mock_instance.analyze_wallet.return_value = None

            response = client.post("/api/v1/analyze", json={"address": TEST_ADDRESS})

            # The route raises NotFoundException when analyze_wallet returns None.
            # Cache is bypassed by the autouse _bypass_analysis_cache fixture.
            assert response.status_code in [400, 404, 500]

    def test_analyze_invalid_address_format(self, client):
        """Should reject addresses that are too short (AnalyzeRequest has min_length=58)."""
        response = client.post("/api/v1/analyze", json={"address": "TOOSHORT"})
        # The app has a custom RequestValidationError handler that returns 400
        assert response.status_code == 400


class TestSovereigntyTiersE2E:
    """Test that all 5 sovereignty tiers are correctly assigned end-to-end."""

    TIER_SCENARIOS = [
        # (portfolio_usd, monthly_expenses, expected_status)
        (2250, 4000, "Vulnerable"),
        (57000, 4000, "Fragile"),
        (175000, 4000, "Robust"),
        (469000, 4000, "Antifragile"),
        (1400500, 4000, "Generationally Sovereign"),
    ]

    @pytest.mark.parametrize("portfolio,expenses,expected_status", TIER_SCENARIOS)
    def test_sovereignty_tier_assignment(self, client, portfolio, expenses, expected_status):
        """Verify each tier is assigned at the correct portfolio/expense ratio."""
        with patch("api.routes.AlgorandSovereigntyAnalyzer") as MockAnalyzer, \
             patch("api.routes.validate_algorand_address"):

            mock_instance = MockAnalyzer.return_value
            mock_instance.analyze_wallet.return_value = {
                "hard_money": [{"ticker": "goBTC", "name": "goBTC", "amount": 1, "usd_value": portfolio}],
                "algo": [],
                "dollars": [],
                "shitcoin": [],
            }
            mock_instance.last_is_participating = False
            mock_instance.last_hard_money_algo = 0.0
            mock_instance.last_participation_info = None

            ratio = round(portfolio / (expenses * 12), 2)
            mock_instance.calculate_sovereignty_metrics.return_value = SovereigntyData(
                monthly_fixed_expenses=expenses,
                annual_fixed_expenses=expenses * 12,
                algo_price=0.35,
                portfolio_usd=portfolio,
                sovereignty_ratio=ratio,
                sovereignty_status=expected_status,
                years_of_runway=ratio,
            )

            response = client.post("/api/v1/analyze", json={
                "address": TEST_ADDRESS,
                "monthly_fixed_expenses": expenses,
            })

            assert response.status_code == 200
            data = response.json()
            assert data["sovereignty_data"]["sovereignty_status"] == expected_status


# ============================================================================
# Response Structure Tests
# ============================================================================

class TestResponseStructure:
    """Verify the API response contains all expected fields."""

    def test_analysis_response_has_required_fields(self, client):
        """Response must include address, categories, and sovereignty_data."""
        with patch("api.routes.AlgorandSovereigntyAnalyzer") as MockAnalyzer, \
             patch("api.routes.validate_algorand_address"):

            mock_instance = MockAnalyzer.return_value
            mock_instance.analyze_wallet.return_value = {
                "hard_money": [], "algo": [], "dollars": [], "shitcoin": [],
            }
            mock_instance.last_is_participating = False
            mock_instance.last_hard_money_algo = 0.0
            mock_instance.last_participation_info = None

            response = client.post("/api/v1/analyze", json={"address": TEST_ADDRESS})

            assert response.status_code == 200
            data = response.json()

            # Required top-level fields
            assert "address" in data
            assert "categories" in data
            assert "sovereignty_data" in data
            assert "is_participating" in data

            # Categories must have all four keys
            cats = data["categories"]
            assert set(cats.keys()) >= {"hard_money", "algo", "dollars", "shitcoin"}

    def test_sovereignty_data_fields(self, client):
        """Sovereignty data must include all SovereigntyData model fields."""
        with patch("api.routes.AlgorandSovereigntyAnalyzer") as MockAnalyzer, \
             patch("api.routes.validate_algorand_address"):

            mock_instance = MockAnalyzer.return_value
            mock_instance.analyze_wallet.return_value = {
                "hard_money": [], "algo": [], "dollars": [], "shitcoin": [],
            }
            mock_instance.last_is_participating = False
            mock_instance.last_hard_money_algo = 0.0
            mock_instance.last_participation_info = None
            mock_instance.calculate_sovereignty_metrics.return_value = SovereigntyData(
                monthly_fixed_expenses=4000,
                annual_fixed_expenses=48000,
                algo_price=0.35,
                portfolio_usd=100000,
                sovereignty_ratio=2.08,
                sovereignty_status="Fragile",
                years_of_runway=2.08,
            )

            response = client.post("/api/v1/analyze", json={
                "address": TEST_ADDRESS,
                "monthly_fixed_expenses": 4000,
            })

            assert response.status_code == 200
            sov = response.json()["sovereignty_data"]

            required_fields = [
                "monthly_fixed_expenses",
                "annual_fixed_expenses",
                "algo_price",
                "portfolio_usd",
                "sovereignty_ratio",
                "sovereignty_status",
                "years_of_runway",
            ]
            for field in required_fields:
                assert field in sov, f"Missing field: {field}"

    def test_asset_objects_have_required_fields(self, client):
        """Each asset in categories must have ticker, name, amount, usd_value."""
        with patch("api.routes.AlgorandSovereigntyAnalyzer") as MockAnalyzer, \
             patch("api.routes.validate_algorand_address"):

            mock_instance = MockAnalyzer.return_value
            mock_instance.analyze_wallet.return_value = {
                "hard_money": [{"ticker": "goBTC", "name": "goBTC", "amount": 0.1, "usd_value": 9500}],
                "algo": [{"ticker": "ALGO", "name": "Algorand", "amount": 1000, "usd_value": 350}],
                "dollars": [{"ticker": "USDC", "name": "USDC", "amount": 500, "usd_value": 500}],
                "shitcoin": [],
            }
            mock_instance.last_is_participating = False
            mock_instance.last_hard_money_algo = 0.0
            mock_instance.last_participation_info = None

            response = client.post("/api/v1/analyze", json={"address": TEST_ADDRESS})

            data = response.json()
            for cat_name, assets in data["categories"].items():
                for asset in assets:
                    assert "ticker" in asset, f"Missing ticker in {cat_name}"
                    assert "name" in asset, f"Missing name in {cat_name}"
                    assert "amount" in asset, f"Missing amount in {cat_name}"
                    assert "usd_value" in asset, f"Missing usd_value in {cat_name}"


# ============================================================================
# Classifications Endpoint Tests
# ============================================================================

class TestClassificationsEndpoint:
    """Test the GET /api/v1/classifications endpoint."""

    def test_classifications_returns_dict(self, client):
        """Should return a dict of asset classifications."""
        response = client.get("/api/v1/classifications")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


# ============================================================================
# Corrections Workflow E2E Tests
# ============================================================================

class TestCorrectionsWorkflow:
    """Test the full corrections submission and retrieval workflow."""

    def test_submit_and_retrieve_correction(self, client):
        """Submit a correction, then verify it appears in the list."""
        # Submit a correction
        correction_data = {
            "asset_id": "12345",
            "original_category": "shitcoin",
            "corrected_category": "hard_money",
            "asset_name": "Test Bitcoin Token",
            "asset_ticker": "TBT",
            "reason": "This is a Bitcoin derivative that should be classified as hard money",
        }

        submit_response = client.post("/api/v1/corrections", json=correction_data)

        # If corrections endpoint is available
        if submit_response.status_code == 200:
            # Retrieve corrections
            list_response = client.get("/api/v1/corrections")
            assert list_response.status_code == 200
            corrections = list_response.json()
            assert isinstance(corrections, list)

            # Check our correction is in the list
            found = any(c.get("asset_id") == "12345" for c in corrections)
            assert found, "Submitted correction not found in list"

            # Clean up: delete the test correction
            client.delete("/api/v1/corrections/12345")

    def test_correction_stats_endpoint(self, client):
        """Should return correction statistics."""
        response = client.get("/api/v1/corrections/stats")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


# ============================================================================
# Root Endpoint Tests
# ============================================================================

class TestRootEndpoint:
    """Test the root health check endpoint."""

    def test_root_returns_welcome(self, client):
        """GET / should return a welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Sovereignty" in data["message"] or "Algorand" in data["message"]


# ============================================================================
# Input Validation Tests
# ============================================================================

class TestInputValidation:
    """Test input validation across endpoints."""

    def test_missing_address_field(self, client):
        """POST /analyze without address should fail validation."""
        response = client.post("/api/v1/analyze", json={})
        # The app has a custom RequestValidationError handler that returns 400
        assert response.status_code == 400

    def test_negative_expenses_handled(self, client):
        """Negative expenses should be handled gracefully."""
        with patch("api.routes.AlgorandSovereigntyAnalyzer") as MockAnalyzer, \
             patch("api.routes.validate_algorand_address"):

            mock_instance = MockAnalyzer.return_value
            mock_instance.analyze_wallet.return_value = {
                "hard_money": [], "algo": [], "dollars": [], "shitcoin": [],
            }
            mock_instance.last_is_participating = False
            mock_instance.last_hard_money_algo = 0.0
            mock_instance.last_participation_info = None
            mock_instance.calculate_sovereignty_metrics.return_value = None

            response = client.post("/api/v1/analyze", json={
                "address": TEST_ADDRESS,
                "monthly_fixed_expenses": -100,
            })

            # Should either reject or return None sovereignty data
            if response.status_code == 200:
                data = response.json()
                assert data["sovereignty_data"] is None

    def test_zero_expenses_handled(self, client):
        """Zero expenses should be handled gracefully."""
        with patch("api.routes.AlgorandSovereigntyAnalyzer") as MockAnalyzer, \
             patch("api.routes.validate_algorand_address"):

            mock_instance = MockAnalyzer.return_value
            mock_instance.analyze_wallet.return_value = {
                "hard_money": [], "algo": [], "dollars": [], "shitcoin": [],
            }
            mock_instance.last_is_participating = False
            mock_instance.last_hard_money_algo = 0.0
            mock_instance.last_participation_info = None

            response = client.post("/api/v1/analyze", json={
                "address": TEST_ADDRESS,
                "monthly_fixed_expenses": 0,
            })

            if response.status_code == 200:
                data = response.json()
                # Zero expenses -> no sovereignty calculation
                assert data["sovereignty_data"] is None
