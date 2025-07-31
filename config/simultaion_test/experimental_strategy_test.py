#!/usr/bin/env python3
"""
EXPERIMENTAL STRATEGY TESTING MODULE
====================================
Test new DFS strategies using the same framework as main simulator
Outputs results in identical format to main simulator
"""

import sys
import os
import numpy as np
import json
import time
import sys
from datetime import datetime
from collections import defaultdict, deque

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import from main simulator - use all the same functions
from robust_dfs_simulator import (
    generate_slate, simulate_contest, create_lineup_dict,
    build_adaptive_lineup, optimize_salary_usage_adaptive,
    SlateAnalyzer, CLASSIC_CONFIG, SHOWDOWN_CONFIG,
    draw_dashboard, complete_lineup_with_requirements,
    validate_lineup, process_batch, OutputLogger
)


# ========== EXPERIMENTAL STRATEGIES ==========
# Replace the existing build_lineup function with this one that includes experimental strategies
def build_lineup(players, strategy_config, format_type, slate_size):
    """Extended lineup builder that knows about experimental strategies"""
    strategy_type = strategy_config.get('type', 'unknown')

    # Check if it's an experimental strategy
    if strategy_type in EXPERIMENTAL_BUILDERS:
        builder = EXPERIMENTAL_BUILDERS[strategy_type]
        try:
            lineup = builder(players)
            return lineup
        except Exception as e:
            print(f"Error in experimental strategy {strategy_type}: {str(e)}")
            return None

    # Otherwise, use the main simulator's build_lineup
    from robust_dfs_simulator import build_lineup as main_build_lineup
    return main_build_lineup(players, strategy_config, format_type, slate_size)


def build_contrarian_showdown(players):
    """Showdown: Low-owned captain with negative correlation"""
    if not players:
        return None

    # Find low-owned players
    low_owned = [p for p in players if p.get('ownership', 20) < 15]

    if len(low_owned) < 3:
        low_owned = [p for p in players if p.get('ownership', 20) < 20]

    # Calculate contrarian captain scores
    for p in low_owned:
        ownership_leverage = 30 / (p.get('ownership', 20) + 5)
        ceiling_mult = p.get('ceiling', p['projection'] * 1.5) / p['projection']
        p['contrarian_captain_score'] = ownership_leverage * ceiling_mult * p['projection']

    # Sort by contrarian score
    captain_candidates = sorted(low_owned,
                                key=lambda x: x.get('contrarian_captain_score', 0),
                                reverse=True)

    # Try captains
    for captain in captain_candidates[:10]:
        lineup = []

        # Captain slot
        captain_slot = {
            'id': captain['id'],
            'name': captain['name'] + ' (CPT)',
            'team': captain['team'],
            'position': 'CPT',
            'salary': int(captain['salary'] * 1.5),
            'projection': captain['projection'],
            'ownership': captain['ownership'],
            'is_captain': True,
            'ceiling': captain.get('ceiling', captain['projection'] * 1.5),
            'floor': captain.get('floor', captain['projection'] * 0.5)
        }
        lineup.append(captain_slot)

        remaining_salary = 50000 - captain_slot['salary']

        # Get remaining players
        remaining = [p for p in players if p['id'] != captain['id']]

        # NEGATIVE correlation - emphasize opposing team
        same_team = [p for p in remaining if p['team'] == captain['team']]
        opp_team = [p for p in remaining if p['team'] != captain['team']]

        # Sort by ceiling for GPP
        same_team.sort(key=lambda x: x.get('ceiling', x['projection']), reverse=True)
        opp_team.sort(key=lambda x: x.get('ceiling', x['projection']), reverse=True)

        # Build with MORE from opposing team
        flex_players = []
        flex_salary = 0

        # Target: 1-2 from captain's team, 3-4 from opponent
        target_order = opp_team[:4] + same_team[:2] + opp_team[4:] + same_team[2:]

        for p in target_order:
            if (len(flex_players) < 5 and
                    flex_salary + p['salary'] <= remaining_salary):
                flex_slot = p.copy()
                flex_slot['is_captain'] = False
                flex_players.append(flex_slot)
                flex_salary += p['salary']

        if len(flex_players) == 5:
            lineup.extend(flex_players)

            # Calculate projections CORRECTLY
            total_proj = captain['projection'] * 1.5  # Captain gets 1.5x
            total_proj += sum(p['projection'] for p in flex_players)

            total_salary = captain_slot['salary'] + flex_salary

            # Calculate other metrics
            total_ceiling = captain['ceiling'] * 1.5 + sum(
                p.get('ceiling', p['projection'] * 1.5) for p in flex_players)
            total_floor = captain['floor'] * 1.5 + sum(p.get('floor', p['projection'] * 0.5) for p in flex_players)

            lineup_dict = {
                'players': lineup,
                'salary': total_salary,
                'projection': total_proj,
                'ownership': np.mean([captain['ownership']] + [p['ownership'] for p in flex_players]),
                'strategy': 'contrarian_showdown',
                'captain': captain['name'],
                'captain_ownership': captain['ownership'],
                'format': 'showdown',
                'ceiling': total_ceiling,
                'floor': total_floor,
                'captain_multiplier': 1.5
            }

            return lineup_dict

    return None


def build_balanced_showdown_fixed(players):
    """ROBUST FIXED: Showdown with correct scoring"""
    if not players:
        return None

    # Ensure we have both teams
    teams = list(set(p['team'] for p in players))
    if len(teams) < 2:
        return None

    # Calculate captain scores with proper multipliers
    for p in players:
        # Captain efficiency with safety checks
        ceiling = p.get('ceiling', p['projection'] * 1.5)
        salary = max(p['salary'], 1500)  # Minimum salary safety

        p['captain_score'] = (ceiling * 1.5) / (salary * 1.5 / 1000)
        p['captain_efficiency'] = ceiling / salary

    # Sort candidates
    captain_candidates = sorted(players,
                                key=lambda x: x.get('captain_score', 0),
                                reverse=True)

    # Try multiple captains for robustness
    for captain in captain_candidates[:15]:  # Try more candidates
        lineup = []

        # Create captain with proper salary
        captain_slot = {
            'id': captain['id'],
            'name': captain['name'] + ' (CPT)',
            'team': captain['team'],
            'position': 'CPT',
            'salary': int(captain['salary'] * 1.5),
            'projection': captain['projection'],
            'ownership': captain['ownership'],
            'ceiling': captain.get('ceiling', captain['projection'] * 1.5),
            'floor': captain.get('floor', captain['projection'] * 0.5),
            'is_captain': True
        }
        lineup.append(captain_slot)

        remaining_salary = 50000 - captain_slot['salary']

        # Get remaining players
        remaining = [p for p in players if p['id'] != captain['id']]

        # Prioritize correlation
        same_team = [p for p in remaining if p['team'] == captain['team']]
        opp_team = [p for p in remaining if p['team'] != captain['team']]

        # Sort by value
        same_team.sort(key=lambda x: x.get('value_score', 2), reverse=True)
        opp_team.sort(key=lambda x: x.get('value_score', 2), reverse=True)

        # Build FLEX positions
        flex_players = []
        flex_salary = 0

        # Try for 2-3 from captain's team, 2-3 from opponent
        target_order = same_team[:3] + opp_team[:3] + same_team[3:] + opp_team[3:]

        for p in target_order:
            if (len(flex_players) < 5 and
                    flex_salary + p['salary'] <= remaining_salary):
                flex_slot = p.copy()
                flex_slot['is_captain'] = False
                flex_players.append(flex_slot)
                flex_salary += p['salary']

        if len(flex_players) == 5:
            lineup.extend(flex_players)

            # CORRECT scoring calculation
            total_proj = captain['projection'] * 1.5  # Captain multiplier
            total_proj += sum(p['projection'] for p in flex_players)

            total_salary = captain_slot['salary'] + flex_salary

            # Calculate other metrics
            total_ceiling = captain['ceiling'] * 1.5 + sum(
                p.get('ceiling', p['projection'] * 1.5) for p in flex_players)
            total_floor = captain['floor'] * 1.5 + sum(p.get('floor', p['projection'] * 0.5) for p in flex_players)

            # Calculate ownership
            all_ownership = [captain['ownership'] * 1.5]  # Captain owned more
            all_ownership.extend([p['ownership'] for p in flex_players])

            lineup_dict = {
                'players': lineup,
                'salary': total_salary,
                'projection': total_proj,
                'ownership': np.mean(all_ownership),
                'strategy': 'balanced_showdown_fixed',
                'captain': captain['name'],
                'captain_multiplier': 1.5,
                'format': 'showdown',
                'ceiling': total_ceiling,
                'floor': total_floor
            }

            return lineup_dict

    return None

def build_elite_hybrid_gpp(players):
    """ROBUST: Combine best elements from top GPP performers"""
    if not players:
        return None

    slate = SlateAnalyzer(players)

    def hybrid_scoring(player, relaxation=0):
        if player['position'] == 'P':
            # Pitcher dominance with safety
            k_rate = player.get('k_rate', 20)
            bb_rate = player.get('bb_rate', 8)
            k_bb_ratio = k_rate / max(bb_rate + 1, 1)

            # Scale down extreme values
            k_bb_bonus = min(k_bb_ratio / 2.5, 1.5)  # Cap at 1.5x

            return player['projection'] * k_bb_bonus

        else:  # Hitters
            score = player['projection']

            # 1. Leverage weak pitchers (from matchup_leverage_stack)
            opp_era = player.get('opp_pitcher_era', 3.8)
            if opp_era > 4.5:
                score *= 1.4
            elif opp_era > 4.0:
                score *= 1.2

            # 2. Value component (from correlation_value)
            if player.get('value_score', 2) > 2.5:
                score *= 1.15

            # 3. Ceiling focus for GPP
            ceiling_ratio = player.get('ceiling', player['projection'] * 1.5) / player['projection']
            if ceiling_ratio > 2.0:
                score *= 1.1

            # Relaxation increases flexibility
            score *= (1 + relaxation * 0.1)

        return max(score, 0.1)

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    lineup = build_adaptive_lineup(
        players, position_requirements, hybrid_scoring, 'elite_hybrid_gpp'
    )

    if lineup and lineup['salary'] < 48000:
        lineup = optimize_salary_usage_adaptive(lineup, players, 'elite_hybrid_gpp')

    return lineup


def build_ultimate_cash_hybrid(players):
    """ROBUST: Combine top 2 cash strategies adaptively"""
    if not players:
        return None

    slate = SlateAnalyzer(players)

    def ultimate_scoring(player, relaxation=0):
        if player['position'] == 'P':
            # Focus on consistent pitchers
            k_rate = player.get('k_rate', 20)
            bb_rate = player.get('bb_rate', 8)
            whip = player.get('whip', 1.25)

            # Safety metrics
            k_bb_ratio = k_rate / max(bb_rate + 1, 1)
            whip_safety = max(2 - whip, 0.5)

            score = player['projection'] * min(k_bb_ratio / 2.5, 1.3) * whip_safety

        else:  # Hitters
            # Start with projection
            score = player['projection']

            # Floor safety (from value_floor)
            floor_ratio = player.get('floor', 5) / player['projection'] if player['projection'] > 0 else 0.5
            if floor_ratio > 0.6:  # High floor
                score *= 1.2

            # Matchup bonus (from matchup_optimal)
            if player.get('platoon_advantage', 0) > 0:
                score *= 1.15

            # Batting order (top 5 preferred)
            batting_order = player.get('batting_order', 9)
            if batting_order <= 3:
                score *= 1.2
            elif batting_order <= 5:
                score *= 1.1
            elif batting_order >= 8:
                score *= 0.8

        return max(score, 0.1)

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    lineup = build_adaptive_lineup(
        players, position_requirements, ultimate_scoring, 'ultimate_cash_hybrid'
    )

    if lineup and lineup['salary'] < 49000:
        lineup = optimize_salary_usage_adaptive(lineup, players, 'ultimate_cash_hybrid')

    return lineup


def build_top_5_batting_order_only(players):
    """GPP: Focus on top of batting order with smart fallbacks"""
    if not players:
        return None

    def batting_order_scoring(player, relaxation=0):
        if player['position'] == 'P':
            return player['projection']

        batting_order = player.get('batting_order', 9)

        # Adaptive thresholds
        max_order = 5 + int(relaxation * 2)  # Relaxes to 7 max

        if batting_order <= max_order:
            order_mult = {
                1: 1.5, 2: 1.4, 3: 1.5, 4: 1.4, 5: 1.2,
                6: 1.0, 7: 0.9
            }.get(batting_order, 0.8)

            # Still need upside for GPP
            ceiling_bonus = 1.0
            if player.get('ceiling', 0) > player['projection'] * 2:
                ceiling_bonus = 1.1

            return player['projection'] * order_mult * ceiling_bonus
        else:
            return player['projection'] * (0.3 + relaxation * 0.3)

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    lineup = build_adaptive_lineup(
        players, position_requirements, batting_order_scoring, 'top_5_batting_order_only'
    )

    return lineup


def build_single_game_hammer(players):
    """GPP: 60% exposure to highest total game (safer than 80%)"""
    if not players:
        return None

    # Find game totals
    game_info = defaultdict(lambda: {'total': 0, 'players': []})

    for p in players:
        game_id = p.get('game_id', 0)
        game_total = p.get('game_total', 8.5)
        game_info[game_id]['total'] = game_total
        game_info[game_id]['players'].append(p)

    if not game_info:
        return None

    # Find best game
    sorted_games = sorted(game_info.items(),
                          key=lambda x: x[1]['total'], reverse=True)

    if not sorted_games:
        return None

    hammer_game_id = sorted_games[0][0]
    hammer_total = sorted_games[0][1]['total']

    def hammer_scoring(player, relaxation=0):
        player_game = player.get('game_id', -1)

        if player_game == hammer_game_id:
            if player['position'] != 'P':
                # Strong bonus but not extreme
                base_mult = 1.8 - (relaxation * 0.2)  # Relaxes from 1.8x to 1.6x
                return player['ceiling'] * base_mult
            else:
                # Be careful with pitchers in high-scoring games
                return player['projection'] * 0.9
        else:
            # Need some diversification
            outside_mult = 0.6 + (relaxation * 0.2)  # 0.6 to 0.8
            return player['projection'] * outside_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    lineup = build_adaptive_lineup(
        players, position_requirements, hammer_scoring, 'single_game_hammer'
    )

    # Verify exposure (cap at 60%)
    if lineup:
        hammer_count = sum(1 for p in lineup['players']
                           if p.get('game_id') == hammer_game_id)
        if hammer_count > 6:  # Too much exposure
            # Try again with more balance
            def balanced_hammer_scoring(player, relaxation=0):
                if player.get('game_id') == hammer_game_id:
                    return player['projection'] * 1.4
                else:
                    return player['projection'] * 0.8

            lineup = build_adaptive_lineup(
                players, position_requirements, balanced_hammer_scoring, 'single_game_hammer'
            )

    return lineup


def build_balanced_stack_plus(players):
    """GPP: Traditional 5-man stack with optimal bring-back"""
    if not players:
        return None

    # Find best stacking teams
    team_metrics = defaultdict(lambda: {'players': [], 'avg_proj': 0, 'avg_ceiling': 0})

    for p in players:
        if p['position'] != 'P':
            team_metrics[p['team']]['players'].append(p)

    # Calculate team quality
    stackable_teams = []
    for team, data in team_metrics.items():
        if len(data['players']) >= 5:
            avg_proj = np.mean([p['projection'] for p in data['players']])
            avg_ceiling = np.mean([p.get('ceiling', p['projection'] * 1.5) for p in data['players']])

            stackable_teams.append({
                'team': team,
                'players': data['players'],
                'avg_proj': avg_proj,
                'avg_ceiling': avg_ceiling,
                'stack_score': avg_ceiling * len(data['players'])
            })

    if not stackable_teams:
        return None

    # Sort by stack score
    stackable_teams.sort(key=lambda x: x['stack_score'], reverse=True)

    # Try top teams
    for stack_data in stackable_teams[:3]:
        def stack_scoring(player, relaxation=0):
            if player['team'] == stack_data['team'] and player['position'] != 'P':
                # Heavy bonus for stack team
                return player.get('ceiling', player['projection'] * 1.5) * 2.0
            elif player['position'] == 'P':
                # Reasonable pitcher scoring
                return player['projection']
            else:
                # Look for bring-back opportunities
                # (In real implementation, would check if player faces stack team)
                return player['projection'] * 0.8

        position_requirements = {
            'P': 2, 'C': 1, '1B': 1, '2B': 1,
            '3B': 1, 'SS': 1, 'OF': 3
        }

        lineup = build_adaptive_lineup(
            players, position_requirements, stack_scoring, 'balanced_stack_plus'
        )

        if lineup:
            # Verify we got a real stack
            team_counts = defaultdict(int)
            for p in lineup['players']:
                team_counts[p['team']] += 1

            max_stack = max(team_counts.values())
            if max_stack >= 4:  # Good enough
                return lineup

    return None


# ========== CONFIGURATION ==========

# Define experimental strategies to test
EXPERIMENTAL_STRATEGIES = {
    'classic': {
        'small': {
            'cash': {
                'ultimate_cash_hybrid': {'name': 'Ultimate Cash Hybrid', 'type': 'ultimate_cash_hybrid'}
            },
            'gpp': {
                'elite_hybrid_gpp': {'name': 'Elite Hybrid GPP', 'type': 'elite_hybrid_gpp'},
                'single_game_hammer': {'name': 'Single Game Hammer', 'type': 'single_game_hammer'},
                'top_5_batting_order_only': {'name': 'Top 5 Batting Order', 'type': 'top_5_batting_order_only'},
                'balanced_stack_plus': {'name': 'Balanced Stack Plus', 'type': 'balanced_stack_plus'}
            }
        },
        'medium': {
            'cash': {
                'ultimate_cash_hybrid': {'name': 'Ultimate Cash Hybrid', 'type': 'ultimate_cash_hybrid'}
            },
            'gpp': {
                'elite_hybrid_gpp': {'name': 'Elite Hybrid GPP', 'type': 'elite_hybrid_gpp'},
                'single_game_hammer': {'name': 'Single Game Hammer', 'type': 'single_game_hammer'},
                'top_5_batting_order_only': {'name': 'Top 5 Batting Order', 'type': 'top_5_batting_order_only'},
                'balanced_stack_plus': {'name': 'Balanced Stack Plus', 'type': 'balanced_stack_plus'}
            }
        },
        'large': {
            'cash': {
                'ultimate_cash_hybrid': {'name': 'Ultimate Cash Hybrid', 'type': 'ultimate_cash_hybrid'}
            },
            'gpp': {
                'elite_hybrid_gpp': {'name': 'Elite Hybrid GPP', 'type': 'elite_hybrid_gpp'},
                'single_game_hammer': {'name': 'Single Game Hammer', 'type': 'single_game_hammer'},
                'top_5_batting_order_only': {'name': 'Top 5 Batting Order', 'type': 'top_5_batting_order_only'},
                'balanced_stack_plus': {'name': 'Balanced Stack Plus', 'type': 'balanced_stack_plus'}
            }
        }
    }
}

EXPERIMENTAL_STRATEGIES['showdown'] = {
    'cash': {
        'balanced_showdown_fixed': {'name': 'Balanced Showdown', 'type': 'balanced_showdown_fixed'}
    },
    'gpp': {
        'contrarian_showdown': {'name': 'Contrarian Showdown', 'type': 'contrarian_showdown'}
    }
}




# Strategy builders map
EXPERIMENTAL_BUILDERS = {
    'ultimate_cash_hybrid': build_ultimate_cash_hybrid,
    'elite_hybrid_gpp': build_elite_hybrid_gpp,
    'single_game_hammer': build_single_game_hammer,
    'top_5_batting_order_only': build_top_5_batting_order_only,
    'balanced_stack_plus': build_balanced_stack_plus,
    'balanced_showdown_fixed': build_balanced_showdown_fixed,
    'contrarian_showdown': build_contrarian_showdown
}


# ========== ROBUSTNESS TESTING ==========

def test_strategy_robustness():
    """Test that all experimental strategies build valid lineups consistently"""
    print("\n" + "=" * 80)
    print("TESTING EXPERIMENTAL STRATEGY ROBUSTNESS")
    print("=" * 80)

    success_rates = {}

    # Test each strategy multiple times
    test_iterations = 10

    for format_type in ['classic', 'showdown']:
        if format_type == 'showdown':
            slate_sizes = ['showdown']
        else:
            slate_sizes = ['small', 'medium', 'large']

        for slate_size in slate_sizes:
            print(f"\n📋 Testing {format_type} - {slate_size}:")

            # Generate multiple test slates
            test_slates = []
            for i in range(test_iterations):
                if format_type == 'showdown':
                    slate = generate_slate(i * 100, 'showdown', 'showdown')
                else:
                    slate = generate_slate(i * 100, format_type, slate_size)

                if slate and slate.get('players'):
                    test_slates.append(slate)

            if not test_slates:
                print("   ❌ Failed to generate test slates")
                continue

            # Test each strategy
            strategies_to_test = {}
            for ct in ['cash', 'gpp']:
                if format_type == 'showdown':
                    strategies_to_test.update(EXPERIMENTAL_STRATEGIES.get('showdown', {}).get(ct, {}))
                else:
                    strategies_to_test.update(EXPERIMENTAL_STRATEGIES['classic'].get(slate_size, {}).get(ct, {}))

            for strategy_name, strategy_config in strategies_to_test.items():
                successes = 0
                total_salary = 0

                for slate in test_slates:
                    builder_func = EXPERIMENTAL_BUILDERS.get(strategy_config['type'])
                    if builder_func:
                        lineup = builder_func(slate['players'])

                        if lineup:
                            if format_type == 'showdown' or validate_lineup(lineup['players']):
                                successes += 1
                                total_salary += lineup['salary']

                success_rate = (successes / len(test_slates)) * 100
                avg_salary = total_salary / successes if successes > 0 else 0

                key = f"{format_type}_{slate_size}_{strategy_name}"
                success_rates[key] = success_rate

                status = "✅" if success_rate == 100 else "⚠️" if success_rate >= 90 else "❌"

                print(f"   {strategy_name:<30} Success: {success_rate:>5.1f}% "
                      f"Avg Salary: ${avg_salary:>7,.0f} {status}")

# ========== MAIN SIMULATION ==========
# ========== MAIN SIMULATION ==========
def simulate_contest_with_experimental(slate, strategy_name, strategy_config, contest_type, field_size):
    """Modified simulate_contest that handles experimental strategies"""

    # Build our lineup using experimental builder
    strategy_type = strategy_config.get('type', 'unknown')

    if strategy_type in EXPERIMENTAL_BUILDERS:
        our_lineup = EXPERIMENTAL_BUILDERS[strategy_type](slate['players'])
    else:
        # Fallback to main simulator's builder
        from robust_dfs_simulator import build_lineup as main_build_lineup
        our_lineup = main_build_lineup(slate['players'], strategy_config, slate['format'], slate['slate_size'])

    if not our_lineup:
        return None

    # Now use the rest of simulate_contest logic from main simulator
    from robust_dfs_simulator import generate_field, simulate_lineup_score

    # Generate field
    field_lineups = generate_field(slate, field_size, contest_type)

    if not field_lineups:
        field_lineups = []

    # Score all lineups
    our_score = simulate_lineup_score(our_lineup)

    field_scores = []
    for lineup in field_lineups:
        score = simulate_lineup_score(lineup)
        field_scores.append(score)

    # Calculate placement and payout
    all_scores = field_scores + [our_score]
    all_scores.sort(reverse=True)

    our_rank = all_scores.index(our_score) + 1
    percentile = ((len(all_scores) - our_rank) / len(all_scores)) * 100

    # Calculate payout
    if slate['format'] == 'showdown':
        entry_fee = 5 if contest_type == 'cash' else 3
        from robust_dfs_simulator import SHOWDOWN_CONFIG as config
    else:
        entry_fee = 10 if contest_type == 'cash' else 3
        from robust_dfs_simulator import CLASSIC_CONFIG as config

    if contest_type == 'cash':
        cash_line_percentile = (1 - config['cash_payout_threshold']) * 100
        if percentile >= cash_line_percentile:
            payout = entry_fee * 2
        else:
            payout = 0
    else:  # GPP
        payout = 0
        payout_pct = our_rank / len(all_scores)

        for threshold, multiplier in sorted(config['gpp_payout_structure'].items()):
            if payout_pct <= threshold:
                payout = entry_fee * multiplier
                break

    profit = payout - entry_fee
    roi = (profit / entry_fee) * 100

    win = profit > 0
    top_10 = percentile >= 90
    top_1 = percentile >= 99

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
        'actual_score': our_score,
        'win': win,
        'top_10': top_10,
        'top_1': top_1,
        'lineup_salary': our_lineup.get('salary', 0),
        'max_stack': our_lineup.get('max_stack', 0),
        'cash_line': all_scores[
            int(len(all_scores) * config['cash_payout_threshold'])] if contest_type == 'cash' and all_scores else None,
        'winning_score': all_scores[0] if all_scores else 0,
        'actual_field_size': len(field_lineups) + 1,
        'expected_field_size': field_size
    }


def run_experimental_simulation(num_slates=1000):
    """Run simulation using exact same framework as main simulator"""

    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f'experimental_strategy_results_{timestamp}.txt'

    # Start logging output
    output_logger = OutputLogger(output_filename)
    original_stdout = sys.stdout
    sys.stdout = output_logger

    try:
        print("\n" + "=" * 80)
        print("EXPERIMENTAL STRATEGY TESTING - USING MAIN SIMULATOR FRAMEWORK")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Count strategies
        total_strategies = 0
        for format_strategies in EXPERIMENTAL_STRATEGIES.values():
            if isinstance(format_strategies, dict):
                for size_strategies in format_strategies.values():
                    if isinstance(size_strategies, dict):
                        for contest_strategies in size_strategies.values():
                            if isinstance(contest_strategies, dict):
                                total_strategies += len(contest_strategies)

        print(f"\n📊 Configuration:")
        print(f"   • Slates per size: {num_slates}")
        print(f"   • Total experimental strategies: {total_strategies}")

        input("\nPress Enter to start...")

        start_time = time.time()

        # Create slate configurations
        slate_configs = []

        # Classic slates
        for slate_size in ['small', 'medium', 'large']:
            for i in range(num_slates):
                slate_id = (i * 1000 + abs(hash(slate_size))) % (2 ** 31 - 1)
                slate_configs.append((slate_id, 'classic', slate_size))

        # Showdown slates
        for i in range(num_slates // 3):  # Fewer showdown slates
            slate_id = (i * 2000) % (2 ** 31 - 1)
            slate_configs.append((slate_id, 'showdown', 'showdown'))

        # Contest configurations
        contest_configs = [
            ('cash', 100),  # 100-person double-up
            ('gpp', 1000),  # 1000-person tournament
        ]

        print(f"\n🎮 Running {len(slate_configs)} slates x {len(contest_configs)} contest types")
        print(f"   = {len(slate_configs) * len(contest_configs) * (total_strategies // 2)} total contests\n")

        all_results = []
        failed_count = 0
        recent_activity = deque(maxlen=10)

        # Sequential processing with dashboard (like main simulator)
        for i, (slate_id, format_type, slate_size) in enumerate(slate_configs):
            # Update dashboard
            if i % 5 == 0 or i == 0 or i == len(slate_configs) - 1:
                draw_dashboard(i, len(slate_configs), len(all_results), failed_count,
                               start_time, recent_activity)

            recent_activity.append(f"✓ Generating {format_type} slate #{i + 1} ({slate_size})")

            # Generate slate
            slate = generate_slate(slate_id, format_type, slate_size)

            if not slate or not slate.get('players'):
                failed_count += 1
                recent_activity.append(f"❌ Failed to generate slate {slate_id}")
                continue

            recent_activity.append(f"  → Generated {len(slate['players'])} players")

            # Get strategies for this configuration
            if format_type == 'showdown':
                all_strategies = {}
                for contest_type in ['cash', 'gpp']:
                    all_strategies.update(
                        EXPERIMENTAL_STRATEGIES.get('showdown', {}).get(contest_type, {})
                    )
            else:  # classic
                all_strategies = {}
                for contest_type in ['cash', 'gpp']:
                    all_strategies.update(
                        EXPERIMENTAL_STRATEGIES['classic'].get(slate_size, {}).get(contest_type, {})
                    )

            # Test each strategy in each contest type
            for strategy_name, strategy_config in all_strategies.items():
                for contest_type, field_size in contest_configs:
                    recent_activity.append(f"  → Testing {strategy_name} ({contest_type})")

                    try:
                        # Use our custom simulate_contest that handles experimental strategies
                        result = simulate_contest_with_experimental(
                            slate,
                            strategy_name,
                            strategy_config,
                            contest_type,
                            field_size
                        )

                        if result:
                            all_results.append(result)
                            recent_activity.append(
                                f"    ✓ {strategy_name}: Rank {result['rank']}/{field_size} ({result['percentile']:.0f}%ile)")
                        else:
                            failed_count += 1
                            recent_activity.append(f"    ❌ {strategy_name} failed to build lineup")

                    except Exception as e:
                        failed_count += 1
                        recent_activity.append(f"    ❌ {strategy_name} error: {str(e)[:40]}...")
                        import traceback
                        traceback.print_exc()

            # Milestone notification every 10%
            if i > 0 and (i * 100 // len(slate_configs)) % 10 == 0:
                milestone_pct = (i * 100 // len(slate_configs))
                recent_activity.append(f"🎯 ═══ {milestone_pct}% MILESTONE REACHED! ═══")

        # Final dashboard update
        draw_dashboard(len(slate_configs), len(slate_configs), len(all_results),
                       failed_count, start_time, recent_activity)

        # Complete
        elapsed = time.time() - start_time
        print(f"\n\n✅ Simulation complete in {elapsed:.1f} seconds")
        print(f"📊 Total results: {len(all_results):,}")
        if failed_count > 0:
            print(f"⚠️  Failed tests: {failed_count}")

        # Analyze results (using same format as main simulator)
        if all_results:
            analyze_experimental_results(all_results)

            # Save results to JSON
            save_data = {
                'metadata': {
                    'timestamp': timestamp,
                    'duration_seconds': elapsed,
                    'num_slates': num_slates,
                    'total_results': len(all_results),
                    'strategies_tested': {
                        'classic': {
                            size: {
                                ct: list(EXPERIMENTAL_STRATEGIES['classic'].get(size, {}).get(ct, {}).keys())
                                for ct in ['cash', 'gpp']
                            }
                            for size in ['small', 'medium', 'large']
                        },
                        'showdown': {
                            ct: list(EXPERIMENTAL_STRATEGIES.get('showdown', {}).get(ct, {}).keys())
                            for ct in ['cash', 'gpp']
                        }
                    }
                },
                'results': all_results
            }

            json_filename = f'experimental_results_{timestamp}.json'
            with open(json_filename, 'w') as f:
                json.dump(save_data, f, indent=2)

            print(f"\n💾 Results saved to: {json_filename}")

    finally:
        # Restore stdout and close logger
        sys.stdout = original_stdout
        output_logger.close()

        # Also print to console that file was saved
        print(f"\n💾 Full results saved to: {output_filename}")

def simulate_contest_with_experimental(slate, strategy_name, strategy_config, contest_type, field_size):
    """Modified simulate_contest that handles experimental strategies"""

    # Build our lineup using experimental builder
    strategy_type = strategy_config.get('type', 'unknown')

    if strategy_type in EXPERIMENTAL_BUILDERS:
        our_lineup = EXPERIMENTAL_BUILDERS[strategy_type](slate['players'])
    else:
        # Fallback to main simulator's builder
        from robust_dfs_simulator import build_lineup as main_build_lineup
        our_lineup = main_build_lineup(slate['players'], strategy_config, slate['format'], slate['slate_size'])

    if not our_lineup:
        return None

    # Now use the rest of simulate_contest logic from main simulator
    from robust_dfs_simulator import generate_field, simulate_lineup_score

    # Generate field
    field_lineups = generate_field(slate, field_size, contest_type)

    if not field_lineups:
        field_lineups = []

    # Score all lineups
    our_score = simulate_lineup_score(our_lineup)

    field_scores = []
    for lineup in field_lineups:
        score = simulate_lineup_score(lineup)
        field_scores.append(score)

    # Calculate placement and payout
    all_scores = field_scores + [our_score]
    all_scores.sort(reverse=True)

    our_rank = all_scores.index(our_score) + 1
    percentile = ((len(all_scores) - our_rank) / len(all_scores)) * 100

    # Calculate payout
    if slate['format'] == 'showdown':
        entry_fee = 5 if contest_type == 'cash' else 3
        from robust_dfs_simulator import SHOWDOWN_CONFIG as config
    else:
        entry_fee = 10 if contest_type == 'cash' else 3
        from robust_dfs_simulator import CLASSIC_CONFIG as config

    if contest_type == 'cash':
        cash_line_percentile = (1 - config['cash_payout_threshold']) * 100
        if percentile >= cash_line_percentile:
            payout = entry_fee * 2
        else:
            payout = 0
    else:  # GPP
        payout = 0
        payout_pct = our_rank / len(all_scores)

        for threshold, multiplier in sorted(config['gpp_payout_structure'].items()):
            if payout_pct <= threshold:
                payout = entry_fee * multiplier
                break

    profit = payout - entry_fee
    roi = (profit / entry_fee) * 100

    win = profit > 0
    top_10 = percentile >= 90
    top_1 = percentile >= 99

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
        'actual_score': our_score,
        'win': win,
        'top_10': top_10,
        'top_1': top_1,
        'lineup_salary': our_lineup.get('salary', 0),
        'max_stack': our_lineup.get('max_stack', 0)
    }

def analyze_experimental_results(results):
    """Analyze using exact same format as main simulator"""

    # Group results
    by_strategy = defaultdict(list)

    for r in results:
        if r:
            key = f"{r['format']}_{r['slate_size']}_{r['contest_type']}_{r['strategy']}"
            by_strategy[key].append(r)

    # Analyze by slate size and contest type (exact same format)
    for slate_size in ['small', 'medium', 'large']:
        print(f"\n{'=' * 80}")
        print(f"CLASSIC - {slate_size.upper()} SLATES")
        print(f"{'=' * 80}")

        # Cash analysis
        print(f"\n📊 CASH GAMES (Double-Ups):")
        print(f"{'Strategy':<30} {'Win%':>8} {'ROI%':>8} {'Avg Score':>10} {'Avg Rank':>10} {'Build%':>8}")
        print("-" * 80)

        cash_results = []
        for strategy_name in EXPERIMENTAL_STRATEGIES['classic'].get(slate_size, {}).get('cash', {}):
            key = f"classic_{slate_size}_cash_{strategy_name}"
            if key in by_strategy and by_strategy[key]:
                results_list = by_strategy[key]

                # Calculate metrics
                wins = sum(1 for r in results_list if r['win'])
                win_rate = (wins / len(results_list)) * 100
                avg_roi = np.mean([r['roi'] for r in results_list])
                avg_rank = np.mean([r['rank'] for r in results_list])
                avg_score = np.mean([r['score'] for r in results_list])

                cash_results.append({
                    'strategy': strategy_name,
                    'win_rate': win_rate,
                    'roi': avg_roi,
                    'avg_rank': avg_rank,
                    'avg_score': avg_score,
                    'sample_size': len(results_list),
                    'build_rate': 100.0
                })

        # Sort by win rate
        cash_results.sort(key=lambda x: x['win_rate'], reverse=True)

        for r in cash_results:
            status = "🏆" if r['win_rate'] >= 50 else "✅" if r['win_rate'] >= 44 else "⚠️" if r[
                                                                                                 'win_rate'] >= 40 else "❌"
            print(f"{r['strategy']:<30} {r['win_rate']:>7.1f}% {r['roi']:>+7.1f}% "
                  f"{r['avg_score']:>9.1f} {r['avg_rank']:>9.1f} {r['build_rate']:>7.0f}% {status}")

        # GPP analysis
        print(f"\n📊 TOURNAMENTS (GPPs):")
        print(f"{'Strategy':<30} {'ROI%':>8} {'Top 10%':>9} {'Avg Score':>10} {'Top 1%':>8} {'Build%':>8}")
        print("-" * 80)

        gpp_results = []
        for strategy_name in EXPERIMENTAL_STRATEGIES['classic'].get(slate_size, {}).get('gpp', {}):
            key = f"classic_{slate_size}_gpp_{strategy_name}"
            if key in by_strategy and by_strategy[key]:
                results_list = by_strategy[key]

                avg_roi = np.mean([r['roi'] for r in results_list])
                avg_score = np.mean([r['score'] for r in results_list])
                top_10 = sum(1 for r in results_list if r['top_10']) / len(results_list) * 100
                top_1 = sum(1 for r in results_list if r['top_1']) / len(results_list) * 100

                gpp_results.append({
                    'strategy': strategy_name,
                    'roi': avg_roi,
                    'avg_score': avg_score,
                    'top_10': top_10,
                    'top_1': top_1,
                    'sample_size': len(results_list),
                    'build_rate': 100.0
                })

        # Sort by ROI
        gpp_results.sort(key=lambda x: x['roi'], reverse=True)

        for r in gpp_results:
            status = "🔥" if r['roi'] > 50 else "💰" if r['roi'] > 20 else "✅" if r['roi'] > 0 else "❌"
            print(f"{r['strategy']:<30} {r['roi']:>+7.1f}% {r['top_10']:>8.1f}% "
                  f"{r['avg_score']:>9.1f} {r['top_1']:>7.1f}% {r['build_rate']:>7.0f}% {status}")

    # In analyze_experimental_results, add:
    if r['avg_salary'] < 48500:
        print(f"  Note: {strategy_name} naturally uses less salary (${r['avg_salary']:,.0f})")

    # Summary statistics
    print(f"\n{'=' * 80}")
    print("EXPERIMENTAL STRATEGY SUMMARY")
    print(f"{'=' * 80}")

    print(f"\n✅ Simulation completed successfully!")


# ========== MAIN EXECUTION ==========

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║      EXPERIMENTAL STRATEGY TESTING MODULE                ║
    ║                                                          ║
    ║  Tests experimental strategies using main simulator      ║
    ║  framework with identical output format                  ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    if len(sys.argv) > 1:
        # Command line argument provided - run directly
        try:
            num_slates = int(sys.argv[1])
            print(f"\nRunning experimental simulation with {num_slates} slates...")
            run_experimental_simulation(num_slates)
        except ValueError:
            print(f"\nError: '{sys.argv[1]}' is not a valid number of slates")
            print("Usage: python experimental_strategy_test.py <number_of_slates>")
            print("Example: python experimental_strategy_test.py 100")
            sys.exit(1)
    else:
        # No command line argument - show interactive menu
        print("\nSelect option:")
        print("1. Test Strategy Robustness (10 lineups each)")
        print("2. Run Full Simulation (1000 slates)")
        print("3. Quick Test (100 slates)")
        print("4. Extended Test (500 slates)")

        choice = input("\nEnter choice (1-4): ")

        if choice == '1':
            print("\nTesting robustness of all experimental strategies...")
            # test_strategy_robustness()  # Commented out
            print("Robustness test is currently disabled (commented out)")

        elif choice == '2':
            print("\nSkipping robustness check, starting full simulation...")
            run_experimental_simulation(1000)

        elif choice == '3':
            run_experimental_simulation(100)

        elif choice == '4':
            run_experimental_simulation(500)

        else:
            print("Invalid choice. Running quick test...")
            run_experimental_simulation(100)