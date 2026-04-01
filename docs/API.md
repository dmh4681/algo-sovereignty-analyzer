# Algorand Sovereignty Analyzer API Documentation

## Base URL
- Development: `http://localhost:8000`
- Production: TBD

## Authentication
None required (public API)

## Rate Limiting
- 15-minute cache per wallet address
- Respects CoinGecko API rate limits (50 calls/minute)

## Endpoints

### POST /api/v1/analyze
Analyze an Algorand wallet and calculate sovereignty metrics.

**Request Body:**
```json
{
  "address": "I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4",
  "monthly_fixed_expenses": 4000 
}
```
*Note: `monthly_fixed_expenses` is optional. If omitted, sovereignty metrics (runway, ratio) will be null.*

**Response:**
```json
{
  "address": "I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4",
  "is_participating": true,
  "hard_money_algo": 121118.99,
  "categories": {
    "hard_money": [
      {
        "name": "Algorand (PARTICIPATING)",
        "ticker": "ALGO",
        "amount": 121118.99,
        "usd_value": 16487.08
      }
    ],
    "productive": [
      {
        "name": "TinymanPool2.0 goBTC-ALGO",
        "ticker": "TMPOOL2",
        "amount": 73.2,
        "usd_value": 0
      }
    ],
    "nft": [],
    "shitcoin": []
  },
  "sovereignty_data": {
    "monthly_fixed_expenses": 4000,
    "annual_fixed_expenses": 48000,
    "algo_price": 0.1361,
    "portfolio_usd": 16487.08,
    "sovereignty_ratio": 0.34,
    "sovereignty_status": "Vulnerable ⚫",
    "years_of_runway": 0.3
  }
}
```

### GET /api/v1/classifications
Returns manual asset classification overrides.

**Response:**
```json
{
  "123456": {
    "name": "Special Token",
    "ticker": "SPEC",
    "category": "hard_money"
  }
}
```

## Error Codes
- **404**: Wallet not found or has no assets.
- **500**: Internal server error (e.g., node connection failure).
