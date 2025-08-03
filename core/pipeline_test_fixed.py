#!/usr/bin/env python3
"""
Fixed comprehensive test of the DFS optimization pipeline
"""
import sys

sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem
from dfs_optimizer.strategies.strategy_selector import StrategyAutoSelector
import pandas as pd
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def fix_projections(system, csv_path):
    """Fix missing projections from CSV"""
    # Read CSV to check columns
    df = pd.read_csv(csv_path)
    print(f"\nCSV Columns: {list(df.columns)}")

    # Try to find projection column
    projection_col = None
    for col in ['AvgPointsPerGame', 'Avg Points', 'Projection', 'FPPG', 'Points']:
        if col in df.columns:
            projection_col = col
            break

    if projection_col:
        print(f"Found projection column: {projection_col}")
        # Apply projections
        for player in system.players:
            matching = df[df['Name'] == player.name]
            if not matching.empty:
                proj = float(matching.iloc[0][projection_col])
                player.base_projection = proj
                player.enhanced_score = proj  # Initial score
    else:
        print("No projection column found - using salary-based projections")
        # Create projections based on salary
        for player in system.players:
            # Simple formula: expected points = salary / 400
            player.base_projection = player.salary / 400
            player.enhanced_score = player.base_projection


def test_full_pipeline(csv_path):
    """Test the complete optimization pipeline"""
    print("=" * 80)
    print(f"🧪 COMPREHENSIVE PIPELINE TEST")
    print(f"📁 CSV: {csv_path}")
    print("=" * 80)

    # Initialize system
    system = UnifiedCoreSystem()

    # 1. LOAD PLAYERS
    print("\n1️⃣ LOADING PLAYERS")
    print("-" * 40)
    system.load_players_from_csv(csv_path)
    print(f"✅ Loaded {len(system.players)} players from CSV")

    # Fix projections
    fix_projections(system, csv_path)

    # Show sample players
    print("\nSample players (with fixed projections):")
    for i, p in enumerate(system.players[:5]):
        print(f"  {i + 1}. {p.name} ({p.primary_position}) - ${p.salary} - {p.base_projection:.1f} pts")

    # 2. BUILD PLAYER POOL
    print("\n2️⃣ BUILDING PLAYER POOL")
    print("-" * 40)
    system.build_player_pool(include_unconfirmed=True)
    print(f"✅ Built pool with {len(system.player_pool)} players")

    # Check slate detection
    positions = {}
    teams = set()
    for p in system.player_pool:
        positions[p.primary_position] = positions.get(p.primary_position, 0) + 1
        teams.add(p.team)

    print(f"\n📊 Slate Analysis:")
    print(f"  Positions: {positions}")
    print(f"  Teams: {len(teams)} unique teams")
    print(f"  Games: ~{len(teams) // 2} games")

    # Detect slate type
    is_showdown = 'CPT' in positions or 'UTIL' in positions
    slate_type = "SHOWDOWN" if is_showdown else "CLASSIC"
    print(f"  Slate Type: {slate_type}")

    # 3. ENRICHMENT
    print("\n3️⃣ ENRICHMENT")
    print("-" * 40)

    # Check before enrichment
    sample_player = system.player_pool[0]
    print(f"Before enrichment - {sample_player.name}:")
    print(f"  Vegas: {sample_player.vegas_score}")
    print(f"  Park: {sample_player.park_score}")
    print(f"  Weather: {sample_player.weather_score}")

    # Run enrichment
    system.enrich_player_pool()

    # Check after enrichment
    print(f"\nAfter enrichment - {sample_player.name}:")
    print(f"  Vegas: {sample_player.vegas_score:.2f}")
    print(f"  Park: {sample_player.park_score:.2f}")
    print(f"  Weather: {sample_player.weather_score:.2f}")
    print(f"  Game total: {sample_player.game_total:.1f}")

    # Check variation
    vegas_scores = set(p.vegas_score for p in system.player_pool[:50])
    park_scores = set(p.park_score for p in system.player_pool[:50])
    print(f"\n📊 Enrichment Variation:")
    print(f"  Unique Vegas scores: {len(vegas_scores)}")
    print(f"  Unique Park scores: {len(park_scores)}")

    # 4. SCORING COMPARISON
    print("\n4️⃣ SCORING COMPARISON")
    print("-" * 40)

    # Score for GPP first
    system.score_players('gpp')

    # Compare base vs enhanced scoring
    print("\nBase Projection vs Enhanced Score (top 10 players):")
    print(f"{'Player':<25} {'Pos':<4} {'Salary':<7} {'Base':<8} {'Enhanced':<10} {'Diff':<8}")
    print("-" * 70)

    # Sort by enhanced score
    top_players = sorted(system.player_pool, key=lambda p: p.enhanced_score, reverse=True)[:10]

    for p in top_players:
        diff = p.enhanced_score - p.base_projection
        diff_pct = (diff / p.base_projection * 100) if p.base_projection > 0 else 0
        print(f"{p.name:<25} {p.primary_position:<4} ${p.salary:<6} {p.base_projection:<8.1f} "
              f"{p.enhanced_score:<10.1f} {diff_pct:>+7.1f}%")

    # 5. CASH VS GPP SCORING
    print("\n5️⃣ CASH VS GPP SCORING DIFFERENCES")
    print("-" * 40)

    # Score for cash
    system.score_players('cash')
    cash_scores = {p.name: p.cash_score for p in system.player_pool}

    # Score for GPP
    system.score_players('gpp')
    gpp_scores = {p.name: p.gpp_score for p in system.player_pool}

    # Find players with biggest differences
    score_diffs = []
    for p in system.player_pool[:100]:  # Check first 100
        diff = abs(gpp_scores[p.name] - cash_scores[p.name])
        if diff > 0.1:  # Only significant differences
            score_diffs.append((p, cash_scores[p.name], gpp_scores[p.name], diff))

    score_diffs.sort(key=lambda x: x[3], reverse=True)

    if score_diffs:
        print("\nBiggest Cash vs GPP score differences:")
        print(f"{'Player':<25} {'Pos':<4} {'Cash':<8} {'GPP':<8} {'Diff':<8}")
        print("-" * 55)
        for p, cash, gpp, diff in score_diffs[:5]:
            print(f"{p.name:<25} {p.primary_position:<4} {cash:<8.1f} {gpp:<8.1f} {diff:<8.1f}")
    else:
        print("\nNo significant Cash vs GPP differences found")

    # 6. STRATEGY SELECTION
    print("\n6️⃣ STRATEGY AUTO-SELECTION")
    print("-" * 40)

    selector = StrategyAutoSelector()

    # Determine slate size
    num_games = len(teams) // 2
    if num_games <= 3:
        slate_size = 'small'
    elif num_games <= 7:
        slate_size = 'medium'
    else:
        slate_size = 'large'

    print(f"Slate size: {slate_size} ({num_games} games)")

    # Use the correct method name
    cash_strategy = selector.top_strategies['cash'][slate_size]
    gpp_strategy = selector.top_strategies['gpp'][slate_size]

    print(f"\nRecommended strategies:")
    print(f"  Cash: {cash_strategy}")
    print(f"  GPP: {gpp_strategy}")

    # 7. OPTIMIZATION - CASH
    print("\n7️⃣ CASH OPTIMIZATION")
    print("-" * 40)

    system.score_players('cash')
    cash_lineups = system.optimize_lineups(
        num_lineups=3,
        strategy=cash_strategy,
        contest_type='cash'
    )

    if cash_lineups:
        print(f"✅ Generated {len(cash_lineups)} cash lineups")

        # Show first lineup
        lineup = cash_lineups[0]
        print(f"\nCash Lineup #1 (Score: {lineup['total_score']:.1f}, Salary: ${lineup['total_salary']})")
        print(f"{'Player':<25} {'Pos':<4} {'Team':<4} {'Salary':<7} {'Score':<7}")
        print("-" * 55)
        for p in lineup['players']:
            print(f"{p.name:<25} {p.primary_position:<4} {p.team:<4} "
                  f"${p.salary:<6} {p.cash_score:<7.1f}")

    # 8. OPTIMIZATION - GPP
    print("\n8️⃣ GPP OPTIMIZATION")
    print("-" * 40)

    system.score_players('gpp')
    gpp_lineups = system.optimize_lineups(
        num_lineups=5,
        strategy=gpp_strategy,
        contest_type='gpp',
        min_unique_players=3
    )

    if gpp_lineups:
        print(f"✅ Generated {len(gpp_lineups)} GPP lineups")

        # Show diversity
        all_players = set()
        for lineup in gpp_lineups:
            all_players.update(p.name for p in lineup['players'])

        print(f"  Total unique players used: {len(all_players)}")

        # Show first GPP lineup
        lineup = gpp_lineups[0]
        print(f"\nGPP Lineup #1 (Score: {lineup['total_score']:.1f}, Salary: ${lineup['total_salary']})")
        print(f"{'Player':<25} {'Pos':<4} {'Team':<4} {'Salary':<7} {'Score':<7}")
        print("-" * 55)
        for p in lineup['players']:
            print(f"{p.name:<25} {p.primary_position:<4} {p.team:<4} "
                  f"${p.salary:<6} {p.gpp_score:<7.1f}")

    # 9. STRATEGY COMPARISON
    print("\n9️⃣ STRATEGY COMPARISON")
    print("-" * 40)

    if cash_lineups and gpp_lineups:
        # Compare top cash vs GPP lineup
        cash_players = set(p.name for p in cash_lineups[0]['players'])
        gpp_players = set(p.name for p in gpp_lineups[0]['players'])

        overlap = cash_players & gpp_players
        cash_only = cash_players - gpp_players
        gpp_only = gpp_players - cash_players

        print(f"Player overlap: {len(overlap)}/10 players")
        if cash_only:
            print(f"  Cash-only: {', '.join(list(cash_only)[:3])}")
        if gpp_only:
            print(f"  GPP-only: {', '.join(list(gpp_only)[:3])}")

    # 10. FINAL SUMMARY
    print("\n🎯 FINAL SUMMARY")
    print("-" * 40)

    # Show value plays
    value_players = sorted(system.player_pool,
                           key=lambda p: p.enhanced_score / (p.salary / 1000) if p.salary > 0 else 0,
                           reverse=True)[:5]

    print("\nTop Value Plays (pts per $1k):")
    for p in value_players:
        value = p.enhanced_score / (p.salary / 1000) if p.salary > 0 else 0
        print(f"  {p.name} ({p.primary_position}): {value:.2f} pts/$1k")

    print("\n" + "=" * 80)
    print("✅ PIPELINE TEST COMPLETE!")
    print("=" * 80)

    return system


if __name__ == "__main__":
    """Run tests on available CSV files"""
    csv_files = [
        "/home/michael/Downloads/DKSalaries(33).csv",
        "/home/michael/Downloads/DKSalaries(34).csv"
    ]

    for csv_path in csv_files:
        try:
            print(f"\n\n{'🏈' * 40}\n")
            system = test_full_pipeline(csv_path)

            # Quick summary
            print(f"\n📊 QUICK SUMMARY for {csv_path.split('/')[-1]}:")
            print(f"  Players loaded: {len(system.players)}")
            print(f"  Player pool: {len(system.player_pool)}")
            print(f"  Enrichment: {'✅ Applied' if system.enrichments_applied else '❌ Failed'}")

        except Exception as e:
            print(f"\n❌ ERROR testing {csv_path}: {e}")
            import traceback

            traceback.print_exc()