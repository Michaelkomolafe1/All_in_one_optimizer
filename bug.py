#!/usr/bin/env python3
"""Test what's failing to import"""

print("Testing imports...")

try:
    from bulletproof_dfs_core import BulletproofDFSCore

    print("✅ bulletproof_dfs_core imported successfully!")
except Exception as e:
    print(f"❌ bulletproof_dfs_core failed: {e}")

    # Test individual imports
    try:
        import pulp

        print("  ✅ pulp OK")
    except:
        print("  ❌ pulp MISSING - install with: pip install pulp")

    try:
        import pandas

        print("  ✅ pandas OK")
    except:
        print("  ❌ pandas MISSING - install with: pip install pandas")

    try:
        import numpy

        print("  ✅ numpy OK")
    except:
        print("  ❌ numpy MISSING - install with: pip install numpy")

    try:
        from unified_data_system import UnifiedDataSystem

        print("  ✅ unified_data_system OK")
    except Exception as e:
        print(f"  ❌ unified_data_system failed: {e}")

    try:
        from optimal_lineup_optimizer import OptimalLineupOptimizer

        print("  ✅ optimal_lineup_optimizer OK")
    except Exception as e:
        print(f"  ❌ optimal_lineup_optimizer failed: {e}")