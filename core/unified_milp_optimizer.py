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

    def apply_strategy_filter(self, players: List, strategy: str) -> List:
        """Apply strategy-based filtering to player pool"""

        # Map strategies to filtering logic
        if strategy in ["confirmed_only", "confirmed_plus_value"]:
            # Only confirmed starters
            eligible = [p for p in players if getattr(p, 'is_confirmed', False)]

            # For confirmed_plus_value, add high-value players
            if strategy == "confirmed_plus_value" and len(eligible) < 30:
                non_confirmed = [p for p in players if not getattr(p, 'is_confirmed', False)]
                # Sort by value (points per dollar)
                non_confirmed.sort(key=lambda x: getattr(x, 'base_projection', 0) / max(x.salary, 1), reverse=True)
                eligible.extend(non_confirmed[:20])

        elif strategy == "stack_leverage":
            # Focus on stacking opportunities
            eligible = []
            # Get teams with high totals
            team_totals = {}
            for p in players:
                team = getattr(p, 'team', 'UNK')
                total = getattr(p, 'team_total', 0)
                if team != 'UNK' and total > 0:
                    team_totals[team] = total

            # Get top 6 teams by total
            top_teams = sorted(team_totals.items(), key=lambda x: x[1], reverse=True)[:6]
            top_team_names = [t[0] for t in top_teams]

            # Include all players from top teams
            for p in players:
                if getattr(p, 'team', 'UNK') in top_team_names:
                    eligible.append(p)
                elif p.primary_position == 'P' and getattr(p, 'is_confirmed', False):
                    eligible.append(p)

        elif strategy in ["balanced", "balanced_upside"]:
            # Mix of confirmed and high-projection players
            confirmed = [p for p in players if getattr(p, 'is_confirmed', False)]

            # Add top projections
            non_confirmed = [p for p in players if not getattr(p, 'is_confirmed', False)]

            if strategy == "balanced_upside":
                # For GPP, focus on ceiling
                non_confirmed.sort(key=lambda x: getattr(x, 'ceiling', getattr(x, 'base_projection', 0)), reverse=True)
            else:
                # For cash, focus on floor
                non_confirmed.sort(key=lambda x: getattr(x, 'floor', getattr(x, 'base_projection', 0)), reverse=True)

            eligible = confirmed + non_confirmed[:30]

        elif strategy == "multi_stack":
            # Multiple team stacks for large GPP
            eligible = []
            teams_included = set()

            # First add confirmed pitchers
            for p in players:
                if p.primary_position == 'P' and getattr(p, 'is_confirmed', False):
                    eligible.append(p)

            # Add players from high-total teams
            for p in players:
                team = getattr(p, 'team', 'UNK')
                team_total = getattr(p, 'team_total', 0)

                if team != 'UNK' and team_total >= 4.5:
                    eligible.append(p)
                    teams_included.add(team)

            # Ensure we have enough players
            if len(eligible) < 50:
                remaining = [p for p in players if p not in eligible]
                remaining.sort(key=lambda x: getattr(x, 'base_projection', 0), reverse=True)
                eligible.extend(remaining[:30])

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

    def optimize_lineup(self, players: List, strategy: str = None,
                        manual_selections: str = "", contest_type: str = "gpp") -> Tuple[List, float]:
        """
        Main optimization method - automatically selects best strategy if not provided
        """
        # Auto-select the best strategy for this contest type if not provided
        if strategy is None or strategy == "auto":
            strategy = self._get_best_strategy(contest_type, players)

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
            self.config.min_salary_usage = 0.98  # Use more salary in cash
        else:
            # GPP settings
            self.config.max_players_per_team = 5  # More stacking allowed
            self.config.preferred_stack_size = 4  # Bigger stacks
            self.config.max_opposing_hitters = 2  # More flexibility
            self.config.min_salary_usage = 0.95  # Can leave more salary on table

        # Apply strategy filter
        eligible_players = self.apply_strategy_filter(players, strategy)

        if not eligible_players:
            logger.error("No eligible players after strategy filtering")
            return [], 0

        # Pre-filter for performance
        if len(eligible_players) > 200:
            eligible_players = self._pre_filter_players(eligible_players, strategy)

        # Ensure scores are calculated
        eligible_players = self.calculate_player_scores(eligible_players)

        # Parse manual selections
        manual_names = self.parse_manual_selections(manual_selections, eligible_players)

        # Create MILP problem
        prob = pulp.LpProblem("DFS_Optimizer", pulp.LpMaximize)

        # Decision variables
        player_vars = {
            i: pulp.LpVariable(f"player_{i}", cat='Binary')
            for i in range(len(eligible_players))
        }

        # Objective: Maximize total score
        prob += pulp.lpSum([
            player_vars[i] * getattr(eligible_players[i], 'optimization_score', 0)
            for i in range(len(eligible_players))
        ])

        # Constraint: Salary cap
        prob += pulp.lpSum([
            player_vars[i] * eligible_players[i].salary
            for i in range(len(eligible_players))
        ]) <= self.config.salary_cap

        # Constraint: Minimum salary usage
        prob += pulp.lpSum([
            player_vars[i] * eligible_players[i].salary
            for i in range(len(eligible_players))
        ]) >= self.config.salary_cap * self.config.min_salary_usage

        # Position constraints
        for pos, required in self.config.position_requirements.items():
            # Find players eligible for this position
            position_players = [
                i for i in range(len(eligible_players))
                if pos in getattr(eligible_players[i], 'eligible_positions', [eligible_players[i].primary_position])
            ]

            if len(position_players) < required:
                logger.warning(
                    f"Not enough players for position {pos}: {len(position_players)} available, {required} required")
                return [], 0

            prob += pulp.lpSum([player_vars[i] for i in position_players]) == required

        # Manual selections constraint
        if manual_names:
            manual_indices = [
                i for i in range(len(eligible_players))
                if eligible_players[i].name in manual_names
            ]

            for idx in manual_indices:
                prob += player_vars[idx] == 1
                logger.info(f"Manual selection enforced: {eligible_players[idx].name}")

        # Team stacking constraints
        teams = list(set(getattr(p, 'team', 'UNK') for p in eligible_players))
        for team in teams:
            team_players = [
                i for i in range(len(eligible_players))
                if getattr(eligible_players[i], 'team', 'UNK') == team
            ]

            if team_players:
                prob += pulp.lpSum([player_vars[i] for i in team_players]) <= self.config.max_players_per_team

        # Pitcher vs opposing hitters constraint
        pitchers = [i for i in range(len(eligible_players)) if eligible_players[i].primary_position == 'P']

        for p_idx in pitchers:
            pitcher = eligible_players[p_idx]
            pitcher_team = getattr(pitcher, 'team', 'UNK')
            opponent = getattr(pitcher, 'opponent', 'UNK')

            if opponent != 'UNK':
                # Find hitters on the opposing team
                opposing_hitters = [
                    i for i in range(len(eligible_players))
                    if getattr(eligible_players[i], 'team', 'UNK') == opponent
                       and eligible_players[i].primary_position != 'P'
                ]

                if opposing_hitters and self.config.max_opposing_hitters < 999:
                    # Add constraint: if this pitcher is selected, limit opposing hitters
                    prob += pulp.lpSum([player_vars[h] for h in opposing_hitters]) <= \
                            self.config.max_opposing_hitters + (1 - player_vars[p_idx]) * len(opposing_hitters)

        # Solve the problem
        try:
            prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=self.config.timeout_seconds))

            if prob.status == pulp.LpStatusOptimal:
                # Extract the lineup
                lineup = []
                for i in range(len(eligible_players)):
                    if player_vars[i].value() == 1:
                        lineup.append(eligible_players[i])

                total_score = sum(getattr(p, 'optimization_score', 0) for p in lineup)

                # Store result
                self._last_result = {
                    'lineup': lineup,
                    'score': total_score,
                    'strategy': strategy,
                    'contest_type': contest_type
                }

                # Log correlation information
                pitchers_in_lineup = [p for p in lineup if p.primary_position == 'P']
                for pitcher in pitchers_in_lineup:
                    opp_team = getattr(pitcher, 'opponent', 'UNK')
                    if opp_team != 'UNK':
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
                    f"LINEUP SELECTED: Total score = {total_score:.1f}, "
                    f"Total salary = {sum(p.salary for p in lineup)}"
                )
                logger.info(f"Strategy used: {strategy}")
                for p in lineup:
                    logger.info(
                        f"  LINEUP: {p.primary_position} - {p.name} - ${p.salary} - "
                        f"{getattr(p, 'optimization_score', 0):.1f} pts"
                    )

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