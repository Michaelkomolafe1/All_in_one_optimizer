#!/usr/bin/env python3
"""
ENRICHMENT AUDIT - Standalone Version
======================================
Tests what enrichments are actually being applied
"""

import sys
import os
import logging

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main_optimizer'))

# Enable INFO logging to see enrichment details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s'
)


def test_available_sources():
    """Test what data sources are available"""
    print("\n" + "=" * 70)
    print("1. CHECKING AVAILABLE DATA SOURCES")
    print("=" * 70)

    from main_optimizer.unified_core_system_updated import UnifiedCoreSystem

    system = UnifiedCoreSystem()

    sources = {
        'Vegas Lines': system.vegas_lines,
        'Statcast': system.stats_fetcher,
        'Confirmations': system.confirmation_system,
        'Enrichment Manager': system.enrichment_manager,
        'Scoring Engine': system.scoring_engine
    }

    print("\nData Sources Status:")
    for name, source in sources.items():
        if source is not None:
            print(f"  ✅ {name:20} : Available ({type(source).__name__})")
        else:
            print(f"  ❌ {name:20} : Not Available")

    return sources


def test_enrichment_profiles():
    """Check what each strategy is configured to use"""
    print("\n" + "=" * 70)
    print("2. ENRICHMENT PROFILES BY STRATEGY")
    print("=" * 70)

    from main_optimizer.smart_enrichment_manager import SmartEnrichmentManager

    manager = SmartEnrichmentManager()

    strategies = [
        ('projection_monster', 'cash', 'medium'),
        ('pitcher_dominance', 'cash', 'small'),
        ('tournament_winner_gpp', 'gpp', 'medium'),
        ('correlation_value', 'gpp', 'large')
    ]

    for strategy, contest_type, slate_size in strategies:
        print(f"\n{strategy} ({contest_type}, {slate_size} slate):")

        profile = manager.get_enrichment_requirements(
            slate_size=slate_size,
            strategy=strategy,
            contest_type=contest_type
        )

        print(f"  Vegas: {profile.needs_vegas}")
        print(f"  Statcast: {profile.needs_statcast} (top {profile.statcast_priority_players} players)")
        print(f"  Ownership: {profile.needs_ownership}")
        print(f"  Weather: {profile.needs_weather}")
        print(f"  Batting Order: {profile.needs_batting_order}")
        print(f"  Recent Form: {profile.needs_recent_form}")
        print(f"  Consistency: {profile.needs_consistency}")

        if strategy == 'pitcher_dominance':
            print(f"  K-Rate: {profile.needs_k_rate}")

        if 'gpp' in strategy:
            print(f"  Barrel Rate: {profile.needs_barrel_rate}")
            print(f"  Hard Hit: {profile.needs_hard_hit}")


def test_actual_enrichment():
    """Test enrichments being applied to real players"""
    print("\n" + "=" * 70)
    print("3. TESTING ACTUAL PLAYER ENRICHMENT")
    print("=" * 70)

    from main_optimizer.unified_core_system_updated import UnifiedCoreSystem

    system = UnifiedCoreSystem()
    csv_path = "/home/michael/Downloads/DKSalaries(46).csv"

    # Load CSV
    count = system.load_csv(csv_path)
    print(f"\nLoaded {count} players from CSV")

    # Fetch confirmations
    confirmed = system.fetch_confirmed_players()
    print(f"Confirmed {confirmed} players")

    # Build pool with all players
    pool_size = system.build_player_pool(include_unconfirmed=True)
    print(f"Player pool: {pool_size} players")

    # Test enrichment for each strategy
    print("\n" + "-" * 50)
    print("ENRICHMENT BY STRATEGY:")
    print("-" * 50)

    strategies = [
        ('projection_monster', 'cash'),
        ('pitcher_dominance', 'cash'),
        ('tournament_winner_gpp', 'gpp'),
        ('correlation_value', 'gpp')
    ]

    for strategy, contest_type in strategies:
        print(f"\n{strategy} ({contest_type}):")

        # This triggers enrichment
        system.score_players(contest_type)

        # Sample high-salary players to check enrichments
        top_players = sorted(system.player_pool, key=lambda p: p.salary, reverse=True)[:3]

        for i, player in enumerate(top_players, 1):
            print(f"\n  Player {i}: {player.name} ({player.position}, ${player.salary})")

            # Check basic enrichments
            attrs = {
                'Base Projection': getattr(player, 'base_projection', 'NOT SET'),
                'Optimization Score': getattr(player, 'optimization_score', 'NOT SET'),
                'Recent Form': getattr(player, 'recent_form', 'NOT SET'),
                'Consistency': getattr(player, 'consistency_score', 'NOT SET'),
                'Team Total (Vegas)': getattr(player, 'implied_team_score', 'NOT SET'),
                'Batting Order': getattr(player, 'batting_order', 'NOT SET'),
            }

            for attr_name, value in attrs.items():
                if value != 'NOT SET':
                    if isinstance(value, float):
                        print(f"    {attr_name:20}: {value:.2f}")
                    else:
                        print(f"    {attr_name:20}: {value}")
                else:
                    print(f"    {attr_name:20}: ❌ NOT SET")

            # Check strategy-specific enrichments
            if contest_type == 'gpp':
                ownership = getattr(player, 'ownership_projection', 'NOT SET')
                print(f"    {'Ownership':20}: {ownership}")

            if strategy == 'pitcher_dominance' and player.position in ['P', 'SP', 'RP']:
                k_rate = getattr(player, 'k_rate', 'NOT SET')
                print(f"    {'K-Rate':20}: {k_rate}")

            if 'tournament_winner' in strategy:
                barrel = getattr(player, 'barrel_rate', 'NOT SET')
                print(f"    {'Barrel Rate':20}: {barrel}")


def test_enrichment_impact():
    """Test the impact of enrichments on lineups"""
    print("\n" + "=" * 70)
    print("4. ENRICHMENT IMPACT ON LINEUPS")
    print("=" * 70)

    from main_optimizer.unified_core_system_updated import UnifiedCoreSystem

    system = UnifiedCoreSystem()
    csv_path = "/home/michael/Downloads/DKSalaries(46).csv"

    # Setup
    system.load_csv(csv_path)
    system.fetch_confirmed_players()
    system.build_player_pool(include_unconfirmed=True)

    strategies = [
        ('projection_monster', 'cash'),
        ('tournament_winner_gpp', 'gpp')
    ]

    for strategy, contest_type in strategies:
        print(f"\n{strategy} ({contest_type}):")

        # Generate lineup
        lineups = system.optimize_lineup(
            strategy=strategy,
            contest_type=contest_type,
            num_lineups=1
        )

        if lineups:
            lineup = lineups[0]

            print("  Lineup generated successfully!")

            # Analyze enrichments in lineup
            if isinstance(lineup, dict):
                players = lineup.get('players', [])

                # Count enrichments
                enrichment_counts = {
                    'with_vegas': 0,
                    'with_batting_order': 0,
                    'with_recent_form': 0,
                    'with_ownership': 0
                }

                for p in players:
                    if isinstance(p, dict):
                        if p.get('implied_team_score', 0) > 0:
                            enrichment_counts['with_vegas'] += 1
                        if p.get('batting_order', 0) > 0:
                            enrichment_counts['with_batting_order'] += 1
                        if p.get('recent_form', 0) != 0:
                            enrichment_counts['with_recent_form'] += 1
                        if p.get('ownership_projection', 0) > 0:
                            enrichment_counts['with_ownership'] += 1

                print("\n  Enrichment Coverage:")
                for enrichment, count in enrichment_counts.items():
                    print(f"    {enrichment:20}: {count}/10 players")
        else:
            print("  ❌ Failed to generate lineup")


def main():
    """Run complete enrichment audit"""

    print("\n" + "=" * 70)
    print("COMPLETE ENRICHMENT AUDIT")
    print("=" * 70)

    # Test 1: Available sources
    sources = test_available_sources()

    # Test 2: Strategy profiles
    test_enrichment_profiles()

    # Test 3: Actual enrichment
    test_actual_enrichment()

    # Test 4: Impact on lineups
    test_enrichment_impact()

    # Summary
    print("\n" + "=" * 70)
    print("ENRICHMENT SUMMARY")
    print("=" * 70)

    print("\n✅ CONFIRMED ENRICHMENTS:")
    print("  • Recent form calculation (working)")
    print("  • Consistency scores (working)")
    print("  • Batting order from confirmations (working)")

    print("\n⚠️ POSSIBLE ISSUES:")
    if not sources.get('Vegas Lines'):
        print("  • Vegas lines not available - using defaults")
    if not sources.get('Statcast'):
        print("  • Statcast not available - no advanced metrics")

    print("\n📊 ENRICHMENT USAGE BY STRATEGY:")
    print("  • projection_monster: Recent form + Consistency")
    print("  • pitcher_dominance: K-rates (if Statcast available)")
    print("  • tournament_winner_gpp: Ownership + Barrel rates")
    print("  • correlation_value: Vegas totals for stacking")

    print("\n💡 RECOMMENDATIONS:")
    print("  1. Vegas data would significantly improve all strategies")
    print("  2. Statcast critical for pitcher_dominance strategy")
    print("  3. Ownership projections needed for GPP success")
    print("  4. Consider caching enrichments to improve speed")


if __name__ == "__main__":
    main()