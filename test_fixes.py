#!/usr/bin/env python3
"""Test the fixes"""

import sys
import os
sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem

print("Testing system...")
system = UnifiedCoreSystem()

# Load CSV
csv_path = "/home/michael/Downloads/DKSalaries(46).csv"
count = system.load_csv(csv_path)
print(f"Loaded {count} players")

# Build pool with all players
pool_size = system.build_player_pool(include_unconfirmed=True)
print(f"Player pool: {pool_size} players")

# Check for None values
none_count = 0
for p in system.player_pool:
    if p.base_projection is None or p.optimization_score is None:
        none_count += 1
        print(f"  Player {p.name} has None values!")

if none_count == 0:
    print("✓ No None values found - optimization should work!")
else:
    print(f"⚠ Found {none_count} players with None values")
