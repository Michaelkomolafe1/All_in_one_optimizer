"""Performance profiler stub for DFS Optimizer"""

def profile_function(func):
    """Decorator that returns function unchanged (no profiling)"""
    return func

class PerformanceTimer:
    """Stub timer class"""
    def __init__(self, name="Operation"):
        self.name = name
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

# Create a profiler object that the GUI is looking for
class Profiler:
    """Simple profiler class"""
    def __init__(self):
        pass
    
    def profile(self, func):
        return func

# Create the profiler instance that's being imported
profiler = Profiler()
