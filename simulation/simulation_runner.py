#!/usr/bin/env python3
"""
CLEAN SIMULATION RUNNER
=======================
Uses ONLY your ACTUAL working strategies
No phantom strategies, no broken imports
"""

import sys
import os
import json
import random
import numpy as np
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple

# Fix paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import YOUR ACTUAL system
from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
from main_optimizer.unified_player_model import UnifiedPlayer

# Import the GOOD simulator (realistic_dfs_simulator.py)
from realistic_dfs_simulator import (
    RealisticDFSSimulator,
    generate_realistic_slate,
    SimulatedPlayer,
    analyze_contest_results,
    CONTEST_DYNAMICS,
    REAL_STACKING_FREQUENCIES
)

# YOUR ACTUAL STRATEGIES
WORKING_STRATEGIES = {
    'gpp': [
        'tournament_winner_gpp',  # Forces 4-5 stacks
        'correlation_value'  # Value with correlation
    ],
    'cash': [
        'cash',  # Basic conservative
        'projection_monster',  # Max projections
        'pitcher_dominance'  # Elite pitchers
    ]
}


class CleanSimulationRunner:
    """Run simulations with YOUR ACTUAL strategies"""

    def __init__(self):
        self.system = UnifiedCoreSystem()
        self.results = defaultdict(list)

    def run_strategy_test(
            self,
            strategy_name: str,
            contest_type: str,
            num_slates: int = 100,
            contest_size: int = 100
    ):
        """Test a single strategy"""

        print(f"\n🎯 Testing {strategy_name} ({contest_type.upper()})")
        print(f"   Slates: {num_slates}, Contest size: {contest_size}")

        strategy_results = {
            'strategy': strategy_name,
            'contest_type': contest_type,
            'placements': [],
            'scores': [],
            'roi_total': 0,
            'patterns_used': defaultdict(int)
        }

        for slate_num in range(num_slates):
            if slate_num % 10 == 0:
                print(f"   Progress: {slate_num}/{num_slates}")

            # Generate realistic slate
            slate_size = random.choice(['small', 'medium', 'large'])
            sim_players = generate_realistic_slate(200, slate_size)

            # Convert to your format
            your_players = self._convert_players(sim_players)

            # Generate YOUR lineup
            self.system.player_pool = your_players

            try:
                lineups = self.system.optimize_lineups(
                    num_lineups=1,
                    strategy=strategy_name,
                    contest_type=contest_type
                )

                if not lineups:
                    continue

                your_lineup = lineups[0]

            except Exception as e:
                print(f"   Error generating lineup: {e}")
                continue

            # Create contest
            sim = RealisticDFSSimulator(contest_size, slate_size)

            # Generate realistic field
            field = sim.generate_realistic_field(sim_players)

            # Add your lineup
            your_entry = self._convert_lineup_back(your_lineup, sim_players)
            field.append(your_entry)

            # Simulate
            scored = sim.simulate_scoring(field)
            results = sim.calculate_payouts(scored)

            # Find your result
            for i, result in enumerate(results):
                if result['lineup'] == your_entry:
                    strategy_results['placements'].append(result['rank'])
                    strategy_results['scores'].append(result['score'])
                    strategy_results['roi_total'] += result['roi']
                    strategy_results['patterns_used'][result['pattern']] += 1
                    break

        # Calculate stats
        if strategy_results['placements']:
            n = len(strategy_results['placements'])
            strategy_results['avg_placement'] = np.mean(strategy_results['placements'])
            strategy_results['win_rate'] = sum(1 for p in strategy_results['placements'] if p == 1) / n * 100
            strategy_results['top10_rate'] = sum(1 for p in strategy_results['placements'] if p <= 10) / n * 100
            strategy_results['avg_roi'] = strategy_results['roi_total'] / n
            strategy_results['avg_score'] = np.mean(strategy_results['scores'])

        return strategy_results

    def _convert_players(self, sim_players: List[SimulatedPlayer]) -> List[UnifiedPlayer]:
        """Convert sim players to your format"""
        converted = []

        for sp in sim_players:
            player = UnifiedPlayer(
                id=sp.name,
                name=sp.name,
                primary_position=sp.position,
                position=sp.position,
                team=sp.team,
                salary=sp.salary,
                projection=sp.projection,
                base_projection=sp.projection
            )

            # Add attributes
            player.ownership = sp.ownership * 100
            player.batting_order = getattr(sp, 'batting_order', 0)
            player.team_total = getattr(sp, 'team_total', 4.5)
            player.ceiling = sp.ceiling
            player.floor = sp.floor

            converted.append(player)

        return converted

    def _convert_lineup_back(self, your_lineup: Dict, sim_players: List) -> Dict:
        """Convert your lineup back to sim format"""

        sim_lineup = []

        # Match players
        for your_player in your_lineup.get('players', []):
            for sp in sim_players:
                if sp.name == your_player.id or sp.name == your_player.name:
                    sim_lineup.append(sp)
                    break

        # Detect stack pattern
        teams = defaultdict(int)
        for p in sim_lineup:
            if p.position != 'P':
                teams[p.team] += 1

        max_stack = max(teams.values()) if teams else 0

        if max_stack >= 5:
            pattern = '5-man'
        elif max_stack >= 4:
            pattern = '4-man'
        elif max_stack >= 3:
            pattern = '3-man'
        else:
            pattern = 'no_stack'

        return {
            'players': sim_lineup,
            'stack_pattern': pattern,
            'total_salary': sum(p.salary for p in sim_lineup),
            'is_valid': len(sim_lineup) == 10
        }

    def run_all_tests(self, num_slates: int = 50):
        """Test all your strategies"""

        print("=" * 60)
        print("🚀 TESTING YOUR ACTUAL STRATEGIES")
        print("=" * 60)
        print(f"\nStrategies to test:")
        print(f"  GPP: {WORKING_STRATEGIES['gpp']}")
        print(f"  Cash: {WORKING_STRATEGIES['cash']}")

        all_results = []

        # Test GPP strategies
        for strategy in WORKING_STRATEGIES['gpp']:
            result = self.run_strategy_test(strategy, 'gpp', num_slates, 100)
            all_results.append(result)
            self._print_summary(result)

        # Test Cash strategies
        for strategy in WORKING_STRATEGIES['cash']:
            result = self.run_strategy_test(strategy, 'cash', num_slates, 10)
            all_results.append(result)
            self._print_summary(result)

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'clean_sim_results_{timestamp}.json'

        with open(filename, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)

        print(f"\n📁 Results saved to: {filename}")

        # Final analysis
        self._final_analysis(all_results)

    def _print_summary(self, result: Dict):
        """Print strategy summary"""
        print(f"\n📊 {result['strategy']} Summary:")
        print(f"   Avg Place: {result.get('avg_placement', 0):.1f}")
        print(f"   Win Rate: {result.get('win_rate', 0):.1f}%")
        print(f"   Top 10: {result.get('top10_rate', 0):.1f}%")
        print(f"   ROI: {result.get('avg_roi', 0):+.1f}%")

        # Stack analysis for GPP
        if result['contest_type'] == 'gpp':
            patterns = result.get('patterns_used', {})
            total = sum(patterns.values())
            if total > 0:
                four_plus = patterns.get('4-man', 0) + patterns.get('5-man', 0)
                print(f"   4+ Stacks: {four_plus}/{total} ({four_plus / total * 100:.1f}%)")

    def _final_analysis(self, results: List[Dict]):
        """Final analysis and recommendations"""

        print("\n" + "=" * 60)
        print("🏆 FINAL ANALYSIS")
        print("=" * 60)

        # Best strategies
        gpp_results = [r for r in results if r['contest_type'] == 'gpp']
        cash_results = [r for r in results if r['contest_type'] == 'cash']

        if gpp_results:
            best_gpp = max(gpp_results, key=lambda x: x.get('avg_roi', -100))
            print(f"\n🎯 Best GPP: {best_gpp['strategy']}")
            print(f"   ROI: {best_gpp.get('avg_roi', 0):+.1f}%")

            # Check if stacking enough
            patterns = best_gpp.get('patterns_used', {})
            total = sum(patterns.values())
            if total > 0:
                four_plus = patterns.get('4-man', 0) + patterns.get('5-man', 0)
                stack_rate = four_plus / total * 100

                if stack_rate < 80:
                    print(f"\n⚠️ WARNING: Only {stack_rate:.1f}% use 4+ stacks")
                    print("   Winners use 83% - NEED MORE STACKING!")

        if cash_results:
            best_cash = max(cash_results, key=lambda x: x.get('avg_roi', -100))
            print(f"\n💰 Best Cash: {best_cash['strategy']}")
            print(f"   ROI: {best_cash.get('avg_roi', 0):+.1f}%")

        print("\n📝 Recommendations:")
        print("""
1. GPP: Force MORE 4-5 player stacks (83% of winners use them)
2. Cash: Avoid heavy correlation, focus on floor
3. All: Low ownership is OK - stacks rarely exceed 1% owned
4. Test more to find your edge against the 1.3% sharks
        """)


def main():
    """Main execution"""

    runner = CleanSimulationRunner()

    print("\n🎮 CLEAN SIMULATION RUNNER")
    print("=" * 50)
    print("Options:")
    print("1. Quick test (20 slates)")
    print("2. Standard test (50 slates)")
    print("3. Thorough test (100 slates)")
    print("4. Test single strategy")

    choice = input("\nSelect (1-4): ")

    if choice == '1':
        runner.run_all_tests(20)
    elif choice == '2':
        runner.run_all_tests(50)
    elif choice == '3':
        runner.run_all_tests(100)
    elif choice == '4':
        print("\nAvailable strategies:")
        for contest_type, strategies in WORKING_STRATEGIES.items():
            print(f"  {contest_type.upper()}: {strategies}")

        strategy = input("Enter strategy name: ")
        contest_type = input("Contest type (gpp/cash): ")
        slates = int(input("Number of slates: "))

        result = runner.run_strategy_test(strategy, contest_type, slates)
        runner._print_summary(result)
    else:
        print("Running standard test...")
        runner.run_all_tests(50)


if __name__ == "__main__":
    main()