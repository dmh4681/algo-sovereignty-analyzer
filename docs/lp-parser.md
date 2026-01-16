# LP Token Parser Documentation

> Decomposing Algorand DEX LP tokens into underlying assets for accurate sovereignty scoring

## Overview

The LP Parser (`core/lp_parser.py`) extracts the underlying asset values from liquidity pool tokens on Algorand DEXes (Tinyman, Pact, Folks Finance). This is critical for accurate sovereignty scoring because LP tokens contain valuable assets that would otherwise be classified as "shitcoins."

## Why LP Parsing Matters

Consider a user holding `TMPOOL-ALGO-goBTC` LP tokens worth $10,000:

**Without LP Parsing:**
```
Category: shitcoins
Value: $10,000
Sovereignty Impact: Negative (non-hard money)
```

**With LP Parsing:**
```
Category Breakdown:
- ALGO portion: $5,000 → algorand category
- goBTC portion: $5,000 → hard_money category
Sovereignty Impact: Positive (50% hard money)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        LP Token Detection                        │
│  is_lp_token() - Pattern matching on ticker/name                │
│  Patterns: TMPOOL*, TM*POOL*, PACT*, PLP*, *-LP, */            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Pool Info Retrieval                       │
│  get_pool_info() - Fetch LP token metadata from Algorand        │
│  Extract: asset1_ticker, asset2_ticker, creator address         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Pool State Query                          │
│  get_pool_state() - Use Tinyman SDK for accurate reserves       │
│  Returns: total_supply, reserve1, reserve2                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Value Calculation                         │
│  estimate_lp_value() - Calculate user's share of pool           │
│  Formula: (user_lp / total_supply) × (reserve1 + reserve2)      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Component Classification                  │
│  classify_lp_components() - Categorize each underlying asset   │
│  Returns: [(category, asset_dict), (category, asset_dict)]      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Classes and Methods

### LPBreakdown

Data class representing a decomposed LP position.

```python
@dataclass
class LPBreakdown:
    lp_ticker: str       # "TMPOOL-XALGO-ALGO"
    lp_amount: float     # 150.0 (LP tokens held)

    asset1_ticker: str   # "XALGO"
    asset1_amount: float # 2500.0
    asset1_usd: float    # 625.00

    asset2_ticker: str   # "ALGO"
    asset2_amount: float # 2500.0
    asset2_usd: float    # 625.00

    total_usd: float     # 1250.00
```

### LPParser

Main parser class with caching and fallback strategies.

```python
class LPParser:
    def __init__(self, algod_address: str = "https://mainnet-api.algonode.cloud"):
        self.algod_address = algod_address
        self._pool_cache: Dict[int, Dict] = {}  # asset_id → pool info
```

---

## Key Methods

### is_lp_token(ticker, name) → bool

Detect if an asset is an LP token based on naming patterns.

```python
# Patterns detected:
- "TMPOOL*"       # Tinyman V1
- "TM*POOL*"      # Tinyman V2 (TM1.1POOL)
- "PACT*", "PLP*" # Pact Finance
- "*-LP"          # Generic LP suffix
- "*/*"           # Slash notation (xALGO / ALGO)
- "POOL" in name  # Generic pool indicator
```

**Example:**
```python
parser.is_lp_token("TMPOOL11", "TinymanPool2.0 XALGO-ALGO")  # True
parser.is_lp_token("ALGO", "Algorand")                        # False
```

### get_pool_info(asset_id) → Optional[Dict]

Retrieve pool configuration from blockchain.

```python
# Returns:
{
    "asset1_ticker": "XALGO",
    "asset2_ticker": "ALGO",
    "lp_asset_id": 1234567890,
    "creator": "POOL_ADDRESS...",
    "estimated": True  # True if parsed from name
}
```

**Implementation:**
1. Check cache first
2. Fetch asset metadata from Algorand
3. Parse pair from name/unit-name patterns
4. Cache result for future calls

### get_pool_state(pool_address, lp_asset_id, asset1_id, asset2_id) → Optional[Dict]

Query Tinyman SDK for accurate pool reserves.

```python
# Returns:
{
    "total_supply": 1000000.0,  # Total LP tokens in circulation
    "reserve1": 5000000.0,      # Asset 1 in pool
    "reserve2": 5000000.0       # Asset 2 in pool
}
```

**Implementation:**
```python
from tinyman.v2.client import TinymanV2MainnetClient

# Create Tinyman client
tinyman_client = TinymanV2MainnetClient(algod_client=algod_client)

# Fetch pool
pool = tinyman_client.fetch_pool(asset1, asset2)
info = pool.info()

# Extract reserves (accounting for decimals)
total_supply = info['issued_pool_tokens'] / 10**6
reserve1 = info['asset_1_reserves'] / 10**asset1.decimals
reserve2 = info['asset_2_reserves'] / 10**asset2.decimals
```

### estimate_lp_value(lp_ticker, lp_name, lp_amount, asset_id, get_price_fn) → Optional[LPBreakdown]

Calculate the USD value of an LP position using two methods:

**Method 1: Accurate (Tinyman SDK)**
```python
# If pool state is available:
user_share = lp_amount / total_supply
asset1_amount = user_share * reserve1
asset2_amount = user_share * reserve2
total_usd = (asset1_amount * price1) + (asset2_amount * price2)
```

**Method 2: Fallback (Geometric Mean)**
```python
# If Tinyman SDK fails:
lp_token_value = 2 * sqrt(price1 * price2)  # Standard AMM pricing
total_usd = lp_amount * lp_token_value
asset1_usd = total_usd / 2
asset2_usd = total_usd / 2
```

**Example:**
```python
breakdown = parser.estimate_lp_value(
    lp_ticker="TMPOOL11",
    lp_name="TinymanPool2.0 XALGO-ALGO",
    lp_amount=150.0,
    asset_id=1234567890,
    get_price_fn=pricing.get_price
)

# Result:
# LPBreakdown(
#   lp_ticker="TMPOOL11",
#   lp_amount=150.0,
#   asset1_ticker="XALGO", asset1_amount=2500.0, asset1_usd=625.00,
#   asset2_ticker="ALGO", asset2_amount=2500.0, asset2_usd=625.00,
#   total_usd=1250.00
# )
```

### classify_lp_components(breakdown, classify_fn) → List[Tuple[str, Dict]]

Classify the underlying assets of an LP breakdown.

```python
# Input: LPBreakdown for ALGO-goBTC LP
# Output:
[
    ("algorand", {
        "name": "ALGO (from TMPOOL-ALGO-GOBTC)",
        "ticker": "ALGO",
        "amount": 5000.0,
        "usd_value": 1250.00,
        "from_lp": "TMPOOL-ALGO-GOBTC"
    }),
    ("hard_money", {
        "name": "goBTC (from TMPOOL-ALGO-GOBTC)",
        "ticker": "goBTC",
        "amount": 0.0125,
        "usd_value": 1250.00,
        "from_lp": "TMPOOL-ALGO-GOBTC"
    })
]
```

---

## Ticker Normalization

Wrapped and derivative tokens are normalized for pricing:

```python
def _normalize_ticker(ticker: str) -> str:
    # Folks Finance wrapped ALGO variants
    "fALGO", "xALGO", "FALGO", "XALGO" → "ALGO"

    # Folks Finance wrapped stablecoins
    "fUSDC", "FUSDC" → "USDC"
    "fUSDT", "FUSDT" → "USDT"

    # Folks Finance wrapped BTC/ETH
    "fgoBTC", "FGOBTC" → "GOBTC"
    "fgoETH", "FGOETH" → "GOETH"
```

---

## Hardcoded Asset IDs

Fallback mappings for common assets when dynamic resolution fails:

```python
# Algorand Mainnet Asset IDs
ALGO         = 0           # Native ALGO
USDC         = 31566704
USDT         = 312769
xALGO        = 1134696561  # Folks Finance liquid staking
fUSDC        = 3184331239  # Folks Finance wrapped USDC
fALGO        = 3184331013  # Folks Finance wrapped ALGO
goBTC        = 386192725   # Wrapped BTC via glitter.finance
GOLD$        = 1241944285  # Meld Gold token
SILVER$      = 1241945177  # Meld Silver token
```

---

## Integration with Analyzer

The LP Parser integrates with `AlgorandSovereigntyAnalyzer`:

```python
# In analyzer.py
def _process_holdings(self, holdings: List[Dict]) -> Dict[str, List]:
    categories = {"hard_money": [], "algorand": [], "dollars": [], "shitcoins": []}

    for holding in holdings:
        ticker = holding.get("unit-name", "")
        name = holding.get("name", "")

        # Check if LP token
        if self.lp_parser.is_lp_token(ticker, name):
            breakdown = self.lp_parser.estimate_lp_value(
                ticker, name, amount, asset_id, self._get_price
            )

            if breakdown:
                # Classify components separately
                components = self.lp_parser.classify_lp_components(
                    breakdown, self._classify_asset
                )
                for category, asset_dict in components:
                    categories[category].append(asset_dict)
                continue

        # Normal asset classification
        category = self._classify_asset(asset_id, ticker, name)
        categories[category].append(holding)
```

---

## Error Handling

The parser handles various failure scenarios:

1. **Network Failures**: Returns `None`, caller treats as shitcoin
2. **Invalid LP Format**: Returns `None` after logging warning
3. **Missing Prices**: Uses geometric mean with available prices
4. **Zero Pool State**: Falls back to geometric mean estimation
5. **SDK Errors**: Logged and falls back to geometric mean

```python
# Example with fallback chain:
breakdown = parser.estimate_lp_value(...)
if breakdown is None:
    # Treat as unknown shitcoin with face value
    categories["shitcoins"].append(holding)
```

---

## Supported DEXes

| DEX | Detection Pattern | SDK Support |
|-----|-------------------|-------------|
| Tinyman V1 | TMPOOL* | Legacy (limited) |
| Tinyman V2 | TM*POOL*, TinymanPool2.0 | Full (tinyman-py-sdk) |
| Pact Finance | PACT*, PLP* | Pattern only |
| Folks Finance | */* patterns | Pattern only |
| Generic | *-LP, POOL in name | Pattern only |

---

## Performance Considerations

1. **Caching**: Pool info cached per asset_id
2. **Lazy SDK**: Tinyman SDK only imported when needed
3. **Timeout**: 10s for blockchain queries, 5s for account lookups
4. **Batch Friendly**: Cache persists across multiple calls

---

## Testing

```python
# Test LP detection
def test_is_lp_token():
    parser = LPParser()
    assert parser.is_lp_token("TMPOOL11", "TinymanPool2.0 ALGO-USDC") == True
    assert parser.is_lp_token("ALGO", "Algorand") == False
    assert parser.is_lp_token("PLP-ALGO-USDC", "Pact LP") == True

# Test value estimation
def test_estimate_lp_value():
    parser = LPParser()
    breakdown = parser.estimate_lp_value(
        "TMPOOL11", "TinymanPool2.0 ALGO-USDC",
        100.0, 123456789,
        lambda ticker, asset_id: 0.25 if ticker == "ALGO" else 1.0
    )
    assert breakdown is not None
    assert breakdown.total_usd > 0
```

---

*Last Updated: 2026-01-15*
