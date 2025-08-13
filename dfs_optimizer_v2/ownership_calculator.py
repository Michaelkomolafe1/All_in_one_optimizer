#!/usr/bin/env python3
"""
SIMPLE OWNERSHIP CALCULATOR
===========================
Complete replacement that works with all call signatures
"""

import logging

logger = logging.getLogger(__name__)


class OwnershipCalculator:
    """Simple ownership projections that just work"""

    def __init__(self):
        self.ownership_cache = {}

    def get_ownership(self, *args):
        """
        Flexible method that handles multiple signatures:
        - get_ownership(player_object)
        - get_ownership(name, position, salary, team)
        - get_ownership(player_id)
        """
        if len(args) == 1:
            # Could be player object or player_id
            arg = args[0]
            if hasattr(arg, 'salary'):
                # It's a player object
                return self._calculate_for_player(arg)
            else:
                # It's a player_id
                return self.ownership_cache.get(arg, 15.0)

        elif len(args) == 4:
            # It's (name, position, salary, team)
            name, position, salary, team = args
            return self._calculate_from_values(name, position, salary, team)

        # Default
        return 15.0

    def calculate_ownership(self, *args, **kwargs):
        """
        Flexible calculation method:
        - calculate_ownership(players, contest_type)
        - calculate_ownership(name, salary, projection)
        """
        if len(args) >= 1 and isinstance(args[0], list):
            # It's a list of players
            return self._calculate_for_list(args[0], args[1] if len(args) > 1 else 'gpp')

        elif len(args) == 3:
            # It's (name, salary, projection)
            name, salary, projection = args
            value = projection / (salary / 1000) if salary > 0 else 3.0

            # Simple ownership based on value
            if value > 5.0:
                ownership = 35.0  # Great value
            elif value > 4.5:
                ownership = 28.0
            elif value > 4.0:
                ownership = 22.0
            elif value > 3.5:
                ownership = 18.0
            elif value > 3.0:
                ownership = 15.0
            elif value > 2.5:
                ownership = 12.0
            else:
                ownership = 8.0  # Poor value

            # Salary tier adjustment
            if salary >= 10000:
                ownership *= 1.2  # Aces get more ownership
            elif salary <= 4000:
                ownership *= 0.8  # Punts less popular

            return max(1.0, min(60.0, ownership))

        # Default
        return 15.0

    def _calculate_from_values(self, name, position, salary, team):
        """Calculate ownership from individual values"""
        ownership = 15.0  # Base

        # Salary-based tiers
        if salary >= 10000:
            ownership = 35.0  # Expensive aces
        elif salary >= 8000:
            ownership = 25.0  # Premium players
        elif salary >= 6000:
            ownership = 18.0  # Mid-tier
        elif salary >= 4500:
            ownership = 12.0  # Value plays
        else:
            ownership = 5.0  # Punt plays

        # Position adjustments
        if position in ['P', 'SP', 'RP']:
            ownership *= 1.15  # Pitchers slightly more owned
        elif position == 'C':
            ownership *= 0.85  # Catchers less owned

        # Popular teams get boost
        if team in ['NYY', 'LAD', 'HOU', 'ATL']:
            ownership *= 1.1

        return max(1.0, min(60.0, ownership))

    def _calculate_for_player(self, player):
        """Calculate for a player object"""
        return self._calculate_from_values(
            getattr(player, 'name', ''),
            getattr(player, 'position', ''),
            getattr(player, 'salary', 5000),
            getattr(player, 'team', '')
        )

    def _calculate_for_list(self, players, contest_type='gpp'):
        """Calculate for a list of players"""
        ownership = {}

        for player in players:
            own = self._calculate_for_player(player)

            # Contest type adjustment
            if contest_type == 'cash':
                own = min(own * 1.3, 60)  # Cash more concentrated

            player_id = getattr(player, 'player_id', player.name)
            ownership[player_id] = own

            # Set on player object
            if hasattr(player, 'ownership_projection'):
                player.ownership_projection = own
            if hasattr(player, 'projected_ownership'):
                player.projected_ownership = own

        self.ownership_cache.update(ownership)
        return ownership