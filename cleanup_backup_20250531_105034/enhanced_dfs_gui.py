#!/usr/bin/env python3
"""
Enhanced DFS GUI - User-Friendly Version
Clean, modern interface with better fonts and improved readability
"""

import sys
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Import PyQt5 with error handling
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *

    print("✅ PyQt5 loaded successfully")
except ImportError:
    print("❌ PyQt5 not available. Install with: pip install PyQt5")
    sys.exit(1)

# Import our optimized core
try:
    from optimized_dfs_core import (
        OptimizedPlayer,
        OptimizedDFSCore,
        load_and_optimize_complete_pipeline,
        create_enhanced_test_data
    )

    print("✅ Optimized DFS Core imported successfully")
    CORE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Could not import optimized DFS core: {e}")
    CORE_AVAILABLE = False


class ModernCardWidget(QFrame):
    """Modern card-style widget with improved styling"""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 1px solid #e3e6ea;
                margin: 5px;
            }
            QFrame:hover {
                border: 1px solid #4285f4;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
        """)

        # Layout with better spacing
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title with improved typography
        if title:
            title_label = QLabel(title)
            title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
            title_label.setStyleSheet("""
                color: #1a73e8; 
                margin-bottom: 10px;
                padding-bottom: 5px;
                border-bottom: 2px solid #e8f0fe;
            """)
            layout.addWidget(title_label)

        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)


class OptimizationWorker(QThread):
    """Background worker for DFS optimization with better error handling"""

    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)

    def __init__(self, dk_file, dff_file, manual_input, contest_type, strategy_index):
        super().__init__()
        self.dk_file = dk_file
        self.dff_file = dff_file
        self.manual_input = manual_input
        self.contest_type = contest_type
        self.strategy_index = strategy_index
        self.is_cancelled = False

    def run(self):
        """Enhanced optimization with unified pipeline"""
        try:
            self.status_signal.emit("Starting optimization...")
            self.progress_signal.emit(10)

            if self.is_cancelled:
                return

            # Strategy mapping
            strategy_mapping = {
                0: 'smart_confirmed',  # Smart Default (RECOMMENDED)
                1: 'confirmed_only',  # Safe Only
                2: 'confirmed_plus_manual',  # Smart + Picks
                3: 'confirmed_pitchers_all_batters',  # Balanced
                4: 'manual_only'  # Manual Only
            }

            strategy_name = strategy_mapping.get(self.strategy_index, 'smart_confirmed')
            self.output_signal.emit(f"🎯 Using strategy: {strategy_name}")

            # Validate Manual Only requirements
            if strategy_name == 'manual_only':
                if not self.manual_input or not self.manual_input.strip():
                    self.finished_signal.emit(False, "Manual Only strategy requires player names", {})
                    return

                manual_count = len([name.strip() for name in self.manual_input.split(',') if name.strip()])
                if manual_count < 8:
                    error_msg = f"Manual Only needs 8+ players for all positions, you provided {manual_count}"
                    self.finished_signal.emit(False, error_msg, {})
                    return

            self.status_signal.emit("Loading and processing data...")
            self.progress_signal.emit(30)

            # Run the complete pipeline
            lineup, score, summary = load_and_optimize_complete_pipeline(
                dk_file=self.dk_file,
                dff_file=self.dff_file,
                manual_input=self.manual_input,
                contest_type=self.contest_type,
                strategy=strategy_name
            )

            self.progress_signal.emit(90)

            if lineup and score > 0:
                # Extract lineup data for display
                lineup_data = {
                    'players': [],
                    'total_salary': 0,
                    'total_score': score,
                    'summary': summary
                }

                # Count special players
                confirmed_count = 0
                manual_count = 0

                for player in lineup:
                    player_info = {
                        'position': player.primary_position,
                        'name': player.name,
                        'team': player.team,
                        'salary': player.salary,
                        'score': player.enhanced_score,
                        'status': player.get_status_string()
                    }
                    lineup_data['players'].append(player_info)
                    lineup_data['total_salary'] += player.salary

                    if getattr(player, 'is_confirmed', False):
                        confirmed_count += 1
                    if getattr(player, 'is_manual_selected', False):
                        manual_count += 1

                lineup_data['confirmed_count'] = confirmed_count
                lineup_data['manual_count'] = manual_count
                lineup_data['strategy_used'] = strategy_name

                self.progress_signal.emit(100)
                self.status_signal.emit("Complete!")
                self.finished_signal.emit(True, summary, lineup_data)
            else:
                error_msg = "No valid lineup found"
                if strategy_name == 'confirmed_only':
                    error_msg += "\n💡 Try 'Smart Default' for more player options"
                elif strategy_name == 'manual_only':
                    error_msg += "\n💡 Make sure you have enough players for all positions"
                self.finished_signal.emit(False, error_msg, {})

        except Exception as e:
            import traceback
            error_msg = f"Optimization failed: {str(e)}"
            self.output_signal.emit(f"❌ {error_msg}")
            self.output_signal.emit(f"Debug info: {traceback.format_exc()}")
            self.finished_signal.emit(False, error_msg, {})

    def cancel(self):
        self.is_cancelled = True


class EnhancedDFSGUI(QMainWindow):
    """Enhanced DFS GUI with improved fonts and user experience"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Enhanced DFS Optimizer Pro")
        self.setMinimumSize(1400, 900)

        # Set better default font
        font = QFont("Segoe UI", 10)
        self.setFont(font)

        # Data
        self.dk_file = ""
        self.dff_file = ""
        self.worker = None

        self.setup_ui()
        self.apply_modern_styles()
        self.show_welcome_message()

        print("✅ Enhanced DFS GUI initialized")

    def setup_ui(self):
        """Setup the user interface with improved layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout with better spacing
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Modern header
        self.create_header(layout)

        # Tab widget with improved styling
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Segoe UI", 11, QFont.Bold))

        # Create tabs
        self.tab_widget.addTab(self.create_setup_tab(), "📁 Data Setup")
        self.tab_widget.addTab(self.create_optimize_tab(), "🚀 Optimize")
        self.tab_widget.addTab(self.create_results_tab(), "📊 Results")

        layout.addWidget(self.tab_widget)

        # Modern status bar
        self.status_bar = QStatusBar()
        self.status_bar.setFont(QFont("Segoe UI", 9))
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Select DraftKings CSV to begin")

    def create_header(self, layout):
        """Create modern header section"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a73e8, stop:1 #4285f4);
                border-radius: 15px;
                margin-bottom: 10px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 20, 30, 20)

        # Main title
        title = QLabel("🚀 Enhanced DFS Optimizer Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setStyleSheet("color: white; margin-bottom: 5px;")
        header_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Advanced MLB DFS Optimization with MILP & Multi-Position Support")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #e8f0fe; margin-bottom: 10px;")
        header_layout.addWidget(subtitle)

        # Feature highlights
        features = QLabel(
            "✅ MILP Optimization  •  ✅ Multi-Position Players  •  ✅ DFF Integration  •  ✅ Real Statcast Data")
        features.setAlignment(Qt.AlignCenter)
        features.setFont(QFont("Segoe UI", 10))
        features.setStyleSheet("color: #e8f0fe;")
        header_layout.addWidget(features)

        layout.addWidget(header_frame)

    def create_setup_tab(self):
        """Create the setup tab with improved layout"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)

        # DraftKings file section
        dk_card = ModernCardWidget("📁 DraftKings CSV File")

        dk_file_layout = QHBoxLayout()
        self.dk_label = QLabel("No file selected")
        self.dk_label.setFont(QFont("Segoe UI", 11))
        self.dk_label.setStyleSheet("""
            color: #5f6368; 
            padding: 12px; 
            border: 2px dashed #dadce0; 
            border-radius: 8px;
            background: #f8f9fa;
        """)

        dk_btn = QPushButton("📁 Browse Files")
        dk_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        dk_btn.clicked.connect(self.select_dk_file)
        dk_btn.setFixedSize(140, 45)

        dk_file_layout.addWidget(self.dk_label, 1)
        dk_file_layout.addWidget(dk_btn)
        dk_card.add_layout(dk_file_layout)

        # Enhanced instructions
        instructions = QLabel("""
        <div style="line-height: 1.6;">
        <h3 style="color: #1a73e8; margin-bottom: 15px;">📋 Quick Start Guide:</h3>
        <ol style="margin-left: 20px;">
        <li style="margin-bottom: 8px;"><b>Export from DraftKings:</b> Go to your contest and click "Export to CSV"</li>
        <li style="margin-bottom: 8px;"><b>Select the file:</b> Use the browse button above to select your CSV file</li>
        <li style="margin-bottom: 8px;"><b>Optional Enhancement:</b> Upload DFF expert rankings for better results</li>
        <li style="margin-bottom: 8px;"><b>Optimize:</b> Go to the Optimize tab and generate your optimal lineup</li>
        </ol>
        </div>
        """)
        instructions.setWordWrap(True)
        instructions.setFont(QFont("Segoe UI", 11))
        instructions.setStyleSheet("""
            background: #e8f5e8; 
            padding: 20px; 
            border-radius: 10px; 
            border-left: 4px solid #34a853;
            margin-top: 15px;
        """)
        dk_card.add_widget(instructions)

        layout.addWidget(dk_card)

        # DFF file section
        dff_card = ModernCardWidget("🎯 DFF Expert Rankings (Optional)")

        dff_file_layout = QHBoxLayout()
        self.dff_label = QLabel("No DFF file selected")
        self.dff_label.setFont(QFont("Segoe UI", 11))
        self.dff_label.setStyleSheet("""
            color: #5f6368; 
            padding: 12px; 
            border: 2px dashed #dadce0; 
            border-radius: 8px;
            background: #f8f9fa;
        """)

        dff_btn = QPushButton("📊 Browse DFF CSV")
        dff_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        dff_btn.clicked.connect(self.select_dff_file)
        dff_btn.setFixedSize(140, 45)

        dff_file_layout.addWidget(self.dff_label, 1)
        dff_file_layout.addWidget(dff_btn)
        dff_card.add_layout(dff_file_layout)

        # DFF benefits
        dff_info = QLabel("""
        <div style="line-height: 1.6;">
        <h4 style="color: #f57c00; margin-bottom: 10px;">💡 DFF Integration Benefits:</h4>
        <ul style="margin-left: 20px;">
        <li>Expert rankings boost player scores automatically</li>
        <li>Enhanced name matching with 95%+ success rate</li>
        <li>Vegas lines and confirmed lineup data integration</li>
        <li>Recent form analysis using L5 game averages</li>
        </ul>
        </div>
        """)
        dff_info.setWordWrap(True)
        dff_info.setFont(QFont("Segoe UI", 11))
        dff_info.setStyleSheet("""
            background: #fff8e1; 
            padding: 20px; 
            border-radius: 10px; 
            border-left: 4px solid #ff9800;
            margin-top: 15px;
        """)
        dff_card.add_widget(dff_info)

        layout.addWidget(dff_card)

        # Test data section
        test_card = ModernCardWidget("🧪 Test with Sample Data")

        test_btn = QPushButton("🧪 Load Sample MLB Data")
        test_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        test_btn.clicked.connect(self.use_sample_data)
        test_btn.setFixedHeight(50)
        test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4285f4, stop:1 #1a73e8);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5094f5, stop:1 #2b7de9);
            }
        """)
        test_card.add_widget(test_btn)

        test_info = QLabel("Use realistic sample MLB data to test the optimizer with multi-position players")
        test_info.setFont(QFont("Segoe UI", 10))
        test_info.setStyleSheet("color: #5f6368; font-style: italic; margin-top: 10px;")
        test_info.setAlignment(Qt.AlignCenter)
        test_card.add_widget(test_info)

        layout.addWidget(test_card)

        layout.addStretch()
        return tab

    def create_optimize_tab(self):
        """Create the optimize tab with improved settings"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)

        # Settings card
        settings_card = ModernCardWidget("⚙️ Optimization Settings")
        settings_form = QFormLayout()
        settings_form.setSpacing(15)

        # Contest type
        self.contest_combo = QComboBox()
        self.contest_combo.setFont(QFont("Segoe UI", 11))
        self.contest_combo.addItems([
            "🏆 Classic Contest (10 players)",
            "⚡ Showdown Contest (6 players)"
        ])
        settings_form.addRow("Contest Type:", self.contest_combo)

        # Strategy selection with clear descriptions
        strategy_label = QLabel("Player Selection Strategy:")
        strategy_label.setFont(QFont("Segoe UI", 11, QFont.Bold))

        self.strategy_combo = QComboBox()
        self.strategy_combo.setFont(QFont("Segoe UI", 11))
        self.strategy_combo.addItems([
            "🎯 Smart Default (Confirmed + Enhanced Data) - RECOMMENDED",
            "🔒 Safe Only (Confirmed Players Only)",
            "🎯 Smart + Manual (Confirmed + Your Picks)",
            "⚖️ Balanced (Confirmed Pitchers + All Batters)",
            "✏️ Manual Only (Your Specified Players)"
        ])
        settings_form.addRow(strategy_label, self.strategy_combo)

        # Manual players input
        manual_label = QLabel("Manual Player Selection:")
        manual_label.setFont(QFont("Segoe UI", 11, QFont.Bold))

        self.manual_input = QLineEdit()
        self.manual_input.setFont(QFont("Segoe UI", 11))
        self.manual_input.setPlaceholderText(
            "Enter player names separated by commas (e.g., Aaron Judge, Shohei Ohtani, Mookie Betts)")
        settings_form.addRow(manual_label, self.manual_input)

        settings_card.add_layout(settings_form)

        # Strategy explanation
        strategy_info = QLabel("""
        <div style="line-height: 1.6;">
        <h4 style="color: #1a73e8; margin-bottom: 10px;">📋 Strategy Guide:</h4>
        <p><b>🎯 Smart Default:</b> Uses confirmed starters + enhanced data + your manual picks (Best for most users)</p>
        <p><b>🔒 Safe Only:</b> Only confirmed starting players + manual picks (Safest but limited)</p>
        <p><b>⚖️ Balanced:</b> Confirmed pitchers + all available batters (Good compromise)</p>
        <p><b>✏️ Manual Only:</b> Only uses players you specify (Requires 8+ players for all positions)</p>
        </div>
        """)
        strategy_info.setWordWrap(True)
        strategy_info.setFont(QFont("Segoe UI", 10))
        strategy_info.setStyleSheet("""
            background: #f0f4ff; 
            padding: 15px; 
            border-radius: 8px; 
            border-left: 3px solid #4285f4;
            margin-top: 15px;
        """)
        settings_card.add_widget(strategy_info)

        layout.addWidget(settings_card)

        # Optimization control card
        control_card = ModernCardWidget("🚀 Generate Lineup")

        self.run_btn = QPushButton("🚀 Generate Optimal Lineup")
        self.run_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.run_btn.setMinimumHeight(60)
        self.run_btn.clicked.connect(self.run_optimization)
        self.run_btn.setEnabled(False)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34a853, stop:1 #137333);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #46b566, stop:1 #1e8e3e);
            }
            QPushButton:disabled {
                background: #9aa0a6;
                color: #e8eaed;
            }
        """)
        control_card.add_widget(self.run_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(QFont("Segoe UI", 10))
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e8eaed;
                border-radius: 8px;
                text-align: center;
                background: white;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4285f4, stop:1 #1a73e8);
                border-radius: 6px;
            }
        """)
        control_card.add_widget(self.progress_bar)

        # Cancel button
        self.cancel_btn = QPushButton("❌ Cancel Optimization")
        self.cancel_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self.cancel_optimization)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #ea4335;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: #d73527;
            }
        """)
        control_card.add_widget(self.cancel_btn)

        layout.addWidget(control_card)

        # Console output card
        console_card = ModernCardWidget("📋 Optimization Log")

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(350)
        self.console.setFont(QFont("Consolas", 10))
        self.console.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                padding: 15px;
                selection-background-color: #264f78;
            }
        """)
        console_card.add_widget(self.console)

        layout.addWidget(console_card)

        return tab

    def create_results_tab(self):
        """Create the results tab with improved display"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)

        # Results summary card
        summary_card = ModernCardWidget("📊 Lineup Summary")

        self.results_summary = QLabel("No optimization results yet")
        self.results_summary.setFont(QFont("Segoe UI", 11))
        self.results_summary.setWordWrap(True)
        self.results_summary.setStyleSheet("""
            color: #5f6368; 
            font-style: italic; 
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        """)
        summary_card.add_widget(self.results_summary)

        layout.addWidget(summary_card)

        # Lineup table card
        table_card = ModernCardWidget("💰 Optimized Lineup")

        self.lineup_table = QTableWidget()
        self.lineup_table.setColumnCount(6)
        self.lineup_table.setHorizontalHeaderLabels([
            "Position", "Player", "Team", "Salary", "Score", "Status"
        ])

        # Enhanced table styling
        self.lineup_table.setFont(QFont("Segoe UI", 10))
        self.lineup_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e8eaed;
                background: white;
                border: 1px solid #dadce0;
                border-radius: 8px;
                selection-background-color: #e8f0fe;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #f1f3f4;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e8eaed);
                padding: 12px 8px;
                border: none;
                border-right: 1px solid #dadce0;
                font-weight: bold;
                color: #3c4043;
            }
        """)

        # Configure table
        header = self.lineup_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Player name column

        table_card.add_widget(self.lineup_table)
        layout.addWidget(table_card)

        # DraftKings import card
        import_card = ModernCardWidget("📋 DraftKings Import")

        self.import_text = QTextEdit()
        self.import_text.setMaximumHeight(120)
        self.import_text.setFont(QFont("Consolas", 11))
        self.import_text.setPlaceholderText("Optimized lineup will appear here for copy/paste into DraftKings")
        self.import_text.setStyleSheet("""
            QTextEdit {
                background: #f8f9fa;
                border: 2px dashed #dadce0;
                border-radius: 8px;
                padding: 15px;
                color: #3c4043;
            }
            QTextEdit:focus {
                border: 2px solid #4285f4;
                background: white;
            }
        """)
        import_card.add_widget(self.import_text)

        # Copy button
        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        copy_btn.clicked.connect(self.copy_to_clipboard)
        copy_btn.setStyleSheet("""
            QPushButton {
                background: #4285f4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background: #3367d6;
            }
        """)
        import_card.add_widget(copy_btn)

        layout.addWidget(import_card)

        return tab

    def apply_modern_styles(self):
        """Apply modern styling throughout the application"""
        self.setStyleSheet("""
            QMainWindow {
                background: #f8f9fa;
            }

            QTabWidget::pane {
                border: 1px solid #dadce0;
                border-radius: 8px;
                background: white;
                margin-top: 5px;
            }

            QTabBar::tab {
                background: #f1f3f4;
                color: #5f6368;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                min-width: 120px;
            }

            QTabBar::tab:selected {
                background: white;
                color: #1a73e8;
                border-bottom: 3px solid #4285f4;
            }

            QTabBar::tab:hover:!selected {
                background: #e8f0fe;
                color: #1a73e8;
            }

            QComboBox {
                padding: 10px 15px;
                border: 2px solid #dadce0;
                border-radius: 8px;
                background: white;
                font-size: 11px;
                min-height: 20px;
            }

            QComboBox:focus {
                border-color: #4285f4;
            }

            QComboBox::drop-down {
                border: none;
                padding-right: 15px;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #5f6368;
            }

            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #dadce0;
                border-radius: 8px;
                background: white;
                font-size: 11px;
                min-height: 20px;
            }

            QLineEdit:focus {
                border-color: #4285f4;
                background: #fefefe;
            }

            QStatusBar {
                background: #f1f3f4;
                border: none;
                padding: 8px 15px;
                color: #5f6368;
            }
        """)

    def show_welcome_message(self):
        """Show enhanced welcome message"""
        welcome = [
            "🚀 ENHANCED DFS OPTIMIZER PRO",
            "=" * 50,
            "",
            "✨ PREMIUM FEATURES:",
            "  • MILP optimization for maximum accuracy and consistency",
            "  • Multi-position player support (3B/SS, 1B/3B, etc.)",
            "  • DFF expert rankings integration with 95%+ match rate",
            "  • Manual player selection with strategy flexibility",
            "  • Real-time confirmed lineup detection",
            "  • Baseball Savant Statcast data integration",
            "",
            "📋 GETTING STARTED:",
            "  1. Go to 'Data Setup' tab and select your DraftKings CSV file",
            "  2. Optionally upload DFF expert rankings for enhanced results",
            "  3. Switch to 'Optimize' tab and configure your strategy",
            "  4. Click 'Generate Optimal Lineup' and view results",
            "",
            "🎯 STRATEGY RECOMMENDATIONS:",
            "  • Use 'Smart Default' for best overall results",
            "  • Use 'Safe Only' for confirmed starters only",
            "  • Add manual players for specific targeting",
            "",
            "💡 Ready to create your winning lineup!",
            ""
        ]
        self.console.setPlainText("\n".join(welcome))

    def select_dk_file(self):
        """Select DraftKings CSV file with improved feedback"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DraftKings CSV File", "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            self.dk_file = file_path
            filename = os.path.basename(file_path)
            self.dk_label.setText(f"✅ {filename}")
            self.dk_label.setStyleSheet("""
                color: #137333; 
                font-weight: bold; 
                padding: 12px; 
                border: 2px solid #34a853; 
                border-radius: 8px;
                background: #e8f5e8;
            """)
            self.run_btn.setEnabled(True)
            self.status_bar.showMessage(f"✅ DraftKings file loaded: {filename}")

            # Update console
            self.console.append(f"📁 DraftKings file selected: {filename}")
            self.console.append("✅ Ready to optimize! Go to the Optimize tab.")

    def select_dff_file(self):
        """Select DFF CSV file with improved feedback"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DFF Rankings CSV", "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            self.dff_file = file_path
            filename = os.path.basename(file_path)
            self.dff_label.setText(f"✅ {filename}")
            self.dff_label.setStyleSheet("""
                color: #b8860b; 
                font-weight: bold; 
                padding: 12px; 
                border: 2px solid #ff9800; 
                border-radius: 8px;
                background: #fff8e1;
            """)
            self.status_bar.showMessage(f"✅ DFF file loaded: {filename}")

            # Update console
            self.console.append(f"📊 DFF file selected: {filename}")
            self.console.append("🎯 Expert rankings will boost player scoring!")

    def use_sample_data(self):
        """Load sample data with enhanced user feedback"""
        try:
            self.console.append("🧪 Loading sample MLB data...")

            dk_file, dff_file = create_enhanced_test_data()
            self.dk_file = dk_file
            self.dff_file = dff_file

            self.dk_label.setText("✅ Sample DraftKings data loaded")
            self.dk_label.setStyleSheet("""
                color: #137333; 
                font-weight: bold; 
                padding: 12px; 
                border: 2px solid #34a853; 
                border-radius: 8px;
                background: #e8f5e8;
            """)

            self.dff_label.setText("✅ Sample DFF data loaded")
            self.dff_label.setStyleSheet("""
                color: #b8860b; 
                font-weight: bold; 
                padding: 12px; 
                border: 2px solid #ff9800; 
                border-radius: 8px;
                background: #fff8e1;
            """)

            self.run_btn.setEnabled(True)
            self.status_bar.showMessage("✅ Sample data loaded - ready to optimize")

            # Pre-fill manual players for demo
            self.manual_input.setText("Jorge Polanco, Christian Yelich")

            # Enhanced success message
            QMessageBox.information(self, "Sample Data Loaded Successfully!",
                                    "✅ <b>Sample MLB Data Loaded!</b><br><br>"
                                    "📊 <b>Includes:</b><br>"
                                    "• 29 realistic MLB players with proper salary ranges<br>"
                                    "• Multi-position players (3B/SS, 1B/3B)<br>"
                                    "• DFF expert rankings and projections<br>"
                                    "• Confirmed lineup data<br>"
                                    "• Manual player selections pre-filled<br><br>"
                                    "🚀 <b>Next Step:</b> Go to the Optimize tab to generate your lineup!")

            # Update console
            self.console.append("✅ Sample data loaded successfully!")
            self.console.append("📊 29 players loaded with multi-position support")
            self.console.append("🎯 DFF expert rankings included")
            self.console.append("📝 Manual players: Jorge Polanco, Christian Yelich")
            self.console.append("")
            self.console.append("🚀 Ready to optimize! Switch to the Optimize tab.")

        except Exception as e:
            QMessageBox.critical(self, "Error Loading Sample Data",
                                 f"❌ Failed to load sample data:<br><br>{str(e)}")
            self.console.append(f"❌ Error loading sample data: {e}")

    def run_optimization(self):
        """Run optimization with enhanced UI feedback"""
        if self.worker and self.worker.isRunning():
            return

        # Get settings
        strategy_index = self.strategy_combo.currentIndex()
        manual_input = self.manual_input.text().strip()
        contest_type = 'classic' if self.contest_combo.currentIndex() == 0 else 'showdown'

        # Update UI for running state
        self.run_btn.setEnabled(False)
        self.run_btn.setText("⏳ Optimizing Your Lineup...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.cancel_btn.setVisible(True)

        # Clear and start console
        self.console.clear()
        self.console.append("🚀 Starting Enhanced DFS Optimization...")
        self.console.append("=" * 60)

        # Create and start worker
        self.worker = OptimizationWorker(
            dk_file=self.dk_file,
            dff_file=self.dff_file,
            manual_input=manual_input,
            contest_type=contest_type,
            strategy_index=strategy_index
        )

        # Connect signals
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.status_signal.connect(self.status_bar.showMessage)
        self.worker.output_signal.connect(self.console.append)
        self.worker.finished_signal.connect(self.optimization_finished)
        self.worker.start()

    def cancel_optimization(self):
        """Cancel running optimization"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)
            self.optimization_finished(False, "Cancelled by user", {})

    def optimization_finished(self, success, result, lineup_data):
        """Handle optimization completion with enhanced feedback"""
        # Reset UI
        self.run_btn.setEnabled(True)
        self.run_btn.setText("🚀 Generate Optimal Lineup")
        self.progress_bar.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.status_bar.showMessage("Ready")

        if success:
            self.console.append("\n🎉 OPTIMIZATION COMPLETED SUCCESSFULLY!")
            self.console.append("=" * 60)
            self.console.append(result)

            # Update results tab
            if lineup_data and isinstance(lineup_data, dict):
                self.update_results(lineup_data)

                # Switch to results tab automatically
                self.tab_widget.setCurrentIndex(2)
                self.status_bar.showMessage("✅ Optimization complete! Check Results tab for your optimal lineup.")

                # Show success notification
                QMessageBox.information(self, "Optimization Complete!",
                                        f"🎉 <b>Success!</b><br><br>"
                                        f"Your optimal lineup has been generated!<br><br>"
                                        f"📊 <b>Results:</b><br>"
                                        f"• Total Salary: ${lineup_data.get('total_salary', 0):,}<br>"
                                        f"• Projected Score: {lineup_data.get('total_score', 0):.2f} points<br>"
                                        f"• Strategy Used: {lineup_data.get('strategy_used', 'Unknown')}<br><br>"
                                        f"🔍 Check the Results tab for detailed analysis!")
            else:
                self.console.append("⚠️ Results data incomplete, but optimization succeeded")

        else:
            self.console.append(f"\n❌ OPTIMIZATION FAILED")
            self.console.append(f"Error: {result}")
            self.status_bar.showMessage("❌ Optimization failed - check console for details")

            # Show error dialog with helpful suggestions
            QMessageBox.critical(self, "Optimization Failed",
                                 f"❌ <b>The optimization failed:</b><br><br>"
                                 f"{result}<br><br>"
                                 f"💡 <b>Suggestions:</b><br>"
                                 f"• Try a different strategy (Smart Default recommended)<br>"
                                 f"• Check that your CSV file is valid<br>"
                                 f"• For Manual Only, ensure you have 8+ players<br>"
                                 f"• Try using sample data to test the system")

    def update_results(self, lineup_data):
        """Update results tab with enhanced display"""
        try:
            # Extract data
            total_salary = lineup_data.get('total_salary', 0)
            total_score = lineup_data.get('total_score', 0)
            players = lineup_data.get('players', [])
            confirmed_count = lineup_data.get('confirmed_count', 0)
            manual_count = lineup_data.get('manual_count', 0)
            strategy_used = lineup_data.get('strategy_used', 'unknown')

            # Create enhanced summary
            summary_html = f"""
            <div style="line-height: 1.8; font-family: Segoe UI;">
                <h2 style="color: #1a73e8; margin-bottom: 20px;">📊 Optimization Results</h2>

                <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h3 style="color: #137333; margin-bottom: 10px;">💰 Financial Summary</h3>
                    <p><b>Total Salary:</b> ${total_salary:,} / $50,000</p>
                    <p><b>Salary Remaining:</b> ${50000 - total_salary:,}</p>
                    <p><b>Projected Score:</b> {total_score:.2f} points</p>
                </div>

                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h3 style="color: #1a73e8; margin-bottom: 10px;">🎯 Strategy Analysis</h3>
                    <p><b>Strategy Used:</b> {strategy_used.replace('_', ' ').title()}</p>
                    <p><b>Total Players:</b> {len(players)}</p>
                    <p><b>Confirmed Players:</b> {confirmed_count} ✅</p>
                    <p><b>Manual Selections:</b> {manual_count} 📝</p>
                </div>

                <div style="background: #fff8e1; padding: 15px; border-radius: 8px;">
                    <h3 style="color: #f57c00; margin-bottom: 10px;">🏆 Lineup Quality</h3>
                    <p><b>Average Salary:</b> ${total_salary // len(players):,} per player</p>
                    <p><b>Score per $1000:</b> {(total_score / (total_salary / 1000)):.2f}</p>
                    <p><b>Optimization Status:</b> <span style="color: #137333;">✅ Optimal Solution Found</span></p>
                </div>
            </div>
            """

            self.results_summary.setText(summary_html)

            # Update lineup table
            if hasattr(self, 'lineup_table'):
                self.lineup_table.setRowCount(len(players))

                for row, player in enumerate(players):
                    # Position
                    pos_item = QTableWidgetItem(player.get('position', ''))
                    pos_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                    pos_item.setTextAlignment(Qt.AlignCenter)
                    self.lineup_table.setItem(row, 0, pos_item)

                    # Player name
                    name_item = QTableWidgetItem(player.get('name', ''))
                    name_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                    self.lineup_table.setItem(row, 1, name_item)

                    # Team
                    team_item = QTableWidgetItem(player.get('team', ''))
                    team_item.setFont(QFont("Segoe UI", 10))
                    team_item.setTextAlignment(Qt.AlignCenter)
                    self.lineup_table.setItem(row, 2, team_item)

                    # Salary
                    salary_item = QTableWidgetItem(f"${player.get('salary', 0):,}")
                    salary_item.setFont(QFont("Segoe UI", 10))
                    salary_item.setTextAlignment(Qt.AlignRight)
                    self.lineup_table.setItem(row, 3, salary_item)

                    # Score
                    score_item = QTableWidgetItem(f"{player.get('score', 0):.1f}")
                    score_item.setFont(QFont("Segoe UI", 10))
                    score_item.setTextAlignment(Qt.AlignCenter)
                    self.lineup_table.setItem(row, 4, score_item)

                    # Status
                    status_item = QTableWidgetItem(player.get('status', ''))
                    status_item.setFont(QFont("Segoe UI", 9))
                    self.lineup_table.setItem(row, 5, status_item)

                # Auto-resize columns
                self.lineup_table.resizeColumnsToContents()
                self.lineup_table.horizontalHeader().setStretchLastSection(True)

            # Update import text
            if hasattr(self, 'import_text'):
                player_names = [p.get('name', '') for p in players]
                import_string = ", ".join(player_names)
                self.import_text.setPlainText(import_string)

            print(f"✅ Results updated: {len(players)} players, ${total_salary:,}, {total_score:.2f} pts")

        except Exception as e:
            print(f"❌ Error updating results: {e}")
            import traceback
            traceback.print_exc()

    def copy_to_clipboard(self):
        """Copy lineup to clipboard with enhanced feedback"""
        text = self.import_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

            # Enhanced feedback
            self.status_bar.showMessage("✅ Lineup copied to clipboard successfully!", 3000)

            # Success notification
            QMessageBox.information(self, "Copied Successfully!",
                                    "📋 <b>Lineup copied to clipboard!</b><br><br>"
                                    "You can now paste this directly into DraftKings:<br><br>"
                                    "1. Go to your DraftKings contest<br>"
                                    "2. Click in the player search box<br>"
                                    "3. Press Ctrl+V (or Cmd+V on Mac) to paste<br>"
                                    "4. The lineup will auto-populate!<br><br>"
                                    "🚀 <b>Good luck with your lineup!</b>")
        else:
            QMessageBox.warning(self, "No Lineup Available",
                                "❌ <b>No lineup to copy</b><br><br>"
                                "Please generate an optimal lineup first by going to the Optimize tab.")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Enhanced DFS Optimizer Pro")
    app.setApplicationVersion("2.0")

    # Set application icon if available
    try:
        app.setWindowIcon(QIcon("dfs_icon.png"))
    except:
        pass

    # Check if core is available
    if not CORE_AVAILABLE:
        QMessageBox.critical(None, "Missing Core Module",
                             "❌ <b>Could not import optimized_dfs_core.py</b><br><br>"
                             "Make sure the following files are in the same directory:<br>"
                             "• optimized_dfs_core.py<br>"
                             "• enhanced_dfs_gui.py<br><br>"
                             "Please check the file locations and try again.")
        return 1

    # Create and show the main window
    window = EnhancedDFSGUI()
    window.show()
    window.raise_()
    window.activateWindow()

    print("✅ Enhanced DFS GUI launched successfully!")
    print("🎯 Features: Modern UI, MILP optimization, multi-position support")
    print("🚀 Ready for professional DFS optimization!")

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())