#!/usr/bin/env python3
"""
UNIFIED SCORING ENGINE - Single Source of Truth for All Score Calculations
=========================================================================
Replaces the scattered scoring logic across multiple files with one
consistent, validated, and efficient implementation.
"""

from unified_config_manager import get_config_manager
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
from logging_config import get_logger
logger = get_logger(__name__)


@dataclass
class ScoringConfig:
    """Configuration for scoring system with validation"""

    # Weight configuration - ALWAYS sums to 1.0
    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "base": 0.30,  # Reduced for DFS optimization
            "recent_form": 0.25,  # Increased - hot/cold streaks matter
            "vegas": 0.20,  # Vegas lines are sharp
            "matchup": 0.20,  # Matchup quality is crucial
            "park": 0.05,  # Park factors (minor)
            "batting_order": 0.05,  # Batting order (minor)
        }
    )

    # Multiplier bounds for each component
    bounds: Dict[str, Tuple[float, float]] = field(
        default_factory=lambda: {
            "recent_form": (0.70, 1.35),  # Increased upside
            "vegas": (0.75, 1.25),  # ±25% max
            "matchup": (0.80, 1.25),  # Good matchups matter
            "park": (0.85, 1.15),  # ±15% max
            "batting_order": (0.92, 1.10),  # Increased for top of order
            "final": (0.65, 1.40),  # Overall bounds
        }
    )

    # Validation rules
    validation: Dict[str, Any] = field(
        default_factory=lambda: {
            "max_implied_total": 15.0,
            "min_implied_total": 2.0,
            "max_projection": 60.0,
            "min_projection": 0.0,
            "max_salary": 15000,
            "min_salary": 2000,
            "max_barrel_rate": 100.0,
            "max_k_rate": 100.0,
        }
    )

    def __post_init__(self):
        """Validate configuration on initialization"""
        # Ensure weights sum to 1.0
        weight_sum = sum(self.weights.values())
        if abs(weight_sum - 1.0) > 0.001:
            # Normalize weights
            self.weights = {k: v / weight_sum for k, v in self.weights.items()}
            logger.warning(f"Normalized weights to sum to 1.0 (was {weight_sum})")

        # Ensure all bounds are valid
        for component, (min_bound, max_bound) in self.bounds.items():
            if min_bound >= max_bound:
                raise ValueError(f"Invalid bounds for {component}: {min_bound} >= {max_bound}")


@dataclass
class ScoreComponent:
    """Represents a single scoring component with validation"""

    name: str
    multiplier: float
    weight: float
    data_source: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate component data"""
        if self.weight < 0 or self.weight > 1:
            raise ValueError(f"Invalid weight {self.weight} for {self.name}")
        if self.multiplier < 0:
            raise ValueError(f"Invalid multiplier {self.multiplier} for {self.name}")


class UnifiedScoringEngine:
    """
    Centralized scoring engine that handles all player score calculations
    with proper validation, caching, and audit trails.
    """

    def __init__(self, config: Optional[ScoringConfig] = None):
        """Initialize with configuration"""
        self.config = config or ScoringConfig()
        # Load park factors
        from park_factors import PARK_FACTORS
        self.park_factors = {team: data['factor'] for team, data in PARK_FACTORS.items()}
        self._cache = {}
        self._calculation_count = 0


        logger.info("Unified Scoring Engine initialized")
        logger.debug(f"Weights: {self.config.weights}")
        logger.debug(f"Bounds: {self.config.bounds}")

    def calculate_score(self, player: Any) -> float:
        """
        Main entry point for calculating a player's enhanced score.
        This is the ONLY method that should be called for scoring.
        """
        # Generate cache key
        cache_key = self._generate_cache_key(player)

        # Check cache first
        if cache_key in self._cache:
            cached_score, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < 300:  # 5 min cache
                logger.debug(f"Cache hit for {player.name}")
                return cached_score

        # Calculate fresh score
        self._calculation_count += 1
        logger.debug(
            f"Calculating score for {player.name} (calculation #{self._calculation_count})"
        )

        # Get base score
        base_score = self._get_base_score(player)
        if base_score <= 0:
            logger.warning(f"No valid base score for {player.name}")
            return 0.0

        # Collect score components
        components = self._collect_components(player, base_score)

        # Calculate final score
        final_score = self._calculate_weighted_score(base_score, components)

        # Store audit trail
        self._store_audit_trail(player, base_score, components, final_score)

        # Cache result
        self._cache[cache_key] = (final_score, datetime.now())

        # Update player object
        player.enhanced_score = final_score

        # Set calculation flag
        if hasattr(player, "_score_calculated"):
            player._score_calculated = True

        return final_score

    def _get_base_score(self, player: Any) -> float:
        """Get the base projection score with validation"""
        # Priority order for base score
        base_score = 0.0
        base_source = None

        # Try DFF projection first
        if hasattr(player, "dff_projection") and player.dff_projection > 0:
            base_score = float(player.dff_projection)
            base_source = "dff_projection"
        # Then base projection
        elif hasattr(player, "base_projection") and player.base_projection > 0:
            base_score = float(player.base_projection)
            base_source = "base_projection"
        # Finally original projection
        elif hasattr(player, "projection") and player.projection > 0:
            base_score = float(player.projection)
            base_source = "projection"

        # Validate base score
        if base_score > self.config.validation["max_projection"]:
            logger.warning(
                f"Base score {base_score} exceeds max, capping at {self.config.validation['max_projection']}"
            )
            base_score = self.config.validation["max_projection"]

        if base_score > 0:
            logger.debug(f"Base score for {player.name}: {base_score} from {base_source}")

        return base_score

    def _collect_components(self, player: Any, base_score: float) -> List[ScoreComponent]:
        """Collect all available scoring components"""
        components = []

        # 1. Recent Form Component
        recent_mult = self._calculate_recent_form(player, base_score)
        if recent_mult is not None:
            components.append(
                ScoreComponent(
                    name="recent_form",
                    multiplier=recent_mult,
                    weight=self.config.weights["recent_form"],
                    data_source={"type": "recent_performance"},
                )
            )

        # 2. Vegas Component
        vegas_mult = self._calculate_vegas_multiplier(player)
        if vegas_mult is not None:
            components.append(
                ScoreComponent(
                    name="vegas",
                    multiplier=vegas_mult,
                    weight=self.config.weights["vegas"],
                    data_source={"type": "vegas_lines"},
                )
            )

        # 3. Matchup Component
        matchup_mult = self._calculate_matchup_multiplier(player)
        if matchup_mult is not None:
            components.append(
                ScoreComponent(
                    name="matchup",
                    multiplier=matchup_mult,
                    weight=self.config.weights["matchup"],
                    data_source={"type": "statcast"},
                )
            )

        # 4. Park Factor Component
        park_mult = self._calculate_park_environment(player)
        if park_mult is not None:
            components.append(
                ScoreComponent(
                    name="park",
                    multiplier=park_mult,
                    weight=self.config.weights["park"],
                    data_source={"type": "park_factors"},
                )
            )

        # 5. Batting Order Component (hitters only)
        if player.primary_position != "P":
            order_mult = self._calculate_batting_order_multiplier(player)
            if order_mult is not None:
                components.append(
                    ScoreComponent(
                        name="batting_order",
                        multiplier=order_mult,
                        weight=self.config.weights["batting_order"],
                        data_source={"type": "lineup"},
                    )
                )

        return components



        # Collect score components
        components = self._collect_components(player, base_score)

        # Calculate final score with FIXED weight calculation
        final_score = self._calculate_weighted_score(base_score, components)

        # Validate final score
        if final_score < 0:
            logger.error(f"Negative final score {final_score} for {player.name}, setting to 0")
            final_score = 0.0
        elif final_score > self.config.validation["max_projection"]:
            logger.warning(f"Score {final_score} exceeds max for {player.name}, capping")
            final_score = self.config.validation["max_projection"]

        # Store audit trail
        self._store_audit_trail(player, base_score, components, final_score)

        # Cache result
        self._cache[cache_key] = (final_score, datetime.now())

        # Update player object
        player.enhanced_score = final_score

        # Set calculation flag
        if hasattr(player, "_score_calculated"):
            player._score_calculated = True

        # Log high-level players for debugging
        if final_score > base_score * 1.15:
            boost_pct = ((final_score / base_score) - 1) * 100
            logger.info(f"SCORE BOOST: {player.name} - Base: {base_score:.1f} → Enhanced: {final_score:.1f} (+{boost_pct:.0f}%)")

            # Log why the boost happened
            if hasattr(player, '_score_audit'):
                audit = player._score_audit
                for comp_name, comp_data in audit['components'].items():
                    if comp_data['multiplier'] > 1.05:
                        logger.info(f"  BOOST REASON: {comp_name} = {comp_data['multiplier']:.2f}x")
            logger.info(f"High score for {player.name}: {base_score:.1f} → {final_score:.1f}")

        return final_score

    def _calculate_weighted_score(
        self, base_score: float, components: List[ScoreComponent]
    ) -> float:
        """
        FIXED: Calculate final weighted score with proper weight application

        The key fix: We calculate each component's FULL contribution, not just the delta
        """
        if not components:
            # No adjustments available, return base score
            return base_score

        # Get weights that need to be redistributed
        available_weights = {comp.name: comp.weight for comp in components}
        available_weights["base"] = self.config.weights["base"]

        # Normalize weights to sum to 1.0
        normalized_weights = self._normalize_weights(available_weights)

        # Start with zero and build up the score
        final_score = 0.0

        # Add base component contribution
        base_contribution = base_score * normalized_weights["base"]
        final_score += base_contribution

        logger.debug(
            f"  Base: {base_score:.2f} × {normalized_weights['base']:.3f} = {base_contribution:.2f}"
        )

        # Add each component's FULL contribution
        for component in components:
            normalized_weight = normalized_weights[component.name]

            # Calculate the component's adjusted score
            component_score = base_score * component.multiplier

            # Calculate its weighted contribution
            component_contribution = component_score * normalized_weight

            # Add to final score
            final_score += component_contribution

            logger.debug(
                f"  {component.name}: {base_score:.2f} × {component.multiplier:.3f} × {normalized_weight:.3f} = {component_contribution:.2f}"
            )

        # Apply final bounds
        min_allowed = base_score * self.config.bounds["final"][0]
        max_allowed = base_score * self.config.bounds["final"][1]

        # Store pre-bounded score for debugging
        unbounded_score = final_score

        # Apply bounds
        final_score = max(min_allowed, min(final_score, max_allowed))

        if unbounded_score != final_score:
            logger.debug(
                f"  Final: {unbounded_score:.2f} bounded to [{min_allowed:.2f}, {max_allowed:.2f}] = {final_score:.2f}"
            )
        else:
            logger.debug(f"  Final: {final_score:.2f} (within bounds)")

        # Log detailed scoring for high-value players
        if final_score > 20:
            logger.info(f"SCORE DETAILS:  scored {final_score:.1f} with components: {[f"{c.name}:{c.multiplier:.2f}" for c in components]}")

        return final_score

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Ensure weights sum to exactly 1.0"""
        total = sum(weights.values())
        if total == 0:
            return {"base": 1.0}

        return {k: v / total for k, v in weights.items()}

    def _calculate_recent_form(self, player: Any, base_score: float) -> Optional[float]:
        try:
            if hasattr(player, "_recent_performance") and player._recent_performance is not None:
                if isinstance(player._recent_performance, (int, float)):
                    return self._apply_bounds(float(player._recent_performance), "recent_form")

                elif isinstance(player._recent_performance, dict):
                    form_score = player._recent_performance.get("form_score", 1.0)
                    return self._apply_bounds(float(form_score), "recent_form")

            if hasattr(player, "dff_l5_avg") and player.dff_l5_avg and base_score > 0:
                ratio = float(player.dff_l5_avg) / float(base_score)
                multiplier = 0.7 + (min(max(ratio, 0), 2.0) * 0.3)
                return self._apply_bounds(multiplier, "recent_form")

            if hasattr(player, "recent_scores") and player.recent_scores and len(player.recent_scores) >= 3:
                avg_recent = sum(player.recent_scores[-5:]) / len(player.recent_scores[-5:])
                if base_score > 0:
                    ratio = avg_recent / base_score
                    multiplier = 0.7 + (min(max(ratio, 0), 2.0) * 0.3)
                    return self._apply_bounds(multiplier, "recent_form")

            return None

        except Exception as e:
            logger.debug(f"Error in recent form calculation: {e}")
            return None


    def validate_scoring_logic(self):
        """
        NEW: Self-test to validate scoring calculations are correct
        """
        print("\n🧪 Validating scoring logic...")

        # Create test player
        from unified_player_model import UnifiedPlayer

        test_player = UnifiedPlayer(
            id="test",
            name="Test Player",
            team="TEST",
            salary=5000,
            primary_position="OF",
            positions=["OF"],
            base_projection=10.0,
        )

        # Test 1: Base score only
        score1 = self.calculate_score(test_player)
        expected1 = 10.0  # Just base score
        print(
            f"Test 1 - Base only: {score1:.2f} (expected: {expected1:.2f}) {'✅' if abs(score1 - expected1) < 0.01 else '❌'}"
        )

        # Test 2: With Vegas boost
        test_player._vegas_data = {"implied_total": 6.0}  # Should give 1.20x
        self.clear_cache()  # Force recalculation
        score2 = self.calculate_score(test_player)
        # With weights: base(0.30) + vegas(0.20) normalized
        # base: 10 * (0.30/0.50) = 6.0
        # vegas: 10 * 1.20 * (0.20/0.50) = 4.8
        # total: 10.8
        expected2 = 10.8
        print(
            f"Test 2 - With Vegas: {score2:.2f} (expected: ~{expected2:.2f}) {'✅' if abs(score2 - expected2) < 0.5 else '❌'}"
        )

        # Test 3: Show audit trail
        if hasattr(test_player, "_score_audit"):
            audit = test_player._score_audit
            print("\nAudit trail for Test 2:")
            for comp_name, comp_data in audit["components"].items():
                print(
                    f"  {comp_name}: {comp_data['contribution']:.2f} "
                    f"({comp_data['multiplier']:.2f}x @ {comp_data['weight']:.1%})"
                )

        print("\n✅ Scoring validation complete")

    def recalculate_all_scores(self, players: List[Any], force: bool = False) -> int:
        """
        NEW: Batch recalculation with progress tracking
        """
        if force:
            self.clear_cache()

        recalculated = 0

        for i, player in enumerate(players):
            if i % 50 == 0 and i > 0:
                logger.info(f"Recalculating scores: {i}/{len(players)}")

            old_score = getattr(player, "enhanced_score", 0)
            new_score = self.calculate_score(player)

            if abs(old_score - new_score) > 0.01:
                recalculated += 1

        logger.info(f"Recalculated {recalculated} player scores")
        return recalculated

    def get_component_breakdown(self, player: Any) -> Dict[str, float]:
        """
        NEW: Get detailed breakdown of score components for display
        """
        if not hasattr(player, "_score_audit"):
            return {}

        audit = player._score_audit
        breakdown = {}

        for comp_name, comp_data in audit["components"].items():
            breakdown[comp_name] = {
                "multiplier": comp_data["multiplier"],
                "weight": comp_data["weight"],
                "contribution": comp_data["contribution"],
                "percentage": (
                    (comp_data["contribution"] / audit["final_score"] * 100)
                    if audit["final_score"] > 0
                    else 0
                ),
            }

        return breakdown

    def _calculate_vegas_multiplier(self, player: Any) -> Optional[float]:
        """Calculate Vegas multiplier with validation"""
        # Check for Vegas data
        vegas_data = getattr(player, "_vegas_data", None)
        if not vegas_data:
            return None

        implied_total = vegas_data.get("implied_total", 0)

        # Validate implied total
        if implied_total < self.config.validation["min_implied_total"]:
            return None
        if implied_total > self.config.validation["max_implied_total"]:
            logger.warning(f"Invalid implied total {implied_total} for {player.name}")
            return None

        # Calculate multiplier based on position
        if player.primary_position == "P":
            # For pitchers: opponent's implied total matters
            opp_total = vegas_data.get("opponent_total", 4.5)
            if opp_total < 3.5:
                mult = 1.20
            elif opp_total < 4.0:
                mult = 1.15
            elif opp_total < 4.5:
                mult = 1.05
            elif opp_total < 5.0:
                mult = 0.95
            elif opp_total < 5.5:
                mult = 0.90
            else:
                mult = 0.85
        else:
            # For hitters: team's implied total
            if implied_total > 5.5:
                mult = 1.20
            elif implied_total > 5.0:
                mult = 1.15
            elif implied_total > 4.5:
                mult = 1.10
            elif implied_total > 4.0:
                mult = 1.00
            elif implied_total > 3.5:
                mult = 0.90
            else:
                mult = 0.85

        return self._apply_bounds(mult, "vegas")

    def _calculate_matchup_multiplier(self, player: Any) -> Optional[float]:
        """Calculate matchup quality multiplier"""
        statcast = getattr(player, "_statcast_data", None)
        if not statcast:
            return None

        mult = 1.0
        adjustments = 0

        if player.primary_position == "P":
            # Pitcher metrics
            k_rate = statcast.get("k_rate", 0)
            if 0 < k_rate <= self.config.validation["max_k_rate"]:
                if k_rate > 28:
                    mult *= 1.10
                    adjustments += 1
                elif k_rate > 25:
                    mult *= 1.05
                    adjustments += 1
                elif k_rate < 20:
                    mult *= 0.95
                    adjustments += 1

            # WHIP
            whip = statcast.get("whip", 0)
            if whip > 0:
                if whip < 1.00:
                    mult *= 1.05
                    adjustments += 1
                elif whip > 1.40:
                    mult *= 0.95
                    adjustments += 1
        else:
            # Hitter metrics
            barrel_rate = statcast.get("barrel_rate", 0)
            if 0 < barrel_rate <= self.config.validation["max_barrel_rate"]:
                if barrel_rate > 12:
                    mult *= 1.10
                    adjustments += 1
                elif barrel_rate > 10:
                    mult *= 1.05
                    adjustments += 1
                elif barrel_rate < 6:
                    mult *= 0.95
                    adjustments += 1

            # Opposing pitcher ERA
            opp_era = statcast.get("opposing_pitcher_era", 0)
            if opp_era > 0:
                if opp_era > 5.0:
                    mult *= 1.10
                    adjustments += 1
                elif opp_era < 3.0:
                    mult *= 0.90
                    adjustments += 1

        # Only return if we made adjustments based on real data
        return self._apply_bounds(mult, "matchup") if adjustments > 0 else None

    def _calculate_park_environment(self, player: Any) -> Optional[float]:
        """Calculate park factor multiplier - SINGLE APPLICATION POINT"""

        # Check if already applied
        if hasattr(player, '_park_factor_applied'):
            return None

        park_factor = self.park_factors.get(player.team, 1.0)

        # Mark as applied
        player._park_factor_applied = True

        # Return adjustment factor
        if player.primary_position == 'P':
            return 2.0 - park_factor  # Inverse for pitchers
        else:
            return park_factor

    def _calculate_batting_order_multiplier(self, player: Any) -> Optional[float]:
        """Calculate batting order multiplier"""
        batting_order = getattr(player, "batting_order", None)
        if not batting_order or batting_order <= 0 or batting_order > 9:
            return None

        # Position-based multipliers (optimized for DFS)
        if batting_order <= 2:
            mult = 1.10  # Top of order premium
        elif batting_order <= 4:
            mult = 1.06  # Heart of order
        elif batting_order <= 6:
            mult = 1.02  # Middle
        else:
            mult = 0.92  # Bottom penalty

        return self._apply_bounds(mult, "batting_order")

    def _apply_bounds(self, value: float, component: str) -> float:
        """Apply component-specific bounds"""
        if component in self.config.bounds:
            min_val, max_val = self.config.bounds[component]
            return max(min_val, min(value, max_val))
        return value

    def _store_audit_trail(
        self, player: Any, base_score: float, components: List[ScoreComponent], final_score: float
    ):
        """
        FIXED: Store detailed audit trail with correct contribution calculations
        """
        # Get normalized weights
        available_weights = {comp.name: comp.weight for comp in components}
        available_weights["base"] = self.config.weights["base"]
        normalized_weights = self._normalize_weights(available_weights)

        audit = {
            "base_score": base_score,
            "final_score": final_score,
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "weights_used": normalized_weights,
            "calculation_method": "weighted_sum_v2",  # Version identifier
        }

        # Calculate base contribution
        base_contribution = base_score * normalized_weights["base"]
        audit["components"]["base"] = {
            "score": base_score,
            "multiplier": 1.0,
            "weight": normalized_weights["base"],
            "contribution": base_contribution,
        }

        # Store each component with CORRECT contribution calculation
        for comp in components:
            normalized_weight = normalized_weights[comp.name]

            # Component's adjusted score
            component_score = base_score * comp.multiplier

            # Component's weighted contribution
            component_contribution = component_score * normalized_weight

            audit["components"][comp.name] = {
                "score": component_score,
                "multiplier": comp.multiplier,
                "weight": normalized_weight,
                "contribution": component_contribution,
                "data_source": comp.data_source,
            }

        # Add summary
        total_contribution = sum(c["contribution"] for c in audit["components"].values())
        audit["summary"] = {
            "total_contributions": total_contribution,
            "bounds_applied": total_contribution != final_score,
            "min_bound": base_score * self.config.bounds["final"][0],
            "max_bound": base_score * self.config.bounds["final"][1],
        }

        # Store in player
        player._score_audit = audit
        player._score_components = audit  # Backwards compatibility

    def _generate_cache_key(self, player: Any) -> tuple:
        """
        FIXED: Generate cache key for player using tuple (faster than string concatenation)

        Returns:
            Tuple that can be used as dict key (hashable and fast)
        """
        # Use tuple instead of string concatenation - MUCH faster!
        return (
            getattr(player, "id", player.name),
            getattr(player, "base_projection", 0),
            getattr(player, "dff_projection", 0),
            getattr(player, "batting_order", 0),
            len(getattr(player, "recent_scores", [])),
            # Add a hash of any complex data
            hash(str(getattr(player, "_vegas_data", {}))),
        )

    def clear_cache(self):
        """Clear the score cache"""
        self._cache.clear()
        logger.info("Score cache cleared")

    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            "calculations": self._calculation_count,
            "cache_size": len(self._cache),
            "cache_hit_rate": len(self._cache) / max(self._calculation_count, 1),
        }


# Convenience functions
def load_config_from_file(filepath: str) -> ScoringConfig:
    """Load configuration from unified config system"""
    try:
        # Use unified config manager
        config_manager = get_config_manager()

        # Get scoring configuration
        scoring_config = config_manager.export_for_module('scoring_engine')

        return ScoringConfig(
            weights=scoring_config.get('weights', {}),
            bounds=scoring_config.get('bounds', {}),
            validation=scoring_config.get('validation', {})
        )
    except Exception as e:
        logger.warning(f"Could not load config: {e}")
        return ScoringConfig()


# Global engine instance (singleton pattern)
_engine_instance = None


def get_scoring_engine(config: Optional[ScoringConfig] = None) -> UnifiedScoringEngine:
    """Get or create the global scoring engine instance"""
    global _engine_instance

    if _engine_instance is None:
        _engine_instance = UnifiedScoringEngine(config)
    elif config is not None:
        # Update config if provided
        _engine_instance.config = config
        _engine_instance.clear_cache()

    return _engine_instance
