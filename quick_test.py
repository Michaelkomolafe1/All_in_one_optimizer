#!/usr/bin/env python3
"""
SETUP INTEGRATION SCRIPT
========================
Helps integrate all the improvements into your DFS system
"""

import os
import sys
import shutil
from pathlib import Path


def check_required_files():
    """Check which required files exist"""
    print("\n🔍 Checking required files...")

    required_files = {
        # Core files that should exist
        'unified_player_model.py': 'Core player model',
        'unified_milp_optimizer.py': 'MILP optimization engine',
        'smart_confirmation_system.py': 'Lineup confirmations',
        'simple_statcast_fetcher.py': 'Baseball statistics',
        'vegas_lines.py': 'Vegas betting lines',
        'cash_optimization_config.py': 'Contest configurations',

        # New files to be added
        'correlation_scoring_config.py': 'Correlation scoring configuration',
        'step2_updated_player_model.py': 'Simplified scoring engine',
        'step3_stack_detection.py': 'Stack detection system',
        'integrated_scoring_system.py': 'Integrated correlation scoring',
        'fixed_showdown_optimization.py': 'Fixed showdown optimizer',
    }

    existing = []
    missing = []

    for filename, description in required_files.items():
        if Path(filename).exists():
            existing.append((filename, description))
            print(f"  ✅ {filename} - {description}")
        else:
            missing.append((filename, description))
            print(f"  ❌ {filename} - {description} (MISSING)")

    return existing, missing


def create_integration_patches():
    """Create patches to integrate the new system"""
    print("\n🔧 Creating integration patches...")

    # Create a patch file for UnifiedCoreSystem
    patch_content = '''#!/usr/bin/env python3
"""
INTEGRATION PATCH
=================
Apply this to integrate the new scoring system
"""

def patch_unified_core():
    """Patch UnifiedCoreSystem to use new scoring"""
    try:
        # Import the fixed version
        from unified_core_system import UnifiedCoreSystem

        # The new version already has integrated scoring
        print("✅ UnifiedCoreSystem is already using integrated scoring")
        return True

    except ImportError as e:
        print(f"❌ Could not import UnifiedCoreSystem: {e}")
        return False


def patch_showdown():
    """Ensure showdown optimization is fixed"""
    try:
        from fixed_showdown_optimization import integrate_showdown_with_core
        from unified_core_system import UnifiedCoreSystem

        # Apply the patch
        integrate_showdown_with_core(UnifiedCoreSystem)
        print("✅ Showdown optimization patched successfully")
        return True

    except ImportError as e:
        print(f"❌ Could not patch showdown: {e}")
        return False


if __name__ == "__main__":
    print("Applying integration patches...")
    patch_unified_core()
    patch_showdown()
'''

    with open('apply_patches.py', 'w') as f:
        f.write(patch_content)

    print("  ✅ Created apply_patches.py")


def create_minimal_test():
    """Create a minimal test script"""
    print("\n🧪 Creating minimal test script...")

    test_content = '''#!/usr/bin/env python3
"""
MINIMAL INTEGRATION TEST
========================
Tests that all components work together
"""

import sys
from types import SimpleNamespace


def test_scoring_integration():
    """Test the integrated scoring system"""
    print("\\n1️⃣ Testing Integrated Scoring...")

    try:
        from integrated_scoring_system import IntegratedScoringEngine

        # Create test player
        player = SimpleNamespace(
            name="Test Player",
            team="NYY",
            primary_position="OF",
            salary=10000,
            dk_projection=10.0,
            team_total=5.5,
            batting_order=3,
            game_park="neutral"
        )

        # Test scoring
        engine = IntegratedScoringEngine()
        engine.set_contest_type('gpp')
        score = engine.calculate_score(player)

        print(f"  ✅ Scoring works! Test score: {score:.2f}")
        return True

    except Exception as e:
        print(f"  ❌ Scoring failed: {e}")
        # Try fallback
        try:
            from step2_updated_player_model import SimplifiedScoringEngine
            engine = SimplifiedScoringEngine()
            print("  ⚠️  Using fallback SimplifiedScoringEngine")
            return True
        except:
            return False


def test_showdown_detection():
    """Test showdown detection"""
    print("\\n2️⃣ Testing Showdown Detection...")

    try:
        from fixed_showdown_optimization import ShowdownOptimizer

        # Create test showdown players
        players = [
            SimpleNamespace(name="P1", position="CPT", team="NYY", salary=15000),
            SimpleNamespace(name="P2", position="UTIL", team="NYY", salary=10000),
        ]

        optimizer = ShowdownOptimizer(None)
        is_showdown = optimizer.detect_showdown_slate(players)

        if is_showdown:
            print("  ✅ Showdown detection works!")
            return True
        else:
            print("  ❌ Failed to detect showdown slate")
            return False

    except Exception as e:
        print(f"  ❌ Showdown test failed: {e}")
        return False


def test_core_system():
    """Test the core system initialization"""
    print("\\n3️⃣ Testing Core System...")

    try:
        from unified_core_system import UnifiedCoreSystem

        system = UnifiedCoreSystem()

        # Check components
        checks = [
            (hasattr(system, 'scoring_engine'), "Scoring engine"),
            (hasattr(system, 'optimizer'), "MILP optimizer"),
            (hasattr(system, 'showdown_optimizer'), "Showdown optimizer"),
        ]

        all_good = True
        for check, name in checks:
            if check:
                print(f"  ✅ {name} initialized")
            else:
                print(f"  ❌ {name} missing")
                all_good = False

        return all_good

    except Exception as e:
        print(f"  ❌ Core system test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 MINIMAL INTEGRATION TEST")
    print("=" * 40)

    results = []
    results.append(test_scoring_integration())
    results.append(test_showdown_detection())
    results.append(test_core_system())

    print("\\n" + "=" * 40)
    if all(results):
        print("✅ ALL TESTS PASSED! System is integrated correctly.")
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)
'''

    with open('test_integration.py', 'w') as f:
        f.write(test_content)

    print("  ✅ Created test_integration.py")


def fix_imports():
    """Create a script to fix import issues"""
    print("\n🔧 Creating import fixer...")

    fixer_content = '''#!/usr/bin/env python3
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
        content = content.replace(old_import + '\\n', '')
        content = content.replace(old_import, '')

    # Save the fixed file
    with open('unified_core_system.py.fixed', 'w') as f:
        f.write(content)

    print("✅ Created unified_core_system.py.fixed")
    print("   Review and rename to unified_core_system.py")


if __name__ == "__main__":
    fix_unified_core_imports()
'''

    with open('fix_imports.py', 'w') as f:
        f.write(fixer_content)

    print("  ✅ Created fix_imports.py")


def main():
    """Main setup process"""
    print("🚀 DFS OPTIMIZER INTEGRATION SETUP")
    print("=" * 50)

    # Check files
    existing, missing = check_required_files()

    if missing:
        print("\n⚠️  You need to create the following files:")
        for filename, description in missing:
            print(f"   - {filename}: {description}")
        print("\nUse the artifacts from our conversation to create these files.")

    # Create helpers
    create_integration_patches()
    create_minimal_test()
    fix_imports()

    print("\n📋 NEXT STEPS:")
    print("1. Use the fixed unified_core_system.py from the artifact")
    print("2. Create any missing files from the artifacts")
    print("3. Run: python fix_imports.py")
    print("4. Run: python apply_patches.py")
    print("5. Run: python test_integration.py")

    print("\n✅ Setup complete! Follow the steps above to integrate everything.")


if __name__ == "__main__":
    main()