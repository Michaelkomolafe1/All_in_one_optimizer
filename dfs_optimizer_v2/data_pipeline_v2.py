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

                    # Get batting order for hitters
                    if player.position not in ['P', 'SP', 'RP']:
                        order = confirmations.get_batting_order(player.name, player.team)
                        if order and order > 0:
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
                if enricher:
                    try:
                        pitcher_stats = enricher.get_pitcher_stats(player.name)
                        if pitcher_stats:
                            player.k_rate = pitcher_stats.get('k_per_9', 8.0)
                            player.whip = pitcher_stats.get('whip', 1.25)
                            player.era = pitcher_stats.get('era', 4.00)
                    except:
                        player.k_rate = 8.0  # Default
                else:
                    # Estimate K-rate from salary (higher salary = better pitcher)
                    player.k_rate = 6.0 + (player.salary / 2000)  # 6-11 range

            # 6. STRATEGY-SPECIFIC ENRICHMENTS

            # Cash: Focus on consistency and floor
            if contest_type == 'cash':
                # Ensure consistency score exists
                if not hasattr(player, 'consistency_score'):
                    # Estimate from salary and projection
                    player.consistency_score = min(90, 40 + (player.salary / 200))

                # Recent form (default to neutral if not available)
                if not hasattr(player, 'recent_form'):
                    player.recent_form = 1.0

            # GPP: Ensure ownership exists
            elif contest_type == 'gpp':
                if not hasattr(player, 'ownership_projection'):
                    # Estimate ownership from salary and projection
                    # High salary + high projection = higher ownership
                    value = player.projection / (player.salary / 1000) if player.salary > 0 else 2.0

                    if value > 4.0:  # Great value
                        player.ownership_projection = 25.0
                    elif value > 3.0:  # Good value
                        player.ownership_projection = 15.0
                    else:
                        player.ownership_projection = 8.0

        # Log enrichment results
        logger.info(f"Enrichment complete: {stats}")

        # Log sample enriched player for debugging
        if self.player_pool:
            sample = self.player_pool[0]
            logger.debug(f"Sample enriched player: {sample.name}")
            logger.debug(f"  Team Score: {getattr(sample, 'implied_team_score', 'N/A')}")
            logger.debug(f"  Batting Order: {getattr(sample, 'batting_order', 'N/A')}")
            logger.debug(f"  Ownership: {getattr(sample, 'ownership_projection', 'N/A')}")
            logger.debug(f"  Confirmed: {getattr(sample, 'confirmed', False)}")

        return stats

    def fetch_confirmations(self) -> int:
        """Fetch and apply MLB confirmations"""

        if not self.all_players:
            logger.error("No players loaded")
            return 0

        try:
            from smart_confirmation import UniversalSmartConfirmation

            confirmations = UniversalSmartConfirmation(
                csv_players=self.all_players,
                verbose=False
            )

            lineup_count, pitcher_count = confirmations.get_all_confirmations()

            # Mark confirmed players
            confirmed = 0
            for player in self.all_players:
                if confirmations.is_player_confirmed(player.name, player.team):
                    player.confirmed = True
                    confirmed += 1

                    # Get batting order
                    if player.position not in ['P', 'SP', 'RP']:
                        order = confirmations.get_batting_order(player.name, player.team)
                        if order:
                            player.batting_order = order

            logger.info(f"Confirmed {confirmed} players ({lineup_count} hitters, {pitcher_count} pitchers)")
            return confirmed

        except Exception as e:
            logger.error(f"Failed to fetch confirmations: {e}")
            return 0

    def update_player_pool_confirmations(self):
        """Update confirmations for players in pool"""

        confirmed = 0
        for player in self.player_pool:
            if getattr(player, 'confirmed', False):
                confirmed += 1

        logger.info(f"Pool has {confirmed}/{len(self.player_pool)} confirmed players")
        return confirmed

    # =========================================
    # STEP 4: SCORE PLAYERS
    # =========================================

    def score_players(self, contest_type: str) -> int:
        """Score all players in pool"""

        if not self.player_pool:
            logger.error("No players to score")
            return 0

        logger.info(f"Scoring {len(self.player_pool)} players for {contest_type}")

        # Score all players
        self.scorer.score_all_players(self.player_pool, contest_type)

        return len(self.player_pool)

    # =========================================
    # STEP 5: APPLY STRATEGY
    # =========================================

    def apply_strategy(self, strategy: str = None, contest_type: str = 'gpp') -> str:
        """Apply strategy to player pool"""

        # Auto-select if not specified
        if not strategy:
            strategy, reason = self.strategy_manager.auto_select_strategy(
                self.num_games, contest_type
            )
            logger.info(f"Auto-selected: {reason}")

        # Apply strategy adjustments
        self.player_pool = self.strategy_manager.apply_strategy(
            self.player_pool, strategy
        )

        logger.info(f"Applied strategy: {strategy}")
        return strategy

    # =========================================
    # STEP 6: OPTIMIZE
    # =========================================

    def optimize_lineups(self,
                         contest_type: str = 'gpp',
                         num_lineups: int = 1) -> List[Dict]:
        """Generate optimized lineups"""

        if not self.player_pool:
            logger.error("No players to optimize")
            return []

        logger.info(f"Optimizing {num_lineups} {contest_type} lineups")

        # Run optimization
        self.lineups = self.optimizer.optimize(
            self.player_pool,
            contest_type,
            num_lineups
        )

        # Add metadata
        for lineup in self.lineups:
            lineup['contest_type'] = contest_type
            lineup['slate_size'] = self.slate_size
            lineup['num_games'] = self.num_games
            lineup['timestamp'] = datetime.now().isoformat()

        logger.info(f"Generated {len(self.lineups)} lineups")
        return self.lineups

    # =========================================
    # STEP 7: EXPORT
    # =========================================

    def export_lineups(self, filepath: str = None) -> bool:
        """Export lineups to DraftKings CSV format"""

        if not self.lineups:
            logger.error("No lineups to export")
            return False

        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"{self.config.EXPORT_DIR}/lineups_{timestamp}.csv"

        # Create export directory if needed
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        logger.info(f"Exporting {len(self.lineups)} lineups to {filepath}")

        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.config.DK_POSITIONS)
                writer.writeheader()

                for lineup in self.lineups:
                    row = self._format_lineup_for_dk(lineup)
                    writer.writerow(row)

            logger.info(f"Export complete: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Export error: {e}")
            return False

    def _format_lineup_for_dk(self, lineup: Dict) -> Dict:
        """Format lineup for DraftKings CSV"""

        row = {}
        players = lineup['players']

        # Group by position
        positions = {
            'P': [], 'C': [], '1B': [], '2B': [],
            '3B': [], 'SS': [], 'OF': []
        }

        for player in players:
            pos = player.position  # NOT player['position']
            if pos in ['SP', 'RP']:
                pos = 'P'
            if pos in positions:
                positions[pos].append(player.name)  # NOT player['name']

        # Fill DK positions
        row['P1'] = positions['P'][0] if len(positions['P']) > 0 else ''
        row['P2'] = positions['P'][1] if len(positions['P']) > 1 else ''
        row['C'] = positions['C'][0] if positions['C'] else ''
        row['1B'] = positions['1B'][0] if positions['1B'] else ''
        row['2B'] = positions['2B'][0] if positions['2B'] else ''
        row['3B'] = positions['3B'][0] if positions['3B'] else ''
        row['SS'] = positions['SS'][0] if positions['SS'] else ''
        row['OF1'] = positions['OF'][0] if len(positions['OF']) > 0 else ''
        row['OF2'] = positions['OF'][1] if len(positions['OF']) > 1 else ''
        row['OF3'] = positions['OF'][2] if len(positions['OF']) > 2 else ''

        return row

    # =========================================
    # COMPLETE WORKFLOW
    # =========================================

    def run_complete_optimization(self,
                                  csv_path: str,
                                  contest_type: str = 'gpp',
                                  num_lineups: int = 20,
                                  confirmed_only: bool = False,
                                  manual_selections: List[str] = None) -> List[Dict]:
        """Run the complete optimization pipeline"""

        logger.info("=" * 60)
        logger.info("STARTING COMPLETE OPTIMIZATION")
        logger.info("=" * 60)

        # 1. Load CSV
        if not self.load_csv(csv_path):
            return []

        # 2. Build pool
        if not self.build_player_pool(confirmed_only, manual_selections):
            return []

        # 3. Auto-select strategy
        strategy = self.apply_strategy(contest_type=contest_type)

        # 4. Enrich data
        self.enrich_players(strategy, contest_type)

        # 5. Score players
        self.score_players(contest_type)

        # 6. Optimize
        lineups = self.optimize_lineups(contest_type, num_lineups)

        # 7. Log results
        if lineups:
            logger.info("=" * 60)
            logger.info("OPTIMIZATION COMPLETE")
            logger.info(f"Generated {len(lineups)} lineups")

            for i, lineup in enumerate(lineups[:3]):  # Show first 3
                logger.info(f"\nLineup {i + 1}:")
                logger.info(f"  Salary: ${lineup['salary']:,}")
                logger.info(f"  Projection: {lineup['projection']:.1f}")
                logger.info(f"  Max Stack: {lineup['max_stack']} players")

        return lineups


# Test the complete system
if __name__ == "__main__":
    print("DFS Pipeline V2 Test")
    print("=" * 60)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # Create pipeline
    pipeline = DFSPipeline()

    # Create test CSV
    test_csv = "test_slate.csv"
    with open(test_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Position', 'Team', 'Salary', 'Game Info', 'AvgPointsPerGame'])

        # Add test players
        writer.writerow(['Gerrit Cole', 'P', 'NYY', '9000', 'NYY@BOS', '45'])
        writer.writerow(['Shane Bieber', 'P', 'CLE', '8500', 'CLE@DET', '42'])
        writer.writerow(['Tyler Glasnow', 'P', 'TB', '8000', 'TB@TOR', '40'])
        writer.writerow(['Mike Trout', 'OF', 'LAA', '6000', 'LAA@HOU', '15'])
        writer.writerow(['Aaron Judge', 'OF', 'NYY', '5800', 'NYY@BOS', '14'])
        writer.writerow(['Ronald Acuna Jr.', 'OF', 'ATL', '5600', 'ATL@MIA', '13'])
        # Add more players for complete lineup...

    # Run optimization
    lineups = pipeline.run_complete_optimization(
        csv_path=test_csv,
        contest_type='gpp',
        num_lineups=3,
        confirmed_only=False
    )

    if lineups:
        print("\n✅ Pipeline working correctly!")
        print(f"Generated {len(lineups)} lineups")
    else:
        print("\n❌ Pipeline failed")

    # Clean up
    os.remove(test_csv)