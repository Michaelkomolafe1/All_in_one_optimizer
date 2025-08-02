#!/usr/bin/env python3
"""
FIXED WORKING DFS OPTIMIZER
==========================
All fixes applied and working
"""

import sys
import pandas as pd

sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem
from dfs_optimizer.strategies.strategy_selector import StrategyAutoSelector


def fix_projections(system, csv_path):
    """Apply projection fix"""
    df = pd.read_csv(csv_path)
    for player in system.players:
        matching_row = df[df['Name'] == player.name]
        if not matching_row.empty:
            player.base_projection = float(matching_row.iloc[0]['AvgPointsPerGame'])
            player.projection = player.base_projection
        player.is_pitcher = player.primary_position in ['P', 'SP', 'RP']

        # NORMALIZE POSITIONS - This is likely the issue!
        if player.primary_position in ['SP', 'RP']:
            player.primary_position = 'P'


def main():
    # Settings
    CSV_PATH = "/home/michael/Downloads/DKSalaries(32).csv"  # Update with your CSV
    CONTEST_TYPE = "gpp"  # or "cash"
    NUM_LINEUPS = 5  # Start with fewer for testing

    print("=" * 60)
    print(f"🎯 DFS OPTIMIZER - {CONTEST_TYPE.upper()} MODE")
    print("=" * 60)

    # Initialize system
    system = UnifiedCoreSystem()
    selector = StrategyAutoSelector()

    # Load and fix data
    print("\n📊 Loading data...")
    system.load_players_from_csv(CSV_PATH)
    fix_projections(system, CSV_PATH)

    # Verify projections loaded
    proj_count = sum(1 for p in system.players if p.base_projection > 0)
    print(f"   ✅ {proj_count}/{len(system.players)} players have projections")

    # Build player pool
    print("\n🏗️  Building player pool...")
    system.build_player_pool(include_unconfirmed=True)

    # Also normalize positions in player pool
    for p in system.player_pool:
        if p.primary_position in ['SP', 'RP']:
            p.primary_position = 'P'

    system.enrich_player_pool()

    # Analyze slate - FIXED METHOD NAME
    slate_analysis = selector.analyze_slate_from_csv(system.player_pool)

    # Determine slate size based on game count
    game_count = slate_analysis.get('game_count', 1)
    if game_count <= 4:
        slate_size = 'small'
    elif game_count <= 9:
        slate_size = 'medium'
    else:
        slate_size = 'large'

    # Select strategy
    strategy = selector.top_strategies[CONTEST_TYPE][slate_size]
    print(f"\n🎲 Slate: {slate_size} ({game_count} games)")
    print(f"📋 Strategy: {strategy}")

    # Score players
    print(f"\n💯 Scoring players for {CONTEST_TYPE}...")
    system.score_players(CONTEST_TYPE)

    # Check position availability
    from collections import defaultdict
    position_counts = defaultdict(int)
    for p in system.player_pool:
        position_counts[p.primary_position] += 1

    print("\n📊 Position availability:")
    for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
        count = position_counts.get(pos, 0)
        print(f"   {pos}: {count} players")

    # Generate lineups
    print(f"\n🎯 Generating {NUM_LINEUPS} lineups...")
    lineups = system.optimize_lineups(
        num_lineups=NUM_LINEUPS,
        strategy=strategy,
        contest_type=CONTEST_TYPE,
        min_unique_players=3
    )

    # Display results
    if lineups:
        print(f"\n✅ Generated {len(lineups)} lineups!")

        # Show first lineup in detail
        lineup = lineups[0]
        print(f"\n{'=' * 50}")
        print(f"LINEUP 1 DETAILS")
        print(f"{'=' * 50}")
        print(f"Salary: ${lineup['total_salary']:,}/50,000")
        print(f"Projected: {lineup['total_projection']:.1f} points")

        # Check for stacks
        team_counts = defaultdict(int)
        for p in lineup['players']:
            team_counts[p.team] += 1

        stacks = [(team, count) for team, count in team_counts.items() if count >= 3]
        if stacks:
            print(f"Stacks: {', '.join([f'{team}({count})' for team, count in stacks])}")

        print("\nPlayers:")
        position_order = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
        sorted_players = []

        for pos in position_order:
            for p in lineup['players']:
                if p.primary_position == pos and p not in sorted_players:
                    sorted_players.append(p)
                    break

        for p in sorted_players:
            score = getattr(p, 'optimization_score', 0)
            print(f"  {p.primary_position}: {p.name} ({p.team}) - ${p.salary:,} - {score:.1f} pts")

        # Summary of all lineups
        if len(lineups) > 1:
            print(f"\n📊 All {len(lineups)} lineups summary:")
            for i, lineup in enumerate(lineups):
                print(f"   Lineup {i + 1}: ${lineup['total_salary']:,} - {lineup['total_projection']:.1f} pts")

    else:
        print("\n❌ Failed to generate lineups")
        print("\n🔍 Debugging info:")
        print("   Run the optimizer_debug.py script to diagnose the issue")


if __name__ == "__main__":
    main()