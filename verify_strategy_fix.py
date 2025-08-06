#!/usr/bin/env python3
"""Verify the strategy filter fix"""

import sys
sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem

print("=" * 50)
print("VERIFYING STRATEGY FILTER FIX")
print("=" * 50)

# Test each strategy
strategies = ['projection_monster', 'balanced_projections', 'value_beast']
contest_types = ['cash', 'gpp']

system = UnifiedCoreSystem()
csv_path = "/home/michael/Downloads/DKSalaries(46).csv"
system.load_csv(csv_path)
system.fetch_confirmed_players()

for contest_type in contest_types:
    print(f"\nTesting {contest_type.upper()} contests:")

    for strategy in strategies:
        # Build pool with confirmed only
        system.build_player_pool(include_unconfirmed=False)

        print(f"  {strategy}:", end=" ")

        # Try to generate lineup
        lineups = system.optimize_lineup(
            strategy=strategy,
            contest_type=contest_type,
            num_lineups=1
        )

        if lineups and len(lineups) > 0:
            print(f"✅ SUCCESS - Generated lineup")
        else:
            print(f"❌ FAILED - Could not generate lineup")

print("\n" + "=" * 50)
print("All strategies should show SUCCESS")
