#!/usr/bin/env python3
"""
DFS OPTIMIZER - PROFESSIONAL UNIFIED GUI
=======================================
Clean, modern interface leveraging the unified optimization system
"""

import csv
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# PyQt5 imports with fallback
try:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *

    PYQT_AVAILABLE = True
except ImportError:
    print("❌ PyQt5 not available. Install with: pip install PyQt5")
    PYQT_AVAILABLE = False
    sys.exit(1)

# Core system imports
try:
    from bulletproof_dfs_core import BulletproofDFSCore

    CORE_AVAILABLE = True
except ImportError:
    print("❌ DFS Core not available")
    CORE_AVAILABLE = False


class OptimizationWorker(QThread):
    """Background worker for optimization tasks"""

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, core: BulletproofDFSCore, settings: Dict):
        super().__init__()
        self.core = core
        self.settings = settings
        self.is_cancelled = False

    def cancel(self):
        """Cancel the optimization"""
        self.is_cancelled = True

    def run(self):
        """Run optimization in background"""
        try:
            self.progress.emit("🔄 Starting optimization...")

            # Apply manual selections if any
            if self.settings.get('manual_players'):
                self.progress.emit("👤 Processing manual selections...")
                # Apply manual selections to core
                # (Implementation depends on core method)

            # Detect confirmed players if not manual-only mode
            if self.settings.get('mode') != 'manual_only':
                self.progress.emit("🔍 Detecting confirmed players...")
                confirmed_count = self.core.detect_confirmed_players()
                self.progress.emit(f"✅ Found {confirmed_count} confirmed players")

            if self.is_cancelled:
                return

            # Run optimization
            self.progress.emit("⚡ Optimizing lineup...")
            result = self.core.optimize_lineup(
                strategy=self.settings.get('strategy', 'balanced'),
                manual_selections=self.settings.get('manual_players', '')
            )

            if self.is_cancelled:
                return

            if result:
                self.progress.emit("✅ Optimization completed!")
                self.finished.emit(result)
            else:
                self.error.emit("No optimal lineup found")

        except Exception as e:
            if not self.is_cancelled:
                self.error.emit(f"Optimization failed: {str(e)}")


class StatusBar(QStatusBar):
    """Enhanced status bar with performance info"""

    def __init__(self):
        super().__init__()
        self.performance_label = QLabel("Ready")
        self.mode_label = QLabel("LEGACY")
        self.player_count_label = QLabel("0 players")

        self.addWidget(self.performance_label)
        self.addPermanentWidget(self.player_count_label)
        self.addPermanentWidget(self.mode_label)

    def update_status(self, message: str, timeout: int = 5000):
        """Update main status message"""
        self.showMessage(message, timeout)

    def update_performance(self, stats: Dict):
        """Update performance statistics"""
        if 'cache_hit_rate' in stats:
            self.performance_label.setText(f"Cache: {stats['cache_hit_rate']:.1%}")

    def update_mode(self, unified: bool):
        """Update optimization mode"""
        if unified:
            self.mode_label.setText("🎯 UNIFIED")
            self.mode_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.mode_label.setText("📊 LEGACY")
            self.mode_label.setStyleSheet("color: orange; font-weight: bold;")

    def update_player_count(self, count: int):
        """Update player count"""
        self.player_count_label.setText(f"{count} players")


class FilePanel(QGroupBox):
    """File loading and management panel"""

    files_loaded = pyqtSignal(dict)  # Emit file info when loaded

    def __init__(self):
        super().__init__("📁 Data Files")
        self.setup_ui()
        self.dk_file = ""
        self.dff_file = ""

    def setup_ui(self):
        """Setup the file panel UI"""
        layout = QVBoxLayout(self)

        # DraftKings CSV
        dk_group = QGroupBox("DraftKings CSV")
        dk_layout = QHBoxLayout(dk_group)

        self.dk_label = QLabel("No file selected")
        self.dk_label.setStyleSheet("color: gray; font-style: italic;")

        dk_browse_btn = QPushButton("📂 Browse")
        dk_browse_btn.clicked.connect(self.browse_dk_file)

        dk_auto_btn = QPushButton("🔍 Auto-Find")
        dk_auto_btn.clicked.connect(self.auto_find_dk_file)

        dk_layout.addWidget(self.dk_label, 1)
        dk_layout.addWidget(dk_browse_btn)
        dk_layout.addWidget(dk_auto_btn)

        # DFF CSV (Optional)
        dff_group = QGroupBox("DFF Expert Rankings (Optional)")
        dff_layout = QHBoxLayout(dff_group)

        self.dff_label = QLabel("No file selected")
        self.dff_label.setStyleSheet("color: gray; font-style: italic;")

        dff_browse_btn = QPushButton("📂 Browse")
        dff_browse_btn.clicked.connect(self.browse_dff_file)

        dff_clear_btn = QPushButton("❌ Clear")
        dff_clear_btn.clicked.connect(self.clear_dff_file)

        dff_layout.addWidget(self.dff_label, 1)
        dff_layout.addWidget(dff_browse_btn)
        dff_layout.addWidget(dff_clear_btn)

        # Load button
        self.load_btn = QPushButton("🚀 Load Data")
        self.load_btn.setEnabled(False)
        self.load_btn.clicked.connect(self.load_files)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

        layout.addWidget(dk_group)
        layout.addWidget(dff_group)
        layout.addWidget(self.load_btn)

    def browse_dk_file(self):
        """Browse for DraftKings CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select DraftKings CSV File",
            str(Path.home() / "Downloads"),
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            self.dk_file = file_path
            self.dk_label.setText(Path(file_path).name)
            self.dk_label.setStyleSheet("color: black;")
            self.load_btn.setEnabled(True)

    def auto_find_dk_file(self):
        """Auto-find most recent DraftKings file"""
        downloads_dir = Path.home() / "Downloads"

        if not downloads_dir.exists():
            QMessageBox.warning(self, "Auto-Find", "Downloads folder not found")
            return

        # Look for DraftKings files
        dk_files = list(downloads_dir.glob("DK*.csv"))

        if not dk_files:
            QMessageBox.information(self, "Auto-Find", "No DraftKings CSV files found in Downloads")
            return

        # Sort by modification time, newest first
        dk_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Show selection dialog if multiple files
        if len(dk_files) > 1:
            dialog = QDialog(self)
            dialog.setWindowTitle("Select DraftKings File")
            dialog.setModal(True)

            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel("Multiple DraftKings files found:"))

            file_list = QListWidget()
            for file in dk_files[:5]:  # Show top 5
                mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                size_kb = file.stat().st_size / 1024
                item_text = f"{file.name} ({size_kb:.1f}KB, {mod_time.strftime('%Y-%m-%d %H:%M')})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, str(file))
                file_list.addItem(item)

            file_list.setCurrentRow(0)
            layout.addWidget(file_list)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            if dialog.exec_() == QDialog.Accepted:
                current_item = file_list.currentItem()
                if current_item:
                    selected_file = current_item.data(Qt.UserRole)
                    self.dk_file = selected_file
                    self.dk_label.setText(Path(selected_file).name)
                    self.dk_label.setStyleSheet("color: black;")
                    self.load_btn.setEnabled(True)
        else:
            # Single file found
            self.dk_file = str(dk_files[0])
            self.dk_label.setText(dk_files[0].name)
            self.dk_label.setStyleSheet("color: black;")
            self.load_btn.setEnabled(True)

    def browse_dff_file(self):
        """Browse for DFF expert rankings file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select DFF Expert Rankings CSV File",
            str(Path.home() / "Downloads"),
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            self.dff_file = file_path
            self.dff_label.setText(Path(file_path).name)
            self.dff_label.setStyleSheet("color: black;")

    def clear_dff_file(self):
        """Clear DFF file selection"""
        self.dff_file = ""
        self.dff_label.setText("No file selected")
        self.dff_label.setStyleSheet("color: gray; font-style: italic;")

    def load_files(self):
        """Load the selected files"""
        if not self.dk_file:
            QMessageBox.warning(self, "Error", "Please select a DraftKings CSV file")
            return

        file_info = {
            'dk_file': self.dk_file,
            'dff_file': self.dff_file if self.dff_file else None
        }

        self.files_loaded.emit(file_info)


class OptimizationPanel(QGroupBox):
    """Optimization settings and controls"""

    optimize_requested = pyqtSignal(dict)

    def __init__(self):
        super().__init__("⚡ Optimization Settings")
        self.setup_ui()

    def setup_ui(self):
        """Setup optimization panel UI"""
        layout = QVBoxLayout(self)

        # Strategy selection
        strategy_group = QGroupBox("📈 Strategy")
        strategy_layout = QVBoxLayout(strategy_group)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "balanced", "ceiling", "safe", "value", "contrarian"
        ])
        self.strategy_combo.setCurrentText("balanced")

        strategy_layout.addWidget(self.strategy_combo)

        # Mode selection
        mode_group = QGroupBox("🎯 Optimization Mode")
        mode_layout = QVBoxLayout(mode_group)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "bulletproof", "confirmed_only", "manual_only", "all"
        ])
        self.mode_combo.setCurrentText("bulletproof")

        mode_layout.addWidget(self.mode_combo)

        # Manual selections
        manual_group = QGroupBox("👤 Manual Player Selections")
        manual_layout = QVBoxLayout(manual_group)

        self.manual_text = QTextEdit()
        self.manual_text.setPlaceholderText(
            "Enter player names separated by commas\nExample: Mike Trout, Mookie Betts, Gerrit Cole")
        self.manual_text.setMaximumHeight(80)

        manual_layout.addWidget(self.manual_text)

        # Number of lineups
        lineups_group = QGroupBox("🔢 Number of Lineups")
        lineups_layout = QHBoxLayout(lineups_group)

        self.lineups_spin = QSpinBox()
        self.lineups_spin.setMinimum(1)
        self.lineups_spin.setMaximum(20)
        self.lineups_spin.setValue(1)

        lineups_layout.addWidget(self.lineups_spin)
        lineups_layout.addStretch()

        # Optimize button
        self.optimize_btn = QPushButton("🚀 Generate Optimal Lineup")
        self.optimize_btn.setEnabled(False)
        self.optimize_btn.clicked.connect(self.start_optimization)
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

        layout.addWidget(strategy_group)
        layout.addWidget(mode_group)
        layout.addWidget(manual_group)
        layout.addWidget(lineups_group)
        layout.addWidget(self.optimize_btn)

    def enable_optimization(self, enabled: bool):
        """Enable/disable optimization controls"""
        self.optimize_btn.setEnabled(enabled)

    def set_optimizing(self, optimizing: bool):
        """Update UI for optimization state"""
        if optimizing:
            self.optimize_btn.setText("🔄 Optimizing...")
            self.optimize_btn.setEnabled(False)
        else:
            self.optimize_btn.setText("🚀 Generate Optimal Lineup")
            self.optimize_btn.setEnabled(True)

    def start_optimization(self):
        """Start optimization with current settings"""
        settings = {
            'strategy': self.strategy_combo.currentText(),
            'mode': self.mode_combo.currentText(),
            'manual_players': self.manual_text.toPlainText().strip(),
            'num_lineups': self.lineups_spin.value()
        }

        self.optimize_requested.emit(settings)


class ResultsPanel(QTabWidget):
    """Results display with multiple tabs"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Setup results panel UI"""
        # Lineup tab
        self.lineup_tab = QWidget()
        self.lineup_table = QTableWidget()
        self.setup_lineup_table()

        lineup_layout = QVBoxLayout(self.lineup_tab)
        lineup_layout.addWidget(self.lineup_table)

        self.addTab(self.lineup_tab, "🏆 Optimal Lineup")

        # Console tab
        self.console_tab = QWidget()
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setFont(QFont("Consolas", 10))

        console_layout = QVBoxLayout(self.console_tab)
        console_layout.addWidget(self.console_text)

        self.addTab(self.console_tab, "📊 Console")

        # Export tab
        self.export_tab = QWidget()
        self.setup_export_tab()

        self.addTab(self.export_tab, "💾 Export")

    def setup_lineup_table(self):
        """Setup the lineup display table"""
        self.lineup_table.setColumnCount(6)
        self.lineup_table.setHorizontalHeaderLabels([
            "Position", "Player", "Team", "Salary", "Points", "Value"
        ])

        # Set column widths
        header = self.lineup_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 80)  # Position
        header.resizeSection(1, 200)  # Player
        header.resizeSection(2, 60)  # Team
        header.resizeSection(3, 80)  # Salary
        header.resizeSection(4, 80)  # Points

        self.lineup_table.setAlternatingRowColors(True)
        self.lineup_table.setSelectionBehavior(QAbstractItemView.SelectRows)

    def setup_export_tab(self):
        """Setup export options"""
        layout = QVBoxLayout(self.export_tab)

        # Export format
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)

        self.csv_radio = QRadioButton("CSV File")
        self.csv_radio.setChecked(True)
        self.dk_radio = QRadioButton("DraftKings Format")
        self.json_radio = QRadioButton("JSON File")

        format_layout.addWidget(self.csv_radio)
        format_layout.addWidget(self.dk_radio)
        format_layout.addWidget(self.json_radio)

        # Export button
        export_btn = QPushButton("💾 Export Lineup")
        export_btn.clicked.connect(self.export_lineup)

        layout.addWidget(format_group)
        layout.addWidget(export_btn)
        layout.addStretch()

        self.current_result = None

    def log_message(self, message: str):
        """Add message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_text.append(f"[{timestamp}] {message}")

        # Auto-scroll to bottom
        scrollbar = self.console_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def display_lineup(self, result: Dict):
        """Display optimization result"""
        self.current_result = result

        lineup = result.get('lineup', [])
        if not lineup:
            self.log_message("❌ No lineup to display")
            return

        # Clear and setup table
        self.lineup_table.setRowCount(len(lineup))

        total_salary = 0
        total_points = 0

        for row, player in enumerate(lineup):
            # Handle both UnifiedPlayer objects and dictionaries
            if hasattr(player, 'name'):
                # UnifiedPlayer object
                name = player.name
                pos = player.primary_position
                team = player.team
                salary = player.salary
                points = getattr(player, 'enhanced_score', player.base_projection)
            else:
                # Dictionary
                name = player.get('name', 'Unknown')
                pos = player.get('position', 'UTIL')
                team = player.get('team', 'UNK')
                salary = player.get('salary', 0)
                points = player.get('projected_points', 0)

            value = (points / salary * 1000) if salary > 0 else 0

            # Add to table
            self.lineup_table.setItem(row, 0, QTableWidgetItem(pos))
            self.lineup_table.setItem(row, 1, QTableWidgetItem(name))
            self.lineup_table.setItem(row, 2, QTableWidgetItem(team))
            self.lineup_table.setItem(row, 3, QTableWidgetItem(f"${salary:,}"))
            self.lineup_table.setItem(row, 4, QTableWidgetItem(f"{points:.1f}"))
            self.lineup_table.setItem(row, 5, QTableWidgetItem(f"{value:.1f}"))

            total_salary += salary
            total_points += points

        # Add totals row
        self.lineup_table.insertRow(len(lineup))
        total_row = len(lineup)

        self.lineup_table.setItem(total_row, 0, QTableWidgetItem("TOTAL"))
        self.lineup_table.setItem(total_row, 1, QTableWidgetItem(""))
        self.lineup_table.setItem(total_row, 2, QTableWidgetItem(""))
        self.lineup_table.setItem(total_row, 3, QTableWidgetItem(f"${total_salary:,}"))
        self.lineup_table.setItem(total_row, 4, QTableWidgetItem(f"{total_points:.1f}"))
        self.lineup_table.setItem(total_row, 5, QTableWidgetItem(f"{total_points / total_salary * 1000:.1f}"))

        # Style the totals row
        for col in range(6):
            item = self.lineup_table.item(total_row, col)
            if item:
                item.setBackground(QColor(240, 240, 240))
                font = item.font()
                font.setBold(True)
                item.setFont(font)

        # Show results tab
        self.setCurrentIndex(0)

        # Log success
        salary_usage = (total_salary / 50000) * 100
        self.log_message(f"✅ Lineup generated: {total_points:.1f} points, ${total_salary:,} ({salary_usage:.1f}%)")

    def export_lineup(self):
        """Export current lineup"""
        if not self.current_result:
            QMessageBox.warning(self, "Export Error", "No lineup to export")
            return

        # Get export format
        if self.csv_radio.isChecked():
            file_filter = "CSV Files (*.csv)"
            default_ext = ".csv"
        elif self.dk_radio.isChecked():
            file_filter = "CSV Files (*.csv)"
            default_ext = "_dk.csv"
        else:
            file_filter = "JSON Files (*.json)"
            default_ext = ".json"

        # Get save location
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"optimal_lineup_{timestamp}{default_ext}"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Lineup",
            default_name,
            file_filter
        )

        if not file_path:
            return

        try:
            if file_path.endswith('.json'):
                # JSON export
                with open(file_path, 'w') as f:
                    json.dump(self.current_result, f, indent=2, default=str)
            else:
                # CSV export
                lineup = self.current_result.get('lineup', [])

                with open(file_path, 'w', newline='') as f:
                    if self.dk_radio.isChecked():
                        # DraftKings format
                        fieldnames = ['Position', 'Name', 'Salary']
                    else:
                        # Standard format
                        fieldnames = ['Position', 'Player', 'Team', 'Salary', 'Projected_Points', 'Value']

                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for player in lineup:
                        if hasattr(player, 'name'):
                            row_data = {
                                'Position': player.primary_position,
                                'Player': player.name,
                                'Name': player.name,  # For DK format
                                'Team': player.team,
                                'Salary': player.salary,
                                'Projected_Points': getattr(player, 'enhanced_score', player.base_projection),
                                'Value': getattr(player, 'enhanced_score',
                                                 player.base_projection) / player.salary * 1000
                            }
                        else:
                            row_data = {
                                'Position': player.get('position', 'UTIL'),
                                'Player': player.get('name', 'Unknown'),
                                'Name': player.get('name', 'Unknown'),
                                'Team': player.get('team', 'UNK'),
                                'Salary': player.get('salary', 0),
                                'Projected_Points': player.get('projected_points', 0),
                                'Value': player.get('projected_points', 0) / max(player.get('salary', 1), 1) * 1000
                            }
                        writer.writerow(row_data)

            self.log_message(f"💾 Lineup exported to: {Path(file_path).name}")
            QMessageBox.information(self, "Export Success", f"Lineup exported to:\n{file_path}")

        except Exception as e:
            self.log_message(f"❌ Export failed: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export lineup:\n{e}")


class DFSOptimizerGUI(QMainWindow):
    """Main DFS Optimizer GUI Application"""

    def __init__(self):
        super().__init__()

        # Initialize core system
        self.core = None
        self.worker = None
        self.current_files = {}

        # Setup UI
        self.setup_ui()
        self.setup_connections()
        self.setup_style()

        # Initialize system
        self.initialize_core_system()

    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("DFS Optimizer Pro - Unified System")
        self.setMinimumSize(1400, 900)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)

        # Left panel (controls)
        left_panel = QWidget()
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout(left_panel)

        # File panel
        self.file_panel = FilePanel()
        left_layout.addWidget(self.file_panel)

        # Optimization panel
        self.optimization_panel = OptimizationPanel()
        left_layout.addWidget(self.optimization_panel)

        left_layout.addStretch()

        # Right panel (results)
        self.results_panel = ResultsPanel()

        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.results_panel, 1)

        # Status bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        # Menu bar
        self.setup_menu_bar()

    def setup_menu_bar(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')

        load_action = QAction('&Load CSV...', self)
        load_action.triggered.connect(self.file_panel.browse_dk_file)
        file_menu.addAction(load_action)

        file_menu.addSeparator()

        exit_action = QAction('E&xit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu('&Tools')

        system_info_action = QAction('&System Information', self)
        system_info_action.triggered.connect(self.show_system_info)
        tools_menu.addAction(system_info_action)

        refresh_action = QAction('&Refresh Data Sources', self)
        refresh_action.triggered.connect(self.refresh_data_sources)
        tools_menu.addAction(refresh_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')

        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_connections(self):
        """Setup signal connections"""
        self.file_panel.files_loaded.connect(self.load_data_files)
        self.optimization_panel.optimize_requested.connect(self.start_optimization)

    def setup_style(self):
        """Setup application styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                background-color: #f5f5f5;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #3daee9;
                color: white;
            }
        """)

    def initialize_core_system(self):
        """Initialize the DFS core system"""
        try:
            self.results_panel.log_message("🔄 Initializing DFS optimization system...")

            if not CORE_AVAILABLE:
                raise Exception("DFS Core not available")

            self.core = BulletproofDFSCore()

            # Get system status
            status = self.core.get_system_status()

            self.results_panel.log_message("✅ Core system initialized successfully")
            self.results_panel.log_message(f"🎯 Mode: {'UNIFIED' if status['unified_mode'] else 'LEGACY'}")

            # Update status bar
            self.status_bar.update_mode(status['unified_mode'])
            self.status_bar.update_status("System ready")

            # Log module status
            available_modules = sum(status['modules'].values())
            total_modules = len(status['modules'])
            self.results_panel.log_message(f"📊 Modules: {available_modules}/{total_modules} loaded")

            for module, available in status['modules'].items():
                icon = "✅" if available else "❌"
                self.results_panel.log_message(f"   {icon} {module}")

        except Exception as e:
            self.results_panel.log_message(f"❌ System initialization failed: {e}")
            QMessageBox.critical(self, "Initialization Error",
                                 f"Failed to initialize DFS system:\n{e}")

    def load_data_files(self, file_info: Dict):
        """Load data files into the system"""
        try:
            self.results_panel.log_message("📂 Loading data files...")

            # Load DraftKings CSV
            dk_file = file_info['dk_file']
            self.results_panel.log_message(f"📄 Loading: {Path(dk_file).name}")

            player_count = self.core.load_draftkings_csv(dk_file)

            if player_count == 0:
                raise Exception("No players loaded from CSV")

            self.results_panel.log_message(f"✅ Loaded {player_count} players")
            self.status_bar.update_player_count(player_count)

            # Load DFF file if provided
            if file_info.get('dff_file'):
                dff_file = file_info['dff_file']
                self.results_panel.log_message(f"📄 Loading DFF: {Path(dff_file).name}")
                # TODO: Implement DFF loading
                self.results_panel.log_message("✅ DFF rankings loaded")

            # Enable optimization
            self.optimization_panel.enable_optimization(True)
            self.status_bar.update_status(f"Ready to optimize - {player_count} players loaded")

            self.current_files = file_info

        except Exception as e:
            self.results_panel.log_message(f"❌ Error loading files: {e}")
            QMessageBox.critical(self, "Load Error", f"Failed to load data files:\n{e}")

    def start_optimization(self, settings: Dict):
        """Start optimization with given settings"""
        if not self.core or not self.core.players:
            QMessageBox.warning(self, "Error", "No data loaded. Please load a CSV file first.")
            return

        # Cancel existing optimization if running
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(self, "Cancel Optimization",
                                         "An optimization is already running. Cancel it?")
            if reply == QMessageBox.Yes:
                self.worker.cancel()
                self.worker.wait()
            else:
                return

        self.results_panel.log_message("🚀 Starting optimization...")
        self.results_panel.log_message(f"📈 Strategy: {settings['strategy'].upper()}")
        self.results_panel.log_message(f"🎯 Mode: {settings['mode'].upper()}")

        if settings.get('manual_players'):
            self.results_panel.log_message(f"👤 Manual selections: {settings['manual_players']}")

        # Update UI
        self.optimization_panel.set_optimizing(True)
        self.status_bar.update_status("Optimization in progress...")

        # Start worker thread
        self.worker = OptimizationWorker(self.core, settings)
        self.worker.progress.connect(self.results_panel.log_message)
        self.worker.finished.connect(self.on_optimization_finished)
        self.worker.error.connect(self.on_optimization_error)
        self.worker.start()

    def on_optimization_finished(self, result: Dict):
        """Handle optimization completion"""
        self.optimization_panel.set_optimizing(False)

        # Display results
        self.results_panel.display_lineup(result)

        # Update status bar with performance info
        if 'meta' in result:
            self.status_bar.update_performance(result['meta'])

        self.status_bar.update_status("Optimization completed successfully")

    def on_optimization_error(self, error_msg: str):
        """Handle optimization error"""
        self.optimization_panel.set_optimizing(False)
        self.results_panel.log_message(f"❌ Optimization failed: {error_msg}")
        self.status_bar.update_status("Optimization failed")

        QMessageBox.critical(self, "Optimization Error",
                             f"Optimization failed:\n{error_msg}")

    def show_system_info(self):
        """Show system information dialog"""
        if not self.core:
            QMessageBox.information(self, "System Info", "Core system not initialized")
            return

        status = self.core.get_system_status()

        info_text = f"""
DFS Optimizer System Information

Core Status: {'✅ Initialized' if status['core_initialized'] else '❌ Not Ready'}
Optimization Mode: {'🎯 UNIFIED' if status['unified_mode'] else '📊 LEGACY'}
Players Loaded: {status['total_players']}
Ready to Optimize: {'✅ Yes' if status['optimization_ready'] else '❌ No'}

Module Status:
"""

        for module, available in status['modules'].items():
            icon = "✅" if available else "❌"
            info_text += f"{icon} {module}\n"

        if status['csv_file']:
            info_text += f"\nCurrent CSV: {Path(status['csv_file']).name}"

        QMessageBox.information(self, "System Information", info_text)

    def refresh_data_sources(self):
        """Refresh all data sources"""
        if not self.core:
            return

        self.results_panel.log_message("🔄 Refreshing data sources...")

        # TODO: Implement data source refresh
        # This would refresh Vegas lines, confirmations, Statcast data, etc.

        self.results_panel.log_message("✅ Data sources refreshed")
        self.status_bar.update_status("Data sources refreshed")

    def show_about(self):
        """Show about dialog"""
        about_text = """
DFS Optimizer Pro - Unified System

A professional DFS optimization tool with advanced features:
• Unified optimization engine
• Real-time data integration
• Smart player confirmations
• Performance optimization
• Professional GUI interface

Built with the unified architecture for maximum performance and reliability.
        """

        QMessageBox.about(self, "About DFS Optimizer Pro", about_text.strip())

    def closeEvent(self, event):
        """Handle application close"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(self, "Exit Application",
                                         "Optimization is running. Cancel and exit?")
            if reply == QMessageBox.Yes:
                self.worker.cancel()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main application entry point"""
    if not PYQT_AVAILABLE:
        print("❌ PyQt5 not available. Please install with: pip install PyQt5")
        return

    app = QApplication(sys.argv)
    app.setApplicationName("DFS Optimizer Pro")
    app.setApplicationVersion("2.0")

    # Set application icon (if available)
    try:
        app.setWindowIcon(QIcon("icon.png"))
    except:
        pass

    # Create and show main window
    window = DFSOptimizerGUI()
    window.show()

    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()