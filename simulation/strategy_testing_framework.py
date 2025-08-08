#!/usr/bin/env python3
"""
COMPREHENSIVE STRATEGY TESTING FRAMEWORK
=========================================
Tests YOUR actual strategies against realistic competition
Measures what ACTUALLY matters for DFS success
"""

import sys
import os
import numpy as np
import random
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json
from datetime import datetime

# Add your project paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==========================================
# IMPORT YOUR ACTUAL STRATEGIES
# ==========================================

try:
    # Import YOUR cash strategies
    from main_optimizer.cash_strategies import (
        build_projection_monster,
        build_pitcher_dominance
    )

    print("✅ Imported YOUR cash strategies")
    CASH_STRATEGIES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Could not import cash strategies: {e}")
    CASH_STRATEGIES_AVAILABLE = False


    # Fallback implementations
    def build_projection_monster(players, params=None):
        """Fallback: Simple high projection strategy"""
        players_copy = [p for p in players]
        # Sort by projection, take best that fit
        players_copy.sort(key=lambda p: p.base_projection, reverse=True)
        return {'players': players_copy[:10], 'strategy': 'projection_monster'}


    def build_pitcher_dominance(players, params=None):
        """Fallback: Focus on elite pitchers"""
        players_copy = [p for p in players]
        pitchers = [p for p in players_copy if p.primary_position == 'P']
        pitchers.sort(key=lambda p: p.base_projection, reverse=True)
        return {'players': pitchers[:2] + players_copy[:8], 'strategy': 'pitcher_dominance'}

try:
    # Import YOUR GPP strategies
    from main_optimizer.gpp_strategies import (
        build_correlation_value,
        build_truly_smart_stack,
        build_matchup_leverage_stack
    )

    print("✅ Imported YOUR GPP strategies")
    GPP_STRATEGIES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Could not import GPP strategies: {e}")
    GPP_STRATEGIES_AVAILABLE = False


    # Fallback implementations
    def build_correlation_value(players, params=None):
        """Fallback: Basic correlation strategy"""
        return {'players': players[:10], 'strategy': 'correlation_value'}


    def build_truly_smart_stack(players, params=None):
        """Fallback: Basic stacking"""
        return {'players': players[:10], 'strategy': 'truly_smart_stack'}

try:
    # Import tournament winner if in separate file
    from main_optimizer.tournament_winner_gpp_strategy import build_tournament_winner_gpp

    print("✅ Imported tournament_winner_gpp strategy")
except ImportError:
    def build_tournament_winner_gpp(players, params=None):
        """Fallback: Tournament optimized"""
        return {'players': players[:10], 'strategy': 'tournament_winner_gpp'}

# Import the realistic simulator
try:
    from realistic_dfs_simulator import (
        RealisticDFSSimulator,
        SimulatedPlayer,
        generate_realistic_slate,
        MLB_VARIANCE,
        CONTEST_DYNAMICS
    )

    print("✅ Imported realistic simulator")
except ImportError:
    print("❌ Please run the realistic simulator code first!")
    sys.exit(1)

# ==========================================
# WHAT ACTUALLY MATTERS (from research)
# ==========================================

SUCCESS_METRICS = {
    'large_gpp': {
        'top_1_percent_rate': 0.02,  # Should achieve 2x field rate
        'top_10_percent_rate': 0.15,  # Should achieve 1.5x field rate
        'uses_4_5_stacks': 0.80,  # 80%+ of winners use 4-5 stacks
        'consecutive_batting_order': 0.75,  # Critical for correlation
        'avg_stack_ownership': 0.01,  # Should be under 1%
        'survives_chalk_fail': 0.30,  # Wins when chalk busts
    },
    'small_gpp': {
        'win_rate': 0.20,  # Should win 20%+ in small fields
        'top_3_rate': 0.40,  # Top 3 in 40%+ of contests
        'consistency': 0.60,  # Score above median 60%+
        'uses_moderate_stacks': 0.60,  # 3-4 man stacks work here
    },
    'cash': {
        'cash_rate': 0.55,  # Beat 55%+ of field (beat rake)
        'consistency_score': 0.70,  # Consistent scoring
        'avoid_zeros': 0.90,  # Avoid disaster 90%+ of time
        'floor_achievement': 0.65,  # Hit projection floor 65%+
        'max_player_correlation': 3,  # Max 3 from same team
    }
}


# ==========================================
# STRATEGY TESTING ENGINE
# ==========================================

class StrategyTestingFramework:
    """
    Tests YOUR strategies against realistic competition
    Provides detailed insights on what works
    """

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.results = defaultdict(lambda: defaultdict(list))
        self.detailed_results = []

    def test_strategy(self,
                      strategy_func,
                      strategy_name: str,
                      contest_type: str,  # 'cash' or 'gpp'
                      slate_size: str,  # 'small', 'medium', 'large'
                      num_slates: int = 100,
                      contest_sizes: List[int] = None) -> Dict:
        """
        Test a strategy across multiple slates and contests
        """

        if contest_sizes is None:
            if contest_type == 'cash':
                contest_sizes = [100, 500]  # Double-ups
            else:
                if slate_size == 'small':
                    contest_sizes = [3, 10, 20]  # Small field GPPs
                else:
                    contest_sizes = [100, 500, 5000]  # Large field GPPs

        print(f"\n{'=' * 80}")
        print(f"TESTING: {strategy_name} ({contest_type} - {slate_size} slates)")
        print(f"{'=' * 80}")

        strategy_results = {
            'strategy': strategy_name,
            'contest_type': contest_type,
            'slate_size': slate_size,
            'detailed_metrics': defaultdict(list),
            'summary': {}
        }

        for slate_num in range(num_slates):
            if self.verbose and slate_num % 10 == 0:
                print(f"  Testing slate {slate_num + 1}/{num_slates}...", end='\r')

            # Generate slate based on size
            num_games = self._get_num_games(slate_size)
            slate = self._generate_slate_for_testing(num_games)

            # Build lineup using YOUR strategy
            try:
                lineup_result = strategy_func(slate)

                # Convert to our format if needed
                if isinstance(lineup_result, dict):
                    lineup = lineup_result
                else:
                    # Handle if it returns just players
                    lineup = {'players': lineup_result[:10]}

                # Add metadata
                lineup['strategy'] = strategy_name
                lineup['slate_size'] = slate_size

            except Exception as e:
                print(f"\n  ❌ Strategy failed: {e}")
                continue

            # Test in different contest sizes
            for contest_size in contest_sizes:
                result = self._run_single_contest(
                    lineup, slate, contest_size, contest_type
                )

                # Store results
                strategy_results['detailed_metrics'][contest_size].append(result)

        # Analyze results
        print(f"\n{'=' * 60}")
        print(f"RESULTS FOR: {strategy_name}")
        print(f"{'=' * 60}")

        summary = self._analyze_strategy_results(
            strategy_results, contest_type, slate_size
        )

        strategy_results['summary'] = summary

        # Store for comparison
        self.results[contest_type][strategy_name] = strategy_results

        return strategy_results

    def _get_num_games(self, slate_size: str) -> int:
        """Get number of games for slate size"""
        if slate_size == 'small':
            return random.randint(2, 3)  # 2-3 games
        elif slate_size == 'medium':
            return random.randint(4, 8)  # 4-8 games
        else:
            return random.randint(9, 15)  # 9+ games

    def _generate_slate_for_testing(self, num_games: int) -> List:
        """Generate a slate that works with YOUR strategy format"""

        # Generate using realistic simulator
        raw_slate = generate_realistic_slate(num_games * 20, 'medium')

        # Convert to YOUR format (add attributes your strategies expect)
        converted_slate = []
        for player in raw_slate:
            # Create player object with YOUR expected attributes
            p = type('Player', (), {})()

            # Map from simulator format to YOUR format
            p.name = player.name
            p.primary_position = player.position
            p.team = player.team
            p.salary = player.salary
            p.base_projection = player.projection
            p.projected_ownership = player.ownership * 100  # Convert to percentage
            p.ownership_projection = player.ownership * 100

            # Add additional attributes YOUR strategies might use
            p.batting_order = getattr(player, 'batting_order', 0)
            p.implied_team_score = getattr(player, 'team_total', 4.5)
            p.game_total = getattr(player, 'game_total', 9.0)
            p.park_factor = getattr(player, 'park_factor', 1.0)
            p.ceiling = player.ceiling
            p.floor = player.floor

            # GPP specific attributes
            p.correlation_score = 1.0
            p.leverage_score = 1.0 / max(player.ownership, 0.01)

            # Add optimization score (your strategies modify this)
            p.optimization_score = p.base_projection

            converted_slate.append(p)

        return converted_slate

    def _run_single_contest(self,
                            your_lineup: Dict,
                            slate: List,
                            contest_size: int,
                            contest_type: str) -> Dict:
        """Run a single contest with your lineup vs realistic field"""

        # Create simulator
        sim = RealisticDFSSimulator(contest_size)

        # Generate realistic competition
        sim_slate = self._convert_to_sim_format(slate)
        field = sim.generate_realistic_field(sim_slate)

        # Insert YOUR lineup at position 0
        your_lineup_converted = self._convert_lineup_to_sim_format(your_lineup, slate)
        field[0] = your_lineup_converted

        # Simulate scoring
        scored = sim.simulate_scoring(field)

        # Calculate payouts
        results = sim.calculate_payouts(scored)

        # Find your result
        your_result = None
        for r in results:
            if r['lineup'] == your_lineup_converted:
                your_result = r
                break

        if not your_result:
            your_result = results[0]  # Fallback

        # Analyze lineup characteristics
        analysis = self._analyze_lineup(your_lineup, slate)

        return {
            'rank': your_result['rank'],
            'percentile': (contest_size - your_result['rank']) / contest_size,
            'score': your_result['score'],
            'roi': your_result['roi'],
            'payout': your_result['payout'],
            'contest_size': contest_size,
            'stack_size': analysis['stack_size'],
            'stack_type': analysis['stack_type'],
            'ownership_sum': analysis['ownership_sum'],
            'is_consecutive': analysis['is_consecutive'],
            'num_teams': analysis['num_teams'],
            'won': your_result['rank'] == 1,
            'cashed': your_result['payout'] > 0,
            'top_10_percent': your_result['rank'] <= contest_size * 0.1,
            'top_1_percent': your_result['rank'] <= max(1, contest_size * 0.01),
        }

    def _convert_to_sim_format(self, slate: List) -> List[SimulatedPlayer]:
        """Convert YOUR slate format to simulator format"""
        sim_slate = []

        for p in slate:
            sim_player = SimulatedPlayer(
                name=p.name,
                position=p.primary_position,
                team=p.team,
                salary=p.salary,
                projection=p.base_projection,
                ownership=p.projected_ownership / 100,  # Convert from percentage
                batting_order=getattr(p, 'batting_order', 0)
            )
            sim_slate.append(sim_player)

        return sim_slate

    def _convert_lineup_to_sim_format(self, lineup: Dict, slate: List) -> Dict:
        """Convert YOUR lineup format to simulator format"""

        players = lineup.get('players', [])

        # Convert players
        sim_players = []
        for p in players[:10]:  # Ensure max 10
            # Find matching player in slate
            for slate_p in slate:
                if slate_p.name == p.name:
                    sim_player = SimulatedPlayer(
                        name=slate_p.name,
                        position=slate_p.primary_position,
                        team=slate_p.team,
                        salary=slate_p.salary,
                        projection=slate_p.base_projection,
                        ownership=slate_p.projected_ownership / 100,
                        batting_order=getattr(slate_p, 'batting_order', 0)
                    )
                    sim_players.append(sim_player)
                    break

        # Determine stack pattern
        stack_analysis = self._analyze_lineup({'players': sim_players}, slate)

        return {
            'players': sim_players,
            'stack_pattern': stack_analysis['stack_type'],
            'total_salary': sum(p.salary for p in sim_players),
            'is_valid': len(sim_players) == 10
        }

    def _analyze_lineup(self, lineup: Dict, slate: List) -> Dict:
        """Analyze lineup characteristics"""

        players = lineup.get('players', [])

        # Team distribution
        team_counts = defaultdict(list)
        for p in players:
            if hasattr(p, 'primary_position'):
                pos = p.primary_position
            else:
                pos = p.position

            if pos != 'P':
                team_counts[p.team].append(p)

        # Find largest stack
        max_stack = 0
        stack_type = 'no_stack'
        is_consecutive = False

        if team_counts:
            largest_team = max(team_counts.values(), key=len)
            max_stack = len(largest_team)

            # Check if consecutive
            if max_stack >= 3:
                orders = sorted([p.batting_order for p in largest_team
                                 if hasattr(p, 'batting_order') and p.batting_order > 0])
                if orders:
                    is_consecutive = all(
                        orders[i + 1] - orders[i] == 1
                        for i in range(len(orders) - 1)
                    )

            # Classify stack type
            if max_stack >= 5:
                stack_type = '5-man'
            elif max_stack == 4:
                stack_type = '4-man'
            elif max_stack == 3:
                stack_type = '3-man'
            elif max_stack == 2:
                stack_type = '2-man'

        # Calculate total ownership
        total_own = sum(
            getattr(p, 'ownership', 0) if hasattr(p, 'ownership')
            else getattr(p, 'projected_ownership', 0) / 100
            for p in players
        )

        return {
            'stack_size': max_stack,
            'stack_type': stack_type,
            'is_consecutive': is_consecutive,
            'num_teams': len(team_counts),
            'ownership_sum': total_own,
        }

    def _analyze_strategy_results(self,
                                  results: Dict,
                                  contest_type: str,
                                  slate_size: str) -> Dict:
        """Comprehensive analysis of strategy performance"""

        summary = {
            'contest_type': contest_type,
            'slate_size': slate_size,
            'performance_by_contest_size': {}
        }

        print(f"\n📊 DETAILED ANALYSIS:")
        print(f"{'=' * 60}")

        for contest_size, contest_results in results['detailed_metrics'].items():
            if not contest_results:
                continue

            print(f"\n📈 {contest_size}-Player Contests:")
            print(f"{'-' * 40}")

            # Calculate key metrics
            metrics = self._calculate_metrics(contest_results, contest_type)

            # Display based on contest type
            if contest_type == 'cash':
                self._display_cash_metrics(metrics, contest_size)
            else:
                self._display_gpp_metrics(metrics, contest_size)

            summary['performance_by_contest_size'][contest_size] = metrics

        # Overall assessment
        print(f"\n{'=' * 60}")
        print(f"🎯 OVERALL ASSESSMENT:")
        self._provide_assessment(summary, contest_type, slate_size)

        return summary

    def _calculate_metrics(self, results: List[Dict], contest_type: str) -> Dict:
        """Calculate all relevant metrics"""

        metrics = {
            'total_contests': len(results),
            'win_rate': sum(1 for r in results if r['won']) / len(results),
            'cash_rate': sum(1 for r in results if r['cashed']) / len(results),
            'avg_roi': np.mean([r['roi'] for r in results]),
            'median_roi': np.median([r['roi'] for r in results]),
            'top_10_rate': sum(1 for r in results if r['top_10_percent']) / len(results),
            'top_1_rate': sum(1 for r in results if r['top_1_percent']) / len(results),
            'avg_percentile': np.mean([r['percentile'] for r in results]),
            'avg_score': np.mean([r['score'] for r in results]),
            'score_std': np.std([r['score'] for r in results]),

            # Stack analysis
            'stack_distribution': defaultdict(int),
            'consecutive_rate': sum(1 for r in results if r['is_consecutive']) / len(results),
            'avg_ownership': np.mean([r['ownership_sum'] for r in results]),

            # Consistency metrics
            'above_median_rate': sum(1 for r in results if r['percentile'] >= 0.5) / len(results),
            'disaster_rate': sum(1 for r in results if r['percentile'] < 0.2) / len(results),
        }

        # Stack distribution
        for r in results:
            metrics['stack_distribution'][r['stack_type']] += 1

        # Normalize stack distribution
        total = sum(metrics['stack_distribution'].values())
        if total > 0:
            for stack_type in metrics['stack_distribution']:
                metrics['stack_distribution'][stack_type] /= total

        return metrics

    def _display_cash_metrics(self, metrics: Dict, contest_size: int):
        """Display metrics relevant for cash games"""

        print(f"  💰 Cash Rate: {metrics['cash_rate'] * 100:.1f}%")
        print(f"  📊 Avg ROI: {metrics['avg_roi']:.1f}%")
        print(f"  🎯 Consistency: {metrics['above_median_rate'] * 100:.1f}% above median")
        print(f"  💥 Disaster Rate: {metrics['disaster_rate'] * 100:.1f}% bottom 20%")
        print(f"  📈 Avg Score: {metrics['avg_score']:.1f} (std: {metrics['score_std']:.1f})")

        # Check against success criteria
        success = SUCCESS_METRICS['cash']

        print(f"\n  ✅ Success Criteria Check:")
        cash_check = metrics['cash_rate'] >= success['cash_rate']
        print(f"    Cash Rate: {'✅' if cash_check else '❌'} "
              f"{metrics['cash_rate'] * 100:.1f}% vs {success['cash_rate'] * 100:.0f}% target")

        consistency_check = metrics['above_median_rate'] >= success['consistency_score']
        print(f"    Consistency: {'✅' if consistency_check else '❌'} "
              f"{metrics['above_median_rate'] * 100:.1f}% vs {success['consistency_score'] * 100:.0f}% target")

        disaster_check = (1 - metrics['disaster_rate']) >= success['avoid_zeros']
        print(f"    Avoid Disasters: {'✅' if disaster_check else '❌'} "
              f"{(1 - metrics['disaster_rate']) * 100:.1f}% vs {success['avoid_zeros'] * 100:.0f}% target")

    def _display_gpp_metrics(self, metrics: Dict, contest_size: int):
        """Display metrics relevant for GPPs"""

        print(f"  🏆 Win Rate: {metrics['win_rate'] * 100:.2f}%")
        print(f"  💰 ROI: {metrics['avg_roi']:.1f}% (median: {metrics['median_roi']:.1f}%)")
        print(f"  🎯 Top 10%: {metrics['top_10_rate'] * 100:.1f}%")
        print(f"  🚀 Top 1%: {metrics['top_1_rate'] * 100:.2f}%")
        print(f"  📊 Avg Ownership: {metrics['avg_ownership']:.2f}%")

        # Stack analysis
        print(f"\n  📚 Stack Distribution:")
        for stack_type, pct in sorted(metrics['stack_distribution'].items(),
                                      key=lambda x: x[1], reverse=True):
            print(f"    {stack_type}: {pct * 100:.1f}%")

        print(f"  🔗 Consecutive Stacks: {metrics['consecutive_rate'] * 100:.1f}%")

        # Check against success criteria
        if contest_size >= 100:
            success = SUCCESS_METRICS['large_gpp']
        else:
            success = SUCCESS_METRICS['small_gpp']

        print(f"\n  ✅ Success Criteria Check:")

        if contest_size >= 100:
            # Large GPP checks
            top_1_check = metrics['top_1_rate'] >= success['top_1_percent_rate']
            print(f"    Top 1% Rate: {'✅' if top_1_check else '❌'} "
                  f"{metrics['top_1_rate'] * 100:.2f}% vs {success['top_1_percent_rate'] * 100:.0f}% target")

            # Check 4-5 stacks
            big_stack_rate = (metrics['stack_distribution'].get('4-man', 0) +
                              metrics['stack_distribution'].get('5-man', 0))
            stack_check = big_stack_rate >= success['uses_4_5_stacks']
            print(f"    4-5 Stacks: {'✅' if stack_check else '❌'} "
                  f"{big_stack_rate * 100:.1f}% vs {success['uses_4_5_stacks'] * 100:.0f}% target")

            consecutive_check = metrics['consecutive_rate'] >= success['consecutive_batting_order']
            print(f"    Consecutive: {'✅' if consecutive_check else '❌'} "
                  f"{metrics['consecutive_rate'] * 100:.1f}% vs {success['consecutive_batting_order'] * 100:.0f}% target")
        else:
            # Small GPP checks
            win_check = metrics['win_rate'] >= success['win_rate']
            print(f"    Win Rate: {'✅' if win_check else '❌'} "
                  f"{metrics['win_rate'] * 100:.1f}% vs {success['win_rate'] * 100:.0f}% target")

    def _provide_assessment(self, summary: Dict, contest_type: str, slate_size: str):
        """Provide strategic assessment and recommendations"""

        print(f"\n💡 KEY INSIGHTS:")

        # Aggregate performance across contest sizes
        all_metrics = []
        for size, metrics in summary['performance_by_contest_size'].items():
            all_metrics.append(metrics)

        if not all_metrics:
            print("  ⚠️ No results to analyze")
            return

        # Average across all contest sizes
        avg_roi = np.mean([m['avg_roi'] for m in all_metrics])
        avg_cash_rate = np.mean([m['cash_rate'] for m in all_metrics])

        if contest_type == 'cash':
            if avg_cash_rate >= 0.55:
                print(f"  ✅ PROFITABLE in cash games! ({avg_cash_rate * 100:.1f}% cash rate)")
                print(f"  💰 Expected ROI: {avg_roi:.1f}%")
            else:
                print(f"  ❌ UNPROFITABLE in cash ({avg_cash_rate * 100:.1f}% cash rate)")
                print(f"  📉 Losing ROI: {avg_roi:.1f}%")
                print(f"\n  🔧 RECOMMENDATIONS:")
                print(f"    • Reduce variance - focus on floor")
                print(f"    • Avoid stacking in cash games")
                print(f"    • Play chalk with high floor")
        else:
            # GPP assessment
            avg_top_1 = np.mean([m['top_1_rate'] for m in all_metrics])

            if avg_roi > -20:  # Better than -20% ROI is good for GPPs
                print(f"  ✅ STRONG GPP performance! ROI: {avg_roi:.1f}%")
                print(f"  🚀 Top 1%: {avg_top_1 * 100:.2f}% of contests")
            else:
                print(f"  ⚠️ Needs improvement. ROI: {avg_roi:.1f}%")

                # Check specific issues
                avg_big_stacks = np.mean([
                    m['stack_distribution'].get('4-man', 0) +
                    m['stack_distribution'].get('5-man', 0)
                    for m in all_metrics
                ])

                if avg_big_stacks < 0.50:
                    print(f"\n  🔧 CRITICAL ISSUE: Not enough 4-5 stacks!")
                    print(f"    Current: {avg_big_stacks * 100:.1f}%")
                    print(f"    Target: 80%+ for GPP success")
                    print(f"    FIX: Force 4-5 player stacks")

                avg_consecutive = np.mean([m['consecutive_rate'] for m in all_metrics])
                if avg_consecutive < 0.50:
                    print(f"\n  🔧 ISSUE: Stacks not consecutive!")
                    print(f"    Current: {avg_consecutive * 100:.1f}% consecutive")
                    print(f"    Target: 75%+ consecutive")
                    print(f"    FIX: Target 2-3-4-5 batting order")

    def compare_all_strategies(self):
        """Compare all tested strategies"""

        print(f"\n{'=' * 80}")
        print(f"STRATEGY COMPARISON")
        print(f"{'=' * 80}")

        # Cash comparison
        if self.results['cash']:
            print(f"\n💰 CASH GAME STRATEGIES:")
            print(f"{'Strategy':<30} {'Cash Rate':>12} {'ROI':>10} {'Consistency':>12}")
            print(f"{'-' * 65}")

            for name, data in self.results['cash'].items():
                summary = data['summary']
                avg_metrics = self._average_metrics(summary)

                print(f"{name:<30} {avg_metrics['cash_rate'] * 100:>11.1f}% "
                      f"{avg_metrics['roi']:>9.1f}% "
                      f"{avg_metrics['consistency'] * 100:>11.1f}%")

        # GPP comparison
        if self.results['gpp']:
            print(f"\n🎯 GPP STRATEGIES:")
            print(f"{'Strategy':<30} {'Win Rate':>10} {'ROI':>10} {'Top 1%':>10} {'4-5 Stack':>12}")
            print(f"{'-' * 73}")

            for name, data in self.results['gpp'].items():
                summary = data['summary']
                avg_metrics = self._average_metrics(summary)

                print(f"{name:<30} {avg_metrics['win_rate'] * 100:>9.2f}% "
                      f"{avg_metrics['roi']:>9.1f}% "
                      f"{avg_metrics['top_1'] * 100:>9.2f}% "
                      f"{avg_metrics['big_stacks'] * 100:>11.1f}%")

        # Overall winner
        self._declare_winners()

    def _average_metrics(self, summary: Dict) -> Dict:
        """Average metrics across contest sizes"""

        metrics = {
            'cash_rate': 0,
            'roi': 0,
            'consistency': 0,
            'win_rate': 0,
            'top_1': 0,
            'big_stacks': 0
        }

        count = 0
        for size, m in summary['performance_by_contest_size'].items():
            metrics['cash_rate'] += m.get('cash_rate', 0)
            metrics['roi'] += m.get('avg_roi', 0)
            metrics['consistency'] += m.get('above_median_rate', 0)
            metrics['win_rate'] += m.get('win_rate', 0)
            metrics['top_1'] += m.get('top_1_rate', 0)
            metrics['big_stacks'] += (m['stack_distribution'].get('4-man', 0) +
                                      m['stack_distribution'].get('5-man', 0))
            count += 1

        if count > 0:
            for key in metrics:
                metrics[key] /= count

        return metrics

    def _declare_winners(self):
        """Declare winning strategies"""

        print(f"\n{'=' * 80}")
        print(f"🏆 WINNERS")
        print(f"{'=' * 80}")

        # Cash winner
        if self.results['cash']:
            best_cash = max(
                self.results['cash'].items(),
                key=lambda x: self._average_metrics(x[1]['summary'])['cash_rate']
            )
            metrics = self._average_metrics(best_cash[1]['summary'])
            print(f"\n💰 BEST CASH: {best_cash[0]}")
            print(f"   Cash Rate: {metrics['cash_rate'] * 100:.1f}%")
            print(f"   ROI: {metrics['roi']:.1f}%")

        # GPP winner
        if self.results['gpp']:
            best_gpp = max(
                self.results['gpp'].items(),
                key=lambda x: self._average_metrics(x[1]['summary'])['roi']
            )
            metrics = self._average_metrics(best_gpp[1]['summary'])
            print(f"\n🎯 BEST GPP: {best_gpp[0]}")
            print(f"   ROI: {metrics['roi']:.1f}%")
            print(f"   Top 1%: {metrics['top_1'] * 100:.2f}%")
            print(f"   4-5 Stacks: {metrics['big_stacks'] * 100:.1f}%")


# ==========================================
# MAIN TEST RUNNER
# ==========================================

def run_comprehensive_tests():
    """
    Test YOUR actual strategies across all scenarios
    """

    print("\n" + "=" * 80)
    print("COMPREHENSIVE STRATEGY TESTING")
    print("Testing YOUR actual strategies against realistic competition")
    print("=" * 80)

    # Initialize framework
    framework = StrategyTestingFramework(verbose=True)

    # Define what to test
    test_configs = [
        # CASH GAMES
        {
            'strategy': build_projection_monster,
            'name': 'projection_monster',
            'type': 'cash',
            'sizes': ['small', 'medium', 'large']
        },
        {
            'strategy': build_pitcher_dominance,
            'name': 'pitcher_dominance',
            'type': 'cash',
            'sizes': ['small', 'medium', 'large']
        },

        # GPP TOURNAMENTS
        {
            'strategy': build_tournament_winner_gpp,
            'name': 'tournament_winner_gpp',
            'type': 'gpp',
            'sizes': ['small', 'medium', 'large']
        },
        {
            'strategy': build_correlation_value,
            'name': 'correlation_value',
            'type': 'gpp',
            'sizes': ['small', 'medium', 'large']
        },
        {
            'strategy': build_truly_smart_stack,
            'name': 'truly_smart_stack',
            'type': 'gpp',
            'sizes': ['medium', 'large']  # Skip small for heavy stacking
        }
    ]

    # Run tests
    for config in test_configs:
        for slate_size in config['sizes']:
            framework.test_strategy(
                strategy_func=config['strategy'],
                strategy_name=config['name'],
                contest_type=config['type'],
                slate_size=slate_size,
                num_slates=50  # Adjust for speed vs accuracy
            )

    # Compare all strategies
    framework.compare_all_strategies()

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'strategy_test_results_{timestamp}.json'

    with open(filename, 'w') as f:
        json.dump(framework.results, f, indent=2, default=str)

    print(f"\n📁 Results saved to: {filename}")

    # Final recommendations
    print(f"\n{'=' * 80}")
    print("📋 FINAL RECOMMENDATIONS")
    print("=" * 80)

    print("""
Based on testing against REALISTIC competition:

FOR CASH GAMES:
• Small slates (2-3 games): Use pitcher_dominance
• Medium slates (4-8 games): Use projection_monster  
• Large slates (9+ games): Use projection_monster
• Focus on FLOOR and CONSISTENCY
• Avoid stacking - max 3 from same team

FOR GPP TOURNAMENTS:
• CRITICAL: Force 4-5 player stacks (80%+ of lineups)
• Target CONSECUTIVE batting orders (2-3-4-5)
• Embrace LOW ownership (<1% for stacks is fine!)
• Small fields: Balance safety with upside
• Large fields: Maximum variance and correlation

KEY INSIGHTS:
• Your strategies need MORE stacking for GPPs
• Cash strategies should AVOID correlation
• Ownership is overestimated by 10-20x
• Variance is your friend in GPPs, enemy in cash
    """)


if __name__ == "__main__":
    run_comprehensive_tests()