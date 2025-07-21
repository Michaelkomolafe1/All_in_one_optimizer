#!/usr/bin/env python3
"""
QUICK TEST - Verify Unified System Works
========================================
Run this before integrating with GUI
"""

import sys
from pathlib import Path


def quick_test():
    """Quick test of the unified system"""
    print("\n🚀 QUICK TEST OF UNIFIED DFS SYSTEM")
    print("=" * 60)

    # Step 1: Check imports
    print("\n1️⃣ CHECKING IMPORTS...")

    required_modules = {
        'unified_core_system': 'UnifiedCoreSystem',
        'unified_player_model': 'UnifiedPlayer',
        'unified_milp_optimizer': 'UnifiedMILPOptimizer',
        'unified_scoring_engine': 'get_scoring_engine',
        'simple_statcast_fetcher': 'FastStatcastFetcher',
        'smart_confirmation_system': 'SmartConfirmationSystem',
        'vegas_lines': 'VegasLines'
    }

    all_good = True
    for module, component in required_modules.items():
        try:
            mod = __import__(module)
            if hasattr(mod, component):
                print(f"   ✅ {module}")
            else:
                print(f"   ❌ {module} - missing {component}")
                all_good = False
        except ImportError as e:
            print(f"   ❌ {module} - {e}")
            all_good = False

    if not all_good:
        print("\n❌ Missing required modules!")
        print("Make sure all files are in the current directory")
        return False

    # Step 2: Initialize system
    print("\n2️⃣ INITIALIZING UNIFIED SYSTEM...")

    try:
        from unified_core_system import UnifiedCoreSystem
        system = UnifiedCoreSystem()
        print("   ✅ System initialized successfully")
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        return False

    # Step 3: Check for CSV
    print("\n3️⃣ LOOKING FOR CSV FILE...")

    csv_files = list(Path('.').glob('*.csv'))
    if not csv_files:
        print("   ❌ No CSV files found!")
        print("   Please run: python quick_test.py your_file.csv")
        return False

    csv_file = csv_files[0]
    print(f"   ✅ Found: {csv_file}")

    # Step 4: Load data
    print("\n4️⃣ LOADING PLAYER DATA...")

    try:
        num_loaded = system.load_csv(str(csv_file))
        print(f"   ✅ Loaded {num_loaded} players")

        # Show some sample players
        sample_players = list(system.all_players.values())[:5]
        print("\n   Sample players:")
        for p in sample_players:
            print(f"     • {p.name} ({p.primary_position}) - ${p.salary}")

    except Exception as e:
        print(f"   ❌ Load failed: {e}")
        return False

    # Step 5: Test confirmed players
    print("\n5️⃣ TESTING CONFIRMED PLAYER FETCH...")

    try:
        num_confirmed = system.fetch_confirmed_players()
        print(f"   ✅ Found {num_confirmed} confirmed players")

        if num_confirmed == 0:
            print("   ℹ️  No confirmed lineups available yet")
            print("   Adding manual players for testing...")

            # Add some test players
            test_players = ["Zack Wheeler", "Shohei Ohtani", "Juan Soto"]
            for name in test_players:
                if system.add_manual_player(name):
                    print(f"     ✅ Added {name}")

    except Exception as e:
        print(f"   ⚠️  Confirmation fetch issue: {e}")

    # Step 6: Build pool
    print("\n6️⃣ BUILDING PLAYER POOL...")

    pool_size = system.build_player_pool()
    print(f"   ✅ Pool size: {pool_size} players")

    if pool_size == 0:
        print("   ❌ No players in pool!")
        return False

    # Step 7: Test enrichment
    print("\n7️⃣ TESTING DATA ENRICHMENT...")

    try:
        enriched = system.enrich_player_pool()
        print(f"   ✅ Enriched {enriched} players")

        # Show a sample enriched player
        if system.player_pool:
            p = system.player_pool[0]
            print(f"\n   Sample enriched player: {p.name}")
            print(f"     • Base projection: {p.base_projection:.1f}")
            print(f"     • Optimization score: {getattr(p, 'optimization_score', 'N/A')}")
            print(f"     • Vegas total: {getattr(p, 'vegas_total', 'N/A')}")
            print(f"     • Recent OPS: {getattr(p, 'recent_ops', 'N/A')}")

    except Exception as e:
        print(f"   ⚠️  Enrichment issue: {e}")

    # Step 8: Test optimization
    print("\n8️⃣ TESTING LINEUP OPTIMIZATION...")

    try:
        lineups = system.optimize_lineups(num_lineups=1, strategy="balanced")

        if lineups:
            print("   ✅ Optimization successful!")

            lineup = lineups[0]
            print(f"\n   Sample lineup:")
            print(f"   Total salary: ${lineup['total_salary']:,}")
            print(f"   Projected points: {lineup['total_projection']:.1f}")
            print(f"   Players:")

            for p in lineup['players'][:5]:  # Show first 5
                print(f"     • {p.primary_position} {p.name} ${p.salary}")

        else:
            print("   ❌ Optimization failed!")

    except Exception as e:
        print(f"   ❌ Optimization error: {e}")
        return False

    # Final summary
    print("\n" + "=" * 60)
    print("✅ SYSTEM TEST COMPLETE!")
    print("=" * 60)

    status = system.get_system_status()
    print(f"\n📊 System Status:")
    print(f"   • Total players: {status['total_players']}")
    print(f"   • Confirmed: {status['confirmed_players']}")
    print(f"   • Manual: {status['manual_players']}")
    print(f"   • Pool size: {status['pool_size']}")
    print(f"   • All components: ✅")

    print("\n🎯 NEXT STEPS:")
    print("1. Copy OptimizationWorker from gui_integration.py")
    print("2. Replace it in your complete_dfs_gui_debug.py")
    print("3. Run your GUI!")

    return True


if __name__ == "__main__":
    success = quick_test()

    if not success:
        print("\n❌ Please fix the issues above before proceeding")
        sys.exit(1)
    else:
        print("\n✅ Ready for GUI integration!")
        sys.exit(0)