#!/usr/bin/env python3
"""
TEST DFS OPTIMIZER SYSTEM
========================
Run this to verify strategies and enhancements are working
"""

import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.unified_core_system import UnifiedCoreSystem
from core.strategy_auto_selector import StrategyAutoSelector


def test_optimizer_system():
    """Test the complete optimizer system"""
    print("=" * 60)
    print("DFS OPTIMIZER SYSTEM TEST")
    print("=" * 60)

    # Initialize system
    system = UnifiedCoreSystem()
    selector = StrategyAutoSelector()

    # Load your CSV
    csv_path = "/home/michael/Downloads/DKSalaries(27).csv"  # Update if needed
    if not os.path.exists(csv_path):
        csv_path = "/home/michael/Downloads/DKSalaries(28).csv"

    print(f"\n1. LOADING CSV: {os.path.basename(csv_path)}")
    system.load_players_from_csv(csv_path)
    print(f"   ✓ Loaded {len(system.players)} players")

    # Analyze slate
    print("\n2. SLATE ANALYSIS:")
    slate_info = selector.analyze_slate_from_csv(system.players)
    print(f"   ✓ Slate size: {slate_info['slate_size']}")
    print(f"   ✓ Games detected: {slate_info.get('games_detected', 'Unknown')}")
    print(f"   ✓ Average total: {slate_info.get('avg_total', 0):.1f}")

    # Fetch confirmations
    print("\n3. FETCHING CONFIRMATIONS:")
    try:
        confirmed = system.fetch_confirmed_players()
        print(f"   ✓ Found {len(confirmed)} confirmed players")
    except Exception as e:
        print(f"   ✗ Error fetching confirmations: {e}")
        confirmed = set()

    # Build pool
    print("\n4. BUILDING PLAYER POOL:")
    system.build_player_pool(include_unconfirmed=True)  # Include all for testing
    print(f"   ✓ Pool size: {len(system.player_pool)} players")

    # Check batting orders
    print("\n5. BATTING ORDER CHECK:")
    players_with_order = 0
    for player in system.player_pool[:10]:
        order = getattr(player, 'batting_order', None)
        if order and order > 0:
            players_with_order += 1
            print(f"   • {player.name}: Order {order}")

    if players_with_order == 0:
        print("   ✗ No batting order data found")
        print("   Note: This is normal if lineups aren't posted yet")
    else:
        print(f"   ✓ Players with batting order: {players_with_order}")

    # Test scoring differences
    print("\n6. STRATEGY & SCORING TEST:")

    # Get strategies for both contest types
    cash_strategy = selector.top_strategies['cash'][slate_info['slate_size']]
    gpp_strategy = selector.top_strategies['gpp'][slate_info['slate_size']]

    print(f"   Cash strategy: {cash_strategy}")
    print(f"   GPP strategy: {gpp_strategy}")

    if system.player_pool:
        # Score players for both
        system.score_players('cash')
        test_player = system.player_pool[0]
        cash_score = test_player.enhanced_score

        system.score_players('gpp')
        gpp_score = test_player.enhanced_score

        print(f"\n   Test player: {test_player.name}")
        print(f"   Cash score: {cash_score:.2f}")
        print(f"   GPP score: {gpp_score:.2f}")
        print(f"   Difference: {abs(cash_score - gpp_score):.2f}")

        if abs(cash_score - gpp_score) < 0.01:
            print("   ⚠️  WARNING: Scores are identical - strategies may not be applying correctly")
        else:
            print("   ✓ Different scoring for Cash vs GPP confirmed!")

    # Check enhancements
    print("\n7. ENHANCEMENT CHECK:")
    if system.player_pool:
        test_player = system.player_pool[0]
        enhanced_attrs = {
            'team_total': 'Team Total',
            'game_total': 'Game Total',
            'dff_projection': 'DFF Projection',
            'salary': 'Salary'
        }

        found_enhancements = 0
        for attr, name in enhanced_attrs.items():
            value = getattr(test_player, attr, None)
            if value:
                print(f"   ✓ {name}: {value}")
                found_enhancements += 1
            else:
                print(f"   ✗ {name}: Not found")

        if found_enhancements == 0:
            print("   ⚠️  No enhancements found - enrichment may have failed")

    # Run optimization for both contest types
    print("\n8. OPTIMIZATION TEST:")

    if len(system.player_pool) >= 10:
        # Cash optimization
        print("\n   CASH (1 lineup):")
        try:
            cash_lineups = system.optimize_lineups(
                num_lineups=1,
                strategy=cash_strategy,
                contest_type='cash'
            )
            if cash_lineups:
                lineup = cash_lineups[0]
                print(f"   ✓ Total salary: ${lineup['total_salary']:,}")
                print(f"   ✓ Total projection: {lineup['total_projection']:.1f}")
                print(f"   ✓ Players: {', '.join([p.name for p in lineup['players'][:3]])}...")

                # Check strategy applied
                teams_in_lineup = {}
                for p in lineup['players']:
                    teams_in_lineup[p.team] = teams_in_lineup.get(p.team, 0) + 1
                max_from_team = max(teams_in_lineup.values())
                print(f"   ✓ Max players from one team: {max_from_team} (Cash should be ≤3)")
        except Exception as e:
            print(f"   ✗ Cash optimization failed: {e}")

        # GPP optimization
        print("\n   GPP (3 lineups):")
        try:
            gpp_lineups = system.optimize_lineups(
                num_lineups=3,
                strategy=gpp_strategy,
                contest_type='gpp'
            )
            if gpp_lineups:
                for i, lineup in enumerate(gpp_lineups, 1):
                    print(f"   Lineup {i}: ${lineup['total_salary']:,} - {lineup['total_projection']:.1f} pts")

                    # Check for stacking
                    teams_in_lineup = {}
                    for p in lineup['players']:
                        teams_in_lineup[p.team] = teams_in_lineup.get(p.team, 0) + 1
                    stacks = [t for t, c in teams_in_lineup.items() if c >= 3]
                    if stacks:
                        print(f"      Stack detected: {', '.join(stacks)}")
        except Exception as e:
            print(f"   ✗ GPP optimization failed: {e}")
    else:
        print("   ✗ Not enough players in pool for optimization")

    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    print("\nSUMMARY:")
    print("- If scores are different for Cash vs GPP: ✓ Strategies working")
    print("- If Cash limits players per team: ✓ Constraints working")
    print("- If GPP shows stacks: ✓ Correlation working")
    print("- If batting order missing: Normal before lineups posted")
    print("=" * 60)


if __name__ == "__main__":
    test_optimizer_system()
