#!/usr/bin/env python3
"""Test if game info is working"""

from unified_core_system import UnifiedCoreSystem

system = UnifiedCoreSystem()
system.load_csv("/home/michael/Downloads/DKSalaries(13).csv")

# Check first 5 players
print("\nChecking if players have game_info:")
for i, (name, player) in enumerate(system.all_players.items()):
    if i < 5:
        game_info = getattr(player, 'game_info', 'MISSING')
        print(f"{name}: game_info = '{game_info}'")

# Count how many have game_info
count = sum(1 for p in system.all_players.values() if hasattr(p, 'game_info') and p.game_info)
print(f"\nTotal with game_info: {count}/{len(system.all_players)}")
