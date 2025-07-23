#!/usr/bin/env python3
"""
ENHANCED PURE SCORING ENGINE - Fixed Weights + Environmental Factors
==================================================================
Best for large GPPs where ceiling matters more than consistency
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from weather_integration import get_weather_integration
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EnhancedPureConfig:
    """Configuration for enhanced pure scoring"""

    # FIXED weights - never redistribute
    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "base": 0.35,
            "recent_form": 0.25,
            "vegas": 0.20,
            "matchup": 0.15,
            "batting_order": 0.05
        }
    )

    # Environmental factors
    park_factors: Dict[str, float] = field(
        default_factory=lambda: {
            'COL': 1.15,  # Coors Field
            'TEX': 1.08,  # Globe Life
            'ARI': 1.06,  # Chase Field
            'TOR': 1.05,  # Rogers Centre
            'KC': 1.04,  # Kauffman
            'CIN': 1.03,  # Great American
            'MIL': 1.02,  # American Family
            'BAL': 1.02,  # Camden Yards
            'HOU': 1.01,  # Minute Maid
            'CWS': 1.01,  # Guaranteed Rate
            'BOS': 1.00,  # Fenway
            'NYY': 1.00,  # Yankee Stadium
            'PHI': 0.99,  # Citizens Bank
            'MIN': 0.99,  # Target Field
            'LAD': 0.98,  # Dodger Stadium
            'CLE': 0.98,  # Progressive
            'ATL': 0.97,  # Truist Park
            'CHC': 0.97,  # Wrigley
            'DET': 0.96,  # Comerica
            'NYM': 0.96,  # Citi Field
            'SD': 0.95,  # Petco
            'SEA': 0.95,  # T-Mobile
            'STL': 0.94,  # Busch
            'LAA': 0.94,  # Angel Stadium
            'OAK': 0.93,  # Oakland Coliseum
            'TB': 0.93,  # Tropicana
            'MIA': 0.92,  # Marlins Park
            'SF': 0.91,  # Oracle Park
            'PIT': 0.90,  # PNC Park
            'WAS': 0.90,  # Nationals Park
        }
    )

    # Weather impact ranges
    weather_impacts: Dict[str, float] = field(
        default_factory=lambda: {
            'ideal': 1.15,  # Perfect hitting weather
            'good': 1.05,  # Good conditions
            'neutral': 1.00,  # Average
            'pitcher': 0.95,  # Favors pitching
            'poor': 0.85  # Bad weather
        }
    )


class EnhancedPureScoringEngine:
    """
    Enhanced pure scoring with environmental factors
    Fixed weights + park/weather adjustments
    """

    def __init__(self, config: Optional[EnhancedPureConfig] = None):
        self.config = config or EnhancedPureConfig()
        self._cache = {}
        self._calculation_count = 0

        # Data source connections
        self.statcast_fetcher = None
        self.vegas_client = None
        self.confirmation_system = None

        # Initialize weather integration
        self.weather_integration = get_weather_integration()

        logger.info("Enhanced Pure Scoring Engine initialized")
        logger.info(f"Fixed weights: {self.config.weights}")

    def set_data_sources(self, statcast_fetcher=None, vegas_client=None, confirmation_system=None):
        """Connect data sources for enrichment"""
        self.statcast_fetcher = statcast_fetcher
        self.vegas_client = vegas_client
        self.confirmation_system = confirmation_system

    def calculate_score(self, player: Any) -> float:
        """
        Calculate enhanced pure score with environmental factors
        """
        # Check cache
        cache_key = self._generate_cache_key(player)
        if cache_key in self._cache:
            cached_score, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < 300:  # 5 min cache
                return cached_score

        # Get base projection
        base_score = self._get_base_score(player)
        if base_score <= 0:
            logger.warning(f"{player.name}: No valid base projection - score = 0")
            return 0

        # Calculate fixed-weight score
        pure_score = self._calculate_pure_score(player, base_score)

        # Apply environmental multipliers
        env_multiplier = self._calculate_environmental_multiplier(player)

        # Final enhanced score
        enhanced_score = pure_score * env_multiplier

        # Store in cache
        self._cache[cache_key] = (enhanced_score, datetime.now())

        # Store audit trail
        self._store_audit_trail(player, base_score, pure_score, enhanced_score, env_multiplier)

        return enhanced_score

    def _get_base_score(self, player: Any) -> float:
        """Get base projection score"""
        base_score = 0.0

        # Priority order
        if hasattr(player, "base_projection") and player.base_projection > 0:
            base_score = float(player.base_projection)
        elif hasattr(player, "dff_projection") and player.dff_projection > 0:
            base_score = float(player.dff_projection)
        elif hasattr(player, "projection") and player.projection > 0:
            base_score = float(player.projection)

        return base_score

    def _calculate_pure_score(self, player: Any, base_score: float) -> float:
        """Calculate score with fixed weights (no redistribution)"""
        # Base contribution (always present)
        score = base_score * self.config.weights["base"]

        # Recent form
        if hasattr(player, "_recent_performance") and player._recent_performance:
            form_mult = player._recent_performance.get("form_score", 1.0)
            contribution = base_score * form_mult * self.config.weights["recent_form"]
            score += contribution

        # Vegas
        if hasattr(player, "_vegas_data") and player._vegas_data:
            vegas_mult = self._get_vegas_multiplier(player._vegas_data)
            contribution = base_score * vegas_mult * self.config.weights["vegas"]
            score += contribution

        # Matchup
        if hasattr(player, "_statcast_data") and player._statcast_data:
            matchup_mult = self._get_matchup_multiplier(player._statcast_data)
            contribution = base_score * matchup_mult * self.config.weights["matchup"]
            score += contribution

        # Batting order (hitters only)
        if player.primary_position != "P" and hasattr(player, "batting_order") and player.batting_order:
            order_mult = self._get_batting_order_multiplier(player.batting_order)
            contribution = base_score * order_mult * self.config.weights["batting_order"]
            score += contribution

        return score

    def _calculate_environmental_multiplier(self, player: Any) -> float:
        """Calculate park and weather impacts"""
        multiplier = 1.0

        # Park factor
        team = getattr(player, 'team', '')
        if team in self.config.park_factors:
            park_factor = self.config.park_factors[team]

            # Invert for pitchers
            if player.primary_position == 'P':
                park_factor = 2.0 - park_factor

            # Apply with 70% weight (30% neutral)
            multiplier *= (0.3 + 0.7 * park_factor)

        # Weather impact - NOW USING REAL DATA!
        weather_mult = self._get_real_weather_multiplier(player)

        # Apply with 30% weight (70% neutral)
        multiplier *= (0.7 + 0.3 * weather_mult)

        return multiplier

    def _get_vegas_multiplier(self, vegas_data: Dict) -> float:
        """Convert Vegas total to multiplier"""
        implied_total = vegas_data.get("implied_total", 4.5)

        # Scale: 3.0 = 0.8x, 4.5 = 1.0x, 6.0 = 1.2x
        multiplier = 0.8 + (implied_total - 3.0) * 0.133

        return max(0.7, min(1.3, multiplier))

    def _get_matchup_multiplier(self, statcast_data: Dict) -> float:
        """Convert matchup data to multiplier"""
        # Simple barrel rate based for now
        barrel_rate = statcast_data.get("barrel_rate", 8.0)

        # Scale: 5% = 0.85x, 8% = 1.0x, 15% = 1.25x
        multiplier = 0.85 + (barrel_rate - 5.0) * 0.0286

        return max(0.75, min(1.25, multiplier))

    def _get_batting_order_multiplier(self, order: int) -> float:
        """Batting order impact"""
        order_mults = {
            1: 1.10, 2: 1.08, 3: 1.08, 4: 1.06,
            5: 1.04, 6: 1.02, 7: 1.00, 8: 0.98, 9: 0.96
        }
        return order_mults.get(order, 1.0)

    def _get_real_weather_multiplier(self, player: Any) -> float:
        """Get real weather impact using weather integration"""
        team = getattr(player, 'team', '')
        if not team:
            return 1.0

        try:
            # Get real weather data
            weather_data = self.weather_integration.get_weather_for_game(team)

            # Calculate impact
            is_pitcher = player.primary_position == 'P'
            weather_impact = self.weather_integration.calculate_weather_impact(
                weather_data,
                is_pitcher=is_pitcher
            )

            # Store weather info for audit
            if not hasattr(player, '_weather_data'):
                player._weather_data = {
                    'temperature': weather_data.temperature,
                    'wind_speed': weather_data.wind_speed,
                    'wind_direction': weather_data.wind_direction,
                    'condition': weather_data.condition,
                    'impact': weather_impact
                }

            logger.debug(f"{player.name} ({team}): Weather impact {weather_impact:.2f}x")

            return weather_impact

        except Exception as e:
            logger.warning(f"Weather fetch failed for {player.name}: {e}")
            # Fallback to simplified weather
            return self._get_weather_multiplier(player)

    def _generate_cache_key(self, player: Any) -> tuple:
        """Generate cache key for player"""
        return (
            getattr(player, "id", player.name),
            getattr(player, "base_projection", 0),
            getattr(player, "batting_order", 0),
            len(getattr(player, "recent_scores", [])),
            hash(str(getattr(player, "_vegas_data", {}))),
        )

    def _store_audit_trail(self, player: Any, base_score: float, pure_score: float,
                           enhanced_score: float, env_mult: float):
        """Store scoring audit trail"""
        audit = {
            "base_score": base_score,
            "pure_score": pure_score,
            "environmental_multiplier": env_mult,
            "final_score": enhanced_score,
            "timestamp": datetime.now().isoformat(),
            "scoring_method": "enhanced_pure",
            "data_completeness": self._calculate_data_completeness(player),
            "weather_data": getattr(player, '_weather_data', None)  # Add weather to audit
        }

        player._score_audit = audit
        player._score_components = audit  # Backwards compatibility

    def _calculate_data_completeness(self, player: Any) -> float:
        """Calculate what percentage of data is available"""
        checks = [
            hasattr(player, "base_projection") and player.base_projection > 0,
            hasattr(player, "_vegas_data") and bool(player._vegas_data),
            hasattr(player, "_recent_performance") and bool(player._recent_performance),
            hasattr(player, "_statcast_data") and bool(player._statcast_data),
            hasattr(player, "batting_order") and bool(player.batting_order)
        ]

        return sum(checks) / len(checks)

    def clear_cache(self):
        """Clear score cache"""
        self._cache.clear()
        logger.info("Enhanced pure score cache cleared")


# Singleton instance
_enhanced_engine_instance = None


def get_enhanced_pure_engine(config: Optional[EnhancedPureConfig] = None) -> EnhancedPureScoringEngine:
    """Get or create enhanced pure scoring engine instance"""
    global _enhanced_engine_instance

    if _enhanced_engine_instance is None:
        _enhanced_engine_instance = EnhancedPureScoringEngine(config)
    elif config is not None:
        _enhanced_engine_instance.config = config
        _enhanced_engine_instance.clear_cache()

    return _enhanced_engine_instance