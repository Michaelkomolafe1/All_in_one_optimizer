"""
SCORING ENGINE COMPATIBILITY LAYER
===================================
Ensures old imports still work after consolidation
All scoring engines now use V2
"""

from .enhanced_scoring_engine_v2 import EnhancedScoringEngineV2

# Aliases for backward compatibility
UnifiedScoringEngine = EnhancedScoringEngineV2
EnhancedScoringEngine = EnhancedScoringEngineV2
PureDataScoringEngine = EnhancedScoringEngineV2
VegasScoringEngine = EnhancedScoringEngineV2

# The one true scoring engine
ScoringEngine = EnhancedScoringEngineV2

print("✅ Scoring compatibility layer loaded - all engines → V2")

__all__ = [
    'ScoringEngine',
    'EnhancedScoringEngineV2',
    'UnifiedScoringEngine',
    'EnhancedScoringEngine',
    'PureDataScoringEngine'
]
