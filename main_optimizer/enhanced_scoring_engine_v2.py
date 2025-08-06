"""Enhanced Scoring Engine V2 - FIXED"""

class EnhancedScoringEngineV2:
    def __init__(self):
        self.initialized = True
    
    def score_player(self, player):
        score = getattr(player, 'base_projection', 10.0)
        if hasattr(player, 'recent_performance'):
            score *= (0.7 + 0.3 * player.recent_performance)
        if hasattr(player, 'matchup_score'):
            score *= (0.8 + 0.2 * player.matchup_score)
        return round(score, 2)
    
    def score_player_gpp(self, player):
        base_score = self.score_player(player)
        if hasattr(player, 'ownership_projection'):
            if player.ownership_projection < 10:
                base_score *= 1.15
            elif player.ownership_projection > 30:
                base_score *= 0.90
        return round(base_score, 2)
    
    def score_player_cash(self, player):
        base_score = self.score_player(player)
        if hasattr(player, 'floor'):
            floor_factor = player.floor / max(player.base_projection, 1)
            base_score *= (0.5 + 0.5 * floor_factor)
        return round(base_score, 2)
    
    def score_player_showdown(self, player):
        return self.score_player_gpp(player) * 1.1
