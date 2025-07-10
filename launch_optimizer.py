#!/usr/bin/env python3
"""DFS Optimizer - Main Launcher"""

import sys
from pathlib import Path

def main():
    """Launch the DFS Optimizer GUI"""
    try:
        from enhanced_dfs_gui import main as gui_main
        print("🚀 Launching DFS Optimizer...")
        return gui_main()
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
