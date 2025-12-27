"""
Meld Pricing Module - Additions for core/pricing.py
Add these functions to your existing pricing.py file
"""

import httpx
from typing import Optional
from functools import lru_cache
from datetime import datetime, timedelta

# Meld ASA IDs on Algorand Mainnet
MELD_GOLD_ASA = 246516580   # GOLD$ - 1 token = 1 gram of gold
MELD_SILVER_ASA = 246519683  # SILVER$ - 1 token = 1 gram of silver

# Conversion constant
GRAMS_PER_TROY_OZ = 31.1035

# Vestige API for Algorand ASA prices
VESTIGE_API_URL = "https://free-api.vestige.fi/asset/{asa_id}/price"

# Cache for Meld prices (5 minute TTL)
_meld_price_cache: dict = {}
_cache_ttl = timedelta(minutes=5)


def get_vestige_price(asa_id: int) -> Optional[float]:
    """
    Fetch current USD price for an ASA from Vestige API.
    
    Args:
        asa_id: Algorand Standard Asset ID
        
    Returns:
        USD price per token, or None if unavailable
    """
    try:
        url = VESTIGE_API_URL.format(asa_id=asa_id)
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        # Vestige returns price in USD
        return float(data.get('price', 0))
    except Exception as e:
        print(f"Error fetching Vestige price for ASA {asa_id}: {e}")
        return None


def get_meld_gold_price() -> Optional[float]:
    """
    Get current Meld GOLD$ price (USD per gram).
    
    Returns:
        USD price per GOLD$ token (1 gram), or None if unavailable
    """
    cache_key = 'meld_gold'
    
    # Check cache
    if cache_key in _meld_price_cache:
        price, timestamp = _meld_price_cache[cache_key]
        if datetime.now() - timestamp < _cache_ttl:
            return price
    
    price = get_vestige_price(MELD_GOLD_ASA)
    
    if price is not None:
        _meld_price_cache[cache_key] = (price, datetime.now())
    
    return price


def get_meld_silver_price() -> Optional[float]:
    """
    Get current Meld SILVER$ price (USD per gram).
    
    Returns:
        USD price per SILVER$ token (1 gram), or None if unavailable
    """
    cache_key = 'meld_silver'
    
    # Check cache
    if cache_key in _meld_price_cache:
        price, timestamp = _meld_price_cache[cache_key]
        if datetime.now() - timestamp < _cache_ttl:
            return price
    
    price = get_vestige_price(MELD_SILVER_ASA)
    
    if price is not None:
        _meld_price_cache[cache_key] = (price, datetime.now())
    
    return price


def get_meld_prices() -> dict:
    """
    Get both Meld Gold and Silver prices.
    
    Returns:
        Dict with 'gold' and 'silver' prices in USD per gram
    """
    return {
        'gold': get_meld_gold_price(),
        'silver': get_meld_silver_price()
    }


def calculate_implied_price_per_gram(spot_price_per_oz: float) -> float:
    """
    Convert spot price per troy ounce to price per gram.
    
    Args:
        spot_price_per_oz: Spot price in USD per troy ounce
        
    Returns:
        Price in USD per gram
    """
    return spot_price_per_oz / GRAMS_PER_TROY_OZ


def calculate_arbitrage(
    spot_per_oz: float,
    meld_price: float
) -> dict:
    """
    Calculate arbitrage opportunity between spot and Meld prices.
    
    Args:
        spot_per_oz: Spot price in USD per troy ounce
        meld_price: Meld token price in USD per gram
        
    Returns:
        Dict with implied price, premium %, and trading signal
    """
    implied_per_gram = calculate_implied_price_per_gram(spot_per_oz)
    
    if implied_per_gram <= 0:
        return {
            'implied_per_gram': 0,
            'premium_pct': 0,
            'premium_usd': 0,
            'signal': 'ERROR',
            'signal_strength': 0
        }
    
    premium_usd = meld_price - implied_per_gram
    premium_pct = (premium_usd / implied_per_gram) * 100
    
    # Determine signal based on premium
    if premium_pct > 10:
        signal = 'STRONG_SELL'
        signal_strength = min(100, premium_pct * 5)
    elif premium_pct > 5:
        signal = 'SELL'
        signal_strength = premium_pct * 5
    elif premium_pct < -10:
        signal = 'STRONG_BUY'
        signal_strength = min(100, abs(premium_pct) * 5)
    elif premium_pct < -5:
        signal = 'BUY'
        signal_strength = abs(premium_pct) * 5
    else:
        signal = 'HOLD'
        signal_strength = 0
    
    return {
        'implied_per_gram': round(implied_per_gram, 4),
        'premium_pct': round(premium_pct, 2),
        'premium_usd': round(premium_usd, 4),
        'signal': signal,
        'signal_strength': round(signal_strength, 1)
    }


# ============================================================================
# Full Arbitrage Analysis Function
# ============================================================================

def get_meld_arbitrage_analysis() -> dict:
    """
    Get complete arbitrage analysis for Meld Gold and Silver.
    
    Compares Meld on-chain prices to Yahoo Finance spot prices.
    
    Returns:
        Complete analysis with spot prices, Meld prices, and arbitrage signals
    """
    # Import spot price functions (adjust import based on your structure)
    # These should already exist in your pricing.py
    from core.pricing import get_gold_price_per_oz, get_silver_price_per_oz
    
    # Get spot prices
    spot_gold = get_gold_price_per_oz()
    spot_silver = get_silver_price_per_oz()
    
    # Get Meld prices
    meld_gold = get_meld_gold_price()
    meld_silver = get_meld_silver_price()
    
    # Build response
    result = {
        'gold': None,
        'silver': None,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'data_complete': True
    }
    
    # Gold analysis
    if spot_gold and meld_gold:
        arb = calculate_arbitrage(spot_gold, meld_gold)
        result['gold'] = {
            'spot_per_oz': round(spot_gold, 2),
            'implied_per_gram': arb['implied_per_gram'],
            'meld_price': round(meld_gold, 4),
            'premium_pct': arb['premium_pct'],
            'premium_usd': arb['premium_usd'],
            'signal': arb['signal'],
            'signal_strength': arb['signal_strength']
        }
    else:
        result['data_complete'] = False
        result['gold'] = {
            'error': 'Unable to fetch gold prices',
            'spot_available': spot_gold is not None,
            'meld_available': meld_gold is not None
        }
    
    # Silver analysis
    if spot_silver and meld_silver:
        arb = calculate_arbitrage(spot_silver, meld_silver)
        result['silver'] = {
            'spot_per_oz': round(spot_silver, 2),
            'implied_per_gram': arb['implied_per_gram'],
            'meld_price': round(meld_silver, 4),
            'premium_pct': arb['premium_pct'],
            'premium_usd': arb['premium_usd'],
            'signal': arb['signal'],
            'signal_strength': arb['signal_strength']
        }
    else:
        result['data_complete'] = False
        result['silver'] = {
            'error': 'Unable to fetch silver prices',
            'spot_available': spot_silver is not None,
            'meld_available': meld_silver is not None
        }
    
    return result


# ============================================================================
# Test function
# ============================================================================

if __name__ == "__main__":
    print("Testing Meld Arbitrage Analysis...")
    print("-" * 50)
    
    analysis = get_meld_arbitrage_analysis()
    
    print(f"\n📊 GOLD ARBITRAGE")
    if 'error' not in analysis['gold']:
        g = analysis['gold']
        print(f"  Spot (per oz):     ${g['spot_per_oz']:,.2f}")
        print(f"  Implied (per g):   ${g['implied_per_gram']:.4f}")
        print(f"  Meld GOLD$:        ${g['meld_price']:.4f}")
        print(f"  Premium:           {g['premium_pct']:+.2f}%")
        print(f"  Signal:            {g['signal']}")
    else:
        print(f"  Error: {analysis['gold']['error']}")
    
    print(f"\n⚪ SILVER ARBITRAGE")
    if 'error' not in analysis['silver']:
        s = analysis['silver']
        print(f"  Spot (per oz):     ${s['spot_per_oz']:,.2f}")
        print(f"  Implied (per g):   ${s['implied_per_gram']:.4f}")
        print(f"  Meld SILVER$:      ${s['meld_price']:.4f}")
        print(f"  Premium:           {s['premium_pct']:+.2f}%")
        print(f"  Signal:            {s['signal']}")
    else:
        print(f"  Error: {analysis['silver']['error']}")
    
    print(f"\nTimestamp: {analysis['timestamp']}")
