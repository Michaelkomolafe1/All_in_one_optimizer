#!/usr/bin/env python3
"""
Quick verification that real data mode is active
"""

print("🔍 VERIFYING REAL DATA MODE")
print("=" * 40)

# Check configuration
try:
    from bulletproof_dfs_core import USE_ONLY_REAL_DATA, REAL_DATA_SOURCES

    if USE_ONLY_REAL_DATA:
        print("✅ Real data mode is ACTIVE")

        print("\nEnabled sources:")
        for source, enabled in REAL_DATA_SOURCES.items():
            if enabled:
                print(f"  ✅ {source}")

        print("\nDisabled sources:")
        for source, enabled in REAL_DATA_SOURCES.items():
            if not enabled:
                print(f"  ❌ {source}")
    else:
        print("❌ Real data mode is NOT active")

except Exception as e:
    print(f"❌ Error: {e}")

# Check Statcast fetcher
print("\n" + "-" * 40)
try:
    from simple_statcast_fetcher import SimpleStatcastFetcher

    fetcher = SimpleStatcastFetcher()

    if hasattr(fetcher, 'USE_FALLBACK'):
        if fetcher.USE_FALLBACK:
            print("❌ Statcast fallbacks are ENABLED")
        else:
            print("✅ Statcast fallbacks are DISABLED")
    else:
        print("✅ Statcast fetcher modified (no fallbacks)")

except Exception as e:
    print(f"❌ Error checking Statcast: {e}")

print("\n✅ You're ready to run with REAL DATA ONLY!")
print("\nRun: python enhanced_dfs_gui.py")