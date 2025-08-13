#!/usr/bin/env python3
"""
Simple Statcast Fetcher - Minimal Implementation
"""

import logging

logger = logging.getLogger(__name__)


class SimpleStatcastFetcher:
    """Minimal Statcast fetcher for testing"""

    def __init__(self):
        """Initialize fetcher"""
        self.enabled = False
        logger.info("SimpleStatcastFetcher initialized (minimal mode)")

    def get_batter_stats(self, player_name):
        """Wrapper method for compatibility"""
        # Check if other methods exist
        if hasattr(self, 'get_player_stats'):
            return self.get_player_stats(player_name)

        # Return default stats
        return {
            'barrel%': 8.5,
            'xwoba': 0.320,
            'hard_hit%': 40.0
        }

    def get_player_stats(self, player_name: str) -> dict:
        """Get player stats (returns empty for now)"""
        return {}

    def get_recent_performance(self, player_name: str, days: int = 7) -> float:
        """Get recent performance multiplier"""
        return 1.0

    def get_barrel_rate(self, player_name: str) -> float:
        """Get barrel rate"""
        return 0.0
