#!/usr/bin/env python3
"""
MILP OPTIMIZER WITH INTEGRATED STACKING
======================================
Extends UnifiedMILPOptimizer to include automated stacking constraints
"""

from typing import List, Optional, Tuple
import pulp
import logging

from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig
from automated_stacking_system import StackCandidate

logger = logging.getLogger(__name__)


class MILPWithStacking(UnifiedMILPOptimizer):
    """
    Enhanced MILP optimizer that integrates automated stacking
    """

    def __init__(self, config: OptimizationConfig = None):
        super().__init__(config)
        self.selected_stack = None
        self.stack_constraints_enabled = True

    def optimize_lineup_with_stack(
            self,
            players: List,
            selected_stack: Optional[StackCandidate] = None,
            strategy: str = "balanced"
    ) -> Tuple[List, float]:
        """
        Optimize lineup with automated stack constraints

        Args:
            players: List of all players
            selected_stack: Pre-selected stack to enforce
            strategy: Optimization strategy

        Returns:
            (lineup, total_score)
        """
        self.selected_stack = selected_stack

        # If stack provided, ensure those players are in the pool
        if selected_stack:
            logger.info(f"Optimizing with {selected_stack.team} stack ({selected_stack.size} players)")

            # Mark stack players for inclusion
            stack_player_names = [p.name.lower() for p in selected_stack.players]
            for player in players:
                if player.name.lower() in stack_player_names:
                    # Boost their score slightly to encourage selection
                    player._original_score = player.optimization_score
                    player.optimization_score *= 1.02  # 2% boost
                    player._in_stack = True

        # Run base optimization with modified constraints
        lineup, score = self.optimize_lineup(players, strategy)

        # Restore original scores
        if selected_stack:
            for player in players:
                if hasattr(player, '_original_score'):
                    player.optimization_score = player._original_score
                    delattr(player, '_original_score')
                if hasattr(player, '_in_stack'):
                    delattr(player, '_in_stack')

        return lineup, score

    def _run_milp_optimization(self, players: List) -> Tuple[List, float]:
        """
        Override to add stacking constraints
        """
        if not players:
            return [], 0

        # Create optimization problem
        prob = pulp.LpProblem("DFS_Lineup_With_Stacking", pulp.LpMaximize)

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

        # STANDARD CONSTRAINTS

        # 1. Salary cap constraint
        prob += pulp.lpSum([
            player_vars[i] * players[i].salary
            for i in range(len(players))
        ]) <= self.config.salary_cap

        # 2. Minimum salary usage
        prob += pulp.lpSum([
            player_vars[i] * players[i].salary
            for i in range(len(players))
        ]) >= self.config.salary_cap * self.config.min_salary_usage

        # 3. Position requirements
        for pos, required in self.config.position_requirements.items():
            eligible_indices = [
                i for i in range(len(players))
                if players[i].primary_position == pos or pos in getattr(players[i], 'positions', [])
            ]

            if len(eligible_indices) < required:
                logger.warning(f"Not enough players for position {pos}")
                return [], 0

            prob += pulp.lpSum([
                player_vars[i] for i in eligible_indices
            ]) == required

        # 4. Total roster size
        total_required = sum(self.config.position_requirements.values())
        prob += pulp.lpSum(player_vars) == total_required

        # STACKING CONSTRAINTS

        if self.selected_stack and self.stack_constraints_enabled:
            # 5a. Force inclusion of stack players
            stack_indices = []
            for i, player in enumerate(players):
                if hasattr(player, '_in_stack') and player._in_stack:
                    stack_indices.append(i)

            if stack_indices:
                # Must include at least min_stack_size from the stack
                min_from_stack = min(3, len(stack_indices))  # At least 3 or all available
                prob += pulp.lpSum([
                    player_vars[i] for i in stack_indices
                ]) >= min_from_stack

                logger.info(f"Added stack constraint: minimum {min_from_stack} from {self.selected_stack.team}")

        else:
            # 5b. General team stacking constraints
            teams = set(p.team for p in players if hasattr(p, 'team'))

            for team in teams:
                team_indices = [
                    i for i in range(len(players))
                    if getattr(players[i], 'team', None) == team
                ]

                if team_indices:
                    # Standard max players per team
                    prob += pulp.lpSum([
                        player_vars[i] for i in team_indices
                    ]) <= self.config.max_players_per_team

        # 6. Correlation constraints (optional)
        if self.config.use_correlation:
            # Limit opposing hitters vs your pitcher
            pitcher_indices = [
                i for i in range(len(players))
                if players[i].primary_position == 'P'
            ]

            for pitcher_idx in pitcher_indices:
                pitcher = players[pitcher_idx]
                pitcher_team = getattr(pitcher, 'team', None)

                if pitcher_team:
                    # Find opposing team (would need game data)
                    # For now, just ensure we don't have too many hitters vs our pitcher
                    pass

        # Solve
        try:
            solver = pulp.PULP_CBC_CMD(
                timeLimit=self.config.timeout_seconds,
                msg=0  # Suppress output
            )
            prob.solve(solver)

            if prob.status == pulp.LpStatusOptimal:
                # Extract lineup
                lineup = []
                total_score = 0

                for i in range(len(players)):
                    if player_vars[i].varValue == 1:
                        lineup.append(players[i])
                        total_score += getattr(players[i], 'optimization_score', 0)

                # Verify stack was included
                if self.selected_stack:
                    stack_count = sum(
                        1 for p in lineup
                        if p.team == self.selected_stack.team
                    )
                    logger.info(f"Final lineup includes {stack_count} players from {self.selected_stack.team} stack")

                # Sort lineup by position
                position_order = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']
                lineup.sort(key=lambda p: (
                    position_order.index(p.primary_position)
                    if p.primary_position in position_order else 99
                ))

                return lineup, total_score

            else:
                logger.error(f"Optimization failed with status: {pulp.LpStatus[prob.status]}")
                return [], 0

        except Exception as e:
            logger.error(f"MILP optimization error: {e}")
            return [], 0

    def optimize_with_multiple_stacks(
            self,
            players: List,
            primary_stack: StackCandidate,
            secondary_stack: Optional[StackCandidate] = None
    ) -> Tuple[List, float]:
        """
        Optimize with multiple stacks (game stacking)
        """
        # Mark players from both stacks
        all_stack_players = set()

        # Primary stack
        for p in primary_stack.players:
            all_stack_players.add(p.name.lower())

        # Secondary stack (e.g., opposing team)
        if secondary_stack:
            for p in secondary_stack.players[:2]:  # Limit secondary stack size
                all_stack_players.add(p.name.lower())

        # Mark players
        for player in players:
            if player.name.lower() in all_stack_players:
                player._in_multi_stack = True
                player.optimization_score *= 1.03  # 3% boost

        # Temporarily increase max players per team
        original_max = self.config.max_players_per_team
        self.config.max_players_per_team = max(5, len(primary_stack.players) + 1)

        # Run optimization
        lineup, score = self._run_milp_optimization(players)

        # Restore settings
        self.config.max_players_per_team = original_max

        # Clean up
        for player in players:
            if hasattr(player, '_in_multi_stack'):
                delattr(player, '_in_multi_stack')
                if hasattr(player, 'optimization_score'):
                    player.optimization_score /= 1.03

        return lineup, score


def create_milp_with_stacking(config: Optional[OptimizationConfig] = None) -> MILPWithStacking:
    """Create MILP optimizer with stacking capabilities"""
    return MILPWithStacking(config)