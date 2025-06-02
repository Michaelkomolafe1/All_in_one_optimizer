#!/usr/bin/env python3
"""
Enhanced DFS GUI - Updated for Strict System
✅ Uses strict_dfs_core.py (NO unconfirmed leaks)
✅ All existing functionality preserved
✅ Vegas lines integration
✅ Statcast integration
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# PyQt5 imports
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    print("✅ PyQt5 loaded successfully")
except ImportError:
    print("❌ PyQt5 not available. Install with: pip install PyQt5")
    sys.exit(1)

# Import strict system
try:
    from strict_dfs_core import run_strict_optimization, StrictPlayer
    print("✅ Strict DFS core loaded")
except ImportError as e:
    print(f"❌ Could not import strict DFS core: {e}")
    sys.exit(1)


class OptimizationThread(QThread):
    """Background thread for running optimization"""

    progress_updated = pyqtSignal(str)
    optimization_completed = pyqtSignal(object, float, str)
    optimization_failed = pyqtSignal(str)

    def __init__(self, dk_file, dff_file, manual_input):
        super().__init__()
        self.dk_file = dk_file
        self.dff_file = dff_file
        self.manual_input = manual_input

    def run(self):
        """Run strict optimization in background"""
        try:
            self.progress_updated.emit("🔒 Starting STRICT optimization...")
            self.progress_updated.emit("📊 Loading DraftKings data...")

            lineup, score, summary = run_strict_optimization(
                dk_file=self.dk_file,
                dff_file=self.dff_file,
                manual_input=self.manual_input
            )

            if lineup and score > 0:
                # Verify NO unconfirmed players
                unconfirmed = [p for p in lineup if not p.is_eligible_for_selection()]
                if unconfirmed:
                    error_msg = f"🚨 CRITICAL: {len(unconfirmed)} unconfirmed players detected!"
                    self.optimization_failed.emit(error_msg)
                else:
                    self.progress_updated.emit("🔒 VERIFICATION PASSED: All players confirmed/manual")
                    self.optimization_completed.emit(lineup, score, summary)
            else:
                self.optimization_failed.emit("No valid lineup generated - need more confirmed/manual players")

        except Exception as e:
            self.optimization_failed.emit(str(e))


class StrictDFSGUI(QMainWindow):
    """Enhanced DFS GUI with strict confirmation system"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DFS Optimizer - STRICT Confirmed Only (No Leaks)")
        self.setMinimumSize(1200, 900)

        self.dk_file = ""
        self.dff_file = ""
        self.optimization_thread = None

        self.setup_ui()
        self.setup_status_bar()
        self.auto_detect_files()

        print("✅ Strict DFS GUI initialized")

    def setup_ui(self):
        """Setup user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        self.create_header(layout)

        # Main content
        self.tab_widget = QTabWidget()

        # Setup tab
        self.tab_widget.addTab(self.create_setup_tab(), "⚙️ Setup")

        # Results tab  
        self.tab_widget.addTab(self.create_results_tab(), "📊 Results")

        layout.addWidget(self.tab_widget)

        # Optimize button
        self.optimize_btn = QPushButton("🔒 OPTIMIZE (STRICT CONFIRMED ONLY)")
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.optimize_btn.clicked.connect(self.run_optimization)
        self.optimize_btn.setEnabled(False)
        layout.addWidget(self.optimize_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Console
        self.console = QTextEdit()
        self.console.setMaximumHeight(200)
        self.console.setFont(QFont("Consolas", 9))
        self.console.setStyleSheet("background-color: #1e1e1e; color: #ffffff; border: 1px solid #333;")
        layout.addWidget(self.console)

        # Welcome message
        self.show_welcome_message()

    def create_header(self, layout):
        """Create header section"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #dc2626, stop: 1 #991b1b);
                border-radius: 10px;
                color: white;
                padding: 20px;
            }
        """)

        header_layout = QVBoxLayout(header_frame)

        title = QLabel("🔒 STRICT DFS OPTIMIZER")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)

        subtitle = QLabel("🚫 ZERO Unconfirmed Players • ✅ Vegas Lines • 🔬 Statcast Data • 🎯 Manual Selection")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: white; opacity: 0.9;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header_frame)

    def create_setup_tab(self):
        """Create setup tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # File selection
        file_group = QGroupBox("📁 Data Files")
        file_layout = QVBoxLayout(file_group)

        # DK file
        dk_layout = QHBoxLayout()
        self.dk_label = QLabel("No DraftKings file selected")
        self.dk_label.setStyleSheet("padding: 10px; border: 2px dashed #ccc; border-radius: 5px;")
        dk_btn = QPushButton("Browse DK CSV")
        dk_btn.clicked.connect(self.select_dk_file)
        dk_layout.addWidget(self.dk_label, 1)
        dk_layout.addWidget(dk_btn)
        file_layout.addLayout(dk_layout)

        # DFF file
        dff_layout = QHBoxLayout()
        self.dff_label = QLabel("No DFF file selected")
        self.dff_label.setStyleSheet("padding: 10px; border: 2px dashed #ccc; border-radius: 5px;")
        dff_btn = QPushButton("Browse DFF CSV")
        dff_btn.clicked.connect(self.select_dff_file)
        dff_layout.addWidget(self.dff_label, 1)
        dff_layout.addWidget(dff_btn)
        file_layout.addLayout(dff_layout)

        layout.addWidget(file_group)

        # Manual selection
        manual_group = QGroupBox("🎯 Manual Player Selection (TREATED AS CONFIRMED)")
        manual_layout = QVBoxLayout(manual_group)

        info = QLabel("💡 Players added here are treated as CONFIRMED starters")
        info.setStyleSheet("color: #dc2626; font-weight: bold;")
        manual_layout.addWidget(info)

        self.manual_input = QTextEdit()
        self.manual_input.setMaximumHeight(150)
        self.manual_input.setPlaceholderText("Enter player names separated by commas...")
        manual_layout.addWidget(self.manual_input)

        # Quick fill buttons
        btn_layout = QHBoxLayout()

        sample_btn = QPushButton("📝 Load Sample")
        sample_btn.clicked.connect(self.load_sample_players)
        btn_layout.addWidget(sample_btn)

        your_list_btn = QPushButton("📋 Load Your Full List")
        your_list_btn.clicked.connect(self.load_your_full_list)
        btn_layout.addWidget(your_list_btn)

        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.manual_input.clear)
        btn_layout.addWidget(clear_btn)

        manual_layout.addLayout(btn_layout)
        layout.addWidget(manual_group)

        layout.addStretch()
        return tab

    def create_results_tab(self):
        """Create results tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Summary
        self.results_summary = QLabel("No optimization run yet")
        self.results_summary.setWordWrap(True)
        self.results_summary.setStyleSheet("padding: 15px; background-color: #f5f5f5; border-radius: 5px;")
        layout.addWidget(self.results_summary)

        # Lineup table
        self.lineup_table = QTableWidget()
        self.lineup_table.setColumnCount(6)
        self.lineup_table.setHorizontalHeaderLabels(["Position", "Player", "Team", "Salary", "Score", "Status"])
        self.lineup_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.lineup_table)

        # Import section
        import_group = QGroupBox("📋 DraftKings Import")
        import_layout = QVBoxLayout(import_group)

        self.import_text = QTextEdit()
        self.import_text.setMaximumHeight(60)
        self.import_text.setPlaceholderText("Optimized lineup will appear here for copy/paste into DraftKings")
        import_layout.addWidget(self.import_text)

        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        import_layout.addWidget(copy_btn)

        layout.addWidget(import_group)
        return tab

    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Strict DFS Optimizer (No Unconfirmed Leaks)")

    def show_welcome_message(self):
        """Show welcome message"""
        welcome = [
            "🔒 STRICT DFS OPTIMIZER - ZERO UNCONFIRMED LEAKS",
            "=" * 60,
            "",
            "✨ KEY FEATURES:",
            "  🔒 BULLETPROOF: Only confirmed + manual players allowed",
            "  💰 Vegas Lines: Real-time odds integration",
            "  🔬 Statcast: Real Baseball Savant data for priority players",
            "  🎯 Manual Selection: Your picks are treated as confirmed",
            "",
            "📋 WORKFLOW:",
            "  1. Select your DraftKings CSV file",
            "  2. Optionally select DFF rankings file",
            "  3. Add manual players (treated as confirmed)",
            "  4. Click 'OPTIMIZE' - only confirmed/manual players used",
            "",
            "🔒 GUARANTEE: NO unconfirmed players will ever appear in lineups!",
            ""
        ]

        for line in welcome:
            self.console.append(line)

    def auto_detect_files(self):
        """Auto-detect CSV files"""
        import glob

        # Look for DraftKings files
        dk_patterns = ['DKSalaries*.csv', '*dksalaries*.csv', '*draftkings*.csv']
        dk_files = []
        for pattern in dk_patterns:
            dk_files.extend(glob.glob(pattern))

        # Look for DFF files  
        dff_patterns = ['DFF*.csv', '*dff*.csv', '*cheat*.csv']
        dff_files = []
        for pattern in dff_patterns:
            dff_files.extend(glob.glob(pattern))

        # Set most recent files
        if dk_files:
            dk_files.sort(key=os.path.getmtime, reverse=True)
            self.set_dk_file(dk_files[0])

        if dff_files:
            dff_files.sort(key=os.path.getmtime, reverse=True)
            self.set_dff_file(dff_files[0])

    def select_dk_file(self):
        """Select DraftKings file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select DraftKings CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.set_dk_file(file_path)

    def select_dff_file(self):
        """Select DFF file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select DFF Rankings CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.set_dff_file(file_path)

    def set_dk_file(self, file_path):
        """Set DraftKings file"""
        self.dk_file = file_path
        self.dk_label.setText(f"✅ {Path(file_path).name}")
        self.dk_label.setStyleSheet("padding: 10px; border: 2px solid green; border-radius: 5px; background-color: #e8f5e8;")
        self.optimize_btn.setEnabled(True)
        self.status_bar.showMessage(f"✅ DK file loaded: {Path(file_path).name}")

    def set_dff_file(self, file_path):
        """Set DFF file"""
        self.dff_file = file_path
        self.dff_label.setText(f"✅ {Path(file_path).name}")
        self.dff_label.setStyleSheet("padding: 10px; border: 2px solid orange; border-radius: 5px; background-color: #fff3cd;")

    def load_sample_players(self):
        """Load sample manual players"""
        sample = "CJ Abrams, James Wood, Ketel Marte, Cal Raleigh, Josh Naylor, Bryan Reynolds"
        self.manual_input.setPlainText(sample)

    def load_your_full_list(self):
        """Load your full manual list"""
        full_list = """CJ Abrams, James Wood, Nathaniel Lowe, Luis García Jr., Josh Bell, Robert Hassell III, Keibert Ruiz, Jose Tena, Daylen Lile, Corbin Carroll, Ketel Marte, Geraldo Perdomo, Josh Naylor, Eugenio Suárez, Lourdes Gurriel Jr., Gabriel Moreno, Alek Thomas, Oneil Cruz, Andrew McCutchen, Bryan Reynolds, Spencer Horwitz, Henry Davis, Ke'Bryan Hayes, Adam Frazier, Tommy Pham, Isiah Kiner-Falefa, Fernando Tatis Jr., Luis Arraez, Manny Machado, Jackson Merrill, Gavin Sheets, Xander Bogaerts, Jake Cronenworth, Elias Díaz, Byron Buxton, Trevor Larnach, Ryan Jeffers, Carlos Correa, Ty France, Kody Clemens, Royce Lewis, Willi Castro, J.P. Crawford, Jorge Polanco, Julio Rodríguez, Cal Raleigh, Randy Arozarena, Rowdy Tellez, Leody Taveras, Ben Williamson, Shohei Ohtani, Teoscar Hernández, Will Smith, Freddie Freeman, Andy Pages, Tommy Edman, Kiké Hernández, Michael Conforto, Miguel Rojas"""
        self.manual_input.setPlainText(full_list)

    def run_optimization(self):
        """Run strict optimization"""
        if not self.dk_file or not os.path.exists(self.dk_file):
            QMessageBox.warning(self, "No File", "Please select a DraftKings CSV file first.")
            return

        manual_input = self.manual_input.toPlainText().strip()

        # Update UI
        self.optimize_btn.setEnabled(False)
        self.optimize_btn.setText("🔄 Optimizing (Strict Mode)...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.console.append(f"\n🔒 Starting STRICT optimization...")
        self.console.append(f"📊 DK File: {Path(self.dk_file).name}")
        if self.dff_file:
            self.console.append(f"🎯 DFF File: {Path(self.dff_file).name}")
        if manual_input:
            manual_count = len([name.strip() for name in manual_input.split(',') if name.strip()])
            self.console.append(f"🎯 Manual players: {manual_count}")

        # Start optimization thread
        self.optimization_thread = OptimizationThread(self.dk_file, self.dff_file, manual_input)
        self.optimization_thread.progress_updated.connect(self.on_progress_updated)
        self.optimization_thread.optimization_completed.connect(self.on_optimization_completed)
        self.optimization_thread.optimization_failed.connect(self.on_optimization_failed)
        self.optimization_thread.start()

    def on_progress_updated(self, message):
        """Handle progress updates"""
        self.console.append(message)

    def on_optimization_completed(self, lineup, score, summary):
        """Handle successful optimization"""
        self.console.append("\n✅ STRICT OPTIMIZATION COMPLETED!")

        # Final verification
        unconfirmed = [p for p in lineup if not p.is_eligible_for_selection()]
        if unconfirmed:
            self.console.append(f"\n🚨 CRITICAL ERROR: {len(unconfirmed)} unconfirmed players detected!")
            for p in unconfirmed:
                self.console.append(f"   ❌ {p.name} - {p.get_status_string()}")

            QMessageBox.critical(self, "Verification Failed", 
                               f"🚨 CRITICAL ERROR!\n\n{len(unconfirmed)} unconfirmed players in lineup.\nThis should NEVER happen!")
        else:
            self.console.append("🔒 FINAL VERIFICATION: All players confirmed/manual ✅")

            # Update results
            self.update_results(lineup, score, summary)
            self.tab_widget.setCurrentIndex(1)

            QMessageBox.information(self, "Success!", 
                                  f"🔒 STRICT optimization successful!\n\n"
                                  f"Generated {len(lineup)} player lineup\n"
                                  f"Projected score: {score:.2f} points\n"
                                  f"All players verified as confirmed/manual!")

        self._reset_ui()

    def on_optimization_failed(self, error_message):
        """Handle optimization failure"""
        self.console.append(f"\n❌ OPTIMIZATION FAILED: {error_message}")

        QMessageBox.critical(self, "Optimization Failed", 
                           f"❌ Strict optimization failed:\n\n{error_message}\n\n"
                           f"💡 Try adding more manual players or wait for confirmed lineups")

        self._reset_ui()

    def _reset_ui(self):
        """Reset UI after optimization"""
        self.optimize_btn.setEnabled(True)
        self.optimize_btn.setText("🔒 OPTIMIZE (STRICT CONFIRMED ONLY)")
        self.progress_bar.setVisible(False)

    def update_results(self, lineup, score, summary):
        """Update results display"""
        # Update summary
        total_salary = sum(p.salary for p in lineup)
        confirmed_count = sum(1 for p in lineup if p.is_confirmed)
        manual_count = sum(1 for p in lineup if p.is_manual_selected)

        summary_text = f"""
        <b>🔒 STRICT OPTIMIZATION SUCCESS</b><br><br>
        💰 <b>Salary:</b> ${total_salary:,} / $50,000 (${50000 - total_salary:,} remaining)<br>
        📊 <b>Projected Score:</b> {score:.2f} points<br>
        ✅ <b>Confirmed Players:</b> {confirmed_count}/10<br>
        🎯 <b>Manual Players:</b> {manual_count}/10<br><br>
        <b>🔒 VERIFICATION:</b> All players are confirmed or manually selected!
        """

        self.results_summary.setText(summary_text)

        # Update table
        self.lineup_table.setRowCount(len(lineup))

        for row, player in enumerate(lineup):
            self.lineup_table.setItem(row, 0, QTableWidgetItem(player.primary_position))
            self.lineup_table.setItem(row, 1, QTableWidgetItem(player.name))
            self.lineup_table.setItem(row, 2, QTableWidgetItem(player.team))
            self.lineup_table.setItem(row, 3, QTableWidgetItem(f"${player.salary:,}"))
            self.lineup_table.setItem(row, 4, QTableWidgetItem(f"{player.enhanced_score:.1f}"))
            self.lineup_table.setItem(row, 5, QTableWidgetItem(player.get_status_string()))

        # Update import text
        player_names = [player.name for player in lineup]
        import_string = ", ".join(player_names)
        self.import_text.setPlainText(import_string)

    def copy_to_clipboard(self):
        """Copy lineup to clipboard"""
        text = self.import_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "Copied!", 
                                  "✅ Lineup copied to clipboard!\n\nPaste into DraftKings to import your lineup.")
        else:
            QMessageBox.warning(self, "No Lineup", "No lineup to copy. Run optimization first.")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Strict DFS Optimizer")

    # Create and show main window
    window = StrictDFSGUI()
    window.show()

    print("✅ Strict DFS GUI launched successfully!")
    print("🔒 Guaranteed: NO unconfirmed players will leak through")

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
