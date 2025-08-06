"""Redirect to v2 version"""
try:
    from .enhanced_scoring_engine_v2 import *
    from .enhanced_scoring_engine_v2 import EnhancedScoringEngineV2
    EnhancedScoringEngine = EnhancedScoringEngineV2
except ImportError:
    # Fallback if v2 has issues
    class EnhancedScoringEngine:
        def __init__(self, *args, **kwargs):
            pass
        def score_player_gpp(self, player, *args, **kwargs):
            return getattr(player, 'base_projection', 10.0)
        def score_player_cash(self, player, *args, **kwargs):
            return getattr(player, 'base_projection', 10.0)
        def score_player(self, player, *args, **kwargs):
            return getattr(player, 'base_projection', 10.0)

    EnhancedScoringEngineV2 = EnhancedScoringEngine

__all__ = ['EnhancedScoringEngine', 'EnhancedScoringEngineV2']
