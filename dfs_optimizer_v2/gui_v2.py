#!/usr/bin/env python3
"""
DFS OPTIMIZER GUI V2
====================
Clean, simple interface using the new components
"""

import sys
import os
from datetime import datetime
from typing import List, Set
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Import our new clean components
from data_pipeline_v2 import DFSPipeline
from config_v2 import get_config


class DFSOptimizerGUI(QMainWindow):
    """Clean, simple DFS optimizer interface"""

    def __init__(self):
        super().__init__()

        # Initialize pipeline
        self.pipeline = DFSPipeline()
        self.config = get_config()

        # State
        self.csv_loaded = False
        self.manual_selections = set()
        self.generated_lineups = []

        # Setup UI
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""

        self.setWindowTitle("DFS Optimizer V2 - Clean & Simple")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Create sections
        layout.addWidget(self.create_load_section())
        layout.addWidget(self.create_settings_section())
        layout.addWidget(self.create_player_pool_section())
        layout.addWidget(self.create_optimize_section())
        layout.addWidget(self.create_results_section())

        # Status bar
        self.status_bar = self.statusBar()
        self.update_status("Ready - Load CSV to begin")

    def create_load_section(self) -> QGroupBox:
        """Section 1: Load CSV"""

        group = QGroupBox("1. Load Data")
        layout = QHBoxLayout()

        # CSV info
        self.csv_label = QLabel("No CSV loaded")
        self.csv_label.setMinimumWidth(300)
        layout.addWidget(self.csv_label)

        # Load button
        self.load_btn = QPushButton("Load CSV")
        self.load_btn.clicked.connect(self.load_csv)
        self.load_btn.setStyleSheet("font-weight: bold; padding: 5px 15px;")
        layout.addWidget(self.load_btn)

        # Slate info
        self.slate_label = QLabel("")
        self.slate_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(self.slate_label)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def fetch_confirmations(self):
        """Fetch MLB confirmations"""

        self.log("Fetching MLB confirmations...")
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("Fetching...")
        QApplication.processEvents()

        try:
            confirmed = self.pipeline.fetch_confirmations()

            if confirmed > 0:
                self.log(f"✅ Found {confirmed} confirmed players")
                # Update the confirmed label
                self.confirmed_label.setText(f"({confirmed} confirmed)")
                self.confirmed_label.setStyleSheet("color: green; margin-left: 5px; font-weight: bold;")

                # Update pool if "confirmed only" is checked
                if self.confirmed_cb.isChecked():
                    self.update_pool_label()
            else:
                self.log("⚠️ No confirmations found (games may not have started)")
                self.confirmed_label.setText("(0 confirmed)")

        except Exception as e:
            self.log(f"❌ Error fetching confirmations: {str(e)}")

        finally:
            self.fetch_btn.setEnabled(True)
            self.fetch_btn.setText("Fetch Confirmations")

    def on_confirmed_changed(self):
        """Handle confirmed-only checkbox change"""

        if self.csv_loaded:
            self.update_pool_label()

            if self.confirmed_cb.isChecked():
                self.log("Showing confirmed players only")
            else:
                self.log("Showing all players")

    def create_settings_section(self) -> QGroupBox:
        """Section 2: Contest Settings"""

        group = QGroupBox("2. Contest Settings")
        layout = QGridLayout()

        # Contest type
        layout.addWidget(QLabel("Contest:"), 0, 0)
        self.contest_combo = QComboBox()
        self.contest_combo.addItems(["GPP (Tournament)", "Cash (50/50)"])
        self.contest_combo.currentTextChanged.connect(self.on_contest_changed)
        layout.addWidget(self.contest_combo, 0, 1)

        # Number of lineups
        layout.addWidget(QLabel("Lineups:"), 0, 2)
        self.lineups_spin = QSpinBox()
        self.lineups_spin.setRange(1, 150)
        self.lineups_spin.setValue(20)
        layout.addWidget(self.lineups_spin, 0, 3)

        # Strategy info
        self.strategy_label = QLabel("Strategy will be auto-selected based on slate")
        self.strategy_label.setStyleSheet("color: green; margin-top: 5px;")
        layout.addWidget(self.strategy_label, 1, 0, 1, 4)

        layout.setColumnStretch(4, 1)
        group.setLayout(layout)
        return group

    def create_player_pool_section(self) -> QGroupBox:
        """Section 3: Player Pool"""

        group = QGroupBox("3. Player Pool")
        layout = QVBoxLayout()

        # Pool controls
        controls = QHBoxLayout()

        # Fetch confirmations button (NEW!)
        self.fetch_btn = QPushButton("Fetch Confirmations")
        self.fetch_btn.clicked.connect(self.fetch_confirmations)
        self.fetch_btn.setEnabled(False)  # Will enable after CSV load
        self.fetch_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:enabled {
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover:enabled {
                background-color: #1976D2;
            }
        """)
        controls.addWidget(self.fetch_btn)

        # Separator
        separator = QLabel("|")
        separator.setStyleSheet("color: #ccc; margin: 0 10px;")
        controls.addWidget(separator)

        # Confirmed only checkbox
        self.confirmed_cb = QCheckBox("Confirmed Players Only")
        self.confirmed_cb.setChecked(False)
        self.confirmed_cb.stateChanged.connect(self.on_confirmed_changed)  # NEW handler
        controls.addWidget(self.confirmed_cb)

        # Pool info
        self.pool_label = QLabel("Pool: 0 players")
        self.pool_label.setStyleSheet("font-weight: bold; margin-left: 20px;")
        controls.addWidget(self.pool_label)

        # Confirmed count (NEW!)
        self.confirmed_label = QLabel("(0 confirmed)")
        self.confirmed_label.setStyleSheet("color: green; margin-left: 5px;")
        controls.addWidget(self.confirmed_label)

        controls.addStretch()
        layout.addLayout(controls)

        # Manual selections
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Manual:"))

        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Player name (optional)")
        self.manual_input.returnPressed.connect(self.add_manual)
        manual_layout.addWidget(self.manual_input)

        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self.add_manual)
        manual_layout.addWidget(self.add_btn)

        self.manual_label = QLabel("0 selected")
        manual_layout.addWidget(self.manual_label)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_manual)
        manual_layout.addWidget(self.clear_btn)

        manual_layout.addStretch()
        layout.addLayout(manual_layout)

        group.setLayout(layout)
        return group


    def create_optimize_section(self) -> QGroupBox:
        """Section 4: Optimization"""

        group = QGroupBox("4. Optimize")
        layout = QVBoxLayout()

        # Optimize button
        btn_layout = QHBoxLayout()

        self.optimize_btn = QPushButton("OPTIMIZE LINEUPS")
        self.optimize_btn.setEnabled(False)
        self.optimize_btn.clicked.connect(self.run_optimization)
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 14px;
                padding: 10px 30px;
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        btn_layout.addStretch()
        btn_layout.addWidget(self.optimize_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Status
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        self.status_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.status_text)

        group.setLayout(layout)
        return group

    def create_results_section(self) -> QGroupBox:
        """Section 5: Results"""

        group = QGroupBox("5. Results")
        layout = QVBoxLayout()

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Lineup", "Score", "Salary", "Stack", "Strategy", "Action"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.results_table)

        # Export button
        export_layout = QHBoxLayout()

        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_lineups)
        export_layout.addWidget(self.export_btn)

        export_layout.addStretch()
        layout.addLayout(export_layout)

        group.setLayout(layout)
        return group

    # =========================================
    # EVENT HANDLERS
    # =========================================

    def load_csv(self):
        """Load CSV file"""

        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load DraftKings CSV", "", "CSV Files (*.csv)"
        )

        if not filepath:
            return

        self.log("Loading CSV...")
        QApplication.processEvents()

        # Load CSV
        count = self.pipeline.load_csv(filepath)

        if count > 0:
            self.csv_loaded = True
            filename = os.path.basename(filepath)
            self.csv_label.setText(f"{filename} ({count} players)")

            # Show slate info
            games = self.pipeline.num_games
            slate = self.pipeline.slate_size
            self.slate_label.setText(f"{games} games ({slate} slate)")

            # Update strategy label
            self.update_strategy_label()

            # Update pool
            self.update_pool_label()

            # Enable buttons (UPDATED!)
            self.optimize_btn.setEnabled(True)
            self.fetch_btn.setEnabled(True)  # NEW - Enable fetch button!

            self.log(f"✅ Loaded {count} players from {games} games")
        else:
            QMessageBox.warning(self, "Error", "Failed to load CSV")

    def on_contest_changed(self):
        """Handle contest type change"""

        if self.csv_loaded:
            self.update_strategy_label()

            # Update default lineups
            if "Cash" in self.contest_combo.currentText():
                self.lineups_spin.setValue(3)
            else:
                self.lineups_spin.setValue(20)

    def update_strategy_label(self):
        """Update strategy label based on slate"""

        if not self.csv_loaded:
            return

        contest = "cash" if "Cash" in self.contest_combo.currentText() else "gpp"
        strategy, reason = self.pipeline.strategy_manager.auto_select_strategy(
            self.pipeline.num_games, contest
        )

        self.strategy_label.setText(f"Strategy: {reason}")

    def add_manual(self):
        """Add manual player selection"""

        name = self.manual_input.text().strip()
        if name:
            self.manual_selections.add(name)
            self.manual_input.clear()
            self.manual_label.setText(f"{len(self.manual_selections)} selected")
            self.update_pool_label()
            self.log(f"Added manual: {name}")

    def clear_manual(self):
        """Clear manual selections"""

        self.manual_selections.clear()
        self.manual_label.setText("0 selected")
        self.update_pool_label()
        self.log("Cleared manual selections")

    def update_pool_label(self):
        """Update player pool label"""

        if not self.csv_loaded:
            return

        # Build pool
        confirmed = self.confirmed_cb.isChecked()
        manual = list(self.manual_selections)

        count = self.pipeline.build_player_pool(confirmed, manual)

        # Update main pool label
        if confirmed:
            self.pool_label.setText(f"Pool: {count} confirmed players")
        else:
            self.pool_label.setText(f"Pool: {count} players")

        # Count how many in pool are confirmed
        confirmed_in_pool = 0
        for player in self.pipeline.player_pool:
            if getattr(player, 'confirmed', False):
                confirmed_in_pool += 1

        # Update confirmed count if not showing confirmed-only
        if not confirmed:
            self.confirmed_label.setText(f"({confirmed_in_pool} confirmed)")
            

    def run_optimization(self):
        """Run the optimization"""

        if not self.csv_loaded:
            return

        # Get settings
        contest = "cash" if "Cash" in self.contest_combo.currentText() else "gpp"
        num_lineups = self.lineups_spin.value()
        confirmed = self.confirmed_cb.isChecked()
        manual = list(self.manual_selections)

        # Show progress
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)

        self.log("=" * 50)
        self.log(f"Starting {contest.upper()} optimization for {num_lineups} lineups")

        try:
            # Progress: Load
            self.progress.setValue(20)
            QApplication.processEvents()

            # Build pool
            self.pipeline.build_player_pool(confirmed, manual)
            self.log(f"Player pool: {len(self.pipeline.player_pool)} players")

            # Progress: Strategy
            self.progress.setValue(40)
            QApplication.processEvents()

            # Apply strategy
            strategy = self.pipeline.apply_strategy(contest_type=contest)
            self.log(f"Applied strategy: {strategy}")

            # Progress: Enrich
            self.progress.setValue(60)
            QApplication.processEvents()

            # Enrich and score
            self.pipeline.enrich_players(strategy, contest)
            self.pipeline.score_players(contest)
            self.log("Players enriched and scored")

            # Progress: Optimize
            self.progress.setValue(80)
            QApplication.processEvents()

            # Generate lineups
            lineups = self.pipeline.optimize_lineups(contest, num_lineups)

            # Progress: Complete
            self.progress.setValue(100)

            if lineups:
                self.generated_lineups = lineups
                self.display_results(lineups)
                self.log(f"✅ Generated {len(lineups)} lineups!")
                self.export_btn.setEnabled(True)
            else:
                self.log("❌ Failed to generate lineups")

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            QMessageBox.critical(self, "Error", str(e))

        finally:
            self.progress.setVisible(False)

    def display_results(self, lineups: List):
        """Display lineup results"""

        self.results_table.setRowCount(len(lineups))

        for i, lineup in enumerate(lineups):
            # Lineup number
            self.results_table.setItem(i, 0, QTableWidgetItem(f"#{i + 1}"))

            # Score
            score = lineup.get('projection', 0)
            self.results_table.setItem(i, 1, QTableWidgetItem(f"{score:.1f}"))

            # Salary
            salary = lineup.get('salary', 0)
            self.results_table.setItem(i, 2, QTableWidgetItem(f"${salary:,}"))

            # Stack
            stack = lineup.get('max_stack', 0)
            self.results_table.setItem(i, 3, QTableWidgetItem(f"{stack}"))

            # Strategy (from metadata)
            strategy = lineup.get('strategy', 'auto')
            self.results_table.setItem(i, 4, QTableWidgetItem(strategy))

            # View button
            view_btn = QPushButton("View")
            view_btn.clicked.connect(lambda checked, idx=i: self.view_lineup(idx))
            self.results_table.setCellWidget(i, 5, view_btn)

    def view_lineup(self, index: int):
        """View detailed lineup"""

        if index >= len(self.generated_lineups):
            return

        lineup = self.generated_lineups[index]

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Lineup #{index + 1}")
        dialog.setModal(True)
        dialog.resize(500, 400)

        layout = QVBoxLayout()

        # Lineup details
        text = QTextEdit()
        text.setReadOnly(True)

        content = f"LINEUP #{index + 1}\n"
        content += "=" * 40 + "\n\n"

        # Players by position
        for player in lineup['players']:
            content += f"{player.position:3} {player.name:20} ({player.team}) ${player.salary:,}\n"

        content += "\n" + "-" * 40 + "\n"
        content += f"Total Salary: ${lineup['salary']:,}\n"
        content += f"Projection: {lineup['projection']:.1f} points\n"
        content += f"Max Stack: {lineup['max_stack']} players\n"

        # Show stacks
        if lineup.get('stack_info'):
            content += "\nStacks:\n"
            for team, count in lineup['stack_info'].items():
                if count > 1:
                    content += f"  {team}: {count} players\n"

        text.setText(content)
        layout.addWidget(text)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def export_lineups(self):
        """Export lineups to CSV"""

        if not self.generated_lineups:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Lineups", "lineups.csv", "CSV Files (*.csv)"
        )

        if filepath:
            if self.pipeline.export_lineups(filepath):
                self.log(f"✅ Exported to {filepath}")
                QMessageBox.information(self, "Success", "Lineups exported!")
            else:
                QMessageBox.warning(self, "Error", "Export failed")

    def log(self, message: str):
        """Add message to log"""

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")

        # Limit log size
        doc = self.status_text.document()
        if doc.blockCount() > 100:
            cursor = self.status_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()

    def update_status(self, message: str):
        """Update status bar"""

        self.status_bar.showMessage(message, 3000)


def main():
    """Main entry point"""

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Create and show GUI
    window = DFSOptimizerGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()