#!/usr/bin/env python3
"""
DFS OPTIMIZER INTEGRATED GUI - STEP 5
=====================================
Complete GUI with CSV loading, slate detection, strategy auto-selection,
player pool management, and optimization
"""

import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import pyperclip  # If not installed: pip install pyperclip
import json
import traceback

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing components with correct paths
from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem
from dfs_optimizer.strategies.strategy_selector import StrategyAutoSelector
from dfs_optimizer.data.smart_confirmation import SmartConfirmationSystem
from dfs_optimizer.strategies import STRATEGY_REGISTRY


class PlayerPoolModel(QAbstractTableModel):
    """Model for player pool table with checkboxes"""

    def __init__(self, players=None):
        super().__init__()
        self.players = players or []
        self.manual_selections = set()  # Start empty
        self.headers = ['Select', 'Name', 'Team', 'Pos', 'Salary', 'Proj', 'Confirmed', 'Bat']

    def rowCount(self, parent=QModelIndex()):
        return len(self.players)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        player = self.players[index.row()]
        col = index.column()

        if role == Qt.CheckStateRole and col == 0:
            return Qt.Checked if player.name in self.manual_selections else Qt.Unchecked

        if role == Qt.DisplayRole:
            if col == 1:
                return player.name
            elif col == 2:
                return player.team
            elif col == 3:
                return player.primary_position
            elif col == 4:
                return f"${player.salary:,}"
            elif col == 5:
                # Use dff_projection or projection, whichever exists
                proj = getattr(player, 'dff_projection', getattr(player, 'projection', 0))
                return f"{proj:.1f}"
            elif col == 6:
                return "✓" if getattr(player, 'is_confirmed', False) else ""
            elif col == 7:
                order = getattr(player, 'batting_order', 0)
                # Handle None values
                if order is None:
                    return ""
                return str(order) if order > 0 else ""

        if role == Qt.TextAlignmentRole:
            if col in [4, 5, 6, 7]:
                return Qt.AlignCenter

        if role == Qt.BackgroundRole:
            if getattr(player, 'is_confirmed', False):
                return QColor(200, 255, 200)  # Light green for confirmed

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def flags(self, index):
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole and index.column() == 0:
            player = self.players[index.row()]
            if value == Qt.Checked:
                self.manual_selections.add(player.name)
            else:
                self.manual_selections.discard(player.name)
            self.dataChanged.emit(index, index)
            return True
        return False

    def update_players(self, players):
        self.beginResetModel()
        self.players = players
        self.endResetModel()




class OptimizationWorker(QThread):
    """Background worker for optimization"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    log = pyqtSignal(str, str)
    slate_analyzed = pyqtSignal(dict)

    def __init__(self, system, settings):
        super().__init__()
        self.system = system
        self.settings = settings

    def run(self):
        """Run optimization process"""
        try:
            # Score players
            self.progress.emit(70, "Scoring players...")
            self.system.score_players(contest_type=self.settings['contest_type'])

            # Optimize lineups
            self.progress.emit(85, "Generating optimal lineups...")
            lineups = self.system.optimize_lineups(
                num_lineups=self.settings['num_lineups'],
                strategy=self.settings['strategy'],
                contest_type=self.settings['contest_type'],
                min_unique_players=self.settings.get('min_unique', 3)
            )

            self.progress.emit(100, "Optimization complete!")
            self.finished.emit(lineups)

        except Exception as e:
            self.error.emit(str(e))


class DFSOptimizerGUI(QMainWindow):
    """Main GUI Application"""

    def __init__(self):
        super().__init__()
        self.system = UnifiedCoreSystem()
        self.strategy_selector = StrategyAutoSelector()
        self.confirmation_system = SmartConfirmationSystem(verbose=False)
        self.system.confirmation_system = self.confirmation_system

        self.slate_info = {}
        self.selected_strategy = None
        self.lineups = []

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("DFS Optimizer - Step 5 Integration")
        self.setGeometry(100, 100, 1400, 900)

        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Add workflow steps
        main_layout.addWidget(self.create_workflow_widget())

        # Add main content area
        content_layout = QHBoxLayout()

        # Left panel - Controls
        left_panel = self.create_control_panel()
        content_layout.addWidget(left_panel, 1)

        # Center panel - Player Pool
        center_panel = self.create_player_pool_panel()
        content_layout.addWidget(center_panel, 2)

        # Right panel - Results
        right_panel = self.create_results_panel()
        content_layout.addWidget(right_panel, 1)

        main_layout.addLayout(content_layout)

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready to load CSV")

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def create_workflow_widget(self):
        """Create workflow steps indicator"""
        workflow = QWidget()
        layout = QHBoxLayout(workflow)

        steps = [
            ("1. Load CSV", "load"),
            ("2. Detect Slate", "detect"),
            ("3. Get Confirmations", "confirm"),
            ("4. Build Pool", "pool"),
            ("5. Optimize", "optimize"),
            ("6. Export", "export")
        ]

        self.step_labels = {}

        for i, (text, key) in enumerate(steps):
            label = QLabel(text)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    background-color: #e0e0e0;
                    border: 2px solid #cccccc;
                    border-radius: 5px;
                    padding: 10px;
                    font-weight: bold;
                }
            """)
            self.step_labels[key] = label
            layout.addWidget(label)

            if i < len(steps) - 1:
                arrow = QLabel("→")
                arrow.setAlignment(Qt.AlignCenter)
                layout.addWidget(arrow)

        return workflow

    def create_control_panel(self):
        """Create left control panel"""
        panel = QGroupBox("Controls")
        layout = QVBoxLayout(panel)

        # CSV Loading
        csv_group = QGroupBox("1. Load DraftKings CSV")
        csv_layout = QVBoxLayout(csv_group)

        self.csv_path_label = QLabel("No file loaded")
        csv_layout.addWidget(self.csv_path_label)

        self.load_csv_btn = QPushButton("Load CSV")
        self.load_csv_btn.clicked.connect(self.load_csv)
        csv_layout.addWidget(self.load_csv_btn)

        layout.addWidget(csv_group)

        # Slate Info
        slate_group = QGroupBox("2. Slate Detection")
        slate_layout = QVBoxLayout(slate_group)

        self.slate_info_text = QTextEdit()
        self.slate_info_text.setReadOnly(True)
        self.slate_info_text.setMaximumHeight(100)
        slate_layout.addWidget(self.slate_info_text)

        self.strategy_label = QLabel("Strategy: Not selected")
        self.strategy_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        slate_layout.addWidget(self.strategy_label)

        layout.addWidget(slate_group)

        # Contest Settings
        contest_group = QGroupBox("3. Contest Settings")
        contest_layout = QFormLayout(contest_group)

        # Contest type - CASH AS DEFAULT
        self.contest_type = QComboBox()
        self.contest_type.addItems(["Cash", "GPP"])  # Cash first
        self.contest_type.currentTextChanged.connect(self.update_strategy_display)
        contest_layout.addRow("Contest Type:", self.contest_type)

        # Number of lineups - DEFAULT TO 1
        self.num_lineups = QSpinBox()
        self.num_lineups.setRange(1, 150)
        self.num_lineups.setValue(1)  # Default to 1 lineup
        contest_layout.addRow("Lineups:", self.num_lineups)

        # Min unique players
        self.min_unique = QSpinBox()
        self.min_unique.setRange(1, 6)
        self.min_unique.setValue(3)
        contest_layout.addRow("Min Unique:", self.min_unique)

        # MANUAL SLATE SIZE OVERRIDE
        self.manual_slate_cb = QCheckBox("Manual Slate Size")
        self.manual_slate_cb.toggled.connect(self.toggle_manual_slate)
        contest_layout.addRow("", self.manual_slate_cb)

        self.manual_slate_size = QComboBox()
        self.manual_slate_size.addItems(["Small", "Medium", "Large"])
        self.manual_slate_size.setEnabled(False)
        self.manual_slate_size.currentTextChanged.connect(self.update_strategy_display)
        contest_layout.addRow("Slate Size:", self.manual_slate_size)

        layout.addWidget(contest_group)

        # Action Buttons
        actions_group = QGroupBox("4. Actions")
        actions_layout = QVBoxLayout(actions_group)

        self.fetch_confirm_btn = QPushButton("Fetch Confirmations")
        self.fetch_confirm_btn.clicked.connect(self.fetch_confirmations)
        self.fetch_confirm_btn.setEnabled(False)
        actions_layout.addWidget(self.fetch_confirm_btn)

        self.build_pool_btn = QPushButton("Build Player Pool")
        self.build_pool_btn.clicked.connect(self.build_player_pool)
        self.build_pool_btn.setEnabled(False)
        actions_layout.addWidget(self.build_pool_btn)

        # Pool filter options
        filter_layout = QHBoxLayout()
        self.confirmed_only_cb = QCheckBox("Confirmed Only")
        self.confirmed_only_cb.setChecked(True)  # Default to confirmed only
        filter_layout.addWidget(self.confirmed_only_cb)

        self.manual_selections_cb = QCheckBox("Include Manual")
        self.manual_selections_cb.setChecked(False)  # Default to NOT include manual
        filter_layout.addWidget(self.manual_selections_cb)

        actions_layout.addLayout(filter_layout)

        self.optimize_btn = QPushButton("OPTIMIZE LINEUPS")
        self.optimize_btn.clicked.connect(self.run_optimization)
        self.optimize_btn.setEnabled(False)
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                font-size: 14px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        actions_layout.addWidget(self.optimize_btn)

        # NEW: Export Tracking Button
        self.export_tracking_btn = QPushButton("📋 Copy Lineup for Tracking")
        self.export_tracking_btn.clicked.connect(self.export_lineup_summary)
        self.export_tracking_btn.setEnabled(False)  # Disabled until lineups generated
        self.export_tracking_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-weight: bold;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        actions_layout.addWidget(self.export_tracking_btn)

        layout.addWidget(actions_group)

        layout.addStretch()

        return panel

    def export_lineup_summary(self):
        """Export lineup summary for easy tracking"""
        if not self.lineups:
            self.log("No lineups to export!", "error")
            return

        # Get the first lineup (or let user select which one)
        lineup = self.lineups[0]

        # Build a formatted summary
        summary_lines = [
            "=" * 60,
            f"DFS LINEUP TRACKING - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
            f"Contest Type: {self.contest_type.currentText()}",
            f"Strategy: {self.selected_strategy}",
            f"Projected Points: {lineup.get('total_projection', 0):.1f}",
            f"Total Salary: ${lineup.get('total_salary', 0):,}",
            "",
            "LINEUP:",
            "-" * 40
        ]

        # Add each player
        for player in lineup['players']:
            pos = player.primary_position
            name = player.name
            team = player.team
            salary = player.salary
            proj = getattr(player, 'dff_projection', 0)
            summary_lines.append(f"{pos:<4} {name:<20} {team:<4} ${salary:>6,} {proj:>5.1f}")

        # Add tracking fields
        summary_lines.extend([
            "",
            "-" * 40,
            "RESULTS (Fill in after contest):",
            "Actual Score: _______",
            "Placement: _______",
            "Entries: _______",
            "Winnings: $_______",
            "ROI: _______%",
            "=" * 60
        ])

        # Join all lines
        summary = "\n".join(summary_lines)

        # Copy to clipboard
        try:
            QApplication.clipboard().setText(summary)
            self.log("✅ Lineup copied to clipboard! Paste into your tracking spreadsheet.", "success")
        except Exception as e:
            self.log(f"Error copying to clipboard: {e}", "error")

        # Also save to a file for backup
        tracking_dir = "lineup_tracking"
        os.makedirs(tracking_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{tracking_dir}/lineup_{timestamp}.txt"

        with open(filename, 'w') as f:
            f.write(summary)

        self.log(f"Also saved to: {filename}", "info")


    def create_player_pool_panel(self):
        """Create center player pool panel"""
        panel = QGroupBox("Player Pool")
        layout = QVBoxLayout(panel)

        # Pool info
        self.pool_info_label = QLabel("No players loaded")
        layout.addWidget(self.pool_info_label)

        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.textChanged.connect(self.filter_players)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)

        # Player table
        self.player_table = QTableView()
        self.player_model = PlayerPoolModel()
        self.player_table.setModel(self.player_model)
        self.player_table.setAlternatingRowColors(True)
        self.player_table.setSelectionBehavior(QTableView.SelectRows)
        self.player_table.setSortingEnabled(True)

        # Set column widths
        self.player_table.setColumnWidth(0, 50)  # Select
        self.player_table.setColumnWidth(1, 150)  # Name
        self.player_table.setColumnWidth(2, 50)  # Team
        self.player_table.setColumnWidth(3, 50)  # Pos
        self.player_table.setColumnWidth(4, 70)  # Salary
        self.player_table.setColumnWidth(5, 60)  # Proj
        self.player_table.setColumnWidth(6, 80)  # Confirmed
        self.player_table.setColumnWidth(7, 40)  # Bat (batting order)

        layout.addWidget(self.player_table)

        # Quick actions
        quick_actions = QHBoxLayout()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_players)
        quick_actions.addWidget(select_all_btn)

        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all_players)
        quick_actions.addWidget(clear_all_btn)

        select_confirmed_btn = QPushButton("Select Confirmed")
        select_confirmed_btn.clicked.connect(self.select_confirmed_players)
        quick_actions.addWidget(select_confirmed_btn)

        quick_actions.addStretch()
        layout.addLayout(quick_actions)

        # Manual player addition
        manual_add_layout = QHBoxLayout()
        manual_add_layout.addWidget(QLabel("Add Player:"))
        self.manual_player_input = QLineEdit()
        self.manual_player_input.setPlaceholderText("Enter player name...")
        self.manual_player_input.returnPressed.connect(self.add_manual_player)  # Enter key support
        manual_add_layout.addWidget(self.manual_player_input)

        add_player_btn = QPushButton("Add")
        add_player_btn.clicked.connect(self.add_manual_player)
        manual_add_layout.addWidget(add_player_btn)

        layout.addLayout(manual_add_layout)

        return panel

    def create_results_panel(self):
        """Create right results panel"""
        panel = QGroupBox("Results")
        layout = QVBoxLayout(panel)

        # Results tabs
        self.results_tabs = QTabWidget()

        # Lineups tab
        self.lineups_text = QTextEdit()
        self.lineups_text.setReadOnly(True)
        self.results_tabs.addTab(self.lineups_text, "Lineups")

        # Analysis tab
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.results_tabs.addTab(self.analysis_text, "Analysis")

        # Log tab
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.results_tabs.addTab(self.log_text, "Log")

        layout.addWidget(self.results_tabs)

        # Export button
        self.export_btn = QPushButton("Export Lineups")
        self.export_btn.clicked.connect(self.export_lineups)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)

        return panel

    def update_step(self, step_key, completed=True):
        """Update workflow step visual status"""
        if step_key in self.step_labels:
            if completed:
                self.step_labels[step_key].setStyleSheet("""
                    QLabel {
                        background-color: #4CAF50;
                        color: white;
                        border: 2px solid #45a049;
                        border-radius: 5px;
                        padding: 10px;
                        font-weight: bold;
                    }
                """)
            else:
                self.step_labels[step_key].setStyleSheet("""
                    QLabel {
                        background-color: #FFC107;
                        border: 2px solid #FFA000;
                        border-radius: 5px;
                        padding: 10px;
                        font-weight: bold;
                    }
                """)

    def log(self, message, level="info"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        colors = {
            "info": "#000000",
            "success": "#4CAF50",
            "warning": "#ff9800",
            "error": "#f44336"
        }

        color = colors.get(level, "#000000")
        self.log_text.append(f'<span style="color: #666">[{timestamp}]</span> '
                             f'<span style="color: {color}">{message}</span>')

    def load_csv(self):
        """Load DraftKings CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select DraftKings CSV",
            "",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            # Load CSV through system
            self.system.load_players_from_csv(file_path)

            # Update UI
            self.csv_path_label.setText(os.path.basename(file_path))
            self.update_step("load", True)
            self.log(f"Loaded {len(self.system.players)} players from CSV", "success")

            # Enable next steps
            self.fetch_confirm_btn.setEnabled(True)
            self.build_pool_btn.setEnabled(True)

            # Analyze slate
            self.analyze_slate()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")
            self.log(f"Error loading CSV: {str(e)}", "error")

    def analyze_slate(self):
        """Analyze slate and auto-select strategy"""
        try:
            # Use strategy selector to analyze
            self.slate_info = self.strategy_selector.analyze_slate_from_csv(self.system.players)

            # Detect if showdown
            positions = {p.primary_position for p in self.system.players}
            is_showdown = 'CPT' in positions or 'UTIL' in positions

            # Update slate info display
            info_text = f"Slate Type: {'SHOWDOWN' if is_showdown else 'CLASSIC'}\n"
            info_text += f"Games: {self.slate_info.get('num_games', 'Unknown')}\n"
            info_text += f"Size: {self.slate_info.get('slate_size', 'Unknown').upper()}\n"
            info_text += f"Players: {len(self.system.players)}"

            self.slate_info_text.setText(info_text)

            # Update strategy
            self.update_strategy_display()

            self.update_step("detect", True)
            self.log(
                f"Detected {self.slate_info.get('slate_size', 'unknown')} slate with {self.slate_info.get('num_games', 0)} games",
                "success")

        except Exception as e:
            self.log(f"Error analyzing slate: {str(e)}", "error")

    def toggle_manual_slate(self, checked):
        """Toggle manual slate size override"""
        self.manual_slate_size.setEnabled(checked)
        if checked:
            self.log("Manual slate size override enabled", "info")
        self.update_strategy_display()

    def update_strategy_display(self):
        """Update the displayed strategy based on slate and contest type"""
        contest_type = self.contest_type.currentText().lower()

        # Get slate size - use manual override if enabled
        if self.manual_slate_cb.isChecked():
            slate_size = self.manual_slate_size.currentText().lower()
        else:
            slate_size = self.slate_info.get('slate_size', 'medium')

        # Get recommended strategy
        if 'showdown' in str(self.slate_info.get('slate_type', '')).lower():
            self.selected_strategy = self.strategy_selector.top_strategies['showdown']['all']
        else:
            self.selected_strategy = self.strategy_selector.top_strategies[contest_type][slate_size]

        self.strategy_label.setText(f"Strategy: {self.selected_strategy.replace('_', ' ').title()}")

        # Update lineup count based on contest type
        if contest_type == 'cash' and not self.num_lineups.value() == 1:
            self.num_lineups.setValue(1)  # Reset to 1 for cash
        elif contest_type == 'gpp' and self.num_lineups.value() == 1:
            self.num_lineups.setValue(20)  # Default to 20 for GPP

    def fetch_confirmations(self):
        """Fetch confirmed lineups"""
        try:
            self.log("Fetching confirmed lineups...", "info")
            confirmed = self.system.fetch_confirmed_players()

            if confirmed:
                self.log(f"Found {len(confirmed)} confirmed players", "success")
                self.update_step("confirm", True)

                # Update player model to show confirmations
                if hasattr(self, 'player_model') and self.player_model.players:
                    for player in self.player_model.players:
                        player.is_confirmed = player.name in confirmed
                    self.player_model.layoutChanged.emit()
            else:
                self.log("No confirmations available yet", "warning")

        except Exception as e:
            self.log(f"Error fetching confirmations: {str(e)}", "error")

    def add_manual_player(self):
        """Add a manual player to the selection"""
        player_name = self.manual_player_input.text().strip()
        if not player_name:
            return

        # Find the player in the pool
        player_found = False
        for player in self.player_model.players:
            if player.name.lower() == player_name.lower():
                self.player_model.manual_selections.add(player.name)
                player_found = True
                self.log(f"Added {player.name} to manual selections", "success")
                break

        if not player_found:
            # Try partial match
            matches = []
            for player in self.player_model.players:
                if player_name.lower() in player.name.lower():
                    matches.append(player)

            if matches:
                if len(matches) == 1:
                    self.player_model.manual_selections.add(matches[0].name)
                    self.log(f"Added {matches[0].name} to manual selections", "success")
                else:
                    names = ", ".join([p.name for p in matches[:5]])
                    self.log(f"Multiple matches found: {names}", "warning")
            else:
                self.log(f"Player '{player_name}' not found in pool", "error")

        # Clear input and refresh display
        self.manual_player_input.clear()
        self.player_model.layoutChanged.emit()

    def build_player_pool(self):
        """Build the player pool based on filters"""
        try:
            # Disable button during processing
            self.build_pool_btn.setEnabled(False)
            QApplication.processEvents()  # Keep GUI responsive

            # Check filter settings
            include_unconfirmed = not self.confirmed_only_cb.isChecked()

            # Clear manual selections first to avoid the "all selected" bug
            self.system.manual_selections = set()

            # Only add manual selections if checkbox is checked AND there are selections
            if self.manual_selections_cb.isChecked() and hasattr(self.player_model, 'manual_selections'):
                if self.player_model.manual_selections:  # Only if not empty
                    self.system.manual_selections = self.player_model.manual_selections.copy()
                    self.log(f"Including {len(self.system.manual_selections)} manual selections", "info")

            # Build pool
            self.system.build_player_pool(include_unconfirmed=include_unconfirmed)

            # Update display
            self.player_model.update_players(self.system.player_pool)
            self.pool_info_label.setText(f"Pool: {len(self.system.player_pool)} players")

            # Enrich player data
            self.log("Enhancing player data...", "info")
            QApplication.processEvents()  # Keep GUI responsive

            self.system.enrich_player_pool()

            # Debug: Check batting orders
            players_with_order = 0
            for player in self.system.player_pool:
                if hasattr(player, 'batting_order') and player.batting_order:
                    players_with_order += 1

            if players_with_order > 0:
                self.log(f"Found batting order for {players_with_order} players", "info")

            self.update_step("pool", True)
            self.log(f"Built pool with {len(self.system.player_pool)} players", "success")

            # Enable optimization
            self.optimize_btn.setEnabled(True)

        except Exception as e:
            self.log(f"Error building pool: {str(e)}", "error")
            import traceback
            self.log(traceback.format_exc(), "error")

        finally:
            # Re-enable button
            self.build_pool_btn.setEnabled(True)

    def filter_players(self, text):
        """Filter player table based on search text"""
        # This would implement filtering logic
        pass

    def select_all_players(self):
        """Select all players in the table"""
        for player in self.player_model.players:
            self.player_model.manual_selections.add(player.name)
        self.player_model.layoutChanged.emit()
        self.log(f"Selected all {len(self.player_model.players)} players", "info")

    def clear_all_players(self):
        """Clear all player selections"""
        self.player_model.manual_selections.clear()
        self.player_model.layoutChanged.emit()
        self.log("Cleared all manual selections", "info")

    def select_confirmed_players(self):
        """Select only confirmed players"""
        self.player_model.manual_selections.clear()
        count = 0
        for player in self.player_model.players:
            if getattr(player, 'is_confirmed', False):
                self.player_model.manual_selections.add(player.name)
                count += 1
        self.player_model.layoutChanged.emit()
        self.log(f"Selected {count} confirmed players", "info")

    def run_optimization(self):
        """Run the optimization process"""
        # Disable controls
        self.optimize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)

        # Prepare settings
        settings = {
            'num_lineups': self.num_lineups.value(),
            'contest_type': self.contest_type.currentText().lower(),
            'strategy': self.selected_strategy,
            'min_unique': self.min_unique.value()
        }

        # Update status
        self.update_step("optimize", False)
        self.log(f"Starting {settings['contest_type'].upper()} optimization with {self.selected_strategy} strategy...",
                 "info")

        # Create and start worker
        self.worker = OptimizationWorker(self.system, settings)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.finished.connect(self.on_optimization_complete)
        self.worker.error.connect(self.on_optimization_error)
        self.worker.log.connect(self.log)
        self.worker.start()

    def on_progress_update(self, value, message):
        """Handle progress updates"""
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(message)

    def on_optimization_complete(self, lineups):
        """Handle successful optimization"""
        self.lineups = lineups

        # Re-enable controls
        self.optimize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.update_step("optimize", True)

        # Display results
        self.display_lineups(lineups)
        self.display_analysis(lineups)

        # Enable export
        self.export_btn.setEnabled(True)
        self.update_step("export", False)

        # Success message
        self.log(f"✅ Generated {len(lineups)} optimal lineups!", "success")
        self.status_bar.showMessage("Optimization complete!")

    def on_optimization_error(self, error_msg):
        """Handle optimization error"""
        self.optimize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        QMessageBox.critical(self, "Optimization Error", error_msg)
        self.log(f"Optimization failed: {error_msg}", "error")

    def display_lineups(self, lineups):
        """Display generated lineups"""
        self.lineups_text.clear()

        for i, lineup in enumerate(lineups, 1):
            self.lineups_text.append(f"Lineup {i}:")
            self.lineups_text.append("-" * 50)

            total_salary = 0
            total_proj = 0

            # Sort by position for display
            players = lineup.get('players', [])

            for player in players:
                pos = player.primary_position
                name = player.name
                team = player.team
                salary = player.salary
                # Use dff_projection or projection, whichever exists
                proj = getattr(player, 'dff_projection', getattr(player, 'projection', 0))

                total_salary += salary
                total_proj += proj

                self.lineups_text.append(f"{pos:<4} {name:<20} {team:<4} ${salary:>6,} {proj:>6.1f}")
                self.export_tracking_btn.setEnabled(True)


            self.lineups_text.append(f"\nTotal Salary: ${total_salary:,} | Projected: {total_proj:.1f}")
            self.lineups_text.append("\n")

    def display_analysis(self, lineups):
        """Display lineup analysis"""
        self.analysis_text.clear()

        if not lineups:
            return

        # Basic stats
        num_lineups = len(lineups)
        avg_proj = sum(l.get('total_projection', 0) for l in lineups) / num_lineups
        avg_salary = sum(l.get('total_salary', 0) for l in lineups) / num_lineups

        self.analysis_text.append("📊 LINEUP ANALYSIS")
        self.analysis_text.append("=" * 50)
        self.analysis_text.append(f"Total Lineups: {num_lineups}")
        self.analysis_text.append(f"Average Projection: {avg_proj:.1f}")
        self.analysis_text.append(f"Average Salary: ${avg_salary:,.0f}")
        self.analysis_text.append(f"Strategy Used: {self.selected_strategy.replace('_', ' ').title()}")

        # Stack analysis
        self.analysis_text.append("\n🏟️ STACK ANALYSIS")
        self.analysis_text.append("-" * 30)

        team_counts = {}
        for lineup in lineups:
            lineup_teams = {}
            for player in lineup.get('players', []):
                team = player.team
                lineup_teams[team] = lineup_teams.get(team, 0) + 1

            # Count stacks
            for team, count in lineup_teams.items():
                if count >= 3:
                    team_counts[team] = team_counts.get(team, 0) + 1

        for team, count in sorted(team_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            pct = (count / num_lineups) * 100
            self.analysis_text.append(f"{team}: {count} lineups ({pct:.1f}%)")

    def export_lineups(self):
        """Export lineups to CSV"""
        if not self.lineups:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Lineups",
            f"dfs_lineups_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            # Create export data
            export_data = []

            for lineup in self.lineups:
                row = {}

                # Add players by position
                for player in lineup.get('players', []):
                    pos = player.primary_position

                    # Handle multi-position slots
                    if pos in row:
                        # Find next available slot
                        for i in range(2, 10):
                            alt_pos = f"{pos}{i}"
                            if alt_pos not in row:
                                row[alt_pos] = player.name
                                break
                    else:
                        row[pos] = player.name

                export_data.append(row)

            # Convert to DataFrame and save
            df = pd.DataFrame(export_data)
            df.to_csv(file_path, index=False)

            self.update_step("export", True)
            self.log(f"Exported {len(self.lineups)} lineups to {os.path.basename(file_path)}", "success")
            QMessageBox.information(self, "Success", f"Lineups exported to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
            self.log(f"Export failed: {str(e)}", "error")


# Add this method to your DFSOptimizerGUI class in dfs_optimizer_integrated_GUI.py

def run_system_diagnostics(self):
    """Test that strategies and enhancements are working correctly"""
    self.log("\n=== STRATEGY & ENHANCEMENT TEST ===", "warning")

    # Test 1: Check current strategy
    contest_type = self.contest_type.currentText().lower()
    self.log(f"Contest Type: {contest_type.upper()}", "info")
    self.log(f"Selected Strategy: {self.selected_strategy}", "info")

    # Test 2: Check if we have a player pool
    if not self.system.player_pool:
        self.log("⚠️ No player pool built yet! Build pool first.", "error")
        return

    # Test 3: Check if scoring is different for cash vs GPP
    test_player = self.system.player_pool[0]

    # Score for cash
    self.system.score_players('cash')
    cash_score = test_player.enhanced_score

    # Score for GPP
    self.system.score_players('gpp')
    gpp_score = test_player.enhanced_score

    self.log(f"\nTest Player: {test_player.name}", "info")
    self.log(f"Cash Score: {cash_score:.2f}", "info")
    self.log(f"GPP Score: {gpp_score:.2f}", "info")
    self.log(f"Difference: {abs(cash_score - gpp_score):.2f}", "success")

    if abs(cash_score - gpp_score) < 0.01:
        self.log("⚠️ WARNING: Scores identical - strategies may not be different!", "error")
    else:
        self.log("✓ Strategies producing different scores!", "success")

    # Test 4: Check if enhancements are applied
    self.log("\n--- Enhancement Check ---", "warning")

    # Check basic attributes
    basic_attrs = ['salary', 'team', 'primary_position', 'dff_projection']
    for attr in basic_attrs:
        value = getattr(test_player, attr, None)
        if value:
            self.log(f"✓ {attr}: {value}", "success")

    # Check team total
    team_total = getattr(test_player, 'team_total', None)
    self.log(f"Team Total: {team_total if team_total else 'Not set (using default 4.5)'}", "info")

    # Check batting order
    batting_order = getattr(test_player, 'batting_order', None)
    if batting_order and batting_order > 0:
        self.log(f"Batting Order: {batting_order}", "success")
    else:
        self.log("Batting Order: Not available", "warning")

    # Test 5: Strategy-specific behavior
    self.log("\n--- Strategy Behavior ---", "warning")

    if contest_type == 'cash':
        self.log("Cash strategy active:", "info")
        self.log("- projection_monster strategy", "info")
        self.log("- High floor prioritization", "info")
        self.log("- Max 3 players per team", "info")
        self.log("- Conservative approach", "info")
    else:
        self.log("GPP strategy active:", "info")
        self.log(f"- {self.selected_strategy} strategy", "info")
        self.log("- High ceiling prioritization", "info")
        self.log("- Stacking encouraged (3-5 players)", "info")
        self.log("- Ownership leverage", "info")

    # Test 6: Check lineup constraints
    self.log("\n--- Quick Optimization Test ---", "warning")

    try:
        # Run a quick 1-lineup optimization
        self.system.score_players(contest_type)
        test_lineup = self.system.optimize_lineups(
            num_lineups=1,
            strategy=self.selected_strategy,
            contest_type=contest_type
        )

        if test_lineup:
            lineup = test_lineup[0]
            self.log(f"✓ Generated test lineup: ${lineup['total_salary']:,}", "success")

            # Check team distribution
            teams = {}
            for p in lineup['players']:
                teams[p.team] = teams.get(p.team, 0) + 1

            max_from_team = max(teams.values())
            self.log(f"Max players from one team: {max_from_team}", "info")

            if contest_type == 'cash' and max_from_team > 3:
                self.log("⚠️ Cash lineup has >3 from same team!", "error")
            elif contest_type == 'gpp' and max_from_team >= 3:
                self.log("✓ GPP lineup has stack!", "success")
    except Exception as e:
        self.log(f"Optimization test failed: {str(e)}", "error")

    self.log("\n=== TEST COMPLETE ===", "warning")
    self.log("Check results above to verify system is working correctly", "info")

def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("DFS Optimizer")
    app.setOrganizationName("DFS Tools")

    # Create and show main window
    window = DFSOptimizerGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()