#!/usr/bin/env python3
"""
HEAD-TO-HEAD STRATEGY VERIFICATION TEST
=======================================
Definitively determines the best GPP and Cash strategies
Runs longer for statistical confidence
"""

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import numpy as np
from collections import defaultdict
import json
from datetime import datetime
import random
from scipy import stats
import matplotlib.pyplot as plt

# Import your simulation
import sys

sys.path.append('/home/michael/Desktop/All_in_one_optimizer')
from fixed_complete_dfs_sim import *


def run_definitive_comparison_test():
    """Run head-to-head test with high confidence"""

    print("🏆 DEFINITIVE HEAD-TO-HEAD STRATEGY TEST")
    print("=" * 80)
    print("Finding the ABSOLUTE BEST strategies with 95% confidence")
    print("Running extended test for statistical certainty")
    print(f"Using {mp.cpu_count()} CPU cores")
    print("=" * 80)

    # Create simulation
    sim = ComprehensiveValidatedSimulation(verbose=False)

    # Test parameters for HIGH CONFIDENCE
    iterations = 100  # More iterations for certainty
    slate_types = ['Main Slate', 'Small Slate', 'Turbo']

    # TOP STRATEGIES TO TEST - TOP 3 ONLY
    gpp_strategies = [
        'stacks_only',  # Previous #1
        'advanced_sabermetrics',  # Previous #2 (after yours)
        'your_system_gpp'  # Your strategy to compare
    ]

    cash_strategies = [
        'cash_optimized',  # Best cash strategy
        'historical_optimized',  # Second best
        'value_optimized'  # Third best (excluding yours)
    ]

    print(f"\n🎯 Testing TOP 3 GPP strategies")
    print(f"💵 Testing TOP 3 Cash strategies (excluding your_system_cash)")
    print(f"📊 {iterations} iterations each for statistical confidence")

    # Generate test slates
    print("\nGenerating diverse test slates...")
    all_slates = {}
    for slate_config in [c for c in sim.contest_configs if c.name in slate_types]:
        slates = []
        for i in range(20):  # 20 unique slates per type
            players, games = sim.generate_realistic_slate(slate_config)
            slates.append((players, games, slate_config))
        all_slates[slate_config.name] = slates

    # Test GPP strategies
    print("\n" + "=" * 80)
    print("🎯 GPP TOURNAMENT TESTING")
    print("=" * 80)

    gpp_results = test_strategies_head_to_head(
        sim, gpp_strategies, 'gpp', all_slates, iterations
    )

    # Test Cash strategies
    print("\n" + "=" * 80)
    print("💵 CASH GAME TESTING")
    print("=" * 80)

    cash_results = test_strategies_head_to_head(
        sim, cash_strategies, 'cash', all_slates, iterations
    )

    # Comprehensive analysis
    print("\n" + "=" * 80)
    print("📊 DEFINITIVE RESULTS WITH CONFIDENCE INTERVALS")
    print("=" * 80)

    analyze_definitive_results(gpp_results, cash_results, iterations)

    # Save detailed report
    save_definitive_report(gpp_results, cash_results)


def test_strategies_head_to_head(sim, strategy_names, contest_type, all_slates, iterations):
    """Test strategies with high statistical confidence"""

    results = defaultdict(list)
    completed = 0
    total_tasks = len(strategy_names) * iterations * len(all_slates)

    # Prepare all tasks
    tasks = []
    for strategy_name in strategy_names:
        if strategy_name not in sim.strategies:
            print(f"Warning: {strategy_name} not found")
            continue

        strategy = sim.strategies[strategy_name]

        # Test on multiple slate types
        for slate_name, slate_list in all_slates.items():
            for i in range(iterations):
                # Rotate through slates
                players, games, slate_config = slate_list[i % len(slate_list)]

                tasks.append((
                    strategy_name, strategy, contest_type,
                    players, games, slate_config
                ))

    # Process in parallel
    start_time = time.time()

    with ProcessPoolExecutor(max_workers=min(16, mp.cpu_count() - 2)) as executor:
        futures = {executor.submit(run_single_contest_simulation, task): task[0]
                   for task in tasks}

        for future in as_completed(futures):
            completed += 1
            strategy_name = futures[future]

            if completed % 100 == 0 or completed == len(tasks):
                elapsed = time.time() - start_time
                rate = completed / elapsed
                remaining = (len(tasks) - completed) / rate
                print(f"\rProgress: {completed}/{len(tasks)} "
                      f"({completed / len(tasks) * 100:.0f}%) "
                      f"ETA: {remaining / 60:.1f} min",
                      end='', flush=True)

            try:
                result = future.result()
                if result:
                    results[strategy_name].append(result)
            except Exception as e:
                print(f"\nError: {e}")

    print(f"\nCompleted in {(time.time() - start_time) / 60:.1f} minutes")
    return results


def run_single_contest_simulation(args):
    """Run realistic single contest simulation"""
    strategy_name, strategy, contest_type, players, games, slate_config = args

    # Import field simulator
    from realistic_test import RealisticFieldSimulator, simulate_realistic_contest

    field_simulator = RealisticFieldSimulator()

    result = simulate_realistic_contest(
        players, games, strategy, contest_type, slate_config,
        strategy_name, field_simulator
    )

    return result


def analyze_definitive_results(gpp_results, cash_results, iterations):
    """Provide definitive analysis with statistical confidence"""

    # GPP Analysis
    print("\n🎯 DEFINITIVE GPP RANKINGS")
    print("-" * 100)

    gpp_analysis = []

    for strategy_name, results in gpp_results.items():
        if not results:
            continue

        rois = [r['roi'] * 100 for r in results]

        analysis = {
            'strategy': strategy_name,
            'mean_roi': np.mean(rois),
            'median_roi': np.median(rois),
            'std_roi': np.std(rois),
            'ci_lower': np.percentile(rois, 2.5),
            'ci_upper': np.percentile(rois, 97.5),
            'win_rate': sum(r['rank'] == 1 for r in results) / len(results) * 100,
            'top_10_rate': sum(r['top_10_pct'] for r in results) / len(results) * 100,
            'cash_rate': sum(r['cashed'] for r in results) / len(results) * 100,
            'big_win_rate': sum(r.get('big_win', False) for r in results) / len(results) * 100,
            'sample_size': len(results)
        }

        gpp_analysis.append(analysis)

    # Sort by mean ROI
    gpp_analysis.sort(key=lambda x: x['mean_roi'], reverse=True)

    # Display results
    print(f"\n{'Rank':<6} {'Strategy':<20} {'Mean ROI':<10} {'95% CI':<20} "
          f"{'Win%':<8} {'Top10%':<8} {'Cash%':<8}")
    print("-" * 100)

    for i, a in enumerate(gpp_analysis):
        is_yours = "⭐" if "your_system" in a['strategy'] else "  "
        ci = f"({a['ci_lower']:.0f}%, {a['ci_upper']:.0f}%)"

        print(f"{is_yours}{i + 1:<4} {a['strategy']:<20} {a['mean_roi']:>8.1f}% {ci:<20} "
              f"{a['win_rate']:>6.1f}% {a['top_10_rate']:>7.1f}% {a['cash_rate']:>7.1f}%")

    # Statistical significance testing
    print("\n📊 STATISTICAL SIGNIFICANCE (vs #1 strategy)")
    print("-" * 80)

    if len(gpp_analysis) > 1:
        best_strategy = gpp_analysis[0]['strategy']
        best_results = gpp_results[best_strategy]
        best_rois = [r['roi'] for r in best_results]

        for i, analysis in enumerate(gpp_analysis[1:], 1):
            strategy_rois = [r['roi'] for r in gpp_results[analysis['strategy']]]

            # T-test
            t_stat, p_value = stats.ttest_ind(best_rois, strategy_rois)

            # Effect size (Cohen's d)
            effect_size = (np.mean(best_rois) - np.mean(strategy_rois)) / np.sqrt(
                (np.std(best_rois) ** 2 + np.std(strategy_rois) ** 2) / 2
            )

            sig_symbol = "✅" if p_value < 0.05 else "❌"

            print(f"{analysis['strategy']:<20} vs {best_strategy}:")
            print(f"  Difference: {analysis['mean_roi'] - gpp_analysis[0]['mean_roi']:.1f}% ROI")
            print(f"  P-value: {p_value:.4f} {sig_symbol}")
            print(
                f"  Effect size: {effect_size:.2f} ({'large' if abs(effect_size) > 0.8 else 'medium' if abs(effect_size) > 0.5 else 'small'})")

    # Cash Analysis
    print("\n\n💵 DEFINITIVE CASH RANKINGS")
    print("-" * 100)

    cash_analysis = []

    for strategy_name, results in cash_results.items():
        if not results:
            continue

        rois = [r['roi'] * 100 for r in results]

        analysis = {
            'strategy': strategy_name,
            'mean_roi': np.mean(rois),
            'win_rate': sum(r['cashed'] for r in results) / len(results) * 100,
            'ci_lower_wr': stats.binom.interval(0.95, len(results),
                                                sum(r['cashed'] for r in results) / len(results))[0] / len(
                results) * 100,
            'ci_upper_wr': stats.binom.interval(0.95, len(results),
                                                sum(r['cashed'] for r in results) / len(results))[1] / len(
                results) * 100,
            'consistency': np.std(rois),
            'sample_size': len(results)
        }

        cash_analysis.append(analysis)

    # Sort by win rate
    cash_analysis.sort(key=lambda x: x['win_rate'], reverse=True)

    print(f"\n{'Rank':<6} {'Strategy':<20} {'Win Rate':<12} {'95% CI':<20} {'ROI':<10}")
    print("-" * 100)

    for i, a in enumerate(cash_analysis):
        is_yours = "⭐" if "your_system" in a['strategy'] else "  "
        ci = f"({a['ci_lower_wr']:.1f}%, {a['ci_upper_wr']:.1f}%)"

        print(f"{is_yours}{i + 1:<4} {a['strategy']:<20} {a['win_rate']:>10.1f}% {ci:<20} "
              f"{a['mean_roi']:>8.1f}%")

    # Profitability threshold
    print(f"\n💡 Profitability threshold: 55.6% win rate")
    print(f"   Strategies above threshold: {sum(1 for a in cash_analysis if a['win_rate'] > 55.6)}")

    # Final recommendations
    print("\n" + "=" * 80)
    print("🏆 DEFINITIVE RECOMMENDATIONS")
    print("=" * 80)

    if gpp_analysis:
        best_gpp = gpp_analysis[0]
        print(f"\n🎯 BEST GPP STRATEGY: {best_gpp['strategy']}")
        print(
            f"   Expected ROI: {best_gpp['mean_roi']:.1f}% (95% CI: {best_gpp['ci_lower']:.0f}%-{best_gpp['ci_upper']:.0f}%)")
        print(f"   Win rate: {best_gpp['win_rate']:.1f}%")
        print(f"   Top 10% rate: {best_gpp['top_10_rate']:.1f}%")

        # Check if significantly better than your strategy
        your_gpp = next((a for a in gpp_analysis if 'your_system_gpp' in a['strategy']), None)
        if your_gpp and your_gpp['strategy'] != best_gpp['strategy']:
            diff = best_gpp['mean_roi'] - your_gpp['mean_roi']
            if diff > 30:
                print(f"\n   ⚠️  {best_gpp['strategy']} is {diff:.0f}% better than your strategy")
                print(f"   RECOMMENDATION: Consider switching to {best_gpp['strategy']}")
            else:
                print(f"\n   ✅ Your strategy is close enough ({diff:.0f}% difference)")
                print(f"   RECOMMENDATION: Stick with your optimized strategy")

    if cash_analysis:
        best_cash = cash_analysis[0]
        print(f"\n💵 BEST CASH STRATEGY: {best_cash['strategy']}")
        print(
            f"   Win rate: {best_cash['win_rate']:.1f}% (95% CI: {best_cash['ci_lower_wr']:.1f}%-{best_cash['ci_upper_wr']:.1f}%)")
        print(f"   Expected ROI: {best_cash['mean_roi']:.1f}%")

        if best_cash['win_rate'] > 55.6:
            print(f"   ✅ PROFITABLE (above 55.6% threshold)")
        else:
            print(f"   ❌ NOT PROFITABLE")


def save_definitive_report(gpp_results, cash_results):
    """Save comprehensive report"""

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'definitive_strategy_report_{timestamp}.json'

    report = {
        'test_type': 'definitive_head_to_head',
        'timestamp': timestamp,
        'gpp_results_summary': {},
        'cash_results_summary': {},
        'recommendations': {}
    }

    # Process results
    for strategy_name, results in gpp_results.items():
        if results:
            rois = [r['roi'] * 100 for r in results]
            report['gpp_results_summary'][strategy_name] = {
                'mean_roi': np.mean(rois),
                'ci_95': [np.percentile(rois, 2.5), np.percentile(rois, 97.5)],
                'sample_size': len(results),
                'win_rate': sum(r['rank'] == 1 for r in results) / len(results) * 100
            }

    for strategy_name, results in cash_results.items():
        if results:
            report['cash_results_summary'][strategy_name] = {
                'win_rate': sum(r['cashed'] for r in results) / len(results) * 100,
                'mean_roi': np.mean([r['roi'] * 100 for r in results]),
                'sample_size': len(results)
            }

    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n💾 Definitive report saved to: {filename}")


if __name__ == "__main__":
    # Set seeds for reproducibility
    random.seed(42)
    np.random.seed(42)

    # Run the definitive test
    run_definitive_comparison_test()