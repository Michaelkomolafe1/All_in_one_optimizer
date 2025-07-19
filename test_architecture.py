#!/usr/bin/env python3
"""Test the fixed architecture"""

import pandas as pd

# Test creating UnifiedPlayer correctly
print("🧪 TESTING UNIFIED PLAYER CREATION")
print("=" * 60)

try:
    from unified_player_model import UnifiedPlayer

    # Create test player with CORRECT parameters
    player = UnifiedPlayer(
        id="test123",
        name="Mike Trout",
        team="LAA",
        salary=10000,
        primary_position="OF",  # NOT 'position'
        positions=["OF"],       # List, not string
        base_projection=12.5
    )

    print("✅ UnifiedPlayer created successfully!")
    print(f"   Name: {player.name}")
    print(f"   Primary Position: {player.primary_position}")
    print(f"   Positions: {player.positions}")
    print(f"   Salary: ${player.salary}")

except Exception as e:
    print(f"❌ Error: {e}")

# Test BulletproofDFSCore methods
print("\n🧪 TESTING BULLETPROOF DFS CORE")
print("=" * 60)

try:
    from bulletproof_dfs_core import BulletproofDFSCore

    core = BulletproofDFSCore(mode="test")

    print("Available methods:")
    methods = ['load_players', 'optimize', 'enrich_player_data', 'run_confirmation_analysis']
    for method in methods:
        if hasattr(core, method):
            print(f"  ✅ {method}")
        else:
            print(f"  ❌ {method} (not found)")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Test complete!")
print("\nNow run: python complete_dfs_gui_debug.py")
