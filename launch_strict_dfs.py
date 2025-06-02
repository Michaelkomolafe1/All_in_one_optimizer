#!/usr/bin/env python3
"""
DFS Optimizer Launcher - Strict System
=====================================
🔒 Guaranteed NO unconfirmed player leaks
🚀 One-click launcher for the fixed system
"""

import sys
import os

def main():
    """Launch the strict DFS optimizer"""
    print("🚀 LAUNCHING STRICT DFS OPTIMIZER")
    print("=" * 50)
    print("🔒 Bulletproof confirmed-only system")
    print("🚫 ZERO unconfirmed player leaks")
    print("=" * 50)

    try:
        # Launch the strict GUI
        from strict_dfs_gui import main as gui_main
        return gui_main()

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all required files are in the same directory:")
        print("   - strict_dfs_core.py")
        print("   - strict_dfs_gui.py") 
        print("   - dfs_data.py")
        print("   - vegas_lines.py")
        print("   - confirmed_lineups.py")
        print("   - simple_statcast_fetcher.py")
        return 1

    except Exception as e:
        print(f"❌ Launch error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
