"""
UNIFIED SCORING ENGINE
======================
Consolidated scoring engine with all scoring methods
"""

import numpy as np
from typing import Optional, Dict, Any


class UnifiedScoringEngine:
    """Single scoring engine for all contest types and strategies"""

    def __init__(self, use_bayesian=False, use_vegas=True, use_statcast=True):
        """Initialize with configuration options"""
        self.use_bayesian = use_bayesian
        self.use_vegas = use_vegas
        self.use_statcast = use_statcast
        self.initialized = True

    def score_player(self, player, contest_type='gpp', strategy=None) -> float:
        """Main scoring method - routes to appropriate scorer"""

        # Get base projection
        base_score = self._get_base_projection(player)

        # Apply contest-specific scoring
        if contest_type.lower() == 'cash':
            score = self._score_cash(player, base_score)
        elif contest_type.lower() == 'showdown':
            score = self._score_showdown(player, base_score)
        else:  # GPP
            score = self._score_gpp(player, base_score, strategy)

        return round(score, 2)

    def _get_base_projection(self, player) -> float:
        """Get base projection from player"""
        # Try different projection attributes
        projection_attrs = [
            'base_projection',
            'projection',
            'dff_projection',
            'avg_points',
            'AvgPointsPerGame'
        ]

        for attr in projection_attrs:
            if hasattr(player, attr):
                value = getattr(player, attr)
                if value and value > 0:
                    return float(value)

        # Default fallback
        return 10.0

    def _score_gpp(self, player, base_score: float, strategy: str = None) -> float:
        """GPP scoring with strategy adjustments"""
        score = base_score

        # Recent performance boost
        if hasattr(player, 'recent_performance'):
            score *= (0.7 + 0.3 * min(player.recent_performance, 2.0))

        # Matchup adjustments
        if hasattr(player, 'matchup_score'):
            score *= (0.8 + 0.2 * min(player.matchup_score, 2.0))

        # Ownership adjustments for GPP
        if hasattr(player, 'ownership_projection'):
            ownership = player.ownership_projection
            if ownership < 5:
                score *= 1.25  # Big boost for super low owned
            elif ownership < 10:
                score *= 1.15
            elif ownership > 30:
                score *= 0.90  # Slight fade on chalk

        # Vegas adjustments if available
        if self.use_vegas and hasattr(player, 'vegas_total'):
            if player.vegas_total > 9:
                score *= 1.1
            elif player.vegas_total < 7:
                score *= 0.9

        # Strategy-specific adjustments
        if strategy:
            score = self._apply_strategy_adjustments(player, score, strategy)

        return score

    def _score_cash(self, player, base_score: float) -> float:
        """Cash game scoring with floor emphasis"""
        score = base_score

        # Consistency is key for cash
        if hasattr(player, 'consistency_score'):
            score *= (0.6 + 0.4 * player.consistency_score)

        # Floor emphasis
        if hasattr(player, 'floor'):
            floor_ratio = player.floor / max(base_score, 1)
            score *= (0.5 + 0.5 * min(floor_ratio, 1.5))

        # Recent form matters more in cash
        if hasattr(player, 'recent_performance'):
            score *= (0.8 + 0.2 * min(player.recent_performance, 1.5))

        # Batting order boost for cash
        if hasattr(player, 'batting_order'):
            if 1 <= player.batting_order <= 3:
                score *= 1.15
            elif 4 <= player.batting_order <= 5:
                score *= 1.05

        return score

    def _score_showdown(self, player, base_score: float) -> float:
        """Showdown scoring"""
        score = base_score

        # Captain eligibility boost
        if hasattr(player, 'is_captain_eligible'):
            if player.is_captain_eligible:
                score *= 1.2

        # Game total matters more in showdown
        if hasattr(player, 'vegas_total'):
            if player.vegas_total > 8:
                score *= 1.15

        return score

    def _apply_strategy_adjustments(self, player, score: float, strategy: str) -> float:
        """Apply strategy-specific score adjustments"""

        if 'stack' in strategy.lower():
            # Boost players in same game/team
            if hasattr(player, 'team_stack_score'):
                score *= (1.0 + 0.1 * player.team_stack_score)

        elif 'correlation' in strategy.lower():
            # Boost correlated players
            if hasattr(player, 'correlation_score'):
                score *= (1.0 + 0.15 * player.correlation_score)

        elif 'contrarian' in strategy.lower():
            # Boost low ownership more
            if hasattr(player, 'ownership_projection'):
                if player.ownership_projection < 5:
                    score *= 1.35

        return score

    # Compatibility methods for legacy code
    def score_player_gpp(self, player):
        """Legacy GPP scoring method"""
        return self.score_player(player, 'gpp')

    def score_player_cash(self, player):
        """Legacy cash scoring method"""
        return self.score_player(player, 'cash')

    def score_player_showdown(self, player):
        """Legacy showdown scoring method"""
        return self.score_player(player, 'showdown')


# Create instance for backward compatibility
default_engine = UnifiedScoringEngine()

# Exports
__all__ = ['UnifiedScoringEngine', 'default_engine']
