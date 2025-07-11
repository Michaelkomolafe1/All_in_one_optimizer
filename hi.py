#!/usr/bin/env python3
"""
DFS OPTIMIZER SYSTEM CHECK
=========================
Comprehensive verification of all modules and configurations
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple


# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")


def print_status(module: str, status: bool, message: str = ""):
    """Print module status with color coding"""
    if status:
        symbol = f"{Colors.GREEN}✅{Colors.END}"
        status_text = f"{Colors.GREEN}OK{Colors.END}"
    else:
        symbol = f"{Colors.RED}❌{Colors.END}"
        status_text = f"{Colors.RED}FAILED{Colors.END}"

    print(f"  {symbol} {module:<35} {status_text}", end="")
    if message:
        print(f" - {message}")
    else:
        print()


def check_imports() -> Dict[str, bool]:
    """Check all required imports"""
    print_header("CHECKING IMPORTS")

    imports_status = {}

    # Core imports
    core_imports = [
        ("unified_player_model", "UnifiedPlayer"),
        ("unified_milp_optimizer", "UnifiedMILPOptimizer"),
        ("unified_scoring_engine", "get_scoring_engine"),
        ("data_validator", "get_validator"),
        ("performance_optimizer", "get_performance_optimizer"),
        ("bulletproof_dfs_core", "BulletproofDFSCore"),
    ]

    # Optional imports
    optional_imports = [
        ("park_factors", "get_park_factors"),
        ("vegas_lines", "VegasLines"),
        ("smart_confirmation_system", "SmartConfirmationSystem"),
        ("simple_statcast_fetcher", "SimpleStatcastFetcher"),
        ("recent_form_analyzer", "RecentFormAnalyzer"),
        ("batting_order_correlation_system", "BattingOrderEnricher"),
        ("multi_lineup_optimizer", "MultiLineupOptimizer"),
        ("enhanced_stats_engine", "apply_enhanced_statistical_analysis"),
    ]

    print("\n📦 Core Modules:")
    for module_name, class_name in core_imports:
        try:
            module = __import__(module_name)
            if hasattr(module, class_name):
                imports_status[module_name] = True
                print_status(module_name, True)
            else:
                imports_status[module_name] = False
                print_status(module_name, False, f"Missing {class_name}")
        except ImportError as e:
            imports_status[module_name] = False
            print_status(module_name, False, str(e))

    print("\n📦 Optional Modules:")
    for module_name, class_name in optional_imports:
        try:
            module = __import__(module_name)
            if hasattr(module, class_name):
                imports_status[module_name] = True
                print_status(module_name, True)
            else:
                imports_status[module_name] = False
                print_status(module_name, False, f"Missing {class_name}")
        except ImportError:
            imports_status[module_name] = False
            print_status(module_name, False, "Not installed")

    return imports_status


def check_core_initialization() -> Tuple[bool, object]:
    """Check if BulletproofDFSCore initializes properly"""
    print_header("CORE INITIALIZATION")

    try:
        from bulletproof_dfs_core import BulletproofDFSCore

        print("🚀 Initializing BulletproofDFSCore...")
        core = BulletproofDFSCore()

        # Check key attributes
        attributes_to_check = [
            ("salary_cap", lambda x: x == 50000, "Should be 50000"),
            ("players", lambda x: isinstance(x, list), "Should be a list"),
            ("scoring_engine", lambda x: x is not None, "Should be initialized"),
            ("validator", lambda x: x is not None, "Should be initialized"),
            ("performance_optimizer", lambda x: x is not None, "Should be initialized"),
        ]

        print("\n🔍 Checking core attributes:")
        all_good = True

        for attr_name, check_func, expected in attributes_to_check:
            if hasattr(core, attr_name):
                attr_value = getattr(core, attr_name)
                if check_func(attr_value):
                    print_status(attr_name, True)
                else:
                    print_status(attr_name, False, expected)
                    all_good = False
            else:
                print_status(attr_name, False, "Not found")
                all_good = False

        # Check optimization modules
        print("\n🔧 Checking optimization modules:")
        opt_modules = [
            ("scoring_engine", "Unified Scoring Engine"),
            ("validator", "Data Validator"),
            ("performance_optimizer", "Performance Optimizer"),
            ("park_factors", "Park Factors"),
            ("vegas_lines", "Vegas Lines"),
            ("statcast_fetcher", "Statcast Fetcher"),
            ("confirmation_system", "Confirmation System"),
            ("form_analyzer", "Form Analyzer"),
        ]

        for attr_name, display_name in opt_modules:
            if hasattr(core, attr_name) and getattr(core, attr_name) is not None:
                print_status(display_name, True)
            else:
                print_status(display_name, False, "Not initialized")

        return all_good, core

    except Exception as e:
        print(f"{Colors.RED}❌ Failed to initialize core: {e}{Colors.END}")
        return False, None


def check_scoring_engine(core) -> bool:
    """Test the unified scoring engine"""
    print_header("SCORING ENGINE TEST")

    try:
        from unified_player_model import UnifiedPlayer

        # Create test player
        test_player = UnifiedPlayer(
            id="test1",
            name="Test Player",
            team="NYY",
            salary=5000,
            primary_position="OF",
            positions=["OF"],
            base_projection=10.0
        )

        print("🧪 Testing scoring engine with test player...")

        # Test basic scoring
        if hasattr(core, 'scoring_engine') and core.scoring_engine:
            score = core.scoring_engine.calculate_score(test_player)
            print(f"  Base score: {test_player.base_projection}")
            print(f"  Enhanced score: {score}")

            # Check if score audit exists
            if hasattr(test_player, '_score_audit'):
                print_status("Score audit trail", True)
                audit = test_player._score_audit
                print(f"\n  📊 Score components:")
                for comp_name, comp_data in audit.get('components', {}).items():
                    print(f"    - {comp_name}: {comp_data.get('contribution', 0):.2f} "
                          f"({comp_data.get('multiplier', 1.0):.2f}x @ "
                          f"{comp_data.get('weight', 0):.1%})")
            else:
                print_status("Score audit trail", False, "Not generated")

            # Test with data
            print("\n🧪 Testing with enriched data...")
            test_player._vegas_data = {'implied_total': 5.5}
            test_player.batting_order = 3

            score2 = core.scoring_engine.calculate_score(test_player)
            print(f"  Score with Vegas + batting order: {score2:.2f}")

            improvement = (score2 - score) / score * 100 if score > 0 else 0
            print(f"  Improvement: {improvement:+.1f}%")

            return True
        else:
            print_status("Scoring engine", False, "Not available")
            return False

    except Exception as e:
        print(f"{Colors.RED}❌ Scoring engine test failed: {e}{Colors.END}")
        return False


def check_data_sources(core) -> Dict[str, bool]:
    """Check availability of data sources"""
    print_header("DATA SOURCES")

    sources_status = {}

    # Vegas Lines
    if hasattr(core, 'vegas_lines') and core.vegas_lines:
        try:
            lines = core.vegas_lines.lines
            sources_status['vegas'] = len(lines) > 0
            print_status("Vegas Lines", True, f"{len(lines)} teams loaded")
        except:
            sources_status['vegas'] = False
            print_status("Vegas Lines", False, "No data")
    else:
        sources_status['vegas'] = False
        print_status("Vegas Lines", False, "Not initialized")

    # Statcast
    if hasattr(core, 'statcast_fetcher') and core.statcast_fetcher:
        try:
            # Test connection
            result = core.statcast_fetcher.test_connection() if hasattr(core.statcast_fetcher,
                                                                        'test_connection') else False
            sources_status['statcast'] = result
            print_status("Statcast API", result)
        except:
            sources_status['statcast'] = False
            print_status("Statcast API", False, "Connection failed")
    else:
        sources_status['statcast'] = False
        print_status("Statcast API", False, "Not initialized")

    # Park Factors
    if hasattr(core, 'park_factors') and core.park_factors:
        try:
            # Test a known park
            factor = core.park_factors.get_factor("COL")
            sources_status['park_factors'] = factor == 1.20  # Coors Field
            print_status("Park Factors", True, f"Coors Field factor: {factor}")
        except:
            sources_status['park_factors'] = False
            print_status("Park Factors", False, "Not working")
    else:
        sources_status['park_factors'] = False
        print_status("Park Factors", False, "Not initialized")

    return sources_status


def check_optimization_config() -> bool:
    """Check optimization configuration"""
    print_header("CONFIGURATION")

    try:
        import json
        import os

        config_files = [
            "optimization_config.json",
            "dfs_config.json",
        ]

        config_found = False
        for config_file in config_files:
            if os.path.exists(config_file):
                print_status(config_file, True)

                # Load and check config
                with open(config_file, 'r') as f:
                    config = json.load(f)

                # Check scoring weights
                if 'scoring' in config and 'weights' in config['scoring']:
                    weights = config['scoring']['weights']
                    total = sum(weights.values())
                    if abs(total - 1.0) < 0.001:
                        print(f"  ✅ Scoring weights sum to 1.0")
                    else:
                        print(f"  ⚠️  Scoring weights sum to {total:.3f} (should be 1.0)")

                config_found = True
                break

        if not config_found:
            print_status("Configuration file", False, "No config file found")

        return config_found

    except Exception as e:
        print(f"{Colors.RED}❌ Config check failed: {e}{Colors.END}")
        return False


def run_quick_optimization_test(core) -> bool:
    """Run a quick optimization test"""
    print_header("OPTIMIZATION TEST")

    try:
        from unified_player_model import UnifiedPlayer

        # Create test players
        test_players = []
        positions = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'OF', 'OF']

        for i, pos in enumerate(positions):
            player = UnifiedPlayer(
                id=f"test{i}",
                name=f"Test Player {i}",
                team="NYY" if i % 2 == 0 else "BOS",
                salary=4000 + (i * 500),
                primary_position=pos,
                positions=[pos],
                base_projection=8.0 + (i * 0.5)
            )
            player.is_confirmed = True
            test_players.append(player)

        print(f"🎮 Created {len(test_players)} test players")

        # Set players
        core.players = test_players

        # Try optimization
        print("🎯 Running test optimization...")
        lineup, score = core.optimize_lineup_with_mode()

        if lineup and len(lineup) > 0:
            print_status("Optimization", True, f"Score: {score:.2f}")
            print(f"\n📋 Test Lineup:")
            total_salary = 0
            for p in lineup:
                print(f"  {p.primary_position:>3} {p.name:<15} ${p.salary:,}")
                total_salary += p.salary
            print(f"  Total: ${total_salary:,} / $50,000")
            return True
        else:
            print_status("Optimization", False, "No lineup generated")
            return False

    except Exception as e:
        print(f"{Colors.RED}❌ Optimization test failed: {e}{Colors.END}")
        return False


def generate_report(results: Dict) -> None:
    """Generate final report"""
    print_header("SYSTEM CHECK REPORT")

    total_checks = len(results)
    passed_checks = sum(1 for v in results.values() if v)

    print(f"\n📊 Overall Status: {passed_checks}/{total_checks} checks passed")

    percentage = (passed_checks / total_checks) * 100

    if percentage == 100:
        print(f"\n{Colors.GREEN}🎉 PERFECT! Your DFS optimizer is fully configured!{Colors.END}")
    elif percentage >= 80:
        print(f"\n{Colors.GREEN}✅ GOOD! Your optimizer is ready with minor issues.{Colors.END}")
    elif percentage >= 60:
        print(f"\n{Colors.YELLOW}⚠️  OK - Your optimizer works but needs some fixes.{Colors.END}")
    else:
        print(f"\n{Colors.RED}❌ NEEDS WORK - Several critical components are missing.{Colors.END}")

    # Recommendations
    if percentage < 100:
        print(f"\n{Colors.BOLD}📝 Recommendations:{Colors.END}")

        if not results.get('scoring_engine', False):
            print("  1. Fix scoring engine initialization in __init__ method")

        if not results.get('park_factors', False):
            print("  2. Ensure park_factors module is properly integrated")

        if not results.get('config', False):
            print("  3. Create optimization_config.json with proper settings")

        if not results.get('vegas', False):
            print("  4. Check Vegas API key and connection")


def main():
    """Run complete system check"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           DFS OPTIMIZER SYSTEM CHECK v1.0                ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")

    print(f"🕐 Check started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # 1. Check imports
    import_results = check_imports()
    results['imports'] = all(v for k, v in import_results.items()
                             if k in ['unified_player_model', 'unified_milp_optimizer',
                                      'unified_scoring_engine', 'bulletproof_dfs_core'])

    # 2. Check core initialization
    init_ok, core = check_core_initialization()
    results['initialization'] = init_ok

    if core:
        # 3. Check scoring engine
        results['scoring_engine'] = check_scoring_engine(core)

        # 4. Check data sources
        data_results = check_data_sources(core)
        results['data_sources'] = any(data_results.values())

        # 5. Check park factors specifically
        results['park_factors'] = data_results.get('park_factors', False)

        # 6. Run optimization test
        results['optimization'] = run_quick_optimization_test(core)

    # 7. Check configuration
    results['config'] = check_optimization_config()

    # Generate report
    generate_report(results)

    print(f"\n🏁 Check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()