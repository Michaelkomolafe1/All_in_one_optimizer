#!/usr/bin/env python3
"""
DFS Optimizer GUI Launcher
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from main_optimizer.GUI import CompleteDFSOptimizerGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompleteDFSOptimizerGUI()
    window.show()
    sys.exit(app.exec_())
