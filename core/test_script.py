#!/usr/bin/env python3
"""
VERIFY PROJECTIONS LOADING
==========================
Quick script to check if projections are loading correctly
"""

import sys
sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

from core.unified_core_system import UnifiedCoreSystem

# Test the system
print("Testing projection loading...")
print("=" * 60)

system = UnifiedCoreSystem()

# Load CSV
csv_path = "/home/michael/Downloads/DKSalaries(28).csv"
system.load_players_from_csv(csv_path)

print(f"\nLoaded {len(system.players)} players")

# Check first 10 players
print("\nFirst 10 players with projections:")
print(f"{'Name':<20} {'Team':<5} {'Salary':<8} {'DK Proj':<10} {'Has Proj'}")
print("-" * 60)

for i, player in enumerate(system.players[:10]):
    dk_proj = getattr(player, 'dff_projection', 0)
    has_proj = "✓" if dk_proj > 0 else "✗"
    print(f"{player.name:<20} {player.team:<5} ${player.salary:<7,} {dk_proj:<10.1f} {has_proj}")

# Count players with projections
players_with_proj = sum(1 for p in system.players if getattr(p, 'dff_projection', 0) > 0)
print(f"\nPlayers with projections: {players_with_proj}/{len(system.players)}")

# Test scoring
print("\nTesting scoring system...")
system.build_player_pool(include_unconfirmed=True)
system.score_players('cash')

# Check if scoring worked
scored_players = sum(1 for p in system.player_pool if hasattr(p, 'enhanced_score') and p.enhanced_score > 0)
print(f"Players with enhanced scores: {scored_players}/{len(system.player_pool)}")

if scored_players > 0:
    # Show top 5 by score
    system.player_pool.sort(key=lambda x: getattr(x, 'enhanced_score', 0), reverse=True)
    print("\nTop 5 players by enhanced score (Cash):")
    for p in system.player_pool[:5]:
        print(f"  {p.name}: {p.enhanced_score:.2f} (base: {p.dff_projection:.1f})")
else:
    print("\n⚠️  No players have enhanced scores - scoring may not be working!")

print("\n" + "=" * 60)
print("SUMMARY:")
if players_with_proj > 0 and scored_players > 0:
    print("✅ Projections loading correctly!")
    print("✅ Scoring system working!")
else:
    if players_with_proj == 0:
        print("❌ Projections not loading from CSV")
    if scored_players == 0:
        print("❌ Scoring system not producing scores")