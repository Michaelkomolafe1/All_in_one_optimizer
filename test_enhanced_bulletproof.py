#!/usr/bin/env python3
"""
Enhanced Bulletproof DFS System Tests
=====================================
Comprehensive testing for the bulletproof DFS system
"""

import sys
import os
import tempfile
from pathlib import Path

def test_core_imports():
    """Test core module imports"""
    try:
        from bulletproof_dfs_core import BulletproofDFSCore, AdvancedPlayer
        print("✅ Bulletproof core imports successfully")
        return True
    except Exception as e:
        print(f"❌ Core import failed: {e}")
        return False

def test_gui_imports():
    """Test GUI imports"""
    try:
        from enhanced_dfs_gui import EnhancedDFSGUI
        print("✅ Enhanced GUI imports successfully")
        return True
    except Exception as e:
        print(f"❌ GUI import failed: {e}")
        return False

def test_core_functionality():
    """Test core functionality"""
    try:
        from bulletproof_dfs_core import BulletproofDFSCore, create_enhanced_test_data

        # Create test data
        dk_file, dff_file = create_enhanced_test_data()

        # Test core
        core = BulletproofDFSCore()
        success = core.load_draftkings_csv(dk_file)

        # Cleanup
        os.unlink(dk_file)

        if success:
            print(f"✅ Core functionality test passed")
            return True
        else:
            print("❌ Core functionality test failed")
            return False

    except Exception as e:
        print(f"❌ Core functionality test error: {e}")
        return False

def test_player_creation():
    """Test player creation"""
    try:
        from bulletproof_dfs_core import AdvancedPlayer

        test_data = {
            'id': 1,
            'name': 'Test Player',
            'position': 'OF',
            'team': 'HOU',
            'salary': 4500,
            'projection': 8.0
        }

        player = AdvancedPlayer(test_data)

        if player.name == 'Test Player' and player.salary == 4500:
            print("✅ Player creation test passed")
            return True
        else:
            print("❌ Player creation test failed")
            return False

    except Exception as e:
        print(f"❌ Player creation test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 ENHANCED BULLETPROOF DFS SYSTEM TESTS")
    print("=" * 50)

    tests = [
        ("Core Imports", test_core_imports),
        ("GUI Imports", test_gui_imports),
        ("Core Functionality", test_core_functionality),
        ("Player Creation", test_player_creation)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        if test_func():
            passed += 1

    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
