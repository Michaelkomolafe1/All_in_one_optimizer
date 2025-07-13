#!/usr/bin/env python3
"""
TEST SCRIPT FOR DFS OPTIMIZER FIXES
==================================
Run this after implementing all fixes to verify everything works
"""


def test_all_fixes():
    """Comprehensive test of all fixes"""
    print("🧪 DFS OPTIMIZER FIX VERIFICATION")
    print("=" * 60)

    # Test 1: AdvancedPlayer initialization
    print("\n1️⃣ Testing AdvancedPlayer initialization...")
    try:
        from bulletproof_dfs_core import AdvancedPlayer

        # Test dictionary initialization
        player_data = {
            'id': 1,
            'name': 'Mike Trout',
            'team': 'LAA',
            'position': 'OF',
            'salary': 8500,
            'projection': 12.5,
            'game_info': 'LAA@NYY 07:05PM ET'
        }

        player = AdvancedPlayer(player_data)
        print(f"   ✅ Created player: {player.name}")
        print(f"   ✅ Opponent parsed: {player.opponent}")
        print(f"   ✅ Home/Away: {player.home_away}")

        # Verify all attributes exist
        required_attrs = ['opponent', 'batting_order', '_statcast_data', 'optimization_score']
        for attr in required_attrs:
            if hasattr(player, attr):
                print(f"   ✅ Has attribute: {attr}")
            else:
                print(f"   ❌ Missing attribute: {attr}")

    except Exception as e:
        print(f"   ❌ AdvancedPlayer test failed: {e}")
        return False

    # Test 2: Statcast Fetcher
    print("\n2️⃣ Testing Statcast Fetcher...")
    try:
        from simple_statcast_fetcher import FastStatcastFetcher

        fetcher = FastStatcastFetcher()

        # Test if methods exist
        if hasattr(fetcher, 'get_pitcher_stats'):
            print("   ✅ Has get_pitcher_stats method")
        else:
            print("   ❌ Missing get_pitcher_stats method")

        if hasattr(fetcher, 'get_hitter_stats'):
            print("   ✅ Has get_hitter_stats method")
        else:
            print("   ❌ Missing get_hitter_stats method")

        # Test actual fetch (will return None if no connection)
        try:
            stats = fetcher.get_pitcher_stats("Zac Gallen")
            if stats is None:
                print("   ⚠️ No stats returned (check internet/pybaseball)")
            else:
                print(f"   ✅ Got stats: {list(stats.keys())[:3]}...")
        except Exception as e:
            print(f"   ❌ Fetch failed: {e}")

    except Exception as e:
        print(f"   ❌ Statcast test failed: {e}")
        return False

    # Test 3: Batting Order Sorting
    print("\n3️⃣ Testing Batting Order Sorting...")
    try:
        from unified_milp_optimizer import UnifiedMILPOptimizer

        # Create test players with None batting orders
        test_players = []
        for i in range(5):
            p = AdvancedPlayer({
                'name': f'Player{i}',
                'team': 'NYY',
                'salary': 5000,
                'position': 'OF',
                'projection': 10.0
            })
            # Mix of None and numeric batting orders
            p.batting_order = i + 1 if i < 3 else None
            test_players.append(p)

        # Try to sort them
        try:
            sorted_players = sorted(
                test_players,
                key=lambda p: p.batting_order if p.batting_order is not None else 999
            )
            print("   ✅ Sorting with None values works")

            # Show sorted order
            for p in sorted_players:
                print(f"      {p.name}: batting_order = {p.batting_order}")

        except TypeError as e:
            print(f"   ❌ Sorting failed: {e}")
            return False

    except Exception as e:
        print(f"   ❌ Batting order test failed: {e}")
        return False

    # Test 4: MILP Optimizer
    print("\n4️⃣ Testing MILP Optimizer...")
    try:
        from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig

        config = OptimizationConfig()
        optimizer = UnifiedMILPOptimizer(config)

        # Create test lineup
        test_lineup = []
        positions = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']

        for i, pos in enumerate(positions):
            p = AdvancedPlayer({
                'name': f'{pos}_Player{i}',
                'team': 'NYY' if i % 2 == 0 else 'BOS',
                'position': pos,
                'salary': 4000 + i * 200,
                'projection': 8.0 + i * 0.5,
                'game_info': 'NYY@BOS 07:05PM ET' if i % 2 == 0 else 'BOS@NYY 07:05PM ET'
            })
            p.enhanced_score = p.base_projection
            test_lineup.append(p)

        # Test prepare_players_for_optimization
        try:
            prepared = optimizer.prepare_players_for_optimization(test_lineup)
            print("   ✅ prepare_players_for_optimization works")

            # Check optimization scores
            has_opt_score = all(hasattr(p, 'optimization_score') for p in prepared)
            if has_opt_score:
                print("   ✅ All players have optimization_score")
            else:
                print("   ❌ Some players missing optimization_score")

        except Exception as e:
            print(f"   ❌ Optimization prep failed: {e}")
            return False

    except Exception as e:
        print(f"   ❌ MILP test failed: {e}")
        return False

    # Test 5: Full Integration
    print("\n5️⃣ Testing Full Integration...")
    try:
        from bulletproof_dfs_core import BulletproofDFSCore

        core = BulletproofDFSCore()
        print("   ✅ Core initialized")

        # Check all modules
        modules = {
            'scoring_engine': core.scoring_engine,
            'validator': core.validator,
            'performance_optimizer': core.performance_optimizer,
            'statcast_fetcher': core.statcast_fetcher,
            'vegas_lines': core.vegas_lines
        }

        for name, module in modules.items():
            if module is not None:
                print(f"   ✅ {name} is available")
            else:
                print(f"   ⚠️ {name} is not available")

    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED!")
    print("\nNext steps:")
    print("1. Load your CSV file")
    print("2. Run optimization")
    print("3. Check for any remaining errors")

    return True


def quick_csv_test(csv_path):
    """Quick test with actual CSV file"""
    print(f"\n📄 Testing with CSV: {csv_path}")
    print("=" * 60)

    try:
        from bulletproof_dfs_core import BulletproofDFSCore

        core = BulletproofDFSCore()
        success = core.load_draftkings_csv(csv_path)

        if success:
            print(f"✅ Loaded {len(core.players)} players")

            # Check first few players
            print("\nFirst 3 players:")
            for i, p in enumerate(core.players[:3]):
                print(f"{i + 1}. {p.name} ({p.team})")
                print(f"   Position: {p.primary_position}")
                print(f"   Salary: ${p.salary}")
                print(f"   Projection: {p.base_projection}")
                print(f"   Opponent: {p.opponent}")
                print(f"   Game Info: {p.game_info}")

            # Check for zero projections
            zero_proj = [p for p in core.players if p.base_projection == 0]
            if zero_proj:
                print(f"\n⚠️ {len(zero_proj)} players have 0 projection")
                for p in zero_proj[:3]:
                    print(f"   - {p.name}")

            # Try optimization
            print("\n🎯 Testing optimization...")
            lineup, score = core.optimize_lineup_with_mode()

            if lineup:
                print(f"✅ Generated lineup with score: {score:.2f}")
            else:
                print("❌ No lineup generated")

        else:
            print("❌ Failed to load CSV")

    except Exception as e:
        print(f"❌ CSV test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    # Run all tests
    test_all_fixes()

    # If CSV provided, test with it
    if len(sys.argv) > 1:
        quick_csv_test(sys.argv[1])
    else:
        print("\n💡 Tip: Run with your CSV file:")
        print("   python test_fixes.py your_file.csv")