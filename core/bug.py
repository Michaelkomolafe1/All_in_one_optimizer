#!/usr/bin/env python3
"""
Test lineup generation without GUI
Run this from command line to test your optimizer
"""
import sys

sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem
from dfs_optimizer.strategies.strategy_selector import StrategyAutoSelector
from enhanced_gui_display import EnhancedGUIDisplay
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)


def test_lineup_generation(csv_path, contest_type='cash', num_lineups=1):
    """Test lineup generation with full details"""
    print("=" * 80)
    print(f"🏈 DFS OPTIMIZER TEST - {contest_type.upper()}")
    print("=" * 80)

    # 1. Initialize system
    print("\n1️⃣ Initializing system...")
    system = UnifiedCoreSystem()
    selector = StrategyAutoSelector()

    # 2. Load CSV
    print(f"\n2️⃣ Loading CSV: {csv_path}")
    system.load_players_from_csv(csv_path)
    print(f"✅ Loaded {len(system.players)} players")

    # Show sample players
    print("\nSample players:")
    for p in system.players[:3]:
        print(f"  {p.name} ({p.primary_position}) - ${p.salary} - {p.base_projection:.1f} pts")

    # 3. Build player pool
    print("\n3️⃣ Building player pool...")
    system.build_player_pool(include_unconfirmed=True)
    print(f"✅ Pool size: {len(system.player_pool)} players")

    # 4. Detect slate
    teams = set(p.team for p in system.player_pool)
    num_games = len(teams) // 2
    if num_games <= 3:
        slate_size = 'small'
    elif num_games <= 7:
        slate_size = 'medium'
    else:
        slate_size = 'large'

    print(f"\n📊 Slate info:")
    print(f"  Teams: {len(teams)}")
    print(f"  Games: ~{num_games}")
    print(f"  Size: {slate_size}")

    # 5. Get strategy
    strategy = selector.top_strategies[contest_type][slate_size]
    print(f"  Strategy: {strategy}")

    # 6. Enrich players
    print("\n4️⃣ Enriching player data...")
    system.enrich_player_pool()

    # Check enrichment
    sample = system.player_pool[0]
    print(f"\nEnrichment check - {sample.name}:")
    print(f"  Base: {sample.base_projection:.1f}")
    print(f"  Vegas: {sample.vegas_score:.2f}")
    print(f"  Park: {sample.park_score:.2f}")
    print(f"  Enhanced: {sample.enhanced_score:.1f}")

    # 7. Score players
    print(f"\n5️⃣ Scoring players for {contest_type}...")
    system.score_players(contest_type)

    # Show top scorers
    print("\nTop 5 scorers:")
    sorted_players = sorted(system.player_pool,
                            key=lambda p: p.cash_score if contest_type == 'cash' else p.gpp_score,
                            reverse=True)[:5]

    for i, p in enumerate(sorted_players):
        score = p.cash_score if contest_type == 'cash' else p.gpp_score
        print(f"  {i + 1}. {p.name} ({p.primary_position}): {score:.1f} pts")

    # 8. Optimize lineups
    print(f"\n6️⃣ Optimizing {num_lineups} lineup(s)...")
    lineups = system.optimize_lineups(
        num_lineups=num_lineups,
        strategy=strategy,
        contest_type=contest_type
    )

    if not lineups:
        print("❌ No lineups generated!")
        return

    # 9. Display lineups with enhanced details
    print(f"\n✅ Generated {len(lineups)} lineup(s):\n")

    for i, lineup in enumerate(lineups, 1):
        display_data = EnhancedGUIDisplay.create_lineup_display(lineup, contest_type)

        print(f"{'=' * 80}")
        print(f"LINEUP {i}")
        print(f"{'=' * 80}")
        print(f"{'Pos':<4} {'Player':<20} {'Team':<4} {'Salary':<8} {'DK Proj':<8} {'Enhanced':<9} {'Using':<8}")
        print("-" * 80)

        for player_data in display_data['players']:
            print(f"{player_data['position']:<4} "
                  f"{player_data['name']:<20} "
                  f"{player_data['team']:<4} "
                  f"{player_data['salary_display']:<8} "
                  f"{player_data['dk_projection']:<8.1f} "
                  f"{player_data['enhanced_score']:<9.1f} "
                  f"{player_data['optimization_score']:<8.1f}")

        print("-" * 80)
        totals = display_data['totals']
        print(f"{'TOTALS:':<37} "
              f"${totals['salary']:<7,} "
              f"{totals['dk_projection']:<8.1f} "
              f"{totals['enhanced_total']:<9.1f} "
              f"{display_data['optimization_score']:<8.1f}")

        # Show stacks
        teams = {}
        for p in lineup['players']:
            teams[p.team] = teams.get(p.team, 0) + 1
        stacks = {t: c for t, c in teams.items() if c >= 2}
        if stacks:
            print(f"\n🏟️ Stacks: {stacks}")

        print()


def quick_test():
    """Quick test with default settings"""
    csv_path = "/home/michael/Downloads/DKSalaries(34).csv"

    # Test cash lineup
    print("\n" + "🎯" * 40 + "\n")
    test_lineup_generation(csv_path, 'cash', 1)

    # Test GPP lineups
    print("\n" + "🎯" * 40 + "\n")
    test_lineup_generation(csv_path, 'gpp', 3)


if __name__ == "__main__":
    # Run with command line args or use defaults
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        contest_type = sys.argv[2] if len(sys.argv) > 2 else 'cash'
        num_lineups = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        test_lineup_generation(csv_path, contest_type, num_lineups)
    else:
        quick_test()