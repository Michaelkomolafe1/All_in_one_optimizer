#!/usr/bin/env python3
"""
DFS Configuration Management System - Updated to use Unified Config
==================================================================
Now uses the unified configuration manager as the backend
"""

from typing import Any, Dict
from unified_config_manager import get_config_manager


class DFSConfig:
    """Configuration manager for DFS optimizer - now wraps unified config"""

    def __init__(self, config_file: str = "dfs_unified_config.json"):
        self.config_manager = get_config_manager(config_file)
        # For backward compatibility
        self.config_file = config_file
        self.config = self._get_legacy_format()

    def get_form_analysis_limit(self):
        """Get player limit for form analysis - None means no limit"""
        limit = self.config_manager.get("optimization.max_form_analysis_players", None)
        if limit is None:
            print("📊 Form analysis will process ALL players (no limit set)")
        else:
            print(f"📊 Form analysis limited to {limit} players")
        return limit

    def _get_legacy_format(self) -> Dict[str, Any]:
        """Get config in legacy format for backward compatibility"""
        # Build legacy structure from unified config
        return {
            "optimization": {
                "max_form_analysis_players": self.config_manager.get("optimization.max_form_analysis_players"),
                "parallel_workers": self.config_manager.get("optimization.parallel_workers", 10),
                "batch_size": self.config_manager.get("optimization.batch_size", 25),
                "cache_enabled": self.config_manager.get("performance.cache_enabled", True),
                "salary_cap": self.config_manager.get("optimization.salary_cap", 50000),
                "min_salary_usage": self.config_manager.get("optimization.min_salary_usage", 0.95),
            },
            "data_sources": self.config_manager.config.data_sources.__dict__,
            "api_limits": {
                "pybaseball_delay": self.config_manager.get("api.pybaseball_delay", 0.5),
                "max_retries": self.config_manager.get("api.max_retries", 3),
                "timeout": self.config_manager.get("api.timeout", 30),
                "rate_limit_per_minute": self.config_manager.get("api.rate_limit_per_minute", 60),
            },
            "player_filtering": {
                "min_salary": self.config_manager.get("validation.player_salary_min", 2000),
                "exclude_injured": True,
                "require_confirmation": True,
                "min_games_played": 5,
            },
            "output": {
                "show_progress": self.config_manager.get("ui.show_progress", True),
                "verbose_logging": self.config_manager.get("ui.verbose_logging", False),
                "export_format": self.config_manager.get("ui.export_format", "csv"),
                "save_lineups": self.config_manager.get("ui.save_lineups", True),
            },
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get config value using dot notation (e.g., 'optimization.batch_size')"""
        # First try unified config format
        value = self.config_manager.get(key_path, None)
        if value is not None:
            return value

        # Fall back to legacy format
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """Set config value using dot notation"""
        self.config_manager.set(key_path, value)
        # Update legacy format
        self.config = self._get_legacy_format()

    def reload(self):
        """Reload configuration from file"""
        # Unified config manager handles this internally
        self.config = self._get_legacy_format()


# Global config instance - backward compatible
dfs_config = DFSConfig()

# For new code, prefer using unified config directly:
# from unified_config_manager import get_config_value
# value = get_config_value('optimization.salary_cap')