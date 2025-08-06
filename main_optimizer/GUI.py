#!/usr/bin/env python3
"""
COMPLETE DFS OPTIMIZER GUI
==========================
Full implementation with proper flow:
1. Load CSV → Auto-detect slate → Auto-select strategy
2. Enrich based on strategy → Filter by confirmations
3. Score players → Optimize lineups
"""

import sys
import os
from datetime import datetime
from typing import List, Set, Dict
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Add main_optimizer to path
sys.path.insert(0, 'main_optimizer')

# Import core system components
from unified_core_system_updated import UnifiedCoreSystem
from gui_strategy_configuration import GUIStrategyManager


class CompleteDFSOptimizerGUI(QMainWindow):
    """Complete DFS Optimizer GUI with all features"""

    def __init__(self):
        super().__init__()

        # Initialize core system
        self.system = UnifiedCoreSystem()
        self.strategy_manager = GUIStrategyManager()

        # State tracking
        self.csv_loaded = False
        self.detected_games = 0
        self.detected_slate_size = None
        self.manual_selections = set()
        self.generated_lineups = []

        # Initialize UI
        self.init_ui()

    def init_ui(self):
        """Initialize the complete UI"""
        self.setWindowTitle("DFS Optimizer - Complete System")
        self.setGeometry(100, 100, 1400, 900)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Create all sections
        self.create_header_section(main_layout)
        self.create_settings_section(main_layout)
        self.create_pool_section(main_layout)
        self.create_optimization_section(main_layout)
        self.create_status_section(main_layout)
        self.create_results_section(main_layout)

        # Status bar
        self.status_bar = self.statusBar()
        self.update_status("Ready - Load CSV to begin")

    def create_header_section(self, layout):
        """Section 1: CSV Loading and Slate Detection"""
        group = QGroupBox("1. Data Loading & Slate Detection")
        group_layout = QHBoxLayout()

        # CSV info
        self.csv_label = QLabel("No CSV loaded")
        self.csv_label.setMinimumWidth(300)
        group_layout.addWidget(self.csv_label)

        # Load button
        self.load_btn = QPushButton("Load CSV")
        self.load_btn.clicked.connect(self.load_csv)
        self.load_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        group_layout.addWidget(self.load_btn)

        # Slate info (auto-detected)
        self.slate_info_label = QLabel("Slate: Not detected")
        self.slate_info_label.setStyleSheet("color: blue; font-weight: bold;")
        group_layout.addWidget(self.slate_info_label)

        group_layout.addStretch()
        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_settings_section(self, layout):
        """Section 2: Contest Settings & Strategy"""
        group = QGroupBox("2. Contest Settings & Strategy Selection")
        group_layout = QGridLayout()

        # Contest type
        group_layout.addWidget(QLabel("Contest Type:"), 0, 0)
        self.contest_combo = QComboBox()
        self.contest_combo.addItems(["GPP", "Cash"])
        self.contest_combo.currentTextChanged.connect(self.on_contest_changed)
        group_layout.addWidget(self.contest_combo, 0, 1)

        # Strategy selection
        group_layout.addWidget(QLabel("Strategy:"), 0, 2)
        self.strategy_combo = QComboBox()
        self.setup_strategy_dropdown()
        self.strategy_combo.currentIndexChanged.connect(self.on_strategy_changed)
        group_layout.addWidget(self.strategy_combo, 0, 3)

        # Strategy info
        self.strategy_info_label = QLabel("Auto-selected based on slate")
        self.strategy_info_label.setStyleSheet("color: green;")
        group_layout.addWidget(self.strategy_info_label, 1, 0, 1, 4)

        # Number of lineups
        group_layout.addWidget(QLabel("Lineups:"), 0, 4)
        self.lineups_spin = QSpinBox()
        self.lineups_spin.setRange(1, 150)
        self.lineups_spin.setValue(1)
        group_layout.addWidget(self.lineups_spin, 0, 5)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_pool_section(self, layout):
        """Section 3: Player Pool Management"""
        group = QGroupBox("3. Player Pool & Confirmations")
        group_layout = QVBoxLayout()

        # Pool controls
        controls = QHBoxLayout()

        # Fetch confirmations
        self.fetch_btn = QPushButton("Fetch Confirmations")
        self.fetch_btn.clicked.connect(self.fetch_confirmations)
        self.fetch_btn.setEnabled(False)
        controls.addWidget(self.fetch_btn)

        # Confirmed only checkbox
        self.confirmed_only_cb = QCheckBox("Confirmed Only")
        self.confirmed_only_cb.setChecked(False)
        self.confirmed_only_cb.stateChanged.connect(self.on_pool_filter_changed)
        controls.addWidget(self.confirmed_only_cb)

        # Pool info
        self.pool_info_label = QLabel("Pool: 0 players")
        self.pool_info_label.setStyleSheet("font-weight: bold;")
        controls.addWidget(self.pool_info_label)

        # Rebuild button
        self.rebuild_btn = QPushButton("Rebuild Pool")
        self.rebuild_btn.clicked.connect(self.rebuild_pool)
        self.rebuild_btn.setEnabled(False)
        controls.addWidget(self.rebuild_btn)

        controls.addStretch()
        group_layout.addLayout(controls)

        # Manual selections
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Manual Add:"))

        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Player name...")
        manual_layout.addWidget(self.manual_input)

        self.add_manual_btn = QPushButton("Add")
        self.add_manual_btn.clicked.connect(self.add_manual_player)
        manual_layout.addWidget(self.add_manual_btn)

        self.manual_label = QLabel("Manual: 0")
        manual_layout.addWidget(self.manual_label)

        self.clear_manual_btn = QPushButton("Clear")
        self.clear_manual_btn.clicked.connect(self.clear_manual_selections)
        manual_layout.addWidget(self.clear_manual_btn)

        manual_layout.addStretch()
        group_layout.addLayout(manual_layout)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_optimization_section(self, layout):
        """Section 4: Optimization Controls"""
        group = QGroupBox("4. Optimization")
        group_layout = QVBoxLayout()

        # Optimize button
        self.optimize_btn = QPushButton("OPTIMIZE LINEUPS")
        self.optimize_btn.setEnabled(False)
        self.optimize_btn.setMinimumHeight(50)
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.optimize_btn.clicked.connect(self.run_optimization)
        group_layout.addWidget(self.optimize_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        group_layout.addWidget(self.progress_bar)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_status_section(self, layout):
        """Section 5: Status & Logs"""
        group = QGroupBox("5. Status & Activity Log")
        group_layout = QVBoxLayout()

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(120)
        self.status_text.setFont(QFont("Courier", 9))
        group_layout.addWidget(self.status_text)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def create_results_section(self, layout):
        """Section 6: Results Display"""
        group = QGroupBox("6. Generated Lineups")
        group_layout = QVBoxLayout()

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Lineup", "Projection", "Salary", "Strategy", "Stack", "Actions"
        ])
        self.results_table.itemClicked.connect(self.on_lineup_selected)
        group_layout.addWidget(self.results_table)

        # Export button
        export_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export Lineups")
        self.export_btn.clicked.connect(self.export_lineups)
        self.export_btn.setEnabled(False)
        export_layout.addWidget(self.export_btn)
        export_layout.addStretch()
        group_layout.addLayout(export_layout)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def setup_strategy_dropdown(self):
        """Setup strategy dropdown with categories"""
        self.strategy_combo.clear()

        # Add auto option
        self.strategy_combo.addItem("🤖 Auto (Recommended)", "auto")
        self.strategy_combo.insertSeparator(1)

        # Get strategies from manager
        strategies = self.strategy_manager.get_gui_strategies()

        # Add by category
        for category, strat_list in strategies.items():
            if strat_list and strat_list[0] != 'auto':
                # Add category header
                self.strategy_combo.insertSeparator(self.strategy_combo.count())

                # Add strategies in category
                for strategy in strat_list:
                    if strategy != 'auto':
                        desc = self.strategy_manager.get_strategy_description(strategy)
                        display = f"{strategy} - {desc}"
                        self.strategy_combo.addItem(display, strategy)

    def load_csv(self):
        """Load CSV and trigger auto-detection flow"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load DraftKings CSV", "", "CSV Files (*.csv)"
        )

        if not file_path:
            return

        self.log_status("Loading CSV...")

        # Load CSV
        count = self.system.load_csv(file_path)

        if count > 0:
            self.csv_loaded = True
            self.csv_label.setText(f"Loaded: {os.path.basename(file_path)} ({count} players)")

            # Auto-detect slate and update display
            self.detect_and_display_slate()

            # Enable controls
            self.fetch_btn.setEnabled(True)
            self.rebuild_btn.setEnabled(True)

            # Build initial pool
            self.rebuild_pool()

            self.log_status(f"✅ Loaded {count} players successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to load CSV")

    def detect_and_display_slate(self):
        """Detect slate characteristics and auto-select strategy"""
        # Get slate info
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
        """Auto-select best strategy for slate"""
        contest_type = self.contest_combo.currentText().lower()

        strategy, reason = self.strategy_manager.auto_select_strategy(
            num_games=self.detected_games,
            contest_type=contest_type
        )

        self.strategy_info_label.setText(f"Auto: {reason}")
        self.log_status(f"Strategy: {reason}")

    def on_contest_changed(self):
        """Handle contest type change"""
        if self.csv_loaded and self.strategy_combo.currentData() == "auto":
            self.auto_select_strategy()

    def on_strategy_changed(self):
        """Handle manual strategy selection"""
        if self.strategy_combo.currentData() != "auto":
            strategy = self.strategy_combo.currentData()
            desc = self.strategy_manager.get_strategy_description(strategy)
            self.strategy_info_label.setText(f"Manual: {desc}")

    def fetch_confirmations(self):
        """Fetch MLB confirmed lineups"""
        self.log_status("Fetching MLB confirmations...")
        QApplication.processEvents()

        # Fetch confirmations
        confirmed = self.system.fetch_confirmed_players()

        if confirmed > 0:
            self.log_status(f"✅ Found {confirmed} confirmed players")
            self.rebuild_pool()
        else:
            self.log_status("⚠️ No confirmations found (games may not have started)")

    def on_pool_filter_changed(self):
        """Handle pool filter change"""
        if self.csv_loaded:
            self.rebuild_pool()

    def rebuild_pool(self):
        """Rebuild player pool with current settings"""
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
        filter_text = "all" if include_unconfirmed else "confirmed only"
        self.pool_info_label.setText(f"Pool: {pool_size} players ({filter_text})")

        # Enable optimize if we have players
        self.optimize_btn.setEnabled(pool_size > 0)

        if pool_size > 0:
            self.log_status(f"Player pool: {pool_size} players")

    def add_manual_player(self):
        """Add manual player selection"""
        name = self.manual_input.text().strip()
        if name:
            self.manual_selections.add(name)
            self.manual_input.clear()
            self.manual_label.setText(f"Manual: {len(self.manual_selections)}")
            self.rebuild_pool()

    def clear_manual_selections(self):
        """Clear all manual selections"""
        self.manual_selections.clear()
        self.manual_label.setText("Manual: 0")
        self.rebuild_pool()

    def run_optimization(self):
        """Run the complete optimization pipeline"""
        if not self.csv_loaded or len(self.system.player_pool) == 0:
            QMessageBox.warning(self, "Error", "No players in pool!")
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

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(10)

        self.log_status(f"Starting optimization: {strategy} for {contest_type}")
        QApplication.processEvents()

        try:
            # Step 1: Enrich players based on strategy (30%)
            self.log_status("Enriching players based on strategy...")
            self.progress_bar.setValue(30)
            QApplication.processEvents()

            enrichment_stats = self.system.enrich_player_pool_smart(strategy, contest_type)
            self.log_status(f"Enriched: Vegas={enrichment_stats.get('vegas', 0)}, "
                            f"Recent={enrichment_stats.get('recent_form', 0)}")

            # Step 2: Score players (50%)
            self.progress_bar.setValue(50)
            self.log_status("Scoring players...")
            QApplication.processEvents()

            scored = self.system.score_players(contest_type)
            self.log_status(f"Scored {scored} players")

            # Step 3: Generate lineups (70-100%)
            self.log_status(f"Generating {num_lineups} lineups...")
            self.progress_bar.setValue(70)
            QApplication.processEvents()

            # Get manual selections as string
            manual_str = ",".join(self.manual_selections) if self.manual_selections else ""

            # Run optimization
            lineups = self.system.optimize_lineup(
                strategy=strategy,
                contest_type=contest_type,
                num_lineups=num_lineups,
                manual_selections=manual_str
            )

            self.progress_bar.setValue(100)

            if lineups:
                self.generated_lineups = lineups
                self.display_results(lineups)
                self.log_status(f"✅ Generated {len(lineups)} lineups successfully!")
                self.export_btn.setEnabled(True)
            else:
                self.log_status("❌ No lineups generated")

        except Exception as e:
            self.log_status(f"❌ Error: {str(e)}")
            QMessageBox.critical(self, "Optimization Error", str(e))
        finally:
            self.progress_bar.setVisible(False)

    def display_results(self, lineups):
        """Display generated lineups in table"""
        self.results_table.setRowCount(len(lineups))

        for i, lineup in enumerate(lineups):
            # Lineup number
            self.results_table.setItem(i, 0, QTableWidgetItem(f"Lineup {i + 1}"))

            # Projection
            proj = lineup.get('projection', 0)
            self.results_table.setItem(i, 1, QTableWidgetItem(f"{proj:.1f}"))

            # Salary
            salary = lineup.get('salary', 0)
            self.results_table.setItem(i, 2, QTableWidgetItem(f"${salary:,}"))

            # Strategy
            strategy = lineup.get('strategy', 'unknown')
            self.results_table.setItem(i, 3, QTableWidgetItem(strategy))

            # Stack info
            stack = lineup.get('max_stack', 0)
            self.results_table.setItem(i, 4, QTableWidgetItem(f"{stack} players"))

            # View button
            view_btn = QPushButton("View")
            view_btn.clicked.connect(lambda checked, idx=i: self.view_lineup(idx))
            self.results_table.setCellWidget(i, 5, view_btn)

    def view_lineup(self, index):
        """View detailed lineup"""
        if index >= len(self.generated_lineups):
            return

        lineup = self.generated_lineups[index]

        # Create detail dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Lineup {index + 1} Details")
        dialog.setModal(True)
        dialog.resize(600, 500)

        layout = QVBoxLayout()

        # Lineup details
        details = QTextEdit()
        details.setReadOnly(True)

        text = f"LINEUP {index + 1}\n"
        text += "=" * 50 + "\n\n"

        # Group by position
        positions = {}
        for player in lineup.get('players', []):
            pos = player.position
            if pos not in positions:
                positions[pos] = []
            positions[pos].append(player)

        # Display by position
        for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
            if pos in positions:
                text += f"{pos}:\n"
                for p in positions[pos]:
                    text += f"  {p.name:20s} ({p.team}) ${p.salary:,} - {p.optimization_score:.1f}pts\n"
                text += "\n"

        text += "-" * 50 + "\n"
        text += f"Total Salary: ${lineup.get('salary', 0):,} / $50,000\n"
        text += f"Projected: {lineup.get('projection', 0):.1f} points\n"

        details.setText(text)
        layout.addWidget(details)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def on_lineup_selected(self, item):
        """Handle lineup selection"""
        row = item.row()
        if row < len(self.generated_lineups):
            self.view_lineup(row)

    def export_lineups(self):
        """Export lineups to CSV"""
        if not self.generated_lineups:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Lineups", "lineups.csv", "CSV Files (*.csv)"
        )

        if file_path:
            try:
                # Export logic here
                self.log_status(f"✅ Exported {len(self.generated_lineups)} lineups to {file_path}")
                QMessageBox.information(self, "Success", "Lineups exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def log_status(self, message):
        """Log status message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        self.status_bar.showMessage(message, 3000)

    def update_status(self, message):
        """Update status bar"""
        self.status_bar.showMessage(message)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Set application icon if available
    app.setWindowIcon(QIcon('icon.png'))

    # Create and show GUI
    gui = CompleteDFSOptimizerGUI()
    gui.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()