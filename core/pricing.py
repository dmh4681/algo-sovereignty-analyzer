import requests
import time
from typing import Optional

def get_hardcoded_price(ticker: str) -> Optional[float]:
    """
    Returns a conservative hardcoded price for critical assets
    to ensure the app remains functional during API outages.
    """
    t = ticker.upper()
    
    # Stablecoins
    if t in ['USDC', 'USDT', 'DAI', 'STBL', 'FUSDC', 'FUSDT', 'FUSD']:
        return 1.0
        
    # ALGO & Derivatives
    if t in ['ALGO', 'FALGO', 'XALGO']:
        return 0.15  # Conservative floor price
        
    # Bitcoin
    if t in ['BTC', 'WBTC', 'GOBTC', 'FGOBTC']:
        return 90000.0 # Approximate
        
    # Ethereum
    if t in ['ETH', 'WETH', 'GOETH', 'FGOETH']:
        return 3000.0 # Approximate
        
    # Meld Silver (1g)
    if t == 'SILVER$':
        return 0.90
        
    # Meld Gold (1g)
    if t == 'GOLD$':
        return 80.0
        
    return None

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

def get_gold_price() -> Optional[float]:
    """Fetch Gold price (per gram) using PAXG (per oz) as proxy"""
    paxg_price = _fetch_price('pax-gold')
    if paxg_price:
        return paxg_price / 31.1035  # Convert oz to gram
    return None

def get_silver_price() -> Optional[float]:
    """Fetch Silver price (per gram) using KAG (per oz) as proxy"""
    kag_price = _fetch_price('kinesis-silver')
    if kag_price:
        return kag_price / 31.1035  # Convert oz to gram
    return None

def fetch_vestige_price(asset_id: int) -> Optional[float]:
    """Fetch price from Vestige API denominated in USDC"""
    try:
        # Vestige API endpoint for asset price denominated in USDC (31566704)
        url = f"https://api.vestigelabs.org/assets/price?asset_ids={asset_id}&denominating_asset_id=31566704"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return data[0].get('price')
    except Exception as e:
        print(f"⚠️  Failed to fetch Vestige price for asset {asset_id}: {e}")
    return None

def get_asset_price(ticker: str, asset_id: Optional[int] = None) -> Optional[float]:
    """
    Router function that returns price for any ticker.
    Prioritizes Vestige API if asset_id is provided.
    """
    ticker_upper = ticker.upper()

    # Stablecoins - Assume peg for now (Optimization: avoid API call)
    if ticker_upper in ['USDC', 'USDT', 'FUSDC', 'FUSDT', 'DAI', 'FUSD', 'STBL']:
        return 1.0

    # If we have an asset ID, try Vestige first (covers almost all ASAs)
    if asset_id is not None and asset_id >= 0:
        price = fetch_vestige_price(asset_id)
        if price is not None:
            return price

    # Fallback to CoinGecko/Proxies for legacy or missing ID support
    
    # ALGO (including Folks Finance wrapped versions)
    # Note: We keep FALGO/XALGO here as fallback if asset_id resolution fails
    if ticker_upper in ['ALGO', 'FALGO', 'XALGO']:
        return get_algo_price()

    # Bitcoin (goBTC, BTC, WBTC, and Folks wrapped)
    if ticker_upper in ['GOBTC', 'BTC', 'WBTC', 'FGOBTC']:
        return get_bitcoin_price()

    # Ethereum (goETH, ETH, WETH, and Folks wrapped)
    if ticker_upper in ['GOETH', 'ETH', 'WETH', 'FGOETH']:
        return get_ethereum_price()

    # Stablecoins - Assume peg for now (Optimization: avoid API call)
    # Note: We keep FUSDC/FUSDT/FUSD here as fallback if asset_id resolution fails
    if ticker_upper in ['USDC', 'USDT', 'DAI', 'STBL', 'FUSDC', 'FUSDT', 'FUSD']:
        return 1.0

    # Gold (Meld Gold is 1g)
    if ticker_upper in ['GOLD$', 'XAUT', 'PAXG']:
        return get_gold_price()

    # Silver (Meld Silver is 1g)
    if ticker_upper in ['SILVER$']:
        return get_silver_price()

    # ALPHA (Alpha Coin)
    if ticker_upper == 'ALPHA':
        return _fetch_price('alpha-finance')

    # LAST RESORT: Hardcoded prices to prevent "Shitcoin" classification on network failure
    return get_hardcoded_price(ticker)

