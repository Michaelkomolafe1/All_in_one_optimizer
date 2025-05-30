#!/usr/bin/env python3
"""
Streamlined DFS GUI - Working Version
Clean, functional GUI that integrates perfectly with working_dfs_core_final.py
"""

import sys
import os
import traceback
import tempfile
from pathlib import Path

# Import PyQt5
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *

    print("✅ PyQt5 loaded successfully")
except ImportError:
    print("❌ PyQt5 not available. Install with: pip install PyQt5")
    sys.exit(1)

# Import our working DFS core
try:
    from working_dfs_core_final import (
        OptimizedDFSCore,
        load_and_optimize_complete_pipeline,
        create_enhanced_test_data
    )

    print("✅ Working DFS Core imported successfully")
    CORE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Could not import working DFS core: {e}")
    print("💡 Make sure working_dfs_core_final.py is in the same directory")
    CORE_AVAILABLE = False


class OptimizationWorker(QThread):
    """Background worker for DFS optimization"""

    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, dict)

    def __init__(self, dk_file, dff_file, manual_input, contest_type, strategy):
        super().__init__()
        self.dk_file = dk_file
        self.dff_file = dff_file
        self.manual_input = manual_input
        self.contest_type = contest_type
        self.strategy = strategy
        self.is_cancelled = False

    def run(self):
        try:
            self.status_signal.emit("Starting optimization...")
            self.progress_signal.emit(10)

            if self.is_cancelled:
                return

            # Run the complete pipeline
            self.status_signal.emit("Loading data...")
            self.progress_signal.emit(30)

            lineup, score, summary = load_and_optimize_complete_pipeline(
                dk_file=self.dk_file,
                dff_file=self.dff_file,
                manual_input=self.manual_input,
                contest_type=self.contest_type,
                strategy=self.strategy
            )

            self.progress_signal.emit(90)

            if lineup and score > 0:
                # Extract lineup data for table display
                lineup_data = {
                    'players': [],
                    'total_salary': sum(p.salary for p in lineup),
                    'total_score': score,
                    'summary': summary
                }

                for player in lineup:
                    player_info = {
                        'position': player.primary_position,
                        'name': player.name,
                        'team': player.team,
                        'salary': player.salary,
                        'score': player.enhanced_score,
                        'status': self._get_player_status(player)
                    }
                    lineup_data['players'].append(player_info)

                self.progress_signal.emit(100)
                self.status_signal.emit("Complete!")
                self.finished_signal.emit(True, summary, lineup_data)
            else:
                self.finished_signal.emit(False, "No valid lineup found", {})

        except Exception as e:
            error_msg = f"Optimization failed: {str(e)}"
            self.finished_signal.emit(False, error_msg, {})

    def _get_player_status(self, player):
        """Get player status string"""
        status_parts = []
        if hasattr(player, 'is_confirmed') and player.is_confirmed:
            status_parts.append("CONF")
        if hasattr(player, 'is_manual_selected') and player.is_manual_selected:
            status_parts.append("MANUAL")
        if hasattr(player, 'dff_projection') and player.dff_projection > 0:
            status_parts.append(f"DFF:{player.dff_projection:.1f}")
        return ",".join(status_parts) if status_parts else "-"

    def cancel(self):
        self.is_cancelled = True


class StreamlinedDFSGUI(QMainWindow):
    """Clean, working DFS GUI"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Streamlined DFS Optimizer")
        self.setMinimumSize(1200, 800)

        # Data
        self.dk_file = ""
        self.dff_file = ""
        self.worker = None

        self.setup_ui()
        self.apply_styles()

        # Show welcome message
        self.show_welcome()

        print("✅ Streamlined DFS GUI initialized")

    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QLabel("🚀 Streamlined DFS Optimizer")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 20px;")
        layout.addWidget(header)

        # Create tabs
        self.tab_widget = QTabWidget()

        # Tab 1: Setup
        self.setup_tab = self.create_setup_tab()
        self.tab_widget.addTab(self.setup_tab, "📁 Setup")

        # Tab 2: Optimize
        self.optimize_tab = self.create_optimize_tab()
        self.tab_widget.addTab(self.optimize_tab, "🚀 Optimize")

        # Tab 3: Results
        self.results_tab = self.create_results_tab()
        self.tab_widget.addTab(self.results_tab, "📊 Results")

        layout.addWidget(self.tab_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Select DraftKings CSV to begin")

    def create_setup_tab(self):
        """Create the setup tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)

        # DraftKings file section
        dk_group = QGroupBox("📁 DraftKings CSV File")
        dk_layout = QVBoxLayout(dk_group)

        dk_file_layout = QHBoxLayout()
        self.dk_label = QLabel("No file selected")
        self.dk_label.setStyleSheet("color: #7f8c8d; padding: 10px; border: 1px dashed #bdc3c7; border-radius: 5px;")

        dk_btn = QPushButton("📁 Browse Files")
        dk_btn.clicked.connect(self.select_dk_file)
        dk_btn.setFixedWidth(150)

        dk_file_layout.addWidget(self.dk_label, 1)
        dk_file_layout.addWidget(dk_btn)
        dk_layout.addLayout(dk_file_layout)

        # Instructions
        instructions = QLabel("""
        <h3>📋 Instructions:</h3>
        <ol>
        <li><b>Export from DraftKings:</b> Go to your contest and click "Export to CSV"</li>
        <li><b>Select the file:</b> Use the browse button above</li>
        <li><b>Optional:</b> Upload DFF expert rankings for better results</li>
        <li><b>Optimize:</b> Go to the Optimize tab and generate your lineup</li>
        </ol>
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("""
            background: #e8f5e8; 
            padding: 15px; 
            border-radius: 8px; 
            border-left: 4px solid #27ae60;
            margin-top: 10px;
        """)
        dk_layout.addWidget(instructions)

        layout.addWidget(dk_group)

        # DFF file section (optional)
        dff_group = QGroupBox("🎯 DFF Expert Rankings (Optional)")
        dff_layout = QVBoxLayout(dff_group)

        dff_file_layout = QHBoxLayout()
        self.dff_label = QLabel("No DFF file selected")
        self.dff_label.setStyleSheet("color: #7f8c8d; padding: 10px; border: 1px dashed #bdc3c7; border-radius: 5px;")

        dff_btn = QPushButton("📊 Browse DFF CSV")
        dff_btn.clicked.connect(self.select_dff_file)
        dff_btn.setFixedWidth(150)

        dff_file_layout.addWidget(self.dff_label, 1)
        dff_file_layout.addWidget(dff_btn)
        dff_layout.addLayout(dff_file_layout)

        # DFF info
        dff_info = QLabel("""
        <b>💡 DFF Integration Benefits:</b><br>
        • Expert rankings boost player scores<br>
        • Enhanced name matching (95%+ success rate)<br>
        • Vegas lines and confirmed lineup data<br>
        • Recent form analysis (L5 game averages)
        """)
        dff_info.setWordWrap(True)
        dff_info.setStyleSheet("""
            background: #fff3cd; 
            padding: 15px; 
            border-radius: 8px; 
            border-left: 4px solid #ffc107;
            margin-top: 10px;
        """)
        dff_layout.addWidget(dff_info)

        layout.addWidget(dff_group)

        # Test data option
        test_group = QGroupBox("🧪 Test with Sample Data")
        test_layout = QVBoxLayout(test_group)

        test_btn = QPushButton("🧪 Use Sample Data for Testing")
        test_btn.clicked.connect(self.use_sample_data)
        test_btn.setStyleSheet("background: #3498db; color: white; padding: 10px;")
        test_layout.addWidget(test_btn)

        test_info = QLabel("Use realistic sample MLB data to test the optimizer")
        test_info.setStyleSheet("color: #6c757d; font-style: italic; margin-top: 5px;")
        test_layout.addWidget(test_info)

        layout.addWidget(test_group)

        layout.addStretch()
        return tab

    def create_optimize_tab(self):
        """Create the optimize tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)

        # Settings
        settings_group = QGroupBox("⚙️ Optimization Settings")
        settings_layout = QFormLayout(settings_group)

        # Contest type
        self.contest_combo = QComboBox()
        self.contest_combo.addItems([
            "🏆 Classic Contest (10 players)",
            "⚡ Showdown Contest (6 players)"
        ])
        settings_layout.addRow("Contest Type:", self.contest_combo)

        # Strategy
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "⚖️ Balanced (Recommended)",
            "🔒 Confirmed Only (Safest)",
            "🎯 High Floor (Cash Games)",
            "🚀 High Ceiling (GPPs)",
            "✏️ Manual Only"
        ])
        settings_layout.addRow("Strategy:", self.strategy_combo)

        # Manual players
        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Optional: Enter player names separated by commas")
        settings_layout.addRow("Manual Players:", self.manual_input)

        layout.addWidget(settings_group)

        # Run optimization
        run_group = QGroupBox("🚀 Generate Lineup")
        run_layout = QVBoxLayout(run_group)

        self.run_btn = QPushButton("🚀 Generate Optimal Lineup")
        self.run_btn.setMinimumHeight(50)
        self.run_btn.clicked.connect(self.run_optimization)
        self.run_btn.setEnabled(False)
        run_layout.addWidget(self.run_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        run_layout.addWidget(self.progress_bar)

        # Cancel button
        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self.cancel_optimization)
        run_layout.addWidget(self.cancel_btn)

        layout.addWidget(run_group)

        # Console output
        console_group = QGroupBox("📋 Optimization Log")
        console_layout = QVBoxLayout(console_group)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(300)
        console_layout.addWidget(self.console)

        layout.addWidget(console_group)

        return tab

    def create_results_tab(self):
        """Create the results tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)

        # Summary
        summary_group = QGroupBox("📊 Lineup Summary")
        summary_layout = QVBoxLayout(summary_group)

        self.summary_label = QLabel("No optimization results yet")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("color: #6c757d; font-style: italic;")
        summary_layout.addWidget(self.summary_label)

        layout.addWidget(summary_group)

        # Lineup table
        table_group = QGroupBox("💰 Optimized Lineup")
        table_layout = QVBoxLayout(table_group)

        self.lineup_table = QTableWidget()
        self.lineup_table.setColumnCount(6)
        self.lineup_table.setHorizontalHeaderLabels([
            "Position", "Player", "Team", "Salary", "Score", "Status"
        ])

        # Make table look nice
        header = self.lineup_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Player name column

        table_layout.addWidget(self.lineup_table)
        layout.addWidget(table_group)

        # DraftKings import
        import_group = QGroupBox("📋 DraftKings Import")
        import_layout = QVBoxLayout(import_group)

        self.import_text = QTextEdit()
        self.import_text.setMaximumHeight(100)
        self.import_text.setPlaceholderText("Optimized lineup will appear here for copy/paste into DraftKings")
        import_layout.addWidget(self.import_text)

        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        import_layout.addWidget(copy_btn)

        layout.addWidget(import_group)

        return tab

    def apply_styles(self):
        """Apply modern styling"""
        self.setStyleSheet("""
            QMainWindow {
                background: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background: white;
            }
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
            QPushButton:disabled {
                background: #95a5a6;
            }
            QComboBox, QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background: white;
            }
            QTableWidget {
                gridline-color: #dee2e6;
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f8f9fa;
            }
            QHeaderView::section {
                background: #f8f9fa;
                padding: 10px;
                border: none;
                border-right: 1px solid #dee2e6;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background: white;
            }
            QTabBar::tab {
                background: #f8f9fa;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
            }
        """)

    def show_welcome(self):
        """Show welcome message in console"""
        welcome = [
            "🚀 STREAMLINED DFS OPTIMIZER",
            "=" * 40,
            "",
            "✨ FEATURES:",
            "  • MILP optimization for maximum accuracy",
            "  • Multi-position player support (3B/SS, 1B/3B)",
            "  • DFF expert rankings integration",
            "  • Manual player selection",
            "  • Real-time confirmed lineup detection",
            "",
            "📋 INSTRUCTIONS:",
            "  1. Go to Setup tab and select your DraftKings CSV",
            "  2. Optionally upload DFF expert rankings",
            "  3. Come back to Optimize tab and generate lineup",
            "  4. View results in Results tab",
            "",
            "💡 Ready to optimize your lineup!",
            ""
        ]
        self.console.setPlainText("\n".join(welcome))

    def select_dk_file(self):
        """Select DraftKings CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DraftKings CSV File", "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            self.dk_file = file_path
            filename = os.path.basename(file_path)
            self.dk_label.setText(f"✅ {filename}")
            self.dk_label.setStyleSheet(
                "color: #27ae60; font-weight: bold; padding: 10px; border: 1px solid #27ae60; border-radius: 5px;")
            self.run_btn.setEnabled(True)
            self.status_bar.showMessage(f"DraftKings file loaded: {filename}")

    def select_dff_file(self):
        """Select DFF CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DFF Rankings CSV", "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            self.dff_file = file_path
            filename = os.path.basename(file_path)
            self.dff_label.setText(f"✅ {filename}")
            self.dff_label.setStyleSheet(
                "color: #27ae60; font-weight: bold; padding: 10px; border: 1px solid #27ae60; border-radius: 5px;")
            self.status_bar.showMessage(f"DFF file loaded: {filename}")

    def use_sample_data(self):
        """Use sample data for testing"""
        try:
            dk_file, dff_file = create_enhanced_test_data()
            self.dk_file = dk_file
            self.dff_file = dff_file

            self.dk_label.setText("✅ Sample DraftKings data loaded")
            self.dk_label.setStyleSheet(
                "color: #27ae60; font-weight: bold; padding: 10px; border: 1px solid #27ae60; border-radius: 5px;")

            self.dff_label.setText("✅ Sample DFF data loaded")
            self.dff_label.setStyleSheet(
                "color: #27ae60; font-weight: bold; padding: 10px; border: 1px solid #27ae60; border-radius: 5px;")

            self.run_btn.setEnabled(True)
            self.status_bar.showMessage("Sample data loaded - ready to optimize")

            # Pre-fill manual players for demo
            self.manual_input.setText("Jorge Polanco, Christian Yelich")

            QMessageBox.information(self, "Sample Data Loaded",
                                    "✅ Sample MLB data loaded!\n\n"
                                    "• 35 realistic players with multi-position support\n"
                                    "• DFF expert rankings included\n"
                                    "• Manual players pre-selected\n\n"
                                    "Go to the Optimize tab to generate your lineup!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sample data:\n{str(e)}")

    def run_optimization(self):
        """Run the optimization"""
        if not CORE_AVAILABLE:
            QMessageBox.critical(self, "Error", "DFS Core not available. Check working_dfs_core_final.py")
            return

        if not self.dk_file:
            QMessageBox.warning(self, "Warning", "Please select a DraftKings CSV file first")
            return

        # Get settings
        contest_type = 'classic' if self.contest_combo.currentIndex() == 0 else 'showdown'

        strategy_map = {
            0: 'balanced',
            1: 'confirmed_only',
            2: 'high_floor',
            3: 'high_ceiling',
            4: 'manual_only'
        }
        strategy = strategy_map.get(self.strategy_combo.currentIndex(), 'balanced')

        manual_input = self.manual_input.text().strip()

        # Update UI
        self.run_btn.setEnabled(False)
        self.run_btn.setText("⏳ Optimizing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.cancel_btn.setVisible(True)

        self.console.clear()
        self.console.append("🚀 Starting DFS optimization...")

        # Start worker thread
        self.worker = OptimizationWorker(
            self.dk_file, self.dff_file, manual_input, contest_type, strategy
        )
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
        """Handle optimization completion"""
        # Reset UI
        self.run_btn.setEnabled(True)
        self.run_btn.setText("🚀 Generate Optimal Lineup")
        self.progress_bar.setVisible(False)
        self.cancel_btn.setVisible(False)

        if success:
            self.console.append("\n✅ OPTIMIZATION COMPLETED!")
            self.console.append("=" * 50)
            self.console.append(result)

            # Update results tab
            self.update_results(lineup_data)

            # Switch to results tab
            self.tab_widget.setCurrentIndex(2)

            self.status_bar.showMessage("Optimization complete! Check Results tab.")

        else:
            self.console.append(f"\n❌ OPTIMIZATION FAILED: {result}")
            self.status_bar.showMessage("Optimization failed - check console for details")

            QMessageBox.critical(self, "Optimization Failed",
                                 f"The optimization failed:\n\n{result}")

    def update_results(self, lineup_data):
        """Update the results tab with lineup data"""
        try:
            # Update summary
            total_salary = lineup_data.get('total_salary', 0)
            total_score = lineup_data.get('total_score', 0)
            players = lineup_data.get('players', [])

            summary_text = f"""
            <h3>📊 Optimization Results</h3>
            <p><b>Total Players:</b> {len(players)}</p>
            <p><b>Total Salary:</b> ${total_salary:,}</p>
            <p><b>Projected Score:</b> {total_score:.2f} points</p>
            <p><b>Salary Remaining:</b> ${50000 - total_salary:,}</p>
            """

            # Add lineup composition info
            confirmed = sum(1 for p in players if 'CONF' in p.get('status', ''))
            manual = sum(1 for p in players if 'MANUAL' in p.get('status', ''))
            dff = sum(1 for p in players if 'DFF' in p.get('status', ''))

            summary_text += f"""
            <p><b>Confirmed Players:</b> {confirmed}</p>
            <p><b>Manual Selections:</b> {manual}</p>
            <p><b>DFF Enhanced:</b> {dff}</p>
            """

            self.summary_label.setText(summary_text)

            # Update table
            self.lineup_table.setRowCount(len(players))

            for row, player in enumerate(players):
                self.lineup_table.setItem(row, 0, QTableWidgetItem(player.get('position', '')))
                self.lineup_table.setItem(row, 1, QTableWidgetItem(player.get('name', '')))
                self.lineup_table.setItem(row, 2, QTableWidgetItem(player.get('team', '')))
                self.lineup_table.setItem(row, 3, QTableWidgetItem(f"${player.get('salary', 0):,}"))
                self.lineup_table.setItem(row, 4, QTableWidgetItem(f"{player.get('score', 0):.1f}"))
                self.lineup_table.setItem(row, 5, QTableWidgetItem(player.get('status', '')))

            # Update import text
            player_names = [p.get('name', '') for p in players]
            self.import_text.setPlainText(", ".join(player_names))

        except Exception as e:
            print(f"Error updating results: {e}")
            traceback.print_exc()

    def copy_to_clipboard(self):
        """Copy lineup to clipboard"""
        text = self.import_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.status_bar.showMessage("Lineup copied to clipboard!", 3000)
            QMessageBox.information(self, "Copied!",
                                    "Lineup copied to clipboard!\n\nYou can now paste this into DraftKings.")
        else:
            QMessageBox.warning(self, "No Lineup", "No lineup available to copy")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Streamlined DFS Optimizer")
    app.setApplicationVersion("1.0")

    # Check if core is available
    if not CORE_AVAILABLE:
        QMessageBox.critical(None, "Missing Core",
                             "Could not import working_dfs_core_final.py\n\n"
                             "Make sure the file is in the same directory as this GUI.")
        return 1

    # Create and show the main window
    window = StreamlinedDFSGUI()
    window.show()
    window.raise_()
    window.activateWindow()

    print("✅ Streamlined DFS GUI launched successfully!")

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())