#!/usr/bin/env python3
"""
REALISTIC DRAFTKINGS MLB DFS SIMULATOR
=======================================
Based on actual data: 1.3% of players win 91% of profits
Built with real behavioral patterns and variance models
"""

import random
import numpy as np
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


# ==========================================
# REAL DATA FROM RESEARCH
# ==========================================

class PlayerTier(Enum):
    """Actual player distribution in DFS"""
    SUPER_SHARK = 0.0001  # 0.01% - The 11 players making $135k/year
    SHARK = 0.013  # 1.3% - Profitable players with 27% ROI
    BIG_FISH = 0.05  # 5% - High volume losers (-$1,100/year)
    REGULAR = 0.15  # 15% - Semi-regular players
    MINNOW = 0.80  # 80% - Casual players (-$25/year)


# Actual contest dynamics from research
CONTEST_DYNAMICS = {
    '3-man': {
        'shark_percentage': 0.33,  # 1 in 3 is a shark
        'win_rate_vs_sharks': 0.14,  # 14% win rate
        'expected_roi': -0.94,  # -94% ROI due to sharks
        'rake': 0.10
    },
    '5-man': {
        'shark_percentage': 0.20,
        'win_rate_vs_mixed': 0.20,
        'expected_roi': -0.50,
        'rake': 0.10
    },
    '10-man': {
        'shark_percentage': 0.15,
        'win_rate_vs_mixed': 0.18,
        'expected_roi': -0.30,
        'rake': 0.11
    },
    '20-man': {
        'shark_percentage': 0.10,
        'win_rate_vs_mixed': 0.10,
        'expected_roi': -0.20,
        'rake': 0.12
    },
    '100-man': {
        'shark_percentage': 0.08,
        'win_rate_vs_mixed': 0.05,
        'expected_roi': -0.15,
        'rake': 0.14
    },
    '500+': {
        'shark_percentage': 0.05,
        'win_rate_vs_mixed': 0.002,
        'expected_roi': -0.25,
        'rake': 0.159  # Highest rake for large GPPs
    }
}

# ACTUAL stacking frequencies from 10,330 tournament entries
REAL_STACKING_FREQUENCIES = {
    'no_stack': 0.134,  # 13.4% use no stack
    '2_man': 0.268,  # 26.8% use 2-man mini-stack
    '3_man': 0.123,  # 12.3% use 3-man stack
    '4_man': 0.028,  # 2.8% use 4-man stack (RARE!)
    '5_man': 0.006,  # 0.6% use 5-man stack (SUPER RARE!)
    'mixed_mini': 0.441  # 44.1% use multiple mini-stacks
}

# Ownership patterns - CRITICAL INSIGHT
OWNERSHIP_REALITY = {
    'highest_stack_ownership_ever': 0.0066,  # 0.66% max for ANY stack
    'typical_chalk_stack': 0.003,  # 0.3% for "obvious" stacks
    'pitcher_chalk_threshold': 0.30,  # 30% for top pitchers
    'hitter_chalk_threshold': 0.20,  # 20% for top hitters
    'contrarian_threshold': 0.02,  # 2% is truly contrarian
}

# MLB Variance - HIGHEST among all DFS sports
MLB_VARIANCE = {
    'hitter_std_dev': 2.7,  # Points
    'pitcher_std_dev': 4.7,  # Points
    'zero_point_probability': 0.10,  # 10% chance any hitter scores 0
    'pitcher_disaster_rate': 0.15,  # 15% chance of pitcher blowup
    'correlation_same_team': 0.40,  # Team correlation
    'correlation_batting_order': {
        '1_2': 0.087,
        '2_3': 0.076,
        '3_4': 0.089,  # HIGHEST correlation
        '4_5': 0.065,
        'non_consecutive': 0.030
    }
}


@dataclass
class SimulatedPlayer:
    """Realistic player with actual DFS attributes"""
    name: str
    position: str
    team: str
    salary: int
    projection: float
    ownership: float
    batting_order: int = 0

    # Variance factors
    ceiling: float = 0
    floor: float = 0
    boom_rate: float = 0
    bust_rate: float = 0

    # Correlation data
    game_total: float = 8.5
    team_total: float = 4.25
    opposing_pitcher_era: float = 4.00
    park_factor: float = 1.0
    weather_score: float = 1.0

    def __post_init__(self):
        # Set realistic ceiling/floor based on projection
        self.ceiling = self.projection * 1.8
        self.floor = max(0, self.projection * 0.4)
        self.boom_rate = 0.15 if self.projection > 10 else 0.08
        self.bust_rate = 0.10  # 10% chance of zero


class RealisticDFSSimulator:
    """
    Simulates ACTUAL DraftKings MLB DFS contests
    Based on real data where 1.3% win 91% of profits
    """

    def __init__(self, contest_size: int, slate_size: str = 'medium'):
        self.contest_size = contest_size
        self.slate_size = slate_size
        self.contest_type = self._determine_contest_type()
        self.field = []

    def _determine_contest_type(self) -> str:
        """Map contest size to type"""
        if self.contest_size <= 3:
            return '3-man'
        elif self.contest_size <= 5:
            return '5-man'
        elif self.contest_size <= 10:
            return '10-man'
        elif self.contest_size <= 20:
            return '20-man'
        elif self.contest_size <= 100:
            return '100-man'
        else:
            return '500+'

    def generate_realistic_field(self, slate_players: List[SimulatedPlayer]) -> List[Dict]:
        """
        Generate a field that matches ACTUAL DFS demographics
        96% of unique players submit 1-10 entries
        But they only represent 37% of total entries!
        """
        field = []
        dynamics = CONTEST_DYNAMICS[self.contest_type]

        # Calculate player distribution
        num_sharks = max(1, int(self.contest_size * dynamics['shark_percentage']))
        num_regular = int(self.contest_size * 0.20)  # 20% are regulars
        num_casual = self.contest_size - num_sharks - num_regular

        # Generate shark lineups (they multi-enter)
        entries_per_shark = min(150, max(20, self.contest_size // 10))
        for _ in range(num_sharks):
            # Sharks enter multiple correlated lineups
            shark_lineups = self._generate_shark_lineups(slate_players, entries_per_shark)
            field.extend(shark_lineups)

        # Generate regular player lineups
        for _ in range(num_regular):
            entries = random.randint(2, 10)
            for _ in range(entries):
                lineup = self._generate_regular_lineup(slate_players)
                field.append(lineup)

        # Generate casual lineups (1-2 entries each)
        for _ in range(num_casual):
            entries = random.randint(1, 2)
            for _ in range(entries):
                lineup = self._generate_casual_lineup(slate_players)
                field.append(lineup)

        # Trim to exact contest size
        random.shuffle(field)
        return field[:self.contest_size]

    def _generate_shark_lineup(self, players: List[SimulatedPlayer]) -> Dict:
        """
        Sharks know the meta:
        - 85% use proper stacks (but usually 4-man, not 5)
        - Target low ownership with correlation
        - Understand batting order matters
        """
        lineup = {'players': [], 'stack_pattern': None, 'total_salary': 0}

        # 85% of time, use a proper stack
        if random.random() < 0.85:
            # Choose stack size based on ACTUAL data
            stack_roll = random.random()
            if stack_roll < 0.60:  # 60% use 4-man stacks
                stack_size = 4
                pattern = '4-2-1-1'
            elif stack_roll < 0.85:  # 25% use 3-man stacks
                stack_size = 3
                pattern = '3-3-2'
            else:  # 15% use 5-man
                stack_size = 5
                pattern = '5-1-1-1'

            # Build stack with CONSECUTIVE batting order
            stack = self._build_consecutive_stack(players, stack_size)
            lineup['players'].extend(stack)
            lineup['stack_pattern'] = pattern
        else:
            # Game theory contrarian play
            lineup = self._build_contrarian_lineup(players)
            lineup['stack_pattern'] = 'contrarian'

        # Complete lineup respecting salary cap
        lineup = self._complete_lineup(lineup, players)
        return lineup

    def _generate_shark_lineups(self, players: List[SimulatedPlayer], num_entries: int) -> List[Dict]:
        """Sharks enter multiple CORRELATED lineups"""
        lineups = []

        # Pick a core (3-4 players they love)
        core_players = self._identify_sharp_core(players)

        for _ in range(num_entries):
            lineup = self._generate_shark_lineup(players)

            # 70% of their lineups include their core
            if random.random() < 0.70:
                lineup = self._integrate_core(lineup, core_players)

            lineups.append(lineup)

        return lineups

    def _generate_regular_lineup(self, players: List[SimulatedPlayer]) -> Dict:
        """
        Regular players:
        - Know stacking is good but execute poorly
        - Often use 2-3 man stacks instead of proper 4-5
        - Chase narratives and "hot" players
        """
        lineup = {'players': [], 'stack_pattern': None, 'total_salary': 0}

        # 40% use some stack (but usually too small)
        if random.random() < 0.40:
            stack_size = random.choices([2, 3, 4], weights=[0.6, 0.3, 0.1])[0]

            # They don't optimize for consecutive order
            stack = self._build_random_stack(players, stack_size)
            lineup['players'].extend(stack)
            lineup['stack_pattern'] = f'{stack_size}-man'

        # Fill rest with "good" players (high projection)
        lineup = self._complete_with_chalk(lineup, players)
        return lineup

    def _generate_casual_lineup(self, players: List[SimulatedPlayer]) -> Dict:
        """
        Casual players (80% of field):
        - Pick names they recognize
        - Try to spend all salary
        - No correlation strategy
        """
        lineup = {'players': [], 'stack_pattern': 'none', 'total_salary': 0}

        # Sort by "name value" (ownership * projection)
        popular = sorted(players, key=lambda p: p.ownership * p.projection, reverse=True)

        # Pick expensive pitcher they've heard of
        pitchers = [p for p in popular if p.position == 'P']
        if pitchers:
            lineup['players'].append(pitchers[0])

        # Fill with recognizable names, trying to use all salary
        lineup = self._complete_lineup_casual(lineup, players)
        return lineup

    def _build_consecutive_stack(self, players: List[SimulatedPlayer], size: int) -> List[SimulatedPlayer]:
        """Build a stack with CONSECUTIVE batting order (critical for correlation)"""

        # Group by team
        team_players = defaultdict(list)
        for p in players:
            if p.position != 'P' and p.batting_order > 0:
                team_players[p.team].append(p)

        # Find teams with enough consecutive batters
        valid_stacks = []
        for team, roster in team_players.items():
            roster.sort(key=lambda x: x.batting_order)

            # Look for consecutive windows
            for i in range(len(roster) - size + 1):
                window = roster[i:i + size]

                # Check if consecutive
                orders = [p.batting_order for p in window]
                if orders == list(range(orders[0], orders[0] + size)):
                    valid_stacks.append(window)

        if valid_stacks:
            # Sharks target correlation + low ownership
            stack_scores = []
            for stack in valid_stacks:
                avg_own = np.mean([p.ownership for p in stack])
                team_total = stack[0].team_total

                # Lower ownership is better, higher total is better
                score = (team_total / 5.0) * (1.0 / max(avg_own, 0.01))
                stack_scores.append((stack, score))

            # Pick from top options with some randomness
            stack_scores.sort(key=lambda x: x[1], reverse=True)
            top_stacks = stack_scores[:3]

            if top_stacks:
                return random.choice(top_stacks)[0]

        # Fallback to random team stack
        return self._build_random_stack(players, size)

    def _build_random_stack(self, players: List[SimulatedPlayer], size: int) -> List[SimulatedPlayer]:
        """Build a random team stack (what most players do)"""

        team_players = defaultdict(list)
        for p in players:
            if p.position != 'P':
                team_players[p.team].append(p)

        # Find teams with enough players
        valid_teams = [team for team, roster in team_players.items() if len(roster) >= size]

        if valid_teams:
            team = random.choice(valid_teams)
            roster = team_players[team]

            # Regular players just pick highest projected
            roster.sort(key=lambda x: x.projection, reverse=True)
            return roster[:size]

        return []

    def _build_contrarian_lineup(self, players: List[SimulatedPlayer]) -> Dict:
        """Shark game theory play - fade all chalk"""
        lineup = {'players': [], 'stack_pattern': 'contrarian', 'total_salary': 0}

        # Find low-owned, high-upside plays
        contrarian = [p for p in players if p.ownership < 0.05 and p.ceiling > 15]

        if len(contrarian) >= 8:
            # Build lineup from contrarian plays
            contrarian.sort(key=lambda x: x.ceiling / max(x.ownership, 0.001), reverse=True)

            # Take best low-owned plays
            lineup['players'] = contrarian[:8]

        return lineup

    def _identify_sharp_core(self, players: List[SimulatedPlayer]) -> List[SimulatedPlayer]:
        """Identify 3-4 players sharks will overweight"""

        # Sharks love: Low ownership + high correlation + good spot
        scores = []
        for p in players:
            if p.position != 'P':
                # Batting order 3-4 in high total game with low ownership
                if 3 <= p.batting_order <= 4 and p.team_total > 5:
                    score = (p.projection / max(p.ownership, 0.01)) * p.team_total
                    scores.append((p, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        core_size = random.randint(3, 4)

        return [p for p, _ in scores[:core_size]]

    def _complete_lineup(self, partial: Dict, players: List[SimulatedPlayer]) -> Dict:
        """Complete a lineup respecting salary and positions"""

        current = partial['players'].copy()
        remaining_salary = 50000 - sum(p.salary for p in current)

        # Position requirements
        needs = {
            'P': 2,
            'C': 1,
            '1B': 1,
            '2B': 1,
            '3B': 1,
            'SS': 1,
            'OF': 3
        }

        # Subtract what we have
        for p in current:
            if p.position in needs:
                needs[p.position] -= 1

        # Fill remaining spots
        available = [p for p in players if p not in current]
        available.sort(key=lambda x: x.projection / max(x.salary, 1), reverse=True)

        for p in available:
            if len(current) >= 10:
                break

            if p.position in needs and needs[p.position] > 0:
                if p.salary <= remaining_salary:
                    current.append(p)
                    needs[p.position] -= 1
                    remaining_salary -= p.salary

        return {
            'players': current[:10],
            'stack_pattern': partial.get('stack_pattern', 'unknown'),
            'total_salary': sum(p.salary for p in current[:10]),
            'is_valid': len(current) == 10
        }

    def _complete_with_chalk(self, partial: Dict, players: List[SimulatedPlayer]) -> Dict:
        """Regular players fill with obvious plays"""

        current = partial['players'].copy()
        remaining_salary = 50000 - sum(p.salary for p in current)

        # Just take highest ownership players that fit
        available = [p for p in players if p not in current]
        available.sort(key=lambda x: x.ownership, reverse=True)

        # Position requirements
        needs = self._get_position_needs(current)

        for p in available[:30]:  # Only look at top 30 by ownership
            if len(current) >= 10:
                break

            if p.position in needs and needs[p.position] > 0:
                if p.salary <= remaining_salary - 2000:  # Leave buffer
                    current.append(p)
                    needs[p.position] -= 1
                    remaining_salary -= p.salary

        return {
            'players': current[:10],
            'stack_pattern': partial.get('stack_pattern', 'chalk'),
            'total_salary': sum(p.salary for p in current[:10]),
            'is_valid': len(current) == 10
        }

    def _complete_lineup_casual(self, partial: Dict, players: List[SimulatedPlayer]) -> Dict:
        """Casual players obsess over using all salary"""

        current = partial['players'].copy()
        remaining_salary = 50000 - sum(p.salary for p in current)

        # Try to get to exactly $50,000
        available = [p for p in players if p not in current]

        # Sort by name recognition (high ownership)
        available.sort(key=lambda x: x.ownership, reverse=True)

        needs = self._get_position_needs(current)

        # Casual players often force expensive players to use salary
        for p in available:
            if len(current) >= 10:
                break

            if p.position in needs and needs[p.position] > 0:
                future_spots = 10 - len(current)
                avg_needed = remaining_salary / max(future_spots, 1)

                # Take if it helps reach $50k
                if abs(p.salary - avg_needed) < 2000:
                    current.append(p)
                    needs[p.position] -= 1
                    remaining_salary -= p.salary

        return {
            'players': current[:10],
            'stack_pattern': 'casual',
            'total_salary': sum(p.salary for p in current[:10]),
            'remaining': remaining_salary,
            'is_valid': len(current) == 10
        }

    def _get_position_needs(self, current: List[SimulatedPlayer]) -> Dict[str, int]:
        """Calculate remaining position needs"""
        needs = {
            'P': 2,
            'C': 1,
            '1B': 1,
            '2B': 1,
            '3B': 1,
            'SS': 1,
            'OF': 3
        }

        for p in current:
            if p.position in needs:
                needs[p.position] = max(0, needs[p.position] - 1)

        return needs

    def _integrate_core(self, lineup: Dict, core: List[SimulatedPlayer]) -> Dict:
        """Force core players into lineup"""

        # Remove conflicts and add core
        positions_in_core = [p.position for p in core]
        filtered = [p for p in lineup['players'] if p.position not in positions_in_core]

        new_lineup = core + filtered

        # Rebalance if needed
        if len(new_lineup) > 10:
            new_lineup = new_lineup[:10]

        lineup['players'] = new_lineup
        return lineup

    def simulate_scoring(self, lineups: List[Dict]) -> List[Tuple[Dict, float]]:
        """
        Apply REALISTIC variance and correlation
        MLB has highest variance of all DFS sports!
        """
        scored_lineups = []

        # Determine if this is a "chalk fail" slate (happens ~20% of time)
        chalk_fails = random.random() < 0.20

        for lineup in lineups:
            if not lineup.get('is_valid', True):
                score = 0
            else:
                score = self._score_lineup(lineup, chalk_fails)

            scored_lineups.append((lineup, score))

        # Sort by score
        scored_lineups.sort(key=lambda x: x[1], reverse=True)
        return scored_lineups

    def _score_lineup(self, lineup: Dict, chalk_fails: bool) -> float:
        """Score a lineup with realistic variance"""

        total_score = 0
        players = lineup.get('players', [])

        if len(players) != 10:
            return 0

        # Check for stacks to apply correlation
        team_groups = defaultdict(list)
        for p in players:
            if p.position != 'P':
                team_groups[p.team].append(p)

        # Find largest stack
        largest_stack = max(team_groups.values(), key=len) if team_groups else []
        stack_size = len(largest_stack)

        # Roll for stack correlation
        if stack_size >= 3:
            stack_outcome = random.random()

            if stack_outcome < 0.15:  # 15% BOOM
                stack_multiplier = random.uniform(1.5, 2.2)
            elif stack_outcome < 0.35:  # 20% good
                stack_multiplier = random.uniform(1.2, 1.4)
            elif stack_outcome < 0.70:  # 35% average
                stack_multiplier = random.uniform(0.9, 1.1)
            else:  # 30% bust
                stack_multiplier = random.uniform(0.4, 0.7)
        else:
            stack_multiplier = 1.0

        # Score each player
        for p in players:
            # Base score with variance
            if p.position == 'P':
                # Pitchers have higher variance
                variance = np.random.normal(0, MLB_VARIANCE['pitcher_std_dev'])

                # Disaster check
                if random.random() < MLB_VARIANCE['pitcher_disaster_rate']:
                    player_score = random.uniform(-5, 5)  # Negative possible!
                else:
                    player_score = p.projection + variance
            else:
                # Hitters
                # 10% chance of zero regardless of projection
                if random.random() < MLB_VARIANCE['zero_point_probability']:
                    player_score = 0
                else:
                    variance = np.random.normal(0, MLB_VARIANCE['hitter_std_dev'])
                    player_score = p.projection + variance

                    # Apply stack correlation if in largest stack
                    if p in largest_stack:
                        player_score *= stack_multiplier

                    # Apply chalk fail if high ownership
                    if chalk_fails and p.ownership > 0.20:
                        player_score *= random.uniform(0.5, 0.8)

            total_score += max(0, player_score)  # Can't go below 0

        return round(total_score, 2)

    def calculate_payouts(self, scored_lineups: List[Tuple[Dict, float]]) -> Dict:
        """Calculate realistic payouts based on DraftKings structure"""

        prize_pool = self.contest_size * 10 * (1 - CONTEST_DYNAMICS[self.contest_type]['rake'])

        # Payout structure based on contest size
        if self.contest_size <= 3:
            # Winner take all
            payouts = {1: prize_pool}
        elif self.contest_size <= 10:
            # Top 3 pay
            payouts = {
                1: prize_pool * 0.50,
                2: prize_pool * 0.30,
                3: prize_pool * 0.20
            }
        elif self.contest_size <= 100:
            # Top 20% pay, heavily weighted to top
            spots = max(1, self.contest_size // 5)
            payouts = self._generate_payout_structure(prize_pool, spots)
        else:
            # Large GPP - top 20% pay
            spots = self.contest_size // 5
            payouts = self._generate_payout_structure(prize_pool, spots)

        results = []
        for rank, (lineup, score) in enumerate(scored_lineups, 1):
            payout = payouts.get(rank, 0)
            roi = (payout - 10) / 10 * 100 if payout > 0 else -100

            results.append({
                'rank': rank,
                'lineup': lineup,
                'score': score,
                'payout': payout,
                'roi': roi,
                'pattern': lineup.get('stack_pattern', 'unknown')
            })

        return results

    def _generate_payout_structure(self, prize_pool: float, paying_spots: int) -> Dict[int, float]:
        """Generate realistic top-heavy payout structure"""

        payouts = {}

        if paying_spots <= 0:
            return {1: prize_pool}

        # First place gets ~10% of pool
        first_place = prize_pool * 0.10

        # Min cash is 1.5-2x buy-in
        min_cash = 15.0

        # Exponential decay from first to min cash
        remaining = prize_pool - first_place

        payouts[1] = first_place

        if paying_spots > 1:
            # Distribute remaining with exponential decay
            for pos in range(2, paying_spots + 1):
                # Exponential decay formula
                decay_rate = 0.7
                percentage = decay_rate ** (pos - 2)
                payout = max(min_cash, remaining * percentage / paying_spots)
                payouts[pos] = payout

        return payouts


# ==========================================
# SLATE GENERATION WITH REAL OWNERSHIP
# ==========================================

def generate_realistic_slate(num_players: int = 200, slate_size: str = 'medium') -> List[SimulatedPlayer]:
    """Generate a slate with realistic ownership patterns"""

    players = []
    player_id = 0

    # Generate pitchers
    for _ in range(20):
        # Ownership concentrates on few pitchers
        if player_id < 3:
            ownership = random.uniform(0.20, 0.35)  # Chalk pitchers
        elif player_id < 8:
            ownership = random.uniform(0.08, 0.15)  # Mid-tier
        else:
            ownership = random.uniform(0.01, 0.05)  # Low-owned

        pitcher = SimulatedPlayer(
            name=f"P{player_id}",
            position='P',
            team=f"TM{random.randint(1, 15)}",
            salary=random.randint(7000, 11000),
            projection=random.uniform(12, 22),
            ownership=ownership
        )
        players.append(pitcher)
        player_id += 1

    # Generate hitters by team
    teams = [f"TM{i}" for i in range(1, 16)]

    for team in teams:
        # Team implied total affects all players
        team_total = random.uniform(3.5, 6.5)

        # Generate batting order
        for batting_pos in range(1, 10):
            pos_options = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
            position = random.choice(pos_options)

            # Top of order has higher projection
            if batting_pos <= 4:
                base_proj = random.uniform(8, 12)
            else:
                base_proj = random.uniform(5, 9)

            # Ownership based on team total and batting order
            if team_total > 5.5 and batting_pos <= 4:
                ownership = random.uniform(0.08, 0.20)
            else:
                ownership = random.uniform(0.01, 0.08)

            # Stack ownership NEVER exceeds 1% (critical insight)
            if batting_pos > 1:
                ownership = min(ownership, 0.01)

            hitter = SimulatedPlayer(
                name=f"{team}_B{batting_pos}",
                position=position,
                team=team,
                salary=random.randint(3000, 6000),
                projection=base_proj,
                ownership=ownership,
                batting_order=batting_pos,
                team_total=team_total
            )
            players.append(hitter)
            player_id += 1

    return players


# ==========================================
# ANALYSIS FUNCTIONS
# ==========================================

def analyze_contest_results(results: List[Dict]) -> None:
    """Analyze contest to understand what won"""

    print("\n" + "=" * 60)
    print("CONTEST ANALYSIS")
    print("=" * 60)

    # Winner analysis
    winner = results[0]
    print(f"\n🏆 WINNER:")
    print(f"  Score: {winner['score']:.2f}")
    print(f"  Pattern: {winner['pattern']}")
    print(f"  ROI: {winner['roi']:.1f}%")

    # Pattern analysis
    pattern_performance = defaultdict(list)
    for r in results:
        pattern = r['pattern']
        pattern_performance[pattern].append(r['rank'])

    print("\n📊 PATTERN PERFORMANCE:")
    for pattern, ranks in pattern_performance.items():
        avg_rank = np.mean(ranks)
        top10_rate = sum(1 for r in ranks if r <= 10) / len(ranks) * 100
        print(f"  {pattern}: Avg rank {avg_rank:.1f}, Top 10: {top10_rate:.1f}%")

    # Stack analysis
    print("\n🔍 WHAT WON:")
    top10 = results[:10]
    stack_patterns = [r['pattern'] for r in top10]

    four_plus_stacks = sum(1 for p in stack_patterns if '4' in str(p) or '5' in str(p))
    print(f"  Top 10 with 4+ stacks: {four_plus_stacks}/10 ({four_plus_stacks * 10}%)")

    # Compare to expected 83% from research
    if four_plus_stacks >= 8:
        print("  ✅ Matches research: 80%+ of winners use 4-5 stacks")
    else:
        print(f"  ⚠️  Below research: Only {four_plus_stacks * 10}% vs expected 83%")


# ==========================================
# MAIN SIMULATION
# ==========================================

def run_realistic_simulation():
    """Run a complete realistic DFS simulation"""

    print("\n" + "=" * 60)
    print("REALISTIC DRAFTKINGS MLB DFS SIMULATION")
    print("Based on: 1.3% of players win 91% of profits")
    print("=" * 60)

    # Generate slate
    print("\n📋 Generating slate...")
    slate = generate_realistic_slate(200, 'medium')
    print(f"  Created {len(slate)} players")

    # Pick contest size
    contest_size = 100
    print(f"\n🎮 Simulating {contest_size}-player contest")

    # Create simulator
    sim = RealisticDFSSimulator(contest_size, 'medium')

    # Generate field
    print("\n👥 Generating realistic field...")
    field = sim.generate_realistic_field(slate)
    print(f"  Generated {len(field)} lineups")

    # Count patterns
    patterns = defaultdict(int)
    for lineup in field:
        patterns[lineup.get('stack_pattern', 'unknown')] += 1

    print("\n📊 Field composition:")
    for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(field) * 100
        print(f"  {pattern}: {count} ({pct:.1f}%)")

    # Simulate scoring
    print("\n🎲 Simulating contest...")
    scored = sim.simulate_scoring(field)

    # Calculate payouts
    results = sim.calculate_payouts(scored)

    # Analyze
    analyze_contest_results(results)

    # Show top 5
    print("\n🏅 TOP 5 LINEUPS:")
    for r in results[:5]:
        print(f"  #{r['rank']}: {r['score']:.2f} pts, "
              f"Pattern: {r['pattern']}, Payout: ${r['payout']:.2f}")

    return results


if __name__ == "__main__":
    # Run simulation
    results = run_realistic_simulation()

    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("This reflects ACTUAL DFS dynamics where:")
    print("• 1.3% of players win 91% of profits")
    print("• Most players don't stack properly")
    print("• Variance is extreme (10% zero rate for hitters)")
    print("• Ownership rarely exceeds 1% for stacks")
    print("=" * 60)