#!/usr/bin/env python3
"""
FIXED SHOWDOWN OPTIMIZATION MODULE
==================================
Corrects the captain multiplier issue in showdown slates
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class ShowdownOptimizer:
    """
    Fixed showdown optimizer that properly handles captain multipliers
    Key fix: Uses UTIL prices and applies 1.5x multiplier ONLY to selected captain
    """

    def __init__(self, milp_optimizer):
        self.milp_optimizer = milp_optimizer
        self.salary_cap = 50000
        self.captain_multiplier = 1.5
        self.captain_score_multiplier = 1.5

    def detect_showdown_slate(self, players: List) -> bool:
        """Detect if this is a showdown slate"""
        # Check for CPT/UTIL positions
        positions = {p.primary_position for p in players}
        if 'CPT' in positions or 'UTIL' in positions:
            return True

        # Check if no traditional positions
        traditional_positions = {'P', 'C', '1B', '2B', '3B', 'SS', 'OF'}
        if not any(pos in positions for pos in traditional_positions):
            return True

        return False

    def prepare_showdown_players(self, all_players: List) -> List:
        """
        Prepare players for showdown optimization
        CRITICAL: Only use UTIL entries, ignore CPT entries
        """
        # Filter to UTIL players only
        util_players = []
        seen_names = set()

        for player in all_players:
            # Skip CPT entries entirely
            if player.primary_position == 'CPT':
                continue

            # Use UTIL entries or deduplicate if positions are mixed
            if player.name not in seen_names:
                util_players.append(player)
                seen_names.add(player.name)

        logger.info(f"Showdown pool: {len(util_players)} unique UTIL players")
        return util_players

    def optimize_showdown_lineup(self, players: List, strategy: str = "balanced") -> Dict:
        """
        Optimize a single showdown lineup
        Uses MILP to select 6 players, then assigns captain
        """
        if len(players) < 6:
            logger.error(f"Not enough players for showdown: {len(players)}")
            return None

        # Use MILP to find optimal 6 players
        from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpStatus, value

        # Create problem
        prob = LpProblem("Showdown_DFS", LpMaximize)

        # Decision variables
        player_vars = {}
        captain_vars = {}

        for player in players:
            # Binary variable for selecting player
            player_vars[player.name] = LpVariable(
                f"player_{player.name}",
                cat='Binary'
            )
            # Binary variable for captain (can only be 1 if player selected)
            captain_vars[player.name] = LpVariable(
                f"captain_{player.name}",
                cat='Binary'
            )

        # Objective: Maximize score with captain bonus
        prob += lpSum([
            player_vars[p.name] * p.optimization_score +
            captain_vars[p.name] * p.optimization_score * (self.captain_score_multiplier - 1)
            for p in players
        ])

        # Constraints

        # 1. Exactly 6 players
        prob += lpSum([player_vars[p.name] for p in players]) == 6

        # 2. Exactly 1 captain
        prob += lpSum([captain_vars[p.name] for p in players]) == 1

        # 3. Captain must be selected player
        for player in players:
            prob += captain_vars[player.name] <= player_vars[player.name]

        # 4. Salary cap constraint
        # Regular players at normal salary, captain at 1.5x
        prob += lpSum([
            player_vars[p.name] * p.salary +
            captain_vars[p.name] * p.salary * (self.captain_multiplier - 1)
            for p in players
        ]) <= self.salary_cap

        # 5. Team limits for competitive balance (optional)
        if strategy != "stack":
            teams = list(set(p.team for p in players))
            for team in teams:
                team_players = [p for p in players if p.team == team]
                if len(team_players) > 4:
                    prob += lpSum([
                        player_vars[p.name] for p in team_players
                    ]) <= 4

        # Solve
        from pulp import PULP_CBC_CMD
        solver = PULP_CBC_CMD(timeLimit=20, gapRel=0.01, msg=0)
        prob.solve(solver)

        if LpStatus[prob.status] != 'Optimal':
            logger.error("No optimal showdown lineup found")
            return None

        # Extract results
        selected_players = []
        captain = None
        total_salary = 0
        total_score = 0

        for player in players:
            if value(player_vars[player.name]) == 1:
                selected_players.append(player)

                if value(captain_vars[player.name]) == 1:
                    captain = player
                    # Captain costs 1.5x
                    total_salary += player.salary * self.captain_multiplier
                    total_score += player.optimization_score * self.captain_score_multiplier
                else:
                    # Regular UTIL
                    total_salary += player.salary
                    total_score += player.optimization_score

        if not captain or len(selected_players) != 6:
            logger.error("Invalid showdown lineup generated")
            return None

        # Create lineup result
        result = {
            'success': True,
            'captain': captain,
            'utilities': [p for p in selected_players if p != captain],
            'total_salary': total_salary,
            'total_score': total_score,
            'players': selected_players
        }

        logger.info(f"Showdown lineup: Captain {captain.name} (${captain.salary * 1.5:.0f}), "
                    f"Score: {total_score:.1f}, Salary: ${total_salary:.0f}")

        return result

    def generate_diverse_lineups(
            self,
            players: List,
            num_lineups: int,
            min_captain_variety: int = 3
    ) -> List[Dict]:
        """Generate multiple diverse showdown lineups"""
        lineups = []
        used_captains = []
        captain_counts = {}

        # Prepare players
        util_players = self.prepare_showdown_players(players)

        for i in range(num_lineups):
            # Apply penalties to overused captains
            if i > 0:
                for player in util_players:
                    if captain_counts.get(player.name, 0) >= 2:
                        # Temporarily reduce score to encourage variety
                        player.temp_score = player.optimization_score
                        player.optimization_score *= 0.7

            # Generate lineup
            result = self.optimize_showdown_lineup(util_players)

            # Restore original scores
            for player in util_players:
                if hasattr(player, 'temp_score'):
                    player.optimization_score = player.temp_score

            if result and result['success']:
                lineups.append(result)
                captain = result['captain']
                used_captains.append(captain.name)
                captain_counts[captain.name] = captain_counts.get(captain.name, 0) + 1

                # Log progress
                unique_captains = len(set(used_captains))
                logger.info(f"Lineup {i + 1}/{num_lineups}: "
                            f"{unique_captains} unique captains")

        return lineups


def integrate_showdown_with_core(UnifiedCoreSystem):
    """
    Monkey patch to integrate fixed showdown optimization
    This replaces the broken showdown methods in UnifiedCoreSystem
    """

    def optimize_showdown_lineups(self, num_lineups=20, strategy="balanced", **kwargs):
        """Fixed showdown optimization method"""
        # Create showdown optimizer
        showdown_opt = ShowdownOptimizer(self.optimizer)

        # Detect if showdown
        if not showdown_opt.detect_showdown_slate(self.player_pool):
            logger.warning("Not a showdown slate, use regular optimization")
            return []

        # Generate lineups
        lineups = showdown_opt.generate_diverse_lineups(
            self.player_pool,
            num_lineups
        )

        # Convert to expected format
        formatted_lineups = []
        for lineup in lineups:
            formatted = {
                'players': lineup['players'],
                'captain': lineup['captain'],
                'utilities': lineup['utilities'],
                'total_salary': lineup['total_salary'],
                'total_score': lineup['total_score'],
                'type': 'showdown'
            }
            formatted_lineups.append(formatted)

        return formatted_lineups

    # Patch the method
    UnifiedCoreSystem.optimize_showdown_lineups = optimize_showdown_lineups

    logger.info("✅ Showdown optimization fixed and integrated")


# Example usage for testing
if __name__ == "__main__":
    # Test with mock data
    from types import SimpleNamespace

    # Create mock UTIL players (not CPT)
    mock_players = [
        SimpleNamespace(
            name="Judge", position="UTIL", team="NYY",
            salary=10200, optimization_score=15.5
        ),
        SimpleNamespace(
            name="Ohtani", position="UTIL", team="LAA",
            salary=10000, optimization_score=14.8
        ),
        # Add more test players...
    ]

    # Test optimizer
    milp_optimizer = None  # Would be real MILP optimizer
    showdown = ShowdownOptimizer(milp_optimizer)

    print("Showdown slate detected:", showdown.detect_showdown_slate(mock_players))
    print("UTIL players:", len(showdown.prepare_showdown_players(mock_players)))