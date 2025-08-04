#!/usr/bin/env python3
"""Debug why scoring engine gives same scores"""

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

# Apply fixes
for player in system.player_pool:
    if hasattr(player, 'team_total'):
        player.implied_team_score = player.team_total

# Get scoring engine
engine = system.scoring_engine

print("🔍 SCORING ENGINE DEBUG")
print("="*50)

# Check GPP parameters
print("\nGPP Parameters:")
for k, v in engine.gpp_params.items():
    print(f"  {k}: {v}")

# Test scoring on specific players
test_players = [
    ("High Vegas", next(p for p in system.player_pool if p.implied_team_score > 6.5)),
    ("Low Vegas", next(p for p in system.player_pool if p.implied_team_score < 4.5))
]

print("\n📊 Test Scoring:")
for label, player in test_players:
    print(f"\n{label}: {player.name} ({player.team})")
    print(f"  Base Projection: {player.base_projection}")
    print(f"  Vegas Total: {player.implied_team_score}")
    
    # Manually calculate GPP score
    score = player.base_projection
    
    # Check team total multiplier
    if player.implied_team_score >= engine.gpp_params['threshold_high']:
        mult = engine.gpp_params['mult_high']
        print(f"  Vegas Multiplier: {mult} (HIGH)")
    elif player.implied_team_score >= engine.gpp_params['threshold_med']:
        mult = engine.gpp_params['mult_med']
        print(f"  Vegas Multiplier: {mult} (MED)")
    elif player.implied_team_score >= engine.gpp_params['threshold_low']:
        mult = engine.gpp_params['mult_low']
        print(f"  Vegas Multiplier: {mult} (LOW)")
    else:
        mult = engine.gpp_params['mult_none']
        print(f"  Vegas Multiplier: {mult} (NONE)")
    
    score *= mult
    print(f"  After Vegas: {score:.2f}")
    
    # Call actual scoring method
    actual_gpp = engine.score_player_gpp(player)
    print(f"  Actual GPP Score: {actual_gpp:.2f}")
    
    # Check cash scoring
    actual_cash = engine.score_player_cash(player)
    print(f"  Actual Cash Score: {actual_cash:.2f}")
