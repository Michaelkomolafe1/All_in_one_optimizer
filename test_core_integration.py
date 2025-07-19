#!/usr/bin/env python3
"""Test Core System Integration"""

import sys

print("🧪 TESTING CORE SYSTEM")
print("=" * 60)

# Test 1: Import core
try:
    from bulletproof_dfs_core import BulletproofDFSCore
    print("✅ Core system imports successfully")
except Exception as e:
    print(f"❌ Core import failed: {e}")
    sys.exit(1)

# Test 2: Initialize core
try:
    core = BulletproofDFSCore(mode="test")
    print("✅ Core initializes successfully")
except Exception as e:
    print(f"❌ Core initialization failed: {e}")
    sys.exit(1)

# Test 3: Check modules
print("\n📦 Available modules:")
if hasattr(core, 'modules_status'):
    for module, status in core.modules_status.items():
        print(f"  {'✅' if status else '❌'} {module}")
else:
    print("  ⚠️  Module status not available")

# Test 4: Check methods
print("\n🔧 Core methods:")
methods = ['load_players', 'run_confirmation_analysis', 'enrich_player_data', 'optimize']
for method in methods:
    if hasattr(core, method):
        print(f"  ✅ {method}")
    else:
        print(f"  ❌ {method}")

print("\n✅ Core system test complete!")
