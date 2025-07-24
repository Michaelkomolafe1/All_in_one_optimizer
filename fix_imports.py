#!/usr/bin/env python3
"""
IMPORT FIXER
============
Fixes import issues in your project
"""

import os
import re


def fix_unified_core_imports():
    """Fix imports in unified_core_system.py"""
    if not os.path.exists('unified_core_system.py'):
        print("❌ unified_core_system.py not found")
        return

    # Read the file
    with open('unified_core_system.py', 'r') as f:
        content = f.read()

    # Remove old imports
    old_imports = [
        'from showdown_optimizer import ShowdownOptimizer, is_showdown_slate',
        'from unified_scoring_engine import get_scoring_engine, ScoringConfig',
        'from pure_data_scoring_engine import get_pure_scoring_engine, PureDataScoringConfig',
    ]

    for old_import in old_imports:
        content = content.replace(old_import + '\n', '')
        content = content.replace(old_import, '')

    # Save the fixed file
    with open('unified_core_system.py.fixed', 'w') as f:
        f.write(content)

    print("✅ Created unified_core_system.py.fixed")
    print("   Review and rename to unified_core_system.py")


if __name__ == "__main__":
    fix_unified_core_imports()
