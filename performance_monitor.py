#!/usr/bin/env python3
"""
PERFORMANCE MONITOR FOR DFS OPTIMIZER
====================================
Monitors and reports on optimization performance
"""

import time
import psutil
import os
from datetime import datetime
from typing import Dict, Any


class PerformanceMonitor:
    """Monitor DFS optimizer performance"""

    def __init__(self):
        self.start_time = None
        self.metrics = {}
        self.process = psutil.Process(os.getpid())

    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        self.metrics['start_memory'] = self.process.memory_info().rss / 1024 / 1024  # MB
        self.metrics['start_cpu'] = self.process.cpu_percent()
        print("🔍 Performance monitoring started...")

    def checkpoint(self, name: str):
        """Record a performance checkpoint"""
        if not self.start_time:
            return

        elapsed = time.time() - self.start_time
        memory = self.process.memory_info().rss / 1024 / 1024

        self.metrics[name] = {
            'elapsed': elapsed,
            'memory_mb': memory,
            'memory_delta': memory - self.metrics['start_memory']
        }

        print(f"⏱️  {name}: {elapsed:.1f}s, Memory: {memory:.1f}MB (+{memory - self.metrics['start_memory']:.1f}MB)")

    def stop_monitoring(self):
        """Stop monitoring and show report"""
        total_time = time.time() - self.start_time
        final_memory = self.process.memory_info().rss / 1024 / 1024

        print("\n📊 PERFORMANCE REPORT")
        print("=" * 50)
        print(f"Total time: {total_time:.1f}s")
        print(f"Memory usage: {self.metrics['start_memory']:.1f}MB → {final_memory:.1f}MB")
        print(f"Memory increase: {final_memory - self.metrics['start_memory']:.1f}MB")

        # Show checkpoints
        if len(self.metrics) > 2:
            print("\nCheckpoints:")
            for name, data in self.metrics.items():
                if isinstance(data, dict) and 'elapsed' in data:
                    print(f"  {name}: {data['elapsed']:.1f}s")

        # Performance tips
        self.show_performance_tips()

    def show_performance_tips(self):
        """Show performance optimization tips"""
        print("\n💡 Performance Tips:")

        total_time = time.time() - self.start_time

        if total_time > 30:
            print("  - Optimization took >30s. Consider:")
            print("    • Reduce player pool size with filters")
            print("    • Use cached data when possible")
            print("    • Enable player pre-filtering")

        memory_increase = self.process.memory_info().rss / 1024 / 1024 - self.metrics['start_memory']
        if memory_increase > 100:
            print("  - High memory usage detected. Consider:")
            print("    • Clear cache between optimizations")
            print("    • Reduce batch sizes")
            print("    • Process players in smaller chunks")


# Decorator for timing functions
def time_function(func):
    """Decorator to time function execution"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"⏱️  {func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper


# Usage example
if __name__ == "__main__":
    monitor = PerformanceMonitor()
    monitor.start_monitoring()

    # Simulate some work
    time.sleep(1)
    monitor.checkpoint("Data loading")

    time.sleep(2)
    monitor.checkpoint("Optimization")

    monitor.stop_monitoring()
