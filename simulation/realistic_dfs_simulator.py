import sys
import os

sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')
sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer/main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem


# Simple test player
class TestPlayer:
    def __init__(self):
        self.name = "Test Player"
        self.position = "1B"
        self.team = "NYY"
        self.salary = 5000
        self.projection = 10.0
        self.ownership = 20.0
        self.batting_order = 3


system = UnifiedCoreSystem()

# Create a few test players
test_players = [TestPlayer() for _ in range(10)]

# Try different loading methods
print("Testing player loading methods:")

# Method 1
system.players = test_players
print(f"1. Set players directly: {len(system.players) if hasattr(system, 'players') and system.players else 0} players")

# Method 2
if hasattr(system, 'build_player_pool'):
    result = system.build_player_pool(test_players)
    print(f"2. build_player_pool(): Success")

# Method 3 - Check if optimize needs different setup
if hasattr(system, 'player_pool'):
    print(f"3. player_pool exists: {len(system.player_pool) if system.player_pool else 0} players")

# Try to optimize
try:
    lineup = system.optimize_lineup('gpp')
    if lineup:
        print(f"✅ Optimization worked! Got {len(lineup)} players")
    else:
        print("❌ Optimization returned None")
except Exception as e:
    print(f"❌ Optimization error: {e}")