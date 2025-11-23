import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.lp_parser import LPParser
from core.pricing import get_asset_price

def test_crash():
    print("Initializing LP Parser...")
    parser = LPParser()
    
    # Test case: fUSDC/fALGO LP
    # Ticker: TMPOOL2
    # Name: TinymanPool2.0 fUSDC-fALGO
    # Amount: 1544.69
    # Asset ID: Unknown (simulating resolution failure)
    
    print("Testing estimate_lp_value...")
    try:
        # We pass a dummy asset ID for the LP token
        # And get_asset_price as the price function
        breakdown = parser.estimate_lp_value(
            lp_ticker="TMPOOL2",
            lp_name="TinymanPool2.0 fUSDC-fALGO",
            lp_amount=1544.69,
            asset_id=123456789, # Dummy ID
            get_price_fn=get_asset_price
        )
        
        if breakdown:
            print("Success!")
            print(breakdown)
        else:
            print("Returned None")
            
    except Exception as e:
        print(f"Caught exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crash()
