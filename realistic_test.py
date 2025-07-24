#!/usr/bin/env python3
"""
ULTRA-REALISTIC DFS STRATEGY TEST WITH COMPREHENSIVE ANALYTICS
==============================================================
More realistic field simulation, detailed statistics, cash vs GPP analysis
"""

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import numpy as np
from collections import defaultdict, Counter
import json
from datetime import datetime
import random
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import pandas as pd

# Import your simulation
import sys
sys.path.append('/home/michael/Desktop/All_in_one_optimizer')
from fixed_complete_dfs_sim import *

class RealisticFieldSimulator:
    """More realistic opponent modeling"""

    def __init__(self):
        # Real DFS player skill distribution (from industry data)
        self.skill_distribution = {
            'sharks': 0.02,  # 2% are pros/sharks
            'regs': 0.08,  # 8% are solid regulars
            'semi_regs': 0.15,  # 15% semi-regulars
            'decent': 0.25,  # 25% decent players
            'casual': 0.35,  # 35% casual players
            'weak': 0.15  # 15% weak/new players
        }

        # Lineup quality by player type (relative to optimal)
        self.quality_ranges = {
            'sharks': (0.92, 1.05),  # Can exceed optimal with correlation
            'regs': (0.85, 0.98),
            'semi_regs': (0.80, 0.93),
            'decent': (0.75, 0.88),
            'casual': (0.65, 0.82),
            'weak': (0.55, 0.75)
        }

        # Correlation usage by player type
        self.correlation_usage = {
            'sharks': 0.95,  # Almost always use correlation
            'regs': 0.75,
            'semi_regs': 0.50,
            'decent': 0.30,
            'casual': 0.15,
            'weak': 0.05
        }

    def generate_opponent_score(self, optimal_score, player_type, use_correlation=None):
        """Generate realistic opponent score"""
        quality_min, quality_max = self.quality_ranges[player_type]
        base_quality = random.uniform(quality_min, quality_max)

        # Determine if they use correlation
        if use_correlation is None:
            use_correlation = random.random() < self.correlation_usage[player_type]

        # Apply correlation bonus if used
        if use_correlation:
            # Correlation can push scores above "optimal" single-lineup score
            correlation_bonus = random.uniform(1.02, 1.12)
            base_quality *= correlation_bonus

        # Add natural variance
        variance = random.gauss(1.0, 0.05)

        return optimal_score * base_quality * variance


def simulate_realistic_contest(players, games, strategy, contest_type, slate_config,
                               strategy_name, field_simulator):
    """Enhanced contest simulation with realistic field"""

    slate_context = {
        'contest_type': contest_type,
        'num_games': slate_config.num_games,
        'games': games
    }

    # Create temporary sim object
    sim = ComprehensiveValidatedSimulation(verbose=False)

    # Build our lineup
    result = sim.build_optimized_lineup(players, strategy, slate_context)
    if not result:
        return None

    our_lineup, our_proj_score = result

    # Generate actual scores
    actual_scores = sim.simulate_actual_scores(players, games, slate_config)
    our_actual = sum(actual_scores[p.name] for p in our_lineup)

    # Apply correlation
    team_counts = defaultdict(int)
    for p in our_lineup:
        if p.position != 'P':
            team_counts[p.team] += 1

    max_stack = max(team_counts.values()) if team_counts else 0
    correlation_multiplier = 1.0

    if max_stack >= 5:
        correlation_multiplier = random.uniform(1.06, 1.10)
    elif max_stack >= 4:
        correlation_multiplier = random.uniform(1.04, 1.07)
    elif max_stack >= 3:
        correlation_multiplier = random.uniform(1.02, 1.04)

    our_actual *= correlation_multiplier

    # Different field sizes for different contest types
    if contest_type == 'gpp':
        # Various GPP sizes
        contest_size = random.choice([100, 500, 1000, 5000, 10000])
        if contest_size >= 5000:
            contest_name = 'large_gpp'
        elif contest_size >= 1000:
            contest_name = 'medium_gpp'
        else:
            contest_name = 'small_gpp'
    else:
        # Cash game types
        contest_type_roll = random.random()
        if contest_type_roll < 0.5:
            contest_size = 10  # Head to head
            contest_name = 'h2h'
        elif contest_type_roll < 0.8:
            contest_size = 50  # 50/50
            contest_name = '50_50'
        else:
            contest_size = 100  # Double up
            contest_name = 'double_up'

    # Generate realistic field
    field_scores = []

    # Sample field with realistic distribution
    for i in range(contest_size):
        # Determine player skill
        roll = random.random()
        cumulative = 0
        player_type = 'weak'

        for ptype, prob in field_simulator.skill_distribution.items():
            cumulative += prob
            if roll < cumulative:
                player_type = ptype
                break

        # Generate their score
        opponent_score = field_simulator.generate_opponent_score(
            our_actual / correlation_multiplier,  # Base optimal score
            player_type
        )
        field_scores.append(opponent_score)

    # Add our score
    field_scores.append(our_actual)
    field_scores.sort(reverse=True)

    # Calculate placement
    our_rank = field_scores.index(our_actual) + 1
    percentile = (1 - our_rank / len(field_scores)) * 100

    # Realistic payout structures
    if 'gpp' in contest_name:
        payout, entry_fee = calculate_gpp_payout(our_rank, contest_size)
    else:
        payout, entry_fee = calculate_cash_payout(our_rank, contest_size, contest_name)

    roi = (payout - entry_fee) / entry_fee if entry_fee > 0 else 0

    # Detailed metrics
    return {
        'score': our_actual,
        'rank': our_rank,
        'field_size': contest_size,
        'percentile': percentile,
        'payout': payout,
        'entry_fee': entry_fee,
        'roi': roi,
        'cashed': payout > 0,
        'min_cash': payout > 0 and payout <= entry_fee * 2,
        'big_win': payout > entry_fee * 5,
        'top_1_pct': percentile >= 99,
        'top_10_pct': percentile >= 90,
        'max_stack': max_stack,
        'contest_type': contest_type,
        'contest_name': contest_name,
        'correlation_used': correlation_multiplier > 1.0,
        'field_scores': field_scores[:10],  # Top 10 for analysis
        'score_differential': our_actual - field_scores[0]  # vs winner
    }


def calculate_gpp_payout(rank, field_size):
    """Realistic GPP payout structures"""

    # Entry fees by size
    if field_size >= 10000:
        entry_fee = 3  # Mass multi-entry
    elif field_size >= 1000:
        entry_fee = 20  # Standard GPP
    else:
        entry_fee = 50  # Smaller field, higher stakes

    # Payout percentages (top heavy)
    total_pool = field_size * entry_fee * 0.82  # 18% rake

    if rank == 1:
        payout = total_pool * 0.20  # First gets 20%
    elif rank == 2:
        payout = total_pool * 0.10
    elif rank == 3:
        payout = total_pool * 0.06
    elif rank <= 10:
        payout = total_pool * 0.02
    elif rank <= field_size * 0.01:  # Top 1%
        payout = total_pool * 0.002
    elif rank <= field_size * 0.10:  # Top 10%
        payout = total_pool * 0.0005
    elif rank <= field_size * 0.20:  # Top 20%
        payout = entry_fee * 2.5  # Min cash
    else:
        payout = 0

    return payout, entry_fee


def calculate_cash_payout(rank, field_size, contest_name):
    """Realistic cash game payouts"""

    if contest_name == 'h2h':
        entry_fee = 50
        payout = 90 if rank == 1 else 0  # Winner takes all minus rake
    elif contest_name == '50_50':
        entry_fee = 20
        payout = 36 if rank <= field_size // 2 else 0  # Top 50% win
    else:  # double_up
        entry_fee = 50
        payout = 90 if rank <= field_size * 0.45 else 0  # Top 45% double

    return payout, entry_fee


def process_realistic_contest_batch(args):
    """Process a single contest with realistic field"""
    players, games, strategy, contest_type, slate_config, strategy_name = args

    field_simulator = RealisticFieldSimulator()

    try:
        result = simulate_realistic_contest(
            players, games, strategy, contest_type, slate_config,
            strategy_name, field_simulator
        )
        return (strategy_name, contest_type, result)
    except Exception as e:
        print(f"Error in {strategy_name}: {str(e)}")
        return (strategy_name, contest_type, None)


def run_comprehensive_realistic_test():
    """Ultra-realistic test with detailed analytics"""

    print("🚀 ULTRA-REALISTIC DFS STRATEGY TEST")
    print("=" * 80)
    print("Enhanced features:")
    print("  • Realistic player skill distribution")
    print("  • Proper correlation modeling")
    print("  • Multiple contest types (H2H, 50/50, GPPs)")
    print("  • Detailed win/loss statistics")
    print("  • Variance and streak analysis")
    print(f"  • Using {mp.cpu_count()} CPU cores")
    print("=" * 80)

    # Create simulation
    sim = ComprehensiveValidatedSimulation(verbose=False)

    # Test parameters
    iterations_per_slate = 30  # More iterations for better statistics
    slates_to_test = ['Main Slate', 'Small Slate']  # Focus on main types

    # Filter strategies to most relevant
    strategies_to_test = [
        'pure_projections',
        'value_optimized',
        'ownership_leverage',
        'historical_optimized',
        'advanced_sabermetrics',
        'ml_ensemble',
        'stacks_only',
        'cash_optimized',
        'your_system_gpp',
        'your_system_cash'
    ]

    sim.strategies = {k: v for k, v in sim.strategies.items() if k in strategies_to_test}
    sim.contest_configs = [c for c in sim.contest_configs if c.name in slates_to_test]

    print(f"\nTesting {len(sim.strategies)} strategies")
    print(f"Slates: {len(sim.contest_configs)}")
    print(f"Iterations per slate: {iterations_per_slate}")
    print(f"Contest types: GPP (various sizes) + Cash (H2H, 50/50, Double-up)")

    # Prepare all tasks
    all_tasks = []

    for slate_config in sim.contest_configs:
        print(f"\nPreparing {slate_config.name}...")

        # Pre-generate slates
        slates = []
        for i in range(iterations_per_slate):
            players, games = sim.generate_realistic_slate(slate_config)
            slates.append((players, games))

        # Create tasks
        for iteration in range(iterations_per_slate):
            players, games = slates[iteration % len(slates)]

            for strategy_name, strategy in sim.strategies.items():
                # Test both GPP and cash for all strategies
                for contest_type in ['gpp', 'cash']:
                    # Skip mismatched strategy/contest combos
                    if 'cash' in strategy_name and contest_type == 'gpp':
                        continue
                    if 'gpp' in strategy_name and contest_type == 'cash':
                        continue

                    all_tasks.append((
                        players, games, strategy, contest_type,
                        slate_config, strategy_name
                    ))

    print(f"\nTotal simulations: {len(all_tasks)}")
    print("\n⚡ Running parallel simulations...")

    # Process with multicore
    all_results = defaultdict(lambda: defaultdict(list))
    completed = 0
    start_time = time.time()

    num_workers = min(16, mp.cpu_count() - 2)

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(process_realistic_contest_batch, task): task
                   for task in all_tasks}

        for future in as_completed(futures):
            completed += 1

            if completed % 50 == 0 or completed == len(all_tasks):
                elapsed = time.time() - start_time
                rate = completed / elapsed
                remaining = (len(all_tasks) - completed) / rate
                print(f"\rProgress: {completed}/{len(all_tasks)} "
                      f"({completed / len(all_tasks) * 100:.0f}%) "
                      f"ETA: {remaining / 60:.1f} min",
                      end='', flush=True)

            try:
                strategy_name, contest_type, result = future.result()
                if result:
                    key = f"{strategy_name}_{contest_type}"
                    all_results[strategy_name][key].append(result)
            except Exception as e:
                print(f"\nError: {e}")

    total_time = time.time() - start_time
    print(f"\n\n✅ Completed in {total_time / 60:.1f} minutes!")

    # Analyze results
    analyze_comprehensive_results(all_results)


def analyze_comprehensive_results(all_results):
    """Comprehensive analysis with detailed statistics"""

    print("\n" + "=" * 100)
    print("📊 COMPREHENSIVE REALISTIC RESULTS")
    print("=" * 100)

    # Separate GPP and Cash analysis
    gpp_analysis = analyze_contest_type(all_results, 'gpp', 'GPP TOURNAMENTS')
    cash_analysis = analyze_contest_type(all_results, 'cash', 'CASH GAMES')

    # Strategy comparison
    print("\n" + "=" * 100)
    print("🎯 STRATEGY COMPARISON")
    print("=" * 100)

    comparison_df = create_comparison_table(gpp_analysis, cash_analysis)
    print(comparison_df.to_string())

    # Statistical significance testing
    print("\n" + "=" * 100)
    print("📈 STATISTICAL SIGNIFICANCE TESTING")
    print("=" * 100)

    test_significance(all_results)

    # Best practices summary
    print("\n" + "=" * 100)
    print("💡 KEY INSIGHTS & RECOMMENDATIONS")
    print("=" * 100)

    provide_recommendations(gpp_analysis, cash_analysis)

    # Save detailed results
    save_detailed_results(all_results, gpp_analysis, cash_analysis)


def analyze_contest_type(all_results, contest_type, title):
    """Detailed analysis for specific contest type"""

    print(f"\n🎯 {title}")
    print("-" * 100)

    analyses = {}

    for strategy_name, results in all_results.items():
        # Find matching results
        matching_keys = [k for k in results.keys() if contest_type in k]

        if not matching_keys:
            continue

        # Combine all results for this contest type
        combined_results = []
        for key in matching_keys:
            combined_results.extend(results[key])

        if not combined_results:
            continue

        # Calculate comprehensive statistics
        rois = [r['roi'] * 100 for r in combined_results]
        scores = [r['score'] for r in combined_results]
        ranks = [r['rank'] for r in combined_results]
        cashed = [r['cashed'] for r in combined_results]
        big_wins = [r.get('big_win', False) for r in combined_results]

        analysis = {
            'strategy': strategy_name,
            'contests': len(combined_results),
            'avg_roi': np.mean(rois),
            'median_roi': np.median(rois),
            'std_roi': np.std(rois),
            'min_roi': np.min(rois),
            'max_roi': np.max(rois),
            'sharpe_ratio': np.mean(rois) / np.std(rois) if np.std(rois) > 0 else 0,
            'cash_rate': sum(cashed) / len(cashed) * 100,
            'avg_score': np.mean(scores),
            'avg_rank': np.mean(ranks),
            'top_10_pct': sum(r['top_10_pct'] for r in combined_results) / len(combined_results) * 100,
            'big_win_rate': sum(big_wins) / len(big_wins) * 100,
            'win_rate': sum(r['rank'] == 1 for r in combined_results) / len(combined_results) * 100,
            'max_stack_avg': np.mean([r['max_stack'] for r in combined_results]),
            'correlation_usage': sum(r.get('correlation_used', False) for r in combined_results) / len(
                combined_results) * 100
        }

        # Calculate streaks
        cash_streak = 0
        max_cash_streak = 0
        loss_streak = 0
        max_loss_streak = 0

        for cash in cashed:
            if cash:
                cash_streak += 1
                loss_streak = 0
                max_cash_streak = max(max_cash_streak, cash_streak)
            else:
                loss_streak += 1
                cash_streak = 0
                max_loss_streak = max(max_loss_streak, loss_streak)

        analysis['max_win_streak'] = max_cash_streak
        analysis['max_loss_streak'] = max_loss_streak

        analyses[strategy_name] = analysis

    # Sort by ROI
    sorted_analyses = sorted(analyses.values(), key=lambda x: x['avg_roi'], reverse=True)

    # Display results
    if contest_type == 'gpp':
        print(f"\n{'Strategy':<20} {'ROI%':<8} {'Sharpe':<8} {'Cash%':<8} {'Top10%':<8} "
              f"{'BigWin%':<9} {'MaxWin':<8} {'MaxLoss':<8}")
        print("-" * 100)

        for a in sorted_analyses:
            is_yours = "⭐" if "your_system" in a['strategy'] else "  "
            print(f"{is_yours}{a['strategy']:<18} {a['avg_roi']:>6.1f} {a['sharpe_ratio']:>7.2f} "
                  f"{a['cash_rate']:>7.1f} {a['top_10_pct']:>7.1f} {a['big_win_rate']:>8.1f} "
                  f"{a['max_win_streak']:>7} {a['max_loss_streak']:>7}")
    else:
        print(f"\n{'Strategy':<20} {'ROI%':<8} {'Cash%':<8} {'WinRate%':<10} "
              f"{'AvgRank':<9} {'MaxWin':<8} {'MaxLoss':<8}")
        print("-" * 100)

        for a in sorted_analyses:
            is_yours = "⭐" if "your_system" in a['strategy'] else "  "
            print(f"{is_yours}{a['strategy']:<18} {a['avg_roi']:>6.1f} {a['cash_rate']:>7.1f} "
                  f"{a['win_rate']:>9.1f} {a['avg_rank']:>8.1f} "
                  f"{a['max_win_streak']:>7} {a['max_loss_streak']:>7}")

    return analyses


def create_comparison_table(gpp_analysis, cash_analysis):
    """Create comparison table between GPP and Cash performance"""

    data = []

    for strategy in set(list(gpp_analysis.keys()) + list(cash_analysis.keys())):
        row = {'Strategy': strategy}

        if strategy in gpp_analysis:
            row['GPP_ROI'] = f"{gpp_analysis[strategy]['avg_roi']:.1f}%"
            row['GPP_Sharpe'] = f"{gpp_analysis[strategy]['sharpe_ratio']:.2f}"
            row['GPP_Cash%'] = f"{gpp_analysis[strategy]['cash_rate']:.1f}%"
        else:
            row['GPP_ROI'] = 'N/A'
            row['GPP_Sharpe'] = 'N/A'
            row['GPP_Cash%'] = 'N/A'

        if strategy in cash_analysis:
            row['Cash_ROI'] = f"{cash_analysis[strategy]['avg_roi']:.1f}%"
            row['Cash_Win%'] = f"{cash_analysis[strategy]['cash_rate']:.1f}%"
        else:
            row['Cash_ROI'] = 'N/A'
            row['Cash_Win%'] = 'N/A'

        data.append(row)

    df = pd.DataFrame(data)
    df = df.set_index('Strategy')
    return df


def test_significance(all_results):
    """Test statistical significance between strategies"""

    # Test your strategy vs baseline
    baseline = 'pure_projections'
    your_strategies = ['your_system_gpp', 'your_system_cash']

    for your_strat in your_strategies:
        if your_strat not in all_results:
            continue

        contest_type = 'gpp' if 'gpp' in your_strat else 'cash'

        # Get ROIs
        your_key = f"{your_strat}_{contest_type}"
        baseline_key = f"{baseline}_{contest_type}"

        if your_key in all_results[your_strat] and baseline_key in all_results[baseline]:
            your_rois = [r['roi'] for r in all_results[your_strat][your_key]]
            baseline_rois = [r['roi'] for r in all_results[baseline][baseline_key]]

            if len(your_rois) >= 10 and len(baseline_rois) >= 10:
                t_stat, p_value = stats.ttest_ind(your_rois, baseline_rois)

                print(f"\n{your_strat} vs {baseline}:")
                print(f"  Your mean ROI: {np.mean(your_rois) * 100:.1f}%")
                print(f"  Baseline ROI: {np.mean(baseline_rois) * 100:.1f}%")
                print(f"  Difference: {(np.mean(your_rois) - np.mean(baseline_rois)) * 100:.1f}%")
                print(f"  p-value: {p_value:.4f}")

                if p_value < 0.05:
                    print("  ✅ STATISTICALLY SIGNIFICANT!")
                else:
                    print("  ❌ Not statistically significant")


def provide_recommendations(gpp_analysis, cash_analysis):
    """Provide actionable recommendations"""

    # Find best strategies
    if gpp_analysis:
        best_gpp = max(gpp_analysis.values(), key=lambda x: x['avg_roi'])
        best_gpp_sharpe = max(gpp_analysis.values(), key=lambda x: x['sharpe_ratio'])

        print(f"\n🎯 GPP Recommendations:")
        print(f"  Best ROI: {best_gpp['strategy']} ({best_gpp['avg_roi']:.1f}%)")
        print(f"  Best Risk-Adjusted: {best_gpp_sharpe['strategy']} (Sharpe: {best_gpp_sharpe['sharpe_ratio']:.2f})")

        # Check your strategy
        your_gpp = gpp_analysis.get('your_system_gpp')
        if your_gpp:
            print(f"\n  Your GPP Strategy Performance:")
            print(
                f"    ROI: {your_gpp['avg_roi']:.1f}% (Rank: {sum(1 for s in gpp_analysis.values() if s['avg_roi'] > your_gpp['avg_roi']) + 1}/{len(gpp_analysis)})")
            print(f"    Uses correlation: {your_gpp['correlation_usage']:.0f}% of lineups")
            print(f"    Recommendation: ", end='')

            if your_gpp['avg_roi'] > 0:
                print("✅ Profitable - continue using!")
            else:
                print("❌ Not profitable - needs optimization")

    if cash_analysis:
        best_cash = max(cash_analysis.values(), key=lambda x: x['cash_rate'])
        best_cash_roi = max(cash_analysis.values(), key=lambda x: x['avg_roi'])

        print(f"\n💵 Cash Game Recommendations:")
        print(f"  Highest Win Rate: {best_cash['strategy']} ({best_cash['cash_rate']:.1f}%)")
        print(f"  Best ROI: {best_cash_roi['strategy']} ({best_cash_roi['avg_roi']:.1f}%)")

        # Minimum win rate for profitability
        print(f"\n  Profitability thresholds:")
        print(f"    H2H: Need >55.6% win rate (10% rake)")
        print(f"    50/50: Need >55.6% win rate")
        print(f"    Double-up: Need >55.6% win rate")


def save_detailed_results(all_results, gpp_analysis, cash_analysis):
    """Save comprehensive results"""

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'realistic_dfs_results_{timestamp}.json'

    # Prepare serializable data
    serializable_results = {}
    for strategy, data in all_results.items():
        serializable_results[strategy] = {}
        for key, results in data.items():
            serializable_results[strategy][key] = [
                {k: v for k, v in r.items() if k != 'field_scores'}
                for r in results
            ]

    output = {
        'test_configuration': {
            'timestamp': timestamp,
            'test_type': 'ultra_realistic',
            'features': [
                'realistic_field_strength',
                'multiple_contest_types',
                'correlation_modeling',
                'streak_analysis'
            ]
        },
        'gpp_analysis': gpp_analysis,
        'cash_analysis': cash_analysis,
        'raw_results': serializable_results
    }

    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n\n💾 Detailed results saved to: {filename}")


if __name__ == "__main__":
    # Set seeds for reproducibility
    random.seed(42)
    np.random.seed(42)

    # Run the comprehensive test
    run_comprehensive_realistic_test()