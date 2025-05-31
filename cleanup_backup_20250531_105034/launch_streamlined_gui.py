#!/usr/bin/env python3
"""
Streamlined DFS GUI Launcher
Launches only the streamlined DFS GUI system
"""

import sys
import os

def main():
    """Launch the streamlined DFS GUI"""
    print("🚀 STREAMLINED DFS OPTIMIZER")
    print("=" * 40)

    try:
        print("⚡ Launching Streamlined DFS GUI...")
        from streamlined_dfs_gui import main as streamlined_main
        return streamlined_main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure streamlined_dfs_gui.py exists")
    except Exception as e:
        print(f"❌ Error launching GUI: {e}")
        print("💡 Try running: python streamlined_dfs_gui.py")

    return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
        sys.exit(0)
