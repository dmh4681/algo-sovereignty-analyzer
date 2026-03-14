import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app
from core.models import SovereigntyData

client = TestClient(app)

# Valid format Algorand test address (58 chars, base32: A-Z, 2-7)
# This is a properly formatted address for validation, mocked for actual calls
TEST_ADDRESS = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"  # 58 chars

# A real Algorand address with valid checksum for tests that don't mock validation
REAL_TEST_ADDRESS = "I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4"


# ---------------------------------------------------------------------------
# Input validation tests — wallet address
# ---------------------------------------------------------------------------

class TestAddressValidation:
    def test_short_address_returns_400(self):
        """Address shorter than 58 chars is rejected before hitting the analyzer."""
        response = client.post("/api/v1/analyze", json={"address": "TOOSHORT"})
        assert response.status_code == 400

    def test_long_address_returns_400(self):
        """Address longer than 58 chars is rejected."""
        response = client.post("/api/v1/analyze", json={"address": "A" * 59})
        assert response.status_code == 400

    def test_address_with_invalid_base32_chars_returns_400(self):
        """Address containing 0, 1, 8, or 9 (not valid base32) is rejected."""
        # Replace last char with an invalid base32 digit
        invalid_address = "A" * 57 + "0"  # '0' is not in base32 alphabet (A-Z, 2-7)
        response = client.post("/api/v1/analyze", json={"address": invalid_address})
        assert response.status_code == 400

    def test_address_with_lowercase_returns_400(self):
        """Lowercase address is rejected (Algorand addresses are uppercase base32)."""
        lowercase = "a" * 58
        response = client.post("/api/v1/analyze", json={"address": lowercase})
        assert response.status_code == 400

    def test_missing_address_returns_400(self):
        """Missing address field returns 400 validation error."""
        response = client.post("/api/v1/analyze", json={"monthly_fixed_expenses": 1000})
        assert response.status_code == 400

    def test_empty_address_returns_400(self):
        """Empty string address returns 400 validation error."""
        response = client.post("/api/v1/analyze", json={"address": ""})
        assert response.status_code == 400

    def test_address_with_spaces_returns_400(self):
        """Address with whitespace is rejected (spaces not in base32 alphabet)."""
        spaced = " " + "A" * 56 + " "  # 58 chars total but contains spaces
        response = client.post("/api/v1/analyze", json={"address": spaced})
        assert response.status_code == 400

    def test_invalid_address_error_format(self):
        """Error response uses the structured {error: {code, message}} format."""
        response = client.post("/api/v1/analyze", json={"address": "TOOSHORT"})
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]


# ---------------------------------------------------------------------------
# Input validation tests — monthly_fixed_expenses
# ---------------------------------------------------------------------------

class TestExpensesValidation:
    def test_negative_expenses_returns_400(self):
        """Negative monthly expenses are rejected."""
        response = client.post("/api/v1/analyze", json={
            "address": REAL_TEST_ADDRESS,
            "monthly_fixed_expenses": -500
        })
        assert response.status_code == 400

    def test_expenses_over_limit_returns_400(self):
        """Monthly expenses over 1,000,000 are rejected."""
        response = client.post("/api/v1/analyze", json={
            "address": REAL_TEST_ADDRESS,
            "monthly_fixed_expenses": 1_000_001
        })
        assert response.status_code == 400

    def test_zero_expenses_is_accepted(self):
        """Zero expenses is allowed (ge=0 constraint); analysis proceeds without sovereignty calc."""
        with patch("api.routes.validate_algorand_address"), \
             patch("api.schemas.validate_algorand_address", return_value=TEST_ADDRESS), \
             patch("api.routes.AlgorandSovereigntyAnalyzer") as MockAnalyzer:
            mock_instance = MockAnalyzer.return_value
            mock_instance.analyze_wallet.return_value = {
                "hard_money": [], "algo": [], "dollars": [], "shitcoin": []
            }
            mock_instance.last_is_participating = False
            mock_instance.last_hard_money_algo = 0.0
            mock_instance.last_participation_info = None

            response = client.post("/api/v1/analyze", json={
                "address": TEST_ADDRESS,
                "monthly_fixed_expenses": 0
            })
        assert response.status_code == 200
        assert response.json()["sovereignty_data"] is None


# ---------------------------------------------------------------------------
# History endpoint address validation
# ---------------------------------------------------------------------------

class TestHistoryAddressValidation:
    def test_history_short_address_returns_400(self):
        """GET /history/{address} with short address returns 400."""
        response = client.get("/api/v1/history/TOOSHORT")
        assert response.status_code == 400

    def test_history_address_invalid_chars_returns_400(self):
        """GET /history/{address} with non-base32 address returns 400."""
        invalid_address = "A" * 57 + "0"
        response = client.get(f"/api/v1/history/{invalid_address}")
        assert response.status_code == 400


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Algorand Sovereignty Analyzer API"}


@patch("api.routes.AlgorandSovereigntyAnalyzer")
@patch("api.routes.validate_algorand_address")
@patch("api.schemas.validate_algorand_address")
def test_analyze_wallet(mock_schema_validate, mock_validate, MockAnalyzer):
    # Skip address validation in both the schema and the route handler
    mock_schema_validate.return_value = TEST_ADDRESS
    mock_validate.return_value = None

    # Setup mock analyzer
    mock_instance = MockAnalyzer.return_value
    mock_instance.analyze_wallet.return_value = {
        "hard_money": [],
        "algo": [],
        "dollars": [],
        "shitcoin": []
    }
    mock_instance.last_is_participating = False
    mock_instance.last_hard_money_algo = 0.0
    mock_instance.last_participation_info = None  # Required for AnalysisResponse

    response = client.post("/api/v1/analyze", json={"address": TEST_ADDRESS})

    assert response.status_code == 200
    data = response.json()
    assert data["address"] == TEST_ADDRESS
    assert "categories" in data
    assert data["sovereignty_data"] is None


@patch("api.routes.AlgorandSovereigntyAnalyzer")
@patch("api.routes.validate_algorand_address")
@patch("api.schemas.validate_algorand_address")
def test_analyze_wallet_with_expenses(mock_schema_validate, mock_validate, MockAnalyzer):
    # Skip address validation in both the schema and the route handler
    mock_schema_validate.return_value = TEST_ADDRESS
    mock_validate.return_value = None

    # Setup mock analyzer
    mock_instance = MockAnalyzer.return_value
    mock_instance.analyze_wallet.return_value = {
        "hard_money": [],
        "algo": [{"ticker": "ALGO", "amount": 1000, "name": "Algorand"}],
        "dollars": [],
        "shitcoin": []
    }
    mock_instance.last_is_participating = True
    mock_instance.last_hard_money_algo = 1000.0
    mock_instance.last_participation_info = None  # Required for AnalysisResponse

    # Mock calculate_sovereignty_metrics
    mock_instance.calculate_sovereignty_metrics.return_value = SovereigntyData(
        monthly_fixed_expenses=1000,
        annual_fixed_expenses=12000,
        algo_price=0.2,
        portfolio_usd=200,
        sovereignty_ratio=0.02,
        sovereignty_status="Vulnerable ⚫",
        years_of_runway=0.0
    )

    response = client.post("/api/v1/analyze", json={
        "address": TEST_ADDRESS,
        "monthly_fixed_expenses": 1000
    })

    assert response.status_code == 200
    data = response.json()
    assert data["sovereignty_data"] is not None
    assert data["sovereignty_data"]["monthly_fixed_expenses"] == 1000
    assert data["sovereignty_data"]["sovereignty_status"] == "Vulnerable ⚫"

@patch("api.routes.AlgorandSovereigntyAnalyzer")
def test_get_classifications(MockAnalyzer):
    # Setup mock
    mock_instance = MockAnalyzer.return_value
    mock_instance.classifier.classifications = {
        "123": {"name": "Test Asset", "ticker": "TEST", "category": "hard_money"}
    }
    
    response = client.get("/api/v1/classifications")
    
    assert response.status_code == 200
    data = response.json()
    assert "123" in data
    assert data["123"]["name"] == "Test Asset"
