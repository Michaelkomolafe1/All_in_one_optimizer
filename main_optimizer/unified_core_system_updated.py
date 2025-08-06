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

# Fix Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
data_dir = os.path.join(parent_dir, 'data')
if data_dir not in sys.path:
    sys.path.insert(0, data_dir)

# Core imports
from unified_player_model import UnifiedPlayer
from unified_milp_optimizer import UnifiedMILPOptimizer

# NEW IMPORTS - Use V2 scoring engine
from enhanced_scoring_engine_v2 import EnhancedScoringEngineV2
from smart_enrichment_manager import SmartEnrichmentManager
from gui_strategy_configuration import GUIStrategyManager

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

        # NEW: Smart managers
        self.scoring_engine = EnhancedScoringEngineV2(use_bayesian=False)
        self.enrichment_manager = SmartEnrichmentManager()
        self.strategy_manager = GUIStrategyManager()

        # Optimizer
        from correlation_scoring_config import CorrelationScoringConfig
        self.config = CorrelationScoringConfig()
        self.optimizer = UnifiedMILPOptimizer(self.config)

        # Data sources
        self.confirmation_system = SmartConfirmationSystem() if CONFIRMATION_AVAILABLE else None
        self.stats_fetcher = SimpleStatcastFetcher() if STATCAST_AVAILABLE else None
        self.vegas_lines = VegasLines() if VEGAS_AVAILABLE else None
        # Setup enrichment sources
        if self.vegas_lines:
            self.enrichment_manager.set_enrichment_source('vegas', self.vegas_lines)
        if self.stats_fetcher:
            self.enrichment_manager.set_enrichment_source('statcast', self.stats_fetcher)
        if self.confirmation_system:
            self.enrichment_manager.set_enrichment_source('confirmations', self.confirmation_system)

        # State tracking
        self.csv_loaded = False
        self.current_slate_size = None
        self.current_contest_type = None
        self.current_strategy = None

        # Logging
        self.log_messages = []

    def log(self, message: str):
        """Add timestamped log message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)
        logger.info(message)

    def load_csv(self, csv_path: str) -> int:
        """Load players from DraftKings CSV"""
        self.log(f"Loading CSV: {csv_path}")

        try:
            df = pd.read_csv(csv_path)
            self.log(f"Loaded {len(df)} rows from CSV")

            # Convert to UnifiedPlayer objects
            self.players = []
            for idx, row in df.iterrows():
                try:
                    player = UnifiedPlayer.from_csv_row(row.to_dict())
                    self.players.append(player)
                except Exception as e:
                    self.log(f"Error loading player at row {idx}: {e}")

            self.csv_loaded = True
            self.log(f"Successfully loaded {len(self.players)} players")

            # Auto-detect slate size
            self.detect_slate_characteristics()

            return len(self.players)

        except Exception as e:
            self.log(f"Error loading CSV: {e}")
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
        """Fetch confirmed lineups"""
        if not self.confirmation_system:
            self.log("Confirmation system not available")
            return 0

        try:
            confirmed = self.confirmation_system.get_confirmed_players()
            confirmed_count = 0

            for player in self.players:
                if player.name in confirmed:
                    player.is_confirmed = True
                    player.batting_order = confirmed[player.name].get('batting_order', 0)
                    confirmed_count += 1

            self.log(f"Marked {confirmed_count} players as confirmed")
            return confirmed_count

        except Exception as e:
            self.log(f"Error fetching confirmations: {e}")
            return 0

    def build_player_pool(self, include_unconfirmed: bool = False, manual_selections: Set[str] = None):
        """Build the player pool for optimization"""
        self.player_pool = []

        for player in self.players:
            # Include logic
            include = False

            # Check confirmed
            if getattr(player, 'is_confirmed', False):
                include = True

            # Check manual selection
            if manual_selections and player.name in manual_selections:
                include = True
                player.is_manual_selected = True

            # Include unconfirmed if requested
            if include_unconfirmed:
                include = True

            if include:
                self.player_pool.append(player)

        self.log(f"Player pool: {len(self.player_pool)} players")
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

    def score_players(self, contest_type: str) -> int:
        """
        NEW METHOD: Unified scoring using V2 engine
        """
        if not self.player_pool:
            self.log("No players to score")
            return 0

        self.log(f"Scoring {len(self.player_pool)} players for {contest_type}")

        scored_count = 0
        for player in self.player_pool:
            # Single scoring call
            score = self.scoring_engine.score_player(player, contest_type)

            # Store scores
            player.optimization_score = score
            setattr(player, f'{contest_type}_score', score)

            if score > 0:
                scored_count += 1

        self.log(f"Scored {scored_count} players with non-zero scores")

        # Get top scorers for logging
        if scored_count > 0:
            top_players = sorted(self.player_pool, key=lambda p: p.optimization_score, reverse=True)[:3]
            for p in top_players:
                self.log(f"  Top: {p.name} = {p.optimization_score:.1f}")

        return scored_count

    def optimize_lineup(self,
                        strategy: str,
                        contest_type: str,
                        num_lineups: int = 1,
                        manual_selections: str = "") -> List[Dict]:
        """
        NEW METHOD: Complete optimization pipeline
        """
        lineups = []

        # Set current state
        self.current_strategy = strategy
        self.current_contest_type = contest_type

        # STEP 1: Smart enrichment for this strategy
        self.log(f"\n=== OPTIMIZATION PIPELINE ===")
        self.log(f"Strategy: {strategy}, Contest: {contest_type}")

        enrichment_stats = self.enrich_player_pool_smart(strategy, contest_type)
        self.log(f"Enriched: {enrichment_stats}")

        # STEP 2: Score players
        scored = self.score_players(contest_type)
        if scored == 0:
            self.log("ERROR: No players scored!")
            return []

        # STEP 3: Filter valid players
        valid_players = [p for p in self.player_pool if p.optimization_score > 0]
        self.log(f"Valid players for optimization: {len(valid_players)}")

        # STEP 4: Generate lineups
        for i in range(num_lineups):
            self.log(f"\nGenerating lineup {i + 1}/{num_lineups}")

            # Run optimizer
            lineup, score = self.optimizer.optimize_lineup(
                players=valid_players,
                strategy=strategy,
                manual_selections=manual_selections,
                contest_type=contest_type
            )

            if lineup and len(lineup) > 0:
                # CREATE PROPER LINEUP DICT
                lineup_dict = self.create_proper_lineup_dict(lineup, score)
                lineups.append(lineup_dict)

                self.log(f"Lineup {i + 1}: Score={lineup_dict['optimization_score']:.1f}, "
                         f"Projection={lineup_dict['projection']:.1f}, "
                         f"Salary=${lineup_dict['salary']}")
            else:
                self.log(f"Failed to generate lineup {i + 1}")

        self.log(f"\n=== Generated {len(lineups)} lineups ===")
        return lineups

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
            import pandas as pd

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