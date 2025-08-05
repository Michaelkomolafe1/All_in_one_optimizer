# debug_strategy_data.py
# Save in main_optimizer/
"""Debug what data the simulator provides"""

import sys
import os
import json

# Fix imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'simulation'))

# Import simulation
from simulation.robust_dfs_simulator import generate_slate


def debug_simulator_data():
    """Show exactly what data structure the simulator provides"""

    print("=" * 80)
    print("DEBUGGING SIMULATOR DATA STRUCTURE")
    print("=" * 80)

    # Generate different slate sizes
    for slate_size in ['small', 'medium', 'large']:
        print("\n{} SLATE:".format(slate_size.upper()))
        print("-" * 40)

        slate = generate_slate(12345, 'classic', slate_size)

        print("Slate keys: {}".format(list(slate.keys())))
        print("Total players: {}".format(len(slate.get('players', []))))

        # Get sample players
        players = slate.get('players', [])
        if not players:
            print("NO PLAYERS FOUND!")
            continue

        # Check different position types
        pitcher = next((p for p in players if p.get('position') == 'P'), None)
        hitter = next((p for p in players if p.get('position') != 'P'), None)

        if pitcher:
            print("\nPITCHER DATA:")
            print(json.dumps(pitcher, indent=2, default=str))

        if hitter:
            print("\nHITTER DATA:")
            print(json.dumps(hitter, indent=2, default=str))

        # Check what keys are common
        if players:
            all_keys = set()
            for p in players:
                all_keys.update(p.keys())

            print("\nALL AVAILABLE KEYS:")
            for key in sorted(all_keys):
                print("  - {}".format(key))

        # Check game_data structure
        sample_with_game_data = next((p for p in players if 'game_data' in p), None)
        if sample_with_game_data:
            print("\nGAME_DATA STRUCTURE:")
            print(json.dumps(sample_with_game_data.get('game_data'), indent=2))


def test_simple_lineup_build():
    """Test building a simple lineup manually"""

    print("\n" + "=" * 80)
    print("TESTING SIMPLE LINEUP BUILD")
    print("=" * 80)

    slate = generate_slate(99999, 'classic', 'medium')
    players = slate.get('players', [])

    # Try to build a simple lineup
    lineup = []
    salary_used = 0
    positions_needed = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Sort by value
    players_with_value = []
    for p in players:
        if p.get('salary', 0) > 0:
            value = p.get('projection', 0) / (p.get('salary', 1) / 1000)
            players_with_value.append((value, p))

    players_with_value.sort(reverse=True)

    print("\nTop 10 players by value:")
    for i, (value, p) in enumerate(players_with_value[:10]):
        print("{:2d}. {} ({}) - ${} - {:.1f} pts - {:.2f} value".format(
            i + 1,
            p.get('name', 'Unknown'),
            p.get('position', '??'),
            p.get('salary', 0),
            p.get('projection', 0),
            value
        ))

    # Try to fill positions
    for value, player in players_with_value:
        pos = player.get('position')
        if positions_needed.get(pos, 0) > 0:
            if salary_used + player.get('salary', 0) <= 50000:
                lineup.append(player)
                salary_used += player.get('salary', 0)
                positions_needed[pos] -= 1

                if len(lineup) == 10:
                    break

    print("\nSimple lineup result:")
    print("  Players selected: {}".format(len(lineup)))
    print("  Total salary: ${}".format(salary_used))
    print("  Positions filled:")
    for player in lineup:
        print("    {} - {} - ${}".format(
            player.get('position'),
            player.get('name'),
            player.get('salary')
        ))


if __name__ == "__main__":
    debug_simulator_data()
    test_simple_lineup_build()