#!/usr/bin/env python3
"""
DFS PROJECT HEALTH CHECK
========================
Comprehensive health check for your DFS optimizer
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import importlib.util


class DFSHealthCheck:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        self.critical_errors = []

    def run_all_checks(self):
        """Run all health checks"""
        print("🏥 DFS PROJECT HEALTH CHECK")
        print("=" * 60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # System checks
        self.check_python_version()
        self.check_required_modules()
        self.check_dependencies()

        # Data checks
        self.check_data_sources()
        self.check_cache_health()
        self.check_csv_files()

        # Performance checks
        self.check_optimization_speed()
        self.check_memory_usage()

        # Configuration checks
        self.check_configurations()

        # Show results
        self.show_results()

    def check_python_version(self):
        """Check Python version"""
        print("🐍 Checking Python version...")

        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
            self.checks_passed += 1
        else:
            print(f"   ❌ Python {version.major}.{version.minor} (3.8+ recommended)")
            self.checks_failed += 1
            self.warnings.append("Update Python to 3.8 or newer")

    def check_required_modules(self):
        """Check if all required modules are present"""
        print("\n📦 Checking core modules...")

        required_modules = {
            'unified_core_system': 'UnifiedCoreSystem',
            'unified_player_model': 'UnifiedPlayer',
            'unified_milp_optimizer': 'UnifiedMILPOptimizer',
            'unified_scoring_engine': 'get_scoring_engine',
            'simple_statcast_fetcher': 'FastStatcastFetcher',
            'smart_confirmation_system': 'SmartConfirmationSystem',
            'vegas_lines': 'VegasLines',
            'park_factors': 'get_park_factors',
            'enhanced_caching_system': 'get_cache_manager',
            'parallel_data_fetcher': 'ParallelDataFetcher'
        }

        missing = []
        for module, component in required_modules.items():
            try:
                spec = importlib.util.find_spec(module)
                if spec is not None:
                    self.checks_passed += 1
                else:
                    missing.append(module)
                    self.checks_failed += 1
            except:
                missing.append(module)
                self.checks_failed += 1

        if missing:
            print(f"   ❌ Missing modules: {', '.join(missing)}")
            self.critical_errors.append(f"Missing core modules: {', '.join(missing)}")
        else:
            print(f"   ✅ All {len(required_modules)} core modules present")

    def check_dependencies(self):
        """Check Python package dependencies"""
        print("\n📚 Checking dependencies...")

        try:
            import pandas
            import numpy
            import pulp
            print("   ✅ Core packages (pandas, numpy, pulp) installed")
            self.checks_passed += 1
        except ImportError as e:
            print(f"   ❌ Missing core package: {e}")
            self.checks_failed += 1
            self.critical_errors.append("Install requirements: pip install -r requirements.txt")

    def check_data_sources(self):
        """Test data source connections"""
        print("\n🌐 Checking data sources...")

        # Test statcast
        try:
            from simple_statcast_fetcher import FastStatcastFetcher
            fetcher = FastStatcastFetcher()
            print("   ✅ Statcast fetcher ready")
            self.checks_passed += 1
        except Exception as e:
            print(f"   ⚠️ Statcast issue: {str(e)[:50]}...")
            self.warnings.append("Statcast fetcher may have issues")

        # Test Vegas lines
        try:
            from vegas_lines import VegasLines
            vegas = VegasLines()
            print("   ✅ Vegas lines ready")
            self.checks_passed += 1
        except Exception as e:
            print(f"   ⚠️ Vegas lines issue: {str(e)[:50]}...")
            self.warnings.append("Vegas lines may have issues")

    def check_cache_health(self):
        """Check cache system health"""
        print("\n💾 Checking cache health...")

        cache_dirs = ['.gui_cache', 'data/cache', '.dfs_cache']
        total_size = 0

        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                size = sum(f.stat().st_size for f in Path(cache_dir).rglob('*') if f.is_file())
                total_size += size

                if size > 100 * 1024 * 1024:  # 100MB
                    self.warnings.append(f"{cache_dir} is large ({size / 1024 / 1024:.1f}MB)")

        print(f"   Total cache size: {total_size / 1024 / 1024:.1f}MB")

        if total_size > 500 * 1024 * 1024:  # 500MB
            print("   ⚠️ Cache is getting large, consider cleaning")
            self.warnings.append("Cache size exceeds 500MB")
        else:
            print("   ✅ Cache size is reasonable")
            self.checks_passed += 1

    def check_csv_files(self):
        """Check for CSV files"""
        print("\n📄 Checking for CSV files...")

        csv_files = list(Path('.').glob('*.csv'))
        sample_csv = list(Path('sample_data').glob('*.csv')) if Path('sample_data').exists() else []

        total_csv = len(csv_files) + len(sample_csv)

        if total_csv > 0:
            print(f"   ✅ Found {total_csv} CSV files")
            self.checks_passed += 1

            # Check if any are recent DraftKings files
            for csv in csv_files[:5]:
                mod_time = datetime.fromtimestamp(csv.stat().st_mtime)
                age_days = (datetime.now() - mod_time).days
                print(f"      • {csv.name} ({age_days} days old)")
        else:
            print("   ⚠️ No CSV files found")
            self.warnings.append("No CSV files found - download from DraftKings")

    def check_optimization_speed(self):
        """Test optimization speed"""
        print("\n⚡ Testing optimization speed...")

        try:
            from unified_core_system import UnifiedCoreSystem

            # Create small test
            start = time.time()
            system = UnifiedCoreSystem()
            init_time = time.time() - start

            print(f"   System initialization: {init_time:.2f}s")

            if init_time < 5:
                print("   ✅ Good initialization speed")
                self.checks_passed += 1
            else:
                print("   ⚠️ Slow initialization")
                self.warnings.append("System initialization is slow")

        except Exception as e:
            print(f"   ❌ Could not test: {e}")
            self.checks_failed += 1

    def check_memory_usage(self):
        """Check current memory usage"""
        print("\n🧠 Checking memory usage...")

        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            print(f"   Current usage: {memory_mb:.1f}MB")

            if memory_mb < 500:
                print("   ✅ Memory usage is good")
                self.checks_passed += 1
            else:
                print("   ⚠️ High memory usage")
                self.warnings.append(f"High memory usage: {memory_mb:.1f}MB")
        except:
            print("   ℹ️ Install psutil for memory monitoring")

    def check_configurations(self):
        """Check configuration files"""
        print("\n⚙️ Checking configurations...")

        configs = ['dfs_unified_config.json', 'cash_optimization_config.py']
        found = 0

        for config in configs:
            if os.path.exists(config):
                found += 1

                # Check if JSON is valid
                if config.endswith('.json'):
                    try:
                        with open(config) as f:
                            json.load(f)
                        print(f"   ✅ {config} - valid")
                    except:
                        print(f"   ❌ {config} - invalid JSON")
                        self.critical_errors.append(f"{config} has invalid JSON")
                else:
                    print(f"   ✅ {config} - found")

        if found > 0:
            self.checks_passed += 1
        else:
            print("   ⚠️ No configuration files found")
            self.warnings.append("No configuration files found")

    def show_results(self):
        """Show health check results"""
        print("\n" + "=" * 60)
        print("📊 HEALTH CHECK RESULTS")
        print("=" * 60)

        total_checks = self.checks_passed + self.checks_failed
        if total_checks > 0:
            health_score = (self.checks_passed / total_checks) * 100
        else:
            health_score = 0

        # Show score with color
        if health_score >= 80:
            status = "💚 HEALTHY"
        elif health_score >= 60:
            status = "💛 FAIR"
        else:
            status = "❤️ NEEDS ATTENTION"

        print(f"\nHealth Score: {health_score:.0f}% {status}")
        print(f"Checks passed: {self.checks_passed}/{total_checks}")

        if self.critical_errors:
            print(f"\n🚨 CRITICAL ERRORS ({len(self.critical_errors)}):")
            for error in self.critical_errors:
                print(f"   • {error}")

        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")

        if not self.critical_errors and not self.warnings:
            print("   ✅ Your DFS optimizer is in great shape!")
        else:
            if self.critical_errors:
                print("   1. Fix critical errors first")
            if any('cache' in w.lower() for w in self.warnings):
                print("   2. Run cleanup script to clear cache")
            if any('csv' in w.lower() for w in self.warnings):
                print("   3. Download fresh CSV from DraftKings")
            if any('memory' in w.lower() for w in self.warnings):
                print("   4. Restart the application to free memory")

        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'health_score': health_score,
            'checks_passed': self.checks_passed,
            'checks_failed': self.checks_failed,
            'warnings': self.warnings,
            'critical_errors': self.critical_errors
        }

        with open('health_check_report.json', 'w') as f:
            json.dump(report, f, indent=2)

        print("\n📄 Full report saved to: health_check_report.json")


if __name__ == "__main__":
    checker = DFSHealthCheck()
    checker.run_all_checks()