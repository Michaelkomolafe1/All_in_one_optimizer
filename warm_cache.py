#!/usr/bin/env python3
"""
Cache Warming Utility
====================
Pre-populate caches for faster optimization
"""

from enhanced_caching_system import get_cache_manager
from vegas_lines import VegasLines
from simple_statcast_fetcher import SimpleStatcastFetcher
import time


def warm_caches():
    """Warm up all caches"""
    print("\n🔥 Warming up caches...")

    cache_manager = get_cache_manager()

    # 1. Warm Vegas cache
    print("\n📊 Warming Vegas cache...")
    vegas = VegasLines()
    vegas.get_vegas_lines()

    # 2. Get cache statistics
    stats = cache_manager.get_all_stats()

    print("\n📈 Cache Statistics:")
    for cache_name, cache_stats in stats.items():
        print(f"\n{cache_name}:")
        print(f"  Size: {cache_stats['size']}")
        print(f"  Hit Rate: {cache_stats['hit_rate']:.1%}")
        print(f"  Total Requests: {cache_stats['total_requests']}")


if __name__ == "__main__":
    start_time = time.time()
    warm_caches()
    elapsed = time.time() - start_time
    print(f"\n✅ Cache warming complete in {elapsed:.1f}s")