# Railway Deployment Instructions

## New Features to Deploy

The following new files/changes need to be deployed for the 3-way Bitcoin arbitrage feature:

### Backend Changes (Python/FastAPI)

1. **`core/pricing.py`** - Added WBTC pricing support
   - New constant: `WBTC_ASA = 1058926737`
   - New function: `get_wbtc_price()`

2. **`core/btc_history.py`** - NEW FILE
   - SQLite-based price history tracking
   - Auto-captures snapshots every 10 minutes
   - 30-day retention with auto-cleanup

3. **`api/routes.py`** - Extended endpoints
   - `/arbitrage/meld` - Now returns 3-way comparison (goBTC + WBTC)
   - `/arbitrage/btc-history` - NEW endpoint for historical data

### Frontend Changes (Next.js)

These are deployed via Vercel (or wherever frontend is hosted):

1. **`web/components/BitcoinArbitrageCard.tsx`** - NEW
2. **`web/components/BitcoinHistoryChart.tsx`** - NEW
3. **`web/lib/types.ts`** - New TypeScript interfaces
4. **`web/lib/api.ts`** - New `getBTCHistory()` function
5. **`web/app/arbitrage/page.tsx`** - Updated with new components

---

## Deployment Steps

### 1. Push to GitHub

```bash
git add .
git commit -m "Add 3-way Bitcoin arbitrage (goBTC vs WBTC) with historical chart"
git push origin main
```

### 2. Railway Backend Deployment

Railway should auto-deploy on push to main. If not:

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Select your project
3. Click "Deploy" or trigger manual redeploy

**Important:** The new `core/btc_history.py` creates a SQLite database at `data/btc_price_history.db`. Make sure:
- The `data/` directory is writable
- SQLite is available (usually is by default)

If using Railway volumes for persistence:
```bash
# In Railway settings, mount a volume at /app/data
```

### 3. Verify Deployment

Test the new endpoints:

```bash
# Test main arbitrage endpoint (should show goBTC + WBTC)
curl https://your-api.railway.app/api/v1/arbitrage/meld | jq '.bitcoin'

# Test history endpoint
curl https://your-api.railway.app/api/v1/arbitrage/btc-history?hours=24
```

Expected response structure for `/arbitrage/meld`:
```json
{
  "bitcoin": {
    "spot_price": 94000.00,
    "gobtc": {
      "price": 93200.00,
      "premium_pct": -0.85,
      "signal": "BUY",
      ...
    },
    "wbtc": {
      "price": 94100.00,
      "premium_pct": 0.11,
      "signal": "HOLD",
      ...
    },
    "cross_dex_spread": {
      "gobtc_vs_wbtc_pct": -0.96,
      "description": "goBTC is 0.96% cheaper than WBTC"
    },
    "best_opportunity": {
      "token": "goBTC",
      "action": "BUY",
      "reason": "goBTC has deeper discount (-0.85% vs 0.11%)",
      ...
    }
  }
}
```

### 4. Seed Historical Data (Optional)

If you want historical data immediately after deploy:

```bash
# SSH into Railway or run via Railway CLI
railway run python scripts/seed_btc_history.py --days 7
```

Or let it populate naturally - each page visit captures a snapshot (max 1 per 10 minutes).

---

## Environment Variables

**Required for persistent storage with Railway Volume:**
```
DATA_DIR=/app/data
```

Set this in Railway's Variables tab. This tells the app where to store:
- Sovereignty history JSON files (`/app/data/history/*.json`)
- BTC price history SQLite database (`/app/data/btc_price_history.db`)

**Other dependencies (no auth required):**
- Coinbase free API
- Vestige API
- SQLite (local file)

---

## Rollback

If issues occur, the new endpoints are additive and won't break existing functionality. To rollback:

```bash
git revert HEAD
git push origin main
```

---

## Monitoring

Check Railway logs for:
- `[WARN] Using BTC spot price for WBTC` - Vestige fallback triggered
- `Warning: Failed to save BTC price snapshot` - History write issues
- `Error calculating Bitcoin arbitrage` - General errors

The feature gracefully degrades - if WBTC price fails, it shows error state for that token only.
