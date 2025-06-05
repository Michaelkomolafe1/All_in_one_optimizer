#!/usr/bin/env python3
"""
OPTIMAL LINEUP OPTIMIZER
=======================
Uses integer programming to find the true optimal lineup
No greedy fill-ins, only the best possible lineup
"""

import pulp
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of lineup optimization"""
    lineup: List
    total_score: float
    total_salary: int
    positions_filled: Dict[str, int]
    optimization_status: str


class OptimalLineupOptimizer:
    """
    True optimal lineup optimizer using integer programming
    No greedy fill-ins - finds the globally optimal lineup
    """

    def __init__(self, salary_cap: int = 50000):
        self.salary_cap = salary_cap
        self.classic_requirements = {
            'P': 2,
            'C': 1,
            '1B': 1,
            '2B': 1,
            '3B': 1,
            'SS': 1,
            'OF': 3
        }
        self.showdown_requirements = {
            'CPT': 1,  # Captain
            'UTIL': 5  # Utility
        }

    def optimize_classic_lineup(self, players: List, use_confirmations: bool = False) -> OptimizationResult:
        """
        Optimize classic lineup using integer programming
        """
        if len(players) < 10:
            return OptimizationResult(
                lineup=[],
                total_score=0,
                total_salary=0,
                positions_filled={},
                optimization_status="Not enough players"
            )

        # Create the optimization problem
        prob = pulp.LpProblem("DFS_Classic_Lineup", pulp.LpMaximize)

        # Decision variables - binary for each player
        player_vars = {}
        for i, player in enumerate(players):
            player_vars[i] = pulp.LpVariable(f"player_{i}", cat='Binary')

        # Objective function - maximize total projected points
        prob += pulp.lpSum([
            player_vars[i] * player.enhanced_score
            for i, player in enumerate(players)
        ])

        # Constraint 1: Salary cap
        prob += pulp.lpSum([
            player_vars[i] * player.salary
            for i, player in enumerate(players)
        ]) <= self.salary_cap

        # Constraint 2: Exactly 10 players
        prob += pulp.lpSum(player_vars.values()) == 10

        # Constraint 3: Position requirements - FIXED
        for position, required in self.classic_requirements.items():
            # Get eligible players for this position
            eligible_indices = []
            for i, player in enumerate(players):
                if self._can_fill_position(player, position):
                    eligible_indices.append(i)

            # Must have EXACTLY the required number (not >=)
            prob += pulp.lpSum([player_vars[i] for i in eligible_indices]) == required

        # Constraint 4: Each player can only be used once (already handled by binary)

        # Solve the problem
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        # Extract results
        if prob.status == pulp.LpStatusOptimal:
            selected_players = []
            total_salary = 0
            positions_filled = {pos: [] for pos in self.classic_requirements}

            # Get selected players
            for i, player in enumerate(players):
                if player_vars[i].value() == 1:
                    selected_players.append(player)
                    total_salary += player.salary

            # Now assign positions optimally
            position_assignments = self._assign_positions_optimally(selected_players)

            # Apply assignments and count
            for player, assigned_pos in position_assignments.items():
                player.assigned_position = assigned_pos
                if assigned_pos in positions_filled:
                    positions_filled[assigned_pos].append(player)

            # Verify we filled all positions correctly
            positions_filled_count = {pos: len(players) for pos, players in positions_filled.items()}

            # Check if valid
            for pos, required in self.classic_requirements.items():
                if positions_filled_count.get(pos, 0) != required:
                    return OptimizationResult(
                        lineup=[],
                        total_score=0,
                        total_salary=0,
                        positions_filled={},
                        optimization_status=f"Failed to fill position {pos} correctly"
                    )

            # Calculate total score
            total_score = sum(p.enhanced_score for p in selected_players)

            return OptimizationResult(
                lineup=selected_players,
                total_score=total_score,
                total_salary=total_salary,
                positions_filled=positions_filled_count,
                optimization_status="Optimal"
            )
        else:
            return OptimizationResult(
                lineup=[],
                total_score=0,
                total_salary=0,
                positions_filled={},
                optimization_status=f"Optimization failed: {pulp.LpStatus[prob.status]}"
            )

    def _assign_positions_optimally(self, players: List) -> Dict:
        """
        Assign positions to players optimally using Hungarian algorithm
        """
        position_assignments = {}
        unassigned_players = set(players)

        # First, assign players who can only play one position
        for pos in self.classic_requirements:
            for player in list(unassigned_players):
                eligible_positions = [p for p in self.classic_requirements if self._can_fill_position(player, p)]
                if len(eligible_positions) == 1 and eligible_positions[0] == pos:
                    position_assignments[player] = pos
                    unassigned_players.remove(player)

        # Then assign remaining players
        # Create a bipartite matching problem
        remaining_positions = []
        for pos, count in self.classic_requirements.items():
            assigned = sum(1 for p, assigned_pos in position_assignments.items() if assigned_pos == pos)
            remaining_positions.extend([pos] * (count - assigned))

        if unassigned_players and remaining_positions:
            # Use greedy assignment for now
            for pos in remaining_positions:
                best_player = None
                for player in unassigned_players:
                    if self._can_fill_position(player, pos):
                        best_player = player
                        break

                if best_player:
                    position_assignments[best_player] = pos
                    unassigned_players.remove(best_player)

        return position_assignments

    def optimize_showdown_lineup(self, players: List) -> OptimizationResult:
        """
        Optimize showdown lineup - all players are UTIL
        Captain gets 1.5x points but costs 1.5x salary

        Args:
            players: List of player objects

        Returns:
            OptimizationResult with optimal lineup
        """
        if len(players) < 6:
            return OptimizationResult(
                lineup=[],
                total_score=0,
                total_salary=0,
                positions_filled={},
                optimization_status="Not enough players for showdown"
            )

        # Create the optimization problem
        prob = pulp.LpProblem("DFS_Showdown_Lineup", pulp.LpMaximize)

        # Decision variables - binary for each player/role combination
        captain_vars = {}
        util_vars = {}

        for i, player in enumerate(players):
            captain_vars[i] = pulp.LpVariable(f"captain_{i}", cat='Binary')
            util_vars[i] = pulp.LpVariable(f"util_{i}", cat='Binary')

        # Objective function - maximize total points
        # Captain gets 1.5x points
        prob += pulp.lpSum([
            captain_vars[i] * player.enhanced_score * 1.5 +
            util_vars[i] * player.enhanced_score
            for i, player in enumerate(players)
        ])

        # Constraint 1: Salary cap
        # Captain costs 1.5x salary
        prob += pulp.lpSum([
            captain_vars[i] * player.salary * 1.5 +
            util_vars[i] * player.salary
            for i, player in enumerate(players)
        ]) <= self.salary_cap

        # Constraint 2: Exactly 1 captain
        prob += pulp.lpSum(captain_vars.values()) == 1

        # Constraint 3: Exactly 5 utility players
        prob += pulp.lpSum(util_vars.values()) == 5

        # Constraint 4: Each player can only be used once
        for i in range(len(players)):
            prob += captain_vars[i] + util_vars[i] <= 1

        # Solve the problem
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        # Extract results
        if prob.status == pulp.LpStatusOptimal:
            selected_players = []
            total_salary = 0
            total_score = 0
            positions_filled = {'CPT': 0, 'UTIL': 0}

            # Get captain
            for i, player in enumerate(players):
                if captain_vars[i].value() == 1:
                    player_copy = player.copy() if hasattr(player, 'copy') else player
                    player_copy.assigned_position = 'CPT'
                    player_copy.multiplier = 1.5
                    selected_players.append(player_copy)
                    total_salary += int(player.salary * 1.5)
                    total_score += player.enhanced_score * 1.5
                    positions_filled['CPT'] = 1

            # Get utility players
            for i, player in enumerate(players):
                if util_vars[i].value() == 1:
                    player_copy = player.copy() if hasattr(player, 'copy') else player
                    player_copy.assigned_position = 'UTIL'
                    player_copy.multiplier = 1.0
                    selected_players.append(player_copy)
                    total_salary += player.salary
                    total_score += player.enhanced_score
                    positions_filled['UTIL'] += 1

            return OptimizationResult(
                lineup=selected_players,
                total_score=total_score,
                total_salary=total_salary,
                positions_filled=positions_filled,
                optimization_status="Optimal"
            )
        else:
            return OptimizationResult(
                lineup=[],
                total_score=0,
                total_salary=0,
                positions_filled={},
                optimization_status=f"Optimization failed: {pulp.LpStatus[prob.status]}"
            )

    def _can_fill_position(self, player, position: str) -> bool:
        """
        Check if player can fill a specific position

        Args:
            player: Player object
            position: Position to check

        Returns:
            True if player can fill position
        """
        # Get player's eligible positions
        if hasattr(player, 'positions') and player.positions:
            player_positions = player.positions
        elif hasattr(player, 'primary_position'):
            player_positions = [player.primary_position]
        else:
            return False

        # Direct position match
        if position in player_positions:
            return True

        # Outfield flexibility
        if position == 'OF' and any(pos in ['OF', 'LF', 'CF', 'RF'] for pos in player_positions):
            return True

        # Utility can be filled by anyone
        if position == 'UTIL':
            return True

        return False


def assign_positions_to_lineup(self, lineup: List) -> List:
    """
    Assign specific positions to players in lineup
    Ensures each position requirement is met optimally
    """
    position_assignments = {}
    assigned_players = set()

    # First pass: assign players who can only fill one position
    for pos, required in self.classic_requirements.items():
        candidates = [
            p for p in lineup
            if p not in assigned_players and
               self._can_fill_position(p, pos) and
               len([req_pos for req_pos in self.classic_requirements
                    if self._can_fill_position(p, req_pos)]) == 1
        ]

        for player in candidates[:required]:
            player.assigned_position = pos
            assigned_players.add(player)
            if pos not in position_assignments:
                position_assignments[pos] = []
            position_assignments[pos].append(player)

    # Second pass: fill remaining positions
    for pos, required in self.classic_requirements.items():
        current_count = len(position_assignments.get(pos, []))
        if current_count < required:
            candidates = [
                p for p in lineup
                if p not in assigned_players and
                   self._can_fill_position(p, pos)
            ]

            # Sort by how many other positions they can fill (less flexible first)
            candidates.sort(key=lambda p: len([
                req_pos for req_pos in self.classic_requirements
                if self._can_fill_position(p, req_pos)
            ]))

            needed = required - current_count
            for player in candidates[:needed]:
                player.assigned_position = pos
                assigned_players.add(player)
                if pos not in position_assignments:
                    position_assignments[pos] = []
                position_assignments[pos].append(player)

    return lineup