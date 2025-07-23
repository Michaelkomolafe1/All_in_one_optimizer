#!/usr/bin/env python3
"""
project_cleanup_analyzer.py
==========================
Identify files safe to delete
"""

import os
from pathlib import Path
import re


def analyze_project_files():
    """Analyze project and suggest what to delete"""

    # Files we know are essential
    ESSENTIAL_FILES = {
        'unified_core_system.py',
        'unified_player_model.py',
        'unified_milp_optimizer.py',
        'unified_scoring_engine.py',
        'vegas_lines.py',
        'simple_statcast_fetcher.py',
        'smart_confirmation_system.py',
        'park_factors.py',
        'enhanced_caching_system.py',
        'parallel_data_fetcher.py',
        'cash_optimization_config.py',
        'complete_dfs_gui_debug.py',
        'requirements.txt',
        'helo.py'  # Your test file
    }

    # Patterns for files typically safe to delete
    SAFE_TO_DELETE_PATTERNS = [
        r'.*_backup_.*\.py$',  # Backup files
        r'.*\.pyc$',  # Compiled Python
        r'test_.*\.py$',  # Test files (unless you want them)
        r'.*_old\.py$',  # Old versions
        r'.*_deprecated\.py$',  # Deprecated files
        r'__pycache__',  # Cache directories
        r'\.pytest_cache',  # Pytest cache
        r'.*\.log$',  # Log files
    ]

    # Files we didn't use in implementation
    UNUSED_FEATURES = {
        'automated_stacking_system.py',  # Skipped stacking
        'backtesting_framework.py',  # Skipped backtesting
        'multi_lineup_optimizer.py',  # Not needed for cash
    }

    current_dir = Path.cwd()
    all_files = []

    print("📂 ANALYZING PROJECT FILES")
    print("=" * 60)

    # Collect all Python files
    for file in current_dir.rglob("*.py"):
        if not any(part.startswith('.') for part in file.parts):
            all_files.append(file.relative_to(current_dir))

    # Categorize files
    essential = []
    safe_to_delete = []
    unused_features = []
    review_needed = []

    for file in all_files:
        file_str = str(file)

        if file.name in ESSENTIAL_FILES:
            essential.append(file)
        elif file.name in UNUSED_FEATURES:
            unused_features.append(file)
        elif any(re.match(pattern, file_str) for pattern in SAFE_TO_DELETE_PATTERNS):
            safe_to_delete.append(file)
        else:
            review_needed.append(file)

    # Print results
    print(f"\n✅ ESSENTIAL FILES ({len(essential)}):")
    for f in sorted(essential):
        print(f"   {f}")

    print(f"\n🗑️ SAFE TO DELETE ({len(safe_to_delete)}):")
    for f in sorted(safe_to_delete):
        print(f"   {f}")

    print(f"\n❓ UNUSED FEATURES ({len(unused_features)}):")
    for f in sorted(unused_features):
        print(f"   {f}")

    print(f"\n🔍 NEED REVIEW ({len(review_needed)}):")
    for f in sorted(review_needed):
        print(f"   {f}")

    # Generate cleanup script
    print("\n📝 CLEANUP COMMANDS:")
    print("# Remove safe-to-delete files:")
    for f in safe_to_delete:
        print(f"rm {f}")

    print("\n# Remove unused features (if you don't plan to use them):")
    for f in unused_features:
        print(f"rm {f}")

    print(f"\n📊 SUMMARY:")
    print(f"   Total Python files: {len(all_files)}")
    print(f"   Essential: {len(essential)}")
    print(f"   Can delete: {len(safe_to_delete) + len(unused_features)}")
    print(f"   Need review: {len(review_needed)}")


if __name__ == "__main__":
    analyze_project_files()