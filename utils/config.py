#!/usr/bin/env python3
"""Configuration Management for DFS Optimizer"""

import os
import json
from typing import Dict, Any

class Config:
    """Centralized configuration management"""

    DEFAULT_CONFIG = {
        'salary_cap': 50000,
        'max_workers': 5,
        'cache_expiry_hours': {
            'statcast': 6,
            'vegas': 2,
            'lineups': 1,
            'dff': 24
        },
        'api_keys': {
            'odds_api': os.getenv('ODDS_API_KEY', '14b669db87ed65f1d0f3e70a90386707')
        },
        'optimization': {
            'max_pool_size': 150,
            'min_projection': 5.0,
            'diversity_factor': 0.7,
            'multi_lineup_count': 20
        },
        'data_sources': {
            'use_statcast': True,
            'use_vegas': True,
            'use_dff': True,
            'use_confirmations': True
        }
    }

    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """Load configuration from file or use defaults"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    return self._deep_merge(self.DEFAULT_CONFIG.copy(), user_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")

        return self.DEFAULT_CONFIG.copy()

    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def get(self, key: str, default=None):
        """Get config value with dot notation support"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set config value"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        self.save_config()

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")

# Global config instance
config = Config()
