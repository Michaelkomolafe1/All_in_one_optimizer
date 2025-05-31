#!/usr/bin/env python3
"""
Optimized DFS Launcher - Works with fixed system
"""

import sys

def main():
    """Launch the optimized DFS system"""
    print("🚀 OPTIMIZED DFS SYSTEM LAUNCHER")
    print("=" * 40)

    # Check if we're running tests
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("🧪 Running system test...")
        try:
            from optimized_dfs_core import test_system
            success = test_system()
            if success:
                print("✅ System test PASSED!")
                return 0
            else:
                print("❌ System test FAILED!")
                return 1
        except Exception as e:
            print(f"❌ Test error: {e}")
            return 1

    # Launch the GUI
    try:
        print("🖥️ Launching Enhanced DFS GUI...")
        from enhanced_dfs_gui import main as gui_main
        return gui_main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure optimized_dfs_core.py and enhanced_dfs_gui.py exist")
        return 1
    except Exception as e:
        print(f"❌ Launch error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
