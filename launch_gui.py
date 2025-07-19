#!/usr/bin/env python3
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
                        "To fix:\n"
                        "1. Run: python fix_gui_only.py\n"
                        "2. Check that all files are present\n"
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
