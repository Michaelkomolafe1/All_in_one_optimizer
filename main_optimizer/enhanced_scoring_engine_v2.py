"""Enhanced Scoring Engine V2 - FIXED"""

class EnhancedScoringEngineV2:
    """Enhanced scoring engine with all methods"""

    def __init__(self, use_bayesian=False, **kwargs):
        """Initialize - accepts any parameters for compatibility"""
        self.initialized = True
        self.use_bayesian = use_bayesian
        # Store any additional kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def score_player(self, player, contest_type='gpp'):
        """Main scoring method"""
        # Get base projection
        base_score = getattr(player, 'base_projection', 10.0)
        if base_score == 0:
            base_score = getattr(player, 'projection', 10.0)

        # Apply contest-specific scoring
        if contest_type.lower() == 'cash':
            return self.score_player_cash(player)
        elif contest_type.lower() == 'showdown':
            return self.score_player_showdown(player)
        else:
            return self.score_player_gpp(player)

    def score_player_gpp(self, player):
        """GPP scoring with upside emphasis"""
        base_score = getattr(player, 'base_projection', 10.0)
        if base_score == 0:
            base_score = getattr(player, 'projection', 10.0)

        # Apply adjustments
        if hasattr(player, 'recent_performance'):
            base_score *= (0.7 + 0.3 * min(player.recent_performance, 2.0))

        if hasattr(player, 'matchup_score'):
            base_score *= (0.8 + 0.2 * min(player.matchup_score, 2.0))

        if hasattr(player, 'ownership_projection'):
            ownership = player.ownership_projection
            if ownership < 10:
                base_score *= 1.15
            elif ownership > 30:
                base_score *= 0.90

        return round(base_score, 2)

    def score_player_cash(self, player):
        """Cash game scoring with floor emphasis"""
        base_score = getattr(player, 'base_projection', 10.0)
        if base_score == 0:
            base_score = getattr(player, 'projection', 10.0)

        # Consistency emphasis
        if hasattr(player, 'floor'):
            floor_factor = player.floor / max(base_score, 1)
            base_score *= (0.5 + 0.5 * min(floor_factor, 1.5))

        if hasattr(player, 'recent_performance'):
            base_score *= (0.8 + 0.2 * min(player.recent_performance, 1.5))

        return round(base_score, 2)

    def score_player_showdown(self, player):
        """Showdown scoring"""
        return self.score_player_gpp(player) * 1.1


# Alias for compatibility
EnhancedScoringEngine = EnhancedScoringEngineV2

# For imports that expect UnifiedScoringEngine
UnifiedScoringEngine = EnhancedScoringEngineV2

__all__ = ['EnhancedScoringEngineV2', 'EnhancedScoringEngine', 'UnifiedScoringEngine']
