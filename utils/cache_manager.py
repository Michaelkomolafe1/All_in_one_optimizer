#!/usr/bin/env python3
"""
Unified Cache Manager - Replaces multiple scattered cache systems
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Callable

class UnifiedCacheManager:
    """Single cache manager for all data types"""

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

        # Cache expiry times (hours)
        self.expiry_times = {
            'statcast': 6,
            'vegas': 2, 
            'lineups': 1,
            'dff': 24,
            'performance': 12
        }

    def get_cache_path(self, category: str, key: str) -> str:
        """Get file path for cache entry"""
        safe_key = key.replace(' ', '_').replace('/', '_')
        return os.path.join(self.cache_dir, f"{category}_{safe_key}.json")

    def is_expired(self, category: str, key: str) -> bool:
        """Check if cache entry is expired"""
        cache_path = self.get_cache_path(category, key)

        if not os.path.exists(cache_path):
            return True

        # Check file age
        file_time = os.path.getmtime(cache_path)
        age_hours = (time.time() - file_time) / 3600
        expiry_hours = self.expiry_times.get(category, 6)

        return age_hours > expiry_hours

    def get(self, category: str, key: str, fetch_func: Callable = None, 
            force_refresh: bool = False) -> Optional[Any]:
        """Get data from cache or fetch fresh"""

        if not force_refresh and not self.is_expired(category, key):
            try:
                cache_path = self.get_cache_path(category, key)
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    data['_cache_source'] = 'cache'
                    return data
            except Exception as e:
                print(f"Cache read error for {category}:{key}: {e}")

        # Fetch fresh data if available
        if fetch_func:
            try:
                fresh_data = fetch_func()
                if fresh_data:
                    self.set(category, key, fresh_data)
                    fresh_data['_cache_source'] = 'fresh'
                    return fresh_data
            except Exception as e:
                print(f"Fresh fetch error for {category}:{key}: {e}")

        return None

    def set(self, category: str, key: str, data: Any) -> bool:
        """Store data in cache"""
        try:
            cache_path = self.get_cache_path(category, key)

            # Add metadata
            cache_data = dict(data) if isinstance(data, dict) else data
            if isinstance(cache_data, dict):
                cache_data['_cached_at'] = datetime.now().isoformat()
                cache_data['_category'] = category

            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)

            return True
        except Exception as e:
            print(f"Cache write error for {category}:{key}: {e}")
            return False

    def clear_category(self, category: str) -> int:
        """Clear all cache entries for a category"""
        cleared = 0
        for filename in os.listdir(self.cache_dir):
            if filename.startswith(f"{category}_"):
                try:
                    os.remove(os.path.join(self.cache_dir, filename))
                    cleared += 1
                except Exception as e:
                    print(f"Error clearing {filename}: {e}")

        return cleared

    def clear_all(self) -> int:
        """Clear entire cache"""
        cleared = 0
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                try:
                    os.remove(os.path.join(self.cache_dir, filename))
                    cleared += 1
                except Exception as e:
                    print(f"Error clearing {filename}: {e}")

        return cleared

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        stats = {'total_files': 0, 'categories': {}, 'total_size_mb': 0}

        if not os.path.exists(self.cache_dir):
            return stats

        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                stats['total_files'] += 1

                # Get category from filename
                category = filename.split('_')[0]
                if category not in stats['categories']:
                    stats['categories'][category] = 0
                stats['categories'][category] += 1

                # Get file size
                file_path = os.path.join(self.cache_dir, filename)
                stats['total_size_mb'] += os.path.getsize(file_path) / (1024 * 1024)

        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        return stats

# Global cache instance
cache = UnifiedCacheManager()
