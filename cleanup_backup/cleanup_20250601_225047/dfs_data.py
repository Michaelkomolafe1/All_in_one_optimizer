"""
dfs_data.py - DFS data management and processing
Handles loading and processing of DraftKings data and advanced metrics
"""
import os
import csv
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import glob


# Part 2 of DFSData class - Enhanced scoring system and data visualization

# Part 1: First half of DFSData class

class DFSData:
    def __init__(self):
        # Existing attributes
        self.hitter_metrics = {}
        self.pitcher_metrics = {}
        self.opponent_map = {}
        self.team_implied_totals = {}

        # New data structures for enhanced scoring
        self.team_handedness = {}  # Percentage of lefty batters in each team
        self.team_is_home = {}  # Boolean of whether each team is home or away
        self.team_pitcher = {}  # Dictionary mapping teams to their starting pitcher
        self.park_factors = {}  # Park factors for each stadium

        # Tracking flags for data sources
        self.has_statcast_data = False
        self.has_vegas_data = False

    def import_from_draftkings(self, file_path):
        """
        Import player data from a DraftKings CSV export
        """
        try:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False

            print(f"Importing data from DraftKings file: {file_path}")

            # List to store player data
            players = []
            team_games = {}

            # Add a position mapping to standardize positions
            position_map = {
                "SP": "P",
                "RP": "P"
            }

            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Skip header row

                # Find indices of relevant columns
                name_idx = headers.index('Name') if 'Name' in headers else 0
                position_idx = headers.index('Position') if 'Position' in headers else 1
                team_idx = headers.index('TeamAbbrev') if 'TeamAbbrev' in headers else 5
                salary_idx = headers.index('Salary') if 'Salary' in headers else 2

                # Try to find fantasy points projection column (different versions use different names)
                fpts_idx = None
                for possibility in ['AvgPointsPerGame', 'FPPG', 'Projection']:
                    if possibility in headers:
                        fpts_idx = headers.index(possibility)
                        break

                for row in reader:
                    if len(row) <= max(name_idx, position_idx, team_idx, salary_idx):
                        continue

                    # Extract player info
                    player_id = len(players) + 1  # Generate an ID
                    name = row[name_idx]
                    position = row[position_idx]

                    # Normalize position
                    if position in position_map:
                        position = position_map[position]

                    team = row[team_idx]

                    # Convert salary from string "$5,500" to integer 5500
                    salary_str = row[salary_idx].replace('$', '').replace(',', '')
                    salary = int(salary_str) if salary_str.isdigit() else 0

                    # Get projected points if available
                    proj_pts = 0.0
                    if fpts_idx is not None and fpts_idx < len(row):
                        try:
                            proj_pts = float(row[fpts_idx])
                        except (ValueError, TypeError):
                            pass

                    # Calculate a basic score for players without advanced metrics
                    # Make sure it's a valid number and not None
                    if proj_pts and proj_pts > 0:
                        score = float(proj_pts)  # Use projection if available
                    elif salary > 0:
                        score = salary / 1000.0  # Use salary-based default
                    else:
                        score = 5.0  # Fallback default score

                    # Create basic player data structure
                    # [id, name, position, team, salary, proj_pts, score, batting_order]
                    player_data = [
                        player_id,
                        name,
                        position,
                        team,
                        salary,
                        proj_pts,
                        score,
                        None  # batting_order (will be filled in later if available)
                    ]

                    # Add to players list
                    players.append(player_data)

                    # Track games
                    if team not in team_games:
                        team_games[team] = True

            print(f"Imported {len(players)} players from {len(team_games)} teams")

            # Store players in instance for further processing
            self.players = players

            return True

        except Exception as e:
            print(f"Error importing DraftKings data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def find_dk_files(self, directory="data"):
        """
        Find DraftKings CSV files in the data directory

        Args:
            directory: Directory to search in

        Returns:
            List of file paths
        """
        # Default to current directory if data dir doesn't exist
        if not os.path.exists(directory):
            directory = "."

        dk_files = []

        # Common filenames for DraftKings exports
        dk_patterns = [
            "DKSalaries*.csv",
            "*dksalaries*.csv",
            "*draftkings*.csv"
        ]

        # Find all matching files
        for pattern in dk_patterns:
            import glob
            dk_files.extend(glob.glob(os.path.join(directory, pattern)))
            dk_files.extend(glob.glob(os.path.join(".", pattern)))  # Also check current directory

        return dk_files

    def generate_enhanced_player_data(self, force_refresh=False):
        """
        Generate enhanced player data with Statcast metrics
        """
        if not hasattr(self, 'players') or not self.players:
            print("No player data loaded. Call import_from_draftkings first.")
            return []

        # Before enriching, normalize all pitcher positions to "P"
        for player in self.players:
            if player[2] in ["SP", "RP"]:
                player[2] = "P"

        # If we have Statcast integration, use it to enrich player data
        if hasattr(self, 'statcast') and self.statcast:
            print("Using Statcast integration to enrich player data...")
            # Set force refresh flag if specified
            if force_refresh:
                self.statcast.set_force_refresh(force_refresh)

            # Enrich player data with Statcast metrics
            enriched_players = self.statcast.enrich_player_data(self.players, force_refresh)

            # Validate and fix scores
            for player in enriched_players:
                # Ensure player has a valid score
                if player[6] is None or not isinstance(player[6], (int, float)):
                    # If there's a projection, use that
                    if player[5] and isinstance(player[5], (int, float)) and player[5] > 0:
                        player[6] = float(player[5])
                    # Otherwise use salary-based score
                    elif player[4] and isinstance(player[4], (int, float)) and player[4] > 0:
                        player[6] = player[4] / 1000.0
                    else:
                        # Last resort - give a default score based on position
                        if player[2] == "P":
                            player[6] = 10.0  # Default pitcher score
                        else:
                            player[6] = 5.0  # Default batter score

            # Initialize player metrics from the enriched data
            self.initialize_player_data(enriched_players)

            return enriched_players
        else:
            print("No Statcast integration available. Using basic player data.")
            # Ensure all players have valid scores
            for player in self.players:
                if player[6] is None or not isinstance(player[6], (int, float)):
                    # If no valid score, calculate one
                    if player[5] and isinstance(player[5], (int, float)) and player[5] > 0:
                        player[6] = float(player[5])
                    elif player[4] and isinstance(player[4], (int, float)) and player[4] > 0:
                        player[6] = player[4] / 1000.0
                    else:
                        player[6] = 5.0  # Default score

            return self.players

    def initialize_player_data(self, players_data):
        """
        Initialize player metrics data from raw player data
        """
        self.hitter_metrics = {}
        self.pitcher_metrics = {}

        # Count metrics for debugging
        pitcher_count = 0
        hitter_count = 0

        for player in players_data:
            player_name = player[1]  # Index 1 is player name based on your output
            position = player[2]  # Index 2 is position

            # Normalize pitcher positions
            is_pitcher = position in ["P", "SP", "RP"]

            # Extract Statcast data from the player data
            # Check both index 14 and 15 (different versions might use different indices)
            statcast_data = None
            if len(player) > 15 and isinstance(player[15], dict):
                statcast_data = player[15]
            elif len(player) > 14 and isinstance(player[14], dict):
                statcast_data = player[14]

            if statcast_data:
                self.has_statcast_data = True  # Set flag if any player has Statcast data

                # For pitchers
                if is_pitcher:
                    self.pitcher_metrics[player_name] = {
                        "xwOBA": statcast_data.get("xwOBA", 0.0),
                        "K": statcast_data.get("swinging_strike_rate", 0.0),
                        "Hard_Hit": statcast_data.get("hard_hit_rate", 0.0),
                        "Whiff": statcast_data.get("swinging_strike_rate", 0.0),
                        "avg_velocity": statcast_data.get("avg_velocity", 0.0),
                        "hand": "R"  # Default to right-handed if not specified
                    }

                    # Add handedness if available
                    if "handedness" in statcast_data:
                        self.pitcher_metrics[player_name]["hand"] = statcast_data["handedness"]

                    # Add splits data if available
                    if "xwOBA_vs_LHB" in statcast_data and "xwOBA_vs_RHB" in statcast_data:
                        self.pitcher_metrics[player_name]["vs_LHB"] = {"wOBA": statcast_data["xwOBA_vs_LHB"]}
                        self.pitcher_metrics[player_name]["vs_RHB"] = {"wOBA": statcast_data["xwOBA_vs_RHB"]}

                    pitcher_count += 1

                # For hitters
                else:
                    self.hitter_metrics[player_name] = {
                        "xwOBA": statcast_data.get("xwOBA", 0.0),
                        "K": statcast_data.get("chase_rate", 0.0),  # Using chase rate as K% if available
                        "BB": statcast_data.get("walk_rate", 0.0),
                        "Hard_Hit": statcast_data.get("hard_hit_rate", 0.0),
                        "Barrel": statcast_data.get("barrel_rate", 0.0),
                        "Pull": statcast_data.get("pull_rate", 0.0),
                        "avg_exit_velocity": statcast_data.get("avg_exit_velocity", 0.0),
                        "hand": "R"  # Default to right-handed if not specified
                    }

                    # Add handedness if available
                    if "handedness" in statcast_data:
                        self.hitter_metrics[player_name]["hand"] = statcast_data["handedness"]
                    elif "hand" in statcast_data:
                        self.hitter_metrics[player_name]["hand"] = statcast_data["hand"]

                    hitter_count += 1

            # If we don't have Statcast data, create basic entries
            else:
                # For pitchers without Statcast data, use basic data from other indexes
                if is_pitcher:
                    self.pitcher_metrics[player_name] = {
                        "xwOBA": player[8] if len(player) > 8 and isinstance(player[8], (int, float)) else 0.320,
                        "K": player[9] if len(player) > 9 and isinstance(player[9], (int, float)) else 0.200,
                        "Hard_Hit": player[13] if len(player) > 13 and isinstance(player[13], (int, float)) else 0.350,
                        "hand": "R"  # Default to right-handed
                    }
                    pitcher_count += 1

                # For hitters without Statcast data
                else:
                    self.hitter_metrics[player_name] = {
                        "xwOBA": player[8] if len(player) > 8 and isinstance(player[8], (int, float)) else 0.320,
                        "Hard_Hit": player[9] if len(player) > 9 and isinstance(player[9], (int, float)) else 0.350,
                        "Barrel": player[10] if len(player) > 10 and isinstance(player[10], (int, float)) else 0.060,
                        "hand": "R"  # Default to right-handed
                    }
                    hitter_count += 1

        print(f"Processed metrics for {pitcher_count} pitchers and {hitter_count} hitters")
    def load_vegas_data(self, vegas_data=None):
        """
        Load vegas lines data - either from provided data or using default estimates
        """
        if vegas_data:
            try:
                self.team_implied_totals = {}
                for team_data in vegas_data:
                    team = team_data.get('team')
                    implied_total = team_data.get('implied_total', 0.0)
                    if team and implied_total:
                        self.team_implied_totals[team] = float(implied_total)

                if self.team_implied_totals:
                    self.has_vegas_data = True
                    print(f"Loaded Vegas implied totals for {len(self.team_implied_totals)} teams")
                else:
                    print("Warning: Vegas data was provided but no implied totals were found")
                    self._generate_default_implied_totals()
            except Exception as e:
                print(f"Error loading Vegas data: {e}")
                self._generate_default_implied_totals()
        else:
            self._generate_default_implied_totals()

    def _generate_default_implied_totals(self):
        """Generate default implied totals for all teams in the opponent map"""
        # Only generate if we don't already have data
        if not self.team_implied_totals:
            # Default to league average (4.5 runs) with slight variation
            import random

            # Get all unique teams from opponent map
            all_teams = set(list(self.opponent_map.keys()) + list(self.opponent_map.values()))

            # Generate reasonable implied totals
            self.team_implied_totals = {
                team: round(random.uniform(4.0, 5.0), 1) for team in all_teams
            }

            # If we have any pitcher metrics, adjust implied totals based on pitcher quality
            for team, pitcher in self.team_pitcher.items():
                if pitcher in self.pitcher_metrics:
                    opponent = self.opponent_map.get(team)
                    if opponent:
                        # Better pitchers (lower xwOBA) lead to lower implied totals for opponents
                        pitcher_xwoba = self.pitcher_metrics[pitcher].get("xwOBA", 0.320)

                        # Adjust implied total based on pitcher quality
                        if pitcher_xwoba < 0.290:  # Excellent pitcher
                            self.team_implied_totals[opponent] = round(
                                max(3.2, self.team_implied_totals.get(opponent, 4.5) - 0.8), 1)
                        elif pitcher_xwoba < 0.320:  # Good pitcher
                            self.team_implied_totals[opponent] = round(
                                max(3.5, self.team_implied_totals.get(opponent, 4.5) - 0.5), 1)
                        elif pitcher_xwoba > 0.360:  # Poor pitcher
                            self.team_implied_totals[opponent] = round(
                                min(5.8, self.team_implied_totals.get(opponent, 4.5) + 0.8), 1)
                        elif pitcher_xwoba > 0.340:  # Below average pitcher
                            self.team_implied_totals[opponent] = round(
                                min(5.3, self.team_implied_totals.get(opponent, 4.5) + 0.5), 1)

            print("Generated default implied totals for all teams")
            self.has_vegas_data = True  # We now have (estimated) Vegas data

    # Part 2: Second half of DFSData class

    def load_park_factors(self, file_path=None):
        """
        Load park factors from CSV file or use default values
        Format: TeamID, overall, hr, 1b, 2b, 3b, left_field, center_field, right_field
        """
        # Default park factors if file not available
        default_factors = {
            "LAA": {"overall": 102, "hr": 104, "left_field": 101, "center_field": 100, "right_field": 108},
            "HOU": {"overall": 103, "hr": 112, "left_field": 95, "center_field": 102, "right_field": 115},
            "TOR": {"overall": 106, "hr": 115, "left_field": 110, "center_field": 102, "right_field": 112},
            "BOS": {"overall": 108, "hr": 105, "left_field": 120, "center_field": 95, "right_field": 98},
            "NYY": {"overall": 104, "hr": 118, "left_field": 95, "center_field": 100, "right_field": 120},
            "CHC": {"overall": 103, "hr": 106, "left_field": 105, "center_field": 98, "right_field": 110},
            "COL": {"overall": 115, "hr": 117, "left_field": 113, "center_field": 110, "right_field": 113},
            "CIN": {"overall": 106, "hr": 114, "left_field": 105, "center_field": 103, "right_field": 108},
            "MIL": {"overall": 103, "hr": 110, "left_field": 102, "center_field": 101, "right_field": 105},
            "PHI": {"overall": 105, "hr": 109, "left_field": 101, "center_field": 100, "right_field": 107},
            "ATL": {"overall": 101, "hr": 103, "left_field": 100, "center_field": 99, "right_field": 102},
            "TEX": {"overall": 101, "hr": 105, "left_field": 104, "center_field": 97, "right_field": 103},
            "SF": {"overall": 95, "hr": 92, "left_field": 97, "center_field": 95, "right_field": 93},
            "SEA": {"overall": 96, "hr": 93, "left_field": 95, "center_field": 98, "right_field": 97},
            "DET": {"overall": 97, "hr": 94, "left_field": 98, "center_field": 99, "right_field": 95},
            "SD": {"overall": 95, "hr": 89, "left_field": 97, "center_field": 100, "right_field": 94},
            "OAK": {"overall": 94, "hr": 90, "left_field": 96, "center_field": 98, "right_field": 92},
            "MIA": {"overall": 93, "hr": 89, "left_field": 95, "center_field": 97, "right_field": 93},
            "TB": {"overall": 98, "hr": 96, "left_field": 99, "center_field": 100, "right_field": 97},
            "WSH": {"overall": 100, "hr": 99, "left_field": 101, "center_field": 98, "right_field": 100},
            "BAL": {"overall": 101, "hr": 111, "left_field": 95, "center_field": 97, "right_field": 107},
            "CLE": {"overall": 99, "hr": 96, "left_field": 100, "center_field": 99, "right_field": 98},
            "STL": {"overall": 98, "hr": 95, "left_field": 99, "center_field": 100, "right_field": 97},
            "KC": {"overall": 98, "hr": 92, "left_field": 100, "center_field": 103, "right_field": 95},
            "PIT": {"overall": 97, "hr": 95, "left_field": 99, "center_field": 97, "right_field": 96},
            "LAD": {"overall": 101, "hr": 102, "left_field": 100, "center_field": 99, "right_field": 103},
            "MIN": {"overall": 100, "hr": 101, "left_field": 99, "center_field": 100, "right_field": 101},
            "CWS": {"overall": 104, "hr": 112, "left_field": 102, "center_field": 98, "right_field": 108},
            "ARI": {"overall": 102, "hr": 105, "left_field": 101, "center_field": 100, "right_field": 103},
            "NYM": {"overall": 97, "hr": 92, "left_field": 98, "center_field": 101, "right_field": 95}
        }

        if file_path:
            try:
                import csv
                with open(file_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        team_id = row['team']
                        self.park_factors[team_id] = {
                            "overall": float(row.get('overall', 100)),
                            "hr": float(row.get('hr', 100)),
                            "left_field": float(row.get('left_field', 100)),
                            "center_field": float(row.get('center_field', 100)),
                            "right_field": float(row.get('right_field', 100))
                        }
                print(f"Loaded park factors from {file_path}")
            except Exception as e:
                print(f"Error loading park factors: {e}")
                print("Using default park factors")
                self.park_factors = default_factors
        else:
            print("Using default park factors")
            self.park_factors = default_factors

    def set_game_info(self, games_data):
        """
        Set home/away status and opponent mappings from games data
        Format expected: List of dictionaries with {home_team, away_team} keys
        """
        self.team_is_home = {}
        self.opponent_map = {}

        for game in games_data:
            home_team = game.get('home_team')
            away_team = game.get('away_team')

            if home_team and away_team:
                # Set home/away status
                self.team_is_home[home_team] = True
                self.team_is_home[away_team] = False

                # Set opponent mapping
                self.opponent_map[home_team] = away_team
                self.opponent_map[away_team] = home_team

        print(f"Set up game info for {len(games_data)} games")

    def load_team_handedness(self, file_path=None):
        """
        Load team handedness data from CSV file or use default values
        Format: TeamID, left_pct, switch_pct
        """
        # Default values (league average is around 33% LHB)
        default_handedness = {team: {"left_pct": 0.33, "switch_pct": 0.10} for team in self.opponent_map.keys()}

        # Teams with notably more left-handed batters
        lhb_heavy_teams = ["CLE", "SEA", "LAD", "TEX", "SF"]
        for team in lhb_heavy_teams:
            if team in default_handedness:
                default_handedness[team]["left_pct"] = 0.45

        if file_path:
            try:
                import csv
                with open(file_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        team_id = row['team']
                        self.team_handedness[team_id] = {
                            "left_pct": float(row.get('left_pct', 0.33)),
                            "switch_pct": float(row.get('switch_pct', 0.10))
                        }
                print(f"Loaded team handedness from {file_path}")
            except Exception as e:
                print(f"Error loading team handedness: {e}")
                print("Using default team handedness data")
                self.team_handedness = default_handedness
        else:
            print("Using default team handedness data")
            self.team_handedness = default_handedness

    def set_starting_pitchers(self, pitchers_data):
        """
        Set starting pitchers for each team
        Format expected: List of dictionaries with {team, pitcher_name} keys
        """
        self.team_pitcher = {}

        for entry in pitchers_data:
            team = entry.get('team')
            pitcher = entry.get('pitcher_name')

            if team and pitcher:
                self.team_pitcher[team] = pitcher

        print(f"Set starting pitchers for {len(self.team_pitcher)} teams")

    def add_recent_performance_data(self, recent_stats_file=None):
        """
        Add recent performance metrics to player data
        For both pitchers and hitters, add recent_xwOBA and recent_sample_size
        """
        if not recent_stats_file:
            print("No recent stats file provided, skipping recent performance data")
            return

        try:
            import csv
            with open(recent_stats_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    player_name = row.get('Name')
                    position_type = row.get('Type', 'B')  # B for batter, P for pitcher
                    recent_xwoba = float(row.get('recent_xwOBA', 0))
                    sample_size = int(row.get('recent_PA', 0))

                    if position_type == 'P' and player_name in self.pitcher_metrics:
                        self.pitcher_metrics[player_name]['recent_xwOBA'] = recent_xwoba
                        self.pitcher_metrics[player_name]['recent_sample_size'] = sample_size

                    elif position_type == 'B' and player_name in self.hitter_metrics:
                        self.hitter_metrics[player_name]['recent_xwOBA'] = recent_xwoba
                        self.hitter_metrics[player_name]['recent_sample_size'] = sample_size

            # Count how many players got recent data
            pitcher_count = sum(1 for p in self.pitcher_metrics.values() if 'recent_xwOBA' in p)
            hitter_count = sum(1 for h in self.hitter_metrics.values() if 'recent_xwOBA' in h)
            print(f"Added recent performance data for {pitcher_count} pitchers and {hitter_count} hitters")

        except Exception as e:
            print(f"Error loading recent performance data: {e}")

    def print_data_sources_summary(self):
        """
        Print a summary of what data sources are available
        This should be called before running the optimizer
        """
        print("\n===== DATA SOURCES SUMMARY =====\n")

        # Statcast data summary
        if self.has_statcast_data:
            print("STATCAST DATA:")
            pitcher_count = len(self.pitcher_metrics)
            hitter_count = len(self.hitter_metrics)
            print(f"- Loaded for {pitcher_count} pitchers and {hitter_count} hitters")
            # Show some key metrics that are available
            metrics_available = []
            if any("xwOBA" in p for p in self.pitcher_metrics.values()):
                metrics_available.append("xwOBA")
            if any("Hard_Hit" in p for p in self.pitcher_metrics.values()):
                metrics_available.append("Hard Hit %")
            if any("K" in p for p in self.pitcher_metrics.values()):
                metrics_available.append("K%")
            if any("Barrel" in h for h in self.hitter_metrics.values()):
                metrics_available.append("Barrel %")

            if metrics_available:
                print(f"- Key metrics: {', '.join(metrics_available)}")
        else:
            print("STATCAST DATA:")
            print("- No Statcast data detected")

        # Vegas lines data summary
        if self.has_vegas_data:
            print("\nVEGAS LINES DATA:")
            team_count = len(self.team_implied_totals)
            print(f"- Implied totals for {team_count} teams")
            if team_count > 0:
                min_total = min(self.team_implied_totals.values())
                max_total = max(self.team_implied_totals.values())
                print(f"- Range: {min_total:.1f} to {max_total:.1f} runs")

                # Show some high/low teams
                high_teams = sorted(self.team_implied_totals.items(), key=lambda x: x[1], reverse=True)[:3]
                low_teams = sorted(self.team_implied_totals.items(), key=lambda x: x[1])[:3]

                print(f"- Highest totals: {', '.join([f'{team} ({total:.1f})' for team, total in high_teams])}")
                print(f"- Lowest totals: {', '.join([f'{team} ({total:.1f})' for team, total in low_teams])}")
        else:
            print("\nVEGAS LINES DATA:")
            print("- No Vegas lines data detected")

        # Park factors summary
        if self.park_factors:
            print("\nPARK FACTORS:")
            print(f"- Data for {len(self.park_factors)} stadiums")

            # Show some extreme parks
            hitter_parks = sorted([(team, data["overall"]) for team, data in self.park_factors.items()],
                                  key=lambda x: x[1], reverse=True)[:3]
            pitcher_parks = sorted([(team, data["overall"]) for team, data in self.park_factors.items()],
                                   key=lambda x: x[1])[:3]

            print(f"- Most hitter-friendly: {', '.join([f'{team} ({factor})' for team, factor in hitter_parks])}")
            print(f"- Most pitcher-friendly: {', '.join([f'{team} ({factor})' for team, factor in pitcher_parks])}")

        # Team handedness summary
        if self.team_handedness:
            print("\nTEAM HANDEDNESS:")
            print(f"- Data for {len(self.team_handedness)} teams")

            # Show teams with most lefties
            lefty_teams = sorted([(team, data["left_pct"]) for team, data in self.team_handedness.items()],
                                 key=lambda x: x[1], reverse=True)[:3]
            print(f"- Highest % of LHB: {', '.join([f'{team} ({pct:.0%})' for team, pct in lefty_teams])}")

        print("\n========================================\n")

    def initialize_enhanced_scoring(self):
        """
        Initialize all required data structures for enhanced scoring
        Call this method before running your DFS optimizer
        """
        # 1. Load park factors if not already done
        if not self.park_factors:
            self.load_park_factors()

        # 2. Load team handedness if not already done
        if not self.team_handedness:
            self.load_team_handedness()

        # 3. Check that we have the necessary opponent mappings
        if not self.opponent_map:
            print("WARNING: No opponent mappings found. Game info should be set before scoring.")

        # 4. Check that we have team home/away info
        if not self.team_is_home:
            print("WARNING: No home/away information found. Game info should be set before scoring.")

        # 5. Check if we have starting pitcher information
        if not self.team_pitcher:
            print("WARNING: No starting pitcher information found. Platoon advantages will be limited.")

        # 6. Generate Vegas data if missing
        if not self.has_vegas_data and self.opponent_map:
            self._generate_default_implied_totals()

        # 7. Print summary of available data sources
        self.print_data_sources_summary()

        print("Enhanced scoring system initialized and ready for use")

    # Part 3: The calculate_player_score method

    def calculate_player_score(self, name, position, team, salary, proj_pts, batting_order):
        """Calculate player score based on advanced metrics with enhanced factors"""
        # Base score from projected points (if available)
        base_score = 8
        if proj_pts is not None and proj_pts > 0:
            base_score = max(5, min(15, proj_pts / 2))

        if position == "P":
            # PITCHER SCORING
            if name in self.pitcher_metrics:
                metrics = self.pitcher_metrics[name]
                # Base score at least 10 for pitchers
                base_score = max(base_score, 10)

                # K% bonus (high is good for pitchers)
                k_pct = metrics.get("K", 0)
                if k_pct >= 30:
                    base_score += 5
                elif k_pct >= 25:
                    base_score += 3
                elif k_pct >= 20:
                    base_score += 1

                # Hard Hit% bonus (low is good for pitchers)
                hard_hit = metrics.get("Hard_Hit", 0)
                if hard_hit <= 25:
                    base_score += 5
                elif hard_hit <= 30:
                    base_score += 3
                elif hard_hit <= 35:
                    base_score += 1

                # xwOBA bonus (low is good for pitchers)
                xwoba = metrics.get("xwOBA", 0)
                if xwoba <= .270:
                    base_score += 5
                elif xwoba <= .300:
                    base_score += 3
                elif xwoba <= .330:
                    base_score += 1

                # Whiff% bonus - ENHANCED METRIC
                whiff = metrics.get("Whiff", 0)
                if whiff >= 30:
                    base_score += 3
                elif whiff >= 25:
                    base_score += 2
                elif whiff >= 20:
                    base_score += 1

                # Velocity bonus - ENHANCED METRIC
                velo = metrics.get("avg_velocity", 0)
                if velo >= 96:
                    base_score += 2
                elif velo >= 94:
                    base_score += 1

                # ENHANCEMENT: Recent performance trend
                if "recent_xwOBA" in metrics and metrics.get("recent_sample_size", 0) >= 10:
                    recent_xwoba = metrics["recent_xwOBA"]
                    season_xwoba = metrics.get("xwOBA", 0.320)

                    # For pitchers lower is better
                    if recent_xwoba < season_xwoba - 0.030:  # Much better recently
                        base_score += 2.0
                        print(f"⬆️ {name} trending up: recent xwOBA {recent_xwoba:.3f} vs season {season_xwoba:.3f}")
                    elif recent_xwoba < season_xwoba - 0.015:  # Better recently
                        base_score += 1.0
                    elif recent_xwoba > season_xwoba + 0.030:  # Much worse recently
                        base_score -= 2.0
                        print(f"⬇️ {name} trending down: recent xwOBA {recent_xwoba:.3f} vs season {season_xwoba:.3f}")
                    elif recent_xwoba > season_xwoba + 0.015:  # Worse recently
                        base_score -= 1.0

                # ENHANCEMENT: Handedness splits advantage
                if "vs_LHB" in metrics and "vs_RHB" in metrics:
                    # Check if we know the opponent lineup's handedness distribution
                    opponent = self.opponent_map.get(team, None)
                    if opponent in getattr(self, 'team_handedness', {}):
                        lhb_pct = self.team_handedness[opponent].get("left_pct", 0.33)
                        rhb_pct = 1.0 - lhb_pct

                        # Calculate weighted splits
                        vs_left_woba = metrics["vs_LHB"].get("wOBA", 0.330)
                        vs_right_woba = metrics["vs_RHB"].get("wOBA", 0.320)
                        weighted_woba = (vs_left_woba * lhb_pct) + (vs_right_woba * rhb_pct)

                        # Bonus/penalty based on matchup
                        if weighted_woba < 0.300:  # Strong matchup
                            base_score += 2.0
                        elif weighted_woba < 0.315:  # Good matchup
                            base_score += 1.0
                        elif weighted_woba > 0.345:  # Bad matchup
                            base_score -= 2.0
                        elif weighted_woba > 0.330:  # Tough matchup
                            base_score -= 1.0

                # ENHANCEMENT: Park factors
                # Get home team (venue) for the game
                venue_team = None
                if hasattr(self, 'team_is_home') and team in self.team_is_home:
                    if not self.team_is_home.get(team, True):
                        # If this pitcher's team is away, the venue is the opponent's park
                        venue_team = self.opponent_map.get(team, None)
                    else:
                        # If this pitcher's team is home, the venue is their park
                        venue_team = team
                else:
                    # Default to team if home/away info not available
                    venue_team = team

                if venue_team and hasattr(self, 'park_factors') and venue_team in self.park_factors:
                    park_factor = self.park_factors[venue_team].get("overall", 100)
                    if park_factor >= 105:  # Very hitter-friendly
                        base_score -= 1.5
                    elif park_factor >= 102:  # Hitter-friendly
                        base_score -= 1.0
                    elif park_factor <= 93:  # Very pitcher-friendly
                        base_score += 1.5
                    elif park_factor <= 97:  # Pitcher-friendly
                        base_score += 1.0

                # Apply opponent implied total adjustment
                if team in self.opponent_map and self.opponent_map[team] in self.team_implied_totals:
                    opp_implied = self.team_implied_totals[self.opponent_map[team]]
                    if opp_implied <= 3.5:
                        base_score += 3
                    elif opp_implied <= 4.0:
                        base_score += 2
                    elif opp_implied <= 4.5:
                        base_score += 1
                    elif opp_implied >= 5.5:
                        base_score -= 2
                    elif opp_implied >= 5.0:
                        base_score -= 1

                return max(1, min(base_score, 20))
            else:
                return base_score  # Default score if no advanced metrics
        else:
            # HITTER SCORING
            if name in self.hitter_metrics:
                metrics = self.hitter_metrics[name]

                # xwOBA bonus (high is good for hitters)
                xwoba = metrics.get("xwOBA", 0)
                if xwoba >= .370:
                    base_score += 5
                elif xwoba >= .340:
                    base_score += 3
                elif xwoba >= .320:
                    base_score += 2
                elif xwoba >= .300:
                    base_score += 1

                # Hard Hit% bonus
                hard_hit = metrics.get("Hard_Hit", 0)
                if hard_hit >= 45:
                    base_score += 3
                elif hard_hit >= 40:
                    base_score += 2
                elif hard_hit >= 35:
                    base_score += 1

                # Barrel% bonus
                barrel = metrics.get("Barrel", 0)
                if barrel >= 12:
                    base_score += 3
                elif barrel >= 8:
                    base_score += 2
                elif barrel >= 5:
                    base_score += 1

                # Exit Velocity bonus - ENHANCED METRIC
                exit_velo = metrics.get("avg_exit_velocity", 0)
                if exit_velo >= 92:
                    base_score += 2
                elif exit_velo >= 90:
                    base_score += 1

                # K% penalty (low is good for hitters)
                k_pct = metrics.get("K", 0)
                if k_pct <= 15:
                    base_score += 2
                elif k_pct <= 20:
                    base_score += 1
                elif k_pct >= 30:
                    base_score -= 1

                # BB% bonus
                bb_pct = metrics.get("BB", 0)
                if bb_pct >= 12:
                    base_score += 2
                elif bb_pct >= 9:
                    base_score += 1

                # Pull% bonus (for power hitters)
                pull = metrics.get("Pull", 0)
                if hard_hit >= 40 and pull >= 45:  # Power pull hitters
                    base_score += 2
                elif hard_hit >= 35 and pull >= 40:
                    base_score += 1

                # ENHANCEMENT: Recent performance trend
                if "recent_xwOBA" in metrics and metrics.get("recent_sample_size", 0) >= 10:
                    recent_xwoba = metrics["recent_xwOBA"]
                    season_xwoba = metrics.get("xwOBA", 0.320)

                    # For hitters higher is better
                    if recent_xwoba > season_xwoba + 0.030:  # Much better recently
                        base_score += 2.0
                        print(f"⬆️ {name} trending up: recent xwOBA {recent_xwoba:.3f} vs season {season_xwoba:.3f}")
                    elif recent_xwoba > season_xwoba + 0.015:  # Better recently
                        base_score += 1.0
                    elif recent_xwoba < season_xwoba - 0.030:  # Much worse recently
                        base_score -= 2.0
                        print(f"⬇️ {name} trending down: recent xwOBA {recent_xwoba:.3f} vs season {season_xwoba:.3f}")
                    elif recent_xwoba < season_xwoba - 0.015:  # Worse recently
                        base_score -= 1.0

                # ENHANCEMENT: Park factors for hitters
                # Get where the game is played
                venue_team = None
                if hasattr(self, 'team_is_home') and team in self.team_is_home:
                    if self.team_is_home.get(team, False):
                        # If this batter's team is home, the venue is their park
                        venue_team = team
                    else:
                        # If this batter's team is away, the venue is the opponent's park
                        venue_team = self.opponent_map.get(team, None)
                else:
                    # Default to using opponent's park if home/away info not available
                    venue_team = self.opponent_map.get(team, None)

                if venue_team and hasattr(self, 'park_factors') and venue_team in self.park_factors:
                    # Determine player type based on metrics
                    is_power_hitter = metrics.get("Barrel", 0) >= 8.0 or metrics.get("Hard_Hit", 0) >= 40.0
                    is_contact_hitter = metrics.get("K", 0) <= 18.0 and metrics.get("Barrel", 0) < 8.0

                    if is_power_hitter:
                        # Power hitters benefit more from HR park factor
                        hr_factor = self.park_factors[venue_team].get("hr", 100)
                        if hr_factor >= 110:  # Great for homers
                            base_score += 2.0
                        elif hr_factor >= 105:  # Good for homers
                            base_score += 1.0
                        elif hr_factor <= 90:  # Bad for homers
                            base_score -= 1.0
                    elif is_contact_hitter:
                        # Contact hitters benefit more from overall park factor
                        overall_factor = self.park_factors[venue_team].get("overall", 100)
                        if overall_factor >= 105:  # Very hitter-friendly
                            base_score += 1.5
                        elif overall_factor >= 102:  # Hitter-friendly
                            base_score += 0.75
                        elif overall_factor <= 93:  # Very pitcher-friendly
                            base_score -= 1.5
                        elif overall_factor <= 97:  # Pitcher-friendly
                            base_score -= 0.75

                # ENHANCEMENT: Platoon advantage (batter vs pitcher handedness)
                batter_hand = metrics.get("hand", None)
                if batter_hand and team in self.opponent_map:
                    opponent_team = self.opponent_map[team]
                    if hasattr(self, 'team_pitcher') and opponent_team in self.team_pitcher:
                        opponent_pitcher = self.team_pitcher[opponent_team]

                        if opponent_pitcher and opponent_pitcher in self.pitcher_metrics:
                            pitcher_hand = self.pitcher_metrics[opponent_pitcher].get("hand", None)

                            # Apply platoon bonus if opposite hands (classic platoon advantage)
                            if pitcher_hand and batter_hand != pitcher_hand:
                                # LHB vs RHP or RHB vs LHP
                                base_score += 1.5

                            # Extra bonus for LHB vs RHP in power-friendly parks
                            if (batter_hand == "L" and pitcher_hand == "R" and
                                    venue_team and venue_team in self.park_factors):
                                pull_side_factor = self.park_factors[venue_team].get("right_field", 100)
                                if pull_side_factor >= 110 and is_power_hitter:
                                    base_score += 1.0  # Ideal situation for pull-power lefty

                # Batting order bonus
                if batting_order is not None:
                    if batting_order <= 2:
                        base_score += 3
                    elif batting_order <= 4:
                        base_score += 2
                    elif batting_order <= 6:
                        base_score += 1

                # Team implied total bonus
                implied_total = self.team_implied_totals.get(team, 0)
                if implied_total >= 5.0:
                    base_score += 2
                elif implied_total >= 4.5:
                    base_score += 1

                return max(1, min(base_score, 20))
            else:
                # Default score adjustment based on salary
                # Higher paid players tend to be better
                max_salary = 6000  # Estimate for max hitter salary
                if salary is not None and salary > 0:
                    salary_factor = min(1.0, salary / max_salary)
                    base_score = base_score * (0.7 + 0.5 * salary_factor)

                return max(1, min(base_score, 20))


class StatcastIntegration:
    """Enhanced Statcast integration for DFS optimizer"""

    def __init__(self, cache_dir="data/statcast"):
        """Initialize the Statcast integration module"""
        self.cache_dir = cache_dir
        self.player_ids = {}
        self.force_refresh = False  # Add force refresh flag
        self.cache_expiry = 24  # Cache expiry in hours

        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)

        # Load player IDs if available
        self._load_player_ids()

        print(f"Statcast integration initialized with {len(self.player_ids)} player IDs")

    def set_force_refresh(self, force_refresh):
        """Set force refresh flag to override cache"""
        self.force_refresh = force_refresh
        print(f"Statcast force refresh set to: {force_refresh}")

    def _load_player_ids(self):
        """Load cached player IDs from a JSON file"""
        try:
            file_path = os.path.join(self.cache_dir, "player_ids.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    self.player_ids = json.load(f)
                print(f"Loaded {len(self.player_ids)} player IDs from cache")
        except Exception as e:
            print(f"Error loading player IDs: {e}")
            self.player_ids = {}

    def _save_player_ids(self):
        """Save player IDs to a JSON file"""
        try:
            file_path = os.path.join(self.cache_dir, "player_ids.json")
            with open(file_path, 'w') as f:
                json.dump(self.player_ids, f, indent=2)
        except Exception as e:
            print(f"Error saving player IDs: {e}")

    def import_player_ids_from_csv(self, file_path):
        """Import player IDs from a CSV file"""
        try:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False

            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header row

                # Find name and ID columns
                name_col = None
                id_col = None
                for i, col in enumerate(header):
                    if col.lower() in ['name', 'player', 'player_name']:
                        name_col = i
                    elif col.lower() in ['id', 'player_id', 'mlbam_id']:
                        id_col = i

                if name_col is None or id_col is None:
                    print("Could not find name and ID columns in CSV")
                    return False

                # Load player IDs
                count = 0
                for row in reader:
                    if len(row) > max(name_col, id_col):
                        name = row[name_col].strip()
                        player_id = row[id_col].strip()
                        if name and player_id:
                            self.player_ids[name] = player_id
                            count += 1

                print(f"Imported {count} player IDs from {file_path}")
                self._save_player_ids()
                return True

        except Exception as e:
            print(f"Error importing player IDs from CSV: {e}")
            return False

    class StatcastIntegration:
        """Enhanced Statcast integration for DFS optimizer"""

        def __init__(self, cache_dir="data/statcast"):
            """Initialize the Statcast integration module"""
            self.cache_dir = cache_dir
            self.player_ids = {}
            self.force_refresh = False  # Add force refresh flag
            self.cache_expiry = 24  # Cache expiry in hours

            # Create cache directory if it doesn't exist
            os.makedirs(self.cache_dir, exist_ok=True)

            # Load player IDs if available
            self._load_player_ids()

            print(f"Statcast integration initialized with {len(self.player_ids)} player IDs")

    def _generate_placeholder_metrics(self, player_name, is_pitcher):
        """Generate placeholder metrics for demo purposes"""
        import random

        # For demo purposes, create somewhat realistic metrics
        if is_pitcher:
            return {
                "name": player_name,
                "xwOBA": round(random.uniform(0.250, 0.350), 3),
                "Hard_Hit": round(random.uniform(25, 45), 1),
                "Barrel": round(random.uniform(3, 12), 1),
                "K": round(random.uniform(15, 35), 1),
                "BB": round(random.uniform(5, 12), 1),
                "GB": round(random.uniform(35, 55), 1),
                "Whiff": round(random.uniform(15, 35), 1),
                "avg_velocity": round(random.uniform(90, 98), 1),
                "data_source": "fresh data (placeholder)"
            }
        else:
            return {
                "name": player_name,
                "xwOBA": round(random.uniform(0.280, 0.400), 3),
                "Hard_Hit": round(random.uniform(25, 50), 1),
                "Barrel": round(random.uniform(3, 15), 1),
                "K": round(random.uniform(10, 30), 1),
                "BB": round(random.uniform(5, 15), 1),
                "GB": round(random.uniform(30, 55), 1),
                "Pull": round(random.uniform(25, 55), 1),
                "avg_exit_velocity": round(random.uniform(85, 95), 1),
                "data_source": "fresh data (placeholder)"
            }

    def print_metrics_summary(self, players_data):
        """Print a summary of the Statcast metrics to verify data quality"""
        print("\n===== STATCAST METRICS QUALITY REPORT =====")

        # Count metrics by source
        metrics_count = 0
        source_counts = {}
        pitcher_count = 0
        hitter_count = 0

        # Collect metrics
        for player in players_data:
            player_name = player[1]
            player_pos = player[2]

            if len(player) > 14 and isinstance(player[14], dict):
                metrics = player[14]
                metrics_count += 1

                # Count by source
                source = metrics.get('data_source', 'unknown')
                if source not in source_counts:
                    source_counts[source] = 0
                source_counts[source] += 1

                # Count by type
                if player_pos == 'P':
                    pitcher_count += 1
                else:
                    hitter_count += 1

        # Print summary
        print(
            f"Total players with metrics: {metrics_count}/{len(players_data)} ({metrics_count / len(players_data) * 100:.1f}%)")
        print(f"Pitchers with metrics: {pitcher_count}")
        print(f"Hitters with metrics: {hitter_count}")

        print("\nMetrics by source:")
        for source, count in source_counts.items():
            print(f"  - {source}: {count} players")

        # Print sample metrics
        print("\nSample metrics:")
        samples_shown = 0

        # First show a pitcher
        for player in players_data:
            if player[2] == 'P' and len(player) > 14 and isinstance(player[14], dict):
                metrics = player[14]
                print(f"\nPitcher: {player[1]} ({player[3]})")
                print(f"  Data source: {metrics.get('data_source', 'unknown')}")
                print(f"  Key metrics:")
                print(f"    - xwOBA: {metrics.get('xwOBA', 'N/A')}")
                print(f"    - Hard Hit%: {metrics.get('Hard_Hit', 'N/A')}")
                print(f"    - Barrel%: {metrics.get('Barrel', 'N/A')}")
                print(f"    - Velocity: {metrics.get('avg_velocity', 'N/A')}")
                print(f"    - Whiff%: {metrics.get('Whiff', 'N/A')}")
                samples_shown += 1
                break

        # Then show a hitter
        for player in players_data:
            if player[2] != 'P' and len(player) > 14 and isinstance(player[14], dict):
                metrics = player[14]
                print(f"\nHitter: {player[1]} ({player[3]})")
                print(f"  Data source: {metrics.get('data_source', 'unknown')}")
                print(f"  Key metrics:")
                print(f"    - xwOBA: {metrics.get('xwOBA', 'N/A')}")
                print(f"    - Hard Hit%: {metrics.get('Hard_Hit', 'N/A')}")
                print(f"    - Barrel%: {metrics.get('Barrel', 'N/A')}")
                print(f"    - Exit Velo: {metrics.get('avg_exit_velocity', 'N/A')}")
                samples_shown += 1
                break

        if samples_shown == 0:
            print("  No players found with Statcast metrics!")

        print("==========================================")

    def fetch_metrics(self, player_name, is_pitcher=False):
        """
        Fetch metrics for a player, either from cache or fresh data
        """
        # Generate cache key for this player
        cache_key = f"{player_name}_{'p' if is_pitcher else 'h'}"
        cache_key = cache_key.replace(' ', '_').replace("'", "").lower()
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        # Check cache unless force refresh is enabled
        if os.path.exists(cache_file) and not self.force_refresh:
            cache_time = os.path.getmtime(cache_file)
            hours_old = (datetime.now() - datetime.fromtimestamp(cache_time)).total_seconds() / 3600

            if hours_old < self.cache_expiry:
                try:
                    with open(cache_file, 'r') as f:
                        metrics = json.load(f)
                        # Add data source info
                        metrics['data_source'] = f"cached ({hours_old:.1f} hours old)"
                        return metrics
                except Exception as e:
                    print(f"Error reading cache for {player_name}: {e}")

        # If we get here, we need to fetch fresh data
        if self.force_refresh:
            print(f"Force refresh enabled. Fetching fresh metrics for {player_name}")
        else:
            print(f"No valid cache. Fetching fresh metrics for {player_name}")

        # This would call Statcast API in a real implementation
        # For now, just return a placeholder with some realistic metrics
        metrics = self._generate_placeholder_metrics(player_name, is_pitcher)

        # Save to cache
        try:
            with open(cache_file, 'w') as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            print(f"Error saving cache for {player_name}: {e}")

        return metrics
    def debug_statcast_data(self):
        """Print diagnostic information about Statcast data"""
        print("\n=== STATCAST DIAGNOSTICS ===")

        # Check if the service is available
        print(f"Statcast service available: True")
        print(f"Force refresh: {self.force_refresh}")

        # Check cache directory
        if os.path.exists(self.cache_dir):
            cache_files = os.listdir(self.cache_dir)
            print(f"Cache directory: {self.cache_dir}")
            print(f"Cache files found: {len(cache_files)}")
            if cache_files:
                metric_files = [f for f in cache_files if f != "player_ids.json"]
                print(f"Metric cache files: {len(metric_files)}")
                if metric_files:
                    print(f"Sample cache files: {metric_files[:5]}")
        else:
            print(f"Cache directory {self.cache_dir} does not exist")

        # Test fetch for a sample player
        print("\nTesting fetch for a sample pitcher...")
        try:
            pitcher_metrics = self.fetch_metrics("Max Scherzer", is_pitcher=True)
            print(f"Pitcher metrics type: {type(pitcher_metrics).__name__}")
            print(f"Pitcher metrics sample: {list(pitcher_metrics.keys())[:5]}")
            if "xwOBA" in pitcher_metrics:
                print(f"Pitcher xwOBA: {pitcher_metrics['xwOBA']}")
            if "avg_velocity" in pitcher_metrics:
                print(f"Pitcher Velocity: {pitcher_metrics.get('avg_velocity', 'N/A')}")
        except Exception as e:
            print(f"Error testing pitcher metrics: {e}")
            import traceback
            traceback.print_exc()

        print("\nTesting fetch for a sample hitter...")
        try:
            hitter_metrics = self.fetch_metrics("Mike Trout", is_pitcher=False)
            print(f"Hitter metrics type: {type(hitter_metrics).__name__}")
            print(f"Hitter metrics sample: {list(hitter_metrics.keys())[:5]}")
            if "xwOBA" in hitter_metrics:
                print(f"Hitter xwOBA: {hitter_metrics['xwOBA']}")
            if "Barrel" in hitter_metrics:
                print(f"Hitter Barrel%: {hitter_metrics.get('Barrel', 'N/A')}")
        except Exception as e:
            print(f"Error testing hitter metrics: {e}")
            import traceback
            traceback.print_exc()

        print("\n=== END DIAGNOSTICS ===\n")

    def enrich_player_data(self, players, force_refresh=False):
        """
        Enrich player data with Statcast metrics
        """
        # Update force refresh flag
        self.set_force_refresh(force_refresh)

        enhanced_players = []
        print(f"Enriching {len(players)} players with Statcast metrics...")

        start_time = datetime.now()

        for i, player in enumerate(players):
            if i % 100 == 0 and i > 0:
                print(f"Processed {i}/{len(players)} players...")

            player_name = player[1]
            position = player[2]
            is_pitcher = position == "P"

            # Create a copy to avoid modifying the original
            enhanced_player = list(player)

            # Get metrics for this player
            metrics = self.fetch_metrics(player_name, is_pitcher)

            # Make sure we have at least 14 elements
            while len(enhanced_player) < 14:
                enhanced_player.append(None)

            # Add the metrics dictionary at index 14
            enhanced_player.append(metrics)

            # Add to result
            enhanced_players.append(enhanced_player)

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"Enriched {len(enhanced_players)} players in {elapsed:.2f} seconds")
        return enhanced_players

    def enrich_player_data(self, players):
        """
        Placeholder for Statcast enrichment - would need pybaseball in a real implementation
        This simple version just passes the data through
        """
        print("Note: Full Statcast integration requires pybaseball package")
        print("Skipping Statcast enrichment in this simple version")