#!/usr/bin/env python3
"""
COMPLETE DFS GUI - STREAMLINED VERSION
=====================================
Simplified interface with correlation-aware scoring
"""

import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import json

# Import core system
from unified_core_system import UnifiedCoreSystem


class OptimizationWorker(QThread):
    """Background worker for optimization"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    log = pyqtSignal(str, str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):
        """Run optimization process"""
        try:
            # Initialize system
            self.progress.emit(10, "Initializing optimizer...")
            system = UnifiedCoreSystem()

            # Load CSV
            self.progress.emit(20, "Loading player data...")
            system.load_players_from_csv(self.settings['csv_path'])
            self.log.emit(f"Loaded {len(system.players)} players", "info")

            # Fetch confirmations
            self.progress.emit(40, "Fetching starting lineups...")
            confirmed = system.fetch_confirmed_players()
            if confirmed:
                self.log.emit(f"Found {len(confirmed)} confirmed starters", "success")
            else:
                self.log.emit("No confirmations available yet", "warning")

            # Build player pool
            self.progress.emit(60, "Building player pool...")
            system.build_player_pool(include_unconfirmed=True)
            self.log.emit(f"Player pool: {len(system.player_pool)} players", "info")

            # Enrich data
            self.progress.emit(80, "Calculating correlations...")
            system.enrich_player_pool()

            # Optimize lineups
            self.progress.emit(90, "Generating optimal lineups...")
            if True:  # Force showdown mode
                lineups = system.optimize_showdown_lineups(
                    num_lineups=self.settings['num_lineups'],
                    strategy=self.settings['contest_type']
                )
            else:
                lineups = system.optimize_lineups(...)

            # System auto-detects showdown and applies correlation scoring
            lineups = system.optimize_lineups(
                num_lineups=self.settings['num_lineups'],
                contest_type=self.settings['contest_type'],
                min_unique_players=self.settings.get('min_unique', 3)
            )

            self.progress.emit(100, "Optimization complete!")
            self.finished.emit(lineups)

        except Exception as e:
            self.error.emit(str(e))
            import traceback
            self.log.emit(traceback.format_exc(), "error")


class CompleteDFSGUI(QMainWindow):
    """Main DFS Optimizer GUI"""

    def __init__(self):
        super().__init__()
        self.csv_path = None
        self.lineups = []
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("DFS Optimizer - Correlation Edition")
        self.setGeometry(100, 100, 1400, 900)

        # Apply stylesheet
        self.setStyleSheet(self.get_stylesheet())

        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Top toolbar
        self.create_toolbar()

        # Main content area
        content_layout = QHBoxLayout()
        layout.addLayout(content_layout)

        # Left panel - Controls
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 1)

        # Right panel - Results
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 2)

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready to optimize")

    def get_stylesheet(self):
        """Modern dark theme stylesheet"""
        return """
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            }
            QGroupBox {
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #4CAF50;
            }
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #4d4d4d;
            }
            QPushButton#primary {
                background-color: #4CAF50;
                border: none;
                color: white;
                font-weight: bold;
            }
            QPushButton#primary:hover {
                background-color: #5CBF60;
            }
            QPushButton#primary:disabled {
                background-color: #2d2d2d;
                color: #666;
            }
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #252525;
                gridline-color: #3d3d3d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #3d3d3d;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QProgressBar {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            QTextEdit {
                background-color: #252525;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            }
            QSpinBox, QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                padding: 6px;
                border-radius: 4px;
                min-height: 30px;
            }
            QRadioButton {
                spacing: 8px;
                padding: 4px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QLabel {
                color: #cccccc;
            }
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3d3d3d;
                border-bottom: 2px solid #4CAF50;
            }
        """

    def create_toolbar(self):
        """Create top toolbar"""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)

        # File menu
        file_menu = QMenu("File", self)
        file_menu.addAction("Load CSV", self.load_csv)
        file_menu.addAction("Export Lineups", self.export_lineups)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        # Add to toolbar
        file_button = QToolButton()
        file_button.setText("📁 File")
        file_button.setMenu(file_menu)
        file_button.setPopupMode(QToolButton.InstantPopup)
        toolbar.addWidget(file_button)

        toolbar.addSeparator()

        # Quick actions
        toolbar.addAction("🔄 Refresh Data", self.refresh_data)
        toolbar.addAction("📊 View Stats", self.view_stats)

    def create_left_panel(self):
        """Create left control panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # CSV Selection
        csv_group = QGroupBox("📁 Data Source")
        csv_layout = QVBoxLayout()

        self.csv_label = QLabel("No file loaded")
        self.csv_label.setStyleSheet("padding: 10px; background-color: #2d2d2d; border-radius: 4px;")
        csv_layout.addWidget(self.csv_label)

        load_btn = QPushButton("Select DraftKings CSV")
        load_btn.clicked.connect(self.load_csv)
        csv_layout.addWidget(load_btn)

        csv_group.setLayout(csv_layout)
        layout.addWidget(csv_group)

        # Contest Settings
        contest_group = QGroupBox("🎯 Contest Settings")
        contest_layout = QVBoxLayout()

        # Contest type selection
        type_layout = QHBoxLayout()
        self.gpp_radio = QRadioButton("GPP (Tournaments)")
        self.cash_radio = QRadioButton("Cash (50/50s)")
        self.gpp_radio.setChecked(True)
        type_layout.addWidget(self.gpp_radio)
        type_layout.addWidget(self.cash_radio)
        contest_layout.addLayout(type_layout)

        # Contest info
        self.contest_info = QLabel()
        self.update_contest_info()
        self.gpp_radio.toggled.connect(self.update_contest_info)
        contest_layout.addWidget(self.contest_info)

        contest_group.setLayout(contest_layout)
        layout.addWidget(contest_group)

        # Optimization Settings
        opt_group = QGroupBox("⚙️ Optimization Settings")
        opt_layout = QFormLayout()

        # Number of lineups
        self.lineups_spin = QSpinBox()
        self.lineups_spin.setRange(1, 150)
        self.lineups_spin.setValue(1)  # ← Changed from 20 to 1
        opt_layout.addRow("Lineups:", self.lineups_spin)

        # Min unique
        self.unique_spin = QSpinBox()
        self.unique_spin.setRange(0, 5)
        self.unique_spin.setValue(1)  # ← Changed from 3 to 1
        self.unique_spin.setToolTip("Minimum unique players between lineups")
        opt_layout.addRow("Min Unique:", self.unique_spin)

        opt_group.setLayout(opt_layout)
        layout.addWidget(opt_group)

        # Optimize button
        self.optimize_btn = QPushButton("🚀 OPTIMIZE LINEUPS")
        self.optimize_btn.setObjectName("primary")
        self.optimize_btn.clicked.connect(self.run_optimization)
        self.optimize_btn.setEnabled(False)
        layout.addWidget(self.optimize_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Console
        console_group = QGroupBox("📝 Console Output")
        console_layout = QVBoxLayout()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(150)
        console_layout.addWidget(self.console)
        console_group.setLayout(console_layout)
        layout.addWidget(console_group)

        layout.addStretch()
        return widget

    def create_right_panel(self):
        """Create right results panel"""
        self.tabs = QTabWidget()

        # Lineups tab
        self.lineups_table = QTableWidget()
        self.tabs.addTab(self.lineups_table, "📋 Lineups")

        # Analysis tab
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.tabs.addTab(self.analysis_text, "📊 Analysis")

        # Players tab
        self.players_table = QTableWidget()
        self.tabs.addTab(self.players_table, "👥 Player Pool")

        return self.tabs

    def update_contest_info(self):
        """Update contest information display"""
        if self.gpp_radio.isChecked():
            info = """<b>GPP Settings:</b><br>
• Team boost: 1.15x for 5+ runs<br>
• Order boost: 1.10x for top 4<br>
• Aggressive stacking (3-5 players)<br>
• High variance plays"""
            self.contest_info.setStyleSheet("color: #ff9800;")
        else:
            info = """<b>Cash Settings:</b><br>
• Team boost: 1.08x for 5+ runs<br>
• Order boost: 1.05x for top 4<br>
• Conservative (max 3 per team)<br>
• Consistency focused"""
            self.contest_info.setStyleSheet("color: #4CAF50;")

        self.contest_info.setText(info)

    def load_csv(self):
        """Load CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select DraftKings CSV",
            "",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            # Read CSV
            df = pd.read_csv(file_path)
            self.csv_path = file_path
            self.csv_label.setText(os.path.basename(file_path))

            # Enable optimization
            self.optimize_btn.setEnabled(True)

            # Show basic info
            self.log(f"Loaded {len(df)} players from {os.path.basename(file_path)}", "success")

            # Detect slate type
            self.analyze_slate(df)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")

    def analyze_slate(self, df):
        """Analyze and display slate information"""
        # Basic stats
        num_players = len(df)

        # Detect showdown
        positions = df['Position'].unique() if 'Position' in df.columns else []
        is_showdown = 'CPT' in positions or 'UTIL' in positions

        if is_showdown:
            self.log("⚡ Showdown slate detected!", "info")

        # Update player pool tab
        self.update_player_pool(df)

    def update_player_pool(self, df):
        """Update player pool display"""
        self.players_table.setRowCount(len(df))
        self.players_table.setColumnCount(6)
        self.players_table.setHorizontalHeaderLabels([
            'Name', 'Position', 'Team', 'Salary', 'Opponent', 'Game'
        ])

        for i, row in df.iterrows():
            self.players_table.setItem(i, 0, QTableWidgetItem(row.get('Name', '')))
            self.players_table.setItem(i, 1, QTableWidgetItem(row.get('Position', '')))
            self.players_table.setItem(i, 2, QTableWidgetItem(row.get('TeamAbbrev', '')))
            self.players_table.setItem(i, 3, QTableWidgetItem(f"${row.get('Salary', 0):,}"))
            self.players_table.setItem(i, 4, QTableWidgetItem(row.get('Opponent', '')))
            self.players_table.setItem(i, 5, QTableWidgetItem(row.get('Game Info', '')))

        self.players_table.resizeColumnsToContents()

    def log(self, message, level="info"):
        """Add message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        colors = {
            "info": "#ffffff",
            "success": "#4CAF50",
            "warning": "#ff9800",
            "error": "#f44336"
        }

        html = f'<span style="color: #666">[{timestamp}]</span> '
        html += f'<span style="color: {colors.get(level, "#ffffff")}">{message}</span>'

        self.console.append(html)

    def run_optimization(self):
        """Run the optimization process"""
        if not self.csv_path:
            return

        # Disable controls
        self.optimize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)

        # Get settings
        settings = {
            'csv_path': self.csv_path,
            'num_lineups': self.lineups_spin.value(),
            'contest_type': 'gpp' if self.gpp_radio.isChecked() else 'cash',
            'min_unique': self.unique_spin.value()
        }

        # Clear console
        self.console.clear()
        self.log(f"Starting {settings['contest_type'].upper()} optimization...", "info")

        # Create and start worker
        self.worker = OptimizationWorker(settings)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_optimization_complete)
        self.worker.error.connect(self.on_optimization_error)
        self.worker.log.connect(self.log)
        self.worker.start()

    def update_progress(self, value, message):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(message)

    def on_optimization_complete(self, lineups):
        """Handle successful optimization"""
        self.lineups = lineups

        # Re-enable controls
        self.optimize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        # Display results
        self.display_lineups(lineups)
        self.display_analysis(lineups)

        # Success message
        self.log(f"✅ Generated {len(lineups)} optimal lineups!", "success")
        self.status_bar.showMessage("Optimization complete!")

        # Switch to lineups tab
        self.tabs.setCurrentIndex(0)

    def on_optimization_error(self, error_msg):
        """Handle optimization error"""
        self.optimize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.log(f"❌ Error: {error_msg}", "error")
        QMessageBox.critical(self, "Optimization Error", error_msg)

    def display_lineups(self, lineups):
        """Display lineups in table"""
        if not lineups:
            return

        # Setup table
        self.lineups_table.clear()
        self.lineups_table.setRowCount(len(lineups))

        # Determine columns based on lineup type
        first_lineup = lineups[0]
        if first_lineup.get('type') == 'showdown':
            columns = ['#', 'Captain', 'UTIL1', 'UTIL2', 'UTIL3', 'UTIL4', 'UTIL5', 'Salary', 'Proj']
        else:
            columns = ['#', 'P1', 'P2', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3', 'Salary', 'Proj']

        self.lineups_table.setColumnCount(len(columns))
        self.lineups_table.setHorizontalHeaderLabels(columns)

        # Populate table
        for i, lineup in enumerate(lineups):
            # Lineup number
            self.lineups_table.setItem(i, 0, QTableWidgetItem(f"{i + 1}"))

            if lineup.get('type') == 'showdown':
                # Showdown format
                self.lineups_table.setItem(i, 1, QTableWidgetItem(f"{lineup['captain'].name} (C)"))
                for j, util in enumerate(lineup['utilities']):
                    self.lineups_table.setItem(i, j + 2, QTableWidgetItem(util.name))
            else:
                # Classic format - properly map players to positions
                position_map = {}
                for player in lineup['players']:
                    pos = player.primary_position
                    if pos not in position_map:
                        position_map[pos] = []
                    position_map[pos].append(player)

                # Fill positions in order
                col = 1
                positions = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
                for pos in positions:
                    if pos in position_map and position_map[pos]:
                        player = position_map[pos].pop(0)
                        self.lineups_table.setItem(i, col, QTableWidgetItem(player.name))
                    col += 1

            # Salary and projection
            self.lineups_table.setItem(i, len(columns) - 2,
                                       QTableWidgetItem(f"${lineup['total_salary']:,}"))
            self.lineups_table.setItem(i, len(columns) - 1,
                                       QTableWidgetItem(f"{lineup['total_score']:.1f}"))

        # Resize columns
        self.lineups_table.resizeColumnsToContents()

    def display_analysis(self, lineups):
        """Display lineup analysis"""
        if not lineups:
            return

        # Calculate statistics
        total_lineups = len(lineups)
        avg_score = sum(l['total_score'] for l in lineups) / total_lineups
        avg_salary = sum(l['total_salary'] for l in lineups) / total_lineups

        # Find stacks
        stacks = {}
        for lineup in lineups:
            teams = {}
            for player in lineup['players']:
                team = player.team
                teams[team] = teams.get(team, 0) + 1

            for team, count in teams.items():
                if count >= 3:
                    stacks[team] = stacks.get(team, 0) + 1

        # Create analysis HTML
        html = f"""
        <h2>Lineup Analysis</h2>
        <p><b>Total Lineups:</b> {total_lineups}</p>
        <p><b>Average Projection:</b> {avg_score:.1f} points</p>
        <p><b>Average Salary:</b> ${avg_salary:,.0f}</p>
        <p><b>Salary Efficiency:</b> {avg_score / (avg_salary / 1000):.2f} pts/$1k</p>
        """

        if stacks:
            html += "<h3>Stack Usage</h3><ul>"
            for team, count in sorted(stacks.items(), key=lambda x: x[1], reverse=True):
                percentage = count / total_lineups * 100
                html += f"<li><b>{team}:</b> {count} lineups ({percentage:.0f}%)</li>"
            html += "</ul>"

        self.analysis_text.setHtml(html)

    def export_lineups(self):
        """Export lineups to CSV"""
        if not self.lineups:
            QMessageBox.warning(self, "No Lineups", "No lineups to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Lineups",
            f"lineups_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            # Create DataFrame for export
            rows = []
            for i, lineup in enumerate(self.lineups):
                row = {'Lineup': i + 1}

                if lineup.get('type') == 'showdown':
                    row['Captain'] = lineup['captain'].name
                    for j, util in enumerate(lineup['utilities']):
                        row[f'UTIL{j + 1}'] = util.name
                else:
                    # Map players by position
                    for player in lineup['players']:
                        pos = player.primary_position
                        if pos not in row:
                            row[pos] = player.name
                        else:
                            # Handle multiple players at same position
                            count = 2
                            while f"{pos}{count}" in row:
                                count += 1
                            row[f"{pos}{count}"] = player.name

                row['Salary'] = lineup['total_salary']
                row['Projection'] = lineup['total_score']
                rows.append(row)

            # Save to CSV
            df = pd.DataFrame(rows)
            df.to_csv(file_path, index=False)

            self.log(f"Exported {len(self.lineups)} lineups to {os.path.basename(file_path)}", "success")
            QMessageBox.information(self, "Export Complete", f"Lineups exported successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")

    def refresh_data(self):
        """Refresh data sources"""
        self.log("Refreshing data sources...", "info")
        # This would refresh confirmations, vegas lines, etc.

    def view_stats(self):
        """View optimization statistics"""
        if not self.lineups:
            QMessageBox.information(self, "No Data", "Generate lineups first to view statistics")
            return

        # Switch to analysis tab
        self.tabs.setCurrentIndex(1)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("DFS Optimizer - Correlation Edition")

    # Set application style
    app.setStyle('Fusion')

    # Create and show window
    window = CompleteDFSGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()