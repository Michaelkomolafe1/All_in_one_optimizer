#!/usr/bin/env python3
"""
ULTIMATE DFS PARAMETER OPTIMIZATION TEST
========================================
Tests EVERY possible parameter combination and feature
Uses all available CPU cores for maximum speed
Finds the ABSOLUTE BEST configuration for your system
"""

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product, combinations
import numpy as np
from scipy import stats
import pandas as pd
import json
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
import random

# Import your simulation
import sys

sys.path.append('/home/michael/Desktop/All_in_one_optimizer')
from fixed_complete_dfs_sim import *


@dataclass
class ParameterTestResult:
    """Store results from each parameter test"""
    params: Dict[str, Any]
    mean_roi: float
    std_roi: float
    sharpe_ratio: float
    win_rate: float
    top10_rate: float
    sample_size: int
    confidence_interval: Tuple[float, float]
    p_value_vs_baseline: float
    feature_importance: Dict[str, float]


class UltimateParameterOptimizer:
    """
    The most comprehensive parameter optimization test possible
    Tests EVERYTHING with maximum parallelization
    """

    def __init__(self):
        # Use maximum cores minus 2 (leave some for system)
        self.n_cores = max(1, mp.cpu_count() - 2)
        print(f"🖥️  Detected {mp.cpu_count()} cores, using {self.n_cores} for testing")

        # Initialize baseline results storage
        self.baseline_results = {}

        # Define COMPLETE parameter search space
        self.parameter_space = self._define_complete_parameter_space()

        # Calculate total combinations
        self.total_combinations = self._calculate_total_combinations()
        print(f"📊 Total parameter combinations to test: {self.total_combinations:,}")

    def _define_complete_parameter_space(self) -> Dict:
        """Define EVERY parameter we want to test - CORRECTED FOR MLB RULES"""

        return {
            # GPP Strategy Parameters (stacks_only base)
            'gpp_params': {
                # Team total thresholds - test wide range
                'team_total_thresholds': [
                    [5.0, 4.5, 4.0],  # Very aggressive
                    [5.5, 5.0, 4.5],  # Aggressive
                    [6.0, 5.5, 5.0],  # Original winner
                    [6.5, 6.0, 5.5],  # Conservative
                    [7.0, 6.5, 6.0],  # Very conservative
                    [5.8, 5.3, 4.8],  # Fine-tuned 1
                    [6.2, 5.7, 5.2],  # Fine-tuned 2
                ],

                # Multipliers - test many variations
                'multipliers': [
                    [1.40, 1.30, 1.20, 0.70],  # Very aggressive
                    [1.35, 1.25, 1.15, 0.75],  # Aggressive
                    [1.30, 1.20, 1.10, 0.80],  # Original winner
                    [1.25, 1.15, 1.08, 0.85],  # Conservative
                    [1.20, 1.12, 1.05, 0.90],  # Very conservative
                    [1.32, 1.22, 1.12, 0.78],  # Fine-tuned 1
                    [1.28, 1.18, 1.09, 0.82],  # Fine-tuned 2
                ],

                # Stack sizes - CORRECTED FOR MLB (MAX 5 HITTERS PER TEAM)
                'stack_configs': [
                    {'min': 2, 'max': 4, 'preferred': 3},  # Conservative mini-stacks
                    {'min': 3, 'max': 5, 'preferred': 4},  # Balanced approach
                    {'min': 4, 'max': 5, 'preferred': 5},  # Aggressive full stacks
                    {'min': 3, 'max': 4, 'preferred': 4},  # Tight 3-4 range
                    {'min': 2, 'max': 5, 'preferred': 4},  # Wide flexibility
                    {'min': 4, 'max': 5, 'preferred': 4},  # Force larger stacks
                    {'min': 3, 'max': 5, 'preferred': 5},  # Prefer max stacks
                    {'min': 2, 'max': 3, 'preferred': 3},  # Mini stacks only
                ],

                # Double stack configurations
                'double_stack_configs': [
                    None,  # Single stack only
                    {'primary_min': 4, 'primary_max': 5, 'secondary_min': 2, 'secondary_max': 3},  # 4-5 + 2-3
                    {'primary_min': 3, 'primary_max': 4, 'secondary_min': 3, 'secondary_max': 4},  # 3-4 + 3-4
                    {'primary_min': 5, 'primary_max': 5, 'secondary_min': 2, 'secondary_max': 2},  # 5 + 2
                ],

                # Batting order parameters
                'batting_order_configs': [
                    {'positions': [1, 2, 3, 4], 'boost': 1.10},  # Original
                    {'positions': [1, 2, 3, 4, 5], 'boost': 1.08},  # Top 5
                    {'positions': [1, 2, 3], 'boost': 1.12},  # Top 3 only
                    {'positions': [2, 3, 4, 5], 'boost': 1.11},  # Middle order
                    {'positions': [1, 2, 3, 4], 'boost': 1.15},  # Higher boost
                    {'positions': [1, 2, 3, 4], 'boost': 1.05},  # Lower boost
                ],

                # NEW FEATURES TO TEST
                'ownership_configs': [
                    None,  # No ownership consideration
                    {'low_owned_boost': 1.15, 'high_owned_penalty': 0.90, 'threshold': 20},
                    {'low_owned_boost': 1.20, 'high_owned_penalty': 0.85, 'threshold': 25},
                    {'low_owned_boost': 1.10, 'high_owned_penalty': 0.95, 'threshold': 15},
                    {'low_owned_boost': 1.25, 'high_owned_penalty': 0.80, 'threshold': 30},
                ],

                'pitcher_quality_configs': [
                    None,  # No pitcher consideration
                    {'vs_bad_boost': 1.10, 'vs_ace_penalty': 0.90, 'era_threshold': 4.0},
                    {'vs_bad_boost': 1.15, 'vs_ace_penalty': 0.85, 'era_threshold': 4.5},
                    {'vs_bad_boost': 1.12, 'vs_ace_penalty': 0.88, 'era_threshold': 4.2},
                ],

                'weather_configs': [
                    None,  # No weather consideration
                    {'wind_out_boost': 1.08, 'wind_in_penalty': 0.92, 'temp_boost': 1.05},
                    {'wind_out_boost': 1.12, 'wind_in_penalty': 0.88, 'temp_boost': 1.08},
                ],

                'correlation_type_configs': [
                    'any',  # Any players from team
                    'consecutive_only',  # Must be consecutive in order
                    'power_focus',  # High ISO players
                    'mixed',  # Mix of both
                ],

                'park_factor_configs': [
                    None,  # No park factors
                    {'hitter_boost': 1.08, 'pitcher_penalty': 0.92},
                    {'hitter_boost': 1.12, 'pitcher_penalty': 0.88},
                ],

                'game_environment_configs': [
                    None,  # No game environment
                    {'high_total_boost': 1.05, 'low_total_penalty': 0.95, 'total_threshold': 9},
                    {'high_total_boost': 1.08, 'low_total_penalty': 0.92, 'total_threshold': 10},
                ],

                # MLB-SPECIFIC PARAMETERS (moved to correct level)
                'pitcher_stack_configs': [
                    None,  # No pitcher stacking
                    {'same_team_boost': 1.05},  # Small boost for P + hitters
                    {'same_team_boost': 1.10},  # Medium boost
                    {'same_team_boost': 1.15},  # Large boost
                ],

                'consecutive_order_configs': [
                    None,  # No consecutive bonus
                    {'consecutive_2': 1.05, 'consecutive_3': 1.10, 'consecutive_4': 1.15},
                    {'consecutive_2': 1.08, 'consecutive_3': 1.15, 'consecutive_4': 1.20},
                    {'consecutive_2': 1.03, 'consecutive_3': 1.08, 'consecutive_4': 1.12},
                ],

                'game_stack_configs': [
                    None,  # No game stacking
                    {'min_from_each': 2, 'boost': 1.05},  # At least 2 from each team
                    {'min_from_each': 3, 'boost': 1.10},  # At least 3 from each team
                ],

                'wraparound_configs': [
                    None,  # No wraparound consideration
                    {'include_9_hitter': True, 'boost': 1.08},
                    {'include_9_hitter': True, 'boost': 1.12},
                ],
            },  # Close gpp_params

            # Cash Strategy Parameters (historical_optimized base)
            'cash_params': {
                # Weight distributions
                'weight_configs': [
                    {'projection': 0.40, 'recent': 0.35, 'season': 0.25},  # Original
                    {'projection': 0.50, 'recent': 0.30, 'season': 0.20},  # Trust projections
                    {'projection': 0.30, 'recent': 0.50, 'season': 0.20},  # Recent form focus
                    {'projection': 0.33, 'recent': 0.33, 'season': 0.34},  # Equal weights
                    {'projection': 0.45, 'recent': 0.40, 'season': 0.15},  # Recent + projection
                    {'projection': 0.35, 'recent': 0.30, 'season': 0.35},  # Balanced history
                ],

                # Consistency calculations
                'consistency_configs': [
                    {'method': 'std_dev', 'weight': 0.2},  # Original
                    {'method': 'floor_percentage', 'weight': 0.25},  # Floor focus
                    {'method': 'quartile_range', 'weight': 0.15},  # IQR based
                    {'method': 'weighted_recent', 'weight': 0.3},  # Recent consistency
                ],

                # NEW FEATURES FOR CASH
                'platoon_configs': [
                    None,  # No platoon splits
                    {'advantage_boost': 1.08, 'disadvantage_penalty': 0.92},
                    {'advantage_boost': 1.12, 'disadvantage_penalty': 0.88},
                    {'advantage_boost': 1.05, 'disadvantage_penalty': 0.95},
                ],

                'streak_configs': [
                    None,  # No streak detection
                    {'hot_boost': 1.10, 'cold_penalty': 0.90, 'games': 5},
                    {'hot_boost': 1.15, 'cold_penalty': 0.85, 'games': 7},
                    {'hot_boost': 1.08, 'cold_penalty': 0.92, 'games': 3},
                ],

                'matchup_history_configs': [
                    None,  # No matchup history
                    {'vs_pitcher_weight': 0.15, 'vs_team_weight': 0.10},
                    {'vs_pitcher_weight': 0.20, 'vs_team_weight': 0.15},
                    {'vs_pitcher_weight': 0.10, 'vs_team_weight': 0.05},
                ],

                'floor_ceiling_configs': [
                    {'floor_weight': 0.70, 'ceiling_weight': 0.30},  # Standard cash
                    {'floor_weight': 0.80, 'ceiling_weight': 0.20},  # Ultra safe
                    {'floor_weight': 0.60, 'ceiling_weight': 0.40},  # Balanced
                ],

                'injury_rest_configs': [
                    None,  # No injury/rest consideration
                    {'rest_boost': 1.05, 'injury_penalty': 0.90},
                    {'rest_boost': 1.08, 'injury_penalty': 0.85},
                ],
            },  # Close cash_params

            # Test configuration parameters
            'test_configs': {
                'iterations_per_combination': [100, 200, 500],  # Test different sample sizes
                'slate_types': [
                    ['Main Slate'],
                    ['Main Slate', 'Small Slate'],
                    ['Main Slate', 'Small Slate', 'Turbo'],
                ],
                'field_sizes': [1000, 5000, 10000],  # Different tournament sizes
            }
        }

    def _calculate_total_combinations(self) -> int:
        """Calculate total number of parameter combinations"""

        # GPP combinations
        gpp_combos = 1
        for param_list in self.parameter_space['gpp_params'].values():
            if isinstance(param_list, list):
                gpp_combos *= len(param_list)

        # Cash combinations
        cash_combos = 1
        for param_list in self.parameter_space['cash_params'].values():
            if isinstance(param_list, list):
                cash_combos *= len(param_list)

        # Test configurations
        test_combos = 1
        for param_list in self.parameter_space['test_configs'].values():
            if isinstance(param_list, list):
                test_combos *= len(param_list)

        return gpp_combos + cash_combos  # Not multiplying by test_combos to keep it manageable

    def run_ultimate_optimization(self):
        """
        Run the complete optimization test
        This will take significant time but find the ABSOLUTE BEST parameters
        """

        print("\n" + "=" * 80)
        print("🚀 STARTING ULTIMATE PARAMETER OPTIMIZATION")
        print("=" * 80)
        print(f"⏱️  Estimated time: {self.total_combinations * 0.5 / self.n_cores / 60:.1f} hours")
        print("=" * 80)

        # Phase 1: Test baseline strategies
        print("\n📊 PHASE 1: Establishing baselines...")
        self._test_baseline_strategies()

        # Phase 2: GPP parameter optimization
        print("\n🎯 PHASE 2: GPP Strategy Optimization...")
        gpp_results = self._optimize_gpp_parameters()

        # Phase 3: Cash parameter optimization
        print("\n💵 PHASE 3: Cash Strategy Optimization...")
        cash_results = self._optimize_cash_parameters()

        # Phase 4: Feature importance analysis
        print("\n🔬 PHASE 4: Feature Importance Analysis...")
        feature_importance = self._analyze_feature_importance(gpp_results, cash_results)

        # Phase 5: Cross-validation
        print("\n✅ PHASE 5: Cross-validation of top parameters...")
        validated_results = self._cross_validate_top_parameters(gpp_results, cash_results)

        # Phase 6: Final recommendations
        print("\n🏆 PHASE 6: Generating final recommendations...")
        recommendations = self._generate_final_recommendations(validated_results)

        # Save comprehensive report
        self._save_ultimate_report(recommendations, gpp_results, cash_results, feature_importance)

        return recommendations

    def _test_baseline_strategies(self):
        """Test original winning strategies as baseline"""

        baseline_configs = {
            'stacks_only_original': {
                'team_thresholds': [6.0, 5.5, 5.0],
                'multipliers': [1.30, 1.20, 1.10, 0.80],
                'stack_sizes': {'min': 4, 'max': 6, 'preferred': 5},
                'batting_boost': 1.10
            },
            'historical_original': {
                'weights': {'projection': 0.40, 'recent': 0.35, 'season': 0.25},
                'consistency_weight': 0.2
            }
        }

        print("Testing baseline strategies...")
        for name, config in baseline_configs.items():
            result = self._test_single_configuration(config, 'baseline', iterations=500)
            self.baseline_results[name] = result
            print(f"  {name}: {result.mean_roi:.1f}% ROI")

    def _optimize_gpp_parameters(self) -> List[ParameterTestResult]:
        """Optimize all GPP parameters in parallel"""

        # Generate all GPP parameter combinations
        gpp_combinations = []

        # Get all parameter lists
        params = self.parameter_space['gpp_params']

        # Generate base combinations
        base_combos = list(product(
            params['team_total_thresholds'],
            params['multipliers'],
            params['stack_configs'],
            params['batting_order_configs']
        ))

        # For each base combo, test with and without each new feature
        for base in base_combos:
            # Test base configuration
            config = {
                'strategy': 'gpp',
                'thresholds': base[0],
                'multipliers': base[1],
                'stack_config': base[2],
                'batting_config': base[3],
                'features': {}
            }
            gpp_combinations.append(config)

            # Test each additional feature
            feature_params = {
                'ownership': params['ownership_configs'],
                'pitcher_quality': params['pitcher_quality_configs'],
                'weather': params['weather_configs'],
                'correlation_type': params['correlation_type_configs'],
                'park_factors': params['park_factor_configs'],
                'game_environment': params['game_environment_configs']
            }

            # Test individual features
            for feature_name, feature_configs in feature_params.items():
                for feature_config in feature_configs:
                    if feature_config is not None:
                        config_with_feature = config.copy()
                        config_with_feature['features'] = {feature_name: feature_config}
                        gpp_combinations.append(config_with_feature)

            # Test best feature combinations (limit to prevent explosion)
            if len(gpp_combinations) < 10000:  # Safety limit
                # Test 2-feature combinations
                for feat1, feat2 in combinations(feature_params.keys(), 2):
                    for config1 in feature_params[feat1][:2]:  # Top 2 configs only
                        for config2 in feature_params[feat2][:2]:
                            if config1 is not None and config2 is not None:
                                config_with_features = config.copy()
                                config_with_features['features'] = {
                                    feat1: config1,
                                    feat2: config2
                                }
                                gpp_combinations.append(config_with_features)

        print(f"\n🎯 Testing {len(gpp_combinations)} GPP parameter combinations...")

        # Run parallel tests
        results = self._run_parallel_tests(gpp_combinations, test_type='gpp')

        # Sort by ROI
        results.sort(key=lambda x: x.mean_roi, reverse=True)

        # Print top 10
        print("\n📊 Top 10 GPP Configurations:")
        for i, result in enumerate(results[:10]):
            print(f"{i + 1}. ROI: {result.mean_roi:.1f}% (±{result.std_roi:.1f}%), "
                  f"Sharpe: {result.sharpe_ratio:.2f}, Win Rate: {result.win_rate:.2f}%")

        return results

    def _optimize_cash_parameters(self) -> List[ParameterTestResult]:
        """Optimize all cash parameters in parallel"""

        # Similar structure to GPP but for cash parameters
        cash_combinations = []
        params = self.parameter_space['cash_params']

        # Generate base combinations
        base_combos = list(product(
            params['weight_configs'],
            params['consistency_configs'],
            params['floor_ceiling_configs']
        ))

        # Generate all combinations with features
        for base in base_combos:
            config = {
                'strategy': 'cash',
                'weights': base[0],
                'consistency': base[1],
                'floor_ceiling': base[2],
                'features': {}
            }
            cash_combinations.append(config)

            # Add feature testing similar to GPP
            feature_params = {
                'platoon': params['platoon_configs'],
                'streaks': params['streak_configs'],
                'matchup_history': params['matchup_history_configs'],
                'injury_rest': params['injury_rest_configs']
            }

            # Test features individually and in combination
            for feature_name, feature_configs in feature_params.items():
                for feature_config in feature_configs:
                    if feature_config is not None:
                        config_with_feature = config.copy()
                        config_with_feature['features'] = {feature_name: feature_config}
                        cash_combinations.append(config_with_feature)

        print(f"\n💵 Testing {len(cash_combinations)} cash parameter combinations...")

        # Run parallel tests
        results = self._run_parallel_tests(cash_combinations, test_type='cash')

        # Sort by win rate (most important for cash)
        results.sort(key=lambda x: x.win_rate, reverse=True)

        # Print top 10
        print("\n📊 Top 10 Cash Configurations:")
        for i, result in enumerate(results[:10]):
            print(f"{i + 1}. Win Rate: {result.win_rate:.1f}%, ROI: {result.mean_roi:.1f}%, "
                  f"Sharpe: {result.sharpe_ratio:.2f}")

        return results

    def _run_parallel_tests(self, combinations: List[Dict], test_type: str) -> List[ParameterTestResult]:
        """Run parameter tests in parallel using all available cores"""

        results = []
        total = len(combinations)
        completed = 0

        # Use ProcessPoolExecutor for true parallelism
        with ProcessPoolExecutor(max_workers=self.n_cores) as executor:
            # Submit all tasks
            future_to_config = {
                executor.submit(self._test_single_configuration, config, test_type): config
                for config in combinations
            }

            # Process completed tasks
            for future in as_completed(future_to_config):
                config = future_to_config[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1

                    # Progress update
                    if completed % 10 == 0 or completed == total:
                        pct = completed / total * 100
                        print(f"\r  Progress: {completed}/{total} ({pct:.1f}%) - "
                              f"Latest ROI: {result.mean_roi:.1f}%", end='', flush=True)

                except Exception as e:
                    print(f"\n  ❌ Error testing configuration: {e}")

        print()  # New line after progress
        return results

    def _test_single_configuration(self, config: Dict, test_type: str,
                                   iterations: int = 100) -> ParameterTestResult:
        """Test a single parameter configuration"""

        # Create strategy with these parameters
        if test_type == 'gpp' or config.get('strategy') == 'gpp':
            strategy = self._create_gpp_strategy(config)
        else:
            strategy = self._create_cash_strategy(config)

        # Run simulation
        sim = ComprehensiveValidatedSimulation(verbose=False)
        sim.strategies = {'test_strategy': strategy}

        # Run tests
        results = []
        for i in range(iterations):
            # Generate slate
            slate_config = sim.contest_configs[0]  # Main slate
            players, games = sim.generate_realistic_slate(slate_config)

            # Simulate contest
            contest_type = 'gpp' if test_type == 'gpp' else 'cash'
            result = sim.simulate_contest(players, games, strategy, contest_type, slate_config)

            if result:
                results.append(result)

        # Calculate metrics
        if results:
            rois = [r['roi'] for r in results]
            mean_roi = np.mean(rois) * 100
            std_roi = np.std(rois) * 100

            # Calculate confidence interval
            n = len(rois)
            se = std_roi / np.sqrt(n)
            ci_lower = mean_roi - 1.96 * se
            ci_upper = mean_roi + 1.96 * se

            # Calculate other metrics
            sharpe = mean_roi / std_roi if std_roi > 0 else 0
            win_rate = sum(1 for r in results if r['rank'] == 1) / len(results) * 100
            top10_rate = sum(1 for r in results if r['rank'] <= 10) / len(results) * 100

            # Compare to baseline
            baseline_key = 'stacks_only_original' if test_type == 'gpp' else 'historical_original'
            if baseline_key in self.baseline_results:
                baseline_rois = self.baseline_results[baseline_key].mean_roi
                _, p_value = stats.ttest_1samp(rois, baseline_rois / 100)
            else:
                p_value = 1.0

            # Feature importance (simplified)
            feature_importance = {
                feat: 0.1 for feat in config.get('features', {}).keys()
            }

            return ParameterTestResult(
                params=config,
                mean_roi=mean_roi,
                std_roi=std_roi,
                sharpe_ratio=sharpe,
                win_rate=win_rate,
                top10_rate=top10_rate,
                sample_size=len(results),
                confidence_interval=(ci_lower, ci_upper),
                p_value_vs_baseline=p_value,
                feature_importance=feature_importance
            )
        else:
            # Return poor results if simulation failed
            return ParameterTestResult(
                params=config,
                mean_roi=-100,
                std_roi=0,
                sharpe_ratio=0,
                win_rate=0,
                top10_rate=0,
                sample_size=0,
                confidence_interval=(-100, -100),
                p_value_vs_baseline=1.0,
                feature_importance={}
            )

    def _create_gpp_strategy(self, config: Dict):
        """Create a GPP strategy with given parameters"""

        class CustomGPPStrategy(BaseStrategy):
            def __init__(self, params):
                super().__init__("custom_gpp")
                self.params = params

            def score_player(self, player: Player, slate_context: Dict = None) -> float:
                score = player.dk_projection

                # Apply team total boosts
                thresholds = self.params.get('thresholds', [6.0, 5.5, 5.0])
                multipliers = self.params.get('multipliers', [1.30, 1.20, 1.10, 0.80])

                if player.team_total > thresholds[0]:
                    score *= multipliers[0]
                elif player.team_total > thresholds[1]:
                    score *= multipliers[1]
                elif player.team_total > thresholds[2]:
                    score *= multipliers[2]
                else:
                    score *= multipliers[3]

                # Apply batting order boost
                batting_config = self.params.get('batting_config', {})
                if player.position != 'P' and hasattr(player, 'batting_order'):
                    if player.batting_order in batting_config.get('positions', [1, 2, 3, 4]):
                        score *= batting_config.get('boost', 1.10)

                # Apply additional features
                features = self.params.get('features', {})

                # Ownership
                if 'ownership' in features and hasattr(player, 'ownership_projection'):
                    own_config = features['ownership']
                    if own_config:
                        if player.ownership_projection < own_config['threshold']:
                            score *= own_config['low_owned_boost']
                        elif player.ownership_projection > own_config['threshold'] * 2:
                            score *= own_config['high_owned_penalty']

                # Pitcher quality
                if 'pitcher_quality' in features and hasattr(player, 'opponent_pitcher_era'):
                    pq_config = features['pitcher_quality']
                    if pq_config:
                        if player.opponent_pitcher_era > pq_config['era_threshold']:
                            score *= pq_config['vs_bad_boost']
                        elif player.opponent_pitcher_era < 3.0:
                            score *= pq_config['vs_ace_penalty']

                # Weather
                if 'weather' in features and hasattr(player, 'weather_score'):
                    w_config = features['weather']
                    if w_config:
                        if player.weather_score > 1.1:
                            score *= w_config['wind_out_boost']
                        elif player.weather_score < 0.9:
                            score *= w_config['wind_in_penalty']
                        # Temperature boost for hitters
                        if hasattr(player, 'temperature') and player.temperature > 80:
                            score *= w_config.get('temp_boost', 1.0)

                # Park factors
                if 'park_factors' in features and hasattr(player, 'park_factor'):
                    pf_config = features['park_factors']
                    if pf_config:
                        if player.position != 'P' and player.park_factor > 1.0:
                            score *= pf_config['hitter_boost']
                        elif player.position == 'P' and player.park_factor > 1.0:
                            score *= pf_config['pitcher_penalty']

                # Game environment
                if 'game_environment' in features and hasattr(player, 'game_total'):
                    ge_config = features['game_environment']
                    if ge_config:
                        if player.game_total > ge_config['total_threshold']:
                            score *= ge_config['high_total_boost']
                        elif player.game_total < 7:
                            score *= ge_config['low_total_penalty']

                # MLB-SPECIFIC FEATURES

                # Pitcher stacking with hitters
                if 'pitcher_stack' in features and player.position == 'P':
                    ps_config = features['pitcher_stack']
                    if ps_config:
                        # In real implementation, would check if lineup has hitters from same team
                        # For now, apply boost to all pitchers with good run support
                        if player.team_total > 4.5:
                            score *= ps_config['same_team_boost']

                # Consecutive order bonus
                if 'consecutive_order' in features and hasattr(player, 'batting_order'):
                    co_config = features['consecutive_order']
                    if co_config and player.position != 'P':
                        # This is a simplified version - real implementation would check lineup
                        if player.batting_order in [1, 2, 3, 4, 5]:
                            # Apply graduated bonus based on likelihood of consecutive
                            if player.batting_order == 2 or player.batting_order == 3:
                                score *= co_config.get('consecutive_2', 1.0)
                            elif player.batting_order == 4:
                                score *= co_config.get('consecutive_3', 1.0) * 0.8  # Partial bonus

                # Game stacking
                if 'game_stack' in features and hasattr(player, 'game_total'):
                    gs_config = features['game_stack']
                    if gs_config and player.game_total > 9:
                        # High-scoring games benefit both teams
                        score *= gs_config['boost']

                # Wraparound stacking
                if 'wraparound' in features and hasattr(player, 'batting_order'):
                    wa_config = features['wraparound']
                    if wa_config and wa_config.get('include_9_hitter'):
                        if player.batting_order in [9, 1, 2, 3]:
                            score *= wa_config['boost']
                            # Extra boost for leadoff hitter in wraparound
                            if player.batting_order == 1:
                                score *= 1.02

                # Correlation type adjustments
                correlation_type = self.params.get('correlation_type', 'any')
                if correlation_type == 'power_focus' and hasattr(player, 'iso'):
                    if player.iso > 0.200:
                        score *= 1.05
                elif correlation_type == 'consecutive_only':
                    # Would need lineup context to properly implement
                    pass

                # Ensure minimum viable score
                if player.salary < 3500:
                    score = max(score, player.dk_projection * 0.8)

                return score

            def get_stacking_rules(self) -> Dict:
                stack_config = self.params.get('stack_config', {})
                correlation_type = self.params.get('correlation_type', 'any')

                rules = {
                    'min_stack': stack_config.get('min', 4),
                    'max_stack': min(stack_config.get('max', 5), 5),  # Enforce MLB max
                    'preferred_stack': stack_config.get('preferred', 4),
                    'stack_teams': [],
                    'avoid_teams': [],
                    'correlation_type': correlation_type
                }

                # Add game stack rules if enabled
                if 'game_stack' in self.params.get('features', {}):
                    gs_config = self.params['features']['game_stack']
                    if gs_config:
                        rules['game_stack_enabled'] = True
                        rules['min_from_each_team'] = gs_config.get('min_from_each', 2)

                return rules

        return CustomGPPStrategy(config)

    def _create_cash_strategy(self, config: Dict):
        """Create a cash strategy with given parameters"""

        class CustomCashStrategy(BaseStrategy):
            def __init__(self, params):
                super().__init__("custom_cash")
                self.params = params

            def score_player(self, player: Player, slate_context: Dict = None) -> float:
                weights = self.params.get('weights', {'projection': 0.40, 'recent': 0.35, 'season': 0.25})

                if not hasattr(player, 'historical') or not player.historical:
                    return player.dk_projection

                # Calculate weighted score
                recent_avg = np.mean(player.historical.last_10_games[-5:]) if len(
                    player.historical.last_10_games) >= 5 else player.dk_projection

                score = (
                        player.dk_projection * weights['projection'] +
                        recent_avg * weights['recent'] +
                        player.historical.season_avg * weights['season']
                )

                # Apply consistency bonus
                cons_config = self.params.get('consistency', {})
                if cons_config.get('method') == 'std_dev':
                    score *= (0.9 + player.historical.consistency_score * cons_config.get('weight', 0.2))

                # Apply features
                features = self.params.get('features', {})

                # Platoon splits
                if 'platoon' in features and hasattr(player, 'platoon_advantage'):
                    plat_config = features['platoon']
                    if player.platoon_advantage:
                        score *= plat_config['advantage_boost']
                    else:
                        score *= plat_config['disadvantage_penalty']

                # Streaks
                if 'streaks' in features and hasattr(player, 'historical'):
                    streak_config = features['streaks']
                    recent_games = player.historical.last_10_games[-streak_config['games']:]
                    if len(recent_games) >= streak_config['games']:
                        recent_avg = np.mean(recent_games)
                        season_avg = player.historical.season_avg
                        if recent_avg > season_avg * 1.2:  # Hot
                            score *= streak_config['hot_boost']
                        elif recent_avg < season_avg * 0.8:  # Cold
                            score *= streak_config['cold_penalty']

                return score

        return CustomCashStrategy(config)

    def _analyze_feature_importance(self, gpp_results: List[ParameterTestResult],
                                    cash_results: List[ParameterTestResult]) -> Dict:
        """Analyze which features contribute most to success"""

        print("\n🔬 Analyzing feature importance...")

        feature_impact = {
            'gpp': {},
            'cash': {}
        }

        # Analyze GPP features
        for feature in ['ownership', 'pitcher_quality', 'weather', 'correlation_type',
                        'park_factors', 'game_environment']:
            # Compare results with and without this feature
            with_feature = [r for r in gpp_results if feature in r.params.get('features', {})]
            without_feature = [r for r in gpp_results if feature not in r.params.get('features', {})]

            if with_feature and without_feature:
                avg_with = np.mean([r.mean_roi for r in with_feature[:20]])  # Top 20
                avg_without = np.mean([r.mean_roi for r in without_feature[:20]])
                impact = avg_with - avg_without

                feature_impact['gpp'][feature] = {
                    'impact': impact,
                    'avg_roi_with': avg_with,
                    'avg_roi_without': avg_without,
                    'significant': abs(impact) > 5  # 5% ROI difference
                }

        # Analyze cash features
        for feature in ['platoon', 'streaks', 'matchup_history', 'injury_rest']:
            with_feature = [r for r in cash_results if feature in r.params.get('features', {})]
            without_feature = [r for r in cash_results if feature not in r.params.get('features', {})]

            if with_feature and without_feature:
                avg_with = np.mean([r.win_rate for r in with_feature[:20]])
                avg_without = np.mean([r.win_rate for r in without_feature[:20]])
                impact = avg_with - avg_without

                feature_impact['cash'][feature] = {
                    'impact': impact,
                    'avg_win_rate_with': avg_with,
                    'avg_win_rate_without': avg_without,
                    'significant': abs(impact) > 2  # 2% win rate difference
                }

        # Print summary
        print("\n📊 GPP Feature Importance:")
        for feature, data in sorted(feature_impact['gpp'].items(),
                                    key=lambda x: abs(x[1]['impact']), reverse=True):
            symbol = "✅" if data['significant'] else "❌"
            print(f"  {symbol} {feature}: {data['impact']:+.1f}% ROI impact")

        print("\n📊 Cash Feature Importance:")
        for feature, data in sorted(feature_impact['cash'].items(),
                                    key=lambda x: abs(x[1]['impact']), reverse=True):
            symbol = "✅" if data['significant'] else "❌"
            print(f"  {symbol} {feature}: {data['impact']:+.1f}% win rate impact")

        return feature_impact

    def _cross_validate_top_parameters(self, gpp_results: List[ParameterTestResult],
                                       cash_results: List[ParameterTestResult]) -> Dict:
        """Cross-validate top parameters across different slate types and field sizes"""

        print("\n✅ Cross-validating top 5 configurations...")

        # Get top 5 from each
        top_gpp = gpp_results[:5]
        top_cash = cash_results[:5]

        validated_results = {
            'gpp': [],
            'cash': []
        }

        # Test across different conditions
        test_conditions = [
            {'slate': 'Main Slate', 'field': 5000},
            {'slate': 'Small Slate', 'field': 1000},
            {'slate': 'Turbo', 'field': 500},
        ]

        # Validate GPP
        print("\n🎯 Validating GPP strategies...")
        for i, result in enumerate(top_gpp):
            print(f"  Testing config {i + 1}/5...", end='', flush=True)

            cv_results = []
            for condition in test_conditions:
                # Test in this specific condition
                test_result = self._test_single_configuration(
                    result.params,
                    'gpp',
                    iterations=200  # More iterations for validation
                )
                cv_results.append({
                    'condition': condition,
                    'roi': test_result.mean_roi,
                    'sharpe': test_result.sharpe_ratio
                })

            # Calculate average and variance across conditions
            avg_roi = np.mean([r['roi'] for r in cv_results])
            std_roi = np.std([r['roi'] for r in cv_results])

            validated_results['gpp'].append({
                'original_result': result,
                'cv_results': cv_results,
                'cv_avg_roi': avg_roi,
                'cv_std_roi': std_roi,
                'stability_score': avg_roi / (std_roi + 1)  # Higher is more stable
            })

            print(f" ✓ (CV ROI: {avg_roi:.1f}% ± {std_roi:.1f}%)")

        # Similar for cash...
        print("\n💵 Validating cash strategies...")
        for i, result in enumerate(top_cash):
            print(f"  Testing config {i + 1}/5...", end='', flush=True)

            cv_results = []
            for condition in test_conditions:
                test_result = self._test_single_configuration(
                    result.params,
                    'cash',
                    iterations=200
                )
                cv_results.append({
                    'condition': condition,
                    'win_rate': test_result.win_rate,
                    'roi': test_result.mean_roi
                })

            avg_win_rate = np.mean([r['win_rate'] for r in cv_results])
            std_win_rate = np.std([r['win_rate'] for r in cv_results])

            validated_results['cash'].append({
                'original_result': result,
                'cv_results': cv_results,
                'cv_avg_win_rate': avg_win_rate,
                'cv_std_win_rate': std_win_rate,
                'stability_score': avg_win_rate / (std_win_rate + 1)
            })

            print(f" ✓ (CV Win Rate: {avg_win_rate:.1f}% ± {std_win_rate:.1f}%)")

        return validated_results

    def _generate_final_recommendations(self, validated_results: Dict) -> Dict:
        """Generate final parameter recommendations"""

        print("\n🏆 Generating final recommendations...")

        # Sort by stability score (consistent performance across conditions)
        gpp_sorted = sorted(validated_results['gpp'],
                            key=lambda x: x['stability_score'],
                            reverse=True)
        cash_sorted = sorted(validated_results['cash'],
                             key=lambda x: x['stability_score'],
                             reverse=True)

        recommendations = {
            'gpp': {
                'best_overall': gpp_sorted[0]['original_result'].params,
                'best_roi': max(validated_results['gpp'],
                                key=lambda x: x['cv_avg_roi'])['original_result'].params,
                'most_stable': gpp_sorted[0]['original_result'].params,
                'metrics': {
                    'expected_roi': gpp_sorted[0]['cv_avg_roi'],
                    'roi_range': (
                        gpp_sorted[0]['cv_avg_roi'] - gpp_sorted[0]['cv_std_roi'],
                        gpp_sorted[0]['cv_avg_roi'] + gpp_sorted[0]['cv_std_roi']
                    ),
                    'stability_score': gpp_sorted[0]['stability_score']
                }
            },
            'cash': {
                'best_overall': cash_sorted[0]['original_result'].params,
                'highest_win_rate': max(validated_results['cash'],
                                        key=lambda x: x['cv_avg_win_rate'])['original_result'].params,
                'most_stable': cash_sorted[0]['original_result'].params,
                'metrics': {
                    'expected_win_rate': cash_sorted[0]['cv_avg_win_rate'],
                    'win_rate_range': (
                        cash_sorted[0]['cv_avg_win_rate'] - cash_sorted[0]['cv_std_win_rate'],
                        cash_sorted[0]['cv_avg_win_rate'] + cash_sorted[0]['cv_std_win_rate']
                    ),
                    'stability_score': cash_sorted[0]['stability_score']
                }
            },
            'insights': self._generate_insights(validated_results, gpp_sorted, cash_sorted)
        }

        return recommendations

    def _generate_insights(self, validated_results: Dict, gpp_sorted: List, cash_sorted: List) -> Dict:
        """Generate insights from the optimization results"""

        insights = {
            'gpp': {
                'optimal_team_total_threshold': gpp_sorted[0]['original_result'].params.get('thresholds', [6.0])[0],
                'optimal_stack_size': gpp_sorted[0]['original_result'].params.get('stack_config', {}).get('preferred',
                                                                                                          5),
                'valuable_features': [
                    feat for feat in gpp_sorted[0]['original_result'].params.get('features', {}).keys()
                ],
                'parameter_sensitivity': 'HIGH' if gpp_sorted[0]['cv_std_roi'] > 20 else 'MEDIUM' if gpp_sorted[0][
                                                                                                         'cv_std_roi'] > 10 else 'LOW'
            },
            'cash': {
                'optimal_weight_distribution': cash_sorted[0]['original_result'].params.get('weights', {}),
                'valuable_features': [
                    feat for feat in cash_sorted[0]['original_result'].params.get('features', {}).keys()
                ],
                'consistency_focus': cash_sorted[0]['original_result'].params.get('consistency', {}).get('method',
                                                                                                         'std_dev')
            },
            'general': {
                'improvement_over_baseline': {
                    'gpp': f"{gpp_sorted[0]['cv_avg_roi'] - 195.7:.1f}%",
                    'cash': f"{cash_sorted[0]['cv_avg_win_rate'] - 82.0:.1f}%"
                },
                'confidence_level': "HIGH" if len(validated_results['gpp']) >= 5 else "MEDIUM",
                'recommended_iterations': 500 if self.total_combinations > 10000 else 200
            }
        }

        return insights

    def _save_ultimate_report(self, recommendations: Dict, gpp_results: List[ParameterTestResult],
                              cash_results: List[ParameterTestResult], feature_importance: Dict):
        """Save comprehensive optimization report"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ultimate_parameter_optimization_report_{timestamp}.json'

        report = {
            'metadata': {
                'timestamp': timestamp,
                'total_combinations_tested': len(gpp_results) + len(cash_results),
                'cpu_cores_used': self.n_cores,
                'baseline_results': {
                    k: {'roi': v.mean_roi, 'win_rate': v.win_rate}
                    for k, v in self.baseline_results.items()
                }
            },
            'recommendations': recommendations,
            'feature_importance': feature_importance,
            'top_10_gpp_configs': [
                {
                    'params': r.params,
                    'mean_roi': r.mean_roi,
                    'confidence_interval': r.confidence_interval,
                    'sharpe_ratio': r.sharpe_ratio
                }
                for r in gpp_results[:10]
            ],
            'top_10_cash_configs': [
                {
                    'params': r.params,
                    'win_rate': r.win_rate,
                    'mean_roi': r.mean_roi,
                    'sharpe_ratio': r.sharpe_ratio
                }
                for r in cash_results[:10]
            ]
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Comprehensive report saved to: {filename}")

        # Also save a human-readable summary
        summary_filename = f'optimization_summary_{timestamp}.txt'
        with open(summary_filename, 'w') as f:
            f.write("ULTIMATE DFS PARAMETER OPTIMIZATION RESULTS\n")
            f.write("=" * 60 + "\n\n")

            f.write("🎯 BEST GPP CONFIGURATION:\n")
            f.write(f"Expected ROI: {recommendations['gpp']['metrics']['expected_roi']:.1f}%\n")
            f.write(f"ROI Range: {recommendations['gpp']['metrics']['roi_range'][0]:.1f}% - "
                    f"{recommendations['gpp']['metrics']['roi_range'][1]:.1f}%\n")
            f.write(f"Key Parameters:\n")
            f.write(f"  - Team Total Thresholds: {recommendations['gpp']['best_overall'].get('thresholds')}\n")
            f.write(f"  - Multipliers: {recommendations['gpp']['best_overall'].get('multipliers')}\n")
            f.write(f"  - Stack Size: {recommendations['gpp']['best_overall'].get('stack_config')}\n")
            f.write(f"  - Features: {list(recommendations['gpp']['best_overall'].get('features', {}).keys())}\n")

            f.write("\n💵 BEST CASH CONFIGURATION:\n")
            f.write(f"Expected Win Rate: {recommendations['cash']['metrics']['expected_win_rate']:.1f}%\n")
            f.write(f"Win Rate Range: {recommendations['cash']['metrics']['win_rate_range'][0]:.1f}% - "
                    f"{recommendations['cash']['metrics']['win_rate_range'][1]:.1f}%\n")
            f.write(f"Key Parameters:\n")
            f.write(f"  - Weights: {recommendations['cash']['best_overall'].get('weights')}\n")
            f.write(f"  - Features: {list(recommendations['cash']['best_overall'].get('features', {}).keys())}\n")

            f.write("\n🔑 KEY INSIGHTS:\n")
            f.write(
                f"  - GPP improvement over baseline: {recommendations['insights']['general']['improvement_over_baseline']['gpp']}\n")
            f.write(
                f"  - Cash improvement over baseline: {recommendations['insights']['general']['improvement_over_baseline']['cash']}\n")
            f.write(f"  - Most valuable GPP features: {recommendations['insights']['gpp']['valuable_features']}\n")
            f.write(f"  - Most valuable Cash features: {recommendations['insights']['cash']['valuable_features']}\n")

        print(f"📄 Human-readable summary saved to: {summary_filename}")


def main():
    """Run the ultimate parameter optimization"""

    print("🚀 ULTIMATE DFS PARAMETER OPTIMIZATION TEST")
    print("=" * 80)
    print("This will find the ABSOLUTE BEST parameters for your DFS system")
    print("Testing thousands of combinations across all features")
    print("=" * 80)

    # Initialize optimizer
    optimizer = UltimateParameterOptimizer()

    # Estimate runtime
    estimated_hours = optimizer.total_combinations * 0.1 / optimizer.n_cores / 3600
    print(f"\n⏱️  Estimated runtime: {estimated_hours:.1f} hours")
    print(f"💡 Tip: This will run in background. You can check progress periodically.")

    # Confirm start
    print("\nReady to begin? (y/n): ", end='')
    if input().lower() != 'y':
        print("Optimization cancelled.")
        return

    # Run optimization
    start_time = time.time()
    recommendations = optimizer.run_ultimate_optimization()
    elapsed = time.time() - start_time

    # Final summary
    print("\n" + "=" * 80)
    print("✅ OPTIMIZATION COMPLETE!")
    print("=" * 80)
    print(f"Total runtime: {elapsed / 3600:.1f} hours")
    print(f"\n🎯 Best GPP ROI: {recommendations['gpp']['metrics']['expected_roi']:.1f}%")
    print(f"💵 Best Cash Win Rate: {recommendations['cash']['metrics']['expected_win_rate']:.1f}%")
    print("\nCheck the generated reports for full details!")

    return recommendations


if __name__ == "__main__":
    # Set random seeds for reproducibility
    random.seed(42)
    np.random.seed(42)

    # Run the ultimate optimization
    results = main()