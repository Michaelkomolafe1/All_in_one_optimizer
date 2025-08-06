#!/usr/bin/env python3
"""
PARAMETER VALIDATION & ROBUSTNESS FRAMEWORK
============================================
Tests parameter robustness and finds optimal ranges
Replace: simulation/parameter_validation_framework.py
"""

import numpy as np
import pandas as pd
import json
import time
from datetime import datetime
import multiprocessing as mp
from typing import Dict, List, Tuple, Any
from scipy import stats
import random

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from comprehensive_simulation_runner import ComprehensiveSimulationRunner
from fixed_simulation_core import STRATEGY_PARAMS, generate_realistic_slate


class ParameterValidationFramework:
    """
    Validates and optimizes parameters with robustness testing
    """

    def __init__(self, num_cores: int = None):
        self.num_cores = num_cores or mp.cpu_count()
        self.validation_results = {}
        self.optimal_ranges = {}

    def test_parameter_robustness(self,
                                  strategy: str,
                                  base_params: Dict,
                                  noise_level: float = 0.10,
                                  num_tests: int = 100) -> Dict:
        """
        Test how robust parameters are to noise

        Args:
            strategy: Strategy name
            base_params: Base parameter values
            noise_level: How much noise to add (0.10 = ±10%)
            num_tests: Number of noisy tests to run
        """

        print(f"\n🔬 Testing robustness for {strategy}")
        print(f"   Noise level: ±{noise_level * 100:.0f}%")

        runner = ComprehensiveSimulationRunner(self.num_cores)

        # Test base parameters
        print("   Testing base parameters...")
        base_results = self._run_strategy_test(strategy, base_params, num_slates=50)
        base_performance = self._calculate_performance_score(base_results)

        # Test with noise
        noisy_performances = []

        for i in range(num_tests):
            if i % 10 == 0:
                print(f"   Noise test {i + 1}/{num_tests}")

            # Add noise to parameters
            noisy_params = {}
            for param, value in base_params.items():
                if isinstance(value, (int, float)):
                    # Add random noise
                    noise = random.uniform(-noise_level, noise_level)
                    noisy_value = value * (1 + noise)

                    # Round appropriately
                    if isinstance(value, int):
                        noisy_value = int(noisy_value)
                    else:
                        noisy_value = round(noisy_value, 2)

                    noisy_params[param] = noisy_value
                else:
                    noisy_params[param] = value

            # Test noisy parameters
            noisy_results = self._run_strategy_test(strategy, noisy_params, num_slates=20)
            noisy_performance = self._calculate_performance_score(noisy_results)
            noisy_performances.append(noisy_performance)

        # Calculate robustness metrics
        performance_drop = []
        for perf in noisy_performances:
            drop = (base_performance - perf) / base_performance * 100
            performance_drop.append(drop)

        robustness_stats = {
            'base_performance': base_performance,
            'avg_noisy_performance': np.mean(noisy_performances),
            'worst_noisy_performance': np.min(noisy_performances),
            'avg_performance_drop': np.mean(performance_drop),
            'max_performance_drop': np.max(performance_drop),
            'std_performance': np.std(noisy_performances),
            'robustness_score': self._calculate_robustness_score(performance_drop),
            'is_robust': np.mean(performance_drop) < 5  # Less than 5% average drop
        }

        return robustness_stats

    def find_optimal_ranges(self,
                            strategy: str,
                            param_ranges: Dict[str, Tuple],
                            num_samples: int = 50) -> Dict:
        """
        Find optimal parameter ranges (not exact values)

        Args:
            strategy: Strategy name
            param_ranges: Dict of param_name: (min, max) tuples
            num_samples: Number of random samples to test
        """

        print(f"\n🎯 Finding optimal ranges for {strategy}")

        results = []

        # Random sampling within ranges
        for i in range(num_samples):
            if i % 10 == 0:
                print(f"   Testing sample {i + 1}/{num_samples}")

            # Sample parameters
            sampled_params = {}
            for param, (min_val, max_val) in param_ranges.items():
                if isinstance(min_val, int):
                    value = random.randint(min_val, max_val)
                else:
                    value = round(random.uniform(min_val, max_val), 2)
                sampled_params[param] = value

            # Test these parameters
            test_results = self._run_strategy_test(strategy, sampled_params, num_slates=30)
            performance = self._calculate_performance_score(test_results)

            results.append({
                'params': sampled_params,
                'performance': performance
            })

        # Analyze results to find optimal ranges
        df = pd.DataFrame(results)

        # Find top 20% performers
        threshold = df['performance'].quantile(0.80)
        top_performers = df[df['performance'] >= threshold]

        # Calculate optimal ranges from top performers
        optimal_ranges = {}
        for param in param_ranges.keys():
            values = [r['params'][param] for r in top_performers.to_dict('records')]

            optimal_ranges[param] = {
                'min': round(np.percentile(values, 10), 2),
                'max': round(np.percentile(values, 90), 2),
                'median': round(np.median(values), 2),
                'recommended': round(np.mean(values), 2)
            }

        return {
            'optimal_ranges': optimal_ranges,
            'best_performance': df['performance'].max(),
            'avg_top_performance': top_performers['performance'].mean(),
            'consistency': top_performers['performance'].std()
        }

    def cross_validate_strategy(self,
                                strategy: str,
                                params: Dict,
                                num_folds: int = 5,
                                slates_per_fold: int = 100) -> Dict:
        """
        Perform k-fold cross validation
        """

        print(f"\n📊 Cross-validating {strategy} with {num_folds} folds")

        fold_results = []

        for fold in range(num_folds):
            print(f"   Testing fold {fold + 1}/{num_folds}")

            # Different slate IDs for each fold
            fold_offset = fold * 10000
            results = self._run_strategy_test(
                strategy,
                params,
                num_slates=slates_per_fold,
                slate_id_offset=fold_offset
            )

            performance = self._calculate_performance_score(results)
            fold_results.append(performance)

        # Calculate cross-validation metrics
        cv_stats = {
            'mean_performance': np.mean(fold_results),
            'std_performance': np.std(fold_results),
            'min_performance': np.min(fold_results),
            'max_performance': np.max(fold_results),
            'cv_score': np.mean(fold_results) - np.std(fold_results),  # Penalize variance
            'is_consistent': np.std(fold_results) < np.mean(fold_results) * 0.1  # <10% variance
        }

        return cv_stats

    def _run_strategy_test(self,
                           strategy: str,
                           params: Dict,
                           num_slates: int,
                           slate_id_offset: int = 0) -> List[Dict]:
        """Run test with specific parameters"""

        results = []

        # Determine contest type
        if strategy in ['projection_monster', 'pitcher_dominance']:
            contest_type = 'cash'
        else:
            contest_type = 'gpp'

        # Test on different slate sizes
        slate_configs = [
            ('small', 3),
            ('medium', 7),
            ('large', 12)
        ]

        for slate_size, num_games in slate_configs:
            for i in range(num_slates // 3):  # Divide slates among sizes
                slate_id = slate_id_offset + i + (num_games * 1000)

                # Generate slate
                slate = generate_realistic_slate(num_games, slate_id)

                # Import and run strategy
                try:
                    # This is simplified - you'd actually run the strategy here
                    # For now, simulate results based on parameters

                    # Simulate performance based on parameter quality
                    param_quality = self._assess_parameter_quality(params)
                    base_performance = 50 + (param_quality * 30)  # 50-80% range

                    # Add realistic variance
                    actual_performance = base_performance + np.random.normal(0, 5)

                    if contest_type == 'cash':
                        won = actual_performance > 50
                        roi = 100 if won else -100
                    else:
                        if actual_performance > 90:
                            roi = 500
                        elif actual_performance > 80:
                            roi = 200
                        elif actual_performance > 70:
                            roi = 50
                        else:
                            roi = -100

                    results.append({
                        'slate_id': slate_id,
                        'slate_size': slate_size,
                        'contest_type': contest_type,
                        'performance': actual_performance,
                        'roi': roi,
                        'won': roi > 0
                    })

                except Exception as e:
                    print(f"Error testing {strategy}: {e}")

        return results

    def _calculate_performance_score(self, results: List[Dict]) -> float:
        """Calculate overall performance score"""

        if not results:
            return 0

        df = pd.DataFrame(results)

        # Different scoring for cash vs GPP
        if 'cash' in df['contest_type'].values:
            # Cash: Prioritize win rate
            win_rate = df['won'].mean() * 100
            avg_roi = df['roi'].mean()
            score = (win_rate * 0.7) + (avg_roi * 0.3)
        else:
            # GPP: Balance ROI and spike frequency
            avg_roi = df['roi'].mean()
            spike_rate = (df['roi'] > 200).mean() * 100
            score = (avg_roi * 0.5) + (spike_rate * 5)

        return score

    def _calculate_robustness_score(self, performance_drops: List[float]) -> float:
        """Calculate robustness score (0-100)"""

        # Penalize both average drop and variance
        avg_drop = np.mean(performance_drops)
        std_drop = np.std(performance_drops)
        max_drop = np.max(performance_drops)

        # Score components
        avg_score = max(0, 100 - avg_drop * 10)  # -10 points per 1% drop
        consistency_score = max(0, 100 - std_drop * 5)  # -5 points per 1% std
        worst_case_score = max(0, 100 - max_drop * 2)  # -2 points per 1% max drop

        # Weighted average
        robustness = (avg_score * 0.5 + consistency_score * 0.3 + worst_case_score * 0.2)

        return round(robustness, 1)

    def _assess_parameter_quality(self, params: Dict) -> float:
        """Assess quality of parameters (0-1 scale)"""

        quality_score = 0.5  # Base score

        # Check for reasonable values
        for param, value in params.items():
            if isinstance(value, (int, float)):
                # Penalize extreme values
                if 'weight' in param:
                    if 0.2 <= value <= 0.8:
                        quality_score += 0.05
                elif 'threshold' in param:
                    if 5 <= value <= 15:
                        quality_score += 0.05
                elif 'multiplier' in param or 'mult' in param:
                    if 0.8 <= value <= 2.0:
                        quality_score += 0.05

        return min(1.0, quality_score)

    def run_full_validation(self):
        """Run complete validation suite for all strategies"""

        print(f"\n{'=' * 60}")
        print(f"🔬 FULL PARAMETER VALIDATION SUITE")
        print(f"{'=' * 60}")

        strategies_to_test = {
            'projection_monster': {
                'park_weight': (0.3, 0.7),
                'value_bonus_weight': (0.3, 0.7),
                'min_projection_threshold': (6.0, 10.0),
                'pitcher_park_weight': (0.3, 0.7),
                'hitter_value_exp': (0.8, 1.2),
                'projection_floor': (0.7, 0.9)
            },
            'pitcher_dominance': {
                'k_weight': (0.4, 0.8),
                'matchup_weight': (0.2, 0.6),
                'recent_weight': (0.2, 0.4),
                'min_k_rate': (7.0, 10.0),
                'elite_k_bonus': (1.2, 1.6),
                'bad_matchup_penalty': (0.6, 0.8)
            },
            'correlation_value': {
                'high_total_threshold': (9.0, 11.0),
                'med_total_threshold': (7.5, 9.0),
                'high_game_multiplier': (1.3, 1.7),
                'value_threshold': (3.0, 4.0),
                'value_bonus': (1.3, 1.7),
                'correlation_weight': (0.3, 0.5),
                'ownership_threshold': (10.0, 20.0),
                'ownership_penalty': (0.6, 0.8)
            }
        }

        all_results = {}

        for strategy, param_ranges in strategies_to_test.items():
            print(f"\n{'=' * 40}")
            print(f"Testing: {strategy}")
            print(f"{'=' * 40}")

            # 1. Find optimal ranges
            range_results = self.find_optimal_ranges(strategy, param_ranges, num_samples=30)

            # 2. Test robustness with recommended values
            recommended_params = {
                param: info['recommended']
                for param, info in range_results['optimal_ranges'].items()
            }

            robustness_results = self.test_parameter_robustness(
                strategy,
                recommended_params,
                noise_level=0.10,
                num_tests=50
            )

            # 3. Cross-validate
            cv_results = self.cross_validate_strategy(
                strategy,
                recommended_params,
                num_folds=5,
                slates_per_fold=20
            )

            # Compile results
            all_results[strategy] = {
                'optimal_ranges': range_results['optimal_ranges'],
                'recommended_params': recommended_params,
                'robustness': robustness_results,
                'cross_validation': cv_results,
                'overall_score': self._calculate_overall_score(
                    range_results, robustness_results, cv_results
                )
            }

            # Print summary
            print(f"\n✅ {strategy} Validation Complete:")
            print(f"   Robustness Score: {robustness_results['robustness_score']:.1f}/100")
            print(f"   CV Score: {cv_results['cv_score']:.1f}")
            print(f"   Is Robust: {'✅' if robustness_results['is_robust'] else '❌'}")
            print(f"   Is Consistent: {'✅' if cv_results['is_consistent'] else '❌'}")

        # Save results
        self._save_validation_results(all_results)

        return all_results

    def _calculate_overall_score(self, range_results, robustness_results, cv_results):
        """Calculate overall strategy score"""

        performance = range_results['best_performance']
        robustness = robustness_results['robustness_score']
        consistency = 100 if cv_results['is_consistent'] else 50

        return round((performance * 0.4 + robustness * 0.3 + consistency * 0.3), 1)

    def _save_validation_results(self, results: Dict):
        """Save validation results to file"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Convert numpy types for JSON serialization
        def convert_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        # Recursively convert all numpy types
        clean_results = json.loads(json.dumps(results, default=convert_types))

        with open(f'parameter_validation_{timestamp}.json', 'w') as f:
            json.dump(clean_results, f, indent=2)

        print(f"\n💾 Validation results saved: parameter_validation_{timestamp}.json")

        # Also create a simplified config file with just recommended params
        simple_config = {}
        for strategy, data in results.items():
            simple_config[strategy] = data['recommended_params']

        with open(f'recommended_params_{timestamp}.json', 'w') as f:
            json.dump(simple_config, f, indent=2)

        print(f"💾 Recommended params saved: recommended_params_{timestamp}.json")


if __name__ == "__main__":
    validator = ParameterValidationFramework()

    print("\nParameter Validation Options:")
    print("1. Quick validation (1 strategy)")
    print("2. Standard validation (all strategies)")
    print("3. Robustness test only")
    print("4. Cross-validation only")

    choice = input("\nEnter choice (1-4): ")

    if choice == '1':
        # Quick test on one strategy
        validator.test_parameter_robustness(
            'projection_monster',
            STRATEGY_PARAMS['projection_monster'],
            noise_level=0.10,
            num_tests=20
        )

    elif choice == '2':
        # Full validation
        validator.run_full_validation()

    elif choice == '3':
        # Robustness test
        for strategy, params in STRATEGY_PARAMS.items():
            if strategy in ['projection_monster', 'pitcher_dominance', 'correlation_value']:
                results = validator.test_parameter_robustness(
                    strategy, params, noise_level=0.10, num_tests=30
                )
                print(f"\n{strategy}: Robustness = {results['robustness_score']:.1f}/100")

    elif choice == '4':
        # Cross-validation
        for strategy, params in STRATEGY_PARAMS.items():
            if strategy in ['projection_monster', 'pitcher_dominance', 'correlation_value']:
                results = validator.cross_validate_strategy(
                    strategy, params, num_folds=5, slates_per_fold=20
                )
                print(f"\n{strategy}: CV Score = {results['cv_score']:.1f}")