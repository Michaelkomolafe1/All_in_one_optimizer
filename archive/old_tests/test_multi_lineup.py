#!/usr/bin/env python3
"""
Simple test to verify multi-lineup works
"""

from bulletproof_dfs_core import BulletproofDFSCore

print("🧪 Testing multi-lineup generation...")

# Create core
core = BulletproofDFSCore()

# Load a CSV
csv_file = "DKSalaries_good.csv"  # Update with your CSV
if core.load_draftkings_csv(csv_file):
    print("✅ Loaded CSV")

    # Try to generate 3 lineups
    print("\nGenerating 3 test lineups...")
    lineups = core.generate_multiple_lineups(3)

    if lineups:
        print(f"✅ Generated {len(lineups)} lineups!")
    else:
        print("❌ Multi-lineup generation failed")
else:
    print("❌ Could not load CSV")
