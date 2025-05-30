
# Lazy loading utilities to improve startup time
class LazyImport:
    """Lazy import to avoid loading modules until needed"""
    def __init__(self, module_name):
        self.module_name = module_name
        self._module = None

    def __getattr__(self, name):
        if self._module is None:
            self._module = __import__(self.module_name, fromlist=[name])
        return getattr(self._module, name)

# Lazy imports for optional modules
statcast = LazyImport('statcast_integration')
vegas = LazyImport('vegas_lines')
confirmed = LazyImport('confirmed_lineups')
