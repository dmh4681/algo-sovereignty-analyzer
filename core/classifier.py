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
        Auto-classify assets based on sovereignty principles:
        - Hard Money: Censorship-resistant, scarce, widely accepted
        - Productive: Yield-bearing, stablecoins, LP tokens
        - NFT: Digital collectibles, domains
        - Shitcoin: Everything else
        """
        
        # Check manual overrides first
        if str(asset_id) in self.classifications:
            return self.classifications[str(asset_id)]['category']
        
        ticker_upper = ticker.upper()
        
        # HARD MONEY: Wrapped Bitcoin, precious metals
        # Matches exact BTC, WBTC, or patterns like goBTC, gold/silver tokens
        hard_money_patterns = [
            r'^WBTC$', r'^BTC$', r'^GOBTC$',
            r'GOLD', r'SILVER', r'^XAUT$',
            r'^PAXG$'
        ]
        if any(re.search(pattern, ticker_upper) for pattern in hard_money_patterns):
            return AssetCategory.HARD_MONEY.value
        
        # PRODUCTIVE ASSETS: LP tokens, liquid staking, stablecoins, lending
        productive_patterns = [
            r'TMPOOL',      # Tinyman LP tokens
            r'PACT',        # Pact LP tokens
            r'PLP$',        # Pact LP token suffix
            r'POOL',        # Generic pool tokens
            r'-LP$',        # Generic LP suffix
            r'^XALGO$',     # Liquid staking ALGO
            r'^STALGO$',    # Staked ALGO
            r'^USDC',       # Stablecoins
            r'^USDT', 
            r'^FUSD',
            r'^FALGO',      # Folks wrapped ALGO
            r'^FOLKS$',     # Folks Finance governance
            r'^GALGO$',     # Governance ALGO
            r'YIELD',
        ]
        if any(re.search(pattern, ticker_upper) for pattern in productive_patterns):
            return AssetCategory.PRODUCTIVE.value
        
        # NFTs: Domain names, verification badges, collectibles
        nft_patterns = [
            r'^NFD',        # NFDomains
            r'^VL\d+',      # Verification Lofty (e.g. VL0)
            r'^AFK$',       # AFK Elephants
            r'^SMC$',       # Crypto collectibles
            r'^OGG$',       # OG Governor badges
        ]
        
        # Check if ticker matches NFT patterns
        if any(re.search(pattern, ticker_upper) for pattern in nft_patterns):
            return AssetCategory.NFT.value
        
        # Check if it's likely an NFT by characteristics:
        # - Ticker is very short with numbers (like "VL008381")
        # - Has sequential numbering pattern
        if len(ticker) >= 5 and any(char.isdigit() for char in ticker):
            if ticker[:2].isalpha() and ticker[2:].isdigit():
                return AssetCategory.NFT.value
        
        # SHITCOINS: Everything else
        return AssetCategory.SHITCOINS.value if hasattr(AssetCategory, 'SHITCOINS') else 'shitcoin'
