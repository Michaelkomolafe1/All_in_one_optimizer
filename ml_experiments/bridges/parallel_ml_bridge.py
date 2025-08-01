# simulator_ml_bridge_parallel.py
"""
PARALLEL ML BRIDGE - Tests YOUR System with Multiprocessing
===========================================================
Uses YOUR MILP optimizer and parallel processing for speed
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Tuple
import time
import multiprocessing as mp
from functools import partial

# Add paths
sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')
sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer/config/simulation_test')

# Import YOUR components
from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem
from dfs_optimizer.strategies.strategy_selector import StrategyAutoSelector
from dfs_optimizer.core.unified_player_model import UnifiedPlayer

# Import simulator components
from ml_experiments.simulators.robust_dfs_simulator import (
    generate_slate, simulate_lineup_score, generate_field
)


def process_single_slate(args: Tuple) -> Dict:
    """Process a single slate - used for parallel processing"""
    slate_id, strategy_config, contest_type, slate_size = args

    try:
        # Generate slate
        slate = generate_slate(slate_id, 'classic', slate_size)

        # Convert to UnifiedPlayer format
        players = []
        for sim_player in slate['players']:
            player = UnifiedPlayer(
                id=str(sim_player.get('id', hash(sim_player['name']))),
                name=sim_player['name'],
                team=sim_player['team'],
                salary=sim_player['salary'],
                primary_position=sim_player['position'],
                positions=[sim_player['position']],  # Single position for now
                base_projection=sim_player.get('projection', 0)
            )

            # Add simulator attributes
            player.is_pitcher = (player.primary_position == 'P')
            # Extract ACTUAL simulator data - it's all at the top level!
            player.batting_order = sim_player.get('batting_order', 0)
            
            # Game totals - directly on player, not in game_data
            player.game_total = sim_player.get('game_total', 9.0)
            player.implied_team_score = player.game_total / 2  # Estimate team total
            player.team_total = player.implied_team_score
            
            # CRITICAL FIX: Store ownership in a protected attribute
            player._simulator_ownership = sim_player.get('ownership', 15)
            
            # Pitcher stats
            if player.primary_position == 'P':
                player.k_rate = sim_player.get('k_rate', 22.0)
                player.whip = sim_player.get('whip', 1.25)
                player.era = sim_player.get('era', 4.00)
                player.k9 = sim_player.get('k_per_9', 9.0)
                player.woba = (sim_player.get('vs_l_woba', 0.320) + sim_player.get('vs_r_woba', 0.320)) / 2
            else:
                # Hitter stats - check if they exist
                player.woba = sim_player.get('woba', 0.320)
                player.iso = sim_player.get('iso', 0.150)
                player.barrel_rate = sim_player.get('barrel_rate', 8.0)
                player.hard_hit_rate = sim_player.get('hard_hit_rate', 35.0)
                player.k_rate = sim_player.get('k_rate', 22.0)
            
            # Use ACTUAL projections from simulator!
            player.fantasy_points = sim_player.get('projection', 10.0)
            player.dff_projection = player.fantasy_points
            player.fpts = player.fantasy_points
            
            # Additional rich data from simulator
            player.floor = sim_player.get('floor', player.fantasy_points * 0.7)
            player.ceiling = sim_player.get('ceiling', player.fantasy_points * 1.5)
            player.recent_form = sim_player.get('recent_avg', player.fantasy_points)
            player.consistency = sim_player.get('consistency', 50)
            player.woba = sim_player.get('woba', 0.320)
            player.iso = sim_player.get('iso', 0.150)
            player.barrel_rate = sim_player.get('barrel_rate', 8.0)
            player.hard_hit_rate = sim_player.get('hard_hit_rate', 35.0)
            player.k_rate = sim_player.get('k_rate', 22.0)

            if player.primary_position == 'P':
                player.era = sim_player.get('era', 4.00)
                player.whip = sim_player.get('whip', 1.25)
                player.k9 = sim_player.get('k9', 9.0)

            players.append(player)

        # Initialize YOUR system
        system = UnifiedCoreSystem()
        system.players = players
        system.csv_loaded = True  # Mark as loaded since we're bypassing CSV

        # Build and enrich pool
        system.build_player_pool(include_unconfirmed=True)
        system.enrich_player_pool()
        
        # RESTORE simulator ownership after enrichment
        for p in system.player_pool:
            if hasattr(p, '_simulator_ownership'):
                p.ownership_projection = p._simulator_ownership

        # Score players with YOUR enhanced scoring engine
        system.score_players(contest_type)

        # Optimize with YOUR MILP optimizer
        # This DOES use your UnifiedMILPOptimizer internally!
        lineups = system.optimize_lineups(
            num_lineups=1,
            strategy=strategy_config,
            contest_type=contest_type
        )

        if not lineups:
            return None

        our_lineup = lineups[0]

        # Simulate contest
        field_lineups = generate_field(slate, 99, contest_type)
        # Convert lineup to simulator format
        sim_lineup = {
            'projection': our_lineup.get('total_score', 0),
            'players': []
        }
        
        # Convert players to simulator format
        for player in our_lineup['players']:
            sim_player = {
                'name': player.name,
                'position': player.primary_position,
                'team': player.team,
                'salary': player.salary,
                'projection': getattr(player, 'fantasy_points', 0),
                'ownership': getattr(player, 'ownership_projection', 15)
            }
            sim_lineup['players'].append(sim_player)
        
        our_score = simulate_lineup_score(sim_lineup)
        field_scores = [simulate_lineup_score(l) for l in field_lineups]

        # Calculate results
        all_scores = field_scores + [our_score]
        all_scores.sort(reverse=True)
        our_rank = all_scores.index(our_score) + 1

        # Calculate ROI
        if contest_type == 'cash':
            cash_line = all_scores[int(len(all_scores) * 0.44)]
            win = our_score >= cash_line
            roi = 100 if win else -100
        else:  # GPP
            if our_rank == 1:
                roi = 900
            elif our_rank <= 3:
                roi = 400
            elif our_rank <= 10:
                roi = 100
            elif our_rank <= 20:
                roi = -50
            else:
                roi = -100
            win = our_rank <= 20

        # Collect data for each player
        player_data = []
        for player in our_lineup['players']:
            player_data.append({
                'slate_id': slate_id,
                'strategy': strategy_config,
                'contest_type': contest_type,
                'slate_size': slate_size,

                # Player features
                'name': player.name,
                'position': player.primary_position,
                'salary': player.salary,
                'dk_projection': getattr(player, 'dff_projection', getattr(player, 'fantasy_points', 0)),
                'enhanced_score': player.enhanced_score,
                'cash_score': getattr(player, 'cash_score', 0),
                'gpp_score': getattr(player, 'gpp_score', 0),
                'batting_order': getattr(player, 'batting_order', 0),
                'team_total': getattr(player, 'implied_team_score', 4.5),
                'ownership': getattr(player, 'ownership_projection', 15),
                'barrel_rate': getattr(player, 'barrel_rate', 8.0),

                # Results
                'lineup_predicted': our_lineup['total_score'],
                'lineup_actual': our_score,
                'lineup_error': our_score - our_lineup['total_score'],
                'lineup_rank': our_rank,
                'lineup_win': win,
                'lineup_roi': roi
            })

        # Ensure we have valid data
        if not player_data:
            print(f"Warning: No player data for slate {slate_id}")
            return None
            
        return {
            'success': True,
            'player_data': player_data,
            'performance': {
                'strategy': strategy_config,
                'contest_type': contest_type,
                'win': win,
                'roi': roi,
                'rank': our_rank,
                'score': our_score,
                'predicted': our_lineup['total_score'],
                'error': abs(our_score - our_lineup['total_score']),
                'top_10': our_rank <= 10
            }
        }

    except Exception as e:
        import traceback
        print(f"\nError processing slate {slate_id}: {e}")
        print(f"Error type: {type(e).__name__}")
        print("Traceback:")
        traceback.print_exc()
        return None


class ParallelYourSystemMLBridge:
    """Parallel version with progress tracking"""

    def __init__(self, num_cores=None):
        self.num_cores = num_cores or mp.cpu_count()
        self.strategy_selector = StrategyAutoSelector()

    def run_parallel_test(self, num_slates_per_config: int = 100):
        """Run comprehensive test with parallel processing"""

        print("\n" + "=" * 80)
        print("🚀 PARALLEL ML BRIDGE - TESTING YOUR SYSTEM")
        print("=" * 80)
        print(f"\n⚡ Parallel Processing Configuration:")
        print(f"   • CPU cores available: {mp.cpu_count()}")
        print(f"   • Cores to use: {self.num_cores}")
        print(f"   • Slates per strategy: {num_slates_per_config}")

        # Get your strategies
        strategies = []
        for slate_size in ['small', 'medium', 'large']:
            strategies.append({
                'name': self.strategy_selector.top_strategies['cash'][slate_size],
                'contest_type': 'cash',
                'slate_size': slate_size
            })
            strategies.append({
                'name': self.strategy_selector.top_strategies['gpp'][slate_size],
                'contest_type': 'gpp',
                'slate_size': slate_size
            })

        print(f"\n📋 Testing {len(strategies)} strategies:")
        for s in strategies:
            print(f"   • {s['name']} ({s['contest_type'].upper()}, {s['slate_size']})")

        print(f"\n🎯 CONFIRMING: This DOES use your MILP optimizer!")
        print(f"   When optimize_lineups() is called, it uses UnifiedMILPOptimizer")
        print(f"   with all your constraints and optimization logic\n")

        start_time = time.time()
        all_results = []

        # Process each strategy
        for strategy in strategies:
            print(f"\n{'=' * 60}")
            print(f"Testing: {strategy['name']} ({strategy['contest_type'].upper()}, {strategy['slate_size']})")
            print(f"{'=' * 60}")

            # Create tasks for parallel processing
            tasks = []
            for i in range(num_slates_per_config):
                slate_id = i + hash(strategy['name']) % 10000
                tasks.append((
                    slate_id,
                    strategy['name'],
                    strategy['contest_type'],
                    strategy['slate_size']
                ))

            # Process in parallel
            with mp.Pool(self.num_cores) as pool:
                # Show progress
                results = []
                for i, result in enumerate(pool.imap(process_single_slate, tasks)):
                    if i % 10 == 0:
                        print(f"\r   Progress: {i}/{num_slates_per_config} slates",
                              end="", flush=True)
                    if result:
                        results.append(result)

                all_results.extend(results)

            # Print strategy summary
            self._print_strategy_performance(results, strategy['name'])

        # Save results
        self._save_all_results(all_results)

        total_time = time.time() - start_time
        print(f"\n\n✅ Complete! Total time: {total_time:.1f} seconds")
        print(f"   Processing rate: {len(all_results) / total_time:.1f} slates/second")

    def _print_strategy_performance(self, results: List[Dict], strategy_name: str):
        """Print performance for a strategy"""
        if not results:
            return

        perfs = [r['performance'] for r in results if r and 'performance' in r]
        if not perfs:
            return

        wins = sum(1 for p in perfs if p['win'])
        total = len(perfs)
        win_rate = (wins / total) * 100 if total > 0 else 0

        avg_roi = sum(p['roi'] for p in perfs) / total
        avg_error = sum(p['error'] for p in perfs) / total

        if perfs[0]['contest_type'] == 'gpp':
            top_10s = sum(1 for p in perfs if p['top_10'])
            top_10_rate = (top_10s / total) * 100
            print(f"\n\n📊 {strategy_name} Results:")
            print(f"   • Contests: {total}")
            print(f"   • Top 10%: {top_10_rate:.1f}%")
            print(f"   • ROI: {avg_roi:+.1f}%")
            print(f"   • Avg Error: {avg_error:.1f} points")
        else:
            print(f"\n\n📊 {strategy_name} Results:")
            print(f"   • Contests: {total}")
            print(f"   • Win Rate: {win_rate:.1f}%")
            print(f"   • ROI: {avg_roi:+.1f}%")
            print(f"   • Avg Error: {avg_error:.1f} points")

    def _save_all_results(self, all_results: List[Dict]):
        """Save all results to CSV"""
        if not all_results:
            return

        # Extract player data
        all_player_data = []
        seen_lineups = set()
        
        for result in all_results:
            if result and 'player_data' in result:
                # Create unique key for this lineup
                lineup_key = None
                if result['player_data']:
                    first_record = result['player_data'][0]
                    lineup_key = (
                        first_record['slate_id'],
                        first_record['strategy'],
                        first_record['contest_type']
                    )
                
                # Only add if we haven't seen this lineup
                if lineup_key and lineup_key not in seen_lineups:
                    seen_lineups.add(lineup_key)
                    all_player_data.extend(result['player_data'])

        if all_player_data:
            df = pd.DataFrame(all_player_data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'parallel_ml_training_data_{timestamp}.csv'
            df.to_csv(filename, index=False)
            print(f"\n\n💾 Training data saved to: {filename}")
            print(f"   Total records: {len(df)}")
            print(f"   Unique slates: {df['slate_id'].nunique()}")


# Main execution
if __name__ == "__main__":
    print("""
    ⚡ PARALLEL ML BRIDGE FOR YOUR SYSTEM
    =====================================

    This uses PARALLEL PROCESSING to test YOUR strategies:
    - Uses YOUR UnifiedCoreSystem
    - Uses YOUR EnhancedScoringEngine  
    - Uses YOUR UnifiedMILPOptimizer (YES, it does!)
    - Runs on multiple CPU cores for speed

    Options:
    1. Quick test (10 slates per strategy)
    2. Standard test (50 slates per strategy)
    3. Comprehensive test (100 slates per strategy)
    4. Extended test (500 slates per strategy)
    5. MASSIVE test (1000 slates per strategy) ← NEW!
    """)

    choice = input("\nSelect option (1-5): ")

    # Ask about cores
    max_cores = mp.cpu_count()
    core_input = input(f"\nHow many CPU cores to use? (1-{max_cores}, default={max_cores}): ")
    num_cores = int(core_input) if core_input.isdigit() else max_cores

    bridge = ParallelYourSystemMLBridge(num_cores=min(num_cores, max_cores))

    slates_map = {
        '1': 10,
        '2': 50,
        '3': 100,
        '4': 500,
        '5': 1000  # NEW option!
    }

    if choice in slates_map:
        bridge.run_parallel_test(slates_map[choice])
    else:
        print("Invalid choice!")