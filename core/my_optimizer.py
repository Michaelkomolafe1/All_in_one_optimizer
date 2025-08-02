#!/usr/bin/env python3
import sys
import pandas as pd
import random

sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem
from dfs_optimizer.strategies.strategy_selector import StrategyAutoSelector


class MyOptimizer(UnifiedCoreSystem):
    """Enhanced optimizer that ensures projections are loaded"""

    def load_players_from_csv(self, csv_path: str):
        """Override to ensure projections are loaded correctly"""
        # Call parent method
        super().load_players_from_csv(csv_path)

        # Fix projections
        df = pd.read_csv(csv_path)
        for player in self.players:
            matching_row = df[df['Name'] == player.name]
            if not matching_row.empty:
                projection = float(matching_row.iloc[0]['AvgPointsPerGame'])
                player.base_projection = projection
                player.recent_form_score = projection

                # Set enrichment attributes
                player.vegas_score = 0.8 + (projection / 50)
                player.matchup_score = 0.7 + (player.salary / 20000)
                player.park_score = 1.0
                player.weather_score = 1.0

        print(f"✅ Fixed projections for {len(self.players)} players")


def run_cash_optimizer():
    """Run cash game optimization"""
    system = MyOptimizer()
    system.load_players_from_csv("/home/michael/Downloads/DKSalaries(29).csv")
    system.build_player_pool(include_unconfirmed=True)

    # Apply variation in enrichment
    import random
    for player in system.player_pool:
        if player.base_projection > 0:
            player.vegas_score = 0.8 + (player.base_projection / 50)
            player.recent_form_score = player.base_projection * (0.85 + random.random() * 0.3)
            player.matchup_score = 0.7 + (player.salary / 20000)
            player.weather_score = 0.95 + (hash(player.name) % 10) / 100

            park_factors = {
                'COL': 1.15, 'TEX': 1.10, 'CIN': 1.08, 'BOS': 1.05,
                'SF': 0.92, 'SD': 0.90, 'LAD': 0.93, 'SEA': 0.88
            }
            player.park_score = park_factors.get(player.team, 1.0)

    system.enrichments_applied = True
    system.score_players('cash')

    # Set enhanced scores
    for player in system.player_pool:
        player.enhanced_score = player.cash_score
        player.optimization_score = player.cash_score

    # Get strategy and optimize
    selector = StrategyAutoSelector()
    strategy = selector.top_strategies['cash']['medium']

    lineups = system.optimize_lineups(
        num_lineups=1,
        strategy=strategy,
        contest_type='cash'
    )

    if lineups:
        lineup = lineups[0]
        print(f"\n🏆 Optimized Cash Lineup:")
        print(f"Salary: ${sum(p.salary for p in lineup['players']):,}/50,000")
        print(f"Projected: {lineup.get('total_score', 0):.1f} points\n")

        print("POSITION | NAME | TEAM | SALARY | SCORE")
        print("-" * 50)
        for p in lineup['players']:
            print(f"{p.primary_position:8} | {p.name:20} | {p.team:3} | ${p.salary:,} | {p.enhanced_score:.1f}")

        # Copy to clipboard format
        print("\n📋 DraftKings Upload Format:")
        for p in lineup['players']:
            print(f"{p.primary_position}:{p.name}")


if __name__ == "__main__":
    run_cash_optimizer()