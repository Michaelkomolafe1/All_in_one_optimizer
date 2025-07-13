#!/usr/bin/env python3
"""
PERFORMANCE OPTIMIZER - Efficient Data Processing for DFS Optimizer
==================================================================
Handles caching, batch processing, and lazy evaluation to improve performance.
"""

import hashlib
import logging
import os
import pickle
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration"""
    max_size: int = 10000
    ttl_seconds: Dict[str, int] = field(default_factory=lambda: {
        'player_scores': 300,      # 5 minutes
        'api_calls': 3600,         # 1 hour
        'statcast': 7200,          # 2 hours
        'vegas': 600,              # 10 minutes
        'recent_form': 900,        # 15 minutes
        'lineup_correlation': 1800  # 30 minutes
    })
    enable_disk_cache: bool = True
    cache_dir: str = ".dfs_cache"


class PerformanceOptimizer:
    """Handles performance optimization for DFS calculations"""

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._memory_cache = {}
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
        self._processing_times = []

        # Create cache directory if needed
        if self.config.enable_disk_cache:
            os.makedirs(self.config.cache_dir, exist_ok=True)

    def cached(self, category: str = 'default', key_func: Optional[Callable] = None):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self._generate_cache_key(func.__name__, args, kwargs)

                cache_key = f"{category}:{cache_key}"

                # Check cache
                cached_result = self._get_from_cache(cache_key, category)
                if cached_result is not None:
                    self._cache_stats['hits'] += 1
                    return cached_result

                # Cache miss - compute result
                self._cache_stats['misses'] += 1
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Store in cache
                self._store_in_cache(cache_key, result, category)

                # Track performance
                self._processing_times.append({
                    'function': func.__name__,
                    'category': category,
                    'elapsed': elapsed,
                    'timestamp': datetime.now()
                })

                return result

            return wrapper
        return decorator

    def batch_process(self, items: List[Any], 
                     process_func: Callable,
                     batch_size: int = 50,
                     max_workers: int = 4) -> List[Any]:
        """Process items in batches for efficiency"""
        results = []
        total_items = len(items)

        logger.info(f"Batch processing {total_items} items in batches of {batch_size}")

        # Process in batches
        for i in range(0, total_items, batch_size):
            batch = items[i:i + batch_size]
            batch_results = self._process_batch(batch, process_func, max_workers)
            results.extend(batch_results)

            # Log progress
            processed = min(i + batch_size, total_items)
            logger.debug(f"Processed {processed}/{total_items} items")

        return results

    def _process_batch(self, batch: List[Any], 
                      process_func: Callable,
                      max_workers: int) -> List[Any]:
        """Process a single batch with threading"""
        results = [None] * len(batch)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(process_func, item): i 
                for i, item in enumerate(batch)
            }

            # Collect results
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    logger.error(f"Error processing item {index}: {e}")
                    results[index] = None

        return results

    def lazy_calculate(self, player: Any, calculation_func: Callable) -> 'LazyCalculator':
        """Create a lazy calculator for deferred computation"""
        return LazyCalculator(player, calculation_func, self)

    def optimize_player_pool(self, players: List[Any], 
                           enrichment_funcs: List[Callable]) -> List[Any]:
        """Optimize enrichment of player pool"""
        logger.info(f"Optimizing enrichment for {len(players)} players")

        # Sort players by priority (higher projection = higher priority)
        sorted_players = sorted(
            players, 
            key=lambda p: getattr(p, 'base_projection', 0), 
            reverse=True
        )

        # Track which enrichments each player needs
        enrichment_needed = {}
        for player in sorted_players:
            needed = []

            # Check what enrichments are needed
            if not hasattr(player, '_enrichment_complete'):
                player._enrichment_complete = set()

            for func in enrichment_funcs:
                func_name = func.__name__
                if func_name not in player._enrichment_complete:
                    needed.append(func)

            if needed:
                enrichment_needed[getattr(player, 'id', player.name)] = needed

        # Batch process enrichments by type
        for func in enrichment_funcs:
            # Get players needing this enrichment
            players_needing = [
                p for p in sorted_players 
                if getattr(p, 'id', p.name) in enrichment_needed and func in enrichment_needed[getattr(p, 'id', p.name)]
            ]

            if not players_needing:
                continue

            logger.info(f"Applying {func.__name__} to {len(players_needing)} players")

            # Process in batches
            enriched = self.batch_process(
                players_needing,
                func,
                batch_size=50
            )

            # Mark as complete
            for player in players_needing:
                if hasattr(player, '_enrichment_complete'):
                    player._enrichment_complete.add(func.__name__)

        return sorted_players

    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function and arguments"""
        # Create a string representation
        key_parts = [func_name]

        # Handle args
        for arg in args:
            if hasattr(arg, 'id'):
                key_parts.append(f"id:{arg.id}")
            elif hasattr(arg, 'name'):
                key_parts.append(f"name:{arg.name}")
            elif isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                key_parts.append(str(type(arg).__name__))

        # Handle kwargs
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")

        # Create hash
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_from_cache(self, key: str, category: str) -> Optional[Any]:
        """Get value from cache"""
        # Check memory cache first
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            ttl = self.config.ttl_seconds.get(category, 300)

            if datetime.now() - entry['timestamp'] < timedelta(seconds=ttl):
                return entry['data']
            else:
                # Expired - remove from cache
                del self._memory_cache[key]
                self._cache_stats['evictions'] += 1

        # Check disk cache if enabled
        if self.config.enable_disk_cache:
            return self._get_from_disk_cache(key, category)

        return None

    def _store_in_cache(self, key: str, data: Any, category: str):
        """Store value in cache"""
        # Check cache size limit
        if len(self._memory_cache) >= self.config.max_size:
            # Evict oldest entries
            self._evict_oldest(self.config.max_size // 10)

        # Store in memory
        self._memory_cache[key] = {
            'data': data,
            'timestamp': datetime.now(),
            'category': category
        }

        # Store on disk if enabled
        if self.config.enable_disk_cache:
            self._store_in_disk_cache(key, data, category)

    def _evict_oldest(self, count: int):
        """Evict oldest cache entries"""
        if not self._memory_cache:
            return

        # Sort by timestamp
        sorted_keys = sorted(
            self._memory_cache.keys(),
            key=lambda k: self._memory_cache[k]['timestamp']
        )

        # Remove oldest
        for key in sorted_keys[:count]:
            del self._memory_cache[key]
            self._cache_stats['evictions'] += 1

    def _get_from_disk_cache(self, key: str, category: str) -> Optional[Any]:
        """Get from disk cache"""
        cache_file = os.path.join(self.config.cache_dir, f"{key}.pkl")

        if not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file, 'rb') as f:
                entry = pickle.load(f)

            ttl = self.config.ttl_seconds.get(category, 300)
            if datetime.now() - entry['timestamp'] < timedelta(seconds=ttl):
                return entry['data']
            else:
                # Expired - remove file
                os.remove(cache_file)

        except Exception as e:
            logger.error(f"Error reading disk cache: {e}")

        return None

    def _store_in_disk_cache(self, key: str, data: Any, category: str):
        """Store in disk cache"""
        cache_file = os.path.join(self.config.cache_dir, f"{key}.pkl")

        try:
            entry = {
                'data': data,
                'timestamp': datetime.now(),
                'category': category
            }

            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)

        except Exception as e:
            logger.error(f"Error writing disk cache: {e}")

    def clear_cache(self, category: Optional[str] = None):
        """Clear cache (optionally by category)"""
        if category:
            # Clear specific category
            keys_to_remove = [
                k for k, v in self._memory_cache.items()
                if v.get('category') == category
            ]
            for key in keys_to_remove:
                del self._memory_cache[key]
        else:
            # Clear all
            self._memory_cache.clear()

        # Clear disk cache
        if self.config.enable_disk_cache:
            try:
                import shutil
                shutil.rmtree(self.config.cache_dir)
                os.makedirs(self.config.cache_dir)
            except:
                pass

        logger.info(f"Cleared cache for category: {category or 'all'}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        hit_rate = self._cache_stats['hits'] / max(
            self._cache_stats['hits'] + self._cache_stats['misses'], 1
        )

        # Calculate average processing times
        avg_times = {}
        if self._processing_times:
            from itertools import groupby
            sorted_times = sorted(self._processing_times, key=lambda x: x['function'])

            for func_name, times in groupby(sorted_times, key=lambda x: x['function']):
                times_list = list(times)
                avg_times[func_name] = sum(t['elapsed'] for t in times_list) / len(times_list)

        return {
            'cache_stats': self._cache_stats,
            'cache_hit_rate': hit_rate,
            'cache_size': len(self._memory_cache),
            'average_processing_times': avg_times,
            'total_processing_calls': len(self._processing_times)
        }


class LazyCalculator:
    """Lazy calculation wrapper for deferred computation"""

    def __init__(self, obj: Any, calc_func: Callable, optimizer: PerformanceOptimizer):
        self._obj = obj
        self._calc_func = calc_func
        self._optimizer = optimizer
        self._result = None
        self._calculated = False

    @property
    def value(self) -> Any:
        """Get calculated value (calculates on first access)"""
        if not self._calculated:
            # Use caching if available
            cache_key = f"lazy:{id(self._obj)}:{self._calc_func.__name__}"

            cached = self._optimizer._get_from_cache(cache_key, 'lazy')
            if cached is not None:
                self._result = cached
            else:
                self._result = self._calc_func(self._obj)
                self._optimizer._store_in_cache(cache_key, self._result, 'lazy')

            self._calculated = True

        return self._result

    def invalidate(self):
        """Invalidate the calculated value"""
        self._calculated = False
        self._result = None


# Global optimizer instance
_optimizer_instance = None

def get_performance_optimizer(config: Optional[CacheConfig] = None) -> PerformanceOptimizer:
    """Get or create global performance optimizer"""
    global _optimizer_instance

    if _optimizer_instance is None:
        _optimizer_instance = PerformanceOptimizer(config)
    elif config is not None:
        _optimizer_instance.config = config

    return _optimizer_instance
