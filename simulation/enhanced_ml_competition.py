#!/usr/bin/env python3
"""
ENHANCED REALISTIC ML COMPETITION WITH DIFFICULTY SETTINGS
=========================================================
Tests YOUR system against increasingly difficult competition
"""

import sys
import os
import pandas as pd
import numpy as np
import random
from datetime import datetime
import multiprocessing as mp
# from functools import partial  # Not needed for this version
from typing import Dict, List, Tuple

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import YOUR components - CORRECTED PATHS
from main_optimizer.unified_core_system import UnifiedCoreSystem
from main_optimizer.strategy_selector import StrategyAutoSelector
from main_optimizer.unified_player_model import UnifiedPlayer

# Import simulator components - CORRECTED PATH
from simulation.robust_dfs_simulator import (
    generate_slate, simulate_lineup_score, generate_field
)

def generate_harder_field(num_opponents: int, slate: Dict, contest_type: str,
                          difficulty: str = 'medium') -> List[Dict]:
    """
    Generate a more challenging field of opponents

    Difficulty levels:
    - 'easy': Original mixed field (20% sharks, 50% average, 30% fish)
    - 'medium': Tougher field (40% sharks, 50% good, 10% average)
    - 'hard': Elite field (60% sharks, 40% good players)
    - 'extreme': Top competition (80% sharks, 20% elite sharks)
    - 'custom': Specify exact percentages
    """

    field = []

    # Define opponent distributions by difficulty
    distributions = {
        'easy': {
            'shark': 0.20,  # Optimal lineup builders
            'good': 0.30,  # Good players
            'average': 0.30,  # Average players
            'fish': 0.20  # Poor players
        },
        'medium': {
            'shark': 0.40,
            'good': 0.40,
            'average': 0.20,
            'fish': 0.00
        },
        'hard': {
            'shark': 0.60,
            'good': 0.35,
            'average': 0.05,
            'fish': 0.00
        },
        'extreme': {
            'shark': 0.80,
            'elite_shark': 0.15,  # Super optimizers
            'good': 0.05,
            'average': 0.00,
            'fish': 0.00
        }
    }

    dist = distributions.get(difficulty, distributions['medium'])

    # Generate opponents based on distribution
    for i in range(num_opponents):
        rand = random.random()
        cumulative = 0

        for player_type, percentage in dist.items():
            cumulative += percentage
            if rand <= cumulative:
                opponent_type = player_type
                break
        else:
            opponent_type = 'average'  # Fallback

        # Generate lineup based on opponent type
        lineup = generate_opponent_lineup(slate, contest_type, opponent_type)
        field.append(lineup)

    return field


def generate_opponent_lineup(slate: Dict, contest_type: str, opponent_type: str) -> Dict:
    """Generate lineup based on opponent skill level"""

    players = slate['players']

    if opponent_type == 'elite_shark':
        # Elite sharks use near-optimal strategies with slight randomization
        # They consider ownership, correlation, and advanced metrics
        strategy_params = {
            'projection_weight': 0.4,
            'ownership_weight': 0.3,
            'correlation_weight': 0.2,
            'advanced_metrics_weight': 0.1,
            'randomization': 0.05  # Small random factor
        }
        lineup = build_elite_shark_lineup(players, contest_type, strategy_params)

    elif opponent_type == 'shark':
        # Regular sharks use good strategies
        # Similar to your optimizer but with different parameters
        strategies = ['chalk_plus', 'balanced_sharp', 'correlation_value',
                      'smart_stack', 'ceiling_stack']
        strategy = random.choice(strategies)
        lineup = build_shark_lineup(players, contest_type, strategy)

    elif opponent_type == 'good':
        # Good players use reasonable approaches
        # Focus on projections with some strategy
        lineup = build_good_player_lineup(players, contest_type)

    elif opponent_type == 'average':
        # Average players use basic strategies
        lineup = build_average_lineup(players, contest_type)

    else:  # fish
        # Poor players make suboptimal choices
        lineup = build_fish_lineup(players, contest_type)

    return lineup


def build_elite_shark_lineup(players: List, contest_type: str, params: Dict) -> Dict:
    """
    Build lineup like an elite DFS player would
    Uses sophisticated multi-factor optimization
    """
    scored_players = []

    for player in players:
        # Multi-factor scoring
        score = 0

        # Base projection (with slight randomization)
        proj = player.get('projection', 0)
        proj_score = proj * (1 + random.uniform(-params['randomization'], params['randomization']))
        score += proj_score * params['projection_weight']

        # Ownership leverage
        ownership = player.get('ownership', 15)
        if contest_type == 'gpp':
            if ownership < 10:
                own_score = proj * 1.3  # Low owned upside
            elif ownership > 25:
                own_score = proj * 0.8  # Fade chalk in GPPs
            else:
                own_score = proj
        else:
            # Cash: embrace chalk
            own_score = proj * (1 + ownership / 100)
        score += own_score * params['ownership_weight']

        # Correlation (stacking)
        if contest_type == 'gpp' and player.get('position') != 'P':
            team_total = player.get('team_total', 4.5)
            if team_total > 5.0:
                corr_score = proj * 1.2
            else:
                corr_score = proj * 0.9
        else:
            corr_score = proj
        score += corr_score * params['correlation_weight']

        # Advanced metrics
        if player.get('position') == 'P':
            k_rate = player.get('k_rate', 20)
            adv_score = proj * (k_rate / 20)
        else:
            woba = player.get('woba', 0.320)
            adv_score = proj * (woba / 0.320)
        score += adv_score * params['advanced_metrics_weight']

        scored_players.append({
            'player': player,
            'score': score
        })

    # Build lineup using sophisticated position filling
    return optimize_lineup_sophisticated(scored_players, contest_type)


def build_shark_lineup(players: List, contest_type: str, strategy: str) -> Dict:
    """Build lineup using good but not perfect strategies"""

    # Similar to your strategies but with some variation
    scored_players = []

    for player in players:
        if strategy == 'chalk_plus':
            # High ownership + projection
            score = player.get('projection', 0) * (1 + player.get('ownership', 15) / 50)
        elif strategy == 'balanced_sharp':
            # Balance of factors
            score = (player.get('projection', 0) * 0.6 +
                     player.get('ceiling', 0) * 0.2 +
                     player.get('value_score', 0) * 0.2)
        elif strategy == 'correlation_value':
            # Correlation focus
            score = player.get('projection', 0)
            if player.get('team_total', 4.5) > 5.0:
                score *= 1.3
        elif strategy == 'smart_stack':
            # Team stacking
            score = player.get('projection', 0)
            # Boost for certain teams (simplified)
            if player.get('team') in get_top_projected_teams(players):
                score *= 1.4
        else:  # ceiling_stack
            score = player.get('ceiling', player.get('projection', 0) * 1.5)

        scored_players.append({
            'player': player,
            'score': score
        })

    return optimize_lineup_basic(scored_players)


def build_good_player_lineup(players: List, contest_type: str) -> Dict:
    """Build lineup like a good but not great player"""
    scored_players = []

    for player in players:
        # Good players focus mostly on projections with some basic strategy
        score = player.get('projection', 0)

        # Basic adjustments
        if contest_type == 'cash':
            # Favor consistent players
            if player.get('floor', 0) > player.get('projection', 0) * 0.8:
                score *= 1.1
        else:
            # Look for some upside
            ceiling = player.get('ceiling', player.get('projection', 0) * 1.5)
            score = score * 0.7 + ceiling * 0.3

        scored_players.append({
            'player': player,
            'score': score
        })

    return optimize_lineup_basic(scored_players)


def build_average_lineup(players: List, contest_type: str) -> Dict:
    """Build lineup like an average player"""
    scored_players = []

    for player in players:
        # Average players use simple heuristics
        score = player.get('projection', 0)

        # Basic value consideration
        if player.get('salary', 5000) > 0:
            value = score / (player.get('salary', 5000) / 1000)
            if value > 3.0:
                score *= 1.2

        scored_players.append({
            'player': player,
            'score': score
        })

    return optimize_lineup_basic(scored_players)


def build_fish_lineup(players: List, contest_type: str) -> Dict:
    """Build lineup like a poor player - makes bad decisions"""
    scored_players = []

    for player in players:
        # Fish make poor decisions
        score = player.get('projection', 0)

        # Overvalue name recognition (randomize a bit)
        score *= random.uniform(0.5, 1.5)

        # Chase previous performance too much
        if player.get('recent_performance', 1.0) > 1.2:
            score *= 1.5  # Overreact to hot streaks

        # Ignore important factors
        if player.get('position') == 'P' and player.get('era', 4.0) > 5.0:
            score *= 0.9  # Don't fade bad pitchers enough

        scored_players.append({
            'player': player,
            'score': score
        })

    return optimize_lineup_basic(scored_players)


def get_top_projected_teams(players: List, top_n: int = 3) -> List[str]:
    """Get teams with highest projected totals"""
    team_totals = {}
    for p in players:
        team = p.get('team')
        if team and p.get('position') != 'P':
            if team not in team_totals:
                team_totals[team] = 0
            team_totals[team] += p.get('projection', 0)

    sorted_teams = sorted(team_totals.items(), key=lambda x: x[1], reverse=True)
    return [team for team, _ in sorted_teams[:top_n]]


def optimize_lineup_sophisticated(scored_players: List, contest_type: str) -> Dict:
    """Sophisticated lineup optimization with stacking logic"""
    # This would implement actual stacking correlations
    # For now, using simplified version
    return optimize_lineup_basic(scored_players)


def optimize_lineup_basic(scored_players: List) -> Dict:
    """Basic lineup optimization"""
    # Sort by score
    scored_players.sort(key=lambda x: x['score'], reverse=True)

    # Fill positions (simplified)
    lineup = {
        'players': [],
        'positions_filled': {
            'P': 0, 'C': 0, '1B': 0, '2B': 0,
            '3B': 0, 'SS': 0, 'OF': 0
        },
        'salary_used': 0,
        'projection': 0  # ADD THIS LINE!
    }

    position_limits = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    for item in scored_players:
        player = item['player']
        pos = player.get('position')

        if (lineup['positions_filled'].get(pos, 0) < position_limits.get(pos, 0) and
                lineup['salary_used'] + player.get('salary', 0) <= 50000 and
                len(lineup['players']) < 10):
            lineup['players'].append(player)
            lineup['positions_filled'][pos] += 1
            lineup['salary_used'] += player.get('salary', 0)
            lineup['projection'] += player.get('projection', 0)  # ADD THIS LINE!

    return lineup

def process_single_slate_vs_field_enhanced(args: Tuple) -> Dict:
    """Enhanced version with difficulty settings"""
    slate_id, contest_type, slate_size, difficulty = args

    try:
        # Generate slate
        slate = generate_slate(slate_id, 'classic', slate_size)

        # BUILD YOUR LINEUP (same as before)
        players = []
        for sim_player in slate['players']:
            player = UnifiedPlayer(
                id=str(sim_player.get('id', hash(sim_player['name']))),
                name=sim_player['name'],
                team=sim_player['team'],
                salary=sim_player['salary'],
                primary_position=sim_player['position'],
                positions=[sim_player['position']],
                base_projection=sim_player.get('projection', 0)
            )

            # Add all attributes
            player.is_pitcher = (player.primary_position == 'P')
            for attr in ['ownership', 'recent_performance', 'matchup_score',
                         'hitting_matchup', 'pitching_matchup', 'park_factor',
                         'weather_score', 'vegas_score', 'correlation_score']:
                setattr(player, attr, sim_player.get(attr, 0))
            player._simulator_ownership = sim_player.get('ownership', 15)

            players.append(player)

        # Auto-select YOUR strategy
        selector = StrategyAutoSelector()
        your_strategy = selector.top_strategies[contest_type][slate_size]

        # Initialize YOUR system
        system = UnifiedCoreSystem()
        system.players = players
        system.csv_loaded = True

        # Build and optimize
        system.build_player_pool(include_unconfirmed=True)
        system.enrich_player_pool()

        # Restore simulator ownership
        for p in system.player_pool:
            if hasattr(p, '_simulator_ownership'):
                p.ownership_projection = p._simulator_ownership

        # Score and optimize
        system.score_players(contest_type)
        lineups = system.optimize_lineups(
            num_lineups=1,
            strategy=your_strategy,
            contest_type=contest_type
        )

        if not lineups or not lineups[0]:
            return None

        your_lineup = lineups[0]

        # Convert to sim format and calculate score
        your_sim_lineup = {
            'projection': your_lineup.get('total_score', 0),
            'salary': sum(p.salary for p in your_lineup['players']),
            'players': [{'id': p.id} for p in your_lineup['players']]
        }

        your_score = simulate_lineup_score(your_sim_lineup)

        # Generate HARDER field based on difficulty
        # Use the original generate_field with correct parameter order
        field = generate_field(slate, 100, contest_type)  # 100 total (you + 99 opponents)

        # Generate standard field first
        field = generate_field(slate, 100, contest_type)

        # Then modify based on difficulty
        if difficulty == 'hard':
            # Boost the field scores to make it harder
            for lineup in field:
                if 'projection' in lineup:
                    # Hard mode: opponents are 10-20% better
                    lineup['projection'] *= random.uniform(1.1, 1.2)
        elif difficulty == 'extreme':
            # Extreme mode: opponents are 20-30% better
            for lineup in field:
                if 'projection' in lineup:
                    lineup['projection'] *= random.uniform(1.2, 1.3)


        # Calculate scores and rank
        all_scores = []
        for lineup in field:
            score = simulate_lineup_score(lineup)
            all_scores.append(score)

        all_scores.append(your_score)
        all_scores.sort(reverse=True)

        your_rank = all_scores.index(your_score) + 1
        percentile = (100 - your_rank) / 100

        # Win conditions
        if contest_type == 'cash':
            win = your_rank <= 44
            roi = 80 if win else -100
        else:
            if your_rank == 1:
                roi = 900
            elif your_rank <= 3:
                roi = 400
            elif your_rank <= 10:
                roi = 100
            elif your_rank <= 20:
                roi = 0
            else:
                roi = -100
            win = your_rank <= 20

        return {
            'slate_id': slate_id,
            'strategy': your_strategy,
            'contest_type': contest_type,
            'slate_size': slate_size,
            'difficulty': difficulty,
            'rank': your_rank,
            'score': your_score,
            'win': win,
            'roi': roi,
            'percentile': percentile,
            'field_avg_score': np.mean(all_scores[:-1]),  # Exclude your score
            'field_top_score': all_scores[0] if your_rank > 1 else all_scores[1]
        }

    except Exception as e:
        print(f"\nError processing slate {slate_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


class EnhancedRealisticMLCompetition:
    """Enhanced competition with difficulty settings"""

    def __init__(self, num_cores=None):
        self.num_cores = num_cores or mp.cpu_count()
        self.strategy_selector = StrategyAutoSelector()

    def run_competition(self, slates_per_config: int = 100, difficulty: str = 'medium'):
        """Run competition with specified difficulty"""

        print("\n" + "=" * 80)
        print("🏁 ENHANCED REALISTIC ML COMPETITION")
        print("=" * 80)
        print(f"\n⚔️  DIFFICULTY: {difficulty.upper()}")

        # Describe the field
        if difficulty == 'easy':
            print("   • Field: 20% sharks, 30% good, 30% average, 20% fish")
            print("   • Expected cash win rate: ~50-55%")
            print("   • Expected GPP win rate: ~22-25%")
        elif difficulty == 'medium':
            print("   • Field: 40% sharks, 40% good, 20% average")
            print("   • Expected cash win rate: ~40-45%")
            print("   • Expected GPP win rate: ~15-20%")
        elif difficulty == 'hard':
            print("   • Field: 60% sharks, 35% good, 5% average")
            print("   • Expected cash win rate: ~30-35%")
            print("   • Expected GPP win rate: ~10-15%")
        elif difficulty == 'extreme':
            print("   • Field: 80% sharks, 15% ELITE sharks, 5% good")
            print("   • Expected cash win rate: ~20-25%")
            print("   • Expected GPP win rate: ~5-10%")
            print("   • WARNING: This is EXTREMELY difficult!")

        print(f"\n📋 Competition Setup:")
        print(f"   • Slates per configuration: {slates_per_config}")
        print(f"   • Using {self.num_cores} CPU cores")

        # Create tasks
        tasks = []
        slate_id = 5000  # Different starting ID

        for slate_size in ['small', 'medium', 'large']:
            for contest_type in ['cash', 'gpp']:
                for i in range(slates_per_config):
                    tasks.append((slate_id, contest_type, slate_size, difficulty))
                    slate_id += 1

        print(f"\n🏁 Processing {len(tasks)} slates at {difficulty} difficulty...")

        # Process in parallel
        all_results = []
        start_time = datetime.now()

        with mp.Pool(self.num_cores) as pool:
            for i, result in enumerate(pool.imap(process_single_slate_vs_field_enhanced, tasks)):
                if i % 10 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (len(tasks) - i) / rate if rate > 0 else 0
                    print(f"\r   Progress: {i}/{len(tasks)} slates "
                          f"({rate:.1f} slates/sec, ETA: {eta / 60:.1f} min)",
                          end="", flush=True)

                if result:
                    all_results.append(result)

        print(f"\n\n✅ Processed {len(all_results)} slates successfully")

        # Analyze results
        self._analyze_enhanced_results(all_results, difficulty)

        # Save results
        self._save_enhanced_results(all_results, difficulty)

    def _analyze_enhanced_results(self, all_results, difficulty):
        """Enhanced analysis with difficulty context"""

        print("\n" + "=" * 80)
        print(f"📊 COMPETITION RESULTS vs {difficulty.upper()} FIELD")
        print("=" * 80)

        # Calculate performance by strategy
        strategy_performance = {}

        for result in all_results:
            key = f"{result['strategy']}_{result['contest_type']}"

            if key not in strategy_performance:
                strategy_performance[key] = {
                    'wins': 0,
                    'total': 0,
                    'roi_sum': 0,
                    'ranks': [],
                    'percentiles': [],
                    'vs_field_avg': []
                }

            perf = strategy_performance[key]
            perf['total'] += 1
            perf['roi_sum'] += result['roi']
            perf['ranks'].append(result['rank'])
            perf['percentiles'].append(result['percentile'])
            if result['win']:
                perf['wins'] += 1

            # Compare to field average
            if result['score'] > 0 and result['field_avg_score'] > 0:
                perf['vs_field_avg'].append(result['score'] / result['field_avg_score'])

        # Expected win rates by difficulty
        expected_rates = {
            'easy': {'cash': 50, 'gpp': 23},
            'medium': {'cash': 42, 'gpp': 18},
            'hard': {'cash': 32, 'gpp': 12},
            'extreme': {'cash': 22, 'gpp': 7}
        }

        expected = expected_rates.get(difficulty, expected_rates['medium'])

        # Print results
        print(f"\n💰 CASH GAME PERFORMANCE (vs {difficulty} field):")
        print(f"{'Strategy':<30} {'Win %':>8} {'vs Expected':>12} {'Avg Rank':>10} {'vs Field':>10}")
        print("-" * 80)

        for key, perf in sorted(strategy_performance.items()):
            if '_cash' in key:
                strategy = key.replace('_cash', '')
                win_rate = (perf['wins'] / perf['total']) * 100
                avg_rank = np.mean(perf['ranks'])
                vs_field = np.mean(perf['vs_field_avg']) if perf['vs_field_avg'] else 1.0
                vs_expected = win_rate - expected['cash']

                status = "🏆" if vs_expected > 5 else "✅" if vs_expected > 0 else "⚠️"

                print(f"{strategy:<30} {win_rate:>7.1f}% {vs_expected:>+11.1f}% "
                      f"{avg_rank:>9.1f} {vs_field:>9.1%} {status}")

        print(f"\n🎯 GPP PERFORMANCE (vs {difficulty} field):")
        print(f"{'Strategy':<30} {'Win %':>8} {'ROI %':>10} {'Top 10%':>10} {'vs Field':>10}")
        print("-" * 80)

        for key, perf in sorted(strategy_performance.items()):
            if '_gpp' in key:
                strategy = key.replace('_gpp', '')
                win_rate = (perf['wins'] / perf['total']) * 100
                avg_roi = perf['roi_sum'] / perf['total']
                top_10_pct = sum(1 for r in perf['ranks'] if r <= 10) / perf['total'] * 100
                vs_field = np.mean(perf['vs_field_avg']) if perf['vs_field_avg'] else 1.0

                status = "🔥" if avg_roi > 50 else "✅" if avg_roi > 0 else "⚠️"

                print(f"{strategy:<30} {win_rate:>7.1f}% {avg_roi:>9.1f}% "
                      f"{top_10_pct:>9.1f}% {vs_field:>9.1%} {status}")

        # Overall summary
        print(f"\n📈 OVERALL vs {difficulty.upper()} COMPETITION:")
        total_cash = sum(1 for r in all_results if r['contest_type'] == 'cash')
        total_gpp = sum(1 for r in all_results if r['contest_type'] == 'gpp')
        cash_wins = sum(1 for r in all_results if r['contest_type'] == 'cash' and r['win'])
        gpp_wins = sum(1 for r in all_results if r['contest_type'] == 'gpp' and r['win'])

        if total_cash > 0:
            cash_win_rate = cash_wins / total_cash * 100
            print(f"   Cash win rate: {cash_win_rate:.1f}% (expected: {expected['cash']}%)")

        if total_gpp > 0:
            gpp_win_rate = gpp_wins / total_gpp * 100
            print(f"   GPP win rate: {gpp_win_rate:.1f}% (expected: {expected['gpp']}%)")

    def _save_enhanced_results(self, all_results, difficulty):
        """Save results with difficulty information"""
        df = pd.DataFrame(all_results)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ml_competition_{difficulty}_{timestamp}.csv'
        df.to_csv(filename, index=False)

        print(f"\n💾 Results saved to: {filename}")
        print(f"   • Total records: {len(df):,}")
        print(f"   • Difficulty: {difficulty}")


if __name__ == "__main__":
    print("""
    🏁 ENHANCED REALISTIC ML COMPETITION
    ====================================

    Test your system against increasingly difficult competition!

    Difficulty Levels:
    1. Easy (Original) - Mixed field with many weak players
    2. Medium - Tougher field, mostly good players
    3. Hard - Majority sharks, few weak players
    4. Extreme - Almost all sharks + elite optimizers
    5. Custom - Design your own field

    Slate Options:
    A. Quick test (10 slates per config = 60 total)
    B. Standard test (50 slates per config = 300 total)
    C. Comprehensive test (100 slates per config = 600 total)
    """)

    # Get difficulty
    diff_choice = input("\nSelect difficulty (1-5): ")
    difficulty_map = {
        '1': 'easy',
        '2': 'medium',
        '3': 'hard',
        '4': 'extreme',
        '5': 'custom'
    }
    difficulty = difficulty_map.get(diff_choice, 'medium')

    if difficulty == 'custom':
        print("\nCustom difficulty not implemented in this demo. Using 'hard' instead.")
        difficulty = 'hard'

    # Get slate count
    slate_choice = input("\nSelect slate option (A-C): ").upper()
    slates_map = {
        'A': 10,
        'B': 50,
        'C': 100
    }
    slates_per_config = slates_map.get(slate_choice, 50)

    # Cores
    max_cores = mp.cpu_count()
    core_input = input(f"\nHow many CPU cores to use? (1-{max_cores}, default={max_cores}): ")
    num_cores = int(core_input) if core_input.isdigit() else max_cores

    # Run competition
    competition = EnhancedRealisticMLCompetition(num_cores=min(num_cores, max_cores))
    competition.run_competition(slates_per_config, difficulty)

    print("\n✅ Competition complete!")

    # Suggest next steps based on results
    if difficulty == 'easy':
        print("\n💡 Try 'medium' or 'hard' difficulty next to really test your system!")
    elif difficulty in ['medium', 'hard']:
        print("\n💡 Your system is being properly tested. Use these results to improve!")
    elif difficulty == 'extreme':
        print("\n💡 This is elite-level competition. Even 10% wins here is impressive!")