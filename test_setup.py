#!/usr/bin/env python3
"""Test that everything is set up correctly"""

import sys
import os

# Add to path
sys.path.insert(0, 'main_optimizer')

print("🧪 Testing DFS Optimizer Setup")
print("=" * 40)

# Test imports
tests = [
    ("Core System", "from unified_core_system import UnifiedCoreSystem"),
    ("Strategy Selector", "from strategy_selector import StrategyAutoSelector"),
    ("Vegas Lines", "from vegas_lines import VegasLines"),
    ("Cash Strategies", "from cash_strategies import build_projection_monster"),
    ("GPP Strategies", "from gpp_strategies import build_correlation_value"),
]

for name, import_str in tests:
    try:
        exec(import_str)
        print(f"✅ {name}: OK")
    except Exception as e:
        print(f"❌ {name}: {e}")

# Test Vegas
print("\n🎲 Testing Vegas API...")
try:
    from vegas_lines import VegasLines
    v = VegasLines()
    lines = v.get_vegas_lines()
    if lines:
        print(f"✅ Vegas: Got {len(lines)} team lines")
    else:
        print("⚠️  Vegas: No data (check API)")
except Exception as e:
    print(f"❌ Vegas: {e}")

print("\n✨ Setup test complete!")
