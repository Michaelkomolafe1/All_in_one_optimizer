#!/usr/bin/env python3
"""
Smart DFS Optimizer GUI
======================
Automatically detects slate type and optimizes accordingly
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

# Import your optimization system
from unified_core_system import UnifiedCoreSystem


class SlateAnalyzer:
    """Analyzes uploaded CSV to determine slate characteristics"""

    @staticmethod
    def analyze_slate(df: pd.DataFrame) -> Dict:
        """
        Analyze slate and return characteristics
        """
        analysis = {
            'type': 'unknown',
            'teams': [],
            'games': 0,
            'players': len(df),
            'has_captains': False,
            'positions': [],
            'salary_range': {},
            'recommendations': []
        }

        # Check for team columns
        team_cols = ['Team', 'TeamAbbrev', 'team']
        team_col = None
        for col in team_cols:
            if col in df.columns:
                team_col = col
                break

        if team_col:
            teams = df[team_col].dropna().unique()
            analysis['teams'] = list(teams)
            analysis['games'] = len(teams) // 2

        # Check for captain mode
        if 'Name' in df.columns:
            analysis['has_captains'] = df['Name'].str.contains('(CPT)', na=False).any()

        # Get positions
        pos_cols = ['Position', 'Pos', 'position']
        for col in pos_cols:
            if col in df.columns:
                positions = df[col].dropna().unique()
                analysis['positions'] = list(positions)
                break

        # Salary analysis
        sal_cols = ['Salary', 'salary']
        for col in sal_cols:
            if col in df.columns:
                analysis['salary_range'] = {
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'avg': df[col].mean()
                }
                break

        # Determine slate type
        if len(analysis['teams']) == 2:
            analysis['type'] = 'showdown'
            analysis['recommendations'].append("🎪 Showdown slate detected (2 teams)")
            analysis['recommendations'].append("Will optimize for 1 Captain + 5 Utilities")
        elif len(analysis['teams']) <= 6:
            analysis['type'] = 'small'
            analysis['recommendations'].append("📊 Small slate detected (3-6 teams)")
            analysis['recommendations'].append("Consider using 'cash' or 'balanced' strategy")
        elif len(analysis['teams']) <= 20:
            analysis['type'] = 'main'
            analysis['recommendations'].append("🎯 Main slate detected (7-20 teams)")
            analysis['recommendations'].append("All strategies available")
        else:
            analysis['type'] = 'large'
            analysis['recommendations'].append("📈 Large slate detected (20+ teams)")
            analysis['recommendations'].append("Consider GPP strategies for differentiation")

        # Sport detection
        if 'P' in analysis['positions'] or 'SP' in analysis['positions']:
            analysis['sport'] = 'MLB'
        elif 'QB' in analysis['positions']:
            analysis['sport'] = 'NFL'
        elif 'PG' in analysis['positions'] or 'SG' in analysis['positions']:
            analysis['sport'] = 'NBA'
        else:
            analysis['sport'] = 'Unknown'

        return analysis


class SmartDFSGUI(QMainWindow):
    """Intelligent DFS Optimizer GUI with auto-detection"""

    def __init__(self):
        super().__init__()
        self.csv_path = None
        self.players_df = None
        self.slate_analysis = None
        self.optimization_thread = None
        self.lineups = []

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Smart DFS Optimizer - Auto-Detect Edition")
        self.setGeometry(100, 100, 1200, 800)

        # Apply modern dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #4d4d4d;
            }
            QPushButton#primary {
                background-color: #4CAF50;
                border: none;
            }
            QPushButton#primary:hover {
                background-color: #5CBF60;
            }
            QComboBox, QSpinBox, QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                padding: 6px;
                border-radius: 4px;
            }
            QGroupBox {
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #4CAF50;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #252525;
                gridline-color: #3d3d3d;
            }
            QHeaderView::section {
                background-color: #3d3d3d;
                padding: 5px;
                border: none;
            }
            QProgressBar {
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top toolbar
        self.create_toolbar()

        # Main content area
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        # Left panel - Controls
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 1)

        # Right panel - Results
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 2)

        # Status bar
        self.create_status_bar()

    def create_toolbar(self):
        """Create top toolbar"""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)

        # Load CSV action
        load_action = QAction(QIcon(), "📁 Load CSV", self)
        load_action.triggered.connect(self.load_csv)
        toolbar.addAction(load_action)

        toolbar.addSeparator()

        # Export action
        export_action = QAction(QIcon(), "💾 Export Lineups", self)
        export_action.triggered.connect(self.export_lineups)
        toolbar.addAction(export_action)

        # Settings action
        settings_action = QAction(QIcon(), "⚙️ Settings", self)
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)

    def create_left_panel(self) -> QWidget:
        """Create left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Slate info card
        self.slate_info = QGroupBox("📊 Slate Analysis")
        slate_layout = QVBoxLayout()
        self.slate_details = QLabel("No slate loaded")
        self.slate_details.setWordWrap(True)
        self.slate_details.setStyleSheet("padding: 10px; background-color: #2d2d2d; border-radius: 4px;")
        slate_layout.addWidget(self.slate_details)
        self.slate_info.setLayout(slate_layout)
        layout.addWidget(self.slate_info)

        # Smart optimization settings
        self.opt_settings = QGroupBox("🎯 Optimization Settings")
        opt_layout = QFormLayout()

        # Auto-detected strategy
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(['Auto-Detect', 'balanced', 'ceiling', 'safe', 'value', 'contrarian'])
        opt_layout.addRow("Strategy:", self.strategy_combo)

        # Contest type (auto-selected based on slate)
        self.contest_combo = QComboBox()
        self.contest_combo.addItems(['Auto-Detect', 'cash', 'gpp', 'balanced_gpp'])
        opt_layout.addRow("Contest:", self.contest_combo)

        # Number of lineups
        self.lineups_spin = QSpinBox()
        self.lineups_spin.setRange(1, 150)
        self.lineups_spin.setValue(20)
        opt_layout.addRow("Lineups:", self.lineups_spin)

        # Min salary
        self.salary_slider = QSlider(Qt.Horizontal)
        self.salary_slider.setRange(85, 100)
        self.salary_slider.setValue(95)
        self.salary_label = QLabel("95%")
        self.salary_slider.valueChanged.connect(
            lambda v: self.salary_label.setText(f"{v}%")
        )
        salary_layout = QHBoxLayout()
        salary_layout.addWidget(self.salary_slider)
        salary_layout.addWidget(self.salary_label)
        opt_layout.addRow("Min Salary:", salary_layout)

        self.opt_settings.setLayout(opt_layout)
        layout.addWidget(self.opt_settings)

        # Optimize button
        self.optimize_btn = QPushButton("🚀 OPTIMIZE LINEUPS")
        self.optimize_btn.setObjectName("primary")
        self.optimize_btn.setMinimumHeight(50)
        self.optimize_btn.clicked.connect(self.optimize_lineups)
        self.optimize_btn.setEnabled(False)
        layout.addWidget(self.optimize_btn)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Console
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(150)
        self.console.setStyleSheet("font-family: monospace; font-size: 10pt;")
        layout.addWidget(self.console)

        layout.addStretch()
        return panel

    def create_right_panel(self) -> QWidget:
        """Create right results panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Results tabs
        self.results_tabs = QTabWidget()

        # Lineups tab
        self.lineups_widget = QTableWidget()
        self.lineups_widget.setAlternatingRowColors(True)
        self.results_tabs.addTab(self.lineups_widget, "📋 Lineups")

        # Analysis tab
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.results_tabs.addTab(self.analysis_text, "📊 Analysis")

        # Player pool tab
        self.players_table = QTableWidget()
        self.players_table.setAlternatingRowColors(True)
        self.results_tabs.addTab(self.players_table, "👥 Player Pool")

        layout.addWidget(self.results_tabs)

        return panel

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready to load slate")

    def load_csv(self):
        """Load and analyze CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select DFS CSV",
            "",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            # Load CSV
            self.csv_path = file_path
            self.players_df = pd.read_csv(file_path)

            # Analyze slate
            self.slate_analysis = SlateAnalyzer.analyze_slate(self.players_df)

            # Update UI based on analysis
            self.update_slate_info()
            self.auto_configure_settings()

            # Enable optimization
            self.optimize_btn.setEnabled(True)

            # Log
            self.log(f"✅ Loaded {len(self.players_df)} players", "success")
            self.log(f"📊 Slate type: {self.slate_analysis['type'].upper()}", "info")

            # Update player pool display
            self.update_player_pool_display()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV:\n{str(e)}")

    def update_slate_info(self):
        """Update slate information display"""
        if not self.slate_analysis:
            return

        info = self.slate_analysis

        # Build info text
        text = f"<b>Slate Type:</b> {info['type'].upper()}<br>"
        text += f"<b>Teams:</b> {len(info['teams'])} ({', '.join(info['teams'][:5])}{'...' if len(info['teams']) > 5 else ''})<br>"
        text += f"<b>Players:</b> {info['players']}<br>"
        text += f"<b>Games:</b> {info['games']}<br>"

        if info['salary_range']:
            text += f"<b>Salary Range:</b> ${info['salary_range']['min']:,} - ${info['salary_range']['max']:,}<br>"

        if info['has_captains']:
            text += "<b>Mode:</b> 🎪 SHOWDOWN (Captains detected)<br>"

        text += "<br><b>Recommendations:</b><br>"
        for rec in info['recommendations']:
            text += f"• {rec}<br>"

        self.slate_details.setText(text)

    def auto_configure_settings(self):
        """Auto-configure settings based on slate analysis"""
        if not self.slate_analysis:
            return

        slate_type = self.slate_analysis['type']

        # Auto-select contest type
        if slate_type == 'showdown':
            self.contest_combo.setCurrentText('Auto-Detect')
            self.lineups_spin.setValue(5)
            self.salary_slider.setValue(95)
            self.log("🎪 Showdown mode auto-configured", "info")

        elif slate_type == 'small':
            self.contest_combo.setCurrentText('cash')
            self.lineups_spin.setValue(3)
            self.strategy_combo.setCurrentText('balanced')
            self.log("📊 Small slate - configured for cash games", "info")

        elif slate_type == 'main':
            self.contest_combo.setCurrentText('Auto-Detect')
            self.lineups_spin.setValue(20)
            self.log("🎯 Main slate - all options available", "info")

        else:  # large
            self.contest_combo.setCurrentText('gpp')
            self.lineups_spin.setValue(50)
            self.strategy_combo.setCurrentText('ceiling')
            self.log("📈 Large slate - configured for GPPs", "info")

    def optimize_lineups(self):
        """Run optimization with smart detection"""
        if not self.players_df:
            return

        # Determine actual contest type
        contest_type = self.contest_combo.currentText()
        if contest_type == 'Auto-Detect':
            if self.slate_analysis['type'] == 'showdown':
                contest_type = 'showdown'
            elif self.slate_analysis['type'] == 'small':
                contest_type = 'cash'
            else:
                contest_type = 'gpp'

        # Determine strategy
        strategy = self.strategy_combo.currentText()
        if strategy == 'Auto-Detect':
            if contest_type == 'cash':
                strategy = 'balanced'
            else:
                strategy = 'ceiling'

        # Prepare settings
        settings = {
            'csv_path': self.csv_path,
            'contest_type': contest_type,
            'strategy': strategy,
            'num_lineups': self.lineups_spin.value(),
            'min_salary': self.salary_slider.value() / 100
        }

        # Run optimization
        self.log(f"🚀 Starting optimization: {contest_type.upper()} - {strategy}", "info")
        self.run_optimization(settings)

    def run_optimization(self, settings):
        """Run optimization in thread"""
        self.progress_bar.show()
        self.optimize_btn.setEnabled(False)

        # Create and start worker thread
        self.worker = OptimizationWorker(settings)
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self.on_optimization_complete)
        self.worker.error.connect(self.on_optimization_error)
        self.worker.start()

    def update_progress(self, value, message):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(message)

    def log(self, message, level="info"):
        """Add message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if level == "error":
            color = "#ff4444"
        elif level == "success":
            color = "#44ff44"
        elif level == "warning":
            color = "#ffaa44"
        else:
            color = "#ffffff"

        html = f'<span style="color: #888">[{timestamp}]</span> '
        html += f'<span style="color: {color}">{message}</span>'

        self.console.append(html)

    def on_optimization_complete(self, lineups):
        """Handle successful optimization"""
        self.lineups = lineups
        self.progress_bar.hide()
        self.optimize_btn.setEnabled(True)

        self.log(f"✅ Generated {len(lineups)} lineups!", "success")

        # Display lineups
        self.display_lineups(lineups)

        # Switch to lineups tab
        self.results_tabs.setCurrentIndex(0)

    def on_optimization_error(self, error_msg):
        """Handle optimization error"""
        self.progress_bar.hide()
        self.optimize_btn.setEnabled(True)

        self.log(f"❌ Error: {error_msg}", "error")
        QMessageBox.critical(self, "Optimization Error", error_msg)

    def display_lineups(self, lineups):
        """Display lineups in table"""
        if not lineups:
            return

        # Check if showdown format
        is_showdown = lineups[0].get('type') == 'showdown'

        if is_showdown:
            self.display_showdown_lineups(lineups)
        else:
            self.display_regular_lineups(lineups)

    def display_showdown_lineups(self, lineups):
        """Display showdown lineups"""
        # Setup table
        self.lineups_widget.setRowCount(len(lineups))
        self.lineups_widget.setColumnCount(8)
        self.lineups_widget.setHorizontalHeaderLabels([
            'Lineup', 'Captain', 'UTIL 1', 'UTIL 2', 'UTIL 3', 'UTIL 4', 'UTIL 5', 'Salary', 'Points'
        ])

        for i, lineup in enumerate(lineups):
            # Lineup number
            self.lineups_widget.setItem(i, 0, QTableWidgetItem(f"#{i + 1}"))

            # Captain
            captain = lineup['captain']
            self.lineups_widget.setItem(i, 1, QTableWidgetItem(
                f"{captain.name} (${int(captain.salary * 1.5)})"
            ))

            # Utilities
            for j, player in enumerate(lineup['utilities']):
                self.lineups_widget.setItem(i, j + 2, QTableWidgetItem(
                    f"{player.name} (${player.salary})"
                ))

            # Salary and points
            self.lineups_widget.setItem(i, 7, QTableWidgetItem(f"${lineup['total_salary']:,}"))
            self.lineups_widget.setItem(i, 8, QTableWidgetItem(f"{lineup['total_score']:.1f}"))

        self.lineups_widget.resizeColumnsToContents()

    def display_regular_lineups(self, lineups):
        """Display regular lineups"""
        # Setup table based on first lineup
        if not lineups:
            return

        first = lineups[0]['players']
        positions = [p['position'] for p in first]

        self.lineups_widget.setRowCount(len(lineups))
        self.lineups_widget.setColumnCount(len(positions) + 3)

        headers = ['Lineup'] + positions + ['Salary', 'Points']
        self.lineups_widget.setHorizontalHeaderLabels(headers)

        for i, lineup in enumerate(lineups):
            # Lineup number
            self.lineups_widget.setItem(i, 0, QTableWidgetItem(f"#{i + 1}"))

            # Players
            for j, player in enumerate(lineup['players']):
                self.lineups_widget.setItem(i, j + 1, QTableWidgetItem(
                    f"{player['name']} (${player['salary']})"
                ))

            # Totals
            self.lineups_widget.setItem(i, len(positions) + 1, QTableWidgetItem(
                f"${lineup['total_salary']:,}"
            ))
            self.lineups_widget.setItem(i, len(positions) + 2, QTableWidgetItem(
                f"{lineup['projected_points']:.1f}"
            ))

        self.lineups_widget.resizeColumnsToContents()

    def update_player_pool_display(self):
        """Update player pool display"""
        if self.players_df is None:
            return

        # Setup table
        self.players_table.setRowCount(len(self.players_df))
        self.players_table.setColumnCount(5)
        self.players_table.setHorizontalHeaderLabels([
            'Name', 'Position', 'Team', 'Salary', 'Projection'
        ])

        # Fill data
        for i, row in self.players_df.iterrows():
            self.players_table.setItem(i, 0, QTableWidgetItem(str(row.get('Name', ''))))
            self.players_table.setItem(i, 1, QTableWidgetItem(str(row.get('Position', ''))))
            self.players_table.setItem(i, 2, QTableWidgetItem(str(row.get('Team', ''))))
            self.players_table.setItem(i, 3, QTableWidgetItem(f"${row.get('Salary', 0):,}"))
            self.players_table.setItem(i, 4, QTableWidgetItem(f"{row.get('AvgPointsPerGame', 0):.1f}"))

        self.players_table.resizeColumnsToContents()

    def export_lineups(self):
        """Export lineups to CSV"""
        if not self.lineups:
            QMessageBox.warning(self, "No Lineups", "No lineups to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Lineups",
            f"lineups_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )

        if file_path:
            # Create export data
            export_data = []

            for lineup in self.lineups:
                if lineup.get('type') == 'showdown':
                    # Showdown format
                    row = {
                        'CPT': lineup['captain'].name,
                        'UTIL1': lineup['utilities'][0].name,
                        'UTIL2': lineup['utilities'][1].name,
                        'UTIL3': lineup['utilities'][2].name,
                        'UTIL4': lineup['utilities'][3].name,
                        'UTIL5': lineup['utilities'][4].name,
                        'Salary': lineup['total_salary'],
                        'Points': lineup['total_score']
                    }
                else:
                    # Regular format
                    row = {}
                    for player in lineup['players']:
                        row[player['position']] = player['name']
                    row['Salary'] = lineup['total_salary']
                    row['Points'] = lineup['projected_points']

                export_data.append(row)

            # Save to CSV
            df = pd.DataFrame(export_data)
            df.to_csv(file_path, index=False)

            self.log(f"✅ Exported {len(self.lineups)} lineups to {file_path}", "success")

    def show_settings(self):
        """Show settings dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        # Add settings options
        info = QLabel("Settings coming soon...")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec_()


class OptimizationWorker(QThread):
    """Worker thread for optimization"""

    progress = pyqtSignal(int, str)
    log = pyqtSignal(str, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):
        """Run optimization"""
        try:
            # Initialize system
            self.progress.emit(10, "Initializing system...")
            system = UnifiedCoreSystem()

            # Load CSV
            self.progress.emit(20, "Loading players...")
            system.load_csv(self.settings['csv_path'])

            # Fetch confirmations
            self.progress.emit(40, "Fetching confirmations...")
            system.fetch_confirmed_players()

            # Build pool
            self.progress.emit(60, "Building player pool...")
            system.build_player_pool()

            # Enrich data
            self.progress.emit(80, "Enriching player data...")
            system.enrich_player_pool()

            # Optimize
            self.progress.emit(90, "Optimizing lineups...")

            # The system will auto-detect showdown
            lineups = system.optimize_lineups(
                num_lineups=self.settings['num_lineups'],
                strategy=self.settings['strategy'],
                contest_type=self.settings['contest_type']
            )

            self.progress.emit(100, "Complete!")

            # Convert to GUI format
            gui_lineups = self.convert_lineups(lineups)
            self.finished.emit(gui_lineups)

        except Exception as e:
            self.error.emit(str(e))

    def convert_lineups(self, lineups):
        """Convert lineups to GUI format"""
        # The lineups are already in the correct format
        return lineups


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Smart DFS Optimizer")

    # Apply application style
    app.setStyle('Fusion')

    # Create and show window
    window = SmartDFSGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()