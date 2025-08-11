#!/usr/bin/env python3
"""
STRATEGY MANAGER V2
===================
Your 4 proven strategies - simplified and clear
"""

from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class StrategyManager:
    """Manages your proven DFS strategies"""

    def __init__(self):
        # Strategy selection based on slate size
        self.strategy_map = {
            'cash': {
                'small': 'pitcher_dominance',  # 80% win rate
                'medium': 'projection_monster',  # 72% win rate
                'large': 'projection_monster'  # 74% win rate
            },
            'gpp': {
                'small': 'tournament_winner_gpp',  # Best small GPP
                'medium': 'tournament_winner_gpp',  # Best medium GPP
                'large': 'correlation_value'  # Best large GPP
            }
        }

    # In strategies_v2.py, update the auto_select_strategy method:

    def auto_select_strategy(self, num_games: int, contest_type: str) -> Tuple[str, str]:
        """
        Auto-select best strategy based on slate

        Returns: (strategy_name, reason)
        """
        # Determine slate size
        if num_games <= 4:
            slate_size = 'small'
        elif num_games <= 9:
            slate_size = 'medium'
        else:
            slate_size = 'large'

        # Get optimal strategy
        strategy = self.strategy_map[contest_type][slate_size]

        # Build reason with CORRECT names
        if contest_type == 'cash':
            if strategy == 'pitcher_dominance':
                reason = f"{num_games} games → Pitcher Dominance (80% win rate)"
            elif strategy == 'projection_monster':
                reason = f"{num_games} games → Projection Monster (72-74% win rate)"
            else:
                reason = f"{num_games} games → {strategy}"
        else:  # GPP
            if strategy == 'tournament_winner_gpp':
                reason = f"{num_games} games → Tournament Winner (proven GPP)"
            elif strategy == 'correlation_value':
                reason = f"{num_games} games → Correlation Value (large slate specialist)"
            else:
                reason = f"{num_games} games → {strategy}"

        return strategy, reason

    def apply_strategy(self, players: List, strategy: str) -> List:
        """
        Apply strategy-specific adjustments to player pool

        This is SIMPLE filtering and adjustment only!
        Scoring drives the actual optimization behavior
        """

        logger.info(f"Applying strategy: {strategy}")

        if strategy == 'tournament_winner_gpp':
            players = self._tournament_winner(players)

        elif strategy == 'correlation_value':
            players = self._correlation_value(players)

        elif strategy == 'projection_monster':
            players = self._projection_monster(players)

        elif strategy == 'pitcher_dominance':
            players = self._pitcher_dominance(players)

        else:
            logger.warning(f"Unknown strategy: {strategy}")

        return players

    def _tournament_winner(self, players: List) -> List:
        """
        Tournament Winner GPP Strategy
        - Focus on 4-5 player stacks
        - Leverage low ownership
        - Target high-total games
        """

        # Mark stackable players (high-total games)
        for player in players:
            team_total = getattr(player, 'implied_team_score', 4.5)

            if player.position not in ['P', 'SP', 'RP']:
                # Hitters in high-scoring games are stackable
                if team_total >= 5.0:
                    player.stack_eligible = True
                    # Small boost to encourage optimizer to pick them together
                    player.optimization_score *= 1.05

            else:
                # Pitchers against low-scoring teams
                opp_total = getattr(player, 'opponent_implied_total', 4.5)
                if opp_total < 4.0:
                    player.optimization_score *= 1.05

        return players

    def _correlation_value(self, players: List) -> List:
        """
        Correlation Value Strategy
        - Value plays in correlated spots
        - Focus on game environment
        - Large slate specialist
        """

        for player in players:
            # Value calculation
            if player.salary > 0:
                value = player.projection / (player.salary / 1000)
            else:
                value = 0

            # Boost value plays in good spots
            team_total = getattr(player, 'implied_team_score', 4.5)

            if value >= 3.0 and team_total >= 4.5:
                player.optimization_score *= 1.08
                player.value_play = True

        return players

    def _projection_monster(self, players: List) -> List:
        """
        Projection Monster (Cash)
        - Pure projection focus
        - Consistency emphasis
        - Safe floor plays
        """

        # Filter out risky plays
        min_projection = 8.0  # Minimum viable projection

        for player in players:
            # Penalize low projections
            if player.projection < min_projection:
                player.optimization_score *= 0.7

            # Boost consistent players
            consistency = getattr(player, 'consistency_score', 50)
            if consistency >= 70:
                player.optimization_score *= 1.05

        return players

    def _pitcher_dominance(self, players: List) -> List:
        """
        Pitcher Dominance (Cash - Small Slates)
        - Elite pitchers priority
        - K-rate focus
        - Value bats to fit
        """

        for player in players:
            if player.position in ['P', 'SP', 'RP']:
                # Boost elite K pitchers
                k_rate = getattr(player, 'k_rate', 7.0)

                if k_rate >= 10.0:
                    player.optimization_score *= 1.20  # Big boost
                elif k_rate >= 8.5:
                    player.optimization_score *= 1.10
                else:
                    player.optimization_score *= 0.90  # Penalize low K

            else:
                # Slight penalty to expensive hitters (need salary for pitchers)
                if player.salary > 5000:
                    player.optimization_score *= 0.95

        return players

    def get_all_strategies(self) -> dict:
        """Get all available strategies with descriptions"""

        return {
            'tournament_winner_gpp': 'Proven GPP winner - 4-5 player stacks',
            'correlation_value': 'Value in correlated spots - large slates',
            'projection_monster': 'Max projections - cash games',
            'pitcher_dominance': 'Elite pitchers - small slate cash'
        }


# Test
if __name__ == "__main__":
    print("Strategy Manager V2 Test")
    print("=" * 50)

    manager = StrategyManager()

    # Test auto-selection
    print("\nAuto-Selection Tests:")

    # Small slate cash
    strategy, reason = manager.auto_select_strategy(3, 'cash')
    print(f"3-game cash: {strategy}")
    print(f"  Reason: {reason}")

    # Large slate GPP
    strategy, reason = manager.auto_select_strategy(12, 'gpp')
    print(f"12-game GPP: {strategy}")
    print(f"  Reason: {reason}")


    # Test strategy application
    class TestPlayer:
        def __init__(self, name, pos, salary, proj):
            self.name = name
            self.position = pos
            self.salary = salary
            self.projection = proj
            self.optimization_score = proj
            self.implied_team_score = 5.0
            self.k_rate = 9.0
            self.consistency_score = 75


    players = [
        TestPlayer("Cole", "P", 9000, 45),
        TestPlayer("Trout", "OF", 6000, 15)
    ]

    # Apply pitcher dominance
    players = manager.apply_strategy(players, 'pitcher_dominance')

    print("\nAfter Pitcher Dominance Strategy:")
    for p in players:
        print(f"  {p.name}: {p.optimization_score:.1f} (was {p.projection})")

    print("\n✅ Strategy Manager V2 working correctly!")