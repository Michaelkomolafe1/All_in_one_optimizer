#!/usr/bin/env python3
"""Quick fixes for common issues"""

# Fix 1: Update __init__.py imports
def fix_imports():
    init_file = "dfs_optimizer/strategies/__init__.py"
    content = """
from .strategy_selector import StrategyAutoSelector

__all__ = ['StrategyAutoSelector']
"""
    with open(init_file, 'w') as f:
        f.write(content.strip())
    print("✅ Fixed strategy imports")

# Fix 2: Ensure contest type is passed
def check_scoring_params():
    """Verify scoring parameters are different"""
    from enhanced_scoring_engine import EnhancedScoringEngine
    engine = EnhancedScoringEngine()

    print("Cash params:", engine.cash_params)
    print("GPP params:", engine.gpp_params)

    # Check if they're different
    cash_weights = engine.cash_params.get('weight_projection', 0)
    gpp_weights = engine.gpp_params.get('weight_ceiling', 0)

    if abs(cash_weights - gpp_weights) < 0.1:
        print("⚠️ Parameters too similar!")

if __name__ == "__main__":
    print("Running quick fixes...")
    # fix_imports()  # Uncomment to run
    check_scoring_params()
