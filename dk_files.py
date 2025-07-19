#!/usr/bin/env python3
"""
FIND DRAFTKINGS CSV FILES
========================
Helps locate DraftKings CSV files in your Downloads folder
"""

import os
import glob
from pathlib import Path
from datetime import datetime


def find_dk_csvs():
    """Find all DraftKings CSV files in common locations"""
    print("🔍 SEARCHING FOR DRAFTKINGS CSV FILES...")
    print("=" * 60)

    # Common download locations
    possible_paths = [
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/downloads"),
        os.path.expanduser("~/Desktop"),
        "/home/michael/Downloads",  # Your specific path
        ".",  # Current directory
    ]

    all_csvs = []
    dk_csvs = []

    for path in possible_paths:
        if os.path.exists(path):
            print(f"\n📂 Checking: {path}")

            # Find all CSV files
            csv_pattern = os.path.join(path, "*.csv")
            csv_files = glob.glob(csv_pattern)

            # Also check with different cases
            csv_pattern2 = os.path.join(path, "*.CSV")
            csv_files.extend(glob.glob(csv_pattern2))

            # Remove duplicates
            csv_files = list(set(csv_files))

            if csv_files:
                print(f"   Found {len(csv_files)} CSV files")

                # Look for DraftKings files
                for csv_file in csv_files:
                    filename = os.path.basename(csv_file)

                    # Common DraftKings CSV patterns
                    if any(pattern in filename.lower() for pattern in
                           ['dksalaries', 'draftkings', 'dk_', 'showdown', 'classic']):
                        dk_csvs.append(csv_file)

                        # Get file info
                        stat = os.stat(csv_file)
                        size_mb = stat.st_size / (1024 * 1024)
                        mod_time = datetime.fromtimestamp(stat.st_mtime)

                        print(f"   ✅ DK CSV: {filename}")
                        print(f"      Path: {csv_file}")
                        print(f"      Size: {size_mb:.2f} MB")
                        print(f"      Modified: {mod_time.strftime('%Y-%m-%d %H:%M')}")

                    all_csvs.append(csv_file)
            else:
                print(f"   No CSV files found")

    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   Total CSV files found: {len(all_csvs)}")
    print(f"   DraftKings CSV files: {len(dk_csvs)}")

    if dk_csvs:
        print(f"\n✅ FOUND {len(dk_csvs)} DRAFTKINGS FILES:")
        for i, csv_path in enumerate(dk_csvs, 1):
            print(f"{i}. {csv_path}")

        # Show how to use in code
        print(f"\n📝 TO USE IN YOUR CODE:")
        print(f'csv_path = "{dk_csvs[0]}"')
        print(f'core.load_draftkings_csv(csv_path)')

        # Create a simple test script
        with open('test_with_csv.py', 'w') as f:
            f.write(f'''#!/usr/bin/env python3
"""Auto-generated test script with your CSV path"""

from bulletproof_dfs_core import BulletproofDFSCore

# Your DraftKings CSV
csv_path = "{dk_csvs[0]}"

# Initialize and load
core = BulletproofDFSCore()
if core.load_draftkings_csv(csv_path):
    print(f"✅ Loaded {{len(core.players)}} players")

    # Show first few players
    for i, player in enumerate(core.players[:5]):
        print(f"  {{i+1}}. {{player.name}} ({{player.team}}) - ${{player.salary}}")
else:
    print("❌ Failed to load CSV")
''')
        print(f"\n💾 Created test_with_csv.py with your CSV path")

    else:
        print(f"\n❌ NO DRAFTKINGS CSV FILES FOUND")
        print(f"\n💡 SUGGESTIONS:")
        print(f"1. Check if files are named differently (list all CSVs):")
        print(f"   - Look for files with 'salary', 'lineup', 'contest' in the name")
        print(f"2. Download a fresh CSV from DraftKings")
        print(f"3. Make sure files have .csv extension (not .xlsx)")

        if all_csvs:
            print(f"\n📄 ALL CSV FILES FOUND:")
            for csv in all_csvs[:10]:  # Show first 10
                print(f"   - {csv}")
            if len(all_csvs) > 10:
                print(f"   ... and {len(all_csvs) - 10} more")


def check_specific_file():
    """Check a specific file path"""
    print("\n\n🎯 CHECKING SPECIFIC FILE")
    print("=" * 60)

    # Try the path from your previous runs
    test_path = "/home/michael/Downloads/DKSalaries(6).csv"

    if os.path.exists(test_path):
        print(f"✅ Found: {test_path}")
        stat = os.stat(test_path)
        print(f"   Size: {stat.st_size / 1024:.1f} KB")
        print(f"   Full path: {os.path.abspath(test_path)}")

        # Show first few lines
        print(f"\n📄 First 3 lines:")
        with open(test_path, 'r') as f:
            for i in range(3):
                line = f.readline().strip()
                if line:
                    print(f"   {line}")
    else:
        print(f"❌ Not found: {test_path}")

        # Try variations
        base_path = "/home/michael/Downloads/"
        print(f"\n🔍 Looking for similar files in {base_path}")

        if os.path.exists(base_path):
            files = os.listdir(base_path)
            dk_files = [f for f in files if 'dk' in f.lower() and f.endswith('.csv')]

            if dk_files:
                print(f"Found {len(dk_files)} possible DK files:")
                for f in dk_files:
                    print(f"   - {f}")


if __name__ == "__main__":
    find_dk_csvs()
    check_specific_file()