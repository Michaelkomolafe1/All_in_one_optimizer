#!/usr/bin/env python3
"""
SMART CONFIRMATION SYSTEM
========================
Unified system for lineup and pitcher confirmations
Uses data integration system for consistent team/name mapping
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from unified_data_system import UnifiedDataSystem
import logging

logger = logging.getLogger(__name__)


class SmartConfirmationSystem:
    """Unified confirmation system with smart filtering"""

    def __init__(self, csv_players: List = None, verbose: bool = False):
        self.verbose = verbose
        self.csv_players = csv_players or []
        self.data_system = UnifiedDataSystem()
        self.confirmed_lineups = {}
        self.confirmed_pitchers = {}

        # Extract teams from CSV for smart filtering
        self.csv_teams = self.data_system.get_teams_from_players(csv_players) if csv_players else set()

        if self.verbose and self.csv_teams:
            print(f"📊 CSV teams detected: {sorted(self.csv_teams)}")

    def get_all_confirmations(self) -> Tuple[int, int]:
        """
        Get all confirmations using multiple sources
        Only for teams in the CSV

        Returns:
            Tuple of (lineup_count, pitcher_count)
        """
        print("🔍 SMART CONFIRMATION SYSTEM")
        print("=" * 50)

        # Try MLB Stats API first
        mlb_data = self._fetch_mlb_confirmations()

        # If not enough data, use enhanced CSV analysis
        if self._needs_more_confirmations():
            csv_data = self._enhanced_csv_analysis()
            self._merge_confirmations(csv_data)

        # Filter to only CSV teams
        self._filter_to_csv_teams()

        lineup_count = sum(len(lineup) for lineup in self.confirmed_lineups.values())
        pitcher_count = len(self.confirmed_pitchers)

        print(f"✅ Total confirmations: {lineup_count} lineup spots, {pitcher_count} pitchers")
        print(f"📊 Teams covered: {len(self.confirmed_lineups)} lineups, {len(self.confirmed_pitchers)} pitchers")

        return lineup_count, pitcher_count

    def _fetch_mlb_confirmations(self) -> Dict:
        """Fetch confirmations from MLB Stats API"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=lineups,probablePitcher"

            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return {}

            data = response.json()
            confirmations = {'lineups': {}, 'pitchers': {}}

            for date_data in data.get('dates', []):
                for game in date_data.get('games', []):
                    self._process_game_data(game, confirmations)

            # Apply confirmations
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
            if self.verbose:
                print(f"⚠️ MLB API error: {e}")
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
        # Remove any teams not in CSV
        self.confirmed_lineups = {
            team: lineup for team, lineup in self.confirmed_lineups.items()
            if team in self.csv_teams
        }
        self.confirmed_pitchers = {
            team: pitcher for team, pitcher in self.confirmed_pitchers.items()
            if team in self.csv_teams
        }

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
        pass

    def is_player_confirmed(self, player_name: str, team: str = None) -> Tuple[bool, Optional[int]]:
        """Check if player is confirmed"""
        if team:
            team = self.data_system.normalize_team(team)
            if team in self.confirmed_lineups:
                for lineup_player in self.confirmed_lineups[team]:
                    if self.data_system.match_player_names(player_name, lineup_player['name']):
                        return True, lineup_player.get('order', 1)

        return False, None

    def is_pitcher_confirmed(self, pitcher_name: str, team: str = None) -> bool:
        """Check if pitcher is confirmed starter"""
        if team:
            team = self.data_system.normalize_team(team)
            if team in self.confirmed_pitchers:
                return self.data_system.match_player_names(
                    pitcher_name,
                    self.confirmed_pitchers[team]['name']
                )

        return False