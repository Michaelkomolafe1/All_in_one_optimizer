#!/usr/bin/env python3
"""
CLEAN DFS OPTIMIZER GUI
=======================
Modern, maintainable GUI for DFS optimization
"""

import sys
import os
import csv
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from bankroll_management import BankrollManagementWidget, update_clean_gui_with_bankroll
# Import PyQt5
try:
    from bankroll_management import BankrollManagementWidget, update_clean_gui_with_bankroll
    BANKROLL_AVAILABLE = True
except ImportError:
    print("⚠️ Bankroll management not found. Some features will be limited.")
    BANKROLL_AVAILABLE = False

# Import core systems with proper error handling
try:
    from bulletproof_dfs_core import BulletproofDFSCore
    CORE_AVAILABLE = True
except ImportError:
    print("⚠️ Core optimizer not found. Some features will be limited.")
    CORE_AVAILABLE = False
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
except ImportError:
    print("❌ PyQt5 not available. Install with: pip install PyQt5")
    sys.exit(1)

# Import core systems with proper error handling
try:
    from bulletproof_dfs_core import BulletproofDFSCore

    CORE_AVAILABLE = True
except ImportError:
    print("⚠️ Core optimizer not found. Some features will be limited.")
    CORE_AVAILABLE = False


    # Mock class for testing
    class BulletproofDFSCore:
        def __init__(self):
            self.players = []
            self.optimization_mode = 'bulletproof'

        def load_draftkings_csv(self, path):
            return True

        def set_optimization_mode(self, mode):
            self.optimization_mode = mode

        def apply_manual_selection(self, text):
            return 5

        def detect_confirmed_players(self):
            return 10

        def optimize_lineup_with_mode(self):
            # Return mock lineup
            from types import SimpleNamespace
            mock_players = []
            for i in range(10):
                player = SimpleNamespace(
                    name=f"Player {i + 1}",
                    primary_position=['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'P'][i],
                    team="NYY",
                    salary=5000 - i * 100,
                    enhanced_score=10.5 + i * 0.5,
                    is_confirmed=True
                )
                mock_players.append(player)
            return mock_players, 105.5

        def generate_contest_lineups(self, count, contest_type):
            lineups = []
            for i in range(count):
                lineup, score = self.optimize_lineup_with_mode()
                lineups.append({
                    'lineup_id': i + 1,
                    'lineup': lineup,
                    'total_score': score + i,
                    'total_salary': 48000 + i * 100,
                    'contest_type': contest_type
                })
            return lineups


class OptimizationWorker(QObject):
    """Worker for background optimization"""

    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, core, settings):
        super().__init__()
        self.core = core
        self.settings = settings

    def run(self):
        """Run optimization"""
        try:
            self.progress.emit("Starting optimization...")

            # Apply settings
            self.core.set_optimization_mode(self.settings['mode'])

            if self.settings['manual_players']:
                count = self.core.apply_manual_selection(self.settings['manual_players'])
                self.progress.emit(f"Applied {count} manual selections")

            # Detect confirmations
            if self.settings['mode'] != 'manual_only':
                confirmed = self.core.detect_confirmed_players()
                self.progress.emit(f"Found {confirmed} confirmed players")

            # Generate lineups
            if self.settings['multi_lineup']:
                self.progress.emit(f"Generating {self.settings['lineup_count']} lineups...")
                lineups = self.core.generate_contest_lineups(
                    self.settings['lineup_count'],
                    self.settings['contest_type']
                )
                self.finished.emit(lineups)
            else:
                self.progress.emit("Optimizing single lineup...")
                lineup, score = self.core.optimize_lineup_with_mode()
                if lineup:
                    self.finished.emit([{
                        'lineup_id': 1,
                        'lineup': lineup,
                        'total_score': score,
                        'total_salary': sum(p.salary for p in lineup),
                        'contest_type': self.settings['contest_type']
                    }])
                else:
                    self.error.emit("No valid lineup found")

        except Exception as e:
            self.error.emit(str(e))


class DFSOptimizerGUI(QMainWindow):
    """Main GUI window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DFS Optimizer Pro")
        self.setMinimumSize(1200, 800)

        # Data
        self.dk_file = ""
        self.dff_file = ""
        self.core = None
        self.last_results = []

        # Setup
        self.setup_ui()
        self.apply_theme()
        self.load_settings()
        self.auto_detect_files()

    def setup_ui(self):
        """Create UI elements"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        self.create_header(main_layout)

        # Content area with splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Control tabs
        self.control_tabs = QTabWidget()
        self.control_tabs.addTab(self.create_data_tab(), "📁 Data")
        self.control_tabs.addTab(self.create_settings_tab(), "⚙️ Settings")
        self.control_tabs.addTab(self.create_lineup_tab(), "🎯 Lineups")

        left_layout.addWidget(self.control_tabs)

        # Optimize button
        self.optimize_btn = QPushButton("🚀 Generate Optimal Lineup")
        self.optimize_btn.setMinimumHeight(60)
        self.optimize_btn.clicked.connect(self.run_optimization)
        self.optimize_btn.setEnabled(False)
        left_layout.addWidget(self.optimize_btn)

        # Right panel - Results
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Results tabs
        self.results_tabs = QTabWidget()
        self.results_tabs.addTab(self.create_console_tab(), "📋 Console")
        self.results_tabs.addTab(self.create_results_tab(), "📊 Results")
        self.results_tabs.addTab(self.create_analytics_tab(), "📈 Analytics")

        right_layout.addWidget(self.results_tabs)

        # Add to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 800])

        main_layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Progress bar in status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def create_header(self, layout):
        """Create application header"""
        header = QFrame()
        header.setMaximumHeight(80)
        header_layout = QHBoxLayout(header)

        # Logo/Title
        title_layout = QVBoxLayout()
        title = QLabel("DFS Optimizer Pro")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e40af;")
        subtitle = QLabel("Advanced Daily Fantasy Sports Lineup Optimization")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        # Quick actions
        actions_layout = QHBoxLayout()

        # Quick generate buttons
        for label, count, contest in [("5 Cash", 5, "cash"), ("20 GPP", 20, "gpp"), ("150 Max", 150, "gpp")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, c=count, t=contest: self.quick_generate(c, t))
            actions_layout.addWidget(btn)

        header_layout.addLayout(actions_layout)

        layout.addWidget(header)

    def create_data_tab(self):
        """Create data input tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # DraftKings file
        dk_group = QGroupBox("DraftKings CSV")
        dk_layout = QVBoxLayout(dk_group)

        self.dk_label = QLabel("No file selected")
        self.dk_label.setStyleSheet("""
            QLabel {
                padding: 20px;
                border: 2px dashed #cbd5e1;
                border-radius: 8px;
                background-color: #f8fafc;
            }
        """)
        self.dk_label.setAlignment(Qt.AlignCenter)

        dk_btn_layout = QHBoxLayout()
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.select_dk_file)

        download_btn = QPushButton("Download Latest")
        download_btn.clicked.connect(self.download_dk_file)

        dk_btn_layout.addWidget(browse_btn)
        dk_btn_layout.addWidget(download_btn)

        dk_layout.addWidget(self.dk_label)
        dk_layout.addLayout(dk_btn_layout)

        layout.addWidget(dk_group)

        # DFF file (optional)
        dff_group = QGroupBox("DFF Rankings (Optional)")
        dff_layout = QVBoxLayout(dff_group)

        self.dff_label = QLabel("No file selected")
        self.dff_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                border: 2px dashed #cbd5e1;
                border-radius: 8px;
                background-color: #f8fafc;
            }
        """)
        self.dff_label.setAlignment(Qt.AlignCenter)

        dff_btn = QPushButton("Browse DFF")
        dff_btn.clicked.connect(self.select_dff_file)

        dff_layout.addWidget(self.dff_label)
        dff_layout.addWidget(dff_btn)

        layout.addWidget(dff_group)

        # Manual players
        manual_group = QGroupBox("Manual Player Selection")
        manual_layout = QVBoxLayout(manual_group)

        self.manual_input = QTextEdit()
        self.manual_input.setMaximumHeight(100)
        self.manual_input.setPlaceholderText("Enter player names separated by commas...")

        manual_btn_layout = QHBoxLayout()

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.manual_input.clear)

        sample_btn = QPushButton("Load Sample")
        sample_btn.clicked.connect(self.load_sample_players)

        manual_btn_layout.addWidget(clear_btn)
        manual_btn_layout.addWidget(sample_btn)

        manual_layout.addWidget(self.manual_input)
        manual_layout.addLayout(manual_btn_layout)

        layout.addWidget(manual_group)

        # Test data
        test_btn = QPushButton("🧪 Create Test Data")
        test_btn.clicked.connect(self.create_test_data)
        layout.addWidget(test_btn)

        layout.addStretch()

        return widget

    def update_starting_bankroll(self):
        """Update the starting bankroll"""
        new_starting = self.new_starting_bankroll.value()

        # Confirm the change
        if self.adjust_current.isChecked():
            message = (f"This will change your starting bankroll to ${new_starting:,.2f} "
                       f"and set your current bankroll to the same amount.\n\n"
                       f"Continue?")
        else:
            message = (f"This will change your starting bankroll to ${new_starting:,.2f}.\n"
                       f"Your current bankroll will remain at ${self.manager.data['current_bankroll']:,.2f}.\n\n"
                       f"Continue?")

        reply = QMessageBox.question(
            self, "Confirm Bankroll Change",
            message,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Update starting bankroll
            old_starting = self.manager.data['starting_bankroll']
            self.manager.data['starting_bankroll'] = new_starting

            # Optionally update current bankroll
            if self.adjust_current.isChecked():
                old_current = self.manager.data['current_bankroll']
                self.manager.data['current_bankroll'] = new_starting

                # Add a transaction to record this
                transaction = {
                    'date': datetime.now().isoformat(),
                    'type': 'Bankroll Adjustment',
                    'amount': new_starting - old_current,
                    'notes': f'Bankroll adjusted from ${old_current:.2f} to ${new_starting:.2f}',
                    'balance': new_starting
                }
                self.manager.data['transactions'].append(transaction)

            # Save and refresh
            self.manager.save_data()

            # Force refresh ALL tabs
            self.refresh_all_tabs()

            QMessageBox.information(
                self, "Success",
                f"Starting bankroll updated to ${new_starting:,.2f}" +
                (f"\nCurrent bankroll updated to ${new_starting:,.2f}" if self.adjust_current.isChecked() else "")
            )

    def refresh_all_tabs(self):
        """Force refresh all tabs"""
        # Save current tab
        current_tab = self.tabs.currentIndex()

        # Clear and recreate all tabs
        self.tabs.clear()

        self.tabs.addTab(self.create_overview_tab(), "📊 Overview")
        self.tabs.addTab(self.create_recommendations_tab(), "🎯 Recommendations")
        self.tabs.addTab(self.create_calculator_tab(), "🧮 Calculators")
        self.tabs.addTab(self.create_history_tab(), "📈 History")
        self.tabs.addTab(self.create_settings_tab(), "⚙️ Settings")

        # Restore tab
        self.tabs.setCurrentIndex(current_tab)

    class SmartContestRecommendation(QWidget):
        """Smart contest recommendation widget that updates automatically"""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.parent = parent
            self.manager = BankrollManager()
            self.setup_ui()

            # Auto-refresh timer
            self.timer = QTimer()
            self.timer.timeout.connect(self.auto_update)
            self.timer.start(1000)  # Check every second

            self.last_bankroll = self.manager.data['current_bankroll']

        def setup_ui(self):
            layout = QVBoxLayout(self)

            # Live recommendations card
            self.reco_card = QGroupBox("🎯 Live Contest Recommendations")
            self.reco_card.setStyleSheet("""
                QGroupBox {
                    background-color: #f0f9ff;
                    border: 2px solid #3b82f6;
                    border-radius: 8px;
                    font-weight: bold;
                }
            """)

            self.reco_layout = QVBoxLayout(self.reco_card)
            layout.addWidget(self.reco_card)

            # Initial update
            self.update_recommendations()

        def auto_update(self):
            """Check if bankroll changed and update recommendations"""
            current_bankroll = self.manager.data['current_bankroll']

            if current_bankroll != self.last_bankroll:
                self.last_bankroll = current_bankroll
                self.update_recommendations()
                self.flash_update()  # Visual feedback

        def flash_update(self):
            """Flash the card to show it updated"""
            self.reco_card.setStyleSheet("""
                QGroupBox {
                    background-color: #dbeafe;
                    border: 3px solid #2563eb;
                    border-radius: 8px;
                    font-weight: bold;
                }
            """)

            QTimer.singleShot(500, lambda: self.reco_card.setStyleSheet("""
                QGroupBox {
                    background-color: #f0f9ff;
                    border: 2px solid #3b82f6;
                    border-radius: 8px;
                    font-weight: bold;
                }
            """))

        def update_recommendations(self):
            """Update recommendations based on current bankroll"""
            # Clear current layout
            while self.reco_layout.count():
                child = self.reco_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            bankroll = self.manager.data['current_bankroll']
            risk = self.manager.data['settings']['risk_tolerance']

            # Bankroll status
            status_label = QLabel(f"💰 Current Bankroll: ${bankroll:,.2f}")
            status_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
            self.reco_layout.addWidget(status_label)

            # Get smart recommendations
            recommendations = self.get_smart_recommendations(bankroll, risk)

            # Display recommendations
            for reco in recommendations:
                reco_widget = self.create_recommendation_widget(reco)
                self.reco_layout.addWidget(reco_widget)

            # Action button
            action_btn = QPushButton("🚀 Generate Recommended Lineups")
            action_btn.clicked.connect(self.execute_recommendations)
            action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 6px;
                    margin-top: 10px;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
            """)
            self.reco_layout.addWidget(action_btn)

        def get_smart_recommendations(self, bankroll: float, risk: str) -> List[Dict]:
            """Get smart recommendations based on current bankroll"""
            recommendations = []

            # Daily budget
            daily_budget = bankroll * {'conservative': 0.05, 'moderate': 0.10,
                                       'aggressive': 0.15, 'very_aggressive': 0.20}.get(risk, 0.10)

            if bankroll < 50:
                # Micro stakes
                recommendations.append({
                    'icon': '🎯',
                    'title': 'Micro Stakes Strategy',
                    'contest': 'Free Contests + $0.25 Games',
                    'lineups': 1,
                    'reason': 'Build bankroll risk-free',
                    'budget': min(5, daily_budget),
                    'warning': 'Critical: Bankroll too low for paid contests'
                })

            elif bankroll < 100:
                # Low stakes
                recommendations.append({
                    'icon': '💵',
                    'title': 'Low Stakes Cash Games',
                    'contest': '$1-$3 50/50s',
                    'lineups': 2,
                    'reason': 'Steady growth with low variance',
                    'budget': daily_budget * 0.8
                })
                recommendations.append({
                    'icon': '🎰',
                    'title': 'Micro GPPs',
                    'contest': '$0.25-$1 Tournaments',
                    'lineups': 5,
                    'reason': 'Low risk upside plays',
                    'budget': daily_budget * 0.2
                })

            elif bankroll < 500:
                # Mid stakes
                recommendations.append({
                    'icon': '💰',
                    'title': 'Cash Game Core',
                    'contest': '$5-$10 Double-Ups',
                    'lineups': 3,
                    'reason': 'Consistent profits at higher stakes',
                    'budget': daily_budget * 0.6
                })
                recommendations.append({
                    'icon': '🏆',
                    'title': 'Single Entry GPPs',
                    'contest': '$3-$20 Single Entry',
                    'lineups': 1,
                    'reason': 'Better ROI than multi-entry',
                    'budget': daily_budget * 0.3
                })
                recommendations.append({
                    'icon': '🎲',
                    'title': 'Small Multi-Entry',
                    'contest': '$1-$3 20-max',
                    'lineups': 10,
                    'reason': 'Diversified tournament exposure',
                    'budget': daily_budget * 0.1
                })

            elif bankroll < 1000:
                # Standard stakes
                recommendations.append({
                    'icon': '💎',
                    'title': 'Premium Cash Games',
                    'contest': '$25-$50 Games',
                    'lineups': 2,
                    'reason': 'Lower rake percentage',
                    'budget': daily_budget * 0.5
                })
                recommendations.append({
                    'icon': '🚀',
                    'title': 'Featured GPPs',
                    'contest': '$5-$25 Tournaments',
                    'lineups': 15,
                    'reason': 'Larger prize pools available',
                    'budget': daily_budget * 0.4
                })
                recommendations.append({
                    'icon': '🎯',
                    'title': 'Satellites',
                    'contest': '$5-$10 Qualifiers',
                    'lineups': 2,
                    'reason': 'Win entries to bigger contests',
                    'budget': daily_budget * 0.1
                })

            else:
                # High stakes
                recommendations.append({
                    'icon': '👑',
                    'title': 'High Stakes Cash',
                    'contest': '$100+ Games',
                    'lineups': 1,
                    'reason': 'Minimal rake impact',
                    'budget': daily_budget * 0.4
                })
                recommendations.append({
                    'icon': '🏆',
                    'title': 'Major GPPs',
                    'contest': '$20+ Tournaments',
                    'lineups': 50,
                    'reason': 'Chase life-changing scores',
                    'budget': daily_budget * 0.5
                })
                recommendations.append({
                    'icon': '💫',
                    'title': 'Live Finals Satellites',
                    'contest': 'Qualifier Tournaments',
                    'lineups': 5,
                    'reason': 'Win trips to live events',
                    'budget': daily_budget * 0.1
                })

            return recommendations

        def create_recommendation_widget(self, reco: Dict) -> QWidget:
            """Create a widget for a single recommendation"""
            widget = QFrame()
            widget.setFrameStyle(QFrame.Box)
            widget.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 10px;
                    margin: 5px 0;
                }
            """)

            layout = QVBoxLayout(widget)

            # Header
            header_layout = QHBoxLayout()

            icon_label = QLabel(reco['icon'])
            icon_label.setStyleSheet("font-size: 24px;")

            title_label = QLabel(reco['title'])
            title_label.setStyleSheet("font-size: 14px; font-weight: bold;")

            budget_label = QLabel(f"${reco['budget']:.2f}")
            budget_label.setStyleSheet("font-size: 14px; color: #10b981; font-weight: bold;")

            header_layout.addWidget(icon_label)
            header_layout.addWidget(title_label)
            header_layout.addStretch()
            header_layout.addWidget(budget_label)

            layout.addLayout(header_layout)

            # Details
            details = QLabel(f"<b>Contest:</b> {reco['contest']}<br>"
                             f"<b>Lineups:</b> {reco['lineups']}<br>"
                             f"<b>Why:</b> {reco['reason']}")
            details.setWordWrap(True)
            details.setStyleSheet("color: #4b5563; font-size: 12px; margin-top: 5px;")
            layout.addWidget(details)

            # Warning if present
            if 'warning' in reco:
                warning = QLabel(f"⚠️ {reco['warning']}")
                warning.setStyleSheet("color: #dc2626; font-size: 12px; font-weight: bold; margin-top: 5px;")
                layout.addWidget(warning)

            return widget

        def execute_recommendations(self):
            """Execute the current recommendations"""
            # This would integrate with your optimizer
            QMessageBox.information(
                self, "Generate Lineups",
                "This will generate lineups based on the recommendations.\n\n"
                "Feature coming soon!"
            )

    def create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Contest settings
        contest_group = QGroupBox("Contest Settings")
        contest_layout = QFormLayout(contest_group)

        self.contest_type = QComboBox()
        self.contest_type.addItems(["Classic", "Showdown", "Single Entry", "3-Max", "5-Max"])
        contest_layout.addRow("Contest Type:", self.contest_type)

        self.slate_type = QComboBox()
        self.slate_type.addItems(["Main", "Early", "Afternoon", "Night", "All Day"])
        contest_layout.addRow("Slate:", self.slate_type)

        layout.addWidget(contest_group)

        # Optimization settings
        opt_group = QGroupBox("Optimization Settings")
        opt_layout = QFormLayout(opt_group)

        self.opt_mode = QComboBox()
        self.opt_mode.addItems([
            "Bulletproof (Confirmed + Manual)",
            "Manual Only",
            "Confirmed Only",
            "All Players"
        ])
        opt_layout.addRow("Mode:", self.opt_mode)

        self.min_salary = QSpinBox()
        self.min_salary.setRange(45000, 50000)
        self.min_salary.setValue(48000)
        self.min_salary.setSingleStep(500)
        opt_layout.addRow("Min Salary:", self.min_salary)

        self.max_exposure = QSpinBox()
        self.max_exposure.setRange(0, 100)
        self.max_exposure.setValue(60)
        self.max_exposure.setSuffix("%")
        opt_layout.addRow("Max Exposure:", self.max_exposure)

        layout.addWidget(opt_group)

        # Features
        features_group = QGroupBox("Data Sources")
        features_layout = QVBoxLayout(features_group)

        self.use_vegas = QCheckBox("Vegas Lines")
        self.use_vegas.setChecked(True)

        self.use_statcast = QCheckBox("Statcast Data")
        self.use_statcast.setChecked(True)

        self.use_weather = QCheckBox("Weather Data")
        self.use_weather.setChecked(True)

        self.use_trends = QCheckBox("Recent Trends")
        self.use_trends.setChecked(True)

        features_layout.addWidget(self.use_vegas)
        features_layout.addWidget(self.use_statcast)
        features_layout.addWidget(self.use_weather)
        features_layout.addWidget(self.use_trends)

        layout.addWidget(features_group)

        layout.addStretch()

        return widget

    def create_lineup_tab(self):
        """Create lineup generation tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Single vs Multi
        mode_group = QGroupBox("Generation Mode")
        mode_layout = QVBoxLayout(mode_group)

        self.single_radio = QRadioButton("Single Lineup")
        self.single_radio.setChecked(True)
        self.multi_radio = QRadioButton("Multiple Lineups")

        mode_layout.addWidget(self.single_radio)
        mode_layout.addWidget(self.multi_radio)

        layout.addWidget(mode_group)

        # Multi lineup settings
        self.multi_group = QGroupBox("Multiple Lineup Settings")
        multi_layout = QFormLayout(self.multi_group)

        self.lineup_count = QSpinBox()
        self.lineup_count.setRange(2, 150)
        self.lineup_count.setValue(20)
        multi_layout.addRow("Number of Lineups:", self.lineup_count)

        self.diversity = QSlider(Qt.Horizontal)
        self.diversity.setRange(0, 100)
        self.diversity.setValue(70)
        self.diversity_label = QLabel("70%")

        diversity_layout = QHBoxLayout()
        diversity_layout.addWidget(self.diversity)
        diversity_layout.addWidget(self.diversity_label)

        multi_layout.addRow("Diversity:", diversity_layout)

        self.allow_dupes = QCheckBox("Allow duplicate lineups")
        multi_layout.addRow("", self.allow_dupes)

        self.multi_group.setEnabled(False)
        layout.addWidget(self.multi_group)

        # Connect radio buttons
        self.single_radio.toggled.connect(lambda checked: self.multi_group.setEnabled(not checked))
        self.diversity.valueChanged.connect(lambda v: self.diversity_label.setText(f"{v}%"))

        # Presets
        presets_group = QGroupBox("Quick Presets")
        presets_layout = QGridLayout(presets_group)

        preset_buttons = [
            ("Cash Game", self.preset_cash),
            ("GPP", self.preset_gpp),
            ("Single Entry", self.preset_single),
            ("Mass Multi", self.preset_mass)
        ]

        for i, (label, func) in enumerate(preset_buttons):
            btn = QPushButton(label)
            btn.clicked.connect(func)
            presets_layout.addWidget(btn, i // 2, i % 2)

        layout.addWidget(presets_group)

        layout.addStretch()

        return widget

    def create_console_tab(self):
        """Create console output tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 10))

        # Clear button
        clear_btn = QPushButton("Clear Console")
        clear_btn.clicked.connect(self.console.clear)

        layout.addWidget(self.console)
        layout.addWidget(clear_btn)

        return widget

    def create_results_tab(self):
        """Create results display tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Summary card
        self.summary_widget = QWidget()
        self.summary_widget.setMaximumHeight(150)
        summary_layout = QHBoxLayout(self.summary_widget)

        self.score_label = self.create_stat_widget("Score", "0.0")
        self.salary_label = self.create_stat_widget("Salary", "$0")
        self.value_label = self.create_stat_widget("Value", "0.0")

        summary_layout.addWidget(self.score_label)
        summary_layout.addWidget(self.salary_label)
        summary_layout.addWidget(self.value_label)

        layout.addWidget(self.summary_widget)

        # Lineup table
        self.lineup_table = QTableWidget()
        self.lineup_table.setColumnCount(6)
        self.lineup_table.setHorizontalHeaderLabels([
            "Position", "Player", "Team", "Salary", "Projected", "Value"
        ])

        header = self.lineup_table.horizontalHeader()
        header.setStretchLastSection(True)

        layout.addWidget(self.lineup_table)

        # Export buttons
        export_layout = QHBoxLayout()

        copy_btn = QPushButton("📋 Copy Lineup")
        copy_btn.clicked.connect(self.copy_lineup)

        export_csv_btn = QPushButton("💾 Export CSV")
        export_csv_btn.clicked.connect(self.export_csv)

        export_dk_btn = QPushButton("🏈 DraftKings Format")
        export_dk_btn.clicked.connect(self.export_draftkings)

        export_layout.addWidget(copy_btn)
        export_layout.addWidget(export_csv_btn)
        export_layout.addWidget(export_dk_btn)

        layout.addLayout(export_layout)

        return widget

    def create_analytics_tab(self):
        """Create analytics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)


        # Player exposure (for multi-lineup)
        exposure_group = QGroupBox("Player Exposure")
        exposure_layout = QVBoxLayout(exposure_group)



        self.exposure_table = QTableWidget()
        self.exposure_table.setColumnCount(4)
        self.exposure_table.setHorizontalHeaderLabels([
            "Player", "Count", "Exposure %", "Avg Score"
        ])

        exposure_layout.addWidget(self.exposure_table)
        layout.addWidget(exposure_group)

        # Stack analysis
        stack_group = QGroupBox("Stack Analysis")
        stack_layout = QVBoxLayout(stack_group)

        self.stack_list = QListWidget()
        stack_layout.addWidget(self.stack_list)

        layout.addWidget(stack_group)

        return widget

    def create_stat_widget(self, label, value):
        """Create a stat display widget"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f1f5f9;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 12px; color: #64748b;")
        label_widget.setAlignment(Qt.AlignCenter)

        value_widget = QLabel(value)
        value_widget.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e293b;")
        value_widget.setAlignment(Qt.AlignCenter)
        value_widget.setObjectName(f"{label.lower()}_value")

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)

        return widget

    def apply_theme(self):
        """Apply modern theme to application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px;
            }

            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2563eb;
            }

            QPushButton:pressed {
                background-color: #1d4ed8;
            }

            QPushButton:disabled {
                background-color: #94a3b8;
            }

            QComboBox, QSpinBox {
                padding: 6px;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                background-color: white;
            }

            QComboBox:focus, QSpinBox:focus {
                border-color: #3b82f6;
            }

            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QTableWidget::item:selected {
                background-color: #dbeafe;
                color: #1e40af;
            }

            QTextEdit {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px;
            }

            QTabWidget::pane {
                border: 2px solid #e2e8f0;
                background-color: white;
                border-radius: 8px;
            }

            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
                background-color: #f1f5f9;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }

            QTabBar::tab:selected {
                background-color: white;
                color: #1e40af;
                font-weight: bold;
            }

            QTabBar::tab:hover {
                background-color: #e2e8f0;
            }

            QCheckBox, QRadioButton {
                spacing: 8px;
            }

            QCheckBox::indicator, QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }

            QSlider::groove:horizontal {
                height: 6px;
                background: #e2e8f0;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #3b82f6;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }

            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #e2e8f0;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 4px;
            }
        """)

        # Special styling for the optimize button
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }

            QPushButton:hover {
                background-color: #059669;
            }

            QPushButton:pressed {
                background-color: #047857;
            }

            QPushButton:disabled {
                background-color: #94a3b8;
            }
        """)

    def load_settings(self):
        """Load saved settings"""
        settings = QSettings("DFSOptimizer", "Settings")

        # Restore window geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Restore splitter state
        # Add more settings as needed

    def save_settings(self):
        """Save current settings"""
        settings = QSettings("DFSOptimizer", "Settings")
        settings.setValue("geometry", self.saveGeometry())

    def closeEvent(self, event):
        """Handle close event"""
        self.save_settings()
        event.accept()

    def auto_detect_files(self):
        """Auto-detect CSV files"""
        import glob

        # Look for DraftKings files
        for pattern in ["*DKSalaries*.csv", "*draftkings*.csv"]:
            files = glob.glob(pattern)
            if files:
                # Use most recent
                files.sort(key=os.path.getmtime, reverse=True)
                self.set_dk_file(files[0])
                break

    def select_dk_file(self):
        """Select DraftKings CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DraftKings CSV", "", "CSV Files (*.csv)"
        )
        if file_path:
            self.set_dk_file(file_path)

    def set_dk_file(self, path):
        """Set DraftKings file"""
        self.dk_file = path
        filename = os.path.basename(path)
        self.dk_label.setText(f"✅ {filename}")
        self.dk_label.setStyleSheet("""
            QLabel {
                padding: 20px;
                border: 2px solid #10b981;
                border-radius: 8px;
                background-color: #d1fae5;
                color: #065f46;
                font-weight: bold;
            }
        """)
        self.optimize_btn.setEnabled(True)
        self.status_bar.showMessage(f"Loaded: {filename}")

        # Initialize core
        if CORE_AVAILABLE:
            self.core = BulletproofDFSCore()
            self.core.load_draftkings_csv(path)

    def select_dff_file(self):
        """Select DFF file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DFF Rankings", "", "CSV Files (*.csv)"
        )
        if file_path:
            self.dff_file = file_path
            filename = os.path.basename(file_path)
            self.dff_label.setText(f"✅ {filename}")
            self.dff_label.setStyleSheet("""
                QLabel {
                    padding: 15px;
                    border: 2px solid #f59e0b;
                    border-radius: 8px;
                    background-color: #fef3c7;
                    color: #92400e;
                    font-weight: bold;
                }
            """)

    def download_dk_file(self):
        """Download latest DraftKings CSV"""
        # This would implement actual download logic
        QMessageBox.information(
            self, "Download",
            "This feature would download the latest DraftKings CSV.\n"
            "For now, please download manually from DraftKings."
        )

    def load_sample_players(self):
        """Load sample player names"""
        sample = "Shohei Ohtani, Mike Trout, Aaron Judge, Mookie Betts, Ronald Acuna Jr."
        self.manual_input.setPlainText(sample)

    def create_test_data(self):
        """Create test CSV data"""
        test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)

        # Write test data
        writer = csv.writer(test_file)
        writer.writerow(['Position', 'Name', 'Name', 'ID', 'Roster Position',
                         'Salary', 'Game Info', 'TeamAbbrev', 'AvgPointsPerGame'])

        test_players = [
            ['P', 'Gerrit Cole', 'Gerrit Cole', '1', 'P', '10000', 'NYY@BOS', 'NYY', '18.5'],
            ['P', 'Shane Bieber', 'Shane Bieber', '2', 'P', '9500', 'CLE@MIN', 'CLE', '17.2'],
            ['C', 'Will Smith', 'Will Smith', '3', 'C', '5000', 'LAD@SD', 'LAD', '10.2'],
            ['1B', 'Freddie Freeman', 'Freddie Freeman', '4', '1B', '5500', 'LAD@SD', 'LAD', '11.5'],
            ['2B', 'Jose Altuve', 'Jose Altuve', '5', '2B', '5200', 'HOU@TEX', 'HOU', '10.8'],
            ['3B', 'Manny Machado', 'Manny Machado', '6', '3B', '5300', 'SD@LAD', 'SD', '11.0'],
            ['SS', 'Trea Turner', 'Trea Turner', '7', 'SS', '5100', 'PHI@NYM', 'PHI', '10.5'],
            ['OF', 'Aaron Judge', 'Aaron Judge', '8', 'OF', '6500', 'NYY@BOS', 'NYY', '13.8'],
            ['OF', 'Mike Trout', 'Mike Trout', '9', 'OF', '6000', 'LAA@SEA', 'LAA', '12.5'],
            ['OF', 'Mookie Betts', 'Mookie Betts', '10', 'OF', '5800', 'LAD@SD', 'LAD', '12.0'],
        ]

        for player in test_players:
            writer.writerow(player)

        test_file.close()
        self.set_dk_file(test_file.name)

        QMessageBox.information(self, "Test Data", "Test data created and loaded!")

    def preset_cash(self):
        """Cash game preset"""
        self.single_radio.setChecked(True)
        self.opt_mode.setCurrentIndex(2)  # Confirmed only
        self.min_salary.setValue(49000)

    def preset_gpp(self):
        """GPP preset"""
        self.multi_radio.setChecked(True)
        self.lineup_count.setValue(20)
        self.diversity.setValue(80)
        self.opt_mode.setCurrentIndex(0)  # Bulletproof

    def preset_single(self):
        """Single entry preset"""
        self.single_radio.setChecked(True)
        self.opt_mode.setCurrentIndex(0)  # Bulletproof
        self.min_salary.setValue(48500)

    def preset_mass(self):
        """Mass multi-entry preset"""
        self.multi_radio.setChecked(True)
        self.lineup_count.setValue(150)
        self.diversity.setValue(90)
        self.allow_dupes.setChecked(False)

    def quick_generate(self, count, contest_type):
        """Quick lineup generation"""
        if not self.dk_file:
            QMessageBox.warning(self, "No Data", "Please load a DraftKings CSV first")
            return

        self.multi_radio.setChecked(True)
        self.lineup_count.setValue(count)

        # Set contest type
        if contest_type == "cash":
            self.contest_type.setCurrentIndex(0)
            self.opt_mode.setCurrentIndex(2)  # Confirmed only
        else:
            self.contest_type.setCurrentIndex(0)
            self.opt_mode.setCurrentIndex(0)  # Bulletproof

        self.run_optimization()

    def run_optimization(self):
        """Run the optimization process"""
        if not self.dk_file:
            QMessageBox.warning(self, "No Data", "Please load a DraftKings CSV first")
            return

        # Prepare settings
        settings = {
            'mode': ['bulletproof', 'manual_only', 'confirmed_only', 'all'][self.opt_mode.currentIndex()],
            'contest_type': self.contest_type.currentText().lower(),
            'manual_players': self.manual_input.toPlainText().strip(),
            'multi_lineup': self.multi_radio.isChecked(),
            'lineup_count': self.lineup_count.value() if self.multi_radio.isChecked() else 1,
            'min_salary': self.min_salary.value(),
            'max_exposure': self.max_exposure.value() / 100.0,
            'diversity': self.diversity.value() / 100.0
        }

        # Clear previous results
        self.console.clear()
        self.lineup_table.setRowCount(0)

        # Update UI
        self.optimize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        # Create worker thread
        self.thread = QThread()
        self.worker = OptimizationWorker(self.core, settings)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)

        # Start
        self.thread.start()

    def on_progress(self, message):
        """Handle progress updates"""
        self.console.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def on_finished(self, results):
        """Handle optimization completion"""
        self.last_results = results

        if not results:
            self.on_error("No valid lineups generated")
            return

        self.console.append(f"\n✅ Generated {len(results)} lineup(s) successfully!")

        # Update UI
        self.optimize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Generated {len(results)} lineup(s)")

        # Display results
        if len(results) == 1:
            self.display_single_result(results[0])
        else:
            self.display_multi_results(results)

        # Switch to results tab
        self.results_tabs.setCurrentIndex(1)

        # Show notification
        QMessageBox.information(
            self, "Success",
            f"Successfully generated {len(results)} lineup(s)!\n"
            f"Average score: {sum(r['total_score'] for r in results) / len(results):.1f}"
        )

    def on_error(self, error_message):
        """Handle optimization error"""
        self.console.append(f"\n❌ ERROR: {error_message}")

        # Reset UI
        self.optimize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Optimization failed")

        # Show error dialog
        QMessageBox.critical(self, "Optimization Failed", error_message)

    def display_single_result(self, result):
        """Display single lineup result"""
        lineup = result['lineup']

        # Update summary
        score = result['total_score']
        salary = result['total_salary']
        value = score / (salary / 1000) if salary > 0 else 0

        self.score_label.findChild(QLabel, "score_value").setText(f"{score:.1f}")
        self.salary_label.findChild(QLabel, "salary_value").setText(f"${salary:,}")
        self.value_label.findChild(QLabel, "value_value").setText(f"{value:.2f}")

        # Update table
        self.lineup_table.setRowCount(len(lineup))

        for i, player in enumerate(lineup):
            # Position
            pos_item = QTableWidgetItem(player.primary_position)
            pos_item.setTextAlignment(Qt.AlignCenter)
            self.lineup_table.setItem(i, 0, pos_item)

            # Name
            self.lineup_table.setItem(i, 1, QTableWidgetItem(player.name))

            # Team
            team_item = QTableWidgetItem(player.team)
            team_item.setTextAlignment(Qt.AlignCenter)
            self.lineup_table.setItem(i, 2, team_item)

            # Salary
            salary_item = QTableWidgetItem(f"${player.salary:,}")
            salary_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lineup_table.setItem(i, 3, salary_item)

            # Projected
            proj_item = QTableWidgetItem(f"{player.enhanced_score:.1f}")
            proj_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lineup_table.setItem(i, 4, proj_item)

            # Value
            player_value = player.enhanced_score / (player.salary / 1000) if player.salary > 0 else 0
            value_item = QTableWidgetItem(f"{player_value:.2f}")
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.lineup_table.setItem(i, 5, value_item)

            # Color code by position
            if player.primary_position == 'P':
                for j in range(6):
                    self.lineup_table.item(i, j).setBackground(QColor(219, 234, 254))
            elif player.primary_position in ['C', '1B', '2B', '3B', 'SS']:
                for j in range(6):
                    self.lineup_table.item(i, j).setBackground(QColor(254, 215, 215))
            else:  # OF
                for j in range(6):
                    self.lineup_table.item(i, j).setBackground(QColor(209, 250, 229))

    def display_multi_results(self, results):
        """Display multiple lineup results"""
        # Show summary dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{len(results)} Lineups Generated")
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout(dialog)

        # Summary stats
        scores = [r['total_score'] for r in results]
        salaries = [r['total_salary'] for r in results]

        summary = QLabel(f"""
            <h3>Lineup Generation Summary</h3>
            <p><b>Lineups:</b> {len(results)}</p>
            <p><b>Score Range:</b> {min(scores):.1f} - {max(scores):.1f}</p>
            <p><b>Average Score:</b> {sum(scores) / len(scores):.1f}</p>
            <p><b>Salary Range:</b> ${min(salaries):,} - ${max(salaries):,}</p>
        """)
        layout.addWidget(summary)

        # Lineup list
        lineup_list = QListWidget()
        for i, result in enumerate(results):
            item_text = f"Lineup {i + 1}: {result['total_score']:.1f} pts, ${result['total_salary']:,}"
            lineup_list.addItem(item_text)

        lineup_list.itemDoubleClicked.connect(
            lambda item: self.display_single_result(results[lineup_list.row(item)])
        )
        layout.addWidget(lineup_list)

        # Buttons
        button_layout = QHBoxLayout()

        export_btn = QPushButton("Export All")
        export_btn.clicked.connect(lambda: self.export_multi_lineups(results))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)

        button_layout.addWidget(export_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        dialog.exec_()

        # Update exposure analysis
        self.update_exposure_analysis(results)

    def update_exposure_analysis(self, results):
        """Update player exposure analysis"""
        player_usage = {}

        for result in results:
            for player in result['lineup']:
                key = player.name
                if key not in player_usage:
                    player_usage[key] = {
                        'count': 0,
                        'total_score': 0,
                        'salary': player.salary
                    }
                player_usage[key]['count'] += 1
                player_usage[key]['total_score'] += player.enhanced_score

        # Sort by usage
        sorted_players = sorted(
            player_usage.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )

        # Update table
        self.exposure_table.setRowCount(len(sorted_players))

        for i, (name, data) in enumerate(sorted_players):
            self.exposure_table.setItem(i, 0, QTableWidgetItem(name))
            self.exposure_table.setItem(i, 1, QTableWidgetItem(str(data['count'])))

            exposure = (data['count'] / len(results)) * 100
            exposure_item = QTableWidgetItem(f"{exposure:.1f}%")

            # Color code exposure
            if exposure > 60:
                exposure_item.setBackground(QColor(254, 202, 202))
            elif exposure > 40:
                exposure_item.setBackground(QColor(254, 240, 138))
            else:
                exposure_item.setBackground(QColor(187, 247, 208))

            self.exposure_table.setItem(i, 2, exposure_item)

            avg_score = data['total_score'] / data['count']
            self.exposure_table.setItem(i, 3, QTableWidgetItem(f"{avg_score:.1f}"))

    def copy_lineup(self):
        """Copy lineup to clipboard"""
        if not self.last_results:
            return

        lineup = self.last_results[0]['lineup']
        text = ", ".join([p.name for p in lineup])

        QApplication.clipboard().setText(text)
        self.status_bar.showMessage("Lineup copied to clipboard!", 3000)

    def export_csv(self):
        """Export lineup(s) to CSV"""
        if not self.last_results:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Lineups", "lineups.csv", "CSV Files (*.csv)"
        )

        if file_path:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Lineup', 'Position', 'Player', 'Team', 'Salary', 'Projection'])

                for i, result in enumerate(self.last_results):
                    for player in result['lineup']:
                        writer.writerow([
                            i + 1,
                            player.primary_position,
                            player.name,
                            player.team,
                            player.salary,
                            player.enhanced_score
                        ])

            QMessageBox.information(self, "Export Complete", f"Exported to {file_path}")

    def export_draftkings(self):
        """Export in DraftKings upload format"""
        if not self.last_results:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export for DraftKings", "dk_upload.csv", "CSV Files (*.csv)"
        )

        if file_path:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)

                # DraftKings format - just player names in position order
                for result in self.last_results:
                    row = []
                    positions = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']

                    lineup_by_pos = {}
                    for player in result['lineup']:
                        pos = player.primary_position
                        if pos not in lineup_by_pos:
                            lineup_by_pos[pos] = []
                        lineup_by_pos[pos].append(player.name)

                    for pos in positions:
                        if pos in lineup_by_pos and lineup_by_pos[pos]:
                            row.append(lineup_by_pos[pos].pop(0))
                        else:
                            row.append("")

                    writer.writerow(row)

            QMessageBox.information(self, "Export Complete",
                                    f"Exported {len(self.last_results)} lineup(s) for DraftKings upload")

    def export_multi_lineups(self, results):
        """Export multiple lineups"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export All Lineups", "all_lineups.csv", "CSV Files (*.csv)"
        )

        if file_path:
            self.last_results = results
            self.export_csv()

update_clean_gui_with_bankroll(DFSOptimizerGUI)
if BANKROLL_AVAILABLE:
    update_clean_gui_with_bankroll(DFSOptimizerGUI)

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("DFS Optimizer Pro")
    app.setOrganizationName("DFS Tools")

    # Set application icon if available
    if os.path.exists("icon.png"):
        app.setWindowIcon(QIcon("icon.png"))

    # Create and show main window
    window = DFSOptimizerGUI()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())