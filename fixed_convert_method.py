def convert_to_unified_players(self, sim_players: List) -> List[UnifiedPlayer]:
    """Convert simulated players to UnifiedPlayer objects"""
    unified_players = []

    for sp in sim_players:
        # UnifiedPlayer expects these exact arguments in order
        player = UnifiedPlayer(
            id=str(hash(sp.name)),
            name=sp.name,
            team=sp.team,
            salary=sp.salary,
            primary_position=sp.position,
            positions=[sp.position]
        )

        # Now set additional attributes
        player.AvgPointsPerGame = sp.projection
        player.base_projection = sp.projection
        player.dff_projection = sp.projection
        player.projection = sp.projection

        # Position info
        player.is_pitcher = (sp.position == 'P')
        player.position = sp.position

        # Batting order - NEVER None for position players
        if sp.position != 'P':
            player.batting_order = getattr(sp, 'batting_order', 5)
        else:
            player.batting_order = None

        # Performance metrics - ALWAYS have values
        player.recent_performance = getattr(sp, 'recent_performance', 1.0)
        player.consistency_score = getattr(sp, 'consistency_score', 0.7)
        player.matchup_score = getattr(sp, 'matchup_score', 1.0)
        player.floor = sp.projection * 0.7
        player.ceiling = sp.projection * 1.5

        # Vegas data - ALWAYS have values
        player.vegas_total = getattr(sp, 'vegas_total', 8.5)
        player.game_total = getattr(sp, 'game_total', 8.5)
        player.team_total = getattr(sp, 'team_total', 4.25)
        player.implied_team_score = player.team_total

        # Ownership - ALWAYS have value
        player.ownership_projection = getattr(sp, 'ownership', 15.0)
        player.projected_ownership = player.ownership_projection

        # Advanced stats - ALWAYS have values
        player.park_factor = getattr(sp, 'park_factor', 1.0)
        player.weather_score = getattr(sp, 'weather_score', 1.0)
        player.barrel_rate = getattr(sp, 'barrel_rate', 8.0)
        player.hard_hit_rate = getattr(sp, 'hard_hit_rate', 35.0)
        player.xwoba = getattr(sp, 'xwoba', 0.320)

        # Correlation/Stack scores
        player.stack_score = 0.0
        player.correlation_score = 0.0
        player.game_stack_score = 0.0

        # Optimization scores
        player.optimization_score = sp.projection
        player.enhanced_score = sp.projection
        player.gpp_score = sp.projection
        player.cash_score = sp.projection

        # Other required attributes
        player.value = sp.projection / (sp.salary / 1000) if sp.salary > 0 else 0
        player.points_per_dollar = player.value
        player.recent_scores = [sp.projection * 0.9, sp.projection * 1.1, sp.projection * 0.95]
        player.dff_l5_avg = sp.projection

        unified_players.append(player)

    return unified_players