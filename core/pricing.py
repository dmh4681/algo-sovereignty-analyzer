import requests
import time
from typing import Optional

def _fetch_price(coin_id: str) -> Optional[float]:
    """Helper to fetch price from CoinGecko with retry logic"""
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data[coin_id]['usd']
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"⚠️  Failed to fetch {coin_id} price after {max_retries} attempts: {e}")
                return None
            
            # Exponential backoff: 1s, 2s, 4s
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
    return None

def get_algo_price() -> Optional[float]:
    """Fetch live ALGO price from CoinGecko API"""
    return _fetch_price('algorand')

def get_bitcoin_price() -> Optional[float]:
    """Fetch BTC price from CoinGecko (for goBTC valuation)"""
    return _fetch_price('bitcoin')

def get_ethereum_price() -> Optional[float]:
    """Fetch ETH price from CoinGecko (for goETH valuation)"""
    return _fetch_price('ethereum')

def get_asset_price(ticker: str) -> Optional[float]:
    """
    Router function that returns price for any ticker.
    Handles wrapped/derivative tokens (fALGO, xALGO, fUSDC, etc.)
    """
    ticker_upper = ticker.upper()

    # ALGO (including Folks Finance wrapped versions)
    if ticker_upper in ['ALGO', 'FALGO', 'XALGO']:
        return get_algo_price()

    # Bitcoin (goBTC, BTC, WBTC, and Folks wrapped)
    if ticker_upper in ['GOBTC', 'BTC', 'WBTC', 'FGOBTC']:
        return get_bitcoin_price()

    # Ethereum (goETH, ETH, WETH, and Folks wrapped)
    if ticker_upper in ['GOETH', 'ETH', 'WETH', 'FGOETH']:
        return get_ethereum_price()

    # Stablecoins - Assume peg for now (including Folks Finance wrapped)
    if ticker_upper in ['USDC', 'USDT', 'FUSDC', 'FUSDT', 'DAI', 'FUSD']:
        return 1.0

    # Gold/Silver (PAXG, XAUT) - Fetch if possible, but for now we might skip or add later
    if ticker_upper in ['PAXG', 'XAUT']:
        # Could add gold price fetching later
        return None

    return None

