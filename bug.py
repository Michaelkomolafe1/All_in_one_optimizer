#!/usr/bin/env python3
"""
FIX GUI ERRORS
=============
Fix all import and reference errors in enhanced_dfs_gui.py
"""

import re
import os


def fix_gui_errors():
    """Fix all GUI errors"""
    print("🔧 FIXING GUI ERRORS")
    print("=" * 50)

    # Read the GUI file
    with open('enhanced_dfs_gui.py', 'r') as f:
        content = f.read()

    # Fix 1: Update imports at the top
    # Find the import section
    import_section_start = content.find('from bulletproof_dfs_core import')
    if import_section_start != -1:
        # Find the end of the import line
        import_line_end = content.find('\n', import_section_start)
        current_import_line = content[import_section_start:import_line_end]

        # Update the import to include all needed items
        new_import_line = 'from bulletproof_dfs_core import BulletproofDFSCore, AdvancedPlayer'
        content = content.replace(current_import_line, new_import_line)

    # Fix 2: Add missing function imports
    # Check if create_enhanced_test_data is imported
    if 'create_enhanced_test_data' in content and 'import create_enhanced_test_data' not in content:
        # Add it to the bulletproof_dfs_core import
        content = content.replace(
            'from bulletproof_dfs_core import BulletproofDFSCore, AdvancedPlayer',
            'from bulletproof_dfs_core import BulletproofDFSCore, AdvancedPlayer, create_enhanced_test_data'
        )

    # Fix 3: Replace load_and_optimize_complete_pipeline with direct core usage
    # This function doesn't exist anymore, we need to replace its usage
    pipeline_pattern = r'lineup, score, summary = load_and_optimize_complete_pipeline\((.*?)\)'

    def replace_pipeline(match):
        args = match.group(1)
        return '''# Use core directly instead of pipeline
        core = BulletproofDFSCore()

        # Load data
        if self.dk_file:
            core.load_draftkings_csv(self.dk_file)
        if self.dff_file:
            core.load_dff_rankings(self.dff_file)

        # Set optimization mode
        core.set_optimization_mode(self.optimization_mode)

        # Apply manual selections if any
        if self.manual_input:
            core.apply_manual_selection(self.manual_input)

        # Run optimization
        lineup, score = core.optimize_lineup_with_mode()
        summary = f"Optimization complete with {len(lineup)} players"'''

    content = re.sub(pipeline_pattern, replace_pipeline, content, flags=re.DOTALL)

    # Fix 4: Clean up the optimization thread
    # Find the OptimizationThread class and fix it
    thread_start = content.find('class OptimizationThread(QThread):')
    if thread_start != -1:
        # Find the run method
        run_start = content.find('def run(self):', thread_start)
        if run_start != -1:
            # Find the end of the run method
            # Look for the next method or class
            next_method = content.find('\n    def ', run_start + 1)
            next_class = content.find('\nclass ', run_start + 1)

            if next_method != -1 and (next_class == -1 or next_method < next_class):
                run_end = next_method
            elif next_class != -1:
                run_end = next_class
            else:
                # Find by indentation
                lines = content[run_start:].split('\n')
                for i, line in enumerate(lines[1:], 1):
                    if line and not line.startswith(' '):
                        run_end = run_start + len('\n'.join(lines[:i]))
                        break

            # Replace the run method
            new_run_method = '''    def run(self):
        """Run optimization in background with mode support"""
        try:
            if self.optimization_mode == 'manual_only':
                self.progress_updated.emit("🎯 MANUAL-ONLY MODE - Perfect for 3AM!")
                self.progress_updated.emit("📝 Using only your manual selections...")
                self.progress_updated.emit("🧠 Advanced algorithms still active...")
            else:
                self.progress_updated.emit("🚀 Starting optimization...")
                self.progress_updated.emit("📊 Loading DraftKings data...")
                self.progress_updated.emit("🔍 Detecting confirmed lineups...")

            # Create core instance
            core = BulletproofDFSCore()

            # Load data
            if self.dk_file:
                if not core.load_draftkings_csv(self.dk_file):
                    self.optimization_failed.emit("Failed to load DraftKings CSV")
                    return

            if self.dff_file:
                core.load_dff_rankings(self.dff_file)

            # Set optimization mode
            core.set_optimization_mode(self.optimization_mode)

            # Apply manual selections
            if self.manual_input:
                manual_count = core.apply_manual_selection(self.manual_input)
                self.progress_updated.emit(f"✅ Applied {manual_count} manual selections")

            # Run optimization
            lineup, score = core.optimize_lineup_with_mode()

            if lineup and score > 0:
                summary = f"Generated {len(lineup)} player lineup with {score:.2f} points"
                self.optimization_completed.emit(lineup, score, summary)
            else:
                if self.optimization_mode == 'manual_only':
                    self.optimization_failed.emit("Manual-only optimization failed - check manual player names")
                else:
                    self.optimization_failed.emit("No valid lineup generated - try manual-only mode for 3AM testing")

        except Exception as e:
            self.optimization_failed.emit(str(e))'''

            # Replace the method
            if run_end:
                content = content[:run_start] + new_run_method + content[run_end:]

    # Fix 5: Remove unused imports
    # Remove specific unused imports
    unused_imports = [
        'from pathlib import Path',
        'import tempfile'
    ]

    for unused in unused_imports:
        content = content.replace(unused + '\n', '')

    # Fix 6: Update create_enhanced_test_data usage
    # This function might need to be imported or created
    if 'create_enhanced_test_data' in content and 'def create_enhanced_test_data' not in content:
        # Add a simple implementation if it's not in bulletproof_dfs_core
        test_data_impl = '''

def create_enhanced_test_data():
    """Create test data files for demonstration"""
    import csv
    import tempfile
    import os

    # Create temporary DraftKings CSV
    dk_file = os.path.join(tempfile.gettempdir(), 'test_dk_salaries.csv')

    with open(dk_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Position', 'Name', 'Name', 'ID', 'Roster Position', 'Salary', 'Game Info', 'TeamAbbrev', 'AvgPointsPerGame'])

        # Add test players
        test_players = [
            ['P', 'Test Pitcher 1', 'Test Pitcher 1', '1', 'P', '9000', 'TEST@TEST', 'TST', '15.0'],
            ['P', 'Test Pitcher 2', 'Test Pitcher 2', '2', 'P', '7500', 'TEST@TEST', 'TST', '12.0'],
            ['C', 'Test Catcher', 'Test Catcher', '3', 'C', '4000', 'TEST@TEST', 'TST', '8.0'],
            ['1B', 'Test First Base', 'Test First Base', '4', '1B', '5000', 'TEST@TEST', 'TST', '10.0'],
            ['2B', 'Test Second Base', 'Test Second Base', '5', '2B', '4500', 'TEST@TEST', 'TST', '9.0'],
            ['3B', 'Test Third Base', 'Test Third Base', '6', '3B', '4800', 'TEST@TEST', 'TST', '9.5'],
            ['SS', 'Test Shortstop', 'Test Shortstop', '7', 'SS', '4600', 'TEST@TEST', 'TST', '9.0'],
            ['OF', 'Test Outfield 1', 'Test Outfield 1', '8', 'OF', '5500', 'TEST@TEST', 'TST', '11.0'],
            ['OF', 'Test Outfield 2', 'Test Outfield 2', '9', 'OF', '5000', 'TEST@TEST', 'TST', '10.0'],
            ['OF', 'Test Outfield 3', 'Test Outfield 3', '10', 'OF', '4500', 'TEST@TEST', 'TST', '9.0']
        ]

        for player in test_players:
            writer.writerow(player)

    return dk_file, None
'''

        # Add before the class definitions
        class_start = content.find('class OptimizationThread')
        if class_start != -1:
            content = content[:class_start] + test_data_impl + '\n\n' + content[class_start:]

    # Write the fixed content
    with open('enhanced_dfs_gui.py', 'w') as f:
        f.write(content)

    print("✅ GUI errors fixed!")
    print("\nChanges made:")
    print("1. Fixed imports for BulletproofDFSCore and AdvancedPlayer")
    print("2. Replaced load_and_optimize_complete_pipeline with direct core usage")
    print("3. Updated OptimizationThread.run() method")
    print("4. Removed unused imports")
    print("5. Added create_enhanced_test_data function")

    return True


if __name__ == "__main__":
    # Backup first
    import shutil
    from datetime import datetime

    backup_name = f'enhanced_dfs_gui_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
    shutil.copy2('enhanced_dfs_gui.py', backup_name)
    print(f"✅ Backup created: {backup_name}")

    # Fix the GUI
    if fix_gui_errors():
        print("\n🎉 GUI FIXED!")
        print("\nNow you can:")
        print("1. Run: python enhanced_dfs_gui.py")
        print("2. The GUI should launch without errors")
        print("3. Test with your CSV files")
    else:
        print("\n❌ Fix failed!")