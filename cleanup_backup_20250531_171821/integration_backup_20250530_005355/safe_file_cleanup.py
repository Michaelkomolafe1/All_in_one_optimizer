#!/usr/bin/env python3
"""
Safe File Cleanup Script
Deletes duplicate/typo files one at a time with confirmation
Based on your actual file structure from the screenshots
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


class SafeFileCleanup:
    """Handles safe deletion of duplicate/redundant files"""

    def __init__(self):
        self.project_root = Path(".")
        self.deleted_files = []
        self.backup_dir = Path("cleanup_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))

        # Files identified from your screenshots
        self.cleanup_targets = {
            "typo_duplicates": {
                "performace_integrated_data.py": {
                    "reason": "Typo in filename (should be 'performance')",
                    "safe_to_delete": True,
                    "correct_version": "performance_integrated_data.py"
                },
                "performace_integrated_gui.py": {
                    "reason": "Typo in filename (should be 'performance')",
                    "safe_to_delete": True,
                    "correct_version": "performance_integrated_gui.py"
                }
            },
            "redundant_launchers": {
                "launch.py": {
                    "reason": "Redundant launcher - multiple launchers exist",
                    "safe_to_delete": False,  # Need to check dependencies first
                    "action": "consolidate"
                },
                "dfs_optimizer_launcher.py": {
                    "reason": "Redundant launcher - multiple launchers exist",
                    "safe_to_delete": False,
                    "action": "consolidate"
                },
                "main_enhanced_performance.py": {
                    "reason": "Redundant launcher - multiple launchers exist",
                    "safe_to_delete": False,
                    "action": "consolidate"
                }
            },
            "duplicate_integrations": {
                "performance_integrated_data.py": {
                    "reason": "Duplicate of async_data_manager.py functionality",
                    "safe_to_delete": False,  # Need to merge first
                    "action": "needs_review"
                },
                "performance_integrated_gui.py": {
                    "reason": "Duplicate of enhanced_dfs_gui.py functionality",
                    "safe_to_delete": False,
                    "action": "needs_review"
                }
            }
        }

    def create_safety_backup(self):
        """Create backup before any deletions"""
        print(f"📦 Creating safety backup in {self.backup_dir}")

        try:
            self.backup_dir.mkdir(exist_ok=True)

            backup_count = 0
            for py_file in self.project_root.glob("*.py"):
                if py_file.is_file():
                    shutil.copy2(py_file, self.backup_dir / py_file.name)
                    backup_count += 1

            print(f"✅ Safety backup created: {backup_count} files backed up")
            return True

        except Exception as e:
            print(f"❌ Backup creation failed: {e}")
            return False

    def analyze_file_before_deletion(self, filename: str):
        """Analyze file before deletion to check for unique code"""
        file_path = self.project_root / filename

        if not file_path.exists():
            return {"exists": False}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            analysis = {
                "exists": True,
                "size": len(content),
                "lines": len(content.split('\n')),
                "has_classes": "class " in content,
                "has_functions": "def " in content,
                "has_imports": "import " in content,
                "unique_identifiers": []
            }

            # Look for unique function/class names
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('def ') or line.startswith('class '):
                    identifier = line.split('(')[0].split(':')[0]
                    analysis["unique_identifiers"].append(identifier)

            return analysis

        except Exception as e:
            return {"exists": True, "error": str(e)}

    def delete_typo_files_safely(self):
        """Delete files with obvious typos (safest deletions)"""
        print("\n🗑️ DELETING TYPO DUPLICATE FILES")
        print("=" * 40)
        print("These files have typos in their names and are safe to delete:")

        for filename, info in self.cleanup_targets["typo_duplicates"].items():
            print(f"\n📄 Analyzing: {filename}")
            print(f"   Reason: {info['reason']}")

            if info.get("correct_version"):
                correct_file = self.project_root / info["correct_version"]
                if correct_file.exists():
                    print(f"   ✅ Correct version exists: {info['correct_version']}")
                else:
                    print(f"   ⚠️ Correct version missing: {info['correct_version']}")

            # Analyze the file
            analysis = self.analyze_file_before_deletion(filename)

            if not analysis["exists"]:
                print(f"   ⚪ File doesn't exist - skipping")
                continue

            print(f"   📊 File size: {analysis.get('size', 0)} bytes")
            print(f"   📊 Lines: {analysis.get('lines', 0)}")

            if analysis.get("unique_identifiers"):
                print(f"   🔍 Contains: {', '.join(analysis['unique_identifiers'][:3])}...")

            # Confirm deletion
            if info["safe_to_delete"]:
                response = input(f"   ❓ Delete {filename}? (y/n/s=skip): ").lower()

                if response == 'y':
                    try:
                        file_path = self.project_root / filename
                        file_path.unlink()
                        self.deleted_files.append(filename)
                        print(f"   ✅ Deleted: {filename}")
                    except Exception as e:
                        print(f"   ❌ Failed to delete {filename}: {e}")
                elif response == 's':
                    print(f"   ⏭️ Skipped: {filename}")
                else:
                    print(f"   🚫 Kept: {filename}")
            else:
                print(f"   🔒 Marked as not safe to delete")

    def analyze_redundant_launchers(self):
        """Analyze redundant launcher files"""
        print("\n🔍 ANALYZING REDUNDANT LAUNCHERS")
        print("=" * 40)

        launcher_analysis = {}

        for filename, info in self.cleanup_targets["redundant_launchers"].items():
            print(f"\n📄 Analyzing: {filename}")

            analysis = self.analyze_file_before_deletion(filename)

            if not analysis["exists"]:
                print(f"   ⚪ File doesn't exist")
                continue

            print(f"   📊 Size: {analysis.get('size', 0)} bytes")
            print(f"   📊 Lines: {analysis.get('lines', 0)}")

            if analysis.get("unique_identifiers"):
                print(f"   🔍 Functions/Classes: {', '.join(analysis['unique_identifiers'])}")

            launcher_analysis[filename] = analysis

        # Recommend which launcher to keep
        print(f"\n💡 LAUNCHER RECOMMENDATIONS:")

        existing_launchers = [(f, a) for f, a in launcher_analysis.items() if a.get("exists")]

        if existing_launchers:
            # Find the most complete launcher
            best_launcher = max(existing_launchers, key=lambda x: x[1].get("size", 0))
            print(f"   🎯 Recommended to keep: {best_launcher[0]} (largest/most complete)")

            for filename, analysis in existing_launchers:
                if filename != best_launcher[0]:
                    print(f"   🗑️ Can delete: {filename}")

        return launcher_analysis

    def create_unified_launcher(self):
        """Create a single unified launcher"""
        print(f"\n🔗 CREATING UNIFIED LAUNCHER")
        print("=" * 30)

        unified_launcher_code = '''#!/usr/bin/env python3
"""
Unified DFS Optimizer Launcher
Created by safe cleanup script
"""

import sys
import os

def main():
    """Unified launcher - tries GUI options in order of preference"""
    print("🚀 DFS Optimizer Unified Launcher")

    # Try streamlined GUI first (new system)
    try:
        print("⚡ Attempting to launch Streamlined GUI...")
        from streamlined_dfs_gui import main as streamlined_main
        return streamlined_main()
    except ImportError:
        print("   ⚠️ Streamlined GUI not available")
    except Exception as e:
        print(f"   ❌ Streamlined GUI error: {e}")

    # Try enhanced GUI (existing system)
    try:
        print("🔧 Attempting to launch Enhanced GUI...")
        from enhanced_dfs_gui import main as enhanced_main
        return enhanced_main()
    except ImportError:
        print("   ⚠️ Enhanced GUI not available")
    except Exception as e:
        print(f"   ❌ Enhanced GUI error: {e}")

    # Try performance integrated GUI
    try:
        print("⚡ Attempting to launch Performance GUI...")
        from performance_integrated_gui import main as perf_main
        return perf_main()
    except ImportError:
        print("   ⚠️ Performance GUI not available")
    except Exception as e:
        print(f"   ❌ Performance GUI error: {e}")

    # No GUI available
    print("❌ No GUI systems available!")
    print("💡 Make sure you have the required files:")
    print("   - streamlined_dfs_gui.py (recommended)")
    print("   - enhanced_dfs_gui.py (fallback)")
    print("   - PyQt5 installed: pip install PyQt5")

    return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\\n👋 Cancelled by user")
        sys.exit(0)
'''

        try:
            with open("unified_launcher.py", 'w') as f:
                f.write(unified_launcher_code)
            print("✅ Created unified_launcher.py")
            return True
        except Exception as e:
            print(f"❌ Failed to create unified launcher: {e}")
            return False

    def interactive_cleanup(self):
        """Interactive cleanup process"""
        print("🧹 INTERACTIVE FILE CLEANUP")
        print("=" * 40)
        print("This will safely clean up duplicate and redundant files.")
        print("You'll be asked to confirm each deletion.\n")

        # Step 1: Safety backup
        if input("Create safety backup first? (y/n): ").lower() == 'y':
            if not self.create_safety_backup():
                print("❌ Cannot proceed without backup")
                return False

        # Step 2: Delete typo files
        if input("Delete files with typos in names? (y/n): ").lower() == 'y':
            self.delete_typo_files_safely()

        # Step 3: Analyze launchers
        if input("Analyze redundant launcher files? (y/n): ").lower() == 'y':
            self.analyze_redundant_launchers()

        # Step 4: Create unified launcher
        if input("Create unified launcher? (y/n): ").lower() == 'y':
            self.create_unified_launcher()

        # Summary
        print(f"\n📊 CLEANUP SUMMARY")
        print("=" * 20)
        print(f"Files deleted: {len(self.deleted_files)}")
        if self.deleted_files:
            print("Deleted files:")
            for file in self.deleted_files:
                print(f"  - {file}")

        if self.backup_dir.exists():
            print(f"Backup location: {self.backup_dir}")

        return True

    def restore_from_backup(self):
        """Restore files from backup if needed"""
        if not self.backup_dir.exists():
            print("❌ No backup directory found")
            return False

        print(f"🔄 RESTORE FROM BACKUP")
        print("=" * 25)
        print(f"Backup location: {self.backup_dir}")

        backup_files = list(self.backup_dir.glob("*.py"))
        print(f"Available files in backup: {len(backup_files)}")

        if input("Restore all files from backup? (y/n): ").lower() == 'y':
            try:
                restored_count = 0
                for backup_file in backup_files:
                    target_file = self.project_root / backup_file.name
                    shutil.copy2(backup_file, target_file)
                    restored_count += 1
                    print(f"  ✅ Restored: {backup_file.name}")

                print(f"✅ Restored {restored_count} files from backup")
                return True

            except Exception as e:
                print(f"❌ Restore failed: {e}")
                return False

        return False


def quick_typo_cleanup():
    """Quick cleanup of obvious typo files only"""
    print("🚀 QUICK TYPO CLEANUP")
    print("=" * 25)
    print("This will only delete files with obvious typos in their names.")
    print("This is the safest cleanup option.\n")

    typo_files = [
        "performace_integrated_data.py",  # Typo: should be "performance"
        "performace_integrated_gui.py"  # Typo: should be "performance"
    ]

    project_root = Path(".")
    deleted_files = []

    for typo_file in typo_files:
        file_path = project_root / typo_file

        if file_path.exists():
            print(f"📄 Found typo file: {typo_file}")

            # Check if correct version exists
            correct_file = typo_file.replace("performace", "performance")
            correct_path = project_root / correct_file

            if correct_path.exists():
                print(f"   ✅ Correct version exists: {correct_file}")

                if input(f"   ❓ Delete typo file {typo_file}? (y/n): ").lower() == 'y':
                    try:
                        file_path.unlink()
                        deleted_files.append(typo_file)
                        print(f"   ✅ Deleted: {typo_file}")
                    except Exception as e:
                        print(f"   ❌ Failed to delete: {e}")
                else:
                    print(f"   🚫 Kept: {typo_file}")
            else:
                print(f"   ⚠️ Correct version not found: {correct_file}")
                print(f"   🔒 Keeping typo file for safety")
        else:
            print(f"⚪ Not found: {typo_file}")

    print(f"\n📊 Quick cleanup complete!")
    print(f"Files deleted: {len(deleted_files)}")
    if deleted_files:
        for file in deleted_files:
            print(f"  - {file}")

    return len(deleted_files) > 0


def create_project_analysis():
    """Create analysis of current project structure"""
    print("🔍 PROJECT STRUCTURE ANALYSIS")
    print("=" * 35)

    project_root = Path(".")

    # Categorize files
    file_categories = {
        "core_optimizers": [],
        "data_handlers": [],
        "gui_interfaces": [],
        "launchers": [],
        "integrations": [],
        "utilities": [],
        "config_files": [],
        "unknown": []
    }

    # Classification rules
    classification_rules = {
        "core_optimizers": ["optimizer", "milp", "monte_carlo"],
        "data_handlers": ["data", "csv", "import", "load"],
        "gui_interfaces": ["gui", "interface", "window"],
        "launchers": ["launch", "main", "run", "start"],
        "integrations": ["integration", "api", "vegas", "statcast"],
        "utilities": ["util", "helper", "tool"],
        "config_files": [".json", ".cfg", ".ini"]
    }

    # Analyze each Python file
    for py_file in project_root.glob("*.py"):
        if py_file.is_file():
            filename = py_file.name.lower()
            categorized = False

            for category, keywords in classification_rules.items():
                if any(keyword in filename for keyword in keywords):
                    file_categories[category].append(py_file.name)
                    categorized = True
                    break

            if not categorized:
                file_categories["unknown"].append(py_file.name)

    # Add JSON files
    for json_file in project_root.glob("*.json"):
        if json_file.is_file():
            file_categories["config_files"].append(json_file.name)

    # Display analysis
    total_files = sum(len(files) for files in file_categories.values())
    print(f"📊 Total files analyzed: {total_files}")
    print()

    for category, files in file_categories.items():
        if files:
            print(f"📁 {category.replace('_', ' ').title()} ({len(files)} files):")
            for file in sorted(files):
                # Mark potential duplicates
                if "performace" in file:
                    print(f"   ⚠️ {file} (TYPO)")
                elif file.count("_") > 2:
                    print(f"   🔄 {file} (Complex)")
                else:
                    print(f"   📄 {file}")
            print()

    # Identify potential issues
    print("🚨 POTENTIAL ISSUES IDENTIFIED:")

    # Check for typos
    typo_files = [f for f in sum(file_categories.values(), []) if "performace" in f]
    if typo_files:
        print(f"   📝 Typo files: {len(typo_files)} files with 'performace' instead of 'performance'")

    # Check for too many launchers
    launcher_count = len(file_categories["launchers"])
    if launcher_count > 2:
        print(f"   🚀 Too many launchers: {launcher_count} launcher files (recommend 1-2)")

    # Check for similar named files
    gui_files = file_categories["gui_interfaces"]
    if len(gui_files) > 3:
        print(f"   🖥️ Many GUI files: {len(gui_files)} GUI files (may have duplicates)")

    integration_files = file_categories["integrations"]
    if len(integration_files) > 5:
        print(f"   🔗 Many integrations: {len(integration_files)} integration files")

    print("\n💡 RECOMMENDATIONS:")
    print("   1. Run quick_typo_cleanup() to fix obvious typos")
    print("   2. Consolidate launcher files into one unified launcher")
    print("   3. Review GUI files for duplicates")
    print("   4. Test core functionality before major changes")

    return file_categories


def main():
    """Main cleanup interface"""
    print("🧹 DFS OPTIMIZER SAFE FILE CLEANUP")
    print("=" * 40)
    print("Choose cleanup option:")
    print("1. 🚀 Quick typo cleanup (safest)")
    print("2. 🔍 Full interactive cleanup")
    print("3. 📊 Project structure analysis")
    print("4. 🔄 Restore from backup")
    print("5. ❌ Exit")

    while True:
        choice = input("\nEnter choice (1-5): ").strip()

        if choice == '1':
            quick_typo_cleanup()
            break
        elif choice == '2':
            cleanup = SafeFileCleanup()
            cleanup.interactive_cleanup()
            break
        elif choice == '3':
            create_project_analysis()
            break
        elif choice == '4':
            cleanup = SafeFileCleanup()
            cleanup.restore_from_backup()
            break
        elif choice == '5':
            print("👋 Exiting cleanup utility")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cleanup cancelled by user")
    except Exception as e:
        print(f"\n❌ Cleanup error: {e}")
        import traceback

        traceback.print_exc()