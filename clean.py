#!/usr/bin/env python3
"""
ENHANCED SMART DFS PROJECT CLEANUP
=================================
Intelligently cleans up your DFS project while preserving essential files
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json


class EnhancedDFSCleaner:
    def __init__(self):
        """Initialize with updated essential files list based on new architecture"""

        # ESSENTIAL FILES - Core System
        self.essential_core = {
            # Main system
            'unified_core_system.py',
            'unified_player_model.py',
            'unified_milp_optimizer.py',

            # NEW correlation-aware system
            'correlation_scoring_config.py',
            'step2_updated_player_model.py',
            'step3_stack_detection.py',

            # Data sources
            'smart_confirmation_system.py',
            'simple_statcast_fetcher.py',
            'vegas_lines.py',
            'park_factors.py',
            'weather_integration.py',

            # Caching & optimization
            'enhanced_caching_system.py',
            'parallel_data_fetcher.py',
            'cash_optimization_config.py',
        }

        # ESSENTIAL FILES - User Interface
        self.essential_ui = {
            'complete_dfs_gui_debug.py',  # Main GUI
            'launch_dfs_optimizer.py',  # Launcher
        }

        # ESSENTIAL FILES - Config & Docs
        self.essential_config = {
            'requirements.txt',
            'README.md',
            'dfs_unified_config.json',
            '.gitignore',
            'Makefile',
            'pyproject.toml',
            '.pre-commit-config.yaml',
        }

        # Testing files to keep
        self.essential_tests = {
            'test.py',  # New correlation test
        }

        # Combine all essentials
        self.essential_files = (
                self.essential_core |
                self.essential_ui |
                self.essential_config |
                self.essential_tests
        )

        # Old implementations to remove
        self.old_implementations = {
            # Old cores
            'bulletproof_dfs_core.py',
            'advanced_dfs_core.py',
            'pure_data_pipeline.py',
            'optimized_dfs_core.py',
            'working_dfs_core_final.py',
            'optimized_data_pipeline.py',

            # Old scoring engines
            'advanced_scoring_engine.py',
            'enhanced_stats_engine.py',
            'unified_scoring_engine.py',
            'bayesian_scoring_engine.py',

            # Old optimizers
            'optimal_lineup_optimizer.py',
            'milp_with_stacking.py',
            'multi_lineup_optimizer.py',

            # Redundant GUIs
            'enhanced_dfs_gui.py',
            'streamlined_dfs_gui.py',
            'dfs_launcher.py',

            # Old utilities
            'unified_data_system.py',
            'unified_config_manager.py',
            'automated_stacking_system.py',
            'slate_aware_confirmation.py',
            'rotowire_pitcher_system.py',
            'bankroll_management.py',
            'data_validator.py',
            'validator.py',
            'smart_cache.py',
            'logging_config.py',
            'dfs_config.py',
        }

        # Test/debug files to remove
        self.debug_files = {
            'bug.py', 'debug.py', 'auidt.py',
            'check_system.py', 'check_2.py', 'clean.py',
            'quick_check.py', 'quick_test.py', 'verify_slate.py',
            'warm_cache.py', 'analyze_logs.py', 'helo.py',
            'debug_game_info.py', 'gui_diagonistic.py',
            'test_real_statcast.py', 'test_new_strategies.py',
        }

    def create_backup(self):
        """Create backup before cleaning"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f"backup_{timestamp}")

        print(f"📦 Creating backup in {backup_dir}/")

        # Only backup Python files
        for file_path in Path('.').glob('*.py'):
            if file_path.name not in self.essential_files:
                backup_path = backup_dir / file_path.name
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, backup_path)

        return backup_dir

    def clean_project(self, dry_run=True):
        """Clean the project"""
        print("\n🧹 ENHANCED DFS PROJECT CLEANUP")
        print("=" * 60)

        removed_files = []
        removed_dirs = []

        # Clean cache directories
        cache_dirs = ['__pycache__', '.pytest_cache', '.gui_cache', 'htmlcov', '.mypy_cache']
        for cache_dir in cache_dirs:
            if Path(cache_dir).exists():
                if not dry_run:
                    shutil.rmtree(cache_dir)
                removed_dirs.append(cache_dir)
                print(f"🗑️  Removed cache: {cache_dir}")

        # Clean old implementations
        for old_file in self.old_implementations:
            if Path(old_file).exists():
                if not dry_run:
                    Path(old_file).unlink()
                removed_files.append(old_file)
                print(f"🗑️  Removed old implementation: {old_file}")

        # Clean debug files
        for debug_file in self.debug_files:
            if Path(debug_file).exists():
                if not dry_run:
                    Path(debug_file).unlink()
                removed_files.append(debug_file)
                print(f"🗑️  Removed debug file: {debug_file}")

        # Clean compiled Python files
        for pattern in ['*.pyc', '*.pyo', '*.pyd']:
            for file_path in Path('.').rglob(pattern):
                if not dry_run:
                    file_path.unlink()
                removed_files.append(str(file_path))

        # Show summary
        print("\n📊 CLEANUP SUMMARY:")
        print(f"   Files removed: {len(removed_files)}")
        print(f"   Directories removed: {len(removed_dirs)}")
        print(f"   Essential files preserved: {len(self.essential_files)}")

        if dry_run:
            print("\n⚠️  DRY RUN MODE - No files were actually deleted")
            print("   Run with --execute to perform actual cleanup")

        return removed_files, removed_dirs

    def create_project_structure(self):
        """Create organized project structure"""
        directories = [
            'data/cache',
            'data/historical',
            'output/lineups',
            'output/reports',
            'config',
            'logs',
            'tests',
        ]

        print("\n📁 Creating organized directory structure...")
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created: {directory}/")

    def verify_essentials(self):
        """Verify all essential files exist"""
        print("\n🔍 Verifying essential files...")
        missing = []

        for essential in self.essential_files:
            if not Path(essential).exists():
                missing.append(essential)
                print(f"   ❌ MISSING: {essential}")
            else:
                print(f"   ✅ Found: {essential}")

        if missing:
            print(f"\n⚠️  WARNING: {len(missing)} essential files are missing!")
        else:
            print("\n✅ All essential files present!")

        return missing


def main():
    """Run the enhanced cleanup"""
    import argparse

    parser = argparse.ArgumentParser(description='Clean up DFS project')
    parser.add_argument('--execute', action='store_true',
                        help='Actually delete files (default is dry run)')
    parser.add_argument('--backup', action='store_true',
                        help='Create backup before cleaning')
    parser.add_argument('--organize', action='store_true',
                        help='Create organized directory structure')
    args = parser.parse_args()

    cleaner = EnhancedDFSCleaner()

    # Verify essentials first
    missing = cleaner.verify_essentials()

    if args.backup and args.execute:
        backup_dir = cleaner.create_backup()
        print(f"\n✅ Backup created: {backup_dir}/")

    # Run cleanup
    removed_files, removed_dirs = cleaner.clean_project(dry_run=not args.execute)

    # Create structure if requested
    if args.organize:
        cleaner.create_project_structure()

    print("\n🎉 Cleanup complete!")


if __name__ == "__main__":
    main()