#!/usr/bin/env python3
"""
FIXED DATA PIPELINE V2
======================
Properly handles confirmed player filtering and pool building
"""

import csv
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from copy import deepcopy
from strategies_v2 import StrategyManager
from optimizer_v2 import DFSOptimizer
from lineup_diversity_engine import LineupDiversityEngine, DiversityConfig

logger = logging.getLogger(__name__)


@dataclass
class Player:
    """Enhanced Player data structure with all modern DFS metrics"""
    # Core attributes
    name: str
    position: str
    team: str
    salary: int
    projection: float
    optimization_score: float = 0

    # Status flags
    confirmed: bool = False
    batting_order: int = 0
    opponent: str = ""
    game_info: str = ""
    player_id: str = ""

    # Ownership and leverage
    ownership: float = 15.0
    ownership_projection: float = 15.0  # Alias for scoring engine

    # Statcast metrics (batters)
    barrel_rate: float = 8.5
    xwoba: float = 0.320
    hard_hit_rate: float = 40.0
    avg_exit_velo: float = 88.0

    # Pitcher metrics
    k_rate: float = 8.0  # K/9 rate
    era: float = 4.00
    whip: float = 1.30

    # Team and game context
    implied_team_score: float = 4.5
    game_total: float = 8.5
    park_factor: float = 1.0
    weather_score: float = 1.0

    # Performance metrics
    recent_form: float = 1.0
    consistency_score: float = 50.0
    ceiling_projection: float = 0.0
    floor_projection: float = 0.0

    def __post_init__(self):
        """Calculate derived metrics after initialization"""
        # Set ownership_projection alias
        self.ownership_projection = self.ownership

        # Calculate ceiling/floor if not set
        if self.ceiling_projection == 0.0:
            self.ceiling_projection = self.projection * 1.6
        if self.floor_projection == 0.0:
            self.floor_projection = max(0, self.projection * 0.6)

        # Ensure optimization_score is set
        if self.optimization_score == 0:
            self.optimization_score = self.projection


class DFSPipeline:
    """Fixed data pipeline with proper confirmation handling"""

    def __init__(self):
        self.all_players: List[Player] = []
        self.player_pool: List[Player] = []
        self.num_games: int = 0
        self.strategy_manager = StrategyManager()
        self.optimizer = DFSOptimizer()
        self.diversity_engine = LineupDiversityEngine()

    def load_csv(self, csv_path: str) -> tuple:
        """Load DraftKings CSV"""
        try:
            self.all_players = []
            games_seen = set()

            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    player = self._create_player_from_csv(row)
                    if player:
                        self.all_players.append(player)
                        if player.game_info:
                            games_seen.add(player.game_info)

            self.num_games = len(games_seen)
            logger.info(f"Loaded {len(self.all_players)} players from {self.num_games} games")
            return len(self.all_players), self.num_games

        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return 0, 0

    def _create_player_from_csv(self, row: dict) -> Optional[Player]:
        """Create a Player object from CSV row"""
        try:
            name = row.get('Name', '').strip()
            position = row.get('Position', '').strip()
            team = row.get('TeamAbbrev', '').strip()
            salary = int(row.get('Salary', '0').replace('$', '').replace(',', ''))
            proj = float(row.get('AvgPointsPerGame', '0') or 10.0)

            player = Player(
                name=name,
                position=position,
                team=team,
                salary=salary,
                projection=proj,
                optimization_score=proj,  # Initialize with projection
                opponent=row.get('Opponent', ''),
                game_info=row.get('Game Info', ''),
                player_id=row.get('ID', '') or row.get('PlayerID', '') or str(hash(name))
            )

            return player

        except Exception as e:
            logger.debug(f"Error creating player: {e}")
            return None

    def fetch_confirmations(self) -> tuple:
        """
        FIXED: Properly mark confirmed players based on MLB data
        Returns: (total_confirmed, pitcher_count, position_player_count)
        """
        logger.info("Fetching MLB confirmations...")

        try:
            from smart_confirmation import UniversalSmartConfirmation

            # Create confirmation system with current players
            confirmations = UniversalSmartConfirmation(
                csv_players=deepcopy(self.all_players),
                verbose=True
            )

            # Get confirmations from MLB
            lineup_count, pitcher_count = confirmations.get_all_confirmations()

            # FIXED: Properly mark players as confirmed
            confirmed_pitchers = 0
            confirmed_position_players = 0

            for player in self.all_players:
                # Reset confirmation status
                player.confirmed = False

                # Check pitchers
                if player.position in ['P', 'SP', 'RP']:
                    if confirmations.is_pitcher_confirmed(player.name, player.team):
                        player.confirmed = True
                        confirmed_pitchers += 1
                        logger.debug(f"✅ Confirmed pitcher: {player.name} ({player.team})")
                else:
                    # Check position players
                    is_confirmed, batting_order = confirmations.is_player_confirmed(
                        player.name, player.team
                    )
                    if is_confirmed:
                        player.confirmed = True
                        player.batting_order = batting_order or 0
                        confirmed_position_players += 1
                        logger.debug(f"✅ Confirmed player: {player.name} ({player.team}) #{batting_order}")

            total_confirmed = confirmed_pitchers + confirmed_position_players
            logger.info(f"Marked {total_confirmed}/{len(self.all_players)} players as confirmed")
            logger.info(f"  Pitchers: {confirmed_pitchers}, Position players: {confirmed_position_players}")
            return (total_confirmed, confirmed_pitchers, confirmed_position_players)

        except ImportError as e:
            logger.warning(f"Smart confirmation not available: {e}")
            # Fallback: mark some players as confirmed for testing
            for i, player in enumerate(self.all_players):
                player.confirmed = (i % 3 != 2)  # Mark 2/3 as confirmed
            total = sum(1 for p in self.all_players if p.confirmed)
            return (total, total // 2, total // 2)  # Rough split

        except Exception as e:
            logger.error(f"Error during confirmation: {e}")
            return (0, 0, 0)

    def build_player_pool(self, confirmed_only: bool = False,
                          manual_selections: List[str] = None) -> int:
        """Build the player pool for optimization"""
        self.player_pool = []

        for player in self.all_players:
            include = False

            # Check manual selections first (always include)
            if manual_selections and player.name in manual_selections:
                include = True
                logger.debug(f"Including manual selection: {player.name}")
            # Then check confirmed status
            elif not confirmed_only:
                include = True  # Include all if not filtering
            elif player.confirmed:
                include = True  # Include only confirmed

            if include:
                self.player_pool.append(player)

        logger.info(f"Built pool: {len(self.player_pool)} players (confirmed_only={confirmed_only})")

        # Debug position counts
        self._debug_pool_positions()

        return len(self.player_pool)

    def _debug_pool_positions(self):
        """Debug helper to show position distribution"""
        from collections import defaultdict

        pos_counts = defaultdict(int)
        conf_counts = defaultdict(int)

        for player in self.player_pool:
            # Normalize pitcher positions
            if player.position in ['P', 'SP', 'RP']:
                pos_counts['P'] += 1
                if player.confirmed:
                    conf_counts['P'] += 1
            else:
                # Handle multi-position
                positions = player.position.split('/')
                for pos in positions:
                    if pos in ['C', '1B', '2B', '3B', 'SS', 'OF']:
                        pos_counts[pos] += 1
                        if player.confirmed:
                            conf_counts[pos] += 1

        logger.debug("Pool position distribution:")
        for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
            total = pos_counts.get(pos, 0)
            confirmed = conf_counts.get(pos, 0)
            need = 2 if pos == 'P' else 3 if pos == 'OF' else 1
            status = "✓" if total >= need else "✗"
            logger.debug(f"  {pos}: {total} total ({confirmed} confirmed) - need {need} {status}")

    def apply_strategy(self, contest_type: str = 'gpp') -> str:
        """Apply strategy-based scoring adjustments"""
        # Get strategy
        strategy_name, reason = self.strategy_manager.auto_select_strategy(
            contest_type, self.num_games
        )

        # Apply to pool
        self.player_pool = self.strategy_manager.apply_strategy(
            self.player_pool, strategy_name
        )

        logger.info(f"Applied strategy: {strategy_name}")
        return strategy_name

    def enrich_players(self, strategy: str, contest_type: str, skip_statcast: bool = False) -> Dict:
        """Enrich players with additional data"""
        stats = {
            'vegas': 0,
            'batting_order': 0,
            'statcast': 0,
            'weather': 0,
            'ownership': 0
        }

        # Try Vegas lines
        try:
            from vegas_lines import VegasLines
            vegas = VegasLines()
            vegas_data = vegas.get_all_lines()

            for player in self.player_pool:
                if player.team in vegas_data:
                    team_data = vegas_data[player.team]
                    team_total = team_data.get('total', 4.5)
                    game_total = team_data.get('game_total', 8.5)

                    # Set team context
                    player.implied_team_score = team_total
                    player.game_total = game_total

                    # Apply scoring boost (moved to scoring engine)
                    stats['vegas'] += 1
                    logger.debug(f"✅ Vegas data for {player.name}: Team {team_total}, Game {game_total}")
        except Exception as e:
            logger.debug(f"Vegas enrichment failed: {e}")

        # Try real Statcast data for confirmed players (unless skipped)
        if not skip_statcast:
            try:
                from simple_statcast_fetcher import SimpleStatcastFetcher
                statcast = SimpleStatcastFetcher()

                if statcast.enabled:
                    confirmed_players = [p for p in self.player_pool if getattr(p, 'confirmed', False)]
                    logger.info(f"Enriching with real Statcast data for {len(confirmed_players)} confirmed players...")

                    statcast_fetched = 0
                    for i, player in enumerate(self.player_pool):
                        if player.position not in ['P', 'SP', 'RP']:
                            # BATTER ENRICHMENT
                            # Only fetch for confirmed players to save API calls
                            if getattr(player, 'confirmed', False):
                                try:
                                    real_stats = statcast.get_batter_stats(player.name)
                                    if real_stats:
                                        # Set all Statcast metrics
                                        player.barrel_rate = real_stats.get('barrel%', 8.5)
                                        player.xwoba = real_stats.get('xwoba', 0.320)
                                        player.hard_hit_rate = real_stats.get('hard_hit%', 40.0)
                                        player.avg_exit_velo = real_stats.get('avg_exit_velo', 88.0)

                                        # Calculate recent form from xwOBA
                                        if player.xwoba > 0.350:
                                            player.recent_form = 1.15
                                        elif player.xwoba > 0.320:
                                            player.recent_form = 1.05
                                        else:
                                            player.recent_form = 0.95

                                        stats['statcast'] += 1
                                        statcast_fetched += 1
                                        logger.info(f"✅ Statcast {statcast_fetched}/{len(confirmed_players)}: {player.name} - {player.barrel_rate:.1f}% barrel")
                                        logger.debug(f"✅ Real Statcast for {player.name}: {player.barrel_rate:.1f}% barrel, {player.xwoba:.3f} xwOBA")
                                    else:
                                        self._set_default_batter_stats(player)
                                except Exception as e:
                                    logger.debug(f"Statcast failed for {player.name}: {e}")
                                    self._set_default_batter_stats(player)
                            else:
                                # Use defaults for unconfirmed players
                                self._set_default_batter_stats(player)
                        else:
                            # PITCHER ENRICHMENT
                            if getattr(player, 'confirmed', False):
                                # Try real pitcher Statcast data for confirmed pitchers
                                try:
                                    real_pitcher_stats = statcast.get_pitcher_stats(player.name)
                                    if real_pitcher_stats and real_pitcher_stats.get('has_recent_data', False):
                                        # Use real data if available (with validation)
                                        k_rate = real_pitcher_stats.get('k_rate', 8.0)
                                        era = real_pitcher_stats.get('era', 4.00)
                                        whip = real_pitcher_stats.get('whip', 1.30)

                                        # Validate K-rate (reject if too low)
                                        if k_rate >= 6.0:  # Minimum reasonable K-rate
                                            player.k_rate = k_rate
                                        else:
                                            # Use salary-based default for bad data
                                            self._set_default_pitcher_stats(player)

                                        player.era = era
                                        player.whip = whip
                                        player.recent_form = real_pitcher_stats.get('quality_score', 1.0)
                                        stats['statcast'] += 1
                                        statcast_fetched += 1
                                        logger.info(f"✅ Pitcher Statcast {statcast_fetched}: {player.name} - K/9 {player.k_rate:.1f}")
                                        logger.debug(f"✅ Real pitcher Statcast for {player.name}: K/9 {player.k_rate:.1f}, ERA {player.era:.2f}")
                                    else:
                                        # Fall back to salary-based defaults
                                        self._set_default_pitcher_stats(player)
                                except Exception as e:
                                    logger.debug(f"Pitcher Statcast failed for {player.name}: {e}")
                                    self._set_default_pitcher_stats(player)
                            else:
                                # Use defaults for unconfirmed pitchers
                                self._set_default_pitcher_stats(player)
                else:
                    # Fallback to defaults
                    for player in self.player_pool:
                        if player.position not in ['P', 'SP', 'RP']:
                            self._set_default_batter_stats(player)
                        else:
                            self._set_default_pitcher_stats(player)
                        stats['statcast'] += 1

            except Exception as e:
                logger.debug(f"Statcast enrichment failed: {e}")
                # Fallback to defaults
                for player in self.player_pool:
                    if player.position not in ['P', 'SP', 'RP']:
                        self._set_default_batter_stats(player)
                    else:
                        self._set_default_pitcher_stats(player)
                    stats['statcast'] += 1
        else:
            # Fast mode - use defaults immediately
            logger.info("Fast mode: Using default stats (skipping Statcast)")
            for player in self.player_pool:
                if player.position not in ['P', 'SP', 'RP']:
                    self._set_default_batter_stats(player)
                else:
                    self._set_default_pitcher_stats(player)
                stats['statcast'] += 1

        # Try weather data
        try:
            from weather_integration import WeatherIntegration
            weather = WeatherIntegration()
            weather_data = weather.get_all_weather()

            for player in self.player_pool:
                # Simple weather scoring (wind/temp effects)
                weather_score = 1.0
                if weather_data:
                    # Positive weather = higher scoring
                    weather_score = 1.05 if len(weather_data) > 0 else 1.0

                player.weather_score = weather_score
                stats['weather'] += 1

        except Exception as e:
            logger.debug(f"Weather enrichment failed: {e}")

        # Try ownership projections
        try:
            from ownership_calculator import OwnershipCalculator
            ownership_calc = OwnershipCalculator()

            for player in self.player_pool:
                ownership = ownership_calc.get_ownership(player)
                player.ownership = ownership
                player.ownership_projection = ownership  # Alias for scoring engine
                stats['ownership'] += 1

        except Exception as e:
            logger.debug(f"Ownership enrichment failed: {e}")

        return stats

    def _set_default_batter_stats(self, player):
        """Set default stats for batters"""
        # Salary-based defaults (higher salary = better stats)
        if player.salary >= 5500:
            player.barrel_rate = 10.0
            player.xwoba = 0.340
            player.hard_hit_rate = 45.0
            player.recent_form = 1.05
        elif player.salary >= 4500:
            player.barrel_rate = 8.5
            player.xwoba = 0.320
            player.hard_hit_rate = 40.0
            player.recent_form = 1.0
        else:
            player.barrel_rate = 6.5
            player.xwoba = 0.300
            player.hard_hit_rate = 35.0
            player.recent_form = 0.95

    def _set_default_pitcher_stats(self, player):
        """Set default stats for pitchers"""
        # Salary-based defaults
        if player.salary >= 8000:
            player.k_rate = 10.0
            player.era = 3.20
            player.whip = 1.10
        elif player.salary >= 6000:
            player.k_rate = 8.5
            player.era = 3.80
            player.whip = 1.25
        else:
            player.k_rate = 7.0
            player.era = 4.50
            player.whip = 1.40

    def score_players(self, contest_type: str = 'gpp') -> Dict:
        """Score players using the unified scoring engine"""
        if not self.player_pool:
            logger.warning("No player pool to score")
            return {}

        try:
            from scoring_v2 import ScoringEngine
            scoring_engine = ScoringEngine()

            # Score all players
            scoring_engine.score_all_players(self.player_pool, contest_type)

            logger.info(f"Scored {len(self.player_pool)} players for {contest_type}")

            # Return scoring stats
            scores = [p.optimization_score for p in self.player_pool]
            return {
                'players_scored': len(self.player_pool),
                'avg_score': sum(scores) / len(scores) if scores else 0,
                'max_score': max(scores) if scores else 0,
                'min_score': min(scores) if scores else 0
            }

        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            return {}

    def optimize_lineups(self, contest_type: str = 'gpp',
                         num_lineups: int = 1, use_diversity: bool = None) -> List[Dict]:
        """Generate optimized lineups with optional diversity"""
        logger.info(f"Optimizing {num_lineups} {contest_type} lineups...")
        logger.info(f"Pool has {len(self.player_pool)} players")

        # Auto-enable diversity for multiple lineups in tournaments
        if use_diversity is None:
            use_diversity = (num_lineups > 1 and contest_type == 'gpp')

        if use_diversity and num_lineups > 1:
            # Use diversity engine for multiple tournament lineups
            logger.info(f"Using diversity engine for {num_lineups} lineups")
            lineups = self.diversity_engine.generate_diverse_lineups(
                self.optimizer, self.player_pool, contest_type, num_lineups
            )
        else:
            # Use standard optimizer
            lineups = self.optimizer.optimize(
                self.player_pool,
                contest_type,
                num_lineups
            )

        logger.info(f"Generated {len(lineups)} lineups")
        return lineups

    def export_lineups(self, lineups: List[Dict], output_path: str) -> bool:
        """Export lineups to CSV"""
        try:
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)

                for lineup in lineups:
                    row = []
                    # DraftKings order: P, P, C, 1B, 2B, 3B, SS, OF, OF, OF
                    position_order = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
                    position_filled = {pos: 0 for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']}

                    for target_pos in position_order:
                        found = False
                        for player in lineup['players']:
                            player_pos = player.position
                            # Normalize pitcher position
                            if player_pos in ['SP', 'RP']:
                                player_pos = 'P'

                            # Check if this player fits this slot
                            if player_pos == target_pos:
                                current_count = position_filled[target_pos]
                                max_count = 2 if target_pos == 'P' else 3 if target_pos == 'OF' else 1

                                if current_count < max_count and player.name not in row:
                                    row.append(player.name)
                                    position_filled[target_pos] += 1
                                    found = True
                                    break

                        if not found:
                            row.append("")  # Empty slot

                    writer.writerow(row)

            logger.info(f"Exported {len(lineups)} lineups to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Export error: {e}")
            return False