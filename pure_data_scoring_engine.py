#!/usr/bin/env python3
"""
PURE DATA SCORING ENGINE - Fixed Weight System
=============================================
No fallbacks, no weight redistribution, pure data-driven scoring
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PureDataScoringConfig:
    """Configuration for pure data scoring - NO FALLBACKS"""

    # FIXED weights - always sum to 1.0, never redistribute
    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "base": 0.35,  # Base projection (required)
            "recent_form": 0.25,  # Recent performance
            "vegas": 0.20,  # Vegas implied totals
            "matchup": 0.15,  # Statcast matchup data
            "batting_order": 0.05  # Lineup position
        }
    )

    # Component requirements - if missing, score = 0
    required_components: List[str] = field(
        default_factory=lambda: ["base"]  # Only base is absolutely required
    )

    # Multiplier bounds for components
    bounds: Dict[str, Tuple[float, float]] = field(
        default_factory=lambda: {
            "recent_form": (0.50, 1.50),  # ±50% for hot/cold streaks
            "vegas": (0.70, 1.30),  # ±30% for Vegas
            "matchup": (0.75, 1.25),  # ±25% for matchups
            "batting_order": (0.90, 1.15),  # Small boost for top of order
            "final": (0.00, 2.00),  # ← CHANGED: No minimum bound
        }
    )

    # Validation thresholds
    validation: Dict[str, float] = field(
        default_factory=lambda: {
            "min_projection": 0.0,
            "max_projection": 50.0,  # Reasonable MLB DFS max
            "min_salary": 2000,
            "max_salary": 15000,
            "min_implied_total": 2.0,
            "max_implied_total": 15.0,
        }
    )


class PureDataScoringEngine:
    """
    Pure data-driven scoring engine with fixed weights
    NO FALLBACKS - if data is missing, that component contributes 0
    """

    def __init__(self, config: Optional[PureDataScoringConfig] = None):
        self.config = config or PureDataScoringConfig()
        self._cache = {}
        self._missing_data_players = set()

        # Load park factors once
        try:
            from park_factors import PARK_FACTORS
            self.park_factors = {team: data['factor'] for team, data in PARK_FACTORS.items()}
        except:
            self.park_factors = {}

        logger.info("Pure Data Scoring Engine initialized")
        logger.info(f"Fixed weights: {self.config.weights}")

    def calculate_score(self, player: Any) -> float:
        """
        Calculate player score with FIXED weights
        Missing data = 0 contribution, no redistribution
        """
        # Check cache
        cache_key = (player.id, getattr(player, "base_projection", 0))
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Get base projection (REQUIRED)
        base_score = self._get_base_projection(player)
        if base_score <= 0:
            logger.warning(f"{player.name}: No valid base projection - score = 0")
            self._missing_data_players.add(player.name)
            return 0.0

        # Calculate final score with FIXED weights
        final_score = self._calculate_fixed_weight_score(player, base_score)

        # Cache and return
        self._cache[cache_key] = final_score
        player.pure_data_score = final_score
        player.optimization_score = final_score  # Direct assignment for MILP

        return final_score

    def _get_base_projection(self, player: Any) -> float:
        """Get base projection - NO FALLBACKS"""
        # Only use explicit base_projection field
        base = getattr(player, "base_projection", 0)

        # Validate
        if base < self.config.validation["min_projection"]:
            return 0.0
        if base > self.config.validation["max_projection"]:
            logger.warning(f"{player.name}: Capping projection {base} to max")
            return self.config.validation["max_projection"]

        return float(base)

    def _calculate_fixed_weight_score(self, player: Any, base_score: float) -> float:
        """
        Calculate score using FIXED weights
        Each component either contributes its full weight or 0
        """
        # Start with base contribution (always present)
        final_score = base_score * self.config.weights["base"]

        # Track what data we have for audit
        components_used = {"base": 1.0}

        # Recent Form Component
        recent_mult = self._get_recent_form_multiplier(player)
        if recent_mult is not None:
            contribution = base_score * recent_mult * self.config.weights["recent_form"]
            final_score += contribution
            components_used["recent_form"] = recent_mult
        else:
            # Missing data = 0 contribution (not redistributed)
            logger.debug(f"{player.name}: No recent form data")

        # Vegas Component
        vegas_mult = self._get_vegas_multiplier(player)
        if vegas_mult is not None:
            contribution = base_score * vegas_mult * self.config.weights["vegas"]
            final_score += contribution
            components_used["vegas"] = vegas_mult
        else:
            logger.debug(f"{player.name}: No Vegas data")

        # Matchup Component
        matchup_mult = self._get_matchup_multiplier(player)
        if matchup_mult is not None:
            contribution = base_score * matchup_mult * self.config.weights["matchup"]
            final_score += contribution
            components_used["matchup"] = matchup_mult
        else:
            logger.debug(f"{player.name}: No matchup data")

        # Batting Order Component (hitters only)
        if player.primary_position != "P":
            order_mult = self._get_batting_order_multiplier(player)
            if order_mult is not None:
                contribution = base_score * order_mult * self.config.weights["batting_order"]
                final_score += contribution
                components_used["batting_order"] = order_mult
            else:
                logger.debug(f"{player.name}: No batting order")

        # Apply final bounds
        min_allowed = base_score * self.config.bounds["final"][0]
        max_allowed = base_score * self.config.bounds["final"][1]
        final_score = max(min_allowed, min(final_score, max_allowed))

        # Store audit trail
        self._store_audit(player, base_score, components_used, final_score)

        return final_score

    def _get_recent_form_multiplier(self, player: Any) -> Optional[float]:
        """Get recent form multiplier - pure data only"""
        # Check for recent performance data
        if hasattr(player, "_recent_performance") and player._recent_performance:
            if isinstance(player._recent_performance, (int, float)):
                return self._apply_bounds(float(player._recent_performance), "recent_form")
            elif isinstance(player._recent_performance, dict):
                form_score = player._recent_performance.get("form_score")
                if form_score:
                    return self._apply_bounds(float(form_score), "recent_form")

        # Check for L5 average
        if hasattr(player, "dff_l5_avg") and player.dff_l5_avg and player.base_projection > 0:
            ratio = player.dff_l5_avg / player.base_projection
            # Convert ratio to multiplier (0.5 to 1.5 range)
            multiplier = 0.5 + (min(max(ratio, 0), 2.0) * 0.5)
            return self._apply_bounds(multiplier, "recent_form")

        return None  # No data available

    def _get_vegas_multiplier(self, player: Any) -> Optional[float]:
        """Get Vegas multiplier - pure data only"""
        vegas_data = getattr(player, "_vegas_data", None)
        if not vegas_data:
            return None

        implied_total = vegas_data.get("implied_total", 0)

        # Validate
        if implied_total < self.config.validation["min_implied_total"]:
            return None
        if implied_total > self.config.validation["max_implied_total"]:
            return None

        # Calculate multiplier based on position
        if player.primary_position == "P":
            # Pitchers: opponent's implied total
            opp_total = vegas_data.get("opponent_total", 0)
            if opp_total <= 0:
                return None

            # Lower opponent total = better for pitcher
            if opp_total < 3.5:
                mult = 1.25
            elif opp_total < 4.0:
                mult = 1.15
            elif opp_total < 4.5:
                mult = 1.05
            elif opp_total < 5.0:
                mult = 0.95
            else:
                mult = 0.85
        else:
            # Hitters: team's implied total
            if implied_total > 5.5:
                mult = 1.25
            elif implied_total > 5.0:
                mult = 1.15
            elif implied_total > 4.5:
                mult = 1.05
            elif implied_total > 4.0:
                mult = 0.95
            else:
                mult = 0.85

        return self._apply_bounds(mult, "vegas")

    def _get_matchup_multiplier(self, player: Any) -> Optional[float]:
        """Get matchup multiplier from Statcast data"""
        statcast = getattr(player, "_statcast_data", None)
        if not statcast:
            return None

        if player.primary_position == "P":
            # Pitcher matchup based on K rate
            k_rate = statcast.get("k_rate", 0)
            if k_rate <= 0:
                return None

            if k_rate > 28:
                mult = 1.20
            elif k_rate > 25:
                mult = 1.10
            elif k_rate > 22:
                mult = 1.00
            else:
                mult = 0.90
        else:
            # Hitter matchup based on barrel rate
            barrel_rate = statcast.get("barrel_rate", 0)
            if barrel_rate <= 0:
                return None

            if barrel_rate > 12:
                mult = 1.20
            elif barrel_rate > 10:
                mult = 1.10
            elif barrel_rate > 8:
                mult = 1.00
            else:
                mult = 0.90

        return self._apply_bounds(mult, "matchup")

    def _get_batting_order_multiplier(self, player: Any) -> Optional[float]:
        """Get batting order multiplier"""
        order = getattr(player, "batting_order", None)
        if not order or order <= 0 or order > 9:
            return None

        # Top of order gets boost
        if order <= 2:
            mult = 1.12
        elif order <= 4:
            mult = 1.08
        elif order <= 6:
            mult = 1.00
        else:
            mult = 0.95

        return self._apply_bounds(mult, "batting_order")

    def _apply_bounds(self, value: float, component: str) -> float:
        """Apply component-specific bounds"""
        if component in self.config.bounds:
            min_val, max_val = self.config.bounds[component]
            return max(min_val, min(value, max_val))
        return value

    def _store_audit(self, player: Any, base: float, components: Dict, final: float):
        """Store scoring audit trail"""
        audit = {
            "timestamp": datetime.now().isoformat(),
            "base_score": base,
            "final_score": final,
            "components": components,
            "weights": self.config.weights,
            "data_completeness": len(components) / len(self.config.weights)
        }

        player._score_audit = audit
        player._has_all_data = len(components) >= 4  # At least 4 of 5 components

    def get_missing_data_report(self) -> Dict[str, List[str]]:
        """Get report of players with missing data"""
        return {
            "players_with_no_projection": list(self._missing_data_players),
            "total_affected": len(self._missing_data_players)
        }

    def clear_cache(self):
        """Clear score cache"""
        self._cache.clear()
        self._missing_data_players.clear()


# Global instance
_pure_engine = None


def get_pure_scoring_engine(config: Optional[PureDataScoringConfig] = None) -> PureDataScoringEngine:
    """Get or create the pure scoring engine"""
    global _pure_engine
    if _pure_engine is None:
        _pure_engine = PureDataScoringEngine(config)
    return _pure_engine