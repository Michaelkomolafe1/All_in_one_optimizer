#!/usr/bin/env python
# strategy_wrapper.py
# Save in main_optimizer/
"""Wrapper to fix strategy return formats"""


def wrap_strategy_result(players_or_lineup):
    """
    Convert strategy output to proper format.

    Strategies might return:
    - A list of players (old format)
    - A dict with lineup info (new format)
    - None (failed to build)
    """

    # If it's None, strategy failed
    if players_or_lineup is None:
        return None

    # If it's already a proper dict with 'players' key, return as-is
    if isinstance(players_or_lineup, dict) and 'players' in players_or_lineup:
        return players_or_lineup

    # If it's a list of players, wrap it in proper format
    if isinstance(players_or_lineup, list):
        # Calculate total salary and projection
        total_salary = 0
        total_projection = 0

        for player in players_or_lineup:
            # Handle both UnifiedPlayer objects and dicts
            if hasattr(player, 'salary'):  # UnifiedPlayer
                total_salary += player.salary
                total_projection += getattr(player, 'base_projection', 0) or getattr(player, 'projection', 0)
            elif isinstance(player, dict):  # Dict
                total_salary += player.get('salary', 0)
                total_projection += player.get('projection', 0)

        # Return proper lineup format
        return {
            'players': players_or_lineup,
            'salary': total_salary,
            'projection': total_projection,
            'positions': _extract_positions(players_or_lineup)
        }

    # Unknown format
    return None


def _extract_positions(players):
    """Extract position counts from lineup"""
    positions = {}
    for player in players:
        if hasattr(player, 'primary_position'):
            pos = player.primary_position
        elif hasattr(player, 'position'):
            pos = player.position
        elif isinstance(player, dict):
            pos = player.get('position', 'UNK')
        else:
            pos = 'UNK'
        positions[pos] = positions.get(pos, 0) + 1
    return positions


def call_strategy_safely(strategy_func, players, slate_size=None, use_wrapper=True):
    """
    Safely call a strategy function with proper parameters and error handling.
    """
    try:
        # Special handling for different strategies
        strategy_name = strategy_func.__name__

        # Strategies that need slate_size parameter
        if strategy_name == 'build_correlation_gpp':
            result = strategy_func(players, slate_size or 'medium')
        # Strategies that need params
        elif strategy_name == 'build_matchup_leverage_stack':
            # Provide default params to avoid KeyError
            params = {
                'pitcher_leverage_mult': 1.2,
                'hitter_leverage_mult': 1.15,
                'ownership_fade': 0.8,
                'stack_correlation_bonus': 1.1
            }
            result = strategy_func(players, params)
        # Standard strategies
        else:
            result = strategy_func(players)

        # Wrap result if needed
        if use_wrapper:
            return wrap_strategy_result(result)
        else:
            return result

    except Exception as e:
        print("Strategy {} failed: {}".format(strategy_name, e))
        return None