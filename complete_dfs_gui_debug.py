#!/usr/bin/env python3
"""
COMPLETE DFS GUI WITH DEBUG & PROGRESS
======================================
A fully functional GUI with debugging console and progress tracking
"""

# 1. IMPORTS (lines 1-20)
import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd
import random
import time
import traceback



class DebugConsole(QWidget):
    """Debug console widget for showing logs"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title bar
        title_layout = QHBoxLayout()
        title = QLabel("🐛 Debug Console")
        title.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(title)

        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setMaximumWidth(60)
        self.clear_btn.clicked.connect(self.clear_log)
        title_layout.addWidget(self.clear_btn)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # Console text area
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                padding: 5px;
            }
        """)
        self.console.setMaximumHeight(150)
        layout.addWidget(self.console)

        self.setLayout(layout)

    def log(self, message, level="INFO"):
        """Add a log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color coding by level
        colors = {
            "INFO": "#cccccc",
            "SUCCESS": "#4CAF50",
            "WARNING": "#FF9800",
            "ERROR": "#F44336",
            "DEBUG": "#2196F3"
        }

        color = colors.get(level, "#cccccc")

        # Format message
        formatted_msg = f'<span style="color: #666666;">[{timestamp}]</span> '
        formatted_msg += f'<span style="color: {color};">{level}:</span> '
        formatted_msg += f'<span style="color: #cccccc;">{message}</span>'

        self.console.append(formatted_msg)

        # Auto-scroll to bottom
        scrollbar = self.console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        # Process events to update immediately
        QApplication.processEvents()

    def clear_log(self):
        """Clear the console"""
        self.console.clear()


class FileLoadPanel(QWidget):
    """Panel for loading CSV files"""

    file_loaded = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("📁 Load Player Data")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # File info frame
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Box)
        info_frame.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        info_layout = QVBoxLayout(info_frame)

        self.file_label = QLabel("No file loaded")
        self.file_label.setStyleSheet("font-style: italic; color: #666;")
        info_layout.addWidget(self.file_label)

        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("font-size: 12px; color: #333;")
        info_layout.addWidget(self.stats_label)

        layout.addWidget(info_frame)

        # Buttons
        btn_layout = QHBoxLayout()

        self.load_btn = QPushButton("📂 Load CSV")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
        """)
        self.load_btn.clicked.connect(self.load_file)
        btn_layout.addWidget(self.load_btn)

        self.sample_btn = QPushButton("📊 Load Sample")
        self.sample_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #545B62;
            }
        """)
        self.sample_btn.clicked.connect(self.load_sample)
        btn_layout.addWidget(self.sample_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()
        self.setLayout(layout)

    def load_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select DraftKings CSV",
            "",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        if filename:
            self.process_file(filename)

    def load_sample(self):
        """Create a sample CSV for testing"""
        sample_data = {
            'Name': ['Mike Trout', 'Mookie Betts', 'Aaron Judge', 'Freddie Freeman'],
            'Position': ['OF', 'OF', 'OF', '1B'],
            'Salary': [10200, 9800, 9500, 8900],
            'TeamAbbrev': ['LAA', 'LAD', 'NYY', 'LAD'],
            'AvgPointsPerGame': [12.5, 11.8, 11.2, 10.5]
        }

        df = pd.DataFrame(sample_data)
        filename = 'sample_dfs_data.csv'
        df.to_csv(filename, index=False)
        self.process_file(filename)

    def process_file(self, filename):
        """Process the loaded file"""
        try:
            df = pd.read_csv(filename)

            # Update labels
            self.file_label.setText(f"✅ {os.path.basename(filename)}")
            self.file_label.setStyleSheet("color: #28a745; font-weight: bold;")

            # Show stats
            stats = f"Players: {len(df)} | "
            if 'Position' in df.columns:
                stats += f"Positions: {df['Position'].nunique()} | "
            if 'Salary' in df.columns:
                stats += f"Avg Salary: ${df['Salary'].mean():,.0f}"

            self.stats_label.setText(stats)

            # Emit signal
            self.file_loaded.emit(filename)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")


class OptimizationPanel(QWidget):
    """Panel for optimization settings - confirmed players + manual only"""

    optimize_clicked = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.manual_players = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("⚙️ Optimization Settings")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Settings group
        settings_group = QGroupBox("Parameters")
        settings_layout = QFormLayout()

        # Strategy
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(['balanced', 'ceiling', 'safe', 'value', 'contrarian'])
        self.strategy_combo.setCurrentText('balanced')
        settings_layout.addRow("Strategy:", self.strategy_combo)

        # Number of lineups
        self.lineups_spin = QSpinBox()
        self.lineups_spin.setRange(1, 20)
        self.lineups_spin.setValue(1)
        settings_layout.addRow("Lineups:", self.lineups_spin)

        # Min salary
        self.min_salary_slider = QSlider(Qt.Horizontal)
        self.min_salary_slider.setRange(80, 100)
        self.min_salary_slider.setValue(95)
        self.min_salary_label = QLabel("95%")
        self.min_salary_slider.valueChanged.connect(
            lambda v: self.min_salary_label.setText(f"{v}%")
        )
        salary_layout = QHBoxLayout()
        salary_layout.addWidget(self.min_salary_slider)
        salary_layout.addWidget(self.min_salary_label)
        settings_layout.addRow("Min Salary:", salary_layout)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Manual Player Selection
        manual_group = QGroupBox("Manual Player Selection")
        manual_layout = QVBoxLayout()

        # Input section
        input_layout = QHBoxLayout()
        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Enter exact player name...")
        self.manual_input.returnPressed.connect(self.add_manual_player)
        input_layout.addWidget(self.manual_input)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_manual_player)
        add_btn.setMaximumWidth(60)
        input_layout.addWidget(add_btn)

        manual_layout.addLayout(input_layout)

        # Current manual players
        self.manual_list = QListWidget()
        self.manual_list.setMaximumHeight(120)
        manual_layout.addWidget(self.manual_list)

        # List controls
        controls_layout = QHBoxLayout()
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_selected_player)
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all_players)
        controls_layout.addWidget(remove_btn)
        controls_layout.addWidget(clear_btn)
        manual_layout.addLayout(controls_layout)

        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)

        # Status
        self.status_label = QLabel("Only confirmed + manual players will be used")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)

        # Optimize button
        self.optimize_btn = QPushButton("🚀 Generate Lineups")
        self.optimize_btn.setEnabled(False)
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                font-size: 16px;
                padding: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.optimize_btn.clicked.connect(self.on_optimize)
        layout.addWidget(self.optimize_btn)

        layout.addStretch()
        self.setLayout(layout)

    def add_manual_player(self):
        """Add exact player name to manual selection"""
        player_name = self.manual_input.text().strip()
        if player_name and player_name not in self.manual_players:
            self.manual_players.append(player_name)
            self.manual_list.addItem(player_name)
            self.manual_input.clear()
            self.update_status()

    def remove_selected_player(self):
        """Remove selected player"""
        current_row = self.manual_list.currentRow()
        if current_row >= 0:
            player_name = self.manual_list.takeItem(current_row).text()
            self.manual_players.remove(player_name)
            self.update_status()

    def clear_all_players(self):
        """Clear all manual players"""
        self.manual_players.clear()
        self.manual_list.clear()
        self.update_status()

    def update_status(self):
        """Update status based on manual players"""
        count = len(self.manual_players)
        if count > 0:
            self.status_label.setText(f"{count} manual player(s) selected")
        else:
            self.status_label.setText("Only confirmed players will be used")

    def enable_optimization(self, enabled=True):
        """Enable optimization button"""
        self.optimize_btn.setEnabled(enabled)

    def on_optimize(self):
        """Emit settings with manual players only"""
        settings = {
            'strategy': self.strategy_combo.currentText(),
            'num_lineups': self.lineups_spin.value(),
            'min_salary': self.min_salary_slider.value(),
            'manual_players': self.manual_players.copy()
        }
        self.optimize_clicked.emit(settings)

class ProgressTracker(QWidget):
    """Progress tracking widget"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Stage label
        self.stage_label = QLabel("Ready")
        self.stage_label.setAlignment(Qt.AlignCenter)
        self.stage_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(self.stage_label)

        self.setLayout(layout)

    def set_progress(self, value, stage=""):
        """Update progress"""
        self.progress_bar.setValue(value)
        if stage:
            self.stage_label.setText(stage)
        QApplication.processEvents()

    def reset(self):
        """Reset progress"""
        self.progress_bar.setValue(0)
        self.stage_label.setText("Ready")


class OptimizationWorker(QThread):
    """Worker thread using the Unified Core System"""

    progress = pyqtSignal(int, str)
    log = pyqtSignal(str, str)
    result = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, players_df, settings, csv_filename=None):
        super().__init__()
        self.players_df = players_df
        self.settings = settings
        self.csv_filename = csv_filename

    def run(self):
        """Run optimization using Unified Core System"""
        try:
            # Import the unified system
            from unified_core_system import UnifiedCoreSystem

            self.log.emit("🚀 Starting Unified Core System", "INFO")
            self.progress.emit(5, "Initializing system...")

            # Initialize system
            system = UnifiedCoreSystem()

            # Load CSV
            self.progress.emit(15, "Loading player data...")
            self.log.emit(f"Loading {len(self.players_df)} players", "INFO")

            # Save temp CSV if needed
            if not self.csv_filename:
                self.csv_filename = 'temp_optimization.csv'
                self.players_df.to_csv(self.csv_filename, index=False)

            num_loaded = system.load_csv(self.csv_filename)
            self.log.emit(f"✅ Loaded {num_loaded} players", "SUCCESS")

            # Fetch confirmed players
            self.progress.emit(30, "Fetching confirmed lineups...")
            self.log.emit("🔍 Checking for confirmed lineups...", "INFO")

            num_confirmed = system.fetch_confirmed_players()
            self.log.emit(f"✅ Found {num_confirmed} confirmed players", "SUCCESS")

            # Add manual selections
            manual_players = self.settings.get('manual_players', [])
            if manual_players:
                self.log.emit(f"Adding {len(manual_players)} manual selections", "INFO")
                for player_name in manual_players:
                    if system.add_manual_player(player_name):
                        self.log.emit(f"   ✅ Added: {player_name}", "SUCCESS")
                    else:
                        self.log.emit(f"   ❌ Not found: {player_name}", "WARNING")

            # Build player pool
            # Build player pool
            self.progress.emit(40, "Building player pool...")

            # Add manual players first
            manual_players = self.settings.get('manual_players', [])
            if manual_players:
                self.log.emit(f"Adding {len(manual_players)} manual players...", "INFO")
                added_count = 0
                for player_name in manual_players:
                    if system.add_manual_player(player_name):
                        added_count += 1
                        self.log.emit(f"   ✅ Added: {player_name}", "SUCCESS")
                    else:
                        self.log.emit(f"   ❌ Not found in CSV: {player_name}", "WARNING")

                if added_count == 0 and len(manual_players) > 0:
                    self.log.emit("❌ No manual players found in CSV", "ERROR")

            # Build final pool (confirmed + manual only)
            pool_size = system.build_player_pool()

            # Strict check - no fallbacks
            if pool_size == 0:
                self.log.emit("❌ No players available", "ERROR")
                self.log.emit("No confirmed lineups found and no valid manual players", "ERROR")
                self.error.emit("No confirmed players found. Add valid manual players or wait for lineups.")
                return

            self.log.emit(f"✅ Final pool: {pool_size} players (confirmed + manual)", "SUCCESS")

            # Show pool breakdown
            status = system.get_system_status()
            self.log.emit(f"   Confirmed: {status['confirmed_players']} (includes pitchers)", "INFO")
            self.log.emit(f"   Manual: {status['manual_players']}", "INFO")

            # Enrich player pool with ALL data
            self.progress.emit(50, "Enriching with Vegas data...")
            self.log.emit("📊 Fetching Vegas lines...", "INFO")

            self.progress.emit(60, "Enriching with Statcast data...")
            self.log.emit("⚾ Fetching Statcast data...", "INFO")

            enriched_count = system.enrich_player_pool()
            self.log.emit(f"✅ Enriched {enriched_count} players", "SUCCESS")

            # Generate lineups
            self.progress.emit(70, "Optimizing lineups...")
            num_lineups = self.settings.get('num_lineups', 1)
            strategy = self.settings.get('strategy', 'balanced')

            self.log.emit(f"🎯 Generating {num_lineups} {strategy} lineups...", "INFO")

            lineups = system.optimize_lineups(
                num_lineups=num_lineups,
                strategy=strategy,
                min_unique_players=3
            )

            if not lineups:
                self.log.emit("❌ Optimization failed!", "ERROR")
                self.error.emit("Failed to generate lineups")
                return

            # Convert to GUI format
            gui_lineups = []

            for i, lineup in enumerate(lineups, 1):
                self.progress.emit(70 + (25 * i // num_lineups), f"Processing lineup {i}...")



                gui_lineup = {
                    'players': [],
                    'total_salary': lineup['total_salary'],
                    'projected_points': lineup['total_projection']
                }

                # Convert each player
                for p in lineup['players']:
                    # Get display position
                    pos = getattr(p, 'display_position', p.primary_position)

                    # Get best score
                    score = getattr(p, 'optimization_score', p.base_projection)

                    # Check if confirmed/manual
                    is_confirmed = getattr(p, 'is_confirmed', False)
                    is_manual = getattr(p, 'is_manual', False)

                    player_dict = {
                        'position': pos,
                        'name': p.name,
                        'salary': p.salary,
                        'team': p.team,
                        'points': score,
                        'confirmed': is_confirmed,
                        'manual': is_manual
                    }

                    gui_lineup['players'].append(player_dict)

                gui_lineups.append(gui_lineup)

                # Log lineup summary
                self.log.emit(f"✅ Lineup {i}: {lineup['total_projection']:.1f} pts, ${lineup['total_salary']:,}",
                              "SUCCESS")

            # Final status
            self.progress.emit(100, "Optimization complete!")
            self.log.emit(f"✅ Generated {len(gui_lineups)} optimized lineups", "SUCCESS")

            # Emit results
            self.result.emit(gui_lineups)

        except Exception as e:
            import traceback
            self.log.emit(f"Error: {str(e)}", "ERROR")
            self.log.emit(traceback.format_exc(), "ERROR")
            self.error.emit(str(e))


def apply_gui_integration():
    """Apply the integration to complete_dfs_gui_debug.py"""
    import shutil
    from datetime import datetime

    print("\n🔧 APPLYING GUI INTEGRATION")
    print("=" * 60)

    gui_file = 'complete_dfs_gui_debug.py'

    # Backup
    backup = f"{gui_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy(gui_file, backup)
        print(f"✅ Created backup: {backup}")
    except:
        print("⚠️  Could not create backup")

    print("\n📋 MANUAL INTEGRATION STEPS:")
    print("1. Copy the OptimizationWorker class above")
    print("2. Replace the existing OptimizationWorker in your GUI")
    print("3. Make sure unified_core_system.py is in the same directory")
    print("4. Run your GUI!")

    print("\n🎯 WHAT THIS GIVES YOU:")
    print("• Confirmed players only optimization")
    print("• ALL enrichments (Vegas, Statcast, etc)")
    print("• Pure data - no fallbacks")
    print("• Manual player selection support")
    print("• Detailed progress and logging")


if __name__ == "__main__":
    apply_gui_integration()



class EnhancedDFSGUI(QMainWindow):
    """Main GUI window with debug features"""

    def __init__(self):
        super().__init__()
        self.players_df = None
        self.optimization_thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("DFS Optimizer - Enhanced Debug Edition")
        self.setGeometry(100, 100, 1400, 900)

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

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Top section - Controls and Results
        top_layout = QHBoxLayout()

        # Left panel - Controls
        left_panel = QWidget()
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # File load panel
        self.file_panel = FileLoadPanel()
        self.file_panel.file_loaded.connect(self.on_file_loaded)
        left_layout.addWidget(self.file_panel)

        # Optimization panel
        self.opt_panel = OptimizationPanel()
        self.opt_panel.optimize_clicked.connect(self.on_optimize)
        left_layout.addWidget(self.opt_panel)

        # Right panel - Results
        results_group = QGroupBox("📊 Results")
        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        results_layout.addWidget(self.results_text)

        # Export button
        self.export_btn = QPushButton("💾 Export Results")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_results)
        results_layout.addWidget(self.export_btn)

        results_group.setLayout(results_layout)

        # Add to top layout
        top_layout.addWidget(left_panel)
        top_layout.addWidget(results_group, 1)

        main_layout.addLayout(top_layout, 1)

        # Progress tracker
        self.progress_tracker = ProgressTracker()
        main_layout.addWidget(self.progress_tracker)

        # Debug console
        self.debug_console = DebugConsole()
        main_layout.addWidget(self.debug_console)

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        # Initial debug messages
        self.debug_console.log("DFS Optimizer initialized", "SUCCESS")
        self.debug_console.log("GUI ready for use", "INFO")

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        load_action = QAction('Load CSV', self)
        load_action.setShortcut('Ctrl+O')
        load_action.triggered.connect(self.file_panel.load_file)
        file_menu.addAction(load_action)

        export_action = QAction('Export Results', self)
        export_action.setShortcut('Ctrl+S')
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu('Tools')

        clear_debug = QAction('Clear Debug Console', self)
        clear_debug.triggered.connect(self.debug_console.clear_log)
        tools_menu.addAction(clear_debug)

        # Help menu
        help_menu = menubar.addMenu('Help')

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def on_file_loaded(self, filename):

        self.debug_console.log(f"Loading file: {filename}", "INFO")

        # Store the filename for core to use
        self.current_csv_file = filename

        try:
            self.players_df = pd.read_csv(filename)
            self.players_df = pd.read_csv(filename)

            # Log file info
            self.debug_console.log(f"Loaded {len(self.players_df)} players", "SUCCESS")
            self.debug_console.log(f"Columns: {list(self.players_df.columns)}", "DEBUG")

            # Show initial stats
            info = f"📁 File: {os.path.basename(filename)}\n"
            info += f"📊 Total Players: {len(self.players_df)}\n\n"

            if 'Position' in self.players_df.columns:
                info += "📍 Positions:\n"
                pos_counts = self.players_df['Position'].value_counts()
                for pos, count in pos_counts.items():
                    info += f"  • {pos}: {count} players\n"

            if 'Salary' in self.players_df.columns:
                info += f"\n💰 Salary Stats:\n"
                info += f"  • Min: ${self.players_df['Salary'].min():,}\n"
                info += f"  • Max: ${self.players_df['Salary'].max():,}\n"
                info += f"  • Avg: ${self.players_df['Salary'].mean():,.0f}\n"

            self.results_text.setText(info)

            # Enable optimization
            self.opt_panel.enable_optimization(True)
            self.status_bar.showMessage(f"Loaded {len(self.players_df)} players")

        except Exception as e:
            self.debug_console.log(f"Error loading file: {str(e)}", "ERROR")
            self.debug_console.log(traceback.format_exc(), "DEBUG")
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")

    def on_optimize(self, settings):
        """Handle optimization request"""
        if self.players_df is None:
            QMessageBox.warning(self, "Warning", "Please load a CSV file first!")
            return

        # Save the CSV filename for core to use
        if hasattr(self, 'current_csv_file'):
            csv_file = self.current_csv_file
        else:
            # Save dataframe to temp file
            csv_file = 'temp_optimization_data.csv'
            self.players_df.to_csv(csv_file, index=False)

        self.debug_console.log(f"Starting optimization with settings: {settings}", "INFO")

        # Disable controls during optimization
        self.opt_panel.optimize_btn.setEnabled(False)
        self.file_panel.load_btn.setEnabled(False)

        # Reset progress
        self.progress_tracker.reset()

        # Create and start worker thread with CSV filename
        self.optimization_thread = OptimizationWorker(self.players_df, settings, csv_file)
        self.optimization_thread.progress.connect(self.progress_tracker.set_progress)
        self.optimization_thread.log.connect(self.debug_console.log)
        self.optimization_thread.result.connect(self.on_optimization_complete)
        self.optimization_thread.error.connect(self.on_optimization_error)
        self.optimization_thread.finished.connect(self.on_thread_finished)

        self.optimization_thread.start()
    def on_optimization_complete(self, lineups):
        """Handle successful optimization"""
        self.debug_console.log("Optimization completed successfully!", "SUCCESS")

        # Display results
        result_text = "🏆 OPTIMIZATION RESULTS\n"
        result_text += "=" * 60 + "\n\n"

        for i, lineup_data in enumerate(lineups, 1):
            result_text += f"📋 LINEUP {i}\n"
            result_text += "-" * 40 + "\n"

            total_salary = 0
            total_points = 0

            for player in lineup_data['players']:
                result_text += f"{player['position']:6} {player['name']:20} "
                result_text += f"${player['salary']:6,} {player['team']:4} "
                result_text += f"{player['points']:5.1f} pts\n"
                total_salary += player['salary']
                total_points += player['points']

            result_text += "-" * 40 + "\n"
            result_text += f"Total Salary: ${total_salary:,} ({total_salary / 500:.1f}%)\n"
            result_text += f"Projected Points: {total_points:.1f}\n\n"

        self.results_text.setText(result_text)
        self.export_btn.setEnabled(True)
        self.status_bar.showMessage(f"Generated {len(lineups)} lineups")

    def on_optimization_error(self, error_msg):
        """Handle optimization error"""
        self.debug_console.log(f"Optimization failed: {error_msg}", "ERROR")
        QMessageBox.critical(self, "Optimization Error",
                             f"Failed to generate lineups:\n{error_msg}")

    def on_thread_finished(self):
        """Handle thread completion"""
        # Re-enable controls
        self.opt_panel.optimize_btn.setEnabled(True)
        self.file_panel.load_btn.setEnabled(True)

    def export_results(self):
        """Export results to file"""
        if not self.results_text.toPlainText():
            QMessageBox.warning(self, "Warning", "No results to export!")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            f"dfs_lineups_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;CSV Files (*.csv)"
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.results_text.toPlainText())

                self.debug_console.log(f"Results exported to: {filename}", "SUCCESS")
                QMessageBox.information(self, "Success",
                                        f"Results saved to:\n{filename}")

            except Exception as e:
                self.debug_console.log(f"Export failed: {str(e)}", "ERROR")
                QMessageBox.critical(self, "Error",
                                     f"Failed to save file:\n{str(e)}")

    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h3>DFS Optimizer - Enhanced Debug Edition</h3>
        <p>Version 2.0</p>
        <p>A powerful tool for optimizing DraftKings lineups with:</p>
        <ul>
            <li>Real-time progress tracking</li>
            <li>Debug console for troubleshooting</li>
            <li>Multiple optimization strategies</li>
            <li>Export functionality</li>
        </ul>
        <p>© 2025 DFS Optimizer Team</p>
        """

        QMessageBox.about(self, "About DFS Optimizer", about_text)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("DFS Optimizer")

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    window = EnhancedDFSGUI()
    window.show()

    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()