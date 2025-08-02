"""
GPP Tournament Strategies - #1 Winners
=====================================
UPDATED WITH optimization_score
"""
from collections import defaultdict
import numpy as np


def build_correlation_value(players):
    """
    #1 GPP Strategy for Small Slates (+24.7% ROI)
    Value plays in high-scoring games
    """
    for player in players:
        if player.primary_position == 'P':
            # Standard pitcher scoring
            # SET OPTIMIZATION SCORE
            player.optimization_score = player.projection
        else:
            # Calculate value score
            value_score = player.projection / (player.salary / 1000) if player.salary > 0 else 0

            # Game total bonus
            game_total = getattr(player, 'game_total', 8.5)
            if game_total > 9:
                game_bonus = 1.2
            else:
                game_bonus = 1.0

            # Combine factors
            # SET OPTIMIZATION SCORE
            player.optimization_score = value_score * player.projection * game_bonus / 10

    return players


def build_truly_smart_stack(players):
    """
    #1 GPP Strategy for Medium Slates (Your Enhanced Version)
    Multi-factor team stacking with intelligent selection
    """
    # Initialize tracking
    team_projections = defaultdict(float)
    team_players = defaultdict(list)
    team_ceilings = defaultdict(float)
    team_vs_bad_pitchers = defaultdict(float)
    team_game_totals = defaultdict(float)

    # Analyze all teams
    for p in players:
        if p.primary_position != 'P':
            team = p.team

            # Factor 1: Team projections
            team_projections[team] += p.projection
            team_players[team].append(p)

            # Factor 2: Team ceilings
            ceiling = getattr(p, 'ceiling', p.projection * 1.5)
            team_ceilings[team] += ceiling

            # Factor 3: Matchup vs bad pitchers
            if hasattr(p, 'matchup_info') and p.matchup_info:
                opp_era = p.matchup_info.get('opp_pitcher_era', 4.0)
            else:
                opp_era = getattr(p, 'opp_pitcher_era', 4.0)

            if opp_era > 4.5:  # Bad pitcher
                team_vs_bad_pitchers[team] += p.projection * 1.3

            # Factor 4: Game totals
            game_total = getattr(p, 'game_total', 8.5)
            team_game_totals[team] = game_total

    # Calculate composite scores for each team
    team_scores = {}
    for team in team_projections:
        # Smart weighting of all factors
        team_scores[team] = (
                team_projections[team] * 0.3 +  # 30% weight on projections
                team_ceilings[team] * 0.3 +  # 30% weight on upside
                team_vs_bad_pitchers.get(team, 0) * 0.2 +  # 20% weight on matchup
                (team_game_totals.get(team, 8.5) / 10) * team_projections[team] * 0.2  # 20% game environment
        )

    # Sort teams by score
    sorted_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)

    if sorted_teams:
        best_team = sorted_teams[0][0]
        second_team = sorted_teams[1][0] if len(sorted_teams) > 1 else None

        # Apply scoring boosts
        for p in players:
            if p.primary_position == 'P':
                # Don't modify pitcher scores
                # SET OPTIMIZATION SCORE
                p.optimization_score = p.projection
            elif p.team == best_team:
                # Primary stack gets full boost
                # SET OPTIMIZATION SCORE
                p.optimization_score = p.projection * 1.4
            elif second_team and p.team == second_team:
                # Secondary stack gets smaller boost
                # SET OPTIMIZATION SCORE
                p.optimization_score = p.projection * 1.15
            else:
                # Non-stack players
                # SET OPTIMIZATION SCORE
                p.optimization_score = p.projection
    else:
        # Fallback if no teams found
        for p in players:
            # SET OPTIMIZATION SCORE
            p.optimization_score = p.projection

    return players


def build_matchup_leverage_stack(players):
    """
    #1 GPP Strategy for Large Slates (+40.1% ROI!)
    Target team stacks facing weak pitching
    """
    # Identify weak pitchers (ERA > 4.5)
    weak_pitchers = []
    pitcher_opponents = {}

    for p in players:
        if p.primary_position == 'P':
            era = getattr(p, 'era', 4.0)
            if era > 4.5:
                weak_pitchers.append(p)
                # Store which team this pitcher faces
                opp_team = getattr(p, 'opponent', None)
                if opp_team:
                    pitcher_opponents[p.name] = opp_team

    # Find teams facing weak pitchers
    target_teams = set()
    for pitcher in weak_pitchers:
        if pitcher.name in pitcher_opponents:
            target_teams.add(pitcher_opponents[pitcher.name])

    # Score players based on leverage
    for p in players:
        if p.primary_position == 'P':
            # Standard pitcher scoring
            # SET OPTIMIZATION SCORE
            p.optimization_score = p.projection
        else:
            # Check if on a target team
            if p.team in target_teams:
                # Big boost for teams facing weak pitching
                matchup_mult = 1.5

                # Additional boost for high-upside players
                ceiling = getattr(p, 'ceiling', p.projection * 1.5)
                if ceiling > p.projection * 1.4:
                    upside_mult = 1.2
                else:
                    upside_mult = 1.0

                # SET OPTIMIZATION SCORE
                p.optimization_score = p.projection * matchup_mult * upside_mult
            else:
                # Reduced score for non-leverage plays
                # SET OPTIMIZATION SCORE
                p.optimization_score = p.projection * 0.8

    return players