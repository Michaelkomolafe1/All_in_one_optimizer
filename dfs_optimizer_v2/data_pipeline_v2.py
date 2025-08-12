# In data_pipeline_v2.py, update imports section:

import os
import csv
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# Import our new modules with error handling
try:
    from optimizer_v2 import DFSOptimizer, OptimizerConfig
    from scoring_v2 import ScoringEngine
    from strategies_v2 import StrategyManager
    from config_v2 import get_config
except ImportError as e:
    print(f"Error importing V2 modules: {e}")
    print("Make sure you're running from the dfs_optimizer_v2 directory")
    raise

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
        self.lineups: List[Dict] = []

        # State tracking
        self.csv_loaded = False
        self.slate_size = None
        self.num_games = 0

        logger.info("DFS Pipeline initialized")

    # =========================================
    # STEP 1: LOAD DATA
    # =========================================

    def load_csv(self, filepath: str) -> int:
        """Load DraftKings CSV"""

        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return 0

        logger.info(f"Loading CSV: {filepath}")
        self.all_players = []

        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    player = self._parse_csv_row(row)
                    if player:
                        self.all_players.append(player)

            # Detect slate characteristics
            self._detect_slate()

            self.csv_loaded = True
            logger.info(f"Loaded {len(self.all_players)} players")
            return len(self.all_players)

        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return 0

    def _parse_csv_row(self, row: Dict) -> Optional[Player]:
        """Parse a CSV row into Player object"""

        try:
            # Extract fields
            name = row.get('Name', '')
            position = row.get('Position', '')

            # NORMALIZE PITCHER POSITIONS
            if position in ['SP', 'RP']:
                position = 'P'

            team = row.get('TeamAbbrev', row.get('Team', ''))

            # Parse salary
            salary_str = row.get('Salary', '0')
            salary = int(str(salary_str).replace('$', '').replace(',', ''))

            # Parse game info
            game_info = row.get('Game Info', '')
            opponent = ''
            if '@' in game_info:
                parts = game_info.split('@')
                if team in parts[0]:
                    opponent = parts[1].split()[0]
                else:
                    opponent = parts[0].strip()

            # Get projection
            projection = float(row.get('AvgPointsPerGame', 10.0) or 10.0)

            return Player(
                name=name,
                position=position,
                team=team,
                salary=salary,
                projection=projection,
                opponent=opponent,
                game_info=game_info
            )

        except Exception as e:
            logger.debug(f"Error parsing row: {e}")
            return None

    def _detect_slate(self):
        """Detect slate characteristics"""

        teams = set(p.team for p in self.all_players)
        self.num_games = len(teams) // 2
        self.slate_size = self.config.get_slate_size(self.num_games)

        logger.info(f"Detected: {self.num_games} games ({self.slate_size} slate)")

    # =========================================
    # STEP 2: BUILD PLAYER POOL
    # =========================================

    def build_player_pool(self,
                          confirmed_only: bool = False,
                          manual_selections: List[str] = None) -> int:
        """Build the pool of players to optimize from"""

        if not self.csv_loaded:
            logger.error("No CSV loaded")
            return 0

        logger.info(f"Building player pool (confirmed_only={confirmed_only})")

        # Start with all or confirmed
        if confirmed_only:
            self.player_pool = [p for p in self.all_players if p.confirmed]
        else:
            self.player_pool = self.all_players.copy()

        # Add manual selections
        if manual_selections:
            for name in manual_selections:
                player = self._find_player(name)
                if player and player not in self.player_pool:
                    self.player_pool.append(player)
                    logger.info(f"Added manual selection: {name}")

        logger.info(f"Player pool: {len(self.player_pool)} players")
        return len(self.player_pool)

    def fetch_confirmations(self) -> int:
        """Fetch and apply MLB confirmations - ONLY MARK ACTUAL STARTERS"""

        if not self.all_players:
            logger.error("No players loaded")
            return 0

        try:
            from smart_confirmation import UniversalSmartConfirmation

            # Show CSV teams for debugging
            csv_teams = set()
            for player in self.all_players:
                csv_teams.add(player.team)
            logger.info(f"Your CSV teams: {sorted(csv_teams)}")

            # Create confirmation system with CSV filtering
            confirmations = UniversalSmartConfirmation(
                csv_players=self.all_players,
                verbose=True
            )

            lineup_count, pitcher_count = confirmations.get_all_confirmations()
            logger.info(f"MLB API found {lineup_count} lineup players, {pitcher_count} pitchers")

            # Filter to ONLY actual confirmed starters
            confirmed = 0
            confirmed_players = []

            for player in self.all_players:
                # CRITICAL: Proper tuple unpacking
                is_confirmed, batting_order = confirmations.is_player_confirmed(player.name, player.team)

                if is_confirmed:
                    player.confirmed = True
                    confirmed += 1
                    confirmed_players.append(f"{player.name} ({player.team})")

                    # Set batting order for hitters
                    if player.position not in ['P', 'SP', 'RP'] and batting_order:
                        player.batting_order = batting_order
                else:
                    player.confirmed = False

            logger.info(f"RESULT: {confirmed}/{len(self.all_players)} CSV players are confirmed starters")

            if confirmed > 0:
                logger.info("First 10 confirmed players:")
                for player_info in confirmed_players[:10]:
                    logger.info(f"  ✅ {player_info}")

            return confirmed

        except Exception as e:
            logger.error(f"Failed to fetch confirmations: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0

    def _find_player(self, name: str) -> Optional[Player]:
        """Find player by name"""

        name_lower = name.lower().strip()
        for player in self.all_players:
            if player.name.lower() == name_lower:
                return player
        return None

    # =========================================
    # STEP 3: ENRICH DATA
    # =========================================

    def enrich_players(self, strategy: str, contest_type: str) -> Dict:
        """Enrich player pool with real data"""

        logger.info(f"Enriching players for {strategy} ({contest_type})")

        stats = {
            'vegas': 0,
            'batting_order': 0,
            'ownership': 0,
            'statcast': 0,
            'confirmed': 0
        }

        # Import your actual data sources
        try:
            from vegas_lines import VegasLines
            vegas = VegasLines()
            vegas_data = vegas.get_all_lines()
            logger.info(f"Loaded Vegas data for {len(vegas_data)} teams")
        except Exception as e:
            logger.warning(f"Vegas data unavailable: {e}")
            vegas_data = {}

        try:
            from smart_confirmation import UniversalSmartConfirmation
            confirmations = UniversalSmartConfirmation(
                csv_players=self.all_players,
                verbose=False
            )
            confirmations.get_all_confirmations()
            logger.info("Loaded MLB confirmations")
        except Exception as e:
            logger.warning(f"Confirmations unavailable: {e}")
            confirmations = None

        try:
            from real_data_enrichments import RealDataEnrichments
            enricher = RealDataEnrichments()
            logger.info("Loaded real data enrichments")
        except Exception as e:
            logger.warning(f"Real data enrichments unavailable: {e}")
            enricher = None

        try:
            from ownership_calculator import OwnershipCalculator
            ownership_calc = OwnershipCalculator()
            logger.info("Loaded ownership calculator")
        except Exception as e:
            logger.warning(f"Ownership unavailable: {e}")
            ownership_calc = None

        # Enrich each player
        for player in self.player_pool:
            # 1. VEGAS DATA
            if vegas_data and player.team in vegas_data:
                team_data = vegas_data[player.team]
                player.implied_team_score = team_data.get('implied_total', 4.5)
                player.game_total = team_data.get('game_total', 9.0)
                player.opponent_implied_total = team_data.get('opponent_total', 4.5)
                stats['vegas'] += 1
            else:
                # Defaults if no Vegas data
                player.implied_team_score = 4.5
                player.game_total = 9.0

            # 2. CONFIRMATIONS & BATTING ORDER
            if confirmations:
                # Check if player is confirmed
                if confirmations.is_player_confirmed(player.name, player.team):
                    player.confirmed = True
                    stats['confirmed'] += 1

                    # Get batting order
                    if player.position not in ['P', 'SP', 'RP']:
                        confirmed, order = confirmations.is_player_confirmed(player.name, player.team)
                        if confirmed and order:
                            player.batting_order = order
                            stats['batting_order'] += 1
                        else:
                            player.batting_order = 9  # Default to bottom

            # 3. OWNERSHIP (GPP only)
            if contest_type == 'gpp' and ownership_calc:
                try:
                    ownership = ownership_calc.calculate_ownership(
                        player.name,
                        player.salary,
                        player.projection
                    )
                    player.ownership_projection = ownership
                    stats['ownership'] += 1
                except:
                    player.ownership_projection = 15.0  # Default 15%

            # 4. STATCAST & ADVANCED STATS
            if enricher and player.position not in ['P', 'SP', 'RP']:
                try:
                    # Get recent form
                    recent_stats = enricher.get_recent_form(player.name)
                    if recent_stats:
                        player.recent_form = recent_stats.get('form_rating', 1.0)
                        player.consistency_score = recent_stats.get('consistency', 50.0)

                    # Get advanced stats for top players (by salary)
                    if player.salary >= 5000:  # Only for expensive players
                        adv_stats = enricher.get_advanced_stats(player.name)
                        if adv_stats:
                            player.barrel_rate = adv_stats.get('barrel_rate', 8.0)
                            player.hard_hit_rate = adv_stats.get('hard_hit_rate', 35.0)
                            player.xwoba = adv_stats.get('xwoba', 0.320)
                            stats['statcast'] += 1
                except Exception as e:
                    logger.debug(f"Stats unavailable for {player.name}: {e}")

            # 5. PITCHER-SPECIFIC STATS
            if player.position in ['P', 'SP', 'RP']:
                
        # REAL DATA ENRICHMENTS - ENSURE BARREL RATE IS SET
        if enricher:
            try:
                # Call the enricher for this player
                enrichment_success = enricher.enrich_player(player)
                if enrichment_success:
                    stats['statcast'] += 1

                # FORCE barrel rate if not set (backup)
                if not hasattr(player, 'barrel_rate'):
                    player.barrel_rate = 8.5  # Default value

            except Exception as e:
                # If enricher fails, set defaults
                if not hasattr(player, 'barrel_rate'):
                    player.barrel_rate = 8.5
                if not hasattr(player, 'xwoba'):
                    player.xwoba = 0.320