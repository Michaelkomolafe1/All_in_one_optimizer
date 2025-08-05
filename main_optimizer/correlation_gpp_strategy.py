# correlation_gpp_strategy.py
"""
GPP Strategy Based on Stack Correlation Data
- 83.2% of winners use 4-5 man stacks
- 3-4 hitters have highest correlation (0.654)
- Focus on consecutive batting spots
- Road team preference
"""

import random
import numpy as np


def build_correlation_gpp(players, slate_size='medium'):
    """
    GPP strategy using correlation data:
    - 56.7% chance of 5-man stack
    - 26.5% chance of 4-man stack
    - Focus on 3-4, 2-3, 1-2 correlations

    Args:
        players: List of player dictionaries
        slate_size: Size of slate ('small', 'medium', 'large') - affects stack preferences
    """

    # Adjust stack weights based on slate size
    if slate_size == 'small':
        # Smaller slates favor tighter stacks
        stack_weights = [60, 25]  # More 5-man stacks
    elif slate_size == 'large':
        # Larger slates can use more 4-man stacks
        stack_weights = [50, 35]  # More balanced
    else:
        # Default medium slate weights from data
        stack_weights = [56.7, 26.5]

    # Decide primary stack size based on win rates
    stack_type = random.choices(
        ['5-man', '4-man'],
        weights=stack_weights,
        k=1
    )[0]

    # Analyze teams for stacking
    team_stack_scores = analyze_teams_for_correlation_stacking(players)

    if not team_stack_scores:
        return None

    # Build primary stack
    if stack_type == '5-man':
        lineup = build_five_man_correlation_stack(players, team_stack_scores, slate_size)
    else:
        lineup = build_four_man_correlation_stack(players, team_stack_scores, slate_size)

    return lineup


def analyze_teams_for_correlation_stacking(players):
    """Score teams based on correlation potential"""

    teams = {}

    for p in players:
        if p['position'] == 'P':
            continue

        team = p['team']
        if team not in teams:
            teams[team] = {
                'players': [],
                'game_total': p.get('game_data', {}).get('game_total', 9.0),
                'team_total': p.get('game_data', {}).get('team_total', 4.5),
                'is_road': not p.get('is_home', True),
                'correlation_score': 0
            }
        teams[team]['players'].append(p)

    # Score each team
    for team, data in teams.items():
        # Sort by batting order
        data['players'].sort(key=lambda x: x.get('batting_order', 9))

        # Base score from game environment
        score = data['team_total'] * 2

        # Road bonus (51.6% of PAs)
        if data['is_road']:
            score *= 1.05

        # Check for strong correlations (consecutive hitters)
        correlation_bonus = calculate_team_correlation_potential(data['players'])
        score *= correlation_bonus

        # Ownership leverage
        avg_ownership = np.mean([p.get('ownership', 15) for p in data['players'][:5]])
        if avg_ownership < 20:
            score *= 1.15  # Low owned stacks

        data['correlation_score'] = score

    return teams


def calculate_team_correlation_potential(players):
    """Calculate correlation strength based on batting order"""

    if len(players) < 4:
        return 0.5

    # Get batting orders
    orders = [p.get('batting_order', 9) for p in players[:6]]

    # Check for key correlations
    bonus = 1.0

    # 3-4 hitters (strongest correlation)
    if 3 in orders and 4 in orders:
        bonus *= 1.3

    # 2-3 hitters
    if 2 in orders and 3 in orders:
        bonus *= 1.25

    # 1-2 hitters
    if 1 in orders and 2 in orders:
        bonus *= 1.2

    # Check for consecutive runs
    consecutive_count = count_consecutive_spots(orders)
    if consecutive_count >= 5:
        bonus *= 1.4
    elif consecutive_count >= 4:
        bonus *= 1.25
    elif consecutive_count >= 3:
        bonus *= 1.15

    return bonus


def count_consecutive_spots(orders):
    """Count maximum consecutive batting spots"""

    if not orders:
        return 0

    orders_set = set(orders)
    max_consecutive = 1
    current_consecutive = 1

    for i in range(1, 10):
        if i in orders_set and (i - 1) in orders_set:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 1 if i in orders_set else 0

    # Check 9-1 wraparound
    if 9 in orders_set and 1 in orders_set:
        max_consecutive = max(max_consecutive, 2)

    return max_consecutive


def build_five_man_correlation_stack(players, team_scores, slate_size):
    """Build 5-man stack with correlation focus"""

    # Sort teams by correlation score
    sorted_teams = sorted(team_scores.items(), key=lambda x: x[1]['correlation_score'], reverse=True)

    # On smaller slates, be more selective
    max_teams_to_try = 3 if slate_size == 'small' else 5

    for team, data in sorted_teams[:max_teams_to_try]:
        team_players = data['players']

        if len(team_players) < 5:
            continue

        # Find best 5 consecutive hitters
        best_stack = find_best_consecutive_five(team_players)

        if best_stack:
            # Get pitchers for this stack
            opposing_pitcher = find_opposing_pitcher(players, team)
            avoid_pitchers = [opposing_pitcher] if opposing_pitcher else []

            # Get best available pitchers
            pitchers = select_gpp_pitchers(players, avoid_pitchers)

            if len(pitchers) == 2:
                # Decide secondary stack pattern
                remaining_salary = 50000 - sum(p.get('salary', 5000) for p in best_stack + pitchers)

                # 39.1% naked, 33.6% 2-man, 27.1% 3-man
                pattern = random.choices(
                    ['naked', '2-man', '3-man'],
                    weights=[39.1, 33.6, 27.1],
                    k=1
                )[0]

                return complete_correlation_lineup(
                    best_stack + pitchers,
                    players,
                    team,
                    pattern,
                    remaining_salary
                )

    return None


def find_best_consecutive_five(team_players):
    """Find the best 5 consecutive hitters by batting order"""

    if len(team_players) < 5:
        return None

    # Try all possible 5-consecutive combinations
    best_combo = None
    best_score = 0

    for start in range(len(team_players) - 4):
        combo = team_players[start:start + 5]

        # Check if actually consecutive
        orders = [p.get('batting_order', 9) for p in combo]
        if max(orders) - min(orders) == 4:  # Consecutive
            # Score based on correlations
            score = sum(p['projection'] for p in combo)

            # Bonus for including 3-4 hitters
            if 3 in orders and 4 in orders:
                score *= 1.3
            if 2 in orders and 3 in orders:
                score *= 1.2

            if score > best_score:
                best_score = score
                best_combo = combo

    # Also check wraparound (7-8-9-1-2)
    if len(team_players) >= 9:
        wraparound = []
        for order in [7, 8, 9, 1, 2]:
            player = next((p for p in team_players if p.get('batting_order') == order), None)
            if player:
                wraparound.append(player)

        if len(wraparound) == 5:
            score = sum(p['projection'] for p in wraparound)
            score *= 1.15  # Wraparound bonus

            if score > best_score:
                best_combo = wraparound

    return best_combo


def build_four_man_correlation_stack(players, team_scores, slate_size):
    """Build 4-man stack with correlation focus"""

    # Sort teams by correlation score
    sorted_teams = sorted(team_scores.items(), key=lambda x: x[1]['correlation_score'], reverse=True)

    # On smaller slates, be more selective
    max_teams_to_try = 3 if slate_size == 'small' else 5

    for team, data in sorted_teams[:max_teams_to_try]:
        team_players = data['players']

        if len(team_players) < 4:
            continue

        # Find best 4 consecutive hitters
        best_stack = find_best_consecutive_four(team_players)

        if best_stack:
            # Get pitchers for this stack
            opposing_pitcher = find_opposing_pitcher(players, team)
            avoid_pitchers = [opposing_pitcher] if opposing_pitcher else []

            # Get best available pitchers
            pitchers = select_gpp_pitchers(players, avoid_pitchers)

            if len(pitchers) == 2:
                # Decide secondary stack pattern for 4-man
                remaining_salary = 50000 - sum(p['salary'] for p in best_stack + pitchers)

                # Based on data: 37.2% use 2-man secondary, 23.2% naked
                pattern = random.choices(
                    ['2-man', 'naked', '3-man', '4-man'],
                    weights=[37.2, 23.2, 20.9, 18.6],
                    k=1
                )[0]

                return complete_correlation_lineup(
                    best_stack + pitchers,
                    players,
                    team,
                    pattern,
                    remaining_salary
                )

    return None


def find_best_consecutive_four(team_players):
    """Find the best 4 consecutive hitters by batting order"""

    if len(team_players) < 4:
        return None

    # Try all possible 4-consecutive combinations
    best_combo = None
    best_score = 0

    for start in range(len(team_players) - 3):
        combo = team_players[start:start + 4]

        # Check if actually consecutive
        orders = [p.get('batting_order', 9) for p in combo]
        if max(orders) - min(orders) == 3:  # Consecutive
            # Score based on correlations
            score = sum(p['projection'] for p in combo)

            # Bonus for including 3-4 hitters
            if 3 in orders and 4 in orders:
                score *= 1.3

            if score > best_score:
                best_score = score
                best_combo = combo

    return best_combo


def select_gpp_pitchers(players, avoid_pitchers):
    """Select tournament pitchers (K-upside focus)"""

    pitchers = [p for p in players if p['position'] == 'P' and p not in avoid_pitchers]

    # Score for GPP (K-rate is king)
    for p in pitchers:
        k_rate = p.get('k_rate', 20)
        ownership = p.get('ownership', 20)

        # K-rate score
        if k_rate >= 28:
            k_score = 2.0
        elif k_rate >= 25:
            k_score = 1.5
        else:
            k_score = 1.0

        # Ownership leverage
        if ownership < 10:
            own_score = 1.4
        elif ownership < 20:
            own_score = 1.2
        else:
            own_score = 0.9

        p['gpp_score'] = p['projection'] * k_score * own_score

    pitchers.sort(key=lambda x: x.get('gpp_score', 0), reverse=True)
    return pitchers[:2]


def complete_correlation_lineup(current_lineup, all_players, primary_team, pattern, remaining_salary):
    """Complete lineup based on secondary pattern"""

    available = [p for p in all_players if p not in current_lineup and p['team'] != primary_team]

    if pattern == '2-man':
        # Find a correlated 2-man mini-stack
        mini_stack = find_mini_stack(available, remaining_salary)
        if mini_stack:
            current_lineup.extend(mini_stack)

    elif pattern == '3-man':
        # Find a 3-man secondary stack
        secondary_stack = find_secondary_stack(available, remaining_salary, 3)
        if secondary_stack:
            current_lineup.extend(secondary_stack)

    # Fill remaining spots with best available
    return fill_remaining_spots(current_lineup, available, remaining_salary)


def find_opposing_pitcher(all_players, team):
    """Find pitcher facing this team"""

    # This is simplified - in real implementation you'd have game matchup data
    opposing_pitchers = [
        p for p in all_players
        if p['position'] == 'P' and p.get('opponent') == team
    ]

    if opposing_pitchers:
        return opposing_pitchers[0]
    return None


def find_mini_stack(available_players, budget):
    """Find a 2-man mini-stack within budget"""

    # Group by team
    teams = {}
    for p in available_players:
        if p['position'] != 'P':
            team = p['team']
            if team not in teams:
                teams[team] = []
            teams[team].append(p)

    # Find best 2-man combo
    best_combo = None
    best_score = 0

    for team, players in teams.items():
        if len(players) >= 2:
            # Sort by batting order
            players.sort(key=lambda x: x.get('batting_order', 9))

            # Check consecutive pairs
            for i in range(len(players) - 1):
                if players[i].get('batting_order', 9) + 1 == players[i + 1].get('batting_order', 9):
                    combo = [players[i], players[i + 1]]
                    cost = sum(p['salary'] for p in combo)

                    if cost <= budget - 3000:  # Leave room for final player
                        score = sum(p['projection'] for p in combo)
                        # Bonus for 3-4 or 1-2 combos
                        if players[i].get('batting_order') in [3, 1]:
                            score *= 1.2

                        if score > best_score:
                            best_score = score
                            best_combo = combo

    return best_combo


def find_secondary_stack(available_players, budget, stack_size):
    """Find a secondary stack of specified size"""

    # Group by team
    teams = {}
    for p in available_players:
        if p['position'] != 'P':
            team = p['team']
            if team not in teams:
                teams[team] = []
            teams[team].append(p)

    # Find best stack
    best_stack = None
    best_score = 0

    for team, players in teams.items():
        if len(players) >= stack_size:
            # Sort by projection
            players.sort(key=lambda x: x['projection'], reverse=True)

            # Take top N players
            stack = players[:stack_size]
            cost = sum(p['salary'] for p in stack)

            if cost <= budget:
                score = sum(p['projection'] for p in stack)

                # Bonus for consecutive batting orders
                orders = sorted([p.get('batting_order', 9) for p in stack])
                if len(orders) == stack_size and max(orders) - min(orders) == stack_size - 1:
                    score *= 1.15

                if score > best_score:
                    best_score = score
                    best_stack = stack

    return best_stack


def fill_remaining_spots(current_lineup, available_players, remaining_salary):
    """Fill remaining roster spots to reach 10 players"""

    if len(current_lineup) >= 10:
        return complete_lineup_with_positions(current_lineup[:10])

    # Determine what positions we need
    positions_filled = {}
    for p in current_lineup:
        pos = p['position']
        positions_filled[pos] = positions_filled.get(pos, 0) + 1

    # Position requirements
    requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Fill remaining spots
    salary_left = remaining_salary

    # Sort available by value (projection/salary)
    available = [p for p in available_players if p not in current_lineup]
    available.sort(key=lambda x: x['projection'] / (x['salary'] / 1000), reverse=True)

    for player in available:
        if len(current_lineup) >= 10:
            break

        pos = player['position']
        current_count = positions_filled.get(pos, 0)
        max_allowed = requirements.get(pos, 0)

        if current_count < max_allowed and player['salary'] <= salary_left:
            current_lineup.append(player)
            positions_filled[pos] = current_count + 1
            salary_left -= player['salary']

    # If still not 10, add cheapest available
    if len(current_lineup) < 10:
        remaining = [p for p in available_players if p not in current_lineup]
        remaining.sort(key=lambda x: x['salary'])

        for p in remaining:
            if len(current_lineup) >= 10:
                break
            if p['salary'] <= salary_left:
                current_lineup.append(p)
                salary_left -= p['salary']

    return complete_lineup_with_positions(current_lineup)


def complete_lineup_with_positions(players):
    """Convert player list to proper lineup format"""

    if len(players) != 10:
        return None

    return {
        'players': players,
        'salary': sum(p['salary'] for p in players),
        'projection': sum(p['projection'] for p in players),
        'stack_info': analyze_stack_pattern(players)
    }


def analyze_stack_pattern(players):
    """Analyze the stack pattern of the lineup"""

    teams = {}
    for p in players:
        if p['position'] != 'P':
            team = p['team']
            teams[team] = teams.get(team, 0) + 1

    # Find primary stack
    if teams:
        primary_team = max(teams.items(), key=lambda x: x[1])
        primary_size = primary_team[1]

        # Determine pattern
        if primary_size >= 5:
            pattern = "5-man ({})".format(primary_team[0])
        elif primary_size >= 4:
            pattern = "4-man ({})".format(primary_team[0])
        else:
            pattern = "No major stack"

        return {
            'pattern': pattern,
            'primary_size': primary_size,
            'teams_used': len(teams)
        }

    return {'pattern': 'Unknown', 'primary_size': 0, 'teams_used': 0}