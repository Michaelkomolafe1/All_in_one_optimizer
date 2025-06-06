#!/usr/bin/env python3
"""
OPTIMAL LINEUP OPTIMIZER
=======================
Uses integer programming to find the true optimal lineup
No greedy fill-ins, only the best possible lineup
"""

import pulp
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
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
        Optimize classic lineup using integer programming with multi-position support
        """
        if len(players) < 10:
            return OptimizationResult(
                lineup=[],
                total_score=0,
                total_salary=0,
                positions_filled={},
                optimization_status="Not enough players"
            )

        print(f"\n💰 Pre-Optimization Analysis:")
        salaries = [p.salary for p in players]
        print(f"   Players available: {len(players)}")
        print(f"   Salary range: ${min(salaries):,} - ${max(salaries):,}")
        print(f"   Average salary: ${sum(salaries) / len(salaries):,.0f}")

        # Show multi-position players
        print("\n🔄 Multi-position players:")
        multi_pos_count = 0
        for player in players:
            if hasattr(player, 'positions') and len(player.positions) > 1:
                multi_pos_count += 1
                if multi_pos_count <= 10:  # Show first 10
                    print(f"   {player.name}: {' / '.join(player.positions)} (${player.salary:,})")

        if multi_pos_count > 10:
            print(f"   ... and {multi_pos_count - 10} more")
        print(f"   Total: {multi_pos_count} players with multiple position eligibility")

        # Create the optimization problem
        prob = pulp.LpProblem("DFS_Classic_Lineup", pulp.LpMaximize)

        # Decision variables - binary for each player
        player_vars = {}
        for i, player in enumerate(players):
            player_vars[i] = pulp.LpVariable(f"player_{i}", cat='Binary')

        # Group players by team for stacking analysis
        team_player_indices = {}
        for i, player in enumerate(players):
            if player.team not in team_player_indices:
                team_player_indices[player.team] = []
            team_player_indices[player.team].append(i)

        # Apply small stacking bonus to players on teams with 4+ available players
        # This encourages stacking without breaking the linear programming constraints
        stack_bonus_multiplier = 0.03  # 3% bonus for being in a potential stack

        for team, player_indices in team_player_indices.items():
            if len(player_indices) >= 4:
                for idx in player_indices:
                    # Store original score and apply temporary bonus
                    if not hasattr(players[idx], '_original_enhanced_score'):
                        players[idx]._original_enhanced_score = players[idx].enhanced_score
                    players[idx]._stack_potential_score = players[idx].enhanced_score * (1 + stack_bonus_multiplier)
            else:
                for idx in player_indices:
                    players[idx]._stack_potential_score = players[idx].enhanced_score

        # Objective function - maximize total projected points (with stack bonuses)
        prob += pulp.lpSum([
            player_vars[i] * getattr(player, '_stack_potential_score', player.enhanced_score)
            for i, player in enumerate(players)
        ])

        # Constraint 1: Salary cap
        prob += pulp.lpSum([
            player_vars[i] * player.salary
            for i, player in enumerate(players)
        ]) <= self.salary_cap

        # Constraint 2: Exactly 10 players
        prob += pulp.lpSum(player_vars.values()) == 10

        # Create position assignment variables
        position_vars = {}
        for i, player in enumerate(players):
            for pos in self.classic_requirements.keys():
                if self._can_fill_position(player, pos):
                    position_vars[(i, pos)] = pulp.LpVariable(f"player_{i}_pos_{pos}", cat='Binary')

        # Constraint 3: If a player is selected, they must be assigned to exactly one position
        for i, player in enumerate(players):
            eligible_positions = [pos for pos in self.classic_requirements.keys()
                                  if self._can_fill_position(player, pos)]

            if eligible_positions:
                # If player is selected, sum of position assignments must equal 1
                prob += pulp.lpSum([position_vars[(i, pos)] for pos in eligible_positions]) == player_vars[i]

        # Constraint 4: Each position must be filled exactly as required
        for pos, required in self.classic_requirements.items():
            eligible_count = sum(1 for p in players if self._can_fill_position(p, pos))
            print(f"   {pos}: {eligible_count} eligible players (need exactly {required})")

            # Sum of all players assigned to this position must equal requirement
            prob += pulp.lpSum([
                position_vars[(i, pos)]
                for i, player in enumerate(players)
                if (i, pos) in position_vars
            ]) == required

        # Optional: Add diversity constraint to avoid too many players from one team
        for team, player_indices in team_player_indices.items():
            if len(player_indices) > 5:
                # Limit to max 5 players from any single team
                prob += pulp.lpSum([player_vars[i] for i in player_indices]) <= 5

        # Debug: Show constraint counts
        print(f"\n🧮 Running MILP optimization...")
        print(f"   Variables: {len(player_vars) + len(position_vars)}")
        print(f"   Constraints: {len(prob.constraints)}")

        # Solve the problem
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=30)
        prob.solve(solver)

        # Extract results
        if prob.status == pulp.LpStatusOptimal:
            selected_players = []
            total_salary = 0
            positions_filled = {pos: [] for pos in self.classic_requirements}

            # Get selected players WITH their assigned positions
            for i, player in enumerate(players):
                if player_vars[i].value() == 1:
                    # Find which position this player was assigned to
                    assigned_pos = None
                    for pos in self.classic_requirements.keys():
                        if (i, pos) in position_vars and position_vars[(i, pos)].value() == 1:
                            assigned_pos = pos
                            break

                    if assigned_pos:
                        player.assigned_position = assigned_pos
                        # Restore original score if we modified it
                        if hasattr(player, '_original_enhanced_score'):
                            player.enhanced_score = player._original_enhanced_score
                        selected_players.append(player)
                        total_salary += player.salary
                        positions_filled[assigned_pos].append(player)

            # Verify we filled all positions correctly
            positions_filled_count = {pos: len(players) for pos, players in positions_filled.items()}

            # Calculate total score
            total_score = sum(p.enhanced_score for p in selected_players)

            print(f"\n✅ MILP Optimization successful!")
            print(f"   Score: {total_score:.2f}")
            print(f"   Salary: ${total_salary:,}")
            print(f"\n📋 Optimal Lineup:")
            for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
                for p in positions_filled.get(pos, []):
                    multi_pos_indicator = "*" if len(p.positions) > 1 else " "
                    print(f"   {pos}: {p.name}{multi_pos_indicator} - ${p.salary:,} ({p.enhanced_score:.1f} pts)")

            if any(len(p.positions) > 1 for p in selected_players):
                print("\n   * = Multi-position eligible player")

            # Clean up temporary attributes
            for player in players:
                if hasattr(player, '_stack_potential_score'):
                    delattr(player, '_stack_potential_score')
                if hasattr(player, '_original_enhanced_score'):
                    delattr(player, '_original_enhanced_score')

            return OptimizationResult(
                lineup=selected_players,
                total_score=total_score,
                total_salary=total_salary,
                positions_filled=positions_filled_count,
                optimization_status="Optimal"
            )
        else:
            print(f"\n❌ MILP Optimization failed: {pulp.LpStatus[prob.status]}")

            # Run detailed debugging
            self.debug_infeasible_lineup(players)

            return OptimizationResult(
                lineup=[],
                total_score=0,
                total_salary=0,
                positions_filled={},
                optimization_status=f"Optimization failed: {pulp.LpStatus[prob.status]}"
            )

    def debug_infeasible_lineup(self, players: List):
        """Debug why optimization is infeasible"""
        print("\n🔍 DEBUGGING INFEASIBLE LINEUP")
        print("=" * 60)

        # 1. Check position coverage
        print("📊 Position Coverage Analysis:")
        insufficient_positions = []
        for pos, required in self.classic_requirements.items():
            eligible = [p for p in players if self._can_fill_position(p, pos)]
            print(f"   {pos}: {len(eligible)} players available (need {required})")

            if len(eligible) < required:
                insufficient_positions.append(pos)
                print(f"      ❌ INSUFFICIENT!")

            if len(eligible) <= required + 1:  # Show players when tight
                print(f"      Players: {[p.name + f' (${p.salary})' for p in eligible]}")

        if insufficient_positions:
            print(f"\n❌ Cannot fill positions: {insufficient_positions}")
            return

        # 2. Check salary feasibility by position
        print("\n💰 Minimum Salary by Position:")
        total_min = 0
        position_minimums = {}

        for pos, required in self.classic_requirements.items():
            eligible = sorted([p for p in players if self._can_fill_position(p, pos)],
                              key=lambda x: x.salary)[:required]
            if len(eligible) >= required:
                pos_min = sum(p.salary for p in eligible)
                total_min += pos_min
                position_minimums[pos] = (pos_min, eligible)
                print(f"   {pos}: ${pos_min:,} for {required} player(s)")
            else:
                print(f"   {pos}: INSUFFICIENT PLAYERS!")

        print(f"\n   Total Minimum: ${total_min:,}")
        print(f"   Salary Cap: ${self.salary_cap:,}")
        print(f"   Feasible: {'YES' if total_min <= self.salary_cap else 'NO'}")

        # 3. Try a greedy solution to see what's blocking
        print("\n🎯 Attempting Greedy Solution:")
        lineup = []
        used_players = set()
        remaining_cap = self.salary_cap
        position_filled = {pos: 0 for pos in self.classic_requirements}

        # Fill positions in order of scarcity
        sorted_positions = sorted(self.classic_requirements.items(),
                                  key=lambda x: len([p for p in players if self._can_fill_position(p, x[0])]))

        for pos, needed in sorted_positions:
            for _ in range(needed):
                # Find cheapest eligible player not yet used
                candidates = [p for p in players
                              if p not in used_players
                              and self._can_fill_position(p, pos)
                              and p.salary <= remaining_cap]

                if candidates:
                    # Use best value instead of just cheapest
                    best = max(candidates, key=lambda x: x.enhanced_score / x.salary)
                    lineup.append(best)
                    used_players.add(best)
                    remaining_cap -= best.salary
                    position_filled[pos] += 1
                    print(f"   Added {best.name} ({pos}) for ${best.salary:,} (${remaining_cap:,} left)")
                else:
                    print(f"   ❌ Cannot fill {pos} #{position_filled[pos] + 1} with ${remaining_cap:,} remaining")
                    print(
                        f"      Available players: {len([p for p in players if p not in used_players and self._can_fill_position(p, pos)])}")
                    print(
                        f"      Affordable players: {len([p for p in players if p not in used_players and self._can_fill_position(p, pos) and p.salary <= remaining_cap])}")
                    return

        if len(lineup) == 10:
            total_used = self.salary_cap - remaining_cap
            total_score = sum(p.enhanced_score for p in lineup)
            print(f"\n✅ Greedy solution found!")
            print(f"   Total salary: ${total_used:,}")
            print(f"   Total score: {total_score:.2f}")
            print(f"   Remaining cap: ${remaining_cap:,}")
            print("\n⚠️ The MILP solver might have conflicting constraints.")

            # Show the greedy lineup
            print("\n📋 Greedy Lineup:")
            for p in sorted(lineup, key=lambda x: x.primary_position):
                print(f"   {p.primary_position}: {p.name} - ${p.salary:,} ({p.enhanced_score:.1f} pts)")

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

        # Outfield flexibility (LF, CF, RF can all play OF)
        if position == 'OF' and any(pos in ['OF', 'LF', 'CF', 'RF'] for pos in player_positions):
            return True

        # Utility can be filled by anyone
        if position == 'UTIL':
            return True

        return False


# Add this method to OptimalLineupOptimizer class:

def evaluate_lineup_stacks(self, lineup: List) -> Dict[str, Any]:
    """Evaluate stacking patterns in lineup"""
    stack_info = {
        'stacks': [],
        'correlation_bonus': 0.0,
        'largest_stack': 0,
        'has_pitcher_stack': False
    }

    # Count players by team
    team_counts = {}
    team_players = {}

    for player in lineup:
        if not hasattr(player, 'team'):
            continue

        team = player.team
        if team not in team_counts:
            team_counts[team] = 0
            team_players[team] = []

        team_counts[team] += 1
        team_players[team].append(player)

    # Identify stacks (2+ players from same team)
    for team, count in team_counts.items():
        if count >= 2:
            stack_players = team_players[team]

            # Check stack quality
            has_pitcher = any(p.primary_position == 'P' for p in stack_players)
            has_top_hitter = any(
                hasattr(p, 'batting_order') and p.batting_order <= 3
                for p in stack_players if p.primary_position != 'P'
            )

            stack_data = {
                'team': team,
                'size': count,
                'has_pitcher': has_pitcher,
                'has_top_hitter': has_top_hitter,
                'players': [p.name for p in stack_players]
            }

            # Calculate correlation bonus
            if count >= 3:  # 3+ player stack
                base_bonus = 1.5 * count
                if has_top_hitter:
                    base_bonus *= 1.2
                if has_pitcher and count >= 4:  # Pitcher + 3 hitters
                    base_bonus *= 1.3
                    stack_info['has_pitcher_stack'] = True

                stack_data['bonus'] = base_bonus
                stack_info['correlation_bonus'] += base_bonus
            else:
                stack_data['bonus'] = 0.5 * count
                stack_info['correlation_bonus'] += stack_data['bonus']

            stack_info['stacks'].append(stack_data)
            stack_info['largest_stack'] = max(stack_info['largest_stack'], count)

    return stack_info

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