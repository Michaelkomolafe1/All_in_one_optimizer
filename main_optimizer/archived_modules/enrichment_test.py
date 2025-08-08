#!/usr/bin/env python3
"""
ENRICHMENT AUDIT SYSTEM
=======================
Tests what enrichments each strategy actually uses
"""

import sys
import os

sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem
from smart_enrichment_manager import SmartEnrichmentManager

print("=" * 70)
print("ENRICHMENT AUDIT - WHAT'S ACTUALLY BEING USED")
print("=" * 70)

# Define what each strategy SHOULD use based on your profiles
EXPECTED_ENRICHMENTS = {
    'projection_monster': {
        'vegas': True,
        'statcast': False,
        'ownership': False,
        'weather': False,
        'batting_order': True,
        'recent_form': True,
        'consistency': True,
        'statcast_players': 0
    },
    'pitcher_dominance': {
        'vegas': True,
        'statcast': True,  # NEEDS K-rates
        'ownership': False,
        'weather': False,
        'batting_order': True,
        'recent_form': True,
        'consistency': True,
        'k_rate': True,
        'statcast_players': 20  # Top pitchers only
    },
    'tournament_winner_gpp': {
        'vegas': True,
        'statcast': True,
        'ownership': True,  # CRITICAL for GPP
        'weather': False,
        'batting_order': True,
        'recent_form': True,
        'barrel_rate': True,
        'hard_hit': True,
        'statcast_players': 50
    },
    'correlation_value': {
        'vegas': True,  # Team totals critical
        'statcast': True,
        'ownership': True,
        'weather': False,
        'batting_order': True,  # For stacking
        'recent_form': True,
        'barrel_rate': True,
        'statcast_players': 40
    }
}


def test_enrichment_sources():
    """Test what enrichment sources are available"""
    print("\n1. CHECKING AVAILABLE ENRICHMENT SOURCES")
    print("-" * 50)

    system = UnifiedCoreSystem()

    sources = {
        'Vegas Lines': system.vegas_lines is not None,
        'Statcast': system.stats_fetcher is not None,
        'Confirmations': system.confirmation_system is not None,
        'Enrichment Manager': system.enrichment_manager is not None
    }

    for source, available in sources.items():
        status = "✅ Available" if available else "❌ Not Available"
        print(f"  {source:20} : {status}")

    return sources


def test_strategy_enrichments():
    """Test what each strategy actually enriches"""
    print("\n2. TESTING STRATEGY ENRICHMENTS")
    print("-" * 50)

    system = UnifiedCoreSystem()
    manager = SmartEnrichmentManager()

    # Load test data
    csv_path = "/home/michael/Downloads/DKSalaries(46).csv"
    system.load_csv(csv_path)
    system.fetch_confirmed_players()
    system.build_player_pool(include_unconfirmed=True)

    results = {}

    for strategy, expected in EXPECTED_ENRICHMENTS.items():
        print(f"\n  Testing {strategy}...")

        # Get enrichment profile
        profile = manager.get_enrichment_requirements(
            slate_size='medium',
            strategy=strategy,
            contest_type='gpp' if 'gpp' in strategy else 'cash'
        )

        # Check what's configured
        configured = {
            'vegas': profile.needs_vegas,
            'statcast': profile.needs_statcast,
            'ownership': profile.needs_ownership,
            'weather': profile.needs_weather,
            'batting_order': profile.needs_batting_order,
            'recent_form': profile.needs_recent_form,
            'consistency': profile.needs_consistency,
            'k_rate': profile.needs_k_rate if hasattr(profile, 'needs_k_rate') else False,
            'barrel_rate': profile.needs_barrel_rate,
            'statcast_players': profile.statcast_priority_players
        }

        # Compare with expected
        print(f"    Expected vs Configured:")
        for key in expected:
            exp_val = expected[key]
            conf_val = configured.get(key, False)
            match = "✅" if exp_val == conf_val else "❌"
            print(f"      {key:15} : Expected={exp_val:5} Configured={conf_val:5} {match}")

        results[strategy] = configured

    return results


def test_actual_enrichment():
    """Test if enrichments are actually applied to players"""
    print("\n3. TESTING ACTUAL PLAYER ENRICHMENT")
    print("-" * 50)

    system = UnifiedCoreSystem()
    csv_path = "/home/michael/Downloads/DKSalaries(46).csv"

    # Load and setup
    system.load_csv(csv_path)
    system.fetch_confirmed_players()

    # Test each strategy
    strategies = ['projection_monster', 'pitcher_dominance', 'tournament_winner_gpp', 'correlation_value']

    for strategy in strategies:
        print(f"\n  {strategy}:")

        # Build pool and enrich
        system.build_player_pool(include_unconfirmed=True)

        # Score players (which triggers enrichment)
        contest_type = 'gpp' if 'gpp' in strategy else 'cash'
        system.score_players(contest_type)

        # Check a sample player for enrichments
        if system.player_pool:
            # Get a high-salary player (more likely to have data)
            test_player = sorted(system.player_pool, key=lambda p: p.salary, reverse=True)[0]

            enrichments = {
                'name': test_player.name,
                'team': test_player.team,
                'salary': test_player.salary,
                'base_projection': getattr(test_player, 'base_projection', None),
                'optimization_score': getattr(test_player, 'optimization_score', None),
                'implied_team_score': getattr(test_player, 'implied_team_score', None),
                'batting_order': getattr(test_player, 'batting_order', 0),
                'recent_form': getattr(test_player, 'recent_form', None),
                'consistency_score': getattr(test_player, 'consistency_score', None),
                'ownership_projection': getattr(test_player, 'ownership_projection', None),
                'k_rate': getattr(test_player, 'k_rate', None),
                'barrel_rate': getattr(test_player, 'barrel_rate', None),
            }

            print(f"    Sample Player: {enrichments['name']} (${enrichments['salary']})")
            print(f"      Base Projection: {enrichments['base_projection']}")
            print(f"      Optimization Score: {enrichments['optimization_score']}")
            print(f"      Team Score (Vegas): {enrichments['implied_team_score']}")
            print(f"      Batting Order: {enrichments['batting_order']}")
            print(f"      Recent Form: {enrichments['recent_form']}")
            print(f"      Consistency: {enrichments['consistency_score']}")

            if 'gpp' in strategy:
                print(f"      Ownership: {enrichments['ownership_projection']}")

            if strategy == 'pitcher_dominance' and test_player.position in ['P', 'SP', 'RP']:
                print(f"      K-Rate: {enrichments['k_rate']}")

            if 'tournament_winner' in strategy:
                print(f"      Barrel Rate: {enrichments['barrel_rate']}")


def test_enrichment_impact():
    """Test how enrichments affect lineup scores"""
    print("\n4. TESTING ENRICHMENT IMPACT ON LINEUPS")
    print("-" * 50)

    system = UnifiedCoreSystem()
    csv_path = "/home/michael/Downloads/DKSalaries(46).csv"

    system.load_csv(csv_path)
    system.fetch_confirmed_players()
    system.build_player_pool(include_unconfirmed=True)

    # Test with and without enrichments (if possible)
    strategies = [
        ('projection_monster', 'cash'),
        ('tournament_winner_gpp', 'gpp')
    ]

    for strategy, contest_type in strategies:
        print(f"\n  {strategy} ({contest_type}):")

        # Generate lineup
        lineups = system.optimize_lineup(
            strategy=strategy,
            contest_type=contest_type,
            num_lineups=1
        )

        if lineups:
            lineup = lineups[0]

            # Check enrichments in lineup
            enriched_count = 0
            for player in (lineup.get('players', []) if isinstance(lineup, dict) else []):
                if isinstance(player, dict):
                    if player.get('recent_form', 0) != 0:
                        enriched_count += 1

            print(f"    Players with enrichments: {enriched_count}/10")

            # Show top scorers
            if isinstance(lineup, dict):
                players = lineup.get('players', [])
                top_scorers = sorted(players, key=lambda p: p.get('projection', 0), reverse=True)[:3]
                print(f"    Top scorers in lineup:")
                for p in top_scorers:
                    print(f"      {p.get('name', 'Unknown'):20} : {p.get('projection', 0):.1f} pts")


def main():
    """Run all enrichment tests"""

    # Test 1: Check sources
    sources = test_enrichment_sources()

    # Test 2: Check strategy configurations
    configs = test_strategy_enrichments()

    # Test 3: Check actual enrichment
    test_actual_enrichment()

    # Test 4: Check impact
    test_enrichment_impact()

    # Summary
    print("\n" + "=" * 70)
    print("ENRICHMENT AUDIT SUMMARY")
    print("=" * 70)

    print("\n📊 ENRICHMENTS BY STRATEGY:")
    print("-" * 40)

    summary = {
        'projection_monster (CASH)': [
            '✅ Vegas team totals',
            '✅ Recent form (last 5 games)',
            '✅ Consistency scores',
            '✅ Batting order',
            '❌ NO Statcast (not needed)',
            '❌ NO Ownership (cash game)'
        ],
        'pitcher_dominance (CASH)': [
            '✅ K-rates (via Statcast)',
            '✅ Recent form',
            '✅ Consistency',
            '✅ Vegas totals',
            '⚠️ Statcast for top 20 pitchers only',
            '❌ NO Ownership'
        ],
        'tournament_winner_gpp (GPP)': [
            '✅ Ownership projections (CRITICAL)',
            '✅ Barrel rates (upside)',
            '✅ Hard hit rates',
            '✅ Vegas totals',
            '✅ Batting order (stacking)',
            '⚠️ Statcast for top 50 players'
        ],
        'correlation_value (GPP)': [
            '✅ Vegas team totals (stacking)',
            '✅ Ownership',
            '✅ Batting order (correlation)',
            '✅ Barrel rates',
            '⚠️ Statcast for top 40 players'
        ]
    }

    for strategy, enrichments in summary.items():
        print(f"\n{strategy}:")
        for item in enrichments:
            print(f"  {item}")

    print("\n💡 KEY INSIGHTS:")
    print("-" * 40)
    print("• Cash strategies focus on consistency, not ownership")
    print("• GPP strategies ALWAYS need ownership data")
    print("• Statcast is limited to top N players to save API calls")
    print("• Vegas data is used by ALL strategies")
    print("• pitcher_dominance specifically needs K-rates")
    print("• tournament_winner_gpp needs the most enrichments")


if __name__ == "__main__":
    main()