#!/usr/bin/env python3
"""
Simple Advanced DFS Launcher
"""

import sys

def main():
    """Launch the advanced system"""

    print("🚀 ADVANCED DFS SYSTEM LAUNCHER")
    print("=" * 40)

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test mode
        print("🧪 Running test...")
        from advanced_dfs_wrapper import run_advanced_dfs_optimization
        from advanced_dfs_core import create_enhanced_test_data

        dk_file, dff_file = create_enhanced_test_data()

        lineup, score, summary = run_advanced_dfs_optimization(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input="Jorge Polanco, Christian Yelich"
        )

        if lineup:
            print(f"✅ Test successful: {len(lineup)} players, {score:.1f} score")
            print("🧠 Advanced algorithm working!")
        else:
            print("❌ Test failed")

        # Cleanup
        import os
        try:
            os.unlink(dk_file)
            os.unlink(dff_file)
        except:
            pass

    else:
        # GUI mode
        try:
            print("🖥️ Launching GUI...")
            import streamlined_dfs_gui
            return streamlined_dfs_gui.main()
        except Exception as e:
            print(f"❌ GUI launch failed: {e}")
            print("💡 Try: python launch_advanced.py test")
            return 1

if __name__ == "__main__":
    sys.exit(main())
