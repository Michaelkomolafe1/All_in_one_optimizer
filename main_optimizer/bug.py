#!/usr/bin/env python
# test_one_strategy.py
# Save in main_optimizer/
"""Test each strategy individually to avoid import issues"""

import sys
import os

# Fix imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'simulation'))

print("INDIVIDUAL STRATEGY TEST")
print("=" * 60)


def test_cash_strategies():
    """Test cash strategies without importing GPP"""
    print("\nTesting CASH strategies:")
    print("-" * 40)

    try:
        # Only import what we need
        from simulation.robust_dfs_simulator import generate_slate
        from unified_core_system import UnifiedCoreSystem
        from player_converter import convert_sim_players_to_unified
        from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig

        # Generate test slate
        slate = generate_slate(12345, 'classic', 'small')
        unified_players = convert_sim_players_to_unified(slate['players'])

        # Test projection_monster
        print("\n1. Testing projection_monster:")
        try:
            from cash_strategies import build_projection_monster

            system = UnifiedCoreSystem()
            system.players = unified_players
            system.csv_loaded = True
            system.enrichments_applied = True
            system.build_player_pool(include_unconfirmed=True)

            # Apply strategy
            system.player_pool = build_projection_monster(system.player_pool)

            # Optimize
            config = OptimizationConfig()
            config.contest_type = 'cash'
            optimizer = UnifiedMILPOptimizer(config)
            lineup, score = optimizer.optimize_lineup(
                players=system.player_pool,
                strategy='balanced'
            )

            if lineup and len(lineup) == 10:
                print("   ✅ SUCCESS! Generated valid lineup")
                total_salary = sum(p.salary for p in lineup)
                print(f"   Salary: ${total_salary:,}")
                print(f"   Score: {score:.1f}")
            else:
                print("   ❌ Failed to generate lineup")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    except Exception as e:
        print(f"Error setting up test: {e}")


def test_tournament_winner():
    """Test tournament winner separately"""
    print("\n\nTesting TOURNAMENT WINNER GPP:")
    print("-" * 40)

    try:
        # Test if we can import it
        print("\n1. Testing import:")
        from tournament_winner_gpp_strategy import build_tournament_winner_gpp
        print("   ✅ Import successful!")

        # Test if it works
        print("\n2. Testing strategy:")
        from simulation.robust_dfs_simulator import generate_slate
        from unified_core_system import UnifiedCoreSystem
        from player_converter import convert_sim_players_to_unified
        from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig

        slate = generate_slate(54321, 'classic', 'medium')
        unified_players = convert_sim_players_to_unified(slate['players'])

        system = UnifiedCoreSystem()
        system.players = unified_players
        system.csv_loaded = True
        system.enrichments_applied = True
        system.build_player_pool(include_unconfirmed=True)

        # Apply strategy
        system.player_pool = build_tournament_winner_gpp(system.player_pool)

        # Optimize
        config = OptimizationConfig()
        config.contest_type = 'gpp'
        optimizer = UnifiedMILPOptimizer(config)
        lineup, score = optimizer.optimize_lineup(
            players=system.player_pool,
            strategy='balanced'
        )

        if lineup and len(lineup) == 10:
            print("   ✅ SUCCESS! Generated valid lineup")
            total_salary = sum(p.salary for p in lineup)
            total_projection = sum(getattr(p, 'base_projection', 10) for p in lineup)

            print(f"   Salary: ${total_salary:,}")
            print(f"   Projection: {total_projection:.1f} points")

            # Check for stacks
            team_counts = {}
            for p in lineup:
                if p.primary_position != 'P':
                    team_counts[p.team] = team_counts.get(p.team, 0) + 1

            stacks = [(team, count) for team, count in team_counts.items() if count >= 4]
            if stacks:
                print(f"   ✅ Has 4+ man stacks: {stacks}")

        else:
            print("   ❌ Failed to generate lineup")

    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        print("\n   To fix:")
        print("   1. Make sure tournament_winner_gpp_strategy.py is in main_optimizer/")
        print("   2. Check that the function name is exactly 'build_tournament_winner_gpp'")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()


# Run tests
print("\nRunning tests without complex imports...\n")

test_cash_strategies()
test_tournament_winner()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nIf strategies are working, you can use them!")
print("The import issues are just about file organization.")