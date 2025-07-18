#!/usr/bin/env python3
"""
Clear the confirmation system cache
Run this if confirmations are stuck on old data
"""

import os
import shutil
from datetime import datetime


def clear_confirmation_cache():
    """Clear all confirmation system caches"""
    print("🧹 CLEARING CONFIRMATION CACHE")
    print("=" * 50)

    # Common cache directories
    cache_dirs = [
        ".gui_cache",
        ".cache",
        "__pycache__",
        "cache"
    ]

    cleared = 0

    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ Cleared: {cache_dir}")
                cleared += 1
            except Exception as e:
                print(f"❌ Failed to clear {cache_dir}: {e}")

    # Clear any .json cache files
    for file in os.listdir('.'):
        if file.endswith('_cache.json') or 'confirmations_' in file:
            try:
                os.remove(file)
                print(f"✅ Removed: {file}")
                cleared += 1
            except Exception as e:
                print(f"❌ Failed to remove {file}: {e}")

    print(f"\n📊 Cleared {cleared} cache items")
    print("🔄 Cache will be rebuilt on next run")


if __name__ == "__main__":
    clear_confirmation_cache()