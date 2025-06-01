#!/usr/bin/env python3
# confirmed_lineups.py - New MLB DFS Confirmed Lineups Module using MLB-StatsAPI

import logging
import statsapi
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mlb_confirmed_lineups')

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


class ConfirmedLineups:
    """
    A class to fetch, parse, and manage confirmed MLB lineups and starting pitchers
    using the MLB-StatsAPI package.
    """

    def __init__(self, cache_timeout: int = 15, verbose: bool = False):
        """
        Initialize the ConfirmedLineups module.

        Args:
            cache_timeout: Minutes before cached data expires (default: 15)
            verbose: Whether to print detailed info (default: False)
        """
        self.cache_timeout = cache_timeout
        self.last_refresh_time = None
        self.lineups = {}
        self.starting_pitchers = {}

        # Set verbose mode
        set_verbose_mode(verbose)

        # Add position mapping to translate MLB API positions to DraftKings positions
        self.position_map = {
            "C": "C",
            "1B": "1B",
            "2B": "2B",
            "3B": "3B",
            "SS": "SS",
            "OF": "OF",
            "RF": "OF",
            "CF": "OF",
            "LF": "OF",
            "DH": "UTIL"
        }

        # Do initial refresh
        self.refresh_all_data()

    def debug_position_mapping(self):
        """Debug position mapping in lineups"""
        position_counts = {}

        for team, lineup in self.lineups.items():
            for player in lineup:
                pos = player['position']
                if pos not in position_counts:
                    position_counts[pos] = 0
                position_counts[pos] += 1

        verbose_print(f"Position counts in lineups: {position_counts}")

        # Print a few sample players from each position
        for pos in sorted(position_counts.keys()):
            verbose_print(f"\nSample players for position {pos}:")
            count = 0
            for team, lineup in self.lineups.items():
                for player in lineup:
                    if player['position'] == pos:
                        verbose_print(f"  {player['name']} (Team: {team})")
                        count += 1
                        if count >= 3:  # Show up to 3 examples
                            break
                if count >= 3:
                    break

    def refresh_all_data(self) -> None:
        """
        Refresh all lineup and pitcher data using MLB-StatsAPI.
        """
        logger.info("Refreshing lineup and pitcher data...")

        # Get lineups from MLB API
        mlb_lineups = self._fetch_mlb_lineups()
        for team, lineup in mlb_lineups.items():
            self.lineups[team] = lineup

        # Get starting pitchers from MLB API
        self.starting_pitchers = self._fetch_mlb_pitchers()

        # If we don't have any lineups and mock data is enabled, use mock data
        if not self.lineups and self._should_use_mock_data():
            mock_lineups = self._fetch_mock_lineups()
            for team, lineup in mock_lineups.items():
                self.lineups[team] = lineup
            verbose_print(f"Using {len(mock_lineups)} mock lineups")

        # If we don't have any pitchers and mock data is enabled, use mock data
        if not self.starting_pitchers and self._should_use_mock_data():
            self.starting_pitchers = self._fetch_mock_pitchers()
            verbose_print(f"Using {len(self.starting_pitchers)} mock pitchers")

        # Update last refresh time
        self.last_refresh_time = datetime.now()

        logger.info(
            f"Data refresh complete. Found {len(self.lineups)} lineups and {len(self.starting_pitchers)} starting pitchers.")

    def _fetch_mlb_lineups(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch lineup data from MLB API using MLB-StatsAPI package.

        Returns:
            Dictionary of lineups by team
        """
        today = datetime.now().strftime("%Y-%m-%d")
        verbose_print(f"Getting MLB lineups for {today}...")

        # Get today's schedule
        schedule = statsapi.schedule(date=today)

        if not schedule:
            verbose_print("No games scheduled for today.")
            return {}

        lineups = {}

        # Loop through each game
        for game in schedule:
            game_id = game['game_id']
            away_team = game['away_name']
            home_team = game['home_name']

            verbose_print(f"Getting lineups for {away_team} @ {home_team}...")

            # Get the game's live feed data which contains lineups
            try:
                # Use the lower-level API to get the full game data
                live_data = statsapi.get('game', {'gamePk': game_id})

                # Check if lineups are available in the live feed
                if 'liveData' in live_data and 'boxscore' in live_data['liveData']:
                    boxscore = live_data['liveData']['boxscore']

                    # Process away team lineup
                    away_lineup = []
                    # IMPORTANT: Initialize away_batting_order before using it
                    away_batting_order = []
                    if 'teams' in boxscore and 'away' in boxscore['teams'] and 'battingOrder' in boxscore['teams'][
                        'away']:
                        away_batting_order = boxscore['teams']['away']['battingOrder']
                        away_players = boxscore['teams']['away']['players']

                        for player_id in away_batting_order:
                            player_id_str = f"ID{player_id}"
                            if player_id_str in away_players:
                                player = away_players[player_id_str]
                                player_name = player['person']['fullName']
                                position = player.get('position', {}).get('abbreviation', 'Unknown')

                                # Map position to DraftKings format
                                mapped_position = self.position_map.get(position, position)

                                away_lineup.append({
                                    'name': player_name,
                                    'position': mapped_position,  # Use mapped position
                                    'order': len(away_lineup) + 1,
                                    'team': game['away_id'],
                                    'source': 'mlb-statsapi'
                                })

                    # Process home team lineup
                    home_lineup = []
                    # IMPORTANT: Initialize home_batting_order before using it
                    home_batting_order = []
                    if 'teams' in boxscore and 'home' in boxscore['teams'] and 'battingOrder' in boxscore['teams'][
                        'home']:
                        home_batting_order = boxscore['teams']['home']['battingOrder']
                        home_players = boxscore['teams']['home']['players']

                        for player_id in home_batting_order:
                            player_id_str = f"ID{player_id}"
                            if player_id_str in home_players:
                                player = home_players[player_id_str]
                                player_name = player['person']['fullName']
                                position = player.get('position', {}).get('abbreviation', 'Unknown')

                                # Map position to DraftKings format
                                mapped_position = self.position_map.get(position, position)

                                home_lineup.append({
                                    'name': player_name,
                                    'position': mapped_position,  # Use mapped position
                                    'order': len(home_lineup) + 1,
                                    'team': game['home_id'],
                                    'source': 'mlb-statsapi'
                                })

                    # Add lineups to the result dictionary
                    if away_lineup:
                        lineups[game['away_id']] = away_lineup
                        verbose_print(f"Found {len(away_lineup)} players for {away_team}")

                    if home_lineup:
                        lineups[game['home_id']] = home_lineup
                        verbose_print(f"Found {len(home_lineup)} players for {home_team}")

            except Exception as e:
                verbose_print(f"Error getting lineups for game {game_id}: {str(e)}")

        print(f"Found lineups for {len(lineups)} teams")
        return lineups

    def _fetch_mlb_pitchers(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch starting pitcher data from MLB API using MLB-StatsAPI package.

        Returns:
            Dictionary of starting pitchers by team
        """
        today = datetime.now().strftime("%Y-%m-%d")
        verbose_print(f"Getting MLB starting pitchers for {today}...")

        # Get today's schedule with probable pitchers
        schedule = statsapi.schedule(date=today)

        if not schedule:
            verbose_print("No games scheduled for today.")
            return {}

        pitchers = {}

        # Loop through each game
        for game in schedule:
            game_id = game['game_id']
            away_team = game['away_name']
            home_team = game['home_name']

            # Check for probable pitchers
            away_pitcher = game.get('away_probable_pitcher', '')
            home_pitcher = game.get('home_probable_pitcher', '')

            if away_pitcher:
                pitchers[game['away_id']] = {
                    'name': away_pitcher,
                    'team': game['away_id'],
                    'confirmed': True,
                    'source': 'mlb-statsapi'
                }
                verbose_print(f"Found starting pitcher for {away_team}: {away_pitcher}")

            if home_pitcher:
                pitchers[game['home_id']] = {
                    'name': home_pitcher,
                    'team': game['home_id'],
                    'confirmed': True,
                    'source': 'mlb-statsapi'
                }
                verbose_print(f"Found starting pitcher for {home_team}: {home_pitcher}")

        verbose_print(f"Found starting pitchers for {len(pitchers)} teams")
        return pitchers

    def _should_use_mock_data(self) -> bool:
        """Check if we should use mock data (when real sources fail)"""
        # This is a simple implementation that always returns True
        # You can modify this based on your preferences
        return True

    def _fetch_mock_lineups(self) -> Dict[str, List[Dict[str, Any]]]:
        """Mock data source for testing when real sources fail"""
        mock_lineups = {
            "WSH": [
                {"name": "CJ Abrams", "position": "SS", "order": 1, "team": "WSH", "source": "mock"},
                {"name": "Jacob Young", "position": "OF", "order": 2, "team": "WSH", "source": "mock"},
                {"name": "James Wood", "position": "OF", "order": 3, "team": "WSH", "source": "mock"},
                {"name": "Keibert Ruiz", "position": "C", "order": 4, "team": "WSH", "source": "mock"},
                {"name": "Luis Garcia", "position": "2B", "order": 5, "team": "WSH", "source": "mock"},
                {"name": "Jose Tena", "position": "3B", "order": 6, "team": "WSH", "source": "mock"},
                {"name": "Dylan Crews", "position": "OF", "order": 7, "team": "WSH", "source": "mock"},
                {"name": "Josh Bell", "position": "1B", "order": 8, "team": "WSH", "source": "mock"},
                {"name": "MacKenzie Gore", "position": "P", "order": 9, "team": "WSH", "source": "mock"}
            ],
            "TB": [
                {"name": "Yandy Diaz", "position": "1B", "order": 1, "team": "TB", "source": "mock"},
                {"name": "Brandon Lowe", "position": "2B", "order": 2, "team": "TB", "source": "mock"},
                {"name": "Josh Lowe", "position": "OF", "order": 3, "team": "TB", "source": "mock"},
                {"name": "Richie Palacios", "position": "OF", "order": 4, "team": "TB", "source": "mock"},
                {"name": "Jose Caballero", "position": "SS", "order": 5, "team": "TB", "source": "mock"},
                {"name": "Jonathan Aranda", "position": "3B", "order": 6, "team": "TB", "source": "mock"},
                {"name": "Danny Jansen", "position": "C", "order": 7, "team": "TB", "source": "mock"},
                {"name": "Kameron Misner", "position": "OF", "order": 8, "team": "TB", "source": "mock"},
                {"name": "Taylor Walls", "position": "SS", "order": 9, "team": "TB", "source": "mock"}
            ],
            "MIA": [
                {"name": "Nick Gordon", "position": "2B", "order": 1, "team": "MIA", "source": "mock"},
                {"name": "Kyle Stowers", "position": "OF", "order": 2, "team": "MIA", "source": "mock"},
                {"name": "Connor Norby", "position": "3B", "order": 3, "team": "MIA", "source": "mock"},
                {"name": "Jesus Sanchez", "position": "OF", "order": 4, "team": "MIA", "source": "mock"},
                {"name": "Dane Myers", "position": "OF", "order": 5, "team": "MIA", "source": "mock"},
                {"name": "Nick Fortes", "position": "C", "order": 6, "team": "MIA", "source": "mock"},
                {"name": "Vidal Brujan", "position": "2B", "order": 7, "team": "MIA", "source": "mock"},
                {"name": "Matt Mervis", "position": "1B", "order": 8, "team": "MIA", "source": "mock"},
                {"name": "Nasim Nunez", "position": "SS", "order": 9, "team": "MIA", "source": "mock"}
            ],
            "BAL": [
                {"name": "Gunnar Henderson", "position": "SS", "order": 1, "team": "BAL", "source": "mock"},
                {"name": "Adley Rutschman", "position": "C", "order": 2, "team": "BAL", "source": "mock"},
                {"name": "Cedric Mullins", "position": "OF", "order": 3, "team": "BAL", "source": "mock"},
                {"name": "Ryan O'Hearn", "position": "1B", "order": 4, "team": "BAL", "source": "mock"},
                {"name": "Anthony Santander", "position": "OF", "order": 5, "team": "BAL", "source": "mock"},
                {"name": "Jordan Westburg", "position": "3B", "order": 6, "team": "BAL", "source": "mock"},
                {"name": "Ryan Mountcastle", "position": "1B", "order": 7, "team": "BAL", "source": "mock"},
                {"name": "Ramon Urias", "position": "2B", "order": 8, "team": "BAL", "source": "mock"},
                {"name": "Heston Kjerstad", "position": "OF", "order": 9, "team": "BAL", "source": "mock"}
            ]
        }
        return mock_lineups

    def _fetch_mock_pitchers(self) -> Dict[str, Dict[str, Any]]:
        """Mock pitchers for testing"""
        mock_pitchers = {
            "WSH": {"name": "MacKenzie Gore", "team": "WSH", "confirmed": True, "source": "mock"},
            "TB": {"name": "Joe Boyle", "team": "TB", "confirmed": True, "source": "mock"},
            "MIA": {"name": "Ryan Weathers", "team": "MIA", "confirmed": True, "source": "mock"},
            "BAL": {"name": "Cade Povich", "team": "BAL", "confirmed": True, "source": "mock"}
        }
        return mock_pitchers

    def _is_cache_stale(self) -> bool:
        """
        Check if cached data is stale and should be refreshed.

        Returns:
            True if cache is stale, False otherwise
        """
        if self.last_refresh_time is None:
            return True

        elapsed_minutes = (datetime.now() - self.last_refresh_time).total_seconds() / 60
        return elapsed_minutes > self.cache_timeout

    def get_starting_pitchers(self, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Get all starting pitchers.

        Args:
            force_refresh: Force a refresh of pitcher data

        Returns:
            Dictionary of starting pitchers
        """
        if force_refresh or self._is_cache_stale() or not self.starting_pitchers:
            self.refresh_all_data()

        return self.starting_pitchers

    def is_player_confirmed(self, player_name: str, team: Optional[str] = None) -> Tuple[bool, Optional[int]]:
        """
        Check if a player is in a confirmed lineup.

        Args:
            player_name: Name of the player to check
            team: Optional team abbreviation

        Returns:
            Tuple of (is_confirmed, batting_order)
        """
        if self._is_cache_stale():
            self.refresh_all_data()

        # If team is provided, only check that team
        if team:
            # Try to match the team to a known team ID
            for team_id, lineup in self.lineups.items():
                # This is a simplistic approach - you may need more sophisticated team matching
                for player in lineup:
                    if self._is_name_match(player_name, player['name']):
                        return True, player['order']

        # Otherwise check all teams
        else:
            for team, lineup in self.lineups.items():
                for player in lineup:
                    if self._is_name_match(player_name, player['name']):
                        return True, player['order']

        return False, None

    def is_pitcher_starting(self, pitcher_name: str, team: Optional[str] = None) -> bool:
        """
        Check if a pitcher is confirmed to start.

        Args:
            pitcher_name: Name of the pitcher to check
            team: Optional team abbreviation

        Returns:
            Whether the pitcher is starting
        """
        if self._is_cache_stale():
            self.refresh_all_data()

        pitcher_lower = pitcher_name.lower()

        # If team is provided, only check that team
        if team:
            if team not in self.starting_pitchers:
                return False

            pitcher = self.starting_pitchers[team]
            return pitcher_lower == pitcher['name'].lower()

        # Otherwise check all teams
        else:
            for team, pitcher in self.starting_pitchers.items():
                if pitcher_lower == pitcher['name'].lower():
                    return True

        return False

    def print_diagnostic_info(self):
        """Print detailed diagnostic information about lineups and pitchers"""
        verbose_print("\n===== LINEUP DIAGNOSTIC INFORMATION =====")

        # Check lineup data
        verbose_print(f"Total teams with lineups: {len(self.lineups)}")

        # Sample some lineup data
        verbose_print("\nSample lineup data:")
        sample_count = 0
        for team, lineup in self.lineups.items():
            if sample_count >= 3:  # Show 3 teams
                break
            verbose_print(f"\nTeam {team} lineup:")
            for player in lineup:
                verbose_print(f"  {player['order']}: {player['name']} ({player['position']})")
            sample_count += 1

        # Check pitcher data
        verbose_print(f"\nTotal teams with starting pitchers: {len(self.starting_pitchers)}")

        # Sample some pitcher data
        verbose_print("\nSample pitcher data:")
        sample_count = 0
        for team, pitcher in self.starting_pitchers.items():
            if sample_count >= 5:  # Show 5 pitchers
                break
            verbose_print(f"  {team}: {pitcher['name']}")
            sample_count += 1

        verbose_print("\n========================================")

    def filter_confirmed_players(self, players: List[Dict], include_unconfirmed_pitchers: bool = True) -> List[Dict]:
        """
        Filter a list of players to only include confirmed lineup players.

        Args:
            players: List of player dictionaries
            include_unconfirmed_pitchers: Include all pitchers even if not confirmed

        Returns:
            Filtered list of players
        """
        if self._is_cache_stale():
            self.refresh_all_data()

        # Create a team mapping dictionary from numeric IDs to abbreviations
        team_mapping = {
            "121": "NYM",  # New York Mets
            "147": "NYY",  # New York Yankees
            "145": "CWS",  # Chicago White Sox
            "112": "CHC",  # Chicago Cubs
            "116": "DET",  # Detroit Tigers
            "141": "TOR",  # Toronto Blue Jays
            "120": "WSH",  # Washington Nationals
            "110": "BAL",  # Baltimore Orioles
            "139": "TB",  # Tampa Bay Rays
            "146": "MIA",  # Miami Marlins
            "134": "PIT",  # Pittsburgh Pirates
            "143": "PHI",  # Philadelphia Phillies
            "114": "CLE",  # Cleveland Guardians
            "113": "CIN",  # Cincinnati Reds
            "117": "HOU",  # Houston Astros
            "140": "TEX",  # Texas Rangers
            "138": "STL",  # St. Louis Cardinals
            "118": "KC",  # Kansas City Royals
            "144": "ATL",  # Atlanta Braves
            "111": "BOS",  # Boston Red Sox
            "142": "MIN",  # Minnesota Twins
            "158": "MIL",  # Milwaukee Brewers
            "115": "COL",  # Colorado Rockies
            "109": "ARI",  # Arizona Diamondbacks
            "136": "SEA",  # Seattle Mariners
            "135": "SD",  # San Diego Padres
            "133": "OAK",  # Oakland Athletics
            "137": "SF",  # San Francisco Giants
            "108": "LAA",  # Los Angeles Angels
            "119": "LAD",  # Los Angeles Dodgers
        }

        # Alternative team abbreviations that might be in DraftKings
        alt_abbreviations = {
            "NYM": ["NYM", "NY METS"],
            "NYY": ["NYY", "NY YANKEES"],
            "CWS": ["CWS", "CHW"],
            "CHC": ["CHC", "CHI CUBS"],
            "DET": ["DET", "DETROIT"],
            "TOR": ["TOR", "TORONTO"],
            "WSH": ["WSH", "WAS"],
            "BAL": ["BAL", "BALTIMORE"],
            "TB": ["TB", "TAM", "TBR"],
            "MIA": ["MIA", "MIAMI"],
            "PIT": ["PIT", "PITTSBURGH"],
            "PHI": ["PHI", "PHILADELPHIA"],
            "CLE": ["CLE", "CLEVELAND"],
            "CIN": ["CIN", "CINCINNATI"],
            "HOU": ["HOU", "HOUSTON"],
            "TEX": ["TEX", "TEXAS"],
            "STL": ["STL", "ST LOUIS"],
            "KC": ["KC", "KAN", "KCR"],
            "ATL": ["ATL", "ATLANTA"],
            "BOS": ["BOS", "BOSTON"],
            "MIN": ["MIN", "MINNESOTA"],
            "MIL": ["MIL", "MILWAUKEE"],
            "COL": ["COL", "COLORADO"],
            "ARI": ["ARI", "ARIZONA"],
            "SEA": ["SEA", "SEATTLE"],
            "SD": ["SD", "SDP"],
            "OAK": ["OAK", "OAKLAND"],
            "SF": ["SF", "SFG"],
            "LAA": ["LAA", "LA ANGELS"],
            "LAD": ["LAD", "LA DODGERS"],
        }

        # For debugging - print player positions
        position_counts = {}
        for player in players:
            pos = player.get('position', '')
            if pos not in position_counts:
                position_counts[pos] = 0
            position_counts[pos] += 1
        verbose_print(f"Positions before filtering: {position_counts}")

        # Print a sample of input players
        verbose_print("\nSample of input players:")
        for player in players[:5]:
            verbose_print(f"Name: {player.get('name', 'Unknown')} | Position: {player.get('position', 'Unknown')}")

        filtered_players = []

        for player in players:
            player_name = player.get('name', '')
            team = player.get('team', '')
            position = player.get('position', '')

            # Skip players without name or team
            if not player_name or not team:
                continue

            # Check if player is a pitcher
            is_pitcher = position == 'P'

            if is_pitcher:
                # Include all pitchers if specified
                if include_unconfirmed_pitchers:
                    filtered_players.append(player)
                # Otherwise only include confirmed pitchers
                elif self.is_pitcher_starting(player_name, None):  # Ignore team matching for pitchers
                    filtered_players.append(player)
            else:
                # For non-pitchers, check ALL lineups without team filtering
                is_confirmed = False

                for lineup_team, lineup in self.lineups.items():
                    for lineup_player in lineup:
                        # Fuzzy name matching to be more flexible
                        if self._is_name_match(player_name, lineup_player['name']):
                            # Debug output on match
                            print(
                                f"Matched {player_name} ({position}) to {lineup_player['name']} ({lineup_player['position']}) for team {lineup_team}")
                            # Check that the positions match
                            if lineup_player['position'] == position:
                                is_confirmed = True
                                filtered_players.append(player)
                                break
                    if is_confirmed:
                        break

        # For debugging - print positions after filtering
        position_counts_after = {}
        for player in filtered_players:
            pos = player.get('position', '')
            if pos not in position_counts_after:
                position_counts_after[pos] = 0
            position_counts_after[pos] += 1
        verbose_print(f"Positions after filtering: {position_counts_after}")

        return filtered_players

    def _is_name_match(self, name1, name2):
        """
        More flexible name matching between DraftKings and MLB API names.

        Args:
            name1: First name to compare
            name2: Second name to compare

        Returns:
            True if names match, False otherwise
        """
        # Convert to lowercase and strip spaces
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()

        # Exact match
        if name1 == name2:
            return True

        # Handle common name variations
        name1_parts = name1.split()
        name2_parts = name2.split()

        # If different number of parts, check if last names match
        if len(name1_parts) > 0 and len(name2_parts) > 0:
            # Check if last names match
            if name1_parts[-1] == name2_parts[-1]:
                # If last names match, check if first initials match
                if len(name1_parts[0]) > 0 and len(name2_parts[0]) > 0:
                    if name1_parts[0][0] == name2_parts[0][0]:
                        return True

        # Check for substring matches (if one name is contained in the other)
        if len(name1) > 3 and len(name2) > 3:
            if name1 in name2 or name2 in name1:
                return True

        return False

    def print_all_lineups(self) -> None:
        """
        Print all confirmed lineups and pitchers to the console.
        """
        if self._is_cache_stale():
            self.refresh_all_data()

        verbose_print("\n=== CONFIRMED LINEUPS ===")
        for team, lineup in sorted(self.lineups.items()):
            verbose_print(f"\n{team} Lineup:")
            for player in lineup:
                verbose_print(f"  {player['order']}. {player['name']} ({player['position']})")

        verbose_print("\n=== STARTING PITCHERS ===")
        for team, pitcher in sorted(self.starting_pitchers.items()):
            status = "CONFIRMED" if pitcher.get('confirmed', False) else "PROBABLE"
            verbose_print(f"{team}: {pitcher['name']} ({status})")


# Add support for direct command-line usage
if __name__ == "__main__":
    # Create the lineups object
    lineups = ConfirmedLineups()

    # Print all lineups and pitchers
    lineups.print_all_lineups()