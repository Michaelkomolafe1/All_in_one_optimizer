#!/usr/bin/env python3
"""
Quick DFS Configuration
Modify these settings to customize your optimizer
"""

# STACKING SETTINGS FOR CASH GAMES
CASH_GAME_STACKING = {
    'enable': True,           # Enable team stacking
    'min_players': 2,         # Minimum stack size  
    'max_players': 3,         # Maximum stack size (conservative)
    'min_team_total': 4.8,    # Only stack high-scoring teams
}

# STACKING SETTINGS FOR TOURNAMENTS  
TOURNAMENT_STACKING = {
    'enable': True,           # Enable team stacking
    'min_players': 2,         # Minimum stack size
    'max_players': 5,         # Maximum stack size (aggressive)
    'min_team_total': 4.5,    # Lower threshold for GPP
}

# VEGAS INTEGRATION
VEGAS_SETTINGS = {
    'enable': True,           # Use Vegas lines for boosts
    'cache_hours': 2,         # How long to cache data
    'high_total_boost': 2.0,  # Boost for 5.0+ team totals
    'low_total_penalty': -1.0 # Penalty for <3.5 team totals
}

# DEFAULT STRATEGIES
DEFAULT_STRATEGY = 'smart_confirmed'  # Best for most users

AVAILABLE_STRATEGIES = [
    'smart_confirmed',        # Confirmed players + enhanced data
    'confirmed_only',         # Only confirmed starters  
    'confirmed_plus_manual',  # Confirmed + your manual picks
    'manual_only',           # Only your specified players
    'all_players'            # Maximum flexibility
]

# MANUAL SELECTION EXAMPLES
MANUAL_EXAMPLES = [
    "Kyle Tucker, Jorge Polanco",              # Star hitters
    "Hunter Brown, Christian Yelich",          # Pitcher + hitter  
    "Vladimir Guerrero Jr., Francisco Lindor", # Infield stack
]

print("✅ DFS Configuration loaded")
print(f"📊 Default strategy: {DEFAULT_STRATEGY}")
print(f"🏆 Cash game stacking: {CASH_GAME_STACKING['min_players']}-{CASH_GAME_STACKING['max_players']} players")
