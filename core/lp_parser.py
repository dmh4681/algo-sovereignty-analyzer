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

import logging
import requests
import re
import math
import traceback
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from .retry import retry_with_backoff

logger = logging.getLogger("core.lp_parser")


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
        Retrieve pool configuration for an LP token by querying the Algorand node.

        Fetches the LP token's ASA metadata from the blockchain and extracts
        pool information (underlying asset pair, creator/pool address). Results
        are cached in ``_pool_cache`` to avoid redundant network requests.

        Algorithm:
            1. Check in-memory cache first
            2. Fetch ASA params from Algorand node (``/v2/assets/{id}``)
            3. Extract creator address (this is the pool account on Tinyman)
            4. Parse the asset pair from the ASA name using ``_parse_tinyman_pool``
            5. Cache and return the result

        Args:
            asset_id: The ASA ID of the LP token to look up.

        Returns:
            Dict with pool info (asset tickers, creator address, LP asset ID),
            or None if the LP token metadata cannot be fetched or parsed.

        Raises:
            No exceptions raised; errors are caught and logged, returning None.
        """
        if asset_id in self._pool_cache:
            return self._pool_cache[asset_id]

        # First, get the LP token details to find pool app ID
        def _do_fetch():
            url = f"{self.algod_address}/v2/assets/{asset_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()

        try:
            asset_data = retry_with_backoff(
                _do_fetch,
                max_retries=3,
                base_delay=1.0,
                operation_name=f"LPParser.pool_info_{asset_id}",
            )
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

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.debug(f"LP token {asset_id} not found on Algorand node")
            else:
                logger.warning(f"HTTP error fetching pool info for LP token {asset_id}: {e}")
        except Exception as e:
            logger.warning(f"Failed to get pool info for LP token {asset_id}: {e}")

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
        Fetch the underlying asset IDs by inspecting the pool account's holdings.

        On Algorand, a DEX pool account must opt-in to (and therefore hold) the
        ASAs it trades. By querying the pool account's asset holdings, we can
        determine which two assets the pool trades.

        Edge Cases:
            - If the pool account holds exactly 2 ASAs, those are the pair.
            - If the pool account holds exactly 1 ASA, the other asset is ALGO
              (ASA ID 0), since ALGO doesn't appear in the ``assets`` list.
            - If the pool account holds 0 or 3+ ASAs, we cannot reliably
              determine the pair and return (None, None).
            - Zero-balance assets are filtered out (``amount > 0``), so drained
              pools may return fewer assets than expected.

        Args:
            creator_address: The Algorand address of the pool account.

        Returns:
            Tuple of (asset1_id, asset2_id), or (None, None) if resolution fails.
        """
        def _do_fetch():
            url = f"{self.algod_address}/v2/accounts/{creator_address}"
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            return response.json()

        try:
            data = retry_with_backoff(
                _do_fetch,
                max_retries=3,
                base_delay=1.0,
                operation_name=f"LPParser.pool_assets_{creator_address[:8]}",
            )
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
            logger.warning(f"Failed to fetch pool assets for {creator_address[:8]}...: {e}")

        return None, None
    
    def get_pool_state(self, pool_address: str, lp_asset_id: int, asset1_id: int, asset2_id: int) -> Optional[dict]:
        """
        Query on-chain pool state via the Tinyman V2 SDK for exact reserves.

        This is the preferred (accurate) method for LP valuation. It uses the
        Tinyman Python SDK to fetch the actual pool reserves and total LP token
        supply directly from the blockchain application state.

        Tinyman vs Pact Difference:
            - **Tinyman**: Uses ``tinyman-py-sdk`` with ``TinymanV2MainnetClient``.
              Pool state is read from the Tinyman V2 application's local state.
            - **Pact**: Not directly supported by this method. Pact LP tokens
              fall through to the geometric mean fallback in ``estimate_lp_value``.

        Algorithm:
            1. Initialize an AlgodClient and TinymanV2MainnetClient
            2. Fetch Asset objects for both underlying assets
            3. Fetch the pool for the asset pair
            4. Read pool info (reserves, issued LP tokens) from app state
            5. Convert raw amounts from microunits using asset decimals

        Args:
            pool_address: The Algorand address of the pool account (unused by
                SDK but kept for interface consistency).
            lp_asset_id: The ASA ID of the LP token.
            asset1_id: ASA ID of the first underlying asset (0 for ALGO).
            asset2_id: ASA ID of the second underlying asset (0 for ALGO).

        Returns:
            Dict with keys:
                - ``total_supply``: Total LP tokens issued (in human-readable units)
                - ``reserve1``: Pool's reserve of asset 1 (human-readable)
                - ``reserve2``: Pool's reserve of asset 2 (human-readable)
            Returns None if the Tinyman SDK is not installed, the pool doesn't
            exist, or any error occurs during the query.

        Note:
            The Tinyman SDK import is done lazily inside this method so the
            module can still be used without the SDK installed (falling back
            to geometric mean estimation).
        """
        try:
            logger.debug(f"Using Tinyman SDK for LP {lp_asset_id} (assets: {asset1_id}, {asset2_id})")
            
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
                logger.debug(f"Tinyman pool not found for LP {lp_asset_id}")
                return None

            # Get pool info
            info = pool.info()
            logger.debug(f"Tinyman pool info keys for LP {lp_asset_id}: {list(info.keys())}")
            
            # Pool info is returned as a dict (not an object) from Tinyman V2.
            # LP token amounts are always in microunits with 6 decimals.
            total_supply = info.get('issued_pool_tokens', 0) / (10 ** 6)

            # Tinyman V2 SDK key names have varied between versions;
            # try both underscore formats to handle SDK version differences.
            r1 = info.get('asset_1_reserves') or info.get('asset1_reserves', 0)
            r2 = info.get('asset_2_reserves') or info.get('asset2_reserves', 0)

            # Convert from raw microunits to human-readable amounts
            # using each asset's declared decimal precision
            reserve1 = r1 / (10 ** asset1.decimals)
            reserve2 = r2 / (10 ** asset2.decimals)
            
            logger.debug(
                f"Tinyman SDK LP {lp_asset_id}: supply={total_supply:,.2f}, "
                f"{asset1.unit_name}={reserve1:,.2f}, {asset2.unit_name}={reserve2:,.2f}"
            )
            
            return {
                'total_supply': total_supply,
                'reserve1': reserve1,
                'reserve2': reserve2
            }
            
        except Exception as e:
            logger.warning(f"Tinyman SDK error for LP {lp_asset_id}: {e}")
            logger.debug(traceback.format_exc())
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
        # --- Step 1: Extract underlying asset tickers from LP token name ---
        # Strip the Tinyman prefix to isolate the pair, e.g. "XALGO-ALGO"
        # This simple split only works for hyphen-separated pairs; names with
        # multiple hyphens or other formats will fail and return None.
        parts = lp_name.replace("TinymanPool2.0 ", "").split("-")
        if len(parts) != 2:
            logger.debug(f"Could not parse LP name: {lp_name}")
            return None
            
        asset1_ticker = parts[0]
        asset2_ticker = parts[1]
        
        # --- Step 2: Resolve ASA IDs for the underlying assets ---
        # We need numeric ASA IDs to fetch prices and query pool state.
        # Primary method: query the pool account's holdings via get_pool_info.
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
        
        # --- Step 2b: Hardcoded fallback ASA ID mappings ---
        # If on-chain resolution failed (pool account query error, pool drained,
        # non-Tinyman pool, etc.), use known ASA IDs for common sovereignty assets.
        # This ensures pricing works even when the pool account is unreachable.
        if asset1_id is None or asset2_id is None:
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

        # --- Step 3: Fetch USD prices for both underlying assets ---
        # Pass both ticker and ASA ID to the pricing function for best resolution.
        # Tickers are NOT normalized (xALGO stays xALGO) to preserve pricing accuracy.
        price1 = get_price_fn(asset1_ticker, asset1_id) or 0
        price2 = get_price_fn(asset2_ticker, asset2_id) or 0

        # --- Step 4: Attempt exact valuation via Tinyman SDK (Method 1) ---
        # Query on-chain pool state for total LP supply and reserves.
        pool_state = None
        if pool_info and 'creator' in pool_info and asset1_id is not None and asset2_id is not None:
            pool_state = self.get_pool_state(
                pool_info['creator'],
                asset_id,
                asset1_id,
                asset2_id
            )
        
        # Check if pool state is valid AND has non-zero supply.
        # Zero supply means the pool is drained or the SDK returned bad data.
        if pool_state and pool_state['total_supply'] > 0:
            # User's proportional share of the pool = their LP tokens / total LP supply
            user_share = lp_amount / pool_state['total_supply']
            reserve1_value = pool_state['reserve1'] * price1
            reserve2_value = pool_state['reserve2'] * price2
            potential_total_usd = user_share * (reserve1_value + reserve2_value)
            
            if potential_total_usd > 0.01:  # Guard: skip near-zero values from stale/empty pools
                total_usd = potential_total_usd
                
                # Calculate user's share of each asset
                asset1_amount = user_share * pool_state['reserve1']
                asset2_amount = user_share * pool_state['reserve2']
                
                asset1_usd = asset1_amount * price1
                asset2_usd = asset2_amount * price2
                
                logger.debug(f"Tinyman formula: {lp_amount:.2f} LP / {pool_state['total_supply']:.2f} total = {user_share*100:.4f}% share = ${total_usd:.2f}")
                
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
                logger.debug(f"Tinyman SDK returned near-zero value (${potential_total_usd:.4f}) for {lp_ticker}, falling back to geometric mean")

        # --- Step 5: Fallback to geometric mean estimation (Method 2) ---
        # Reached when: Tinyman SDK not installed, pool not found, pool drained,
        # non-Tinyman pool (Pact, Humble), or SDK returned near-zero value.
        logger.debug(f"Pool state unavailable or invalid for {lp_ticker}, using geometric mean estimate")
        
        # If both prices are zero, we have no basis for estimation at all
        if price1 == 0 and price2 == 0:
            return None

        # Geometric Mean formula for constant-product AMM (x * y = k):
        # Value per LP token ≈ 2 × √(price_asset1 × price_asset2)
        # This assumes the pool is balanced (50/50 value split), which is
        # approximately true for well-arbitraged pools but less accurate
        # for imbalanced or low-liquidity pools.
        
        if price1 > 0 and price2 > 0:
            # Calculate value per LP token
            lp_token_value = 2 * math.sqrt(price1 * price2)
            
            total_usd = lp_amount * lp_token_value
            
            # Assume 50/50 value split (constant product AMM invariant)
            asset1_usd = total_usd / 2
            asset2_usd = total_usd / 2
            
            # Back-derive token amounts from USD values and prices
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
