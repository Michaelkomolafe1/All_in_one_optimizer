#!/usr/bin/env python3
"""DFS Optimizer Launcher"""

import sys
import os

# Add main_optimizer to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'main_optimizer'))

# Launch GUI
try:
    from GUI_simplified_dfs_optimizer import SimplifiedDFSOptimizer
    import tkinter as tk
    
    print("🚀 Launching DFS Optimizer GUI...")
    root = tk.Tk()
    app = SimplifiedDFSOptimizer(root)
    root.mainloop()
except ImportError as e:
    print(f"Error: {e}")
    print("Make sure you're in the project root and have all dependencies installed")
