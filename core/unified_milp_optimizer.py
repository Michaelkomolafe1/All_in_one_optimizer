#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

# Force reload of the module
import importlib
import dfs_optimizer.core.unified_core_system
importlib.reload(dfs_optimizer.core.unified_core_system)

from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem

# Now test
system = UnifiedCoreSystem()
system.load_players_from_csv("/home/michael/Downloads/DKSalaries(29).csv")

print("After reload and load:")
for p in system.players[:5]:
    print(f"  {p.name}: base_projection={p.base_projection}")