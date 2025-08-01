#!/usr/bin/env python3
"""
ENHANCED IN-MEMORY CACHING SYSTEM
=================================
Efficient caching without external dependencies
"""

import time
import hashlib
import json
import pickle
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Optional, Callable, Tuple
import logging
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)


class CacheEntry:
    """Single cache entry with metadata"""

    def __init__(self, value: Any, ttl_seconds: int = 300):
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.last_accessed = time.time()

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.created_at > self.ttl_seconds

    def access(self) -> Any:
        """Access the cached value and update metadata"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value


class LRUCache:
    """Thread-safe LRU cache with TTL support"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.Lock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return None

            entry = self.cache[key]

            # Check expiration
            if entry.is_expired():
                del self.cache[key]
                self.stats['expirations'] += 1
                self.stats['misses'] += 1
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.stats['hits'] += 1

            return entry.access()

    def put(self, key: str, value: Any, ttl: Optional[int] = None):
        """Put value in cache"""
        with self.lock:
            # Remove if exists (to update position)
            if key in self.cache:
                del self.cache[key]

            # Evict if necessary
            while len(self.cache) >= self.max_size:
                evicted_key = next(iter(self.cache))
                del self.cache[evicted_key]
                self.stats['evictions'] += 1

            # Add new entry
            ttl = ttl or self.default_ttl
            self.cache[key] = CacheEntry(value, ttl)

    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0

            return {
                **self.stats,
                'size': len(self.cache),
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }


class DFSCacheManager:
    """Centralized cache manager for DFS optimizer"""

    def __init__(self):
        # Different caches for different data types
        self.caches = {
            'statcast': LRUCache(max_size=500, default_ttl=3600),  # 1 hour
            'vegas': LRUCache(max_size=100, default_ttl=600),  # 10 minutes
            'scoring': LRUCache(max_size=1000, default_ttl=300),  # 5 minutes
            'lineups': LRUCache(max_size=100, default_ttl=1800),  # 30 minutes
            'api_calls': LRUCache(max_size=200, default_ttl=300)  # 5 minutes
        }

    def get_cache(self, cache_type: str) -> LRUCache:
        """Get specific cache by type"""
        return self.caches.get(cache_type, self.caches['api_calls'])

    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        # Create string representation
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

        # Hash for consistent key
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def cached_statcast(self, player_name: str, position: str) -> Optional[Any]:
        """Get cached Statcast data"""
        key = self.cache_key('statcast', player_name, position)
        return self.get_cache('statcast').get(key)

    def cache_statcast(self, player_name: str, position: str, data: Any):
        """Cache Statcast data"""
        key = self.cache_key('statcast', player_name, position)
        self.get_cache('statcast').put(key, data)

    def cached_vegas(self, team: str) -> Optional[Dict]:
        """Get cached Vegas data"""
        key = self.cache_key('vegas', team)
        return self.get_cache('vegas').get(key)

    def cache_vegas(self, team: str, data: Dict):
        """Cache Vegas data"""
        key = self.cache_key('vegas', team)
        self.get_cache('vegas').put(key, data)

    def clear_all(self):
        """Clear all caches"""
        for cache in self.caches.values():
            cache.clear()

    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all caches"""
        return {
            name: cache.get_stats()
            for name, cache in self.caches.items()
        }


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> DFSCacheManager:
    """Get or create global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = DFSCacheManager()
    return _cache_manager


# Decorator for caching function results
def cached(cache_type: str = 'api_calls', ttl: int = None):
    """Decorator to cache function results"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache manager
            manager = get_cache_manager()
            cache = manager.get_cache(cache_type)

            # Generate cache key
            key = manager.cache_key(func.__name__, *args, **kwargs)

            # Check cache
            result = cache.get(key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result

            # Call function
            result = func(*args, **kwargs)

            # Cache result
            cache.put(key, result, ttl)

            return result

        return wrapper

    return decorator


# Example usage in your modules
class CachedStatcastFetcher:
    """Example of integrating cache into Statcast fetcher"""

    def __init__(self):
        self.cache_manager = get_cache_manager()

    def fetch_player_data(self, player_name: str, position: str):
        # Check cache first
        cached_data = self.cache_manager.cached_statcast(player_name, position)
        if cached_data is not None:
            logger.info(f"Using cached Statcast data for {player_name}")
            return cached_data

        # Fetch from API
        data = self._fetch_from_api(player_name, position)

        # Cache the result
        if data is not None:
            self.cache_manager.cache_statcast(player_name, position, data)

        return data

    @cached(cache_type='statcast', ttl=3600)
    def _fetch_from_api(self, player_name: str, position: str):
        # Your existing API call
        pass


# Integration into existing modules
def integrate_caching():
    """Code snippets to integrate caching into existing modules"""

    vegas_integration = '''
    # In vegas_lines.py get_vegas_lines method:

    def get_vegas_lines(self, force_refresh: bool = False):
        if not force_refresh:
            # Check cache
            cache_manager = get_cache_manager()
            cache_key = cache_manager.cache_key('vegas_all', datetime.now().strftime('%Y%m%d_%H'))
            cached = cache_manager.get_cache('vegas').get(cache_key)
            if cached:
                self.lines = cached
                return cached

        # ... existing fetch code ...

        # Cache the result
        if self.lines:
            cache_manager.get_cache('vegas').put(cache_key, self.lines)

        return self.lines
    '''

    scoring_integration = '''
    # In unified_scoring_engine.py calculate_score method:

    @cached(cache_type='scoring', ttl=300)
    def calculate_score(self, player: Any) -> float:
        # ... existing scoring logic ...
    '''

    return vegas_integration, scoring_integration


if __name__ == "__main__":
    print("✅ Enhanced Caching System")
    print("\nFeatures:")
    print("  - LRU eviction policy")
    print("  - TTL support")
    print("  - Thread-safe operations")
    print("  - Cache statistics")
    print("  - Multiple cache types")

    # Demo
    manager = get_cache_manager()

    # Simulate some caching
    manager.cache_statcast("Mike Trout", "OF", {"avg": .300})
    manager.cache_vegas("LAA", {"total": 9.5, "home": True})

    print("\nCache Statistics:")
    for cache_name, stats in manager.get_all_stats().items():
        print(f"\n{cache_name}:")
        print(f"  Size: {stats['size']}")
        print(f"  Hit Rate: {stats['hit_rate']:.1%}")