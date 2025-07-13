#!/usr/bin/env python3
"""Fix DFF to handle first_name and last_name columns"""

import re

# Read the bulletproof_dfs_core.py file
with open('bulletproof_dfs_core.py', 'r') as f:
    content = f.read()

# Find the apply_dff_rankings method and add handling for first_name/last_name
# Look for where it reads the CSV
pattern = r'(df = pd\.read_csv\(dff_file_path\))'
replacement = '''df = pd.read_csv(dff_file_path)
            
            # Handle separate first_name and last_name columns
            if 'first_name' in df.columns and 'last_name' in df.columns:
                df['name'] = df['first_name'] + ' ' + df['last_name']
                print("✅ Combined first_name and last_name into 'name' column")'''

content = re.sub(pattern, replacement, content, count=1)

# Write back
with open('bulletproof_dfs_core.py', 'w') as f:
    f.write(content)

print("✅ Fixed DFF name column handling")
print("\nNow try loading the DFF file again in the GUI!")
