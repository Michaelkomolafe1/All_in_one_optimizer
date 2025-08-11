#!/usr/bin/env python3
"""
Ownership Projection Calculator
Estimates ownership based on DFS patterns
"""

import logging
from typing import Dict, List
import numpy as np

logger = logging.getLogger(__name__)


class OwnershipCalculator:
    """Calculate projected ownership percentages"""

    def __init__(self):
        self.ownership_cache = {}

    def calculate_ownership(self, players: List, contest_type: str = 'gpp') -> Dict:
        """
        Calculate ownership projections based on:
        1. Salary (cheap/expensive)
        2. Projection ranking
        3. Recent performance
        4. Position scarcity
        5. Team narrative
        """

        ownership = {}

        # Group by position for scarcity calculation
        by_position = {}
        for p in players:
            pos = p.primary_position
            if pos not in by_position:
                by_position[pos] = []
            by_position[pos].append(p)

        # Calculate for each player
        for player in players:
            base_ownership = 10.0  # Start at 10%

            # 1. SALARY FACTOR (Value plays get owned more)
            value = player.base_projection / (player.salary / 1000) if player.salary > 0 else 0
            if value > 5.0:  # Great value
                base_ownership += 15
            elif value > 4.0:  # Good value
                base_ownership += 8
            elif value < 2.5:  # Poor value
                base_ownership -= 5

            # 2. PROJECTION RANKING (Top projected players)
            pos_players = sorted(by_position[player.primary_position],
                                 key=lambda x: x.base_projection, reverse=True)
            rank = pos_players.index(player) + 1

            if rank == 1:  # Best at position
                base_ownership += 20
            elif rank <= 3:  # Top 3
                base_ownership += 10
            elif rank <= 5:  # Top 5
                base_ownership += 5

            # 3. PITCHER ADJUSTMENTS
            if player.primary_position in ['P', 'SP', 'RP']:
                if player.salary >= 10000:  # Expensive ace
                    base_ownership += 10
                elif player.salary <= 7000:  # Cheap pitcher
                    base_ownership -= 5

            # 4. RECENT HOT STREAK (if available)
            if hasattr(player, 'recent_form') and player.recent_form > 1.2:
                base_ownership += 8

            # 5. TEAM FACTORS
            if hasattr(player, 'implied_team_score'):
                if player.implied_team_score >= 5.5:  # High scoring game
                    base_ownership += 10
                elif player.implied_team_score <= 3.5:  # Low scoring
                    base_ownership -= 8

            # 6. POSITION SCARCITY
            position_depth = len(by_position[player.primary_position])
            if position_depth <= 10:  # Shallow position
                base_ownership += 5

            # Contest type adjustments
            if contest_type == 'cash':
                # Cash ownership is more concentrated
                if base_ownership > 30:
                    base_ownership = min(base_ownership * 1.5, 60)
            else:  # GPP
                # GPP ownership more spread out
                base_ownership = base_ownership * 0.8

            # Bound between 1% and 60%
            final_ownership = max(1, min(60, base_ownership))

            ownership[player.player_id] = final_ownership
            player.ownership_projection = final_ownership
            player.projected_ownership = final_ownership

        logger.info(f"Calculated ownership for {len(ownership)} players")
        return ownership

    def get_ownership(self, player_id: str) -> float:
        """Get ownership for a specific player"""
        return self.ownership_cache.get(player_id, 10.0)