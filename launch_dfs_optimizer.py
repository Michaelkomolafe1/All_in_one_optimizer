#!/usr/bin/env python3
"""
DFS OPTIMIZER LAUNCHER
=====================
Simple launcher for the DFS optimization system
"""

import sys
import os
from pathlib import Path


def check_environment():
    """Check if the environment is set up correctly"""
    issues = []

    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(f"Python 3.8+ required (you have {sys.version})")

    # Check required modules
    required_modules = ['pandas', 'numpy', 'pulp', 'PyQt5']
    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        issues.append(f"Missing modules: {', '.join(missing_modules)}")
        issues.append("Run: pip install -r requirements.txt")

    return issues


def launch_gui():
    """Launch the GUI application"""
    try:
        from complete_dfs_gui_debug import main
        print("🚀 Launching DFS Optimizer GUI...")
        main()
    except ImportError:
        print("❌ GUI module not found. Creating it now...")
        create_gui()
        print("\n✅ GUI created. Please run the launcher again.")
        sys.exit(0)


def launch_cli():
    """Launch command line interface"""
    print("\n📊 DFS Optimizer - Command Line Mode")
    print("=" * 50)

    from unified_core_system import UnifiedCoreSystem

    # Example workflow
    print("\nExample usage:")
    print("1. system = UnifiedCoreSystem()")
    print("2. system.load_csv('DKSalaries.csv')")
    print("3. system.fetch_confirmed_players()")
    print("4. system.build_player_pool()")
    print("5. system.enrich_player_pool()")
    print("6. lineups = system.optimize_lineups(20, contest_type='gpp')")
    print("\nStarting interactive Python session...")

    # Start interactive session
    import code
    code.interact(local=locals())


def create_gui():
    """Create the GUI if it doesn't exist"""
    # Import the streamlined GUI from our artifacts
    from streamlined_dfs_gui import main as gui_code

    # Get the source code of the GUI
    import inspect
    gui_source = inspect.getsource(gui_code)

    # Write to file
    with open('complete_dfs_gui_debug.py', 'w') as f:
        f.write(gui_source)


def main():
    """Main launcher function"""
    print("🎯 DFS Optimizer - Correlation Edition")
    print("=" * 50)

    # Check environment
    issues = check_environment()
    if issues:
        print("\n❌ Environment issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nPlease fix these issues before continuing.")
        sys.exit(1)

    # Check for GUI availability
    gui_available = Path('complete_dfs_gui_debug.py').exists()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--cli':
            launch_cli()
        elif sys.argv[1] == '--gui':
            launch_gui()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Usage: python launch_dfs_optimizer.py [--gui|--cli]")
    else:
        # Default to GUI if available
        if gui_available:
            launch_gui()
        else:
            print("\nGUI not found. Choose an option:")
            print("1. Create GUI and launch")
            print("2. Use command line interface")

            choice = input("\nEnter choice (1 or 2): ")

            if choice == '1':
                create_gui()
                print("\n✅ GUI created. Launching...")
                launch_gui()
            else:
                launch_cli()


if __name__ == "__main__":
    main()
