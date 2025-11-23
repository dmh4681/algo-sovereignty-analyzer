import sys
import os
sys.path.append(os.getcwd())

from core.lp_parser import LPParser
from core.pricing import get_asset_price

def test_tinyman_lp():
    print("Testing Tinyman LP valuation...")
    parser = LPParser()
    
    # Test xALGO/ALGO pool
    # Expected from Tinyman: $6,880.11
    print("\n=== xALGO/ALGO Pool ===")
    print("Expected value from Tinyman: $6,880.11")
    print("LP tokens held: 20,563.221469")
    
    breakdown = parser.estimate_lp_value(
        lp_ticker="TMPOOL2",
        lp_name="TinymanPool2.0 xALGO-ALGO",
        lp_amount=20563.221469,
        asset_id=1067294154,  # xALGO/ALGO LP token ID (you'll need to verify this)
        get_price_fn=get_asset_price
    )
    
    if breakdown:
        print(f"\nCalculated value: ${breakdown.total_usd:.2f}")
        print(f"Asset 1 ({breakdown.asset1_ticker}): {breakdown.asset1_amount:.2f} (${breakdown.asset1_usd:.2f})")
        print(f"Asset 2 ({breakdown.asset2_ticker}): {breakdown.asset2_amount:.2f} (${breakdown.asset2_usd:.2f})")
        
        diff = abs(breakdown.total_usd - 6880.11)
        print(f"\nDifference from Tinyman: ${diff:.2f}")
        if diff < 10:
            print("✅ MATCH! Within $10 of Tinyman value")
        else:
            print(f"❌ OFF by ${diff:.2f}")
    else:
        print("❌ Failed to calculate LP value")
    
    # Test fUSDC/fALGO pool
    print("\n\n=== fUSDC/fALGO Pool ===")
    print("Expected value from Tinyman: $1,667.52")
    print("LP tokens held: 1,544.696742")
    
    breakdown2 = parser.estimate_lp_value(
        lp_ticker="TMPOOL2",
        lp_name="TinymanPool2.0 fUSDC-fALGO",
        lp_amount=1544.696742,
        asset_id=1067257070,  # fUSDC/fALGO LP token ID (you'll need to verify this)
        get_price_fn=get_asset_price
    )
    
    if breakdown2:
        print(f"\nCalculated value: ${breakdown2.total_usd:.2f}")
        print(f"Asset 1 ({breakdown2.asset1_ticker}): {breakdown2.asset1_amount:.2f} (${breakdown2.asset1_usd:.2f})")
        print(f"Asset 2 ({breakdown2.asset2_ticker}): {breakdown2.asset2_amount:.2f} (${breakdown2.asset2_usd:.2f})")
        
        diff = abs(breakdown2.total_usd - 1667.52)
        print(f"\nDifference from Tinyman: ${diff:.2f}")
        if diff < 10:
            print("✅ MATCH! Within $10 of Tinyman value")
        else:
            print(f"❌ OFF by ${diff:.2f}")
    else:
        print("❌ Failed to calculate LP value")

if __name__ == "__main__":
    test_tinyman_lp()
