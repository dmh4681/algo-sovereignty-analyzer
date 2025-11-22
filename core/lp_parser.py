"""
LP Token Parser for Tinyman and other Algorand DEXes.

This module extracts the underlying asset values from LP tokens,
allowing proper classification of the component assets.
"""

import requests
import re
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
                # We'll estimate reserves later based on pricing
                'estimated': True
            }

        return None

    def estimate_lp_value(self, lp_ticker: str, lp_name: str, lp_amount: float,
                          asset_id: int, get_price_fn) -> Optional[LPBreakdown]:
        """
        Estimate the underlying value of LP tokens.

        Since querying on-chain pool state is complex, we'll use a simplified approach:
        - Parse the asset pair from the LP token name
        - Estimate 50/50 split of total value (common for most AMM pools)
        - Use current prices to calculate USD values
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

        # Get prices for both assets
        price1 = get_price_fn(asset1_ticker) or 0
        price2 = get_price_fn(asset2_ticker) or 0

        # If we have no price data, we can't estimate
        if price1 == 0 and price2 == 0:
            return None

        # For AMM pools, the value is typically split ~50/50
        # If we have both prices, estimate based on that
        # If we only have one price, we can estimate total value = 2 * known_value

        # This is a rough estimate - actual LP value depends on pool reserves
        # For now, we'll use LP amount as a proxy (most LP tokens have ~1:1 with total pool value)

        # Try to estimate based on known stablecoin value
        if asset2_ticker in ['USDC', 'USDT', 'DAI', 'FUSD']:
            # Asset 2 is a stablecoin, LP amount often represents total USD value
            total_usd = lp_amount  # Very rough estimate
            asset2_usd = total_usd / 2
            asset1_usd = total_usd / 2
            asset1_amount = asset1_usd / price1 if price1 > 0 else 0
            asset2_amount = asset2_usd  # Stablecoin
        elif asset1_ticker in ['USDC', 'USDT', 'DAI', 'FUSD']:
            # Asset 1 is a stablecoin
            total_usd = lp_amount
            asset1_usd = total_usd / 2
            asset2_usd = total_usd / 2
            asset1_amount = asset1_usd  # Stablecoin
            asset2_amount = asset2_usd / price2 if price2 > 0 else 0
        elif price1 > 0 and price2 > 0:
            # Both have prices, estimate based on typical LP mechanics
            # LP tokens are usually issued at sqrt(asset1 * asset2) or similar
            # For simplicity, assume total value = lp_amount * some_factor
            # This is very rough - in practice you'd query the pool
            total_usd = lp_amount * max(price1, price2) * 0.1  # Rough heuristic
            asset1_usd = total_usd / 2
            asset2_usd = total_usd / 2
            asset1_amount = asset1_usd / price1
            asset2_amount = asset2_usd / price2
        else:
            return None

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
