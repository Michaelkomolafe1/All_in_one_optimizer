#!/usr/bin/env python3
"""
PROJECT CLEANUP SCRIPT
Removes unnecessary files and organizes the DFS optimizer project
"""

import os
import shutil
from pathlib import Path
import json

# Files and patterns to remove
UNNECESSARY_FILES = [
    # Temporary and cache files
    '*.pyc',
    '__pycache__',
    '.pytest_cache',
    '.coverage',
    'htmlcov',
    '*.egg-info',
    '.eggs',
    '*.log',

    # Backup files
    '*_backup_*.py',
    '*.bak',
    '*.tmp',
    '*.temp',

    # Old/duplicate files
    'bug.py',
    'core_optimizations.txt',
    'position_flex_analyzer.py',
    'smart_lineup_validator.py',
    'migration_script.py',
    'enhanced_dfs_gui_backup_*.py',

    # Test files that aren't needed
    'test_confirmed_lineups.py',
    'test_new_optimizer.py',

    # IDE files
    '.idea',
    '.vscode',
    '*.swp',
    '.DS_Store',

    # Old data files
    'data/cache/*',
    'data/statcast_cache/*',
    'data/vegas/*'
]

# Files to keep
ESSENTIAL_FILES = [
    # Core files
    'bulletproof_dfs_core.py',
    'enhanced_dfs_gui.py',
    'professional_dfs_gui.py',

    # System files
    'unified_data_system.py',
    'optimal_lineup_optimizer.py',
    'smart_confirmation_system.py',
    'unified_player_model.py',

    # Data source files
    'vegas_lines.py',
    'simple_statcast_fetcher.py',
    'enhanced_stats_engine.py',
    'universal_csv_parser.py',

    # Utils
    'utils/__init__.py',
    'utils/cache_manager.py',
    'utils/csv_utils.py',
    'utils/profiler.py',
    'utils/validator.py',
    'utils/config.py',
    'utils/lazy_imports.py',

    # Configuration
    'requirements.txt',
    'config.json',

    # Test data
    'DKSalaries_test.csv',
    'DKSalaries_good.csv',

    # Simple test script
    'test_simple.py',
    'test_optimizations.py'
]


def cleanup_project():
    """Clean up the project directory"""

    print("🧹 DFS OPTIMIZER PROJECT CLEANUP")
    print("=" * 50)

    removed_count = 0

    # Get all files in directory
    all_files = []
    for root, dirs, files in os.walk('.'):
        # Skip venv directory
        if '.venv' in root or 'venv' in root:
            continue

        for file in files:
            all_files.append(os.path.join(root, file))
        for dir in dirs:
            all_files.append(os.path.join(root, dir))

    # Remove unnecessary files
    for pattern in UNNECESSARY_FILES:
        if '*' in pattern:
            # Handle wildcards
            import glob
            for file in glob.glob(pattern, recursive=True):
                if os.path.exists(file):
                    try:
                        if os.path.isdir(file):
                            shutil.rmtree(file)
                        else:
                            os.remove(file)
                        print(f"🗑️ Removed: {file}")
                        removed_count += 1
                    except Exception as e:
                        print(f"⚠️ Could not remove {file}: {e}")
        else:
            # Direct file/directory
            if os.path.exists(pattern):
                try:
                    if os.path.isdir(pattern):
                        shutil.rmtree(pattern)
                    else:
                        os.remove(pattern)
                    print(f"🗑️ Removed: {pattern}")
                    removed_count += 1
                except Exception as e:
                    print(f"⚠️ Could not remove {pattern}: {e}")

    # Clean cache directories but keep the directories
    cache_dirs = ['data/cache', 'data/statcast_cache', 'data/vegas']
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                # Remove contents but keep directory
                for file in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        removed_count += 1
                print(f"🧹 Cleaned cache: {cache_dir}")
            except Exception as e:
                print(f"⚠️ Could not clean {cache_dir}: {e}")

    # List remaining files
    print(f"\n✅ Removed {removed_count} files/directories")

    # Show project structure
    print("\n📁 PROJECT STRUCTURE:")
    print("=" * 50)

    # Count remaining files
    remaining_files = []
    for root, dirs, files in os.walk('.'):
        # Skip venv
        if '.venv' in root or 'venv' in root:
            continue

        level = root.replace('.', '', 1).count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")

        sub_indent = ' ' * 2 * (level + 1)
        for file in sorted(files):
            if not file.startswith('.'):
                print(f"{sub_indent}{file}")
                remaining_files.append(os.path.join(root, file))

    print(f"\n📊 Total files remaining: {len(remaining_files)}")

    # Create project info file
    project_info = {
        'project': 'DFS Optimizer',
        'version': '2.0',
        'cleaned_date': str(Path.cwd()),
        'essential_files': ESSENTIAL_FILES,
        'file_count': len(remaining_files)
    }

    with open('project_info.json', 'w') as f:
        json.dump(project_info, f, indent=2)

    print("\n✅ Cleanup complete!")
    print("📄 Project info saved to project_info.json")


def create_gitignore():
    """Create a proper .gitignore file"""

    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
env.bak/
venv.bak/

# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/
.nox/
coverage.xml
*.cover
.hypothesis/

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~
.project
.pydevproject

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
data/cache/
data/statcast_cache/
data/vegas/
bankroll_data.json
*_backup_*.py
*.log
*.tmp
*.temp

# Config with sensitive data
config_local.json
"""

    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)

    print("📄 Created .gitignore file")


if __name__ == "__main__":
    import sys

    print("⚠️ This will clean up your project directory")
    print("   Unnecessary files will be removed")
    print("   Cache directories will be cleaned")

    response = input("\nProceed with cleanup? (y/n): ").lower()

    if response == 'y':
        cleanup_project()
        create_gitignore()
    else:
        print("Cleanup cancelled")