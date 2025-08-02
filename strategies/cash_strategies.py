"""
Cash Game Strategies - #1 Winners
================================
UPDATED WITH optimization_score
"""
from collections import defaultdict
import numpy as np


def build_projection_monster(players):
    """
    #1 Cash Strategy for Small Slates (54% win rate)
    Focus on pure projections with park adjustment
    """
    for player in players:
        if player.primary_position == 'P':
            # Pitchers: Pure projection
            base_proj = player.projection
            park_adj = getattr(player, 'park_adjusted_projection', base_proj)

            # Average the adjustments
            final_proj = (base_proj + park_adj) / 2

            # SET OPTIMIZATION SCORE
            player.optimization_score = final_proj

        else:
            # Hitters: Projection + small value bonus
            base_proj = player.projection
            park_adj = getattr(player, 'park_adjusted_projection', base_proj)
            final_proj = (base_proj + park_adj) / 2

            # Small value component
            value_score = player.projection / (player.salary / 1000) if player.salary > 0 else 0
            value_bonus = value_score * 0.5

            # SET OPTIMIZATION SCORE
            player.optimization_score = final_proj + value_bonus

    return players


def build_pitcher_dominance(players):
    """
    #1 Cash Strategy for Medium/Large Slates (55-57% win rate)
    Elite pitchers + high floor hitters
    """
    for player in players:
        if player.primary_position == 'P':
            # Focus on strikeout ability
            k_rate = getattr(player, 'k_rate', 20)
            bb_rate = getattr(player, 'bb_rate', 8)
            k_bb_ratio = k_rate / max(bb_rate + 1, 1)

            # Elite pitcher multipliers
            if k_bb_ratio > 3:
                elite_mult = 1.5
            elif k_bb_ratio > 2.5:
                elite_mult = 1.3
            else:
                elite_mult = 0.9

            # SET OPTIMIZATION SCORE
            player.optimization_score = player.projection * elite_mult

        else:
            # Hitters: Floor-focused
            floor = getattr(player, 'floor', player.projection * 0.6)

            # 60% floor, 40% projection
            # SET OPTIMIZATION SCORE
            player.optimization_score = (floor * 0.6) + (player.projection * 0.4)

    return players