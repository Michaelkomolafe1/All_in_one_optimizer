#!/usr/bin/env python3
"""
FIXED REALISTIC DFS SIMULATION CORE
=====================================
Properly calibrated parameters with 2-decimal precision
Replace: simulation/realistic_simulation_core.py
"""

import numpy as np
import random
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import multiprocessing as mp
from datetime import datetime
import json
import time
import sys
import os

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==========================================
# FIXED REALISTIC PARAMETERS (2 DECIMALS MAX!)
# ==========================================

REALISTIC_PARAMS = {
    'score_variance': {
        'normal_std': 0.11,  # 11% standard deviation
        'disaster_rate': 0.01,  # 1% disaster chance
        'disaster_range': (0.50, 0.70),  # 50-70% of projection
        'ceiling_rate': 0.03,  # 3% chance of ceiling game
        'ceiling_range': (1.40, 1.75),  # 140-175% max (realistic!)
    },

    'cash_field': {
        'sharp': 0.25,  # 25% professionals
        'good': 0.35,  # 35% experienced players
        'average': 0.30,  # 30% casual players
        'weak': 0.10  # 10% beginners
    },

    'gpp_field': {
        'elite': 0.05,  # 5% ML-optimized pros
        'sharp': 0.15,  # 15% sharks
        'good': 0.30,  # 30% good players
        'average': 0.35,  # 35% average players
        'weak': 0.15  # 15% weak players
    },

    'correlation': {
        'stack_boost_3': 1.15,  # 3-man stack
        'stack_boost_4': 1.20,  # 4-man stack
        'stack_boost_5': 1.25,  # 5-man stack
        'stack_bust_factor': 0.70,  # When stack fails
        'game_correlation': 0.30  # Within-game correlation
    }
}

# ==========================================
# YOUR STRATEGY PARAMETERS - FIXED TO 2 DECIMALS!
# ==========================================

STRATEGY_PARAMS = {
    'projection_monster': {
        'park_weight': 0.50,
        'value_bonus_weight': 0.50,
        'min_projection_threshold': 8.00,
        'pitcher_park_weight': 0.50,
        'hitter_value_exp': 1.00,
        'projection_floor': 0.80
    },

    'pitcher_dominance': {
        'k_weight': 0.60,
        'matchup_weight': 0.40,
        'recent_weight': 0.30,
        'min_k_rate': 8.50,
        'elite_k_bonus': 1.40,
        'bad_matchup_penalty': 0.70
    },

    'correlation_value': {
        'high_total_threshold': 10.00,
        'med_total_threshold': 8.50,
        'high_game_multiplier': 1.50,
        'med_game_multiplier': 1.20,
        'low_game_multiplier': 0.80,
        'value_threshold': 3.50,
        'value_bonus': 1.50,
        'correlation_weight': 0.40,
        'ownership_threshold': 15.00,
        'ownership_penalty': 0.70
    },

    'tournament_winner_gpp': {
        'stack_size_min': 4,
        'stack_size_max': 5,
        'game_total_threshold': 9.50,
        'ownership_leverage_threshold': 15.00,
        'low_own_boost': 1.25,
        'high_own_penalty': 0.85,
        'k_rate_threshold': 25.00,
        'elite_k_boost': 1.20,
        'stack_correlation_mult': 1.30
    }
}

# ==========================================
# YOUR OPTIMAL STRATEGY SELECTION
# ==========================================

OPTIMAL_STRATEGY_MAP = {
    'cash': {
        'small': 'pitcher_dominance',  # Your 80% win rate winner
        'medium': 'projection_monster',  # Your 72% win rate winner
        'large': 'projection_monster'  # Your 74% win rate winner
    },
    'gpp': {
        'small': 'tournament_winner_gpp',  # Your best small GPP
        'medium': 'tournament_winner_gpp',  # Your best medium GPP
        'large': 'correlation_value'  # Your best large GPP
    }
}


# NEW VERSION - Better ranges based on real DFS slates
def get_slate_size(num_games: int) -> str:
    """Determine slate size from number of games - IMPROVED"""

    # More realistic ranges that match actual DFS offerings
    if num_games <= 5:  # Small: 2-5 games (early/afternoon slates)
        return 'small'
    elif num_games <= 10:  # Medium: 6-10 games (main slates)
        return 'medium'
    else:  # Large: 11+ games (all day slates)
        return 'large'


class SimulatedPlayer:
    """Realistic player for simulations"""

    def __init__(self, data: Dict):
        self.name = data['name']
        self.team = data['team']
        self.position = data['position']
        self.salary = data['salary']
        self.projection = round(data['projection'], 2)
        self.ownership = round(data.get('ownership', 15), 1)

        # Realistic variance
        self.floor = round(self.projection * 0.75, 2)
        self.ceiling = round(self.projection * 1.40, 2)

        # Add all other attributes
        for key, value in data.items():
            if not hasattr(self, key):
                if isinstance(value, float):
                    setattr(self, key, round(value, 2))
                else:
                    setattr(self, key, value)


def generate_realistic_slate(num_games: int, slate_id: int = None) -> Dict:
    """Generate a realistic slate with proper parameters"""

    if slate_id is None:
        slate_id = random.randint(1000, 9999)

    slate_size = get_slate_size(num_games)
    players = []

    # Generate teams
    teams = []
    for i in range(num_games * 2):
        teams.append(f"TM{i + 1}")

    # Create games with realistic totals
    games = []
    for i in range(0, len(teams), 2):
        game_total = round(random.uniform(7.5, 11.5), 1)  # Realistic MLB totals
        games.append({
            'home': teams[i],
            'away': teams[i + 1],
            'total': game_total,
            'home_total': round(game_total * random.uniform(0.45, 0.55), 1),
            'away_total': round(game_total * random.uniform(0.45, 0.55), 1)
        })

    # Generate pitchers
    for game in games:
        for team in [game['home'], game['away']]:
            # Ace vs average distribution
            is_ace = random.random() < 0.3

            pitcher = {
                'name': f"P_{team}",
                'team': team,
                'position': 'P',
                'salary': random.randint(8500, 11000) if is_ace else random.randint(6500, 8500),
                'projection': round(random.uniform(18, 25), 2) if is_ace else round(random.uniform(12, 18), 2),
                'k_rate': round(random.uniform(25, 32), 1) if is_ace else round(random.uniform(18, 25), 1),
                'era': round(random.uniform(2.5, 3.5), 2) if is_ace else round(random.uniform(3.5, 5.0), 2),
                'ownership': round(random.uniform(15, 35), 1) if is_ace else round(random.uniform(5, 15), 1),
                'game_total': game['total'],
                'opponent_total': game['away_total'] if team == game['home'] else game['home_total']
            }
            players.append(SimulatedPlayer(pitcher))

    # Generate hitters
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']

    for game in games:
        for team in [game['home'], game['away']]:
            team_total = game['home_total'] if team == game['home'] else game['away_total']

            for i, pos in enumerate(positions):
                # Batting order affects projection
                order_mult = 1.2 - (i * 0.05)  # 1-3 hitters get boost

                hitter = {
                    'name': f"{pos}_{team}_{i + 1}",
                    'team': team,
                    'position': pos,
                    'salary': random.randint(3000, 5500) if i < 4 else random.randint(2500, 4000),
                    'projection': round(random.uniform(7, 12) * order_mult, 2),
                    'batting_order': i + 1,
                    'game_total': game['total'],
                    'team_total': team_total,
                    'ownership': round(random.uniform(5, 30), 1),
                    'recent_performance': round(random.uniform(0.80, 1.20), 2),
                    'matchup_score': round(random.uniform(0.70, 1.30), 2),
                    'park_factor': round(random.uniform(0.85, 1.15), 2)
                }
                players.append(SimulatedPlayer(hitter))

    return {
        'slate_id': slate_id,
        'slate_size': slate_size,
        'num_games': num_games,
        'players': players,
        'games': games,
        'total_salary_cap': 50000
    }


def apply_realistic_variance(player: SimulatedPlayer,
                             correlation_group: Optional[List] = None) -> float:
    """Apply realistic variance to player scores"""

    base_score = player.projection

    # Determine performance type
    rand = random.random()

    if rand < REALISTIC_PARAMS['score_variance']['disaster_rate']:
        # Disaster performance (1% chance)
        mult_range = REALISTIC_PARAMS['score_variance']['disaster_range']
        multiplier = random.uniform(mult_range[0], mult_range[1])

    elif rand < (REALISTIC_PARAMS['score_variance']['disaster_rate'] +
                 REALISTIC_PARAMS['score_variance']['ceiling_rate']):
        # Ceiling performance (3% chance)
        mult_range = REALISTIC_PARAMS['score_variance']['ceiling_range']
        multiplier = random.uniform(mult_range[0], mult_range[1])

    else:
        # Normal variance (96% of the time)
        std = REALISTIC_PARAMS['score_variance']['normal_std']
        multiplier = np.random.normal(1.0, std)
        multiplier = max(0.60, min(1.40, multiplier))  # Cap at reasonable limits

    # Apply correlation if in a stack
    if correlation_group and len(correlation_group) >= 3:
        # Check if this is a correlated outcome
        correlation_roll = random.random()
        if correlation_roll < REALISTIC_PARAMS['correlation']['game_correlation']:
            # All stack members trend same direction
            if multiplier > 1.0:
                stack_size = min(len(correlation_group), 5)
                boost_key = f'stack_boost_{stack_size}'
                multiplier *= REALISTIC_PARAMS['correlation'].get(boost_key, 1.15)
            else:
                multiplier *= REALISTIC_PARAMS['correlation']['stack_bust_factor']

    return round(base_score * multiplier, 2)


def build_opponent_lineup(players: List, skill_level: str = 'average') -> Dict:
    """Build realistic opponent lineup based on skill level"""

    # CRITICAL: Make opponents ACTUALLY competitive
    import random

    # First, ensure all players have required attributes
    valid_players = []
    for p in players:
        if hasattr(p, 'projection') and p.projection > 0:
            valid_players.append(p)

    if len(valid_players) < 10:
        return {'players': players[:10]}

    # Build lineup based on skill
    if skill_level == 'elite':
        # Elite players use near-optimal strategy
        sorted_players = sorted(valid_players, key=lambda p: p.projection, reverse=True)

        # Get best pitcher
        pitchers = [p for p in sorted_players if p.position == 'P']
        best_pitcher = pitchers[0] if pitchers else sorted_players[0]

        # Get best hitters
        hitters = [p for p in sorted_players if p.position != 'P'][:9]

        lineup = [best_pitcher] + hitters[:9]

        # Apply small random variance to make it realistic
        for p in lineup:
            p.actual_score = p.projection * random.uniform(0.85, 1.15)

    elif skill_level == 'sharp':
        # Sharp players are good but not perfect
        sorted_players = sorted(valid_players, key=lambda p: p.projection * random.uniform(0.9, 1.1), reverse=True)

        # Take top 15 and build from them
        top_players = sorted_players[:15]
        lineup = top_players[:10]

        for p in lineup:
            p.actual_score = p.projection * random.uniform(0.8, 1.2)

    elif skill_level == 'average':
        # Average players make some mistakes
        score_func = lambda p: p.projection * random.uniform(0.7, 1.0)
        sorted_players = sorted(valid_players, key=score_func, reverse=True)

        # Take from top 25
        pool = sorted_players[:25]
        random.shuffle(pool)
        lineup = pool[:10]

        for p in lineup:
            p.actual_score = p.projection * random.uniform(0.7, 1.3)

    else:  # weak
        # Weak players make lots of mistakes
        random.shuffle(valid_players)
        lineup = valid_players[:10]

        for p in lineup:
            p.actual_score = p.projection * random.uniform(0.6, 1.4)

    # Calculate total projection for this lineup
    total_projection = sum(getattr(p, 'projection', 10) for p in lineup)

    return {
        'players': lineup,
        'skill_level': skill_level,
        'projected_score': total_projection,
        'actual_score': sum(getattr(p, 'actual_score', p.projection) for p in lineup)
    }


def simulate_contest(your_lineup: Dict, field: List[Dict], contest_type: str) -> Dict:
    """Simulate a realistic DFS contest"""

    import random
    import numpy as np

    # Calculate YOUR actual score with variance
    your_projected = sum(getattr(p, 'projection', 10) for p in your_lineup['players'])
    your_actual = 0

    for player in your_lineup['players']:
        # Apply realistic variance
        player_score = getattr(player, 'projection', 10)
        actual = player_score * np.random.normal(1.0, 0.15)  # 15% standard deviation
        actual = max(0, actual)  # Can't score negative
        your_actual += actual

    # Calculate FIELD scores
    field_scores = []
    for opponent in field:
        # Use the actual_score if it exists, otherwise calculate
        if 'actual_score' in opponent:
            opp_score = opponent['actual_score']
        else:
            opp_projected = sum(getattr(p, 'projection', 10) for p in opponent['players'])
            # Apply variance based on skill
            skill = opponent.get('skill_level', 'average')
            if skill == 'elite':
                std_dev = 0.12  # Less variance for elite
            elif skill == 'sharp':
                std_dev = 0.15
            else:
                std_dev = 0.20  # More variance for weaker players

            opp_score = opp_projected * np.random.normal(1.0, std_dev)
            opp_score = max(0, opp_score)

        field_scores.append(opp_score)

    # Determine your rank
    field_scores.sort(reverse=True)
    your_rank = sum(1 for score in field_scores if score > your_actual) + 1
    percentile = (len(field_scores) - your_rank + 1) / len(field_scores) * 100

    # Calculate realistic payouts
    if contest_type == 'cash':
        # Cash game - top 45% win (more realistic than 50%)
        cutoff = int(len(field_scores) * 0.45)
        won = your_rank <= cutoff
        roi = 80 if won else -100  # 0.8x payout for cash

    else:  # GPP
        # Tournament payouts
        total_field = len(field_scores)
        if your_rank == 1:
            roi = 500 + random.randint(0, 400)  # 5-9x
        elif your_rank <= 3:
            roi = 200 + random.randint(0, 200)  # 2-4x
        elif your_rank <= total_field * 0.01:  # Top 1%
            roi = 100 + random.randint(0, 100)  # 1-2x
        elif your_rank <= total_field * 0.1:  # Top 10%
            roi = random.randint(-50, 50)  # Break even-ish
        elif your_rank <= total_field * 0.2:  # Top 20%
            roi = -75  # Small loss
        else:
            roi = -100  # Total loss

    return {
        'your_score': your_actual,
        'your_projected': your_projected,
        'your_rank': your_rank,
        'field_size': len(field_scores),
        'percentile': percentile,
        'won': roi > 0,
        'roi': roi,
        'top_score': field_scores[0] if field_scores else your_actual,
        'cash_line': field_scores[cutoff] if contest_type == 'cash' and cutoff < len(field_scores) else 0
    }


# Export functions for parallel processing
def process_single_simulation(args):
    """Single simulation for parallel processing"""
    sim_id, num_games, contest_type, your_strategy_name, your_lineup, field_size = args

    # Generate slate
    slate = generate_realistic_slate(num_games, sim_id)

    # Generate field
    field = []
    if contest_type == 'cash':
        distribution = REALISTIC_PARAMS['cash_field']
    else:
        distribution = REALISTIC_PARAMS['gpp_field']

    for skill_level, percentage in distribution.items():
        num_lineups = int(field_size * percentage)

        for _ in range(num_lineups):
            lineup = build_opponent_lineup(slate['players'], skill_level, contest_type)
            if lineup:
                field.append({
                    'players': lineup,
                    'skill_level': skill_level
                })

    # Run contest
    result = simulate_contest(your_lineup, field, contest_type)
    result['sim_id'] = sim_id
    result['strategy'] = your_strategy_name

    return result


if __name__ == "__main__":
    print("Fixed Realistic Simulation Core loaded successfully!")
    print(f"Strategies configured: {list(OPTIMAL_STRATEGY_MAP['cash'].values())}")
    print(f"Field distributions fixed: Cash={REALISTIC_PARAMS['cash_field']['sharp'] * 100:.0f}% sharp")
    print(f"Variance fixed: {REALISTIC_PARAMS['score_variance']['normal_std'] * 100:.0f}% std dev")