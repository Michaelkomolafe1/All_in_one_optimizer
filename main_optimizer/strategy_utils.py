"""
Utility functions for strategies
"""


def apply_strategy_to_players(players, strategy_name):
    """
    Apply a strategy by name
    """
    from __init__ import STRATEGY_REGISTRY

    # Determine slate size (you'll implement this)
    player_count = len(players)
    if player_count <= 100:
        slate_size = 'small'
    elif player_count <= 200:
        slate_size = 'medium'
    else:
        slate_size = 'large'

    # Determine contest type (passed in or default)
    contest_type = 'gpp'  # You'll pass this in

    # Get strategy function
    strategy_func = STRATEGY_REGISTRY[contest_type][slate_size]

    # Apply strategy
    return strategy_func(players)