import pytest
from core.classifier import AssetClassifier
from core.models import AssetCategory

@pytest.fixture
def classifier():
    return AssetClassifier()

def test_classifier_loading_empty():
    # Test with non-existent file
    classifier = AssetClassifier(classification_file="non_existent.csv")
    assert classifier.classifications == {}

def test_classifier_loading_default():
    # Test with default file (if it exists)
    import os
    if os.path.exists('data/asset_classification.csv'):
        classifier = AssetClassifier()
        assert len(classifier.classifications) > 0

def test_auto_classification_hard_money(classifier):
    """Hard money: Bitcoin, Gold, Silver ONLY"""
    # Bitcoin
    assert classifier.auto_classify_asset(1, "Bitcoin", "BTC") == AssetCategory.HARD_MONEY.value
    assert classifier.auto_classify_asset(2, "Wrapped Bitcoin", "WBTC") == AssetCategory.HARD_MONEY.value
    assert classifier.auto_classify_asset(3, "goBitcoin", "goBTC") == AssetCategory.HARD_MONEY.value
    # Gold
    assert classifier.auto_classify_asset(4, "Tether Gold", "XAUT") == AssetCategory.HARD_MONEY.value
    assert classifier.auto_classify_asset(5, "Pax Gold", "PAXG") == AssetCategory.HARD_MONEY.value
    assert classifier.auto_classify_asset(6, "Meld Gold", "GOLD$") == AssetCategory.HARD_MONEY.value
    # Silver
    assert classifier.auto_classify_asset(7, "Meld Silver", "SILVER$") == AssetCategory.HARD_MONEY.value

def test_auto_classification_dollars(classifier):
    """Dollars: Stablecoins (fiat-pegged)"""
    assert classifier.auto_classify_asset(10, "USDC", "USDC") == AssetCategory.DOLLARS.value
    assert classifier.auto_classify_asset(11, "Tether", "USDt") == AssetCategory.DOLLARS.value
    assert classifier.auto_classify_asset(12, "Tether", "USDT") == AssetCategory.DOLLARS.value
    assert classifier.auto_classify_asset(13, "DAI", "DAI") == AssetCategory.DOLLARS.value
    assert classifier.auto_classify_asset(14, "FUSD", "FUSD") == AssetCategory.DOLLARS.value

def test_auto_classification_shitcoin(classifier):
    """Shitcoins: ALGO and everything else"""
    # ALGO is now a shitcoin
    assert classifier.auto_classify_asset(0, "Algorand", "ALGO") == AssetCategory.SHITCOIN.value
    # Ethereum is a shitcoin
    assert classifier.auto_classify_asset(20, "Wrapped Ethereum", "goETH") == AssetCategory.SHITCOIN.value
    # LP tokens are shitcoins
    assert classifier.auto_classify_asset(21, "Tinyman Pool", "TMPOOL123") == AssetCategory.SHITCOIN.value
    # NFTs are shitcoins
    assert classifier.auto_classify_asset(22, "NFDomain", "NFD") == AssetCategory.SHITCOIN.value
    # Governance tokens are shitcoins
    assert classifier.auto_classify_asset(23, "Folks Finance", "FOLKS") == AssetCategory.SHITCOIN.value
    # Random tokens are shitcoins
    assert classifier.auto_classify_asset(30, "Meme Coin", "MEME") == AssetCategory.SHITCOIN.value
    assert classifier.auto_classify_asset(31, "Random Token", "RNDM") == AssetCategory.SHITCOIN.value

def test_manual_override(classifier):
    # Mock manual classifications
    classifier.classifications = {
        '999': {'name': 'Special Token', 'ticker': 'SPEC', 'category': 'hard_money'}
    }
    assert classifier.auto_classify_asset(999, "Special Token", "SPEC") == "hard_money"
