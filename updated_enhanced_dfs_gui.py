#!/usr/bin/env python3
"""
UPDATED ENHANCED DFS GUI
========================
Works with the new Advanced DFS Core system
Includes automated stacking integration
"""

import csv
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
except ImportError:
    print("❌ PyQt5 not installed. Install with: pip install PyQt5")
    sys.exit(1)

# Import the new advanced system
try:
    from advanced_dfs_core import AdvancedDFSCore
    from automated_stacking_system import create_stacking_system
    from milp_with_stacking import create_milp_with_stacking

    CORE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Advanced system not available: {e}")
    CORE_AVAILABLE = False


    class AdvancedDFSCore:
        pass


class OptimizationWorker(QThread):
    """Background worker for optimization"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, core, settings):
        super().__init__()
        self.core = core
        self.settings = settings
        self.is_cancelled = False

    def run(self):
        """Run optimization in background"""
        try:
            # Enrich data first
            self.progress.emit("📊 Enriching player data with Statcast metrics...")
            enriched_count = self.core.enrich_player_data()
            self.progress.emit(f"✅ Enriched {enriched_count} players")

            # Check for stacking
            if self.settings.get('use_stacking', True):
                self.progress.emit("🏟️ Analyzing stacking opportunities...")

                # Get stacking system
                stacking_system = create_stacking_system()

                # Get Vegas data
                vegas_data = {}
                for player in self.core.players:
                    if hasattr(player, 'vegas_data') and player.vegas_data:
                        vegas_data[player.team] = player.vegas_data

                # Find stacks
                stacks = stacking_system.identify_stack_candidates(
                    self.core.players,
                    vegas_data=vegas_data
                )

                if stacks:
                    self.progress.emit(f"✅ Found {len(stacks)} potential stacks")

                    # Use top stack
                    best_stack = stacks[0]
                    self.progress.emit(f"🎯 Using {best_stack.team} stack ({best_stack.size} players)")

                    # Get stacking optimizer
                    from unified_milp_optimizer import OptimizationConfig
                    config = OptimizationConfig(salary_cap=50000)
                    stacking_optimizer = create_milp_with_stacking(config)

                    # Replace core optimizer
                    self.core.optimizer = stacking_optimizer

                    # Optimize with stack
                    lineup, score = stacking_optimizer.optimize_lineup_with_stack(
                        self.core.players,
                        selected_stack=best_stack,
                        strategy=self.settings['strategy']
                    )

                    result = {
                        'lineup': lineup,
                        'score': score,
                        'stack': best_stack,
                        'strategy': self.settings['strategy']
                    }
                else:
                    self.progress.emit("No viable stacks found - using standard optimization")
                    lineup, score = self.core.optimize_lineup(
                        manual_selections=self.settings.get('manual_players', '')
                    )
                    result = {
                        'lineup': lineup,
                        'score': score,
                        'stack': None,
                        'strategy': self.settings['strategy']
                    }
            else:
                # Standard optimization
                self.progress.emit("🎯 Running optimization...")
                lineup, score = self.core.optimize_lineup(
                    manual_selections=self.settings.get('manual_players', '')
                )
                result = {
                    'lineup': lineup,
                    'score': score,
                    'stack': None,
                    'strategy': self.settings['strategy']
                }

            if self.is_cancelled:
                return

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))
            traceback.print_exc()

    def cancel(self):
        """Cancel optimization"""
        self.is_cancelled = True


class FileLoadPanel(QWidget):
    """Panel for loading data files"""
    files_loaded = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("📁 Load Data Files")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # DraftKings CSV
        dk_layout = QHBoxLayout()
        self.dk_label = QLabel("DraftKings CSV: Not loaded")
        self.dk_button = QPushButton("Browse...")
        self.dk_button.clicked.connect(self.load_dk_csv)
        dk_layout.addWidget(self.dk_label)
        dk_layout.addWidget(self.dk_button)
        layout.addLayout(dk_layout)

        # DFF Rankings (optional)
        dff_layout = QHBoxLayout()
        self.dff_label = QLabel("DFF Rankings (optional): Not loaded")
        self.dff_button = QPushButton("Browse...")
        self.dff_button.clicked.connect(self.load_dff_file)
        dff_layout.addWidget(self.dff_label)
        dff_layout.addWidget(self.dff_button)
        layout.addLayout(dff_layout)

        # Load button
        self.load_button = QPushButton("🚀 Load Data")
        self.load_button.clicked.connect(self.emit_files)
        self.load_button.setEnabled(False)
        self.load_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout.addWidget(self.load_button)

        self.setLayout(layout)

        # Store file paths
        self.dk_file = None
        self.dff_file = None

    def load_dk_csv(self):
        """Load DraftKings CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DraftKings CSV", "", "CSV Files (*.csv)"
        )

        if file_path:
            self.dk_file = file_path
            self.dk_label.setText(f"DraftKings CSV: {Path(file_path).name}")
            self.load_button.setEnabled(True)

    def load_dff_file(self):
        """Load DFF rankings file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DFF Rankings", "", "CSV Files (*.csv)"
        )

        if file_path:
            self.dff_file = file_path
            self.dff_label.setText(f"DFF Rankings: {Path(file_path).name}")

    def emit_files(self):
        """Emit loaded files"""
        if self.dk_file:
            file_info = {
                'dk_file': self.dk_file,
                'dff_file': self.dff_file
            }
            self.files_loaded.emit(file_info)


class OptimizationPanel(QWidget):
    """Panel for optimization settings"""
    optimize_requested = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("⚙️ Optimization Settings")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Strategy selection
        strategy_layout = QFormLayout()

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "All Players",
            "Confirmed Only",
            "Confirmed + Manual",
            "Balanced",
            "Manual Only"
        ])
        self.strategy_combo.setCurrentIndex(2)  # Default to Confirmed + Manual
        strategy_layout.addRow("Strategy:", self.strategy_combo)

        # Stacking option
        self.use_stacking = QCheckBox("Use Automated Stacking")
        self.use_stacking.setChecked(True)
        strategy_layout.addRow("Stacking:", self.use_stacking)

        # Manual selections
        self.manual_input = QTextEdit()
        self.manual_input.setPlaceholderText("Enter player names separated by commas...")
        self.manual_input.setMaximumHeight(60)
        strategy_layout.addRow("Manual Players:", self.manual_input)

        layout.addLayout(strategy_layout)

        # Optimize button
        self.optimize_button = QPushButton("🎯 Optimize Lineup")
        self.optimize_button.clicked.connect(self.start_optimization)
        self.optimize_button.setEnabled(False)
        self.optimize_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 15px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout.addWidget(self.optimize_button)

        self.setLayout(layout)

    def enable_optimization(self, enabled: bool):
        """Enable/disable optimization button"""
        self.optimize_button.setEnabled(enabled)

    def start_optimization(self):
        """Start optimization with current settings"""
        strategy_map = {
            "All Players": "all",
            "Confirmed Only": "confirmed_only",
            "Confirmed + Manual": "confirmed_plus_manual",
            "Balanced": "balanced",
            "Manual Only": "manual_only"
        }

        settings = {
            'strategy': strategy_map.get(self.strategy_combo.currentText(), "all"),
            'manual_players': self.manual_input.toPlainText().strip(),
            'use_stacking': self.use_stacking.isChecked()
        }

        self.optimize_requested.emit(settings)

    def set_optimizing(self, is_optimizing: bool):
        """Update UI during optimization"""
        self.optimize_button.setEnabled(not is_optimizing)
        if is_optimizing:
            self.optimize_button.setText("⏳ Optimizing...")
        else:
            self.optimize_button.setText("🎯 Optimize Lineup")


class ResultsPanel(QWidget):
    """Panel for displaying results"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("📊 Results")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Tabs for different views
        self.tabs = QTabWidget()

        # Lineup tab
        self.lineup_table = QTableWidget()
        self.lineup_table.setColumnCount(8)
        self.lineup_table.setHorizontalHeaderLabels([
            "Pos", "Player", "Team", "Salary", "Base Proj",
            "Score", "Value", "Details"
        ])
        self.lineup_table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.lineup_table, "📋 Lineup")

        # Log tab
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: monospace;")
        self.tabs.addTab(self.log_text, "📝 Log")

        # Analytics tab
        self.analytics_text = QTextEdit()
        self.analytics_text.setReadOnly(True)
        self.tabs.addTab(self.analytics_text, "📈 Analytics")

        layout.addWidget(self.tabs)

        # Export button
        self.export_button = QPushButton("💾 Export Lineup")
        self.export_button.clicked.connect(self.export_lineup)
        self.export_button.setEnabled(False)
        layout.addWidget(self.export_button)

        self.setLayout(layout)

        self.current_lineup = None

    def log_message(self, message: str):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def display_lineup(self, result: Dict):
        """Display optimization result"""
        lineup = result.get('lineup', [])
        score = result.get('score', 0)
        stack = result.get('stack', None)

        if not lineup:
            self.log_message("❌ No valid lineup found")
            return

        self.current_lineup = lineup
        self.lineup_table.setRowCount(len(lineup))

        total_salary = 0

        for i, player in enumerate(lineup):
            # Position
            self.lineup_table.setItem(i, 0, QTableWidgetItem(player.primary_position))

            # Player name
            name_item = QTableWidgetItem(player.name)
            if getattr(player, 'is_confirmed', False):
                name_item.setForeground(QColor('green'))
            self.lineup_table.setItem(i, 1, name_item)

            # Team
            team_item = QTableWidgetItem(player.team)
            if stack and player.team == stack.team:
                team_item.setBackground(QColor('#FFE4B5'))  # Highlight stack
            self.lineup_table.setItem(i, 2, team_item)

            # Salary
            salary = player.salary
            total_salary += salary
            self.lineup_table.setItem(i, 3, QTableWidgetItem(f"${salary:,}"))

            # Base projection
            base = getattr(player, 'base_projection', 0)
            self.lineup_table.setItem(i, 4, QTableWidgetItem(f"{base:.1f}"))

            # Enhanced score
            enhanced = getattr(player, 'enhanced_score', 0)
            score_item = QTableWidgetItem(f"{enhanced:.1f}")
            if enhanced > base * 1.1:  # 10% boost
                score_item.setForeground(QColor('blue'))
            self.lineup_table.setItem(i, 5, score_item)

            # Value
            value = enhanced / salary * 1000 if salary > 0 else 0
            self.lineup_table.setItem(i, 6, QTableWidgetItem(f"{value:.2f}"))

            # Details
            details = []
            if hasattr(player, 'batting_order') and player.batting_order:
                details.append(f"#{player.batting_order}")
            if hasattr(player, 'statcast_metrics') and player.statcast_metrics:
                if 'barrel_rate' in player.statcast_metrics:
                    details.append(f"Barrel: {player.statcast_metrics['barrel_rate']:.1f}%")
            if hasattr(player, 'is_hot') and player.is_hot:
                details.append("🔥 HOT")

            self.lineup_table.setItem(i, 7, QTableWidgetItem(" | ".join(details)))

        # Update summary
        self.log_message(f"\n✅ OPTIMIZATION COMPLETE")
        self.log_message(f"Score: {score:.1f} points")
        self.log_message(f"Salary: ${total_salary:,} / $50,000")

        if stack:
            self.log_message(f"Stack: {stack.team} ({stack.size} players)")

        # Update analytics
        self.update_analytics(result)

        self.export_button.setEnabled(True)

    def update_analytics(self, result: Dict):
        """Update analytics tab"""
        lineup = result.get('lineup', [])
        stack = result.get('stack', None)

        analytics = []
        analytics.append("📊 LINEUP ANALYTICS")
        analytics.append("=" * 50)

        # Position breakdown
        pos_counts = {}
        for p in lineup:
            pos_counts[p.primary_position] = pos_counts.get(p.primary_position, 0) + 1

        analytics.append("\nPosition Distribution:")
        for pos, count in sorted(pos_counts.items()):
            analytics.append(f"  {pos}: {count}")

        # Team exposure
        team_counts = {}
        for p in lineup:
            team_counts[p.team] = team_counts.get(p.team, 0) + 1

        analytics.append("\nTeam Exposure:")
        for team, count in sorted(team_counts.items(), key=lambda x: x[1], reverse=True):
            analytics.append(f"  {team}: {count} players")

        # Advanced metrics
        analytics.append("\nAdvanced Metrics:")

        # Batters
        batters = [p for p in lineup if p.primary_position != 'P']
        if batters:
            barrel_rates = [
                p.statcast_metrics.get('barrel_rate', 0)
                for p in batters
                if hasattr(p, 'statcast_metrics') and p.statcast_metrics
            ]
            if barrel_rates:
                analytics.append(f"  Avg Barrel Rate: {sum(barrel_rates) / len(barrel_rates):.1f}%")

        # Stack analysis
        if stack:
            analytics.append(f"\nStack Analysis ({stack.team}):")
            analytics.append(f"  Score: {stack.stack_score:.1f}")
            analytics.append(f"  Implied Total: {stack.implied_total:.1f} runs")
            analytics.append(f"  Batting Order: {stack.get_batting_order_string()}")

            for reason in stack.reasons:
                analytics.append(f"  • {reason}")

        self.analytics_text.setPlainText("\n".join(analytics))

    def export_lineup(self):
        """Export lineup to CSV"""
        if not self.current_lineup:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Lineup",
            f"lineup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )

        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Position', 'Player', 'Team', 'Salary', 'Projection'])

                    for player in self.current_lineup:
                        writer.writerow([
                            player.primary_position,
                            player.name,
                            player.team,
                            player.salary,
                            getattr(player, 'enhanced_score', 0)
                        ])

                self.log_message(f"✅ Lineup exported to {Path(file_path).name}")

            except Exception as e:
                self.log_message(f"❌ Export failed: {e}")


class StatusBar(QWidget):
    """Custom status bar"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Status message
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Player count
        self.player_label = QLabel("Players: 0")
        layout.addWidget(self.player_label)

        # Mode
        self.mode_label = QLabel("Mode: Standard")
        layout.addWidget(self.mode_label)

        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border-top: 1px solid #cccccc;
            }
        """)

    def update_status(self, message: str):
        self.status_label.setText(message)

    def update_player_count(self, count: int):
        self.player_label.setText(f"Players: {count}")

    def update_mode(self, is_advanced: bool):
        mode = "Advanced (80+ metrics)" if is_advanced else "Standard"
        self.mode_label.setText(f"Mode: {mode}")


class EnhancedDFSGUI(QMainWindow):
    """Main GUI window"""

    def __init__(self):
        super().__init__()
        self.core = None
        self.worker = None
        self.current_files = {}

        self.init_ui()
        self.init_core()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("DFS Optimizer - Advanced Edition")
        self.setGeometry(100, 100, 1200, 800)

        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
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

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()

        # Top section - File loading and optimization
        top_layout = QHBoxLayout()

        # File panel
        self.file_panel = FileLoadPanel()
        self.file_panel.files_loaded.connect(self.load_data_files)

        file_group = QGroupBox("Step 1: Load Data")
        file_group_layout = QVBoxLayout()
        file_group_layout.addWidget(self.file_panel)
        file_group.setLayout(file_group_layout)
        top_layout.addWidget(file_group)

        # Optimization panel
        self.optimization_panel = OptimizationPanel()
        self.optimization_panel.optimize_requested.connect(self.start_optimization)

        opt_group = QGroupBox("Step 2: Optimize")
        opt_group_layout = QVBoxLayout()
        opt_group_layout.addWidget(self.optimization_panel)
        opt_group.setLayout(opt_group_layout)
        top_layout.addWidget(opt_group)

        main_layout.addLayout(top_layout)

        # Results panel
        self.results_panel = ResultsPanel()

        results_group = QGroupBox("Results")
        results_group_layout = QVBoxLayout()
        results_group_layout.addWidget(self.results_panel)
        results_group.setLayout(results_group_layout)
        main_layout.addWidget(results_group)

        # Status bar
        self.status_bar = StatusBar()
        main_layout.addWidget(self.status_bar)

        central_widget.setLayout(main_layout)

        # Menu bar
        self.create_menu_bar()

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        load_action = QAction("Load CSV", self)
        load_action.setShortcut("Ctrl+O")
        file_menu.addAction(load_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        system_info_action = QAction("System Info", self)
        system_info_action.triggered.connect(self.show_system_info)
        tools_menu.addAction(system_info_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def init_core(self):
        """Initialize DFS core system"""
        if not CORE_AVAILABLE:
            QMessageBox.critical(self, "Error",
                                 "Advanced DFS Core not available.\n"
                                 "Please ensure all required files are present.")
            return

        try:
            self.core = AdvancedDFSCore(mode="production")
            status = self.core.get_system_status()

            self.results_panel.log_message("✅ Advanced DFS Core initialized")
            self.results_panel.log_message(f"🎯 Mode: ADVANCED (80+ metrics)")

            # Update status bar
            self.status_bar.update_mode(True)
            self.status_bar.update_status("System ready")

            # Log module status
            modules = status['modules']
            available = sum(modules.values())
            total = len(modules)
            self.results_panel.log_message(f"📊 Modules: {available}/{total} loaded")

        except Exception as e:
            self.results_panel.log_message(f"❌ System initialization failed: {e}")
            QMessageBox.critical(self, "Error", f"Failed to initialize:\n{e}")

    def load_data_files(self, file_info: Dict):
        """Load data files"""
        try:
            self.results_panel.log_message("📂 Loading data files...")

            # Load CSV
            dk_file = file_info['dk_file']
            self.results_panel.log_message(f"📄 Loading: {Path(dk_file).name}")

            player_count = self.core.load_draftkings_csv(dk_file)

            if player_count == 0:
                raise Exception("No players loaded from CSV")

            self.results_panel.log_message(f"✅ Loaded {player_count} players")
            self.status_bar.update_player_count(player_count)

            # Enable optimization
            self.optimization_panel.enable_optimization(True)
            self.status_bar.update_status(f"Ready - {player_count} players loaded")

            self.current_files = file_info

        except Exception as e:
            self.results_panel.log_message(f"❌ Error loading files: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load files:\n{e}")

    def start_optimization(self, settings: Dict):
        """Start optimization"""
        if not self.core or not self.core.players:
            QMessageBox.warning(self, "Error", "No data loaded.")
            return

        # Cancel existing optimization
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(self, "Cancel?",
                                         "An optimization is running. Cancel it?")
            if reply == QMessageBox.Yes:
                self.worker.cancel()
                self.worker.wait()
            else:
                return

        self.results_panel.log_message("🚀 Starting optimization...")
        self.results_panel.log_message(f"📈 Strategy: {settings['strategy'].upper()}")

        # Update UI
        self.optimization_panel.set_optimizing(True)
        self.status_bar.update_status("Optimization in progress...")

        # Set optimization mode
        self.core.set_optimization_mode(settings['strategy'])

        # Start worker
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

        self.status_bar.update_status("Optimization completed")

    def on_optimization_error(self, error_msg: str):
        """Handle optimization error"""
        self.optimization_panel.set_optimizing(False)
        self.results_panel.log_message(f"❌ Optimization failed: {error_msg}")
        self.status_bar.update_status("Optimization failed")

        QMessageBox.critical(self, "Error", f"Optimization failed:\n{error_msg}")

    def show_system_info(self):
        """Show system information"""
        if not self.core:
            return

        status = self.core.get_system_status()

        info = []
        info.append("SYSTEM INFORMATION")
        info.append("=" * 40)
        info.append(f"Mode: Advanced (80+ metrics)")
        info.append(f"Players loaded: {status['players_loaded']}")
        info.append(f"Players scored: {status['players_scored']}")
        info.append(f"Confirmed players: {status['confirmed_players']}")
        info.append("\nModules:")

        for module, available in status['modules'].items():
            status_icon = "✅" if available else "❌"
            info.append(f"  {status_icon} {module}")

        info.append(f"\nStats:")
        for key, value in status['stats'].items():
            info.append(f"  {key}: {value}")

        QMessageBox.information(self, "System Info", "\n".join(info))

    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>DFS Optimizer - Advanced Edition</h2>
        <p>Version 2.0</p>
        <p>Features:</p>
        <ul>
        <li>80+ Baseball Savant metrics</li>
        <li>Automated stacking algorithms</li>
        <li>Pure data approach (no fallbacks)</li>
        <li>Advanced MILP optimization</li>
        <li>Real-time data enrichment</li>
        </ul>
        <p>© 2025 - Built with PyQt5</p>
        """

        QMessageBox.about(self, "About", about_text)

    def closeEvent(self, event):
        """Handle close event"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(self, "Exit?",
                                         "Optimization is running. Exit anyway?")
            if reply == QMessageBox.Yes:
                self.worker.cancel()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Set application icon
    app.setWindowIcon(QIcon())

    # Create and show GUI
    gui = EnhancedDFSGUI()
    gui.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()