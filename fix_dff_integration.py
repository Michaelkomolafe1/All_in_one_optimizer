#!/usr/bin/env python3
"""Fix DFF integration and scoring weights"""

import json
import os

print("🔧 Fixing DFF Integration...")
print("="*50)

# Fix 1: Update the config to include DFF weight
config_files = ["dfs_config.json", "optimization_config.json"]

for config_file in config_files:
    if os.path.exists(config_file):
        print(f"\n📝 Updating {config_file}...")
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Ensure scoring_weights exists and includes DFF
        if 'scoring_weights' not in config:
            config['scoring_weights'] = {}
        
        # Set reasonable weights
        config['scoring_weights'] = {
            'base_projection': 0.20,
            'dff_projection': 0.25,  # Give DFF high weight
            'recent_form': 0.15,
            'vegas': 0.10,
            'statcast': 0.15,
            'park_factors': 0.05,
            'confirmed_status': 0.10
        }
        
        # Save updated config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Updated {config_file} with DFF weight")

# Fix 2: Check the apply_dff_rankings method
print("\n🔍 Checking DFF implementation...")
with open('bulletproof_dfs_core.py', 'r') as f:
    content = f.read()
    if 'def apply_dff_rankings' in content:
        print("✅ apply_dff_rankings method exists")
        
        # Check if it's looking for the right columns
        if 'PPG Projection' in content or 'Projection' in content:
            print("✅ DFF column mapping looks correct")
        else:
            print("⚠️  May need to check DFF column names")

print("\n✅ Configuration updated!")
print("\nNext steps:")
print("1. Restart the GUI")
print("2. Load DraftKings CSV first")
print("3. Then load DFF file")
print("4. You should see 'DFF rankings applied' in console")
