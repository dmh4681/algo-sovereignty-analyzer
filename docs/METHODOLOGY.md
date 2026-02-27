# Sovereignty Scoring Methodology

> A deep dive into the mathematical formulas, philosophical foundations, and practical implementation of sovereignty scoring in the Algorand Sovereignty Analyzer.

---

## Table of Contents

1. [Philosophy: Why Hard Money?](#philosophy-why-hard-money)
2. [The Sovereignty Ratio Formula](#the-sovereignty-ratio-formula)
3. [Asset Classification Hierarchy](#asset-classification-hierarchy)
4. [Status Level Thresholds](#status-level-thresholds)
5. [LP Token Decomposition](#lp-token-decomposition)
6. [Mathematical Examples](#mathematical-examples)
7. [Implementation Details](#implementation-details)

---

## Philosophy: Why Hard Money?

### The Core Thesis

The Algorand Sovereignty Analyzer is built on a fundamental observation:

> **Not all assets are equal in their ability to preserve purchasing power across time.**

Throughout human history, only three asset classes have consistently maintained value across centuries, empires, and monetary regimes:

1. **Gold** - 5,000+ years of monetary history
2. **Silver** - 4,000+ years as money
3. **Bitcoin** - Digital scarcity (21 million cap), 15+ years of price appreciation

### Why These Three?

| Asset | Scarcity Mechanism | Key Property |
|-------|-------------------|--------------|
| **Gold** | Geological (mining is hard) | Cannot be printed, ~2% annual supply growth |
| **Silver** | Geological + Industrial demand | Monetary metal + industrial consumption |
| **Bitcoin** | Cryptographic (halving events) | Mathematically enforced 21M cap |

### What Disqualifies Other Assets?

| Asset Type | Problem | Risk |
|------------|---------|------|
| **Fiat Currency** | Unlimited supply | Inflation erodes value (USD lost 96% since 1913) |
| **Stablecoins** | Pegged to fiat | Inherit fiat's inflation problem |
| **Altcoins** | Variable supply, governance risk | Can change monetary policy anytime |
| **Stocks** | Dilution, regulatory risk | Companies can issue more shares |
| **Real Estate** | Property taxes, illiquid | Never truly "owned" (try not paying taxes) |

### The Sovereignty Lens

We view assets through the lens of **"years of freedom"**:

> If you lost all income tomorrow, how many years could you maintain your lifestyle using ONLY assets that governments cannot debase?

This is the essence of financial sovereignty.

---

## The Sovereignty Ratio Formula

### Core Formula

```
Sovereignty Ratio = Total Portfolio Value (USD) / Annual Fixed Expenses (USD)
```

Where:
- **Total Portfolio Value** = Sum of all asset categories (hard_money + algo + dollars + shitcoin)
- **Annual Fixed Expenses** = Monthly Fixed Expenses × 12

### Why Use Total Portfolio (Not Just Hard Money)?

While hard money assets are the foundation of sovereignty, we include the full portfolio because:

1. **Practical reality**: You can convert other assets to hard money
2. **Liquidity matters**: Stablecoins provide immediate spending power
3. **Optionality**: ALGO and other assets have utility value

However, the philosophy emphasizes **converting speculative assets to hard money over time**.

### Fixed Expenses Definition

Fixed expenses are costs you **cannot easily reduce**:

| Include | Exclude |
|---------|---------|
| Rent/Mortgage | Entertainment |
| Utilities (electric, water, gas) | Dining out |
| Insurance (health, auto, home) | Subscriptions |
| Minimum debt payments | Discretionary shopping |
| Property taxes | Travel |
| Basic food | Luxury items |

The goal is to measure: **"How long can I survive if I cut everything non-essential?"**

---

## Asset Classification Hierarchy

### The Four Categories

Assets are classified into four categories, ordered by sovereignty value:

#### 1. Hard Money (Highest Sovereignty Value)

```python
HARD_MONEY_ASSETS = {
    # Bitcoin representations on Algorand
    'goBTC': 386192725,    # Wrapped BTC via Algomint
    'WBTC': ...,           # Wrapped Bitcoin
    'aBTC': ...,           # Algorand bridged BTC

    # Gold representations
    'GOLD$': 1241944285,   # Meld Gold
    'XAUT': ...,           # Tether Gold
    'PAXG': ...,           # Paxos Gold

    # Silver representations
    'SILVER$': 1241945177, # Meld Silver
}
```

**Classification criteria**:
- Represents physical Bitcoin, Gold, or Silver
- Has verifiable backing/reserves
- Cannot have supply arbitrarily increased

#### 2. Algorand Native (Medium-High Sovereignty Value)

```python
ALGO_ASSETS = {
    'ALGO': 0,             # Native ALGO
    'xALGO': 1134696561,   # Liquid staking
    'fALGO': ...,          # Folks Finance ALGO
    'gALGO': ...,          # Governance ALGO
    'mALGO': ...,          # Messina staked ALGO
    'lALGO': ...,          # Lofty staked ALGO
    'tALGO': ...,          # Tinyman staked ALGO
}
```

**Why ALGO is semi-sovereign**:
- Fixed supply cap (10 billion)
- No inflation beyond distribution schedule
- Proof-of-Stake with participation rewards
- Native blockchain asset

#### 3. Dollars (Low Sovereignty Value)

```python
DOLLAR_ASSETS = {
    'USDC': 31566704,      # Circle USD Coin
    'USDT': ...,           # Tether
    'DAI': ...,            # MakerDAO stablecoin
    'fUSDC': ...,          # Folks Finance wrapped USDC
    'fUSDT': ...,          # Folks Finance wrapped USDT
}
```

**Why dollars are counted but not "sovereign"**:
- Provide liquidity and spending power
- Subject to inflation of underlying fiat
- Counterparty risk (issuer can freeze)
- Useful for short-term expenses

#### 4. Shitcoins (Zero Sovereignty Value)

Everything else:
- Governance tokens
- Meme coins
- NFTs
- LP tokens (before decomposition)
- Reward tokens
- Any unclassified ASA

**Philosophy**: These assets may have speculative value but do not contribute to long-term financial sovereignty.

### Classification Priority Order

```
1. CSV Manual Override (data/asset_classification.csv)
   ↓ (if not found)
2. User Corrections (data/user_corrections.json)
   ↓ (if not found)
3. Regex Pattern Matching (core/classifier.py)
   ↓ (if no match)
4. Default: 'shitcoin'
```

---

## Status Level Thresholds

### The Five Sovereignty Levels

| Level | Ratio | Years | Emoji | Meaning |
|-------|-------|-------|-------|---------|
| **Generationally Sovereign** | ≥20 | 20+ | Green Square | Multigenerational wealth |
| **Antifragile** | ≥6 | 6-20 | Green Circle | Benefits from volatility |
| **Robust** | ≥3 | 3-6 | Yellow Circle | Can weather major storms |
| **Fragile** | ≥1 | 1-3 | Red Circle | Building foundation |
| **Vulnerable** | <1 | <1 | Black Circle | Immediate action needed |

### Threshold Rationale

#### Vulnerable (< 1 year)
- Cannot survive a single year without income
- High stress from financial pressure
- Forced to accept unfavorable terms

#### Fragile (1-3 years)
- Basic runway established
- Can survive job loss or health issue
- Still dependent on regular income

#### Robust (3-6 years)
- Significant buffer against uncertainty
- Can take career risks
- Time to pivot if needed

#### Antifragile (6-20 years)
- Named after Nassim Taleb's concept
- Benefits from volatility (can buy dips)
- True optionality in life decisions

#### Generationally Sovereign (20+ years)
- Wealth that outlasts a career
- Can focus on legacy building
- True financial independence

### Status Determination Code

```python
def determine_status(sovereignty_ratio: float) -> str:
    """
    Determine sovereignty status from ratio.

    The thresholds are chosen based on:
    - 1 year: Minimum viable runway
    - 3 years: Average recession length
    - 6 years: Longest post-war recession + buffer
    - 20 years: Generational time horizon
    """
    if sovereignty_ratio >= 20:
        return "Generationally Sovereign"
    elif sovereignty_ratio >= 6:
        return "Antifragile"
    elif sovereignty_ratio >= 3:
        return "Robust"
    elif sovereignty_ratio >= 1:
        return "Fragile"
    else:
        return "Vulnerable"
```

---

## LP Token Decomposition

### The Problem

LP (Liquidity Provider) tokens represent a share of a DEX pool. A user holding `ALGO-goBTC LP` tokens actually owns:
- Some amount of ALGO
- Some amount of goBTC (Bitcoin)

Without decomposition, the entire LP position would be classified as "shitcoin", losing the hard money value of the goBTC component.

### The Solution: LP Parsing

```
User holds: 100 ALGO-goBTC LP tokens
    ↓
LP Parser queries pool state
    ↓
Decomposed to:
  - 500 ALGO → 'algo' category
  - 0.005 goBTC → 'hard_money' category
```

### Calculation Methods

#### Method 1: Tinyman SDK (Accurate)

When pool state is available:

```python
# Get pool reserves from Tinyman V2
total_lp_supply = pool.info()['issued_pool_tokens']
reserve_asset1 = pool.info()['asset_1_reserves']
reserve_asset2 = pool.info()['asset_2_reserves']

# Calculate user's share
user_share = user_lp_amount / total_lp_supply

# User's portion of each asset
user_asset1 = user_share * reserve_asset1
user_asset2 = user_share * reserve_asset2
```

#### Method 2: Geometric Mean (Fallback)

When pool state unavailable, use standard AMM formula:

```python
# Value of 1 LP token using constant product formula
lp_token_value = 2 * sqrt(price_asset1 * price_asset2)

# Total position value
total_value = lp_amount * lp_token_value

# Split 50/50 between assets (approximation)
asset1_value = total_value / 2
asset2_value = total_value / 2
```

### Supported DEXes

| DEX | LP Token Pattern | Method |
|-----|-----------------|--------|
| Tinyman V2 | `TMPOOL2`, `TinymanPool2.0` | SDK (accurate) |
| Tinyman V1 | `TM1POOL`, `TMPOOL` | Geometric mean |
| Pact | `PACT LP`, `PLP` | Geometric mean |
| Humble | `hLP`, `-LP` | Geometric mean |

---

## Mathematical Examples

### Example 1: Basic Sovereignty Calculation

**Input**:
- Monthly fixed expenses: $4,000
- Holdings:
  - 0.1 goBTC @ $100,000 = $10,000
  - 10 oz GOLD$ @ $2,000 = $20,000
  - 50,000 ALGO @ $0.30 = $15,000
  - 5,000 USDC = $5,000
  - Various shitcoins = $500

**Calculation**:
```
Total Portfolio = $10,000 + $20,000 + $15,000 + $5,000 + $500 = $50,500
Annual Expenses = $4,000 × 12 = $48,000
Sovereignty Ratio = $50,500 / $48,000 = 1.05
Status = "Fragile" (≥1 but <3)
```

**Interpretation**: This portfolio can cover 1.05 years of fixed expenses. The user is in the "Fragile" zone, meaning they have basic runway but should continue building hard money reserves.

### Example 2: LP Token Impact

**Without LP Decomposition**:
```
Holdings:
- 100 ALGO-goBTC LP tokens → classified as 'shitcoin' ($1,000)
- 1,000 ALGO → 'algo' ($300)

Total "sovereign-adjacent": $300
```

**With LP Decomposition**:
```
LP tokens decomposed:
- 500 ALGO → 'algo' ($150)
- 0.005 goBTC → 'hard_money' ($500)

Plus direct holdings:
- 1,000 ALGO → 'algo' ($300)

Total hard_money: $500
Total algo: $450
```

The sovereignty picture is dramatically different when LP tokens are properly decomposed.

### Example 3: Status Level Progression

**Current situation**:
- Ratio: 2.5 (Fragile)
- Portfolio: $120,000
- Annual expenses: $48,000

**To reach Robust (3.0)**:
```
Needed ratio = 3.0
Needed portfolio = 3.0 × $48,000 = $144,000
Gap = $144,000 - $120,000 = $24,000
```

At ALGO price of $0.30: Need ~80,000 more ALGO (or equivalent in hard money).

---

## Implementation Details

### Core Classes

#### `AlgorandSovereigntyAnalyzer` (core/analyzer.py)

Main orchestrator class that:
1. Fetches wallet data from Algorand blockchain
2. Classifies each asset using `AssetClassifier`
3. Decomposes LP tokens using `LPParser`
4. Calculates sovereignty metrics
5. Exports results to JSON

Key method signature:
```python
def calculate_sovereignty_metrics(
    self,
    categories: Dict[str, List[Dict[str, Any]]],
    monthly_fixed_expenses: float
) -> Optional[SovereigntyData]
```

#### `AssetClassifier` (core/classifier.py)

Handles asset categorization with priority:
1. CSV overrides
2. User corrections
3. Regex patterns

Key patterns:
```python
HARD_MONEY_PATTERNS = [
    r"(?i)^(go)?btc",           # goBTC, BTC
    r"(?i)gold|xaut|paxg",      # Gold tokens
    r"(?i)silver",              # Silver tokens
]
```

#### `LPParser` (core/lp_parser.py)

Decomposes LP tokens:
1. Detects LP tokens by naming patterns
2. Fetches pool state via Tinyman SDK
3. Calculates user's share of reserves
4. Returns `LPBreakdown` dataclass

### Data Flow

```
User Input (address, expenses)
         ↓
┌─────────────────────────────────────┐
│        analyze_wallet()             │
│  1. Fetch account from blockchain   │
│  2. For each asset:                 │
│     a. Get asset details            │
│     b. Check if LP token            │
│        - Yes: Decompose via LPParser│
│        - No: Classify directly      │
│     c. Get price from Vestige       │
│     d. Add to appropriate category  │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│   calculate_sovereignty_metrics()   │
│  1. Sum all category USD values     │
│  2. Calculate annual expenses       │
│  3. Compute ratio                   │
│  4. Determine status level          │
└─────────────────────────────────────┘
         ↓
SovereigntyData {
    sovereignty_ratio: 2.5,
    sovereignty_status: "Fragile",
    years_of_runway: 2.5,
    portfolio_usd: 120000.0,
    ...
}
```

### Configuration

Key thresholds in `core/analyzer.py`:
```python
class AlgorandSovereigntyAnalyzer:
    # Minimum USD to include (filters dust)
    DUST_THRESHOLD_USD = 10.0

    # Maximum amount for NFT detection
    NFT_MAX_AMOUNT = 10

    # Pagination settings
    DEFAULT_PAGE_SIZE = 20
    PAGINATION_THRESHOLD = 50
```

---

## Extending the Methodology

### Adding New Hard Money Assets

1. Add to `data/asset_classification.csv`:
   ```csv
   asset_id,category,name,ticker
   NEW_ASSET_ID,hard_money,New Gold Token,NGOLD
   ```

2. Or add regex pattern to `core/classifier.py`:
   ```python
   HARD_MONEY_PATTERNS.append(r"(?i)ngold")
   ```

### Custom Status Thresholds

Modify `calculate_sovereignty_metrics()` in `core/analyzer.py`:
```python
# Custom thresholds for different risk profiles
CONSERVATIVE_THRESHOLDS = {
    'generational': 25,  # More conservative
    'antifragile': 10,
    'robust': 5,
    'fragile': 2,
}
```

### Adding New LP DEXes

In `core/lp_parser.py`, add detection pattern:
```python
def is_lp_token(self, ticker: str, name: str) -> bool:
    # Add new DEX pattern
    if 'NEWDEX' in ticker_upper:
        return True
```

---

## References

- [Bitcoin Whitepaper](https://bitcoin.org/bitcoin.pdf) - Satoshi Nakamoto
- [The Bitcoin Standard](https://saifedean.com/thebitcoinstandard/) - Saifedean Ammous
- [Antifragile](https://www.penguinrandomhouse.com/books/176227/antifragile-by-nassim-nicholas-taleb/) - Nassim Nicholas Taleb
- [Algorand Documentation](https://developer.algorand.org/)
- [Tinyman SDK](https://github.com/tinymanorg/tinyman-py-sdk)

---

*Last Updated: 2026-01-25*
