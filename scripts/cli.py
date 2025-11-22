import sys
import requests
import sys
import requests
# When running as a script from root with python -m scripts.cli, this import works
# if the root directory is in PYTHONPATH. 
# We'll assume the user runs it as `python -m scripts.cli` from the root.
from core.analyzer import AlgorandSovereigntyAnalyzer

def main():
    # Check if address provided
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <ALGORAND_ADDRESS>")
        print("\nExample:")
        print("  python3 main.py I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4")
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
