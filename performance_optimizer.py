#!/usr/bin/env python3
"""
ENHANCED PERFORMANCE OPTIMIZER - With proper cache management
===========================================================
Fixes memory leak and adds LRU cache eviction
"""

import hashlib
import heapq
import logging
import os
import pickle
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Enhanced cache configuration"""

    max_size: int = 10000
    ttl_seconds: Dict[str, int] = field(
        default_factory=lambda: {
            "player_scores": 300,  # 5 minutes
            "api_calls": 3600,  # 1 hour
            "statcast": 7200,  # 2 hours
            "vegas": 600,  # 10 minutes
            "recent_form": 900,  # 15 minutes
            "lineup_correlation": 1800,  # 30 minutes
        }
    )
    enable_disk_cache: bool = True
    cache_dir: str = ".dfs_cache"
    eviction_policy: str = "lru"  # lru or lfu

    # Performance monitoring
    enable_monitoring: bool = True
    slow_operation_threshold: float = 0.1  # seconds

    # Memory management
    max_memory_mb: int = 100
    check_memory_interval: int = 100  # Check every N operations


class LRUCache:
    """Thread-safe LRU cache implementation"""

    def __init__(self, max_size: int):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.access_count = {}
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Tuple[Any, datetime]]:
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.access_count[key] = self.access_count.get(key, 0) + 1
                return self.cache[key]
            return None

    def put(self, key: str, value: Any, timestamp: datetime):
        with self.lock:
            if key in self.cache:
                # Update existing
                self.cache.move_to_end(key)
            else:
                # Add new
                if len(self.cache) >= self.max_size:
                    # Evict least recently used
                    evicted_key = next(iter(self.cache))
                    del self.cache[evicted_key]
                    if evicted_key in self.access_count:
                        del self.access_count[evicted_key]

            self.cache[key] = (value, timestamp)
            self.access_count[key] = self.access_count.get(key, 0) + 1

    def clear(self):
        with self.lock:
            self.cache.clear()
            self.access_count.clear()

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "total_accesses": sum(self.access_count.values()),
                "most_accessed": max(self.access_count.items(), key=lambda x: x[1])[0] if self.access_count else None
            }


import threading


class EnhancedPerformanceOptimizer:
    """Enhanced performance optimization with monitoring and memory management"""

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._memory_cache = LRUCache(self.config.max_size)
        self._cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
        self._processing_times = []
        self._operation_count = 0

        # Performance monitoring
        self._slow_operations = []
        self._operation_timings = {}

        # Create cache directory if needed
        if self.config.enable_disk_cache:
            os.makedirs(self.config.cache_dir, exist_ok=True)

    def cached(self, category: str = "default", key_func: Optional[Callable] = None):
        """Enhanced decorator with monitoring"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()

                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self._generate_cache_key(func.__name__, args, kwargs)

                cache_key = f"{category}:{cache_key}"

                # Check cache
                cached_result = self._get_from_cache(cache_key, category)
                if cached_result is not None:
                    self._cache_stats["hits"] += 1
                    elapsed = time.time() - start_time
                    self._record_timing(func.__name__, elapsed, True)
                    return cached_result

                # Cache miss - compute result
                self._cache_stats["misses"] += 1

                try:
                    result = func(*args, **kwargs)

                    # Cache the result
                    self._add_to_cache(cache_key, result, category)

                    elapsed = time.time() - start_time
                    self._record_timing(func.__name__, elapsed, False)

                    # Check for slow operations
                    if self.config.enable_monitoring and elapsed > self.config.slow_operation_threshold:
                        self._record_slow_operation(func.__name__, elapsed, args, kwargs)

                    return result

                except Exception as e:
                    elapsed = time.time() - start_time
                    self._record_timing(func.__name__, elapsed, False, error=True)
                    logger.error(f"Error in {func.__name__}: {e}")
                    raise
                finally:
                    # Periodic memory check
                    self._operation_count += 1
                    if self._operation_count % self.config.check_memory_interval == 0:
                        self._check_memory_usage()

            return wrapper

        return decorator

    def _get_from_cache(self, key: str, category: str) -> Optional[Any]:
        """Get value from cache with TTL check"""
        # Check memory cache
        cached = self._memory_cache.get(key)
        if cached:
            value, timestamp = cached
            ttl = self.config.ttl_seconds.get(category, 300)
            if (datetime.now() - timestamp).total_seconds() < ttl:
                return value
            else:
                # Expired - remove from cache
                self._memory_cache.cache.pop(key, None)

        # Check disk cache if enabled
        if self.config.enable_disk_cache:
            return self._get_from_disk_cache(key, category)

        return None

    def _add_to_cache(self, key: str, value: Any, category: str):
        """Add value to cache with size management"""
        timestamp = datetime.now()

        # Add to memory cache (LRU handles eviction)
        self._memory_cache.put(key, value, timestamp)

        # Also save to disk if enabled
        if self.config.enable_disk_cache:
            self._save_to_disk_cache(key, value, category)

    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key with better handling of complex objects"""
        try:
            # Create a string representation
            key_parts = [func_name]

            # Handle args
            for arg in args:
                if hasattr(arg, '__dict__'):
                    # For objects, use their attributes
                    key_parts.append(str(sorted(arg.__dict__.items())))
                else:
                    key_parts.append(str(arg))

            # Handle kwargs
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")

            key_string = "|".join(key_parts)

            # Hash for consistent length
            return hashlib.md5(key_string.encode()).hexdigest()

        except Exception as e:
            logger.warning(f"Error generating cache key: {e}")
            # Fallback to timestamp-based key
            return f"{func_name}_{int(time.time() * 1000000)}"

    def _get_from_disk_cache(self, key: str, category: str) -> Optional[Any]:
        """Load from disk cache"""
        cache_file = os.path.join(self.config.cache_dir, f"{key}.pkl")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)

                # Check TTL
                ttl = self.config.ttl_seconds.get(category, 300)
                if (datetime.now() - data['timestamp']).total_seconds() < ttl:
                    return data['value']
                else:
                    # Expired - remove file
                    os.remove(cache_file)
            except Exception as e:
                logger.warning(f"Error reading disk cache: {e}")
                # Remove corrupted file
                try:
                    os.remove(cache_file)
                except:
                    pass

        return None

    def _save_to_disk_cache(self, key: str, value: Any, category: str):
        """Save to disk cache"""
        cache_file = os.path.join(self.config.cache_dir, f"{key}.pkl")

        try:
            data = {
                'value': value,
                'timestamp': datetime.now(),
                'category': category
            }

            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)

        except Exception as e:
            logger.warning(f"Error saving to disk cache: {e}")

    def _record_timing(self, func_name: str, elapsed: float, cache_hit: bool, error: bool = False):
        """Record operation timing for monitoring"""
        if not self.config.enable_monitoring:
            return

        if func_name not in self._operation_timings:
            self._operation_timings[func_name] = {
                'count': 0,
                'total_time': 0,
                'cache_hits': 0,
                'errors': 0,
                'max_time': 0,
                'min_time': float('inf')
            }

        stats = self._operation_timings[func_name]
        stats['count'] += 1
        stats['total_time'] += elapsed
        stats['max_time'] = max(stats['max_time'], elapsed)
        stats['min_time'] = min(stats['min_time'], elapsed)

        if cache_hit:
            stats['cache_hits'] += 1
        if error:
            stats['errors'] += 1

    def _record_slow_operation(self, func_name: str, elapsed: float, args: tuple, kwargs: dict):
        """Record slow operations for analysis"""
        self._slow_operations.append({
            'function': func_name,
            'elapsed': elapsed,
            'timestamp': datetime.now(),
            'args_preview': str(args)[:100],  # Truncate for memory
            'kwargs_preview': str(kwargs)[:100]
        })

        # Keep only recent slow operations
        if len(self._slow_operations) > 100:
            self._slow_operations = self._slow_operations[-100:]

        logger.warning(f"Slow operation: {func_name} took {elapsed:.3f}s")

    def _check_memory_usage(self):
        """Check memory usage and clear cache if needed"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            if memory_mb > self.config.max_memory_mb:
                logger.warning(f"Memory usage ({memory_mb:.1f}MB) exceeds limit ({self.config.max_memory_mb}MB)")
                # Clear 20% of cache
                self.clear_cache(partial=0.2)
        except ImportError:
            # psutil not available
            pass

    def batch_process(self, items: List[Any], process_func: Callable,
                      batch_size: Optional[int] = None, max_workers: Optional[int] = None) -> List[Any]:
        """Enhanced batch processing with progress tracking"""
        if not items:
            return []

        batch_size = batch_size or 50
        max_workers = max_workers or 4

        results = [None] * len(items)  # Pre-allocate results array
        total_items = len(items)
        processed = 0

        # Process in batches
        for i in range(0, total_items, batch_size):
            batch = items[i:i + batch_size]
            batch_start_idx = i

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit batch with index tracking
                future_to_idx = {}
                for batch_idx, item in enumerate(batch):
                    future = executor.submit(process_func, item)
                    actual_idx = batch_start_idx + batch_idx
                    future_to_idx[future] = actual_idx

                # Collect results in order
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        results[idx] = future.result()
                        processed += 1

                        # Progress callback
                        if processed % 10 == 0:
                            logger.info(f"Processed {processed}/{total_items} items")

                    except Exception as e:
                        logger.error(f"Error processing item at index {idx}: {e}")
                        results[idx] = None

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        cache_stats = self._memory_cache.get_stats()

        # Calculate operation statistics
        operation_stats = {}
        for func_name, stats in self._operation_timings.items():
            if stats['count'] > 0:
                operation_stats[func_name] = {
                    'count': stats['count'],
                    'avg_time': stats['total_time'] / stats['count'],
                    'max_time': stats['max_time'],
                    'min_time': stats['min_time'],
                    'cache_hit_rate': stats['cache_hits'] / stats['count'],
                    'error_rate': stats['errors'] / stats['count']
                }

        return {
            'cache': {
                **cache_stats,
                'hit_rate': self._cache_stats['hits'] / max(1, self._cache_stats['hits'] + self._cache_stats['misses'])
            },
            'operations': operation_stats,
            'slow_operations': len(self._slow_operations),
            'total_operations': self._operation_count
        }

    def clear_cache(self, partial: float = None):
        """Clear cache with optional partial clearing"""
        if partial and 0 < partial < 1:
            # Clear only a portion of the cache
            current_size = len(self._memory_cache.cache)
            items_to_remove = int(current_size * partial)

            # Remove oldest items
            for _ in range(items_to_remove):
                if self._memory_cache.cache:
                    self._memory_cache.cache.popitem(last=False)

            logger.info(f"Cleared {items_to_remove} items from cache")
        else:
            # Clear everything
            self._memory_cache.clear()
            self._cache_stats = {"hits": 0, "misses": 0, "evictions": 0}

            # Clear disk cache if enabled
            if self.config.enable_disk_cache:
                self._clear_disk_cache()

    def _clear_disk_cache(self):
        """Clear disk cache"""
        try:
            for file in os.listdir(self.config.cache_dir):
                if file.endswith('.pkl'):
                    os.remove(os.path.join(self.config.cache_dir, file))
        except Exception as e:
            logger.error(f"Error clearing disk cache: {e}")


# Singleton instance getter
_optimizer_instance = None


def get_performance_optimizer(config: Optional[CacheConfig] = None) -> EnhancedPerformanceOptimizer:
    """Get or create the performance optimizer instance"""
    global _optimizer_instance

    # If config is provided and we need a different instance
    if config is not None:
        # Always create new instance with specific config for testing
        return EnhancedPerformanceOptimizer(config)

    # Otherwise use singleton
    if _optimizer_instance is None:
        _optimizer_instance = EnhancedPerformanceOptimizer()

    return _optimizer_instance