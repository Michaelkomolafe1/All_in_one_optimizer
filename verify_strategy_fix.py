#!/usr/bin/env python3
"""Verify the strategy filter fix"""

import sys
sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem

print("=" * 50)
print("VERIFYING STRATEGY FILTER FIX")
print("=" * 50)

# Test each strategy
strategies = ['projection_monster', 'balanced_projections', 'balanced_ownership', 'value_beast']
contest_types = ['cash', 'gpp']

system = UnifiedCoreSystem()

# You'll need to update this path to your actual CSV file
csv_path = "/home/michael/Downloads/DKSalaries(46).csv"  
system.load_csv(csv_path)
system.fetch_confirmed_players()

results = []
for contest_type in contest_types:
    print(f"\nTesting {contest_type.upper()} contests:")

    for strategy in strategies:
        # Build pool with confirmed only
        system.build_player_pool(include_unconfirmed=False)

        print(f"  {strategy}:", end=" ")

        # Try to generate lineup
        try:
            lineups = system.optimize_lineup(
                strategy=strategy,
                contest_type=contest_type,
                num_lineups=1
            )

            if lineups and len(lineups) > 0:
                print(f"✅ SUCCESS - Generated lineup with {len(lineups[0])} players")
                results.append((contest_type, strategy, True))
            else:
                print(f"❌ FAILED - Could not generate lineup")
                results.append((contest_type, strategy, False))
        except Exception as e:
            print(f"❌ ERROR - {str(e)}")
            results.append((contest_type, strategy, False))

print("\n" + "=" * 50)
print("SUMMARY:")
print("=" * 50)

success_count = sum(1 for _, _, success in results if success)
total_count = len(results)

print(f"Success Rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

if success_count == total_count:
    print("\n✅ ALL STRATEGIES WORKING! The fix is successful!")
else:
    print("\n⚠️ Some strategies still failing. Check the logs above.")

print("=" * 50)
