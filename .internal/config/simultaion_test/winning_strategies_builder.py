#!/usr/bin/env python3
"""
COMPLETE WINNING STRATEGIES BUILDER
===================================
All winning strategy implementations including missing ones
"""

from collections import defaultdict
import numpy as np
import random

# Import configs from your simulator
from simulation import SHOWDOWN_CONFIG, CLASSIC_CONFIG, create_showdown_lineup_result, create_classic_lineup_result


# ============== HELPER FUNCTIONS ==============

def build_by_metric(players, metric_name):
    """Generic builder that sorts by a metric and builds lineup"""
    players.sort(key=lambda x: x.get(metric_name, 0), reverse=True)

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    for player in players:
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
            break

    if len(lineup) == 10:
        return create_classic_lineup_result(lineup)
    return None


# ============== SHOWDOWN STRATEGIES ==============

def build_ace_only(players, strategy=None):
    """Ace Only - Best Showdown Cash (75.6% win rate)"""
    pitchers = [p for p in players if p['position'] == 'P' and p['projection'] >= 25]
    if not pitchers:
        pitchers = [p for p in players if p['position'] == 'P']

    if not pitchers:
        return None

    pitchers.sort(key=lambda x: x['projection'], reverse=True)
    captain = pitchers[0]

    lineup = [captain]
    salary = int(captain['salary'] * 1.5)
    teams_used = defaultdict(int)
    teams_used[captain['team']] = 1

    # Get high floor hitters
    hitters = [p for p in players if p['position'] != 'P']
    for h in hitters:
        h['floor_value'] = h.get('floor', h['projection'] * 0.7) / (h['salary'] / 1000)

    hitters.sort(key=lambda x: x['floor_value'], reverse=True)

    for hitter in hitters:
        if len(lineup) >= 6:
            break

        if salary + hitter['salary'] <= 50000:
            lineup.append(hitter)
            salary += hitter['salary']
            teams_used[hitter['team']] = teams_used.get(hitter['team'], 0) + 1

    if len(lineup) == 6 and len(teams_used) >= 2:
        return create_showdown_lineup_result(lineup, captain)
    return None


def build_balanced_game_3_3(players, strategy=None):
    """Balanced 3-3 - Best Overall Showdown (74.3% cash, 344% GPP)"""
    teams = defaultdict(list)
    for p in players:
        teams[p['team']].append(p)

    if len(teams) != 2:
        return None

    team_list = list(teams.keys())
    team1_players = teams[team_list[0]]
    team2_players = teams[team_list[1]]

    # Sort by projection
    team1_players.sort(key=lambda x: x['projection'], reverse=True)
    team2_players.sort(key=lambda x: x['projection'], reverse=True)

    best_lineup = None
    best_score = 0

    # Try different captain selections
    for captain_team_idx in [0, 1]:
        captain_pool = team1_players if captain_team_idx == 0 else team2_players
        other_pool = team2_players if captain_team_idx == 0 else team1_players

        for captain in captain_pool[:3]:
            lineup = [captain]
            salary = int(captain['salary'] * 1.5)

            # Add 2 more from captain's team
            captain_team_added = 0
            for p in captain_pool:
                if p != captain and captain_team_added < 2:
                    if salary + p['salary'] <= 50000 - 15000:  # Leave room
                        lineup.append(p)
                        salary += p['salary']
                        captain_team_added += 1

            # Add 3 from other team
            other_team_added = 0
            for p in other_pool:
                if other_team_added < 3:
                    if salary + p['salary'] <= 50000:
                        lineup.append(p)
                        salary += p['salary']
                        other_team_added += 1

            if len(lineup) == 6:
                total_proj = sum(p['projection'] for p in lineup) + captain['projection'] * 0.5
                if total_proj > best_score:
                    best_score = total_proj
                    best_lineup = (lineup, captain)

    if best_lineup:
        return create_showdown_lineup_result(best_lineup[0], best_lineup[1])
    return None


def build_underdog_leverage_2_4(players, strategy=None):
    """2 from favorite, 4 from underdog (69% win rate, 270.8% ROI)"""
    teams = defaultdict(list)
    team_totals = {}

    for p in players:
        teams[p['team']].append(p)
        if p['team'] not in team_totals:
            team_totals[p['team']] = p.get('team_total', 4.5)

    if len(teams) != 2:
        return None

    sorted_teams = sorted(team_totals.items(), key=lambda x: x[1], reverse=True)
    favorite_team = sorted_teams[0][0]
    underdog_team = sorted_teams[1][0]

    favorite_players = sorted(teams[favorite_team], key=lambda x: x['projection'], reverse=True)
    underdog_players = sorted(teams[underdog_team], key=lambda x: x['projection'], reverse=True)

    # Captain from underdog
    if not underdog_players:
        return None

    captain = underdog_players[0]
    lineup = [captain]
    salary = int(captain['salary'] * 1.5)

    # Add 3 more from underdog
    underdog_added = 0
    for p in underdog_players[1:]:
        if underdog_added < 3 and salary + p['salary'] <= 50000 - 8000:  # Leave room
            lineup.append(p)
            salary += p['salary']
            underdog_added += 1

    # Add 2 from favorite
    favorite_added = 0
    for p in favorite_players:
        if favorite_added < 2 and salary + p['salary'] <= 50000:
            lineup.append(p)
            salary += p['salary']
            favorite_added += 1

    if len(lineup) == 6:
        return create_showdown_lineup_result(lineup, captain)
    return None


def build_value_captain_under_5k(players, strategy=None):
    """Captain under $5000 with highest projection (66.4% win rate)"""
    value_players = [p for p in players if p['salary'] < 5000]

    if not value_players:
        return None

    value_players.sort(key=lambda x: x['projection'], reverse=True)
    captain = value_players[0]

    lineup = [captain]
    salary = int(captain['salary'] * 1.5)

    # Fill with best value
    other_players = [p for p in players if p != captain]
    for p in other_players:
        p['value_score'] = p['projection'] / (p['salary'] / 1000)

    other_players.sort(key=lambda x: x['value_score'], reverse=True)

    for p in other_players[:5]:
        if salary + p['salary'] <= 50000:
            lineup.append(p)
            salary += p['salary']

    if len(lineup) == 6:
        return create_showdown_lineup_result(lineup, captain)
    return None


def build_onslaught_contrarian_captain(players, strategy=None):
    """4-2 favorite stack but captain from underdog (66% win rate)"""
    teams = defaultdict(list)
    team_totals = {}

    for p in players:
        teams[p['team']].append(p)
        if p['team'] not in team_totals:
            team_totals[p['team']] = p.get('team_total', 4.5)

    if len(teams) != 2:
        return None

    sorted_teams = sorted(team_totals.items(), key=lambda x: x[1], reverse=True)
    favorite_team = sorted_teams[0][0]
    underdog_team = sorted_teams[1][0]

    favorite_players = sorted(teams[favorite_team], key=lambda x: x['projection'], reverse=True)
    underdog_players = sorted(teams[underdog_team], key=lambda x: x['projection'], reverse=True)

    # Captain from underdog
    if not underdog_players:
        return None

    captain = underdog_players[0]
    lineup = [captain]
    salary = int(captain['salary'] * 1.5)

    # Add 4 from favorite
    favorite_added = 0
    for p in favorite_players:
        if favorite_added < 4 and salary + p['salary'] <= 50000 - 4000:
            lineup.append(p)
            salary += p['salary']
            favorite_added += 1

    # Add 1 more from underdog
    for p in underdog_players[1:]:
        if len(lineup) < 6 and salary + p['salary'] <= 50000:
            lineup.append(p)
            salary += p['salary']
            break

    if len(lineup) == 6:
        return create_showdown_lineup_result(lineup, captain)
    return None


def build_favorite_onslaught_4_2(players, strategy=None):
    """4 from favorite, 2 from underdog (303% ROI)"""
    teams = defaultdict(list)
    team_totals = {}

    for p in players:
        teams[p['team']].append(p)
        if p['team'] not in team_totals:
            team_totals[p['team']] = p.get('team_total', 4.5)

    if len(teams) != 2:
        return None

    sorted_teams = sorted(team_totals.items(), key=lambda x: x[1], reverse=True)
    favorite_team = sorted_teams[0][0]
    underdog_team = sorted_teams[1][0]

    favorite_players = sorted(teams[favorite_team], key=lambda x: x['projection'], reverse=True)
    underdog_players = sorted(teams[underdog_team], key=lambda x: x['projection'], reverse=True)

    # Captain from favorite
    if not favorite_players:
        return None

    captain = favorite_players[0]
    lineup = [captain]
    salary = int(captain['salary'] * 1.5)

    # Add 3 more from favorite
    favorite_added = 0
    for p in favorite_players[1:]:
        if favorite_added < 3 and salary + p['salary'] <= 50000 - 8000:
            lineup.append(p)
            salary += p['salary']
            favorite_added += 1

    # Add 2 from underdog
    underdog_added = 0
    for p in underdog_players:
        if underdog_added < 2 and salary + p['salary'] <= 50000:
            lineup.append(p)
            salary += p['salary']
            underdog_added += 1

    if len(lineup) == 6:
        return create_showdown_lineup_result(lineup, captain)
    return None


# ============== CLASSIC STRATEGIES ==============

def build_mini_stack_floor(players, strategy=None):
    """Mini Stack + Floor - 3-stack from 5.25+ team (71.2% win rate)"""
    team_players = defaultdict(list)
    team_totals = {}

    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)
            if p['team'] not in team_totals:
                team_totals[p['team']] = p.get('team_total', 4.5)

    # Find eligible teams
    eligible_teams = [(team, total) for team, total in team_totals.items()
                      if total >= 5.25 and len(team_players[team]) >= 3]

    if not eligible_teams:
        eligible_teams = [(team, team_totals.get(team, 4.5))
                          for team in team_players
                          if len(team_players[team]) >= 3]

    if not eligible_teams:
        return None

    eligible_teams.sort(key=lambda x: x[1], reverse=True)

    # Try each team
    for team, _ in eligible_teams[:3]:
        lineup = []
        salary = 0
        positions_filled = defaultdict(int)
        teams_used = defaultdict(int)

        # Get team players sorted by floor
        team_list = team_players[team]
        for p in team_list:
            p['floor_score'] = p.get('floor', p['projection'] * 0.7)

        team_list.sort(key=lambda x: x['floor_score'], reverse=True)

        # Add 3-player stack
        stack_added = 0
        for player in team_list:
            if stack_added >= 3:
                break

            pos = player['position']
            if positions_filled[pos] < CLASSIC_CONFIG['positions'][pos]:
                if salary + player['salary'] <= 50000 - 35000:
                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1
                    stack_added += 1

        if stack_added < 3:
            continue

        # Fill with high floor players
        other_players = [p for p in players if p not in lineup]
        for p in other_players:
            p['floor_value'] = p.get('floor', p['projection'] * 0.7) / (p['salary'] / 1000)

        other_players.sort(key=lambda x: x['floor_value'], reverse=True)

        # Complete lineup
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


def build_balanced_50_50(players, strategy=None):
    """50% projection + 50% ownership (63.6% win rate)"""
    for p in players:
        norm_own = p['ownership'] / 100
        norm_proj = p['projection'] / 50
        p['balanced_score'] = (norm_own * 50 + norm_proj * 50)

    return build_by_metric(players, 'balanced_score')


def build_pure_projection(players, strategy=None):
    """Highest projection regardless of ownership (62.9% win rate)"""
    return build_by_metric(players, 'projection')


def build_pure_floor(players, strategy=None):
    """Highest floor projections only (62.4% win rate)"""
    for p in players:
        p['floor'] = p.get('floor', p['projection'] * 0.7)
    return build_by_metric(players, 'floor')


def build_pure_ceiling(players, strategy=None):
    """Highest ceiling projections (81.6% ROI)"""
    for p in players:
        p['ceiling'] = p.get('ceiling', p['projection'] * 2.5)
    return build_by_metric(players, 'ceiling')


def build_balanced_60_40(players, strategy=None):
    """60% ownership + 40% projection (70% win rate)"""
    for p in players:
        norm_own = p['ownership'] / 100
        norm_proj = p['projection'] / 50
        p['balanced_score'] = (norm_own * 60 + norm_proj * 40)

    return build_by_metric(players, 'balanced_score')


def build_balanced_40_60(players, strategy=None):
    """40% ownership + 60% projection (64.4% win rate)"""
    for p in players:
        norm_own = p['ownership'] / 100
        norm_proj = p['projection'] / 50
        p['balanced_score'] = (norm_own * 40 + norm_proj * 60)

    return build_by_metric(players, 'balanced_score')


def build_pure_chalk(players, strategy=None):
    """Highest ownership players (70.2% win rate)"""
    return build_by_metric(players, 'ownership')


def build_balanced_70_30(players, strategy=None):
    """70% ownership + 30% projection (66% win rate)"""
    for p in players:
        norm_own = p['ownership'] / 100
        norm_proj = p['projection'] / 50
        p['balanced_score'] = (norm_own * 70 + norm_proj * 30)

    return build_by_metric(players, 'balanced_score')


def build_five_man_stack(players, strategy=None):
    """5 players from same team (83.7% ROI)"""
    team_players = defaultdict(list)
    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    best_lineup = None

    for team, players_list in team_players.items():
        if len(players_list) < 5:
            continue

        # Get top 5 by projection
        stack = sorted(players_list, key=lambda x: x['projection'], reverse=True)[:5]

        # Build lineup starting with stack
        lineup = stack[:]
        salary = sum(p['salary'] for p in stack)
        positions_filled = defaultdict(int)
        teams_used = defaultdict(int)

        for p in stack:
            positions_filled[p['position']] += 1
            teams_used[p['team']] += 1

        # Fill remaining positions
        other_players = [p for p in players if p not in stack]
        other_players.sort(key=lambda x: x.get('value_score', x['projection'] / (x['salary'] / 1000)), reverse=True)

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
            result = create_classic_lineup_result(lineup)
            if not best_lineup or result['projection'] > best_lineup['projection']:
                best_lineup = result

    return best_lineup


def build_four_man_stack(players, strategy=None):
    """4 players from same team (70.6% ROI)"""
    # Similar to five_man_stack but with 4
    team_players = defaultdict(list)
    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    best_lineup = None

    for team, players_list in team_players.items():
        if len(players_list) < 4:
            continue

        stack = sorted(players_list, key=lambda x: x['projection'], reverse=True)[:4]

        lineup = stack[:]
        salary = sum(p['salary'] for p in stack)
        positions_filled = defaultdict(int)
        teams_used = defaultdict(int)

        for p in stack:
            positions_filled[p['position']] += 1
            teams_used[p['team']] += 1

        other_players = [p for p in players if p not in stack]
        other_players.sort(key=lambda x: x.get('value_score', x['projection'] / (x['salary'] / 1000)), reverse=True)

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
            result = create_classic_lineup_result(lineup)
            if not best_lineup or result['projection'] > best_lineup['projection']:
                best_lineup = result

    return best_lineup


def build_game_stack_3_2(players, strategy=None):
    """3 from one team, 2 from opponent (199.5% ROI)"""
    games = defaultdict(lambda: defaultdict(list))

    for p in players:
        if 'game_id' in p:
            games[p['game_id']][p['team']].append(p)

    best_lineup = None
    best_score = 0

    for game_id, game_teams in games.items():
        if len(game_teams) != 2:
            continue

        teams = list(game_teams.keys())

        # Try both team combinations
        for primary_team, secondary_team in [(teams[0], teams[1]), (teams[1], teams[0])]:
            primary_players = game_teams[primary_team]
            secondary_players = game_teams[secondary_team]

            if len(primary_players) < 3 or len(secondary_players) < 2:
                continue

            # Get best 3 from primary
            primary_stack = sorted(primary_players, key=lambda x: x['projection'], reverse=True)[:3]

            # Get best 2 from secondary
            secondary_stack = sorted(secondary_players, key=lambda x: x['projection'], reverse=True)[:2]

            # Build lineup
            stack = primary_stack + secondary_stack
            lineup = stack[:]
            salary = sum(p['salary'] for p in stack)
            positions_filled = defaultdict(int)
            teams_used = defaultdict(int)

            for p in stack:
                positions_filled[p['position']] += 1
                teams_used[p['team']] = teams_used.get(p['team'], 0) + 1

            # Fill remaining
            other_players = [p for p in players if p not in stack]
            other_players.sort(key=lambda x: x.get('value_score', x['projection'] / (x['salary'] / 1000)), reverse=True)

            for player in other_players:
                if len(lineup) >= 10:
                    break

                pos = player['position']
                if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
                    continue

                if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                    continue

                if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                    continue

                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] = teams_used.get(player['team'], 0) + 1

            if len(lineup) == 10:
                total_proj = sum(p['projection'] for p in lineup)
                if total_proj > best_score:
                    best_score = total_proj
                    best_lineup = create_classic_lineup_result(lineup)

    return best_lineup


def build_game_stack_4_2(players, strategy=None):
    """4 from one team, 2 from opponent (183.6% ROI)"""
    games = defaultdict(lambda: defaultdict(list))

    for p in players:
        if 'game_id' in p:
            games[p['game_id']][p['team']].append(p)

    best_lineup = None
    best_score = 0

    for game_id, game_teams in games.items():
        if len(game_teams) != 2:
            continue

        teams = list(game_teams.keys())

        for primary_team, secondary_team in [(teams[0], teams[1]), (teams[1], teams[0])]:
            primary_players = game_teams[primary_team]
            secondary_players = game_teams[secondary_team]

            if len(primary_players) < 4 or len(secondary_players) < 2:
                continue

            # Get best 4 from primary
            primary_stack = sorted(primary_players, key=lambda x: x['projection'], reverse=True)[:4]

            # Get best 2 from secondary
            secondary_stack = sorted(secondary_players, key=lambda x: x['projection'], reverse=True)[:2]

            # Build lineup
            stack = primary_stack + secondary_stack
            lineup = stack[:]
            salary = sum(p['salary'] for p in stack)
            positions_filled = defaultdict(int)
            teams_used = defaultdict(int)

            for p in stack:
                positions_filled[p['position']] += 1
                teams_used[p['team']] = teams_used.get(p['team'], 0) + 1

            # Fill remaining
            other_players = [p for p in players if p not in stack]
            other_players.sort(key=lambda x: x.get('value_score', x['projection'] / (x['salary'] / 1000)), reverse=True)

            for player in other_players:
                if len(lineup) >= 10:
                    break

                pos = player['position']
                if positions_filled[pos] >= CLASSIC_CONFIG['positions'][pos]:
                    continue

                if salary + player['salary'] > CLASSIC_CONFIG['salary_cap']:
                    continue

                if teams_used.get(player['team'], 0) >= CLASSIC_CONFIG['max_players_per_team']:
                    continue

                lineup.append(player)
                salary += player['salary']
                positions_filled[pos] += 1
                teams_used[player['team']] = teams_used.get(player['team'], 0) + 1

            if len(lineup) == 10:
                total_proj = sum(p['projection'] for p in lineup)
                if total_proj > best_score:
                    best_score = total_proj
                    best_lineup = create_classic_lineup_result(lineup)

    return best_lineup


def build_smart_chalk_zone(players, strategy=None):
    """Target 37-40% ownership sweet spot (64% win rate)"""
    # Filter players in the ownership zone
    zone_players = [p for p in players if 35 <= p['ownership'] <= 42]

    if len(zone_players) < 5:
        # Expand the zone
        zone_players = [p for p in players if 30 <= p['ownership'] <= 45]

    if len(zone_players) < 5:
        # Use top 40% by ownership
        players_sorted = sorted(players, key=lambda x: x['ownership'], reverse=True)
        cutoff = int(len(players_sorted) * 0.4)
        zone_players = players_sorted[:cutoff]

    # Build with zone players prioritized
    for p in zone_players:
        p['zone_score'] = p['projection'] * 1.2  # Boost zone players

    for p in players:
        if p not in zone_players:
            p['zone_score'] = p['projection']

    return build_by_metric(players, 'zone_score')


def build_sequential_leverage(players, strategy=None):
    """1-5 batting order with leverage plays (63.8% cash, 97.2% GPP)"""
    # Filter batters only
    batters = [p for p in players if p['position'] != 'P']

    # Prioritize 1-5 batting order
    top_order = [p for p in batters if 1 <= p.get('batting_order', 9) <= 5]

    if len(top_order) < 4:
        # Include 6th spot too
        top_order = [p for p in batters if 1 <= p.get('batting_order', 9) <= 6]

    # Sort by projection within top order
    top_order.sort(key=lambda x: x['projection'], reverse=True)

    # Build lineup prioritizing top order
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Add top order players first
    for player in top_order:
        if len(lineup) >= 8:  # Leave room for pitcher and value
            break

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

    # Fill remaining with best available
    remaining = [p for p in players if p not in lineup]
    remaining.sort(key=lambda x: x.get('value_score', x['projection'] / (x['salary'] / 1000)), reverse=True)

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

    if len(lineup) == 10:
        return create_classic_lineup_result(lineup)
    return None


def build_floor_correlation(players, strategy=None):
    """High floor with mini game correlation (68% win rate, 120.7% ROI)"""
    # Calculate floor scores
    for p in players:
        p['floor_score'] = p.get('floor', p['projection'] * 0.7)

    # Find high floor game
    game_floors = defaultdict(list)
    for p in players:
        if 'game_id' in p:
            game_floors[p['game_id']].append(p['floor_score'])

    best_game = None
    best_floor = 0

    for game_id, floors in game_floors.items():
        if floors:
            avg_floor = np.mean(floors)
            if avg_floor > best_floor:
                best_floor = avg_floor
                best_game = game_id

    # Boost players from high floor game
    if best_game:
        for p in players:
            if p.get('game_id') == best_game:
                p['floor_score'] *= 1.2

    return build_by_metric(players, 'floor_score')


def build_multi_statcast_leverage(players, strategy=None):
    """Two 3-stacks with statcast edges (52.9% ROI)"""
    # Find teams with good statcast metrics
    team_players = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            # Boost players with good statcast
            if p.get('barrel_rate', 0) > 0.08 or p.get('xwoba', 0) > 0.330:
                p['statcast_boost'] = 1.3
            else:
                p['statcast_boost'] = 1.0

            team_players[p['team']].append(p)

    # Find two teams for stacks
    team_scores = {}
    for team, players_list in team_players.items():
        if len(players_list) >= 3:
            top_3 = sorted(players_list,
                           key=lambda x: x['projection'] * x.get('statcast_boost', 1),
                           reverse=True)[:3]
            team_scores[team] = sum(p['projection'] * p.get('statcast_boost', 1) for p in top_3)

    if len(team_scores) < 2:
        return None

    # Get top 2 teams
    top_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)[:2]

    # Build lineup with two 3-stacks
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    # Add 3 from each top team
    for team, _ in top_teams:
        team_list = sorted(team_players[team],
                           key=lambda x: x['projection'] * x.get('statcast_boost', 1),
                           reverse=True)[:3]

        for player in team_list:
            if len(lineup) >= 6:
                break

            pos = player['position']
            if positions_filled[pos] < CLASSIC_CONFIG['positions'][pos]:
                if salary + player['salary'] <= CLASSIC_CONFIG['salary_cap'] - 20000:
                    lineup.append(player)
                    salary += player['salary']
                    positions_filled[pos] += 1
                    teams_used[player['team']] += 1

    # Fill remaining
    other_players = [p for p in players if p not in lineup]
    other_players.sort(key=lambda x: x.get('value_score', x['projection'] / (x['salary'] / 1000)), reverse=True)

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


# Strategy mapping for easy access
WINNING_STRATEGY_BUILDERS = {
    'showdown': {
        'ace_only': build_ace_only,
        'balanced_game_3_3': build_balanced_game_3_3,
        'underdog_leverage_2_4': build_underdog_leverage_2_4,
        'value_captain_under_5k': build_value_captain_under_5k,
        'onslaught_contrarian_captain': build_onslaught_contrarian_captain,
        'favorite_onslaught_4_2': build_favorite_onslaught_4_2,
    },
    'classic': {
        'mini_stack_floor': build_mini_stack_floor,
        'balanced_50_50': build_balanced_50_50,
        'balanced_60_40': build_balanced_60_40,
        'balanced_40_60': build_balanced_40_60,
        'balanced_70_30': build_balanced_70_30,
        'pure_chalk': build_pure_chalk,
        'pure_projection': build_pure_projection,
        'pure_floor': build_pure_floor,
        'pure_ceiling': build_pure_ceiling,
        'five_man_stack': build_five_man_stack,
        'four_man_stack': build_four_man_stack,
        'game_stack_3_2': build_game_stack_3_2,
        'game_stack_4_2': build_game_stack_4_2,
        'smart_chalk_zone': build_smart_chalk_zone,
        'sequential_leverage': build_sequential_leverage,
        'floor_correlation': build_floor_correlation,
        'multi_statcast_leverage': build_multi_statcast_leverage,
    }
}