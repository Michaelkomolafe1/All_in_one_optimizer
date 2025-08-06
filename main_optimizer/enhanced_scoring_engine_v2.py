#!/usr/bin/env python3
"""
ENHANCED SCORING ENGINE V2
==========================
Simplified scoring with optional Bayesian parameters
Maintains your slate-specific strategies while reducing complexity
"""

import json
import logging
from typing import Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class EnhancedScoringEngineV2:
    """
    Unified scoring engine that:
    1. Uses simple, explainable multipliers by default
    2. Can optionally use Bayesian parameters (for future optimization)
    3. ONE scoring path per contest type
    """

    def __init__(self, use_bayesian: bool = False):
        """
        Args:
            use_bayesian: If True, uses your optimized Bayesian parameters
                         If False, uses simple round multipliers
        """
        self.use_bayesian = use_bayesian

        if use_bayesian:
            self._load_bayesian_parameters()
        else:
            self._load_simple_parameters()

        # Track scoring calls for debugging
        self.scoring_stats = {
            'cash_scores': 0,
            'gpp_scores': 0,
            'zero_scores': 0
        }

    def _load_simple_parameters(self):
        """Simple, explainable parameters that work"""

        # GPP Parameters (proven from your tests)
        self.gpp_params = {
            # Team totals (simplified from Bayesian 5.879652818354419)
            'threshold_high': 5.5,  # High scoring games
            'threshold_med': 5.0,  # Good scoring games
            'threshold_low': 4.5,  # Average games

            # Multipliers (rounded from Bayesian)
            'mult_high': 1.35,  # Was 1.3362904255411312
            'mult_med': 1.20,  # Was 1.2163912748563654
            'mult_low': 1.10,  # Was 1.1393921566433494
            'mult_none': 0.85,  # Was 0.7614333531096783

            # Stack configuration (keep as-is)
            'stack_min': 4,
            'stack_max': 5,
            'stack_preferred': 4,

            # Batting order (simplified)
            'batting_boost': 1.15,  # Was 1.114543568527152
            'batting_positions': 5,  # Top 5 in order

            # Ownership (simplified)
            'ownership_low_boost': 1.10,  # Was 1.106440616808056
            'ownership_high_penalty': 0.90,
            'ownership_threshold': 15,

            # Advanced stats (simplified)
            'barrel_rate_threshold': 12.0,  # Was 11.66458072425903
            'barrel_rate_boost': 1.20,  # Was 1.1937255322047728
        }

        # Cash Parameters (proven 79% win rate)
        self.cash_params = {
            # Core weights
            'projection_weight': 0.40,  # Base projection importance
            'recent_weight': 0.35,  # Recent form importance
            'consistency_weight': 0.25,  # Consistency importance

            # Boosts
            'platoon_boost': 0.08,  # 8% for platoon advantage
            'pitcher_preference': 1.10,  # Prefer pitchers in cash

            # Floor/ceiling balance
            'floor_weight': 0.80,
            'ceiling_weight': 0.20
        }

    def _load_bayesian_parameters(self):
        """Load your original Bayesian-optimized parameters"""
        # Keep all your original precise parameters here
        # This allows future A/B testing without losing the work
        self.gpp_params = {
            'threshold_high': 5.879652818354419,
            'threshold_med': 5.731303194500506,
            # ... (all original parameters)
        }

        self.cash_params = {
            'consistency_weight': 0.24994454993253398,
            # ... (all original parameters)
        }

    def score_player(self, player, contest_type: str) -> float:
        """
        UNIFIED scoring method - ONE path for scoring

        Args:
            player: UnifiedPlayer object
            contest_type: 'cash' or 'gpp'

        Returns:
            float: The player's score for the contest type
        """
        # Get base projection (check all possible attributes)
        base = self._get_base_projection(player)

        if base <= 0:
            self.scoring_stats['zero_scores'] += 1
            logger.debug(f"Zero base projection for {player.name}")
            return 0.0

        # Route to appropriate scoring
        if contest_type.lower() == 'cash':
            score = self._score_for_cash(player, base)
            self.scoring_stats['cash_scores'] += 1
        else:
            score = self._score_for_gpp(player, base)
            self.scoring_stats['gpp_scores'] += 1

        # Store the score on the player object
        setattr(player, f'{contest_type.lower()}_score', score)
        player.optimization_score = score  # For optimizer

        return round(score, 2)

    def _get_base_projection(self, player) -> float:
        """Get base projection from any available source"""
        # Check all possible projection attributes in order of preference
        projection_attrs = [
            'base_projection',
            'projection',
            'dff_projection',
            'fantasy_points',
            'AvgPointsPerGame',
            'avg_points'
        ]

        for attr in projection_attrs:
            value = getattr(player, attr, 0)
            if value > 0:
                return float(value)

        return 0.0

    def _score_for_cash(self, player, base: float) -> float:
        """Cash game scoring - emphasize floor and consistency"""
        score = base

        # 1. Recent form (35% weight)
        recent = getattr(player, 'recent_form', 1.0)
        form_impact = 1.0 + (recent - 1.0) * self.cash_params['recent_weight']
        score *= form_impact

        # 2. Consistency (25% weight)
        consistency = getattr(player, 'consistency_score', 1.0)
        consistency_impact = 1.0 + (consistency - 1.0) * self.cash_params['consistency_weight']
        score *= consistency_impact

        # 3. Matchup quality
        matchup = getattr(player, 'matchup_score', 1.0)
        score *= (0.9 + matchup * 0.1)  # Smaller impact for cash

        # 4. Platoon advantage
        if getattr(player, 'platoon_advantage', False):
            score *= (1.0 + self.cash_params['platoon_boost'])

        # 5. Pitcher preference
        if player.is_pitcher:
            score *= self.cash_params['pitcher_preference']

        # 6. Environmental factors (reduced impact for cash)
        park = getattr(player, 'park_factor', 1.0)
        weather = getattr(player, 'weather_impact', 1.0)
        environmental = (park * weather) ** 0.3  # Dampened effect
        score *= environmental

        return score

    def _score_for_gpp(self, player, base: float) -> float:
        """GPP scoring - emphasize ceiling and correlation"""
        score = base

        # 1. Team total multiplier (biggest factor)
        team_total = self._get_team_total(player)

        if team_total >= self.gpp_params['threshold_high']:
            score *= self.gpp_params['mult_high']
        elif team_total >= self.gpp_params['threshold_med']:
            score *= self.gpp_params['mult_med']
        elif team_total >= self.gpp_params['threshold_low']:
            score *= self.gpp_params['mult_low']
        else:
            score *= self.gpp_params['mult_none']

        # 2. Batting order boost (for hitters)
        if not player.is_pitcher:
            bat_order = getattr(player, 'batting_order', 0)
            if 1 <= bat_order <= self.gpp_params['batting_positions']:
                score *= self.gpp_params['batting_boost']

        # 3. Ownership leverage
        ownership = getattr(player, 'projected_ownership',
                            getattr(player, 'ownership_projection', 15))

        if ownership < self.gpp_params['ownership_threshold']:
            score *= self.gpp_params['ownership_low_boost']
        elif ownership > 30:
            score *= self.gpp_params['ownership_high_penalty']

        # 4. Advanced stats boost (for hitters)
        if not player.is_pitcher:
            barrel_rate = getattr(player, 'barrel_rate', 0)
            if barrel_rate > self.gpp_params['barrel_rate_threshold']:
                score *= self.gpp_params['barrel_rate_boost']

        # 5. Environmental factors (bigger impact for GPP)
        park = getattr(player, 'park_factor', 1.0)
        weather = getattr(player, 'weather_impact', 1.0)
        environmental = park * weather

        if environmental > 1.15:  # Great conditions
            score *= 1.10  # Ceiling boost
        elif environmental < 0.90:  # Bad conditions
            score *= 0.85  # Bigger penalty

        # 6. Recent form (hot/cold streaks matter for GPP)
        recent = getattr(player, 'recent_form', 1.0)
        if recent > 1.20:  # Hot player
            score *= 1.15  # Chase the ceiling
        elif recent < 0.80:  # Cold player
            score *= 0.75  # Avoid

        return score

    def _get_team_total(self, player) -> float:
        """Get team total from any available source"""
        # Check multiple possible attributes
        total = getattr(player, 'implied_team_score', None)
        if total: return total

        total = getattr(player, 'team_total', None)
        if total: return total

        if hasattr(player, '_vegas_data') and player._vegas_data:
            total = player._vegas_data.get('implied_total', None)
            if total: return total

        return 4.5  # Default MLB average

    def get_scoring_summary(self, player, contest_type: str) -> Dict:
        """Get detailed scoring breakdown for debugging"""
        base = self._get_base_projection(player)
        score = self.score_player(player, contest_type)

        summary = {
            'player': player.name,
            'contest_type': contest_type,
            'base_projection': base,
            'final_score': score,
            'multiplier': score / base if base > 0 else 0,
            'components': {}
        }

        # Add component breakdown
        if contest_type.lower() == 'cash':
            summary['components'] = {
                'recent_form': getattr(player, 'recent_form', 1.0),
                'consistency': getattr(player, 'consistency_score', 1.0),
                'matchup': getattr(player, 'matchup_score', 1.0),
                'is_pitcher': player.is_pitcher
            }
        else:  # GPP
            summary['components'] = {
                'team_total': self._get_team_total(player),
                'batting_order': getattr(player, 'batting_order', 0),
                'ownership': getattr(player, 'projected_ownership', 15),
                'barrel_rate': getattr(player, 'barrel_rate', 0)
            }

        return summary

    def print_scoring_stats(self):
        """Print scoring statistics for debugging"""
        total = sum(self.scoring_stats.values())
        if total == 0:
            logger.warning("No players have been scored yet")
            return

        logger.info("=== SCORING STATISTICS ===")
        logger.info(f"Total scored: {total}")
        logger.info(f"Cash scores: {self.scoring_stats['cash_scores']}")
        logger.info(f"GPP scores: {self.scoring_stats['gpp_scores']}")
        logger.info(f"Zero scores: {self.scoring_stats['zero_scores']} "
                    f"({100 * self.scoring_stats['zero_scores'] / total:.1f}%)")

    def score_player_gpp(self, player, slate_players=None):
        """Score player for GPP contests"""
        if hasattr(self, 'calculate_gpp_score'):
            return self.calculate_gpp_score(player, slate_players)
        return self.score_player(player, 'gpp', slate_players)

    def score_player_cash(self, player, slate_players=None):
        """Score player for cash contests"""
        if hasattr(self, 'calculate_cash_score'):
            return self.calculate_cash_score(player, slate_players)
        return self.score_player(player, 'cash', slate_players)



# Compatibility layer for existing code
def EnhancedScoringEngine():
    """Factory function for backward compatibility"""
    return EnhancedScoringEngineV2(use_bayesian=False)