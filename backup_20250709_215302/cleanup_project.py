#!/usr/bin/env python3
# AUTO-GENERATED CLEANUP SCRIPT
# Review before running!

import os
import shutil
from pathlib import Path

def cleanup_project():
    print("🧹 CLEANING DFS PROJECT...")

    # 1. Remove backup files
    backup_patterns = ['*backup*', '*_backup_*', 'cleanup_backup*', 'auto_fix_backup*']
    removed_count = 0

    for pattern in backup_patterns:
        for file in Path('.').glob(pattern):
            if file.is_file():
                print(f"   Removing: {file}")
                file.unlink()
                removed_count += 1

    print(f"   ✅ Removed {removed_count} backup files")

    # 2. Clean __pycache__
    for cache_dir in Path('.').rglob('__pycache__'):
        shutil.rmtree(cache_dir)
        print(f"   ✅ Removed cache: {cache_dir}")

    # 3. Create organized structure
    dirs_to_create = [
        'core',           # Core optimizer files
        'data/cache',     # Data caches
        'data/inputs',    # Input CSV files
        'tests',          # Test files
        'utils',          # Utility scripts
        'gui'             # GUI related files
    ]

    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created: {dir_path}")

    print("\n✅ Cleanup complete!")

if __name__ == "__main__":
    response = input("This will clean your project. Continue? (y/n): ")
    if response.lower() == 'y':
        cleanup_project()
