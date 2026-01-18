"""
Algorand Sovereignty Analyzer - Core Wallet Analysis Engine

This module provides the main analysis logic for evaluating Algorand wallet holdings
through a hard money maximalist lens. It classifies assets into four categories:

1. Hard Money (BTC, Gold, Silver) - True sovereignty assets
2. Algo (ALGO, xALGO, etc.) - Platform native tokens
3. Dollars (USDC, USDT) - Stablecoin exposure
4. Shitcoins - Everything else

The Sovereignty Ratio is calculated as:
    Total Hard Money Value (USD) / Annual Fixed Expenses

This ratio determines how many years of essential expenses can be covered by
hard money assets alone, indicating true financial independence.

Example Usage:
    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
    categories = analyzer.analyze_wallet("ALGO_ADDRESS_HERE")
    metrics = analyzer.calculate_sovereignty_metrics(categories, monthly_expenses=4000)

Architecture Notes:
    - Uses classifier.py for asset categorization (CSV > User Corrections > Regex)
    - Uses pricing.py for multi-source price fetching (Vestige primary, CoinGecko fallback)
    - Uses lp_parser.py to decompose LP tokens into underlying assets
    - Caches last analysis results for sovereignty calculation and JSON export
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from .models import AssetCategory, SovereigntyData
from .classifier import AssetClassifier
from .pricing import get_algo_price, get_asset_price
from .lp_parser import LPParser

if TYPE_CHECKING:
    from .alerts import AlertEngine, Alert
    from .history import SovereigntySnapshot


class AlgorandSovereigntyAnalyzer:
    """
    Main analysis engine for Algorand wallet sovereignty scoring.

    This class fetches wallet data from the Algorand blockchain, classifies
    assets according to hard money maximalist principles, and calculates
    sovereignty metrics.

    Attributes:
        DUST_THRESHOLD_USD (float): Minimum USD value to include in analysis.
            Assets below this threshold are filtered as dust.
        NFT_MAX_AMOUNT (int): Maximum integer amount for NFT detection.
            Small integer holdings with no price data are treated as NFTs.
        algod_address (str): Algorand node API endpoint.
        classifier (AssetClassifier): Handles asset categorization.
        lp_parser (LPParser): Decomposes LP tokens into underlying assets.
        last_categories (dict): Cached results from most recent analysis.
        last_address (str): Address of most recent analysis.
        last_participation_info (dict): Consensus participation details.

    Sovereignty Status Levels:
        - Generationally Sovereign (≥20): 20+ years of hard money reserves
        - Antifragile (≥6): Benefits from volatility
        - Robust (≥3): Can weather major economic storms
        - Fragile (≥1): Building towards independence
        - Vulnerable (<1): Less than 1 year of coverage
    """

    # Minimum USD value to include in shitcoin category (filters dust)
    DUST_THRESHOLD_USD = 10.0
    # Maximum amount for NFT-like detection (small integer holdings)
    NFT_MAX_AMOUNT = 10

    def __init__(self, use_local_node: bool = True):
        if use_local_node:
            # Your local node
            self.algod_address = "http://127.0.0.1:8080"
            self.algod_token = "c61cbf17f80a4c5001ba61a1f7840b2cfb5f32fe65e0479257acc6dd71da0ad5"
            self.headers = {"Authorization": f"Bearer {self.algod_token}"}
        else:
            # Public AlgoNode API
            self.algod_address = "https://mainnet-api.algonode.cloud"
            self.algod_token = ""
            self.headers = {}
        
        self.classifier = AssetClassifier()
        self.lp_parser = LPParser(self.algod_address, self.headers)

        # State storage for re-exporting
        self.last_categories: Dict[str, List[Dict[str, Any]]] = {}
        self.last_address: str = ""
        self.last_is_participating: bool = False
        self.last_hard_money_algo: float = 0.0
        self.last_participation_info: Dict[str, Any] = {}

    def get_account_assets(self, address: str) -> Optional[Dict[str, Any]]:
        """Get all assets for an Algorand address"""
        url = f"{self.algod_address}/v2/accounts/{address}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching account data: {e}")
            return None
    
    def get_asset_details(self, asset_id: int) -> Optional[Dict[str, Any]]:
        """Get details for a specific ASA"""
        url = f"{self.algod_address}/v2/assets/{asset_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            # Silently fail for asset detail fetching
            return None

    def _is_dust_or_nft(self, amount: float, usd_value: float, price: Optional[float], name: str) -> bool:
        """
        Detect dust tokens and NFT-like items that should be filtered out.

        Criteria:
        - NFT-like: Small integer amount (1-10) with no price data
        - Dust: Very low USD value (< threshold) with no meaningful price
        - Reward tokens: Names containing 'reward', 'airdrop', etc. with low value
        """
        # NFT-like detection: small integer holdings with no price
        if amount <= self.NFT_MAX_AMOUNT and amount == int(amount) and price is None:
            return True

        # Dust detection: has a price but value is negligible
        if price is not None and usd_value < self.DUST_THRESHOLD_USD:
            # Check for reward/airdrop tokens which are often spam
            dust_keywords = ['reward', 'airdrop', 'free', 'bonus', 'promo']
            name_lower = name.lower()
            if any(keyword in name_lower for keyword in dust_keywords):
                return True
            # Still filter if value is truly negligible (< $1)
            if usd_value < 1.0:
                return True

        return False

    def analyze_wallet(self, address: str) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """
        Analyze an Algorand wallet and categorize all holdings.

        This is the main entry point for wallet analysis. It performs the following:
        1. Fetches all ASAs (Algorand Standard Assets) from the blockchain
        2. Classifies each asset into hard_money, algo, dollars, or shitcoin
        3. Decomposes LP tokens into their underlying assets
        4. Filters out dust tokens and NFT-like items
        5. Calculates USD values using multi-source pricing

        Args:
            address: 58-character Algorand wallet address

        Returns:
            Dict with four category keys, each containing a list of asset dicts:
            {
                'hard_money': [{'name': str, 'ticker': str, 'amount': float, 'usd_value': float}],
                'algo': [...],
                'dollars': [...],
                'shitcoin': [...]
            }
            Returns None if the wallet cannot be fetched.

        Side Effects:
            - Stores results in self.last_categories for later use
            - Exports results to JSON file: sovereignty_analysis_{address[:8]}.json
            - Prints analysis progress and results to console
        """
        print(f"\n🔍 Analyzing wallet: {address[:8]}...{address[-6:]}\n")
        
        # Get account data
        account_data = self.get_account_assets(address)
        if not account_data:
            return None
        
        # Initialize categories (4 categories now)
        categories = {
            'hard_money': [],
            'algo': [],
            'dollars': [],
            'shitcoin': []
        }

        # Check if participating in consensus
        is_participating = account_data.get('status') == 'Online'
        algo_balance = account_data['amount'] / 1_000_000

        # ALGO goes to 'algo' category
        algo_category = 'algo'
        participation_note = " (PARTICIPATING)" if is_participating else " (NOT PARTICIPATING)"
        
        # Get ALGO price
        algo_price = get_algo_price() or 0.0
        algo_usd_value = algo_balance * algo_price
        
        categories[algo_category].append({
            'name': f'Algorand{participation_note}',
            'ticker': 'ALGO',
            'amount': algo_balance,
            'usd_value': algo_usd_value
        })
        
        # Process ASAs
        assets = account_data.get('assets', [])
        print(f"Found {len(assets)} ASAs in wallet...\n")
        
        processed = 0
        for asset in assets:
            asset_id = asset['asset-id']
            amount = asset['amount']
            
            # Skip zero balances
            if amount == 0:
                continue
            
            # Get asset details
            details = self.get_asset_details(asset_id)
            if not details:
                continue
                
            params = details.get('params', {})
            decimals = params.get('decimals', 0)
            name = params.get('name', 'Unknown')
            ticker = params.get('unit-name', 'Unknown')
            
            # Calculate actual amount
            actual_amount = amount / (10 ** decimals)
            
            # Check if this is an LP token that we can parse
            if self.lp_parser.is_lp_token(ticker, name):
                # Try to break down LP token into components
                breakdown = self.lp_parser.estimate_lp_value(
                    ticker, name, actual_amount, asset_id, get_asset_price
                )

                if breakdown:
                    # Add the parsed components to appropriate categories
                    components = self.lp_parser.classify_lp_components(
                        breakdown,
                        self.classifier.auto_classify_asset
                    )

                    for comp_category, comp_asset in components:
                        # If classifier returns shitcoin but it's ALGO-related, move to algo
                        if comp_asset['ticker'] in ['ALGO', 'XALGO', 'FALGO']:
                            comp_category = 'algo'
                        
                        if comp_category not in categories:
                            comp_category = 'shitcoin'
                        categories[comp_category].append(comp_asset)

                    print(f"  📊 Parsed LP: {ticker} → {breakdown.asset1_ticker} + {breakdown.asset2_ticker}")
                    processed += 1
                    continue  # Skip adding the raw LP token

            # Auto-classify
            category = self.classifier.auto_classify_asset(asset_id, name, ticker)

            # Override name/ticker if in manual classifications
            if str(asset_id) in self.classifier.classifications:
                name = self.classifier.classifications[str(asset_id)]['name']
                ticker = self.classifier.classifications[str(asset_id)]['ticker']

            # Get price and calculate USD value
            price = get_asset_price(ticker, asset_id)
            usd_value = 0.0
            if price:
                usd_value = actual_amount * price

            # Ensure category key exists
            if category not in categories:
                # Check if it should be in algo category
                if ticker.upper() in ['ALGO', 'XALGO', 'FALGO']:
                    category = 'algo'
                else:
                    category = 'shitcoin'

            # Filter out dust tokens and NFT-like items from shitcoin category
            if category == 'shitcoin' and self._is_dust_or_nft(actual_amount, usd_value, price, name):
                continue  # Skip this asset

            categories[category].append({
                'name': name,
                'ticker': ticker,
                'amount': actual_amount,
                'usd_value': usd_value
            })

            processed += 1
        
        print(f"✅ Processed {processed} assets with non-zero balances\n")
        
        # Sort shitcoins by USD value (highest to lowest)
        categories['shitcoin'].sort(key=lambda x: x.get('usd_value', 0), reverse=True)
        
        # Calculate hard money algo amount for later use (legacy support)
        hard_money_algo = 0
        for asset in categories['hard_money']:
            if asset['ticker'] == 'ALGO':
                hard_money_algo = asset['amount']
                break

        # Extract participation key information
        participation_info = {}
        if is_participating:
            participation_data = account_data.get('participation', {})
            
            # Extract key expiration data
            vote_first_valid = participation_data.get('vote-first-valid')
            vote_last_valid = participation_data.get('vote-last-valid')
            
            # Calculate rounds until expiration if available
            key_expiration_rounds = None
            if vote_last_valid:
                key_expiration_rounds = vote_last_valid
            
            # Check incentive eligibility (mainnet threshold is typically 1 ALGO minimum)
            # For participation rewards, need to be online + have sufficient stake
            is_incentive_eligible = algo_balance >= 1.0
            
            # Estimated APY (Algorand participation rewards are ~4-5% currently)
            # This is a baseline estimate - actual rewards vary by network conditions
            estimated_apy = 4.5
            
            participation_info = {
                'staked_amount': algo_balance,
                'vote_first_valid': vote_first_valid,
                'vote_last_valid': vote_last_valid,
                'key_expiration_rounds': key_expiration_rounds,
                'is_incentive_eligible': is_incentive_eligible,
                'estimated_apy': estimated_apy
            }
        else:
            # Not participating - provide minimal info
            participation_info = {
                'staked_amount': 0.0,
                'vote_first_valid': None,
                'vote_last_valid': None,
                'key_expiration_rounds': None,
                'is_incentive_eligible': False,
                'estimated_apy': 0.0
            }

        # Store for later JSON export with sovereignty data
        self.last_categories = categories
        self.last_address = address
        self.last_is_participating = is_participating
        self.last_hard_money_algo = hard_money_algo
        self.last_participation_info = participation_info
        
        # Print results
        self.print_results(categories, is_participating)
        
        # Export to JSON (without sovereignty data initially)
        self.export_to_json(categories, address, is_participating, hard_money_algo)
        
        return categories
    
    def print_results(self, categories: Dict[str, List[Dict[str, Any]]], is_participating: bool):
        """Print sovereignty analysis results (hard money maximalist philosophy)"""
        print("\n" + "="*60)
        print("ALGORAND SOVEREIGNTY ANALYSIS")
        print("="*60 + "\n")

        # Hard Money (Bitcoin, Gold, Silver)
        print("💎 HARD MONEY (Bitcoin, Gold, Silver)")
        print("-" * 60)
        hard_money_total_usd = 0
        if categories['hard_money']:
            for asset in categories['hard_money']:
                usd_str = f"${asset['usd_value']:,.2f}" if asset['usd_value'] > 0 else "-"
                print(f"  {asset['ticker']:12} {asset['amount']:>18,.2f} ({usd_str:>10})  {asset['name']}")
                hard_money_total_usd += asset.get('usd_value', 0)
            print(f"\n  {'TOTAL USD':12} ${hard_money_total_usd:,.2f}")
        else:
            print("  None")

        print("\n")

        # Algorand
        print("Ⱥ ALGORAND")
        print("-" * 60)
        algo_total_usd = 0
        if categories['algo']:
            for asset in categories['algo']:
                amount_str = f"{asset['amount']:,.2f}" if asset['amount'] < 1000 else f"{asset['amount']:,.0f}"
                usd_str = f"${asset['usd_value']:,.2f}" if asset.get('usd_value', 0) > 0 else "-"
                print(f"  {asset['ticker']:12} {amount_str:>18} ({usd_str:>10})  {asset['name']}")
                algo_total_usd += asset.get('usd_value', 0)
            print(f"\n  {'TOTAL USD':12} ${algo_total_usd:,.2f}")
        else:
            print("  None")

        print("\n")

        # Dollars (Stablecoins)
        print("💵 DOLLARS (Stablecoins)")
        print("-" * 60)
        dollars_total_usd = 0
        dollars_count = 0
        if categories['dollars']:
            for asset in categories['dollars']:
                amount_str = f"{asset['amount']:,.2f}" if asset['amount'] < 1000 else f"{asset['amount']:,.0f}"
                usd_str = f"${asset['usd_value']:,.2f}" if asset.get('usd_value', 0) > 0 else "-"
                print(f"  {asset['ticker']:12} {amount_str:>18} ({usd_str:>10})  {asset['name']}")
                dollars_total_usd += asset.get('usd_value', 0)
                dollars_count += 1
            print(f"\n  {'TOTAL USD':12} ${dollars_total_usd:,.2f}")
        else:
            print("  None")

        print("\n")

        # Shitcoins (Everything Else)
        print("💩 SHITCOINS (Everything Else)")
        print("-" * 60)
        shitcoin_count = 0
        if categories['shitcoin']:
            for asset in categories['shitcoin']:
                amount_str = f"{asset['amount']:,.2f}" if asset['amount'] < 1000 else f"{asset['amount']:,.0f}"
                usd_str = f"${asset['usd_value']:,.2f}" if asset.get('usd_value', 0) > 0 else "-"
                print(f"  {asset['ticker']:12} {amount_str:>18} ({usd_str:>10})  {asset['name']}")
                shitcoin_count += 1
            print(f"\n  Total shitcoins: {shitcoin_count}")
        else:
            print("  None")

        print("\n" + "="*60)
        print("SOVEREIGNTY SUMMARY")
        print("="*60)
        print(f"Participation Status: {'✅ ONLINE' if is_participating else '⚪ OFFLINE'}")
        print(f"Hard Money Assets: {len(categories['hard_money'])} (BTC, Gold, Silver)")
        print(f"Algorand Assets: {len(categories['algo'])}")
        print(f"Dollars: {dollars_count} (Stablecoins)")
        print(f"Shitcoins: {shitcoin_count} (Everything Else)")
        print("="*60 + "\n")

        # SOVEREIGNTY RATIO CALCULATION
        # Note: In CLI mode we might not have expenses, so we skip or prompt
        # But here we just print results. The calculation method handles prompting if called directly.
    
    def calculate_sovereignty_metrics(self, categories: Dict[str, List[Dict[str, Any]]], monthly_fixed_expenses: float) -> Optional[SovereigntyData]:
        """
        Calculate sovereignty metrics from categorized holdings and expenses.

        The core formula is:
            Sovereignty Ratio = Total Portfolio USD / Annual Fixed Expenses

        Note: The ratio uses the FULL portfolio value (all categories), not just
        hard money. This gives a complete picture of financial runway.

        Args:
            categories: Output from analyze_wallet() with asset categories
            monthly_fixed_expenses: User's monthly fixed costs in USD
                (rent/mortgage, utilities, insurance, minimum debt payments)

        Returns:
            SovereigntyData object containing:
                - monthly_fixed_expenses: Input value
                - annual_fixed_expenses: monthly × 12
                - algo_price: Current ALGO/USD price
                - portfolio_usd: Total portfolio value
                - sovereignty_ratio: years of runway
                - sovereignty_status: human-readable status with emoji
                - years_of_runway: same as ratio (alias)
            Returns None if monthly_fixed_expenses <= 0.

        Status Thresholds:
            ≥20 → "Generationally Sovereign 🟩"
            ≥6  → "Antifragile 🟢"
            ≥3  → "Robust 🟡"
            ≥1  → "Fragile 🔴"
            <1  → "Vulnerable ⚫"
        """
        if monthly_fixed_expenses <= 0:
            return None
            
        # Calculate annual fixed expenses
        annual_fixed = monthly_fixed_expenses * 12
        
        # Calculate total portfolio value in USD (Hard Money + Algo + Dollars + Shitcoins)
        portfolio_usd = 0.0
        for category in ['hard_money', 'algo', 'dollars', 'shitcoin']:
            for asset in categories.get(category, []):
                portfolio_usd += asset.get('usd_value', 0.0)
            
        # Get ALGO price for reference
        algo_price = get_algo_price() or 0.174
        
        # Calculate Sovereignty Ratio
        sovereignty_ratio = portfolio_usd / annual_fixed
        
        # Determine sovereignty status
        if sovereignty_ratio >= 20:
            status = "Generationally Sovereign 🟩"
        elif sovereignty_ratio >= 6:
            status = "Antifragile 🟢"
        elif sovereignty_ratio >= 3:
            status = "Robust 🟡"
        elif sovereignty_ratio >= 1:
            status = "Fragile 🔴"
        else:
            status = "Vulnerable ⚫"
            
        return SovereigntyData(
            monthly_fixed_expenses=monthly_fixed_expenses,
            annual_fixed_expenses=annual_fixed,
            algo_price=algo_price,
            portfolio_usd=portfolio_usd,
            sovereignty_ratio=round(sovereignty_ratio, 2),
            sovereignty_status=status,
            years_of_runway=round(sovereignty_ratio, 1)
        )

    def calculate_sovereignty_ratio(self, hard_money_algo: float):
        """Calculate and display sovereignty ratio based on manual expense input"""
        print("\n" + "="*60)
        print("SOVEREIGNTY RATIO CALCULATOR")
        print("="*60 + "\n")
        
        print("To calculate your Sovereignty Ratio, we need your monthly fixed expenses.")
        print("(Rent/mortgage, insurance, utilities, minimum debt payments)\n")
        
        try:
            monthly_fixed_input = input("Enter your monthly FIXED expenses (USD): $")
            monthly_fixed = float(monthly_fixed_input.replace(',', ''))
            
            # Use the new metrics calculation with self.last_categories
            metrics = self.calculate_sovereignty_metrics(self.last_categories, monthly_fixed)
            
            if not metrics:
                print("\n⚠️  Invalid amount. Skipping sovereignty ratio calculation.\n")
                return

            # Print results
            print("-" * 60)
            print("RESULTS:")
            print("-" * 60)
            print(f"Monthly Fixed Expenses:    ${metrics.monthly_fixed_expenses:>12,.2f}")
            print(f"Annual Fixed Expenses:     ${metrics.annual_fixed_expenses:>12,.2f}")
            print(f"Hard Money Portfolio:      ${metrics.portfolio_usd:>12,.2f}")
            print(f"\nSovereignty Ratio:         {metrics.sovereignty_ratio:>12,.2f}")
            print(f"Sovereignty Status:        {metrics.sovereignty_status}")
            print("-" * 60)
            
            # Show next level threshold
            if metrics.sovereignty_ratio < 20:
                next_thresholds = {
                    'Vulnerable': (1, 'Fragile 🔴'),
                    'Fragile': (3, 'Robust 🟡'),
                    'Robust': (6, 'Antifragile 🟢'),
                    'Antifragile': (20, 'Generationally Sovereign 🟩')
                }
                
                current_status_name = metrics.sovereignty_status.split()[0]
                if current_status_name in next_thresholds:
                    next_threshold, next_status = next_thresholds[current_status_name]
                    needed_usd = (next_threshold * metrics.annual_fixed_expenses) - metrics.portfolio_usd
                    # Just estimate needed ALGO based on current price
                    needed_algo = needed_usd / metrics.algo_price
                    
                    print(f"\nTo reach {next_status}:")
                    print(f"  Need: ${needed_usd:,.2f} more (~{needed_algo:,.0f} ALGO)")
                    print(f"  Target Ratio: {next_threshold}")
            
            print("="*60 + "\n")
            
            # Explanation
            print("💡 WHAT THIS MEANS:")
            print("-" * 60)
            print(f"Your hard money can cover {metrics.sovereignty_ratio:.1f} years of fixed expenses.")
            print(f"This means you could say 'no' to income for {metrics.sovereignty_ratio:.1f} years")
            print(f"and still cover your essential costs with just your hard money assets.")
            print("\nSovereignty = Optionality = Freedom")
            print("="*60 + "\n")
            
            # Re-export with sovereignty data included
            self.export_to_json(
                self.last_categories, 
                self.last_address, 
                self.last_is_participating, 
                self.last_hard_money_algo,
                metrics
            )
        except ValueError:
            print("\n⚠️  Invalid input. Skipping sovereignty ratio calculation.\n")
        except KeyboardInterrupt:
            print("\n\n⚠️  Calculation cancelled.\n")

    def export_to_json(self, categories: Dict[str, List[Dict[str, Any]]], address: str, 
                       is_participating: bool, hard_money_algo: float, 
                       sovereignty_data: Optional[SovereigntyData] = None):
        """Export analysis results to JSON file"""
        
        # Build the export data (3 categories: hard money maximalist philosophy)
        export_data = {
            "metadata": {
                "analyzed_at": datetime.now().isoformat(),
                "address": address,
                "address_short": f"{address[:8]}...{address[-6:]}",
                "participation_status": "online" if is_participating else "offline"
            },
            "assets": {
                "hard_money": [
                    {
                        "ticker": asset['ticker'],
                        "name": asset['name'],
                        "amount": asset['amount'],
                        "usd_value": asset.get('usd_value', 0)
                    }
                    for asset in categories['hard_money']
                ],
                "algo": [
                    {
                        "ticker": asset['ticker'],
                        "name": asset['name'],
                        "amount": asset['amount'],
                        "usd_value": asset.get('usd_value', 0)
                    }
                    for asset in categories['algo']
                ],
                "dollars": [
                    {
                        "ticker": asset['ticker'],
                        "name": asset['name'],
                        "amount": asset['amount'],
                        "usd_value": asset.get('usd_value', 0)
                    }
                    for asset in categories['dollars']
                ],
                "shitcoin": [
                    {
                        "ticker": asset['ticker'],
                        "name": asset['name'],
                        "amount": asset['amount'],
                        "usd_value": asset.get('usd_value', 0)
                    }
                    for asset in categories['shitcoin']
                ]
            },
            "summary": {
                "hard_money_count": len(categories['hard_money']),
                "dollars_count": len(categories['dollars']),
                "shitcoin_count": len(categories['shitcoin']),
                "total_algo": hard_money_algo
            }
        }
        
        # Add sovereignty ratio data if provided
        if sovereignty_data:
            export_data["sovereignty"] = sovereignty_data.dict()
        
        # Write to file
        filename = f"sovereignty_analysis_{address[:8]}.json"
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n💾 Results exported to: {filename}\n")
        return filename

    def generate_alerts(
        self,
        categories: Dict[str, List[Dict[str, Any]]],
        sovereignty_data: Optional[SovereigntyData] = None,
        history: Optional[List["SovereigntySnapshot"]] = None,
        user_prefs: Optional[Dict[str, Any]] = None
    ) -> List["Alert"]:
        """
        Generate sovereignty alerts based on current analysis.

        Args:
            categories: Asset categories from wallet analysis
            sovereignty_data: Current sovereignty metrics (may be None if no expenses)
            history: Historical snapshots for comparison
            user_prefs: User preferences for alerts

        Returns:
            List of Alert objects
        """
        from .alerts import AlertEngine

        alert_engine = AlertEngine()
        return alert_engine.generate_all_alerts(
            categories=categories,
            sovereignty_data=sovereignty_data,
            history=history,
            user_prefs=user_prefs
        )
