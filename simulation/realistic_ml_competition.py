#!/usr/bin/env python3
"""
REALISTIC ML COMPETITION WITH ADJUSTABLE DIFFICULTY
==================================================
Tests YOUR system against realistic DFS field with varying difficulty levels
"""

import sys
import os
import pandas as pd
import numpy as np
import random
from datetime import datetime
import multiprocessing as mp
from typing import Dict, List, Tuple
import time

# PATCH: Disable API calls for simulation
os.environ['DISABLE_LIVE_ENRICHMENTS'] = 'true'

# Fix paths - use relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import YOUR components with correct paths
from main_optimizer.unified_core_system import UnifiedCoreSystem
from main_optimizer.strategy_selector import StrategyAutoSelector
from main_optimizer.unified_player_model import UnifiedPlayer

# Import simulator components
from simulation.robust_dfs_simulator import (
    generate_slate, simulate_lineup_score, generate_field
)


class RealisticMLCompetition:
    """
    Realistic competition with adjustable difficulty
    """

    def __init__(self, num_cores=4, difficulty='medium'):
        self.num_cores = num_cores
        self.difficulty = difficulty
        self.results = []

        # Define difficulty distributions
        self.difficulty_settings = {
            'easy': {
                'shark_pct': 0.10,  # 10% optimal players
                'good_pct': 0.20,  # 20% good players
                'average_pct': 0.40,  # 40% average
                'fish_pct': 0.30  # 30% weak players
            },
            'medium': {
                'shark_pct': 0.20,
                'good_pct': 0.30,
                'average_pct': 0.35,
                'fish_pct': 0.15
            },
            'hard': {
                'shark_pct': 0.35,
                'good_pct': 0.40,
                'average_pct': 0.20,
                'fish_pct': 0.05
            },
            'extreme': {
                'shark_pct': 0.50,
                'good_pct': 0.35,
                'average_pct': 0.15,
                'fish_pct': 0.00
            },
            'sliding': None  # Will be set based on slate number
        }

    def generate_adaptive_field(self, num_opponents: int, slate_num: int = 0) -> List[Dict]:
        """Generate field that gets harder over time if sliding difficulty"""

        if self.difficulty == 'sliding':
            # Start easy, get harder every 100 slates
            progress = min(slate_num / 500, 1.0)  # Max difficulty at 500 slates

            # Interpolate between easy and extreme
            shark_pct = 0.10 + (0.50 - 0.10) * progress
            good_pct = 0.20 + (0.35 - 0.20) * progress
            fish_pct = 0.30 * (1 - progress)  # Fish disappear
            average_pct = 1.0 - shark_pct - good_pct - fish_pct

            dist = {
                'shark_pct': shark_pct,
                'good_pct': good_pct,
                'average_pct': average_pct,
                'fish_pct': fish_pct
            }
        else:
            dist = self.difficulty_settings[self.difficulty]

        # Generate opponents
        field = []
        for i in range(num_opponents):
            rand = random.random()

            if rand < dist['shark_pct']:
                skill_level = 'shark'
                skill_factor = random.uniform(0.9, 1.0)  # Very good
            elif rand < dist['shark_pct'] + dist['good_pct']:
                skill_level = 'good'
                skill_factor = random.uniform(0.7, 0.9)
            elif rand < dist['shark_pct'] + dist['good_pct'] + dist['average_pct']:
                skill_level = 'average'
                skill_factor = random.uniform(0.5, 0.7)
            else:
                skill_level = 'fish'
                skill_factor = random.uniform(0.3, 0.5)

            field.append({
                'id': i,
                'skill_level': skill_level,
                'skill_factor': skill_factor
            })

        return field

    def process_single_slate_vs_field(self, args: Tuple) -> Dict:
        """Process a single slate with YOUR system vs field"""

        slate_id, contest_type, slate_size, slate_num = args

        try:
            # Generate slate
            slate = generate_slate(slate_id, 'classic', slate_size)

            # Convert to UnifiedPlayer format for YOUR system
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

                # Copy all simulator attributes
                for attr in ['matchup_score', 'park_factor', 'weather_score',
                             'recent_performance', 'consistency_score', 'ownership',
                             'batting_order', 'game_total', 'team_total']:
                    if attr in sim_player:
                        setattr(player, attr, sim_player[attr])

                # Set derived attributes
                player.is_pitcher = (player.primary_position == 'P')
                player.implied_team_score = sim_player.get('team_total', 4.5)
                player.recent_form = sim_player.get('recent_performance', 1.0)
                player.projected_ownership = sim_player.get('ownership', 15)

                players.append(player)

            # Auto-select strategy FIRST
            selector = StrategyAutoSelector()

            # Try to analyze slate first
            try:
                slate_analysis = selector.analyze_slate_from_csv(players)
                strategy_name, reason = selector.select_strategy(
                    slate_analysis=slate_analysis,
                    contest_type=contest_type
                )
            except Exception as e:
                # Fallback: Direct access based on known slate size
                print(f"Warning: Strategy selection failed ({e}), using direct access")
                strategy_name = selector.top_strategies[contest_type][slate_size]
                reason = f"Direct selection for {slate_size} {contest_type}"

            # Build YOUR lineup using YOUR system
            system = UnifiedCoreSystem()
            system.players = players
            system.csv_loaded = True

            # Build YOUR lineup using YOUR system
            system = UnifiedCoreSystem()
            system.players = players
            system.csv_loaded = True

            # Build player pool
            system.build_player_pool(include_unconfirmed=True)

            # SKIP API ENRICHMENTS - we already have all data from simulator
            # Instead, copy simulator data directly and mark as enriched
            system.player_pool = system.player_pool or players

            # Copy simulator data to player pool
            for player in system.player_pool:
                # Find matching sim player
                sim_player = next((sp for sp in slate['players'] if sp['name'] == player.name), None)
                if sim_player:
                    # Copy all the enrichment data from simulator
                    player.team_total = sim_player.get('team_total', 4.5)
                    player.implied_team_score = sim_player.get('team_total', 4.5) / 2
                    player.weather_impact = 1.0  # Perfect conditions in sim
                    player.park_factor = sim_player.get('park_factor', 1.0)
                    player.recent_form = sim_player.get('recent_performance', 1.0)
                    player.consistency_score = 50 + (player.salary / 10000 * 30)

                    # Restore ownership
                    if hasattr(player, '_simulator_ownership'):
                        player.ownership_projection = player._simulator_ownership

            # Mark enrichments as applied to bypass the check
            system.enrichments_applied = True

            # Score players with YOUR enhanced scoring engine
            system.score_players(contest_type)

            # Optimize with YOUR MILP optimizer
            lineups = system.optimize_lineups(
                num_lineups=1,
                strategy=strategy_name,
                contest_type=contest_type
            )

            if not lineups or not lineups[0]:
                print(f"Failed to generate lineup for slate {slate_id}")
                return None

            your_lineup = lineups[0]

            # Convert YOUR lineup to simulator format
            your_sim_lineup = []
            for p in your_lineup['players']:
                sim_player = next((sp for sp in slate['players'] if sp['name'] == p.name), None)
                if sim_player:
                    your_sim_lineup.append(sim_player)

            # If we couldn't match all players, something is wrong
            if len(your_sim_lineup) != len(your_lineup['players']):
                print(f"Warning: Could only match {len(your_sim_lineup)}/{len(your_lineup['players'])} players")
                return None

            # Generate field with adaptive difficulty
            field = self.generate_adaptive_field(99, slate_num)

            # Generate opponent lineups using the standard generate_field
            # The skill distribution is already built into generate_field
            opponent_lineups = generate_field(slate, 100, contest_type)

            # For harder difficulties, we can adjust the scores after generation
            if self.difficulty == 'hard':
                # Make opponents 10-20% better
                for i, lineup in enumerate(opponent_lineups):
                    boost = 1.0 + (field[i]['skill_factor'] * 0.2) if i < len(field) else 1.1
                    # We'll apply the boost when scoring
            elif self.difficulty == 'extreme':
                # Make opponents 15-30% better
                for i, lineup in enumerate(opponent_lineups):
                    boost = 1.0 + (field[i]['skill_factor'] * 0.3) if i < len(field) else 1.2

            # Score all lineups
            # simulate_lineup_score expects a lineup dict with 'players' key
            your_lineup_dict = {
                'players': your_sim_lineup,
                'salary': sum(p.get('salary', 0) for p in your_sim_lineup),
                'projection': sum(p.get('projection', 0) for p in your_sim_lineup)
            }
            your_score = simulate_lineup_score(your_lineup_dict)

            # Score opponents with difficulty adjustments
            opponent_scores = []
            for lineup in opponent_lineups:
                base_score = simulate_lineup_score(lineup)

                # Apply difficulty boost
                if self.difficulty == 'easy':
                    # Easy mode: reduce opponent scores by 5-10%
                    adjusted_score = base_score * random.uniform(0.90, 0.95)
                elif self.difficulty == 'hard':
                    # Hard mode: boost opponent scores by 5-15%
                    adjusted_score = base_score * random.uniform(1.05, 1.15)
                elif self.difficulty == 'extreme':
                    # Extreme mode: boost opponent scores by 10-25%
                    adjusted_score = base_score * random.uniform(1.10, 1.25)
                elif self.difficulty == 'sliding':
                    # Sliding: progressively harder
                    progress = min(slate_num / 500, 1.0)
                    boost = 1.0 - (0.1 * (1 - progress))  # From 0.9 to 1.0
                    adjusted_score = base_score * boost
                else:  # medium
                    adjusted_score = base_score

                opponent_scores.append(adjusted_score)

            # Calculate results
            all_scores = [your_score] + opponent_scores
            all_scores.sort(reverse=True)

            your_rank = all_scores.index(your_score) + 1
            percentile = ((100 - your_rank) / 100) * 100

            # ROI calculation
            if contest_type == 'cash':
                win = your_rank <= 44  # Top 44%
                roi = 100 if win else -100
            else:  # GPP
                if your_rank == 1:
                    roi = 900
                elif your_rank <= 3:
                    roi = 400
                elif your_rank <= 10:
                    roi = 100
                elif your_rank <= 20:
                    roi = -50
                else:
                    roi = -100
                win = your_rank <= 20

            # Collect ML training data
            player_data = []
            for player in your_lineup['players']:
                sim_p = next((sp for sp in slate['players'] if sp['name'] == player.name), None)
                if sim_p:
                    player_data.append({
                        'slate_id': slate_id,
                        'slate_num': slate_num,
                        'difficulty': self.difficulty,
                        'strategy': strategy_name,
                        'contest_type': contest_type,
                        'slate_size': slate_size,
                        'player_name': player.name,
                        'position': player.primary_position,
                        'salary': player.salary,
                        'projection': player.base_projection,
                        'actual_score': sim_p.get('actual_score', 0),
                        'optimization_score': getattr(player, 'optimization_score', 0),
                        'lineup_score': your_score,
                        'lineup_rank': your_rank,
                        'lineup_percentile': percentile,
                        'lineup_win': win,
                        'lineup_roi': roi,
                        'field_avg_score': np.mean(opponent_scores),
                        'difficulty_level': self.difficulty
                    })

            return {
                'slate_id': slate_id,
                'contest_type': contest_type,
                'strategy': strategy_name,
                'your_score': your_score,
                'your_rank': your_rank,
                'win': win,
                'roi': roi,
                'percentile': percentile,
                'player_data': player_data
            }

        except Exception as e:
            print(f"Error processing slate {slate_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def run_competition(self, slates_per_config: int = 50):
        """Run full competition test"""

        print(f"\n🏁 REALISTIC ML COMPETITION - {self.difficulty.upper()} DIFFICULTY")
        print("=" * 60)

        # Create test configurations
        configs = [
            ('cash', 'small'),
            ('cash', 'medium'),
            ('cash', 'large'),
            ('gpp', 'small'),
            ('gpp', 'medium'),
            ('gpp', 'large')
        ]

        all_tasks = []
        slate_counter = 0

        for contest_type, slate_size in configs:
            for i in range(slates_per_config):
                slate_id = slate_counter * 1000 + i
                all_tasks.append((slate_id, contest_type, slate_size, slate_counter))
                slate_counter += 1

        # Process in parallel
        print(f"\n📊 Running {len(all_tasks)} total slates on {self.num_cores} cores...")

        all_results = []

        with mp.Pool(self.num_cores) as pool:
            for i, result in enumerate(pool.imap_unordered(
                    self.process_single_slate_vs_field, all_tasks)):

                if result:
                    all_results.append(result)

                if (i + 1) % 50 == 0:
                    print(f"Progress: {i + 1}/{len(all_tasks)} slates processed...")

        # Save results
        self._save_training_data(all_results)

        # Print summary
        self._print_summary(all_results)

        return all_results

    def _save_training_data(self, all_results):
        """Save ML training data"""

        all_player_data = []
        for result in all_results:
            if 'player_data' in result:
                all_player_data.extend(result['player_data'])

        if all_player_data:
            df = pd.DataFrame(all_player_data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'ml_training_data_{self.difficulty}_{timestamp}.csv'
            df.to_csv(filename, index=False)

            print(f"\n💾 Training data saved to: {filename}")
            print(f"   • Total records: {len(df):,}")
            print(f"   • Unique slates: {df['slate_id'].nunique()}")
            print(f"   • Difficulty: {self.difficulty}")

    def _print_summary(self, all_results):
        """Print competition summary"""

        print("\n" + "=" * 60)
        print(f"📊 COMPETITION RESULTS - {self.difficulty.upper()} DIFFICULTY")
        print("=" * 60)

        # Group by strategy
        from collections import defaultdict
        strategy_results = defaultdict(list)

        for result in all_results:
            key = f"{result['strategy']}_{result['contest_type']}"
            strategy_results[key].append(result)

        # Print results by strategy
        for strategy_key, results in strategy_results.items():
            strategy, contest = strategy_key.rsplit('_', 1)

            wins = sum(1 for r in results if r['win'])
            total = len(results)
            win_rate = wins / total * 100 if total > 0 else 0
            avg_roi = sum(r['roi'] for r in results) / total if total > 0 else 0
            avg_rank = sum(r['your_rank'] for r in results) / total if total > 0 else 0

            print(f"\n{strategy} ({contest}):")
            print(f"  • Contests: {total}")
            print(f"  • Win Rate: {win_rate:.1f}%")
            print(f"  • Avg ROI: {avg_roi:+.1f}%")
            print(f"  • Avg Rank: {avg_rank:.1f}/100")

        # Overall performance
        total_contests = len(all_results)
        total_wins = sum(1 for r in all_results if r['win'])
        overall_win_rate = total_wins / total_contests * 100 if total_contests > 0 else 0

        print(f"\n🎯 OVERALL PERFORMANCE:")
        print(f"   • Total contests: {total_contests}")
        print(f"   • Overall win rate: {overall_win_rate:.1f}%")
        print(f"   • Difficulty: {self.difficulty}")


if __name__ == "__main__":
    print("""
    🏁 REALISTIC ML COMPETITION
    ==========================

    Test your system against increasingly difficult competition!

    Difficulty Levels:
    1. Easy (Original) - Mixed field with many weak players
    2. Medium - Tougher field, mostly good players
    3. Hard - Majority sharks, few weak players
    4. Extreme - Almost all sharks + elite optimizers
    5. Sliding - Starts easy, gets progressively harder

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
        '5': 'sliding'
    }
    difficulty = difficulty_map.get(diff_choice, 'medium')

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
    print(f"\n🚀 Starting competition with:")
    print(f"   Difficulty: {difficulty}")
    print(f"   Slates per config: {slates_per_config}")
    print(f"   CPU cores: {num_cores}")

    confirm = input("\nProceed? (y/n): ")
    if confirm.lower() == 'y':
        competition = RealisticMLCompetition(
            num_cores=min(num_cores, max_cores),
            difficulty=difficulty
        )
        competition.run_competition(slates_per_config)
        print("\n✅ Competition complete!")
    else:
        print("\nCompetition cancelled.")