#!/usr/bin/env python3
"""
STREAMLINED DFS OPTIMIZER GUI
============================
Simplified interface focusing on what matters: Contest Type (GPP/Cash)
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
            system.build_player_pool()
            self.log.emit(f"Player pool: {len(system.player_pool)} players", "info")

            # Enrich data
            self.progress.emit(80, "Calculating correlations...")
            system.enrich_player_pool()

            # Optimize lineups
            self.progress.emit(90, "Generating optimal lineups...")

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


class StreamlinedDFSGUI(QMainWindow):
    """Simplified DFS Optimizer focused on essentials"""

    def __init__(self):
        super().__init__()
        self.csv_path = None
        self.lineups = []
        self.init_ui()

    def init_ui(self):
        """Initialize the streamlined interface"""
        self.setWindowTitle("DFS Optimizer - Correlation Edition")
        self.setGeometry(100, 100, 1200, 800)

        # Apply clean theme
        self.setStyleSheet(self.get_stylesheet())

        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Top section - File and Contest Type
        top_section = self.create_top_section()
        layout.addWidget(top_section)

        # Main content - Split view
        splitter = QSplitter(Qt.Horizontal)

        # Left: Controls
        controls = self.create_controls()
        splitter.addWidget(controls)

        # Right: Results
        results = self.create_results_panel()
        splitter.addWidget(results)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready to optimize")

    def get_stylesheet(self):
        """Clean, modern stylesheet"""
        return """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                selection-background-color: #4CAF50;
                gridline-color: #ddd;
            }
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """

    def create_top_section(self):
        """Create top section with file selection and contest type"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 10)

        # File selection
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet(
            "padding: 8px; background-color: white; border: 1px solid #ddd; border-radius: 4px;")

        self.browse_btn = QPushButton("📁 Select CSV")
        self.browse_btn.clicked.connect(self.load_csv)

        # Contest type toggle
        self.contest_group = QButtonGroup()
        self.gpp_radio = QRadioButton("🎯 GPP (Tournaments)")
        self.cash_radio = QRadioButton("💰 Cash (50/50s)")
        self.gpp_radio.setChecked(True)

        self.contest_group.addButton(self.gpp_radio)
        self.contest_group.addButton(self.cash_radio)

        # Info label
        self.mode_info = QLabel()
        self.update_mode_info()
        self.gpp_radio.toggled.connect(self.update_mode_info)

        # Layout
        layout.addWidget(QLabel("CSV File:"))
        layout.addWidget(self.file_label, 2)
        layout.addWidget(self.browse_btn)
        layout.addSpacing(20)
        layout.addWidget(self.gpp_radio)
        layout.addWidget(self.cash_radio)
        layout.addSpacing(20)
        layout.addWidget(self.mode_info, 1)

        return widget

    def create_controls(self):
        """Create simplified control panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Slate Info
        self.slate_info = QGroupBox("📊 Slate Information")
        slate_layout = QVBoxLayout()
        self.slate_details = QLabel("Load a CSV file to begin")
        self.slate_details.setWordWrap(True)
        self.slate_details.setStyleSheet("padding: 10px; background-color: white;")
        slate_layout.addWidget(self.slate_details)
        self.slate_info.setLayout(slate_layout)
        layout.addWidget(self.slate_info)

        # Optimization Settings
        settings_group = QGroupBox("⚙️ Settings")
        settings_layout = QFormLayout()

        # Number of lineups
        self.lineups_spin = QSpinBox()
        self.lineups_spin.setRange(1, 150)
        self.lineups_spin.setValue(20)
        self.lineups_spin.setSingleStep(5)
        settings_layout.addRow("Lineups:", self.lineups_spin)

        # Min unique players
        self.unique_spin = QSpinBox()
        self.unique_spin.setRange(0, 5)
        self.unique_spin.setValue(3)
        self.unique_spin.setToolTip("Minimum unique players between lineups")
        settings_layout.addRow("Min Unique:", self.unique_spin)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Optimize button
        self.optimize_btn = QPushButton("🚀 OPTIMIZE LINEUPS")
        self.optimize_btn.clicked.connect(self.run_optimization)
        self.optimize_btn.setEnabled(False)
        layout.addWidget(self.optimize_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Console output
        console_group = QGroupBox("📝 Console Output")
        console_layout = QVBoxLayout()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(200)
        console_layout.addWidget(self.console)
        console_group.setLayout(console_layout)
        layout.addWidget(console_group)

        layout.addStretch()
        return widget

    def create_results_panel(self):
        """Create results display panel"""
        self.tabs = QTabWidget()

        # Lineups tab
        self.lineups_table = QTableWidget()
        self.lineups_table.setSortingEnabled(True)
        self.tabs.addTab(self.lineups_table, "📋 Lineups")

        # Analysis tab
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.tabs.addTab(self.analysis_text, "📊 Analysis")

        # Export button
        export_widget = QWidget()
        export_layout = QVBoxLayout(export_widget)
        export_layout.addWidget(self.tabs)

        export_btn = QPushButton("💾 Export Lineups")
        export_btn.clicked.connect(self.export_lineups)
        export_layout.addWidget(export_btn)

        return export_widget

    def update_mode_info(self):
        """Update mode information label"""
        if self.gpp_radio.isChecked():
            self.mode_info.setText("🎯 GPP: Stack 3-5 players, +15% team boost, +10% order boost")
            self.mode_info.setStyleSheet("color: #d32f2f; font-weight: bold;")
        else:
            self.mode_info.setText("💰 Cash: Max 3 per team, +8% team boost, +5% order boost")
            self.mode_info.setStyleSheet("color: #388e3c; font-weight: bold;")

    def load_csv(self):
        """Load and analyze CSV file"""
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

            # Store path
            self.csv_path = file_path
            self.file_label.setText(os.path.basename(file_path))

            # Analyze slate
            self.analyze_slate(df)

            # Enable optimization
            self.optimize_btn.setEnabled(True)
            self.log("CSV loaded successfully", "success")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")

    def analyze_slate(self, df):
        """Analyze and display slate information"""
        # Basic stats
        num_players = len(df)
        avg_salary = df['Salary'].mean() if 'Salary' in df.columns else 0

        # Detect slate type
        positions = df['Position'].unique() if 'Position' in df.columns else []
        is_showdown = 'CPT' in positions or 'UTIL' in positions

        # Count games
        num_teams = df['TeamAbbrev'].nunique() if 'TeamAbbrev' in df.columns else 0
        num_games = num_teams // 2

        # Update display
        info = f"""
        <b>Slate Type:</b> {'SHOWDOWN' if is_showdown else 'CLASSIC'}<br>
        <b>Total Players:</b> {num_players}<br>
        <b>Games:</b> {num_games}<br>
        <b>Avg Salary:</b> ${avg_salary:,.0f}<br>
        """

        if is_showdown:
            info += "<br><b>⚡ Showdown Mode:</b> 1 Captain + 5 UTIL"

        self.slate_details.setText(info.strip())

    def log(self, message, level="info"):
        """Add message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        colors = {
            "info": "#000000",
            "success": "#4CAF50",
            "warning": "#ff9800",
            "error": "#f44336"
        }

        color = colors.get(level, "#000000")
        self.console.append(f'<span style="color: #666">[{timestamp}]</span> '
                            f'<span style="color: {color}">{message}</span>')

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

        # Log start
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

        # Columns depend on lineup type
        first_lineup = lineups[0]
        if first_lineup.get('type') == 'showdown':
            columns = ['Lineup', 'Captain', 'UTIL1', 'UTIL2', 'UTIL3', 'UTIL4', 'UTIL5', 'Salary', 'Proj']
        else:
            columns = ['Lineup', 'P1', 'P2', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3', 'Salary', 'Proj']

        self.lineups_table.setColumnCount(len(columns))
        self.lineups_table.setHorizontalHeaderLabels(columns)

        # Populate table
        for i, lineup in enumerate(lineups):
            self.lineups_table.setItem(i, 0, QTableWidgetItem(f"#{i + 1}"))

            if lineup.get('type') == 'showdown':
                # Showdown format
                self.lineups_table.setItem(i, 1, QTableWidgetItem(f"{lineup['captain'].name} (C)"))
                for j, util in enumerate(lineup['utilities']):
                    self.lineups_table.setItem(i, j + 2, QTableWidgetItem(util.name))
            else:
                # Classic format
                positions = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
                col = 1
                for pos in positions:
                    for player in lineup['players']:
                        if player.primary_position == pos or pos in player.primary_position:
                            self.lineups_table.setItem(i, col, QTableWidgetItem(player.name))
                            col += 1
                            break

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

        analysis = f"""
        <h2>Lineup Analysis</h2>
        <p><b>Total Lineups:</b> {len(lineups)}</p>
        <p><b>Average Projection:</b> {sum(l['total_score'] for l in lineups) / len(lineups):.1f}</p>
        <p><b>Average Salary Used:</b> ${sum(l['total_salary'] for l in lineups) / len(lineups):,.0f}</p>
        """

        # Find stacks
        stacks = {}
        for lineup in lineups:
            teams = {}
            for player in lineup['players']:
                team = player.team
                if team not in teams:
                    teams[team] = 0
                teams[team] += 1

            for team, count in teams.items():
                if count >= 3:
                    if team not in stacks:
                        stacks[team] = 0
                    stacks[team] += 1

        if stacks:
            analysis += "<h3>Stack Usage</h3><ul>"
            for team, count in sorted(stacks.items(), key=lambda x: x[1], reverse=True):
                analysis += f"<li>{team}: {count} lineups ({count / len(lineups) * 100:.0f}%)</li>"
            analysis += "</ul>"

        self.analysis_text.setHtml(analysis)

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
            # Create export data
            rows = []
            for i, lineup in enumerate(self.lineups):
                row = {'Lineup': i + 1}

                if lineup.get('type') == 'showdown':
                    row['Captain'] = lineup['captain'].name
                    for j, util in enumerate(lineup['utilities']):
                        row[f'UTIL{j + 1}'] = util.name
                else:
                    # Add players by position
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
            QMessageBox.information(self, "Export Complete", f"Lineups exported to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("DFS Optimizer - Correlation Edition")

    # Create and show window
    window = StreamlinedDFSGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()