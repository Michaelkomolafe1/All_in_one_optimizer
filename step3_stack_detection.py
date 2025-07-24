#!/usr/bin/env python3
"""
STEP 3: Stack Detection and Optimizer Integration
=================================================
Implements smart stack detection and correlation bonuses
"""

import logging
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class StackInfo:
    """Information about a detected stack"""
    team: str
    players: List[any]  # List of players
    size: int
    total_salary: int
    avg_score: float
    correlation_score: float
    has_consecutive_order: bool
    batting_orders: List[int]


class StackDetector:
    """
    Detects and scores potential stacks based on correlation
    This is what makes the correlation_aware method work!
    """

    def __init__(self):
        self.min_stack_size = 2
        self.max_stack_size = 5

    def detect_stacks(self, players: List) -> Dict[str, StackInfo]:
        """
        Detect all possible stacks from player pool
        Returns dict of team -> StackInfo
        """
        # Group players by team (excluding pitchers)
        team_players = defaultdict(list)

        for player in players:
            if player.team and player.primary_position != "P":
                team_players[player.team].append(player)

        # Analyze each team for stack potential
        stacks = {}

        for team, team_roster in team_players.items():
            if len(team_roster) >= self.min_stack_size:
                stack_info = self._analyze_stack(team, team_roster)
                if stack_info and stack_info.correlation_score > 0:
                    stacks[team] = stack_info

        return stacks

    def _analyze_stack(self, team: str, players: List) -> Optional[StackInfo]:
        """Analyze a potential stack for quality"""
        if len(players) < self.min_stack_size:
            return None

        # Sort by batting order if available
        players_with_order = []
        players_without_order = []

        for p in players:
            if hasattr(p, 'batting_order') and p.batting_order > 0:
                players_with_order.append(p)
            else:
                players_without_order.append(p)

        # Sort by batting order
        players_with_order.sort(key=lambda x: x.batting_order)

        # Combine lists (ordered players first)
        sorted_players = players_with_order + players_without_order

        # Get best players for stack (top by score)
        sorted_players.sort(key=lambda x: getattr(x, 'enhanced_score', 0), reverse=True)
        best_players = sorted_players[:self.max_stack_size]

        # Calculate stack metrics
        batting_orders = [
            p.batting_order for p in best_players
            if hasattr(p, 'batting_order') and p.batting_order > 0
        ]

        has_consecutive = self._has_consecutive_orders(batting_orders)
        correlation_score = self._calculate_correlation_score(
            best_players, has_consecutive
        )

        return StackInfo(
            team=team,
            players=best_players,
            size=len(best_players),
            total_salary=sum(p.salary for p in best_players),
            avg_score=sum(p.enhanced_score for p in best_players) / len(best_players),
            correlation_score=correlation_score,
            has_consecutive_order=has_consecutive,
            batting_orders=batting_orders
        )

    def _has_consecutive_orders(self, orders: List[int]) -> bool:
        """Check if batting orders are consecutive"""
        if len(orders) < 2:
            return False

        sorted_orders = sorted(orders)
        for i in range(len(sorted_orders) - 1):
            if sorted_orders[i + 1] - sorted_orders[i] == 1:
                return True
        return False

    def _calculate_correlation_score(self, players: List, has_consecutive: bool) -> float:
        """
        Calculate how well these players correlate
        Higher score = better stack
        """
        score = 1.0

        # Check team total
        team_totals = []
        for p in players:
            total = 0
            if hasattr(p, 'team_total') and p.team_total > 0:
                total = p.team_total
            elif hasattr(p, '_vegas_data') and p._vegas_data:
                total = p._vegas_data.get('implied_total', 0)
            if total > 0:
                team_totals.append(total)

        if team_totals:
            avg_total = sum(team_totals) / len(team_totals)
            if avg_total > 5.5:
                score *= 1.3
            elif avg_total > 5.0:
                score *= 1.2
            elif avg_total > 4.5:
                score *= 1.1
            elif avg_total < 3.5:
                score *= 0.7

        # Batting order concentration
        orders = [p.batting_order for p in players
                  if hasattr(p, 'batting_order') and p.batting_order > 0]

        if orders:
            # Reward top-of-order concentration
            top_4_count = sum(1 for o in orders if o <= 4)
            if top_4_count >= 3:
                score *= 1.2
            elif top_4_count >= 2:
                score *= 1.1

            # Bonus for consecutive orders
            if has_consecutive:
                score *= 1.15

        # Stack size bonus
        if len(players) >= 4:
            score *= 1.1
        elif len(players) == 3:
            score *= 1.05

        return score


class EnhancedOptimizer:
    """
    Enhanced optimizer that leverages correlation for stacking
    Integrates with your existing MILP optimizer
    """

    def __init__(self, base_optimizer):
        self.base_optimizer = base_optimizer
        self.stack_detector = StackDetector()
        self.contest_type = "gpp"

    def set_contest_type(self, contest_type: str):
        """Configure optimizer for contest type"""
        self.contest_type = contest_type.lower()

        if self.contest_type in ["cash", "50-50", "double-up"]:
            # Cash game settings
            self.stack_detector.min_stack_size = 1
            self.stack_detector.max_stack_size = 3
            self.min_correlation_score = 1.1
            self.max_exposure = 0.3  # Max 30% exposure to any team
        else:
            # GPP settings
            self.stack_detector.min_stack_size = 3
            self.stack_detector.max_stack_size = 5
            self.min_correlation_score = 1.0
            self.max_exposure = 0.6  # Max 60% exposure to any team

    def optimize_with_stacks(self, players: List, num_lineups: int = 1) -> List[Dict]:
        """
        Optimize lineups with correlation-aware stacking
        """
        # Detect potential stacks
        stacks = self.stack_detector.detect_stacks(players)

        # Log stack information
        logger.info(f"Detected {len(stacks)} potential stacks")
        for team, stack_info in stacks.items():
            if stack_info.correlation_score >= self.min_correlation_score:
                logger.info(f"  {team}: {stack_info.size} players, "
                            f"correlation={stack_info.correlation_score:.2f}, "
                            f"avg_score={stack_info.avg_score:.1f}")

        # Filter to quality stacks
        quality_stacks = {
            team: info for team, info in stacks.items()
            if info.correlation_score >= self.min_correlation_score
        }

        lineups = []
        used_stacks = defaultdict(int)

        for i in range(num_lineups):
            # Select primary stack for this lineup
            primary_stack = self._select_primary_stack(
                quality_stacks, used_stacks, i
            )

            if primary_stack:
                # Build lineup around the stack
                lineup = self._build_lineup_with_stack(
                    players, primary_stack, stacks
                )

                if lineup:
                    lineups.append(lineup)
                    # Track stack usage
                    used_stacks[primary_stack.team] += 1

                    # Log lineup info
                    logger.info(f"Lineup {i + 1}: {primary_stack.team} stack "
                                f"({primary_stack.size} players)")
            else:
                # No good stacks left, use base optimizer
                lineup = self._build_balanced_lineup(players)
                if lineup:
                    lineups.append(lineup)

        return lineups

    def _select_primary_stack(self, quality_stacks: Dict, used_stacks: Dict,
                              lineup_num: int) -> Optional[StackInfo]:
        """Select the best available stack for this lineup"""
        # Sort stacks by correlation score * avg score
        stack_scores = []

        for team, stack_info in quality_stacks.items():
            # Check exposure limit
            usage_rate = used_stacks[team] / max(1, lineup_num)
            if usage_rate >= self.max_exposure:
                continue

            # Calculate stack priority score
            priority = stack_info.correlation_score * stack_info.avg_score

            # Reduce priority if already used
            if used_stacks[team] > 0:
                priority *= (1 - usage_rate * 0.5)

            stack_scores.append((priority, stack_info))

        if not stack_scores:
            return None

        # Select best stack
        stack_scores.sort(reverse=True)
        return stack_scores[0][1]

    def _build_lineup_with_stack(self, all_players: List, primary_stack: StackInfo,
                                 all_stacks: Dict) -> Optional[Dict]:
        """Build a lineup around a primary stack"""
        # Start with stack players
        lineup_players = primary_stack.players[:4]  # Max 4 from primary stack
        used_teams = {primary_stack.team}
        used_positions = set()
        total_salary = sum(p.salary for p in lineup_players)

        # Track positions used
        for p in lineup_players:
            used_positions.add(p.primary_position)

        # Determine if we can add a mini-stack
        remaining_spots = 9 - len(lineup_players)  # Assuming 9-player lineup
        can_add_mini_stack = (remaining_spots >= 2 and
                              self.contest_type != "cash")

        if can_add_mini_stack:
            # Try to add a 2-player mini-stack
            mini_stack = self._select_mini_stack(
                all_stacks, used_teams, primary_stack.team
            )

            if mini_stack and len(lineup_players) + 2 <= 9:
                # Add 2 players from mini stack
                mini_players = mini_stack.players[:2]
                lineup_players.extend(mini_players)
                used_teams.add(mini_stack.team)
                total_salary += sum(p.salary for p in mini_players)

                for p in mini_players:
                    used_positions.add(p.primary_position)

        # Fill remaining spots with best available players
        remaining_budget = 50000 - total_salary
        remaining_spots = 9 - len(lineup_players)

        if remaining_spots > 0:
            # Get eligible players
            eligible = [
                p for p in all_players
                if p not in lineup_players
                   and p.salary <= remaining_budget / remaining_spots * 1.5
                   and (self.contest_type == "gpp" or p.team not in used_teams)
            ]

            # Sort by score
            eligible.sort(key=lambda x: x.enhanced_score, reverse=True)

            # Fill positions needed
            positions_needed = self._get_positions_needed(used_positions)

            for pos in positions_needed:
                best_for_pos = next(
                    (p for p in eligible
                     if p.primary_position == pos
                     and p.salary <= remaining_budget),
                    None
                )

                if best_for_pos:
                    lineup_players.append(best_for_pos)
                    total_salary += best_for_pos.salary
                    remaining_budget = 50000 - total_salary
                    eligible.remove(best_for_pos)

                    if len(lineup_players) >= 9:
                        break

        # Validate lineup
        if len(lineup_players) == 9 and total_salary <= 50000:
            return {
                'players': lineup_players,
                'total_salary': total_salary,
                'total_score': sum(p.enhanced_score for p in lineup_players),
                'primary_stack': primary_stack.team,
                'stack_size': len([p for p in lineup_players
                                   if p.team == primary_stack.team])
            }

        return None

    def _select_mini_stack(self, all_stacks: Dict, used_teams: Set,
                           primary_team: str) -> Optional[StackInfo]:
        """Select a 2-player mini-stack to complement primary stack"""
        candidates = []

        for team, stack_info in all_stacks.items():
            if (team not in used_teams and
                    team != primary_team and
                    stack_info.size >= 2 and
                    stack_info.correlation_score >= 1.05):
                candidates.append(stack_info)

        if candidates:
            # Sort by correlation score
            candidates.sort(key=lambda x: x.correlation_score, reverse=True)
            return candidates[0]

        return None

    def _build_balanced_lineup(self, players: List) -> Optional[Dict]:
        """Build a balanced lineup without heavy stacking (for cash)"""
        # This would use your existing optimizer
        # Just limiting team exposure
        return None  # Placeholder

    def _get_positions_needed(self, used_positions: Set[str]) -> List[str]:
        """Determine what positions still need to be filled"""
        # Standard DFS positions needed
        required = {
            'P': 2,  # 2 pitchers
            'C': 1,  # 1 catcher
            '1B': 1,  # 1 first base
            '2B': 1,  # 1 second base
            '3B': 1,  # 1 third base
            'SS': 1,  # 1 shortstop
            'OF': 3  # 3 outfielders
        }

        # Count what we have
        position_counts = defaultdict(int)
        for pos in used_positions:
            position_counts[pos] += 1

        # Determine what's needed
        needed = []
        for pos, count in required.items():
            current = position_counts.get(pos, 0)
            for _ in range(count - current):
                needed.append(pos)

        return needed


def integrate_with_optimizer(optimizer):
    """
    Integration function to enhance your existing optimizer
    """
    print("\n🔧 Integrating Stack Detection with Optimizer")
    print("=" * 60)

    # Wrap existing optimizer
    enhanced = EnhancedOptimizer(optimizer)

    # Configure based on contest type
    contest_type = getattr(optimizer, 'contest_type', 'gpp')
    enhanced.set_contest_type(contest_type)

    print(f"✅ Optimizer enhanced for {contest_type.upper()}")
    print(f"   Min stack size: {enhanced.stack_detector.min_stack_size}")
    print(f"   Max stack size: {enhanced.stack_detector.max_stack_size}")
    print(f"   Max team exposure: {enhanced.max_exposure * 100}%")

    return enhanced


if __name__ == "__main__":
    print("🎯 Stack Detection and Correlation System")
    print("=" * 60)

    # Example of how stacking improves scores
    print("\n📊 Why Stacking Works:")
    print("\nExample: Yankees vs Orioles, O/U 11.5")
    print("Yankees implied total: 6.5 runs\n")

    print("WITHOUT STACKING:")
    print("- Pick best players individually")
    print("- Judge: 15 pts, Soto: 14 pts, Rizzo: 12 pts")
    print("- Total: 41 pts (if each performs to projection)")

    print("\nWITH CORRELATION STACKING:")
    print("- Same players, but now correlated")
    print("- If Yankees score 8+ runs (beat implied total):")
    print("  - Judge: 25 pts (multi-hit game)")
    print("  - Soto: 22 pts (RBIs batting behind Judge)")
    print("  - Rizzo: 18 pts (cleanup RBIs)")
    print("- Total: 65 pts (58% higher!)")

    print("\n✨ The magic: When one hits, they often ALL hit!")
    print("That's why correlation_aware beat pure statistics!")