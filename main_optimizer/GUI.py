#!/usr/bin/env python3
"""
DFS OPTIMIZER GUI - UPDATED VERSION
====================================
Integrates new scoring, smart enrichment, and strategy management
"""

import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime
from typing import List, Dict, Set

# Add to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the UPDATED core system
from unified_core_system_updated import UnifiedCoreSystem
from gui_strategy_configuration import GUIStrategyManager


class SimplifiedDFSOptimizerGUI(QMainWindow):
    """
    UPDATED GUI with:
    1. Smart strategy selection
    2. Proper enrichment based on strategy
    3. Clean strategy dropdown (only proven strategies)
    """

    def __init__(self):
        super().__init__()

        # Initialize systems
        self.system = UnifiedCoreSystem()
        self.strategy_manager = GUIStrategyManager()

        # State tracking
        self.csv_loaded = False
        self.detected_games = 0
        self.detected_slate_size = 'medium'
        self.manual_selections = set()

        # Setup UI
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("DFS Optimizer - Professional Edition")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Main Optimizer
        self.create_optimizer_tab()

        # Tab 2: Results
        self.create_results_tab()

        # Tab 3: Debug (optional)
        self.create_debug_tab()

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def create_optimizer_tab(self):
        """Create the main optimizer tab"""
        optimizer_widget = QWidget()
        self.tabs.addTab(optimizer_widget, "Optimizer")

        layout = QVBoxLayout(optimizer_widget)

        # ========== FILE SECTION ==========
        file_group = QGroupBox("1. Load Data")
        file_layout = QHBoxLayout()

        self.csv_label = QLabel("No file loaded")
        file_layout.addWidget(self.csv_label)

        self.load_csv_btn = QPushButton("Load CSV")
        self.load_csv_btn.clicked.connect(self.load_csv)
        file_layout.addWidget(self.load_csv_btn)

        self.fetch_confirmations_btn = QPushButton("Fetch Confirmations")
        self.fetch_confirmations_btn.clicked.connect(self.fetch_confirmations)
        self.fetch_confirmations_btn.setEnabled(False)
        file_layout.addWidget(self.fetch_confirmations_btn)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # ========== SETTINGS SECTION ==========
        settings_group = QGroupBox("2. Contest Settings")
        settings_layout = QGridLayout()

        # Contest Type
        settings_layout.addWidget(QLabel("Contest Type:"), 0, 0)
        self.contest_combo = QComboBox()
        self.contest_combo.addItems(["Cash", "GPP"])
        self.contest_combo.currentTextChanged.connect(self.on_contest_changed)
        settings_layout.addWidget(self.contest_combo, 0, 1)

        # Strategy Selection
        settings_layout.addWidget(QLabel("Strategy:"), 0, 2)
        self.strategy_combo = QComboBox()
        self.setup_strategy_dropdown()  # NEW METHOD
        settings_layout.addWidget(self.strategy_combo, 0, 3)

        # Slate Info Display
        self.slate_info_label = QLabel("Slate: Not detected")
        self.slate_info_label.setStyleSheet("font-weight: bold; color: blue;")
        settings_layout.addWidget(self.slate_info_label, 1, 0, 1, 2)

        # Strategy Info Display
        self.strategy_info_label = QLabel("")
        self.strategy_info_label.setStyleSheet("color: green;")
        settings_layout.addWidget(self.strategy_info_label, 1, 2, 1, 2)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # ========== POOL SECTION ==========
        pool_group = QGroupBox("3. Player Pool")
        pool_layout = QVBoxLayout()

        pool_controls = QHBoxLayout()

        self.confirmed_only_cb = QCheckBox("Confirmed Only")
        self.confirmed_only_cb.setChecked(True)
        pool_controls.addWidget(self.confirmed_only_cb)

        self.pool_size_label = QLabel("Pool: 0 players")
        pool_controls.addWidget(self.pool_size_label)

        pool_controls.addStretch()

        self.rebuild_pool_btn = QPushButton("Rebuild Pool")
        self.rebuild_pool_btn.clicked.connect(self.rebuild_pool)
        self.rebuild_pool_btn.setEnabled(False)
        pool_controls.addWidget(self.rebuild_pool_btn)

        pool_layout.addLayout(pool_controls)

        # Manual selections
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Manual Add:"))
        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Player name...")
        manual_layout.addWidget(self.manual_input)

        self.add_manual_btn = QPushButton("Add")
        self.add_manual_btn.clicked.connect(self.add_manual_selection)
        manual_layout.addWidget(self.add_manual_btn)

        self.manual_count_label = QLabel("Manual: 0")
        manual_layout.addWidget(self.manual_count_label)

        pool_layout.addLayout(manual_layout)

        pool_group.setLayout(pool_layout)
        layout.addWidget(pool_group)

        # ========== OPTIMIZATION SECTION ==========
        optimize_group = QGroupBox("4. Optimize")
        optimize_layout = QVBoxLayout()

        opt_controls = QHBoxLayout()

        opt_controls.addWidget(QLabel("Lineups:"))
        self.lineups_spin = QSpinBox()
        self.lineups_spin.setRange(1, 150)
        self.lineups_spin.setValue(1)
        opt_controls.addWidget(self.lineups_spin)

        opt_controls.addStretch()

        self.optimize_btn = QPushButton("OPTIMIZE")
        self.optimize_btn.clicked.connect(self.run_optimization)
        self.optimize_btn.setEnabled(False)
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        opt_controls.addWidget(self.optimize_btn)

        optimize_layout.addLayout(opt_controls)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        optimize_layout.addWidget(self.progress_bar)

        # Status display
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        optimize_layout.addWidget(self.status_text)

        optimize_group.setLayout(optimize_layout)
        layout.addWidget(optimize_group)

    def setup_strategy_dropdown(self):
        """
        NEW METHOD: Setup strategy dropdown with only proven strategies
        """
        self.strategy_combo.clear()

        # Get strategies from manager
        strategies = self.strategy_manager.get_gui_strategies()

        # Add Auto option first
        self.strategy_combo.addItem("🤖 Auto-Select", "auto")
        self.strategy_combo.insertSeparator(1)

        # Add Cash strategies
        self.strategy_combo.addItem("── Cash Strategies ──", None)
        last_index = self.strategy_combo.count() - 1
        self.strategy_combo.model().item(last_index).setEnabled(False)

        for strategy in strategies.get('Cash (50/50, Double-Up)', []):
            desc = self.strategy_manager.get_strategy_description(strategy)
            self.strategy_combo.addItem(f"  {strategy}", strategy)
            self.strategy_combo.setItemData(
                self.strategy_combo.count() - 1,
                desc,
                Qt.ToolTipRole
            )

        self.strategy_combo.insertSeparator(self.strategy_combo.count())

        # Add GPP strategies
        self.strategy_combo.addItem("── GPP Strategies ──", None)
        last_index = self.strategy_combo.count() - 1
        self.strategy_combo.model().item(last_index).setEnabled(False)

        for strategy in strategies.get('GPP (Tournaments)', []):
            desc = self.strategy_manager.get_strategy_description(strategy)
            self.strategy_combo.addItem(f"  {strategy}", strategy)
            self.strategy_combo.setItemData(
                self.strategy_combo.count() - 1,
                desc,
                Qt.ToolTipRole
            )

    def create_results_tab(self):
        """Create results display tab"""
        results_widget = QWidget()
        self.tabs.addTab(results_widget, "Results")

        layout = QVBoxLayout(results_widget)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "Lineup", "Score", "Projection", "Salary", "Ownership",
            "Teams", "Max Stack", "Strategy"
        ])

        # Make table read-only but selectable
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)

        # Connect row click to show details
        self.results_table.clicked.connect(self.on_lineup_clicked)

        layout.addWidget(self.results_table)

        # Details display area
        self.lineup_details = QTextEdit()
        self.lineup_details.setReadOnly(True)
        self.lineup_details.setMaximumHeight(200)
        self.lineup_details.setPlaceholderText("Click a lineup to see details...")
        layout.addWidget(self.lineup_details)

        # Store lineups for display
        self.displayed_lineups = []

    def create_debug_tab(self):
        """Create debug tab for troubleshooting"""
        debug_widget = QWidget()
        self.tabs.addTab(debug_widget, "Debug")

        layout = QVBoxLayout(debug_widget)

        # Debug display
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.debug_text)

        # Debug controls
        debug_controls = QHBoxLayout()

        test_scoring_btn = QPushButton("Test Scoring")
        test_scoring_btn.clicked.connect(self.test_scoring)
        debug_controls.addWidget(test_scoring_btn)

        test_enrichment_btn = QPushButton("Test Enrichment")
        test_enrichment_btn.clicked.connect(self.test_enrichment)
        debug_controls.addWidget(test_enrichment_btn)

        clear_debug_btn = QPushButton("Clear")
        clear_debug_btn.clicked.connect(lambda: self.debug_text.clear())
        debug_controls.addWidget(clear_debug_btn)

        debug_controls.addStretch()
        layout.addLayout(debug_controls)

    def load_csv(self):
        """Load DraftKings CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load DraftKings CSV", "", "CSV Files (*.csv)"
        )

        if not file_path:
            return

        # Load with new system
        count = self.system.load_csv(file_path)

        if count > 0:
            self.csv_loaded = True
            self.csv_label.setText(f"Loaded: {os.path.basename(file_path)} ({count} players)")

            # Auto-detect slate
            self.detect_and_display_slate()

            # Enable buttons
            self.fetch_confirmations_btn.setEnabled(True)
            self.rebuild_pool_btn.setEnabled(True)

            # Build initial pool
            self.rebuild_pool()

            # Update status
            self.update_status(f"Loaded {count} players")
        else:
            QMessageBox.warning(self, "Error", "Failed to load CSV")

    def detect_and_display_slate(self):
        """
        NEW METHOD: Detect slate and update display
        """
        # Get slate info from system
        slate_size = self.system.current_slate_size

        # Count games
        teams = set(p.team for p in self.system.players if hasattr(p, 'team'))
        num_games = len(teams) // 2

        self.detected_games = num_games
        self.detected_slate_size = slate_size

        # Update display
        self.slate_info_label.setText(f"Slate: {num_games} games ({slate_size})")

        # Auto-select strategy if on auto
        if self.strategy_combo.currentData() == "auto":
            self.auto_select_strategy()

    def auto_select_strategy(self):
        """
        NEW METHOD: Auto-select best strategy
        """
        contest_type = self.contest_combo.currentText().lower()

        strategy, reason = self.strategy_manager.auto_select_strategy(
            num_games=self.detected_games,
            contest_type=contest_type
        )

        # Update display
        self.strategy_info_label.setText(f"Strategy: {reason}")

        # Find and select in dropdown (if not auto)
        if strategy != "auto":
            for i in range(self.strategy_combo.count()):
                if self.strategy_combo.itemData(i) == strategy:
                    self.strategy_combo.blockSignals(True)
                    self.strategy_combo.setCurrentIndex(i)
                    self.strategy_combo.blockSignals(False)
                    break

    def on_contest_changed(self):
        """When contest type changes"""
        if self.csv_loaded:
            # Re-select strategy
            if self.strategy_combo.currentData() == "auto":
                self.auto_select_strategy()

            # Re-score players
            contest_type = self.contest_combo.currentText().lower()
            self.system.score_players(contest_type)

            self.update_status(f"Switched to {contest_type.upper()} mode")

    def fetch_confirmations(self):
        """Fetch confirmed lineups"""
        confirmed = self.system.fetch_confirmed_players()

        if confirmed > 0:
            self.update_status(f"Found {confirmed} confirmed players")
            # Rebuild pool to reflect confirmations
            self.rebuild_pool()
        else:
            self.update_status("No confirmations found (might be too early)")

    def rebuild_pool(self):
        """Rebuild player pool"""
        if not self.csv_loaded:
            return

        # Get settings
        include_unconfirmed = not self.confirmed_only_cb.isChecked()

        # Build pool
        pool_size = self.system.build_player_pool(
            include_unconfirmed=include_unconfirmed,
            manual_selections=self.manual_selections
        )

        # Update display
        self.pool_size_label.setText(f"Pool: {pool_size} players")

        # Enable optimize if we have players
        self.optimize_btn.setEnabled(pool_size > 0)

    def add_manual_selection(self):
        """Add manual player selection"""
        player_name = self.manual_input.text().strip()

        if player_name:
            self.manual_selections.add(player_name)
            self.manual_input.clear()
            self.manual_count_label.setText(f"Manual: {len(self.manual_selections)}")

            # Rebuild pool to include manual selection
            self.rebuild_pool()

    def run_optimization(self):
        """
        NEW METHOD: Run optimization with proper pipeline
        """
        if not self.csv_loaded:
            return

        # Get settings
        num_lineups = self.lineups_spin.value()
        contest_type = self.contest_combo.currentText().lower()

        # Get strategy
        strategy_data = self.strategy_combo.currentData()
        if strategy_data == "auto":
            strategy, _ = self.strategy_manager.auto_select_strategy(
                self.detected_games, contest_type
            )
        else:
            strategy = strategy_data

        # Validate strategy
        if not self.strategy_manager.validate_strategy(strategy):
            QMessageBox.warning(self, "Error", f"Invalid strategy: {strategy}")
            return

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, num_lineups)

        # Clear status
        self.status_text.clear()
        self.update_status(f"Optimizing {num_lineups} lineups with {strategy}...")

        # Get manual selections
        manual_str = ",".join(self.manual_selections) if self.manual_selections else ""

        try:
            # Run optimization with new system
            lineups = self.system.optimize_lineup(
                strategy=strategy,
                contest_type=contest_type,
                num_lineups=num_lineups,
                manual_selections=manual_str
            )

            # Display results
            self.display_results(lineups)

            # Update status
            self.update_status(f"Generated {len(lineups)} lineups successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Optimization failed: {str(e)}")
            self.update_status(f"ERROR: {str(e)}")

        finally:
            self.progress_bar.setVisible(False)

    def display_results(self, lineups: List[Dict]):
        """Display optimization results with player details"""
        self.results_table.setRowCount(len(lineups))

        # Store lineups for detail display
        self.displayed_lineups = lineups

        for idx, lineup in enumerate(lineups):
            # Lineup number
            self.results_table.setItem(idx, 0, QTableWidgetItem(f"#{idx + 1}"))

            # Score
            score = lineup.get('optimization_score', 0)
            self.results_table.setItem(idx, 1, QTableWidgetItem(f"{score:.1f}"))

            # Projection
            projection = lineup.get('projection', 0)
            self.results_table.setItem(idx, 2, QTableWidgetItem(f"{projection:.1f}"))

            # Salary
            salary = lineup.get('salary', 0)
            self.results_table.setItem(idx, 3, QTableWidgetItem(f"${salary:,}"))

            # Ownership
            ownership = lineup.get('avg_ownership', 0)
            self.results_table.setItem(idx, 4, QTableWidgetItem(f"{ownership:.1f}%"))

            # Teams
            teams = lineup.get('num_teams', 0)
            self.results_table.setItem(idx, 5, QTableWidgetItem(str(teams)))

            # Max stack
            stack = lineup.get('max_stack', 0)
            self.results_table.setItem(idx, 6, QTableWidgetItem(str(stack)))

            # Strategy
            strategy = lineup.get('strategy', '')
            self.results_table.setItem(idx, 7, QTableWidgetItem(strategy))

        # Auto-resize columns
        self.results_table.resizeColumnsToContents()

        # Show first lineup details by default
        if lineups:
            self.show_lineup_details(lineups[0])

        # Switch to results tab
        self.tabs.setCurrentIndex(1)

    def on_lineup_clicked(self, index):
        """Handle lineup row click to show details"""
        row = index.row()
        if 0 <= row < len(self.displayed_lineups):
            self.show_lineup_details(self.displayed_lineups[row])

    def show_lineup_details(self, lineup: Dict):
        """Show detailed lineup in details area"""
        details = "📋 LINEUP DETAILS\n"
        details += "=" * 60 + "\n\n"

        # Group players by position
        positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']

        for pos in positions:
            players_at_pos = [p for p in lineup['players'] if p.primary_position == pos]
            if players_at_pos:
                if pos == 'P':
                    details += "⚾ PITCHERS:\n"
                elif pos == 'OF':
                    details += "🏃 OUTFIELD:\n"
                else:
                    details += f"🥊 {pos}:\n"

                for player in players_at_pos:
                    details += f"  • {player.name:<20} ({player.team}) - ${player.salary:,}"
                    if hasattr(player, 'optimization_score'):
                        details += f" → {player.optimization_score:.1f} pts"
                    details += "\n"
                details += "\n"

        details += "=" * 60 + "\n"
        details += f"💰 Total Salary: ${lineup['salary']:,} / $50,000\n"
        details += f"📊 Projected Score: {lineup['projection']:.1f} points\n"
        details += f"⚡ Optimized Score: {lineup['optimization_score']:.1f} points\n"

        # Show stack information
        if lineup.get('max_stack', 0) > 1:
            details += f"🔥 Max Stack Size: {lineup['max_stack']} players\n"

        # Show in details area
        if hasattr(self, 'lineup_details'):
            self.lineup_details.setText(details)

        # Also show in status for backwards compatibility
        self.status_text.clear()
        self.status_text.append(details)

    def test_scoring(self):
        """Test scoring engine"""
        if not self.system.player_pool:
            self.debug_text.append("No player pool to test!")
            return

        self.debug_text.append("=== SCORING TEST ===\n")

        # Test a few players
        for player in self.system.player_pool[:5]:
            cash_score = self.system.scoring_engine.score_player(player, 'cash')
            gpp_score = self.system.scoring_engine.score_player(player, 'gpp')

            self.debug_text.append(f"{player.name}:")
            self.debug_text.append(f"  Base: {getattr(player, 'base_projection', 0):.1f}")
            self.debug_text.append(f"  Cash: {cash_score:.1f}")
            self.debug_text.append(f"  GPP: {gpp_score:.1f}\n")

    def test_enrichment(self):
        """Test enrichment for current strategy"""
        if not self.csv_loaded:
            self.debug_text.append("Load CSV first!")
            return

        strategy = self.strategy_combo.currentData()
        if strategy == "auto":
            strategy, _ = self.strategy_manager.auto_select_strategy(
                self.detected_games,
                self.contest_combo.currentText().lower()
            )

        self.debug_text.append(f"=== ENRICHMENT TEST for {strategy} ===\n")

        # Get requirements
        reqs = self.strategy_manager.get_strategy_requirements(strategy)

        self.debug_text.append("Requirements:")
        for key, value in reqs.items():
            self.debug_text.append(f"  {key}: {value}")

        self.debug_text.append("\nWould fetch:")
        if reqs.get('needs_vegas'): self.debug_text.append("  ✓ Vegas lines")
        if reqs.get('needs_statcast'): self.debug_text.append("  ✓ Statcast data")
        if reqs.get('needs_ownership'): self.debug_text.append("  ✓ Ownership projections")
        if reqs.get('needs_weather'): self.debug_text.append("  ✓ Weather data")

    def update_status(self, message: str):
        """Update status display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        self.status_bar.showMessage(message, 5000)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show GUI
    gui = SimplifiedDFSOptimizerGUI()
    gui.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()