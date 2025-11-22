import requests
import sys

class AlgorandSovereigntyAnalyzer:
    def __init__(self, use_local_node=True):
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
        
        # Load manual overrides from CSV (optional)
        self.load_classifications()

    def get_algo_price(self):
        """Fetch live ALGO price from CoinGecko API"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=algorand&vs_currencies=usd"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data['algorand']['usd']
        except Exception as e:
            # Silently fail and return None - we'll use fallback
            return None
        
    def load_classifications(self):
        """Load manual asset classification overrides from CSV"""
        self.classifications = {}
        try:
            with open('asset_classification.csv', 'r') as f:
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
            print("ℹ️  No asset_classificationscsv found - using auto-classification only\n")
    
    def auto_classify_asset(self, asset_id, name, ticker):
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
        name_upper = name.upper()
        
        # HARD MONEY: Wrapped Bitcoin, precious metals
        hard_money_patterns = [
            'GOBTC', 'WBTC', 'BTC', 
            'GOLD$', 'SILVER$', 'GOLD', 'SILVER',
            'XAUT',  # Tether Gold
        ]
        if any(pattern in ticker_upper for pattern in hard_money_patterns):
            return 'hard_money'
        
        # PRODUCTIVE ASSETS: LP tokens, liquid staking, stablecoins, lending
        productive_patterns = [
            'TMPOOL',      # Tinyman LP tokens
            'PACT',        # Pact LP tokens
            'PLP',         # Pact LP token
            'POOL',        # Generic pool tokens
            '-LP',         # Generic LP suffix
            'XALGO',       # Liquid staking ALGO
            'STALGO',      # Staked ALGO
            'USDC',        # Stablecoins
            'USDT', 
            'FUSD',
            'FUSDC',
            'FALGO',       # Folks wrapped ALGO
            'FOLKS',       # Folks Finance governance
            'GALGO',       # Governance ALGO
        ]
        if any(pattern in ticker_upper for pattern in productive_patterns):
            return 'productive'
        
        # NFTs: Domain names, verification badges, collectibles
        nft_patterns = [
            'NFD',         # NFDomains
            'VL0',         # Verification Lofty
            'AFK',         # AFK Elephants
            'SMC',         # Crypto collectibles
            'OGG',         # OG Governor badges
        ]
        
        # Check if ticker matches NFT patterns
        if any(pattern in ticker_upper for pattern in nft_patterns):
            return 'nft'
        
        # Check if it's likely an NFT by characteristics:
        # - Ticker is very short with numbers (like "VL008381")
        # - Has sequential numbering pattern
        if len(ticker) >= 5 and any(char.isdigit() for char in ticker):
            if ticker[:2].isalpha() and ticker[2:].isdigit():
                return 'nft'
        
        # SHITCOINS: Everything else
        # - Meme coins
        # - Prediction market tokens
        # - Gaming tokens
        # - Unclassified utility tokens
        return 'shitcoin'
    
    def get_account_assets(self, address):
        """Get all assets for an Algorand address"""
        url = f"{self.algod_address}/v2/accounts/{address}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching account data: {e}")
            return None
    
    def get_asset_details(self, asset_id):
        """Get details for a specific ASA"""
        url = f"{self.algod_address}/v2/assets/{asset_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Silently fail for asset detail fetching
            return None
    
    def analyze_wallet(self, address):
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
        
        categories[algo_category].append({
            'name': f'Algorand{participation_note}',
            'ticker': 'ALGO',
            'amount': algo_balance,
            'usd_value': 0
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
            category = self.auto_classify_asset(asset_id, name, ticker)
            
            # Override name/ticker if in manual classifications
            if str(asset_id) in self.classifications:
                name = self.classifications[str(asset_id)]['name']
                ticker = self.classifications[str(asset_id)]['ticker']
            
            categories[category].append({
                'name': name,
                'ticker': ticker,
                'amount': actual_amount,
                'usd_value': 0
            })
            
            processed += 1
        
        print(f"✅ Processed {processed} assets with non-zero balances\n")
        
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
    
    def print_results(self, categories, is_participating):
        """Print sovereignty analysis results"""
        print("\n" + "="*60)
        print("ALGORAND SOVEREIGNTY ANALYSIS")
        print("="*60 + "\n")
        
        # Hard Money
        print("💎 HARD MONEY ASSETS")
        print("-" * 60)
        hard_money_algo = 0
        if categories['hard_money']:
            for asset in categories['hard_money']:
                print(f"  {asset['ticker']:12} {asset['amount']:>18,.2f}  {asset['name']}")
                if asset['ticker'] == 'ALGO':
                    hard_money_algo = asset['amount']
            if hard_money_algo > 0:
                print(f"\n  {'TOTAL':12} {hard_money_algo:>18,.2f} ALGO")
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
                print(f"  {asset['ticker']:12} {amount_str:>18}  {asset['name']}")
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
        self.calculate_sovereignty_ratio(hard_money_algo)
    
    def calculate_sovereignty_ratio(self, hard_money_algo):
        """Calculate and display sovereignty ratio based on manual expense input"""
        print("\n" + "="*60)
        print("SOVEREIGNTY RATIO CALCULATOR")
        print("="*60 + "\n")
        
        print("To calculate your Sovereignty Ratio, we need your monthly fixed expenses.")
        print("(Rent/mortgage, insurance, utilities, minimum debt payments)\n")
        
        try:
            monthly_fixed = input("Enter your monthly FIXED expenses (USD): $")
            monthly_fixed = float(monthly_fixed.replace(',', ''))
            
            if monthly_fixed <= 0:
                print("\n⚠️  Invalid amount. Skipping sovereignty ratio calculation.\n")
                return
            
            # Calculate annual fixed expenses
            annual_fixed = monthly_fixed * 12
            
            # Get live ALGO price from CoinGecko
            algo_price = self.get_algo_price()
            
            if algo_price:
                print(f"\n✅ Live ALGO price: ${algo_price:.4f} (CoinGecko)")
            else:
                print(f"\n⚠️  Could not fetch live price, using fallback: $0.174")
                algo_price = 0.174
            print()
            
            # Calculate portfolio value in USD
            portfolio_usd = hard_money_algo * algo_price
            
            # Calculate Sovereignty Ratio
            sovereignty_ratio = portfolio_usd / annual_fixed
            
            # Determine sovereignty status
            if sovereignty_ratio >= 20:
                status = "Generationally Sovereign 🟩"
                color = "green"
            elif sovereignty_ratio >= 6:
                status = "Antifragile 🟢"
                color = "green"
            elif sovereignty_ratio >= 3:
                status = "Robust 🟡"
                color = "yellow"
            elif sovereignty_ratio >= 1:
                status = "Fragile 🔴"
                color = "red"
            else:
                status = "Vulnerable ⚫"
                color = "red"
            
            # Print results
            print("-" * 60)
            print("RESULTS:")
            print("-" * 60)
            print(f"Monthly Fixed Expenses:    ${monthly_fixed:>12,.2f}")
            print(f"Annual Fixed Expenses:     ${annual_fixed:>12,.2f}")
            print(f"Hard Money Portfolio:      ${portfolio_usd:>12,.2f}")
            print(f"\nSovereignty Ratio:         {sovereignty_ratio:>12,.2f}")
            print(f"Sovereignty Status:        {status}")
            print("-" * 60)
            
            # Show next level threshold
            if sovereignty_ratio < 20:
                next_thresholds = {
                    'Vulnerable': (1, 'Fragile 🔴'),
                    'Fragile': (3, 'Robust 🟡'),
                    'Robust': (6, 'Antifragile 🟢'),
                    'Antifragile': (20, 'Generationally Sovereign 🟩')
                }
                
                current_status_name = status.split()[0]
                if current_status_name in next_thresholds:
                    next_threshold, next_status = next_thresholds[current_status_name]
                    needed_usd = (next_threshold * annual_fixed) - portfolio_usd
                    needed_algo = needed_usd / algo_price
                    
                    print(f"\nTo reach {next_status}:")
                    print(f"  Need: ${needed_usd:,.2f} more ({needed_algo:,.0f} ALGO @ ${algo_price:.3f})")
                    print(f"  Target Ratio: {next_threshold}")
            
            print("="*60 + "\n")
            
            # Explanation
            print("💡 WHAT THIS MEANS:")
            print("-" * 60)
            print(f"Your hard money can cover {sovereignty_ratio:.1f} years of fixed expenses.")
            print(f"This means you could say 'no' to income for {sovereignty_ratio:.1f} years")
            print(f"and still cover your essential costs with just your ALGO.")
            print("\nSovereignty = Optionality = Freedom")
            print("="*60 + "\n")
            # Export sovereignty data
            sovereignty_data = {
                "monthly_fixed_expenses": monthly_fixed,
                "annual_fixed_expenses": annual_fixed,
                "algo_price": algo_price,
                "portfolio_usd": portfolio_usd,
                "sovereignty_ratio": round(sovereignty_ratio, 2),
                "sovereignty_status": status,
                "years_of_runway": round(sovereignty_ratio, 1)
            }
            
            # Re-export with sovereignty data included
            self.export_to_json(
                self.last_categories, 
                self.last_address, 
                self.last_is_participating, 
                self.last_hard_money_algo,
                sovereignty_data
            )
        except ValueError:
            print("\n⚠️  Invalid input. Skipping sovereignty ratio calculation.\n")
        except KeyboardInterrupt:
            print("\n\n⚠️  Calculation cancelled.\n")

     def export_to_json(self, categories, address, is_participating, hard_money_algo, sovereignty_data=None):
        """Export analysis results to JSON file"""
        import json
        from datetime import datetime
        
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
            export_data["sovereignty"] = sovereignty_data
        
        # Write to file
        filename = f"sovereignty_analysis_{address[:8]}.json"
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n💾 Results exported to: {filename}\n")
        return filename

def main():
    # Check if address provided
    if len(sys.argv) < 2:
        print("Usage: python3 algo_sovereignty.py <ALGORAND_ADDRESS>")
        print("\nExample:")
        print("  python3 algo_sovereignty.py I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4")
        sys.exit(1)
    
    address = sys.argv[1]
    
    # Try local node first, fallback to public API
    print("Attempting to use local node...")
    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=True)
    
    # Quick test if local node is accessible
    try:
        test = requests.get(f"{analyzer.algod_address}/health", headers=analyzer.headers, timeout=2)
        if test.status_code != 200:
            raise Exception("Local node not responding")
        print("✅ Connected to local node\n")
    except:
        print("⚠️  Local node not accessible, using public AlgoNode API\n")
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
    
    # Analyze the wallet
    analyzer.analyze_wallet(address)

if __name__ == "__main__":
    main()
