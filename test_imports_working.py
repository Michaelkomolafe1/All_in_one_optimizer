#!/usr/bin/env python3
"""Working Import Test"""

def test_imports():
    """Test all imports work"""
    print("Testing imports...")

    success = []
    failed = []

    # Test 1: Core system
    try:
        from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
        success.append("UnifiedCoreSystem")
        print("✓ UnifiedCoreSystem")
    except Exception as e:
        failed.append(f"UnifiedCoreSystem: {e}")
        print(f"❌ UnifiedCoreSystem: {e}")

    # Test 2: Player model
    try:
        from main_optimizer.unified_player_model import UnifiedPlayer
        success.append("UnifiedPlayer")
        print("✓ UnifiedPlayer")
    except Exception as e:
        failed.append(f"UnifiedPlayer: {e}")
        print(f"❌ UnifiedPlayer: {e}")

    # Test 3: Strategies
    try:
        from main_optimizer.cash_strategies import build_projection_monster
        success.append("Cash strategies")
        print("✓ Cash strategies")
    except Exception as e:
        failed.append(f"Cash strategies: {e}")
        print(f"❌ Cash strategies: {e}")

    # Test 4: Package import
    try:
        import main_optimizer
        success.append("Package import")
        print("✓ Package import")
    except Exception as e:
        failed.append(f"Package: {e}")
        print(f"❌ Package: {e}")

    print(f"\n✅ Passed: {len(success)}")
    print(f"❌ Failed: {len(failed)}")

    return len(failed) == 0

if __name__ == "__main__":
    # Run as script, not test
    result = test_imports()
    if result:
        print("\n🎉 ALL IMPORTS WORKING!")
    else:
        print("\n⚠️ Some imports still failing")
