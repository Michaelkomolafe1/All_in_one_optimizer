#!/usr/bin/env python3
"""
Quick launcher for enhanced optimizer
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from enhanced_optimizer_gui import main
    print("🚀 Launching Enhanced DFS Optimizer...")
    main()
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nMake sure you have created enhanced_optimizer_gui.py")
except Exception as e:
    print(f"❌ Error: {e}")
