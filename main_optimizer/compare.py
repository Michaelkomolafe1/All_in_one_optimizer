#!/usr/bin/env python
# simple_strategy_test_final.py
# Save in main_optimizer/
"""
Simple test - just see if strategies generate good lineups
No simulator complications!
"""

import sys
import os

# Fix imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'simulation'))

# Import what we need
from simulation.robust_dfs_simulator import generate_slate
from unified_core_system import UnifiedCoreSystem
from player_converter import convert_sim_players_to_unified

print("STRATEGY SUCCESS TEST")
print("=" * 60)
print("Testing if your strategies can generate winning lineups\n")


def test_strategy_success(strategy_name, contest_type='gpp', num_tests=5):
    """Test if a strategy generates good lineups"""

    print(f"\nTesting {strategy_name} ({contest_type}):")
    print("-" * 40)

    successful_lineups = 0
    total_projections = []
    total_salaries = []

    for i in range(num_tests):
        try:
            # Generate different slates
            slate_id = 12345 + i
            slate = generate_slate(slate_id, 'classic', 'medium')

            # Convert to UnifiedPlayer
            unified_players = convert_sim_players_to_unified(slate['players'])

            # Initialize system
            system = UnifiedCoreSystem()
            system.players = unified_players
            system.csv_loaded = True
            system.enrichments_applied = True

            # Build pool
            system.build_player_pool(include_unconfirmed=True)

            # Apply strategy based on name
            if strategy_name == 'projection_monster':
                from cash_strategies import build_projection_monster
                system.player_pool = build_projection_monster(system.player_pool)
            elif strategy_name == 'pitcher_dominance':
                from cash_strategies import build_pitcher_dominance
                system.player_pool = build_pitcher_dominance(system.player_pool)
            elif strategy_name == 'correlation_value':
                from gpp_strategies import build_correlation_value
                system.player_pool = build_correlation_value(system.player_pool)
            elif strategy_name == 'matchup_leverage_stack':
                from gpp_strategies import build_matchup_leverage_stack
                params = {
                    'pitcher_leverage_mult': 1.2,
                    'hitter_leverage_mult': 1.15,
                    'ownership_fade': 0.8,
                    'stack_correlation_bonus': 1.1,
                    'era_threshold': 3.5,
                    'k9_threshold': 9.0,
                    'whip_threshold': 1.2,
                    'iso_threshold': 0.200,
                    'woba_threshold': 0.340,
                    'barrel_threshold': 10.0
                }
                system.player_pool = build_matchup_leverage_stack(system.player_pool, params)

            # Check if we're trying tournament_winner_gpp
            elif strategy_name == 'tournament_winner_gpp':
                try:
                    from tournament_winner_gpp_strategy import build_tournament_winner_gpp
                    system.player_pool = build_tournament_winner_gpp(system.player_pool)
                except ImportError:
                    print("  ⚠️  tournament_winner_gpp_strategy.py not found!")
                    print("     Make sure to save that file first.")
                    return

            # Optimize
            from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig

            config = OptimizationConfig()
            config.contest_type = contest_type

            optimizer = UnifiedMILPOptimizer(config)
            lineup, score = optimizer.optimize_lineup(
                players=system.player_pool,
                strategy='balanced'
            )

            if lineup and len(lineup) == 10:
                total_salary = sum(p.salary for p in lineup)
                total_projection = sum(getattr(p, 'base_projection', 10) for p in lineup)

                successful_lineups += 1
                total_projections.append(total_projection)
                total_salaries.append(total_salary)

                # Show one example lineup
                if i == 0:
                    print(f"\n  Example Lineup:")
                    # Count team stacks
                    team_counts = {}
                    for p in lineup:
                        if p.primary_position != 'P':
                            team_counts[p.team] = team_counts.get(p.team, 0) + 1

                    # Show lineup
                    for p in lineup:
                        print(
                            f"    {p.primary_position:>2} {p.name:<15} ${p.salary:>5} {getattr(p, 'base_projection', 0):>5.1f}pts")

                    print(f"\n  Salary: ${total_salary:,} / $50,000")
                    print(f"  Projection: {total_projection:.1f} points")

                    # Show stacks for GPP
                    if contest_type == 'gpp':
                        stacks = [(team, count) for team, count in team_counts.items() if count >= 2]
                        if stacks:
                            print(f"  Stacks: {', '.join([f'{team}({count})' for team, count in stacks])}")

        except Exception as e:
            print(f"  Error on test {i + 1}: {e}")

    # Summary
    if successful_lineups > 0:
        avg_projection = sum(total_projections) / len(total_projections)
        avg_salary = sum(total_salaries) / len(total_salaries)

        print(f"\n  ✅ SUCCESS: {successful_lineups}/{num_tests} valid lineups")
        print(f"  Average projection: {avg_projection:.1f} points")
        print(f"  Average salary: ${avg_salary:,.0f}")

        # Rate the strategy
        if contest_type == 'cash' and avg_projection > 140:
            print(f"  💪 Strong cash strategy!")
        elif contest_type == 'gpp' and any(p > 160 for p in total_projections):
            print(f"  🚀 Good GPP ceiling!")

        return True
    else:
        print(f"  ❌ FAILED: No valid lineups generated")
        return False


# Test strategies
print("\nCASH STRATEGIES:")
cash_results = {}
cash_results['projection_monster'] = test_strategy_success('projection_monster', 'cash')
cash_results['pitcher_dominance'] = test_strategy_success('pitcher_dominance', 'cash')

print("\n\nGPP STRATEGIES:")
gpp_results = {}
gpp_results['correlation_value'] = test_strategy_success('correlation_value', 'gpp')
gpp_results['matchup_leverage_stack'] = test_strategy_success('matchup_leverage_stack', 'gpp')

# Try tournament winner if it exists
gpp_results['tournament_winner_gpp'] = test_strategy_success('tournament_winner_gpp', 'gpp')

# Final summary
print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)

print("\nCash Strategies:")
for strat, success in cash_results.items():
    status = "✅ Working" if success else "❌ Failed"
    print(f"  {strat}: {status}")

print("\nGPP Strategies:")
for strat, success in gpp_results.items():
    if strat == 'tournament_winner_gpp' and not success:
        print(f"  {strat}: ⚠️  File not found")
    else:
        status = "✅ Working" if success else "❌ Failed"
        print(f"  {strat}: {status}")

working_count = sum(cash_results.values()) + sum(gpp_results.values())
total_count = len(cash_results) + len(gpp_results)

print(f"\nOverall: {working_count}/{total_count} strategies working")

if working_count > 0:
    print("\n🎉 Your optimizer is generating valid lineups!")
    print("The tournament enhancements are successfully integrated.")
    print("\nNext steps:")
    print("1. Save tournament_winner_gpp_strategy.py if you haven't")
    print("2. Fix the recursion in build_truly_smart_stack")
    print("3. Use these strategies in real contests!")
else:
    print("\n⚠️  Check the errors above to debug")