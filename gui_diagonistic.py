#!/usr/bin/env python3
"""
DIAGNOSE GUI ISSUES
==================
Helps identify why the GUI isn't showing up
"""

import os
import sys
import subprocess


def diagnose_gui():
    """Diagnose GUI issues"""

    print("🔍 DIAGNOSING GUI ISSUES")
    print("=" * 60)

    issues_found = []

    # 1. Check Python version
    print("\n1️⃣ Python Version:")
    print(f"   {sys.version}")
    if sys.version_info < (3, 6):
        issues_found.append("Python version too old (need 3.6+)")

    # 2. Check PyQt5
    print("\n2️⃣ PyQt5 Installation:")
    try:
        import PyQt5
        print(f"   ✅ PyQt5 version: {PyQt5.Qt.PYQT_VERSION_STR}")

        from PyQt5.QtCore import QT_VERSION_STR
        print(f"   ✅ Qt version: {QT_VERSION_STR}")
    except ImportError:
        print("   ❌ PyQt5 not installed")
        issues_found.append("PyQt5 not installed")

    # 3. Check display
    print("\n3️⃣ Display Environment:")
    display = os.environ.get('DISPLAY', 'Not set')
    print(f"   DISPLAY={display}")

    if display == 'Not set':
        issues_found.append("DISPLAY environment variable not set")
        print("   ⚠️  No display variable set")

        # Check if we're in SSH
        if 'SSH_CONNECTION' in os.environ:
            print("   📡 SSH connection detected")
            issues_found.append("Running via SSH without X11 forwarding")

    # 4. Test simple PyQt5 app
    print("\n4️⃣ Testing PyQt5 Application:")
    test_code = '''
import sys
from PyQt5.QtWidgets import QApplication, QLabel

try:
    app = QApplication(sys.argv)
    print("SUCCESS: QApplication created")
except Exception as e:
    print(f"FAILED: {e}")
'''

    try:
        result = subprocess.run(
            [sys.executable, '-c', test_code],
            capture_output=True,
            text=True,
            timeout=5
        )

        if "SUCCESS" in result.stdout:
            print("   ✅ PyQt5 can create applications")
        else:
            print("   ❌ PyQt5 cannot create applications")
            print(f"   Error: {result.stderr}")
            issues_found.append("PyQt5 cannot create QApplication")

    except subprocess.TimeoutExpired:
        print("   ⚠️  Test timed out (might be waiting for display)")
        issues_found.append("GUI test timed out")

    except Exception as e:
        print(f"   ❌ Test failed: {e}")

    # 5. Check if enhanced_dfs_gui.py exists and is valid
    print("\n5️⃣ Checking enhanced_dfs_gui.py:")
    if os.path.exists('enhanced_dfs_gui.py'):
        print("   ✅ File exists")

        # Check if it has a main block
        with open('enhanced_dfs_gui.py', 'r') as f:
            content = f.read()

        if '__main__' in content:
            print("   ✅ Has main block")
        else:
            print("   ❌ Missing main block")
            issues_found.append("enhanced_dfs_gui.py missing main block")

        # Check for syntax errors
        try:
            compile(content, 'enhanced_dfs_gui.py', 'exec')
            print("   ✅ No syntax errors")
        except SyntaxError as e:
            print(f"   ❌ Syntax error: {e}")
            issues_found.append(f"Syntax error in GUI: {e}")

    else:
        print("   ❌ File not found!")
        issues_found.append("enhanced_dfs_gui.py not found")

    # 6. Try importing the GUI
    print("\n6️⃣ Testing GUI Import:")
    try:
        # First try importing bulletproof_dfs_core
        try:
            from bulletproof_dfs_core import BulletproofDFSCore
            print("   ✅ Core system imports")
        except Exception as e:
            print(f"   ❌ Core import failed: {e}")
            issues_found.append(f"Core import error: {e}")

        # Then try GUI
        from enhanced_dfs_gui import EnhancedDFSGUI
        print("   ✅ GUI imports successfully")

    except Exception as e:
        print(f"   ❌ GUI import failed: {e}")
        issues_found.append(f"GUI import error: {e}")

    # Summary and solutions
    print("\n" + "=" * 60)
    print("📊 DIAGNOSIS SUMMARY:")
    print("=" * 60)

    if not issues_found:
        print("✅ No issues found! The GUI should work.")
        print("\nTry running:")
        print("  python enhanced_dfs_gui.py")
    else:
        print(f"❌ Found {len(issues_found)} issues:\n")
        for i, issue in enumerate(issues_found, 1):
            print(f"{i}. {issue}")

        print("\n💡 SOLUTIONS:")

        if "PyQt5 not installed" in str(issues_found):
            print("\n1. Install PyQt5:")
            print("   pip install PyQt5")

        if "DISPLAY" in str(issues_found):
            print("\n2. Fix display:")
            print("   export DISPLAY=:0")
            print("   Or if using SSH: ssh -X user@host")

        if "Core import error" in str(issues_found):
            print("\n3. Fix core imports:")
            print("   python auto_fix_typing.py")

        if "main block" in str(issues_found):
            print("\n4. The GUI file needs a main block. Add at the end:")
            print('''
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = EnhancedDFSGUI()
    window.show()
    sys.exit(app.exec_())
''')

    # Offer to create simple working GUI
    print("\n" + "=" * 60)
    print("🔧 CREATE SIMPLE WORKING GUI?")
    print("=" * 60)
    response = input("\nCreate a simple_gui.py that should work? (y/n): ")

    if response.lower() == 'y':
        create_simple_gui()


def create_simple_gui():
    """Create a simple GUI that should work"""

    content = '''#!/usr/bin/env python3
"""Simple DFS GUI - Guaranteed to work"""

import sys
import os

# Set display if not set
if 'DISPLAY' not in os.environ and sys.platform == 'linux':
    os.environ['DISPLAY'] = ':0'

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class SimpleDFSGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple DFS Optimizer")
        self.setGeometry(100, 100, 800, 600)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Title
        title = QLabel("DFS Optimizer - Simple Version")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)

        # Load button
        self.load_btn = QPushButton("Load CSV File")
        self.load_btn.clicked.connect(self.load_csv)
        layout.addWidget(self.load_btn)

        # Info area
        self.info = QTextEdit()
        self.info.setReadOnly(True)
        layout.addWidget(self.info)

        # Optimize button
        self.opt_btn = QPushButton("Optimize Lineup")
        self.opt_btn.clicked.connect(self.optimize)
        self.opt_btn.setEnabled(False)
        layout.addWidget(self.opt_btn)

        self.log("Simple GUI loaded successfully!")

    def log(self, msg):
        self.info.append(msg)

    def load_csv(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if filename:
            self.log(f"Selected: {filename}")
            self.opt_btn.setEnabled(True)

    def optimize(self):
        self.log("Optimization would run here...")
        self.log("(Core system needs to be fixed first)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleDFSGUI()
    window.show()
    sys.exit(app.exec_())
'''

    with open('simple_gui.py', 'w') as f:
        f.write(content)

    print("\n✅ Created simple_gui.py")
    print("Try running: python simple_gui.py")


if __name__ == "__main__":
    diagnose_gui()