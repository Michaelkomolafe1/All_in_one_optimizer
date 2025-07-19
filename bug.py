#!/usr/bin/env python3
"""
FIX GUI LAUNCH ISSUES
====================
Focused script to fix and launch the DFS GUI
"""

import os
import sys
import subprocess
import traceback


def diagnose_gui_issue():
    """Diagnose why the GUI isn't launching"""
    print("🔍 DIAGNOSING GUI ISSUES")
    print("=" * 60)

    issues = []

    # 1. Check display
    print("\n1️⃣ Display Check:")
    if sys.platform == 'linux':
        display = os.environ.get('DISPLAY', 'Not set')
        print(f"   DISPLAY = {display}")

        if display == 'Not set':
            os.environ['DISPLAY'] = ':0'
            print("   ✅ Set DISPLAY=:0")
    else:
        print("   ✅ Not Linux, display not required")

    # 2. Test PyQt5
    print("\n2️⃣ PyQt5 Test:")
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QT_VERSION_STR
        print(f"   ✅ PyQt5 working (Qt {QT_VERSION_STR})")
    except ImportError as e:
        print(f"   ❌ PyQt5 import failed: {e}")
        issues.append("PyQt5 not installed")
        return issues

    # 3. Test creating QApplication
    print("\n3️⃣ QApplication Test:")
    try:
        test_app = QApplication.instance()
        if test_app is None:
            test_app = QApplication([])
        print("   ✅ Can create QApplication")
    except Exception as e:
        print(f"   ❌ Cannot create QApplication: {e}")
        issues.append(f"QApplication error: {e}")

    # 4. Check GUI file
    print("\n4️⃣ GUI File Check:")
    if not os.path.exists('enhanced_dfs_gui.py'):
        print("   ❌ enhanced_dfs_gui.py not found!")
        issues.append("GUI file missing")
        return issues

    print("   ✅ GUI file exists")

    # 5. Try importing GUI components
    print("\n5️⃣ Import Test:")
    sys.path.insert(0, os.getcwd())

    try:
        # First check what's failing
        print("   Testing imports...")

        # Test if we can import basic stuff
        from enhanced_dfs_gui import FileLoadPanel, OptimizationPanel, ResultsPanel
        print("   ✅ GUI components import OK")

        # Now try the main GUI
        from enhanced_dfs_gui import EnhancedDFSGUI
        print("   ✅ Main GUI class imports OK")

        # Try the main function
        from enhanced_dfs_gui import main
        print("   ✅ main() function found")

    except ImportError as e:
        print(f"   ❌ Import error: {e}")

        # Check if it's the core system
        if "AdvancedDFSCore" in str(e) or "bulletproof_dfs_core" in str(e):
            print("\n   ℹ️  The issue is with importing the core system")
            issues.append("Core system import error")

            # Try to fix by modifying the import
            fix_core_import()
        else:
            issues.append(f"Import error: {e}")

    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        traceback.print_exc()
        issues.append(f"Unexpected error: {e}")

    return issues


def fix_core_import():
    """Fix the core import issue in GUI"""
    print("\n🔧 Fixing core import in GUI...")

    # Read the GUI file
    with open('enhanced_dfs_gui.py', 'r') as f:
        content = f.read()

    # Check what core it's trying to import
    if 'from advanced_dfs_core import AdvancedDFSCore' in content:
        print("   ℹ️  GUI is trying to use AdvancedDFSCore")

        # Replace with bulletproof core
        content = content.replace(
            'from advanced_dfs_core import AdvancedDFSCore',
            'from bulletproof_dfs_core import BulletproofDFSCore as AdvancedDFSCore'
        )

        # Save the fixed file
        with open('enhanced_dfs_gui.py', 'w') as f:
            f.write(content)

        print("   ✅ Fixed import to use BulletproofDFSCore")

    elif 'AdvancedDFSCore' in content and 'import AdvancedDFSCore' not in content:
        print("   ℹ️  GUI references AdvancedDFSCore but doesn't import it")

        # Add the import
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'from bulletproof_dfs_core import' in line:
                lines[i] = 'from bulletproof_dfs_core import BulletproofDFSCore, BulletproofDFSCore as AdvancedDFSCore'
                break

        with open('enhanced_dfs_gui.py', 'w') as f:
            f.write('\n'.join(lines))

        print("   ✅ Added AdvancedDFSCore alias")


def create_working_launcher():
    """Create a launcher that definitely works"""

    launcher = '''#!/usr/bin/env python3
"""
DFS GUI LAUNCHER
================
Simple launcher that handles common issues
"""

import os
import sys

# Set up environment
if sys.platform == 'linux' and 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'

# Ensure we can import from current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        # Import PyQt5
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt

        # Create app
        app = QApplication(sys.argv)
        app.setApplicationName("DFS Optimizer")

        # Try to import and run the GUI
        try:
            from enhanced_dfs_gui import EnhancedDFSGUI

            # Create and show window
            window = EnhancedDFSGUI()
            window.show()

            print("✅ GUI launched successfully!")
            sys.exit(app.exec_())

        except ImportError as e:
            print(f"❌ Import error: {e}")

            # Show error window
            from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QTextEdit, QPushButton

            class ErrorWindow(QMainWindow):
                def __init__(self, error_msg):
                    super().__init__()
                    self.setWindowTitle("DFS Optimizer - Launch Error")
                    self.setGeometry(100, 100, 600, 400)

                    central = QWidget()
                    self.setCentralWidget(central)
                    layout = QVBoxLayout(central)

                    # Error message
                    label = QLabel("Failed to launch DFS Optimizer:")
                    label.setStyleSheet("font-weight: bold; color: red;")
                    layout.addWidget(label)

                    # Error details
                    error_text = QTextEdit()
                    error_text.setReadOnly(True)
                    error_text.setPlainText(str(error_msg))
                    layout.addWidget(error_text)

                    # Instructions
                    instructions = QLabel(
                        "To fix:\\n"
                        "1. Run: python fix_gui_only.py\\n"
                        "2. Check that all files are present\\n"
                        "3. Install requirements: pip install -r requirements.txt"
                    )
                    layout.addWidget(instructions)

                    # Close button
                    close_btn = QPushButton("Close")
                    close_btn.clicked.connect(self.close)
                    layout.addWidget(close_btn)

            error_window = ErrorWindow(e)
            error_window.show()
            sys.exit(app.exec_())

    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
'''

    with open('launch_gui.py', 'w') as f:
        f.write(launcher)

    # Make it executable
    os.chmod('launch_gui.py', 0o755)

    print("\n✅ Created launch_gui.py")


def launch_gui_directly():
    """Try to launch the GUI directly"""
    print("\n🚀 Attempting to launch GUI...")

    # Set display
    if sys.platform == 'linux' and 'DISPLAY' not in os.environ:
        os.environ['DISPLAY'] = ':0'

    # Add current directory to path
    sys.path.insert(0, os.getcwd())

    try:
        # Import and run
        from enhanced_dfs_gui import main
        print("✅ Starting GUI...")
        main()
    except Exception as e:
        print(f"❌ Failed to launch: {e}")
        traceback.print_exc()

        print("\n💡 Try running the launcher instead:")
        print("   python launch_gui.py")


def main():
    """Main function"""
    print("🔧 DFS GUI FIX")
    print("=" * 60)

    # Diagnose issues
    issues = diagnose_gui_issue()

    if issues:
        print(f"\n❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("\n✅ No issues detected!")

    # Create launcher
    print("\n📝 Creating failsafe launcher...")
    create_working_launcher()

    # Ask if user wants to try launching
    print("\n" + "=" * 60)
    response = input("\nTry to launch GUI now? (y/n): ")

    if response.lower() == 'y':
        launch_gui_directly()
    else:
        print("\n✅ Setup complete!")
        print("\nTo launch the GUI, run one of these:")
        print("   python launch_gui.py")
        print("   python enhanced_dfs_gui.py")
        print("   ./launch_gui.py")


if __name__ == "__main__":
    main()