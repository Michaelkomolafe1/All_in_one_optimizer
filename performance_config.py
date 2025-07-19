#!/usr/bin/env python3
"""
PERFORMANCE CONFIGURATION
========================
Centralized performance settings for DFS optimizer
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PerformanceSettings:
    """Performance optimization settings"""

    # Batch processing
    batch_sizes: Dict[str, int] = None

    # Parallel processing
    max_workers: Dict[str, int] = None

    # Caching
    cache_settings: Dict[str, Any] = None

    # API rate limiting
    api_delays: Dict[str, float] = None

    # Timeouts
    timeouts: Dict[str, int] = None

    def __post_init__(self):
        if self.batch_sizes is None:
            self.batch_sizes = {
                'statcast': 20,      # Players per Statcast batch
                'vegas': 50,         # Teams per Vegas request
                'confirmation': 30,  # Players per confirmation batch
                'scoring': 50,       # Players per scoring batch
                'enrichment': 25     # Players per enrichment batch
            }

        if self.max_workers is None:
            self.max_workers = {
                'statcast': 5,       # Concurrent Statcast requests
                'enrichment': 8,     # Concurrent enrichment workers
                'scoring': 10,       # Concurrent scoring calculations
                'general': 4         # General thread pool size
            }

        if self.cache_settings is None:
            self.cache_settings = {
                'memory_cache_size': 50000,  # Max items in memory
                'disk_cache_enabled': True,
                'cache_ttl': {
                    'statcast': 7200,    # 2 hours
                    'vegas': 600,        # 10 minutes
                    'scores': 300,       # 5 minutes
                    'lineups': 1800      # 30 minutes
                },
                'use_compression': True  # Compress disk cache
            }

        if self.api_delays is None:
            self.api_delays = {
                'statcast': 0.1,     # Delay between Statcast calls
                'vegas': 0.05,       # Delay between Vegas calls
                'confirmation': 0.0   # No delay for confirmation
            }

        if self.timeouts is None:
            self.timeouts = {
                'api_call': 30,      # API call timeout
                'optimization': 60,   # MILP optimization timeout
                'enrichment': 120    # Total enrichment timeout
            }


# Global instance
PERFORMANCE_SETTINGS = PerformanceSettings()


def get_performance_settings():
    """Get global performance settings"""
    return PERFORMANCE_SETTINGS
