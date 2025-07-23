#!/usr/bin/env python3
"""
SMART DFS PROJECT CLEANUP
========================
Intelligently cleans up your DFS project while preserving essential files
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json


class SmartDFSCleaner:
    def __init__(self):
        """Initialize the cleaner with essential files list"""

        # ESSENTIAL FILES - DO NOT DELETE
        self.essential_files = {
            # Core Unified System
            'unified_core_system.py',
            'unified_player_model.py',
            'unified_milp_optimizer.py',
            'unified_scoring_engine.py',

            # Data Sources
            'simple_statcast_fetcher.py',
            'smart_confirmation_system.py',
            'vegas_lines.py',
            'park_factors.py',

            # Advanced Features
            'enhanced_caching_system.py',
            'parallel_data_fetcher.py',
            'cash_optimization_config.py',

            # GUI
            'complete_dfs_gui_debug.py',  # Your main GUI
            'enhanced_dfs_gui.py',  # Alternative GUI
            'launch_dfs_optimizer.py',  # Launcher

            # Configuration & Documentation
            'requirements.txt',
            'README.md',
            'dfs_unified_config.json',
            '.gitignore',
            'Makefile',

            # This cleanup script
            'smart_cleanup.py'
        }

        # Directories to always clean
        self.always_clean_dirs = {
            '__pycache__',
            '.pytest_cache',
            '.gui_cache',
            'htmlcov',
            '.coverage',
            '.mypy_cache'
        }

        # File patterns to always clean
        self.always_clean_patterns = [
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '*~',
            '*.swp',
            '*.swo',
            '.DS_Store',
            'Thumbs.db',
            '*.orig',
            '*.rej'
        ]

        # Files to remove (old implementations)
        self.old_implementations = {
            'bulletproof_dfs_core.py',
            'advanced_dfs_core.py',
            'pure_data_pipeline.py',
            'optimized_dfs_core.py',
            'working_dfs_core_final.py',
            'advanced_scoring_engine.py',
            'enhanced_stats_engine.py',
            'optimal_lineup_optimizer.py',
            'milp_with_stacking.py',
            'unified_data_system.py',
            'unified_milp_optimizer_clean.py',
            'unified_config_manager.py'
        }

        # Test and debug files
        self.test_debug_files = {
            'test.py', 'bug.py', 'debug.py', 'auidt.py',
            'check_system.py', 'check_2.py', 'clean.py',
            'quick_check.py', 'quick_test.py', 'verify_slate.py',
            'warm_cache.py', 'analyze_logs.py', 'helo.py',
            'debug_game_info.py', 'gui_diagonistic.py'
        }

        # Performance and optimization files (old)
        self.old_performance_files = {
            'optimize_performance.py',
            'performance_monitor.py',
            'performance_optimizer.py',
            'performance_tracker.py',
            'performance_config.py',
            'progress_tracker.py'
        }

        # Unused features
        self.unused_features = {
            'multi_lineup_optimizer.py',
            'automated_stacking_system.py',
            'slate_aware_confirmation.py',
            'rotowire_pitcher_system.py',
            'bankroll_management.py',
            'data_validator.py',
            'validator.py',
            'smart_cache.py',
            'logging_config.py',
            'dfs_config.py'
        }

    def analyze_project(self):
        """Analyze the project and categorize files"""

        print("🔍 ANALYZING DFS PROJECT STRUCTURE")
        print("=" * 80)

        analysis = {
            'essential': [],
            'cache_files': [],
            'log_files': [],
            'backup_files': [],
            'old_implementations': [],
            'test_debug': [],
            'unused_features': [],
            'untracked': [],
            'safe_to_delete': []
        }

        # Walk through all files
        for root, dirs, files in os.walk('.'):
            # Skip .venv and .git
            dirs[:] = [d for d in dirs if d not in {'.venv', 'venv', '.git'}]

            root_path = Path(root)

            # Check directories
            for d in dirs:
                dir_path = root_path / d
                rel_path = dir_path.relative_to('.')

                # Cache directories
                if d in self.always_clean_dirs:
                    analysis['cache_files'].append(str(rel_path))
                # Backup directories
                elif 'backup' in d.lower() or d.startswith('archive_'):
                    analysis['backup_files'].append(str(rel_path))

            # Check files
            for f in files:
                file_path = root_path / f
                rel_path = file_path.relative_to('.')
                rel_str = str(rel_path)

                # Skip if in .venv
                if '.venv' in rel_str or 'venv' in rel_str:
                    continue

                # Essential files
                if f in self.essential_files:
                    analysis['essential'].append(rel_str)
                # Cache files
                elif any(f.endswith(ext) for ext in ['.pyc', '.pyo', '.pyd']):
                    analysis['cache_files'].append(rel_str)
                # Log files
                elif f.endswith('.log'):
                    analysis['log_files'].append(rel_str)
                # Backup files
                elif any(pattern in f for pattern in ['backup', '_old', '.bak']):
                    analysis['backup_files'].append(rel_str)
                # Old implementations
                elif f in self.old_implementations:
                    analysis['old_implementations'].append(rel_str)
                # Test/debug files
                elif f in self.test_debug_files or f.startswith('test_'):
                    analysis['test_debug'].append(rel_str)
                # Unused features
                elif f in self.unused_features:
                    analysis['unused_features'].append(rel_str)
                # Always clean patterns
                elif any(f.endswith(pattern.replace('*', '')) for pattern in self.always_clean_patterns):
                    analysis['safe_to_delete'].append(rel_str)
                # Python files not in essential
                elif f.endswith('.py') and f not in self.essential_files:
                    analysis['untracked'].append(rel_str)

        return analysis

    def show_analysis(self, analysis):
        """Display the analysis results"""

        print("\n📊 PROJECT ANALYSIS RESULTS:")
        print("=" * 80)

        # Essential files
        print(f"\n✅ ESSENTIAL FILES ({len(analysis['essential'])})")
        print("These files are core to your system and will be preserved:")
        for f in sorted(analysis['essential'])[:10]:
            print(f"   {f}")
        if len(analysis['essential']) > 10:
            print(f"   ... and {len(analysis['essential']) - 10} more")

        # Files to delete
        total_deletable = 0

        categories = [
            ('cache_files', '🗑️ CACHE FILES', 'Python cache, temporary files'),
            ('log_files', '📝 LOG FILES', 'Application logs'),
            ('backup_files', '💾 BACKUP FILES', 'Old backups and copies'),
            ('old_implementations', '🔧 OLD IMPLEMENTATIONS', 'Replaced by unified system'),
            ('test_debug', '🐛 TEST/DEBUG FILES', 'Testing and debugging scripts'),
            ('unused_features', '❌ UNUSED FEATURES', 'Features not in use'),
            ('safe_to_delete', '🧹 TEMPORARY FILES', 'Editor and OS files')
        ]

        for key, title, desc in categories:
            items = analysis[key]
            if items:
                print(f"\n{title} ({len(items)})")
                print(f"   {desc}")
                for f in sorted(items)[:5]:
                    print(f"   • {f}")
                if len(items) > 5:
                    print(f"   ... and {len(items) - 5} more")
                total_deletable += len(items)

        # Untracked Python files
        if analysis['untracked']:
            print(f"\n⚠️ UNTRACKED PYTHON FILES ({len(analysis['untracked'])})")
            print("   Review these - they might be deletable:")
            for f in sorted(analysis['untracked'])[:10]:
                print(f"   ? {f}")
            if len(analysis['untracked']) > 10:
                print(f"   ... and {len(analysis['untracked']) - 10} more")

        print(f"\n📊 SUMMARY:")
        print(f"   Essential files: {len(analysis['essential'])}")
        print(f"   Files to delete: {total_deletable}")
        print(f"   Untracked files to review: {len(analysis['untracked'])}")

        # Estimate space savings
        total_size = 0
        for category in ['cache_files', 'log_files', 'backup_files', 'old_implementations',
                         'test_debug', 'unused_features', 'safe_to_delete']:
            for f in analysis[category]:
                if os.path.exists(f):
                    try:
                        total_size += os.path.getsize(f)
                    except:
                        pass

        print(f"   Estimated space to free: {total_size / 1024 / 1024:.1f} MB")

        return total_deletable

    def create_cleanup_script(self, analysis):
        """Create a shell script to perform the cleanup"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        script_name = f'perform_cleanup_{timestamp}.sh'

        with open(script_name, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"# DFS Project Cleanup Script\n")
            f.write(f"# Generated: {datetime.now()}\n")
            f.write("# Review before running!\n\n")

            f.write("echo '🧹 DFS PROJECT CLEANUP'\n")
            f.write("echo '====================='\n\n")

            # Remove cache directories
            if analysis['cache_files']:
                f.write("echo '🗑️ Removing cache files...'\n")
                for item in analysis['cache_files']:
                    if os.path.isdir(item):
                        f.write(f"rm -rf '{item}' 2>/dev/null\n")
                    else:
                        f.write(f"rm -f '{item}' 2>/dev/null\n")
                f.write("echo '   ✓ Cache cleaned'\n\n")

            # Remove other categories
            for category, title in [
                ('log_files', 'log files'),
                ('backup_files', 'backup files'),
                ('old_implementations', 'old implementations'),
                ('test_debug', 'test/debug files'),
                ('unused_features', 'unused features'),
                ('safe_to_delete', 'temporary files')
            ]:
                if analysis[category]:
                    f.write(f"echo 'Removing {title}...'\n")
                    for item in analysis[category]:
                        if os.path.exists(item):
                            if os.path.isdir(item):
                                f.write(f"rm -rf '{item}' 2>/dev/null\n")
                            else:
                                f.write(f"rm -f '{item}' 2>/dev/null\n")
                    f.write(f"echo '   ✓ {title.capitalize()} removed'\n\n")

            f.write("echo '✅ Cleanup complete!'\n")

        os.chmod(script_name, 0o755)
        return script_name

    def run_cleanup(self, dry_run=True):
        """Main cleanup function"""

        print("\n🧹 SMART DFS PROJECT CLEANUP")
        print("=" * 80)

        # Analyze project
        analysis = self.analyze_project()

        # Show analysis
        total_deletable = self.show_analysis(analysis)

        if total_deletable == 0:
            print("\n✅ Your project is already clean!")
            return

        # Create cleanup script
        script_name = self.create_cleanup_script(analysis)

        print(f"\n📝 Cleanup script created: {script_name}")

        if dry_run:
            print("\n🔍 DRY RUN MODE - No files deleted")
            print("\nTo perform cleanup:")
            print(f"1. Review the script: cat {script_name}")
            print(f"2. Run it: ./{script_name}")
            print("\nOr run this script with --clean flag to execute immediately")
        else:
            print("\n⚠️ Ready to clean up files!")
            response = input("Continue? (yes/no): ")
            if response.lower() == 'yes':
                os.system(f"./{script_name}")
                print("\n✅ Cleanup complete!")
            else:
                print("Cancelled. Run the script manually when ready:")
                print(f"./{script_name}")


def main():
    """Main entry point"""
    import sys

    cleaner = SmartDFSCleaner()

    # Check for flags
    dry_run = '--clean' not in sys.argv

    cleaner.run_cleanup(dry_run=dry_run)


if __name__ == "__main__":
    main()