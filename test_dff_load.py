#!/usr/bin/env python3
"""Test DFF file loading"""

import pandas as pd
import os

dff_file = "DFF_MLB_cheatsheet_202507122.csv"

print(f"🔍 Testing DFF file: {dff_file}")
print("="*50)

# Check if file exists
if not os.path.exists(dff_file):
    print(f"❌ File not found: {dff_file}")
    exit(1)

# Load the file
try:
    df = pd.read_csv(dff_file)
    print(f"✅ Successfully loaded DFF file")
    print(f"📊 Shape: {df.shape[0]} players, {df.shape[1]} columns")
    print(f"\n📋 Columns found:")
    for col in df.columns:
        print(f"   - {col}")
    
    # Show sample data
    print(f"\n👀 First 5 players:")
    print(df.head())
    
    # Check for required columns
    required_cols = ['Name', 'Projection', 'Salary']
    missing = [col for col in required_cols if col not in df.columns and not any(col.lower() in c.lower() for c in df.columns)]
    
    if missing:
        print(f"\n⚠️  Missing expected columns: {missing}")
    else:
        print(f"\n✅ All expected columns found")
        
    # Check for player name format
    if 'Name' in df.columns or any('name' in col.lower() for col in df.columns):
        name_col = next((col for col in df.columns if 'name' in col.lower()), 'Name')
        print(f"\n📝 Sample player names:")
        for name in df[name_col].head(10):
            print(f"   - {name}")
            
except Exception as e:
    print(f"❌ Error loading DFF file: {e}")

# Now check if it was integrated
print("\n🔍 Checking integration with optimizer...")

try:
    from bulletproof_dfs_core import BulletproofDFSCore
    
    core = BulletproofDFSCore()
    
    # Check if apply_dff_rankings exists and works
    if hasattr(core, 'apply_dff_rankings'):
        print("✅ DFF integration method found")
        
        # Try to apply it
        result = core.apply_dff_rankings(dff_file)
        if result:
            print("✅ DFF rankings applied successfully!")
        else:
            print("❌ DFF rankings failed to apply")
    else:
        print("❌ No DFF integration method found")
        
except Exception as e:
    print(f"❌ Error testing integration: {e}")
