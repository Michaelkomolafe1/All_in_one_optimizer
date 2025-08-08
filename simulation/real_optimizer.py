#!/usr/bin/env python3
"""
WORKING OPTIMIZER TEST
======================
Using the CORRECT class name: UnifiedCoreSystem
"""

import sys
import os
import numpy as np
from collections import defaultdict

# Setup paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'main_optimizer'))

print("Importing your optimizer with CORRECT class name...")

# Use the CORRECT class name we found
from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
from main_optimizer.unified_player_model import UnifiedPlayer
from main_optimizer.unified_milp_optimizer import UnifiedMILPOptimizer

print("✅ Successfully imported UnifiedCoreSystem!")

# Import the realistic simulator for testing
from simulation.realistic_dfs_simulator import (
    RealisticDFSSimulator,
    generate_realistic_slate
)


# ==========================================
# TEST YOUR ACTUAL OPTIMIZER
# ==========================================

def test_your_optimizer():
    """Test your actual optimizer with correct class"""

    print("\n" + "=" * 80)
    print("TESTING YOUR OPTIMIZER: UnifiedCoreSystem")
    print("=" * 80)

    try:
        # Initialize YOUR system
        print("\n📋 Initializing UnifiedCoreSystem...")
        system = UnifiedCoreSystem()
        print("✅ System initialized successfully!")

        # Check what methods are available
        print("\n📊 Available methods:")
        methods = [m for m in dir(system) if not m.startswith('_')]
        for method in methods[:10]:  # Show first 10
            print(f"  - {method}")

        # Generate a realistic test slate
        print("\n🎲 Generating test slate...")
        slate_players = generate_realistic_slate(150, 'medium')

        # Convert to your player format
        print("📋 Converting players to your format...")
        your_players = []

        for p in slate_players:
            player = UnifiedPlayer(
                name=p.name,
                position=p.position,
                team=p.team,
                salary=p.salary
            )
            player.base_projection = p.projection
            player.ownership_projection = p.ownership * 100
            player.batting_order = getattr(p, 'batting_order', 0)
            player.implied_team_score = getattr(p, 'team_total', 4.5)

            # Add required attributes
            player.primary_position = p.position
            player.optimization_score = p.projection  # Default score

            your_players.append(player)

        print(f"✅ Created {len(your_players)} players")

        # Load players (need to find the right method)
        print("\n📥 Loading players into system...")

        # Try different methods to load players
        if hasattr(system, 'load_players'):
            system.load_players(your_players)
            print("✅ Used load_players method")
        elif hasattr(system, 'set_players'):
            system.set_players(your_players)
            print("✅ Used set_players method")
        elif hasattr(system, 'players'):
            system.players = your_players
            print("✅ Set players directly")
        else:
            print("⚠️ Could not find method to load players")
            print("Available attributes:", [a for a in dir(system) if 'player' in a.lower()])

        # Test GPP lineup generation
        print("\n" + "=" * 60)
        print("TESTING GPP LINEUP GENERATION")
        print("=" * 60)

        gpp_results = []

        for i in range(5):
            print(f"\n🎯 Generating GPP lineup {i + 1}/5...")

            try:
                # Try to find the optimize method
                if hasattr(system, 'optimize_lineup'):
                    lineup = system.optimize_lineup(
                        contest_type='gpp',
                        strategy='tournament_winner_gpp'
                    )
                elif hasattr(system, 'optimize'):
                    lineup = system.optimize(
                        contest_type='gpp',
                        strategy='tournament_winner_gpp'
                    )
                elif hasattr(system, 'build_lineup'):
                    lineup = system.build_lineup(
                        contest_type='gpp',
                        strategy='tournament_winner_gpp'
                    )
                else:
                    print("  ❌ Could not find optimization method")
                    print("  Available methods:",
                          [m for m in dir(system) if 'optim' in m.lower() or 'build' in m.lower()])
                    lineup = None

                if lineup:
                    # Analyze the lineup
                    teams = defaultdict(int)
                    total_salary = 0

                    for p in lineup[:10]:  # Ensure max 10 players
                        if hasattr(p, 'position') and p.position != 'P':
                            teams[p.team] += 1
                        if hasattr(p, 'salary'):
                            total_salary += p.salary

                    max_stack = max(teams.values()) if teams else 0

                    print(f"  ✅ Generated lineup:")
                    print(f"     Players: {len(lineup[:10])}")
                    print(f"     Salary: ${total_salary:,}")
                    print(f"     Largest stack: {max_stack} players")

                    gpp_results.append({
                        'stack_size': max_stack,
                        'salary': total_salary,
                        'valid': len(lineup) >= 10
                    })

            except Exception as e:
                print(f"  ❌ Error: {e}")

        # Analyze GPP results
        if gpp_results:
            valid_results = [r for r in gpp_results if r['valid']]
            if valid_results:
                avg_stack = np.mean([r['stack_size'] for r in valid_results])
                four_plus = sum(1 for r in valid_results if r['stack_size'] >= 4)
                four_plus_rate = (four_plus / len(valid_results)) * 100

                print(f"\n📊 GPP SUMMARY:")
                print(f"  Valid lineups: {len(valid_results)}/5")
                print(f"  Average stack size: {avg_stack:.1f}")
                print(f"  4+ player stack rate: {four_plus_rate:.0f}%")

                if four_plus_rate >= 80:
                    print(f"  ✅ EXCELLENT! Your optimizer enforces proper stacking!")
                elif four_plus_rate >= 50:
                    print(f"  ⚠️ GOOD but could be better (target: 80%+)")
                else:
                    print(f"  ❌ ISSUE: Need more 4-5 player stacks")

        # Test Cash lineup generation
        print("\n" + "=" * 60)
        print("TESTING CASH LINEUP GENERATION")
        print("=" * 60)

        cash_results = []

        for i in range(5):
            print(f"\n💰 Generating Cash lineup {i + 1}/5...")

            try:
                # Try to generate cash lineup
                if hasattr(system, 'optimize_lineup'):
                    lineup = system.optimize_lineup(
                        contest_type='cash',
                        strategy='projection_monster'
                    )
                elif hasattr(system, 'optimize'):
                    lineup = system.optimize(
                        contest_type='cash',
                        strategy='projection_monster'
                    )
                else:
                    lineup = None

                if lineup:
                    # Analyze team exposure
                    teams = defaultdict(int)
                    total_salary = 0

                    for p in lineup[:10]:
                        teams[p.team] += 1
                        if hasattr(p, 'salary'):
                            total_salary += p.salary

                    max_exposure = max(teams.values()) if teams else 0

                    print(f"  ✅ Generated lineup:")
                    print(f"     Players: {len(lineup[:10])}")
                    print(f"     Salary: ${total_salary:,}")
                    print(f"     Max team exposure: {max_exposure} players")

                    cash_results.append({
                        'max_exposure': max_exposure,
                        'salary': total_salary,
                        'valid': len(lineup) >= 10
                    })

            except Exception as e:
                print(f"  ❌ Error: {e}")

        # Analyze Cash results
        if cash_results:
            valid_results = [r for r in cash_results if r['valid']]
            if valid_results:
                avg_exposure = np.mean([r['max_exposure'] for r in valid_results])

                print(f"\n📊 CASH SUMMARY:")
                print(f"  Valid lineups: {len(valid_results)}/5")
                print(f"  Average max team exposure: {avg_exposure:.1f}")

                if avg_exposure <= 3:
                    print(f"  ✅ EXCELLENT! Good correlation control for cash!")
                else:
                    print(f"  ⚠️ Consider reducing max team exposure to 3 for cash")

        print("\n" + "=" * 80)
        print("🎉 TEST COMPLETE!")
        print("=" * 80)

        print("\n📋 KEY FINDINGS:")
        print("""
Based on this test, check if your optimizer:
1. ✅ Enforces 4-5 player stacks in GPP (80%+ of the time)
2. ✅ Limits team exposure in Cash (max 3 per team)
3. ✅ Uses full salary cap efficiently
4. ✅ Generates valid 10-player lineups

If any of these are failing, we can adjust your MILP constraints.
        """)

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_your_optimizer()