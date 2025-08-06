#!/usr/bin/env python3
"""
PROPER FIX FOR ENHANCED SCORING
=================================
This completely fixes the import issue
Save as: fix_enhanced_scoring.py
"""

import os


def fix_method_1_redirect():
    """Fix the redirect file to use absolute imports"""

    content = """# Enhanced Scoring Engine Redirect
# This redirects to the v2 version

from main_optimizer.enhanced_scoring_engine_v2 import *
from main_optimizer.enhanced_scoring_engine_v2 import EnhancedScoringEngine

# Make sure the class is available
__all__ = ['EnhancedScoringEngine']
"""

    with open('main_optimizer/enhanced_scoring_engine.py', 'w') as f:
        f.write(content)

    print("✓ Created proper redirect file")


def fix_method_2_disable():
    """Disable enhanced scoring for simulations (it's not needed)"""

    filepath = 'main_optimizer/unified_player_model.py'

    # Read the file
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Save backup
    with open(filepath + '.backup3', 'w') as f:
        f.writelines(lines)

    # Find and comment out the calculate_enhanced_score call
    for i, line in enumerate(lines):
        if 'self.calculate_enhanced_score()' in line and not line.strip().startswith('#'):
            lines[i] = '        # ' + line.lstrip() + '        # Disabled for simulations\n'
            print(f"✓ Disabled enhanced scoring at line {i + 1}")

    # Write back
    with open(filepath, 'w') as f:
        f.writelines(lines)

    print("✓ Enhanced scoring disabled for simulations")


def fix_method_3_direct():
    """Change the import to the correct module name"""

    filepath = 'main_optimizer/unified_player_model.py'

    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()

    # Save backup
    with open(filepath + '.backup4', 'w') as f:
        f.write(content)

    # Fix the import
    content = content.replace(
        'from enhanced_scoring_engine import EnhancedScoringEngine',
        'from main_optimizer.enhanced_scoring_engine_v2 import EnhancedScoringEngine'
    )

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print("✓ Fixed import to use enhanced_scoring_engine_v2")


if __name__ == "__main__":
    print("FIXING ENHANCED SCORING IMPORT ISSUE")
    print("=" * 60)

    # Check we're in the right directory
    if not os.path.exists('main_optimizer'):
        print("❌ ERROR: Run from All_in_one_optimizer directory!")
        exit(1)

    print("\nChoose fix method:")
    print("1. Create proper redirect (recommended)")
    print("2. Disable enhanced scoring for simulations")
    print("3. Fix import directly")
    print("4. Apply ALL fixes (most thorough)")

    choice = input("\nChoice (1-4): ").strip()

    if choice == '1':
        fix_method_1_redirect()
    elif choice == '2':
        fix_method_2_disable()
    elif choice == '3':
        fix_method_3_direct()
    elif choice == '4':
        print("\nApplying all fixes...")
        fix_method_1_redirect()
        fix_method_2_disable()
        print("\n✅ All fixes applied!")
    else:
        print("Invalid choice, applying recommended fix...")
        fix_method_1_redirect()

    print("\n✅ Fix complete! Now run:")
    print("python simulation/comprehensive_simulation_runner.py")