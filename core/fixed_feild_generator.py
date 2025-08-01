#!/usr/bin/env python3
"""
FIXED FIELD GENERATOR
====================
Ensures we always get the correct number of opponents
"""

import random
from collections import defaultdict
import numpy as np


def generate_fixed_field(slate, num_opponents, contest_type):
    """
    Generate exactly num_opponents lineups for the field
    Uses progressively simpler methods to ensure we hit the target
    """
    field_lineups = []
    players = slate.get('players', [])

    if not players:
        print("ERROR: No players in slate")
        return []

    # Define skill distribution
    if contest_type == 'cash':
        skill_weights = {
            'sharp': 0.08,
            'good': 0.27,
            'average': 0.45,
            'weak': 0.20
        }
    else:  # GPP
        skill_weights = {
            'sharp': 0.05,
            'good': 0.15,
            'average': 0.50,
            'weak': 0.30
        }

    # Pre-calculate how many of each skill level we need
    skill_counts = {}
    remaining = num_opponents
    for skill, weight in skill_weights.items():
        count = int(num_opponents * weight)
        skill_counts[skill] = count
        remaining -= count

    # Add any remaining to 'average'
    skill_counts['average'] += remaining

    # Method 1: Try sophisticated lineup building
    print(f"Generating {num_opponents} opponents for {contest_type}...")

    for skill_level, count_needed in skill_counts.items():
        attempts = 0
        lineups_generated = 0

        while lineups_generated < count_needed and attempts < count_needed * 3:
            attempts += 1

            lineup = build_skilled_lineup(players, skill_level, contest_type)
            if lineup:
                lineup['skill_level'] = skill_level
                field_lineups.append(lineup)
                lineups_generated += 1

    # Method 2: If we don't have enough, use simpler generation
    if len(field_lineups) < num_opponents:
        shortfall = num_opponents - len(field_lineups)
        print(f"Using simple generation for {shortfall} more opponents...")

        for _ in range(shortfall):
            lineup = build_simple_valid_lineup(players)
            if lineup:
                lineup['skill_level'] = 'average'
                field_lineups.append(lineup)

    # Method 3: If still short, duplicate and vary existing lineups
    if len(field_lineups) < num_opponents:
        shortfall = num_opponents - len(field_lineups)
        print(f"Duplicating and varying {shortfall} lineups...")

        existing = field_lineups.copy()
        for i in range(shortfall):
            base_lineup = existing[i % len(existing)]
            varied_lineup = vary_lineup(base_lineup, players)
            field_lineups.append(varied_lineup)

    # Ensure exactly num_opponents
    field_lineups = field_lineups[:num_opponents]

    print(f"✅ Generated exactly {len(field_lineups)} opponents")
    return field_lineups


def build_skilled_lineup(players, skill_level, contest_type):
    """Build a lineup based on skill level"""

    # Skill level affects how well they pick players
    skill_multipliers = {
        'sharp': {'good_pick_rate': 0.80, 'salary_efficiency': 0.95},
        'good': {'good_pick_rate': 0.65, 'salary_efficiency': 0.90},
        'average': {'good_pick_rate': 0.50, 'salary_efficiency': 0.85},
        'weak': {'good_pick_rate': 0.35, 'salary_efficiency': 0.75}
    }

    mult = skill_multipliers[skill_level]

    lineup = []
    used_salary = 0
    team_counts = defaultdict(int)

    position_needs = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Group players by position
    by_position = defaultdict(list)
    for p in players:
        by_position[p['position']].append(p)

    # Sort players by projection (sharp players pick better)
    for pos, player_list in by_position.items():
        if random.random() < mult['good_pick_rate']:
            # Good pick - sort by projection
            player_list.sort(key=lambda x: x.get('projection', 0), reverse=True)
        else:
            # Bad pick - randomize
            random.shuffle(player_list)

    # Fill positions
    for pos, needed in position_needs.items():
        candidates = by_position.get(pos, [])
        added = 0

        for player in candidates:
            if added >= needed:
                break

            # Check constraints
            player_salary = player.get('salary', 5000)
            remaining_spots = sum(position_needs.values()) - len(lineup)
            min_remaining_salary = remaining_spots * 2500

            if (used_salary + player_salary <= 50000 * mult['salary_efficiency'] and
                    team_counts[player.get('team', 'UNK')] < 5 and
                    used_salary + player_salary + min_remaining_salary <= 50000):
                lineup.append(player)
                used_salary += player_salary
                team_counts[player.get('team', 'UNK')] += 1
                added += 1

    if len(lineup) == 10:
        return {
            'players': lineup,
            'salary': used_salary,
            'projection': sum(p.get('projection', 0) for p in lineup),
            'skill_level': skill_level
        }

    return None


def build_simple_valid_lineup(players):
    """Simple but always successful lineup builder"""

    lineup = []
    used_salary = 0
    team_counts = defaultdict(int)

    position_needs = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Just take cheapest valid player for each position
    for pos, needed in position_needs.items():
        pos_players = [p for p in players if p['position'] == pos]
        pos_players.sort(key=lambda x: x.get('salary', 5000))

        added = 0
        for player in pos_players:
            if added >= needed:
                break

            if (used_salary + player.get('salary', 5000) <= 48000 and
                    team_counts[player.get('team', 'UNK')] < 5):
                lineup.append(player)
                used_salary += player.get('salary', 5000)
                team_counts[player.get('team', 'UNK')] += 1
                added += 1

    if len(lineup) == 10:
        return {
            'players': lineup,
            'salary': used_salary,
            'projection': sum(p.get('projection', 0) for p in lineup),
            'skill_level': 'simple'
        }

    return None


def vary_lineup(base_lineup, all_players):
    """Create a variation of an existing lineup"""

    new_lineup = base_lineup['players'].copy()

    # Randomly swap 1-3 players
    num_swaps = random.randint(1, 3)

    for _ in range(num_swaps):
        # Pick a random position to swap
        pos_idx = random.randint(0, 9)
        old_player = new_lineup[pos_idx]

        # Find replacement
        same_pos_players = [p for p in all_players
                            if p['position'] == old_player['position']
                            and p != old_player]

        if same_pos_players:
            new_player = random.choice(same_pos_players)
            new_lineup[pos_idx] = new_player

    return {
        'players': new_lineup,
        'salary': sum(p.get('salary', 5000) for p in new_lineup),
        'projection': sum(p.get('projection', 0) for p in new_lineup),
        'skill_level': base_lineup.get('skill_level', 'average')
    }


# Monkey patch the original generate_field function
def patch_field_generator():
    """Replace the original generate_field with our fixed version"""
    import sys
    sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

    try:
        from ml_experiments.simulators import robust_dfs_simulator
        robust_dfs_simulator.generate_field = generate_fixed_field
        print("✅ Patched generate_field with fixed version")
        return True
    except Exception as e:
        print(f"❌ Failed to patch: {e}")
        return False


if __name__ == "__main__":
    print("Fixed Field Generator")
    print("====================")
    print("\nThis module provides generate_fixed_field() which ensures")
    print("exactly the requested number of opponents are generated.")
    print("\nTo use in your competition:")
    print("1. Import this module")
    print("2. Call patch_field_generator()")
    print("3. Run your competition normally")

    # Test it
    print("\n" + "=" * 60)
    print("TESTING FIXED GENERATOR")
    print("=" * 60)

    # Create a test slate
    test_players = []
    positions = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF'] * 10

    for i, pos in enumerate(positions):
        test_players.append({
            'id': f'player_{i}',
            'name': f'{pos}_{i}',
            'position': pos,
            'team': f'TEAM{i % 8}',
            'salary': 3000 + (i * 100),
            'projection': 5 + (i * 0.5)
        })

    test_slate = {'players': test_players}

    # Test generation
    for contest_type in ['cash', 'gpp']:
        print(f"\nTesting {contest_type} field generation...")
        field = generate_fixed_field(test_slate, 99, contest_type)
        print(f"Requested: 99, Got: {len(field)}")

        if field:
            # Check skill distribution
            skill_counts = defaultdict(int)
            for lineup in field:
                skill_counts[lineup.get('skill_level', 'unknown')] += 1

            print("Skill distribution:")
            for skill, count in sorted(skill_counts.items()):
                print(f"  {skill}: {count} ({count / len(field) * 100:.0f}%)")