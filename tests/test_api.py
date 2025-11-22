from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app
from core.models import SovereigntyData

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Algorand Sovereignty Analyzer API"}

@patch("api.routes.AlgorandSovereigntyAnalyzer")
def test_analyze_wallet(MockAnalyzer):
    # Setup mock
    mock_instance = MockAnalyzer.return_value
    mock_instance.analyze_wallet.return_value = {
        "hard_money": [],
        "productive": [],
        "nft": [],
        "shitcoin": []
    }
    mock_instance.last_is_participating = False
    mock_instance.last_hard_money_algo = 0.0
    
    response = client.post("/api/v1/analyze", json={"address": "TEST_ADDRESS"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "TEST_ADDRESS"
    assert "categories" in data
    assert data["sovereignty_data"] is None

@patch("api.routes.AlgorandSovereigntyAnalyzer")
def test_analyze_wallet_with_expenses(MockAnalyzer):
    # Setup mock
    mock_instance = MockAnalyzer.return_value
    mock_instance.analyze_wallet.return_value = {
        "hard_money": [{"ticker": "ALGO", "amount": 1000, "name": "Algorand"}],
        "productive": [],
        "nft": [],
        "shitcoin": []
    }
    mock_instance.last_is_participating = True
    mock_instance.last_hard_money_algo = 1000.0
    
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
        "address": "TEST_ADDRESS",
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
