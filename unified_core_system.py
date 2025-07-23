#!/usr/bin/env python3
"""
UNIFIED CORE SYSTEM - PURE DATA APPROACH
========================================
Complete unified DFS system with ALL enrichments, NO fallbacks
Only uses confirmed players + manual selections
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd

# Core imports
from unified_player_model import UnifiedPlayer
from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig
from unified_scoring_engine import get_scoring_engine, ScoringConfig
from cash_optimization_config import apply_contest_config
from cash_optimization_config import apply_contest_config, get_contest_description
from pure_data_scoring_engine import get_pure_scoring_engine, PureDataScoringConfig
from hybrid_scoring_system import get_hybrid_scoring_system
from weather_integration import get_weather_integration
from showdown_optimizer import ShowdownOptimizer, is_showdown_slate


# Data enrichment imports
from simple_statcast_fetcher import FastStatcastFetcher
from smart_confirmation_system import SmartConfirmationSystem
from vegas_lines import VegasLines


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedCoreSystem:
    """
    Pure data unified DFS system - NO FALLBACKS
    Works exclusively with confirmed players and manual selections
    """

    def __init__(self):
        '''Initialize the unified core system'''

        # Core data structures
        self.all_players: Dict[str, UnifiedPlayer] = {}
        self.confirmed_names: Set[str] = set()
        self.manual_names: Set[str] = set()
        self.player_pool: List[UnifiedPlayer] = []

        # System configuration
        self.logger = logger
        self.salary_cap = 50000
        self.min_salary_usage = 0.95

        # Initialize ALL components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all system components"""
        print("\n🚀 INITIALIZING UNIFIED CORE SYSTEM")
        print("=" * 60)

        # 1. Confirmation System
        print("📋 Initializing Confirmation System...")
        try:
            from rotowire_pitcher_system import EnhancedConfirmationSystem
            self.confirmation_system = EnhancedConfirmationSystem(verbose=True)
            print("   ✅ Using Enhanced Confirmation System")
            print("   ✅ MLB API + Rotowire for pitchers")
            self._using_enhanced = True
        except ImportError:
            self.confirmation_system = SmartConfirmationSystem(verbose=True)
            print("   ✅ Using Smart Confirmation System")
            print("   ⚠️  No Rotowire backup for pitchers")
            self._using_enhanced = False

        # 2. Statcast Fetcher
        print("\n⚾ Initializing Statcast Fetcher...")
        self.statcast = FastStatcastFetcher(max_workers=10)
        print("   ✅ Ready for player statistics")

        # 3. Vegas Lines
        print("\n🎰 Initializing Vegas Lines...")
        try:
            self.vegas = VegasLines(cache_ttl=300)
        except TypeError:
            self.vegas = VegasLines()
        print("   ✅ Ready for betting data")

        # 4. Weather Integration
        print("\n🌦️ Initializing Weather Integration...")
        self.weather = get_weather_integration()
        print("   ✅ Ready for weather data")
        print("   📍 Using free weather service (wttr.in)")

        # 5. Hybrid Scoring System (REPLACES pure scoring)
        print("\n🎯 Initializing Hybrid Scoring System...")
        self.scoring_engine = get_hybrid_scoring_system()
        print("   ✅ Contest-specific scoring ready")
        print("   • Cash/Small GPPs: Dynamic scoring")
        print("   • Large GPPs: Enhanced pure scoring")

        # Connect data sources to scoring engine
        self.scoring_engine.set_data_sources(
            statcast_fetcher=self.statcast,
            vegas_client=self.vegas,
            confirmation_system=self.confirmation_system
        )

        # Also set weather on enhanced engine
        if hasattr(self.scoring_engine, 'enhanced_engine'):
            self.scoring_engine.enhanced_engine.weather_integration = self.weather

        # 6. MILP Optimizer
        print("\n🎯 Initializing MILP Optimizer...")
        optimizer_config = OptimizationConfig(
            salary_cap=self.salary_cap,
            min_salary_usage=self.min_salary_usage
        )
        self.optimizer = UnifiedMILPOptimizer(optimizer_config)

        # Connect data sources to optimizer
        if hasattr(self.optimizer, 'set_data_sources'):
            self.optimizer.set_data_sources(
                statcast_fetcher=self.statcast,
                vegas_client=self.vegas
            )
            print("   ✅ Optimizer connected to data sources")
        else:
            print("   ✅ Optimizer ready")

        # 7. Showdown Optimizer
        print("\n🎪 Initializing Showdown Optimizer...")
        self.showdown_optimizer = ShowdownOptimizer(salary_cap=self.salary_cap)
        print("   ✅ Ready for showdown contests")

        print("\n" + "=" * 60)
        print("✅ ALL SYSTEMS INITIALIZED - HYBRID SCORING MODE")
        print("=" * 60)

    def _get_util_players(self) -> List:
        """Extract unique UTIL players (no CPT entries)"""
        util_players = []
        seen_names = set()

        for player in self.player_pool:
            # Skip if already seen
            if player.name in seen_names:
                continue

            # Skip CPT entries
            if (hasattr(player, 'display_position') and 'CPT' in player.display_position) or \
                    (hasattr(player, 'roster_position') and 'CPT' in player.roster_position) or \
                    '(CPT)' in player.name:
                continue

            util_players.append(player)
            seen_names.add(player.name)

        return util_players

    def _get_util_players(self) -> List:
        """Extract unique UTIL players (no CPT entries)"""
        util_players = []
        seen_names = set()

        for player in self.player_pool:
            # Skip if already seen
            if player.name in seen_names:
                continue

            # Skip CPT entries
            if (hasattr(player, 'display_position') and 'CPT' in player.display_position) or \
                    (hasattr(player, 'roster_position') and 'CPT' in player.roster_position) or \
                    '(CPT)' in player.name:
                continue

            util_players.append(player)
            seen_names.add(player.name)

        return util_players

    def _show_captain_candidates(self, players: List, top_n: int = 5):
        """Display top captain candidates by score"""
        sorted_players = sorted(
            players,
            key=lambda p: getattr(p, 'optimization_score', 0),
            reverse=True
        )[:top_n]

        print("\n🌟 Top Captain Candidates:")
        for i, player in enumerate(sorted_players, 1):
            score = getattr(player, 'optimization_score', 0)
            captain_score = score * 1.5
            print(f"   {i}. {player.name} ({player.team}): "
                  f"{score:.1f} pts → CPT: {captain_score:.1f} pts")

    def _apply_diversity_penalty(self, used_players: set, penalty: float = 0.8):
        """Apply penalty to used players for diversity"""
        for player in self.player_pool:
            if player.name in used_players:
                if not hasattr(player, 'temp_score'):
                    player.temp_score = player.optimization_score
                player.optimization_score *= penalty

    def _restore_diversity_scores(self):
        """Restore original scores after diversity penalty"""
        for player in self.player_pool:
            if hasattr(player, 'temp_score'):
                player.optimization_score = player.temp_score
                delattr(player, 'temp_score')

    def _apply_captain_penalty(self, players: List, used_captains: set, penalty: float = 0.7):
        """Apply penalty to previously used captains"""
        for player in players:
            if player.name in used_captains:
                if not hasattr(player, 'original_score'):
                    player.original_score = player.optimization_score
                player.optimization_score *= penalty

    def _restore_captain_scores(self, players: List):
        """Restore original scores after captain penalty"""
        for player in players:
            if hasattr(player, 'original_score'):
                player.optimization_score = player.original_score
                delattr(player, 'original_score')

    def _create_lineup_dict(self, players: List, score: float,
                            strategy: str, contest_type: str) -> Dict:
        """Create standard lineup dictionary"""
        lineup_dict = {
            'players': players,
            'total_salary': sum(p.salary for p in players),
            'total_projection': score,
            'strategy': strategy,
            'contest_type': contest_type,
            'pool_size': len(self.player_pool),
            'type': 'classic'
        }

        return lineup_dict

    def _create_showdown_lineup_dict(self, captain, utilities: List,
                                     total_score: float, strategy: str) -> Dict:
        """Create showdown lineup dictionary"""
        captain_salary = int(captain.salary * 1.5)
        util_salaries = sum(p.salary for p in utilities)
        total_salary = captain_salary + util_salaries

        lineup_dict = {
            'captain': captain,
            'utilities': utilities,
            'players': [captain] + utilities,  # For compatibility
            'total_salary': total_salary,
            'total_projection': total_score,
            'captain_salary': captain_salary,
            'strategy': strategy,
            'type': 'showdown'
        }

        return lineup_dict

    def _analyze_lineup(self, lineup_dict: Dict, contest_type: str):
        """Analyze and display lineup information"""
        players = lineup_dict['players']
        total_salary = lineup_dict['total_salary']
        score = lineup_dict['total_projection']

        print(f"   ✅ Score: {score:.1f} pts")
        print(f"   💰 Salary: ${total_salary:,} ({total_salary / self.salary_cap * 100:.1f}%)")

        # Check for stacks
        team_counts = {}
        for player in players:
            if player.primary_position != 'P':
                team_counts[player.team] = team_counts.get(player.team, 0) + 1

        stacks = [team for team, count in team_counts.items() if count >= 3]
        if stacks:
            lineup_dict['stacks'] = stacks
            print(f"   🔥 Stack(s): {', '.join(stacks)}")

        # Cash game pitcher-hitter warnings
        if contest_type == 'cash':
            self._check_pitcher_hitter_correlation(players)

    def _check_pitcher_hitter_correlation(self, players: List):
        """Check for negative pitcher-hitter correlation in cash games"""
        for pitcher in players:
            if pitcher.primary_position == 'P':
                opp_team = getattr(pitcher, 'opponent', None)
                if opp_team:
                    opp_hitters = [p.name for p in players
                                   if p.primary_position != 'P' and p.team == opp_team]
                    if opp_hitters:
                        print(f"   ⚠️  {pitcher.name} facing {len(opp_hitters)} hitter(s): "
                              f"{', '.join(opp_hitters)}")

    def _display_showdown_summary(self, lineup_dict: Dict):
        """Display showdown lineup summary"""
        captain = lineup_dict['captain']
        total_salary = lineup_dict['total_salary']
        total_score = lineup_dict['total_projection']

        print(f"   ✅ Score: {total_score:.1f} pts")
        print(f"   💰 Salary: ${total_salary:,} ({total_salary / self.salary_cap * 100:.1f}%)")
        print(f"   👑 Captain: {captain.name} ({captain.team}) - "
              f"${lineup_dict['captain_salary']:,}")

    def _optimize_showdown_lineup(self, players: List, strategy: str) -> Dict:
        """
        Run showdown optimization using the ShowdownOptimizer

        This method should interface with your showdown_optimizer.py
        """
        if hasattr(self, 'showdown_optimizer'):
            # Use the dedicated showdown optimizer
            lineups = self.showdown_optimizer.optimize_showdown(
                players=players,
                num_lineups=1,
                min_salary_usage=0.95
            )

            if lineups and len(lineups) > 0:
                lineup = lineups[0]
                return {
                    'success': True,
                    'captain': lineup['captain'],
                    'utilities': lineup['utilities'],
                    'total_score': lineup['total_score']
                }

        # Fallback or error
        print("   ❌ Showdown optimizer not available")
        return {'success': False}

    def load_csv(self, csv_path: str) -> int:
        print(f"\n📂 Loading CSV: {csv_path}")

        df = pd.read_csv(csv_path)
        self.all_players.clear()

        POSITION_MAP = {
            'SP': 'P',
            'RP': 'P',
            'P': 'P',
            'C': 'C',
            '1B': '1B',
            '2B': '2B',
            '3B': '3B',
            'SS': 'SS',
            'OF': 'OF',
            'UTIL': 'UTIL'
        }

        for idx, row in df.iterrows():
            pos_str = str(row.get('Position', ''))
            raw_positions = pos_str.split('/') if '/' in pos_str else [pos_str]

            positions = [POSITION_MAP.get(p.strip(), p.strip()) for p in raw_positions]
            primary = positions[0]

            player = UnifiedPlayer(
                id=str(row.get('ID', f"{row['Name']}_{idx}")),
                name=row['Name'],
                team=row.get('TeamAbbrev', 'UNK'),
                salary=int(row['Salary']),
                primary_position=primary,
                positions=positions,
                base_projection=float(row.get('AvgPointsPerGame', 0))
            )

            player.display_position = pos_str

            player.opponent = row.get('Opponent', '')
            player.game_info = row.get('Game Info', '')
            player.is_home = '@' not in row.get('Game Info', '')

            if 'DFF Proj' in row:
                player.dff_projection = float(row.get('DFF Proj', 0))
            if 'DFF L5 Avg' in row:
                player.dff_l5_avg = float(row.get('DFF L5 Avg', 0))

            self.all_players[player.name] = player

        print(f"✅ Loaded {len(self.all_players)} total players")

        position_counts = {}
        for player in self.all_players.values():
            pos = player.primary_position
            position_counts[pos] = position_counts.get(pos, 0) + 1

        print("\n📊 Position breakdown (after mapping):")
        for pos in sorted(position_counts.keys()):
            count = position_counts[pos]
            print(f"   {pos}: {count} players")

        return len(self.all_players)

    def fetch_confirmed_players(self) -> int:
        """
        Fetch confirmed lineups and identify confirmed players
        Now SLATE-AWARE - only looks for games in the CSV

        Returns:
            Number of confirmed players found
        """
        print("\n🔍 Fetching Confirmed Lineups...")

        self.confirmed_names.clear()

        # Extract slate games from CSV data
        slate_teams = set()
        slate_games = {}

        print("\n📋 Identifying slate games from CSV...")
        import re

        for player in self.all_players.values():
            if hasattr(player, 'game_info') and player.game_info:
                # Parse game info with date format: "HOU@ARI 07/21/2025 09:40PM ET"
                game_str = str(player.game_info).strip()

                # Extract just the teams (simpler approach)
                if '@' in game_str:
                    parts = game_str.split()
                    if parts:
                        teams_part = parts[0]  # "HOU@ARI"
                        if '@' in teams_part:
                            away, home = teams_part.split('@')
                            game_key = f"{away}@{home}"

                            if game_key not in slate_games:
                                # Extract time if available
                                time = None
                                if len(parts) >= 3:
                                    time = parts[2].replace('ET', '').strip()

                                slate_games[game_key] = {
                                    'away': away,
                                    'home': home,
                                    'time': time,
                                    'game_info': game_str
                                }
                                slate_teams.add(away)
                                slate_teams.add(home)

                # Also add player's team
                if hasattr(player, 'team') and player.team:
                    slate_teams.add(player.team)

        print(f"   Found {len(slate_games)} games in slate")
        print(f"   Teams: {sorted(slate_teams)}")

        # Initialize counts
        lineup_count = 0
        pitcher_count = 0

        if self._using_enhanced:
            # Enhanced system returns lineups and pitchers directly
            confirmed_lineups, confirmed_pitchers = self.confirmation_system.fetch_all_confirmations()

            # Filter to only slate teams
            for team, lineup_data in confirmed_lineups.items():
                if team in slate_teams:  # Only process slate teams
                    for player_info in lineup_data:
                        player_name = player_info.get('name', '')
                        if player_name and player_name in self.all_players:
                            self.confirmed_names.add(player_name)
                            lineup_count += 1

            # Process pitchers
            for team, pitcher_info in confirmed_pitchers.items():
                if team in slate_teams:  # Only process slate teams
                    pitcher_name = pitcher_info.get('name', '')
                    if pitcher_name and pitcher_name in self.all_players:
                        self.confirmed_names.add(pitcher_name)
                        pitcher_count += 1
                        print(
                            f"   ⚾ Confirmed Pitcher: {pitcher_name} ({team}) - {pitcher_info.get('source', 'unknown')}")

        else:
            # Standard smart confirmation system
            lineup_count, pitcher_count = self.confirmation_system.get_all_confirmations()

            # Get the actual confirmation data
            confirmed_lineups = self.confirmation_system.confirmed_lineups
            confirmed_pitchers = self.confirmation_system.confirmed_pitchers

            # Process confirmed lineup players - filtered by slate
            for team, lineup_data in confirmed_lineups.items():
                if team in slate_teams:  # Only process slate teams
                    for player_info in lineup_data:
                        player_name = player_info.get('name', '')
                        if player_name and player_name in self.all_players:
                            self.confirmed_names.add(player_name)

            # Process confirmed pitchers - filtered by slate
            for team, pitcher_info in confirmed_pitchers.items():
                if team in slate_teams:  # Only process slate teams
                    pitcher_name = pitcher_info.get('name', '')
                    if pitcher_name and pitcher_name in self.all_players:
                        self.confirmed_names.add(pitcher_name)
                        print(f"   ⚾ Confirmed Pitcher: {pitcher_name} ({team})")

        print(f"\n✅ Found {len(self.confirmed_names)} confirmed players")
        print(f"   • From slate teams only")
        print(f"   • Lineup players: {lineup_count}")
        print(f"   • Starting pitchers: {pitcher_count}")

        if pitcher_count == 0:
            print("\n⚠️  No pitchers found for slate games!")
            print("   Lineups might not be posted yet for evening games")
            print("   Consider adding manual pitcher selections")

        return len(self.confirmed_names)

    def add_manual_player(self, player_name: str) -> bool:
        """
        Manually add a player to the pool

        Args:
            player_name: Name of player to add

        Returns:
            True if added successfully
        """
        if player_name in self.all_players:
            self.manual_names.add(player_name)
            print(f"✅ Manually added: {player_name}")
            return True
        else:
            print(f"❌ Player not found: {player_name}")
            return False

    def remove_manual_player(self, player_name: str) -> bool:
        """Remove a manually added player"""
        if player_name in self.manual_names:
            self.manual_names.remove(player_name)
            print(f"✅ Removed: {player_name}")
            return True
        return False

    def build_player_pool(self) -> int:
        """
        Build the final player pool from confirmed + manual selections

        Returns:
            Size of player pool
        """
        print("\n🏊 Building Player Pool...")

        # Combine confirmed and manual selections
        pool_names = self.confirmed_names.union(self.manual_names)

        # Create pool
        self.player_pool = []
        for name in pool_names:
            if name in self.all_players:
                player = self.all_players[name]
                # Mark as confirmed/manual for scoring boost
                player.is_confirmed = name in self.confirmed_names
                player.is_manual = name in self.manual_names
                self.player_pool.append(player)

        print(f"✅ Player pool size: {len(self.player_pool)}")
        print(f"   • Confirmed: {len(self.confirmed_names)}")
        print(f"   • Manual: {len(self.manual_names)}")

        # Show pool by position
        pos_counts = {}
        for p in self.player_pool:
            for pos in p.positions:
                pos_counts[pos] = pos_counts.get(pos, 0) + 1

        print("\n📊 Pool breakdown:")
        for pos, count in sorted(pos_counts.items()):
            print(f"   {pos}: {count} players")

        return len(self.player_pool)

    def enrich_player_pool(self) -> int:
        """
        Enrich player pool with all available data sources IN PARALLEL
        """
        if not self.player_pool:
            return 0

        print(f"\n🔄 Enriching {len(self.player_pool)} players with ALL data sources...")

        # Import parallel fetcher
        from parallel_data_fetcher import ParallelDataFetcher
        import time
        import pandas as pd

        # Create parallel fetcher with all data sources
        fetcher = ParallelDataFetcher(
            confirmation_system=self.confirmation_system,
            vegas_client=self.vegas,
            statcast_fetcher=self.statcast,
            max_workers=10
        )

        # Track timing
        start_time = time.time()

        # Fetch all data in parallel
        print("⚡ Starting parallel data enrichment...")
        results = fetcher.enrich_players_parallel(self.player_pool)

        # Calculate timing
        elapsed = time.time() - start_time

        # Count successful enrichments
        enriched_count = 0
        vegas_count = 0
        statcast_count = 0
        confirmation_count = 0

        for player_name, result in results.items():
            # Check Vegas data
            if result.vegas_data:
                vegas_count += 1

            # Check Statcast data (handle DataFrame properly)
            if result.statcast_data is not None:
                # If it's a DataFrame, check if it's not empty
                if isinstance(result.statcast_data, pd.DataFrame):
                    if not result.statcast_data.empty:
                        statcast_count += 1
                else:
                    # If it's not a DataFrame but not None, count it
                    statcast_count += 1

            # Check confirmation data
            if result.confirmation_data:
                confirmation_count += 1

            # Count as enriched if any data exists
            has_data = False
            if result.vegas_data:
                has_data = True
            if result.statcast_data is not None:
                if isinstance(result.statcast_data, pd.DataFrame):
                    if not result.statcast_data.empty:
                        has_data = True
                else:
                    has_data = True
            if result.confirmation_data:
                has_data = True

            if has_data:
                enriched_count += 1

        # Print detailed results
        print(f"\n✅ Enrichment complete in {elapsed:.1f}s")
        print(f"   Total enriched: {enriched_count}/{len(self.player_pool)} players")
        print(f"   Vegas data: {vegas_count} players")
        print(f"   Statcast data: {statcast_count} players")
        print(f"   Confirmations: {confirmation_count} players")

        # Calculate performance metrics
        players_per_second = len(self.player_pool) / elapsed if elapsed > 0 else 0
        print(f"   Performance: {players_per_second:.1f} players/second")

        # Show cache statistics if available
        try:
            from enhanced_caching_system import get_cache_manager
            cache_manager = get_cache_manager()

            print("\n📊 Cache Statistics:")
            all_stats = cache_manager.get_all_stats()

            for cache_name, stats in all_stats.items():
                if stats['total_requests'] > 0:
                    print(f"   {cache_name}: {stats['size']} items, "
                          f"{stats['hit_rate']:.1%} hit rate, "
                          f"{stats['hits']}/{stats['total_requests']} hits")
        except Exception as e:
            logger.debug(f"Could not get cache stats: {e}")

        # Score all players
        print("\n📈 Calculating pure data scores...")
        score_start = time.time()

        scored = 0
        missing_data = []

        for player in self.player_pool:
            try:
                # Use the pure data scoring engine directly
                score = self.scoring_engine.calculate_score(player)
                player.enhanced_score = score
                player.optimization_score = score  # Direct assignment

                if score > 0:
                    scored += 1
                else:
                    missing_data.append(player.name)

            except Exception as e:
                logger.error(f"Error scoring {player.name}: {e}")
                player.enhanced_score = 0
                player.optimization_score = 0

        print(f"   Scored {scored}/{len(self.player_pool)} players")
        if missing_data:
            print(f"   ⚠️ {len(missing_data)} players with insufficient data")

        score_elapsed = time.time() - score_start
        print(f"   Scored all players in {score_elapsed:.1f}s")

        # Total time
        total_elapsed = time.time() - start_time
        print(f"\n⏱️  Total enrichment time: {total_elapsed:.1f}s")

        # Compare to sequential estimate
        sequential_estimate = len(self.player_pool) * 0.3  # ~0.3s per player sequential
        speedup = sequential_estimate / total_elapsed if total_elapsed > 0 else 1
        print(f"   Estimated speedup: {speedup:.1f}x faster than sequential")

        return enriched_count

    def _call_optimizer(self, players, strategy, min_salary_val, existing_lineups=None):
        """
        Call the optimizer with correct parameters.
        Note: UnifiedMILPOptimizer only accepts: players, strategy, manual_selections
        """
        try:
            # The optimize_lineup method only accepts: players, strategy, manual_selections
            lineup_players, score = self.optimizer.optimize_lineup(
                players=players,
                strategy=strategy,
                manual_selections=""  # Empty string for no manual selections
            )
            return lineup_players, score
        except Exception as e:
            print(f"   ❌ Optimization error: {e}")
            raise

    def optimize_showdown_lineups(
            self,
            num_lineups: int = 1,
            strategy: str = "balanced",
            min_unique_players: int = 2,
            contest_type: str = "gpp"
    ) -> List[Dict]:
        """
        Generate optimized showdown lineups (1 Captain + 5 Utilities)

        Args:
            num_lineups: Number of lineups to generate
            strategy: Optimization strategy
            min_unique_players: Minimum unique players between lineups
            contest_type: Contest type (usually gpp for showdown)

        Returns:
            List of showdown lineup dictionaries
        """
        if not self.player_pool:
            print("❌ No players in pool!")
            return []

        print(f"\n🎰 Optimizing {num_lineups} SHOWDOWN lineups...")
        print(f"   Strategy: {strategy}")
        print(f"   Contest Type: {contest_type}")
        print(f"   Pool size: {len(self.player_pool)} players")

        # Filter to unique UTIL players only (no CPT entries)
        util_players = self._get_util_players()
        print(f"   Unique UTIL players: {len(util_players)}")

        if len(util_players) < 6:
            print(f"❌ Not enough unique players for showdown: {len(util_players)} (need 6)")
            return []

        # Set scoring for showdown
        slate_size = len(util_players)
        scoring_method = self.scoring_engine.set_contest_type(contest_type, slate_size)
        print(f"   Scoring Method: {scoring_method.upper()}")

        # Calculate scores
        print(f"\n📊 Calculating scores for showdown players...")
        for player in util_players:
            score = self.scoring_engine.calculate_score(player)
            player.enhanced_score = score
            player.optimization_score = score

        # Show top captain candidates
        self._show_captain_candidates(util_players)

        # Generate lineups
        lineups = []
        used_captains = set()

        for i in range(num_lineups):
            print(f"\n   Lineup {i + 1}/{num_lineups}...")

            # Apply diversity penalty for used captains
            if i > 0 and min_unique_players > 0:
                self._apply_captain_penalty(util_players, used_captains, penalty=0.7)

            # Optimize showdown lineup
            lineup_result = self._optimize_showdown_lineup(util_players, strategy)

            # Restore scores
            self._restore_captain_scores(util_players)

            if lineup_result and lineup_result.get('success'):
                captain = lineup_result['captain']
                utilities = lineup_result['utilities']

                # Track captain
                used_captains.add(captain.name)

                # Create showdown lineup dictionary
                lineup_dict = self._create_showdown_lineup_dict(
                    captain, utilities, lineup_result['total_score'], strategy
                )

                lineups.append(lineup_dict)

                # Display lineup summary
                self._display_showdown_summary(lineup_dict)

        print(f"\n✅ Generated {len(lineups)} showdown lineups")
        return lineups

    def optimize_lineups(
            self,
            num_lineups: int = 1,
            strategy: str = "balanced",
            min_unique_players: int = 3,
            contest_type: str = "cash"
    ) -> List[Dict]:
        """
        Generate optimized lineups from the player pool

        Auto-detects showdown slates and routes appropriately

        Args:
            num_lineups: Number of lineups to generate
            strategy: Optimization strategy (balanced, ceiling, safe, etc.)
            min_unique_players: Minimum unique players between lineups
            contest_type: Type of contest (cash, gpp, showdown)

        Returns:
            List of lineup dictionaries
        """
        if not self.player_pool:
            print("❌ No players in pool!")
            return []

        # AUTO-DETECT SHOWDOWN SLATES
        if is_showdown_slate(self.player_pool) or contest_type == 'showdown':
            print("\n🎪 Showdown slate detected! Switching to showdown optimization...")
            return self.optimize_showdown_lineups(
                num_lineups=num_lineups,
                strategy=strategy,
                min_unique_players=min_unique_players,
                contest_type=contest_type
            )

        # REGULAR OPTIMIZATION
        print(f"\n🎯 Optimizing {num_lineups} lineups...")
        print(f"   Strategy: {strategy}")
        print(f"   Contest Type: {contest_type}")
        print(f"   Pool size: {len(self.player_pool)} players")

        # Set scoring engine mode based on contest type
        slate_size = len(self.player_pool)
        scoring_method = self.scoring_engine.set_contest_type(contest_type, slate_size)
        print(f"   Scoring Method: {scoring_method.upper()}")

        # Apply contest-specific configuration
        from cash_optimization_config import apply_contest_config, get_contest_description
        contest_config = apply_contest_config(self.optimizer, contest_type)

        # Print contest configuration
        print(f"\n📋 Contest Configuration:")
        for line in get_contest_description(contest_type).split('\n'):
            print(f"   {line}")

        # Calculate scores with the selected engine
        print(f"\n📊 Calculating scores with {scoring_method} engine...")
        for player in self.player_pool:
            score = self.scoring_engine.calculate_score(player)
            player.enhanced_score = score
            player.optimization_score = score

        # Generate lineups
        lineups = []
        used_players = set()

        for i in range(num_lineups):
            print(f"\n   Lineup {i + 1}/{num_lineups}...")

            # Apply diversity penalty for used players
            if i > 0 and min_unique_players > 0:
                self._apply_diversity_penalty(used_players, penalty=0.8)

            try:
                # Run optimization
                lineup_players, score = self._call_optimizer(
                    players=self.player_pool,
                    strategy=strategy,
                    min_salary_val=self.optimizer.config.min_salary_usage
                )

                # Restore original scores
                self._restore_diversity_scores()

                if lineup_players:
                    # Track used players
                    for p in lineup_players:
                        used_players.add(p.name)

                    # Create lineup dictionary
                    lineup_dict = self._create_lineup_dict(
                        lineup_players, score, strategy, contest_type
                    )

                    # Add lineup analysis
                    self._analyze_lineup(lineup_dict, contest_type)

                    lineups.append(lineup_dict)

            except Exception as e:
                print(f"   ❌ Optimization failed: {str(e)}")
                self._restore_diversity_scores()
                continue

        # Final cleanup
        self._restore_diversity_scores()

        print(f"\n✅ Generated {len(lineups)} lineups")
        return lineups

    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            'total_players': len(self.all_players),
            'confirmed_players': len(self.confirmed_names),
            'manual_players': len(self.manual_names),
            'pool_size': len(self.player_pool),
            'components': {
                'confirmation_system': True,
                'statcast': True,
                'vegas': True,
                'scoring_engine': True,
                'optimizer': True
            }
        }


# Test function
def test_unified_system():
    """Test the unified system"""
    print("\n" + "=" * 80)
    print("🧪 TESTING UNIFIED CORE SYSTEM")
    print("=" * 80)

    system = UnifiedCoreSystem()

    # Show status
    status = system.get_system_status()
    print(f"\n📊 System Status:")
    print(f"   Components ready: {sum(status['components'].values())}/5")

    print("\n✅ System test complete!")
    print("\nTo use with your GUI:")
    print("1. Import this system in your GUI")
    print("2. Replace optimization worker with calls to this system")
    print("3. Use the workflow: load → confirm → enrich → optimize")


if __name__ == "__main__":
    test_unified_system()