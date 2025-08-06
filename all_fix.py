#!/usr/bin/env python3
"""
QUICK GUI TEST
=============
Test the GUI flow quickly
"""

import sys
import os
import time

# Setup paths
project_root = os.path.dirname(os.path.abspath(__file__))
if 'main_optimizer' in project_root:
    project_root = os.path.dirname(project_root)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'main_optimizer'))

print("=" * 60)
print("GUI QUICK TEST")
print("=" * 60)


def test_core_system():
    """Test the core system directly"""
    print("\n1. TESTING CORE SYSTEM")
    print("-" * 40)

    from main_optimizer.unified_core_system_updated import UnifiedCoreSystem

    system = UnifiedCoreSystem()
    csv_path = "/home/michael/Downloads/DKSalaries(46).csv"

    # Load CSV
    count = system.load_csv(csv_path)
    print("   Loaded: {} players".format(count))

    # Fetch confirmations
    confirmed = system.fetch_confirmed_players()
    print("   Confirmed: {} players".format(confirmed))

    # Build pools
    pool_confirmed = system.build_player_pool(include_unconfirmed=False)
    pool_all = system.build_player_pool(include_unconfirmed=True)

    print("   Pool (confirmed): {} players".format(pool_confirmed))
    print("   Pool (all): {} players".format(pool_all))

    return pool_confirmed, pool_all


def test_optimization():
    """Test if optimization works"""
    print("\n2. TESTING OPTIMIZATION")
    print("-" * 40)

    from main_optimizer.unified_core_system_updated import UnifiedCoreSystem

    system = UnifiedCoreSystem()
    csv_path = "/home/michael/Downloads/DKSalaries(46).csv"

    # Load and build pool
    system.load_csv(csv_path)
    system.build_player_pool(include_unconfirmed=True)

    print("   Player pool: {} players".format(len(system.player_pool)))

    # Try to optimize
    try:
        # Score players first
        if hasattr(system, 'score_players'):
            system.score_players('gpp')
            print("   Scored players for GPP")

        # Try optimization
        if hasattr(system, 'optimize_lineup'):
            lineups = system.optimize_lineup(
                strategy='projection_monster',
                contest_type='gpp',
                num_lineups=1
            )

            if lineups:
                print("   ✅ Generated {} lineup(s)!".format(len(lineups)))

                # Show first lineup
                lineup = lineups[0]
                print("\n   Sample Lineup:")
                for player in lineup.players[:5]:  # Show first 5
                    print("      - {} ({}) ${}".format(
                        player.name, player.position, player.salary
                    ))
            else:
                print("   ⚠️ No lineups generated")
    except Exception as e:
        print("   ❌ Optimization error: {}".format(str(e)))

    print("\n" + "=" * 60)


def print_instructions():
    """Print GUI instructions"""
    print("\n📋 GUI INSTRUCTIONS")
    print("-" * 40)
    print("1. Start GUI: python main_optimizer/GUI.py")
    print("2. Load CSV file")
    print("3. Click 'Fetch Confirmations'")
    print("4. You should see:")
    print("   - About 111 confirmed players")
    print("5. With 'Confirmed Only' CHECKED:")
    print("   - Rebuild Pool → 111 players")
    print("6. With 'Confirmed Only' UNCHECKED:")
    print("   - Rebuild Pool → 466 players")
    print("7. Set lineups to 1 and click 'Optimize'")


if __name__ == "__main__":
    try:
        # Test core system
        confirmed, total = test_core_system()

        # Test optimization
        test_optimization()

        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        if confirmed > 0:
            print("✅ Confirmations: WORKING ({} players)".format(confirmed))
        else:
            print("⚠️ Confirmations: No players (check if games started)")

        print("✅ Total players: {} available".format(total))
        print("\n✅ System ready for GUI!")

        # Instructions
        print_instructions()

    except Exception as e:
        print("\n❌ Error:", str(e))
        import traceback

        traceback.print_exc()