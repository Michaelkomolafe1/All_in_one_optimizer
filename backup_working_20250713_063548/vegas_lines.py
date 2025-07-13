#!/usr/bin/env python3
"""
Vegas Lines Module - FIXED to use multipliers instead of fixed boosts
====================================================================
Integrates with UnifiedScoringEngine for consistent scoring
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry  # Fixed import

# Set up logging
logger = logging.getLogger(__name__)


class VegasLines:
    """
    FIXED: Vegas lines data fetcher and processor using MULTIPLIERS
    Now properly integrates with the unified scoring system
    """

    def __init__(self, use_cache: bool = True, cache_duration_minutes: int = 30, verbose: bool = False):
        """Initialize Vegas lines fetcher with caching"""
        self.api_key = os.environ.get("ODDS_API_KEY", "YOUR_API_KEY_HERE")
        self.base_url = "https://api.the-odds-api.com/v4"
        self.sport = "baseball_mlb"

        self.use_cache = use_cache
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.cache_file = "vegas_cache.json"

        self.verbose = verbose
        self.lines = {}

        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Initialize on creation
        self.get_vegas_lines()

    def verbose_print(self, message: str):
        """Print if verbose mode is enabled"""
        if self.verbose:
            print(f"[Vegas] {message}")

    def get_vegas_lines(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Fetch Vegas lines with caching support
        Returns dict keyed by team code with vegas data
        """
        # Check cache first
        if self.use_cache and not force_refresh:
            cached_data = self._load_from_cache()
            if cached_data:
                self.lines = cached_data
                return cached_data

        # Fetch fresh data
        try:
            self.verbose_print("Fetching fresh Vegas lines...")

            # Markets to fetch
            markets = "totals"  # We primarily care about totals

            url = f"{self.base_url}/sports/{self.sport}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "us",
                "markets": markets,
                "oddsFormat": "american",
                "dateFormat": "iso"
            }

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                processed = self._process_odds_data(data)

                # Save to cache
                if self.use_cache and processed:
                    self._save_to_cache(processed)

                self.lines = processed
                return processed
            else:
                self.verbose_print(f"API request failed: {response.status_code}")
                return self._get_fallback_lines()

        except Exception as e:
            self.verbose_print(f"Error fetching Vegas lines: {e}")
            return self._get_fallback_lines()

    def _process_odds_data(self, data: List[Dict]) -> Dict[str, Dict]:
        """Process raw odds API data into team-keyed format"""
        processed = {}

        for game in data:
            try:
                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')

                # Find totals from bookmakers
                total = None
                for bookmaker in game.get('bookmakers', []):
                    for market in bookmaker.get('markets', []):
                        if market.get('key') == 'totals':
                            outcomes = market.get('outcomes', [])
                            if outcomes and len(outcomes) > 0:
                                points = outcomes[0].get('point')
                                if points is not None:
                                    total = float(points)
                                    break
                    if total is not None:
                        break

                if total is None:
                    continue

                # Map team names to codes
                home_code = self._map_team_to_code(home_team)
                away_code = self._map_team_to_code(away_team)

                if not home_code or not away_code:
                    continue

                # Calculate implied totals (simple 50/50 split for now)
                # In production, use moneyline to weight this properly
                home_implied = total / 2
                away_implied = total / 2

                # Store data for both teams
                processed[home_code] = {
                    'team': home_code,
                    'opponent': away_code,
                    'game_total': total,
                    'team_total': home_implied,
                    'opponent_total': away_implied,
                    'implied_total': home_implied,  # For compatibility
                    'is_home': True
                }

                processed[away_code] = {
                    'team': away_code,
                    'opponent': home_code,
                    'game_total': total,
                    'team_total': away_implied,
                    'opponent_total': home_implied,
                    'implied_total': away_implied,  # For compatibility
                    'is_home': False
                }

            except Exception as e:
                self.verbose_print(f"Error processing game: {e}")
                continue

        self.verbose_print(f"Processed {len(processed)} team Vegas lines")
        return processed

    def enrich_players(self, players: List[Any]) -> int:
        """
        NEW METHOD: Enrich players with Vegas data for unified scoring engine
        This replaces the old apply_to_players method

        Returns: Number of players enriched
        """
        if not self.lines:
            self.get_vegas_lines()

        if not self.lines:
            self.verbose_print("No Vegas lines available for enrichment")
            return 0

        enriched_count = 0

        for player in players:
            try:
                # Skip if no team
                if not hasattr(player, 'team') or not player.team:
                    continue

                # Get Vegas data for player's team
                team_vegas = self.lines.get(player.team)
                if not team_vegas:
                    continue

                # Create Vegas data structure for player
                vegas_data = {
                    'implied_total': team_vegas['team_total'],
                    'opponent_total': team_vegas['opponent_total'],
                    'game_total': team_vegas['game_total'],
                    'is_home': team_vegas['is_home']
                }

                # Apply to player object
                if hasattr(player, 'apply_vegas_data'):
                    player.apply_vegas_data(vegas_data)
                else:
                    # Fallback - just set the attribute
                    player._vegas_data = vegas_data

                enriched_count += 1

                # Verbose logging for high/low totals
                if self.verbose:
                    if vegas_data['implied_total'] >= 5.5:
                        logger.info(f"HIGH total for {player.name}: {vegas_data['implied_total']:.1f}")
                    elif vegas_data['implied_total'] <= 3.5:
                        logger.info(f"LOW total for {player.name}: {vegas_data['implied_total']:.1f}")

            except Exception as e:
                logger.debug(f"Error enriching {getattr(player, 'name', 'unknown')}: {e}")

        self.verbose_print(f"Enriched {enriched_count} players with Vegas data")
        return enriched_count

    def get_player_vegas_data(self, player: Any) -> Optional[Dict]:
        """
        NEW METHOD: Get Vegas data for a single player
        Used by the performance optimizer for cached enrichment
        """
        if not hasattr(player, 'team') or not player.team:
            return None

        return self.lines.get(player.team)

    def get_team_implied_total(self, team_code: str) -> Optional[float]:
        """Get implied total for a specific team"""
        if team_code in self.lines:
            return self.lines[team_code].get('implied_total', 0)
        return None

    def get_game_total(self, team_code: str) -> Optional[float]:
        """Get game total for a team's game"""
        if team_code in self.lines:
            return self.lines[team_code].get('game_total', 0)
        return None

    def get_high_total_teams(self, threshold: float = 5.0) -> List[str]:
        """Get list of teams with high implied totals"""
        high_teams = []
        for team, data in self.lines.items():
            if data.get('implied_total', 0) >= threshold:
                high_teams.append(team)
        return sorted(high_teams)

    def get_low_total_teams(self, threshold: float = 4.0) -> List[str]:
        """Get list of teams with low implied totals"""
        low_teams = []
        for team, data in self.lines.items():
            if data.get('implied_total', 0) <= threshold:
                low_teams.append(team)
        return sorted(low_teams)

    def print_summary(self):
        """Print summary of current Vegas lines"""
        if not self.lines:
            print("No Vegas lines loaded")
            return

        print("\n📊 VEGAS LINES SUMMARY")
        print("=" * 60)

        # Sort by implied total
        sorted_teams = sorted(
            self.lines.items(),
            key=lambda x: x[1].get('implied_total', 0),
            reverse=True
        )

        print(f"{'Team':4} {'Total':>6} {'Opp':>6} {'Game':>6} {'Home':>5}")
        print("-" * 35)

        for team, data in sorted_teams[:20]:  # Top 20
            print(f"{team:4} {data['implied_total']:6.1f} "
                  f"{data['opponent_total']:6.1f} "
                  f"{data['game_total']:6.1f} "
                  f"{'Y' if data['is_home'] else 'N':>5}")

    def _load_from_cache(self) -> Optional[Dict]:
        """Load Vegas lines from cache if valid"""
        if not os.path.exists(self.cache_file):
            return None

        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)

            # Check if cache is still valid
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time < self.cache_duration:
                self.verbose_print("Using cached Vegas lines")
                return cache_data['lines']

        except Exception as e:
            self.verbose_print(f"Cache read error: {e}")

        return None

    def _save_to_cache(self, lines: Dict):
        """Save Vegas lines to cache"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'lines': lines
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)

        except Exception as e:
            self.verbose_print(f"Cache write error: {e}")

    def _get_fallback_lines(self) -> Dict[str, Dict]:
        """Get fallback Vegas lines when API fails"""
        # Try to load from cache even if expired
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                self.verbose_print("Using expired cache as fallback")
                return cache_data['lines']
        except:
            pass

        # Return empty dict as last resort
        self.verbose_print("No Vegas data available")
        return {}

    def _map_team_to_code(self, team_name: str) -> Optional[str]:
        """Map team name from API to standard MLB team code"""
        # Complete mapping of all variations
        mapping = {
            # National League
            "Arizona Diamondbacks": "ARI",
            "Atlanta Braves": "ATL",
            "Chicago Cubs": "CHC",
            "Cincinnati Reds": "CIN",
            "Colorado Rockies": "COL",
            "Los Angeles Dodgers": "LAD",
            "Miami Marlins": "MIA",
            "Milwaukee Brewers": "MIL",
            "New York Mets": "NYM",
            "Philadelphia Phillies": "PHI",
            "Pittsburgh Pirates": "PIT",
            "San Diego Padres": "SD",
            "San Francisco Giants": "SF",
            "St. Louis Cardinals": "STL",
            "Washington Nationals": "WSH",

            # American League
            "Baltimore Orioles": "BAL",
            "Boston Red Sox": "BOS",
            "Chicago White Sox": "CHW",
            "Cleveland Guardians": "CLE",
            "Detroit Tigers": "DET",
            "Houston Astros": "HOU",
            "Kansas City Royals": "KC",
            "Los Angeles Angels": "LAA",
            "Minnesota Twins": "MIN",
            "New York Yankees": "NYY",
            "Oakland Athletics": "OAK",
            "Seattle Mariners": "SEA",
            "Tampa Bay Rays": "TB",
            "Texas Rangers": "TEX",
            "Toronto Blue Jays": "TOR"
        }

        # Direct match
        if team_name in mapping:
            return mapping[team_name]

        # Partial match fallback
        for full_name, code in mapping.items():
            if team_name.lower() in full_name.lower() or full_name.lower() in team_name.lower():
                return code

        self.verbose_print(f"Could not map team: {team_name}")
        return None

    # DEPRECATED METHODS - Kept for backward compatibility
    def apply_to_players(self, players: List[Any]) -> List[Any]:
        """
        DEPRECATED: Use enrich_players() instead
        This method uses incorrect fixed boosts
        """
        logger.warning("DEPRECATED: apply_to_players() called - use enrich_players() instead")
        self.enrich_players(players)
        return players


# Integration function for bulletproof_dfs_core
def enrich_players_with_vegas(core_instance, players: List[Any]) -> int:
    """
    Helper function to enrich players with Vegas data
    Used by BulletproofDFSCore
    """
    if not hasattr(core_instance, 'vegas_lines') or not core_instance.vegas_lines:
        logger.warning("Vegas lines module not available")
        return 0

    return core_instance.vegas_lines.enrich_players(players)


# Example usage and testing
if __name__ == "__main__":
    # Test the module
    print("🎰 Testing Vegas Lines Module")
    print("=" * 60)

    vegas = VegasLines(verbose=True)

    # Get fresh lines
    lines = vegas.get_vegas_lines(force_refresh=True)

    if lines:
        # Show summary
        vegas.print_summary()

        # Show high/low total teams
        print(f"\n🔥 High total teams (5.0+): {vegas.get_high_total_teams()}")
        print(f"❄️  Low total teams (4.0-): {vegas.get_low_total_teams()}")

        # Test player enrichment
        from unified_player_model import UnifiedPlayer

        test_players = [
            UnifiedPlayer(
                id="1",
                name="Test Hitter",
                team="LAD",
                salary=5000,
                primary_position="OF",
                positions=["OF"],
                base_projection=10.0
            ),
            UnifiedPlayer(
                id="2",
                name="Test Pitcher",
                team="COL",
                salary=7000,
                primary_position="P",
                positions=["P"],
                base_projection=15.0
            )
        ]

        enriched = vegas.enrich_players(test_players)
        print(f"\n✅ Enriched {enriched} test players")

        for player in test_players:
            if hasattr(player, '_vegas_data'):
                print(f"\n{player.name} Vegas data:")
                print(f"  Team total: {player._vegas_data['implied_total']:.1f}")
                print(f"  Opp total: {player._vegas_data['opponent_total']:.1f}")
                print(f"  Game total: {player._vegas_data['game_total']:.1f}")
    else:
        print("❌ No Vegas lines available")