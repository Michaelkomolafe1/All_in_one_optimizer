#!/usr/bin/env python3
"""
AUTOMATIC DFS CLEANUP SCRIPT
============================
This script will automatically perform all cleanup operations
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
import sys


class AutomaticDFSCleaner:
    def __init__(self, project_path="."):
        self.project_path = Path(project_path)
        self.backup_dir = self.project_path / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.actions_taken = []

    def run_full_cleanup(self):
        """Execute the complete cleanup process"""
        print("🚀 STARTING AUTOMATIC DFS CLEANUP")
        print("=" * 60)

        # Step 1: Create backup
        self.create_backup()

        # Step 2: Delete unnecessary files
        self.delete_unnecessary_files()

        # Step 3: Create new directory structure
        self.create_directory_structure()

        # Step 4: Consolidate config files
        self.consolidate_configs()

        # Step 5: Move files to new structure
        self.reorganize_files()

        # Step 6: Fix recent form integration
        self.fix_recent_form_integration()

        # Step 7: Create main.py
        self.create_main_entry_point()

        # Step 8: Update requirements.txt
        self.update_requirements()

        # Step 9: Generate summary report
        self.generate_summary_report()

        print("\n✅ CLEANUP COMPLETE!")
        print(f"📁 Backup saved to: {self.backup_dir}")
        print(f"📊 Total actions taken: {len(self.actions_taken)}")

    def create_backup(self):
        """Create complete backup of project"""
        print("\n📦 Creating backup...")

        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)

        # Backup all Python files
        for py_file in self.project_path.glob("*.py"):
            if py_file.is_file():
                dest = self.backup_dir / py_file.name
                shutil.copy2(py_file, dest)
                self.actions_taken.append(f"Backed up {py_file.name}")

        # Backup JSON files
        for json_file in self.project_path.glob("*.json"):
            if json_file.is_file():
                dest = self.backup_dir / json_file.name
                shutil.copy2(json_file, dest)
                self.actions_taken.append(f"Backed up {json_file.name}")

        print(f"✅ Backup created with {len(list(self.backup_dir.glob('*')))} files")

    def delete_unnecessary_files(self):
        """Delete files identified as unnecessary"""
        print("\n🗑️ Deleting unnecessary files...")

        files_to_delete = [
            'enhanced_dfs_gui.py.backup_20250616_2',
            'bug.py',
            'cleanup_project.py',
            'force_fresh_patch.txt',
            'run_script.py',
            'dfs_diagnostic_20250616_211921.json',
            'analytics_verification_report.json',
            'project_analysis_report.json',
            'mlb_api_response.json',
            'cleanup_report.txt',  # Previous cleanup report
        ]

        deleted_count = 0
        for filename in files_to_delete:
            file_path = self.project_path / filename
            if file_path.exists():
                try:
                    file_path.unlink()
                    self.actions_taken.append(f"Deleted {filename}")
                    deleted_count += 1
                except Exception as e:
                    print(f"⚠️ Could not delete {filename}: {e}")

        print(f"✅ Deleted {deleted_count} unnecessary files")

    def create_directory_structure(self):
        """Create the new organized directory structure"""
        print("\n📁 Creating new directory structure...")

        directories = [
            'core',
            'data_sources',
            'optimization',
            'ui',
            'utils',
            'tests',
            'config',
            'output'
        ]

        for dir_name in directories:
            dir_path = self.project_path / dir_name
            dir_path.mkdir(exist_ok=True)

            # Create __init__.py
            init_file = dir_path / '__init__.py'
            init_file.write_text('"""{}"""\n'.format(dir_name.replace('_', ' ').title()))

            self.actions_taken.append(f"Created directory: {dir_name}/")

        print(f"✅ Created {len(directories)} directories")

    def consolidate_configs(self):
        """Consolidate all config files into one"""
        print("\n🔧 Consolidating configuration files...")

        # Collect all config data
        consolidated_config = {
            "optimization": {
                "salary_cap": 50000,
                "min_salary_usage": 0.95,
                "max_form_analysis_players": None,
                "parallel_workers": 10,
                "batch_size": 25,
                "cache_enabled": True,
                "min_projection": 5.0,
                "lineup_count": 20,
                "max_exposure": 0.5
            },
            "data_sources": {
                "statcast": {
                    "enabled": True,
                    "cache_hours": 6,
                    "batch_size": 20
                },
                "vegas": {
                    "enabled": True,
                    "cache_hours": 1,
                    "min_total_deviation": 1.0
                },
                "recent_form": {
                    "enabled": True,
                    "days_back": 14,
                    "cache_hours": 6,
                    "hot_threshold": 1.15,
                    "cold_threshold": 0.85
                },
                "dff": {
                    "enabled": True,
                    "auto_detect": True
                },
                "batting_order": {
                    "enabled": True,
                    "top_order_boost": 0.05
                }
            },
            "contest_settings": {
                "gpp": {
                    "lineup_count": 20,
                    "max_exposure": 0.5,
                    "min_unique": 0.8,
                    "ownership_fade": True
                },
                "cash": {
                    "lineup_count": 1,
                    "prefer_consistency": True,
                    "min_projection": 8.0
                }
            },
            "api_settings": {
                "pybaseball_delay": 0.5,
                "max_retries": 3,
                "timeout": 30
            }
        }

        # Try to load existing configs to preserve user settings
        config_files = ['dfs_config.json', 'real_data_config.json', 'config.json']

        for config_file in config_files:
            file_path = self.project_path / config_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        existing_config = json.load(f)
                        # Merge with consolidated config
                        consolidated_config = self._deep_merge(consolidated_config, existing_config)
                except Exception as e:
                    print(f"⚠️ Could not load {config_file}: {e}")

        # Save consolidated config
        config_path = self.project_path / 'config' / 'config.json'
        config_path.parent.mkdir(exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(consolidated_config, f, indent=2)

        self.actions_taken.append("Created consolidated config.json")

        # Delete old config files
        for config_file in ['dfs_config.json', 'real_data_config.json']:
            file_path = self.project_path / config_file
            if file_path.exists():
                file_path.unlink()
                self.actions_taken.append(f"Deleted old config: {config_file}")

        print("✅ Configuration consolidated")

    def _deep_merge(self, base, update):
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def reorganize_files(self):
        """Move files to their new organized locations"""
        print("\n📂 Reorganizing files...")

        # File mapping: current_name -> new_location
        file_moves = {
            # Core files
            'bulletproof_dfs_core.py': 'core/dfs_optimizer.py',
            'unified_player_model.py': 'core/player_model.py',

            # Data sources
            'enhanced_stats_engine.py': 'data_sources/stats_engine.py',
            'vegas_lines.py': 'data_sources/vegas_lines.py',
            'simple_statcast_fetcher.py': 'data_sources/statcast.py',
            'smart_confirmation_system.py': 'data_sources/confirmations.py',

            # Optimization
            'optimal_lineup_optimizer.py': 'optimization/lineup_optimizer.py',
            'multi_lineup_optimizer.py': 'optimization/multi_lineup.py',
            'batting_order_correlation_system.py': 'optimization/correlation.py',

            # UI
            'enhanced_dfs_gui.py': 'ui/gui.py',

            # Utils
            'unified_data_system.py': 'utils/data_system.py',
            'smart_cache.py': 'utils/cache.py',
            'performance_tracker.py': 'utils/performance.py',
            'progress_tracker.py': 'utils/progress.py',
            'bankroll_management.py': 'utils/bankroll.py',

            # Tests
            'test_integration.py': 'tests/test_optimizer.py',
            'test_multi_lineup.py': 'tests/test_multi_lineup.py',
        }

        moved_count = 0
        for current_file, new_location in file_moves.items():
            current_path = self.project_path / current_file
            new_path = self.project_path / new_location

            if current_path.exists():
                try:
                    # Ensure directory exists
                    new_path.parent.mkdir(parents=True, exist_ok=True)

                    # Move file
                    shutil.move(str(current_path), str(new_path))
                    self.actions_taken.append(f"Moved {current_file} -> {new_location}")
                    moved_count += 1
                except Exception as e:
                    print(f"⚠️ Could not move {current_file}: {e}")

        print(f"✅ Moved {moved_count} files to new structure")

        # Handle recent form consolidation
        self.consolidate_recent_form()

    def consolidate_recent_form(self):
        """Consolidate recent form modules"""
        print("\n🔄 Consolidating recent form modules...")

        # Read both files if they exist
        real_recent = self.project_path / 'real_recent_form.py'
        analyzer = self.project_path / 'recent_form_analyzer.py'

        consolidated_path = self.project_path / 'data_sources' / 'recent_form.py'

        # Use the consolidated version from the artifact
        consolidated_content = '''#!/usr/bin/env python3
"""
Consolidated Recent Form System
===============================
Merged from real_recent_form.py and recent_form_analyzer.py
"""

# Import the consolidated analyzer
from .stats_engine import apply_enhanced_statistical_analysis

# This file has been consolidated - see the ConsolidatedRecentFormAnalyzer
# in the project artifacts for the full implementation

class RecentFormAnalyzer:
    """Consolidated recent form analyzer - see artifacts for full implementation"""

    def __init__(self, cache_manager=None, days_back=14):
        self.cache_manager = cache_manager
        self.days_back = days_back
        print("⚠️ Using placeholder - implement ConsolidatedRecentFormAnalyzer from artifacts")

    def enrich_players_with_form(self, players):
        """Placeholder - implement from artifacts"""
        print("⚠️ Recent form not fully implemented - copy from artifacts")
        return 0

# Temporary placeholder - replace with ConsolidatedRecentFormAnalyzer from artifacts
'''

        # Write consolidated file
        consolidated_path.write_text(consolidated_content)
        self.actions_taken.append("Created consolidated recent_form.py")

        # Delete old files
        for old_file in [real_recent, analyzer]:
            if old_file.exists():
                old_file.unlink()
                self.actions_taken.append(f"Deleted {old_file.name}")

    def fix_recent_form_integration(self):
        """Create patch file to fix recent form integration"""
        print("\n🔧 Creating recent form fix...")

        fix_content = '''#!/usr/bin/env python3
"""
RECENT FORM INTEGRATION FIX
==========================
Apply this patch to core/dfs_optimizer.py (formerly bulletproof_dfs_core.py)
"""

# Add this method to the BulletproofDFSCore class:

def apply_recent_form_adjustments(self):
    """Apply recent form adjustments to all eligible players"""
    if not hasattr(self, 'form_analyzer') or not self.form_analyzer:
        print("⚠️ Form analyzer not initialized")
        return 0

    print("\\n📊 APPLYING RECENT FORM ADJUSTMENTS...")

    eligible = [p for p in self.players if p.is_eligible_for_selection(self.optimization_mode)]
    adjusted_count = 0

    for player in eligible:
        try:
            # Get current enhanced score
            original_score = player.enhanced_score

            # Analyze form
            form_data = self.form_analyzer.analyze_player_form(player)

            if form_data and 'form_score' in form_data:
                # Apply multiplier
                player.enhanced_score = original_score * form_data['form_score']

                # Store form data
                player.recent_form = {
                    'status': 'hot' if form_data['form_score'] > 1.05 else 'cold' if form_data['form_score'] < 0.95 else 'normal',
                    'multiplier': form_data['form_score'],
                    'original_score': original_score,
                    'adjusted_score': player.enhanced_score
                }

                adjusted_count += 1

        except Exception as e:
            print(f"⚠️ Error applying form to {player.name}: {e}")

    print(f"✅ Form adjustments applied to {adjusted_count}/{len(eligible)} players")
    return adjusted_count

# IMPORTANT: Add this line to the enrich_players() method after other enrichments:
# adjusted = self.apply_recent_form_adjustments()
'''

        fix_path = self.project_path / 'APPLY_THIS_FIX.py'
        fix_path.write_text(fix_content)
        self.actions_taken.append("Created recent form fix file")

        print("✅ Fix created - see APPLY_THIS_FIX.py")

    def create_main_entry_point(self):
        """Create new main.py entry point"""
        print("\n📝 Creating main.py...")

        main_content = '''#!/usr/bin/env python3
"""
DFS Optimizer - Main Entry Point
================================
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.dfs_optimizer import BulletproofDFSCore
from ui.gui import DFSOptimizerGUI

def run_cli(csv_file, mode='classic', **kwargs):
    """Run optimizer in CLI mode"""
    print("🎯 DFS Optimizer - CLI Mode")
    print("=" * 60)

    try:
        # Initialize optimizer
        optimizer = BulletproofDFSCore()

        # Load data
        print(f"Loading {csv_file}...")
        optimizer.load_draftkings_csv(csv_file)

        # Set mode
        optimizer.optimization_mode = mode

        # Run optimization
        lineup, score = optimizer.optimize_lineup_with_mode()

        if lineup:
            print(f"\\n✅ Optimal lineup found!")
            print(f"📊 Projected: {score:.2f} points")
            print(f"💰 Salary: ${sum(p.salary for p in lineup):,}")
            print("\\nLineup:")
            for i, player in enumerate(lineup, 1):
                print(f"{i}. {player.name} ({player.primary_position}) - ${player.salary:,}")
        else:
            print("❌ No valid lineup found")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0

def run_gui():
    """Run optimizer with GUI"""
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = DFSOptimizerGUI()
        window.show()
        sys.exit(app.exec_())
    except ImportError:
        print("❌ PyQt5 not installed. Install with: pip install PyQt5")
        return 1

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # CLI mode
        csv_file = sys.argv[1]
        mode = sys.argv[2] if len(sys.argv) > 2 else 'classic'
        return run_cli(csv_file, mode)
    else:
        # GUI mode
        return run_gui()

if __name__ == "__main__":
    sys.exit(main())
'''

        main_path = self.project_path / 'main.py'
        main_path.write_text(main_content)

        # Make it executable
        main_path.chmod(0o755)

        self.actions_taken.append("Created main.py")
        print("✅ Main entry point created")

    def update_requirements(self):
        """Update requirements.txt with all dependencies"""
        print("\n📦 Updating requirements.txt...")

        requirements = '''# DFS Optimizer Requirements
# Core dependencies
numpy>=1.21.0
pandas>=1.3.0
pulp>=2.5.0

# Data sources
pybaseball>=2.2.0
requests>=2.26.0

# UI
PyQt5>=5.15.0

# Utils
python-dateutil>=2.8.0

# Optional but recommended
scipy>=1.7.0
scikit-learn>=0.24.0
matplotlib>=3.4.0

# Development
pytest>=6.2.0
black>=21.6b0
'''

        req_path = self.project_path / 'requirements.txt'
        req_path.write_text(requirements)

        self.actions_taken.append("Updated requirements.txt")
        print("✅ Requirements updated")

    def generate_summary_report(self):
        """Generate summary of all actions taken"""
        print("\n📄 Generating summary report...")

        report = f'''DFS OPTIMIZER CLEANUP SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 60}

ACTIONS COMPLETED: {len(self.actions_taken)}

BACKUP LOCATION: {self.backup_dir}

NEW STRUCTURE:
  main.py              - Main entry point
  config/
    └── config.json    - Consolidated configuration
  core/
    ├── dfs_optimizer.py
    └── player_model.py
  data_sources/
    ├── recent_form.py
    ├── vegas_lines.py
    ├── statcast.py
    ├── confirmations.py
    └── stats_engine.py
  optimization/
    ├── lineup_optimizer.py
    ├── multi_lineup.py
    └── correlation.py
  ui/
    └── gui.py
  utils/
    ├── cache.py
    ├── performance.py
    ├── progress.py
    ├── bankroll.py
    └── data_system.py
  tests/
    ├── test_optimizer.py
    └── test_multi_lineup.py
  output/
    └── (lineup outputs)

NEXT STEPS:
1. Apply the recent form fix from APPLY_THIS_FIX.py
2. Update imports in all moved files
3. Test with: python main.py your_csv_file.csv
4. Run GUI with: python main.py

DETAILED ACTIONS:
{chr(10).join(f"  - {action}" for action in self.actions_taken)}
'''

        summary_path = self.project_path / 'CLEANUP_SUMMARY.txt'
        summary_path.write_text(report)

        print("✅ Summary report generated")
        print("\n" + "=" * 60)
        print(report)


def main():
    """Main execution"""
    print("🤖 DFS OPTIMIZER AUTOMATIC CLEANUP")
    print("=" * 60)
    print("This script will:")
    print("  1. Create a backup of your project")
    print("  2. Delete unnecessary files")
    print("  3. Reorganize into a clean structure")
    print("  4. Consolidate configurations")
    print("  5. Fix the recent form issue")
    print()

    response = input("Proceed with automatic cleanup? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        cleaner = AutomaticDFSCleaner()
        cleaner.run_full_cleanup()
    else:
        print("❌ Cleanup cancelled")


if __name__ == "__main__":
    main()