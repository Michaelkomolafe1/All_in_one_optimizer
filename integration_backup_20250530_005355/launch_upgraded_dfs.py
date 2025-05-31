#!/usr/bin/env python3
"""
UPGRADED DFS Launcher - Now with Real Statcast Data
"""

import sys

def main():
    """Launch the UPGRADED DFS system with real Statcast data"""
    print("🔬 UPGRADED DFS SYSTEM LAUNCHER - REAL STATCAST DATA")
    print("=" * 60)

    # Check if we're running tests
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("🧪 Testing upgraded system with real Statcast data...")
        try:
            from old_files_backup_20250531_154026.upgraded_dfs_core import upgraded_pipeline_with_real_statcast
            from optimized_dfs_core import create_enhanced_test_data

            # Test with sample data
            dk_file, dff_file = create_enhanced_test_data()

            lineup, score, summary = upgraded_pipeline_with_real_statcast(
                dk_file=dk_file,
                dff_file=dff_file,
                manual_input="Kyle Tucker, Jorge Polanco",
                strategy='smart_confirmed'
            )

            if lineup and score > 0:
                print("✅ UPGRADED system test PASSED!")
                print(f"📊 Generated lineup: {len(lineup)} players, {score:.2f} score")

                # Check for real data
                real_count = sum(1 for p in lineup 
                               if hasattr(p, 'statcast_data') and 
                               'Baseball Savant' in p.statcast_data.get('data_source', ''))

                if real_count > 0:
                    print(f"🎉 REAL Baseball Savant data used for {real_count} players!")
                else:
                    print("⚡ Enhanced simulation used (real data requires pybaseball)")

                return 0
            else:
                print("❌ Upgraded system test FAILED!")
                return 1

        except Exception as e:
            print(f"❌ Test error: {e}")
            return 1

    # Launch the GUI with upgraded core
    try:
        print("🖥️ Launching Enhanced DFS GUI with REAL Statcast data...")

        # Patch the GUI to use upgraded core
        import enhanced_dfs_gui

        # Replace the import in the GUI module
        enhanced_dfs_gui.load_and_optimize_complete_pipeline = upgraded_pipeline_with_real_statcast

        return enhanced_dfs_gui.main()

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure enhanced_dfs_gui.py and upgraded_dfs_core.py exist")
        return 1
    except Exception as e:
        print(f"❌ Launch error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
