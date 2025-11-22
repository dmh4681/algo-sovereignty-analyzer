import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import AssetCategory, SovereigntyData
from .classifier import AssetClassifier
from .pricing import get_algo_price, get_asset_price

class AlgorandSovereigntyAnalyzer:
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
        
        # State storage for re-exporting
        self.last_categories: Dict[str, List[Dict[str, Any]]] = {}
        self.last_address: str = ""
        self.last_is_participating: bool = False
        self.last_hard_money_algo: float = 0.0

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
    
    def analyze_wallet(self, address: str) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """Analyze an Algorand wallet's sovereignty score"""
        print(f"\n🔍 Analyzing wallet: {address[:8]}...{address[-6:]}\n")
        
        # Get account data
        account_data = self.get_account_assets(address)
        if not account_data:
            return None
        
        # Initialize categories
        categories = {
            'hard_money': [],
            'productive': [],
            'nft': [],
            'shitcoin': []
        }
        
        # Check if participating in consensus
        is_participating = account_data.get('status') == 'Online'
        algo_balance = account_data['amount'] / 1_000_000
        
        # Add ALGO to appropriate category
        algo_category = 'hard_money' if is_participating else 'productive'
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
            
            # Auto-classify
            category = self.classifier.auto_classify_asset(asset_id, name, ticker)
            
            # Override name/ticker if in manual classifications
            if str(asset_id) in self.classifier.classifications:
                name = self.classifier.classifications[str(asset_id)]['name']
                ticker = self.classifier.classifications[str(asset_id)]['ticker']
            
            # Get price and calculate USD value
            price = get_asset_price(ticker)
            usd_value = 0.0
            if price:
                usd_value = actual_amount * price

            # Ensure category key exists
            if category not in categories:
                category = 'shitcoin'

            categories[category].append({
                'name': name,
                'ticker': ticker,
                'amount': actual_amount,
                'usd_value': usd_value
            })
            
            processed += 1
        
        print(f"✅ Processed {processed} assets with non-zero balances\n")
        
        # Calculate hard money algo amount for later use (legacy support)
        hard_money_algo = 0
        for asset in categories['hard_money']:
            if asset['ticker'] == 'ALGO':
                hard_money_algo = asset['amount']
                break

        # Store for later JSON export with sovereignty data
        self.last_categories = categories
        self.last_address = address
        self.last_is_participating = is_participating
        self.last_hard_money_algo = hard_money_algo
        
        # Print results
        self.print_results(categories, is_participating)
        
        # Export to JSON (without sovereignty data initially)
        self.export_to_json(categories, address, is_participating, hard_money_algo)
        
        return categories
    
    def print_results(self, categories: Dict[str, List[Dict[str, Any]]], is_participating: bool):
        """Print sovereignty analysis results"""
        print("\n" + "="*60)
        print("ALGORAND SOVEREIGNTY ANALYSIS")
        print("="*60 + "\n")
        
        # Hard Money
        print("💎 HARD MONEY ASSETS")
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
        
        # Productive Assets
        print("🌱 PRODUCTIVE ASSETS (Yield-Bearing)")
        print("-" * 60)
        productive_count = 0
        if categories['productive']:
            for asset in categories['productive']:
                amount_str = f"{asset['amount']:,.2f}" if asset['amount'] < 1000 else f"{asset['amount']:,.0f}"
                usd_str = f"${asset['usd_value']:,.2f}" if asset.get('usd_value', 0) > 0 else "-"
                print(f"  {asset['ticker']:12} {amount_str:>18} ({usd_str:>10})  {asset['name']}")
                productive_count += 1
            print(f"\n  Total positions: {productive_count}")
        else:
            print("  None")
        
        print("\n")
        
        # NFTs
        print("🎨 NFTs & COLLECTIBLES")
        print("-" * 60)
        nft_count = 0
        if categories['nft']:
            for asset in categories['nft']:
                amount_str = f"{asset['amount']:,.0f}"
                print(f"  {asset['ticker']:12} {amount_str:>18}  {asset['name']}")
                nft_count += 1
            print(f"\n  Total NFTs: {nft_count}")
        else:
            print("  None")
        
        print("\n")
        
        # Shitcoins
        print("💩 SHITCOINS")
        print("-" * 60)
        shitcoin_count = 0
        if categories['shitcoin']:
            for asset in categories['shitcoin']:
                amount_str = f"{asset['amount']:,.2f}" if asset['amount'] < 1000 else f"{asset['amount']:,.0f}"
                print(f"  {asset['ticker']:12} {amount_str:>18}  {asset['name']}")
                shitcoin_count += 1
            print(f"\n  Total shitcoins: {shitcoin_count}")
        else:
            print("  None")
        
        print("\n" + "="*60)
        print("SOVEREIGNTY SUMMARY")
        print("="*60)
        print(f"Participation Status: {'✅ ONLINE - Hard Money Status' if is_participating else '⚪ OFFLINE - Not Hard Money'}")
        print(f"Hard Money Assets: {len(categories['hard_money'])}")
        print(f"Productive Assets: {productive_count}")
        print(f"NFTs: {nft_count}")
        print(f"Shitcoins: {shitcoin_count}")
        print("="*60 + "\n")
        
        # SOVEREIGNTY RATIO CALCULATION
        # Note: In CLI mode we might not have expenses, so we skip or prompt
        # But here we just print results. The calculation method handles prompting if called directly.
    
    def calculate_sovereignty_metrics(self, categories: Dict[str, List[Dict[str, Any]]], monthly_fixed_expenses: float) -> Optional[SovereigntyData]:
        """Calculate sovereignty metrics based on TOTAL hard money portfolio and expenses"""
        if monthly_fixed_expenses <= 0:
            return None
            
        # Calculate annual fixed expenses
        annual_fixed = monthly_fixed_expenses * 12
        
        # Calculate total hard money portfolio value in USD
        portfolio_usd = 0.0
        for asset in categories.get('hard_money', []):
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
        
        # Build the export data
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
                "productive": [
                    {
                        "ticker": asset['ticker'],
                        "name": asset['name'],
                        "amount": asset['amount'],
                        "usd_value": asset.get('usd_value', 0)
                    }
                    for asset in categories['productive']
                ],
                "nft": [
                    {
                        "ticker": asset['ticker'],
                        "name": asset['name'],
                        "amount": asset['amount']
                    }
                    for asset in categories['nft']
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
                "productive_count": len(categories['productive']),
                "nft_count": len(categories['nft']),
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
