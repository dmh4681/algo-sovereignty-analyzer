"""
Seed script for Bitcoin price history.

Generates realistic historical data points for testing the chart.
Run this once to populate the database with sample data.

Usage:
    python scripts/seed_btc_history.py
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.btc_history import BTCPriceHistory, BTCPriceSnapshot


def generate_seed_data(days: int = 7, points_per_day: int = 24) -> list[BTCPriceSnapshot]:
    """
    Generate realistic historical BTC price data.

    Args:
        days: Number of days of history to generate
        points_per_day: Data points per day (24 = hourly)

    Returns:
        List of BTCPriceSnapshot objects
    """
    snapshots = []

    # Base prices (approximate current values)
    base_spot = 94000.0

    # Premium/discount ranges (realistic based on observed data)
    # goBTC typically trades at slight discount (-2% to +1%)
    # WBTC typically trades closer to spot (-1% to +1%)

    now = datetime.utcnow()
    start_time = now - timedelta(days=days)

    total_points = days * points_per_day
    interval_hours = (days * 24) / total_points

    # Random walk parameters
    spot_volatility = 0.002  # 0.2% per hour volatility
    gobtc_premium_mean = -0.8  # Average -0.8% discount
    gobtc_premium_std = 0.4   # Standard deviation
    wbtc_premium_mean = 0.2   # Average +0.2% premium
    wbtc_premium_std = 0.3    # Standard deviation

    current_spot = base_spot
    current_gobtc_premium = gobtc_premium_mean
    current_wbtc_premium = wbtc_premium_mean

    for i in range(total_points):
        timestamp = start_time + timedelta(hours=i * interval_hours)

        # Random walk for spot price
        spot_change = random.gauss(0, spot_volatility)
        current_spot *= (1 + spot_change)

        # Mean-reverting random walk for premiums
        gobtc_drift = (gobtc_premium_mean - current_gobtc_premium) * 0.1
        current_gobtc_premium += gobtc_drift + random.gauss(0, gobtc_premium_std * 0.3)
        current_gobtc_premium = max(-3.0, min(2.0, current_gobtc_premium))  # Clamp

        wbtc_drift = (wbtc_premium_mean - current_wbtc_premium) * 0.1
        current_wbtc_premium += wbtc_drift + random.gauss(0, wbtc_premium_std * 0.3)
        current_wbtc_premium = max(-2.0, min(2.0, current_wbtc_premium))  # Clamp

        # Calculate actual prices
        gobtc_price = current_spot * (1 + current_gobtc_premium / 100)
        wbtc_price = current_spot * (1 + current_wbtc_premium / 100)

        snapshot = BTCPriceSnapshot(
            timestamp=timestamp,
            spot_btc=round(current_spot, 2),
            gobtc_price=round(gobtc_price, 2),
            wbtc_price=round(wbtc_price, 2),
            gobtc_premium_pct=round(current_gobtc_premium, 2),
            wbtc_premium_pct=round(current_wbtc_premium, 2)
        )
        snapshots.append(snapshot)

    return snapshots


def seed_database(days: int = 7, clear_existing: bool = False):
    """
    Seed the database with historical data.

    Args:
        days: Days of history to generate
        clear_existing: If True, clear existing data first
    """
    history = BTCPriceHistory()

    if clear_existing:
        print("Clearing existing data...")
        history.cleanup_old_data(days=0)  # Clear all

    print(f"Generating {days} days of historical data...")
    snapshots = generate_seed_data(days=days, points_per_day=24)

    print(f"Inserting {len(snapshots)} data points...")

    # Bypass the duplicate check by inserting directly
    import sqlite3
    with sqlite3.connect(history.db_path) as conn:
        for snap in snapshots:
            conn.execute('''
                INSERT INTO btc_price_history
                (timestamp, spot_btc, gobtc_price, wbtc_price, gobtc_premium_pct, wbtc_premium_pct)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                snap.timestamp.isoformat(),
                snap.spot_btc,
                snap.gobtc_price,
                snap.wbtc_price,
                snap.gobtc_premium_pct,
                snap.wbtc_premium_pct
            ))
        conn.commit()

    # Verify
    stats = history.get_stats(hours=days * 24)
    print(f"\nSeeding complete!")
    print(f"  Data points: {stats['data_points']}")
    print(f"  goBTC avg premium: {stats['gobtc']['avg_premium_pct']:.2f}%")
    print(f"  WBTC avg premium: {stats['wbtc']['avg_premium_pct']:.2f}%")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Seed BTC price history database')
    parser.add_argument('--days', type=int, default=7, help='Days of history to generate (default: 7)')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    args = parser.parse_args()

    seed_database(days=args.days, clear_existing=args.clear)
