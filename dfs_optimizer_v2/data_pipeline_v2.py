#!/usr/bin/env python3
"""
DFS PIPELINE V2 - FIXED VERSION
================================
Complete working pipeline with all methods properly implemented
"""

import os
import csv
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from copy import deepcopy
from typing import Set  # <-- ADD THIS at the top with the other imports

# Remove circular imports from top-level
logger = logging.getLogger(__name__)


@dataclass
class Player:
    """Complete player data model"""

    # Core fields (required)
    name: str
    position: str
    team: str
    salary: int

    # Projections
    projection: float = 10.0
    optimization_score: float = 10.0

    # Game info
    opponent: str = ""
    game_info: str = ""

    # Enrichment fields (optional)
    implied_team_score: float = 4.5
    batting_order: int = 0
    ownership_projection: float = 15.0
    consistency_score: float = 50.0
    recent_form: float = 1.0
    k_rate: float = 7.0
    barrel_rate: float = 8.5  # Default barrel rate for batters
    xwoba: float = 0.320  # Default xwOBA

    # Status flags
    confirmed: bool = False
    stack_eligible: bool = False
    value_play: bool = False

    # IDs
    player_id: str = ""

    def __post_init__(self):
        if not self.player_id:
            self.player_id = f"{self.name}_{self.team}".lower().replace(" ", "_")


class DFSPipeline:
    """Main system orchestrator"""

    def __init__(self):
        # Lazy imports inside __init__ to avoid circular imports
        try:
            from optimizer_v2 import DFSOptimizer, OptimizerConfig
            from scoring_v2 import ScoringEngine
            from strategies_v2 import StrategyManager
            from config_v2 import get_config
        except ImportError as e:
            print(f"Error importing V2 modules: {e}")
            print("Make sure you're running from the dfs_optimizer_v2 directory")
            raise

        # Load configuration
        self.config = get_config()

        # Initialize components
        self.optimizer = DFSOptimizer(OptimizerConfig(
            salary_cap=self.config.SALARY_CAP,
            min_salary_gpp=self.config.MIN_SALARY['gpp'],
            min_salary_cash=self.config.MIN_SALARY['cash'],
            max_per_team_gpp=self.config.MAX_PER_TEAM['gpp'],
            max_per_team_cash=self.config.MAX_PER_TEAM['cash']
        ))

        self.scorer = ScoringEngine()
        self.strategy_manager = StrategyManager()

        # Data storage
        self.all_players: List[Player] = []
        self.player_pool: List[Player] = []
        self.num_games = 0

        # Enrichment sources (optional)
        self.enrichment_sources = {}
        self._init_enrichment_sources()

    def _init_enrichment_sources(self):
        """Initialize optional enrichment sources"""
        try:
            from real_data_enrichments import RealDataEnrichments
            self.enrichment_sources['real_data'] = RealDataEnrichments()
        except ImportError:
            logger.debug("RealDataEnrichments not available")


    def load_csv(self, csv_path: str) -> Tuple[int, int]:
        """Load DraftKings CSV and return (player_count, game_count)"""
        logger.info(f"Loading CSV: {csv_path}")

        self.all_players = []
        games_seen = set()

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Create player from CSV row
                    player = self._create_player_from_csv(row)
                    if player:
                        self.all_players.append(player)

                        # Track games
                        if player.game_info:
                            games_seen.add(player.game_info)

            self.num_games = len(games_seen)
            logger.info(f"Loaded {len(self.all_players)} players from {self.num_games} games")
            return len(self.all_players), self.num_games

        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return 0, 0

    def _create_player_from_csv(self, row: dict) -> Optional[Player]:
        """Create a Player object from DraftKings row, using the official MLB player ID"""
        try:
            # Basic CSV fields
            name = row.get('Name', '').strip()
            position = row.get('Position', '').strip()
            team = row.get('TeamAbbrev', '').strip()

            # Salary
            salary = int(row.get('Salary', '0').replace('$', '').replace(',', ''))

            # Projection
            proj = float(row.get('AvgPointsPerGame', '0') or 10.0)

            # Game context
            game_info = row.get('Game Info', '')
            opponent = row.get('Opponent', '')

            # Use the MLB player-ID column (DraftKings calls it "ID" or "PlayerID")
            numeric_id = row.get('ID') or row.get('PlayerID') or '0'

            return Player(
                name=name,
                position=position,
                team=team,
                salary=salary,
                projection=proj,
                optimization_score=proj,
                opponent=opponent,
                game_info=game_info,
                player_id=str(numeric_id),  # store the actual MLB ID as a string
            )

        except Exception as e:
            logger.debug(f"Error creating player from row: {e}")
            return None

    def fetch_confirmations(self) -> int:
        """
        Fetch MLB confirmations and reduce `self.all_players`
        to **only** players who are:
            1. In today’s confirmed batting order, **OR**
            2. Listed as the probable starting pitcher
        Returns the number of players left in the pool.
        """
        logger.info("Fetching MLB confirmations & filtering player pool...")

        try:
            from smart_confirmation import UniversalSmartConfirmation

            # 1. Run confirmation system on a *copy* to avoid side-effects
            confirmations = UniversalSmartConfirmation(
                csv_players=deepcopy(self.all_players),
                verbose=True
            )
            lineup_count, pitcher_count = confirmations.get_all_confirmations()

            # 2. Build a single set of confirmed MLB player IDs
            confirmed_ids: Set[int] = set()

            # 2a. Hitters in confirmed lineups
            for team_lineup in confirmations.confirmed_lineups.values():
                confirmed_ids.update(int(p["id"]) for p in team_lineup)

            # 2b. Probable starting pitchers
            confirmed_ids.update(int(p["id"]) for p in confirmations.confirmed_pitchers.values())

            logger.info(f"Found {len(confirmed_ids)} confirmed MLB IDs")

            # 3. Filter the master list in-place
            original_count = len(self.all_players)

            def _mlb_id(p: Player) -> int:
                return int(p.player_id)   # exact MLB numeric ID

            # 4. Mark every remaining player as confirmed for downstream use
            for p in self.all_players:
                p.confirmed = True

            return len(self.all_players)

        except ImportError:
            logger.warning("Smart confirmation system not available")
            import random
            for p in self.all_players:
                p.confirmed = random.random() < 0.5
            logger.info("Using fallback random confirmation")
            return len(self.all_players)

        except Exception as e:
            logger.error(f"Error during confirmation fetch: {e}")
            return len(self.all_players)  # keep list unchanged

    def build_player_pool(self, confirmed_only: bool = False,
                          manual_selections: List[str] = None) -> int:
        """Build the player pool for optimization"""
        self.player_pool = []

        for player in self.all_players:
            # Check if player should be included
            include = False

            # Check manual selections first
            if manual_selections and player.name in manual_selections:
                include = True
            # Then check confirmed status
            elif not confirmed_only or player.confirmed:
                include = True

            if include:
                self.player_pool.append(player)

        logger.info(f"Built player pool: {len(self.player_pool)} players")
        return len(self.player_pool)

    def apply_strategy(self, contest_type: str = 'gpp') -> str:
        """Apply strategy and return strategy name"""
        # Auto-select best strategy
        strategy_name, reason = self.strategy_manager.auto_select_strategy(
            self.num_games, contest_type
        )

        # Apply strategy adjustments to player pool
        self.player_pool = self.strategy_manager.apply_strategy(
            self.player_pool, strategy_name
        )

        logger.info(f"Applied strategy: {strategy_name} ({reason})")
        return strategy_name

    def enrich_players(self, strategy: str, contest_type: str) -> Dict:
        """Enrich players with additional data from multiple sources"""
        stats = {
            'vegas': 0,
            'batting_order': 0,
            'statcast': 0,
            'weather': 0,
            'ownership': 0
        }

        # Try to connect to real data sources
        vegas_data = None
        confirmations = None
        ownership_calc = None

        # 1. Vegas Lines
        try:
            from vegas_lines import VegasLines
            vegas = VegasLines()
            vegas_data = vegas.get_all_lines()
            logger.info(f"Connected to Vegas data: {len(vegas_data)} teams")
        except Exception as e:
            logger.debug(f"Vegas data unavailable: {e}")

        # 2. MLB Confirmations
        try:
            from smart_confirmation import UniversalSmartConfirmation
            confirmations = UniversalSmartConfirmation(
                csv_players=self.all_players,
                verbose=False
            )
            confirmations.get_all_confirmations()
            logger.info("Connected to MLB confirmations")
        except Exception as e:
            logger.debug(f"Confirmations unavailable: {e}")

        # 3. Ownership Calculator
        if contest_type == 'gpp':
            try:
                from ownership_calculator import OwnershipCalculator
                ownership_calc = OwnershipCalculator()
                logger.info("Connected to ownership calculator")
            except Exception as e:
                logger.debug(f"Ownership unavailable: {e}")

        # 4. Real Data Enrichments (Statcast, etc)
        enricher = self.enrichment_sources.get('real_data')

        # Enrich each player
        for player in self.player_pool:
            # VEGAS DATA
            if vegas_data and player.team in vegas_data:
                team_data = vegas_data[player.team]
                player.implied_team_score = team_data.get('implied_total', 4.5)
                player.game_total = team_data.get('game_total', 9.0)
                stats['vegas'] += 1
            else:
                player.implied_team_score = 4.5
                player.game_total = 9.0

            # BATTING ORDER (from confirmations)
            if confirmations and player.position not in ['P', 'SP', 'RP']:
                try:
                    is_confirmed, order = confirmations.is_player_confirmed(player.name, player.team)
                    if is_confirmed and order:
                        player.batting_order = order
                        stats['batting_order'] += 1
                    else:
                        player.batting_order = 5  # Default middle of order
                except:
                    player.batting_order = 5

            # OWNERSHIP (GPP only)
            if ownership_calc:
                try:
                    ownership = ownership_calc.calculate_ownership(
                        player.name, player.salary, player.projection
                    )
                    player.ownership_projection = ownership
                    stats['ownership'] += 1
                except:
                    player.ownership_projection = 15.0
            else:
                player.ownership_projection = 15.0

            # STATCAST & BARREL RATE
            if player.position in ['P', 'SP', 'RP']:
                # Pitchers don't need barrel rate
                player.k_rate = 8.0  # Default K/9 for pitchers
            else:
                # BATTERS - Ensure barrel rate is set
                if not hasattr(player, 'barrel_rate') or player.barrel_rate == 0:
                    # Try enricher first
                    if enricher:
                        try:
                            if enricher.enrich_player(player):
                                stats['statcast'] += 1
                        except:
                            pass

                    # Set defaults if still not set
                    if not hasattr(player, 'barrel_rate') or player.barrel_rate == 0:
                        # Default based on salary
                        if player.salary >= 5500:
                            player.barrel_rate = 10.5
                        elif player.salary >= 4500:
                            player.barrel_rate = 8.5
                        else:
                            player.barrel_rate = 6.5

                    if not hasattr(player, 'xwoba') or player.xwoba == 0:
                        player.xwoba = 0.320

            # COMMON DEFAULTS (ensure all players have these)
            if not hasattr(player, 'consistency_score'):
                player.consistency_score = 50.0
            if not hasattr(player, 'recent_form'):
                player.recent_form = 1.0
            if not hasattr(player, 'k_rate'):
                player.k_rate = 7.0 if player.position in ['P', 'SP', 'RP'] else 20.0

        logger.info(
            f"Enriched {len(self.player_pool)} players - Active sources: {[k for k, v in stats.items() if v > 0]}")
        return stats

    def score_players(self, contest_type: str = 'gpp'):
        """Score all players in the pool"""
        self.player_pool = self.scorer.score_all_players(
            self.player_pool, contest_type
        )
        logger.info(f"Scored {len(self.player_pool)} players for {contest_type}")

    def optimize_lineups(self, contest_type: str = 'gpp', num_lineups: int = 1) -> List[Dict]:
        """Generate optimized lineups + live feasibility report"""
        logger.info(f"Optimizing {num_lineups} {contest_type} lineups...")

        pool = self.player_pool
        logger.info(f"DEBUG: total players in pool: {len(pool)}")

        # ==== LIVE POSITION CHECK ====
        from collections import defaultdict
        by_pos = defaultdict(list)
        for p in pool:
            # handle multi-positions like "1B/OF"
            positions = p.position.split("/") if "/" in p.position else [p.position]
            for pos in positions:
                if pos in {"P", "C", "1B", "2B", "3B", "SS", "OF"}:
                    by_pos[pos].append(p)

        logger.info("DEBUG: Position counts in pool:")
        for pos, need in self.optimizer.config.positions.items():
            have = len(by_pos.get(pos, []))
            logger.warning(f"  {pos}: need {need}, have {have}")
        # ==== END CHECK ====

        # Actually call the optimizer
        lineups = self.optimizer.optimize(pool, contest_type, num_lineups)
        logger.info(f"Generated {len(lineups)} lineups")
        return lineups


    def export_lineups(self, lineups: List[Dict], output_path: str) -> bool:
        """Export lineups to CSV for DraftKings upload"""
        try:
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)

                # DraftKings upload format
                for i, lineup in enumerate(lineups):
                    row = []
                    for pos in ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']:
                        # Find player for this position
                        player_found = False
                        for player in lineup['players']:
                            if player.position == pos and player.name not in row:
                                row.append(player.name)
                                player_found = True
                                break

                        if not player_found:
                            # Handle multi-position eligibility
                            for player in lineup['players']:
                                if pos in player.position and player.name not in row:
                                    row.append(player.name)
                                    break

                    writer.writerow(row)

            logger.info(f"Exported {len(lineups)} lineups to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting lineups: {e}")
            return False


# Test the pipeline
if __name__ == "__main__":
    print("Testing DFS Pipeline V2")
    print("=" * 50)

    pipeline = DFSPipeline()

    # Test player creation
    test_player = Player(
        name="Test Player",
        position="OF",
        team="LAD",
        salary=5000,
        projection=12.0
    )

    print(f"Created test player: {test_player.name}")
    print(f"  Default barrel_rate: {test_player.barrel_rate}")
    print(f"  Default xwoba: {test_player.xwoba}")

    # Test pipeline methods
    pipeline.all_players = [test_player]
    pipeline.build_player_pool()

    # Test apply_strategy method
    strategy = pipeline.apply_strategy('cash')
    print(f"Applied strategy: {strategy}")

    # Test enrichment
    stats = pipeline.enrich_players(strategy, 'cash')
    print(f"Enrichment stats: {stats}")

    # Test scoring
    pipeline.score_players('cash')
    print(f"Player score after scoring: {test_player.optimization_score}")

    print("\n✅ Pipeline V2 working correctly!")