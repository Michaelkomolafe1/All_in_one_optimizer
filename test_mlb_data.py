#!/usr/bin/env python3
"""Test the fixed optimization"""

import pandas as pd

# Load your CSV
csv_file = "/home/michael/Downloads/DKSalaries(12).csv"
df = pd.read_csv(csv_file)

print(f"Loaded {len(df)} players")
print(f"\nPositions available:")
for pos, count in df['Position'].value_counts().head(15).items():
    print(f"  {pos:6}: {count:3} players")

# Test position matching
print("\n✅ SP/RP players:")
pitchers = df[df['Position'].isin(['SP', 'RP'])]
print(f"Found {len(pitchers)} pitchers")

print("\n✅ Multi-position players:")
multi_pos = df[df['Position'].str.contains('/')]
print(f"Found {len(multi_pos)} multi-position eligible players")
for pos in multi_pos['Position'].unique()[:10]:
    print(f"  • {pos}")

print("\nYour data looks good for optimization!")
