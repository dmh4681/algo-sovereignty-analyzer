# Core Analyzer Documentation

> AlgorandSovereigntyAnalyzer - Main wallet analysis engine

## Overview

The `AlgorandSovereigntyAnalyzer` class (`core/analyzer.py`) is the heart of the sovereignty scoring system. It:

1. Fetches wallet holdings from Algorand blockchain
2. Classifies each asset into sovereignty categories
3. Decomposes LP tokens into underlying assets
4. Calculates sovereignty metrics and status

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AlgorandSovereigntyAnalyzer                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ AssetClassifier  │    │    LPParser      │                   │
│  │ (classifier.py)  │    │  (lp_parser.py)  │                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                              │
│           ▼                       ▼                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    analyze_wallet()                          ││
│  │                                                              ││
│  │  1. Fetch account data from Algorand                        ││
│  │  2. Process native ALGO (check participation)               ││
│  │  3. Loop through ASAs:                                      ││
│  │     - Get asset details (decimals, name, ticker)            ││
│  │     - Check if LP token → decompose                         ││
│  │     - Get price from pricing module                         ││
│  │     - Filter dust/NFTs                                      ││
│  │     - Classify into category                                ││
│  │  4. Calculate totals per category                           ││
│  │  5. Return structured result                                ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                  calculate_sovereignty()                     ││
│  │                                                              ││
│  │  Input: categories dict, monthly_fixed_expenses             ││
│  │  Output: SovereigntyData with:                              ││
│  │    - sovereignty_ratio (total / annual expenses)            ││
│  │    - years_of_freedom                                       ││
│  │    - status (vulnerable → generational)                     ││
│  │    - hard_money_percentage                                  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Class: AlgorandSovereigntyAnalyzer

### Constants

```python
# Filter thresholds
DUST_THRESHOLD_USD = 10.0   # Minimum USD value to include
NFT_MAX_AMOUNT = 10         # Max amount for NFT-like detection
```

### Constructor

```python
def __init__(self, use_local_node: bool = True):
    """
    Initialize the analyzer.

    Args:
        use_local_node: If True, use local Algorand node (faster).
                       If False, use public AlgoNode API.

    Attributes:
        algod_address: Algorand node URL
        algod_token: API token (if using local node)
        classifier: AssetClassifier instance
        lp_parser: LPParser instance
        last_*: State storage for re-exporting results
    """
```

**Node Configuration:**

| Setting | Local Node | AlgoNode (Public) |
|---------|------------|-------------------|
| URL | http://127.0.0.1:8080 | https://mainnet-api.algonode.cloud |
| Token | Required | Not required |
| Speed | Faster | Slightly slower |
| Rate Limit | None | Soft limits |

---

## Core Methods

### get_account_assets(address) → Optional[Dict]

Fetch complete account data from Algorand.

```python
def get_account_assets(self, address: str) -> Optional[Dict[str, Any]]:
    """
    Get all assets for an Algorand address.

    Args:
        address: 58-character Algorand address

    Returns:
        Account data dict with keys:
        - amount: ALGO balance in microAlgos
        - assets: List of ASA holdings
        - status: 'Online' if participating in consensus
        - participation: Key info if participating

    Raises:
        Returns None on network errors (logged to console)
    """
```

**Response Structure:**
```python
{
    "address": "AAAA...",
    "amount": 50000000000,  # 50,000 ALGO in microAlgos
    "status": "Online",     # or "Offline"
    "assets": [
        {"asset-id": 31566704, "amount": 1000000},  # USDC
        {"asset-id": 386192725, "amount": 15000}    # goBTC
    ],
    "participation": {
        "vote-first-valid": 40000000,
        "vote-last-valid": 50000000
    }
}
```

### get_asset_details(asset_id) → Optional[Dict]

Fetch metadata for a specific ASA.

```python
def get_asset_details(self, asset_id: int) -> Optional[Dict[str, Any]]:
    """
    Get details for a specific Algorand Standard Asset.

    Args:
        asset_id: The ASA ID (e.g., 31566704 for USDC)

    Returns:
        Asset details dict with params:
        - name: Full asset name
        - unit-name: Ticker symbol
        - decimals: Decimal places (e.g., 6 for USDC)
        - total: Total supply
        - creator: Creator address

    Note:
        Silently returns None on errors (common for deleted assets)
    """
```

### _is_dust_or_nft(amount, usd_value, price, name) → bool

Filter out unwanted tokens.

```python
def _is_dust_or_nft(self, amount: float, usd_value: float,
                    price: Optional[float], name: str) -> bool:
    """
    Detect dust tokens and NFT-like items that should be filtered.

    Detection Criteria:
    1. NFT-like: amount 1-10, integer, no price data
    2. Dust: has price but value < $10
    3. Spam: contains 'reward', 'airdrop', 'free' with low value
    4. Negligible: value < $1 regardless of name

    Args:
        amount: Token amount after decimal adjustment
        usd_value: Calculated USD value
        price: Price per token (None if unavailable)
        name: Asset name for spam detection

    Returns:
        True if token should be filtered out

    Examples:
        # NFT - filter
        _is_dust_or_nft(1, 0, None, "CryptoKitty #123")  → True

        # Real holding - keep
        _is_dust_or_nft(1000, 250, 0.25, "ALGO")  → False

        # Airdrop spam - filter
        _is_dust_or_nft(1000, 0.50, 0.0005, "FREE REWARDS!")  → True
    """
```

---

### analyze_wallet(address) → Optional[Dict]

Main entry point for wallet analysis.

```python
def analyze_wallet(self, address: str) -> Optional[Dict[str, List[Dict]]]:
    """
    Analyze an Algorand wallet's sovereignty composition.

    This method:
    1. Fetches account data from blockchain
    2. Processes native ALGO (checks consensus participation)
    3. Iterates through all ASAs:
       - Retrieves asset metadata
       - Handles LP token decomposition
       - Gets current USD price
       - Filters dust/NFTs
       - Classifies into sovereignty category
    4. Stores results for potential re-export

    Args:
        address: 58-character Algorand address

    Returns:
        Categories dict:
        {
            "hard_money": [
                {"name": "goBTC", "ticker": "GOBTC", "amount": 0.015, "usd_value": 1500}
            ],
            "algo": [
                {"name": "Algorand (PARTICIPATING)", "ticker": "ALGO", "amount": 50000, "usd_value": 12500}
            ],
            "dollars": [
                {"name": "USD Coin", "ticker": "USDC", "amount": 5000, "usd_value": 5000}
            ],
            "shitcoin": [
                {"name": "SomeMemeToken", "ticker": "MEME", "amount": 1000000, "usd_value": 50}
            ]
        }

    Side Effects:
        - Updates self.last_* state variables
        - Prints progress to console

    Example:
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
        categories = analyzer.analyze_wallet("AAAA...")
        print(f"Hard money: ${sum(a['usd_value'] for a in categories['hard_money'])}")
    """
```

**Category Definitions:**

| Category | Assets Included | Sovereignty Impact |
|----------|----------------|-------------------|
| `hard_money` | BTC (goBTC, WBTC), Gold (GOLD$, XAUT), Silver (SILVER$) | Positive (generational wealth) |
| `algo` | Native ALGO, xALGO, fALGO, gALGO, mALGO, lALGO, tALGO | Positive (hard cap, staking) |
| `dollars` | USDC, USDT, DAI, STBL, fUSDC, fUSDT | Neutral (fiat proxy, can be frozen) |
| `shitcoin` | Everything else | Negative (speculative, volatile) |

---

### calculate_sovereignty(categories, monthly_expenses) → SovereigntyData

Calculate sovereignty metrics from categorized holdings.

```python
def calculate_sovereignty(self, categories: Dict[str, List[Dict]],
                         monthly_fixed_expenses: float) -> SovereigntyData:
    """
    Calculate financial sovereignty metrics.

    Formula:
        sovereignty_ratio = total_portfolio_usd / annual_expenses
        years_of_freedom = sovereignty_ratio
        hard_money_pct = hard_money_usd / total_portfolio_usd * 100

    Status Thresholds:
        >= 20 years: "Generationally Sovereign"
        >= 6 years:  "Antifragile"
        >= 3 years:  "Robust"
        >= 1 year:   "Fragile"
        < 1 year:    "Vulnerable"

    Args:
        categories: Output from analyze_wallet()
        monthly_fixed_expenses: User's monthly burn rate

    Returns:
        SovereigntyData(
            total_portfolio_usd=25000.0,
            annual_expenses=48000.0,
            sovereignty_ratio=0.52,
            years_of_freedom=0.52,
            status="vulnerable",
            hard_money_percentage=15.0,
            message="Build your hard money reserves"
        )

    Example:
        categories = analyzer.analyze_wallet(address)
        sovereignty = analyzer.calculate_sovereignty(categories, 4000)
        print(f"Status: {sovereignty.status}")  # "fragile"
        print(f"Runway: {sovereignty.years_of_freedom:.1f} years")  # "1.5 years"
    """
```

---

## LP Token Processing

When an LP token is detected, special handling occurs:

```python
# In analyze_wallet():
if self.lp_parser.is_lp_token(ticker, name):
    breakdown = self.lp_parser.estimate_lp_value(
        ticker, name, actual_amount, asset_id,
        lambda t, aid: get_asset_price(t, aid)  # Price callback
    )

    if breakdown:
        # Decompose into underlying assets
        components = self.lp_parser.classify_lp_components(
            breakdown, self.classifier.classify
        )

        for category, asset_dict in components:
            categories[category].append(asset_dict)

        continue  # Skip normal processing

# Fall through to normal classification if LP parsing fails
```

**Example LP Decomposition:**

```
Input: 100 TMPOOL-ALGO-GOBTC tokens

LP Parser Returns:
  - ALGO portion: 5000 ALGO → $1,250
  - goBTC portion: 0.0125 BTC → $1,250
  Total: $2,500

Classification:
  - ALGO → "algo" category
  - goBTC → "hard_money" category

Result: LP token correctly contributes to both categories
```

---

## State Management

The analyzer stores state for re-export scenarios:

```python
# After analyze_wallet() completes:
self.last_categories = categories      # Full category breakdown
self.last_address = address            # Analyzed address
self.last_is_participating = is_part   # Consensus status
self.last_hard_money_algo = hm_algo    # Hard money in ALGO terms
self.last_participation_info = {...}   # Participation key details
```

This allows:
- Exporting results without re-fetching
- History snapshots using cached data
- Alert engine access to last analysis

---

## Integration Example

```python
from core.analyzer import AlgorandSovereigntyAnalyzer

# Initialize (use public node for simplicity)
analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)

# Analyze wallet
address = "AAAA...your address..."
categories = analyzer.analyze_wallet(address)

if categories is None:
    print("Failed to fetch wallet data")
    exit(1)

# Calculate totals
total_usd = sum(
    sum(a['usd_value'] for a in assets)
    for assets in categories.values()
)
print(f"Total Portfolio: ${total_usd:,.2f}")

# Calculate sovereignty (assuming $4000/month expenses)
sovereignty = analyzer.calculate_sovereignty(categories, 4000)

print(f"Status: {sovereignty.status}")
print(f"Runway: {sovereignty.years_of_freedom:.1f} years")
print(f"Hard Money: {sovereignty.hard_money_percentage:.1f}%")
```

---

## Performance Notes

1. **API Calls**: One call per ASA for details (can be slow for large wallets)
2. **Caching**: Results cached in analyzer state, not persisted
3. **Timeouts**: 10 seconds per API call
4. **LP Parsing**: Additional calls to Tinyman SDK when LP tokens detected

**Optimization Tips:**
- Use local node for faster analysis
- Results cached at API layer (15 min TTL)
- Consider batch analysis for multiple wallets

---

*Last Updated: 2026-01-15*
