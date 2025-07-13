#!/usr/bin/env python3
# vegas_lines.py - Enhanced version with better cache validation but no mock data

import json
import os
from datetime import datetime

import requests

# Initialize module-level variable for verbosity
VERBOSE_MODE = False


def set_verbose_mode(verbose=False):
    """Set verbose mode for the module"""
    global VERBOSE_MODE
    VERBOSE_MODE = verbose


def verbose_print(message):
    """Print message only in verbose mode"""
    global VERBOSE_MODE
    if VERBOSE_MODE:
        print(message)


class VegasLines:
    """Class for fetching and applying Vegas lines to MLB DFS projections"""

    def __init__(self, cache_dir="data/vegas", verbose=False):
        """Initialize the Vegas lines module"""
        self.cache_dir = cache_dir
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.cache_expiry = 2  # Hours - lines change frequently
        self.lines = {}
        self.api_key = "14b669db87ed65f1d0f3e70a90386707"  # Your API key

        # Set verbose mode
        set_verbose_mode(verbose)

        # Print debug info if verbose
        verbose_print(f"Vegas Lines initialized with cache dir: {cache_dir}")
        verbose_print(f"Today's date: {self.today}")

        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_vegas_lines(self, force_refresh=False):
        """
        Get Vegas lines data for today's MLB games.

        Args:
            force_refresh: If True, force refresh from API (default: False)

        Returns:
            Dictionary of Vegas lines data by team
        """
        # Check if we have cached lines data that's not stale
        cache_file = os.path.join(self.cache_dir, f"vegas_lines_{self.today}.json")

        if not force_refresh and os.path.exists(cache_file):
            # Check if file is stale
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            cache_age_hours = (datetime.now() - file_time).total_seconds() / 3600

            if cache_age_hours < self.cache_expiry:
                try:
                    verbose_print(f"Loading Vegas lines from cache: {cache_file}")
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)

                    # Validate the cache data has the expected structure
                    if cache_data and isinstance(cache_data, dict) and len(cache_data) > 0:
                        self.lines = cache_data
                        verbose_print(f"Successfully loaded Vegas lines for {len(self.lines)} teams from cache")
                        print(f"Vegas data loaded successfully!")
                        return self.lines
                    else:
                        verbose_print("Cache file exists but contains invalid data. Will try API.")
                except Exception as e:
                    verbose_print(f"Error reading Vegas lines cache: {str(e)}")
                    # Continue to fetch fresh data
            else:
                verbose_print(f"Cache is {cache_age_hours:.1f} hours old (expiry: {self.cache_expiry}h). Will refresh.")

        # Fetch fresh data
        verbose_print("Fetching Vegas lines from The Odds API...")

        url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'totals',
            'oddsFormat': 'american',
            'dateFormat': 'iso'
        }

        try:
            verbose_print(f"Making API request to: {url}")
            response = requests.get(url, params=params, timeout=10)  # Add timeout

            # Check for HTTP errors
            response.raise_for_status()

            data = response.json()

            # Verify we got valid data
            if not data or not isinstance(data, list) or len(data) == 0:
                verbose_print(f"API returned empty or invalid data: {data}")
                print("No Vegas lines data available from API. Skipping Vegas adjustments.")
                return {}

            # Process the data to extract the lines by team
            self.lines = self._process_odds_data(data)

            if not self.lines:
                verbose_print("Failed to process odds data")
                print("Failed to process Vegas odds data. Skipping Vegas adjustments.")
                return {}

            # Save to cache
            with open(cache_file, 'w') as f:
                json.dump(self.lines, f)

            verbose_print(f"Saved Vegas lines to cache: {cache_file}")
            print(f"Vegas data loaded successfully!")
            return self.lines

        except Exception as e:
            verbose_print(f"Error fetching Vegas lines: {str(e)}")
            print("Failed to fetch Vegas odds data. Skipping Vegas adjustments.")
            return {}

    def _process_odds_data(self, data):
        """
        Process odds data from The Odds API into a more usable format.

        Args:
            data: JSON data from The Odds API

        Returns:
            Dictionary of Vegas lines data by team
        """
        processed = {}
        total_games = len(data)
        verbose_print(f"Processing odds data for {total_games} games")

        for game_idx, game in enumerate(data):
            try:
                # Get game info
                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')

                verbose_print(f"Processing game {game_idx + 1}/{total_games}: {away_team} @ {home_team}")

                # Skip if missing teams
                if not home_team or not away_team:
                    verbose_print(f"  Skipping game with missing team info: {game}")
                    continue

                # Find totals in bookmakers data
                total = None
                bookmakers = game.get('bookmakers', [])

                if not bookmakers:
                    verbose_print(f"  No bookmakers data for {away_team} @ {home_team}")
                    continue

                # Try to find totals from multiple bookmakers - prefer DraftKings
                for bookmaker in bookmakers:
                    bookmaker_key = bookmaker.get('key', '')
                    markets = bookmaker.get('markets', [])

                    for market in markets:
                        if market.get('key') == 'totals':
                            outcomes = market.get('outcomes', [])

                            # Get total from first outcome (over/under are same number)
                            if outcomes and len(outcomes) > 0:
                                points = outcomes[0].get('point')
                                if points is not None:
                                    total = float(points)
                                    verbose_print(f"  Found total {total} from {bookmaker_key}")
                                    break

                    # If we found a total, no need to check more bookmakers
                    if total is not None:
                        break

                # Skip if we couldn't find a total
                if total is None:
                    verbose_print(f"  No total found for {away_team} @ {home_team}")
                    continue

                # Map team names to MLB team codes
                home_code = self._map_team_to_code(home_team)
                away_code = self._map_team_to_code(away_team)

                verbose_print(f"  Mapped teams: {home_team} -> {home_code}, {away_team} -> {away_code}")

                if not home_code or not away_code:
                    verbose_print(f"  Couldn't map one or both teams to codes")
                    continue

                # Calculate implied team totals (simple 50/50 split for now)
                # In a real implementation, this would use the money line to calculate
                # more accurate implied totals
                home_implied = total / 2
                away_implied = total / 2

                # Add home team data
                processed[home_code] = {
                    'team': home_code,
                    'opponent': away_code,
                    'total': total,
                    'team_total': home_implied,
                    'opponent_total': away_implied,
                    'is_favorite': True,  # Default assumption
                    'is_home': True
                }

                # Add away team data
                processed[away_code] = {
                    'team': away_code,
                    'opponent': home_code,
                    'total': total,
                    'team_total': away_implied,
                    'opponent_total': home_implied,
                    'is_favorite': False,  # Default assumption
                    'is_home': False
                }

                verbose_print(f"  Successfully processed game data")

            except Exception as e:
                verbose_print(f"Error processing game data: {str(e)}")
                continue

        verbose_print(f"Processed Vegas lines for {len(processed)} teams")
        return processed

    def _map_team_to_code(self, team_name):
        """
        Map team name from API to standard MLB team code.

        Args:
            team_name: Team name from API

        Returns:
            MLB team code (3-letter abbreviation)
        """
        # This mapping handles various team name formats
        mapping = {
            "Arizona Diamondbacks": "ARI",
            "Arizona": "ARI",
            "Diamondbacks": "ARI",

            "Atlanta Braves": "ATL",
            "Atlanta": "ATL",
            "Braves": "ATL",

            "Baltimore Orioles": "BAL",
            "Baltimore": "BAL",
            "Orioles": "BAL",

            "Boston Red Sox": "BOS",
            "Boston": "BOS",
            "Red Sox": "BOS",

            "Chicago Cubs": "CHC",
            "Cubs": "CHC",

            "Chicago White Sox": "CWS",
            "White Sox": "CWS",

            "Cincinnati Reds": "CIN",
            "Cincinnati": "CIN",
            "Reds": "CIN",

            "Cleveland Guardians": "CLE",
            "Cleveland": "CLE",
            "Guardians": "CLE",

            "Colorado Rockies": "COL",
            "Colorado": "COL",
            "Rockies": "COL",

            "Detroit Tigers": "DET",
            "Detroit": "DET",
            "Tigers": "DET",

            "Houston Astros": "HOU",
            "Houston": "HOU",
            "Astros": "HOU",

            "Kansas City Royals": "KC",
            "Kansas City": "KC",
            "Royals": "KC",

            "Los Angeles Angels": "LAA",
            "LA Angels": "LAA",
            "Angels": "LAA",

            "Los Angeles Dodgers": "LAD",
            "LA Dodgers": "LAD",
            "Dodgers": "LAD",

            "Miami Marlins": "MIA",
            "Miami": "MIA",
            "Marlins": "MIA",

            "Milwaukee Brewers": "MIL",
            "Milwaukee": "MIL",
            "Brewers": "MIL",

            "Minnesota Twins": "MIN",
            "Minnesota": "MIN",
            "Twins": "MIN",

            "New York Mets": "NYM",
            "NY Mets": "NYM",
            "Mets": "NYM",

            "New York Yankees": "NYY",
            "NY Yankees": "NYY",
            "Yankees": "NYY",

            "Oakland Athletics": "OAK",
            "Oakland": "OAK",
            "Athletics": "OAK",
            "A's": "OAK",

            "Philadelphia Phillies": "PHI",
            "Philadelphia": "PHI",
            "Phillies": "PHI",

            "Pittsburgh Pirates": "PIT",
            "Pittsburgh": "PIT",
            "Pirates": "PIT",

            "San Diego Padres": "SD",
            "San Diego": "SD",
            "Padres": "SD",

            "San Francisco Giants": "SF",
            "San Francisco": "SF",
            "Giants": "SF",

            "Seattle Mariners": "SEA",
            "Seattle": "SEA",
            "Mariners": "SEA",

            "St. Louis Cardinals": "STL",
            "Saint Louis Cardinals": "STL",
            "St Louis Cardinals": "STL",
            "St. Louis": "STL",
            "St Louis": "STL",
            "Cardinals": "STL",

            "Tampa Bay Rays": "TB",
            "Tampa Bay": "TB",
            "Rays": "TB",

            "Texas Rangers": "TEX",
            "Texas": "TEX",
            "Rangers": "TEX",

            "Toronto Blue Jays": "TOR",
            "Toronto": "TOR",
            "Blue Jays": "TOR",

            "Washington Nationals": "WSH",
            "Washington": "WSH",
            "Nationals": "WSH"
        }

        # Direct match
        if team_name in mapping:
            return mapping[team_name]

        # Case-insensitive exact match
        for full_name, code in mapping.items():
            if full_name.lower() == team_name.lower():
                return code

        # Partial match
        for full_name, code in mapping.items():
            if full_name.lower() in team_name.lower() or team_name.lower() in full_name.lower():
                return code

        verbose_print(f"Couldn't map team name: {team_name}")
        return None

    def apply_to_players(self, players):
        """
        Apply Vegas line adjustments to player projections.

        Args:
            players: List of player objects (AdvancedPlayer instances)

        Returns:
            Updated player list with Vegas adjustments
        """
        if not self.lines:
            # Try to get lines if we don't have them yet
            self.get_vegas_lines()

        if not self.lines:
            print("No Vegas lines data available. Skipping Vegas adjustments.")
            return players

        adjusted_count = 0

        for player in players:
            try:
                # Handle AdvancedPlayer objects
                if hasattr(player, 'team'):  # It's an object
                    team = player.team
                    player_name = player.name
                    position = player.primary_position
                else:  # Legacy list/tuple format
                    team = player[3]
                    player_name = player[1]
                    position = player[2]

                if not team or team not in self.lines:
                    continue

                team_data = self.lines[team]
                team_implied = team_data.get('team_total', 0)
                opp_implied = team_data.get('opponent_total', 0)

                # Apply Vegas boosts/penalties
                boost = 0.0
                if position != 'P':  # Batter
                    if team_implied >= 5.0:
                        boost = 2.0
                    elif team_implied >= 4.5:
                        boost = 1.0
                    elif team_implied <= 3.5:
                        boost = -1.0
                else:  # Pitcher
                    if opp_implied <= 3.5:
                        boost = 2.0
                    elif opp_implied <= 4.0:
                        boost = 1.0
                    elif opp_implied >= 5.0:
                        boost = -1.0

                # Apply boost
                if boost != 0.0 and hasattr(player, 'enhanced_score'):
                    old_score = player.enhanced_score
                    player.enhanced_score += boost
                    adjusted_count += 1
                    verbose_print(f"Vegas adjustment for {player_name}: {boost:+.1f}")

                # Add Vegas data to player
                if hasattr(player, 'apply_vegas_data'):
                    vegas_info = {
                        "team_total": team_implied,
                        "opponent_total": opp_implied,
                        "total": team_data.get('total', 0),
                        "is_home": team_data.get('is_home', False)
                    }
                    player.apply_vegas_data(vegas_info)

            except Exception as e:
                verbose_print(
                    f"Error applying Vegas data to {player_name if 'player_name' in locals() else 'unknown'}: {str(e)}")
                continue

        if adjusted_count > 0:
            print(f"Applied Vegas lines adjustments to {adjusted_count} players")

        return players

# Direct usage example
if __name__ == "__main__":
    # Test the class
    vegas = VegasLines(verbose=True)
    lines = vegas.get_vegas_lines(force_refresh=True)

    # Print the lines
    if lines:
        print("\nVegas Lines:")
        for team, data in sorted(lines.items()):
            print(
                f"{team}: Total {data['total']}, Team Total: {data['team_total']:.1f}, Opp Total: {data['opponent_total']:.1f}")
    else:
        print("\nNo Vegas lines available")