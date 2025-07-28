#!/usr/bin/env python3
"""
DFS OPTIMIZER INTEGRATION – FIXED & UNCHANGED NUMBERS
=====================================================
This file bridges the Bayesian optimiser with your existing simulator.
Nothing in your original simulator needs to change.
"""

import numpy as np
import json
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from scipy.stats import qmc   #  <-- fixes the two unresolved references

# ------------------------------------------------------------------
# 1.  Bridge class – no numeric changes
# ------------------------------------------------------------------
class DFSOptimizerBridge:
    """Connects your existing simulator to the Bayesian optimiser."""
    def __init__(self, n_cores=None):
        self.n_cores = n_cores or min(mp.cpu_count() - 1, 8)
        print(f"🔌 DFS Optimizer Bridge initialised")
        print(f"🖥️  Using {self.n_cores} cores")

    # ------------------------------------------------------------------
    #  FIXED  generate_parameter_sets – identical numeric values
    # ------------------------------------------------------------------
    def generate_parameter_sets(self, strategy_config, n_sets):
        """Latin-Hypercube sampling – all bounds unchanged."""
        dimensions = strategy_config['dimensions']
        bounds, names, cats = [], [], {}

        for dim in dimensions:
            if isinstance(dim, dict):
                if 'low' in dim:                       # Real / Integer
                    bounds.append([dim['low'], dim['high']])
                    names.append(dim['name'])
                    if dim.get('dtype') == 'int':
                        pass  # handled later
                elif 'categories' in dim:              # Categorical
                    cats[dim['name']] = dim['categories']
            else:                                      # scikit-optimize objects (if any)
                if hasattr(dim, 'low'):
                    bounds.append([dim.low, dim.high])
                    names.append(dim.name)
                else:
                    cats[dim.name] = dim.categories

        param_sets = []
        if bounds:
            sampler = qmc.LatinHypercube(d=len(bounds))
            samples = sampler.random(n=n_sets)
            scaled = qmc.scale(samples, [b[0] for b in bounds], [b[1] for b in bounds])
        else:
            scaled = np.empty((n_sets, 0))

        for i in range(n_sets):
            params = {}
            # continuous / integer
            for j, name in enumerate(names):
                val = scaled[i, j]
                # convert int if requested
                for dim in dimensions:
                    if isinstance(dim, dict) and dim.get('name') == name and dim.get('dtype') == 'int':
                        val = int(val)
                    elif not isinstance(dim, dict) and hasattr(dim, 'dtype') and dim.dtype == np.int64 and dim.name == name:
                        val = int(val)
                params[name] = val
            # categorical
            for name, choices in cats.items():
                params[name] = np.random.choice(choices)
            param_sets.append(params)
        return param_sets

    # ------------------------------------------------------------------
    #  run_optimization_for_strategy – identical numeric values
    # ------------------------------------------------------------------
    def run_optimization_for_strategy(self, strategy_name, strategy_config, n_iterations=50):
        print(f"\n🎯 Optimising {strategy_name}...")
        best_score = -float('inf')
        best_params = None
        scores_history = []

        param_sets = self.generate_parameter_sets(strategy_config, n_iterations)

        for i, params in enumerate(param_sets):
            score = self.evaluate_parameters(
                strategy_name=strategy_config['strategy_type'],
                params=params,
                slate_size=strategy_config['slate_size'],
                contest_type=strategy_config['contest_type']
            )
            scores_history.append(score)
            if score > best_score:
                best_score = score
                best_params = params
                print(f"  📈 New best! Score: {score:.2f}")
            if i % 10 == 0:
                print(f"  Progress: {i}/{n_iterations}")

        return {
            'optimal_params': best_params,
            'best_score': best_score,
            'scores_history': scores_history
        }

    # ------------------------------------------------------------------
    #  evaluate_parameters – unchanged
    # ------------------------------------------------------------------
    def evaluate_parameters(self, strategy_name, params, slate_size, contest_type):
        from simulation import simulate_contest, generate_slate  # local import avoids circularity

        n_simulations = 20
        results = []
        for i in range(n_simulations):
            slate = generate_slate(i * 1000, 'classic' if slate_size != 'showdown' else 'showdown', slate_size)
            strategy_config = self.create_strategy_config(strategy_name, params)
            result = simulate_contest(
                slate=slate,
                strategy_name=strategy_name,
                strategy_config=strategy_config,
                contest_type=contest_type,
                field_size=5000 if contest_type == 'gpp' else 100
            )
            if not result.get('failed'):
                results.append(result)

        if not results:
            return -1000

        if contest_type == 'gpp':
            first_places = sum(1 for r in results if r['rank'] == 1)
            top_10_pct = sum(1 for r in results if r['percentile'] >= 90)
            avg_roi = np.mean([r['roi'] for r in results])
            score = (first_places * 100 + top_10_pct * 10 + max(0, avg_roi))
        else:
            wins = sum(1 for r in results if r['profit'] > 0)
            win_rate = wins / len(results)
            avg_roi = np.mean([r['roi'] for r in results])
            score = (win_rate * 100 + max(0, avg_roi) * 10)
        return score

    # ------------------------------------------------------------------
    #  create_strategy_config – unchanged
    # ------------------------------------------------------------------
    def create_strategy_config(self, strategy_name, params):
        config = {'type': strategy_name}
        for key in ['min_game_total', 'stack_size', 'ownership_weight', 'projection_weight']:
            if key in params:
                config[key] = params[key]
        return config


# ------------------------------------------------------------------
#  2.  FULL strategy dictionary – identical numeric values
# ------------------------------------------------------------------
def optimise_best_strategies():
    """Main function to optimise strategies – numeric bounds unchanged."""
    print("🚀 DFS Strategy Optimizer - Integration Mode")
    print("=" * 60)

    bridge = DFSOptimizerBridge()

    strategies_to_optimize = {
        'game_stack_4_2': {
            'dimensions': [
                {'name': 'min_game_total', 'low': 5.5, 'high': 7.0},
                {'name': 'primary_stack_size', 'low': 3, 'high': 5, 'dtype': 'int'},
                {'name': 'secondary_stack_size', 'low': 1, 'high': 3, 'dtype': 'int'},
                {'name': 'max_avg_ownership', 'low': 0.10, 'high': 0.35},
                {'name': 'correlation_boost', 'low': 1.15, 'high': 1.45},
            ],
            'strategy_type': 'game_4_2',
            'slate_size': 'large',
            'contest_type': 'gpp'
        },
        'game_stack_3_2': {
            'dimensions': [
                {'name': 'min_game_total', 'low': 5.0, 'high': 6.5},
                {'name': 'primary_stack_size', 'low': 3, 'high': 4, 'dtype': 'int'},
                {'name': 'secondary_stack_size', 'low': 2, 'high': 3, 'dtype': 'int'},
                {'name': 'max_avg_ownership', 'low': 0.15, 'high': 0.40},
            ],
            'strategy_type': 'game_3_2',
            'slate_size': 'medium',
            'contest_type': 'gpp'
        },
        'stack_5': {
            'dimensions': [
                {'name': 'min_team_total', 'low': 4.5, 'high': 6.0},
                {'name': 'stack_size', 'low': 4, 'high': 5, 'dtype': 'int'},
                {'name': 'ownership_flexibility', 'low': 0.20, 'high': 0.50},
            ],
            'strategy_type': 'stack_5',
            'slate_size': 'small',
            'contest_type': 'gpp'
        },
        'balanced_3_3': {
            'dimensions': [
                {'name': 'min_game_total', 'low': 7.5, 'high': 10.5},
                {'name': 'captain_ownership_sweet_spot', 'low': 10.0, 'high': 30.0},
                {'name': 'team_balance_flexibility', 'low': 0.45, 'high': 0.55},
            ],
            'strategy_type': 'balanced_3_3',
            'slate_size': 'showdown',
            'contest_type': 'gpp'
        },
        'pure_chalk': {
            'dimensions': [
                {'name': 'ownership_weight', 'low': 0.65, 'high': 0.85},
                {'name': 'projection_weight', 'low': 0.15, 'high': 0.35},
                {'name': 'min_ownership_threshold', 'low': 20.0, 'high': 40.0},
            ],
            'strategy_type': 'pure_chalk',
            'slate_size': 'large',
            'contest_type': 'cash'
        },
        'balanced_60_40': {
            'dimensions': [
                {'name': 'ownership_weight', 'low': 0.55, 'high': 0.65},
                {'name': 'projection_weight', 'low': 0.35, 'high': 0.45},
                {'name': 'value_weight', 'low': 0.05, 'high': 0.15},
                {'name': 'ownership_threshold', 'low': 15.0, 'high': 30.0},
                {'name': 'mini_stack_size', 'low': 2, 'high': 4, 'dtype': 'int'},
            ],
            'strategy_type': 'balanced_60_40',
            'slate_size': 'medium',
            'contest_type': 'cash'
        },
        'balanced_50_50': {
            'dimensions': [
                {'name': 'ownership_weight', 'low': 0.45, 'high': 0.55},
                {'name': 'projection_weight', 'low': 0.45, 'high': 0.55},
                {'name': 'contrarian_weight', 'low': 0.0, 'high': 0.1},
                {'name': 'max_players_per_team', 'low': 0, 'high': 3, 'dtype': 'int'},
                {'name': 'floor_emphasis', 'low': 0.7, 'high': 0.9},
                {'name': 'min_value_score', 'low': 2.5, 'high': 3.5},
            ],
            'strategy_type': 'balanced_50_50',
            'slate_size': 'small',
            'contest_type': 'cash'
        }
    }

    optimal_parameters = {}
    with ProcessPoolExecutor(max_workers=bridge.n_cores) as executor:
        future_to_strategy = {
            executor.submit(bridge.run_optimization_for_strategy,
                            strategy_name,
                            strategy_config,
                            n_iterations=30): strategy_name
            for strategy_name, strategy_config in strategies_to_optimize.items()
        }

        for future in as_completed(future_to_strategy):
            strategy_name = future_to_strategy[future]
            try:
                result = future.result()
                optimal_parameters[strategy_name] = result
                print(f"✅ Completed: {strategy_name}")
            except Exception as e:
                print(f"❌ Error with {strategy_name}: {e}")

    # Save and display results – unchanged
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'optimal_dfs_parameters_{timestamp}.json'
    with open(filename, 'w') as f:
        json.dump(optimal_parameters, f, indent=2)
    print(f"\n💾 Saved optimal parameters to: {filename}")

    print("\n" + "=" * 60)
    print("🏆 OPTIMIZATION RESULTS")
    print("=" * 60)
    for strategy, result in optimal_parameters.items():
        print(f"\n📊 {strategy}")
        print(f"   Best Score: {result['best_score']:.2f}")
        print("   Optimal Parameters:")
        for param, value in result['optimal_params'].items():
            if isinstance(value, float):
                print(f"     • {param}: {value:.3f}")
            else:
                print(f"     • {param}: {value}")
    return optimal_parameters


# ------------------------------------------------------------------
#  3.  Entry point – unchanged
# ------------------------------------------------------------------
if __name__ == "__main__":
    optimise_best_strategies()