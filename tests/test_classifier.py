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
    assert classifier.auto_classify_asset(1, "Bitcoin", "BTC") == AssetCategory.HARD_MONEY.value
    assert classifier.auto_classify_asset(2, "Wrapped Bitcoin", "WBTC") == AssetCategory.HARD_MONEY.value
    assert classifier.auto_classify_asset(3, "goBitcoin", "goBTC") == AssetCategory.HARD_MONEY.value
    assert classifier.auto_classify_asset(4, "Tether Gold", "XAUT") == AssetCategory.HARD_MONEY.value

def test_auto_classification_productive(classifier):
    assert classifier.auto_classify_asset(10, "USDC", "USDC") == AssetCategory.PRODUCTIVE.value
    assert classifier.auto_classify_asset(11, "Tinyman Pool", "TMPOOL123") == AssetCategory.PRODUCTIVE.value
    assert classifier.auto_classify_asset(12, "Staked ALGO", "STALGO") == AssetCategory.PRODUCTIVE.value
    assert classifier.auto_classify_asset(13, "Governance ALGO", "GALGO") == AssetCategory.PRODUCTIVE.value

def test_auto_classification_nft(classifier):
    assert classifier.auto_classify_asset(20, "NFDomain", "NFD") == AssetCategory.NFT.value
    assert classifier.auto_classify_asset(21, "Lofty", "VL012345") == AssetCategory.NFT.value
    assert classifier.auto_classify_asset(22, "AFK Elephant", "AFK") == AssetCategory.NFT.value
    
    # Heuristic NFT check
    assert classifier.auto_classify_asset(23, "Unknown NFT", "AB12345") == AssetCategory.NFT.value

def test_auto_classification_shitcoin(classifier):
    assert classifier.auto_classify_asset(30, "Meme Coin", "MEME") == "shitcoin"
    assert classifier.auto_classify_asset(31, "Random Token", "RNDM") == "shitcoin"

def test_manual_override(classifier):
    # Mock manual classifications
    classifier.classifications = {
        '999': {'name': 'Special Token', 'ticker': 'SPEC', 'category': 'hard_money'}
    }
    assert classifier.auto_classify_asset(999, "Special Token", "SPEC") == "hard_money"
