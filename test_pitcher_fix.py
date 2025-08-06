#!/usr/bin/env python3
"""Test pitcher filtering fix"""

import sys
sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem

print("Testing pitcher filtering fix...")
print("=" * 50)

# Create system and load CSV
system = UnifiedCoreSystem()
csv_path = "/home/michael/Downloads/DKSalaries(46).csv"

# Load and setup
system.load_csv(csv_path)
system.fetch_confirmed_players()
system.build_player_pool(include_unconfirmed=False)

print(f"Total players in pool: {len(system.player_pool)}")

# Count positions
position_counts = {}
for p in system.player_pool:
    pos = p.position
    if pos not in position_counts:
        position_counts[pos] = 0
    position_counts[pos] += 1

print("\nPositions in pool:")
for pos, count in sorted(position_counts.items()):
    print(f"  {pos}: {count} players")

# Try optimization
print("\nTrying optimization...")
lineups = system.optimize_lineup(
    strategy='projection_monster',
    contest_type='cash',
    num_lineups=1
)

if lineups:
    print(f"✅ SUCCESS! Generated {len(lineups)} lineup(s)")
else:
    print("❌ Failed to generate lineups")
