#!/usr/bin/env python3
"""
DFS OPTIMIZER - INTELLIGENT SYSTEM LAUNCHER
===========================================
Smart launcher that detects your environment and launches the best interface
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


class DFSLauncher:
    """Intelligent launcher for DFS Optimizer system"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.available_interfaces = []
        self.csv_files = []

    def print_header(self):
        """Print professional header"""
        print("🚀 DFS OPTIMIZER - INTELLIGENT LAUNCHER")
        print("=" * 60)
        print(f"📁 Project: {self.project_root}")
        print(f"🐍 Python: {sys.version.split()[0]}")

    def detect_interfaces(self) -> List[dict]:
        """Detect available user interfaces"""
        interfaces = []

        # Check for GUI
        gui_file = self.project_root / "enhanced_dfs_gui.py"
        if gui_file.exists():
            # Check if PyQt5 is available
            try:
                import PyQt5
                interfaces.append({
                    'name': 'Enhanced GUI',
                    'file': 'enhanced_dfs_gui.py',
                    'command': [sys.executable, str(gui_file)],
                    'description': '🖥️  Full-featured graphical interface',
                    'priority': 1,
                    'available': True
                })
            except ImportError:
                interfaces.append({
                    'name': 'Enhanced GUI',
                    'file': 'enhanced_dfs_gui.py',
                    'command': [sys.executable, str(gui_file)],
                    'description': '🖥️  Full-featured GUI (PyQt5 required)',
                    'priority': 1,
                    'available': False,
                    'error': 'PyQt5 not installed. Run: pip install PyQt5'
                })

        # Check for CLI
        cli_file = self.project_root / "script.py"
        if cli_file.exists():
            interfaces.append({
                'name': 'Professional CLI',
                'file': 'script.py',
                'command': [sys.executable, str(cli_file)],
                'description': '💻 Advanced command-line interface',
                'priority': 2,
                'available': True
            })

        # Check for other interfaces
        other_files = [
            ('streamlined_dfs_gui.py', '🖥️  Simplified GUI interface'),
            ('dfs_cli.py', '⚡ Basic CLI interface'),
        ]

        for filename, desc in other_files:
            file_path = self.project_root / filename
            if file_path.exists():
                interfaces.append({
                    'name': filename.replace('.py', '').replace('_', ' ').title(),
                    'file': filename,
                    'command': [sys.executable, str(file_path)],
                    'description': desc,
                    'priority': 3,
                    'available': True
                })

        return sorted(interfaces, key=lambda x: x['priority'])

    def detect_csv_files(self) -> List[str]:
        """Detect available CSV files"""
        csv_files = []

        # Check current directory
        for file in self.project_root.glob("*.csv"):
            csv_files.append(str(file))

        # Check sample_data directory
        sample_dir = self.project_root / "sample_data"
        if sample_dir.exists():
            for file in sample_dir.glob("*.csv"):
                csv_files.append(str(file))

        # Check Downloads directory (common location)
        downloads_dir = Path.home() / "Downloads"
        if downloads_dir.exists():
            dk_files = list(downloads_dir.glob("DK*.csv"))
            if dk_files:
                # Sort by modification time, newest first
                dk_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                csv_files.extend([str(f) for f in dk_files[:5]])  # Top 5 most recent

        return csv_files

    def check_system_health(self) -> dict:
        """Check system health and requirements"""
        health = {
            'core_available': False,
            'dependencies_met': True,
            'missing_deps': [],
            'warnings': []
        }

        # Check core module
        try:
            from bulletproof_dfs_core import BulletproofDFSCore
            health['core_available'] = True
        except ImportError as e:
            health['warnings'].append(f"Core module issue: {e}")

        # Check key dependencies
        required_deps = [
            ('pandas', 'Data processing'),
            ('requests', 'Web data fetching'),
            ('pulp', 'Optimization engine')
        ]

        for dep, purpose in required_deps:
            try:
                __import__(dep)
            except ImportError:
                health['dependencies_met'] = False
                health['missing_deps'].append(f"{dep} ({purpose})")

        return health

    def show_quick_menu(self) -> Optional[str]:
        """Show interactive menu for interface selection"""
        print(f"\n📋 AVAILABLE INTERFACES:")
        print("-" * 40)

        available_choices = []
        choice_num = 1

        for interface in self.available_interfaces:
            if interface['available']:
                print(f"{choice_num:2d}. {interface['description']}")
                available_choices.append(interface)
                choice_num += 1
            else:
                print(f" ❌ {interface['description']}")
                if 'error' in interface:
                    print(f"    {interface['error']}")

        # Add special options
        print(f"{choice_num:2d}. 💻 CLI with CSV file")
        csv_choice_num = choice_num
        choice_num += 1

        print(f"{choice_num:2d}. 🎮 Interactive CLI mode")
        interactive_choice_num = choice_num
        choice_num += 1

        print(f"{choice_num:2d}. 📊 System information")
        info_choice_num = choice_num
        choice_num += 1

        print(f" Q. ❌ Quit")

        # Show CSV files if available
        if self.csv_files:
            print(f"\n📄 RECENT CSV FILES FOUND:")
            for i, csv_file in enumerate(self.csv_files[:3], 1):
                file_path = Path(csv_file)
                size_kb = file_path.stat().st_size / 1024
                mod_time = time.ctime(file_path.stat().st_mtime)
                print(f"   {i}. {file_path.name} ({size_kb:.1f}KB, {mod_time})")

        print("-" * 40)

        while True:
            try:
                choice = input("Select option (1-{} or Q): ".format(choice_num)).strip().upper()

                if choice == 'Q':
                    return None

                choice_int = int(choice)

                if 1 <= choice_int <= len(available_choices):
                    # Launch selected interface
                    selected = available_choices[choice_int - 1]
                    print(f"\n🚀 Launching {selected['name']}...")
                    return selected['file']

                elif choice_int == csv_choice_num:
                    return self.handle_csv_choice()

                elif choice_int == interactive_choice_num:
                    return self.launch_interactive_cli()

                elif choice_int == info_choice_num:
                    return self.show_system_info()

                else:
                    print("❌ Invalid choice. Please try again.")

            except ValueError:
                print("❌ Please enter a number or Q to quit.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return None

    def handle_csv_choice(self) -> Optional[str]:
        """Handle CSV file selection for CLI"""
        if not self.csv_files:
            csv_path = input("Enter CSV file path: ").strip()
        else:
            print("\nSelect CSV file:")
            for i, csv_file in enumerate(self.csv_files, 1):
                print(f"{i:2d}. {Path(csv_file).name}")
            print(" 0. Enter custom path")

            try:
                choice = int(input("Choice: ").strip())
                if choice == 0:
                    csv_path = input("Enter CSV file path: ").strip()
                elif 1 <= choice <= len(self.csv_files):
                    csv_path = self.csv_files[choice - 1]
                else:
                    print("❌ Invalid choice")
                    return self.handle_csv_choice()
            except ValueError:
                print("❌ Please enter a number")
                return self.handle_csv_choice()

        # Launch CLI with CSV
        if csv_path and os.path.exists(csv_path):
            print(f"🚀 Launching CLI with {Path(csv_path).name}...")
            subprocess.run([sys.executable, "script.py", csv_path])
            return "script.py"
        else:
            print(f"❌ File not found: {csv_path}")
            return None

    def launch_interactive_cli(self) -> str:
        """Launch interactive CLI mode"""
        print("🚀 Launching Interactive CLI...")
        subprocess.run([sys.executable, "script.py", "--interactive"])
        return "script.py"

    def show_system_info(self) -> str:
        """Show system information"""
        print("\n📊 SYSTEM INFORMATION")
        print("=" * 60)

        health = self.check_system_health()

        print(f"Core Status: {'✅ Available' if health['core_available'] else '❌ Issues'}")
        print(f"Dependencies: {'✅ All installed' if health['dependencies_met'] else '❌ Missing some'}")

        if health['missing_deps']:
            print(f"\nMissing dependencies:")
            for dep in health['missing_deps']:
                print(f"  ❌ {dep}")

        if health['warnings']:
            print(f"\nWarnings:")
            for warning in health['warnings']:
                print(f"  ⚠️ {warning}")

        print(f"\nProject structure:")
        print(f"  📁 Root: {self.project_root}")
        print(f"  🖥️ Interfaces: {len(self.available_interfaces)} found")
        print(f"  📄 CSV files: {len(self.csv_files)} found")

        # Try to get core system status
        try:
            from bulletproof_dfs_core import BulletproofDFSCore
            core = BulletproofDFSCore()
            status = core.get_system_status()

            print(f"\nCore system:")
            print(f"  🎯 Mode: {'UNIFIED' if status['unified_mode'] else 'LEGACY'}")
            print(f"  📊 Modules: {sum(status['modules'].values())}/{len(status['modules'])} loaded")
            print(f"  ⚡ Ready: {'✅' if status['optimization_ready'] else '❌'}")

        except Exception as e:
            print(f"\nCore system: ❌ {e}")

        input("\nPress Enter to continue...")
        return ""

    def auto_launch(self) -> bool:
        """Auto-launch the best available interface"""
        # Try GUI first if available
        for interface in self.available_interfaces:
            if interface['available'] and interface['priority'] == 1:
                print(f"🚀 Auto-launching {interface['name']}...")
                subprocess.run(interface['command'])
                return True

        # Fall back to CLI
        for interface in self.available_interfaces:
            if interface['available'] and interface['priority'] == 2:
                print(f"🚀 Auto-launching {interface['name']} in interactive mode...")
                subprocess.run(interface['command'] + ["--interactive"])
                return True

        return False

    def run(self):
        """Main launcher logic"""
        self.print_header()

        # System health check
        health = self.check_system_health()
        if not health['core_available']:
            print("❌ Core system not available. Please check installation.")
            return

        if health['missing_deps']:
            print(f"\n⚠️ Missing dependencies: {', '.join(health['missing_deps'])}")
            print("Install with: pip install " + " ".join([dep.split()[0] for dep in health['missing_deps']]))

        # Detect available interfaces
        self.available_interfaces = self.detect_interfaces()
        self.csv_files = self.detect_csv_files()

        print(f"\n✅ Found {len([i for i in self.available_interfaces if i['available']])} available interfaces")
        if self.csv_files:
            print(f"✅ Found {len(self.csv_files)} CSV files")

        # Check for command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == '--auto':
                if self.auto_launch():
                    return
                else:
                    print("❌ No interfaces available for auto-launch")
            elif sys.argv[1] == '--cli':
                subprocess.run([sys.executable, "script.py", "--interactive"])
                return
            elif sys.argv[1] == '--gui':
                # Try to launch GUI
                for interface in self.available_interfaces:
                    if 'gui' in interface['file'].lower() and interface['available']:
                        subprocess.run(interface['command'])
                        return
                print("❌ GUI not available")
                return

        # Show interactive menu
        selected_file = self.show_quick_menu()

        if selected_file and selected_file.endswith('.py'):
            subprocess.run([sys.executable, selected_file])


def main():
    """Main entry point"""
    try:
        launcher = DFSLauncher()
        launcher.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Launcher error: {e}")
        print("Try running interfaces directly:")
        print("  python enhanced_dfs_gui.py")
        print("  python script.py --interactive")


if __name__ == "__main__":
    main()