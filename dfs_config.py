#!/usr/bin/env python3
"""
DFS Configuration Management System
==================================
Centralized configuration for all DFS optimizer settings
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class DFSConfig:
    """Configuration manager for DFS optimizer"""

    def __init__(self, config_file: str = 'dfs_config.json'):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration with sensible defaults"""
        defaults = {
            "optimization": {
                "max_form_analysis_players": None,  # None = analyze all
                "parallel_workers": 10,
                "batch_size": 25,
                "cache_enabled": True,
                "salary_cap": 50000,
                "min_salary_usage": 0.95  # Use at least 95% of salary cap
            },
            "data_sources": {
                "statcast": {
                    "enabled": True,
                    "priority": 1,
                    "cache_hours": 6,
                    "batch_size": 20
                },
                "vegas": {
                    "enabled": True,
                    "priority": 2,
                    "cache_hours": 1,
                    "min_total_deviation": 1.0  # Only apply if game total differs by 1+ run
                },
                "recent_form": {
                    "enabled": True,
                    "priority": 3,
                    "days_back": 7,
                    "min_games": 3,
                    "cache_hours": 6
                },
                "dff": {
                    "enabled": True,
                    "priority": 4,
                    "auto_detect": True
                },
                "batting_order": {
                    "enabled": True,
                    "priority": 5
                }
            },
            "api_limits": {
                "pybaseball_delay": 0.5,
                "max_retries": 3,
                "timeout": 30,
                "rate_limit_per_minute": 60
            },
            "player_filtering": {
                "min_salary": 2000,
                "exclude_injured": True,
                "require_confirmation": True,
                "min_games_played": 5
            },
            "output": {
                "show_progress": True,
                "verbose_logging": False,
                "export_format": "csv",
                "save_lineups": True
            }
        }

        # Try to load user config
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    return self._deep_merge(defaults, user_config)
            except Exception as e:
                print(f"⚠️ Error loading config file: {e}")
                print("   Using default configuration")

        # Save defaults if no config exists
        self._save_config(defaults)
        return defaults

    def _deep_merge(self, default: Dict, update: Dict) -> Dict:
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self._deep_merge(default[key], value)
            else:
                default[key] = value
        return default

    def _save_config(self, config: Dict):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"⚠️ Could not save config: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get config value using dot notation (e.g., 'optimization.batch_size')"""
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """Set config value using dot notation"""
        keys = key_path.split('.')
        config = self.config

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the value
        config[keys[-1]] = value

        # Save updated config
        self._save_config(self.config)

    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()


# Global config instance
dfs_config = DFSConfig()