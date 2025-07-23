#!/usr/bin/env python3
"""
HYBRID SCORING SYSTEM - Contest-Specific Scoring Strategy
========================================================
Automatically selects the best scoring method based on contest type
"""

import logging
from typing import Any, Optional, Dict

# Import both scoring engines
from unified_scoring_engine import get_scoring_engine, ScoringConfig
from enhanced_pure_scoring_engine import get_enhanced_pure_engine, EnhancedPureConfig

logger = logging.getLogger(__name__)


class HybridScoringSystem:
    """
    Hybrid scoring that switches between Dynamic and Enhanced Pure
    based on contest type and slate size
    """

    def __init__(self):
        """Initialize both scoring engines"""
        print("\n🎯 Initializing Hybrid Scoring System...")

        # Initialize Dynamic Scoring Engine (for cash/small GPPs)
        dynamic_config = ScoringConfig(
            weights={
                "base": 0.30,
                "recent_form": 0.25,
                "vegas": 0.20,
                "matchup": 0.20,
                "park": 0.00,  # Handled separately
                "batting_order": 0.05
            },
            bounds={
                "recent_form": (0.70, 1.35),
                "vegas": (0.75, 1.25),
                "matchup": (0.80, 1.25),
                "park": (0.85, 1.15),
                "batting_order": (0.92, 1.10),
                "final": (0.65, 1.40)
            }
        )
        self.dynamic_engine = get_scoring_engine(dynamic_config)
        print("   ✅ Dynamic engine ready (cash/small GPPs)")

        # Initialize Enhanced Pure Engine (for large GPPs)
        enhanced_config = EnhancedPureConfig(
            weights={
                "base": 0.35,
                "recent_form": 0.25,
                "vegas": 0.20,
                "matchup": 0.15,
                "batting_order": 0.05
            }
        )
        self.enhanced_engine = get_enhanced_pure_engine(enhanced_config)
        print("   ✅ Enhanced pure engine ready (large GPPs)")

        # Current active engine
        self.current_engine = None
        self.current_mode = None

        # Data sources
        self.statcast_fetcher = None
        self.vegas_client = None
        self.confirmation_system = None

        print("   ✅ Hybrid system initialized")

    def set_data_sources(self, statcast_fetcher=None, vegas_client=None, confirmation_system=None):
        """Connect data sources to both engines"""
        self.statcast_fetcher = statcast_fetcher
        self.vegas_client = vegas_client
        self.confirmation_system = confirmation_system

        # Pass to both engines
        if hasattr(self.dynamic_engine, 'set_data_sources'):
            self.dynamic_engine.set_data_sources(
                statcast_fetcher=statcast_fetcher,
                vegas_client=vegas_client,
                confirmation_system=confirmation_system
            )

        if hasattr(self.enhanced_engine, 'set_data_sources'):
            self.enhanced_engine.set_data_sources(
                statcast_fetcher=statcast_fetcher,
                vegas_client=vegas_client,
                confirmation_system=confirmation_system
            )

    def get_scoring_method(self, contest_type: str, slate_size: Optional[str] = None) -> str:
        """
        Determine which scoring method to use
        Based on simulation results showing optimal strategies
        """
        # Map slate player count to size category
        if slate_size is None:
            slate_size = 'medium'  # Default
        elif isinstance(slate_size, int):
            if slate_size < 100:
                slate_size = 'small'
            elif slate_size < 200:
                slate_size = 'medium'
            else:
                slate_size = 'large'

        # Apply the strategy from simulation results
        if contest_type == 'cash':
            return 'dynamic'
        elif slate_size in ['small', 'medium']:
            return 'dynamic'
        else:  # Large GPPs
            return 'enhanced_pure'

    def set_contest_type(self, contest_type: str, slate_size: Optional[str] = None):
        """Set the active scoring engine based on contest type"""
        scoring_method = self.get_scoring_method(contest_type, slate_size)

        if scoring_method == 'dynamic':
            self.current_engine = self.dynamic_engine
            self.current_mode = 'dynamic'
            logger.info(f"Switched to DYNAMIC scoring for {contest_type}")
        else:
            self.current_engine = self.enhanced_engine
            self.current_mode = 'enhanced_pure'
            logger.info(f"Switched to ENHANCED PURE scoring for {contest_type}")

        return scoring_method

    def calculate_score(self, player: Any) -> float:
        """Calculate score using the current active engine"""
        if self.current_engine is None:
            # Default to dynamic if not set
            self.set_contest_type('cash')

        return self.current_engine.calculate_score(player)

    def clear_cache(self):
        """Clear both engine caches"""
        self.dynamic_engine.clear_cache()
        self.enhanced_engine.clear_cache()

    def get_engine_stats(self) -> Dict:
        """Get statistics from both engines"""
        return {
            'current_mode': self.current_mode,
            'dynamic_stats': getattr(self.dynamic_engine, 'get_statistics', lambda: {})(),
            'enhanced_stats': getattr(self.enhanced_engine, 'get_statistics', lambda: {})()
        }

    # Proxy properties to match existing interface
    @property
    def config(self):
        """Get current engine config"""
        return self.current_engine.config if self.current_engine else None


# Singleton instance
_hybrid_instance = None


def get_hybrid_scoring_system() -> HybridScoringSystem:
    """Get or create hybrid scoring system instance"""
    global _hybrid_instance

    if _hybrid_instance is None:
        _hybrid_instance = HybridScoringSystem()

    return _hybrid_instance