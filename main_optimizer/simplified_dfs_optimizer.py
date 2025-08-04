#!/usr/bin/env python3
"""
SIMPLIFIED DFS OPTIMIZER GUI
A standalone 2-button interface with debug mode
"""

import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime
import traceback

# Import your existing system components
from unified_core_system import UnifiedCoreSystem
from enhanced_scoring_engine import EnhancedScoringEngine


class SimplifiedDFSOptimizer(QMainWindow):
    """Simple 2-button DFS Optimizer with debug mode"""

    def __init__(self):
        super().__init__()
        self.system = UnifiedCoreSystem()
        self.manual_players = set()
        self.debug_mode = False  # Toggle for debug info
        self.setWindowTitle("DFS Optimizer - Simple Mode")
        self.setGeometry(100, 100, 1400, 900)  # Wider for debug panel
        self.init_ui()

    def update_status(self, message, append=False):
        """Update status display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if hasattr(self, 'status_display'):
            if append:
                current = self.status_display.toPlainText()
                self.status_display.setText(f"{current}\n[{timestamp}] {message}")
            else:
                self.status_display.setText(f"[{timestamp}] {message}")

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)  # Changed to horizontal

        # Left side - Main controls
        left_panel = QWidget()
        layout = QVBoxLayout(left_panel)

        # Header
        header = QLabel("DFS OPTIMIZER")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(header)

        # Main Control Panel
        control_panel = QGroupBox()
        control_layout = QVBoxLayout(control_panel)

        # Status Display - Create the widget FIRST
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setMaximumHeight(150)
        self.status_display.setStyleSheet("""
            QTextEdit {
                background-color: #f0f0f0;
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-family: monospace;
                font-size: 12px;
            }
        """)

        # Add to layout BEFORE using it
        control_layout.addWidget(self.status_display)

        # NOW we can safely call update_status
        self.update_status("Ready to load CSV file")

        # Settings Row
        settings_layout = QHBoxLayout()

        # Contest Type
        settings_layout.addWidget(QLabel("Contest:"))
        self.contest_type = QComboBox()
        self.contest_type.addItems(["Cash", "GPP"])
        self.contest_type.setStyleSheet("font-size: 14px; padding: 5px;")
        self.contest_type.currentTextChanged.connect(self.on_contest_changed)
        settings_layout.addWidget(self.contest_type)

        settings_layout.addSpacing(20)

        # Manual Strategy Override
        self.manual_strategy_cb = QCheckBox("Manual Strategy")
        self.manual_strategy_cb.toggled.connect(self.toggle_manual_strategy)
        settings_layout.addWidget(self.manual_strategy_cb)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "projection_monster",
            "pitcher_dominance",
            "correlation_value",
            "smart_stack",
            "matchup_leverage"
        ])
        self.strategy_combo.setEnabled(False)
        self.strategy_combo.setStyleSheet("font-size: 14px; padding: 5px;")
        settings_layout.addWidget(self.strategy_combo)

        # Debug Mode Toggle
        self.debug_cb = QCheckBox("Debug Mode")
        self.debug_cb.setStyleSheet("color: red; font-weight: bold;")
        self.debug_cb.toggled.connect(self.toggle_debug_mode)
        settings_layout.addWidget(self.debug_cb)

        # ADD THIS NEW CHECKBOX HERE:
        self.test_mode_cb = QCheckBox("Test Mode (No Confirmations)")
        self.test_mode_cb.setToolTip("Use when lineups aren't confirmed yet or testing old CSVs")
        self.test_mode_cb.setStyleSheet("color: orange; font-weight: bold;")
        settings_layout.addWidget(self.test_mode_cb)





        settings_layout.addStretch()
        control_layout.addLayout(settings_layout)

        # Manual Player Addition
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Add Player:"))
        self.manual_player_input = QLineEdit()
        self.manual_player_input.setPlaceholderText("Enter player name...")
        self.manual_player_input.returnPressed.connect(self.add_manual_player)
        manual_layout.addWidget(self.manual_player_input)

        self.add_player_btn = QPushButton("Add")
        self.add_player_btn.clicked.connect(self.add_manual_player)
        manual_layout.addWidget(self.add_player_btn)



        self.manual_label = QLabel("Manual: None")
        self.manual_label.setStyleSheet("color: #666; font-style: italic;")
        manual_layout.addWidget(self.manual_label)

        control_layout.addLayout(manual_layout)

        # The 2 Main Buttons
        button_layout = QHBoxLayout()

        # Button 1: Load & Setup
        self.load_button = QPushButton("📁 LOAD & SETUP")
        self.load_button.setMinimumHeight(60)
        self.load_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.load_button.clicked.connect(self.load_and_setup)
        button_layout.addWidget(self.load_button)

        # Button 2: Optimize
        self.optimize_button = QPushButton("🚀 OPTIMIZE")
        self.optimize_button.setMinimumHeight(60)
        self.optimize_button.setEnabled(False)
        self.optimize_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.optimize_button.clicked.connect(self.run_optimization)
        button_layout.addWidget(self.optimize_button)

        control_layout.addLayout(button_layout)
        layout.addWidget(control_panel)

        # Results Display (Tabbed)
        self.tabs = QTabWidget()

        # Lineup tab
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.tabs.addTab(self.results_display, "Lineup")

        # Player pool tab
        self.pool_display = QTextEdit()
        self.pool_display.setReadOnly(True)
        self.tabs.addTab(self.pool_display, "Player Pool")

        # Debug tab
        self.debug_display = QTextEdit()
        self.debug_display.setReadOnly(True)
        self.debug_display.setStyleSheet("font-family: monospace; font-size: 10px;")
        self.tabs.addTab(self.debug_display, "Debug Info")

        layout.addWidget(self.tabs)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        main_layout.addWidget(left_panel)

        # Right side - Debug Panel (initially hidden)
        self.debug_panel = self.create_debug_panel()
        self.debug_panel.setVisible(False)
        main_layout.addWidget(self.debug_panel)

    def create_debug_panel(self):
        """Create a detailed debug panel"""
        panel = QGroupBox("🔍 DEBUG PANEL")
        panel.setMaximumWidth(400)
        panel.setStyleSheet("""
            QGroupBox {
                background-color: #fff3cd;
                border: 2px solid #856404;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(panel)

        # Enrichment Stats
        self.enrichment_stats = QTextEdit()
        self.enrichment_stats.setReadOnly(True)
        self.enrichment_stats.setMaximumHeight(200)
        layout.addWidget(QLabel("Enrichment Stats:"))
        layout.addWidget(self.enrichment_stats)

        # Sample Player Details
        self.sample_player_details = QTextEdit()
        self.sample_player_details.setReadOnly(True)
        layout.addWidget(QLabel("Sample Player Analysis:"))
        layout.addWidget(self.sample_player_details)

        # Test Buttons
        test_btn_layout = QVBoxLayout()

        verify_btn = QPushButton("🔬 Verify All Enrichments")
        verify_btn.clicked.connect(self.verify_all_enrichments)
        test_btn_layout.addWidget(verify_btn)

        # Add this button to your debug panel
        test_breakdown_btn = QPushButton("📊 Test Scoring Breakdown")
        test_breakdown_btn.clicked.connect(self.test_scoring_with_breakdown)
        test_btn_layout.addWidget(test_breakdown_btn)

        test_ownership_btn = QPushButton("💰 Test Ownership Projections")
        test_ownership_btn.clicked.connect(self.test_ownership_projections)
        test_btn_layout.addWidget(test_ownership_btn)

        test_scoring_btn = QPushButton("📊 Test Scoring Engine")
        test_scoring_btn.clicked.connect(self.test_scoring_engine)
        test_btn_layout.addWidget(test_scoring_btn)

        dump_player_btn = QPushButton("💾 Dump Player Data")
        dump_player_btn.clicked.connect(self.dump_player_data)
        test_btn_layout.addWidget(dump_player_btn)

        check_enrichments_btn = QPushButton("🔍 Check Enrichment Usage")
        check_enrichments_btn.clicked.connect(self.verify_enrichment_usage)
        test_btn_layout.addWidget(check_enrichments_btn)

        # ADD THIS NEW BUTTON HERE! ↓↓↓
        test_real_data_btn = QPushButton("🌐 Test Real Data Sources")
        test_real_data_btn.clicked.connect(self.test_real_enrichments)
        test_btn_layout.addWidget(test_real_data_btn)

        layout.addLayout(test_btn_layout)

        return panel

    def toggle_debug_mode(self, checked):
        """Toggle debug mode on/off"""
        self.debug_mode = checked
        self.debug_panel.setVisible(checked)
        if checked:
            self.update_status("🔍 DEBUG MODE ENABLED", append=True)
            self.tabs.setCurrentIndex(2)  # Switch to debug tab
        else:
            self.update_status("Debug mode disabled", append=True)

    def load_and_setup(self):
        """Enhanced with debug tracking"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select DraftKings CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            self.progress.setVisible(True)
            self.load_button.setEnabled(False)

            # Clear debug info
            self.debug_display.clear()

            # Step 1: Load CSV
            self.progress.setValue(20)
            self.update_status("📂 Loading CSV...")
            self.debug_log("=== LOADING CSV ===")

            self.system.load_players_from_csv(file_path)
            self.update_status(f"✅ Loaded {len(self.system.players)} players", append=True)
            self.debug_log(f"Loaded {len(self.system.players)} players from {file_path}")
            self.debug_log(f"Positions found: {set(p.primary_position for p in self.system.players)}")

            if self.system.players:
                sample = self.system.players[0]
                self.debug_log(f"CSV has AvgPointsPerGame: {hasattr(sample, 'AvgPointsPerGame')}")
                self.debug_log(f"Sample AvgPointsPerGame: {getattr(sample, 'AvgPointsPerGame', 'MISSING')}")



                sample_game_info = self.system.players[0].game_info if hasattr(self.system.players[0],
                                                                               'game_info') else ""

                self.debug_log(f"Sample game info: {sample_game_info}")

                # Check if this is old data
                today = datetime.now().strftime('%m/%d')
                if today not in sample_game_info:
                    self.update_status("⚠️ CSV appears to be from a different date than today", append=True)
                    self.update_status("💡 Consider enabling Test Mode for testing", append=True)
                    # Auto-enable test mode for old CSVs
                    self.test_mode_cb.setChecked(True)

            # Step 2: Detect Slate & Strategy
            self.progress.setValue(30)
            self.update_status("🔍 Analyzing slate...", append=True)
            self.debug_log("\n=== SLATE ANALYSIS ===")

            slate_info = self.analyze_and_select_strategy()
            self.update_status(f"✅ {slate_info['slate_size'].upper()} slate | {slate_info['num_games']} games",
                               append=True)
            self.debug_log(f"Slate: {slate_info}")

            # Use manual strategy if selected
            if self.manual_strategy_cb.isChecked():
                self.selected_strategy = self.strategy_combo.currentText()
                self.update_status(f"📋 Strategy: {self.selected_strategy} (manual)", append=True)
            else:
                self.update_status(f"📋 Strategy: {self.selected_strategy} (auto)", append=True)
            self.debug_log(f"Selected strategy: {self.selected_strategy}")

            # Step 3: Fetch Confirmations
            self.progress.setValue(50)
            self.update_status("🔄 Fetching confirmed lineups...", append=True)
            self.debug_log("\n=== CONFIRMATIONS ===")

            confirmed = self.system.fetch_confirmed_players()
            self.update_status(f"✅ Found {len(confirmed)} confirmed players", append=True)
            self.debug_log(f"Confirmed: {len(confirmed)} players")
            if self.debug_mode and confirmed:
                self.debug_log(f"Sample: {list(confirmed)[:5]}")

            # Step 4: Build Pool
            self.progress.setValue(70)
            self.update_status("🏗️ Building player pool...", append=True)
            self.debug_log("\n=== PLAYER POOL ===")

            self.build_pool_with_manual()
            self.update_status(f"✅ Pool: {len(self.system.player_pool)} players", append=True)
            self.debug_log(f"Pool size: {len(self.system.player_pool)}")

            # Step 5: Enrich Data
            self.progress.setValue(85)
            self.update_status("🔬 Enriching player data...", append=True)
            self.debug_log("\n=== ENRICHMENT ===")

            # Fix base projections FIRST
            self.fix_base_projections()


            # Now enrich with real data
            try:
                enrichment_results = self.system.enrich_player_pool_with_real_data()
                self.update_status(f"✅ Enrichments applied: {sum(enrichment_results.values())} total", append=True)
            except Exception as e:
                self.debug_log(f"Real enrichment error: {e}")
                self.debug_log("Falling back to basic enrichment")
                # Fall back to basic enrichment
                self.system.enrich_player_pool()
                enrichment_results = self.track_enrichments()

            # Step 6: Score Players
            self.progress.setValue(95)
            self.update_status("📊 Calculating scores...", append=True)
            self.debug_log("\n=== SCORING ===")

            contest_type = self.contest_type.currentText().lower()
            self.system.score_players(contest_type)


            # Add this test:
            if self.debug_mode and self.system.player_pool:
                # Quick test of top 3 players
                self.debug_log("\n=== QUICK SCORING TEST ===")
                for p in sorted(self.system.player_pool, key=lambda x: x.salary, reverse=True)[:3]:
                    self.debug_log(f"{p.name}: Cash={p.cash_score:.1f}, GPP={p.gpp_score:.1f}")
                    self.debug_log(
                        f"  Enrichments: form={p.recent_form}, park={p.park_factor}, weather={p.weather_impact}")


            self.debug_log(f"Scored for {contest_type}")

            # Verify scoring
            self.verify_scoring_distribution()

            # Done!
            self.progress.setValue(100)
            self.update_status("✅ READY TO OPTIMIZE!", append=True)
            self.optimize_button.setEnabled(True)
            self.load_button.setEnabled(True)
            self.progress.setVisible(False)

            # Show summaries
            self.show_setup_summary()
            self.update_pool_display()

            if self.debug_mode:
                self.update_debug_panel(enrichment_results)

        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", append=True)
            self.debug_log(f"ERROR: {str(e)}\n{traceback.format_exc()}")
            self.load_button.setEnabled(True)
            self.progress.setVisible(False)

    def check_player_fields(self):
        """Debug what fields are actually in the CSV"""
        if not self.system.players:
            self.debug_log("No players loaded!")
            return

        player = self.system.players[0]
        self.debug_log("\n=== CSV FIELD NAMES ===")

        # Get all numeric fields
        for attr in dir(player):
            if not attr.startswith('_'):
                value = getattr(player, attr)
                if isinstance(value, (int, float)) and not callable(value):
                    self.debug_log(f"{attr}: {value}")


    # Add this to your simplified GUI to verify enrichments are available
    def check_enrichment_modules(self):
        """Check which enrichment modules are available"""
        self.debug_log("\n=== CHECKING ENRICHMENT MODULES ===")

        modules_to_check = [
            ('simple_statcast_fetcher', 'SimpleStatcastFetcher'),
            ('weather_integration', 'WeatherIntegration'),
            ('park_factors', 'ParkFactors'),
            ('vegas_lines', 'VegasLines'),
            ('real_data_enrichments', 'RealStatcastFetcher')
        ]

        available = []
        missing = []

        for module_name, class_name in modules_to_check:
            try:
                module = __import__(module_name)
                if hasattr(module, class_name):
                    available.append(module_name)
                    self.debug_log(f"✅ {module_name} is available", "success")
                else:
                    missing.append(module_name)
                    self.debug_log(f"❌ {module_name} missing class {class_name}", "error")
            except ImportError:
                missing.append(module_name)
                self.debug_log(f"❌ {module_name} not found", "error")

        return available, missing

    def verify_enrichment_usage(self):
        """Verify strategies are actually using enrichments"""
        if not self.system.player_pool:
            self.debug_log("No players to verify!")
            return

        self.debug_log("\n=== ENRICHMENT USAGE VERIFICATION ===")

        # Get a test player
        test_player = self.system.player_pool[0]

        # Test with fresh scoring engine instance
        from enhanced_scoring_engine import EnhancedScoringEngine
        test_engine = EnhancedScoringEngine()

        # Test CASH scoring
        self.debug_log(f"\nTesting CASH scoring for {test_player.name}:")
        self.debug_log(f"Base projection: {test_player.base_projection}")

        # Score with normal values
        normal_cash = test_engine.score_player_cash(test_player)
        self.debug_log(f"Normal cash score: {normal_cash:.2f}")

        # Create a copy and modify
        import copy
        boosted_player = copy.deepcopy(test_player)
        boosted_player.recent_form = 1.5
        boosted_player.consistency_score = 1.5

        boosted_cash = test_engine.score_player_cash(boosted_player)
        self.debug_log(f"Boosted cash score: {boosted_cash:.2f}")

        # Check multiplier
        if test_player.base_projection > 0:
            expected = normal_cash * 1.5 * 1.5  # 2.25x
            self.debug_log(f"Expected: ~{expected:.2f}")

        # Test GPP
        self.debug_log(f"\nTesting GPP scoring:")
        normal_gpp = test_engine.score_player_gpp(test_player)

        boosted_player.park_factor = 1.5
        boosted_player.weather_impact = 1.5
        boosted_gpp = test_engine.score_player_gpp(boosted_player)

        self.debug_log(f"Normal GPP: {normal_gpp:.2f}")
        self.debug_log(f"Boosted GPP: {boosted_gpp:.2f}")
        self.debug_log(f"Boost ratio: {boosted_gpp / normal_gpp:.2f}x")



    def on_contest_changed(self):
        """Re-score players when contest type changes"""
        if hasattr(self, 'system') and hasattr(self.system, 'player_pool') and self.system.player_pool:
            contest_type = self.contest_type.currentText().lower()
            self.update_status(f"Re-scoring for {contest_type.upper()}...", append=True)
            self.system.score_players(contest_type)
            # Update display if you have one
            if hasattr(self, 'update_pool_display'):
                self.update_pool_display()

    def toggle_manual_strategy(self, checked):
        """Enable/disable manual strategy selection"""
        self.strategy_combo.setEnabled(checked)
        if checked:
            self.update_status("⚙️ Manual strategy override enabled", append=True)

    def add_manual_player(self):
        """Add a player manually to the pool"""
        player_name = self.manual_player_input.text().strip()
        if not player_name:
            return

        self.manual_players.add(player_name)
        self.manual_player_input.clear()

        # Update display
        if self.manual_players:
            self.manual_label.setText(f"Manual: {len(self.manual_players)} added")

        self.update_status(f"➕ Added {player_name} to manual pool", append=True)

    def analyze_and_select_strategy(self):
        """Auto-detect slate and select strategy"""
        # Simple slate detection
        positions = {p.primary_position for p in self.system.players}
        is_showdown = 'CPT' in positions or 'UTIL' in positions

        # Count unique games (simplified)
        teams = set(p.team for p in self.system.players if hasattr(p, 'team'))
        num_games = len(teams) // 2  # Rough estimate

        # Determine slate size
        if is_showdown:
            slate_size = 'showdown'
        elif num_games <= 3:
            slate_size = 'small'
        elif num_games <= 8:
            slate_size = 'medium'
        else:
            slate_size = 'large'

        # Select strategy based on contest type and slate size
        contest_type = self.contest_type.currentText().lower()

        # Use the strategy registry
        if slate_size == 'showdown':
            self.selected_strategy = 'showdown_leverage'
        else:
            strategies = {
                'cash': {
                    'small': 'projection_monster',
                    'medium': 'pitcher_dominance',
                    'large': 'pitcher_dominance'
                },
                'gpp': {
                    'small': 'correlation_value',
                    'medium': 'smart_stack',
                    'large': 'matchup_leverage'
                }
            }
            self.selected_strategy = strategies[contest_type][slate_size]

        return {
            'slate_size': slate_size,
            'num_games': num_games,
            'is_showdown': is_showdown
        }

    def fix_base_projections(self):
        """Fix players with 0 base projection by checking all possible DK fields"""
        self.debug_log("\n=== FIXING BASE PROJECTIONS ===")

        fixed_count = 0
        zero_count = 0

        # Debug: Check what fields exist on first player
        if self.system.player_pool:
            sample = self.system.player_pool[0]
            self.debug_log(f"Sample player fields: {[attr for attr in dir(sample) if not attr.startswith('_')]}")

        for player in self.system.player_pool:
            original = getattr(player, 'base_projection', 0)

            # Try all possible DraftKings field names
            projection_fields = [
                'AvgPointsPerGame',  # Most common DK field
                'ppg',  # Alternate name
                'Fpts',  # Some CSVs use this
                'proj',  # Short form
                'projection',  # Generic
                'projected_points',  # Verbose form
                'dkfpts',  # DK specific
                'points'  # Generic
            ]

            # Try each field
            found_value = 0
            for field in projection_fields:
                value = getattr(player, field, 0)
                if value and value > 0:
                    found_value = value
                    self.debug_log(f"Found projection for {player.name} in field '{field}': {value}")
                    break

            # Set the base projection
            if found_value > 0:
                player.base_projection = found_value
                if original == 0:
                    fixed_count += 1
            else:
                # Use position-based defaults as last resort
                if player.is_pitcher:
                    player.base_projection = 15.0  # Default pitcher projection
                else:
                    player.base_projection = 8.0  # Default hitter projection
                zero_count += 1
                self.debug_log(f"⚠️ No projection found for {player.name}, using default {player.base_projection}")

        self.debug_log(f"\n✅ Fixed {fixed_count} players with 0 projections")
        self.debug_log(f"⚠️ {zero_count} players using position defaults")

        # Show sample of fixed projections
        self.debug_log("\nSample projections after fix:")
        for player in self.system.player_pool[:5]:
            self.debug_log(f"  {player.name}: {player.base_projection:.1f} pts")

    def build_pool_with_manual(self):
        """Build pool including manual players"""
        # Sync manual selections to the system
        self.system.manual_selections = self.manual_players.copy()

        # CHECK TEST MODE FIRST:
        if self.test_mode_cb.isChecked():
            # Test mode - include ALL players
            self.system.build_player_pool(include_unconfirmed=True)
            self.update_status("⚠️ TEST MODE: Including all players (ignoring confirmations)", append=True)
        else:
            # Normal mode - respect confirmation settings
            include_unconfirmed = self.contest_type.currentText() == "GPP"
            self.system.build_player_pool(include_unconfirmed=include_unconfirmed)

        # The system's build_player_pool should already handle manual players
        # So we just need to report what happened
        manual_in_pool = sum(1 for p in self.system.player_pool if p.name in self.manual_players)
        if manual_in_pool > 0:
            self.update_status(f"➕ {manual_in_pool} manual players included in pool", append=True)

    def show_setup_summary(self):
        """Show a nice summary of what we've set up"""
        summary = f"""
    ========================================
            SETUP COMPLETE
    ========================================
    📊 Players: {len(self.system.player_pool)}
    🎯 Contest: {self.contest_type.currentText()}
    📋 Strategy: {self.selected_strategy.replace('_', ' ').title()}
    ➕ Manual Players: {len(self.manual_players)}
    ✅ Ready to optimize!

    Click OPTIMIZE to generate your lineup!
    ========================================
    """
        self.results_display.setText(summary)

    def update_pool_display(self):
        """Show the player pool in the second tab"""
        pool_text = f"PLAYER POOL ({len(self.system.player_pool)} players)\n"
        pool_text += "=" * 60 + "\n"
        pool_text += f"{'Name':<20} {'Pos':<5} {'Team':<5} {'Salary':<8} {'Score':<8}\n"
        pool_text += "-" * 60 + "\n"

        # Sort by optimization score
        contest_type = self.contest_type.currentText().lower()
        score_attr = 'cash_score' if contest_type == 'cash' else 'gpp_score'

        sorted_pool = sorted(self.system.player_pool,
                             key=lambda p: getattr(p, score_attr, 0),
                             reverse=True)[:50]  # Show top 50

        for player in sorted_pool:
            score = getattr(player, score_attr, 0)
            is_manual = player.name in self.manual_players
            manual_mark = " *" if is_manual else ""

            pool_text += f"{player.name[:19] + manual_mark:<20} {player.primary_position:<5} "
            pool_text += f"{player.team:<5} ${player.salary:<7,} {score:<8.1f}\n"

        if len(self.system.player_pool) > 50:
            pool_text += f"\n... and {len(self.system.player_pool) - 50} more players"

        if self.manual_players:
            pool_text += f"\n\n* = Manually added player"

        self.pool_display.setText(pool_text)

    def run_optimization(self):
        """Run the optimization"""
        self.optimize_button.setEnabled(False)
        contest_type = self.contest_type.currentText().lower()

        try:
            self.update_status(f"🚀 Optimizing {contest_type.upper()} lineup...", append=True)

            lineups = self.system.optimize_lineups(
                num_lineups=1,  # Just 1 for cash, could make this configurable for GPP
                strategy=self.selected_strategy,
                contest_type=contest_type,
                min_unique_players=3
            )

            if lineups:
                self.display_lineup(lineups[0])
                self.update_status("✅ Optimization complete!", append=True)
            else:
                self.update_status("❌ No valid lineups found", append=True)

        except Exception as e:
            self.update_status(f"❌ Optimization error: {str(e)}", append=True)
            self.debug_log(f"ERROR: {traceback.format_exc()}")
        finally:
            self.optimize_button.setEnabled(True)

    def display_lineup(self, lineup):
        """Display the optimized lineup"""
        output = f"""
    ========================================
            OPTIMIZED LINEUP
    ========================================
    Contest: {self.contest_type.currentText()}
    Strategy: {self.selected_strategy.replace('_', ' ').title()}
    Total Salary: ${lineup['total_salary']:,}
    Projected Points: {lineup['total_projection']:.1f}
    Optimizer Score: {lineup.get('optimizer_score', 0):.1f}
    ========================================

    {"POS":<4} {"PLAYER":<20} {"TEAM":<5} {"SALARY":<8} {"PROJ":<6}
    {"-" * 50}
    """
        for player in lineup['players']:
            output += f"{player.primary_position:<4} {player.name:<20} {player.team:<5} ${player.salary:<7,} {player.base_projection:<6.1f}\n"

        # Show stacks
        teams = {}
        for p in lineup['players']:
            teams[p.team] = teams.get(p.team, 0) + 1
        stacks = {t: c for t, c in teams.items() if c >= 2}

        if stacks:
            output += f"\n🏟️ Stacks: {stacks}\n"

        output += "\n" + "=" * 40 + "\n"
        output += "Copy this lineup to DraftKings!"

        self.results_display.setText(output)

        # Copy lineup info to clipboard for easy tracking
        QApplication.clipboard().setText(output)
        self.update_status("📋 Lineup copied to clipboard!", append=True)



    def track_enrichments(self):
        """Track what enrichments are applied"""
        self.system.enrich_player_pool()

        results = {
            'total': len(self.system.player_pool),  # ADD THIS LINE
            'vegas': 0,
            'weather': 0,
            'park': 0,
            'stats': 0,
            'consistency': 0,
            'confirmed': 0
        }

        for player in self.system.player_pool:
            if hasattr(player, 'team_total') and player.team_total > 0:
                results['vegas'] += 1
            if hasattr(player, 'weather_impact') and player.weather_impact != 1.0:
                results['weather'] += 1
            if hasattr(player, 'park_factor') and player.park_factor != 1.0:
                results['park'] += 1
            if hasattr(player, 'recent_form') and player.recent_form != 1.0:
                results['stats'] += 1
            if hasattr(player, 'consistency_score'):
                results['consistency'] += 1
            if getattr(player, 'is_confirmed', False):
                results['confirmed'] += 1

        # Log results
        self.debug_log(f"Enrichment Results: {results}")

        # Update status
        self.update_status(
            f"   Vegas: {results['vegas']}/{results['total']} | "
            f"Weather: {results['weather']}/{results['total']} | "
            f"Stats: {results['stats']}/{results['total']}",
            append=True
        )

        return results

    def verify_scoring_distribution(self):
        """Check score distribution"""
        if not self.system.player_pool:
            return

        contest_type = self.contest_type.currentText().lower()
        score_attr = 'cash_score' if contest_type == 'cash' else 'gpp_score'

        scores = [getattr(p, score_attr, 0) for p in self.system.player_pool]

        if scores:
            self.debug_log(f"Score distribution:")
            self.debug_log(f"  Min: {min(scores):.2f}")
            self.debug_log(f"  Max: {max(scores):.2f}")
            self.debug_log(f"  Avg: {sum(scores) / len(scores):.2f}")
            self.debug_log(f"  Zero scores: {scores.count(0)}")

    def verify_all_enrichments(self):
        """Detailed enrichment verification"""
        if not self.system.player_pool:
            QMessageBox.warning(self, "Warning", "No player pool to verify!")
            return

        # Clear debug display
        self.debug_display.clear()
        self.debug_log("=== ENRICHMENT VERIFICATION ===\n")

        # Sample different player types
        test_groups = {
            'High Salary Pitcher': next((p for p in self.system.player_pool
                                         if p.is_pitcher and p.salary >= 9000), None),
            'Min Salary Hitter': next((p for p in self.system.player_pool
                                       if not p.is_pitcher and p.salary <= 3000), None),
            'Confirmed Player': next((p for p in self.system.player_pool
                                      if getattr(p, 'is_confirmed', False)), None),
        }

        for group_name, player in test_groups.items():
            if not player:
                self.debug_log(f"{group_name}: NOT FOUND")
                continue

            self.debug_log(f"\n{group_name}: {player.name} (${player.salary})")
            self.debug_log("-" * 50)

            # Check all attributes
            attrs_to_check = [
                ('base_projection', 'Base DK Projection'),
                ('AvgPointsPerGame', 'Avg Points (CSV)'),
                ('team_total', 'Vegas Team Total'),
                ('park_factor', 'Park Factor'),
                ('weather_impact', 'Weather Impact'),
                ('recent_form', 'Recent Form'),
                ('consistency_score', 'Consistency'),
                ('batting_order', 'Batting Order'),
                ('is_confirmed', 'Confirmed Status'),
                ('cash_score', 'Cash Score'),
                ('gpp_score', 'GPP Score'),
                ('optimization_score', 'Optimization Score')
            ]

            for attr, label in attrs_to_check:
                value = getattr(player, attr, 'MISSING')
                if value == 'MISSING':
                    self.debug_log(f"  ❌ {label}: MISSING")
                else:
                    self.debug_log(f"  ✅ {label}: {value}")

            # Check for Statcast data
            if hasattr(player, 'recent_avg'):
                self.debug_log(f"  ✅ Statcast AVG: {player.recent_avg}")
            elif hasattr(player, 'recent_velocity'):
                self.debug_log(f"  ✅ Statcast Velo: {player.recent_velocity}")
            else:
                self.debug_log(f"  ❌ Statcast: NO DATA")

        # Summary stats
        self.debug_log("\n=== ENRICHMENT SUMMARY ===")
        total = len(self.system.player_pool)

        for attr in ['team_total', 'park_factor', 'weather_impact', 'recent_form']:
            count = sum(1 for p in self.system.player_pool
                        if hasattr(p, attr) and getattr(p, attr) != 'MISSING')
            pct = (count / total * 100) if total > 0 else 0
            self.debug_log(f"{attr}: {count}/{total} ({pct:.1f}%)")

    def verify_full_system(self):
        """Complete system verification"""
        self.debug_log("\n=== FULL SYSTEM VERIFICATION ===")

        if not self.system.player_pool:
            self.debug_log("❌ No player pool!")
            return

        # Check a sample player
        player = self.system.player_pool[0]
        self.debug_log(f"\nChecking {player.name}:")

        # Check all attributes
        attrs = {
            'base_projection': 'Base DK Projection',
            'recent_form': 'Recent Form',
            'consistency_score': 'Consistency',
            'park_factor': 'Park Factor',
            'weather_impact': 'Weather Impact',
            'team_total': 'Vegas Total',
            'cash_score': 'Cash Score',
            'gpp_score': 'GPP Score'
        }

        all_good = True
        for attr, label in attrs.items():
            value = getattr(player, attr, 'MISSING')
            if value == 'MISSING' or value == 0:
                self.debug_log(f"  ❌ {label}: {value}")
                all_good = False
            else:
                self.debug_log(f"  ✅ {label}: {value}")

        # Test scoring
        if hasattr(self.system, 'scoring_engine'):
            cash = self.system.scoring_engine.score_player_cash(player)
            gpp = self.system.scoring_engine.score_player_gpp(player)

            if player.base_projection > 0:
                cash_mult = cash / player.base_projection
                gpp_mult = gpp / player.base_projection
                self.debug_log(f"\n  Cash multiplier: {cash_mult:.2f}x")
                self.debug_log(f"  GPP multiplier: {gpp_mult:.2f}x")

                if cash_mult < 0.8:
                    self.debug_log("  ⚠️ Cash multiplier too low!")

        if all_good:
            self.debug_log("\n✅ System fully operational!")
        else:
            self.debug_log("\n❌ System has issues - check above")

    # In your SimplifiedDFSOptimizer class, add this method:

    def test_imports(self):
        """Test all import paths"""
        import os
        import sys

        self.debug_log("\n=== IMPORT PATH TEST ===")
        self.debug_log(f"Current working dir: {os.getcwd()}")
        self.debug_log(f"Script dir: {os.path.dirname(os.path.abspath(__file__))}")

        # Check if files exist
        files_to_check = [
            'park_factors.py',
            'vegas_lines.py',
            'weather_integration.py',
            '../park_factors.py',  # Parent directory
            '../vegas_lines.py',
            '../weather_integration.py'
        ]

        for file in files_to_check:
            full_path = os.path.join(os.path.dirname(__file__), file)
            exists = os.path.exists(full_path)
            self.debug_log(f"{file}: {'✅ EXISTS' if exists else '❌ NOT FOUND'}")
            if exists:
                self.debug_log(f"  Full path: {os.path.abspath(full_path)}")


    def test_real_enrichments(self):
        """Test the real data enrichment system"""
        self.debug_log("\n=== TESTING REAL DATA SOURCES ===")

        try:
            from main_optimizer.real_data_enrichments import (
                RealStatcastFetcher,
                RealWeatherIntegration,
                check_and_install_dependencies
            )

            # Check dependencies
            self.debug_log("Checking dependencies...")
            if check_and_install_dependencies():
                self.debug_log("✅ All dependencies installed!")

                # Test on a known player - use the EXISTING method
                self.debug_log("\nTesting Statcast data...")
                stats = RealStatcastFetcher()

                # Test a few players
                test_players = ["Aaron Judge", "Shohei Ohtani", "Mike Trout"]

                for player_name in test_players:
                    try:
                        # Use the existing get_recent_stats method
                        data = stats.get_recent_stats(player_name, days=7)

                        if data.get('games_analyzed', 0) > 0:
                            self.debug_log(
                                f"✅ {player_name}: {data.get('games_analyzed')} games, form={data.get('recent_form', 1.0):.3f}")
                        else:
                            # Try 14 days
                            data = stats.get_recent_stats(player_name, days=14)
                            if data.get('games_analyzed', 0) > 0:
                                self.debug_log(
                                    f"✅ {player_name}: {data.get('games_analyzed')} games (14d), form={data.get('recent_form', 1.0):.3f}")
                            else:
                                self.debug_log(f"⚠️ {player_name}: No recent games")

                    except Exception as e:
                        self.debug_log(f"Error with {player_name}: {e}")

                # Test weather
                self.debug_log("\nTesting Weather data...")
                weather = RealWeatherIntegration()
                weather_data = weather.get_game_weather('NYY')
                self.debug_log(
                    f"Yankees weather: Temp={weather_data.get('temperature')}°F, Impact={weather_data.get('weather_impact')}")

            else:
                self.debug_log("❌ Missing dependencies")

        except ImportError as e:
            self.debug_log(f"❌ Import Error: {e}")
            self.debug_log("Make sure real_data_enrichments.py exists in main_optimizer/")
        except Exception as e:
            self.debug_log(f"❌ Error: {e}")
            import traceback
            self.debug_log(traceback.format_exc())

    def test_ownership_projections(self):
        """Test ownership projection system"""
        if not self.system.player_pool:
            self.debug_log("No players to test!")
            return

        self.debug_log("\n=== OWNERSHIP PROJECTION TEST ===")

        # Get highest owned players
        by_ownership = sorted(self.system.player_pool,
                              key=lambda p: getattr(p, 'ownership_projection', 0),
                              reverse=True)

        self.debug_log("\nHIGHEST PROJECTED OWNERSHIP:")
        for p in by_ownership[:10]:
            own = getattr(p, 'ownership_projection', 0)
            self.debug_log(f"{p.name:<20} ${p.salary:<6,} {own:>5.1f}%")

        # Check for value plays
        self.debug_log("\nVALUE PLAYS (<$4000):")
        value_plays = [p for p in self.system.player_pool if p.salary <= 4000]
        value_by_own = sorted(value_plays,
                              key=lambda p: getattr(p, 'ownership_projection', 0),
                              reverse=True)[:5]

        for p in value_by_own:
            own = getattr(p, 'ownership_projection', 0)
            self.debug_log(f"{p.name:<20} ${p.salary:<6,} {own:>5.1f}%")

        # Check pitcher ownership
        self.debug_log("\nPITCHER OWNERSHIP:")
        pitchers = [p for p in self.system.player_pool if p.is_pitcher]
        pitcher_by_own = sorted(pitchers,
                                key=lambda p: getattr(p, 'ownership_projection', 0),
                                reverse=True)[:5]

        for p in pitcher_by_own:
            own = getattr(p, 'ownership_projection', 0)
            opp = getattr(p, 'opponent_implied_total', 'N/A')
            self.debug_log(f"{p.name:<20} ${p.salary:<6,} {own:>5.1f}% (vs {opp})")

        # Show ownership distribution
        self.debug_log("\nOWNERSHIP DISTRIBUTION:")
        own_ranges = {
            "0-5%": 0,
            "5-10%": 0,
            "10-15%": 0,
            "15-20%": 0,
            "20-30%": 0,
            "30%+": 0
        }

        for p in self.system.player_pool:
            own = getattr(p, 'ownership_projection', 0)
            if own <= 5:
                own_ranges["0-5%"] += 1
            elif own <= 10:
                own_ranges["5-10%"] += 1
            elif own <= 15:
                own_ranges["10-15%"] += 1
            elif own <= 20:
                own_ranges["15-20%"] += 1
            elif own <= 30:
                own_ranges["20-30%"] += 1
            else:
                own_ranges["30%+"] += 1

        for range_name, count in own_ranges.items():
            self.debug_log(f"  {range_name}: {count} players")

    def test_scoring_with_breakdown(self):
        """Test scoring with detailed breakdown"""
        if not self.system.player_pool:
            self.debug_log("No players to test!")
            return

        self.debug_log("\n=== SCORING BREAKDOWN TEST ===")

        # Test a few players
        test_players = self.system.player_pool[:5]

        for player in test_players:
            self.debug_log(f"\n{player.name} (${player.salary}):")

            # Get breakdown for both contest types
            cash_breakdown = self.system.scoring_engine.get_scoring_summary(player, 'cash')
            gpp_breakdown = self.system.scoring_engine.get_scoring_summary(player, 'gpp')

            self.debug_log(f"  Base: {cash_breakdown['base_projection']:.1f}")
            self.debug_log(f"  Cash: {cash_breakdown['final_score']:.1f} ({cash_breakdown['total_multiplier']:.2f}x)")
            self.debug_log(f"  GPP:  {gpp_breakdown['final_score']:.1f} ({gpp_breakdown['total_multiplier']:.2f}x)")

            # Show components
            self.debug_log("  Components:")
            for key, value in gpp_breakdown['components'].items():
                self.debug_log(f"    {key}: {value}")

    def test_scoring_engine(self):
        """Test the scoring engine with sample players"""
        if not self.system.player_pool:
            QMessageBox.warning(self, "Warning", "No player pool to test!")
            return

        self.debug_display.clear()
        self.debug_log("=== SCORING ENGINE TEST ===\n")

        # Get scoring engine
        if not hasattr(self.system, 'scoring_engine'):
            from enhanced_scoring_engine import EnhancedScoringEngine
            self.system.scoring_engine = EnhancedScoringEngine()

        # Test a few players
        test_players = self.system.player_pool[:3]

        for player in test_players:
            self.debug_log(f"\nTesting: {player.name}")
            self.debug_log(f"Base projection: {getattr(player, 'base_projection', 0)}")

            # Calculate both scores
            cash_score = self.system.scoring_engine.score_player_cash(player)
            gpp_score = self.system.scoring_engine.score_player_gpp(player)

            self.debug_log(f"Cash score: {cash_score:.2f}")
            self.debug_log(f"GPP score: {gpp_score:.2f}")

            # Show multipliers
            if player.base_projection > 0:
                cash_mult = cash_score / player.base_projection
                gpp_mult = gpp_score / player.base_projection
                self.debug_log(f"Cash multiplier: {cash_mult:.2f}x")
                self.debug_log(f"GPP multiplier: {gpp_mult:.2f}x")

    def dump_player_data(self):
        """Dump complete data for a few players"""
        if not self.system.player_pool:
            return

        # Get top 3 by score
        contest_type = self.contest_type.currentText().lower()
        score_attr = 'cash_score' if contest_type == 'cash' else 'gpp_score'

        top_players = sorted(self.system.player_pool,
                             key=lambda p: getattr(p, score_attr, 0),
                             reverse=True)[:3]

        output = f"=== TOP 3 PLAYERS BY {score_attr.upper()} ===\n\n"

        for player in top_players:
            output += f"{player.name}:\n"
            output += "-" * 40 + "\n"

            # Dump all attributes
            for attr in sorted(dir(player)):
                if not attr.startswith('_'):
                    try:
                        value = getattr(player, attr)
                        if not callable(value):
                            output += f"  {attr}: {value}\n"
                    except:
                        pass

            output += "\n"

        # Save to clipboard
        QApplication.clipboard().setText(output)
        self.debug_log("Player data copied to clipboard!")

    def debug_player_attributes(self):
        """Debug what attributes players actually have"""
        if not self.system.player_pool:
            self.debug_log("No players to debug!")
            return

        player = self.system.player_pool[0]
        self.debug_log("\n=== PLAYER ATTRIBUTE DEBUG ===")
        self.debug_log(f"Checking player: {player.name}")

        # Check all numeric attributes
        for attr in dir(player):
            if not attr.startswith('_'):
                try:
                    value = getattr(player, attr)
                    if isinstance(value, (int, float)) and not callable(value):
                        self.debug_log(f"  {attr}: {value}")
                except:
                    pass

    def debug_log(self, message):
        """Add to debug log"""
        if self.debug_mode:
            current = self.debug_display.toPlainText()
            self.debug_display.setText(f"{current}\n{message}" if current else message)
            # Auto-scroll to bottom
            cursor = self.debug_display.textCursor()
            cursor.movePosition(cursor.End)
            self.debug_display.setTextCursor(cursor)

    def update_debug_panel(self, enrichment_results):
        """Update the debug panel with enrichment stats"""
        # Get total from player pool length, not from enrichment_results
        total_players = len(self.system.player_pool)

        # Enrichment stats
        stats_text = f"""Total Players: {total_players}
    Vegas Data: {enrichment_results.get('vegas', 0)} ({enrichment_results.get('vegas', 0) / total_players * 100:.1f}%)
    Weather: {enrichment_results.get('weather', 0)} ({enrichment_results.get('weather', 0) / total_players * 100:.1f}%)
    Park Factors: {enrichment_results.get('park', 0)} ({enrichment_results.get('park', 0) / total_players * 100:.1f}%)
    Stats/Form: {enrichment_results.get('stats', 0)} ({enrichment_results.get('stats', 0) / total_players * 100:.1f}%)
    Confirmed: {sum(1 for p in self.system.player_pool if getattr(p, 'is_confirmed', False))}"""

        self.enrichment_stats.setText(stats_text)

        # Sample player details
        if self.system.player_pool:
            sample = self.system.player_pool[0]
            details = f"""Player: {sample.name}
    Team: {sample.team}
    Salary: ${sample.salary}
    Base Proj: {getattr(sample, 'base_projection', 'N/A')}
    Vegas Total: {getattr(sample, 'team_total', 'N/A')}
    Park Factor: {getattr(sample, 'park_factor', 'N/A')}
    Weather: {getattr(sample, 'weather_impact', 'N/A')}
    Form: {getattr(sample, 'recent_form', 'N/A')}
    Cash Score: {getattr(sample, 'cash_score', 'N/A')}
    GPP Score: {getattr(sample, 'gpp_score', 'N/A')}"""

            self.sample_player_details.setText(details)


# Make it runnable as standalone
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimplifiedDFSOptimizer()
    window.show()

    # Auto-enable debug for testing
    window.debug_cb.setChecked(True)

    sys.exit(app.exec_())