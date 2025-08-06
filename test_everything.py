#!/usr/bin/env python3
"""Test that everything works after fixes"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_all():
    """Test all components"""
    print("=" * 60)
    print("TESTING ALL COMPONENTS")
    print("=" * 60)

    # Test 1: EnhancedScoringEngineV2
    print("\n1. Testing EnhancedScoringEngineV2...")
    try:
        from main_optimizer.enhanced_scoring_engine_v2 import EnhancedScoringEngineV2
        engine = EnhancedScoringEngineV2(use_bayesian=False)
        print("   ✅ EnhancedScoringEngineV2 initialized")

        # Test scoring methods
        class TestPlayer:
            def __init__(self):
                self.base_projection = 15.0
                self.name = "Test Player"

        player = TestPlayer()
        gpp_score = engine.score_player_gpp(player)
        cash_score = engine.score_player_cash(player)
        print(f"   ✅ Scoring works: GPP={gpp_score}, Cash={cash_score}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Test 2: UnifiedCoreSystem
    print("\n2. Testing UnifiedCoreSystem...")
    try:
        from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
        system = UnifiedCoreSystem()
        print("   ✅ UnifiedCoreSystem initialized")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Test 3: SmartEnrichmentManager
    print("\n3. Testing SmartEnrichmentManager...")
    try:
        from main_optimizer.smart_enrichment_manager import SmartEnrichmentManager
        manager = SmartEnrichmentManager()
        print("   ✅ SmartEnrichmentManager initialized")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Test 4: GUIStrategyManager
    print("\n4. Testing GUIStrategyManager...")
    try:
        from main_optimizer.gui_strategy_configuration import GUIStrategyManager
        strategy_mgr = GUIStrategyManager()
        strategies = strategy_mgr.get_gui_strategies()
        print(f"   ✅ GUIStrategyManager initialized with {sum(len(v) for v in strategies.values())} strategies")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Test 5: GUI (without showing)
    print("\n5. Testing GUI initialization...")
    try:
        from PyQt5.QtWidgets import QApplication
        from main_optimizer.GUI import SimplifiedDFSOptimizerGUI

        app = QApplication([])
        gui = SimplifiedDFSOptimizerGUI()
        print("   ✅ GUI initialized successfully!")
        app.quit()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    return True

if __name__ == "__main__":
    success = test_all()

    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("Your optimizer should work now!")
        print("\nRun your GUI with:")
        print("  python main_optimizer/GUI.py")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    print("=" * 60)
