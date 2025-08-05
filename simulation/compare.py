# test_robustness_comparison.py
# Save in simulation folder and run to compare your ROBUST strategies vs NEW strategies

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.robust_dfs_simulator import generate_slate, simulate_lineup_score, generate_field
from strategies.data_driven_cash_strategy import build_data_driven_cash
from strategies.correlation_gpp_strategy import build_correlation_gpp
import numpy as np

# Import your ROBUST strategies
# Assuming they're in your simulation or config folder
from config.simulation_test.dfs_optimizer_integration import (
    build_balanced_optimal,
    build_smart_stack,
    build_truly_smart_stack,
    build_game_stack_4_2,
    build_game_stack_3_2
)


def quick_strategy_comparison(num_slates=50):
    """Quick comparison of strategies without optimization"""

    print("\n" + "=" * 80)
    print("🔬 ROBUSTNESS COMPARISON TEST")
    print("=" * 80)
    print("\nComparing your CURRENT ROBUST strategies vs NEW DATA-DRIVEN strategies")
    print(f"Testing {num_slates} slates per strategy...\n")

    # Define what to test
    cash_matchups = {
        'current_robust_cash': build_balanced_optimal,  # Your robust cash
        'new_data_driven_cash': build_data_driven_cash  # New cash
    }

    gpp_matchups = {
        'current_smart_stack': build_smart_stack,  # Your robust GPP
        'current_truly_smart': build_truly_smart_stack,  # Your newer GPP
        'new_correlation_gpp': build_correlation_gpp  # New GPP
    }

    results = {
        'cash': {},
        'gpp': {}
    }

    # Test CASH strategies
    print("Testing CASH strategies...")
    for strategy_name, strategy_func in cash_matchups.items():
        wins = 0
        total_roi = 0
        scores = []

        for i in range(num_slates):
            slate = generate_slate(i * 1000, 'classic', 'medium')

            try:
                lineup = strategy_func(slate['players'])
                if lineup:
                    score = simulate_lineup_score(lineup)

                    # Quick field of 100
                    field = generate_field(slate, 100, 'cash')
                    field_scores = [simulate_lineup_score(f) for f in field]

                    all_scores = [score] + field_scores
                    all_scores.sort(reverse=True)
                    rank = all_scores.index(score) + 1

                    win = rank <= 44  # Top 44%
                    roi = 80 if win else -100

                    wins += win
                    total_roi += roi
                    scores.append(score)
            except:
                pass

        if scores:
            results['cash'][strategy_name] = {
                'win_rate': (wins / len(scores)) * 100,
                'avg_roi': total_roi / len(scores),
                'avg_score': np.mean(scores),
                'success_rate': (len(scores) / num_slates) * 100
            }

    # Test GPP strategies
    print("\nTesting GPP strategies...")
    for strategy_name, strategy_func in gpp_matchups.items():
        wins = 0
        total_roi = 0
        scores = []
        top_10s = 0

        for i in range(num_slates):
            slate = generate_slate(i * 2000, 'classic', 'large')

            try:
                lineup = strategy_func(slate['players'])
                if lineup:
                    score = simulate_lineup_score(lineup)

                    # Quick field of 1000
                    field = generate_field(slate, 1000, 'gpp')
                    field_scores = [simulate_lineup_score(f) for f in field]

                    all_scores = [score] + field_scores
                    all_scores.sort(reverse=True)
                    rank = all_scores.index(score) + 1

                    if rank == 1:
                        roi = 900
                    elif rank <= 30:
                        roi = 400
                    elif rank <= 100:
                        roi = 100
                        top_10s += 1
                    elif rank <= 200:
                        roi = 0
                    else:
                        roi = -100

                    win = rank <= 200
                    wins += win
                    total_roi += roi
                    scores.append(score)
            except:
                pass

        if scores:
            results['gpp'][strategy_name] = {
                'win_rate': (wins / len(scores)) * 100,
                'avg_roi': total_roi / len(scores),
                'avg_score': np.mean(scores),
                'top_10_rate': (top_10s / len(scores)) * 100,
                'success_rate': (len(scores) / num_slates) * 100
            }

    # Print results
    print("\n" + "=" * 80)
    print("📊 RESULTS")
    print("=" * 80)

    print("\n💰 CASH STRATEGIES:")
    print(f"{'Strategy':<30} {'Win%':>8} {'ROI':>8} {'Score':>8} {'Success':>8}")
    print("-" * 60)

    for name, stats in results['cash'].items():
        marker = "🆕" if "new" in name else "📦"
        print(f"{marker} {name:<27} {stats['win_rate']:>7.1f}% {stats['avg_roi']:>+7.1f}% "
              f"{stats['avg_score']:>7.1f} {stats['success_rate']:>7.0f}%")

    # Find winner
    cash_winner = max(results['cash'].items(), key=lambda x: x[1]['win_rate'])
    print(f"\n🏆 CASH WINNER: {cash_winner[0]} ({cash_winner[1]['win_rate']:.1f}% win rate)")

    print("\n\n🎯 GPP STRATEGIES:")
    print(f"{'Strategy':<30} {'Win%':>8} {'ROI':>8} {'Top10%':>8} {'Score':>8}")
    print("-" * 70)

    for name, stats in results['gpp'].items():
        marker = "🆕" if "new" in name else "📦"
        print(f"{marker} {name:<27} {stats['win_rate']:>7.1f}% {stats['avg_roi']:>+7.1f}% "
              f"{stats['top_10_rate']:>7.1f}% {stats['avg_score']:>7.1f}")

    # Find winner
    gpp_winner = max(results['gpp'].items(), key=lambda x: x[1]['avg_roi'])
    print(f"\n🏆 GPP WINNER: {gpp_winner[0]} ({gpp_winner[1]['avg_roi']:+.1f}% ROI)")

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("=" * 80)

    # Recommendations
    if "new" in cash_winner[0]:
        print("✅ The NEW data-driven cash strategy is better! Use it!")
    else:
        print("📦 Your current ROBUST cash strategy is still better.")
        print("   Consider adding elements from the new strategy:")
        print("   - Focus on 25%+ K-rate pitchers")
        print("   - Weight batting order more heavily")

    if "new" in gpp_winner[0]:
        print("✅ The NEW correlation GPP strategy is better! Use it!")
    else:
        print("📦 Your current ROBUST GPP strategy is still better.")
        print("   Consider adding elements from the new strategy:")
        print("   - Ensure 80%+ of lineups use 4-5 man stacks")
        print("   - Focus on 3-4 batting order correlation")


if __name__ == "__main__":
    print("""
    This test compares:
    - Your CURRENT robust strategies (already optimized)
    - The NEW data-driven strategies (based on tournament data)

    No optimization yet - just seeing who wins!
    """)

    slates = input("\nHow many slates to test? (20=quick, 50=standard, 100=thorough): ")

    try:
        num_slates = int(slates)
    except:
        num_slates = 50

    quick_strategy_comparison(num_slates)