#!/usr/bin/env python3
"""Verify scoring is working correctly"""

import pandas as pd
from unified_core_system import UnifiedCoreSystem
from enhanced_scoring_engine import EnhancedScoringEngine

# Initialize
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

# Score players
system.score_players('cash')

# Check variety in scores
print("🔍 SCORING VERIFICATION")
print("="*50)

# Get unique enhanced scores
enhanced_scores = set(p.enhanced_score for p in system.player_pool)
print(f"\nUnique enhanced scores: {len(enhanced_scores)}")
if len(enhanced_scores) < 10:
    print("❌ Too few unique scores - something is wrong!")
    print(f"   Scores: {enhanced_scores}")

# Show sample players with different attributes
print("\n📊 Sample Players:")
print("-"*80)
print(f"{'Name':<20} {'Team':<5} {'Salary':<8} {'Base':<6} {'Vegas':<6} {'Park':<6} {'Cash':<6} {'GPP':<6} {'Enhanced':<8}")
print("-"*80)

samples = [
    ('Jacob deGrom', 'TEX'),
    ('Dylan Cease', 'SD'),
    ('Manny Machado', 'SD'),
    ('Cal Raleigh', 'SEA'),
    ('Connor Kaiser', 'ARI')
]

for name, team in samples:
    player = next((p for p in system.player_pool if p.name == name), None)
    if player:
        vegas = getattr(player, 'implied_team_score', 'N/A')
        park = getattr(player, 'park_factor', 'N/A')
        print(f"{player.name:<20} {player.team:<5} ${player.salary:<7} "
              f"{player.base_projection:<6.1f} {vegas:<6} {park:<6} "
              f"{player.cash_score:<6.1f} {player.gpp_score:<6.1f} {player.enhanced_score:<8.1f}")

# Check if enrichments are actually being used in scoring
print("\n🔍 Enrichment Usage Check:")
engine = EnhancedScoringEngine()

# Test player with high vegas total
high_vegas = next((p for p in system.player_pool if getattr(p, 'implied_team_score', 0) > 9), None)
if high_vegas:
    print(f"\nHigh Vegas Player: {high_vegas.name} ({high_vegas.team})")
    print(f"  Vegas Total: {high_vegas.implied_team_score}")
    print(f"  Base Proj: {high_vegas.base_projection}")
    print(f"  GPP Score: {high_vegas.gpp_score}")
    
# Test player with low vegas total  
low_vegas = next((p for p in system.player_pool if getattr(p, 'implied_team_score', 0) < 7), None)
if low_vegas:
    print(f"\nLow Vegas Player: {low_vegas.name} ({low_vegas.team})")
    print(f"  Vegas Total: {low_vegas.implied_team_score}")
    print(f"  Base Proj: {low_vegas.base_projection}")
    print(f"  GPP Score: {low_vegas.gpp_score}")

# Verify thresholds
print(f"\n📊 GPP Thresholds:")
print(f"  High: {engine.gpp_params.get('threshold_high', 'Not set')}")
print(f"  Med: {engine.gpp_params.get('threshold_med', 'Not set')}")
print(f"  Low: {engine.gpp_params.get('threshold_low', 'Not set')}")
