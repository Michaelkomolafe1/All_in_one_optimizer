#!/usr/bin/env python3
"""
BULLETPROOF DFS LAUNCHER
========================
Launch the bulletproof DFS system with full GUI
"""

import sys
import os
from pathlib import Path

def main():
    print("🚀 LAUNCHING BULLETPROOF DFS SYSTEM")
    print("=" * 50)

    # Check if GUI is available
    gui_file = Path(__file__).parent / 'enhanced_dfs_gui.py'
    if not gui_file.exists():
        print("❌ GUI file not found!")
        return 1

    # Try to launch GUI
    try:
        print("🖥️ Starting Enhanced DFS GUI...")

        # Import and run GUI
        sys.path.insert(0, str(Path(__file__).parent))
        from enhanced_dfs_gui import main as gui_main

        return gui_main()

    except ImportError as e:
        print(f"❌ GUI import error: {e}")
        print("💡 Try: pip install PyQt5")
        return 1
    except Exception as e:
        print(f"❌ Launcher error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
