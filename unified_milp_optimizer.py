#!/usr/bin/env python3
"""
UNIFIED MILP OPTIMIZER - FIXED COMPLETE VERSION
==============================================
Clean implementation with all optimizations included
"""

import copy
from unified_config_manager import get_config_value
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pulp

# Import unified player model
from unified_player_model import UnifiedPlayer

# Import new optimization modules

try:
    from performance_optimizer import get_performance_optimizer
    from unified_scoring_engine import get_scoring_engine

    OPTIMIZATION_MODULES_AVAILABLE = True
except ImportError:
    OPTIMIZATION_MODULES_AVAILABLE = False
    print("⚠️ New optimization modules not available, using fallback")

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
    correlation_boost: float = 0.05  # Small boost for correlated plays

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
    NO artificial bonuses - pure performance-based optimization
    """

    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.logger = logger

        # Load DFS configuration
        self._load_dfs_config()

        # Load park factors if available
        self.park_factors = self._load_park_factors()

        # Load real data sources
        self._initialize_data_sources()

    def _load_dfs_config(self):
        """Load configuration from unified config system"""
        try:
            # Use unified config
            self.config.salary_cap = get_config_value("optimization.salary_cap", 50000)
            self.config.min_salary_usage = get_config_value("optimization.min_salary_usage", 0.95)
            self.config.max_players_per_team = get_config_value("optimization.max_players_per_team", 4)
            self.max_form_analysis_players = get_config_value("optimization.max_form_analysis_players", 100)

            self.logger.info("✅ Loaded configuration from unified config system")
        except Exception as e:
            self.logger.warning(f"Could not load unified config: {e}")
            # Keep defaults

        # Fallback to dfs_config.json
        if not config_loaded:
            try:
                with open("dfs_config.json", "r") as f:
                    config_data = json.load(f)

                self.config.salary_cap = config_data.get("optimization", {}).get(
                    "salary_cap", 50000
                )
                self.config.min_salary_usage = config_data.get("optimization", {}).get(
                    "min_salary_usage", 0.95
                )
                self.max_form_analysis_players = config_data.get("optimization", {}).get(
                    "max_form_analysis_players", 100
                )

                self.logger.info("✅ Loaded configuration from dfs_config.json")
            except:
                self.logger.warning("⚠️ Using default configuration")

    def _load_park_factors(self) -> Dict[str, float]:
        """Load park factors from file or use defaults"""
        try:
            with open("park_factors.json", "r") as f:
                return json.load(f)
        except:
            # Default park factors for major parks
            return {
                "COL": 1.15,  # Coors Field
                "BOS": 1.08,  # Fenway
                "TEX": 1.06,  # Globe Life
                "CIN": 1.05,  # Great American
                "MIL": 1.04,  # Miller Park
                "SF": 0.92,  # Oracle Park
                "SD": 0.93,  # Petco
                "NYM": 0.95,  # Citi Field
                "SEA": 0.96,  # T-Mobile
                "MIA": 0.97,  # Marlins Park
            }

    def _initialize_data_sources(self):
        """Initialize connections to real data sources"""
        # This is a placeholder - implement based on your data sources

    def get_optimization_score(self, player: UnifiedPlayer) -> float:
        """
        Get the player's score for optimization (includes pre-calculated bonuses)
        This is the score that MILP will use.
        """
        # Check if player has optimization-specific score
        if hasattr(player, "optimization_score"):
            return player.optimization_score

        # Otherwise use enhanced score
        return player.enhanced_score

    def prepare_players_for_optimization(self, players: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """
        Pre-calculate all bonuses and penalties before optimization.
        This avoids quadratic terms in MILP.
        """
        # Calculate correlation bonuses if enabled
        if self.config.use_correlation:
            # Group players by team for stacking bonuses
            team_groups = {}
            for player in players:
                if player.team not in team_groups:
                    team_groups[player.team] = []
                team_groups[player.team].append(player)

            # Apply stacking bonuses
            for team, team_players in team_groups.items():
                if len(team_players) >= 3:  # Potential stack
                    # Find best stack candidates (e.g., 1-3-5 batting order)
                    stack_candidates = sorted(
                        team_players, key=lambda p: getattr(p, "batting_order", None) or 999
                    )[:5]

                    # Apply small bonus to encourage stacking
                    for player in stack_candidates:
                        if hasattr(player, "batting_order") and player.batting_order in [1, 3, 5]:
                            # Add 5% bonus for stack candidates
                            player.optimization_score = player.enhanced_score * 1.05
                        else:
                            player.optimization_score = player.enhanced_score
                else:
                    # No stacking bonus for teams with few players
                    for player in team_players:
                        player.optimization_score = player.enhanced_score
        else:
            # No correlation - just use enhanced score
            for player in players:
                player.optimization_score = player.enhanced_score

        return players

    def calculate_player_scores(self, players: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """
        Calculate enhanced scores for all players using available data
        """
        if OPTIMIZATION_MODULES_AVAILABLE:
            # Use new scoring system
            scoring_engine = get_scoring_engine()
            perf_opt = get_performance_optimizer()

            # Use score_player method
            score_player = scoring_engine.calculate_score

            # Process in batches
            scores = perf_opt.batch_process(players, score_player, batch_size=50, max_workers=4)

            # Apply scores
            for player, score in zip(players, scores):
                if score is not None:
                    player.enhanced_score = score
                    player._score_calculated = True

            self.logger.info(f"Calculated scores for {len(players)} players")

        else:
            # Fallback to original calculation method
            self.logger.info("Using fallback score calculation")

            # Count how many are already enriched
            already_enriched = sum(
                1 for p in players if hasattr(p, "_is_enriched") and p._is_enriched
            )
            if already_enriched > 0:
                print(f"ℹ️ Skipping {already_enriched}/{len(players)} already enriched players")

            # Determine how many players to analyze for form
            getattr(self, "max_form_analysis_players", None)

            # Sort players by base projection for prioritization
            sorted_players = sorted(
                players, key=lambda p: getattr(p, "base_projection", 0), reverse=True
            )

            for i, player in enumerate(sorted_players):
                # Skip if already enriched
                if hasattr(player, "_is_enriched") and player._is_enriched:
                    continue

                # Use existing calculate_enhanced_score method
                if hasattr(player, "calculate_enhanced_score"):
                    player.calculate_enhanced_score()
                else:
                    # Fallback - just use base projection
                    player.enhanced_score = getattr(player, "base_projection", 0)

        return players

    def optimize_lineup(
        self, players: List[UnifiedPlayer], strategy: str = "balanced", manual_selections: str = ""
    ) -> Tuple[List[UnifiedPlayer], float]:
        """
        Main optimization method
        1. Apply strategy filter to create player pool
        2. Calculate scores using real data
        3. Pre-calculate correlation bonuses (NEW)
        4. Run MILP optimization
        """
        # Step 1: Create player pool based on strategy
        strategy_filter = StrategyFilter()
        player_pool = strategy_filter.apply_strategy_filter(players, strategy, manual_selections)

        self.logger.info(f"Strategy '{strategy}' created pool of {len(player_pool)} players")

        # Step 2: Calculate enhanced scores using real data
        player_pool = self.calculate_player_scores(player_pool)

        # Step 3: Pre-calculate correlation bonuses (NEW)
        player_pool = self.prepare_players_for_optimization(player_pool)

        # Step 4: Run MILP optimization
        try:
            return self._optimize_milp(player_pool)
        except Exception as e:
            self.logger.error(f"MILP optimization failed: {e}")
            return [], 0

    def _optimize_milp(self, players: List[UnifiedPlayer]) -> Tuple[List[UnifiedPlayer], float]:
        """
        Pure MILP optimization with correlation constraints
        """
        self.logger.info(f"🔬 MILP: Optimizing {len(players)} players")

        # Create problem
        prob = pulp.LpProblem("DFS_Clean_Optimizer", pulp.LpMaximize)

        # Decision variables
        player_vars = {}
        for i, player in enumerate(players):
            player_vars[i] = pulp.LpVariable(f"x_{i}", cat="Binary")

        # Position assignment variables
        position_vars = {}
        for i, player in enumerate(players):
            for pos in player.positions:
                if pos in self.config.position_requirements:
                    position_vars[(i, pos)] = pulp.LpVariable(f"y_{i}_{pos}", cat="Binary")

        # OBJECTIVE: Use optimization score (accounts for diversity penalties)
        objective = pulp.lpSum(
            [player_vars[i] * self.get_optimization_score(players[i]) for i in range(len(players))]
        )

        prob += objective

        # CONSTRAINTS

        # 1. Exactly 10 players (or as specified)
        total_players = sum(self.config.position_requirements.values())
        prob += pulp.lpSum(player_vars.values()) == total_players

        # 2. Salary cap constraint
        prob += (
            pulp.lpSum([player_vars[i] * players[i].salary for i in range(len(players))])
            <= self.config.salary_cap
        )

        # 3. Minimum salary usage
        prob += (
            pulp.lpSum([player_vars[i] * players[i].salary for i in range(len(players))])
            >= self.config.salary_cap * self.config.min_salary_usage
        )

        # 4. Position requirements
        for pos, required in self.config.position_requirements.items():
            prob += (
                pulp.lpSum([position_vars.get((i, pos), 0) for i in range(len(players))])
                == required
            )

        # 5. Link player and position variables
        for i, player in enumerate(players):
            # If player is selected, they must fill exactly one position
            prob += (
                pulp.lpSum(
                    [
                        position_vars.get((i, pos), 0)
                        for pos in player.positions
                        if pos in self.config.position_requirements
                    ]
                )
                == player_vars[i]
            )

        # 6. Max players per team (handle None batting_order)
        for team in set(p.team for p in players):
            team_players = [i for i, p in enumerate(players) if p.team == team]
            if team_players:
                prob += (
                    pulp.lpSum([player_vars[i] for i in team_players])
                    <= self.config.max_players_per_team
                )

        # 7. Batting order diversity (if enabled) - handle None values
        if self.config.use_correlation and self.config.enforce_lineup_rules:
            # Group by team and batting order
            team_order_groups = {}
            for i, player in enumerate(players):
                if hasattr(player, "batting_order") and player.batting_order is not None:
                    key = (player.team, player.batting_order)
                    if key not in team_order_groups:
                        team_order_groups[key] = []
                    team_order_groups[key].append(i)

            # Max 1 player per batting order per team
            for (team, order), player_indices in team_order_groups.items():
                if len(player_indices) > 1:
                    prob += pulp.lpSum([player_vars[i] for i in player_indices]) <= 1

        # 8. Hitter vs Pitcher constraints (with opponent handling)
        if self.config.max_hitters_vs_pitcher > 0:
            pitcher_opponents = {}
            for i, player in enumerate(players):
                if "P" in player.positions:
                    opp = player.opponent if hasattr(player, "opponent") else None
                    if opp:
                        if opp not in pitcher_opponents:
                            pitcher_opponents[opp] = []
                        pitcher_opponents[opp].append(i)

            # For each team, limit hitters facing selected pitchers
            for team in set(p.team for p in players if "P" not in p.positions):
                team_hitters = [
                    i for i, p in enumerate(players) if p.team == team and "P" not in p.positions
                ]

                opposing_pitchers = pitcher_opponents.get(team, [])

                if team_hitters and opposing_pitchers:
                    # If we select a pitcher, limit hitters from opposing team
                    for pitcher_idx in opposing_pitchers:
                        prob += pulp.lpSum(
                            [player_vars[h] for h in team_hitters]
                        ) <= self.config.max_hitters_vs_pitcher + (
                            1 - player_vars[pitcher_idx]
                        ) * len(
                            team_hitters
                        )

        # Solve with timeout
        solver = pulp.PULP_CBC_CMD(timeLimit=self.config.timeout_seconds, msg=0)
        prob.solve(solver)

        # Extract solution
        if prob.status != pulp.LpStatusOptimal:
            self.logger.warning("No optimal solution found")
            return [], 0

        # Build lineup with assigned positions
        lineup = []
        total_score = 0

        for i, player in enumerate(players):
            if player_vars[i].value() > 0.5:
                # Find assigned position
                for pos in player.positions:
                    if pos in self.config.position_requirements:
                        if (
                            position_vars.get((i, pos), None)
                            and position_vars[(i, pos)].value() > 0.5
                        ):
                            # Create a copy to avoid modifying original
                            player_copy = copy.copy(player)
                            player_copy.assigned_position = pos
                            lineup.append(player_copy)
                            # Use the same score that was used in optimization
                            total_score += self.get_optimization_score(player)
                            break

        return lineup, total_score


class StrategyFilter:
    """
    Creates player pools based on strategy WITHOUT modifying scores
    """

    def __init__(self):
        self.logger = logger

    def apply_strategy_filter(
        self, players: List[UnifiedPlayer], strategy: str, manual_input: str = ""
    ) -> List[UnifiedPlayer]:
        """
        Creates player pools WITHOUT modifying scores
        """

        # Parse manual selections
        manual_players = self._parse_manual_selections(players, manual_input)

        # Get confirmed players
        confirmed_players = [p for p in players if p.is_confirmed]

        # Build pool based on strategy
        if strategy == "confirmed_plus_manual":
            base_pool = list(set(confirmed_players + manual_players))

            if len(base_pool) < 40:
                remaining = [p for p in players if p not in base_pool]
                remaining.sort(key=lambda x: (x.enhanced_score if x.enhanced_score is not None else 0), reverse=True)
                base_pool.extend(remaining[: 40 - len(base_pool)])

            return base_pool

        elif strategy == "manual_only":
            return manual_players

        elif strategy == "top_value":
            players_with_value = [
                (p, p.enhanced_score / (p.salary / 1000)) for p in players if p.salary > 0
            ]
            players_with_value.sort(key=lambda x: x[1], reverse=True)
            cutoff = max(20, len(players) // 2)
            return [p for p, _ in players_with_value[:cutoff]]

        elif strategy == "high_ceiling":
            ceiling_players = []

            for player in players:
                # Must have real performance data
                pass

                # Check recent form
                if hasattr(player, "_recent_performance") and player._recent_performance:
                    form = player._recent_performance.get("form_score", 1.0)
                    if form > 1.15:  # Hot streak
                        player.enhanced_score * 1.2
                        ceiling_players.append(player)
                        continue

                # Check high upside stats
                if hasattr(player, "statcast_data") and player.statcast_data:
                    data = player.statcast_data
                    if data.get("barrel_rate", 0) > 10 or data.get("hard_hit_rate", 0) > 45:
                        player.enhanced_score * 1.15
                        ceiling_players.append(player)

            # Sort by ceiling potential
            ceiling_players.sort(key=lambda x: (x.enhanced_score if x.enhanced_score is not None else 0), reverse=True)
            return ceiling_players[: max(30, len(players) // 3)]

        elif strategy == "balanced":
            # Mix of confirmed, high-value, and top-projected
            pool = set(confirmed_players + manual_players)

            # Add some high-value plays
            values = [
                (p, p.enhanced_score / (p.salary / 1000))
                for p in players
                if p.salary > 0 and p not in pool
            ]
            values.sort(key=lambda x: x[1], reverse=True)
            pool.update([p for p, _ in values[:10]])

            # Add top projections
            remaining = [p for p in players if p not in pool]
            remaining.sort(key=lambda x: (x.enhanced_score if x.enhanced_score is not None else 0), reverse=True)
            pool.update(remaining[:20])

            return list(pool)

        else:  # 'all_players' or unknown
            return players

    def _parse_manual_selections(
        self, all_players: List[UnifiedPlayer], manual_input: str
    ) -> List[UnifiedPlayer]:
        """Parse manual player selections from input string"""
        if not manual_input or not manual_input.strip():
            return []

        selected = []
        names = [name.strip() for name in manual_input.split(",") if name.strip()]

        for name in names:
            # Find best match
            best_match = None
            best_score = 0

            for player in all_players:
                # Calculate similarity
                score = self._name_similarity(name.lower(), player.name.lower())
                if score > best_score and score > 0.7:  # 70% threshold
                    best_score = score
                    best_match = player

            if best_match:
                # Mark as manually selected
                best_match.is_manual_selected = True
                selected.append(best_match)
                self.logger.info(f"Manual selection: {best_match.name} matched for '{name}'")
            else:
                self.logger.warning(f"No match found for manual selection: '{name}'")

        return selected

    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity score"""
        # Direct match
        if name1 == name2:
            return 1.0

        # Partial match
        if name1 in name2 or name2 in name1:
            return 0.9

        # Last name match
        parts1 = name1.split()
        parts2 = name2.split()
        if parts1 and parts2 and parts1[-1] == parts2[-1]:
            return 0.8

        # Character-based similarity
        from difflib import SequenceMatcher

        return SequenceMatcher(None, name1, name2).ratio()


# Convenience function for backwards compatibility
def create_unified_optimizer(config: OptimizationConfig = None) -> UnifiedMILPOptimizer:
    """Create a unified MILP optimizer instance"""
    return UnifiedMILPOptimizer(config)


if __name__ == "__main__":
    # Test basic functionality
    print("Unified MILP Optimizer module loaded successfully")
    optimizer = UnifiedMILPOptimizer()
    print(f"Salary cap: ${optimizer.config.salary_cap}")
    print(f"Position requirements: {optimizer.config.position_requirements}")
