#!/usr/bin/env python3
"""
Essential Tools for DFS Optimizer Development
============================================
Run this to access various development and debugging tools
"""

import os
import sys
from datetime import datetime


def print_menu():
    """Display the tools menu"""
    print("\n" + "=" * 60)
    print("🛠️  DFS OPTIMIZER DEVELOPMENT TOOLS")
    print("=" * 60)
    print("\n📋 Available Tools:\n")

    tools = [
        ("1", "System Check", "Check all modules and components"),
        ("2", "Run Tests", "Run comprehensive integration tests"),
        ("3", "Performance Monitor", "Monitor system performance"),
        ("4", "Config Manager", "View/edit configuration"),
        ("5", "Cache Inspector", "Inspect and manage cache"),
        ("6", "Quick Optimizer Test", "Test optimization with sample data"),
        ("7", "Verify Fixes", "Verify all fixes are implemented"),
        ("8", "Code Formatter", "Format Python code (black)"),
        ("9", "Lint Check", "Check code quality (flake8)"),
        ("10", "Debug Mode", "Run optimizer in debug mode"),
        ("11", "Backup System", "Create full system backup"),
        ("12", "Health Check", "Check system health and errors"),
    ]

    for num, name, desc in tools:
        print(f"  {num:>2}. {name:<20} - {desc}")

    print(f"\n  {'Q':>2}. {'Quit':<20} - Exit tools")
    print("\n" + "-" * 60)


def run_system_check():
    """Run comprehensive system check"""
    print("\n🔍 Running System Check...")
    os.system("python check_system.py")

    # Additional checks
    print("\n📦 Checking installed packages...")
    required_packages = [
        "pandas", "numpy", "pulp", "requests",
        "beautifulsoup4", "pybaseball", "streamlit"
    ]

    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - Run: pip install {package}")


def run_tests():
    """Run all tests"""
    print("\n🧪 Running Tests...")

    # Check if test files exist
    test_files = [
        "test_enhanced_performance.py",
        "test_unified_config.py",
        "tests/test_integration_complete.py"
    ]

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📝 Running {test_file}...")
            os.system(f"python {test_file}")
        else:
            print(f"  ⚠️  {test_file} not found")


def performance_monitor():
    """Monitor system performance"""
    print("\n📊 Performance Monitor")

    try:
        from performance_optimizer import get_performance_optimizer
        optimizer = get_performance_optimizer()
        stats = optimizer.get_statistics()

        print("\n📈 Cache Statistics:")
        print(f"  Hit Rate: {stats['cache']['hit_rate']:.1%}")
        print(f"  Cache Size: {stats['cache']['size']}/{stats['cache']['max_size']}")
        print(f"  Total Operations: {stats['total_operations']}")

        if stats['slow_operations'] > 0:
            print(f"\n⚠️  Slow Operations Detected: {stats['slow_operations']}")

        print("\n📊 Operation Performance:")
        for func_name, perf in stats['operations'].items():
            print(f"  {func_name}:")
            print(f"    - Calls: {perf['count']}")
            print(f"    - Avg Time: {perf['avg_time']:.3f}s")
            print(f"    - Cache Hit Rate: {perf['cache_hit_rate']:.1%}")

    except Exception as e:
        print(f"  ❌ Error: {e}")


def config_manager():
    """Interactive configuration manager"""
    print("\n⚙️  Configuration Manager")

    try:
        from unified_config_manager import get_config_manager
        config = get_config_manager()

        while True:
            print("\n1. View configuration")
            print("2. Get config value")
            print("3. Set config value")
            print("4. Validate configuration")
            print("5. Save configuration")
            print("6. Back to main menu")

            choice = input("\nChoice: ").strip()

            if choice == "1":
                print("\n📋 Current Configuration:")
                print(f"  Salary Cap: ${config.get('optimization.salary_cap'):,}")
                print(f"  Min Salary Usage: {config.get('optimization.min_salary_usage'):.0%}")
                print(f"  Cache Enabled: {config.get('performance.cache_enabled')}")
                print(f"  Base Weight: {config.get('scoring.weights.base')}")

            elif choice == "2":
                key = input("Enter config key (e.g., optimization.salary_cap): ")
                value = config.get(key)
                print(f"  {key} = {value}")

            elif choice == "3":
                key = input("Enter config key: ")
                value = input("Enter new value: ")
                try:
                    # Try to parse as number
                    if '.' in value:
                        value = float(value)
                    elif value.isdigit():
                        value = int(value)
                    elif value.lower() in ['true', 'false']:
                        value = value.lower() == 'true'
                except:
                    pass

                config.set(key, value)
                print(f"  ✅ Set {key} = {value}")

            elif choice == "4":
                issues = config.validate()
                if issues:
                    print(f"  ⚠️  Validation issues: {issues}")
                else:
                    print("  ✅ Configuration is valid")

            elif choice == "5":
                config.save_config()
                print("  ✅ Configuration saved")

            elif choice == "6":
                break

    except Exception as e:
        print(f"  ❌ Error: {e}")


def cache_inspector():
    """Inspect and manage cache"""
    print("\n🔍 Cache Inspector")

    try:
        from performance_optimizer import get_performance_optimizer
        optimizer = get_performance_optimizer()

        while True:
            stats = optimizer.get_statistics()
            print(f"\n📊 Cache Status: {stats['cache']['size']} items")
            print(f"   Hit Rate: {stats['cache']['hit_rate']:.1%}")

            print("\n1. View cache statistics")
            print("2. Clear all cache")
            print("3. Clear category cache")
            print("4. Back to main menu")

            choice = input("\nChoice: ").strip()

            if choice == "1":
                print(f"\n  Total Hits: {optimizer._cache_stats['hits']}")
                print(f"  Total Misses: {optimizer._cache_stats['misses']}")
                print(f"  Evictions: {optimizer._cache_stats['evictions']}")

            elif choice == "2":
                optimizer.clear_cache()
                print("  ✅ Cache cleared")

            elif choice == "3":
                category = input("Enter category to clear: ")
                optimizer.clear_cache(category=category)
                print(f"  ✅ Cleared {category} cache")

            elif choice == "4":
                break

    except Exception as e:
        print(f"  ❌ Error: {e}")


def quick_test():
    """Quick optimization test"""
    print("\n🚀 Quick Optimization Test")

    csv_file = input("Enter CSV file path (or press Enter for test data): ").strip()

    if not csv_file:
        # Create test data
        print("  📝 Using test data...")
        csv_file = "test_players.csv"
        # You could create a small test CSV here

    os.system(f"python script.py {csv_file}")


def verify_fixes():
    """Verify all fixes are implemented"""
    print("\n✅ Verifying Fixes Implementation")
    os.system("python verify_fixes_script.py")


def format_code():
    """Format Python code with black"""
    print("\n🎨 Formatting Code...")

    try:
        import black
        os.system("black . --line-length 100 --exclude '.venv|backup_*'")
        print("  ✅ Code formatted")
    except ImportError:
        print("  ❌ Black not installed. Run: pip install black")


def lint_check():
    """Check code quality with flake8"""
    print("\n🔍 Running Lint Check...")

    try:
        import flake8
        os.system("flake8 . --max-line-length=100 --exclude=.venv,backup_* --count")
    except ImportError:
        print("  ❌ Flake8 not installed. Run: pip install flake8")


def debug_mode():
    """Run optimizer in debug mode"""
    print("\n🐛 Debug Mode")

    # Set debug environment variables
    os.environ['DFS_DEBUG'] = '1'
    os.environ['PYTHONUNBUFFERED'] = '1'

    csv_file = input("Enter CSV file path: ").strip()
    if csv_file:
        os.system(f"python -u script.py {csv_file}")


def backup_system():
    """Create full system backup"""
    print("\n💾 Creating System Backup...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_complete_{timestamp}"

    os.makedirs(backup_dir, exist_ok=True)

    # Files to backup
    important_files = [
        "*.py",
        "*.json",
        "*.csv",
        "requirements.txt",
        "README.md"
    ]

    import shutil
    import glob

    backed_up = 0
    for pattern in important_files:
        for file in glob.glob(pattern):
            if not file.startswith('backup_'):
                try:
                    shutil.copy2(file, backup_dir)
                    backed_up += 1
                except:
                    pass

    print(f"  ✅ Backed up {backed_up} files to {backup_dir}/")


def health_check():
    """System health check"""
    print("\n🏥 System Health Check")

    try:
        from enhanced_error_handling import RobustBulletproofCore
        core = RobustBulletproofCore()
        health = core.get_system_health()

        print(f"\n  Overall Status: {health['overall_status'].upper()}")
        print(f"  Error Rate: {health['error_rate']:.2f} errors/min")

        print("\n  Component Status:")
        for component, status in health['components'].items():
            icon = "✅" if status['status'] == 'healthy' else "❌"
            print(f"    {icon} {component}: {status['status']}")

        if health['recent_errors']:
            print("\n  Recent Errors:")
            for error in health['recent_errors'][-3:]:
                print(f"    - {error['time']}: {error['component']}.{error['operation']}")

    except Exception as e:
        print(f"  ❌ Health check not available: {e}")
        print("  ℹ️  Using basic check...")
        os.system("python check_system.py")


def main():
    """Main tool runner"""
    while True:
        print_menu()
        choice = input("Select tool (1-12 or Q): ").strip().upper()

        if choice == 'Q':
            print("\n👋 Goodbye!")
            break
        elif choice == '1':
            run_system_check()
        elif choice == '2':
            run_tests()
        elif choice == '3':
            performance_monitor()
        elif choice == '4':
            config_manager()
        elif choice == '5':
            cache_inspector()
        elif choice == '6':
            quick_test()
        elif choice == '7':
            verify_fixes()
        elif choice == '8':
            format_code()
        elif choice == '9':
            lint_check()
        elif choice == '10':
            debug_mode()
        elif choice == '11':
            backup_system()
        elif choice == '12':
            health_check()
        else:
            print("  ❌ Invalid choice")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    print("🚀 DFS Optimizer Development Tools")
    print("Version 1.0")
    main()