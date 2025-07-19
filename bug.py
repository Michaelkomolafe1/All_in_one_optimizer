#!/usr/bin/env python3
"""
FIX ALL ERRORS SCRIPT
====================
Run this to fix all import and reference errors
"""

import os


def fix_bulletproof_dfs_core():
    """Add missing imports to bulletproof_dfs_core.py"""
    print("Fixing bulletproof_dfs_core.py...")

    with open('bulletproof_dfs_core.py', 'r') as f:
        content = f.read()

    # Check if typing imports already exist
    if 'from typing import' not in content:
        # Add after the docstring and before other imports
        lines = content.split('\n')
        insert_pos = 0

        # Find where to insert (after docstring)
        for i, line in enumerate(lines):
            if line.strip().startswith('import') or line.strip().startswith('from'):
                insert_pos = i
                break

        # Insert the typing import
        lines.insert(insert_pos, 'from typing import Any, Dict, List, Optional, Tuple')

        with open('bulletproof_dfs_core.py', 'w') as f:
            f.write('\n'.join(lines))

        print("✅ Added typing imports to bulletproof_dfs_core.py")
    else:
        print("✅ bulletproof_dfs_core.py already has typing imports")


def fix_simple_statcast_fetcher():
    """Add missing imports to simple_statcast_fetcher.py"""
    print("\nFixing simple_statcast_fetcher.py...")

    with open('simple_statcast_fetcher.py', 'r') as f:
        content = f.read()

    if 'from typing import' not in content:
        lines = content.split('\n')
        insert_pos = 0

        for i, line in enumerate(lines):
            if line.strip().startswith('import') or line.strip().startswith('from'):
                insert_pos = i
                break

        lines.insert(insert_pos, 'from typing import Any, Dict, List, Optional, Tuple')

        with open('simple_statcast_fetcher.py', 'w') as f:
            f.write('\n'.join(lines))

        print("✅ Added typing imports to simple_statcast_fetcher.py")
    else:
        print("✅ simple_statcast_fetcher.py already has typing imports")


def fix_advanced_dfs_core():
    """Fix imports in advanced_dfs_core.py"""
    print("\nFixing advanced_dfs_core.py...")

    # Read the file
    with open('advanced_dfs_core.py', 'r') as f:
        content = f.read()

    # Replace the problematic import
    old_import = "from advanced_scoring_engine import create_advanced_scoring_engine, AdvancedScoringConfig"
    new_import = "from advanced_scoring_engine import AdvancedScoringEngine, AdvancedScoringConfig"

    if old_import in content:
        content = content.replace(old_import, new_import)

        # Also fix the initialization
        content = content.replace(
            "self.scoring_engine = create_advanced_scoring_engine(scoring_config)",
            "self.scoring_engine = AdvancedScoringEngine(scoring_config)"
        )

        with open('advanced_dfs_core.py', 'w') as f:
            f.write(content)

        print("✅ Fixed imports in advanced_dfs_core.py")
    else:
        print("⚠️  Import already fixed or different in advanced_dfs_core.py")


def check_advanced_scoring_engine():
    """Check what's in advanced_scoring_engine.py"""
    print("\nChecking advanced_scoring_engine.py...")

    try:
        with open('advanced_scoring_engine.py', 'r') as f:
            content = f.read()

        # Check for the class
        if 'class AdvancedScoringEngine' in content:
            print("✅ Found AdvancedScoringEngine class")
        else:
            print("❌ Missing AdvancedScoringEngine class!")

        if 'class AdvancedScoringConfig' in content:
            print("✅ Found AdvancedScoringConfig class")
        else:
            print("❌ Missing AdvancedScoringConfig class!")

        # Check if it's the wrong file
        if 'UnifiedScoringEngine' in content:
            print("\n⚠️  WARNING: This might be the old unified_scoring_engine.py!")
            print("   You need the NEW advanced_scoring_engine.py from our conversation")

    except FileNotFoundError:
        print("❌ advanced_scoring_engine.py not found!")


def main():
    print("🔧 FIXING ALL IMPORT ERRORS")
    print("=" * 50)

    # Fix each file
    try:
        fix_bulletproof_dfs_core()
    except Exception as e:
        print(f"❌ Error fixing bulletproof_dfs_core.py: {e}")

    try:
        fix_simple_statcast_fetcher()
    except Exception as e:
        print(f"❌ Error fixing simple_statcast_fetcher.py: {e}")

    try:
        fix_advanced_dfs_core()
    except Exception as e:
        print(f"❌ Error fixing advanced_dfs_core.py: {e}")

    # Check the scoring engine
    check_advanced_scoring_engine()

    print("\n✅ Fix script complete!")
    print("\n📋 Next steps:")
    print("1. If advanced_scoring_engine.py is wrong, save the correct one from our conversation")
    print("2. Run 'python check_system.py' to verify everything works")
    print("3. Remove unused imports manually or with your IDE's cleanup tool")


if __name__ == "__main__":
    main()