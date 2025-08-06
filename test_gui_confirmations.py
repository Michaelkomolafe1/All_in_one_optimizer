#!/usr/bin/env python3
"""
Test that confirmations work in GUI context - FIXED VERSION
"""

import sys
import os

# Fix the import paths
project_root = os.path.dirname(os.path.abspath(__file__))
if 'main_optimizer' not in project_root:
    # We're in the root, add main_optimizer to path
    sys.path.insert(0, os.path.join(project_root, 'main_optimizer'))
else:
    # We're in main_optimizer, add parent to path
    sys.path.insert(0, os.path.dirname(project_root))
    sys.path.insert(0, project_root)

# Now import
try:
    from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
except ImportError:
    from unified_core_system_updated import UnifiedCoreSystem

print("Testing Confirmation System in GUI Context")
print("=" * 50)

try:
    # Create system
    system = UnifiedCoreSystem()
    print("✓ System created")

    # Load CSV
    csv_path = "/home/michael/Downloads/DKSalaries(46).csv"
    if not os.path.exists(csv_path):
        print("ERROR: CSV file not found at:", csv_path)
        sys.exit(1)

    players_loaded = system.load_csv(csv_path)
    print("1. Loaded {} players".format(players_loaded))

    # Fetch confirmations
    print("\n2. Fetching confirmations...")
    confirmed = system.fetch_confirmed_players()
    print("   Fetched {} confirmed players".format(confirmed))

    # Check actual confirmed count
    actual_confirmed = 0
    for p in system.players:
        if hasattr(p, 'is_confirmed') and p.is_confirmed:
            actual_confirmed += 1
    print("3. Actually marked: {} players".format(actual_confirmed))

    # Build pool - confirmed only
    print("\n4. Building pools...")
    pool_confirmed = system.build_player_pool(include_unconfirmed=False)
    print("   Pool (confirmed only): {} players".format(pool_confirmed))

    # Build pool - all players
    pool_all = system.build_player_pool(include_unconfirmed=True)
    print("   Pool (all players): {} players".format(pool_all))

    # Summary
    print("\n" + "=" * 50)
    if pool_confirmed > 0:
        print("✅ CONFIRMATIONS WORKING!")
        print("   - Confirmed players: {}".format(pool_confirmed))
        print("   - All players: {}".format(pool_all))
        print("\nIn the GUI:")
        print("   ✓ With 'Confirmed Only' checked: {} players".format(pool_confirmed))
        print("   ✓ With 'Confirmed Only' unchecked: {} players".format(pool_all))
    else:
        print("⚠️ No confirmed players in pool")
        print("   Check if games have started for today")
        print("   Or just use all {} players (uncheck 'Confirmed Only')".format(pool_all))

except Exception as e:
    print("\n❌ Error:", str(e))
    import traceback

    traceback.print_exc()