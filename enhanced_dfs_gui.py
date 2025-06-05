#!/usr/bin/env python3
"""
ENHANCED DFS OPTIMIZER GUI
==========================
Modern, non-blocking GUI for DFS optimization
"""

import sys
import os
import csv
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from io import StringIO

# Import PyQt5
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
except ImportError:
    print("❌ PyQt5 not available. Install with: pip install PyQt5")
    sys.exit(1)

# Import bankroll management
try:
    from bankroll_management import BankrollManagementWidget, update_clean_gui_with_bankroll

    BANKROLL_AVAILABLE = True
except ImportError:
    print("⚠️ Bankroll management not found. Some features will be limited.")
    BANKROLL_AVAILABLE = False

# Import core optimizer
try:
    from bulletproof_dfs_core import BulletproofDFSCore

    CORE_AVAILABLE = True
except ImportError:
    print("⚠️ Core optimizer not found. Some features will be limited.")
    CORE_AVAILABLE = False


    # Mock class for testing
    class BulletproofDFSCore:
        def __init__(self):
            self.players = []
            self.optimization_mode = 'bulletproof'
            self.contest_type = 'classic'

        def load_draftkings_csv(self, path):
            return True

        def set_optimization_mode(self, mode):
            self.optimization_mode = mode

        def apply_manual_selection(self, text):
            return 5

        def detect_confirmed_players(self):
            return 10

        def optimize_lineup_with_mode(self):
            from types import SimpleNamespace
            mock_players = []
            positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'P']
            for i in range(10):
                player = SimpleNamespace(
                    name=f"Player {i + 1}",
                    primary_position=positions[i],
                    team="NYY",
                    salary=5000 - i * 100,
                    enhanced_score=10.5 + i * 0.5,
                    is_confirmed=True
                )
                mock_players.append(player)
            return mock_players, 105.5

        def generate_contest_lineups(self, count, contest_type):
            lineups = []
            for i in range(count):
                lineup, score = self.optimize_lineup_with_mode()
                lineups.append({
                    'lineup_id': i + 1,
                    'lineup': lineup,
                    'total_score': score + i,
                    'total_salary': 48000 + i * 100,
                    'contest_type': contest_type
                })
            return lineups


class ConsoleRedirect:
    """Redirect console output to GUI widget"""

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.terminal = sys.stdout

    def write(self, message):
        if message.strip():  # Only write non-empty messages
            # Append to GUI console
            self.text_widget.append(message.strip())
            # Force GUI update
            QApplication.processEvents()

        # Also write to terminal for debugging
        if self.terminal:
            self.terminal.write(message)

    def flush(self):
        if self.terminal:
            self.terminal.flush()


class OptimizationWorker(QThread):
    """Worker thread for running optimization without blocking GUI"""

    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, core, settings):
        super().__init__()
        self.core = core
        self.settings = settings
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        """Run optimization in separate thread"""
        try:
            # Apply settings
            self.progress.emit("🔧 Applying optimization settings...")
            self.core.set_optimization_mode(self.settings['mode'])

            # Apply manual selections if any
            if self.settings['manual_players'] and self._is_running:
                self.progress.emit("🎯 Processing manual player selections...")
                count = self.core.apply_manual_selection(self.settings['manual_players'])
                self.progress.emit(f"✅ Applied {count} manual selections")

            # Detect confirmations if not manual-only mode
            if self.settings['mode'] != 'manual_only' and self._is_running:
                self.progress.emit("🔍 Detecting confirmed players...")
                confirmed = self.core.detect_confirmed_players()
                self.progress.emit(f"✅ Found {confirmed} confirmed players")

            if not self._is_running:
                return

            # Generate lineups
            if self.settings['multi_lineup']:
                self.progress.emit(f"🎰 Generating {self.settings['lineup_count']} lineups...")
                lineups = self.core.generate_contest_lineups(
                    self.settings['lineup_count'],
                    self.settings['contest_type']
                )
                if lineups:
                    self.finished.emit(lineups)
                else:
                    self.error.emit("Failed to generate lineups")
            else:
                self.progress.emit("🚀 Optimizing single lineup...")
                lineup, score = self.core.optimize_lineup_with_mode()

                if lineup:
                    # Wrap single lineup in expected format
                    lineup_data = [{
                        'lineup_id': 1,
                        'lineup': lineup,
                        'total_score': score,
                        'total_salary': sum(p.salary for p in lineup),
                        'contest_type': self.settings['contest_type']
                    }]
                    self.finished.emit(lineup_data)
                else:
                    self.error.emit("No valid lineup found")

        except Exception as e:
            self.error.emit(f"Optimization failed: {str(e)}")


class DFSOptimizerGUI(QMainWindow):
    """Main GUI window with non-blocking optimization"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DFS Optimizer Pro")
        self.setMinimumSize(1200, 800)

        # Initialize data
        self.dk_file = ""
        self.dff_file = ""
        self.core = None
        self.last_results = []
        self.worker = None
        self.console_redirect = None

        # Setup UI
        self.setup_ui()
        self.apply_theme()
        self.load_settings()
        self.auto_detect_files()

        # Setup console redirect
        self.setup_console_redirect()

    def setup_console_redirect(self):
        """Setup console output redirection"""
        self.console_redirect = ConsoleRedirect(self.console)
        sys.stdout = self.console_redirect

    def setup_ui(self):
        """Create UI elements"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        self.create_header(main_layout)

        # Content area with splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Control tabs
        self.control_tabs = QTabWidget()
        self.control_tabs.addTab(self.create_data_tab(), "📁 Data")
        self.control_tabs.addTab(self.create_settings_tab(), "⚙️ Settings")
        self.control_tabs.addTab(self.create_lineup_tab(), "🎯 Lineups")

        left_layout.addWidget(self.control_tabs)

        # Optimize button
        self.optimize_btn = QPushButton("🚀 Generate Optimal Lineup")
        self.optimize_btn.setMinimumHeight(60)
        self.optimize_btn.clicked.connect(self.run_optimization)
        self.optimize_btn.setEnabled(False)  # Start disabled until CSV loaded
        left_layout.addWidget(self.optimize_btn)

        # Right panel - Results
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Results tabs
        self.results_tabs = QTabWidget()
        self.results_tabs.addTab(self.create_console_tab(), "📋 Console")
        self.results_tabs.addTab(self.create_results_tab(), "📊 Results")
        self.results_tabs.addTab(self.create_analytics_tab(), "📈 Analytics")

        right_layout.addWidget(self.results_tabs)

        # Add to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 800])

        main_layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Load a DraftKings CSV to begin")

        # Progress bar in status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def create_header(self, layout):
        """Create application header"""
        header = QFrame()
        header.setMaximumHeight(80)
        header_layout = QHBoxLayout(header)

        # Logo/Title
        title_layout = QVBoxLayout()
        title = QLabel("DFS Optimizer Pro")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e40af;")
        subtitle = QLabel("Advanced Daily Fantasy Sports Lineup Optimization")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        # Quick actions
        actions_layout = QHBoxLayout()

        # Quick generate buttons
        for label, count, contest in [("5 Cash", 5, "cash"), ("20 GPP", 20, "gpp"), ("150 Max", 150, "gpp")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, c=count, t=contest: self.quick_generate(c, t))
            actions_layout.addWidget(btn)

        header_layout.addLayout(actions_layout)

        layout.addWidget(header)

    def create_data_tab(self):
        """Create data input tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # DraftKings file
        dk_group = QGroupBox("DraftKings CSV")
        dk_layout = QVBoxLayout(dk_group)

        self.dk_label = QLabel("No file selected")
        self.dk_label.setStyleSheet("""
            QLabel {
                padding: 20px;
                border: 2px dashed #cbd5e1;
                border-radius: 8px;
                background-color: #f8fafc;
            }
        """)
        self.dk_label.setAlignment(Qt.AlignCenter)

        dk_btn_layout = QHBoxLayout()
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.select_dk_file)

        download_btn = QPushButton("Download Latest")
        download_btn.clicked.connect(self.download_dk_file)

        dk_btn_layout.addWidget(browse_btn)
        dk_btn_layout.addWidget(download_btn)

        dk_layout.addWidget(self.dk_label)
        dk_layout.addLayout(dk_btn_layout)

        layout.addWidget(dk_group)

        # DFF file (optional)
        dff_group = QGroupBox("DFF Rankings (Optional)")
        dff_layout = QVBoxLayout(dff_group)

        self.dff_label = QLabel("No file selected")
        self.dff_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                border: 2px dashed #cbd5e1;
                border-radius: 8px;
                background-color: #f8fafc;
            }
        """)
        self.dff_label.setAlignment(Qt.AlignCenter)

        dff_btn = QPushButton("Browse DFF")
        dff_btn.clicked.connect(self.select_dff_file)

        dff_layout.addWidget(self.dff_label)
        dff_layout.addWidget(dff_btn)

        layout.addWidget(dff_group)

        # Manual players
        manual_group = QGroupBox("Manual Player Selection")
        manual_layout = QVBoxLayout(manual_group)

        self.manual_input = QTextEdit()
        self.manual_input.setMaximumHeight(100)
        self.manual_input.setPlaceholderText("Enter player names separated by commas...")

        manual_btn_layout = QHBoxLayout()

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.manual_input.clear)

        sample_btn = QPushButton("Load Sample")
        sample_btn.clicked.connect(self.load_sample_players)

        manual_btn_layout.addWidget(clear_btn)
        manual_btn_layout.addWidget(sample_btn)

        manual_layout.addWidget(self.manual_input)
        manual_layout.addLayout(manual_btn_layout)

        layout.addWidget(manual_group)

        # Test data
        test_btn = QPushButton("🧪 Create Test Data")
        test_btn.clicked.connect(self.create_test_data)
        layout.addWidget(test_btn)

        layout.addStretch()

        return widget

    def create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Contest settings
        contest_group = QGroupBox("Contest Settings")
        contest_layout = QFormLayout(contest_group)

        self.contest_type = QComboBox()
        self.contest_type.addItems(["Classic", "Showdown", "Single Entry", "3-Max", "5-Max"])
        contest_layout.addRow("Contest Type:", self.contest_type)

        self.slate_type = QComboBox()
        self.slate_type.addItems(["Main", "Early", "Afternoon", "Night", "All Day"])
        contest_layout.addRow("Slate:", self.slate_type)

        layout.addWidget(contest_group)

        # Optimization settings
        opt_group = QGroupBox("Optimization Settings")
        opt_layout = QFormLayout(opt_group)

        self.opt_mode = QComboBox()
        self.opt_mode.addItems([
            "Bulletproof (Confirmed + Manual)",
            "Manual Only",
            "Confirmed Only",
            "All Players"
        ])
        opt_layout.addRow("Mode:", self.opt_mode)

        self.min_salary = QSpinBox()
        self.min_salary.setRange(45000, 50000)
        self.min_salary.setValue(48000)
        self.min_salary.setSingleStep(500)
        opt_layout.addRow("Min Salary:", self.min_salary)

        self.max_exposure = QSpinBox()
        self.max_exposure.setRange(0, 100)
        self.max_exposure.setValue(60)
        self.max_exposure.setSuffix("%")
        opt_layout.addRow("Max Exposure:", self.max_exposure)

        layout.addWidget(opt_group)

        # Features
        features_group = QGroupBox("Data Sources")
        features_layout = QVBoxLayout(features_group)

        self.use_vegas = QCheckBox("Vegas Lines")
        self.use_vegas.setChecked(True)

        self.use_statcast = QCheckBox("Statcast Data")
        self.use_statcast.setChecked(True)

        self.use_weather = QCheckBox("Weather Data")
        self.use_weather.setChecked(True)

        self.use_trends = QCheckBox("Recent Trends")
        self.use_trends.setChecked(True)

        features_layout.addWidget(self.use_vegas)
        features_layout.addWidget(self.use_statcast)
        features_layout.addWidget(self.use_weather)
        features_layout.addWidget(self.use_trends)

        layout.addWidget(features_group)

        layout.addStretch()

        return widget

    def create_lineup_tab(self):
        """Create lineup generation tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Single vs Multi
        mode_group = QGroupBox("Generation Mode")
        mode_layout = QVBoxLayout(mode_group)

        self.single_radio = QRadioButton("Single Lineup")
        self.single_radio.setChecked(True)
        self.multi_radio = QRadioButton("Multiple Lineups")

        mode_layout.addWidget(self.single_radio)
        mode_layout.addWidget(self.multi_radio)

        layout.addWidget(mode_group)

        # Multi lineup settings
        self.multi_group = QGroupBox("Multiple Lineup Settings")
        multi_layout = QFormLayout(self.multi_group)

        self.lineup_count = QSpinBox()
        self.lineup_count.setRange(2, 150)
        self.lineup_count.setValue(20)
        multi_layout.addRow("Number of Lineups:", self.lineup_count)

        self.diversity = QSlider(Qt.Horizontal)
        self.diversity.setRange(0, 100)
        self.diversity.setValue(70)
        self.diversity_label = QLabel("70%")

        diversity_layout = QHBoxLayout()
        diversity_layout.addWidget(self.diversity)
        diversity_layout.addWidget(self.diversity_label)

        multi_layout.addRow("Diversity:", diversity_layout)

        self.allow_dupes = QCheckBox("Allow duplicate lineups")
        multi_layout.addRow("", self.allow_dupes)

        self.multi_group.setEnabled(False)
        layout.addWidget(self.multi_group)

        # Connect radio buttons
        self.single_radio.toggled.connect(lambda checked: self.multi_group.setEnabled(not checked))
        self.diversity.valueChanged.connect(lambda v: self.diversity_label.setText(f"{v}%"))

        # Presets
        presets_group = QGroupBox("Quick Presets")
        presets_layout = QGridLayout(presets_group)

        preset_buttons = [
            ("Cash Game", self.preset_cash),
            ("GPP", self.preset_gpp),
            ("Single Entry", self.preset_single),
            ("Mass Multi", self.preset_mass)
        ]

        for i, (label, func) in enumerate(preset_buttons):
            btn = QPushButton(label)
            btn.clicked.connect(func)
            presets_layout.addWidget(btn, i // 2, i % 2)

        layout.addWidget(presets_group)

        layout.addStretch()

        return widget

    def create_console_tab(self):
        """Create console output tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 10))

        # Clear button
        clear_btn = QPushButton("Clear Console")
        clear_btn.clicked.connect(self.console.clear)

        layout.addWidget(self.console)
        layout.addWidget(clear_btn)

        return widget

    def create_results_tab(self):
        """Create results display tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Summary card
        self.summary_widget = QWidget()
        self.summary_widget.setMaximumHeight(150)
        summary_layout = QHBoxLayout(self.summary_widget)

        self.score_label = self.create_stat_widget("Score", "0.0")
        self.salary_label = self.create_stat_widget("Salary", "$0")
        self.value_label = self.create_stat_widget("Value", "0.0")

        summary_layout.addWidget(self.score_label)
        summary_layout.addWidget(self.salary_label)
        summary_layout.addWidget(self.value_label)

        layout.addWidget(self.summary_widget)

        # Lineup table
        self.lineup_table = QTableWidget()
        self.lineup_table.setColumnCount(6)
        self.lineup_table.setHorizontalHeaderLabels([
            "Position", "Player", "Team", "Salary", "Projected", "Value"
        ])

        header = self.lineup_table.horizontalHeader()
        header.setStretchLastSection(True)

        layout.addWidget(self.lineup_table)

        # Export buttons
        export_layout = QHBoxLayout()

        copy_btn = QPushButton("📋 Copy Lineup")
        copy_btn.clicked.connect(self.copy_lineup)

        export_csv_btn = QPushButton("💾 Export CSV")
        export_csv_btn.clicked.connect(self.export_csv)

        export_dk_btn = QPushButton("🏈 DraftKings Format")
        export_dk_btn.clicked.connect(self.export_draftkings)

        export_layout.addWidget(copy_btn)
        export_layout.addWidget(export_csv_btn)
        export_layout.addWidget(export_dk_btn)

        layout.addLayout(export_layout)

        return widget

    def create_analytics_tab(self):
        """Create analytics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Add bankroll management if available
        if BANKROLL_AVAILABLE:
            self.bankroll_widget = BankrollManagementWidget(self)
            layout.addWidget(self.bankroll_widget)
        else:
            # Player exposure (for multi-lineup)
            exposure_group = QGroupBox("Player Exposure")
            exposure_layout = QVBoxLayout(exposure_group)

            self.exposure_table = QTableWidget()
            self.exposure_table.setColumnCount(4)
            self.exposure_table.setHorizontalHeaderLabels([
                "Player", "Count", "Exposure %", "Avg Score"
            ])

            exposure_layout.addWidget(self.exposure_table)
            layout.addWidget(exposure_group)

            # Stack analysis
            stack_group = QGroupBox("Stack Analysis")
            stack_layout = QVBoxLayout(stack_group)

            self.stack_list = QListWidget()
            stack_layout.addWidget(self.stack_list)

            layout.addWidget(stack_group)

        return widget

    def create_stat_widget(self, label, value):
        """Create a stat display widget"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f1f5f9;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 12px; color: #64748b;")
        label_widget.setAlignment(Qt.AlignCenter)

        value_widget = QLabel(value)
        value_widget.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e293b;")
        value_widget.setAlignment(Qt.AlignCenter)
        value_widget.setObjectName(f"{label.lower()}_value")

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)

        return widget

    def apply_theme(self):
        """Apply modern theme to application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px;
            }

            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2563eb;
            }

            QPushButton:pressed {
                background-color: #1d4ed8;
            }

            QPushButton:disabled {
                background-color: #94a3b8;
            }

            QComboBox, QSpinBox {
                padding: 6px;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                background-color: white;
            }

            QComboBox:focus, QSpinBox:focus {
                border-color: #3b82f6;
            }

            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QTableWidget::item:selected {
                background-color: #dbeafe;
                color: #1e40af;
            }

            QTextEdit {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px;
            }

            QTabWidget::pane {
                border: 2px solid #e2e8f0;
                background-color: white;
                border-radius: 8px;
            }

            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
                background-color: #f1f5f9;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }

            QTabBar::tab:selected {
                background-color: white;
                color: #1e40af;
                font-weight: bold;
            }

            QTabBar::tab:hover {
                background-color: #e2e8f0;
            }

            QCheckBox, QRadioButton {
                spacing: 8px;
            }

            QCheckBox::indicator, QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }

            QSlider::groove:horizontal {
                height: 6px;
                background: #e2e8f0;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #3b82f6;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }

            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #e2e8f0;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 4px;
            }
        """)

        # Special styling for the optimize button
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }

            QPushButton:hover {
                background-color: #059669;
            }

            QPushButton:pressed {
                background-color: #047857;
            }

            QPushButton:disabled {
                background-color: #94a3b8;
            }
        """)

    def load_settings(self):
        """Load saved settings"""
        settings = QSettings("DFSOptimizer", "Settings")

        # Restore window geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def save_settings(self):
        """Save current settings"""
        settings = QSettings("DFSOptimizer", "Settings")
        settings.setValue("geometry", self.saveGeometry())

    def closeEvent(self, event):
        """Handle close event"""
        # Stop any running optimization
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self.save_settings()
        event.accept()

    def auto_detect_files(self):
        """Auto-detect CSV files"""
        import glob

        # Look for DraftKings files
        for pattern in ["*DKSalaries*.csv", "*draftkings*.csv"]:
            files = glob.glob(pattern)
            if files:
                # Use most recent
                files.sort(key=os.path.getmtime, reverse=True)
                self.set_dk_file(files[0])
                break

    def select_dk_file(self):
        """Select DraftKings CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DraftKings CSV", "", "CSV Files (*.csv)"
        )
        if file_path:
            self.set_dk_file(file_path)

    def set_dk_file(self, path):
        """Set DraftKings file and properly enable optimize button"""
        self.dk_file = path
        filename = os.path.basename(path)

        # Update label to show file is loaded
        self.dk_label.setText(f"✅ {filename}")
        self.dk_label.setStyleSheet("""
            QLabel {
                padding: 20px;
                border: 2px solid #10b981;
                border-radius: 8px;
                background-color: #d1fae5;
                color: #065f46;
                font-weight: bold;
            }
        """)

        # Initialize core and load CSV
        if CORE_AVAILABLE:
            try:
                self.core = BulletproofDFSCore()

                # Detect contest type from filename
                if 'showdown' in filename.lower() or 'captain' in filename.lower():
                    self.core.contest_type = 'showdown'
                    self.console.append("🎯 Detected SHOWDOWN contest")
                else:
                    self.core.contest_type = 'classic'

                # Load the CSV
                if self.core.load_draftkings_csv(path):
                    # Enable the optimize button
                    self.optimize_btn.setEnabled(True)
                    self.status_bar.showMessage(f"✅ Loaded {filename} - Ready to optimize!")
                    self.console.append(f"✅ Successfully loaded {len(self.core.players)} players")
                else:
                    self.optimize_btn.setEnabled(False)
                    self.status_bar.showMessage(f"❌ Failed to load {filename}")
                    self.console.append("❌ Error loading CSV file")

            except Exception as e:
                self.optimize_btn.setEnabled(False)
                self.status_bar.showMessage(f"❌ Error: {str(e)}")
                self.console.append(f"❌ Error: {str(e)}")
        else:
            # Mock mode - still enable button for testing
            self.core = BulletproofDFSCore()
            self.optimize_btn.setEnabled(True)
            self.status_bar.showMessage(f"✅ Loaded {filename} (Test mode)")

    def select_dff_file(self):
        """Select DFF file with auto-detection"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DFF Rankings", "", "CSV Files (*.csv)"
        )

        if file_path:
            filename = os.path.basename(file_path)

            # Detect type
            if 'showdown' in filename.lower() or 'sd' in filename.lower():
                self.dff_showdown_file = file_path
                label_text = f"🎰 Showdown: {filename}"
            else:
                self.dff_classic_file = file_path
                label_text = f"🏈 Classic: {filename}"

            self.dff_label.setText(label_text)
            self.dff_label.setStyleSheet("""
                QLabel {
                    padding: 15px;
                    border: 2px solid #f59e0b;
                    border-radius: 8px;
                    background-color: #fef3c7;
                    color: #92400e;
                    font-weight: bold;
                }
            """)

            # Apply to core if available
            if self.core:
                self.core.detect_and_load_dff_files(file_path)

    def auto_detect_files(self):
        """Auto-detect both DK and DFF files"""
        import glob

        # Look for DraftKings files
        dk_patterns = ["*DKSalaries*.csv", "*draftkings*.csv"]
        for pattern in dk_patterns:
            files = glob.glob(pattern)
            if files:
                files.sort(key=os.path.getmtime, reverse=True)
                self.set_dk_file(files[0])
                break

        # Look for DFF files
        dff_files = glob.glob("DFF_MLB_*.csv")
        for file in dff_files:
            if self.core:
                self.core.detect_and_load_dff_files(file)

    def download_dk_file(self):
        """Download latest DraftKings CSV"""
        QMessageBox.information(
            self, "Download",
            "This feature would download the latest DraftKings CSV.\n"
            "For now, please download manually from DraftKings."
        )

    def load_sample_players(self):
        """Load sample player names"""
        sample = "Shohei Ohtani, Mike Trout, Aaron Judge, Mookie Betts, Ronald Acuna Jr."
        self.manual_input.setPlainText(sample)

    def create_test_data(self):
        """Create test CSV data"""
        test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)

        # Write test data
        writer = csv.writer(test_file)
        writer.writerow(['Position', 'Name', 'Name', 'ID', 'Roster Position',
                         'Salary', 'Game Info', 'TeamAbbrev', 'AvgPointsPerGame'])

        test_players = [
            ['P', 'Gerrit Cole', 'Gerrit Cole', '1', 'P', '10000', 'NYY@BOS', 'NYY', '18.5'],
            ['P', 'Shane Bieber', 'Shane Bieber', '2', 'P', '9500', 'CLE@MIN', 'CLE', '17.2'],
            ['C', 'Will Smith', 'Will Smith', '3', 'C', '5000', 'LAD@SD', 'LAD', '10.2'],
            ['1B', 'Freddie Freeman', 'Freddie Freeman', '4', '1B', '5500', 'LAD@SD', 'LAD', '11.5'],
            ['2B', 'Jose Altuve', 'Jose Altuve', '5', '2B', '5200', 'HOU@TEX', 'HOU', '10.8'],
            ['3B', 'Manny Machado', 'Manny Machado', '6', '3B', '5300', 'SD@LAD', 'SD', '11.0'],
            ['SS', 'Trea Turner', 'Trea Turner', '7', 'SS', '5100', 'PHI@NYM', 'PHI', '10.5'],
            ['OF', 'Aaron Judge', 'Aaron Judge', '8', 'OF', '6500', 'NYY@BOS', 'NYY', '13.8'],
            ['OF', 'Mike Trout', 'Mike Trout', '9', 'OF', '6000', 'LAA@SEA', 'LAA', '12.5'],
            ['OF', 'Mookie Betts', 'Mookie Betts', '10', 'OF', '5800', 'LAD@SD', 'LAD', '12.0'],
        ]

        for player in test_players:
            writer.writerow(player)

        test_file.close()
        self.set_dk_file(test_file.name)

        QMessageBox.information(self, "Test Data", "Test data created and loaded!")

    def preset_cash(self):
        """Cash game preset"""
        self.single_radio.setChecked(True)
        self.opt_mode.setCurrentIndex(2)  # Confirmed only
        self.min_salary.setValue(49000)

    def preset_gpp(self):
        """GPP preset"""
        self.multi_radio.setChecked(True)
        self.lineup_count.setValue(20)
        self.diversity.setValue(80)
        self.opt_mode.setCurrentIndex(0)  # Bulletproof

    def preset_single(self):
        """Single entry preset"""
        self.single_radio.setChecked(True)
        self.opt_mode.setCurrentIndex(0)  # Bulletproof
        self.min_salary.setValue(48500)

    def preset_mass(self):
        """Mass multi-entry preset"""
        self.multi_radio.setChecked(True)
        self.lineup_count.setValue(150)
        self.diversity.setValue(90)
        self.allow_dupes.setChecked(False)

    def quick_generate(self, count, contest_type):
        """Quick lineup generation"""
        if not self.dk_file:
            QMessageBox.warning(self, "No Data", "Please load a DraftKings CSV first")
            return

        self.multi_radio.setChecked(True)
        self.lineup_count.setValue(count)

        # Set contest type
        if contest_type == "cash":
            self.contest_type.setCurrentIndex(0)
            self.opt_mode.setCurrentIndex(2)  # Confirmed only
        else:
            self.contest_type.setCurrentIndex(0)
            self.opt_mode.setCurrentIndex(0)  # Bulletproof

        self.run_optimization()

    def run_optimization(self):
        """Run optimization with contest awareness"""
        if not self.dk_file:
            QMessageBox.warning(self, "No Data", "Please load a DraftKings CSV first")
            return

        # Check if already running
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Already Running", "Optimization is already in progress")
            return

        # Clear previous results
        self.console.clear()
        self.lineup_table.setRowCount(0)

        # Map contest types from GUI to optimizer
        contest_type_mapping = {
            "Classic": "classic",
            "Showdown": "showdown",
            "Single Entry": "single",
            "3-Max": "gpp",
            "5-Max": "gpp",
            "Cash - Double Up (Top 45% win)": "cash"
        }

        # Get selected contest type
        selected_contest = self.contest_type.currentText()
        contest_type = contest_type_mapping.get(selected_contest, "classic")

        # Prepare settings
        settings = {
            'mode': ['bulletproof', 'manual_only', 'confirmed_only', 'all'][self.opt_mode.currentIndex()],
            'contest_type': contest_type,
            'manual_players': self.manual_input.toPlainText().strip(),
            'multi_lineup': self.multi_radio.isChecked(),
            'lineup_count': self.lineup_count.value() if self.multi_radio.isChecked() else 1,
            'min_salary': self.min_salary.value(),
            'max_exposure': self.max_exposure.value() / 100.0,
            'diversity': self.diversity.value() / 100.0
        }

        # Set contest type for optimization
        if self.core:
            self.core.optimization_contest_type = contest_type

            # Show what adjustments will be applied
            self.console.append(f"🎯 Contest Type: {selected_contest}")
            self.console.append(f"📊 Optimization Mode: {settings['mode']}")

            if contest_type == "gpp":
                self.console.append("   ⚡ GPP Mode: Boosting high-ceiling players")
            elif contest_type == "cash":
                self.console.append("   🛡️ Cash Mode: Favoring confirmed, consistent players")
            elif contest_type == "single":
                self.console.append("   🎯 Single Entry: Balanced approach")

        # Update UI
        self.optimize_btn.setEnabled(False)
        self.optimize_btn.setText("🔄 Optimizing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        # Create and start worker thread
        self.worker = OptimizationWorker(self.core, settings)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_optimization_finished)
        self.worker.error.connect(self.on_optimization_error)
        self.worker.start()

    def on_progress(self, message):
        """Handle progress updates from worker thread"""
        self.console.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.status_bar.showMessage(message)

    def on_optimization_finished(self, results):
        """Handle successful optimization"""
        # Reset UI
        self.optimize_btn.setEnabled(True)
        self.optimize_btn.setText("🚀 Generate Optimal Lineup")
        self.progress_bar.setVisible(False)

        # Store results
        self.last_results = results

        if not results:
            self.console.append("❌ No valid lineups generated")
            return

        self.console.append(f"\n✅ Generated {len(results)} lineup(s) successfully!")

        # Display results
        if len(results) == 1:
            self.display_single_result(results[0])
        else:
            self.display_multi_results(results)

        # Switch to results tab
        self.results_tabs.setCurrentIndex(1)

        # Update status
        avg_score = sum(r['total_score'] for r in results) / len(results)
        self.status_bar.showMessage(
            f"✅ Generated {len(results)} lineup(s) - Average score: {avg_score:.1f}"
        )

    def on_optimization_error(self, error_msg):
        """Handle optimization error"""
        # Reset UI
        self.optimize_btn.setEnabled(True)
        self.optimize_btn.setText("🚀 Generate Optimal Lineup")
        self.progress_bar.setVisible(False)

        # Show error
        self.console.append(f"\n❌ ERROR: {error_msg}")
        self.status_bar.showMessage("Optimization failed")

        QMessageBox.critical(self, "Optimization Failed", error_msg)

    def display_single_result(self, result):
        """Display single lineup result"""
        lineup = result['lineup']

        # Update summary
        score = result['total_score']
        salary = result['total_salary']
        value = score / (salary / 1000) if salary > 0 else 0

        self.score_label.findChild(QLabel, "score_value").setText(f"{score:.1f}")
        self.salary_label.findChild(QLabel, "salary_value").setText(f"${salary:,}")
        self.value_label.findChild(QLabel, "value_value").setText(f"{value:.2f}")

        # Update table
        self.lineup_table.setRowCount(len(lineup))

        # Update table
        self.lineup_table.setRowCount(len(lineup))

        for i, player in enumerate(lineup):
            # Position with flex indicator
            pos_display = player.get_position_display() if hasattr(player,
                                                                   'get_position_display') else player.primary_position
            pos_item = QTableWidgetItem(pos_display)
            pos_item.setTextAlignment(Qt.AlignCenter)

            # Add tooltip showing all eligible positions
            if hasattr(player, 'positions') and len(player.positions) > 1:
                pos_item.setToolTip(f"Eligible: {'/'.join(player.positions)}")
                # Bold if using flex position
                if hasattr(player, 'is_using_flex_position') and player.is_using_flex_position():
                    font = pos_item.font()
                    font.setBold(True)
                    pos_item.setFont(font)

            self.lineup_table.setItem(i, 0, pos_item)

            # Salary
            salary_item = QTableWidgetItem(f"${player.salary:,}")
            salary_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lineup_table.setItem(i, 3, salary_item)

            # Projected
            proj_item = QTableWidgetItem(f"{player.enhanced_score:.1f}")
            proj_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lineup_table.setItem(i, 4, proj_item)

            # Value
            player_value = player.enhanced_score / (player.salary / 1000) if player.salary > 0 else 0
            value_item = QTableWidgetItem(f"{player_value:.2f}")
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lineup_table.setItem(i, 5, value_item)

            # Color code by position
            if player.primary_position == 'P':
                for j in range(6):
                    self.lineup_table.item(i, j).setBackground(QColor(219, 234, 254))
            elif player.primary_position in ['C', '1B', '2B', '3B', 'SS']:
                for j in range(6):
                    self.lineup_table.item(i, j).setBackground(QColor(254, 215, 215))
            else:  # OF
                for j in range(6):
                    self.lineup_table.item(i, j).setBackground(QColor(209, 250, 229))

    def display_multi_results(self, results):
        """Display multiple lineup results"""
        # Show summary dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{len(results)} Lineups Generated")
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout(dialog)

        # Summary stats
        scores = [r['total_score'] for r in results]
        salaries = [r['total_salary'] for r in results]

        summary = QLabel(f"""
            <h3>Lineup Generation Summary</h3>
            <p><b>Lineups:</b> {len(results)}</p>
            <p><b>Score Range:</b> {min(scores):.1f} - {max(scores):.1f}</p>
            <p><b>Average Score:</b> {sum(scores) / len(scores):.1f}</p>
            <p><b>Salary Range:</b> ${min(salaries):,} - ${max(salaries):,}</p>
        """)
        layout.addWidget(summary)

        # Lineup list
        lineup_list = QListWidget()
        for i, result in enumerate(results):
            item_text = f"Lineup {i + 1}: {result['total_score']:.1f} pts, ${result['total_salary']:,}"
            lineup_list.addItem(item_text)

        lineup_list.itemDoubleClicked.connect(
            lambda item: self.display_single_result(results[lineup_list.row(item)])
        )
        layout.addWidget(lineup_list)

        # Buttons
        button_layout = QHBoxLayout()

        export_btn = QPushButton("Export All")
        export_btn.clicked.connect(lambda: self.export_multi_lineups(results))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)

        button_layout.addWidget(export_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        dialog.exec_()

        # Update exposure analysis
        self.update_exposure_analysis(results)

    def update_exposure_analysis(self, results):
        """Update player exposure analysis"""
        if not hasattr(self, 'exposure_table'):
            return

        player_usage = {}

        for result in results:
            for player in result['lineup']:
                key = player.name
                if key not in player_usage:
                    player_usage[key] = {
                        'count': 0,
                        'total_score': 0,
                        'salary': player.salary
                    }
                player_usage[key]['count'] += 1
                player_usage[key]['total_score'] += player.enhanced_score

        # Sort by usage
        sorted_players = sorted(
            player_usage.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )

        # Update table
        self.exposure_table.setRowCount(len(sorted_players))

        for i, (name, data) in enumerate(sorted_players):
            self.exposure_table.setItem(i, 0, QTableWidgetItem(name))
            self.exposure_table.setItem(i, 1, QTableWidgetItem(str(data['count'])))

            exposure = (data['count'] / len(results)) * 100
            exposure_item = QTableWidgetItem(f"{exposure:.1f}%")

            # Color code exposure
            if exposure > 60:
                exposure_item.setBackground(QColor(254, 202, 202))
            elif exposure > 40:
                exposure_item.setBackground(QColor(254, 240, 138))
            else:
                exposure_item.setBackground(QColor(187, 247, 208))

            self.exposure_table.setItem(i, 2, exposure_item)

            avg_score = data['total_score'] / data['count']
            self.exposure_table.setItem(i, 3, QTableWidgetItem(f"{avg_score:.1f}"))

    def copy_lineup(self):
        """Copy lineup to clipboard"""
        if not self.last_results:
            return

        lineup = self.last_results[0]['lineup']
        text = ", ".join([p.name for p in lineup])

        QApplication.clipboard().setText(text)
        self.status_bar.showMessage("Lineup copied to clipboard!", 3000)

    def export_csv(self):
        """Export lineup(s) to CSV"""
        if not self.last_results:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Lineups", "lineups.csv", "CSV Files (*.csv)"
        )

        if file_path:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Lineup', 'Position', 'Player', 'Team', 'Salary', 'Projection'])

                for i, result in enumerate(self.last_results):
                    for player in result['lineup']:
                        writer.writerow([
                            i + 1,
                            player.primary_position,
                            player.name,
                            player.team,
                            player.salary,
                            player.enhanced_score
                        ])

            QMessageBox.information(self, "Export Complete", f"Exported to {file_path}")

    def export_draftkings(self):
        """Export in DraftKings upload format"""
        if not self.last_results:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export for DraftKings", "dk_upload.csv", "CSV Files (*.csv)"
        )

        if file_path:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)

                # DraftKings format - just player names in position order
                for result in self.last_results:
                    row = []
                    positions = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']

                    lineup_by_pos = {}
                    for player in result['lineup']:
                        pos = player.primary_position
                        if pos not in lineup_by_pos:
                            lineup_by_pos[pos] = []
                        lineup_by_pos[pos].append(player.name)

                    for pos in positions:
                        if pos in lineup_by_pos and lineup_by_pos[pos]:
                            row.append(lineup_by_pos[pos].pop(0))
                        else:
                            row.append("")

                    writer.writerow(row)

            QMessageBox.information(self, "Export Complete",
                                    f"Exported {len(self.last_results)} lineup(s) for DraftKings upload")

    def export_multi_lineups(self, results):
        """Export multiple lineups"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export All Lineups", "all_lineups.csv", "CSV Files (*.csv)"
        )

        if file_path:
            self.last_results = results
            self.export_csv()


# Update with bankroll management if available
if BANKROLL_AVAILABLE:
    update_clean_gui_with_bankroll(DFSOptimizerGUI)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("DFS Optimizer Pro")
    app.setOrganizationName("DFS Tools")

    # Set application icon if available
    if os.path.exists("icon.png"):
        app.setWindowIcon(QIcon("icon.png"))

    # Create and show main window
    window = DFSOptimizerGUI()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())