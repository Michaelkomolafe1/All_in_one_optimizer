#!/usr/bin/env python3
"""
AUTOMATED STACKING SYSTEM
========================
Intelligent lineup stacking based on data-driven analysis
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class StackCandidate:
    """Represents a potential stack"""
    team: str
    players: List  # List of player objects
    stack_score: float = 0.0
    implied_total: float = 0.0
    opposing_pitcher: Optional[str] = None
    park_factor: float = 1.0
    correlation_bonus: float = 0.0
    reasons: List[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.players)

    @property
    def total_salary(self) -> int:
        return sum(p.salary for p in self.players)

    @property
    def avg_projection(self) -> float:
        return np.mean([p.enhanced_score for p in self.players]) if self.players else 0

    @property
    def has_top_order(self) -> bool:
        """Check if stack includes top of batting order"""
        return any(
            getattr(p, 'batting_order', 0) <= 3
            for p in self.players
        )

    def get_batting_order_string(self) -> str:
        """Get batting order positions as string"""
        orders = sorted([
            getattr(p, 'batting_order', 0)
            for p in self.players
            if getattr(p, 'batting_order', 0) > 0
        ])
        return f"[{','.join(map(str, orders))}]" if orders else "[?]"


class AutomatedStackingSystem:
    """
    Identifies and ranks optimal stacking opportunities
    Based on multiple data-driven factors
    """

    def __init__(self):
        # Stack size preferences
        self.min_stack_size = 3
        self.max_stack_size = 5
        self.preferred_stack_size = 4

        # Scoring weights
        self.stack_weights = {
            'implied_total': 0.30,  # Vegas implied runs
            'pitcher_matchup': 0.25,  # Opposing pitcher quality
            'recent_offense': 0.20,  # Team's recent scoring
            'batting_order': 0.15,  # Consecutive batting order
            'park_factor': 0.10  # Ballpark advantage
        }

        # Thresholds
        self.min_implied_total = 4.5  # Minimum team total to consider
        self.elite_implied_total = 5.5  # Elite offensive environment

        # Park factors for stacking
        self.hitter_friendly_parks = {
            'COL': 1.20,  # Coors Field
            'CIN': 1.12,  # Great American Ball Park
            'TEX': 1.10,  # Globe Life Field
            'BOS': 1.08,  # Fenway Park
            'BAL': 1.06,  # Camden Yards
            'PHI': 1.05,  # Citizens Bank Park
            'MIL': 1.05,  # American Family Field
            'HOU': 1.04  # Minute Maid Park
        }

        logger.info("Automated Stacking System initialized")

    def identify_stack_candidates(self, players: List,
                                  vegas_data: Dict = None,
                                  min_confirmed: int = 2) -> List[StackCandidate]:
        """
        Identify all potential stacking opportunities

        Args:
            players: List of all players
            vegas_data: Vegas lines by team
            min_confirmed: Minimum confirmed players required in stack

        Returns:
            List of StackCandidate objects sorted by score
        """
        # Group players by team
        team_players = self._group_players_by_team(players)

        # Identify stackable teams
        stack_candidates = []

        for team, team_players_list in team_players.items():
            # Skip if not enough players
            if len(team_players_list) < self.min_stack_size:
                continue

            # Check if enough confirmed players
            confirmed_count = sum(
                1 for p in team_players_list
                if getattr(p, 'is_confirmed', False)
            )

            if confirmed_count < min_confirmed:
                continue

            # Create stack candidate
            candidate = self._evaluate_team_stack(
                team,
                team_players_list,
                vegas_data
            )

            if candidate and candidate.stack_score > 0:
                stack_candidates.append(candidate)

        # Sort by score
        stack_candidates.sort(key=lambda x: x.stack_score, reverse=True)

        return stack_candidates

    def _group_players_by_team(self, players: List) -> Dict[str, List]:
        """Group non-pitcher players by team"""
        team_players = {}

        for player in players:
            # Skip pitchers
            if player.primary_position == 'P':
                continue

            # Skip unconfirmed players with low projections
            if (not getattr(player, 'is_confirmed', False) and
                    getattr(player, 'enhanced_score', 0) < 8.0):
                continue

            team = player.team
            if team not in team_players:
                team_players[team] = []

            team_players[team].append(player)

        return team_players

    def _evaluate_team_stack(self, team: str,
                             players: List,
                             vegas_data: Dict = None) -> Optional[StackCandidate]:
        """Evaluate a team's stacking potential"""
        candidate = StackCandidate(team=team, players=[])

        # 1. Check Vegas implied total
        if vegas_data and team in vegas_data:
            team_vegas = vegas_data[team]
            implied_total = team_vegas.get('implied_total', 4.5)
            candidate.implied_total = implied_total

            # Skip low-scoring games
            if implied_total < self.min_implied_total:
                return None

            # Bonus for high-scoring games
            if implied_total >= self.elite_implied_total:
                candidate.reasons.append(f"Elite implied total: {implied_total:.1f}")
        else:
            candidate.implied_total = 4.5  # Default

        # 2. Get opposing pitcher info
        if vegas_data and team in vegas_data:
            candidate.opposing_pitcher = vegas_data[team].get('opposing_pitcher', 'Unknown')

        # 3. Sort players by batting order and projection
        sorted_players = self._sort_players_for_stacking(players)

        # 4. Build optimal stack
        selected_players = self._select_stack_players(sorted_players)

        if len(selected_players) < self.min_stack_size:
            return None

        candidate.players = selected_players

        # 5. Calculate stack score
        self._calculate_stack_score(candidate)

        return candidate

    def _sort_players_for_stacking(self, players: List) -> List:
        """Sort players for optimal stacking selection"""
        # Separate confirmed and unconfirmed
        confirmed = [p for p in players if getattr(p, 'is_confirmed', False)]
        unconfirmed = [p for p in players if not getattr(p, 'is_confirmed', False)]

        # Sort confirmed by batting order, then by projection
        confirmed.sort(key=lambda p: (
            getattr(p, 'batting_order', 10),  # Batting order (10 if unknown)
            -getattr(p, 'enhanced_score', 0)  # Higher projection first
        ))

        # Sort unconfirmed by projection only
        unconfirmed.sort(key=lambda p: getattr(p, 'enhanced_score', 0), reverse=True)

        # Combine: confirmed first, then best unconfirmed
        return confirmed + unconfirmed

    def _select_stack_players(self, sorted_players: List) -> List:
        """Select optimal players for stack"""
        selected = []
        batting_orders = set()

        # First, try to get consecutive batting order players
        for player in sorted_players:
            if len(selected) >= self.max_stack_size:
                break

            batting_order = getattr(player, 'batting_order', None)

            # Always include top 5 batting order
            if batting_order and batting_order <= 5:
                selected.append(player)
                batting_orders.add(batting_order)
            # Include others if they fit
            elif len(selected) < self.preferred_stack_size:
                # Check for consecutive batting order
                if batting_order and self._fits_consecutive_pattern(batting_order, batting_orders):
                    selected.append(player)
                    batting_orders.add(batting_order)
                # Or if high projection
                elif getattr(player, 'enhanced_score', 0) > 10.0:
                    selected.append(player)
                    if batting_order:
                        batting_orders.add(batting_order)

        # Ensure minimum size
        if len(selected) < self.min_stack_size:
            # Add best remaining players
            remaining = [p for p in sorted_players if p not in selected]
            for player in remaining[:self.min_stack_size - len(selected)]:
                selected.append(player)

        return selected[:self.max_stack_size]

    def _fits_consecutive_pattern(self, batting_order: int, existing_orders: Set[int]) -> bool:
        """Check if batting order fits consecutive pattern"""
        if not existing_orders:
            return True

        # Check if adjacent to any existing order
        return any(
            abs(batting_order - existing) == 1
            for existing in existing_orders
        )

    def _calculate_stack_score(self, candidate: StackCandidate):
        """Calculate comprehensive stack score"""
        scores = {}

        # 1. Implied total score (0-1 scale)
        if candidate.implied_total >= self.elite_implied_total:
            scores['implied_total'] = 1.0
        else:
            scores['implied_total'] = max(0, (candidate.implied_total - 3.5) / 2.5)

        # 2. Pitcher matchup score
        scores['pitcher_matchup'] = self._evaluate_pitcher_matchup(candidate)

        # 3. Recent offense score
        scores['recent_offense'] = self._evaluate_recent_offense(candidate)

        # 4. Batting order correlation
        scores['batting_order'] = self._evaluate_batting_order_correlation(candidate)

        # 5. Park factor
        park_factor = self.hitter_friendly_parks.get(candidate.team, 1.0)
        scores['park_factor'] = (park_factor - 0.85) / 0.35  # Normalize to 0-1
        candidate.park_factor = park_factor

        # Apply weights
        total_score = 0.0
        for component, weight in self.stack_weights.items():
            component_score = scores.get(component, 0.5)
            total_score += component_score * weight

        # Scale to 0-100
        candidate.stack_score = total_score * 100

        # Add reasoning
        if scores['implied_total'] > 0.8:
            candidate.reasons.append(f"High implied total: {candidate.implied_total:.1f}")
        if scores['batting_order'] > 0.8:
            candidate.reasons.append(f"Strong batting order correlation {candidate.get_batting_order_string()}")
        if park_factor > 1.05:
            candidate.reasons.append(f"Hitter-friendly park ({park_factor:.2f}x)")

    def _evaluate_pitcher_matchup(self, candidate: StackCandidate) -> float:
        """Evaluate opposing pitcher quality"""
        # Check if any players have opposing pitcher stats
        pitcher_scores = []

        for player in candidate.players:
            if hasattr(player, 'matchup_score'):
                pitcher_scores.append(player.matchup_score)

        if pitcher_scores:
            return np.mean(pitcher_scores)

        # Default based on implied total
        if candidate.implied_total >= 5.5:
            return 0.8  # Likely facing weak pitcher
        elif candidate.implied_total <= 3.5:
            return 0.2  # Likely facing strong pitcher
        else:
            return 0.5

    def _evaluate_recent_offense(self, candidate: StackCandidate) -> float:
        """Evaluate team's recent offensive performance"""
        # Check for hot hitters
        hot_hitters = sum(
            1 for p in candidate.players
            if getattr(p, 'is_hot', False)
        )

        if hot_hitters >= 2:
            return 0.9
        elif hot_hitters == 1:
            return 0.7

        # Check average recent performance
        recent_avgs = [
            getattr(p, 'recent_avg', 0.250)
            for p in candidate.players
        ]

        team_recent_avg = np.mean(recent_avgs) if recent_avgs else 0.250

        # Scale: .200 = 0.0, .300 = 1.0
        return max(0, min(1, (team_recent_avg - 0.200) / 0.100))

    def _evaluate_batting_order_correlation(self, candidate: StackCandidate) -> float:
        """Evaluate batting order correlation strength"""
        batting_orders = [
            getattr(p, 'batting_order', 0)
            for p in candidate.players
            if getattr(p, 'batting_order', 0) > 0
        ]

        if len(batting_orders) < 2:
            return 0.5

        batting_orders.sort()

        # Check for consecutive batters
        consecutive_count = 1
        max_consecutive = 1

        for i in range(1, len(batting_orders)):
            if batting_orders[i] - batting_orders[i - 1] == 1:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 1

        # Also check if we have top of order
        has_top_order = any(bo <= 3 for bo in batting_orders)

        # Score based on consecutive and position
        base_score = max_consecutive / len(batting_orders)
        if has_top_order:
            base_score += 0.2

        return min(1.0, base_score)

    def recommend_stacks(self, stack_candidates: List[StackCandidate],
                         salary_budget: int,
                         max_recommendations: int = 3) -> List[StackCandidate]:
        """
        Recommend best stacks considering salary constraints

        Args:
            stack_candidates: All potential stacks
            salary_budget: Available salary for stacking
            max_recommendations: Maximum stacks to recommend

        Returns:
            List of recommended stacks
        """
        recommendations = []
        used_teams = set()

        for candidate in stack_candidates:
            # Skip if team already used
            if candidate.team in used_teams:
                continue

            # Skip if too expensive
            if candidate.total_salary > salary_budget * 0.6:  # Don't use >60% on one stack
                continue

            # Skip if score too low
            if candidate.stack_score < 50:
                continue

            recommendations.append(candidate)
            used_teams.add(candidate.team)

            if len(recommendations) >= max_recommendations:
                break

        return recommendations

    def apply_stack_to_optimizer(self, optimizer_config: Dict,
                                 selected_stack: StackCandidate) -> Dict:
        """
        Apply stacking constraints to optimizer configuration

        Args:
            optimizer_config: Current optimizer configuration
            selected_stack: The stack to enforce

        Returns:
            Updated configuration with stack constraints
        """
        # Add constraints to force stack inclusion
        stack_constraints = {
            'force_players': [p.name for p in selected_stack.players],
            'min_from_team': {selected_stack.team: selected_stack.size},
            'stack_type': 'team_stack',
            'correlation_bonus': selected_stack.correlation_bonus
        }

        # Update optimizer config
        optimizer_config['stack_constraints'] = stack_constraints

        # Adjust position requirements if needed
        # (ensure we have enough roster spots)

        return optimizer_config

    def display_stack_analysis(self, stack_candidates: List[StackCandidate]):
        """Display detailed stack analysis"""
        print("\n" + "=" * 80)
        print("🏟️  AUTOMATED STACK ANALYSIS")
        print("=" * 80)

        if not stack_candidates:
            print("No viable stacks found")
            return

        print(f"\nFound {len(stack_candidates)} potential stacks:\n")

        for i, stack in enumerate(stack_candidates[:5], 1):
            print(f"{i}. {stack.team} Stack (Score: {stack.stack_score:.1f})")
            print(f"   Players: {stack.size} | Salary: ${stack.total_salary:,}")
            print(f"   Implied Total: {stack.implied_total:.1f} runs")
            print(f"   Batting Order: {stack.get_batting_order_string()}")
            print(f"   Avg Projection: {stack.avg_projection:.1f} pts")

            if stack.reasons:
                print(f"   Key Factors:")
                for reason in stack.reasons:
                    print(f"     • {reason}")

            # Show players
            print(f"   Stack Composition:")
            for p in stack.players[:5]:  # Show up to 5
                confirmed = "✓" if getattr(p, 'is_confirmed', False) else " "
                order = getattr(p, 'batting_order', '?')
                print(f"     {confirmed} {order}. {p.name:<15} ${p.salary:,} ({p.enhanced_score:.1f} pts)")

            print()


def create_stacking_system() -> AutomatedStackingSystem:
    """Factory function to create stacking system"""
    return AutomatedStackingSystem()


if __name__ == "__main__":
    print("✅ Automated Stacking System loaded")
    print("\n📊 Stack evaluation factors:")
    print("  - Vegas implied team totals")
    print("  - Opposing pitcher matchups")
    print("  - Recent team offensive performance")
    print("  - Batting order correlation")
    print("  - Park factors")
    print("\n🎯 Identifies optimal 3-5 player stacks automatically!")