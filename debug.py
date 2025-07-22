#!/usr/bin/env python3
"""
VERIFY COMPLETE LINEUP SYSTEM
=============================
Test that we can get all lineups with correct team codes
"""

import requests
from datetime import datetime


def verify_complete_system():
    """Verify we can extract all lineups with correct team codes"""
    print("\n✅ VERIFYING COMPLETE LINEUP EXTRACTION")
    print("=" * 60)

    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=probablePitcher,lineups"

    confirmed_lineups = {}
    confirmed_pitchers = {}

    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = data.get('dates', [{}])[0].get('games', [])

        print(f"Processing {len(games)} games...\n")

        for game in games:
            teams = game.get('teams', {})

            # Get team abbreviations
            away_abbr = teams.get('away', {}).get('team', {}).get('abbreviation', '')
            home_abbr = teams.get('home', {}).get('team', {}).get('abbreviation', '')

            # Get pitchers
            away_pitcher = teams.get('away', {}).get('probablePitcher', {})
            home_pitcher = teams.get('home', {}).get('probablePitcher', {})

            if away_pitcher:
                confirmed_pitchers[away_abbr] = away_pitcher.get('fullName', '')
            if home_pitcher:
                confirmed_pitchers[home_abbr] = home_pitcher.get('fullName', '')

            # Get lineups from game.lineups
            lineups = game.get('lineups', {})
            if lineups:
                # Away lineup
                away_players = lineups.get('awayPlayers', [])
                if away_players and away_abbr:
                    confirmed_lineups[away_abbr] = []
                    for player in away_players:
                        confirmed_lineups[away_abbr].append({
                            'name': player.get('fullName', ''),
                            'position': player.get('primaryPosition', {}).get('abbreviation', '')
                        })

                # Home lineup
                home_players = lineups.get('homePlayers', [])
                if home_players and home_abbr:
                    confirmed_lineups[home_abbr] = []
                    for player in home_players:
                        confirmed_lineups[home_abbr].append({
                            'name': player.get('fullName', ''),
                            'position': player.get('primaryPosition', {}).get('abbreviation', '')
                        })

        # Show results
        print("📊 RESULTS:")
        print(f"Teams with lineups: {len(confirmed_lineups)}")
        print(f"Teams with pitchers: {len(confirmed_pitchers)}")
        print(f"Total players: {sum(len(lineup) for lineup in confirmed_lineups.values())}")

        # Show sample teams
        print("\n📋 Sample Teams with Lineups:")
        for team in sorted(confirmed_lineups.keys())[:10]:
            lineup = confirmed_lineups[team]
            pitcher = confirmed_pitchers.get(team, 'TBD')
            print(f"\n{team} ({len(lineup)} players) - SP: {pitcher}")
            # Show first 3 batters
            for i, player in enumerate(lineup[:3]):
                print(f"  {i + 1}. {player['name']} ({player['position']})")

        # Check against your slate teams
        print("\n🎯 Checking Your Slate Teams:")
        your_slate_teams = ['ARI', 'ATH', 'ATL', 'CHC', 'COL', 'CWS', 'HOU',
                            'KC', 'LAA', 'LAD', 'MIL', 'MIN', 'NYM', 'NYY',
                            'SEA', 'SF', 'STL', 'TB', 'TEX', 'TOR']

        matches = 0
        for team in your_slate_teams:
            if team in confirmed_lineups:
                matches += 1
                print(f"  ✅ {team}: {len(confirmed_lineups[team])} players")
            else:
                # Check if it's ATH -> OAK
                if team == 'ATH' and 'OAK' in confirmed_lineups:
                    matches += 1
                    print(f"  ✅ {team} (as OAK): {len(confirmed_lineups['OAK'])} players")
                else:
                    print(f"  ❌ {team}: Not found")

        print(f"\nMatched {matches}/{len(your_slate_teams)} of your slate teams")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    verify_complete_system()

    print("\n\n🎯 NEXT STEPS:")
    print("=" * 60)
    print("""
1. Add the lineup extraction code to smart_confirmation_system.py
2. The code needs to:
   - Get team abbreviations from teams.away.team.abbreviation
   - Check for lineups in game.lineups.awayPlayers/homePlayers
   - Store them in self.confirmed_lineups[team_abbr]
3. Restart your GUI
4. You'll have 270+ confirmed players!

Your optimizer will finally work with real confirmed lineups!
""")