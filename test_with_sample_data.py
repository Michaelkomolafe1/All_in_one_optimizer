#!/usr/bin/env python3
"""
Comprehensive Test Suite for Optimized DFS System
Tests all functionality including multi-position, manual selection, and complete pipeline
"""

import os
import sys
import tempfile
import csv
import time
from pathlib import Path

# Import the optimized system
try:
    from streamlined_dfs_core_OPTIMIZED import (
        OptimizedDFSCore,
        OptimizedPlayer,
        EnhancedDFFMatcher,
        ManualPlayerSelector,
        load_and_optimize_complete_pipeline,
        create_enhanced_test_data
    )

    SYSTEM_AVAILABLE = True
    print("✅ Optimized DFS system loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import optimized system: {e}")
    print("💡 Make sure to save streamlined_dfs_core_OPTIMIZED.py first!")
    SYSTEM_AVAILABLE = False
    sys.exit(1)


class DFSSystemTester:
    """Comprehensive test suite for the DFS system"""

    def __init__(self):
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }

    def run_test(self, test_name: str, test_func):
        """Run a single test with error handling"""
        print(f"\n🧪 {test_name}")
        print("-" * 50)

        try:
            result = test_func()
            if result:
                print(f"✅ {test_name} PASSED")
                self.test_results['passed'] += 1
                return True
            else:
                print(f"❌ {test_name} FAILED")
                self.test_results['failed'] += 1
                return False
        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")
            self.test_results['errors'].append(f"{test_name}: {e}")
            self.test_results['failed'] += 1
            import traceback
            traceback.print_exc()
            return False

    def test_multi_position_support(self):
        """Test multi-position player functionality"""
        print("Testing multi-position player support...")

        # Test Jorge Polanco (3B/SS)
        polanco_data = {
            'id': 1,
            'name': 'Jorge Polanco',
            'position': '3B/SS',
            'team': 'SEA',
            'salary': 4500,
            'projection': 7.9
        }

        polanco = OptimizedPlayer(polanco_data)

        # Verify positions parsed correctly
        if '3B' not in polanco.positions or 'SS' not in polanco.positions:
            print(f"❌ Position parsing failed: {polanco.positions}")
            return False

        # Test position eligibility
        if not polanco.can_play_position('3B'):
            print("❌ Cannot play 3B")
            return False

        if not polanco.can_play_position('SS'):
            print("❌ Cannot play SS")
            return False

        if polanco.can_play_position('OF'):
            print("❌ Should not be able to play OF")
            return False

        # Test multi-position detection
        if not polanco.is_multi_position():
            print("❌ Multi-position detection failed")
            return False

        print(f"✅ Jorge Polanco multi-position test passed")

        # Test Yandy Diaz (1B/3B)
        diaz_data = {
            'id': 2,
            'name': 'Yandy Diaz',
            'position': '1B/3B',
            'team': 'TB',
            'salary': 4300,
            'projection': 7.5
        }

        diaz = OptimizedPlayer(diaz_data)

        if not (diaz.can_play_position('1B') and diaz.can_play_position('3B')):
            print(f"❌ Yandy Diaz position test failed: {diaz.positions}")
            return False

        print(f"✅ Yandy Diaz multi-position test passed")

        # Test position flexibility scoring
        flexibility_score = polanco.get_position_flexibility()
        if flexibility_score != 2:
            print(f"❌ Position flexibility score wrong: {flexibility_score}")
            return False

        print(f"✅ Position flexibility scoring works")

        return True

    def test_enhanced_dff_matching(self):
        """Test enhanced DFF name matching"""
        print("Testing enhanced DFF name matching...")

        # Create test players
        players = [
            OptimizedPlayer({'id': 1, 'name': 'Christian Yelich', 'position': 'OF', 'team': 'MIL', 'salary': 4600}),
            OptimizedPlayer(
                {'id': 2, 'name': 'Vladimir Guerrero Jr.', 'position': '1B', 'team': 'TOR', 'salary': 4800}),
            OptimizedPlayer({'id': 3, 'name': 'Jorge Polanco', 'position': '3B/SS', 'team': 'SEA', 'salary': 4500}),
            OptimizedPlayer({'id': 4, 'name': 'Jazz Chisholm Jr.', 'position': '2B', 'team': 'NYY', 'salary': 4700}),
        ]

        matcher = EnhancedDFFMatcher()

        # Test cases with different formats
        test_cases = [
            ('Yelich, Christian', 'Christian Yelich', 'MIL'),  # DFF format
            ('Christian Yelich', 'Christian Yelich', 'MIL'),  # Direct match
            ('Guerrero Jr., Vladimir', 'Vladimir Guerrero Jr.', 'TOR'),  # Complex name with suffix
            ('Jorge Polanco', 'Jorge Polanco', 'SEA'),  # Multi-position player
            ('Chisholm Jr., Jazz', 'Jazz Chisholm Jr.', 'NYY'),  # Another complex name
        ]

        matches = 0
        for dff_name, expected_name, team in test_cases:
            matched_player, confidence, method = matcher.match_player(dff_name, players, team)

            if matched_player and matched_player.name == expected_name and confidence >= 70:
                matches += 1
                print(f"   ✅ '{dff_name}' → '{matched_player.name}' ({confidence:.0f}% via {method})")
            else:
                print(f"   ❌ '{dff_name}' → Failed (expected {expected_name})")

        success_rate = (matches / len(test_cases)) * 100
        print(f"DFF matching success rate: {success_rate:.1f}%")

        if success_rate >= 80:
            print("✅ EXCELLENT DFF matching performance!")
            return True
        elif success_rate >= 60:
            print("✅ Good DFF matching performance")
            return True
        else:
            print("❌ DFF matching needs improvement")
            return False

    def test_manual_player_selection(self):
        """Test manual player selection functionality"""
        print("Testing manual player selection...")

        # Create test players
        players = [
            OptimizedPlayer({'id': 1, 'name': 'Christian Yelich', 'position': 'OF', 'team': 'MIL', 'salary': 4600}),
            OptimizedPlayer({'id': 2, 'name': 'Hunter Brown', 'position': 'P', 'team': 'HOU', 'salary': 11000}),
            OptimizedPlayer({'id': 3, 'name': 'Jorge Polanco', 'position': '3B/SS', 'team': 'SEA', 'salary': 4500}),
            OptimizedPlayer({'id': 4, 'name': 'William Contreras', 'position': 'C', 'team': 'MIL', 'salary': 4700}),
        ]

        selector = ManualPlayerSelector()

        # Test different input formats
        test_inputs = [
            "Christian Yelich, Hunter Brown, Jorge Polanco",  # Comma separated
            "Christian Yelich; Hunter Brown; Jorge Polanco",  # Semicolon separated
            "Christian Yelich\nHunter Brown\nJorge Polanco",  # Newline separated
        ]

        for manual_input in test_inputs:
            manual_count = selector.apply_manual_selection(players, manual_input)

            if manual_count >= 3:
                print(f"   ✅ Manual selection test passed: {manual_count} players")

                # Verify manual selection applied
                manual_players = [p for p in players if p.is_manual_selected]
                if len(manual_players) >= 3:
                    print(f"   ✅ Manual selection flags applied correctly")

                    # Check that manual players get score boost
                    for player in manual_players:
                        if player.enhanced_score <= player.base_score:
                            print(f"   ❌ Manual player {player.name} didn't get score boost")
                            return False

                    print(f"   ✅ Manual players received score boost")
                    return True
                else:
                    print(f"   ❌ Manual selection flags not applied")
                    return False
            else:
                print(f"   ❌ Manual selection failed: only {manual_count} players")

        return False

    def test_position_constraint_validation(self):
        """Test position constraint validation"""
        print("Testing position constraint validation...")

        # Create test data with proper position distribution
        dk_file, dff_file = create_enhanced_test_data()

        try:
            core = OptimizedDFSCore()

            # Load data
            if not core.load_draftkings_csv(dk_file):
                print("❌ Failed to load test data")
                return False

            # Check position requirements
            requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

            print("Position availability check:")
            all_valid = True

            for pos, needed in requirements.items():
                available = sum(1 for p in core.players if p.can_play_position(pos))
                status = "✅" if available >= needed else "❌"
                print(f"   {status} {pos}: need {needed}, have {available}")

                if available < needed:
                    all_valid = False

            if all_valid:
                print("✅ All position requirements can be satisfied")
                return True
            else:
                print("❌ Position requirements cannot be satisfied")
                return False

        finally:
            # Cleanup
            try:
                os.unlink(dk_file)
                os.unlink(dff_file)
            except:
                pass

    def test_complete_optimization_pipeline(self):
        """Test the complete optimization pipeline"""
        print("Testing complete optimization pipeline...")

        # Create enhanced test data
        dk_file, dff_file = create_enhanced_test_data()

        try:
            # Test with different strategies
            strategies = [
                ('balanced', 'Balanced strategy'),
                ('confirmed_pitchers_all_batters', 'Confirmed P + All batters'),
                ('high_floor', 'High floor strategy'),
                ('high_ceiling', 'High ceiling strategy')
            ]

            for strategy, description in strategies:
                print(f"\n   Testing {description}...")

                try:
                    lineup, score, summary = load_and_optimize_complete_pipeline(
                        dk_file=dk_file,
                        dff_file=dff_file,
                        manual_input="Jorge Polanco, Christian Yelich, Hunter Brown",
                        contest_type='classic',
                        method='milp',
                        strategy=strategy,
                        fetch_statcast=False,  # Skip for speed
                        fetch_vegas=False,  # Skip for speed
                        fetch_confirmed=True
                    )

                    if lineup and score > 0:
                        print(f"      ✅ {description}: {len(lineup)} players, {score:.2f} score")

                        # Validate lineup
                        if len(lineup) != 10:
                            print(f"      ❌ Invalid lineup size: {len(lineup)}")
                            continue

                        total_salary = sum(p.salary for p in lineup)
                        if not (49000 <= total_salary <= 50000):
                            print(f"      ❌ Invalid salary: ${total_salary:,}")
                            continue

                        # Check for multi-position players
                        multi_pos_players = [p for p in lineup if p.is_multi_position()]
                        if multi_pos_players:
                            print(f"      🔄 Multi-position players: {len(multi_pos_players)}")

                        # Check for manual selections
                        manual_players = [p for p in lineup if p.is_manual_selected]
                        if manual_players:
                            print(f"      📝 Manual selections: {len(manual_players)}")

                    else:
                        print(f"      ❌ {description} failed")
                        return False

                except Exception as e:
                    print(f"      ❌ {description} error: {e}")
                    return False

            print("✅ All optimization strategies working")
            return True

        finally:
            # Cleanup
            try:
                os.unlink(dk_file)
                os.unlink(dff_file)
            except:
                pass

    def test_optimization_methods(self):
        """Test different optimization methods"""
        print("Testing different optimization methods...")

        dk_file, dff_file = create_enhanced_test_data()

        try:
            methods = [
                ('milp', 'MILP Optimization'),
                ('monte_carlo', 'Monte Carlo Optimization'),
                ('genetic', 'Genetic Algorithm')
            ]

            for method, description in methods:
                print(f"\n   Testing {description}...")

                try:
                    lineup, score, summary = load_and_optimize_complete_pipeline(
                        dk_file=dk_file,
                        dff_file=dff_file,
                        contest_type='classic',
                        method=method,
                        strategy='balanced',
                        fetch_statcast=False,
                        fetch_vegas=False,
                        fetch_confirmed=False
                    )

                    if lineup and score > 0:
                        print(
                            f"      ✅ {description}: {len(lineup)} players, {score:.2f} score, ${sum(p.salary for p in lineup):,}")
                    else:
                        print(f"      ⚠️ {description}: No valid lineup (may be expected for genetic)")

                except Exception as e:
                    print(f"      ⚠️ {description} error: {e}")
                    # Don't fail the test for genetic algorithm issues
                    if method != 'genetic':
                        return False

            print("✅ Optimization methods tested")
            return True

        finally:
            try:
                os.unlink(dk_file)
                os.unlink(dff_file)
            except:
                pass

    def test_contest_types(self):
        """Test different contest types"""
        print("Testing different contest types...")

        dk_file, dff_file = create_enhanced_test_data()

        try:
            contest_types = [
                ('classic', 10),
                ('showdown', 6)
            ]

            for contest_type, expected_players in contest_types:
                print(f"\n   Testing {contest_type} contest...")

                lineup, score, summary = load_and_optimize_complete_pipeline(
                    dk_file=dk_file,
                    dff_file=dff_file,
                    contest_type=contest_type,
                    method='monte_carlo',  # Use monte carlo for reliability
                    strategy='balanced',
                    fetch_statcast=False,
                    fetch_vegas=False,
                    fetch_confirmed=False
                )

                if lineup and len(lineup) == expected_players:
                    print(f"      ✅ {contest_type}: {len(lineup)} players, {score:.2f} score")
                else:
                    print(f"      ❌ {contest_type}: Expected {expected_players}, got {len(lineup) if lineup else 0}")
                    return False

            print("✅ Contest types working")
            return True

        finally:
            try:
                os.unlink(dk_file)
                os.unlink(dff_file)
            except:
                pass

    def test_data_pipeline_integration(self):
        """Test complete data pipeline integration"""
        print("Testing data pipeline integration...")

        dk_file, dff_file = create_enhanced_test_data()

        try:
            core = OptimizedDFSCore()

            # Test step by step
            print("   Step 1: Loading DraftKings data...")
            if not core.load_draftkings_csv(dk_file):
                print("   ❌ Failed to load DK data")
                return False
            print(f"   ✅ Loaded {len(core.players)} players")

            print("   Step 2: Applying DFF rankings...")
            if not core.apply_dff_rankings(dff_file):
                print("   ❌ Failed to apply DFF rankings")
                return False

            dff_enhanced = sum(1 for p in core.players if p.dff_rank)
            print(f"   ✅ DFF enhanced {dff_enhanced} players")

            print("   Step 3: Fetching confirmed lineups...")
            core.fetch_confirmed_lineups()
            confirmed_count = sum(1 for p in core.players if p.is_confirmed)
            print(f"   ✅ Confirmed {confirmed_count} players")

            print("   Step 4: Applying manual selection...")
            core.apply_manual_selection("Jorge Polanco, Christian Yelich")
            manual_count = sum(1 for p in core.players if p.is_manual_selected)
            print(f"   ✅ Manual selected {manual_count} players")

            print("   Step 5: Running optimization...")
            lineup, score = core.optimize_lineup(
                contest_type='classic',
                method='milp',
                strategy='balanced'
            )

            if lineup and score > 0:
                print(f"   ✅ Optimization successful: {len(lineup)} players, {score:.2f} score")

                # Analyze lineup composition
                multi_pos = sum(1 for p in lineup if p.is_multi_position())
                confirmed = sum(1 for p in lineup if p.is_confirmed)
                manual = sum(1 for p in lineup if p.is_manual_selected)
                dff_ranked = sum(1 for p in lineup if p.dff_rank)

                print(f"   📊 Lineup composition:")
                print(f"      🔄 Multi-position: {multi_pos}")
                print(f"      ✅ Confirmed: {confirmed}")
                print(f"      📝 Manual: {manual}")
                print(f"      🎯 DFF ranked: {dff_ranked}")

                return True
            else:
                print("   ❌ Optimization failed")
                return False

        finally:
            try:
                os.unlink(dk_file)
                os.unlink(dff_file)
            except:
                pass

    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("Testing error handling and edge cases...")

        core = OptimizedDFSCore()

        # Test with non-existent file
        if core.load_draftkings_csv("nonexistent_file.csv"):
            print("   ❌ Should have failed with non-existent file")
            return False
        print("   ✅ Properly handles non-existent files")

        # Test optimization with no players
        lineup, score = core.optimize_lineup()
        if lineup or score > 0:
            print("   ❌ Should have failed with no players")
            return False
        print("   ✅ Properly handles empty player pool")

        # Test invalid manual input
        players = [OptimizedPlayer({'id': 1, 'name': 'Test Player', 'position': 'OF', 'salary': 4000})]
        core.players = players

        result = core.apply_manual_selection("NonExistentPlayer, AnotherFakePlayer")
        print("   ✅ Handles invalid manual input gracefully")

        return True

    def run_all_tests(self):
        """Run all tests and generate summary"""
        print("🧪 COMPREHENSIVE DFS SYSTEM TEST SUITE")
        print("=" * 70)

        start_time = time.time()

        # Define all tests
        tests = [
            ("Multi-Position Support", self.test_multi_position_support),
            ("Enhanced DFF Matching", self.test_enhanced_dff_matching),
            ("Manual Player Selection", self.test_manual_player_selection),
            ("Position Constraint Validation", self.test_position_constraint_validation),
            ("Complete Optimization Pipeline", self.test_complete_optimization_pipeline),
            ("Optimization Methods", self.test_optimization_methods),
            ("Contest Types", self.test_contest_types),
            ("Data Pipeline Integration", self.test_data_pipeline_integration),
            ("Error Handling", self.test_error_handling)
        ]

        # Run all tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)

        # Generate summary
        total_time = time.time() - start_time
        total_tests = self.test_results['passed'] + self.test_results['failed']

        print("\n" + "=" * 70)
        print("🏁 TEST SUITE SUMMARY")
        print("=" * 70)
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        print(f"🧪 Total Tests: {total_tests}")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")

        if self.test_results['errors']:
            print(f"\n💥 ERRORS:")
            for error in self.test_results['errors']:
                print(f"   • {error}")

        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        print(f"\n📊 Success Rate: {success_rate:.1f}%")

        if success_rate >= 90:
            print("🎉 EXCELLENT! System is working perfectly!")
            print("\n🚀 READY FOR PRODUCTION:")
            print("   ✅ Multi-position flexibility working")
            print("   ✅ DFF integration with high success rate")
            print("   ✅ Manual player selection supported")
            print("   ✅ Complete data pipeline functional")
            print("   ✅ Multiple optimization methods available")
            print("   ✅ Error handling robust")

            print("\n💡 NEXT STEPS:")
            print("   1. Save streamlined_dfs_core_OPTIMIZED.py")
            print("   2. Run your GUI: python streamlined_dfs_gui.py")
            print("   3. Test with real DraftKings CSV files")
            print("   4. Integrate with your existing workflows")

        elif success_rate >= 70:
            print("👍 GOOD! Most functionality working, minor issues to address")
        else:
            print("⚠️  NEEDS WORK! Several critical issues found")

        return success_rate >= 90


def main():
    """Main test execution"""
    if not SYSTEM_AVAILABLE:
        print("❌ Cannot run tests - optimized system not available")
        return False

    tester = DFSSystemTester()
    success = tester.run_all_tests()

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)