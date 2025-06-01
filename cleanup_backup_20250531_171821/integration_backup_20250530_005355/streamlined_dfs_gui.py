#!/usr/bin/env python3
"""
Streamlined DFS GUI - Clean and Functional
Simple, reliable GUI that works with the core optimizer
"""

import sys
import os
from pathlib import Path

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *

    GUI_AVAILABLE = True
except ImportError:
    print("❌ PyQt5 not available. Install with: pip install PyQt5")
    GUI_AVAILABLE = False
    sys.exit(1)

# Import our core system
from streamlined_dfs_core import StreamlinedDFSCore, Player


class OptimizationThread(QThread):
    """Background thread for optimization to keep GUI responsive"""

    output_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, core: StreamlinedDFSCore, contest_type: str, strategy: str):
        super().__init__()
        self.core = core
        self.contest_type = contest_type
        self.strategy = strategy
        self.cancelled = False

    def run(self):
        try:
            self.output_signal.emit("🚀 Starting optimization...")
            self.progress_signal.emit(10)

            if self.cancelled:
                return

            # Detect confirmed lineups
            self.output_signal.emit("🔍 Detecting confirmed lineups...")
            self.core.detect_confirmed_lineups()
            self.progress_signal.emit(40)

            if self.cancelled:
                return

            # Run optimization
            self.output_signal.emit(f"🧠 Optimizing {self.contest_type} lineup...")
            lineup, score = self.core.optimize_lineup(self.contest_type, self.strategy)
            self.progress_signal.emit(80)

            if self.cancelled:
                return

            # Format results
            if lineup:
                result = self.core.format_lineup_output(lineup, score)
                self.output_signal.emit("✅ Optimization complete!")
                self.progress_signal.emit(100)
                self.finished_signal.emit(True, result)
            else:
                self.finished_signal.emit(False, "No valid lineup found")

        except Exception as e:
            self.finished_signal.emit(False, f"Optimization failed: {str(e)}")

    def cancel(self):
        self.cancelled = True


class StreamlinedDFSGUI(QMainWindow):
    """Clean, functional DFS GUI"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Streamlined DFS Optimizer")
        self.setMinimumSize(1000, 700)

        # Core system
        self.dfs_core = StreamlinedDFSCore()
        self.optimization_thread = None

        # File paths
        self.dk_file = ""
        self.dff_file = ""

        self.setup_ui()
        self.apply_theme()

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
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        layout.addWidget(header)

        # File selection section
        file_section = QGroupBox("📁 Data Files")
        file_layout = QVBoxLayout(file_section)

        # DraftKings file
        dk_layout = QHBoxLayout()
        self.dk_label = QLabel("No DraftKings CSV selected")
        self.dk_label.setWordWrap(True)
        dk_btn = QPushButton("📁 Select DraftKings CSV")
        dk_btn.clicked.connect(self.select_dk_file)
        dk_layout.addWidget(self.dk_label, 1)
        dk_layout.addWidget(dk_btn)
        file_layout.addLayout(dk_layout)

        # DFF file
        dff_layout = QHBoxLayout()
        self.dff_label = QLabel("No DFF file selected (optional)")
        self.dff_label.setWordWrap(True)
        dff_btn = QPushButton("🎯 Select DFF CSV")
        dff_btn.clicked.connect(self.select_dff_file)
        dff_layout.addWidget(self.dff_label, 1)
        dff_layout.addWidget(dff_btn)
        file_layout.addLayout(dff_layout)

        layout.addWidget(file_section)

        # Settings section
        settings_section = QGroupBox("⚙️ Optimization Settings")
        settings_layout = QFormLayout(settings_section)

        # Contest type
        self.contest_combo = QComboBox()
        self.contest_combo.addItems([
            "🏆 Classic (10 players)",
            "⚡ Showdown (6 players)"
        ])
        settings_layout.addRow("Contest Type:", self.contest_combo)

        # Strategy
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "⚖️ Balanced (Recommended)",
            "💰 Cash Game (High Floor)",
            "🎲 GPP (High Ceiling)"
        ])
        settings_layout.addRow("Strategy:", self.strategy_combo)

        layout.addWidget(settings_section)

        # Run section
        run_section = QGroupBox("🚀 Optimization")
        run_layout = QVBoxLayout(run_section)

        # Run button
        self.run_btn = QPushButton("🚀 Generate Optimal Lineup")
        self.run_btn.setMinimumHeight(50)
        self.run_btn.setFont(QFont("Arial", 14, QFont.Bold))
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

        layout.addWidget(run_section)

        # Results section
        results_section = QGroupBox("📊 Results")
        results_layout = QVBoxLayout(results_section)

        # Output text
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setMinimumHeight(300)
        results_layout.addWidget(self.output_text)

        # Copy button
        self.copy_btn = QPushButton("📋 Copy Lineup to Clipboard")
        self.copy_btn.clicked.connect(self.copy_lineup)
        self.copy_btn.setVisible(False)
        results_layout.addWidget(self.copy_btn)

        layout.addWidget(results_section)

        # Welcome message
        self.show_welcome_message()

    def show_welcome_message(self):
        """Show welcome message"""
        welcome = [
            "🚀 STREAMLINED DFS OPTIMIZER",
            "=" * 40,
            "",
            "✨ KEY FEATURES:",
            "  • Multi-position player support (3B/SS, etc.)",
            "  • Enhanced DFF name matching (87.5%+ success)",
            "  • Real-time confirmed lineup detection",
            "  • Classic and Showdown contest support",
            "  • Smart optimization strategies",
            "",
            "📋 QUICK START:",
            "  1. Select your DraftKings CSV file",
            "  2. Upload DFF expert rankings (optional)",
            "  3. Choose contest type and strategy",
            "  4. Click 'Generate Optimal Lineup'",
            "",
            "💡 Ready to optimize your lineups!",
            ""
        ]

        self.output_text.setPlainText("\n".join(welcome))

    def apply_theme(self):
        """Apply modern theme"""
        self.setStyleSheet("""
            QMainWindow {
                background: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                padding-top: 15px;
                margin-top: 10px;
                border: 2px solid #dee2e6;
                border-radius: 8px;
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
                font-size: 12px;
            }
            QPushButton:hover {
                background: #2980b9;
            }
            QPushButton:disabled {
                background: #95a5a6;
            }
            QPushButton:pressed {
                background: #21618c;
            }
            QTextEdit {
                background: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 6px;
                padding: 15px;
                font-family: 'Consolas', monospace;
            }
            QLabel {
                color: #2c3e50;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
                font-size: 12px;
            }
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: #3498db;
                border-radius: 3px;
            }
        """)

    def select_dk_file(self):
        """Select DraftKings CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DraftKings CSV", "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            if self.dfs_core.load_draftkings_data(file_path):
                self.dk_file = file_path
                filename = os.path.basename(file_path)
                self.dk_label.setText(f"✅ {filename}")
                self.dk_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                self.run_btn.setEnabled(True)

                # Show loaded data summary
                self.output_text.append(f"\n📁 Loaded DraftKings data: {filename}")
                self.output_text.append(f"✅ {len(self.dfs_core.players)} players loaded")

                # Show position breakdown
                positions = {}
                for player in self.dfs_core.players:
                    for pos in player.positions:
                        positions[pos] = positions.get(pos, 0) + 1

                self.output_text.append(f"📊 Position breakdown: {dict(sorted(positions.items()))}")

                # Show multi-position players
                multi_pos_players = [p for p in self.dfs_core.players if len(p.positions) > 1]
                if multi_pos_players:
                    self.output_text.append(f"🔄 Multi-position players: {len(multi_pos_players)}")
                    for player in multi_pos_players[:5]:  # Show first 5
                        pos_str = "/".join(player.positions)
                        self.output_text.append(f"  • {player.name} ({pos_str})")
                    if len(multi_pos_players) > 5:
                        self.output_text.append(f"  • ... and {len(multi_pos_players) - 5} more")
            else:
                QMessageBox.critical(self, "Error", "Failed to load DraftKings CSV file")

    def select_dff_file(self):
        """Select DFF CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DFF Rankings CSV", "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            if self.dfs_core.load_dff_data(file_path):
                self.dff_file = file_path
                filename = os.path.basename(file_path)
                self.dff_label.setText(f"✅ {filename}")
                self.dff_label.setStyleSheet("color: #27ae60; font-weight: bold;")

                self.output_text.append(f"\n🎯 Loaded DFF data: {filename}")

                # Show DFF integration results
                dff_enhanced = sum(1 for p in self.dfs_core.players if p.dff_rank is not None)
                if dff_enhanced > 0:
                    success_rate = (dff_enhanced / len(self.dfs_core.players)) * 100
                    self.output_text.append(f"✅ DFF enhanced {dff_enhanced} players ({success_rate:.1f}% success rate)")

                    if success_rate >= 80:
                        self.output_text.append("🎉 EXCELLENT match rate! DFF integration working perfectly!")
                    elif success_rate >= 60:
                        self.output_text.append("👍 Good match rate for DFF integration")
                    else:
                        self.output_text.append("⚠️ Lower match rate - check name formats")
            else:
                QMessageBox.warning(self, "Warning", "Failed to load DFF CSV file")

    def run_optimization(self):
        """Run the optimization process"""
        if not self.dfs_core.players:
            QMessageBox.warning(self, "Warning", "Please load DraftKings data first")
            return

        # Get settings
        contest_type = "classic" if self.contest_combo.currentIndex() == 0 else "showdown"
        strategy_map = {0: "balanced", 1: "cash", 2: "gpp"}
        strategy = strategy_map.get(self.strategy_combo.currentIndex(), "balanced")

        # Update UI
        self.run_btn.setEnabled(False)
        self.run_btn.setText("⏳ Optimizing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.cancel_btn.setVisible(True)
        self.copy_btn.setVisible(False)

        # Clear output
        self.output_text.clear()
        self.output_text.append(f"🚀 Starting {contest_type} optimization with {strategy} strategy...")

        # Start optimization thread
        self.optimization_thread = OptimizationThread(self.dfs_core, contest_type, strategy)
        self.optimization_thread.output_signal.connect(self.output_text.append)
        self.optimization_thread.progress_signal.connect(self.progress_bar.setValue)
        self.optimization_thread.finished_signal.connect(self.optimization_finished)
        self.optimization_thread.start()

    def cancel_optimization(self):
        """Cancel running optimization"""
        if self.optimization_thread and self.optimization_thread.isRunning():
            self.optimization_thread.cancel()
            self.output_text.append("🛑 Optimization cancelled by user")

    def optimization_finished(self, success: bool, result: str):
        """Handle optimization completion"""
        # Reset UI
        self.run_btn.setEnabled(True)
        self.run_btn.setText("🚀 Generate Optimal Lineup")
        self.progress_bar.setVisible(False)
        self.cancel_btn.setVisible(False)

        if success:
            self.output_text.append("\n" + "=" * 60)
            self.output_text.append(result)
            self.copy_btn.setVisible(True)
            self.lineup_text = result  # Store for copying

            # Show optimization summary
            confirmed_players = sum(1 for p in self.dfs_core.players if p.confirmed_lineup)
            dff_players = sum(1 for p in self.dfs_core.players if p.dff_rank is not None)

            self.output_text.append(f"\n📊 OPTIMIZATION SUMMARY:")
            self.output_text.append(f"  • Total players considered: {len(self.dfs_core.players)}")
            self.output_text.append(f"  • Confirmed lineup players: {confirmed_players}")
            self.output_text.append(f"  • DFF enhanced players: {dff_players}")
            self.output_text.append(f"  • Multi-position flexibility: ✅ Active")

        else:
            self.output_text.append(f"\n❌ OPTIMIZATION FAILED")
            self.output_text.append(f"Error: {result}")
            QMessageBox.critical(self, "Optimization Failed", result)

    def copy_lineup(self):
        """Copy lineup to clipboard"""
        if hasattr(self, 'lineup_text'):
            # Extract just the player names for DraftKings import
            lines = self.lineup_text.split('\n')
            for line in lines:
                if line.startswith("📋 DRAFTKINGS IMPORT:"):
                    import_line_idx = lines.index(line)
                    if import_line_idx + 1 < len(lines):
                        lineup_names = lines[import_line_idx + 1]
                        clipboard = QApplication.clipboard()
                        clipboard.setText(lineup_names)

                        # Show confirmation
                        QMessageBox.information(
                            self, "Copied!",
                            "Lineup copied to clipboard!\n\nYou can now paste this into DraftKings."
                        )
                        return

            # Fallback - copy everything
            clipboard = QApplication.clipboard()
            clipboard.setText(self.lineup_text)
            QMessageBox.information(self, "Copied!", "Full results copied to clipboard!")
        else:
            QMessageBox.warning(self, "No Lineup", "No lineup available to copy")

    def closeEvent(self, event):
        """Handle window close"""
        if self.optimization_thread and self.optimization_thread.isRunning():
            reply = QMessageBox.question(
                self, 'Close Application',
                'Optimization is running. Are you sure you want to quit?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.optimization_thread.cancel()
                self.optimization_thread.wait(2000)  # Wait up to 2 seconds
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main application entry point"""
    if not GUI_AVAILABLE:
        print("❌ GUI not available. Install PyQt5 first.")
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName("Streamlined DFS Optimizer")

    # Create and show the main window
    window = StreamlinedDFSGUI()
    window.show()
    window.raise_()
    window.activateWindow()

    print("✅ Streamlined DFS GUI launched successfully!")

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())