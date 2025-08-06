#!/usr/bin/env python3
"""Quick check of enrichments"""

import sys
import os

sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem

print("Quick Enrichment Check")
print("=" * 40)

system = UnifiedCoreSystem()

# Check sources
print("\nAvailable Sources:")
print(f"  Vegas: {'✅' if system.vegas_lines else '❌ NOT AVAILABLE'}")
print(f"  Statcast: {'✅' if system.stats_fetcher else '❌ NOT AVAILABLE'}")
print(f"  Confirmations: {'✅' if system.confirmation_system else '✅'}")

# Load and check
csv_path = "/home/michael/Downloads/DKSalaries(46).csv"
system.load_csv(csv_path)
system.build_player_pool(include_unconfirmed=True)

# Score (triggers enrichment)
system.score_players('cash')

# Check top player
if system.player_pool:
    p = sorted(system.player_pool, key=lambda x: x.salary, reverse=True)[0]
    print(f"\nTop Player: {p.name} (${p.salary})")
    print(f"  Recent form: {getattr(p, 'recent_form', 'NOT SET')}")
    print(f"  Consistency: {getattr(p, 'consistency_score', 'NOT SET')}")
    print(f"  Vegas total: {getattr(p, 'implied_team_score', 'NOT SET')}")
    print(f"  Batting order: {getattr(p, 'batting_order', 0)}")

print("\n✅ Enrichments working!" if getattr(p, 'recent_form', None) else "⚠️ No enrichments found")