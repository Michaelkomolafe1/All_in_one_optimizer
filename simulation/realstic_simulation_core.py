#!/usr/bin/env python3
"""
REALISTIC DFS SIMULATION CORE
==============================
Fixed parameters, realistic field generation, YOUR strategies only
"""

import numpy as np
import random
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import multiprocessing as mp
from datetime import datetime
import json
import time

# ==========================================
# REALISTIC PARAMETERS (FIXED)
# ==========================================

REALISTIC_PARAMS = {
    'score_variance': {
        'normal_std': 0.10,  # 10% standard deviation (was 15%)
        'disaster_rate': 0.01,  # 1% disaster chance (was 3%)
        'disaster_range': (0.5, 0.7),  # 50-70% of projection (was 30-60%)
        'ceiling_rate': 0.02,  # 2% chance of ceiling game
        'ceiling_range': (1.4, 1.8),  # 140-180% max (was 250-350%!)
    },

    'cash_field': {
        'sharp': 0.25,  # 25% pros (was 8%!)
        'good': 0.35,  # 35% experienced
        'average': 0.30,  # 30% casual
        'weak': 0.10  # 10% beginners
    },

    'gpp_field': {
        'elite': 0.05,  # 5% ML-optimized pros
        'sharp': 0.15,  # 15% sharks
        'good': 0.30,  # 30% good players
        'average': 0.35,  # 35% average
        'weak': 0.15  # 15% weak
    },

    'correlation': {
        'stack_boost_3': 1.15,  # 3-man stack correlation
        'stack_boost_4': 1.20,  # 4-man stack correlation
        'stack_boost_5': 1.25,  # 5-man stack correlation
        'stack_bust_factor': 0.7,  # When stack fails
        'game_correlation': 0.3  # Correlation within same game
    }
}

# ==========================================
# YOUR STRATEGY MAPPINGS (From your tests)
# ==========================================

STRATEGY_MAP = {
    'cash': {
        'small': 'pitcher_dominance',  # 80% win rate
        'medium': 'projection_monster',  # 72% win rate
        'large': 'projection_monster'  # 74% win rate
    },
    'gpp': {
        'small': 'tournament_winner_gpp',  # Best small GPP
        'medium': 'tournament_winner_gpp',  # Best medium GPP
        'large': 'correlation_value'  # Best large GPP
    }
}

# Simple, robust multipliers (2 decimals max!)
STRATEGY_PARAMS = {
    'pitcher_dominance': {
        'k_rate_threshold': 25,  # Simple whole number
        'elite_multiplier': 1.20,  # 2 decimals max
        'consistency_weight': 0.35,  # Simple weight
        'floor_emphasis': 0.65
    },
    'projection_monster': {
        'projection_weight': 0.70,
        'value_weight': 0.30,
        'min_projection': 8.0,
        'value_threshold': 2.0
    },
    'tournament_winner_gpp': {
        'stack_size': 4,
        'ownership_threshold': 15,
        'ownership_leverage': 1.10,
        'ceiling_weight': 0.60
    },
    'correlation_value': {
        'min_correlation': 3,
        'team_total_threshold': 5.0,
        'correlation_multiplier': 1.25,
        'game_stack_bonus': 1.15
    }
}


class SimulatedPlayer:
    """Simulated player with realistic attributes"""

    def __init__(self, name: str, position: str, team: str, salary: int,
                 projection: float, ownership: float = None):
        self.name = name
        self.position = position
        self.primary_position = position
        self.team = team
        self.salary = salary
        self.projection = projection
        self.base_projection = projection

        # Add realistic ownership
        if ownership is None:
            if salary >= 9000:
                self.ownership = np.random.uniform(15, 35)
            elif salary >= 7000:
                self.ownership = np.random.uniform(10, 25)
            elif salary >= 5000:
                self.ownership = np.random.uniform(5, 20)
            else:
                self.ownership = np.random.uniform(2, 15)
        else:
            self.ownership = ownership

        self.projected_ownership = self.ownership

        # Add other attributes your strategies expect
        self.is_pitcher = (position == 'P')
        self.batting_order = random.randint(1, 9) if not self.is_pitcher else 0
        self.implied_team_score = np.random.uniform(3.5, 6.5)
        self.team_total = self.implied_team_score
        self.consistency_score = np.random.uniform(0.7, 1.3)
        self.recent_form = np.random.uniform(0.8, 1.2)
        self.matchup_score = np.random.uniform(0.8, 1.2)
        self.park_factor = np.random.uniform(0.85, 1.15)

        # Set ID for compatibility
        self.id = f"{name.replace(' ', '_')}_{team}".lower()


def generate_realistic_slate(slate_size: str = 'medium', num_games: int = None) -> Dict:
    """Generate realistic slate of players"""

    if num_games is None:
        if slate_size == 'small':
            num_games = random.randint(2, 4)
        elif slate_size == 'medium':
            num_games = random.randint(5, 9)
        else:  # large
            num_games = random.randint(10, 15)

    teams = []
    for i in range(num_games * 2):
        teams.append(f"TM{i + 1}")

    players = []
    player_id = 0

    # Generate pitchers (2 per team)
    for team in teams:
        # Ace pitcher
        salary = random.randint(8000, 11000)
        projection = salary / 1000 * np.random.uniform(1.8, 2.4)
        players.append(SimulatedPlayer(
            f"Pitcher{player_id}",
            'P', team, salary, projection
        ))
        player_id += 1

        # Second pitcher
        salary = random.randint(6000, 8500)
        projection = salary / 1000 * np.random.uniform(1.6, 2.2)
        players.append(SimulatedPlayer(
            f"Pitcher{player_id}",
            'P', team, salary, projection
        ))
        player_id += 1

    # Generate position players
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']

    for team in teams:
        for pos in positions:
            # Stud players
            if random.random() < 0.2:
                salary = random.randint(5000, 6000)
                projection = salary / 1000 * np.random.uniform(2.0, 2.8)
            # Average players
            elif random.random() < 0.6:
                salary = random.randint(3500, 5000)
                projection = salary / 1000 * np.random.uniform(1.8, 2.4)
            # Value plays
            else:
                salary = random.randint(2500, 3500)
                projection = salary / 1000 * np.random.uniform(1.6, 2.3)

            players.append(SimulatedPlayer(
                f"Player{player_id}",
                pos, team, salary, projection
            ))
            player_id += 1

    return {
        'slate_size': slate_size,
        'num_games': num_games,
        'players': players,
        'teams': teams
    }


def simulate_realistic_score(lineup: List[SimulatedPlayer]) -> float:
    """Simulate lineup score with REALISTIC variance"""

    params = REALISTIC_PARAMS['score_variance']
    total_projection = sum(p.projection for p in lineup)

    # Check for disaster (1% chance)
    if random.random() < params['disaster_rate']:
        disaster_mult = np.random.uniform(*params['disaster_range'])
        return total_projection * disaster_mult

    # Check for ceiling game (2% chance)
    if random.random() < params['ceiling_rate']:
        ceiling_mult = np.random.uniform(*params['ceiling_range'])
        return total_projection * ceiling_mult

    # Normal variance with correlation
    scores = []

    # Group by team for correlation
    team_groups = defaultdict(list)
    for player in lineup:
        team_groups[player.team].append(player)

    # Calculate correlated scores
    for team, team_players in team_groups.items():
        # Team correlation factor
        if len(team_players) >= 3:
            # Stack correlation
            team_factor = np.random.normal(1.0, 0.15)
            if team_factor > 1.2:  # Stack hits
                team_factor *= REALISTIC_PARAMS['correlation']['stack_boost_3']
            elif team_factor < 0.8:  # Stack busts
                team_factor *= REALISTIC_PARAMS['correlation']['stack_bust_factor']
        else:
            team_factor = np.random.normal(1.0, params['normal_std'])

        # Apply to each player
        for player in team_players:
            player_variance = np.random.normal(1.0, params['normal_std'] * 0.5)
            final_score = player.projection * team_factor * player_variance
            scores.append(max(0, final_score))  # Can't go negative

    return sum(scores)


def build_opponent_lineup(players: List[SimulatedPlayer], skill_level: str,
                          contest_type: str) -> List[SimulatedPlayer]:
    """Build opponent lineup based on skill level"""

    lineup = []
    used_salary = 0
    max_salary = 50000

    # Sort players by different metrics based on skill
    if skill_level == 'elite':
        # Elite players use advanced metrics
        sorted_players = sorted(players,
                                key=lambda p: p.projection * (1.0 + (20 - p.ownership) * 0.01),
                                reverse=True)
    elif skill_level == 'sharp':
        # Sharp players focus on value
        sorted_players = sorted(players,
                                key=lambda p: p.projection / p.salary * 1000,
                                reverse=True)
    elif skill_level == 'good':
        # Good players use projections with some randomness
        sorted_players = sorted(players,
                                key=lambda p: p.projection * np.random.uniform(0.9, 1.1),
                                reverse=True)
    elif skill_level == 'average':
        # Average players use projections
        sorted_players = sorted(players, key=lambda p: p.projection, reverse=True)
    else:  # weak
        # Weak players are somewhat random
        random.shuffle(players)
        sorted_players = players

    # Build lineup respecting positions
    positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

    for position, count in positions_needed.items():
        position_players = [p for p in sorted_players
                            if p.position == position
                            and p not in lineup
                            and used_salary + p.salary <= max_salary - (10 - len(lineup)) * 2500]

        for i in range(min(count, len(position_players))):
            if len(lineup) < 10:
                lineup.append(position_players[i])
                used_salary += position_players[i].salary

    return lineup if len(lineup) == 10 else None


def generate_realistic_field(slate: Dict, contest_type: str, field_size: int) -> List:
    """Generate realistic field of opponents"""

    field = []

    # Get skill distribution
    if contest_type == 'cash':
        distribution = REALISTIC_PARAMS['cash_field']
    else:
        distribution = REALISTIC_PARAMS['gpp_field']

    # Generate lineups for each skill level
    for skill_level, percentage in distribution.items():
        num_lineups = int(field_size * percentage)

        for _ in range(num_lineups):
            lineup = build_opponent_lineup(slate['players'], skill_level, contest_type)
            if lineup:
                field.append({
                    'players': lineup,
                    'skill_level': skill_level,
                    'projection': sum(p.projection for p in lineup)
                })

    return field


def run_single_simulation(args: Tuple) -> Dict:
    """Run single simulation (for parallel processing)"""

    slate_num, slate_size, contest_type, strategy_name = args

    # Generate slate
    slate = generate_realistic_slate(slate_size)

    # Import YOUR system
    try:
        import sys
        import os
        sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer/main_optimizer')

        from unified_core_system_updated import UnifiedCoreSystem
        from unified_player_model import UnifiedPlayer

        # Create system
        system = UnifiedCoreSystem()

        # Convert simulated players to UnifiedPlayer objects
        unified_players = []
        for sim_player in slate['players']:
            player = UnifiedPlayer(
                id=sim_player.id,
                name=sim_player.name,
                team=sim_player.team,
                salary=sim_player.salary,
                primary_position=sim_player.position,
                positions=[sim_player.position],
                base_projection=sim_player.projection
            )

            # Copy attributes
            for attr in ['ownership', 'is_pitcher', 'batting_order',
                         'implied_team_score', 'consistency_score',
                         'recent_form', 'matchup_score', 'park_factor']:
                setattr(player, attr, getattr(sim_player, attr))

            # Set additional attributes
            player.projected_ownership = sim_player.ownership
            player.team_total = sim_player.implied_team_score

            unified_players.append(player)

        # Set up system
        system.players = unified_players
        system.player_pool = unified_players
        system.csv_loaded = True
        system.current_slate_size = slate_size

        # Run optimization with YOUR strategy
        lineups = system.optimize_lineup(
            strategy=strategy_name,
            contest_type=contest_type,
            num_lineups=1
        )

        if not lineups:
            return None

        our_lineup = lineups[0]['players']

    except Exception as e:
        print(f"Error building lineup: {e}")
        return None

    # Generate field
    field_size = 100 if contest_type == 'cash' else 150
    field = generate_realistic_field(slate, contest_type, field_size)

    # Score our lineup
    our_score = simulate_realistic_score(our_lineup)

    # Score field
    field_scores = []
    for opponent in field:
        if opponent and opponent['players']:
            score = simulate_realistic_score(opponent['players'])
            field_scores.append(score)

    # Calculate results
    all_scores = [our_score] + field_scores
    all_scores.sort(reverse=True)
    rank = all_scores.index(our_score) + 1
    percentile = ((len(all_scores) - rank) / len(all_scores)) * 100

    # Determine win
    if contest_type == 'cash':
        win = rank <= int(field_size * 0.44)  # Top 44% cash
        roi = 80 if win else -100  # Realistic cash ROI
    else:
        # GPP payouts
        if rank == 1:
            roi = 500  # More realistic than 900%
        elif rank <= 3:
            roi = 200
        elif rank <= 10:
            roi = 50
        elif rank <= 20:
            roi = -50
        else:
            roi = -100
        win = rank <= 20

    return {
        'slate_num': slate_num,
        'slate_size': slate_size,
        'contest_type': contest_type,
        'strategy': strategy_name,
        'rank': rank,
        'percentile': percentile,
        'score': our_score,
        'win': win,
        'roi': roi,
        'field_avg': np.mean(field_scores) if field_scores else 0,
        'projection': sum(p.base_projection for p in our_lineup)
    }


def run_parallel_simulation(num_slates: int = 1000, num_cores: int = None) -> Dict:
    """Run parallel simulation of all strategies"""

    if num_cores is None:
        num_cores = mp.cpu_count() - 1

    print(f"\n{'=' * 60}")
    print(f"REALISTIC DFS SIMULATION")
    print(f"{'=' * 60}")
    print(f"Slates: {num_slates}")
    print(f"Cores: {num_cores}")
    print(f"Strategies: YOUR actual winning strategies")
    print(f"Field: REALISTIC (25% sharks in cash)")
    print(f"Variance: FIXED (10% std dev, 1% disasters)")

    # Create simulation tasks
    tasks = []
    slate_num = 0

    for _ in range(num_slates // 6):  # Divide by 6 for all combinations
        for slate_size in ['small', 'medium', 'large']:
            for contest_type in ['cash', 'gpp']:
                strategy = STRATEGY_MAP[contest_type][slate_size]
                tasks.append((slate_num, slate_size, contest_type, strategy))
                slate_num += 1

    print(f"\nRunning {len(tasks)} simulations...")
    start_time = time.time()

    # Run in parallel
    with mp.Pool(num_cores) as pool:
        results = []
        for i, result in enumerate(pool.imap_unordered(run_single_simulation, tasks)):
            if result:
                results.append(result)

            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining = (len(tasks) - i - 1) / rate
                print(f"Progress: {i + 1}/{len(tasks)} ({100 * (i + 1) / len(tasks):.1f}%) "
                      f"- ETA: {remaining / 60:.1f} min")

    print(f"\n✅ Completed in {(time.time() - start_time) / 60:.1f} minutes")

    return analyze_results(results)


def analyze_results(results: List[Dict]) -> Dict:
    """Analyze simulation results"""

    if not results:
        print("No results to analyze!")
        return {}

    print(f"\n{'=' * 60}")
    print("RESULTS ANALYSIS")
    print(f"{'=' * 60}")

    # Group by strategy
    by_strategy = defaultdict(list)
    for r in results:
        key = f"{r['strategy']}_{r['contest_type']}_{r['slate_size']}"
        by_strategy[key].append(r)

    # Analyze each strategy
    summary = {}

    print(f"\n{'Strategy':<30} {'Contest':<8} {'Slate':<8} {'Win%':<8} {'ROI%':<8} {'Avg Rank'}")
    print("-" * 80)

    for key in sorted(by_strategy.keys()):
        results_list = by_strategy[key]
        if not results_list:
            continue

        strategy, contest, slate = key.rsplit('_', 2)

        wins = sum(1 for r in results_list if r['win'])
        win_rate = wins / len(results_list) * 100
        avg_roi = np.mean([r['roi'] for r in results_list])
        avg_rank = np.mean([r['rank'] for r in results_list])
        avg_percentile = np.mean([r['percentile'] for r in results_list])

        print(f"{strategy:<30} {contest:<8} {slate:<8} {win_rate:<7.1f}% "
              f"{avg_roi:<+7.1f}% {avg_rank:<.1f}")

        summary[key] = {
            'strategy': strategy,
            'contest_type': contest,
            'slate_size': slate,
            'num_sims': len(results_list),
            'win_rate': win_rate,
            'roi': avg_roi,
            'avg_rank': avg_rank,
            'percentile': avg_percentile
        }

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'simulation_results_{timestamp}.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n💾 Results saved to simulation_results_{timestamp}.json")

    # Check if strategies are working as expected
    print(f"\n{'=' * 60}")
    print("VALIDATION CHECKS")
    print(f"{'=' * 60}")

    expected_ranges = {
        'cash': {'win_rate': (40, 55), 'roi': (-20, 30)},
        'gpp': {'win_rate': (15, 25), 'roi': (-40, 20)}
    }

    issues = []
    for key, stats in summary.items():
        contest = stats['contest_type']
        expected = expected_ranges[contest]

        if not (expected['win_rate'][0] <= stats['win_rate'] <= expected['win_rate'][1]):
            issues.append(f"{key}: Win rate {stats['win_rate']:.1f}% outside expected range")

        if not (expected['roi'][0] <= stats['roi'] <= expected['roi'][1]):
            issues.append(f"{key}: ROI {stats['roi']:.1f}% outside expected range")

    if issues:
        print("⚠️ ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ All strategies performing within expected ranges!")

    return summary


if __name__ == "__main__":
    # Run simulation
    results = run_parallel_simulation(num_slates=1000, num_cores=4)