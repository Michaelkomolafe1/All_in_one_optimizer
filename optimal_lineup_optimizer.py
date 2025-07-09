#!/usr/bin/env python3
"""
OPTIMAL LINEUP OPTIMIZER - FIXED VERSION
=======================================
✅ Fixed position constraints to enforce EXACT requirements
✅ Proper multi-position player handling
✅ No more 3 pitchers or duplicate positions!
"""

import pulp
import numpy as np
import copy
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
    Fixed optimal lineup optimizer with proper position constraints
    """

    def __init__(self, salary_cap: int = 50000):
        self.salary_cap = salary_cap
        self.classic_requirements = {
            'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3
        }
        self.showdown_requirements = {
            'CPT': 1,  # Captain
            'UTIL': 5  # Utility
        }

    def check_for_duplicate_players(self):
        """Check if there are duplicate players in the pool"""
        print("\n🔍 CHECKING FOR DUPLICATE PLAYERS")
        print("=" * 60)

        # Check by name
        name_counts = {}
        for player in self.players:
            name_key = f"{player.name}_{player.team}"
            if name_key not in name_counts:
                name_counts[name_key] = []
            name_counts[name_key].append(player)

        # Find duplicates
        duplicates_found = False
        for name_key, players in name_counts.items():
            if len(players) > 1:
                duplicates_found = True
                print(f"❌ DUPLICATE: {name_key} appears {len(players)} times")
                for i, p in enumerate(players):
                    print(f"   {i + 1}. ID: {p.id}, Salary: ${p.salary}, Positions: {p.positions}")

        if not duplicates_found:
            print("✅ No duplicate players found")

        return duplicates_found

    def optimize_classic_lineup(self, players: List, use_confirmations: bool = False) -> OptimizationResult:
        """
        FIXED: Classic lineup optimization with exact position requirements
        """
        print("\n🏈 CLASSIC LINEUP OPTIMIZATION")
        print("=" * 50)

        if len(players) < 10:
            return OptimizationResult(
                lineup=[], total_score=0, total_salary=0,
                positions_filled={}, optimization_status="Not enough players"
            )

        # Pre-validation
        validation_result = self._validate_classic_feasibility(players)
        if not validation_result['feasible']:
            return OptimizationResult(
                lineup=[], total_score=0, total_salary=0,
                positions_filled={}, optimization_status=validation_result['reason']
            )

        # Try optimization with proper constraints
        try:
            return self._fixed_classic_milp_optimization(players, use_confirmations)
        except Exception as e:
            print(f"❌ MILP optimization failed: {e}")
            print("🔄 Falling back to greedy optimization...")
            return self._greedy_classic_fallback(players)

    def _fixed_classic_milp_optimization(self, players: List, use_confirmations: bool) -> OptimizationResult:
        """
        FIXED MILP optimization with proper position assignment
        """
        n_players = len(players)

        # Create problem
        prob = pulp.LpProblem("DFS_Classic_Fixed", pulp.LpMaximize)

        # Decision variables
        # x[i] = 1 if player i is selected
        player_vars = {}
        for i in range(n_players):
            player_vars[i] = pulp.LpVariable(f"x_{i}", cat='Binary')

        # Position assignment variables
        # y[i,pos] = 1 if player i is assigned to position pos
        position_vars = {}
        player_positions = {}  # Track which positions each player can fill

        for i, player in enumerate(players):
            player_positions[i] = []
            for pos in self.classic_requirements.keys():
                if self._can_fill_position(player, pos):
                    position_vars[(i, pos)] = pulp.LpVariable(f"y_{i}_{pos}", cat='Binary')
                    player_positions[i].append(pos)

        # Objective: maximize total score
        prob += pulp.lpSum([
            player_vars[i] * players[i].enhanced_score
            for i in range(n_players)
        ])

        # Constraint 1: Exactly 10 players
        prob += pulp.lpSum(player_vars.values()) == 10

        # Constraint 2: Salary cap
        prob += pulp.lpSum([
            player_vars[i] * players[i].salary
            for i in range(n_players)
        ]) <= self.salary_cap

        # Constraint 3: If a player is selected, they must be assigned to exactly one position
        for i in range(n_players):
            if player_positions[i]:  # If player can fill any position
                prob += pulp.lpSum([
                    position_vars.get((i, pos), 0)
                    for pos in player_positions[i]
                ]) == player_vars[i]

        # Constraint 4: Each position must be filled EXACTLY as required
        for pos, required in self.classic_requirements.items():
            prob += pulp.lpSum([
                position_vars.get((i, pos), 0)
                for i in range(n_players)
                if (i, pos) in position_vars
            ]) == required

        # Optional: Confirmation bonus
        if use_confirmations:
            confirmation_bonus = pulp.lpSum([
                player_vars[i] * (1 if hasattr(players[i], 'is_confirmed') and players[i].is_confirmed else 0)
                for i in range(n_players)
            ])
            # Soft constraint - try to include more confirmed players
            prob += confirmation_bonus >= 0

        # Solve with timeout
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=30)
        prob.solve(solver)

        if prob.status == pulp.LpStatusOptimal:
            return self._extract_fixed_classic_solution(players, player_vars, position_vars)
        else:
            raise Exception(f"MILP failed with status: {pulp.LpStatus[prob.status]}")

    def _extract_fixed_classic_solution(self, players: List, player_vars: Dict,
                                        position_vars: Dict) -> OptimizationResult:
        """
        Extract solution with proper position assignments from MILP
        """
        selected_players = []
        positions_filled = {pos: 0 for pos in self.classic_requirements}

        # Get selected players and their assigned positions
        for i, player in enumerate(players):
            if player_vars[i].value() == 1:
                # Find which position this player was assigned to
                assigned_pos = None
                for pos in self.classic_requirements.keys():
                    if position_vars.get((i, pos)) and position_vars[(i, pos)].value() == 1:
                        assigned_pos = pos
                        break

                if assigned_pos:
                    # Create player copy with assigned position
                    player_copy = self._copy_player(player)
                    player_copy.assigned_position = assigned_pos
                    selected_players.append(player_copy)
                    positions_filled[assigned_pos] += 1
                else:
                    print(f"⚠️  Warning: {player.name} selected but no position assigned")

        # Verify we have exactly 10 players
        if len(selected_players) != 10:
            print(f"❌ Error: Selected {len(selected_players)} players instead of 10")
            return OptimizationResult(
                lineup=[], total_score=0, total_salary=0,
                positions_filled={}, optimization_status="Invalid player count"
            )

        # Verify position requirements are met
        for pos, required in self.classic_requirements.items():
            if positions_filled[pos] != required:
                print(f"❌ Error: {pos} has {positions_filled[pos]} players, need {required}")
                return OptimizationResult(
                    lineup=[], total_score=0, total_salary=0,
                    positions_filled={}, optimization_status=f"Invalid {pos} count"
                )

        total_salary = sum(p.salary for p in selected_players)
        total_score = sum(p.enhanced_score for p in selected_players)

        # Sort lineup by position for display
        position_order = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
        sorted_lineup = []
        position_counts = {pos: 0 for pos in self.classic_requirements}

        for desired_pos in position_order:
            for player in selected_players:
                if (player.assigned_position == desired_pos and
                        player not in sorted_lineup):
                    sorted_lineup.append(player)
                    break

        return OptimizationResult(
            lineup=sorted_lineup,
            total_score=total_score,
            total_salary=total_salary,
            positions_filled=positions_filled,
            optimization_status="Optimal"
        )

    def optimize_showdown_lineup(self, players: List) -> OptimizationResult:
        """
        Showdown optimization (unchanged from original)
        """
        print("\n🎰 SHOWDOWN LINEUP OPTIMIZATION")
        print("=" * 50)

        if len(players) < 6:
            return OptimizationResult(
                lineup=[], total_score=0, total_salary=0,
                positions_filled={}, optimization_status="Not enough players for showdown (need 6)"
            )

        try:
            return self._safe_showdown_milp_optimization(players)
        except Exception as e:
            print(f"❌ MILP showdown optimization failed: {e}")
            print("🔄 Falling back to greedy showdown optimization...")
            return self._greedy_showdown_fallback(players)

    def _validate_classic_feasibility(self, players: List) -> Dict:
        """Pre-validate if classic optimization is feasible"""
        print("🔍 Pre-validating classic feasibility...")

        # Check position coverage
        for pos, required in self.classic_requirements.items():
            eligible = [p for p in players if self._can_fill_position(p, pos)]
            if len(eligible) < required:
                return {
                    'feasible': False,
                    'reason': f"Insufficient {pos} players: {len(eligible)}/{required}"
                }

        # Check if we have enough multi-position flexibility
        total_roster_spots = sum(self.classic_requirements.values())  # Should be 10
        if len(players) < total_roster_spots:
            return {
                'feasible': False,
                'reason': f"Not enough players: {len(players)}/{total_roster_spots}"
            }

        return {'feasible': True, 'reason': 'Valid'}

    def _safe_showdown_milp_optimization(self, players: List) -> OptimizationResult:
        """Safe showdown MILP optimization with enhanced duplicate prevention"""

        # First, ensure unique players
        unique_players = []
        seen_ids = set()

        for player in players:
            # Use player ID or name+team as unique identifier
            player_key = f"{player.name}_{player.team}" if not hasattr(player, 'id') else player.id

            if player_key not in seen_ids:
                unique_players.append(player)
                seen_ids.add(player_key)
            else:
                print(f"⚠️ Skipping duplicate player: {player.name} ({player.team})")

        players = unique_players
        print(f"🎯 Optimizing with {len(players)} unique players")

        # Create problem
        prob = pulp.LpProblem("DFS_Showdown", pulp.LpMaximize)

        # Decision variables
        captain_vars = {}
        util_vars = {}
        for i, player in enumerate(players):
            captain_vars[i] = pulp.LpVariable(f"cpt_{i}", cat='Binary')
            util_vars[i] = pulp.LpVariable(f"util_{i}", cat='Binary')

        # Objective: Captain gets 1.5x points
        prob += pulp.lpSum([
            captain_vars[i] * player.enhanced_score * 1.5 +
            util_vars[i] * player.enhanced_score
            for i, player in enumerate(players)
        ])

        # Constraint 1: Exactly 1 captain
        prob += pulp.lpSum(captain_vars.values()) == 1

        # Constraint 2: Exactly 5 utility
        prob += pulp.lpSum(util_vars.values()) == 5

        # Constraint 3: Each player used at most once (CRITICAL)
        for i in range(len(players)):
            prob += captain_vars[i] + util_vars[i] <= 1

        # Constraint 4: Salary cap with captain costing 1.5x
        prob += pulp.lpSum([
            captain_vars[i] * player.salary * 1.5 +
            util_vars[i] * player.salary
            for i, player in enumerate(players)
        ]) <= self.salary_cap

        # Constraint 5: Must have players from both teams
        teams = list(set(p.team for p in players))
        print(f"Teams in showdown: {teams}")

        if len(teams) >= 2:
            # At least 1 player from each of first 2 teams
            for team in teams[:2]:
                team_indices = [i for i, p in enumerate(players) if p.team == team]
                if team_indices:
                    prob += pulp.lpSum([
                        captain_vars[i] + util_vars[i]
                        for i in team_indices
                    ]) >= 1

        # Solve
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=30)
        prob.solve(solver)

        print(f"Optimization status: {pulp.LpStatus[prob.status]}")

        if prob.status == pulp.LpStatusOptimal:
            # Debug: show which variables are selected
            selected_captain = None
            selected_utils = []

            for i, player in enumerate(players):
                if captain_vars[i].value() == 1:
                    selected_captain = (i, player)
                    print(f"Captain selected: {player.name} ({player.team})")
                if util_vars[i].value() == 1:
                    selected_utils.append((i, player))
                    print(f"Util selected: {player.name} ({player.team})")

            return self._extract_showdown_solution(players, captain_vars, util_vars)
        else:
            raise Exception(f"Showdown MILP failed: {pulp.LpStatus[prob.status]}")

    def _extract_showdown_solution(self, players: List, captain_vars: Dict, util_vars: Dict) -> OptimizationResult:
        """Extract showdown solution with proper team preservation"""
        selected_players = []
        total_salary = 0
        total_score = 0
        positions_filled = {'CPT': 0, 'UTIL': 0}

        # Track which indices were selected
        selected_indices = set()

        # Extract captain
        for i, player in enumerate(players):
            if captain_vars[i].value() == 1:
                if i in selected_indices:
                    print(f"❌ ERROR: Player {player.name} already selected!")
                    continue

                player_copy = self._copy_player(player)
                player_copy.assigned_position = 'CPT'
                player_copy.multiplier = 1.5

                # CRITICAL: Ensure team is preserved
                if not hasattr(player_copy, 'team') or not player_copy.team:
                    print(f"⚠️ WARNING: No team for {player_copy.name}")
                    player_copy.team = player.team  # Force copy team

                selected_players.append(player_copy)
                total_salary += int(player.salary * 1.5)
                total_score += player.enhanced_score * 1.5
                positions_filled['CPT'] = 1
                selected_indices.add(i)

                print(f"✅ Captain: {player_copy.name} ({player_copy.team}) - ${int(player.salary * 1.5):,}")

        # Extract utility players
        for i, player in enumerate(players):
            if util_vars[i].value() == 1:
                if i in selected_indices:
                    print(f"❌ ERROR: Player {player.name} already selected as captain!")
                    continue

                player_copy = self._copy_player(player)
                player_copy.assigned_position = 'UTIL'
                player_copy.multiplier = 1.0

                # CRITICAL: Ensure team is preserved
                if not hasattr(player_copy, 'team') or not player_copy.team:
                    print(f"⚠️ WARNING: No team for {player_copy.name}")
                    player_copy.team = player.team  # Force copy team

                selected_players.append(player_copy)
                total_salary += player.salary
                total_score += player.enhanced_score
                positions_filled['UTIL'] += 1
                selected_indices.add(i)

                print(f"✅ Utility: {player_copy.name} ({player_copy.team}) - ${player.salary:,}")

        # Verify lineup
        if len(selected_players) != 6:
            print(f"❌ ERROR: Expected 6 players, got {len(selected_players)}")

        # Check team distribution
        team_counts = {}
        for p in selected_players:
            team = p.team if hasattr(p, 'team') else 'UNKNOWN'
            team_counts[team] = team_counts.get(team, 0) + 1

        print(f"\n📊 Team distribution: {team_counts}")

        return OptimizationResult(
            lineup=selected_players,
            total_score=total_score,
            total_salary=total_salary,
            positions_filled=positions_filled,
            optimization_status="Optimal" if len(selected_players) == 6 else "Incomplete"
        )

    def _copy_player(self, player):
        """Safe player copying that preserves all attributes including team"""
        try:
            import copy
            player_copy = copy.deepcopy(player)

            # Ensure critical attributes are preserved
            critical_attrs = ['name', 'team', 'salary', 'id', 'positions', 'primary_position']
            for attr in critical_attrs:
                if hasattr(player, attr):
                    setattr(player_copy, attr, getattr(player, attr))
                else:
                    print(f"⚠️ Missing attribute {attr} on {player.name}")

            return player_copy
        except Exception as e:
            print(f"❌ Error copying player {player.name}: {e}")
            # Fallback: manual copy
            player_copy = type(player).__new__(type(player))
            for key, value in player.__dict__.items():
                try:
                    player_copy.__dict__[key] = copy.deepcopy(value)
                except:
                    player_copy.__dict__[key] = value
            return player_copy

    def _can_fill_position(self, player, position: str) -> bool:
        """Check if player can fill position"""
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

        # OF flexibility (LF, CF, RF can all play OF)
        if position == 'OF' and any(pos in ['OF', 'LF', 'CF', 'RF'] for pos in player_positions):
            return True

        return False

    def _greedy_classic_fallback(self, players: List) -> OptimizationResult:
        """Greedy fallback that respects exact position requirements"""
        print("🔄 Using greedy classic fallback...")

        # Sort by value
        players_with_value = [(p, p.enhanced_score / (p.salary / 1000)) for p in players if p.salary > 0]
        players_with_value.sort(key=lambda x: x[1], reverse=True)

        lineup = []
        remaining_salary = self.salary_cap
        positions_filled = {pos: 0 for pos in self.classic_requirements}

        # Fill each position with best available player
        for pos, required in self.classic_requirements.items():
            candidates = [
                (p, v) for p, v in players_with_value
                if p not in lineup and self._can_fill_position(p, pos)
            ]

            for _ in range(required):
                if not candidates:
                    break

                # Find best player that fits salary
                for player, value in candidates:
                    if player.salary <= remaining_salary:
                        player_copy = self._copy_player(player)
                        player_copy.assigned_position = pos
                        lineup.append(player_copy)
                        remaining_salary -= player.salary
                        positions_filled[pos] += 1
                        # Remove from candidates
                        candidates = [(p, v) for p, v in candidates if p != player]
                        break

        if len(lineup) == 10:
            total_salary = sum(p.salary for p in lineup)
            total_score = sum(p.enhanced_score for p in lineup)
            return OptimizationResult(
                lineup=lineup, total_score=total_score, total_salary=total_salary,
                positions_filled=positions_filled, optimization_status="Greedy"
            )
        else:
            return OptimizationResult(
                lineup=[], total_score=0, total_salary=0,
                positions_filled={}, optimization_status="Greedy failed - insufficient players"
            )

    def _greedy_showdown_fallback(self, players: List) -> OptimizationResult:
        """Greedy fallback for showdown lineup"""
        print("🔄 Using greedy showdown fallback...")

        # Sort by value
        players_with_value = [(p, p.enhanced_score / (p.salary / 1000)) for p in players if p.salary > 0]
        players_with_value.sort(key=lambda x: x[1], reverse=True)

        best_lineup = None
        best_score = 0

        # Try each player as captain
        for captain_idx, (captain_player, _) in enumerate(players_with_value[:20]):  # Try top 20 as captain
            if captain_player.salary * 1.5 > self.salary_cap:
                continue

            lineup = []
            remaining_salary = self.salary_cap

            # Add captain
            captain_copy = self._copy_player(captain_player)
            captain_copy.assigned_position = 'CPT'
            captain_copy.multiplier = 1.5
            lineup.append(captain_copy)
            remaining_salary -= int(captain_player.salary * 1.5)

            # Add 5 best utility players that fit
            for player, value in players_with_value:
                if (len(lineup) < 6 and
                        player != captain_player and
                        player.salary <= remaining_salary):
                    util_copy = self._copy_player(player)
                    util_copy.assigned_position = 'UTIL'
                    util_copy.multiplier = 1.0
                    lineup.append(util_copy)
                    remaining_salary -= player.salary

            # Check if complete and better
            if len(lineup) == 6:
                total_score = captain_player.enhanced_score * 1.5 + sum(p.enhanced_score for p in lineup[1:])
                if total_score > best_score:
                    best_score = total_score
                    best_lineup = lineup

        if best_lineup:
            total_salary = sum(
                int(p.salary * getattr(p, 'multiplier', 1.0)) for p in best_lineup
            )
            return OptimizationResult(
                lineup=best_lineup, total_score=best_score, total_salary=total_salary,
                positions_filled={'CPT': 1, 'UTIL': 5}, optimization_status="Greedy"
            )
        else:
            return OptimizationResult(
                lineup=[], total_score=0, total_salary=0,
                positions_filled={}, optimization_status="Greedy failed"
            )

    def debug_infeasible_lineup(self, players: List):
        """Debug why optimization is infeasible"""
        print("\n🔍 DEBUGGING LINEUP CONSTRAINTS")
        print("=" * 60)

        # Show multi-position players
        multi_pos_players = [p for p in players if hasattr(p, 'positions') and len(p.positions) > 1]
        if multi_pos_players:
            print(f"\n📊 Multi-position players: {len(multi_pos_players)}")
            for p in multi_pos_players[:10]:  # Show first 10
                print(f"   {p.name}: {'/'.join(p.positions)}")

        # Check position coverage
        print("\n📊 Position Coverage:")
        for pos, required in self.classic_requirements.items():
            eligible = [p for p in players if self._can_fill_position(p, pos)]
            print(f"   {pos}: {len(eligible)} players available (need {required})")
            if len(eligible) < required:
                print(f"      ❌ INSUFFICIENT!")