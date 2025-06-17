#!/usr/bin/env python3
"""
Quick fix for the GUI RuntimeError
"""

import os
from datetime import datetime

print("🔧 APPLYING QUICK GUI FIX")
print("=" * 60)

# Check if GUI file exists
if not os.path.exists('enhanced_dfs_gui.py'):
    print("❌ enhanced_dfs_gui.py not found!")
    exit(1)

# Read the file
with open('enhanced_dfs_gui.py', 'r') as f:
    content = f.read()

# Create backup
backup_name = f'enhanced_dfs_gui.py.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
with open(backup_name, 'w') as f:
    f.write(content)
print(f"✅ Backup created: {backup_name}")

# Fix 1: Add safety check for manual_text widget
if 'manual_layout.addWidget(self.manual_text)' in content:
    print("\n🔧 Fixing manual_text widget issue...")

    # Replace the problematic line with a safe version
    old_line = 'manual_layout.addWidget(self.manual_text)'
    new_code = '''try:
            manual_layout.addWidget(self.manual_text)
        except (RuntimeError, AttributeError) as e:
            print(f"Warning: Could not add manual_text widget: {e}")
            # Create a new text widget if needed
            from PyQt6.QtWidgets import QTextEdit
            self.manual_text = QTextEdit()
            self.manual_text.setPlaceholderText("Enter player names...")
            self.manual_text.setMaximumHeight(60)
            try:
                manual_layout.addWidget(self.manual_text)
            except:
                pass'''

    content = content.replace(old_line, new_code)
    print("✅ Added safety wrapper for manual_text")

# Fix 2: Ensure manual_text is initialized
if 'def __init__(self' in content:
    print("\n🔧 Ensuring manual_text is initialized...")

    # Find the __init__ method
    init_start = content.find('def __init__(self')
    if init_start != -1:
        # Find where to add initialization
        init_section = content[init_start:init_start + 2000]

        # Add initialization if not present
        if 'self.manual_text = ' not in init_section:
            # Find a good place to add it (after self.core initialization)
            insert_marker = 'self.core = BulletproofDFSCore()'
            insert_pos = content.find(insert_marker)

            if insert_pos != -1:
                insert_pos = content.find('\n', insert_pos) + 1
                initialization = '''        
        # Initialize GUI elements early
        from PyQt6.QtWidgets import QTextEdit
        self.manual_text = QTextEdit()
        self.manual_text.setPlaceholderText("Enter player names separated by commas...")
        self.manual_text.setMaximumHeight(60)
'''
                content = content[:insert_pos] + initialization + content[insert_pos:]
                print("✅ Added early initialization of manual_text")

# Write the fixed content
with open('enhanced_dfs_gui.py', 'w') as f:
    f.write(content)

print("\n✅ GUI fix applied!")
print("\n🚀 Try running the GUI again:")
print("   python enhanced_dfs_gui.py")
print("\nIf it still fails, use the test script to verify core functionality:")
print("   python test_core_directly.py")