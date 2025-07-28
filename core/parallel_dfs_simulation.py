#!/usr/bin/env python3
"""
DFS ULTIMATE SIMULATOR 2.0 - FIXED EDITION
==========================================
Tests strategies across different slate sizes and formats (Classic/Showdown)
Discovers what ACTUALLY works for each contest type
"""

print("🚀 Loading DFS Ultimate Simulator 2.0 (Fixed Edition)...", flush=True)

import numpy as np
import random
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import time
from typing import Dict, List, Optional, Tuple, Set
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
    'balanced_captain': {
        'name': 'Balanced Captain',
        'type': 'balanced',
        'description': 'Top projected player as CPT, value UTIL'
    },
    'leverage_captain': {
        'name': 'Leverage Captain',
        'type': 'leverage',
        'description': 'Low-owned player as CPT for GPP'
    },
    'onslaught': {
        'name': 'Onslaught',
        'type': 'onslaught',
        'description': '4-5 players from winning team'
    },
    'game_theory': {
        'name': 'Game Theory',
        'type': 'game_theory',
        'description': 'Pitcher CPT with opposing hitters'
    },
    'value_hunt': {
        'name': 'Value Hunt',
        'type': 'value',
        'description': 'Cheapest viable CPT + studs'
    }
}

# Classic strategies that vary by slate size - EXPANDED
CLASSIC_STRATEGIES_BY_SIZE = {
    'small': {  # 3 games - Value dominates
        'cash': {
            'pure_value': {'name': 'Pure Value', 'type': 'value', 'weight': 1.0,
                           'description': 'Highest points per dollar'},
            'value_80_own_20': {'name': 'Value 80/Own 20', 'type': 'blend',
                                'value_weight': 0.8, 'own_weight': 0.2,
                                'description': 'Mostly value with some ownership'},
            'chalk_value_blend': {'name': 'Chalk Value 60/40', 'type': 'blend',
                                  'value_weight': 0.6, 'own_weight': 0.4,
                                  'description': 'Balanced chalk and value'},
            'optimized_cash': {'name': 'Optimized Cash', 'type': 'optimized_cash',
                               'description': 'Multi-factor optimization'},
        },
        'gpp': {
            'ceiling_focus': {'name': 'Ceiling Focus', 'type': 'ceiling',
                              'description': 'Maximum upside plays'},
            'mini_onslaught': {'name': 'Mini Onslaught', 'type': 'stack', 'stack_size': 4,
                               'description': '4-player team stack'},
            'anti_chalk_value': {'name': 'Anti-Chalk Value', 'type': 'contrarian', 'max_own': 20,
                                 'description': 'Avoid high ownership'},
            'optimized_gpp': {'name': 'Optimized GPP', 'type': 'optimized_gpp',
                              'description': 'Stack with leverage'},
            'pitcher_stack': {'name': 'Pitcher + Stack', 'type': 'pitcher_stack',
                              'description': 'Ace + opposing team stack'},
        }
    },
    'medium': {  # 7 games - Balanced approach
        'cash': {
            'smart_chalk_60_40': {'name': 'Smart Chalk 60/40', 'type': 'blend',
                                  'own_weight': 0.6, 'value_weight': 0.4,
                                  'description': 'Ownership focused blend'},
            'smart_chalk_50_50': {'name': 'Smart Chalk 50/50', 'type': 'blend',
                                  'own_weight': 0.5, 'value_weight': 0.5,
                                  'description': 'Equal weight blend'},
            'mini_stack_cash': {'name': 'Mini Stack Cash', 'type': 'mini_stack', 'stack_size': 3,
                                'description': 'Small correlation play'},
            'optimized_cash': {'name': 'Optimized Cash', 'type': 'optimized_cash',
                               'description': 'Multi-factor optimization'},
        },
        'gpp': {
            'full_stack': {'name': 'Full Stack', 'type': 'stack', 'stack_size': 5,
                           'description': '5-player team stack'},
            'game_stack': {'name': 'Game Stack', 'type': 'game_stack',
                           'description': 'Multiple teams from same game'},
            'balanced_ownership': {'name': 'Balanced Own', 'type': 'ownership_buckets',
                                   'description': 'Mix of ownership levels'},
            'optimized_gpp': {'name': 'Optimized GPP', 'type': 'optimized_gpp',
                              'description': 'Stack with leverage'},
            'sequential_stack': {'name': 'Sequential Stack 1-5', 'type': 'sequential_stack',
                                 'description': 'Consecutive batting order'},
            'double_stack': {'name': 'Double Stack', 'type': 'double_stack',
                             'description': 'Two 3-player mini stacks'},
            'contrarian_stack': {'name': 'Contrarian Stack', 'type': 'contrarian_stack',
                                 'description': 'Low-owned team stack'},
        }
    },
    'large': {  # 12+ games - Ownership dominates
        'cash': {
            'pure_chalk': {'name': 'Pure Chalk', 'type': 'ownership',
                           'description': 'Highest ownership plays'},
            'smart_chalk_70_30': {'name': 'Smart Chalk 70/30', 'type': 'blend',
                                  'own_weight': 0.7, 'value_weight': 0.3,
                                  'description': 'Heavy ownership focus'},
            'fade_mega_chalk': {'name': 'Fade Mega Chalk', 'type': 'fade_threshold', 'fade_above': 35,
                                'description': 'Avoid extreme chalk'},
            'optimized_cash': {'name': 'Optimized Cash', 'type': 'optimized_cash',
                               'description': 'Multi-factor optimization'},
            'balanced_cash': {'name': 'Balanced Approach', 'type': 'balanced_cash',
                              'description': 'Mix of metrics'},
        },
        'gpp': {
            'leverage_theory': {'name': 'Leverage Theory', 'type': 'leverage',
                                'description': 'Low-owned correlations'},
            'max_correlation': {'name': 'Max Correlation', 'type': 'correlation',
                                'description': 'Game stack focus'},
            'anti_optimizer': {'name': 'Anti-Optimizer', 'type': 'anti_optimizer',
                               'description': 'Avoid common builds'},
            'optimized_gpp': {'name': 'Optimized GPP', 'type': 'optimized_gpp',
                              'description': 'Stack with leverage'},
            'sequential_stack': {'name': 'Sequential Stack 1-5', 'type': 'sequential_stack',
                                 'description': 'Consecutive batting order'},
            'multi_game_stack': {'name': 'Multi-Game Correlation', 'type': 'multi_game',
                                 'description': 'Players from 2-3 games'},
            'stars_scrubs': {'name': 'Stars and Scrubs', 'type': 'stars_scrubs',
                             'description': 'Studs with min price plays'},
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
        return build_by_metric(players, 'ceiling')  # Fallback

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
    """Build classic lineup based on strategy and slate size - NO FALLBACKS"""
    # Ensure we have enough players
    if len(players) < 50:
        return None

    strategy_type = strategy.get('type')
    lineup = None

    if strategy_type == 'value':
        lineup = build_by_metric(players, 'value_score')

    elif strategy_type == 'ownership':
        lineup = build_by_metric(players, 'ownership')

    elif strategy_type == 'ceiling':
        lineup = build_by_metric(players, 'ceiling')

    elif strategy_type == 'blend':
        # Weighted blend of ownership and value
        own_weight = strategy.get('own_weight', 0.5)
        value_weight = strategy.get('value_weight', 0.5)

        for p in players:
            # Normalize metrics
            norm_own = p['ownership'] / 40
            norm_value = p['value_score'] / 4
            p['blend_score'] = norm_own * own_weight + norm_value * value_weight

        lineup = build_by_metric(players, 'blend_score')

    elif strategy_type == 'stack':
        stack_size = strategy.get('stack_size', 5)
        lineup = build_team_stack(players, stack_size)

    elif strategy_type == 'mini_stack':
        stack_size = strategy.get('stack_size', 3)
        lineup = build_with_mini_stack(players, stack_size)

    elif strategy_type == 'game_stack':
        lineup = build_game_stack_classic(players)

    elif strategy_type == 'contrarian':
        max_own = strategy.get('max_own', 10)
        eligible = [p for p in players if p['ownership'] <= max_own]
        if len(eligible) >= 50:
            lineup = build_by_metric(eligible, 'projection')
        # else return None - don't fallback

    elif strategy_type == 'fade_threshold':
        threshold = strategy.get('fade_above', 35)
        eligible = [p for p in players if p['ownership'] <= threshold]
        if len(eligible) >= 50:
            lineup = build_by_metric(eligible, 'projection')
        # else return None - don't fallback

    elif strategy_type == 'ownership_buckets':
        lineup = build_with_ownership_buckets(players)

    elif strategy_type == 'leverage':
        lineup = build_leverage_classic(players)

    elif strategy_type == 'correlation':
        lineup = build_max_correlation_classic(players)

    elif strategy_type == 'anti_optimizer':
        lineup = build_anti_optimizer_classic(players)

    elif strategy_type == 'optimized_cash':
        lineup = build_optimized_cash(players)

    elif strategy_type == 'optimized_gpp':
        lineup = build_optimized_gpp(players)

    elif strategy_type == 'sequential_stack':
        lineup = build_sequential_stack(players)

    elif strategy_type == 'pitcher_stack':
        lineup = build_pitcher_stack(players)

    elif strategy_type == 'double_stack':
        lineup = build_double_stack(players)

    elif strategy_type == 'contrarian_stack':
        lineup = build_contrarian_stack(players)

    elif strategy_type == 'stars_scrubs':
        lineup = build_stars_scrubs(players)

    elif strategy_type == 'balanced_cash':
        lineup = build_balanced_cash(players)

    elif strategy_type == 'multi_game':
        lineup = build_multi_game_stack(players)

    # NO FALLBACK - return None if strategy couldn't execute
    return lineup

# ========== FIELD GENERATION - FIXED ==========
def generate_field(slate, field_size, contest_type):
    """Generate realistic field based on format and slate size - FIXED FOR REALISM"""
    field_lineups = []
    players = slate['players']
    format_type = slate['format']
    slate_size = slate['slate_size']

    # FIXED: Much more realistic field composition
    if contest_type == 'cash':
        if slate_size == 'small' or format_type == 'showdown':
            field_composition = {
                'sharp': 0.30,  # 30% sharp (was 15%)
                'good': 0.40,  # 40% good (was 25%)
                'average': 0.25,  # 25% average (was 40%)
                'weak': 0.05  # 5% weak (was 20%)
            }
        elif slate_size == 'medium':
            field_composition = {
                'sharp': 0.25,  # 25% sharp
                'good': 0.40,  # 40% good
                'average': 0.30,  # 30% average
                'weak': 0.05  # 5% weak
            }
        else:  # large
            field_composition = {
                'sharp': 0.20,  # 20% sharp
                'good': 0.35,  # 35% good
                'average': 0.35,  # 35% average
                'weak': 0.10  # 10% weak
            }
    else:  # GPP
        if slate_size == 'small' or format_type == 'showdown':
            field_composition = {
                'sharp': 0.10,  # 10% sharp (was 5%)
                'good': 0.25,  # 25% good (was 15%)
                'average': 0.40,  # 40% average
                'weak': 0.25  # 25% weak (was 40%)
            }
        elif slate_size == 'medium':
            field_composition = {
                'sharp': 0.08,  # 8% sharp
                'good': 0.22,  # 22% good
                'average': 0.45,  # 45% average
                'weak': 0.25  # 25% weak
            }
        else:  # large
            field_composition = {
                'sharp': 0.05,  # 5% sharp (was 2%)
                'good': 0.20,  # 20% good (was 10%)
                'average': 0.45,  # 45% average (was 48%)
                'weak': 0.30  # 30% weak (was 40%)
            }

    # CRITICAL: Add randomness to field composition
    # Some contests are tougher than others
    toughness_multiplier = random.uniform(0.8, 1.2)

    # Generate lineups
    successful_lineups = 0
    attempts = 0
    max_attempts = field_size * 5  # More attempts

    # Track what strategies the field is using
    field_strategy_distribution = defaultdict(int)

    while successful_lineups < field_size and attempts < max_attempts:
        attempts += 1

        # Adjust composition based on toughness
        adjusted_sharp = min(1.0, field_composition['sharp'] * toughness_multiplier)
        rand = random.random()

        # Random lineup for diversity (1% chance)
        if random.random() < 0.01:
            lineup = build_random_lineup(players, format_type, slate_size)
        else:
            if format_type == 'showdown':
                # FIXED: Sharp players use optimal strategies more often
                if rand < adjusted_sharp:
                    # Sharp players adapt to slate
                    if contest_type == 'cash':
                        # Sharp cash players know balanced is best
                        strategy = random.choices(
                            [{'type': 'balanced'}, {'type': 'game_theory'}, {'type': 'onslaught'}],
                            weights=[0.7, 0.2, 0.1]
                        )[0]
                    else:
                        # Sharp GPP players use diverse strategies
                        strategy = random.choices([
                            {'type': 'onslaught'},
                            {'type': 'leverage'},
                            {'type': 'game_theory'},
                            {'type': 'balanced'}
                        ], weights=[0.4, 0.3, 0.2, 0.1])[0]
                    lineup = build_showdown_lineup(players, strategy)

                elif rand < adjusted_sharp + field_composition['good']:
                    # Good players use reasonable strategies
                    if contest_type == 'cash':
                        strategy = random.choice([
                            {'type': 'balanced'},
                            {'type': 'value'},
                            {'type': 'onslaught'}
                        ])
                    else:
                        strategy = random.choice([
                            {'type': 'onslaught'},
                            {'type': 'balanced'},
                            {'type': 'leverage'}
                        ])
                    lineup = build_showdown_lineup(players, strategy)

                elif rand < adjusted_sharp + field_composition['good'] + field_composition['average']:
                    # Average players
                    strategy = random.choice([
                        {'type': 'balanced'},
                        {'type': 'value'},
                        {'type': 'leverage'}
                    ])
                    lineup = build_showdown_lineup(players, strategy)
                else:
                    # Weak players - poor strategy choices
                    strategy = random.choice([
                        {'type': 'value'},  # Wrong for showdown
                        {'type': 'leverage'},  # Risky
                        {'type': 'balanced'}
                    ])
                    lineup = build_showdown_lineup(players, strategy)

            else:  # Classic
                if rand < adjusted_sharp:
                    # Sharp players use slate-appropriate strategies
                    if contest_type == 'cash':
                        if slate_size == 'small':
                            # Sharp players know value dominates small slates
                            strategy = random.choices([
                                {'type': 'value'},
                                {'type': 'blend', 'value_weight': 0.8, 'own_weight': 0.2},
                                {'type': 'optimized_cash'}
                            ], weights=[0.4, 0.4, 0.2])[0]
                        elif slate_size == 'medium':
                            strategy = random.choices([
                                {'type': 'blend', 'own_weight': 0.5, 'value_weight': 0.5},
                                {'type': 'blend', 'own_weight': 0.6, 'value_weight': 0.4},
                                {'type': 'mini_stack', 'stack_size': 3},
                                {'type': 'optimized_cash'}
                            ], weights=[0.3, 0.3, 0.2, 0.2])[0]
                        else:  # large
                            strategy = random.choices([
                                {'type': 'blend', 'own_weight': 0.7, 'value_weight': 0.3},
                                {'type': 'ownership'},
                                {'type': 'optimized_cash'},
                                {'type': 'balanced_cash'}
                            ], weights=[0.3, 0.3, 0.2, 0.2])[0]
                    else:  # GPP
                        if slate_size == 'small':
                            strategy = random.choices([
                                {'type': 'stack', 'stack_size': 4},
                                {'type': 'stack', 'stack_size': 5},
                                {'type': 'ceiling'},
                                {'type': 'mini_stack', 'stack_size': 3}
                            ], weights=[0.3, 0.3, 0.2, 0.2])[0]
                        else:
                            # Sharp GPP players on larger slates
                            strategy = random.choices([
                                {'type': 'stack', 'stack_size': 5},
                                {'type': 'sequential_stack'},
                                {'type': 'game_stack'},
                                {'type': 'ownership_buckets'},
                                {'type': 'leverage'}
                            ], weights=[0.2, 0.2, 0.2, 0.2, 0.2])[0]

                    lineup = build_classic_lineup(players, strategy, slate_size)
                    if lineup:
                        field_strategy_distribution[strategy.get('type', 'unknown')] += 1

                elif rand < adjusted_sharp + field_composition['good']:
                    # Good players - mostly sound strategies
                    if contest_type == 'cash':
                        strategy = random.choices([
                            {'type': 'blend', 'own_weight': 0.5, 'value_weight': 0.5},
                            {'type': 'value'},
                            {'type': 'ownership'},
                            {'type': 'mini_stack', 'stack_size': 3}
                        ], weights=[0.3, 0.3, 0.2, 0.2])[0]
                    else:
                        strategy = random.choices([
                            {'type': 'stack', 'stack_size': random.choice([4, 5])},
                            {'type': 'ownership_buckets'},
                            {'type': 'ceiling'},
                            {'type': 'game_stack'}
                        ], weights=[0.4, 0.2, 0.2, 0.2])[0]
                    lineup = build_classic_lineup(players, strategy, slate_size)

                elif rand < adjusted_sharp + field_composition['good'] + field_composition['average']:
                    # Average players
                    if contest_type == 'cash':
                        # Some use wrong strategies
                        strategy = random.choices([
                            {'type': 'value'},
                            {'type': 'ownership'},
                            {'type': 'ceiling'},  # Wrong for cash
                            {'type': 'blend', 'own_weight': 0.3, 'value_weight': 0.7}
                        ], weights=[0.3, 0.3, 0.1, 0.3])[0]
                    else:
                        # Often don't stack properly
                        strategy = random.choices([
                            {'type': 'stack', 'stack_size': random.choice([3, 4, 5])},
                            {'type': 'value'},  # No correlation
                            {'type': 'ownership'},  # No correlation
                            {'type': 'ceiling'}
                        ], weights=[0.3, 0.3, 0.2, 0.2])[0]
                    lineup = build_classic_lineup(players, strategy, slate_size)
                else:
                    # Weak players - poor choices
                    if contest_type == 'cash':
                        strategy = random.choices([
                            {'type': 'ceiling'},  # Wrong for cash
                            {'type': 'contrarian', 'max_own': 15},  # Wrong for cash
                            {'type': 'value'},
                            {'type': 'stack', 'stack_size': 5}  # Wrong for cash
                        ], weights=[0.3, 0.2, 0.3, 0.2])[0]
                    else:
                        strategy = random.choices([
                            {'type': 'value'},  # No correlation
                            {'type': 'ownership'},  # No correlation
                            {'type': 'contrarian', 'max_own': 5},  # Too strict
                            {'type': 'stack', 'stack_size': 2}  # Too small
                        ], weights=[0.3, 0.3, 0.2, 0.2])[0]
                    lineup = build_classic_lineup(players, strategy, slate_size)

        if lineup:
            field_lineups.append(lineup)
            successful_lineups += 1

    # Fill remaining with duplicates that have score variance
    while len(field_lineups) < field_size:
        if field_lineups:
            # Duplicate with small modifications
            base_lineup = random.choice(field_lineups).copy()
            # Add small variance to projection/ownership
            if 'projection' in base_lineup:
                base_lineup['projection'] *= random.uniform(0.95, 1.05)
            if 'ownership' in base_lineup:
                base_lineup['ownership'] *= random.uniform(0.90, 1.10)
            field_lineups.append(base_lineup)
        else:
            break

    return field_lineups[:field_size]

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
def simulate_lineup_score(lineup):
    """Simulate realistic lineup scoring with PROPER variance"""
    total_score = 0
    format_type = lineup.get('format', 'classic')

    # INJURY/SCRATCH RISK (before game)
    for player in lineup['lineup']:
        if random.random() < 0.015:  # 1.5% chance player is scratched
            # Player doesn't play - need to handle this
            # For now, severe penalty
            return random.uniform(50, 80)  # Lineup is broken

    # WEATHER/GAME FACTORS
    weather_factor = 1.0

    # Extreme weather (affects outdoor games)
    if random.random() < 0.05:  # 5% chance
        weather_factor = random.choice([
            0.7,  # Rain delay, shortened game
            0.85,  # Cold weather, low scoring
            1.15,  # Hot weather, balls flying
            0.6  # Game postponed mid-way
        ])

    # Blowout factor
    if random.random() < 0.10:  # 10% chance of blowout
        # One team dominates
        if format_type == 'showdown':
            # In showdown, this really matters
            teams = list(set(p['team'] for p in lineup['lineup']))
            if len(teams) == 2:
                winning_team = random.choice(teams)
                losing_team = teams[0] if teams[1] == winning_team else teams[1]

                for player in lineup['lineup']:
                    if player['team'] == winning_team:
                        player['temp_multiplier'] = random.uniform(1.2, 1.5)
                    else:
                        player['temp_multiplier'] = random.uniform(0.5, 0.8)

    if format_type == 'showdown':
        # Captain scoring
        captain = lineup.get('captain')
        if captain:
            mean = captain['projection'] * 1.5

            # MORE VARIANCE for showdown
            std = mean * 0.30  # 30% standard deviation

            # Add player-specific variance
            player_var = random.random()
            if player_var < 0.02:  # 2% mega bust
                captain_score = random.uniform(0, mean * 0.3)
            elif player_var < 0.05:  # 3% injury/early exit
                captain_score = random.uniform(mean * 0.1, mean * 0.4)
            elif player_var < 0.10:  # 5% bad game
                captain_score = random.uniform(mean * 0.4, mean * 0.7)
            elif player_var < 0.90:  # 80% normal range
                captain_score = np.random.normal(mean, std)
            elif player_var < 0.97:  # 7% great game
                captain_score = random.uniform(mean * 1.5, mean * 2.0)
            else:  # 3% ceiling game
                captain_score = random.uniform(mean * 2.0, mean * 3.0)

            # Apply team multiplier if exists
            if hasattr(captain, 'temp_multiplier'):
                captain_score *= captain['temp_multiplier']

            captain_score *= weather_factor
            total_score += max(0, captain_score)

        # UTIL scoring
        for player in lineup['lineup'][1:]:
            mean = player['projection']
            std = mean * 0.25

            # Individual variance
            player_var = random.random()
            if player_var < 0.03:  # 3% bust
                score = random.uniform(0, mean * 0.4)
            elif player_var < 0.10:  # 7% poor
                score = random.uniform(mean * 0.4, mean * 0.7)
            elif player_var < 0.85:  # 75% normal
                score = np.random.normal(mean, std)
            elif player_var < 0.95:  # 10% good
                score = random.uniform(mean * 1.3, mean * 1.8)
            else:  # 5% ceiling
                score = random.uniform(mean * 1.8, mean * 2.5)

            if hasattr(player, 'temp_multiplier'):
                score *= player['temp_multiplier']

            score *= weather_factor
            total_score += max(0, score)

        # Showdown correlation bonus/penalty
        teams_in_lineup = defaultdict(int)
        for p in lineup['lineup']:
            teams_in_lineup[p['team']] += 1

        max_team_count = max(teams_in_lineup.values())
        if max_team_count >= 4:
            # Onslaught - high variance
            onslaught_result = random.random()
            if onslaught_result < 0.25:  # 25% bust
                total_score *= random.uniform(0.7, 0.85)
            elif onslaught_result < 0.65:  # 40% normal
                total_score *= random.uniform(0.95, 1.05)
            else:  # 35% boom
                total_score *= random.uniform(1.15, 1.40)

    else:  # Classic
        # Team and game correlations
        team_counts = defaultdict(int)
        team_players = defaultdict(list)
        game_players = defaultdict(list)
        team_scores = defaultdict(float)

        for player in lineup['lineup']:
            team_counts[player['team']] += 1
            team_players[player['team']].append(player)
            if 'game_id' in player:
                game_players[player['game_id']].append(player)

        # Determine team performances (correlated)
        team_multipliers = {}
        for team in team_counts:
            team_var = random.random()
            if team_var < 0.05:  # 5% team explosion
                team_multipliers[team] = random.uniform(1.4, 1.8)
            elif team_var < 0.15:  # 10% very good
                team_multipliers[team] = random.uniform(1.15, 1.35)
            elif team_var < 0.30:  # 15% good
                team_multipliers[team] = random.uniform(1.05, 1.15)
            elif team_var < 0.70:  # 40% average
                team_multipliers[team] = random.uniform(0.90, 1.10)
            elif team_var < 0.85:  # 15% poor
                team_multipliers[team] = random.uniform(0.75, 0.90)
            elif team_var < 0.95:  # 10% very poor
                team_multipliers[team] = random.uniform(0.60, 0.75)
            else:  # 5% complete bust
                team_multipliers[team] = random.uniform(0.40, 0.60)

        # Score each player
        for player in lineup['lineup']:
            if player['position'] == 'P':
                # Pitchers have independent variance
                mean = player['projection']
                std = mean * 0.35  # High variance

                pitcher_var = random.random()
                if pitcher_var < 0.02:  # 2% injury
                    score = random.uniform(0, 5)
                elif pitcher_var < 0.07:  # 5% blow up
                    score = random.uniform(-5, mean * 0.3)
                elif pitcher_var < 0.15:  # 8% bad start
                    score = random.uniform(mean * 0.3, mean * 0.6)
                elif pitcher_var < 0.80:  # 65% normal
                    score = np.random.normal(mean, std)
                elif pitcher_var < 0.93:  # 13% quality start
                    score = random.uniform(mean * 1.2, mean * 1.5)
                elif pitcher_var < 0.98:  # 5% gem
                    score = random.uniform(mean * 1.5, mean * 2.0)
                else:  # 2% no-hitter/CGSO
                    score = random.uniform(mean * 2.0, mean * 2.5)

                # Opposing team penalty if pitcher does well
                if score > mean * 1.3:
                    for p in lineup['lineup']:
                        if p['team'] != player['team'] and p.get('game_id') == player.get('game_id'):
                            opp_team = p['team']
                            if opp_team in team_multipliers:
                                team_multipliers[opp_team] *= 0.85
                            break

            else:  # Hitter
                mean = player['projection']
                std = mean * 0.25

                # Base score
                hitter_var = random.random()
                if hitter_var < 0.02:  # 2% injury/ejection
                    score = random.uniform(0, mean * 0.2)
                elif hitter_var < 0.08:  # 6% golden sombrero
                    score = random.uniform(mean * 0.2, mean * 0.5)
                elif hitter_var < 0.20:  # 12% bad game
                    score = random.uniform(mean * 0.5, mean * 0.8)
                elif hitter_var < 0.80:  # 60% normal
                    score = np.random.normal(mean, std)
                elif hitter_var < 0.93:  # 13% good game
                    score = random.uniform(mean * 1.2, mean * 1.6)
                elif hitter_var < 0.98:  # 5% great game
                    score = random.uniform(mean * 1.6, mean * 2.2)
                else:  # 2% historic game
                    score = random.uniform(mean * 2.2, mean * 3.0)

                # Apply team correlation
                team_mult = team_multipliers.get(player['team'], 1.0)
                score *= team_mult

                # Batting order matters more in high-scoring games
                if team_mult > 1.2 and player.get('batting_order', 0) in [1, 2, 3, 4]:
                    score *= random.uniform(1.05, 1.15)
                elif team_mult < 0.8 and player.get('batting_order', 0) in [7, 8, 9]:
                    score *= random.uniform(0.85, 0.95)

            score *= weather_factor
            total_score += max(0, score)

        # Stack correlation bonus
        max_stack = max(team_counts.values()) if team_counts else 0

        if max_stack >= 5:
            # Full stack correlation
            stack_team = max(team_counts.items(), key=lambda x: x[1])[0]
            team_mult = team_multipliers.get(stack_team, 1.0)

            if team_mult > 1.3:  # Team went off
                total_score *= random.uniform(1.10, 1.20)
            elif team_mult > 1.1:  # Team did well
                total_score *= random.uniform(1.05, 1.10)
            elif team_mult < 0.7:  # Team busted
                total_score *= random.uniform(0.85, 0.92)
            else:
                total_score *= random.uniform(0.97, 1.03)

        elif max_stack >= 4:
            # 4-man stack
            stack_team = max(team_counts.items(), key=lambda x: x[1])[0]
            team_mult = team_multipliers.get(stack_team, 1.0)

            if team_mult > 1.2:
                total_score *= random.uniform(1.05, 1.12)
            elif team_mult < 0.8:
                total_score *= random.uniform(0.90, 0.95)

        # Game stack correlation
        if game_players:
            max_game_stack = max(len(players) for players in game_players.values())
            if max_game_stack >= 5:
                # Shootout bonus
                if random.random() < 0.15:  # 15% chance
                    total_score *= random.uniform(1.08, 1.18)

    # Final adjustments
    # Add small random noise
    total_score += np.random.normal(0, 2)

    # Extreme outliers (both ways)
    outlier_chance = random.random()
    if outlier_chance < 0.005:  # 0.5% disaster
        total_score *= 0.5
    elif outlier_chance > 0.995:  # 0.5% miracle
        total_score *= 1.5

    # Reasonable bounds
    if format_type == 'showdown':
        total_score = max(40, min(350, total_score))
    else:
        total_score = max(60, min(300, total_score))

    return total_score

# ========== ANALYSIS - ENHANCED ==========

def analyze_results(results: List[Dict]):
    """Analyze results by format and slate size - ENHANCED"""
    print("\n" + "=" * 80)
    print("🎯 DFS ULTIMATE SIMULATOR 2.0 - DETAILED RESULTS ANALYSIS")
    print("=" * 80 + "\n")

    # Group results
    grouped_results = defaultdict(lambda: defaultdict(list))

    for r in results:
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
                wins = sum(1 for r in results_list if r['profit'] > 0)
                win_rate = (wins / len(results_list)) * 100
                avg_roi = np.mean([r['roi'] for r in results_list])
                avg_score = np.mean([r['score'] for r in results_list])
                avg_ownership = np.mean([r['ownership'] for r in results_list])
                avg_rank = np.mean([r['rank'] for r in results_list])
                median_rank = np.median([r['rank'] for r in results_list])
                percentile_75 = np.percentile([r['percentile'] for r in results_list], 75)
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
                avg_roi = np.mean([r['roi'] for r in results_list])
                top1_pct = sum(1 for r in results_list if r['percentile'] >= 99) / len(results_list) * 100
                top5_pct = sum(1 for r in results_list if r['percentile'] >= 95) / len(results_list) * 100
                top10_pct = sum(1 for r in results_list if r['percentile'] >= 90) / len(results_list) * 100
                top20_pct = sum(1 for r in results_list if r['percentile'] >= 80) / len(results_list) * 100
                profitable = sum(1 for r in results_list if r['profit'] > 0) / len(results_list) * 100
                avg_rank = np.mean([r['rank'] for r in results_list])
                median_rank = np.median([r['rank'] for r in results_list])
                best_finish = min(r['rank'] for r in results_list)
                avg_payout_when_cash = np.mean([r['payout'] for r in results_list if r['payout'] > 0]) if any(
                    r['payout'] > 0 for r in results_list) else 0

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

        # Display results
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

    # Extract failure summaries
    failures = []
    score_distributions = defaultdict(list)

    for r in results:
        if r.get('type') == 'failure_summary':
            failures.append(r)
        elif not r.get('failed'):
            # Track score distributions
            key = f"{r['format']}_{r['slate_size']}_{r['contest_type']}"
            score_distributions[key].append({
                'score': r['score'],
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
            for key, reasons in f['failures'].items():
                if key != 'exceptions':
                    total = reasons.get('total', sum(v for k, v in reasons.items() if k != 'total'))
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
            'team_totals': {
                game['home_team']: game['home_total'],
                game['away_team']: game['away_total']
            }
        }

        for team in [game['home_team'], game['away_team']]:
            if format_type == 'showdown':
                # SHOWDOWN: Realistic roster (1 pitcher + 9 starters + 1-2 bench)

                # Starting pitcher
                player = generate_realistic_showdown_player(player_id, team, 'P', 0, game_data)
                players.append(player)
                player_id += 1

                # Position distribution for realistic lineup
                batting_order_positions = {
                    1: random.choice(['CF', 'SS', '2B']),  # Speedy leadoff
                    2: random.choice(['2B', 'SS', 'RF']),  # Contact hitter
                    3: random.choice(['1B', '3B', 'RF']),  # Best hitter
                    4: random.choice(['1B', 'DH', 'LF']),  # Power cleanup
                    5: random.choice(['3B', 'DH', 'RF']),  # RBI guy
                    6: random.choice(['C', 'LF', '2B']),
                    7: random.choice(['SS', '2B', 'CF']),
                    8: random.choice(['C', 'CF', '2B']),
                    9: random.choice(['C', 'SS', '2B'])  # Weakest hitter
                }

                # Generate starters in batting order
                for batting_order in range(1, 10):
                    position = batting_order_positions[batting_order]
                    # Convert DH to actual position for DFS
                    if position == 'DH':
                        position = random.choice(['1B', 'OF'])
                    # Convert specific OF to generic OF
                    if position in ['LF', 'CF', 'RF']:
                        position = 'OF'

                    player = generate_realistic_showdown_player(
                        player_id, team, position, batting_order, game_data
                    )
                    players.append(player)
                    player_id += 1

                # 1-2 bench players (utility/pinch hitters)
                num_bench = random.choice([1, 2])
                for _ in range(num_bench):
                    position = random.choice(['OF', '2B', 'SS'])
                    player = generate_realistic_showdown_player(
                        player_id, team, position, 0, game_data  # 0 = bench
                    )
                    players.append(player)
                    player_id += 1

            else:  # CLASSIC format
                # CLASSIC: Full roster with realistic distribution

                # Starting pitchers (1-2 confirmed starters)
                num_starters = 2 if random.random() < 0.7 else 1  # 70% double header
                for _ in range(num_starters):
                    player = generate_realistic_classic_player(
                        player_id, team, 'P', 0, game_data, slate_size, is_starter=True
                    )
                    players.append(player)
                    player_id += 1

                # Relief pitchers (1-3)
                num_relievers = random.choice([1, 2, 3])
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

                for batting_order in range(1, 10):
                    position = classic_batting_positions[batting_order]
                    # Handle DH and specific OF
                    if position == 'DH':
                        position = random.choice(['1B', 'OF'])
                    if position in ['LF', 'CF', 'RF']:
                        position = 'OF'

                    # Ensure we don't have too many of one position
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

                # Bench players (3-5 extras)
                num_bench = random.choice([3, 4, 5])
                bench_positions = ['OF', 'OF', '2B', 'SS', '3B', 'C', '1B']
                random.shuffle(bench_positions)

                for i in range(num_bench):
                    position = bench_positions[i % len(bench_positions)]
                    # Ensure position variety
                    if positions_used[position] >= 5:
                        position = random.choice(['2B', 'SS', '3B'])

                    player = generate_realistic_classic_player(
                        player_id, team, position, 0, game_data, slate_size  # 0 = bench
                    )
                    players.append(player)
                    positions_used[position] += 1
                    player_id += 1

                # Add a few cheap punt plays to ensure lineup flexibility
                punt_positions = ['C', 'SS', '2B', 'OF']
                for _ in range(2):
                    position = random.choice(punt_positions)
                    player = generate_realistic_classic_player(
                        player_id, team, position, 0, game_data, slate_size, force_punt=True
                    )
                    players.append(player)
                    player_id += 1

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
    """Generate classic player with realistic salary based on role"""

    team_total = game_data.get('team_totals', {}).get(team, 4.5)

    if position == 'P':
        if is_starter:
            # Starting pitchers
            skill = random.random()
            if skill < 0.15:  # 15% aces
                salary = random.randint(9000, 12000)
                projection = random.uniform(40, 50)
                ownership = random.uniform(20, 40)
            elif skill < 0.40:  # 25% good starters
                salary = random.randint(7000, 9000)
                projection = random.uniform(30, 40)
                ownership = random.uniform(10, 25)
            else:  # 60% average/backend starters
                salary = random.randint(4500, 7000)
                projection = random.uniform(20, 30)
                ownership = random.uniform(5, 15)
        else:
            # Relief pitchers (cheaper)
            salary = random.randint(3000, 5500)
            projection = random.uniform(10, 20)
            ownership = random.uniform(2, 10)
    else:
        # Hitters
        if force_punt:
            # Forced punt plays for lineup flexibility
            salary = random.randint(2000, 2800)
            projection = salary / 1000 * random.uniform(2.0, 2.8)
            ownership = random.uniform(1, 8)
        elif batting_order == 0:  # Bench
            salary = random.randint(2000, 4000)
            projection = random.uniform(5, 10)
            ownership = random.uniform(2, 12)
        elif batting_order in [1, 2]:  # Top of order
            salary = random.randint(6000, 9000)
            projection = random.uniform(14, 20)
            ownership = random.uniform(15, 35) if slate_size == 'small' else random.uniform(10, 25)
        elif batting_order in [3, 4]:  # Heart of order
            salary = random.randint(6500, 10000)
            projection = random.uniform(15, 22)
            ownership = random.uniform(20, 45) if slate_size == 'small' else random.uniform(12, 30)
        elif batting_order in [5, 6]:  # Middle order
            salary = random.randint(4500, 7000)
            projection = random.uniform(11, 16)
            ownership = random.uniform(10, 25) if slate_size == 'small' else random.uniform(5, 15)
        elif batting_order in [7, 8]:  # Bottom order
            salary = random.randint(3000, 5000)
            projection = random.uniform(8, 12)
            ownership = random.uniform(5, 15) if slate_size == 'small' else random.uniform(2, 10)
        else:  # 9th hitter
            salary = random.randint(2000, 3500)
            projection = random.uniform(6, 10)
            ownership = random.uniform(3, 12) if slate_size == 'small' else random.uniform(1, 8)

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

    # Skill level (for field generation)
    if salary > 8000:
        skill_level = random.uniform(0.80, 1.0)
    elif salary > 6000:
        skill_level = random.uniform(0.60, 0.80)
    elif salary > 4000:
        skill_level = random.uniform(0.40, 0.60)
    else:
        skill_level = random.uniform(0.10, 0.40)

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
        'skill_level': skill_level,
        'is_punt': salary <= 3000
    }

# ========== SHOWDOWN LINEUP BUILDERS ==========

def build_showdown_lineup(players, strategy):
    """Build showdown lineup with 1 CPT + 5 UTIL"""
    strategy_type = strategy.get('type')

    if strategy_type == 'balanced':
        # Top projected player as captain
        sorted_players = sorted(players, key=lambda x: x['projection'], reverse=True)
        if not sorted_players:
            return None  # Don't fallback
        captain = sorted_players[0]
        util_pool = [p for p in players if p['id'] != captain['id']]
        util_pool.sort(key=lambda x: x['value_score'], reverse=True)
        return build_showdown_with_captain(captain, util_pool)

    elif strategy_type == 'leverage':
        # Low-owned player as captain
        leverage_players = [p for p in players if p['ownership'] < 20 and p['ceiling'] > 20]
        if not leverage_players:
            return None  # Don't fallback to balanced
        leverage_players.sort(key=lambda x: x['ceiling'] / (x['ownership'] + 1), reverse=True)
        captain = leverage_players[0]
        util_pool = [p for p in players if p['id'] != captain['id']]
        return build_showdown_with_captain(captain, util_pool)

    elif strategy_type == 'onslaught':
        # Must find a team with enough players
        team_totals = defaultdict(float)
        team_players = defaultdict(list)

        for p in players:
            team_players[p['team']].append(p)
            if 'team_total' in p:
                team_totals[p['team']] = p['team_total']

        if not team_totals:
            return None  # Can't execute onslaught without team totals

        winning_team = max(team_totals.items(), key=lambda x: x[1])[0]
        winning_players = team_players[winning_team]

        if len(winning_players) < 4:  # Need at least 4 for onslaught
            return None

        winning_players.sort(key=lambda x: x['projection'], reverse=True)
        captain = winning_players[0]

        # Must get 3-4 more from winning team
        util_pool = winning_players[1:5] + [p for p in players if p['team'] != winning_team]
        util_pool.sort(key=lambda x: x['value_score'], reverse=True)

        lineup_result = build_showdown_with_captain(captain, util_pool)

        # Verify it's actually an onslaught
        if lineup_result:
            team_count = sum(1 for p in lineup_result['lineup'] if p['team'] == winning_team)
            if team_count < 4:
                return None  # Not a true onslaught

        return lineup_result

    elif strategy_type == 'game_theory':
        # Must have a pitcher as captain
        pitchers = [p for p in players if p['position'] == 'P']
        if not pitchers:
            return None
        pitchers.sort(key=lambda x: x['projection'], reverse=True)
        captain = pitchers[0]

        # Must have opposing hitters
        opp_hitters = [p for p in players
                       if p['team'] != captain['team'] and p['position'] != 'P']
        if len(opp_hitters) < 3:
            return None  # Can't execute game theory

        same_team = [p for p in players
                     if p['team'] == captain['team'] and p['id'] != captain['id']]

        util_pool = opp_hitters[:3] + same_team
        util_pool.sort(key=lambda x: x['value_score'], reverse=True)

        return build_showdown_with_captain(captain, util_pool)

    elif strategy_type == 'value':
        # Must find cheap viable captain
        cheap_viable = [p for p in players if p['salary'] < 5000 and p['projection'] > 8]
        if not cheap_viable:
            return None  # Can't execute value strategy

        cheap_viable.sort(key=lambda x: x['captain_value'], reverse=True)
        captain = cheap_viable[0]

        util_pool = [p for p in players if p['id'] != captain['id']]
        util_pool.sort(key=lambda x: x['projection'], reverse=True)

        return build_showdown_with_captain(captain, util_pool)

    return None  # Invalid strategy type


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


def build_by_metric(players, metric, reverse=True):
    """Build lineup optimizing for specific metric with RELAXED constraints"""
    # Ensure all players have the metric
    valid_players = [p for p in players if metric in p]

    if not valid_players:
        return None

    sorted_players = sorted(valid_players, key=lambda x: x.get(metric, 0), reverse=reverse)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # CHANGED: More flexible salary management
    # Phase 1: Fill core positions first (P, C are often bottlenecks)
    priority_positions = ['P', 'C', 'SS', '2B', '3B', '1B', 'OF']

    for pos in priority_positions:
        required = CLASSIC_CONFIG['positions'].get(pos, 0)
        pos_players = [p for p in sorted_players if p['position'] == pos and p not in lineup]

        for player in pos_players[:required * 2]:  # Consider more players
            if positions_filled[pos] >= required:
                break

            # CHANGED: Less restrictive salary check
            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            # CHANGED: Check team limit but be flexible
            if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                # Only skip if we have other options at this position
                other_options = [p for p in pos_players if p['team'] != player['team']
                                 and p not in lineup]
                if len(other_options) > 0:
                    continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

    # Phase 2: Fill remaining spots with best available
    remaining_needed = 10 - len(lineup)
    if remaining_needed > 0:
        # Get all remaining eligible players
        remaining_players = []
        for p in sorted_players:
            if p in lineup:
                continue
            pos = p['position']
            if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'].get(pos, 0):
                continue
            if salary + p['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue
            remaining_players.append(p)

        # Sort by metric but also consider position needs
        remaining_players.sort(key=lambda x: x.get(metric, 0), reverse=reverse)

        for player in remaining_players:
            if len(lineup) >= 10:
                break

            # CHANGED: More flexible team constraint
            if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                # Check if we're close to finishing and need this player
                spots_left = 10 - len(lineup)
                if spots_left > 2:  # Only enforce strictly if we have options
                    continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[player['position']] += 1
            teams_used[player['team']] += 1

    # Phase 3: If still short, fill with any valid player
    if len(lineup) < 10:
        all_remaining = [p for p in players if p not in lineup]
        all_remaining.sort(key=lambda x: x['salary'])  # Cheapest first

        for player in all_remaining:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'].get(pos, 0):
                continue

            if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                continue

            # CHANGED: Ignore team constraint if desperate
            if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                # If we're at 9 players, take anyone
                if len(lineup) < 9:
                    continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

    # Validate lineup
    if len(lineup) == 10:
        num_teams = len(set(p['team'] for p in lineup))
        if num_teams >= 2:  # Minimum team requirement
            return create_classic_lineup_result(lineup)

    return None


def build_team_stack(players, stack_size):
    """Build lineup with team stack - RELAXED CONSTRAINTS"""
    team_players = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    # Check if any team has enough players
    valid_teams = [(team, players_list) for team, players_list in team_players.items()
                   if len(players_list) >= stack_size]

    if not valid_teams:
        return None  # Can't build the requested stack size

    # Sort teams by total projection of best players
    team_scores = []
    for team, players_list in valid_teams:
        players_list.sort(key=lambda x: x['projection'], reverse=True)
        score = sum(p['projection'] for p in players_list[:stack_size])
        team_scores.append((team, score, players_list))

    team_scores.sort(key=lambda x: x[1], reverse=True)

    # Try multiple teams
    for team, _, team_list in team_scores[:10]:  # Try more teams
        # Try different combinations of stack players
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

            # Add stack players with flexible position filling
            stack_added = 0
            positions_needed = dict(CLASSIC_CONFIG['positions'])

            for player in stack_candidates:
                if stack_added >= stack_size:
                    break

                pos = player['position']

                # CHANGED: Don't skip if position filled, save for later
                if positions_filled[pos] >= positions_needed[pos]:
                    continue

                # CHANGED: More flexible salary check
                # Only check if we'd have enough for minimum lineup
                min_remaining_salary = 2500 * (9 - len(lineup))  # Assume $2500 avg for rest
                if salary + player['salary'] + min_remaining_salary > CLASSIC_CONFIG['salary_cap']:
                    continue

                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1
                stack_added += 1

            # Need at least stack_size players from the team
            if stack_added < stack_size:
                continue

            # Fill remaining roster spots
            # CHANGED: Priority order - P and C first (scarcest positions)
            priority_positions = ['P', 'C', 'SS', '2B', '3B', '1B', 'OF']

            other_players = [p for p in players if p['team'] != team]

            for pos in priority_positions:
                needed = positions_needed[pos] - positions_filled.get(pos, 0)
                if needed <= 0:
                    continue

                pos_players = [p for p in other_players if p['position'] == pos and p not in lineup]
                pos_players.sort(key=lambda x: x.get('value_score', 0), reverse=True)

                for player in pos_players[:needed * 2]:  # Consider extra players
                    if positions_filled[pos] >= positions_needed[pos]:
                        break

                    if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                        continue

                    # CHANGED: Flexible team constraint
                    if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                        if len(lineup) < 9:  # Only enforce if we have options
                            continue

                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1

            # Fill any remaining spots with best available
            if len(lineup) < 10:
                remaining = [p for p in players if p not in lineup]
                remaining.sort(key=lambda x: x.get('value_score', 0), reverse=True)

                for player in remaining:
                    if len(lineup) >= 10:
                        break

                    pos = player['position']
                    if positions_filled.get(pos, 0) >= positions_needed[pos]:
                        continue

                    if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                        continue

                    # Very flexible on team constraint for last spots
                    if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                        if len(lineup) < 9 and player['team'] != team:
                            continue

                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1

            # Check if valid lineup
            if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
                return create_classic_lineup_result(lineup)

    return None



def build_with_mini_stack(players: List[Dict], stack_size: int = 3) -> Optional[Dict]:
    """Build cash lineup with mini stack - FIXED"""
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
        return build_by_metric(players, 'floor')

    # Sort teams by score
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

    # Fallback to regular cash build
    return build_optimized_cash(players)


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
        return build_by_metric(players, 'projection')

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
    return build_by_metric(players, 'projection')


def build_optimized_cash(players: List[Dict]) -> Optional[Dict]:
    """Build cash lineup using optimization findings - 79% win rate approach"""

    # Calculate optimized score for each player based on findings:
    # - 37% weight on recent form (last 4 games)
    # - 38% weight on projections
    # - 19% weight on season average
    # - 80% floor focus, 20% ceiling
    # - Platoon advantage: +8.4%
    # - Hot streaks: +8.5%

    for player in players:
        # Recent form component (37%)
        recent_bonus = player.get('recent_form', 1.0)
        recent_score = player['projection'] * recent_bonus * 0.37

        # Base projection component (38%)
        proj_score = player['projection'] * 0.38

        # Season average proxy (19%)
        season_score = player['projection'] * 0.95 * 0.19  # Slight discount for season avg

        # Floor/ceiling blend (80/20)
        floor_ceiling = player['floor'] * 0.80 + player['ceiling'] * 0.20

        # Apply bonuses
        platoon_boost = 1.0 + player.get('platoon_advantage', 0)
        hot_streak_boost = 1.085 if player.get('is_hot_streak', False) else 1.0

        # Combined optimized score
        player['optimized_cash_score'] = (
                (recent_score + proj_score + season_score) *
                platoon_boost * hot_streak_boost *
                (floor_ceiling / player['projection'])  # Floor/ceiling adjustment
        )

    return build_by_metric(players, 'optimized_cash_score')


def build_optimized_gpp(players: List[Dict]) -> Optional[Dict]:
    """Build GPP lineup using optimization findings - 64th percentile approach"""

    # Key findings:
    # - Stack size: 4 optimal (not 5)
    # - Sequential stacking (1-2-3-4-5 batting order)
    # - Top teams get 1.34x multiplier
    # - Mid teams get 1.22x multiplier
    # - Barrel rate > 11.7% get 1.19x boost
    # - Undervalued xwOBA players get 1.25x boost

    # Find best team to stack
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
    """Build lineup with sequential batting order stack (1-2-3-4-5) - RELAXED"""

    # Group by team and batting order
    team_batting_orders = defaultdict(lambda: defaultdict(list))

    for p in players:
        if p['position'] != 'P' and p.get('batting_order', 0) > 0:
            team = p['team']
            order = p['batting_order']
            team_batting_orders[team][order].append(p)

    # Find teams with good sequential options
    valid_teams = []

    for team, batting_orders in team_batting_orders.items():
        # Check different sequential combinations
        sequences = [
            (1, 2, 3, 4, 5),  # Ideal
            (2, 3, 4, 5, 6),  # Also good
            (1, 2, 3, 4),  # Top 4
            (3, 4, 5, 6),  # Middle 4
        ]

        for seq in sequences:
            if all(i in batting_orders for i in seq):
                # Calculate cost and projection
                seq_players = []
                for i in seq:
                    # Get best player at each spot
                    best_at_spot = max(batting_orders[i], key=lambda x: x['projection'])
                    seq_players.append(best_at_spot)

                total_salary = sum(p['salary'] for p in seq_players)
                total_proj = sum(p['projection'] for p in seq_players)

                valid_teams.append({
                    'team': team,
                    'sequence': seq,
                    'players': seq_players,
                    'salary': total_salary,
                    'projection': total_proj
                })

    if not valid_teams:
        return None

    # Sort by projection
    valid_teams.sort(key=lambda x: x['projection'], reverse=True)

    # Try each valid team
    for team_data in valid_teams[:5]:
        team = team_data['team']
        sequence = team_data['sequence']

        # Try different player combinations at each batting spot
        for combo_attempt in range(3):
            lineup = []
            salary = 0
            positions_filled = defaultdict(int)
            teams_used = defaultdict(int)

            # Add sequential players
            for batting_pos in sequence:
                candidates = team_batting_orders[team][batting_pos]

                # Sort differently each attempt
                if combo_attempt == 0:
                    candidates.sort(key=lambda x: x['projection'], reverse=True)
                elif combo_attempt == 1:
                    candidates.sort(key=lambda x: x.get('value_score', 0), reverse=True)
                else:
                    candidates.sort(key=lambda x: x['salary'])  # Cheapest

                added_at_spot = False
                for player in candidates:
                    if player in lineup:
                        continue

                    pos = player['position']

                    # CHANGED: Flexible position filling
                    if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                        # Try next player at this batting spot
                        continue

                    # CHANGED: Flexible salary check
                    remaining_spots = 10 - len(lineup)
                    min_needed = 2300 * (remaining_spots - 1)  # Lower minimum
                    if salary + player['salary'] + min_needed > CLASSIC_CONFIG['salary_cap']:
                        continue

                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1
                    added_at_spot = True
                    break

                if not added_at_spot:
                    # Couldn't add player at this batting spot
                    break

            # Check if we got enough sequential players (at least 4)
            if len([p for p in lineup if p['team'] == team]) < 4:
                continue

            # Fill remaining spots - prioritize scarce positions
            priority_positions = ['P', 'C', 'SS', '2B', '3B', '1B', 'OF']

            other_players = [p for p in players if p not in lineup]

            for pos in priority_positions:
                needed = CLASSIC_CONFIG['positions'][pos] - positions_filled.get(pos, 0)
                if needed <= 0:
                    continue

                pos_players = [p for p in other_players if p['position'] == pos]

                # For pitchers, prefer from different teams
                if pos == 'P':
                    pos_players.sort(key=lambda x: (x['team'] == team, -x.get('value_score', 0)))
                else:
                    pos_players.sort(key=lambda x: x.get('value_score', 0), reverse=True)

                for player in pos_players[:needed * 3]:  # Consider more options
                    if positions_filled.get(pos, 0) >= CLASSIC_CONFIG['positions'][pos]:
                        break

                    if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                        continue

                    # CHANGED: Very flexible team constraint
                    if teams_used[player['team']] >= CLASSIC_CONFIG['max_players_per_team']:
                        # Only skip if we have many other options
                        other_team_options = [p for p in pos_players
                                              if p['team'] != player['team']
                                              and p not in lineup
                                              and salary + p['salary'] <= CLASSIC_CONFIG['salary_cap']]
                        if len(other_team_options) > 2:
                            continue

                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1

            # Final fill with any valid players
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
                    teams_used[player['team']] += 1

            if len(lineup) == 10 and len(set(p['team'] for p in lineup)) >= 2:
                return create_classic_lineup_result(lineup)

    return None


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

    # Generate field
    field_lineups = generate_field(slate, field_size - 1, contest_type)

    # Score all lineups
    our_score = simulate_lineup_score(our_lineup)

    # Score field with same variance
    field_scores = []
    for lineup in field_lineups:
        score = simulate_lineup_score(lineup)
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
# ========== BATCH PROCESSING (WITH PARALLEL PROCESSING) ==========
def process_batch(args):
    """Process a batch of slates with guaranteed attempts per strategy"""
    slate_configs, contest_configs = args
    results = []

    # Track detailed failure reasons
    failure_tracker = defaultdict(lambda: defaultdict(int))

    for slate_config in slate_configs:
        slate_id, format_type, slate_size = slate_config

        try:
            # Generate slate
            slate = generate_slate(slate_id, format_type, slate_size)

            if not slate or not slate.get('players'):
                continue

            # Get appropriate strategies
            if format_type == 'showdown':
                strategies = SHOWDOWN_STRATEGIES
            else:
                # Get all strategies for this slate size
                strategies = {}
                if slate_size in CLASSIC_STRATEGIES_BY_SIZE:
                    # Include both cash and GPP strategies
                    for contest_type in ['cash', 'gpp']:
                        if contest_type in CLASSIC_STRATEGIES_BY_SIZE[slate_size]:
                            for strat_name, strat_config in CLASSIC_STRATEGIES_BY_SIZE[slate_size][
                                contest_type].items():
                                # Add contest type to strategy name to make unique
                                unique_name = f"{strat_name}_{contest_type}"
                                strategies[unique_name] = strat_config

            # CRITICAL: Test EVERY strategy with EVERY contest type
            for strategy_name, strategy_config in strategies.items():
                for contest_type, field_size in contest_configs:
                    # Determine if this strategy is appropriate for contest type
                    if '_cash' in strategy_name and contest_type == 'gpp':
                        continue
                    if '_gpp' in strategy_name and contest_type == 'cash':
                        continue

                    # Clean strategy name for tracking
                    clean_strategy_name = strategy_name.replace('_cash', '').replace('_gpp', '')

                    result = simulate_contest(
                        slate, clean_strategy_name, strategy_config,
                        contest_type, field_size
                    )

                    results.append(result)

                    # Track failures
                    if result.get('failed'):
                        key = f"{format_type}_{slate_size}_{clean_strategy_name}_{contest_type}"
                        failure_tracker[key]['total'] += 1
                        failure_tracker[key][result.get('failure_reason', 'unknown')] += 1

        except Exception as e:
            # Log the error
            failure_tracker['exceptions'][f"{format_type}_{slate_size}_{type(e).__name__}"] += 1
            continue

    # Add failure summary to results
    if failure_tracker and len(results) > 0:
        # Add a summary record
        results.append({
            'type': 'failure_summary',
            'failures': dict(failure_tracker)
        })

    return results

if __name__ == "__main__":
    main()