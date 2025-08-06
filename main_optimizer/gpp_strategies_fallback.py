#!/usr/bin/env python3
"""
FALLBACK GPP STRATEGIES
=======================
Simple implementations for missing strategies
"""

from typing import List, Dict, Any
import random


def build_smart_stack(players: List, params: Dict = None) -> List:
    """Smart stacking strategy - groups players from same team/game"""
    if not players:
        return []

    # Group by team
    team_groups = {}
    for p in players:
        team = getattr(p, 'team', 'UNK')
        if team not in team_groups:
            team_groups[team] = []
        team_groups[team].append(p)

    # Find best team to stack (most high-projection players)
    best_team = None
    best_score = 0

    for team, team_players in team_groups.items():
        if len(team_players) >= 3:
            team_score = sum(getattr(p, 'base_projection', 10) for p in team_players[:3])
            if team_score > best_score:
                best_score = team_score
                best_team = team

    # Build lineup with stack
    lineup = []

    if best_team:
        # Add 3-4 players from best team
        team_players = sorted(team_groups[best_team], 
                             key=lambda p: getattr(p, 'base_projection', 10), 
                             reverse=True)
        lineup.extend(team_players[:3])

    # Fill rest with best available
    remaining = [p for p in players if p not in lineup]
    remaining.sort(key=lambda p: getattr(p, 'base_projection', 10), reverse=True)

    while len(lineup) < 10 and remaining:
        lineup.append(remaining.pop(0))

    return lineup


def build_matchup_leverage_stack(players: List, params: Dict = None) -> List:
    """Leverage good matchups"""
    if not players:
        return []

    # Prioritize high matchup scores
    scored_players = []
    for p in players:
        matchup = getattr(p, 'matchup_score', 1.0)
        projection = getattr(p, 'base_projection', 10)
        score = projection * (0.8 + 0.2 * matchup)
        scored_players.append((score, p))

    scored_players.sort(reverse=True)
    return [p for _, p in scored_players[:10]]


def build_truly_smart_stack(players: List, params: Dict = None) -> List:
    """Advanced stacking with correlations"""
    # For now, just use smart_stack logic
    return build_smart_stack(players, params)


def build_game_stack_3_2(players: List, params: Dict = None) -> List:
    """3-2 game stack (3 from one team, 2 from opponent)"""
    if not players:
        return []

    # Group by team
    team_groups = {}
    for p in players:
        team = getattr(p, 'team', 'UNK')
        if team not in team_groups:
            team_groups[team] = []
        team_groups[team].append(p)

    # Find teams with enough players
    valid_teams = [t for t, ps in team_groups.items() if len(ps) >= 3]

    if len(valid_teams) >= 2:
        # Pick two teams (ideally from same game)
        team1 = valid_teams[0]
        team2 = valid_teams[1] if len(valid_teams) > 1 else valid_teams[0]

        # Get 3 from team1, 2 from team2
        team1_players = sorted(team_groups[team1], 
                              key=lambda p: getattr(p, 'base_projection', 10), 
                              reverse=True)[:3]
        team2_players = sorted(team_groups[team2], 
                              key=lambda p: getattr(p, 'base_projection', 10), 
                              reverse=True)[:2]

        lineup = team1_players + team2_players

        # Fill rest
        remaining = [p for p in players if p not in lineup]
        remaining.sort(key=lambda p: getattr(p, 'base_projection', 10), reverse=True)

        while len(lineup) < 10 and remaining:
            lineup.append(remaining.pop(0))

        return lineup

    # Fallback to best available
    return sorted(players, key=lambda p: getattr(p, 'base_projection', 10), reverse=True)[:10]


def build_game_stack_4_2(players: List, params: Dict = None) -> List:
    """4-2 game stack (4 from one team, 2 from opponent)"""
    if not players:
        return []

    # Similar to 3-2 but with 4-2 split
    team_groups = {}
    for p in players:
        team = getattr(p, 'team', 'UNK')
        if team not in team_groups:
            team_groups[team] = []
        team_groups[team].append(p)

    # Find team with 4+ players
    for team, team_players in team_groups.items():
        if len(team_players) >= 4:
            # Get 4 from this team
            main_stack = sorted(team_players, 
                              key=lambda p: getattr(p, 'base_projection', 10), 
                              reverse=True)[:4]

            # Find opponent team (different team with 2+ players)
            for opp_team, opp_players in team_groups.items():
                if opp_team != team and len(opp_players) >= 2:
                    opp_stack = sorted(opp_players, 
                                     key=lambda p: getattr(p, 'base_projection', 10), 
                                     reverse=True)[:2]

                    lineup = main_stack + opp_stack

                    # Fill rest
                    remaining = [p for p in players if p not in lineup]
                    remaining.sort(key=lambda p: getattr(p, 'base_projection', 10), reverse=True)

                    while len(lineup) < 10 and remaining:
                        lineup.append(remaining.pop(0))

                    return lineup

    # Fallback
    return sorted(players, key=lambda p: getattr(p, 'base_projection', 10), reverse=True)[:10]


# Make them available
__all__ = [
    'build_smart_stack',
    'build_matchup_leverage_stack', 
    'build_truly_smart_stack',
    'build_game_stack_3_2',
    'build_game_stack_4_2'
]
