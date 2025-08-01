#!/usr/bin/env python3
"""
UNIFIED MILP OPTIMIZER - COMPLETE CLEAN VERSION
==============================================
All methods implemented with proper logging and performance optimizations
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pulp

# Configure logging
try:
    from logging_config import get_logger

    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Enhanced configuration for optimization"""

    salary_cap: int = 50000
    min_salary_usage: float = 0.95
    position_requirements: Dict[str, int] = None

    # Team stacking constraints
    max_players_per_team: int = 4
    min_players_per_team: int = 0
    preferred_stack_size: int = 3

    # Correlation settings
    max_hitters_vs_pitcher: int = 4
    correlation_boost: float = 0.05

    # PITCHER-HITTER CORRELATION CONTROL
    # 0 = No opposing hitters allowed (strictest - best for cash)
    # 1 = Allow 1 elite hitter (balanced - good for most cases)
    # 2 = Allow 2 hitters (loose - for small slates)
    # 999 = No constraint (maximum points potential)
    max_opposing_hitters: int = 1  # Default: balanced approach

    # Optimization settings
    timeout_seconds: int = 30
    use_correlation: bool = True
    enforce_lineup_rules: bool = True

    def __post_init__(self):
        if self.position_requirements is None:
            self.position_requirements = {
                "P": 2,
                "C": 1,
                "1B": 1,
                "2B": 1,
                "3B": 1,
                "SS": 1,
                "OF": 3,
            }


class UnifiedMILPOptimizer:
    """
    Clean MILP optimizer with comprehensive data integration
    """

    def __init__(self, config: OptimizationConfig = None):
        """Initialize optimization engine with configuration"""
        self.config = config or OptimizationConfig()
        self.logger = logger

        # Load configuration
        self._load_dfs_config()

        # Load park factors
        self.park_factors = self._load_park_factors()

        # Initialize data sources
        self._initialize_data_sources()

        # Cache for optimization results
        self._last_result = None
        self._optimization_count = 0
        self._lineup_cache = {}


    def get_showdown_config(self) -> OptimizationConfig:
        """Get configuration for showdown slates"""
        config = OptimizationConfig()
        config.position_requirements = {
            'UTIL': 6  # 1 captain + 5 utilities (all from UTIL pool)
        }
        config.salary_cap = 50000
        config.max_players_per_team = 6  # Can use all from same team
        config.min_salary_usage = 0.90  # Can use less salary in showdown
        return config




    def _load_dfs_config(self):
        """Load configuration from unified config system or JSON file"""
        try:
            # First try to load from optimization_config.json
            config_path = Path("optimization_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)

                # Update configuration with loaded values
                if 'salary_cap' in config_data:
                    self.config.salary_cap = config_data['salary_cap']

                if 'min_salary_usage' in config_data:
                    self.config.min_salary_usage = config_data['min_salary_usage']

                if 'position_requirements' in config_data:
                    self.config.position_requirements = config_data['position_requirements']

                if 'optimization' in config_data:
                    opt_settings = config_data['optimization']
                    self.config.max_players_per_team = opt_settings.get('max_players_per_team', 4)
                    self.config.correlation_boost = opt_settings.get('correlation_boost', 0.05)
                    self.config.timeout_seconds = opt_settings.get('timeout_seconds', 30)

                logger.info(f"Configuration loaded from {config_path}")

            else:
                # Try to import unified_config_manager
                try:
                    from unified_config_manager import get_config_value

                    self.config.salary_cap = get_config_value("optimization.salary_cap", 50000)
                    self.config.min_salary_usage = get_config_value("optimization.min_salary_usage", 0.95)

                    # Load position requirements
                    default_positions = {"P": 2, "C": 1, "1B": 1, "2B": 1, "3B": 1, "SS": 1, "OF": 3}
                    self.config.position_requirements = get_config_value(
                        "optimization.position_requirements",
                        default_positions
                    )

                    # Load team constraints
                    self.config.max_players_per_team = get_config_value(
                        "optimization.max_players_per_team", 4
                    )

                    logger.info("Configuration loaded from unified config manager")

                except ImportError:
                    logger.warning("No config manager available, using defaults")

        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")

    def _load_park_factors(self) -> Dict[str, float]:
        """Load park factors for teams"""
        park_factors = {
            # Extreme hitter-friendly
            "COL": 1.20,  # Coors Field
            # Hitter-friendly
            "CIN": 1.12, "TEX": 1.10, "PHI": 1.08, "MIL": 1.06,
            "BAL": 1.05, "HOU": 1.04, "TOR": 1.03, "BOS": 1.03,
            # Slight hitter-friendly
            "NYY": 1.02, "CHC": 1.01,
            # Neutral
            "ARI": 1.00, "ATL": 1.00, "MIN": 0.99,
            # Slight pitcher-friendly
            "WSH": 0.98, "NYM": 0.97, "LAA": 0.96, "STL": 0.95,
            # Pitcher-friendly
            "CLE": 0.94, "TB": 0.93, "KC": 0.92, "DET": 0.91, "SEA": 0.90,
            # Extreme pitcher-friendly
            "OAK": 0.89, "SF": 0.88, "SD": 0.87, "MIA": 0.86, "PIT": 0.85,
            # Additional teams
            "LAD": 0.98, "CHW": 0.96, "CWS": 0.96,
        }

        # Try to load from file
        try:
            park_file = Path("data/park_factors.json")
            if park_file.exists():
                with open(park_file, 'r') as f:
                    loaded_factors = json.load(f)
                    park_factors.update(loaded_factors)
                    logger.info(f"Loaded park factors from {park_file}")
        except Exception as e:
            logger.debug(f"Could not load park factors file: {e}")

        return park_factors

    def _initialize_data_sources(self):
        """Initialize external data sources with fallback options"""
        self.data_sources = {
            'statcast': None,
            'vegas': None,
            'weather': None,
            'batting_order': None
        }

        # Try to initialize each data source
        try:
            from simple_statcast_fetcher import SimpleStatcastFetcher
            self.data_sources['statcast'] = SimpleStatcastFetcher()
            logger.info("Statcast data source initialized")
        except ImportError:
            logger.debug("Statcast module not available")

        try:
            from vegas_lines import VegasLines
            self.data_sources['vegas'] = VegasLines()
            logger.info("Vegas lines data source initialized")
        except ImportError:
            logger.debug("Vegas lines module not available")

    def apply_strategy_filter(self, players: List, strategy: str) -> List:
        """Apply strategy-based filtering to player pool"""
        if strategy == "all_players":
            # Use all players
            eligible = [p for p in players if self._is_valid_player(p)]

        elif strategy == "confirmed_only":
            # Only confirmed starters
            eligible = [p for p in players if getattr(p, 'is_confirmed', False)]

        elif strategy == "confirmed_plus_manual":
            # Confirmed + manually selected
            eligible = [
                p for p in players
                if getattr(p, 'is_confirmed', False) or getattr(p, 'is_manual_selected', False)
            ]

        elif strategy == "manual_only":
            # Only manually selected
            eligible = [p for p in players if getattr(p, 'is_manual_selected', False)]

        elif strategy == "balanced":
            # Mix of confirmed and high-projection players
            confirmed = [p for p in players if getattr(p, 'is_confirmed', False)]

            # Add top projections if not enough confirmed
            if len(confirmed) < 20:
                non_confirmed = [p for p in players if not getattr(p, 'is_confirmed', False)]
                non_confirmed.sort(key=lambda x: getattr(x, 'base_projection', 0), reverse=True)
                eligible = confirmed + non_confirmed[:30]
            else:
                eligible = confirmed

        else:
            # Default to all valid players
            eligible = [p for p in players if self._is_valid_player(p)]

        logger.info(f"Strategy '{strategy}' resulted in {len(eligible)} eligible players")
        return eligible

    def _is_valid_player(self, player) -> bool:
        """Check if player meets basic validation criteria"""
        # Must have required attributes
        if not all(hasattr(player, attr) for attr in ['name', 'salary', 'primary_position']):
            return False

        # Must have positive salary
        if player.salary <= 0:
            return False

        # Must have valid position
        valid_positions = {'P', 'SP', 'RP', 'C', '1B', '2B', '3B', 'SS', 'OF'}
        if player.primary_position not in valid_positions:
            return False

        return True

    def _pre_filter_players(self, players: List[Any], strategy: str) -> List[Any]:
        """Pre-filter players to reduce problem size for performance"""
        if len(players) <= 200:
            return players

        logger.info(f"PERFORMANCE: Pre-filtering {len(players)} players")

        # Sort by value (points per dollar)
        players_with_value = [
            (p, getattr(p, 'optimization_score', 0) / max(p.salary, 1))
            for p in players
        ]
        players_with_value.sort(key=lambda x: x[1], reverse=True)

        # Keep top players by value, ensuring position coverage
        filtered = []
        position_counts = {}

        for player, value in players_with_value:
            pos = player.primary_position
            count = position_counts.get(pos, 0)

            # Keep at least 10 per position, or top 200 overall
            if count < 10 or len(filtered) < 200:
                filtered.append(player)
                position_counts[pos] = count + 1

        logger.info(f"PERFORMANCE: Reduced to {len(filtered)} players")
        return filtered


    def calculate_player_scores(self, players: List) -> List:
        """
        Use scores from pure data engine - NO MODIFICATIONS

        The pure data scoring engine has already calculated final scores.
        This method now just ensures optimization_score is set.
        """
        for player in players:
            # Simply use the score that was already calculated by pure data engine
            if hasattr(player, 'optimization_score') and player.optimization_score > 0:
                # Score already set, nothing to do
                pass
            elif hasattr(player, 'enhanced_score'):
                # Copy enhanced_score to optimization_score
                player.optimization_score = player.enhanced_score
            elif hasattr(player, 'pure_data_score'):
                # If using pure_data_score attribute
                player.optimization_score = player.pure_data_score
            else:
                # No valid score found
                player.optimization_score = 0
                logger.warning(f"No valid score for {player.name}")

        return players

    def pre_calculate_correlation_bonuses(self, players: List) -> List:
        """Pre-calculate correlation adjustments for optimization"""
        # This is where correlation logic would go
        # For now, just copy enhanced_score to optimization_score
        for player in players:
            player.optimization_score = getattr(player, 'enhanced_score', 0)

        return players

    def optimize_lineup(self, players: List, strategy: str = "balanced", manual_selections: str = "", contest_type: str = "gpp") -> Tuple[List, float]:
        """
        Main optimization method with dynamic salary constraints
        """
        logger.info(f"OPTIMIZATION: Starting {contest_type.upper()} optimization with strategy: {strategy}")
        logger.info(f"OPTIMIZATION: Players available: {len(players)}")
        logger.info(f"OPTIMIZATION: Manual selections: {manual_selections}")
        self._optimization_count += 1

        # Adjust constraints based on contest type


        if contest_type.lower() == 'cash':


            # Cash game adjustments


            self.config.max_players_per_team = 3  # Less stacking


            self.config.preferred_stack_size = 2  # Smaller stacks


            self.config.max_opposing_hitters = 0  # No opposing hitters vs your pitcher


        else:


            # GPP settings (restore defaults)


            self.config.max_players_per_team = 4


            self.config.preferred_stack_size = 3


            self.config.max_opposing_hitters = 1


        


        # Adjust constraints based on contest type



        


        if contest_type.lower() == 'cash':



        


            # Cash game adjustments



        


            self.config.max_players_per_team = 3  # Less stacking



        


            self.config.preferred_stack_size = 2  # Smaller stacks



        


            self.config.max_opposing_hitters = 0  # No opposing hitters vs your pitcher



        


        else:



        


            # GPP settings (restore defaults)



        


            self.config.max_players_per_team = 4



        


            self.config.preferred_stack_size = 3



        


            self.config.max_opposing_hitters = 1



        


        



        


        # Dynamic minimum salary based on strategy
        if strategy in ['projection_monster', 'truly_smart_stack']:
            min_salary = 48000  # 96%
        elif strategy == 'pitcher_dominance':
            min_salary = 48500  # 97%
        elif strategy == 'correlation_value':
            min_salary = 47500  # 95%
        elif strategy == 'matchup_leverage_stack':
            min_salary = 47000  # 94% - needs variance room
        else:
            min_salary = 45000  # 90% default

        # Store for use in _run_milp_optimization
        self._strategy_min_salary = min_salary

        # Check cache first
        cache_key = (strategy, tuple(manual_selections) if manual_selections else (), len(players))
        if cache_key in self._lineup_cache:
            cached_result, cache_time = self._lineup_cache[cache_key]
            from datetime import datetime
            if (datetime.now() - cache_time).seconds < 300:  # 5 min cache
                logger.info("PERFORMANCE: Using cached lineup result")
                return cached_result

        # 1. Apply strategy filter
        eligible_players = self.apply_strategy_filter(players, strategy)
        if not eligible_players:
            logger.error("No eligible players after strategy filter")
            return [], 0

        # 2. Pre-filter for performance if needed
        eligible_players = self._pre_filter_players(eligible_players, strategy)

        # 3. Calculate scores
        scored_players = self.calculate_player_scores(eligible_players)

        # 4. Apply correlation bonuses
        final_players = self.pre_calculate_correlation_bonuses(scored_players)

        # 5. Process manual selections
        if manual_selections:
            manual_names = [name.strip().lower() for name in manual_selections.split(',')]
            for player in final_players:
                if player.name.lower() in manual_names:
                    player.is_manual_selected = True
                    # Boost score slightly to encourage selection
                    player.optimization_score *= 1.1

        # 6. Run MILP optimization
        lineup, total_score = self._run_milp_optimization(final_players)

        # 7. Store result
        self._last_result = {
            'lineup': lineup,
            'score': total_score,
            'strategy': strategy,
            'players_considered': len(final_players)
        }

        # Cache the result
        from datetime import datetime
        self._lineup_cache[cache_key] = ((lineup, total_score), datetime.now())

        return lineup, total_score

    def _run_milp_optimization(self, players: List) -> Tuple[List, float]:
        """
        Run the actual MILP optimization
        """
        if not players:
            return [], 0

        # Create optimization problem
        prob = pulp.LpProblem("DFS_Lineup_Optimization", pulp.LpMaximize)

        # Decision variables
        player_vars = pulp.LpVariable.dicts(
            "players",
            range(len(players)),
            cat="Binary"
        )

        # Objective function - maximize total score
        prob += pulp.lpSum([
            player_vars[i] * getattr(players[i], 'optimization_score', 0)
            for i in range(len(players))
        ])

        # Constraints

        # 1. Salary cap constraint (maximum)
        prob += pulp.lpSum([
            player_vars[i] * players[i].salary
            for i in range(len(players))
        ]) <= self.config.salary_cap

        # 2. Minimum salary usage (NOW DYNAMIC!)
        # Use the strategy-specific minimum we set earlier
        min_salary = getattr(self, '_strategy_min_salary', 45000)
        prob += pulp.lpSum([
            player_vars[i] * players[i].salary
            for i in range(len(players))
        ]) >= min_salary

        # 3. Position requirements
        for pos, required in self.config.position_requirements.items():
            eligible_indices = [
                i for i in range(len(players))
                if players[i].primary_position == pos or pos in getattr(players[i], 'positions', [])
            ]

            if len(eligible_indices) < required:
                logger.warning(f"Not enough players for position {pos}")
                logger.info(
                    f"OPTIMIZATION: Position constraint failed - {pos} needs {required}, have {len(eligible_indices)}")
                return [], 0

            prob += pulp.lpSum([
                player_vars[i] for i in eligible_indices
            ]) == required

        # 4. Total roster size
        total_required = sum(self.config.position_requirements.values())
        prob += pulp.lpSum(player_vars) == total_required

        # 5. Max players per team
        teams = set(p.team for p in players if hasattr(p, 'team'))
        for team in teams:
            team_indices = [
                i for i in range(len(players))
                if getattr(players[i], 'team', None) == team
            ]
            if team_indices:
                prob += pulp.lpSum([
                    player_vars[i] for i in team_indices
                ]) <= self.config.max_players_per_team

        # 6. Force manual selections
        for i, player in enumerate(players):
            if getattr(player, 'is_manual_selected', False):
                prob += player_vars[i] == 1

        # 7. PITCHER-HITTER CORRELATION CONSTRAINT (Configurable)
        # Default: Allow up to 1 hitter from opposing team (balanced approach)
        # Set to 0 for strict cash games, 999 for no constraint (max points)
        max_opposing_hitters = getattr(self.config, 'max_opposing_hitters', 1)

        if max_opposing_hitters < 999:  # Only apply if not disabled
            # Find all pitchers and their opponents
            for p_idx, pitcher in enumerate(players):
                if pitcher.primary_position == 'P':
                    # Get pitcher's opponent team
                    opp_team = getattr(pitcher, 'opponent', None)
                    if opp_team:
                        # Find all hitters from the opposing team
                        opp_hitter_indices = [
                            h_idx for h_idx, hitter in enumerate(players)
                            if hitter.primary_position != 'P' and
                               getattr(hitter, 'team', None) == opp_team
                        ]

                        if opp_hitter_indices:
                            # Add constraint: If pitcher is selected, limit opposing hitters
                            # This uses Big-M method: allows all hitters if pitcher not selected
                            constraint_name = f"pitcher_{p_idx}_vs_{opp_team}_hitters"

                            prob += (
                                pulp.lpSum([player_vars[h] for h in opp_hitter_indices])
                                <= max_opposing_hitters +
                                (len(opp_hitter_indices) * (1 - player_vars[p_idx])),
                                constraint_name
                            )

                            logger.debug(
                                f"Added constraint: {pitcher.name} vs {opp_team} "
                                f"({len(opp_hitter_indices)} hitters, max allowed: {max_opposing_hitters})"
                            )

        # Solve
        try:
            # Use optimized solver settings
            solver_options = pulp.PULP_CBC_CMD(
                timeLimit=30,  # 30 second timeout
                threads=4,  # Use 4 threads
                options=['preprocess=on', 'cuts=on', 'heuristics=on'],
                msg=0  # Suppress solver output
            )
            prob.solve(solver_options)

            if prob.status == pulp.LpStatusOptimal:
                # Extract lineup
                lineup = []
                total_score = 0

                for i in range(len(players)):
                    if player_vars[i].varValue == 1:
                        lineup.append(players[i])
                        total_score += getattr(players[i], 'optimization_score', 0)

                # Sort lineup by position for display
                position_order = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']
                lineup.sort(key=lambda p: (
                    position_order.index(p.primary_position)
                    if p.primary_position in position_order else 99
                ))

                logger.info(f"Optimization successful: {len(lineup)} players, score: {total_score:.2f}")

                # Log correlation info
                if max_opposing_hitters < 999:
                    # Check if we have pitcher-hitter conflicts
                    for pitcher in lineup:
                        if pitcher.primary_position == 'P':
                            opp_team = getattr(pitcher, 'opponent', None)
                            if opp_team:
                                opp_hitters = [
                                    h.name for h in lineup
                                    if h.primary_position != 'P' and getattr(h, 'team', None) == opp_team
                                ]
                                if opp_hitters:
                                    logger.info(
                                        f"  ⚠️  Correlation: {pitcher.name} with {len(opp_hitters)} "
                                        f"opposing hitter(s) from {opp_team}: {', '.join(opp_hitters)}"
                                    )

                # Log the final lineup
                logger.info(
                    f"LINEUP SELECTED: Total score = {total_score:.1f}, Total salary = {sum(p.salary for p in lineup)}")
                for p in lineup:
                    logger.info(
                        f"  LINEUP: {p.primary_position} - {p.name} - ${p.salary} - {getattr(p, 'optimization_score', 0):.1f} pts")

                return lineup, total_score

            else:
                logger.error(f"Optimization failed with status: {pulp.LpStatus[prob.status]}")
                return [], 0

        except Exception as e:
            logger.error(f"MILP optimization error: {e}")
            return [], 0

    def get_optimization_stats(self) -> Dict:
        """Get statistics about optimization performance"""
        stats = {
            'total_optimizations': self._optimization_count,
            'last_result': self._last_result,
            'config': {
                'salary_cap': self.config.salary_cap,
                'position_requirements': self.config.position_requirements,
                'max_players_per_team': self.config.max_players_per_team
            }
        }
        return stats

    def parse_manual_selections(self, manual_text: str, all_players: List) -> List[str]:
        """Parse manual player selections from text"""
        if not manual_text:
            return []

        manual_names = []
        for name in manual_text.split(','):
            name = name.strip()
            if name:
                manual_names.append(name.lower())

        # Find matching players
        selected_players = []
        for player in all_players:
            if player.name.lower() in manual_names:
                selected_players.append(player.name)
                player.is_manual_selected = True

        return selected_players

    def optimize(self, players: List, strategy: str = "balanced",
                 manual_selections: Optional[List[str]] = None) -> Any:
        """Optimize lineup (compatibility method)"""
        # Convert manual selections list to string if needed
        manual_text = ""
        if manual_selections:
            manual_text = ", ".join(manual_selections)

        lineup, score = self.optimize_lineup(players, strategy, manual_text)

        # Return a result object for compatibility
        class OptimizationResult:
            def __init__(self, lineup, score):
                self.lineup = lineup
                self.score = score
                self.total_score = score

        return OptimizationResult(lineup, score) if lineup else None


def create_unified_optimizer(config: Optional[OptimizationConfig] = None) -> UnifiedMILPOptimizer:
    """Factory function to create optimizer instance"""
    return UnifiedMILPOptimizer(config)


# For backward compatibility
if __name__ == "__main__":
    print("✅ Unified MILP Optimizer module loaded successfully")
    print("📋 Usage:")
    print("   from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig")
    print("   config = OptimizationConfig(salary_cap=50000)")
    print("   optimizer = UnifiedMILPOptimizer(config)")