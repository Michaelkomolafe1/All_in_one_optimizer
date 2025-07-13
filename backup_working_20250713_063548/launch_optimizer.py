#!/usr/bin/env python3
"""
DFS Optimizer - Main Launcher
Simple script to launch the optimizer
"""

import subprocess
import sys


def main():
    print("🚀 Launching DFS Optimizer...")

    try:
        # Try to launch the GUI
        subprocess.run([sys.executable, "enhanced_dfs_gui.py"])
    except Exception as e:
        print(f"Error launching GUI: {e}")
        print("Try running: python enhanced_dfs_gui.py directly")

if __name__ == "__main__":
    main()
