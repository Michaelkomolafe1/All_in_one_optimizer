# player_converter.py
# Save in main_optimizer/
"""Convert dict to UnifiedPlayer objects for old strategies"""

from unified_player_model import UnifiedPlayer


def convert_sim_players_to_unified(sim_players):
    """Convert simulator dict players to UnifiedPlayer objects"""
    unified_players = []

    for p in sim_players:
        # Create UnifiedPlayer with required parameters
        player = UnifiedPlayer(
            id=str(p.get('id', hash(p['name']))),
            name=p['name'],
            team=p['team'],
            salary=p['salary'],
            primary_position=p['position'],
            positions=[p['position']],  # Single position for now
            base_projection=p.get('projection', 0)
        )

        # Add simulator attributes that old strategies expect
        player.is_pitcher = (p['position'] == 'P')
        player.batting_order = p.get('batting_order', 0)
        player.implied_team_score = p.get('game_data', {}).get('team_total', 4.5)
        player.game_total = p.get('game_data', {}).get('game_total', 9.0)
        player.ownership_projection = p.get('ownership', 15)
        player.projected_ownership = p.get('ownership', 15)

        # Add matchup attributes
        player.matchup_score = p.get('matchup_score', 1.0)
        player.park_factor = p.get('park_factor', 1.0)
        player.weather_score = p.get('weather_score', 1.0)
        player.recent_performance = p.get('recent_performance', 50)
        player.consistency_score = p.get('consistency_score', 50)

        # Add required attributes for cash strategies
        player.bb_rate = p.get('bb_rate', 10)
        player.k_rate = p.get('k_rate', 20)
        player.win_probability = p.get('win_probability', 0.5)
        player.is_home = p.get('is_home', True)

        # Set the base_projection which strategies use
        player.projection = p.get('projection', 0)
        player.base_projection = p.get('projection', 0)

        # Add game info
        player.game_info = "{team}@OPP".format(team=p['team'])
        player.opponent = p.get('opponent', 'OPP')

        # Add optimization score (used by some strategies)
        player.optimization_score = p.get('projection', 0)

        unified_players.append(player)

    return unified_players