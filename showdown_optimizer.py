#!/usr/bin/env python3
"""
Showdown Optimizer for DFS
=========================
Handles the special case of DK Showdown slates with CPT/UTIL entries
"""

import logging
from typing import List, Dict, Tuple, Optional
import pulp

logger = logging.getLogger(__name__)


class ShowdownOptimizer:
    """
    Specialized optimizer for DraftKings Showdown contests

    Key Features:
    - Handles CPT/UTIL duplicate entries
    - Uses ONLY UTIL entries as base
    - Applies 1.5x multiplier in MILP for captain
    - Ensures exactly 1 captain + 5 utilities
    """

    def __init__(self, salary_cap: int = 50000):
        self.salary_cap = salary_cap
        self.captain_multiplier = 1.5
        self.lineup_size = 6  # 1 CPT + 5 UTIL

    def prepare_showdown_pool(self, players: List) -> List:
        """
        Filter to UTIL entries only and prepare for showdown

        DK CSV format has:
        - Player Name (CPT) at 1.5x salary
        - Player Name (UTIL) at 1.0x salary

        We use ONLY the UTIL entries!
        """
        util_players = []
        seen_names = set()

        for player in players:
            # Skip CPT entries - they have "(CPT)" in display name
            if "(CPT)" in getattr(player, 'Name', '') or \
                    "CPT" in getattr(player, 'roster_position', ''):
                logger.debug(f"Skipping CPT entry: {player.name}")
                continue

            # Also check if this is a duplicate (same player, higher salary)
            player_key = f"{player.name}_{player.team}"
            if player_key not in seen_names:
                seen_names.add(player_key)
                util_players.append(player)
                logger.debug(f"Added UTIL player: {player.name} ${player.salary}")
            else:
                # If we see the same player again, keep the cheaper one (UTIL)
                for i, existing in enumerate(util_players):
                    if existing.name == player.name and existing.team == player.team:
                        if player.salary < existing.salary:
                            util_players[i] = player
                            logger.debug(f"Replaced with cheaper: {player.name} ${player.salary}")

        logger.info(f"Showdown pool: {len(util_players)} UTIL players from {len(players)} total")

        # Set showdown flag on all players
        for player in util_players:
            player.is_showdown = True
            player.util_salary = player.salary  # Store original UTIL salary

        return util_players

    def optimize_showdown(
            self,
            players: List,
            num_lineups: int = 1,
            min_salary_usage: float = 0.95,
            diversity_factor: float = 0.15
    ) -> List[Dict]:
        """
        Optimize showdown lineups using MILP

        Returns list of lineups with format:
        {
            'captain': player_object,
            'utilities': [player1, player2, ...],
            'total_salary': int,
            'total_score': float
        }
        """
        # Prepare player pool (UTIL only)
        util_players = self.prepare_showdown_pool(players)

        if len(util_players) < 6:
            logger.error(f"Not enough players for showdown: {len(util_players)} < 6")
            return []

        lineups = []
        used_captains = set()

        for lineup_num in range(num_lineups):
            # Run MILP optimization
            lineup = self._optimize_single_showdown(
                util_players,
                used_captains,
                min_salary_usage
            )

            if lineup:
                lineups.append(lineup)
                # Track captain for diversity
                if lineup['captain']:
                    used_captains.add(lineup['captain'].name)

                    # Apply diversity penalty for next lineup
                    if diversity_factor > 0 and lineup_num < num_lineups - 1:
                        for player in util_players:
                            if player.name in used_captains:
                                player.temp_score = getattr(player, 'optimization_score', 0)
                                player.optimization_score *= (1 - diversity_factor)
            else:
                logger.warning(f"Failed to generate lineup {lineup_num + 1}")
                break

        # Restore original scores
        for player in util_players:
            if hasattr(player, 'temp_score'):
                player.optimization_score = player.temp_score
                delattr(player, 'temp_score')

        return lineups

    def _optimize_single_showdown(
            self,
            players: List,
            used_captains: set,
            min_salary_usage: float
    ) -> Optional[Dict]:
        """
        Optimize a single showdown lineup using MILP
        """
        n_players = len(players)

        # Create optimization problem
        prob = pulp.LpProblem("Showdown_DFS", pulp.LpMaximize)

        # Decision variables
        # x[i] = 1 if player i is selected as UTIL
        x = pulp.LpVariable.dicts("util", range(n_players), cat="Binary")

        # c[i] = 1 if player i is selected as CAPTAIN
        c = pulp.LpVariable.dicts("captain", range(n_players), cat="Binary")

        # Objective: Maximize total score
        # Captain gets 1.5x score, utilities get 1x score
        prob += pulp.lpSum([
            c[i] * getattr(players[i], 'optimization_score', 0) * self.captain_multiplier +
            x[i] * getattr(players[i], 'optimization_score', 0)
            for i in range(n_players)
        ])

        # Constraints

        # 1. Exactly 1 captain
        prob += pulp.lpSum([c[i] for i in range(n_players)]) == 1

        # 2. Exactly 5 utilities (not including captain)
        prob += pulp.lpSum([x[i] for i in range(n_players)]) == 5

        # 3. Player can't be both captain and utility
        for i in range(n_players):
            prob += x[i] + c[i] <= 1

        # 4. Salary constraint
        # Captain costs 1.5x, utilities cost 1x
        total_salary = pulp.lpSum([
            c[i] * players[i].salary * self.captain_multiplier +
            x[i] * players[i].salary
            for i in range(n_players)
        ])
        prob += total_salary <= self.salary_cap

        # 5. Minimum salary usage
        prob += total_salary >= self.salary_cap * min_salary_usage

        # 6. Captain diversity (soft constraint via objective penalty)
        # Already handled by score modification

        # 7. Team balance (optional - max 4 from same team)
        teams = list(set(p.team for p in players))
        for team in teams:
            team_players = [i for i in range(n_players) if players[i].team == team]
            if len(team_players) > 4:
                prob += pulp.lpSum([
                    x[i] + c[i] for i in team_players
                ]) <= 4

        # Solve
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        if prob.status == pulp.LpStatusOptimal:
            # Extract lineup
            captain = None
            utilities = []
            total_salary = 0
            total_score = 0

            for i in range(n_players):
                if c[i].varValue == 1:
                    captain = players[i]
                    total_salary += captain.salary * self.captain_multiplier
                    total_score += getattr(captain, 'optimization_score', 0) * self.captain_multiplier
                elif x[i].varValue == 1:
                    utilities.append(players[i])
                    total_salary += players[i].salary
                    total_score += getattr(players[i], 'optimization_score', 0)

            if captain and len(utilities) == 5:
                logger.info(f"Showdown lineup: CPT {captain.name} + 5 UTIL, "
                            f"${total_salary} ({total_salary / self.salary_cap:.1%}), "
                            f"{total_score:.1f} pts")

                return {
                    'captain': captain,
                    'utilities': utilities,
                    'total_salary': int(total_salary),
                    'total_score': total_score,
                    'type': 'showdown'
                }
            else:
                logger.error(f"Invalid lineup: captain={captain is not None}, "
                             f"utils={len(utilities)}")
                return None
        else:
            logger.error(f"Optimization failed: {pulp.LpStatus[prob.status]}")

            # Debug information
            if prob.status == pulp.LpStatusInfeasible:
                logger.error("Problem is infeasible. Checking constraints...")

                # Check if we have enough salary room
                min_cost = sum(sorted([p.salary for p in players])[:5])  # 5 cheapest as UTIL
                cheapest_captain = min(p.salary * self.captain_multiplier for p in players)
                min_possible = min_cost + cheapest_captain

                logger.error(f"Minimum possible salary: ${min_possible}")
                logger.error(f"Required salary: ${self.salary_cap * min_salary_usage}")

                if min_possible > self.salary_cap:
                    logger.error("Not enough salary cap for any valid lineup!")

            return None

    def format_showdown_lineup(self, lineup: Dict) -> List:
        """
        Format showdown lineup for display/export

        Returns list of players with captain marked
        """
        formatted = []

        # Add captain first
        captain = lineup['captain']
        captain_display = {
            'position': 'CPT',
            'name': captain.name,
            'team': captain.team,
            'salary': int(captain.salary * self.captain_multiplier),
            'util_salary': captain.salary,
            'score': getattr(captain, 'optimization_score', 0) * self.captain_multiplier,
            'is_captain': True
        }
        formatted.append(captain_display)

        # Add utilities
        for player in lineup['utilities']:
            util_display = {
                'position': 'UTIL',
                'name': player.name,
                'team': player.team,
                'salary': player.salary,
                'score': getattr(player, 'optimization_score', 0),
                'is_captain': False
            }
            formatted.append(util_display)

        return formatted


# Integration helper
def is_showdown_slate(players: List) -> bool:
    """
    Detect if this is a showdown slate

    Indicators:
    - Player names contain (CPT)
    - Only 2 teams in player pool
    - Small player pool (< 50 players)
    """
    # Check for CPT entries
    has_cpt = any("(CPT)" in getattr(p, 'Name', '') or
                  "CPT" in getattr(p, 'roster_position', '')
                  for p in players)

    # Check team count
    teams = set(p.team for p in players if hasattr(p, 'team'))
    is_two_teams = len(teams) == 2

    # Small player pool
    is_small = len(players) < 50

    return has_cpt or (is_two_teams and is_small)


if __name__ == "__main__":
    print("✅ Showdown Optimizer Module")
    print("\nFeatures:")
    print("  • Handles CPT/UTIL pricing correctly")
    print("  • Uses UTIL entries only")
    print("  • Applies 1.5x multiplier in optimization")
    print("  • Ensures valid 1 CPT + 5 UTIL lineups")
    print("  • Supports multi-lineup generation")