#!/usr/bin/env python3
"""Fix all sorting issues with None values"""

import re

files_to_check = [
    'unified_milp_optimizer.py',
    'bulletproof_dfs_core.py',
    'unified_player_model.py',
    'optimal_lineup_optimizer.py'
]

fixes_made = 0

for filename in files_to_check:
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        original = content
        
        # Fix 1: batting_order sorting
        content = re.sub(
            r'getattr\(([^,]+),\s*"batting_order",\s*(\d+)\)',
            r'(getattr(\1, "batting_order", None) or \2)',
            content
        )
        
        # Fix 2: Any numeric sorting with potential None
        content = re.sub(
            r'key=lambda\s+(\w+):\s+(\w+)\.(\w+_score|score|value|salary)',
            r'key=lambda \1: (\2.\3 if \2.\3 is not None else 0)',
            content
        )
        
        # Fix 3: getattr that might return None for sorting
        content = re.sub(
            r'sorted\(([^,]+),\s*key=lambda\s+(\w+):\s+getattr\((\w+),\s*["\'](\w+)["\']\)\)',
            r'sorted(\1, key=lambda \2: (getattr(\3, "\4") if getattr(\3, "\4") is not None else 0))',
            content
        )
        
        if content != original:
            with open(filename, 'w') as f:
                f.write(content)
            fixes_made += 1
            print(f"✅ Fixed sorting issues in {filename}")
    
    except FileNotFoundError:
        print(f"⚠️  {filename} not found")

print(f"\n✅ Fixed {fixes_made} files")

# Additional safety check for common None comparison patterns
print("\n🔍 Checking for remaining potential None comparison issues...")

for filename in files_to_check:
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # Check for sorted() calls that might have issues
            if 'sorted(' in line and 'key=' in line and 'or' not in line:
                if any(attr in line for attr in ['score', 'value', 'order', 'salary']):
                    print(f"⚠️  Potential issue in {filename}:{i} - {line.strip()}")
    except:
        pass
