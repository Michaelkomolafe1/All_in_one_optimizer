#!/usr/bin/env python3
"""
COMPLETE DFS OPTIMIZER SYSTEM
=============================
Integrates:
- Smart Confirmation System (your existing)
- Manual Player Selection
- Contest-specific data enhancement
- Auto slate detection (Classic/Showdown)
- Full GUI with all features
"""

import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
import json
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================
# PLAYER MODEL WITH ALL ATTRIBUTES
# ============================================

class EnhancedPlayer:
    """Complete player model with all attributes"""

    def __init__(self, name: str, position: str, team: str, salary: int, projection: float):
        # Core attributes
        self.name = name
        self.position = position
        self.positions = position.split('/')
        self.primary_position = self.positions[0]
        self.team = team
        self.salary = salary
        self.base_projection = projection

        # Handle pitcher positions
        if self.primary_position in ['SP', 'RP']:
            self.primary_position = 'P'
            self.positions = ['P']

        # Game info
        self.opponent = ""
        self.game_info = ""
        self.game_time = ""

        # Status
        self.is_confirmed = False
        self.is_manual = False
        self.batting_order = 0

        # Cash-specific attributes
        self.recent_form_score = 0.0
        self.consistency_score = 0.0
        self.floor_projection = 0.0
        self.platoon_advantage = False
        self.vs_pitcher_era = 4.50
        self.last_5_avg = 0.0

        # GPP-specific attributes
        self.projected_ownership = 15.0
        self.ceiling_projection = 0.0
        self.team_total = 4.5
        self.game_total = 9.0
        self.barrel_rate = 8.0
        self.xwoba_diff = 0.0
        self.k_rate = 0.20

        # Weather/Park factors
        self.wind_speed = 5.0
        self.park_factor = 1.0
        self.weather_score = 0.0

        # Scoring
        self.enhanced_score = projection
        self.gpp_score = projection
        self.cash_score = projection
        self.value_score = projection / (salary / 1000) if salary > 0 else 0


# ============================================
# SMART CONFIRMATION SYSTEM (Simplified)
# ============================================

class SmartConfirmationSystem:
    """Simplified version of your confirmation system"""

    def __init__(self):
        self.confirmed_pitchers = {}
        self.confirmed_lineups = {}
        self.csv_teams = set()

    def get_all_confirmations(self):
        """Fetch confirmations from MLB API"""
        logger.info("Fetching confirmed lineups...")

        # Simulated for now - you'd use your real implementation
        # This would call MLB API and parse actual lineups

        # Example data structure
        self.confirmed_pitchers = {
            'HOU': {'name': 'Hunter Brown'},
            'SEA': {'name': 'Logan Gilbert'},
            'MIL': {'name': 'Freddy Peralta'}
        }

        self.confirmed_lineups = {
            'HOU': [
                {'name': 'Jose Altuve', 'order': 1},
                {'name': 'Alex Bregman', 'order': 2},
                {'name': 'Kyle Tucker', 'order': 3}
            ]
        }

        return True

    def is_player_confirmed(self, player_name: str, team: str) -> Tuple[bool, Optional[int]]:
        """Check if player is confirmed"""
        if team in self.confirmed_lineups:
            for player in self.confirmed_lineups[team]:
                if player['name'].lower() == player_name.lower():
                    return True, player.get('order', 0)
        return False, None

    def is_pitcher_confirmed(self, pitcher_name: str, team: str) -> bool:
        """Check if pitcher is confirmed"""
        if team in self.confirmed_pitchers:
            return self.confirmed_pitchers[team]['name'].lower() == pitcher_name.lower()
        return False


# ============================================
# ENHANCED SCORING ENGINE WITH ALL PARAMETERS
# ============================================

class EnhancedScoringEngine:
    """Complete scoring engine with all your optimized parameters"""

    def __init__(self):
        # GPP Parameters (from your -67.7 optimization)
        self.gpp_params = {
            'threshold_high': 5.731,
            'threshold_med': 5.879,
            'threshold_low': 4.865,
            'mult_high': 1.336,
            'mult_med': 1.216,
            'mult_low': 1.139,
            'mult_none': 0.761,
            'stack_min': 4,
            'stack_preferred': 4,
            'batting_boost': 1.115,
            'batting_positions': 5,
            'ownership_low_boost': 1.106,
            'ownership_high_penalty': 0.9,
            'ownership_threshold': 15,
            'pitcher_bad_boost': 1.135,
            'pitcher_ace_penalty': 0.92,
            'era_threshold': 4.232,
            'barrel_rate_threshold': 11.665,
            'barrel_rate_boost': 1.194,
            'exit_velo_threshold': 90.781,
            'exit_velo_boost': 1.078,
            'xwoba_diff_threshold': 0.015,
            'undervalued_boost': 1.25,
            'min_k9_threshold': 9.898,
            'high_k9_boost': 1.198,
            'opp_k_rate_threshold': 0.211,
            'high_opp_k_boost': 1.196
        }

        # Cash Parameters (from your 86.2 optimization)
        self.cash_params = {
            'weight_projection': 0.377,
            'weight_recent': 0.369,
            'weight_season': 0.189,
            'consistency_weight': 0.250,
            'recent_games_window': 4,
            'platoon_advantage_boost': 1.084,
            'streak_hot_boost': 1.085,
            'streak_cold_penalty': 0.935,
            'streak_window': 3,
            'floor_weight': 0.8,
            'vs_ace_penalty': 0.922,
            'vs_bad_pitcher_boost': 1.15
        }

    def enhance_player_cash(self, player: EnhancedPlayer):
        """Enhance player with cash-specific data"""
        # Weight components
        base_score = (
                player.base_projection * self.cash_params['weight_projection'] +
                player.recent_form_score * self.cash_params['weight_recent'] +
                player.last_5_avg * self.cash_params['weight_season']
        )

        # Consistency bonus
        if player.consistency_score > 0.7:
            base_score *= (1 + self.cash_params['consistency_weight'])

        # Platoon advantage
        if player.platoon_advantage:
            base_score *= self.cash_params['platoon_advantage_boost']

        # Hot/Cold streaks
        if player.recent_form_score > 15:
            base_score *= self.cash_params['streak_hot_boost']
        elif player.recent_form_score < 5:
            base_score *= self.cash_params['streak_cold_penalty']

        # Pitcher matchup
        if player.vs_pitcher_era > 5.0:
            base_score *= self.cash_params['vs_bad_pitcher_boost']
        elif player.vs_pitcher_era < 3.5:
            base_score *= self.cash_params['vs_ace_penalty']

        # Floor emphasis
        floor = player.base_projection * 0.7
        ceiling = player.base_projection * 1.3

        player.cash_score = (
                floor * self.cash_params['floor_weight'] +
                ceiling * (1 - self.cash_params['floor_weight'])
        )

        player.enhanced_score = player.cash_score

    def enhance_player_gpp(self, player: EnhancedPlayer):
        """Enhance player with GPP-specific data"""
        score = player.base_projection

        # Team total multipliers
        if player.team_total > self.gpp_params['threshold_high']:
            score *= self.gpp_params['mult_high']
        elif player.team_total > self.gpp_params['threshold_med']:
            score *= self.gpp_params['mult_med']
        elif player.team_total > self.gpp_params['threshold_low']:
            score *= self.gpp_params['mult_low']
        else:
            score *= self.gpp_params['mult_none']

        # Batting order boost
        if player.batting_order > 0 and player.batting_order <= self.gpp_params['batting_positions']:
            score *= self.gpp_params['batting_boost']

        # Ownership leverage
        if player.projected_ownership < self.gpp_params['ownership_threshold']:
            score *= self.gpp_params['ownership_low_boost']
        elif player.projected_ownership > 30:
            score *= self.gpp_params['ownership_high_penalty']

        # Advanced stats boosts
        if player.barrel_rate > self.gpp_params['barrel_rate_threshold']:
            score *= self.gpp_params['barrel_rate_boost']

        if player.xwoba_diff > self.gpp_params['xwoba_diff_threshold']:
            score *= self.gpp_params['undervalued_boost']

        # Pitcher specific (K upside)
        if player.primary_position == 'P' and hasattr(player, 'k9'):
            if player.k9 > self.gpp_params['min_k9_threshold']:
                score *= self.gpp_params['high_k9_boost']

        player.gpp_score = score
        player.enhanced_score = score


# ============================================
# DATA ENRICHMENT SYSTEM
# ============================================

class DataEnrichmentSystem:
    """Handles all data enrichment based on contest type"""

    def __init__(self):
        self.scoring_engine = EnhancedScoringEngine()

    def enrich_for_cash(self, players: List[EnhancedPlayer]):
        """Enrich players with cash-specific data"""
        logger.info("Enriching players for CASH contest...")

        for player in players:
            # Simulate data enrichment (you'd fetch real data)
            player.recent_form_score = np.random.uniform(5, 20)
            player.consistency_score = np.random.uniform(0.5, 0.9)
            player.last_5_avg = player.base_projection * np.random.uniform(0.8, 1.2)
            player.platoon_advantage = np.random.choice([True, False], p=[0.3, 0.7])
            player.vs_pitcher_era = np.random.uniform(3.0, 5.5)

            # Calculate cash score
            self.scoring_engine.enhance_player_cash(player)

    def enrich_for_gpp(self, players: List[EnhancedPlayer]):
        """Enrich players with GPP-specific data"""
        logger.info("Enriching players for GPP contest...")

        for player in players:
            # Simulate data enrichment (you'd fetch real data)
            player.projected_ownership = np.random.uniform(5, 35)
            player.team_total = np.random.uniform(3.5, 6.5)
            player.game_total = np.random.uniform(7, 11)
            player.barrel_rate = np.random.uniform(5, 15)
            player.xwoba_diff = np.random.uniform(-0.02, 0.05)

            if player.primary_position == 'P':
                player.k9 = np.random.uniform(7, 12)

            # Calculate GPP score
            self.scoring_engine.enhance_player_gpp(player)


# ============================================
# MAIN DFS OPTIMIZER GUI
# ============================================

class DFSOptimizerGUI(QMainWindow):
    """Complete GUI with all features"""

    def __init__(self):
        super().__init__()
        self.csv_path = None
        self.all_players = []
        self.player_pool = []
        self.slate_type = "classic"
        self.confirmation_system = SmartConfirmationSystem()
        self.enrichment_system = DataEnrichmentSystem()
        self.manual_selections = set()

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("DFS Optimizer - Complete System")
        self.setGeometry(100, 100, 1400, 900)

        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding-top: 15px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #0d7377;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #14FFEC;
                color: #1e1e1e;
            }
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #323232;
                gridline-color: #3d3d3d;
            }
            QLineEdit, QSpinBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                padding: 5px;
                color: white;
            }
        """)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # Left panel
        left_panel = self.create_left_panel()
        layout.addWidget(left_panel, 1)

        # Right panel (tabs)
        right_panel = self.create_right_panel()
        layout.addWidget(right_panel, 2)

    def create_left_panel(self):
        """Create control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # CSV Selection
        csv_group = QGroupBox("📁 Data Source")
        csv_layout = QVBoxLayout()

        self.csv_label = QLabel("No file loaded")
        self.csv_label.setStyleSheet("padding: 10px; background-color: #323232; border-radius: 4px;")
        csv_layout.addWidget(self.csv_label)

        load_btn = QPushButton("Load DraftKings CSV")
        load_btn.clicked.connect(self.load_csv)
        csv_layout.addWidget(load_btn)

        # Slate info
        self.slate_info = QLabel("")
        self.slate_info.setStyleSheet("color: #14FFEC; font-weight: bold; padding: 5px;")
        csv_layout.addWidget(self.slate_info)

        csv_group.setLayout(csv_layout)
        layout.addWidget(csv_group)

        # Contest Settings
        contest_group = QGroupBox("🎯 Contest Settings")
        contest_layout = QVBoxLayout()

        # Contest type
        self.gpp_radio = QRadioButton("GPP (Tournaments)")
        self.cash_radio = QRadioButton("Cash (50/50s)")
        self.gpp_radio.setChecked(True)
        contest_layout.addWidget(self.gpp_radio)
        contest_layout.addWidget(self.cash_radio)

        # Number of lineups
        lineup_layout = QHBoxLayout()
        lineup_layout.addWidget(QLabel("Lineups:"))
        self.lineup_count = QSpinBox()
        self.lineup_count.setRange(1, 150)
        self.lineup_count.setValue(20)
        lineup_layout.addWidget(self.lineup_count)
        contest_layout.addLayout(lineup_layout)

        contest_group.setLayout(contest_layout)
        layout.addWidget(contest_group)

        # Player Pool Settings
        pool_group = QGroupBox("👥 Player Pool")
        pool_layout = QVBoxLayout()

        self.confirmed_only = QCheckBox("Confirmed Players Only")
        self.confirmed_only.setChecked(True)
        pool_layout.addWidget(self.confirmed_only)

        self.include_manual = QCheckBox("Include Manual Selections")
        self.include_manual.setChecked(True)
        pool_layout.addWidget(self.include_manual)

        # Pool stats
        self.pool_stats = QLabel("Pool: 0 players")
        self.pool_stats.setStyleSheet("color: #888; padding: 5px;")
        pool_layout.addWidget(self.pool_stats)

        pool_group.setLayout(pool_layout)
        layout.addWidget(pool_group)

        # Action buttons
        action_group = QGroupBox("⚡ Actions")
        action_layout = QVBoxLayout()

        fetch_btn = QPushButton("🔄 Fetch Confirmations")
        fetch_btn.clicked.connect(self.fetch_confirmations)
        action_layout.addWidget(fetch_btn)

        build_btn = QPushButton("🏗️ Build Player Pool")
        build_btn.clicked.connect(self.build_player_pool)
        action_layout.addWidget(build_btn)

        optimize_btn = QPushButton("🚀 Optimize Lineups")
        optimize_btn.clicked.connect(self.optimize_lineups)
        optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #14FFEC;
                color: #1e1e1e;
                font-size: 16px;
                padding: 12px;
            }
        """)
        action_layout.addWidget(optimize_btn)

        export_btn = QPushButton("📤 Export Lineups")
        export_btn.clicked.connect(self.export_lineups)
        action_layout.addWidget(export_btn)

        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        # Console
        console_group = QGroupBox("📋 Console")
        console_layout = QVBoxLayout()

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(150)
        console_layout.addWidget(self.console)

        console_group.setLayout(console_layout)
        layout.addWidget(console_group)

        layout.addStretch()
        return panel

    def create_right_panel(self):
        """Create tabbed panel"""
        tabs = QTabWidget()

        # Player Pool tab
        self.player_table = QTableWidget()
        self.player_table.setColumnCount(8)
        self.player_table.setHorizontalHeaderLabels([
            'Name', 'Pos', 'Team', 'Salary', 'Proj', 'Status', 'Score', 'Select'
        ])
        self.player_table.setAlternatingRowColors(True)
        tabs.addTab(self.player_table, "Player Pool")

        # Lineups tab
        self.lineup_table = QTableWidget()
        tabs.addTab(self.lineup_table, "Lineups")

        # Analysis tab
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        tabs.addTab(self.analysis_text, "Analysis")

        return tabs

    def load_csv(self):
        """Load DraftKings CSV"""
        filepath, _ = QFileDialog.getOpenFileName(self, "Select DraftKings CSV", "", "CSV Files (*.csv)")
        if not filepath:
            return

        try:
            df = pd.read_csv(filepath)
            self.csv_path = filepath
            self.csv_label.setText(os.path.basename(filepath))

            # Detect slate type
            positions = set(df['Position'].unique()) if 'Position' in df else set()
            if 'CPT' in positions or 'UTIL' in positions:
                self.slate_type = "showdown"
                self.slate_info.setText("⚡ SHOWDOWN SLATE DETECTED")
                # Filter to UTIL only
                df = df[df['Position'] == 'UTIL']
                self.log("Showdown slate - using UTIL entries only", "info")
            else:
                self.slate_type = "classic"
                self.slate_info.setText("📋 CLASSIC SLATE")

            # Create players
            self.all_players = []
            for _, row in df.iterrows():
                player = EnhancedPlayer(
                    name=row.get('Name', ''),
                    position=row.get('Position', ''),
                    team=row.get('TeamAbbrev', row.get('Team', '')),
                    salary=int(row.get('Salary', 0)),
                    projection=float(row.get('AvgPointsPerGame', 0))
                )

                # Parse game info
                game_info = row.get('Game Info', '')
                if game_info and '@' in game_info:
                    parts = game_info.split('@')
                    if len(parts) == 2:
                        away = parts[0].strip()
                        home = parts[1].split()[0]
                        player.opponent = home if player.team == away else away
                        player.game_info = game_info

                self.all_players.append(player)

            self.log(f"Loaded {len(self.all_players)} players ({self.slate_type} slate)", "success")
            self.update_player_table()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")

    def fetch_confirmations(self):
        """Fetch confirmed lineups"""
        self.log("Fetching confirmed lineups...", "info")

        # Get confirmations
        self.confirmation_system.get_all_confirmations()

        # Mark confirmed players
        confirmed_count = 0
        for player in self.all_players:
            # Check if pitcher is confirmed
            if player.primary_position == 'P':
                if self.confirmation_system.is_pitcher_confirmed(player.name, player.team):
                    player.is_confirmed = True
                    confirmed_count += 1
            else:
                # Check if hitter is confirmed
                is_confirmed, order = self.confirmation_system.is_player_confirmed(player.name, player.team)
                if is_confirmed:
                    player.is_confirmed = True
                    player.batting_order = order or 0
                    confirmed_count += 1

        self.log(f"Found {confirmed_count} confirmed players", "success")
        self.update_player_table()

    def build_player_pool(self):
        """Build filtered player pool"""
        self.player_pool = []

        # Start with all players
        pool = self.all_players.copy()

        # Filter to confirmed only if checked
        if self.confirmed_only.isChecked():
            pool = [p for p in pool if p.is_confirmed]
            self.log(f"Filtered to {len(pool)} confirmed players", "info")

        # Add manual selections
        if self.include_manual.isChecked():
            manual_players = [p for p in self.all_players if p.is_manual and p not in pool]
            pool.extend(manual_players)
            if manual_players:
                self.log(f"Added {len(manual_players)} manual selections", "info")

        self.player_pool = pool
        self.pool_stats.setText(f"Pool: {len(self.player_pool)} players")

        # Enrich based on contest type
        contest_type = "gpp" if self.gpp_radio.isChecked() else "cash"
        self.log(f"Enriching pool for {contest_type.upper()} contest...", "info")

        if contest_type == "cash":
            self.enrichment_system.enrich_for_cash(self.player_pool)
        else:
            self.enrichment_system.enrich_for_gpp(self.player_pool)

        self.log("Player pool ready for optimization!", "success")
        self.update_player_table()

    def optimize_lineups(self):
        """Run optimization"""
        if not self.player_pool:
            QMessageBox.warning(self, "Warning", "Build player pool first!")
            return

        contest_type = "gpp" if self.gpp_radio.isChecked() else "cash"
        num_lineups = self.lineup_count.value()

        self.log(f"Optimizing {num_lineups} {contest_type.upper()} lineups...", "info")

        # Simple optimization (you'd use your MILP optimizer here)
        lineups = []
        for i in range(num_lineups):
            lineup = self.generate_lineup(contest_type)
            if lineup:
                lineups.append(lineup)

        self.log(f"Generated {len(lineups)} lineups", "success")
        self.display_lineups(lineups)

    def generate_lineup(self, contest_type: str):
        """Generate a single lineup (simplified)"""
        # Sort by enhanced score
        sorted_players = sorted(self.player_pool, key=lambda p: p.enhanced_score, reverse=True)

        lineup = []
        salary = 0
        positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        positions_filled = {pos: 0 for pos in positions_needed}

        for player in sorted_players:
            if salary + player.salary > 50000:
                continue

            # Check position
            for pos in player.positions:
                if pos in positions_needed and positions_filled[pos] < positions_needed[pos]:
                    lineup.append(player)
                    salary += player.salary
                    positions_filled[pos] += 1
                    break

            if len(lineup) == 10:
                break

        if len(lineup) == 10:
            return {
                'players': lineup,
                'salary': salary,
                'projection': sum(p.enhanced_score for p in lineup)
            }
        return None

    def display_lineups(self, lineups):
        """Display lineups in table"""
        self.lineup_table.clear()
        self.lineup_table.setRowCount(len(lineups))
        self.lineup_table.setColumnCount(13)
        self.lineup_table.setHorizontalHeaderLabels([
            'Lineup', 'P1', 'P2', 'C', '1B', '2B', '3B', 'SS',
            'OF1', 'OF2', 'OF3', 'Salary', 'Projection'
        ])

        for i, lineup in enumerate(lineups):
            self.lineup_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))

            # Fill positions
            positions = {'P': [], 'C': [], '1B': [], '2B': [], '3B': [], 'SS': [], 'OF': []}
            for player in lineup['players']:
                positions[player.primary_position].append(player.name)

            # Add to table
            col = 1
            for pos in ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']:
                if pos == 'P' and len(positions['P']) > 0:
                    self.lineup_table.setItem(i, col, QTableWidgetItem(positions['P'].pop(0)))
                elif pos == 'OF' and len(positions['OF']) > 0:
                    self.lineup_table.setItem(i, col, QTableWidgetItem(positions['OF'].pop(0)))
                elif pos in positions and len(positions[pos]) > 0:
                    self.lineup_table.setItem(i, col, QTableWidgetItem(positions[pos].pop(0)))
                col += 1

            self.lineup_table.setItem(i, 11, QTableWidgetItem(f"${lineup['salary']:,}"))
            self.lineup_table.setItem(i, 12, QTableWidgetItem(f"{lineup['projection']:.1f}"))

    def export_lineups(self):
        """Export lineups to CSV"""
        # Implementation here
        self.log("Export functionality to be implemented", "info")

    def update_player_table(self):
        """Update player display"""
        self.player_table.setRowCount(len(self.all_players))

        for i, player in enumerate(self.all_players):
            self.player_table.setItem(i, 0, QTableWidgetItem(player.name))
            self.player_table.setItem(i, 1, QTableWidgetItem(player.primary_position))
            self.player_table.setItem(i, 2, QTableWidgetItem(player.team))
            self.player_table.setItem(i, 3, QTableWidgetItem(f"${player.salary:,}"))
            self.player_table.setItem(i, 4, QTableWidgetItem(f"{player.base_projection:.1f}"))

            # Status
            status = ""
            if player.is_confirmed:
                status = "✅ Confirmed"
            elif player.is_manual:
                status = "📌 Manual"
            self.player_table.setItem(i, 5, QTableWidgetItem(status))

            # Enhanced score
            score_item = QTableWidgetItem(f"{player.enhanced_score:.1f}")
            if player in self.player_pool:
                score_item.setBackground(QColor(20, 255, 236, 50))
            self.player_table.setItem(i, 6, score_item)

            # Manual selection checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(player.is_manual)
            checkbox.stateChanged.connect(lambda state, p=player: self.toggle_manual(p, state))
            self.player_table.setCellWidget(i, 7, checkbox)

    def toggle_manual(self, player, state):
        """Toggle manual selection"""
        player.is_manual = state == Qt.Checked
        if player.is_manual:
            self.manual_selections.add(player.name)
        else:
            self.manual_selections.discard(player.name)

    def log(self, message: str, level: str = "info"):
        """Add message to console"""
        colors = {
            "info": "#ffffff",
            "success": "#14FFEC",
            "warning": "#ffa500",
            "error": "#ff4444"
        }

        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color: {colors.get(level, "#ffffff")}">[{timestamp}] {message}</span>'
        self.console.append(html)


# ============================================
# MAIN ENTRY POINT
# ============================================

def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show GUI
    gui = DFSOptimizerGUI()
    gui.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()