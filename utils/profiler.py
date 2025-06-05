#!/usr/bin/env python3
"""Performance Profiler for DFS Optimizer"""

import time
import functools
from typing import Dict, List

class PerformanceProfiler:
    def __init__(self):
        self.timings = {}

    def profile(self, name: str = None):
        """Decorator to profile function execution time"""
        def decorator(func):
            func_name = name or f"{func.__module__}.{func.__name__}"

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start

                if func_name not in self.timings:
                    self.timings[func_name] = []
                self.timings[func_name].append(duration)

                return result
            return wrapper
        return decorator

    def get_report(self) -> Dict:
        """Get performance report"""
        report = {}
        for func_name, times in self.timings.items():
            if times:
                report[func_name] = {
                    'calls': len(times),
                    'total': sum(times),
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times)
                }
        return report

    def reset(self):
        """Reset all timings"""
        self.timings.clear()

# Global profiler instance
profiler = PerformanceProfiler()
