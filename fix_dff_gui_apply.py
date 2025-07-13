#!/usr/bin/env python3
"""Fix GUI to apply DFF rankings when selected"""

import re

# Read the GUI file
with open('enhanced_dfs_gui.py', 'r') as f:
    content = f.read()

# Find the select_dff_file method
pattern = r'(if file_path:\s+self\.dff_file = file_path\s+filename = os\.path\.basename\(file_path\)\s+self\.dff_label\.setText\(f"✅ {filename}"\))'

replacement = '''if file_path:
            self.dff_file = file_path
            filename = os.path.basename(file_path)
            self.dff_label.setText(f"✅ {filename}")
            
            # Apply DFF rankings immediately if core is loaded
            if hasattr(self, 'core') and self.core and hasattr(self.core, 'apply_dff_rankings'):
                try:
                    print(f"🎯 Applying DFF rankings from {filename}...")
                    success = self.core.apply_dff_rankings(file_path)
                    if success:
                        print("✅ DFF rankings applied successfully!")
                        if hasattr(self, 'console'):
                            self.console.thread_safe_append(f"✅ DFF rankings applied from {filename}")
                    else:
                        print("❌ Failed to apply DFF rankings")
                        if hasattr(self, 'console'):
                            self.console.thread_safe_append(f"❌ Failed to apply DFF rankings from {filename}")
                except Exception as e:
                    print(f"❌ Error applying DFF: {e}")
                    if hasattr(self, 'console'):
                        self.console.thread_safe_append(f"❌ Error applying DFF: {str(e)}")'''

# Apply the fix
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('enhanced_dfs_gui.py', 'w') as f:
    f.write(content)

print("✅ Fixed GUI to apply DFF rankings when selected")
print("\nNow restart the GUI and try again:")
print("1. Load DraftKings CSV")
print("2. Load DFF file")
print("3. You should see DFF application messages")
