#!/usr/bin/env python3
"""
🚀 Unified DFS Optimizer - Auto-Fixed Version
Single entry point for all DFS optimization needs
"""

import sys
import os
from pathlib import Path

def main():
    """Unified main entry point"""
    print("🚀 Auto-Fixed DFS Optimizer")
    print("=" * 40)

    # Parse arguments
    if len(sys.argv) == 1:
        # No arguments - launch GUI
        print("🖥️ Launching GUI...")
        return launch_gui()

    elif '--gui' in sys.argv:
        return launch_gui()

    elif '--cli' in sys.argv or len(sys.argv) >= 2:
        return launch_cli()

    else:
        print_usage()
        return 1

def launch_gui():
    """Launch GUI application"""
    try:
        # Try to find and launch best GUI file
        gui_files = [
            'fixed_complete_gui.py',
            'working_dfs_gui.py',
            'dfs_gui.py'
        ]

        for gui_file in gui_files:
            if Path(gui_file).exists():
                print(f"📱 Using GUI: {gui_file}")

                # Import and run GUI
                gui_module = __import__(gui_file[:-3])  # Remove .py

                if hasattr(gui_module, 'main'):
                    return gui_module.main()
                elif hasattr(gui_module, 'FreshWorkingDFSGUI'):
                    from PyQt5.QtWidgets import QApplication
                    app = QApplication(sys.argv)
                    window = gui_module.FreshWorkingDFSGUI()
                    window.show()
                    return app.exec_()

        print("❌ No GUI file found!")
        return 1

    except ImportError as e:
        print(f"❌ GUI launch failed: {e}")
        print("💡 Try installing: pip install PyQt5")
        return 1

def launch_cli():
    """Launch CLI optimization"""
    try:
        # Try to find and launch best CLI runner
        cli_files = [
            'dfs_runner_enhanced.py',
            'dfs_enhanced_runner.py', 
            'working_quick_fixes.py'
        ]

        for cli_file in cli_files:
            if Path(cli_file).exists():
                print(f"⚡ Using CLI: {cli_file}")

                # Run CLI module
                import subprocess
                result = subprocess.run([sys.executable, cli_file] + sys.argv[1:])
                return result.returncode

        print("❌ No CLI runner found!")
        return 1

    except Exception as e:
        print(f"❌ CLI launch failed: {e}")
        return 1

def print_usage():
    """Print usage information"""
    print("""
🚀 Auto-Fixed DFS Optimizer Usage:

GUI Mode (default):
  python main.py
  python main.py --gui

CLI Mode:
  python main.py --cli --dk your_file.csv
  python main.py your_dk_file.csv your_dff_file.csv

Examples:
  python main.py                           # Launch GUI
  python main.py --dk DKSalaries.csv      # CLI optimization
  python main.py DK.csv DFF.csv           # CLI with DFF data
""")

if __name__ == "__main__":
    sys.exit(main())
