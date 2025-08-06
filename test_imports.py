#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, 'main_optimizer')

try:
    from unified_core_system_updated import UnifiedCoreSystem
    print("  ✓ UnifiedCoreSystem imported")
except ImportError as e:
    print(f"  ✗ UnifiedCoreSystem failed: {e}")

try:
    from unified_player_model import UnifiedPlayer
    print("  ✓ UnifiedPlayer imported")
except ImportError as e:
    print(f"  ✗ UnifiedPlayer failed: {e}")

try:
    from gui_strategy_configuration import GUIStrategyManager
    print("  ✓ GUIStrategyManager imported")
except ImportError as e:
    print(f"  ✗ GUIStrategyManager failed: {e}")

try:
    from smart_enrichment_manager import SmartEnrichmentManager
    print("  ✓ SmartEnrichmentManager imported")
except ImportError as e:
    print(f"  ✗ SmartEnrichmentManager failed: {e}")

print("\n✅ Import test complete!")
