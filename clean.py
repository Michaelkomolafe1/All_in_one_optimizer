#!/usr/bin/env python3
"""
CLEANUP PROJECT - Remove Unnecessary Files
==========================================
Identifies and optionally removes competing/unnecessary files
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


def cleanup_project(dry_run=True):
    """Clean up unnecessary files from the project"""
    print("\n🧹 DFS PROJECT CLEANUP")
    print("=" * 60)

    # Files to potentially remove
    files_to_remove = {
        'competing_systems': [
            'optimized_dfs_core.py',  # Old core
            'working_dfs_core_final.py',  # Old implementation
            'advanced_dfs_core.py',  # Competing system
            'complete_statcast_fetcher.py',  # Use simple_statcast_fetcher.py
            'real_recent_form.py',  # Integrated into pipeline
            'batting_order_correlation_system.py',  # Integrated
            'rotowire_confirmation_system.py',  # Use smart_confirmation_system
        ],
        'test_files': [
            'test.py',
            'bug.py',
            'bug_2.py',
            'debug.py',
            'test_mlb_data.py',
            'test_architecture.py',
            'direct_test_*.py',
            'quick_fix_*.py',
            'verify_sources.py',
            'test_dff_load.py',
        ],
        'old_guis': [
            'streamlined_dfs_gui.py',  # Keep enhanced_dfs_gui.py
            'dfs_gui_fixed.py',
            'gui_fixed_*.py',
            'pure_showdown_*.py',
        ],
        'backups': [
            'backup_*.py',
            '*_backup.py',
            '*_old.py',
            '*.backup_*',
        ],
        'launchers': [
            'launch_optimizer.py',  # Keep launch_dfs_optimizer.py
            'dfs_launcher.py',  # Keep launch_dfs_optimizer.py
            'run_tools.py',
        ]
    }

    # Files to keep (core system)
    files_to_keep = [
        # Core unified system
        'unified_core_system.py',  # NEW - Main system
        'unified_player_model.py',
        'unified_milp_optimizer.py',
        'unified_scoring_engine.py',
        'unified_config_manager.py',

        # Data sources
        'simple_statcast_fetcher.py',
        'smart_confirmation_system.py',
        'vegas_lines.py',

        # GUI
        'complete_dfs_gui_debug.py',  # Your current GUI
        'enhanced_dfs_gui.py',  # Alternative GUI
        'launch_dfs_optimizer.py',  # Main launcher

        # Utilities
        'data_validator.py',
        'performance_optimizer.py',

        # Project files
        'requirements.txt',
        'README.md',
        'dfs_config.json',
    ]

    # Find files to remove
    all_files_to_remove = []

    for category, patterns in files_to_remove.items():
        print(f"\n📁 {category.upper()}:")

        for pattern in patterns:
            if '*' in pattern:
                # Handle wildcards
                for file in Path('.').glob(pattern):
                    if file.is_file() and str(file) not in files_to_keep:
                        all_files_to_remove.append(str(file))
                        print(f"   • {file}")
            else:
                # Direct file
                if os.path.exists(pattern) and pattern not in files_to_keep:
                    all_files_to_remove.append(pattern)
                    print(f"   • {pattern}")

    # Remove duplicates
    all_files_to_remove = list(set(all_files_to_remove))

    print(f"\n📊 SUMMARY:")
    print(f"   Files to remove: {len(all_files_to_remove)}")
    print(f"   Files to keep: {len(files_to_keep)}")

    if not all_files_to_remove:
        print("\n✅ No unnecessary files found!")
        return

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be deleted")
        print("\nTo actually remove files, run:")
        print("python cleanup_project.py --remove")

    else:
        print("\n🗑️  REMOVING FILES...")

        # Create archive directory
        archive_dir = f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(archive_dir, exist_ok=True)

        removed = 0
        for file in all_files_to_remove:
            try:
                # Move to archive instead of deleting
                shutil.move(file, os.path.join(archive_dir, os.path.basename(file)))
                removed += 1
                print(f"   ✓ Archived: {file}")
            except Exception as e:
                print(f"   ✗ Error with {file}: {e}")

        print(f"\n✅ Archived {removed} files to {archive_dir}/")

    # Show final structure
    print("\n📋 RECOMMENDED PROJECT STRUCTURE:")
    print("""
DFS_Optimizer/
├── unified_core_system.py      # ← NEW MAIN SYSTEM
├── unified_player_model.py     # Player data model
├── unified_milp_optimizer.py   # MILP optimizer
├── unified_scoring_engine.py   # Scoring engine
├── unified_config_manager.py   # Configuration
│
├── Data Sources/
│   ├── simple_statcast_fetcher.py
│   ├── smart_confirmation_system.py
│   └── vegas_lines.py
│
├── GUI/
│   ├── complete_dfs_gui_debug.py  # Your GUI
│   ├── enhanced_dfs_gui.py        # Alternative
│   └── launch_dfs_optimizer.py    # Launcher
│
├── Utilities/
│   ├── data_validator.py
│   └── performance_optimizer.py
│
└── Project Files/
    ├── requirements.txt
    ├── README.md
    └── dfs_config.json
""")


def main():
    """Main cleanup function"""
    import sys

    # Check for --remove flag
    remove_files = '--remove' in sys.argv

    if remove_files:
        print("\n⚠️  WARNING: This will archive unnecessary files!")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return

    cleanup_project(dry_run=not remove_files)

    print("\n🎯 NEXT STEPS:")
    print("1. Run: python quick_test.py")
    print("2. Copy OptimizationWorker from gui_integration.py to your GUI")
    print("3. Run your GUI with the unified system!")


if __name__ == "__main__":
    main()