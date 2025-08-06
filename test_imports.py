#!/usr/bin/env python3
"""Test that all imports work"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

try:
    from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
    print("✓ UnifiedCoreSystem")
except Exception as e:
    print(f"❌ UnifiedCoreSystem: {e}")

try:
    from main_optimizer.unified_player_model import UnifiedPlayer
    print("✓ UnifiedPlayer")
except Exception as e:
    print(f"❌ UnifiedPlayer: {e}")

try:
    from main_optimizer.enhanced_scoring_engine_v2 import EnhancedScoringEngineV2
    print("✓ EnhancedScoringEngineV2")
except Exception as e:
    print(f"❌ EnhancedScoringEngineV2: {e}")

try:
    from main_optimizer.cash_strategies import build_projection_monster
    print("✓ Cash strategies")
except Exception as e:
    print(f"❌ Cash strategies: {e}")

try:
    from main_optimizer.gpp_strategies import build_correlation_value
    print("✓ GPP strategies")
except Exception as e:
    print(f"❌ GPP strategies: {e}")

print("\n✅ Import test complete!")
