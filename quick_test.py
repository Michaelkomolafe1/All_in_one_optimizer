#!/usr/bin/env python3
"""
DFS QUICK TOOLS
===============
Quick command-line tools for common DFS tasks
"""

import sys
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
import json


class DFSQuickTools:
    def __init__(self):
        self.commands = {
            'info': self.show_csv_info,
            'stats': self.show_player_stats,
            'check': self.quick_health_check,
            'clean': self.quick_clean,
            'optimize': self.quick_optimize,
            'export': self.export_lineup,
            'backup': self.backup_data,
            'find': self.find_player,
            'top': self.show_top_players,
            'help': self.show_help
        }

    def run(self, args):
        """Run command based on arguments"""
        if len(args) < 2:
            self.show_help()
            return

        command = args[1].lower()

        if command in self.commands:
            self.commands[command](args[2:] if len(args) > 2 else [])
        else:
            print(f"❌ Unknown command: {command}")
            self.show_help()

    def show_csv_info(self, args):
        """Show info about CSV file"""
        if not args:
            # Find CSV files
            csv_files = list(Path('.').glob('*.csv'))
            if not csv_files:
                print("❌ No CSV files found")
                return

            print("📄 CSV files found:")
            for i, csv in enumerate(csv_files, 1):
                size = csv.stat().st_size / 1024
                print(f"  {i}. {csv.name} ({size:.1f}KB)")
            return

        csv_file = args[0]
        if not os.path.exists(csv_file):
            print(f"❌ File not found: {csv_file}")
            return

        df = pd.read_csv(csv_file)

        print(f"\n📊 CSV INFO: {csv_file}")
        print("=" * 50)
        print(f"Players: {len(df)}")
        print(f"Columns: {list(df.columns)}")

        if 'Position' in df.columns:
            print("\nPositions:")
            for pos, count in df['Position'].value_counts().items():
                print(f"  {pos}: {count}")

        if 'Salary' in df.columns:
            print(f"\nSalary Range: ${df['Salary'].min():,} - ${df['Salary'].max():,}")
            print(f"Average Salary: ${df['Salary'].mean():,.0f}")

    def show_player_stats(self, args):
        """Show player statistics"""
        csv_files = list(Path('.').glob('*.csv'))
        if not csv_files:
            print("❌ No CSV files found")
            return

        # Use first CSV found
        df = pd.read_csv(csv_files[0])

        print(f"\n📈 PLAYER STATS from {csv_files[0].name}")
        print("=" * 50)

        # Top projected scorers
        if 'AvgPointsPerGame' in df.columns:
            top_scorers = df.nlargest(10, 'AvgPointsPerGame')[['Name', 'Position', 'Salary', 'AvgPointsPerGame']]
            print("\nTop Projected Scorers:")
            for _, player in top_scorers.iterrows():
                print(
                    f"  {player['Name']:<20} {player['Position']:<4} ${player['Salary']:>6,} {player['AvgPointsPerGame']:>6.1f}pts")

        # Best values
        if 'Salary' in df.columns and 'AvgPointsPerGame' in df.columns:
            df['Value'] = df['AvgPointsPerGame'] / df['Salary'] * 1000
            best_values = df.nlargest(10, 'Value')[['Name', 'Position', 'Salary', 'AvgPointsPerGame', 'Value']]
            print("\nBest Values (pts/$1000):")
            for _, player in best_values.iterrows():
                print(
                    f"  {player['Name']:<20} {player['Position']:<4} ${player['Salary']:>6,} {player['Value']:>5.2f}x")

    def quick_health_check(self, args):
        """Quick system health check"""
        print("\n🏥 QUICK HEALTH CHECK")
        print("=" * 40)

        # Check modules
        modules = ['unified_core_system', 'unified_milp_optimizer', 'unified_player_model']
        missing = []

        for module in modules:
            try:
                __import__(module)
                print(f"✅ {module}")
            except:
                print(f"❌ {module}")
                missing.append(module)

        # Check data directory
        if os.path.exists('data'):
            size = sum(f.stat().st_size for f in Path('data').rglob('*') if f.is_file())
            print(f"\n📁 Data directory: {size / 1024 / 1024:.1f}MB")

        # Check CSV files
        csv_count = len(list(Path('.').glob('*.csv')))
        print(f"📄 CSV files: {csv_count}")

        if missing:
            print(f"\n⚠️ Missing modules: {', '.join(missing)}")
        else:
            print("\n✅ All systems operational!")

    def quick_clean(self, args):
        """Quick cleanup"""
        print("🧹 Running quick cleanup...")

        # Run the quick cleanup script if it exists
        if os.path.exists('quick_cleanup.sh'):
            os.system('./quick_cleanup.sh')
        else:
            # Manual cleanup
            os.system('find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null')
            os.system('rm -rf .pytest_cache .gui_cache 2>/dev/null')
            print("✅ Basic cleanup complete")

    def quick_optimize(self, args):
        """Quick optimization with minimal setup"""
        strategy = args[0] if args else "balanced"

        print(f"\n🎯 Quick optimization (strategy: {strategy})")

        try:
            from unified_core_system import UnifiedCoreSystem

            # Find CSV
            csv_files = list(Path('.').glob('*.csv'))
            if not csv_files:
                print("❌ No CSV files found")
                return

            system = UnifiedCoreSystem()
            system.load_csv(str(csv_files[0]))

            lineup = system.optimize_lineup(strategy=strategy)

            if lineup:
                print("\n✅ OPTIMIZED LINEUP:")
                total_salary = 0
                total_proj = 0

                for player in lineup:
                    print(
                        f"{player.primary_position:<4} {player.name:<20} ${player.salary:>6,} {player.enhanced_score:>6.1f}pts")
                    total_salary += player.salary
                    total_proj += player.enhanced_score

                print(f"\nTotal Salary: ${total_salary:,}")
                print(f"Projected: {total_proj:.1f}pts")

        except Exception as e:
            print(f"❌ Optimization failed: {e}")

    def export_lineup(self, args):
        """Export last lineup"""
        print("📤 Export feature - integrate with your optimizer")

    def backup_data(self, args):
        """Backup important data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backup_{timestamp}"

        os.makedirs(backup_dir, exist_ok=True)

        # Backup CSVs
        for csv in Path('.').glob('*.csv'):
            os.system(f"cp {csv} {backup_dir}/")

        # Backup configs
        for config in ['dfs_unified_config.json', 'auto_update_config.json']:
            if os.path.exists(config):
                os.system(f"cp {config} {backup_dir}/")

        print(f"✅ Backed up to {backup_dir}/")

    def find_player(self, args):
        """Find a player in CSV files"""
        if not args:
            print("Usage: dfs_quick find <player_name>")
            return

        search_name = ' '.join(args).lower()

        for csv_file in Path('.').glob('*.csv'):
            df = pd.read_csv(csv_file)

            if 'Name' in df.columns:
                matches = df[df['Name'].str.lower().str.contains(search_name, na=False)]

                if not matches.empty:
                    print(f"\n📍 Found in {csv_file.name}:")
                    for _, player in matches.iterrows():
                        info = f"  {player['Name']}"
                        if 'Position' in df.columns:
                            info += f" ({player['Position']})"
                        if 'Salary' in df.columns:
                            info += f" - ${player['Salary']:,}"
                        if 'AvgPointsPerGame' in df.columns:
                            info += f" - {player['AvgPointsPerGame']:.1f}pts"
                        print(info)

    def show_top_players(self, args):
        """Show top players by position"""
        position = args[0].upper() if args else None

        csv_files = list(Path('.').glob('*.csv'))
        if not csv_files:
            print("❌ No CSV files found")
            return

        df = pd.read_csv(csv_files[0])

        if position and 'Position' in df.columns:
            df = df[df['Position'].str.contains(position, na=False)]

        if 'AvgPointsPerGame' in df.columns:
            top = df.nlargest(10, 'AvgPointsPerGame')[['Name', 'Position', 'Salary', 'AvgPointsPerGame']]

            print(f"\n🏆 TOP PLAYERS" + (f" - {position}" if position else ""))
            print("=" * 50)

            for i, (_, player) in enumerate(top.iterrows(), 1):
                print(
                    f"{i:2d}. {player['Name']:<20} {player['Position']:<4} ${player['Salary']:>6,} {player['AvgPointsPerGame']:>6.1f}pts")

    def show_help(self):
        """Show help message"""
        print("\n🎯 DFS QUICK TOOLS")
        print("=" * 40)
        print("Usage: python dfs_quick.py <command> [args]")
        print("\nCommands:")
        print("  info [file]    - Show CSV file info")
        print("  stats          - Show player statistics")
        print("  check          - Quick health check")
        print("  clean          - Quick cleanup")
        print("  optimize [str] - Quick optimization")
        print("  find <name>    - Find a player")
        print("  top [pos]      - Show top players")
        print("  backup         - Backup data")
        print("  help           - Show this help")
        print("\nExamples:")
        print("  python dfs_quick.py info")
        print("  python dfs_quick.py optimize balanced")
        print("  python dfs_quick.py find ohtani")
        print("  python dfs_quick.py top OF")


if __name__ == "__main__":
    tools = DFSQuickTools()
    tools.run(sys.argv)