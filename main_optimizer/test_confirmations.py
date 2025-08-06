#!/usr/bin/env python3
"""Test confirmation system"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the system
from unified_core_system_updated import UnifiedCoreSystem

def test_confirmations():
    print("=" * 60)
    print("TESTING CONFIRMATION SYSTEM")
    print("=" * 60)

    # Create system
    system = UnifiedCoreSystem()

    # Load CSV
    csv_path = "/home/michael/Downloads/DKSalaries(46).csv"
    count = system.load_csv(csv_path)
    print(f"\n✓ Loaded {count} players")

    # Try fetching confirmations
    print("\nFetching confirmations...")
    confirmed = system.fetch_confirmed_players()
    print(f"✓ Found {confirmed} confirmed players")

    # Build pool with confirmed only
    print("\nBuilding pool (confirmed only)...")
    pool_size = system.build_player_pool(include_unconfirmed=False)
    print(f"Pool size (confirmed only): {pool_size}")

    # Build pool with all
    print("\nBuilding pool (all players)...")
    pool_size = system.build_player_pool(include_unconfirmed=True)
    print(f"Pool size (all players): {pool_size}")

    # Show some confirmed players
    if confirmed > 0:
        print("\nSample confirmed players:")
        count = 0
        for p in system.players:
            if hasattr(p, 'is_confirmed') and p.is_confirmed:
                print(f"  ✓ {p.name} ({p.team})")
                count += 1
                if count >= 5:
                    break

if __name__ == "__main__":
    test_confirmations()
