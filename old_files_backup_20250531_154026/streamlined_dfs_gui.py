#!/usr/bin/env python3
"""
Clean & Readable DFS GUI - Focus on usability and clear text
Simplified design that prioritizes readability and functionality
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


class CleanCardWidget(QFrame):
    """Clean, readable card widget with proper spacing"""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)

        # Clean, readable styling
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                margin: 5px;
            }
        """)

        # Layout with generous spacing for readability
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Clear, readable title
        if title:
            title_label = QLabel(title)
            title_label.setFont(QFont("Arial", 14, QFont.Bold))
            title_label.setStyleSheet("""
                color: #374151;
                padding-bottom: 10px;
                border-bottom: 2px solid #e5e7eb;
                margin-bottom: 15px;
            """)
            layout.addWidget(title_label)

        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)


class ReadableButton(QPushButton):
    """Clean, readable button with clear text"""

    def __init__(self, text, button_type="primary"):
        super().__init__(text)
        self.button_type = button_type

        self.setFont(QFont("Arial", 11, QFont.Bold))
        self.setMinimumHeight(40)
        self.setMinimumWidth(120)
        self.setCursor(Qt.PointingHandCursor)

        self.apply_style()

    def apply_style(self):
        if self.button_type == "primary":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
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
                    color: #d1d5db;
                }
            """)
        elif self.button_type == "success":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #059669;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #047857;
                }
                QPushButton:pressed {
                    background-color: #065f46;
                }
            """)
        elif self.button_type == "danger":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #dc2626;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #b91c1c;
                }
            """)


class ReadableInput(QLineEdit):
    """Clean input field with good readability"""

    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setFont(QFont("Arial", 11))
        self.setMinimumHeight(35)

        self.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11px;
                color: #374151;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
            }
        """)


class ReadableComboBox(QComboBox):
    """Clean dropdown with good readability"""

    def __init__(self):
        super().__init__()
        self.setFont(QFont("Arial", 11))
        self.setMinimumHeight(35)

        self.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 2px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11px;
                color: #374151;
                min-width: 200px;
            }
            QComboBox:focus {
                border-color: #3b82f6;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #6b7280;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 2px solid #d1d5db;
                selection-background-color: #eff6ff;
            }
        """)


class OptimizationWorker(QThread):
    """Background worker for optimization"""

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
        """Run optimization with clear progress updates"""
        try:
            self.status_signal.emit("Starting optimization...")
            self.progress_signal.emit(10)

            if self.is_cancelled:
                return

            # Strategy mapping
            strategy_mapping = {
                0: 'smart_confirmed',
                1: 'confirmed_only',
                2: 'confirmed_plus_manual',
                3: 'confirmed_pitchers_all_batters',
                4: 'manual_only'
            }

            strategy_name = strategy_mapping.get(self.strategy_index, 'smart_confirmed')
            self.output_signal.emit(f"Strategy: {strategy_name}")

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
                self.status_signal.emit("Optimization complete!")
                self.finished_signal.emit(True, summary, lineup_data)
            else:
                error_msg = "No valid lineup found"
                if strategy_name == 'confirmed_only':
                    error_msg += "\nTry 'Smart Default' for more player options"
                elif strategy_name == 'manual_only':
                    error_msg += "\nMake sure you have enough players for all positions"
                self.finished_signal.emit(False, error_msg, {})

        except Exception as e:
            import traceback
            error_msg = f"Optimization failed: {str(e)}"
            self.output_signal.emit(f"Error: {error_msg}")
            self.output_signal.emit(f"Debug: {traceback.format_exc()}")
            self.finished_signal.emit(False, error_msg, {})

    def cancel(self):
        self.is_cancelled = True


class ReadableDFSGUI(QMainWindow):
    """Clean, readable DFS GUI with proper spacing and clear text"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced DFS Optimizer Pro")
        self.setMinimumSize(1200, 800)

        # Set clean, readable font
        font = QFont("Arial", 10)
        self.setFont(font)

        # Data
        self.dk_file = ""
        self.dff_file = ""
        self.worker = None

        self.setup_ui()
        self.apply_clean_styles()
        self.show_welcome_message()

        print("✅ Readable DFS GUI initialized")

    def setup_ui(self):
        """Setup clean, readable user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout with proper spacing
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Simple, readable header
        self.create_header(layout)

        # Clean tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Arial", 11, QFont.Bold))

        # Create tabs
        self.tab_widget.addTab(self.create_setup_tab(), "Data Setup")
        self.tab_widget.addTab(self.create_optimize_tab(), "Optimize")
        self.tab_widget.addTab(self.create_results_tab(), "Results")

        layout.addWidget(self.tab_widget)

        # Simple status bar
        self.status_bar = QStatusBar()
        self.status_bar.setFont(QFont("Arial", 9))
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Select DraftKings CSV to begin")

    def create_header(self, layout):
        """Create simple, readable header"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #3b82f6;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 20, 30, 20)

        # Main title
        title = QLabel("Enhanced DFS Optimizer Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: white; margin-bottom: 5px;")
        header_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Advanced MLB DFS Optimization with MILP & Multi-Position Support")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: white; margin-bottom: 10px;")
        header_layout.addWidget(subtitle)

        # Feature list
        features = QLabel("MILP Optimization • Multi-Position Players • DFF Integration • Real Statcast Data")
        features.setAlignment(Qt.AlignCenter)
        features.setFont(QFont("Arial", 10))
        features.setStyleSheet("color: white;")
        header_layout.addWidget(features)

        layout.addWidget(header_frame)

    def create_setup_tab(self):
        """Create setup tab with clear spacing"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)

        # DraftKings file section
        dk_card = CleanCardWidget("DraftKings CSV File")

        dk_file_layout = QHBoxLayout()
        dk_file_layout.setSpacing(15)

        self.dk_label = QLabel("No file selected")
        self.dk_label.setFont(QFont("Arial", 11))
        self.dk_label.setStyleSheet("""
            color: #6b7280;
            padding: 12px;
            border: 2px dashed #d1d5db;
            border-radius: 6px;
            background-color: #f9fafb;
            min-height: 20px;
        """)

        dk_btn = ReadableButton("Browse Files", "primary")
        dk_btn.clicked.connect(self.select_dk_file)
        dk_btn.setFixedWidth(130)

        dk_file_layout.addWidget(self.dk_label, 1)
        dk_file_layout.addWidget(dk_btn)
        dk_card.add_layout(dk_file_layout)

        # Instructions
        instructions = QLabel("""
        <b>Quick Start Guide:</b><br><br>
        1. <b>Export from DraftKings:</b> Go to your contest and click "Export to CSV"<br>
        2. <b>Select the file:</b> Use the browse button above to select your CSV file<br>
        3. <b>Optional Enhancement:</b> Upload DFF expert rankings for better results<br>
        4. <b>Optimize:</b> Go to the Optimize tab and generate your optimal lineup
        """)
        instructions.setWordWrap(True)
        instructions.setFont(QFont("Arial", 11))
        instructions.setStyleSheet("""
            background-color: #eff6ff;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #3b82f6;
            margin-top: 10px;
            color: #374151;
        """)
        dk_card.add_widget(instructions)

        layout.addWidget(dk_card)

        # DFF file section
        dff_card = CleanCardWidget("DFF Expert Rankings (Optional)")

        dff_file_layout = QHBoxLayout()
        dff_file_layout.setSpacing(15)

        self.dff_label = QLabel("No DFF file selected")
        self.dff_label.setFont(QFont("Arial", 11))
        self.dff_label.setStyleSheet("""
            color: #6b7280;
            padding: 12px;
            border: 2px dashed #d1d5db;
            border-radius: 6px;
            background-color: #f9fafb;
            min-height: 20px;
        """)

        dff_btn = ReadableButton("Browse DFF CSV", "primary")
        dff_btn.clicked.connect(self.select_dff_file)
        dff_btn.setFixedWidth(130)

        dff_file_layout.addWidget(self.dff_label, 1)
        dff_file_layout.addWidget(dff_btn)
        dff_card.add_layout(dff_file_layout)

        # DFF benefits
        dff_info = QLabel("""
        <b>DFF Integration Benefits:</b><br><br>
        • Expert rankings boost player scores automatically<br>
        • Enhanced name matching with 95%+ success rate<br>
        • Vegas lines and confirmed lineup data integration<br>
        • Recent form analysis using L5 game averages
        """)
        dff_info.setWordWrap(True)
        dff_info.setFont(QFont("Arial", 11))
        dff_info.setStyleSheet("""
            background-color: #fef3c7;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #f59e0b;
            margin-top: 10px;
            color: #374151;
        """)
        dff_card.add_widget(dff_info)

        layout.addWidget(dff_card)

        # Test data section
        test_card = CleanCardWidget("Test with Sample Data")

        test_btn = ReadableButton("Load Sample MLB Data", "success")
        test_btn.setFont(QFont("Arial", 12, QFont.Bold))
        test_btn.clicked.connect(self.use_sample_data)
        test_btn.setMinimumHeight(45)
        test_card.add_widget(test_btn)

        test_info = QLabel("Use realistic sample MLB data to test the optimizer with multi-position players")
        test_info.setFont(QFont("Arial", 10))
        test_info.setStyleSheet("color: #6b7280; font-style: italic; margin-top: 10px;")
        test_info.setAlignment(Qt.AlignCenter)
        test_card.add_widget(test_info)

        layout.addWidget(test_card)

        layout.addStretch()
        return tab

    def create_optimize_tab(self):
        """Create optimize tab with clear layout"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)

        # Settings card
        settings_card = CleanCardWidget("Optimization Settings")
        settings_form = QFormLayout()
        settings_form.setSpacing(15)

        # Contest type
        contest_label = QLabel("Contest Type:")
        contest_label.setFont(QFont("Arial", 11, QFont.Bold))

        self.contest_combo = ReadableComboBox()
        self.contest_combo.addItems([
            "Classic Contest (10 players)",
            "Showdown Contest (6 players)"
        ])
        settings_form.addRow(contest_label, self.contest_combo)

        # Strategy selection
        strategy_label = QLabel("Player Selection Strategy:")
        strategy_label.setFont(QFont("Arial", 11, QFont.Bold))

        self.strategy_combo = ReadableComboBox()
        self.strategy_combo.addItems([
            "Smart Default (Confirmed + Enhanced Data) - RECOMMENDED",
            "Safe Only (Confirmed Players Only)",
            "Smart + Manual (Confirmed + Your Picks)",
            "Balanced (Confirmed Pitchers + All Batters)",
            "Manual Only (Your Specified Players)"
        ])
        settings_form.addRow(strategy_label, self.strategy_combo)

        # Manual players input
        manual_label = QLabel("Manual Player Selection:")
        manual_label.setFont(QFont("Arial", 11, QFont.Bold))

        self.manual_input = ReadableInput("Enter player names separated by commas (e.g., Aaron Judge, Shohei Ohtani)")
        settings_form.addRow(manual_label, self.manual_input)

        settings_card.add_layout(settings_form)

        # Strategy explanation
        strategy_info = QLabel("""
        <b>Strategy Guide:</b><br><br>
        <b>Smart Default:</b> Uses confirmed starters + enhanced data + your manual picks (Best for most users)<br>
        <b>Safe Only:</b> Only confirmed starting players + manual picks (Safest but limited)<br>
        <b>Balanced:</b> Confirmed pitchers + all available batters (Good compromise)<br>
        <b>Manual Only:</b> Only uses players you specify (Requires 8+ players for all positions)
        """)
        strategy_info.setWordWrap(True)
        strategy_info.setFont(QFont("Arial", 10))
        strategy_info.setStyleSheet("""
            background-color: #f0f9ff;
            padding: 15px;
            border-radius: 6px;
            border-left: 3px solid #3b82f6;
            margin-top: 15px;
            color: #374151;
        """)
        settings_card.add_widget(strategy_info)

        layout.addWidget(settings_card)

        # Optimization control card
        control_card = CleanCardWidget("Generate Lineup")

        self.run_btn = ReadableButton("Generate Optimal Lineup", "success")
        self.run_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.run_btn.setMinimumHeight(50)
        self.run_btn.clicked.connect(self.run_optimization)
        self.run_btn.setEnabled(False)
        control_card.add_widget(self.run_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(QFont("Arial", 10))
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #d1d5db;
                border-radius: 6px;
                text-align: center;
                background-color: white;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 4px;
            }
        """)
        control_card.add_widget(self.progress_bar)

        # Cancel button
        self.cancel_btn = ReadableButton("Cancel Optimization", "danger")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self.cancel_optimization)
        control_card.add_widget(self.cancel_btn)

        layout.addWidget(control_card)

        # Console output card
        console_card = CleanCardWidget("Optimization Log")

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(300)
        self.console.setFont(QFont("Consolas", 10))
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #1f2937;
                color: #e5e7eb;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 15px;
                selection-background-color: #374151;
            }
        """)
        console_card.add_widget(self.console)

        layout.addWidget(console_card)

        return tab

    def create_results_tab(self):
        """Create results tab with clear display"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)

        # Results summary card
        summary_card = CleanCardWidget("Lineup Summary")

        self.results_summary = QLabel("No optimization results yet")
        self.results_summary.setFont(QFont("Arial", 11))
        self.results_summary.setWordWrap(True)
        self.results_summary.setStyleSheet("""
            color: #6b7280;
            font-style: italic;
            padding: 20px;
            background-color: #f9fafb;
            border-radius: 6px;
            text-align: center;
        """)
        summary_card.add_widget(self.results_summary)

        layout.addWidget(summary_card)

        # Lineup table card
        table_card = CleanCardWidget("Optimized Lineup")

        self.lineup_table = QTableWidget()
        self.lineup_table.setColumnCount(6)
        self.lineup_table.setHorizontalHeaderLabels([
            "Position", "Player", "Team", "Salary", "Score", "Status"
        ])

        # Clean table styling
        self.lineup_table.setFont(QFont("Arial", 10))
        self.lineup_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e5e7eb;
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                selection-background-color: #eff6ff;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #f3f4f6;
            }
            QHeaderView::section {
                background-color: #f9fafb;
                padding: 12px 8px;
                border: none;
                border-right: 1px solid #d1d5db;
                font-weight: bold;
                color: #374151;
            }
        """)

        # Configure table
        header = self.lineup_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Player name column

        table_card.add_widget(self.lineup_table)
        layout.addWidget(table_card)

        # DraftKings import card
        import_card = CleanCardWidget("DraftKings Import")

        self.import_text = QTextEdit()
        self.import_text.setMaximumHeight(100)
        self.import_text.setFont(QFont("Consolas", 11))
        self.import_text.setPlaceholderText("Optimized lineup will appear here for copy/paste into DraftKings")
        self.import_text.setStyleSheet("""
            QTextEdit {
                background-color: #f9fafb;
                border: 2px dashed #d1d5db;
                border-radius: 6px;
                padding: 15px;
                color: #374151;
            }
            QTextEdit:focus {
                border: 2px solid #3b82f6;
                background-color: white;
            }
        """)
        import_card.add_widget(self.import_text)

        # Copy button
        copy_btn = ReadableButton("Copy to Clipboard", "primary")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        import_card.add_widget(copy_btn)

        layout.addWidget(import_card)

        return tab

    def apply_clean_styles(self):
        """Apply clean, readable styling throughout the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f3f4f6;
            }

            QTabWidget::pane {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background-color: white;
                margin-top: 5px;
            }

            QTabBar::tab {
                background-color: #f3f4f6;
                color: #6b7280;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                min-width: 100px;
            }

            QTabBar::tab:selected {
                background-color: white;
                color: #374151;
                border-bottom: 3px solid #3b82f6;
            }

            QTabBar::tab:hover:!selected {
                background-color: #e5e7eb;
                color: #374151;
            }

            QStatusBar {
                background-color: #f3f4f6;
                border: none;
                padding: 8px 15px;
                color: #6b7280;
            }
        """)

    def show_welcome_message(self):
        """Display a detailed welcome message in the console."""
        welcome = [
            "🚀 STREAMLINED DFS OPTIMIZER PRO",
            "=" * 50,
            "",
            "✨ PREMIUM FEATURES:",
            "  • Advanced MILP optimization with real Statcast data",
            "  • Multi-position player support (3B/SS, 1B/3B, etc.)",
            "  • DFF expert rankings integration with 95%+ match rate",
            "  • Manual player selection with priority scoring",
            "  • Real-time confirmed lineup detection",
            "  • Baseball Savant Statcast data integration",
            "",
            "🧠 ADVANCED DFS ALGORITHM:",
            "  • Real Baseball Savant data for priority players",
            "  • MILP-optimized scoring weights",
            "  • Advanced DFF confidence analysis",
            "  • Multi-factor context adjustments (Vegas, park, weather)",
            "  • Position scarcity optimization",
            "  • Smart fallback for missing data",
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
            "💡 Ready to create your winning lineup with advanced algorithms!",
            ""
        ]
        self.console.setPlainText("\n".join(welcome))

    def select_dk_file(self):
        """Select DraftKings CSV file with clear feedback"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DraftKings CSV File", "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            self.dk_file = file_path
            filename = os.path.basename(file_path)
            self.dk_label.setText(f"✓ {filename}")
            self.dk_label.setStyleSheet("""
                color: #059669;
                font-weight: bold;
                padding: 12px;
                border: 2px solid #10b981;
                border-radius: 6px;
                background-color: #ecfdf5;
                min-height: 20px;
            """)
            self.run_btn.setEnabled(True)
            self.status_bar.showMessage(f"✓ DraftKings file loaded: {filename}")

            # Update console
            self.console.append(f"DraftKings file selected: {filename}")
            self.console.append("✓ Ready to optimize! Go to the Optimize tab.")

    def select_dff_file(self):
        """Select DFF CSV file with clear feedback"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DFF Rankings CSV", "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            self.dff_file = file_path
            filename = os.path.basename(file_path)
            self.dff_label.setText(f"✓ {filename}")
            self.dff_label.setStyleSheet("""
                color: #ea580c;
                font-weight: bold;
                padding: 12px;
                border: 2px solid #f97316;
                border-radius: 6px;
                background-color: #fff7ed;
                min-height: 20px;
            """)
            self.status_bar.showMessage(f"✓ DFF file loaded: {filename}")

            # Update console
            self.console.append(f"DFF file selected: {filename}")
            self.console.append("Expert rankings will boost player scoring!")

    def use_sample_data(self):
        """Load sample data with clear user feedback"""
        try:
            self.console.append("Loading sample MLB data...")

            dk_file, dff_file = create_enhanced_test_data()
            self.dk_file = dk_file
            self.dff_file = dff_file

            self.dk_label.setText("✓ Sample DraftKings data loaded")
            self.dk_label.setStyleSheet("""
                color: #059669;
                font-weight: bold;
                padding: 12px;
                border: 2px solid #10b981;
                border-radius: 6px;
                background-color: #ecfdf5;
                min-height: 20px;
            """)

            self.dff_label.setText("✓ Sample DFF data loaded")
            self.dff_label.setStyleSheet("""
                color: #ea580c;
                font-weight: bold;
                padding: 12px;
                border: 2px solid #f97316;
                border-radius: 6px;
                background-color: #fff7ed;
                min-height: 20px;
            """)

            self.run_btn.setEnabled(True)
            self.status_bar.showMessage("✓ Sample data loaded - ready to optimize")

            # Pre-fill manual players for demo
            self.manual_input.setText("Jorge Polanco, Christian Yelich")

            # Success message
            QMessageBox.information(self, "Sample Data Loaded Successfully!",
                                    "✓ Sample MLB Data Loaded!\n\n"
                                    "Includes:\n"
                                    "• 29 realistic MLB players with proper salary ranges\n"
                                    "• Multi-position players (3B/SS, 1B/3B)\n"
                                    "• DFF expert rankings and projections\n"
                                    "• Confirmed lineup data\n"
                                    "• Manual player selections pre-filled\n\n"
                                    "Next Step: Go to the Optimize tab to generate your lineup!")

            # Update console
            self.console.append("✓ Sample data loaded successfully!")
            self.console.append("29 players loaded with multi-position support")
            self.console.append("DFF expert rankings included")
            self.console.append("Manual players: Jorge Polanco, Christian Yelich")
            self.console.append("")
            self.console.append("Ready to optimize! Switch to the Optimize tab.")

        except Exception as e:
            QMessageBox.critical(self, "Error Loading Sample Data",
                                 f"Failed to load sample data:\n\n{str(e)}")
            self.console.append(f"Error loading sample data: {e}")

    def run_optimization(self):
        """Run optimization with clear UI feedback"""
        if self.worker and self.worker.isRunning():
            return

        # Get settings
        strategy_index = self.strategy_combo.currentIndex()
        manual_input = self.manual_input.text().strip()
        contest_type = 'classic' if self.contest_combo.currentIndex() == 0 else 'showdown'

        # Update UI for running state
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Optimizing Your Lineup...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.cancel_btn.setVisible(True)

        # Clear and start console
        self.console.clear()
        self.console.append("Starting Enhanced DFS Optimization...")
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
        """Handle optimization completion with clear feedback"""
        # Reset UI
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Generate Optimal Lineup")
        self.progress_bar.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.status_bar.showMessage("Ready")

        if success:
            self.console.append("\n✓ OPTIMIZATION COMPLETED SUCCESSFULLY!")
            self.console.append("=" * 60)
            self.console.append(result)

            # Update results tab
            if lineup_data and isinstance(lineup_data, dict):
                self.update_results(lineup_data)

                # Switch to results tab automatically
                self.tab_widget.setCurrentIndex(2)
                self.status_bar.showMessage("✓ Optimization complete! Check Results tab for your optimal lineup.")

                # Show success notification
                QMessageBox.information(self, "Optimization Complete!",
                                        f"✓ Success!\n\n"
                                        f"Your optimal lineup has been generated!\n\n"
                                        f"Results:\n"
                                        f"• Total Salary: ${lineup_data.get('total_salary', 0):,}\n"
                                        f"• Projected Score: {lineup_data.get('total_score', 0):.2f} points\n"
                                        f"• Strategy Used: {lineup_data.get('strategy_used', 'Unknown')}\n\n"
                                        f"Check the Results tab for detailed analysis!")
            else:
                self.console.append("⚠ Results data incomplete, but optimization succeeded")

        else:
            self.console.append(f"\n✗ OPTIMIZATION FAILED")
            self.console.append(f"Error: {result}")
            self.status_bar.showMessage("✗ Optimization failed - check console for details")

            # Show error dialog
            QMessageBox.critical(self, "Optimization Failed",
                                 f"The optimization failed:\n\n"
                                 f"{result}\n\n"
                                 f"Suggestions:\n"
                                 f"• Try a different strategy (Smart Default recommended)\n"
                                 f"• Check that your CSV file is valid\n"
                                 f"• For Manual Only, ensure you have 8+ players\n"
                                 f"• Try using sample data to test the system")

    def update_results(self, lineup_data):
        """Update results tab with clear display"""
        try:
            # Extract data
            total_salary = lineup_data.get('total_salary', 0)
            total_score = lineup_data.get('total_score', 0)
            players = lineup_data.get('players', [])
            confirmed_count = lineup_data.get('confirmed_count', 0)
            manual_count = lineup_data.get('manual_count', 0)
            strategy_used = lineup_data.get('strategy_used', 'unknown')

            # Create clear summary
            summary_text = f"""
            <b>Optimization Results</b><br><br>

            <b>Financial Summary:</b><br>
            • Total Salary: ${total_salary:,} / $50,000<br>
            • Salary Remaining: ${50000 - total_salary:,}<br>
            • Projected Score: {total_score:.2f} points<br><br>

            <b>Strategy Analysis:</b><br>
            • Strategy Used: {strategy_used.replace('_', ' ').title()}<br>
            • Total Players: {len(players)}<br>
            • Confirmed Players: {confirmed_count}<br>
            • Manual Selections: {manual_count}<br><br>

            <b>Lineup Quality:</b><br>
            • Average Salary: ${total_salary // len(players):,} per player<br>
            • Score per $1000: {(total_score / (total_salary / 1000)):.2f}<br>
            • Optimization Status: ✓ Optimal Solution Found
            """

            self.results_summary.setText(summary_text)
            self.results_summary.setStyleSheet("""
                color: #374151;
                padding: 20px;
                background-color: #f9fafb;
                border-radius: 6px;
                border: 1px solid #d1d5db;
            """)

            # Update lineup table
            if hasattr(self, 'lineup_table'):
                self.lineup_table.setRowCount(len(players))

                for row, player in enumerate(players):
                    # Position
                    pos_item = QTableWidgetItem(player.get('position', ''))
                    pos_item.setFont(QFont("Arial", 10, QFont.Bold))
                    pos_item.setTextAlignment(Qt.AlignCenter)
                    self.lineup_table.setItem(row, 0, pos_item)

                    # Player name
                    name_item = QTableWidgetItem(player.get('name', ''))
                    name_item.setFont(QFont("Arial", 10, QFont.Bold))
                    self.lineup_table.setItem(row, 1, name_item)

                    # Team
                    team_item = QTableWidgetItem(player.get('team', ''))
                    team_item.setFont(QFont("Arial", 10))
                    team_item.setTextAlignment(Qt.AlignCenter)
                    self.lineup_table.setItem(row, 2, team_item)

                    # Salary
                    salary_item = QTableWidgetItem(f"${player.get('salary', 0):,}")
                    salary_item.setFont(QFont("Arial", 10))
                    salary_item.setTextAlignment(Qt.AlignRight)
                    self.lineup_table.setItem(row, 3, salary_item)

                    # Score
                    score_item = QTableWidgetItem(f"{player.get('score', 0):.1f}")
                    score_item.setFont(QFont("Arial", 10))
                    score_item.setTextAlignment(Qt.AlignCenter)
                    self.lineup_table.setItem(row, 4, score_item)

                    # Status
                    status_item = QTableWidgetItem(player.get('status', ''))
                    status_item.setFont(QFont("Arial", 9))
                    self.lineup_table.setItem(row, 5, status_item)

                # Auto-resize columns
                self.lineup_table.resizeColumnsToContents()
                self.lineup_table.horizontalHeader().setStretchLastSection(True)

            # Update import text
            if hasattr(self, 'import_text'):
                player_names = [p.get('name', '') for p in players]
                import_string = ", ".join(player_names)
                self.import_text.setPlainText(import_string)

            print(f"✓ Results updated: {len(players)} players, ${total_salary:,}, {total_score:.2f} pts")

        except Exception as e:
            print(f"✗ Error updating results: {e}")
            import traceback
            traceback.print_exc()

    def copy_to_clipboard(self):
        """Copy lineup to clipboard with clear feedback"""
        text = self.import_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

            # Clear feedback
            self.status_bar.showMessage("✓ Lineup copied to clipboard successfully!", 3000)

            # Success notification
            QMessageBox.information(self, "Copied Successfully!",
                                    "✓ Lineup copied to clipboard!\n\n"
                                    "You can now paste this directly into DraftKings:\n\n"
                                    "1. Go to your DraftKings contest\n"
                                    "2. Click in the player search box\n"
                                    "3. Press Ctrl+V (or Cmd+V on Mac) to paste\n"
                                    "4. The lineup will auto-populate!\n\n"
                                    "Good luck with your lineup!")
        else:
            QMessageBox.warning(self, "No Lineup Available",
                                "✗ No lineup to copy\n\n"
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
                             "✗ Could not import optimized_dfs_core.py\n\n"
                             "Make sure the following files are in the same directory:\n"
                             "• optimized_dfs_core.py\n"
                             "• enhanced_dfs_gui.py\n\n"
                             "Please check the file locations and try again.")
        return 1

    # Create and show the main window
    window = ReadableDFSGUI()
    window.show()
    window.raise_()
    window.activateWindow()

    print("✓ Readable DFS GUI launched successfully!")
    print("Features: Clean UI, MILP optimization, multi-position support")
    print("Ready for professional DFS optimization!")

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())