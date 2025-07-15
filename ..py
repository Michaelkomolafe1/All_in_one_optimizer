#!/usr/bin/env python3
"""
Create DKSalaries5.csv for testing
==================================
This creates a CSV file with the structure you showed me
"""

import pandas as pd
import random


def create_dk_salaries_csv():
    """Create a sample DraftKings CSV file"""

    # Sample data based on your CSV structure
    teams = ['NYY', 'BOS', 'TB', 'TOR', 'BAL', 'LAD', 'SD', 'SF', 'ARI', 'COL']
    positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']

    # Sample player data
    data = []
    player_id = 15000

    # Add some pitchers
    pitchers = [
        ("Gerrit Cole", "NYY", 9800, 8.5),
        ("Shane Bieber", "CLE", 9500, 8.2),
        ("Jacob deGrom", "TEX", 9200, 8.0),
        ("Corbin Burnes", "BAL", 8900, 7.8),
        ("Tyler Glasnow", "LAD", 8600, 7.5),
        ("Logan Webb", "SF", 8300, 7.2),
        ("Zack Wheeler", "PHI", 8000, 6.9),
        ("Framber Valdez", "HOU", 7700, 6.6),
    ]

    for name, team, salary, proj in pitchers:
        data.append({
            'Position': 'P',
            'Name + ID': f'{name} ({player_id})',
            'Name': name,
            'ID': player_id,
            'Roster Position': 'P',
            'Salary': salary,
            'Game Info': f'{team}@OPP 07:05PM ET',
            'TeamAbbrev': team,
            'AvgPointsPerGame': proj
        })
        player_id += 1

    # Add position players
    position_players = [
        # Catchers
        ("J.T. Realmuto", "PHI", "C", 5200, 9.2),
        ("Will Smith", "LAD", "C", 5000, 8.8),
        ("Salvador Perez", "KC", "C", 4800, 8.5),

        # First basemen
        ("Freddie Freeman", "LAD", "1B", 5900, 10.5),
        ("Matt Olson", "ATL", "1B", 5700, 10.2),
        ("Vladimir Guerrero Jr.", "TOR", "1B", 5600, 10.0),

        # Second basemen
        ("Marcus Semien", "TEX", "2B", 5500, 9.8),
        ("Jose Altuve", "HOU", "2B", 5300, 9.5),
        ("Gleyber Torres", "NYY", "2B", 4900, 8.9),

        # Third basemen
        ("Rafael Devers", "BOS", "3B", 5700, 10.3),
        ("Manny Machado", "SD", "3B", 5600, 10.1),
        ("Jose Ramirez", "CLE", "3B", 5800, 10.8),

        # Shortstops
        ("Trea Turner", "PHI", "SS", 5800, 10.4),
        ("Corey Seager", "TEX", "SS", 5900, 10.6),
        ("Francisco Lindor", "NYM", "SS", 5700, 10.2),

        # Outfielders
        ("Ronald Acuna Jr.", "ATL", "OF", 6500, 12.5),
        ("Mookie Betts", "LAD", "OF", 6300, 11.8),
        ("Aaron Judge", "NYY", "OF", 6400, 12.2),
        ("Juan Soto", "NYY", "OF", 6200, 11.5),
        ("Mike Trout", "LAA", "OF", 6000, 11.0),
        ("Yordan Alvarez", "HOU", "OF", 5900, 10.8),
        ("Kyle Tucker", "HOU", "OF", 5700, 10.4),
        ("Randy Arozarena", "TB", "OF", 5200, 9.5),
        ("George Springer", "TOR", "OF", 5100, 9.2),
        ("Julio Rodriguez", "SEA", "OF", 5500, 10.0),
    ]

    for name, team, pos, salary, proj in position_players:
        # Determine opponent
        opp_team = random.choice([t for t in teams if t != team])

        # Create game info
        if random.random() > 0.5:
            game_info = f'{team}@{opp_team} 07:05PM ET'
        else:
            game_info = f'{opp_team}@{team} 07:05PM ET'

        data.append({
            'Position': pos,
            'Name + ID': f'{name} ({player_id})',
            'Name': name,
            'ID': player_id,
            'Roster Position': pos,
            'Salary': salary,
            'Game Info': game_info,
            'TeamAbbrev': team,
            'AvgPointsPerGame': proj
        })
        player_id += 1

    # Add some multi-position players
    multi_position = [
        ("Jazz Chisholm Jr.", "MIA", "2B/OF", 5000, 9.1),
        ("Cody Bellinger", "CHC", "1B/OF", 4900, 8.8),
        ("Mookie Betts", "LAD", "2B/SS/OF", 6300, 11.8),  # Duplicate with multiple positions
    ]

    for name, team, positions, salary, proj in multi_position:
        opp_team = random.choice([t for t in teams if t != team])
        game_info = f'{team}@{opp_team} 07:05PM ET'

        data.append({
            'Position': positions.split('/')[0],  # Primary position
            'Name + ID': f'{name} ({player_id})',
            'Name': name,
            'ID': player_id,
            'Roster Position': positions,  # All positions
            'Salary': salary,
            'Game Info': game_info,
            'TeamAbbrev': team,
            'AvgPointsPerGame': proj
        })
        player_id += 1

    # Create DataFrame and save
    df = pd.DataFrame(data)

    # Save to CSV
    df.to_csv('DKSalaries5.csv', index=False)
    print(f"✅ Created DKSalaries5.csv with {len(df)} players")

    # Show summary
    print("\nSummary:")
    print(f"  Total players: {len(df)}")
    print(f"  Salary range: ${df['Salary'].min():,} - ${df['Salary'].max():,}")
    print(f"  Avg projection: {df['AvgPointsPerGame'].mean():.1f}")
    print("\nPositions:")
    for pos, count in df['Position'].value_counts().items():
        print(f"  {pos}: {count}")

    return df


if __name__ == "__main__":
    create_dk_salaries_csv()

    # Also create a simpler test file
    print("\n" + "=" * 50)
    print("Creating test_players.csv as well...")

    # Create simple test data
    simple_data = []
    for i in range(50):
        pos = random.choice(['P', 'C', '1B', '2B', '3B', 'SS', 'OF'])
        team = random.choice(['NYY', 'BOS', 'LAD', 'HOU'])
        salary = random.randint(3000, 10000)
        proj = random.uniform(5.0, 12.0)

        simple_data.append({
            'Position': pos,
            'Name + ID': f'Player {i} ({15000 + i})',
            'Name': f'Player {i}',
            'ID': 15000 + i,
            'Roster Position': pos,
            'Salary': salary,
            'Game Info': f'{team}@OPP 07:05PM ET',
            'TeamAbbrev': team,
            'AvgPointsPerGame': round(proj, 1)
        })

    simple_df = pd.DataFrame(simple_data)
    simple_df.to_csv('test_players_new.csv', index=False)
    print(f"✅ Created test_players_new.csv with {len(simple_df)} players")