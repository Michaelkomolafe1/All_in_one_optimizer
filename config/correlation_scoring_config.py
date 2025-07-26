#!/usr/bin/env python3
"""
CORRELATION AWARE SCORING CONFIGURATION
======================================
Based on test results showing correlation_aware as the winner
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class CorrelationAwareScoringConfig:
    """Configuration for the winning correlation-aware scoring system"""

    # Stacking thresholds
    team_total_threshold: float = 5.0  # Teams projected for 5+ runs
    team_total_boost: float = 1.15  # 15% boost for high-scoring teams

    # Batting order boosts
    premium_batting_positions: List[int] = field(default_factory=lambda: [1, 2, 3, 4])
    batting_order_boost: float = 1.10  # 10% boost for top of order

    # Additional correlation factors to implement
    correlation_factors: Dict[str, float] = field(
        default_factory=lambda: {
            "consecutive_order_bonus": 0.05,  # 5% for consecutive batters
            "same_team_pitcher_penalty": -0.20,  # -20% for opposing your pitcher
            "mini_stack_bonus": 0.08,  # 8% for 2-3 player stacks
            "full_stack_bonus": 0.12,  # 12% for 4+ player stacks
            "game_total_high": 0.05,  # 5% for games with O/U > 10
            "game_total_low": -0.05,  # -5% for games with O/U < 7
        }
    )

    # Park factor adjustments (simplified)
    park_multipliers: Dict[str, float] = field(
        default_factory=lambda: {
            "extreme_hitter": 1.08,  # Coors, Great American
            "hitter_friendly": 1.04,  # Yankees, Rangers
            "neutral": 1.00,  # Most parks
            "pitcher_friendly": 0.96,  # Dodger Stadium, Petco
            "extreme_pitcher": 0.92,  # Marlins Park
        }
    )

    # Contest type adjustments
    contest_adjustments: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: {
            "cash": {
                "correlation_weight": 0.7,  # Less emphasis on stacking
                "floor_weight": 1.3,  # More emphasis on consistency
                "ceiling_weight": 0.7,  # Less emphasis on upside
            },
            "gpp": {
                "correlation_weight": 1.3,  # Heavy stacking emphasis
                "floor_weight": 0.7,  # Less emphasis on floor
                "ceiling_weight": 1.3,  # More emphasis on ceiling
                "ownership_factor": -0.15,  # Fade high ownership in large GPPs
            }
        }
    )

    # Statistical thresholds for validation
    validation_thresholds: Dict[str, Tuple[float, float]] = field(
        default_factory=lambda: {
            "min_team_total": (2.5, 15.0),
            "batting_order": (1, 9),
            "correlation_score": (0.0, 2.0),
            "final_score": (0.0, 100.0),
        }
    )

    def __post_init__(self):
        """Validate configuration"""
        if self.team_total_boost < 1.0:
            raise ValueError("team_total_boost must be >= 1.0")
        if self.batting_order_boost < 1.0:
            raise ValueError("batting_order_boost must be >= 1.0")


class CorrelationAwareScorer:
    """Simplified scorer based on the winning correlation_aware method"""

    def __init__(self, config: CorrelationAwareScoringConfig = None):
        self.config = config or CorrelationAwareScoringConfig()
        self._stack_groups = {}  # Track stacks for bonuses

    def calculate_score(self, player, contest_type: str = "gpp") -> float:
        """
        Calculate player score using correlation-aware method
        This is the SIMPLIFIED winning approach from your tests
        """
        # Start with base projection
        base_score = self._get_base_projection(player)
        if base_score <= 0:
            return 0

        # Apply correlation-aware adjustments
        score = base_score

        # 1. Team Total Boost (KEY FACTOR)
        team_total = self._get_team_total(player)
        if team_total > self.config.team_total_threshold:
            score *= self.config.team_total_boost

        # 2. Batting Order Boost (KEY FACTOR)
        if not player.primary_position == "P":
            batting_order = getattr(player, 'batting_order', 0)
            if batting_order in self.config.premium_batting_positions:
                score *= self.config.batting_order_boost

        # 3. Park Factor (SIMPLE)
        park_category = self._get_park_category(player)
        park_mult = self.config.park_multipliers.get(park_category, 1.0)
        if player.primary_position == "P":
            # Invert for pitchers
            park_mult = 2.0 - park_mult
        score *= park_mult

        # 4. Contest-specific adjustments
        contest_adj = self.config.contest_adjustments.get(contest_type, {})
        correlation_weight = contest_adj.get("correlation_weight", 1.0)
        score *= correlation_weight

        # 5. Game total adjustment
        game_total = self._get_game_total(player)
        if game_total > 10:
            score *= (1 + self.config.correlation_factors["game_total_high"])
        elif game_total < 7:
            score *= (1 + self.config.correlation_factors["game_total_low"])

        return max(0, score)

    def _get_base_projection(self, player) -> float:
        """Get the most reliable projection available"""
        # Priority order based on your test results
        if hasattr(player, 'dk_projection') and player.dk_projection > 0:
            return player.dk_projection
        elif hasattr(player, 'base_projection') and player.base_projection > 0:
            return player.base_projection
        elif hasattr(player, 'projection') and player.projection > 0:
            return player.projection
        return 0

    def _get_team_total(self, player) -> float:
        """Get team's implied total runs"""
        if hasattr(player, 'team_total') and player.team_total > 0:
            return player.team_total
        elif hasattr(player, 'implied_team_score') and player.implied_team_score:
            return player.implied_team_score
        elif hasattr(player, '_vegas_data') and player._vegas_data:
            return player._vegas_data.get('implied_total', 0)
        return 0

    def _get_game_total(self, player) -> float:
        """Get game's over/under total"""
        if hasattr(player, 'vegas_total') and player.vegas_total > 0:
            return player.vegas_total
        elif hasattr(player, 'over_under') and player.over_under:
            return player.over_under
        return 8.5  # MLB average

    def _get_park_category(self, player) -> str:
        """Categorize park for simple adjustments"""
        team = getattr(player, 'team', '')

        # Extreme hitter parks
        if team in ['COL', 'CIN']:
            return "extreme_hitter"
        # Hitter friendly
        elif team in ['TEX', 'BAL', 'NYY', 'PHI']:
            return "hitter_friendly"
        # Pitcher friendly
        elif team in ['LAD', 'SD', 'SEA', 'SF']:
            return "pitcher_friendly"
        # Extreme pitcher
        elif team in ['MIA', 'OAK']:
            return "extreme_pitcher"
        else:
            return "neutral"

    def apply_stack_bonuses(self, lineup: List, positions_filled: Dict) -> List:
        """
        Apply correlation bonuses to players in stacks
        This happens AFTER initial scoring
        """
        # Count players per team
        team_counts = {}
        team_players = {}

        for pos, player in positions_filled.items():
            if player and player.team:
                team = player.team
                team_counts[team] = team_counts.get(team, 0) + 1
                if team not in team_players:
                    team_players[team] = []
                team_players[team].append((pos, player))

        # Apply stack bonuses
        for team, count in team_counts.items():
            if count >= 4:
                # Full stack bonus
                bonus = self.config.correlation_factors["full_stack_bonus"]
            elif count >= 2:
                # Mini stack bonus
                bonus = self.config.correlation_factors["mini_stack_bonus"]
            else:
                continue

            # Apply bonus to stacked players
            for pos, player in team_players[team]:
                if hasattr(player, 'enhanced_score'):
                    player.stack_correlation_bonus = player.enhanced_score * bonus

        # Check for consecutive batting order bonus
        for team, players in team_players.items():
            if len(players) >= 2:
                # Sort by batting order
                players_with_order = [
                    (p, getattr(p[1], 'batting_order', 0))
                    for p in players if getattr(p[1], 'batting_order', 0) > 0
                ]

                if len(players_with_order) >= 2:
                    players_with_order.sort(key=lambda x: x[1])

                    # Check for consecutive orders
                    for i in range(len(players_with_order) - 1):
                        if players_with_order[i + 1][1] - players_with_order[i][1] == 1:
                            # Apply consecutive bonus
                            bonus = self.config.correlation_factors["consecutive_order_bonus"]
                            players_with_order[i][0][1].consecutive_order_bonus = (
                                    players_with_order[i][0][1].enhanced_score * bonus
                            )
                            players_with_order[i + 1][0][1].consecutive_order_bonus = (
                                    players_with_order[i + 1][0][1].enhanced_score * bonus
                            )

        return lineup