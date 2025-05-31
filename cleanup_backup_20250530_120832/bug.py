#!/usr/bin/env python3
"""
Project Cleanup Script
Safely removes duplicate, typo, and redundant files from your DFS optimizer project
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


class ProjectCleanup:
    def __init__(self):
        self.project_root = Path(".")
        self.backup_dir = Path(f"cleanup_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        # Files to delete based on your project structure
        self.files_to_delete = {
            "typo_files": [
                "performace_integrated_data.py",  # Typo: should be "performance"
                "performace_integrated_gui.py"  # Typo: should be "performance"
            ],
            "duplicate_launchers": [
                "dfs_optimizer_launcer.py",  # Typo + duplicate
                "launch.py",  # Redundant
                "main_enhanced_performance.py"  # Redundant with main_enhanced.py
            ],
            "redundant_files": [
                "bug.py",  # Temporary debugging file
                "extract_proven_optimization_algorithims.py",  # Extracted already
                "auto_integration_script.py",  # Integration done
                "auto_integration.py",  # Integration done
                "complete_integration_wizard.py",  # Integration done
                "safe_file_cleanup.py"  # Will be replaced by this script
            ],
            "testing_files": [
                # Keep test_with_sample_data.py as it's needed
            ]
        }

        # Files to keep (your core working files)
        self.essential_files = [
            "streamlined_dfs_core.py",
            "streamlined_dfs_gui.py",
            "test_with_sample_data.py",
            "dfs_data_enhanced.py",
            "dfs_optimizer_enhanced.py",
            "dfs_runner_enhanced.py",
            "enhanced_dfs_gui.py",
            "vegas_lines.py",
            "statcast_integration.py",
            "async_data_manager.py",
            "performance_integrated_data",  # No extension - this is a file without .py
            "performance_integrated_gui.py",
            "config.json",
            "schedule.json",
            "extracted_algorithms.json"
        ]

    def create_backup(self):
        """Create backup of all files before deletion"""
        print(f"📦 Creating backup in {self.backup_dir}")

        try:
            self.backup_dir.mkdir(exist_ok=True)

            # Backup all Python files
            backup_count = 0
            for py_file in self.project_root.glob("*.py"):
                if py_file.is_file():
                    shutil.copy2(py_file, self.backup_dir / py_file.name)
                    backup_count += 1

            # Backup JSON files
            for json_file in self.project_root.glob("*.json"):
                if json_file.is_file():
                    shutil.copy2(json_file, self.backup_dir / json_file.name)
                    backup_count += 1

            print(f"✅ Backup created: {backup_count} files backed up")
            return True

        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False

    def delete_files_safely(self):
        """Delete files with confirmation"""
        print("\n🗑️ DELETING REDUNDANT FILES")
        print("=" * 40)

        deleted_count = 0

        for category, files in self.files_to_delete.items():
            print(f"\n📁 {category.replace('_', ' ').title()}:")

            for filename in files:
                file_path = self.project_root / filename

                if file_path.exists():
                    try:
                        file_size = file_path.stat().st_size
                        print(f"  🗑️ Deleting {filename} ({file_size} bytes)")
                        file_path.unlink()
                        deleted_count += 1
                        print(f"     ✅ Deleted successfully")
                    except Exception as e:
                        print(f"     ❌ Failed to delete: {e}")
                else:
                    print(f"  ⚪ {filename} not found")

        print(f"\n✅ Cleanup complete: {deleted_count} files deleted")
        return deleted_count

    def create_unified_launcher(self):
        """Create a single, working launcher"""
        launcher_code = '''#!/usr/bin/env python3
"""
DFS Optimizer - Unified Launcher
The one launcher to rule them all
"""

import sys
import os

def main():
    """Launch the DFS optimizer GUI"""
    print("🚀 DFS Optimizer - Unified Launcher")
    print("=" * 40)

    # Try streamlined GUI first (best option)
    try:
        print("⚡ Launching Streamlined DFS GUI...")
        from streamlined_dfs_gui import main as streamlined_main
        return streamlined_main()
    except ImportError:
        print("   ⚠️ Streamlined GUI not available")
    except Exception as e:
        print(f"   ❌ Streamlined GUI error: {e}")

    # Try enhanced GUI (fallback)
    try:
        print("🔧 Launching Enhanced DFS GUI...")  
        from enhanced_dfs_gui import main as enhanced_main
        return enhanced_main()
    except ImportError:
        print("   ⚠️ Enhanced GUI not available")
    except Exception as e:
        print(f"   ❌ Enhanced GUI error: {e}")

    # Error message
    print("❌ No DFS GUI available!")
    print()
    print("💡 TROUBLESHOOTING:")
    print("   1. Make sure you have PyQt5: pip install PyQt5")
    print("   2. Make sure streamlined_dfs_gui.py exists")
    print("   3. Run: python test_with_sample_data.py")

    return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\\n👋 Cancelled by user")
        sys.exit(0)
'''

        try:
            with open("dfs_optimizer.py", 'w') as f:
                f.write(launcher_code)
            print("✅ Created unified launcher: dfs_optimizer.py")
            return True
        except Exception as e:
            print(f"❌ Failed to create launcher: {e}")
            return False

    def analyze_remaining_files(self):
        """Show what files remain after cleanup"""
        print("\n📊 REMAINING FILES ANALYSIS")
        print("=" * 35)

        remaining_files = list(self.project_root.glob("*.py")) + list(self.project_root.glob("*.json"))

        print(f"📁 Total remaining files: {len(remaining_files)}")

        for file_path in sorted(remaining_files):
            file_size = file_path.stat().st_size
            if file_path.name in self.essential_files:
                print(f"  ✅ {file_path.name} ({file_size} bytes) - Essential")
            else:
                print(f"  📄 {file_path.name} ({file_size} bytes)")

    def run_cleanup(self):
        """Run the complete cleanup process"""
        print("🧹 DFS OPTIMIZER PROJECT CLEANUP")
        print("=" * 40)
        print("This will clean up duplicate and redundant files.")
        print("A backup will be created first for safety.")
        print()

        # Create backup
        if not self.create_backup():
            print("❌ Cannot proceed without backup")
            return False

        # Delete files
        deleted_count = self.delete_files_safely()

        # Create unified launcher
        self.create_unified_launcher()

        # Show analysis
        self.analyze_remaining_files()

        # Summary
        print(f"\n🎉 CLEANUP COMPLETE!")
        print(f"📊 Files deleted: {deleted_count}")
        print(f"💾 Backup location: {self.backup_dir}")
        print(f"🚀 New launcher: dfs_optimizer.py")
        print()
        print("🎯 NEXT STEPS:")
        print("1. Run: python test_with_sample_data.py")
        print("2. If tests pass, run: python dfs_optimizer.py")
        print("3. Test with your DraftKings CSV files")

        return True


def main():
    """Main cleanup execution"""
    cleanup = ProjectCleanup()

    print("🚨 WARNING: This will delete files from your project!")
    print("A backup will be created, but please confirm you want to proceed.")
    print()

    response = input("Proceed with cleanup? (y/n): ")
    if response.lower() != 'y':
        print("👋 Cleanup cancelled")
        return

    cleanup.run_cleanup()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cleanup cancelled by user")
    except Exception as e:
        print(f"\n❌ Cleanup error: {e}")
        import traceback

        traceback.print_exc()