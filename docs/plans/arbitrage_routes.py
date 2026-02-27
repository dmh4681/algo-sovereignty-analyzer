"""
Meld Arbitrage API Endpoint
Add this to your api/routes.py file
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ============================================================================
# SCHEMAS - Add to api/schemas.py
# ============================================================================

class ArbitrageMetalData(BaseModel):
    """Arbitrage data for a single metal (gold or silver)."""
    spot_per_oz: float
    implied_per_gram: float
    meld_price: float
    premium_pct: float
    premium_usd: float
    signal: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    signal_strength: float  # 0-100


class ArbitrageMetalError(BaseModel):
    """Error response when price data unavailable."""
    error: str
    spot_available: bool
    meld_available: bool


class MeldArbitrageResponse(BaseModel):
    """Complete Meld arbitrage analysis response."""
    gold: Optional[ArbitrageMetalData] = None
    silver: Optional[ArbitrageMetalData] = None
    timestamp: str
    data_complete: bool


# ============================================================================
# ENDPOINT - Add to api/routes.py
# ============================================================================

# Add this import at the top of routes.py:
# from core.pricing import get_gold_price_per_oz, get_silver_price_per_oz, get_meld_gold_price, get_meld_silver_price

# Constants
GRAMS_PER_TROY_OZ = 31.1035

# Meld ASA IDs
MELD_GOLD_ASA = 246516580
MELD_SILVER_ASA = 246519683


def _calculate_arbitrage_signal(premium_pct: float) -> tuple[str, float]:
    """
    Determine trading signal based on premium percentage.
    
    Returns:
        Tuple of (signal_name, signal_strength 0-100)
    """
    if premium_pct > 10:
        return ('STRONG_SELL', min(100, premium_pct * 5))
    elif premium_pct > 5:
        return ('SELL', premium_pct * 5)
    elif premium_pct < -10:
        return ('STRONG_BUY', min(100, abs(premium_pct) * 5))
    elif premium_pct < -5:
        return ('BUY', abs(premium_pct) * 5)
    else:
        return ('HOLD', 0)


@router.get("/arbitrage/meld")
async def get_meld_arbitrage():
    """
    Compare Meld Gold/Silver on-chain prices to spot prices.
    
    Returns premium/discount percentage and trading signals for arbitrage opportunities.
    
    **Signal Interpretation:**
    - STRONG_BUY: Meld >10% below spot (buy Meld, it's cheap)
    - BUY: Meld 5-10% below spot
    - HOLD: Within ±5% of spot (fair value)
    - SELL: Meld 5-10% above spot
    - STRONG_SELL: Meld >10% above spot (sell Meld, buy physical)
    
    **Data Sources:**
    - Spot prices: Yahoo Finance (COMEX futures GC=F, SI=F)
    - Meld prices: Vestige API (Algorand DEX aggregator)
    """
    # Import pricing functions
    from core.pricing import (
        get_gold_price_per_oz, 
        get_silver_price_per_oz,
        get_meld_gold_price,
        get_meld_silver_price
    )
    
    result = {
        'gold': None,
        'silver': None,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'data_complete': True
    }
    
    # =========== GOLD ===========
    try:
        spot_gold = get_gold_price_per_oz()
        meld_gold = get_meld_gold_price()
        
        if spot_gold and meld_gold and spot_gold > 0:
            implied_gold = spot_gold / GRAMS_PER_TROY_OZ
            premium_usd = meld_gold - implied_gold
            premium_pct = (premium_usd / implied_gold) * 100
            signal, strength = _calculate_arbitrage_signal(premium_pct)
            
            result['gold'] = {
                'spot_per_oz': round(spot_gold, 2),
                'implied_per_gram': round(implied_gold, 4),
                'meld_price': round(meld_gold, 4),
                'premium_pct': round(premium_pct, 2),
                'premium_usd': round(premium_usd, 4),
                'signal': signal,
                'signal_strength': round(strength, 1)
            }
        else:
            result['data_complete'] = False
            result['gold'] = {
                'error': 'Unable to fetch gold prices',
                'spot_available': spot_gold is not None,
                'meld_available': meld_gold is not None
            }
    except Exception as e:
        print(f"Error calculating gold arbitrage: {e}")
        result['data_complete'] = False
        result['gold'] = {'error': str(e), 'spot_available': False, 'meld_available': False}
    
    # =========== SILVER ===========
    try:
        spot_silver = get_silver_price_per_oz()
        meld_silver = get_meld_silver_price()
        
        if spot_silver and meld_silver and spot_silver > 0:
            implied_silver = spot_silver / GRAMS_PER_TROY_OZ
            premium_usd = meld_silver - implied_silver
            premium_pct = (premium_usd / implied_silver) * 100
            signal, strength = _calculate_arbitrage_signal(premium_pct)
            
            result['silver'] = {
                'spot_per_oz': round(spot_silver, 2),
                'implied_per_gram': round(implied_silver, 4),
                'meld_price': round(meld_silver, 4),
                'premium_pct': round(premium_pct, 2),
                'premium_usd': round(premium_usd, 4),
                'signal': signal,
                'signal_strength': round(strength, 1)
            }
        else:
            result['data_complete'] = False
            result['silver'] = {
                'error': 'Unable to fetch silver prices',
                'spot_available': spot_silver is not None,
                'meld_available': meld_silver is not None
            }
    except Exception as e:
        print(f"Error calculating silver arbitrage: {e}")
        result['data_complete'] = False
        result['silver'] = {'error': str(e), 'spot_available': False, 'meld_available': False}
    
    return result


# ============================================================================
# Example Response
# ============================================================================
"""
{
  "gold": {
    "spot_per_oz": 2650.00,
    "implied_per_gram": 85.20,
    "meld_price": 88.50,
    "premium_pct": 3.87,
    "premium_usd": 3.30,
    "signal": "HOLD",
    "signal_strength": 0
  },
  "silver": {
    "spot_per_oz": 30.50,
    "implied_per_gram": 0.981,
    "meld_price": 1.15,
    "premium_pct": 17.2,
    "premium_usd": 0.169,
    "signal": "STRONG_SELL",
    "signal_strength": 86.0
  },
  "timestamp": "2024-12-27T15:30:00Z",
  "data_complete": true
}
"""
