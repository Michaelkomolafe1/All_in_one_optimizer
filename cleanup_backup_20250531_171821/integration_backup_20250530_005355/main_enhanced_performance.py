#!/usr/bin/env python3
"""
Enhanced Main Launcher with High-Performance Integration
Automatically detects and uses the best available optimization system
"""

import sys
import os
import argparse
import time
from pathlib import Path

def check_performance_system():
    """Check what performance systems are available"""
    systems = {
        'async_data': False,
        'performance_data': False,
        'enhanced_gui': False,
        'milp_optimizer': False
    }

    # Check async data manager
    try:
        from async_data_manager import load_high_performance_data
        systems['async_data'] = True
    except ImportError:
        pass

    # Check performance integrated data
    try:
        from performance_integrated_data import SuperEnhancedDFSData
        systems['performance_data'] = True
    except ImportError:
        pass

    # Check enhanced GUI
    try:
        from performance_integrated_gui import HighPerformanceDFSGUI
        systems['enhanced_gui'] = True
    except ImportError:
        try:
            from enhanced_dfs_gui import ModernDFSGUI
            systems['enhanced_gui'] = True
        except ImportError:
            pass

    # Check MILP optimizer
    try:
        import pulp
        systems['milp_optimizer'] = True
    except ImportError:
        pass

    return systems

def launch_best_gui():
    """Launch the best available GUI"""
    print("🚀 Launching Enhanced DFS Optimizer...")

    systems = check_performance_system()

    try:
        # Try performance integrated GUI first
        if systems['enhanced_gui']:
            try:
                from performance_integrated_gui import HighPerformanceDFSGUI, main as gui_main
                print("✅ Using High-Performance GUI")
                return gui_main()
            except ImportError:
                pass

        # Fallback to enhanced GUI
        try:
            from enhanced_dfs_gui import ModernDFSGUI, main as gui_main
            print("✅ Using Enhanced GUI")
            return gui_main()
        except ImportError:
            pass

        # Last resort fallback
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)

            msg = QMessageBox()
            msg.setWindowTitle("DFS Optimizer")
            msg.setText("GUI components not found. Please run setup first.")
            msg.exec_()

            return 1

        except ImportError:
            print("❌ No GUI system available")
            return 1

    except Exception as e:
        print(f"❌ GUI launch failed: {e}")
        return 1

def launch_cli(args):
    """Launch CLI with best available system"""
    print("🔧 Launching High-Performance CLI...")

    systems = check_performance_system()

    if not args.dk:
        print("❌ DraftKings CSV file required")
        print("Usage: python main_enhanced_performance.py --cli --dk your_file.csv")
        return 1

    if not os.path.exists(args.dk):
        print(f"❌ File not found: {args.dk}")
        return 1

    try:
        # Try async high-performance loading
        if systems['async_data']:
            print("⚡ Using high-performance async data loading...")
            import asyncio
            from async_data_manager import load_high_performance_data

            start_time = time.time()
            players = asyncio.run(load_high_performance_data(args.dk, args.force_refresh))
            load_time = time.time() - start_time

            print(f"✅ Loaded {len(players)} players in {load_time:.2f} seconds")

        # Try performance integrated system
        elif systems['performance_data']:
            print("🚀 Using performance integrated data system...")
            from performance_integrated_data import load_dfs_data

            start_time = time.time()
            players, dfs_data = load_dfs_data(args.dk, args.force_refresh)
            load_time = time.time() - start_time

            print(f"✅ Loaded {len(players)} players in {load_time:.2f} seconds")

        # Fallback to standard system
        else:
            print("⚠️ Using standard data loading...")
            try:
                from dfs_data_enhanced import load_dfs_data
                players, dfs_data = load_dfs_data(args.dk, args.force_refresh)
            except ImportError:
                from dfs_data_enhanced import DFSData
                dfs_data = DFSData()
                if dfs_data.import_from_draftkings(args.dk):
                    players = dfs_data.generate_enhanced_player_data(args.force_refresh)
                else:
                    players = None

        if not players:
            print("❌ Failed to load player data")
            return 1

        # Run optimization
        print("🧠 Running optimization...")

        try:
            from dfs_optimizer_enhanced import optimize_lineup_milp, optimize_lineup, display_lineup

            if args.milp and systems['milp_optimizer']:
                print("🧠 Using MILP optimization...")
                lineup, score = optimize_lineup_milp(players, budget=args.budget, min_salary=args.min_salary)
            else:
                print("🎲 Using Monte Carlo optimization...")
                lineup, score = optimize_lineup(players, budget=args.budget, num_attempts=args.attempts, min_salary=args.min_salary)

            if lineup:
                print("\n" + "="*60)
                print(display_lineup(lineup, verbose=args.verbose))
                print(f"\n🎯 Optimal Score: {score:.2f}")
                print("="*60)

                if args.export:
                    export_lineup(lineup, args.export)

                return 0
            else:
                print("❌ No valid lineup found")
                return 1

        except ImportError:
            print("❌ Optimization modules not available")
            return 1

    except Exception as e:
        print(f"❌ CLI optimization failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def export_lineup(lineup, filename):
    """Export lineup to CSV"""
    try:
        import csv
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Position', 'Player', 'Team', 'Salary', 'Score'])
            for player in lineup:
                writer.writerow([
                    player[2], player[1], player[3], 
                    player[4], player[6] if len(player) > 6 else 0
                ])
        print(f"✅ Lineup exported to {filename}")
    except Exception as e:
        print(f"⚠️ Export failed: {e}")

def show_system_status():
    """Show system status and performance capabilities"""
    print("🔍 SYSTEM STATUS")
    print("=" * 50)

    systems = check_performance_system()

    print("📦 PERFORMANCE SYSTEMS:")
    print(f"  ⚡ Async Data Loading: {'✅ Available' if systems['async_data'] else '❌ Not Available'}")
    print(f"  🚀 Performance Integration: {'✅ Available' if systems['performance_data'] else '❌ Not Available'}")
    print(f"  🖥️ Enhanced GUI: {'✅ Available' if systems['enhanced_gui'] else '❌ Not Available'}")
    print(f"  🧠 MILP Optimization: {'✅ Available' if systems['milp_optimizer'] else '❌ Not Available'}")

    # Performance estimate
    if systems['async_data'] and systems['milp_optimizer']:
        print("\n⚡ PERFORMANCE ESTIMATE:")
        print("  📊 Data Loading: ~15-30 seconds (10x improvement)")
        print("  🧠 Optimization: ~5-10 seconds") 
        print("  💾 Subsequent Loads: ~2-5 seconds (cached)")
        print("  🎯 Total Time: ~20-45 seconds (vs 4-6 minutes standard)")
    elif systems['performance_data']:
        print("\n🚀 PERFORMANCE ESTIMATE:")
        print("  📊 Data Loading: ~30-60 seconds (5x improvement)")
        print("  🧠 Optimization: ~10-20 seconds")
        print("  💾 Subsequent Loads: ~10-15 seconds")
        print("  🎯 Total Time: ~1-2 minutes (vs 4-6 minutes standard)")
    else:
        print("\n⚠️ PERFORMANCE ESTIMATE:")
        print("  📊 Standard performance (4-6 minutes total)")
        print("  💡 Run setup to enable high-performance features")

def main():
    """Main entry point with performance integration"""
    parser = argparse.ArgumentParser(
        description='Enhanced DFS Optimizer with High-Performance Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Launch best available GUI
  %(prog)s --status                  # Show performance system status
  %(prog)s --cli --dk file.csv       # High-performance CLI
  %(prog)s --cli --dk file.csv --milp --verbose  # Advanced CLI
        """
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--gui', action='store_true', 
                           help='Launch GUI (default)')
    mode_group.add_argument('--cli', action='store_true',
                           help='Use command line interface') 
    mode_group.add_argument('--status', action='store_true',
                           help='Show system status and performance info')

    # CLI arguments
    cli_group = parser.add_argument_group('CLI Options')
    cli_group.add_argument('--dk', type=str, help='DraftKings CSV file')
    cli_group.add_argument('--milp', action='store_true', help='Use MILP optimization')
    cli_group.add_argument('--attempts', type=int, default=1000, help='Monte Carlo attempts')
    cli_group.add_argument('--budget', type=int, default=50000, help='Salary cap')
    cli_group.add_argument('--min-salary', type=int, default=49000, help='Minimum salary')
    cli_group.add_argument('--force-refresh', action='store_true', help='Force refresh cached data')
    cli_group.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    cli_group.add_argument('--export', type=str, help='Export lineup to CSV')

    args = parser.parse_args()

    # Show system status
    if args.status:
        show_system_status()
        return 0

    # Launch CLI or GUI
    if args.cli:
        return launch_cli(args)
    else:
        return launch_best_gui()

if __name__ == "__main__":
    try:
        print("🚀 Enhanced DFS Optimizer with High-Performance Integration")
        print("⚡ Automatic performance system detection and optimization")
        print()

        exit_code = main()
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
