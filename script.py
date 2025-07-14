#!/usr/bin/env python3
"""
DFS OPTIMIZER - PROFESSIONAL CLI INTERFACE
=========================================
Complete command-line interface with all features integrated
"""

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from bulletproof_dfs_core import BulletproofDFSCore


class DFSOptimizerCLI:
    """Professional command-line interface for DFS optimization"""

    def __init__(self):
        self.core = None
        self.start_time = None

    def print_header(self):
        """Print professional header"""
        print("=" * 80)
        print("🚀 DFS OPTIMIZER - PROFESSIONAL CLI INTERFACE")
        print("=" * 80)
        print(f"   🕐 Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   📁 Working directory: {os.getcwd()}")
        print(f"   🐍 Python version: {sys.version.split()[0]}")
        print("=" * 80)

    def initialize_system(self, verbose: bool = True) -> bool:
        """Initialize the DFS optimization system"""
        if verbose:
            print("\n🔧 INITIALIZING DFS OPTIMIZATION SYSTEM")
            print("-" * 50)

        try:
            self.start_time = time.time()
            self.core = BulletproofDFSCore()

            if verbose:
                # Get system status
                status = self.core.get_system_status()

                print(f"✅ Core initialized successfully")
                print(f"   🎯 Mode: {'UNIFIED' if status['unified_mode'] else 'LEGACY'}")
                print(f"   📊 Modules loaded: {sum(status['modules'].values())}/{len(status['modules'])}")

                # Show module status
                print("\n📋 Module Status:")
                for module, available in status['modules'].items():
                    icon = "✅" if available else "❌"
                    print(f"   {icon} {module}")

            return True

        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            return False

    def load_players(self, csv_path: str, verbose: bool = True) -> bool:
        """Load players from CSV file"""
        if verbose:
            print(f"\n📂 LOADING PLAYER DATA")
            print("-" * 50)
            print(f"📄 File: {csv_path}")

        try:
            if not os.path.exists(csv_path):
                print(f"❌ File not found: {csv_path}")
                return False

            # Get file info
            file_size = os.path.getsize(csv_path) / 1024  # KB
            if verbose:
                print(f"📊 File size: {file_size:.1f} KB")

            start_load = time.time()
            player_count = self.core.load_draftkings_csv(csv_path)
            load_time = time.time() - start_load

            if player_count == 0:
                print("❌ No players loaded")
                return False

            if verbose:
                print(f"✅ Loaded {player_count} players in {load_time:.2f}s")

                # Player breakdown
                if hasattr(self.core.players[0], 'primary_position'):
                    # UnifiedPlayer objects
                    positions = {}
                    for player in self.core.players:
                        pos = player.primary_position
                        positions[pos] = positions.get(pos, 0) + 1
                else:
                    # Dictionary objects
                    positions = {}
                    for player in self.core.players:
                        pos = player.get('position', 'UNK')
                        positions[pos] = positions.get(pos, 0) + 1

                print("📊 Position breakdown:")
                for pos, count in sorted(positions.items()):
                    print(f"   {pos}: {count} players")

            return True

        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return False

    def detect_confirmations(self, verbose: bool = True) -> int:
        """Detect confirmed players"""
        if verbose:
            print(f"\n🔍 PLAYER CONFIRMATION DETECTION")
            print("-" * 50)

        try:
            start_confirm = time.time()
            confirmed_count = self.core.detect_confirmed_players()
            confirm_time = time.time() - start_confirm

            if verbose:
                print(f"✅ Confirmation completed in {confirm_time:.2f}s")
                print(f"🎯 Found {confirmed_count} confirmed players")

                if confirmed_count > 0:
                    # Show confirmed players
                    confirmed_players = []
                    for player in self.core.players:
                        if hasattr(player, 'is_confirmed'):
                            is_confirmed = player.is_confirmed
                        else:
                            is_confirmed = player.get('is_confirmed', False)

                        if is_confirmed:
                            name = player.name if hasattr(player, 'name') else player.get('name', 'Unknown')
                            team = player.team if hasattr(player, 'team') else player.get('team', 'UNK')
                            confirmed_players.append(f"{name} ({team})")

                    if len(confirmed_players) <= 10:
                        print("📋 Confirmed players:")
                        for player in confirmed_players:
                            print(f"   ✓ {player}")
                    else:
                        print(f"📋 Confirmed players (showing first 10 of {len(confirmed_players)}):")
                        for player in confirmed_players[:10]:
                            print(f"   ✓ {player}")
                        print(f"   ... and {len(confirmed_players) - 10} more")

            return confirmed_count

        except Exception as e:
            print(f"❌ Confirmation detection failed: {e}")
            return 0

    def optimize_lineup(self, strategy: str = "balanced", manual_selections: str = "",
                        verbose: bool = True) -> Optional[Dict]:
        """Generate optimized lineup"""
        if verbose:
            print(f"\n🎯 LINEUP OPTIMIZATION")
            print("-" * 50)
            print(f"📈 Strategy: {strategy.upper()}")
            if manual_selections:
                print(f"👤 Manual selections: {manual_selections}")

        try:
            start_opt = time.time()
            result = self.core.optimize_lineup(strategy, manual_selections)
            opt_time = time.time() - start_opt

            if not result:
                print("❌ No lineup generated")
                return None

            if verbose:
                print(f"✅ Optimization completed in {opt_time:.3f}s")

                # Show optimization method used
                method = result.get('optimization_method', 'unknown')
                print(f"⚙️  Method: {method.upper()}")

            return result

        except Exception as e:
            print(f"❌ Optimization failed: {e}")
            return None

    def display_lineup(self, result: Dict, verbose: bool = True):
        """Display the optimized lineup"""
        lineup = result.get('lineup', [])
        if not lineup:
            print("❌ No lineup to display")
            return

        print(f"\n🏆 OPTIMAL LINEUP")
        print("=" * 80)

        # Header
        print(f"{'Pos':4} {'Player':22} {'Team':4} {'Salary':>8} {'Points':>8} {'Value':>7}")
        print("-" * 80)

        total_salary = 0
        total_points = 0

        for player in lineup:
            # Handle both UnifiedPlayer objects and dictionaries
            if hasattr(player, 'name'):
                # UnifiedPlayer object
                name = player.name[:21]  # Truncate long names
                pos = player.primary_position
                team = player.team
                salary = player.salary
                points = getattr(player, 'enhanced_score', player.base_projection)
            else:
                # Dictionary
                name = player.get('name', 'Unknown')[:21]
                pos = player.get('position', 'UTIL')
                team = player.get('team', 'UNK')
                salary = player.get('salary', 0)
                points = player.get('projected_points', 0)

            value = (points / salary * 1000) if salary > 0 else 0

            print(f"{pos:4} {name:22} {team:4} ${salary:7,} {points:8.1f} {value:7.1f}")

            total_salary += salary
            total_points += points

        print("-" * 80)

        # Summary
        salary_usage = (total_salary / 50000) * 100
        avg_value = (total_points / total_salary * 1000) if total_salary > 0 else 0

        print(f"{'TOTAL:':31} ${total_salary:7,} {total_points:8.1f} {avg_value:7.1f}")
        print(f"💰 Salary Usage: {salary_usage:.1f}% (${50000 - total_salary:,} remaining)")

        # Additional stats
        if verbose and result.get('optimization_method') == 'unified':
            print(f"\n📊 Advanced Stats:")
            if 'correlation_score' in result:
                print(f"   🔗 Correlation Score: {result['correlation_score']:.2f}")
            if 'meta' in result:
                meta = result['meta']
                if 'calculations' in meta:
                    print(f"   🧮 Calculations: {meta['calculations']}")
                if 'cache_hit_rate' in meta:
                    print(f"   💾 Cache Hit Rate: {meta['cache_hit_rate']:.1%}")

    def save_lineup(self, result: Dict, output_path: str = None) -> str:
        """Save lineup to CSV file"""
        try:
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"optimal_lineup_{timestamp}.csv"

            # Create output directory if needed
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

            lineup = result.get('lineup', [])

            import csv
            with open(output_path, 'w', newline='') as csvfile:
                fieldnames = ['Position', 'Player', 'Team', 'Salary', 'Projected_Points', 'Value']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for player in lineup:
                    # Handle both object types
                    if hasattr(player, 'name'):
                        row = {
                            'Position': player.primary_position,
                            'Player': player.name,
                            'Team': player.team,
                            'Salary': player.salary,
                            'Projected_Points': getattr(player, 'enhanced_score', player.base_projection),
                            'Value': getattr(player, 'enhanced_score', player.base_projection) / player.salary * 1000
                        }
                    else:
                        row = {
                            'Position': player.get('position', 'UTIL'),
                            'Player': player.get('name', 'Unknown'),
                            'Team': player.get('team', 'UNK'),
                            'Salary': player.get('salary', 0),
                            'Projected_Points': player.get('projected_points', 0),
                            'Value': player.get('projected_points', 0) / max(player.get('salary', 1), 1) * 1000
                        }
                    writer.writerow(row)

            print(f"💾 Lineup saved to: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ Error saving lineup: {e}")
            return ""

    def show_system_info(self):
        """Show comprehensive system information"""
        print(f"\n📊 SYSTEM INFORMATION")
        print("=" * 80)

        if self.core:
            status = self.core.get_system_status()

            print(f"🎯 Core Status:")
            print(f"   Initialized: {'✅' if status['core_initialized'] else '❌'}")
            print(f"   Mode: {'🎯 UNIFIED' if status['unified_mode'] else '📊 LEGACY'}")
            print(f"   Players Loaded: {status['total_players']}")
            print(f"   Ready to Optimize: {'✅' if status['optimization_ready'] else '❌'}")

            print(f"\n📋 Module Status:")
            for module, available in status['modules'].items():
                icon = "✅" if available else "❌"
                print(f"   {icon} {module}")

            if status['csv_file']:
                print(f"\n📄 Current CSV: {status['csv_file']}")

            # Performance info
            if self.start_time:
                uptime = time.time() - self.start_time
                print(f"\n⏱️  Session uptime: {uptime:.1f}s")

        else:
            print("❌ System not initialized")

    def run_interactive_mode(self):
        """Run in interactive mode"""
        print("\n🎮 INTERACTIVE MODE")
        print("=" * 80)
        print("Available commands:")
        print("  📄 'load <csv_path>' - Load player data")
        print("  🔍 'confirm' - Detect confirmed players")
        print("  🎯 'optimize [strategy] [manual_players]' - Generate lineup")
        print("  📊 'info' - Show system information")
        print("  💾 'save [path]' - Save last lineup")
        print("  ❌ 'quit' - Exit")
        print("-" * 80)

        last_result = None

        while True:
            try:
                command = input("\n>>> ").strip().lower()

                if command == 'quit' or command == 'exit':
                    print("👋 Goodbye!")
                    break

                elif command.startswith('load '):
                    csv_path = command[5:].strip()
                    self.load_players(csv_path)

                elif command == 'confirm':
                    if not self.core or not self.core.players:
                        print("❌ No players loaded. Use 'load <csv_path>' first.")
                    else:
                        self.detect_confirmations()

                elif command.startswith('optimize'):
                    if not self.core or not self.core.players:
                        print("❌ No players loaded. Use 'load <csv_path>' first.")
                    else:
                        parts = command.split()
                        strategy = parts[1] if len(parts) > 1 else "balanced"
                        manual = " ".join(parts[2:]) if len(parts) > 2 else ""

                        result = self.optimize_lineup(strategy, manual)
                        if result:
                            self.display_lineup(result)
                            last_result = result

                elif command == 'info':
                    self.show_system_info()

                elif command.startswith('save'):
                    if not last_result:
                        print("❌ No lineup to save. Generate a lineup first.")
                    else:
                        parts = command.split()
                        output_path = parts[1] if len(parts) > 1 else None
                        self.save_lineup(last_result, output_path)

                else:
                    print("❌ Unknown command. Type 'quit' to exit.")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="DFS Optimizer - Professional CLI Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python script.py data.csv                     # Basic optimization
  python script.py data.csv --strategy ceiling  # Ceiling strategy
  python script.py data.csv --manual "Trout,Judge"  # Force include players
  python script.py --interactive                # Interactive mode
  python script.py --info                       # Show system info only
        """
    )

    parser.add_argument('csv_file', nargs='?', help='DraftKings CSV file path')
    parser.add_argument('--strategy', '-s', default='balanced',
                        choices=['balanced', 'ceiling', 'safe', 'value', 'contrarian'],
                        help='Optimization strategy')
    parser.add_argument('--manual', '-m', default='',
                        help='Comma-separated list of players to force include')
    parser.add_argument('--output', '-o', help='Output file path for lineup')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Run in interactive mode')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Minimal output')
    parser.add_argument('--info', action='store_true',
                        help='Show system info and exit')

    args = parser.parse_args()

    # Initialize CLI
    cli = DFSOptimizerCLI()

    if not args.quiet:
        cli.print_header()

    # Initialize system
    if not cli.initialize_system(verbose=not args.quiet):
        sys.exit(1)

    # Handle info mode
    if args.info:
        cli.show_system_info()
        sys.exit(0)

    # Handle interactive mode
    if args.interactive:
        cli.run_interactive_mode()
        sys.exit(0)

    # Handle CSV file mode
    if not args.csv_file:
        print("❌ No CSV file specified. Use --interactive for interactive mode.")
        parser.print_help()
        sys.exit(1)

    # Load players
    if not cli.load_players(args.csv_file, verbose=not args.quiet):
        sys.exit(1)

    # Detect confirmations
    cli.detect_confirmations(verbose=not args.quiet)

    # Optimize lineup
    result = cli.optimize_lineup(args.strategy, args.manual, verbose=not args.quiet)
    if not result:
        sys.exit(1)

    # Display result
    cli.display_lineup(result, verbose=not args.quiet)

    # Save if requested
    if args.output:
        cli.save_lineup(result, args.output)

    # Show session summary
    if not args.quiet:
        total_time = time.time() - cli.start_time
        print(f"\n⏱️  Total session time: {total_time:.2f}s")
        print("✅ Session completed successfully!")


if __name__ == "__main__":
    main()