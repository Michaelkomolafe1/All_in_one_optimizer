#!/usr/bin/env python3
"""
Vegas Lines Integration with The Odds API
========================================
Enhanced version with proper caching and clean structure
"""

import json
import logging
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import wraps

# Set up logging
logger = logging.getLogger(__name__)

# Try to import enhanced caching system if available
try:
    from enhanced_caching_system import get_cache_manager

    ENHANCED_CACHE_AVAILABLE = True
except ImportError:
    ENHANCED_CACHE_AVAILABLE = False
    logger.info("Enhanced caching system not available, using file-based cache")


class VegasLines:
    """Vegas lines using The Odds API with improved caching"""

    # Team abbreviation mapping
    TEAM_MAP = {
        "Arizona Diamondbacks": "ARI", "Atlanta Braves": "ATL",
        "Baltimore Orioles": "BAL", "Boston Red Sox": "BOS",
        "Chicago Cubs": "CHC", "Chicago White Sox": "CWS",
        "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE",
        "Colorado Rockies": "COL", "Detroit Tigers": "DET",
        "Houston Astros": "HOU", "Kansas City Royals": "KC",
        "Los Angeles Angels": "LAA", "Los Angeles Dodgers": "LAD",
        "Miami Marlins": "MIA", "Milwaukee Brewers": "MIL",
        "Minnesota Twins": "MIN", "New York Mets": "NYM",
        "New York Yankees": "NYY", "Oakland Athletics": "OAK",
        "Philadelphia Phillies": "PHI", "Pittsburgh Pirates": "PIT",
        "San Diego Padres": "SD", "San Francisco Giants": "SF",
        "Seattle Mariners": "SEA", "St. Louis Cardinals": "STL",
        "Tampa Bay Rays": "TB", "Texas Rangers": "TEX",
        "Toronto Blue Jays": "TOR", "Washington Nationals": "WSH"
    }

    def __init__(self, api_key: str = "14b669db87ed65f1d0f3e70a90386707", verbose: bool = True):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.lines = {}
        self.verbose = verbose

        # Cache configuration
        self.cache_duration = 600  # 10 minutes
        self.cache_file = Path("data/cache/vegas_lines_cache.json")
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Enhanced cache manager if available
        self.cache_manager = get_cache_manager() if ENHANCED_CACHE_AVAILABLE else None

        # API call tracking
        self._api_calls_made = 0
        self._last_api_call = None

    def verbose_print(self, message: str):
        """Print if verbose mode is on"""
        if self.verbose:
            print(message)

    def _get_cache_key(self) -> str:
        """Generate cache key with hourly granularity"""
        now = datetime.now()
        return f"vegas_lines_{now.strftime('%Y%m%d_%H')}"

    def _load_from_file_cache(self) -> Optional[Dict]:
        """Load data from file-based cache"""
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)

            # Check if cache is expired
            cached_time = datetime.fromisoformat(cache_data.get('timestamp', '2000-01-01'))
            if datetime.now() - cached_time > timedelta(seconds=self.cache_duration):
                self.verbose_print("📅 File cache expired")
                return None

            self.verbose_print(f"📁 Loaded {len(cache_data.get('data', {}))} games from file cache")
            return cache_data.get('data', {})

        except Exception as e:
            logger.error(f"Error loading file cache: {e}")
            return None

    def _save_to_file_cache(self, data: Dict):
        """Save data to file-based cache"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            self.verbose_print("💾 Saved to file cache")
        except Exception as e:
            logger.error(f"Error saving to file cache: {e}")

    def get_vegas_lines(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Get Vegas lines with proper caching
        Returns: Dict[team_abbr, team_data]
        """
        # Try enhanced cache first
        if not force_refresh and self.cache_manager:
            cache_key = self._get_cache_key()
            cached_data = self.cache_manager.get_cache('vegas').get(cache_key)

            if cached_data and isinstance(cached_data, dict) and len(cached_data) > 0:
                self.verbose_print(f"✅ Using enhanced cached Vegas data ({len(cached_data)} games)")
                self.lines = cached_data
                return cached_data

        # Try file cache as fallback
        if not force_refresh:
            file_cached = self._load_from_file_cache()
            if file_cached:
                self.lines = file_cached

                # Also update enhanced cache if available
                if self.cache_manager:
                    cache_key = self._get_cache_key()
                    self.cache_manager.get_cache('vegas').put(cache_key, file_cached)

                return file_cached

        # No valid cache - fetch from API
        self.verbose_print("🎰 Fetching fresh Vegas lines from API...")
        fresh_data = self._fetch_from_api()

        if fresh_data:
            self.lines = fresh_data

            # Update both caches
            self._save_to_file_cache(fresh_data)

            if self.cache_manager:
                cache_key = self._get_cache_key()
                self.cache_manager.get_cache('vegas').put(cache_key, fresh_data)

        return fresh_data

    # In vegas_lines.py, find the _fetch_from_api method and update:

    # In main_optimizer/vegas_lines.py, update the _fetch_from_api method:

    def _fetch_from_api(self) -> Dict[str, Dict]:
        """Fetch fresh data from The Odds API"""
        try:
            self._api_calls_made += 1
            self._last_api_call = datetime.now()

            # The correct URL for The Odds API v4
            url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

            # API key MUST be in params for The Odds API
            params = {
                "apiKey": "14b669db87ed65f1d0f3e70a90386707",
                "regions": "us",
                "markets": "totals",
                "dateFormat": "iso",
                "oddsFormat": "american"
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.verbose_print(f"📡 API call successful - {len(data)} games")
                return self._process_odds_data(data)
            else:
                self.verbose_print(f"❌ API error: {response.status_code}")
                logger.error(f"Vegas API error: {response.status_code} - {response.text}")
                return {}

        except Exception as e:
            self.verbose_print(f"❌ Error fetching Vegas: {e}")
            logger.error(f"Exception fetching Vegas lines: {e}")
            return {}

        except Exception as e:
            self.verbose_print(f"❌ Error fetching Vegas: {e}")
            logger.error(f"Exception fetching Vegas lines: {e}")
            return {}

    def _process_odds_data(self, data: List[Dict]) -> Dict[str, Dict]:
        """Process raw odds data into our format"""
        processed = {}

        for game in data:
            try:
                # Skip if no bookmakers
                if not game.get('bookmakers'):
                    continue

                # Get teams
                home_team = self._normalize_team(game.get('home_team', ''))
                away_team = self._normalize_team(game.get('away_team', ''))

                # Find total from first bookmaker with totals
                total = 9.0  # Default
                for bookmaker in game['bookmakers']:
                    for market in bookmaker.get('markets', []):
                        if market.get('key') == 'totals':
                            outcomes = market.get('outcomes', [])
                            if outcomes:
                                total = outcomes[0].get('point', 9.0)
                                break
                    if total != 9.0:
                        break

                # Calculate implied totals (simple split)
                implied_home = total / 2.0
                implied_away = total / 2.0

                # Store data for both teams
                processed[home_team] = {
                    'total': total,
                    'implied_total': implied_home,
                    'opponent': away_team,
                    'home': True,
                    'game_time': game.get('commence_time', '')
                }

                processed[away_team] = {
                    'total': total,
                    'implied_total': implied_away,
                    'opponent': home_team,
                    'home': False,
                    'game_time': game.get('commence_time', '')
                }

            except Exception as e:
                logger.error(f"Error processing game: {e}")
                continue

        self.verbose_print(f"✅ Processed {len(processed)} team entries")
        return processed

    def _normalize_team(self, team_name: str) -> str:
        """Convert API team names to DFS abbreviations"""
        return self.TEAM_MAP.get(team_name, team_name[:3].upper())

    def get_player_vegas_data(self, player) -> Optional[Dict]:
        """Get Vegas data for a single player"""
        if not hasattr(player, "team") or not player.team:
            return None

        # Ensure we have data
        if not self.lines:
            self.get_vegas_lines()

        team_data = self.lines.get(player.team)
        if not team_data:
            return None

        # Return enriched data
        vegas_data = {
            'total': team_data.get('total', 9.0),
            'implied_total': team_data.get('implied_total', 4.5),
            'home': team_data.get('home', True),
            'opponent': team_data.get('opponent', 'OPP'),
            'vegas_multiplier': self._calculate_vegas_multiplier(player, team_data)
        }

        # Log high-scoring games
        if vegas_data['implied_total'] > 5.5:
            logger.info(f"VEGAS: High-scoring game - {player.team} implied: {vegas_data['implied_total']}")

        return vegas_data

    def _calculate_vegas_multiplier(self, player, team_data: Dict) -> float:
        """Calculate Vegas multiplier based on game total and player position"""
        game_total = team_data.get('total', 9.0)

        # Get player position safely
        position = getattr(player, 'primary_position', getattr(player, 'position', 'UTIL'))

        if position == 'P':
            # Pitchers benefit from low totals
            if game_total <= 7.5:
                return 1.12
            elif game_total <= 8.5:
                return 1.06
            elif game_total >= 10.5:
                return 0.92
            elif game_total >= 9.5:
                return 0.96
            else:
                return 1.0
        else:
            # Hitters benefit from high totals
            if game_total >= 10.5:
                return 1.15
            elif game_total >= 9.5:
                return 1.08
            elif game_total <= 7.5:
                return 0.88
            elif game_total <= 8.5:
                return 0.94
            else:
                return 1.0

    def enrich_players(self, players: List) -> int:
        """Enrich multiple players with Vegas data"""
        if not self.lines:
            self.get_vegas_lines()

        enriched = 0
        for player in players:
            try:
                vegas_data = self.get_player_vegas_data(player)
                if vegas_data:
                    # Set all Vegas attributes on player
                    player.vegas_total = vegas_data['total']
                    player.team_total = vegas_data['implied_total']
                    player.vegas_multiplier = vegas_data['vegas_multiplier']
                    player.is_home = vegas_data['home']
                    player.opponent = vegas_data['opponent']

                    # Also try to apply multiplier if method exists
                    if hasattr(player, 'apply_vegas_multiplier'):
                        player.apply_vegas_multiplier(vegas_data['vegas_multiplier'])

                    enriched += 1
            except Exception as e:
                logger.error(f"Error enriching player {getattr(player, 'name', 'Unknown')}: {e}")

        self.verbose_print(f"✅ Enriched {enriched}/{len(players)} players with Vegas data")
        return enriched

    # Convenience methods
    def apply_to_players(self, players: List) -> List:
        """Legacy method for compatibility"""
        self.enrich_players(players)
        return players

    def get_high_total_teams(self, threshold: float = 9.5) -> List[str]:
        """Get teams in high-scoring games"""
        if not self.lines:
            self.get_vegas_lines()
        return [team for team, info in self.lines.items()
                if info.get('total', 0) >= threshold]

    def get_low_total_teams(self, threshold: float = 8.0) -> List[str]:
        """Get teams in low-scoring games"""
        if not self.lines:
            self.get_vegas_lines()
        return [team for team, info in self.lines.items()
                if info.get('total', 0) <= threshold]

    def get_team_vegas_data(self, team: str) -> Optional[Dict]:
        """Get Vegas data for a specific team"""
        if not self.lines:
            self.get_vegas_lines()
        return self.lines.get(team)

    def get_api_status(self) -> Dict:
        """Get API usage status"""
        return {
            'api_calls_made': self._api_calls_made,
            'last_api_call': self._last_api_call,
            'cached_games': len(self.lines),
            'cache_type': 'enhanced' if self.cache_manager else 'file'
        }

    def print_summary(self):
        """Print Vegas lines summary"""
        if not self.lines:
            self.get_vegas_lines()

        print("\n🎰 VEGAS LINES SUMMARY")
        print("=" * 50)

        # Group by game
        games = {}
        for team, info in self.lines.items():
            if info['home']:
                games[team] = (team, info['opponent'], info['total'])

        # Sort by total
        sorted_games = sorted(games.values(), key=lambda x: x[2], reverse=True)

        print(f"Total games: {len(sorted_games)}")
        print(f"API calls made: {self._api_calls_made}")
        print(f"Cache status: {'Enhanced' if self.cache_manager else 'File-based'}")
        print("\nGames by total:")

        for home, away, total in sorted_games:
            print(f"  {away} @ {home}: {total}")

        high_total = self.get_high_total_teams(9.5)
        low_total = self.get_low_total_teams(8.0)

        print(f"\nHigh totals (9.5+): {len(high_total)} teams")
        if high_total:
            print(f"  Teams: {', '.join(sorted(high_total))}")

        print(f"\nLow totals (8.0-): {len(low_total)} teams")
        if low_total:
            print(f"  Teams: {', '.join(sorted(low_total))}")


# Test functionality
if __name__ == "__main__":
    print("Testing Vegas Lines module...")
    vegas = VegasLines()

    # Test fetching
    lines = vegas.get_vegas_lines()
    if lines:
        print("✅ Module working correctly!")
        vegas.print_summary()

        # Test API status
        print(f"\nAPI Status: {vegas.get_api_status()}")

        # Test caching by calling again
        print("\n🔄 Testing cache...")
        lines2 = vegas.get_vegas_lines()
        print(f"Cache working: {vegas._api_calls_made == 1}")
    else:
        print("❌ Failed to fetch lines")