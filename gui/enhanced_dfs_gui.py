#!/usr/bin/env python3
"""
ENHANCED DFS GUI - COMPLETE REWRITE
===================================
Works with new unified systems
"""

import sys
import os
import csv
import tempfile
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Import PyQt5
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *

    PYQT5_AVAILABLE = True
except ImportError:
    print("❌ PyQt5 not available. Install with: pip install PyQt5")
    sys.exit(1)

# Import our core systems
try:
    from core.bulletproof_dfs_core import BulletproofDFSCore, AdvancedPlayer
    from core.unified_data_system import UnifiedDataSystem
    from core.optimal_lineup_optimizer import OptimalLineupOptimizer
    from core.smart_confirmation_system import SmartConfirmationSystem

    CORE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Could not import core systems: {e}")
    CORE_AVAILABLE = False


class OptimizationThread(QThread):
    """Background thread for running optimization"""

    progress_updated = pyqtSignal(str)
    optimization_completed = pyqtSignal(list, float, str)
    optimization_failed = pyqtSignal(str)

    def __init__(self, dk_file, dff_file, manual_input, contest_type, optimization_mode):
        super().__init__()
        self.dk_file = dk_file
        self.dff_file = dff_file
        self.manual_input = manual_input
        self.contest_type = contest_type
        self.optimization_mode = optimization_mode

    def run(self):
        """Run optimization in background"""
        try:
            # Emit progress updates
            self.progress_updated.emit(f"🚀 Starting {self.optimization_mode.upper()} optimization...")

            # Create core instance
            core = BulletproofDFSCore()

            # Set contest type
            if self.contest_type == 'showdown':
                core.contest_type = 'showdown'

            # Load DraftKings data
            self.progress_updated.emit("📊 Loading DraftKings data...")
            if not core.load_draftkings_csv(self.dk_file):
                self.optimization_failed.emit("Failed to load DraftKings CSV")
                return

            # Load DFF data if available
            if self.dff_file and os.path.exists(self.dff_file):
                self.progress_updated.emit("📈 Loading DFF rankings...")
                core.load_dff_rankings(self.dff_file)

            # Set optimization mode
            core.set_optimization_mode(self.optimization_mode)

            # Apply manual selections if any
            if self.manual_input:
                self.progress_updated.emit("🎯 Applying manual selections...")
                manual_count = core.apply_manual_selection(self.manual_input)
                self.progress_updated.emit(f"✅ Applied {manual_count} manual selections")

                if self.optimization_mode == 'manual_only' and manual_count < 10:
                    self.optimization_failed.emit(
                        f"Manual-only mode requires at least 10 players. Found {manual_count}")
                    return

            # Get confirmations
            if self.optimization_mode in ['bulletproof', 'confirmed_only']:
                self.progress_updated.emit("🔍 Detecting confirmed players...")
                confirmed_count = core.detect_confirmed_players()
                self.progress_updated.emit(f"✅ Found {confirmed_count} confirmed players")

            # Run statistical analysis
            self.progress_updated.emit("📊 Running statistical analysis...")
            eligible_players = core.get_eligible_players_by_mode()

            if not eligible_players:
                self.optimization_failed.emit("No eligible players found for optimization")
                return

            self.progress_updated.emit(f"📈 Analyzing {len(eligible_players)} eligible players...")

            # Apply all enhancements
            if hasattr(core, '_apply_comprehensive_statistical_analysis'):
                core._apply_comprehensive_statistical_analysis(eligible_players)

            # Run optimization
            self.progress_updated.emit("⚡ Running optimization...")
            lineup, score = core.optimize_lineup_with_mode()

            if lineup and score > 0:
                # Create summary
                total_salary = sum(p.salary for p in lineup)
                summary = f"""
                Optimization Complete!
                Players: {len(lineup)}
                Projected Score: {score:.2f}
                Total Salary: ${total_salary:,}
                Mode: {self.optimization_mode}
                """
                self.optimization_completed.emit(lineup, score, summary.strip())
            else:
                self.optimization_failed.emit("Optimization failed - no valid lineup found")

        except Exception as e:
            self.optimization_failed.emit(f"Error during optimization: {str(e)}")


class EnhancedDFSGUI(QMainWindow):
    """Enhanced DFS GUI with all new systems integrated"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced DFS Optimizer 2.0")
        self.setMinimumSize(1200, 900)

        # Initialize data
        self.dk_file = ""
        self.dff_file = ""
        self.optimization_thread = None
        self.last_lineup = []

        # Setup UI
        self.setup_ui()
        self.show_welcome_message()
        self.auto_detect_files()

    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        self.create_header(layout)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                background: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 5px;
            }
            QTabBar::tab:selected {
                background: #1e40af;
                color: white;
            }
        """)

        self.tab_widget.addTab(self.create_setup_tab(), "⚙️ Setup")
        self.tab_widget.addTab(self.create_optimize_tab(), "🚀 Optimize")
        self.tab_widget.addTab(self.create_results_tab(), "📊 Results")

        layout.addWidget(self.tab_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Enhanced DFS Optimizer 2.0")

    def create_header(self, layout):
        """Create application header"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #1e40af, stop: 1 #3730a3);
                border-radius: 12px;
                padding: 20px;
            }
        """)

        header_layout = QVBoxLayout(header_frame)

        title = QLabel("🚀 Enhanced DFS Optimizer 2.0")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)

        subtitle = QLabel("Mathematical Optimization • Advanced Statistics • Smart Confirmations")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: white; opacity: 0.9;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header_frame)

    def create_setup_tab(self):
        """Create the setup tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # DraftKings file section
        dk_group = QGroupBox("📁 DraftKings CSV File")
        dk_layout = QVBoxLayout(dk_group)

        dk_file_layout = QHBoxLayout()
        self.dk_label = QLabel("No file selected")
        self.dk_label.setStyleSheet("padding: 10px; border: 2px dashed #ccc; border-radius: 5px;")

        dk_btn = QPushButton("Browse Files")
        dk_btn.clicked.connect(self.select_dk_file)
        dk_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e40af;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e3a8a;
            }
        """)

        dk_file_layout.addWidget(self.dk_label, 1)
        dk_file_layout.addWidget(dk_btn)
        dk_layout.addLayout(dk_file_layout)

        layout.addWidget(dk_group)

        # DFF file section
        dff_group = QGroupBox("📈 DFF Expert Rankings (Optional)")
        dff_layout = QVBoxLayout(dff_group)

        dff_file_layout = QHBoxLayout()
        self.dff_label = QLabel("No file selected (optional)")
        self.dff_label.setStyleSheet("padding: 10px; border: 2px dashed #ccc; border-radius: 5px;")

        dff_btn = QPushButton("Browse DFF")
        dff_btn.clicked.connect(self.select_dff_file)
        dff_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #047857;
            }
        """)

        dff_file_layout.addWidget(self.dff_label, 1)
        dff_file_layout.addWidget(dff_btn)
        dff_layout.addLayout(dff_file_layout)

        layout.addWidget(dff_group)

        # Manual players section
        manual_group = QGroupBox("🎯 Manual Player Selection")
        manual_layout = QVBoxLayout(manual_group)

        info = QLabel("Add players manually (comma separated). Required for Manual-Only mode.")
        info.setStyleSheet("color: #1e40af; margin-bottom: 10px;")
        manual_layout.addWidget(info)

        self.manual_input = QTextEdit()
        self.manual_input.setMaximumHeight(100)
        self.manual_input.setPlaceholderText(
            "Example: Shohei Ohtani, Mike Trout, Aaron Judge, Freddie Freeman..."
        )
        manual_layout.addWidget(self.manual_input)

        # Quick buttons
        btn_layout = QHBoxLayout()

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.manual_input.clear)
        btn_layout.addWidget(clear_btn)

        sample_btn = QPushButton("Load Sample Players")
        sample_btn.clicked.connect(self.load_sample_players)
        btn_layout.addWidget(sample_btn)

        manual_layout.addLayout(btn_layout)
        layout.addWidget(manual_group)

        # Test data section
        test_group = QGroupBox("🧪 Test Mode")
        test_layout = QVBoxLayout(test_group)

        test_btn = QPushButton("🧪 Create Test Data")
        test_btn.clicked.connect(self.use_test_data)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed;
                color: white;
                padding: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #6d28d9;
            }
        """)
        test_layout.addWidget(test_btn)

        layout.addWidget(test_group)

        layout.addStretch()
        return tab

    def create_optimize_tab(self):
        """Create the optimize tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Settings
        settings_group = QGroupBox("⚙️ Optimization Settings")
        settings_layout = QFormLayout(settings_group)

        # Contest type
        self.contest_combo = QComboBox()
        self.contest_combo.addItems(["Classic (10 players)", "Showdown (6 players)"])
        settings_layout.addRow("Contest Type:", self.contest_combo)

        # Optimization mode
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Bulletproof (All eligible players)",
            "Manual-Only (Your selections only)",
            "Confirmed-Only (Confirmed lineups only)"
        ])
        settings_layout.addRow("Mode:", self.mode_combo)

        layout.addWidget(settings_group)

        # Features info
        info_group = QGroupBox("🧠 Active Features")
        info_layout = QVBoxLayout(info_group)

        info_text = QLabel("""
        <b>Mathematical Optimization:</b> Integer programming for true optimal lineups<br>
        <b>Vegas Lines:</b> Real-time betting data integration<br>
        <b>Statcast Data:</b> Advanced baseball metrics<br>
        <b>Smart Confirmations:</b> Unified lineup detection<br>
        <b>Position Flexibility:</b> Multi-position player optimization<br>
        <b>No Artificial Boosts:</b> Pure data-driven projections
        """)
        info_text.setWordWrap(True)
        info_text.setStyleSheet("padding: 10px; background-color: #f0f9ff; border-radius: 5px;")
        info_layout.addWidget(info_text)

        layout.addWidget(info_group)

        # Run button
        self.run_btn = QPushButton("🚀 Generate Optimal Lineup")
        self.run_btn.setMinimumHeight(50)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e40af;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1e3a8a;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        self.run_btn.clicked.connect(self.run_optimization)
        layout.addWidget(self.run_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Console
        console_group = QGroupBox("📋 Optimization Log")
        console_layout = QVBoxLayout(console_group)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 10))
        self.console.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        console_layout.addWidget(self.console)

        layout.addWidget(console_group)

        return tab

    def create_results_tab(self):
        """Create the results tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Summary
        self.results_summary = QLabel("No optimization results yet")
        self.results_summary.setWordWrap(True)
        self.results_summary.setStyleSheet(
            "padding: 20px; background-color: #f0f9ff; border-radius: 8px; font-size: 14px;"
        )
        layout.addWidget(self.results_summary)

        # Lineup table
        self.lineup_table = QTableWidget()
        self.lineup_table.setColumnCount(7)
        self.lineup_table.setHorizontalHeaderLabels([
            "Position", "Player", "Team", "Salary", "Projected", "Vegas", "Statcast"
        ])
        self.lineup_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.lineup_table)

        # Export section
        export_group = QGroupBox("📤 Export Lineup")
        export_layout = QVBoxLayout(export_group)

        self.export_text = QTextEdit()
        self.export_text.setMaximumHeight(60)
        self.export_text.setPlaceholderText("Lineup will appear here for copy/paste")
        export_layout.addWidget(self.export_text)

        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_lineup)
        export_layout.addWidget(copy_btn)

        layout.addWidget(export_group)

        return tab

    def show_welcome_message(self):
        """Show welcome message in console"""
        welcome = """
🚀 ENHANCED DFS OPTIMIZER 2.0
================================
✅ Mathematical Optimization Engine
✅ Advanced Statistical Analysis
✅ Real-time Data Integration
✅ Smart Lineup Confirmations

Ready to generate optimal lineups!
"""
        self.console.setPlainText(welcome)

    def auto_detect_files(self):
        """Auto-detect CSV files in directory"""
        import glob

        # Look for DraftKings files
        dk_patterns = ['*DKSalaries*.csv', '*draftkings*.csv', '*dk*.csv']
        for pattern in dk_patterns:
            files = glob.glob(pattern, recursive=False)
            if files:
                self.set_dk_file(files[-1])  # Use most recent
                break

        # Look for DFF files
        dff_patterns = ['*DFF*.csv', '*dff*.csv', '*rankings*.csv']
        for pattern in dff_patterns:
            files = glob.glob(pattern, recursive=False)
            if files:
                self.set_dff_file(files[-1])  # Use most recent
                break

    def select_dk_file(self):
        """Select DraftKings CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DraftKings CSV", "", "CSV Files (*.csv)"
        )
        if file_path:
            self.set_dk_file(file_path)

    def select_dff_file(self):
        """Select DFF CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DFF Rankings CSV", "", "CSV Files (*.csv)"
        )
        if file_path:
            self.set_dff_file(file_path)

    def set_dk_file(self, file_path):
        """Set DraftKings file"""
        self.dk_file = file_path
        filename = os.path.basename(file_path)
        self.dk_label.setText(f"✅ {filename}")
        self.dk_label.setStyleSheet(
            "padding: 10px; border: 2px solid #059669; border-radius: 5px; background-color: #ecfdf5;"
        )
        self.run_btn.setEnabled(True)
        self.status_bar.showMessage(f"Loaded: {filename}")

    def set_dff_file(self, file_path):
        """Set DFF file"""
        self.dff_file = file_path
        filename = os.path.basename(file_path)
        self.dff_label.setText(f"✅ {filename}")
        self.dff_label.setStyleSheet(
            "padding: 10px; border: 2px solid #f59e0b; border-radius: 5px; background-color: #fefce8;"
        )

    def load_sample_players(self):
        """Load sample players"""
        sample = "Shohei Ohtani, Mike Trout, Aaron Judge, Freddie Freeman, Mookie Betts, Ronald Acuna Jr., Trea Turner, Jose Ramirez, Vladimir Guerrero Jr., Rafael Devers"
        self.manual_input.setPlainText(sample)

    def use_test_data(self):
        """Create and use test data"""
        try:
            # Create test CSV
            test_file = os.path.join(tempfile.gettempdir(), 'test_dk_salaries.csv')

            with open(test_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Position', 'Name', 'Name', 'ID', 'Roster Position',
                                 'Salary', 'Game Info', 'TeamAbbrev', 'AvgPointsPerGame'])

                # Add diverse test players
                test_players = [
                    ['P', 'Gerrit Cole', 'Gerrit Cole', '1', 'P', '10000', 'NYY@BOS', 'NYY', '18.5'],
                    ['P', 'Shane Bieber', 'Shane Bieber', '2', 'P', '9500', 'CLE@MIN', 'CLE', '17.2'],
                    ['P', 'Dylan Cease', 'Dylan Cease', '3', 'P', '8000', 'SD@LAD', 'SD', '15.1'],
                    ['C', 'Will Smith', 'Will Smith', '4', 'C', '5000', 'LAD@SD', 'LAD', '10.2'],
                    ['C', 'Salvador Perez', 'Salvador Perez', '5', 'C', '4500', 'KC@DET', 'KC', '9.1'],
                    ['1B', 'Freddie Freeman', 'Freddie Freeman', '6', '1B', '5500', 'LAD@SD', 'LAD', '11.5'],
                    ['1B', 'Pete Alonso', 'Pete Alonso', '7', '1B', '5000', 'NYM@PHI', 'NYM', '10.3'],
                    ['2B', 'Jose Altuve', 'Jose Altuve', '8', '2B', '5200', 'HOU@TEX', 'HOU', '10.8'],
                    ['2B', 'Marcus Semien', 'Marcus Semien', '9', '2B', '4800', 'TEX@HOU', 'TEX', '9.7'],
                    ['3B', 'Manny Machado', 'Manny Machado', '10', '3B', '5300', 'SD@LAD', 'SD', '11.0'],
                    ['3B', 'Jose Ramirez', 'Jose Ramirez', '11', '3B', '5800', 'CLE@MIN', 'CLE', '12.2'],
                    ['SS', 'Trea Turner', 'Trea Turner', '12', 'SS', '5100', 'PHI@NYM', 'PHI', '10.5'],
                    ['SS', 'Corey Seager', 'Corey Seager', '13', 'SS', '5400', 'TEX@HOU', 'TEX', '11.2'],
                    ['OF', 'Aaron Judge', 'Aaron Judge', '14', 'OF', '6500', 'NYY@BOS', 'NYY', '13.8'],
                    ['OF', 'Mike Trout', 'Mike Trout', '15', 'OF', '6000', 'LAA@SEA', 'LAA', '12.5'],
                    ['OF', 'Mookie Betts', 'Mookie Betts', '16', 'OF', '5800', 'LAD@SD', 'LAD', '12.0'],
                    ['OF', 'Ronald Acuna Jr.', 'Ronald Acuna Jr.', '17', 'OF', '5600', 'ATL@MIA', 'ATL', '11.6'],
                    ['OF', 'Juan Soto', 'Juan Soto', '18', 'OF', '5500', 'SD@LAD', 'SD', '11.3'],
                    ['OF', 'Yordan Alvarez', 'Yordan Alvarez', '19', 'OF', '5400', 'HOU@TEX', 'HOU', '11.0']
                ]

                for player in test_players:
                    writer.writerow(player)

            self.set_dk_file(test_file)
            QMessageBox.information(self, "Test Data", "Test data created and loaded successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create test data: {str(e)}")

    def run_optimization(self):
        """Run the optimization"""
        if not self.dk_file:
            QMessageBox.warning(self, "No Data", "Please select a DraftKings CSV file first.")
            return

        # Get settings
        contest_type = 'classic' if self.contest_combo.currentIndex() == 0 else 'showdown'
        mode_map = {
            0: 'bulletproof',
            1: 'manual_only',
            2: 'confirmed_only'
        }
        optimization_mode = mode_map[self.mode_combo.currentIndex()]

        # Get manual input
        manual_input = self.manual_input.toPlainText().strip()

        # Validate manual-only mode
        if optimization_mode == 'manual_only' and not manual_input:
            QMessageBox.warning(
                self,
                "Manual Input Required",
                "Manual-Only mode requires manual player selections.\n\n"
                "Please add players in the Manual Player Selection box."
            )
            return

        # Update UI
        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.console.clear()

        # Create and start optimization thread
        self.optimization_thread = OptimizationThread(
            self.dk_file,
            self.dff_file,
            manual_input,
            contest_type,
            optimization_mode
        )

        self.optimization_thread.progress_updated.connect(self.on_progress_update)
        self.optimization_thread.optimization_completed.connect(self.on_optimization_complete)
        self.optimization_thread.optimization_failed.connect(self.on_optimization_failed)

        self.optimization_thread.start()

    def on_progress_update(self, message):
        """Handle progress updates"""
        self.console.append(message)

    def on_optimization_complete(self, lineup, score, summary):
        """Handle successful optimization"""
        self.console.append("\n" + "=" * 50)
        self.console.append("✅ OPTIMIZATION COMPLETE!")
        self.console.append(summary)

        # Store lineup
        self.last_lineup = lineup

        # Update results tab
        self.update_results(lineup, score, summary)

        # Switch to results tab
        self.tab_widget.setCurrentIndex(2)

        # Reset UI
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Optimization complete!")

        # Show success message
        QMessageBox.information(
            self,
            "Success!",
            f"Optimization complete!\n\n"
            f"Score: {score:.2f} points\n"
            f"Players: {len(lineup)}"
        )

    def on_optimization_failed(self, error_message):
        """Handle optimization failure"""
        self.console.append("\n" + "=" * 50)
        self.console.append(f"❌ OPTIMIZATION FAILED: {error_message}")

        # Reset UI
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Optimization failed")

        # Show error message
        QMessageBox.critical(
            self,
            "Optimization Failed",
            f"Optimization failed:\n\n{error_message}"
        )

    def update_results(self, lineup, score, summary):
        """Update the results tab"""
        # Update summary
        total_salary = sum(p.salary for p in lineup)

        summary_html = f"""
        <h3>Optimization Results</h3>
        <p><b>Total Score:</b> {score:.2f} points</p>
        <p><b>Total Salary:</b> ${total_salary:,} / $50,000</p>
        <p><b>Players:</b> {len(lineup)}</p>
        <p><b>Average Score:</b> {score / len(lineup):.2f} per player</p>
        """

        self.results_summary.setText(summary_html)

        # Update table
        self.lineup_table.setRowCount(len(lineup))

        for i, player in enumerate(lineup):
            # Position
            pos = getattr(player, 'assigned_position', player.primary_position)
            self.lineup_table.setItem(i, 0, QTableWidgetItem(pos))

            # Name
            self.lineup_table.setItem(i, 1, QTableWidgetItem(player.name))

            # Team
            self.lineup_table.setItem(i, 2, QTableWidgetItem(player.team))

            # Salary
            self.lineup_table.setItem(i, 3, QTableWidgetItem(f"${player.salary:,}"))

            # Projected score
            self.lineup_table.setItem(i, 4, QTableWidgetItem(f"{player.enhanced_score:.2f}"))

            # Vegas indicator
            vegas_indicator = "✅" if hasattr(player, 'vegas_data') and player.vegas_data else "❌"
            self.lineup_table.setItem(i, 5, QTableWidgetItem(vegas_indicator))

            # Statcast indicator
            statcast_indicator = "✅" if hasattr(player, 'statcast_data') and player.statcast_data else "❌"
            self.lineup_table.setItem(i, 6, QTableWidgetItem(statcast_indicator))

        # Create export text
        export_lines = []
        for player in lineup:
            export_lines.append(player.name)

        self.export_text.setPlainText(", ".join(export_lines))

    def copy_lineup(self):
        """Copy lineup to clipboard"""
        text = self.export_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.status_bar.showMessage("Lineup copied to clipboard!", 3000)
            QMessageBox.information(self, "Copied!", "Lineup copied to clipboard!")
        else:
            QMessageBox.warning(self, "No Lineup", "No lineup to copy.")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Enhanced DFS Optimizer")

    # Check if core is available
    if not CORE_AVAILABLE:
        QMessageBox.critical(
            None,
            "Missing Dependencies",
            "Core systems not found. Please ensure all files are present:\n"
            "- bulletproof_dfs_core.py\n"
            "- unified_data_system.py\n"
            "- optimal_lineup_optimizer.py\n"
            "- smart_confirmation_system.py"
        )
        return 1

    # Create and show main window
    window = EnhancedDFSGUI()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())