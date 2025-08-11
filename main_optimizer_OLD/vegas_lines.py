#!/usr/bin/env python3
"""
Vegas Lines with The Odds API
Your API Key: 14b669db87ed65f1d0f3e70a90386707
"""

import requests
import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)


class VegasLines:
    """Real Vegas lines from The Odds API"""

    def __init__(self):
        self.api_key = '14b669db87ed65f1d0f3e70a90386707'
        self.base_url = 'https://api.the-odds-api.com/v4'
        self.cache = {}
        self.cache_time = None

        # Initial fetch
        self.fetch_all_lines()

    def fetch_all_lines(self):
        """Fetch MLB totals from The Odds API"""
        try:
            # Check your remaining quota first
            response = requests.get(
                f'{self.base_url}/sports/baseball_mlb/odds',
                params={
                    'apiKey': self.api_key,
                    'regions': 'us',
                    'markets': 'totals',
                    'oddsFormat': 'american',
                    'bookmakers': 'draftkings,fanduel'
                }
            )

            if response.status_code == 200:
                games = response.json()
                self.process_games(games)

                # Check remaining requests
                remaining = response.headers.get('x-requests-remaining', 'unknown')
                logger.info(f"✅ Vegas data fetched. Requests remaining: {remaining}")
            else:
                logger.warning(f"Vegas API error: {response.status_code}")
                self.set_defaults()

        except Exception as e:
            logger.error(f"Vegas fetch error: {e}")
            self.set_defaults()

    def process_games(self, games):
        """Process API response into team totals"""
        self.cache = {}

        for game in games:
            home = self.convert_team_name(game.get('home_team', ''))
            away = self.convert_team_name(game.get('away_team', ''))

            # Get the total from bookmakers
            total = 8.5  # Default
            for bookmaker in game.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'totals':
                        outcomes = market.get('outcomes', [])
                        if outcomes:
                            total = outcomes[0].get('point', 8.5)
                            break

            # Simple 50/50 split (can be improved with spreads)
            self.cache[home] = {
                'implied_total': total / 2,
                'game_total': total,
                'is_home': True
            }
            self.cache[away] = {
                'implied_total': total / 2,
                'game_total': total,
                'is_home': False
            }

        self.cache_time = datetime.now()

    def convert_team_name(self, full_name: str) -> str:
        """Convert API team names to DK abbreviations"""
        # More comprehensive mapping
        mappings = {
            # API Name -> DK Code
            'New York Yankees': 'NYY',
            'Boston Red Sox': 'BOS',
            'Baltimore Orioles': 'BAL',
            'Tampa Bay Rays': 'TB',
            'Toronto Blue Jays': 'TOR',
            'Chicago White Sox': 'CWS',
            'Cleveland Guardians': 'CLE',
            'Detroit Tigers': 'DET',
            'Kansas City Royals': 'KC',
            'Minnesota Twins': 'MIN',
            'Houston Astros': 'HOU',
            'Los Angeles Angels': 'LAA',
            'Oakland Athletics': 'OAK',
            'Seattle Mariners': 'SEA',
            'Texas Rangers': 'TEX',
            'Atlanta Braves': 'ATL',
            'Miami Marlins': 'MIA',
            'New York Mets': 'NYM',
            'Philadelphia Phillies': 'PHI',
            'Washington Nationals': 'WAS',
            'Chicago Cubs': 'CHC',
            'Cincinnati Reds': 'CIN',
            'Milwaukee Brewers': 'MIL',
            'Pittsburgh Pirates': 'PIT',
            'St. Louis Cardinals': 'STL',
            'Arizona Diamondbacks': 'ARI',
            'Colorado Rockies': 'COL',
            'Los Angeles Dodgers': 'LAD',
            'San Diego Padres': 'SD',
            'San Francisco Giants': 'SF'
        }

        # Try exact match first
        if full_name in mappings:
            return mappings[full_name]

        # Try partial match
        for api_name, dk_code in mappings.items():
            if api_name.lower() in full_name.lower():
                return dk_code

        logger.warning(f"Unknown team: {full_name}")
        return None

    def set_defaults(self):
        """Fallback totals if API fails"""
        self.cache = {
            'COL': {'implied_total': 5.5, 'game_total': 11.0, 'is_home': True},
            'NYY': {'implied_total': 5.0, 'game_total': 9.5, 'is_home': True},
            'LAD': {'implied_total': 5.0, 'game_total': 9.0, 'is_home': True},
            # Basic defaults
        }

    # In vegas_lines.py, improve the get_data method:

    def get_data(self, team: str) -> Dict:
        """Get Vegas data for a team with smart fallbacks"""

        # First, check cache
        if team in self.cache:
            return self.cache[team]

        team_fixes = {
            'WSH': 'WAS',
            'ATH': 'ATL',
            'CHW': 'CWS',
            'CHA': 'CWS',  # Charlotte (White Sox AA) maps to CWS
        }

        team = team_fixes.get(team, team)

        # Now check cache
        if team in self.cache:
            return self.cache[team]

        # If not in cache, might be a different team code
        team_mappings = {
            'CHW': 'CWS',
            'WSH': 'WAS',
            # Add others as needed
        }

        mapped_team = team_mappings.get(team, team)
        if mapped_team in self.cache:
            return self.cache[mapped_team]

        # Smart defaults based on team quality (not just 4.5)
        team_defaults = {
            # Good offenses
            'NYY': 5.5, 'LAD': 5.0, 'ATL': 5.0, 'HOU': 5.0,
            'TB': 4.8, 'TEX': 4.8, 'TOR': 4.7,

            # Average teams
            'SEA': 4.5, 'MIL': 4.5, 'PHI': 4.5, 'SD': 4.5,
            'BOS': 4.5, 'MIN': 4.5, 'CHC': 4.5,

            # Lower scoring
            'OAK': 3.8, 'MIA': 3.8, 'PIT': 3.8,
            'KC': 4.0, 'DET': 4.0, 'CIN': 4.0,
            'WAS': 4.0, 'CWS': 3.5, 'COL': 5.5,  # COL high for Coors
        }

        # Return smart default
        default_total = team_defaults.get(team, 4.5)

        logger.debug(f"Team {team} not in Vegas cache, using default {default_total}")

        return {
            'implied_total': default_total,
            'game_total': default_total * 2,
            'is_home': False  # Unknown
        }

    def get_team_total(self, team: str) -> float:
        """Get implied team total"""
        return self.cache.get(team, {}).get('implied_total', 4.5)