#!/usr/bin/env python3
"""
FIXED SMART CONFIRMATION SYSTEM
================================
Fixes variable scope issues and improves error handling
"""

import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from copy import deepcopy
import threading

logger = logging.getLogger(__name__)


class UniversalSmartConfirmation:
    """Fixed confirmation system with proper error handling"""

    TEAM_VARIATIONS = {
        'ATH': ['OAK', 'ATH'],
        'OAK': ['OAK', 'ATH'],
        'CHW': ['CWS', 'CHW'],
        'CWS': ['CWS', 'CHW'],
        'WSH': ['WAS', 'WSH'],
        'WAS': ['WAS', 'WSH'],
    }

    def __init__(self, csv_players: List = None, verbose: bool = True):
        self.csv_players = deepcopy(csv_players) if csv_players else []
        self.verbose = verbose
        self.confirmed_lineups = {}
        self.confirmed_pitchers = {}
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._lock = threading.Lock()
        self.csv_teams = self._build_team_set()

        if self.verbose:
            print(f"🎯 Universal Smart Confirmation System initialized")
            print(f"📋 Tracking teams: {sorted(self.csv_teams)}")

    def _build_team_set(self) -> Set[str]:
        """Build comprehensive team set"""
        teams = set()

        for player in self.csv_players:
            team = None
            if hasattr(player, 'team'):
                team = player.team
            elif isinstance(player, dict):
                team = player.get('team') or player.get('TeamAbbrev')

            if team:
                team = team.upper().strip()
                teams.add(team)
                teams.update(self.TEAM_VARIATIONS.get(team, []))

        return teams

    def get_all_confirmations(self) -> Tuple[int, int]:
        """Main entry point - fetches all confirmations"""
        if self.verbose:
            print("\n🔍 FETCHING CONFIRMATIONS - UNIVERSAL MODE")
            print("=" * 60)

        self._fetch_confirmations()

        lineup_count = sum(len(lineup) for lineup in self.confirmed_lineups.values())
        pitcher_count = len(self.confirmed_pitchers)

        if self.verbose:
            print(f"\n📊 CONFIRMATION TOTALS:")
            print(f"   Teams with lineups: {len(self.confirmed_lineups)}")
            print(f"   Total players: {lineup_count}")
            print(f"   Starting pitchers: {pitcher_count}")

        return lineup_count, pitcher_count

    def _fetch_confirmations(self):
        """Fetch confirmations from MLB API"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=lineups,probablePitcher,team"

            if self.verbose:
                print(f"🌐 Fetching from MLB API...")
                print(f"   URL: {url}")

            response = self._session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"❌ API returned status {response.status_code}")
                return

            data = response.json()
            dates = data.get('dates', [])

            if not dates:
                print("❌ No games found for today")
                return

            games = dates[0].get('games', [])

            if self.verbose:
                print(f"📅 Found {len(games)} games today")

            games_processed = 0
            for game in games:
                if self._process_game_universal(game):
                    games_processed += 1

            if self.verbose:
                print(f"✅ Processed {games_processed} games with relevant teams")

        except Exception as e:
            logger.error(f"Error fetching confirmations: {e}")
            if self.verbose:
                print(f"❌ Error: {e}")

    def _process_game_universal(self, game: Dict) -> bool:
        """FIXED: Process a game with proper variable handling"""
        try:
            teams_data = game.get('teams', {})

            away_data = teams_data.get('away', {})
            home_data = teams_data.get('home', {})

            away_team = away_data.get('team', {})
            home_team = home_data.get('team', {})

            away_abbr = away_team.get('abbreviation', '')
            home_abbr = home_team.get('abbreviation', '')

            if not away_abbr or not home_abbr:
                return False

            process_away = self._should_process_team(away_abbr)
            process_home = self._should_process_team(home_abbr)

            if not process_away and not process_home:
                return False

            if self.verbose:
                status = game.get('status', {}).get('detailedState', 'Unknown')
                print(f"\n🎮 Processing: {away_abbr}@{home_abbr} ({status})")

            lineups_found = False
            pitchers_found = False  # FIXED: Track pitchers separately

            # Check for lineups
            game_lineups = game.get('lineups', {})
            if game_lineups:
                if process_away:
                    away_players = game_lineups.get('awayPlayers', [])
                    if away_players:
                        self._store_lineup(away_abbr, away_players, 'game.lineups')
                        lineups_found = True

                if process_home:
                    home_players = game_lineups.get('homePlayers', [])
                    if home_players:
                        self._store_lineup(home_abbr, home_players, 'game.lineups')
                        lineups_found = True

            # Check team data for lineups
            if not lineups_found:
                if process_away:
                    away_players = away_data.get('players', {})
                    if away_players:
                        self._store_lineup_from_dict(away_abbr, away_players, 'teams.players')
                        lineups_found = True

                if process_home:
                    home_players = home_data.get('players', {})
                    if home_players:
                        self._store_lineup_from_dict(home_abbr, home_players, 'teams.players')
                        lineups_found = True

            # FIXED: Check for pitchers separately with proper scope
            if process_away:
                away_pitcher = away_data.get('probablePitcher', {})
                if away_pitcher and away_pitcher.get('fullName'):
                    self._store_pitcher(away_abbr, away_pitcher)
                    pitchers_found = True

            if process_home:
                home_pitcher = home_data.get('probablePitcher', {})
                if home_pitcher and home_pitcher.get('fullName'):
                    self._store_pitcher(home_abbr, home_pitcher)
                    pitchers_found = True

            return lineups_found or pitchers_found

        except Exception as e:
            logger.error(f"Error processing game: {e}")
            if self.verbose:
                print(f"   ❌ Error: {e}")
            return False

    def _should_process_team(self, team_abbr: str) -> bool:
        """Determine if a team should be processed"""
        if not self.csv_teams:
            return True

        if team_abbr in self.csv_teams:
            return True

        variations = self.TEAM_VARIATIONS.get(team_abbr, [])
        for variant in variations:
            if variant in self.csv_teams:
                return True

        return False

    def _store_lineup(self, team_abbr: str, players: List[Dict], source: str):
        """Store lineup from list format"""
        with self._lock:
            if team_abbr not in self.confirmed_lineups:
                self.confirmed_lineups[team_abbr] = []

            for i, player in enumerate(players):
                player_info = {
                    'name': player.get('fullName', ''),
                    'id': player.get('id'),
                    'position': player.get('primaryPosition', {}).get('abbreviation', ''),
                    'order': i + 1,
                    'team': team_abbr,
                    'source': source
                }
                self.confirmed_lineups[team_abbr].append(player_info)

            if self.verbose:
                print(f"   ✅ {team_abbr}: {len(players)} players from {source}")

    def _store_lineup_from_dict(self, team_abbr: str, players_dict: Dict, source: str):
        """Store lineup from dict format"""
        with self._lock:
            if team_abbr not in self.confirmed_lineups:
                self.confirmed_lineups[team_abbr] = []

            order = 1
            for player_id, player_data in players_dict.items():
                player_info = {
                    'name': player_data.get('fullName', ''),
                    'id': player_id,
                    'position': player_data.get('primaryPosition', {}).get('abbreviation', ''),
                    'order': order,
                    'team': team_abbr,
                    'source': source
                }
                self.confirmed_lineups[team_abbr].append(player_info)
                order += 1

            if self.verbose:
                print(f"   ✅ {team_abbr}: {len(players_dict)} players from {source}")

    def _store_pitcher(self, team_abbr: str, pitcher_data: Dict):
        """Store pitcher information"""
        with self._lock:
            pitcher_info = {
                'name': pitcher_data.get('fullName', ''),
                'id': pitcher_data.get('id'),
                'team': team_abbr,
                'source': 'mlb_api'
            }
            self.confirmed_pitchers[team_abbr] = pitcher_info

            if self.verbose:
                print(f"   ⚾ {team_abbr}: {pitcher_info['name']} (SP)")

    def is_player_confirmed(self, player_name: str, team: str = None) -> Tuple[bool, Optional[int]]:
        """Check if player is confirmed with batting order"""
        if not team:
            return False, None

        teams_to_check = [team]
        if team in self.TEAM_VARIATIONS:
            teams_to_check.extend(self.TEAM_VARIATIONS[team])

        for check_team in teams_to_check:
            if check_team in self.confirmed_lineups:
                lineup = self.confirmed_lineups[check_team]
                player_name_lower = player_name.lower().strip()

                for lineup_player in lineup:
                    lineup_name = lineup_player.get('name', '').lower().strip()

                    if player_name_lower == lineup_name:
                        return True, lineup_player.get('order', 1)

                    if self._names_match(player_name_lower, lineup_name):
                        return True, lineup_player.get('order', 1)

        return False, None

    def is_pitcher_confirmed(self, pitcher_name: str, team: str = None) -> bool:
        """Check if pitcher is confirmed starter"""
        if not team:
            return False

        teams_to_check = [team]
        if team in self.TEAM_VARIATIONS:
            teams_to_check.extend(self.TEAM_VARIATIONS[team])

        for check_team in teams_to_check:
            if check_team in self.confirmed_pitchers:
                confirmed_pitcher = self.confirmed_pitchers[check_team]
                pitcher_name_lower = pitcher_name.lower().strip()
                confirmed_name = confirmed_pitcher.get('name', '').lower().strip()

                if pitcher_name_lower == confirmed_name:
                    return True

                if self._names_match(pitcher_name_lower, confirmed_name):
                    return True

        return False

    def _names_match(self, name1: str, name2: str) -> bool:
        """Fuzzy name matching"""
        for suffix in [' jr.', ' sr.', ' jr', ' sr', ' iii', ' ii']:
            name1 = name1.replace(suffix, '')
            name2 = name2.replace(suffix, '')

        if name1 in name2 or name2 in name1:
            return True

        parts1 = name1.split()
        parts2 = name2.split()

        if len(parts1) >= 2 and len(parts2) >= 2:
            if parts1[-1] == parts2[-1]:
                if parts1[0][0] == parts2[0][0]:
                    return True

        return False


# For compatibility
SmartConfirmationSystem = UniversalSmartConfirmation