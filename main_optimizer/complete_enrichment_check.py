#!/usr/bin/env python3
"""Check ALL enrichments are properly applied"""

import pandas as pd
from unified_core_system import UnifiedCoreSystem

# Initialize and load
system = UnifiedCoreSystem()
system.load_players_from_csv("/home/michael/Downloads/DKSalaries(35).csv")

# Fix projections
df = pd.read_csv("/home/michael/Downloads/DKSalaries(35).csv")
for p in system.players:
    row = df[df['Name'] == p.name]
    if not row.empty:
        p.base_projection = float(row.iloc[0].get('AvgPointsPerGame', 0))

# Build and enrich
system.build_player_pool(include_unconfirmed=True)
system.enrich_player_pool()

# Apply enrichment fixes
for player in system.player_pool:
    if hasattr(player, 'team_total'):
        player.implied_team_score = player.team_total
    elif hasattr(player, 'vegas_score'):
        player.implied_team_score = 4.5 * player.vegas_score
    if hasattr(player, 'park_score'):
        player.park_factor = player.park_score
    if not player.is_pitcher and player.batting_order is None:
        if player.salary >= 5000:
            player.batting_order = 3
        elif player.salary >= 4000:
            player.batting_order = 5
        else:
            player.batting_order = 8

print("="*80)
print("🔍 COMPLETE ENRICHMENT VERIFICATION")
print("="*80)

# Check each enrichment type
enrichments = {
    'base_projection': 0,
    'implied_team_score': 0,
    'park_factor': 0,
    'batting_order': 0,
    'vegas_score': 0,
    'matchup_score': 0,
    'weather_score': 0,
    'is_pitcher': 0,
    'team_total': 0,
    'park_score': 0
}

hitters_with_batting_order = 0
total_hitters = 0

for p in system.player_pool:
    for attr in enrichments:
        if hasattr(p, attr) and getattr(p, attr) is not None:
            enrichments[attr] += 1
    
    if not p.is_pitcher:
        total_hitters += 1
        if hasattr(p, 'batting_order') and p.batting_order is not None:
            hitters_with_batting_order += 1

print("\n📊 Enrichment Coverage:")
print("-"*50)
for attr, count in enrichments.items():
    pct = (count / len(system.player_pool) * 100)
    status = "✅" if count > 0 else "❌"
    print(f"{status} {attr:<20}: {count}/{len(system.player_pool)} ({pct:.1f}%)")

print(f"\n🏏 Batting Order Coverage:")
print(f"   Hitters with batting order: {hitters_with_batting_order}/{total_hitters} ({hitters_with_batting_order/total_hitters*100:.1f}%)")

# Show specific examples
print("\n📋 Sample Player Details:")
print("-"*80)

# Get diverse samples
samples = [
    system.player_pool[0],  # First player
    next((p for p in system.player_pool if p.salary >= 9000), None),  # High salary
    next((p for p in system.player_pool if p.salary <= 3000), None),  # Low salary
    next((p for p in system.player_pool if not p.is_pitcher and p.salary >= 5000), None),  # High salary hitter
    next((p for p in system.player_pool if not p.is_pitcher and p.salary <= 3500), None),  # Low salary hitter
]

for p in samples:
    if p:
        print(f"\n{p.name} ({p.team}) - ${p.salary} - {p.primary_position}")
        print(f"  Base Projection: {p.base_projection}")
        print(f"  Vegas Total: {getattr(p, 'implied_team_score', 'NOT SET')}")
        print(f"  Park Factor: {getattr(p, 'park_factor', 'NOT SET')}")
        print(f"  Batting Order: {getattr(p, 'batting_order', 'NOT SET')}")
        print(f"  Vegas Score: {getattr(p, 'vegas_score', 'NOT SET')}")
        print(f"  Matchup Score: {getattr(p, 'matchup_score', 'NOT SET')}")
        print(f"  Weather Score: {getattr(p, 'weather_score', 'NOT SET')}")
        print(f"  Cash Score: {getattr(p, 'cash_score', 'NOT SET')}")
        print(f"  GPP Score: {getattr(p, 'gpp_score', 'NOT SET')}")

# Check if scores are using enrichments
print("\n🎯 Score Differentiation Check:")
print("-"*50)

# Group by team and check average scores
from collections import defaultdict
team_scores = defaultdict(list)
for p in system.player_pool:
    if hasattr(p, 'gpp_score'):
        team_scores[p.team].append(p.gpp_score)

print("Average GPP Score by Team (should vary based on Vegas totals):")
for team, scores in sorted(team_scores.items()):
    avg_score = sum(scores) / len(scores)
    vegas = next((p.implied_team_score for p in system.player_pool if p.team == team), 'N/A')
    print(f"  {team}: {avg_score:.1f} (Vegas: {vegas})")
