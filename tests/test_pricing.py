import pytest
from unittest.mock import patch, MagicMock
from core.pricing import get_algo_price

def test_get_algo_price_success():
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {'algorand': {'usd': 1.23}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        price = get_algo_price()
        assert price == 1.23
        mock_get.assert_called_once()

def test_get_algo_price_retry_success():
    with patch('requests.get') as mock_get:
        mock_response_fail = MagicMock()
        mock_response_fail.raise_for_status.side_effect = Exception("API Error")
        
        mock_response_success = MagicMock()
        mock_response_success.json.return_value = {'algorand': {'usd': 1.23}}
        mock_response_success.raise_for_status.return_value = None
        
        # Fail twice, then succeed
        mock_get.side_effect = [Exception("Conn Error"), Exception("Timeout"), mock_response_success]
        
        with patch('time.sleep') as mock_sleep: # Don't actually sleep
            price = get_algo_price()
            assert price == 1.23
            assert mock_get.call_count == 3

def test_get_algo_price_failure():
    """When CoinGecko fails, get_algo_price should return hardcoded fallback (0.35)."""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Persistent Error")

        with patch('time.sleep') as mock_sleep:
            price = get_algo_price()
            # Now uses hardcoded fallback instead of returning None
            assert price == 0.35
            assert mock_get.call_count == 3
