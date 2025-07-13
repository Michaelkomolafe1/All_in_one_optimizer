#!/usr/bin/env python3
"""Fix cache and check DFF setup"""

# Fix 1: Ensure cache works
print("🔧 Fixing cache issue...")
cache_content = '''"""Cache manager for DFS optimizer"""

class DataCache:
    """Simple cache implementation"""
    def __init__(self):
        self.cache = {}

    def get(self, key, default=None):
        return self.cache.get(key, default)

    def set(self, key, value):
        self.cache[key] = value
        return True

    def clear(self):
        self.cache.clear()

# Global instance
cache = DataCache()
'''

with open('utils/cache_manager.py', 'w') as f:
    f.write(cache_content)

print("✅ Cache fixed!")

# Test recent form
try:
    from recent_form_analyzer import RecentFormAnalyzer
    from utils.cache_manager import cache

    analyzer = RecentFormAnalyzer(cache_manager=cache)
    print("✅ Recent Form Analyzer now working!")
except Exception as e:
    print(f"❌ Recent Form still has issues: {e}")

# Check for DFF files
import os
import glob

print("\n🔍 Looking for DFF/Cheatsheet files...")
possible_dff = []
for pattern in ['*DFF*.csv', '*dff*.csv', '*cheat*.csv', '*Cheat*.csv']:
    possible_dff.extend(glob.glob(pattern))

if possible_dff:
    print(f"✅ Found potential DFF files: {possible_dff}")
else:
    print("❌ No DFF files found")
    print("   To use DFF: Save your DFF cheatsheet as 'DFF_Cheatsheet.csv' in this directory")

# Check scoring weights
print("\n🔧 Checking scoring configuration...")
try:
    # Load config
    import json

    config_files = glob.glob('*config*.json')

    for cf in config_files:
        with open(cf, 'r') as f:
            config = json.load(f)
            if 'scoring_weights' in config:
                print(f"✅ Found scoring weights in {cf}:")
                for k, v in config['scoring_weights'].items():
                    print(f"   - {k}: {v}")
except:
    pass

print("\n✅ Setup check complete!")
print("\nTo use DFF rankings:")
print("1. Save your DFF CSV in this directory")
print("2. Name it something with 'DFF' or 'cheat' in the filename")
print("3. The GUI should detect it automatically or have a 'Load DFF' button")