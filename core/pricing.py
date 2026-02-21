"""
Pricing Module - Multi-source price fetching for cryptocurrency and precious metals.

This module provides price data from various public APIs including:
- CoinGecko (crypto prices)
- Coinbase (BTC spot price)
- Yahoo Finance (gold/silver futures)
- Vestige Labs (Algorand ASA prices)

Security Note:
    This module uses only PUBLIC APIs that require NO authentication.
    No API keys or secrets are used in this module.
    If authenticated APIs are needed in the future, use core.secrets.get_secret()
    to retrieve credentials securely.

Caching:
    All prices are cached using the centralized cache module (core/cache.py).
    Default TTLs:
    - Live prices: 60 seconds (configurable via CACHE_PRICE_TTL)
    - Reduces external API calls and improves response times
    - Hardcoded fallback prices are used when APIs fail

Cache Invalidation:
    Call invalidate_all_prices() to clear all cached prices manually.
    The cache will automatically expire based on TTL.
"""

import logging
import requests
import time
from typing import Optional
from .cache import get_cache, CacheCategory, CacheConfig

# Configure module logger
logger = logging.getLogger("core.pricing")

# Meld ASA IDs
MELD_GOLD_ASA = 246516580
MELD_SILVER_ASA = 246519683
GRAMS_PER_TROY_OZ = 31.1035

# Bitcoin ASA IDs
GOBTC_ASA = 386192725  # goBTC - wrapped Bitcoin on Algorand (native)
WBTC_ASA = 1058926737  # WBTC - Wormhole-bridged wrapped Bitcoin

# Coinbase API for BTC spot price (free, no auth needed)
COINBASE_BTC_URL = "https://api.coinbase.com/v2/prices/BTC-USD/spot"

# Cache TTL constants (in seconds)
PRICE_CACHE_TTL = CacheConfig.PRICE_LIVE_TTL  # Default: 60 seconds
MELD_CACHE_TTL_SECONDS = 300  # 5 minutes for Meld prices (less volatile)


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
        return 0.35  # Conservative fallback (Dec 2024/Jan 2025)

    # Bitcoin
    if t in ['BTC', 'WBTC', 'GOBTC', 'FGOBTC']:
        return 90000.0 # Approximate

    # Ethereum
    if t in ['ETH', 'WETH', 'GOETH', 'FGOETH']:
        return 3000.0 # Approximate

    # Meld Silver (1g) - Fallback, live price from Yahoo Finance is preferred
    if t == 'SILVER$':
        return 2.25  # ~$70/oz (Dec 2024)

    # Meld Gold (1g) - Fallback, live price from Yahoo Finance is preferred
    if t == 'GOLD$':
        return 144.75  # ~$4500/oz (Dec 2024)

    return None


def _fetch_price_with_cache(
    ticker: str,
    fetch_func,
    ttl: int = PRICE_CACHE_TTL
) -> Optional[float]:
    """
    Generic cached price fetching wrapper.

    Args:
        ticker: The ticker symbol for cache key
        fetch_func: Function to call if cache miss (no args)
        ttl: Cache TTL in seconds

    Returns:
        Cached or freshly fetched price
    """
    cache = get_cache()

    # Check cache first
    cached_price = cache.get_price(ticker)
    if cached_price is not None:
        return cached_price

    # Cache miss - fetch fresh price
    price = fetch_func()

    if price is not None:
        cache.set_price(ticker, price, ttl=ttl)

    return price


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
                logger.warning(f"Failed to fetch {coin_id} price after {max_retries} attempts: {e}")
                return None

            # Exponential backoff: 1s, 2s, 4s
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
    return None


def _fetch_coingecko_price_cached(coin_id: str, ticker: str) -> Optional[float]:
    """Fetch CoinGecko price with caching."""
    return _fetch_price_with_cache(
        ticker=ticker,
        fetch_func=lambda: _fetch_price(coin_id),
        ttl=PRICE_CACHE_TTL
    )


def get_algo_price() -> Optional[float]:
    """
    Fetch live ALGO price from CoinGecko API with caching and hardcoded fallback.

    Returns:
        ALGO price in USD, or hardcoded fallback if API fails
    """
    price = _fetch_coingecko_price_cached('algorand', 'ALGO')
    if price is None:
        logger.warning("CoinGecko ALGO price failed, using hardcoded fallback")
        return get_hardcoded_price('ALGO')
    return price


def get_bitcoin_price() -> Optional[float]:
    """
    Fetch BTC price from CoinGecko with caching (for goBTC valuation).

    Returns:
        BTC price in USD, or None if unavailable
    """
    return _fetch_coingecko_price_cached('bitcoin', 'BTC')


def get_ethereum_price() -> Optional[float]:
    """
    Fetch ETH price from CoinGecko with caching (for goETH valuation).

    Returns:
        ETH price in USD, or None if unavailable
    """
    return _fetch_coingecko_price_cached('ethereum', 'ETH')


def _fetch_coinbase_btc_price() -> Optional[float]:
    """Fetch BTC price from Coinbase API (internal, no caching)."""
    try:
        response = requests.get(COINBASE_BTC_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data['data']['amount'])
    except requests.exceptions.Timeout:
        logger.warning("Timeout fetching Bitcoin price from Coinbase")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Network error fetching Bitcoin price from Coinbase: {e}")
    except Exception as e:
        logger.warning(f"Error fetching Bitcoin price from Coinbase: {e}")
    return None


def get_bitcoin_spot_price() -> Optional[float]:
    """
    Fetch current Bitcoin spot price from Coinbase with caching.

    Uses Coinbase's free public API which requires no authentication.
    Falls back to CoinGecko, then hardcoded price.

    Returns:
        USD price per BTC, or fallback price if unavailable
    """
    cache = get_cache()

    # Check cache first
    cached_price = cache.get_price('BTC_SPOT')
    if cached_price is not None:
        return cached_price

    # Try Coinbase
    price = _fetch_coinbase_btc_price()

    if price is not None:
        cache.set_price('BTC_SPOT', price, ttl=PRICE_CACHE_TTL)
        return price

    # Fallback to CoinGecko
    cg_price = get_bitcoin_price()
    if cg_price:
        return cg_price

    # Last resort: hardcoded fallback
    return get_hardcoded_price('BTC')


def _fetch_vestige_price_raw(asset_id: int) -> Optional[float]:
    """Fetch price from Vestige API (internal, no caching)."""
    try:
        url = f"https://api.vestigelabs.org/assets/price?asset_ids={asset_id}&denominating_asset_id=31566704"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            price = data[0].get('price')
            if price is not None and price > 0:
                return price
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching Vestige price for asset {asset_id}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Network error fetching Vestige price for asset {asset_id}: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error fetching Vestige price for asset {asset_id}: {e}")
    return None


def fetch_vestige_price(asset_id: int) -> Optional[float]:
    """
    Fetch price from Vestige API with caching, denominated in USDC.

    Args:
        asset_id: The Algorand ASA ID

    Returns:
        Price in USD, or None if unavailable
    """
    cache = get_cache()
    cache_key = f"vestige_{asset_id}"

    # Check cache
    cached_price = cache.get_price(cache_key)
    if cached_price is not None:
        return cached_price

    # Fetch fresh
    price = _fetch_vestige_price_raw(asset_id)

    if price is not None:
        cache.set_price(cache_key, price, ttl=PRICE_CACHE_TTL)

    return price


def get_gobtc_price() -> Optional[float]:
    """
    Fetch current goBTC price from Vestige API with caching.

    goBTC (ASA 386192725) is wrapped Bitcoin on Algorand, maintaining
    a 1:1 peg with BTC. This fetches the on-chain trading price.

    Returns:
        USD price per goBTC token, or fallback price if unavailable
    """
    cache = get_cache()

    # Check cache first
    cached_price = cache.get_price('GOBTC')
    if cached_price is not None:
        return cached_price

    # Fetch from Vestige
    price = _fetch_vestige_price_raw(GOBTC_ASA)

    if price is not None and price > 0:
        cache.set_price('GOBTC', price, ttl=MELD_CACHE_TTL_SECONDS)
        return price

    # Fallback to BTC spot price (goBTC should track 1:1)
    spot_price = get_bitcoin_spot_price()
    if spot_price:
        logger.info(f"Using BTC spot price for goBTC: ${spot_price:,.2f} (Vestige fallback)")
        return spot_price

    # Last resort: hardcoded fallback
    return get_hardcoded_price('GOBTC')


def get_wbtc_price() -> Optional[float]:
    """
    Fetch current WBTC (Wormhole-bridged) price from Vestige API with caching.

    WBTC (ASA 1058926737) is wrapped Bitcoin bridged to Algorand via Wormhole,
    maintaining a 1:1 peg with BTC. This fetches the on-chain trading price.

    Note: WBTC has lower liquidity than goBTC (~$139K TVL vs larger goBTC pools).

    Returns:
        USD price per WBTC token, or fallback price if unavailable
    """
    cache = get_cache()

    # Check cache first
    cached_price = cache.get_price('WBTC')
    if cached_price is not None:
        return cached_price

    # Fetch from Vestige
    price = _fetch_vestige_price_raw(WBTC_ASA)

    if price is not None and price > 0:
        cache.set_price('WBTC', price, ttl=MELD_CACHE_TTL_SECONDS)
        return price

    # Fallback to BTC spot price (WBTC should track 1:1)
    spot_price = get_bitcoin_spot_price()
    if spot_price:
        logger.info(f"Using BTC spot price for WBTC: ${spot_price:,.2f} (Vestige fallback)")
        return spot_price

    # Last resort: hardcoded fallback
    return get_hardcoded_price('WBTC')


def _fetch_yahoo_finance_price(symbol: str) -> Optional[float]:
    """
    Fetch real-time commodity prices from Yahoo Finance.

    Args:
        symbol: Yahoo Finance symbol (e.g., 'GC=F' for gold futures, 'SI=F' for silver futures)

    Returns:
        Current market price in USD, or None on failure
    """
    max_retries = 3
    base_delay = 1

    for attempt in range(max_retries):
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Extract the regularMarketPrice from the response
            result = data.get('chart', {}).get('result', [])
            if result and len(result) > 0:
                price = result[0].get('meta', {}).get('regularMarketPrice')
                if price is not None and price > 0:
                    return float(price)

            return None
        except Exception as e:
            if attempt == max_retries - 1:
                logger.warning(f"Failed to fetch {symbol} price after {max_retries} attempts: {e}")
                return None

            # Exponential backoff: 1s, 2s, 4s
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
    return None


def _fetch_yahoo_price_cached(symbol: str, ticker: str) -> Optional[float]:
    """Fetch Yahoo Finance price with caching."""
    return _fetch_price_with_cache(
        ticker=ticker,
        fetch_func=lambda: _fetch_yahoo_finance_price(symbol),
        ttl=PRICE_CACHE_TTL
    )


def get_gold_price_per_oz() -> Optional[float]:
    """
    Fetch real-time Gold spot price (per troy oz) from Yahoo Finance with caching.
    Uses COMEX Gold Futures (GC=F) as the price source.

    Returns:
        Gold price per troy ounce in USD, or fallback on failure
    """
    price = _fetch_yahoo_price_cached('GC=F', 'GOLD_OZ')
    if price:
        return price

    # Fallback to hardcoded price if API fails
    logger.warning("Yahoo Finance gold price failed, using hardcoded fallback")
    return 4500.0  # Conservative fallback


def get_silver_price_per_oz() -> Optional[float]:
    """
    Fetch real-time Silver spot price (per troy oz) from Yahoo Finance with caching.
    Uses COMEX Silver Futures (SI=F) as the price source.

    Returns:
        Silver price per troy ounce in USD, or fallback on failure
    """
    price = _fetch_yahoo_price_cached('SI=F', 'SILVER_OZ')
    if price:
        return price

    # Fallback to hardcoded price if API fails
    logger.warning("Yahoo Finance silver price failed, using hardcoded fallback")
    return 70.0  # Conservative fallback


def get_gold_price() -> Optional[float]:
    """
    Fetch Gold price (per gram) from Yahoo Finance with caching.

    Returns:
        Gold price per gram in USD, or None on failure
    """
    oz_price = get_gold_price_per_oz()
    if oz_price:
        return oz_price / 31.1035  # Convert oz to gram
    return None


def get_silver_price() -> Optional[float]:
    """
    Fetch Silver price (per gram) from Yahoo Finance with caching.

    Returns:
        Silver price per gram in USD, or None on failure
    """
    oz_price = get_silver_price_per_oz()
    if oz_price:
        return oz_price / 31.1035  # Convert oz to gram
    return None


def _fetch_meld_price_from_vestige(asset_id: int) -> Optional[float]:
    """
    Fetch Meld token price from Vestige API.

    Tries the main API first (returns USDC price directly), then falls back
    to the free API endpoint.

    Args:
        asset_id: The ASA ID (MELD_GOLD_ASA or MELD_SILVER_ASA)

    Returns:
        Price in USD per token (per gram for Meld), or None on error
    """
    # Try the main Vestige API first
    price = _fetch_vestige_price_raw(asset_id)
    if price is not None and price > 0:
        return price

    # Fallback: try the free API endpoint
    try:
        url = f"https://free-api.vestige.fi/asset/{asset_id}/price"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # The free API returns price in ALGO
        price_in_algo = data.get('price')
        if price_in_algo is None or price_in_algo <= 0:
            return None

        # Convert to USD using current ALGO price
        algo_price = get_algo_price()
        if algo_price is None or algo_price <= 0:
            return None

        return price_in_algo * algo_price

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching Meld price from Vestige for ASA {asset_id}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Network error fetching Meld price from Vestige: {e}")
    except Exception as e:
        logger.warning(f"Error fetching Meld price from Vestige: {e}")
    return None


def get_meld_gold_price() -> Optional[float]:
    """
    Fetch Meld GOLD$ price from Vestige API with caching.

    Returns USD per gram. Uses centralized cache with configurable TTL.
    Falls back to implied spot price on error.

    Returns:
        Gold price per gram in USD
    """
    cache = get_cache()

    # Check cache
    cached_price = cache.get_price('MELD_GOLD')
    if cached_price is not None:
        return cached_price

    # Fetch fresh price
    price = _fetch_meld_price_from_vestige(MELD_GOLD_ASA)

    if price is not None and price > 0:
        cache.set_price('MELD_GOLD', price, ttl=MELD_CACHE_TTL_SECONDS)
        return price

    # Fallback: use implied price from spot
    spot_oz = get_gold_price_per_oz()
    if spot_oz:
        implied = spot_oz / GRAMS_PER_TROY_OZ
        logger.info(f"Using implied gold price: ${implied:.4f}/g (spot fallback)")
        return implied

    # Last resort: hardcoded fallback
    return get_hardcoded_price('GOLD$')


def get_meld_silver_price() -> Optional[float]:
    """
    Fetch Meld SILVER$ price from Vestige API with caching.

    Returns USD per gram. Uses centralized cache with configurable TTL.
    Falls back to implied spot price on error.

    Returns:
        Silver price per gram in USD
    """
    cache = get_cache()

    # Check cache
    cached_price = cache.get_price('MELD_SILVER')
    if cached_price is not None:
        return cached_price

    # Fetch fresh price
    price = _fetch_meld_price_from_vestige(MELD_SILVER_ASA)

    if price is not None and price > 0:
        cache.set_price('MELD_SILVER', price, ttl=MELD_CACHE_TTL_SECONDS)
        return price

    # Fallback: use implied price from spot
    spot_oz = get_silver_price_per_oz()
    if spot_oz:
        implied = spot_oz / GRAMS_PER_TROY_OZ
        logger.info(f"Using implied silver price: ${implied:.4f}/g (spot fallback)")
        return implied

    # Last resort: hardcoded fallback
    return get_hardcoded_price('SILVER$')


def get_asset_price(ticker: str, asset_id: Optional[int] = None) -> Optional[float]:
    """
    Router function that returns price for any ticker with caching.
    Prioritizes Vestige API if asset_id is provided.

    Args:
        ticker: Asset ticker symbol
        asset_id: Optional Algorand ASA ID for Vestige lookup

    Returns:
        Price in USD, or hardcoded fallback if unavailable
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
    if ticker_upper in ['ALGO', 'FALGO', 'XALGO']:
        return get_algo_price()

    # Bitcoin (goBTC, BTC, WBTC, and Folks wrapped)
    if ticker_upper in ['GOBTC', 'BTC', 'WBTC', 'FGOBTC']:
        return get_bitcoin_price()

    # Ethereum (goETH, ETH, WETH, and Folks wrapped)
    if ticker_upper in ['GOETH', 'ETH', 'WETH', 'FGOETH']:
        return get_ethereum_price()

    # Gold (Meld Gold is 1g)
    if ticker_upper in ['GOLD$', 'XAUT', 'PAXG']:
        return get_gold_price()

    # Silver (Meld Silver is 1g)
    if ticker_upper in ['SILVER$']:
        return get_silver_price()

    # ALPHA (Alpha Coin)
    if ticker_upper == 'ALPHA':
        return _fetch_coingecko_price_cached('alpha-finance', 'ALPHA')

    # LAST RESORT: Hardcoded prices to prevent "Shitcoin" classification on network failure
    return get_hardcoded_price(ticker)


# =============================================================================
# Cache Management Functions
# =============================================================================

def invalidate_all_prices() -> int:
    """
    Invalidate all cached prices.

    Returns:
        Number of cache entries invalidated
    """
    cache = get_cache()
    return cache.invalidate_prices()


def get_price_cache_stats() -> dict:
    """
    Get statistics about the price cache.

    Returns:
        Dictionary with cache statistics
    """
    cache = get_cache()
    stats = cache.get_stats()

    # Filter to just price-related stats
    return {
        "overall": stats.get("overall", {}),
        "price_live": stats.get("by_category", {}).get("price_live", {}),
        "size": stats.get("size", 0),
        "utilization": stats.get("utilization", 0)
    }
