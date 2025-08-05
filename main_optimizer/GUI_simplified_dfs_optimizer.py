#!/usr/bin/env python3
"""
SIMPLIFIED DFS OPTIMIZER GUI
A standalone 2-button interface with debug mode
"""

import sys
import os
import traceback
from datetime import datetime

# PyQt5 imports
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Your DFS system imports
from unified_core_system import UnifiedCoreSystem
from enhanced_scoring_engine import EnhancedScoringEngine
# If you use pandas for CSV handling
import pandas as pd

# If you need JSON for debugging
import json

# If you use logging
import logging

# Your optimizer
from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig


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
        """Load CSV and set everything up"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select DraftKings CSV",
            "",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        # Store path for later reference
        self.csv_path = file_path

        try:
            # Clear previous data
            self.manual_players.clear()
            self.manual_label.setText("Manual: None")

            # Load CSV
            self.update_status(f"📁 Loading {os.path.basename(file_path)}...")
            self.system.load_players_from_csv(file_path)
            self.update_status(f"✅ Loaded {len(self.system.players)} players")

            # Build initial pool to have players to fix
            self.system.build_player_pool(include_unconfirmed=True)

            # Fix projections using your existing method
            self.fix_base_projections()

            # Fetch confirmations
            self.update_status("🔄 Fetching confirmed lineups...", append=True)
            confirmations = self.system.fetch_confirmed_players()
            if confirmations:
                self.update_status(f"✅ Found {confirmations} confirmed players", append=True)
            else:
                self.update_status("⚠️ No confirmations found (might be too early)", append=True)

            # Auto-detect and select strategy
            self.analyze_and_select_strategy()

            # Rebuild pool with proper settings
            include_unconfirmed = self.contest_type.currentText() == "GPP"
            self.system.build_player_pool(include_unconfirmed=include_unconfirmed)
            self.update_status(f"📊 Player pool: {len(self.system.player_pool)} players", append=True)

            # Enrich player pool
            self.update_status("🔄 Enriching player data...", append=True)
            enrichment_stats = self.system.enrich_player_pool()

            # Check if we got real data
            if isinstance(enrichment_stats, dict):
                vegas_count = enrichment_stats.get('vegas', 0)
                weather_count = enrichment_stats.get('weather', 0)
                park_count = enrichment_stats.get('park', 0)

                # Report what we got
                if vegas_count > 0:
                    self.update_status(f"✅ Vegas data: {vegas_count} players", append=True)
                if weather_count > 0:
                    self.update_status(f"✅ Weather data: {weather_count} players", append=True)
                if park_count > 0:
                    self.update_status(f"✅ Park factors: {park_count} players", append=True)

                # If no real enrichment data, apply static data
                if vegas_count == 0 and weather_count == 0 and park_count == 0:
                    self.update_status("⚠️ APIs returned no real data", append=True)

                    # Test APIs to see what's wrong (only in debug mode)
                    if self.debug_mode:
                        self.update_status("🔍 Testing APIs...", append=True)
                        api_results = self.test_all_apis()

                    # Apply real static data instead
                    if hasattr(self, 'apply_real_static_data'):
                        self.apply_real_static_data()
                        self.update_status("✅ Applied real park factors and team averages", append=True)

            # Score players for current contest type
            contest_type = self.contest_type.currentText().lower()
            self.system.score_players(contest_type)
            self.update_status(f"📊 Scored {len(self.system.player_pool)} players for {contest_type.upper()}",
                               append=True)

            # Verify scoring is working (only in debug mode)
            if self.debug_mode and hasattr(self, 'verify_scoring_multipliers'):
                self.verify_scoring_multipliers()

            # Update displays
            self.update_pool_display()
            self.show_setup_summary()

            # Enable optimize button
            self.optimize_button.setEnabled(True)
            self.update_status("✅ Setup complete! Click OPTIMIZE to generate lineup.", append=True)

        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}", append=True)
            self.debug_log(f"ERROR: {traceback.format_exc()}")

            # Try to recover
            if self.system.players:
                self.update_status("🔧 Attempting recovery...", append=True)
                self.optimize_button.setEnabled(True)

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
                    self.debug_log(f"{attr}: {value}")  # Added missing closing parenthesis

        # Also show string fields that might contain data
        self.debug_log("\n=== STRING FIELDS ===")
        for attr in dir(player):
            if not attr.startswith('_'):
                value = getattr(player, attr)
                if isinstance(value, str) and not callable(value):
                    self.debug_log(f"{attr}: '{value}'")

        # Show all fields sorted by type
        self.debug_log("\n=== ALL PLAYER ATTRIBUTES ===")
        all_attrs = []
        for attr in dir(player):
            if not attr.startswith('_') and not callable(getattr(player, attr)):
                value = getattr(player, attr)
                attr_type = type(value).__name__
                all_attrs.append((attr, value, attr_type))

        # Sort by type then by name
        all_attrs.sort(key=lambda x: (x[2], x[0]))

        for attr, value, attr_type in all_attrs:
            if attr_type == 'str':
                self.debug_log(f"{attr:<25} {attr_type:<10} '{value}'")
            else:
                self.debug_log(f"{attr:<25} {attr_type:<10} {value}")


    def test_data_sources(self):
        """Test each data source individually"""
        self.debug_log("\n=== TESTING DATA SOURCES ===")

        # Test Vegas API
        try:
            from vegas_lines import VegasLines
            vegas = VegasLines()
            self.debug_log("\n1. Testing Vegas Lines...")

            # Try to get data for a known team
            test_teams = ['NYY', 'LAD', 'HOU']
            for team in test_teams:
                # Create a dummy player to test
                class TestPlayer:
                    def __init__(self, team):
                        self.team = team
                        self.name = f"Test {team}"

                test_player = TestPlayer(team)
                vegas.enrich_player(test_player)

                if hasattr(test_player, 'team_total'):
                    self.debug_log(f"   ✅ {team}: {test_player.team_total} runs")
                else:
                    self.debug_log(f"   ❌ {team}: No data")
        except Exception as e:
            self.debug_log(f"   ❌ Vegas API Error: {str(e)}")

        # Test Weather API
        try:
            from weather_integration import WeatherIntegration
            weather = WeatherIntegration()
            self.debug_log("\n2. Testing Weather...")

            data = weather.get_game_weather('NYY')
            if data:
                self.debug_log(f"   ✅ Weather data: {data}")
            else:
                self.debug_log(f"   ❌ No weather data")
        except Exception as e:
            self.debug_log(f"   ❌ Weather API Error: {str(e)}")

        # Test Park Factors
        try:
            from park_factors import ParkFactors
            parks = ParkFactors()
            self.debug_log("\n3. Testing Park Factors...")

            factor = parks.get_park_factor('COL')
            self.debug_log(f"   ✅ Coors Field factor: {factor}")
        except Exception as e:
            self.debug_log(f"   ❌ Park Factors Error: {str(e)}")

    def debug_vegas_data(self):
        """Debug what Vegas actually returns"""
        from vegas_lines import VegasLines
        vegas = VegasLines()

        print("\n=== VEGAS DEBUG ===")

        # Test what get_vegas_lines returns
        lines = vegas.get_vegas_lines()
        print(f"get_vegas_lines type: {type(lines)}")
        if lines:
            print(f"Sample data: {list(lines.items())[:2]}")

        # Test apply_to_players with one player
        class TestPlayer:
            def __init__(self):
                self.name = "Aaron Judge"
                self.team = "NYY"

        test = TestPlayer()
        vegas.apply_to_players([test])

        print(f"\nAfter apply_to_players:")
        for attr in dir(test):
            if not attr.startswith('_'):
                print(f"  {attr}: {getattr(test, attr)}")



    def debug_enrichment_data(self):
        """Check what enrichment data we have"""
        self.debug_log("\n=== ENRICHMENT DEBUG ===")

        # Check a few players
        sample_size = min(5, len(self.system.player_pool))
        for i, player in enumerate(self.system.player_pool[:sample_size]):
            self.debug_log(f"\n{i + 1}. {player.name} ({player.team}):")
            self.debug_log(f"   Position: {player.primary_position}")
            self.debug_log(f"   Salary: ${player.salary:,}")
            self.debug_log(f"   Base Projection: {getattr(player, 'base_projection', 'MISSING')}")
            self.debug_log(f"   DFF Projection: {getattr(player, 'dff_projection', 'MISSING')}")
            self.debug_log(f"   Team Total: {getattr(player, 'implied_team_score', 'MISSING')}")
            self.debug_log(f"   Batting Order: {getattr(player, 'batting_order', 'MISSING')}")
            self.debug_log(f"   Weather Impact: {getattr(player, 'weather_impact', 'MISSING')}")
            self.debug_log(f"   Park Factor: {getattr(player, 'park_factor', 'MISSING')}")
            self.debug_log(f"   Recent Form: {getattr(player, 'recent_form', 'MISSING')}")
            self.debug_log(f"   Ownership Proj: {getattr(player, 'ownership_projection', 'MISSING')}")

    def verify_scoring_multipliers(self):
        """Check if scoring is applying multipliers correctly"""
        self.debug_log("\n=== SCORING VERIFICATION ===")

        # Find players with different characteristics
        test_cases = [
            ("High Salary Pitcher", lambda p: p.is_pitcher and p.salary >= 9000),
            ("Low Salary Hitter", lambda p: not p.is_pitcher and p.salary <= 3000),
            ("Mid Salary Hitter", lambda p: not p.is_pitcher and 4000 <= p.salary <= 6000)
        ]

        for label, condition in test_cases:
            player = next((p for p in self.system.player_pool if condition(p)), None)
            if player:
                self.debug_log(f"\n{label}: {player.name}")
                self.debug_log(f"  Base Projection: {player.base_projection}")
                self.debug_log(f"  Cash Score: {player.cash_score}")
                if player.base_projection > 0:
                    multiplier = player.cash_score / player.base_projection
                    self.debug_log(f"  Multiplier: {multiplier:.2f}x")

                    if multiplier > 1.05:
                        self.debug_log("  ✅ Enhancements ARE being applied!")
                    elif 0.95 <= multiplier <= 1.05:
                        self.debug_log("  ⚠️ Default multipliers (no real enrichment)")
                    else:
                        self.debug_log("  📉 Negative multipliers applied")

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

        # Count unique games
        teams = set(p.team for p in self.system.players if hasattr(p, 'team'))
        num_games = len(teams) // 2  # Rough estimate

        # Store for debugging
        self.detected_games = num_games

        # Determine slate size - MATCHING StrategyAutoSelector thresholds
        if is_showdown:
            slate_size = 'showdown'
        elif num_games <= 4:  # 1-4 games = small
            slate_size = 'small'
        elif num_games <= 9:  # 5-9 games = medium
            slate_size = 'medium'
        else:  # 10+ games = large
            slate_size = 'large'

        # Select strategy based on contest type and slate size
        contest_type = self.contest_type.currentText().lower()

        # Use the strategy registry - FIXED MAPPINGS
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
                    'medium': 'truly_smart_stack',  # FIXED from 'smart_stack'
                    'large': 'matchup_leverage_stack'
                }
            }

            self.selected_strategy = strategies.get(contest_type, strategies['gpp']).get(
                slate_size, 'balanced_optimal'
            )

        # Update display with detection info
        self.update_status(f"📊 Detected: {num_games} games = {slate_size} slate", append=True)
        self.update_status(f"🎯 Strategy: {self.selected_strategy} ({contest_type})", append=True)

        # Store slate info for debugging
        self.slate_info = {
            'games': num_games,
            'size': slate_size,
            'contest': contest_type,
            'strategy': self.selected_strategy
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
    🎮 Games: {getattr(self, 'detected_games', '?')}
    📏 Slate Size: {getattr(self, 'slate_info', {}).get('size', '?')}
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
            # Final check on strategy
            self.update_status(f"🚀 Optimizing {contest_type.upper()} lineup...", append=True)
            self.update_status(f"📋 Strategy: {self.selected_strategy}", append=True)

            # Debug slate info
            if hasattr(self, 'slate_info'):
                self.update_status(f"📊 Slate: {self.slate_info['games']} games ({self.slate_info['size']})",
                                   append=True)

            # Run optimization
            lineups = self.system.optimize_lineups(
                num_lineups=1,
                strategy=self.selected_strategy,
                contest_type=contest_type,
                min_unique_players=3
            )

            if lineups and lineups[0]:
                self.display_lineup(lineups[0])
                self.update_status("✅ Optimization complete!", append=True)

                # Debug: Check what scores were used
                if self.debug_mode:
                    lineup = lineups[0]
                    self.debug_log("\n=== LINEUP SCORES ===")
                    for player in lineup['players']:
                        self.debug_log(f"{player.name}: base={player.base_projection:.1f}, "
                                       f"opt_score={getattr(player, 'optimization_score', 0):.1f}")
            else:
                self.update_status("❌ No valid lineups found", append=True)
                self.debug_log("Failed to generate lineup - check constraints")

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

    def test_all_apis(self):
        """Test each API to see what's actually working"""
        self.debug_log("\n=== COMPREHENSIVE API TEST ===")

        results = {
            'vegas': False,
            'weather': False,
            'park': False,
            'stats': False
        }

        # 1. Test Vegas Lines
        self.debug_log("\n1. VEGAS LINES API TEST:")
        try:
            from vegas_lines import VegasLines
            vegas = VegasLines()

            # Check if it has the right methods
            self.debug_log(f"   Methods available: {[m for m in dir(vegas) if not m.startswith('_')]}")

            # Try different approaches
            if hasattr(vegas, 'get_game_totals'):
                totals = vegas.get_game_totals()
                self.debug_log(f"   Game totals: {totals}")
                if totals:
                    results['vegas'] = True

            if hasattr(vegas, 'fetch_current_lines'):
                lines = vegas.fetch_current_lines()
                self.debug_log(f"   Current lines: {lines}")
                if lines:
                    results['vegas'] = True

        except Exception as e:
            self.debug_log(f"   ❌ Vegas API Error: {str(e)}")

        # 2. Test Weather API
        self.debug_log("\n2. WEATHER API TEST:")
        try:
            from weather_integration import WeatherIntegration
            weather = WeatherIntegration()

            # Test for today's games
            test_stadiums = ['Yankee Stadium', 'Fenway Park', 'Dodger Stadium']
            for stadium in test_stadiums:
                try:
                    data = weather.get_weather_for_stadium(stadium)
                    if data:
                        self.debug_log(f"   ✅ {stadium}: {data}")
                        results['weather'] = True
                        break
                except:
                    pass

        except Exception as e:
            self.debug_log(f"   ❌ Weather API Error: {str(e)}")

        # 3. Test Real Stats
        self.debug_log("\n3. STATCAST API TEST:")
        try:
            # Try different possible module names
            stats_module_found = False
            stats = None

            # Try different import names that might exist in your project
            try:
                from simple_statcast_fetcher import SimpleStatcastFetcher
                stats = SimpleStatcastFetcher()
                stats_module_found = True
            except ImportError:
                try:
                    from statcast_fetcher import StatcastFetcher
                    stats = StatcastFetcher()
                    stats_module_found = True
                except ImportError:
                    try:
                        from real_data_enrichments import RealDataEnrichments
                        stats = RealDataEnrichments()
                        stats_module_found = True
                    except ImportError:
                        self.debug_log("   ❌ No Statcast module found - skipping test")

            if stats_module_found and stats:
                # Test a known player
                test_players = ['Aaron Judge', 'Shohei Ohtani', 'Ronald Acuna Jr.']
                for player_name in test_players:
                    try:
                        # Try different method names
                        data = None
                        if hasattr(stats, 'get_recent_stats'):
                            data = stats.get_recent_stats(player_name, days=7)
                        elif hasattr(stats, 'get_player_stats'):
                            data = stats.get_player_stats(player_name)
                        elif hasattr(stats, 'fetch_stats'):
                            data = stats.fetch_stats(player_name)

                        if data and data.get('games_analyzed', 0) > 0:
                            self.debug_log(f"   ✅ {player_name}: {data.get('games_analyzed')} games")
                            results['stats'] = True
                            break
                    except Exception as e:
                        self.debug_log(f"   Error testing {player_name}: {str(e)}")

        except Exception as e:
            self.debug_log(f"   ❌ Statcast API Error: {str(e)}")

            # Test a known player
            test_players = ['Aaron Judge', 'Shohei Ohtani', 'Ronald Acuna Jr.']
            for player_name in test_players:
                try:
                    data = stats.get_recent_stats(player_name, days=7)
                    if data and data.get('games_analyzed', 0) > 0:
                        self.debug_log(f"   ✅ {player_name}: {data.get('games_analyzed')} games")
                        results['stats'] = True
                        break
                except:
                    pass

        except Exception as e:
            self.debug_log(f"   ❌ Statcast API Error: {str(e)}")

        # Summary
        self.debug_log("\n=== API TEST SUMMARY ===")
        for api, working in results.items():
            status = "✅ WORKING" if working else "❌ NOT WORKING"
            self.debug_log(f"   {api.upper()}: {status}")

        return results

    def debug_enrichment_apis(self):
        """Test each enrichment API individually"""
        self.debug_log("\n=== TESTING ENRICHMENT APIs ===")

        # Get a test player
        if not self.system.player_pool:
            self.debug_log("No players in pool to test!")
            return

        test_player = self.system.player_pool[0]
        self.debug_log(f"Test player: {test_player.name} ({test_player.team})")

        # 1. Test Vegas
        self.debug_log("\n1. VEGAS TEST:")
        try:
            from vegas_lines import VegasLines
            vegas = VegasLines()

            # Create a copy to test
            test_copy = type('Player', (), {})()
            test_copy.name = test_player.name
            test_copy.team = test_player.team

            # Try to enrich
            vegas.enrich_player(test_copy)

            # Check what was added
            for attr in ['team_total', 'implied_team_score', 'game_total', 'vegas_score']:
                if hasattr(test_copy, attr):
                    self.debug_log(f"   {attr}: {getattr(test_copy, attr)}")

            if not any(hasattr(test_copy, attr) for attr in ['team_total', 'implied_team_score']):
                self.debug_log("   ❌ No Vegas data added")

        except Exception as e:
            self.debug_log(f"   ❌ Vegas error: {str(e)}")

        # 2. Test Weather
        self.debug_log("\n2. WEATHER TEST:")
        try:
            from weather_integration import WeatherIntegration
            weather = WeatherIntegration()

            # Test method
            result = weather.get_game_weather(test_player.team)
            self.debug_log(f"   Result: {result}")

        except Exception as e:
            self.debug_log(f"   ❌ Weather error: {str(e)}")

        # 3. Test Park Factors
        self.debug_log("\n3. PARK FACTORS TEST:")
        try:
            from park_factors import ParkFactors
            parks = ParkFactors()

            # Test method
            factor = parks.get_park_factor(test_player.team)
            self.debug_log(f"   {test_player.team} park factor: {factor}")

        except Exception as e:
            self.debug_log(f"   ❌ Park factors error: {str(e)}")

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