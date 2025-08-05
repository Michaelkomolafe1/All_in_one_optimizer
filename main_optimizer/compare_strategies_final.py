# compare_strategies_fixed.py
# Save in main_optimizer/
"""Compare strategies with proper player conversion"""

import sys
import os
import numpy as np
from datetime import datetime

# Fix imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'simulation'))

# Import simulation
from simulation.robust_dfs_simulator import generate_slate, simulate_lineup_score, generate_field

# Import converter
from player_converter import convert_sim_players_to_unified

# Import strategies
from cash_strategies import build_projection_monster, build_pitcher_dominance
from gpp_strategies import build_correlation_value, build_truly_smart_stack, build_matchup_leverage_stack
from data_driven_cash_strategy import build_data_driven_cash
from correlation_gpp_strategy import build_correlation_gpp


class FixedStrategyComparison:
    """Compare strategies with proper conversion"""

    def __init__(self):
        print("\n*** USING PROPER PLAYER CONVERSION ***")
        print("Old strategies get UnifiedPlayer objects")
        print("New strategies get dict format\n")

        # Strategy mappings
        self.current_strategies = {
            'cash': {
                'small': ('projection_monster', build_projection_monster, True),  # True = needs UnifiedPlayer
                'medium': ('pitcher_dominance', build_pitcher_dominance, True),
                'large': ('pitcher_dominance', build_pitcher_dominance, True)
            },
            'gpp': {
                'small': ('correlation_value', build_correlation_value, True),
                'medium': ('truly_smart_stack', build_truly_smart_stack, True),
                'large': ('matchup_leverage_stack', build_matchup_leverage_stack, True)
            }
        }

        self.new_strategies = {
            'cash': ('data_driven_cash', build_data_driven_cash, False),  # False = uses dict
            'gpp': ('correlation_gpp', build_correlation_gpp, False)
        }

    def test_single_slate(self, strategy_func, strategy_name, slate, contest_type, field_size, slate_size, use_unified):
        """Test strategy on slate with proper conversion"""
        try:
            # Convert players if needed
            if use_unified:
                players = convert_sim_players_to_unified(slate['players'])
            else:
                players = slate['players']

            # Build lineup
            if strategy_name == 'correlation_gpp':
                lineup = strategy_func(players, slate_size)
            else:
                lineup = strategy_func(players)

            if not lineup or not lineup.get('players') or len(lineup['players']) != 10:
                return None

            # Check salary cap
            if lineup.get('salary', 0) > 50000:
                return None

            # Score using simulator
            our_score = simulate_lineup_score(lineup)

            # Generate simulated field
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
        """Run comparison with proper conversion"""

        print("=" * 80)
        print("STRATEGY COMPARISON WITH PROPER CONVERSION")
        print("=" * 80)

        results = {}

        for contest_type in ['cash', 'gpp']:
            results[contest_type] = {}

            print("\n{} CONTESTS".format(contest_type.upper()))
            print("-" * 60)

            for slate_size in ['small', 'medium', 'large']:
                print("\n{} slates:".format(slate_size.upper()))

                # Get strategies
                current_name, current_func, current_unified = self.current_strategies[contest_type][slate_size]
                new_name, new_func, new_unified = self.new_strategies[contest_type]

                # Track results
                current_wins = 0
                new_wins = 0
                current_roi_sum = 0
                new_roi_sum = 0
                valid_slates = 0

                # Test on multiple slates
                for i in range(num_slates):
                    # Generate slate with unique seed
                    slate_id = hash("{}_{}_{}".format(contest_type, slate_size, i)) % (2 ** 31 - 1)
                    slate = generate_slate(slate_id, 'classic', slate_size)

                    field_size = 100 if contest_type == 'cash' else 1000

                    # Test both strategies
                    current_result = self.test_single_slate(
                        current_func, current_name, slate, contest_type,
                        field_size, slate_size, current_unified
                    )

                    new_result = self.test_single_slate(
                        new_func, new_name, slate, contest_type,
                        field_size, slate_size, new_unified
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

                    print("\n   CURRENT: {} (UnifiedPlayer)".format(current_name))
                    print("      Win rate: {:.1f}%".format(current_win_rate))
                    print("      Avg ROI: {:+.1f}%".format(current_avg_roi))

                    print("\n   NEW: {} (dict)".format(new_name))
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
                else:
                    print("\n   No valid results - check strategy errors")

        print("\n" + "=" * 80)
        print("COMPARISON COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    print("""
    STRATEGY COMPARISON - FIXED VERSION
    ===================================

    This properly converts players for each strategy type:
    - Current strategies: Get UnifiedPlayer objects
    - New strategies: Get dict format

    No API calls - pure simulation!
    """)

    # First run the debug script
    print("\nFirst, let's debug the data structure...")
    os.system("python debug_strategy_data.py")

    slates = raw_input("\nSlates per test? (20=quick, 50=standard): ") if sys.version_info[0] < 3 else input(
        "\nSlates per test? (20=quick, 50=standard): ")

    try:
        num_slates = int(slates)
    except:
        num_slates = 30

    comparison = FixedStrategyComparison()
    comparison.run_comparison(num_slates)

    print("\nDone! Check test_strategies_fixed.py for individual strategy tests.")