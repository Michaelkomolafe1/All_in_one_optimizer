#!/usr/bin/env python3
"""
REALISTIC ML COMPETITION
========================
Tests YOUR system (with auto-selected strategy) against realistic DFS field
Opponents use various approaches - NOT your system
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import multiprocessing as mp
from functools import partial
from typing import Dict, List, Tuple

# Add paths
sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

# Import YOUR components
from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem
from dfs_optimizer.strategies.strategy_selector import StrategyAutoSelector
from dfs_optimizer.core.unified_player_model import UnifiedPlayer

# Import simulator components
from ml_experiments.simulators.robust_dfs_simulator import (
    generate_slate, simulate_lineup_score, generate_field
)


def process_single_slate_vs_field(args: Tuple) -> Dict:
    """
    Process a single slate:
    - YOU use your exact system with auto-selected strategy
    - OPPONENTS are simulated field (various skill levels)
    """
    slate_id, contest_type, slate_size = args

    try:
        # Generate slate
        slate = generate_slate(slate_id, 'classic', slate_size)

        # BUILD YOUR LINEUP USING YOUR EXACT SYSTEM
        # Convert to UnifiedPlayer format - EXACTLY like ML bridge
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

            # Add simulator attributes - EXACTLY like ML bridge
            player.is_pitcher = (player.primary_position == 'P')
            for attr in ['ownership', 'recent_performance', 'matchup_score',
                         'hitting_matchup', 'pitching_matchup', 'park_factor',
                         'weather_score', 'vegas_score', 'correlation_score']:
                setattr(player, attr, sim_player.get(attr, 0))
            player._simulator_ownership = sim_player.get('ownership', 15)

            players.append(player)

        # Auto-select YOUR strategy for this slate/contest
        # Use the same approach as ML bridge - directly access based on known slate size
        selector = StrategyAutoSelector()
        your_strategy = selector.top_strategies[contest_type][slate_size]

        # Initialize YOUR system - EXACTLY like ML bridge
        system = UnifiedCoreSystem()
        system.players = players
        system.csv_loaded = True

        # Build and enrich pool - EXACTLY like ML bridge
        system.build_player_pool(include_unconfirmed=True)
        system.enrich_player_pool()

        # Restore simulator ownership after enrichment
        for p in system.player_pool:
            if hasattr(p, '_simulator_ownership'):
                p.ownership_projection = p._simulator_ownership

        # Score players with YOUR enhanced scoring engine
        system.score_players(contest_type)

        # Optimize with YOUR MILP optimizer
        lineups = system.optimize_lineups(
            num_lineups=1,
            strategy=your_strategy,
            contest_type=contest_type
        )

        if not lineups or not lineups[0]:
            return None

        your_lineup = lineups[0]

        # Convert YOUR lineup to simulator format
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

        # GENERATE OPPONENT FIELD - They DON'T use your system
        # This uses the simulator's realistic field generation
        field_size = 100  # Total contest size
        opponent_lineups = generate_field(slate, field_size - 1, contest_type)

        # Score all lineups
        all_scores = []

        # Your score
        your_score = simulate_lineup_score(your_sim_lineup)

        # Opponent scores
        opponent_scores = []
        for opp_lineup in opponent_lineups:
            score = simulate_lineup_score(opp_lineup)
            opponent_scores.append(score)

        # Combine and sort
        all_scores = [your_score] + opponent_scores
        all_scores.sort(reverse=True)

        # Find your rank
        your_rank = all_scores.index(your_score) + 1
        total_entries = len(all_scores)
        percentile = ((total_entries - your_rank) / total_entries) * 100

        # Calculate payout
        if contest_type == 'cash':
            # Top 44% cash
            win = your_rank <= int(total_entries * 0.44)
            roi = 100 if win else -100
        else:  # GPP
            if your_rank == 1:
                roi = 900
            elif your_rank <= 3:
                roi = 400
            elif your_rank <= int(total_entries * 0.1):  # Top 10%
                roi = 100
            elif your_rank <= int(total_entries * 0.2):  # Top 20%
                roi = -50
            else:
                roi = -100
            win = your_rank <= int(total_entries * 0.2)

        # Collect ML training data
        player_data = []
        for player in your_lineup['players']:
            player_data.append({
                'slate_id': slate_id,
                'strategy': your_strategy,
                'contest_type': contest_type,
                'slate_size': slate_size,
                'player_name': player.name,
                'position': player.primary_position,
                'team': player.team,
                'salary': player.salary,
                'ownership': getattr(player, 'ownership_projection', 15),
                'projection': getattr(player, 'base_projection', 0),
                'cash_score': getattr(player, 'cash_score', 0),
                'gpp_score': getattr(player, 'gpp_score', 0),
                'enhanced_score': getattr(player, 'enhanced_score', 0),
                'lineup_predicted': your_lineup.get('total_score', 0),
                'lineup_actual': your_score,
                'lineup_error': abs(your_score - your_lineup.get('total_score', 0)),
                'lineup_rank': your_rank,
                'lineup_percentile': percentile,
                'lineup_win': win,
                'lineup_roi': roi
            })

        return {
            'slate_id': slate_id,
            'strategy': your_strategy,
            'contest_type': contest_type,
            'slate_size': slate_size,
            'rank': your_rank,
            'score': your_score,
            'win': win,
            'roi': roi,
            'player_data': player_data
        }

    except Exception as e:
        print(f"\nError processing slate {slate_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


class RealisticMLCompetition:
    """Test YOUR system against realistic DFS field"""

    def __init__(self, num_cores=None):
        self.num_cores = num_cores or mp.cpu_count()
        self.strategy_selector = StrategyAutoSelector()

    def run_competition(self, slates_per_config: int = 100):
        """Run realistic competition"""

        print("\n" + "=" * 80)
        print("🏁 REALISTIC ML COMPETITION")
        print("=" * 80)
        print("\n📋 Competition Setup:")
        print("   • YOU: Use your full system (UnifiedCoreSystem + MILP)")
        print("   • YOU: Auto-select best strategy for each slate")
        print("   • OPPONENTS: Simulated field (various skill levels)")
        print("   • OPPONENTS: Don't use your system")
        print(f"\n⚡ Using {self.num_cores} CPU cores")
        print(f"🎯 Slates per configuration: {slates_per_config}")

        # Show what strategies you'll be using
        print("\n📊 Your strategies by slate type:")
        for contest_type in ['cash', 'gpp']:
            print(f"\n{contest_type.upper()}:")
            for slate_size in ['small', 'medium', 'large']:
                strategy = self.strategy_selector.top_strategies[contest_type][slate_size]
                print(f"   {slate_size}: {strategy}")

        # Create tasks
        tasks = []
        slate_id = 3000  # Start from 3000 to avoid conflicts

        for slate_size in ['small', 'medium', 'large']:
            for contest_type in ['cash', 'gpp']:
                for i in range(slates_per_config):
                    tasks.append((slate_id, contest_type, slate_size))
                    slate_id += 1

        print(f"\n🏁 Processing {len(tasks)} slates...")

        # Process in parallel
        all_results = []
        start_time = datetime.now()

        with mp.Pool(self.num_cores) as pool:
            for i, result in enumerate(pool.imap(process_single_slate_vs_field, tasks)):
                if i % 10 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (len(tasks) - i) / rate if rate > 0 else 0
                    print(f"\r   Progress: {i}/{len(tasks)} slates "
                          f"({rate:.1f} slates/sec, ETA: {eta / 60:.1f} min)",
                          end="", flush=True)

                if result:
                    all_results.append(result)

        print(f"\n\n✅ Processed {len(all_results)} slates successfully")

        # Analyze results
        self._analyze_results(all_results)

        # Save training data
        self._save_training_data(all_results)

    def _analyze_results(self, all_results):
        """Analyze competition results"""

        print("\n" + "=" * 80)
        print("📊 COMPETITION RESULTS vs REALISTIC FIELD")
        print("=" * 80)

        # Group by strategy and contest type
        strategy_performance = {}

        for result in all_results:
            key = f"{result['strategy']}_{result['contest_type']}"

            if key not in strategy_performance:
                strategy_performance[key] = {
                    'wins': 0,
                    'total': 0,
                    'roi_sum': 0,
                    'ranks': []
                }

            perf = strategy_performance[key]
            perf['total'] += 1
            perf['roi_sum'] += result['roi']
            perf['ranks'].append(result['rank'])
            if result['win']:
                perf['wins'] += 1

        # Print cash results
        print("\n💰 CASH GAME PERFORMANCE:")
        print(f"{'Strategy':<30} {'Win Rate':>10} {'Avg ROI':>10} {'Avg Rank':>10}")
        print("-" * 60)

        expected_cash_win = 44  # Top 44% win in cash

        cash_results = [(k, v) for k, v in strategy_performance.items() if '_cash' in k]
        cash_results.sort(key=lambda x: x[1]['wins'] / x[1]['total'], reverse=True)

        for key, perf in cash_results:
            strategy = key.replace('_cash', '')
            win_rate = (perf['wins'] / perf['total']) * 100
            avg_roi = perf['roi_sum'] / perf['total']
            avg_rank = np.mean(perf['ranks'])

            # Compare to expected
            if win_rate > expected_cash_win * 1.2:
                status = "🏆"  # Significantly better
            elif win_rate > expected_cash_win:
                status = "✅"  # Better than expected
            elif win_rate > expected_cash_win * 0.8:
                status = "➖"  # Close to expected
            else:
                status = "⚠️"  # Below expected

            print(f"{strategy:<30} {win_rate:>9.1f}% {avg_roi:>+9.1f}% {avg_rank:>9.1f} {status}")

        # Print GPP results
        print("\n🎯 GPP PERFORMANCE:")
        print(f"{'Strategy':<30} {'Win Rate':>10} {'Avg ROI':>10} {'Avg Rank':>10}")
        print("-" * 60)

        expected_gpp_win = 20  # Top 20% win in GPP

        gpp_results = [(k, v) for k, v in strategy_performance.items() if '_gpp' in k]
        gpp_results.sort(key=lambda x: x[1]['roi_sum'] / x[1]['total'], reverse=True)

        for key, perf in gpp_results:
            strategy = key.replace('_gpp', '')
            win_rate = (perf['wins'] / perf['total']) * 100
            avg_roi = perf['roi_sum'] / perf['total']
            avg_rank = np.mean(perf['ranks'])

            # Compare to expected
            if avg_roi > 50:
                status = "🔥"  # Great ROI
            elif avg_roi > 0:
                status = "✅"  # Positive ROI
            elif avg_roi > -50:
                status = "➖"  # Small loss
            else:
                status = "⚠️"  # Big loss

            print(f"{strategy:<30} {win_rate:>9.1f}% {avg_roi:>+9.1f}% {avg_rank:>9.1f} {status}")

        # Overall analysis
        total_cash = sum(v['total'] for k, v in strategy_performance.items() if '_cash' in k)
        total_gpp = sum(v['total'] for k, v in strategy_performance.items() if '_gpp' in k)
        cash_wins = sum(v['wins'] for k, v in strategy_performance.items() if '_cash' in k)
        gpp_wins = sum(v['wins'] for k, v in strategy_performance.items() if '_gpp' in k)

        overall_cash_win = (cash_wins / total_cash * 100) if total_cash > 0 else 0
        overall_gpp_win = (gpp_wins / total_gpp * 100) if total_gpp > 0 else 0

        print(f"\n📈 OVERALL PERFORMANCE:")
        print(f"   Cash win rate: {overall_cash_win:.1f}% (expected: {expected_cash_win}%)")
        print(f"   GPP win rate: {overall_gpp_win:.1f}% (expected: {expected_gpp_win}%)")

        if overall_cash_win > expected_cash_win * 1.5:
            print("\n⚠️  Note: Cash win rate seems high. Check if field strength is realistic.")
        elif overall_cash_win > expected_cash_win:
            print("\n✅ Your system is outperforming the field in cash games!")

        if overall_gpp_win > expected_gpp_win * 1.5:
            print("\n⚠️  Note: GPP win rate seems high. Check if field strength is realistic.")
        elif overall_gpp_win > expected_gpp_win:
            print("\n✅ Your system is outperforming the field in GPPs!")

    def _save_training_data(self, all_results):
        """Save ML training data"""

        # Extract all player data
        all_player_data = []

        for result in all_results:
            if 'player_data' in result:
                all_player_data.extend(result['player_data'])

        if all_player_data:
            df = pd.DataFrame(all_player_data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'realistic_ml_training_data_{timestamp}.csv'
            df.to_csv(filename, index=False)

            print(f"\n💾 Training data saved to: {filename}")
            print(f"   • Total records: {len(df):,}")
            print(f"   • Unique slates: {df['slate_id'].nunique()}")
            print(f"   • File size: {os.path.getsize(filename) / 1024 / 1024:.1f} MB")

            # Show sample of data
            print("\n📋 Sample records:")
            print(df[['slate_id', 'strategy', 'contest_type', 'lineup_rank', 'lineup_win', 'lineup_roi']].head(10))


if __name__ == "__main__":
    print("""
    🏁 REALISTIC ML COMPETITION
    ==========================

    This tests YOUR exact system against a realistic DFS field.

    Setup:
    - YOU use UnifiedCoreSystem + MILP optimizer
    - YOU auto-select best strategy for each slate
    - OPPONENTS are simulated (various skill levels)
    - 100-person contests (you + 99 opponents)

    Expected results:
    - Cash: ~44% win rate (top 44% cash)
    - GPP: ~20% win rate (top 20% cash)
    - Your edge depends on optimizer quality

    Options:
    1. Quick test (10 slates per config = 60 total)
    2. Standard test (50 slates per config = 300 total)
    3. Comprehensive test (100 slates per config = 600 total)
    4. Extended test (500 slates per config = 3000 total)
    """)

    choice = input("\nSelect option (1-4): ")

    # Ask about cores
    max_cores = mp.cpu_count()
    core_input = input(f"\nHow many CPU cores to use? (1-{max_cores}, default={max_cores}): ")
    num_cores = int(core_input) if core_input.isdigit() else max_cores

    competition = RealisticMLCompetition(num_cores=min(num_cores, max_cores))

    slates_map = {
        '1': 10,
        '2': 50,
        '3': 100,
        '4': 500
    }

    if choice in slates_map:
        competition.run_competition(slates_map[choice])
    else:
        print("Invalid choice!")

    print("\n✅ Competition complete!")
    print("\n⚠️  REMINDER: After ML testing, we need to fix your optimizer's lineup generation issue!")