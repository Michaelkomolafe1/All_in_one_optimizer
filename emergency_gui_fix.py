# ADD THIS TO YOUR enhanced_dfs_gui.py FILE
# Replace your existing start_optimization method with this enhanced version

def start_optimization(self):
    """
    ENHANCED start_optimization method with All-Star game support and debugging
    """
    print("\n🎯 GUI OPTIMIZATION STARTING...")

    # Check if core is available
    if not self.core:
        self.results_panel.log_message("❌ Core system not initialized")
        return

    # Check if players are loaded
    if not hasattr(self.core, 'players') or not self.core.players:
        self.results_panel.log_message("❌ No players loaded - load CSV first")
        return

    player_count = len(self.core.players)
    self.results_panel.log_message(f"🎯 Starting optimization with {player_count} players...")

    try:
        # Get optimization settings from GUI
        settings = self.optimization_panel.get_settings()
        strategy = settings.get('strategy', 'balanced')
        manual_players = settings.get('manual_players', '')

        self.results_panel.log_message(f"📊 Strategy: {strategy}")
        if manual_players:
            self.results_panel.log_message(f"👤 Manual players: {manual_players}")

        # ALL-STAR GAME FIX: Force confirm all players
        confirmed_count = sum(1 for p in self.core.players if getattr(p, 'is_confirmed', False))
        self.results_panel.log_message(f"🔍 Currently confirmed: {confirmed_count} players")

        if confirmed_count == 0:
            self.results_panel.log_message("🌟 Detected All-Star game - confirming all players...")
            for player in self.core.players:
                player.is_confirmed = True
                if not hasattr(player, 'confirmation_sources'):
                    player.confirmation_sources = []
                player.confirmation_sources.append('allstar_gui_fix')

            confirmed_count = len(self.core.players)
            self.results_panel.log_message(f"✅ Force-confirmed {confirmed_count} players")

        # Set optimization mode to 'all' for All-Star games
        if hasattr(self.core, 'optimization_mode'):
            self.core.optimization_mode = 'all'
            self.results_panel.log_message("✅ Set optimization mode to 'all'")

        # Apply manual selections if provided
        if manual_players:
            self.results_panel.log_message("👤 Processing manual selections...")
            manual_list = [name.strip() for name in manual_players.split(',')]

            for player in self.core.players:
                for manual_name in manual_list:
                    if manual_name.lower() in player.name.lower():
                        player.is_manually_selected = True
                        self.results_panel.log_message(f"   ⭐ Selected: {player.name}")
                        break

        # Create and start worker thread
        self.results_panel.log_message("🚀 Starting optimization worker...")

        self.worker = OptimizationWorker(self.core, settings)
        self.worker.progress.connect(self.results_panel.log_message)
        self.worker.finished.connect(self.optimization_completed)
        self.worker.error.connect(self.optimization_error)

        # Disable optimize button during processing
        if hasattr(self.optimization_panel, 'optimize_button'):
            self.optimization_panel.optimize_button.setEnabled(False)
            self.optimization_panel.optimize_button.setText("Optimizing...")

        self.worker.start()

    except Exception as e:
        error_msg = f"❌ Optimization setup error: {str(e)}"
        self.results_panel.log_message(error_msg)
        print(f"GUI Error: {e}")
        import traceback
        traceback.print_exc()


def optimization_completed(self, result):
    """
    Handle completed optimization with enhanced error checking
    """
    try:
        print(f"\n✅ GUI: Optimization completed")
        print(f"Result type: {type(result)}")

        # Re-enable optimize button
        if hasattr(self.optimization_panel, 'optimize_button'):
            self.optimization_panel.optimize_button.setEnabled(True)
            self.optimization_panel.optimize_button.setText("Optimize Lineup")

        if not result:
            self.results_panel.log_message("❌ Optimization returned no result")
            return

        self.results_panel.log_message("✅ Optimization completed successfully!")

        # Handle different result types
        if isinstance(result, dict):
            if 'lineup' in result:
                lineup = result['lineup']
                score = result.get('score', 0)
                self.results_panel.log_message(f"📊 Lineup score: {score:.1f}")
                self.display_optimization_result(lineup, score)
            elif 'players' in result:
                players = result['players']
                score = result.get('total_score', 0)
                self.results_panel.log_message(f"📊 Classic lineup score: {score:.1f}")
                self.display_classic_result(players, score)
            else:
                self.results_panel.log_message(f"📋 Result keys: {list(result.keys())}")
                self.display_raw_result(result)

        elif isinstance(result, (list, tuple)) and len(result) == 2:
            # Tuple format: (lineup, score)
            lineup, score = result
            if lineup:
                self.results_panel.log_message(f"📊 Tuple result - Score: {score:.1f}")
                self.display_optimization_result(lineup, score)
            else:
                self.results_panel.log_message("❌ Empty lineup in tuple result")

        else:
            self.results_panel.log_message(f"⚠️ Unexpected result format: {type(result)}")
            self.display_raw_result(result)

    except Exception as e:
        error_msg = f"❌ Error displaying results: {str(e)}"
        self.results_panel.log_message(error_msg)
        print(f"Display error: {e}")
        import traceback
        traceback.print_exc()


def optimization_error(self, error_message):
    """
    Handle optimization errors with detailed logging
    """
    self.results_panel.log_message(f"❌ Optimization failed: {error_message}")
    print(f"Optimization error: {error_message}")

    # Re-enable optimize button
    if hasattr(self.optimization_panel, 'optimize_button'):
        self.optimization_panel.optimize_button.setEnabled(True)
        self.optimization_panel.optimize_button.setText("Optimize Lineup")

    # Show troubleshooting tips
    self.results_panel.log_message("💡 Troubleshooting tips:")
    self.results_panel.log_message("   1. Ensure CSV is properly loaded")
    self.results_panel.log_message("   2. Try selecting 'All' mode")
    self.results_panel.log_message("   3. Add manual player selections")
    self.results_panel.log_message("   4. For All-Star games, all players should be eligible")


def display_optimization_result(self, lineup, score):
    """
    Display optimization results in the GUI
    """
    if not lineup:
        self.results_panel.log_message("❌ No lineup to display")
        return

    self.results_panel.log_message(f"\n🏆 OPTIMIZED LINEUP - Score: {score:.1f}")
    self.results_panel.log_message("=" * 50)

    # Check if this is a showdown lineup
    captain = None
    utilities = []

    for player in lineup:
        if getattr(player, 'is_captain', False) or getattr(player, 'assigned_position', '') == 'CPT':
            captain = player
        else:
            utilities.append(player)

    total_salary = 0

    # Display captain
    if captain:
        cap_salary = int(captain.salary * 1.5)
        cap_score = getattr(captain, 'enhanced_score', captain.projection) * 1.5
        total_salary += cap_salary

        self.results_panel.log_message(f"👑 CAPTAIN: {captain.name} ({captain.team})")
        self.results_panel.log_message(f"   Salary: ${cap_salary:,} | Points: {cap_score:.1f}")

    # Display utilities
    if utilities:
        self.results_panel.log_message(f"\n⚡ UTILITY PLAYERS:")
        for i, player in enumerate(utilities, 1):
            total_salary += player.salary
            points = getattr(player, 'enhanced_score', player.projection)
            self.results_panel.log_message(
                f"   {i}. {player.name} ({player.team}) - ${player.salary:,} | {points:.1f} pts")

    # Summary
    self.results_panel.log_message(f"\n💰 Total Salary: ${total_salary:,} / $50,000")
    remaining = 50000 - total_salary
    self.results_panel.log_message(f"💰 Remaining: ${remaining:,}")

    # Populate the results table if it exists
    if hasattr(self.results_panel, 'lineup_table'):
        self.populate_lineup_table(lineup)


def display_raw_result(self, result):
    """
    Display raw results for debugging
    """
    self.results_panel.log_message(f"📋 Raw result:")
    self.results_panel.log_message(f"   Type: {type(result)}")

    if hasattr(result, '__dict__'):
        self.results_panel.log_message(f"   Attributes: {list(result.__dict__.keys())}")
    elif isinstance(result, dict):
        self.results_panel.log_message(f"   Keys: {list(result.keys())}")
    elif isinstance(result, (list, tuple)):
        self.results_panel.log_message(f"   Length: {len(result)}")
        if result:
            self.results_panel.log_message(f"   First item type: {type(result[0])}")

    self.results_panel.log_message(f"   Value: {str(result)[:200]}...")


# ALSO ADD THIS ENHANCED OPTIMIZATION WORKER

class OptimizationWorker(QThread):
    """Enhanced optimization worker with better error handling"""

    progress = pyqtSignal(str)
    finished = pyqtSignal(object)  # Changed to object to handle any result type
    error = pyqtSignal(str)

    def __init__(self, core, settings):
        super().__init__()
        self.core = core
        self.settings = settings
        self.is_cancelled = False

    def run(self):
        """Enhanced run method with comprehensive error handling"""
        try:
            self.progress.emit("🔄 Optimization worker started...")

            strategy = self.settings.get('strategy', 'balanced')
            manual_players = self.settings.get('manual_players', '')

            self.progress.emit(f"⚙️ Using strategy: {strategy}")

            # Try different optimization methods
            result = None

            # Method 1: Try showdown optimization if available
            if hasattr(self.core, 'optimize_showdown_lineup'):
                self.progress.emit("🎰 Attempting showdown optimization...")
                try:
                    result = self.core.optimize_showdown_lineup()
                    if result and (isinstance(result, tuple) and result[0]) or (
                            isinstance(result, dict) and result.get('lineup')):
                        self.progress.emit("✅ Showdown optimization successful!")
                        self.finished.emit(result)
                        return
                    else:
                        self.progress.emit("⚠️ Showdown optimization returned empty result")
                except Exception as e:
                    self.progress.emit(f"❌ Showdown optimization failed: {str(e)}")

            # Method 2: Try unified optimization
            if hasattr(self.core, 'optimize_lineup'):
                self.progress.emit("🎯 Attempting unified optimization...")
                try:
                    result = self.core.optimize_lineup(strategy, manual_players)
                    if result:
                        self.progress.emit("✅ Unified optimization successful!")
                        self.finished.emit(result)
                        return
                    else:
                        self.progress.emit("⚠️ Unified optimization returned empty result")
                except Exception as e:
                    self.progress.emit(f"❌ Unified optimization failed: {str(e)}")

            # Method 3: Try legacy optimization methods
            legacy_methods = ['optimize_classic_lineup', 'generate_lineup', 'create_lineup']
            for method_name in legacy_methods:
                if hasattr(self.core, method_name):
                    self.progress.emit(f"🔄 Attempting {method_name}...")
                    try:
                        method = getattr(self.core, method_name)
                        result = method(strategy) if 'strategy' in str(method.__code__.co_varnames) else method()
                        if result:
                            self.progress.emit(f"✅ {method_name} successful!")
                            self.finished.emit(result)
                            return
                    except Exception as e:
                        self.progress.emit(f"❌ {method_name} failed: {str(e)}")

            # If we get here, all methods failed
            self.error.emit("All optimization methods failed - check logs for details")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.error.emit(f"Worker thread error: {str(e)}\n{error_details}")


"""
INTEGRATION INSTRUCTIONS:
========================

1. Find your enhanced_dfs_gui.py file

2. Replace the existing start_optimization method with the enhanced version above

3. Replace the OptimizationWorker class with the enhanced version above

4. Add the new helper methods (optimization_completed, optimization_error, etc.)

5. Test with your All-Star CSV

This will give you detailed logging and handle All-Star games properly!
"""