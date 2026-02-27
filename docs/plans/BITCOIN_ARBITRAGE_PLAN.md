# Bitcoin 3-Way Arbitrage Implementation Plan

## Overview

Build a comprehensive Bitcoin arbitrage comparison feature that tracks:
1. **Coinbase Spot BTC** - Real Bitcoin spot price (reference)
2. **goBTC** (ASA 386192725) - Algorand-native wrapped Bitcoin
3. **WBTC** (ASA 1058926737) - Wormhole-bridged wrapped Bitcoin

## Key Discovery

- **WBTC ASA ID:** 1058926737
- **Source:** Wormhole bridge (cross-chain interoperability)
- **Current Market Cap:** ~$533K
- **TVL:** ~$139K (smaller liquidity than goBTC)

## Architecture

### Backend Changes

**File: `core/pricing.py`**
```python
# Add WBTC constant
WBTC_ASA = 1058926737

# Add function
def get_wbtc_price() -> Optional[float]:
    """Fetch WBTC price from Vestige API."""
    return fetch_vestige_price(WBTC_ASA)
```

**File: `api/routes.py`**
- Extend `/api/v1/meld-arbitrage` endpoint to include WBTC data
- Add new endpoint `/api/v1/btc-arbitrage-history` for historical data
- Calculate 3-way spreads:
  - goBTC vs Spot
  - WBTC vs Spot
  - goBTC vs WBTC (cross-DEX arbitrage opportunity)

### New Historical Tracking

**File: `core/btc_history.py`** (NEW)
- SQLite table for Bitcoin price snapshots
- Store: timestamp, spot_btc, gobtc_price, wbtc_price
- Auto-capture every 15 minutes via background task
- 30-day retention for charting

**Table Schema:**
```sql
CREATE TABLE btc_price_history (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    spot_btc REAL,
    gobtc_price REAL,
    wbtc_price REAL,
    gobtc_premium_pct REAL,
    wbtc_premium_pct REAL
);
```

### Frontend Changes

**File: `web/components/BitcoinArbitrageCard.tsx`** (NEW)
- Unified card showing all 3 prices side-by-side
- Premium/discount indicators for each wrapped token
- Color-coded signals (green = discount/buy, red = premium/sell)
- Trading links to both goBTC and WBTC on Tinyman

**File: `web/components/BitcoinHistoryChart.tsx`** (NEW)
- Recharts line chart with 3 series
- Toggle between:
  - Absolute prices ($)
  - Premium/discount (%)
- Time range selector: 24h, 7d, 30d
- Highlight arbitrage windows

**File: `web/app/arbitrage/page.tsx`** (UPDATE)
- Replace current single-token view with 3-way comparison
- Add historical chart section
- Add "Best Opportunity" highlight card

## API Response Structure

```typescript
interface BitcoinArbitrageData {
  timestamp: string;

  // Prices
  spotBtc: number;
  gobtcPrice: number;
  wbtcPrice: number;

  // vs Spot premiums
  gobtcPremiumPct: number;
  gobtcPremiumUsd: number;
  wbtcPremiumPct: number;
  wbtcPremiumUsd: number;

  // Cross-DEX spread
  gobtcVsWbtcSpread: number;

  // Signals
  gobtcSignal: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL';
  wbtcSignal: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL';

  // Best opportunity
  bestOpportunity: {
    action: string;
    token: 'goBTC' | 'WBTC';
    reason: string;
  };

  // Trading links
  gobtcTinymanUrl: string;
  wbtcTinymanUrl: string;
}

interface BitcoinArbitrageHistory {
  dataPoints: {
    timestamp: string;
    spotBtc: number;
    gobtcPrice: number;
    wbtcPrice: number;
    gobtcPremiumPct: number;
    wbtcPremiumPct: number;
  }[];

  stats: {
    avgGobtcPremium: number;
    avgWbtcPremium: number;
    maxGobtcDiscount: number;
    maxWbtcDiscount: number;
  };
}
```

## UI Design

### 3-Way Comparison Card
```
┌─────────────────────────────────────────────────────────┐
│  BITCOIN ARBITRAGE MONITOR                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  COINBASE SPOT          goBTC              WBTC         │
│  $94,523.00        $93,845.21         $94,102.45       │
│  Reference          -0.72%             -0.44%          │
│                     -$677.79           -$420.55        │
│                     🟢 BUY             🟢 BUY          │
│                                                         │
│  ──────────────────────────────────────────────────    │
│                                                         │
│  CROSS-DEX SPREAD: goBTC is 0.27% cheaper than WBTC    │
│  💡 Best Play: Buy goBTC at deeper discount            │
│                                                         │
│  [Trade goBTC on Tinyman]  [Trade WBTC on Tinyman]     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Historical Chart
```
Premium/Discount vs Spot (%)
     │
 +2% ┤                        ╭───╮
     │                       ╱     ╲
  0% ┼────────────╱╲────────╱───────╲────────────────
     │           ╱  ╲      ╱         ╲        ╭────
 -2% ┤          ╱    ╲────╱           ╲──────╯
     │         ╱
 -4% ┤────────╯
     └──────────────────────────────────────────────
       Dec 20    Dec 22    Dec 24    Dec 26    Dec 28

     ━━ goBTC    ─── WBTC    ··· Spot reference
```

## Implementation Steps

### Phase 1: Backend (pricing + API)
1. Add WBTC_ASA constant to pricing.py
2. Create get_wbtc_price() function
3. Update /api/v1/meld-arbitrage to return 3-way data
4. Create btc_history.py for historical storage

### Phase 2: Historical Data
5. Create SQLite table for price history
6. Add background task to capture snapshots
7. Create /api/v1/btc-arbitrage-history endpoint

### Phase 3: Frontend
8. Create BitcoinArbitrageCard.tsx component
9. Create BitcoinHistoryChart.tsx component
10. Update arbitrage/page.tsx with new layout

### Phase 4: Polish
11. Add loading states and error handling
12. Test with live data
13. Build and verify

## Trading Links

- **goBTC on Tinyman:** `https://app.tinyman.org/#/swap?asset_in=0&asset_out=386192725`
- **WBTC on Tinyman:** `https://app.tinyman.org/#/swap?asset_in=0&asset_out=1058926737`

## Risk Notes for UI

- WBTC has lower liquidity (~$139K TVL vs goBTC's larger pool)
- Slippage may be higher on WBTC trades
- Wormhole bridge carries smart contract risk
- goBTC is native Algorand (no bridge risk)

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `core/pricing.py` | MODIFY | Add WBTC constant + function |
| `core/btc_history.py` | CREATE | Historical price tracking |
| `api/routes.py` | MODIFY | Extend arbitrage endpoint |
| `web/lib/types.ts` | MODIFY | Add TypeScript interfaces |
| `web/components/BitcoinArbitrageCard.tsx` | CREATE | 3-way comparison UI |
| `web/components/BitcoinHistoryChart.tsx` | CREATE | Historical chart |
| `web/app/arbitrage/page.tsx` | MODIFY | Integrate new components |
