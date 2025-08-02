#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

# Force reload of the module
import importlib
import dfs_optimizer.core.unified_core_system
importlib.reload(dfs_optimizer.core.unified_core_system)

from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem

# Test the changes
system = UnifiedCoreSystem()
system.load_players_from_csv("/home/michael/Downloads/DKSalaries(29).csv")

print("Testing if changes were applied:")
print("\n1️⃣ Checking projections:")
for p in system.players[:5]:
    print(f"  {p.name}: base_projection={p.base_projection}")

print("\n2️⃣ Checking enrichment attributes:")
p = system.players[0]
print(f"  vegas_score: {getattr(p, 'vegas_score', 'NOT SET')}")
print(f"  matchup_score: {getattr(p, 'matchup_score', 'NOT SET')}")
print(f"  recent_form_score: {getattr(p, 'recent_form_score', 'NOT SET')}")

if p.base_projection > 0 and hasattr(p, 'vegas_score'):
    print("\n✅ Changes successfully applied!")
else:
    print("\n❌ Changes not applied yet")