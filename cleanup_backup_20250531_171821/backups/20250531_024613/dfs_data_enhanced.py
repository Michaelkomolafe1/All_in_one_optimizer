#!/usr/bin/env python3
"""
Enhanced DFS Data Integration
Combines all your existing data sources with improved processing
"""

import os
import csv
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import glob


class EnhancedDFSData:
    """Enhanced DFS data management with all integrations"""

    def __init__(self):
        # Core data structures
        self.players = []
        self.hitter_metrics = {}
        self.pitcher_metrics = {}
        self.opponent_map = {}
        self.team_implied_totals = {}

        # Enhanced data structures
        self.team_handedness = {}
        self.team_is_home = {}
        self.team_pitcher = {}
        self.park_factors = {}
        self.confirmed_lineups = {}
        self.recent_performance = {}
        self.weather_data = {}

        # Data availability flags
        self.has_statcast_data = False
        self.has_vegas_data = False
        self.has_confirmed_lineups = False
        self.has_weather_data = False

        # Initialize integrations
        self.statcast = None
        self.vegas = None
        self.name_matcher = None

        print("🔧 Enhanced DFS Data System initialized")

    def load_all_integrations(self):
        """Load all available integrations"""
        try:
            # Load Statcast integration
            try:
                from statacast_integration import StatcastIntegration
                self.statcast = StatcastIntegration()
                print("✅ Statcast integration loaded")
            except ImportError:
                print("⚠️ Statcast integration not available")

            # Load Vegas lines integration
            try:
                from vegas_lines import VegasLines
                self.vegas = VegasLines()
                print("✅ Vegas lines integration loaded")
            except ImportError:
                print("⚠️ Vegas lines integration not available")

            # Load name matcher
            try:
                from dfs_runner_enhanced import PlayerNameMatcher
                self.name_matcher = PlayerNameMatcher()
                print("✅ Enhanced name matcher loaded")
            except ImportError:
                print("⚠️ Enhanced name matcher not available")

        except Exception as e:
            print(f"⚠️ Error loading integrations: {e}")

    def import_from_draftkings(self, file_path):
        """Enhanced DraftKings import with better error handling"""
        try:
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                return False

            print(f"📁 Importing DraftKings data: {os.path.basename(file_path)}")

            players = []
            team_games = set()

            # Position mapping
            position_map = {"SP": "P", "RP": "P"}

            with open(file_path, 'r', encoding='utf-8') as f:
                # Handle different CSV formats
                sample = f.read(1024)
                f.seek(0)

                # Detect delimiter
                delimiter = ','
                if '\t' in sample:
                    delimiter = '\t'
                elif ';' in sample:
                    delimiter = ';'

                reader = csv.reader(f, delimiter=delimiter)
                headers = next(reader, None)

                if not headers:
                    print("❌ Empty CSV file")
                    return False

                print(f"📊 CSV Headers: {headers}")

                # Enhanced column detection
                column_map = self._detect_columns(headers)
                print(f"🎯 Column mapping: {column_map}")

                row_count = 0
                for row in reader:
                    if len(row) < max(column_map.values(), default=[0]):
                        continue

                    try:
                        # Extract player data with better error handling
                        player_data = self._extract_player_data(row, column_map, position_map, row_count + 1)
                        if player_data:
                            players.append(player_data)
                            team_games.add(player_data[3])  # Track teams
                            row_count += 1

                    except Exception as e:
                        print(f"⚠️ Error processing row {row_count + 1}: {e}")
                        continue

            print(f"✅ Imported {len(players)} players from {len(team_games)} teams")

            # Store and validate
            self.players = players
            return self._validate_player_data()

        except Exception as e:
            print(f"❌ Error importing DraftKings data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _detect_columns(self, headers):
        """Enhanced column detection for various DK export formats"""
        column_map = {}

        for i, header in enumerate(headers):
            header_lower = header.lower().strip()

            # Player name detection
            if any(name in header_lower for name in ['name', 'player']):
                column_map['name'] = i

            # Position detection
            elif any(pos in header_lower for pos in ['position', 'pos']):
                column_map['position'] = i

            # Team detection
            elif any(team in header_lower for team in ['team', 'teamabbrev', 'tm']):
                column_map['team'] = i

            # Salary detection
            elif any(sal in header_lower for sal in ['salary', 'sal', 'cost']):
                column_map['salary'] = i

            # Projection detection
            elif any(proj in header_lower for proj in
                     ['avgpointspergame', 'fppg', 'projection', 'proj', 'points']):
                column_map['projection'] = i

            # Game info detection
            elif any(game in header_lower for game in ['game info', 'game', 'matchup']):
                column_map['game_info'] = i

        return column_map

    def _extract_player_data(self, row, column_map, position_map, player_id):
        """Extract and validate player data from CSV row"""
        try:
            # Extract basic info with defaults
            name = row[column_map.get('name', 0)].strip() if column_map.get(
                'name') is not None else f"Player_{player_id}"
            position = row[column_map.get('position', 1)].strip() if column_map.get('position') is not None else "UTIL"
            team = row[column_map.get('team', 2)].strip() if column_map.get('team') is not None else "UNK"

            # Clean and normalize position
            position = position_map.get(position, position)

            # Extract and clean salary
            salary_str = row[column_map.get('salary', 3)] if column_map.get('salary') is not None else "3000"
            salary = self._parse_salary(salary_str)

            # Extract projection
            proj_str = row[column_map.get('projection')] if column_map.get('projection') is not None else "0"
            projection = self._parse_projection(proj_str)

            # Calculate initial score
            score = self._calculate_initial_score(salary, projection, position)

            # Build player data structure
            # [id, name, position, team, salary, projection, score, batting_order, ...]
            player_data = [
                player_id,
                name,
                position,
                team,
                salary,
                projection,
                score,
                None,  # batting_order - will be filled later
            ]

            # Extend to full length for additional data
            while len(player_data) < 20:
                player_data.append(None)

            return player_data

        except Exception as e:
            print(f"⚠️ Error extracting player data: {e}")
            return None

    def _parse_salary(self, salary_str):
        """Parse salary from various formats"""
        try:
            # Remove common characters and convert
            cleaned = str(salary_str).replace(', '').replace(', ', '').replace(' ', ''')
            return max(2000, int(float(cleaned))) if cleaned and cleaned != '' else 3000
        except:
            return 3000

    def _parse_projection(self, proj_str):
        """Parse projection from various formats"""
        try:
            cleaned = str(proj_str).replace(' ', '')
            return max(0.0, float(cleaned)) if cleaned and cleaned != '' else 0.0
        except:
            return 0.0

    def _calculate_initial_score(self, salary, projection, position):
        """Calculate initial player score"""
        if projection > 0:
            return float(projection)
        elif salary > 0:
            # Position-based salary multipliers
            multipliers = {'P': 0.002, 'C': 0.0018, '1B': 0.0016, 'OF': 0.0015,
                           '2B': 0.0014, '3B': 0.0015, 'SS': 0.0014}
            multiplier = multipliers.get(position, 0.0015)
            return salary * multiplier
        else:
            return 5.0

    def _validate_player_data(self):
        """Validate imported player data"""
        if not self.players:
            print("❌ No players imported")
            return False

        # Check position distribution
        position_counts = {}
        for player in self.players:
            pos = player[2]
            position_counts[pos] = position_counts.get(pos, 0) + 1

        print(f"📊 Position distribution: {position_counts}")

        # Check required positions
        required_positions = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        missing_positions = []

        for pos, required in required_positions.items():
            available = position_counts.get(pos, 0)
            if available < required:
                missing_positions.append(f"{pos} (need {required}, have {available})")

        if missing_positions:
            print(f"⚠️ Missing positions: {', '.join(missing_positions)}")
            return False

        print("✅ Player data validation passed")
        return True

    def enhance_with_all_data(self, force_refresh=False):
        """Enhance players with all available data sources"""
        if not self.players:
            print("❌ No players loaded. Import DraftKings data first.")
            return []

        print("🔄 Enhancing players with all available data...")
        enhanced_players = list(self.players)

        # 1. Statcast enhancement
        if self.statcast:
            print("📊 Adding Statcast metrics...")
            try:
                enhanced_players = self.statcast.enrich_player_data(enhanced_players, force_refresh)
                self.has_statcast_data = True
                self._extract_statcast_metrics(enhanced_players)
            except Exception as e:
                print(f"⚠️ Statcast enhancement failed: {e}")

        # 2. Vegas lines enhancement
        if self.vegas:
            print("💰 Adding Vegas lines data...")
            try:
                vegas_lines = self.vegas.get_vegas_lines(force_refresh)
                if vegas_lines:
                    enhanced_players = self.vegas.apply_to_players(enhanced_players)
                    self.has_vegas_data = True
                    self._extract_vegas_data(vegas_lines)
            except Exception as e:
                print(f"⚠️ Vegas enhancement failed: {e}")

        # 3. Load confirmed lineups
        self._load_confirmed_lineups()

        # 4. Apply confirmed lineup data
        if self.has_confirmed_lineups:
            print("✅ Applying confirmed lineup data...")
            enhanced_players = self._apply_confirmed_lineups(enhanced_players)

        # 5. Calculate enhanced scores
        print("🧮 Calculating enhanced scores...")
        enhanced_players = self._calculate_enhanced_scores(enhanced_players)

        # 6. Final validation and cleanup
        enhanced_players = self._cleanup_player_data(enhanced_players)

        print(f"✅ Enhanced {len(enhanced_players)} players with all available data")
        return enhanced_players

    def _extract_statcast_metrics(self, players):
        """Extract Statcast metrics into organized structure"""
        self.hitter_metrics = {}
        self.pitcher_metrics = {}

        for player in players:
            if len(player) > 14 and isinstance(player[14], dict):
                name = player[1]
                position = player[2]
                metrics = player[14]

                if position == 'P':
                    self.pitcher_metrics[name] = {
                        'xwOBA': metrics.get('xwOBA', 0.320),
                        'K': metrics.get('K', 20.0),
                        'Hard_Hit': metrics.get('Hard_Hit', 35.0),
                        'Whiff': metrics.get('Whiff', 25.0),
                        'avg_velocity': metrics.get('avg_velocity', 93.0),
                        'hand': metrics.get('hand', 'R')
                    }
                else:
                    self.hitter_metrics[name] = {
                        'xwOBA': metrics.get('xwOBA', 0.320),
                        'Hard_Hit': metrics.get('Hard_Hit', 35.0),
                        'Barrel': metrics.get('Barrel', 6.0),
                        'K': metrics.get('K', 22.0),
                        'BB': metrics.get('BB', 8.5),
                        'avg_exit_velocity': metrics.get('avg_exit_velocity', 88.0),
                        'hand': metrics.get('hand', 'R')
                    }

    def _extract_vegas_data(self, vegas_lines):
        """Extract Vegas data into organized structure"""
        self.team_implied_totals = {}
        self.opponent_map = {}
        self.team_is_home = {}

        for team, data in vegas_lines.items():
            self.team_implied_totals[team] = data.get('team_total', 4.5)
            self.opponent_map[team] = data.get('opponent', '')
            self.team_is_home[team] = data.get('is_home', False)

    def _load_confirmed_lineups(self):
        """Load confirmed lineup data from various sources"""
        confirmed_files = [
            'data/confirmed_lineups.csv',
            'data/starting_lineups.csv',
            'confirmed_lineups.csv',
            'starting_lineups.csv'
        ]

        for file_path in confirmed_files:
            if os.path.exists(file_path):
                try:
                    self._parse_confirmed_lineups_file(file_path)
                    self.has_confirmed_lineups = True
                    print(f"✅ Loaded confirmed lineups from {file_path}")
                    break
                except Exception as e:
                    print(f"⚠️ Error loading {file_path}: {e}")

    def _parse_confirmed_lineups_file(self, file_path):
        """Parse confirmed lineups CSV file"""
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                player_name = row.get('Name', '').strip()
                team = row.get('Team', '').strip()
                batting_order = row.get('Batting_Order', '').strip()
                status = row.get('Status', '').strip().lower()

                if player_name and status in ['confirmed', 'starting', 'in']:
                    self.confirmed_lineups[player_name] = {
                        'team': team,
                        'batting_order': self._safe_int(batting_order),
                        'status': 'confirmed'
                    }

    def _safe_int(self, value):
        """Safely convert to integer"""
        try:
            return int(float(str(value).strip())) if value and str(value).strip() else None
        except:
            return None

    def _apply_confirmed_lineups(self, players):
        """Apply confirmed lineup data to players"""
        matched_count = 0

        for player in players:
            player_name = player[1]

            # Direct match first
            if player_name in self.confirmed_lineups:
                confirmed_data = self.confirmed_lineups[player_name]
                player[7] = confirmed_data['batting_order']  # Set batting order
                matched_count += 1

            # Enhanced name matching if available
            elif self.name_matcher:
                try:
                    for confirmed_name, confirmed_data in self.confirmed_lineups.items():
                        match_result, confidence, method = self.name_matcher.match_player_name(
                            confirmed_name, {player_name: player}, player[3]
                        )
                        if match_result and confidence >= 80:
                            player[7] = confirmed_data['batting_order']
                            matched_count += 1
                            break
                except Exception as e:
                    continue

        print(f"✅ Applied confirmed lineups to {matched_count} players")
        return players

    def _calculate_enhanced_scores(self, players):
        """Calculate enhanced scores using all available data"""
        for player in players:
            try:
                # Get basic info
                name = player[1]
                position = player[2]
                team = player[3]
                salary = player[4]
                base_projection = player[5]

                # Calculate enhanced score
                enhanced_score = self._calculate_player_enhanced_score(
                    name, position, team, salary, base_projection, player
                )

                # Update player score
                player[6] = enhanced_score

            except Exception as e:
                print(f"⚠️ Error calculating score for {player[1]}: {e}")
                # Ensure player has a valid score
                if not player[6] or player[6] <= 0:
                    player[6] = salary / 1000.0 if salary > 0 else 5.0

        return players

    def _calculate_player_enhanced_score(self, name, position, team, salary, base_projection, player_data):
        """Calculate enhanced player score using all data sources"""

        # Start with base score
        base_score = base_projection if base_projection > 0 else salary / 1000.0
        enhanced_score = max(5.0, base_score)

        # Statcast adjustments
        if position == 'P' and name in self.pitcher_metrics:
            metrics = self.pitcher_metrics[name]

            # xwOBA adjustment (lower is better for pitchers)
            xwoba = metrics.get('xwOBA', 0.320)
            if xwoba <= 0.280:
                enhanced_score += 3.0
            elif xwoba <= 0.300:
                enhanced_score += 2.0
            elif xwoba <= 0.320:
                enhanced_score += 1.0
            elif xwoba >= 0.360:
                enhanced_score -= 2.0

            # Strikeout rate adjustment
            k_rate = metrics.get('K', 20.0)
            if k_rate >= 28:
                enhanced_score += 2.0
            elif k_rate >= 24:
                enhanced_score += 1.0
            elif k_rate <= 16:
                enhanced_score -= 1.0

            # Hard hit rate adjustment (lower is better for pitchers)
            hard_hit = metrics.get('Hard_Hit', 35.0)
            if hard_hit <= 30:
                enhanced_score += 1.5
            elif hard_hit >= 40:
                enhanced_score -= 1.5

        elif position != 'P' and name in self.hitter_metrics:
            metrics = self.hitter_metrics[name]

            # xwOBA adjustment (higher is better for hitters)
            xwoba = metrics.get('xwOBA', 0.320)
            if xwoba >= 0.380:
                enhanced_score += 3.0
            elif xwoba >= 0.350:
                enhanced_score += 2.0
            elif xwoba >= 0.320:
                enhanced_score += 1.0
            elif xwoba <= 0.280:
                enhanced_score -= 2.0

            # Hard hit rate adjustment
            hard_hit = metrics.get('Hard_Hit', 35.0)
            if hard_hit >= 45:
                enhanced_score += 2.0
            elif hard_hit >= 40:
                enhanced_score += 1.0
            elif hard_hit <= 25:
                enhanced_score -= 1.0

            # Barrel rate adjustment
            barrel = metrics.get('Barrel', 6.0)
            if barrel >= 12:
                enhanced_score += 2.0
            elif barrel >= 8:
                enhanced_score += 1.0

        # Vegas lines adjustments
        if team in self.team_implied_totals:
            implied_total = self.team_implied_totals[team]

            if position == 'P':
                # For pitchers, look at opponent's implied total
                opponent = self.opponent_map.get(team)
                if opponent and opponent in self.team_implied_totals:
                    opp_total = self.team_implied_totals[opponent]
                    if opp_total <= 3.8:
                        enhanced_score += 2.0
                    elif opp_total <= 4.2:
                        enhanced_score += 1.0
                    elif opp_total >= 5.2:
                        enhanced_score -= 1.5
            else:
                # For hitters, higher team total is better
                if implied_total >= 5.2:
                    enhanced_score += 2.0
                elif implied_total >= 4.8:
                    enhanced_score += 1.0
                elif implied_total <= 3.8:
                    enhanced_score -= 1.5

        # Confirmed lineup bonus
        if len(player_data) > 7 and player_data[7] is not None:
            batting_order = player_data[7]
            if isinstance(batting_order, (int, float)) and 1 <= batting_order <= 9:
                # Batting order bonus
                if batting_order <= 3:
                    enhanced_score += 2.0
                elif batting_order <= 6:
                    enhanced_score += 1.0

                # General confirmed lineup bonus
                enhanced_score += 1.0

        # Salary efficiency check
        if salary > 0:
            efficiency = enhanced_score / (salary / 1000.0)
            if efficiency >= 3.0:
                enhanced_score += 0.5  # Efficiency bonus
            elif efficiency <= 1.5:
                enhanced_score -= 0.5  # Efficiency penalty

        return max(1.0, enhanced_score)

    def _cleanup_player_data(self, players):
        """Final cleanup and validation of player data"""
        cleaned_players = []

        for player in players:
            try:
                # Ensure all required fields are present and valid
                if len(player) < 8:
                    continue

                # Validate core fields
                if not player[1] or not player[2] or not player[3]:  # name, position, team
                    continue

                if not isinstance(player[4], (int, float)) or player[4] <= 0:  # salary
                    player[4] = 3000

                if not isinstance(player[6], (int, float)) or player[6] <= 0:  # score
                    player[6] = player[4] / 1000.0

                # Ensure player array is proper length
                while len(player) < 20:
                    player.append(None)

                cleaned_players.append(player)

            except Exception as e:
                print(f"⚠️ Error cleaning player {player[1] if len(player) > 1 else 'unknown'}: {e}")
                continue

        return cleaned_players

    def print_data_summary(self):
        """Print comprehensive data summary"""
        print("\n" + "=" * 60)
        print("📊 ENHANCED DFS DATA SUMMARY")
        print("=" * 60)

        # Player summary
        print(f"👥 Total Players: {len(self.players)}")
        if self.players:
            position_counts = {}
            score_sum = 0
            salary_sum = 0
            confirmed_count = 0

            for player in self.players:
                pos = player[2]
                position_counts[pos] = position_counts.get(pos, 0) + 1
                score_sum += player[6] if player[6] else 0
                salary_sum += player[4] if player[4] else 0
                if len(player) > 7 and player[7] is not None:
                    confirmed_count += 1

            print(f"📍 Positions: {dict(sorted(position_counts.items()))}")
            print(f"💰 Avg Salary: ${salary_sum / len(self.players):,.0f}")
            print(f"📊 Avg Score: {score_sum / len(self.players):.2f}")
            print(f"✅ Confirmed Players: {confirmed_count} ({confirmed_count / len(self.players) * 100:.1f}%)")

        # Data source summary
        print(f"\n🔧 Data Sources:")
        print(f"  📊 Statcast: {'✅ Active' if self.has_statcast_data else '❌ Not Available'}")
        print(f"  💰 Vegas Lines: {'✅ Active' if self.has_vegas_data else '❌ Not Available'}")
        print(f"  ✅ Confirmed Lineups: {'✅ Active' if self.has_confirmed_lineups else '❌ Not Available'}")

        # Metrics summary
        if self.has_statcast_data:
            print(f"\n📈 Statcast Metrics:")
            print(f"  🥎 Hitters: {len(self.hitter_metrics)}")
            print(f"  ⚾ Pitchers: {len(self.pitcher_metrics)}")

        if self.has_vegas_data:
            print(f"\n💸 Vegas Data:")
            print(f"  🎯 Team Totals: {len(self.team_implied_totals)}")
            if self.team_implied_totals:
                avg_total = sum(self.team_implied_totals.values()) / len(self.team_implied_totals)
                print(f"  📊 Avg Implied Total: {avg_total:.1f} runs")

        print("=" * 60 + "\n")

    def export_enhanced_data(self, output_file="enhanced_players.json"):
        """Export enhanced player data for external use"""
        try:
            export_data = {
                'players': self.players,
                'data_sources': {
                    'statcast': self.has_statcast_data,
                    'vegas': self.has_vegas_data,
                    'confirmed_lineups': self.has_confirmed_lineups
                },
                'team_data': {
                    'implied_totals': self.team_implied_totals,
                    'opponent_map': self.opponent_map,
                    'home_away': self.team_is_home
                },
                'export_timestamp': datetime.now().isoformat()
            }

            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            print(f"✅ Enhanced data exported to {output_file}")
            return True

        except Exception as e:
            print(f"❌ Export failed: {e}")
            return False


# Convenience functions for backward compatibility
def load_dfs_data(dk_file_path, force_refresh=False):
    """Load and enhance DFS data from DraftKings file"""
    dfs_data = EnhancedDFSData()
    dfs_data.load_all_integrations()

    if dfs_data.import_from_draftkings(dk_file_path):
        enhanced_players = dfs_data.enhance_with_all_data(force_refresh)
        dfs_data.print_data_summary()
        return enhanced_players, dfs_data
    else:
        return None, None


if __name__ == "__main__":
    print("🚀 Enhanced DFS Data Integration System")
    print("✅ Multi-source data integration")
    print("✅ Advanced player enhancement")
    print("✅ Comprehensive validation")
    print("✅ Export capabilities")