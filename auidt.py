#!/usr/bin/env python3
"""
DFS PROJECT AUDIT SCRIPT
========================
Shows complete project structure and identifies issues
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import hashlib


class ProjectAuditor:
    def __init__(self, project_root="."):
        self.root = Path(project_root).resolve()
        self.files_data = []
        self.duplicates = {}
        self.report = []

    def run_audit(self):
        """Run complete project audit"""
        print("🔍 DFS PROJECT AUDIT")
        print("=" * 80)
        print(f"Project Root: {self.root}")
        print(f"Audit Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Collect all files
        self._collect_files()

        # Generate reports
        self._show_directory_tree()
        self._analyze_python_files()
        self._find_duplicates()
        self._check_required_files()
        self._show_recommendations()

        # Save report
        self._save_report()

    def _collect_files(self):
        """Collect all files in project"""
        for path in self.root.rglob("*"):
            if path.is_file():
                # Skip hidden files and common excludes
                if any(part.startswith('.') for part in path.parts):
                    continue
                if any(skip in str(path) for skip in ['__pycache__', '.pyc', '.git', 'venv', '.venv']):
                    continue

                rel_path = path.relative_to(self.root)
                size = path.stat().st_size
                modified = datetime.fromtimestamp(path.stat().st_mtime)

                file_info = {
                    'path': str(rel_path),
                    'name': path.name,
                    'size': size,
                    'modified': modified,
                    'extension': path.suffix
                }

                # Get file hash for duplicate detection
                if size < 1024 * 1024:  # Only hash files < 1MB
                    try:
                        with open(path, 'rb') as f:
                            file_info['hash'] = hashlib.md5(f.read()).hexdigest()
                    except:
                        file_info['hash'] = None

                self.files_data.append(file_info)

    def _show_directory_tree(self):
        """Show directory structure"""
        print("\n📁 DIRECTORY STRUCTURE")
        print("-" * 80)

        # Use tree command if available
        if os.system("which tree > /dev/null 2>&1") == 0:
            os.system(f"tree -I '__pycache__|*.pyc|.git|venv|.venv' {self.root} -L 3")
        else:
            # Fallback to manual tree
            self._print_tree(self.root, prefix="", max_depth=3)

    def _print_tree(self, path, prefix="", current_depth=0, max_depth=3):
        """Manual directory tree printer"""
        if current_depth > max_depth:
            return

        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))

        for i, item in enumerate(items):
            if item.name.startswith('.') or item.name == '__pycache__':
                continue

            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item.name}")

            if item.is_dir() and current_depth < max_depth:
                next_prefix = prefix + ("    " if is_last else "│   ")
                self._print_tree(item, next_prefix, current_depth + 1, max_depth)

    def _analyze_python_files(self):
        """Analyze Python files"""
        print("\n🐍 PYTHON FILES ANALYSIS")
        print("-" * 80)

        py_files = [f for f in self.files_data if f['extension'] == '.py']
        py_files.sort(key=lambda x: x['size'], reverse=True)

        print(f"Total Python files: {len(py_files)}")
        print(f"\nLargest Python files:")
        print(f"{'File':<50} {'Size':>10} {'Modified':<20}")
        print("-" * 80)

        for f in py_files[:20]:
            size_kb = f['size'] / 1024
            modified = f['modified'].strftime('%Y-%m-%d %H:%M')
            print(f"{f['path']:<50} {size_kb:>9.1f}K {modified:<20}")

        # Group by directory
        print("\n📊 Files by Directory:")
        by_dir = {}
        for f in py_files:
            dir_name = os.path.dirname(f['path']) or 'root'
            if dir_name not in by_dir:
                by_dir[dir_name] = []
            by_dir[dir_name].append(f['name'])

        for dir_name, files in sorted(by_dir.items()):
            print(f"\n{dir_name}/ ({len(files)} files)")
            for fname in sorted(files)[:10]:
                print(f"  - {fname}")
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more")

    def _find_duplicates(self):
        """Find duplicate files"""
        print("\n🔍 DUPLICATE FILES CHECK")
        print("-" * 80)

        # Group by hash
        by_hash = {}
        for f in self.files_data:
            if f.get('hash'):
                if f['hash'] not in by_hash:
                    by_hash[f['hash']] = []
                by_hash[f['hash']].append(f)

        # Find duplicates
        duplicates = {h: files for h, files in by_hash.items() if len(files) > 1}

        if duplicates:
            print(f"Found {len(duplicates)} sets of duplicate files:")
            for hash_val, files in list(duplicates.items())[:10]:
                print(f"\nDuplicate set (size: {files[0]['size']} bytes):")
                for f in files:
                    print(f"  - {f['path']}")
        else:
            print("✅ No duplicate files found")

    def _check_required_files(self):
        """Check for required files"""
        print("\n✅ REQUIRED FILES CHECK")
        print("-" * 80)

        # New system files
        required_new = [
            'advanced_dfs_core.py',
            'advanced_scoring_engine.py',
            'pure_data_pipeline.py',
            'automated_stacking_system.py',
            'milp_with_stacking.py',
            'unified_milp_optimizer.py',
            'unified_player_model.py',
            'unified_data_system.py',
            'unified_config_manager.py',
            'smart_confirmation_system.py',
            'vegas_lines.py',
            'data_validator.py',
            'performance_optimizer.py'
        ]

        # Check which exist
        existing_files = [f['name'] for f in self.files_data]

        print("Core System Files:")
        for req_file in required_new:
            exists = req_file in existing_files
            status = "✅" if exists else "❌"
            print(f"  {status} {req_file}")

        # Files that should be deleted
        print("\n🗑️  FILES TO DELETE:")
        delete_patterns = [
            'backup_',
            'test.py',
            'bug.py',
            'test_',
            '_old',
            '_backup',
            'PURE SHOWDOWN',
            'clean_optimizer_integration',
            'quick_fix',
            'direct_test',
            'gui_fixed',
            'verify_sources',
            'test_dff_load',
            'launch_optimizer.py',
            'run_tools.py',
            'batting_order_correlation_system.py',  # Integrated into stacking
            'rotowire_confirmation_system.py',  # Redundant
            'real_recent_form.py'  # Integrated into pipeline
        ]

        files_to_delete = []
        for f in self.files_data:
            if any(pattern in f['name'] for pattern in delete_patterns):
                files_to_delete.append(f['path'])

        if files_to_delete:
            for f in files_to_delete[:20]:
                print(f"  - {f}")
            if len(files_to_delete) > 20:
                print(f"  ... and {len(files_to_delete) - 20} more")
        else:
            print("  None found")

    def _show_recommendations(self):
        """Show recommendations"""
        print("\n💡 RECOMMENDATIONS")
        print("-" * 80)

        recommendations = []

        # Check for old vs new files
        old_files = ['bulletproof_dfs_core.py', 'simple_statcast_fetcher.py']
        new_files = ['advanced_dfs_core.py', 'complete_statcast_fetcher.py']

        existing = [f['name'] for f in self.files_data]

        for old, new in zip(old_files, new_files):
            if old in existing and new in existing:
                recommendations.append(f"Replace {old} with {new}")
            elif old in existing and new not in existing:
                recommendations.append(f"Missing {new} - using old {old}")

        # Check for test files
        test_files = [f for f in self.files_data if 'test' in f['name'].lower()]
        if len(test_files) > 5:
            recommendations.append(f"Clean up {len(test_files)} test files")

        # Check for backups
        backup_files = [f for f in self.files_data if 'backup' in f['name'].lower()]
        if backup_files:
            recommendations.append(f"Remove {len(backup_files)} backup files")

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print("✅ Project structure looks good!")

    def _save_report(self):
        """Save detailed report"""
        report_file = f"project_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(report_file, 'w') as f:
            f.write("DFS PROJECT AUDIT REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Project: {self.root}\n")
            f.write("=" * 80 + "\n\n")

            # All Python files
            f.write("PYTHON FILES:\n")
            py_files = sorted([f for f in self.files_data if f['extension'] == '.py'])
            for pf in py_files:
                f.write(f"  {pf['path']:<60} {pf['size']:>8} bytes\n")

            # All CSV files
            f.write("\n\nCSV FILES:\n")
            csv_files = sorted([f for f in self.files_data if f['extension'] == '.csv'])
            for cf in csv_files:
                f.write(f"  {cf['path']:<60} {cf['size']:>8} bytes\n")

        print(f"\n📄 Detailed report saved to: {report_file}")


def main():
    """Run the audit"""
    print("Starting DFS Project Audit...\n")

    # Get project root (current directory or specified)
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."

    auditor = ProjectAuditor(project_root)
    auditor.run_audit()

    print("\n✅ Audit complete!")


if __name__ == "__main__":
    main()