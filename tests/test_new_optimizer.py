#!/usr/bin/env python3
"""
TEST NEW OPTIMIZER - FIXED VERSION
==================================
Test the updated optimization system with proper position coverage
"""

import sys
from unified_data_system import UnifiedDataSystem
from optimal_lineup_optimizer import OptimalLineupOptimizer
from smart_confirmation_system import SmartConfirmationSystem


def test_optimizer():
    """Test the new optimization system"""
    print("🧪 TESTING NEW OPTIMIZER")
    print("=" * 50)

    # Test 1: Data System
    print("\n1️⃣ Testing Unified Data System...")
    data_system = UnifiedDataSystem()

    # Test team normalization
    test_teams = ['New York Yankees', 'NYY', '147', 'yanks', 'LA Angels']
    for team in test_teams:
        normalized = data_system.normalize_team(team)
        print(f"   '{team}' → '{normalized}'")

    # Test name matching
    test_names = [
        ('Mike Trout', 'Michael Trout'),
        ('J.D. Martinez', 'JD Martinez'),
        ('Ronald Acuna Jr.', 'Ronald Acuna'),
        ('Shohei Ohtani', 'Shohei Ohtani')
    ]

    print("\n   Name matching tests:")
    for dk_name, other_name in test_names:
        matches = data_system.match_player_names(dk_name, other_name)
        print(f"   '{dk_name}' ↔ '{other_name}': {matches}")

    # Test 2: Optimizer
    print("\n2️⃣ Testing Optimal Lineup Optimizer...")

    # Create mock players with PROPER POSITION COVERAGE
    class MockPlayer:
        def __init__(self, name, position, salary, score, team='NYY'):
            self.name = name
            self.primary_position = position
            self.positions = [position]
            self.salary = salary
            self.enhanced_score = score
            self.team = team
            self.is_confirmed = False
            self.confirmation_source = []

    # Create enough players for each position
    test_players = [
        # Pitchers (need at least 2)
        MockPlayer("Gerrit Cole", "P", 10000, 18.5),
        MockPlayer("Shane Bieber", "P", 9500, 17.8),
        MockPlayer("Dylan Cease", "P", 8500, 16.2),

        # Catchers (need at least 1)
        MockPlayer("Will Smith", "C", 4000, 8.2),
        MockPlayer("Salvador Perez", "C", 3800, 7.8),

        # First Base (need at least 1)
        MockPlayer("Freddie Freeman", "1B", 5200, 10.5),
        MockPlayer("Pete Alonso", "1B", 4800, 9.5),

        # Second Base (need at least 1)
        MockPlayer("Jose Altuve", "2B", 4800, 9.8),
        MockPlayer("Marcus Semien", "2B", 4400, 8.8),

        # Third Base (need at least 1)
        MockPlayer("Manny Machado", "3B", 4600, 9.2),
        MockPlayer("Jose Ramirez", "3B", 5000, 10.0),

        # Shortstop (need at least 1)
        MockPlayer("Trea Turner", "SS", 4400, 8.9),
        MockPlayer("Corey Seager", "SS", 4600, 9.1),

        # Outfield (need at least 3)
        MockPlayer("Aaron Judge", "OF", 6000, 12.5),
        MockPlayer("Mike Trout", "OF", 5800, 11.8),
        MockPlayer("Mookie Betts", "OF", 5600, 11.2),
        MockPlayer("Ronald Acuna Jr.", "OF", 5400, 10.9),
        MockPlayer("Juan Soto", "OF", 5200, 10.6),
        MockPlayer("Kyle Tucker", "OF", 4800, 9.6),
    ]

    optimizer = OptimalLineupOptimizer()

    # Test classic optimization
    result = optimizer.optimize_classic_lineup(test_players)

    if result.optimization_status == "Optimal":
        print(f"   ✅ Classic optimization successful!")
        print(f"   💰 Salary: ${result.total_salary:,}")
        print(f"   📈 Points: {result.total_score:.2f}")
        print(f"   📊 Lineup:")
        for player in result.lineup:
            pos = getattr(player, 'assigned_position', player.primary_position)
            print(f"      {pos}: {player.name} - ${player.salary:,} - {player.enhanced_score:.1f}pts")
    else:
        print(f"   ❌ Optimization failed: {result.optimization_status}")

    # Test showdown optimization
    print("\n   Testing Showdown optimization...")
    showdown_result = optimizer.optimize_showdown_lineup(test_players[:8])

    if showdown_result.optimization_status == "Optimal":
        print(f"   ✅ Showdown optimization successful!")
        print(f"   💰 Salary: ${showdown_result.total_salary:,}")
        print(f"   📈 Points: {showdown_result.total_score:.2f}")
        print(f"   📊 Showdown Lineup:")
        for player in showdown_result.lineup:
            mult = getattr(player, 'multiplier', 1.0)
            pos = getattr(player, 'assigned_position', 'UTIL')
            print(f"      {pos}: {player.name} ({mult}x) - ${int(player.salary * mult):,}")
    else:
        print(f"   ❌ Showdown failed: {showdown_result.optimization_status}")

    print("\n✅ All tests complete!")


if __name__ == "__main__":
    test_optimizer()