#!/usr/bin/env python3
"""
UNIFIED CORE SYSTEM - UPDATED VERSION
=====================================
Integrates new scoring, smart enrichment, and proper lineup projections
"""

import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Core imports - all at the top!
from .unified_player_model import UnifiedPlayer
from .unified_milp_optimizer import UnifiedMILPOptimizer
from .enhanced_scoring_engine_v2 import EnhancedScoringEngineV2
from .smart_enrichment_manager import SmartEnrichmentManager
from .gui_strategy_configuration import GUIStrategyManager
from .correlation_scoring_config import CorrelationScoringConfig

# Data enrichment imports with error handling
try:
    from real_data_enrichments import RealStatcastFetcher as SimpleStatcastFetcher
    STATCAST_AVAILABLE = True
    logger.info("✅ Statcast initialized")
except ImportError:
    logger.warning("Statcast not available")
    STATCAST_AVAILABLE = False
    SimpleStatcastFetcher = None

try:
    from smart_confirmation import SmartConfirmationSystem
    CONFIRMATION_AVAILABLE = True
except ImportError:
    logger.warning("Smart confirmation not available")
    CONFIRMATION_AVAILABLE = False
    SmartConfirmationSystem = None

try:
    from vegas_lines import VegasLines
    VEGAS_AVAILABLE = True
    logger.info("✅ Vegas lines initialized")
except ImportError:
    logger.warning("Vegas lines not available")
    VEGAS_AVAILABLE = False
    VegasLines = None


class UnifiedCoreSystem:
    """
    UPDATED core system with:
    1. Smart enrichment based on slate/strategy
    2. Unified scoring path
    3. Proper lineup projections
    """

    def __init__(self):
        """Initialize the unified DFS system"""
        # Player data
        self.players = []
        self.player_pool = []

        # FIRST: Create managers (before data sources)
        self.scoring_engine = EnhancedScoringEngineV2()
        self.enrichment_manager = SmartEnrichmentManager()
        self.strategy_manager = GUIStrategyManager()

        # Optimizer
        self.config = CorrelationScoringConfig()
        self.optimizer = UnifiedMILPOptimizer(self.config)

        # THEN: Initialize data sources
        # 1. Confirmations
        self.confirmation_system = None
        if CONFIRMATION_AVAILABLE:
            try:
                self.confirmation_system = SmartConfirmationSystem()
                self.enrichment_manager.set_enrichment_source('confirmations', self.confirmation_system)
                logger.info("✅ Confirmations initialized")
            except Exception as e:
                logger.warning(f"Confirmation system error: {e}")

        # 2. Statcast
        self.stats_fetcher = None
        if STATCAST_AVAILABLE:
            try:
                self.stats_fetcher = SimpleStatcastFetcher()
                self.enrichment_manager.set_enrichment_source('statcast', self.stats_fetcher)
                logger.info("✅ Statcast initialized")
            except Exception as e:
                logger.warning(f"Statcast error: {e}")

        # 3. Vegas
        self.vegas_lines = None
        if VEGAS_AVAILABLE:
            try:
                self.vegas_lines = VegasLines()
                self.enrichment_manager.set_enrichment_source('vegas', self.vegas_lines)
                logger.info("✅ Vegas lines initialized")
            except Exception as e:
                logger.warning(f"Vegas error: {e}")

        # 4. Weather (NEW)
        self.weather = None
        try:
            from weather_integration import get_weather_integration
            self.weather = get_weather_integration()
            self.enrichment_manager.set_enrichment_source('weather', self.weather)
            logger.info("✅ Weather integration initialized")
        except ImportError as e:
            logger.warning(f"Weather integration not available: {e}")

        # 5. Ownership (NEW)
        self.ownership_calculator = None
        try:
            from ownership_calculator import OwnershipCalculator
            self.ownership_calculator = OwnershipCalculator()
            self.enrichment_manager.set_enrichment_source('ownership', self.ownership_calculator)
            logger.info("✅ Ownership calculator initialized")
        except ImportError as e:
            logger.warning(f"Ownership calculator not available: {e}")

        # State tracking
        self.csv_loaded = False
        self.current_slate_size = None
        self.current_contest_type = None
        self.current_strategy = None
        self.detected_games = 0
        self.slate_size_category = None

        # Logging
        self.log_messages = []

    def log(self, message: str):
        """Add timestamped log message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)
        logger.info(message)

    def load_csv(self, filepath: str) -> int:
        """Load players from DraftKings CSV with proper slate detection"""
        logger.info(f"Loading CSV: {filepath}")

        try:
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} rows from CSV")

            # Convert to UnifiedPlayer objects
            self.players = []
            for idx, row in df.iterrows():
                try:
                    player = UnifiedPlayer.from_csv_row(row.to_dict())
                    self.players.append(player)
                except Exception as e:
                    logger.debug(f"Error loading player at row {idx}: {e}")

            self.csv_loaded = True
            logger.info(f"Successfully loaded {len(self.players)} players")

            # DETECT SLATE CHARACTERISTICS
            # Count unique games to determine slate size
            games = set()
            for player in self.players:
                # Create game identifier from team and opponent
                if hasattr(player, 'team') and hasattr(player, 'opponent'):
                    game = tuple(sorted([player.team, player.opponent]))
                    games.add(game)

            # Store number of games (CRITICAL FIX)
            self.detected_games = len(games)

            # Determine slate size category
            if self.detected_games <= 4:
                slate_size_str = 'small'
            elif self.detected_games <= 9:
                slate_size_str = 'medium'
            else:
                slate_size_str = 'large'

            # STORE BOTH VERSIONS (fixes the type error)
            self.current_slate_size = self.detected_games  # Store as INTEGER
            self.slate_size_category = slate_size_str  # Store as STRING

            logger.info(f"Detected: {self.detected_games} games = {slate_size_str} slate")

            # Initialize projections for all players
            for player in self.players:
                if not hasattr(player, 'base_projection') or player.base_projection is None:
                    # Use AvgPointsPerGame or default
                    if hasattr(player, 'AvgPointsPerGame') and player.AvgPointsPerGame:
                        player.base_projection = float(player.AvgPointsPerGame)
                    else:
                        # Default projections by position
                        pos_defaults = {
                            'P': 15.0, 'SP': 15.0, 'RP': 10.0,
                            'C': 8.0, '1B': 10.0, '2B': 9.0,
                            '3B': 9.0, 'SS': 9.0, 'OF': 9.0
                        }
                        player.base_projection = pos_defaults.get(player.primary_position, 8.0)

                # Initialize other scores
                player.projection = player.base_projection
                player.optimization_score = player.base_projection
                player.gpp_score = player.base_projection
                player.cash_score = player.base_projection

            return len(self.players)

        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def detect_slate_characteristics(self):
        """Auto-detect slate size and type"""
        if not self.players:
            return

        # Count unique teams to estimate games
        teams = set(p.team for p in self.players if hasattr(p, 'team'))
        num_games = len(teams) // 2

        # Determine slate size
        if num_games <= 4:
            self.current_slate_size = 'small'
        elif num_games <= 9:
            self.current_slate_size = 'medium'
        else:
            self.current_slate_size = 'large'

        self.log(f"Detected: {num_games} games = {self.current_slate_size} slate")

    def fetch_confirmed_players(self) -> int:
        """Fetch confirmed lineups with proper tuple handling"""
        try:
            # Import confirmation system
            from smart_confirmation import UniversalSmartConfirmation

            # Reinitialize with CSV players for proper team tracking
            self.log("Reinitializing confirmation system with CSV players...")
            self.confirmation_system = UniversalSmartConfirmation(
                csv_players=self.players,
                verbose=False  # Less verbose for GUI
            )

            # Fetch confirmations - returns (lineup_count, pitcher_count)
            self.log("Fetching MLB confirmed lineups...")
            result = self.confirmation_system.get_all_confirmations()

            # Handle tuple return
            if isinstance(result, tuple):
                lineup_count, pitcher_count = result
                self.log(f"MLB API: {lineup_count} position players, {pitcher_count} pitchers")
            else:
                self.log("Unexpected return format from confirmations")
                return 0

            # Match confirmed players to CSV players
            confirmed_count = 0

            # Process lineups
            if hasattr(self.confirmation_system, 'confirmed_lineups'):
                for team, lineup in self.confirmation_system.confirmed_lineups.items():
                    for player_info in lineup:
                        if isinstance(player_info, dict):
                            mlb_name = player_info.get('name', '')
                            batting_order = player_info.get('order', 0)
                        else:
                            mlb_name = str(player_info)
                            batting_order = 0

                        # Try to match with CSV players
                        for p in self.players:
                            if p.team == team and self._fuzzy_match_names(p.name, mlb_name):
                                p.is_confirmed = True
                                p.batting_order = batting_order
                                confirmed_count += 1
                                break

            # Process pitchers
            if hasattr(self.confirmation_system, 'confirmed_pitchers'):
                for team, pitcher_info in self.confirmation_system.confirmed_pitchers.items():
                    if isinstance(pitcher_info, dict):
                        mlb_name = pitcher_info.get('name', '')
                    else:
                        mlb_name = str(pitcher_info)

                    # Match pitchers
                    for p in self.players:
                        if p.team == team and p.position in ['P', 'SP'] and self._fuzzy_match_names(p.name, mlb_name):
                            p.is_confirmed = True
                            p.is_starting_pitcher = True
                            confirmed_count += 1
                            break

            self.log(f"Matched {confirmed_count} confirmed players to CSV")
            return confirmed_count

        except Exception as e:
            self.log(f"Error in confirmations: {e}")
            return 0

    def _fuzzy_match_names(self, csv_name: str, mlb_name: str) -> bool:
        """Fuzzy name matching"""
        csv_clean = csv_name.upper().replace('.', '').replace(',', '').strip()
        mlb_clean = mlb_name.upper().replace('.', '').replace(',', '').strip()

        # Exact match
        if csv_clean == mlb_clean:
            return True

        # Last name match
        csv_last = csv_clean.split()[-1] if ' ' in csv_clean else csv_clean
        mlb_last = mlb_clean.split()[-1] if ' ' in mlb_clean else mlb_clean

        if csv_last == mlb_last:
            # Check first initial
            if csv_clean[0] == mlb_clean[0]:
                return True

        # Partial match
        if csv_clean in mlb_clean or mlb_clean in csv_clean:
            return True

        return False
    def _names_match(self, csv_name: str, mlb_name: str) -> bool:
        """Check if two names match (handles variations)"""
        # Clean names
        csv_clean = csv_name.upper().strip()
        mlb_clean = mlb_name.upper().strip()

        # Exact match
        if csv_clean == mlb_clean:
            return True

        # Remove common suffixes
        for suffix in [' JR.', ' JR', ' SR.', ' SR', ' III', ' II']:
            csv_clean = csv_clean.replace(suffix, '')
            mlb_clean = mlb_clean.replace(suffix, '')

        # Check again after cleaning
        if csv_clean == mlb_clean:
            return True

        # Last name match with first initial
        csv_parts = csv_clean.split()
        mlb_parts = mlb_clean.split()

        if len(csv_parts) >= 2 and len(mlb_parts) >= 2:
            # Same last name
            if csv_parts[-1] == mlb_parts[-1]:
                # First names start with same letter
                if csv_parts[0][0] == mlb_parts[0][0]:
                    return True

        # One name contains the other
        if csv_clean in mlb_clean or mlb_clean in csv_clean:
            return True

        return False

    def build_player_pool(self, include_unconfirmed: bool = False, manual_selections: set = None):
        """Build the player pool for optimization with small slate handling"""
        manual_selections = manual_selections or set()
        self.player_pool = []

        # Check slate size
        unique_teams = set(p.team for p in self.players if hasattr(p, 'team'))
        num_games = len(unique_teams) / 2 if unique_teams else 0

        # SMALL SLATE OVERRIDE
        if num_games <= 2 and not include_unconfirmed:
            self.log(
                f"WARNING: Only {num_games} games detected. Consider including unconfirmed players or adding manual selections.")

        # Debug logging
        self.log(f"Building pool: include_unconfirmed={include_unconfirmed}, manual={len(manual_selections)}")

        confirmed_count = 0
        projection_count = 0

        # Convert manual selections to list of names if it's a string
        if isinstance(manual_selections, str):
            manual_names = [name.strip() for name in manual_selections.split(',') if name.strip()]
        elif isinstance(manual_selections, set):
            manual_names = list(manual_selections)
        elif isinstance(manual_selections, list):
            manual_names = manual_selections
        else:
            manual_names = []

        for player in self.players:
            # Count players with projections
            if hasattr(player, 'base_projection') and player.base_projection > 0:
                projection_count += 1

            # Count confirmed players
            if hasattr(player, 'is_confirmed') and player.is_confirmed:
                confirmed_count += 1

            # MAIN LOGIC - Include player if:
            # 1. Has a valid projection AND
            # 2. Either include_unconfirmed is True OR player is confirmed OR manually selected

            has_projection = hasattr(player, 'base_projection') and player.base_projection > 0

            if not has_projection:
                continue  # Skip players without projections

            # Check if player name matches manual selection
            is_manually_selected = False
            if manual_names:
                # Check various name formats
                player_name_lower = player.name.lower()
                for manual_name in manual_names:
                    if manual_name.lower() in player_name_lower or player_name_lower in manual_name.lower():
                        is_manually_selected = True
                        break

            # Now check if we should include this player
            if include_unconfirmed:
                # Include ALL players with projections
                self.player_pool.append(player)
            elif is_manually_selected:
                # Always include manual selections
                player.is_manual_selected = True
                self.player_pool.append(player)
                self.log(f"  Added manual selection: {player.name}")
            elif hasattr(player, 'is_confirmed') and player.is_confirmed:
                # Include confirmed players
                self.player_pool.append(player)

        # POSITION CHECK for small slates
        if len(self.player_pool) < 50:
            position_counts = {}
            for p in self.player_pool:
                pos = 'P' if p.position in ['P', 'SP', 'RP'] else p.position
                position_counts[pos] = position_counts.get(pos, 0) + 1

            # Check if we have minimum positions
            missing_positions = []
            min_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

            for pos, needed in min_needed.items():
                if position_counts.get(pos, 0) < needed:
                    missing_positions.append(f"{pos}({needed - position_counts.get(pos, 0)} needed)")

            if missing_positions:
                self.log(f"⚠️ WARNING: Missing positions: {', '.join(missing_positions)}")
                self.log("  Consider adding manual selections for these positions")

        # Debug output
        self.log(f"Players with projections: {projection_count}")
        self.log(f"Confirmed players: {confirmed_count}")
        self.log(f"Player pool: {len(self.player_pool)} players")

        # Store slate size for later use
        self.current_slate_size = num_games

        return len(self.player_pool)


    def enrich_player_pool_smart(self, strategy: str, contest_type: str) -> Dict:
        """
        NEW METHOD: Smart enrichment based on strategy and slate
        """
        if not self.player_pool:
            self.log("No player pool to enrich")
            return {}

        if not self.current_slate_size:
            self.detect_slate_characteristics()

        self.log(f"Smart enrichment for {strategy} on {self.current_slate_size} {contest_type}")

        # Use smart enrichment manager
        self.player_pool = self.enrichment_manager.enrich_players(
            players=self.player_pool,
            slate_size=self.current_slate_size,
            strategy=strategy,
            contest_type=contest_type
        )

        # Count enrichments for reporting
        stats = {
            'vegas': sum(1 for p in self.player_pool if hasattr(p, 'implied_team_score') and p.implied_team_score > 0),
            'batting_order': sum(1 for p in self.player_pool if hasattr(p, 'batting_order') and p.batting_order > 0),
            'recent_form': sum(1 for p in self.player_pool if hasattr(p, 'recent_form')),
            'consistency': sum(1 for p in self.player_pool if hasattr(p, 'consistency_score'))
        }

        return stats

    def score_players(self, contest_type: str = 'gpp'):
        """Score all players in pool"""
        if not self.player_pool:
            logger.warning("No players in pool to score")
            return

        logger.info(f"Scoring {len(self.player_pool)} players for {contest_type}")

        # Check if already enriched to avoid double enrichment
        if not any(hasattr(p, 'implied_team_score') for p in self.player_pool[:5]):
            slate_size = 'small' if self.current_slate_size <= 4 else 'medium' if self.current_slate_size <= 9 else 'large'
            strategy = self.current_strategy or 'projection_monster'

            logger.info(f"Enriching players for {strategy} on {slate_size} {contest_type}")
            self.player_pool = self.enrichment_manager.enrich_players(
                players=self.player_pool,
                slate_size=slate_size,
                strategy=strategy,
                contest_type=contest_type
            )
        else:
            logger.info("Players already enriched, skipping")

        # Score players
        scored_count = 0
        for player in self.player_pool:
            if contest_type == 'cash':
                player.cash_score = self.scoring_engine.score_player_cash(player)
                player.optimization_score = player.cash_score
            else:  # GPP
                player.gpp_score = self.scoring_engine.score_player_gpp(player)
                player.optimization_score = player.gpp_score

            # FIX: Handle None values
            if player.optimization_score is not None and player.optimization_score > 0:
                scored_count += 1
            elif player.optimization_score is None:
                # Set default if None
                player.optimization_score = player.base_projection or 0
                logger.debug(f"Player {player.name} had None score, using base: {player.optimization_score}")

        logger.info(f"Scored {scored_count} players with non-zero scores")

        # Log top scorers
        top_players = sorted(
            [p for p in self.player_pool if p.optimization_score is not None],
            key=lambda p: p.optimization_score,
            reverse=True
        )[:3]

        for p in top_players:
            logger.info(f"  Top: {p.name} = {p.optimization_score:.1f}")

    def optimize_lineup(self, strategy: str = 'auto', contest_type: str = 'gpp',
                        num_lineups: int = 1, manual_selections: str = '') -> List:
        """Generate optimized lineups with ENRICHMENT"""

        logger.info("=== OPTIMIZATION PIPELINE ===")
        logger.info(f"Strategy: {strategy}, Contest: {contest_type}")

        # Auto-select strategy if needed
        if strategy == 'auto':
            # Ensure we have a numeric slate size
            num_games = self.detected_games if hasattr(self, 'detected_games') else 6
            strategy, reason = self.strategy_manager.auto_select_strategy(
                num_games,
                contest_type
            )
            logger.info(f"Auto-selected: {strategy}")

        self.current_strategy = strategy
        self.current_contest_type = contest_type

        # Handle both string and int slate sizes
        if isinstance(self.current_slate_size, str):
            # If it's already a string like 'medium', use it
            slate_size = self.current_slate_size
        elif isinstance(self.current_slate_size, int):
            # Convert number to size category
            slate_size = 'small' if self.current_slate_size <= 4 else 'medium' if self.current_slate_size <= 9 else 'large'
        else:
            # Default fallback
            num_games = self.detected_games if hasattr(self, 'detected_games') else 6
            slate_size = 'small' if num_games <= 4 else 'medium' if num_games <= 9 else 'large'

        logger.info(f"Smart enrichment for {strategy} on {slate_size} {contest_type}")

        # Enrich players before optimization
        self.player_pool = self.enrichment_manager.enrich_players(
            players=self.player_pool,
            slate_size=slate_size,
            strategy=strategy,
            contest_type=contest_type
        )

        # Log enrichment results
        enrichment_stats = {
            'vegas': 0,
            'recent_form': 0,
            'consistency': 0,
            'batting_order': 0
        }

        for p in self.player_pool[:10]:  # Check first 10
            if getattr(p, 'implied_team_score', 0) > 0:
                enrichment_stats['vegas'] += 1
            if getattr(p, 'recent_form', 0) != 0:
                enrichment_stats['recent_form'] += 1
            if getattr(p, 'consistency_score', 0) != 0:
                enrichment_stats['consistency'] += 1
            if getattr(p, 'batting_order', 0) > 0:
                enrichment_stats['batting_order'] += 1

        logger.info(f"Enriched: {enrichment_stats}")

        # Score players based on contest type
        self.score_players(contest_type)

        # Get valid players for optimization
        valid_players = [p for p in self.player_pool if p.optimization_score and p.optimization_score > 0]
        logger.info(f"Valid players for optimization: {len(valid_players)}")

        if not valid_players:
            logger.error("No valid players for optimization")
            return []

        # Set contest type on the optimizer config (if needed)
        if hasattr(self.optimizer, 'config') and hasattr(self.optimizer.config, 'contest_type'):
            self.optimizer.config.contest_type = contest_type

        # Generate lineups
        generated_lineups = []

        for i in range(num_lineups):
            logger.info(f"\nGenerating lineup {i + 1}/{num_lineups}")

            # Run MILP optimization
            # FIX: Handle OptimizationResult object
            result = self.optimizer.optimize(
                players=valid_players,
                strategy=strategy,
                manual_selections=manual_selections
            )

            # Handle different result types
            if result:
                # Check if it's an object with attributes
                if hasattr(result, 'lineup') and hasattr(result, 'score'):
                    lineup = result.lineup
                    score = result.score
                # Check if it's a tuple (old format)
                elif isinstance(result, tuple) and len(result) == 2:
                    lineup, score = result
                # Check if it's just a list of players
                elif isinstance(result, list):
                    lineup = result
                    score = sum(p.optimization_score for p in lineup)
                else:
                    # Try to extract lineup from the result object
                    lineup = getattr(result, 'lineup', None) or getattr(result, 'players', None)
                    score = getattr(result, 'score', 0) or getattr(result, 'total_score', 0)

                if lineup:
                    # Convert to dict format for GUI
                    lineup_dict = {
                        'players': [self._player_to_dict(p) for p in lineup],
                        'score': score,
                        'projection': sum(p.base_projection for p in lineup),
                        'salary': sum(p.salary for p in lineup),
                        'strategy': strategy,
                        'contest_type': contest_type
                    }
                    generated_lineups.append(lineup_dict)
                    logger.info(
                        f"Lineup {i + 1}: Score={score:.1f}, Projection={lineup_dict['projection']:.1f}, Salary=${lineup_dict['salary']}")
                else:
                    logger.info(f"Failed to generate lineup {i + 1}")
            else:
                logger.info(f"No result from optimizer for lineup {i + 1}")

        logger.info(f"\n=== Generated {len(generated_lineups)} lineups ===")
        return generated_lineups

    def _player_to_dict(self, player) -> Dict:
        """Convert player object to dictionary for GUI"""
        
        # Set contest type based on strategy
                
        return {
            'name': player.name,
            'position': player.position,
            'team': player.team,
            'opponent': getattr(player, 'opponent', ''),
            'salary': player.salary,
            'projection': player.base_projection,
            'optimization_score': player.optimization_score,
            'recent_form': getattr(player, 'recent_form', 0),
            'consistency_score': getattr(player, 'consistency_score', 0),
            'implied_team_score': getattr(player, 'implied_team_score', 0),
            'batting_order': getattr(player, 'batting_order', 0),
            'ownership_projection': getattr(player, 'ownership_projection', 0),
            'k_rate': getattr(player, 'k_rate', 0) if player.position in ['P', 'SP', 'RP'] else 0,
            'barrel_rate': getattr(player, 'barrel_rate', 0)
        }

    def create_proper_lineup_dict(self, lineup_players: List, optimization_score: float) -> Dict:
        """
        CRITICAL: Create lineup dict with PROPER projection calculation
        """
        # Calculate REAL projection sum (not optimized score!)
        total_projection = 0
        for player in lineup_players:
            # Try multiple projection sources
            proj = getattr(player, 'base_projection', 0)
            if proj == 0:
                proj = getattr(player, 'projection', 0)
            if proj == 0:
                proj = getattr(player, 'dff_projection', 0)
            total_projection += proj

        # Calculate salary
        total_salary = sum(p.salary for p in lineup_players)

        # Build position map
        positions = {}
        for p in lineup_players:
            positions[p.primary_position] = positions.get(p.primary_position, [])
            positions[p.primary_position].append(p.name)

        # Count teams for stacking
        team_counts = {}
        for p in lineup_players:
            if not p.is_pitcher:
                team_counts[p.team] = team_counts.get(p.team, 0) + 1

        max_stack = max(team_counts.values()) if team_counts else 0

        lineup_dict = {
            'players': lineup_players,
            'projection': total_projection,  # THIS IS THE FIX!
            'optimization_score': optimization_score,
            'salary': total_salary,
            'contest_type': self.current_contest_type,
            'strategy': self.current_strategy,
            'positions': positions,
            'num_teams': len(set(p.team for p in lineup_players)),
            'max_stack': max_stack,
            'avg_ownership': sum(getattr(p, 'projected_ownership', 15) for p in lineup_players) / len(lineup_players)
        }

        return lineup_dict

    def export_lineups(self, lineups: List[Dict], filename: str) -> bool:
        """Export lineups to CSV for DraftKings upload"""
        if not lineups:
            self.log("No lineups to export")
            return False

        try:

            # Create DraftKings upload format
            export_data = []

            for idx, lineup in enumerate(lineups):
                row = {}
                players = lineup['players']

                # DraftKings Classic format positions
                positions_needed = {
                    'P': ['P1', 'P2'],
                    'C': ['C'],
                    '1B': ['1B'],
                    '2B': ['2B'],
                    '3B': ['3B'],
                    'SS': ['SS'],
                    'OF': ['OF1', 'OF2', 'OF3']
                }

                # Group players by position
                position_groups = {}
                for player in players:
                    pos = player.primary_position
                    if pos not in position_groups:
                        position_groups[pos] = []
                    position_groups[pos].append(player.name + " (" + player.id + ")")

                # Fill each position
                for pos, dk_slots in positions_needed.items():
                    players_at_pos = position_groups.get(pos, [])
                    for i, slot in enumerate(dk_slots):
                        if i < len(players_at_pos):
                            row[slot] = players_at_pos[i]
                        else:
                            row[slot] = ""  # Empty if no player

                export_data.append(row)

            # Create DataFrame with DraftKings column order
            column_order = ['P1', 'P2', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3']
            df = pd.DataFrame(export_data)

            # Ensure all columns exist
            for col in column_order:
                if col not in df.columns:
                    df[col] = ""

            # Save in DraftKings order
            df = df[column_order]
            df.to_csv(filename, index=False)

            self.log(f"✅ Exported {len(lineups)} lineups to {filename}")
            return True

        except Exception as e:
            self.log(f"Export error: {e}")
            return False


# For backwards compatibility
def create_unified_system() -> UnifiedCoreSystem:
    """Factory function for creating system"""
    return UnifiedCoreSystem()