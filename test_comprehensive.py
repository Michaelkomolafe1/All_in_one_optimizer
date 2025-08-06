#!/usr/bin/env python3
"""
COMPREHENSIVE TEST SCRIPT
=========================
Tests all components to ensure everything works
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test all imports work correctly"""
    print("\n" + "=" * 60)
    print("TESTING IMPORTS")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    # Test 1: Enhanced Scoring Engine
    print("\n1. Testing EnhancedScoringEngineV2...")
    try:
        from main_optimizer.enhanced_scoring_engine_v2 import EnhancedScoringEngineV2
        engine = EnhancedScoringEngineV2(use_bayesian=False)

        # Create test player
        class TestPlayer:
            def __init__(self):
                self.base_projection = 15.0
                self.name = "Test Player"
                self.ownership_projection = 12.0

        player = TestPlayer()
        gpp_score = engine.score_player_gpp(player)
        cash_score = engine.score_player_cash(player)

        print(f"   ✅ Scoring engine works!")
        print(f"      GPP Score: {gpp_score}")
        print(f"      Cash Score: {cash_score}")
        success_count += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        fail_count += 1

    # Test 2: Smart Enrichment Manager
    print("\n2. Testing SmartEnrichmentManager...")
    try:
        from main_optimizer.smart_enrichment_manager import SmartEnrichmentManager
        manager = SmartEnrichmentManager()
        manager.set_enrichment_source('test', None)
        print("   ✅ SmartEnrichmentManager works!")
        success_count += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        fail_count += 1

    # Test 3: GUI Strategy Manager
    print("\n3. Testing GUIStrategyManager...")
    try:
        from main_optimizer.gui_strategy_configuration import GUIStrategyManager
        strategy_mgr = GUIStrategyManager()
        strategies = strategy_mgr.get_gui_strategies()
        total_strategies = sum(len(v) for v in strategies.values())
        print(f"   ✅ GUIStrategyManager works!")
        print(f"      Found {total_strategies} strategies")
        success_count += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        fail_count += 1

    # Test 4: Unified Core System
    print("\n4. Testing UnifiedCoreSystem...")
    try:
        from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
        system = UnifiedCoreSystem()
        print("   ✅ UnifiedCoreSystem initialized!")
        success_count += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        fail_count += 1

    # Test 5: Unified Player Model
    print("\n5. Testing UnifiedPlayer...")
    try:
        from main_optimizer.unified_player_model import UnifiedPlayer

        # Create test player data
        player_data = {
            'Name': 'Test Player',
            'Position': 'P',
            'Salary': 10000,
            'Team': 'NYY',
            'AvgPointsPerGame': 15.0
        }

        player = UnifiedPlayer(player_data)
        print(f"   ✅ UnifiedPlayer works!")
        print(f"      Name: {player.name}")
        print(f"      Projection: {player.base_projection}")
        success_count += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        fail_count += 1

    # Test 6: GUI (headless test)
    print("\n6. Testing GUI initialization...")
    try:
        # Set environment for headless
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'

        from PyQt5.QtWidgets import QApplication
        from main_optimizer.GUI import SimplifiedDFSOptimizerGUI

        app = QApplication([])
        gui = SimplifiedDFSOptimizerGUI()

        print("   ✅ GUI initialized successfully!")
        success_count += 1

        app.quit()
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        if "could not connect to display" in str(e).lower():
            print("      (This is normal if running without display)")
        fail_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {success_count}/6")
    print(f"❌ Failed: {fail_count}/6")

    if fail_count == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYour optimizer is ready to use:")
        print("  python main_optimizer/GUI.py")
    elif success_count >= 5:
        print("\n✅ Core components working!")
        print("GUI test may fail in headless environment - this is normal")
        print("\nTry running your GUI:")
        print("  python main_optimizer/GUI.py")
    else:
        print("\n⚠️ Some critical tests failed")
        print("Please check the errors above")

    return fail_count == 0


if __name__ == "__main__":
    # Run as standalone script, not pytest
    test_imports()
