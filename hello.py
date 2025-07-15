#!/usr/bin/env python3
"""
Verify MLB Showdown is using enriched data
==========================================
"""

from bulletproof_dfs_core import BulletproofDFSCore
import os


def verify_showdown_enrichment():
    print("🔍 VERIFYING MLB SHOWDOWN DATA ENRICHMENT")
    print("=" * 60)

    # Initialize
    core = BulletproofDFSCore()

    # Load CSV
    csv_path = os.path.expanduser("~/Downloads/DKSalaries(5).csv")
    core.load_draftkings_csv(csv_path)

    # Set to all mode
    core.optimization_mode = "all"

    # Get lineup
    lineup, score = core.optimize_showdown_lineup()

    if lineup:
        print(f"\n✅ Generated lineup with score: {score:.1f}")

        # Check captain data enrichment
        captain = [p for p in lineup if getattr(p, 'is_captain', False)][0]

        print(f"\n🔍 CAPTAIN DATA CHECK: {captain.name}")
        print(f"   Base Projection: {getattr(captain, 'base_projection', 'N/A')}")
        print(f"   Enhanced Score: {captain.enhanced_score:.1f}")

        # Check for enrichments
        enrichments = []
        if hasattr(captain, 'vegas_data') and captain.vegas_data:
            enrichments.append('Vegas')
            print(f"   ✅ Vegas Data: {captain.vegas_data}")

        if hasattr(captain, 'statcast_data') and captain.statcast_data:
            enrichments.append('Statcast')
            print(f"   ✅ Statcast Data: Available")

        if hasattr(captain, '_recent_performance') and captain._recent_performance:
            enrichments.append('Recent Form')
            print(f"   ✅ Recent Form: Available")

        if hasattr(captain, 'park_factors') and captain.park_factors:
            enrichments.append('Park Factors')
            print(f"   ✅ Park Factors: Available")

        # Show utility players
        print(f"\n⚡ UTILITY PLAYERS:")
        utils = [p for p in lineup if not getattr(p, 'is_captain', False)]
        for i, player in enumerate(utils, 1):
            print(f"   {i}. {player.name} ({player.team}) - ${player.salary:,} → {player.enhanced_score:.1f} pts")

        # Summary
        print(f"\n📊 DATA ENRICHMENT SUMMARY:")
        if enrichments:
            print(f"   ✅ Using enriched data from: {', '.join(enrichments)}")
        else:
            print(f"   ⚠️  No data enrichments detected - using base projections only")
            print(f"   💡 To enable enrichments:")
            print(f"      1. Run: core.detect_confirmed_players()")
            print(f"      2. Run: core.enrich_confirmed_players()")

        # Calculate total salary
        total_salary = sum(p.salary * getattr(p, 'multiplier', 1.0) for p in lineup)
        print(f"\n💰 Total Salary Used: ${total_salary:,} / $50,000")
        print(f"   Remaining: ${50000 - total_salary:,}")

        # Team distribution
        teams = {}
        for p in lineup:
            teams[p.team] = teams.get(p.team, 0) + 1
        print(f"\n🏈 Team Distribution: {dict(teams)}")

    else:
        print("❌ Failed to generate lineup")


if __name__ == "__main__":
    verify_showdown_enrichment()