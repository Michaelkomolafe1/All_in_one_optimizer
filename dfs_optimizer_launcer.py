#!/usr/bin/env python3
"""
🚀 DFS Optimizer Launcher
Simple launcher for the high-performance DFS optimizer with better visibility
"""

import sys
import os
import subprocess


# ANSI color codes for better visibility
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def colored_print(text, color=None):
    """Print colored text for better visibility"""
    if color and hasattr(Colors, color.upper()):
        color_code = getattr(Colors, color.upper())
        print(f"{color_code}{text}{Colors.ENDC}")
    else:
        print(text)


def main():
    """Main launcher function"""
    colored_print("🚀 DFS OPTIMIZER LAUNCHER", "HEADER")
    colored_print("=" * 50, "CYAN")

    # Check what's available
    files_exist = {
        'performance_gui': os.path.exists('performance_integrated_gui.py'),
        'enhanced_gui': os.path.exists('enhanced_dfs_gui.py'),
        'main_enhanced': os.path.exists('main_enhanced.py'),
        'integration_test': os.path.exists('integration_test_script.py')
    }

    colored_print("\n📦 Available Components:", "BLUE")
    for component, exists in files_exist.items():
        status = "✅" if exists else "❌"
        color = "GREEN" if exists else "FAIL"
        colored_print(f"  {status} {component}", color)

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            if files_exist['integration_test']:
                colored_print("\n🧪 Running integration test...", "CYAN")
                return subprocess.call([sys.executable, 'integration_test_script.py'])
            else:
                colored_print("❌ Integration test not available", "FAIL")
                return 1

        elif sys.argv[1] == '--cli':
            if len(sys.argv) < 3:
                colored_print("❌ CLI mode requires a DraftKings CSV file", "FAIL")
                colored_print("Usage: python launch_optimizer.py --cli <dk_file.csv>", "WARNING")
                return 1

            dk_file = sys.argv[2]
            if not os.path.exists(dk_file):
                colored_print(f"❌ File not found: {dk_file}", "FAIL")
                return 1

            # Try different CLI launchers
            cli_options = [
                'main_enhanced_performance.py',
                'main_enhanced.py',
                'dfs_runner_enhanced.py'
            ]

            for cli_script in cli_options:
                if os.path.exists(cli_script):
                    colored_print(f"🔧 Using {cli_script} for CLI mode...", "CYAN")
                    return subprocess.call([
                                               sys.executable, cli_script, '--cli', '--dk', dk_file
                                           ] + sys.argv[3:])

            colored_print("❌ No CLI script available", "FAIL")
            return 1

        elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
            show_help()
            return 0

    # Default: Launch GUI
    colored_print("\n🖥️ Launching GUI...", "GREEN")

    # Try GUI options in order of preference
    gui_options = [
        ('performance_integrated_gui.py', 'High-Performance GUI'),
        ('enhanced_dfs_gui.py', 'Enhanced GUI'),
        ('main_enhanced.py', 'Main Enhanced')
    ]

    for gui_script, gui_name in gui_options:
        if os.path.exists(gui_script):
            colored_print(f"✅ Launching {gui_name}...", "GREEN")
            try:
                return subprocess.call([sys.executable, gui_script])
            except Exception as e:
                colored_print(f"❌ {gui_name} failed: {e}", "FAIL")
                continue

    colored_print("❌ No GUI available", "FAIL")
    show_help()
    return 1


def show_help():
    """Show help information"""
    colored_print("\n💡 AVAILABLE COMMANDS:", "HEADER")
    colored_print("=" * 30, "CYAN")

    commands = [
        ("python launch_optimizer.py", "Launch GUI (default)", "GREEN"),
        ("python launch_optimizer.py --test", "Run integration test", "CYAN"),
        ("python launch_optimizer.py --cli <file.csv>", "CLI mode with DK file", "BLUE"),
        ("python launch_optimizer.py --help", "Show this help", "WARNING")
    ]

    for cmd, desc, color in commands:
        colored_print(f"  {cmd}", color)
        colored_print(f"    → {desc}", "CYAN")
        print()

    colored_print("📁 EXAMPLE USAGE:", "HEADER")
    colored_print("  python launch_optimizer.py --cli DKSalaries.csv", "BLUE")
    colored_print("  python launch_optimizer.py --test", "CYAN")


if __name__ == "__main__":
    try:
        exit_code = main()
        if exit_code == 0:
            colored_print("\n👋 Completed successfully!", "GREEN")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        colored_print("\n👋 Cancelled by user", "WARNING")
        sys.exit(0)
    except Exception as e:
        colored_print(f"\n❌ Launcher error: {e}", "FAIL")
        sys.exit(1)