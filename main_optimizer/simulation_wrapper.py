# simulation_wrapper.py
# Save this in main_optimizer/ if needed
"""
Wrapper to ensure strategies use simulation data without API calls
"""


def prepare_players_for_strategy(sim_players):
    """
    Convert simulator players to strategy format WITHOUT any API calls
    The simulator already has ALL the data we need!
    """

    prepared_players = []

    for sim_player in sim_players:
        # The simulator already provides everything
        player = {
            'name': sim_player['name'],
            'team': sim_player['team'],
            'position': sim_player['position'],
            'salary': sim_player['salary'],
            'projection': sim_player['projection'],

            # For cash strategy
            'batting_order': sim_player.get('batting_order', 5),
            'bb_rate': sim_player.get('bb_rate', 10),
            'is_home': sim_player.get('is_home', True),
            'k_rate': sim_player.get('k_rate', 20),
            'win_probability': sim_player.get('win_probability', 0.5),

            # For GPP strategy
            'ownership': sim_player.get('ownership', 15),
            'game_data': sim_player.get('game_data', {
                'game_total': 9.0,
                'team_total': 4.5
            }),

            # Additional fields strategies might expect
            'opponent': sim_player.get('opponent', 'OPP'),
            'matchup_projection': sim_player['projection'],  # Already adjusted
            'floor': sim_player['projection'] * 0.7,
            'ceiling': sim_player['projection'] * 1.5,

            # NO API CALLS - just use what simulator provides
            'confirmed': True,  # Simulator only gives starters
            'form_rating': 50,  # Default
            'woba': 0.320,  # Default
            'platoon_advantage': 0  # Default
        }

        prepared_players.append(player)

    return prepared_players


# If you need to mock the UnifiedCoreSystem for testing
class MockCoreSystem:
    """Mock system that doesn't make API calls"""

    def __init__(self):
        self.player_pool = []

    def build_player_pool(self, *args, **kwargs):
        """Mock - does nothing, no API calls"""
        pass

    def enrich_player_pool(self, *args, **kwargs):
        """Mock - does nothing, no API calls"""
        pass

    def score_players(self, contest_type='gpp'):
        """Mock scoring using existing projections"""
        for player in self.player_pool:
            player['optimization_score'] = player.get('projection', 10)