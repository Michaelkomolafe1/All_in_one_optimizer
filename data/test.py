#!/usr/bin/env python3
"""
SIMPLE CSV TEST - ALL IN ONE FILE
=================================
No imports needed! Just run this file.
"""

import pandas as pd
import os


def test_csv(filepath=None):
    """Test loading a DraftKings CSV"""

    # If no file provided, look in Downloads
    if not filepath:
        downloads = os.path.expanduser("~/Downloads")
        print(f"Looking in {downloads} for CSV files...")

        # Find DraftKings files
        for file in os.listdir(downloads):
            if "DKSalaries" in file and file.endswith(".csv"):
                filepath = os.path.join(downloads, file)
                print(f"Found: {file}")
                break

    if not filepath:
        print("❌ No CSV file found!")
        print("Usage: python3 simple_csv_test.py path/to/DKSalaries.csv")
        return

    print(f"\n📂 Loading: {filepath}")

    try:
        # Load CSV
        df = pd.read_csv(filepath)
        print(f"✅ Loaded {len(df)} rows")

        # Show columns
        print(f"\n📋 Columns: {', '.join(df.columns)}")

        # Check slate type
        if 'Position' in df.columns:
            positions = df['Position'].unique()
            if 'CPT' in positions or 'UTIL' in positions:
                print("\n⚡ SHOWDOWN slate!")
                # Filter to UTIL only
                df = df[df['Position'] == 'UTIL']
                print(f"   Using {len(df)} UTIL players")
            else:
                print("\n📋 CLASSIC slate")

        # Show sample players
        print("\n👥 Sample Players:")
        for i, row in df.head(10).iterrows():
            name = row.get('Name', '')
            pos = row.get('Position', '')
            team = row.get('TeamAbbrev', row.get('Team', ''))
            salary = row.get('Salary', 0)
            proj = row.get('AvgPointsPerGame', 0)

            print(f"{name:20} {pos:4} {team:3} ${salary:6,} {proj:5.1f}pts")

        # Team summary
        print(f"\n🏟️  Teams: {df['TeamAbbrev'].nunique() if 'TeamAbbrev' in df else 'Unknown'}")

        # Salary range
        if 'Salary' in df:
            print(f"💰 Salary range: ${df['Salary'].min():,} - ${df['Salary'].max():,}")
            print(f"💰 Average: ${df['Salary'].mean():,.0f}")

        print("\n✅ CSV loaded successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys

    # Check if file provided
    if len(sys.argv) > 1:
        test_csv(sys.argv[1])
    else:
        # Auto-find in Downloads
        test_csv()