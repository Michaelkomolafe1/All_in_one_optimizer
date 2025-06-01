#!/usr/bin/env python3
"""
Simple DFS Test Script
Tests each component individually
"""

import sys
from pathlib import Path

def test_packages():
    """Test package imports"""
    print("📦 Testing package imports...")

    packages = {
        'pandas': 'pandas',
        'numpy': 'numpy', 
        'pulp': 'pulp',
        'requests': 'requests'
    }

    all_good = True
    for name, module in packages.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError as e:
            print(f"   ❌ {name}: {e}")
            all_good = False

    # Test PyQt5 separately (it's finicky)
    try:
        from PyQt5.QtWidgets import QApplication
        print("   ✅ PyQt5")
    except ImportError as e:
        print(f"   ❌ PyQt5: {e}")
        all_good = False

    return all_good

def test_enhanced_core():
    """Test enhanced core"""
    print("\n🔬 Testing enhanced core...")

    try:
        from enhanced_dfs_core import (
            EnhancedDFSCore,
            StackingConfig,
            load_and_optimize_with_enhanced_features
        )
        print("   ✅ Enhanced core imports")

        # Test configuration
        config = StackingConfig()
        print(f"   ✅ Stacking config: {config.min_stack_size}-{config.max_stack_size} players")

        return True

    except Exception as e:
        print(f"   ❌ Enhanced core failed: {e}")
        return False

def test_base_core():
    """Test base core"""
    print("\n⚙️ Testing base core...")

    try:
        from optimized_dfs_core_with_statcast import (
            OptimizedDFSCore,
            load_and_optimize_complete_pipeline
        )
        print("   ✅ Base core imports")
        return True

    except Exception as e:
        print(f"   ❌ Base core failed: {e}")
        return False

def test_vegas_integration():
    """Test Vegas lines"""
    print("\n💰 Testing Vegas integration...")

    try:
        from vegas_lines import VegasLines
        vegas = VegasLines(verbose=False)
        print("   ✅ Vegas lines imports")
        return True

    except Exception as e:
        print(f"   ❌ Vegas integration failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 SIMPLE DFS COMPONENT TEST")
    print("=" * 40)

    tests = [
        ("Packages", test_packages),
        ("Enhanced Core", test_enhanced_core),
        ("Base Core", test_base_core), 
        ("Vegas Integration", test_vegas_integration)
    ]

    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()

    print("\n📊 TEST RESULTS:")
    print("-" * 20)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")

    passed_count = sum(results.values())
    total_count = len(results)

    print(f"\n📈 Overall: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED - System ready!")
        return 0
    elif passed_count >= 2:
        print("⚠️ Partial success - System should work with reduced features")
        return 0
    else:
        print("❌ Multiple failures - Need troubleshooting")
        return 1

if __name__ == "__main__":
    sys.exit(main())
