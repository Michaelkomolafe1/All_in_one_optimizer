"""Cache manager for DFS optimizer"""

class DataCache:
    """Simple cache implementation"""
    def __init__(self):
        self.cache = {}

    def get(self, key, default=None):
        return self.cache.get(key, default)

    def set(self, key, value):
        self.cache[key] = value
        return True

    def clear(self):
        self.cache.clear()

# Global instance
cache = DataCache()
