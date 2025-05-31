#!/usr/bin/env python3
"""
Automated DFS Integration Script
Safely integrates your proven algorithms with the streamlined system
Handles file migration and cleanup step-by-step
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime


class DFSIntegrationManager:
    """Manages the safe integration of your DFS optimizer files"""

    def __init__(self):
        self.project_root = Path(".")
        self.backup_dir = Path("backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))

        # Your actual files from the screenshots
        self.existing_files = {
            # Core files to preserve
            'keep': [
                'dfs_data_enhanced.py',
                'dfs_optimizer_enhanced.py',
                'dfs_runner_enhanced.py',
                'enhanced_dfs_gui.py',
                'vegas_lines.py',
                'statcast_integration.py'
            ],
            # Files with typos - safe to delete
            'typo_duplicates': [
                'performace_integrated_data.py',  # Typo in "performance"
                'performace_integrated_gui.py'  # Typo in "performance"
            ],
            # Multiple launchers - consolidate
            'redundant_launchers': [
                'launch.py',
                'dfs_optimizer_launcher.py',
                'main_enhanced_performance.py'
            ],
            # Integration files to merge
            'integration_files': [
                'async_data_manager.py',
                'performance_integrated_data.py',
                'performance_integrated_gui.py'
            ]
        }

        print("🚀 DFS Integration Manager initialized")
        print(f"📁 Project root: {self.project_root.absolute()}")

    def create_backup(self):
        """Create backup of all existing files"""
        print(f"\n📦 Creating backup in {self.backup_dir}")

        try:
            self.backup_dir.mkdir(exist_ok=True)

            # Backup all Python files
            for py_file in self.project_root.glob("*.py"):
                if py_file.is_file():
                    shutil.copy2(py_file, self.backup_dir / py_file.name)
                    print(f"  ✅ Backed up: {py_file.name}")

            # Backup JSON files
            for json_file in self.project_root.glob("*.json"):
                if json_file.is_file():
                    shutil.copy2(json_file, self.backup_dir / json_file.name)
                    print(f"  ✅ Backed up: {json_file.name}")

            print(f"✅ Backup completed: {len(list(self.backup_dir.glob('*')))} files backed up")
            return True

        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False

    def extract_proven_milp_algorithm(self):
        """Extract your proven MILP algorithm from dfs_optimizer_enhanced.py"""
        print("\n🧠 Extracting proven MILP algorithm...")

        source_file = self.project_root / "dfs_optimizer_enhanced.py"

        if not source_file.exists():
            print("❌ dfs_optimizer_enhanced.py not found")
            return False

        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for MILP optimization function
            if "optimize_lineup_milp" in content:
                print("✅ Found optimize_lineup_milp function")

                # Extract the function (simplified - you can enhance this)
                milp_code = self._extract_function(content, "optimize_lineup_milp")
                if milp_code:
                    self._save_extracted_code("extracted_milp.py", milp_code)
                    print("✅ MILP algorithm extracted to extracted_milp.py")
                    return True

            print("⚠️ optimize_lineup_milp function not found")
            return False

        except Exception as e:
            print(f"❌ Error extracting MILP: {e}")
            return False

    def extract_fixed_name_matcher(self):
        """Extract the fixed name matcher from dfs_runner_enhanced.py"""
        print("\n🎯 Extracting fixed DFF name matcher...")

        source_file = self.project_root / "dfs_runner_enhanced.py"

        if not source_file.exists():
            print("❌ dfs_runner_enhanced.py not found")
            return False

        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for the fixed name matching classes
            if "FixedNameMatcher" in content or "FixedDFFNameMatcher" in content:
                print("✅ Found fixed name matcher")

                # Extract the class
                matcher_code = self._extract_class(content, "FixedDFFNameMatcher")
                if matcher_code:
                    self._save_extracted_code("extracted_name_matcher.py", matcher_code)
                    print("✅ Name matcher extracted to extracted_name_matcher.py")
                    return True

            print("⚠️ Fixed name matcher not found")
            return False

        except Exception as e:
            print(f"❌ Error extracting name matcher: {e}")
            return False

    def safe_delete_typo_files(self):
        """Safely delete files with typos (obviously duplicates)"""
        print("\n🗑️ Safely deleting typo duplicate files...")

        deleted_count = 0
        for filename in self.existing_files['typo_duplicates']:
            file_path = self.project_root / filename

            if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"  ✅ Deleted: {filename} (typo duplicate)")
                    deleted_count += 1
                except Exception as e:
                    print(f"  ❌ Failed to delete {filename}: {e}")
            else:
                print(f"  ⚪ Not found: {filename}")

        print(f"✅ Deleted {deleted_count} typo duplicate files")
        return deleted_count > 0

    def consolidate_launchers(self):
        """Consolidate multiple launcher files into one"""
        print("\n🔗 Consolidating launcher files...")

        # Create unified launcher
        unified_launcher = '''#!/usr/bin/env python3
"""
Unified DFS Optimizer Launcher
Consolidated from multiple launcher files
"""

import sys
import os

def main():
    """Main launcher entry point"""
    print("🚀 DFS Optimizer Launcher")

    # Try to launch the streamlined GUI first
    try:
        from streamlined_dfs_gui import main as gui_main
        print("✅ Launching Streamlined DFS GUI...")
        return gui_main()
    except ImportError:
        print("⚠️ Streamlined GUI not available")

    # Fallback to enhanced GUI
    try:
        from enhanced_dfs_gui import main as enhanced_main
        print("✅ Launching Enhanced DFS GUI...")
        return enhanced_main()
    except ImportError:
        print("❌ No GUI available")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''

        try:
            with open("unified_launcher.py", 'w') as f:
                f.write(unified_launcher)
            print("✅ Created unified_launcher.py")

            # Mark redundant launchers for deletion (but don't delete yet)
            redundant_found = []
            for launcher in self.existing_files['redundant_launchers']:
                if (self.project_root / launcher).exists():
                    redundant_found.append(launcher)

            if redundant_found:
                print(f"📋 Found {len(redundant_found)} redundant launchers to remove later:")
                for launcher in redundant_found:
                    print(f"  - {launcher}")

            return True

        except Exception as e:
            print(f"❌ Error consolidating launchers: {e}")
            return False

    def create_streamlined_files(self):
        """Create the streamlined core files if they don't exist"""
        print("\n✨ Creating streamlined core files...")

        files_created = []

        # Check if streamlined files already exist
        streamlined_files = [
            'streamlined_dfs_core.py',
            'streamlined_dfs_gui.py',
            'test_with_sample_data.py'
        ]

        for filename in streamlined_files:
            if not (self.project_root / filename).exists():
                print(f"  📝 {filename} needs to be created")
                files_created.append(filename)
            else:
                print(f"  ✅ {filename} already exists")

        if files_created:
            print(f"💡 Please save the streamlined files from Claude's artifacts:")
            for filename in files_created:
                print(f"  - {filename}")

        return len(files_created) == 0

    def analyze_file_dependencies(self):
        """Analyze which files depend on which others"""
        print("\n🔍 Analyzing file dependencies...")

        dependencies = {}

        for py_file in self.project_root.glob("*.py"):
            if py_file.is_file():
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    imports = []
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('from ') and '.py' not in line:
                            # Extract module name
                            try:
                                module = line.split('from ')[1].split(' import')[0].strip()
                                if not module.startswith('.') and module not in ['sys', 'os', 'json', 'pandas']:
                                    imports.append(module)
                            except:
                                pass
                        elif line.startswith('import ') and '.' not in line:
                            try:
                                module = line.split('import ')[1].split(' ')[0].strip()
                                if module not in ['sys', 'os', 'json', 'pandas']:
                                    imports.append(module)
                            except:
                                pass

                    if imports:
                        dependencies[py_file.name] = imports

                except Exception as e:
                    print(f"  ⚠️ Error analyzing {py_file.name}: {e}")

        print("📊 File Dependencies Found:")
        for file, deps in dependencies.items():
            if deps:
                print(f"  {file} → {', '.join(deps)}")

        return dependencies

    def generate_integration_plan(self):
        """Generate a step-by-step integration plan"""
        print("\n📋 INTEGRATION PLAN")
        print("=" * 50)

        plan = {
            "phase_1": {
                "name": "🔒 Safety & Backup",
                "steps": [
                    "✅ Create backup of all files",
                    "✅ Analyze file dependencies",
                    "✅ Test existing system"
                ]
            },
            "phase_2": {
                "name": "🧠 Extract Proven Code",
                "steps": [
                    "🔄 Extract MILP optimization from dfs_optimizer_enhanced.py",
                    "🔄 Extract name matching from dfs_runner_enhanced.py",
                    "🔄 Extract Vegas integration from vegas_lines.py",
                    "🔄 Extract Statcast integration from statcast_integration.py"
                ]
            },
            "phase_3": {
                "name": "🗑️ Safe Cleanup",
                "steps": [
                    "🔄 Delete typo duplicate files (performace_*)",
                    "🔄 Consolidate redundant launchers",
                    "🔄 Mark integration files for merger"
                ]
            },
            "phase_4": {
                "name": "🔗 Integration",
                "steps": [
                    "🔄 Create streamlined core system",
                    "🔄 Integrate extracted algorithms",
                    "🔄 Test with sample data",
                    "🔄 Validate functionality"
                ]
            }
        }

        for phase_key, phase in plan.items():
            print(f"\n{phase['name']}:")
            for step in phase['steps']:
                print(f"  {step}")

        return plan

    def _extract_function(self, content: str, function_name: str) -> str:
        """Extract a function from Python code"""
        lines = content.split('\n')
        function_lines = []
        in_function = False
        indent_level = 0

        for line in lines:
            if f"def {function_name}" in line:
                in_function = True
                indent_level = len(line) - len(line.lstrip())
                function_lines.append(line)
            elif in_function:
                current_indent = len(line) - len(line.lstrip())
                if line.strip() and current_indent <= indent_level and not line.startswith(' ' * (indent_level + 1)):
                    break
                function_lines.append(line)

        return '\n'.join(function_lines) if function_lines else ""

    def _extract_class(self, content: str, class_name: str) -> str:
        """Extract a class from Python code"""
        lines = content.split('\n')
        class_lines = []
        in_class = False
        indent_level = 0

        for line in lines:
            if f"class {class_name}" in line:
                in_class = True
                indent_level = len(line) - len(line.lstrip())
                class_lines.append(line)
            elif in_class:
                current_indent = len(line) - len(line.lstrip())
                if line.strip() and current_indent <= indent_level and line[0] not in [' ', '\t']:
                    break
                class_lines.append(line)

        return '\n'.join(class_lines) if class_lines else ""

    def _save_extracted_code(self, filename: str, code: str):
        """Save extracted code to a file"""
        try:
            with open(filename, 'w') as f:
                f.write(f'#!/usr/bin/env python3\n')
                f.write(f'"""\nExtracted from existing DFS optimizer\n"""\n\n')
                f.write(code)
            print(f"✅ Saved extracted code to {filename}")
        except Exception as e:
            print(f"❌ Failed to save {filename}: {e}")


def run_integration_wizard():
    """Interactive integration wizard"""
    print("🧙‍♂️ DFS INTEGRATION WIZARD")
    print("=" * 40)
    print("This wizard will safely integrate your DFS optimizer files.")
    print("Each step will ask for confirmation before making changes.\n")

    integration_manager = DFSIntegrationManager()

    # Step 1: Create backup
    print("STEP 1: Creating Backup")
    if input("Create backup of all files? (y/n): ").lower() == 'y':
        if integration_manager.create_backup():
            print("✅ Backup created successfully!")
        else:
            print("❌ Backup failed. Stopping for safety.")
            return False

    # Step 2: Analyze dependencies
    print("\nSTEP 2: Analyzing Dependencies")
    if input("Analyze file dependencies? (y/n): ").lower() == 'y':
        integration_manager.analyze_file_dependencies()

    # Step 3: Extract proven algorithms
    print("\nSTEP 3: Extract Proven Algorithms")
    if input("Extract MILP optimization algorithm? (y/n): ").lower() == 'y':
        integration_manager.extract_proven_milp_algorithm()

    if input("Extract fixed name matcher? (y/n): ").lower() == 'y':
        integration_manager.extract_fixed_name_matcher()

    # Step 4: Safe cleanup
    print("\nSTEP 4: Safe Cleanup")
    if input("Delete typo duplicate files (safe)? (y/n): ").lower() == 'y':
        integration_manager.safe_delete_typo_files()

    if input("Consolidate launcher files? (y/n): ").lower() == 'y':
        integration_manager.consolidate_launchers()

    # Step 5: Generate plan
    print("\nSTEP 5: Integration Plan")
    if input("Generate complete integration plan? (y/n): ").lower() == 'y':
        integration_manager.generate_integration_plan()

    print("\n✅ Integration wizard completed!")
    print("💡 Next: Save the streamlined files from Claude's artifacts")
    print("🚀 Then run: python test_with_sample_data.py")

    return True


if __name__ == "__main__":
    try:
        run_integration_wizard()
    except KeyboardInterrupt:
        print("\n\n👋 Integration cancelled by user")
    except Exception as e:
        print(f"\n❌ Integration wizard error: {e}")
        import traceback

        traceback.print_exc()