"""
Enhanced Cash Game Strategies with Tunable Parameters
====================================================
"""
from collections import defaultdict

import numpy as np


def build_projection_monster(players, params=None):
    """
    #1 Cash Strategy for Small Slates - Now with tunable parameters!

    Default params based on your original strategy, but now adjustable
    """
    params = params or {
        'park_weight': 0.5,           # 0.0-2.0: How much park factors matter
        'value_bonus_weight': 0.5,    # 0.0-1.0: Importance of salary efficiency
        'min_projection_threshold': 8, # 5-12: Minimum viable projection
        'pitcher_park_weight': 0.5,    # 0.0-1.0: Park weight for pitchers specifically
        'hitter_value_exp': 1.0,       # 0.5-2.0: Exponential scaling for value
        'projection_floor': 0.8,       # 0.5-1.0: Multiplier for min acceptable projection
    }

    for player in players:
        base_proj = player.base_projection

        # Skip if below minimum threshold
        if base_proj < params['min_projection_threshold'] * params['projection_floor']:
            player.optimization_score = 0
            continue

        if player.primary_position == 'P':
            # Pitchers: Configurable park adjustment
            park_adj = getattr(player, 'park_adjusted_projection', base_proj)

            # Weighted average based on park_weight parameter
            final_proj = (base_proj * (1 - params['pitcher_park_weight']) +
                         park_adj * params['pitcher_park_weight'])

            player.optimization_score = final_proj

        else:
            # Hitters: Configurable projection + value balance
            park_adj = getattr(player, 'park_adjusted_projection', base_proj)
            final_proj = (base_proj * (1 - params['park_weight']) +
                         park_adj * params['park_weight'])

            # Value component with exponential scaling
            if player.salary > 0:
                value_score = (base_proj / (player.salary / 1000)) ** params['hitter_value_exp']
            else:
                value_score = 0

            # Combine with configurable weights
            player.optimization_score = (
                final_proj * (1 - params['value_bonus_weight']) +
                value_score * params['value_bonus_weight'] * 10  # Scale to match projections
            )

        # Apply tournament enhancements
    for player in players:
        if player.primary_position == 'P':
            # K-rate is KING in cash
            k_rate = getattr(player, 'k_rate', 20)
            if k_rate >= 25:
                player.optimization_score *= 1.18  # Big boost
                player.cash_elite = True
            elif k_rate >= 22:
                player.optimization_score *= 1.08
            elif k_rate < 18:
                player.optimization_score *= 0.75  # Heavy penalty

            # Win probability crucial
            win_prob = getattr(player, 'win_probability', 0.5)
            if win_prob >= 0.65:
                player.optimization_score *= 1.15
            elif win_prob >= 0.60:
                player.optimization_score *= 1.05
            elif win_prob < 0.40:
                player.optimization_score *= 0.70

        else:  # Hitters
            # Batting order is MASSIVE in cash
            batting_order = getattr(player, 'batting_order', 9)
            if batting_order in [1, 2]:
                player.optimization_score *= 1.25  # 29% more PAs!
            elif batting_order in [3, 4]:
                player.optimization_score *= 1.12
            elif batting_order == 5:
                player.optimization_score *= 1.02
            elif batting_order >= 7:
                player.optimization_score *= 0.75  # Avoid bottom third

            # Walk rate for floor
            bb_rate = getattr(player, 'bb_rate', 8)
            if bb_rate >= 12:
                player.optimization_score *= 1.08
                player.high_floor = True
            elif bb_rate >= 10:
                player.optimization_score *= 1.03

            # Contact rate for safety
            k_rate = getattr(player, 'k_rate', 22)
            if k_rate <= 15:  # High contact
                player.optimization_score *= 1.05
            elif k_rate >= 28:  # Strikeout prone
                player.optimization_score *= 0.92

            # Slight road team edge (51.6% of PAs)
            if not getattr(player, 'is_home', True):
                player.optimization_score *= 1.02

    return players


def build_pitcher_dominance(players, params=None):
    """
    #1 Cash Strategy for Medium/Large Slates - Now with tunable parameters!
    Elite pitchers + high floor hitters
    """

    # Default parameters
    default_params = {
        'elite_k_bb_threshold': 3.0,
        'good_k_bb_threshold': 2.5,
        'elite_multiplier': 1.5,
        'good_multiplier': 1.3,
        'bad_multiplier': 0.9,
        'floor_weight': 0.6,
        'consistency_bonus': 0.2,
        'min_k_rate': 15,
        'whip_impact': 0.3,  # THIS WAS MISSING
    }

    # ROBUST FIX: Merge passed params with defaults
    if params is None:
        params = default_params
    else:
        # Fill in any missing keys with defaults
        for key, default_value in default_params.items():
            if key not in params:
                params[key] = default_value

    for player in players:
        if player.primary_position == 'P':
            # Get pitcher stats with safe defaults
            k_rate = getattr(player, 'k_rate', 20)
            bb_rate = getattr(player, 'bb_rate', 8)
            whip = getattr(player, 'whip', 1.30)

            # Skip terrible pitchers
            if k_rate < params['min_k_rate']:
                player.optimization_score = player.base_projection * 0.7
                continue

            # Calculate K/BB ratio
            k_bb_ratio = k_rate / max(bb_rate, 1)  # Avoid division by zero

            # WHIP adjustment - now guaranteed to have whip_impact
            whip_factor = 1.0 - (whip - 1.0) * params['whip_impact']
            whip_factor = max(0.5, min(1.5, whip_factor))

            # Apply tiered multipliers based on K/BB
            if k_bb_ratio >= params['elite_k_bb_threshold']:
                multiplier = params['elite_multiplier']
            elif k_bb_ratio >= params['good_k_bb_threshold']:
                multiplier = params['good_multiplier']
            else:
                multiplier = params['bad_multiplier']

            player.optimization_score = player.base_projection * multiplier * whip_factor

        else:
            # Hitters: Configurable floor/ceiling balance
            floor = getattr(player, 'floor', player.base_projection * 0.6)
            ceiling = getattr(player, 'ceiling', player.base_projection * 1.5)

            # Weighted combination
            base_score = (floor * params['floor_weight'] +
                          player.base_projection * (1 - params['floor_weight']))

            # Consistency bonus
            consistency = getattr(player, 'consistency_score', 0.5)
            consistency_mult = 1.0 + (consistency * params['consistency_bonus'])

            player.optimization_score = base_score * consistency_mult

    return players

def build_enhanced_cash_strategy(players, params=None):
    """
    Experimental: Multi-factor cash strategy with many parameters

    This is for testing which factors matter most
    """
    params = params or {
        # Base weights
        'projection_weight': 0.4,
        'recent_form_weight': 0.2,
        'matchup_weight': 0.2,
        'consistency_weight': 0.2,

        # Thresholds
        'min_projection': 8,
        'hot_player_threshold': 1.2,
        'cold_player_threshold': 0.8,

        # Position-specific
        'pitcher_premium': 1.1,
        'catcher_discount': 0.95,
        'top_order_boost': 1.15,

        # Environmental
        'weather_impact': 0.3,
        'park_impact': 0.3,
        'vegas_impact': 0.4,

        # Risk parameters
        'variance_penalty': 0.2,
        'injury_risk_penalty': 0.3,
    }

    for player in players:
        # Start with base projection
        score = player.base_projection

        # Skip if too low
        if score < params['min_projection']:
            player.optimization_score = 0
            continue

        # Build composite score
        factors = []

        # 1. Base projection (normalized)
        proj_factor = score / 20.0  # Normalize to ~1.0
        factors.append(('projection', proj_factor, params['projection_weight']))

        # 2. Recent form
        form = getattr(player, 'recent_form', 1.0)
        if form > params['hot_player_threshold']:
            form_factor = 1.2
        elif form < params['cold_player_threshold']:
            form_factor = 0.8
        else:
            form_factor = form
        factors.append(('form', form_factor, params['recent_form_weight']))

        # 3. Matchup quality
        matchup = getattr(player, 'matchup_score', 1.0)
        factors.append(('matchup', matchup, params['matchup_weight']))

        # 4. Consistency
        consistency = getattr(player, 'consistency_score', 0.7)
        factors.append(('consistency', consistency + 0.3, params['consistency_weight']))

        # Calculate weighted score
        total_score = 0
        total_weight = 0
        for name, value, weight in factors:
            total_score += value * weight
            total_weight += weight

        if total_weight > 0:
            normalized_score = (total_score / total_weight) * score
        else:
            normalized_score = score

        # Apply position adjustments
        if player.primary_position == 'P':
            normalized_score *= params['pitcher_premium']
        elif player.primary_position == 'C':
            normalized_score *= params['catcher_discount']

        # Batting order boost
        bat_order = getattr(player, 'batting_order', 6)
        if bat_order and 1 <= bat_order <= 3:
            normalized_score *= params['top_order_boost']

        # Environmental factors
        park = getattr(player, 'park_factor', 1.0)
        weather = getattr(player, 'weather_impact', 1.0)
        vegas = getattr(player, 'implied_team_score', 4.5) / 4.5

        env_factor = (
            1.0 +
            (park - 1.0) * params['park_impact'] +
            (weather - 1.0) * params['weather_impact'] +
            (vegas - 1.0) * params['vegas_impact']
        )

        normalized_score *= max(0.7, min(1.3, env_factor))

        # Risk adjustments
        variance = getattr(player, 'projection_variance', 0.3)
        injury_risk = getattr(player, 'injury_risk', 0.0)

        risk_factor = 1.0 - (variance * params['variance_penalty']) - (injury_risk * params['injury_risk_penalty'])
        risk_factor = max(0.5, risk_factor)

        player.optimization_score = normalized_score * risk_factor

    return players

# ============== ADD TO BOTTOM OF cash_strategies.py ==============


