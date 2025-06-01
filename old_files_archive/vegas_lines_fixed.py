#!/usr/bin/env python3
"""
Vegas Lines Wrapper - Ensures VegasLines class is available
"""

# Try to import from the existing vegas_lines module
try:
    import sys
    import os
    from pathlib import Path

    # Import the existing vegas_lines content
    current_dir = Path(__file__).parent
    vegas_file = current_dir / "vegas_lines.py"

    if vegas_file.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("vegas_lines_orig", vegas_file)
        vegas_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vegas_module)

        # Check if VegasLines class exists
        if hasattr(vegas_module, 'VegasLines'):
            VegasLines = vegas_module.VegasLines
        else:
            # Create a simple fallback VegasLines class
            class VegasLines:
                def __init__(self, cache_dir="data/vegas", verbose=False):
                    self.cache_dir = cache_dir
                    self.verbose = verbose
                    self.lines = {}

                def get_vegas_lines(self, force_refresh=False):
                    if self.verbose:
                        print("⚠️ Using fallback Vegas integration")
                    return {}

                def apply_to_players(self, players):
                    if self.verbose:
                        print("⚠️ Vegas lines not available")
                    return players
    else:
        # Create fallback class
        class VegasLines:
            def __init__(self, cache_dir="data/vegas", verbose=False):
                self.cache_dir = cache_dir
                self.verbose = verbose
                self.lines = {}

            def get_vegas_lines(self, force_refresh=False):
                if self.verbose:
                    print("⚠️ Vegas lines file not found")
                return {}

            def apply_to_players(self, players):
                return players

except Exception as e:
    print(f"⚠️ Vegas lines error: {e}")

    # Ultimate fallback
    class VegasLines:
        def __init__(self, cache_dir="data/vegas", verbose=False):
            self.cache_dir = cache_dir
            self.verbose = verbose
            self.lines = {}

        def get_vegas_lines(self, force_refresh=False):
            return {}

        def apply_to_players(self, players):
            return players

print("✅ Vegas lines wrapper loaded")
