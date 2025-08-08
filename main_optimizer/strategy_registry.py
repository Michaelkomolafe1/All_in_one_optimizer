"""
STRATEGY REGISTRY
=================
Your ACTUAL working strategies
"""

# GPP STRATEGIES (Tournament)
GPP_STRATEGIES = {
    'tournament_winner_gpp': {
        'description': 'Based on 50,000+ winning lineups - forces 4-5 stacks',
        'min_stack': 4,
        'correlation_bonus': 2.0,
        'best_for': 'all slate sizes'
    },
    'correlation_value': {
        'description': 'Value plays with correlation',
        'min_stack': 4,
        'correlation_bonus': 1.5,
        'best_for': 'large slates'
    },
    'truly_smart_stack': {
        'description': 'Advanced stacking logic',
        'min_stack': 4,
        'correlation_bonus': 1.5,
        'best_for': 'medium slates'
    },
    'matchup_leverage_stack': {
        'description': 'Exploits specific matchups',
        'min_stack': 4,
        'correlation_bonus': 1.3,
        'best_for': 'small slates with clear edges'
    }
}

# CASH STRATEGIES
CASH_STRATEGIES = {
    'cash': {
        'description': 'Basic cash game optimization',
        'max_per_team': 3,
        'focus': 'floor',
        'best_for': 'all slate sizes'
    },
    'projection_monster': {
        'description': 'Maximizes raw projections',
        'max_per_team': 3,
        'focus': 'highest projections',
        'best_for': 'large slates'
    },
    'pitcher_dominance': {
        'description': 'Elite pitchers with value bats',
        'max_per_team': 3,
        'focus': 'pitching floor',
        'best_for': 'small slates'
    },
    'balanced': {
        'description': 'Balanced approach',
        'max_per_team': 3,
        'focus': 'balance',
        'best_for': 'medium slates'
    }
}

def get_strategy_list(contest_type='gpp'):
    """Get list of available strategies for contest type"""
    if contest_type.lower() == 'gpp':
        return list(GPP_STRATEGIES.keys())
    else:
        return list(CASH_STRATEGIES.keys())

def is_valid_strategy(strategy_name):
    """Check if strategy exists"""
    all_strategies = list(GPP_STRATEGIES.keys()) + list(CASH_STRATEGIES.keys())
    return strategy_name in all_strategies
