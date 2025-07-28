#!/usr/bin/env python3
"""
CSV LOADER FOR UNIFIED CORE SYSTEM V2
=====================================
Handles DraftKings CSV loading with support for:
- Classic slates (standard positions)
- Showdown slates (CPT/UTIL positions)
- Multi-position players
- Various column name formats
"""

import pandas as pd
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Assuming these imports from your project
from unified_player_model import UnifiedPlayer

logger = logging.getLogger(__name__)


class CSVLoaderV2:
    """
    Robust CSV loader for DraftKings and similar formats
    Handles all contest types and edge cases
    """

    def __init__(self):
        """Initialize CSV loader"""
        self.slate_type = "classic"  # classic or showdown
        self.raw_df = None
        self.processed_players = []

        # Column mappings for flexibility
        self.column_mappings = {
            'name': ['Name', 'name', 'Player', 'player'],
            'position': ['Position', 'Pos', 'position', 'pos'],
            'team': ['TeamAbbrev', 'Team', 'team', 'TeamAbbr'],
            'salary': ['Salary', 'salary', 'Sal'],
            'projection': ['AvgPointsPerGame', 'Projection', 'proj', 'Proj', 'FPPG'],
            'game_info': ['Game Info', 'GameInfo', 'Game', 'game_info'],
            'batting_order': ['batting_order', 'Order', 'order']
        }

        logger.info("📁 CSV Loader V2 initialized")

    def load_csv(self, filepath: str) -> Tuple[List[UnifiedPlayer], str]:
        """
        Load and process DraftKings CSV
        Returns: (players_list, slate_type)
        """
        logger.info(f"📂 Loading CSV from: {filepath}")

        try:
            # Read CSV
            self.raw_df = pd.read_csv(filepath)
            logger.info(f"✅ Loaded {len(self.raw_df)} rows from CSV")

            # Detect slate type
            self.slate_type = self._detect_slate_type()
            logger.info(f"🎯 Detected slate type: {self.slate_type.upper()}")

            # Process based on slate type
            if self.slate_type == "showdown":
                players = self._process_showdown_csv()
            else:
                players = self._process_classic_csv()

            self.processed_players = players
            logger.info(f"✅ Processed {len(players)} players")

            # Log some stats
            self._log_slate_info()

            return players, self.slate_type

        except Exception as e:
            logger.error(f"❌ Failed to load CSV: {e}")
            raise

    def _get_column(self, key: str) -> Optional[str]:
        """Get actual column name from possible variations"""
        possible_names = self.column_mappings.get(key, [])

        for name in possible_names:
            if name in self.raw_df.columns:
                return name

        return None

    def _detect_slate_type(self) -> str:
        """Detect if this is a showdown or classic slate"""
        pos_col = self._get_column('position')

        if not pos_col:
            return "classic"

        positions = set(self.raw_df[pos_col].unique())

        # Check for showdown positions
        if 'CPT' in positions or 'UTIL' in positions:
            return "showdown"

        return "classic"

    def _process_classic_csv(self) -> List[UnifiedPlayer]:
        """Process standard DraftKings CSV"""
        players = []

        # Get column names
        name_col = self._get_column('name')
        pos_col = self._get_column('position')
        team_col = self._get_column('team')
        salary_col = self._get_column('salary')
        proj_col = self._get_column('projection')
        game_col = self._get_column('game_info')
        order_col = self._get_column('batting_order')

        for idx, row in self.raw_df.iterrows():
            try:
                # Extract base data
                name = row.get(name_col, '')
                position = row.get(pos_col, '')
                team = row.get(team_col, '')
                salary = int(row.get(salary_col, 0))
                projection = float(row.get(proj_col, 0))
                game_info = row.get(game_col, '') if game_col else ''

                # Skip if missing critical data
                if not name or not position or salary == 0:
                    continue

                # Parse opponent from game info
                opponent = self._parse_opponent(team, game_info)

                # Handle multi-position players
                positions = self._parse_positions(position)
                primary_position = positions[0]

                # Create player ID
                player_id = f"{name.replace(' ', '_')}_{team}".lower()

                # Create UnifiedPlayer
                player = UnifiedPlayer(
                    id=player_id,
                    name=name,
                    team=team,
                    salary=salary,
                    primary_position=primary_position,
                    positions=positions,
                    base_projection=projection
                )

                # Add extra attributes
                player.opponent = opponent
                player.game_info = game_info
                player.dff_projection = projection  # Store original projection

                # Add batting order if available
                if order_col and pd.notna(row.get(order_col)):
                    player.batting_order = int(row.get(order_col))

                players.append(player)

            except Exception as e:
                logger.warning(f"Failed to process row {idx}: {e}")
                continue

        return players

    def _process_showdown_csv(self) -> List[UnifiedPlayer]:
        """
        Process showdown CSV - ONLY use UTIL entries
        CPT entries are filtered out (they're just duplicates with higher salary)
        """
        logger.info("⚡ Processing SHOWDOWN slate")

        # Get column names
        pos_col = self._get_column('position')

        # Filter to UTIL only
        util_df = self.raw_df[self.raw_df[pos_col] == 'UTIL'].copy()
        logger.info(f"📊 Found {len(util_df)} UTIL players (filtering out CPT duplicates)")

        # Process like classic but with UTIL position
        players = []

        name_col = self._get_column('name')
        team_col = self._get_column('team')
        salary_col = self._get_column('salary')
        proj_col = self._get_column('projection')
        game_col = self._get_column('game_info')

        for idx, row in util_df.iterrows():
            try:
                name = row.get(name_col, '')
                team = row.get(team_col, '')
                salary = int(row.get(salary_col, 0))
                projection = float(row.get(proj_col, 0))
                game_info = row.get(game_col, '') if game_col else ''

                if not name or salary == 0:
                    continue

                # For showdown, all players are UTIL
                player_id = f"{name.replace(' ', '_')}_{team}_util".lower()

                player = UnifiedPlayer(
                    id=player_id,
                    name=name,
                    team=team,
                    salary=salary,
                    primary_position='UTIL',
                    positions=['UTIL'],
                    base_projection=projection
                )

                # Parse opponent for showdown
                player.opponent = self._parse_opponent(team, game_info)
                player.game_info = game_info
                player.dff_projection = projection
                player.is_showdown = True

                players.append(player)

            except Exception as e:
                logger.warning(f"Failed to process showdown row {idx}: {e}")
                continue

        return players

    def _parse_opponent(self, team: str, game_info: str) -> str:
        """Parse opponent from game info string like 'TB@BOS' """
        if not game_info or '@' not in game_info:
            return ''

        try:
            # Remove time info if present
            game_part = game_info.split(' ')[0]
            teams = game_part.split('@')

            if len(teams) == 2:
                away_team = teams[0].strip()
                home_team = teams[1].strip()

                # Return the opponent
                return home_team if team == away_team else away_team
        except:
            pass

        return ''

    def _parse_positions(self, position_str: str) -> List[str]:
        """
        Parse position string and handle multi-position players
        Also maps pitcher positions (SP/RP) to 'P'
        """
        # Split multi-position
        positions = position_str.split('/')

        # Map pitcher positions
        mapped_positions = []
        for pos in positions:
            pos = pos.strip()

            # Map SP and RP to P for optimizer
            if pos in ['SP', 'RP']:
                if 'P' not in mapped_positions:
                    mapped_positions.append('P')
            else:
                mapped_positions.append(pos)

        return mapped_positions if mapped_positions else [position_str]

    def _log_slate_info(self):
        """Log information about the loaded slate"""
        if not self.processed_players:
            return

        # Team distribution
        teams = {}
        positions = {}

        for player in self.processed_players:
            # Count teams
            teams[player.team] = teams.get(player.team, 0) + 1

            # Count positions
            pos = player.primary_position
            positions[pos] = positions.get(pos, 0) + 1

        # Log summary
        logger.info("📊 Slate Summary:")
        logger.info(f"   Total players: {len(self.processed_players)}")
        logger.info(f"   Teams: {len(teams)} ({', '.join(sorted(teams.keys()))})")

        # Position breakdown
        logger.info("   Position breakdown:")
        for pos, count in sorted(positions.items()):
            logger.info(f"     {pos}: {count}")

        # Salary info
        salaries = [p.salary for p in self.processed_players]
        if salaries:
            logger.info(f"   Salary range: ${min(salaries):,} - ${max(salaries):,}")
            logger.info(f"   Avg salary: ${sum(salaries) / len(salaries):,.0f}")

        # Games (for classic slates)
        if self.slate_type == "classic":
            games = set()
            for player in self.processed_players:
                if player.game_info:
                    game = player.game_info.split(' ')[0]  # Remove time
                    games.add(game)
            logger.info(f"   Games: {len(games)}")

    def get_player_by_name(self, name: str) -> Optional[UnifiedPlayer]:
        """Get a player by name (useful for testing)"""
        for player in self.processed_players:
            if player.name.lower() == name.lower():
                return player
        return None

    def get_players_by_team(self, team: str) -> List[UnifiedPlayer]:
        """Get all players from a specific team"""
        return [p for p in self.processed_players if p.team == team]

    def get_players_by_position(self, position: str) -> List[UnifiedPlayer]:
        """Get all players at a specific position"""
        return [p for p in self.processed_players
                if position in p.positions or p.primary_position == position]


# Integration with UnifiedCoreSystemV2
def integrate_csv_loader(core_system):
    """
    Add CSV loading capability to UnifiedCoreSystemV2
    This function patches the existing system
    """

    def load_players_from_csv(self, csv_path: str) -> List[UnifiedPlayer]:
        """Enhanced CSV loading with proper handling"""
        loader = CSVLoaderV2()

        try:
            # Load and process CSV
            players, slate_type = loader.load_csv(csv_path)

            # Store in system
            self.all_players = players
            self.slate_type = slate_type

            # Update confirmation system if available
            if hasattr(self, 'confirmation') and hasattr(self.confirmation, 'csv_players'):
                self.confirmation.csv_players = players

                # Rebuild team set
                teams = {p.team for p in players}
                self.confirmation.csv_teams = teams
                logger.info(f"Updated confirmation system with teams: {sorted(teams)}")

            return players

        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            raise

    # Patch the method onto the core system
    core_system.load_players_from_csv = load_players_from_csv.__get__(core_system, type(core_system))
    core_system.csv_loader = CSVLoaderV2()

    logger.info("✅ CSV Loader integrated with Core System V2")


# Example usage
if __name__ == "__main__":
    # Test the CSV loader standalone
    loader = CSVLoaderV2()

    # Example: Load a DraftKings CSV
    # players, slate_type = loader.load_csv("sample_data/DKSalaries.csv")

    print("CSV Loader V2 ready for use!")
    print("\nTo integrate with your system:")
    print("1. Import this module")
    print("2. Call integrate_csv_loader(your_core_system)")
    print("3. Use your_core_system.load_players_from_csv(filepath)")