import sys
import os
sys.path.append(os.getcwd())

from core.analyzer import AlgorandSovereigntyAnalyzer

def test_real_wallet():
    print("Testing with real wallet address...")
    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)
    
    try:
        address = "I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4"
        print(f"Analyzing {address}...")
        categories = analyzer.analyze_wallet(address)
        
        if categories:
            print("\n✅ Analysis successful!")
            print(f"Hard Money: {len(categories.get('hard_money', []))} assets")
            print(f"Dollars: {len(categories.get('dollars', []))} assets")
            print(f"Algo: {len(categories.get('algo', []))} assets")
            print(f"Shitcoins: {len(categories.get('shitcoin', []))} assets")
        else:
            print("❌ Analysis returned None")
            
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_wallet()
