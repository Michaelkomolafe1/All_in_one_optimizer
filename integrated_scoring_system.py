#!/usr/bin/env python3
"""
FULLY INTEGRATED CORRELATION SCORING SYSTEM
==========================================
Replaces unified_scoring_engine.py with the proven correlation-aware approach
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# Import the winning configuration
from correlation_scoring_config import CorrelationAwareScoringConfig, CorrelationAwareScorer

logger = logging.getLogger(__name__)


class IntegratedScoringEngine:
    """
    Complete replacement for UnifiedScoringEngine
    Uses ONLY the correlation-aware scoring that won your tests
    """

    def __init__(self):
        # Initialize configs for both contest types
        self.gpp_config = self._create_gpp_config()
        self.cash_config = self._create_cash_config()

        # Create scorers
        self.gpp_scorer = CorrelationAwareScorer(self.gpp_config)
        self.cash_scorer = CorrelationAwareScorer(self.cash_config)

        # Default to GPP
        self.current_scorer = self.gpp_scorer
        self.contest_type = "gpp"

        # Cache for performance
        self._score_cache = {}
        self._team_totals_cache = {}

        logger.info("Integrated Correlation Scoring System initialized")

    def _create_gpp_config(self) -> CorrelationAwareScoringConfig:
        """GPP configuration - aggressive stacking"""
        config = CorrelationAwareScoringConfig()
        # Use defaults from winning config
        return config

    def _create_cash_config(self) -> CorrelationAwareScoringConfig:
        """Cash configuration - conservative approach"""
        config = CorrelationAwareScoringConfig()

        # Reduce bonuses for cash games
        config.team_total_boost = 1.08  # Down from 1.15
        config.batting_order_boost = 1.05  # Down from 1.10

        # Adjust correlation factors
        config.correlation_factors = {
            "consecutive_order_bonus": 0.02,  # Down from 0.05
            "same_team_pitcher_penalty": -0.30,  # Stronger penalty
            "mini_stack_bonus": 0.03,  # Down from 0.08
            "full_stack_bonus": 0.05,  # Down from 0.12
            "game_total_high": 0.03,  # Down from 0.05
            "game_total_low": -0.08,  # Stronger penalty
        }

        return config

    def set_contest_type(self, contest_type: str, slate_size: int = 0) -> str:
        """
        Set contest type and return scoring method name
        This maintains compatibility with existing code
        """
        contest_type = contest_type.lower()

        if contest_type in ['cash', '50-50', '50/50', 'double-up']:
            self.contest_type = 'cash'
            self.current_scorer = self.cash_scorer
            return 'correlation_cash'
        else:
            self.contest_type = 'gpp'
            self.current_scorer = self.gpp_scorer
            return 'correlation_gpp'

    def calculate_score(self, player: Any) -> float:
        """
        Main scoring method - replaces all complex calculations
        """
        # Check cache first
        cache_key = f"{player.name}_{player.team}_{self.contest_type}"
        if cache_key in self._score_cache:
            return self._score_cache[cache_key]

        # Get base projection
        base_score = self._get_base_projection(player)
        if base_score <= 0:
            return 0

        score = base_score

        # 1. Team Total Boost (PRIMARY FACTOR)
        team_total = self._get_team_total(player)
        if team_total >= self.current_scorer.config.team_total_threshold:
            score *= self.current_scorer.config.team_total_boost
            logger.debug(f"{player.name}: Team boost applied ({team_total:.1f} runs)")

        # 2. Batting Order Boost (SECONDARY FACTOR)
        if player.primary_position != "P":
            batting_order = getattr(player, 'batting_order', 0)
            if batting_order in self.current_scorer.config.premium_batting_positions:
                score *= self.current_scorer.config.batting_order_boost
                logger.debug(f"{player.name}: Order boost applied (batting {batting_order})")

        # 3. Simple Park Factor
        park_multiplier = self._get_park_multiplier(player)
        score *= park_multiplier

        # 4. Contest type weighting
        if self.contest_type == 'cash':
            # Reduce variance for cash
            score = score * 0.8 + base_score * 0.2

        # Cache and return
        self._score_cache[cache_key] = score
        return score

    def _get_base_projection(self, player: Any) -> float:
        """Get base fantasy points projection"""
        # Priority order for projections
        if hasattr(player, 'dk_projection') and player.dk_projection > 0:
            return player.dk_projection
        elif hasattr(player, 'fantasy_points_per_game') and player.fantasy_points_per_game > 0:
            return player.fantasy_points_per_game
        elif hasattr(player, 'projected_points') and player.projected_points > 0:
            return player.projected_points
        else:
            # Fallback based on salary
            return player.salary / 1000 * 2.0

    def _get_team_total(self, player: Any) -> float:
        """Get team's projected run total"""
        # Check cache
        if player.team in self._team_totals_cache:
            return self._team_totals_cache[player.team]

        team_total = 4.5  # Default

        # Try various attributes
        if hasattr(player, 'team_total') and player.team_total > 0:
            team_total = player.team_total
        elif hasattr(player, 'implied_total') and player.implied_total > 0:
            team_total = player.implied_total
        elif hasattr(player, 'vegas_total') and player.vegas_total > 0:
            team_total = player.vegas_total / 2  # Divide game total by 2

        self._team_totals_cache[player.team] = team_total
        return team_total

    def _get_park_multiplier(self, player: Any) -> float:
        """Simple park factor adjustment"""
        # Get park
        park = getattr(player, 'game_park', None) or getattr(player, 'park', 'neutral')

        # Map to category
        hitter_parks = ['COL', 'CIN', 'TEX', 'BAL', 'NYY']
        pitcher_parks = ['MIA', 'SD', 'LAD', 'SEA', 'SF']

        if any(p in str(park).upper() for p in hitter_parks):
            multiplier = 1.05 if player.primary_position != 'P' else 0.95
        elif any(p in str(park).upper() for p in pitcher_parks):
            multiplier = 0.95 if player.primary_position != 'P' else 1.05
        else:
            multiplier = 1.0

        return multiplier

    def calculate_correlation_bonus(self, players: List[Any]) -> float:
        """
        Calculate correlation bonus for a group of players
        Used by the optimizer to evaluate stacks
        """
        if len(players) < 2:
            return 0

        bonus = 0
        same_team_groups = {}

        # Group by team
        for player in players:
            team = player.team
            if team not in same_team_groups:
                same_team_groups[team] = []
            same_team_groups[team].append(player)

        # Calculate bonuses
        for team, team_players in same_team_groups.items():
            if len(team_players) >= 2:
                # Stack size bonus
                if len(team_players) >= 4:
                    bonus += self.current_scorer.config.correlation_factors['full_stack_bonus']
                else:
                    bonus += self.current_scorer.config.correlation_factors['mini_stack_bonus']

                # Consecutive order bonus
                batting_orders = sorted([
                    getattr(p, 'batting_order', 99)
                    for p in team_players
                    if p.primary_position != 'P'
                ])

                if len(batting_orders) >= 2:
                    for i in range(len(batting_orders) - 1):
                        if batting_orders[i + 1] - batting_orders[i] == 1:
                            bonus += self.current_scorer.config.correlation_factors['consecutive_order_bonus']

        return bonus

    def get_scoring_summary(self) -> Dict[str, Any]:
        """Get current scoring configuration summary"""
        config = self.current_scorer.config
        return {
            'contest_type': self.contest_type,
            'team_total_threshold': config.team_total_threshold,
            'team_total_boost': config.team_total_boost,
            'batting_order_boost': config.batting_order_boost,
            'correlation_factors': config.correlation_factors,
            'method': f'correlation_{self.contest_type}'
        }

    def clear_cache(self):
        """Clear scoring caches"""
        self._score_cache.clear()
        self._team_totals_cache.clear()
        logger.info("Scoring caches cleared")


def patch_unified_core_system():
    """
    Patch UnifiedCoreSystem to use the new integrated scoring
    """
    try:
        from unified_core_system import UnifiedCoreSystem

        # Replace the scoring engine initialization
        original_init = UnifiedCoreSystem.__init__

        def new_init(self, *args, **kwargs):
            # Call original init
            original_init(self, *args, **kwargs)
            # Replace scoring engine
            self.scoring_engine = IntegratedScoringEngine()
            logger.info("✅ Integrated correlation scoring system active")

        UnifiedCoreSystem.__init__ = new_init

        logger.info("✅ UnifiedCoreSystem patched successfully")

    except ImportError:
        logger.error("Could not import UnifiedCoreSystem for patching")


# Auto-patch on import
patch_unified_core_system()

if __name__ == "__main__":
    # Test the integrated system
    from types import SimpleNamespace

    # Create test player
    test_player = SimpleNamespace(
        name="Aaron Judge",
        team="NYY",
        primary_position="OF",
        salary=11000,
        dk_projection=12.5,
        team_total=5.8,
        batting_order=2,
        game_park="NYY"
    )

    # Test scoring
    engine = IntegratedScoringEngine()

    print("Testing Integrated Scoring Engine")
    print("=" * 50)

    # Test GPP scoring
    engine.set_contest_type('gpp')
    gpp_score = engine.calculate_score(test_player)
    print(f"GPP Score: {gpp_score:.2f}")

    # Test Cash scoring
    engine.set_contest_type('cash')
    cash_score = engine.calculate_score(test_player)
    print(f"Cash Score: {cash_score:.2f}")

    # Show configuration
    print("\nCurrent Configuration:")
    summary = engine.get_scoring_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")