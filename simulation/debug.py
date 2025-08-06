#!/usr/bin/env python3
"""
DEBUG SIMULATION RUNNER
========================
Diagnoses why simulations are failing
Save as: simulation/debug_simulation.py
"""

import sys
import os

# Add paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'main_optimizer'))

print("=" * 60)
print("DEBUG SIMULATION RUNNER")
print("=" * 60)

# Test imports
print("\n1️⃣ TESTING IMPORTS...")
try:
    from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
    from main_optimizer.unified_player_model import UnifiedPlayer

    print("✓ Core imports successful")
except Exception as e:
    print(f"❌ Core import failed: {e}")

try:
    from fixed_simulation_core import (
        generate_realistic_slate,
        get_slate_size,
        SimulatedPlayer
    )

    print("✓ Simulation core imports successful")
except Exception as e:
    print(f"❌ Simulation core import failed: {e}")

# Test slate generation
print("\n2️⃣ TESTING SLATE GENERATION...")
try:
    test_slate = generate_realistic_slate(5, 1001)
    print(f"✓ Generated slate with {len(test_slate['players'])} players")
    print(f"  Games: {test_slate.get('num_games', 'Unknown')}")
    print(f"  Slate size: {get_slate_size(5)}")

    # Check player structure
    if test_slate['players']:
        sample_player = test_slate['players'][0]
        print(f"  Sample player attributes: {list(vars(sample_player).keys())[:5]}...")
except Exception as e:
    print(f"❌ Slate generation failed: {e}")
    import traceback

    traceback.print_exc()

# Test player conversion
print("\n3️⃣ TESTING PLAYER CONVERSION...")
try:
    if 'test_slate' in locals():
        sim_player = test_slate['players'][0]

        # Try to create UnifiedPlayer
        up = UnifiedPlayer(
            id=str(hash(sim_player.name)),
            name=sim_player.name,
            team=sim_player.team,
            salary=sim_player.salary,
            primary_position=sim_player.position,
            positions=[sim_player.position],
            base_projection=sim_player.projection
        )
        print(f"✓ Created UnifiedPlayer: {up.name}")
        print(f"  Position: {up.primary_position}")
        print(f"  Salary: ${up.salary}")
        print(f"  Projection: {up.base_projection}")
except Exception as e:
    print(f"❌ Player conversion failed: {e}")
    import traceback

    traceback.print_exc()

# Test strategy execution
print("\n4️⃣ TESTING STRATEGY EXECUTION...")
try:
    from main_optimizer.cash_strategies import build_projection_monster

    if 'test_slate' in locals():
        # Convert all players
        unified_players = []
        for sp in test_slate['players']:
            up = UnifiedPlayer(
                id=str(hash(sp.name)),
                name=sp.name,
                team=sp.team,
                salary=sp.salary,
                primary_position=sp.position,
                positions=[sp.position],
                base_projection=sp.projection
            )
            up.is_pitcher = (sp.position == 'P')
            up.ownership_projection = sp.ownership
            unified_players.append(up)

        print(f"  Converted {len(unified_players)} players")

        # Try to run strategy
        result = build_projection_monster(unified_players)

        if result:
            print(f"✓ Strategy returned result")
            print(f"  Type: {type(result)}")
            print(f"  Length: {len(result) if hasattr(result, '__len__') else 'N/A'}")

            if isinstance(result, list) and len(result) > 0:
                print(f"  First player: {result[0].name if hasattr(result[0], 'name') else result[0]}")
        else:
            print(f"❌ Strategy returned None or empty")

except Exception as e:
    print(f"❌ Strategy execution failed: {e}")
    import traceback

    traceback.print_exc()

# Test single simulation
print("\n5️⃣ TESTING SINGLE SIMULATION...")
try:
    from comprehensive_simulation_runner import ComprehensiveSimulationRunner

    runner = ComprehensiveSimulationRunner(num_cores=1)

    # Run single simulation
    test_args = (2001, 7, 'cash', 50)  # slate_id, num_games, contest_type, field_size

    print(f"  Running simulation with args: {test_args}")
    result = runner.run_single_slate_simulation(test_args)

    if 'error' in result:
        print(f"❌ Simulation failed with error: {result['error']}")

        # Try to get more details
        if 'slate_id' in result:
            print(f"  Slate ID: {result['slate_id']}")
        if 'strategy' in result:
            print(f"  Strategy: {result['strategy']}")
    else:
        print(f"✓ Simulation successful!")
        print(f"  Your score: {result.get('your_score', 'N/A')}")
        print(f"  Your rank: {result.get('your_rank', 'N/A')}")
        print(f"  ROI: {result.get('roi', 'N/A')}%")

except Exception as e:
    print(f"❌ Single simulation test failed: {e}")
    import traceback

    traceback.print_exc()

# Check strategy return format
print("\n6️⃣ CHECKING STRATEGY RETURN FORMAT...")
try:
    from main_optimizer.gpp_strategies import build_correlation_value
    from main_optimizer.cash_strategies import build_pitcher_dominance

    strategies_to_test = {
        'projection_monster': build_projection_monster,
        'pitcher_dominance': build_pitcher_dominance,
        'correlation_value': build_correlation_value,
    }

    if 'unified_players' in locals():
        for name, func in strategies_to_test.items():
            try:
                result = func(unified_players)
                print(f"\n  {name}:")
                print(f"    Returns: {type(result)}")

                if result is None:
                    print(f"    ❌ Returns None!")
                elif isinstance(result, list):
                    print(f"    ✓ Returns list with {len(result)} items")
                    if len(result) > 0:
                        print(f"    First item type: {type(result[0])}")
                elif hasattr(result, 'players'):
                    print(f"    Returns object with players attribute")
                    print(f"    Players: {len(result.players) if result.players else 0}")
                else:
                    print(f"    ⚠️ Unexpected return type!")

            except Exception as e:
                print(f"    ❌ Error: {e}")

except Exception as e:
    print(f"❌ Strategy format check failed: {e}")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)

# Summary
print("\n📋 SUMMARY:")
print("Check the errors above to identify the issue.")
print("Most likely causes:")
print("1. Strategies returning None instead of a list")
print("2. Strategies expecting different player format")
print("3. Not enough valid players to build lineup")
print("4. Position requirements not being met")

print("\n💡 QUICK FIX:")
print("If strategies are returning None, they might not be")
print("finding enough valid players. Check that:")
print("1. Players have optimization_score > 0")
print("2. Position requirements can be met")
print("3. Salary cap constraints are satisfied")