#!/usr/bin/env python3
"""
Comprehensive DFS Scoring Strategy Simulation
Tests Pure Data vs Dynamic vs DK-only vs Hybrid approaches
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from collections import defaultdict
from dataclasses import dataclass
import warnings

warnings.filterwarnings('ignore')


@dataclass
class Player:
    """Represents a DFS player with all attributes"""
    name: str
    position: str
    salary: int
    team: str
    opponent: str
    dk_projection: float
    true_skill: float
    has_vegas: bool
    has_recent: bool
    has_matchup: bool
    has_batting_order: bool
    has_statcast: bool
    is_pitcher: bool
    park_factor: float
    weather_score: float

    def __hash__(self):
        """Make Player hashable using name"""
        return hash(self.name)

    def __eq__(self, other):
        """Compare players by name"""
        if isinstance(other, Player):
            return self.name == other.name
        return False

    @property
    def data_completeness(self) -> float:
        """Percentage of data available"""
        data_points = [self.has_vegas, self.has_recent, self.has_matchup,
                       self.has_batting_order, self.has_statcast]
        return sum(data_points) / len(data_points)


class DFSSimulator:
    """Advanced DFS simulation with realistic constraints"""

    def __init__(self):
        self.positions = {
            'P': {'count': 2, 'pool_size': 40},
            'C': {'count': 1, 'pool_size': 24},
            '1B': {'count': 1, 'pool_size': 24},
            '2B': {'count': 1, 'pool_size': 24},
            '3B': {'count': 1, 'pool_size': 24},
            'SS': {'count': 1, 'pool_size': 24},
            'OF': {'count': 3, 'pool_size': 60}
        }
        self.salary_cap = 50000
        self.scoring_systems = {
            'pure_data': self.score_pure_data,
            'dynamic': self.score_dynamic,
            'dk_only': self.score_dk_only,
            'hybrid_smart': self.score_hybrid_smart,
            'enhanced_pure': self.score_enhanced_pure
        }

    def generate_realistic_slate(self, slate_size: str = 'main') -> List[Player]:
        """Generate a realistic DFS slate with various player types"""
        np.random.seed(None)  # Random seed for variety

        # Slate sizes
        slate_configs = {
            'showdown': {'games': 1, 'player_mult': 0.5},
            'small': {'games': 2, 'player_mult': 0.7},
            'medium': {'games': 5, 'player_mult': 1.0},
            'main': {'games': 10, 'player_mult': 1.2},
            'large': {'games': 15, 'player_mult': 1.5}
        }

        config = slate_configs[slate_size]
        players = []
        player_id = 0

        # Generate teams and matchups
        teams = [f"T{i}" for i in range(config['games'] * 2)]
        matchups = [(teams[i], teams[i + 1]) for i in range(0, len(teams), 2)]

        for position, info in self.positions.items():
            pool_size = int(info['pool_size'] * config['player_mult'])

            for _ in range(pool_size):
                # Player characteristics
                team_idx = np.random.randint(len(teams))
                team = teams[team_idx]
                opponent = teams[team_idx + 1] if team_idx % 2 == 0 else teams[team_idx - 1]

                # Skill distribution (some stars, mostly average, some punts)
                skill_roll = np.random.random()
                if skill_roll < 0.15:  # 15% stars
                    true_skill = np.random.normal(1.5, 0.2)
                    salary = np.random.choice(range(8000, 10100, 100))
                elif skill_roll < 0.30:  # 15% punt plays
                    true_skill = np.random.normal(0.7, 0.2)
                    salary = np.random.choice(range(3000, 5100, 100))
                else:  # 70% mid-range
                    true_skill = np.random.normal(1.0, 0.25)
                    salary = np.random.choice(range(5000, 8100, 100))

                # DK projection (correlated with skill but with noise)
                projection_accuracy = np.random.normal(1.0, 0.15)
                dk_projection = max(0, (salary / 1000) * true_skill * projection_accuracy)

                # Data availability (varies by player tier)
                if salary >= 8000:  # Premium players have more data
                    data_prob = 0.9
                elif salary >= 6000:  # Mid-tier decent data
                    data_prob = 0.7
                else:  # Value plays often missing data
                    data_prob = 0.5

                # Environmental factors
                park_factor = np.random.normal(1.0, 0.1)
                weather_score = np.random.normal(1.0, 0.15)

                player = Player(
                    name=f"{position}{player_id}",
                    position=position,
                    salary=salary,
                    team=team,
                    opponent=opponent,
                    dk_projection=dk_projection,
                    true_skill=true_skill,
                    has_vegas=np.random.random() < data_prob,
                    has_recent=np.random.random() < (data_prob + 0.1),
                    has_matchup=np.random.random() < (data_prob - 0.1),
                    has_batting_order=np.random.random() < (data_prob - 0.2) if position != 'P' else False,
                    has_statcast=np.random.random() < data_prob,
                    is_pitcher=position == 'P',
                    park_factor=park_factor,
                    weather_score=weather_score
                )

                players.append(player)
                player_id += 1

        return players

    def score_pure_data(self, player: Player) -> float:
        """Pure data scoring - fixed weights, no redistribution"""
        if player.dk_projection <= 0:
            return 0

        score = player.dk_projection * 0.35  # Base weight

        # Add components only if data exists
        if player.has_vegas:
            vegas_mult = np.random.normal(1.05, 0.1)
            score += player.dk_projection * 0.20 * vegas_mult

        if player.has_recent:
            recent_mult = np.random.normal(1.0, 0.15)
            score += player.dk_projection * 0.25 * recent_mult

        if player.has_matchup:
            matchup_mult = np.random.normal(1.0, 0.1)
            score += player.dk_projection * 0.15 * matchup_mult

        if player.has_batting_order and not player.is_pitcher:
            order_mult = np.random.normal(1.02, 0.05)
            score += player.dk_projection * 0.05 * order_mult

        return max(0, score)

    def score_dynamic(self, player: Player) -> float:
        """Dynamic scoring - redistributes weights when data missing"""
        if player.dk_projection <= 0:
            return 0

        # Calculate active weights
        weights = {
            'base': 0.35,
            'vegas': 0.20 if player.has_vegas else 0,
            'recent': 0.25 if player.has_recent else 0,
            'matchup': 0.15 if player.has_matchup else 0,
            'order': 0.05 if (player.has_batting_order and not player.is_pitcher) else 0
        }

        # Redistribute weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            normalized = {k: v / total_weight for k, v in weights.items()}
        else:
            return 0

        # Calculate score
        score = player.dk_projection * normalized['base']

        if player.has_vegas:
            vegas_mult = np.random.normal(1.05, 0.1)
            score += player.dk_projection * normalized['vegas'] * vegas_mult

        if player.has_recent:
            recent_mult = np.random.normal(1.0, 0.15)
            score += player.dk_projection * normalized['recent'] * recent_mult

        if player.has_matchup:
            matchup_mult = np.random.normal(1.0, 0.1)
            score += player.dk_projection * normalized['matchup'] * matchup_mult

        if player.has_batting_order and not player.is_pitcher:
            order_mult = np.random.normal(1.02, 0.05)
            score += player.dk_projection * normalized['order'] * order_mult

        return max(0, score)

    def score_dk_only(self, player: Player) -> float:
        """DK projections only"""
        return player.dk_projection

    def score_hybrid_smart(self, player: Player) -> float:
        """Smart hybrid - uses pure for complete data, dynamic for incomplete"""
        if player.data_completeness >= 0.8:  # 80%+ data available
            return self.score_pure_data(player)
        else:
            return self.score_dynamic(player)

    def score_enhanced_pure(self, player: Player) -> float:
        """Enhanced pure data - adds environmental factors"""
        base_score = self.score_pure_data(player)

        # Apply park and weather factors
        environmental_mult = (player.park_factor * 0.7 + player.weather_score * 0.3)

        return base_score * environmental_mult

    def optimize_lineup(self, players: List[Player], scoring_method: str) -> Dict:
        """Optimize lineup with position constraints"""
        score_func = self.scoring_systems[scoring_method]

        # Calculate scores
        for player in players:
            player.optimization_score = score_func(player)
            player.value = player.optimization_score / (player.salary / 1000)

        # Group by position
        by_position = defaultdict(list)
        for player in players:
            by_position[player.position].append(player)

        # Sort each position by value
        for pos in by_position:
            by_position[pos].sort(key=lambda p: p.value, reverse=True)

        # Build lineup greedily with position constraints
        lineup = []
        used_players = set()
        total_salary = 0

        # Fill required positions
        position_needs = {
            'P': 2, 'C': 1, '1B': 1, '2B': 1,
            '3B': 1, 'SS': 1, 'OF': 3
        }

        iterations = 0
        max_iterations = 100

        while len(lineup) < 10 and iterations < max_iterations:
            iterations += 1
            best_player = None
            best_value = -1

            for pos, needed in position_needs.items():
                if needed > 0:
                    for player in by_position[pos]:
                        if (player not in used_players and
                                total_salary + player.salary <= self.salary_cap - (9 - len(lineup)) * 3000):
                            if player.value > best_value:
                                best_value = player.value
                                best_player = player

            if best_player:
                lineup.append(best_player)
                used_players.add(best_player)
                total_salary += best_player.salary
                position_needs[best_player.position] -= 1
            else:
                break

        # Calculate actual points
        if len(lineup) == 10:
            actual_points = sum(self.calculate_actual_points(p) for p in lineup)
            projected_points = sum(p.optimization_score for p in lineup)

            return {
                'valid': True,
                'lineup': lineup,
                'total_salary': total_salary,
                'projected_points': projected_points,
                'actual_points': actual_points,
                'avg_data_completeness': np.mean([p.data_completeness for p in lineup])
            }
        else:
            return {'valid': False}

    def calculate_actual_points(self, player: Player) -> float:
        """Simulate actual performance based on true skill"""
        base_performance = (player.salary / 1000) * player.true_skill

        # Add variance
        game_variance = np.random.normal(1.0, 0.25)

        # Environmental impact
        env_impact = (player.park_factor * 0.3 + player.weather_score * 0.2) * 0.5 + 0.5

        actual = base_performance * game_variance * env_impact

        # Pitcher variance is higher
        if player.is_pitcher:
            actual *= np.random.normal(1.0, 0.3)

        return max(0, actual)

    def run_comprehensive_test(self, num_simulations: int = 1000):
        """Run comprehensive testing across all scenarios"""
        results = defaultdict(lambda: defaultdict(list))

        print("🚀 RUNNING COMPREHENSIVE DFS SCORING SIMULATION")
        print("=" * 60)
        print(f"Testing {len(self.scoring_systems)} scoring methods")
        print(f"Running {num_simulations} simulations")
        print("=" * 60)

        slate_types = ['small', 'medium', 'main', 'large']

        for slate_type in slate_types:
            print(f"\n📊 Testing {slate_type.upper()} slates...")

            for sim in range(num_simulations // len(slate_types)):
                # Generate slate
                players = self.generate_realistic_slate(slate_type)

                # Test each scoring method
                for method_name in self.scoring_systems:
                    result = self.optimize_lineup(players, method_name)

                    if result['valid']:
                        results[slate_type][method_name].append({
                            'actual': result['actual_points'],
                            'projected': result['projected_points'],
                            'salary': result['total_salary'],
                            'data_completeness': result['avg_data_completeness']
                        })

        return results

    def analyze_results(self, results: Dict) -> Dict:
        """Analyze results and provide recommendations"""
        analysis = {}

        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE RESULTS ANALYSIS")
        print("=" * 60)

        # Overall performance
        print("\n🏆 OVERALL PERFORMANCE (All Slates)")
        print("-" * 60)

        overall_scores = defaultdict(list)
        for slate_type, slate_results in results.items():
            for method, scores in slate_results.items():
                overall_scores[method].extend([s['actual'] for s in scores])

        method_stats = {}
        for method, scores in overall_scores.items():
            if scores:
                method_stats[method] = {
                    'mean': np.mean(scores),
                    'std': np.std(scores),
                    'sharpe': np.mean(scores) / np.std(scores) if np.std(scores) > 0 else 0,
                    'percentile_90': np.percentile(scores, 90),
                    'percentile_10': np.percentile(scores, 10)
                }

        # Sort by mean performance
        sorted_methods = sorted(method_stats.items(), key=lambda x: x[1]['mean'], reverse=True)

        for method, stats in sorted_methods:
            print(f"\n{method.upper()}:")
            print(f"  Average Score: {stats['mean']:.2f}")
            print(f"  Consistency (StdDev): {stats['std']:.2f}")
            print(f"  Sharpe Ratio: {stats['sharpe']:.3f}")
            print(f"  90th Percentile: {stats['percentile_90']:.2f}")
            print(f"  10th Percentile: {stats['percentile_10']:.2f}")

        # By slate type
        print("\n\n📈 PERFORMANCE BY SLATE TYPE")
        print("-" * 60)

        for slate_type in ['small', 'medium', 'main', 'large']:
            print(f"\n{slate_type.upper()} Slates:")

            slate_stats = {}
            for method, scores in results[slate_type].items():
                if scores:
                    actuals = [s['actual'] for s in scores]
                    slate_stats[method] = np.mean(actuals)

            sorted_slate = sorted(slate_stats.items(), key=lambda x: x[1], reverse=True)
            for method, avg in sorted_slate:
                print(f"  {method}: {avg:.2f}")

        # Data completeness analysis
        print("\n\n📊 DATA COMPLETENESS IMPACT")
        print("-" * 60)

        for method in self.scoring_systems:
            all_completeness = []
            all_scores = []

            for slate_results in results.values():
                for result in slate_results[method]:
                    all_completeness.append(result['data_completeness'])
                    all_scores.append(result['actual'])

            if all_completeness and all_scores:
                correlation = np.corrcoef(all_completeness, all_scores)[0, 1]
                print(f"{method}: Data-Score Correlation = {correlation:.3f}")

        # Generate recommendations
        best_overall = sorted_methods[0][0]
        best_consistency = min(method_stats.items(), key=lambda x: x[1]['std'])[0]
        best_sharpe = max(method_stats.items(), key=lambda x: x[1]['sharpe'])[0]

        print("\n\n" + "=" * 60)
        print("🎯 FINAL RECOMMENDATIONS")
        print("=" * 60)

        recommendations = {
            'best_overall': best_overall,
            'best_consistency': best_consistency,
            'best_sharpe': best_sharpe,
            'method_stats': method_stats
        }

        print(f"\n✅ BEST OVERALL METHOD: {best_overall.upper()}")
        print(f"   • Highest average score across all conditions")
        print(f"   • {method_stats[best_overall]['mean']:.2f} average points")

        print(f"\n✅ MOST CONSISTENT: {best_consistency.upper()}")
        print(f"   • Lowest variance (best for cash games)")
        print(f"   • StdDev: {method_stats[best_consistency]['std']:.2f}")

        print(f"\n✅ BEST RISK-ADJUSTED: {best_sharpe.upper()}")
        print(f"   • Highest Sharpe ratio")
        print(f"   • Sharpe: {method_stats[best_sharpe]['sharpe']:.3f}")

        # Specific recommendations
        print("\n\n💡 STRATEGIC RECOMMENDATIONS:")
        print("-" * 60)

        # Check if hybrid performs best
        if 'hybrid_smart' in [best_overall, best_sharpe]:
            print("\n1. USE HYBRID SMART APPROACH")
            print("   • Best of both worlds")
            print("   • Pure data for complete players")
            print("   • Dynamic for incomplete data")
            print("   • Optimal for mixed player pools")
        elif best_overall == 'enhanced_pure':
            print("\n1. USE ENHANCED PURE DATA")
            print("   • Pure scoring + environmental factors")
            print("   • Considers park factors and weather")
            print("   • Best for accurate projections")
        elif best_overall == 'dynamic':
            print("\n1. USE DYNAMIC SYSTEM")
            print("   • Weight redistribution helps find value")
            print("   • Better for incomplete data scenarios")
            print("   • Good for large GPPs")
        else:
            print("\n1. USE PURE DATA SYSTEM")
            print("   • Most transparent and consistent")
            print("   • Easier to track and improve")
            print("   • Best for learning")

        # Contest type recommendations
        print("\n2. CONTEST-SPECIFIC STRATEGY:")
        print(f"   • Cash Games: Use {best_consistency.upper()}")
        print(f"   • Small GPPs: Use {best_sharpe.upper()}")
        print(f"   • Large GPPs: Use {best_overall.upper()}")

        # Implementation code
        print("\n3. IMPLEMENTATION CODE:")
        print("   Add this to your optimizer:")
        print(f"""
   def get_scoring_method(self, contest_type, slate_size):
       if contest_type == 'cash':
           return '{best_consistency}'
       elif slate_size in ['small', 'medium']:
           return '{best_sharpe}'
       else:
           return '{best_overall}'
        """)

        return recommendations


def main():
    """Run the comprehensive simulation"""
    simulator = DFSSimulator()

    # Run comprehensive test
    results = simulator.run_comprehensive_test(num_simulations=1000)

    # Analyze and get recommendations
    recommendations = simulator.analyze_results(results)

    # Save results
    print("\n\n📁 Saving detailed results to 'dfs_simulation_results.txt'...")

    with open('dfs_simulation_results.txt', 'w') as f:
        f.write("DFS SCORING SIMULATION RESULTS\n")
        f.write("=" * 60 + "\n\n")

        for slate_type, slate_results in results.items():
            f.write(f"\n{slate_type.upper()} SLATE RESULTS:\n")
            for method, scores in slate_results.items():
                if scores:
                    actuals = [s['actual'] for s in scores]
                    f.write(f"{method}: {np.mean(actuals):.2f} ± {np.std(actuals):.2f}\n")

    print("✅ Simulation complete!")
    print("\n🎯 FINAL VERDICT:")
    print(f"   Use {recommendations['best_overall'].upper()} for optimal performance!")


if __name__ == "__main__":
    main()