#!/usr/bin/env python3
"""Test script to verify all fixes work"""

import sys
import os

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work"""
    print("Testing imports...")

    try:
        print("  Testing EnhancedScoringEngineV2...")
        from main_optimizer.enhanced_scoring_engine_v2 import EnhancedScoringEngineV2
        engine = EnhancedScoringEngineV2(use_bayesian=False)  # Should work now!
        print("  ✅ EnhancedScoringEngineV2 works!")

        print("  Testing UnifiedCoreSystem...")
        from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
        system = UnifiedCoreSystem()  # Should initialize without error
        print("  ✅ UnifiedCoreSystem works!")

        print("  Testing SmartEnrichmentManager...")
        from main_optimizer.smart_enrichment_manager import SmartEnrichmentManager
        manager = SmartEnrichmentManager()
        print("  ✅ SmartEnrichmentManager works!")

        print("  Testing GUIStrategyManager...")
        from main_optimizer.gui_strategy_configuration import GUIStrategyManager
        strategy_mgr = GUIStrategyManager()
        print("  ✅ GUIStrategyManager works!")

        print("\n✅ All imports successful!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gui():
    """Test that GUI can start"""
    print("\nTesting GUI startup...")

    try:
        from main_optimizer.GUI import SimplifiedDFSOptimizerGUI
        from PyQt5.QtWidgets import QApplication

        app = QApplication([])
        gui = SimplifiedDFSOptimizerGUI()
        print("✅ GUI initialized successfully!")

        # Don't actually show it, just test initialization
        return True

    except Exception as e:
        print(f"❌ GUI Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING MAIN OPTIMIZER FIXES")
    print("=" * 60)

    # Run tests
    import_success = test_imports()
    gui_success = test_gui()

    print("\n" + "=" * 60)
    if import_success and gui_success:
        print("🎉 ALL TESTS PASSED! Your optimizer should work now!")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    print("=" * 60)
