#!/usr/bin/env python3
"""
CONFIRMATION WORKFLOW PERFORMANCE OPTIMIZER
===========================================
Test and optimize the actual lineup confirmation process
"""

import time
import pandas as pd
from typing import Dict, List, Set
from unified_data_system import UnifiedDataSystem
from enhanced_name_matcher import EnhancedNameMatcher


class ConfirmationWorkflowTester:
    """Test the actual confirmation workflow performance"""

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.current_system = UnifiedDataSystem()
        self.enhanced_system = EnhancedNameMatcher()

        # Load CSV data
        self.csv_data = pd.read_csv(csv_path)
        print(f"📄 Loaded {len(self.csv_data)} players from CSV")

        # Extract player names and teams
        self.csv_players = []
        name_col = None
        team_col = None

        for col in self.csv_data.columns:
            if 'name' in col.lower():
                name_col = col
            if 'team' in col.lower():
                team_col = col

        if name_col:
            for _, row in self.csv_data.iterrows():
                self.csv_players.append({
                    'name': row[name_col],
                    'team': row.get(team_col, 'UNK') if team_col else 'UNK'
                })

        # Simulate confirmed lineups (like what comes from MLB API)
        self.mock_confirmed_lineups = self._create_mock_lineups()

    def _create_mock_lineups(self) -> Dict:
        """Create realistic mock confirmed lineups"""
        # Simulate what your confirmation system gets from MLB API
        mock_lineups = {
            'NYY': [
                {'name': 'Aaron Judge', 'position': 'RF', 'order': 1},
                {'name': 'Gleyber Torres', 'position': '2B', 'order': 2},
                {'name': 'Anthony Rizzo', 'position': '1B', 'order': 3},
                {'name': 'Giancarlo Stanton', 'position': 'DH', 'order': 4},
                {'name': 'DJ LeMahieu', 'position': '3B', 'order': 5},
                {'name': 'Jose Trevino', 'position': 'C', 'order': 6},
                {'name': 'Oswaldo Cabrera', 'position': 'LF', 'order': 7},
                {'name': 'Isiah Kiner-Falefa', 'position': 'SS', 'order': 8},
                {'name': 'Harrison Bader', 'position': 'CF', 'order': 9}
            ],
            'BOS': [
                {'name': 'Rafael Devers', 'position': '3B', 'order': 1},
                {'name': 'Alex Verdugo', 'position': 'LF', 'order': 2},
                {'name': 'Xander Bogaerts', 'position': 'SS', 'order': 3},
                {'name': 'J.D. Martinez', 'position': 'DH', 'order': 4},
                {'name': 'Trevor Story', 'position': '2B', 'order': 5},
                {'name': 'Christian Arroyo', 'position': '1B', 'order': 6},
                {'name': 'Kike Hernandez', 'position': 'CF', 'order': 7},
                {'name': 'Christian Vazquez', 'position': 'C', 'order': 8},
                {'name': 'Jarren Duran', 'position': 'RF', 'order': 9}
            ],
            'LAD': [
                {'name': 'Mookie Betts', 'position': 'RF', 'order': 1},
                {'name': 'Freddie Freeman', 'position': '1B', 'order': 2},
                {'name': 'Trea Turner', 'position': 'SS', 'order': 3},
                {'name': 'Will Smith', 'position': 'C', 'order': 4},
                {'name': 'Max Muncy', 'position': '3B', 'order': 5},
                {'name': 'Justin Turner', 'position': 'DH', 'order': 6},
                {'name': 'Cody Bellinger', 'position': 'CF', 'order': 7},
                {'name': 'Gavin Lux', 'position': '2B', 'order': 8},
                {'name': 'Chris Taylor', 'position': 'LF', 'order': 9}
            ]
        }

        # Add variations to test name matching
        # Simulate what actually comes from MLB API (full names, different formats)
        api_variations = {
            'NYY': [
                {'name': 'Aaron James Judge', 'position': 'RF', 'order': 1},
                {'name': 'Gleyber David Torres', 'position': '2B', 'order': 2},
                {'name': 'Anthony Vincent Rizzo', 'position': '1B', 'order': 3},
                {'name': 'Giancarlo Cruz-Michael Stanton', 'position': 'DH', 'order': 4},
                {'name': 'David John LeMahieu', 'position': '3B', 'order': 5},
                {'name': 'José Treviño', 'position': 'C', 'order': 6},
                {'name': 'Oswaldo Cabrera', 'position': 'LF', 'order': 7},
                {'name': 'Isiah Kiner-Falefa', 'position': 'SS', 'order': 8},
                {'name': 'Harrison Joseph Bader', 'position': 'CF', 'order': 9}
            ]
        }

        # Mix regular and API-style names to simulate real scenario
        mock_lineups.update(api_variations)

        return mock_lineups

    def test_current_confirmation_workflow(self) -> Dict:
        """Test current confirmation workflow performance"""
        print("\n🔍 TESTING CURRENT CONFIRMATION WORKFLOW")
        print("=" * 50)

        start_time = time.time()
        confirmed_players = []
        total_comparisons = 0

        # Simulate the actual confirmation process
        for csv_player in self.csv_players:
            csv_name = csv_player['name']
            csv_team = csv_player['team']

            # Check against all confirmed lineups
            for team, lineup in self.mock_confirmed_lineups.items():
                team_normalized = self.current_system.normalize_team(team)
                csv_team_normalized = self.current_system.normalize_team(csv_team)

                # Only check same team
                if team_normalized == csv_team_normalized:
                    for lineup_player in lineup:
                        total_comparisons += 1
                        lineup_name = lineup_player['name']

                        # This is the bottleneck - name matching
                        if self.current_system.match_player_names(csv_name, lineup_name):
                            confirmed_players.append({
                                'csv_name': csv_name,
                                'confirmed_name': lineup_name,
                                'team': team,
                                'order': lineup_player['order']
                            })
                            break

        current_time = time.time() - start_time

        print(f"⏱️  Total time: {current_time:.3f}s")
        print(f"📊 Total comparisons: {total_comparisons:,}")
        print(f"🎯 Confirmed players: {len(confirmed_players)}")
        print(f"📈 Comparisons per second: {total_comparisons / current_time:,.0f}")

        return {
            'time': current_time,
            'comparisons': total_comparisons,
            'confirmed': len(confirmed_players),
            'rate': total_comparisons / current_time
        }

    def test_enhanced_confirmation_workflow(self) -> Dict:
        """Test enhanced confirmation workflow performance"""
        print("\n🚀 TESTING ENHANCED CONFIRMATION WORKFLOW")
        print("=" * 50)

        start_time = time.time()
        confirmed_players = []
        total_comparisons = 0

        # Simulate the same process with enhanced system
        for csv_player in self.csv_players:
            csv_name = csv_player['name']
            csv_team = csv_player['team']

            # Check against all confirmed lineups
            for team, lineup in self.mock_confirmed_lineups.items():
                team_normalized = self.enhanced_system.normalize_team(team)
                csv_team_normalized = self.enhanced_system.normalize_team(csv_team)

                # Only check same team
                if team_normalized == csv_team_normalized:
                    for lineup_player in lineup:
                        total_comparisons += 1
                        lineup_name = lineup_player['name']

                        # Enhanced name matching with caching
                        if self.enhanced_system.match_player_names(csv_name, lineup_name):
                            confirmed_players.append({
                                'csv_name': csv_name,
                                'confirmed_name': lineup_name,
                                'team': team,
                                'order': lineup_player['order']
                            })
                            break

        enhanced_time = time.time() - start_time

        print(f"⏱️  Total time: {enhanced_time:.3f}s")
        print(f"📊 Total comparisons: {total_comparisons:,}")
        print(f"🎯 Confirmed players: {len(confirmed_players)}")
        print(f"📈 Comparisons per second: {total_comparisons / enhanced_time:,.0f}")

        return {
            'time': enhanced_time,
            'comparisons': total_comparisons,
            'confirmed': len(confirmed_players),
            'rate': total_comparisons / enhanced_time
        }

    def test_optimized_workflow(self) -> Dict:
        """Test an optimized confirmation workflow"""
        print("\n⚡ TESTING OPTIMIZED CONFIRMATION WORKFLOW")
        print("=" * 50)

        start_time = time.time()
        confirmed_players = []
        total_comparisons = 0

        # OPTIMIZATION 1: Pre-index lineup players by team
        lineup_by_team = {}
        for team, lineup in self.mock_confirmed_lineups.items():
            team_norm = self.enhanced_system.normalize_team(team)
            if team_norm not in lineup_by_team:
                lineup_by_team[team_norm] = []
            lineup_by_team[team_norm].extend(lineup)

        # OPTIMIZATION 2: Pre-normalize all lineup names
        for team in lineup_by_team:
            for player in lineup_by_team[team]:
                player['normalized_name'] = player['name'].lower().strip()

        # OPTIMIZATION 3: Group CSV players by team
        csv_by_team = {}
        for csv_player in self.csv_players:
            team_norm = self.enhanced_system.normalize_team(csv_player['team'])
            if team_norm not in csv_by_team:
                csv_by_team[team_norm] = []
            csv_by_team[team_norm].append(csv_player)

        # OPTIMIZATION 4: Only check players from teams that have confirmed lineups
        for team in csv_by_team:
            if team in lineup_by_team:
                csv_players_for_team = csv_by_team[team]
                lineup_players_for_team = lineup_by_team[team]

                for csv_player in csv_players_for_team:
                    csv_name = csv_player['name']

                    # OPTIMIZATION 5: Early exact match check
                    csv_name_norm = csv_name.lower().strip()
                    exact_match = None
                    for lineup_player in lineup_players_for_team:
                        if csv_name_norm == lineup_player['normalized_name']:
                            exact_match = lineup_player
                            break

                    if exact_match:
                        total_comparisons += 1
                        confirmed_players.append({
                            'csv_name': csv_name,
                            'confirmed_name': exact_match['name'],
                            'team': team,
                            'order': exact_match['order']
                        })
                    else:
                        # OPTIMIZATION 6: Only do complex matching if no exact match
                        for lineup_player in lineup_players_for_team:
                            total_comparisons += 1
                            if self.enhanced_system.match_player_names(csv_name, lineup_player['name']):
                                confirmed_players.append({
                                    'csv_name': csv_name,
                                    'confirmed_name': lineup_player['name'],
                                    'team': team,
                                    'order': lineup_player['order']
                                })
                                break

        optimized_time = time.time() - start_time

        print(f"⏱️  Total time: {optimized_time:.3f}s")
        print(f"📊 Total comparisons: {total_comparisons:,}")
        print(f"🎯 Confirmed players: {len(confirmed_players)}")
        print(f"📈 Comparisons per second: {total_comparisons / optimized_time:,.0f}")

        return {
            'time': optimized_time,
            'comparisons': total_comparisons,
            'confirmed': len(confirmed_players),
            'rate': total_comparisons / optimized_time
        }

    def run_workflow_comparison(self):
        """Run complete workflow comparison"""
        print("🔬 CONFIRMATION WORKFLOW PERFORMANCE ANALYSIS")
        print("=" * 60)
        print(f"📄 Testing with {len(self.csv_players)} CSV players")
        print(f"📋 Against {sum(len(lineup) for lineup in self.mock_confirmed_lineups.values())} confirmed lineup spots")

        # Test all three approaches
        current_results = self.test_current_confirmation_workflow()
        enhanced_results = self.test_enhanced_confirmation_workflow()
        optimized_results = self.test_optimized_workflow()

        # Summary
        print("\n📊 WORKFLOW COMPARISON SUMMARY")
        print("=" * 50)

        approaches = [
            ("Current System", current_results),
            ("Enhanced System", enhanced_results),
            ("Optimized Workflow", optimized_results)
        ]

        print(f"{'Approach':<20} {'Time':<8} {'Rate':<12} {'Speedup'}")
        print("-" * 50)

        baseline_time = current_results['time']
        for name, results in approaches:
            speedup = f"{baseline_time / results['time']:.1f}x" if results['time'] > 0 else "∞"
            print(f"{name:<20} {results['time']:.3f}s {results['rate']:>8.0f}/s {speedup:>8}")

        # Recommendation
        best_time = min(r['time'] for _, r in approaches)
        best_approach = next(name for name, r in approaches if r['time'] == best_time)

        print(f"\n🎯 FASTEST APPROACH: {best_approach}")

        if best_approach == "Optimized Workflow":
            speedup = baseline_time / optimized_results['time']
            print(f"🚀 {speedup:.1f}x faster than current system!")
            print("\n💡 OPTIMIZATIONS TO IMPLEMENT:")
            print("1. Pre-index lineups by team")
            print("2. Pre-normalize all names")
            print("3. Group CSV players by team")
            print("4. Try exact matches first")
            print("5. Only do complex matching when needed")


def main():
    """Run confirmation workflow performance test"""
    import sys

    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        tester = ConfirmationWorkflowTester(csv_path)
        tester.run_workflow_comparison()
    else:
        print("Usage: python confirmation_workflow_optimizer.py your_file.csv")


if __name__ == "__main__":
    main()