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

    # Verify 4 categories exist (hard money maximalist philosophy with separate ALGO)
    assert "hard_money" in data["categories"]
    assert "algo" in data["categories"]
    assert "dollars" in data["categories"]
    assert "shitcoin" in data["categories"]

    # Verify old categories are removed
    assert "productive" not in data["categories"]
    assert "nft" not in data["categories"]

    # ALGO should be in its own 'algo' category (not hard_money, not shitcoin)
    algo_asset = next((a for a in data["categories"]["algo"] if a["ticker"] == "ALGO"), None)
    assert algo_asset is not None, "ALGO should be in algo category"
    assert algo_asset["usd_value"] > 0, "ALGO should have USD value"

    # Hard money should only have BTC, gold, silver
    for asset in data["categories"]["hard_money"]:
        ticker = asset["ticker"].upper()
        is_btc = "BTC" in ticker
        is_gold = "GOLD" in ticker or ticker in ["XAUT", "PAXG"]
        is_silver = "SILVER" in ticker
        assert is_btc or is_gold or is_silver, f"Unexpected hard money asset: {ticker}"

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
    assert data["sovereignty_data"]["sovereignty_ratio"] >= 0
    assert "sovereignty_status" in data["sovereignty_data"]

def test_cache_hit():
    """Test that cached results are returned on repeat requests"""
    # First request
    response1 = client.post("/api/v1/analyze", json={"address": DYLAN_WALLET})
    assert response1.status_code == 200

    # Second request (should hit cache)
    response2 = client.post("/api/v1/analyze", json={"address": DYLAN_WALLET})
    assert response2.status_code == 200
    data2 = response2.json()

    assert data2["address"] == DYLAN_WALLET

def test_invalid_address():
    """Test error handling for invalid addresses"""
    response = client.post("/api/v1/analyze", json={"address": "INVALID"})
    assert response.status_code != 200

def test_classifications_endpoint():
    """Test that classifications endpoint returns expected data"""
    response = client.get("/api/v1/classifications")
    assert response.status_code == 200
    data = response.json()

    # Should have some data if CSV exists, or empty dict if not
    assert isinstance(data, dict)
