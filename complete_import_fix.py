#!/usr/bin/env python3
"""
COMPLETE IMPORT FIX
===================
Creates all missing redirect files and fixes imports
Save as: complete_import_fix.py
"""

import os
import sys


def create_unified_core_redirect():
    """Create unified_core_system.py that redirects to unified_core_system_updated.py"""

    content = """# Redirect to updated version
from .unified_core_system_updated import *
from .unified_core_system_updated import UnifiedCoreSystem

# For backward compatibility
__all__ = ['UnifiedCoreSystem']
"""

    filepath = 'main_optimizer/unified_core_system.py'
    with open(filepath, 'w') as f:
        f.write(content)

    print(f"✓ Created {filepath} (redirect)")


def create_enhanced_scoring_redirect():
    """Create enhanced_scoring_engine.py that redirects to v2"""

    content = """# Redirect to v2 version
from .enhanced_scoring_engine_v2 import *
from .enhanced_scoring_engine_v2 import EnhancedScoringEngineV2

# Alias for compatibility
EnhancedScoringEngine = EnhancedScoringEngineV2

__all__ = ['EnhancedScoringEngine', 'EnhancedScoringEngineV2']
"""

    filepath = 'main_optimizer/enhanced_scoring_engine.py'
    with open(filepath, 'w') as f:
        f.write(content)

    print(f"✓ Created {filepath} (redirect)")


def test_imports_directly():
    """Test imports right here"""

    print("\n📋 Testing imports directly...")

    # Add path
    sys.path.insert(0, os.getcwd())

    success = []
    failed = []

    # Test each import
    tests = [
        ('UnifiedCoreSystem', 'from main_optimizer.unified_core_system_updated import UnifiedCoreSystem'),
        ('UnifiedPlayer', 'from main_optimizer.unified_player_model import UnifiedPlayer'),
        ('EnhancedScoringEngineV2', 'from main_optimizer.enhanced_scoring_engine_v2 import EnhancedScoringEngineV2'),
        ('Cash strategies', 'from main_optimizer.cash_strategies import build_projection_monster'),
        ('GPP strategies', 'from main_optimizer.gpp_strategies import build_correlation_value'),
    ]

    for name, import_str in tests:
        try:
            exec(import_str)
            print(f"  ✓ {name}")
            success.append(name)
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed.append(name)

    return len(failed) == 0


def create_working_test_script():
    """Create a test script that will actually work"""

    content = '''#!/usr/bin/env python3
"""Test imports - Fixed version"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("Testing imports...")

try:
    from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
    print("✓ UnifiedCoreSystem (from _updated)")
except Exception as e:
    print(f"❌ UnifiedCoreSystem: {e}")

try:
    from main_optimizer.unified_core_system import UnifiedCoreSystem
    print("✓ UnifiedCoreSystem (from redirect)")
except Exception as e:
    print(f"❌ UnifiedCoreSystem redirect: {e}")

try:
    from main_optimizer.unified_player_model import UnifiedPlayer
    print("✓ UnifiedPlayer")
except Exception as e:
    print(f"❌ UnifiedPlayer: {e}")

try:
    from main_optimizer.enhanced_scoring_engine_v2 import EnhancedScoringEngineV2
    print("✓ EnhancedScoringEngineV2")
except Exception as e:
    print(f"❌ EnhancedScoringEngineV2: {e}")

try:
    from main_optimizer.enhanced_scoring_engine import EnhancedScoringEngine
    print("✓ EnhancedScoringEngine (redirect)")
except Exception as e:
    print(f"❌ EnhancedScoringEngine: {e}")

try:
    from main_optimizer.cash_strategies import build_projection_monster, build_pitcher_dominance
    print("✓ Cash strategies")
except Exception as e:
    print(f"❌ Cash strategies: {e}")

try:
    from main_optimizer.gpp_strategies import build_correlation_value
    print("✓ GPP strategies")
except Exception as e:
    print(f"❌ GPP strategies: {e}")

try:
    from main_optimizer.tournament_winner_gpp_strategy import build_tournament_winner_gpp
    print("✓ Tournament winner strategy")
except Exception as e:
    print(f"❌ Tournament winner: {e}")

print("\\n✅ Import test complete!")
'''

    with open('test_imports_fixed.py', 'w') as f:
        f.write(content)

    print("✓ Created test_imports_fixed.py")


def quick_gui_test():
    """Quick test if GUI can load"""

    print("\n📋 Quick GUI load test...")

    try:
        sys.path.insert(0, os.getcwd())
        from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
        from main_optimizer.unified_player_model import UnifiedPlayer

        # Try to create instances
        system = UnifiedCoreSystem()
        print("  ✓ Can create UnifiedCoreSystem")

        # Try to create a player (might fail due to enhanced scoring)
        try:
            player = UnifiedPlayer(
                id="test",
                name="Test Player",
                team="TEST",
                salary=5000,
                primary_position="OF",
                positions=["OF"],
                base_projection=10.0
            )
            print("  ✓ Can create UnifiedPlayer")
        except:
            print("  ⚠️ UnifiedPlayer creation has issues (enhanced scoring?)")

        return True

    except Exception as e:
        print(f"  ❌ GUI test failed: {e}")
        return False


def main():
    print("=" * 60)
    print("COMPLETE IMPORT FIX")
    print("=" * 60)

    # Check we're in right directory
    if not os.path.exists('main_optimizer'):
        print("❌ ERROR: Run from All_in_one_optimizer directory!")
        print("cd /home/michael/Desktop/All_in_one_optimizer")
        return

    print("\n🔧 Creating redirect files...")

    # Create all redirects
    create_unified_core_redirect()
    create_enhanced_scoring_redirect()

    print("\n🔧 Creating fixed test script...")
    create_working_test_script()

    print("\n" + "=" * 60)

    # Test imports
    if test_imports_directly():
        print("\n✅ ALL IMPORTS WORKING!")

        # Quick GUI test
        quick_gui_test()

        print("\n" + "=" * 60)
        print("✅ FIXES COMPLETE!")
        print("\nNow you can:")
        print("1. Run GUI: python main_optimizer/GUI.py")
        print("2. Run simulation: python simulation/comprehensive_simulation_runner.py")
        print("3. Test imports: python test_imports_fixed.py")
    else:
        print("\n⚠️ Some imports still failing")
        print("But the redirect files are created.")
        print("Try running your GUI anyway - it might work!")


if __name__ == "__main__":
    main()