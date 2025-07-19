#!/usr/bin/env python3
"""
UNIFIED CONFIGURATION MANAGER - Single source of truth for all settings
=====================================================================
Consolidates all configuration into one manageable system
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ScoringConfig:
    """Scoring engine configuration"""
    weights: Dict[str, float] = field(default_factory=lambda: {
        "base": 0.30,
        "recent_form": 0.25,
        "vegas": 0.20,
        "matchup": 0.20,
        "park_batting": 0.05
    })

    bounds: Dict[str, List[float]] = field(default_factory=lambda: {
        "base": [1.0, 1.0],
        "recent_form": [0.7, 1.3],
        "vegas": [0.85, 1.25],
        "matchup": [0.8, 1.2],
        "park_batting": [0.95, 1.05],
        "final": [0.65, 1.35]  # ±35% max total
    })

    validation: Dict[str, float] = field(default_factory=lambda: {
        "min_projection": 0.0,
        "max_projection": 60.0,
        "min_multiplier": 0.1,
        "max_multiplier": 10.0
    })


@dataclass
class OptimizationConfig:
    """Optimization settings"""
    salary_cap: int = 50000
    min_salary_usage: float = 0.95
    max_players_per_team: int = 4
    min_players_per_team: int = 0
    preferred_stack_size: int = 3
    max_hitters_vs_pitcher: int = 4
    correlation_boost: float = 0.05
    timeout_seconds: int = 30
    use_correlation: bool = True
    enforce_lineup_rules: bool = True

    # Form analysis
    max_form_analysis_players: Optional[int] = None
    parallel_workers: int = 10
    batch_size: int = 25


@dataclass
class DataSourceConfig:
    """Data source configurations"""
    statcast: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "priority": 1,
        "cache_hours": 6,
        "batch_size": 20
    })

    vegas: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "priority": 2,
        "cache_hours": 1,
        "min_total_deviation": 1.0
    })

    recent_form: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "priority": 3,
        "days_back": 7,
        "min_games": 3,
        "cache_hours": 6
    })

    dff: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "priority": 4,
        "auto_detect": True
    })

    batting_order: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "priority": 5
    })


@dataclass
class APIConfig:
    """API rate limiting and timeout settings"""
    pybaseball_delay: float = 0.5
    max_retries: int = 3
    timeout: int = 30
    rate_limit_per_minute: int = 60


@dataclass
class ValidationConfig:
    """Validation rules"""
    player_salary_min: int = 2000
    player_salary_max: int = 15000
    projection_min: float = 0.0
    projection_max: float = 60.0
    ownership_min: float = 0.0
    ownership_max: float = 100.0
    valid_teams: List[str] = field(default_factory=lambda: [
        "ARI", "ATL", "BAL", "BOS", "CHC", "CHW", "CIN", "CLE",
        "COL", "DET", "HOU", "KC", "LAA", "LAD", "MIA", "MIL",
        "MIN", "NYM", "NYY", "OAK", "PHI", "PIT", "SD", "SF",
        "SEA", "STL", "TB", "TEX", "TOR", "WSH"
    ])
    valid_positions: List[str] = field(default_factory=lambda: [
        "P", "C", "1B", "2B", "3B", "SS", "OF", "DH", "UTIL", "CPT"
    ])


@dataclass
class PerformanceConfig:
    """Performance optimization settings"""
    cache_enabled: bool = True
    cache_ttl: Dict[str, int] = field(default_factory=lambda: {
        "player_scores": 300,
        "api_calls": 3600,
        "statcast": 7200,
        "vegas": 600,
        "recent_form": 900
    })
    enable_disk_cache: bool = True
    cache_dir: str = ".dfs_cache"
    max_memory_mb: int = 100
    max_cache_size: int = 10000


@dataclass
class UIConfig:
    """User interface settings"""
    show_progress: bool = True
    verbose_logging: bool = False
    export_format: str = "csv"
    save_lineups: bool = True
    default_strategy: str = "balanced"
    theme: str = "dark"


@dataclass
class DFSConfig:
    """Complete DFS configuration"""
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    data_sources: DataSourceConfig = field(default_factory=DataSourceConfig)
    api: APIConfig = field(default_factory=APIConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    ui: UIConfig = field(default_factory=UIConfig)

    # Metadata
    version: str = "2.0.0"
    last_updated: Optional[str] = None


class UnifiedConfigManager:
    """Centralized configuration management"""

    _instance: Optional['UnifiedConfigManager'] = None

    def __new__(cls, config_file: str = "dfs_config.json"):
        """Singleton pattern to ensure single config instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_file: str = "dfs_config.json"):
        """Initialize configuration manager"""
        if self._initialized:
            return

        self.config_file = config_file
        self.config = self._load_config()
        self._callbacks = []
        self._initialized = True

        logger.info(f"Configuration manager initialized from {config_file}")

    def _load_config(self) -> DFSConfig:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)

                # Handle nested dataclass creation
                config = DFSConfig()

                # Update with loaded data
                if 'scoring' in data:
                    config.scoring = ScoringConfig(**data['scoring'])
                if 'optimization' in data:
                    config.optimization = OptimizationConfig(**data['optimization'])
                if 'data_sources' in data:
                    config.data_sources = DataSourceConfig(**data['data_sources'])
                if 'api' in data:
                    config.api = APIConfig(**data['api'])
                if 'validation' in data:
                    config.validation = ValidationConfig(**data['validation'])
                if 'performance' in data:
                    config.performance = PerformanceConfig(**data['performance'])
                if 'ui' in data:
                    config.ui = UIConfig(**data['ui'])

                # Update metadata
                config.version = data.get('version', config.version)
                config.last_updated = data.get('last_updated')

                logger.info(f"Loaded configuration from {self.config_file}")
                return config

            except Exception as e:
                logger.error(f"Error loading config: {e}")
                logger.info("Using default configuration")

        # Return default config
        return DFSConfig()

    def save_config(self):
        """Save current configuration to file"""
        try:
            # Convert to dict
            config_dict = {
                'scoring': asdict(self.config.scoring),
                'optimization': asdict(self.config.optimization),
                'data_sources': asdict(self.config.data_sources),
                'api': asdict(self.config.api),
                'validation': asdict(self.config.validation),
                'performance': asdict(self.config.performance),
                'ui': asdict(self.config.ui),
                'version': self.config.version,
                'last_updated': self.config.last_updated or str(datetime.now())
            }

            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)

            logger.info(f"Configuration saved to {self.config_file}")

            # Notify callbacks
            self._notify_callbacks('save')

        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path

        Examples:
            config.get('scoring.weights.base')  # 0.30
            config.get('optimization.salary_cap')  # 50000
        """
        try:
            keys = key_path.split('.')
            value = self.config

            for key in keys:
                if hasattr(value, key):
                    value = getattr(value, key)
                elif isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default

            return value

        except Exception as e:
            logger.warning(f"Error getting config value {key_path}: {e}")
            return default

    def set(self, key_path: str, value: Any):
        """
        Set configuration value by dot-separated path

        Examples:
            config.set('scoring.weights.base', 0.35)
            config.set('optimization.salary_cap', 55000)
        """
        try:
            keys = key_path.split('.')
            target = self.config

            # Navigate to parent
            for key in keys[:-1]:
                if hasattr(target, key):
                    target = getattr(target, key)
                elif isinstance(target, dict) and key in target:
                    target = target[key]
                else:
                    logger.error(f"Invalid config path: {key_path}")
                    return

            # Set the value
            final_key = keys[-1]
            if hasattr(target, final_key):
                setattr(target, final_key, value)
            elif isinstance(target, dict):
                target[final_key] = value

            # Notify callbacks
            self._notify_callbacks('set', key_path, value)

            logger.info(f"Config updated: {key_path} = {value}")

        except Exception as e:
            logger.error(f"Error setting config value {key_path}: {e}")

    def update(self, updates: Dict[str, Any]):
        """Update multiple configuration values"""
        for key_path, value in updates.items():
            self.set(key_path, value)

    def register_callback(self, callback: callable):
        """Register callback for configuration changes"""
        self._callbacks.append(callback)

    def _notify_callbacks(self, event: str, *args):
        """Notify registered callbacks of changes"""
        for callback in self._callbacks:
            try:
                callback(event, *args)
            except Exception as e:
                logger.error(f"Error in config callback: {e}")

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []

        # Validate scoring weights sum to 1.0
        weight_sum = sum(self.config.scoring.weights.values())
        if abs(weight_sum - 1.0) > 0.001:
            issues.append(f"Scoring weights sum to {weight_sum}, not 1.0")

        # Validate bounds
        for component, bounds in self.config.scoring.bounds.items():
            if bounds[0] > bounds[1]:
                issues.append(f"Invalid bounds for {component}: {bounds}")

        # Validate salary settings
        if self.config.optimization.min_salary_usage > 1.0:
            issues.append(f"Invalid min_salary_usage: {self.config.optimization.min_salary_usage}")

        # Validate cache settings
        if self.config.performance.max_cache_size < 100:
            issues.append(f"Cache size too small: {self.config.performance.max_cache_size}")

        return issues

    def export_for_module(self, module_name: str) -> Dict[str, Any]:
        """Export configuration for specific module"""
        module_configs = {
            'scoring_engine': {
                'weights': self.config.scoring.weights,
                'bounds': self.config.scoring.bounds,
                'validation': self.config.scoring.validation
            },
            'optimizer': {
                'salary_cap': self.config.optimization.salary_cap,
                'min_salary_usage': self.config.optimization.min_salary_usage,
                'max_players_per_team': self.config.optimization.max_players_per_team,
                'correlation_boost': self.config.optimization.correlation_boost
            },
            'validator': {
                'salary_range': [self.config.validation.player_salary_min,
                                 self.config.validation.player_salary_max],
                'projection_range': [self.config.validation.projection_min,
                                     self.config.validation.projection_max],
                'valid_teams': self.config.validation.valid_teams,
                'valid_positions': self.config.validation.valid_positions
            },
            'performance': {
                'cache_enabled': self.config.performance.cache_enabled,
                'ttl_seconds': self.config.performance.cache_ttl,
                'max_size': self.config.performance.max_cache_size
            }
        }

        return module_configs.get(module_name, {})

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = DFSConfig()
        self._notify_callbacks('reset')
        logger.info("Configuration reset to defaults")


# Global instance getter
from datetime import datetime


def get_config_manager(config_file: str = "dfs_config.json") -> UnifiedConfigManager:
    """Get the global configuration manager instance"""
    return UnifiedConfigManager(config_file)


# Convenience functions for common operations
def get_config_value(key_path: str, default: Any = None) -> Any:
    """Quick access to configuration values"""
    return get_config_manager().get(key_path, default)


def set_config_value(key_path: str, value: Any):
    """Quick update of configuration values"""
    get_config_manager().set(key_path, value)


# Example usage and migration helper
def migrate_old_configs():
    """Migrate from old configuration files to unified system"""
    manager = get_config_manager()

    # Check for old config files
    old_configs = [
        'dfs_config.json',
        'optimization_config.json',
        'real_data_config.json'
    ]

    for old_file in old_configs:
        if os.path.exists(old_file) and old_file != manager.config_file:
            logger.info(f"Migrating configuration from {old_file}")
            try:
                with open(old_file, 'r') as f:
                    old_data = json.load(f)

                # Map old keys to new structure
                if 'scoring_weights' in old_data:
                    manager.config.scoring.weights = old_data['scoring_weights']

                if 'optimization' in old_data:
                    for key, value in old_data['optimization'].items():
                        if hasattr(manager.config.optimization, key):
                            setattr(manager.config.optimization, key, value)

                # Archive old file
                os.rename(old_file, f"{old_file}.migrated")

            except Exception as e:
                logger.error(f"Error migrating {old_file}: {e}")

    # Save migrated configuration
    manager.save_config()