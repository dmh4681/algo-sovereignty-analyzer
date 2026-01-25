"""
LP Token Parser for Algorand DEXes (Tinyman, Pact, Humble, etc.)
================================================================

This module extracts the underlying asset values from Liquidity Provider (LP) tokens,
allowing proper classification of the component assets for sovereignty scoring.

Overview
--------
When users provide liquidity to decentralized exchanges (DEXes), they receive LP tokens
representing their proportional share of the liquidity pool. For accurate sovereignty
analysis, we must decompose these LP tokens back into their underlying assets.

Example LP Decomposition:
    User holds: 100 ALGO-USDC LP tokens (representing 1% of pool)
    Pool reserves: 5,000 ALGO + 5,000 USDC
    Decomposition:
        → 50 ALGO (1% × 5,000) → classified as 'algo' category
        → 50 USDC (1% × 5,000) → classified as 'dollars' category

    This ensures LP positions are correctly weighted in sovereignty calculations
    rather than being lumped into 'shitcoin' category.

Supported DEXes
---------------
+------------------+-------------------+---------------------------+
| DEX              | LP Token Pattern  | Example Ticker            |
+==================+===================+===========================+
| Tinyman v1       | TM1POOL           | TM1POOL-ALGO-USDC         |
| Tinyman v2       | TMPOOL2           | TMPOOL2 (name: TinymanPool2.0) |
| Pact             | PACT, PLP         | PLP-ALGO-goBTC            |
| Humble           | hLP, -LP          | hLP-ALGO-GOLD$            |
| Folks Finance    | / separator       | fUSDC / fALGO             |
+------------------+-------------------+---------------------------+

Value Calculation Methods
-------------------------
**Method 1: Tinyman SDK (Preferred - Accurate)**

    Uses on-chain pool state to calculate exact user share:

    ```
    user_share = user_lp_tokens / total_lp_supply
    asset1_amount = user_share × pool_reserve_1
    asset2_amount = user_share × pool_reserve_2
    total_usd = (asset1_amount × price1) + (asset2_amount × price2)
    ```

    Accuracy: Exact to on-chain state
    Requirements: tinyman-py-sdk installed, pool must exist on Tinyman

**Method 2: Geometric Mean (Fallback)**

    Standard AMM constant product formula when pool state unavailable:

    ```
    # For a constant product AMM: x × y = k
    # LP token value = 2 × √(price1 × price2) per LP token

    lp_value_per_token = 2 × math.sqrt(price1 × price2)
    total_usd = lp_amount × lp_value_per_token

    # Split 50/50 between assets (assumes balanced pool)
    asset1_usd = total_usd / 2
    asset2_usd = total_usd / 2
    ```

    Accuracy: Approximate (assumes 50/50 pool balance)
    Requirements: Price data for both underlying assets

Architecture Flow
-----------------
```
┌─────────────────────────────────────────────────────────────────┐
│                        LP Token Detection                        │
│                                                                  │
│  is_lp_token(ticker, name)                                       │
│      │                                                           │
│      ├── Check Tinyman patterns (TMPOOL, TM1POOL)               │
│      ├── Check Pact patterns (PACT, PLP)                        │
│      ├── Check generic patterns (POOL, -LP, /)                  │
│      │                                                           │
│      └── Returns: True/False                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Pool Info Retrieval                         │
│                                                                  │
│  get_pool_info(asset_id)                                         │
│      │                                                           │
│      ├── Fetch LP token metadata from Algorand node             │
│      ├── Extract creator address (pool account)                  │
│      ├── Parse asset pair from name (e.g., "ALGO-USDC")         │
│      │                                                           │
│      └── Returns: {asset1_ticker, asset2_ticker, creator, ...}  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Pool State Query (Tinyman)                    │
│                                                                  │
│  get_pool_state(pool_address, lp_asset_id, asset1_id, asset2_id)│
│      │                                                           │
│      ├── Initialize Tinyman SDK client                          │
│      ├── Fetch pool reserves from blockchain                     │
│      ├── Get total LP supply                                     │
│      │                                                           │
│      └── Returns: {total_supply, reserve1, reserve2}            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Value Calculation                            │
│                                                                  │
│  estimate_lp_value(ticker, name, amount, asset_id, get_price_fn)│
│      │                                                           │
│      ├── If pool_state available:                               │
│      │       Use exact share calculation (Method 1)              │
│      │                                                           │
│      └── Else:                                                   │
│              Use geometric mean estimate (Method 2)              │
│                                                                  │
│      └── Returns: LPBreakdown dataclass                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Asset Classification                          │
│                                                                  │
│  classify_lp_components(breakdown, classify_fn)                  │
│      │                                                           │
│      ├── Classify asset1 → (category, asset_dict)               │
│      ├── Classify asset2 → (category, asset_dict)               │
│      │                                                           │
│      └── Returns: [(category1, asset1), (category2, asset2)]    │
└─────────────────────────────────────────────────────────────────┘
```

Known Asset ID Mappings
-----------------------
For fallback resolution when pool queries fail:

| Ticker   | ASA ID       | Category    |
|----------|--------------|-------------|
| ALGO     | 0            | algo        |
| xALGO    | 1134696561   | algo        |
| fALGO    | 3184331013   | algo        |
| USDC     | 31566704     | dollars     |
| fUSDC    | 3184331239   | dollars     |
| GOLD$    | 1241944285   | hard_money  |
| SILVER$  | 1241945177   | hard_money  |
| goBTC    | 386192725    | hard_money  |

Example Usage
-------------
```python
from core.lp_parser import LPParser
from core.pricing import get_asset_price

parser = LPParser(algod_address="https://mainnet-api.algonode.cloud")

# Check if asset is an LP token
if parser.is_lp_token(ticker="TMPOOL2", name="TinymanPool2.0 ALGO-USDC"):

    # Get decomposition with USD values
    breakdown = parser.estimate_lp_value(
        lp_ticker="TMPOOL2",
        lp_name="TinymanPool2.0 ALGO-USDC",
        lp_amount=100.0,
        asset_id=123456789,
        get_price_fn=get_asset_price
    )

    if breakdown:
        print(f"LP Value: ${breakdown.total_usd:.2f}")
        print(f"  {breakdown.asset1_ticker}: {breakdown.asset1_amount:.2f} (${breakdown.asset1_usd:.2f})")
        print(f"  {breakdown.asset2_ticker}: {breakdown.asset2_amount:.2f} (${breakdown.asset2_usd:.2f})")

        # Route to sovereignty categories
        components = parser.classify_lp_components(breakdown, classifier.auto_classify_asset)
        for category, asset_data in components:
            print(f"  → {category}: {asset_data['ticker']}")
```

Performance Considerations
--------------------------
- Pool state queries require Tinyman SDK and make network requests
- Caching is done via `_pool_cache` dict to avoid repeated queries
- Fallback to geometric mean is faster but less accurate
- Each LP token decomposition requires 2 price lookups

Error Handling
--------------
- Returns None if LP token cannot be parsed or priced
- Gracefully falls back to geometric mean if SDK unavailable
- Prints warning messages for debugging (visible in logs)

See Also
--------
- core/classifier.py: Asset classification logic
- core/pricing.py: Price fetching for underlying assets
- core/analyzer.py: Main wallet analysis that uses this parser
"""

import requests
import re
import math
import traceback
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class LPBreakdown:
    """
    Represents the decomposition of an LP token into its underlying assets.

    When a user provides liquidity to a DEX, they receive LP tokens proportional
    to their share of the pool. This dataclass captures the breakdown of that
    LP position into the two underlying assets.

    Attributes:
        lp_ticker: The ticker symbol of the LP token (e.g., "TMPOOL2")
        lp_amount: How many LP tokens the user holds
        asset1_ticker: Ticker of the first underlying asset (e.g., "ALGO")
        asset1_amount: User's share of asset 1 based on pool reserves
        asset1_usd: USD value of user's asset 1 position
        asset2_ticker: Ticker of the second underlying asset (e.g., "USDC")
        asset2_amount: User's share of asset 2 based on pool reserves
        asset2_usd: USD value of user's asset 2 position
        total_usd: Combined USD value (asset1_usd + asset2_usd)

    Example:
        LPBreakdown(
            lp_ticker="TMPOOL2",
            lp_amount=100.0,
            asset1_ticker="ALGO",
            asset1_amount=500.0,      # User owns 500 ALGO worth
            asset1_usd=150.0,         # At $0.30 per ALGO
            asset2_ticker="USDC",
            asset2_amount=150.0,      # User owns 150 USDC worth
            asset2_usd=150.0,
            total_usd=300.0
        )
    """
    lp_ticker: str
    lp_amount: float
    asset1_ticker: str
    asset1_amount: float
    asset1_usd: float
    asset2_ticker: str
    asset2_amount: float
    asset2_usd: float
    total_usd: float


class LPParser:
    """
    Parser for extracting underlying asset values from LP (Liquidity Provider) tokens.

    LP tokens represent a user's share of a liquidity pool on a DEX. To properly
    classify holdings for sovereignty analysis, we decompose LP tokens into their
    underlying assets.

    Calculation Methods:
        1. **Tinyman SDK (Accurate)**: Queries on-chain pool state for exact reserves
           and total LP supply. User's share = (user_lp / total_lp) × reserves.

        2. **Geometric Mean (Fallback)**: When pool state unavailable, uses standard
           AMM formula: LP Value = 2 × √(Price1 × Price2)

    Supported LP Token Patterns:
        - Tinyman v1: ticker starts with "TM1POOL" or "TMPOOL"
        - Tinyman v2: ticker contains "TM" and "POOL", name like "TinymanPool2.0"
        - Pact: ticker starts with "PACT" or contains "PLP"
        - Humble: ticker contains "-LP"
        - Folks Finance: name contains "/" with asset pairs

    Attributes:
        algod_address: Algorand node API endpoint
        headers: HTTP headers for API requests (auth token if local node)
        _pool_cache: In-memory cache of pool configurations by asset ID

    Usage:
        parser = LPParser()
        if parser.is_lp_token("TMPOOL2", "TinymanPool2.0 ALGO-USDC"):
            breakdown = parser.estimate_lp_value(...)
    """

    def __init__(self, algod_address: str = "https://mainnet-api.algonode.cloud", headers: dict = None):
        self.algod_address = algod_address
        self.headers = headers or {}

        # Known Tinyman pool asset IDs (asset_id -> (asset1_id, asset2_id, app_id))
        # These are cached pool configurations
        self._pool_cache: Dict[int, Dict[str, Any]] = {}

    def is_lp_token(self, ticker: str, name: str) -> bool:
        """
        Detect if an asset is likely a Liquidity Provider (LP) token.

        Uses pattern matching on ticker and name to identify LP tokens from
        various Algorand DEXes. This is a heuristic check - some edge cases
        may require manual classification override.

        Args:
            ticker: The unit-name of the ASA (e.g., "TMPOOL2", "PLP-ALGO-USDC")
            name: The full name of the ASA (e.g., "TinymanPool2.0 ALGO-USDC")

        Returns:
            True if the asset appears to be an LP token, False otherwise.

        Detection Patterns:
            - Tinyman: "TMPOOL", "TM1POOL", "TM" + "POOL" combinations
            - Pact: "PACT" prefix, "PLP" substring
            - Generic: "POOL" in name, "-LP" in ticker
            - Folks Finance: "/" separator with ALGO/USDC in name
        """
        ticker_upper = ticker.upper()
        name_upper = name.upper()

        # Tinyman LP tokens
        if ticker_upper.startswith('TMPOOL') or 'TMPOOL' in ticker_upper:
            return True
        # Tinyman V2 uses TM1.1POOL or similar
        if 'TM' in ticker_upper and 'POOL' in ticker_upper:
            return True
        # Pact LP tokens
        if ticker_upper.startswith('PACT') or 'PLP' in ticker_upper:
            return True
        # Generic pool patterns
        if 'POOL' in name_upper or '-LP' in ticker_upper:
            return True
        # Folks Finance LP tokens (often have "/" in name like "fUSDC / fALGO")
        if '/' in name and ('ALGO' in name_upper or 'USDC' in name_upper):
            return True
        # Check for common LP name patterns with slashes (e.g., "xALGO / ALGO")
        if re.search(r'\w+\s*/\s*\w+', name):
            return True

        return False

    def get_pool_info(self, asset_id: int) -> Optional[Dict[str, Any]]:
        """
        Get pool information for an LP token.
        Returns pool reserves and total LP supply.
        """
        if asset_id in self._pool_cache:
            return self._pool_cache[asset_id]

        # First, get the LP token details to find pool app ID
        try:
            url = f"{self.algod_address}/v2/assets/{asset_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return None

            asset_data = response.json()
            params = asset_data.get('params', {})

            # The LP token's creator is often the pool application address
            creator = params.get('creator', '')
            unit_name = params.get('unit-name', '')
            name = params.get('name', '')

            # Try to extract pool info from Tinyman V2 naming convention
            # Format is usually like "TinymanPool2.0 ALGO-USDC" or similar
            pool_info = self._parse_tinyman_pool(name, unit_name, creator, asset_id)
            if pool_info:
                self._pool_cache[asset_id] = pool_info
                return pool_info

        except Exception as e:
            print(f"⚠️  Failed to get pool info for LP token {asset_id}: {e}")

        return None

    def _parse_tinyman_pool(self, name: str, unit_name: str, creator: str, asset_id: int) -> Optional[Dict[str, Any]]:
        """
        Parse Tinyman pool information from LP token asset metadata.

        Tinyman LP tokens follow specific naming conventions that allow us to
        extract the underlying asset pair without querying the pool directly.

        Naming Patterns:
            - Tinyman v2: "TinymanPool2.0 ALGO-USDC" or "TinymanPool2.0 xALGO/ALGO"
            - Tinyman v1: "TM1POOL ALGO-USDC"
            - Unit name may also contain pair: "TMPOOL2" with name "ALGO-USDC"

        Algorithm:
            1. First try to match pair from full name (most reliable)
            2. If no match, try unit_name as fallback
            3. Extract both asset tickers and normalize to uppercase

        Args:
            name: Full asset name (e.g., "TinymanPool2.0 ALGO-USDC")
            unit_name: Unit name / ticker (e.g., "TMPOOL2")
            creator: Pool creator address (the pool account)
            asset_id: ASA ID of the LP token

        Returns:
            Dict with pool info or None if parsing fails:
            {
                'asset1_ticker': 'ALGO',
                'asset2_ticker': 'USDC',
                'lp_asset_id': 123456,
                'creator': 'POOL_ADDRESS...',
                'estimated': True  # Flag indicating this is parsed, not from SDK
            }
        """
        # Regex pattern matches: ALGO-USDC, ALGO/USDC, xALGO-ALGO, etc.
        # Captures two word groups separated by - or /
        pair_match = re.search(r'(\w+)[/-](\w+)', name)
        if not pair_match:
            # Fallback: try unit_name if name didn't have the pair
            pair_match = re.search(r'(\w+)[/-](\w+)', unit_name)

        if pair_match:
            # Extract and normalize ticker symbols
            asset1_ticker = pair_match.group(1).upper()
            asset2_ticker = pair_match.group(2).upper()

            return {
                'asset1_ticker': asset1_ticker,
                'asset2_ticker': asset2_ticker,
                'lp_asset_id': asset_id,
                'creator': creator,
                'estimated': True  # Indicates this is from name parsing, not SDK
            }

        return None

    def _get_pool_assets(self, creator_address: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Fetch the assets held by the pool account to identify the pair.
        Returns (asset1_id, asset2_id).
        """
        try:
            url = f"{self.algod_address}/v2/accounts/{creator_address}"
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                assets = data.get('assets', [])
                
                # Tinyman pools hold 2 assets. One might be ALGO (which isn't in 'assets' list).
                # If we find 2 assets, those are the pair.
                # If we find 1 asset, the other is ALGO (Asset 0).
                
                found_ids = [a['asset-id'] for a in assets if a['amount'] > 0]
                
                if len(found_ids) == 2:
                    return found_ids[0], found_ids[1]
                elif len(found_ids) == 1:
                    return found_ids[0], 0  # Asset + ALGO
                
        except Exception as e:
            print(f"⚠️  Failed to fetch pool assets for {creator_address}: {e}")
        
        return None, None
    
    def get_pool_state(self, pool_address: str, lp_asset_id: int, asset1_id: int, asset2_id: int) -> Optional[dict]:
        """
        Query pool using Tinyman SDK to get exact reserves and total supply.
        Returns dict with: total_supply, reserve1, reserve2
        """
        try:
            print(f"🔍 Using Tinyman SDK for LP {lp_asset_id}")
            print(f"   Asset IDs: {asset1_id}, {asset2_id}")
            
            from tinyman.v2.client import TinymanV2MainnetClient
            from algosdk.v2client.algod import AlgodClient
            
            # Create Algorand client
            algod_client = AlgodClient("", self.algod_address)
            
            # Create Tinyman client
            tinyman_client = TinymanV2MainnetClient(algod_client=algod_client)
            
            # Fetch the pool
            # Tinyman SDK needs Asset objects
            from tinyman.assets import Asset as TinymanAsset
            
            # Create asset objects
            if asset1_id == 0:
                asset1 = tinyman_client.fetch_asset(0)  # ALGO
            else:
                asset1 = tinyman_client.fetch_asset(asset1_id)
            
            if asset2_id == 0:
                asset2 = tinyman_client.fetch_asset(0)  # ALGO
            else:
                asset2 = tinyman_client.fetch_asset(asset2_id)
            
            # Fetch the pool
            pool = tinyman_client.fetch_pool(asset1, asset2)
            
            if not pool or not pool.exists:
                print(f"   ❌ Pool not found")
                return None
            
            # Get pool info
            info = pool.info()
            print(f"   ℹ️ Tinyman info keys: {list(info.keys())}")
            
            # info is a dict, not an object
            # Keys usually use underscores in V2 state
            total_supply = info.get('issued_pool_tokens', 0) / (10 ** 6)
            
            # Try both formats just in case
            r1 = info.get('asset_1_reserves') or info.get('asset1_reserves', 0)
            r2 = info.get('asset_2_reserves') or info.get('asset2_reserves', 0)
            
            reserve1 = r1 / (10 ** asset1.decimals)
            reserve2 = r2 / (10 ** asset2.decimals)
            
            print(f"   ✅ Tinyman SDK data:")
            print(f"      Total LP supply: {total_supply:,.2f}")
            print(f"      Reserve1 ({asset1.unit_name}): {reserve1:,.2f}")
            print(f"      Reserve2 ({asset2.unit_name}): {reserve2:,.2f}")
            
            return {
                'total_supply': total_supply,
                'reserve1': reserve1,
                'reserve2': reserve2
            }
            
        except Exception as e:
            print(f"Tinyman SDK error: {e}")
            traceback.print_exc()
            return None

    def estimate_lp_value(self, lp_ticker: str, lp_name: str, lp_amount: float,
                         asset_id: int, get_price_fn) -> Optional[LPBreakdown]:
        """
        Calculate the USD value and component breakdown of an LP token position.

        This method attempts to decompose an LP token into its underlying assets
        and calculate the user's proportional share. It uses two calculation methods:

        **Method 1 - Tinyman SDK (Preferred)**:
        When the Tinyman SDK is available and the pool is a Tinyman pool:
            user_share = user_lp_amount / total_lp_supply
            asset1_amount = user_share × pool_reserve1
            asset2_amount = user_share × pool_reserve2

        **Method 2 - Geometric Mean (Fallback)**:
        Standard AMM constant product formula when pool state is unavailable:
            lp_value = 2 × √(price1 × price2) × lp_amount
        Then split 50/50 between assets.

        Args:
            lp_ticker: The LP token's ticker symbol (e.g., "TMPOOL2")
            lp_name: The LP token's full name (e.g., "TinymanPool2.0 ALGO-USDC")
            lp_amount: How many LP tokens the user holds
            asset_id: The ASA ID of the LP token
            get_price_fn: Function to fetch asset prices, signature:
                          get_price_fn(ticker: str, asset_id: int) -> Optional[float]

        Returns:
            LPBreakdown dataclass with component amounts and USD values,
            or None if the LP token cannot be parsed or priced.

        Side Effects:
            - Prints progress messages to console
            - May query Algorand blockchain for pool state
            - Caches pool info in self._pool_cache
        """
        # Parse the LP name to get underlying assets
        # Expected format: "TinymanPool2.0 XALGO-ALGO"
        parts = lp_name.replace("TinymanPool2.0 ", "").split("-")
        if len(parts) != 2:
            print(f"⚠️  Could not parse LP name: {lp_name}")
            return None
            
        asset1_ticker = parts[0]
        asset2_ticker = parts[1]
        
        # Resolve asset IDs
        # We need the pool creator address to find the assets
        pool_info = self.get_pool_info(asset_id)
        
        asset1_id = None
        asset2_id = None
        
        if pool_info and 'creator' in pool_info:
            # Get the assets from the pool creator account
            # This is reliable because the pool account must opt-in to the assets
            assets = self._get_pool_assets(pool_info['creator'])
            if assets and len(assets) >= 2:
                asset1_id = assets[0]
                asset2_id = assets[1]
        
        # Fallback IDs if resolution failed
        if asset1_id is None or asset2_id is None:
            # Apply hardcoded fallbacks based on ticker names
            if asset1_ticker == 'XALGO': asset1_id = 1134696561
            elif asset1_ticker == 'ALGO': asset1_id = 0
            elif asset1_ticker == 'FUSDC': asset1_id = 3184331239
            elif asset1_ticker == 'FALGO': asset1_id = 3184331013
            elif asset1_ticker == 'USDC': asset1_id = 31566704
            elif asset1_ticker == 'GOLD$': asset1_id = 1241944285
            elif asset1_ticker == 'SILVER$': asset1_id = 1241945177
            elif asset1_ticker == 'goBTC': asset1_id = 386192725
            
            if asset2_ticker == 'XALGO': asset2_id = 1134696561
            elif asset2_ticker == 'ALGO': asset2_id = 0
            elif asset2_ticker == 'FUSDC': asset2_id = 3184331239
            elif asset2_ticker == 'FALGO': asset2_id = 3184331013
            elif asset2_ticker == 'USDC': asset2_id = 31566704
            elif asset2_ticker == 'GOLD$': asset2_id = 1241944285
            elif asset2_ticker == 'SILVER$': asset2_id = 1241945177
            elif asset2_ticker == 'goBTC': asset2_id = 386192725

        # Get prices using resolved IDs if available, otherwise fallback to ticker
        # We do NOT normalize tickers anymore, so xALGO stays xALGO.
        price1 = get_price_fn(asset1_ticker, asset1_id) or 0
        price2 = get_price_fn(asset2_ticker, asset2_id) or 0

        # TINYMAN ACCURATE FORMULA
        # Get pool state (total LP supply and reserves) for exact calculation
        pool_state = None
        if pool_info and 'creator' in pool_info and asset1_id is not None and asset2_id is not None:
            pool_state = self.get_pool_state(
                pool_info['creator'],
                asset_id,
                asset1_id,
                asset2_id
            )
        
        # Check if pool state is valid AND has non-zero value
        if pool_state and pool_state['total_supply'] > 0:
            # Calculate potential value to see if it's valid
            user_share = lp_amount / pool_state['total_supply']
            reserve1_value = pool_state['reserve1'] * price1
            reserve2_value = pool_state['reserve2'] * price2
            potential_total_usd = user_share * (reserve1_value + reserve2_value)
            
            if potential_total_usd > 0.01: # Threshold to avoid zero values
                total_usd = potential_total_usd
                
                # Calculate user's share of each asset
                asset1_amount = user_share * pool_state['reserve1']
                asset2_amount = user_share * pool_state['reserve2']
                
                asset1_usd = asset1_amount * price1
                asset2_usd = asset2_amount * price2
                
                print(f"✅ Tinyman formula: {lp_amount:.2f} LP / {pool_state['total_supply']:.2f} total = {user_share*100:.4f}% share = ${total_usd:.2f}")
                
                return LPBreakdown(
                    lp_ticker=lp_ticker,
                    lp_amount=lp_amount,
                    asset1_ticker=asset1_ticker,
                    asset1_amount=asset1_amount,
                    asset1_usd=asset1_usd,
                    asset2_ticker=asset2_ticker,
                    asset2_amount=asset2_amount,
                    asset2_usd=asset2_usd,
                    total_usd=total_usd
                )
            else:
                print(f"⚠️  Tinyman SDK returned near-zero value (${potential_total_usd:.4f}), falling back to geometric mean")

        # FALLBACK: If pool state query failed OR returned zero value, use geometric mean
        print(f"⚠️  Pool state unavailable or invalid for {lp_ticker}, using geometric mean estimate")
        
        # If we have no price data, we can't estimate
        if price1 == 0 and price2 == 0:
            return None
            
        # Standard AMM Pricing Formula (Geometric Mean)
        # Value of 1 LP Token = 2 * math.sqrt(Price1 * Price2)
        
        if price1 > 0 and price2 > 0:
            # Calculate value per LP token
            lp_token_value = 2 * math.sqrt(price1 * price2)
            
            total_usd = lp_amount * lp_token_value
            
            # Split value 50/50 between assets
            asset1_usd = total_usd / 2
            asset2_usd = total_usd / 2
            
            # Calculate amounts based on prices
            asset1_amount = asset1_usd / price1
            asset2_amount = asset2_usd / price2
            
            return LPBreakdown(
                lp_ticker=lp_ticker,
                lp_amount=lp_amount,
                asset1_ticker=asset1_ticker,
                asset1_amount=asset1_amount,
                asset1_usd=asset1_usd,
                asset2_ticker=asset2_ticker,
                asset2_amount=asset2_amount,
                asset2_usd=asset2_usd,
                total_usd=total_usd
            )
            
        return None

    def classify_lp_components(self, breakdown: LPBreakdown, classify_fn) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Classify the decomposed LP token components into sovereignty categories.

        After an LP token is broken down into its underlying assets, each component
        needs to be classified according to the sovereignty hierarchy:
            - hard_money: BTC, Gold, Silver
            - algo: ALGO, xALGO, fALGO, etc.
            - dollars: USDC, USDT, fUSDC, etc.
            - shitcoin: Everything else

        Important: We use asset_id=-1 to force auto-classification rather than
        CSV lookup. This is intentional because LP components should be classified
        by their ticker pattern, not by the LP token's asset ID.

        Args:
            breakdown: LPBreakdown dataclass with asset amounts and USD values
            classify_fn: Classification function with signature:
                         classify_fn(asset_id: int, name: str, ticker: str) -> str

        Returns:
            List of (category, asset_dict) tuples, one for each underlying asset.

            Example output for ALGO-USDC LP:
            [
                ('algo', {
                    'name': 'ALGO (from TMPOOL2)',
                    'ticker': 'ALGO',
                    'amount': 500.0,
                    'usd_value': 125.0,
                    'from_lp': 'TMPOOL2'
                }),
                ('dollars', {
                    'name': 'USDC (from TMPOOL2)',
                    'ticker': 'USDC',
                    'amount': 125.0,
                    'usd_value': 125.0,
                    'from_lp': 'TMPOOL2'
                })
            ]

        Note:
            The 'from_lp' field is added to track that this asset came from LP
            decomposition. This enables the UI to show LP sources and allows
            filtering/grouping of LP-derived positions.
        """
        components = []

        # =========================================================================
        # Classify Asset 1
        # =========================================================================
        # Use asset_id=-1 to bypass CSV overrides and use pure auto-classification
        # This ensures ALGO is classified as 'algo' even if the LP token itself
        # might have a CSV override for something else
        cat1 = classify_fn(-1, breakdown.asset1_ticker, breakdown.asset1_ticker)
        components.append((cat1, {
            'name': f'{breakdown.asset1_ticker} (from {breakdown.lp_ticker})',
            'ticker': breakdown.asset1_ticker,
            'amount': breakdown.asset1_amount,
            'usd_value': breakdown.asset1_usd,
            'from_lp': breakdown.lp_ticker  # Track LP source for UI display
        }))

        # =========================================================================
        # Classify Asset 2
        # =========================================================================
        cat2 = classify_fn(-1, breakdown.asset2_ticker, breakdown.asset2_ticker)
        components.append((cat2, {
            'name': f'{breakdown.asset2_ticker} (from {breakdown.lp_ticker})',
            'ticker': breakdown.asset2_ticker,
            'amount': breakdown.asset2_amount,
            'usd_value': breakdown.asset2_usd,
            'from_lp': breakdown.lp_ticker
        }))

        return components
