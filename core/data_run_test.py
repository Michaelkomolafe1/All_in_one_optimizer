#!/usr/bin/env python3
"""
DIAGNOSE ENHANCED SCORING ISSUE
==============================
Why are enhanced scores still uniform after fixing projections?
"""

import sys
import pandas as pd

sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem
from dfs_optimizer.core.enhanced_scoring_engine import EnhancedScoringEngine

print("=" * 80)
print("🔍 DIAGNOSING ENHANCED SCORING ISSUE")
print("=" * 80)

# Load and fix projections
CSV_PATH = "/home/michael/Downloads/DKSalaries(29).csv"
system = UnifiedCoreSystem()
system.load_players_from_csv(CSV_PATH)

# Fix projections
df = pd.read_csv(CSV_PATH)
for player in system.players:
    matching_row = df[df['Name'] == player.name]
    if not matching_row.empty:
        player.base_projection = float(matching_row.iloc[0]['AvgPointsPerGame'])
    player.is_pitcher = player.primary_position in ['P', 'SP', 'RP']

system.build_player_pool(include_unconfirmed=True)

# Check what happens in enrichment
print("\n1️⃣ CHECKING ENRICHMENT VALUES:")
print("-" * 60)
system.enrich_player_pool()

# Sample a few players
test_players = []
for p in system.player_pool[:5]:
    test_players.append(p)
    print(f"\n{p.name} ({p.primary_position}):")
    print(f"  base_projection: {p.base_projection}")
    print(f"  recent_form_score: {getattr(p, 'recent_form_score', 'NOT SET')}")
    print(f"  matchup_score: {getattr(p, 'matchup_score', 'NOT SET')}")
    print(f"  vegas_score: {getattr(p, 'vegas_score', 'NOT SET')}")
    print(f"  park_score: {getattr(p, 'park_score', 'NOT SET')}")
    print(f"  weather_score: {getattr(p, 'weather_score', 'NOT SET')}")

# Check the scoring calculation directly
print("\n2️⃣ CHECKING SCORING ENGINE DIRECTLY:")
print("-" * 60)

engine = system.scoring_engine

# Test cash scoring on specific players
for p in test_players[:3]:
    print(f"\n{p.name}:")

    # Check the components of cash scoring
    projection_score = p.base_projection
    recent_score = getattr(p, 'recent_form_score', projection_score)

    print(f"  Components:")
    print(f"    base_projection: {projection_score}")
    print(f"    recent_form_score: {recent_score}")

    # Calculate manually what cash score should be
    cash_params = engine.cash_params
    weight_proj = cash_params.get('weight_projection', 0.4)
    weight_recent = cash_params.get('weight_recent', 0.4)
    weight_season = cash_params.get('weight_season', 0.2)

    manual_calc = (projection_score * weight_proj +
                   recent_score * weight_recent +
                   projection_score * 0.9 * weight_season)

    print(f"  Manual calculation: {manual_calc:.2f}")

    # Get actual cash score
    actual_cash = engine.score_player_cash(p)
    print(f"  Actual cash score: {actual_cash:.2f}")

# Check what score_players does
print("\n3️⃣ CHECKING score_players METHOD:")
print("-" * 60)

# Look at the actual enhanced_score calculation
system.score_players('cash')

print("After score_players('cash'):")
for p in test_players[:3]:
    print(f"{p.name}: enhanced_score = {getattr(p, 'enhanced_score', 'NOT SET')}")

# Check if enhanced_score is being overwritten
print("\n4️⃣ CHECKING IF SCORES ARE BEING OVERWRITTEN:")
print("-" * 60)

# The issue might be in score_players method
# It might be setting enhanced_score to some fixed value

# Let's check the actual values being set
scores_by_position = {}
for p in system.player_pool[:50]:
    pos = p.primary_position
    score = getattr(p, 'enhanced_score', 0)
    if pos not in scores_by_position:
        scores_by_position[pos] = []
    scores_by_position[pos].append(score)

print("Scores by position:")
for pos, scores in scores_by_position.items():
    unique = len(set(scores))
    if scores:
        print(f"  {pos}: {unique} unique values, all are {scores[0]:.1f}")

print("\n" + "=" * 80)
print("💡 LIKELY ISSUE")
print("=" * 80)
print("""
The enhanced_score is being set to a fixed value somewhere.
Possibilities:
1. The score_players method has a bug
2. All enrichment values are the same (0.0 or 1.0)
3. The scoring formula collapses to position-based constants

Check dfs_optimizer/core/unified_core_system.py
Look for where enhanced_score is set in score_players()
""")