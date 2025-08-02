#!/usr/bin/env python3
"""Test that strategies are properly integrated"""

import os
import pandas as pd
from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_strategy_integration():
    """Test the full strategy integration"""

    print("\n=== TESTING STRATEGY INTEGRATION ===\n")

    # Create system
    system = UnifiedCoreSystem()

    # Use real DraftKings CSV
    csv_path = "/home/michael/Downloads/DKSalaries(32).csv"
    print(f"Using DraftKings CSV: {csv_path}")

    # Check if file exists
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found at {csv_path}")
        print("Available DK files in Downloads:")
        downloads_path = "/home/michael/Downloads"
        for file in os.listdir(downloads_path):
            if file.startswith("DKSalaries") and file.endswith(".csv"):
                print(f"  - {file}")
        return

    try:
        # First, let's see what's in the CSV
        df = pd.read_csv(csv_path)
        print(f"\nCSV Info:")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Positions: {df['Position'].unique() if 'Position' in df.columns else 'No Position column'}")

        # Load CSV
        system.load_players_from_csv(csv_path)
        print(f"\n✓ Loaded {len(system.players)} players")

        # Show position breakdown
        position_counts = {}
        for player in system.players:
            pos = player.primary_position
            position_counts[pos] = position_counts.get(pos, 0) + 1
        print(f"Position breakdown: {position_counts}")

        # Show salary range
        salaries = [p.salary for p in system.players]
        print(f"Salary range: ${min(salaries):,} - ${max(salaries):,}")

        # Build player pool
        system.build_player_pool(include_unconfirmed=True)
        print(f"\n✓ Built player pool with {len(system.player_pool)} players")

        # Enrich player pool
        system.enrich_player_pool()
        print("✓ Enriched player pool")

        # Test each strategy
        cash_strategies = ['projection_monster', 'pitcher_dominance']
        gpp_strategies = ['correlation_value', 'truly_smart_stack', 'matchup_leverage_stack']

        all_passed = True

        # Test CASH strategies
        print(f"\n--- Testing CASH strategies ---")
        for strategy in cash_strategies:
            print(f"\nTesting {strategy}...")

            # Generate one lineup
            lineups = system.optimize_lineups(
                num_lineups=1,
                strategy=strategy,
                contest_type='cash'
            )

            if lineups:
                lineup = lineups[0]
                print(f"✓ Success! Generated lineup with score: {lineup['total_projection']:.2f}")
                print(f"  Salary used: ${lineup['total_salary']:,} / $50,000")

                # Show lineup composition
                print("  Lineup:")
                for player in lineup['players']:
                    print(
                        f"    {player.primary_position}: {player.name} ({player.team}) - ${player.salary:,} - {player.optimization_score:.2f}")

                # Check if strategy modified scores
                modified_count = 0
                for player in lineup['players']:
                    if abs(player.optimization_score - player.projection) > 0.01:
                        modified_count += 1
                print(f"  Strategy modified {modified_count}/{len(lineup['players'])} player scores")
            else:
                print(f"✗ Failed to generate lineup")
                all_passed = False

        # Test GPP strategies
        print(f"\n--- Testing GPP strategies ---")
        for strategy in gpp_strategies:
            print(f"\nTesting {strategy}...")

            # Generate one lineup
            lineups = system.optimize_lineups(
                num_lineups=1,
                strategy=strategy,
                contest_type='gpp'
            )

            if lineups:
                lineup = lineups[0]
                print(f"✓ Success! Generated lineup with score: {lineup['total_projection']:.2f}")
                print(f"  Salary used: ${lineup['total_salary']:,} / $50,000")

                # Check team stacking
                team_counts = {}
                for player in lineup['players']:
                    team = player.team
                    team_counts[team] = team_counts.get(team, 0) + 1

                # Sort by count
                sorted_teams = sorted(team_counts.items(), key=lambda x: x[1], reverse=True)
                print(f"  Team distribution: {dict(sorted_teams)}")

                max_stack = max(team_counts.values()) if team_counts else 0
                if max_stack >= 3:
                    print(f"  ✓ Found stack of {max_stack} players from {sorted_teams[0][0]}!")

                # Show lineup
                print("  Lineup:")
                for player in lineup['players']:
                    print(
                        f"    {player.primary_position}: {player.name} ({player.team}) - ${player.salary:,} - {player.optimization_score:.2f}")
            else:
                print(f"✗ Failed to generate lineup")
                all_passed = False

        # Test auto strategy selection
        print("\n--- Testing AUTO strategy selection ---")
        lineups = system.optimize_lineups(
            num_lineups=1,
            strategy='auto',
            contest_type='gpp'
        )

        if lineups:
            print(f"✓ Auto strategy worked!")
            # The strategy used should be in the logs
        else:
            print(f"✗ Auto strategy failed")
            all_passed = False

        print("\n=== TEST COMPLETE ===")
        print(f"Overall result: {'✓ ALL PASSED' if all_passed else '✗ SOME FAILED'}\n")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_strategy_integration()