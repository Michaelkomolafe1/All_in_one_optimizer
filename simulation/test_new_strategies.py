# main_optimizer/test_new_strategies.py
# Test file that works with your actual directory structure

import sys
import os

# Add simulation directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(parent_dir, 'simulation'))

# Import from simulation
from robust_dfs_simulator import generate_slate

# Import strategies from current directory (main_optimizer)
from data_driven_cash_strategy import build_data_driven_cash
from correlation_gpp_strategy import build_correlation_gpp

# Also import your existing strategies for comparison
from cash_strategies import build_projection_monster, build_pitcher_dominance
from gpp_strategies import build_correlation_value, build_truly_smart_stack, build_matchup_leverage_stack


def test_strategy(strategy_func, strategy_name, slate_size='medium'):
    """Test if a strategy works"""
    print(f"\nTesting {strategy_name} on {slate_size} slate...")

    # Generate test slate
    slate = generate_slate(1234, 'classic', slate_size)
    print(f"Generated slate with {len(slate['players'])} players")

    try:
        # Test the strategy
        if 'gpp' in strategy_name.lower() and strategy_func == build_correlation_gpp:
            # New GPP strategy expects slate_size parameter
            lineup = strategy_func(slate['players'], slate_size)
        else:
            # All other strategies (including old ones) just take players
            lineup = strategy_func(slate['players'])

        if lineup and lineup.get('players') and len(lineup['players']) == 10:
            print(f"✅ SUCCESS! Generated valid lineup")
            print(f"   Salary: ${lineup['salary']:,}")
            print(f"   Projection: {lineup['projection']:.1f}")

            # Show stack info if available
            if 'stack_info' in lineup:
                print(f"   Stack pattern: {lineup['stack_info']['pattern']}")

            return True
        else:
            print(f"❌ FAILED: Invalid lineup generated")
            return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("TESTING DFS STRATEGIES")
    print("=" * 80)

    print("\n📦 TESTING CURRENT STRATEGIES:")
    print("-" * 40)

    # Test current strategies
    current_results = {
        'cash': {
            'projection_monster': test_strategy(build_projection_monster, 'projection_monster', 'small'),
            'pitcher_dominance': test_strategy(build_pitcher_dominance, 'pitcher_dominance', 'medium')
        },
        'gpp': {
            'correlation_value': test_strategy(build_correlation_value, 'correlation_value', 'small'),
            'truly_smart_stack': test_strategy(build_truly_smart_stack, 'truly_smart_stack', 'medium'),
            'matchup_leverage_stack': test_strategy(build_matchup_leverage_stack, 'matchup_leverage_stack', 'large')
        }
    }

    print("\n🆕 TESTING NEW STRATEGIES:")
    print("-" * 40)

    # Test new strategies
    new_results = {
        'cash': test_strategy(build_data_driven_cash, 'data_driven_cash', 'medium'),
        'gpp': {
            'small': test_strategy(build_correlation_gpp, 'correlation_gpp_small', 'small'),
            'medium': test_strategy(build_correlation_gpp, 'correlation_gpp_medium', 'medium'),
            'large': test_strategy(build_correlation_gpp, 'correlation_gpp_large', 'large')
        }
    }

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    print("\n📦 Current Strategies:")
    cash_pass = all(current_results['cash'].values())
    gpp_pass = all(current_results['gpp'].values())
    print(f"  Cash: {'✅ ALL PASSED' if cash_pass else '❌ SOME FAILED'}")
    print(f"  GPP: {'✅ ALL PASSED' if gpp_pass else '❌ SOME FAILED'}")

    print("\n🆕 New Strategies:")
    new_cash_pass = new_results['cash']
    new_gpp_pass = all(new_results['gpp'].values())
    print(f"  Cash: {'✅ PASSED' if new_cash_pass else '❌ FAILED'}")
    print(f"  GPP: {'✅ ALL PASSED' if new_gpp_pass else '❌ SOME FAILED'}")

    if cash_pass and gpp_pass and new_cash_pass and new_gpp_pass:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nNext step: Run the strategy comparison to see which perform better.")
    else:
        print("\n⚠️  Some tests failed. Check error messages above.")


if __name__ == "__main__":
    main()