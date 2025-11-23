"""
LP Token Parser for Tinyman and other Algorand DEXes.

This module extracts the underlying asset values from LP tokens,
allowing proper classification of the component assets.
"""

import requests
import re
import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class LPBreakdown:
    """Represents the breakdown of an LP token into its components"""
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
    """Parser for extracting underlying values from LP tokens"""

    def __init__(self, algod_address: str = "https://mainnet-api.algonode.cloud", headers: dict = None):
        self.algod_address = algod_address
        self.headers = headers or {}

        # Known Tinyman pool asset IDs (asset_id -> (asset1_id, asset2_id, app_id))
        # These are cached pool configurations
        self._pool_cache: Dict[int, Dict[str, Any]] = {}

    def _normalize_ticker(self, ticker: str) -> str:
        """
        Normalize wrapped/derivative token tickers to their base asset for pricing.
        fALGO, xALGO, FALGO -> ALGO
        fUSDC, FUSDC -> USDC
        etc.
        """
        t = ticker.upper()

        # Folks Finance wrapped ALGO variants
        if t in ['FALGO', 'XALGO'] or t.startswith('FALGO') or t.startswith('XALGO'):
            return 'ALGO'

        # Folks Finance wrapped USDC
        if t in ['FUSDC'] or t.startswith('FUSDC'):
            return 'USDC'

        # Folks Finance wrapped USDT
        if t in ['FUSDT'] or t.startswith('FUSDT'):
            return 'USDT'

        # Folks Finance wrapped goBTC
        if t in ['FGOBTC'] or t.startswith('FGOBTC'):
            return 'GOBTC'

        # Folks Finance wrapped goETH
        if t in ['FGOETH'] or t.startswith('FGOETH'):
            return 'GOETH'

        return ticker

    def is_lp_token(self, ticker: str, name: str) -> bool:
        """Check if an asset is likely an LP token"""
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
        """Parse Tinyman pool information from asset metadata"""

        # Try to extract asset pair from name (e.g., "TinymanPool2.0 ALGO-USDC")
        pair_match = re.search(r'(\w+)[/-](\w+)', name)
        if not pair_match:
            pair_match = re.search(r'(\w+)[/-](\w+)', unit_name)

        if pair_match:
            asset1_ticker = pair_match.group(1).upper()
            asset2_ticker = pair_match.group(2).upper()

            return {
                'asset1_ticker': asset1_ticker,
                'asset2_ticker': asset2_ticker,
                'lp_asset_id': asset_id,
                'creator': creator,
                'estimated': True
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

    def estimate_lp_value(self, lp_ticker: str, lp_name: str, lp_amount: float,
                          asset_id: int, get_price_fn) -> Optional[LPBreakdown]:
        """
        Estimate the underlying value of LP tokens.
        """

        pool_info = self.get_pool_info(asset_id)
        if not pool_info:
            # Try to parse from the name/ticker directly
            pair_match = re.search(r'(\w+)[/-](\w+)', lp_name)
            if not pair_match:
                pair_match = re.search(r'(\w+)[/-](\w+)', lp_ticker)
            if not pair_match:
                return None

            pool_info = {
                'asset1_ticker': pair_match.group(1).upper(),
                'asset2_ticker': pair_match.group(2).upper(),
                'estimated': True
            }

        asset1_ticker = pool_info['asset1_ticker']
        asset2_ticker = pool_info['asset2_ticker']
        
        # Try to resolve actual asset IDs from the pool creator address
        asset1_id = None
        asset2_id = None
        
        if 'creator' in pool_info:
            id1, id2 = self._get_pool_assets(pool_info['creator'])
            
            if id1 is not None and id2 is not None:
                # We have IDs. We'll assign them to asset1/asset2.
                # We try to match ALGO (0) if present.
                if id1 == 0:
                    if asset1_ticker == 'ALGO': asset1_id = 0; asset2_id = id2
                    else: asset1_id = id2; asset2_id = 0
                elif id2 == 0:
                    if asset1_ticker == 'ALGO': asset1_id = 0; asset2_id = id1
                    else: asset1_id = id1; asset2_id = 0
                else:
                    # Both are ASAs. Just assign in order.
                    asset1_id = id1
                    asset2_id = id2
            else:
                # Fallback: Try to map tickers to known Asset IDs
                # This ensures we get accurate pricing (premiums) even if node lookup fails
                known_ids = {
                    'ALGO': 0,
                    'USDC': 31566704,
                    'USDT': 312769,
                    'XALGO': 1134696561,
                    'FALGO': 3184331013,
                    'FUSDC': 3184331239,
                    'GOBTC': 386192725,
                    'GOETH': 386195940,
                    'WBTC': 1058926737,
                    'WETH': 1058926737, # Check this if needed, but usually same
                    'SILVER$': 246516580, # Meld Silver
                    'GOLD$': 246519683,   # Meld Gold
                }
                
                if asset1_id is None and asset1_ticker in known_ids:
                    asset1_id = known_ids[asset1_ticker]
                    
                if asset2_id is None and asset2_ticker in known_ids:
                    asset2_id = known_ids[asset2_ticker]

        # Get prices using resolved IDs if available, otherwise fallback to ticker
        # We do NOT normalize tickers anymore, so xALGO stays xALGO.
        price1 = get_price_fn(asset1_ticker, asset1_id) or 0
        price2 = get_price_fn(asset2_ticker, asset2_id) or 0

        # STRATEGY 1: Direct LP Token Pricing (The "Better Way")
        # Try to get the price of the LP token itself from Vestige
        # This is accurate because Vestige tracks the LP value directly
        lp_price = get_price_fn(lp_ticker, asset_id)
        
        if lp_price and lp_price > 0:
            total_usd = lp_amount * lp_price
            
            # We still need component prices to estimate amounts
            # If we can't get them, we'll make a best guess
            p1 = price1 if price1 > 0 else (1.0 if 'USDC' in asset1_ticker or 'USDT' in asset1_ticker else 0.15)
            p2 = price2 if price2 > 0 else (1.0 if 'USDC' in asset2_ticker or 'USDT' in asset2_ticker else 0.15)
            
            asset1_usd = total_usd / 2
            asset2_usd = total_usd / 2
            
            asset1_amount = asset1_usd / p1
            asset2_amount = asset2_usd / p2
            
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

        # STRATEGY 2: Component-based Pricing (Geometric Mean)
        # Fallback if Direct LP pricing fails
        
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
        Classify the components of an LP token breakdown.
        Returns a list of (category, asset_dict) tuples.
        """
        components = []

        # Use -1 as asset_id to ensure auto-classification (not manual CSV override)
        # Classify asset 1
        cat1 = classify_fn(-1, breakdown.asset1_ticker, breakdown.asset1_ticker)
        components.append((cat1, {
            'name': f'{breakdown.asset1_ticker} (from {breakdown.lp_ticker})',
            'ticker': breakdown.asset1_ticker,
            'amount': breakdown.asset1_amount,
            'usd_value': breakdown.asset1_usd,
            'from_lp': breakdown.lp_ticker
        }))

        # Classify asset 2
        cat2 = classify_fn(-1, breakdown.asset2_ticker, breakdown.asset2_ticker)
        components.append((cat2, {
            'name': f'{breakdown.asset2_ticker} (from {breakdown.lp_ticker})',
            'ticker': breakdown.asset2_ticker,
            'amount': breakdown.asset2_amount,
            'usd_value': breakdown.asset2_usd,
            'from_lp': breakdown.lp_ticker
        }))

        return components
