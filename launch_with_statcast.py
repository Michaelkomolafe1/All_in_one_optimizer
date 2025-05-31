#!/usr/bin/env python3
"""
Simple Launcher - Uses your core with real Statcast data
"""

import sys

def main():
    """Launch your system with real Statcast data"""
    print("🚀 LAUNCHING DFS OPTIMIZER WITH REAL STATCAST DATA")
    print("=" * 60)

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("🧪 Running test with real Statcast data...")

        try:
            from optimized_dfs_core_with_statcast import (
                load_and_optimize_complete_pipeline,
                create_enhanced_test_data
            )

            # Create test data
            dk_file, dff_file = create_enhanced_test_data()

            # Run optimization with real Statcast
            lineup, score, summary = load_and_optimize_complete_pipeline(
                dk_file=dk_file,
                dff_file=dff_file,
                manual_input="Kyle Tucker, Jorge Polanco",
                contest_type='classic',
                strategy='smart_confirmed'
            )

            if lineup and score > 0:
                print(f"✅ Test PASSED!")
                print(f"📊 Lineup: {len(lineup)} players, {score:.2f} score")

                # Check for real data
                real_count = sum(1 for p in lineup 
                               if hasattr(p, 'statcast_data') and 
                               'Baseball Savant' in p.statcast_data.get('data_source', ''))

                print(f"🌐 Real Statcast data: {real_count} players")
                print(f"⚡ Enhanced simulation: {len(lineup) - real_count} players")

                return 0
            else:
                print("❌ Test FAILED!")
                return 1

        except Exception as e:
            print(f"❌ Test error: {e}")
            return 1

    # Launch your GUI
    try:
        print("🖥️ Launching GUI with real Statcast integration...")

        # Update the GUI to use the enhanced core
        import enhanced_dfs_gui

        # Patch the GUI to use the enhanced pipeline
        from optimized_dfs_core_with_statcast import load_and_optimize_complete_pipeline
        enhanced_dfs_gui.load_and_optimize_complete_pipeline = load_and_optimize_complete_pipeline

        return enhanced_dfs_gui.main()

    except ImportError:
        print("❌ GUI not available")
        print("💡 Your core system is ready - just import optimized_dfs_core_with_statcast")
        return 0
    except Exception as e:
        print(f"❌ Launch error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
