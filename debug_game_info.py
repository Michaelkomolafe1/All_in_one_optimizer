#!/usr/bin/env python3
"""
TEST UNIVERSAL CONFIRMATION SYSTEM
==================================
Test the new universal system with various scenarios
"""

from smart_confirmation_system import UniversalSmartConfirmation


def test_with_your_csv():
    """Test with your specific CSV teams"""
    print("🧪 TEST 1: With Your CSV Teams")
    print("=" * 60)

    # Simulate your CSV
    mock_players = []
    your_teams = ['ATH', 'CHC', 'COL', 'KC', 'STL', 'TEX']

    for team in your_teams:
        mock_players.append({'team': team, 'name': f'Player {team}'})

    system = UniversalSmartConfirmation(csv_players=mock_players, verbose=True)
    lineup_count, pitcher_count = system.get_all_confirmations()

    print(f"\n📊 Results with your teams:")
    print(f"   Players: {lineup_count}")
    print(f"   Pitchers: {pitcher_count}")

    # Show which teams got lineups
    for team in sorted(your_teams):
        if team in system.confirmed_lineups:
            print(f"   ✅ {team}: {len(system.confirmed_lineups[team])} players")
        elif 'OAK' in system.confirmed_lineups and team == 'ATH':
            print(f"   ✅ {team} (as OAK): {len(system.confirmed_lineups['OAK'])} players")


def test_universal_mode():
    """Test without CSV restrictions"""
    print("\n\n🧪 TEST 2: Universal Mode (All Teams)")
    print("=" * 60)

    system = UniversalSmartConfirmation(verbose=False)  # Less verbose
    lineup_count, pitcher_count = system.get_all_confirmations()

    print(f"\n📊 Results for ALL teams:")
    print(f"   Total players: {lineup_count}")
    print(f"   Total pitchers: {pitcher_count}")
    print(f"   Teams with lineups: {len(system.confirmed_lineups)}")

    # Show all teams
    teams = sorted(system.confirmed_lineups.keys())
    print(f"\n   All teams: {', '.join(teams)}")


def test_team_variations():
    """Test team variation handling"""
    print("\n\n🧪 TEST 3: Team Variations")
    print("=" * 60)

    # Test with problematic teams
    problem_teams = ['ATH', 'CWS', 'WAS']
    mock_players = [{'team': team, 'name': f'Player {team}'} for team in problem_teams]

    system = UniversalSmartConfirmation(csv_players=mock_players, verbose=False)

    print("Testing team variations:")
    print(f"Input teams: {problem_teams}")
    print(f"Expanded teams: {sorted(system.csv_teams)}")

    lineup_count, pitcher_count = system.get_all_confirmations()

    print(f"\n📊 Results:")
    for team in sorted(system.confirmed_lineups.keys()):
        print(f"   {team}: {len(system.confirmed_lineups[team])} players")


if __name__ == "__main__":
    # Run all tests
    test_with_your_csv()
    test_universal_mode()
    test_team_variations()

    print("\n\n✅ UNIVERSAL SYSTEM TEST COMPLETE")
    print("=" * 60)
    print("The system should now work with ANY CSV file!")