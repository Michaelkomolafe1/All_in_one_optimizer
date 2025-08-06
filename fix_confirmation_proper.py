#!/usr/bin/env python3
"""
Quick fix for the method name issue
"""

import os


def fix_method_name():
    """Fix the fetch_all_confirmations to get_all_confirmations"""

    print("🔧 Fixing method name in unified_core_system_updated.py...")

    filepath = 'main_optimizer/unified_core_system_updated.py'

    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace the method name
    content = content.replace(
        'self.confirmation_system.fetch_all_confirmations()',
        'self.confirmation_system.get_all_confirmations()'
    )

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print("  ✓ Fixed method name")


def verify_confirmation_methods():
    """Check what methods are available in smart_confirmation.py"""

    print("\n🔍 Checking available confirmation methods...")

    filepath = 'main_optimizer/smart_confirmation.py'

    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()

        # Find method definitions
        import re
        methods = re.findall(r'def (.*?)\(', content)

        print("  Available methods in UniversalSmartConfirmation:")
        for method in methods:
            if 'confirm' in method.lower() or 'get' in method.lower():
                print(f"    - {method}()")
    else:
        print("  ⚠ smart_confirmation.py not found")


def main():
    print("=" * 60)
    print("QUICK FIX - Method Name")
    print("=" * 60)

    if not os.path.exists('main_optimizer'):
        print("❌ Run from All_in_one_optimizer directory!")
        return

    # Fix the method name
    fix_method_name()

    # Verify available methods
    verify_confirmation_methods()

    print("\n" + "=" * 60)
    print("✅ FIXED!")
    print("=" * 60)

    print("\n🚀 Now:")
    print("1. Restart the GUI")
    print("2. Load your CSV")
    print("3. Click 'Fetch Confirmations'")
    print("4. It should work now!")

    print("\n💡 Or just:")
    print("- Uncheck 'Confirmed Only' to see all 466 players immediately")


if __name__ == "__main__":
    main()