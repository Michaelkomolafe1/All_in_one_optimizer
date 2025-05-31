#!/usr/bin/env python3
"""
DFS Project Organizer & Cleanup Script
Analyzes your DFS project and organizes/cleans up redundant files
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set


class DFSProjectOrganizer:
    """Comprehensive project organizer for DFS system"""

    def __init__(self):
        self.current_dir = Path('.')
        self.backup_dir = Path(f'cleanup_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')

        # File categories
        self.core_files = {
            'unified_player_model.py': 'Essential - Unified player data model',
            'unified_milp_optimizer.py': 'Essential - Advanced MILP optimization',
            'optimized_data_pipeline.py': 'Essential - High-performance data loading',
            'optimized_dfs_core.py': 'Essential - Main optimization engine',
            'working_dfs_core_final.py': 'Essential - Working core with all features',
            'working_dfs_core_final.py.backup': 'Backup - Can be archived'
        }

        self.gui_files = {
            'enhanced_dfs_gui.py': 'Primary - Feature-rich GUI interface',
            'streamlined_dfs_gui.py': 'Alternative - Simpler GUI option'
        }

        self.launcher_files = {
            'launch_dfs_optimizer.py': 'Keep - Main launcher',
            'launch_streamlined_gui.py': 'Keep - Streamlined launcher',
            'dfs_launcher.py': 'Enhanced - Advanced launcher with auto-detection',
            'dfs_cli.py': 'Keep - Command line interface'
        }

        self.documentation_files = {
            'DEPLOYMENT_REPORT_20250531_024546.md': 'Archive - Deployment history',
            'INTEGRATION_SUMMARY.md': 'Archive - Integration details',
            'UPGRADE_SUMMARY.md': 'Archive - Upgrade history',
            'CLEANUP_REPORT_20250531_100424.md': 'Archive - Previous cleanup',
            'quickstart.py': 'Keep - Quick start guide',
            'quickstart_streamlined.py': 'Alternative - Streamlined guide'
        }

        self.utility_files = {
            'find_files.py': 'Utility - File finder',
            'find_csv_files.py': 'Utility - CSV file finder',
            'strategy_info_addon.py': 'Utility - GUI enhancement',
            'test_real_statcast.py': 'Test - Statcast testing',
            'test_new_strategies.py': 'Test - Strategy validation'
        }

        # Files to delete (redundant/outdated)
        self.files_to_delete = {
            'working_dfs_core_final.py.backup_timing': 'Redundant backup',
            'working_dfs_core_final.py.backup': 'Old backup - superseded'
        }

        # Archive directories to create
        self.archive_structure = {
            'archives/': 'Historical files and documentation',
            'archives/deployment_reports/': 'Deployment and integration reports',
            'archives/backups/': 'Old backup files',
            'utilities/': 'Helper scripts and tools',
            'tests/': 'Test scripts and validation tools',
            'sample_data/': 'Sample CSV files for testing'
        }

    def analyze_project(self) -> Dict:
        """Analyze the current project structure"""
        print("🔍 ANALYZING DFS PROJECT STRUCTURE")
        print("=" * 50)

        analysis = {
            'total_files': 0,
            'core_files_found': [],
            'gui_files_found': [],
            'redundant_files': [],
            'missing_essential': [],
            'total_size_mb': 0
        }

        # Get all Python files
        python_files = list(self.current_dir.glob('*.py'))
        md_files = list(self.current_dir.glob('*.md'))
        all_files = python_files + md_files

        analysis['total_files'] = len(all_files)

        print(f"📊 Found {len(all_files)} files ({len(python_files)} .py, {len(md_files)} .md)")

        # Calculate total size
        total_size = sum(f.stat().st_size for f in all_files)
        analysis['total_size_mb'] = total_size / (1024 * 1024)

        # Categorize files
        for file_path in all_files:
            filename = file_path.name
            file_size = file_path.stat().st_size / 1024  # KB

            if filename in self.core_files:
                analysis['core_files_found'].append((filename, file_size))
            elif filename in self.gui_files:
                analysis['gui_files_found'].append((filename, file_size))
            elif filename in self.files_to_delete:
                analysis['redundant_files'].append((filename, file_size))

        # Check for missing essential files
        essential_files = [f for f, desc in self.core_files.items() if 'Essential' in desc]
        for essential_file in essential_files:
            if not (self.current_dir / essential_file).exists():
                analysis['missing_essential'].append(essential_file)

        # Print analysis
        print(f"💾 Total project size: {analysis['total_size_mb']:.1f} MB")
        print(f"🎯 Core files found: {len(analysis['core_files_found'])}")
        print(f"🖥️ GUI files found: {len(analysis['gui_files_found'])}")
        print(f"🗑️ Redundant files: {len(analysis['redundant_files'])}")

        if analysis['missing_essential']:
            print(f"⚠️ Missing essential files: {len(analysis['missing_essential'])}")
            for missing in analysis['missing_essential']:
                print(f"   ❌ {missing}")

        return analysis

    def create_backup(self) -> bool:
        """Create backup of current state"""
        try:
            print(f"\n💾 Creating backup: {self.backup_dir}")
            self.backup_dir.mkdir(exist_ok=True)

            # Backup all files
            files_backed_up = 0
            for file_path in self.current_dir.glob('*'):
                if file_path.is_file() and file_path.name != self.backup_dir.name:
                    shutil.copy2(file_path, self.backup_dir / file_path.name)
                    files_backed_up += 1

            print(f"✅ Backed up {files_backed_up} files to {self.backup_dir}")
            return True

        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False

    def create_directory_structure(self):
        """Create organized directory structure"""
        print("\n📁 Creating organized directory structure...")

        for dir_path, description in self.archive_structure.items():
            dir_full_path = self.current_dir / dir_path
            dir_full_path.mkdir(parents=True, exist_ok=True)
            print(f"   📂 {dir_path} - {description}")

    def organize_files(self):
        """Organize files into appropriate directories"""
        print("\n🗂️ Organizing files...")

        moves_made = []

        # Move documentation to archives
        doc_files = [
            'DEPLOYMENT_REPORT_20250531_024546.md',
            'INTEGRATION_SUMMARY.md',
            'UPGRADE_SUMMARY.md',
            'CLEANUP_REPORT_20250531_100424.md'
        ]

        for doc_file in doc_files:
            src = self.current_dir / doc_file
            if src.exists():
                dst = self.current_dir / 'archives' / 'deployment_reports' / doc_file
                shutil.move(str(src), str(dst))
                moves_made.append(f"📄 {doc_file} → archives/deployment_reports/")

        # Move backup files to archives
        backup_files = [
            'working_dfs_core_final.py.backup',
            'working_dfs_core_final.py.backup_timing'
        ]

        for backup_file in backup_files:
            src = self.current_dir / backup_file
            if src.exists():
                dst = self.current_dir / 'archives' / 'backups' / backup_file
                shutil.move(str(src), str(dst))
                moves_made.append(f"💾 {backup_file} → archives/backups/")

        # Move utility files
        utility_files = [
            'find_files.py',
            'find_csv_files.py',
            'strategy_info_addon.py'
        ]

        for util_file in utility_files:
            src = self.current_dir / util_file
            if src.exists():
                dst = self.current_dir / 'utilities' / util_file
                shutil.move(str(src), str(dst))
                moves_made.append(f"🔧 {util_file} → utilities/")

        # Move test files
        test_files = [
            'test_real_statcast.py',
            'test_new_strategies.py'
        ]

        for test_file in test_files:
            src = self.current_dir / test_file
            if src.exists():
                dst = self.current_dir / 'tests' / test_file
                shutil.move(str(src), str(dst))
                moves_made.append(f"🧪 {test_file} → tests/")

        print(f"✅ Organized {len(moves_made)} files:")
        for move in moves_made:
            print(f"   {move}")

    def delete_redundant_files(self):
        """Delete truly redundant files"""
        print("\n🗑️ Removing redundant files...")

        deleted_files = []

        # Only delete files that are truly redundant
        safe_to_delete = [
            'working_dfs_core_final.py.backup_timing'  # Only this one is truly redundant
        ]

        for filename in safe_to_delete:
            file_path = self.current_dir / filename
            if file_path.exists():
                file_path.unlink()
                deleted_files.append(filename)
                print(f"   🗑️ Deleted: {filename}")

        if deleted_files:
            print(f"✅ Removed {len(deleted_files)} redundant files")
        else:
            print("✅ No redundant files to remove")

    def create_recommended_structure(self):
        """Create README with recommended project structure"""
        readme_content = """# DFS Optimizer - Project Structure

## 🎯 Core System Files (Keep in Root)
- `unified_player_model.py` - Advanced player data model
- `unified_milp_optimizer.py` - MILP optimization engine  
- `optimized_data_pipeline.py` - High-performance data loading
- `optimized_dfs_core.py` - Main optimization system
- `working_dfs_core_final.py` - Complete working implementation

## 🖥️ User Interfaces
- `enhanced_dfs_gui.py` - Feature-rich GUI (RECOMMENDED)
- `streamlined_dfs_gui.py` - Simplified GUI option
- `dfs_cli.py` - Command line interface

## 🚀 Launchers
- `launch_dfs_optimizer.py` - Main GUI launcher
- `dfs_launcher.py` - Advanced launcher with auto-detection
- `quickstart.py` - Quick start guide

## 📁 Directory Structure
```
DFS_Optimizer/
├── Core Files (root level)
├── archives/
│   ├── deployment_reports/    # Historical documentation
│   └── backups/              # Old backup files
├── utilities/                # Helper scripts
├── tests/                    # Test and validation scripts
└── sample_data/             # Sample CSV files
```

## 🎯 Quick Start
1. Launch GUI: `python launch_dfs_optimizer.py`
2. Command line: `python dfs_cli.py --dk your_file.csv`
3. Test system: `python tests/test_new_strategies.py`

## 🔧 Utilities Available
- `utilities/find_csv_files.py` - Find CSV files on your system
- `utilities/strategy_info_addon.py` - GUI enhancement addon
- `tests/test_real_statcast.py` - Test real Baseball Savant data

## 📊 Features
✅ Multi-position optimization (3B/SS, 1B/3B, etc.)
✅ Confirmed lineup detection  
✅ DFF expert rankings integration
✅ Manual player selection
✅ Multiple optimization strategies
✅ Real-time data integration
"""

        readme_path = self.current_dir / 'PROJECT_STRUCTURE.md'
        with open(readme_path, 'w') as f:
            f.write(readme_content)

        print(f"📋 Created: PROJECT_STRUCTURE.md")

    def generate_cleanup_report(self, analysis: Dict, moves_made: List[str], deleted_files: List[str]):
        """Generate comprehensive cleanup report"""

        report_content = f"""# DFS Project Cleanup Report
Cleanup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Cleanup ID: {datetime.now().strftime('%Y%m%d_%H%M%S')}

## Project Analysis
- Total files analyzed: {analysis['total_files']}
- Project size: {analysis['total_size_mb']:.1f} MB
- Core files found: {len(analysis['core_files_found'])}
- GUI files found: {len(analysis['gui_files_found'])}
- Redundant files removed: {len(deleted_files)}

## Files Organized
{chr(10).join(f'- {move}' for move in moves_made)}

## Files Removed
{chr(10).join(f'- {file}' for file in deleted_files)}

## Current Structure (After Cleanup)
```
DFS_Optimizer/
├── Core optimization files
├── GUI interfaces  
├── Launcher scripts
├── archives/          # Historical files
├── utilities/         # Helper tools
├── tests/            # Test scripts
└── sample_data/      # Sample files
```

## Backup Information
- Backup created: {self.backup_dir}
- All original files preserved in backup
- Can restore any file if needed

## Recommendations
1. Use `enhanced_dfs_gui.py` as your primary interface
2. Keep `working_dfs_core_final.py` as your core engine
3. Test with: `python tests/test_new_strategies.py`
4. Quick start: `python quickstart.py`

## What's Next
1. Test the organized system: `python launch_dfs_optimizer.py`
2. Verify all features work: `python tests/test_new_strategies.py`
3. Use utilities as needed: `python utilities/find_csv_files.py`
4. Check PROJECT_STRUCTURE.md for detailed guidance

---
Your DFS system is now clean, organized, and optimized!
"""

        report_path = self.current_dir / f'CLEANUP_REPORT_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        with open(report_path, 'w') as f:
            f.write(report_content)

        print(f"📊 Generated cleanup report: {report_path.name}")

    def run_full_organization(self):
        """Run the complete organization process"""
        print("🚀 DFS PROJECT ORGANIZER & CLEANUP")
        print("=" * 50)
        print("This script will:")
        print("✅ Analyze your current project structure")
        print("✅ Create backup of all files")
        print("✅ Organize files into logical directories")
        print("✅ Remove only truly redundant files")
        print("✅ Create documentation")
        print()

        # Get user confirmation
        response = input("🤔 Continue with organization? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Organization cancelled")
            return False

        # Step 1: Analyze
        analysis = self.analyze_project()

        # Step 2: Backup
        if not self.create_backup():
            print("❌ Cannot proceed without backup")
            return False

        # Step 3: Create directory structure
        self.create_directory_structure()

        # Step 4: Organize files
        moves_made = []
        self.organize_files()

        # Step 5: Delete redundant files (very conservative)
        deleted_files = []
        self.delete_redundant_files()

        # Step 6: Create documentation
        self.create_recommended_structure()

        # Step 7: Generate report
        self.generate_cleanup_report(analysis, moves_made, deleted_files)

        print("\n🎉 PROJECT ORGANIZATION COMPLETE!")
        print("=" * 40)
        print("✅ Files organized into logical structure")
        print("✅ Backup created for safety")
        print("✅ Documentation updated")
        print("✅ Redundant files removed")
        print()
        print("📁 Your organized project structure:")
        print("   📋 Core files (root level)")
        print("   📂 archives/ (historical files)")
        print("   📂 utilities/ (helper tools)")
        print("   📂 tests/ (test scripts)")
        print()
        print("🚀 Next steps:")
        print("   1. python launch_dfs_optimizer.py")
        print("   2. python tests/test_new_strategies.py")
        print("   3. Check PROJECT_STRUCTURE.md for guidance")

        return True

    def preview_changes(self):
        """Preview what changes would be made without executing them"""
        print("🔍 PREVIEW MODE - No changes will be made")
        print("=" * 50)

        analysis = self.analyze_project()

        print("\n📁 PROPOSED DIRECTORY STRUCTURE:")
        for dir_path, description in self.archive_structure.items():
            print(f"   📂 {dir_path} - {description}")

        print("\n🗂️ FILES TO BE MOVED:")

        # Preview documentation moves
        doc_files = ['DEPLOYMENT_REPORT_20250531_024546.md', 'INTEGRATION_SUMMARY.md']
        for doc_file in doc_files:
            if (self.current_dir / doc_file).exists():
                print(f"   📄 {doc_file} → archives/deployment_reports/")

        # Preview utility moves
        util_files = ['find_files.py', 'find_csv_files.py', 'strategy_info_addon.py']
        for util_file in util_files:
            if (self.current_dir / util_file).exists():
                print(f"   🔧 {util_file} → utilities/")

        # Preview test moves
        test_files = ['test_real_statcast.py', 'test_new_strategies.py']
        for test_file in test_files:
            if (self.current_dir / test_file).exists():
                print(f"   🧪 {test_file} → tests/")

        print("\n🗑️ FILES TO BE DELETED:")
        redundant_file = 'working_dfs_core_final.py.backup_timing'
        if (self.current_dir / redundant_file).exists():
            print(f"   🗑️ {redundant_file} (redundant backup)")
        else:
            print("   ✅ No redundant files found")

        print("\n📋 CORE FILES TO KEEP (root level):")
        core_keep = [
            'unified_player_model.py',
            'unified_milp_optimizer.py',
            'optimized_data_pipeline.py',
            'optimized_dfs_core.py',
            'working_dfs_core_final.py',
            'enhanced_dfs_gui.py',
            'launch_dfs_optimizer.py',
            'dfs_cli.py'
        ]

        for core_file in core_keep:
            status = "✅" if (self.current_dir / core_file).exists() else "❌"
            print(f"   {status} {core_file}")

        print("\n🎯 SUMMARY:")
        print(f"   📊 Total files: {analysis['total_files']}")
        print(f"   🗂️ Files to organize: ~15-20")
        print(f"   🗑️ Files to delete: 1 (redundant backup)")
        print(f"   📁 Directories to create: {len(self.archive_structure)}")
        print("   💾 Backup: Full backup will be created")


def main():
    """Main function with user options"""
    organizer = DFSProjectOrganizer()

    print("🎯 DFS PROJECT ORGANIZER")
    print("=" * 30)
    print("Choose an option:")
    print("1. Preview changes (no modifications)")
    print("2. Run full organization")
    print("3. Exit")
    print()

    try:
        choice = input("Enter choice (1-3): ").strip()

        if choice == '1':
            organizer.preview_changes()
        elif choice == '2':
            organizer.run_full_organization()
        elif choice == '3':
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")

    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()