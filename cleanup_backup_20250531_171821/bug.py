#!/usr/bin/env python3
"""
DFS Project Cleanup Script - Remove unnecessary files
Keeps only the essential working files
"""

import os
import shutil
from datetime import datetime
from pathlib import Path


class DFSProjectCleaner:
    """Clean up DFS project folder by removing unnecessary files"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_dir = None
        self.files_to_keep = {
            # CORE WORKING FILES (KEEP)
            'optimized_dfs_core_with_statcast.py',  # Your main working core with real Statcast
            'simple_statcast_fetcher.py',  # Working Statcast fetcher
            'enhanced_dfs_gui.py',  # Working GUI
            'launch_with_statcast.py',  # Working launcher

            # DATA FILES (KEEP)
            'DKSalaries_Sample.csv',  # Sample data
            'DFF_Sample_Cheatsheet.csv',  # Sample DFF data
            'DKSalaries (58).csv',  # Your real DK data
            'DFF_MLB_cheatsheet_2025-05-31.csv',  # Your real DFF data

            # ESSENTIAL COMPONENTS (KEEP)
            'unified_player_model.py',  # Advanced player model
            'unified_milp_optimizer.py',  # MILP optimizer

            # PROJECT FILES (KEEP)
            'README.md',  # Documentation
            'PROJECT_STRUCTURE.md',  # Structure guide
            '.gitignore',  # Git ignore

            # CACHE/DATA FOLDERS (KEEP)
            'data',  # Data directory
            'statcast_cache',  # Statcast cache
        }

        self.files_to_remove = {
            # DUPLICATE/OLD CORES
            'optimized_dfs_core.py',  # Duplicate without Statcast
            'optimized_dfs_core_fixed_strategy.py',  # Fixed version (merged)
            'working_dfs_core_final.py',  # Old version

            # OLD/BROKEN COMPONENTS
            'real_statcast_fetcher.py',  # Replaced by simple version
            'statcast_integration.py',  # Complex version

            # TEST/DEBUG FILES
            'bug.py',  # Debug file
            'test_*.py',  # Test files
            'working_test_*.py',  # Test files
            'enhance_*.py',  # Debug files

            # BACKUP/COPY FILES
            'copy_artifacts.py',  # Copy script
            '*_backup_*.py',  # Backup files
            'old_*',  # Old files

            # TEMP/CACHE FILES
            '*.pyc',  # Python cache
            '__pycache__',  # Python cache
            '*.tmp',  # Temp files
            '.DS_Store',  # Mac files
            'Thumbs.db',  # Windows files

            # OLD LAUNCHERS
            'launch_optimized_dfs.py',  # Old launcher
            'dfs_launcher.py',  # Old launcher
            'quickstart.py',  # Old launcher
        }

    def create_backup(self):
        """Create backup before cleanup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.project_root / f"cleanup_backup_{timestamp}"
        self.backup_dir.mkdir(exist_ok=True)

        print(f"📦 Creating backup: {self.backup_dir.name}")

        # Copy all files to backup
        for item in self.project_root.iterdir():
            if item.name.startswith('cleanup_backup_'):
                continue

            try:
                if item.is_file():
                    shutil.copy2(item, self.backup_dir)
                elif item.is_dir() and item.name not in ['__pycache__', '.git']:
                    shutil.copytree(item, self.backup_dir / item.name,
                                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            except Exception as e:
                print(f"⚠️ Backup warning for {item.name}: {e}")

        print(f"✅ Backup created with {len(list(self.backup_dir.iterdir()))} items")

    def analyze_project(self):
        """Analyze current project structure"""
        all_files = list(self.project_root.rglob('*'))
        python_files = [f for f in all_files if f.suffix == '.py' and f.is_file()]
        csv_files = [f for f in all_files if f.suffix == '.csv' and f.is_file()]

        print(f"📊 PROJECT ANALYSIS:")
        print(f"   📁 Total files: {len(all_files)}")
        print(f"   🐍 Python files: {len(python_files)}")
        print(f"   📈 CSV files: {len(csv_files)}")
        print(f"   📂 Total size: {self.get_folder_size():.1f} MB")

        return python_files, csv_files

    def get_folder_size(self):
        """Get folder size in MB"""
        total_size = 0
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except:
                    pass
        return total_size / (1024 * 1024)

    def should_keep_file(self, file_path: Path) -> bool:
        """Determine if file should be kept"""
        relative_path = file_path.relative_to(self.project_root)

        # Keep specific files
        if str(relative_path) in self.files_to_keep:
            return True

        # Keep files in data directories
        if any(part in ['data', 'cache'] for part in relative_path.parts):
            return True

        # Remove specific patterns
        for pattern in self.files_to_remove:
            if file_path.match(pattern) or file_path.name.startswith(pattern.replace('*', '')):
                return False

        # Keep essential project files
        if file_path.suffix in ['.md', '.txt', '.json', '.yml', '.yaml']:
            return True

        # Default: keep if uncertain
        return True

    def cleanup_files(self, dry_run=True):
        """Clean up unnecessary files"""
        files_to_delete = []
        files_to_keep_list = []

        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and not str(file_path).startswith(str(self.backup_dir)):
                if self.should_keep_file(file_path):
                    files_to_keep_list.append(file_path)
                else:
                    files_to_delete.append(file_path)

        print(f"\n🧹 CLEANUP PLAN:")
        print(f"   ✅ Files to keep: {len(files_to_keep_list)}")
        print(f"   🗑️ Files to remove: {len(files_to_delete)}")

        if files_to_delete:
            print(f"\n📋 FILES TO BE REMOVED:")
            for file_path in sorted(files_to_delete):
                print(f"   🗑️ {file_path.relative_to(self.project_root)}")

        if not dry_run:
            print(f"\n🗑️ REMOVING FILES...")
            removed_count = 0
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    removed_count += 1
                    print(f"   ✅ Removed: {file_path.name}")
                except Exception as e:
                    print(f"   ❌ Failed to remove {file_path.name}: {e}")

            print(f"\n✅ Cleanup complete: {removed_count} files removed")

        return files_to_delete

    def create_final_structure(self):
        """Create organized final structure"""
        print(f"\n📁 FINAL PROJECT STRUCTURE:")
        print("DFS_Optimizer/")
        print("├── 🚀 CORE SYSTEM")
        print("│   ├── optimized_dfs_core_with_statcast.py  # Main system with real data")
        print("│   ├── simple_statcast_fetcher.py           # Working Statcast API")
        print("│   ├── enhanced_dfs_gui.py                  # Complete GUI")
        print("│   └── launch_with_statcast.py              # Launcher")
        print("├── 🧠 ADVANCED COMPONENTS")
        print("│   ├── unified_player_model.py              # Player model")
        print("│   └── unified_milp_optimizer.py            # MILP optimizer")
        print("├── 📊 DATA")
        print("│   ├── DKSalaries_Sample.csv                # Sample DK data")
        print("│   ├── DFF_Sample_Cheatsheet.csv            # Sample DFF data")
        print("│   ├── DKSalaries (58).csv                  # Your real DK data")
        print("│   └── DFF_MLB_cheatsheet_2025-05-31.csv    # Your real DFF data")
        print("├── 📚 DOCUMENTATION")
        print("│   ├── README.md                            # Main documentation")
        print("│   └── PROJECT_STRUCTURE.md                 # Structure guide")
        print("└── 🗂️ CACHE")
        print("    └── data/statcast_cache/                 # Cached Statcast data")


def main():
    """Main cleanup function"""
    print("🧹 DFS PROJECT CLEANUP TOOL")
    print("=" * 50)
    print("This will clean up your project by removing unnecessary files")
    print("and keeping only the essential working components.")
    print()

    cleaner = DFSProjectCleaner()

    # Analyze current state
    python_files, csv_files = cleaner.analyze_project()

    # Create backup
    cleaner.create_backup()

    # Show cleanup plan (dry run)
    files_to_delete = cleaner.cleanup_files(dry_run=True)

    if not files_to_delete:
        print("\n✨ Project is already clean! No files need to be removed.")
        return

    print(f"\n❓ PROCEED WITH CLEANUP?")
    print(f"   📦 Backup created: {cleaner.backup_dir.name}")
    print(f"   🗑️ Will remove {len(files_to_delete)} files")
    print(f"   ✅ All important files will be preserved")

    response = input(f"\nContinue? (y/N): ").strip().lower()

    if response == 'y':
        # Perform actual cleanup
        cleaner.cleanup_files(dry_run=False)

        # Show final structure
        cleaner.create_final_structure()

        print(f"\n🎉 CLEANUP COMPLETE!")
        print(f"✅ Your DFS project is now clean and organized")
        print(f"📦 Backup available at: {cleaner.backup_dir.name}")
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. Test your system: python launch_with_statcast.py test")
        print(f"   2. Launch GUI: python launch_with_statcast.py")
        print(f"   3. Your real Statcast data is ready to use!")

    else:
        print("\n❌ Cleanup cancelled")
        print("💡 Your project remains unchanged")


if __name__ == "__main__":
    main()