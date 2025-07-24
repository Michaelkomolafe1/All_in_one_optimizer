#!/usr/bin/env python3
"""
OPTIMAL DFS SIMULATION CONFIGURATION
====================================
Run meaningful tests without waiting 30 minutes
"""

from fixed_complete_dfs_sim import FixedDFSContestSimulation
import time
import matplotlib.pyplot as plt
import json
from datetime import datetime


def run_statistical_test():
    """
    Run different iteration counts to show convergence
    """
    print("🔬 TESTING CONVERGENCE OF RESULTS")
    print("=" * 60)
    print("Running multiple simulations to show when results stabilize\n")

    iteration_counts = [25, 50, 100, 200]
    results_by_iteration = {}

    for num_iter in iteration_counts:
        print(f"\nRunning {num_iter} iterations...")
        start_time = time.time()

        sim = FixedDFSContestSimulation(verbose=False, debug=False)
        sim.run_simulation(num_iterations=num_iter)

        elapsed = time.time() - start_time
        print(f"Completed in {elapsed:.1f} seconds")

        if sim.results:
            # Extract key metrics
            strategy_scores = {}
            for result in sim.results:
                if result.contest_type == 'gpp':
                    if result.strategy not in strategy_scores:
                        strategy_scores[result.strategy] = []
                    strategy_scores[result.strategy].append(result.roi)

            # Calculate average ROI for each strategy
            avg_rois = {}
            for strategy, rois in strategy_scores.items():
                avg_rois[strategy] = sum(rois) / len(rois) * 100 if rois else 0

            results_by_iteration[num_iter] = avg_rois

    # Show convergence
    print("\n\n📊 CONVERGENCE ANALYSIS")
    print("=" * 60)
    print("Average GPP ROI by iteration count:\n")

    # Get all strategies
    all_strategies = set()
    for avg_rois in results_by_iteration.values():
        all_strategies.update(avg_rois.keys())

    # Print convergence table
    print(f"{'Strategy':<20}", end="")
    for num_iter in iteration_counts:
        print(f"{num_iter:>8}", end="")
    print("\n" + "-" * 60)

    for strategy in sorted(all_strategies):
        print(f"{strategy:<20}", end="")
        for num_iter in iteration_counts:
            roi = results_by_iteration.get(num_iter, {}).get(strategy, 0)
            print(f"{roi:>7.1f}%", end="")
        print()

    print("\n💡 INSIGHT: Results typically stabilize around 100-200 iterations")
    print("   Running 1000 iterations provides minimal additional accuracy")


def run_focused_comparison():
    """
    Run a focused test comparing just the top strategies
    """
    print("\n\n🎯 FOCUSED COMPARISON MODE")
    print("=" * 60)
    print("Comparing your correlation strategy vs top alternatives\n")

    # Run 150 iterations - good balance of speed and accuracy
    sim = FixedDFSContestSimulation(verbose=False, debug=False)

    print("Running 150 iterations (should take ~4-5 minutes)...")
    start_time = time.time()

    sim.run_simulation(num_iterations=150)

    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed:.1f} seconds ({elapsed / 60:.1f} minutes)")

    # Analyze results
    sim.analyze_results()

    return sim.results


def provide_actionable_insights(results):
    """
    Provide specific recommendations based on results
    """
    print("\n\n🎮 ACTIONABLE INSIGHTS")
    print("=" * 60)

    # Analyze your strategy's performance
    your_gpp_rois = []
    your_cash_rates = []

    for result in results:
        if result.strategy == 'your_correlation':
            if result.contest_type == 'gpp':
                your_gpp_rois.append(result.roi)
            else:
                your_cash_rates.append(1 if result.payout > 0 else 0)

    if your_gpp_rois:
        avg_gpp_roi = sum(your_gpp_rois) / len(your_gpp_rois) * 100
        cash_rate = sum(your_cash_rates) / len(your_cash_rates) * 100 if your_cash_rates else 0

        print(f"\nYour Correlation Strategy Performance:")
        print(f"  GPP ROI: {avg_gpp_roi:+.1f}%")
        print(f"  Cash Rate: {cash_rate:.1f}%")

        print("\n📋 RECOMMENDATIONS:")

        if avg_gpp_roi > 10:
            print("  ✅ Excellent GPP performance - keep using this strategy!")
        elif avg_gpp_roi > 0:
            print("  👍 Positive GPP ROI - strategy is profitable")
            print("  💡 Consider increasing stacking for higher upside")
        else:
            print("  ⚠️  Negative GPP ROI - needs adjustment")
            print("  💡 Try increasing team total threshold or boost multipliers")

        if cash_rate > 55:
            print("  ✅ Strong cash game performance")
        elif cash_rate > 50:
            print("  👍 Decent cash performance")
        else:
            print("  ⚠️  Cash rate below 50% - be cautious in 50/50s")
            print("  💡 Consider more conservative multipliers for cash games")


def main():
    """
    Run optimal simulation configuration
    """
    print("🚀 OPTIMAL DFS SIMULATION RUNNER")
    print("This provides meaningful results in reasonable time\n")

    # Option 1: Quick convergence test (2-3 minutes)
    print("Option 1: Run convergence analysis? (y/n)")
    if input().lower() == 'y':
        run_statistical_test()

    # Option 2: Focused comparison (4-5 minutes)
    print("\nOption 2: Run focused 150-iteration comparison? (y/n)")
    if input().lower() == 'y':
        results = run_focused_comparison()
        provide_actionable_insights(results)

    print("\n\n✅ COMPLETE!")
    print("\nRemember: DFS success depends on many factors:")
    print("  • Player projections accuracy")
    print("  • Ownership projections")
    print("  • Contest selection")
    print("  • Bankroll management")
    print("  • Multi-entry strategy")
    print("\nThis simulation helps identify which scoring approach")
    print("has the best theoretical foundation.")


if __name__ == "__main__":
    main()