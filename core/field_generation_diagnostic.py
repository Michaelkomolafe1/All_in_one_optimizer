#!/usr/bin/env python3
"""
FIELD GENERATION DIAGNOSTIC
==========================
Check exactly what's happening with opponent generation
"""

import sys
import os
import pandas as pd
import numpy as np
import random

# Add paths
sys.path.insert(0, '/')

# Import YOUR components
from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem
from dfs_optimizer.strategies.strategy_selector import StrategyAutoSelector
from dfs_optimizer.core.unified_player_model import UnifiedPlayer

# Import simulator components
from ml_experiments.simulators.robust_dfs_simulator import (
    generate_slate, simulate_lineup_score, generate_field
)


def detailed_field_diagnostic():
    """Run detailed diagnostic on field generation"""

    print("\n" + "=" * 80)
    print("🔍 FIELD GENERATION DIAGNOSTIC")
    print("=" * 80)

    # Generate test slate
    slate = generate_slate(1234, 'classic', 'medium')
    print(f"\n✅ Generated slate with {len(slate['players'])} players")

    # Test 1: Raw field generation
    print("\n📊 TEST 1: Raw generate_field() calls")
    print("-" * 60)

    for contest_type in ['cash', 'gpp']:
        print(f"\n{contest_type.upper()}:")

        # Try different field sizes
        for requested_size in [20, 50, 100]:
            field = generate_field(slate, requested_size, contest_type)
            actual_size = len(field) if field else 0
            print(f"  Requested: {requested_size}, Got: {actual_size} ({actual_size / requested_size * 100:.0f}%)")

    # Test 2: Batched generation (like your competition does)
    print("\n📊 TEST 2: Batched generation (your competition method)")
    print("-" * 60)

    num_opponents_needed = 99
    opponent_lineups = []
    batch_size = 20
    max_attempts = 10
    attempts = 0

    print(f"Target: {num_opponents_needed} opponents")
    print(f"Batch size: {batch_size}")

    while len(opponent_lineups) < num_opponents_needed and attempts < max_attempts:
        batch = generate_field(slate, batch_size, 'cash')
        if batch:
            opponent_lineups.extend(batch)
            print(f"  Attempt {attempts + 1}: Got {len(batch)}, Total: {len(opponent_lineups)}")
        else:
            print(f"  Attempt {attempts + 1}: Got 0, Total: {len(opponent_lineups)}")
        attempts += 1

    print(f"\nFinal count: {len(opponent_lineups)} opponents")

    # Test 3: Analyze field quality
    print("\n📊 TEST 3: Field quality analysis")
    print("-" * 60)

    if opponent_lineups:
        # Score all lineups
        scores = []
        for lineup in opponent_lineups[:20]:  # Sample first 20
            score = simulate_lineup_score(lineup)
            scores.append(score)

        print(f"Field score statistics (sample of 20):")
        print(f"  Average: {np.mean(scores):.1f}")
        print(f"  Min: {min(scores):.1f}")
        print(f"  Max: {max(scores):.1f}")
        print(f"  Std Dev: {np.std(scores):.1f}")

    # Test 4: Compare YOUR lineup vs field
    print("\n📊 TEST 4: Your lineup vs field comparison")
    print("-" * 60)

    # Build YOUR lineup
    players = []
    for sim_player in slate['players']:
        player = UnifiedPlayer(
            id=str(sim_player.get('id', hash(sim_player['name']))),
            name=sim_player['name'],
            team=sim_player['team'],
            salary=sim_player['salary'],
            primary_position=sim_player['position'],
            positions=[sim_player['position']],
            base_projection=sim_player.get('projection', 0)
        )

        player.is_pitcher = (player.primary_position == 'P')
        for attr in ['ownership', 'recent_performance', 'matchup_score',
                     'hitting_matchup', 'pitching_matchup', 'park_factor',
                     'weather_score', 'vegas_score', 'correlation_score']:
            setattr(player, attr, sim_player.get(attr, 0))
        player._simulator_ownership = sim_player.get('ownership', 15)

        players.append(player)

    # Use YOUR system
    system = UnifiedCoreSystem()
    system.players = players
    system.csv_loaded = True
    system.build_player_pool(include_unconfirmed=True)
    system.enrich_player_pool()

    for p in system.player_pool:
        if hasattr(p, '_simulator_ownership'):
            p.ownership_projection = p._simulator_ownership

    system.score_players('cash')

    selector = StrategyAutoSelector()
    strategy = selector.top_strategies['cash']['medium']

    lineups = system.optimize_lineups(
        num_lineups=1,
        strategy=strategy,
        contest_type='cash'
    )

    if lineups and lineups[0]:
        your_lineup = lineups[0]

        # Convert to sim format
        your_sim_lineup = {
            'projection': your_lineup.get('total_score', 0),
            'salary': sum(p.salary for p in your_lineup['players']),
            'players': []
        }

        for player in your_lineup['players']:
            sim_player = {
                'name': player.name,
                'position': player.primary_position,
                'team': player.team,
                'salary': player.salary,
                'projection': getattr(player, 'fantasy_points', 0),
                'ownership': getattr(player, 'ownership_projection', 15)
            }
            your_sim_lineup['players'].append(sim_player)

        your_score = simulate_lineup_score(your_sim_lineup)

        print(f"YOUR lineup:")
        print(f"  Predicted score: {your_lineup.get('total_score', 0):.1f}")
        print(f"  Simulated score: {your_score:.1f}")
        print(f"  Total salary: ${sum(p.salary for p in your_lineup['players']):,}")

        # Compare to field
        if opponent_lineups:
            field_scores = [simulate_lineup_score(l) for l in opponent_lineups]
            your_rank = len([s for s in field_scores if s > your_score]) + 1

            print(f"\nComparison:")
            print(f"  Your score: {your_score:.1f}")
            print(f"  Field average: {np.mean(field_scores):.1f}")
            print(f"  Your rank: {your_rank} / {len(field_scores) + 1}")
            print(f"  Percentile: {((len(field_scores) + 1 - your_rank) / (len(field_scores) + 1) * 100):.1f}%")
            print(f"  Would win cash: {your_rank <= (len(field_scores) + 1) * 0.44}")

    # Test 5: Check your training data
    print("\n📊 TEST 5: Training data analysis")
    print("-" * 60)

    import glob
    csv_files = glob.glob('realistic_ml_training_data_*.csv')

    if csv_files:
        latest_file = max(csv_files, key=os.path.getctime)
        df = pd.read_csv(latest_file)

        # Check unique ranks per slate
        rank_stats = df.groupby('slate_id')['lineup_rank'].agg(['min', 'max', 'count'])

        print(f"Rank statistics per slate:")
        print(f"  Average max rank: {rank_stats['max'].mean():.1f}")
        print(f"  Min of max ranks: {rank_stats['max'].min()}")
        print(f"  Max of max ranks: {rank_stats['max'].max()}")

        # Sample a few slates
        print("\nSample slate details:")
        for slate_id in df['slate_id'].unique()[:5]:
            slate_df = df[df['slate_id'] == slate_id]
            print(f"  Slate {slate_id}: {len(slate_df)} entries, "
                  f"ranks {slate_df['lineup_rank'].min()}-{slate_df['lineup_rank'].max()}")


def test_simple_lineup_generation():
    """Test if we can generate simple lineups reliably"""

    print("\n" + "=" * 80)
    print("🔧 SIMPLE LINEUP GENERATION TEST")
    print("=" * 80)

    slate = generate_slate(9999, 'classic', 'medium')

    # Create 100 simple random lineups
    simple_lineups = []

    for i in range(100):
        # Group by position
        by_position = {}
        for p in slate['players']:
            pos = p['position']
            if pos not in by_position:
                by_position[pos] = []
            by_position[pos].append(p)

        # Build lineup
        lineup_players = []
        lineup_players.extend(random.sample(by_position.get('P', []), min(2, len(by_position.get('P', [])))))
        lineup_players.extend(random.sample(by_position.get('C', []), min(1, len(by_position.get('C', [])))))
        lineup_players.extend(random.sample(by_position.get('1B', []), min(1, len(by_position.get('1B', [])))))
        lineup_players.extend(random.sample(by_position.get('2B', []), min(1, len(by_position.get('2B', [])))))
        lineup_players.extend(random.sample(by_position.get('3B', []), min(1, len(by_position.get('3B', [])))))
        lineup_players.extend(random.sample(by_position.get('SS', []), min(1, len(by_position.get('SS', [])))))
        lineup_players.extend(random.sample(by_position.get('OF', []), min(3, len(by_position.get('OF', [])))))

        if len(lineup_players) == 10:
            simple_lineup = {
                'players': lineup_players,
                'salary': sum(p.get('salary', 5000) for p in lineup_players),
                'projection': sum(p.get('projection', 0) for p in lineup_players),
                'skill_level': 'random'
            }
            simple_lineups.append(simple_lineup)

    print(f"✅ Generated {len(simple_lineups)} simple lineups")

    if simple_lineups:
        scores = [simulate_lineup_score(l) for l in simple_lineups[:20]]
        print(f"Score stats: {np.mean(scores):.1f} ± {np.std(scores):.1f}")


def main():
    """Run all diagnostics"""
    detailed_field_diagnostic()
    test_simple_lineup_generation()

    print("\n" + "=" * 80)
    print("💡 DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print("\nIf field generation is failing to produce 99 opponents:")
    print("1. The lineup builder in generate_field might be too restrictive")
    print("2. The slate might not have enough valid player combinations")
    print("3. The skill-based building might be failing")
    print("\nNext steps:")
    print("1. Use simple random lineup generation as fallback")
    print("2. Ensure exactly 100 total entries per contest")
    print("3. Re-run competition with fixed field size")


if __name__ == "__main__":
    main()