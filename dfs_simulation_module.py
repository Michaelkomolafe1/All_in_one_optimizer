#!/usr/bin/env python3
"""
REALISTIC MLB DFS VALIDATION
============================
Honest simulation without data manipulation - let the results speak for themselves
"""

import random
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import json
from datetime import datetime
import statistics
from collections import defaultdict


@dataclass
class Player:
    """MLB DFS Player"""
    name: str
    position: str
    team: str
    salary: int
    dk_projection: float
    batting_order: int
    opponent: str
    game_id: str

    def __hash__(self):
        return hash(self.name)


@dataclass
class Game:
    """Game environment"""
    game_id: str
    home_team: str
    away_team: str
    total_runs: float

    def get_team_total(self, team: str) -> float:
        # Home teams typically get 52% of total
        if team == self.home_team:
            return self.total_runs * 0.52
        return self.total_runs * 0.48


class ScoringMethod:
    """Base scoring method"""

    def __init__(self, name: str):
        self.name = name

    def score_player(self, player: Player, team_total: float) -> float:
        """Override in subclasses"""
        return player.dk_projection


class CorrelationAwareScoring(ScoringMethod):
    def score_player(self, player: Player, team_total: float) -> float:
        score = player.dk_projection

        # Team total boost
        if team_total > 5.0:
            score *= 1.15

        # Batting order boost
        if player.position != 'P' and player.batting_order <= 4:
            score *= 1.10

        return score


class DKOnlyScoring(ScoringMethod):
    def score_player(self, player: Player, team_total: float) -> float:
        return player.dk_projection


class WeatherAdjustedScoring(ScoringMethod):
    def score_player(self, player: Player, team_total: float) -> float:
        # Simplified - just add small random weather factor
        weather_factor = random.uniform(0.95, 1.05)
        return player.dk_projection * weather_factor


class EnhancedPureScoring(ScoringMethod):
    def score_player(self, player: Player, team_total: float) -> float:
        # Weighted combination
        base = player.dk_projection * 0.4
        vegas = team_total * 2.0 * 0.3
        order_bonus = (10 - player.batting_order) * 0.5 * 0.3 if player.position != 'P' else 0

        return base + vegas + order_bonus


class BaseballOptimizedScoring(ScoringMethod):
    def score_player(self, player: Player, team_total: float) -> float:
        score = player.dk_projection

        # Batting order specific boosts
        if player.position != 'P':
            order_boosts = {1: 1.08, 2: 1.06, 3: 1.12, 4: 1.10, 5: 1.05}
            score *= order_boosts.get(player.batting_order, 1.0)

        return score


class BayesianScoring(ScoringMethod):
    def score_player(self, player: Player, team_total: float) -> float:
        # Simple Bayesian - blend with league average
        league_avg = 8.5 if player.position != 'P' else 15.0
        weight = 0.7
        return (player.dk_projection * weight) + (league_avg * (1 - weight))


class HybridSmartScoring(ScoringMethod):
    def score_player(self, player: Player, team_total: float) -> float:
        base = player.dk_projection
        vegas_factor = team_total / 5.0
        return base * (0.6 + 0.4 * vegas_factor)


class DynamicScoring(ScoringMethod):
    def score_player(self, player: Player, team_total: float) -> float:
        # Simulate missing data by randomly excluding components
        components = []
        if random.random() > 0.1:  # 90% have base
            components.append(player.dk_projection)
        if random.random() > 0.2:  # 80% have vegas
            components.append(team_total * 2)

        return sum(components) / len(components) if components else player.dk_projection


class PureDataScoring(ScoringMethod):
    def score_player(self, player: Player, team_total: float) -> float:
        score = player.dk_projection

        # Only objective boosts
        if player.batting_order <= 3:
            score *= 1.05
        if team_total > 9:
            score *= 1.03

        return score


class AdvancedStackScoring(ScoringMethod):
    def score_player(self, player: Player, team_total: float) -> float:
        score = player.dk_projection

        # Heavy team total emphasis
        if team_total > 5.5:
            score *= 1.20
        elif team_total > 4.5:
            score *= 1.10

        return score


class RecencyWeightedScoring(ScoringMethod):
    def score_player(self, player: Player, team_total: float) -> float:
        # Simulate recent form
        recent_mult = random.uniform(0.8, 1.2)
        return player.dk_projection * (0.4 + 0.6 * recent_mult)


class SeasonLongScoring(ScoringMethod):
    def score_player(self, player: Player, team_total: float) -> float:
        # Less variance, more consistency
        return player.dk_projection * random.uniform(0.95, 1.05)


class RealisticMLBSimulation:
    """Realistic simulation without manipulation"""

    def __init__(self, verbose_debug=False):
        self.verbose_debug = verbose_debug
        self.scoring_methods = {
            'correlation_aware': CorrelationAwareScoring('correlation_aware'),
            'dk_only': DKOnlyScoring('dk_only'),
            'weather_adjusted': WeatherAdjustedScoring('weather_adjusted'),
            'enhanced_pure': EnhancedPureScoring('enhanced_pure'),
            'baseball_optimized': BaseballOptimizedScoring('baseball_optimized'),
            'bayesian': BayesianScoring('bayesian'),
            'hybrid_smart': HybridSmartScoring('hybrid_smart'),
            'dynamic': DynamicScoring('dynamic'),
            'pure_data': PureDataScoring('pure_data'),
            'advanced_stack': AdvancedStackScoring('advanced_stack'),
            'recency_weighted': RecencyWeightedScoring('recency_weighted'),
            'season_long': SeasonLongScoring('season_long')
        }

        self.results = defaultdict(list)
        self.lineup_stats = defaultdict(list)

    def generate_slate(self, num_games: int = 8) -> Tuple[List[Player], Dict[str, Game]]:
        """Generate a realistic slate"""
        players = []
        games = {}

        for i in range(num_games):
            home = f"TM{i * 2}"
            away = f"TM{i * 2 + 1}"

            # Realistic game totals (most games 7-10 runs)
            total = random.gauss(8.5, 1.0)
            total = max(6.5, min(11.5, total))

            game = Game(
                game_id=f"G{i}",
                home_team=home,
                away_team=away,
                total_runs=total
            )
            games[game.game_id] = game

            # Create players for both teams
            for team in [home, away]:
                opp = away if team == home else home

                # 2-3 pitchers per team to ensure enough options
                num_pitchers = random.randint(2, 3)
                for _ in range(num_pitchers):
                    proj = random.gauss(15.0, 3.0)
                    proj = max(5, min(25, proj))
                    salary = int(5500 + (proj - 12) * 300)

                    players.append(Player(
                        name=f"P_{team}_{random.randint(100, 999)}",
                        position='P',
                        team=team,
                        salary=max(5000, min(11500, salary)),
                        dk_projection=proj,
                        batting_order=0,
                        opponent=opp,
                        game_id=game.game_id
                    ))

                # 9 hitters (ensure all positions are covered)
                for order in range(1, 10):
                    # Base projection by batting order
                    base_by_order = {
                        1: 9.0, 2: 8.8, 3: 9.5, 4: 9.3, 5: 8.5,
                        6: 7.8, 7: 7.3, 8: 6.8, 9: 6.5
                    }
                    base = base_by_order.get(order, 7.0)
                    proj = random.gauss(base, 1.5)
                    proj = max(2, min(15, proj))

                    # Position by typical batting order
                    pos_options = {
                        1: ['SS', '2B', 'OF'],
                        2: ['SS', '2B', 'OF'],
                        3: ['1B', 'OF'],
                        4: ['1B', 'OF', '3B'],
                        5: ['3B', 'OF', '1B'],
                        6: ['OF', 'C'],
                        7: ['2B', 'SS', 'OF'],
                        8: ['C', 'SS'],
                        9: ['SS', '2B', 'C']
                    }
                    position = random.choice(pos_options.get(order, ['OF']))

                    # Salary based on projection
                    salary = int(3000 + proj * 300)

                    players.append(Player(
                        name=f"{position}_{team}_{order}",
                        position=position,
                        team=team,
                        salary=max(2500, min(6000, salary)),
                        dk_projection=proj,
                        batting_order=order,
                        opponent=opp,
                        game_id=game.game_id
                    ))

        return players, games

    def simulate_actual_scores(self, players: List[Player], games: Dict[str, Game]) -> Dict[str, float]:
        """Simulate actual scores with realistic variance"""
        actual_scores = {}

        # Determine which teams exceed expectations
        team_performances = {}
        for game in games.values():
            # 20% chance one team goes off
            if random.random() < 0.2:
                if random.random() < 0.5:
                    team_performances[game.home_team] = random.uniform(1.2, 1.5)
                    team_performances[game.away_team] = random.uniform(0.7, 0.9)
                else:
                    team_performances[game.away_team] = random.uniform(1.2, 1.5)
                    team_performances[game.home_team] = random.uniform(0.7, 0.9)
            else:
                # Normal variance
                team_performances[game.home_team] = random.gauss(1.0, 0.15)
                team_performances[game.away_team] = random.gauss(1.0, 0.15)

        # Generate individual scores
        for player in players:
            # Base variance
            individual_var = random.gauss(1.0, 0.25)

            # Team factor
            team_factor = team_performances.get(player.team, 1.0)

            # Position-specific variance
            if player.position == 'P':
                # Pitchers have different variance pattern
                actual = player.dk_projection * individual_var
                # If opposing team is hot, pitcher suffers
                opp_factor = team_performances.get(player.opponent, 1.0)
                if opp_factor > 1.2:
                    actual *= 0.8
            else:
                # Hitters correlate with team
                actual = player.dk_projection * individual_var * team_factor

                # Batting order correlation (slight)
                if player.batting_order <= 5:
                    actual *= random.uniform(0.95, 1.05)

                # Occasional big game
                if random.random() < 0.03:  # 3% chance
                    actual *= random.uniform(1.8, 2.5)

            actual_scores[player.name] = max(0, actual)

        return actual_scores

    def build_lineup(self, players: List[Player], scoring_method: ScoringMethod,
                     games: Dict[str, Game]) -> List[Player]:
        """Build optimal lineup for scoring method with flexible fallback"""
        # Score all players
        scored_players = []
        for player in players:
            team_total = games[player.game_id].get_team_total(player.team)
            score = scoring_method.score_player(player, team_total)
            value = score / (player.salary / 1000)
            scored_players.append((value, player))

        # Sort by value (first element of tuple)
        scored_players.sort(key=lambda x: x[0], reverse=True)

        # Try multiple approaches
        lineup = self._try_value_based_lineup(scored_players)

        if not lineup:
            lineup = self._try_position_first_lineup(players, scored_players)

        if not lineup:
            lineup = self._try_relaxed_lineup(players, scored_players)

        return lineup

    def _try_value_based_lineup(self, scored_players):
        """Standard value-based approach"""
        lineup = []
        salary_used = 0
        salary_cap = 50000
        positions_filled = defaultdict(int)
        position_limits = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        for value, player in scored_players:
            if positions_filled[player.position] >= position_limits.get(player.position, 0):
                continue

            if salary_used + player.salary > salary_cap:
                continue

            lineup.append(player)
            salary_used += player.salary
            positions_filled[player.position] += 1

            if len(lineup) >= 10:
                break

        if len(lineup) == 10:
            return lineup
        return None

    def _try_position_first_lineup(self, all_players, scored_players):
        """Fill required positions first, then optimize"""
        lineup = []
        salary_used = 0
        salary_cap = 50000
        position_limits = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        used_players = set()

        # Sort all players by position and salary
        players_by_pos = defaultdict(list)
        for _, player in scored_players:
            players_by_pos[player.position].append(player)

        # Fill each position with cheapest acceptable player
        for pos, limit in position_limits.items():
            # Sort by salary for this position
            pos_players = sorted(players_by_pos[pos], key=lambda p: p.salary)

            added = 0
            for player in pos_players:
                if player not in used_players and salary_used + player.salary <= salary_cap - 3000:
                    lineup.append(player)
                    salary_used += player.salary
                    used_players.add(player)
                    added += 1

                    if added >= limit:
                        break

        # If we got all 10 players and are under cap, success
        if len(lineup) == 10 and salary_used <= salary_cap:
            return lineup
        return None

    def _try_relaxed_lineup(self, all_players, scored_players):
        """Very relaxed approach - just get 10 valid players"""
        lineup = []
        salary_used = 0
        salary_cap = 50000
        positions_filled = defaultdict(int)
        position_limits = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        # Group by position and sort by salary
        by_position = defaultdict(list)
        for _, player in scored_players:
            by_position[player.position].append(player)

        # Sort each position by salary
        for pos in by_position:
            by_position[pos].sort(key=lambda p: p.salary)

        # Try to fill minimum requirements with cheapest players
        for pos, limit in position_limits.items():
            players_at_pos = by_position[pos]

            for player in players_at_pos[:limit * 2]:  # Look at more options
                if positions_filled[pos] >= limit:
                    break

                # More relaxed salary check - fill positions first
                if player not in lineup:
                    lineup.append(player)
                    salary_used += player.salary
                    positions_filled[pos] += 1

        # Adjust if over budget by swapping expensive players
        while salary_used > salary_cap and lineup:
            # Find most expensive player
            lineup.sort(key=lambda p: p.salary, reverse=True)
            removed = lineup.pop(0)
            salary_used -= removed.salary
            positions_filled[removed.position] -= 1

            # Try to find cheaper replacement
            for _, player in scored_players:
                if (player.position == removed.position and
                        player not in lineup and
                        player.salary < removed.salary and
                        salary_used + player.salary <= salary_cap):
                    lineup.append(player)
                    salary_used += player.salary
                    positions_filled[player.position] += 1
                    break

        if len(lineup) == 10 and salary_used <= salary_cap:
            if self.verbose_debug:
                print(f"   ✅ Built lineup using relaxed approach")
            return lineup

        if self.verbose_debug:
            positions_needed = []
            for pos, limit in position_limits.items():
                current = sum(1 for p in lineup if p.position == pos)
                if current < limit:
                    positions_needed.extend([pos] * (limit - current))

            print(f"   Failed to build lineup: only {len(lineup)} players")
            print(f"   Missing positions: {positions_needed}")
            print(f"   Salary used: ${salary_used} (cap: ${salary_cap})")

        return None

    def calculate_lineup_score(self, lineup: List[Player], actual_scores: Dict[str, float]) -> float:
        """Calculate actual lineup score with stacking bonus"""
        if not lineup:
            return 0

        base_score = sum(actual_scores.get(p.name, 0) for p in lineup)

        # Calculate stacking bonus
        team_counts = defaultdict(int)
        for p in lineup:
            if p.position != 'P':
                team_counts[p.team] += 1

        max_stack = max(team_counts.values()) if team_counts else 0

        # Apply realistic stacking bonus
        if max_stack >= 5:
            base_score *= 1.10  # 10% bonus
        elif max_stack >= 4:
            base_score *= 1.06  # 6% bonus
        elif max_stack >= 3:
            base_score *= 1.03  # 3% bonus

        return base_score

    def run_simulation(self, num_iterations: int = 1000):
        """Run the simulation"""
        print("\n" + "=" * 60)
        print("🏆 REALISTIC MLB DFS VALIDATION")
        print("=" * 60)
        print(f"Running {num_iterations} iterations...")
        print("No data manipulation - just realistic modeling\n")

        valid_lineups = defaultdict(int)
        failed_attempts = defaultdict(int)

        for i in range(num_iterations):
            if i % 100 == 0:
                print(f"Progress: {i}/{num_iterations}")

            # Generate slate
            players, games = self.generate_slate()  # Back to default 8 gamesduced from 8

            # Debug first iteration
            if i == 0 and self.verbose_debug:
                print(f"\nDebug - First slate:")
                print(f"  Total players: {len(players)}")
                pos_counts = defaultdict(int)
                team_counts = defaultdict(int)
                for p in players:
                    pos_counts[p.position] += 1
                    team_counts[p.team] += 1
                print(f"  Position counts: {dict(pos_counts)}")
                print(f"  Teams: {len(team_counts)} teams")
                print(f"  Avg players per team: {len(players) / len(team_counts):.1f}")
                print(f"  Games: {len(games)}")

                # Show salary distribution
                salaries_by_pos = defaultdict(list)
                for p in players:
                    salaries_by_pos[p.position].append(p.salary)
                print(f"\n  Average salaries by position:")
                for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
                    if salaries_by_pos[pos]:
                        avg_sal = sum(salaries_by_pos[pos]) / len(salaries_by_pos[pos])
                        print(f"    {pos}: ${avg_sal:.0f} ({len(salaries_by_pos[pos])} players)")

            # Simulate actual scores
            actual_scores = self.simulate_actual_scores(players, games)

            # Test each method
            for method_name, method in self.scoring_methods.items():
                lineup = self.build_lineup(players, method, games)

                if lineup:
                    valid_lineups[method_name] += 1
                    score = self.calculate_lineup_score(lineup, actual_scores)
                    self.results[method_name].append(score)

                    # Track stacking
                    team_counts = defaultdict(int)
                    for p in lineup:
                        if p.position != 'P':
                            team_counts[p.team] += 1

                    max_stack = max(team_counts.values()) if team_counts else 0
                    self.lineup_stats[method_name].append({
                        'max_stack': max_stack,
                        'num_teams': len(team_counts)
                    })
                else:
                    failed_attempts[method_name] += 1

        print(f"\n✅ Valid lineups built:")
        for method, count in sorted(valid_lineups.items()):
            success_rate = (count / num_iterations) * 100
            print(f"  {method}: {count}/{num_iterations} ({success_rate:.1f}%)")

        if failed_attempts:
            print(f"\n❌ Failed attempts:")
            for method, count in sorted(failed_attempts.items()):
                print(f"  {method}: {count}")

        return valid_lineups

    def print_results(self):
        """Print results"""
        print("\n" + "=" * 60)
        print("📊 SIMULATION RESULTS")
        print("=" * 60)

        summaries = []
        for method in self.scoring_methods:
            scores = self.results.get(method, [])
            stats = self.lineup_stats.get(method, [])

            if len(scores) >= 10:  # Only include if we have enough data
                avg_stack = statistics.mean(s['max_stack'] for s in stats) if stats else 0
                pct_3plus = sum(1 for s in stats if s['max_stack'] >= 3) / len(stats) * 100 if stats else 0
                pct_4plus = sum(1 for s in stats if s['max_stack'] >= 4) / len(stats) * 100 if stats else 0

                summaries.append({
                    'method': method,
                    'avg_score': statistics.mean(scores),
                    'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
                    'median': statistics.median(scores),
                    'p90': np.percentile(scores, 90),
                    'max': max(scores),
                    'min': min(scores),
                    'avg_stack': avg_stack,
                    'pct_3plus': pct_3plus,
                    'pct_4plus': pct_4plus,
                    'lineups': len(scores)
                })

        if not summaries:
            print("❌ No valid results to display")
            return

        # Sort by average score
        summaries.sort(key=lambda x: x['avg_score'], reverse=True)

        print("\n📈 Rankings by Average Score:")
        print("-" * 90)
        print(f"{'Rank':<6}{'Method':<20}{'Avg':<10}{'StdDev':<10}{'P90':<10}{'Stack':<10}{'4+Stack%':<10}")
        print("-" * 90)

        for i, s in enumerate(summaries, 1):
            print(f"{i:<6}{s['method']:<20}{s['avg_score']:<10.1f}{s['std_dev']:<10.1f}"
                  f"{s['p90']:<10.1f}{s['avg_stack']:<10.2f}{s['pct_4plus']:<10.1f}%")

        # Additional insights
        print("\n\n💡 Key Insights:")
        print("-" * 60)

        if summaries:
            winner = summaries[0]
            loser = summaries[-1]

            print(f"Winner: {winner['method']} ({winner['avg_score']:.1f} avg)")
            print(f"Loser: {loser['method']} ({loser['avg_score']:.1f} avg)")
            print(f"Range: {winner['avg_score'] - loser['avg_score']:.1f} points")

            # Find correlation_aware
            corr_aware = next((s for s in summaries if s['method'] == 'correlation_aware'), None)
            if corr_aware:
                rank = next(i for i, s in enumerate(summaries, 1) if s['method'] == 'correlation_aware')
                print(f"\ncorrelation_aware rank: #{rank}")
                print(f"  Score: {corr_aware['avg_score']:.1f}")
                print(f"  4+ stacks: {corr_aware['pct_4plus']:.1f}%")

        # Score distribution
        print("\n\n📊 Score Distribution:")
        print("-" * 60)
        all_scores = []
        for scores in self.results.values():
            all_scores.extend(scores)

        if all_scores:
            print(f"Overall range: {min(all_scores):.1f} - {max(all_scores):.1f}")
            print(f"Overall average: {statistics.mean(all_scores):.1f}")
            print(f"Overall P90: {np.percentile(all_scores, 90):.1f}")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"realistic_validation_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'summary': summaries,
                'parameters': {
                    'stacking_bonus': {'3-stack': '3%', '4-stack': '6%', '5-stack': '10%'},
                    'team_variance': '±15%',
                    'individual_variance': '±25%',
                    'big_game_chance': '3%'
                }
            }, f, indent=2)

        print(f"\n💾 Results saved to: {filename}")


def main():
    sim = RealisticMLBSimulation(verbose_debug=False)  # Turn off verbose for cleaner output
    sim.run_simulation(100)  # Back to 100 iterations
    sim.print_results()


if __name__ == "__main__":
    main()