#!/usr/bin/env python3
"""
🚀 Quick Start Script for Auto-Fixed DFS Optimizer
Run this for instant DFS optimization with your data
"""

import sys
from pathlib import Path

def quick_start():
    """Quick start with automatic file detection"""
    print("🚀 DFS Optimizer Quick Start")
    print("=" * 40)

    # Auto-detect DraftKings files
    dk_files = list(Path('.').glob('*DK*.csv')) + list(Path('.').glob('*draftkings*.csv'))
    dff_files = list(Path('.').glob('*DFF*.csv')) + list(Path('.').glob('*cheat*.csv'))

    if dk_files:
        dk_file = dk_files[0]
        print(f"📁 Found DK file: {dk_file}")

        if dff_files:
            dff_file = dff_files[0] 
            print(f"🎯 Found DFF file: {dff_file}")
            print(f"⚡ Running optimization with DFF data...")

            import subprocess
            result = subprocess.run([
                sys.executable, 'main.py', '--cli', '--dk', str(dk_file), 
                '--dff-cheat-sheet', str(dff_file)
            ])
            return result.returncode
        else:
            print(f"⚡ Running optimization without DFF data...")

            import subprocess
            result = subprocess.run([
                sys.executable, 'main.py', '--cli', '--dk', str(dk_file)
            ])
            return result.returncode
    else:
        print("❌ No DraftKings CSV files found!")
        print("💡 Place your DKSalaries.csv file in this directory")
        print("💡 Or run: python main.py --gui")
        return 1

if __name__ == "__main__":
    sys.exit(quick_start())
