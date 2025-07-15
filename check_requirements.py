#!/usr/bin/env python3
"""Check and install requirements"""

import subprocess
import sys

required = [
    'streamlit',
    'pandas',
    'numpy',
    'pulp',
    'scikit-learn'
]

print("Checking requirements...")

for package in required:
    try:
        __import__(package)
        print(f"✅ {package}")
    except ImportError:
        print(f"📦 Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

print("\n✅ All requirements satisfied!")
print("\nNow run: streamlit run enhanced_dfs_gui.py")
