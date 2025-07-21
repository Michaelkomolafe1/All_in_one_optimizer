#!/usr/bin/env python3
"""
GUI INTEGRATION FOR UNIFIED SYSTEM
==================================
Drop-in replacement for OptimizationWorker in complete_dfs_gui_debug.py
"""

from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd


class OptimizationWorker(QThread):
    """Worker thread using the Unified Core System"""

    progress = pyqtSignal(int, str)
    log = pyqtSignal(str, str)
    result = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, players_df, settings, csv_filename=None):
        super().__init__()
        self.players_df = players_df
        self.settings = settings
        self.csv_filename = csv_filename

    def run(self):
        """Run optimization using Unified Core System"""
        try:
            # Import the unified system
            from unified_core_system import UnifiedCoreSystem

            self.log.emit("🚀 Starting Unified Core System", "INFO")
            self.progress.emit(5, "Initializing system...")

            # Initialize system
            system = UnifiedCoreSystem()

            # Load CSV
            self.progress.emit(15, "Loading player data...")
            self.log.emit(f"Loading {len(self.players_df)} players", "INFO")

            # Save temp CSV if needed
            if not self.csv_filename:
                self.csv_filename = 'temp_optimization.csv'
                self.players_df.to_csv(self.csv_filename, index=False)

            num_loaded = system.load_csv(self.csv_filename)
            self.log.emit(f"✅ Loaded {num_loaded} players", "SUCCESS")

            # Fetch confirmed players
            self.progress.emit(30, "Fetching confirmed lineups...")
            self.log.emit("🔍 Checking for confirmed lineups...", "INFO")

            num_confirmed = system.fetch_confirmed_players()
            self.log.emit(f"✅ Found {num_confirmed} confirmed players", "SUCCESS")

            # Add manual selections
            manual_players = self.settings.get('manual_players', [])
            if manual_players:
                self.log.emit(f"Adding {len(manual_players)} manual selections", "INFO")
                for player_name in manual_players:
                    if system.add_manual_player(player_name):
                        self.log.emit(f"   ✅ Added: {player_name}", "SUCCESS")
                    else:
                        self.log.emit(f"   ❌ Not found: {player_name}", "WARNING")

            # Build player pool
            self.progress.emit(40, "Building player pool...")
            pool_size = system.build_player_pool()

            if pool_size == 0:
                self.log.emit("❌ No players in pool!", "ERROR")
                self.log.emit("Add manual selections or wait for confirmed lineups", "WARNING")
                self.error.emit("No players available for optimization")
                return

            self.log.emit(f"✅ Player pool: {pool_size} players", "SUCCESS")

            # Show pool breakdown
            status = system.get_system_status()
            self.log.emit(f"   Confirmed: {status['confirmed_players']}", "INFO")
            self.log.emit(f"   Manual: {status['manual_players']}", "INFO")

            # Enrich player pool with ALL data
            self.progress.emit(50, "Enriching with Vegas data...")
            self.log.emit("📊 Fetching Vegas lines...", "INFO")

            self.progress.emit(60, "Enriching with Statcast data...")
            self.log.emit("⚾ Fetching Statcast data...", "INFO")

            enriched_count = system.enrich_player_pool()
            self.log.emit(f"✅ Enriched {enriched_count} players", "SUCCESS")

            # Generate lineups
            self.progress.emit(70, "Optimizing lineups...")
            num_lineups = self.settings.get('num_lineups', 1)
            strategy = self.settings.get('strategy', 'balanced')

            self.log.emit(f"🎯 Generating {num_lineups} {strategy} lineups...", "INFO")

            lineups = system.optimize_lineups(
                num_lineups=num_lineups,
                strategy=strategy,
                min_unique_players=3
            )

            if not lineups:
                self.log.emit("❌ Optimization failed!", "ERROR")
                self.error.emit("Failed to generate lineups")
                return

            # Convert to GUI format
            gui_lineups = []

            for i, lineup in enumerate(lineups, 1):
                self.progress.emit(70 + (25 * i // num_lineups), f"Processing lineup {i}...")

                gui_lineup = {
                    'players': [],
                    'total_salary': lineup['total_salary'],
                    'projected_points': lineup['total_projection']
                }

                # Convert each player
                for p in lineup['players']:
                    # Get display position
                    pos = getattr(p, 'display_position', p.primary_position)

                    # Get best score
                    score = getattr(p, 'optimization_score', p.base_projection)

                    # Check if confirmed/manual
                    is_confirmed = getattr(p, 'is_confirmed', False)
                    is_manual = getattr(p, 'is_manual', False)

                    player_dict = {
                        'position': pos,
                        'name': p.name,
                        'salary': p.salary,
                        'team': p.team,
                        'points': score,
                        'confirmed': is_confirmed,
                        'manual': is_manual
                    }

                    gui_lineup['players'].append(player_dict)

                gui_lineups.append(gui_lineup)

                # Log lineup summary
                self.log.emit(f"✅ Lineup {i}: {lineup['total_projection']:.1f} pts, ${lineup['total_salary']:,}",
                              "SUCCESS")

            # Final status
            self.progress.emit(100, "Optimization complete!")
            self.log.emit(f"✅ Generated {len(gui_lineups)} optimized lineups", "SUCCESS")

            # Emit results
            self.result.emit(gui_lineups)

        except Exception as e:
            import traceback
            self.log.emit(f"Error: {str(e)}", "ERROR")
            self.log.emit(traceback.format_exc(), "ERROR")
            self.error.emit(str(e))


def apply_gui_integration():
    """Apply the integration to complete_dfs_gui_debug.py"""
    import shutil
    from datetime import datetime

    print("\n🔧 APPLYING GUI INTEGRATION")
    print("=" * 60)

    gui_file = 'complete_dfs_gui_debug.py'

    # Backup
    backup = f"{gui_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy(gui_file, backup)
        print(f"✅ Created backup: {backup}")
    except:
        print("⚠️  Could not create backup")

    print("\n📋 MANUAL INTEGRATION STEPS:")
    print("1. Copy the OptimizationWorker class above")
    print("2. Replace the existing OptimizationWorker in your GUI")
    print("3. Make sure unified_core_system.py is in the same directory")
    print("4. Run your GUI!")

    print("\n🎯 WHAT THIS GIVES YOU:")
    print("• Confirmed players only optimization")
    print("• ALL enrichments (Vegas, Statcast, etc)")
    print("• Pure data - no fallbacks")
    print("• Manual player selection support")
    print("• Detailed progress and logging")


if __name__ == "__main__":
    apply_gui_integration()