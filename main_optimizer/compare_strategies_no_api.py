# compare_strategies_no_api.py
# Save in main_optimizer/
"""Compare strategies using ONLY simulation data - NO API CALLS"""

import sys
import os
import numpy as np
from datetime import datetime

# Fix imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'simulation'))

# Import simulation (no APIs)
from simulation.robust_dfs_simulator import generate_slate, simulate_lineup_score, generate_field

# Import strategies
from cash_strategies import build_projection_monster, build_pitcher_dominance
from gpp_strategies import build_correlation_value, build_truly_smart_stack, build_matchup_leverage_stack
from data_driven_cash_strategy import build_data_driven_cash
from correlation_gpp_strategy import build_correlation_gpp


class NoAPIStrategyComparison:
    """Compare strategies using simulation data only"""

    def __init__(self):
        print("\n*** NO API CALLS WILL BE MADE ***")
        print("Using 100% simulated data for fair comparison\n")

        # Your strategy mappings
        self.current_strategies = {
            'cash': {
                'small': ('projection_monster', build_projection_monster),
                'medium': ('pitcher_dominance', build_pitcher_dominance),
                'large': ('pitcher_dominance', build_pitcher_dominance)
            },
            'gpp': {
                'small': ('correlation_value', build_correlation_value),
                'medium': ('truly_smart_stack', build_truly_smart_stack),
                'large': ('matchup_leverage_stack', build_matchup_leverage_stack)
            }
        }

        self.new_strategies = {
            'cash': ('data_driven_cash', build_data_driven_cash),
            'gpp': ('correlation_gpp', build_correlation_gpp)
        }

    def test_single_slate(self, strategy_func, strategy_name, slate, contest_type, field_size, slate_size):
        """Test strategy on simulated slate - NO APIs"""
        try:
            # Build lineup using ONLY simulation data
            if strategy_name == 'correlation_gpp':
                lineup = strategy_func(slate['players'], slate_size)
            else:
                lineup = strategy_func(slate['players'])

            if not lineup or not lineup.get('players') or len(lineup['players']) != 10:
                return None

            # Score using simulator (no APIs)
            our_score = simulate_lineup_score(lineup)

            # Generate simulated field (no APIs)
            field = generate_field(slate, field_size, contest_type)
            field_scores = [simulate_lineup_score(f) for f in field]

            # Calculate results
            all_scores = [our_score] + field_scores
            all_scores.sort(reverse=True)
            rank = all_scores.index(our_score) + 1

            # Win/ROI calculation
            if contest_type == 'cash':
                win = rank <= int(field_size * 0.44)
                roi = 80 if win else -100
            else:
                if rank == 1:
                    roi = 900
                elif rank <= int(field_size * 0.03):
                    roi = 400
                elif rank <= int(field_size * 0.1):
                    roi = 100
                elif rank <= int(field_size * 0.2):
                    roi = 0
                else:
                    roi = -100
                win = rank <= int(field_size * 0.2)

            return {
                'win': win,
                'roi': roi,
                'rank': rank,
                'score': our_score
            }

        except Exception as e:
            return None

    def run_comparison(self, num_slates=30):
        """Run comparison using only simulated data"""

        print("=" * 80)
        print("STRATEGY COMPARISON (SIMULATION ONLY - NO APIs)")
        print("=" * 80)

        results = {}

        for contest_type in ['cash', 'gpp']:
            results[contest_type] = {}

            print("\n{} CONTESTS".format(contest_type.upper()))
            print("-" * 60)

            for slate_size in ['small', 'medium', 'large']:
                print("\n{} slates:".format(slate_size.upper()))

                # Get strategies
                current_name, current_func = self.current_strategies[contest_type][slate_size]
                new_name, new_func = self.new_strategies[contest_type]

                # Track results
                current_wins = 0
                new_wins = 0
                current_roi_sum = 0
                new_roi_sum = 0
                valid_slates = 0

                # Test on multiple slates
                for i in range(num_slates):
                    # Generate simulated slate (NO API CALLS)
                    slate_id = hash("{}_{}_{}_v2".format(contest_type, slate_size, i)) % (2 ** 31 - 1)
                    slate = generate_slate(slate_id, 'classic', slate_size)

                    field_size = 100 if contest_type == 'cash' else 1000

                    # Test both strategies
                    current_result = self.test_single_slate(
                        current_func, current_name, slate, contest_type, field_size, slate_size
                    )

                    new_result = self.test_single_slate(
                        new_func, new_name, slate, contest_type, field_size, slate_size
                    )

                    if current_result and new_result:
                        valid_slates += 1
                        current_wins += current_result['win']
                        new_wins += new_result['win']
                        current_roi_sum += current_result['roi']
                        new_roi_sum += new_result['roi']

                # Show results
                if valid_slates > 0:
                    current_win_rate = (current_wins / valid_slates) * 100
                    new_win_rate = (new_wins / valid_slates) * 100
                    current_avg_roi = current_roi_sum / valid_slates
                    new_avg_roi = new_roi_sum / valid_slates

                    print("\n   CURRENT: {}".format(current_name))
                    print("      Win rate: {:.1f}%".format(current_win_rate))
                    print("      Avg ROI: {:+.1f}%".format(current_avg_roi))

                    print("\n   NEW: {}".format(new_name))
                    print("      Win rate: {:.1f}%".format(new_win_rate))
                    print("      Avg ROI: {:+.1f}%".format(new_avg_roi))

                    # Winner
                    if contest_type == 'cash':
                        diff = new_win_rate - current_win_rate
                        winner = "NEW" if diff > 0 else "CURRENT"
                        print("\n   WINNER: {} (by {:.1f}% win rate)".format(winner, abs(diff)))
                    else:
                        diff = new_avg_roi - current_avg_roi
                        winner = "NEW" if diff > 0 else "CURRENT"
                        print("\n   WINNER: {} (by {:.1f}% ROI)".format(winner, abs(diff)))

        print("\n" + "=" * 80)
        print("SIMULATION COMPLETE - NO API CALLS WERE MADE")
        print("=" * 80)


if __name__ == "__main__":
    print("""
    STRATEGY COMPARISON - SIMULATION ONLY
    =====================================

    This test uses ONLY simulated data - NO API calls!
    Fair comparison between strategies.

    The simulator provides all needed data:
    - Projections
    - Ownership
    - Batting orders
    - K-rates
    - Game totals
    - And more!
    """)

    slates = raw_input("\nSlates per test? (20=quick, 50=standard): ") if sys.version_info[0] < 3 else input(
        "\nSlates per test? (20=quick, 50=standard): ")

    try:
        num_slates = int(slates)
    except:
        num_slates = 30

    comparison = NoAPIStrategyComparison()
    comparison.run_comparison(num_slates)

    print("\nDone! All tests used simulated data only.")