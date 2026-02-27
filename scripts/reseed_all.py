#!/usr/bin/env python3
"""
Reseed all precious metals databases with updated data.
Run this script to apply the latest seed data changes.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("RESEEDING ALL PRECIOUS METALS DATABASES")
    print("=" * 60)

    # 1. Reseed Inflation Data
    print("\n[1/4] Reseeding Inflation Data...")
    try:
        from core.inflation_data import get_inflation_db
        db = get_inflation_db()
        count = db.reseed()
        print(f"    Success! Reseeded {count} inflation data points")

        # Verify the fix
        latest = db.get_latest_data()
        if latest:
            print(f"    Latest date: {latest.date}")
            print(f"    Gold price: ${latest.gold_price:,.2f}/oz")
            print(f"    Silver price: ${latest.silver_price:.2f}/oz")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 2. Reseed Central Bank Gold
    print("\n[2/4] Reseeding Central Bank Gold Data...")
    try:
        from core.central_bank_gold import get_cb_gold_db
        db = get_cb_gold_db()
        count = db.reseed()
        print(f"    Success! Reseeded {count} central bank holdings records")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 3. Reseed Earnings Calendar
    print("\n[3/4] Reseeding Earnings Calendar...")
    try:
        from core.earnings_calendar import get_earnings_db
        db = get_earnings_db()
        count = db.reseed()
        print(f"    Success! Reseeded {count} earnings events")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 4. Reseed Premium Tracker
    print("\n[4/4] Reseeding Premium Tracker...")
    try:
        from core.premium_tracker import get_premium_db
        db = get_premium_db()
        count = db.reseed()
        print(f"    Success! Reseeded {count} premium price entries")

        # Verify spot prices
        summary = db.get_summary_stats()
        print(f"    Gold spot: ${summary.get('spot_prices', {}).get('gold', 'N/A')}")
        print(f"    Silver spot: ${summary.get('spot_prices', {}).get('silver', 'N/A')}")
    except Exception as e:
        print(f"    ERROR: {e}")

    print("\n" + "=" * 60)
    print("RESEED COMPLETE!")
    print("=" * 60)
    print("\nPlease restart your API server to see the changes.")

if __name__ == "__main__":
    main()
