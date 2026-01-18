# Algo Sovereignty API Reference

## Overview

The Algo Sovereignty Analyzer API is built with FastAPI and provides endpoints for analyzing Algorand wallet sovereignty, managing classification corrections, and accessing historical data.

**Base URL:** `http://localhost:8000/api/v1`

## Authentication

Currently, the API is open (no authentication required). For production deployment, add API key authentication.

---

## Endpoints

### Wallet Analysis

#### `POST /analyze`
Analyze an Algorand wallet's sovereignty score.

**Request Body:**
```json
{
  "address": "ABC123...XYZ",
  "monthly_fixed_expenses": 4000
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `address` | string | Yes | 58-character Algorand address |
| `monthly_fixed_expenses` | number | No | Monthly fixed expenses in USD (default: 4000) |

**Response:**
```json
{
  "address": "ABC123...XYZ",
  "sovereignty_ratio": 3.25,
  "sovereignty_status": "robust",
  "total_usd_value": 156000,
  "annual_fixed_expenses": 48000,
  "years_of_sovereignty": 3.25,
  "categories": {
    "hard_money": [
      {
        "asset_id": 0,
        "name": "goBTC",
        "ticker": "goBTC",
        "amount": 0.5,
        "price_usd": 95000,
        "value_usd": 47500,
        "category": "hard_money"
      }
    ],
    "algo": [...],
    "dollars": [...],
    "shitcoin": [...]
  },
  "allocation_percentages": {
    "hard_money": 30.5,
    "algo": 25.0,
    "dollars": 20.0,
    "shitcoin": 24.5
  },
  "timestamp": "2026-01-18T12:00:00Z"
}
```

**Sovereignty Status Levels:**
| Status | Ratio | Meaning |
|--------|-------|---------|
| `generationally_sovereign` | >= 20 | Multi-generational wealth |
| `antifragile` | >= 6 | Benefits from volatility |
| `robust` | >= 3 | Can weather storms |
| `fragile` | >= 1 | Building reserves |
| `vulnerable` | < 1 | Needs immediate action |

---

### AI Coaching

#### `POST /agent/advice`
Get AI coaching advice based on wallet analysis.

**Request Body:**
```json
{
  "address": "ABC123...XYZ",
  "question": "How should I improve my sovereignty ratio?",
  "monthly_fixed_expenses": 4000
}
```

**Response:**
```json
{
  "advice": "Based on your current allocation of 30% hard money...",
  "sovereignty_context": {
    "ratio": 3.25,
    "status": "robust",
    "hard_money_percent": 30.5
  }
}
```

---

### Asset Classification

#### `GET /classifications`
Get classification for a specific asset.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `asset_id` | string | The ASA ID to look up |

**Response:**
```json
{
  "asset_id": "123456789",
  "name": "goBTC",
  "ticker": "goBTC",
  "category": "hard_money",
  "source": "csv"
}
```

---

### Classification Corrections

#### `POST /corrections`
Submit a classification correction.

**Request Body:**
```json
{
  "asset_id": "123456789",
  "asset_name": "Example Token",
  "ticker": "EXT",
  "original_category": "shitcoin",
  "corrected_category": "hard_money",
  "reason": "This is a wrapped Bitcoin token",
  "submitted_by": "ABC123..."
}
```

**Valid Categories:** `hard_money`, `algo`, `dollars`, `shitcoin`

**Response:**
```json
{
  "success": true,
  "message": "Correction submitted for EXT (123456789)",
  "correction": {
    "asset_id": "123456789",
    "asset_name": "Example Token",
    "ticker": "EXT",
    "original_category": "shitcoin",
    "corrected_category": "hard_money",
    "reason": "This is a wrapped Bitcoin token",
    "submitted_at": "2026-01-18T12:00:00Z",
    "status": "active"
  }
}
```

#### `GET /corrections`
List all corrections.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status: active, pending, approved, rejected |

**Response:**
```json
{
  "corrections": [...],
  "count": 5
}
```

#### `GET /corrections/stats`
Get correction system statistics.

**Response:**
```json
{
  "total_corrections": 15,
  "active_corrections": 10,
  "pending_corrections": 2,
  "approved_corrections": 3,
  "rejected_corrections": 0,
  "most_corrected_category": "hard_money",
  "recent_corrections": [...]
}
```

#### `GET /corrections/{asset_id}`
Get correction for a specific asset.

#### `DELETE /corrections/{asset_id}`
Delete a correction.

#### `GET /corrections/export/csv`
Export approved corrections in CSV format.

**Response:**
```json
{
  "csv": "asset_id,name,ticker,category,notes\n123,Token,TKN,hard_money,User correction",
  "instructions": "Add approved lines to data/asset_classification.csv"
}
```

---

### Historical Data

#### `POST /history/save`
Save a wallet snapshot.

**Request Body:**
```json
{
  "address": "ABC123...XYZ",
  "analysis_result": {...}
}
```

**Response:**
```json
{
  "success": true,
  "message": "Snapshot saved",
  "snapshot_date": "2026-01-18"
}
```

#### `GET /history/{address}`
Get historical snapshots for an address.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `days` | int | Number of days to look back (default: 365) |

**Response:**
```json
{
  "address": "ABC123...XYZ",
  "snapshots": [
    {
      "date": "2026-01-18",
      "sovereignty_ratio": 3.25,
      "total_usd": 156000,
      "hard_money_percent": 30.5
    }
  ],
  "count": 30
}
```

---

### Network Statistics

#### `GET /network/stats`
Get Algorand network statistics.

**Response:**
```json
{
  "online_stake": 2500000000,
  "total_supply": 10000000000,
  "participation_rate": 0.25,
  "current_round": 35000000,
  "timestamp": "2026-01-18T12:00:00Z"
}
```

---

### Price Data

#### `GET /prices/bitcoin`
Get current Bitcoin spot price.

**Response:**
```json
{
  "price_usd": 95000,
  "source": "coingecko",
  "timestamp": "2026-01-18T12:00:00Z"
}
```

#### `GET /prices/gold`
Get current gold price per ounce.

#### `GET /prices/silver`
Get current silver price per ounce.

#### `GET /meld/arbitrage`
Get Meld gold/silver arbitrage opportunities.

**Response:**
```json
{
  "gold": {
    "spot_price": 2650,
    "meld_price": 2680,
    "premium_percent": 1.13,
    "opportunity": "slight_premium"
  },
  "silver": {
    "spot_price": 32.50,
    "meld_price": 33.00,
    "premium_percent": 1.54,
    "opportunity": "slight_premium"
  },
  "gsr": {
    "ratio": 81.5,
    "historical_avg": 60,
    "signal": "silver_undervalued"
  },
  "timestamp": "2026-01-18T12:00:00Z"
}
```

---

### Premium Tracking

#### `GET /premiums`
Get historical premium data.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `asset` | string | gold, silver, or bitcoin |
| `days` | int | Days of history (default: 30) |

#### `POST /premiums`
Add premium data point.

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Status Codes:**
| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Request body invalid |
| 500 | Server Error - Internal error |

---

## Data Models

### AssetCategory
```python
class AssetCategory(str, Enum):
    HARD_MONEY = "hard_money"   # BTC, Gold, Silver
    ALGO = "algo"              # ALGO, xALGO, etc.
    DOLLARS = "dollars"        # Stablecoins
    SHITCOIN = "shitcoin"      # Everything else
```

### SovereigntyStatus
```python
VULNERABILITY = "vulnerable"      # ratio < 1
FRAGILE = "fragile"              # 1 <= ratio < 3
ROBUST = "robust"                # 3 <= ratio < 6
ANTIFRAGILE = "antifragile"      # 6 <= ratio < 20
GENERATIONALLY_SOVEREIGN = "generationally_sovereign"  # ratio >= 20
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/analyze` | 30/minute |
| `/agent/advice` | 10/minute |
| All others | 100/minute |

---

## Caching

- Wallet analysis cached for 15 minutes per address
- Price data cached for 5 minutes
- Network stats cached for 1 minute
