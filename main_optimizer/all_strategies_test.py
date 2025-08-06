#!/usr/bin/env python3
"""Remove all unused strategies from codebase"""

import os
import re

print("🧹 CLEANING UP UNUSED STRATEGIES...")

# Strategies to KEEP
keep_strategies = {
    'projection_monster',
    'pitcher_dominance',
    'tournament_winner_gpp',
    'correlation_value',
    'auto'  # For auto-selection
}

# Files to clean
files_to_check = [
    'main_optimizer/gui_strategy_configuration.py',
    'main_optimizer/strategy_selector.py',
    'main_optimizer/smart_enrichment_manager.py'
]

removed_count = 0

for filepath in files_to_check:
    if not os.path.exists(filepath):
        continue

    print(f"\nChecking {filepath}...")

    with open(filepath, 'r') as f:
        content = f.read()

    # Find strategy references
    # This is a simple check - you may need to manually review
    strategies_mentioned = re.findall(r"'(\w+_\w+)'", content)
    strategies_mentioned.update(re.findall(r'"(\w+_\w+)"', content))

    for strategy in set(strategies_mentioned):
        if '_' in strategy and strategy not in keep_strategies:
            if 'balance' in strategy or 'smart_stack' in strategy or 'leverage' in strategy:
                print(f"  Found unused strategy: {strategy}")
                removed_count += 1

print(f"\n📊 Found {removed_count} references to unused strategies")
print("Review files manually to remove them completely")