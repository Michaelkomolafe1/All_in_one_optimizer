#!/usr/bin/env python3
"""
OPTIMAL LINEUP OPTIMIZER - FIXED VERSION
=======================================
✅ Fixed position constraints to enforce EXACT requirements
✅ Proper multi-position player handling
✅ No more 3 pitchers or duplicate positions!
"""

import logging
from dataclasses import dataclass
from typing import Dict, List

import pulp

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
        """Safe showdown MILP optimization with proper duplicate handling"""

        # First, handle the duplicate player issue properly
        # Group players by name to identify captain/utility pairs
        name_groups = {}
        for player in players:
            name_key = player.name.lower().strip()
            if name_key not in name_groups:
                name_groups[name_key] = []
            name_groups[name_key].append(player)

        # Create a clean player list with indices
        player_indices = []
        player_list = []
        idx = 0

        for name, group in name_groups.items():
            if len(group) == 2:
                # Assume higher salary is captain version
                group.sort(key=lambda p: p.salary, reverse=True)
                captain_version = group[0]
                util_version = group[1]

                # Add both versions with proper indexing
                player_indices.append({
                    'captain_idx': idx,
                    'util_idx': idx + 1,
                    'name': name
                })
                player_list.extend([captain_version, util_version])
                idx += 2
            else:
                # Single version - can be used as either
                player_indices.append({
                    'captain_idx': idx,
                    'util_idx': idx,
                    'name': name
                })
                player_list.append(group[0])
                idx += 1

        print(f"🎯 Optimizing with {len(name_groups)} unique players")

        # Create problem
        prob = pulp.LpProblem("DFS_Showdown_Fixed", pulp.LpMaximize)

        # Decision variables - one for each player as captain or utility
        x = {}  # x[i,role] = 1 if player i is selected for role (0=captain, 1=utility)

        for i in range(len(player_list)):
            x[i, 0] = pulp.LpVariable(f"captain_{i}", cat='Binary')  # As captain
            x[i, 1] = pulp.LpVariable(f"util_{i}", cat='Binary')  # As utility

        # Objective: Maximize total score (captain gets 1.5x)
        prob += pulp.lpSum([
            x[i, 0] * player_list[i].enhanced_score * 1.5 +  # Captain score
            x[i, 1] * player_list[i].enhanced_score  # Utility score
            for i in range(len(player_list))
        ])

        # Constraint 1: Exactly 1 captain
        prob += pulp.lpSum([x[i, 0] for i in range(len(player_list))]) == 1

        # Constraint 2: Exactly 5 utility players
        prob += pulp.lpSum([x[i, 1] for i in range(len(player_list))]) == 5

        # Constraint 3: Each unique player can only be selected once (as captain OR utility)
        for player_info in player_indices:
            if player_info['captain_idx'] == player_info['util_idx']:
                # Same index means only one version exists
                idx = player_info['captain_idx']
                prob += x[idx, 0] + x[idx, 1] <= 1
            else:
                # Different indices mean we have both versions
                cap_idx = player_info['captain_idx']
                util_idx = player_info['util_idx']
                # Can only select one version total
                prob += x[cap_idx, 0] + x[util_idx, 1] <= 1
                # Can't select captain version as utility or vice versa
                prob += x[cap_idx, 1] == 0
                prob += x[util_idx, 0] == 0

        # Constraint 4: Salary cap (captain costs 1.5x)
        prob += pulp.lpSum([
            x[i, 0] * player_list[i].salary * 1.5 +  # Captain salary
            x[i, 1] * player_list[i].salary  # Utility salary
            for i in range(len(player_list))
        ]) <= self.salary_cap

        # Constraint 5: Must have players from both teams
        teams = list(set(p.team for p in player_list))
        if len(teams) >= 2:
            for team in teams[:2]:
                team_indices = [i for i, p in enumerate(player_list) if p.team == team]
                if team_indices:
                    prob += pulp.lpSum([
                        x[i, 0] + x[i, 1] for i in team_indices
                    ]) >= 1

        # Solve
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=30)
        prob.solve(solver)

        if prob.status == pulp.LpStatusOptimal:
            return self._extract_showdown_solution_fixed(player_list, x)
        else:
            print(f"❌ MILP failed: {pulp.LpStatus[prob.status]}")
            return self._greedy_showdown_fallback(players)

    def _extract_showdown_solution_fixed(self, player_list: List, x: Dict) -> OptimizationResult:
        """Extract solution from fixed showdown optimization"""
        lineup = []
        total_salary = 0
        total_score = 0
        positions_filled = {'CPT': 0, 'UTIL': 0}

        # Extract selected players
        for i in range(len(player_list)):
            # Check if selected as captain
            if x[i, 0].value() == 1:
                player_copy = self._copy_player(player_list[i])
                player_copy.assigned_position = 'CPT'
                player_copy.multiplier = 1.5
                player_copy.captain_salary = int(player_list[i].salary * 1.5)
                player_copy.captain_score = player_list[i].enhanced_score * 1.5  # ADD THIS
                lineup.append(player_copy)
                total_salary += player_copy.captain_salary
                total_score += player_copy.captain_score  # USE CAPTAIN SCORE
                positions_filled['CPT'] = 1
                print(
                    f"✅ Captain: {player_copy.name} - ${player_copy.captain_salary:,} - {player_copy.captain_score:.1f} pts")

            # Check if selected as utility
            elif x[i, 1].value() == 1:
                player_copy = self._copy_player(player_list[i])
                player_copy.assigned_position = 'UTIL'
                player_copy.multiplier = 1.0
                lineup.append(player_copy)
                total_salary += player_list[i].salary
                total_score += player_list[i].enhanced_score
                positions_filled['UTIL'] += 1
                print(
                    f"✅ Utility: {player_copy.name} - ${player_list[i].salary:,} - {player_list[i].enhanced_score:.1f} pts")

        # Sort lineup: Captain first, then utilities
        lineup.sort(key=lambda p: 0 if p.assigned_position == 'CPT' else 1)

        return OptimizationResult(
            lineup=lineup,
            total_score=total_score,
            total_salary=total_salary,
            positions_filled=positions_filled,
            optimization_status="Optimal"
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
        """Greedy fallback for showdown lineup with proper duplicate handling"""
        print("🔄 Using greedy showdown fallback...")

        # Group players by name to handle duplicates
        name_groups = {}
        for player in players:
            name_key = player.name.lower().strip()
            if name_key not in name_groups:
                name_groups[name_key] = []
            name_groups[name_key].append(player)

        # Create unique player list
        unique_players = []
        for name, group in name_groups.items():
            if len(group) == 1:
                unique_players.append(group[0])
            else:
                # Pick the one with better value for our pool
                best_player = max(group, key=lambda p: p.enhanced_score / (p.salary / 1000) if p.salary > 0 else 0)
                unique_players.append(best_player)

        # Sort by value
        players_with_value = [(p, p.enhanced_score / (p.salary / 1000)) for p in unique_players if p.salary > 0]
        players_with_value.sort(key=lambda x: x[1], reverse=True)

        best_lineup = None
        best_score = 0

        # Try each player as captain
        for captain_idx, (captain_player, _) in enumerate(players_with_value[:20]):
            if captain_player.salary * 1.5 > self.salary_cap:
                continue

            lineup = []
            remaining_salary = self.salary_cap
            used_names = set()

            # Add captain
            captain_copy = self._copy_player(captain_player)
            captain_copy.assigned_position = 'CPT'
            captain_copy.multiplier = 1.5
            captain_copy.captain_salary = int(captain_player.salary * 1.5)
            lineup.append(captain_copy)
            remaining_salary -= captain_copy.captain_salary
            used_names.add(captain_player.name.lower().strip())

            # Add 5 best utility players that fit
            for player, value in players_with_value:
                if len(lineup) >= 6:
                    break

                player_name = player.name.lower().strip()

                # Skip if already used (as captain or utility)
                if player_name in used_names:
                    continue

                # Skip if doesn't fit salary
                if player.salary > remaining_salary:
                    continue

                # Add as utility
                util_copy = self._copy_player(player)
                util_copy.assigned_position = 'UTIL'
                util_copy.multiplier = 1.0
                lineup.append(util_copy)
                remaining_salary -= player.salary
                used_names.add(player_name)

            # Check if complete and better
            if len(lineup) == 6:
                total_score = captain_player.enhanced_score * 1.5 + sum(p.enhanced_score for p in lineup[1:])
                if total_score > best_score:
                    best_score = total_score
                    best_lineup = lineup[:]

        if best_lineup:
            # Calculate actual total salary
            total_salary = 0
            for player in best_lineup:
                if player.assigned_position == 'CPT':
                    total_salary += int(player.salary * 1.5)
                else:
                    total_salary += player.salary

            return OptimizationResult(
                lineup=best_lineup,
                total_score=best_score,
                total_salary=total_salary,
                positions_filled={'CPT': 1, 'UTIL': 5},
                optimization_status="Greedy"
            )
        else:
            return OptimizationResult(
                lineup=[],
                total_score=0,
                total_salary=0,
                positions_filled={},
                optimization_status="Greedy failed - could not build valid lineup"
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
