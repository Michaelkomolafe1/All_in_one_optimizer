#!/usr/bin/env python3
"""
SMART CONFIRMATION SYSTEM
========================
Unified system for lineup and pitcher confirmations
Uses data integration system for consistent team/name mapping
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests

from unified_data_system import UnifiedDataSystem

logger = logging.getLogger(__name__)

class SmartConfirmationSystem:
    """Unified confirmation system with smart filtering"""

    def __init__(self, csv_players: List = None, verbose: bool = False):
        self.verbose = verbose
        self.csv_players = csv_players or []
        self.data_system = UnifiedDataSystem()
        self.confirmed_lineups = {}
        self.confirmed_pitchers = {}

        # Add the cache attributes here
        self._lineup_cache = {}
        self._cache_timestamp = None

        # Extract teams from CSV for smart filtering
        self.csv_teams = self.data_system.get_teams_from_players(csv_players) if csv_players else set()

        if self.verbose and self.csv_teams:
            print(f"📊 CSV teams detected: {sorted(self.csv_teams)}")


    def get_mlb_lineups(self, date):
        """Get MLB lineups with caching"""
        from datetime import datetime, timedelta

        # Check if we have cached data less than 2 hours old
        if (self._cache_timestamp and
                self._lineup_cache and
                datetime.now() - self._cache_timestamp < timedelta(hours=2)):
            print("📋 Using cached MLB lineups")
            return self._lineup_cache

        # Otherwise fetch fresh data
        print("🌐 Fetching fresh MLB lineups")
        lineups = self._fetch_mlb_lineups_original(date)  # Call original method

        # Cache it
        self._lineup_cache = lineups
        self._cache_timestamp = datetime.now()

        return lineups

    def get_all_confirmations(self) -> Tuple[int, int]:
        """Get confirmations from MLB API ONLY - NO FALLBACK"""
        print("🔍 SMART CONFIRMATION SYSTEM - NO FALLBACK MODE")
        print("=" * 50)

        # Try MLB Stats API - NO FALLBACK
        self._fetch_mlb_confirmations()

        # Filter to only CSV teams
        self._filter_to_csv_teams()

        lineup_count = sum(len(lineup) for lineup in self.confirmed_lineups.values())
        pitcher_count = len(self.confirmed_pitchers)

        if lineup_count == 0:
            print("\n❌ NO LINEUPS FOUND FROM MLB API")
            print("This could mean:")
            print("1. Games haven't started posting lineups yet")
            print("2. Your CSV teams aren't playing today")
            print("3. API format has changed")
            print("\nNO FALLBACK - Using only confirmed players")
        else:
            print(f"✅ Found {lineup_count} real lineup spots, {pitcher_count} real pitchers")

        return lineup_count, pitcher_count

    # In smart_confirmation_system.py, replace the _fetch_mlb_confirmations method:

    def _fetch_mlb_confirmations(self) -> Dict:
        """Fetch confirmations from MLB Stats API - NO FALLBACK"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=lineups,probablePitcher,team"

            print(f"🌐 Fetching real lineups from MLB API...")
            print(f"📅 Date: {today}")

            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"⚠️ MLB API returned status {response.status_code}")
                return {}

            data = response.json()
            confirmations = {'lineups': {}, 'pitchers': {}}
            games_processed = 0

            # Debug: save raw response
            with open('mlb_api_response.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("💾 Saved raw API response to mlb_api_response.json")

            for date_data in data.get('dates', []):
                for game in date_data.get('games', []):
                    games_processed += 1
                    game_pk = game.get('gamePk')

                    # Get detailed game data with lineups
                    lineup_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"

                    try:
                        lineup_response = requests.get(lineup_url, timeout=10)
                        if lineup_response.status_code == 200:
                            game_data = lineup_response.json()

                            # Extract lineups from live data
                            lineups_data = game_data.get('liveData', {}).get('boxscore', {}).get('teams', {})

                            # Away team
                            away_data = lineups_data.get('away', {})
                            away_team = game_data.get('gameData', {}).get('teams', {}).get('away', {}).get(
                                'abbreviation', '')

                            if away_team and 'players' in away_data:
                                away_lineup = []
                                for player_id, player_info in away_data['players'].items():
                                    if player_info.get('battingOrder') and int(player_info['battingOrder']) > 0:
                                        away_lineup.append({
                                            'name': player_info.get('person', {}).get('fullName', ''),
                                            'position': player_info.get('position', {}).get('abbreviation', ''),
                                            'order': int(player_info['battingOrder']) // 100,
                                            # Convert 100, 200 to 1, 2
                                            'team': away_team
                                        })

                                if away_lineup:
                                    confirmations['lineups'][away_team] = sorted(away_lineup, key=lambda x: x['order'])
                                    print(f"✅ Found {away_team} lineup: {len(away_lineup)} players")

                            # Home team
                            home_data = lineups_data.get('home', {})
                            home_team = game_data.get('gameData', {}).get('teams', {}).get('home', {}).get(
                                'abbreviation', '')

                            if home_team and 'players' in home_data:
                                home_lineup = []
                                for player_id, player_info in home_data['players'].items():
                                    if player_info.get('battingOrder') and int(player_info['battingOrder']) > 0:
                                        home_lineup.append({
                                            'name': player_info.get('person', {}).get('fullName', ''),
                                            'position': player_info.get('position', {}).get('abbreviation', ''),
                                            'order': int(player_info['battingOrder']) // 100,
                                            'team': home_team
                                        })

                                if home_lineup:
                                    confirmations['lineups'][home_team] = sorted(home_lineup, key=lambda x: x['order'])
                                    print(f"✅ Found {home_team} lineup: {len(home_lineup)} players")

                            # Get probable pitchers
                            pitchers_data = game_data.get('gameData', {}).get('probablePitchers', {})

                            if 'away' in pitchers_data and away_team:
                                confirmations['pitchers'][away_team] = {
                                    'name': pitchers_data['away'].get('fullName', ''),
                                    'team': away_team,
                                    'source': 'mlb_live'
                                }
                                print(f"✅ Found {away_team} pitcher: {pitchers_data['away'].get('fullName', '')}")

                            if 'home' in pitchers_data and home_team:
                                confirmations['pitchers'][home_team] = {
                                    'name': pitchers_data['home'].get('fullName', ''),
                                    'team': home_team,
                                    'source': 'mlb_live'
                                }
                                print(f"✅ Found {home_team} pitcher: {pitchers_data['home'].get('fullName', '')}")

                    except Exception as e:
                        print(f"⚠️ Error fetching lineup for game {game_pk}: {e}")

            print(f"📊 Processed {games_processed} games from MLB API")
            print(f"📋 Found lineups for: {list(confirmations['lineups'].keys())}")
            print(f"⚾ Found pitchers for: {list(confirmations['pitchers'].keys())}")

            # Apply confirmations ONLY if we have them
            for team, lineup in confirmations['lineups'].items():
                team_abbrev = self.data_system.normalize_team(team)
                if team_abbrev in self.csv_teams:
                    self.confirmed_lineups[team_abbrev] = lineup

            for team, pitcher in confirmations['pitchers'].items():
                team_abbrev = self.data_system.normalize_team(team)
                if team_abbrev in self.csv_teams:
                    self.confirmed_pitchers[team_abbrev] = pitcher

            return confirmations

        except Exception as e:
            print(f"⚠️ MLB API error: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _enhanced_csv_analysis(self) -> Dict:
        """Enhanced analysis of CSV data for confirmations"""
        if not self.csv_players:
            return {}

        print("🧠 Running enhanced CSV analysis...")

        # Group by team
        team_players = {}
        for player in self.csv_players:
            team = self.data_system.normalize_team(player.team if hasattr(player, 'team') else player.get('team', ''))
            if team not in team_players:
                team_players[team] = {'pitchers': [], 'hitters': []}

            if hasattr(player, 'primary_position'):
                position = player.primary_position
                salary = player.salary
                name = player.name
            else:
                position = player.get('position', '')
                salary = player.get('salary', 0)
                name = player.get('name', '')

            if position == 'P':
                team_players[team]['pitchers'].append({
                    'name': name,
                    'salary': salary,
                    'player': player
                })
            else:
                team_players[team]['hitters'].append({
                    'name': name,
                    'salary': salary,
                    'position': position,
                    'player': player
                })

        confirmations = {'lineups': {}, 'pitchers': {}}

        # Smart pitcher detection
        for team, players in team_players.items():
            if players['pitchers']:
                # Sort by salary
                players['pitchers'].sort(key=lambda x: x['salary'], reverse=True)

                # Take highest salary pitcher
                top_pitcher = players['pitchers'][0]
                confirmations['pitchers'][team] = {
                    'name': top_pitcher['name'],
                    'team': team,
                    'source': 'csv_analysis',
                    'confidence': 0.8
                }

        # Smart lineup detection
        for team, players in team_players.items():
            if len(players['hitters']) >= 8:
                # Sort by salary
                players['hitters'].sort(key=lambda x: x['salary'], reverse=True)

                # Take top 9 by salary
                lineup = []
                for i, hitter in enumerate(players['hitters'][:9]):
                    lineup.append({
                        'name': hitter['name'],
                        'position': hitter['position'],
                        'order': i + 1,
                        'team': team,
                        'source': 'csv_analysis'
                    })

                confirmations['lineups'][team] = lineup

        return confirmations

    def _merge_confirmations(self, new_data: Dict) -> None:
        """Merge new confirmations with existing"""
        for team, lineup in new_data.get('lineups', {}).items():
            team_abbrev = self.data_system.normalize_team(team)
            if team_abbrev in self.csv_teams and team_abbrev not in self.confirmed_lineups:
                self.confirmed_lineups[team_abbrev] = lineup

        for team, pitcher in new_data.get('pitchers', {}).items():
            team_abbrev = self.data_system.normalize_team(team)
            if team_abbrev in self.csv_teams and team_abbrev not in self.confirmed_pitchers:
                self.confirmed_pitchers[team_abbrev] = pitcher

    def _filter_to_csv_teams(self) -> None:
        """Filter confirmations to only CSV teams"""
        print(f"\n🔍 FILTERING DEBUG:")
        print(f"CSV teams: {self.csv_teams}")
        print(f"Lineup teams before filter: {list(self.confirmed_lineups.keys())}")

        # Remove any teams not in CSV
        self.confirmed_lineups = {
            team: lineup for team, lineup in self.confirmed_lineups.items()
            if team in self.csv_teams
        }
        self.confirmed_pitchers = {
            team: pitcher for team, pitcher in self.confirmed_pitchers.items()
            if team in self.csv_teams
        }

        print(f"Lineup teams after filter: {list(self.confirmed_lineups.keys())}")

    def _needs_more_confirmations(self) -> bool:
        """Check if we need more confirmations"""
        lineup_count = len(self.confirmed_lineups)
        pitcher_count = len(self.confirmed_pitchers)

        # Need at least 50% of CSV teams confirmed
        return lineup_count < len(self.csv_teams) * 0.5 or pitcher_count < len(self.csv_teams) * 0.5

    def _process_game_data(self, game: Dict, confirmations: Dict) -> None:
        """Process game data from MLB API"""
        # Implementation similar to your existing code but using
        # the unified data system for team/name normalization

    def is_player_confirmed(self, player_name: str, team: str = None) -> Tuple[bool, Optional[int]]:
        """Check if player is confirmed in actual lineup - FIXED VERSION"""
        try:
            if not team:
                return False, None

            team = self.data_system.normalize_team(team)
            if team not in self.confirmed_lineups:
                return False, None

            # Get the lineup for this team
            lineup = self.confirmed_lineups.get(team, [])
            if not lineup:
                return False, None

            # Use simple string comparison first
            player_name_lower = player_name.lower().strip()

            for lineup_player in lineup:
                lineup_name = lineup_player.get('name', '').lower().strip()

                # Exact match first (fastest)
                if player_name_lower == lineup_name:
                    return True, lineup_player.get('order', 1)

                # Only do complex matching if names are different
                if player_name_lower != lineup_name:
                    # Use simple contains check before complex matching
                    if player_name_lower in lineup_name or lineup_name in player_name_lower:
                        return True, lineup_player.get('order', 1)

            # If no simple matches, try the complex matcher
            for lineup_player in lineup:
                try:
                    if self.data_system.match_player_names(player_name, lineup_player.get('name', '')):
                        return True, lineup_player.get('order', 1)
                except Exception:
                    # Skip this player if matching fails
                    continue

        except Exception as e:
            print(f"❌ Error in is_player_confirmed for {player_name}: {e}")

        return False, None

    def is_player_confirmed(self, player_name: str, team: str = None) -> Tuple[bool, Optional[int]]:
        """Check if player is confirmed in actual lineup"""
        if team:
            team = self.data_system.normalize_team(team)
            if team in self.confirmed_lineups:
                for lineup_player in self.confirmed_lineups[team]:
                    # Debug output
                    if self.verbose:
                        print(f"   Checking {player_name} vs {lineup_player['name']}")

                    # Use the unified data system's name matching
                    if self.data_system.match_player_names(player_name, lineup_player['name']):
                        if self.verbose:
                            print(f"✅ Matched {player_name} to {lineup_player['name']} in {team} lineup")
                        return True, lineup_player.get('order', 1)
            elif self.verbose:
                print(f"   Team {team} not in confirmed lineups: {list(self.confirmed_lineups.keys())}")

        return False, None

    def is_pitcher_confirmed(self, pitcher_name: str, team: str = None) -> bool:
        """Check if pitcher is confirmed starter"""
        if team:
            team = self.data_system.normalize_team(team)
            if team in self.confirmed_pitchers:
                confirmed_pitcher = self.confirmed_pitchers[team]
                if self.data_system.match_player_names(pitcher_name, confirmed_pitcher['name']):
                    if self.verbose:
                        print(f"✅ Matched pitcher {pitcher_name} to {confirmed_pitcher['name']}")
                    return True

        return False