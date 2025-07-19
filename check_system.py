#!/usr/bin/env python3
"""
COMPREHENSIVE DFS SYSTEM CHECKER
================================
Complete diagnostic tool for the DFS Optimizer system
"""

import os
import sys
import ast
import importlib
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class SystemChecker:
    """Comprehensive system checker for DFS Optimizer"""

    def __init__(self):
        self.results = {
            'syntax_errors': [],
            'import_errors': [],
            'missing_files': [],
            'module_status': {},
            'dependency_status': {},
            'warnings': [],
            'core_functionality': {}
        }

    def check_syntax(self, filepath: str) -> List[Dict]:
        """Check Python file for syntax errors"""
        errors = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Try to compile the code
            try:
                compile(content, filepath, 'exec')
            except SyntaxError as e:
                errors.append({
                    'file': filepath,
                    'line': e.lineno,
                    'column': e.offset,
                    'message': e.msg,
                    'text': e.text.strip() if e.text else ''
                })

            # Parse with AST for additional checks
            try:
                tree = ast.parse(content)
                # Could add more AST-based checks here
            except Exception as e:
                if not errors:  # Only add if we haven't already caught it
                    errors.append({
                        'file': filepath,
                        'line': 0,
                        'message': f'AST parse error: {str(e)}',
                        'text': ''
                    })

        except Exception as e:
            errors.append({
                'file': filepath,
                'line': 0,
                'message': f'Error reading file: {str(e)}',
                'text': ''
            })

        return errors

    def check_imports(self, filepath: str) -> List[Dict]:
        """Check for import issues"""
        import_errors = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        try:
                            importlib.import_module(alias.name)
                        except ImportError as e:
                            import_errors.append({
                                'file': filepath,
                                'line': node.lineno,
                                'module': alias.name,
                                'error': str(e)
                            })

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        try:
                            importlib.import_module(node.module)
                        except ImportError as e:
                            import_errors.append({
                                'file': filepath,
                                'line': node.lineno,
                                'module': node.module,
                                'error': str(e)
                            })

        except SyntaxError:
            # Skip import checking if syntax errors exist
            pass
        except Exception as e:
            import_errors.append({
                'file': filepath,
                'line': 0,
                'module': 'unknown',
                'error': f'Error checking imports: {str(e)}'
            })

        return import_errors

    def check_core_files(self) -> Dict[str, bool]:
        """Check if all core files exist"""
        core_files = [
            'bulletproof_dfs_core.py',
            'unified_player_model.py',
            'unified_milp_optimizer.py',
            'enhanced_dfs_gui.py',
            'simple_statcast_fetcher.py',
            'vegas_lines.py',
            'smart_confirmation_system.py',
            'unified_scoring_engine.py',
            'data_validator.py',
            'performance_optimizer.py'
        ]

        file_status = {}
        for file in core_files:
            file_status[file] = os.path.exists(file)
            if not file_status[file]:
                self.results['missing_files'].append(file)

        return file_status

    def check_dependencies(self) -> Dict[str, bool]:
        """Check if required packages are installed"""
        dependencies = {
            'pandas': 'Data manipulation',
            'numpy': 'Numerical operations',
            'pulp': 'MILP optimization',
            'PyQt5': 'GUI interface',
            'requests': 'API calls',
            'beautifulsoup4': 'Web scraping',
            'lxml': 'XML parsing'
        }

        status = {}
        for package, description in dependencies.items():
            try:
                __import__(package)
                status[package] = True
            except ImportError:
                status[package] = False
                self.results['warnings'].append(f"Missing {package}: {description}")

        return status

    def test_module_loading(self):
        """Test loading each module"""
        modules_to_test = [
            ('unified_player_model', 'UnifiedPlayer'),
            ('unified_milp_optimizer', 'UnifiedMILPOptimizer'),
            ('bulletproof_dfs_core', 'BulletproofDFSCore'),
            ('unified_scoring_engine', 'get_scoring_engine'),
            ('data_validator', 'get_validator'),
            ('performance_optimizer', 'get_performance_optimizer'),
        ]

        for module_name, class_name in modules_to_test:
            try:
                # Remove from sys.modules to force fresh import
                if module_name in sys.modules:
                    del sys.modules[module_name]

                module = __import__(module_name)

                # Check if class/function exists
                if hasattr(module, class_name):
                    self.results['module_status'][module_name] = 'OK'
                else:
                    self.results['module_status'][module_name] = f'Missing {class_name}'

            except SyntaxError as e:
                self.results['module_status'][module_name] = f'Syntax Error: Line {e.lineno}'
                self.results['syntax_errors'].append({
                    'file': f'{module_name}.py',
                    'line': e.lineno,
                    'message': e.msg
                })
            except ImportError as e:
                self.results['module_status'][module_name] = f'Import Error: {str(e)}'
            except Exception as e:
                self.results['module_status'][module_name] = f'Error: {str(e)}'

    def test_core_initialization(self):
        """Test initializing the core system"""
        try:
            # Clear any cached imports
            if 'bulletproof_dfs_core' in sys.modules:
                del sys.modules['bulletproof_dfs_core']

            from bulletproof_dfs_core import BulletproofDFSCore

            # Try to create instance
            core = BulletproofDFSCore(mode="test")
            self.results['core_functionality']['initialization'] = 'OK'

            # Check module availability
            if hasattr(core, 'modules_status'):
                for module, status in core.modules_status.items():
                    self.results['core_functionality'][f'module_{module}'] = 'Available' if status else 'Not Available'

        except Exception as e:
            self.results['core_functionality']['initialization'] = f'Failed: {str(e)}'
            # Get more detailed traceback
            self.results['warnings'].append(f"Core initialization traceback:\n{traceback.format_exc()}")

    def generate_report(self):
        """Generate comprehensive report"""
        print("\n🔍 COMPREHENSIVE DFS SYSTEM CHECK")
        print("=" * 60)

        # 1. File Structure
        print("\n📁 FILE STRUCTURE:")
        file_status = self.check_core_files()
        for file, exists in file_status.items():
            status = "✅" if exists else "❌"
            print(f"  {status} {file}")

        # 2. Dependencies
        print("\n📦 DEPENDENCIES:")
        dep_status = self.check_dependencies()
        self.results['dependency_status'] = dep_status
        for package, installed in dep_status.items():
            status = "✅" if installed else "❌"
            print(f"  {status} {package}")

        # 3. Syntax Errors
        print("\n🔧 SYNTAX CHECK:")
        for file in file_status:
            if file_status[file]:
                errors = self.check_syntax(file)
                if errors:
                    self.results['syntax_errors'].extend(errors)

        if self.results['syntax_errors']:
            print(f"  ❌ Found {len(self.results['syntax_errors'])} syntax errors:")
            for error in self.results['syntax_errors'][:5]:  # Show first 5
                print(f"     {error['file']}:{error['line']} - {error['message']}")
                if error.get('text'):
                    print(f"       > {error['text']}")
        else:
            print("  ✅ No syntax errors found")

        # 4. Import Errors
        print("\n📥 IMPORT CHECK:")
        for file in file_status:
            if file_status[file] and not any(e['file'] == file for e in self.results['syntax_errors']):
                import_errors = self.check_imports(file)
                if import_errors:
                    self.results['import_errors'].extend(import_errors)

        if self.results['import_errors']:
            print(f"  ❌ Found {len(self.results['import_errors'])} import errors:")
            for error in self.results['import_errors'][:5]:
                print(f"     {error['file']}:{error['line']} - Cannot import '{error['module']}'")
        else:
            print("  ✅ All imports resolved")

        # 5. Module Loading
        print("\n🔌 MODULE LOADING:")
        self.test_module_loading()
        for module, status in self.results['module_status'].items():
            if status == 'OK':
                print(f"  ✅ {module}")
            else:
                print(f"  ❌ {module}: {status}")

        # 6. Core System Test
        print("\n🚀 CORE SYSTEM TEST:")
        self.test_core_initialization()
        for test, result in self.results['core_functionality'].items():
            if result == 'OK' or 'Available' in result:
                print(f"  ✅ {test}: {result}")
            else:
                print(f"  ❌ {test}: {result}")

        # 7. Warnings and Recommendations
        if self.results['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in self.results['warnings']:
                print(f"  • {warning}")

        # 8. Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if self.results['syntax_errors']:
            print("  1. Run fix_syntax_errors.py to fix syntax issues")
        if self.results['missing_files']:
            print("  2. Ensure all required files are in the project directory")
        if any(not installed for installed in dep_status.values()):
            print("  3. Install missing dependencies: pip install -r requirements.txt")
        if self.results['import_errors']:
            print("  4. Check import statements and module names")

        # 9. Summary
        print("\n📊 SUMMARY:")
        total_issues = (len(self.results['syntax_errors']) +
                        len(self.results['import_errors']) +
                        len(self.results['missing_files']))

        if total_issues == 0:
            print("  ✅ System is healthy!")
        else:
            print(f"  ❌ Found {total_issues} total issues")
            print(f"     - Syntax errors: {len(self.results['syntax_errors'])}")
            print(f"     - Import errors: {len(self.results['import_errors'])}")
            print(f"     - Missing files: {len(self.results['missing_files'])}")

        return total_issues == 0


def main():
    """Run comprehensive system check"""
    checker = SystemChecker()
    is_healthy = checker.generate_report()

    print("\n" + "=" * 60)
    if is_healthy:
        print("✅ Your DFS Optimizer is ready to use!")
        print("\nRun: python enhanced_dfs_gui.py")
    else:
        print("❌ Please fix the issues above before running the optimizer")
        print("\nQuick fixes:")
        print("1. Run: python fix_syntax_errors.py")
        print("2. Install missing packages: pip install pandas numpy pulp PyQt5")
        print("3. Check that all files are in the correct directory")

    # Save detailed report
    report_file = f"system_check_report_{Path.cwd().name}.txt"
    with open(report_file, 'w') as f:
        f.write("DFS OPTIMIZER SYSTEM CHECK REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Directory: {Path.cwd()}\n")
        f.write(f"Python Version: {sys.version}\n")
        f.write("=" * 60 + "\n\n")

        # Write detailed results
        import json
        f.write(json.dumps(checker.results, indent=2))

    print(f"\n📄 Detailed report saved to: {report_file}")


if __name__ == "__main__":
    main()