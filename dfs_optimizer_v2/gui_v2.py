#!/usr/bin/env python3
"""
DFS OPTIMIZER GUI V2 - FIXED VERSION
=====================================
Fixed tuple handling and improved data source status
"""

import sys
import os
from datetime import datetime
from typing import List, Set, Tuple
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
# gui_v2.py - TOP OF FILE
from typing import List, Set, Tuple, Dict  # Add Dict here

# Import our new clean components
from data_pipeline_v2 import DFSPipeline
from config_v2 import get_config
from bankroll_manager import BankrollManager, RiskLevel, ContestInfo
from daily_bankroll_advisor import DailyBankrollAdvisor, SAMPLE_DAILY_CONTESTS
from strategic_advisor import StrategicAdvisor
from scaling_tracker import ScalingTracker


class DFSOptimizerGUI(QMainWindow):
    """Clean, simple DFS optimizer interface"""

    def __init__(self):
        super().__init__()

        # ✅ Restore this line
        self.pipeline = DFSPipeline()

        self.config = get_config()

        # Initialize bankroll manager
        self.bankroll_manager = None
        self.daily_advisor = None
        self.strategic_advisor = None

        # State
        self.csv_loaded = False
        self.manual_selections = set()
        self.generated_lineups = []

        # Setup UI
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""

        self.setWindowTitle("DFS Optimizer V2 - Clean & Simple")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Create sections
        layout.addWidget(self.create_load_section())
        layout.addWidget(self.create_settings_section())
        layout.addWidget(self.create_bankroll_section())
        layout.addWidget(self.create_player_pool_section())
        layout.addWidget(self.create_optimize_section())
        layout.addWidget(self.create_results_section())

        # Status bar
        self.status_bar = self.statusBar()
        self.update_status("Ready - Load CSV to begin")

    def create_load_section(self) -> QGroupBox:
        """Section 1: Load CSV"""

        group = QGroupBox("1. Load CSV")
        layout = QHBoxLayout()

        # Load button
        self.load_btn = QPushButton("Load CSV")
        self.load_btn.clicked.connect(self.load_csv)
        layout.addWidget(self.load_btn)

        # CSV info
        self.csv_label = QLabel("No file loaded")
        layout.addWidget(self.csv_label)

        # Slate info
        self.slate_label = QLabel("")
        self.slate_label.setStyleSheet("color: green; margin-left: 20px;")
        layout.addWidget(self.slate_label)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def create_settings_section(self) -> QGroupBox:
        """Section 2: Contest Settings"""

        group = QGroupBox("2. Contest Settings")
        layout = QGridLayout()

        # Contest type
        layout.addWidget(QLabel("Contest:"), 0, 0)
        self.contest_combo = QComboBox()
        self.contest_combo.addItems(["GPP (Tournament)", "Cash (50/50)"])
        self.contest_combo.currentTextChanged.connect(self.on_contest_changed)
        layout.addWidget(self.contest_combo, 0, 1)

        # Number of lineups
        layout.addWidget(QLabel("Lineups:"), 0, 2)
        self.lineups_spin = QSpinBox()
        self.lineups_spin.setRange(1, 150)
        self.lineups_spin.setValue(20)
        layout.addWidget(self.lineups_spin, 0, 3)

        # Strategy info
        self.strategy_label = QLabel("Strategy will be auto-selected based on slate")
        self.strategy_label.setStyleSheet("color: green; margin-top: 5px;")
        layout.addWidget(self.strategy_label, 1, 0, 1, 4)

        layout.setColumnStretch(4, 1)
        group.setLayout(layout)
        return group

    def create_bankroll_section(self) -> QGroupBox:
        """Section 2.5: Bankroll Management"""

        group = QGroupBox("💰 Bankroll Management")
        layout = QVBoxLayout()

        # Bankroll input row
        bankroll_layout = QHBoxLayout()

        bankroll_layout.addWidget(QLabel("Current Bankroll ($):"))
        self.bankroll_input = QDoubleSpinBox()
        self.bankroll_input.setRange(10.0, 1000000.0)
        self.bankroll_input.setValue(1000.0)
        self.bankroll_input.setDecimals(2)
        bankroll_layout.addWidget(self.bankroll_input)

        bankroll_layout.addWidget(QLabel("Risk Level:"))
        self.risk_combo = QComboBox()
        self.risk_combo.addItems(["Conservative", "Moderate", "Aggressive"])
        self.risk_combo.setCurrentText("Moderate")
        bankroll_layout.addWidget(self.risk_combo)

        # Initialize bankroll button
        self.init_bankroll_btn = QPushButton("Initialize Bankroll Manager")
        self.init_bankroll_btn.clicked.connect(self.initialize_bankroll_manager)
        bankroll_layout.addWidget(self.init_bankroll_btn)

        # Stake calculator button
        self.stake_calc_btn = QPushButton("Calculate Optimal Stake")
        self.stake_calc_btn.setEnabled(False)
        self.stake_calc_btn.clicked.connect(self.calculate_optimal_stake)
        bankroll_layout.addWidget(self.stake_calc_btn)

        # Daily advisor button
        self.daily_advisor_btn = QPushButton("Get Daily Recommendations")
        self.daily_advisor_btn.setEnabled(False)
        self.daily_advisor_btn.clicked.connect(self.get_daily_recommendations)
        bankroll_layout.addWidget(self.daily_advisor_btn)

        # Strategic guidance button
        self.strategic_btn = QPushButton("Get Strategic Guidance")
        self.strategic_btn.setEnabled(False)
        self.strategic_btn.clicked.connect(self.get_strategic_guidance)
        bankroll_layout.addWidget(self.strategic_btn)

        # Scaling plan button
        self.scaling_btn = QPushButton("Show Scaling Plan to $400")
        self.scaling_btn.setEnabled(False)
        self.scaling_btn.clicked.connect(self.show_scaling_plan)
        bankroll_layout.addWidget(self.scaling_btn)

        bankroll_layout.addStretch()
        layout.addLayout(bankroll_layout)

        # Bankroll status display
        self.bankroll_status = QLabel("Enter bankroll and click Initialize to get stake recommendations")
        self.bankroll_status.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.bankroll_status)

        group.setLayout(layout)
        return group

    def create_player_pool_section(self) -> QGroupBox:
        """Section 3: Player Pool"""

        group = QGroupBox("3. Player Pool")
        layout = QVBoxLayout()

        # Pool controls
        controls = QHBoxLayout()

        # Fetch confirmations button
        self.fetch_btn = QPushButton("Fetch Confirmations")
        self.fetch_btn.clicked.connect(self.fetch_confirmations)
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:enabled {
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover:enabled {
                background-color: #1976D2;
            }
        """)
        controls.addWidget(self.fetch_btn)

        # Data source status (NEW!)
        self.data_status_label = QLabel("Data Sources: Not Connected")
        self.data_status_label.setStyleSheet("color: gray; margin-left: 10px;")
        controls.addWidget(self.data_status_label)

        # Separator
        separator = QLabel("|")
        separator.setStyleSheet("color: #ccc; margin: 0 10px;")
        controls.addWidget(separator)

        # Confirmed only checkbox
        self.confirmed_cb = QCheckBox("Confirmed Players Only")
        self.confirmed_cb.setChecked(False)
        self.confirmed_cb.stateChanged.connect(self.on_confirmed_changed)
        controls.addWidget(self.confirmed_cb)

        # Fast mode checkbox (skip Statcast)
        self.fast_mode_cb = QCheckBox("Fast Mode (Skip Statcast)")
        self.fast_mode_cb.setChecked(False)
        self.fast_mode_cb.setToolTip("Skip Statcast data fetching for faster optimization")
        controls.addWidget(self.fast_mode_cb)

        # Pool info
        self.pool_label = QLabel("Pool: 0 players")
        self.pool_label.setStyleSheet("font-weight: bold; margin-left: 20px;")
        controls.addWidget(self.pool_label)

        # Confirmed count
        self.confirmed_label = QLabel("")
        self.confirmed_label.setStyleSheet("color: green; margin-left: 5px;")
        controls.addWidget(self.confirmed_label)

        controls.addStretch()
        layout.addLayout(controls)

        # Manual selection
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Manual:"))

        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Enter player name")
        self.manual_input.returnPressed.connect(self.add_manual)
        manual_layout.addWidget(self.manual_input)

        self.add_manual_btn = QPushButton("Add")
        self.add_manual_btn.clicked.connect(self.add_manual)
        manual_layout.addWidget(self.add_manual_btn)

        self.manual_label = QLabel("0 selected")
        manual_layout.addWidget(self.manual_label)

        self.clear_manual_btn = QPushButton("Clear")
        self.clear_manual_btn.clicked.connect(self.clear_manual)
        manual_layout.addWidget(self.clear_manual_btn)

        manual_layout.addStretch()
        layout.addLayout(manual_layout)

        group.setLayout(layout)
        return group

    def create_optimize_section(self) -> QGroupBox:
        """Section 4: Optimize"""

        group = QGroupBox("4. Optimize")
        layout = QVBoxLayout()

        # Optimize button
        btn_layout = QHBoxLayout()

        self.optimize_btn = QPushButton("OPTIMIZE LINEUPS")
        self.optimize_btn.setEnabled(False)
        self.optimize_btn.clicked.connect(self.run_optimization)
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:enabled {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton:hover:enabled {
                background-color: #45a049;
            }
        """)
        btn_layout.addWidget(self.optimize_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Status log (enlarged for better visibility)
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(300)  # Increased from 100 to 300
        layout.addWidget(self.status_text)

        group.setLayout(layout)
        return group

    def create_results_section(self) -> QGroupBox:
        """Section 5: Results"""

        group = QGroupBox("5. Results")
        layout = QVBoxLayout()

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Lineup", "Score", "Salary", "Stack", "Strategy", "Action"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.results_table)

        # Export button
        export_layout = QHBoxLayout()

        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_lineups)
        export_layout.addWidget(self.export_btn)

        export_layout.addStretch()
        layout.addLayout(export_layout)

        group.setLayout(layout)
        return group

    # =========================================
    # EVENT HANDLERS - FIXED
    # =========================================

    def load_csv(self):
        """Load CSV file - FIXED to handle tuple return"""

        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load DraftKings CSV", "", "CSV Files (*.csv)"
        )

        if not filepath:
            return

        self.log("Loading CSV...")
        QApplication.processEvents()

        # Load CSV - FIX: Handle tuple return
        result = self.pipeline.load_csv(filepath)

        # Check if result is tuple or int
        if isinstance(result, tuple):
            player_count, game_count = result
        else:
            player_count = result
            game_count = self.pipeline.num_games

        if player_count > 0:
            self.csv_loaded = True
            filename = os.path.basename(filepath)
            self.csv_label.setText(f"{filename} ({player_count} players)")

            # Show slate info
            self.slate_label.setText(f"{game_count} games")

            # Detect slate size
            if game_count <= 4:
                slate_size = "small"
            elif game_count <= 9:
                slate_size = "medium"
            else:
                slate_size = "large"

            self.pipeline.num_games = game_count

            # Update strategy label
            self.update_strategy_label()

            # Update pool
            self.update_pool_label()

            # Enable buttons
            self.optimize_btn.setEnabled(True)
            self.fetch_btn.setEnabled(True)

            # Check data sources
            self.check_data_sources()

            self.log(f"✅ Loaded {player_count} players from {game_count} games")
        else:
            QMessageBox.warning(self, "Error", "Failed to load CSV")

    def check_data_sources(self):
        """Check which data sources are available"""
        available = []

        # Check each data source
        try:
            from vegas_lines import VegasLines
            available.append("Vegas")
        except ImportError:
            pass

        try:
            from smart_confirmation import UniversalSmartConfirmation
            available.append("MLB")
        except ImportError:
            pass

        try:
            from simple_statcast_fetcher import SimpleStatcastFetcher
            statcast = SimpleStatcastFetcher()
            if statcast.enabled:
                available.append("Statcast")
            else:
                available.append("Stats")
        except ImportError:
            pass

        try:
            from ownership_calculator import OwnershipCalculator
            available.append("Own%")
        except ImportError:
            pass

        try:
            from weather_integration import WeatherIntegration
            available.append("Weather")
        except ImportError:
            pass

        # Update status label
        if available:
            self.data_status_label.setText(f"Data: {', '.join(available)}")
            self.data_status_label.setStyleSheet("color: green; margin-left: 10px;")
        else:
            self.data_status_label.setText("Data: Using Defaults")
            self.data_status_label.setStyleSheet("color: orange; margin-left: 10px;")

    def fetch_confirmations(self):
        """Fetch MLB confirmations"""

        self.log("Fetching MLB confirmations...")
        QApplication.processEvents()

        result = self.pipeline.fetch_confirmations()

        # Handle both old (int) and new (tuple) return formats
        if isinstance(result, tuple):
            total_count, pitcher_count, position_count = result
        else:
            # Fallback for old format
            total_count = result
            pitcher_count = 0
            position_count = 0

        if total_count > 0:
            if position_count > 0:
                self.log(f"✅ Found {total_count} confirmed players ({pitcher_count} pitchers, {position_count} position players)")
                self.confirmed_label.setText(f"({total_count} confirmed)")
            else:
                self.log(f"⚠️ Found {pitcher_count} confirmed pitchers, but no position player lineups yet")
                self.confirmed_label.setText(f"({pitcher_count} pitchers only)")

                # Warn about confirmed-only mode and timing
                if self.confirmed_cb.isChecked():
                    self.log("💡 Tip: Uncheck 'Confirmed Only' to include all players until lineups are posted")
                self.log("📅 Note: Position player lineups are typically posted 2-4 hours before first pitch")

            # Update pool if showing confirmed only
            if self.confirmed_cb.isChecked():
                self.update_pool_label()
        else:
            self.log("No confirmations found (may be too early)")
            self.confirmed_label.setText("(none yet)")

    def on_contest_changed(self):
        """Handle contest type change"""

        if self.csv_loaded:
            self.update_strategy_label()

            # Update default lineups
            if "Cash" in self.contest_combo.currentText():
                self.lineups_spin.setValue(3)
            else:
                self.lineups_spin.setValue(20)

    def on_confirmed_changed(self):
        """Handle confirmed checkbox change"""
        self.update_pool_label()

    def update_strategy_label(self):
        """Update strategy label based on slate"""

        if not self.csv_loaded:
            return

        contest = "cash" if "Cash" in self.contest_combo.currentText() else "gpp"
        strategy, reason = self.pipeline.strategy_manager.auto_select_strategy(
            contest, self.pipeline.num_games
        )

        self.strategy_label.setText(f"Strategy: {reason}")

    def add_manual(self):
        """Add manual player selection"""

        name = self.manual_input.text().strip()
        if name:
            self.manual_selections.add(name)
            self.manual_input.clear()
            self.manual_label.setText(f"{len(self.manual_selections)} selected")
            self.update_pool_label()
            self.log(f"Added manual: {name}")

    def clear_manual(self):
        """Clear manual selections"""

        self.manual_selections.clear()
        self.manual_label.setText("0 selected")
        self.update_pool_label()
        self.log("Cleared manual selections")

    def update_pool_label(self):
        """Update player pool label"""

        if not self.csv_loaded:
            return

        # Build pool
        confirmed = self.confirmed_cb.isChecked()
        manual = list(self.manual_selections)

        count = self.pipeline.build_player_pool(confirmed, manual)

        # Update main pool label
        if confirmed:
            self.pool_label.setText(f"Pool: {count} confirmed players")
        else:
            self.pool_label.setText(f"Pool: {count} players")

        # Count how many in pool are confirmed
        confirmed_in_pool = 0
        for player in self.pipeline.player_pool:
            if getattr(player, 'confirmed', False):
                confirmed_in_pool += 1

        # Update confirmed count if not showing confirmed-only
        if not confirmed:
            self.confirmed_label.setText(f"({confirmed_in_pool} confirmed)")

    def run_optimization(self):
        """Run the optimization"""

        if not self.csv_loaded:
            return

        # Get settings
        contest = "cash" if "Cash" in self.contest_combo.currentText() else "gpp"
        num_lineups = self.lineups_spin.value()
        confirmed = self.confirmed_cb.isChecked()
        manual = list(self.manual_selections)

        # Show progress
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)

        self.log("=" * 50)
        self.log(f"Starting {contest.upper()} optimization for {num_lineups} lineups")

        try:
            # Progress: Load
            self.progress.setValue(20)
            QApplication.processEvents()

            # Build pool
            self.pipeline.build_player_pool(confirmed, manual)
            self.log(f"Player pool: {len(self.pipeline.player_pool)} players")

            # Progress: Strategy
            self.progress.setValue(40)
            QApplication.processEvents()

            # Apply strategy
            strategy = self.pipeline.apply_strategy(contest_type=contest)
            self.log(f"Applied strategy: {strategy}")

            # Progress: Enrich
            self.progress.setValue(60)
            QApplication.processEvents()

            # Enrich players with real data
            fast_mode = self.fast_mode_cb.isChecked()
            if fast_mode:
                self.log("Fast mode: Using default stats (skipping Statcast)")
            else:
                self.log("Enriching players with real data...")
                self.log("💡 This may take 10-30 seconds for Statcast data...")
            QApplication.processEvents()  # Keep GUI responsive

            stats = self.pipeline.enrich_players(strategy, contest, skip_statcast=fast_mode)

            # Log enrichment stats
            if stats:
                active_stats = [k for k, v in stats.items() if v > 0]
                if active_stats:
                    self.log(f"Enriched with: {', '.join(active_stats)}")
                else:
                    self.log("Using default values (no external data)")

            # Apply unified scoring engine
            self.log("Applying unified scoring engine...")
            QApplication.processEvents()

            scoring_stats = self.pipeline.score_players(contest)
            if scoring_stats:
                avg_score = scoring_stats.get('avg_score', 0)
                self.log(f"Scored {scoring_stats.get('players_scored', 0)} players (avg: {avg_score:.1f})")
            else:
                self.log("Using basic projection scoring")

            # Progress: Optimize
            self.progress.setValue(80)
            QApplication.processEvents()

            # Generate lineups
            self.log(f"Generating {num_lineups} {contest} lineups...")
            QApplication.processEvents()

            lineups = self.pipeline.optimize_lineups(contest, num_lineups)

            # Progress: Complete
            self.progress.setValue(100)

            if lineups:
                self.generated_lineups = lineups

                # Print lineups to console as well
                self.print_lineups_to_console(lineups)

                self.display_results(lineups)
                self.log(f"✅ Generated {len(lineups)} lineups!")
            else:
                self.log("❌ No lineups generated (may need more players)")

        except Exception as e:
            self.log(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.progress.setVisible(False)

    def print_lineups_to_console(self, lineups: List[Dict]):
        """Print generated lineups to console for easy copying"""
        print("\n" + "=" * 60)
        print("🏆 GENERATED LINEUPS")
        print("=" * 60)

        position_order = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']

        for i, lineup in enumerate(lineups):
            print(f"\n📋 LINEUP {i + 1}")
            print("-" * 40)

            # Group players by position
            players_by_pos = {}
            for player in lineup['players']:
                pos = player.position
                if pos in ['SP', 'RP']:
                    pos = 'P'  # Normalize pitcher positions
                if pos not in players_by_pos:
                    players_by_pos[pos] = []
                players_by_pos[pos].append(player)

            # Display in DraftKings order with enhanced stats
            total_ownership = 0
            for pos in position_order:
                if pos in players_by_pos:
                    for player in players_by_pos[pos]:
                        status = "✅" if getattr(player, 'confirmed', False) else "⚠️"

                        # Basic info line
                        print(f"{player.position:3} {player.name:20} ${player.salary:,} ({player.team}) {status}")

                        # Stats line
                        ownership = getattr(player, 'ownership', 15.0)
                        projection = getattr(player, 'projection', 0.0)
                        opt_score = getattr(player, 'optimization_score', 0.0)
                        total_ownership += ownership

                        # Position-specific stats
                        if player.position not in ['P', 'SP', 'RP']:
                            # Batter stats
                            barrel_rate = getattr(player, 'barrel_rate', 0.0)
                            xwoba = getattr(player, 'xwoba', 0.0)
                            batting_order = getattr(player, 'batting_order', 0)
                            order_str = f"#{batting_order}" if batting_order > 0 else "TBD"

                            print(f"    📊 Proj: {projection:.1f} | Own: {ownership:.1f}% | Opt: {opt_score:.1f} | Barrel: {barrel_rate:.1f}% | xwOBA: {xwoba:.3f} | Order: {order_str}")
                        else:
                            # Pitcher stats
                            k_rate = getattr(player, 'k_rate', 0.0)
                            era = getattr(player, 'era', 0.0)

                            print(f"    📊 Proj: {projection:.1f} | Own: {ownership:.1f}% | Opt: {opt_score:.1f} | K/9: {k_rate:.1f} | ERA: {era:.2f}")

                        print()  # Empty line for readability

            # Summary stats
            avg_ownership = total_ownership / len(lineup['players']) if lineup['players'] else 0
            print(f"💰 Salary: ${lineup['salary']:,} / $50,000 ({(lineup['salary']/50000)*100:.1f}%)")
            print(f"📈 Total Projection: {lineup['projection']:.1f}")
            print(f"👥 Average Ownership: {avg_ownership:.1f}%")
            print(f"🎯 Confirmed Players: {sum(1 for p in lineup['players'] if getattr(p, 'confirmed', False))}/{len(lineup['players'])}")

            if i < len(lineups) - 1:  # Don't print separator after last lineup
                print()

        print("\n" + "=" * 60)

    def display_results(self, lineups: List[Dict]):
        """Display optimization results"""

        self.results_table.setRowCount(len(lineups))

        for i, lineup in enumerate(lineups):
            # Lineup number
            self.results_table.setItem(i, 0, QTableWidgetItem(f"Lineup {i + 1}"))

            # Score
            score = lineup.get('projection', 0)
            self.results_table.setItem(i, 1, QTableWidgetItem(f"{score:.1f}"))

            # Salary
            salary = lineup.get('salary', 0)
            self.results_table.setItem(i, 2, QTableWidgetItem(f"${salary:,}"))

            # Stack info
            max_stack = lineup.get('max_stack', 0)
            self.results_table.setItem(i, 3, QTableWidgetItem(f"{max_stack} players"))

            # Strategy (simplified)
            strategy = lineup.get('strategy', 'optimized')
            self.results_table.setItem(i, 4, QTableWidgetItem(strategy))

            # View button
            view_btn = QPushButton("View")
            view_btn.clicked.connect(lambda checked, idx=i: self.view_lineup(idx))
            self.results_table.setCellWidget(i, 5, view_btn)

        self.export_btn.setEnabled(True)

    def view_lineup(self, index: int):
        """View detailed lineup"""

        if index >= len(self.generated_lineups):
            return

        lineup = self.generated_lineups[index]

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Lineup {index + 1}")
        dialog.setMinimumWidth(600)

        layout = QVBoxLayout()

        # Player list
        text = QTextEdit()
        text.setReadOnly(True)

        content = f"Lineup {index + 1}\n"
        content += "=" * 40 + "\n\n"

        # Show players by position with enhanced metrics (in DraftKings order)
        position_order = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']

        # Group players by position
        players_by_pos = {}
        for player in lineup['players']:
            pos = player.position
            if pos in ['SP', 'RP']:
                pos = 'P'  # Normalize pitcher positions
            if pos not in players_by_pos:
                players_by_pos[pos] = []
            players_by_pos[pos].append(player)

        # Display in DraftKings order with enhanced stats
        total_ownership = 0
        for pos in position_order:
            if pos in players_by_pos:
                for player in players_by_pos[pos]:
                    # Basic info
                    content += f"{player.position:3} {player.name:20} ${player.salary:,} ({player.team})\n"

                    # Enhanced metrics
                    ownership = getattr(player, 'ownership', 15.0)
                    projection = getattr(player, 'projection', 0.0)
                    opt_score = getattr(player, 'optimization_score', 0.0)
                    total_ownership += ownership

                    # Position-specific stats
                    if player.position not in ['P', 'SP', 'RP']:
                        # Batter metrics
                        barrel_rate = getattr(player, 'barrel_rate', 0.0)
                        xwoba = getattr(player, 'xwoba', 0.0)
                        batting_order = getattr(player, 'batting_order', 0)
                        order_str = f"#{batting_order}" if batting_order > 0 else "TBD"

                        content += f"     📊 Proj: {projection:.1f} | Own: {ownership:.1f}% | Opt: {opt_score:.1f}\n"
                        content += f"     ⚾ Barrel: {barrel_rate:.1f}% | xwOBA: {xwoba:.3f} | Order: {order_str}\n"
                    else:
                        # Pitcher metrics
                        k_rate = getattr(player, 'k_rate', 0.0)
                        era = getattr(player, 'era', 0.0)

                        content += f"     📊 Proj: {projection:.1f} | Own: {ownership:.1f}% | Opt: {opt_score:.1f}\n"
                        content += f"     ⚾ K/9: {k_rate:.1f} | ERA: {era:.2f}\n"

                    # Confirmation status
                    status = "✅ Confirmed" if getattr(player, 'confirmed', False) else "⚠️ Unconfirmed"
                    content += f"     {status}\n\n"

        # Summary stats
        avg_ownership = total_ownership / len(lineup['players']) if lineup['players'] else 0
        confirmed_count = sum(1 for p in lineup['players'] if getattr(p, 'confirmed', False))

        content += "=" * 50 + "\n"
        content += "📊 LINEUP SUMMARY\n"
        content += "=" * 50 + "\n"
        content += f"💰 Salary: ${lineup['salary']:,} / $50,000 ({(lineup['salary']/50000)*100:.1f}%)\n"
        content += f"📈 Total Projection: {lineup['projection']:.1f} points\n"
        content += f"👥 Average Ownership: {avg_ownership:.1f}%\n"
        content += f"🎯 Confirmed Players: {confirmed_count}/{len(lineup['players'])}\n"
        if lineup.get('max_stack', 0) > 0:
            content += f"🔗 Max Stack: {lineup['max_stack']} players\n"

        # Show stacks
        if lineup.get('stack_info'):
            content += "\nStacks:\n"
            for team, count in lineup['stack_info'].items():
                if count > 1:
                    content += f"  {team}: {count} players\n"

        text.setText(content)
        layout.addWidget(text)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def export_lineups(self):
        """Export lineups to CSV"""

        if not self.generated_lineups:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Lineups", "lineups.csv", "CSV Files (*.csv)"
        )

        if filepath:
            if self.pipeline.export_lineups(self.generated_lineups, filepath):
                self.log(f"✅ Exported to {filepath}")
                QMessageBox.information(self, "Success", "Lineups exported!")
            else:
                QMessageBox.warning(self, "Error", "Export failed")

    def log(self, message: str):
        """Add message to log"""

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")

        # Limit log size
        doc = self.status_text.document()
        if doc.blockCount() > 100:
            cursor = self.status_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()

    def update_status(self, message: str):
        """Update status bar"""

        self.status_bar.showMessage(message, 3000)

    def initialize_bankroll_manager(self):
        """Initialize the bankroll manager"""

        bankroll = self.bankroll_input.value()
        risk_text = self.risk_combo.currentText().lower()
        risk_level = RiskLevel(risk_text)

        self.bankroll_manager = BankrollManager(bankroll, risk_level)

        # Update status
        summary = self.bankroll_manager.get_bankroll_summary()

        status_text = (f"✅ Bankroll Manager Initialized | "
                      f"${summary['current_bankroll']:,.0f} | "
                      f"{summary['risk_level'].title()} Risk | "
                      f"Max Stake: ${summary['max_single_stake']:.0f}")

        self.bankroll_status.setText(status_text)
        self.bankroll_status.setStyleSheet("color: #4CAF50; font-weight: bold;")

        # Enable all bankroll management features
        self.stake_calc_btn.setEnabled(True)
        self.daily_advisor_btn.setEnabled(True)
        self.strategic_btn.setEnabled(True)
        self.scaling_btn.setEnabled(True)

        # Initialize advisors
        self.daily_advisor = DailyBankrollAdvisor(self.bankroll_manager)
        self.strategic_advisor = StrategicAdvisor(self.daily_advisor)

        self.status_text.append("💰 Bankroll manager initialized successfully")

    def calculate_optimal_stake(self):
        """Calculate optimal stake for current settings"""

        if not self.bankroll_manager:
            self.status_text.append("❌ Please initialize bankroll manager first")
            return

        # Get current settings
        contest_type_display = self.contest_combo.currentText()
        num_lineups = self.lineups_spin.value()

        # Convert display text to internal format
        if "Cash" in contest_type_display:
            contest_type = 'cash'
            entry_fee = 5.0  # Default cash entry fee
        else:  # GPP
            contest_type = 'gpp'
            entry_fee = 3.0  # Default GPP entry fee

        # Create contest info
        contest = ContestInfo(
            name=f"{contest_type_display}",
            entry_fee=entry_fee,
            max_entries=num_lineups,
            total_entries=1000,
            prize_pool=1000 * entry_fee * 0.9,
            contest_type=contest_type,
            slate_size='medium'  # Default
        )

        # Get strategy name
        strategy, _ = self.pipeline.strategy_manager.auto_select_strategy(
            contest_type, self.pipeline.num_games
        )

        # Calculate optimal stake
        stake_info = self.bankroll_manager.get_optimal_stake(contest, strategy)

        # Update status
        status_text = (f"🎯 Optimal Stake: {stake_info['recommended_entries']} entries "
                      f"(${stake_info['actual_stake']:.0f}) | "
                      f"Expected Profit: ${stake_info['expected_profit']:.0f} | "
                      f"Bankroll: {stake_info['bankroll_percentage']:.1f}%")

        self.bankroll_status.setText(status_text)

        # Log detailed info
        self.status_text.append(f"💰 Stake Recommendation:")
        self.status_text.append(f"   Strategy: {strategy}")
        self.status_text.append(f"   Recommended Entries: {stake_info['recommended_entries']}")
        self.status_text.append(f"   Total Stake: ${stake_info['actual_stake']:.2f}")
        self.status_text.append(f"   Expected Profit: ${stake_info['expected_profit']:.2f}")
        self.status_text.append(f"   Win Rate: {stake_info['win_rate']:.1f}%")

    def get_daily_recommendations(self):
        """Get comprehensive daily bankroll recommendations"""

        if not self.daily_advisor:
            self.status_text.append("❌ Please initialize bankroll manager first")
            return

        # Clear previous recommendations to avoid repetition
        self.status_text.clear()

        # Use sample contests (in real use, you'd load actual available contests)
        slate_size = 'medium'  # Could be determined from loaded data

        # Get daily recommendation
        recommendation = self.daily_advisor.get_daily_recommendation(
            SAMPLE_DAILY_CONTESTS, slate_size
        )

        # Update status with summary
        summary_text = (f"📊 Daily Plan: ${recommendation.total_daily_stake:.0f} total "
                       f"(${recommendation.cash_allocation:.0f} cash, "
                       f"${recommendation.gpp_allocation:.0f} GPP) | "
                       f"Expected: +${recommendation.expected_daily_profit:.0f}")

        self.bankroll_status.setText(summary_text)

        # Log detailed recommendations
        self.status_text.append("🏦 DAILY BANKROLL RECOMMENDATIONS:")
        self.status_text.append("=" * 50)

        self.status_text.append(f"💰 DAILY ALLOCATION:")
        self.status_text.append(f"   Total Daily Stake: ${recommendation.total_daily_stake:.2f}")
        self.status_text.append(f"   Cash Allocation: ${recommendation.cash_allocation:.2f}")
        self.status_text.append(f"   GPP Allocation: ${recommendation.gpp_allocation:.2f}")
        self.status_text.append(f"   Bankroll Usage: {recommendation.bankroll_percentage:.1f}%")

        self.status_text.append(f"📈 EXPECTED PERFORMANCE:")
        self.status_text.append(f"   Expected Daily Profit: ${recommendation.expected_daily_profit:.2f}")
        self.status_text.append(f"   Risk Assessment: {recommendation.risk_assessment}")

        self.status_text.append(f"🎯 ALL RECOMMENDED CONTESTS:")

        # Show ALL contests, not just top 5
        for i, contest in enumerate(recommendation.recommended_contests, 1):
            self.status_text.append(f"   {i}. {contest['contest_name']} ({contest['contest_type'].upper()})")
            self.status_text.append(f"      Entries: {contest['recommended_entries']} x ${contest['entry_fee']:.2f}")
            self.status_text.append(f"      Stake: ${contest['recommended_stake']:.2f}")
            self.status_text.append(f"      Expected Profit: ${contest['expected_profit']:.2f}")
            self.status_text.append(f"      Win Rate: {contest['win_rate']:.1f}%")

        self.status_text.append("")
        self.status_text.append("💡 TIP: These recommendations are based on your proven strategy performance!")
        self.status_text.append("💡 Adjust your actual contest entries based on what's available on DraftKings.")

    def get_strategic_guidance(self):
        """Get comprehensive strategic guidance including slate size recommendations"""

        if not self.strategic_advisor:
            self.status_text.append("❌ Please initialize bankroll manager first")
            return

        # Clear previous output to avoid repetition
        self.status_text.clear()

        # Get current bankroll and risk level
        bankroll = self.bankroll_input.value()
        risk_level = self.risk_combo.currentText().lower()

        # Available slate sizes (you could make this dynamic based on actual slates)
        available_slates = ['small', 'medium', 'large']

        # Get strategic guidance
        guidance = self.strategic_advisor.get_strategic_guidance(
            available_slates, bankroll, risk_level
        )

        # Get daily recommendation for context
        recommendation = self.daily_advisor.get_daily_recommendation(
            SAMPLE_DAILY_CONTESTS, guidance.slate_size_recommendation
        )

        # Update status with key recommendation
        key_info = (f"🧠 Strategy: {guidance.slate_size_recommendation.upper()} slates | "
                   f"Win Rate: {guidance.performance_expectations['daily_win_rate']:.1f}% | "
                   f"Monthly Target: +{guidance.performance_expectations['monthly_growth_target']:.0f}%")

        self.bankroll_status.setText(key_info)

        # Create enhanced, specific strategic guidance
        self.status_text.append("🧠 PERSONALIZED STRATEGIC GUIDANCE")
        self.status_text.append("=" * 60)

        # Specific slate recommendation
        slate_rec = guidance.slate_size_recommendation.upper()
        win_rate = guidance.performance_expectations['daily_win_rate']
        self.status_text.append(f"🎯 OPTIMAL SLATE SIZE FOR YOU: {slate_rec}")
        self.status_text.append(f"   Expected Win Rate: {win_rate:.1f}%")
        self.status_text.append(f"   Strategy: {self._get_strategy_for_slate(slate_rec.lower())}")
        self.status_text.append(f"   Why {slate_rec}: {self._get_slate_reasoning(slate_rec.lower(), bankroll, risk_level)}")

        # Specific contest recommendations
        self.status_text.append(f"")
        self.status_text.append(f"🏟️ SPECIFIC CONTEST STRATEGY:")
        cash_strategy = guidance.optimal_contest_sizes['cash']
        gpp_strategy = guidance.optimal_contest_sizes['gpp']
        self.status_text.append(f"   Cash Games: {cash_strategy}")
        self.status_text.append(f"   GPP Tournaments: {gpp_strategy}")

        # Today's specific plan
        self.status_text.append(f"")
        self.status_text.append(f"📊 TODAY'S SPECIFIC PLAN:")
        self.status_text.append(f"   Total Stake: ${recommendation.total_daily_stake:.2f} ({recommendation.bankroll_percentage:.1f}% of bankroll)")
        self.status_text.append(f"   Cash Focus: ${recommendation.cash_allocation:.2f} (65% allocation)")
        self.status_text.append(f"   GPP Focus: ${recommendation.gpp_allocation:.2f} (35% allocation)")
        self.status_text.append(f"   Expected Profit: ${recommendation.expected_daily_profit:.2f}")

        # Top 3 specific recommendations
        self.status_text.append(f"")
        self.status_text.append(f"🎯 TOP 3 SPECIFIC PLAYS FOR YOU:")
        for i, contest in enumerate(recommendation.recommended_contests[:3], 1):
            contest_type = contest['contest_type'].upper()
            self.status_text.append(f"   {i}. {contest['contest_name']} ({contest_type})")
            self.status_text.append(f"      Why: {self._get_contest_reasoning(contest, slate_rec.lower())}")
            self.status_text.append(f"      Stake: ${contest['recommended_stake']:.2f} → Expected: +${contest['expected_profit']:.2f}")

        # Execution plan
        self.status_text.append(f"")
        self.status_text.append(f"💡 YOUR EXECUTION PLAN:")
        self.status_text.append(f"   1. Focus on {slate_rec} slates today")
        self.status_text.append(f"   2. Use {self._get_strategy_for_slate(slate_rec.lower())} strategy")
        self.status_text.append(f"   3. Target {cash_strategy.lower()} for cash games")
        self.status_text.append(f"   4. Target {gpp_strategy.lower()} for tournaments")
        self.status_text.append(f"   5. Stay within ${recommendation.total_daily_stake:.0f} total daily limit")

        self.status_text.append("")
        self.status_text.append("🎯 READY TO DOMINATE! This plan is optimized for your bankroll and risk level.")

    def _get_strategy_for_slate(self, slate_size: str) -> str:
        """Get strategy name for slate size"""
        strategy_map = {
            'small': 'Optimized Correlation Value',
            'medium': 'Optimized Pitcher Dominance',
            'large': 'Optimized Tournament Winner'
        }
        return strategy_map.get(slate_size, 'Optimized Pitcher Dominance')

    def _get_slate_reasoning(self, slate_size: str, bankroll: float, risk_level: str) -> str:
        """Get reasoning for slate size recommendation"""
        if slate_size == 'small':
            return "Highest consistency with 66.1% win rate, good for building bankroll"
        elif slate_size == 'medium':
            return "Best balance: 71.6% win rate with good ROI, optimal for your bankroll"
        else:  # large
            return "Maximum ROI potential (18.52%) with 72.6% win rate, best for growth"

    def _get_contest_reasoning(self, contest: dict, slate_size: str) -> str:
        """Get reasoning for specific contest recommendation"""
        contest_type = contest['contest_type']
        if contest_type == 'cash':
            return f"High win rate ({contest['win_rate']:.1f}%) for consistent profits"
        else:  # gpp
            return f"High ROI potential ({contest['avg_roi']:.0f}%) for bankroll growth"

    def show_scaling_plan(self):
        """Show scaling plan to reach $400 bankroll and $50 daily stakes"""

        if not self.bankroll_manager:
            self.status_text.append("❌ Please initialize bankroll manager first")
            return

        # Clear previous output
        self.status_text.clear()

        # Get current bankroll
        current_bankroll = self.bankroll_input.value()

        # Create scaling tracker
        tracker = ScalingTracker(current_bankroll, 400.0, 50.0)

        # Get scaling plan
        scaling_plan = tracker.format_scaling_plan()

        # Update status with key info
        summary = tracker.get_scaling_summary()
        key_info = (f"🚀 Scaling Plan: {summary['days_to_50_stakes']}d to $50 stakes | "
                   f"{summary['days_to_400_bankroll']}d to $400 | "
                   f"25% daily risk")

        self.bankroll_status.setText(key_info)

        # Display complete scaling plan
        self.status_text.append("🚀 YOUR PERSONALIZED SCALING PLAN")
        self.status_text.append("=" * 60)

        # Split the plan into lines and add to status
        for line in scaling_plan.split('\n'):
            if line.strip():  # Skip empty lines
                self.status_text.append(line)

        self.status_text.append("")
        self.status_text.append("🎯 READY TO START SCALING! Set risk level to 'Aggressive' and follow this plan.")
        self.status_text.append("💡 This approach gets you to $50 daily stakes safely as your bankroll grows!")


def main():
    """Main entry point"""

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Create and show GUI
    window = DFSOptimizerGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()