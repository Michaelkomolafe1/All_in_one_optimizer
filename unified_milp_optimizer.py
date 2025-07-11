#!/usr/bin/env python3
"""
UNIFIED MILP OPTIMIZER - FIXED COMPLETE VERSION
==============================================
Clean implementation with all optimizations included
"""

import pulp
from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
import logging
import numpy as np
from datetime import datetime
import json

# Import unified player model
from unified_player_model import UnifiedPlayer

# Import new optimization modules
try:
    from unified_scoring_engine import get_scoring_engine
    from performance_optimizer import get_performance_optimizer

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
                'P': 2, 'C': 1, '1B': 1, '2B': 1,
                '3B': 1, 'SS': 1, 'OF': 3
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

    def get_optimization_score(self, player: UnifiedPlayer) -> float:
        """
        Get the player's score for optimization (includes pre-calculated bonuses)
        This is the score that MILP will use.
        """
        # Check if player has optimization-specific score
        if hasattr(player, 'optimization_score'):
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
                    stack_candidates = sorted(team_players,
                                              key=lambda p: getattr(p, 'batting_order', 999))[:5]

                    # Apply small bonus to encourage stacking
                    for player in stack_candidates:
                        if hasattr(player, 'batting_order') and player.batting_order in [1, 3, 5]:
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

    def _load_dfs_config(self):
        """Load configuration from dfs_config.json or optimization_config.json"""
        config_loaded = False

        # Try optimization_config.json first
        try:
            with open('optimization_config.json', 'r') as f:
                config_data = json.load(f)

            self.config.salary_cap = config_data.get('optimization', {}).get('salary_cap', 50000)
            self.config.min_salary_usage = config_data.get('optimization', {}).get('min_salary_usage', 0.95)
            self.config.max_players_per_team = config_data.get('optimization', {}).get('max_players_per_team', 4)
            self.max_form_analysis_players = config_data.get('optimization', {}).get('max_form_analysis_players', 100)

            self.logger.info("✅ Loaded configuration from optimization_config.json")
            config_loaded = True
        except:
            pass

        # Fallback to dfs_config.json
        if not config_loaded:
            try:
                with open('dfs_config.json', 'r') as f:
                    config_data = json.load(f)

                self.config.salary_cap = config_data.get('optimization', {}).get('salary_cap', 50000)
                self.config.min_salary_usage = config_data.get('optimization', {}).get('min_salary_usage', 0.95)
                self.max_form_analysis_players = config_data.get('optimization', {}).get('max_form_analysis_players')

                self.logger.info("✅ Loaded configuration from dfs_config.json")
            except:
                self.logger.warning("⚠️ Using default configuration")

    def _load_park_factors(self) -> Dict[str, float]:
        """Load park factors from file or use defaults"""
        try:
            with open('park_factors.json', 'r') as f:
                return json.load(f)
        except:
            # Default park factors for major parks
            return {
                'COL': 1.15,  # Coors Field
                'BOS': 1.08,  # Fenway
                'TEX': 1.06,  # Globe Life
                'CIN': 1.05,  # Great American
                'MIL': 1.04,  # Miller Park
                'SF': 0.92,  # Oracle Park
                'SD': 0.93,  # Petco
                'NYM': 0.95,  # Citi Field
                'SEA': 0.96,  # T-Mobile
                'MIA': 0.97  # Marlins Park
            }

    def _initialize_data_sources(self):
        """Initialize connections to real data sources"""
        # Recent form analyzer
        try:
            from recent_form_analyzer import RecentFormAnalyzer
            self.form_analyzer = RecentFormAnalyzer()
            self.logger.info("✅ Recent form analyzer initialized")
        except:
            self.form_analyzer = None
            self.logger.warning("⚠️ Recent form analyzer not available")

        # Statcast fetcher
        try:
            from simple_statcast_fetcher import SimpleStatcastFetcher
            self.statcast = SimpleStatcastFetcher()
            self.logger.info("✅ Statcast fetcher initialized")
        except:
            self.statcast = None
            self.logger.warning("⚠️ Statcast fetcher not available")

        # Vegas lines
        try:
            from vegas_lines import VegasLines
            self.vegas_lines = VegasLines()
            self.logger.info("✅ Vegas lines initialized")
        except:
            self.vegas_lines = None
            self.logger.warning("⚠️ Vegas lines not available")

    def calculate_player_scores(self, players: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """Calculate enhanced scores using unified engine or fallback"""

        if OPTIMIZATION_MODULES_AVAILABLE:
            # Use new optimization system
            engine = get_scoring_engine()
            perf_opt = get_performance_optimizer()

            # Count already calculated
            already_calculated = sum(1 for p in players if hasattr(p, '_score_calculated') and p._score_calculated)
            if already_calculated > 0:
                self.logger.info(f"Skipping {already_calculated}/{len(players)} already calculated players")

            # Define cached scoring function
            @perf_opt.cached(category='player_scores')
            def score_player(player):
                if hasattr(player, '_score_calculated') and player._score_calculated:
                    return player.enhanced_score
                return engine.calculate_score(player)

            # Batch process all players
            scores = perf_opt.batch_process(
                players,
                score_player,
                batch_size=50,
                max_workers=4
            )

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
            already_enriched = sum(1 for p in players if hasattr(p, '_is_enriched') and p._is_enriched)
            if already_enriched > 0:
                print(f"ℹ️ Skipping {already_enriched}/{len(players)} already enriched players")

            # Determine how many players to analyze for form
            form_limit = getattr(self, 'max_form_analysis_players', None)

            # Sort players by base projection for prioritization
            sorted_players = sorted(players, key=lambda p: getattr(p, 'base_projection', 0), reverse=True)

            for i, player in enumerate(sorted_players):
                # Skip if already enriched
                if hasattr(player, '_is_enriched') and player._is_enriched:
                    continue

                # Use existing calculate_enhanced_score method
                if hasattr(player, 'calculate_enhanced_score'):
                    player.calculate_enhanced_score()
                else:
                    # Fallback - just use base projection
                    player.enhanced_score = getattr(player, 'base_projection', 0)

        return players

    def optimize_lineup(self, players: List[UnifiedPlayer],
                        strategy: str = 'balanced',
                        manual_selections: str = "") -> Tuple[List[UnifiedPlayer], float]:
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
            player_vars[i] = pulp.LpVariable(f"x_{i}", cat='Binary')

        # Position assignment variables
        position_vars = {}
        for i, player in enumerate(players):
            for pos in player.positions:
                if pos in self.config.position_requirements:
                    position_vars[(i, pos)] = pulp.LpVariable(
                        f"y_{i}_{pos}", cat='Binary'
                    )

        # OBJECTIVE: Use optimization score (accounts for diversity penalties)
        objective = pulp.lpSum([
            player_vars[i] * self.get_optimization_score(players[i])
            for i in range(len(players))
        ])

        prob += objective





        # CONSTRAINTS

        # 1. Exactly 10 players (or as specified)
        total_players = sum(self.config.position_requirements.values())
        prob += pulp.lpSum(player_vars.values()) == total_players

        # 2. Salary cap constraint
        prob += pulp.lpSum([
            player_vars[i] * players[i].salary
            for i in range(len(players))
        ]) <= self.config.salary_cap

        # 3. Minimum salary usage
        prob += pulp.lpSum([
            player_vars[i] * players[i].salary
            for i in range(len(players))
        ]) >= self.config.salary_cap * self.config.min_salary_usage

        # 4. Position requirements
        for pos, required in self.config.position_requirements.items():
            prob += pulp.lpSum([
                position_vars.get((i, pos), 0)
                for i in range(len(players))
            ]) == required

        # 5. Player can only be assigned to one position
        for i in range(len(players)):
            prob += pulp.lpSum([
                position_vars.get((i, pos), 0)
                for pos in players[i].positions
                if pos in self.config.position_requirements
            ]) <= player_vars[i]

        # 6. Player must be selected if assigned to position
        for i, pos in position_vars:
            prob += position_vars[(i, pos)] <= player_vars[i]

        # 7. Team stacking constraints
        teams = list(set(p.team for p in players if p.team))
        for team in teams:
            team_indices = [i for i, p in enumerate(players) if p.team == team]
            if team_indices:
                # Max players per team
                prob += pulp.lpSum([
                    player_vars[i] for i in team_indices
                ]) <= self.config.max_players_per_team

        # 8. Pitcher vs opposing hitters constraint
        if self.config.enforce_lineup_rules:
            self._add_pitcher_hitter_constraints(prob, players, player_vars)

        # Solve
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=self.config.timeout_seconds)
        prob.solve(solver)

        if prob.status == pulp.LpStatusOptimal:
            return self._extract_solution(players, player_vars, position_vars)
        else:
            raise Exception(f"Optimization failed: {pulp.LpStatus[prob.status]}")


        """
        Calculate small correlation bonuses for stacks
        Based on REAL batting order data only
        """
        if not self.config.use_correlation:
            return None

        correlation_terms = []

        # Group players by team
        team_players = {}
        for i, player in enumerate(players):
            if player.team and player.primary_position != 'P':
                if player.team not in team_players:
                    team_players[player.team] = []
                team_players[player.team].append(i)

        # Create correlation bonuses for consecutive batting order
        for team, indices in team_players.items():
            # Only if we have batting order data
            team_with_order = []
            for idx in indices:
                player = players[idx]
                if hasattr(player, 'batting_order') and player.batting_order:
                    team_with_order.append((idx, player.batting_order))

            if len(team_with_order) >= 2:
                # Sort by batting order
                team_with_order.sort(key=lambda x: x[1])

                # Add small bonus for consecutive batters
                for i in range(len(team_with_order) - 1):
                    idx1, order1 = team_with_order[i]
                    idx2, order2 = team_with_order[i + 1]

                    if order2 - order1 == 1:  # Consecutive
                        # Small bonus for selecting both
                        bonus = players[idx1].enhanced_score * self.config.correlation_boost
                        correlation_terms.append(
                            bonus * player_vars[idx1] * player_vars[idx2]
                        )

        if correlation_terms:
            return pulp.lpSum(correlation_terms)
        return None

    def _add_pitcher_hitter_constraints(self, prob: pulp.LpProblem,
                                        players: List[UnifiedPlayer],
                                        player_vars: Dict):
        """Add constraints to prevent selecting hitters against your own pitchers"""
        # Find all pitcher indices
        pitcher_indices = [i for i, p in enumerate(players) if p.primary_position == 'P']

        # For each pitcher, limit opposing team hitters
        for p_idx in pitcher_indices:
            pitcher = players[p_idx]
            if not pitcher.opponent:
                continue

            # Find opposing team hitters
            opp_hitter_indices = [
                i for i, p in enumerate(players)
                if p.team == pitcher.opponent and p.primary_position != 'P'
            ]

            if opp_hitter_indices:
                # Limit to max allowed
                prob += pulp.lpSum([
                    player_vars[h_idx] for h_idx in opp_hitter_indices
                ]) <= self.config.max_hitters_vs_pitcher * (1 - player_vars[p_idx])

    def _extract_solution(self, players: List[UnifiedPlayer],
                          player_vars: Dict,
                          position_vars: Dict) -> Tuple[List[UnifiedPlayer], float]:
        """Extract lineup from solved MILP"""
        lineup = []
        total_score = 0

        for i, player in enumerate(players):
            if player_vars[i].value() == 1:
                # Find assigned position
                assigned_pos = None
                for pos in player.positions:
                    if (i, pos) in position_vars and position_vars[(i, pos)].value() == 1:
                        assigned_pos = pos
                        break

                # Create player copy with assigned position
                player_copy = player.copy()
                player_copy.assigned_position = assigned_pos
                lineup.append(player_copy)
                # Use the same score that was used in optimization
                total_score += self.get_optimization_score(player)

        return lineup, total_score


class StrategyFilter:
    """
    Creates player pools based on strategy WITHOUT modifying scores
    """

    def __init__(self):
        self.logger = logger

    def apply_strategy_filter(self, players: List[UnifiedPlayer],
                              strategy: str, manual_input: str = "") -> List[UnifiedPlayer]:
        """
        Creates player pools WITHOUT modifying scores
        """

        # Parse manual selections
        manual_players = self._parse_manual_selections(players, manual_input)

        # Get confirmed players
        confirmed_players = [p for p in players if p.is_confirmed]

        # Build pool based on strategy
        if strategy == 'confirmed_plus_manual':
            base_pool = list(set(confirmed_players + manual_players))

            if len(base_pool) < 40:
                remaining = [p for p in players if p not in base_pool]
                remaining.sort(key=lambda x: x.enhanced_score, reverse=True)
                base_pool.extend(remaining[:40 - len(base_pool)])

            return base_pool

        elif strategy == 'manual_only':
            return manual_players

        elif strategy == 'top_value':
            players_with_value = [(p, p.enhanced_score / (p.salary / 1000))
                                  for p in players if p.salary > 0]
            players_with_value.sort(key=lambda x: x[1], reverse=True)
            cutoff = max(20, len(players) // 2)
            return [p for p, _ in players_with_value[:cutoff]]

        elif strategy == 'high_ceiling':
            ceiling_players = []

            for player in players:
                # Must have real performance data
                ceiling_score = 0

                # Check recent form
                if hasattr(player, '_recent_performance') and player._recent_performance:
                    form = player._recent_performance.get('form_score', 1.0)
                    if form > 1.15:
                        ceiling_score += 2
                    elif form > 1.10:
                        ceiling_score += 1

                # Check Vegas data
                if hasattr(player, '_vegas_data') and player._vegas_data:
                    implied = player._vegas_data.get('implied_total', 0)
                    if implied > 5.0:
                        ceiling_score += 2
                    elif implied > 4.5:
                        ceiling_score += 1

                # Check recent hot streak
                if hasattr(player, 'dff_l5_avg') and player.base_projection > 0:
                    if player.dff_l5_avg / player.base_projection > 1.20:
                        ceiling_score += 2

                if ceiling_score >= 2:  # Multiple positive indicators
                    ceiling_players.append(player)

            # Ensure minimum pool size
            if len(ceiling_players) < 30:
                remaining = [p for p in players if p not in ceiling_players]
                remaining.sort(key=lambda x: x.enhanced_score, reverse=True)
                ceiling_players.extend(remaining[:30 - len(ceiling_players)])

            return ceiling_players

        elif strategy == 'balanced':
            base_set = set(confirmed_players + manual_players)

            # Add high-value players
            value_players = sorted(players,
                                   key=lambda x: x.enhanced_score / (x.salary / 1000) if x.salary > 0 else 0,
                                   reverse=True)

            for player in value_players:
                if player not in base_set:
                    base_set.add(player)
                if len(base_set) >= 60:
                    break

            return list(base_set)

        else:
            # Default: confirmed only
            return confirmed_players

    def _parse_manual_selections(self, all_players: List[UnifiedPlayer],
                                 manual_input: str) -> List[UnifiedPlayer]:
        """Parse manual player selections from input string"""
        if not manual_input or not manual_input.strip():
            return []

        selected = []
        names = [name.strip() for name in manual_input.split(',') if name.strip()]

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