"""
DFS Strategy Parameter Optimization Framework
============================================
Efficiently test parameter combinations for all strategies
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import multiprocessing as mp
from itertools import product
import json
from typing import Dict, List, Tuple, Any
import time

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components - CORRECTED PATHS
from main_optimizer.unified_core_system import UnifiedCoreSystem
from main_optimizer.strategy_selector import StrategyAutoSelector
from main_optimizer.unified_player_model import UnifiedPlayer
from simulation.robust_dfs_simulator import generate_slate, simulate_lineup_score, generate_field
class ParameterOptimizer:
    """
    Comprehensive parameter testing framework
    """

    def __init__(self, num_cores=None):
        self.num_cores = num_cores or mp.cpu_count()
        self.results = []

        # Define parameter grids for each strategy
        self.parameter_grids = {
            'projection_monster': {
                'park_weight': [0.0, 0.3, 0.5, 0.7, 1.0, 1.5],
                'value_bonus_weight': [0.0, 0.2, 0.5, 0.7, 1.0],
                'min_projection_threshold': [6, 8, 10, 12],
                'pitcher_park_weight': [0.0, 0.5, 1.0],
                'projection_floor': [0.8],  # ADD THIS - just use default
                'hitter_value_exp': [1.0]  # ADD THIS - just use default
            },
            'pitcher_dominance': {
                'elite_k_bb_threshold': [2.5, 3.0, 3.5, 4.0],
                'elite_multiplier': [1.3, 1.5, 1.7, 2.0],
                'floor_weight': [0.4, 0.6, 0.8],
                'consistency_bonus': [0.0, 0.2, 0.4],
                'min_k_rate': [15],  # ADD THIS - just use default
                'good_k_bb_threshold': [2.5],  # ADD THIS
                'good_multiplier': [1.3],  # ADD THIS
                'bad_multiplier': [0.9],  # ADD THIS
                'whip_impact': [0.3]  # ADD THIS
            },
            'correlation_value': {
                'high_total_threshold': [9.0, 9.5, 10.0],
                'high_game_multiplier': [1.3, 1.5, 1.7],
                'value_threshold': [3.5, 4.0],
                'value_bonus': [1.3, 1.5],
                'correlation_weight': [0.3, 0.4, 0.5],
                'ownership_threshold': [15, 20],
                'ownership_penalty': [0.7, 0.8, 0.9],
                # Add the missing ones with single values
                'med_total_threshold': [8.0],
                'med_game_multiplier': [1.1],
                'low_game_multiplier': [0.9]
            },
            'truly_smart_stack': {
                # These are fine - keep as is
                'projection_weight': [0.2, 0.25, 0.3],
                'ceiling_weight': [0.2, 0.25, 0.3],
                'matchup_weight': [0.2, 0.25, 0.3],
                'game_total_weight': [0.2, 0.25, 0.3],
                'min_stack_size': [3, 4, 5],
                'bad_pitcher_era': [4.0, 4.5, 5.0],
                'max_stack_size': [6],  # ADD THIS
                'min_game_total': [8.0],  # ADD THIS
                'stack_correlation_mult': [1.3],  # ADD THIS
                'bad_pitcher_mult': [1.4],  # ADD THIS
                'hot_team_mult': [1.2],  # ADD THIS
                'allow_mini_stacks': [1],  # ADD THIS
                'cross_game_correlation': [0.2]  # ADD THIS
            },
            'matchup_leverage_stack': {
                'num_worst_pitchers': [3, 4],
                'era_threshold': [5.0],
                'whip_threshold': [1.4],
                'k_rate_threshold': [18],
                'stack_multiplier': [1.8, 2.0],
                'correlation_bonus': [1.2],
                'ownership_leverage': [0.3],
                'pitcher_leverage_mult': [0.8],
                'weather_boost': [0.2],
                'park_boost': [0.2]
            }
        }

    def generate_parameter_combinations(self, strategy: str) -> List[Dict]:
        """Generate all parameter combinations for a strategy"""
        grid = self.parameter_grids.get(strategy, {})

        if not grid:
            return [{}]  # Return default params

        # Create all combinations
        keys = list(grid.keys())
        values = list(grid.values())

        combinations = []
        for combo in product(*values):
            param_dict = dict(zip(keys, combo))

            # Special validation for truly_smart_stack weights
            if strategy == 'truly_smart_stack':
                total_weight = sum([
                    param_dict['projection_weight'],
                    param_dict['ceiling_weight'],
                    param_dict['matchup_weight'],
                    param_dict['game_total_weight']
                ])
                # Normalize weights to sum to 1.0
                if total_weight > 0:
                    for key in ['projection_weight', 'ceiling_weight', 'matchup_weight', 'game_total_weight']:
                        param_dict[key] = param_dict[key] / total_weight

            combinations.append(param_dict)

        return combinations

    def test_single_configuration(self, args: Tuple) -> Dict:
        """Test a single parameter configuration"""
        strategy, params, contest_type, slate_size, num_slates = args

        wins = 0
        total_roi = 0
        scores = []

        # Test on multiple slates
        for i in range(num_slates):
            slate_id = 10000 + i  # Unique slate IDs

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
                        positions=[sim_player['position']],
                        base_projection=sim_player.get('projection', 0)
                    )

                    # Add all simulator attributes
                    for attr in ['ownership', 'recent_performance', 'matchup_score',
                                 'hitting_matchup', 'pitching_matchup', 'park_factor',
                                 'weather_score', 'vegas_score', 'correlation_score',
                                 'era', 'whip', 'k_rate', 'bb_rate', 'batting_order',
                                 'game_total', 'team_total', 'opponent']:
                        if attr in sim_player:
                            setattr(player, attr, sim_player[attr])

                    # Set derived attributes
                    player.is_pitcher = (player.primary_position == 'P')
                    player.implied_team_score = sim_player.get('team_total', 4.5)
                    player.recent_form = sim_player.get('recent_performance', 1.0)
                    player.projected_ownership = sim_player.get('ownership', 15)

                    players.append(player)

                    # Apply strategy with parameters
                    if strategy == 'projection_monster':
                        from main_optimizer.cash_strategies import build_projection_monster
                        players = build_projection_monster(players, params)
                    elif strategy == 'pitcher_dominance':
                        from main_optimizer.cash_strategies import build_pitcher_dominance
                        players = build_pitcher_dominance(players, params)
                    elif strategy == 'correlation_value':
                        from main_optimizer.gpp_strategies import build_correlation_value
                        players = build_correlation_value(players, params)
                    elif strategy == 'truly_smart_stack':
                        from main_optimizer.gpp_strategies import build_truly_smart_stack
                        players = build_truly_smart_stack(players, params)
                    elif strategy == 'matchup_leverage_stack':
                        from main_optimizer.gpp_strategies import build_matchup_leverage_stack
                        players = build_matchup_leverage_stack(players, params)

                # Initialize system
                system = UnifiedCoreSystem()
                system.players = players
                system.csv_loaded = True
                system.enrichments_applied = True  # Mark enrichments as done

                # Build and score
                system.build_player_pool(include_unconfirmed=True)
                system.player_pool = players  # Use our scored players

                # Optimize
                lineups = system.optimize_lineups(
                    num_lineups=1,
                    strategy=strategy,
                    contest_type=contest_type
                )

                if lineups and lineups[0]:
                    lineup = lineups[0]

                    # Convert YOUR lineup to simulator format
                    sim_lineup = {
                        'projection': lineup.get('total_projection', 0),  # FIX: Use total_projection
                        'salary': lineup.get('total_salary', 0),
                        'players': [{'id': p.id} for p in lineup['players']]
                    }


                    # Simulate score
                    actual_score = simulate_lineup_score(sim_lineup)

                    # Generate field and calculate placement
                    field = generate_field(slate, 100, contest_type)  # FIX: Correct parameter order
                    field_scores = [simulate_lineup_score(lu) for lu in field]
                    field_scores.append(actual_score)
                    field_scores.sort(reverse=True)

                    rank = field_scores.index(actual_score) + 1
                    percentile = (100 - rank) / 100

                    # Calculate win/ROI
                    if contest_type == 'cash':
                        win = rank <= 44
                        roi = 80 if win else -100
                    else:
                        if rank == 1:
                            roi = 900
                        elif rank <= 3:
                            roi = 400
                        elif rank <= 10:
                            roi = 100
                        elif rank <= 20:
                            roi = 0
                        else:
                            roi = -100
                        win = rank <= 20

                    wins += win
                    total_roi += roi
                    scores.append(actual_score)

            except Exception as e:
                print(f"Error testing {strategy} with {params}: {e}")
                continue

        # Calculate averages
        if num_slates > 0:
            win_rate = wins / num_slates
            avg_roi = total_roi / num_slates
            avg_score = np.mean(scores) if scores else 0
        else:
            win_rate = avg_roi = avg_score = 0

        return {
            'strategy': strategy,
            'params': params,
            'contest_type': contest_type,
            'slate_size': slate_size,
            'win_rate': win_rate,
            'avg_roi': avg_roi,
            'avg_score': avg_score,
            'num_slates': len(scores)
        }

    def optimize_strategy(self, strategy: str, contest_type: str,
                          slate_size: str, slates_per_config: int = 20):
        """Find optimal parameters for a specific strategy"""

        print(f"\n🔧 Optimizing {strategy} for {slate_size} {contest_type}")
        print(f"   Testing {len(self.parameter_grids.get(strategy, {}))} parameters")

        # Generate all parameter combinations
        param_combos = self.generate_parameter_combinations(strategy)
        print(f"   Total combinations: {len(param_combos)}")

        # Create tasks
        tasks = [
            (strategy, params, contest_type, slate_size, slates_per_config)
            for params in param_combos
        ]

        # Run in parallel
        results = []
        with mp.Pool(self.num_cores) as pool:
            for i, result in enumerate(pool.imap_unordered(self.test_single_configuration, tasks)):
                results.append(result)
                if i % 10 == 0:
                    print(f"\r   Progress: {i + 1}/{len(tasks)}", end="", flush=True)

        print(f"\n   ✅ Tested {len(results)} configurations")

        # Sort by performance
        if contest_type == 'cash':
            results.sort(key=lambda x: x['win_rate'], reverse=True)
        else:
            results.sort(key=lambda x: x['avg_roi'], reverse=True)

        # Show top 5
        print(f"\n   Top 5 configurations:")
        for i, result in enumerate(results[:5]):
            if contest_type == 'cash':
                print(f"   {i + 1}. Win Rate: {result['win_rate'] * 100:.1f}% | ROI: {result['avg_roi']:.1f}%")
            else:
                print(f"   {i + 1}. ROI: {result['avg_roi']:.1f}% | Win Rate: {result['win_rate'] * 100:.1f}%")
            print(f"      Params: {json.dumps(result['params'], indent=8)}")

        # Store results
        self.results.extend(results)

        return results[0] if results else None

    def run_full_optimization(self, slates_per_config: int = 20):
        """Run optimization for all strategies"""

        print("\n" + "=" * 80)
        print("🚀 DFS STRATEGY PARAMETER OPTIMIZATION")
        print("=" * 80)

        # Define what to test
        test_configs = [
            ('projection_monster', 'cash', 'small'),
            ('pitcher_dominance', 'cash', 'medium'),
            ('pitcher_dominance', 'cash', 'large'),
            ('correlation_value', 'gpp', 'small'),
            ('truly_smart_stack', 'gpp', 'medium'),
            ('matchup_leverage_stack', 'gpp', 'large'),
        ]

        start_time = time.time()
        best_configs = {}

        for strategy, contest_type, slate_size in test_configs:
            best = self.optimize_strategy(strategy, contest_type, slate_size, slates_per_config)
            if best:
                key = f"{strategy}_{contest_type}_{slate_size}"
                best_configs[key] = best

        # Save results
        self._save_results(best_configs)

        elapsed = time.time() - start_time
        print(f"\n✅ Optimization complete in {elapsed / 60:.1f} minutes")

        return best_configs

    def _save_results(self, best_configs: Dict):
        """Save optimization results"""

        # Save detailed results
        df = pd.DataFrame(self.results)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        df.to_csv(f'parameter_optimization_results_{timestamp}.csv', index=False)

        # Save best configurations
        with open(f'optimal_parameters_{timestamp}.json', 'w') as f:
            json.dump(best_configs, f, indent=2)

        print(f"\n💾 Results saved:")
        print(f"   • Detailed results: parameter_optimization_results_{timestamp}.csv")
        print(f"   • Optimal parameters: optimal_parameters_{timestamp}.json")

        # Print summary
        print("\n📊 OPTIMAL PARAMETERS SUMMARY:")
        print("=" * 60)

        for key, config in best_configs.items():
            print(f"\n{key}:")
            print(f"  Performance: {config['win_rate'] * 100:.1f}% wins, {config['avg_roi']:.1f}% ROI")
            print(f"  Parameters:")
            for param, value in config['params'].items():
                print(f"    {param}: {value}")


def estimate_runtime(num_strategies=6, avg_combos_per_strategy=50,
                     slates_per_config=20, cores=8):
    """Estimate how long the optimization will take"""

    total_tests = num_strategies * avg_combos_per_strategy
    total_slates = total_tests * slates_per_config

    # Assume ~0.5 seconds per slate on average
    seconds_per_slate = 0.5
    total_seconds = (total_slates * seconds_per_slate) / cores

    print(f"\n⏱️  RUNTIME ESTIMATE:")
    print(f"   • Strategies to test: {num_strategies}")
    print(f"   • Average parameter combos per strategy: {avg_combos_per_strategy}")
    print(f"   • Slates per configuration: {slates_per_config}")
    print(f"   • Total configurations: {total_tests}")
    print(f"   • Total slate simulations: {total_slates:,}")
    print(f"   • CPU cores: {cores}")
    print(f"   • Estimated time: {total_seconds / 60:.1f} minutes")

    return total_seconds


if __name__ == "__main__":
    print("""
    🔬 DFS STRATEGY PARAMETER OPTIMIZER
    ==================================

    This will test different parameter combinations for your strategies
    to find the optimal settings for each contest type and slate size.

    Options:
    1. Quick test (10 slates per config) - ~5 minutes
    2. Standard test (20 slates per config) - ~10 minutes  
    3. Thorough test (50 slates per config) - ~25 minutes
    4. Comprehensive test (100 slates per config) - ~50 minutes
    """)

    # Get user choice
    choice = input("\nSelect option (1-4): ")
    slates_map = {'1': 10, '2': 20, '3': 50, '4': 100}
    slates_per_config = slates_map.get(choice, 20)

    # Estimate runtime
    cores = mp.cpu_count()
    runtime = estimate_runtime(slates_per_config=slates_per_config, cores=cores)

    confirm = input(f"\nThis will take approximately {runtime / 60:.1f} minutes. Continue? (y/n): ")

    if confirm.lower() == 'y':
        optimizer = ParameterOptimizer(num_cores=cores)
        best_configs = optimizer.run_full_optimization(slates_per_config)

        print("\n🎯 OPTIMIZATION COMPLETE!")
        print("\nYour optimal parameters have been saved.")
        print("Update your strategies with these parameters for best performance!")
    else:
        print("\nOptimization cancelled.")