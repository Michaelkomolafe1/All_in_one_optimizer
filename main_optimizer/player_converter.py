# test_strategies_fixed.py
# Save in main_optimizer/
"""Test strategies with proper player conversion"""

import sys
import os

# Fix imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'simulation'))

# Import simulation
from simulation.robust_dfs_simulator import generate_slate

# Import converter
from player_converter import convert_sim_players_to_unified

# Import strategies
from data_driven_cash_strategy import build_data_driven_cash
from correlation_gpp_strategy import build_correlation_gpp
from cash_strategies import build_projection_monster, build_pitcher_dominance
from gpp_strategies import build_correlation_value, build_truly_smart_stack, build_matchup_leverage_stack


def test_strategy(strategy_func, strategy_name, slate_size='medium', use_unified=True):
    """Test if a strategy works"""
    print("\nTesting {} on {} slate...".format(strategy_name, slate_size))

    # Generate test slate
    slate = generate_slate(1234 + hash(strategy_name), 'classic', slate_size)
    print("Generated slate with {} players".format(len(slate['players'])))

    # Convert players based on strategy type
    if use_unified:
        # Old strategies need UnifiedPlayer objects
        print("Converting to UnifiedPlayer objects...")
        players = convert_sim_players_to_unified(slate['players'])
    else:
        # New strategies use dict format
        players = slate['players']

    try:
        # Test the strategy
        if 'gpp' in strategy_name.lower() and strategy_func == build_correlation_gpp:
            # New GPP strategy expects slate_size parameter
            lineup = strategy_func(players, slate_size)
        else:
            # All other strategies just take players
            lineup = strategy_func(players)

        if lineup and lineup.get('players') and len(lineup['players']) == 10:
            print("SUCCESS! Generated valid lineup")
            print("   Salary: ${}".format(lineup.get('salary', 'N/A')))
            print("   Projection: {:.1f}".format(lineup.get('projection', 0)))

            # Show stack info if available
            if 'stack_info' in lineup:
                print("   Stack pattern: {}".format(lineup['stack_info']['pattern']))

            # Check salary is valid
            if lineup.get('salary', 0) > 50000:
                print("   WARNING: Salary over cap!")
                return False

            return True
        else:
            print("FAILED: Invalid lineup generated")
            if lineup:
                print("   Players in lineup: {}".format(len(lineup.get('players', []))))
                if lineup.get('salary', 0) > 50000:
                    print("   Salary: ${} (OVER CAP!)".format(lineup['salary']))
            return False

    except Exception as e:
        print("ERROR: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return False


def debug_new_strategy_issue():
    """Debug why new strategies aren't working"""
    print("\n" + "=" * 60)
    print("DEBUGGING NEW STRATEGY ISSUES")
    print("=" * 60)

    # Generate a test slate
    slate = generate_slate(9999, 'classic', 'medium')
    players = slate['players']

    print("\nChecking data structure...")
    print("Total players: {}".format(len(players)))

    # Check a sample player
    if players:
        sample = players[0]
        print("\nSample player structure:")
        print("  Keys: {}".format(list(sample.keys())))
        print("  Name: {}".format(sample.get('name', 'N/A')))
        print("  Position: {}".format(sample.get('position', 'N/A')))
        print("  Salary: ${}".format(sample.get('salary', 'N/A')))
        print("  Projection: {}".format(sample.get('projection', 'N/A')))

    # Count positions
    positions = {}
    for p in players:
        pos = p.get('position', 'Unknown')
        positions[pos] = positions.get(pos, 0) + 1

    print("\nPosition counts:")
    for pos, count in sorted(positions.items()):
        print("  {}: {}".format(pos, count))

    # Check salary distribution
    salaries = [p.get('salary', 0) for p in players]
    if salaries:
        print("\nSalary range: ${} - ${}".format(min(salaries), max(salaries)))
        print("Average salary: ${:.0f}".format(sum(salaries) / len(salaries)))


def main():
    print("=" * 80)
    print("TESTING DFS STRATEGIES WITH PROPER CONVERSION")
    print("=" * 80)

    # First debug the data
    debug_new_strategy_issue()

    print("\n" + "-" * 60)
    print("TESTING CURRENT STRATEGIES (with UnifiedPlayer):")
    print("-" * 60)

    # Test current strategies with UnifiedPlayer objects
    current_results = {
        'cash': {
            'projection_monster': test_strategy(build_projection_monster, 'projection_monster', 'small',
                                                use_unified=True),
            'pitcher_dominance': test_strategy(build_pitcher_dominance, 'pitcher_dominance', 'medium', use_unified=True)
        },
        'gpp': {
            'correlation_value': test_strategy(build_correlation_value, 'correlation_value', 'small', use_unified=True),
            'truly_smart_stack': test_strategy(build_truly_smart_stack, 'truly_smart_stack', 'medium',
                                               use_unified=True),
            'matchup_leverage_stack': test_strategy(build_matchup_leverage_stack, 'matchup_leverage_stack', 'large',
                                                    use_unified=True)
        }
    }

    print("\n" + "-" * 60)
    print("TESTING NEW STRATEGIES (with dict format):")
    print("-" * 60)

    # Test new strategies with dict format
    new_results = {
        'cash': test_strategy(build_data_driven_cash, 'data_driven_cash', 'medium', use_unified=False),
        'gpp': {
            'small': test_strategy(build_correlation_gpp, 'correlation_gpp_small', 'small', use_unified=False),
            'medium': test_strategy(build_correlation_gpp, 'correlation_gpp_medium', 'medium', use_unified=False),
            'large': test_strategy(build_correlation_gpp, 'correlation_gpp_large', 'large', use_unified=False)
        }
    }

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    print("\nCurrent Strategies (UnifiedPlayer):")
    cash_pass = all(current_results['cash'].values())
    gpp_pass = all(current_results['gpp'].values())
    print("  Cash: {}".format('ALL PASSED' if cash_pass else 'SOME FAILED'))
    print("  GPP: {}".format('ALL PASSED' if gpp_pass else 'SOME FAILED'))

    print("\nNew Strategies (dict):")
    new_cash_pass = new_results['cash']
    new_gpp_pass = all(new_results['gpp'].values())
    print("  Cash: {}".format('PASSED' if new_cash_pass else 'FAILED'))
    print("  GPP: {}".format('ALL PASSED' if new_gpp_pass else 'SOME FAILED'))


if __name__ == "__main__":
    main()