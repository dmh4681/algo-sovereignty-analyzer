# Asset Classification System

## Philosophy: Hard Money Maximalism

The Algo Sovereignty Analyzer follows **hard money maximalist** principles:

> Only assets with provable scarcity and historical store-of-value properties count toward financial sovereignty.

### What is "Hard Money"?

Hard money refers to assets that:
1. Cannot be arbitrarily created or inflated
2. Have thousands of years of monetary history (gold, silver) OR
3. Have mathematically enforced scarcity (Bitcoin)
4. Maintain purchasing power across generations

### The Four Categories

| Category | Assets | Philosophy |
|----------|--------|------------|
| **Hard Money** | BTC, Gold, Silver | True sovereignty assets |
| **Algo** | ALGO, xALGO, staking | Platform native, not hard money |
| **Dollars** | USDC, USDT, DAI | Fiat exposure, useful but not sovereign |
| **Shitcoin** | Everything else | Speculation, not sovereignty |

## Classification Hierarchy

Assets are classified using a three-tier priority system:

```
┌─────────────────────────────────────────────────────┐
│  1. CSV Manual Overrides (HIGHEST PRIORITY)         │
│     data/asset_classification.csv                   │
│     - Admin-curated, reviewed classifications       │
├─────────────────────────────────────────────────────┤
│  2. User Corrections (MEDIUM PRIORITY)              │
│     data/user_corrections.json                      │
│     - Community-submitted corrections               │
│     - Applied immediately, reviewed later           │
├─────────────────────────────────────────────────────┤
│  3. Auto-Classification (LOWEST PRIORITY)           │
│     core/classifier.py                              │
│     - Regex patterns on name/ticker                 │
│     - Fallback when no manual override exists       │
└─────────────────────────────────────────────────────┘
```

## Hard Money Assets

### Bitcoin (BTC)
```python
# Recognized Bitcoin tokens on Algorand
HARD_MONEY_BTC = [
    'goBTC',      # Wrapped BTC via go-algo
    'wBTC',       # Wrapped BTC
    'BTC',        # Native (if exists)
    'aBTC',       # Algorand wrapped BTC
]
```

### Gold
```python
# Recognized Gold tokens
HARD_MONEY_GOLD = [
    'GOLD$',      # Meld Gold
    'XAUT',       # Tether Gold
    'PAXG',       # Pax Gold
    'GOLD',       # Generic gold tokens
    'MCAU',       # Perth Mint Gold
]

# Conversion: 1 GOLD$ = 1 gram = 1/31.1035 troy oz
```

### Silver
```python
# Recognized Silver tokens
HARD_MONEY_SILVER = [
    'SILVER$',    # Meld Silver
    'SLVR',       # Silver tokens
    'SILV',       # Silver tokens
]

# Conversion: 1 SILVER$ = 1 gram = 1/31.1035 troy oz
```

## Algo Category

Native Algorand and liquid staking derivatives:

```python
ALGO_TOKENS = [
    'ALGO',       # Native (ASA 0)
    'xALGO',      # Folks Finance staking
    'fALGO',      # Folks Finance
    'gALGO',      # Governance ALGO
    'mALGO',      # Messina staking
    'lALGO',      # Liquid staking
    'tALGO',      # Tinyman staking
]
```

**Why separate from Hard Money?**
- ALGO has no fixed supply cap
- Inflationary tokenomics (though declining)
- Platform risk (single blockchain)
- Not multi-generational store of value (yet)

## Dollar Category

Stablecoins pegged to fiat currencies:

```python
STABLECOINS = [
    'USDC',       # Circle USD Coin
    'USDT',       # Tether
    'USDt',       # Tether (alternate)
    'DAI',        # MakerDAO
    'BUSD',       # Binance USD
    'TUSD',       # TrueUSD
    'fUSDC',      # Folks Finance wrapped
    'fUSDT',      # Folks Finance wrapped
    'gUSD',       # Gemini Dollar
]
```

**Why track separately?**
- Useful for liquidity and transactions
- Subject to inflation (purchasing power erosion)
- Counterparty risk (issuer can freeze)
- Not sovereign wealth

## Shitcoin Category

Everything else falls here:

- **LP Tokens** - Decomposed into underlying assets first
- **Governance Tokens** - Protocol tokens (DEFLY, VEST, etc.)
- **NFTs** - Filtered out (dust detection)
- **Reward Tokens** - Airdrops, incentives
- **Unknown ASAs** - Unclassified tokens

### Dust Filtering

Small holdings are filtered to reduce noise:

```python
DUST_THRESHOLD_USD = 10.0  # Minimum USD value
NFT_MAX_AMOUNT = 10        # Max for NFT detection

def is_dust_or_nft(amount, usd_value, price, name):
    # NFT: small integer with no price
    if amount <= NFT_MAX_AMOUNT and amount == int(amount) and price is None:
        return True

    # Dust: negligible value
    if usd_value < 1.0:
        return True

    # Spam: reward/airdrop tokens under threshold
    if usd_value < DUST_THRESHOLD_USD:
        if any(kw in name.lower() for kw in ['reward', 'airdrop', 'free']):
            return True

    return False
```

## LP Token Decomposition

LP (Liquidity Provider) tokens are automatically decomposed:

```
User holds: 100 ALGO/USDC LP tokens
          ↓
System decomposes to:
  - 50 ALGO → "algo" category
  - 50 USDC → "dollars" category
```

### Supported DEXs

| DEX | LP Format | Status |
|-----|-----------|--------|
| Tinyman v1 | TM1POOL | Supported |
| Tinyman v2 | TMPOOL2 | Supported |
| Pact | PACT LP | Supported |
| Humble | hLP | Supported |
| Algofi | AF-POOL | Supported |

### Decomposition Logic

See `core/lp_parser.py` for full implementation:

```python
class LPParser:
    def decompose_lp_token(self, asset_id: int, amount: float):
        """
        1. Identify LP token type (Tinyman, Pact, etc.)
        2. Fetch pool composition from DEX
        3. Calculate user's share of each asset
        4. Return decomposed holdings
        """
```

## Auto-Classification Patterns

When no manual override exists, regex patterns classify:

```python
# Hard Money patterns
HARD_MONEY_PATTERNS = [
    r'^go?BTC',           # goBTC, gBTC
    r'^w?BTC',            # wBTC, BTC
    r'GOLD\$?',           # GOLD, GOLD$
    r'SILVER\$?',         # SILVER, SILVER$
    r'^XAUT$',            # Tether Gold
    r'^PAXG$',            # Pax Gold
]

# Dollar patterns
DOLLAR_PATTERNS = [
    r'^f?USDC$',          # USDC, fUSDC
    r'^f?USDt?$',         # USDT, fUSDT
    r'^DAI$',
    r'^BUSD$',
]

# Algo patterns
ALGO_PATTERNS = [
    r'^[xfgmlt]?ALGO$',   # ALGO, xALGO, fALGO, etc.
]
```

## User Corrections API

Users can submit classification corrections:

```bash
# Submit correction
curl -X POST http://localhost:8000/api/v1/corrections \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "123456789",
    "asset_name": "New BTC Wrapper",
    "ticker": "nBTC",
    "original_category": "shitcoin",
    "corrected_category": "hard_money",
    "reason": "This is a legitimate wrapped Bitcoin"
  }'

# View all corrections
curl http://localhost:8000/api/v1/corrections

# View correction stats
curl http://localhost:8000/api/v1/corrections/stats
```

### Correction Workflow

1. User submits correction via API
2. Correction is immediately **active** (applied to classification)
3. Admin reviews corrections periodically
4. Approved corrections promoted to CSV
5. Rejected corrections marked as rejected

## Sovereignty Ratio Calculation

```python
def calculate_sovereignty_ratio(categories, annual_expenses):
    """
    Sovereignty Ratio = Total Hard Money Value / Annual Fixed Expenses

    Only HARD MONEY counts toward sovereignty:
    - BTC, Gold, Silver

    Algo, Dollars, Shitcoins do NOT count.
    """
    hard_money_value = sum(
        asset['value_usd']
        for asset in categories['hard_money']
    )

    return hard_money_value / annual_expenses
```

### Status Thresholds

| Ratio | Status | Meaning |
|-------|--------|---------|
| >= 20 | Generationally Sovereign | 20+ years of expenses in hard money |
| >= 6 | Antifragile | Benefits from volatility |
| >= 3 | Robust | Can weather major storms |
| >= 1 | Fragile | Building reserves |
| < 1 | Vulnerable | Less than 1 year coverage |

## Adding New Classifications

### Via CSV (Recommended for Admin)

Edit `data/asset_classification.csv`:

```csv
asset_id,name,ticker,category,notes
NEW_ASA_ID,New Token,NTKN,hard_money,Reason for classification
```

### Via User Correction (Community)

```bash
curl -X POST http://localhost:8000/api/v1/corrections \
  -d '{"asset_id": "NEW_ASA_ID", ...}'
```

### Via Code (New Patterns)

Edit `core/classifier.py`:

```python
# Add to appropriate pattern list
HARD_MONEY_PATTERNS.append(r'^newBTC$')
```
