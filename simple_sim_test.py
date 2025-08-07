#!/usr/bin/env python3
"""
Test script for small slate optimization
Save this as: test_small_slate.py
Run from: All_in_one_optimizer directory
"""

import sys

sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem
from collections import defaultdict


def test_small_slate():
    """Test 2-game slate optimization"""

    print("=" * 60)
    print("SMALL SLATE (2-GAME) OPTIMIZATION TEST")
    print("=" * 60)

    system = UnifiedCoreSystem()

    # Load the 2-game slate
    csv_path = "/home/michael/Downloads/DKSalaries(49).csv"
    system.load_csv(csv_path)

    # First, check what we have with confirmed only
    print("\n1️⃣ CHECKING CONFIRMED PLAYERS:")
    print("-" * 40)
    system.build_player_pool(include_unconfirmed=False)

    # Position breakdown
    positions = defaultdict(int)
    for p in system.player_pool:
        pos = 'P' if p.position in ['P', 'SP', 'RP'] else p.position
        positions[pos] += 1

    print(f"Total confirmed: {len(system.player_pool)}")
    print("\nPosition breakdown:")

    min_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

    for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
        count = positions.get(pos, 0)
        needed = min_needed.get(pos, 0)
        status = "✅" if count >= needed else "❌"
        print(f"  {status} {pos}: {count}/{needed}")

    # Check if we need manual additions
    missing = []
    for pos, needed in min_needed.items():
        if positions.get(pos, 0) < needed:
            missing.append(pos)

    if missing:
        print(f"\n⚠️ Missing positions: {missing}")
        print("You need to add manual selections!")

        # Example of adding manual selections
        print("\n2️⃣ ADDING MANUAL SELECTIONS (Example):")
        print("-" * 40)

        # YOU WOULD REPLACE THESE WITH ACTUAL PLAYER NAMES
        manual_players = [
            # "Pitcher Name",  # Add if missing pitchers
            # "Catcher Name",  # Add if missing catchers
        ]

        if manual_players:
            system.build_player_pool(
                include_unconfirmed=False,
                manual_selections=set(manual_players)
            )
            print(f"Pool with manual additions: {len(system.player_pool)}")

    # Try optimization with confirmed only
    print("\n3️⃣ ATTEMPTING OPTIMIZATION (CONFIRMED ONLY):")
    print("-" * 40)

    try:
        lineups = system.optimize_lineup('tournament_winner_gpp', 'gpp', 1)

        if lineups and len(lineups) > 0:
            lineup = lineups[0]
            print(f"✅ SUCCESS! Generated lineup")
            print(f"   Score: {lineup['score']:.1f}")
            print(f"   Salary: ${lineup['salary']}")

            # Check stacking
            teams = defaultdict(int)
            for p in lineup['players']:
                if p.get('position') not in ['P', 'SP', 'RP']:
                    teams[p.get('team')] += 1

            if teams:
                max_stack = max(teams.values())
                print(f"   Stack size: {max_stack} players")
        else:
            print("❌ Failed to generate lineup")
            print("   Try adding manual selections or use include_unconfirmed=True")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Likely not enough players at certain positions")

    # Alternative: Try with all players
    print("\n4️⃣ ATTEMPTING WITH ALL PLAYERS (FALLBACK):")
    print("-" * 40)

    system.build_player_pool(include_unconfirmed=True)
    print(f"Total players (including unconfirmed): {len(system.player_pool)}")

    try:
        lineups = system.optimize_lineup('tournament_winner_gpp', 'gpp', 1)

        if lineups and len(lineups) > 0:
            print(f"✅ Generated lineup with all players")
            print(f"   Score: {lineups[0]['score']:.1f}")
            print("\n⚠️ Note: This includes unconfirmed players who may not play!")
        else:
            print("❌ Still failed - check position requirements")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_small_slate()