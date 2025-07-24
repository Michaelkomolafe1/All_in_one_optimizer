#!/usr/bin/env python3
"""
UNIFIED CORE SYSTEM - FIXED VERSION
===================================
Complete unified DFS system with correlation-aware scoring
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd


# Core imports
from unified_player_model import UnifiedPlayer
from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig
from fixed_showdown_optimization import ShowdownOptimizer

# NEW: Import the integrated scoring system instead of old engines
try:
    from integrated_scoring_system import IntegratedScoringEngine
except ImportError:
    # Fallback to SimplifiedScoringEngine if integrated not available yet
    from step2_updated_player_model import SimplifiedScoringEngine as IntegratedScoringEngine

# Import cash optimization config
from cash_optimization_config import apply_contest_config, get_contest_description

# NEW: Import fixed showdown optimization
from fixed_showdown_optimization import ShowdownOptimizer

# Data enrichment imports
from simple_statcast_fetcher import FastStatcastFetcher
from smart_confirmation_system import SmartConfirmationSystem
from vegas_lines import VegasLines

# Optional weather integration
try:
    from weather_integration import get_weather_integration

    WEATHER_AVAILABLE = True
except ImportError:
    WEATHER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Weather integration not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedCoreSystem:
    """Main orchestrator for the DFS optimization system"""

    def __init__(self):
        """Initialize the unified system"""
        logger.info("Initializing Unified Core System...")

        # Core components
        self.players: List[UnifiedPlayer] = []
        self.player_pool: List[UnifiedPlayer] = []
        self.confirmed_players: Set[str] = set()
        self.manual_selections: Set[str] = set()

        # Initialize components
        self.optimizer = UnifiedMILPOptimizer()

        # NEW: Use integrated scoring engine
        self.scoring_engine = IntegratedScoringEngine()

        # NEW: Initialize showdown optimizer
        self.showdown_optimizer = ShowdownOptimizer(self.optimizer)


        # Data sources - initialize without csv_players
        self.confirmation_system = SmartConfirmationSystem(csv_players=None)
        self.statcast_fetcher = FastStatcastFetcher()
        self.vegas_lines = VegasLines()

        # Weather integration (optional)
        if WEATHER_AVAILABLE:
            self.weather_system = get_weather_integration()
        else:
            self.weather_system = None

        # State tracking
        self.csv_loaded = False
        self.confirmations_fetched = False
        self.enrichments_applied = False

        logger.info("✅ Unified Core System initialized successfully")

    def load_players_from_csv(self, csv_path: str) -> List[UnifiedPlayer]:
        """Load players from DraftKings CSV"""
        logger.info(f"Loading players from {csv_path}")

        try:
            df = pd.read_csv(csv_path)
            self.players = []

            for idx, row in df.iterrows():
                # Extract data from CSV row - DraftKings format
                # Handle different column name variations
                name = row.get('Name', row.get('name', ''))
                position = row.get('Position', row.get('Pos', ''))
                team = row.get('TeamAbbrev', row.get('Team', ''))
                salary = int(row.get('Salary', 0))

                # Handle game info to extract opponent
                game_info = row.get('Game Info', row.get('GameInfo', ''))
                opponent = ''
                if game_info and '@' in game_info:
                    # Parse "TB@BOS" format
                    teams = game_info.split('@')
                    if team == teams[0]:
                        opponent = teams[1]
                    else:
                        opponent = teams[0]

                # Generate unique ID
                player_id = f"{name.replace(' ', '_')}_{team}".lower()

                # Parse positions (handle multi-position)
                positions = position.split('/')
                primary_position = positions[0]

                # Map pitcher positions to 'P' for optimizer
                if primary_position in ['SP', 'RP']:
                    primary_position = 'P'
                    positions = ['P'] + [p for p in positions if p not in ['SP', 'RP']]

                # Get base projection (may be in different columns)
                base_projection = float(row.get('AvgPointsPerGame',
                                                row.get('Projection',
                                                        row.get('proj', 0))))

                # Create UnifiedPlayer instance
                player = UnifiedPlayer(
                    id=player_id,
                    name=name,
                    team=team,
                    salary=salary,
                    primary_position=primary_position,
                    positions=positions,
                    base_projection=base_projection
                )

                # Add additional attributes
                player.opponent = opponent
                player.game_info = game_info

                # Add any other available data
                if 'batting_order' in row:
                    player.batting_order = int(row['batting_order'])

                # Store DFF projection if available
                player.dff_projection = base_projection

                self.players.append(player)

            self.csv_loaded = True
            logger.info(f"✅ Loaded {len(self.players)} players from CSV")

            # Pass players to confirmation system if it supports it
            if hasattr(self, 'confirmation_system') and hasattr(self.confirmation_system, 'csv_players'):
                self.confirmation_system.csv_players = self.players
                # Rebuild the team set with the new players
                if hasattr(self.confirmation_system, '_build_team_set'):
                    self.confirmation_system.csv_teams = self.confirmation_system._build_team_set()
                    logger.info(f"Updated confirmation system with teams: {sorted(self.confirmation_system.csv_teams)}")

            return self.players

        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            raise

    def load_csv(self, csv_path: str) -> List[UnifiedPlayer]:
        """Alias for load_players_from_csv for compatibility"""
        return self.load_players_from_csv(csv_path)

    def fetch_confirmed_players(self) -> Set[str]:
        """Fetch confirmed starting lineups"""
        logger.info("Fetching confirmed players...")

        try:
            # Call get_all_confirmations to fetch data
            self.confirmation_system.get_all_confirmations()

            # Now extract the actual player names
            all_names = []

            # Get pitcher names
            for team, pitcher_info in self.confirmation_system.confirmed_pitchers.items():
                if isinstance(pitcher_info, dict) and 'name' in pitcher_info:
                    all_names.append(pitcher_info['name'])

            # Get position player names
            for team, lineup in self.confirmation_system.confirmed_lineups.items():
                if isinstance(lineup, list):
                    for player in lineup:
                        if isinstance(player, dict) and 'name' in player:
                            all_names.append(player['name'])

            self.confirmed_players = set(all_names)
            logger.info(f"✅ Found {len(self.confirmed_players)} confirmed players")

            if self.confirmed_players and self.csv_loaded:
                # Debug: Show some confirmed names
                logger.info(f"Sample confirmed: {list(self.confirmed_players)[:3]}")

            self.confirmations_fetched = True
            return self.confirmed_players

        except Exception as e:
            logger.warning(f"Could not fetch confirmations: {e}")
            self.confirmed_players = set()
            return self.confirmed_players

    def set_manual_selections(self, player_names: List[str]):
        """Set manual player selections"""
        self.manual_selections = set(player_names)
        logger.info(f"Set {len(self.manual_selections)} manual selections")

    def build_player_pool(self, include_unconfirmed: bool = False):
        """Build the player pool for optimization"""
        logger.info("Building player pool...")

        if not self.csv_loaded:
            raise ValueError("No CSV loaded. Call load_players_from_csv first.")

        # Detect if showdown slate BEFORE building pool
        all_positions = {p.primary_position for p in self.players}
        is_showdown = 'CPT' in all_positions or 'UTIL' in all_positions

        self.player_pool = []
        matches = 0

        for player in self.players:
            # SHOWDOWN: Skip CPT entries - only use UTIL
            if is_showdown and player.primary_position == 'CPT':
                continue

            # Include if manually selected
            if player.name in self.manual_selections:
                self.player_pool.append(player)
                continue

            # Include if confirmed
            if player.name in self.confirmed_players:
                self.player_pool.append(player)
                player.is_confirmed = True
                matches += 1
                continue

            # Include unconfirmed if requested
            if include_unconfirmed:
                self.player_pool.append(player)

        logger.info(f"✅ Built player pool with {len(self.player_pool)} players")
        logger.info(f"   Slate type: {'SHOWDOWN' if is_showdown else 'CLASSIC'}")
        logger.info(f"   Confirmed matches: {matches}")

    def debug_player_matching(self):
        """Debug method to show why players aren't matching"""
        print("\n" + "=" * 60)
        print("PLAYER MATCHING DEBUG")
        print("=" * 60)

        print(f"\nConfirmed players from API ({len(self.confirmed_players)}):")
        for i, name in enumerate(list(self.confirmed_players)[:10]):
            print(f"  {i + 1}. '{name}'")

        print(f"\nCSV players ({len(self.players)}):")
        for i, player in enumerate(self.players[:10]):
            print(f"  {i + 1}. '{player.name}' - {player.team} - ${player.salary}")

        # Try to find why they don't match
        if self.confirmed_players and self.players:
            conf_name = list(self.confirmed_players)[0]
            csv_name = self.players[0].name

            print(f"\nComparing first entries:")
            print(f"  Confirmed: '{conf_name}' (length: {len(conf_name)})")
            print(f"  CSV:       '{csv_name}' (length: {len(csv_name)})")
            print(f"  Equal: {conf_name == csv_name}")
            print(f"  Equal (lower): {conf_name.lower() == csv_name.lower()}")

            # Check for hidden characters
            print(f"\nChecking for hidden characters:")
            print(f"  Confirmed bytes: {conf_name.encode('utf-8')}")
            print(f"  CSV bytes:       {csv_name.encode('utf-8')}")

    def enrich_player_pool(self):
        """Enrich player pool with additional data"""
        if not self.player_pool:
            logger.warning("No players in pool to enrich")
            return

        logger.info("Enriching player pool with additional data...")

        # Get current date info
        today = datetime.now().strftime('%Y-%m-%d')

        # Enrich with Statcast data
        # Enrich with Statcast data
        try:
            logger.info("Fetching Statcast data...")
            # Temporarily disabled - method doesn't exist
            pass
        except Exception as e:
            logger.warning(f"Could not fetch Statcast data: {e}")

        # Enrich with Vegas lines
        # Enrich with Vegas lines
        try:
            logger.info("Fetching Vegas lines...")
            # Set default values for all players
            for player in self.player_pool:
                player.team_total = 4.5  # Default team total
                player.game_total = 9.0  # Default game total
        except Exception as e:
            logger.warning(f"Could not fetch Vegas lines: {e}")

        # Enrich with weather data (if available)
        # Temporarily disabled - method doesn't exist
        pass

        self.enrichments_applied = True
        logger.info("✅ Player pool enrichment complete")

    def set_confirmed_players(self, confirmed_list: List[str]):
        """Manually set confirmed players (for testing)"""
        self.confirmed_players = set(confirmed_list)
        self.confirmations_fetched = True
        logger.info(f"Manually set {len(self.confirmed_players)} confirmed players")

    def detect_showdown_slate(self) -> bool:
        """Detect if this is a showdown slate"""
        if not self.player_pool:
            return False

        # Check if any player has CPT or UTIL position
        positions = {p.primary_position for p in self.player_pool}
        return 'CPT' in positions or 'UTIL' in positions

    def optimize_showdown_lineups(
            self,
            num_lineups: int = 20,
            strategy: str = "balanced",
            min_unique_players: int = 3,
            contest_type: str = "gpp"
    ) -> List[Dict]:
        """Optimize showdown lineups using fixed implementation"""
        if not self.player_pool:
            logger.error("No players in pool!")
            return []

        # Use the fixed showdown optimizer
        showdown_opt = ShowdownOptimizer(self.optimizer)

        # Filter to UTIL players only (ignore CPT entries)
        util_players = [p for p in self.player_pool if p.primary_position != 'CPT']

        logger.info(f"Showdown optimization with {len(util_players)} UTIL players")

        # Generate lineups
        return showdown_opt.generate_diverse_lineups(
            util_players,
            num_lineups
        )

    def optimize_lineups(self, num_lineups: int = 1, strategy: str = "balanced",
                         min_unique_players: int = 3, contest_type: str = "gpp") -> List[Dict]:
        """Generate optimized lineups from the player pool"""
        if not self.player_pool:
            logger.error("No players in pool! Build player pool first.")
            return []

        # Auto-detect showdown slates
        if self.detect_showdown_slate():
            logger.info("Showdown slate detected! Using showdown optimizer...")
            return self.optimize_showdown_lineups(
                num_lineups=num_lineups,
                strategy=strategy,
                min_unique_players=min_unique_players,
                contest_type=contest_type
            )

        # Continue with classic optimization...

        # Regular optimization
        logger.info(f"🎯 Optimizing {num_lineups} lineups...")
        logger.info(f"   Strategy: {strategy}")
        logger.info(f"   Contest Type: {contest_type}")
        logger.info(f"   Pool size: {len(self.player_pool)} players")

        # Set scoring engine mode based on contest type
        scoring_method = self.scoring_engine.set_contest_type(contest_type)
        logger.info(f"   Scoring Method: {scoring_method}")

        # Apply contest-specific configuration
        contest_config = apply_contest_config(self.optimizer, contest_type)

        # Print contest configuration
        logger.info(f"📋 Contest Configuration:")
        for line in get_contest_description(contest_type).split('\n'):
            logger.info(f"   {line}")

        # Calculate scores with the selected engine
        logger.info("📊 Calculating player scores...")
        for player in self.player_pool:
            score = self.scoring_engine.calculate_score(player)
            player.enhanced_score = score
            player.optimization_score = score

        # Generate lineups
        lineups = []
        used_players = set()

        for i in range(num_lineups):
            logger.info(f"\n   Lineup {i + 1}/{num_lineups}...")

            # Apply diversity penalty if needed
            if i > 0 and min_unique_players > 0:
                self._apply_diversity_penalty(used_players, penalty=0.8)

            # Optimize single lineup
            lineup_players, total_score = self.optimizer.optimize_lineup(
                players=self.player_pool,
                strategy=strategy,
                manual_selections=list(self.manual_selections)
            )

            # Restore original scores
            self._restore_original_scores()

            if lineup_players:
                # Track used players
                for player in lineup_players:
                    used_players.add(player.name)

                # Create lineup dictionary
                lineup_dict = {
                    'players': lineup_players,
                    'total_salary': sum(p.salary for p in lineup_players),
                    'total_score': total_score,
                    'strategy': strategy,
                    'contest_type': contest_type
                }

                lineups.append(lineup_dict)

                # Log lineup summary
                self._log_lineup_summary(lineup_dict, i + 1)

        logger.info(f"\n✅ Generated {len(lineups)} optimized lineups")
        return lineups

    def _apply_diversity_penalty(self, used_players: Set[str], penalty: float = 0.8):
        """Apply penalty to previously used players"""
        for player in self.player_pool:
            if player.name in used_players:
                player.temp_score = player.optimization_score
                player.optimization_score *= penalty

    def _restore_original_scores(self):
        """Restore original optimization scores"""
        for player in self.player_pool:
            if hasattr(player, 'temp_score'):
                player.optimization_score = player.temp_score
                delattr(player, 'temp_score')

    def _log_lineup_summary(self, lineup: Dict, lineup_num: int):
        """Log a summary of the lineup"""
        total_salary = lineup['total_salary']
        total_score = lineup['total_score']

        logger.info(f"   ✓ Lineup {lineup_num}: ${total_salary:,} salary, {total_score:.1f} projected points")

        # Count stacks
        team_counts = {}
        for player in lineup['players']:
            team = player.team
            team_counts[team] = team_counts.get(team, 0) + 1

        stacks = [(team, count) for team, count in team_counts.items() if count >= 2]
        if stacks:
            stack_str = ", ".join([f"{team}({count})" for team, count in stacks])
            logger.info(f"   ✓ Stacks: {stack_str}")

    def export_lineups(self, lineups: List[Dict], filename: str = None):
        """Export lineups to CSV"""
        if not lineups:
            logger.warning("No lineups to export")
            return

        if filename is None:
            filename = f"lineups_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Convert to DataFrame format
        rows = []
        for i, lineup in enumerate(lineups):
            row = {'Lineup': i + 1}

            # Add players by position
            positions = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
            pos_counts = {}

            for pos in positions:
                for player in lineup['players']:
                    if player.primary_position == pos or pos in player.primary_position:
                        col_name = f"{pos}{pos_counts.get(pos, 1)}" if pos_counts.get(pos, 0) > 0 else pos
                        row[col_name] = player.name
                        pos_counts[pos] = pos_counts.get(pos, 0) + 1
                        break

            row['Salary'] = lineup['total_salary']
            row['Projection'] = lineup['total_score']
            rows.append(row)

        # Save to CSV
        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False)
        logger.info(f"✅ Exported {len(lineups)} lineups to {filename}")

        return filename


# Example usage
if __name__ == "__main__":
    # Test the system
    system = UnifiedCoreSystem()

    # Example workflow
    print("Unified Core System initialized successfully!")
    print("\nExample usage:")
    print("1. system.load_players_from_csv('DKSalaries.csv')")
    print("2. system.fetch_confirmed_players()")
    # ===== ADD THIS DEBUG CODE HERE =====
    print("\n🔍 STEP 1: DEBUGGING CONFIRMATION DATA")
    print("=" * 60)

    # Check what get_all_confirmations actually returns
    try:
        raw_confirmations = system.confirmation_system.get_all_confirmations()
        print(f"Type of confirmation data: {type(raw_confirmations)}")
        print(f"Number of items: {len(raw_confirmations) if hasattr(raw_confirmations, '__len__') else 'N/A'}")

        # Show first few items
        if isinstance(raw_confirmations, list):
            print("\nFirst 5 items:")
            for i, item in enumerate(raw_confirmations[:5]):
                print(f"  {i}: {item} (type: {type(item)})")
        elif isinstance(raw_confirmations, dict):
            print("\nFirst 5 key-value pairs:")
            for i, (key, value) in enumerate(list(raw_confirmations.items())[:5]):
                print(f"  {key}: {value} (type: {type(value)})")
        else:
            print(f"Unexpected type: {raw_confirmations}")

    except Exception as e:
        print(f"ERROR getting confirmations: {e}")

    print("\n" + "-" * 60)
    print("3. system.build_player_pool()")
    print("4. system.enrich_player_pool()")
    print("5. lineups = system.optimize_lineups(num_lineups=20, contest_type='gpp')")
    print("6. system.export_lineups(lineups)")