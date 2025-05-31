#!/usr/bin/env python3
"""
Cleanup Old Files Script
Safely organizes and removes redundant files while preserving important ones
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


class FileCleanup:
    """Safe file cleanup and organization"""

    def __init__(self):
        self.current_dir = Path('.')
        self.backup_dir = Path(f'old_files_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')

        # Files to keep (essential)
        self.keep_files = {
            'optimized_dfs_core.py',  # Your new working core
            'enhanced_dfs_gui.py',  # Your new working GUI
            'launch_optimized_dfs.py',  # Your new launcher
            'copy_artifacts.py',  # The script that created the files
            'automatic_system_optimizer.py',  # System optimizer
            'working_dfs_core_final.py',  # Original working core (preserve as backup)
            'unified_player_model.py',  # Advanced components (might be useful)
            'unified_milp_optimizer.py',  # Advanced components (might be useful)
            'optimized_data_pipeline.py',  # Advanced components (might be useful)
        }

        # Files to move to archive (old/redundant but keep as backup)
        self.archive_files = {
            'streamlined_dfs_gui.py',  # Old GUI (replaced by enhanced)
            'advanced_dfs_core.py',  # Old core attempt
            'dfs_launcher.py',  # Old launcher
            'launch_streamlined_gui.py',  # Old launcher
            'launch_dfs_optimizer.py',  # Old launcher
            'dfs_cli.py',  # CLI (keep in archive)
            'quickstart.py',  # Old quickstart
            'quickstart_streamlined.py',  # Old quickstart
            'clean.py',  # Old cleanup script
            'bug.py',  # Old bug fix script
            'integration_patches.py',  # Old integration
            'advanced_dfs_wrapper.py',  # Old wrapper
            'launch_advanced.py',  # Old launcher
            'quick_integration_test.py',  # Old test
            'advanced_dfs_algorithm.py',  # Old algorithm
        }

        # Files to delete (truly redundant/empty)
        self.delete_files = {
            'working_dfs_core.py',  # Empty file
            'find_files.py',  # Utility (not needed)
            'find_csv_files.py',  # Utility (not needed)
            'strategy_info_addon.py',  # GUI addon (not needed)
            'test_real_statcast.py',  # Old test
            'test_new_strategies.py',  # Old test
        }

        # Markdown files to archive
        self.archive_md_files = {
            'DEPLOYMENT_REPORT_20250531_024546.md',
            'INTEGRATION_SUMMARY.md',
            'UPGRADE_SUMMARY.md',
            'CLEANUP_REPORT_20250531_100424.md',
        }

    def analyze_current_files(self):
        """Analyze what files are currently present"""
        print("🔍 Analyzing current files...")

        all_py_files = set(f.name for f in self.current_dir.glob('*.py'))
        all_md_files = set(f.name for f in self.current_dir.glob('*.md'))

        present_keep = all_py_files & self.keep_files
        present_archive = all_py_files & self.archive_files
        present_delete = all_py_files & self.delete_files
        present_md_archive = all_md_files & self.archive_md_files

        unknown_py = all_py_files - self.keep_files - self.archive_files - self.delete_files

        print(f"📊 File Analysis:")
        print(f"   📋 Total Python files: {len(all_py_files)}")
        print(f"   📋 Total Markdown files: {len(all_md_files)}")
        print(f"   ✅ Keep files present: {len(present_keep)}")
        print(f"   📦 Archive files present: {len(present_archive)}")
        print(f"   🗑️ Delete files present: {len(present_delete)}")
        print(f"   📄 Archive MD files present: {len(present_md_archive)}")
        print(f"   ❓ Unknown files: {len(unknown_py)}")

        if unknown_py:
            print(f"   ❓ Unknown Python files: {unknown_py}")

        return {
            'keep': present_keep,
            'archive': present_archive,
            'delete': present_delete,
            'archive_md': present_md_archive,
            'unknown': unknown_py
        }

    def create_backup(self):
        """Create backup of ALL current files"""
        print(f"💾 Creating backup in {self.backup_dir}...")

        self.backup_dir.mkdir(exist_ok=True)

        # Backup all Python and Markdown files
        backup_count = 0
        for pattern in ['*.py', '*.md']:
            for file_path in self.current_dir.glob(pattern):
                if file_path.is_file():
                    shutil.copy2(file_path, self.backup_dir / file_path.name)
                    backup_count += 1

        print(f"✅ Backed up {backup_count} files")
        return True

    def create_directories(self):
        """Create organization directories"""
        directories = ['archives', 'archives/old_guis', 'archives/old_launchers', 'archives/documentation']

        for directory in directories:
            dir_path = self.current_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)

        print("✅ Created organization directories")

    def move_files_to_archive(self, file_analysis):
        """Move files to appropriate archive locations"""
        print("📦 Moving files to archives...")

        moved_count = 0

        # Move old GUI files
        gui_files = {'streamlined_dfs_gui.py'}
        for filename in gui_files & file_analysis['archive']:
            src = self.current_dir / filename
            dst = self.current_dir / 'archives' / 'old_guis' / filename
            shutil.move(str(src), str(dst))
            print(f"   📦 {filename} → archives/old_guis/")
            moved_count += 1

        # Move old launcher files
        launcher_files = {
            'dfs_launcher.py', 'launch_streamlined_gui.py', 'launch_dfs_optimizer.py',
            'launch_advanced.py', 'dfs_cli.py'
        }
        for filename in launcher_files & file_analysis['archive']:
            src = self.current_dir / filename
            dst = self.current_dir / 'archives' / 'old_launchers' / filename
            shutil.move(str(src), str(dst))
            print(f"   📦 {filename} → archives/old_launchers/")
            moved_count += 1

        # Move other archive files to main archives
        other_archive = file_analysis['archive'] - gui_files - launcher_files
        for filename in other_archive:
            src = self.current_dir / filename
            dst = self.current_dir / 'archives' / filename
            shutil.move(str(src), str(dst))
            print(f"   📦 {filename} → archives/")
            moved_count += 1

        # Move markdown files
        for filename in file_analysis['archive_md']:
            src = self.current_dir / filename
            dst = self.current_dir / 'archives' / 'documentation' / filename
            shutil.move(str(src), str(dst))
            print(f"   📄 {filename} → archives/documentation/")
            moved_count += 1

        print(f"✅ Moved {moved_count} files to archives")

    def delete_redundant_files(self, file_analysis):
        """Delete truly redundant files"""
        print("🗑️ Deleting redundant files...")

        deleted_count = 0
        for filename in file_analysis['delete']:
            file_path = self.current_dir / filename
            if file_path.exists():
                file_path.unlink()
                print(f"   🗑️ Deleted: {filename}")
                deleted_count += 1

        print(f"✅ Deleted {deleted_count} redundant files")

    def create_organized_readme(self):
        """Create README explaining the new organization"""
        readme_content = '''# DFS Optimizer - Organized and Optimized

## 🎯 YOUR WORKING SYSTEM

### Essential Files (Root Directory):
- `optimized_dfs_core.py` - Main optimization engine (ALL features preserved)
- `enhanced_dfs_gui.py` - Complete GUI interface  
- `launch_optimized_dfs.py` - Simple launcher script

### Original Files (Preserved):
- `working_dfs_core_final.py` - Your original working core (kept as backup)
- `unified_*.py` - Advanced components (preserved for future use)

## 🚀 HOW TO USE

### Launch the System:
```bash
python launch_optimized_dfs.py        # Launch GUI
python launch_optimized_dfs.py test   # Test system
```

### What's Preserved:
✅ Online confirmed lineup fetching
✅ Enhanced DFF logic and matching
✅ Multi-position MILP optimization
✅ Real Statcast data integration
✅ Manual player selection
✅ All original strategies and features

## 📁 ORGANIZATION

### archives/
- `old_guis/` - Previous GUI versions
- `old_launchers/` - Previous launcher scripts  
- `documentation/` - Deployment and integration reports
- Other old/redundant files preserved for reference

### Backup:
- `old_files_backup_[timestamp]/` - Complete backup of all files before cleanup

## ✅ WHAT'S DIFFERENT

- Fixed import issues (optimized_dfs_core.py now exists)
- All functionality preserved exactly as it was
- Better file organization
- Redundant files removed/archived
- Clean working directory

## 🎉 READY TO USE

Your system is now optimized and organized while preserving ALL functionality!
'''

        with open('README.md', 'w') as f:
            f.write(readme_content)

        print("✅ Created organized README.md")

    def run_cleanup(self):
        """Run the complete cleanup process"""
        print("🧹 DFS OPTIMIZER FILE CLEANUP & ORGANIZATION")
        print("=" * 60)
        print("This will organize your files while preserving all important functionality")
        print()

        # Analyze current state
        file_analysis = self.analyze_current_files()
        print()

        # Show what will happen
        print("📋 CLEANUP PLAN:")
        print(f"✅ Keep in root: {len(file_analysis['keep'])} essential files")
        print(f"📦 Move to archives: {len(file_analysis['archive']) + len(file_analysis['archive_md'])} files")
        print(f"🗑️ Delete redundant: {len(file_analysis['delete'])} files")
        print(f"💾 Backup everything first: Yes")
        print()

        # Get confirmation
        response = input("🤔 Continue with cleanup? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Cleanup cancelled")
            return False

        try:
            # Step 1: Create backup
            self.create_backup()

            # Step 2: Create directories
            self.create_directories()

            # Step 3: Move files to archives
            self.move_files_to_archive(file_analysis)

            # Step 4: Delete redundant files
            self.delete_redundant_files(file_analysis)

            # Step 5: Create organized README
            self.create_organized_readme()

            print("\n🎉 CLEANUP COMPLETE!")
            print("=" * 40)
            print("✅ Files organized and cleaned")
            print("✅ All important functionality preserved")
            print("✅ Complete backup created")
            print("✅ Clean working directory")
            print()
            print("📋 YOUR CLEAN SYSTEM:")
            print("   🚀 Launch: python launch_optimized_dfs.py")
            print("   🧪 Test: python launch_optimized_dfs.py test")
            print("   📄 Info: Check README.md")
            print()
            print(f"💾 Backup location: {self.backup_dir}")

            return True

        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False


def main():
    """Main cleanup function"""
    cleanup = FileCleanup()

    # Quick safety check
    if not Path('optimized_dfs_core.py').exists():
        print("❌ optimized_dfs_core.py not found!")
        print("💡 Run copy_artifacts.py first to create the working files")
        return False

    if not Path('enhanced_dfs_gui.py').exists():
        print("❌ enhanced_dfs_gui.py not found!")
        print("💡 Run copy_artifacts.py first to create the working files")
        return False

    print("✅ Working files found - ready for cleanup")
    print()

    return cleanup.run_cleanup()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)