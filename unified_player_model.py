#!/usr/bin/env python3
"""
UNIFIED PLAYER MODEL - ENHANCED VERSION
======================================
Integrates all real data sources with NO fake fallbacks
Clean scoring based on performance metrics only
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class UnifiedPlayer:
    """
    Enhanced player model with real data integration
    NO fake data - only real sources
    """
    # Core attributes
    id: str
    name: str
    team: str
    salary: int

    # Positions
    primary_position: str
    positions: List[str] = field(default_factory=list)
    assigned_position: Optional[str] = None

    # Base projections
    base_projection: float = 0.0
    dff_projection: float = 0.0  # DFF expert projection if available

    # Calculated scores
    enhanced_score: float = 0.0
    _score_components: Dict[str, float] = field(default_factory=dict)

    # Real data sources (only populated if data exists)
    _dff_data: Optional[Dict] = field(default=None, repr=False)
    _statcast_data: Optional[Dict] = field(default=None, repr=False)
    _vegas_data: Optional[Dict] = field(default=None, repr=False)
    _recent_performance: Optional[Dict] = field(default=None, repr=False)
    _park_factors: Optional[Dict] = field(default=None, repr=False)

    # DFF specific data
    dff_rank: Optional[int] = None
    dff_l5_avg: Optional[float] = None
    dff_confirmed_order: Optional[str] = None

    # Recent form data
    recent_scores: List[float] = field(default_factory=list)
    games_played_l7: int = 0

    # Vegas data
    implied_team_score: Optional[float] = None
    over_under: Optional[float] = None
    moneyline: Optional[int] = None

    # Batting order
    batting_order: Optional[int] = None

    # Confirmations (for pool selection, NOT scoring)
    is_confirmed: bool = False
    confirmation_sources: List[str] = field(default_factory=list)
    is_manual_selected: bool = False

    # Game info
    game_info: Optional[str] = None
    game_time: Optional[str] = None

    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    data_quality_score: float = 0.0

    def __post_init__(self):
        """Calculate initial scores and validate data"""
        self._validate_data()
        self._calculate_data_quality()

    def _validate_data(self):
        """Validate and clean data"""
        # Ensure positions list includes primary position
        if self.primary_position and self.primary_position not in self.positions:
            self.positions.insert(0, self.primary_position)

        # Validate salary
        if self.salary < 0:
            self.salary = 0

        # Validate projections
        if self.base_projection < 0:
            self.base_projection = 0
        if self.dff_projection < 0:
            self.dff_projection = 0

    def _calculate_data_quality(self):
        """Calculate data quality score (0-1) based on available real data"""
        quality_points = 0
        max_points = 0

        # Check each data source
        data_checks = [
            (self.base_projection > 0, 2),  # Base projection
            (self._vegas_data is not None, 3),  # Vegas is important
            (self._recent_performance is not None, 3),  # Recent form crucial
            (self._statcast_data is not None, 2),  # Statcast valuable
            (self.batting_order is not None, 1),  # Batting order helpful
            (self._park_factors is not None, 1),  # Park factors
            (len(self.recent_scores) >= 3, 2),  # Recent game scores
            (self.dff_l5_avg is not None, 2),  # DFF recent average
        ]

        for has_data, points in data_checks:
            max_points += points
            if has_data:
                quality_points += points

        self.data_quality_score = quality_points / max_points if max_points > 0 else 0

    def calculate_enhanced_score(self):
        """
        Calculate enhanced score using ONLY real data
        NO fake fallbacks - if data doesn't exist, component is skipped
        """
        # Reset score components
        self._score_components = {}

        # Start with best available projection
        if self.dff_projection > 0:
            base_score = self.dff_projection
            self._score_components['base'] = 'dff_projection'
        elif self.base_projection > 0:
            base_score = self.base_projection
            self._score_components['base'] = 'base_projection'
        else:
            # No projection available
            self.enhanced_score = 0
            return

        # Calculate multipliers from real data only
        multipliers = []

        # 1. Recent Performance (40% weight if available)
        recent_mult = self._calculate_recent_performance()
        if recent_mult is not None:
            multipliers.append(('recent_form', recent_mult, 0.40))
            self._score_components['recent_mult'] = recent_mult

        # 2. Vegas Environment (30% weight if available)
        vegas_mult = self._calculate_vegas_environment()
        if vegas_mult is not None:
            multipliers.append(('vegas', vegas_mult, 0.30))
            self._score_components['vegas_mult'] = vegas_mult

        # 3. Matchup Quality (20% weight if available)
        matchup_mult = self._calculate_matchup_quality()
        if matchup_mult is not None:
            multipliers.append(('matchup', matchup_mult, 0.20))
            self._score_components['matchup_mult'] = matchup_mult

        # 4. Park Factors (10% weight if available)
        park_mult = self._calculate_park_adjustment()
        if park_mult is not None:
            multipliers.append(('park', park_mult, 0.10))
            self._score_components['park_mult'] = park_mult

        # Apply weighted multipliers
        if multipliers:
            # Normalize weights to sum to 1.0
            total_weight = sum(weight for _, _, weight in multipliers)

            final_multiplier = 0
            for name, mult, weight in multipliers:
                normalized_weight = weight / total_weight
                final_multiplier += mult * normalized_weight

            self.enhanced_score = base_score * final_multiplier
            self._score_components['final_multiplier'] = final_multiplier
        else:
            # No multipliers available - use base score
            self.enhanced_score = base_score
            self._score_components['final_multiplier'] = 1.0

        # Apply reasonable bounds
        self.enhanced_score = max(base_score * 0.5, min(self.enhanced_score, base_score * 2.0))

    def _calculate_recent_performance(self) -> Optional[float]:
        """
        Calculate recent form multiplier from REAL data only
        Returns None if no real data available
        """
        # Priority 1: Recent performance from form analyzer
        if self._recent_performance and 'form_score' in self._recent_performance:
            return self._recent_performance['form_score']

        # Priority 2: DFF L5 average
        if self.dff_l5_avg and self.dff_l5_avg > 0 and self.base_projection > 0:
            ratio = self.dff_l5_avg / self.base_projection

            # Convert to multiplier
            if ratio > 1.30:
                return 1.30
            elif ratio > 1.20:
                return 1.25
            elif ratio > 1.10:
                return 1.15
            elif ratio > 1.00:
                return 1.05
            elif ratio > 0.90:
                return 1.00
            elif ratio > 0.80:
                return 0.90
            elif ratio > 0.70:
                return 0.80
            else:
                return 0.70

        # Priority 3: Recent game scores
        if self.recent_scores and len(self.recent_scores) >= 3:
            # Weighted average (more recent = more weight)
            weights = [0.40, 0.30, 0.20, 0.10]  # Most recent first

            weighted_sum = 0
            weight_total = 0

            for i, score in enumerate(self.recent_scores[:4]):
                if i < len(weights):
                    weighted_sum += score * weights[i]
                    weight_total += weights[i]

            if weight_total > 0 and self.base_projection > 0:
                recent_avg = weighted_sum / weight_total
                ratio = recent_avg / self.base_projection

                # Same conversion as above
                if ratio > 1.30:
                    return 1.30
                elif ratio > 1.20:
                    return 1.25
                elif ratio > 1.10:
                    return 1.15
                elif ratio > 1.00:
                    return 1.05
                elif ratio > 0.90:
                    return 1.00
                elif ratio > 0.80:
                    return 0.90
                else:
                    return 0.70

        # No recent performance data available
        return None

    def _calculate_vegas_environment(self) -> Optional[float]:
        """
        Calculate Vegas-based multiplier from REAL data only
        Returns None if no real data available
        """
        # Check if we have Vegas data
        if not self._vegas_data and not self.implied_team_score:
            return None

        # Get implied team total
        implied_total = None
        if self._vegas_data and 'implied_total' in self._vegas_data:
            implied_total = self._vegas_data['implied_total']
        elif self.implied_team_score:
            implied_total = self.implied_team_score

        if implied_total is None or implied_total <= 0:
            return None

        # Calculate multiplier based on position
        if self.primary_position == 'P':
            # For pitchers: opponent's implied total matters
            opp_total = None

            if self._vegas_data and 'opponent_total' in self._vegas_data:
                opp_total = self._vegas_data['opponent_total']
            elif self.over_under and self.implied_team_score:
                opp_total = self.over_under - self.implied_team_score

            if opp_total is None:
                return None

            # Lower opponent total = better for pitcher
            if opp_total < 3.0:
                return 1.30
            elif opp_total < 3.5:
                return 1.20
            elif opp_total < 4.0:
                return 1.10
            elif opp_total < 4.5:
                return 1.00
            elif opp_total < 5.0:
                return 0.90
            elif opp_total < 5.5:
                return 0.80
            else:
                return 0.70
        else:
            # For hitters: team's implied total drives scoring
            mult = 1.0

            if implied_total > 5.5:
                mult = 1.30
            elif implied_total > 5.0:
                mult = 1.20
            elif implied_total > 4.5:
                mult = 1.10
            elif implied_total > 4.0:
                mult = 1.00
            elif implied_total > 3.5:
                mult = 0.90
            else:
                mult = 0.80

            # Adjust for total runs if available
            if self.over_under and self.over_under > 0:
                if self.over_under > 11:
                    mult *= 1.05
                elif self.over_under > 10:
                    mult *= 1.02
                elif self.over_under < 7.5:
                    mult *= 0.98
                elif self.over_under < 7:
                    mult *= 0.95

            return mult

    def _calculate_matchup_quality(self) -> Optional[float]:
        """
        Calculate matchup quality from REAL data only
        Returns None if no real data available
        """
        if not self._statcast_data:
            return None

        mult = 1.0
        adjustments = 0

        if self.primary_position == 'P':
            # Pitcher metrics
            if 'k_rate' in self._statcast_data:
                k_rate = self._statcast_data['k_rate']
                if k_rate > 28:
                    mult *= 1.10
                    adjustments += 1
                elif k_rate > 25:
                    mult *= 1.05
                    adjustments += 1
                elif k_rate < 19:
                    mult *= 0.95
                    adjustments += 1
                elif k_rate < 16:
                    mult *= 0.90
                    adjustments += 1

            if 'whip' in self._statcast_data:
                whip = self._statcast_data['whip']
                if whip < 1.00:
                    mult *= 1.08
                    adjustments += 1
                elif whip < 1.15:
                    mult *= 1.04
                    adjustments += 1
                elif whip > 1.40:
                    mult *= 0.96
                    adjustments += 1
                elif whip > 1.50:
                    mult *= 0.92
                    adjustments += 1
        else:
            # Hitter metrics
            if 'barrel_rate' in self._statcast_data:
                barrel = self._statcast_data['barrel_rate']
                if barrel > 12:
                    mult *= 1.10
                    adjustments += 1
                elif barrel > 10:
                    mult *= 1.05
                    adjustments += 1
                elif barrel < 6:
                    mult *= 0.95
                    adjustments += 1
                elif barrel < 4:
                    mult *= 0.90
                    adjustments += 1

            if 'hard_hit_rate' in self._statcast_data:
                hard_hit = self._statcast_data['hard_hit_rate']
                if hard_hit > 45:
                    mult *= 1.05
                    adjustments += 1
                elif hard_hit > 42:
                    mult *= 1.02
                    adjustments += 1
                elif hard_hit < 35:
                    mult *= 0.98
                    adjustments += 1
                elif hard_hit < 30:
                    mult *= 0.95
                    adjustments += 1

            # Batting order bonus
            if self.batting_order:
                if self.batting_order <= 3:
                    mult *= 1.08
                    adjustments += 1
                elif self.batting_order <= 5:
                    mult *= 1.04
                    adjustments += 1
                elif self.batting_order >= 8:
                    mult *= 0.96
                    adjustments += 1

        # Only return if we made adjustments based on real data
        return mult if adjustments > 0 else None

    def _calculate_park_adjustment(self) -> Optional[float]:
        """
        Calculate park factor adjustment from REAL data only
        Returns None if no real data available
        """
        if not self._park_factors or not self.team:
            return None

        park_data = self._park_factors.get(self.team)
        if not park_data:
            return None

        # Get the appropriate factor
        if isinstance(park_data, dict):
            if self.primary_position == 'P':
                factor = park_data.get('pitcher_factor', park_data.get('overall', 1.0))
            else:
                factor = park_data.get('hitter_factor', park_data.get('overall', 1.0))
        else:
            # Simple numeric factor
            factor = float(park_data)
            if self.primary_position == 'P':
                # Invert for pitchers
                factor = 2.0 - factor

        # Ensure reasonable bounds
        return max(0.85, min(factor, 1.15))

    # Data application methods
    def apply_dff_data(self, dff_data: Dict):
        """Apply DFF ranking data"""
        self._dff_data = dff_data

        # Extract specific fields
        if 'rank' in dff_data:
            self.dff_rank = dff_data['rank']
        if 'l5_avg' in dff_data:
            self.dff_l5_avg = dff_data['l5_avg']
        if 'projection' in dff_data and dff_data['projection'] > 0:
            self.dff_projection = dff_data['projection']
        if 'confirmed_order' in dff_data:
            self.dff_confirmed_order = dff_data['confirmed_order']
            if str(dff_data['confirmed_order']).upper() == 'YES':
                self.is_confirmed = True
                self.confirmation_sources.append('dff')

        # Recalculate score
        self.calculate_enhanced_score()

    def apply_vegas_data(self, vegas_data: Dict):
        """Apply Vegas betting data"""
        self._vegas_data = vegas_data

        # Extract key fields
        if 'implied_total' in vegas_data:
            self.implied_team_score = vegas_data['implied_total']
        if 'game_total' in vegas_data:
            self.over_under = vegas_data['game_total']
        if 'moneyline' in vegas_data:
            self.moneyline = vegas_data['moneyline']

        # Recalculate score
        self.calculate_enhanced_score()

    def apply_statcast_data(self, statcast_data: Dict):
        """Apply Statcast/advanced metrics"""
        self._statcast_data = statcast_data

        # Recalculate score
        self.calculate_enhanced_score()

    def apply_recent_form(self, form_data: Dict):
        """Apply recent form analysis"""
        self._recent_performance = form_data

        # Extract game scores if available
        if 'recent_games' in form_data:
            self.recent_scores = [g.get('fantasy_points', 0)
                                  for g in form_data['recent_games'][-5:]]

        # Recalculate score
        self.calculate_enhanced_score()

    def apply_park_factors(self, park_data: Dict):
        """Apply park factor data"""
        self._park_factors = park_data

        # Recalculate score
        self.calculate_enhanced_score()

    def set_batting_order(self, order: int):
        """Set batting order position"""
        self.batting_order = order

        # Recalculate score
        self.calculate_enhanced_score()

    def add_confirmation_source(self, source: str):
        """Add confirmation source (for pool selection only)"""
        if source not in self.confirmation_sources:
            self.confirmation_sources.append(source)
        self.is_confirmed = True

    def copy(self):
        """Create a deep copy of this player"""
        import copy
        return copy.deepcopy(self)

    # Utility properties
    @property
    def value_score(self) -> float:
        """Points per $1000 salary"""
        return (self.enhanced_score / (self.salary / 1000)) if self.salary > 0 else 0

    @property
    def has_quality_data(self) -> bool:
        """Check if player has sufficient quality data"""
        return self.data_quality_score >= 0.5

    @property
    def score_breakdown(self) -> str:
        """Get a breakdown of score components"""
        if not self._score_components:
            return "No score calculated"

        parts = [f"Base ({self._score_components.get('base', 'none')}): {self.base_projection:.1f}"]

        if 'recent_mult' in self._score_components:
            parts.append(f"Recent: {self._score_components['recent_mult']:.2f}x")
        if 'vegas_mult' in self._score_components:
            parts.append(f"Vegas: {self._score_components['vegas_mult']:.2f}x")
        if 'matchup_mult' in self._score_components:
            parts.append(f"Matchup: {self._score_components['matchup_mult']:.2f}x")
        if 'park_mult' in self._score_components:
            parts.append(f"Park: {self._score_components['park_mult']:.2f}x")

        parts.append(f"Final: {self.enhanced_score:.1f}")

        return " | ".join(parts)

    def __hash__(self):
        """Make player hashable for use in sets"""
        return hash(self.id)

    def __eq__(self, other):
        """Check equality based on player ID"""
        if isinstance(other, UnifiedPlayer):
            return self.id == other.id
        return False

    def __repr__(self):
        return (f"UnifiedPlayer({self.name}, {self.primary_position}, "
                f"${self.salary}, score={self.enhanced_score:.1f}, "
                f"quality={self.data_quality_score:.2f})")


# Example test
if __name__ == "__main__":
    # Create test player
    player = UnifiedPlayer(
        id="test1",
        name="Mike Trout",
        team="LAA",
        salary=5500,
        primary_position="OF",
        positions=["OF"],
        base_projection=12.5
    )

    # Apply some real data
    player.apply_vegas_data({
        'implied_total': 5.2,
        'game_total': 9.5,
        'opponent_total': 4.3
    })

    player.apply_statcast_data({
        'barrel_rate': 14.5,
        'hard_hit_rate': 48.2,
        'xba': .295
    })

    player.dff_l5_avg = 14.8
    player.batting_order = 3

    # Calculate score
    player.calculate_enhanced_score()

    print(player)
    print(f"Score breakdown: {player.score_breakdown}")
    print(f"Value: {player.value_score:.2f} pts/$1k")