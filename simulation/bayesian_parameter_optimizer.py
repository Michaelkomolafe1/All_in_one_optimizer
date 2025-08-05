#!/usr/bin/env python3
"""
BAYESIAN PARAMETER OPTIMIZER
============================
Finds robust parameters for YOUR actual strategies using Bayesian optimization
"""

import numpy as np
from skopt import gp_minimize
from skopt.space import Real, Integer
from skopt.utils import use_named_args
import json
import time
from datetime import datetime
import sys
import os
from collections import defaultdict
import multiprocessing as mp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import YOUR components
from simulation.robust_dfs_simulator import generate_slate, simulate_lineup_score, generate_field
from main_optimizer.unified_core_system import UnifiedCoreSystem
from main_optimizer.unified_player_model import UnifiedPlayer


class BayesianParameterOptimizer:
    """
    Bayesian optimizer for YOUR strategies
    Focuses on finding robust parameters that work 90%+ of the time
    """

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.test_results = []

        # Define search spaces for YOUR strategies
        self.search_spaces = {
            'projection_monster': {
                'dimensions': [
                    Real(0.0, 1.5, name='park_weight'),
                    Real(0.0, 1.0, name='value_bonus_weight'),
                    Integer(6, 12, name='min_projection_threshold'),
                    Real(0.0, 1.0, name='pitcher_park_weight')
                ],
                'defaults': {
                    'projection_floor': 0.8,
                    'hitter_value_exp': 1.0
                }
            },
            'pitcher_dominance': {
                'dimensions': [
                    Real(2.5, 4.0, name='elite_k_bb_threshold'),
                    Real(1.3, 2.0, name='elite_multiplier'),
                    Real(0.4, 0.8, name='floor_weight'),
                    Real(0.0, 0.4, name='consistency_bonus')
                ],
                'defaults': {
                    'min_k_rate': 15,
                    'good_k_bb_threshold': 2.5,
                    'good_multiplier': 1.3,
                    'bad_multiplier': 0.9,
                    'whip_impact': 0.3
                }
            },
            'correlation_value': {
                'dimensions': [
                    Real(9.0, 10.0, name='high_total_threshold'),
                    Real(1.3, 1.7, name='high_game_multiplier'),
                    Real(3.5, 4.0, name='value_threshold'),
                    Real(1.3, 1.5, name='value_bonus'),
                    Real(0.3, 0.5, name='correlation_weight'),
                    Integer(15, 20, name='ownership_threshold'),
                    Real(0.7, 0.9, name='ownership_penalty')
                ],
                'defaults': {
                    'med_total_threshold': 8.0,
                    'med_game_multiplier': 1.1,
                    'low_game_multiplier': 0.9
                }
            },
            'truly_smart_stack': {
                'dimensions': [
                    Real(0.15, 0.35, name='projection_weight'),
                    Real(0.15, 0.35, name='ceiling_weight'),
                    Real(0.15, 0.35, name='matchup_weight'),
                    Real(0.15, 0.35, name='game_total_weight'),
                    Integer(3, 5, name='min_stack_size'),
                    Real(4.0, 5.5, name='bad_pitcher_era'),
                    Real(1.1, 1.6, name='stack_correlation_mult'),
                    Real(1.2, 1.8, name='bad_pitcher_mult')
                ],
                'defaults': {
                    'max_stack_size': 6,
                    'min_game_total': 8.0,
                    'hot_team_mult': 1.2,
                    'allow_mini_stacks': 1,
                    'cross_game_correlation': 0.2
                }
            },
            'matchup_leverage_stack': {
                'dimensions': [
                    Integer(3, 4, name='num_worst_pitchers'),
                    Real(1.8, 2.2, name='stack_multiplier'),
                    Real(0.2, 0.4, name='ownership_leverage'),
                    Real(0.7, 0.9, name='pitcher_leverage_mult')
                ],
                'defaults': {
                    'era_threshold': 5.0,
                    'whip_threshold': 1.4,
                    'k_rate_threshold': 18,
                    'correlation_bonus': 1.2,
                    'weather_boost': 0.2,
                    'park_boost': 0.2
                }
            }
        }

    def test_parameters(self, strategy: str, params: dict, contest_type: str,
                        slate_size: str, num_slates: int = 10) -> dict:
        """Test a parameter set on multiple slates"""

        wins = 0
        total_roi = 0
        scores = []

        for i in range(num_slates):
            slate_id = i * 1000 + hash(f"{strategy}_{slate_size}") % 1000

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

                # Copy attributes
                for attr in ['matchup_score', 'park_factor', 'weather_score',
                             'recent_performance', 'consistency_score', 'ownership',
                             'batting_order', 'game_total', 'team_total']:
                    if attr in sim_player:
                        setattr(player, attr, sim_player[attr])

                player.is_pitcher = (player.primary_position == 'P')
                player.implied_team_score = sim_player.get('team_total', 4.5)
                player.projected_ownership = sim_player.get('ownership', 15)

                players.append(player)

            # Apply strategy with parameters
            try:
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

                # Build lineup using YOUR system
                system = UnifiedCoreSystem()
                system.players = players
                system.csv_loaded = True

                # Optimize
                from main_optimizer.unified_milp_optimizer import UnifiedMILPOptimizer
                optimizer = UnifiedMILPOptimizer(players, contest_type=contest_type)
                lineups = optimizer.optimize(num_lineups=1)

                if lineups:
                    lineup = lineups[0]

                    # Convert back to sim format and score
                    sim_lineup = []
                    for p in lineup['players']:
                        sim_p = next((sp for sp in slate['players'] if sp['name'] == p.name), None)
                        if sim_p:
                            sim_lineup.append(sim_p)

                    score = simulate_lineup_score(sim_lineup)
                    scores.append(score)

                    # Simple win calculation
                    if contest_type == 'cash':
                        win = score > 150  # Arbitrary threshold
                    else:
                        win = score > 180

                    if win:
                        wins += 1
                        total_roi += 100
                    else:
                        total_roi -= 100

            except Exception as e:
                if self.verbose:
                    print(f"    Error: {e}")
                continue

        # Calculate results
        if scores:
            success_rate = wins / len(scores)
            avg_roi = total_roi / len(scores)
            avg_score = np.mean(scores)
        else:
            success_rate = 0
            avg_roi = -100
            avg_score = 0

        return {
            'success_rate': success_rate,
            'avg_roi': avg_roi,
            'avg_score': avg_score,
            'num_valid': len(scores)
        }

    def optimize_strategy_bayesian(self, strategy: str, contest_type: str,
                                   slate_size: str, n_calls: int = 35,
                                   slates_per_test: int = 10):
        """Find optimal parameters using Bayesian optimization"""

        if strategy not in self.search_spaces:
            print(f"Strategy {strategy} not configured for optimization")
            return None

        print(f"\n🔬 Bayesian optimization for {strategy} ({contest_type}, {slate_size})")
        print(f"   Testing {n_calls} parameter combinations...")

        config = self.search_spaces[strategy]
        dimensions = config['dimensions']
        defaults = config['defaults']

        best_score = -float('inf')
        best_params = None

        # Objective function
        def objective(values):
            # Build parameter dict
            params = defaults.copy()
            for i, dim in enumerate(dimensions):
                params[dim.name] = values[i]

            # Normalize weights if needed (for truly_smart_stack)
            if strategy == 'truly_smart_stack':
                weight_keys = ['projection_weight', 'ceiling_weight',
                               'matchup_weight', 'game_total_weight']
                total_weight = sum(params[k] for k in weight_keys)
                for k in weight_keys:
                    params[k] = params[k] / total_weight

            # Test parameters
            result = self.test_parameters(
                strategy, params, contest_type, slate_size, slates_per_test
            )

            # Score based on success rate and ROI
            # Prioritize robustness (success rate) over pure ROI
            score = (result['success_rate'] * 100 * 0.7) + (result['avg_roi'] * 0.3)

            # Track best
            nonlocal best_score, best_params
            if score > best_score:
                best_score = score
                best_params = params.copy()
                if self.verbose:
                    print(f"   📈 New best: {result['success_rate'] * 100:.0f}% success, "
                          f"{result['avg_roi']:.1f}% ROI")

            return -score  # Minimize negative score

        # Run optimization
        try:
            result = gp_minimize(
                func=objective,
                dimensions=dimensions,
                n_calls=n_calls,
                n_initial_points=10,
                acq_func='EI',
                random_state=42,
                verbose=False
            )

            # Return best parameters
            return {
                'strategy': strategy,
                'contest_type': contest_type,
                'slate_size': slate_size,
                'params': best_params,
                'score': best_score,
                'success_rate': best_score * 0.7 / 100,  # Approximate
                'win_rate': best_score * 0.7 / 100,  # For compatibility
                'avg_roi': (best_score - best_score * 0.7) / 0.3  # Approximate
            }

        except Exception as e:
            print(f"   ❌ Optimization failed: {e}")
            return None

    def run_full_optimization(self, strategies_to_test=None):
        """Run optimization for multiple strategies"""

        if strategies_to_test is None:
            strategies_to_test = [
                ('projection_monster', 'cash', 'small'),
                ('projection_monster', 'cash', 'medium'),
                ('pitcher_dominance', 'cash', 'medium'),
                ('correlation_value', 'gpp', 'small'),
                ('truly_smart_stack', 'gpp', 'medium'),
                ('matchup_leverage_stack', 'gpp', 'large')
            ]

        print("\n" + "=" * 60)
        print("🚀 BAYESIAN PARAMETER OPTIMIZATION")
        print("=" * 60)

        all_results = {}

        for strategy, contest_type, slate_size in strategies_to_test:
            result = self.optimize_strategy_bayesian(
                strategy, contest_type, slate_size
            )

            if result:
                key = f"{strategy}_{contest_type}_{slate_size}"
                all_results[key] = result

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save detailed results
        with open(f'bayesian_optimal_params_{timestamp}.json', 'w') as f:
            json.dump(all_results, f, indent=2)

        # Print summary
        print("\n" + "=" * 60)
        print("📊 OPTIMIZATION SUMMARY")
        print("=" * 60)

        for key, result in all_results.items():
            print(f"\n{key}:")
            print(f"  Success rate: {result['win_rate'] * 100:.1f}%")
            print(f"  ROI: {result['avg_roi']:.1f}%")
            print(f"  Key params:")
            for param, value in list(result['params'].items())[:4]:
                if isinstance(value, float):
                    print(f"    {param}: {value:.3f}")
                else:
                    print(f"    {param}: {value}")

        return all_results


if __name__ == "__main__":
    print("""
    🔬 BAYESIAN PARAMETER OPTIMIZER
    ===============================

    This finds robust parameters for YOUR strategies using
    Bayesian optimization (Gaussian Process).

    Benefits over grid search:
    • Smarter exploration of parameter space
    • Finds good parameters in fewer tests
    • Focuses on robustness (90%+ success rate)

    Options:
    1. Quick test (20 iterations per strategy)
    2. Standard test (35 iterations per strategy)
    3. Thorough test (50 iterations per strategy)
    4. Single strategy test
    """)

    choice = input("\nSelect option (1-4): ")

    optimizer = BayesianParameterOptimizer()

    if choice in ['1', '2', '3']:
        n_calls_map = {'1': 20, '2': 35, '3': 50}
        n_calls = n_calls_map[choice]

        # Modify optimizer settings
        results = optimizer.run_full_optimization()

        print("\n✅ Optimization complete!")
        print("Check the generated JSON file for optimal parameters.")

    elif choice == '4':
        # Single strategy test
        print("\nAvailable strategies:")
        strategies = list(optimizer.search_spaces.keys())
        for i, s in enumerate(strategies, 1):
            print(f"{i}. {s}")

        strat_choice = input("\nSelect strategy (1-5): ")
        if strat_choice.isdigit() and 1 <= int(strat_choice) <= len(strategies):
            strategy = strategies[int(strat_choice) - 1]

            contest_type = 'cash' if 'monster' in strategy or 'dominance' in strategy else 'gpp'

            result = optimizer.optimize_strategy_bayesian(
                strategy, contest_type, 'medium', n_calls=35
            )

            if result:
                print(f"\n✅ Optimal parameters for {strategy}:")
                for param, value in result['params'].items():
                    if isinstance(value, float):
                        print(f"  {param}: {value:.3f}")
                    else:
                        print(f"  {param}: {value}")