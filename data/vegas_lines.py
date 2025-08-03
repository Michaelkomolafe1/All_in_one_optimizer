#!/usr/bin/env python3
"""Vegas lines integration with The Odds API"""
from datetime import datetime
import requests
from functools import lru_cache
from typing import Any, Dict, List, Optional
import logging

# Set up logger
logger = logging.getLogger(__name__)


# Simple cache implementation to avoid import errors
class SimpleCache:
    def __init__(self):
        self.cache = {}

    def get(self, key):
        return self.cache.get(key)

    def put(self, key, value):
        self.cache[key] = value


class SimpleCacheManager:
    def __init__(self):
        self._cache = SimpleCache()

    def cache_key(self, *args):
        return str(args)

    def get_cache(self, name):
        return self._cache


# Always use simple cache manager
def get_cache_manager():
    return SimpleCacheManager()


# Constants
ODDS_API_KEY = "14b669db87ed65f1d0f3e70a90386707"
API_BASE_URL = "https://api.the-odds-api.com/v4"


class VegasLines:
    """Fetch and manage Vegas betting lines"""

    def __init__(self, api_key=ODDS_API_KEY):
        self.api_key = api_key
        self.cache_manager = get_cache_manager()
        self.cache = self.cache_manager.get_cache('vegas_lines')
        self.lines = {}

    def get_vegas_lines(self, sport='baseball_mlb'):
        """Fetch current Vegas lines"""
        cache_key = self.cache_manager.cache_key('vegas_lines', sport, datetime.now().date())

        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            logger.info("Using cached Vegas lines")
            self.lines = cached
            return cached

        # Fetch from API
        try:
            url = f"{API_BASE_URL}/sports/{sport}/odds/"
            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': 'totals,spreads',
                'oddsFormat': 'american'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            self.lines = self._parse_odds(data)

            # Cache results
            self.cache.put(cache_key, self.lines)

            logger.info(f"Fetched Vegas lines for {len(self.lines)} teams")
            return self.lines

        except Exception as e:
            logger.error(f"Failed to fetch Vegas lines: {e}")
            # Return default lines
            return self._get_default_lines()

    def _parse_odds(self, data):
        """Parse odds response into team lines"""
        lines = {}

        for game in data:
            home_team = self._normalize_team(game.get('home_team', ''))
            away_team = self._normalize_team(game.get('away_team', ''))

            # Get totals from first bookmaker
            total = 9.0  # Default
            if game.get('bookmakers'):
                for bookmaker in game['bookmakers']:
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'totals':
                            for outcome in market['outcomes']:
                                if outcome['name'] == 'Over':
                                    total = outcome['point']
                                    break
                            break
                    break

            # Calculate implied totals (simple split)
            implied_home = total / 2
            implied_away = total / 2

            lines[home_team] = {
                'team': home_team,
                'opponent': away_team,
                'total': total,
                'implied_total': implied_home,
                'is_home': True
            }

            lines[away_team] = {
                'team': away_team,
                'opponent': home_team,
                'total': total,
                'implied_total': implied_away,
                'is_home': False
            }

        return lines

    def _normalize_team(self, team_name):
        """Normalize team name to abbreviation"""
        # Add your team mappings here
        team_map = {
            "Arizona Diamondbacks": "ARI",
            "Atlanta Braves": "ATL",
            "Baltimore Orioles": "BAL",
            "Boston Red Sox": "BOS",
            "Chicago White Sox": "CWS",
            "Chicago Cubs": "CHC",
            "Cincinnati Reds": "CIN",
            "Cleveland Guardians": "CLE",
            "Colorado Rockies": "COL",
            "Detroit Tigers": "DET",
            "Houston Astros": "HOU",
            "Kansas City Royals": "KC",
            "Los Angeles Angels": "LAA",
            "Los Angeles Dodgers": "LAD",
            "Miami Marlins": "MIA",
            "Milwaukee Brewers": "MIL",
            "Minnesota Twins": "MIN",
            "New York Yankees": "NYY",
            "New York Mets": "NYM",
            "Oakland Athletics": "OAK",
            "Philadelphia Phillies": "PHI",
            "Pittsburgh Pirates": "PIT",
            "San Diego Padres": "SD",
            "San Francisco Giants": "SF",
            "Seattle Mariners": "SEA",
            "St. Louis Cardinals": "STL",
            "Tampa Bay Rays": "TB",
            "Texas Rangers": "TEX",
            "Toronto Blue Jays": "TOR",
            "Washington Nationals": "WSH"
        }
        return team_map.get(team_name, team_name[:3].upper())

    def _get_default_lines(self):
        """Return default lines when API fails"""
        return {
            'NYY': {'total': 9.0, 'implied_total': 4.5},
            'BOS': {'total': 9.5, 'implied_total': 4.8},
            'HOU': {'total': 8.5, 'implied_total': 4.2},
            # Add more defaults as needed
        }

    def get_player_vegas_data(self, player):
        """Get Vegas data for a specific player"""
        if not self.lines:
            self.get_vegas_lines()

        team_data = self.lines.get(player.team, {})
        if team_data:
            return {
                'game_total': team_data.get('total', 9.0),
                'implied_total': team_data.get('implied_total', 4.5),
                'is_home': team_data.get('is_home', True),
                'vegas_multiplier': self._calculate_vegas_multiplier(player, team_data)
            }
        return None

    def _calculate_vegas_multiplier(self, player, team_data):
        """Calculate scoring multiplier based on Vegas data"""
        total = team_data.get('total', 9.0)

        if player.primary_position == 'P':
            # Pitchers: lower totals are better
            if total <= 7.5:
                return 1.10
            elif total <= 8.5:
                return 1.05
            elif total >= 10.0:
                return 0.90
            else:
                return 0.95
        else:
            # Hitters: higher totals are better
            if total >= 10.5:
                return 1.15
            elif total >= 9.5:
                return 1.08
            elif total <= 7.5:
                return 0.85
            else:
                return 1.00