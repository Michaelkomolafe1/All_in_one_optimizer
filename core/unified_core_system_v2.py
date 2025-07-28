#!/usr/bin/env python3
"""
UNIFIED CORE SYSTEM V2 - WITH CSV LOADING
=========================================
Clean rewrite with CSV loading capability
"""

import logging
from typing import List, Dict, Set, Optional
from pathlib import Path
import pandas as pd

# Core components
from unified_player_model import UnifiedPlayer
from unified_milp_optimizer import UnifiedMILPOptimizer
from enhanced_scoring_engine import EnhancedScoringEngine
from csv_loader_v2 import CSVLoaderV2  # The new CSV loader

# Data sources (all in data/ directory)
import sys

sys.path.append(str(Path(__file__).parent.parent))

from data.simple_statcast_fetcher import SimpleStatcastFetcher
from data.smart_confirmation_system import SmartConfirmationSystem
from data.vegas_lines import VegasLines
from data.ownership_calculator import OwnershipCalculator

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UnifiedCoreSystemV2:
    """
    Simplified DFS optimization system WITH CSV LOADING
    Uses ONLY the enhanced scoring engine for ALL contest types
    """

    def __init__(self):
        """Initialize with only what we need"""
        logger.info("🚀 Initializing Unified Core System V2...")

        # Player pools
        self.all_players: List[UnifiedPlayer] = []
        self.player_pool: List[UnifiedPlayer] = []

        # Slate info
        self.slate_type = "classic"  # classic or showdown
        self.csv_loaded = False

        # Core components
        self.scoring_engine = EnhancedScoringEngine()
        self.optimizer = UnifiedMILPOptimizer()
        self.csv_loader = CSVLoaderV2()  # NEW: CSV Loader

        # Data sources
        self.statcast = SimpleStatcastFetcher()
        self.confirmation = SmartConfirmationSystem()
        self.vegas = VegasLines()
        self.ownership_calc = OwnershipCalculator()

        logger.info("✅ System initialized with Enhanced Scoring Engine & CSV Loader")

    def load_players_from_csv(self, csv_path: str, source: str = "dk") -> int:
        """
        Load players from DraftKings/FanDuel CSV
        Now with full implementation!
        """
        logger.info(f"📁 Loading players from {csv_path}")

        try:
            # Use the CSV loader
            players, slate_type = self.csv_loader.load_csv(csv_path)

            # Store results
            self.all_players = players
            self.slate_type = slate_type
            self.csv_loaded = True

            # Update confirmation system if it has CSV support
            if hasattr(self.confirmation, 'csv_players'):
                self.confirmation.csv_players = players

                # Build team set
                teams = {p.team for p in players}
                if hasattr(self.confirmation, 'csv_teams'):
                    self.confirmation.csv_teams = teams
                    logger.info(f"📋 Updated confirmation system with {len(teams)} teams")

            logger.info(f"✅ Loaded {len(players)} players ({slate_type} slate)")
            return len(players)

        except Exception as e:
            logger.error(f"❌ Failed to load CSV: {e}")
            raise

    def detect_slate_type(self) -> str:
        """Get the detected slate type"""
        return self.slate_type

    def set_player_pool(self,
                        strategy: str = "all",
                        confirmed_only: bool = False,
                        include_doubtful: bool = False) -> int:
        """
        Set player pool based on strategy
        Enhanced with slate-type awareness
        """
        if not self.all_players:
            logger.error("No players loaded! Load CSV first.")
            return 0

        logger.info(f"🎯 Setting player pool with strategy: {strategy}")

        if strategy == "confirmed_only":
            # Get confirmed players from confirmation system
            confirmed_names = set()

            if hasattr(self.confirmation, 'get_all_confirmations'):
                self.confirmation.get_all_confirmations()

                # Extract confirmed pitcher names
                for team, pitcher_info in self.confirmation.confirmed_pitchers.items():
                    if isinstance(pitcher_info, dict) and 'name' in pitcher_info:
                        confirmed_names.add(pitcher_info['name'])

                # Extract confirmed hitter names
                for team, lineup in self.confirmation.confirmed_lineups.items():
                    if isinstance(lineup, list):
                        confirmed_names.update(lineup)

            # Filter to confirmed only
            self.player_pool = [p for p in self.all_players if p.name in confirmed_names]
            logger.info(f"📋 Using {len(self.player_pool)} confirmed players only")
        else:
            # Use all players
            self.player_pool = self.all_players.copy()

        logger.info(f"📋 Player pool set: {len(self.player_pool)} players")
        return len(self.player_pool)

    def enrich_player_pool(self) -> int:
        """Enrich players with all data sources"""
        if not self.player_pool:
            logger.warning("No players in pool to enrich!")
            return 0

        logger.info("🔄 Enriching player pool...")
        enriched = 0

        for player in self.player_pool:
            try:
                # 1. Vegas lines
                if self.vegas:
                    # Set defaults (you'd implement actual fetching)
                    player.team_total = 4.5
                    player.game_total = 9.0
                    enriched += 1

                # 2. Ownership projections
                if self.ownership_calc:
                    player.projected_ownership = self.ownership_calc.calculate_ownership(
                        player.name,
                        player.salary,
                        player.base_projection
                    )

                # 3. Recent form (placeholder)
                player.recent_form_score = 10.0  # Default

                # 4. Calculate enhanced score
                contest_type = "gpp"  # Default, could be parameter
                player.enhanced_score = self.scoring_engine.score_player(player, contest_type)

            except Exception as e:
                logger.warning(f"Failed to enrich {player.name}: {e}")
                continue

        logger.info(f"✅ Enriched {enriched} players")
        return enriched

    def optimize_lineups(self,
                         num_lineups: int = 20,
                         contest_type: str = "gpp",
                         min_unique: int = 3) -> List[Dict]:
        """
        Generate optimized lineups
        Handles both classic and showdown
        """
        if not self.player_pool:
            logger.error("No players in pool! Set player pool first.")
            return []

        logger.info(f"🎯 Optimizing {num_lineups} {contest_type.upper()} lineups...")
        logger.info(f"   Slate type: {self.slate_type}")
        logger.info(f"   Pool size: {len(self.player_pool)} players")

        # Score all players for this contest type
        for player in self.player_pool:
            player.enhanced_score = self.scoring_engine.score_player(player, contest_type)

        # Configure optimizer for contest type
        if contest_type.lower() == "gpp":
            self.optimizer.config = {
                'min_teams': 2,
                'max_from_team': 5,
                'min_games': 2
            }
        elif contest_type.lower() == "cash":
            self.optimizer.config = {
                'min_teams': 3,
                'max_from_team': 3,
                'min_games': 3
            }

        # Handle showdown differently
        if self.slate_type == "showdown":
            logger.info("⚡ Using showdown optimization...")
            # Showdown-specific optimization would go here
            # For now, just warn
            logger.warning("Showdown optimization not fully implemented yet")
            return []

        # Generate lineups
        lineups = []
        used_players = set()

        for i in range(num_lineups):
            # Add diversity constraint
            self.optimizer.min_unique_players = min_unique
            self.optimizer.previous_lineups = lineups

            # Optimize
            lineup = self.optimizer.optimize(self.player_pool, contest_type)

            if lineup:
                lineups.append(lineup)

                # Track used players
                for player in lineup['players']:
                    used_players.add(player.name)

                # Log progress
                if (i + 1) % 5 == 0:
                    logger.info(f"   Generated {i + 1}/{num_lineups} lineups...")

        logger.info(f"✅ Generated {len(lineups)} lineups using {len(used_players)} unique players")

        # Show lineup summaries
        self._summarize_lineups(lineups[:3])  # Show first 3

        return lineups

    def _summarize_lineups(self, lineups: List[Dict]):
        """Show summary of lineups"""
        for i, lineup in enumerate(lineups):
            logger.info(f"\n📊 Lineup {i + 1}:")
            logger.info(f"   Salary: ${lineup['total_salary']:,} / $50,000")
            logger.info(f"   Projection: {lineup['total_score']:.2f} pts")

            # Show stacks
            teams = {}
            for p in lineup['players']:
                teams[p.team] = teams.get(p.team, 0) + 1

            stacks = [(team, count) for team, count in teams.items() if count >= 2]
            if stacks:
                stack_str = ", ".join([f"{team}({count})" for team, count in stacks])
                logger.info(f"   Stacks: {stack_str}")

    def export_lineups(self, lineups: List[Dict], filename: str = None) -> str:
        """Export lineups to CSV"""
        if not lineups:
            logger.warning("No lineups to export")
            return ""

        from datetime import datetime

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"lineups_{self.slate_type}_{timestamp}.csv"

        # Create export format
        if self.slate_type == "showdown":
            # Showdown format
            rows = []
            for i, lineup in enumerate(lineups):
                row = {'Lineup': i + 1}

                # Find captain (highest score)
                players_sorted = sorted(lineup['players'],
                                        key=lambda p: p.enhanced_score,
                                        reverse=True)

                row['CPT'] = players_sorted[0].name
                for j, player in enumerate(players_sorted[1:6], 1):
                    row[f'UTIL{j}'] = player.name

                row['Salary'] = lineup['total_salary']
                row['Projection'] = lineup['total_score']
                rows.append(row)
        else:
            # Classic format
            rows = []
            for i, lineup in enumerate(lineups):
                row = {'Lineup': i + 1}

                # Standard positions
                positions = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
                pos_filled = {pos: 0 for pos in positions}

                # Fill positions
                for pos in positions:
                    for player in lineup['players']:
                        if (player.primary_position == pos or
                            pos in player.positions) and pos_filled[pos] == 0:
                            col_name = f"{pos}{pos_filled[pos] + 1}" if pos in ['P', 'OF'] else pos
                            row[col_name] = player.name
                            pos_filled[pos] = 1
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
    # Initialize system
    system = UnifiedCoreSystemV2()

    # Example workflow
    print("\n🚀 Unified Core System V2 with CSV Loading")
    print("=" * 50)

    # 1. Load CSV
    # players_loaded = system.load_players_from_csv("sample_data/DKSalaries.csv")
    # print(f"✅ Loaded {players_loaded} players")

    # 2. Set player pool
    # pool_size = system.set_player_pool(strategy="all")
    # print(f"✅ Player pool: {pool_size} players")

    # 3. Enrich data
    # enriched = system.enrich_player_pool()
    # print(f"✅ Enriched {enriched} players")

    # 4. Optimize lineups
    # lineups = system.optimize_lineups(num_lineups=5, contest_type="gpp")
    # print(f"✅ Generated {len(lineups)} lineups")

    # 5. Export
    # if lineups:
    #     filename = system.export_lineups(lineups)
    #     print(f"✅ Exported to {filename}")

    print("\n✨ System ready for use!")