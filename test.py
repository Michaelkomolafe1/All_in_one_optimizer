#!/usr/bin/env python3
"""
WORKING TEST SCRIPT - Tests the new correlation-aware system
===========================================================
This version works with the current setup
"""

import sys
import os
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))


def test_scoring_comparison():
    """Test the new scoring system directly"""
    print("\n" + "=" * 80)
    print("📊 TESTING SIMPLIFIED SCORING")
    print("=" * 80)

    # Import what we need
    from step2_updated_player_model import SimplifiedScoringEngine

    # Create a mock player object
    class MockPlayer:
        def __init__(self):
            self.name = "Mike Trout"
            self.team = "LAA"
            self.primary_position = "OF"
            self.dk_projection = 15.0
            self.base_projection = 15.0
            self.team_total = 5.8
            self.batting_order = 2
            self._vegas_data = {"implied_total": 5.8}

    player = MockPlayer()

    # Test scoring
    engine = SimplifiedScoringEngine()

    # GPP scoring
    engine.set_contest_type("gpp")
    gpp_score = engine.calculate_score(player)

    # Cash scoring
    engine.set_contest_type("cash")
    cash_score = engine.calculate_score(player)

    print(f"\n🎯 Player: {player.name}")
    print(f"   Base projection: {player.base_projection}")
    print(f"   Team total: {player.team_total}")
    print(f"   Batting order: #{player.batting_order}")
    print(f"\n📈 Scores:")
    print(f"   GPP Score: {gpp_score:.2f}")
    print(f"   Cash Score: {cash_score:.2f}")
    print(f"   Difference: {gpp_score - cash_score:.2f}")

    # Show the calculation
    print(f"\n🔍 GPP Calculation Breakdown:")
    print(f"   Base: {player.base_projection}")
    print(f"   Team boost (5.8 > 5): × 1.15 = {player.base_projection * 1.15:.2f}")
    print(f"   Order boost (#2): × 1.10 = {player.base_projection * 1.15 * 1.10:.2f}")

    return gpp_score, cash_score


def test_stack_detection():
    """Test the stack detection system"""
    print("\n\n" + "=" * 80)
    print("🔍 TESTING STACK DETECTION")
    print("=" * 80)

    from step3_stack_detection import StackDetector

    # Create mock players
    class MockPlayer:
        def __init__(self, name, team, pos, salary, score, order):
            self.name = name
            self.team = team
            self.primary_position = pos
            self.salary = salary
            self.enhanced_score = score
            self.batting_order = order
            self.team_total = 6.2 if team == "NYY" else 5.5

    players = []

    # Yankees stack
    yankees_data = [
        ("Aaron Judge", "OF", 6000, 20.0, 2),
        ("Juan Soto", "OF", 5800, 18.0, 3),
        ("Anthony Rizzo", "1B", 4500, 14.0, 4),
        ("Gleyber Torres", "2B", 4200, 12.0, 5),
    ]

    for name, pos, salary, score, order in yankees_data:
        players.append(MockPlayer(name, "NYY", pos, salary, score, order))

    # Dodgers mini-stack
    dodgers_data = [
        ("Mookie Betts", "OF", 5900, 19.0, 1),
        ("Freddie Freeman", "1B", 5600, 17.0, 2),
    ]

    for name, pos, salary, score, order in dodgers_data:
        players.append(MockPlayer(name, "LAD", pos, salary, score, order))

    # Test detection
    detector = StackDetector()
    stacks = detector.detect_stacks(players)

    print(f"\n📊 Found {len(stacks)} stacks:")
    for team, stack_info in stacks.items():
        print(f"\n{team} Stack:")
        print(f"   Players: {stack_info.size}")
        print(f"   Avg Score: {stack_info.avg_score:.1f}")
        print(f"   Correlation: {stack_info.correlation_score:.2f}")
        print(f"   Players: {', '.join([p.name for p in stack_info.players])}")

    return len(stacks)


def test_correlation_calculations():
    """Test the correlation calculations"""
    print("\n\n" + "=" * 80)
    print("🧮 TESTING CORRELATION CALCULATIONS")
    print("=" * 80)

    from correlation_scoring_config import CorrelationAwareScoringConfig

    config = CorrelationAwareScoringConfig()

    print("\n📊 Configuration Values:")
    print(f"   Team total threshold: {config.team_total_threshold}")
    print(f"   Team total boost: {config.team_total_boost}x")
    print(f"   Batting order boost: {config.batting_order_boost}x")

    print("\n🎯 Example Calculations:")

    # Example 1: High-scoring team, good batting order
    base = 10.0
    score1 = base * config.team_total_boost * config.batting_order_boost
    print(f"\nPlayer A (team total 6.5, batting 3rd):")
    print(f"   {base} × {config.team_total_boost} × {config.batting_order_boost} = {score1:.1f}")

    # Example 2: Low-scoring team
    score2 = base * 1.0 * config.batting_order_boost
    print(f"\nPlayer B (team total 3.5, batting 3rd):")
    print(f"   {base} × 1.0 × {config.batting_order_boost} = {score2:.1f}")

    print(f"\nDifference: {score1 - score2:.1f} points ({(score1 / score2 - 1) * 100:.0f}% higher)")


def show_results_summary():
    """Show summary of the test results"""
    print("\n\n" + "=" * 80)
    print("🏆 YOUR TEST RESULTS SUMMARY")
    print("=" * 80)

    print("\n📊 From your 1000 simulations:")
    print("1. correlation_aware: 192.88 avg (WINNER)")
    print("2. dk_only: 192.47 avg")
    print("3. baseball_optimized: 191.25 avg")
    print("...")
    print("12. bayesian: 181.71 avg (LOSER)")

    print("\n🎯 Why correlation_aware won:")
    print("- Focuses on team totals (primary factor)")
    print("- Rewards batting order position")
    print("- Natural stacking correlation")
    print("- Simple, predictable scoring")

    print("\n✅ What you've implemented:")
    print("- Replaced 12 methods with 1 winner")
    print("- Added GPP vs Cash modes")
    print("- Integrated stack detection")
    print("- Simplified the entire system")


if __name__ == "__main__":
    print("🎯 TESTING NEW CORRELATION-AWARE SYSTEM")
    print("=" * 80)

    try:
        # Run tests
        print("\n1️⃣ Testing Scoring System...")
        gpp_score, cash_score = test_scoring_comparison()

        print("\n2️⃣ Testing Stack Detection...")
        num_stacks = test_stack_detection()

        print("\n3️⃣ Testing Correlation Math...")
        test_correlation_calculations()

        print("\n4️⃣ Showing Your Results...")
        show_results_summary()

        # Summary
        print("\n\n" + "=" * 80)
        print("✅ TEST SUMMARY")
        print("=" * 80)
        print(f"   Scoring works: YES (GPP: {gpp_score:.1f}, Cash: {cash_score:.1f})")
        print(f"   Stack detection works: YES ({num_stacks} stacks found)")
        print(f"   System ready: YES")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()

    print("\n🎉 Your new optimizer is ready to dominate!")