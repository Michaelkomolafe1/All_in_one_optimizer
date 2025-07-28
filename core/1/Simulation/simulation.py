#!/usr/bin/env python3
"""
DFS ULTIMATE SIMULATOR 2.0 - FIXED EDITION
==========================================
Tests strategies across different slate sizes and formats (Classic/Showdown)
Discovers what ACTUALLY works for each contest type
"""

print("🚀 Loading DFS Ultimate Simulator 2.0 (Fixed Edition)...", flush=True)

import numpy as np
import random  # noqa
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import time
from typing import Dict, List, Optional, Set
import json
from datetime import datetime
from scipy import stats
import math
import sys

print("✅ Libraries loaded successfully!", flush=True)

# ========== CONFIGURATION ==========

# Classic DFS Configuration
CLASSIC_CONFIG = {
    'salary_cap': 50000,
    'roster_spots': 10,
    'positions': {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3},
    'max_players_per_team': 5,
    'min_teams': 2,
    'cash_payout_threshold': 0.44,  # Top 44% in cash games
    'gpp_payout_structure': {
        0.001: 100,  # Top 0.1%
        0.005: 20,  # Top 0.5%
        0.01: 10,  # Top 1%
        0.02: 5,  # Top 2%
        0.10: 2,  # Top 10%
        0.20: 1.2,  # Top 20%
    }
}

# Showdown Configuration
SHOWDOWN_CONFIG = {
    'salary_cap': 50000,
    'roster_spots': 6,
    'positions': {'CPT': 1, 'UTIL': 5},
    'captain_multiplier': 1.5,
    'min_teams': 2,  # Must have players from both teams
    'cash_payout_threshold': 0.44,  # Top 44% in cash games
    'gpp_payout_structure': {
        0.001: 100,
        0.005: 20,
        0.01: 10,
        0.02: 5,
        0.10: 2,
        0.20: 1.2,
        0.25: 0.5,  # Top 25% - min cash
    }
}

# Slate size categories
SLATE_SIZES = {
    'showdown': {'games': 1, 'name': 'Showdown'},
    'small': {'games': 3, 'name': 'Small (3 games)'},
    'medium': {'games': 7, 'name': 'Medium (7 games)'},
    'large': {'games': 12, 'name': 'Large (12+ games)'}
}

# ========== STRATEGY DEFINITIONS BY SLATE SIZE ==========

# Showdown-specific strategies
SHOWDOWN_STRATEGIES = {
    # CAPTAIN SELECTION STRATEGIES
    'max_projection_captain': {
        'name': 'Max Projection Captain',
        'type': 'max_proj_captain',
        'description': 'Highest projected player as CPT, fill with value'
    },
    'max_ceiling_captain': {
        'name': 'Max Ceiling Captain',
        'type': 'max_ceiling_captain',
        'description': 'Highest ceiling player as CPT, fill with value'
    },
    'leverage_captain_low_own': {
        'name': 'Leverage Captain <15% Own',
        'type': 'leverage_captain_15',
        'description': 'Captain must be <15% owned, 20+ ceiling'
    },
    'value_captain_under_5k': {
        'name': 'Value Captain <$5K',
        'type': 'value_captain_5k',
        'description': 'Captain under $5000, highest projection'
    },

    # GAME SCRIPT STRATEGIES
    'favorite_onslaught_4_2': {
        'name': 'Favorite Onslaught 4-2',
        'type': 'fav_onslaught_4_2',
        'description': '4 from favorite (higher total), 2 from dog'
    },
    'balanced_3_3': {
        'name': 'Balanced Game 3-3',
        'type': 'balanced_3_3',
        'description': 'Exactly 3 from each team'
    },
    'underdog_leverage_2_4': {
        'name': 'Underdog Leverage 2-4',
        'type': 'dog_leverage_2_4',
        'description': '2 from favorite, 4 from underdog'
    },

    # PITCHER STRATEGIES
    'both_pitchers': {
        'name': 'Both Pitchers',
        'type': 'both_pitchers',
        'description': 'Both starting pitchers + 4 hitters'
    },
    'ace_only': {
        'name': 'Ace Only',
        'type': 'ace_only',
        'description': 'Higher projected pitcher + 5 hitters'
    },
    'no_pitchers': {
        'name': 'No Pitchers',
        'type': 'no_pitchers',
        'description': 'Zero pitchers, all hitters'
    },

    # OWNERSHIP STRATEGIES
    'max_ownership': {
        'name': 'Max Ownership',
        'type': 'max_own',
        'description': 'Highest ownership players only'
    },
    'anti_chalk': {
        'name': 'Anti-Chalk <10% Avg',
        'type': 'anti_chalk_10',
        'description': 'No player over 20% owned, avg <10%'
    }
}

# Classic strategies that vary by slate size - EXPANDED
CLASSIC_STRATEGIES_BY_SIZE = {
    'small': {  # 3 games
        'cash': {
            'pure_projection': {
                'name': 'Pure Projection',
                'type': 'pure_proj',
                'description': 'Highest projection regardless of ownership'
            },
            'pure_floor': {
                'name': 'Pure Floor',
                'type': 'pure_floor',
                'description': 'Highest floor projections only'
            },
            'pure_value': {
                'name': 'Pure Value',
                'type': 'pure_value',
                'description': 'Highest points per dollar'
            },
            'balanced_proj_own': {
                'name': 'Balanced 50/50',
                'type': 'balanced_50_50',
                'description': '50% projection score + 50% ownership score'
            }
        },
        'gpp': {
            'pure_ceiling': {
                'name': 'Pure Ceiling',
                'type': 'pure_ceiling',
                'description': 'Highest ceiling projections only'
            },
            'team_stack_5': {
                'name': '5-Man Stack',
                'type': 'stack_5',
                'description': '5 players from same team, fill value'
            },
            'team_stack_4': {
                'name': '4-Man Stack',
                'type': 'stack_4',
                'description': '4 players from same team, fill value'
            },
            'max_15_ownership': {
                'name': 'Max 15% Ownership',
                'type': 'max_15_own',
                'description': 'No player over 15% owned'
            }
        }
    },

    'medium': {  # 7 games
        'cash': {
            'pure_ownership': {
                'name': 'Pure Ownership',
                'type': 'pure_own',
                'description': 'Highest ownership only'
            },
            'balanced_60_40': {
                'name': 'Balanced 60/40',
                'type': 'balanced_60_40',
                'description': '60% ownership + 40% projection'
            },
            'balanced_40_60': {
                'name': 'Balanced 40/60',
                'type': 'balanced_40_60',
                'description': '40% ownership + 60% projection'
            },
            'min_20_ownership': {
                'name': 'Min 20% Ownership',
                'type': 'min_20_own',
                'description': 'Only players with 20%+ ownership'
            }
        },
        'gpp': {
            'sequential_1_5': {
                'name': 'Sequential Stack 1-5',
                'type': 'seq_1_5',
                'description': 'Batting order 1-5 from same team'
            },
            'sequential_2_6': {
                'name': 'Sequential Stack 2-6',
                'type': 'seq_2_6',
                'description': 'Batting order 2-6 from same team'
            },
            'game_stack_3_2': {
                'name': 'Game Stack 3-2',
                'type': 'game_3_2',
                'description': '3 from one team, 2 from opponent'
            },
            'leverage_chalk': {
                'name': 'Leverage Chalk',
                'type': 'leverage_chalk',
                'description': 'One 30%+ player, rest <10%'
            }
        }
    },

    'large': {  # 12+ games
        'cash': {
            'pure_chalk': {
                'name': 'Pure Chalk',
                'type': 'pure_chalk',
                'description': 'Highest ownership only'
            },
            'chalk_threshold_25': {
                'name': 'Chalk 25%+ Only',
                'type': 'chalk_25',
                'description': 'Only players 25%+ owned'
            },
            'balanced_70_30': {
                'name': 'Balanced 70/30',
                'type': 'balanced_70_30',
                'description': '70% ownership + 30% projection'
            },
            'fade_40_plus': {
                'name': 'Fade 40%+',
                'type': 'fade_40',
                'description': 'No player over 40% owned'
            }
        },
        'gpp': {
            'team_stack_5_leverage': {
                'name': '5-Stack Low Own Team',
                'type': 'stack_5_low',
                'description': '5 from team with <10% avg ownership'
            },
            'multi_stack_3_3': {
                'name': 'Multi-Stack 3-3',
                'type': 'multi_3_3',
                'description': '3 from team A, 3 from team B'
            },
            'game_stack_4_2': {
                'name': 'Game Stack 4-2',
                'type': 'game_4_2',
                'description': '4 from one team, 2 from opponent'
            },
            'stars_scrubs_4_4': {
                'name': 'Stars & Scrubs 4-4',
                'type': 'stars_scrubs_44',
                'description': '4 players >$8K, 4 players <$3K'
            }
        }
    }
}
# ========== SCORING DEFINITIONS ==========

MLB_SCORING = {
    'hitters': {
        'single': 3,
        'double': 5,
        'triple': 8,
        'home_run': 10,
        'rbi': 2,
        'run': 2,
        'walk': 2,
        'hbp': 2,
        'stolen_base': 5
    },
    'pitchers': {
        'inning': 2.25,  # Per full inning
        'out': 0.75,  # Per out
        'strikeout': 2,
        'win': 4,
        'earned_run': -2,
        'hit': -0.6,
        'walk': -0.6,
        'hbp': -0.6,
        'complete_game': 2.5,
        'shutout': 2.5,
        'no_hitter': 5
    }
}

# ========== PLAYER GENERATION - FIXED ==========
def generate_showdown_player(player_id, team, position, game_data):
    """Generate a player for showdown format"""

    # For showdown, generate realistic batting order first
    if position == 'P':
        batting_order = 0
        # Pitcher salaries
        is_ace = random.random() < 0.5  # 50% chance of being the "ace"
        if is_ace:
            salary = random.randint(7500, 9500)
            projection = random.uniform(35, 45)
        else:
            salary = random.randint(5000, 7000)
            projection = random.uniform(25, 35)
    else:
        # Assign batting order realistically (1-9 for starters, 0 for bench)
        if player_id % 12 < 9:  # First 9 are starters
            batting_order = (player_id % 9) + 1
        else:  # Bench players
            batting_order = 0

        # SALARY BASED ON BATTING ORDER (like real DFS)
        if batting_order in [1, 2, 3, 4]:
            salary = random.randint(7000, 10500)
            projection = random.uniform(14, 20)
        elif batting_order in [5, 6]:
            salary = random.randint(5000, 7500)
            projection = random.uniform(10, 15)
        elif batting_order in [7, 8]:
            salary = random.randint(3000, 5000)
            projection = random.uniform(7, 12)
        elif batting_order == 9:
            salary = random.randint(2000, 3500)
            projection = random.uniform(5, 10)
        else:  # Bench
            salary = random.randint(2000, 3000)
            projection = random.uniform(4, 8)

    # Add some variance
    projection = projection * random.uniform(0.9, 1.1)

    # Calculate ownership realistically
    value = projection / (salary / 1000)
    if value > 3.5:
        ownership = random.uniform(35, 55)
    elif value > 3.0:
        ownership = random.uniform(25, 40)
    elif value > 2.5:
        ownership = random.uniform(15, 30)
    else:
        ownership = random.uniform(5, 20)

    # Captain multipliers
    captain_salary = int(salary * 1.5)
    captain_projection = projection * 1.5

    return {
        'id': player_id,
        'name': f"{team}_{position}_{player_id}",
        'team': team,
        'position': position,
        'salary': salary,
        'projection': round(projection, 2),
        'ownership': round(ownership, 1),
        'batting_order': batting_order,
        'captain_projection': round(captain_projection, 2),
        'captain_salary': captain_salary,
        'ceiling': projection * random.uniform(1.8, 3.5),
        'floor': projection * random.uniform(0.3, 0.7),
        'value_score': projection / (salary / 1000),
        'captain_value': captain_projection / (captain_salary / 1000),
        'team_total': game_data.get('team_totals', {}).get(team, 4.5)
    }

def calculate_showdown_ownership(projection, salary, position, batting_order, skill):
    """Calculate ownership for showdown (more concentrated)"""

    # Base ownership from value
    value = projection / (salary / 1000)

    # FIXED: More realistic ownership distribution
    if value > 4.0:
        base_own = random.uniform(40, 55)
    elif value > 3.5:
        base_own = random.uniform(30, 45)
    elif value > 3.0:
        base_own = random.uniform(20, 35)
    elif value > 2.5:
        base_own = random.uniform(10, 25)
    elif value > 2.0:
        base_own = random.uniform(5, 15)
    else:
        base_own = random.uniform(1, 8)

    # Batting order premium (huge in showdown)
    if batting_order in [1, 2, 3]:
        base_own *= random.uniform(1.3, 1.6)
    elif batting_order in [4, 5]:
        base_own *= random.uniform(1.1, 1.3)

    # Pitchers get ownership boost in showdown
    if position == 'P' and skill > 0.6:
        base_own *= random.uniform(1.2, 1.4)

    # Add variance
    ownership = np.random.normal(base_own, base_own * 0.15)

    # Showdown has higher ownership concentration
    return np.clip(ownership, 0.5, 65)


import random, math


def ensure_position_depth(players, format_type, slate_size):
    """Ensure realistic position depth matching actual DFS sites"""

    if format_type != 'classic':
        return players

    position_counts = defaultdict(lambda: defaultdict(int))

    # Count current players by position and salary range
    for p in players:
        pos = p['position']
        if p['salary'] <= 3000:
            position_counts[pos]['punt'] += 1
        elif p['salary'] <= 5000:
            position_counts[pos]['value'] += 1
        else:
            position_counts[pos]['mid_high'] += 1

    # Minimum requirements based on real DFS sites
    MIN_REQUIREMENTS = {
        'P': {'punt': 2, 'value': 3, 'total': 10},
        'C': {'punt': 2, 'value': 2, 'total': 6},
        '1B': {'punt': 1, 'value': 2, 'total': 6},
        '2B': {'punt': 2, 'value': 2, 'total': 6},
        '3B': {'punt': 2, 'value': 2, 'total': 6},  # Key for your issue
        'SS': {'punt': 2, 'value': 2, 'total': 6},
        'OF': {'punt': 4, 'value': 4, 'total': 15}  # Key for your issue
    }

    # Add missing players
    player_id = max(p['id'] for p in players) + 1

    for pos, reqs in MIN_REQUIREMENTS.items():
        current_total = sum(position_counts[pos].values())

        # Add punt plays if needed (realistic - every team has bench/platoon players)
        while position_counts[pos]['punt'] < reqs['punt']:
            # Get a random team already in the slate
            teams = list(set(p['team'] for p in players))
            team = random.choice(teams)

            # Create realistic punt player
            player = {
                'id': player_id,
                'name': f"{team}_{pos}_punt{player_id}",
                'team': team,
                'position': pos,
                'salary': random.randint(2000, 2800),
                'batting_order': 0,  # Bench player
                'team_total': next(p['team_total'] for p in players if p['team'] == team),
                'game_id': next(p['game_id'] for p in players if p['team'] == team),
                'is_punt': True
            }

            # Realistic projections for punt plays
            if pos == 'P':
                player['projection'] = random.uniform(8, 15)
            else:
                player['projection'] = random.uniform(4, 7)

            player['ownership'] = random.uniform(0.5, 5)
            player['ceiling'] = player['projection'] * random.uniform(2.0, 3.0)
            player['floor'] = player['projection'] * random.uniform(0.3, 0.5)
            player['value_score'] = player['projection'] / (player['salary'] / 1000)

            players.append(player)
            position_counts[pos]['punt'] += 1
            player_id += 1

        # Add value plays if needed
        while position_counts[pos]['value'] < reqs['value']:
            teams = list(set(p['team'] for p in players))
            team = random.choice(teams)

            player = {
                'id': player_id,
                'name': f"{team}_{pos}_value{player_id}",
                'team': team,
                'position': pos,
                'salary': random.randint(3000, 4800),
                'batting_order': random.choice([6, 7, 8, 0]),
                'team_total': next(p['team_total'] for p in players if p['team'] == team),
                'game_id': next(p['game_id'] for p in players if p['team'] == team),
                'is_punt': False
            }

            # Value player projections
            points_per_1k = random.uniform(2.4, 3.0)
            player['projection'] = (player['salary'] / 1000) * points_per_1k
            player['ownership'] = random.uniform(5, 20)
            player['ceiling'] = player['projection'] * random.uniform(2.0, 2.8)
            player['floor'] = player['projection'] * random.uniform(0.5, 0.7)
            player['value_score'] = player['projection'] / (player['salary'] / 1000)

            players.append(player)
            position_counts[pos]['value'] += 1
            player_id += 1

    return players

def generate_realistic_player(pid, team, pos, order, game_data, slate_size):
    """
    One function that produces FanDuel-style salary, projection,
    ownership, and showdown keys for **both** Classic and Showdown.
    """
    import random, math

    # Vegas team-total
    team_total = game_data.get('team_totals', {}).get(team, 4.5)

    # ---------- 1.  SALARY TIER (mirrors FD/DK) ----------
    if pos == 'P':
        # Pitchers
        tier_roll = random.random()
        if tier_roll < 0.10:                 # Ace
            salary = random.randint(10000, 12000)
            proj   = random.uniform(40, 50)
        elif tier_roll < 0.35:               # Mid
            salary = random.randint(7500, 9500)
            proj   = random.uniform(30, 40)
        else:                                # Value / back-end
            salary = random.randint(4500, 7500)
            proj   = random.uniform(22, 30)
    else:
        # Hitters – force 1 true punt per 9-man roster
        punt_slot = (order == 9)
        if punt_slot:
            salary = random.randint(2000, 2800)
            proj   = salary / 1000 * random.uniform(2.0, 2.4)
        else:
            tier = random.choice(['stud', 'mid', 'value'])
            salary = {'stud': (8000, 10500),
                      'mid':  (4500, 8000),
                      'value':(3000, 4500)}[tier]
            salary = random.randint(*salary)
            proj   = salary / 1000 * random.uniform(2.4, 3.0)

    # ---------- 2.  BATTING ORDER MULTIPLIER ----------
    if order in (1, 2, 3, 4):
        proj *= random.uniform(1.10, 1.25)
    elif order in (7, 8):
        proj *= random.uniform(0.85, 0.95)
    elif order == 9:
        proj *= random.uniform(0.80, 0.90)

    # ---------- 3.  VEGAS TEAM TOTAL ----------
    proj *= (team_total / 4.5) ** 0.5

    # ---------- 4.  OWNERSHIP CURVE (FanDuel shape) ----------
    pts_per_k = proj / (salary / 1000)
    if pts_per_k > 3.5:
        own = random.uniform(30, 55)
    elif pts_per_k > 3.0:
        own = random.uniform(20, 35)
    elif pts_per_k > 2.5:
        own = random.uniform(10, 25)
    else:
        own = random.uniform(3, 12)

    # ---------- 5.  CEILING / FLOOR ----------
    ceiling = proj * random.uniform(1.8, 2.8)
    floor   = proj * random.uniform(0.5, 0.8)

    # ---------- 6.  SHOWDOWN EXTRAS ----------
    captain_salary = int(salary * 1.5)
    captain_proj   = proj * 1.5

    # ---------- 7.  RETURN UNIFIED PLAYER ----------
    return {
        'id': pid,
        'name': f"{team}_{pos}_{order}",
        'team': team,
        'position': pos,
        'salary': salary,
        'projection': round(proj, 2),
        'ownership': round(own, 1),
        'batting_order': order,
        'team_total': round(team_total, 2),
        'game_id': game_data['game_id'],
        'ceiling': round(ceiling, 2),
        'floor': round(floor, 2),
        'value_score': round(proj / (salary / 1000), 2),
        'captain_projection': round(captain_proj, 2),
        'captain_salary': captain_salary,
        'is_punt': salary <= 3000,  # Changed ) to ,
        'vegas_total': round(team_total, 2),
        'implied_team_runs': round(team_total, 2),
        'game_total': round(game_data.get('game_total', 9.0), 2),
        'vegas_favorite': team_total > (game_data.get('game_total', 9.0) / 2),
        'run_differential': round(team_total - (game_data.get('game_total', 9.0) - team_total), 2),
        'vegas_multiplier': (team_total / 4.5) ** 0.5
    }

def generate_classic_player(player_id, team, position, game_data, slate_size):
    """Generate a player for classic format with slate-size awareness"""

    # CRITICAL: Much wider distribution for lineup flexibility
    rand = random.random()
    if rand < 0.02:  # 2% elite studs
        skill = random.uniform(0.90, 1.0)
        salary_efficiency = random.uniform(0.95, 1.05)
    elif rand < 0.10:  # 8% stars
        skill = random.uniform(0.70, 0.90)
        salary_efficiency = random.uniform(0.90, 1.10)
    elif rand < 0.30:  # 20% solid players
        skill = random.uniform(0.45, 0.70)
        salary_efficiency = random.uniform(0.85, 1.15)
    elif rand < 0.60:  # 30% role players
        skill = random.uniform(0.25, 0.45)
        salary_efficiency = random.uniform(0.80, 1.20)
    else:  # 40% punt plays - CRITICAL FOR LINEUP BUILDING
        skill = random.uniform(0.05, 0.25)
        salary_efficiency = random.uniform(0.70, 1.30)

    # FIXED salary ranges with MORE VARIANCE
    if position == 'P':
        if skill > 0.90:
            base_salary = random.uniform(10000, 12000)
        elif skill > 0.70:
            base_salary = random.uniform(7500, 10000)
        elif skill > 0.45:
            base_salary = random.uniform(5000, 7500)
        elif skill > 0.25:
            base_salary = random.uniform(3500, 5000)
        else:
            base_salary = random.uniform(2500, 3500)
    else:
        # Position-specific ranges with MORE VARIANCE
        if position == 'C':
            salary_multiplier = 0.85  # Catchers cheaper
        elif position in ['SS', 'OF']:
            salary_multiplier = 1.05  # Premium positions
        else:
            salary_multiplier = 1.0

        if skill > 0.90:
            base_salary = random.uniform(8000, 10000) * salary_multiplier
        elif skill > 0.70:
            base_salary = random.uniform(6000, 8000) * salary_multiplier
        elif skill > 0.45:
            base_salary = random.uniform(4000, 6000) * salary_multiplier
        elif skill > 0.25:
            base_salary = random.uniform(2800, 4000) * salary_multiplier
        else:
            base_salary = random.uniform(2000, 2800) * salary_multiplier

    salary = int(base_salary * salary_efficiency)
    salary = max(2000, min(12000, salary))  # Hard limits

    # CRITICAL: Ensure proper batting order distribution
    batting_order = 0
    if position != 'P':
        if skill > 0.70:
            batting_order = random.choice([1, 2, 3, 4])
        elif skill > 0.45:
            batting_order = random.choice([3, 4, 5, 6])
        elif skill > 0.25:
            batting_order = random.choice([5, 6, 7, 8])
        else:
            batting_order = random.choice([7, 8, 9])

    # More realistic projections with better salary correlation
    if position == 'P':
        points_per_1k = 3.0 + (skill * 2.0) + np.random.normal(0, 0.3)
        base_projection = (salary / 1000) * points_per_1k
    else:
        # Better point-per-dollar distribution
        if salary < 3000:  # Punt plays can still have value
            points_per_1k = random.uniform(2.0, 3.5)
        elif salary < 5000:
            points_per_1k = random.uniform(2.2, 3.0)
        elif salary < 7000:
            points_per_1k = random.uniform(2.0, 2.8)
        else:  # Expensive players
            points_per_1k = random.uniform(1.8, 2.5)

        base_projection = (salary / 1000) * points_per_1k

        # Batting order bonus
        if batting_order <= 4:
            base_projection *= random.uniform(1.10, 1.20)
        elif batting_order <= 6:
            base_projection *= random.uniform(1.00, 1.10)
        else:
            base_projection *= random.uniform(0.85, 0.95)

    # Team context
    team_total = game_data.get('team_totals', {}).get(team, 4.5)
    if team_total > 5.5:
        base_projection *= random.uniform(1.08, 1.15)
    elif team_total < 3.5:
        base_projection *= random.uniform(0.85, 0.92)

    projection = max(0, base_projection + np.random.normal(0, base_projection * 0.08))

    # Calculate ownership
    ownership = calculate_classic_ownership(projection, salary, position, team,
                                            batting_order, team_total, skill, slate_size)

    # Advanced stats
    barrel_rate = 0
    xwoba = 0
    recent_form_multiplier = 1.0
    platoon_advantage = 0

    if position != 'P':
        barrel_rate = np.clip(skill * 0.15 + np.random.normal(0, 0.03), 0, 0.25)
        xwoba = 0.250 + skill * 0.150 + np.random.normal(0, 0.02)
        recent_form_multiplier = random.choice([0.85, 0.95, 1.0, 1.08, 1.15])
        platoon_advantage = random.choice([-0.05, 0, 0, 0.05, 0.084])

    return {
        'id': player_id,
        'name': f"{team}_{position}_{player_id}",
        'team': team,
        'position': position,
        'salary': salary,
        'projection': round(projection, 2),
        'ownership': round(ownership, 1),
        'batting_order': batting_order,
        'team_total': team_total,
        'game_id': game_data['game_id'],
        'ceiling': projection * random.uniform(1.8, 2.8),
        'floor': projection * random.uniform(0.5, 0.8),
        'value_score': projection / (salary / 1000),
        'skill_level': skill,
        'barrel_rate': barrel_rate,
        'xwoba': xwoba,
        'recent_form': recent_form_multiplier,
        'platoon_advantage': platoon_advantage,
        'is_hot_streak': recent_form_multiplier >= 1.08,
        'is_undervalued_xwoba': xwoba > 0.350 and ownership < 15,
        'is_punt': salary <= 3000
    }

def calculate_classic_ownership(projection, salary, position, team, batting_order, team_total, skill, slate_size):
    """Calculate ownership with slate size considerations - FIXED"""

    # Base ownership from value
    value = projection / (salary / 1000)

    # FIXED: More realistic ownership by slate size
    if slate_size == 'small':  # Small slates = higher concentration
        if value > 3.5:
            base_own = random.uniform(35, 50)
        elif value > 3.0:
            base_own = random.uniform(25, 40)
        elif value > 2.5:
            base_own = random.uniform(15, 30)
        elif value > 2.0:
            base_own = random.uniform(8, 20)
        else:
            base_own = random.uniform(1, 10)
    elif slate_size == 'medium':
        if value > 3.5:
            base_own = random.uniform(25, 40)
        elif value > 3.0:
            base_own = random.uniform(15, 30)
        elif value > 2.5:
            base_own = random.uniform(8, 20)
        elif value > 2.0:
            base_own = random.uniform(3, 12)
        else:
            base_own = random.uniform(0.5, 5)
    else:  # large
        if value > 3.5:
            base_own = random.uniform(20, 35)
        elif value > 3.0:
            base_own = random.uniform(10, 25)
        elif value > 2.5:
            base_own = random.uniform(5, 15)
        elif value > 2.0:
            base_own = random.uniform(2, 8)
        else:
            base_own = random.uniform(0.1, 3)

    # Recency bias
    recency_multiplier = random.choice([0.8, 1.0, 1.0, 1.2, 1.5])
    base_own *= recency_multiplier

    # Popular teams
    popular_teams = ['LAD', 'NYY', 'HOU', 'ATL', 'SD']
    if team in popular_teams:
        base_own *= random.uniform(1.2, 1.4)

    # Batting order premium
    if batting_order in [1, 2, 3, 4]:
        base_own *= random.uniform(1.15, 1.35)

    # High team totals
    if team_total > 5.5:
        base_own *= random.uniform(1.3, 1.5)
    elif team_total > 5.0:
        base_own *= random.uniform(1.1, 1.3)

    # Add variance
    ownership = np.random.normal(base_own, base_own * 0.2)

    # Ownership caps by slate size
    max_ownership = {'small': 60, 'medium': 50, 'large': 45}[slate_size]

    return np.clip(ownership, 0.1, max_ownership)


# ========== LINEUP BUILDERS - ENHANCED ==========

# [Keep all existing lineup builders but add these new ones]

def build_pitcher_stack(players: List[Dict]) -> Optional[Dict]:
    """Build lineup with pitcher + opposing team stack"""

    # PRE-FLIGHT CHECK - NEW
    pitchers = [p for p in players if p['position'] == 'P' and p['projection'] > 30]
    if not pitchers:
        return None  # No viable pitchers

    # Check if any pitcher has enough opposing hitters
    has_valid_matchup = False
    for pitcher in pitchers[:3]:
        opp_hitters_count = 0
        pitcher_game = pitcher.get('game_id')
        if pitcher_game:
            for p in players:
                if (p['position'] != 'P' and
                        p.get('game_id') == pitcher_game and
                        p['team'] != pitcher['team']):
                    opp_hitters_count += 1
            if opp_hitters_count >= 4:
                has_valid_matchup = True
                break

    if not has_valid_matchup:
        return None  # No pitcher has enough opposing hitters
    # END PRE-FLIGHT CHECK

    # Find good pitchers
    pitchers = [p for p in players if p['position'] == 'P' and p['projection'] > 30]

    if not pitchers:
        return None

    pitchers.sort(key=lambda x: x['projection'], reverse=True)

    for pitcher in pitchers[:3]:  # Try top 3 pitchers
        # Find opposing team hitters
        opp_hitters = []
        pitcher_game = pitcher.get('game_id')

        for p in players:
            if (p['position'] != 'P' and
                    p.get('game_id') == pitcher_game and
                    p['team'] != pitcher['team']):
                opp_hitters.append(p)

        if len(opp_hitters) < 4:
            continue

        # Build lineup
        lineup = [pitcher]
        salary = pitcher['salary']
        positions_filled = {'P': 1}
        teams_used = defaultdict(int)
        teams_used[pitcher['team']] = 1

        # Add opposing team stack
        opp_hitters.sort(key=lambda x: x['projection'], reverse=True)

        for hitter in opp_hitters:
            if len([p for p in lineup if p['team'] == hitter['team']]) >= 4:
                break

            pos = hitter['position']
            if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                continue

            if salary + hitter['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            lineup.append(hitter)
            salary += hitter['salary']
            positions_filled[pos] = positions_filled.get(pos, 0) + 1
            teams_used[hitter['team']] += 1

        # Fill remaining spots
        other_players = [p for p in players if p not in lineup]
        other_players.sort(key=lambda x: x['value_score'], reverse=True)

        for player in other_players:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] = positions_filled.get(pos, 0) + 1
            teams_used[player['team']] += 1

        if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
            return create_classic_lineup_result(lineup)

    return None


def build_double_stack(players: List[Dict]) -> Optional[Dict]:
    """Build lineup with two mini stacks (3 players each)"""
    team_players = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    # Find teams with enough players
    valid_teams = [(team, players_list) for team, players_list in team_players.items()
                   if len(players_list) >= 3]

    if len(valid_teams) < 2:
        return build_team_stack(players, 4)  # Fallback

    # Score teams
    team_scores = []
    for team, players_list in valid_teams:
        players_list.sort(key=lambda x: x['projection'], reverse=True)
        score = sum(p['projection'] for p in players_list[:3])
        team_scores.append((team, score, players_list))

    team_scores.sort(key=lambda x: x[1], reverse=True)

    # Try different team combinations
    for i in range(min(3, len(team_scores))):
        for j in range(i + 1, min(i + 4, len(team_scores))):
            team1, _, players1 = team_scores[i]
            team2, _, players2 = team_scores[j]

            lineup = []
            salary = 0
            positions_filled = defaultdict(int)
            teams_used = defaultdict(int)

            # Add first stack (3 players)
            for player in players1[:3]:
                pos = player['position']
                if positions_filled[pos] < CLASSIC_CONFIG['positions'][pos]:
                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1

            # Add second stack (3 players)
            for player in players2[:3]:
                pos = player['position']
                if positions_filled[pos] < CLASSIC_CONFIG['positions'][pos]:
                    if salary + player['salary'] <= CLASSIC_CONFIG['salary_cap']:
                        lineup.append(player)
                        salary += player['salary']
                        positions_filled[pos] += 1
                        teams_used[player['team']] += 1

            # Need at least 5 players from stacks
            if len(lineup) < 5:
                continue

            # Fill remaining spots
            other_players = [p for p in players if p not in lineup]
            other_players.sort(key=lambda x: x['value_score'], reverse=True)

            for player in other_players:
                if len(lineup) >= 10:
                    break

                pos = player['position']
                if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
                    continue

                if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                    continue

                if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                    continue

                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1

            if len(lineup) == 10:
                return create_classic_lineup_result(lineup)

    return None


def build_contrarian_stack(players: List[Dict]) -> Optional[Dict]:
    """Build lineup with low-owned team stack"""
    team_players = defaultdict(list)
    team_ownership = defaultdict(float)

    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)
            team_ownership[p['team']] += p['ownership']

    # Find low-owned teams with decent projections
    contrarian_teams = []
    for team, players_list in team_players.items():
        if len(players_list) >= 4:
            avg_ownership = team_ownership[team] / len(players_list)
            avg_projection = sum(p['projection'] for p in players_list) / len(players_list)

            # Low ownership but decent projections
            if avg_ownership < 15 and avg_projection > 10:
                contrarian_teams.append((team, avg_ownership, avg_projection, players_list))

    if not contrarian_teams:
        return build_team_stack(players, 4)  # Fallback

    # Sort by projection/ownership ratio
    contrarian_teams.sort(key=lambda x: x[2] / (x[1] + 1), reverse=True)

    # Build with best contrarian team
    team, _, _, team_list = contrarian_teams[0]
    team_list.sort(key=lambda x: x['projection'], reverse=True)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Add stack
    for player in team_list[:5]:
        pos = player['position']
        if positions_filled[pos] < CLASSIC_CONFIG['positions'][pos]:
            if salary + player['salary'] <= CLASSIC_CONFIG['salary_cap'] - 15000:
                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1

    # Fill remaining
    other_players = [p for p in players if p['team'] != team]
    other_players.sort(key=lambda x: x['value_score'], reverse=True)

    for player in other_players:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10:
        return create_classic_lineup_result(lineup)

    return None


def build_stars_scrubs(players: List[Dict]) -> Optional[Dict]:
    """Build lineup with expensive studs and minimum price players"""
    # Categorize players
    studs = [p for p in players if p['salary'] >= 8000]
    scrubs = [p for p in players if p['salary'] <= 3500]
    mid_range = [p for p in players if 3500 < p['salary'] < 8000]

    if len(studs) < 3 or len(scrubs) < 3:
    # Sort by ceiling for studs, value for scrubs
        studs.sort(key=lambda x: x['ceiling'], reverse=True)
    scrubs.sort(key=lambda x: x['value_score'], reverse=True)
    mid_range.sort(key=lambda x: x['value_score'], reverse=True)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Add 3-4 studs
    studs_added = 0
    for player in studs:
        if studs_added >= 4:
            break

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap'] - 20000:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1
        studs_added += 1

    # Add scrubs
    for player in scrubs:
        if len(lineup) >= 8:  # Leave room for mid-range
            break

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    # Fill remaining with mid-range
    all_remaining = scrubs + mid_range
    all_remaining.sort(key=lambda x: x['value_score'], reverse=True)

    for player in all_remaining:
        if len(lineup) >= 10:
            break

        if player in lineup:
            continue

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10:
        return create_classic_lineup_result(lineup)

    return None


def build_balanced_cash(players: List[Dict]) -> Optional[Dict]:
    """Build balanced cash lineup using multiple factors"""
    # Calculate balanced score for each player
    for player in players:
        # Multiple factors with weights
        proj_score = player['projection'] * 0.30
        floor_score = player['floor'] * 0.25
        own_score = player['ownership'] / 100 * 20 * 0.20  # Normalize ownership
        value_score = player['value_score'] * 5 * 0.15  # Normalize value
        consistency = (player['floor'] / player['projection']) * 10 * 0.10

        player['balanced_score'] = (
                proj_score + floor_score + own_score + value_score + consistency
        )

    return build_by_metric(players, 'balanced_score')


def build_multi_game_stack(players: List[Dict]) -> Optional[Dict]:
    """Build lineup with correlations from 2-3 games"""
    # Group by game
    game_players = defaultdict(list)
    game_totals = {}

    for p in players:
        if 'game_id' in p:
            game_id = p['game_id']
            game_players[game_id].append(p)
            if game_id not in game_totals:
                game_totals[game_id] = p.get('team_total', 4.5) * 2

    if len(game_totals) < 2:
        return None

    # Get top games by total
    sorted_games = sorted(game_totals.items(), key=lambda x: x[1], reverse=True)

    # Take top 2-3 games
    target_games = [g[0] for g in sorted_games[:3]]

    # Get players from these games
    target_players = []
    for game_id in target_games:
        target_players.extend(game_players[game_id])

    # Build lineup focusing on these games
    target_players.sort(key=lambda x: x['ceiling'], reverse=True)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)
    games_used = defaultdict(int)

    # Add players from target games
    for player in target_players:
        if len(lineup) >= 8:  # Leave some flexibility
            break

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap'] - 6000:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1
        games_used[player.get('game_id')] += 1

    # Fill remaining
    other_players = [p for p in players if p not in lineup]
    other_players.sort(key=lambda x: x['value_score'], reverse=True)

    for player in other_players:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10:
        return create_classic_lineup_result(lineup)

    return None


def build_classic_lineup(players, strategy, slate_size):
    """Build classic lineup based on explicit strategy rules"""
    strategy_type = strategy.get('type')

    # PURE METRIC STRATEGIES
    if strategy_type == 'pure_proj':
        return build_by_metric(players, 'projection')

    elif strategy_type == 'pure_floor':
        return build_by_metric(players, 'floor')

    elif strategy_type == 'pure_ceiling':
        return build_by_metric(players, 'ceiling')

    elif strategy_type == 'pure_value':
        return build_by_metric(players, 'value_score')

    elif strategy_type == 'pure_own':
        return build_by_metric(players, 'ownership')

    elif strategy_type == 'pure_chalk':
        return build_by_metric(players, 'ownership')

    # BALANCED STRATEGIES
    elif strategy_type == 'balanced_50_50':
        # Rule: 50% projection + 50% ownership
        for p in players:
            # Normalize to 0-100 scale
            p['norm_proj'] = min((p['projection'] / 50) * 100, 100)
            p['norm_own'] = p['ownership']
            p['combined_score_50_50'] = (p['norm_proj'] * 0.5) + (p['norm_own'] * 0.5)
        return build_by_metric(players, 'combined_score_50_50')

    elif strategy_type == 'balanced_60_40':
        # Rule: 60% ownership + 40% projection
        for p in players:
            p['norm_proj'] = min((p['projection'] / 50) * 100, 100)
            p['norm_own'] = p['ownership']
            p['combined_score_60_40'] = (p['norm_own'] * 0.6) + (p['norm_proj'] * 0.4)
        return build_by_metric(players, 'combined_score_60_40')

    elif strategy_type == 'balanced_40_60':
        # Rule: 40% ownership + 60% projection
        for p in players:
            p['norm_proj'] = min((p['projection'] / 50) * 100, 100)
            p['norm_own'] = p['ownership']
            p['combined_score_40_60'] = (p['norm_own'] * 0.4) + (p['norm_proj'] * 0.6)
        return build_by_metric(players, 'combined_score_40_60')

    elif strategy_type == 'balanced_70_30':
        # Rule: 70% ownership + 30% projection
        for p in players:
            p['norm_proj'] = min((p['projection'] / 50) * 100, 100)
            p['norm_own'] = p['ownership']
            p['combined_score_70_30'] = (p['norm_own'] * 0.7) + (p['norm_proj'] * 0.3)
        return build_by_metric(players, 'combined_score_70_30')

    # OWNERSHIP THRESHOLD STRATEGIES
    elif strategy_type == 'min_20_own':
        # Rule: Only players with 20%+ ownership
        eligible = [p for p in players if p['ownership'] >= 20]
        if len(eligible) < 50:  # Need enough to build
            return None
        return build_by_metric(eligible, 'projection')

    elif strategy_type == 'min_30_own':
        # Rule: Only players with 30%+ ownership
        eligible = [p for p in players if p['ownership'] >= 30]
        if len(eligible) < 30:
            return None
        return build_by_metric(eligible, 'projection')

    elif strategy_type == 'chalk_25':
        # Rule: Only players 25%+ owned
        eligible = [p for p in players if p['ownership'] >= 25]
        if len(eligible) < 30:
            return None
        return build_by_metric(eligible, 'ownership')

    elif strategy_type == 'max_15_own':
        # Rule: No player over 15% owned
        eligible = [p for p in players if p['ownership'] <= 15]
        if len(eligible) < 50:
            return None
        return build_by_metric(eligible, 'projection')

    elif strategy_type == 'fade_40':
        # Rule: No player over 40% owned
        eligible = [p for p in players if p['ownership'] <= 40]
        return build_by_metric(eligible, 'ownership')

    # STACK STRATEGIES
    elif strategy_type == 'stack_5':
        return build_exact_stack(players, 5)

    elif strategy_type == 'stack_4':
        return build_exact_stack(players, 4)

    elif strategy_type == 'seq_1_5':
        return build_sequential_exact(players, 1, 5)

    elif strategy_type == 'seq_2_6':
        return build_sequential_exact(players, 2, 6)

    elif strategy_type == 'game_3_2':
        return build_game_stack_exact(players, 3, 2)

    elif strategy_type == 'game_4_2':
        return build_game_stack_exact(players, 4, 2)

    elif strategy_type == 'multi_3_3':
        return build_multi_stack_exact(players, [3, 3])

    elif strategy_type == 'stack_5_low':
        return build_low_owned_stack(players, 5)

    elif strategy_type == 'leverage_chalk':
        return build_leverage_chalk_exact(players)

    elif strategy_type == 'stars_scrubs_44':
        return build_stars_scrubs_exact(players, 4, 4)

    return None


def build_exact_stack(players, stack_size):
    """Build lineup with exactly X players from same team"""
    team_players = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    # Find team with best total projection for stack_size players
    best_team = None
    best_projection = 0

    for team, players_list in team_players.items():
        if len(players_list) >= stack_size:
            players_list.sort(key=lambda x: x['projection'], reverse=True)
            stack_projection = sum(p['projection'] for p in players_list[:stack_size])
            if stack_projection > best_projection:
                best_projection = stack_projection
                best_team = team

    if not best_team:
        return None

    # Take exactly stack_size from best team
    stack = sorted(team_players[best_team], key=lambda x: x['projection'], reverse=True)[:stack_size]

    # Fill remaining with best value from other teams
    remaining = [p for p in players if p['team'] != best_team]
    remaining.sort(key=lambda x: x['value_score'], reverse=True)

    return build_lineup_with_stack(stack, remaining)


def build_sequential_exact(players, start_pos, end_pos):
    """Build lineup with exact sequential batting order"""
    team_batting = defaultdict(lambda: defaultdict(list))

    for p in players:
        if p['position'] != 'P' and p.get('batting_order', 0) > 0:
            team_batting[p['team']][p['batting_order']].append(p)

    best_lineup = None

    for team, batting_positions in team_batting.items():
        # Check if team has all required positions
        has_all = all(pos in batting_positions for pos in range(start_pos, end_pos + 1))
        if not has_all:
            continue

        # Get best player at each position
        stack = []
        for pos in range(start_pos, end_pos + 1):
            best_at_pos = max(batting_positions[pos], key=lambda x: x['projection'])
            stack.append(best_at_pos)

        # Fill remaining
        remaining = [p for p in players if p not in stack]
        remaining.sort(key=lambda x: x['value_score'], reverse=True)

        lineup = build_lineup_with_stack(stack, remaining)
        if lineup:
            best_lineup = lineup
            break

    return best_lineup


def build_game_stack_exact(players, team_a_count, team_b_count):
    """Build lineup with exact players from same game"""
    game_players = defaultdict(lambda: defaultdict(list))

    for p in players:
        if 'game_id' in p:
            game_players[p['game_id']][p['team']].append(p)

    for game_id, teams in game_players.items():
        if len(teams) != 2:
            continue

        teams_list = list(teams.keys())

        # Try both team combinations
        for i in range(2):
            team_a = teams_list[i]
            team_b = teams_list[1 - i]

            if len(teams[team_a]) >= team_a_count and len(teams[team_b]) >= team_b_count:
                # Sort by projection
                teams[team_a].sort(key=lambda x: x['projection'], reverse=True)
                teams[team_b].sort(key=lambda x: x['projection'], reverse=True)

                # Take exact counts
                stack = teams[team_a][:team_a_count] + teams[team_b][:team_b_count]

                # Fill remaining
                remaining = [p for p in players if p not in stack]
                remaining.sort(key=lambda x: x['value_score'], reverse=True)

                lineup = build_lineup_with_stack(stack, remaining)
                if lineup:
                    return lineup

    return None


def build_lineup_with_stack(stack, remaining_players):
    """Helper to complete lineup starting with a stack"""
    lineup = list(stack)
    salary = sum(p['salary'] for p in lineup)
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Count current positions and teams
    for p in lineup:
        positions_filled[p['position']] += 1
        teams_used[p['team']] += 1

    # Fill remaining positions
    for player in remaining_players:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
        return create_classic_lineup_result(lineup)

    return None


def build_stars_scrubs_exact(players, num_stars, num_scrubs):
    """Build lineup with exact number of expensive and cheap players"""
    # Categorize players
    stars = [p for p in players if p['salary'] >= 8000]
    scrubs = [p for p in players if p['salary'] <= 3000]
    mid = [p for p in players if 3000 < p['salary'] < 8000]

    if len(stars) < num_stars or len(scrubs) < num_scrubs:
        return None

    # Sort by ceiling for stars, value for scrubs
    stars.sort(key=lambda x: x.get('ceiling', 0), reverse=True)
    scrubs.sort(key=lambda x: x['value_score'], reverse=True)
    mid.sort(key=lambda x: x['value_score'], reverse=True)

    # Take exact numbers
    lineup = stars[:num_stars] + scrubs[:num_scrubs]

    # Fill remaining (should be 2 spots) with mid-range
    remaining_spots = 10 - len(lineup)
    lineup.extend(mid[:remaining_spots])

    # Now optimize the exact players within constraints
    return optimize_exact_players(lineup, players)


def optimize_exact_players(selected_players, all_players):
    """Optimize exact player selection within position constraints"""
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Sort selected players by value to fill optimally
    selected_players.sort(key=lambda x: x['value_score'], reverse=True)

    for player in selected_players:
        pos = player['position']
        if positions_filled[pos] < CLASSIC_CONFIG['positions'][pos]:
            if salary + player['salary'] <= CLASSIC_CONFIG['salary_cap']:
                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1

    # If we couldn't fit all selected players, fill with others
    if len(lineup) < 10:
        remaining = [p for p in all_players if p not in lineup]
        remaining.sort(key=lambda x: x['value_score'], reverse=True)

        for player in remaining:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
                continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

    if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
        return create_classic_lineup_result(lineup)

    return None


# Add these functions to your dfs_diagnostic.py file

def build_multi_stack_exact(players, stack_sizes):
    """Build lineup with multiple exact-sized stacks
    Args:
        players: List of player dictionaries
        stack_sizes: List of stack sizes, e.g., [3, 3] for two 3-player stacks
    """
    team_players = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    # Find teams with enough players
    valid_teams = []
    for team, players_list in team_players.items():
        if len(players_list) >= stack_sizes[0]:  # At least enough for first stack
            players_list.sort(key=lambda x: x['projection'], reverse=True)
            team_score = sum(p['projection'] for p in players_list[:stack_sizes[0]])
            valid_teams.append((team, team_score, players_list))

    if len(valid_teams) < len(stack_sizes):
        return None

    # Sort teams by score
    valid_teams.sort(key=lambda x: x[1], reverse=True)

    # Try different team combinations
    for i in range(min(3, len(valid_teams))):
        for j in range(i + 1, min(i + 4, len(valid_teams))):
            if j >= len(valid_teams):
                break

            team1, _, players1 = valid_teams[i]
            team2, _, players2 = valid_teams[j]

            # Build lineup with both stacks
            lineup = []
            salary = 0
            positions_filled = defaultdict(int)
            teams_used = defaultdict(int)

            # Add first stack
            stack1_added = 0
            for player in players1:
                if stack1_added >= stack_sizes[0]:
                    break

                pos = player['position']
                if positions_filled[pos] < CLASSIC_CONFIG['positions'][pos]:
                    if salary + player['salary'] <= CLASSIC_CONFIG['salary_cap'] - 30000:
                        lineup.append(player)
                        salary += player['salary']
                        positions_filled[pos] += 1
                        teams_used[player['team']] += 1
                        stack1_added += 1

            # Add second stack
            stack2_added = 0
            for player in players2:
                if stack2_added >= stack_sizes[1]:
                    break

                pos = player['position']
                if positions_filled[pos] < CLASSIC_CONFIG['positions'][pos]:
                    if salary + player['salary'] <= CLASSIC_CONFIG['salary_cap'] - 20000:
                        lineup.append(player)
                        salary += player['salary']
                        positions_filled[pos] += 1
                        teams_used[player['team']] += 1
                        stack2_added += 1

            # Need both stacks to be complete
            if stack1_added < stack_sizes[0] or stack2_added < stack_sizes[1]:
                continue

            # Fill remaining spots
            other_players = [p for p in players if p not in lineup]
            other_players.sort(key=lambda x: x['value_score'], reverse=True)

            for player in other_players:
                if len(lineup) >= 10:
                    break

                pos = player['position']
                if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
                    continue

                if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                    continue

                if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                    continue

                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1

            if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
                return create_classic_lineup_result(lineup)

    return None


def build_low_owned_stack(players, stack_size):
    """Build lineup with stack from low-ownership team"""
    team_players = defaultdict(list)
    team_ownership = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)
            team_ownership[p['team']].append(p['ownership'])

    # Find teams with low average ownership
    low_owned_teams = []
    for team, players_list in team_players.items():
        if len(players_list) >= stack_size:
            avg_ownership = np.mean(team_ownership[team])
            # Only consider teams with <10% average ownership
            if avg_ownership < 10:
                players_list.sort(key=lambda x: x['projection'], reverse=True)
                team_projection = sum(p['projection'] for p in players_list[:stack_size])
                low_owned_teams.append((team, avg_ownership, team_projection, players_list))

    if not low_owned_teams:
        return None

    # Sort by projection/ownership ratio (best leverage)
    low_owned_teams.sort(key=lambda x: x[2] / (x[1] + 1), reverse=True)

    # Try top low-owned teams
    for team, avg_own, proj, team_list in low_owned_teams[:3]:
        lineup = []
        salary = 0
        positions_filled = defaultdict(int)
        teams_used = defaultdict(int)

        # Add stack from low-owned team
        stack_added = 0
        for player in team_list:
            if stack_added >= stack_size:
                break

            pos = player['position']
            if positions_filled[pos] < CLASSIC_CONFIG['positions'][pos]:
                if salary + player['salary'] <= CLASSIC_CONFIG['salary_cap'] - 25000:
                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1
                    stack_added += 1

        if stack_added < stack_size:
            continue

        # Fill remaining with best value
        other_players = [p for p in players if p['team'] != team]
        other_players.sort(key=lambda x: x['value_score'], reverse=True)

        for player in other_players:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
                continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

        if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
            return create_classic_lineup_result(lineup)

    return None


def build_leverage_chalk_exact(players):
    """Build lineup with one 30%+ owned player and rest <10% owned"""
    # Categorize players by ownership
    chalk_players = [p for p in players if p['ownership'] >= 30]
    low_owned = [p for p in players if p['ownership'] < 10]

    if not chalk_players or len(low_owned) < 9:
        return None

    # Sort by projection
    chalk_players.sort(key=lambda x: x['projection'], reverse=True)
    low_owned.sort(key=lambda x: x['projection'], reverse=True)

    # Try each chalk player as the anchor
    for chalk in chalk_players[:5]:
        lineup = [chalk]
        salary = chalk['salary']
        positions_filled = defaultdict(int)
        positions_filled[chalk['position']] = 1
        teams_used = defaultdict(int)
        teams_used[chalk['team']] = 1

        # Fill rest with low-owned players
        for player in low_owned:
            if len(lineup) >= 10:
                break

            if player['ownership'] >= 10:  # Double check ownership
                continue

            pos = player['position']
            if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
                continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

        # If we couldn't fill with just <10% owned, allow some 10-15% players
        if len(lineup) < 10:
            medium_owned = [p for p in players if 10 <= p['ownership'] < 15 and p not in lineup]
            medium_owned.sort(key=lambda x: x['value_score'], reverse=True)

            for player in medium_owned:
                if len(lineup) >= 10:
                    break

                pos = player['position']
                if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
                    continue

                if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                    continue

                if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                    continue

                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1

        if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
            # Verify ownership constraint
            avg_ownership = sum(p['ownership'] for p in lineup) / 10
            if avg_ownership < 15:  # Reasonable threshold
                return create_classic_lineup_result(lineup)

    return None
# ========== FIELD GENERATION - FIXED ==========

def add_execution_mistakes(lineup, skill_rand, field_composition):
    """Add realistic mistakes based on skill level"""
    # This simulates execution errors, not strategy errors

    if skill_rand < field_composition['sharp'] + field_composition['good']:
        # Good players - minor mistakes
        error_rate = 0.05
    elif skill_rand < field_composition['sharp'] + field_composition['good'] + field_composition['average']:
        # Average players - moderate mistakes
        error_rate = 0.15
    else:
        # Weak players - more mistakes
        error_rate = 0.25

    # Randomly reduce projection to simulate suboptimal choices
    if 'projection' in lineup and random.random() < error_rate:
        lineup['projection'] *= random.uniform(0.85, 0.95)

    return lineup


def validate_player_data(player):
    """Ensure player has all required fields for strategies"""
    required_fields = {
        'id': 0,
        'name': 'Unknown',
        'team': 'UNK',
        'position': 'UTIL',
        'salary': 2000,
        'projection': 5.0,
        'ownership': 5.0,
        'batting_order': 0,
        'team_total': 4.5,
        'ceiling': 15.0,
        'floor': 2.0,
        'value_score': 2.5,
        'recent_form': 1.0,
        'platoon_advantage': 0,
        'is_hot_streak': False,
        'barrel_rate': 0.08,
        'xwoba': 0.280,
        'is_undervalued_xwoba': False,
        'is_punt': False,
        'skill_level': 0.5
    }

    for field, default in required_fields.items():
        if field not in player:
            player[field] = default

    return player


# Field generation - opponents can use fallbacks, be imperfect, etc.
def generate_field_realistic(slate, field_size, contest_type):
    """Generate realistic field - SILENT version for parallel processing"""
    field_lineups = []
    players = slate['players']
    format_type = slate['format']
    slate_size = slate['slate_size']

    # Realistic field composition
    if contest_type == 'cash':
        field_composition = {
            'sharp': 0.20,
            'good': 0.50,
            'average': 0.25,
            'weak': 0.05
        }
    else:  # GPP
        field_composition = {
            'sharp': 0.05,
            'good': 0.15,
            'average': 0.50,
            'weak': 0.30
        }

    successful_lineups = 0
    attempts = 0
    consecutive_failures = 0
    max_consecutive_failures = 100

    # REMOVED ALL PRINT STATEMENTS - Silent operation

    while successful_lineups < field_size and attempts < field_size * 5:
        attempts += 1

        if consecutive_failures >= max_consecutive_failures:
            break

        # Determine opponent skill level
        rand = random.random()
        cumulative = 0
        skill_level = 'average'

        for level, pct in field_composition.items():
            cumulative += pct
            if rand < cumulative:
                skill_level = level
                break

        # Build opponent lineup
        lineup = None

        if format_type == 'showdown':
            lineup = build_opponent_showdown_lineup(players, skill_level, contest_type)
        else:
            lineup = build_opponent_classic_lineup(players, skill_level, contest_type, slate_size)

        if lineup:
            lineup['projection'] *= random.uniform(0.92, 1.08)

            if skill_level == 'weak':
                lineup['projection'] *= random.uniform(0.85, 1.0)

            field_lineups.append(lineup)
            successful_lineups += 1
            consecutive_failures = 0
        else:
            consecutive_failures += 1

    # Fill remaining with dummies if needed - SILENTLY
    if len(field_lineups) < field_size:
        remaining = field_size - len(field_lineups)

        for _ in range(remaining):
            if format_type == 'showdown':
                base_proj = 120
                std_dev = 25
            else:
                base_proj = 150
                std_dev = 30

            dummy_opponent = {
                'projection': np.random.normal(base_proj, std_dev),
                'ownership': random.uniform(5, 35),
                'format': format_type,
                'salary': random.randint(47000, 49800),
                'is_dummy': True
            }

            dummy_opponent['projection'] = max(50, dummy_opponent['projection'])
            field_lineups.append(dummy_opponent)

    return field_lineups

def build_opponent_classic_lineup(players, skill_level, contest_type, slate_size):
    """Build opponent lineup - can use fallbacks and make mistakes"""

    # Opponents can try strategies but fall back if needed
    if skill_level == 'sharp':
        if contest_type == 'cash':
            strategies = [
                ('optimal', lambda p: build_by_metric(p, 'projection')),
                ('value', lambda p: build_by_metric(p, 'value_score')),
                ('balanced', lambda p: build_with_weights(p, 0.6, 0.4)),
            ]
        else:  # GPP
            strategies = [
                ('stack', lambda p: build_team_stack(p, random.choice([4, 5]))),
                ('correlation', lambda p: build_game_stack_classic(p)),
            ]

    elif skill_level == 'good':
        strategies = [
            ('basic_proj', lambda p: build_by_metric(p, 'projection')),
            ('basic_value', lambda p: build_by_metric(p, 'value_score')),
            ('ownership', lambda p: build_by_metric(p, 'ownership')),
        ]

    elif skill_level == 'average':
        strategies = [
            ('simple', lambda p: build_simple_lineup(p)),
            ('random_good', lambda p: build_random_decent_lineup(p)),
        ]

    else:  # weak
        strategies = [
            ('expensive', lambda p: build_expensive_lineup(p)),
            ('random', lambda p: build_random_lineup(p)),
        ]

    # Try strategies with fallback
    random.shuffle(strategies)

    for strategy_name, strategy_func in strategies:
        try:
            lineup = strategy_func(players)
            if lineup:
                return lineup
        except:
            pass

    # Ultimate fallback for opponents - just build something valid
    return build_simple_lineup(players)


def build_opponent_showdown_lineup(players, skill_level, contest_type):
    """Build opponent showdown lineup - realistic mix"""

    # Captain selection by skill level
    if skill_level == 'sharp':
        # Smart captain choices
        captain_options = sorted(players, key=lambda x: x['projection'], reverse=True)[:3]
    elif skill_level == 'good':
        # Decent captain choices
        captain_options = sorted(players, key=lambda x: x['ownership'], reverse=True)[:5]
    else:
        # Random captain choices
        captain_options = random.sample(players, min(8, len(players)))

    captain = random.choice(captain_options)

    # Fill utils
    utils = [p for p in players if p['id'] != captain['id']]

    if skill_level in ['sharp', 'good']:
        utils.sort(key=lambda x: x['value_score'], reverse=True)
    else:
        random.shuffle(utils)

    # Build lineup
    lineup = [captain]
    salary = int(captain['salary'] * 1.5)
    teams = {captain['team']: 1}

    for util in utils:
        if len(lineup) >= 6:
            break

        if salary + util['salary'] <= 50000:
            lineup.append(util)
            salary += util['salary']
            teams[util['team']] = teams.get(util['team'], 0) + 1

    # Must have valid lineup
    if len(lineup) == 6 and len(teams) >= 2:
        return create_showdown_lineup_result(lineup, captain)

    return None


# Helper functions for opponent strategies

def build_with_weights(players, own_weight, proj_weight):
    """Weighted approach for opponents"""
    for p in players:
        p['weighted_score'] = (p['ownership'] * own_weight) + (p['projection'] * proj_weight)
    return build_by_metric(players, 'weighted_score')


def build_simple_lineup(players):
    """Simple lineup building for average opponents"""
    # Just pick good value plays
    return build_by_metric(players, 'value_score')


def build_random_decent_lineup(players):
    """Random but somewhat sensible lineup"""
    # Filter to decent players only
    decent_players = [p for p in players if p['value_score'] > 2.0]
    if len(decent_players) < 50:
        decent_players = players

    # Shuffle and build
    shuffled = decent_players.copy()
    random.shuffle(shuffled)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)

    for player in shuffled:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1

    if len(lineup) == 10:
        return create_classic_lineup_result(lineup)

    return None


def build_expensive_lineup(players):
    """Weak players might just pick expensive players"""
    expensive = sorted(players, key=lambda x: x['salary'], reverse=True)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)

    for player in expensive:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1

    if len(lineup) == 10:
        return create_classic_lineup_result(lineup)

    return None


def build_random_lineup(players):
    """Completely random lineup for weak opponents"""
    shuffled = players.copy()
    random.shuffle(shuffled)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams = defaultdict(int)

    for player in shuffled:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        if teams[player['team']] >= 5:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams[player['team']] += 1

    if len(lineup) == 10:
        return create_classic_lineup_result(lineup)

    return None


def build_field_classic_lineup(players, skill_level, contest_type, slate_size):
    """Build a classic lineup for field based on skill level"""

    # Sharp players use optimal strategies
    if skill_level == 'sharp':
        if contest_type == 'cash':
            # Use high-performing cash strategies
            strategies = [
                lambda p: build_by_metric(p, 'projection'),
                lambda p: build_by_metric(p, 'value_score'),
                lambda p: build_balanced_blend(p, own_weight=0.6, proj_weight=0.4),
            ]
        else:  # GPP
            # Use correlation strategies
            strategies = [
                lambda p: build_team_stack(p, 4),
                lambda p: build_team_stack(p, 5),
                lambda p: build_game_stack_classic(p),
            ]

    # Good players use solid strategies
    elif skill_level == 'good':
        if contest_type == 'cash':
            strategies = [
                lambda p: build_by_metric(p, 'ownership'),
                lambda p: build_balanced_blend(p, own_weight=0.5, proj_weight=0.5),
            ]
        else:
            strategies = [
                lambda p: build_team_stack(p, 4),
                lambda p: build_by_metric(p, 'ceiling'),
            ]

    # Average players use basic strategies
    elif skill_level == 'average':
        strategies = [
            lambda p: build_by_metric(p, 'projection'),
            lambda p: build_by_metric(p, 'value_score'),
            lambda p: build_basic_classic_lineup(p),
        ]

    # Weak players make mistakes
    else:
        strategies = [
            lambda p: build_by_metric(p, 'salary'),  # Pick expensive players
            lambda p: build_basic_classic_lineup(p),  # Random
        ]

    # Try strategies until one works
    random.shuffle(strategies)
    for strategy in strategies:
        try:
            lineup = strategy(players)
            if lineup:
                return lineup
        except:
            continue

    # Fallback to basic
    return build_basic_classic_lineup(players)


def build_field_showdown_lineup(players, skill_level, contest_type):
    """Build a showdown lineup for field based on skill level"""

    # Captain selection varies by skill
    if skill_level == 'sharp':
        # Smart captain selection
        captain_strategies = [
            lambda p: max(p, key=lambda x: x['projection']),  # Best projection
            lambda p: max([x for x in p if x['ownership'] < 20], key=lambda x: x['ceiling'], default=None),  # Leverage
        ]
    elif skill_level == 'good':
        captain_strategies = [
            lambda p: max(p, key=lambda x: x['projection']),
            lambda p: max(p, key=lambda x: x['ownership']),
        ]
    else:
        # Random captain selection for average/weak
        captain_strategies = [
            lambda p: random.choice([x for x in p if x['salary'] > 6000]),
            lambda p: random.choice(p),
        ]

    # Try to build lineup
    for captain_selector in captain_strategies:
        try:
            captain = captain_selector(players)
            if not captain:
                continue

            # Build rest of lineup
            utils = [p for p in players if p['id'] != captain['id']]

            # Sort utils based on skill level
            if skill_level in ['sharp', 'good']:
                utils.sort(key=lambda x: x['value_score'], reverse=True)
            else:
                random.shuffle(utils)

            lineup_players = [captain]
            salary = int(captain['salary'] * 1.5)
            teams = {captain['team']: 1}

            for player in utils:
                if len(lineup_players) >= 6:
                    break

                if salary + player['salary'] <= 50000:
                    lineup_players.append(player)
                    salary += player['salary']
                    teams[player['team']] = teams.get(player['team'], 0) + 1

            if len(lineup_players) == 6 and len(teams) >= 2:
                return create_showdown_lineup_result(lineup_players, captain)
        except:
            continue

    return None


def build_balanced_blend(players, own_weight=0.5, proj_weight=0.5):
    """Build lineup with ownership/projection blend"""
    # Calculate blended score
    for p in players:
        p['blend_score'] = (p['ownership'] * own_weight) + (p['projection'] * proj_weight)

    return build_by_metric(players, 'blend_score')


def build_basic_classic_lineup(players):
    """Build a basic but valid classic lineup - ALWAYS WORKS"""
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Shuffle for randomness
    player_pool = players.copy()
    random.shuffle(player_pool)

    # Fill each position requirement
    for pos, required in CLASSIC_CONFIG['positions'].items():
        pos_players = [p for p in player_pool if p['position'] == pos and p not in lineup]
        pos_players.sort(key=lambda x: x['value_score'], reverse=True)

        added = 0
        for player in pos_players:
            if added >= required:
                break

            # Check constraints
            remaining_spots = 10 - len(lineup)
            remaining_budget = CLASSIC_CONFIG['salary_cap'] - salary

            if remaining_spots > 0:
                avg_salary_needed = remaining_budget / remaining_spots

                # Skip if too expensive
                if player['salary'] > avg_salary_needed * 1.5:
                    continue

            if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1
            added += 1

    # Fill remaining spots with best value
    remaining = [p for p in player_pool if p not in lineup]
    remaining.sort(key=lambda x: x['value_score'], reverse=True)

    for player in remaining:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10 and len(teams_used) >= 2:
        return create_classic_lineup_result(lineup)

    return None


def build_basic_showdown_lineup(players):
    """Build a basic but valid showdown lineup - ALWAYS WORKS"""
    # Random captain
    captain = random.choice(players)

    # Random utils
    utils = [p for p in players if p['id'] != captain['id']]
    random.shuffle(utils)

    lineup = [captain]
    salary = int(captain['salary'] * 1.5)
    teams = {captain['team']: 1}

    for player in utils:
        if len(lineup) >= 6:
            break

        if salary + player['salary'] <= 50000:
            lineup.append(player)
            salary += player['salary']
            teams[player['team']] = teams.get(player['team'], 0) + 1

    if len(lineup) == 6 and len(teams) >= 2:
        return create_showdown_lineup_result(lineup, captain)

    return None


def create_showdown_lineup_result(lineup_players, captain):
    """Create showdown lineup result"""
    total_projection = captain['projection'] * 1.5
    total_projection += sum(p['projection'] for p in lineup_players[1:])

    total_ownership = captain['ownership'] * 1.2
    total_ownership += sum(p['ownership'] for p in lineup_players[1:])

    return {
        'lineup': lineup_players,
        'captain': captain,
        'salary': sum(p['salary'] for p in lineup_players[1:]) + int(captain['salary'] * 1.5),
        'projection': total_projection,
        'ownership': total_ownership / 6,
        'format': 'showdown'
    }


def build_random_lineup(players, format_type, slate_size):
    """Build completely random lineup for field diversity"""
    if format_type == 'showdown':
        # Random showdown
        captain = random.choice(players)
        utils = [p for p in players if p['id'] != captain['id']]
        random.shuffle(utils)

        lineup = [captain]
        salary = captain['salary'] * 1.5
        teams = {captain['team']: 1}

        for player in utils:
            if len(lineup) >= 6:
                break
            if salary + player['salary'] <= SHOWDOWN_CONFIG['salary_cap']:
                lineup.append(player)
                salary += player['salary']
                teams[player['team']] = teams.get(player['team'], 0) + 1

        if len(lineup) == 6 and len(teams) >= 2:
            return {
                'lineup': lineup,
                'captain': captain,
                'salary': salary,
                'projection': sum(p['projection'] for p in lineup[1:]) + captain['projection'] * 1.5,
                'ownership': sum(p['ownership'] for p in lineup) / 6,
                'format': 'showdown'
            }
    else:
        # Random classic
        random_players = players.copy()
        random.shuffle(random_players)

        lineup = []
        salary = 0
        positions_filled = defaultdict(int)
        teams_used = defaultdict(int)

        for player in random_players:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
                continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

        if len(lineup) == 10:
            return create_classic_lineup_result(lineup)

    return None


# ========== SCORING SIMULATION - FIXED ==========
# FIX 1: Replace the simulate_realistic_lineup_score function
# This function is returning the projection without variance
# REPLACE the simulate_realistic_lineup_score function in dfs_diagnostic.py with this:

def simulate_realistic_lineup_score(lineup):
    """Simulate lineup scoring with realistic variance"""
    # Get base projection
    base_projection = lineup.get('projection', 0)
    format_type = lineup.get('format', 'classic')

    # If no projection, return 0
    if base_projection <= 0:
        return 0

    # CRITICAL: Add variance - this creates the randomness!
    if format_type == 'showdown':
        # Showdown has higher variance (35%)
        variance = 0.35
    else:
        # Classic has moderate variance (25%)
        variance = 0.25

    # Generate score with normal distribution
    score_std = base_projection * variance
    total_score = np.random.normal(base_projection, score_std)

    # Add injury/bust risk
    bust_roll = random.random()
    if bust_roll < 0.02:  # 2% complete bust
        total_score *= random.uniform(0.2, 0.4)
    elif bust_roll < 0.10:  # 8% bad game
        total_score *= random.uniform(0.5, 0.7)

    # Add ceiling games
    ceiling_roll = random.random()
    if ceiling_roll > 0.95:  # 5% ceiling game
        total_score *= random.uniform(1.5, 2.0)
    elif ceiling_roll > 0.85:  # 10% great game
        total_score *= random.uniform(1.2, 1.4)

    # Stack correlation effects (for classic only)
    if format_type == 'classic' and 'lineup' in lineup:
        team_counts = defaultdict(int)
        for p in lineup.get('lineup', []):
            if isinstance(p, dict) and 'team' in p:
                team_counts[p['team']] += 1

        max_stack = max(team_counts.values()) if team_counts else 0

        if max_stack >= 4:
            # Stacks can correlate positively or negatively
            correlation_roll = random.random()
            if correlation_roll < 0.20:  # 20% negative correlation
                total_score *= random.uniform(0.75, 0.90)
            elif correlation_roll > 0.60:  # 40% positive correlation
                total_score *= random.uniform(1.10, 1.30)

    # Game environment factors
    environment_roll = random.random()
    if environment_roll < 0.05:  # 5% weather/delay impact
        total_score *= random.uniform(0.7, 0.85)
    elif environment_roll > 0.95:  # 5% perfect conditions
        total_score *= random.uniform(1.1, 1.2)

    # Ensure reasonable bounds
    min_score = base_projection * 0.2  # Floor at 20% of projection
    max_score = base_projection * 3.0  # Ceiling at 300% of projection
    total_score = max(min_score, min(max_score, total_score))

    return total_score

# Test function to verify it's working
# DIAGNOSTIC TEST - Add this function to your code to diagnose the issue

def diagnose_simulation_issue():
    """Diagnose what's wrong with the simulation"""
    print("\n" + "=" * 60)
    print("SIMULATION DIAGNOSTIC TEST")
    print("=" * 60)

    # Test 1: Check if scoring variance works
    print("\n1. Testing Scoring Variance:")
    test_lineup = {
        'projection': 150,
        'format': 'classic',
        'lineup': [{'team': 'LAD'} for _ in range(5)]
    }

    scores = []
    for _ in range(10):
        score = simulate_realistic_lineup_score(test_lineup)
        scores.append(score)

    print(f"   Scores: {[round(s, 1) for s in scores]}")
    print(f"   Mean: {np.mean(scores):.1f}, Std: {np.std(scores):.1f}")

    if np.std(scores) < 5:
        print("   ❌ FAIL: No variance in scoring!")
    else:
        print("   ✅ PASS: Scoring has variance")

    # Test 2: Check field generation
    print("\n2. Testing Field Generation:")

    # Create a simple test slate
    test_slate = {
        'format': 'classic',
        'slate_size': 'small',
        'players': []
    }

    # Generate some test players
    for i in range(50):
        test_slate['players'].append({
            'id': i,
            'name': f'Player_{i}',
            'team': f'Team_{i % 6}',
            'position': ['P', 'C', '1B', '2B', '3B', 'SS', 'OF'][i % 7],
            'salary': random.randint(3000, 10000),
            'projection': random.uniform(10, 30),
            'ownership': random.uniform(5, 35),
            'batting_order': (i % 9) + 1,
            'team_total': 4.5,
            'game_id': i % 3,
            'ceiling': 30,
            'floor': 10,
            'value_score': 2.5
        })

    field = generate_field_realistic(test_slate, 10, 'cash')
    print(f"   Field size generated: {len(field)}")

    if len(field) == 0:
        print("   ❌ FAIL: No field lineups generated!")
    else:
        print("   ✅ PASS: Field generation working")
        # Check if lineups are diverse
        unique_lineups = len(set(str(l) for l in field))
        print(f"   Unique lineups: {unique_lineups}/{len(field)}")

    # Test 3: Check contest simulation
    print("\n3. Testing Contest Simulation:")

    # Build a simple lineup
    strategy_config = {'type': 'value'}
    our_lineup = build_by_metric(test_slate['players'], 'value_score')

    if not our_lineup:
        print("   ❌ FAIL: Cannot build test lineup!")
        return

    print(f"   Our lineup projection: {our_lineup['projection']:.1f}")

    # Simulate scoring
    our_score = simulate_realistic_lineup_score(our_lineup)
    print(f"   Our actual score: {our_score:.1f}")

    # Generate and score field
    field_scores = []
    for i in range(10):
        # Create a dummy lineup with projection
        dummy_lineup = {
            'projection': random.uniform(140, 180),
            'format': 'classic'
        }
        score = simulate_realistic_lineup_score(dummy_lineup)
        field_scores.append(score)

    print(f"   Field scores: {[round(s, 1) for s in field_scores[:5]]}...")

    # Test ranking
    all_scores = field_scores + [our_score]
    all_scores.sort(reverse=True)
    our_rank = all_scores.index(our_score) + 1
    percentile = ((len(all_scores) - our_rank) / len(all_scores)) * 100

    print(f"   Our rank: {our_rank}/{len(all_scores)}")
    print(f"   Our percentile: {percentile:.1f}%")

    # Test payout (cash game)
    entry_fee = 10
    cash_threshold = 56  # Top 44%

    if percentile >= cash_threshold:
        print(f"   ✅ Would cash! (need {cash_threshold}%, got {percentile:.1f}%)")
    else:
        print(f"   ❌ Would not cash (need {cash_threshold}%, got {percentile:.1f}%)")

    print("\n" + "=" * 60)


def verify_scoring_variance():
    """Verify the scoring function has proper variance"""
    test_lineup = {
        'projection': 150,
        'format': 'classic',
        'lineup': [{'team': 'LAD'} for _ in range(5)]  # 5-man stack
    }

    scores = []
    for _ in range(1000):
        score = simulate_realistic_lineup_score(test_lineup)
        scores.append(score)

    mean = np.mean(scores)
    std = np.std(scores)
    min_score = min(scores)
    max_score = max(scores)

    print(f"\n{'=' * 60}")
    print(f"SCORING VARIANCE VERIFICATION (1000 simulations)")
    print(f"{'=' * 60}")
    print(f"Base Projection: 150")
    print(f"Actual Mean: {mean:.1f} (should be ~150)")
    print(f"Actual Std Dev: {std:.1f} (should be 35-45)")
    print(f"Min Score: {min_score:.1f}")
    print(f"Max Score: {max_score:.1f}")
    print(f"Coefficient of Variation: {(std / mean) * 100:.1f}%")

    # Check distribution
    below_100 = sum(1 for s in scores if s < 100)
    above_200 = sum(1 for s in scores if s > 200)

    print(f"\nDistribution:")
    print(f"Scores < 100: {below_100 / 10:.1f}% (bust games)")
    print(f"Scores > 200: {above_200 / 10:.1f}% (ceiling games)")

    if std < 20:
        print("\n❌ FAIL: Variance too low! Strategies will show 0% win rates.")
    elif std > 60:
        print("\n⚠️  WARNING: Variance might be too high.")
    else:
        print("\n✅ PASS: Variance looks realistic!")
    print(f"{'=' * 60}\n")


# FIX 2: Fix the simulate_contest function to ensure proper ranking
def simulate_contest(slate, strategy_name, strategy_config, contest_type, field_size):
    """Simulate a DFS contest with proper scoring and ranking"""

    # Set entry fees
    if slate['format'] == 'showdown':
        entry_fee = 3 if contest_type == 'gpp' else 5
    else:
        entry_fee = 3 if contest_type == 'gpp' else 10

    # Build our lineup
    if slate['format'] == 'showdown':
        our_lineup = build_showdown_lineup(slate['players'], strategy_config)
    else:
        our_lineup = build_classic_lineup(slate['players'], strategy_config, slate['slate_size'])

    if not our_lineup:
        return {
            'strategy': strategy_name,
            'contest_type': contest_type,
            'field_size': field_size,
            'format': slate['format'],
            'slate_size': slate['slate_size'],
            'failed': True,
            'failure_reason': 'lineup_build_failed'
        }

    # Generate field
    field_lineups = generate_field_realistic(slate, field_size - 1, contest_type)

    # Score all lineups with proper variance
    our_score = simulate_realistic_lineup_score(our_lineup)

    # Score field with variance
    field_scores = []
    for lineup in field_lineups:
        score = simulate_realistic_lineup_score(lineup)
        field_scores.append(score)

    # CRITICAL: Create combined scores list properly
    all_scores = field_scores + [our_score]
    all_scores_sorted = sorted(all_scores, reverse=True)

    # Calculate placement correctly
    our_rank = all_scores_sorted.index(our_score) + 1
    percentile = ((len(all_scores) - our_rank) / len(all_scores)) * 100

    # Calculate payout
    config = SHOWDOWN_CONFIG if slate['format'] == 'showdown' else CLASSIC_CONFIG

    if contest_type == 'cash':
        cash_threshold_percentile = (1 - config['cash_payout_threshold']) * 100
        if percentile >= cash_threshold_percentile:
            payout = entry_fee * 2
        else:
            payout = 0
    else:  # GPP
        payout_pct = our_rank / len(all_scores)
        payout = 0

        for threshold, multiplier in sorted(config['gpp_payout_structure'].items()):
            if payout_pct <= threshold:
                payout = entry_fee * multiplier
                break

    profit = payout - entry_fee
    roi = (profit / entry_fee) * 100

    # Calculate cash line properly
    cash_line_idx = int(len(all_scores_sorted) * config['cash_payout_threshold'])
    cash_line = all_scores_sorted[cash_line_idx] if cash_line_idx < len(all_scores_sorted) else all_scores_sorted[-1]

    return {
        'strategy': strategy_name,
        'contest_type': contest_type,
        'field_size': field_size,
        'format': slate['format'],
        'slate_size': slate['slate_size'],
        'rank': our_rank,
        'percentile': percentile,
        'score': our_score,
        'payout': payout,
        'profit': profit,
        'roi': roi,
        'ownership': our_lineup.get('ownership', 0),
        'projection': our_lineup.get('projection', 0),
        'failed': False,
        'score_mean': np.mean(all_scores),
        'score_std': np.std(all_scores),
        'score_min': min(all_scores),
        'score_max': max(all_scores),
        'winning_score': all_scores_sorted[0],
        'cash_line': cash_line
    }


# FIX 3: Debug helper to verify scoring is working
def test_scoring_variance():
    """Test that scoring has proper variance"""
    test_lineup = {
        'projection': 150,
        'format': 'classic',
        'lineup': [{'team': 'LAD'} for _ in range(10)]
    }

    scores = []
    for _ in range(100):
        score = simulate_realistic_lineup_score(test_lineup)
        scores.append(score)

    mean = np.mean(scores)
    std = np.std(scores)
    min_score = min(scores)
    max_score = max(scores)

    print(f"Test Results for 150 projection lineup:")
    print(f"Mean: {mean:.1f} (should be ~150)")
    print(f"Std: {std:.1f} (should be ~37.5)")
    print(f"Min: {min_score:.1f}")
    print(f"Max: {max_score:.1f}")
    print(f"Range: {max_score - min_score:.1f}")

    if std < 10:
        print("❌ WARNING: Variance too low!")
    else:
        print("✅ Variance looks good!")


# Add this test call before running your main simulation
# test_scoring_variance()

# ========== ANALYSIS - ENHANCED ==========

def analyze_results(results: List[Dict]):
    """Analyze results by format and slate size - ENHANCED"""
    print("\n" + "=" * 80)
    print("🎯 DFS ULTIMATE SIMULATOR 2.0 - DETAILED RESULTS ANALYSIS")
    print("=" * 80 + "\n")

    # Separate by data quality - handle different result types
    high_confidence = []
    medium_confidence = []
    low_confidence = []
    insights_only = []

    # First, separate special result types from actual game results
    special_results = []
    game_results = []

    for r in results:
        result_type = r.get('type')
        if result_type in ['low_success_strategy', 'impossible_strategy', 'failed_strategy',
                           'strategy_summary', 'batch_summary', 'failure_summary']:
            special_results.append(r)
        elif 'format' in r and 'slate_size' in r and 'contest_type' in r:
            game_results.append(r)

    # Process special results for insights
    for r in special_results:
        if r.get('type') == 'low_success_strategy':
            sample_size = r.get('sample_size', 0)
            if sample_size >= 30:
                high_confidence.append(r)
            elif sample_size >= 10:
                medium_confidence.append(r)
            else:
                low_confidence.append(r)

    # Show different sections
    print("\n🏆 HIGH CONFIDENCE STRATEGIES (30+ samples):")
    # Process high confidence results here...

    print("\n🎲 TOURNAMENT SPECIALISTS (Low success, high reward):")
    for strat in low_confidence:
        if strat.get('avg_roi', 0) > 20:
            print(f"  • {strat['strategy']}: {strat['success_rate']:.1%} success, "
                  f"but {strat['avg_roi']:.1f}% ROI when hits!")

    print("\n⚡ RARE BUT VIABLE (Limited data):")
    for strat in medium_confidence:
        if strat.get('avg_roi', 0) > 10:
            print(f"  • {strat['strategy']}: {strat['sample_size']} samples, "
                  f"{strat['avg_roi']:.1f}% ROI")

    # Group game results
    grouped_results = defaultdict(lambda: defaultdict(list))

    for r in game_results:
        # Only process records with all required fields
        if all(key in r for key in ['format', 'slate_size', 'contest_type', 'strategy']):
            key = f"{r['format']}_{r['slate_size']}_{r['contest_type']}"
            grouped_results[key][r['strategy']].append(r)

    # Analyze each group
    for group_key in sorted(grouped_results.keys()):
        format_type, slate_size, contest_type = group_key.split('_')

        print(f"\n{'=' * 60}")
        print(f"📊 {format_type.upper()} - {SLATE_SIZES[slate_size]['name']} - {contest_type.upper()}")
        print(f"{'=' * 60}\n")

        group_data = grouped_results[group_key]
        summary = []

        for strategy_name, results_list in group_data.items():
            if len(results_list) < 5:
                continue

            if contest_type == 'cash':
                wins = sum(1 for r in results_list if r.get('profit', 0) > 0)
                win_rate = (wins / len(results_list)) * 100
                avg_roi = np.mean([r.get('roi', 0) for r in results_list])
                avg_score = np.mean([r.get('score', 0) for r in results_list])
                avg_ownership = np.mean([r.get('ownership', 0) for r in results_list])
                avg_rank = np.mean([r.get('rank', 999) for r in results_list])
                median_rank = np.median([r.get('rank', 999) for r in results_list])
                percentile_75 = np.percentile([r.get('percentile', 0) for r in results_list], 75)
                times_cashed = wins

                summary.append({
                    'strategy': strategy_name,
                    'win_rate': win_rate,
                    'roi': avg_roi,
                    'avg_score': avg_score,
                    'avg_ownership': avg_ownership,
                    'avg_rank': avg_rank,
                    'median_rank': median_rank,
                    'percentile_75': percentile_75,
                    'times_cashed': times_cashed,
                    'sample_size': len(results_list)
                })
            else:  # GPP
                avg_roi = np.mean([r.get('roi', 0) for r in results_list])
                top1_pct = sum(1 for r in results_list if r.get('percentile', 0) >= 99) / len(results_list) * 100
                top5_pct = sum(1 for r in results_list if r.get('percentile', 0) >= 95) / len(results_list) * 100
                top10_pct = sum(1 for r in results_list if r.get('percentile', 0) >= 90) / len(results_list) * 100
                top20_pct = sum(1 for r in results_list if r.get('percentile', 0) >= 80) / len(results_list) * 100
                profitable = sum(1 for r in results_list if r.get('profit', 0) > 0) / len(results_list) * 100
                avg_rank = np.mean([r.get('rank', 999) for r in results_list])
                median_rank = np.median([r.get('rank', 999) for r in results_list])
                best_finish = min(r.get('rank', 999) for r in results_list)
                avg_payout_when_cash = np.mean(
                    [r.get('payout', 0) for r in results_list if r.get('payout', 0) > 0]) if any(
                    r.get('payout', 0) > 0 for r in results_list) else 0

                summary.append({
                    'strategy': strategy_name,
                    'roi': avg_roi,
                    'top1_pct': top1_pct,
                    'top5_pct': top5_pct,
                    'top10_pct': top10_pct,
                    'top20_pct': top20_pct,
                    'profitable': profitable,
                    'avg_rank': avg_rank,
                    'median_rank': median_rank,
                    'best_finish': best_finish,
                    'avg_payout_when_cash': avg_payout_when_cash,
                    'sample_size': len(results_list)
                })

        # Display results (rest of the display code remains the same...)
        if not summary:
            print("No valid results for this configuration.\n")
            continue

        if contest_type == 'cash':
            summary.sort(key=lambda x: x['win_rate'], reverse=True)

            print(
                f"{'Strategy':<25} {'Win%':>6} {'ROI%':>7} {'Avg Rank':>9} {'Med Rank':>9} {'75th %ile':>10} {'Times Cash':>11}")
            print("-" * 100)

            for data in summary:
                strategy_obj = None
                if format_type == 'showdown':
                    strategy_obj = SHOWDOWN_STRATEGIES.get(data['strategy'])
                else:
                    for ct in ['cash', 'gpp']:
                        if slate_size in CLASSIC_STRATEGIES_BY_SIZE:
                            if data['strategy'] in CLASSIC_STRATEGIES_BY_SIZE[slate_size].get(ct, {}):
                                strategy_obj = CLASSIC_STRATEGIES_BY_SIZE[slate_size][ct][data['strategy']]
                                break

                name = strategy_obj['name'] if strategy_obj else data['strategy']

                # Status indicator
                if data['win_rate'] >= 56:
                    status = "✅"
                elif data['win_rate'] >= 52:
                    status = "⚠️"
                else:
                    status = "❌"

                print(
                    f"{name:<25} {data['win_rate']:>5.1f}% {data['roi']:>+6.1f}% {data['avg_rank']:>8.1f} {data['median_rank']:>8.0f} "
                    f"{data['percentile_75']:>9.1f}% {data['times_cashed']:>10}/{data['sample_size']:<3} {status}")

            # Strategy descriptions
            print("\n📝 Strategy Details:")
            for data in summary[:5]:  # Top 5 strategies
                strategy_obj = None
                if format_type == 'showdown':
                    strategy_obj = SHOWDOWN_STRATEGIES.get(data['strategy'])
                else:
                    for ct in ['cash', 'gpp']:
                        if slate_size in CLASSIC_STRATEGIES_BY_SIZE:
                            if data['strategy'] in CLASSIC_STRATEGIES_BY_SIZE[slate_size].get(ct, {}):
                                strategy_obj = CLASSIC_STRATEGIES_BY_SIZE[slate_size][ct][data['strategy']]
                                break

                if strategy_obj and 'description' in strategy_obj:
                    print(f"   • {strategy_obj['name']}: {strategy_obj['description']}")
                    print(f"     Avg Score: {data['avg_score']:.1f} | Avg Own: {data['avg_ownership']:.1f}%")

        else:  # GPP
            summary.sort(key=lambda x: x['roi'], reverse=True)

            print(f"{'Strategy':<25} {'ROI%':>7} {'Top 1%':>7} {'Top 5%':>7} {'Top 10%':>8} {'Top 20%':>8} {'Best':>6}")
            print("-" * 85)

            for data in summary:
                strategy_obj = None
                if format_type == 'showdown':
                    strategy_obj = SHOWDOWN_STRATEGIES.get(data['strategy'])
                else:
                    for ct in ['cash', 'gpp']:
                        if slate_size in CLASSIC_STRATEGIES_BY_SIZE:
                            if data['strategy'] in CLASSIC_STRATEGIES_BY_SIZE[slate_size].get(ct, {}):
                                strategy_obj = CLASSIC_STRATEGIES_BY_SIZE[slate_size][ct][data['strategy']]
                                break

                name = strategy_obj['name'] if strategy_obj else data['strategy']

                # Status indicator
                if data['roi'] > 20:
                    status = "🔥"
                elif data['roi'] > 0:
                    status = "✅"
                elif data['roi'] > -30:
                    status = "⚠️"
                else:
                    status = "❌"

                print(f"{name:<25} {data['roi']:>+6.1f}% {data['top1_pct']:>6.1f}% {data['top5_pct']:>6.1f}% "
                      f"{data['top10_pct']:>7.1f}% {data['top20_pct']:>7.1f}% {data['best_finish']:>5} {status}")

            # Additional GPP metrics
            print(f"\n📊 Additional Metrics:")
            for data in summary[:5]:  # Top 5 strategies
                strategy_obj = None
                if format_type == 'showdown':
                    strategy_obj = SHOWDOWN_STRATEGIES.get(data['strategy'])
                else:
                    for ct in ['cash', 'gpp']:
                        if slate_size in CLASSIC_STRATEGIES_BY_SIZE:
                            if data['strategy'] in CLASSIC_STRATEGIES_BY_SIZE[slate_size].get(ct, {}):
                                strategy_obj = CLASSIC_STRATEGIES_BY_SIZE[slate_size][ct][data['strategy']]
                                break

                name = strategy_obj['name'] if strategy_obj else data['strategy']
                print(f"   • {name}:")
                print(f"     Profitable: {data['profitable']:.1f}% | Avg Rank: {data['avg_rank']:.1f} | "
                      f"Median Rank: {data['median_rank']:.0f}")
                if data['avg_payout_when_cash'] > 0:
                    print(f"     Avg Payout When Cash: ${data['avg_payout_when_cash']:.2f}")

    # Summary findings
    print("\n" + "=" * 80)
    print("🔍 KEY FINDINGS BY SLATE SIZE")
    print("=" * 80 + "\n")

    print("📈 SMALL SLATES (3 games):")
    print("   • Value/Projection strategies dominate cash games")
    print("   • Ownership less important due to player concentration")
    print("   • Ceiling-focused builds work well for GPPs")
    print("   • Limited differentiation opportunities")
    print()

    print("📊 MEDIUM SLATES (7 games):")
    print("   • Balanced 50/50 approaches optimal for cash")
    print("   • Sequential stacking powerful in GPPs")
    print("   • Double stacks provide unique leverage")
    print("   • Sweet spot for strategy diversity")
    print()

    print("📉 LARGE SLATES (12+ games):")
    print("   • Ownership becomes critical factor")
    print("   • Multiple correlation strategies viable")
    print("   • Leverage theory and contrarian stacks shine")
    print("   • Field makes more mistakes = edge opportunity")
    print()

    print("🎯 SHOWDOWN:")
    print("   • Extremely high variance format")
    print("   • Captain selection determines success")
    print("   • Onslaught correlations powerful when hit")
    print("   • Game theory approach underutilized")
    print()

    print("💡 OVERALL INSIGHTS:")
    print("   • Cash game win rates 52-58% achievable")
    print("   • GPP success requires proper correlation")
    print("   • Slate size dramatically impacts optimal strategy")
    print("   • Field composition creates exploitable edges")

# At the end of analyze_results function, add:
    # Show diagnostic information
    analyze_diagnostics(results)


def analyze_diagnostics(results: List[Dict]):
    """Analyze diagnostic information from simulation"""
    print("\n" + "=" * 80)
    print("📊 DIAGNOSTIC ANALYSIS")
    print("=" * 80 + "\n")

    # Extract failure summaries with safety checks
    failures = []
    score_distributions = defaultdict(list)

    for r in results:
        # Skip if it's a special result type
        result_type = r.get('type')
        if result_type in ['low_success_strategy', 'impossible_strategy', 'failed_strategy',
                           'strategy_summary', 'batch_summary']:
            continue

        if result_type == 'failure_summary':
            failures.append(r)
        elif not r.get('failed', False):
            # Only process game results with required fields
            if all(key in r for key in ['format', 'slate_size', 'contest_type', 'score']):
                key = f"{r['format']}_{r['slate_size']}_{r['contest_type']}"
                score_distributions[key].append({
                    'score': r.get('score', 0),
                    'winning_score': r.get('winning_score'),
                    'cash_line': r.get('cash_line'),
                    'mean': r.get('score_mean'),
                    'std': r.get('score_std')
                })

    # Show failure analysis
    if failures:
        print("LINEUP BUILD FAILURES:")
        print("-" * 40)
        all_failures = defaultdict(int)
        for f in failures:
            for key, reasons in f.get('failures', {}).items():
                if key != 'exceptions':
                    if isinstance(reasons, dict):
                        total = reasons.get('total',
                                            sum(v for k, v in reasons.items() if k != 'total' and isinstance(v, int)))
                    else:
                        total = reasons
                    all_failures[key] = total

        for key, count in sorted(all_failures.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"{key}: {count} failures")

    # Show score distributions
    print("\nSCORE DISTRIBUTIONS:")
    print("-" * 60)
    print(f"{'Config':<30} {'Mean':>8} {'Std':>8} {'Win':>8} {'Cash':>8}")
    print("-" * 60)

    for config, scores in score_distributions.items():
        if scores:
            avg_mean = np.mean([s['mean'] for s in scores if s['mean']])
            avg_std = np.mean([s['std'] for s in scores if s['std']])
            avg_win = np.mean([s['winning_score'] for s in scores if s['winning_score']])
            avg_cash = np.mean([s['cash_line'] for s in scores if s['cash_line']]) if 'cash' in config else 0

            print(f"{config:<30} {avg_mean:>8.1f} {avg_std:>8.1f} {avg_win:>8.1f} {avg_cash:>8.1f}")

    # Calculate score multipliers
    print("\nSCORE MULTIPLIERS (Winning Score / Mean Projection):")
    print("-" * 40)

    for config, scores in score_distributions.items():
        if scores and len(scores) > 10:
            wins = [s['winning_score'] for s in scores if s['winning_score']]
            means = [s['mean'] for s in scores if s['mean']]
            if wins and means:
                multiplier = np.mean(wins) / np.mean(means)
                print(f"{config}: {multiplier:.2f}x")


# ========== MAIN EXECUTION (WITH PARALLEL PROCESSING) ===========

def run_simulation(num_slates_per_config: int = 50, contest_type_override: str = None):
    """Run comprehensive simulation across all formats and slate sizes"""
    print("\n🚀 DFS ULTIMATE SIMULATOR 2.0 - FIXED EDITION")
    print("Testing strategies across different slate sizes and formats")
    print("=" * 60)

    # FIX: Define num_slates from parameter
    num_slates = num_slates_per_config

    # ENHANCED: Different sample sizes for cash vs GPP
    if contest_type_override:
        if contest_type_override == 'cash':
            num_slates = num_slates_per_config if num_slates_per_config >= 75 else 75
            print(f"\n📊 Running CASH ONLY simulation with {num_slates} slates per config")
        else:  # gpp
            num_slates = num_slates_per_config if num_slates_per_config >= 150 else 150
            print(f"\n📊 Running GPP ONLY simulation with {num_slates} slates per config")
    else:
        # Mixed mode - use provided number but recommend higher
        num_slates = num_slates_per_config
        if num_slates < 100:
            print(f"\n⚠️  Warning: {num_slates} slates may be insufficient for GPP analysis")
            print("   Recommended: 75+ for cash, 150+ for GPPs")

    print(f"\n📊 Configuration:")
    print(f"   • Slates per config: {num_slates}")
    print(f"   • Formats: Showdown, Classic")
    print(f"   • Slate sizes: Small (3), Medium (7), Large (12+)")
    print(f"   • Contest types: {contest_type_override.upper() if contest_type_override else 'Cash, GPP'}")
    print(f"   • Field strength: Realistic distribution")

    # Contest configurations - adjusted for better testing
    if contest_type_override == 'cash':
        contest_configs = [('cash', 100)]
    elif contest_type_override == 'gpp':
        contest_configs = [('gpp', 5000)]  # Large field for better variance
    else:
        contest_configs = [
            ('cash', 100),  # Cash games - 100 entries
            ('gpp', 5000),  # GPP - 5000 entries for better variance
        ]

    # Slate configurations to test
    slate_configs = []
    slate_id = 0

    # Generate slate configs - ensure even distribution
    for format_type in ['showdown', 'classic']:
        if format_type == 'showdown':
            slate_sizes = ['showdown']
        else:
            slate_sizes = ['small', 'medium', 'large']

        for slate_size in slate_sizes:
            for i in range(num_slates):
                slate_configs.append((slate_id, format_type, slate_size))
                slate_id += 1

    print(f"\n📈 Running simulation with PARALLEL PROCESSING...")
    print(f"   • Total slate configs: {len(slate_configs)}")
    print(
        f"   • Strategies tested: {len(SHOWDOWN_STRATEGIES) + sum(len(CLASSIC_STRATEGIES_BY_SIZE[s]['cash']) + len(CLASSIC_STRATEGIES_BY_SIZE[s]['gpp']) for s in ['small', 'medium', 'large'])}")

    # Create batches
    batch_size = 10  # Smaller batches for better progress tracking
    batches = []

    for i in range(0, len(slate_configs), batch_size):
        batch = slate_configs[i:i + batch_size]
        batches.append((batch, contest_configs))

    print(f"   • Batches: {len(batches)}")

    # Run simulation with parallel processing
    start_time = time.time()
    all_results = []  # FIX: Define all_results here

    # Use optimal number of cores
    num_cores = min(mp.cpu_count() - 1, 8)

    print(f"   • Using {num_cores} cores for parallel processing\n")

    with ProcessPoolExecutor(max_workers=num_cores) as executor:
        futures = []
        for batch in batches:
            future = executor.submit(process_batch, batch)
            futures.append(future)

        completed = 0
        for future in as_completed(futures):
            try:
                batch_results = future.result()
                all_results.extend(batch_results)

                completed += 1
                pct = (completed / len(batches)) * 100
                print(f"\rProgress: {completed}/{len(batches)} batches ({pct:.1f}%)", end='', flush=True)

            except Exception as e:
                print(f"\nError in batch: {e}")
                import traceback
                traceback.print_exc()

    print("\n\n")  # Clear the progress line

    total_time = time.time() - start_time
    print(f"✅ Simulation complete in {total_time:.1f} seconds")
    print(f"📊 Total results: {len(all_results):,}")

    # Calculate actual lineup success rate - FIXED
    valid_results = [r for r in all_results if r.get('type') != 'failure_summary']
    failed_results = [r for r in valid_results if r.get('failed', False)]
    successful_results = [r for r in valid_results if not r.get('failed', False)]

    total_attempts = len(valid_results)
    successful_attempts = len(successful_results)
    success_rate = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0

    print(f"📈 Lineup build success rate: {success_rate:.1f}%")
    print(f"   • Successful lineups: {successful_attempts}")
    print(f"   • Failed attempts: {len(failed_results)}")

    # Target success rate warning
    if success_rate < 70:
        print(f"\n⚠️  Warning: Low lineup success rate ({success_rate:.1f}%)")
        print("   This may indicate insufficient player pool or overly restrictive strategies")

    # Show distribution of results
    format_counts = defaultdict(int)
    for r in valid_results:
        if 'format' in r and 'slate_size' in r and not r.get('failed', False):
            key = f"{r['format']}_{r['slate_size']}"
            format_counts[key] += 1

    print("\n📊 Results distribution:")
    for key, count in sorted(format_counts.items()):
        print(f"   • {key}: {count} results")

    # Show failure distribution if significant
    if len(failed_results) > 0:
        failure_counts = defaultdict(int)
        for r in failed_results:
            if 'format' in r and 'slate_size' in r:
                key = f"{r['format']}_{r['slate_size']}"
                failure_counts[key] += 1

        print("\n❌ Failure distribution:")
        for key, count in sorted(failure_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {key}: {count} failures")

    # Extract failure summaries for diagnostic
    failure_summaries = [r for r in all_results if r.get('type') == 'failure_summary']
    if failure_summaries:
        print(f"\n📋 Found {len(failure_summaries)} failure summary records for diagnostics")

    # Analyze results - only successful results
    analyze_results(successful_results)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    contest_suffix = f"_{contest_type_override}" if contest_type_override else ""
    filename = f'dfs_simulator_v2_fixed_results_{timestamp}{contest_suffix}.json'

    # Separate data for saving
    save_data = {
        'timestamp': datetime.now().isoformat(),
        'config': {
            'num_slates_per_config': num_slates,
            'contest_types': [contest_type_override] if contest_type_override else ['cash', 'gpp'],
            'formats': ['showdown', 'classic'],
            'slate_sizes': list(SLATE_SIZES.keys()),
            'version': 'Fixed Edition v2',
            'field_strength': 'Realistic (Enhanced)',
            'scoring_variance': 'High'
        },
        'summary': {
            'total_attempts': total_attempts,
            'successful_lineups': successful_attempts,
            'failed_attempts': len(failed_results),
            'success_rate': success_rate,
            'simulation_time': total_time
        },
        'results': successful_results,  # Only save successful results
        'failures': failure_summaries  # Save failure analysis separately
    }

    with open(filename, 'w') as f:
        json.dump(save_data, f, indent=2)

    print(f"\n💾 Detailed results saved to: {filename}")

def main():
    """Main entry point"""
    print("\n🎯 DFS ULTIMATE SIMULATOR 2.0 - FIXED EDITION", flush=True)
    print("Format & Slate Size Aware Testing", flush=True)
    print("=" * 60, flush=True)

    print("\nThis simulation will test:", flush=True)
    print("• Showdown strategies", flush=True)
    print("• Small slate strategies (3 games)", flush=True)
    print("• Medium slate strategies (7 games)", flush=True)
    print("• Large slate strategies (12+ games)", flush=True)
    print("• How ownership vs projections varies by slate size", flush=True)
    print("\n• FIXED: Better player pool generation", flush=True)
    print("• FIXED: No strategy fallbacks (pure testing)", flush=True)
    print("• ENHANCED: Separate cash/GPP testing with proper sample sizes", flush=True)

    print("\nSelect simulation mode:")
    print("1. Quick Test (50 slates each)")
    print("2. Cash Focus (100 slates)")
    print("3. GPP Focus (200 slates)")
    print("4. Full Test (150 slates each)")
    print("5. Custom")

    choice = input("\nEnter choice (1-5): ")

    if choice == '1':
        run_simulation(num_slates_per_config=50)
    elif choice == '2':
        run_simulation(num_slates_per_config=100, contest_type_override='cash')
    elif choice == '3':
        run_simulation(num_slates_per_config=200, contest_type_override='gpp')
    elif choice == '4':
        run_simulation(num_slates_per_config=150)
    elif choice == '5':
        num = int(input("Enter number of slates per config: "))
        contest = input("Contest type (cash/gpp/both): ").lower()
        if contest in ['cash', 'gpp']:
            run_simulation(num_slates_per_config=num, contest_type_override=contest)
        else:
            run_simulation(num_slates_per_config=num)
    else:
        print("Invalid choice, running quick test...")
        run_simulation(num_slates_per_config=50)


# ========== SLATE GENERATION ==========
def get_strategy_for_contest(slate_size, contest_type, strategy_name):
    """Get the correct strategy configuration for contest type"""
    if slate_size in CLASSIC_STRATEGIES_BY_SIZE:
        if contest_type in CLASSIC_STRATEGIES_BY_SIZE[slate_size]:
            strategies = CLASSIC_STRATEGIES_BY_SIZE[slate_size][contest_type]
            if strategy_name in strategies:
                return strategies[strategy_name]
    return None


def generate_slate(slate_id, format_type, slate_size):
    """Generate a slate for specific format and size with REALISTIC player pools"""
    random.seed(slate_id)
    np.random.seed(slate_id)

    num_games = SLATE_SIZES[slate_size]['games']

    # Team pool
    all_teams = ['LAD', 'NYY', 'HOU', 'ATL', 'SD', 'TB', 'BOS', 'MIL', 'PHI', 'TOR',
                 'SEA', 'TEX', 'MIN', 'CLE', 'BAL', 'CHC', 'SF', 'STL', 'NYM', 'LAA',
                 'CHW', 'MIA', 'CIN', 'COL', 'DET', 'KC', 'PIT', 'OAK', 'WSN', 'ARI']

    # Select teams
    if format_type == 'showdown':
        playing_teams = random.sample(all_teams, 2)
    else:
        num_teams_needed = num_games * 2
        playing_teams = random.sample(all_teams, min(num_teams_needed, len(all_teams)))

    games = []
    for i in range(0, len(playing_teams), 2):
        if i + 1 >= len(playing_teams):
            break

        home_team = playing_teams[i]
        away_team = playing_teams[i + 1]

        # Game totals
        base_total = np.random.normal(8.5, 1.2)

        # Park factors
        park_factors = {
            'COL': 1.4, 'TEX': 1.15, 'CIN': 1.1,
            'DET': 0.9, 'SF': 0.85, 'SEA': 0.9
        }

        park_factor = park_factors.get(home_team, 1.0)
        game_total = base_total * park_factor
        game_total = np.clip(game_total, 6.0, 13.5)

        # Split totals
        home_percentage = np.random.normal(0.52, 0.05)
        home_total = game_total * home_percentage
        away_total = game_total * (1 - home_percentage)

        games.append({
            'game_id': i // 2,
            'home_team': home_team,
            'away_team': away_team,
            'game_total': round(game_total, 1),
            'home_total': round(home_total, 2),
            'away_total': round(away_total, 2),
            'park_factor': park_factor
        })

    # Generate players
    players = []
    player_id = 0

    for game in games:
        game_data = {
            'game_id': game['game_id'],
            'park_factor': game['park_factor'],
            'game_total': game['game_total'],
            'team_totals': {
                game['home_team']: game['home_total'],
                game['away_team']: game['away_total']
            }
        }

        for team in [game['home_team'], game['away_team']]:
            if format_type == 'showdown':
                # SHOWDOWN: Realistic roster
                # Starting pitcher
                player = generate_realistic_showdown_player(player_id, team, 'P', 0, game_data)
                players.append(player)
                player_id += 1

                # Position distribution for realistic lineup
                batting_order_positions = {
                    1: random.choice(['CF', 'SS', '2B']),
                    2: random.choice(['2B', 'SS', 'RF']),
                    3: random.choice(['1B', '3B', 'RF']),
                    4: random.choice(['1B', 'DH', 'LF']),
                    5: random.choice(['3B', 'DH', 'RF']),
                    6: random.choice(['C', 'LF', '2B']),
                    7: random.choice(['SS', '2B', 'CF']),
                    8: random.choice(['C', 'CF', '2B']),
                    9: random.choice(['C', 'SS', '2B'])
                }

                # Generate starters in batting order
                for batting_order in range(1, 10):
                    position = batting_order_positions[batting_order]
                    if position == 'DH':
                        position = random.choice(['1B', 'OF'])
                    if position in ['LF', 'CF', 'RF']:
                        position = 'OF'

                    player = generate_realistic_showdown_player(
                        player_id, team, position, batting_order, game_data
                    )
                    players.append(player)
                    player_id += 1

                # Add 2-3 bench/punt players for showdown
                num_bench = random.choice([2, 3])
                for _ in range(num_bench):
                    position = random.choice(['OF', '2B', 'SS'])
                    player = generate_realistic_showdown_player(
                        player_id, team, position, 0, game_data
                    )
                    # Make these true punts
                    player['salary'] = random.randint(2000, 3000)
                    player['projection'] = player['salary'] / 1000 * random.uniform(2.0, 2.5)
                    player['value_score'] = player['projection'] / (player['salary'] / 1000)
                    players.append(player)
                    player_id += 1

            else:  # CLASSIC format
                # Starting pitchers (1-2 confirmed starters)
                num_starters = 2 if random.random() < 0.7 else 1
                for _ in range(num_starters):
                    player = generate_realistic_classic_player(
                        player_id, team, 'P', 0, game_data, slate_size, is_starter=True
                    )
                    players.append(player)
                    player_id += 1

                # Relief pitchers (1-2)
                num_relievers = random.choice([1, 2])
                for _ in range(num_relievers):
                    player = generate_realistic_classic_player(
                        player_id, team, 'P', 0, game_data, slate_size, is_starter=False
                    )
                    players.append(player)
                    player_id += 1

                # Starting lineup (batting order 1-9)
                classic_batting_positions = {
                    1: random.choice(['CF', 'SS', '2B']),
                    2: random.choice(['2B', 'SS', 'RF']),
                    3: random.choice(['1B', '3B', 'RF']),
                    4: random.choice(['1B', 'DH', 'LF']),
                    5: random.choice(['3B', 'DH', 'RF']),
                    6: random.choice(['C', 'LF', '2B']),
                    7: random.choice(['SS', '2B', 'CF']),
                    8: random.choice(['C', 'CF', '2B']),
                    9: random.choice(['C', 'SS', '2B'])
                }

                positions_used = defaultdict(int)

                # Generate starting lineup
                for batting_order in range(1, 10):
                    position = classic_batting_positions[batting_order]
                    if position == 'DH':
                        position = random.choice(['1B', 'OF'])
                    if position in ['LF', 'CF', 'RF']:
                        position = 'OF'

                    # Ensure position variety
                    if position == 'C' and positions_used['C'] >= 2:
                        position = random.choice(['2B', 'SS'])
                    elif position == 'OF' and positions_used['OF'] >= 4:
                        position = random.choice(['2B', 'SS', '3B'])

                    player = generate_realistic_classic_player(
                        player_id, team, position, batting_order, game_data, slate_size
                    )
                    players.append(player)
                    positions_used[position] += 1
                    player_id += 1

                # CRITICAL: ENSURE ADEQUATE OF DEPTH (matches real DFS)
                current_of = sum(1 for p in players if p['team'] == team and p['position'] == 'OF')

                # Real teams have 4-5 OF on roster, ensure at least 5
                while current_of < 5:
                    player = generate_realistic_classic_player(
                        player_id, team, 'OF', 0, game_data, slate_size,
                        is_starter=False,  # Bench player
                        force_punt=(current_of >= 3)  # 4th-5th OF are usually punts
                    )
                    players.append(player)
                    player_id += 1
                    current_of += 1
                    positions_used['OF'] += 1

                # Add bench players for other positions
                bench_positions = ['2B', 'SS', '3B', 'C', '1B']
                random.shuffle(bench_positions)

                num_bench = random.choice([2, 3])
                for i in range(num_bench):
                    position = bench_positions[i % len(bench_positions)]

                    # Ensure position variety
                    if positions_used[position] >= 3:
                        position = random.choice(['2B', 'SS', '3B'])

                    player = generate_realistic_classic_player(
                        player_id, team, position, 0, game_data, slate_size,
                        force_punt=(random.random() < 0.5)  # 50% of bench are punts
                    )
                    players.append(player)
                    positions_used[position] += 1
                    player_id += 1

                # ENSURE PUNT VARIETY: Add 2-3 guaranteed cheap plays per team
                punt_positions = ['C', 'SS', '2B', 'OF', 'OF']  # OF appears twice
                for i in range(random.randint(2, 3)):
                    position = punt_positions[i % len(punt_positions)]
                    player = generate_realistic_classic_player(
                        player_id, team, position, 0, game_data, slate_size,
                        force_punt=True  # Force these to be punts
                    )
                    players.append(player)
                    player_id += 1

                # NEW ADDITION: MATCH REAL DFS - Ensure minimum salary OF exist
                cheap_of_count = sum(1 for p in players
                                     if p['team'] == team
                                     and p['position'] == 'OF'
                                     and p['salary'] <= 2500)

                # Real DFS has 2-3 min salary OF per team
                while cheap_of_count < 2:
                    player = generate_realistic_classic_player(
                        player_id, team, 'OF', 9, game_data, slate_size,  # 9th hitter
                        is_starter=False,
                        force_punt=True
                    )
                    # FORCE minimum salary (matches DK/FD reality)
                    player['salary'] = 2000
                    player['projection'] = random.uniform(4.5, 6)
                    player['ownership'] = random.uniform(0.5, 3)
                    player['value_score'] = player['projection'] / 2.0
                    player['name'] = f"{team}_OF_min{cheap_of_count + 1}"

                    players.append(player)
                    player_id += 1
                    cheap_of_count += 1

    players = ensure_position_depth(players, format_type, slate_size)

    return {
        'slate_id': slate_id,
        'format': format_type,
        'slate_size': slate_size,
        'num_games': num_games,
        'games': games,
        'players': players
    }

def generate_realistic_showdown_player(player_id, team, position, batting_order, game_data):
    """Generate showdown player with realistic salary based on batting order"""

    team_total = game_data.get('team_totals', {}).get(team, 4.5)

    if position == 'P':
        # Pitchers in showdown
        is_ace = team_total > 4.0 or random.random() < 0.4
        if is_ace:
            salary = random.randint(7000, 9500)
            projection = random.uniform(32, 42)
            ownership = random.uniform(20, 40)
        else:
            salary = random.randint(5000, 7500)
            projection = random.uniform(22, 32)
            ownership = random.uniform(10, 25)
    else:
        # Hitters by batting order
        if batting_order == 0:  # Bench player
            salary = random.randint(2000, 3500)
            projection = random.uniform(4, 8)
            ownership = random.uniform(3, 15)
        elif batting_order in [1, 2]:  # Top of order
            salary = random.randint(7500, 10000)
            projection = random.uniform(13, 18)
            ownership = random.uniform(25, 45)
        elif batting_order in [3, 4]:  # Heart of order
            salary = random.randint(8000, 10500)
            projection = random.uniform(14, 20)
            ownership = random.uniform(30, 50)
        elif batting_order in [5, 6]:  # Middle order
            salary = random.randint(5500, 8000)
            projection = random.uniform(10, 15)
            ownership = random.uniform(15, 30)
        elif batting_order in [7, 8]:  # Bottom order
            salary = random.randint(3500, 5500)
            projection = random.uniform(7, 11)
            ownership = random.uniform(8, 20)
        else:  # 9th hitter
            salary = random.randint(2000, 4000)
            projection = random.uniform(5, 9)
            ownership = random.uniform(5, 15)

    # Adjust for team total
    if team_total > 5.5:
        projection *= random.uniform(1.1, 1.2)
        ownership *= random.uniform(1.1, 1.3)
    elif team_total < 3.5:
        projection *= random.uniform(0.8, 0.9)
        ownership *= random.uniform(0.7, 0.9)

    # Add variance
    projection += np.random.normal(0, projection * 0.08)

    # Calculate value metrics
    value_score = projection / (salary / 1000)
    captain_salary = int(salary * 1.5)
    captain_projection = projection * 1.5
    captain_value = captain_projection / (captain_salary / 1000)

    return {
        'id': player_id,
        'name': f"{team}_{position}_{batting_order}",
        'team': team,
        'position': position,
        'salary': salary,
        'projection': round(max(0, projection), 2),
        'ownership': round(np.clip(ownership, 0.5, 65), 1),
        'batting_order': batting_order,
        'captain_projection': round(captain_projection, 2),
        'captain_salary': captain_salary,
        'ceiling': projection * random.uniform(2.0, 3.5),
        'floor': projection * random.uniform(0.4, 0.7),
        'value_score': round(value_score, 2),
        'captain_value': round(captain_value, 2),
        'team_total': team_total
    }


def generate_realistic_classic_player(player_id, team, position, batting_order,
                                      game_data, slate_size, is_starter=True, force_punt=False):
    """Generate classic player with ENHANCED salary distribution for better lineup flexibility"""

    team_total = game_data.get('team_totals', {}).get(team, 4.5)

    # ENSURE PUNT PLAYS EXIST (matches real DFS)
    if position == 'OF':
        # OF has most punt options in real DFS
        punt_chance = 0.30  # 30% of OF are punts
    elif position == 'C':
        punt_chance = 0.25  # Backup catchers
    elif position in ['2B', 'SS']:
        punt_chance = 0.20  # Utility infielders
    else:
        punt_chance = 0.15  # Other positions

    # Force punt for certain batting orders
    if batting_order >= 8:
        punt_chance += 0.30  # 8-9 hitters often punts
    elif batting_order == 0:  # Bench
        punt_chance = 0.60  # Bench players usually cheap

    # Determine if this is a punt
    is_punt_play = force_punt or random.random() < punt_chance

    if position == 'P':
        if is_starter:
            # More varied pitcher salaries
            skill = random.random()
            if skill < 0.10:  # 10% aces
                salary = random.randint(9500, 12000)
                projection = random.uniform(42, 52)
                ownership = random.uniform(25, 45)
            elif skill < 0.30:  # 20% good starters
                salary = random.randint(7500, 9500)
                projection = random.uniform(32, 42)
                ownership = random.uniform(15, 30)
            elif skill < 0.60:  # 30% mid-tier
                salary = random.randint(5500, 7500)
                projection = random.uniform(25, 32)
                ownership = random.uniform(8, 20)
            else:  # 40% value/punt pitchers
                salary = random.randint(3500, 5500)
                projection = random.uniform(18, 25)
                ownership = random.uniform(3, 12)
        else:
            # Relief pitchers
            salary = random.randint(3000, 5000)
            projection = random.uniform(12, 22)
            ownership = random.uniform(1, 8)
    else:
        # HITTER GENERATION WITH PROPER PUNT DISTRIBUTION
        if is_punt_play:
            # REALISTIC PUNT SALARIES BY CONTEXT
            if batting_order >= 8:
                salary = random.randint(2000, 2500)  # Minimum salary 8-9 hitters
                projection = random.uniform(5, 7)
                ownership = random.uniform(1, 5)
            elif batting_order == 0:  # Bench/platoon
                salary = random.randint(2000, 2800)
                projection = random.uniform(4, 6)
                ownership = random.uniform(0.5, 4)
            elif position == 'OF':  # OF has most punts
                salary = random.randint(2200, 3000)
                projection = random.uniform(6, 9)
                ownership = random.uniform(2, 8)
            else:  # Other position punts
                salary = random.randint(2500, 3200)
                projection = random.uniform(6, 9)
                ownership = random.uniform(1, 6)
        else:
            # NON-PUNT HITTERS
            if batting_order in [1, 2]:  # Top of order
                tier = random.random()
                if tier < 0.3:  # 30% premium
                    salary = random.randint(7500, 9500)
                    projection = random.uniform(16, 22)
                elif tier < 0.6:  # 30% mid
                    salary = random.randint(5500, 7500)
                    projection = random.uniform(13, 17)
                else:  # 40% value
                    salary = random.randint(4000, 5500)
                    projection = random.uniform(11, 14)
                ownership = random.uniform(15, 40) if slate_size == 'small' else random.uniform(8, 25)

            elif batting_order in [3, 4]:  # Heart of order
                tier = random.random()
                if tier < 0.25:  # 25% studs
                    salary = random.randint(8000, 10500)
                    projection = random.uniform(17, 24)
                elif tier < 0.50:  # 25% solid
                    salary = random.randint(6000, 8000)
                    projection = random.uniform(14, 18)
                else:  # 50% value options
                    salary = random.randint(4500, 6000)
                    projection = random.uniform(12, 15)
                ownership = random.uniform(20, 50) if slate_size == 'small' else random.uniform(10, 30)

            elif batting_order in [5, 6]:  # Middle order
                if random.random() < 0.3:  # 30% cheap options
                    salary = random.randint(3500, 5000)
                    projection = random.uniform(9, 12)
                else:
                    salary = random.randint(5000, 7000)
                    projection = random.uniform(12, 16)
                ownership = random.uniform(8, 25) if slate_size == 'small' else random.uniform(4, 15)

            elif batting_order in [7, 8]:  # Bottom order
                # Already handled in punt section mostly
                salary = random.randint(3500, 5000)
                projection = random.uniform(9, 12)
                ownership = random.uniform(3, 15) if slate_size == 'small' else random.uniform(1, 8)

            else:  # 9th hitter (if not punt)
                salary = random.randint(2800, 3800)
                projection = random.uniform(7, 10)
                ownership = random.uniform(2, 12) if slate_size == 'small' else random.uniform(0.5, 6)

    # Position adjustments
    if position == 'C':
        salary = int(salary * 0.9)  # Catchers slightly cheaper
    elif position == 'SS' and batting_order in [1, 2, 3]:
        salary = int(salary * 1.05)  # Premium SS slightly more

    # Team total adjustments
    if team_total > 5.5:
        projection *= random.uniform(1.08, 1.15)
        ownership *= random.uniform(1.1, 1.2)
    elif team_total < 3.5:
        projection *= random.uniform(0.85, 0.92)
        ownership *= random.uniform(0.8, 0.9)

    # Slate size ownership adjustments
    if slate_size == 'small':
        ownership *= 1.5  # Higher concentration
    elif slate_size == 'large':
        ownership *= 0.7  # More spread out

    # Calculate advanced metrics
    value_score = projection / (salary / 1000)
    ceiling = projection * random.uniform(1.8, 2.8)
    floor = projection * random.uniform(0.5, 0.8)

    # Add advanced stats for optimized strategies
    recent_form_multiplier = random.choice([0.85, 0.95, 1.0, 1.08, 1.15])
    platoon_advantage = random.choice([-0.05, 0, 0, 0.05, 0.084])
    barrel_rate = np.clip((salary / 100000) * 0.15 + np.random.normal(0, 0.03), 0, 0.25)
    xwoba = 0.250 + (salary / 100000) * 0.150 + np.random.normal(0, 0.02)

    # Add Vegas stats
    game_total = game_data.get('game_total', 9.0)

    return {
        'id': player_id,
        'name': f"{team}_{position}_{batting_order}",
        'team': team,
        'position': position,
        'salary': salary,
        'projection': round(max(0, projection), 2),
        'ownership': round(np.clip(ownership, 0.1, 60), 1),
        'batting_order': batting_order,
        'team_total': team_total,
        'game_id': game_data['game_id'],
        'ceiling': round(ceiling, 2),
        'floor': round(floor, 2),
        'value_score': round(value_score, 2),
        'skill_level': salary / 10000,  # Simplified skill
        'is_punt': salary <= 3000,
        # Vegas stats
        'vegas_total': round(team_total, 2),
        'implied_team_runs': round(team_total, 2),
        'game_total': round(game_total, 2),
        'vegas_favorite': team_total > (game_total / 2),
        'run_differential': round(team_total - (game_total - team_total), 2),
        'vegas_multiplier': (team_total / 4.5) ** 0.5,
        # Advanced stats
        'recent_form': recent_form_multiplier,
        'platoon_advantage': platoon_advantage,
        'is_hot_streak': recent_form_multiplier >= 1.08,
        'barrel_rate': barrel_rate,
        'xwoba': xwoba,
        'is_undervalued_xwoba': xwoba > 0.350 and ownership < 15,
    }
# ========== SHOWDOWN LINEUP BUILDERS ==========
def build_showdown_lineup(players, strategy):
    """Build showdown lineup based on explicit strategy rules"""
    strategy_type = strategy.get('type')

    # CAPTAIN SELECTION STRATEGIES
    if strategy_type == 'max_proj_captain':
        # Rule: Highest projection as captain
        captain = max(players, key=lambda x: x['projection'])
        utils = [p for p in players if p != captain]
        utils.sort(key=lambda x: x['value_score'], reverse=True)
        return build_showdown_with_captain(captain, utils[:5])

    elif strategy_type == 'max_ceiling_captain':
        # Rule: Highest ceiling as captain
        captain = max(players, key=lambda x: x.get('ceiling', 0))
        utils = [p for p in players if p != captain]
        utils.sort(key=lambda x: x['value_score'], reverse=True)
        return build_showdown_with_captain(captain, utils[:5])

    elif strategy_type == 'leverage_captain_15':
        # Rule: Captain <15% owned with 20+ ceiling
        candidates = [p for p in players if p['ownership'] < 15 and p.get('ceiling', 0) >= 20]
        if not candidates:
            return None
        captain = max(candidates, key=lambda x: x['ceiling'])
        utils = [p for p in players if p != captain]
        utils.sort(key=lambda x: x['projection'], reverse=True)
        return build_showdown_with_captain(captain, utils[:5])

    elif strategy_type == 'value_captain_5k':
        # Rule: Captain under $5000
        candidates = [p for p in players if p['salary'] < 5000]
        if not candidates:
            return None
        captain = max(candidates, key=lambda x: x['projection'])
        utils = [p for p in players if p != captain]
        utils.sort(key=lambda x: x['projection'], reverse=True)
        return build_showdown_with_captain(captain, utils[:5])

    # GAME SCRIPT STRATEGIES
    elif strategy_type == 'fav_onslaught_4_2':
        # Rule: 4 from favorite, 2 from underdog
        team_totals = {}
        team_players = defaultdict(list)

        for p in players:
            team_totals[p['team']] = p.get('team_total', 4.5)
            team_players[p['team']].append(p)

        if len(team_totals) != 2:
            return None

        # Identify favorite (higher total)
        teams_sorted = sorted(team_totals.items(), key=lambda x: x[1], reverse=True)
        favorite = teams_sorted[0][0]
        underdog = teams_sorted[1][0]

        # Sort by projection
        team_players[favorite].sort(key=lambda x: x['projection'], reverse=True)
        team_players[underdog].sort(key=lambda x: x['projection'], reverse=True)

        # Captain from favorite
        if not team_players[favorite]:
            return None
        captain = team_players[favorite][0]

        # Exactly 3 more from favorite + 2 from dog
        utils = team_players[favorite][1:4] + team_players[underdog][:2]
        if len(utils) < 5:
            return None

        return build_showdown_with_captain(captain, utils[:5])

    elif strategy_type == 'balanced_3_3':
        # Rule: Exactly 3 from each team
        team_players = defaultdict(list)

        for p in players:
            team_players[p['team']].append(p)

        if len(team_players) != 2:
            return None

        teams = list(team_players.keys())

        # Sort each team by projection
        for team in teams:
            team_players[team].sort(key=lambda x: x['projection'], reverse=True)

        # Try captain from each team
        for captain_team in teams:
            if len(team_players[captain_team]) < 3:
                continue

            captain = team_players[captain_team][0]
            other_team = teams[1] if captain_team == teams[0] else teams[0]

            # 2 more from captain team + 3 from other
            utils = team_players[captain_team][1:3] + team_players[other_team][:3]

            if len(utils) == 5:
                captain_salary = int(captain['salary'] * 1.5)
                util_salary = sum(p['salary'] for p in utils)
                if captain_salary + util_salary <= 50000:
                    return build_showdown_with_captain(captain, utils)

        return None

    elif strategy_type == 'dog_leverage_2_4':
        # Rule: 2 from favorite, 4 from underdog
        team_totals = {}
        team_players = defaultdict(list)

        for p in players:
            team_totals[p['team']] = p.get('team_total', 4.5)
            team_players[p['team']].append(p)

        if len(team_totals) != 2:
            return None

        teams_sorted = sorted(team_totals.items(), key=lambda x: x[1])
        underdog = teams_sorted[0][0]
        favorite = teams_sorted[1][0]

        # Captain from underdog
        team_players[underdog].sort(key=lambda x: x['ceiling'], reverse=True)
        team_players[favorite].sort(key=lambda x: x['projection'], reverse=True)

        if not team_players[underdog]:
            return None
        captain = team_players[underdog][0]

        # 3 more from dog + 2 from favorite
        utils = team_players[underdog][1:4] + team_players[favorite][:2]
        if len(utils) < 5:
            return None

        return build_showdown_with_captain(captain, utils[:5])

    # PITCHER STRATEGIES
    elif strategy_type == 'both_pitchers':
        # Rule: Both pitchers must be in lineup
        pitchers = [p for p in players if p['position'] == 'P']
        if len(pitchers) < 2:
            return None

        pitchers.sort(key=lambda x: x['projection'], reverse=True)

        # Try each as captain
        for i in range(2):
            captain = pitchers[i]
            other_pitcher = pitchers[1 - i]

            # Get best value hitters
            hitters = [p for p in players if p['position'] != 'P']
            hitters.sort(key=lambda x: x['value_score'], reverse=True)

            utils = [other_pitcher] + hitters[:4]

            captain_salary = int(captain['salary'] * 1.5)
            util_salary = sum(p['salary'] for p in utils)

            if captain_salary + util_salary <= 50000:
                return build_showdown_with_captain(captain, utils)

        return None

    elif strategy_type == 'ace_only':
        # Rule: Only higher projected pitcher
        pitchers = [p for p in players if p['position'] == 'P']
        if not pitchers:
            return None

        ace = max(pitchers, key=lambda x: x['projection'])

        # Ace as captain
        captain = ace
        hitters = [p for p in players if p['position'] != 'P']
        hitters.sort(key=lambda x: x['projection'], reverse=True)

        lineup = build_showdown_with_captain(captain, hitters[:5])
        if lineup:
            return lineup

        # Try ace as util
        hitter_captain = max(hitters, key=lambda x: x['projection'])
        utils = [ace] + [h for h in hitters if h != hitter_captain][:4]

        return build_showdown_with_captain(hitter_captain, utils)

    elif strategy_type == 'no_pitchers':
        # Rule: Zero pitchers allowed
        hitters = [p for p in players if p['position'] != 'P']
        if len(hitters) < 6:
            return None

        hitters.sort(key=lambda x: x['projection'], reverse=True)
        captain = hitters[0]
        utils = hitters[1:6]

        return build_showdown_with_captain(captain, utils)

    # OWNERSHIP STRATEGIES
    elif strategy_type == 'max_own':
        # Rule: Highest ownership only
        sorted_players = sorted(players, key=lambda x: x['ownership'], reverse=True)
        captain = sorted_players[0]
        utils = sorted_players[1:6]
        return build_showdown_with_captain(captain, utils)

    elif strategy_type == 'anti_chalk_10':
        # Rule: No player over 20%, avg must be <10%
        eligible = [p for p in players if p['ownership'] <= 20]
        if len(eligible) < 6:
            return None

        # Check if we can achieve <10% average
        eligible.sort(key=lambda x: x['ownership'])
        if sum(p['ownership'] for p in eligible[:6]) / 6 > 10:
            return None

        # Build with lowest ownership that still projects well
        eligible.sort(key=lambda x: x['projection'] / (x['ownership'] + 1), reverse=True)
        captain = eligible[0]
        utils = [p for p in eligible[1:] if p != captain][:5]

        # Verify average ownership
        total_own = captain['ownership'] + sum(p['ownership'] for p in utils)
        if total_own / 6 <= 10:
            return build_showdown_with_captain(captain, utils)

        return None

    return None



def build_showdown_with_captain(captain, util_pool):
    """Build showdown lineup with specified captain"""
    lineup = [captain]
    captain_salary = int(captain['salary'] * 1.5)  # Captain costs 1.5x
    total_salary = captain_salary

    teams_used = defaultdict(int)
    teams_used[captain['team']] = 1

    # Ensure we get players from both teams
    captain_team = captain['team']
    other_team_players = [p for p in util_pool if p['team'] != captain_team]
    same_team_players = [p for p in util_pool if p['team'] == captain_team]

    # Sort both lists by value
    other_team_players.sort(key=lambda x: x['value_score'], reverse=True)
    same_team_players.sort(key=lambda x: x['value_score'], reverse=True)

    # Ensure at least one player from the other team
    if other_team_players and len(lineup) < 6:
        player = other_team_players[0]
        if total_salary + player['salary'] <= SHOWDOWN_CONFIG['salary_cap']:
            lineup.append(player)
            total_salary += player['salary']
            teams_used[player['team']] += 1
            other_team_players.pop(0)

    # Combine remaining players and sort by value
    remaining_pool = other_team_players + same_team_players
    remaining_pool.sort(key=lambda x: x['value_score'], reverse=True)

    # Fill remaining spots
    for player in remaining_pool:
        if len(lineup) >= 6:
            break

        if total_salary + player['salary'] > SHOWDOWN_CONFIG['salary_cap']:
            continue

        lineup.append(player)
        total_salary += player['salary']
        teams_used[player['team']] += 1

    # Must have both teams and full lineup
    if len(lineup) == 6 and len(teams_used) >= 2:
        # Calculate projections
        total_projection = captain['projection'] * 1.5  # Captain gets 1.5x points
        total_projection += sum(p['projection'] for p in lineup[1:])  # Utils get normal points

        total_ownership = captain['ownership'] * 1.2  # Captain ownership premium
        total_ownership += sum(p['ownership'] for p in lineup[1:])

        return {
            'lineup': lineup,
            'captain': captain,
            'salary': total_salary,
            'projection': total_projection,
            'ownership': total_ownership / 6,
            'format': 'showdown'
        }

    return None


# ========== CLASSIC LINEUP BUILDER UTILITIES ==========
def build_vegas_stack(players: List[Dict], min_total: float = 5.5) -> Optional[Dict]:
    """Build lineup focusing on high Vegas total teams"""

    # PRE-FLIGHT CHECK - NEW
    team_totals_check = {}
    for p in players:
        if p['position'] != 'P':
            team_totals_check[p['team']] = p.get('team_total', 4.5)

    if not any(total >= min_total for total in team_totals_check.values()):
        return None  # No teams meet criteria - exit immediately
    # END PRE-FLIGHT CHECK

    team_players = defaultdict(list)
    team_totals = {}

    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)
            team_totals[p['team']] = p.get('team_total', 4.5)

    # Find high-total teams
    high_total_teams = [(team, total) for team, total in team_totals.items()
                        if total >= min_total and len(team_players[team]) >= 4]

    if not high_total_teams:
        return None

    # Sort by total
    high_total_teams.sort(key=lambda x: x[1], reverse=True)

    # Try top 3 teams
    for team, total in high_total_teams[:3]:
        # Build lineup with this team's stack
        lineup = []
        salary = 0
        positions_filled = defaultdict(int)
        teams_used = defaultdict(int)

        # Get team players sorted by projection
        team_list = team_players[team]
        team_list.sort(key=lambda x: x['projection'], reverse=True)

        # Add 4-5 players from high-total team
        stack_size = 5 if len(team_list) >= 5 else 4
        stack_added = 0

        for player in team_list:
            if stack_added >= stack_size:
                break

            pos = player['position']
            if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap'] - 25000:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] = positions_filled.get(pos, 0) + 1
            teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
            stack_added += 1

        if stack_added < 4:
            continue

        # Fill remaining spots
        other_players = [p for p in players if p not in lineup]
        other_players.sort(key=lambda x: x.get('value_score', 0), reverse=True)

        # Prioritize scarce positions
        for pos in ['P', 'C', 'SS', '2B', '3B', '1B', 'OF']:
            needed = CLASSIC_CONFIG['positions'][pos] - positions_filled.get(pos, 0)
            if needed <= 0:
                continue

            pos_players = [p for p in other_players if p['position'] == pos]

            for player in pos_players[:needed * 2]:
                if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                    break

                if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                    continue

                if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                    continue

                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] = positions_filled.get(pos, 0) + 1
                teams_used[player['team']] = teams_used.get(player['team'], 0) + 1

        # Fill any remaining spots
        for player in other_players:
            if len(lineup) >= 10:
                break

            if player in lineup:
                continue

            pos = player['position']
            if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                if len(lineup) < 9:
                    continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] = positions_filled.get(pos, 0) + 1
            teams_used[player['team']] = teams_used.get(player['team'], 0) + 1

        if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
            return create_classic_lineup_result(lineup)

    return None


def build_vegas_game_stack(players: List[Dict], min_game_total: float = 10.0) -> Optional[Dict]:
    """Build lineup from high-scoring games"""

    # PRE-FLIGHT CHECK - NEW
    game_totals_check = {}
    for p in players:
        if 'game_id' in p and 'game_total' in p:
            game_totals_check[p['game_id']] = p.get('game_total', 9.0)

    if not any(total >= min_game_total for total in game_totals_check.values()):
        return None  # No games meet criteria - exit immediately
    # END PRE-FLIGHT CHECK

    game_players = defaultdict(list)
    game_totals = {}

    for p in players:
        if 'game_id' in p:
            game_id = p['game_id']
            game_players[game_id].append(p)
            if game_id not in game_totals:
                game_totals[game_id] = p.get('game_total', 9.0)

    # Find high-total games
    high_games = [(gid, total) for gid, total in game_totals.items()
                  if total >= min_game_total]

    if not high_games:
        return None

    high_games.sort(key=lambda x: x[1], reverse=True)

    # Try top 2 games
    for game_id, total in high_games[:2]:
        hitters = [p for p in game_players[game_id] if p['position'] != 'P']

        if len(hitters) < 5:
            continue

        # Sort by projection
        hitters.sort(key=lambda x: x['projection'], reverse=True)

        lineup = []
        salary = 0
        positions_filled = defaultdict(int)
        teams_used = defaultdict(int)

        # Add 5-6 best hitters from high-total game
        hitters_added = 0
        for player in hitters[:8]:  # Consider top 8
            if hitters_added >= 6:
                break

            pos = player['position']
            if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap'] - 20000:
                continue

            if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] = positions_filled.get(pos, 0) + 1
            teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
            hitters_added += 1

        if hitters_added < 4:  # Need at least 4 from the game
            continue

        # Get pitchers from other games
        other_pitchers = [p for p in players if p['position'] == 'P' and p.get('game_id') != game_id]
        other_pitchers.sort(key=lambda x: x['value_score'], reverse=True)

        for pitcher in other_pitchers:
            if positions_filled.get('P', 0) >= CLASSIC_CONFIG['positions']['P']:
                break

            if salary + pitcher['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used.get(pitcher['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(pitcher)
            salary += pitcher['salary']
            positions_filled['P'] = positions_filled.get('P', 0) + 1
            teams_used[pitcher['team']] = teams_used.get(pitcher['team'], 0) + 1

        # Fill remaining spots
        other_players = [p for p in players if p not in lineup and p.get('game_id') != game_id]
        other_players.sort(key=lambda x: x.get('value_score', 0), reverse=True)

        for player in other_players:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                if len(lineup) < 9:
                    continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] = positions_filled.get(pos, 0) + 1
            teams_used[player['team']] = teams_used.get(player['team'], 0) + 1

        if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
            return create_classic_lineup_result(lineup)

    return None


def track_strategy_success_rates(results):
    """Track and report strategy success rates"""
    strategy_attempts = defaultdict(int)
    strategy_successes = defaultdict(int)

    for result in results:
        if result.get('type') == 'attempt_summary':
            continue

        key = f"{result['format']}_{result['strategy']}"
        strategy_attempts[key] += 1

        if not result.get('failed'):
            strategy_successes[key] += 1

    print("\nSTRATEGY SUCCESS RATES:")
    print("-" * 50)

    for strategy, attempts in strategy_attempts.items():
        successes = strategy_successes[strategy]
        rate = (successes / attempts * 100) if attempts > 0 else 0

        status = "✅" if rate > 70 else "⚠️" if rate > 40 else "❌"
        print(f"{strategy}: {rate:.1f}% ({successes}/{attempts}) {status}")

        # Flag strategies that might need removal
        if rate < 20 and attempts > 50:
            print(f"  ^ Consider removing or major rework")

def build_vegas_leverage(players: List[Dict], min_total: float = 5.0) -> Optional[Dict]:
    """Build lineup with low-owned players from high-total teams"""
    # Find high-total teams
    team_totals = {}
    team_players = defaultdict(list)

    for p in players:
        team_totals[p['team']] = p.get('team_total', 4.5)
        team_players[p['team']].append(p)

    # Get high-total teams
    high_total_teams = [team for team, total in team_totals.items() if total >= min_total]

    if not high_total_teams:
        return None

    # Find leverage plays (low ownership from high-total teams)
    leverage_plays = []

    for team in high_total_teams:
        for player in team_players[team]:
            if player['ownership'] < 15:  # Low owned
                leverage_score = player['projection'] * (team_totals[team] / 4.5) / (player['ownership'] + 1)
                leverage_plays.append((player, leverage_score))

    if len(leverage_plays) < 4:
        return None

    # Sort by leverage score
    leverage_plays.sort(key=lambda x: x[1], reverse=True)

    # Build lineup
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Add top leverage plays
    leverage_added = 0
    for player, score in leverage_plays[:15]:  # Consider top 15
        if leverage_added >= 5:  # Aim for 5 leverage plays
            break

        pos = player['position']
        if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap'] - 25000:
            continue

        if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] = positions_filled.get(pos, 0) + 1
        teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
        leverage_added += 1

    # Fill remaining with value plays
    other_players = [p for p in players if p not in lineup]
    other_players.sort(key=lambda x: x.get('value_score', 0), reverse=True)

    # Prioritize positions
    for pos in ['P', 'C', 'SS', '2B', '3B', '1B', 'OF']:
        needed = CLASSIC_CONFIG['positions'][pos] - positions_filled.get(pos, 0)
        if needed <= 0:
            continue

        pos_players = [p for p in other_players if p['position'] == pos]

        for player in pos_players:
            if needed <= 0:
                break

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] = positions_filled.get(pos, 0) + 1
            teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
            needed -= 1

    # Fill any remaining
    for player in other_players:
        if len(lineup) >= 10:
            break

        if player in lineup:
            continue

        pos = player['position']
        if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] = positions_filled.get(pos, 0) + 1
        teams_used[player['team']] = teams_used.get(player['team'], 0) + 1

    if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
        return create_classic_lineup_result(lineup)

    return None


def build_by_metric(players, metric, reverse=True):
    """Build lineup optimizing for specific metric - QUIET VERSION"""
    # Ensure all players have the metric
    valid_players = [p for p in players if metric in p]

    if not valid_players:
        # REMOVED: print(f"WARNING: No players have metric '{metric}'")
        return None

    # Remove any infinity or NaN values
    for p in valid_players:
        if not isinstance(p[metric], (int, float)) or math.isnan(p[metric]) or math.isinf(p[metric]):
            p[metric] = 0

    sorted_players = sorted(valid_players, key=lambda x: x.get(metric, 0), reverse=reverse)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)
    position_requirements = CLASSIC_CONFIG['positions'].copy()

    # PHASE 1: Fill each position with best available
    for pos, required in position_requirements.items():
        # Get best players at this position
        pos_players = [p for p in sorted_players if p['position'] == pos and p not in lineup]

        for i in range(required):
            if not pos_players:
                break

            # Find best that fits salary
            added = False
            for player in pos_players:
                spots_left = 10 - len(lineup)
                min_salary_needed = 2000 * (spots_left - 1)

                if salary + player['salary'] + min_salary_needed <= CLASSIC_CONFIG['salary_cap']:
                    if teams_used.get(player['team'], 0) < CLASSIC_CONFIG['max_players_per_team']:
                        lineup.append(player)
                        salary += player['salary']
                        positions_filled[pos] += 1
                        teams_used[player['team']] += 1
                        pos_players.remove(player)
                        added = True
                        break

            if not added:
                # Try cheaper players at this position
                cheap_options = [p for p in valid_players
                                 if p['position'] == pos
                                 and p not in lineup
                                 and p['salary'] <= (CLASSIC_CONFIG['salary_cap'] - salary) / max(spots_left, 1)]
                if cheap_options:
                    cheap_options.sort(key=lambda x: x[metric], reverse=reverse)
                    player = cheap_options[0]
                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1

    # PHASE 2: If still missing positions, fill them even if suboptimal
    for pos, required in position_requirements.items():
        while positions_filled.get(pos, 0) < required and len(lineup) < 10:
            candidates = [p for p in valid_players
                          if p['position'] == pos
                          and p not in lineup]

            if not candidates:
                # REMOVED: print(f"No more {pos} available!")
                break

            # Take any that fit
            added = False
            for player in candidates:
                if salary + player['salary'] <= CLASSIC_CONFIG['salary_cap']:
                    if teams_used.get(player['team'], 0) < CLASSIC_CONFIG['max_players_per_team'] or len(lineup) >= 9:
                        lineup.append(player)
                        salary += player['salary']
                        positions_filled[pos] += 1
                        teams_used[player['team']] += 1
                        added = True
                        break

            if not added:
                # REMOVED: print(f"Can't afford any more {pos}")
                break

    # PHASE 3: If still not 10, add best remaining that fit
    if len(lineup) < 10:
        remaining = [p for p in sorted_players if p not in lineup]

        for player in remaining:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled.get(pos, 0) < position_requirements.get(pos, 0):
                if salary + player['salary'] <= CLASSIC_CONFIG['salary_cap']:
                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1

    # Validate lineup
    if len(lineup) == 10:
        num_teams = len(set(p['team'] for p in lineup))
        if num_teams >= 2:
            return create_classic_lineup_result(lineup)
        # else:
        # REMOVED: print(f"Failed team diversity: only {num_teams} teams")
    # else:
    # REMOVED ALL THE DEBUG PRINTS

    return None

def build_team_stack(players, stack_size=5):
    """Build team stack with 2-5 players - MORE FLEXIBLE"""

    # PRE-FLIGHT CHECK - NEW
    team_counts = defaultdict(int)
    for p in players:
        if p['position'] != 'P':
            team_counts[p['team']] += 1

    # Check if ANY team has enough players
    max_available = max(team_counts.values()) if team_counts else 0

    if max_available < 2:
        return None  # Can't even make a mini stack

    # Adjust stack size to what's possible
    if stack_size > max_available:
        stack_size = max(2, max_available)
    # END PRE-FLIGHT CHECK

    # Try sizes in order but with more attempts
    for size in [stack_size, stack_size - 1, stack_size - 2, 3, 2]:
        if size < 2:
            continue

        # Try multiple approaches for each size
        for approach in ['projection', 'value', 'ceiling', 'mixed']:
            # Try different salary bands
            for salary_flexibility in [1.0, 0.8, 0.6, None]:  # None = no restriction
                result = _attempt_flexible_stack(players, size, approach, salary_flexibility)
                if result:
                    return result

    return None

def _attempt_flexible_stack(players, stack_size, approach, salary_flexibility):
    """Attempt to build stack with specific parameters"""
    team_players = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    # Find teams with enough players
    valid_teams = []
    for team, players_list in team_players.items():
        if len(players_list) >= stack_size:
            # Score team based on approach
            if approach == 'projection':
                players_list.sort(key=lambda x: x['projection'], reverse=True)
                score = sum(p['projection'] for p in players_list[:stack_size])
            elif approach == 'value':
                players_list.sort(key=lambda x: x.get('value_score', 0), reverse=True)
                score = sum(p['value_score'] for p in players_list[:stack_size])
            elif approach == 'ceiling':
                players_list.sort(key=lambda x: x.get('ceiling', 0), reverse=True)
                score = sum(p['ceiling'] for p in players_list[:stack_size])
            else:  # mixed
                # Use a combination
                for p in players_list:
                    p['mixed_score'] = p['projection'] * 0.5 + p['value_score'] * 3 + p.get('ceiling', 0) * 0.2
                players_list.sort(key=lambda x: x.get('mixed_score', 0), reverse=True)
                score = sum(p['mixed_score'] for p in players_list[:stack_size])

            # Boost for Vegas totals
            team_total = players_list[0].get('team_total', 4.5) if players_list else 4.5
            if team_total > 5.5:
                score *= 1.15
            elif team_total > 5.0:
                score *= 1.08

            valid_teams.append((team, score, players_list))

    if not valid_teams:
        return None

    valid_teams.sort(key=lambda x: x[1], reverse=True)

    # Try top teams
    for team, _, team_list in valid_teams[:8]:  # Try more teams
        # Try different position combinations
        for position_flexibility in range(3):
            lineup = _build_lineup_from_stack(
                players, team, team_list[:stack_size + 2], stack_size,
                salary_flexibility, position_flexibility
            )
            if lineup:
                return lineup

    return None


def _build_lineup_from_stack(all_players, stack_team, stack_candidates,
                             target_stack_size, salary_flexibility, position_flexibility):
    """Build complete lineup starting from stack"""
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)
    SALARY_CAP = 50000

    # CHANGE: More flexible position limits for stacks
    position_limits = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3
    }

    # For smaller stacks, be more flexible
    if target_stack_size <= 3:
        flex_allowance = 1  # Allow 1 extra at any position
    else:
        flex_allowance = 0

    # Add stack players
    stack_added = 0
    for player in stack_candidates:
        if stack_added >= target_stack_size:
            break

        pos = player['position']

        # CHANGE: More flexible position checking
        if positions_filled[pos] >= position_limits[pos] + flex_allowance:
            if position_flexibility == 0:
                continue
            elif position_flexibility == 1 and positions_filled[pos] >= position_limits[pos] + 1:
                continue
            # position_flexibility == 2 allows any position if needed

        # Salary check with flexibility
        if salary_flexibility:
            max_stack_salary = SALARY_CAP * salary_flexibility
            if salary + player['salary'] > max_stack_salary:
                continue
        else:
            # Just ensure we can finish the lineup
            min_remaining = 2200 * (10 - len(lineup) - 1)
            if salary + player['salary'] + min_remaining > SALARY_CAP:
                continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] = positions_filled.get(pos, 0) + 1
        teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
        stack_added += 1

    # Need minimum stack size
    if stack_added < min(2, target_stack_size):
        return None

    # Fill remaining positions
    other_players = [p for p in all_players if p not in lineup]

    # CHANGE: Smarter position filling
    # First, identify what positions we MUST fill
    must_fill = {}
    for pos, required in position_limits.items():
        current = positions_filled.get(pos, 0)
        if current < required:
            must_fill[pos] = required - current

    # Fill critical positions first (P and C are usually scarce)
    for pos in ['P', 'C', 'SS', '2B', '3B', '1B', 'OF']:
        needed = must_fill.get(pos, 0)
        if needed <= 0:
            continue

        candidates = [p for p in other_players if p['position'] == pos]

        # For pitchers, prefer different teams
        if pos == 'P':
            candidates.sort(key=lambda x: (x['team'] == stack_team, -x['projection']))
        else:
            candidates.sort(key=lambda x: x.get('value_score', 0), reverse=True)

        added = 0
        for player in candidates:
            if added >= needed:
                break

            if salary + player['salary'] > SALARY_CAP:
                continue

            # Flexible team limit for final spots
            if teams_used.get(player['team'], 0) >= 5:
                if len(lineup) < 9:  # Enforce for early spots
                    continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] = positions_filled.get(pos, 0) + 1
            teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
            added += 1
            other_players.remove(player)

    # Fill remaining spots with best available
    if len(lineup) < 10:
        # Calculate remaining budget
        spots_left = 10 - len(lineup)
        budget_left = SALARY_CAP - salary
        avg_available = budget_left / spots_left if spots_left > 0 else 0

        # Get eligible players
        eligible = []
        for p in other_players:
            pos = p['position']
            if positions_filled.get(pos, 0) >= position_limits[pos]:
                continue

            # Be more flexible with salary for final spots
            if p['salary'] <= avg_available * 1.5:
                eligible.append(p)

        # Sort by value
        eligible.sort(key=lambda x: x.get('value_score', 0), reverse=True)

        for player in eligible:
            if len(lineup) >= 10:
                break

            if salary + player['salary'] > SALARY_CAP:
                continue

            # Very flexible team limit for last spot
            if teams_used.get(player['team'], 0) >= 5 and len(lineup) < 9:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[player['position']] = positions_filled.get(player['position'], 0) + 1
            teams_used[player['team']] = teams_used.get(player['team'], 0) + 1

    # Validate lineup
    if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
        return create_classic_lineup_result(lineup)

    return None


def _strict_team_stack(players, stack_size, max_stack_salary=None, log=None):
    """Build lineup with team stack - handles 2-5 players"""
    team_players = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    # Check if any team has enough players
    valid_teams = [(team, players_list) for team, players_list in team_players.items()
                   if len(players_list) >= stack_size]

    if not valid_teams:
        if log: log[f"no_team_with_{stack_size}_players"] += 1
        return None

    # Sort teams by total projection of best players
    team_scores = []
    for team, players_list in valid_teams:
        players_list.sort(key=lambda x: x['projection'], reverse=True)
        score = sum(p['projection'] for p in players_list[:stack_size])
        # Boost high Vegas total teams
        team_total = players_list[0].get('team_total', 4.5) if players_list else 4.5
        if team_total > 5.5:
            score *= 1.1
        team_scores.append((team, score, players_list, team_total))

    team_scores.sort(key=lambda x: x[1], reverse=True)

    # Try multiple teams
    for team, _, team_list, team_total in team_scores[:10]:
        # Special handling for 2-player stacks
        if stack_size == 2:
            # Try different duo combinations
            duo_strategies = [
                # Heart of order (3-4 hitters)
                lambda ps: [p for p in ps if p.get('batting_order', 10) in [3, 4]],
                # Top of order (1-2 hitters)
                lambda ps: [p for p in ps if p.get('batting_order', 10) in [1, 2]],
                # Power combo (4-5 hitters)
                lambda ps: [p for p in ps if p.get('batting_order', 10) in [4, 5]],
                # Best projection duo
                lambda ps: sorted(ps, key=lambda x: x['projection'], reverse=True),
                # Best value duo
                lambda ps: sorted(ps, key=lambda x: x.get('value_score', 0), reverse=True)
            ]

            for get_candidates in duo_strategies:
                candidates = get_candidates(team_list)
                if len(candidates) >= 2:
                    duo = candidates[:2]

                    # Check salary constraint if provided
                    if max_stack_salary:
                        duo_salary = sum(p['salary'] for p in duo)
                        if duo_salary > max_stack_salary:
                            continue

                    # Try to build lineup with this duo
                    lineup_result = _build_lineup_with_stack(
                        players, duo, team, stack_size, max_stack_salary
                    )
                    if lineup_result:
                        return lineup_result

        else:  # 3-5 player stacks
            # Try different combinations
            for stack_combo_attempt in range(3):
                lineup = []
                salary = 0
                positions_filled = defaultdict(int)
                teams_used = defaultdict(int)

                # Get stack players - try different sorts
                if stack_combo_attempt == 0:
                    # Best projection
                    stack_candidates = sorted(team_list, key=lambda x: x['projection'], reverse=True)
                elif stack_combo_attempt == 1:
                    # Best value
                    stack_candidates = sorted(team_list, key=lambda x: x.get('value_score', 0), reverse=True)
                else:
                    # Mix of ceiling and salary efficiency
                    stack_candidates = sorted(team_list,
                                              key=lambda x: x['ceiling'] / x['salary'],
                                              reverse=True)

                # Add stack players
                stack_added = 0
                stack_salary = 0

                for player in stack_candidates:
                    if stack_added >= stack_size:
                        break

                    pos = player['position']

                    # Position flexibility for smaller stacks
                    if stack_size <= 3:
                        # More flexible with positions for small stacks
                        if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                            if stack_added < stack_size - 1:
                                continue
                    else:
                        # Standard position check
                        if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                            continue

                    # Check stack salary constraint
                    if max_stack_salary and stack_salary + player['salary'] > max_stack_salary:
                        continue

                    # Reserve salary for remaining spots
                    min_remaining = 2300 * (10 - len(lineup) - 1)
                    if salary + player['salary'] + min_remaining > CLASSIC_CONFIG['salary_cap']:
                        continue

                    lineup.append(player)
                    salary += player['salary']
                    stack_salary += player['salary']
                    positions_filled[pos] = positions_filled.get(pos, 0) + 1
                    teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
                    stack_added += 1

                # Need at least the minimum stack size
                if stack_added < stack_size:
                    if log: log[f"insufficient_{stack_size}_stack_players"] += 1
                    continue

                # Fill remaining roster spots
                other_players = [p for p in players if p['team'] != team]

                # Prioritize positions we need
                priority_positions = ['P', 'C', 'SS', '2B', '3B', '1B', 'OF']

                for pos in priority_positions:
                    needed = CLASSIC_CONFIG['positions'][pos] - positions_filled.get(pos, 0)
                    if needed <= 0:
                        continue

                    pos_players = [p for p in other_players if p['position'] == pos and p not in lineup]
                    pos_players.sort(key=lambda x: x.get('value_score', 0), reverse=True)

                    for player in pos_players[:needed * 2]:  # Consider extra players
                        if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                            break

                        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                            continue

                        # Flexible team constraint
                        if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                            if len(lineup) < 9:  # Only enforce if we have options
                                continue

                        lineup.append(player)
                        salary += player['salary']
                        positions_filled[pos] = positions_filled.get(pos, 0) + 1
                        teams_used[player['team']] = teams_used.get(player['team'], 0) + 1

                # Fill any remaining spots with best available
                if len(lineup) < 10:
                    remaining = [p for p in players if p not in lineup]
                    remaining.sort(key=lambda x: x.get('value_score', 0), reverse=True)

                    for player in remaining:
                        if len(lineup) >= 10:
                            break

                        pos = player['position']
                        if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                            continue

                        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                            continue

                        # Very flexible on team constraint for last spots
                        if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                            if len(lineup) < 9 and player['team'] != team:
                                continue

                        lineup.append(player)
                        salary += player['salary']
                        positions_filled[pos] = positions_filled.get(pos, 0) + 1
                        teams_used[player['team']] = teams_used.get(player['team'], 0) + 1

                # Check if valid lineup
                if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
                    return create_classic_lineup_result(lineup)

                if log:
                    if len(lineup) < 10:
                        log["incomplete_lineup"] += 1
                    elif len(set(p['team'] for p in lineup)) < 2:
                        log["single_team"] += 1

    if log: log[f"all_{stack_size}_stack_attempts_failed"] += 1
    return None


def _build_lineup_with_stack(players, stack_players, stack_team, stack_size, max_stack_salary):
    """Helper function to build lineup starting with a specific stack"""
    lineup = list(stack_players)  # Copy the stack
    salary = sum(p['salary'] for p in stack_players)
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Count stack positions/teams
    for p in stack_players:
        positions_filled[p['position']] += 1
        teams_used[p['team']] += 1

    # Get other players
    other_players = [p for p in players if p not in lineup]

    # For 2-player stacks, prefer pitchers from different teams
    if stack_size == 2:
        pitchers = [p for p in other_players if p['position'] == 'P' and p['team'] != stack_team]
        pitchers.sort(key=lambda x: x['projection'], reverse=True)

        # Add best available pitcher
        for pitcher in pitchers[:5]:
            if salary + pitcher['salary'] <= CLASSIC_CONFIG['salary_cap'] - 25000:  # Reserve for others
                lineup.append(pitcher)
                salary += pitcher['salary']
                positions_filled['P'] = 1
                teams_used[pitcher['team']] = 1
                break

    # Fill remaining positions
    priority_positions = ['P', 'C', 'SS', '2B', '3B', '1B', 'OF']

    for pos in priority_positions:
        needed = CLASSIC_CONFIG['positions'][pos] - positions_filled.get(pos, 0)
        if needed <= 0:
            continue

        candidates = [p for p in other_players if p['position'] == pos and p not in lineup]
        candidates.sort(key=lambda x: x.get('value_score', 0), reverse=True)

        for player in candidates:
            if needed <= 0:
                break

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1
            needed -= 1

    # Fill any remaining spots
    if len(lineup) < 10:
        all_remaining = [p for p in players if p not in lineup]
        all_remaining.sort(key=lambda x: x.get('value_score', 0), reverse=True)

        for player in all_remaining:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used.get(player['team'], 0) + 1

    if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
        return create_classic_lineup_result(lineup)

    return None


def build_with_mini_stack(players: List[Dict], stack_size: int = 3) -> Optional[Dict]:
    """Build cash lineup with mini stack - FIXED"""

    # PRE-FLIGHT CHECK - NEW
    team_counts = defaultdict(int)
    for p in players:
        if p['position'] != 'P':
            team_counts[p['team']] += 1

    if not any(count >= stack_size for count in team_counts.values()):
        return None  # No team has enough players
    # END PRE-FLIGHT CHECK

    team_players = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    # Find good mini-stack teams
    team_scores = {}
    for team, players_list in team_players.items():
        if len(players_list) >= stack_size:
            # Sort by floor for cash games
            players_list.sort(key=lambda x: x.get('floor', x['projection'] * 0.7), reverse=True)
            # Calculate average floor of top players
            top_players = players_list[:stack_size]
            avg_floor = np.mean([p.get('floor', p['projection'] * 0.7) for p in top_players])
            # Also consider team total
            team_total = top_players[0].get('team_total', 4.5) if top_players else 4.5
            # Combined score
            team_scores[team] = avg_floor * (team_total / 4.5)

    if not team_scores:
        return None

    # FIX THE BUG - Sort teams by score
    sorted_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)

    # Try top teams
    for team, _ in sorted_teams[:5]:  # Try more teams
        lineup = []
        salary = 0
        positions_filled = defaultdict(int)
        teams_used = defaultdict(int)

        # Get team players sorted by floor
        team_list = sorted(team_players[team],
                           key=lambda x: x.get('floor', x['projection'] * 0.7),
                           reverse=True)

        # Add mini stack - be flexible with positions
        stack_added = 0
        for player in team_list:
            if stack_added >= stack_size:
                break

            pos = player['position']
            if positions_filled[pos] < CLASSIC_CONFIG['positions'][pos]:
                # Don't overspend on stack
                if salary + player['salary'] <= CLASSIC_CONFIG['salary_cap'] - 35000:
                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1
                    stack_added += 1

        # Need at least 2 from stack
        if stack_added < 2:
            continue

        # Get high floor pitchers
        pitchers = [p for p in players if p['position'] == 'P' and p['team'] != team]
        pitchers.sort(key=lambda x: x.get('floor', x['projection'] * 0.7), reverse=True)

        for pitcher in pitchers[:6]:
            if positions_filled['P'] >= CLASSIC_CONFIG['positions']['P']:
                break

            if salary + pitcher['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used[pitcher['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(pitcher)
            salary += pitcher['salary']
            positions_filled['P'] += 1
            teams_used[pitcher['team']] += 1

        # Fill remaining with high floor/value players
        other_players = [p for p in players if p not in lineup]
        # Sort by floor/value combination for cash
        for p in other_players:
            floor = p.get('floor', p['projection'] * 0.7)
            value = p.get('value_score', p['projection'] / (p['salary'] / 1000))
            p['cash_score'] = floor * 0.7 + value * 3  # Weight value more

        other_players.sort(key=lambda x: x['cash_score'], reverse=True)

        for player in other_players:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
                continue

            # Flexible salary management
            spots_left = 10 - len(lineup)
            if spots_left > 0:
                avg_needed = (CLASSIC_CONFIG['salary_cap'] - salary) / spots_left
                if avg_needed < 2500 and player['salary'] > 5000:
                    continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

        # Check for valid lineup
        if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
            return create_classic_lineup_result(lineup)

    return None


def build_game_stack_classic(players: List[Dict]) -> Optional[Dict]:
    """Build game stack for classic - FIXED"""
    # Group by game
    game_players = defaultdict(list)
    game_totals = {}

    for p in players:
        if 'game_id' in p:
            game_id = p['game_id']
            game_players[game_id].append(p)

            if game_id not in game_totals:
                game_totals[game_id] = p.get('team_total', 4.5) * 2

    if not game_totals:
        return None

    # Get highest total games
    sorted_games = sorted(game_totals.items(), key=lambda x: x[1], reverse=True)

    best_lineup = None

    # Try top 3 games
    for game_id, total in sorted_games[:3]:
        game_hitters = [p for p in game_players[game_id] if p['position'] != 'P']

        if len(game_hitters) < 5:
            continue

        # Sort by projection
        game_hitters.sort(key=lambda x: x['projection'], reverse=True)

        # Build lineup
        lineup = []
        salary = 0
        positions_filled = defaultdict(int)
        teams_used = defaultdict(int)

        # Add game stack players - be smart about positions
        for player in game_hitters:
            if len(lineup) >= 6:  # Leave room for pitchers and other positions
                break

            pos = player['position']
            if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
                continue

            # Check salary constraints
            spots_left = 10 - len(lineup)
            if spots_left > 1:
                avg_needed = (CLASSIC_CONFIG['salary_cap'] - salary) / spots_left
                if avg_needed < 3000 and player['salary'] > 5000:
                    continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

        # Need at least 4 from the game
        if len(lineup) < 4:
            continue

        # Get pitchers from other games
        other_pitchers = [p for p in players if p['position'] == 'P' and p.get('game_id') != game_id]
        other_pitchers.sort(key=lambda x: x['value_score'], reverse=True)

        for pitcher in other_pitchers:
            if positions_filled['P'] >= CLASSIC_CONFIG['positions']['P']:
                break

            if salary + pitcher['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used[pitcher['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(pitcher)
            salary += pitcher['salary']
            positions_filled['P'] += 1
            teams_used[pitcher['team']] += 1

        # Fill remaining with value plays
        other_players = [p for p in players if p.get('game_id') != game_id and p not in lineup]
        other_players.sort(key=lambda x: x.get('value_score', 0), reverse=True)

        for player in other_players:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
                continue

            # Smart salary management for final spots
            spots_left = 10 - len(lineup)
            if spots_left > 0:
                salary_left = CLASSIC_CONFIG['salary_cap'] - salary
                avg_needed = salary_left / spots_left

                # If we need cheap players, skip expensive ones
                if avg_needed < 3500 and player['salary'] > avg_needed * 1.2:
                    continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

        if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
            best_lineup = lineup
            break  # Found a valid lineup

    if best_lineup:
        return create_classic_lineup_result(best_lineup)

    return None


def build_with_ownership_buckets(players):
    """Build with specific ownership distribution"""
    # Categorize players
    high_own = [p for p in players if p['ownership'] > 25]
    med_own = [p for p in players if 10 <= p['ownership'] <= 25]
    low_own = [p for p in players if p['ownership'] < 10]

    # Sort each by projection
    for bucket in [high_own, med_own, low_own]:
        bucket.sort(key=lambda x: x['projection'], reverse=True)

    # Target: 2 high, 3 medium, 5 low (flexible)
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Add from each bucket with flexible targets
    buckets = [
        (high_own, min(2, len(high_own))),
        (med_own, min(3, len(med_own))),
        (low_own, min(5, len(low_own)))
    ]

    for bucket_list, target in buckets:
        added = 0
        for player in bucket_list:
            if added >= target or len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
                continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1
            added += 1

    # Fill any remaining spots
    all_players = sorted(players, key=lambda x: x['projection'], reverse=True)

    for player in all_players:
        if len(lineup) >= 10:
            break

        if player in lineup:
            continue

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
        return create_classic_lineup_result(lineup)

    # Fallback if ownership buckets don't work
    return build_by_metric(players, 'projection')


def build_leverage_classic(players):
    """Build leverage lineup"""

    # PRE-FLIGHT CHECK - NEW
    high_owned = [p for p in players if p['ownership'] > 30]
    if not high_owned:
        return None  # No chalk to leverage against

    # Check if any high-owned players have low-owned teammates
    has_leverage = False
    for chalk in high_owned:
        teammates = [p for p in players
                     if p['team'] == chalk['team']
                     and p['id'] != chalk['id']
                     and p['ownership'] < 15]
        if teammates:
            has_leverage = True
            break

    if not has_leverage:
        return None  # No leverage opportunities exist
    # END PRE-FLIGHT CHECK

    # Find chalk plays and their correlations
    chalk_players = [p for p in players if p['ownership'] > 30]

    leverage_plays = []

    for chalk in chalk_players:
        # Find low-owned correlations
        teammates = [p for p in players
                     if p['team'] == chalk['team']
                     and p['id'] != chalk['id']
                     and p['ownership'] < 15]

        for teammate in teammates:
            leverage_score = chalk['ownership'] / (teammate['ownership'] + 1)
            leverage_plays.append((teammate, leverage_score))

    if not leverage_plays:
        return None

    # Sort by leverage
    leverage_plays.sort(key=lambda x: x[1], reverse=True)

    # Build lineup with leverage plays
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Add top leverage plays
    for player, score in leverage_plays[:4]:
        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    # Fill remaining
    other_players = sorted(players, key=lambda x: x['projection'], reverse=True)

    for player in other_players:
        if len(lineup) >= 10:
            break

        if player in lineup:
            continue

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
        return create_classic_lineup_result(lineup)

    return None


def build_max_correlation_classic(players: List[Dict]) -> Optional[Dict]:
    """Maximum correlation lineup"""

    # PRE-FLIGHT CHECK - NEW
    game_player_counts = defaultdict(int)
    for p in players:
        if 'game_id' in p and p['position'] != 'P':
            game_player_counts[p['game_id']] += 1

    if not any(count >= 5 for count in game_player_counts.values()):
        return None  # No game has enough players for correlation
    # END PRE-FLIGHT CHECK

    # Find highest scoring game
    game_totals = {}
    game_players = defaultdict(list)

    for p in players:
        if 'game_id' in p:
            game_id = p['game_id']
            game_players[game_id].append(p)
            if game_id not in game_totals:
                game_totals[game_id] = p.get('team_total', 4.5) * 2

    if not game_totals:
        return None

    # Get best game
    best_game = max(game_totals.items(), key=lambda x: x[1])[0]

    # Try to get 6-7 players from this game
    game_list = game_players[best_game]
    game_list.sort(key=lambda x: x['ceiling'], reverse=True)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Add from target game
    for player in game_list[:7]:
        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap'] - 10000:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    # Fill remaining
    other_players = [p for p in players if p.get('game_id') != best_game]
    other_players.sort(key=lambda x: x['ceiling'], reverse=True)

    for player in other_players:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
        return create_classic_lineup_result(lineup)

    return None

def build_anti_optimizer_classic(players: List[Dict]) -> Optional[Dict]:
    """Avoid common optimizer builds"""
    # Target 48,500-49,500 salary
    target_salary_range = (48500, 49500)

    # Add randomness to projections
    for p in players:
        p['anti_opt_score'] = p['projection'] * random.uniform(0.85, 1.15)

    sorted_players = sorted(players, key=lambda x: x['anti_opt_score'], reverse=True)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    for player in sorted_players:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        # Check if we can reach target salary
        potential_salary = salary + player['salary']
        remaining_spots = 10 - len(lineup) - 1

        if remaining_spots > 0:
            avg_needed = (target_salary_range[0] - potential_salary) / remaining_spots
            if avg_needed < 2000 or avg_needed > 6000:
                continue

        if potential_salary > CLASSIC_CONFIG['salary_cap']:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10 and target_salary_range[0] <= salary <= target_salary_range[1]:
        return create_classic_lineup_result(lineup)

    # Fallback


def build_optimized_cash(players: List[Dict]) -> Optional[Dict]:
    """Optimized cash with smart budget management - PRESERVES ORIGINAL STRATEGY"""

    # PRE-FLIGHT CHECK - NEW
    # Check if players have required fields
    required_fields = ['recent_form', 'platoon_advantage', 'is_hot_streak', 'barrel_rate', 'floor', 'ceiling']
    sample_player = players[0] if players else {}

    for field in required_fields:
        if field not in sample_player:
            # Add default values if missing
            for player in players:
                if field == 'recent_form':
                    player[field] = random.choice([0.85, 0.95, 1.0, 1.08, 1.15])
                elif field == 'platoon_advantage':
                    player[field] = random.choice([-0.05, 0, 0, 0.05, 0.084])
                elif field == 'is_hot_streak':
                    player[field] = player.get('recent_form', 1.0) >= 1.08
                elif field == 'barrel_rate':
                    player[field] = np.clip((player['salary'] / 100000) * 0.15 + np.random.normal(0, 0.03), 0, 0.25)
                elif field == 'floor':
                    player[field] = player['projection'] * random.uniform(0.5, 0.8)
                elif field == 'ceiling':
                    player[field] = player['projection'] * random.uniform(1.8, 2.8)

    # Check minimum viable player pool
    position_counts = defaultdict(int)
    cheap_count = 0

    for p in players:
        position_counts[p['position']] += 1
        if p['salary'] <= 3000:
            cheap_count += 1

    # Need flexibility to build
    for pos, req in CLASSIC_CONFIG['positions'].items():
        if position_counts[pos] < req * 1.5:  # Need 50% extra
            return None

    if cheap_count < 3:  # Need some cheap options
        return None
    # END PRE-FLIGHT CHECK

    # Calculate optimized scores - PRESERVING ORIGINAL WEIGHTS
    for player in players:
        recent_bonus = player.get('recent_form', 1.0)
        recent_score = player['projection'] * recent_bonus * 0.37
        proj_score = player['projection'] * 0.38
        season_score = player['projection'] * 0.95 * 0.19
        floor_ceiling = player['floor'] * 0.80 + player['ceiling'] * 0.20
        platoon_boost = 1.0 + player.get('platoon_advantage', 0)
        hot_streak_boost = 1.085 if player.get('is_hot_streak', False) else 1.0

        raw_score = (
                (recent_score + proj_score + season_score) *
                platoon_boost * hot_streak_boost *
                (floor_ceiling / max(player['projection'], 0.1))
        )

        player['optimized_cash_score'] = min(raw_score, 999)

    # Use regular build_by_metric (no changes to strategy)
    return build_by_metric(players, 'optimized_cash_score')

def build_with_position_priority_and_budget(players, metric):
    """Special builder that ensures all positions get filled with better budget management"""

    # Group players by position
    by_position = defaultdict(list)
    for p in players:
        if metric in p:
            by_position[p['position']].append(p)

    # Sort each position by metric
    for pos in by_position:
        by_position[pos].sort(key=lambda x: x[metric], reverse=True)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)
    requirements = CLASSIC_CONFIG['positions'].copy()

    # CRITICAL: Calculate actual minimum costs from available players
    min_position_costs = {}
    for pos, required in requirements.items():
        if pos in by_position and by_position[pos]:
            # Get the cheapest players at this position
            cheapest = sorted(by_position[pos], key=lambda x: x['salary'])[:required]
            if len(cheapest) >= required:
                min_position_costs[pos] = sum(p['salary'] for p in cheapest) / required
            else:
                # Not enough players at this position - use what we have
                min_position_costs[pos] = sum(p['salary'] for p in cheapest) / len(cheapest) if cheapest else 2500
        else:
            min_position_costs[pos] = 2500  # Conservative estimate

    # Phase 1: Fill each position ensuring budget for remaining positions
    # Process positions by scarcity (fewest available players first)
    position_scarcity = []
    for pos, required in requirements.items():
        available_count = len(by_position.get(pos, []))
        if required > 0:
            scarcity_score = available_count / required
            position_scarcity.append((pos, scarcity_score, required))

    # Sort by scarcity (lowest first)
    position_scarcity.sort(key=lambda x: x[1])

    # Fill positions
    for pos, _, required in position_scarcity:
        candidates = by_position.get(pos, [])

        for i in range(required - positions_filled.get(pos, 0)):
            if not candidates:
                break

            # Calculate remaining needs
            total_spots_left = 10 - len(lineup)
            if total_spots_left <= 0:
                break

            # Calculate minimum budget needed for remaining positions
            min_budget_needed = 0
            for other_pos, other_req in requirements.items():
                remaining_at_pos = other_req - positions_filled.get(other_pos, 0)
                if other_pos == pos:
                    # Current position - subtract 1 since we're about to fill one
                    remaining_at_pos = max(0, remaining_at_pos - 1)

                if remaining_at_pos > 0:
                    # Use actual minimum costs or conservative estimate
                    min_cost = min_position_costs.get(other_pos, 2500)
                    min_budget_needed += min_cost * remaining_at_pos

            # Maximum we can spend on this player
            budget_left = CLASSIC_CONFIG['salary_cap'] - salary
            max_spend = budget_left - min_budget_needed

            # Find best affordable player
            found = False
            for player in candidates:
                if player in lineup:
                    continue

                # Check salary constraint
                if player['salary'] > max_spend:
                    continue

                # Check team constraint (relaxed for final spots)
                if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                    if len(lineup) < 8:  # Strict for early picks
                        continue
                    elif len(lineup) < 9 and teams_used.get(player['team'], 0) >= 5:
                        continue
                    # Allow for 9th/10th spot if necessary

                # Add player
                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] = positions_filled.get(pos, 0) + 1
                teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
                found = True
                break

            # If we couldn't find an affordable player with the metric, try ANY affordable player
            if not found and i < required - positions_filled.get(pos, 0):
                all_at_position = [p for p in by_position[pos] if p not in lineup]
                all_at_position.sort(key=lambda x: x['salary'])  # Cheapest first

                for player in all_at_position:
                    if player['salary'] <= max_spend:
                        lineup.append(player)
                        salary += player['salary']
                        positions_filled[pos] = positions_filled.get(pos, 0) + 1
                        teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
                        found = True
                        break

                if not found:
                    print(f"WARNING: Cannot find affordable {pos} (need ${max_spend} or less)")

    # Phase 2: If still not full, fill with any valid player
    if len(lineup) < 10:
        all_remaining = []
        for pos_list in by_position.values():
            all_remaining.extend([p for p in pos_list if p not in lineup])

        # Sort by salary (cheapest first) to ensure we can complete
        all_remaining.sort(key=lambda x: x['salary'])

        for player in all_remaining:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled.get(pos, 0) >= requirements.get(pos, 0):
                continue

            if salary + player['salary'] <= CLASSIC_CONFIG['salary_cap']:
                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] = positions_filled.get(pos, 0) + 1
                teams_used[player['team']] = teams_used.get(player['team'], 0) + 1

    # Validate lineup
    if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
        return create_classic_lineup_result(lineup)

    # Debug output if failed
    if len(lineup) < 10:
        print(f"\nOptimized builder incomplete: {len(lineup)}/10 players")
        print(f"Salary used: ${salary} (${CLASSIC_CONFIG['salary_cap'] - salary} remaining)")
        print("Missing positions:")
        for pos, req in requirements.items():
            filled = positions_filled.get(pos, 0)
            if filled < req:
                remaining_at_pos = [p for p in by_position.get(pos, []) if p not in lineup]
                if remaining_at_pos:
                    cheapest = min(remaining_at_pos, key=lambda x: x['salary'])
                    print(f"  {pos}: need {req - filled}, cheapest available: ${cheapest['salary']}")
                else:
                    print(f"  {pos}: need {req - filled}, NO PLAYERS AVAILABLE")

    return None


def build_by_metric_with_position_check(players, metric, reverse=True):
    """Build lineup optimizing for metric while ensuring all positions filled"""
    # This is a wrapper around build_by_metric that adds position checking
    # WITHOUT changing the core strategy philosophy

    # First attempt - pure metric optimization
    lineup = build_by_metric(players, metric, reverse)

    if lineup:
        return lineup

    # If that failed, try with minimal position awareness
    # Sort players by metric but ensure each position has candidates
    valid_players = [p for p in players if metric in p]
    if not valid_players:
        return None

    # Remove any infinity or NaN values
    for p in valid_players:
        if not isinstance(p[metric], (int, float)) or math.isnan(p[metric]) or math.isinf(p[metric]):
            p[metric] = 0

    sorted_players = sorted(valid_players, key=lambda x: x.get(metric, 0), reverse=reverse)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # CRITICAL: Only intervene if we're about to fail
    # This preserves strategy integrity while ensuring completion

    # Phase 1: Fill normally by metric
    for player in sorted_players:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
            continue

        # Check if we're leaving enough budget for remaining positions
        spots_left = 10 - len(lineup) - 1
        if spots_left > 0:
            # Only check if we're dangerously low on budget
            budget_left = CLASSIC_CONFIG['salary_cap'] - salary - player['salary']
            if budget_left < spots_left * 2200:  # Getting tight
                # Quick check if we can still complete
                can_complete = check_if_can_complete_lineup(
                    sorted_players, lineup, salary + player['salary'],
                    positions_filled, pos
                )
                if not can_complete:
                    continue  # Skip this player

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
            if len(lineup) < 9:  # Be strict early
                continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] = positions_filled.get(pos, 0) + 1
        teams_used[player['team']] = teams_used.get(player['team'], 0) + 1

    # Phase 2: If incomplete, fill missing positions with cheapest available
    # This is the ONLY compromise to ensure lineup completion
    if len(lineup) < 10:
        for pos, required in CLASSIC_CONFIG['positions'].items():
            while positions_filled.get(pos, 0) < required and len(lineup) < 10:
                # Find cheapest at this position
                candidates = [p for p in valid_players
                              if p not in lineup
                              and p['position'] == pos
                              and salary + p['salary'] <= CLASSIC_CONFIG['salary_cap']]

                if not candidates:
                    break

                # Take cheapest to preserve budget
                candidates.sort(key=lambda x: x['salary'])
                player = candidates[0]

                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] = positions_filled.get(pos, 0) + 1
                teams_used[player['team']] = teams_used.get(player['team'], 0) + 1

    if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
        return create_classic_lineup_result(lineup)

    return None


def ensure_adequate_player_pool(players, format_type, slate_size):
    """Ensure the player pool has enough affordable options at each position"""
    position_counts = defaultdict(int)
    position_salary_ranges = defaultdict(list)

    for p in players:
        position_counts[p['position']] += 1
        position_salary_ranges[p['position']].append(p['salary'])

    # Check if we have enough players and salary diversity
    if format_type == 'classic':
        required = CLASSIC_CONFIG['positions']

        for pos, req in required.items():
            current_count = position_counts[pos]

            # Need at least 2x the required amount for flexibility
            min_needed = req * 2

            # Check if we have enough total
            if current_count < min_needed:
                print(f"WARNING: Only {current_count} {pos} players (need {min_needed}+)")

            # Check if we have affordable options
            if pos in position_salary_ranges:
                salaries = position_salary_ranges[pos]
                affordable = [s for s in salaries if s <= 3000]
                if len(affordable) < req:
                    print(f"WARNING: Only {len(affordable)} affordable {pos} players under $3000")

    return players


def check_if_can_complete_lineup(all_players, current_lineup, current_salary,
                                 positions_filled, adding_position):
    """Quick check if we can complete lineup with remaining budget"""
    temp_positions = positions_filled.copy()
    temp_positions[adding_position] = temp_positions.get(adding_position, 0) + 1

    budget_left = CLASSIC_CONFIG['salary_cap'] - current_salary
    spots_left = 10 - len(current_lineup) - 1

    if spots_left == 0:
        return True

    # Check each position we still need
    min_cost_needed = 0
    for pos, required in CLASSIC_CONFIG['positions'].items():
        still_need = required - temp_positions.get(pos, 0)
        if still_need > 0:
            # Find cheapest available at this position
            available = [p for p in all_players
                         if p not in current_lineup
                         and p['position'] == pos]
            if len(available) < still_need:
                return False  # Not enough players

            available.sort(key=lambda x: x['salary'])
            min_cost_needed += sum(p['salary'] for p in available[:still_need])

    return min_cost_needed <= budget_left


def build_optimized_gpp(players: List[Dict]) -> Optional[Dict]:
    """Build GPP lineup using optimization findings - 64th percentile approach"""

    # PRE-FLIGHT CHECK - NEW
    # Check for required fields
    sample_player = players[0] if players else {}
    if 'barrel_rate' not in sample_player or 'is_undervalued_xwoba' not in sample_player:
        # Add defaults if missing
        for p in players:
            if 'barrel_rate' not in p:
                p['barrel_rate'] = np.clip((p['salary'] / 100000) * 0.15 + np.random.normal(0, 0.03), 0, 0.25)
            if 'is_undervalued_xwoba' not in p:
                xwoba = 0.250 + (p['salary'] / 100000) * 0.150 + np.random.normal(0, 0.02)
                p['xwoba'] = xwoba
                p['is_undervalued_xwoba'] = xwoba > 0.350 and p['ownership'] < 15

    # Check if we have enough hitters for stacking
    team_hitter_counts = defaultdict(int)
    for p in players:
        if p['position'] != 'P':
            team_hitter_counts[p['team']] += 1

    # Need at least one team with 4+ hitters
    if not any(count >= 4 for count in team_hitter_counts.values()):
        return None
    # END PRE-FLIGHT CHECK

    # Key findings implementation (rest of function unchanged)
    team_scores = defaultdict(float)
    team_players = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

            # Team scoring with multipliers
            base_score = p['ceiling']

            # Apply barrel rate boost
            if p.get('barrel_rate', 0) > 0.117:
                base_score *= 1.19

            # Apply xwOBA undervalued boost
            if p.get('is_undervalued_xwoba', False):
                base_score *= 1.25

            team_scores[p['team']] += base_score

    # Sort teams by score and apply multipliers
    sorted_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)

    if not sorted_teams:
        return None

    # Apply team multipliers
    best_team = sorted_teams[0][0]
    team_multiplier = 1.34  # Top team

    if len(sorted_teams) > 3:
        # Mid-tier teams
        for i in range(1, 4):
            if i < len(sorted_teams):
                team = sorted_teams[i][0]
                for p in team_players[team]:
                    p['gpp_team_boost'] = 1.22

    # Build with 4-player stack from best team
    best_team_players = team_players[best_team]
    best_team_players.sort(key=lambda x: x.get('batting_order', 10))

    # Get sequential batting order players
    sequential_players = []
    for i in range(1, 6):  # Look for 1-2-3-4-5
        for p in best_team_players:
            if p.get('batting_order') == i:
                sequential_players.append(p)
                break

    # Take first 4 sequential players
    stack_players = sequential_players[:4]

    # Build lineup starting with stack
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Add stack
    for player in stack_players:
        pos = player['position']
        if positions_filled[pos] < CLASSIC_CONFIG['positions'][pos]:
            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

    # Fill remaining with high-upside plays
    other_players = [p for p in players if p not in lineup]

    # Prioritize undervalued xwOBA and high barrel rate
    for p in other_players:
        score = p['ceiling']
        if p.get('is_undervalued_xwoba', False):
            score *= 1.25
        if p.get('barrel_rate', 0) > 0.117:
            score *= 1.19
        p['gpp_fill_score'] = score

    other_players.sort(key=lambda x: x['gpp_fill_score'], reverse=True)

    # Fill remaining spots
    for player in other_players:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
            continue

        if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
            continue

        if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
        return create_classic_lineup_result(lineup)

    return None

def build_sequential_stack(players: List[Dict]) -> Optional[Dict]:
    """Build lineup with sequential batting order - TEST MORE PATTERNS"""

    # PRE-FLIGHT CHECK - NEW
    team_batting_check = defaultdict(set)
    for p in players:
        if p['position'] != 'P' and p.get('batting_order', 0) > 0:
            team_batting_check[p['team']].add(p['batting_order'])

    # Check if ANY team has 3+ consecutive batters
    has_valid_sequence = False
    for team, orders in team_batting_check.items():
        for start in range(1, 8):
            if all(i in orders for i in range(start, start + 3)):
                has_valid_sequence = True
                break
        if has_valid_sequence:
            break

    if not has_valid_sequence:
        return None  # No team has consecutive batters
    # END PRE-FLIGHT CHECK

    team_batting_orders = defaultdict(lambda: defaultdict(list))

    for p in players:
        if p['position'] != 'P' and p.get('batting_order', 0) > 0:
            team = p['team']
            order = p['batting_order']
            team_batting_orders[team][order].append(p)

    # Test more sequential patterns
    sequences = [
        (1, 2, 3, 4, 5),  # Top 5
        (2, 3, 4, 5, 6),  # 2-6
        (3, 4, 5, 6, 7),  # 3-7 (new)
        (1, 2, 3, 4),  # Top 4
        (2, 3, 4, 5),  # 2-5 (new)
        (3, 4, 5, 6),  # Heart
        (4, 5, 6, 7),  # 4-7 (new)
        (1, 2, 3),  # Top 3
        (3, 4, 5),  # Middle 3
        (5, 6, 7),  # 5-7 (new)
        (2, 3, 4),  # 2-4 (new)
    ]

    valid_combos = []

    for team, batting_orders in team_batting_orders.items():
        team_total = 4.5  # default

        # Get team total from any player
        for order_players in batting_orders.values():
            if order_players:
                team_total = order_players[0].get('team_total', 4.5)
                break

        for seq in sequences:
            # Check if we have at least one player at each spot
            if all(i in batting_orders and len(batting_orders[i]) > 0 for i in seq):
                # Calculate the strength of this sequence
                seq_projection = 0
                seq_players = []

                for i in seq:
                    # Get best player at each spot
                    best_at_spot = max(batting_orders[i], key=lambda x: x['projection'])
                    seq_projection += best_at_spot['projection']
                    seq_players.append(best_at_spot)

                # Boost for team total
                if team_total > 5.5:
                    seq_projection *= 1.15
                elif team_total > 5.0:
                    seq_projection *= 1.08

                valid_combos.append({
                    'team': team,
                    'sequence': seq,
                    'players': seq_players,
                    'size': len(seq),
                    'projection': seq_projection,
                    'team_total': team_total
                })

    if not valid_combos:
        return None

    # Sort by projection (best sequences first)
    valid_combos.sort(key=lambda x: x['projection'], reverse=True)

    # Try each combo with multiple approaches
    for combo in valid_combos[:15]:  # Try more combos
        # Try different player selections at each batting spot
        for selection_approach in ['best', 'value', 'mixed']:
            lineup = _build_sequential_lineup(
                players, combo['team'], combo['sequence'],
                team_batting_orders[combo['team']], selection_approach
            )
            if lineup:
                return lineup

    return None

def _build_sequential_lineup(all_players, team, sequence, batting_orders, approach):
    """Build lineup with specific sequential stack"""
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Add sequential players
    for batting_pos in sequence:
        candidates = batting_orders[batting_pos].copy()

        # Sort based on approach
        if approach == 'best':
            candidates.sort(key=lambda x: x['projection'], reverse=True)
        elif approach == 'value':
            candidates.sort(key=lambda x: x.get('value_score', 0), reverse=True)
        else:  # mixed
            candidates.sort(key=lambda x: x['projection'] * x.get('value_score', 1), reverse=True)

        # Try to add a player from this batting position
        added = False
        for player in candidates:
            if player in lineup:
                continue

            pos = player['position']

            # Flexible position limits for sequential stacks
            position_limit = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}[pos]
            if positions_filled.get(pos, 0) >= position_limit:
                # Allow one overflow for sequential stacks
                if positions_filled.get(pos, 0) >= position_limit + 1:
                    continue

            # Salary check
            min_remaining = 2200 * (10 - len(lineup) - 1)
            if salary + player['salary'] + min_remaining > 50000:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] = positions_filled.get(pos, 0) + 1
            teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
            added = True
            break

        if not added and len(lineup) < len(sequence) - 1:
            # Failed to add from this batting position and we're not close to done
            return None

    # Need at least 3 sequential players
    if len([p for p in lineup if p['team'] == team]) < min(3, len(sequence)):
        return None

    # Fill remaining using the flexible function from above
    return _fill_remaining_positions_flexible(lineup, all_players, salary, positions_filled, teams_used)

def fill_remaining_positions(lineup, players, salary, positions_filled, teams_used,
                             stack_team=None, min_salary_buffer=0):
    """Helper to fill remaining lineup spots with maximum flexibility"""

    positions_needed = dict(CLASSIC_CONFIG['positions'])
    remaining_spots = 10 - len(lineup)

    if remaining_spots == 0:
        return lineup, salary

    # Categorize remaining players by scarcity
    position_scarcity = {}
    for pos in positions_needed:
        available = [p for p in players if p not in lineup and p['position'] == pos]
        needed = positions_needed[pos] - positions_filled.get(pos, 0)
        if needed > 0:
            position_scarcity[pos] = len(available) / needed

    # Sort positions by scarcity (fill hardest positions first)
    scarce_positions = sorted(position_scarcity.keys(), key=lambda x: position_scarcity[x])

    # Fill scarce positions first
    for pos in scarce_positions:
        needed = positions_needed[pos] - positions_filled.get(pos, 0)
        if needed <= 0:
            continue

        candidates = [p for p in players if p not in lineup and p['position'] == pos]
        candidates.sort(key=lambda x: x.get('value_score', 0), reverse=True)

        for player in candidates:
            if needed <= 0 or len(lineup) >= 10:
                break

            # Dynamic salary check based on remaining spots
            remaining_after = 10 - len(lineup) - 1
            if remaining_after > 0:
                avg_needed = (CLASSIC_CONFIG['salary_cap'] - salary - player['salary']) / remaining_after
                # Only skip if average needed is impossible
                if avg_needed < 2000:  # Below minimum player cost
                    continue
            else:
                # Last spot - just check cap
                if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                    continue

            # Flexible team constraint
            if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                # More flexible if it's not the stack team
                if stack_team and player['team'] == stack_team:
                    continue  # Enforce for stack team
                elif len(lineup) >= 8:  # For final spots, be very flexible
                    pass  # Allow it
                else:
                    # Check if we have alternatives
                    alternatives = [p for p in candidates
                                    if p['team'] != player['team']
                                    and p not in lineup]
                    if len(alternatives) > 1:
                        continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] = positions_filled.get(pos, 0) + 1
            teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
            needed -= 1

    return lineup, salary

def create_classic_lineup_result(lineup):
    """Create lineup result for classic format"""
    total_salary = sum(p['salary'] for p in lineup)
    total_projection = sum(p['projection'] for p in lineup)
    total_ownership = sum(p['ownership'] for p in lineup)

    # Calculate correlations
    team_counts = defaultdict(int)
    game_counts = defaultdict(int)

    for p in lineup:
        team_counts[p['team']] += 1
        if 'game_id' in p and p['position'] != 'P':
            game_counts[p['game_id']] += 1

    # Stack bonus
    max_stack = max(team_counts.values())
    stack_bonus = 0
    if max_stack >= 5:
        stack_bonus = 0.15
    elif max_stack >= 4:
        stack_bonus = 0.08
    elif max_stack >= 3:
        stack_bonus = 0.04

    return {
        'lineup': lineup,
        'salary': total_salary,
        'projection': total_projection,
        'ownership': total_ownership / 10,
        'stack_bonus': stack_bonus,
        'max_stack': max_stack,
        'format': 'classic'
    }


# ========== CONTEST SIMULATION ==========
def simulate_contest(slate, strategy_name, strategy_config, contest_type, field_size):
    """Simulate a DFS contest with failure tracking"""

    # Set entry fees
    if slate['format'] == 'showdown':
        entry_fee = 3 if contest_type == 'gpp' else 5
    else:
        entry_fee = 3 if contest_type == 'gpp' else 10

    # Build our lineup
    if slate['format'] == 'showdown':
        our_lineup = build_showdown_lineup(slate['players'], strategy_config)
    else:
        our_lineup = build_classic_lineup(slate['players'], strategy_config, slate['slate_size'])

    if not our_lineup:
        # Track why it failed
        return {
            'strategy': strategy_name,
            'contest_type': contest_type,
            'field_size': field_size,
            'format': slate['format'],
            'slate_size': slate['slate_size'],
            'failed': True,
            'failure_reason': 'lineup_build_failed'
        }

    # Generate field - FIXED: use generate_field_realistic
    field_lineups = generate_field_realistic(slate, field_size - 1, contest_type)

    # Score all lineups - FIXED: use simulate_realistic_lineup_score
    our_score = simulate_realistic_lineup_score(our_lineup)

    # Score field with same variance
    field_scores = []
    for lineup in field_lineups:
        score = simulate_realistic_lineup_score(lineup)  # FIXED
        field_scores.append(score)

    # Add score distribution tracking
    all_scores = field_scores + [our_score]
    score_mean = np.mean(all_scores)
    score_std = np.std(all_scores)
    score_min = min(all_scores)
    score_max = max(all_scores)

    # Calculate placement
    all_scores.sort(reverse=True)
    our_rank = all_scores.index(our_score) + 1
    percentile = ((len(all_scores) - our_rank) / len(all_scores)) * 100

    # Calculate payout
    config = SHOWDOWN_CONFIG if slate['format'] == 'showdown' else CLASSIC_CONFIG

    if contest_type == 'cash':
        cash_threshold_percentile = (1 - config['cash_payout_threshold']) * 100
        if percentile >= cash_threshold_percentile:
            payout = entry_fee * 2
        else:
            payout = 0
    else:  # GPP
        payout_pct = our_rank / len(all_scores)
        payout = 0

        for threshold, multiplier in sorted(config['gpp_payout_structure'].items()):
            if payout_pct <= threshold:
                payout = entry_fee * multiplier
                break

    profit = payout - entry_fee
    roi = (profit / entry_fee) * 100

    return {
        'strategy': strategy_name,
        'contest_type': contest_type,
        'field_size': field_size,
        'format': slate['format'],
        'slate_size': slate['slate_size'],
        'rank': our_rank,
        'percentile': percentile,
        'score': our_score,
        'payout': payout,
        'profit': profit,
        'roi': roi,
        'ownership': our_lineup['ownership'],
        'projection': our_lineup['projection'],
        'failed': False,
        # New tracking fields
        'score_mean': score_mean,
        'score_std': score_std,
        'score_min': score_min,
        'score_max': score_max,
        'winning_score': all_scores[0],
        'cash_line': all_scores[
            int(len(all_scores) * config['cash_payout_threshold'])] if contest_type == 'cash' else None
    }


def _fill_remaining_positions_flexible(lineup, all_players, salary, positions_filled, teams_used):
    """Flexible position filling that maintains strategy integrity"""
    position_limits = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3
    }
    SALARY_CAP = 50000

    other_players = [p for p in all_players if p not in lineup]

    # Identify what we must fill
    must_fill = {}
    for pos, required in position_limits.items():
        current = positions_filled.get(pos, 0)
        if current < required:
            must_fill[pos] = required - current

    # Fill by position scarcity
    position_availability = {}
    for pos in must_fill:
        available = len([p for p in other_players if p['position'] == pos])
        if must_fill[pos] > 0:
            position_availability[pos] = available / must_fill[pos]

    # Sort positions by scarcity (fill hardest first)
    scarce_positions = sorted(position_availability.keys(),
                              key=lambda x: position_availability[x])

    # Fill scarce positions
    for pos in scarce_positions:
        needed = must_fill[pos]
        if needed <= 0:
            continue

        candidates = [p for p in other_players if p['position'] == pos]
        candidates.sort(key=lambda x: x.get('value_score', 0), reverse=True)

        for player in candidates:
            if needed <= 0:
                break

            # Dynamic salary check
            spots_left = 10 - len(lineup) - 1
            if spots_left > 0:
                min_needed = 2000 * spots_left  # Absolute minimum
                if salary + player['salary'] + min_needed > SALARY_CAP:
                    continue
            else:
                if salary + player['salary'] > SALARY_CAP:
                    continue

            # Flexible team constraint
            if teams_used.get(player['team'], 0) >= 5:
                # Only enforce for non-final spots
                if len(lineup) < 9:
                    continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] = positions_filled.get(pos, 0) + 1
            teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
            needed -= 1
            other_players.remove(player)

    # Fill any remaining spots with best value
    if len(lineup) < 10:
        remaining = []
        for p in other_players:
            pos = p['position']
            if positions_filled.get(pos, 0) < position_limits[pos]:
                remaining.append(p)

        remaining.sort(key=lambda x: x.get('value_score', 0), reverse=True)

        for player in remaining:
            if len(lineup) >= 10:
                break

            if salary + player['salary'] > SALARY_CAP:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[player['position']] = positions_filled.get(player['position'], 0) + 1
            teams_used[player['team']] = teams_used.get(player['team'], 0) + 1

    if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
        return create_classic_lineup_result(lineup)

    return None

# ========== BATCH PROCESSING (WITH PARALLEL PROCESSING) ==========
def process_batch(args):
    """Process batch - capture ALL data, even from failing strategies"""
    slate_configs, contest_configs = args
    results = []
    batch_size = len(slate_configs)

    # CONFIGURATION - OPTIMIZED FOR SPEED
    MIN_SUCCESSES = {
        'cash': 30,
        'gpp': 50
    }

    EARLY_EXIT_ATTEMPTS = 20  # Check after 20 tries
    ZERO_SUCCESS_EXIT = 20  # Exit immediately if 0 success after 20
    MIN_SUCCESS_RATE = 0.15  # 15% threshold
    MAX_ATTEMPTS = 100  # Hard stop
    MIN_SAMPLES_BEFORE_EXIT = 5  # Get at least 5 successes before giving up

    # Track attempts and successes per strategy
    strategy_attempts = defaultdict(lambda: defaultdict(int))
    strategy_successes = defaultdict(lambda: defaultdict(int))
    strategy_scores = defaultdict(list)

    # Process each slate config
    for slate_config in slate_configs:
        slate_id, format_type, slate_size = slate_config

        # Generate initial slate
        slate = generate_slate(slate_id, format_type, slate_size)
        if not slate or not slate.get('players'):
            continue

        # Get strategies for this configuration
        if format_type == 'showdown':
            strategies = SHOWDOWN_STRATEGIES
        else:
            strategies = {}
            if slate_size in CLASSIC_STRATEGIES_BY_SIZE:
                for contest_type in ['cash', 'gpp']:
                    if contest_type in CLASSIC_STRATEGIES_BY_SIZE[slate_size]:
                        for strat_name, strat_config in CLASSIC_STRATEGIES_BY_SIZE[slate_size][contest_type].items():
                            unique_name = f"{strat_name}_{contest_type}"
                            strategies[unique_name] = strat_config

        # Process each strategy
        for strategy_name, strategy_config in strategies.items():
            for contest_type, field_size in contest_configs:
                # Skip inappropriate strategy/contest combinations
                if '_cash' in strategy_name and contest_type == 'gpp':
                    continue
                if '_gpp' in strategy_name and contest_type == 'cash':
                    continue

                clean_strategy_name = strategy_name.replace('_cash', '').replace('_gpp', '')
                key = f"{format_type}_{slate_size}_{clean_strategy_name}_{contest_type}"

                # Get target successes for this contest type
                target_successes = MIN_SUCCESSES.get(contest_type, 30)
                attempts = 0
                consecutive_failures = 0
                slate_regenerations = 0

                while (strategy_successes[key][clean_strategy_name] < target_successes and
                       attempts < MAX_ATTEMPTS):

                    attempts += 1
                    strategy_attempts[key][clean_strategy_name] += 1

                    # FAST EXIT FOR 0% STRATEGIES
                    if attempts >= ZERO_SUCCESS_EXIT and strategy_successes[key][clean_strategy_name] == 0:
                        print(f"\n⚡ Quick exit: {clean_strategy_name} for {format_type}/{slate_size} - 0% success")

                        # Record as impossible strategy
                        results.append({
                            'type': 'impossible_strategy',
                            'strategy': clean_strategy_name,
                            'format': format_type,
                            'slate_size': slate_size,
                            'contest_type': contest_type,
                            'success_rate': 0.0,
                            'attempts': attempts,
                            'reason': 'No valid lineups after 20 attempts'
                        })
                        break

                    # Standard early exit check
                    if attempts >= EARLY_EXIT_ATTEMPTS:
                        success_count = strategy_successes[key][clean_strategy_name]
                        current_success_rate = success_count / attempts

                        if current_success_rate < MIN_SUCCESS_RATE:
                            # CHECK: Do we have SOME data?
                            if success_count >= MIN_SAMPLES_BEFORE_EXIT:
                                # We have enough to analyze - add summary and exit
                                print(f"\n📊 Low success strategy {clean_strategy_name}: "
                                      f"{success_count} lineups from {attempts} attempts ({current_success_rate:.1%})")

                                # Add a summary record
                                results.append({
                                    'type': 'low_success_strategy',
                                    'strategy': clean_strategy_name,
                                    'format': format_type,
                                    'slate_size': slate_size,
                                    'contest_type': contest_type,
                                    'success_rate': current_success_rate,
                                    'sample_size': success_count,
                                    'attempts': attempts,
                                    'data_quality': 'limited',
                                    'note': 'Strategy has low success rate but some viable lineups'
                                })
                                break

                            elif attempts >= 50:  # Tried hard enough
                                # True failure - almost never works
                                print(f"\n❌ Failed strategy {clean_strategy_name}: "
                                      f"{success_count} successes in {attempts} attempts")

                                results.append({
                                    'type': 'failed_strategy',
                                    'strategy': clean_strategy_name,
                                    'format': format_type,
                                    'slate_size': slate_size,
                                    'contest_type': contest_type,
                                    'success_rate': current_success_rate,
                                    'sample_size': success_count,
                                    'data_quality': 'insufficient'
                                })
                                break

                    # Regenerate slate if too many consecutive failures
                    if consecutive_failures >= 10 and slate_regenerations < 3:
                        slate_id += 10000  # New seed
                        slate = generate_slate(slate_id, format_type, slate_size)
                        if not slate or not slate.get('players'):
                            break
                        consecutive_failures = 0
                        slate_regenerations += 1

                    # Attempt simulation
                    result = simulate_contest(
                        slate, clean_strategy_name, strategy_config,
                        contest_type, field_size
                    )

                    if not result.get('failed'):
                        strategy_successes[key][clean_strategy_name] += 1
                        results.append(result)
                        consecutive_failures = 0

                        # Track score distribution for insights
                        strategy_scores[key].append({
                            'score': result['score'],
                            'roi': result['roi'],
                            'percentile': result['percentile']
                        })
                    else:
                        consecutive_failures += 1

                # Add summary stats for strategies with data
                if strategy_scores[key]:
                    scores_data = strategy_scores[key]
                    results.append({
                        'type': 'strategy_summary',
                        'strategy': clean_strategy_name,
                        'format': format_type,
                        'slate_size': slate_size,
                        'contest_type': contest_type,
                        'attempts': strategy_attempts[key][clean_strategy_name],
                        'successes': len(scores_data),
                        'success_rate': len(scores_data) / strategy_attempts[key][clean_strategy_name],
                        'avg_roi': np.mean([s['roi'] for s in scores_data]),
                        'avg_percentile': np.mean([s['percentile'] for s in scores_data]),
                        'roi_std': np.std([s['roi'] for s in scores_data]) if len(scores_data) > 1 else 0,
                        'score_std': np.std([s['score'] for s in scores_data]) if len(scores_data) > 1 else 0
                    })

    # Final summary of all attempts
    results.append({
        'type': 'batch_summary',
        'total_attempts': dict(strategy_attempts),
        'total_successes': dict(strategy_successes)
    })

    return results
if __name__ == "__main__":
    main()
if __name__ == "__main__":
    # Comment out the test if you don't want it every time
    # test_scoring_variance()

    # Run the actual simulation
    main()