#!/usr/bin/env python3
"""
FOCUSED STRATEGY TESTING
========================
Test only strategies that have proven to work (80%+ success rate)
"""

import sys
import os
# Add this to your focused_strategy_test.py

import os
import sys
from collections import deque


def clear_screen():
    """Clear console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def draw_dashboard(current_slate, total_slates, results_count, failed_count, start_time, recent_activity):
    """Draw the status dashboard"""
    # Clear screen
    clear_screen()

    # Calculate progress
    progress = current_slate / total_slates if total_slates > 0 else 0
    progress_pct = progress * 100

    # Calculate time metrics
    elapsed = time.time() - start_time
    elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

    if current_slate > 0 and elapsed > 0:
        rate = current_slate / elapsed
        eta = (total_slates - current_slate) / rate if rate > 0 else 0
        eta_str = f"{int(eta // 60)}m {int(eta % 60)}s"
    else:
        eta_str = "calculating..."

    # Create progress bar
    bar_width = 20
    filled = int(bar_width * progress)
    bar = "█" * filled + "░" * (bar_width - filled)

    # Draw dashboard
    print("╔═══════════════════════════════════════╗")
    print("║      DFS STRATEGY TEST PROGRESS       ║")
    print("╠═══════════════════════════════════════╣")
    print(f"║ Progress:  {bar}  {progress_pct:3.0f}%   ║")
    print(f"║ Slates:    {current_slate:,} / {total_slates:,}".ljust(39) + "║")
    print(f"║ Results:   {results_count:,}".ljust(39) + "║")
    print(f"║ Time:      {elapsed_str} (ETA: {eta_str})".ljust(39) + "║")
    if failed_count > 0:
        print(f"║ ⚠️  Failed:   {failed_count}".ljust(39) + "║")
    print("╚═══════════════════════════════════════╝")

    # Show recent activity
    print("\nRecent activity:")
    for activity in recent_activity:
        print(activity)
    print()  # Extra line for spacing


# Modified run_focused_strategy_test function
def run_focused_strategy_test(num_slates=100, parallel=False):
    """Test only strategies that work well - WITH STATUS DASHBOARD"""

    print("\n" + "=" * 80)
    print("FOCUSED STRATEGY TESTING - WINNERS ONLY")
    print("=" * 80)

    # ... (keep existing STRATEGIES_TO_TEST definition) ...

    # Count strategies
    total_strategies = 0
    for format_type in STRATEGIES_TO_TEST:
        if format_type == 'classic':
            for contest_type in STRATEGIES_TO_TEST[format_type]:
                total_strategies += len(STRATEGIES_TO_TEST[format_type][contest_type])
        else:  # showdown
            for contest_type in STRATEGIES_TO_TEST[format_type]:
                total_strategies += len(STRATEGIES_TO_TEST[format_type][contest_type])

    print(f"\n📊 Configuration:")
    print(f"   • Slates to test: {num_slates}")
    print(f"   • Strategies: {total_strategies}")
    print(f"   • Contests per slate: 2 (cash + GPP)")

    input("\nPress Enter to start...")  # Give user a chance to see config

    start_time = time.time()

    # Create slate configurations
    slate_configs = []

    # Classic slates - test on all sizes
    for slate_size in ['small', 'medium', 'large']:
        for i in range(num_slates):
            slate_id = (i * 1000 + abs(hash(slate_size))) % (2 ** 31 - 1)
            slate_configs.append((slate_id, 'classic', slate_size))

    # Showdown slates
    for i in range(num_slates // 3):
        slate_id = (i * 2000) % (2 ** 31 - 1)
        slate_configs.append((slate_id, 'showdown', 'showdown'))

    # Contest configurations
    contest_configs = [
        ('cash', 100),
        ('gpp', 1000),
    ]

    all_results = []
    completed_slates = 0
    failed_count = 0

    # Track recent activity (last 10 lines)
    recent_activity = deque(maxlen=10)

    # Process simulations
    for i, (slate_id, format_type, slate_size) in enumerate(slate_configs):
        # Update dashboard
        draw_dashboard(i, len(slate_configs), len(all_results), failed_count,
                       start_time, recent_activity)

        # Generate slate
        slate = generate_slate(slate_id, format_type, slate_size if format_type == 'classic' else 'showdown')

        if not slate or not slate.get('players'):
            failed_count += 1
            recent_activity.append(f"❌ Failed to generate slate {slate_id}")
            continue

        # Add to recent activity
        recent_activity.append(f"✓ Generated {slate_size} slate #{i + 1} - {len(slate['players'])} players")

        # Get strategies for this configuration
        if format_type == 'showdown':
            strategies_dict = STRATEGIES_TO_TEST['showdown']
        else:
            strategies_dict = STRATEGIES_TO_TEST['classic']

        # Test each strategy in each contest type
        strategies_tested = 0
        for contest_type, field_size in contest_configs:
            if contest_type in strategies_dict:
                for strategy_name, strategy_config in strategies_dict[contest_type].items():
                    strategies_tested += 1
                    recent_activity.append(f"  → Testing {strategy_name} ({contest_type})...")

                    # Update dashboard to show current strategy
                    draw_dashboard(i, len(slate_configs), len(all_results), failed_count,
                                   start_time, recent_activity)

                    try:
                        result = simulate_contest(
                            slate,
                            strategy_name,
                            strategy_config,
                            contest_type,
                            field_size
                        )

                        if result:
                            all_results.append(result)
                            recent_activity.append(f"  ✓ {strategy_name}: Rank {result['rank']}/{field_size}")

                    except Exception as e:
                        failed_count += 1
                        recent_activity.append(f"  ❌ {strategy_name} failed: {str(e)[:50]}")

        completed_slates += 1

        # Milestone notification every 10%
        if i > 0 and (i * 100 // len(slate_configs)) % 10 == 0:
            milestone_pct = (i * 100 // len(slate_configs))
            recent_activity.append(f"🎯 ═══ {milestone_pct}% MILESTONE REACHED! ═══")

    # Final update
    draw_dashboard(len(slate_configs), len(slate_configs), len(all_results),
                   failed_count, start_time, recent_activity)

    # Complete
    elapsed = time.time() - start_time
    print(f"\n✅ Simulation complete in {elapsed:.1f} seconds")
    print(f"📊 Total results: {len(all_results):,}")
    if failed_count > 0:
        print(f"⚠️  Failed tests: {failed_count}")

    # Analyze results
    if all_results:
        input("\nPress Enter to see results analysis...")
        analyze_focused_results(all_results)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'focused_strategy_test_{timestamp}.json'

        save_data = {
            'metadata': {
                'timestamp': timestamp,
                'duration_seconds': elapsed,
                'num_slates': num_slates,
                'total_results': len(all_results),
                'strategies_tested': STRATEGIES_TO_TEST
            },
            'results': all_results
        }

        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)

        print(f"\n💾 Results saved to: {filename}")

    return all_results
# Add the parent directory to the path so we can import robust_dfs_simulator
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import what we need from your simulator
try:
    from robust_dfs_simulator import (
        generate_slate, simulate_contest, create_lineup_dict,
        build_value_floor, build_chalk_plus, build_safe_correlation,
        build_diversified_chalk, build_ceiling_stack, build_correlation_value,
        build_contrarian_correlation, build_balanced_showdown, build_leverage_captain,
        CLASSIC_CONFIG, SHOWDOWN_CONFIG
    )
except ImportError as e:
    print(f"Error importing from robust_dfs_simulator: {e}")
    print("Make sure robust_dfs_simulator.py is in the same directory")
    sys.exit(1)

import numpy as np
import json
import time
from datetime import datetime
from collections import defaultdict


# In focused_strategy_test.py, modify the run_focused_strategy_test function:


# Define which strategies to test based on performance
STRATEGIES_TO_TEST = {
    'classic': {
        'cash': {
            'value_floor': {
                'name': 'Value Floor',
                'type': 'value_floor',
                'description': 'High floor value plays',
                'avg_success': '93%'
            },
            'chalk_plus': {
                'name': 'Chalk Plus',
                'type': 'chalk_plus',
                'description': 'Popular plays with differentiation',
                'avg_success': '93%'
            },
            'safe_correlation': {
                'name': 'Safe Correlation',
                'type': 'safe_correlation',
                'description': 'Mini-stacks from multiple games',
                'avg_success': '93%'
            },
            'diversified_chalk': {
                'name': 'Diversified Chalk',
                'type': 'diversified_chalk',
                'description': 'Spread ownership across games',
                'avg_success': '93%'
            }
        },
        'gpp': {
            'ceiling_stack': {
                'name': 'Ceiling Stack',
                'type': 'ceiling_stack',
                'description': 'Maximum upside correlation',
                'avg_success': '100%'
            },
            'correlation_value': {
                'name': 'Correlation Value',
                'type': 'correlation_value',
                'description': 'Value-based with game correlation',
                'avg_success': '97%'
            },
            'contrarian_correlation': {
                'name': 'Contrarian Correlation',
                'type': 'contrarian_correlation',
                'description': 'Low owned game stacks',
                'avg_success': '57%',
                'note': 'Included for GPP diversity despite lower success'
            }
        }
    },
    'showdown': {
        'cash': {
            'balanced_showdown': {
                'name': 'Balanced Showdown',
                'type': 'balanced_showdown',
                'description': 'Optimal captain selection',
                'avg_success': '100%'
            }
        },
        'gpp': {
            'leverage_captain': {
                'name': 'Leverage Captain',
                'type': 'leverage_captain',
                'description': 'Low owned captain with upside',
                'avg_success': '100%'
            }
        }
    }
}

def run_focused_strategy_test(num_slates=100, parallel=False):
    """Test only strategies that work well (80%+ success rate) - WITH CLEAN PROGRESS"""

    print("\n" + "=" * 80)
    print("FOCUSED STRATEGY TESTING - WINNERS ONLY")
    print("=" * 80)

    # Define strategies (keep existing STRATEGIES_TO_TEST)
    # ... existing strategy definitions ...

    # Count strategies
    total_strategies = 0
    for format_type in STRATEGIES_TO_TEST:
        if format_type == 'classic':
            for contest_type in STRATEGIES_TO_TEST[format_type]:
                total_strategies += len(STRATEGIES_TO_TEST[format_type][contest_type])
        else:  # showdown
            for contest_type in STRATEGIES_TO_TEST[format_type]:
                total_strategies += len(STRATEGIES_TO_TEST[format_type][contest_type])

    print(f"\n📊 Configuration:")
    print(f"   • Slates to test: {num_slates}")
    print(f"   • Strategies: {total_strategies}")
    print(f"   • Contests per slate: 2 (cash + GPP)")

    start_time = time.time()

    # Create slate configurations
    slate_configs = []

    # Classic slates - test on all sizes
    for slate_size in ['small', 'medium', 'large']:
        for i in range(num_slates):
            slate_id = (i * 1000 + abs(hash(slate_size))) % (2 ** 31 - 1)
            slate_configs.append((slate_id, 'classic', slate_size))

    # Showdown slates
    for i in range(num_slates // 3):  # Fewer showdown slates
        slate_id = (i * 2000) % (2 ** 31 - 1)
        slate_configs.append((slate_id, 'showdown', 'showdown'))

    # Contest configurations
    contest_configs = [
        ('cash', 100),  # 100-person double-up
        ('gpp', 1000),  # 1000-person tournament
    ]

    total_tests = len(slate_configs) * 2 * (total_strategies // 2)  # Approximate
    print(f"\n🎮 Starting {total_tests} tests...\n")

    all_results = []
    completed_slates = 0
    failed_count = 0

    # Temporarily redirect debug output
    import os
    import sys

    class SuppressDebug:
        def __init__(self):
            self.terminal = sys.stdout

        def write(self, message):
            # Filter out DEBUG messages
            if not message.startswith('DEBUG:') and message.strip():
                self.terminal.write(message)

        def flush(self):
            self.terminal.flush()

    # Process simulations with clean progress
    original_stdout = sys.stdout
    sys.stdout = SuppressDebug()

    try:
        for i, (slate_id, format_type, slate_size) in enumerate(slate_configs):
            # Clean progress update
            progress_pct = (i / len(slate_configs)) * 100
            original_stdout.write(
                f"\r⚡ Progress: {i + 1}/{len(slate_configs)} slates ({progress_pct:.1f}%) | Results: {len(all_results)} | Failed: {failed_count}")
            original_stdout.flush()

            # Generate slate
            slate = generate_slate(slate_id, format_type, slate_size if format_type == 'classic' else 'showdown')

            if not slate or not slate.get('players'):
                failed_count += 1
                continue

            # Get strategies for this configuration
            if format_type == 'showdown':
                strategies_dict = STRATEGIES_TO_TEST['showdown']
            else:
                strategies_dict = STRATEGIES_TO_TEST['classic']

            # Test each strategy in each contest type
            for contest_type, field_size in contest_configs:
                if contest_type in strategies_dict:
                    for strategy_name, strategy_config in strategies_dict[contest_type].items():
                        try:
                            result = simulate_contest(
                                slate,
                                strategy_name,
                                strategy_config,
                                contest_type,
                                field_size
                            )

                            if result:
                                all_results.append(result)

                        except Exception as e:
                            failed_count += 1

            completed_slates += 1

            # Periodic detailed update every 10%
            if i > 0 and i % max(1, len(slate_configs) // 10) == 0:
                elapsed = time.time() - start_time
                rate = completed_slates / elapsed
                eta = (len(slate_configs) - completed_slates) / rate if rate > 0 else 0

                original_stdout.write(
                    f"\n📊 Checkpoint: {completed_slates} slates done | {len(all_results)} results | ETA: {eta:.0f}s\n")
                original_stdout.flush()

    finally:
        # Restore stdout
        sys.stdout = original_stdout

    # Complete
    elapsed = time.time() - start_time
    print(f"\n\n✅ Simulation complete in {elapsed:.1f} seconds")
    print(f"📊 Total results: {len(all_results):,}")
    if failed_count > 0:
        print(f"⚠️  Failed tests: {failed_count}")

    # Analyze results
    if all_results:
        analyze_focused_results(all_results)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'focused_strategy_test_{timestamp}.json'

        save_data = {
            'metadata': {
                'timestamp': timestamp,
                'duration_seconds': elapsed,
                'num_slates': num_slates,
                'total_results': len(all_results),
                'strategies_tested': STRATEGIES_TO_TEST
            },
            'results': all_results
        }

        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)

        print(f"\n💾 Results saved to: {filename}")

    return all_results


def analyze_focused_results(results):
    """Comprehensive analysis with slate size breakdown"""

    print("\n" + "=" * 80)
    print("ULTIMATE TEST RESULTS ANALYSIS")
    print("=" * 80)

    # Group by multiple dimensions
    by_strategy_contest = defaultdict(list)
    by_strategy_slate_size = defaultdict(lambda: defaultdict(list))

    for r in results:
        if r:
            # Main grouping
            key = f"{r['contest_type']}_{r['strategy']}"
            by_strategy_contest[key].append(r)

            # Slate size grouping
            slate_key = f"{r['slate_size']}_{r['contest_type']}_{r['strategy']}"
            by_strategy_slate_size[r['slate_size']][slate_key].append(r)

    # SECTION 1: Overall Performance
    print("\n📊 OVERALL PERFORMANCE:")
    print("=" * 80)

    # Separate cash and GPP
    cash_results = {}
    gpp_results = {}

    for key, results_list in by_strategy_contest.items():
        if 'cash' in key:
            strategy_name = key.replace('cash_', '')
            cash_results[strategy_name] = results_list
        else:
            strategy_name = key.replace('gpp_', '')
            gpp_results[strategy_name] = results_list

    # Cash Analysis with GPP strategies highlighted
    print("\n💰 CASH GAME PERFORMANCE:")
    print(f"{'Strategy':<35} {'Win%':>8} {'ROI%':>8} {'Avg Rank':>10} {'Avg Score':>10}")
    print("-" * 75)

    cash_summary = []
    for strategy_name, results_list in cash_results.items():
        if len(results_list) >= 10:
            wins = sum(1 for r in results_list if r['win'])
            win_rate = (wins / len(results_list)) * 100
            avg_roi = np.mean([r['roi'] for r in results_list])
            avg_rank = np.mean([r['rank'] for r in results_list])
            avg_score = np.mean([r['score'] for r in results_list])

            # Mark GPP strategies being tested in cash
            display_name = strategy_name
            if strategy_name in ['correlation_value', 'ceiling_stack', 'contrarian_correlation']:
                display_name = f"{strategy_name} (GPP→Cash)"

            cash_summary.append({
                'strategy': display_name,
                'win_rate': win_rate,
                'roi': avg_roi,
                'avg_rank': avg_rank,
                'avg_score': avg_score,
                'count': len(results_list)
            })

    # Sort by win rate
    cash_summary.sort(key=lambda x: x['win_rate'], reverse=True)

    for s in cash_summary:
        status = "🏆" if s['win_rate'] >= 56 else "✅" if s['win_rate'] >= 50 else "⚠️"
        print(f"{s['strategy']:<35} {s['win_rate']:>7.1f}% {s['roi']:>+7.1f}% "
              f"{s['avg_rank']:>9.1f} {s['avg_score']:>9.1f} {status}")

    # GPP Analysis
    print(f"\n🎯 TOURNAMENT (GPP) PERFORMANCE:")
    print(f"{'Strategy':<35} {'ROI%':>8} {'Top 10%':>9} {'Avg Rank':>10} {'Bink%':>8}")
    print("-" * 75)

    gpp_summary = []
    for strategy_name, results_list in gpp_results.items():
        if len(results_list) >= 10:
            avg_roi = np.mean([r['roi'] for r in results_list])
            avg_rank = np.mean([r['rank'] for r in results_list])
            top_10 = sum(1 for r in results_list if r['top_10']) / len(results_list) * 100
            top_1 = sum(1 for r in results_list if r['top_1']) / len(results_list) * 100

            gpp_summary.append({
                'strategy': strategy_name,
                'roi': avg_roi,
                'avg_rank': avg_rank,
                'top_10': top_10,
                'top_1': top_1,
                'count': len(results_list)
            })

    gpp_summary.sort(key=lambda x: x['roi'], reverse=True)

    for s in gpp_summary:
        status = "🔥" if s['roi'] > 50 else "💰" if s['roi'] > 20 else "✅" if s['roi'] > 0 else "❌"
        print(f"{s['strategy']:<35} {s['roi']:>+7.1f}% {s['top_10']:>8.1f}% "
              f"{s['avg_rank']:>9.1f} {s['top_1']:>7.1f}% {status}")

    # SECTION 2: Performance by Slate Size
    print(f"\n\n📈 PERFORMANCE BY SLATE SIZE:")
    print("=" * 80)

    for slate_size in ['small', 'medium', 'large']:
        print(f"\n🎮 {slate_size.upper()} SLATES:")

        # Cash games for this slate size
        print(f"\nCash Games ({slate_size}):")
        print(f"{'Strategy':<30} {'Win%':>8} {'ROI%':>8} {'Avg Rank':>10}")
        print("-" * 60)

        slate_cash_results = []
        for key, results_list in by_strategy_slate_size[slate_size].items():
            if 'cash' in key and len(results_list) >= 5:
                strategy_name = key.replace(f'{slate_size}_cash_', '')
                wins = sum(1 for r in results_list if r['win'])
                win_rate = (wins / len(results_list)) * 100
                avg_roi = np.mean([r['roi'] for r in results_list])
                avg_rank = np.mean([r['rank'] for r in results_list])

                slate_cash_results.append({
                    'strategy': strategy_name,
                    'win_rate': win_rate,
                    'roi': avg_roi,
                    'avg_rank': avg_rank,
                    'count': len(results_list)
                })

        slate_cash_results.sort(key=lambda x: x['win_rate'], reverse=True)

        for s in slate_cash_results:
            marker = "→" if s['strategy'] in ['correlation_value', 'ceiling_stack', 'contrarian_correlation'] else " "
            print(f"{marker} {s['strategy']:<28} {s['win_rate']:>7.1f}% {s['roi']:>+7.1f}% {s['avg_rank']:>9.1f}")

        # GPP games for this slate size
        print(f"\nGPP Tournaments ({slate_size}):")
        print(f"{'Strategy':<30} {'ROI%':>8} {'Top10%':>8} {'Avg Rank':>10}")
        print("-" * 60)

        slate_gpp_results = []
        for key, results_list in by_strategy_slate_size[slate_size].items():
            if 'gpp' in key and len(results_list) >= 5:
                strategy_name = key.replace(f'{slate_size}_gpp_', '')
                avg_roi = np.mean([r['roi'] for r in results_list])
                avg_rank = np.mean([r['rank'] for r in results_list])
                top_10 = sum(1 for r in results_list if r['top_10']) / len(results_list) * 100

                slate_gpp_results.append({
                    'strategy': strategy_name,
                    'roi': avg_roi,
                    'avg_rank': avg_rank,
                    'top_10': top_10,
                    'count': len(results_list)
                })

        slate_gpp_results.sort(key=lambda x: x['roi'], reverse=True)

        for s in slate_gpp_results:
            print(f"  {s['strategy']:<28} {s['roi']:>+7.1f}% {s['top_10']:>7.1f}% {s['avg_rank']:>9.1f}")

    # SECTION 3: Key Findings
    print(f"\n\n💡 KEY FINDINGS:")
    print("=" * 80)

    # Find best cash strategy overall
    if cash_summary:
        best_cash = max(cash_summary, key=lambda x: x['win_rate'])
        print(f"\n🏆 Best Cash Strategy: {best_cash['strategy']}")
        print(f"   - Win Rate: {best_cash['win_rate']:.1f}%")
        print(f"   - ROI: {best_cash['roi']:+.1f}%")
        print(f"   - Avg Rank: {best_cash['avg_rank']:.1f}")

    # Find best GPP strategy overall
    if gpp_summary:
        best_gpp = max(gpp_summary, key=lambda x: x['roi'])
        print(f"\n🏆 Best GPP Strategy: {best_gpp['strategy']}")
        print(f"   - ROI: {best_gpp['roi']:+.1f}%")
        print(f"   - Top 10%: {best_gpp['top_10']:.1f}%")
        print(f"   - Avg Rank: {best_gpp['avg_rank']:.1f}")

    # Check if GPP strategies work in cash
    gpp_in_cash = [s for s in cash_summary if '(GPP→Cash)' in s['strategy']]
    if gpp_in_cash:
        print(f"\n🔍 GPP STRATEGIES IN CASH GAMES:")
        for s in gpp_in_cash:
            print(f"   {s['strategy']}: {s['win_rate']:.1f}% win rate ({s['roi']:+.1f}% ROI)")

def export_strategy_comparison(results):
    """Export detailed strategy comparison to CSV"""
    print("\n📊 Exporting strategy comparison...")

    # Group results by strategy
    by_strategy = defaultdict(list)
    for r in results:
        if r:
            by_strategy[r['strategy']].append(r)

    # Create summary data
    summary_data = []
    for strategy, strategy_results in by_strategy.items():
        if strategy_results:
            summary_data.append({
                'Strategy': strategy,
                'Contest Type': strategy_results[0]['contest_type'],
                'Total Contests': len(strategy_results),
                'Avg ROI': f"{np.mean([r['roi'] for r in strategy_results]):.1f}%",
                'Win Rate': f"{sum(1 for r in strategy_results if r.get('win', False)) / len(strategy_results) * 100:.1f}%",
                'Avg Score': f"{np.mean([r['score'] for r in strategy_results]):.1f}",
                'Avg Ownership': f"{np.mean([r['ownership'] for r in strategy_results]):.1f}%"
            })

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'strategy_comparison_{timestamp}.json'

    with open(filename, 'w') as f:
        json.dump(summary_data, f, indent=2)

    print(f"✅ Exported to {filename}")


def show_best_lineups(results):
    """Show best performing lineups from each strategy"""
    print("\n🏆 BEST LINEUPS BY STRATEGY")
    print("=" * 80)

    # Group by strategy
    by_strategy = defaultdict(list)
    for r in results:
        if r:
            by_strategy[r['strategy']].append(r)

    # Find best lineup for each strategy
    for strategy, strategy_results in by_strategy.items():
        if strategy_results:
            # Find highest scoring lineup
            best = max(strategy_results, key=lambda x: x['score'])

            print(f"\n{strategy.upper()}:")
            print(f"Score: {best['score']:.1f} | Rank: {best['rank']} | ROI: {best['roi']:+.1f}%")
            print(f"Salary: ${best['lineup_salary']:,} | Ownership: {best['ownership']:.1f}%")


def analyze_by_slate_size(results):
    """Analyze performance by slate size"""
    print("\n📊 PERFORMANCE BY SLATE SIZE")
    print("=" * 80)

    # Group by slate size and strategy
    by_slate_size = defaultdict(lambda: defaultdict(list))

    for r in results:
        if r and 'slate_size' in r:
            key = f"{r['slate_size']}_{r['strategy']}"
            by_slate_size[r['slate_size']][r['strategy']].append(r)

    # Analyze each slate size
    for slate_size in ['small', 'medium', 'large']:
        if slate_size in by_slate_size:
            print(f"\n{slate_size.upper()} SLATES:")
            print(f"{'Strategy':<25} {'Win%':>8} {'ROI%':>8} {'Contests':>10}")
            print("-" * 51)

            for strategy, results_list in by_slate_size[slate_size].items():
                if len(results_list) >= 5:
                    wins = sum(1 for r in results_list if r.get('win', False))
                    win_rate = (wins / len(results_list)) * 100
                    avg_roi = np.mean([r['roi'] for r in results_list])

                    print(f"{strategy:<25} {win_rate:>7.1f}% {avg_roi:>+7.1f}% {len(results_list):>9}")


# At the bottom of focused_strategy_test.py, modify the menu:

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║           FOCUSED DFS STRATEGY TESTING                   ║
    ║                                                          ║
    ║  Testing only proven strategies (80%+ success rate)      ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    print("\nSelect option:")
    print("1. Quick Test (50 slates) - ~2 minutes")
    print("2. Standard Test (200 slates) - ~5 minutes")
    print("3. Extended Test (500 slates) - ~15 minutes")
    print("4. Full Validation (1000 slates) - ~30 minutes")

    choice = input("\nEnter choice (1-4): ")

    slate_counts = {
        '1': 50,
        '2': 200,
        '3': 500,
        '4': 1000
    }

    num_slates = slate_counts.get(choice, 200)

    print(f"\n🚀 Starting test with {num_slates} slates...")
    print("You'll see progress updates every few seconds.\n")

    results = run_focused_strategy_test(num_slates)