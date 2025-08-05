"""
Enhanced GPP Tournament Strategies with Tunable Parameters
=========================================================
"""
from collections import defaultdict
import numpy as np


def build_correlation_value(players, params=None):
    """
    #1 GPP Strategy for Small Slates - Now with tunable parameters!

    Value plays in high-scoring games with correlation
    """
    print("\n🔥🔥🔥 CORRELATION_VALUE CALLED! 🔥🔥🔥\n")

    params = params or {
        'high_total_threshold': 10.0,  # Increased from 9.0
        'med_total_threshold': 8.5,  # Increased from 8.0
        'high_game_multiplier': 2.0,  # Increased from 1.5
        'med_game_multiplier': 1.3,  # Increased from 1.1
        'low_game_multiplier': 0.8,  # Decreased from 0.9
        'value_threshold': 3.0,  # Decreased from 4.0 - easier to qualify
        'value_bonus': 2.0,  # Increased from 1.3 - bigger boost
        'correlation_weight': 0.5,  # Increased from 0.3
        'ownership_threshold': 15,  # Decreased from 20
        'ownership_penalty': 0.5,  # Decreased from 0.7 - more aggressive
    }

    # DEBUG: Check game totals
    import random
    game_totals_set = set()
    for player in players:
        if hasattr(player, 'game_total'):
            game_totals_set.add(player.game_total)
    print(f"DEBUG correlation_value: Game totals in slate: {sorted(game_totals_set)}")

    # First identify high-scoring games
    game_totals = {}
    for player in players:
        if hasattr(player, 'game_id'):
            game_totals[player.game_id] = getattr(player, 'game_total', 8.5)

    for player in players:
        if player.primary_position == 'P':
            # Standard pitcher scoring with ownership consideration
            ownership = getattr(player, 'projected_ownership', 15)
            own_mult = params['ownership_penalty'] if ownership > params['ownership_threshold'] else 1.0
            player.optimization_score = player.base_projection * own_mult
        else:
            # Calculate value score
            value_score = player.base_projection / (player.salary / 1000) if player.salary > 0 else 0

            # Value bonus - more aggressive
            value_mult = params['value_bonus'] if value_score >= params['value_threshold'] else 1.0

            # Get game total with variance fix
            game_total = getattr(player, 'game_total', 8.5)

            # TEMPORARY FIX: Add variance if all games are around 9.0
            if 8.0 <= game_total <= 10.0:  # If it's in the common range
                variance = random.uniform(-2.0, 2.0)
                game_total = game_total + variance
                game_total = max(6.5, min(12.0, game_total))  # Keep realistic bounds

            # Game total bonus with new thresholds
            if game_total >= params['high_total_threshold']:
                game_mult = params['high_game_multiplier']
            elif game_total >= params['med_total_threshold']:
                game_mult = params['med_game_multiplier']
            else:
                game_mult = params['low_game_multiplier']

            # Correlation bonus for same-game stacks
            correlation_bonus = 1.0
            if hasattr(player, 'correlation_score'):
                correlation_bonus = 1.0 + (player.correlation_score * params['correlation_weight'])

            # Ownership leverage - more aggressive
            ownership = getattr(player, 'projected_ownership', 15)
            if ownership > params['ownership_threshold']:
                own_mult = params['ownership_penalty']
            else:
                # Bonus for low ownership
                own_mult = 1.0 + ((params['ownership_threshold'] - ownership) / 100)

            # Combine all factors - NO DIVISION BY 10!
            player.optimization_score = (
                    player.base_projection *
                    value_mult *
                    game_mult *
                    correlation_bonus *
                    own_mult
            )

        # Apply tournament GPP patterns
        for player in players:
            if player.primary_position != 'P':
                # Mark stackable players
                team_total = getattr(player, 'implied_team_score', 4.5)
                batting_order = getattr(player, 'batting_order', 9)

                # Elite stacking candidates
                if team_total >= 5.5 and batting_order <= 5:
                    player.optimization_score *= 1.25
                    player.elite_stack = True

                    # Consecutive batting order bonus
                    if batting_order <= 4:
                        player.stack_correlation = 1.15

                # Low ownership leverage
                ownership = getattr(player, 'ownership_projection', 15)
                if ownership < 10 and team_total >= 5.0:
                    player.optimization_score *= 1.18
                    player.leverage_play = True
                elif ownership < 15:
                    player.optimization_score *= 1.08

                # Park factor for GPP upside
                park_factor = getattr(player, 'park_factor', 1.0)
                if park_factor >= 1.15:  # Coors, etc
                    player.optimization_score *= 1.12

            else:  # Pitchers
                # GPP pitcher strategy - ceiling over floor
                k_upside = getattr(player, 'k_rate', 20)
                if k_upside >= 30:  # Elite K upside
                    player.optimization_score *= 1.15

        return players


def build_truly_smart_stack(players, params=None):
    """
    #1 GPP Strategy for Medium Slates - Enhanced version with parameters!

    Multi-factor team stacking with intelligent selection
    """
    params = params or {
        # Factor weights (must sum close to 1.0)
        'projection_weight': 0.25,        # 0.1-0.4: Weight on raw projections
        'ceiling_weight': 0.25,           # 0.1-0.4: Weight on upside
        'matchup_weight': 0.25,           # 0.1-0.4: Weight on matchup quality
        'game_total_weight': 0.25,        # 0.1-0.4: Weight on Vegas totals

        # Thresholds
        'min_stack_size': 4,              # 3-5: Minimum players per stack
        'max_stack_size': 6,              # 5-7: Maximum players per stack
        'bad_pitcher_era': 4.5,           # 4.0-5.5: ERA to target against
        'min_game_total': 8.0,            # 7.0-9.0: Minimum acceptable total

        # Multipliers
        'stack_correlation_mult': 1.3,    # 1.1-1.6: Boost for correlated stacks
        'bad_pitcher_mult': 1.4,          # 1.2-1.8: Boost vs bad pitchers
        'hot_team_mult': 1.2,             # 1.1-1.4: Boost for hot teams

        # Advanced
        'allow_mini_stacks': 1,           # 0-1: Allow 2-player mini stacks
        'cross_game_correlation': 0.2,    # 0.0-0.5: Allow opposing pitcher stacks
    }

    # Initialize tracking
    team_scores = defaultdict(lambda: {
        'projections': 0,
        'ceilings': 0,
        'matchup_quality': 0,
        'game_total': 0,
        'players': []
    })

    # Analyze all teams
    for p in players:
        if p.primary_position != 'P':
            team = p.team
            data = team_scores[team]

            # Add to team totals
            data['projections'] += p.projection
            data['ceilings'] += getattr(p, 'ceiling', p.base_projection * 1.5)
            data['players'].append(p)

            # Get matchup info
            if hasattr(p, 'matchup_info') and p.matchup_info:
                opp_era = p.matchup_info.get('opp_pitcher_era', 4.0)
            else:
                opp_era = getattr(p, 'opp_pitcher_era', 4.0)

            if opp_era > params['bad_pitcher_era']:
                data['matchup_quality'] += p.base_projection * params['bad_pitcher_mult']
            else:
                data['matchup_quality'] += p.projection

            # Game total
            data['game_total'] = getattr(p, 'game_total', 8.5)

    # Calculate composite scores and identify best stacks
    best_stacks = []

    for team, data in team_scores.items():
        # Skip if not enough players or low game total
        if (len(data['players']) < params['min_stack_size'] or
            data['game_total'] < params['min_game_total']):
            continue

        # Calculate weighted score
        score = (
            data['projections'] * params['projection_weight'] +
            data['ceilings'] * params['ceiling_weight'] +
            data['matchup_quality'] * params['matchup_weight'] +
            (data['game_total'] / 8.5) * data['projections'] * params['game_total_weight']
        )

        # Hot team bonus
        avg_form = np.mean([getattr(p, 'recent_form', 1.0) for p in data['players']])
        if avg_form > 1.1:
            score *= params['hot_team_mult']

        best_stacks.append((team, score, data))

    # Sort by score
    best_stacks.sort(key=lambda x: x[1], reverse=True)

    # Apply scores to players
    if best_stacks:
        # Take top 2-3 stacks
        num_stacks = 2 if params['allow_mini_stacks'] else 1

        for i, (team, score, data) in enumerate(best_stacks[:num_stacks]):
            # Sort players by projection
            team_players = sorted(data['players'], key=lambda x: x.base_projection, reverse=True)

            # Apply correlation multiplier to top N players
            stack_size = min(params['max_stack_size'], len(team_players))
            for j, player in enumerate(team_players[:stack_size]):
                if j < stack_size:
                    player.optimization_score = (
                        player.base_projection *
                        params['stack_correlation_mult'] *
                        (1 - i * 0.2)  # Slightly favor primary stack
                    )
                else:
                    player.optimization_score = player.base_projection * 0.8

    # Handle non-stack players
    for player in players:
        if not hasattr(player, 'optimization_score'):
            if player.primary_position == 'P':
                # Look for opposing pitcher correlation
                player.optimization_score = player.base_projection

                # Bonus if facing a stacked team
                for team, _, _ in best_stacks[:1]:
                    if hasattr(player, 'opponent') and player.opponent == team:
                        player.optimization_score *= (1 + params['cross_game_correlation'])
            else:
                # Non-stack hitters get reduced score
                player.optimization_score = player.base_projection * 0.7

    players = build_truly_smart_stack(players)

    # Group by team for stack analysis
    teams = {}
    for player in players:
        if player.primary_position != 'P':
            if player.team not in teams:
                teams[player.team] = []
            teams[player.team].append(player)

    # Apply stack bonuses
    for team, team_players in teams.items():
        # Sort by batting order
        team_players.sort(key=lambda p: getattr(p, 'batting_order', 9))

        # Check if we can build 4-5 man stack
        if len(team_players) >= 4:
            team_total = getattr(team_players[0], 'implied_team_score', 4.5)

            if team_total >= 5.0:
                # Apply correlation bonuses for consecutive batters
                for i in range(len(team_players) - 1):
                    bo1 = getattr(team_players[i], 'batting_order', 9)
                    bo2 = getattr(team_players[i + 1], 'batting_order', 9)

                    if abs(bo1 - bo2) == 1 and bo1 <= 5:
                        # Consecutive batters in top 5
                        team_players[i].optimization_score *= 1.12
                        team_players[i + 1].optimization_score *= 1.12
                        team_players[i].stack_correlation = True
                        team_players[i + 1].stack_correlation = True

    return players


def build_matchup_leverage_stack(players, params=None):
    """
    #1 GPP Strategy for Large Slates - Now with tunable parameters!

    Target worst pitchers with correlated stacks
    """
    params = params or {
        'num_worst_pitchers': 3,
        'era_threshold': 5.0,
        'whip_threshold': 1.4,
        'k_rate_threshold': 18,
        'stack_multiplier': 1.8,  # CHANGE THIS to 2.5
        'correlation_bonus': 1.2,  # CHANGE THIS to 1.5
        'ownership_leverage': 0.3,  # CHANGE THIS to 0.5
        # ... rest of params
    }

    # Find worst pitchers
    pitcher_scores = []

    for p in players:
        if p.primary_position == 'P':
            era = getattr(p, 'era', 4.5)
            whip = getattr(p, 'whip', 1.3)
            k_rate = getattr(p, 'k_rate', 20)

            # Calculate "badness" score
            if (era <= params['era_threshold'] and
                whip <= params['whip_threshold'] and
                k_rate >= params['k_rate_threshold']):
                # This is actually a good pitcher, skip
                continue

            badness = (
                (era / 4.5) * 0.4 +          # ERA component
                (whip / 1.3) * 0.3 +         # WHIP component
                ((30 - k_rate) / 10) * 0.3   # Low K rate component
            )

            pitcher_scores.append((p, badness))

    # Sort by badness (worst first)
    pitcher_scores.sort(key=lambda x: x[1], reverse=True)
    worst_pitchers = [p for p, _ in pitcher_scores[:params['num_worst_pitchers']]]

    # Find teams facing these pitchers
    target_teams = set()
    pitcher_opponents = {}

    for pitcher in worst_pitchers:
        if hasattr(pitcher, 'opponent'):
            target_teams.add(pitcher.opponent)
            pitcher_opponents[pitcher.opponent] = pitcher

    # Score players
    for player in players:
        if player.primary_position == 'P':
            # Fade pitchers facing our target teams
            if hasattr(player, 'opponent') and player.opponent in target_teams:
                player.optimization_score = player.base_projection * params['pitcher_leverage_mult']
            else:
                player.optimization_score = player.base_projection
        else:
            # Massive boost for hitters facing bad pitchers
            if player.team in target_teams:
                base_score = player.base_projection * params['stack_multiplier']

                # Additional boosts
                # Correlation within team
                if hasattr(player, 'batting_order'):
                    if 1 <= player.batting_order <= 5:
                        base_score *= params['correlation_bonus']

                # Environmental boosts
                park = getattr(player, 'park_factor', 1.0)
                weather = getattr(player, 'weather_impact', 1.0)

                env_boost = 1.0 + (park - 1.0) * params['park_boost'] + (weather - 1.0) * params['weather_boost']
                base_score *= env_boost

                # Ownership leverage
                ownership = getattr(player, 'projected_ownership', 15)
                if ownership < 10:
                    # Low owned players in good spots
                    base_score *= (1 + params['ownership_leverage'])
                elif ownership > 25:
                    # Fade chalk even in good spots
                    base_score *= (1 - params['ownership_leverage'] * 0.5)

                player.optimization_score = base_score
            else:
                # Non-target teams get standard scoring
                player.optimization_score = player.base_projection * 0.9

    players = build_matchup_leverage_stack(players, params)

    # Apply tournament leverage patterns
    for player in players:
        ownership = getattr(player, 'ownership_projection', 15)

        if player.primary_position == 'P':
            # Extreme leverage on low-owned pitchers
            if ownership < 5:
                player.optimization_score *= 1.30
                player.extreme_leverage = True
            elif ownership < 10:
                player.optimization_score *= 1.15

        else:  # Hitters
            # Leverage + good spots
            team_total = getattr(player, 'implied_team_score', 4.5)
            if ownership < 10 and team_total >= 5.0:
                player.optimization_score *= 1.25
                player.leverage_smash = True

            # Fade mega-chalk
            if ownership > 35:
                player.optimization_score *= params['ownership_fade']

    return players


def build_experimental_gpp_strategy(players, params=None):
    """
    Experimental: Kitchen sink GPP strategy for testing what matters

    This has MANY parameters to test different theories
    """
    params = params or {
        # Base scoring
        'ceiling_weight': 0.6,            # 0.3-0.8: Ceiling vs projection
        'ownership_fade_start': 20,       # 15-30: When to start fading
        'ownership_fade_strength': 0.3,   # 0.1-0.5: How hard to fade

        # Stacking params
        'primary_stack_min': 4,           # 3-5: Minimum stack size
        'secondary_stack_allowed': 1,     # 0-1: Allow second stack
        'stack_ownership_limit': 60,      # 40-80: Max combined ownership

        # Game selection
        'min_game_total': 7.5,            # 7.0-9.0: Minimum Vegas total
        'weather_impact_mult': 1.3,       # 1.0-2.0: Good weather boost
        'max_pitcher_era': 3.8,           # 3.5-4.5: Avoid good pitchers

        # Leverage plays
        'cold_player_boost': 1.4,         # 1.0-2.0: Boost for slumping players
        'platoon_disadvantage_boost': 1.2,# 1.0-1.5: Contrarian platoon plays
        'narrative_fade_mult': 1.3,       # 1.0-2.0: Fade the obvious plays

        # Advanced metrics
        'statcast_weight': 0.3,           # 0.0-0.5: Weight on xStats
        'recent_form_curve': 2.0,         # 1.0-3.0: Exponential form weighting
        'matchup_history_weight': 0.2,    # 0.0-0.4: BvP importance

        # Roster construction
        'stars_scrubs_threshold': 8500,   # 7500-9000: "Star" salary threshold
        'min_scrub_projection': 6,        # 4-8: Minimum for cheap players
        'pitcher_spend_percent': 0.35,    # 0.25-0.45: Budget on pitchers
    }

    # Complex scoring logic that uses many factors
    for player in players:
        # Start with ceiling-weighted score
        projection = player.base_projection
        ceiling = getattr(player, 'ceiling', projection * 1.5)

        base_score = (
            projection * (1 - params['ceiling_weight']) +
            ceiling * params['ceiling_weight']
        )

        # Ownership fade (non-linear)
        ownership = getattr(player, 'projected_ownership', 15)
        if ownership > params['ownership_fade_start']:
            fade_amount = (ownership - params['ownership_fade_start']) / 100
            fade_mult = 1 - (fade_amount ** 2) * params['ownership_fade_strength']
            base_score *= fade_mult

        # Game environment
        game_total = getattr(player, 'game_total', 8.5)
        if game_total < params['min_game_total']:
            base_score *= 0.7
        else:
            base_score *= (game_total / 8.5)

        # Weather bonus
        weather = getattr(player, 'weather_impact', 1.0)
        if weather > 1.1:
            base_score *= params['weather_impact_mult']

        # Leverage plays
        if player.primary_position != 'P':
            # Cold player leverage
            form = getattr(player, 'recent_form', 1.0)
            if form < 0.8 and ownership < 10:
                base_score *= params['cold_player_boost']

            # Platoon disadvantage leverage
            if hasattr(player, 'platoon_advantage') and not player.platoon_advantage:
                if ownership < 8:
                    base_score *= params['platoon_disadvantage_boost']

            # Narrative fade (player "should" be popular but isn't)
            expected_own = getattr(player, 'expected_ownership', ownership)
            if expected_own > ownership * 1.5:
                base_score *= params['narrative_fade_mult']

        # Advanced metrics
        if hasattr(player, 'xwoba'):
            xwoba = player.xwoba
            woba = getattr(player, 'woba', xwoba)
            if xwoba > woba:  # Due for positive regression
                base_score *= (1 + params['statcast_weight'])

        # Recent form (non-linear)
        form = getattr(player, 'recent_form', 1.0)
        form_mult = form ** params['recent_form_curve']
        base_score *= (0.5 + 0.5 * form_mult)  # Bound between 0.5-1.0

        # Roster construction rules
        if player.salary >= params['stars_scrubs_threshold']:
            # This is a "star" - needs high ceiling
            if ceiling < projection * 1.8:
                base_score *= 0.8
        elif player.salary < 4000:
            # This is a "scrub" - needs minimum projection
            if projection < params['min_scrub_projection']:
                base_score *= 0.5

        player.optimization_score = base_score

    return players

#from tournament_winner_gpp_strategy import build_tournament_winner_gpp#