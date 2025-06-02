#!/usr/bin/env python3
"""
CLEANUP OLD FILES SCRIPT
========================
Removes old, duplicate, and unnecessary files from the DFS system
✅ Keeps only the bulletproof core files
✅ Removes conflicting old systems
✅ Cleans up temporary files
✅ Preserves user data (CSV files)
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime


class DFSSystemCleaner:
    """Clean up old DFS system files"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.cleaned_files = []
        self.preserved_files = []
        self.errors = []

        # Files to keep (essential bulletproof system)
        self.keep_files = {
            'bulletproof_dfs_core.py',
            'enhanced_dfs_gui.py',
            'test_bulletproof_system.py',
            'update_system_automatically.py',
            'cleanup_old_files.py',
            'launch_bulletproof_dfs.py',
            'vegas_lines.py',
            'confirmed_lineups.py',
            'simple_statcast_fetcher.py'
        }

        # File patterns to remove (old/conflicting systems)
        self.remove_patterns = [
            '*dfs_core*.py',
            '*optimizer*.py',
            '*statcast*.py',
            '*vegas*.py',
            '*lineup*.py',
            '*confirmed*.py',
            'dfs_data.py',
            'advanced_*.py',
            'optimized_*.py',
            'enhanced_*.py',
            'smart_*.py',
            'pro_*.py'
        ]

        # File patterns to keep (user data)
        self.preserve_patterns = [
            'DKSalaries*.csv',
            '*dff*.csv',
            '*cheat*.csv',
            '*.xlsx',
            'backups/'
        ]

    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def is_file_protected(self, file_path):
        """Check if file should be protected from deletion"""
        file_name = file_path.name

        # Always keep essential files
        if file_name in self.keep_files:
            return True

        # Keep files matching preserve patterns
        for pattern in self.preserve_patterns:
            if file_path.match(pattern):
                return True

        # Keep this cleanup script
        if file_name == Path(__file__).name:
            return True

        return False

    def should_remove_file(self, file_path):
        """Check if file should be removed"""
        file_name = file_path.name

        # Don't remove if protected
        if self.is_file_protected(file_path):
            return False

        # Remove files matching removal patterns
        for pattern in self.remove_patterns:
            if file_path.match(pattern):
                return True

        # Remove old Python files that might conflict
        if file_name.endswith('.py'):
            old_keywords = [
                'old_', 'backup_', 'test_old', 'deprecated_',
                'temp_', 'draft_', 'experimental_'
            ]
            if any(keyword in file_name.lower() for keyword in old_keywords):
                return True

        return False

    def analyze_files(self):
        """Analyze which files will be affected"""
        self.log("🔍 Analyzing files...")

        to_remove = []
        to_keep = []

        for file_path in self.script_dir.iterdir():
            if file_path.is_file():
                if self.should_remove_file(file_path):
                    to_remove.append(file_path)
                elif self.is_file_protected(file_path):
                    to_keep.append(file_path)

        self.log(f"📊 Analysis Results:")
        self.log(f"   Files to remove: {len(to_remove)}")
        self.log(f"   Files to keep: {len(to_keep)}")

        if to_remove:
            self.log(f"\n🗑️ Files that will be REMOVED:")
            for file_path in sorted(to_remove):
                self.log(f"   ❌ {file_path.name}")

        if to_keep:
            self.log(f"\n✅ Files that will be KEPT:")
            for file_path in sorted(to_keep):
                self.log(f"   ✅ {file_path.name}")

        return to_remove, to_keep

    def create_backup_before_cleanup(self, files_to_remove):
        """Create backup before removing files"""
        if not files_to_remove:
            return True

        self.log("💾 Creating cleanup backup...")

        backup_dir = self.script_dir / "cleanup_backup" / f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        backed_up = 0
        for file_path in files_to_remove:
            try:
                shutil.copy2(file_path, backup_dir)
                backed_up += 1
            except Exception as e:
                self.log(f"   ⚠️ Could not backup {file_path.name}: {e}")

        self.log(f"✅ Backup created: {backed_up} files in {backup_dir}")
        return True

    def remove_files(self, files_to_remove):
        """Remove the specified files"""
        if not files_to_remove:
            self.log("✅ No files to remove")
            return True

        self.log(f"🗑️ Removing {len(files_to_remove)} files...")

        for file_path in files_to_remove:
            try:
                file_path.unlink()
                self.cleaned_files.append(file_path.name)
                self.log(f"   ✅ Removed {file_path.name}")
            except Exception as e:
                self.errors.append(f"{file_path.name}: {e}")
                self.log(f"   ❌ Failed to remove {file_path.name}: {e}")

        return len(self.errors) == 0

    def clean_temp_files(self):
        """Clean temporary files and cache"""
        self.log("🧹 Cleaning temporary files...")

        temp_patterns = [
            '__pycache__/',
            '*.pyc',
            '*.pyo',
            '*.tmp',
            '.DS_Store',
            'Thumbs.db',
            '*.log'
        ]

        cleaned_temp = 0
        for pattern in temp_patterns:
            for file_path in self.script_dir.rglob(pattern):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        cleaned_temp += 1
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                        cleaned_temp += 1
                except Exception as e:
                    self.log(f"   ⚠️ Could not remove {file_path}: {e}")

        self.log(f"✅ Cleaned {cleaned_temp} temporary files")

    def verify_essential_files(self):
        """Verify that essential files still exist"""
        self.log("🔍 Verifying essential files...")

        missing_essential = []
        for essential_file in ['bulletproof_dfs_core.py', 'enhanced_dfs_gui.py']:
            file_path = self.script_dir / essential_file
            if not file_path.exists():
                missing_essential.append(essential_file)

        if missing_essential:
            self.log(f"❌ CRITICAL: Missing essential files: {missing_essential}")
            return False
        else:
            self.log("✅ All essential files present")
            return True

    def run_cleanup(self, interactive=True):
        """Run the complete cleanup process"""
        self.log("🧹 BULLETPROOF DFS SYSTEM CLEANUP")
        self.log("=" * 50)

        # Analyze files
        to_remove, to_keep = self.analyze_files()

        if not to_remove:
            self.log("✅ No old files found - system is already clean!")
            self.clean_temp_files()
            return True

        # Interactive confirmation
        if interactive:
            self.log(f"\n⚠️ WARNING: About to remove {len(to_remove)} files")
            response = input("Continue with cleanup? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                self.log("❌ Cleanup cancelled by user")
                return False

        # Create backup
        if not self.create_backup_before_cleanup(to_remove):
            self.log("❌ Backup failed - aborting cleanup")
            return False

        # Remove files
        success = self.remove_files(to_remove)

        # Clean temp files
        self.clean_temp_files()

        # Verify essential files
        if not self.verify_essential_files():
            self.log("❌ Essential files missing after cleanup!")
            return False

        # Summary
        self.log(f"\n🎯 CLEANUP SUMMARY")
        self.log("=" * 50)

        if success and not self.errors:
            self.log("🎉 CLEANUP SUCCESSFUL!")
            self.log(f"✅ Removed {len(self.cleaned_files)} old files")
            self.log("✅ Essential bulletproof files preserved")
            self.log("✅ User data (CSV files) preserved")
            self.log("")
            self.log("🚀 Your bulletproof DFS system is now clean!")
            self.log("   Run: python launch_bulletproof_dfs.py")
        else:
            self.log(f"⚠️ Cleanup completed with {len(self.errors)} errors:")
            for error in self.errors:
                self.log(f"   ❌ {error}")

        return success and len(self.errors) == 0


def main():
    """Main cleanup function"""
    cleaner = DFSSystemCleaner()

    # Check for command line arguments
    interactive = True
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-y', '--yes', '--auto']:
            interactive = False
        elif sys.argv[1] in ['-h', '--help']:
            print("DFS System Cleanup Script")
            print("Usage:")
            print("  python cleanup_old_files.py          # Interactive mode")
            print("  python cleanup_old_files.py -y       # Automatic mode")
            print("  python cleanup_old_files.py --help   # Show this help")
            return 0

    return 0 if cleaner.run_cleanup(interactive) else 1


if __name__ == "__main__":
    sys.exit(main())