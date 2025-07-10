#!/usr/bin/env python3
"""
FIXED Enhanced DFS Launcher
Handles all import edge cases properly
"""

import sys
import os
from pathlib import Path

def main():
    """Main launcher with comprehensive error handling"""
    print("🚀 ENHANCED DFS OPTIMIZER (FIXED)")
    print("=" * 50)
    print("✅ Vegas Lines | ✅ Team Stacking | ✅ Enhanced Statcast")
    print("=" * 50)

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        return run_comprehensive_test()
    else:
        return launch_fixed_gui()

def run_comprehensive_test():
    """Run comprehensive test with multiple fallbacks"""
    print("\n🧪 Running comprehensive system test...")

    # Test 1: Try enhanced core
    try:
        print("🔄 Testing enhanced core...")
        from enhanced_dfs_core import (
            load_and_optimize_with_enhanced_features,
            create_enhanced_test_data,
            StackingConfig
        )

        print("✅ Enhanced core imported successfully")

        # Run enhanced test
        dk_file, dff_file = create_enhanced_test_data()

        stack_config = StackingConfig()
        stack_config.enable_stacking = True
        stack_config.min_stack_size = 2
        stack_config.max_stack_size = 3

        lineup, score, summary = load_and_optimize_with_enhanced_features(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input="Kyle Tucker, Jorge Polanco",
            contest_type='classic',
            strategy='smart_confirmed',
            enable_stacking=True,
            enable_vegas=True,
            stack_config=stack_config
        )

        if lineup and score > 0:
            print(f"✅ ENHANCED TEST PASSED!")
            print(f"📊 Generated {len(lineup)} player lineup")
            print(f"🎯 Total score: {score:.2f}")

            # Check features
            team_counts = {}
            vegas_count = 0
            statcast_count = 0

            for player in lineup:
                team = getattr(player, 'team', 'UNK')
                team_counts[team] = team_counts.get(team, 0) + 1

                if hasattr(player, 'implied_team_score') and player.implied_team_score > 4.5:
                    vegas_count += 1
                if hasattr(player, 'statcast_data') and player.statcast_data:
                    statcast_count += 1

            stacks = {t: c for t, c in team_counts.items() if c >= 2}
            if stacks:
                print(f"🏆 Team stacks: {stacks}")

            print(f"💰 Vegas data: {vegas_count} players")
            print(f"🔬 Statcast data: {statcast_count} players")

            print("\n🎉 ENHANCED SYSTEM WORKING PERFECTLY!")
            return 0

    except Exception as e:
        print(f"⚠️ Enhanced core test failed: {e}")
        print("🔄 Falling back to base system test...")

    # Test 2: Try base core
    try:
        print("🔄 Testing base core...")
        from optimized_dfs_core_with_statcast import (
            load_and_optimize_complete_pipeline,
            create_enhanced_test_data
        )

        print("✅ Base core imported successfully")

        dk_file, dff_file = create_enhanced_test_data()

        lineup, score, summary = load_and_optimize_complete_pipeline(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input="Kyle Tucker, Jorge Polanco",
            contest_type='classic',
            strategy='smart_confirmed'
        )

        if lineup and score > 0:
            print(f"✅ BASE TEST PASSED!")
            print(f"📊 Generated {len(lineup)} player lineup")
            print(f"🎯 Total score: {score:.2f}")
            print("\n💡 System working with base features")
            return 0

    except Exception as e:
        print(f"❌ Base core test failed: {e}")

    print("❌ ALL TESTS FAILED")
    return 1

def launch_fixed_gui():
    """Launch GUI with comprehensive error handling"""
    print("\n🖥️ Launching GUI with fixed imports...")

    try:
        # Import GUI
        import enhanced_dfs_gui
        print("✅ GUI module imported")

        # Try to patch with enhanced system
        enhanced_patched = False
        try:
            from enhanced_dfs_core import load_and_optimize_with_enhanced_features, StackingConfig

            def enhanced_wrapper(dk_file, dff_file=None, manual_input="", 
                                contest_type='classic', strategy='smart_confirmed'):
                """Enhanced wrapper with stacking"""
                stack_config = StackingConfig()
                stack_config.enable_stacking = True
                stack_config.min_stack_size = 2
                stack_config.max_stack_size = 4

                return load_and_optimize_with_enhanced_features(
                    dk_file=dk_file,
                    dff_file=dff_file,
                    manual_input=manual_input,
                    contest_type=contest_type,
                    strategy=strategy,
                    enable_stacking=True,
                    enable_vegas=True,
                    stack_config=stack_config
                )

            enhanced_dfs_gui.load_and_optimize_complete_pipeline = enhanced_wrapper
            enhanced_patched = True
            print("✅ GUI patched with enhanced features")

        except ImportError:
            print("⚠️ Enhanced core not available for GUI")

        # Fallback to base system
        if not enhanced_patched:
            try:
                from optimized_dfs_core_with_statcast import load_and_optimize_complete_pipeline
                enhanced_dfs_gui.load_and_optimize_complete_pipeline = load_and_optimize_complete_pipeline
                print("✅ GUI patched with base system")
            except ImportError:
                print("❌ No working core system found")
                return 1

        # Launch GUI
        return enhanced_dfs_gui.main()

    except Exception as e:
        print(f"❌ GUI launch failed: {e}")
        print("\n💡 Try running the test first: python launch_enhanced_dfs_fixed.py test")
        return 1

if __name__ == "__main__":
    sys.exit(main())
