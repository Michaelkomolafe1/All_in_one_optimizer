#!/usr/bin/env python3
"""
DIAGNOSE SCORING ISSUE
======================
Find out why scoring isn't working
"""

import sys
sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

from core.unified_core_system import UnifiedCoreSystem

# Initialize and load
system = UnifiedCoreSystem()
system.load_players_from_csv("/home/michael/Downloads/DKSalaries(28).csv")
system.build_player_pool(include_unconfirmed=True)
system.enrich_player_pool()

print("=" * 60)
print("SCORING DIAGNOSTIC")
print("=" * 60)

# Check a player after enrichment
test_player = system.player_pool[0]
print(f"\nTest player: {test_player.name}")
print(f"Has fantasy_points: {hasattr(test_player, 'fantasy_points')}")
print(f"fantasy_points value: {getattr(test_player, 'fantasy_points', 'MISSING')}")
print(f"Has is_pitcher: {hasattr(test_player, 'is_pitcher')}")
print(f"is_pitcher value: {getattr(test_player, 'is_pitcher', 'MISSING')}")

# Try scoring manually
print("\nManual scoring test:")
if hasattr(test_player, 'fantasy_points'):
    base_proj = test_player.fantasy_points
    score = base_proj * 1.05  # Simple pitcher bonus
    print(f"Base projection: {base_proj}")
    print(f"Manual score: {score}")
else:
    print("ERROR: No fantasy_points attribute!")

# Check if enrichments_applied flag is set
print(f"\nEnrichments applied flag: {getattr(system, 'enrichments_applied', 'MISSING')}")

# Now try the scoring method
print("\nCalling score_players...")
system.score_players('cash')

# Check results
print("\nChecking results:")
scored_count = 0
for i, player in enumerate(system.player_pool[:5]):
    enhanced = getattr(player, 'enhanced_score', 'MISSING')
    cash = getattr(player, 'cash_score', 'MISSING')
    gpp = getattr(player, 'gpp_score', 'MISSING')
    print(f"{player.name}: enhanced={enhanced}, cash={cash}, gpp={gpp}")
    if enhanced != 'MISSING' and enhanced > 0:
        scored_count += 1

total_scored = sum(1 for p in system.player_pool if hasattr(p, 'enhanced_score') and p.enhanced_score > 0)
print(f"\nTotal players scored: {total_scored}/191")

# Check the score_players method source
print("\n" + "=" * 60)
print("CHECKING METHOD SOURCE")
print("=" * 60)
import inspect
try:
    source = inspect.getsource(system.score_players)
    print("First 200 chars of score_players method:")
    print(source[:200] + "...")
except:
    print("Could not get source - method might not exist")