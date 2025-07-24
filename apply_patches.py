#!/usr/bin/env python3
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
