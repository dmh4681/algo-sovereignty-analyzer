"""
Tests for core/analyzer.py - Algorand wallet sovereignty analysis

These tests cover:
- Asset categorization (hard money, algo, dollars, shitcoin)
- Dust/NFT filtering
- Sovereignty score calculation
"""
import pytest
from unittest.mock import patch, MagicMock
from core.analyzer import AlgorandSovereigntyAnalyzer
from core.models import AssetCategory


class TestAlgorandSovereigntyAnalyzer:
    """Tests for the main analyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance with mocked node connection."""
        with patch('core.analyzer.requests.get'):
            return AlgorandSovereigntyAnalyzer(use_local_node=False)

    def test_initialization_public_node(self):
        """Analyzer should initialize with AlgoNode public API."""
        with patch('core.analyzer.requests.get'):
            analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
            assert "algonode.cloud" in analyzer.algod_address
            assert analyzer.algod_token == ""

    def test_initialization_local_node(self):
        """Analyzer should initialize with local node settings."""
        with patch('core.analyzer.requests.get'):
            analyzer = AlgorandSovereigntyAnalyzer(use_local_node=True)
            assert "127.0.0.1" in analyzer.algod_address
            assert analyzer.algod_token != ""

    def test_dust_threshold_constant(self, analyzer):
        """Dust threshold should be $10 USD."""
        assert analyzer.DUST_THRESHOLD_USD == 10.0

    def test_nft_max_amount_constant(self, analyzer):
        """NFT detection threshold should be 10 units."""
        assert analyzer.NFT_MAX_AMOUNT == 10


class TestDustAndNFTDetection:
    """Tests for _is_dust_or_nft method."""

    @pytest.fixture
    def analyzer(self):
        with patch('core.analyzer.requests.get'):
            return AlgorandSovereigntyAnalyzer(use_local_node=False)

    def test_nft_like_detection(self, analyzer):
        """Small integer holdings with no price should be flagged as NFT-like."""
        # Amount 1-10, integer, no price
        assert analyzer._is_dust_or_nft(
            amount=1,
            usd_value=0,
            price=None,
            name="CryptoKitty #123"
        ) is True

    def test_nft_amount_boundary(self, analyzer):
        """Amount at boundary (10) should still be detected as NFT."""
        assert analyzer._is_dust_or_nft(
            amount=10,
            usd_value=0,
            price=None,
            name="NFT"
        ) is True

    def test_not_nft_with_price(self, analyzer):
        """Small amounts WITH price data should not be NFT-like."""
        # Has price, so not NFT (might be dust though)
        assert analyzer._is_dust_or_nft(
            amount=1,
            usd_value=100,  # Significant value
            price=100.0,
            name="Token"
        ) is False

    def test_dust_with_reward_keyword(self, analyzer):
        """Tokens with 'reward' in name and low value should be dust."""
        assert analyzer._is_dust_or_nft(
            amount=1000,
            usd_value=5.0,  # Low value
            price=0.005,
            name="Reward Token Airdrop"
        ) is True

    def test_dust_very_low_value(self, analyzer):
        """Tokens worth less than $1 should be filtered as dust."""
        assert analyzer._is_dust_or_nft(
            amount=100,
            usd_value=0.50,
            price=0.005,
            name="Random Token"
        ) is True

    def test_not_dust_valuable_token(self, analyzer):
        """Valuable tokens should not be filtered."""
        assert analyzer._is_dust_or_nft(
            amount=10,
            usd_value=500,
            price=50.0,
            name="Valuable Asset"
        ) is False

    def test_large_amount_no_price(self, analyzer):
        """Large amounts without price should not be flagged as NFT."""
        # Amount > 10, not NFT-like (but no price, so won't have value)
        assert analyzer._is_dust_or_nft(
            amount=1000,
            usd_value=0,
            price=None,
            name="Unknown Token"
        ) is False


class TestAccountData:
    """Tests for account data fetching."""

    @pytest.fixture
    def analyzer(self):
        with patch('core.analyzer.requests.get'):
            return AlgorandSovereigntyAnalyzer(use_local_node=False)

    def test_get_account_assets_success(self, analyzer):
        """Should return account data on successful API call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'amount': 1000000000,  # 1000 ALGO
            'status': 'Online',
            'assets': []
        }
        mock_response.raise_for_status = MagicMock()

        with patch('core.analyzer.requests.get', return_value=mock_response):
            result = analyzer.get_account_assets("TEST_ADDRESS")

        assert result is not None
        assert result['amount'] == 1000000000
        assert result['status'] == 'Online'

    def test_get_account_assets_failure(self, analyzer):
        """Should return None on API failure."""
        import requests

        with patch('core.analyzer.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            result = analyzer.get_account_assets("TEST_ADDRESS")

        assert result is None

    def test_get_account_assets_timeout(self, analyzer):
        """Should handle timeout gracefully."""
        import requests

        with patch('core.analyzer.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Timeout")
            result = analyzer.get_account_assets("TEST_ADDRESS")

        assert result is None


class TestAssetDetails:
    """Tests for asset detail fetching."""

    @pytest.fixture
    def analyzer(self):
        with patch('core.analyzer.requests.get'):
            return AlgorandSovereigntyAnalyzer(use_local_node=False)

    def test_get_asset_details_success(self, analyzer):
        """Should return asset details on success."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'params': {
                'name': 'USDC',
                'unit-name': 'USDC',
                'decimals': 6
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch('core.analyzer.requests.get', return_value=mock_response):
            result = analyzer.get_asset_details(31566704)

        assert result is not None
        assert result['params']['name'] == 'USDC'
        assert result['params']['decimals'] == 6

    def test_get_asset_details_failure_silent(self, analyzer):
        """Should return None silently on failure."""
        import requests

        with patch('core.analyzer.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Error")
            result = analyzer.get_asset_details(12345)

        assert result is None


class TestWalletAnalysis:
    """Tests for the main analyze_wallet method."""

    @pytest.fixture
    def analyzer(self):
        with patch('core.analyzer.requests.get'):
            return AlgorandSovereigntyAnalyzer(use_local_node=False)

    def test_analyze_wallet_no_account_data(self, analyzer):
        """Should return None when account data cannot be fetched."""
        with patch.object(analyzer, 'get_account_assets', return_value=None):
            result = analyzer.analyze_wallet("INVALID_ADDRESS")

        assert result is None

    def test_analyze_wallet_basic_algo_only(self, analyzer):
        """Should categorize ALGO correctly."""
        mock_account = {
            'amount': 100_000_000,  # 100 ALGO (microAlgos)
            'status': 'Offline',
            'assets': []
        }

        with patch.object(analyzer, 'get_account_assets', return_value=mock_account):
            with patch('core.analyzer.get_algo_price', return_value=0.35):
                result = analyzer.analyze_wallet("TEST_ADDRESS")

        assert result is not None
        assert 'algo' in result
        assert len(result['algo']) == 1
        assert result['algo'][0]['ticker'] == 'ALGO'
        assert result['algo'][0]['amount'] == 100.0

    def test_analyze_wallet_participating_flag(self, analyzer):
        """Should note participation status in ALGO name."""
        mock_account = {
            'amount': 100_000_000,
            'status': 'Online',  # Participating
            'assets': []
        }

        with patch.object(analyzer, 'get_account_assets', return_value=mock_account):
            with patch('core.analyzer.get_algo_price', return_value=0.35):
                result = analyzer.analyze_wallet("TEST_ADDRESS")

        assert 'PARTICIPATING' in result['algo'][0]['name']

    def test_analyze_wallet_categories_initialized(self, analyzer):
        """Should always initialize all four categories."""
        mock_account = {
            'amount': 0,
            'status': 'Offline',
            'assets': []
        }

        with patch.object(analyzer, 'get_account_assets', return_value=mock_account):
            with patch('core.analyzer.get_algo_price', return_value=0.35):
                result = analyzer.analyze_wallet("TEST_ADDRESS")

        expected_categories = ['hard_money', 'algo', 'dollars', 'shitcoin']
        for cat in expected_categories:
            assert cat in result


class TestStateStorage:
    """Tests for analyzer state storage."""

    @pytest.fixture
    def analyzer(self):
        with patch('core.analyzer.requests.get'):
            return AlgorandSovereigntyAnalyzer(use_local_node=False)

    def test_state_initialized_empty(self, analyzer):
        """State should be initialized empty."""
        assert analyzer.last_categories == {}
        assert analyzer.last_address == ""
        assert analyzer.last_is_participating is False
        assert analyzer.last_hard_money_algo == 0.0
        assert analyzer.last_participation_info == {}
