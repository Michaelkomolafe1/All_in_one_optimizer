#!/usr/bin/env python3
"""
Test script to verify DFS upgrades integration
"""

print("🧪 Testing DFS Upgrades Integration...")
print("=" * 50)

try:
    # Test imports
    print("\n1. Testing imports...")
    from bulletproof_dfs_core import BulletproofDFSCore
    print("   ✅ Core imported")

    # Test cache
    print("\n2. Testing cache...")
    from smart_cache import smart_cache
    test_data = smart_cache.get_or_fetch(
        "test_key",
        lambda: {"test": "data"},
        "default"
    )
    print(f"   ✅ Cache working: {test_data}")

    # Test multi-lineup
    print("\n3. Testing multi-lineup...")
    from multi_lineup_optimizer import MultiLineupOptimizer
    print("   ✅ Multi-lineup imported")

    # Test tracker
    print("\n4. Testing performance tracker...")
    from performance_tracker import tracker
    print("   ✅ Tracker imported")

    # Test core integration
    print("\n5. Testing core integration...")
    core = BulletproofDFSCore()

    if hasattr(core, 'get_cached_data'):
        print("   ✅ get_cached_data method found")
    else:
        print("   ❌ get_cached_data method missing")

    if hasattr(core, 'generate_multiple_lineups'):
        print("   ✅ generate_multiple_lineups method found")
    else:
        print("   ❌ generate_multiple_lineups method missing")

    print("\n✅ Integration test complete!")

except Exception as e:
    print(f"\n❌ Integration test failed: {e}")
    import traceback
    traceback.print_exc()
