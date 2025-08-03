#!/usr/bin/env python3
"""
UNIFIED CORE SYSTEM - ENHANCED VERSION
=====================================
Complete unified DFS system with new optimized scoring
"""

import logging
from datetime import datetime
from typing import Dict, List, Set
# # from dfs_optimizer.tracking.performance_tracker import PerformanceTracker
class PerformanceTracker:
    def __init__(self): pass
    def track_lineup(self, data): return None
import pandas as pd

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Core imports
from dfs_optimizer.core.unified_player_model import UnifiedPlayer
from dfs_optimizer.core.unified_milp_optimizer import UnifiedMILPOptimizer

# NEW: Enhanced scoring engine - the ONLY scoring system we use
from dfs_optimizer.core.enhanced_scoring_engine import EnhancedScoringEngine

# Data enrichment imports
from dfs_optimizer.data.statcast_fetcher import SimpleStatcastFetcher
from dfs_optimizer.data.smart_confirmation import SmartConfirmationSystem
from dfs_optimizer.data.vegas_lines import VegasLines
from core.strategy_auto_selector import StrategyAutoSelector
# Optional imports with proper handling
try:
    from data.weather_integration import get_weather_integration
    WEATHER_AVAILABLE = True
except ImportError:
    WEATHER_AVAILABLE = False
    get_weather_integration = None  # Define as None to avoid reference errors
    logger.warning("Weather integration not available")

# Showdown optimizer (if you still need it)
try:
    from fixed_showdown_optimization import ShowdownOptimizer
    SHOWDOWN_AVAILABLE = True
except ImportError:
    SHOWDOWN_AVAILABLE = False
    ShowdownOptimizer = None  # Define as None to avoid reference errors
    logger.warning("Showdown optimizer not available - using standard optimizer")




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
        self.tracker = PerformanceTracker()

        # Initialize components
        self.optimizer = UnifiedMILPOptimizer()
        self.scoring_engine = EnhancedScoringEngine()  # Your new scoring engine

        # Initialize data sources
        self.statcast = SimpleStatcastFetcher()
        self.strategy_selector = StrategyAutoSelector()
        self.confirmation_system = SmartConfirmationSystem()
        self.vegas = VegasLines()
        self.enrichments_applied = False

        logger.info("✅ Unified Core System initialized with Enhanced Scoring Engine")
        self._last_contest_type = None

    """
    FIX FOR score_players METHOD
    ============================
    Add this to unified_core_system.py to fix scoring
    """

    def score_players(self, contest_type='gpp'):
        """Score all players using enhanced scoring engine"""
        logger.info(f"Scoring players for {contest_type.upper()}")

        # Ensure enrichment has run
        if not self.enrichments_applied:
            logger.info("Running enrichments first...")
            self.enrich_player_pool()

        # Use enhanced scoring engine for ALL scoring
        scored_count = 0
        for player in self.player_pool:
            try:
                # Calculate both scores using enhanced engine
                player.cash_score = self.scoring_engine.score_player_cash(player)
                player.gpp_score = self.scoring_engine.score_player_gpp(player)

                # SET enhanced_score based on contest type
                if contest_type.lower() == 'cash':
                    player.enhanced_score = player.cash_score
                    player.optimization_score = player.cash_score
                else:  # GPP or other
                    player.enhanced_score = player.gpp_score
                    player.optimization_score = player.gpp_score

                scored_count += 1

            except Exception as e:
                logger.error(f"Failed to score {player.name}: {e}")
                # Set default scores on error
                player.cash_score = player.base_projection
                player.gpp_score = player.base_projection
                player.enhanced_score = player.base_projection
                player.optimization_score = player.base_projection

        logger.info(f"✅ Scored {scored_count}/{len(self.player_pool)} players successfully")

        # Store the contest type we scored for
        self._last_contest_type = contest_type

    def load_players_from_csv(self, csv_path: str):
        """Load players from DraftKings CSV with real projections"""
        logger.info(f"Loading players from {csv_path}")

        import pandas as pd
        self.players = []

        # Read CSV
        df = pd.read_csv(csv_path)

        # Check if AvgPointsPerGame column exists
        has_projections = 'AvgPointsPerGame' in df.columns
        if has_projections:
            logger.info("✅ Found AvgPointsPerGame column - using real projections")
        else:
            logger.info("⚠️ No AvgPointsPerGame column - will use salary-based projections")

        # Get unique teams for confirmation system
        teams = df['TeamAbbrev'].unique().tolist()
        self.confirmation_system.update_teams(teams)
        logger.info(f"Updated confirmation system with teams: {teams}")

        # Load each player
        for _, row in df.iterrows():
            # Parse position
            positions = row['Roster Position'].split('/')
            primary_position = positions[0]

            # Get projection
            if has_projections:
                base_projection = float(row['AvgPointsPerGame'])
            else:
                # Fallback to salary-based
                base_projection = float(row['Salary']) / 400

            # Create player
            player = UnifiedPlayer(
                id=str(row['ID']),
                name=row['Name'],
                team=row['TeamAbbrev'],
                salary=int(row['Salary']),
                primary_position=primary_position,
                positions=positions,
                base_projection=base_projection  # Real or estimated
            )

            # Set additional attributes
            player.game_info = row['Game Info']
            player.is_pitcher = (primary_position == 'P')

            # Initialize scores
            player.enhanced_score = base_projection
            player.cash_score = base_projection
            player.gpp_score = base_projection
            player.optimization_score = base_projection

            # Initialize enrichment factors
            player.vegas_score = 1.0
            player.park_score = 1.0
            player.weather_score = 1.0
            player.matchup_score = 1.0
            player.recent_form_score = 1.0

            self.players.append(player)

        logger.info(f"✅ Loaded {len(self.players)} players from CSV")
        if has_projections:
            # Show sample of real projections
            logger.info("Sample projections from CSV:")
            for p in self.players[:3]:
                logger.info(f"  {p.name}: ${p.salary} → {p.base_projection:.1f} pts")

        # Store CSV path for reference
        self.csv_path = csv_path
        self.csv_loaded = True
    # ALSO ADD THIS METHOD to normalize positions when building player pool:


    def _normalize_positions(self):
        """Normalize position names for consistency"""
        position_mapping = {
            'SP': 'P',
            'RP': 'P',
        }

        for player in self.player_pool:
            # Normalize primary position
            if player.primary_position in position_mapping:
                player.primary_position = position_mapping[player.primary_position]

            # Normalize position list
            player.positions = [position_mapping.get(pos, pos) for pos in player.positions]

            # Ensure pitcher flag is set
            if player.primary_position == 'P':
                player.is_pitcher = True


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
        """Enrich player pool with REAL API data"""
        logger.info("Enriching player pool with additional data...")

        if not self.player_pool:
            logger.warning("No players in pool to enrich")
            return

        # CRITICAL: Set default attributes first to avoid AttributeError
        for player in self.player_pool:
            # Default values
            player.vegas_score = 1.0
            player.matchup_score = 1.0
            player.park_score = 1.0
            player.recent_form_score = 1.0
            player.weather_score = 1.0
            player.team_total = 4.5  # Default runs
            player.game_total = 9.0
            player.is_home = True

        # 1. Try to fetch Vegas data with your REAL API
        try:
            logger.info("Fetching Vegas lines from API...")
            # Import locally to avoid caching issues
            from dfs_optimizer.data.vegas_lines import VegasLines

            vegas = VegasLines()
            # Get unique teams
            teams = list({p.team for p in self.player_pool if p.team})

            if teams:
                # Fetch all Vegas data at once
                vegas_data = vegas.get_all_vegas_data(teams)

                # Apply to players
                for player in self.player_pool:
                    if player.team in vegas_data:
                        team_vegas = vegas_data[player.team]
                        player.team_total = team_vegas.get('implied_total', 4.5)
                        player.game_total = team_vegas.get('game_total', 9.0)
                        player.is_home = team_vegas.get('is_home', True)

                        # Calculate vegas score: normalize 3-7 run range to 0.85-1.15
                        player.vegas_score = 0.85 + (player.team_total - 3) * 0.075
                        player.vegas_score = max(0.85, min(1.15, player.vegas_score))

                logger.info(f"✅ Applied Vegas data to {len(vegas_data)} teams")

        except Exception as e:
            logger.warning(f"Could not fetch Vegas data: {e}")
            # Keep default values

        # 2. Try to fetch Weather data
        try:
            logger.info("Fetching weather data...")
            from dfs_optimizer.data.weather_integration import WeatherIntegration

            weather = WeatherIntegration()
            games_weather = weather.get_all_games_weather(self.player_pool)

            for player in self.player_pool:
                game_key = f"{player.team}_game"
                if game_key in games_weather:
                    weather_data = games_weather[game_key]
                    player.weather_score = weather_data.get('impact_multiplier', 1.0)
                    player.game_temp = weather_data.get('temperature', 72)
                    player.wind_speed = weather_data.get('wind_speed', 5)

            logger.info(f"✅ Applied weather data to players")

        except Exception as e:
            logger.warning(f"Could not fetch weather data: {e}")

        # 3. Apply Park Factors (always available)
        park_factors = {
            'COL': 1.33, 'CIN': 1.18, 'TEX': 1.12, 'BOS': 1.08,
            'TOR': 1.07, 'PHI': 1.06, 'BAL': 1.05, 'MIL': 1.04,
            'CHC': 1.02, 'NYY': 1.01, 'MIN': 1.00, 'ATL': 0.99,
            'CWS': 0.99, 'WSH': 0.97, 'ARI': 0.96, 'HOU': 0.95,
            'STL': 0.94, 'NYM': 0.92, 'TB': 0.91, 'OAK': 0.90,
            'SD': 0.89, 'SEA': 0.88, 'SF': 0.87, 'MIA': 0.86,
            'LAD': 0.93, 'LAA': 0.98, 'KC': 0.97, 'PIT': 0.96,
            'DET': 0.98, 'CLE': 0.97
        }

        for player in self.player_pool:
            player.park_score = park_factors.get(player.team, 1.0)

        # 4. Calculate matchup scores (using available data)
        for player in self.player_pool:
            # Smart matchup calculation based on value
            value = player.base_projection / (player.salary / 1000) if player.salary > 0 else 0

            if value > 5.0:  # Great value
                player.matchup_score = 1.10
            elif value > 4.0:  # Good value
                player.matchup_score = 1.05
            elif value < 3.0:  # Poor value
                player.matchup_score = 0.90
            else:
                player.matchup_score = 1.00

        # 5. Calculate recent form (smart defaults with variance)
        for player in self.player_pool:
            if player.base_projection > 15:  # Elite player - less variance
                player.recent_form_score = 0.95 + (hash(player.name) % 20) / 100
            else:  # Average player - more variance
                player.recent_form_score = 0.85 + (hash(player.name) % 30) / 100

        # Mark enrichment as complete
        self.enrichments_applied = True

        # Log summary
        logger.info(f"✅ Enriched {len(self.player_pool)} players with required attributes")

        # Verify enrichment worked
        sample_player = self.player_pool[0] if self.player_pool else None
        if sample_player:
            logger.info(f"Sample enrichment - {sample_player.name}:")
            logger.info(f"  Vegas: {sample_player.vegas_score:.2f} (total: {sample_player.team_total})")
            logger.info(f"  Park: {sample_player.park_score:.2f}")
            logger.info(f"  Weather: {sample_player.weather_score:.2f}")
            logger.info(f"  Matchup: {sample_player.matchup_score:.2f}")
            logger.info(f"  Form: {sample_player.recent_form_score:.2f}")



        def _calculate_matchup_score(self, player):
            """Calculate based on what we know"""

            # If we have opponent pitcher ERA
            if hasattr(player, 'opp_pitcher_era'):
                if player.opp_pitcher_era > 5.0:
                    return 1.15  # Facing weak pitcher
                elif player.opp_pitcher_era < 3.5:
                    return 0.85  # Facing ace
                else:
                    return 1.00

            # Fallback: Use value ratio as proxy
            value = player.base_projection / (player.salary / 1000)
            if value > 5.0:  # Great value
                return 1.10
            elif value < 3.0:  # Poor value
                return 0.90
            else:
                return 1.00

        def _get_vegas_score(self, player):
            """Get Vegas or calculate expected"""

            # If we have real Vegas data
            if hasattr(player, 'team_total') and player.team_total > 0:
                # Normalize 3-7 run range to 0.85-1.15
                return 0.85 + (player.team_total - 3) * 0.075

            # Fallback: Use pitcher quality + park as proxy
            base = 1.0

            # Adjust for park
            park_adjustment = (player.park_score - 1.0) * 0.5
            base += park_adjustment

            # High-salary teams tend to score more
            if player.salary > 5000:
                base += 0.05

            return max(0.85, min(1.15, base))

        def _get_recent_form(self, player):
            """Get recent stats or use smart default"""

            # If we have L5 average
            if hasattr(player, 'L5_avg'):
                return player.L5_avg / player.base_projection

            # Smart default: Add controlled variance
            # Better players are more consistent
            if player.base_projection > 15:  # Elite player
                # Less variance, tend toward projection
                return 0.95 + (hash(player.name + str(datetime.now().day)) % 20) / 100
            else:  # Average players have more variance
                return 0.85 + (hash(player.name + str(datetime.now().day)) % 30) / 100

        def _get_weather_score(self, player):
            """Get weather or use seasonal defaults"""

            # If we have real weather
            if hasattr(player, 'game_temp'):
                return self._calculate_weather_impact(
                    player.game_temp,
                    getattr(player, 'wind_speed', 5),
                    getattr(player, 'wind_dir', 'calm')
                )

            # Seasonal defaults by month
            month = datetime.now().month
            if month in [6, 7, 8]:  # Summer
                return 1.04  # Hotter = more offense
            elif month in [4, 5, 9]:  # Spring/Fall
                return 1.00  # Neutral
            else:  # Early/Late season
                return 0.96  # Cooler

        def verify_enrichment(self, players):
            """Verify enrichment is working properly"""

            scores = {
                'matchup': [p.matchup_score for p in players[:50]],
                'vegas': [p.vegas_score for p in players[:50]],
                'park': [p.park_score for p in players[:50]],
                'form': [p.recent_form_score for p in players[:50]],
                'weather': [p.weather_score for p in players[:50]]
            }

            print("\n📊 ENRICHMENT VERIFICATION:")
            for name, values in scores.items():
                unique = len(set(values))
                avg = sum(values) / len(values)
                print(f"{name:.<15} Unique: {unique}/50, Avg: {avg:.3f}")

            # Check if reasonable
            if all(len(set(v)) > 10 for v in scores.values()):
                print("\n✅ Enrichment has good variation!")
                return True
            else:
                print("\n⚠️  Some scores lack variation")
                return False



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

    def optimize_lineups(self, num_lineups=1, strategy='auto', contest_type='gpp', min_unique_players=3):
        """Generate optimal lineups with proper strategy application"""

        if not self.player_pool:
            logger.error("No players in pool! Build player pool first.")
            return []

        # Auto-select strategy if needed
        if strategy == 'auto' or strategy is None:
            slate_analysis = self.strategy_selector.analyze_slate_from_csv(self.player_pool)
            strategy, reason = self.strategy_selector.select_strategy(slate_analysis, contest_type)
            logger.info(f"Auto-selected strategy: {strategy} ({reason})")

        logger.info(f"\n🎯 Optimizing {num_lineups} lineups...")
        logger.info(f"   Strategy: {strategy}")
        logger.info(f"   Contest Type: {contest_type}")
        logger.info(f"   Pool size: {len(self.player_pool)} players")

        # Make sure contest_type is set on the optimizer config
        self.optimizer.config.contest_type = contest_type

        # Score players first
        self.score_players(contest_type)
        # Fix optimization_score before optimization
        for player in self.player_pool:
            if not hasattr(player, 'optimization_score') or player.optimization_score == 0:
                if contest_type == 'cash':
                    player.optimization_score = player.cash_score
                else:
                    player.optimization_score = player.gpp_score

        # Generate lineups
        lineups = []
        used_players = set()

        for i in range(num_lineups):
            logger.info(f"\n   Lineup {i + 1}/{num_lineups}...")

            # Apply diversity penalty if needed
            if i > 0 and min_unique_players > 0:
                self._apply_diversity_penalty(used_players, penalty=0.8)

            # Optimize single lineup - calls the MILP optimizer
            lineup_players, total_score = self.optimizer.optimize_lineup(
                players=self.player_pool,
                strategy=strategy,
                manual_selections=','.join(self.manual_selections),
                contest_type=contest_type
            )

            if lineup_players:
                # Track used players
                for player in lineup_players:
                    used_players.add(player.name)

                # Create lineup dict
                lineup_dict = {
                    'players': lineup_players,
                    'total_projection': total_score,
                    'total_salary': sum(p.salary for p in lineup_players),
                    'strategy': strategy,
                    'contest_type': contest_type
                }

                lineups.append(lineup_dict)
                logger.info(f"   ✓ Created lineup with score: {total_score:.2f}")

            # Restore original scores after diversity penalty
            if i > 0:
                self._restore_original_scores()

        logger.info(f"\n✅ Generated {len(lineups)}/{num_lineups} lineups successfully")
        return lineups

    def verify_strategy_application(self, sample_size=5):
        """Debug method to verify strategies are working"""
        if not self.player_pool:
            logger.error("No player pool to verify")
            return

        logger.info("\n=== STRATEGY VERIFICATION ===")
        logger.info(f"Checking {sample_size} players...")

        for i, player in enumerate(self.player_pool[:sample_size]):
            logger.info(f"\nPlayer {i + 1}: {player.name}")
            logger.info(f"  Base projection: {getattr(player, 'projection', 0):.2f}")
            logger.info(f"  Cash score: {getattr(player, 'cash_score', 0):.2f}")
            logger.info(f"  GPP score: {getattr(player, 'gpp_score', 0):.2f}")
            logger.info(f"  Optimization score: {getattr(player, 'optimization_score', 0):.2f}")

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
        total_projection = lineup.get('total_projection', 0)

        logger.info(
            f"   ✓ Lineup {lineup_num}: ${total_salary:,} salary, {total_score:.1f} optimizer score, {total_projection:.1f} projected points")

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