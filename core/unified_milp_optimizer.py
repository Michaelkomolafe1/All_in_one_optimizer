#!/usr/bin/env python3
"""
UNIFIED MILP OPTIMIZER - STRATEGY-DRIVEN VERSION
===============================================
Automatically selects and uses the #1 strategy for each contest type
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set  # Add Set here

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
    min_salary_usage: float = 0.85  # CHANGED from 0.95
    position_requirements: Dict[str, int] = None

    # Team stacking constraints
    max_players_per_team: int = 5  # CHANGED from 4
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
    Strategy-driven MILP optimizer that automatically selects the best strategy
    """

    # Define the #1 strategies for each contest type and slate size
    BEST_STRATEGIES = {
        'cash': {
            'small': 'confirmed_only',  # Small slate (< 5 games)
            'medium': 'balanced',  # Medium slate (5-8 games)
            'large': 'confirmed_plus_value',  # Large slate (9+ games)
            'default': 'confirmed_only'  # Default cash strategy
        },
        'gpp': {
            'small': 'stack_leverage',  # Small slate GPP
            'medium': 'balanced_upside',  # Medium slate GPP
            'large': 'multi_stack',  # Large slate GPP
            'default': 'balanced_upside'  # Default GPP strategy
        }
    }

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

        # Initialize strategy selector if available
        self.strategy_selector = self._initialize_strategy_selector()

        # Cache for optimization results
        self._last_result = None
        self._optimization_count = 0
        self._lineup_cache = {}

    def _initialize_strategy_selector(self):
        """Initialize the strategy selector if available"""
        try:
            from strategy_auto_selector import StrategyAutoSelector
            return StrategyAutoSelector()
        except ImportError:
            logger.warning("Strategy selector not available, using default strategies")
            return None

    def _apply_diversity_penalty(self, used_players: Set[str], penalty: float = 0.8):
        """Apply penalty to previously used players"""
        for player in self.player_pool:
            if player.name in used_players:
                if not hasattr(player, 'original_optimization_score'):
                    player.original_optimization_score = player.optimization_score
                player.optimization_score *= penalty

    def _restore_original_scores(self):
        """Restore original optimization scores"""
        for player in self.player_pool:
            if hasattr(player, 'original_optimization_score'):
                player.optimization_score = player.original_optimization_score

    def _determine_slate_size(self, players: List) -> str:
        """Determine slate size based on number of games"""
        # Count unique games from player matchups
        games = set()
        for player in players:
            team = getattr(player, 'team', '')
            opp = getattr(player, 'opponent', '')
            if team and opp:
                # Create a normalized game key
                game = tuple(sorted([team, opp]))
                games.add(game)

        num_games = len(games)

        if num_games < 5:
            return 'small'
        elif num_games <= 8:
            return 'medium'
        else:
            return 'large'

    def _get_best_strategy(self, contest_type: str, players: List) -> str:
        """Get the #1 strategy for the given contest type and slate"""
        contest_type = contest_type.lower()

        # If we have a strategy selector, use it
        if self.strategy_selector:
            try:
                # Get slate info
                slate_size = self._determine_slate_size(players)
                num_games = len(set(tuple(sorted([getattr(p, 'team', ''), getattr(p, 'opponent', '')]))
                                    for p in players if getattr(p, 'team', '') and getattr(p, 'opponent', '')))

                # Use strategy selector to get the best strategy
                strategy_info = self.strategy_selector.select_strategy(
                    contest_type=contest_type,
                    slate_size=num_games,
                    confirmed_count=sum(1 for p in players if getattr(p, 'is_confirmed', False))
                )

                if strategy_info and 'strategy' in strategy_info:
                    logger.info(f"Strategy selector chose: {strategy_info['strategy']} "
                                f"(confidence: {strategy_info.get('confidence', 'N/A')})")
                    return strategy_info['strategy']

            except Exception as e:
                logger.warning(f"Strategy selector failed: {e}, using defaults")

        # Fall back to predefined best strategies
        slate_size = self._determine_slate_size(players)
        strategy_map = self.BEST_STRATEGIES.get(contest_type, self.BEST_STRATEGIES['gpp'])
        strategy = strategy_map.get(slate_size, strategy_map['default'])

        logger.info(f"Selected {contest_type.upper()} strategy for {slate_size} slate: {strategy}")
        return strategy

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

    def apply_strategy_filter(self, players: List[Any], strategy: str,
                              contest_type: str = 'gpp') -> List[Any]:
        """Apply strategy-specific filtering and scoring"""

        # Import strategy functions
        try:
            from dfs_optimizer.strategies.cash_strategies import (
                build_projection_monster,
                build_pitcher_dominance
            )
            from dfs_optimizer.strategies.gpp_strategies import (
                build_correlation_value,
                build_truly_smart_stack,
                build_matchup_leverage_stack
            )
        except ImportError:
            logger.error("Failed to import strategy functions")
            return players

        # Map strategy names to functions
        strategy_functions = {
            'projection_monster': build_projection_monster,
            'pitcher_dominance': build_pitcher_dominance,
            'correlation_value': build_correlation_value,
            'truly_smart_stack': build_truly_smart_stack,
            'matchup_leverage_stack': build_matchup_leverage_stack,
            'smart_stack': build_truly_smart_stack,  # Alias
        }

        # Filter to valid players
        eligible = [p for p in players if self._is_valid_player(p)]

        # Apply the strategy function if it exists
        if strategy in strategy_functions:
            logger.info(f"Applying strategy: {strategy}")
            # Strategy functions modify player.optimization_score
            eligible = strategy_functions[strategy](eligible)
            logger.info(f"Strategy {strategy} applied to {len(eligible)} players")
        else:
            logger.warning(f"Unknown strategy '{strategy}', using default scoring")
            # CRITICAL FIX: Copy the appropriate score to optimization_score
            for player in eligible:
                if contest_type == 'cash' and hasattr(player, 'cash_score'):
                    player.optimization_score = player.cash_score
                elif hasattr(player, 'gpp_score'):
                    player.optimization_score = player.gpp_score
                else:
                    player.optimization_score = getattr(player, 'enhanced_score', 0)

        # CRITICAL FIX: Ensure optimization_score is set for all players
        # Even after strategy application, some might be 0
        for player in eligible:
            if not hasattr(player, 'optimization_score') or player.optimization_score == 0:
                # Fall back to the appropriate score
                if contest_type == 'cash' and hasattr(player, 'cash_score'):
                    player.optimization_score = player.cash_score
                elif hasattr(player, 'gpp_score'):
                    player.optimization_score = player.gpp_score
                else:
                    player.optimization_score = player.base_projection

        # Debug: Log score status
        scores_set = sum(1 for p in eligible if getattr(p, 'optimization_score', 0) > 0)
        logger.info(f"Players with optimization_score > 0: {scores_set}/{len(eligible)}")

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
        """Ensure optimization_score is set, but don't overwrite if already set by strategy"""
        contest_type = getattr(self.config, 'contest_type', 'gpp')

        for player in players:
            # Check if optimization_score was already set by a strategy
            if hasattr(player, 'optimization_score') and player.optimization_score > 0:
                # Strategy already set the score, don't overwrite
                logger.debug(f"{player.name} already has optimization_score: {player.optimization_score}")
                continue

            # Otherwise, set optimization_score based on contest type
            if contest_type.lower() == 'cash' and hasattr(player, 'cash_score'):
                player.optimization_score = player.cash_score
            elif contest_type.lower() == 'gpp' and hasattr(player, 'gpp_score'):
                player.optimization_score = player.gpp_score
            elif hasattr(player, 'enhanced_score'):
                player.optimization_score = player.enhanced_score
            else:
                player.optimization_score = 0
                logger.warning(f"No valid score for {player.name}")

        return players

    def optimize_lineup(self, players: List, strategy: str = "balanced",
                        manual_selections: str = "", contest_type: str = "gpp") -> Tuple[List, float]:
        """Main optimization method with proper strategy application"""

        logger.info(f"OPTIMIZATION: Starting {contest_type.upper()} optimization")
        logger.info(f"OPTIMIZATION: Strategy: {strategy}")
        logger.info(f"OPTIMIZATION: Players available: {len(players)}")

        # Set contest type on config for use in other methods
        self.config.contest_type = contest_type

        # Apply strategy filter AND scoring
        eligible_players = self.apply_strategy_filter(players, strategy)

        if not eligible_players:
            logger.error("No eligible players after strategy filtering")
            return [], 0

        # Pre-filter for performance if needed
        if len(eligible_players) > 200:
            eligible_players = self._pre_filter_players(eligible_players, strategy)

        # Ensure scores are calculated (but don't overwrite strategy scores)
        eligible_players = self.calculate_player_scores(eligible_players)

        # Parse manual selections
        manual_names = []
        if manual_selections:
            manual_names = [name.strip() for name in manual_selections.split(',')]
            logger.info(f"Manual selections: {manual_names}")

        # Now run the MILP optimization with properly scored players
        return self._run_milp_optimization(eligible_players, manual_names, contest_type)

    def _run_milp_optimization(self, eligible_players: List[Any], manual_selections: str = "",
                               contest_type: str = "gpp") -> Tuple[Optional[List[Any]], float]:
        """Run the MILP optimization with eligible players"""

        if not eligible_players:
            logger.warning("No eligible players for optimization")
            return None, 0.0

        # Create the LP problem
        prob = pulp.LpProblem("DFS_Lineup_Optimization", pulp.LpMaximize)

        # Decision variables
        player_vars = []
        for i, player in enumerate(eligible_players):
            var = pulp.LpVariable(f"player_{i}", cat='Binary')
            player_vars.append(var)

        # Objective function - maximize total score
        objective_terms = []
        for i, player in enumerate(eligible_players):
            # CRITICAL FIX: Get the appropriate score
            score = 0.0

            # First try optimization_score (if it exists)
            if hasattr(player, 'optimization_score'):
                score = player.optimization_score
            # If not, use contest-specific score
            elif contest_type == 'cash' and hasattr(player, 'cash_score'):
                score = player.cash_score
            elif hasattr(player, 'gpp_score'):
                score = player.gpp_score
            elif hasattr(player, 'enhanced_score'):
                score = player.enhanced_score
            else:
                # Last resort - use base projection
                score = getattr(player, 'base_projection', 0)

            # Log if score is 0
            if score == 0:
                logger.debug(f"Player {player.name} has 0 score!")

            objective_terms.append(score * player_vars[i])

        prob += pulp.lpSum(objective_terms), "Total Score"

        # Constraint 1: Salary cap
        salary_terms = []
        for i, player in enumerate(eligible_players):
            salary_terms.append(player.salary * player_vars[i])
        prob += pulp.lpSum(salary_terms) <= self.config.salary_cap, "Salary Cap"

        # Optional: Minimum salary usage
        if self.config.min_salary_usage > 0:
            min_salary = self.config.salary_cap * self.config.min_salary_usage
            prob += pulp.lpSum(salary_terms) >= min_salary, "Min Salary Usage"

        # Constraint 2: Position requirements
        for position, required in self.config.position_requirements.items():
            position_terms = []
            for i, player in enumerate(eligible_players):
                # Check if player can fill this position
                if position == player.primary_position or position in getattr(player, 'positions', []):
                    position_terms.append(player_vars[i])

            # Must have exactly the required number
            if position_terms:
                prob += pulp.lpSum(position_terms) == required, f"Position_{position}"
            else:
                logger.warning(f"No players available for position {position}")
                return None, 0.0

        # Constraint 3: Exactly roster_size players
        roster_size = sum(self.config.position_requirements.values())
        prob += pulp.lpSum(player_vars) == roster_size, "Roster Size"

        # Constraint 4: Max players per team
        if self.config.max_players_per_team < roster_size:
            teams = list(set(p.team for p in eligible_players if p.team))
            for team in teams:
                team_terms = []
                for i, player in enumerate(eligible_players):
                    if player.team == team:
                        team_terms.append(player_vars[i])
                if team_terms:
                    prob += pulp.lpSum(team_terms) <= self.config.max_players_per_team, f"Team_{team}_Max"

        # Constraint 5: Manual selections (if any)
        if manual_selections:
            selected_names = [name.strip() for name in manual_selections.split(',') if name.strip()]
            for name in selected_names:
                # Find the player
                for i, player in enumerate(eligible_players):
                    if player.name.lower() == name.lower():
                        prob += player_vars[i] == 1, f"Manual_{name}"
                        break

        # Constraint 6: Pitcher-Hitter constraint
        if self.config.max_opposing_hitters < 999:
            # For each pitcher, limit opposing hitters
            for i, player in enumerate(eligible_players):
                if getattr(player, 'is_pitcher', False):
                    # Find opposing team
                    opp_team = getattr(player, 'opponent', None)
                    if opp_team:
                        # Count opposing hitters
                        opp_hitter_terms = []
                        for j, other in enumerate(eligible_players):
                            if (not getattr(other, 'is_pitcher', False) and
                                    other.team == opp_team):
                                opp_hitter_terms.append(player_vars[j])

                        if opp_hitter_terms:
                            # If this pitcher is selected, limit opposing hitters
                            prob += (pulp.lpSum(opp_hitter_terms) <=
                                     self.config.max_opposing_hitters +
                                     roster_size * (1 - player_vars[i])), f"Pitcher_Opp_{i}"

        # Solve the problem
        try:
            # Use CBC solver with timeout
            solver = pulp.PULP_CBC_CMD(timeLimit=self.config.timeout_seconds, msg=0)
            prob.solve(solver)

            # Check solution status
            if pulp.LpStatus[prob.status] != 'Optimal':
                logger.error(f"Optimization failed with status: {pulp.LpStatus[prob.status]}")
                return None, 0.0

            # Extract selected players
            selected_players = []
            total_score = 0.0

            for i, player in enumerate(eligible_players):
                if player_vars[i].varValue == 1:
                    selected_players.append(player)
                    # Use the same score calculation as in objective
                    if hasattr(player, 'optimization_score'):
                        score = player.optimization_score
                    elif contest_type == 'cash' and hasattr(player, 'cash_score'):
                        score = player.cash_score
                    elif hasattr(player, 'gpp_score'):
                        score = player.gpp_score
                    elif hasattr(player, 'enhanced_score'):
                        score = player.enhanced_score
                    else:
                        score = getattr(player, 'base_projection', 0)
                    total_score += score

            # Verify we have a complete lineup
            if len(selected_players) != roster_size:
                logger.error(f"Invalid lineup size: {len(selected_players)} != {roster_size}")
                return None, 0.0

            # Log the lineup
            logger.info(f"Optimized lineup: {sum(p.salary for p in selected_players)} salary, {total_score:.2f} points")

            return selected_players, total_score

        except Exception as e:
            logger.error(f"MILP optimization error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, 0.0

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

    def optimize(self, players: List, strategy: str = None,
                 manual_selections: Optional[List[str]] = None,
                 contest_type: str = "gpp") -> Any:
        """Optimize lineup (compatibility method) - auto-selects best strategy"""
        # Convert manual selections list to string if needed
        manual_text = ""
        if manual_selections:
            manual_text = ", ".join(manual_selections)

        # If no strategy provided, it will auto-select
        lineup, score = self.optimize_lineup(players, strategy, manual_text, contest_type)

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
    print("\n🎯 Auto-Strategy Selection:")
    print("   The optimizer now automatically selects the #1 strategy for each contest type!")
    print("   - Cash games: Uses conservative confirmed-player strategies")
    print("   - GPP: Uses upside-focused stacking strategies")
    print("   - No need to specify strategy - just pass contest_type!")