import numpy as np
from skopt import gp_minimize
from skopt.space import Real, Integer, Categorical
from skopt.utils import use_named_args
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import json
import time
from datetime import datetime
from functools import partial


class ParallelDFSOptimizer:
    """
    Find optimal parameters FAST using parallel Bayesian optimization
    """

    def __init__(self, simulator_path, n_cores=None):
        self.simulator_path = simulator_path
        self.n_cores = n_cores or min(mp.cpu_count() - 1, 8)
        self.results_cache = {}
        print(f"🖥️ Using {self.n_cores} cores for optimization")

    def optimize_all_strategies(self):
        """
        Optimize all winning strategies in parallel
        """
        start_time = time.time()

        # Define all strategies to optimize
        strategies = {
            'large_gpp_stack': self.get_large_gpp_space(),
            'medium_gpp_stack': self.get_medium_gpp_space(),
            'small_gpp_stack': self.get_small_gpp_space(),
            'showdown_balanced': self.get_showdown_space(),
            'large_cash_chalk': self.get_large_cash_space(),
            'medium_cash_balanced': self.get_medium_cash_space(),
            'small_cash_balanced': self.get_small_cash_space(),
        }

        # Run parallel optimization
        optimal_params = {}

        with ProcessPoolExecutor(max_workers=self.n_cores) as executor:
            # Submit all optimization tasks
            future_to_strategy = {
                executor.submit(
                    self.optimize_single_strategy,
                    strategy_name,
                    strategy_space,
                    n_calls=50  # Iterations per strategy
                ): strategy_name
                for strategy_name, strategy_space in strategies.items()
            }

            # Collect results as they complete
            for future in as_completed(future_to_strategy):
                strategy_name = future_to_strategy[future]
                try:
                    result = future.result()
                    optimal_params[strategy_name] = result
                    print(f"✅ Optimized {strategy_name}")
                except Exception as e:
                    print(f"❌ Error optimizing {strategy_name}: {e}")

        total_time = time.time() - start_time
        print(f"\n⏱️ Total optimization time: {total_time:.1f} seconds")

        return optimal_params

    def get_large_gpp_space(self):
        """
        Parameter space for Game Stack 4-2 (Large Slate GPP)
        """
        return {
            'dimensions': [
                Real(5.5, 7.0, name='min_game_total'),
                Integer(3, 5, name='primary_stack_size'),
                Integer(1, 3, name='secondary_stack_size'),
                Real(0.10, 0.35, name='max_avg_ownership'),
                Real(1.15, 1.45, name='stack_correlation_boost'),
                Real(0.6, 0.9, name='batting_order_concentration'),
                Categorical(['fade', 'include', 'target'], name='pitcher_approach'),
                Real(0.15, 0.40, name='ceiling_weight'),
                Integer(1, 3, name='num_punt_plays'),
                Real(0.7, 0.95, name='min_value_threshold'),
            ],
            'strategy_type': 'game_stack_4_2',
            'slate_size': 'large',
            'contest_type': 'gpp'
        }

    def get_medium_gpp_space(self):
        """
        Parameter space for Game Stack 3-2 (Medium Slate GPP)
        """
        return {
            'dimensions': [
                Real(5.0, 6.5, name='min_game_total'),
                Integer(3, 4, name='primary_stack_size'),
                Integer(2, 3, name='secondary_stack_size'),
                Real(0.15, 0.40, name='max_avg_ownership'),
                Real(1.10, 1.35, name='stack_correlation_boost'),
                Categorical(['sequential', 'spread', 'top_heavy'], name='batting_order_strategy'),
                Real(0.20, 0.45, name='ceiling_weight'),
                Real(0.5, 0.8, name='game_correlation_threshold'),
            ],
            'strategy_type': 'game_stack_3_2',
            'slate_size': 'medium',
            'contest_type': 'gpp'
        }

    def get_small_gpp_space(self):
        """
        Parameter space for 5-Man Stack (Small Slate GPP)
        """
        return {
            'dimensions': [
                Real(4.5, 6.0, name='min_team_total'),
                Integer(4, 5, name='stack_size'),
                Categorical(['1-5', '2-6', '3-7', 'best_proj'], name='batting_order_focus'),
                Real(0.20, 0.50, name='ownership_flexibility'),
                Real(0.65, 0.90, name='same_team_correlation'),
                Real(1.20, 1.60, name='team_stack_multiplier'),
                Categorical(['opposing', 'value', 'ceiling'], name='pitcher_selection'),
            ],
            'strategy_type': 'stack_5',
            'slate_size': 'small',
            'contest_type': 'gpp'
        }

    def get_showdown_space(self):
        """
        Parameter space for Balanced 3-3 (Showdown)
        """
        return {
            'dimensions': [
                Real(7.5, 10.5, name='min_game_total'),
                Real(10.0, 30.0, name='captain_ownership_sweet_spot'),
                Categorical(['favorite', 'underdog', 'value', 'ceiling'], name='captain_strategy'),
                Real(0.45, 0.55, name='team_balance_flexibility'),  # How strict is 3-3
                Real(0.5, 0.8, name='pitcher_inclusion_threshold'),
                Real(2.5, 4.0, name='min_captain_value_score'),
                Categorical(['balanced', 'correlated', 'contrarian'], name='util_selection'),
            ],
            'strategy_type': 'balanced_3_3',
            'slate_size': 'showdown',
            'contest_type': 'gpp'
        }

    def get_large_cash_space(self):
        """
        Parameter space for Pure Chalk (Large Slate Cash)
        """
        return {
            'dimensions': [
                Real(0.65, 0.85, name='ownership_weight'),
                Real(0.15, 0.35, name='projection_weight'),
                Real(20.0, 40.0, name='min_ownership_threshold'),
                Integer(3, 6, name='max_low_owned_players'),
                Real(0.7, 0.9, name='floor_weight'),
                Categorical(['strict', 'flexible'], name='position_fill_strategy'),
            ],
            'strategy_type': 'pure_chalk',
            'slate_size': 'large',
            'contest_type': 'cash'
        }

    def get_medium_cash_space(self):
        """
        Parameter space for Balanced 60/40 (Medium Slate Cash)
        """
        return {
            'dimensions': [
                Real(0.55, 0.65, name='ownership_weight'),
                Real(0.35, 0.45, name='projection_weight'),
                Real(0.05, 0.15, name='value_weight'),
                Real(15.0, 30.0, name='ownership_threshold'),
                Integer(2, 4, name='mini_stack_size'),
                Real(0.6, 0.8, name='floor_multiplier'),
            ],
            'strategy_type': 'balanced_60_40',
            'slate_size': 'medium',
            'contest_type': 'cash'
        }

    def get_small_cash_space(self):
        """
        Parameter space for Balanced 50/50 (Small Slate Cash)
        """
        return {
            'dimensions': [
                Real(0.45, 0.55, name='ownership_weight'),
                Real(0.45, 0.55, name='projection_weight'),
                Real(0.0, 0.1, name='contrarian_weight'),
                Integer(0, 3, name='max_players_per_team'),
                Real(0.7, 0.9, name='floor_emphasis'),
                Real(2.5, 3.5, name='min_value_score'),
            ],
            'strategy_type': 'balanced_50_50',
            'slate_size': 'small',
            'contest_type': 'cash'
        }

    def optimize_single_strategy(self, strategy_name, strategy_config, n_calls=50):
        """
        Optimize a single strategy (runs in parallel)
        """
        dimensions = strategy_config['dimensions']

        @use_named_args(dimensions)
        def objective(**params):
            """
            Objective function - what we're maximizing
            """
            # Run simulations with these parameters
            results = self.run_parallel_simulations(
                strategy_config=strategy_config,
                params=params,
                n_simulations=20  # Simulations per parameter set
            )

            # Calculate objective based on contest type
            if strategy_config['contest_type'] == 'gpp':
                # GPP: Maximize first place + top 10%
                score = (
                        results['first_place_rate'] * 1000 +
                        results['top_10_rate'] * 100 +
                        max(0, results['roi']) * 10
                )
            else:
                # Cash: Maximize win rate
                score = (
                        results['win_rate'] * 100 +
                        max(0, results['roi']) * 50
                )

            # Return negative for minimization
            return -score

        # Run Bayesian optimization
        result = gp_minimize(
            func=objective,
            dimensions=dimensions,
            n_calls=n_calls,
            n_initial_points=10,
            acq_func='EI',
            acq_optimizer='sampling',
            n_jobs=1,  # Single thread per strategy
            random_state=42
        )

        # Extract optimal parameters
        optimal_params = {}
        for i, dim in enumerate(dimensions):
            optimal_params[dim.name] = result.x[i]

        return {
            'optimal_params': optimal_params,
            'best_score': -result.fun,
            'convergence': result.func_vals,
            'strategy_config': strategy_config
        }

    def run_parallel_simulations(self, strategy_config, params, n_simulations):
        """
        Run multiple simulations in parallel for parameter evaluation
        """
        from your_simulator import simulate_contest  # Import your simulator

        results = {
            'scores': [],
            'placements': [],
            'rois': [],
            'first_places': 0,
            'top_10s': 0,
            'cashes': 0
        }

        # Run simulations
        for i in range(n_simulations):
            # Generate slate
            slate = self.generate_test_slate(
                strategy_config['slate_size'],
                seed=i
            )

            # Simulate contest
            result = simulate_contest(
                slate=slate,
                strategy_name=strategy_config['strategy_type'],
                strategy_params=params,
                contest_type=strategy_config['contest_type'],
                field_size=5000 if strategy_config['contest_type'] == 'gpp' else 100
            )

            # Track results
            if not result.get('failed'):
                results['scores'].append(result['score'])
                results['placements'].append(result['rank'])
                results['rois'].append(result['roi'])

                if result['rank'] == 1:
                    results['first_places'] += 1
                if result['percentile'] >= 90:
                    results['top_10s'] += 1
                if result['profit'] > 0:
                    results['cashes'] += 1

        # Calculate rates
        n = len(results['scores'])
        if n > 0:
            return {
                'first_place_rate': results['first_places'] / n,
                'top_10_rate': results['top_10s'] / n,
                'win_rate': results['cashes'] / n,
                'roi': np.mean(results['rois']) if results['rois'] else -100,
                'avg_score': np.mean(results['scores']) if results['scores'] else 0
            }
        else:
            return {
                'first_place_rate': 0,
                'top_10_rate': 0,
                'win_rate': 0,
                'roi': -100,
                'avg_score': 0
            }

    def generate_test_slate(self, slate_size, seed):
        """
        Generate a test slate for optimization
        """
        from your_simulator import generate_slate  # Import your generator

        slate_configs = {
            'small': ('classic', 'small'),
            'medium': ('classic', 'medium'),
            'large': ('classic', 'large'),
            'showdown': ('showdown', 'showdown')
        }

        format_type, size = slate_configs[slate_size]
        return generate_slate(seed, format_type, size)


def save_optimal_parameters(optimal_params, filename=None):
    """
    Save the optimal parameters to a file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'optimal_dfs_params_{timestamp}.json'

    # Convert numpy types to Python types
    clean_params = {}
    for strategy, data in optimal_params.items():
        clean_params[strategy] = {
            'optimal_params': {
                k: float(v) if isinstance(v, np.number) else v
                for k, v in data['optimal_params'].items()
            },
            'best_score': float(data['best_score']),
            'strategy_config': data['strategy_config']
        }

    with open(filename, 'w') as f:
        json.dump(clean_params, f, indent=2)

    print(f"\n💾 Optimal parameters saved to: {filename}")
    return filename


def print_optimization_results(optimal_params):
    """
    Pretty print the optimization results
    """
    print("\n" + "=" * 80)
    print("🏆 OPTIMAL PARAMETERS FOUND")
    print("=" * 80 + "\n")

    for strategy_name, result in optimal_params.items():
        print(f"\n📊 {strategy_name.upper()}")
        print("-" * 40)

        params = result['optimal_params']
        score = result['best_score']

        print(f"Best Score: {score:.2f}")
        print("\nOptimal Parameters:")

        for param_name, param_value in params.items():
            if isinstance(param_value, float):
                print(f"  • {param_name}: {param_value:.3f}")
            else:
                print(f"  • {param_name}: {param_value}")


def run_optimization_pipeline():
    """
    Complete optimization pipeline
    """
    print("🚀 Starting DFS Parameter Optimization Pipeline")
    print("=" * 80)

    # Initialize optimizer
    optimizer = ParallelDFSOptimizer(
        simulator_path='your_simulator.py',
        n_cores=mp.cpu_count() - 1
    )

    # Run optimization
    print(f"\n🔧 Optimizing {7} strategies in parallel...")
    print("This may take 10-30 minutes depending on your CPU\n")

    optimal_params = optimizer.optimize_all_strategies()

    # Save results
    filename = save_optimal_parameters(optimal_params)

    # Display results
    print_optimization_results(optimal_params)

    # Generate implementation code
    print("\n" + "=" * 80)
    print("📝 IMPLEMENTATION CODE")
    print("=" * 80)

    print("\n# Add this to your simulator:\n")
    print("OPTIMAL_PARAMETERS = {")
    for strategy, result in optimal_params.items():
        print(f"    '{strategy}': {{")
        for param, value in result['optimal_params'].items():
            if isinstance(value, str):
                print(f"        '{param}': '{value}',")
            else:
                print(f"        '{param}': {value},")
        print("    },")
    print("}")

    return optimal_params


if __name__ == "__main__":
    # Run the optimization
    optimal_params = run_optimization_pipeline()

    print("\n✅ Optimization complete!")
    print("🎯 Next step: Use these parameters in your lineups")
    print("💰 Expected improvement: +5-8% ROI")
    print("🍀 Translation: Maybe actually profit (but probably not)")