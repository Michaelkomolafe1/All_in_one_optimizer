#!/usr/bin/env python3
"""
DFS Optimizer - Fully Automated Cleanup Script
This script will automatically clean and organize your project
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import sys


class AutoCleanup:
    def __init__(self):
        self.root = Path.cwd()
        self.backup_dir = self.root.parent / f"optimizer_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Essential files to keep
        self.essential_files = {
            # Core files
            'unified_player_model.py',
            'unified_milp_optimizer.py',
            'optimized_data_pipeline.py',
            'working_dfs_core_final.py',
            # GUI
            'enhanced_dfs_gui.py',
            # Utilities
            'vegas_lines.py',
            'simple_statcast_fetcher.py',
            'batting_order_correlation_system.py',
            # CLI
            'dfs_cli.py',
            # Docs
            'README.md',
            'requirements.txt'
        }

        # Files to archive (not delete)
        self.archive_patterns = {
            'old_dirs': ['old_files_archive', 'archives', 'archive'],
            'old_guis': ['streamlined_dfs_gui.py', '*_gui.py.backup'],
            'old_launchers': ['launch_enhanced*.py', 'launch_with_statcast.py',
                              'launch_streamlined*.py', 'launch_advanced.py'],
            'old_tests': ['test_*.py', '*_test.py'],
            'old_docs': ['DEPLOYMENT_REPORT_*.md', 'INTEGRATION_SUMMARY.md',
                         'CLEANUP_REPORT_*.md', 'project_info.json'],
            'backups': ['*.backup', '*.backup_timing'],
            'misc': ['bug.py', 'test_dfs_components.py']
        }

        # Files safe to delete
        self.delete_patterns = [
            '__pycache__',
            '*.pyc',
            '*.html',
            '.pytest_cache'
        ]

    def run(self):
        """Run the complete automated cleanup"""
        print("🧹 DFS OPTIMIZER - AUTOMATED CLEANUP")
        print("=" * 50)
        print(f"📁 Working directory: {self.root}")
        print(f"💾 Backup location: {self.backup_dir}")
        print()

        # Step 1: Check essential files
        print("1️⃣ Checking essential files...")
        missing = self.check_essential_files()
        if missing:
            print(f"⚠️  Warning: Missing files: {', '.join(missing)}")
            print("   These files might be named differently or in subdirectories")

        # Step 2: Create backup
        print("\n2️⃣ Creating backup...")
        if not self.create_backup():
            print("❌ Backup failed! Aborting cleanup.")
            return False

        # Step 3: Create directory structure
        print("\n3️⃣ Creating directory structure...")
        self.create_directories()

        # Step 4: Archive old files
        print("\n4️⃣ Archiving old files...")
        archived = self.archive_old_files()
        print(f"   📦 Archived {archived} items")

        # Step 5: Move data files
        print("\n5️⃣ Organizing data files...")
        moved = self.organize_data_files()
        print(f"   📊 Moved {moved} data files")

        # Step 6: Handle launcher
        print("\n6️⃣ Setting up launcher...")
        self.setup_launcher()

        # Step 7: Clean up
        print("\n7️⃣ Cleaning up temporary files...")
        deleted = self.cleanup_temp_files()
        print(f"   🗑️  Deleted {deleted} temporary files/folders")

        # Step 8: Final check
        print("\n8️⃣ Final verification...")
        self.verify_cleanup()

        print("\n✅ CLEANUP COMPLETE!")
        print("\n📋 Summary:")
        print(f"   • Essential files preserved: {len(self.essential_files)}")
        print(f"   • Files archived: {archived}")
        print(f"   • Data files organized: {moved}")
        print(f"   • Temp files cleaned: {deleted}")
        print(f"   • Backup created at: {self.backup_dir}")

        print("\n🚀 Next steps:")
        print("   1. Test your system: python launch_optimizer.py")
        print("   2. If everything works, you can delete the backup later")
        print("   3. Old files are in 'archive/' - safe to delete after testing")

        return True

    def check_essential_files(self):
        """Check which essential files exist"""
        missing = []
        for file in self.essential_files:
            if not (self.root / file).exists():
                missing.append(file)
        return missing

    def create_backup(self):
        """Create a complete backup"""
        try:
            print(f"   Creating backup at: {self.backup_dir}")
            shutil.copytree(self.root, self.backup_dir,
                            ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
            print("   ✅ Backup created successfully")
            return True
        except Exception as e:
            print(f"   ❌ Backup failed: {e}")
            return False

    def create_directories(self):
        """Create the organized directory structure"""
        dirs = [
            'archive/old_files',
            'archive/old_launchers',
            'archive/old_guis',
            'archive/old_tests',
            'archive/old_docs',
            'archive/backups',
            'data/sample_data',
            'data/cache'
        ]

        for dir_path in dirs:
            (self.root / dir_path).mkdir(parents=True, exist_ok=True)
        print("   ✅ Directory structure created")

    def archive_old_files(self):
        """Archive old files to appropriate subdirectories"""
        archived = 0

        # Archive old directories
        for old_dir in self.archive_patterns['old_dirs']:
            if (self.root / old_dir).exists() and (self.root / old_dir).is_dir():
                try:
                    shutil.move(str(self.root / old_dir),
                                str(self.root / 'archive' / 'old_files' / old_dir))
                    archived += 1
                except:
                    pass

        # Archive files by category
        for category, patterns in self.archive_patterns.items():
            if category == 'old_dirs':
                continue

            target_dir = self.root / 'archive' / category
            for pattern in patterns:
                for file in self.root.glob(pattern):
                    if file.is_file() and file.name not in self.essential_files:
                        try:
                            shutil.move(str(file), str(target_dir / file.name))
                            archived += 1
                        except:
                            pass

        return archived

    def organize_data_files(self):
        """Move CSV files to data directory"""
        moved = 0
        data_dir = self.root / 'data' / 'sample_data'

        for csv_file in self.root.glob('*.csv'):
            try:
                shutil.move(str(csv_file), str(data_dir / csv_file.name))
                moved += 1
            except:
                pass

        return moved

    def setup_launcher(self):
        """Find best launcher and rename it"""
        # Look for existing launchers
        launchers = list(self.root.glob('launch_*.py'))

        if not launchers:
            print("   ⚠️  No launcher found, creating one...")
            self.create_launcher()
        else:
            # Find the best launcher (prefer launch_dfs_optimizer.py)
            best_launcher = None
            for launcher in launchers:
                if 'dfs_optimizer' in launcher.name:
                    best_launcher = launcher
                    break

            if not best_launcher:
                best_launcher = launchers[0]

            # Rename to launch_optimizer.py
            if best_launcher.name != 'launch_optimizer.py':
                best_launcher.rename(self.root / 'launch_optimizer.py')
                print(f"   ✅ Renamed {best_launcher.name} → launch_optimizer.py")
            else:
                print("   ✅ Launcher already set up")

    def create_launcher(self):
        """Create a simple launcher if none exists"""
        launcher_content = '''#!/usr/bin/env python3
"""DFS Optimizer - Main Launcher"""

import sys
from pathlib import Path

def main():
    """Launch the DFS Optimizer GUI"""
    try:
        from enhanced_dfs_gui import main as gui_main
        print("🚀 Launching DFS Optimizer...")
        return gui_main()
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''

        launcher_path = self.root / 'launch_optimizer.py'
        launcher_path.write_text(launcher_content)
        launcher_path.chmod(0o755)
        print("   ✅ Created launch_optimizer.py")

    def cleanup_temp_files(self):
        """Delete temporary and cache files"""
        deleted = 0

        for pattern in self.delete_patterns:
            if '*' in pattern:
                # It's a glob pattern
                for file in self.root.glob(pattern):
                    try:
                        if file.is_file():
                            file.unlink()
                        else:
                            shutil.rmtree(file)
                        deleted += 1
                    except:
                        pass
            else:
                # It's a directory name
                path = self.root / pattern
                if path.exists():
                    try:
                        shutil.rmtree(path)
                        deleted += 1
                    except:
                        pass

        return deleted

    def verify_cleanup(self):
        """Verify the cleanup was successful"""
        # Count remaining files in root
        root_files = [f for f in self.root.iterdir() if f.is_file()]
        root_dirs = [d for d in self.root.iterdir() if d.is_dir() and d.name != '.git']

        print(f"   📁 Root directory now contains:")
        print(f"      • {len(root_files)} files")
        print(f"      • {len(root_dirs)} directories")

        # Check essential files
        essential_found = []
        for file in self.essential_files:
            if (self.root / file).exists():
                essential_found.append(file)

        # Check for launcher
        if (self.root / 'launch_optimizer.py').exists():
            essential_found.append('launch_optimizer.py')

        print(f"   ✅ Essential files found: {len(essential_found)}/{len(self.essential_files) + 1}")

        if len(essential_found) < len(self.essential_files):
            print("   ⚠️  Some essential files are missing - check the archive folder")


def main():
    """Main entry point"""
    print("🤖 DFS Optimizer - Automated Cleanup Tool")
    print()

    # Confirm with user
    print("This script will:")
    print("  1. Create a backup of your entire project")
    print("  2. Archive old files (not delete them)")
    print("  3. Organize your project structure")
    print("  4. Clean up temporary files")
    print()

    response = input("Ready to proceed? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("❌ Cleanup cancelled")
        return 1

    # Run cleanup
    cleanup = AutoCleanup()
    success = cleanup.run()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())