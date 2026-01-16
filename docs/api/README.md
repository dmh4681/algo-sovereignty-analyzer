# Algo Sovereignty Analyzer API Documentation

> Complete API reference for algosovereignty.com

**Base URL:** `http://localhost:8000/api/v1` (development)
**Production:** `https://api.algosovereignty.com/api/v1`

## Overview

The Algo Sovereignty Analyzer API provides endpoints for analyzing Algorand wallet holdings, calculating sovereignty metrics, tracking precious metals arbitrage, and monitoring central bank gold reserves.

## Authentication

Currently, the API is publicly accessible. Rate limiting is applied per IP address.

## Rate Limiting

| Endpoint Type | Limit |
|---------------|-------|
| Wallet Analysis | 10 requests/minute |
| Network Stats | 30 requests/minute |
| Historical Data | 60 requests/minute |
| Reseed Operations | 1 request/hour |

---

## Quick Reference

| Category | Endpoints | Description |
|----------|-----------|-------------|
| [Wallet Analysis](#wallet-analysis) | 3 | Core sovereignty analysis |
| [History](#history--tracking) | 2 | Snapshot tracking |
| [Network Stats](#network-statistics) | 2 | Algorand network metrics |
| [Arbitrage](#arbitrage--pricing) | 3 | Cross-market pricing |
| [Gold Miners](#gold-miner-metrics) | 6 | Mining sector data |
| [Silver Miners](#silver-miner-metrics) | 6 | Silver mining data |
| [Inflation](#inflation-data) | 6 | CPI/M2 analysis |
| [Central Banks](#central-bank-gold) | 8 | Gold reserves tracking |
| [Earnings](#earnings-calendar) | 9 | Mining earnings calendar |
| [Premiums](#physical-premiums) | 9 | Dealer premium tracking |

---

## Wallet Analysis

### POST `/analyze`

Main wallet analysis endpoint. Returns sovereignty metrics, asset classification, and portfolio breakdown.

**Request:**
```json
{
  "address": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
  "monthly_fixed_expenses": 4000
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `address` | string | Yes | 58-character Algorand address |
| `monthly_fixed_expenses` | float | No | Monthly expenses for sovereignty calc |

**Query Parameters:**
- `use_local_node`: boolean (default: false) - Use local Algorand node

**Response:**
```json
{
  "address": "AAAA...AAAA",
  "is_participating": true,
  "hard_money_algo": 1250.50,
  "categories": {
    "hard_money": {
      "items": [
        {
          "name": "goBTC",
          "amount": 0.015,
          "usd_value": 1500,
          "category": "hard_money",
          "sub_category": "bitcoin"
        }
      ],
      "total_usd": 1500
    },
    "algorand": { "items": [...], "total_usd": 5000 },
    "dollars": { "items": [...], "total_usd": 2500 },
    "shitcoins": { "items": [...], "total_usd": 500 }
  },
  "sovereignty_data": {
    "total_portfolio_usd": 9500,
    "annual_expenses": 48000,
    "sovereignty_ratio": 0.198,
    "years_of_freedom": 0.198,
    "status": "vulnerable",
    "hard_money_percentage": 15.79,
    "message": "Build your hard money reserves"
  },
  "participation_info": {
    "is_participating": true,
    "stake_percentage": 0.0001,
    "key_expiry_round": 45000000
  }
}
```

**Asset Categories:**
| Category | Assets Included |
|----------|-----------------|
| `hard_money` | BTC, WBTC, goBTC, XAUT, PAXG, GOLD$, SILVER$ |
| `algorand` | ALGO, xALGO, fALGO, gALGO, mALGO, lALGO, tALGO |
| `dollars` | USDC, USDT, DAI, fUSDC, fUSDT, STBL |
| `shitcoins` | Everything else (LP tokens, NFTs, memecoins) |

**Sovereignty Status Thresholds:**
| Status | Years of Freedom |
|--------|------------------|
| Generationally Sovereign | >= 20 |
| Antifragile | 6-20 |
| Robust | 3-6 |
| Fragile | 1-3 |
| Vulnerable | < 1 |

**Caching:** Results cached 15 minutes per address.

---

### POST `/agent/advice`

Get AI-powered financial coaching using Claude.

**Request:**
```json
{
  "analysis": { /* Full analysis response from /analyze */ }
}
```

**Response:**
```json
{
  "advice": "Based on your portfolio composition, I recommend focusing on increasing your hard money allocation. Your current 15.79% in Bitcoin and precious metals is a solid foundation, but consider...",
  "key_points": [
    "Increase hard money allocation to 25%+",
    "Consider reducing shitcoin exposure",
    "Your ALGO staking position is healthy"
  ]
}
```

**Requirements:** `ANTHROPIC_API_KEY` environment variable

---

### GET `/classifications`

Retrieve manual asset classification mappings.

**Response:**
```json
{
  "GOLD$": "hard_money",
  "SILVER$": "hard_money",
  "goBTC": "hard_money",
  "USDC": "dollars",
  "TINY": "shitcoins"
}
```

---

## History & Tracking

### POST `/history/save`

Save a sovereignty snapshot for historical tracking.

**Request:**
```json
{
  "address": "AAAA...AAAA",
  "monthly_fixed_expenses": 4000
}
```

**Response:**
```json
{
  "success": true,
  "message": "Snapshot saved successfully",
  "snapshot": {
    "timestamp": "2026-01-15T20:00:00Z",
    "total_usd": 9500,
    "hard_money_usd": 1500,
    "sovereignty_ratio": 0.198,
    "status": "vulnerable"
  }
}
```

---

### GET `/history/{address}`

Retrieve historical sovereignty snapshots with progress metrics.

**Path Parameters:**
- `address`: Algorand wallet address

**Query Parameters:**
- `days`: 30, 90, or 365 (default: 90)

**Response:**
```json
{
  "snapshots": [
    {
      "timestamp": "2026-01-15T00:00:00Z",
      "total_usd": 9500,
      "hard_money_usd": 1500,
      "sovereignty_ratio": 0.198,
      "status": "vulnerable"
    },
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "total_usd": 8000,
      "hard_money_usd": 1200,
      "sovereignty_ratio": 0.167,
      "status": "vulnerable"
    }
  ],
  "progress": {
    "total_change_usd": 1500,
    "total_change_pct": 18.75,
    "ratio_improvement": 0.031,
    "days_to_next_status": 180,
    "trend": "improving"
  },
  "all_time": {
    "highest_ratio": 0.198,
    "lowest_ratio": 0.10,
    "average_ratio": 0.15,
    "first_snapshot": "2025-06-01T00:00:00Z"
  }
}
```

---

## Network Statistics

### GET `/network/stats`

Algorand network participation and decentralization metrics.

**Response:**
```json
{
  "network": {
    "total_supply": 10000000000,
    "circulating_supply": 8500000000,
    "online_stake": 5000000000,
    "participation_rate": 0.588
  },
  "foundation": {
    "estimated_holdings": 1500000000,
    "percentage_of_supply": 15.0,
    "impact_on_decentralization": "moderate"
  },
  "community": {
    "stake_percentage": 85.0,
    "estimated_validators": 3075
  },
  "decentralization_score": 72,
  "score_breakdown": {
    "participation_score": 25,
    "distribution_score": 22,
    "validator_score": 25
  },
  "estimated_node_count": 3075,
  "timestamp": "2026-01-15T20:00:00Z"
}
```

**Caching:** 5 minutes

---

### GET `/network/wallet/{address}`

Check specific wallet's consensus participation status.

**Path Parameters:**
- `address`: 58-character Algorand address

**Response:**
```json
{
  "address": "AAAA...AAAA",
  "is_participating": true,
  "balance_algo": 50000,
  "stake_percentage": 0.001,
  "participation_key": {
    "vote_first": 40000000,
    "vote_last": 50000000,
    "vote_key_dilution": 10000
  },
  "contribution_tier": "Active Participant",
  "current_round": 42000000,
  "timestamp": "2026-01-15T20:00:00Z"
}
```

**Contribution Tiers:**
| Tier | ALGO Balance |
|------|--------------|
| Whale Validator | >= 10M |
| Major Validator | 1M - 10M |
| Active Participant | 100K - 1M |
| Community Node | 10K - 100K |
| Micro Validator | 1K - 10K |
| Observer | < 1K |

**Caching:** 1 minute

---

## Arbitrage & Pricing

### GET `/gold-silver-ratio`

Current Gold/Silver ratio with historical context.

**Response:**
```json
{
  "ratio": 65.5,
  "gold_price": 4500.00,
  "silver_price": 68.70,
  "historical_mean": 15.0,
  "historical_range": { "low": 12, "high": 90 },
  "status": "undervalued",
  "interpretation": {
    "signal": "Silver is historically undervalued relative to gold",
    "action": "Consider silver accumulation",
    "context": "Ratio above 60 has historically preceded silver outperformance"
  },
  "timestamp": "2026-01-15T20:00:00Z"
}
```

**Status Values:**
| Status | Ratio Range |
|--------|-------------|
| undervalued | > 50 (silver cheap) |
| normalized | 30-50 |
| compressed | < 30 (silver expensive) |

---

### GET `/arbitrage/meld`

Compare Algorand wrapped assets to spot prices.

**Response:**
```json
{
  "gold": {
    "spot_per_oz": 4500.00,
    "implied_per_gram": 144.68,
    "meld_price": 148.50,
    "premium_pct": 2.64,
    "premium_usd": 3.82,
    "signal": "SELL",
    "signal_strength": 45
  },
  "silver": {
    "spot_per_oz": 68.70,
    "implied_per_gram": 2.21,
    "meld_price": 2.15,
    "premium_pct": -2.71,
    "premium_usd": -0.06,
    "signal": "BUY",
    "signal_strength": 55
  },
  "bitcoin": {
    "spot_price": 100000,
    "gobtc_price": 99500,
    "wbtc_price": 99800,
    "gobtc_premium_pct": -0.50,
    "wbtc_premium_pct": -0.20,
    "cross_dex_spread": 0.30,
    "signal": "BUY_GOBTC",
    "signal_strength": 35
  },
  "gsr": {
    "meld_gsr": 69.07,
    "spot_gsr": 65.50,
    "gsr_spread_pct": 5.45,
    "rotation_signal": "HOLD"
  },
  "timestamp": "2026-01-15T20:00:00Z"
}
```

**Trading Signals:**
| Signal | Premium Range |
|--------|---------------|
| STRONG_BUY | < -6% |
| BUY | -6% to -0.5% |
| HOLD | -0.5% to +0.5% |
| SELL | +0.5% to +6% |
| STRONG_SELL | > +6% |

---

### GET `/arbitrage/btc-history`

Historical Bitcoin arbitrage data for charting.

**Query Parameters:**
- `hours`: 1-720 (default: 24)

**Response:**
```json
{
  "data_points": [
    {
      "timestamp": "2026-01-15T19:00:00Z",
      "spot_btc": 100000,
      "gobtc_price": 99500,
      "wbtc_price": 99800,
      "gobtc_premium_pct": -0.50,
      "wbtc_premium_pct": -0.20
    }
  ],
  "stats": {
    "avg_gobtc_premium": -0.45,
    "avg_wbtc_premium": -0.18,
    "max_spread": 0.85,
    "min_spread": 0.10
  },
  "hours_requested": 24,
  "timestamp": "2026-01-15T20:00:00Z"
}
```

---

## Gold Miner Metrics

### GET `/gold/miners`

All gold miner quarterly metrics.

**Query Parameters:**
- `limit`: 1-500 (default: 100)

**Response:**
```json
{
  "metrics": [
    {
      "id": 1,
      "company": "Newmont Corporation",
      "ticker": "NEM",
      "period": "2025-Q4",
      "aisc": 1250,
      "production": 1500000,
      "revenue": 3200000000,
      "fcf": 800000000,
      "dividend_yield": 2.5,
      "market_cap": 45000000000,
      "tier1": 60,
      "tier2": 30,
      "tier3": 10
    }
  ],
  "count": 50,
  "timestamp": "2026-01-15T20:00:00Z"
}
```

---

### GET `/gold/miners/latest`

Most recent metrics for each gold mining company.

---

### GET `/gold/miners/stats`

Sector-wide aggregated statistics.

**Response:**
```json
{
  "stats": {
    "average_aisc": 1180,
    "total_production_oz": 25000000,
    "avg_dividend_yield": 2.1,
    "tier1_exposure": 55,
    "company_count": 12
  },
  "timestamp": "2026-01-15T20:00:00Z"
}
```

---

### GET `/gold/miners/{ticker}`

Historical data for specific miner.

**Path Parameters:**
- `ticker`: Stock symbol (e.g., NEM, GOLD, AEM)

---

### POST `/gold/miners`

Submit new quarterly report.

**Request:**
```json
{
  "company": "Newmont Corporation",
  "ticker": "NEM",
  "period": "2026-Q1",
  "aisc": 1200,
  "production": 1550000,
  "revenue": 3400000000,
  "fcf": 900000000,
  "dividend_yield": 2.6,
  "market_cap": 48000000000,
  "tier1": 62,
  "tier2": 28,
  "tier3": 10
}
```

---

### POST `/gold/miners/reseed`

Reset database with seed data (2023-2025).

**Warning:** Deletes all existing data.

---

## Silver Miner Metrics

*Same structure as Gold Miners, under `/silver/miners/*`*

---

## Inflation Data

### GET `/inflation/summary`

Inflation dashboard summary.

**Response:**
```json
{
  "stats": {
    "current_cpi": 315.2,
    "yoy_inflation": 3.2,
    "m2_trillion": 21.5,
    "gold_price": 4500,
    "silver_price": 68.70,
    "dollar_purchasing_power_since_1970": 0.12,
    "gold_1980_peak_adjusted": 3200
  },
  "timestamp": "2026-01-15T20:00:00Z"
}
```

---

### GET `/inflation/data`

Historical inflation data (CPI, M2, metals prices).

**Query Parameters:**
- `start_date`: YYYY-MM format
- `end_date`: YYYY-MM format

---

### GET `/inflation/adjusted/{metal}`

Inflation-adjusted prices in constant dollars.

**Path Parameters:**
- `metal`: "gold" or "silver"

**Query Parameters:**
- `base_year`: 1970-2025 (default: 2024)

**Response:**
```json
{
  "metal": "gold",
  "base_year": 2024,
  "data": [
    {
      "date": "1980-01",
      "nominal_price": 675,
      "adjusted_price": 2800,
      "cpi_then": 77.8,
      "cpi_base": 315.2
    }
  ],
  "count": 540,
  "timestamp": "2026-01-15T20:00:00Z"
}
```

---

### GET `/inflation/m2-comparison`

Gold/silver prices vs M2 money supply.

---

### GET `/inflation/purchasing-power`

Dollar purchasing power decline.

**Query Parameters:**
- `from_year`: 1970-2020 (default: 1970)

---

### POST `/inflation/reseed`

Reset inflation database with historical data.

---

## Central Bank Gold

### GET `/central-banks/summary`

Central bank gold dashboard summary.

**Response:**
```json
{
  "stats": {
    "total_global_holdings_tonnes": 36000,
    "ytd_net_purchases": 800,
    "de_dollarization_score": 72,
    "top_holders": ["USA", "Germany", "Italy", "France", "Russia"]
  },
  "timestamp": "2026-01-15T20:00:00Z"
}
```

---

### GET `/central-banks/leaderboard`

Countries ranked by gold holdings.

**Query Parameters:**
- `limit`: 1-50 (default: 20)

---

### GET `/central-banks/country/{country_code}`

Historical gold holdings for specific country.

**Path Parameters:**
- `country_code`: ISO 3166-1 alpha-2 (e.g., US, CN, RU)

---

### GET `/central-banks/net-purchases`

Global net gold purchases by year.

---

### GET `/central-banks/top-buyers`

Top gold-accumulating countries (12-month).

**Query Parameters:**
- `n`: 1-30 (default: 10)

---

### GET `/central-banks/top-sellers`

Top gold-selling countries (12-month).

---

### GET `/central-banks/dedollarization`

De-dollarization score (0-100).

---

### POST `/central-banks/reseed`

Reset central bank database with seed data.

---

## Earnings Calendar

### GET `/earnings/calendar`

Earnings events for specific month.

**Query Parameters:**
- `month`: YYYY-MM (default: current month)

---

### GET `/earnings/upcoming`

Upcoming earnings in N days.

**Query Parameters:**
- `days`: 1-90 (default: 30)

---

### GET `/earnings/ticker/{ticker}`

Historical earnings for specific company.

---

### GET `/earnings/stats/{ticker}`

Beat/miss statistics for company.

---

### GET `/earnings/sector-stats`

Sector-wide earnings statistics.

**Query Parameters:**
- `metal`: "gold" or "silver" (optional)

---

### POST `/earnings`

Create new earnings event.

---

### PUT `/earnings/{event_id}`

Update earnings event with actual results.

---

### POST `/earnings/reseed`

Reset earnings database with seed data.

---

## Physical Premiums

### GET `/premiums/summary`

Premium tracker dashboard summary.

---

### GET `/premiums/products`

All tracked physical bullion products.

**Query Parameters:**
- `metal`: "gold" or "silver" (optional)

---

### GET `/premiums/products/{product_id}`

Details for specific product.

---

### GET `/premiums/dealers`

List all active dealers.

---

### GET `/premiums/compare/{product_id}`

Price comparison across dealers.

---

### GET `/premiums/best-deals`

Products with lowest current premiums.

---

### GET `/premiums/leaderboard`

Dealers ranked by average premium.

---

### POST `/premiums/price`

Add new price entry.

---

### POST `/premiums/reseed`

Reset premium database with sample data.

---

## Error Handling

All endpoints return consistent error format:

```json
{
  "detail": "Wallet address must be 58 characters",
  "status_code": 400
}
```

**Status Codes:**
| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 409 | Conflict (duplicate) |
| 500 | Server Error |
| 503 | Service Unavailable |

---

## SDK Examples

### Python

```python
import requests

# Analyze wallet
response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    json={
        "address": "YOUR_ALGORAND_ADDRESS",
        "monthly_fixed_expenses": 4000
    }
)
data = response.json()
print(f"Status: {data['sovereignty_data']['status']}")
print(f"Runway: {data['sovereignty_data']['years_of_freedom']:.2f} years")
```

### cURL

```bash
# Analyze wallet
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"address": "YOUR_ADDRESS", "monthly_fixed_expenses": 4000}'

# Get gold/silver ratio
curl "http://localhost:8000/api/v1/gold-silver-ratio"

# Get arbitrage opportunities
curl "http://localhost:8000/api/v1/arbitrage/meld"
```

### JavaScript

```javascript
const analyzeWallet = async (address, expenses) => {
  const response = await fetch('http://localhost:8000/api/v1/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      address,
      monthly_fixed_expenses: expenses
    })
  });
  return response.json();
};
```

---

*Generated: 2026-01-15 | Version: 1.0.0*
