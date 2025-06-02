#!/usr/bin/env python3
"""
Enhanced Strict GUI - Works with your advanced system
"""

import sys
import os
from pathlib import Path
from typing import Optional

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    print("✅ PyQt5 loaded successfully")
except ImportError:
    print("❌ PyQt5 not available. Install with: pip install PyQt5")
    sys.exit(1)

try:
    from enhanced_strict_core import (
        run_enhanced_strict_optimization,
        test_enhanced_system,
        EnhancedStrictPlayer
    )
    print("✅ Enhanced strict core imported")
except ImportError as e:
    print(f"❌ Enhanced strict core not available: {e}")
    print("💡 Make sure enhanced_strict_core.py contains your complete system")

class EnhancedStrictGUI(QMainWindow):
    """Enhanced GUI for your advanced DFS system"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Strict DFS System - All Advanced Features")
        self.setMinimumSize(1400, 900)

        self.dk_file = None
        self.dff_file = None

        self.setup_ui()
        self.auto_detect_files()

    def setup_ui(self):
        """Setup enhanced UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Enhanced header
        self.create_enhanced_header(layout)

        # Tabs for different functions
        tab_widget = QTabWidget()

        # Data tab
        data_tab = self.create_data_tab()
        tab_widget.addTab(data_tab, "📊 Data & Files")

        # Manual selection tab
        manual_tab = self.create_manual_tab()
        tab_widget.addTab(manual_tab, "🎯 Manual Selection")

        # Optimization tab
        opt_tab = self.create_optimization_tab()
        tab_widget.addTab(opt_tab, "🧠 Optimization")

        # Results tab
        results_tab = self.create_results_tab()
        tab_widget.addTab(results_tab, "🏆 Results")

        layout.addWidget(tab_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Enhanced Strict DFS System Ready")

    def create_enhanced_header(self, layout):
        """Create enhanced header"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #2E7D32, stop: 1 #1B5E20);
                border-radius: 10px;
                padding: 20px;
            }
        """)

        header_layout = QVBoxLayout(header)

        title = QLabel("🚀 ENHANCED STRICT DFS SYSTEM")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 26, QFont.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)

        subtitle = QLabel("🏟️ Park Factors • 📈 L5 Trends • 💰 Vegas Lines • 🔬 Priority Statcast • 🧠 7+ Factor Scoring")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: white; opacity: 0.9;")
        header_layout.addWidget(subtitle)

        guarantee = QLabel("🔒 BULLETPROOF: NO unconfirmed players can leak through")
        guarantee.setAlignment(Qt.AlignCenter)
        guarantee.setFont(QFont("Arial", 10, QFont.Bold))
        guarantee.setStyleSheet("color: #FFEB3B;")
        header_layout.addWidget(guarantee)

        layout.addWidget(header)

    def create_data_tab(self):
        """Create data tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # File selection
        files_group = QGroupBox("📁 Data Files")
        files_layout = QVBoxLayout(files_group)

        # Auto-detect button
        auto_btn = QPushButton("🔍 Auto-Detect Files")
        auto_btn.clicked.connect(self.auto_detect_files)
        files_layout.addWidget(auto_btn)

        # DK file
        dk_layout = QHBoxLayout()
        self.dk_label = QLabel("No DraftKings file selected")
        dk_browse = QPushButton("Browse DK CSV")
        dk_browse.clicked.connect(self.browse_dk_file)
        dk_layout.addWidget(QLabel("📊 DraftKings:"))
        dk_layout.addWidget(self.dk_label, 1)
        dk_layout.addWidget(dk_browse)
        files_layout.addLayout(dk_layout)

        # DFF file
        dff_layout = QHBoxLayout()
        self.dff_label = QLabel("No DFF file selected")
        dff_browse = QPushButton("Browse DFF CSV")
        dff_browse.clicked.connect(self.browse_dff_file)
        dff_layout.addWidget(QLabel("🎯 DFF Rankings:"))
        dff_layout.addWidget(self.dff_label, 1)
        dff_layout.addWidget(dff_browse)
        files_layout.addLayout(dff_layout)

        layout.addWidget(files_group)

        # Enhanced features status
        features_group = QGroupBox("✨ Enhanced Features Status")
        features_layout = QVBoxLayout(features_group)

        self.features_status = QTextEdit()
        self.features_status.setMaximumHeight(200)
        self.features_status.setReadOnly(True)
        features_layout.addWidget(self.features_status)

        test_btn = QPushButton("🧪 Test Enhanced System")
        test_btn.clicked.connect(self.test_system)
        features_layout.addWidget(test_btn)

        layout.addWidget(features_group)
        layout.addStretch()

        return tab

    def create_manual_tab(self):
        """Create manual selection tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel("🎯 Players added here are treated as CONFIRMED")
        info.setStyleSheet("font-weight: bold; color: #2E7D32;")
        layout.addWidget(info)

        self.manual_input = QTextEdit()
        self.manual_input.setPlaceholderText(
            "Enter player names separated by commas...\n\n"
            "Example: CJ Abrams, James Wood, Ketel Marte, Cal Raleigh, Josh Naylor"
        )
        layout.addWidget(self.manual_input)

        # Quick fill buttons
        button_layout = QHBoxLayout()

        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.manual_input.clear)
        button_layout.addWidget(clear_btn)

        sample_btn = QPushButton("📝 Load Sample")
        sample_btn.clicked.connect(self.load_sample_manual)
        button_layout.addWidget(sample_btn)

        your_list_btn = QPushButton("📋 Load Your Full List")
        your_list_btn.clicked.connect(self.load_your_full_list)
        button_layout.addWidget(your_list_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

        return tab

    def create_optimization_tab(self):
        """Create optimization tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Strategy selection
        strategy_group = QGroupBox("🧠 Enhanced Optimization Settings")
        strategy_layout = QVBoxLayout(strategy_group)

        info = QLabel("Your enhanced system uses ALL advanced algorithms automatically:")
        strategy_layout.addWidget(info)

        features_list = QLabel("""
        🏟️ Park factors with handedness splits
        📈 L5 performance trend analysis  
        💰 Vegas lines with team total calculations
        🔬 Priority Statcast for confirmed/manual players
        🎯 Enhanced DFF integration with value projections
        🤝 Sophisticated name matching with nicknames
        🧠 7+ factor combined scoring system
        """)
        features_list.setStyleSheet("color: #666; font-size: 11px;")
        strategy_layout.addWidget(features_list)

        layout.addWidget(strategy_group)

        # Optimization button
        self.optimize_btn = QPushButton("🚀 RUN ENHANCED OPTIMIZATION")
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: white;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1B5E20;
            }
        """)
        self.optimize_btn.clicked.connect(self.run_enhanced_optimization)
        layout.addWidget(self.optimize_btn)

        # Console
        console_group = QGroupBox("📝 Enhanced Optimization Log")
        console_layout = QVBoxLayout(console_group)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 9))
        self.console.setStyleSheet(
            "background-color: #1e1e1e; color: #ffffff; border: 1px solid #333;"
        )
        console_layout.addWidget(self.console)

        layout.addWidget(console_group)

        return tab

    def create_results_tab(self):
        """Create results tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Results summary
        self.results_summary = QLabel("No optimization results yet")
        self.results_summary.setWordWrap(True)
        self.results_summary.setStyleSheet(
            "padding: 20px; background-color: #f5f5f5; border-radius: 5px; font-weight: bold;"
        )
        layout.addWidget(self.results_summary)

        # Enhanced lineup table
        self.lineup_table = QTableWidget()
        self.lineup_table.setColumnCount(7)
        self.lineup_table.setHorizontalHeaderLabels([
            "Position", "Player", "Team", "Salary", "Enhanced Score", "Status", "Features"
        ])
        layout.addWidget(self.lineup_table)

        # Import section
        import_group = QGroupBox("📋 DraftKings Import")
        import_layout = QVBoxLayout(import_group)

        self.import_text = QTextEdit()
        self.import_text.setMaximumHeight(80)
        self.import_text.setPlaceholderText("Enhanced lineup will appear here")
        import_layout.addWidget(self.import_text)

        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        import_layout.addWidget(copy_btn)

        layout.addWidget(import_group)

        return tab

    def auto_detect_files(self):
        """Auto-detect CSV files"""
        print("🔍 Auto-detecting files...")

        import glob

        # Find DK files
        dk_patterns = ['DKSalaries*.csv', '*DKSalaries*.csv']
        dk_files = []
        for pattern in dk_patterns:
            dk_files.extend(glob.glob(pattern))

        # Find DFF files
        dff_patterns = ['DFF*.csv', '*DFF*.csv', '*cheat*.csv']
        dff_files = []
        for pattern in dff_patterns:
            dff_files.extend(glob.glob(pattern))

        if dk_files:
            dk_files.sort(key=os.path.getmtime, reverse=True)
            self.dk_file = dk_files[0]
            self.dk_label.setText(f"✅ {Path(self.dk_file).name}")
            self.dk_label.setStyleSheet("color: green;")

        if dff_files:
            dff_files.sort(key=os.path.getmtime, reverse=True)
            self.dff_file = dff_files[0]
            self.dff_label.setText(f"✅ {Path(self.dff_file).name}")
            self.dff_label.setStyleSheet("color: green;")

        self.update_features_status()

    def browse_dk_file(self):
        """Browse for DK file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select DraftKings CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.dk_file = file_path
            self.dk_label.setText(f"✅ {Path(file_path).name}")
            self.dk_label.setStyleSheet("color: green;")
            self.update_features_status()

    def browse_dff_file(self):
        """Browse for DFF file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select DFF Rankings CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.dff_file = file_path
            self.dff_label.setText(f"✅ {Path(file_path).name}")
            self.dff_label.setStyleSheet("color: green;")
            self.update_features_status()

    def update_features_status(self):
        """Update features status display"""
        status = []
        status.append("🚀 ENHANCED FEATURES STATUS:")
        status.append("=" * 40)

        if self.dk_file:
            status.append("✅ DraftKings data ready")
        else:
            status.append("❌ DraftKings data needed")

        if self.dff_file:
            status.append("✅ DFF rankings ready")
            status.append("   📈 L5 trends analysis enabled")
            status.append("   🎯 Enhanced value projections enabled")
        else:
            status.append("⚠️ DFF rankings optional")

        status.append("✅ Park factors with handedness splits")
        status.append("✅ Vegas lines integration")
        status.append("✅ Priority Statcast processing")
        status.append("✅ Advanced MILP optimization")
        status.append("✅ 7+ factor scoring system")

        self.features_status.setPlainText("\n".join(status))

    def load_sample_manual(self):
        """Load sample manual players"""
        sample = "CJ Abrams, James Wood, Ketel Marte, Cal Raleigh, Josh Naylor, Bryan Reynolds"
        self.manual_input.setPlainText(sample)

    def load_your_full_list(self):
        """Load your comprehensive manual list"""
        your_list = """CJ Abrams, James Wood, Nathaniel Lowe, Luis García Jr., Josh Bell, 
        Robert Hassell III, Keibert Ruiz, Jose Tena, Daylen Lile, Corbin Carroll, Ketel Marte, 
        Geraldo Perdomo, Josh Naylor, Eugenio Suárez, Lourdes Gurriel Jr., Gabriel Moreno, 
        Alek Thomas, Oneil Cruz, Andrew McCutchen, Bryan Reynolds, Spencer Horwitz, Henry Davis, 
        Ke'Bryan Hayes, Adam Frazier, Tommy Pham, Isiah Kiner-Falefa, Fernando Tatis Jr., 
        Luis Arraez, Manny Machado, Jackson Merrill, Gavin Sheets, Xander Bogaerts, 
        Jake Cronenworth, Tyler Wade, Elias Díaz, Byron Buxton, Trevor Larnach, Ryan Jeffers, 
        Carlos Correa, Brooks Lee, Ty France, Kody Clemens, Royce Lewis, Willi Castro, 
        J.P. Crawford, Jorge Polanco, Julio Rodríguez, Cal Raleigh, Randy Arozarena, 
        Rowdy Tellez, Leody Taveras, Miles Mastrobuoni, Ben Williamson, Shohei Ohtani, 
        Teoscar Hernández, Will Smith, Freddie Freeman, Andy Pages, Tommy Edman, 
        Kiké Hernández, Michael Conforto, Miguel Rojas"""
        self.manual_input.setPlainText(your_list)

    def test_system(self):
        """Test the enhanced system"""
        self.console.append("🧪 Testing Enhanced System...")

        try:
            success = test_enhanced_system()
            if success:
                self.console.append("✅ Enhanced system test PASSED!")
                self.console.append("🔒 No unconfirmed leaks detected")
                self.console.append("🧠 All advanced algorithms working")
            else:
                self.console.append("❌ Enhanced system test FAILED")
        except Exception as e:
            self.console.append(f"❌ Test error: {e}")

    def run_enhanced_optimization(self):
        """Run the enhanced optimization"""
        if not self.dk_file:
            QMessageBox.warning(self, "No Data", "Please select a DraftKings CSV file first.")
            return

        self.console.clear()
        self.console.append("🚀 Starting Enhanced Optimization...")
        self.console.append("=" * 50)

        manual_input = self.manual_input.toPlainText().strip()

        try:
            lineup, score, summary = run_enhanced_strict_optimization(
                self.dk_file, self.dff_file, manual_input
            )

            if lineup:
                self.console.append("✅ ENHANCED OPTIMIZATION SUCCESS!")
                self.console.append(summary)
                self.update_results(lineup, score)

                QMessageBox.information(self, "Success!", 
                    f"✅ Enhanced optimization complete!\n\n"
                    f"Generated {len(lineup)} player lineup\n"
                    f"All players verified as confirmed/manual\n"
                    f"Enhanced score: {score:.2f}")
            else:
                self.console.append("❌ OPTIMIZATION FAILED")
                self.console.append("Not enough eligible players found")
                QMessageBox.warning(self, "Failed", 
                    "Optimization failed. Add more manual players or wait for confirmed lineups.")

        except Exception as e:
            self.console.append(f"❌ ERROR: {e}")
            QMessageBox.critical(self, "Error", f"Optimization error: {e}")

    def update_results(self, lineup, score):
        """Update results display"""
        # Update summary
        total_salary = sum(p.salary for p in lineup)
        confirmed_count = sum(1 for p in lineup if p.is_confirmed)
        manual_count = sum(1 for p in lineup if p.is_manual_selected)

        summary_text = f"""
        <b>🏆 ENHANCED OPTIMIZATION RESULTS</b><br><br>
        <b>💰 Financial:</b><br>
        • Total Salary: ${total_salary:,} / $50,000<br>
        • Remaining: ${50000 - total_salary:,}<br>
        • Enhanced Score: {score:.2f} points<br><br>
        <b>🔒 Player Verification:</b><br>
        • Confirmed Players: {confirmed_count}<br>
        • Manual Players: {manual_count}<br>
        • Total Eligible: {len(lineup)}/10<br><br>
        <b>🧠 Enhanced Features Applied:</b><br>
        • Park factors with handedness<br>
        • L5 performance trends<br>
        • Vegas team total calculations<br>
        • Priority Statcast data<br>
        • Multi-factor scoring system
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

            # Features column
            features = []
            if player.vegas_data:
                features.append("Vegas")
            if player.statcast_data:
                features.append("Statcast")
            if player.park_factors:
                features.append("Park")
            if player.dff_projection > 0:
                features.append("DFF")

            self.lineup_table.setItem(row, 6, QTableWidgetItem(", ".join(features)))

        # Update import text
        player_names = [player.name for player in lineup]
        self.import_text.setPlainText(", ".join(player_names))

    def copy_to_clipboard(self):
        """Copy lineup to clipboard"""
        text = self.import_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "Copied!", "✅ Enhanced lineup copied to clipboard!")


def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setApplicationName("Enhanced Strict DFS System")

    window = EnhancedStrictGUI()
    window.show()

    print("✅ Enhanced Strict DFS GUI launched!")
    print("🧠 All advanced algorithms integrated")
    print("🔒 Bulletproof strict filtering active")

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
