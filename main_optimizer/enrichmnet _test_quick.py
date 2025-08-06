#!/usr/bin/env python3
"""Test that enrichments are now working"""

import sys
import os

sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem

print("=" * 60)
print("TESTING ENRICHMENT FIX")
print("=" * 60)

system = UnifiedCoreSystem()

# Check sources
print("\n1. Data Sources:")
print(f"   Vegas: {'✅' if system.vegas_lines else '❌'}")
print(f"   Statcast: {'✅' if system.stats_fetcher else '❌'}")
print(f"   Confirmations: {'✅' if system.confirmation_system else '❌'}")

# Load data
csv_path = "/home/michael/Downloads/DKSalaries(46).csv"
system.load_csv(csv_path)
system.build_player_pool(include_unconfirmed=True)

# Test enrichment directly
print("\n2. Testing Direct Enrichment:")
slate_size = 'medium'
strategy = 'projection_monster'
contest_type = 'cash'

# Call enrichment explicitly
enriched_players = system.enrichment_manager.smart_enrich(
    players=system.player_pool[:5],  # Test with 5 players
    slate_size=slate_size,
    strategy=strategy,
    contest_type=contest_type
)

# Check if enriched
for p in enriched_players[:3]:
    print(f"\n   {p.name}:")
    print(f"     Recent form: {getattr(p, 'recent_form', 'NOT SET')}")
    print(f"     Consistency: {getattr(p, 'consistency_score', 'NOT SET')}")
    print(f"     Vegas total: {getattr(p, 'implied_team_score', 'NOT SET')}")

# Test full optimization
print("\n3. Testing Full Optimization:")
lineups = system.optimize_lineup(
    strategy='projection_monster',
    contest_type='cash',
    num_lineups=1
)

if lineups:
    print("   ✅ Lineup generated")

    # Check enrichments in lineup
    lineup = lineups[0]
    if isinstance(lineup, dict):
        players = lineup.get('players', [])
        enriched_count = sum(1 for p in players
                             if isinstance(p, dict) and
                             (p.get('recent_form', 0) != 0 or
                              p.get('implied_team_score', 0) != 0))
        print(f"   Players with enrichments: {enriched_count}/10")
else:
    print("   ❌ Failed to generate lineup")

print("\n" + "=" * 60)