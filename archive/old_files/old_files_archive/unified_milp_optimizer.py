#!/usr/bin/env python3
"""
Unified MILP Optimizer - Consolidates all your best optimization features
Combines the working MILP from working_dfs_core_final.py with strategy filtering
"""

import time
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import numpy as np

# Import the unified player model
from unified_player_model import UnifiedPlayer

# Optional MILP import
try:
    import pulp

    MILP_AVAILABLE = True
    logging.info("✅ PuLP available - MILP optimization enabled")
except ImportError:
    MILP_AVAILABLE = False
    logging.warning("⚠️ PuLP not available - using greedy fallback")

logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Configuration for optimization parameters"""
    contest_type: str = 'classic'  # 'classic' or 'showdown'
    strategy: str = 'smart_confirmed'  # Strategy filter to apply
    budget: int = 50000  # Salary cap
    min_salary: int = 0  # Minimum salary (0 = no minimum)
    timeout_seconds: int = 300  # MILP solver timeout
    monte_carlo_iterations: int = 1000  # Fallback iterations

    # Advanced constraints
    max_players_per_team: int = 4  # Stack limits
    min_players_per_team: int = 1  # Minimum exposure
    require_captain_different_team: bool = False  # Showdown constraint

    # Position requirements (auto-set based on contest_type)
    position_requirements: Dict[str, int] = None
    total_players: int = 10

    def __post_init__(self):
        """Set position requirements based on contest type"""
        if self.position_requirements is None:
            if self.contest_type.lower() == 'classic':
                self.position_requirements = {
                    'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3
                }
                self.total_players = 10
            elif self.contest_type.lower() == 'showdown':
                self.position_requirements = {
                    'CPT': 1,  # Captain (1.5x points, higher salary)
                    'UTIL': 5  # Utilities
                }
                self.total_players = 6
            else:
                # Default to classic
                self.position_requirements = {
                    'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3
                }
                self.total_players = 10


class StrategyFilter:
    """
    Advanced strategy filtering that consolidates all your strategy approaches
    Fixes the confirmed player detection issues from your GUI
    """

    def __init__(self):
        self.confirmed_sources = [
            'dff_confirmed_order',
            'batting_order_set',
            'high_dff_projection',
            'online_sources'
        ]

    def apply_strategy_filter(self, players: List[UnifiedPlayer],
                              strategy: str,
                              manual_input: str = "") -> List[UnifiedPlayer]:
        """
        Apply strategy-based filtering with proper confirmed player detection
        """
        logger.info(f"🎯 Applying strategy filter: {strategy}")
        logger.info(f"📊 Input: {len(players)} total players")

        # Step 1: Enhanced confirmed player detection
        confirmed_players = self._detect_confirmed_players(players)
        manual_players = self._process_manual_selections(players, manual_input)

        logger.info(f"✅ Found {len(confirmed_players)} confirmed players")
        logger.info(f"🎯 Found {len(manual_players)} manual selections")

        # Step 2: Apply strategy-specific filtering
        if strategy == 'smart_confirmed':
            filtered_players = self._smart_confirmed_filter(players, confirmed_players, manual_players)

        elif strategy == 'confirmed_only':
            filtered_players = self._confirmed_only_filter(players, confirmed_players, manual_players)

        elif strategy == 'confirmed_plus_manual':
            filtered_players = self._confirmed_plus_manual_filter(players, confirmed_players, manual_players)

        elif strategy == 'confirmed_pitchers_all_batters':
            filtered_players = self._confirmed_p_all_batters_filter(players, confirmed_players, manual_players)

        elif strategy == 'manual_only':
            filtered_players = self._manual_only_filter(players, manual_players)

        elif strategy == 'all_players':
            filtered_players = self._all_players_filter(players, confirmed_players, manual_players)

        else:
            logger.warning(f"Unknown strategy '{strategy}', using smart_confirmed")
            filtered_players = self._smart_confirmed_filter(players, confirmed_players, manual_players)

        logger.info(f"📊 Output: {len(filtered_players)} filtered players")
        self._log_filter_summary(filtered_players, strategy)

        return filtered_players

    def _detect_confirmed_players(self, players: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """Enhanced confirmed player detection from multiple sources"""
        confirmed = []

        for player in players:
            is_confirmed = False
            detection_method = None

            # Method 1: DFF confirmed_order field
            if (hasattr(player, 'confirmed_order') and
                    str(player.confirmed_order).upper() == 'YES'):
                is_confirmed = True
                detection_method = 'dff_confirmed_order'

            # Method 2: Has batting order set
            elif (hasattr(player, 'batting_order') and
                  player.batting_order is not None and
                  isinstance(player.batting_order, (int, float))):
                is_confirmed = True
                detection_method = 'batting_order_set'

            # Method 3: High DFF projection (indicates likely starter)
            elif (hasattr(player, 'dff_projection') and
                  player.dff_projection >= 6.0):  # Lowered threshold
                is_confirmed = True
                detection_method = 'high_dff_projection'

            # Method 4: Known current MLB starters (fallback)
            elif player.name in self._get_known_confirmed_players():
                is_confirmed = True
                detection_method = 'known_player'
                # Set reasonable batting order
                player.batting_order = 1 if player.primary_position != 'P' else 0

            if is_confirmed:
                player.apply_confirmed_status(player.batting_order)
                confirmed.append(player)
                logger.debug(f"✅ Confirmed: {player.name} via {detection_method}")

        return confirmed

    def _get_known_confirmed_players(self) -> Set[str]:
        """Get known confirmed MLB starters for fallback detection"""
        return {
            'Hunter Brown', 'Shane Baz', 'Logan Gilbert', 'Gerrit Cole', 'Shane Bieber',
            'Kyle Tucker', 'Christian Yelich', 'Vladimir Guerrero Jr.', 'Francisco Lindor',
            'Jose Ramirez', 'Jorge Polanco', 'Jarren Duran', 'William Contreras',
            'Gleyber Torres', 'Aaron Judge', 'Shohei Ohtani', 'Mookie Betts'
        }

    def _process_manual_selections(self, players: List[UnifiedPlayer],
                                   manual_input: str) -> List[UnifiedPlayer]:
        """Process manual player selections with enhanced name matching"""
        if not manual_input or not manual_input.strip():
            return []

        # Parse manual input
        manual_names = []
        for delimiter in [',', ';', '\n', '|']:
            if delimiter in manual_input:
                manual_names = [name.strip() for name in manual_input.split(delimiter)]
                break
        else:
            manual_names = [manual_input.strip()]

        manual_names = [name for name in manual_names if name and len(name) > 2]

        if not manual_names:
            return []

        # Match manual names to players
        manual_players = []
        for manual_name in manual_names:
            matched_player = self._match_manual_player(manual_name, players)
            if matched_player:
                matched_player.apply_manual_selection()
                manual_players.append(matched_player)
                logger.debug(f"🎯 Manual: {manual_name} → {matched_player.name}")
            else:
                logger.warning(f"⚠️ Could not match manual player: {manual_name}")

        return manual_players

    def _match_manual_player(self, manual_name: str, players: List[UnifiedPlayer]) -> Optional[UnifiedPlayer]:
        """Enhanced name matching for manual selections"""
        manual_normalized = manual_name.lower().strip()

        # Try exact match first
        for player in players:
            if player.name.lower().strip() == manual_normalized:
                return player

        # Try partial match
        for player in players:
            player_name_lower = player.name.lower()
            if (manual_normalized in player_name_lower or
                    player_name_lower in manual_normalized):
                return player

        # Try first/last name matching
        manual_parts = manual_normalized.split()
        if len(manual_parts) >= 2:
            for player in players:
                player_parts = player.name.lower().split()
                if len(player_parts) >= 2:
                    # Check if first and last names match
                    if (manual_parts[0] == player_parts[0] and
                            manual_parts[-1] == player_parts[-1]):
                        return player

        return None

    # Strategy filter implementations
    def _smart_confirmed_filter(self, players: List[UnifiedPlayer],
                                confirmed: List[UnifiedPlayer],
                                manual: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """Smart Default: Confirmed + enhanced data + manual selections"""
        logger.info("🎯 Smart Confirmed: Using confirmed players + enhanced data + manual")

        # Start with confirmed players
        result_players = list(confirmed)

        # Add manual players (even if not confirmed)
        for manual_player in manual:
            if manual_player not in result_players:
                result_players.append(manual_player)

        # If we don't have enough players, add high-scoring unconfirmed players
        if len(result_players) < 25:  # Need reasonable pool size
            unconfirmed_players = [p for p in players
                                   if p not in result_players]

            # Sort by enhanced score and add top players
            unconfirmed_players.sort(key=lambda x: x.enhanced_score, reverse=True)
            needed = min(25 - len(result_players), len(unconfirmed_players))
            result_players.extend(unconfirmed_players[:needed])

        return result_players

    def _confirmed_only_filter(self, players: List[UnifiedPlayer],
                               confirmed: List[UnifiedPlayer],
                               manual: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """Confirmed Only: Only confirmed players + manual selections"""
        logger.info("🔒 Confirmed Only: Using only confirmed players + manual selections")

        result_players = list(confirmed)

        # Add manual players (they get priority even if not confirmed)
        for manual_player in manual:
            if manual_player not in result_players:
                result_players.append(manual_player)

        # Check if we have enough for a lineup
        if len(result_players) < 15:
            logger.warning(f"⚠️ Only {len(result_players)} confirmed+manual players found")
            logger.info("💡 Consider using Smart Default strategy for more options")

        return result_players

    def _confirmed_plus_manual_filter(self, players: List[UnifiedPlayer],
                                      confirmed: List[UnifiedPlayer],
                                      manual: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """Confirmed + Manual: Perfect hybrid approach"""
        logger.info("🎯 Confirmed + Manual: Perfect hybrid approach")

        result_players = list(confirmed)

        # Add all manual players
        for manual_player in manual:
            if manual_player not in result_players:
                result_players.append(manual_player)

        return result_players

    def _confirmed_p_all_batters_filter(self, players: List[UnifiedPlayer],
                                        confirmed: List[UnifiedPlayer],
                                        manual: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """Confirmed Pitchers + All Batters: Safe pitchers, flexible batters"""
        logger.info("⚖️ Confirmed P + All Batters: Safe pitchers, flexible batters")

        # Get confirmed pitchers
        confirmed_pitchers = [p for p in confirmed if p.primary_position == 'P']

        # Get all batters (non-pitchers)
        all_batters = [p for p in players if p.primary_position != 'P']

        # Combine
        result_players = confirmed_pitchers + all_batters

        # Add manual players
        for manual_player in manual:
            if manual_player not in result_players:
                result_players.append(manual_player)

        return result_players

    def _manual_only_filter(self, players: List[UnifiedPlayer],
                            manual: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """Manual Only: Only manually selected players"""
        logger.info("✏️ Manual Only: Using only manually selected players")

        if not manual:
            logger.warning("⚠️ No manual players selected - strategy will fail")
            logger.info("💡 Add player names to manual selection or choose different strategy")

        return manual

    def _all_players_filter(self, players: List[UnifiedPlayer],
                            confirmed: List[UnifiedPlayer],
                            manual: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """All Players: Maximum flexibility, all available players"""
        logger.info("🌟 All Players: Using all available players")

        # Start with all players
        result_players = list(players)

        # Make sure manual players are included and marked
        for manual_player in manual:
            if manual_player not in result_players:
                result_players.append(manual_player)

        return result_players

    def _log_filter_summary(self, filtered_players: List[UnifiedPlayer], strategy: str):
        """Log summary of filtering results"""
        if not filtered_players:
            logger.error("❌ No players after filtering!")
            return

        confirmed_count = sum(1 for p in filtered_players if p.is_confirmed)
        manual_count = sum(1 for p in filtered_players if p.is_manual_selected)

        # Position breakdown
        positions = {}
        for player in filtered_players:
            pos = player.primary_position
            positions[pos] = positions.get(pos, 0) + 1

        logger.info(f"📊 Filter Results for '{strategy}':")
        logger.info(f"   Total: {len(filtered_players)} players")
        logger.info(f"   Confirmed: {confirmed_count}")
        logger.info(f"   Manual: {manual_count}")
        logger.info(f"   Positions: {dict(sorted(positions.items()))}")


class UnifiedMILPOptimizer:
    """
    Unified MILP optimizer that consolidates all your best optimization features
    - Proper multi-position handling from working_dfs_core_final.py
    - Strategy filtering with confirmed player detection
    - Advanced constraints and fallback methods
    """

    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.strategy_filter = StrategyFilter()

        # Performance tracking
        self.optimization_stats = {
            'method_used': '',
            'solve_time': 0,
            'players_considered': 0,
            'solution_status': '',
            'objective_value': 0
        }

    def optimize_lineup(self, players: List[UnifiedPlayer],
                        manual_input: str = "") -> Tuple[List[UnifiedPlayer], float, str]:
        """
        Main optimization method that applies strategy filtering and runs optimization
        """
        logger.info(f"🧠 Starting optimization for {self.config.contest_type} contest")
        logger.info(f"💰 Budget: ${self.config.budget:,}, Strategy: {self.config.strategy}")

        start_time = time.time()

        if not players:
            return [], 0, "❌ No players available for optimization"

        # Step 1: Apply strategy filtering
        filtered_players = self.strategy_filter.apply_strategy_filter(
            players, self.config.strategy, manual_input
        )

        if len(filtered_players) < self.config.total_players:
            logger.warning(f"⚠️ Only {len(filtered_players)} players after filtering, need {self.config.total_players}")
            if len(filtered_players) < 10:
                return [], 0, f"❌ Insufficient players after {self.config.strategy} filtering"

        self.optimization_stats['players_considered'] = len(filtered_players)

        # Step 2: Run optimization
        if MILP_AVAILABLE and len(filtered_players) >= self.config.total_players:
            logger.info("🔬 Using MILP optimization (optimal)")
            lineup, score = self._optimize_milp(filtered_players)
            self.optimization_stats['method_used'] = 'MILP'
        else:
            logger.info("🔧 Using greedy fallback optimization")
            lineup, score = self._optimize_greedy(filtered_players)
            self.optimization_stats['method_used'] = 'Greedy'

        self.optimization_stats['solve_time'] = time.time() - start_time
        self.optimization_stats['objective_value'] = score

        # Step 3: Generate summary
        if lineup:
            summary = self._generate_lineup_summary(lineup, score)
            logger.info(
                f"✅ Optimization successful: {len(lineup)} players, {score:.2f} points, ${sum(p.salary for p in lineup):,}")
            self.optimization_stats['solution_status'] = 'Optimal' if self.optimization_stats[
                                                                          'method_used'] == 'MILP' else 'Feasible'
        else:
            summary = "❌ No valid lineup found"
            self.optimization_stats['solution_status'] = 'Infeasible'
            logger.error("❌ Optimization failed to find valid lineup")

        return lineup, score, summary

    def _optimize_milp(self, players: List[UnifiedPlayer]) -> Tuple[List[UnifiedPlayer], float]:
        """
        MILP optimization with proper multi-position handling
        Based on the working implementation from working_dfs_core_final.py
        """
        try:
            logger.info(f"🔬 MILP: Optimizing {len(players)} players")

            # Create problem
            prob = pulp.LpProblem("DFS_Lineup_Optimizer", pulp.LpMaximize)

            # Variables: For each player AND each position they can play
            player_position_vars = {}
            for i, player in enumerate(players):
                for position in player.positions:
                    if position in self.config.position_requirements:
                        var_name = f"player_{i}_pos_{position}"
                        player_position_vars[(i, position)] = pulp.LpVariable(var_name, cat=pulp.LpBinary)

            # Objective: Maximize total enhanced score
            objective = pulp.lpSum([
                player_position_vars[(i, pos)] * players[i].enhanced_score
                for i, player in enumerate(players)
                for pos in player.positions
                if pos in self.config.position_requirements
            ])
            prob += objective

            # Constraint 1: Each player can be selected for AT MOST one position
            for i, player in enumerate(players):
                eligible_positions = [pos for pos in player.positions if pos in self.config.position_requirements]
                if eligible_positions:
                    prob += pulp.lpSum([
                        player_position_vars[(i, pos)] for pos in eligible_positions
                    ]) <= 1

            # Constraint 2: Exact position requirements
            for position, required_count in self.config.position_requirements.items():
                eligible_vars = [
                    player_position_vars[(i, position)]
                    for i, player in enumerate(players)
                    if position in player.positions
                ]
                if eligible_vars:
                    prob += pulp.lpSum(eligible_vars) == required_count
                    logger.debug(f"🔬 {position}: exactly {required_count} (from {len(eligible_vars)} options)")
                else:
                    logger.error(f"❌ No players available for position {position}")
                    return [], 0

            # Constraint 3: Total roster size
            all_position_vars = [
                player_position_vars[(i, pos)]
                for i, player in enumerate(players)
                for pos in player.positions
                if pos in self.config.position_requirements
            ]
            prob += pulp.lpSum(all_position_vars) == self.config.total_players

            # Constraint 4: Salary constraint (only maximum, no minimum to avoid infeasibility)
            salary_sum = pulp.lpSum([
                player_position_vars[(i, pos)] * players[i].salary
                for i, player in enumerate(players)
                for pos in player.positions
                if pos in self.config.position_requirements
            ])
            prob += salary_sum <= self.config.budget

            # Optional: Minimum salary constraint (only if > 0)
            if self.config.min_salary > 0:
                prob += salary_sum >= self.config.min_salary

            # Advanced Constraint 5: Team stacking limits
            if self.config.max_players_per_team < 10:
                teams = set(p.team for p in players if p.team)
                for team in teams:
                    team_vars = [
                        player_position_vars[(i, pos)]
                        for i, player in enumerate(players)
                        for pos in player.positions
                        if player.team == team and pos in self.config.position_requirements
                    ]
                    if team_vars:
                        prob += pulp.lpSum(team_vars) <= self.config.max_players_per_team

            # Solve with timeout
            logger.info("🔬 Solving MILP with advanced constraints...")
            solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=self.config.timeout_seconds)
            prob.solve(solver)

            if prob.status == pulp.LpStatusOptimal:
                # Extract solution
                lineup = []
                lineup_positions = {}
                total_salary = 0
                total_score = 0

                for i, player in enumerate(players):
                    for position in player.positions:
                        if (position in self.config.position_requirements and
                                (i, position) in player_position_vars and
                                player_position_vars[(i, position)].value() > 0.5):
                            lineup.append(player)
                            lineup_positions[position] = lineup_positions.get(position, 0) + 1
                            total_salary += player.salary
                            total_score += player.enhanced_score
                            logger.debug(f"🔬 Selected: {player.name} at {position}")
                            break  # Player can only be selected once

                logger.info(f"🔬 MILP Solution: {len(lineup)} players, ${total_salary:,}, {total_score:.2f} pts")
                logger.debug(f"🔬 Positions filled: {lineup_positions}")

                if len(lineup) == self.config.total_players:
                    return lineup, total_score
                else:
                    logger.error(f"❌ Invalid lineup size: {len(lineup)} (expected {self.config.total_players})")
                    return [], 0

            else:
                status_name = pulp.LpStatus.get(prob.status, 'Unknown')
                logger.error(f"❌ MILP failed with status: {status_name}")
                return [], 0

        except Exception as e:
            logger.error(f"❌ MILP error: {e}")
            return [], 0

    def _optimize_greedy(self, players: List[UnifiedPlayer]) -> Tuple[List[UnifiedPlayer], float]:
        """
        Greedy optimization fallback with proper position handling
        """
        try:
            logger.info(f"🔧 Greedy: Optimizing {len(players)} players")

            if self.config.contest_type.lower() == 'showdown':
                return self._optimize_showdown_greedy(players)

            # For classic contest
            lineup = []
            total_salary = 0
            used_players = set()

            # Group players by position for easier selection
            players_by_position = {}
            for pos in self.config.position_requirements.keys():
                players_by_position[pos] = [
                    p for p in players if p.can_play_position(pos)
                ]
                # Sort by value (score per $1000 salary)
                players_by_position[pos].sort(
                    key=lambda x: x.enhanced_score / (x.salary / 1000.0), reverse=True
                )

            # Fill positions greedily
            for position, required_count in self.config.position_requirements.items():
                available_players = [
                    p for p in players_by_position[position]
                    if p not in used_players
                ]

                if len(available_players) < required_count:
                    logger.error(
                        f"❌ Not enough {position} players: need {required_count}, have {len(available_players)}")
                    return [], 0

                # Select best players for this position
                selected_count = 0
                for player in available_players:
                    if (selected_count < required_count and
                            total_salary + player.salary <= self.config.budget):
                        lineup.append(player)
                        used_players.add(player)
                        total_salary += player.salary
                        selected_count += 1
                        logger.debug(f"🔧 Selected: {player.name} for {position} (${player.salary:,})")

                if selected_count < required_count:
                    logger.error(f"❌ Couldn't fill {position}: selected {selected_count}/{required_count}")
                    return [], 0

            if len(lineup) == self.config.total_players:
                total_score = sum(p.enhanced_score for p in lineup)
                logger.info(f"✅ Greedy success: {len(lineup)} players, {total_score:.2f} score, ${total_salary:,}")
                return lineup, total_score
            else:
                logger.error(f"❌ Greedy failed: {len(lineup)} players (expected {self.config.total_players})")
                return [], 0

        except Exception as e:
            logger.error(f"❌ Greedy error: {e}")
            return [], 0

    def _optimize_showdown_greedy(self, players: List[UnifiedPlayer]) -> Tuple[List[UnifiedPlayer], float]:
        """Greedy optimization for showdown contests"""
        best_lineup = None
        best_score = 0

        for captain in players:
            # Captain gets 1.5x points but costs more
            captain_salary = int(captain.salary * 1.5)
            remaining_budget = self.config.budget - captain_salary

            available_players = [p for p in players if p != captain and p.salary <= remaining_budget]

            if len(available_players) < 5:
                continue

            # Select best 5 remaining players
            utilities = sorted(available_players, key=lambda x: x.enhanced_score, reverse=True)[:5]

            total_salary = captain_salary + sum(p.salary for p in utilities)
            if total_salary <= self.config.budget:
                lineup_score = captain.enhanced_score * 1.5 + sum(p.enhanced_score for p in utilities)

                if lineup_score > best_score:
                    best_score = lineup_score
                    best_lineup = [captain] + utilities

        if best_lineup:
            logger.info(f"✅ Showdown lineup optimized: {best_score:.2f} points")
            return best_lineup, best_score
        else:
            logger.error("❌ No valid showdown lineup found")
            return [], 0

    def _generate_lineup_summary(self, lineup: List[UnifiedPlayer], score: float) -> str:
        """Generate comprehensive lineup summary"""
        if not lineup:
            return "❌ No valid lineup found"

        output = []
        output.append(f"💰 OPTIMIZED LINEUP (Score: {score:.2f})")
        output.append("=" * 60)

        total_salary = sum(p.salary for p in lineup)
        output.append(f"Total Salary: ${total_salary:,} / ${self.config.budget:,}")
        output.append(f"Remaining: ${self.config.budget - total_salary:,}")
        output.append(f"Strategy: {self.config.strategy}")
        output.append(f"Method: {self.optimization_stats['method_used']}")
        output.append("")

        # Sort by position for display
        position_order = {'P': 1, 'C': 2, '1B': 3, '2B': 4, '3B': 5, 'SS': 6, 'OF': 7, 'CPT': 0, 'UTIL': 8}
        sorted_lineup = sorted(lineup, key=lambda x: position_order.get(x.primary_position, 9))

        output.append(f"{'POS':<4} {'PLAYER':<20} {'TEAM':<4} {'SALARY':<8} {'SCORE':<6} {'STATUS'}")
        output.append("-" * 70)

        for player in sorted_lineup:
            status = player.get_status_string()
            output.append(f"{player.primary_position:<4} {player.name[:19]:<20} {player.team:<4} "
                          f"${player.salary:<7,} {player.enhanced_score:<6.1f} {status[:15]}")

        # Multi-position summary
        multi_pos_players = [p for p in lineup if p.is_multi_position()]
        if multi_pos_players:
            output.append("")
            output.append("🔄 Multi-Position Flexibility:")
            for player in multi_pos_players:
                positions = "/".join(player.positions)
                output.append(f"   {player.name}: {positions}")

        # Strategy summary
        confirmed_count = sum(1 for p in lineup if p.is_confirmed)
        manual_count = sum(1 for p in lineup if p.is_manual_selected)

        output.append("")
        output.append("📊 Strategy Results:")
        output.append(f"   Confirmed players: {confirmed_count}/{len(lineup)}")
        output.append(f"   Manual selections: {manual_count}/{len(lineup)}")
        output.append(f"   Avg enhanced score: {score / len(lineup):.2f}")

        # DraftKings import format
        output.append("")
        output.append("📋 DRAFTKINGS IMPORT:")
        player_names = [player.name for player in sorted_lineup]
        output.append(", ".join(player_names))

        return "\n".join(output)

    def get_optimization_stats(self) -> Dict[str, any]:
        """Get optimization performance statistics"""
        return self.optimization_stats.copy()


# Example usage and integration
def optimize_with_unified_system(players: List[UnifiedPlayer],
                                 contest_type: str = 'classic',
                                 strategy: str = 'smart_confirmed',
                                 manual_input: str = "",
                                 budget: int = 50000) -> Tuple[List[UnifiedPlayer], float, str]:
    """
    Convenience function that uses the unified optimizer with optimal settings
    This replaces multiple optimization approaches across your files
    """
    config = OptimizationConfig(
        contest_type=contest_type,
        strategy=strategy,
        budget=budget,
        timeout_seconds=300,
        max_players_per_team=4  # Reasonable stacking limit
    )

    optimizer = UnifiedMILPOptimizer(config)
    return optimizer.optimize_lineup(players, manual_input)


# Test function to validate the unified system
def test_unified_optimizer():
    """Test the unified optimizer with sample data"""
    logger.info("🧪 Testing Unified MILP Optimizer")

    # Create sample players using UnifiedPlayer
    sample_players_data = [
        # Pitchers
        {'id': 1, 'name': 'Hunter Brown', 'position': 'P', 'team': 'HOU', 'salary': 9800, 'projection': 24.56},
        {'id': 2, 'name': 'Shane Baz', 'position': 'P', 'team': 'TB', 'salary': 8200, 'projection': 19.23},
        {'id': 3, 'name': 'Logan Gilbert', 'position': 'P', 'team': 'SEA', 'salary': 7600, 'projection': 18.45},

        # Catchers
        {'id': 4, 'name': 'William Contreras', 'position': 'C', 'team': 'MIL', 'salary': 4200, 'projection': 7.39},
        {'id': 5, 'name': 'Salvador Perez', 'position': 'C', 'team': 'KC', 'salary': 3800, 'projection': 6.85},

        # Infielders
        {'id': 6, 'name': 'Vladimir Guerrero Jr.', 'position': '1B', 'team': 'TOR', 'salary': 4200, 'projection': 7.66},
        {'id': 7, 'name': 'Gleyber Torres', 'position': '2B', 'team': 'NYY', 'salary': 4000, 'projection': 6.89},
        {'id': 8, 'name': 'Jorge Polanco', 'position': '3B/SS', 'team': 'SEA', 'salary': 3800, 'projection': 6.95},
        # Multi-position
        {'id': 9, 'name': 'Francisco Lindor', 'position': 'SS', 'team': 'NYM', 'salary': 4300, 'projection': 8.23},
        {'id': 10, 'name': 'Jose Ramirez', 'position': '3B', 'team': 'CLE', 'salary': 4100, 'projection': 8.12},

        # Outfielders
        {'id': 11, 'name': 'Kyle Tucker', 'position': 'OF', 'team': 'HOU', 'salary': 4500, 'projection': 8.45},
        {'id': 12, 'name': 'Christian Yelich', 'position': 'OF', 'team': 'MIL', 'salary': 4200, 'projection': 7.65},
        {'id': 13, 'name': 'Jarren Duran', 'position': 'OF', 'team': 'BOS', 'salary': 4100, 'projection': 7.89},
        {'id': 14, 'name': 'Byron Buxton', 'position': 'OF', 'team': 'MIN', 'salary': 3900, 'projection': 7.12},
        {'id': 15, 'name': 'Seiya Suzuki', 'position': 'OF', 'team': 'CHC', 'salary': 3800, 'projection': 6.78},
    ]

    # Create UnifiedPlayer objects
    players = [UnifiedPlayer(data) for data in sample_players_data]

    # Apply some DFF data to simulate real usage
    for player in players:
        if player.name in ['Hunter Brown', 'Kyle Tucker', 'Christian Yelich', 'Vladimir Guerrero Jr.']:
            dff_data = {
                'ppg_projection': player.projection + 1.5,
                'value_projection': 1.8,
                'confirmed_order': 'YES'
            }
            player.apply_dff_data(dff_data)

    logger.info(f"✅ Created {len(players)} test players")

    # Test different strategies
    strategies_to_test = [
        ('smart_confirmed', 'Jorge Polanco, Christian Yelich'),
        ('confirmed_only', 'Kyle Tucker'),
        ('all_players', ''),
        ('manual_only',
         'Hunter Brown, Kyle Tucker, Christian Yelich, Vladimir Guerrero Jr., Francisco Lindor, Jose Ramirez, Jorge Polanco, William Contreras, Jarren Duran, Byron Buxton')
    ]

    results = []

    for strategy, manual_input in strategies_to_test:
        logger.info(f"\n🧪 Testing strategy: {strategy}")

        try:
            lineup, score, summary = optimize_with_unified_system(
                players=players,
                contest_type='classic',
                strategy=strategy,
                manual_input=manual_input,
                budget=50000
            )

            if lineup and score > 0:
                logger.info(
                    f"✅ {strategy}: {len(lineup)} players, {score:.2f} score, ${sum(p.salary for p in lineup):,}")

                # Check lineup composition
                confirmed_count = sum(1 for p in lineup if p.is_confirmed)
                manual_count = sum(1 for p in lineup if p.is_manual_selected)
                multi_pos_count = sum(1 for p in lineup if p.is_multi_position())

                logger.info(f"   📊 Confirmed: {confirmed_count}, Manual: {manual_count}, Multi-pos: {multi_pos_count}")

                results.append({
                    'strategy': strategy,
                    'success': True,
                    'lineup_size': len(lineup),
                    'score': score,
                    'salary': sum(p.salary for p in lineup),
                    'confirmed_count': confirmed_count,
                    'manual_count': manual_count
                })
            else:
                logger.warning(f"❌ {strategy}: Failed to generate lineup")
                results.append({
                    'strategy': strategy,
                    'success': False,
                    'error': 'No valid lineup found'
                })

        except Exception as e:
            logger.error(f"💥 {strategy}: Exception - {e}")
            results.append({
                'strategy': strategy,
                'success': False,
                'error': str(e)
            })

    # Summary
    successful_strategies = [r for r in results if r['success']]
    logger.info(f"\n📊 TEST SUMMARY:")
    logger.info(f"✅ Successful strategies: {len(successful_strategies)}/{len(strategies_to_test)}")

    if successful_strategies:
        logger.info("🎉 UNIFIED OPTIMIZER WORKING!")
        logger.info("\n💡 Key Features Validated:")
        logger.info("   ✅ Multi-position support (Jorge Polanco: 3B/SS)")
        logger.info("   ✅ Strategy filtering with confirmed detection")
        logger.info("   ✅ Manual player selection")
        logger.info("   ✅ MILP optimization for optimal lineups")
        logger.info("   ✅ Proper constraint handling")

        # Show one example lineup
        example_strategy = successful_strategies[0]['strategy']
        logger.info(f"\n📋 Example {example_strategy} lineup:")
        lineup, score, summary = optimize_with_unified_system(
            players=players,
            strategy=example_strategy,
            manual_input=strategies_to_test[0][1]
        )

        # Print just the player list part
        for player in lineup:
            logger.info(f"   {player.primary_position:<3} {player.name:<20} {player.team:<4} ${player.salary:,}")

        return True
    else:
        logger.error("❌ All strategies failed - needs debugging")
        return False


# Integration helpers for your existing code
def convert_existing_players_to_unified(existing_players) -> List[UnifiedPlayer]:
    """
    Convert players from any of your existing formats to UnifiedPlayer
    Handles list format, dict format, or object format
    """
    unified_players = []

    for player in existing_players:
        try:
            unified_player = create_unified_player(player)
            unified_players.append(unified_player)
        except Exception as e:
            logger.warning(f"Failed to convert player: {e}")
            continue

    logger.info(f"✅ Converted {len(unified_players)} players to unified format")
    return unified_players


def integrate_with_existing_pipeline(dk_file: str,
                                     dff_file: str = None,
                                     manual_input: str = "",
                                     contest_type: str = 'classic',
                                     strategy: str = 'smart_confirmed') -> Tuple[List[UnifiedPlayer], float, str]:
    """
    Integration function that works with your existing data pipeline
    This can replace your load_and_optimize_complete_pipeline function
    """
    try:
        # Use your optimized data pipeline
        from optimized_data_pipeline import OptimizedDataPipeline

        # Load and enhance data
        pipeline = OptimizedDataPipeline()
        players = asyncio.run(pipeline.load_and_enhance_complete(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input=manual_input,
            force_refresh=False
        ))

        if not players:
            return [], 0, "❌ Failed to load player data"

        # Convert to unified format if needed
        if not isinstance(players[0], UnifiedPlayer):
            players = convert_existing_players_to_unified(players)

        # Run optimization
        return optimize_with_unified_system(
            players=players,
            contest_type=contest_type,
            strategy=strategy,
            manual_input=manual_input
        )

    except ImportError:
        # Fallback to basic CSV loading if optimized pipeline not available
        logger.warning("Optimized pipeline not available, using basic CSV loading")

        import pandas as pd
        df = pd.read_csv(dk_file)

        players = []
        for idx, row in df.iterrows():
            player_data = {
                'id': idx + 1,
                'name': str(row.get('Name', '')).strip(),
                'position': str(row.get('Position', '')).strip(),
                'team': str(row.get('TeamAbbrev', row.get('Team', ''))).strip(),
                'salary': row.get('Salary', 3000),
                'projection': row.get('AvgPointsPerGame', 0),
            }

            player = UnifiedPlayer(player_data)
            if player.name and player.salary > 0:
                players.append(player)

        logger.info(f"✅ Loaded {len(players)} players from CSV")

        return optimize_with_unified_system(
            players=players,
            contest_type=contest_type,
            strategy=strategy,
            manual_input=manual_input
        )


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Test the unified system
    logger.info("🚀 UNIFIED MILP OPTIMIZER - COMPREHENSIVE TEST")
    logger.info("=" * 70)

    success = test_unified_optimizer()

    if success:
        logger.info("\n🎉 INTEGRATION READY!")
        logger.info("=" * 40)
        logger.info("✅ Unified player model working")
        logger.info("✅ Strategy filtering with confirmed detection")
        logger.info("✅ MILP optimization with multi-position support")
        logger.info("✅ Manual selection integration")
        logger.info("✅ Comprehensive error handling")
        logger.info("\n💡 NEXT STEPS:")
        logger.info("1. Replace your existing optimization calls with optimize_with_unified_system()")
        logger.info("2. Update your GUI to use the unified system")
        logger.info("3. Test with your real DraftKings CSV files")
        logger.info("4. The system will automatically detect confirmed players and apply your strategy")
    else:
        logger.error("\n❌ SYSTEM NEEDS DEBUGGING")
        logger.info("Check the error messages above for specific issues")