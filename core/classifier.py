"""
Asset Classification System for Algorand Sovereignty Analyzer
=============================================================

This module implements the core asset classification logic that determines
which sovereignty category each Algorand Standard Asset (ASA) belongs to.

Philosophy: Hard Money Maximalism
---------------------------------
The classification system is built on hard money maximalist principles:

- **Hard Money** (BTC, Gold, Silver): The only true stores of value that have
  maintained purchasing power across millennia. These are the foundation of
  financial sovereignty.

- **ALGO**: The native token of Algorand. While not "hard money" by strict
  definition (no physical backing, relatively new), it has a hard cap and
  proof-of-stake consensus. Treated separately from hard money.

- **Dollars**: Stablecoins pegged to fiat currencies. Useful for short-term
  liquidity but fundamentally represent fiat exposure and inflation risk.

- **Shitcoins**: Everything else. Governance tokens, meme coins, LP tokens
  (before decomposition), NFTs, etc. High risk, speculative assets.

Classification Hierarchy
------------------------
The system uses a three-tier priority hierarchy:

```
┌─────────────────────────────────────────────────────────────────┐
│  Priority 1: CSV Manual Overrides (Highest)                     │
│  File: data/asset_classification.csv                            │
│  Purpose: Human-curated classifications for known assets        │
│  Format: asset_id,name,ticker,category,notes                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Priority 2: User-Submitted Corrections (Medium)                │
│  File: data/user_corrections.json                               │
│  Purpose: Community-driven corrections to auto-classification   │
│  Managed by: core/corrections.py (CorrectionsManager)           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Priority 3: Auto-Classification Regex (Lowest)                 │
│  Location: AssetClassifier.auto_classify_asset() method         │
│  Purpose: Pattern-based classification for unknown assets       │
│  Default: shitcoin (if no pattern matches)                      │
└─────────────────────────────────────────────────────────────────┘
```

Auto-Classification Patterns
----------------------------
The regex patterns used for automatic classification:

**Hard Money Patterns:**
```python
[
    r'^WBTC$',      # Wrapped Bitcoin
    r'^BTC$',       # Bitcoin
    r'^GOBTC$',     # goBTC (Algorand-native wrapped BTC)
    r'GOLD',        # Gold tokens (GOLD$, etc.)
    r'^XAUT$',      # Tether Gold
    r'^PAXG$',      # Paxos Gold
    r'SILVER',      # Silver tokens (SILVER$, etc.)
]
```

**ALGO Patterns:**
```python
[
    r'^XALGO$',     # Folks Finance liquid staking
    r'^FALGO$',     # Folks Finance wrapped ALGO
    r'^GALGO$',     # Governance ALGO
    r'^MALGO$',     # Messina ALGO
    r'^LALGO$',     # Liquid ALGO variants
    r'^TALGO$',     # Tinyman ALGO
]
```

**Dollar Patterns:**
```python
[
    r'^USDC',       # USD Coin (and USDCa, etc.)
    r'^FUSDC',      # Folks wrapped USDC
    r'^USDT',       # Tether (and USDt)
    r'^DAI$',       # DAI stablecoin
    r'^FUSD',       # Folks wrapped USD
]
```

CSV File Format
---------------
The manual override CSV uses this format:

```csv
asset_id,name,ticker,category,notes
793124631,goBTC,goBTC,hard_money,Algorand native wrapped Bitcoin via goMint
1241944285,Meld Gold,GOLD$,hard_money,Gold-backed token by Meld
31566704,USD Coin,USDC,dollars,Circle's USDC stablecoin
```

Example Usage
-------------
```python
from core.classifier import AssetClassifier

classifier = AssetClassifier()

# Manual override (highest priority)
category = classifier.auto_classify_asset(
    asset_id=793124631,  # goBTC
    name="goBTC",
    ticker="goBTC"
)
# Returns: "hard_money" (from CSV)

# Auto-classification (lowest priority)
category = classifier.auto_classify_asset(
    asset_id=999999999,  # Unknown asset
    name="Some Meme Token",
    ticker="MEME"
)
# Returns: "shitcoin" (no pattern match)
```

Adding New Classifications
--------------------------
1. **For individual assets**: Add to `data/asset_classification.csv`
2. **For asset patterns**: Update regex patterns in `auto_classify_asset()`
3. **For user corrections**: Submit via POST /corrections API endpoint

See Also
--------
- core/corrections.py: User correction submission system
- core/models.py: AssetCategory enum definition
- docs/CLASSIFICATION-SYSTEM.md: Detailed classification documentation
"""

import re
from typing import Dict
from .models import AssetCategory
from .corrections import get_corrections_manager


class AssetClassifier:
    """
    Asset classification engine using a three-tier priority hierarchy.

    This class is responsible for determining which sovereignty category
    an asset belongs to: hard_money, algo, dollars, or shitcoin.

    The classification follows a strict priority order:
    1. CSV manual overrides (data/asset_classification.csv)
    2. User-submitted corrections (data/user_corrections.json)
    3. Regex pattern matching (auto-classification)

    Attributes:
        classifications: Dict mapping asset_id strings to classification dicts
                        loaded from the CSV file
        corrections_manager: CorrectionsManager instance for user corrections

    Example:
        >>> classifier = AssetClassifier()
        >>> category = classifier.auto_classify_asset(
        ...     asset_id=31566704,
        ...     name="USD Coin",
        ...     ticker="USDC"
        ... )
        >>> print(category)
        'dollars'
    """

    def __init__(self, classification_file: str = 'data/asset_classification.csv'):
        """
        Initialize the asset classifier.

        Args:
            classification_file: Path to CSV file with manual overrides.
                                Defaults to 'data/asset_classification.csv'.
                                If file doesn't exist, only auto-classification is used.
        """
        self.classifications: Dict[str, Dict[str, str]] = {}
        self.corrections_manager = get_corrections_manager()
        self.load_classifications(classification_file)

    def load_classifications(self, filepath: str) -> None:
        """
        Load manual asset classification overrides from CSV file.

        The CSV file provides the highest-priority classification overrides.
        These are typically human-curated entries for well-known assets that
        might not be correctly auto-classified by regex patterns.

        CSV Format:
            asset_id,name,ticker,category,notes
            793124631,goBTC,goBTC,hard_money,Algorand wrapped BTC
            31566704,USD Coin,USDC,dollars,Circle stablecoin

        Args:
            filepath: Path to the CSV file. Expected columns:
                     - asset_id: Algorand Standard Asset ID (string)
                     - name: Human-readable asset name
                     - ticker: Unit name / ticker symbol
                     - category: One of hard_money, algo, dollars, shitcoin

        Side Effects:
            - Populates self.classifications dict
            - Prints warning if file not found (graceful degradation)

        Note:
            If the CSV file is not found, the system continues with
            auto-classification only. This allows the system to work
            without manual configuration.
        """
        self.classifications = {}
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()[1:]  # Skip header row
                for line in lines:
                    parts = line.strip().split(',')
                    # Require at least 4 columns: asset_id, name, ticker, category
                    if len(parts) >= 4:
                        asset_id = parts[0]
                        self.classifications[asset_id] = {
                            'name': parts[1],
                            'ticker': parts[2],
                            'category': parts[3]
                        }
        except FileNotFoundError:
            # Graceful degradation: system works without CSV file
            print("ℹ️  No asset_classifications.csv found - using auto-classification only\n")

    def auto_classify_asset(self, asset_id: int, name: str, ticker: str) -> str:
        """
        Classify an asset using the three-tier priority hierarchy.

        This is the main classification method that determines which sovereignty
        category an asset belongs to. It checks three sources in order:

        Priority Order:
            1. CSV manual overrides (data/asset_classification.csv)
            2. User-submitted corrections (data/user_corrections.json)
            3. Regex pattern matching (auto-classification)

        Hard Money Maximalist Philosophy:
            - **Hard Money**: Only BTC, Gold, and Silver are considered true
              stores of value. These assets have stood the test of time.
            - **ALGO**: Platform native token. Good properties (hard cap,
              staking) but not generational wealth preservation.
            - **Dollars**: Fiat exposure. Useful for liquidity but subject
              to inflation and debasement risk.
            - **Shitcoins**: Everything else. High risk, speculative.

        Args:
            asset_id: Algorand Standard Asset ID (int). Use -1 to force
                     auto-classification and bypass CSV/corrections lookup.
            name: Human-readable asset name (used for display, not classification)
            ticker: Unit name / ticker symbol (used for regex matching)

        Returns:
            Category string: one of 'hard_money', 'algo', 'dollars', 'shitcoin'

        Example:
            >>> classifier.auto_classify_asset(793124631, "goBTC", "goBTC")
            'hard_money'

            >>> classifier.auto_classify_asset(-1, "Unknown", "RANDOM")
            'shitcoin'

        Note:
            The asset_id=-1 convention is used by LP decomposition to force
            auto-classification of underlying assets regardless of any CSV
            overrides that might exist for the LP token itself.
        """
        # =========================================================================
        # PRIORITY 1: CSV Manual Overrides (Highest Priority)
        # =========================================================================
        # Check if this specific asset ID has a manual classification.
        # This allows humans to override auto-classification for known assets.
        if str(asset_id) in self.classifications:
            return self.classifications[str(asset_id)]['category']

        # =========================================================================
        # PRIORITY 2: User-Submitted Corrections (Medium Priority)
        # =========================================================================
        # Check if the community has submitted a correction for this asset.
        # This enables crowd-sourced improvement of classifications.
        corrected_category = self.corrections_manager.get_correction(str(asset_id))
        if corrected_category:
            return corrected_category

        # =========================================================================
        # PRIORITY 3: Auto-Classification via Regex (Lowest Priority)
        # =========================================================================
        # Pattern-based classification for unknown assets.
        # Default to 'shitcoin' if no pattern matches.

        ticker_upper = ticker.upper()

        # -------------------------------------------------------------------------
        # HARD MONEY: Bitcoin, Gold, Silver
        # -------------------------------------------------------------------------
        # These are the only true stores of value according to hard money principles.
        # Bitcoin: Digital gold with mathematical scarcity
        # Gold: 5,000+ years of monetary history
        # Silver: Poor man's gold, industrial + monetary use
        hard_money_patterns = [
            r'^WBTC$', r'^BTC$', r'^GOBTC$',    # Bitcoin variants
            r'GOLD', r'^XAUT$', r'^PAXG$',      # Gold tokens
            r'SILVER',                           # Silver tokens
        ]
        if any(re.search(pattern, ticker_upper) for pattern in hard_money_patterns):
            return AssetCategory.HARD_MONEY.value

        # -------------------------------------------------------------------------
        # ALGO: Native ALGO and Liquid Staking Derivatives
        # -------------------------------------------------------------------------
        # ALGO itself is classified in the analyzer (not here) because ALGO
        # doesn't have an ASA ID (it's the native token). This section handles
        # liquid staking derivatives that maintain 1:1 or near-1:1 peg to ALGO.
        algo_patterns = [
            r'^XALGO$',     # Folks Finance liquid staking (staked ALGO)
            r'^FALGO$',     # Folks Finance wrapped ALGO
            r'^GALGO$',     # Governance ALGO
            r'^MALGO$',     # Messina ALGO
            r'^LALGO$',     # Liquid ALGO variants
            r'^TALGO$',     # Tinyman ALGO
        ]
        if any(re.search(pattern, ticker_upper) for pattern in algo_patterns):
            return AssetCategory.ALGO.value

        # -------------------------------------------------------------------------
        # DOLLARS: Stablecoins (Fiat-Pegged Assets)
        # -------------------------------------------------------------------------
        # Stablecoins represent fiat currency exposure. While useful for
        # short-term liquidity, they carry inflation risk and counterparty risk.
        # Includes Folks Finance wrapped versions for DeFi composability.
        dollar_patterns = [
            r'^USDC',       # USD Coin (Circle) - most liquid
            r'^FUSDC',      # Folks Finance wrapped USDC
            r'^USDT',       # Tether - high volume but controversy
            r'^DAI$',       # MakerDAO DAI - decentralized stablecoin
            r'^FUSD',       # Folks Finance USD variants
        ]
        if any(re.search(pattern, ticker_upper) for pattern in dollar_patterns):
            return AssetCategory.DOLLARS.value

        # -------------------------------------------------------------------------
        # SHITCOINS: Everything Else
        # -------------------------------------------------------------------------
        # Default category for:
        # - LP tokens (before decomposition)
        # - NFTs
        # - Governance tokens
        # - Meme coins
        # - Unknown assets
        # - DEX tokens
        # - Any asset that doesn't match the above patterns
        return AssetCategory.SHITCOIN.value
