#!/usr/bin/env python3
"""
STEP 2: Updated Player Model Integration
=======================================
Integrates the winning correlation-aware scoring with contest-specific adjustments
"""

from typing import Dict, Optional, List, Any
from dataclasses import dataclass
import logging

# Import your new configuration
from correlation_scoring_config import CorrelationAwareScoringConfig, CorrelationAwareScorer

logger = logging.getLogger(__name__)


class SimplifiedScoringEngine:
    """
    Replaces the complex UnifiedScoringEngine with the winning approach
    Two modes: GPP (full correlation) and Cash (consistency focused)
    """

    def __init__(self):
        # Initialize both scoring configs
        self.gpp_config = CorrelationAwareScoringConfig()
        self.cash_config = self._create_cash_config()

        # Create scorers for each contest type
        self.gpp_scorer = CorrelationAwareScorer(self.gpp_config)
        self.cash_scorer = CorrelationAwareScorer(self.cash_config)

        # Default to GPP
        self.current_scorer = self.gpp_scorer
        self.contest_type = "gpp"

        logger.info("Simplified Scoring Engine initialized with dual modes")

    def _create_cash_config(self) -> CorrelationAwareScoringConfig:
        """Create a modified config for cash games"""
        config = CorrelationAwareScoringConfig()

        # Reduce correlation bonuses for cash
        config.team_total_boost = 1.08  # Down from 1.15
        config.batting_order_boost = 1.05  # Down from 1.10

        # Adjust correlation factors for cash
        config.correlation_factors = {
            "consecutive_order_bonus": 0.02,  # Down from 0.05
            "same_team_pitcher_penalty": -0.30,  # Stronger penalty
            "mini_stack_bonus": 0.03,  # Down from 0.08
            "full_stack_bonus": 0.05,  # Down from 0.12
            "game_total_high": 0.03,  # Down from 0.05
            "game_total_low": -0.08,  # Bigger penalty
        }

        return config

    def set_contest_type(self, contest_type: str) -> str:
        """Switch between GPP and Cash scoring modes"""
        self.contest_type = contest_type.lower()

        if self.contest_type in ["cash", "50-50", "double-up"]:
            self.current_scorer = self.cash_scorer
            mode = "cash"
        else:
            self.current_scorer = self.gpp_scorer
            mode = "gpp"

        logger.info(f"Scoring mode set to: {mode.upper()}")
        return mode

    def calculate_score(self, player: Any) -> float:
        """
        Calculate player score using the winning correlation-aware method
        """
        # Use the current scorer (GPP or Cash)
        base_score = self.current_scorer.calculate_score(player, self.contest_type)

        # Add consistency bonus for cash games
        if self.contest_type == "cash":
            consistency_bonus = self._calculate_consistency_bonus(player)
            base_score *= consistency_bonus

        return base_score

    def _calculate_consistency_bonus(self, player: Any) -> float:
        """
        Cash games want consistent players
        Returns multiplier between 0.9 and 1.1
        """
        bonus = 1.0

        # Check recent consistency
        if hasattr(player, 'recent_consistency') and player.recent_consistency > 0:
            if player.recent_consistency > 0.8:
                bonus *= 1.05  # Reward consistency
            elif player.recent_consistency < 0.5:
                bonus *= 0.95  # Penalize volatility

        # Check floor/ceiling ratio
        if hasattr(player, 'recent_floor') and hasattr(player, 'recent_ceiling'):
            if player.recent_ceiling > 0:
                floor_ceiling_ratio = player.recent_floor / player.recent_ceiling
                if floor_ceiling_ratio > 0.6:
                    bonus *= 1.03  # Good floor
                elif floor_ceiling_ratio < 0.3:
                    bonus *= 0.97  # Too volatile

        return bonus


def update_unified_player_calculate_score(self):
    """
    REPLACEMENT METHOD for UnifiedPlayer.calculate_enhanced_score()
    This is what you'll use to replace the complex scoring in your player model
    """
    # Get the simplified scoring engine (singleton pattern)
    if not hasattr(self, '_scoring_engine'):
        self._scoring_engine = SimplifiedScoringEngine()

    # Calculate score with the simplified method
    score = self._scoring_engine.calculate_score(self)

    # Store the results
    self.enhanced_score = score
    self.optimization_score = score  # For MILP

    # Store audit info
    self._score_audit = {
        "method": "correlation_aware",
        "contest_type": self._scoring_engine.contest_type,
        "base_projection": getattr(self, 'base_projection', 0),
        "team_total": self._get_team_total(),
        "batting_order": getattr(self, 'batting_order', 0),
        "final_score": score
    }

    # Update data quality based on what we actually need
    self._update_data_quality_simple()

    return score


def _get_team_total(self) -> float:
    """Helper to get team total from various sources"""
    if hasattr(self, 'team_total') and self.team_total > 0:
        return self.team_total
    elif hasattr(self, 'implied_team_score') and self.implied_team_score:
        return self.implied_team_score
    elif hasattr(self, '_vegas_data') and self._vegas_data:
        return self._vegas_data.get('implied_total', 0)
    return 0


def _update_data_quality_simple(self):
    """
    Simplified data quality calculation
    We only care about the data that matters for correlation scoring
    """
    quality_checks = {
        'has_projection': bool(getattr(self, 'base_projection', 0) > 0),
        'has_vegas': bool(self._get_team_total() > 0),
        'has_batting_order': bool(getattr(self, 'batting_order', 0) > 0),
        'has_team': bool(getattr(self, 'team', None))
    }

    # Calculate quality score (0-1)
    self.data_quality_score = sum(quality_checks.values()) / len(quality_checks)

    # We really only NEED projection and team for basic scoring
    self.has_minimum_data = quality_checks['has_projection'] and quality_checks['has_team']


# Example integration function
def integrate_with_existing_player_model():
    """
    Shows how to integrate this with your existing UnifiedPlayer class
    """
    # In your unified_player_model.py, replace calculate_enhanced_score with:
    print("""
    # In unified_player_model.py, replace the calculate_enhanced_score method:

    def calculate_enhanced_score(self):
        '''Calculate score using simplified correlation-aware method'''
        # Import the update function
        from step2_updated_player_model import update_unified_player_calculate_score

        # Call the new simplified scoring
        return update_unified_player_calculate_score(self)
    """)

    # Also update the initialization to remove complex scoring engines
    print("""
    # Remove these imports from unified_player_model.py:
    # - from unified_scoring_engine import ...
    # - from hybrid_scoring_system import ...
    # - from dynamic_weight_engine import ...

    # Keep only:
    # - Basic player attributes
    # - Data loading methods
    # - The new simplified scoring
    """)


if __name__ == "__main__":
    print("🎯 STEP 2: Simplified Scoring Integration")
    print("=" * 60)

    # Show the two scoring modes
    engine = SimplifiedScoringEngine()

    print("\n📊 Scoring Modes:")
    print("\n1. GPP Mode (Default):")
    print(f"   - Team total > 5: {engine.gpp_config.team_total_boost}x boost")
    print(f"   - Top 4 batting order: {engine.gpp_config.batting_order_boost}x boost")
    print(f"   - Full stack bonus: +{engine.gpp_config.correlation_factors['full_stack_bonus'] * 100}%")

    print("\n2. Cash Mode:")
    print(f"   - Team total > 5: {engine.cash_config.team_total_boost}x boost")
    print(f"   - Top 4 batting order: {engine.cash_config.batting_order_boost}x boost")
    print(f"   - Consistency bonus: 0.9x to 1.1x")
    print(f"   - Limited stacking: +{engine.cash_config.correlation_factors['mini_stack_bonus'] * 100}%")

    print("\n✅ Ready to integrate!")
    print("\nNext steps:")
    print("1. Replace calculate_enhanced_score() in unified_player_model.py")
    print("2. Remove imports for complex scoring engines")
    print("3. Test with both cash and GPP contests")

    integrate_with_existing_player_model()