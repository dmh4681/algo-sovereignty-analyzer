from fastapi.testclient import TestClient
from api.main import app
import pytest

client = TestClient(app)

# Dylan's wallet for real-world testing
DYLAN_WALLET = "I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4"

def test_analyze_dylan_wallet():
    """Test analysis of real wallet with known holdings"""
    response = client.post("/api/v1/analyze", json={"address": DYLAN_WALLET})
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "address" in data
    assert "categories" in data
    assert "hard_money_algo" in data
    
    # Verify Dylan's known holdings
    # Note: Values might fluctuate, but he definitely has ALGO
    assert data["hard_money_algo"] > 1000  
    assert data["is_participating"] == True  # Participating node
    
    # Verify categories exist
    assert "hard_money" in data["categories"]
    assert "productive" in data["categories"]
    
    # Verify pricing is happening (USD value should be > 0 for ALGO)
    algo_asset = next((a for a in data["categories"]["hard_money"] if a["ticker"] == "ALGO"), None)
    assert algo_asset is not None
    assert algo_asset["usd_value"] > 0

def test_analyze_with_expenses():
    """Test sovereignty calculation with monthly expenses"""
    response = client.post("/api/v1/analyze", json={
        "address": DYLAN_WALLET,
        "monthly_fixed_expenses": 4000
    })
    assert response.status_code == 200
    data = response.json()
    
    assert data["sovereignty_data"] is not None
    assert data["sovereignty_data"]["monthly_fixed_expenses"] == 4000
    assert data["sovereignty_data"]["sovereignty_ratio"] > 0
    assert "sovereignty_status" in data["sovereignty_data"]
    
def test_cache_hit():
    """Test that cached results are returned on repeat requests"""
    # First request
    response1 = client.post("/api/v1/analyze", json={"address": DYLAN_WALLET})
    assert response1.status_code == 200
    
    # Second request (should hit cache)
    # We can't easily check internal cache state from outside without mocking,
    # but we can verify it still returns correct data quickly
    response2 = client.post("/api/v1/analyze", json={"address": DYLAN_WALLET})
    assert response2.status_code == 200
    data2 = response2.json()
    
    assert data2["address"] == DYLAN_WALLET

def test_invalid_address():
    """Test error handling for invalid addresses"""
    # Algorand addresses are 58 chars. Short string should fail or return 404/500 depending on node response
    response = client.post("/api/v1/analyze", json={"address": "INVALID"})
    # The node might return 400 or 404 or 500. Our API wraps it in 500 if exception, or 404 if empty.
    assert response.status_code != 200

def test_classifications_endpoint():
    """Test that classifications endpoint returns expected data"""
    response = client.get("/api/v1/classifications")
    assert response.status_code == 200
    data = response.json()
    
    # Should have some data if CSV exists, or empty dict if not
    assert isinstance(data, dict)
