#!/usr/bin/env python3
"""Test CSV Loading"""

import sys
sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem
from unified_player_model import UnifiedPlayer

# Create a test player
test_row = {
    'Name': 'Test Player',
    'Position': 'OF',
    'Salary': '5000',
    'TeamAbbrev': 'NYY',
    'AvgPointsPerGame': '10.5',
    'ID': '12345'
}

print("Testing player creation...")
try:
    player = UnifiedPlayer.from_csv_row(test_row)
    print(f"✓ Created player: {player.name}")
    print(f"  Base projection: {player.base_projection}")
    print(f"  Optimization score: {player.optimization_score}")
    print(f"  Enhanced score: {player.enhanced_score}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\nTesting system...")
system = UnifiedCoreSystem()
print(f"✓ System created")

# Test loading
print("\nTest complete!")
