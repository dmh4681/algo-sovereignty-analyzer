# Meld Arbitrage Spotter - Complete Integration Guide

## Quick Summary
This adds a Meld Gold/Silver arbitrage spotter that compares on-chain Meld token prices to spot precious metals prices.

---

## FILES TO CREATE/MODIFY

### 1. Backend Files
| File | Action | Description |
|------|--------|-------------|
| `core/pricing.py` | MODIFY | Add Meld price fetching functions |
| `api/routes.py` | MODIFY | Add `/api/v1/arbitrage/meld` endpoint |
| `api/schemas.py` | MODIFY | Add response schemas |

### 2. Frontend Files
| File | Action | Description |
|------|--------|-------------|
| `web/components/MeldArbitrageSpotter.tsx` | CREATE | Main widget component |
| `web/app/arbitrage/page.tsx` | CREATE | Dedicated arbitrage page |
| `web/app/analyze/page.tsx` | MODIFY | Add widget to analyze page (optional) |

---

## STEP 1: Update core/pricing.py

Add these imports at the top:
```python
from datetime import datetime, timedelta
from typing import Optional
import httpx
```

Add these constants and functions:
```python
# ============================================================================
# MELD PRICING - Add to core/pricing.py
# ============================================================================

# Meld ASA IDs on Algorand Mainnet
MELD_GOLD_ASA = 246516580   # GOLD$ - 1 token = 1 gram of gold
MELD_SILVER_ASA = 246519683  # SILVER$ - 1 token = 1 gram of silver

# Conversion constant
GRAMS_PER_TROY_OZ = 31.1035

# Vestige API for Algorand ASA prices
VESTIGE_PRICE_URL = "https://free-api.vestige.fi/asset/{asa_id}/price"

# Cache for Meld prices (5 minute TTL)
_meld_price_cache: dict = {}
_meld_cache_ttl = timedelta(minutes=5)


def _get_vestige_price(asa_id: int) -> Optional[float]:
    """
    Fetch current USD price for an ASA from Vestige API.
    
    Args:
        asa_id: Algorand Standard Asset ID
        
    Returns:
        USD price per token, or None if unavailable
    """
    try:
        url = VESTIGE_PRICE_URL.format(asa_id=asa_id)
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
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
        if datetime.now() - timestamp < _meld_cache_ttl:
            return price
    
    price = _get_vestige_price(MELD_GOLD_ASA)
    
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
        if datetime.now() - timestamp < _meld_cache_ttl:
            return price
    
    price = _get_vestige_price(MELD_SILVER_ASA)
    
    if price is not None:
        _meld_price_cache[cache_key] = (price, datetime.now())
    
    return price
```

---

## STEP 2: Update api/schemas.py

Add these Pydantic models:
```python
from typing import Optional, Union

# ============================================================================
# ARBITRAGE SCHEMAS
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
    gold: Optional[Union[ArbitrageMetalData, ArbitrageMetalError]] = None
    silver: Optional[Union[ArbitrageMetalData, ArbitrageMetalError]] = None
    timestamp: str
    data_complete: bool
```

---

## STEP 3: Update api/routes.py

Add this import:
```python
from core.pricing import (
    get_gold_price_per_oz, 
    get_silver_price_per_oz,
    get_meld_gold_price,
    get_meld_silver_price,
    GRAMS_PER_TROY_OZ
)
```

Add this helper function and endpoint:
```python
# ============================================================================
# ARBITRAGE ENDPOINT
# ============================================================================

def _calculate_arbitrage_signal(premium_pct: float) -> tuple:
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
    """
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
```

---

## STEP 4: Create Frontend Component

Create file: `web/components/MeldArbitrageSpotter.tsx`
(See MeldArbitrageSpotter.tsx in outputs)

---

## STEP 5: Create Arbitrage Page

Create file: `web/app/arbitrage/page.tsx`
(See arbitrage_page.tsx in outputs)

---

## STEP 6: Add to Analyze Page (Optional)

In `web/app/analyze/page.tsx`, add:

```tsx
// Import at top
import { MeldArbitrageSpotter } from '@/components/MeldArbitrageSpotter'

// Add in JSX after sovereignty metrics, before asset breakdown:
{/* Arbitrage Opportunities */}
<div className="mt-6">
  <MeldArbitrageSpotter />
</div>
```

---

## STEP 7: Add Navigation Link

Update your navigation component to include:
```tsx
{
  name: 'Arbitrage',
  href: '/arbitrage',
  icon: <Scale className="h-5 w-5" />,  // from lucide-react
}
```

---

## TESTING

### 1. Test Backend
```bash
# Start API server
uvicorn api.main:app --reload --port 8000

# Test endpoint
curl http://localhost:8000/api/v1/arbitrage/meld | jq
```

Expected response:
```json
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
    "implied_per_gram": 0.98,
    "meld_price": 2.97,
    "premium_pct": 203.0,
    "premium_usd": 1.99,
    "signal": "STRONG_SELL",
    "signal_strength": 100
  },
  "timestamp": "2024-12-27T15:30:00Z",
  "data_complete": true
}
```

### 2. Test Frontend
```bash
cd web
npm run dev

# Navigate to http://localhost:3000/arbitrage
```

---

## TROUBLESHOOTING

### "get_gold_price_per_oz not found"
Your pricing.py may use different function names. Check your existing functions and update the import.

### "Vestige returns 0 price"
Meld tokens may have low liquidity. Check Vestige directly:
- https://free-api.vestige.fi/asset/246516580/price (Gold)
- https://free-api.vestige.fi/asset/246519683/price (Silver)

### "CORS error"
Ensure your FastAPI CORS is configured:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://algosovereignty.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### "Premium seems wrong"
Double-check the math:
- Spot gold ~$2650/oz → $85.20/gram
- If Meld GOLD$ is $88.50, premium = (88.50 - 85.20) / 85.20 × 100 = 3.87%

---

## FUTURE ENHANCEMENTS

1. **Historical Premium Tracking** - Store premiums over time, show chart
2. **Gold/Silver Ratio Widget** - Track GSR from Meld prices
3. **Price Alerts** - Notify when premium exceeds threshold
4. **Other Pairs** - goBTC vs BTC spot, ALGO cross-exchange

---

## FILES SUMMARY

Created files (in /mnt/user-data/outputs/):
1. `meld_pricing.py` - Backend pricing functions
2. `arbitrage_routes.py` - API endpoint code
3. `MeldArbitrageSpotter.tsx` - React widget component
4. `arbitrage_page.tsx` - Dedicated page component
5. `MELD_ARBITRAGE_PROMPTS.md` - Claude Code prompts
6. `MELD_ARBITRAGE_INTEGRATION.md` - This file
