#!/usr/bin/env python3
"""
SIMPLE CACHING SYSTEM FIX
========================
Minimal caching to fix import errors
"""

import time
from typing import Dict, Any, Optional
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache to replace enhanced_caching_system"""

    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[str, tuple] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                # Move to end (LRU)
                self.cache.move_to_end(key)
                return value
            else:
                # Expired
                del self.cache[key]
        return None

    def put(self, key: str, value: Any):
        """Put value in cache"""
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)

        self.cache[key] = (value, time.time())

    def clear(self):
        """Clear cache"""
        self.cache.clear()


class DFSCacheManager:
    """Simple cache manager for DFS optimizer"""

    def __init__(self):
        self.vegas_cache = SimpleCache(ttl=600)  # 10 minutes
        self.statcast_cache = SimpleCache(ttl=3600)  # 1 hour
        self.scoring_cache = SimpleCache(ttl=300)  # 5 minutes

    def get_cache(self, cache_type: str) -> SimpleCache:
        """Get cache by type"""
        caches = {
            'vegas': self.vegas_cache,
            'statcast': self.statcast_cache,
            'scoring': self.scoring_cache
        }
        return caches.get(cache_type, self.scoring_cache)

    def cache_key(self, prefix: str, *args) -> str:
        """Generate cache key"""
        parts = [prefix] + [str(arg) for arg in args]
        return ":".join(parts)


# Global instance
_cache_manager = None


def get_cache_manager() -> DFSCacheManager:
    """Get or create cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = DFSCacheManager()
    return _cache_manager


# Create a module that can be imported as enhanced_caching_system
if __name__ != "__main__":
    # When imported, expose the necessary components
    CacheEntry = SimpleCache
    LRUCache = SimpleCache