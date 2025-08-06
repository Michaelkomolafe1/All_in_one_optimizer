#!/usr/bin/env python3
"""Test UnifiedPlayer creation directly"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_optimizer.unified_player_model import UnifiedPlayer

print("Testing UnifiedPlayer creation...")

# Test 1: Create with correct arguments
try:
    player = UnifiedPlayer(
        id="1",
        name="Test Player",
        team="NYY",
        salary=10000,
        primary_position="OF",
        positions=["OF"]
    )
    print("✅ UnifiedPlayer created successfully!")
    print(f"   Name: {player.name}")
    print(f"   Team: {player.team}")
    print(f"   Salary: {player.salary}")

    # Set additional attributes
    player.base_projection = 15.0
    player.batting_order = 3
    player.recent_performance = 1.2
    print(f"   Projection: {player.base_projection}")

except Exception as e:
    print(f"❌ Failed: {e}")

    # Try alternate method if first fails
    print("\nTrying with dictionary...")
    try:
        data = {
            'Name': 'Test Player',
            'Team': 'NYY', 
            'Salary': 10000,
            'Position': 'OF'
        }
        player = UnifiedPlayer(data)
        print("✅ Dictionary method works!")
    except Exception as e2:
        print(f"❌ Dictionary method also failed: {e2}")

print("\n📋 The correct format for UnifiedPlayer is:")
print("UnifiedPlayer(id, name, team, salary, primary_position, positions)")
