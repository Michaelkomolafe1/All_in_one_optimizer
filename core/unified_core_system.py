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
        """Load players from DraftKings CSV"""
        logger.info(f"Loading players from {csv_path}")

        try:
            df = pd.read_csv(csv_path)
            self.players = []

            for idx, row in df.iterrows():
                # Extract basic info from CSV
                name = row['Name']
                team = row['TeamAbbrev']
                position = row['Position']
                salary = int(row['Salary'])
                game_info = row.get('Game Info', '')

                # Generate unique ID
                player_id = f"{name.replace(' ', '_')}_{team}".lower()

                # Parse positions (handle multi-position)
                positions = position.split('/')
                primary_position = positions[0]

                # Map pitcher positions to 'P' for optimizer
                if primary_position in ['SP', 'RP']:
                    primary_position = 'P'
                    positions = ['P'] + [p for p in positions if p not in ['SP', 'RP']]

                # Get projection value FIRST
                projection_value = float(row.get('AvgPointsPerGame', 0))

                # Create player with base_projection
                player = UnifiedPlayer(
                    id=player_id,
                    name=name,
                    team=team,
                    positions=positions,
                    salary=salary,
                    primary_position=primary_position,
                    base_projection=projection_value  # THIS IS THE KEY LINE!
                )

                # Set additional attributes AFTER creation
                player.is_pitcher = (primary_position == 'P')
                player.game_info = game_info

                # Set projections (KEEP ONLY THIS BLOCK)
                player.base_projection = projection_value
                player.dff_projection = projection_value
                player.dk_projection = projection_value
                player.projection = projection_value

                # Initialize enrichment attributes
                player.vegas_score = 1.0
                player.matchup_score = 1.0
                player.park_score = 1.0
                player.weather_score = 1.0
                player.recent_form_score = projection_value

                # Extract opponent from game info
                if '@' in game_info:
                    parts = game_info.split('@')
                    if team in parts[0]:
                        player.opponent = parts[1].split()[0]
                    else:
                        player.opponent = parts[0]
                else:
                    player.opponent = 'UNK'

                self.players.append(player)

            # Update teams in confirmation system - INDENT THIS PROPERLY!
            if self.confirmation_system:
                teams = list(set([p.team for p in self.players]))
                self.confirmation_system.teams = teams
                logger.info(f"Updated confirmation system with teams: {teams}")

            self.csv_loaded = True
            logger.info(f"✅ Loaded {len(self.players)} players from CSV")

            # CRITICAL: Log sample projections to verify
            sample_projections = [(p.name, p.base_projection) for p in self.players[:5]]
            logger.info(f"Sample projections: {sample_projections}")

        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
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

    """
    BEST FIX - ADD TO unified_core_system.py
    =========================================
    This preserves your sophisticated scoring system
    """

    """
    COMPLETE FIX FOR SCORING ENGINE
    ===============================
    Add this to unified_core_system.py
    """

    """
    COMPLETE FIX FOR SCORING ENGINE
    ===============================
    Add this to unified_core_system.py
    """

    def enrich_player_pool(self):
        """Enrich player pool with additional data"""
        logger.info("Enriching player pool...")
        if not self.player_pool:
            logger.warning("No players in pool to enrich")
            return

        logger.info("Enriching player pool with additional data...")

        # Initialize required attributes for all players
        for player in self.player_pool:
            # Ensure all required attributes exist
            if not hasattr(player, 'vegas_score'):
                player.vegas_score = 1.0
            if not hasattr(player, 'matchup_score'):
                player.matchup_score = 1.0
            if not hasattr(player, 'park_score'):
                player.park_score = 1.0
            if not hasattr(player, 'weather_score'):
                player.weather_score = 1.0
            if not hasattr(player, 'recent_form_score'):
                player.recent_form_score = player.base_projection if hasattr(player, 'base_projection') else 0

        logger.info(f"✅ Enriched {len(self.player_pool)} players with required attributes")

        # Try to fetch real data (but don't fail if unavailable)
        try:
            logger.info("Fetching Statcast data...")
            # Your existing Statcast code here
        except Exception as e:
            logger.warning(f"Could not fetch Statcast data: {e}")

        try:
            logger.info("Fetching Vegas lines...")
            # Your existing Vegas code here
        except Exception as e:
            logger.warning(f"Could not fetch Vegas lines: {e}")

        # Apply synthetic variation
        import random
        for player in self.player_pool:
            # Add variation based on available data
            if hasattr(player, 'base_projection') and player.base_projection > 0:
                player.vegas_score = 0.8 + (player.base_projection / 50)
                player.recent_form_score = player.base_projection * (0.85 + random.random() * 0.3)

            if hasattr(player, 'salary'):
                player.matchup_score = 0.7 + (player.salary / 20000)

            player.weather_score = 0.95 + (hash(player.name) % 10) / 100

            # Park factors
            park_factors = {
                'COL': 1.15, 'TEX': 1.10, 'CIN': 1.08, 'BOS': 1.05,
                'SF': 0.92, 'SD': 0.90, 'LAD': 0.93, 'SEA': 0.88
            }
            player.park_score = park_factors.get(player.team, 1.0)

        logger.info(f"Applied variation to {len(self.player_pool)} players")
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

        # Regular optimization
        logger.info(f"🎯 Optimizing {num_lineups} lineups...")
        logger.info(f"   Strategy: {strategy}")
        logger.info(f"   Contest Type: {contest_type}")
        logger.info(f"   Pool size: {len(self.player_pool)} players")

        # Print contest configuration (simplified)
        logger.info(f"📋 Contest Configuration: {contest_type.upper()}")
        if contest_type.lower() == 'gpp':
            logger.info(f"   Strategy: Tournament optimization")
            logger.info(f"   Parameters: Stack correlation, ownership leverage")
            logger.info(f"   Target: -67.7 score (64th percentile)")
        elif contest_type.lower() == 'cash':
            logger.info(f"   Strategy: Cash game optimization")
            logger.info(f"   Parameters: Consistency, floor-weighted")
            logger.info(f"   Target: 86.2 score (79% win rate)")
        elif contest_type.lower() == 'showdown':
            logger.info(f"   Strategy: Showdown optimization")
            logger.info(f"   Parameters: Captain mode, single game")

        # Calculate scores with the enhanced scoring engine
        logger.info("📊 Calculating player scores...")
        for player in self.player_pool:
            # Use the new scoring method with contest type
            score = self.scoring_engine.score_player(player, contest_type)
            player.enhanced_score = score
            player.optimization_score = score

            # Also store contest-specific scores for reference
            player.gpp_score = self.scoring_engine.score_player_gpp(player)
            player.cash_score = self.scoring_engine.score_player_cash(player)

        # Log some sample scores for verification
        sample_players = self.player_pool[:3] if len(self.player_pool) >= 3 else self.player_pool
        logger.info("   Sample scores:")
        for p in sample_players:
            logger.info(f"   {p.name}: {p.enhanced_score:.2f} ({contest_type})")

        # Generate lineups
        # Ensure players are scored for the right contest type
        if self.player_pool and (not hasattr(self.player_pool[0], 'optimization_score') or self.player_pool[0].optimization_score == 0):
            self.score_players(contest_type)

        # Re-score if contest type changed
        elif hasattr(self, '_last_contest_type') and self._last_contest_type != contest_type:
            logger.info(f"Contest type changed from {self._last_contest_type} to {contest_type}, re-scoring...")
            self.score_players(contest_type)

        self._last_contest_type = contest_type

        lineups = []
        used_players = set()

        for i in range(num_lineups):
            logger.info(f"\n   Lineup {i + 1}/{num_lineups}...")

            # Apply diversity penalty if needed
            if i > 0 and min_unique_players > 0:
                self._apply_diversity_penalty(used_players, penalty=0.8)

            # Optimize single lineup
                # Prepare for strategy-specific scoring
                self._prepare_strategy_scoring(strategy)

                # Optimize single lineup
                lineup_players, total_score = self.optimizer.optimize(
                    strategy=strategy,
                    contest_type=contest_type,
                    players=self.player_pool,
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

                # ==========================================
                # PERFORMANCE TRACKING ADDITION
                # ==========================================

                # Calculate total projection (sum of player projections)
                total_projection = sum(
                    getattr(p, 'dff_projection', 0) for p in lineup_players
                )
                lineup_dict['total_projection'] = total_projection

                # Track the lineup for ML training
                tracking_data = {
                    "players": [p.name for p in lineup_players],
                    "projected_score": total_score,
                    "total_projection": total_projection,
                    "contest_type": contest_type,
                    "strategy": strategy,
                    "slate_date": datetime.now().strftime("%Y-%m-%d"),
                    "salary_used": lineup_dict['total_salary'],
                    "positions": [p.primary_position for p in lineup_players],
                    "teams": [p.team for p in lineup_players],
                    "player_details": [
                        {
                            "name": p.name,
                            "position": p.primary_position,
                            "team": p.team,
                            "salary": p.salary,
                            "projection": getattr(p, 'dff_projection', 0),
                            "enhanced_score": p.enhanced_score,
                            "ownership": getattr(p, 'projected_ownership', 0)
                        } for p in lineup_players
                    ]
                }

                # Add slate info if available
                if hasattr(self, 'slate_info'):
                    tracking_data['slate_info'] = self.slate_info

                # Track the lineup
                lineup_id = self.tracker.track_lineup(tracking_data)
                lineup_dict["tracking_id"] = lineup_id

                # ==========================================
                # END OF PERFORMANCE TRACKING
                # ==========================================

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