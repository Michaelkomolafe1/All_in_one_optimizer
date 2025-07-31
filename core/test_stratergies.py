#!/usr/bin/env python3
"""Test strategy integration"""

import sys
sys.path.insert(0, '.')

from strategies.cash_strategies import build_projection_monster
from strategies.gpp_strategies import build_truly_smart_stack
from unified_core_system import UnifiedCoreSystem

print("✅ Strategies imported successfully!")

# Test with a simple player pool
system = UnifiedCoreSystem()
print("✅ System initialized!")

# You can test further if you have a CSV:
# system.load_players_from_csv('sample.csv')
# system.build_player_pool()
# updated_players = build_truly_smart_stack(system.player_pool)