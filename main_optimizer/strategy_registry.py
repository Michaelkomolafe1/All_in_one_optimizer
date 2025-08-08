"""
STRATEGY REGISTRY
=================
Single source of truth for WORKING strategies
Last verified: 2025-08-08
"""

# ✅ WORKING GPP STRATEGIES
GPP_STRATEGIES = {
    'tournament_winner_gpp': {
        'description': 'Based on 50,000+ winning lineups',
        'min_stack': 4,
        'max_stack': 5,
        'tested': True,
        'performance': 'EXCELLENT'
    },
    'correlation_value': {
        'description': 'Value plays with correlation',
        'min_stack': 4,
        'max_stack': 5,
        'tested': True,
        'performance': 'GOOD'
    }
}

# ✅ WORKING CASH STRATEGIES  
CASH_STRATEGIES = {
    'cash': {
        'description': 'Basic cash game optimization',
        'max_per_team': 3,
        'tested': True,
        'performance': 'EXCELLENT'
    },
    'projection_monster': {
        'description': 'Maximize raw projections',
        'max_per_team': 3,
        'tested': True,
        'performance': 'GOOD'
    },
    'pitcher_dominance': {
        'description': 'Elite pitchers with value bats',
        'max_per_team': 3,
        'tested': True,
        'performance': 'GOOD'
    }
}

# ❌ PHANTOM STRATEGIES (Don't exist - remove from code)
PHANTOM_STRATEGIES = [
    'stars_and_scrubs_extreme',
    'cold_player_leverage',
    'woba_explosion',
    'rising_team_stack',
    'iso_power_stack',
    'leverage_theory',
    'smart_stack',
    'ceiling_stack',
    'barrel_rate_correlation',
    'multi_stack_mayhem',
    'pitcher_stack_combo',
    'vegas_explosion',
    'high_k_pitcher_fade'
]

def get_working_strategies(contest_type='gpp'):
    """Get only strategies that actually work"""
    if contest_type.lower() in ['gpp', 'tournament']:
        return list(GPP_STRATEGIES.keys())
    else:
        return list(CASH_STRATEGIES.keys())

def is_valid_strategy(strategy):
    """Check if a strategy actually exists"""
    all_valid = list(GPP_STRATEGIES.keys()) + list(CASH_STRATEGIES.keys())
    return strategy in all_valid

# For backward compatibility
ALL_STRATEGIES = get_working_strategies('gpp') + get_working_strategies('cash')

print(f"✅ Strategy registry loaded: {len(ALL_STRATEGIES)} working strategies")
