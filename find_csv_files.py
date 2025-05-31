#!/usr/bin/env python3
import os
import glob

def find_csv_files():
    """Find CSV files in various locations"""

    # Check current directory
    current_csv = glob.glob("*.csv")

    # Check common download locations
    downloads_csv = glob.glob(os.path.expanduser("~/Downloads/*.csv"))

    # Check desktop
    desktop_csv = glob.glob(os.path.expanduser("~/Desktop/*.csv"))

    # Check Documents
    docs_csv = glob.glob(os.path.expanduser("~/Documents/*.csv"))

    all_csv = current_csv + downloads_csv + desktop_csv + docs_csv

    print(f"🔍 Found {len(all_csv)} CSV files:")

    dk_files = []
    dff_files = []

    for i, file in enumerate(all_csv):
        size = os.path.getsize(file) / 1024
        filename = os.path.basename(file)
        print(f"   {i+1}. {filename} ({size:.1f} KB) - {file}")

        # Categorize files
        if any(keyword in filename.lower() for keyword in ['dk', 'salary', 'draftkings']):
            dk_files.append(file)
        elif any(keyword in filename.lower() for keyword in ['dff', 'cheat', 'projection']):
            dff_files.append(file)

    print(f"\n📊 Potential DraftKings files: {len(dk_files)}")
    for file in dk_files:
        print(f"   {os.path.basename(file)}")

    print(f"\n🎯 Potential DFF files: {len(dff_files)}")
    for file in dff_files:
        print(f"   {os.path.basename(file)}")

if __name__ == "__main__":
    find_csv_files()
