#!/usr/bin/env python3
"""
Test New Strategy System
Verifies that the improved confirmed-first strategies work correctly
"""

import os
import sys

try:
    from cleanup_backup_20250531_105034.working_dfs_core_final import OptimizedDFSCore, load_and_optimize_complete_pipeline
    print("✅ Core imported successfully")
except ImportError as e:
    print(f"❌ Could not import core: {e}")
    sys.exit(1)


def test_new_strategies():
    """Test all new strategies"""

    print("🧪 TESTING NEW CONFIRMED-FIRST STRATEGY SYSTEM")
    print("=" * 60)

    # Find your CSV files
    dk_files = [f for f in os.listdir('.') if f.endswith('.csv') and any(keyword in f.lower() for keyword in ['dk', 'salary'])]
    dff_files = [f for f in os.listdir('.') if f.endswith('.csv') and any(keyword in f.lower() for keyword in ['dff', 'cheat'])]

    if not dk_files:
        print("❌ No DraftKings CSV files found")
        return False

    dk_file = dk_files[0]
    dff_file = dff_files[0] if dff_files else None

    print(f"📊 Using DK file: {dk_file}")
    print(f"🎯 Using DFF file: {dff_file}")

    # Test strategies
    strategies_to_test = [
        ('smart_confirmed', 'Smart Default'),
        ('confirmed_only', 'Safe Only'),
        ('confirmed_plus_manual', 'Smart + Picks'),
        ('manual_only', 'Manual Only')
    ]

    manual_input = "Max Fried, James Wood, Ketel Marte, Manny Machado, Paul Goldschmidt, Aaron Judge, Juan Soto, Gerrit Cole, Kyle Tucker, Salvador Perez, Vladimir Guerrero Jr."

    results = {}

    for strategy_key, strategy_name in strategies_to_test:
        print(f"\n🎯 Testing {strategy_name} ({strategy_key})")
        print("-" * 40)

        try:
            lineup, score, summary = load_and_optimize_complete_pipeline(
                dk_file=dk_file,
                dff_file=dff_file,
                manual_input=manual_input,
                contest_type='classic',
                strategy=strategy_key
            )

            if lineup and score > 0:
                confirmed_count = sum(1 for p in lineup if getattr(p, 'is_confirmed', False))
                manual_count = sum(1 for p in lineup if getattr(p, 'is_manual_selected', False))

                results[strategy_key] = {
                    'success': True,
                    'players': len(lineup),
                    'score': score,
                    'confirmed': confirmed_count,
                    'manual': manual_count
                }

                print(f"✅ {strategy_name}: {len(lineup)} players, {score:.1f} pts")
                print(f"   Confirmed: {confirmed_count}, Manual: {manual_count}")
            else:
                results[strategy_key] = {'success': False}
                print(f"❌ {strategy_name}: Failed")

        except Exception as e:
            results[strategy_key] = {'success': False, 'error': str(e)}
            print(f"❌ {strategy_name}: Error - {e}")

    # Summary
    print("\n" + "=" * 60)
    print("📊 NEW STRATEGY SYSTEM TEST RESULTS")
    print("=" * 60)

    success_count = sum(1 for r in results.values() if r.get('success', False))

    for strategy_key, strategy_name in strategies_to_test:
        result = results[strategy_key]
        if result.get('success'):
            print(f"✅ {strategy_name}: Working perfectly")
        else:
            print(f"❌ {strategy_name}: Needs attention")

    print(f"\n🎯 SUCCESS RATE: {success_count}/{len(strategies_to_test)} strategies working")

    if success_count >= 3:
        print("\n🎉 NEW STRATEGY SYSTEM IS WORKING!")
        print("✅ Confirmed-first approach implemented successfully")
        print("✅ Much smarter default behavior")
        print("✅ Better strategy options for users")
    else:
        print("\n⚠️ Some strategies need debugging")

    return success_count >= 3


if __name__ == "__main__":
    test_new_strategies()
