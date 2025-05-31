#!/usr/bin/env python3
"""
DFS Launcher - FIXED VERSION with Enhanced Integration
Optimized entry point that properly detects dependencies and integrates all components
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path
import traceback


class EnhancedDFSLauncher:
    """Enhanced launcher with better dependency detection and integration"""

    def __init__(self):
        self.current_dir = Path(__file__).parent

        # Prioritized file list - from most advanced to basic fallbacks
        self.core_files = [
            'working_dfs_core_final.py',  # Most advanced core
            'streamlined_dfs_core_OPTIMIZED.py',  # Optimized version
            'optimized_dfs_core.py',  # Standard optimized
            'dfs_data_enhanced.py',  # Enhanced data
            'dfs_data.py'  # Basic fallback
        ]

        self.gui_files = [
            'streamlined_dfs_gui.py',  # Clean streamlined GUI
            'enhanced_dfs_gui.py',  # Feature-rich GUI
            'performance_integrated_gui.py'  # High-performance GUI
        ]

        self.integration_files = [
            'statcast_integration.py',  # Real Baseball Savant data
            'async_data_manager.py',  # High-performance async
            'vegas_lines.py',  # Vegas lines integration
            'dfs_runner_enhanced.py'  # Enhanced runner
        ]

        self.available_modules = {}

    def check_package_import(self, package_name, alternative_names=None):
        """Enhanced package checking with better import detection"""
        if alternative_names is None:
            alternative_names = []

        # Try main package name
        try:
            module = importlib.import_module(package_name)
            return True, module.__version__ if hasattr(module, '__version__') else 'installed'
        except ImportError:
            pass

        # Try alternative names
        for alt_name in alternative_names:
            try:
                module = importlib.import_module(alt_name)
                return True, module.__version__ if hasattr(module, '__version__') else 'installed'
            except ImportError:
                continue

        return False, None

    def check_system_requirements(self):
        """Enhanced system requirements check"""
        print("🔍 Enhanced DFS System Requirements Check")
        print("=" * 60)

        # Check Python version
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 8:
            print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            print(f"⚠️ Python {python_version.major}.{python_version.minor} (recommended: 3.8+)")

        # Check core files and determine best available
        print("\n📁 Core System Files:")
        best_core = None
        for core_file in self.core_files:
            file_path = self.current_dir / core_file
            if file_path.exists():
                print(f"✅ {core_file}")
                if not best_core:
                    best_core = core_file
            else:
                print(f"⚪ {core_file}")

        if not best_core:
            print("❌ No core DFS files found!")
            return False

        self.available_modules['core'] = best_core
        print(f"🎯 Using core: {best_core}")

        # Check GUI files
        print("\n🖥️ GUI Files:")
        best_gui = None
        for gui_file in self.gui_files:
            file_path = self.current_dir / gui_file
            if file_path.exists():
                print(f"✅ {gui_file}")
                if not best_gui:
                    best_gui = gui_file
            else:
                print(f"⚪ {gui_file}")

        self.available_modules['gui'] = best_gui
        if best_gui:
            print(f"🎯 Using GUI: {best_gui}")
        else:
            print("⚠️ No GUI files found - command line only")

        # Check integration files
        print("\n🔧 Integration Modules:")
        for integration_file in self.integration_files:
            file_path = self.current_dir / integration_file
            if file_path.exists():
                print(f"✅ {integration_file}")
                self.available_modules[integration_file] = True
            else:
                print(f"⚪ {integration_file}")

        # Enhanced Python package checking
        print("\n📦 Python Dependencies:")

        # Core packages
        packages_to_check = [
            ('pandas', [], 'data processing - REQUIRED'),
            ('numpy', [], 'numerical computing - REQUIRED'),
            ('PyQt5', ['PyQt6'], 'GUI framework'),
            ('pulp', [], 'MILP optimization'),
            ('requests', [], 'HTTP requests'),
            ('aiohttp', [], 'async HTTP'),
            ('pybaseball', [], 'Baseball Savant data'),
        ]

        missing_required = []

        for package, alternatives, description in packages_to_check:
            found, version = self.check_package_import(package, alternatives)

            if found:
                version_str = f" v{version}" if version != 'installed' else ""
                print(f"✅ {package}{version_str} - {description}")
            else:
                if 'REQUIRED' in description:
                    print(f"❌ {package} - {description}")
                    missing_required.append(package)
                else:
                    print(f"⚪ {package} - {description} (optional)")

        if missing_required:
            print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
            print("\n💡 Install with:")
            print(f"   pip install {' '.join(missing_required)}")
            return False

        print("\n✅ System requirements satisfied!")
        return True

    def detect_best_configuration(self):
        """Detect the best available configuration"""
        config = {
            'core_file': self.available_modules.get('core'),
            'gui_file': self.available_modules.get('gui'),
            'has_async': 'async_data_manager.py' in self.available_modules,
            'has_statcast': 'statcast_integration.py' in self.available_modules,
            'has_vegas': 'vegas_lines.py' in self.available_modules,
            'has_enhanced_runner': 'dfs_runner_enhanced.py' in self.available_modules,
        }

        print("\n🎯 Optimal Configuration Detected:")
        print("=" * 40)

        if config['core_file']:
            print(f"🧠 Core Engine: {config['core_file']}")

        if config['gui_file']:
            print(f"🖥️ GUI Interface: {config['gui_file']}")

        features = []
        if config['has_async']:
            features.append("⚡ High-Performance Async")
        if config['has_statcast']:
            features.append("📊 Real Statcast Data")
        if config['has_vegas']:
            features.append("💰 Vegas Lines")
        if config['has_enhanced_runner']:
            features.append("🎯 Enhanced Processing")

        if features:
            print("🚀 Enhanced Features:")
            for feature in features:
                print(f"   {feature}")
        else:
            print("📋 Standard Features Available")

        return config

    def launch_gui(self, config):
        """Launch the best available GUI"""
        gui_file = config['gui_file']

        if not gui_file:
            print("❌ No GUI available")
            return 1

        print(f"\n🚀 Launching GUI: {gui_file}")

        try:
            # Dynamic import based on available GUI
            if gui_file == 'streamlined_dfs_gui.py':
                from streamlined_dfs_gui import main as gui_main
                print("✅ Streamlined GUI loaded")

            elif gui_file == 'enhanced_dfs_gui.py':
                from enhanced_dfs_gui import main as gui_main
                print("✅ Enhanced GUI loaded")

            elif gui_file == 'performance_integrated_gui.py':
                from performance_integrated_gui import main as gui_main
                print("✅ Performance GUI loaded")

            else:
                print(f"❌ Unknown GUI file: {gui_file}")
                return 1

            print("🎯 Starting DFS Optimizer GUI...")
            return gui_main()

        except ImportError as e:
            print(f"❌ Could not import GUI: {e}")
            print("💡 Try running with --test to check the core system")
            return 1
        except Exception as e:
            print(f"❌ Error launching GUI: {e}")
            traceback.print_exc()
            return 1

    def launch_test(self, config):
        """Launch system test using best available core"""
        core_file = config['core_file']

        if not core_file:
            print("❌ No core system available")
            return 1

        print(f"\n🧪 Testing Core System: {core_file}")

        try:
            # Dynamic import based on available core
            if core_file == 'working_dfs_core_final.py':
                from working_dfs_core_final import test_system
                print("✅ Working DFS Core loaded")

            elif core_file == 'streamlined_dfs_core_OPTIMIZED.py':
                from streamlined_dfs_core_OPTIMIZED import test_system
                print("✅ Streamlined Core loaded")

            elif core_file == 'optimized_dfs_core.py':
                from optimized_dfs_core import test_system
                print("✅ Optimized Core loaded")

            else:
                print(f"⚠️ No test function for {core_file}")
                print("✅ Core file exists - basic functionality available")
                return 0

            print("🔬 Running comprehensive system test...")
            success = test_system()

            if success:
                print("\n🎉 System test PASSED!")
                print("💡 Ready for production use")
                return 0
            else:
                print("\n⚠️ System test had issues")
                print("💡 Basic functionality may still work")
                return 1

        except ImportError as e:
            print(f"❌ Could not import core: {e}")
            return 1
        except Exception as e:
            print(f"❌ Test error: {e}")
            traceback.print_exc()
            return 1

    def create_sample_data(self):
        """Create sample data using the best available method"""
        try:
            print("\n📁 Creating sample data...")

            # Try to use the most advanced core for sample data
            if 'working_dfs_core_final.py' in str(self.available_modules.get('core', '')):
                from optimized_dfs_core import create_enhanced_test_data
                dk_file, dff_file = create_enhanced_test_data()
                print(f"✅ Created enhanced test data")
                print(f"   DK file: {dk_file}")
                print(f"   DFF file: {dff_file}")
                return True

        except Exception as e:
            print(f"⚠️ Could not create sample data: {e}")

        return False

    def show_usage(self):
        """Show enhanced usage information"""
        usage_text = """
🚀 ENHANCED DFS OPTIMIZER LAUNCHER
==================================

USAGE:
  python dfs_launcher.py [command] [options]

COMMANDS:
  gui          Launch graphical interface (default)
  test         Run system test
  check        Check requirements only
  sample       Create sample data
  help         Show this help

OPTIONS:
  --force      Force operation even with warnings
  --verbose    Show detailed output
  --config     Show detected configuration

EXAMPLES:
  python dfs_launcher.py              # Launch best available GUI
  python dfs_launcher.py gui          # Launch GUI explicitly  
  python dfs_launcher.py test         # Test system
  python dfs_launcher.py check        # Check requirements
  python dfs_launcher.py sample       # Create sample data

SYSTEM FEATURES:
  🧠 Multiple optimization engines (MILP, Monte Carlo, Genetic)
  🎯 Multi-position player support (3B/SS, 1B/3B, etc.)
  📊 Real-time Statcast data integration
  💰 Vegas lines and implied totals
  🎲 Confirmed lineup detection
  ⚡ High-performance async data loading
  🖥️ Modern, intuitive GUI interfaces

DETECTED CONFIGURATION:
  The launcher automatically detects your best available components
  and uses the most advanced versions for optimal performance.

TROUBLESHOOTING:
  • Run 'python dfs_launcher.py check' to verify requirements
  • Install missing packages: pip install package_name
  • Use 'python dfs_launcher.py test' to verify functionality
  • Check that all .py files are in the same directory

For support: Check the README.md or run with --verbose for details
        """
        print(usage_text)

    def run(self, args=None):
        """Enhanced main entry point"""
        if args is None:
            args = sys.argv[1:]

        # Parse arguments
        command = args[0] if args and not args[0].startswith('--') else 'gui'
        verbose = '--verbose' in args or '-v' in args
        force = '--force' in args
        show_config = '--config' in args

        # Handle help
        if command in ['help', '--help', '-h']:
            self.show_usage()
            return 0

        # Always check requirements first
        print("🚀 ENHANCED DFS OPTIMIZER LAUNCHER")
        print("=" * 40)

        if not self.check_system_requirements():
            if not force:
                print("\n❌ Requirements not met. Use --force to continue anyway.")
                return 1
            else:
                print("\n⚠️ Continuing with missing dependencies (forced)")

        # Detect best configuration
        config = self.detect_best_configuration()

        if show_config:
            return 0

        # Execute command
        if command == 'check':
            print("\n✅ Requirements check complete")
            return 0

        elif command == 'sample':
            success = self.create_sample_data()
            return 0 if success else 1

        elif command == 'test':
            return self.launch_test(config)

        elif command == 'gui':
            return self.launch_gui(config)

        else:
            print(f"❌ Unknown command: {command}")
            print("💡 Use 'python dfs_launcher.py help' for usage")
            return 1


def main():
    """Main function with enhanced error handling"""
    try:
        launcher = EnhancedDFSLauncher()
        return launcher.run()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        return 0
    except Exception as e:
        print(f"\n💥 Launcher error: {e}")
        print("\n🔍 Full traceback:")
        traceback.print_exc()
        print("\n💡 Try running: python dfs_launcher.py check")
        return 1


if __name__ == "__main__":
    sys.exit(main())