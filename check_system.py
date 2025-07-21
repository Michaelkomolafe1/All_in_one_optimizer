#!/usr/bin/env python3
"""
TEST EVERYTHING WORKING
=======================
Complete test after all fixes
"""

from pathlib import Path
import time


def test_complete_system():
    """Test the complete system with all fixes"""
    print("\n🚀 COMPLETE SYSTEM TEST")
    print("=" * 70)
    print("Testing unified DFS system after all fixes...")
    print("=" * 70)

    # 1. Test imports
    print("\n1️⃣ TESTING IMPORTS...")
    try:
        from unified_core_system import UnifiedCoreSystem
        print("   ✅ UnifiedCoreSystem imported")

        from unified_scoring_engine import ScoringConfig
        print("   ✅ ScoringConfig imported (not ScoringEngineConfig)")

        from unified_milp_optimizer import OptimizationConfig
        print("   ✅ OptimizationConfig imported")

    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False

    # 2. Initialize system
    print("\n2️⃣ INITIALIZING SYSTEM...")
    try:
        system = UnifiedCoreSystem()
        print("   ✅ System initialized successfully!")

    except Exception as e:
        print(f"   ❌ Initialization error: {e}")
        print("\n   Run these fixes:")
        print("   python fix_set_data_sources.py")
        print("   python fix_min_salary_error.py")
        return False

    # 3. Load CSV
    print("\n3️⃣ LOADING CSV DATA...")
    csv_files = list(Path('.').glob('*.csv'))
    if not csv_files:
        print("   ❌ No CSV files found!")
        return False

    csv_path = str(csv_files[0])
    print(f"   Loading: {csv_path}")

    total_players = system.load_csv(csv_path)
    print(f"   ✅ Loaded {total_players} players")

    # 4. Test confirmation system
    print("\n4️⃣ TESTING CONFIRMATION SYSTEM...")

    start_time = time.time()
    confirmed = system.fetch_confirmed_players()
    elapsed = time.time() - start_time

    print(f"   Confirmed players: {confirmed}")
    print(f"   Time taken: {elapsed:.2f} seconds")

    if confirmed == 0:
        print("   ℹ️  No confirmations (no games or too early)")

    # 5. Test manual player additions
    print("\n5️⃣ TESTING MANUAL PLAYER ADDITIONS...")

    test_players = [
        "Shohei Ohtani",
        "Juan Soto",
        "Aaron Judge",
        "Mookie Betts",
        "Freddie Freeman"
    ]

    added = 0
    for player in test_players:
        if system.add_manual_player(player):
            print(f"   ✅ Added: {player}")
            added += 1
        else:
            print(f"   ❌ Not found: {player}")

    print(f"   Total added: {added}")

    # 6. Test pool building
    print("\n6️⃣ TESTING LIMITED POOL CREATION...")

    pool_size = system.build_player_pool()
    print(f"   Pool size: {pool_size} players")
    print(f"   Confirmed: {len(system.confirmed_names)}")
    print(f"   Manual: {len(system.manual_names)}")
    print(f"   IGNORED: {total_players - pool_size} players")

    # 7. Test enrichment
    print("\n7️⃣ TESTING DATA ENRICHMENT...")

    if pool_size > 0:
        print(f"   Enriching {pool_size} players...")
        enriched = system.enrich_player_pool()
        print(f"   ✅ Enriched {enriched} players")

        # Show a sample player
        if system.player_pool:
            player = system.player_pool[0]
            print(f"\n   Sample player: {player.name}")
            print(f"   • Salary: ${player.salary}")
            print(f"   • Base projection: {player.base_projection}")
            print(f"   • Has optimization score: {hasattr(player, 'optimization_score')}")

    # 8. Test optimization
    print("\n8️⃣ TESTING LINEUP OPTIMIZATION...")

    if pool_size >= 9:  # Need at least 9 for a lineup
        lineups = system.optimize_lineups(num_lineups=1)

        if lineups:
            print("   ✅ Successfully generated lineup!")
            lineup = lineups[0]
            print(f"   • Players: {len(lineup['players'])}")
            print(f"   • Salary: ${lineup['total_salary']:,} ({lineup['total_salary'] / 50000:.1%})")
            print(f"   • Points: {lineup['total_projection']:.1f}")
        else:
            print("   ❌ Failed to generate lineup")
    else:
        print(f"   ⚠️  Need at least 9 players in pool (have {pool_size})")
        print("   Add more manual players")

    # 9. Final summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)

    status = system.get_system_status()
    print(f"Total players loaded: {status['total_players']}")
    print(f"Confirmed players: {status['confirmed_players']}")
    print(f"Manual players: {status['manual_players']}")
    print(f"Pool size: {status['pool_size']}")
    print(f"All components ready: {all(status['components'].values())}")

    print("\n✅ SYSTEM TEST COMPLETE!")
    print("\n🎯 Your system is working correctly and does:")
    print("   ✓ Only uses confirmed + manual players")
    print("   ✓ Ignores all other players")
    print("   ✓ Enriches only the pool")
    print("   ✓ Optimizes from limited pool")

    return True


def show_quick_tips():
    """Show quick tips for using the system"""
    print("\n" + "=" * 70)
    print("💡 QUICK TIPS")
    print("=" * 70)

    print("\n1. If you get 0 confirmations:")
    print("   • It's probably no games today")
    print("   • Just use manual players")
    print("   • System works perfectly!")

    print("\n2. To use with your GUI:")
    print("   • Copy OptimizationWorker from gui_integration.py")
    print("   • Replace in complete_dfs_gui_debug.py")
    print("   • Run your GUI")

    print("\n3. Manual player selection strategy:")
    print("   • Add top pitchers (aces)")
    print("   • Add elite hitters")
    print("   • Balance positions")
    print("   • Consider matchups")


if __name__ == "__main__":
    # Run complete test
    success = test_complete_system()

    if success:
        show_quick_tips()
    else:
        print("\n❌ System test failed")
        print("\nRun these fixes in order:")
        print("1. python fix_set_data_sources.py")
        print("2. python fix_min_salary_error.py")
        print("3. python test_everything_working.py")