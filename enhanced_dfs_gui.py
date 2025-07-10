#!/usr/bin/env python3
"""
CLEAN DFS OPTIMIZER GUI - FIXED VERSION
=======================================
Fixed layout errors and improved stability
"""

import sys
import os
import csv
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import tempfile

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QTextEdit, QTableWidget, QTableWidgetItem,
        QGroupBox, QComboBox, QSpinBox, QCheckBox, QRadioButton,
        QSlider, QTabWidget, QDialog, QFileDialog, QMessageBox,
        QListWidget, QFrame, QSplitter, QStatusBar, QProgressBar,
        QFormLayout, QGridLayout, QListWidgetItem, QHeaderView,
        QAbstractItemView, QSizePolicy, QPlainTextEdit
    )
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
except ImportError:
    print("❌ PyQt5 not installed. Install with: pip install PyQt5")
    sys.exit(1)

# Try to import optimizer components
try:
    from bulletproof_dfs_core import BulletproofDFSCore, AdvancedPlayer

    CORE_AVAILABLE = True
except ImportError:
    print("⚠️ Core optimizer not found. Running in demo mode.")
    CORE_AVAILABLE = False

    # Import configuration system
    try:
        from dfs_config import dfs_config

        CONFIG_AVAILABLE = True
    except ImportError:
        CONFIG_AVAILABLE = False
        print("⚠️ Configuration system not available")

    # Import progress tracker
    try:
        from progress_tracker import ProgressTracker, MultiStageProgress

        PROGRESS_AVAILABLE = True
    except ImportError:
        PROGRESS_AVAILABLE = False
        print("⚠️ Progress tracking not available")


    # Mock classes for testing
    class AdvancedPlayer:
        def __init__(self, name="", position="", team="", salary=0, projection=0):
            self.name = name
            self.primary_position = position
            self.positions = [position]
            self.team = team
            self.salary = salary
            self.projection = projection
            self.enhanced_score = projection
            self.assigned_position = None


    class BulletproofDFSCore:
        def __init__(self):
            self.players = []
            self.contest_type = 'classic'
            self.optimization_mode = 'bulletproof'
            self.salary_cap = 50000

        def load_draftkings_csv(self, path):
            filename = os.path.basename(path).lower()
            self.contest_type = 'showdown' if 'showdown' in filename else 'classic'
            self.players = self._generate_classic_players() if self.contest_type == 'classic' else self._generate_showdown_players()
            return True

        def _generate_classic_players(self):
            players = []
            positions = [
                ('P', 40, 5000), ('C', 25, 3000), ('1B', 30, 3500),
                ('2B', 30, 3500), ('3B', 30, 3500), ('SS', 30, 3500),
                ('OF', 60, 4000)
            ]

            for pos, count, base_sal in positions:
                for i in range(count):
                    p = AdvancedPlayer(
                        f"{pos}_Player{i + 1}", pos,
                        ["LAD", "NYY", "HOU", "BOS", "ATL"][i % 5],
                        base_sal + i * 150, 10 + i * 0.3
                    )
                    if i % 3 == 0 and pos in ['1B', '2B']:
                        p.positions = [pos, '3B' if pos == '1B' else 'SS']
                    players.append(p)
            return players

        def _generate_showdown_players(self):
            players = []
            for team in ["NYY", "BOS"]:
                for i in range(15):
                    p = AdvancedPlayer(
                        f"{team}_Player{i + 1}", "UTIL", team,
                        3000 + i * 500, 8 + i * 0.5
                    )
                    p.positions = ["CPT", "UTIL"]
                    players.append(p)
            return players

        def set_optimization_mode(self, mode):
            self.optimization_mode = mode

        def apply_manual_selection(self, text):
            names = [n.strip() for n in text.split(',') if n.strip()]
            return len(names)

        def detect_confirmed_players(self):
            return min(20, len(self.players) // 4)

        def get_eligible_players_by_mode(self):
            if self.optimization_mode == 'all':
                return self.players
            elif self.optimization_mode == 'manual_only':
                return self.players[:int(len(self.players) * 0.3)]
            else:
                return self.players[:int(len(self.players) * 0.5)]

        def optimize_lineup_with_mode(self):
            eligible = self.get_eligible_players_by_mode()

            if self.contest_type == 'showdown':
                if len(eligible) < 6:
                    return [], 0
                lineup = eligible[:6]
                lineup[0].assigned_position = "CPT"
                for p in lineup[1:]:
                    p.assigned_position = "UTIL"
            else:
                if len(eligible) < 10:
                    return [], 0
                lineup = []
                positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

                for pos, count in positions_needed.items():
                    added = 0
                    for player in eligible:
                        if added < count and pos in player.positions and player not in lineup:
                            player.assigned_position = pos
                            lineup.append(player)
                            added += 1

                while len(lineup) < 10 and eligible:
                    for p in eligible:
                        if p not in lineup:
                            lineup.append(p)
                            break

            total_score = sum(p.enhanced_score for p in lineup)
            return lineup, total_score

        def generate_contest_lineups(self, count, contest_type):
            lineups = []
            for i in range(count):
                lineup, score = self.optimize_lineup_with_mode()
                if lineup:
                    lineups.append({
                        'lineup_id': i + 1,
                        'lineup': lineup,
                        'total_score': score + (i * 0.1),
                        'total_salary': sum(p.salary for p in lineup),
                        'contest_type': contest_type
                    })
            return lineups


class ThreadSafeConsole(QPlainTextEdit):
    """Thread-safe console widget"""
    append_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setMaximumBlockCount(1000)

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 5px;
            }
        """)

        self.append_signal.connect(self._append_text)

    @pyqtSlot(str)
    def _append_text(self, text):
        self.appendPlainText(text)
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def thread_safe_append(self, text):
        self.append_signal.emit(text)


class OptimizationWorker(QThread):
    """Worker thread for optimization"""
    started = pyqtSignal()
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
        try:
            self.started.emit()

            self.progress.emit(f"Contest type: {self.core.contest_type}")
            self.progress.emit(f"Optimization mode: {self.settings['mode']}")

            self.core.set_optimization_mode(self.settings['mode'])

            # ========== REMOVED SHOWDOWN PITCHER API ==========
            # We don't need it - the confirmation system handles pitchers correctly

            if self.settings.get('manual_players'):
                self.progress.emit("Processing manual selections...")
                count = self.core.apply_manual_selection(self.settings['manual_players'])
                self.progress.emit(f"Applied {count} manual selections")

            if self.settings['mode'] != 'manual_only':
                self.progress.emit("Detecting confirmed players...")
                confirmed = self.core.detect_confirmed_players()
                self.progress.emit(f"Found {confirmed} confirmed players")

                # For showdown, show pitcher status
                if self.core.contest_type == 'showdown':
                    # Count pitchers that were identified
                    pitcher_count = sum(1 for p in self.core.players
                                        if hasattr(p, 'original_position') and p.original_position == 'P')
                    self.progress.emit(f"✅ Identified {pitcher_count} starting pitchers via MLB data")

            # ========== POSITION COVERAGE CHECK ==========
            if self.core.contest_type == 'classic':
                self.progress.emit("Checking position coverage...")
                self.core.debug_position_coverage()

                # Check current position coverage
                eligible = self.core.get_eligible_players_by_mode()
                position_counts = {}
                for player in eligible:
                    for pos in player.positions:
                        position_counts[pos] = position_counts.get(pos, 0) + 1

                # Check if we're missing key positions
                missing_positions = []
                for pos in ['1B', '2B', '3B']:
                    if position_counts.get(pos, 0) == 0:
                        missing_positions.append(pos)

                if missing_positions:
                    self.progress.emit(f"⚠️ Missing positions: {missing_positions}")
                    self.progress.emit("Fixing known player positions...")
                    self.core.fix_known_player_positions()
                    self.progress.emit("Auto-selecting top infielders...")
                    added = self.core.auto_select_top_infielders(count_per_position=2)
                    self.progress.emit(f"Added {added} infielders")

            elif self.core.contest_type == 'showdown':
                # Show final showdown status
                self.progress.emit("\n📊 Showdown player pool status:")

                eligible = self.core.get_eligible_players_by_mode()
                self.progress.emit(f"   Total eligible: {len(eligible)}")

                # Show pitcher details
                pitchers = [p for p in eligible
                            if hasattr(p, 'original_position') and p.original_position == 'P']

                if pitchers:
                    self.progress.emit(f"   ⚾ Eligible starting pitchers: {len(pitchers)}")
                    for p in pitchers:
                        self.progress.emit(f"      {p.name} ({p.team}) - ${p.salary:,} - Proj: {p.projection}")
                else:
                    self.progress.emit("   ❌ NO ELIGIBLE PITCHERS FOUND!")

                # Show position breakdown
                orig_pos_counts = {}
                for p in eligible:
                    orig = getattr(p, 'original_position', 'UTIL')
                    orig_pos_counts[orig] = orig_pos_counts.get(orig, 0) + 1
                self.progress.emit(f"   By original position: {orig_pos_counts}")
            # ========== END POSITION COVERAGE CHECK ==========

            if not self._is_running:
                return

            lineup_count = self.settings.get('lineup_count', 1)

            if lineup_count > 1:
                self.progress.emit(f"Generating {lineup_count} lineups...")
                lineups = self.core.generate_contest_lineups(lineup_count, self.core.contest_type)
            else:
                self.progress.emit("Optimizing single lineup...")
                lineup, score = self.core.optimize_lineup_with_mode()

                if lineup:
                    lineups = [{
                        'lineup_id': 1,
                        'lineup': lineup,
                        'total_score': score,
                        'total_salary': sum(p.salary for p in lineup),
                        'contest_type': self.core.contest_type
                    }]
                else:
                    lineups = []

            if lineups:
                self.finished.emit(lineups)
            else:
                self.error.emit("No valid lineups found")

        except Exception as e:
            self.error.emit(f"Optimization failed: {str(e)}\n{traceback.format_exc()}")


class DFSOptimizerGUI(QMainWindow):
    """Main application window"""

    def create_config_dialog(self):
        """Create configuration dialog"""
        if not CONFIG_AVAILABLE:
            QMessageBox.warning(self, "Not Available", "Configuration system not installed")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("DFS Optimizer Configuration")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        # Create tabs for different config sections
        tabs = QTabWidget()

        # Optimization tab
        opt_widget = QWidget()
        opt_layout = QFormLayout(opt_widget)

        # Form analysis players
        form_players_spin = QSpinBox()
        form_players_spin.setRange(0, 1000)
        form_players_spin.setSpecialValueText("All")
        form_players_spin.setValue(dfs_config.get('optimization.max_form_analysis_players') or 0)
        opt_layout.addRow("Max Form Analysis Players:", form_players_spin)

        # Batch size
        batch_spin = QSpinBox()
        batch_spin.setRange(10, 100)
        batch_spin.setValue(dfs_config.get('optimization.batch_size', 25))
        opt_layout.addRow("Batch Size:", batch_spin)

        # Parallel workers
        workers_spin = QSpinBox()
        workers_spin.setRange(1, 20)
        workers_spin.setValue(dfs_config.get('optimization.parallel_workers', 10))
        opt_layout.addRow("Parallel Workers:", workers_spin)

        tabs.addTab(opt_widget, "Optimization")

        # Data sources tab
        sources_widget = QWidget()
        sources_layout = QVBoxLayout(sources_widget)

        for source in ['statcast', 'vegas', 'recent_form', 'dff', 'batting_order']:
            enabled = QCheckBox(f"Enable {source.replace('_', ' ').title()}")
            enabled.setChecked(dfs_config.get(f'data_sources.{source}.enabled', True))
            sources_layout.addWidget(enabled)

        sources_layout.addStretch()
        tabs.addTab(sources_widget, "Data Sources")

        layout.addWidget(tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(
            lambda: self.save_config_from_dialog(dialog, form_players_spin, batch_spin, workers_spin))
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        dialog.exec_()

    def save_config_from_dialog(self, dialog, form_spin, batch_spin, workers_spin):
        """Save configuration from dialog"""
        # Update config values
        max_players = form_spin.value() if form_spin.value() > 0 else None
        dfs_config.set('optimization.max_form_analysis_players', max_players)
        dfs_config.set('optimization.batch_size', batch_spin.value())
        dfs_config.set('optimization.parallel_workers', workers_spin.value())

        # Update core if loaded
        if self.core and CONFIG_AVAILABLE:
            self.core.max_form_analysis_players = max_players
            self.core.batch_size = batch_spin.value()

        QMessageBox.information(dialog, "Success", "Configuration saved!")
        dialog.accept()

    def __init__(self):
        super().__init__()

        # Initialize attributes FIRST
        self.core = None
        self.worker = None
        self.dk_file = ""
        self.dff_file = ""
        self.last_results = []
        self.contest_type = 'classic'
        self.last_directory = ""

        # Initialize UI components that might be accessed early
        self.manual_text = None

        # Setup UI
        self.init_ui()
        self.setup_style()
        self.load_settings()

        # Auto-detect files after UI is ready
        QTimer.singleShot(100, self.auto_detect_files)

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("DFS Optimizer Pro - Clean Version")
        self.setMinimumSize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setSpacing(10)

        header = self.create_header()
        layout.addWidget(header)

        content = QSplitter(Qt.Horizontal)

        left_panel = self.create_left_panel()
        right_panel = self.create_right_panel()

        content.addWidget(left_panel)
        content.addWidget(right_panel)
        content.setSizes([450, 750])

        layout.addWidget(content)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.contest_indicator = QLabel("Contest: Unknown")
        self.contest_indicator.setStyleSheet("""
            QLabel {
                padding: 4px 8px;
                background-color: #6b7280;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        self.status_bar.addPermanentWidget(self.contest_indicator)

        self.update_status("Ready - Load a CSV file to begin")

    def create_header(self):
        """Create application header"""
        header = QFrame()
        header.setMaximumHeight(70)
        header.setFrameStyle(QFrame.Box)

        layout = QHBoxLayout(header)

        title_layout = QVBoxLayout()
        title = QLabel("DFS Optimizer Pro")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e40af;")
        subtitle = QLabel("Daily Fantasy Sports Lineup Optimization")
        subtitle.setStyleSheet("font-size: 12px; color: #6b7280;")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)

        layout.addStretch()

        actions_layout = QHBoxLayout()

        actions_layout.addWidget(QLabel("Lineups:"))
        self.quick_lineup_spin = QSpinBox()
        self.quick_lineup_spin.setRange(1, 150)
        self.quick_lineup_spin.setValue(1)
        self.quick_lineup_spin.setMaximumWidth(60)
        actions_layout.addWidget(self.quick_lineup_spin)

        for label, count in [("5 Cash", 5), ("20 GPP", 20), ("150 Max", 150)]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, c=count: self.quick_generate(c))
            actions_layout.addWidget(btn)

        layout.addLayout(actions_layout)

        return header

    def create_left_panel(self):
        """Create left control panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.tabs = QTabWidget()

        data_tab = self.create_data_tab()
        self.tabs.addTab(data_tab, "📁 Data")

        settings_tab = self.create_settings_tab()
        self.tabs.addTab(settings_tab, "⚙️ Settings")

        lineups_tab = self.create_lineups_tab()
        self.tabs.addTab(lineups_tab, "🎯 Lineups")

        layout.addWidget(self.tabs)

        self.generate_btn = QPushButton("🚀 Generate Optimal Lineup")
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.clicked.connect(self.run_optimization)
        self.generate_btn.setEnabled(False)

        layout.addWidget(self.generate_btn)

        return widget

    def create_data_tab(self):
        """Create data input tab - FIXED VERSION"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # CSV file selection
        csv_group = QGroupBox("DraftKings CSV File")
        csv_layout = QVBoxLayout(csv_group)

        self.csv_label = QLabel("No file loaded")
        self.csv_label.setMinimumHeight(60)
        self.csv_label.setAlignment(Qt.AlignCenter)
        self.csv_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #cbd5e1;
                border-radius: 8px;
                padding: 20px;
                background-color: #f8fafc;
            }
        """)

        csv_layout.addWidget(self.csv_label)

        btn_layout = QHBoxLayout()
        browse_btn = QPushButton("Browse Files")
        browse_btn.clicked.connect(self.browse_csv)

        reload_btn = QPushButton("Reload")
        reload_btn.clicked.connect(self.reload_csv)

        btn_layout.addWidget(browse_btn)
        btn_layout.addWidget(reload_btn)
        csv_layout.addLayout(btn_layout)

        layout.addWidget(csv_group)

        # DFF file (optional)
        dff_group = QGroupBox("DFF Rankings (Optional)")
        dff_layout = QVBoxLayout(dff_group)

        self.dff_label = QLabel("No file selected")
        self.dff_label.setMinimumHeight(50)
        self.dff_label.setAlignment(Qt.AlignCenter)
        self.dff_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #cbd5e1;
                border-radius: 8px;
                padding: 15px;
                background-color: #f8fafc;
            }
        """)

        dff_btn = QPushButton("Browse DFF File")
        dff_btn.clicked.connect(self.select_dff_file)

        dff_layout.addWidget(self.dff_label)
        dff_layout.addWidget(dff_btn)

        layout.addWidget(dff_group)

        # Manual player selection - FIXED
        manual_group = QGroupBox("Manual Player Selection")
        manual_layout = QVBoxLayout(manual_group)  # Create the layout!

        # Create manual text widget
        self.manual_text = QTextEdit()
        self.manual_text.setMaximumHeight(100)
        self.manual_text.setPlaceholderText("Enter player names separated by commas...")

        # Add to layout
        manual_layout.addWidget(self.manual_text)

        manual_btn_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.manual_text.clear)

        sample_btn = QPushButton("Sample Players")
        sample_btn.clicked.connect(self.load_sample_players)

        manual_btn_layout.addWidget(clear_btn)
        manual_btn_layout.addWidget(sample_btn)
        manual_layout.addLayout(manual_btn_layout)

        layout.addWidget(manual_group)

        # Test mode
        test_btn = QPushButton("🧪 Create Test Data")
        test_btn.clicked.connect(self.create_test_data)
        layout.addWidget(test_btn)

        layout.addStretch()

        return widget

    def select_dff_file(self):
        """Select DFF rankings file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select DFF Rankings CSV",
            self.last_directory,
            "CSV Files (*.csv);;All Files (*.*)"
        )

        if file_path:
            self.dff_file = file_path
            filename = os.path.basename(file_path)
            self.dff_label.setText(f"✅ {filename}")
            self.dff_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #f59e0b;
                    border-radius: 8px;
                    padding: 15px;
                    background-color: #fef3c7;
                    color: #92400e;
                    font-weight: bold;
                }
            """)

            if self.core and hasattr(self.core, 'current_dff_file'):
                self.core.current_dff_file = file_path
                self.console.thread_safe_append(f"📊 DFF file loaded: {filename}")

                # Apply DFF rankings if core is ready
                if hasattr(self.core, 'apply_dff_rankings'):
                    try:
                        self.core.apply_dff_rankings(file_path)
                        self.console.thread_safe_append("✅ DFF rankings applied")
                    except Exception as e:
                        self.console.thread_safe_append(f"⚠️ Could not apply DFF: {str(e)}")

    def create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Contest settings
        contest_group = QGroupBox("Contest Settings")
        contest_layout = QFormLayout(contest_group)

        self.contest_combo = QComboBox()
        self.contest_combo.addItems(["Auto-Detect", "Classic", "Showdown"])
        contest_layout.addRow("Contest Type:", self.contest_combo)

        self.slate_combo = QComboBox()
        self.slate_combo.addItems(["Main", "Early Only", "Afternoon", "Night", "All Day"])
        contest_layout.addRow("Slate:", self.slate_combo)

        layout.addWidget(contest_group)

        # Optimization settings
        opt_group = QGroupBox("Optimization Settings")
        opt_layout = QFormLayout(opt_group)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Bulletproof (Confirmed + Manual)",
            "Manual Only",
            "Confirmed Only",
            "All Players"
        ])
        opt_layout.addRow("Mode:", self.mode_combo)

        self.min_salary_spin = QSpinBox()
        self.min_salary_spin.setRange(45000, 50000)
        self.min_salary_spin.setValue(48000)
        self.min_salary_spin.setSingleStep(500)
        opt_layout.addRow("Min Salary:", self.min_salary_spin)

        self.max_exposure_spin = QSpinBox()
        self.max_exposure_spin.setRange(0, 100)
        self.max_exposure_spin.setValue(60)
        self.max_exposure_spin.setSuffix("%")
        opt_layout.addRow("Max Exposure:", self.max_exposure_spin)

        layout.addWidget(opt_group)

        # Data sources
        data_group = QGroupBox("Data Sources")
        data_layout = QVBoxLayout(data_group)

        self.use_vegas = QCheckBox("Vegas Lines")
        self.use_vegas.setChecked(True)

        self.use_statcast = QCheckBox("Statcast Data")
        self.use_statcast.setChecked(True)

        self.use_weather = QCheckBox("Weather Data")
        self.use_weather.setChecked(False)

        self.use_trends = QCheckBox("Recent Trends")
        self.use_trends.setChecked(True)

        data_layout.addWidget(self.use_vegas)
        data_layout.addWidget(self.use_statcast)
        data_layout.addWidget(self.use_weather)
        data_layout.addWidget(self.use_trends)

        layout.addWidget(data_group)

        layout.addStretch()

        return widget

    def create_lineups_tab(self):
        """Create lineup generation tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Generation mode
        mode_group = QGroupBox("Generation Mode")
        mode_layout = QVBoxLayout(mode_group)

        self.single_radio = QRadioButton("Single Lineup")
        self.single_radio.setChecked(True)

        self.multi_radio = QRadioButton("Multiple Lineups")

        mode_layout.addWidget(self.single_radio)
        mode_layout.addWidget(self.multi_radio)

        layout.addWidget(mode_group)

        # Multi-lineup settings
        multi_group = QGroupBox("Multiple Lineup Settings")
        multi_layout = QFormLayout(multi_group)

        self.lineup_count_spin = QSpinBox()
        self.lineup_count_spin.setRange(2, 150)
        self.lineup_count_spin.setValue(20)
        multi_layout.addRow("Number of Lineups:", self.lineup_count_spin)

        self.diversity_slider = QSlider(Qt.Horizontal)
        self.diversity_slider.setRange(0, 100)
        self.diversity_slider.setValue(70)
        self.diversity_label = QLabel("70%")

        diversity_layout = QHBoxLayout()
        diversity_layout.addWidget(self.diversity_slider)
        diversity_layout.addWidget(self.diversity_label)
        multi_layout.addRow("Diversity:", diversity_layout)

        layout.addWidget(multi_group)

        # Connect signals
        self.single_radio.toggled.connect(lambda checked: multi_group.setEnabled(not checked))
        self.diversity_slider.valueChanged.connect(lambda v: self.diversity_label.setText(f"{v}%"))

        # Presets
        preset_group = QGroupBox("Quick Presets")
        preset_layout = QGridLayout(preset_group)

        presets = [
            ("Cash Game", lambda: self.apply_preset('cash')),
            ("GPP Tournament", lambda: self.apply_preset('gpp')),
            ("Single Entry", lambda: self.apply_preset('single')),
            ("Mass Multi-Entry", lambda: self.apply_preset('mass'))
        ]

        for i, (label, func) in enumerate(presets):
            btn = QPushButton(label)
            btn.clicked.connect(func)
            preset_layout.addWidget(btn, i // 2, i % 2)

        layout.addWidget(preset_group)

        layout.addStretch()

        return widget

    def create_right_panel(self):
        """Create right results panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.result_tabs = QTabWidget()

        self.console = ThreadSafeConsole()
        self.result_tabs.addTab(self.console, "📋 Console")

        lineup_widget = self.create_lineup_display()
        self.result_tabs.addTab(lineup_widget, "📊 Lineup")

        analytics_widget = self.create_analytics_display()
        self.result_tabs.addTab(analytics_widget, "📈 Analytics")

        layout.addWidget(self.result_tabs)

        return widget

    def create_lineup_display(self):
        """Create lineup display widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        stats_widget = QWidget()
        stats_widget.setMaximumHeight(100)
        stats_layout = QHBoxLayout(stats_widget)

        self.score_label = self.create_stat_card("Score", "0.0")
        self.salary_label = self.create_stat_card("Salary", "$0")
        self.value_label = self.create_stat_card("Value", "0.0")

        stats_layout.addWidget(self.score_label)
        stats_layout.addWidget(self.salary_label)
        stats_layout.addWidget(self.value_label)

        layout.addWidget(stats_widget)

        self.lineup_table = QTableWidget()
        self.lineup_table.setAlternatingRowColors(True)
        self.lineup_table.setSelectionBehavior(QTableWidget.SelectRows)

        layout.addWidget(self.lineup_table)

        export_layout = QHBoxLayout()

        copy_btn = QPushButton("📋 Copy")
        copy_btn.clicked.connect(self.copy_lineup)

        csv_btn = QPushButton("💾 Export CSV")
        csv_btn.clicked.connect(self.export_csv)

        dk_btn = QPushButton("🏈 DK Format")
        dk_btn.clicked.connect(self.export_dk_format)

        export_layout.addWidget(copy_btn)
        export_layout.addWidget(csv_btn)
        export_layout.addWidget(dk_btn)
        export_layout.addStretch()

        layout.addLayout(export_layout)

        return widget

    def create_analytics_display(self):
        """Create analytics display widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        exposure_group = QGroupBox("Player Exposure (Multi-Lineup)")
        exposure_layout = QVBoxLayout(exposure_group)

        self.exposure_table = QTableWidget()
        self.exposure_table.setColumnCount(4)
        self.exposure_table.setHorizontalHeaderLabels(["Player", "Count", "Exposure %", "Avg Score"])

        exposure_layout.addWidget(self.exposure_table)
        layout.addWidget(exposure_group)

        position_group = QGroupBox("Position Distribution")
        position_layout = QVBoxLayout(position_group)

        self.position_text = QTextEdit()
        self.position_text.setReadOnly(True)
        self.position_text.setMaximumHeight(150)

        position_layout.addWidget(self.position_text)
        layout.addWidget(position_group)

        return widget

    def create_stat_card(self, label, value):
        """Create a statistics display card"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f3f4f6;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(widget)

        label_widget = QLabel(label)
        label_widget.setAlignment(Qt.AlignCenter)
        label_widget.setStyleSheet("font-size: 12px; color: #6b7280;")

        value_widget = QLabel(value)
        value_widget.setAlignment(Qt.AlignCenter)
        value_widget.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        value_widget.setObjectName(f"{label.lower()}_value")

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)

        return widget

    def setup_style(self):
        """Apply application styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #e5e7eb;
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
                background-color: #9ca3af;
            }

            QComboBox, QSpinBox {
                padding: 6px;
                border: 2px solid #e5e7eb;
                border-radius: 6px;
                background-color: white;
            }

            QTableWidget {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background-color: white;
            }

            QTabWidget::pane {
                border: 2px solid #e5e7eb;
                background-color: white;
                border-radius: 8px;
            }

            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
                background-color: #f3f4f6;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }

            QTabBar::tab:selected {
                background-color: white;
                color: #1e40af;
                font-weight: bold;
            }
        """)

    def load_settings(self):
        """Load saved settings"""
        settings = QSettings("DFSOptimizer", "CleanGUI")

        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        self.last_directory = settings.value("last_directory", "")

    def save_settings(self):
        """Save application settings"""
        settings = QSettings("DFSOptimizer", "CleanGUI")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("last_directory", self.last_directory)

    def closeEvent(self, event):
        """Handle application close"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self.save_settings()
        event.accept()

    def auto_detect_files(self):
        """Auto-detect CSV files in current directory"""
        import glob

        patterns = ["*DKSalaries*.csv", "*draftkings*.csv", "*DK_*.csv"]

        for pattern in patterns:
            files = glob.glob(pattern)
            if files:
                files.sort(key=os.path.getmtime, reverse=True)
                self.load_csv(files[0])
                break

    def browse_csv(self):
        """Browse for CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select DraftKings CSV",
            self.last_directory,
            "CSV Files (*.csv);;All Files (*.*)"
        )

        if file_path:
            self.last_directory = os.path.dirname(file_path)
            self.load_csv(file_path)

    def reload_csv(self):
        """Reload current CSV file"""
        if self.dk_file:
            self.load_csv(self.dk_file)
        else:
            self.update_status("No CSV file to reload")

    def load_csv(self, file_path):
        """Load DraftKings CSV file"""
        try:
            self.dk_file = file_path
            filename = os.path.basename(file_path)

            self.csv_label.setText(f"✅ {filename}")
            self.csv_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #10b981;
                    border-radius: 8px;
                    padding: 20px;
                    background-color: #d1fae5;
                    color: #065f46;
                    font-weight: bold;
                }
            """)

            if CORE_AVAILABLE:
                self.core = BulletproofDFSCore()
            else:
                self.core = BulletproofDFSCore()

            success = self.core.load_draftkings_csv(file_path)

            if success:
                self.contest_type = self.core.contest_type
                self.update_contest_indicator()
                self.generate_btn.setEnabled(True)

                self.console.thread_safe_append(f"✅ Loaded {filename}")
                self.console.thread_safe_append(f"📊 {len(self.core.players)} players loaded")
                self.console.thread_safe_append(f"🎮 Contest type: {self.contest_type.upper()}")

                # Apply DFF if already selected
                if self.dff_file and hasattr(self.core, 'apply_dff_rankings'):
                    try:
                        self.core.apply_dff_rankings(self.dff_file)
                        self.console.thread_safe_append("✅ DFF rankings applied")
                    except Exception as e:
                        self.console.thread_safe_append(f"⚠️ Could not apply DFF: {str(e)}")

                self.update_status(f"Ready to optimize - {len(self.core.players)} players loaded")
            else:
                raise Exception("Failed to load CSV")

        except Exception as e:
            self.console.thread_safe_append(f"❌ Error loading CSV: {str(e)}")
            self.update_status(f"Error: {str(e)}")
            self.generate_btn.setEnabled(False)

    def update_contest_indicator(self):
        """Update contest type indicator"""
        if self.contest_type == 'showdown':
            self.contest_indicator.setText("Contest: Showdown")
            self.contest_indicator.setStyleSheet("""
                QLabel {
                    padding: 4px 8px;
                    background-color: #f59e0b;
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
        else:
            self.contest_indicator.setText("Contest: Classic")
            self.contest_indicator.setStyleSheet("""
                QLabel {
                    padding: 4px 8px;
                    background-color: #3b82f6;
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)

    def load_sample_players(self):
        """Load sample player names"""
        if self.contest_type == 'showdown':
            sample = "Aaron Judge, Juan Soto, Giancarlo Stanton, Gleyber Torres, Rafael Devers"
        else:
            sample = "Shohei Ohtani, Mookie Betts, Aaron Judge, Mike Trout, Ronald Acuna Jr."

        self.manual_text.setPlainText(sample)

    def create_test_data(self):
        """Create test CSV data"""
        try:
            fd, path = tempfile.mkstemp(suffix='_test.csv')

            with os.fdopen(fd, 'w', newline='') as f:
                writer = csv.writer(f)

                writer.writerow([
                    'Position', 'Name + ID', 'Name', 'ID', 'Roster Position',
                    'Salary', 'Game Info', 'TeamAbbrev', 'AvgPointsPerGame'
                ])

                if self.contest_type == 'showdown':
                    teams = ['NYY', 'BOS']
                    for i, team in enumerate(teams):
                        for j in range(10):
                            writer.writerow([
                                'UTIL', f'{team} Player{j + 1} ({i * 10 + j})',
                                f'{team} Player{j + 1}', str(i * 10 + j), 'CPT/UTIL',
                                3000 + j * 500, f'{teams[0]}@{teams[1]}', team,
                                8 + j * 0.5
                            ])
                else:
                    positions = [
                        ('P', 20), ('C', 10), ('1B', 10), ('2B', 10),
                        ('3B', 10), ('SS', 10), ('OF', 30)
                    ]

                    player_id = 1
                    for pos, count in positions:
                        for i in range(count):
                            writer.writerow([
                                pos, f'{pos} Player{i + 1} ({player_id})',
                                f'{pos} Player{i + 1}', str(player_id), pos,
                                4000 + i * 200, 'NYY@BOS', 'NYY',
                                10 + i * 0.3
                            ])
                            player_id += 1

            self.load_csv(path)
            self.console.thread_safe_append("✅ Test data created and loaded")

        except Exception as e:
            self.console.thread_safe_append(f"❌ Error creating test data: {str(e)}")

    def apply_preset(self, preset_type):
        """Apply optimization preset"""
        if preset_type == 'cash':
            self.single_radio.setChecked(True)
            self.mode_combo.setCurrentIndex(2)
            self.min_salary_spin.setValue(49000)
        elif preset_type == 'gpp':
            self.multi_radio.setChecked(True)
            self.lineup_count_spin.setValue(20)
            self.mode_combo.setCurrentIndex(0)
            self.diversity_slider.setValue(80)
        elif preset_type == 'single':
            self.single_radio.setChecked(True)
            self.mode_combo.setCurrentIndex(0)
            self.min_salary_spin.setValue(48500)
        elif preset_type == 'mass':
            self.multi_radio.setChecked(True)
            self.lineup_count_spin.setValue(150)
            self.mode_combo.setCurrentIndex(0)
            self.diversity_slider.setValue(90)

    def quick_generate(self, count):
        """Quick lineup generation"""
        if not self.core:
            QMessageBox.warning(self, "No Data", "Please load a CSV file first")
            return

        self.multi_radio.setChecked(True)
        self.lineup_count_spin.setValue(count)
        self.run_optimization()

    def get_optimization_settings(self):
        """Get current optimization settings"""
        mode_map = {
            0: 'bulletproof',
            1: 'manual_only',
            2: 'confirmed_only',
            3: 'all'
        }

        settings = {
            'mode': mode_map.get(self.mode_combo.currentIndex(), 'bulletproof'),
            'manual_players': self.manual_text.toPlainText().strip() if self.manual_text else "",
            'lineup_count': 1 if self.single_radio.isChecked() else self.lineup_count_spin.value(),
            'min_salary': self.min_salary_spin.value(),
            'max_exposure': self.max_exposure_spin.value(),
            'contest_type': self.contest_type
        }

        return settings

    def run_optimization(self):
        """Run lineup optimization"""
        if not self.core:
            QMessageBox.warning(self, "No Data", "Please load a CSV file first")
            return

        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "Optimization Running",
                "An optimization is already running. Cancel it?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker.wait()
            else:
                return

        self.console.clear()
        self.console.thread_safe_append("=" * 60)
        self.console.thread_safe_append("🚀 STARTING OPTIMIZATION")
        self.console.thread_safe_append("=" * 60)

        settings = self.get_optimization_settings()

        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("🔄 Optimizing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.worker = OptimizationWorker(self.core, settings)

        self.worker.started.connect(self.on_optimization_started)
        self.worker.progress.connect(self.on_optimization_progress)
        self.worker.finished.connect(self.on_optimization_finished)
        self.worker.error.connect(self.on_optimization_error)

        self.worker.start()

    def on_optimization_started(self):
        """Handle optimization start"""
        self.update_status("Optimization in progress...")

    def on_optimization_progress(self, message):
        """Handle optimization progress"""
        self.console.thread_safe_append(f"  {message}")

    def on_optimization_finished(self, lineups):
        """Handle optimization completion"""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("🚀 Generate Optimal Lineup")
        self.progress_bar.setVisible(False)

        self.last_results = lineups

        self.console.thread_safe_append(f"\n✅ Generated {len(lineups)} lineup(s)")

        if len(lineups) == 1:
            self.display_single_lineup(lineups[0])
        else:
            self.display_multiple_lineups(lineups)

        self.result_tabs.setCurrentIndex(1)

        avg_score = sum(l['total_score'] for l in lineups) / len(lineups)
        self.update_status(f"Optimization complete - {len(lineups)} lineup(s), avg score: {avg_score:.1f}")

    def on_optimization_error(self, error_msg):
        """Handle optimization error"""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("🚀 Generate Optimal Lineup")
        self.progress_bar.setVisible(False)

        self.console.thread_safe_append(f"\n❌ ERROR: {error_msg}")
        self.update_status("Optimization failed")

        if "segmentation" in error_msg.lower() or "memory" in error_msg.lower():
            QMessageBox.critical(
                self, "Optimization Error",
                "The optimization crashed. Try:\n"
                "- Using fewer players (Manual Only mode)\n"
                "- Reducing lineup count\n"
                "- Restarting the application"
            )
        else:
            QMessageBox.warning(self, "Optimization Error", error_msg)

    def display_single_lineup(self, lineup_data):
        """Display a single lineup"""
        lineup = lineup_data['lineup']

        score = lineup_data['total_score']
        salary = lineup_data['total_salary']
        value = score / (salary / 1000) if salary > 0 else 0

        self.score_label.findChild(QLabel, "score_value").setText(f"{score:.1f}")
        self.salary_label.findChild(QLabel, "salary_value").setText(f"${salary:,}")
        self.value_label.findChild(QLabel, "value_value").setText(f"{value:.2f}")

        if self.contest_type == 'showdown':
            self.setup_showdown_table()
            self.display_showdown_lineup(lineup)
        else:
            self.setup_classic_table()
            self.display_classic_lineup(lineup)

    def setup_classic_table(self):
        """Setup table for classic contest"""
        self.lineup_table.setColumnCount(6)
        self.lineup_table.setHorizontalHeaderLabels([
            "Position", "Player", "Team", "Salary", "Projected", "Value"
        ])

        header = self.lineup_table.horizontalHeader()
        header.setStretchLastSection(True)

    def setup_showdown_table(self):
        """Setup table for showdown contest"""
        self.lineup_table.setColumnCount(7)
        self.lineup_table.setHorizontalHeaderLabels([
            "Type", "Player", "Team", "Salary", "Multiplier", "Projected", "Value"
        ])

        header = self.lineup_table.horizontalHeader()
        header.setStretchLastSection(True)

    def display_classic_lineup(self, lineup):
        """Display classic lineup in table"""
        self.lineup_table.setRowCount(len(lineup))

        position_order = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
        position_count = {pos: 0 for pos in set(position_order)}

        for i, player in enumerate(lineup):
            pos = getattr(player, 'assigned_position', player.primary_position)

            if pos in position_count:
                position_count[pos] += 1
                if pos in ['P', 'OF'] and position_count[pos] > 1:
                    display_pos = f"{pos}{position_count[pos]}"
                else:
                    display_pos = pos
            else:
                display_pos = pos

            pos_item = QTableWidgetItem(display_pos)
            pos_item.setTextAlignment(Qt.AlignCenter)
            self.lineup_table.setItem(i, 0, pos_item)

            self.lineup_table.setItem(i, 1, QTableWidgetItem(player.name))

            team_item = QTableWidgetItem(player.team)
            team_item.setTextAlignment(Qt.AlignCenter)
            self.lineup_table.setItem(i, 2, team_item)

            salary_item = QTableWidgetItem(f"${player.salary:,}")
            salary_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lineup_table.setItem(i, 3, salary_item)

            score = getattr(player, 'enhanced_score', player.projection)
            proj_item = QTableWidgetItem(f"{score:.1f}")
            proj_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lineup_table.setItem(i, 4, proj_item)

            value = score / (player.salary / 1000) if player.salary > 0 else 0
            value_item = QTableWidgetItem(f"{value:.2f}")
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lineup_table.setItem(i, 5, value_item)

            if pos == 'P':
                color = QColor(219, 234, 254)
            elif pos in ['C', '1B', '2B', '3B', 'SS']:
                color = QColor(254, 215, 215)
            else:
                color = QColor(209, 250, 229)

            for j in range(6):
                item = self.lineup_table.item(i, j)
                if item:
                    item.setBackground(color)

    def display_showdown_lineup(self, lineup):
        """Display showdown lineup in table"""
        self.lineup_table.setRowCount(len(lineup))

        for i, player in enumerate(lineup):
            player_type = getattr(player, 'assigned_position', 'UTIL')
            if i == 0 and player_type != 'UTIL':
                player_type = 'CPT'

            type_item = QTableWidgetItem(player_type)
            type_item.setTextAlignment(Qt.AlignCenter)
            self.lineup_table.setItem(i, 0, type_item)

            self.lineup_table.setItem(i, 1, QTableWidgetItem(player.name))

            team_item = QTableWidgetItem(player.team)
            team_item.setTextAlignment(Qt.AlignCenter)
            self.lineup_table.setItem(i, 2, team_item)

            multiplier = 1.5 if player_type == 'CPT' else 1.0
            salary = int(player.salary * multiplier)
            salary_item = QTableWidgetItem(f"${salary:,}")
            salary_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lineup_table.setItem(i, 3, salary_item)

            mult_item = QTableWidgetItem(f"{multiplier}x")
            mult_item.setTextAlignment(Qt.AlignCenter)
            self.lineup_table.setItem(i, 4, mult_item)

            base_score = getattr(player, 'enhanced_score', player.projection)
            adj_score = base_score * multiplier
            proj_item = QTableWidgetItem(f"{adj_score:.1f}")
            proj_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lineup_table.setItem(i, 5, proj_item)

            value = adj_score / (salary / 1000) if salary > 0 else 0
            value_item = QTableWidgetItem(f"{value:.2f}")
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lineup_table.setItem(i, 6, value_item)

            if player_type == 'CPT':
                color = QColor(254, 240, 138)
            else:
                color = QColor(226, 232, 240)

            for j in range(7):
                item = self.lineup_table.item(i, j)
                if item:
                    item.setBackground(color)

    def display_multiple_lineups(self, lineups):
        """Display multiple lineups summary"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{len(lineups)} Lineups Generated")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        scores = [l['total_score'] for l in lineups]
        salaries = [l['total_salary'] for l in lineups]

        summary_text = f"""
        <h3>Lineup Summary</h3>
        <p><b>Total Lineups:</b> {len(lineups)}</p>
        <p><b>Score Range:</b> {min(scores):.1f} - {max(scores):.1f}</p>
        <p><b>Average Score:</b> {sum(scores) / len(scores):.1f}</p>
        <p><b>Salary Range:</b> ${min(salaries):,} - ${max(salaries):,}</p>
        """

        summary_label = QLabel(summary_text)
        layout.addWidget(summary_label)

        lineup_list = QListWidget()
        for i, lineup_data in enumerate(lineups):
            item_text = f"Lineup {i + 1}: {lineup_data['total_score']:.1f} pts, ${lineup_data['total_salary']:,}"
            lineup_list.addItem(item_text)

        lineup_list.itemDoubleClicked.connect(
            lambda item: self.display_single_lineup(lineups[lineup_list.row(item)])
        )

        layout.addWidget(lineup_list)

        btn_layout = QHBoxLayout()

        export_btn = QPushButton("Export All")
        export_btn.clicked.connect(lambda: self.export_all_lineups(lineups))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)

        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        dialog.exec_()

        self.update_exposure_analysis(lineups)

    def update_exposure_analysis(self, lineups):
        """Update player exposure analysis"""
        player_usage = {}

        for lineup_data in lineups:
            for player in lineup_data['lineup']:
                key = player.name
                if key not in player_usage:
                    player_usage[key] = {
                        'count': 0,
                        'total_score': 0,
                        'salary': player.salary
                    }
                player_usage[key]['count'] += 1
                score = getattr(player, 'enhanced_score', player.projection)
                player_usage[key]['total_score'] += score

        sorted_players = sorted(
            player_usage.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )

        self.exposure_table.setRowCount(len(sorted_players))

        for i, (name, data) in enumerate(sorted_players):
            self.exposure_table.setItem(i, 0, QTableWidgetItem(name))

            count_item = QTableWidgetItem(str(data['count']))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.exposure_table.setItem(i, 1, count_item)

            exposure = (data['count'] / len(lineups)) * 100
            exp_item = QTableWidgetItem(f"{exposure:.1f}%")
            exp_item.setTextAlignment(Qt.AlignCenter)

            if exposure > 60:
                exp_item.setBackground(QColor(254, 202, 202))
            elif exposure > 40:
                exp_item.setBackground(QColor(254, 240, 138))
            else:
                exp_item.setBackground(QColor(187, 247, 208))

            self.exposure_table.setItem(i, 2, exp_item)

            avg_score = data['total_score'] / data['count']
            avg_item = QTableWidgetItem(f"{avg_score:.1f}")
            avg_item.setTextAlignment(Qt.AlignCenter)
            self.exposure_table.setItem(i, 3, avg_item)

        position_counts = {}
        for lineup_data in lineups:
            for player in lineup_data['lineup']:
                pos = getattr(player, 'assigned_position', player.primary_position)
                position_counts[pos] = position_counts.get(pos, 0) + 1

        pos_text = "Position Distribution:\n\n"
        for pos, count in sorted(position_counts.items()):
            avg_per_lineup = count / len(lineups)
            pos_text += f"{pos}: {count} total ({avg_per_lineup:.1f} per lineup)\n"

        self.position_text.setPlainText(pos_text)

    def copy_lineup(self):
        """Copy lineup to clipboard"""
        if not self.last_results:
            return

        lineup = self.last_results[0]['lineup']
        text = ", ".join([p.name for p in lineup])

        QApplication.clipboard().setText(text)
        self.update_status("Lineup copied to clipboard")

    def export_csv(self):
        """Export lineup(s) to CSV"""
        if not self.last_results:
            QMessageBox.warning(self, "No Data", "No lineups to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Lineups",
            os.path.join(self.last_directory, "lineups.csv"),
            "CSV Files (*.csv)"
        )

        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)

                    if self.contest_type == 'showdown':
                        writer.writerow(['Lineup', 'Type', 'Player', 'Team', 'Salary', 'Multiplier', 'Score'])
                    else:
                        writer.writerow(['Lineup', 'Position', 'Player', 'Team', 'Salary', 'Score'])

                    for i, lineup_data in enumerate(self.last_results):
                        for j, player in enumerate(lineup_data['lineup']):
                            if self.contest_type == 'showdown':
                                player_type = 'CPT' if j == 0 else 'UTIL'
                                multiplier = 1.5 if j == 0 else 1.0
                                score = getattr(player, 'enhanced_score', player.projection) * multiplier
                                writer.writerow([
                                    i + 1, player_type, player.name, player.team,
                                    int(player.salary * multiplier), f"{multiplier}x", score
                                ])
                            else:
                                pos = getattr(player, 'assigned_position', player.primary_position)
                                score = getattr(player, 'enhanced_score', player.projection)
                                writer.writerow([
                                    i + 1, pos, player.name, player.team, player.salary, score
                                ])

                self.update_status(f"Exported {len(self.last_results)} lineup(s) to {os.path.basename(file_path)}")

            except Exception as e:
                QMessageBox.warning(self, "Export Error", f"Failed to export: {str(e)}")

    def export_dk_format(self):
        """Export in DraftKings upload format"""
        if not self.last_results:
            QMessageBox.warning(self, "No Data", "No lineups to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export for DraftKings",
            os.path.join(self.last_directory, "dk_upload.csv"),
            "CSV Files (*.csv)"
        )

        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)

                    for lineup_data in self.last_results:
                        row = []

                        if self.contest_type == 'showdown':
                            for player in lineup_data['lineup']:
                                row.append(player.name)
                        else:
                            positions = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
                            lineup_by_pos = {}

                            for player in lineup_data['lineup']:
                                pos = getattr(player, 'assigned_position', player.primary_position)
                                if pos not in lineup_by_pos:
                                    lineup_by_pos[pos] = []
                                lineup_by_pos[pos].append(player.name)

                            for pos in positions:
                                if pos in lineup_by_pos and lineup_by_pos[pos]:
                                    row.append(lineup_by_pos[pos].pop(0))
                                else:
                                    row.append("")

                        writer.writerow(row)

                self.update_status(f"Exported {len(self.last_results)} lineup(s) for DraftKings")

            except Exception as e:
                QMessageBox.warning(self, "Export Error", f"Failed to export: {str(e)}")

    def export_all_lineups(self, lineups):
        """Export all lineups from dialog"""
        self.last_results = lineups
        self.export_csv()

    def update_status(self, message):
        """Update status bar message"""
        self.status_bar.showMessage(message)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("DFS Optimizer Pro")
    app.setOrganizationName("DFS Tools")

    app.setStyle("Fusion")

    window = DFSOptimizerGUI()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
