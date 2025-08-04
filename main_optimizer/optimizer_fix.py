#!/usr/bin/env python3
"""Fix the contest_type parameter issue"""

from unified_core_system import UnifiedCoreSystem

# Save original method
_orig_optimize_lineups = UnifiedCoreSystem.optimize_lineups

def _fixed_optimize_lineups(self, num_lineups=1, strategy="balanced", contest_type="gpp", min_unique_players=3):
    """Fixed version that handles contest_type properly"""
    
    # Set contest type in optimizer config BEFORE calling optimize
    if hasattr(self.optimizer, 'config'):
        self.optimizer.config.contest_type = contest_type
    
    # Call original method
    return _orig_optimize_lineups(self, num_lineups, strategy, contest_type, min_unique_players)

# Apply fix
UnifiedCoreSystem.optimize_lineups = _fixed_optimize_lineups

print("✅ Fixed optimizer contest_type handling")
