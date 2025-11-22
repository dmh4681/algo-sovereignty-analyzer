import re
from typing import Dict, Any, Optional
from .models import AssetCategory

class AssetClassifier:
    def __init__(self, classification_file: str = 'data/asset_classification.csv'):
        self.classifications: Dict[str, Dict[str, str]] = {}
        self.load_classifications(classification_file)

    def load_classifications(self, filepath: str) -> None:
        """Load manual asset classification overrides from CSV"""
        self.classifications = {}
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()[1:]  # Skip header
                for line in lines:
                    parts = line.strip().split(',')
                    if len(parts) >= 4:
                        asset_id = parts[0]
                        self.classifications[asset_id] = {
                            'name': parts[1],
                            'ticker': parts[2],
                            'category': parts[3]
                        }
        except FileNotFoundError:
            print("ℹ️  No asset_classifications.csv found - using auto-classification only\n")

    def auto_classify_asset(self, asset_id: int, name: str, ticker: str) -> str:
        """
        Hard money maximalist classification:
        - Hard Money: BTC, Gold, Silver ONLY
        - Dollars: Stablecoins (fiat-pegged)
        - Shitcoin: Everything else (including ALGO)
        """

        # Check manual overrides first
        if str(asset_id) in self.classifications:
            return self.classifications[str(asset_id)]['category']

        ticker_upper = ticker.upper()

        # HARD MONEY: Bitcoin, Gold, Silver ONLY
        hard_money_patterns = [
            r'^WBTC$', r'^BTC$', r'^GOBTC$',           # Bitcoin
            r'GOLD', r'^XAUT$', r'^PAXG$',              # Gold
            r'SILVER',                                   # Silver
        ]
        if any(re.search(pattern, ticker_upper) for pattern in hard_money_patterns):
            return AssetCategory.HARD_MONEY.value

        # DOLLARS: Stablecoins (fiat-pegged assets)
        # Includes Folks Finance wrapped versions (fUSDC, etc.)
        dollar_patterns = [
            r'^USDC',       # USDC
            r'^FUSDC',      # Folks wrapped USDC
            r'^USDT',       # USDT / USDt
            r'^DAI$',       # DAI
            r'^FUSD',       # FUSD
        ]
        if any(re.search(pattern, ticker_upper) for pattern in dollar_patterns):
            return AssetCategory.DOLLARS.value

        # EVERYTHING ELSE: Shitcoins (including ALGO, LP tokens, NFTs, governance tokens)
        return AssetCategory.SHITCOIN.value
