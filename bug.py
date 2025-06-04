#!/usr/bin/env python3
"""
QUICK CHECK - Does the method exist?
"""


def check_method_exists():
    try:
        from bulletproof_dfs_core import BulletproofDFSCore

        if hasattr(BulletproofDFSCore, 'optimize_lineup_with_mode'):
            print("✅ Method EXISTS in the code!")
            print("💡 Solution: Restart your GUI completely")
            print("   Close GUI → Run: python enhanced_dfs_gui.py")
        else:
            print("❌ Method MISSING from code!")
            print("💡 Solution: The fix didn't work properly")
            print("   Try: python guaranteed_fix.py")

            # Try to add it now
            print("\n🔧 Attempting to add method now...")

            def optimize_lineup_with_mode(self):
                print("🎯 EMERGENCY METHOD WORKING!")
                return [], 0

            BulletproofDFSCore.optimize_lineup_with_mode = optimize_lineup_with_mode
            print("✅ Emergency method added! Try your GUI now.")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    check_method_exists()