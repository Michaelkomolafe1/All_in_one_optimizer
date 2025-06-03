#!/usr/bin/env python3
"""
COMPREHENSIVE DFS LAUNCHER
=========================
🚀 Launch DFS system with all modes
🎯 Quick access to manual-only mode
🔧 Debug and testing options
"""

import sys
import os
from pathlib import Path

def main():
    """Main launcher with mode selection"""

    print("🚀 COMPREHENSIVE DFS SYSTEM LAUNCHER")
    print("=" * 50)
    print("Select launch mode:")
    print("1. 🔒 Bulletproof Mode (Confirmed + Manual)")
    print("2. 🎯 Manual-Only Mode (Ultimate Control)")
    print("3. 🔍 Confirmed-Only Mode (No Manual)")
    print("4. 🧪 Test All Modes")
    print("5. 🔧 Run System Diagnostics")
    print("6. 📋 Export Debug Data")
    print("7. ❌ Exit")

    while True:
        try:
            choice = input("\nEnter choice (1-7): ").strip()

            if choice == "1":
                launch_bulletproof_mode()
                break
            elif choice == "2":
                launch_manual_only_mode()
                break
            elif choice == "3":
                launch_confirmed_only_mode()
                break
            elif choice == "4":
                test_all_modes()
                break
            elif choice == "5":
                run_diagnostics()
                break
            elif choice == "6":
                export_debug_data()
                break
            elif choice == "7":
                print("👋 Goodbye!")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter 1-7.")

        except KeyboardInterrupt:
            print("\n👋 Cancelled by user")
            sys.exit(0)

def launch_bulletproof_mode():
    """Launch in bulletproof mode"""
    print("🔒 Launching Bulletproof Mode...")
    try:
        from enhanced_dfs_gui import main as gui_main
        # Set default mode to bulletproof
        os.environ['DFS_DEFAULT_MODE'] = 'bulletproof'
        gui_main()
    except ImportError:
        print("❌ GUI not available. Install PyQt5: pip install PyQt5")

def launch_manual_only_mode():
    """Launch in manual-only mode"""
    print("🎯 Launching Manual-Only Mode...")
    try:
        from enhanced_dfs_gui import main as gui_main
        # Set default mode to manual-only
        os.environ['DFS_DEFAULT_MODE'] = 'manual_only'
        gui_main()
    except ImportError:
        print("❌ GUI not available. Install PyQt5: pip install PyQt5")

def launch_confirmed_only_mode():
    """Launch in confirmed-only mode"""
    print("🔍 Launching Confirmed-Only Mode...")
    try:
        from enhanced_dfs_gui import main as gui_main
        # Set default mode to confirmed-only
        os.environ['DFS_DEFAULT_MODE'] = 'confirmed_only'
        gui_main()
    except ImportError:
        print("❌ GUI not available. Install PyQt5: pip install PyQt5")

def test_all_modes():
    """Test all optimization modes"""
    print("🧪 Testing all modes...")
    try:
        from bulletproof_dfs_core import create_complete_test_data, load_and_optimize_complete_enhanced_pipeline

        dk_file, _ = create_complete_test_data()
        manual_input = "Shohei Ohtani, Francisco Lindor, Hunter Brown"

        for mode in ['bulletproof', 'manual_only', 'confirmed_only']:
            print(f"\n🔄 Testing {mode}...")
            lineup, score, _ = load_and_optimize_complete_enhanced_pipeline(
                dk_file=dk_file,
                manual_input=manual_input,
                optimization_mode=mode
            )

            if lineup:
                print(f"✅ {mode}: SUCCESS - {len(lineup)} players")
            else:
                print(f"❌ {mode}: FAILED")

        os.unlink(dk_file)
        print("\n🎉 Testing complete!")

    except Exception as e:
        print(f"❌ Testing failed: {e}")

def run_diagnostics():
    """Run system diagnostics"""
    print("🔧 Running system diagnostics...")

    # Check required files
    required_files = [
        "bulletproof_dfs_core.py",
        "enhanced_dfs_gui.py",
        "vegas_lines.py",
        "confirmed_lineups.py"
    ]

    print("\n📁 File Check:")
    for file in required_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")

    # Check imports
    print("\n📦 Import Check:")
    imports = [
        ("pandas", "import pandas"),
        ("numpy", "import numpy"),
        ("PyQt5", "from PyQt5.QtWidgets import QApplication"),
        ("pulp", "import pulp")
    ]

    for name, import_stmt in imports:
        try:
            exec(import_stmt)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - Install with: pip install {name}")

    print("\n🔧 Diagnostics complete!")

def export_debug_data():
    """Export debug data"""
    print("📋 Exporting debug data...")
    try:
        from bulletproof_dfs_core import CompleteBulletproofDFSCore

        core = CompleteBulletproofDFSCore()
        debug_file = core.export_comprehensive_debug_data()

        if debug_file:
            print(f"✅ Debug data exported: {debug_file}")
        else:
            print("❌ Debug export failed")

    except Exception as e:
        print(f"❌ Export failed: {e}")

if __name__ == "__main__":
    main()
