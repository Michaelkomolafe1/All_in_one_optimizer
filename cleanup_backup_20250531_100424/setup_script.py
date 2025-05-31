#!/usr/bin/env python3
"""
DFS System Setup Script
Automatically installs dependencies and validates the environment
"""

import subprocess
import sys
import os
import importlib
from pathlib import Path


class DFSSetupManager:
    """Manages DFS system setup and dependencies"""

    def __init__(self):
        self.required_packages = {
            'PyQt5': 'PyQt5>=5.15.0',
            'pandas': 'pandas>=1.3.0',
            'numpy': 'numpy>=1.21.0',
            'aiohttp': 'aiohttp>=3.8.0',
            'aiofiles': 'aiofiles>=0.8.0',
            'pulp': 'pulp>=2.6.0',
            'requests': 'requests>=2.28.0'
        }

        self.optional_packages = {
            'pybaseball': 'pybaseball>=2.2.0',  # For real Baseball Savant data
            'plotly': 'plotly>=5.0.0',  # For advanced visualizations
            'dash': 'dash>=2.0.0'  # For web-based dashboards
        }

        self.required_files = [
            'unified_player_model.py',
            'optimized_data_pipeline.py',
            'unified_milp_optimizer.py'
        ]

        self.installation_log = []

    def run_complete_setup(self):
        """Run complete setup process"""
        print("🚀 DFS SYSTEM SETUP")
        print("=" * 40)

        # Step 1: Check Python version
        self.check_python_version()

        # Step 2: Check required files
        self.check_required_files()

        # Step 3: Install required packages
        self.install_required_packages()

        # Step 4: Install optional packages
        self.install_optional_packages()

        # Step 5: Validate installation
        self.validate_installation()

        # Step 6: Create sample data
        self.create_sample_data()

        # Step 7: Generate setup report
        self.generate_setup_report()

        print("\n🎉 SETUP COMPLETE!")
        print("🚀 Run 'python auto_integration_script.py' to integrate")

    def check_python_version(self):
        """Check if Python version is compatible"""
        print("\n🐍 Checking Python version...")

        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            print(f"  ✅ Python {version.major}.{version.minor}.{version.micro} (compatible)")
        elif version.major == 3 and version.minor >= 6:
            print(f"  ⚠️ Python {version.major}.{version.minor}.{version.micro} (may work, but 3.8+ recommended)")
        else:
            print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (too old)")
            print("💡 Please upgrade to Python 3.8 or newer")
            sys.exit(1)

    def check_required_files(self):
        """Check if required unified system files exist"""
        print("\n📁 Checking required files...")

        missing_files = []
        for file_name in self.required_files:
            if os.path.exists(file_name):
                print(f"  ✅ Found: {file_name}")
            else:
                print(f"  ❌ Missing: {file_name}")
                missing_files.append(file_name)

        if missing_files:
            print(f"\n❌ Missing required files: {', '.join(missing_files)}")
            print("💡 Please save the 3 artifacts from the conversation first!")
            print("💡 They should be named exactly:")
            for file_name in self.required_files:
                print(f"   - {file_name}")
            sys.exit(1)

    def install_required_packages(self):
        """Install required Python packages"""
        print("\n📦 Installing required packages...")

        for package_name, package_spec in self.required_packages.items():
            try:
                # Check if already installed
                importlib.import_module(package_name.lower().replace('-', '_'))
                print(f"  ✅ {package_name}: Already installed")
                self.installation_log.append(f"{package_name}: Already installed")
            except ImportError:
                print(f"  🔄 Installing {package_name}...")
                success = self.install_package(package_spec)
                if success:
                    print(f"  ✅ {package_name}: Installed successfully")
                    self.installation_log.append(f"{package_name}: Installed successfully")
                else:
                    print(f"  ❌ {package_name}: Installation failed")
                    self.installation_log.append(f"{package_name}: Installation failed")

    def install_optional_packages(self):
        """Install optional packages for enhanced functionality"""
        print("\n📦 Installing optional packages...")

        for package_name, package_spec in self.optional_packages.items():
            try:
                importlib.import_module(package_name.lower())
                print(f"  ✅ {package_name}: Already installed")
                self.installation_log.append(f"{package_name}: Already installed (optional)")
            except ImportError:
                print(f"  🔄 Installing {package_name} (optional)...")
                success = self.install_package(package_spec)
                if success:
                    print(f"  ✅ {package_name}: Installed successfully")
                    self.installation_log.append(f"{package_name}: Installed successfully (optional)")
                else:
                    print(f"  ⚠️ {package_name}: Installation failed (optional, can continue)")
                    self.installation_log.append(f"{package_name}: Installation failed (optional)")

    def install_package(self, package_spec):
        """Install a single package using pip"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_spec],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"    ⏰ Installation timeout for {package_spec}")
            return False
        except Exception as e:
            print(f"    ❌ Installation error: {e}")
            return False

    def validate_installation(self):
        """Validate that all installations work correctly"""
        print("\n🔍 Validating installation...")

        validation_results = {}

        # Test core packages
        core_tests = {
            'pandas': lambda: __import__('pandas').DataFrame({'test': [1, 2, 3]}),
            'numpy': lambda: __import__('numpy').array([1, 2, 3]),
            'PyQt5': lambda: __import__('PyQt5.QtWidgets'),
            'aiohttp': lambda: __import__('aiohttp'),
            'pulp': lambda: __import__('pulp')
        }

        for package, test_func in core_tests.items():
            try:
                test_func()
                print(f"  ✅ {package}: Working correctly")
                validation_results[package] = "✅ Working"
            except Exception as e:
                print(f"  ❌ {package}: Validation failed - {e}")
                validation_results[package] = f"❌ Failed: {e}"

        # Test unified system components
        unified_tests = {
            'unified_player_model': 'from unified_player_model import UnifiedPlayer',
            'optimized_data_pipeline': 'from optimized_data_pipeline import OptimizedDataPipeline',
            'unified_milp_optimizer': 'from unified_milp_optimizer import optimize_with_unified_system'
        }

        for component, import_test in unified_tests.items():
            try:
                exec(import_test)
                print(f"  ✅ {component}: Import successful")
                validation_results[component] = "✅ Working"
            except Exception as e:
                print(f"  ❌ {component}: Import failed - {e}")
                validation_results[component] = f"❌ Failed: {e}"

        return validation_results

    def create_sample_data(self):
        """Create sample DraftKings and DFF data for testing"""
        print("\n📊 Creating sample data...")

        # Create sample directory
        sample_dir = Path("sample_data")
        sample_dir.mkdir(exist_ok=True)

        # Sample DraftKings CSV
        dk_sample = sample_dir / "sample_draftkings.csv"
        dk_content = """Name,Position,TeamAbbrev,Salary,AvgPointsPerGame,Game Info
Hunter Brown,P,HOU,9800,24.56,HOU@TEX
Shane Baz,P,TB,8200,19.23,TB@BOS
Logan Gilbert,P,SEA,7600,18.45,SEA@LAA
Freddy Peralta,P,MIL,8800,21.78,MIL@CHC
Ronel Blanco,P,HOU,7000,16.89,HOU@TEX
William Contreras,C,MIL,4200,7.39,MIL@CHC
Salvador Perez,C,KC,3800,6.85,KC@CLE
Tyler Stephenson,C,CIN,3200,6.12,CIN@PIT
Vladimir Guerrero Jr.,1B,TOR,4200,7.66,TOR@NYY
Pete Alonso,1B,NYM,4000,7.23,NYM@ATL
Josh Bell,1B,MIA,3600,6.45,MIA@WSH
Yandy Diaz,1B/3B,TB,3800,6.78,TB@BOS
Gleyber Torres,2B,NYY,4000,6.89,TOR@NYY
Jose Altuve,2B,HOU,3900,7.12,HOU@TEX
Andres Gimenez,2B,CLE,3600,6.34,KC@CLE
Jorge Polanco,3B/SS,SEA,3800,6.95,SEA@LAA
Manny Machado,3B,SD,4200,7.45,SD@LAD
Jose Ramirez,3B,CLE,4100,8.12,KC@CLE
Alex Bregman,3B,HOU,4000,7.23,HOU@TEX
Francisco Lindor,SS,NYM,4300,8.23,NYM@ATL
Trea Turner,SS,PHI,4100,7.89,PHI@WAS
Bo Bichette,SS,TOR,3700,6.67,TOR@NYY
Corey Seager,SS,TEX,4000,7.34,HOU@TEX
Kyle Tucker,OF,HOU,4500,8.45,HOU@TEX
Christian Yelich,OF,MIL,4200,7.65,MIL@CHC
Jarren Duran,OF,BOS,4100,7.89,TB@BOS
Byron Buxton,OF,MIN,3900,7.12,DET@MIN
Seiya Suzuki,OF,CHC,3800,6.78,MIL@CHC
Jesse Winker,OF,NYM,3600,6.23,NYM@ATL
Wilyer Abreu,OF,BOS,3500,6.45,TB@BOS
Jackson Chourio,OF,MIL,3400,5.89,MIL@CHC
Lane Thomas,OF,CLE,3300,5.67,KC@CLE"""

        with open(dk_sample, 'w') as f:
            f.write(dk_content)

        # Sample DFF CSV
        dff_sample = sample_dir / "sample_dff.csv"
        dff_content = """first_name,last_name,team,ppg_projection,value_projection,L5_fppg_avg,confirmed_order,implied_team_score,over_under
Hunter,Brown,HOU,26.5,2.32,28.2,YES,5.2,9.5
Shane,Baz,TB,21.8,2.22,19.1,YES,4.8,8.5
Logan,Gilbert,SEA,20.2,2.15,18.9,YES,4.6,8.0
Kyle,Tucker,HOU,9.8,1.96,10.2,YES,5.2,9.5
Christian,Yelich,MIL,8.9,1.93,9.4,YES,4.9,9.0
Vladimir,Guerrero Jr.,TOR,8.5,1.77,7.8,YES,4.7,8.5
Francisco,Lindor,NYM,9.2,1.88,8.9,YES,4.8,8.5
Jose,Ramirez,CLE,9.1,1.90,9.8,YES,4.5,8.0
Jorge,Polanco,SEA,7.8,1.73,7.2,YES,4.6,8.0
Jarren,Duran,BOS,8.7,1.81,9.1,YES,4.8,8.5
William,Contreras,MIL,8.2,1.75,7.9,YES,4.9,9.0
Gleyber,Torres,NYY,7.6,1.69,7.1,YES,5.1,9.0"""

        with open(dff_sample, 'w') as f:
            f.write(dff_content)

        print(f"  ✅ Created sample_data/sample_draftkings.csv")
        print(f"  ✅ Created sample_data/sample_dff.csv")
        print(f"  💡 Use these files to test the system!")

    def generate_setup_report(self):
        """Generate a setup report"""
        print("\n📊 Generating setup report...")

        report_content = f"""# DFS System Setup Report
Generated: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}

## Python Environment
- Version: {sys.version}
- Executable: {sys.executable}

## Installation Log
{chr(10).join('- ' + log for log in self.installation_log)}

## Required Files Status
{chr(10).join('- ' + ('✅' if os.path.exists(f) else '❌') + f' {f}' for f in self.required_files)}

## Sample Data Created
- sample_data/sample_draftkings.csv
- sample_data/sample_dff.csv

## Next Steps
1. Run integration: python auto_integration_script.py
2. Test system: python test_integration.py
3. Launch GUI: python launch_dfs_optimizer.py

## Quick Test Commands
```bash
# Test with sample data
python dfs_cli.py --dk sample_data/sample_draftkings.csv --dff sample_data/sample_dff.csv --strategy smart_confirmed

# Test manual selection
python dfs_cli.py --dk sample_data/sample_draftkings.csv --manual "Jorge Polanco, Christian Yelich, Hunter Brown"

# Test confirmed only strategy
python dfs_cli.py --dk sample_data/sample_draftkings.csv --dff sample_data/sample_dff.csv --strategy confirmed_only
```

## Troubleshooting
If you encounter issues:
1. Make sure Python 3.8+ is installed
2. Check that all required files are saved
3. Try running setup again: python setup_script.py
4. For GUI issues, install PyQt5: pip install PyQt5
"""

        with open('SETUP_REPORT.md', 'w') as f:
            f.write(report_content)

        print("  ✅ Created SETUP_REPORT.md")


def main():
    """Main setup function"""
    try:
        setup_manager = DFSSetupManager()
        setup_manager.run_complete_setup()
        return True
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)