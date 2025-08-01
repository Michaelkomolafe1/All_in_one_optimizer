#!/usr/bin/env python3
"""
UNIFIED PLAYER MODEL - FIXED VERSION
====================================
Fixed calculation methods to prevent multiplicative stacking
"""

from __future__ import annotations  # MUST BE FIRST IMPORT!

import copy
from typing import Dict, List, Optional


# For park factors if not available elsewhere
PARK_FACTORS = {
    # Extreme hitter-friendly
    "COL": 1.20,  # Coors Field
    # Hitter-friendly
    "CIN": 1.12,
    "TEX": 1.10,
    "PHI": 1.08,
    "MIL": 1.06,
    "BAL": 1.05,
    "HOU": 1.04,
    "TOR": 1.03,
    "BOS": 1.03,
    # Slight hitter-friendly
    "NYY": 1.02,
    "CHC": 1.01,
    # Neutral
    "ARI": 1.00,
    "ATL": 1.00,
    "MIN": 0.99,
    # Slight pitcher-friendly
    "WSH": 0.98,
    "NYM": 0.97,
    "LAA": 0.96,
    "STL": 0.95,
    # Pitcher-friendly
    "CLE": 0.94,
    "TB": 0.93,
    "KC": 0.92,
    "DET": 0.91,
    "SEA": 0.90,
    # Extreme pitcher-friendly
    "OAK": 0.89,
    "SF": 0.88,
    "SD": 0.87,
    "MIA": 0.86,
    "PIT": 0.85,
    # Additional teams
    "LAD": 0.98,
    "CHW": 0.96,
    "CWS": 0.96,
}


class UnifiedPlayer:
    """
    Unified player model with all DFS attributes
    FIXED: Proper weighted calculations, no multiplicative stacking
    """

    def __init__(
        self,
        id: str,
        name: str,
        team: str,
        salary: int,
        primary_position: str,
        positions: List[str],
        base_projection: float = 0.0,
    ):
        """Initialize player with basic attributes"""
        # Core attributes
        self.id = id
        self.name = name
        self.team = team
        self.salary = salary
        self.primary_position = primary_position
        self.positions = positions
        self.base_projection = base_projection

        # DFS platform projections
        self.dff_projection = 0.0
        self.dff_l5_avg = None
        self.dff_consistency = None

        # Real-time data
        self.is_confirmed = False
        self.confirmation_sources = []
        self.batting_order = None
        self.batting_order_multiplier = None  # Stored but not auto-applied

        # Vegas/environment
        self.implied_team_score = None
        self.over_under = None
        self.moneyline = None

        # Statistical scores
        self.enhanced_score = base_projection
        self.data_quality_score = 0.0
        self.recent_scores = []
        # In the __init__ method, add these lines:

        # Ownership projections (NEW)
        self.projected_ownership = 0.0
        self.ownership_leverage = 1.0
        self.ownership_tier = "medium"

        # Recent form data (NEW)
        self.recent_form_score = 0.0
        self.recent_game_logs = []

        # Pitcher opponent data (NEW)
        self.opposing_pitcher_era = 4.50
        self.opposing_pitcher_k9 = 8.0
        self.opp_pitcher_k_rate = 0.20

        # Advanced stats (NEW)
        self.xwoba_diff = 0.0
        self.is_undervalued = False
        self.platoon_advantage = False

        # For pitchers (NEW)
        self.k9 = 8.0
        self.whiff_rate = 25.0
        self.barrel_rate_against = 8.0

        # Private data storage
        self._vegas_data = None
        self._statcast_data = None
        self._recent_performance = None
        self._park_factors = None
        self._score_components = {}

        # Calculate initial scores
        self.calculate_data_quality()
        self.calculate_enhanced_score()

    # In unified_player_model.py, inside the UnifiedPlayer class:

    # Add this method to your UnifiedPlayer class in unified_player_model.py

    @classmethod
    def from_csv_row(cls, row: Dict) -> 'UnifiedPlayer':
        """Create UnifiedPlayer from DraftKings CSV row"""
        # Extract data from CSV row - handle different column variations
        name = row.get('Name', row.get('name', ''))
        position = row.get('Position', row.get('Pos', ''))
        team = row.get('TeamAbbrev', row.get('Team', ''))
        salary = int(row.get('Salary', 0))

        # Handle game info to extract opponent
        game_info = row.get('Game Info', row.get('GameInfo', ''))
        opponent = ''
        if game_info and '@' in game_info:
            # Parse "TB@BOS" format
            teams = game_info.split('@')
            if team == teams[0]:
                opponent = teams[1]
            else:
                opponent = teams[0]

        # Generate unique ID
        player_id = f"{name.replace(' ', '_')}_{team}".lower()

        # Parse positions (handle multi-position)
        positions = position.split('/')
        primary_position = positions[0]

        # Get base projection
        base_projection = float(row.get('AvgPointsPerGame',
                                        row.get('Projection',
                                                row.get('proj', 0))))

        # Create instance
        player = cls(
            id=player_id,
            name=name,
            team=team,
            salary=salary,
            primary_position=primary_position,
            positions=positions,
            base_projection=base_projection
        )

        # Add additional attributes
        player.opponent = opponent
        player.game_info = game_info

        # Add batting order if available
        if 'batting_order' in row:
            player.batting_order = int(row['batting_order'])

        # Store DFF projection
        player.dff_projection = base_projection

        return player

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
        """Simplified data quality calculation"""
        quality_checks = {
            'has_projection': bool(getattr(self, 'base_projection', 0) > 0),
            'has_vegas': bool(self._get_team_total() > 0),
            'has_batting_order': bool(
                getattr(self, 'batting_order', None) is not None and getattr(self, 'batting_order', 0) > 0),
            'has_team': bool(getattr(self, 'team', None))
        }

        self.data_quality_score = sum(quality_checks.values()) / len(quality_checks)
        self.has_minimum_data = quality_checks['has_projection'] and quality_checks['has_team']

    def is_eligible_for_selection(self, mode: str = "normal") -> bool:
        """Check if player is eligible based on mode"""
        if mode == "bulletproof":
            return self.is_confirmed and self.enhanced_score > 0
        elif mode == "confirmed_only":
            return self.is_confirmed
        elif mode == "all":
            return self.enhanced_score > 0
        else:  # normal
            return self.enhanced_score > 0

    def calculate_data_quality(self):
        """Calculate data quality score (0-1)"""
        quality_points = 0
        max_points = 0

        # Check data availability
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
        """Calculate score using ONLY the new enhanced scoring engine"""
        from enhanced_scoring_engine import EnhancedScoringEngine

        # Create scoring engine
        engine = EnhancedScoringEngine()

        # Default to GPP scoring (can be changed based on context)
        self.enhanced_score = engine.score_player_gpp(self)

        # Also calculate and store other contest scores
        self.gpp_score = self.enhanced_score
        self.cash_score = engine.score_player_cash(self)
        self.showdown_score = engine.score_player_showdown(self)

        # Set data quality based on available data
        data_points = 0
        if hasattr(self, 'implied_team_score') and self.implied_team_score: data_points += 1
        if hasattr(self, 'batting_order') and self.batting_order: data_points += 1
        if hasattr(self, 'projected_ownership'): data_points += 1
        if hasattr(self, 'recent_form_score'): data_points += 1

        self.data_quality_score = min(1.0, 0.2 + (data_points * 0.2))

        return self.enhanced_score

    def set_contest_type(self, contest_type: str):
        """Set which score to use as enhanced_score"""
        from enhanced_scoring_engine import EnhancedScoringEngine
        engine = EnhancedScoringEngine()

        if contest_type.lower() == 'cash':
            self.enhanced_score = engine.score_player_cash(self)
        elif contest_type.lower() == 'showdown':
            self.enhanced_score = engine.score_player_showdown(self)
        else:  # Default to GPP
            self.enhanced_score = engine.score_player_gpp(self)



    def calculate_data_quality(self):
        """Calculate data quality score (0-1)"""
        quality_points = 0
        max_points = 0

        # Check data availability
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

    def calculate_player_scores(self, players: List) -> List:
        """
        Use scores from pure data engine - NO MODIFICATIONS
        The pure data scoring engine has already calculated final scores.
        """
        for player in players:
            # Simply ensure optimization_score is set
            if not hasattr(player, 'optimization_score') or player.optimization_score == 0:
                player.optimization_score = getattr(player, 'enhanced_score', 0)

        return players

    def _calculate_recent_performance(self) -> Optional[float]:
        """
        Calculate recent form multiplier from REAL data only
        Returns None if no real data available
        """
        # Priority 1: Recent performance from form analyzer
        if self._recent_performance and "form_score" in self._recent_performance:
            return self._recent_performance["form_score"]

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
        if len(self.recent_scores) >= 3:
            avg_recent = sum(self.recent_scores[-5:]) / len(self.recent_scores[-5:])
            if self.base_projection > 0:
                ratio = avg_recent / self.base_projection
                return max(0.70, min(1.30, 0.70 + (ratio * 0.30)))

        return None

    def _calculate_vegas_environment(self) -> Optional[float]:
        """
        Calculate Vegas environment multiplier
        Returns None if no Vegas data available
        """
        if not self._vegas_data and not self.implied_team_score:
            return None

        # Get implied team total
        implied_total = None
        if self._vegas_data and "implied_total" in self._vegas_data:
            implied_total = self._vegas_data["implied_total"]
        elif self.implied_team_score:
            implied_total = self.implied_team_score

        if implied_total is None or implied_total <= 0:
            return None

        # Calculate multiplier based on position
        if self.primary_position == "P":
            # For pitchers: opponent's implied total matters
            opp_total = None

            if self._vegas_data and "opponent_total" in self._vegas_data:
                opp_total = self._vegas_data["opponent_total"]
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

    def prepare_players_for_optimization(self, players: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """
        Pre-calculate stack bonuses to avoid quadratic terms in MILP
        """
        # Reset all stack bonuses
        for player in players:
            player._stack_bonus = 0.0

        # Group by team
        team_groups = {}
        for player in players:
            if player.team and player.primary_position != "P":
                if player.team not in team_groups:
                    team_groups[player.team] = []
                team_groups[player.team].append(player)

        # Apply stack bonuses for teams with good correlation
        for team, team_players in team_groups.items():
            if len(team_players) >= 3:
                # Check for consecutive batting orders
                with_order = [
                    p for p in team_players if hasattr(p, "batting_order") and p.batting_order
                ]

                if len(with_order) >= 2:
                    with_order.sort(key=lambda p: p.batting_order)

                    # Mark players in consecutive order
                    for i in range(len(with_order) - 1):
                        if with_order[i + 1].batting_order - with_order[i].batting_order == 1:
                            # These players get a small stack bonus
                            with_order[i]._stack_bonus = self.config.correlation_boost / 2
                            with_order[i + 1]._stack_bonus = self.config.correlation_boost / 2

        return players

    def get_optimization_score(self, player: UnifiedPlayer) -> float:
        """
        Get player's score for optimization including pre-calculated bonuses
        """
        base_score = player.enhanced_score

        # Apply pre-calculated stack bonuses
        if hasattr(player, "_stack_bonus"):
            return base_score * (1 + player._stack_bonus)

        # Apply diversity penalty if exists
        if hasattr(player, "_diversity_penalty"):
            return base_score * player._diversity_penalty

        return base_score

    def _calculate_matchup_quality(self) -> Optional[float]:
        """
        Calculate matchup quality from REAL data only
        FIXED: Small adjustments only (0.9-1.1 range)
        Returns None if no real data available
        """
        if not self._statcast_data:
            return None

        adjustments = 0
        total_factor = 1.0

        if self.primary_position == "P":
            # Pitcher metrics (small adjustments only)
            if "k_rate" in self._statcast_data:
                k_rate = self._statcast_data["k_rate"]
                if k_rate > 28:
                    total_factor *= 1.03  # 3% boost for elite K rate
                    adjustments += 1
                elif k_rate < 19:
                    total_factor *= 0.97  # 3% penalty for low K rate
                    adjustments += 1

            if "whip" in self._statcast_data:
                whip = self._statcast_data["whip"]
                if whip < 1.00:
                    total_factor *= 1.02  # 2% boost for elite WHIP
                    adjustments += 1
                elif whip > 1.40:
                    total_factor *= 0.98  # 2% penalty for poor WHIP
                    adjustments += 1
        else:
            # Hitter metrics (small adjustments only)
            if "barrel_rate" in self._statcast_data:
                barrel = self._statcast_data["barrel_rate"]
                if barrel > 12:
                    total_factor *= 1.03  # 3% boost for elite barrels
                    adjustments += 1
                elif barrel < 6:
                    total_factor *= 0.97  # 3% penalty for poor barrels
                    adjustments += 1

            if "hard_hit_rate" in self._statcast_data:
                hard_hit = self._statcast_data["hard_hit_rate"]
                if hard_hit > 45:
                    total_factor *= 1.02  # 2% boost
                    adjustments += 1
                elif hard_hit < 35:
                    total_factor *= 0.98  # 2% penalty
                    adjustments += 1

        # Only return if we made adjustments based on real data
        return total_factor if adjustments > 0 else None

    def _calculate_park_adjustment(self) -> Optional[float]:
        """
        Calculate park factor adjustment
        Returns None if no park data available
        """
        if not self._park_factors:
            # Try to use default park factors
            if self.team in PARK_FACTORS:
                return PARK_FACTORS[self.team]
            return None

        # Use provided park factors
        if "factor" in self._park_factors:
            return self._park_factors["factor"]

        return None

    # Data application methods
    def apply_dff_data(self, dff_data: Dict):
        """Apply DFF data to player"""
        # Handle None or empty data
        if dff_data is None:
            return

        if "projection" in dff_data:
            self.dff_projection = dff_data["projection"]
        if "l5_avg" in dff_data:
            self.dff_l5_avg = dff_data["l5_avg"]
        if "consistency" in dff_data:
            self.dff_consistency = dff_data["consistency"]

        # Recalculate scores
        self.calculate_data_quality()
        self.calculate_enhanced_score()

    def apply_vegas_data(self, vegas_data: Dict):
        """Apply Vegas data to player"""
        self._vegas_data = vegas_data

        # Extract key fields
        if "implied_total" in vegas_data:
            self.implied_team_score = vegas_data["implied_total"]
        if "game_total" in vegas_data:
            self.over_under = vegas_data["game_total"]
        if "moneyline" in vegas_data:
            self.moneyline = vegas_data["moneyline"]

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
        if "recent_games" in form_data:
            self.recent_scores = [
                g.get("fantasy_points", 0) for g in form_data["recent_games"][-5:]
            ]

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

        if "recent_form_mult" in self._score_components:
            parts.append(
                f"Recent: {self._score_components['recent_form_mult']:.2f}x ({self._score_components['recent_form_weight']:.0%})"
            )
        if "vegas_mult" in self._score_components:
            parts.append(
                f"Vegas: {self._score_components['vegas_mult']:.2f}x ({self._score_components['vegas_weight']:.0%})"
            )
        if "matchup_mult" in self._score_components:
            parts.append(
                f"Matchup: {self._score_components['matchup_mult']:.2f}x ({self._score_components['matchup_weight']:.0%})"
            )
        if "park_mult" in self._score_components:
            parts.append(
                f"Park: {self._score_components['park_mult']:.2f}x ({self._score_components['park_weight']:.0%})"
            )
        if "batting_order_mult" in self._score_components:
            parts.append(
                f"Order: {self._score_components['batting_order_mult']:.2f}x ({self._score_components['batting_order_weight']:.0%})"
            )

        parts.append(
            f"Final: {self.enhanced_score:.1f} ({self._score_components.get('final_multiplier', 1.0):.2f}x)"
        )

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
        return (
            f"UnifiedPlayer({self.name}, {self.primary_position}, "
            f"${self.salary}, score={self.enhanced_score:.1f}, "
            f"quality={self.data_quality_score:.2f})"
        )


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
        base_projection=12.5,
    )

    # Apply some real data
    player.apply_vegas_data({"implied_total": 5.2, "game_total": 9.5, "opponent_total": 4.3})

    player.apply_statcast_data({"barrel_rate": 14.5, "hard_hit_rate": 48.2, "xba": 0.295})

    player.dff_l5_avg = 14.8
    player.batting_order = 3

    # Calculate score
    player.calculate_enhanced_score()

    print(player)
    print(f"Score breakdown: {player.score_breakdown}")
    print(f"Value: {player.value_score:.2f} pts/$1k")
