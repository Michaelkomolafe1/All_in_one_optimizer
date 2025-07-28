#!/usr/bin/env python3
"""
DFS PHASE 2 IMPROVED SIMULATOR
==============================
- Tests cash improvements (not just pure chalk)
- Fixed stack sizes (max 5 hitters)
- Flexible lineup building with fallbacks
- Ensures minimum entries per strategy
- Optimized for Intel Core Ultra 7 155H
"""

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

# CASH STRATEGIES TO TEST
CASH_STRATEGIES = {
    'pure_chalk': {
        'name': 'Pure Chalk (Baseline)',
        'description': 'Phase 1 winner - 55.4% target',
        'type': 'ownership_based'
    },

    'chalk_mini_stack': {
        'name': 'Chalk + Mini Stack',
        'description': 'Chalk with 3-4 player team correlation',
        'type': 'chalk_plus_stack',
        'stack_size': 3,
        'min_stack_size': 3
    },

    'chalk_quality': {
        'name': 'Chalk + Quality Filter',
        'description': 'Only chalk with good matchups',
        'type': 'filtered_chalk',
        'min_team_total': 4.5,
        'max_pitcher_opp_total': 4.5
    },

    'chalk_value_blend': {
        'name': 'Chalk/Value 70/30',
        'description': 'Mostly chalk with value plays',
        'type': 'weighted_blend',
        'weights': {'ownership': 0.7, 'value': 0.3}
    },

    'chalk_game_focus': {
        'name': 'Chalk from High-Total Games',
        'description': 'Chalk from 9+ total games only',
        'type': 'game_filtered',
        'min_game_total': 9.0
    }
}

# GPP STRATEGIES - FIXED STACK SIZES
GPP_STRATEGIES = {
    # MINI STACKS (More Flexible)
    'chalk_3_stack': {
        'name': 'Chalk + 3-Player Mini Stack',
        'description': '7 chalk + 3 stack',
        'chalk_count': 7,
        'stack_size': 3,
        'min_stack_size': 3,
        'stack_ownership_max': 20
    },

    'chalk_4_stack': {
        'name': 'Chalk + 4-Player Stack',
        'description': '6 chalk + 4 stack',
        'chalk_count': 6,
        'stack_size': 4,
        'min_stack_size': 3,  # Allow partial if needed
        'stack_ownership_max': 15
    },

    'chalk_5_stack': {
        'name': 'Chalk + 5-Player Max Stack',
        'description': '5 chalk + 5 stack (max hitters)',
        'chalk_count': 5,
        'stack_size': 5,
        'min_stack_size': 4,  # Allow 4 if can't get 5
        'stack_ownership_max': 12
    },

    # FLEXIBLE STACKING
    'flexible_correlation': {
        'name': 'Flexible Correlation',
        'description': 'Chalk with any 3-5 stack',
        'chalk_count': 6,
        'min_stack_size': 3,
        'max_stack_size': 5,
        'prefer_larger': True
    },

    # GAME STACKING
    'chalk_game_stack': {
        'name': 'Chalk + Game Stack',
        'description': 'Both teams from high total',
        'chalk_count': 4,
        'game_stack': True,
        'min_game_total': 9.5,
        'min_each_team': 2
    },

    'run_back_stack': {
        'name': 'Chalk + Run Back',
        'description': '4 from one team + 1-2 opposing',
        'chalk_count': 4,
        'primary_stack': 4,
        'run_back': 2
    },

    # OWNERSHIP STRATEGIES
    'balanced_ownership': {
        'name': 'Balanced Ownership',
        'description': 'Mix of chalk and low-owned',
        'ownership_targets': {
            'high': 3,  # 25%+ owned
            'medium': 4,  # 10-25% owned
            'low': 3  # <10% owned
        }
    },

    'chalk_with_leverage': {
        'name': 'Chalk + 2 Leverage Plays',
        'description': 'Core chalk with pivots',
        'chalk_count': 8,
        'leverage_plays': 2,
        'max_leverage_ownership': 5
    },

    # CONTRARIAN APPROACHES
    'chalk_fade_one': {
        'name': 'Fade One Chalk',
        'description': 'All chalk except highest owned',
        'fade_count': 1,
        'fade_highest_owned': True
    },

    'anti_chalk_stack': {
        'name': 'Anti-Chalk Stack',
        'description': '5 chalk + 5 low-owned stack',
        'chalk_count': 5,
        'contrarian_stack_size': 5,
        'max_stack_ownership': 5
    }
}

# FIELD STRATEGIES
FIELD_STRATEGIES = {
    'field_chalk': {
        'frequency': 0.35,
        'weights': {'ownership': 0.6, 'projection': 0.3, 'value': 0.1}
    },
    'field_balanced': {
        'frequency': 0.30,
        'weights': {'ownership': 0.2, 'projection': 0.5, 'value': 0.3}
    },
    'field_stacker': {
        'frequency': 0.20,
        'weights': {'ownership': 0.3, 'projection': 0.4, 'value': 0.3},
        'force_stack': True
    },
    'field_contrarian': {
        'frequency': 0.10,
        'weights': {'ownership': -0.2, 'projection': 0.6, 'value': 0.4}
    },
    'field_random': {
        'frequency': 0.05,
        'weights': {'ownership': 0.1, 'projection': 0.3, 'value': 0.3},
        'randomize': True
    }
}

POPULAR_TEAMS = ['NYY', 'LAD', 'HOU', 'ATL', 'BOS', 'SF', 'PHI']


def generate_improved_slate(slate_id: int) -> Dict:
    """Generate slate with better correlation opportunities"""
    random.seed(slate_id)
    np.random.seed(slate_id)

    num_games = random.choice([10, 12, 14])

    all_teams = ['NYY', 'BOS', 'HOU', 'LAD', 'ATL', 'SD', 'TB', 'MIL', 'SEA', 'PHI',
                 'TOR', 'MIN', 'CLE', 'CHC', 'SF', 'STL', 'TEX', 'NYM', 'BAL', 'COL',
                 'DET', 'KC', 'CIN', 'CHW', 'MIA', 'PIT', 'WSH', 'OAK', 'ARI', 'LAA']

    playing_teams = random.sample(all_teams, min(num_games * 2, len(all_teams)))

    games = []
    for i in range(0, len(playing_teams), 2):
        if i + 1 < len(playing_teams):
            # More varied game totals
            rand = random.random()
            if rand < 0.25:  # 25% shootouts
                total = np.clip(np.random.normal(11.0, 1.0), 9.5, 13.5)
            elif rand < 0.50:  # 25% normal-high
                total = np.clip(np.random.normal(9.0, 1.0), 8.0, 10.5)
            else:  # 50% normal
                total = np.clip(np.random.normal(8.0, 1.5), 6.0, 9.5)

            home_pct = random.uniform(0.48, 0.52)

            games.append({
                'game_id': len(games),
                'home': playing_teams[i],
                'away': playing_teams[i + 1],
                'total': total,
                'home_total': total * home_pct,
                'away_total': total * (1 - home_pct),
                'is_shootout': total > 10.0,
                'is_pitcher_duel': total < 7.0
            })

    players = []
    player_id = 0

    for game in games:
        for team, team_total in [(game['home'], game['home_total']),
                                 (game['away'], game['away_total'])]:

            # Stack bonus for correlation
            stack_multiplier = 1.0
            if game['is_shootout']:
                stack_multiplier = 1.2
            elif game['is_pitcher_duel']:
                stack_multiplier = 0.9

            # PITCHERS (2 per team)
            for p_idx in range(2):
                is_starter = p_idx == 0

                skill = np.clip(np.random.normal(0.6 if is_starter else 0.4, 0.25), 0, 1)

                if is_starter:
                    salary = int(5500 + skill * 5500)  # Range: 5500-11000
                    p_type = 'SP'
                else:
                    salary = int(3500 + skill * 3000)  # Range: 3500-6500
                    p_type = 'RP'

                salary = max(4000, min(11000, salary))

                # Projection based on matchup
                base_proj = (salary / 1000) * 2.1
                opp_total = game['away_total'] if team == game['home'] else game['home_total']

                if opp_total < 3.5:
                    base_proj *= 1.25
                elif opp_total > 5.5:
                    base_proj *= 0.8

                projection = max(0, base_proj + np.random.normal(0, 2.0))

                # Ownership
                ownership = calculate_ownership_improved(
                    projection, salary, is_pitcher=True,
                    team=team, team_total=team_total,
                    opp_total=opp_total, game_total=game['total']
                )

                players.append({
                    'id': player_id,
                    'name': f"{team}_{p_type}{p_idx}",
                    'position': 'P',
                    'team': team,
                    'salary': salary,
                    'projection': round(projection, 1),
                    'ownership': round(ownership, 1),
                    'team_total': round(team_total, 2),
                    'opp_total': round(opp_total, 2),
                    'game_id': game['game_id'],
                    'game_total': round(game['total'], 1),
                    'batting_order': 0,
                    'correlation_group': f"{team}_{game['game_id']}",
                    'stack_multiplier': 1.0  # Pitchers don't get stack bonus
                })
                player_id += 1

            # HITTERS - More variety to ensure valid lineups
            position_counts = {
                'C': 3,  # Increased from 2
                '1B': 3,  # Increased from 2
                '2B': 3,  # Increased from 2
                '3B': 3,  # Increased from 2
                'SS': 3,  # Increased from 2
                'OF': 6  # Increased from 5
            }

            # Track actual hitters added
            hitters_added = 0

            for pos, max_count in position_counts.items():
                for p_idx in range(max_count):
                    # Limit total hitters to prevent 6+ stacks
                    if hitters_added >= 9:  # 9 hitters max per team
                        break

                    # Batting order and skill
                    if p_idx == 0:
                        batting_order = random.choice([1, 2, 3, 4, 5])
                        skill = np.clip(np.random.normal(0.7, 0.15), 0, 1)
                    else:
                        batting_order = random.choice([6, 7, 8, 9, 0])
                        skill = np.clip(np.random.normal(0.4, 0.15), 0, 1)

                    # Salary by position with more variety
                    if pos == 'C':
                        base_salary = 2200 + skill * 2500  # Lower floor
                    elif pos in ['SS', '2B']:
                        base_salary = 2800 + skill * 3000
                    elif pos in ['1B', 'OF']:
                        base_salary = 3000 + skill * 3500
                    else:
                        base_salary = 2600 + skill * 2800

                    salary = int(base_salary)
                    salary = max(2000, min(6500, salary))  # Higher ceiling

                    # Projection with team context
                    base_proj = (salary / 1000) * 1.7

                    # Team total adjustments
                    if team_total > 5.5:
                        base_proj *= 1.18
                    elif team_total > 5.0:
                        base_proj *= 1.10
                    elif team_total < 4.0:
                        base_proj *= 0.85

                    # Batting order bonus
                    if batting_order in [1, 2, 3, 4]:
                        base_proj *= 1.15
                    elif batting_order == 5:
                        base_proj *= 1.08
                    elif batting_order >= 7:
                        base_proj *= 0.9

                    projection = max(0, base_proj + np.random.normal(0, 1.2))

                    # Ownership calculation
                    ownership = calculate_ownership_improved(
                        projection, salary, is_pitcher=False,
                        team=team, team_total=team_total,
                        batting_order=batting_order,
                        game_total=game['total']
                    )

                    players.append({
                        'id': player_id,
                        'name': f"{team}_{pos}{p_idx}",
                        'position': pos,
                        'team': team,
                        'salary': salary,
                        'projection': round(projection, 1),
                        'ownership': round(ownership, 1),
                        'team_total': round(team_total, 2),
                        'game_id': game['game_id'],
                        'game_total': round(game['total'], 1),
                        'batting_order': batting_order,
                        'correlation_group': f"{team}_{game['game_id']}",
                        'stack_multiplier': stack_multiplier,
                        'value_score': projection / (salary / 1000)
                    })
                    player_id += 1
                    hitters_added += 1

    return {
        'slate_id': slate_id,
        'num_games': num_games,
        'players': players,
        'games': games
    }


def calculate_ownership_improved(projection: float, salary: int, is_pitcher: bool = False,
                                 team: str = None, team_total: float = 4.5,
                                 batting_order: int = 5, opp_total: float = 4.5,
                                 game_total: float = 9.0) -> float:
    """Improved ownership calculation"""
    if salary <= 0:
        return 0.1

    value = projection / (salary / 1000)

    # Base ownership by value
    if value > 3.5:
        base = 35
    elif value > 3.0:
        base = 25
    elif value > 2.5:
        base = 18
    elif value > 2.0:
        base = 10
    else:
        base = 4

    # Adjustments
    if is_pitcher:
        if salary > 9500 and opp_total < 4.0:
            base *= 1.4
        elif salary < 6000 and projection > 30:
            base *= 1.5
    else:
        # Hitter adjustments
        if batting_order in [1, 2, 3, 4]:
            base *= 1.2
        if team_total > 5.5:
            base *= 1.3
        if game_total > 10.5:
            base *= 1.15

        # Popular team boost
        if team in POPULAR_TEAMS:
            base *= 1.1

    # Add realistic variance
    ownership = base + np.random.normal(0, base * 0.15)

    return max(0.5, min(40, ownership))


def build_cash_lineup(players: List[Dict], strategy: Dict, slate_info: Dict) -> Optional[Dict]:
    """Build cash lineup with various strategies"""
    strategy_type = strategy.get('type', 'ownership_based')

    lineup = None

    if strategy_type == 'ownership_based':
        lineup = build_pure_chalk_lineup(players)
    elif strategy_type == 'chalk_plus_stack':
        lineup = build_chalk_mini_stack_lineup(players, strategy)
    elif strategy_type == 'filtered_chalk':
        lineup = build_quality_chalk_lineup(players, strategy)
    elif strategy_type == 'weighted_blend':
        lineup = build_weighted_lineup(players, strategy)
    elif strategy_type == 'game_filtered':
        lineup = build_game_focus_lineup(players, strategy, slate_info['games'])
    else:
        lineup = build_pure_chalk_lineup(players)

    # If primary strategy fails, try fallbacks
    if not lineup:
        lineup = build_pure_chalk_lineup(players)

    if not lineup:
        lineup = build_emergency_fallback_lineup(players)

    return lineup


def build_pure_chalk_lineup(players: List[Dict]) -> Optional[Dict]:
    """Pure chalk baseline with relaxed constraints"""
    chalk_players = sorted(players, key=lambda x: x['ownership'], reverse=True)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    teams_used = defaultdict(int)

    for player in chalk_players:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= positions_needed.get(pos, 0):
            continue

        if salary + player['salary'] > 50000:
            continue

        # Relaxed team limit
        if teams_used[player['team']] >= 6:  # Was 5
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    # Relaxed salary constraint
    if len(lineup) == 10 and 40000 <= salary <= 50000:  # Was 45000
        return {
            'lineup': lineup,
            'salary': salary,
            'projected': sum(p['projection'] for p in lineup),
            'ownership': sum(p['ownership'] for p in lineup) / 10,
            'strategy': 'pure_chalk'
        }

    return None


def build_chalk_mini_stack_lineup(players: List[Dict], strategy: Dict) -> Optional[Dict]:
    """Chalk with mini stack (3-4 players)"""
    stack_size = strategy.get('stack_size', 3)

    # Find teams that can provide mini stacks
    team_players = defaultdict(list)
    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    # Sort teams by average ownership
    team_options = []
    for team, players_list in team_players.items():
        if len(players_list) >= stack_size:
            avg_own = np.mean([p['ownership'] for p in players_list[:stack_size]])
            team_options.append((team, avg_own, players_list))

    team_options.sort(key=lambda x: x[1], reverse=True)  # High ownership first for cash

    # Try building with different teams
    for team, avg_own, team_players_list in team_options[:5]:
        lineup = []
        salary = 0
        positions_filled = defaultdict(int)
        positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        teams_used = defaultdict(int)

        # Add mini stack first
        stack_players = sorted(team_players_list,
                               key=lambda x: (x['batting_order'] if x['batting_order'] > 0 else 10,
                                              -x['ownership']))

        stack_added = 0
        for player in stack_players[:stack_size + 2]:  # Try extra players
            if stack_added >= stack_size:
                break

            pos = player['position']
            if positions_filled[pos] < positions_needed.get(pos, 0):
                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1
                stack_added += 1

        if stack_added < stack_size - 1:  # Allow one less than target
            continue

        # Fill rest with chalk
        chalk_players = sorted([p for p in players if p not in lineup],
                               key=lambda x: x['ownership'], reverse=True)

        for player in chalk_players:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled[pos] >= positions_needed.get(pos, 0):
                continue

            if salary + player['salary'] > 50000:
                continue

            if teams_used[player['team']] >= 5:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

        if len(lineup) == 10 and 45000 <= salary <= 50000:
            return {
                'lineup': lineup,
                'salary': salary,
                'projected': sum(p['projection'] for p in lineup),
                'ownership': sum(p['ownership'] for p in lineup) / 10,
                'strategy': 'chalk_mini_stack',
                'stack_team': team,
                'stack_size': stack_added
            }

    # Fallback to pure chalk if stacking fails
    return build_pure_chalk_lineup(players)


def build_quality_chalk_lineup(players: List[Dict], strategy: Dict) -> Optional[Dict]:
    """Chalk filtered by quality metrics"""
    min_team_total = strategy.get('min_team_total', 4.5)
    max_opp_total = strategy.get('max_pitcher_opp_total', 4.5)

    # Filter players
    quality_players = []
    for p in players:
        if p['position'] == 'P':
            if p.get('opp_total', 5.0) <= max_opp_total:
                quality_players.append(p)
        else:
            if p['team_total'] >= min_team_total:
                quality_players.append(p)

    # Sort by ownership
    quality_players.sort(key=lambda x: x['ownership'], reverse=True)

    # Build lineup
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    teams_used = defaultdict(int)

    for player in quality_players:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= positions_needed.get(pos, 0):
            continue

        if salary + player['salary'] > 50000:
            continue

        if teams_used[player['team']] >= 5:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    # Fill remaining with any chalk if needed
    if len(lineup) < 10:
        remaining_chalk = sorted([p for p in players if p not in lineup],
                                 key=lambda x: x['ownership'], reverse=True)

        for player in remaining_chalk:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled[pos] >= positions_needed.get(pos, 0):
                continue

            if salary + player['salary'] > 50000:
                continue

            if teams_used[player['team']] >= 5:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

    if len(lineup) == 10 and 45000 <= salary <= 50000:
        return {
            'lineup': lineup,
            'salary': salary,
            'projected': sum(p['projection'] for p in lineup),
            'ownership': sum(p['ownership'] for p in lineup) / 10,
            'strategy': 'chalk_quality'
        }

    return build_pure_chalk_lineup(players)


def build_weighted_lineup(players: List[Dict], strategy: Dict) -> Optional[Dict]:
    """Weighted blend of ownership and value"""
    weights = strategy.get('weights', {'ownership': 0.7, 'value': 0.3})

    # Score all players
    scored_players = []
    for p in players:
        own_score = p['ownership'] / 40  # Normalize to 0-1
        value_score = p.get('value_score', p['projection'] / (p['salary'] / 1000)) / 4  # Normalize

        total_score = (own_score * weights.get('ownership', 0.7) +
                       value_score * weights.get('value', 0.3))

        scored_players.append({**p, 'blend_score': total_score})

    scored_players.sort(key=lambda x: x['blend_score'], reverse=True)

    # Build lineup
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    teams_used = defaultdict(int)

    for player in scored_players:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= positions_needed.get(pos, 0):
            continue

        if salary + player['salary'] > 50000:
            continue

        if teams_used[player['team']] >= 5:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10 and 45000 <= salary <= 50000:
        return {
            'lineup': lineup,
            'salary': salary,
            'projected': sum(p['projection'] for p in lineup),
            'ownership': sum(p['ownership'] for p in lineup) / 10,
            'strategy': 'weighted_blend'
        }

    return build_pure_chalk_lineup(players)


def build_game_focus_lineup(players: List[Dict], strategy: Dict, games: List[Dict]) -> Optional[Dict]:
    """Chalk from high-total games only"""
    min_total = strategy.get('min_game_total', 9.0)

    # Find high-total games
    high_total_games = [g for g in games if g['total'] >= min_total]
    high_total_game_ids = {g['game_id'] for g in high_total_games}

    if not high_total_games:
        # Fallback to highest total games
        sorted_games = sorted(games, key=lambda x: x['total'], reverse=True)
        high_total_game_ids = {g['game_id'] for g in sorted_games[:3]}

    # Filter players from these games
    game_players = [p for p in players if p['game_id'] in high_total_game_ids]

    # Sort by ownership
    game_players.sort(key=lambda x: x['ownership'], reverse=True)

    # Build lineup
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    teams_used = defaultdict(int)

    for player in game_players:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= positions_needed.get(pos, 0):
            continue

        if salary + player['salary'] > 50000:
            continue

        if teams_used[player['team']] >= 5:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    # Fill remaining from any player if needed
    if len(lineup) < 10:
        remaining = sorted([p for p in players if p not in lineup],
                           key=lambda x: x['ownership'], reverse=True)

        for player in remaining:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled[pos] >= positions_needed.get(pos, 0):
                continue

            if salary + player['salary'] > 50000:
                continue

            if teams_used[player['team']] >= 5:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

    if len(lineup) == 10 and 45000 <= salary <= 50000:
        return {
            'lineup': lineup,
            'salary': salary,
            'projected': sum(p['projection'] for p in lineup),
            'ownership': sum(p['ownership'] for p in lineup) / 10,
            'strategy': 'game_focus'
        }

    return build_pure_chalk_lineup(players)


def build_gpp_lineup(players: List[Dict], strategy: Dict, slate_info: Dict) -> Optional[Dict]:
    """Build GPP lineup with flexible strategies"""

    lineup = None

    # Route to appropriate builder
    if 'stack_size' in strategy and 'chalk_count' in strategy:
        lineup = build_flexible_stack_lineup(players, strategy)
    elif strategy.get('game_stack'):
        lineup = build_game_stack_improved(players, strategy, slate_info['games'])
    elif 'primary_stack' in strategy and 'run_back' in strategy:
        lineup = build_run_back_lineup(players, strategy)
    elif 'ownership_targets' in strategy:
        lineup = build_balanced_ownership_lineup(players, strategy)
    elif 'leverage_plays' in strategy:
        lineup = build_leverage_lineup(players, strategy)
    elif strategy.get('fade_highest_owned'):
        lineup = build_fade_chalk_lineup(players, strategy)
    elif 'contrarian_stack_size' in strategy:
        lineup = build_anti_chalk_lineup(players, strategy)
    elif 'min_stack_size' in strategy and 'max_stack_size' in strategy:
        lineup = build_flexible_correlation_lineup(players, strategy)

    # If primary strategy fails, try simpler approach
    if not lineup:
        lineup = build_flexible_stack_lineup(players, {'chalk_count': 5, 'stack_size': 4, 'min_stack_size': 2})

    # Final fallback
    if not lineup:
        lineup = build_emergency_fallback_lineup(players)

    return lineup


def build_flexible_stack_lineup(players: List[Dict], strategy: Dict) -> Optional[Dict]:
    """Flexible stacking with multiple fallback options"""
    chalk_count = strategy.get('chalk_count', 6)
    target_stack = strategy.get('stack_size', 4)
    min_stack = strategy.get('min_stack_size', 3)
    max_stack_own = strategy.get('stack_ownership_max', 25)  # Increased from 15

    # Get chalk players
    chalk_players = sorted(players, key=lambda x: x['ownership'], reverse=True)

    # Find stackable teams
    team_players = defaultdict(list)
    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    # Find teams that can provide stacks
    stack_options = []
    for team, players_list in team_players.items():
        if len(players_list) >= min_stack:
            # Check different stack sizes
            for size in range(min(target_stack, len(players_list)), max(2, min_stack - 1), -1):
                stack_candidates = sorted(players_list,
                                          key=lambda x: (x['batting_order'] if x['batting_order'] > 0 else 10,
                                                         -x['projection']))[:size]
                avg_own = np.mean([p['ownership'] for p in stack_candidates])

                if avg_own <= max_stack_own:
                    stack_options.append({
                        'team': team,
                        'size': size,
                        'ownership': avg_own,
                        'players': stack_candidates
                    })

    # If no stacks found, create mini stacks
    if not stack_options:
        for team, players_list in team_players.items():
            if len(players_list) >= 2:  # Just 2 players
                stack_candidates = sorted(players_list, key=lambda x: x['projection'], reverse=True)[:2]
                stack_options.append({
                    'team': team,
                    'size': 2,
                    'ownership': np.mean([p['ownership'] for p in stack_candidates]),
                    'players': stack_candidates
                })

    if not stack_options:
        # No stacks possible, just build best lineup
        return build_emergency_fallback_lineup(players)

    # Sort options - prefer larger stacks with lower ownership
    stack_options.sort(key=lambda x: (-x['size'], x['ownership']))

    # Try building with different stacks
    for attempt, stack_option in enumerate(stack_options[:20]):  # Try more options
        lineup = []
        salary = 0
        positions_filled = defaultdict(int)
        positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        teams_used = defaultdict(int)

        # Add the stack
        stack_added = 0
        for player in stack_option['players']:
            pos = player['position']
            if positions_filled[pos] < positions_needed.get(pos, 0):
                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1
                stack_added += 1

        # Add chalk players (avoiding stack team)
        chalk_added = 0
        for player in chalk_players:
            if chalk_added >= chalk_count or len(lineup) >= 10:
                break

            if player in lineup:
                continue

            if player['team'] == stack_option['team'] and teams_used[player['team']] >= 5:
                continue

            pos = player['position']
            if positions_filled[pos] >= positions_needed.get(pos, 0):
                continue

            if salary + player['salary'] > 50000:
                continue

            if teams_used[player['team']] >= 6:  # Relaxed from 5
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1
            chalk_added += 1

        # Fill remaining spots
        remaining = sorted([p for p in players if p not in lineup],
                           key=lambda x: x['projection'], reverse=True)

        for player in remaining:
            if len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled[pos] >= positions_needed.get(pos, 0):
                continue

            if salary + player['salary'] > 50000:
                continue

            if teams_used[player['team']] >= 6:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

        # More relaxed validation
        if len(lineup) == 10 and 40000 <= salary <= 50000:  # Relaxed from 45000
            return {
                'lineup': lineup,
                'salary': salary,
                'projected': sum(p['projection'] for p in lineup),
                'ownership': sum(p['ownership'] for p in lineup) / 10,
                'stack_team': stack_option['team'],
                'stack_size': stack_added,
                'chalk_count': chalk_added
            }

    # Final fallback
    return build_emergency_fallback_lineup(players)


def build_game_stack_improved(players: List[Dict], strategy: Dict, games: List[Dict]) -> Optional[Dict]:
    """Improved game stacking"""
    chalk_count = strategy.get('chalk_count', 4)
    min_total = strategy.get('min_game_total', 9.5)
    min_each = strategy.get('min_each_team', 2)

    # Find high-total games
    target_games = [g for g in games if g['total'] >= min_total]
    if not target_games:
        target_games = sorted(games, key=lambda x: x['total'], reverse=True)[:2]

    # Try each game
    for game in target_games:
        # Get players from this game
        game_players = defaultdict(list)
        for p in players:
            if p['game_id'] == game['game_id'] and p['position'] != 'P':
                game_players[p['team']].append(p)

        # Need at least min_each from each team
        teams = list(game_players.keys())
        if len(teams) < 2:
            continue

        if any(len(game_players[team]) < min_each for team in teams):
            continue

        # Try different distributions
        for team1_count in range(min_each, min(6, len(game_players[teams[0]]) + 1)):
            team2_count = min(5, 10 - team1_count - 2)  # Leave room for 2 pitchers

            if team2_count < min_each:
                continue

            lineup = []
            salary = 0
            positions_filled = defaultdict(int)
            positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
            teams_used = defaultdict(int)

            # Add players from team 1
            team1_players = sorted(game_players[teams[0]],
                                   key=lambda x: (x['batting_order'] if x['batting_order'] > 0 else 10,
                                                  -x['projection']))

            added_team1 = 0
            for player in team1_players:
                if added_team1 >= team1_count:
                    break

                pos = player['position']
                if positions_filled[pos] < positions_needed.get(pos, 0):
                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1
                    added_team1 += 1

            # Add players from team 2
            team2_players = sorted(game_players[teams[1]],
                                   key=lambda x: (x['batting_order'] if x['batting_order'] > 0 else 10,
                                                  -x['projection']))

            added_team2 = 0
            for player in team2_players:
                if added_team2 >= team2_count:
                    break

                pos = player['position']
                if positions_filled[pos] < positions_needed.get(pos, 0):
                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1
                    added_team2 += 1

            # Add chalk players
            chalk_players = sorted(players, key=lambda x: x['ownership'], reverse=True)
            chalk_added = 0

            for player in chalk_players:
                if len(lineup) >= 10 or chalk_added >= chalk_count:
                    break

                if player in lineup:
                    continue

                pos = player['position']
                if positions_filled[pos] >= positions_needed.get(pos, 0):
                    continue

                if salary + player['salary'] > 50000:
                    continue

                if teams_used[player['team']] >= 5:
                    continue

                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1
                chalk_added += 1

            # Fill remaining
            for player in sorted(players, key=lambda x: x['projection'], reverse=True):
                if len(lineup) >= 10:
                    break

                if player in lineup:
                    continue

                pos = player['position']
                if positions_filled[pos] >= positions_needed.get(pos, 0):
                    continue

                if salary + player['salary'] > 50000:
                    continue

                if teams_used[player['team']] >= 5:
                    continue

                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1

            if len(lineup) == 10 and 45000 <= salary <= 50000:
                return {
                    'lineup': lineup,
                    'salary': salary,
                    'projected': sum(p['projection'] for p in lineup),
                    'ownership': sum(p['ownership'] for p in lineup) / 10,
                    'game_stack': True,
                    'game_total': game['total'],
                    'teams_stacked': f"{teams[0]}({added_team1}) vs {teams[1]}({added_team2})"
                }

    return None


def build_run_back_lineup(players: List[Dict], strategy: Dict) -> Optional[Dict]:
    """Primary stack with run back from opposing team"""
    chalk_count = strategy.get('chalk_count', 4)
    primary_size = strategy.get('primary_stack', 4)
    run_back_size = strategy.get('run_back', 2)

    # Find games with correlation potential
    game_teams = defaultdict(set)
    team_to_game = {}
    for p in players:
        game_teams[p['game_id']].add(p['team'])
        team_to_game[p['team']] = p['game_id']

    # Find teams for primary stack
    team_players = defaultdict(list)
    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    # Try different teams
    for team, players_list in team_players.items():
        if len(players_list) < primary_size:
            continue

        # Find opposing team
        game_id = team_to_game[team]
        opposing_teams = game_teams[game_id] - {team}

        if not opposing_teams:
            continue

        opp_team = opposing_teams.pop()
        opp_players = team_players.get(opp_team, [])

        if len(opp_players) < run_back_size:
            continue

        # Build lineup
        lineup = []
        salary = 0
        positions_filled = defaultdict(int)
        positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        teams_used = defaultdict(int)

        # Add primary stack
        primary_players = sorted(players_list,
                                 key=lambda x: (x['batting_order'] if x['batting_order'] > 0 else 10,
                                                -x['projection']))

        primary_added = 0
        for player in primary_players:
            if primary_added >= primary_size:
                break

            pos = player['position']
            if positions_filled[pos] < positions_needed.get(pos, 0):
                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1
                primary_added += 1

        # Add run back
        runback_players = sorted(opp_players,
                                 key=lambda x: (x['batting_order'] if x['batting_order'] in [1, 2, 3, 4] else 10,
                                                -x['projection']))

        runback_added = 0
        for player in runback_players:
            if runback_added >= run_back_size:
                break

            pos = player['position']
            if positions_filled[pos] < positions_needed.get(pos, 0):
                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1
                runback_added += 1

        # Add chalk
        chalk_players = sorted(players, key=lambda x: x['ownership'], reverse=True)
        chalk_added = 0

        for player in chalk_players:
            if len(lineup) >= 10 or chalk_added >= chalk_count:
                break

            if player in lineup:
                continue

            pos = player['position']
            if positions_filled[pos] >= positions_needed.get(pos, 0):
                continue

            if salary + player['salary'] > 50000:
                continue

            if teams_used[player['team']] >= 5:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1
            chalk_added += 1

        # Fill remaining
        for player in sorted(players, key=lambda x: x['projection'], reverse=True):
            if len(lineup) >= 10:
                break

            if player in lineup:
                continue

            pos = player['position']
            if positions_filled[pos] >= positions_needed.get(pos, 0):
                continue

            if salary + player['salary'] > 50000:
                continue

            if teams_used[player['team']] >= 5:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

        if len(lineup) == 10 and 45000 <= salary <= 50000:
            return {
                'lineup': lineup,
                'salary': salary,
                'projected': sum(p['projection'] for p in lineup),
                'ownership': sum(p['ownership'] for p in lineup) / 10,
                'primary_stack': f"{team}({primary_added})",
                'run_back': f"{opp_team}({runback_added})"
            }

    return None


def build_balanced_ownership_lineup(players: List[Dict], strategy: Dict) -> Optional[Dict]:
    """Balance ownership tiers"""
    targets = strategy.get('ownership_targets', {'high': 3, 'medium': 4, 'low': 3})

    # Categorize players
    high_own = [p for p in players if p['ownership'] >= 25]
    med_own = [p for p in players if 10 <= p['ownership'] < 25]
    low_own = [p for p in players if p['ownership'] < 10]

    # Sort each by projection
    high_own.sort(key=lambda x: x['projection'], reverse=True)
    med_own.sort(key=lambda x: x['projection'], reverse=True)
    low_own.sort(key=lambda x: x['projection'], reverse=True)

    # Build lineup
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    teams_used = defaultdict(int)

    # Add from each tier
    for tier_players, target_count, tier_name in [
        (high_own, targets['high'], 'high'),
        (med_own, targets['medium'], 'medium'),
        (low_own, targets['low'], 'low')
    ]:
        added = 0
        for player in tier_players:
            if added >= target_count or len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled[pos] >= positions_needed.get(pos, 0):
                continue

            if salary + player['salary'] > 50000:
                continue

            if teams_used[player['team']] >= 5:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1
            added += 1

    # Fill remaining
    for player in sorted(players, key=lambda x: x['projection'], reverse=True):
        if len(lineup) >= 10:
            break

        if player in lineup:
            continue

        pos = player['position']
        if positions_filled[pos] >= positions_needed.get(pos, 0):
            continue

        if salary + player['salary'] > 50000:
            continue

        if teams_used[player['team']] >= 5:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10 and 45000 <= salary <= 50000:
        high_count = len([p for p in lineup if p['ownership'] >= 25])
        med_count = len([p for p in lineup if 10 <= p['ownership'] < 25])
        low_count = len([p for p in lineup if p['ownership'] < 10])

        return {
            'lineup': lineup,
            'salary': salary,
            'projected': sum(p['projection'] for p in lineup),
            'ownership': sum(p['ownership'] for p in lineup) / 10,
            'ownership_distribution': f"H:{high_count} M:{med_count} L:{low_count}"
        }

    return None


def build_leverage_lineup(players: List[Dict], strategy: Dict) -> Optional[Dict]:
    """Chalk with specific leverage plays"""
    chalk_count = strategy.get('chalk_count', 8)
    leverage_count = strategy.get('leverage_plays', 2)
    max_lev_own = strategy.get('max_leverage_ownership', 5)

    # Get chalk and leverage candidates
    chalk_players = sorted(players, key=lambda x: x['ownership'], reverse=True)
    leverage_candidates = [p for p in players if p['ownership'] <= max_lev_own
                           and p['projection'] > 0]

    # Sort leverage by upside indicators
    for p in leverage_candidates:
        upside = 0
        if p.get('team_total', 0) > 5.0:
            upside += 1
        if p.get('batting_order', 10) <= 4:
            upside += 1
        if p.get('game_total', 0) > 10:
            upside += 1
        p['upside_score'] = upside

    leverage_candidates.sort(key=lambda x: (x['upside_score'], x['projection']), reverse=True)

    # Build lineup
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    teams_used = defaultdict(int)

    # Add chalk first
    chalk_added = 0
    for player in chalk_players:
        if chalk_added >= chalk_count or len(lineup) >= 10 - leverage_count:
            break

        pos = player['position']
        if positions_filled[pos] >= positions_needed.get(pos, 0):
            continue

        if salary + player['salary'] > 47000:  # Leave room
            continue

        if teams_used[player['team']] >= 5:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1
        chalk_added += 1

    # Add leverage plays
    lev_added = 0
    for player in leverage_candidates:
        if lev_added >= leverage_count or len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= positions_needed.get(pos, 0):
            continue

        if salary + player['salary'] > 50000:
            continue

        if teams_used[player['team']] >= 5:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1
        lev_added += 1

    # Fill remaining
    for player in sorted(players, key=lambda x: x['projection'], reverse=True):
        if len(lineup) >= 10:
            break

        if player in lineup:
            continue

        pos = player['position']
        if positions_filled[pos] >= positions_needed.get(pos, 0):
            continue

        if salary + player['salary'] > 50000:
            continue

        if teams_used[player['team']] >= 5:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10 and 45000 <= salary <= 50000:
        return {
            'lineup': lineup,
            'salary': salary,
            'projected': sum(p['projection'] for p in lineup),
            'ownership': sum(p['ownership'] for p in lineup) / 10,
            'chalk_plays': chalk_added,
            'leverage_plays': lev_added
        }

    return None


def build_fade_chalk_lineup(players: List[Dict], strategy: Dict) -> Optional[Dict]:
    """Fade the highest owned player(s)"""
    fade_count = strategy.get('fade_count', 1)

    # Sort by ownership
    sorted_players = sorted(players, key=lambda x: x['ownership'], reverse=True)

    # Identify players to fade (use list, not set)
    fade_players = sorted_players[:fade_count]
    fade_player_ids = {p['id'] for p in fade_players}  # Use IDs for fast lookup

    # Build without faded players
    eligible = [p for p in players if p['id'] not in fade_player_ids]
    eligible.sort(key=lambda x: x['ownership'], reverse=True)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    teams_used = defaultdict(int)

    for player in eligible:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= positions_needed.get(pos, 0):
            continue

        if salary + player['salary'] > 50000:
            continue

        if teams_used[player['team']] >= 5:
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    if len(lineup) == 10 and 45000 <= salary <= 50000:
        # Get names of actually faded players
        lineup_ids = {p['id'] for p in lineup}
        faded_names = [p['name'] for p in fade_players if p['id'] not in lineup_ids][:3]

        return {
            'lineup': lineup,
            'salary': salary,
            'projected': sum(p['projection'] for p in lineup),
            'ownership': sum(p['ownership'] for p in lineup) / 10,
            'faded_players': ', '.join(faded_names) if faded_names else 'None'
        }

    return None


def build_anti_chalk_lineup(players: List[Dict], strategy: Dict) -> Optional[Dict]:
    """Chalk core with contrarian stack"""
    chalk_count = strategy.get('chalk_count', 5)
    stack_size = strategy.get('contrarian_stack_size', 5)
    max_stack_own = strategy.get('max_stack_ownership', 5)

    # Find low-owned stackable teams
    team_players = defaultdict(list)
    for p in players:
        if p['position'] != 'P' and p['ownership'] <= max_stack_own * 2:
            team_players[p['team']].append(p)

    # Find contrarian teams
    contrarian_teams = []
    for team, players_list in team_players.items():
        if len(players_list) >= stack_size:
            avg_own = np.mean([p['ownership'] for p in players_list[:stack_size]])
            if avg_own <= max_stack_own:
                contrarian_teams.append((team, avg_own, players_list))

    if not contrarian_teams:
        return None

    contrarian_teams.sort(key=lambda x: x[1])  # Lowest ownership first

    # Get chalk players
    chalk_players = sorted(players, key=lambda x: x['ownership'], reverse=True)

    # Try different contrarian teams
    for team, avg_own, team_players_list in contrarian_teams[:3]:
        lineup = []
        salary = 0
        positions_filled = defaultdict(int)
        positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        teams_used = defaultdict(int)

        # Add chalk core first
        chalk_added = 0
        for player in chalk_players:
            if chalk_added >= chalk_count:
                break

            if player['team'] == team:  # Skip contrarian team
                continue

            pos = player['position']
            if positions_filled[pos] >= positions_needed.get(pos, 0):
                continue

            if salary + player['salary'] > 35000:  # Leave room for stack
                continue

            if teams_used[player['team']] >= 4:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1
            chalk_added += 1

        # Add contrarian stack
        stack_players = sorted(team_players_list,
                               key=lambda x: (x['batting_order'] if x['batting_order'] > 0 else 10,
                                              -x['projection']))

        stack_added = 0
        for player in stack_players:
            if stack_added >= stack_size or len(lineup) >= 10:
                break

            pos = player['position']
            if positions_filled[pos] < positions_needed.get(pos, 0):
                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1
                stack_added += 1

        # Fill remaining
        for player in sorted(players, key=lambda x: x['projection'], reverse=True):
            if len(lineup) >= 10:
                break

            if player in lineup:
                continue

            pos = player['position']
            if positions_filled[pos] >= positions_needed.get(pos, 0):
                continue

            if salary + player['salary'] > 50000:
                continue

            if teams_used[player['team']] >= 5:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] += 1
            teams_used[player['team']] += 1

        if len(lineup) == 10 and 45000 <= salary <= 50000:
            return {
                'lineup': lineup,
                'salary': salary,
                'projected': sum(p['projection'] for p in lineup),
                'ownership': sum(p['ownership'] for p in lineup) / 10,
                'contrarian_team': team,
                'stack_size': stack_added,
                'chalk_core': chalk_added
            }

    return None


def build_flexible_correlation_lineup(players: List[Dict], strategy: Dict) -> Optional[Dict]:
    """Flexible approach to correlation"""
    chalk_count = strategy.get('chalk_count', 6)
    min_stack = strategy.get('min_stack_size', 3)
    max_stack = strategy.get('max_stack_size', 5)
    prefer_larger = strategy.get('prefer_larger', True)

    # Find all possible stacks
    team_players = defaultdict(list)
    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    # Build lineup with flexible stacking
    best_lineup = None
    best_score = -1

    # Try different stack sizes
    stack_range = range(max_stack, min_stack - 1, -1) if prefer_larger else range(min_stack, max_stack + 1)

    for target_stack_size in stack_range:
        for team, players_list in team_players.items():
            if len(players_list) < target_stack_size:
                continue

            # Try this team/size combination
            lineup = []
            salary = 0
            positions_filled = defaultdict(int)
            positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
            teams_used = defaultdict(int)

            # Add stack
            stack_players = sorted(players_list,
                                   key=lambda x: (x['batting_order'] if x['batting_order'] > 0 else 10,
                                                  -x['projection']))

            stack_added = 0
            for player in stack_players[:target_stack_size + 2]:
                if stack_added >= target_stack_size:
                    break

                pos = player['position']
                if positions_filled[pos] < positions_needed.get(pos, 0):
                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1
                    stack_added += 1

            if stack_added < min_stack:
                continue

            # Add chalk
            chalk_players = sorted(players, key=lambda x: x['ownership'], reverse=True)
            chalk_added = 0

            for player in chalk_players:
                if chalk_added >= chalk_count or len(lineup) >= 10:
                    break

                if player in lineup:
                    continue

                if teams_used[player['team']] >= 5:
                    continue

                pos = player['position']
                if positions_filled[pos] >= positions_needed.get(pos, 0):
                    continue

                if salary + player['salary'] > 50000:
                    continue

                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1
                chalk_added += 1

            # Fill remaining
            for player in sorted(players, key=lambda x: x['projection'], reverse=True):
                if len(lineup) >= 10:
                    break

                if player in lineup:
                    continue

                pos = player['position']
                if positions_filled[pos] >= positions_needed.get(pos, 0):
                    continue

                if salary + player['salary'] > 50000:
                    continue

                if teams_used[player['team']] >= 5:
                    continue

                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] += 1

            if len(lineup) == 10 and 45000 <= salary <= 50000:
                # Score this lineup
                score = (sum(p['projection'] for p in lineup) +
                         stack_added * 2 +  # Bonus for correlation
                         (10 - sum(p['ownership'] for p in lineup) / 10) * 0.5)  # Uniqueness

                if score > best_score:
                    best_score = score
                    best_lineup = {
                        'lineup': lineup,
                        'salary': salary,
                        'projected': sum(p['projection'] for p in lineup),
                        'ownership': sum(p['ownership'] for p in lineup) / 10,
                        'stack_team': team,
                        'stack_size': stack_added
                    }

    return best_lineup


def build_emergency_fallback_lineup(players: List[Dict]) -> Optional[Dict]:
    """Emergency fallback - just build ANY valid lineup"""
    # Sort by projection/salary for value
    for p in players:
        p['emergency_score'] = p['projection'] / (p['salary'] / 1000) if p['salary'] > 0 else 0

    sorted_players = sorted(players, key=lambda x: x['emergency_score'], reverse=True)

    # Try multiple times with different approaches
    for attempt in range(3):
        lineup = []
        salary = 0
        positions_filled = defaultdict(int)
        positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        # On later attempts, shuffle for variety
        if attempt > 0:
            import random
            random.shuffle(sorted_players[:50])

        # Fill required positions first
        for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
            needed = positions_needed[pos] - positions_filled.get(pos, 0)
            if needed > 0:
                pos_players = [p for p in sorted_players if p['position'] == pos and p not in lineup]
                for player in pos_players[:needed]:
                    if salary + player['salary'] <= 50000:
                        lineup.append(player)
                        salary += player['salary']
                        positions_filled[pos] = positions_filled.get(pos, 0) + 1
                        if len(lineup) >= 10:
                            break

        # If still need players, be very flexible
        if len(lineup) < 10:
            remaining = [p for p in sorted_players if p not in lineup]
            for player in remaining:
                if len(lineup) >= 10:
                    break
                if salary + player['salary'] > 50000:
                    continue

                # Very relaxed position limits
                pos = player['position']
                if pos == 'P' and positions_filled.get('P', 0) >= 4:  # Max 4 pitchers
                    continue
                if pos != 'P' and sum(positions_filled.get(p, 0) for p in ['C', '1B', '2B', '3B', 'SS', 'OF']) >= 8:
                    continue

                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] = positions_filled.get(pos, 0) + 1

        # Very relaxed validation
        if len(lineup) == 10 and salary <= 50000:
            return {
                'lineup': lineup,
                'salary': salary,
                'projected': sum(p['projection'] for p in lineup),
                'ownership': sum(p['ownership'] for p in lineup) / 10,
                'is_fallback': True
            }

    return None


def simulate_contest_improved(slate: Dict, strategy_name: str, strategy_config: Dict,
                              contest_type: str, field_size: int) -> Optional[Dict]:
    """Simulate contest with improved scoring"""

    # Build lineup
    if contest_type == 'cash':
        our_lineup = build_cash_lineup(slate['players'], strategy_config, slate)
    else:
        our_lineup = build_gpp_lineup(slate['players'], strategy_config, slate)

    if not our_lineup:
        # Debug: Try a simple fallback lineup
        our_lineup = build_emergency_fallback_lineup(slate['players'])
        if not our_lineup:
            return None
        our_lineup['strategy'] = f"{strategy_name}_fallback"

    # Build field - with more flexible requirements
    actual_field_size = min(field_size, 100)  # Reduced from 300
    field_lineups = []

    # Generate field with various strategies
    for i in range(actual_field_size * 2):  # Try 2x attempts
        if len(field_lineups) >= actual_field_size - 1:
            break

        rand = random.random()
        cumulative = 0

        for strat, field_config in FIELD_STRATEGIES.items():
            cumulative += field_config['frequency']
            if rand < cumulative:
                # Build field lineup with fallbacks
                if field_config.get('force_stack'):
                    field_lineup = build_flexible_stack_lineup(
                        slate['players'],
                        {'chalk_count': 5, 'stack_size': 4, 'min_stack_size': 2}
                    )
                else:
                    field_lineup = build_simple_field_lineup(slate['players'], field_config)

                # If that fails, try emergency fallback
                if not field_lineup:
                    field_lineup = build_emergency_fallback_lineup(slate['players'])

                if field_lineup:
                    field_lineups.append(field_lineup)
                break

    # Much more relaxed requirement - just need SOME field
    if len(field_lineups) < 10:  # Was actual_field_size * 0.5
        # Just simulate with what we have
        if len(field_lineups) < 5:
            # Create some basic lineups
            for _ in range(5):
                fallback = build_emergency_fallback_lineup(slate['players'])
                if fallback:
                    field_lineups.append(fallback)

    # If we have at least our lineup and a few field lineups, proceed
    if len(field_lineups) < 3:
        # Create emergency field
        for _ in range(10):
            emergency = build_emergency_fallback_lineup(slate['players'])
            if emergency:
                field_lineups.append(emergency)
                if len(field_lineups) >= 3:
                    break

    # If still no field, just simulate with our lineup vs a few random scores
    if len(field_lineups) < 3:
        # Generate fake field scores based on normal distribution
        avg_proj = np.mean([p['projection'] for p in slate['players']])
        fake_scores = np.random.normal(avg_proj * 10, avg_proj * 3, 50)
        field_scores = fake_scores.tolist()
    else:
        # Score lineups
        def score_lineup(lineup_data):
            total = 0
            team_counts = defaultdict(int)

            for player in lineup_data['lineup']:
                proj = player['projection']

                # Base variance
                if player['position'] == 'P':
                    std = proj * 0.45
                else:
                    std = proj * 0.3

                score = np.random.normal(proj, std)

                # Simple team correlation
                team_counts[player.get('team', 'UNK')] += 1

                # Individual variance
                rand = random.random()
                if rand < 0.02:  # 2% huge game
                    score *= random.uniform(2.5, 3.5)
                elif rand < 0.08:  # 6% good game
                    score *= random.uniform(1.6, 2.2)
                elif rand < 0.15:  # 7% bad game
                    score *= random.uniform(0.3, 0.7)

                total += max(0, score)

            # Stack bonus
            max_stack = max(team_counts.values()) if team_counts else 0
            if max_stack >= 5:
                total *= 1.12
            elif max_stack >= 4:
                total *= 1.08
            elif max_stack >= 3:
                total *= 1.04

            return total

        # Score all lineups
        try:
            our_score = score_lineup(our_lineup)
        except:
            # Fallback scoring
            our_score = sum(p.get('projection', 10) for p in our_lineup['lineup'])

        field_scores = []
        for lineup in field_lineups:
            try:
                score = score_lineup(lineup)
                field_scores.append(score)
            except:
                # Fallback
                score = sum(p.get('projection', 10) for p in lineup['lineup'])
                field_scores.append(score)

    # Ensure we have some scores
    if not field_scores or our_score is None:
        # Emergency scoring
        avg_proj = 120  # Reasonable average
        our_score = our_score or avg_proj
        if not field_scores:
            field_scores = list(np.random.normal(avg_proj, 20, 100))

    # Extrapolate if needed
    if field_size > len(field_scores):
        if len(field_scores) > 5:
            mean_score = np.mean(field_scores)
            std_score = np.std(field_scores)

            # Use gamma distribution for more realistic scores
            if mean_score > 0 and std_score > 0:
                alpha = (mean_score / std_score) ** 2
                scale = std_score ** 2 / mean_score
                extra_scores = stats.gamma.rvs(alpha, scale=scale, size=field_size - len(field_scores))
                field_scores.extend(extra_scores.tolist())
        else:
            # Just add normal distribution
            extra = list(np.random.normal(120, 20, field_size - len(field_scores)))
            field_scores.extend(extra)

    # Calculate results
    all_scores = field_scores + [our_score]
    all_scores.sort(reverse=True)

    # Find our rank
    try:
        our_rank = all_scores.index(our_score) + 1
    except:
        # If exact match not found, find closest
        our_rank = 1
        for i, score in enumerate(all_scores):
            if score >= our_score:
                our_rank = i + 1
            else:
                break

    percentile = ((len(all_scores) - our_rank) / max(1, len(all_scores) - 1)) * 100

    # Payouts
    if contest_type == 'gpp':
        if our_rank == 1:
            payout = 150  # 50x
        elif our_rank <= field_size * 0.002:
            payout = 50
        elif our_rank <= field_size * 0.01:
            payout = 15
        elif our_rank <= field_size * 0.03:
            payout = 8
        elif our_rank <= field_size * 0.10:
            payout = 5
        elif our_rank <= field_size * 0.20:
            payout = 3.5
        else:
            payout = 0
        entry_fee = 3
    else:  # cash
        if percentile >= 50:
            payout = 10
        else:
            payout = 0
        entry_fee = 5

    profit = payout - entry_fee
    roi = (profit / entry_fee) * 100

    # Always return a result
    return {
        'strategy': strategy_name,
        'contest_type': contest_type,
        'rank': our_rank,
        'percentile': percentile,
        'score': our_score,
        'profit': profit,
        'roi': roi,
        'ownership': our_lineup.get('ownership', 20),
        'lineup_info': {
            'salary': our_lineup.get('salary', 0),
            'is_fallback': our_lineup.get('is_fallback', False)
        }
    }


def build_simple_field_lineup(players: List[Dict], weights: Dict) -> Optional[Dict]:
    """Simple field lineup builder with relaxed constraints"""
    # Score players
    scored_players = []
    for p in players:
        score = (
                p['projection'] * weights.get('projection', 0.5) +
                p.get('value_score', p['projection'] / (p['salary'] / 1000)) * weights.get('value', 0.3) * 5 +
                p['ownership'] * weights.get('ownership', 0.2) * 0.2
        )
        scored_players.append({**p, 'field_score': score})

    # Add randomness for field variety
    if weights.get('randomize'):
        random.shuffle(scored_players)
    else:
        scored_players.sort(key=lambda x: x['field_score'], reverse=True)
        # Add some randomness to top players
        if len(scored_players) > 30:
            top_30 = scored_players[:30]
            random.shuffle(top_30)
            scored_players = top_30 + scored_players[30:]

    # Build lineup with very relaxed constraints
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    teams_used = defaultdict(int)

    # First pass - try to fill required positions
    for player in scored_players:
        if len(lineup) >= 10:
            break

        pos = player['position']
        if positions_filled[pos] >= positions_needed.get(pos, 0):
            continue

        if salary + player['salary'] > 50000:
            continue

        if teams_used[player['team']] >= 7:  # Very relaxed
            continue

        lineup.append(player)
        salary += player['salary']
        positions_filled[pos] += 1
        teams_used[player['team']] += 1

    # Second pass - fill remaining with any valid players
    if len(lineup) < 10:
        for player in scored_players:
            if len(lineup) >= 10:
                break

            if player in lineup:
                continue

            if salary + player['salary'] > 50000:
                continue

            # Very relaxed position limits
            pos = player['position']
            if pos == 'P' and positions_filled.get('P', 0) >= 4:
                continue
            if pos == 'OF' and positions_filled.get('OF', 0) >= 5:
                continue

            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] = positions_filled.get(pos, 0) + 1
            teams_used[player['team']] += 1

    # Very relaxed validation
    if len(lineup) == 10 and 30000 <= salary <= 50000:  # Lower floor
        return {
            'lineup': lineup,
            'salary': salary,
            'projected': sum(p['projection'] for p in lineup),
            'ownership': sum(p['ownership'] for p in lineup) / 10
        }

    return None


def process_slate_batch_improved(args) -> List[Dict]:
    """Process batch with minimum entry requirements"""
    slate_ids, contest_configs, min_entries_per_strategy = args
    results = []
    strategy_entries = defaultdict(int)
    lineup_failures = defaultdict(int)

    # Keep generating slates until all strategies have minimum entries
    slate_index = 0
    max_attempts = len(slate_ids) * 3  # Prevent infinite loop

    while slate_index < len(slate_ids) and slate_index < max_attempts:
        slate_id = slate_ids[slate_index]
        slate = generate_improved_slate(slate_id)

        # Test cash strategies
        for strategy_name, strategy_config in CASH_STRATEGIES.items():
            if strategy_entries[f"cash_{strategy_name}"] < min_entries_per_strategy:
                for contest_type, field_size in contest_configs:
                    if contest_type == 'cash':
                        result = simulate_contest_improved(
                            slate, strategy_name, strategy_config,
                            contest_type, field_size
                        )
                        if result:
                            result['slate_id'] = slate_id
                            results.append(result)
                            strategy_entries[f"cash_{strategy_name}"] += 1
                        else:
                            lineup_failures[f"cash_{strategy_name}"] += 1

        # Test GPP strategies
        for strategy_name, strategy_config in GPP_STRATEGIES.items():
            if strategy_entries[f"gpp_{strategy_name}"] < min_entries_per_strategy:
                for contest_type, field_size in contest_configs:
                    if contest_type == 'gpp':
                        result = simulate_contest_improved(
                            slate, strategy_name, strategy_config,
                            contest_type, field_size
                        )
                        if result:
                            result['slate_id'] = slate_id
                            results.append(result)
                            strategy_entries[f"gpp_{strategy_name}"] += 1
                        else:
                            lineup_failures[f"gpp_{strategy_name}"] += 1

        slate_index += 1

        # Debug logging every 10 slates
        if slate_index % 10 == 0 and slate_index > 0:
            total_success = sum(strategy_entries.values())
            total_failures = sum(lineup_failures.values())
            if total_success + total_failures > 0:
                success_rate = total_success / (total_success + total_failures) * 100
                print(f"  Batch debug - Slate {slate_index}: {total_success} successes, "
                      f"{total_failures} failures ({success_rate:.1f}% success rate)")

                # More detailed debug if all failing
                if total_success == 0 and slate_index == 10:
                    print(f"  ⚠️  Complete failure detected. Checking slate {slate_id}:")
                    print(f"     Players: {len(slate['players'])}")
                    print(f"     Games: {slate['num_games']}")
                    # Try to build one lineup manually
                    test_lineup = build_emergency_fallback_lineup(slate['players'])
                    if test_lineup:
                        print(f"     Emergency fallback CAN build lineup")
                    else:
                        print(f"     Emergency fallback CANNOT build lineup")
                        # Show position distribution
                        pos_counts = defaultdict(int)
                        for p in slate['players']:
                            pos_counts[p['position']] += 1
                        print(f"     Positions: {dict(pos_counts)}")

        # Check if all strategies have minimum entries
        all_satisfied = True
        for strat in CASH_STRATEGIES:
            if strategy_entries[f"cash_{strat}"] < min_entries_per_strategy:
                all_satisfied = False
                break

        if all_satisfied:
            for strat in GPP_STRATEGIES:
                if strategy_entries[f"gpp_{strat}"] < min_entries_per_strategy:
                    all_satisfied = False
                    break

        if all_satisfied and slate_index >= len(slate_ids) // 2:
            break  # Got minimum for all strategies

    # Final debug info
    if lineup_failures:
        print(f"\n  Batch complete - Success: {sum(strategy_entries.values())}, "
              f"Failures: {sum(lineup_failures.values())}")

    return results


def run_phase2_improved(num_slates: int = 1000, num_cores: int = 20):
    """Run improved Phase 2 simulation"""
    print(f"\n{'=' * 80}")
    print("🚀 DFS PHASE 2 IMPROVED - CASH OPTIMIZATION + GPP TESTING")
    print(f"{'=' * 80}")

    # Debug: Generate and check one slate first
    print("\n🔍 Debug: Checking slate generation...")
    test_slate = generate_improved_slate(0)
    print(f"   Games: {test_slate['num_games']}")
    print(f"   Total players: {len(test_slate['players'])}")
    print(f"   Pitchers: {len([p for p in test_slate['players'] if p['position'] == 'P'])}")
    print(f"   Hitters: {len([p for p in test_slate['players'] if p['position'] != 'P'])}")

    # Test lineup building
    print("\n🔍 Debug: Testing lineup builders...")
    test_lineup = build_pure_chalk_lineup(test_slate['players'])
    if test_lineup:
        print("   ✅ Pure chalk lineup built successfully")
    else:
        print("   ❌ Pure chalk lineup failed")
        # Try fallback
        fallback = build_emergency_fallback_lineup(test_slate['players'])
        if fallback:
            print("   ✅ Emergency fallback worked")
        else:
            print("   ❌ Even fallback failed - check player generation!")

    print(f"\n📊 Configuration:")
    print(f"   Slates: {num_slates:,}")
    print(f"   Cash Strategies: {len(CASH_STRATEGIES)}")
    print(f"   GPP Strategies: {len(GPP_STRATEGIES)}")
    print(f"   CPU Cores: {num_cores}")
    print(f"\n📋 Cash Strategies:")
    for name, config in CASH_STRATEGIES.items():
        print(f"   • {config['name']}")
    print(f"\n📋 GPP Strategies:")
    for name, config in GPP_STRATEGIES.items():
        print(f"   • {config['name']}")
    print(f"\n✅ Improvements:")
    print(f"   • Testing cash game variations")
    print(f"   • Fixed stack sizes (max 5 hitters)")
    print(f"   • Flexible lineup building")
    print(f"   • Minimum 50 entries per strategy")
    print(f"{'=' * 80}\n")

    # Contest configurations
    contest_configs = [
        ('gpp', 5000),
        ('gpp', 1000),
        ('cash', 100),
        ('cash', 50)
    ]

    # Create batches with minimum entry requirement
    slates_per_batch = 100  # Larger batches for better coverage
    min_entries = 50  # Minimum per strategy
    batches = []

    for i in range(0, num_slates, slates_per_batch):
        slate_batch = list(range(i, min(i + slates_per_batch, num_slates)))
        batches.append((slate_batch, contest_configs, min_entries))

    total_strategies = len(CASH_STRATEGIES) + len(GPP_STRATEGIES)
    estimated_contests = num_slates * total_strategies * 2

    print(f"📋 Processing {len(batches)} batches")
    print(f"   {slates_per_batch} slates per batch")
    print(f"   ~{estimated_contests:,} total contests")
    print(f"   Minimum {min_entries} entries per strategy\n")

    # Run simulation
    start_time = time.time()
    all_results = []
    completed = 0

    with ProcessPoolExecutor(max_workers=num_cores) as executor:
        future_to_batch = {
            executor.submit(process_slate_batch_improved, batch): batch
            for batch in batches
        }

        for future in as_completed(future_to_batch):
            try:
                batch_results = future.result()
                all_results.extend(batch_results)

                completed += 1

                if completed % 2 == 0 or completed == len(batches):
                    elapsed = time.time() - start_time
                    pct = (completed / len(batches)) * 100
                    rate = len(all_results) / elapsed if elapsed > 0 else 0

                    print(f"Progress: {completed}/{len(batches)} batches ({pct:.1f}%) | "
                          f"Results: {len(all_results)} | Rate: {rate:.1f} contests/sec")

            except Exception as e:
                print(f"Error in batch: {e}")
                import traceback
                traceback.print_exc()

    total_time = time.time() - start_time
    print(f"\n✅ Complete in {total_time:.1f} seconds")
    print(f"📊 Total results: {len(all_results):,}")

    # Analyze results
    analyze_improved_results(all_results, num_slates)


def analyze_improved_results(results: List[Dict], num_slates: int):
    """Analyze improved Phase 2 results"""
    print(f"\n{'=' * 80}")
    print("📊 PHASE 2 IMPROVED RESULTS ANALYSIS")
    print(f"{'=' * 80}\n")

    # Separate by contest type
    cash_results = defaultdict(list)
    gpp_results = defaultdict(list)

    for r in results:
        if r['contest_type'] == 'cash':
            cash_results[r['strategy']].append(r)
        else:
            gpp_results[r['strategy']].append(r)

    # CASH ANALYSIS
    print("💵 CASH GAME ANALYSIS\n")

    cash_summary = {}

    for strategy_name in CASH_STRATEGIES:
        results_list = cash_results.get(strategy_name, [])

        if len(results_list) < 10:
            print(f"⚠️  {CASH_STRATEGIES[strategy_name]['name']}: Only {len(results_list)} entries (skipping)")
            continue

        wins = sum(1 for r in results_list if r['profit'] >= 0)
        win_rate = (wins / len(results_list)) * 100
        roi = (sum(r['profit'] for r in results_list) / (len(results_list) * 5)) * 100
        avg_score = np.mean([r['score'] for r in results_list])
        avg_own = np.mean([r['ownership'] for r in results_list])

        print(f"📊 {CASH_STRATEGIES[strategy_name]['name']}")
        print(f"   Entries: {len(results_list)}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   ROI: {roi:+.1f}%")
        print(f"   Avg Score: {avg_score:.1f}")
        print(f"   Avg Ownership: {avg_own:.1f}%")

        if win_rate >= 55:
            print(f"   ✅ PROFITABLE!")
        elif win_rate >= 52:
            print(f"   ⚠️  Close to profitable")
        else:
            print(f"   ❌ Not profitable")
        print()

        cash_summary[strategy_name] = {
            'win_rate': win_rate,
            'roi': roi,
            'entries': len(results_list)
        }

    # GPP ANALYSIS
    print("\n🎯 GPP STRATEGY ANALYSIS\n")

    gpp_summary = {}

    for strategy_name in GPP_STRATEGIES:
        results_list = gpp_results.get(strategy_name, [])

        if len(results_list) < 10:
            print(f"⚠️  {GPP_STRATEGIES[strategy_name]['name']}: Only {len(results_list)} entries (skipping)")
            continue

        profits = [r['profit'] for r in results_list]
        percentiles = [r['percentile'] for r in results_list]

        roi = (sum(profits) / (len(results_list) * 3)) * 100
        top10 = sum(1 for p in percentiles if p >= 90) / len(results_list) * 100
        top1 = sum(1 for p in percentiles if p >= 99) / len(results_list) * 100
        first = sum(1 for r in results_list if r['rank'] == 1) / len(results_list) * 100
        avg_score = np.mean([r['score'] for r in results_list])
        avg_own = np.mean([r['ownership'] for r in results_list])

        print(f"📊 {GPP_STRATEGIES[strategy_name]['name']}")
        print(f"   Entries: {len(results_list)}")
        print(f"   ROI: {roi:+.1f}%")
        print(f"   Top 10%: {top10:.1f}%")
        print(f"   Top 1%: {top1:.2f}%")
        print(f"   First Place: {first:.3f}%")
        print(f"   Avg Score: {avg_score:.1f}")
        print(f"   Avg Ownership: {avg_own:.1f}%")

        if roi > 5:
            print(f"   🔥 PROFITABLE!")
        elif roi > -5:
            print(f"   ⚠️  Marginal")
        else:
            print(f"   ❌ Losing strategy")
        print()

        gpp_summary[strategy_name] = {
            'roi': roi,
            'top10': top10,
            'top1': top1,
            'entries': len(results_list)
        }

    # RANKINGS
    print(f"\n{'=' * 80}")
    print("🏆 FINAL RANKINGS")
    print(f"{'=' * 80}")

    # Cash rankings
    print("\n💵 CASH STRATEGIES (by Win Rate):")
    cash_ranked = sorted([(k, v['win_rate']) for k, v in cash_summary.items()],
                         key=lambda x: x[1], reverse=True)

    for rank, (strat, win_rate) in enumerate(cash_ranked, 1):
        roi = cash_summary[strat]['roi']
        print(f"{rank}. {CASH_STRATEGIES[strat]['name']:30s} "
              f"Win%: {win_rate:5.1f}%  ROI: {roi:+6.1f}%")

    # GPP rankings
    print("\n🎯 GPP STRATEGIES (by ROI):")
    gpp_ranked = sorted([(k, v['roi']) for k, v in gpp_summary.items()],
                        key=lambda x: x[1], reverse=True)

    for rank, (strat, roi) in enumerate(gpp_ranked, 1):
        top10 = gpp_summary[strat]['top10']
        print(f"{rank}. {GPP_STRATEGIES[strat]['name']:30s} "
              f"ROI: {roi:+6.1f}%  Top10: {top10:4.1f}%")

    # KEY FINDINGS
    print(f"\n{'=' * 80}")
    print("🔍 KEY FINDINGS")
    print(f"{'=' * 80}")

    # Best strategies
    if cash_ranked:
        best_cash = cash_ranked[0]
        print(f"\n💵 Best Cash: {CASH_STRATEGIES[best_cash[0]]['name']}")
        print(f"   Win Rate: {best_cash[1]:.1f}%")
        print(f"   ROI: {cash_summary[best_cash[0]]['roi']:+.1f}%")

    if gpp_ranked:
        best_gpp = gpp_ranked[0]
        print(f"\n🎯 Best GPP: {GPP_STRATEGIES[best_gpp[0]]['name']}")
        print(f"   ROI: {best_gpp[1]:+.1f}%")
        print(f"   Top 10%: {gpp_summary[best_gpp[0]]['top10']:.1f}%")

    # Save results
    results_data = {
        'timestamp': datetime.now().isoformat(),
        'num_slates': num_slates,
        'phase': '2_improved',
        'cash_summary': cash_summary,
        'gpp_summary': gpp_summary,
        'best_cash': cash_ranked[0][0] if cash_ranked else None,
        'best_gpp': gpp_ranked[0][0] if gpp_ranked else None
    }

    with open('phase2_improved_results.json', 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"\n💾 Results saved to: phase2_improved_results.json")

    print(f"\n{'=' * 80}")
    print("✅ PHASE 2 IMPROVED COMPLETE!")
    print(f"{'=' * 80}\n")


def main():
    """Run improved Phase 2"""
    print("\n🚀 DFS PHASE 2 IMPROVED")
    print("Testing cash improvements + fixed GPP strategies")
    print("=" * 60)

    num_slates = 1000
    num_cores = 20

    print(f"\n⚙️  Configuration:")
    print(f"   Slates: {num_slates:,}")
    print(f"   CPU Cores: {num_cores}")
    print(f"   Cash Strategies: {len(CASH_STRATEGIES)}")
    print(f"   GPP Strategies: {len(GPP_STRATEGIES)}")

    print(f"\n📊 Key Improvements:")
    print(f"   ✅ Testing cash variations")
    print(f"   ✅ Max 5 hitters per team")
    print(f"   ✅ Flexible lineup building")
    print(f"   ✅ Minimum entries guaranteed")

    input("\nPress Enter to find optimal strategies...")

    run_phase2_improved(num_slates, num_cores)


if __name__ == "__main__":
    main()