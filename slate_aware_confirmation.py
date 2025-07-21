#!/usr/bin/env python3
"""
SLATE-AWARE CONFIRMATION SYSTEM
===============================
Uses CSV data to identify which games are in the slate
Only fetches confirmations for THOSE games
"""

import re
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple
import requests
from bs4 import BeautifulSoup


class SlateAwareConfirmationSystem:
    """
    Smart confirmation system that uses CSV data to identify slate games
    """

    def __init__(self, csv_path: str = None, csv_df: pd.DataFrame = None, verbose: bool = True):
        self.verbose = verbose
        self.slate_games = {}
        self.slate_teams = set()
        self.confirmed_lineups = {}
        self.confirmed_pitchers = {}

        # Load slate info from CSV
        if csv_path:
            self.df = pd.read_csv(csv_path)
        elif csv_df is not None:
            self.df = csv_df
        else:
            raise ValueError("Must provide either csv_path or csv_df")

        # Parse slate games from CSV
        self._parse_slate_games()

    def _parse_slate_games(self):
        """Parse Game Info column to identify slate games"""
        if self.verbose:
            print("\n📋 PARSING SLATE GAMES FROM CSV")
            print("=" * 60)

        if 'Game Info' not in self.df.columns:
            print("❌ No 'Game Info' column found!")
            return

        # Get unique games
        unique_games = self.df['Game Info'].dropna().unique()

        for game_info in unique_games:
            # Parse game info (format: "TEA@TEB 07:10PM ET")
            match = re.match(r'(\w+)@(\w+)\s+(\d{2}:\d{2}[AP]M)\s+ET', str(game_info))

            if match:
                away_team = match.group(1)
                home_team = match.group(2)
                game_time = match.group(3)

                # Store game info
                game_key = f"{away_team}@{home_team}"
                self.slate_games[game_key] = {
                    'away': away_team,
                    'home': home_team,
                    'time': game_time,
                    'game_info': game_info
                }

                # Add teams to set
                self.slate_teams.add(away_team)
                self.slate_teams.add(home_team)

        if self.verbose:
            print(f"✅ Found {len(self.slate_games)} games in slate")
            print(f"✅ Teams in slate: {sorted(self.slate_teams)}")

            # Show game times
            print("\n⏰ Slate game times:")
            for game, info in self.slate_games.items():
                print(f"   {game} at {info['time']}")

    def fetch_confirmations(self) -> Tuple[int, int]:
        """
        Fetch confirmations ONLY for slate games

        Returns:
            (lineup_count, pitcher_count)
        """
        if self.verbose:
            print("\n🎯 FETCHING CONFIRMATIONS FOR SLATE GAMES ONLY")
            print("=" * 60)

        # Try MLB API first
        lineup_count, pitcher_count = self._fetch_mlb_confirmations()

        # If no pitchers, try Rotowire
        if pitcher_count == 0:
            if self.verbose:
                print("\n📰 MLB had no pitchers, trying Rotowire...")
            pitcher_count = self._fetch_rotowire_pitchers()

        return lineup_count, pitcher_count

    def _fetch_mlb_confirmations(self) -> Tuple[int, int]:
        """Fetch from MLB API, filtered by slate teams"""
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=lineups,probablePitcher"

        lineup_count = 0
        pitcher_count = 0

        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return 0, 0

            data = response.json()
            dates = data.get('dates', [])

            if not dates:
                return 0, 0

            games = dates[0].get('games', [])

            for game in games:
                # Get team abbreviations
                teams = game.get('teams', {})
                away_team_data = teams.get('away', {}).get('team', {})
                home_team_data = teams.get('home', {}).get('team', {})

                away_abbr = away_team_data.get('abbreviation', '')
                home_abbr = home_team_data.get('abbreviation', '')

                # CHECK IF THIS GAME IS IN OUR SLATE
                if away_abbr not in self.slate_teams or home_abbr not in self.slate_teams:
                    continue

                game_key = f"{away_abbr}@{home_abbr}"
                if game_key not in self.slate_games:
                    continue

                # This is a slate game! Check if it's started
                status = game.get('status', {})
                detailed_state = status.get('detailedState', '')

                if detailed_state in ['Final', 'Game Over']:
                    if self.verbose:
                        print(f"   ⚠️  {game_key} already finished")
                    continue

                if self.verbose:
                    print(f"\n   ✅ Found slate game: {game_key}")
                    print(f"      Status: {detailed_state}")

                # Get lineups
                lineups = game.get('lineups', {})

                # Away lineup
                away_players = lineups.get('awayPlayers', [])
                if away_players:
                    self.confirmed_lineups[away_abbr] = []
                    for player in away_players:
                        player_data = {
                            'name': player.get('fullName', ''),
                            'position': player.get('primaryPosition', {}).get('abbreviation', ''),
                            'order': player.get('battingOrder', 0)
                        }
                        self.confirmed_lineups[away_abbr].append(player_data)
                        lineup_count += 1

                # Home lineup
                home_players = lineups.get('homePlayers', [])
                if home_players:
                    self.confirmed_lineups[home_abbr] = []
                    for player in home_players:
                        player_data = {
                            'name': player.get('fullName', ''),
                            'position': player.get('primaryPosition', {}).get('abbreviation', ''),
                            'order': player.get('battingOrder', 0)
                        }
                        self.confirmed_lineups[home_abbr].append(player_data)
                        lineup_count += 1

                # Probable pitchers
                away_pitcher = teams.get('away', {}).get('probablePitcher', {})
                if away_pitcher:
                    self.confirmed_pitchers[away_abbr] = {
                        'name': away_pitcher.get('fullName', ''),
                        'team': away_abbr,
                        'source': 'mlb_api'
                    }
                    pitcher_count += 1

                home_pitcher = teams.get('home', {}).get('probablePitcher', {})
                if home_pitcher:
                    self.confirmed_pitchers[home_abbr] = {
                        'name': home_pitcher.get('fullName', ''),
                        'team': home_abbr,
                        'source': 'mlb_api'
                    }
                    pitcher_count += 1

        except Exception as e:
            if self.verbose:
                print(f"❌ MLB API error: {e}")

        if self.verbose:
            print(f"\n📊 MLB API Results:")
            print(f"   Lineups: {lineup_count} players")
            print(f"   Pitchers: {pitcher_count}")

        return lineup_count, pitcher_count

    def _fetch_rotowire_pitchers(self) -> int:
        """Fetch pitchers from Rotowire, filtered by slate teams"""
        # Similar to regular Rotowire but filters by slate teams
        # ... implementation ...
        return 0

    def get_all_confirmations(self) -> Tuple[Dict, Dict]:
        """Get all confirmed lineups and pitchers"""
        self.fetch_confirmations()
        return self.confirmed_lineups, self.confirmed_pitchers

    def is_player_in_slate(self, player_name: str, team: str) -> bool:
        """Check if a player's team is in the slate"""
        return team in self.slate_teams


# Integration with existing system
class EnhancedSlateAwareSystem:
    """
    Drop-in replacement for existing confirmation system
    Automatically uses slate information from CSV
    """

    def __init__(self, csv_players: List = None, csv_df: pd.DataFrame = None, verbose: bool = True):
        self.verbose = verbose
        self.csv_players = csv_players

        # Create slate-aware system
        if csv_df is not None:
            self.slate_system = SlateAwareConfirmationSystem(csv_df=csv_df, verbose=verbose)
        else:
            # Try to extract DataFrame from players
            if csv_players and hasattr(csv_players[0], '__dict__'):
                # Convert to DataFrame
                data = []
                for p in csv_players:
                    data.append({
                        'Name': getattr(p, 'name', ''),
                        'Team': getattr(p, 'team', ''),
                        'Game Info': getattr(p, 'game_info', '')
                    })
                df = pd.DataFrame(data)
                self.slate_system = SlateAwareConfirmationSystem(csv_df=df, verbose=verbose)
            else:
                raise ValueError("Need CSV data to identify slate")

        # Compatibility attributes
        self.confirmed_lineups = {}
        self.confirmed_pitchers = {}

    def get_all_confirmations(self) -> Tuple[int, int]:
        """Main method - compatible with existing system"""
        lineups, pitchers = self.slate_system.get_all_confirmations()

        self.confirmed_lineups = lineups
        self.confirmed_pitchers = pitchers

        lineup_count = sum(len(lineup) for lineup in lineups.values())
        pitcher_count = len(pitchers)

        return lineup_count, pitcher_count

    def fetch_all_confirmations(self) -> Tuple[Dict, Dict]:
        """Alternative method name for compatibility"""
        return self.slate_system.get_all_confirmations()


if __name__ == "__main__":
    print("🚀 SLATE-AWARE CONFIRMATION SYSTEM TEST")
    print("=" * 70)

    # Test with a CSV
    from pathlib import Path

    csv_files = list(Path('.').glob('*.csv'))

    if csv_files:
        csv_path = str(csv_files[0])
        print(f"\nTesting with: {csv_path}")

        # Create slate-aware system
        system = SlateAwareConfirmationSystem(csv_path=csv_path)

        # Fetch confirmations
        lineup_count, pitcher_count = system.fetch_confirmations()

        print(f"\n✅ Final results:")
        print(f"   Lineups: {lineup_count} players")
        print(f"   Pitchers: {pitcher_count}")

        # Show confirmed teams
        if system.confirmed_lineups:
            print(f"\n📋 Confirmed lineups for teams: {list(system.confirmed_lineups.keys())}")
        if system.confirmed_pitchers:
            print(f"⚾ Confirmed pitchers for teams: {list(system.confirmed_pitchers.keys())}")