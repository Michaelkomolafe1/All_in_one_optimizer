#!/usr/bin/env python3
"""
FIXED DFS OPTIMIZER LAUNCHER
============================
Properly sets up paths for imports
"""

import sys
import os

# Get the project root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir.endswith('core'):
    project_root = os.path.dirname(current_dir)
else:
    project_root = current_dir

# Add both project root and data directory to Python path
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'data'))

print(f"📁 Project root: {project_root}")
print(f"📁 Data directory: {os.path.join(project_root, 'data')}")

# Now try imports with better error messages
print("\n🔍 Checking imports...")

# Test each import individually
try:
    from smart_confirmation_system import SmartConfirmationSystem
    print("✅ SmartConfirmationSystem imported successfully")
except Exception as e:
    print(f"❌ SmartConfirmationSystem import failed: {e}")

try:
    from simple_statcast_fetcher import SimpleStatcastFetcher
    print("✅ SimpleStatcastFetcher imported successfully")
except Exception as e:
    print(f"❌ SimpleStatcastFetcher import failed: {e}")

try:
    from vegas_lines import VegasLines
    print("✅ VegasLines imported successfully")
except Exception as e:
    print(f"❌ VegasLines import failed: {e}")

try:
    from ownership_calculator import OwnershipCalculator
    print("✅ OwnershipCalculator imported successfully")
except Exception as e:
    print(f"❌ OwnershipCalculator import failed: {e}")

# Now run the optimizer
print("\n🚀 Starting DFS Optimizer...")
try:
    # Import from core directory
    sys.path.insert(0, os.path.join(project_root, 'core'))
    from dfs_optimizer_integrated import main
    main()
except Exception as e:
    print(f"\n❌ Error starting optimizer: {e}")
    import traceback
    traceback.print_exc()