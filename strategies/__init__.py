"""DFS Optimizer Strategies"""

from .cash_strategies import (
    build_projection_monster,
    build_pitcher_dominance
)

from .gpp_strategies import (
    build_correlation_value,
    build_truly_smart_stack,  # Your new strategy
    build_matchup_leverage_stack
)

# Strategy registry
STRATEGY_REGISTRY = {
    'cash': {
        'small': build_projection_monster,
        'medium': build_pitcher_dominance,
        'large': build_pitcher_dominance
    },
    'gpp': {
        'small': build_correlation_value,
        'medium': build_truly_smart_stack,  # Your new one replaces old smart_stack
        'large': build_matchup_leverage_stack
    }
}