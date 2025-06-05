#!/usr/bin/env python3
"""
FUNCTIONAL ANALYTICS WIDGET
==========================
Fully functional with editable fields and real data tracking
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
import os
from datetime import datetime, timedelta
import numpy as np


class FunctionalAnalyticsWidget(QWidget):
    """Fully functional analytics with editable fields"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_gui = parent
        self.data_file = 'dfs_analytics_data.json'
        self.load_data()
        self.setup_ui()

    def load_data(self):
        """Load analytics data from file"""
        default_data = {
            'bankroll': {
                'starting': 1000.0,
                'current': 1250.0,
                'deposits': [],
                'withdrawals': []
            },
            'contests': [],
            'settings': {
                'kelly_multiplier': 0.25,
                'max_daily_risk': 0.20,
                'cash_game_pct': 0.10,
                'gpp_small_pct': 0.03,
                'gpp_large_pct': 0.01
            }
        }

        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
                    # Merge with defaults for any missing keys
                    for key in default_data:
                        if key not in self.data:
                            self.data[key] = default_data[key]
            else:
                self.data = default_data
        except:
            self.data = default_data

    def save_data(self):
        """Save analytics data to file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def setup_ui(self):
        """Setup the UI with functional components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #2563eb;
                border-bottom: 3px solid #2563eb;
            }
        """)

        # Add tabs
        self.tabs.addTab(self.create_bankroll_tab(), "💰 Bankroll")
        self.tabs.addTab(self.create_contest_history_tab(), "📊 Contest History")
        self.tabs.addTab(self.create_settings_tab(), "⚙️ Settings")
        self.tabs.addTab(self.create_calculator_tab(), "🧮 Calculators")

        layout.addWidget(self.tabs)

    def create_bankroll_tab(self):
        """Create bankroll management tab with editable fields"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Current bankroll card
        bankroll_card = self.create_card("💰 Bankroll Management")
        card_layout = QGridLayout(bankroll_card)

        # Editable fields
        row = 0

        # Starting bankroll
        card_layout.addWidget(QLabel("Starting Bankroll:"), row, 0)
        self.starting_bankroll_spin = QDoubleSpinBox()
        self.starting_bankroll_spin.setRange(0, 1000000)
        self.starting_bankroll_spin.setPrefix("$")
        self.starting_bankroll_spin.setDecimals(2)
        self.starting_bankroll_spin.setValue(self.data['bankroll']['starting'])
        self.starting_bankroll_spin.setSingleStep(100)
        self.starting_bankroll_spin.setMinimumWidth(150)
        self.starting_bankroll_spin.valueChanged.connect(self.update_starting_bankroll)
        card_layout.addWidget(self.starting_bankroll_spin, row, 1)

        row += 1

        # Current bankroll
        card_layout.addWidget(QLabel("Current Bankroll:"), row, 0)
        self.current_bankroll_spin = QDoubleSpinBox()
        self.current_bankroll_spin.setRange(0, 1000000)
        self.current_bankroll_spin.setPrefix("$")
        self.current_bankroll_spin.setDecimals(2)
        self.current_bankroll_spin.setValue(self.data['bankroll']['current'])
        self.current_bankroll_spin.setSingleStep(100)
        self.current_bankroll_spin.setMinimumWidth(150)
        self.current_bankroll_spin.valueChanged.connect(self.update_current_bankroll)
        card_layout.addWidget(self.current_bankroll_spin, row, 1)

        row += 1

        # Profit/Loss (calculated)
        card_layout.addWidget(QLabel("Total Profit/Loss:"), row, 0)
        self.profit_label = QLabel()
        self.update_profit_label()
        card_layout.addWidget(self.profit_label, row, 1)

        row += 1

        # ROI (calculated)
        card_layout.addWidget(QLabel("ROI:"), row, 0)
        self.roi_label = QLabel()
        self.update_roi_label()
        card_layout.addWidget(self.roi_label, row, 1)

        row += 1

        # Quick actions
        card_layout.addWidget(QLabel("Quick Actions:"), row, 0)
        actions_layout = QHBoxLayout()

        deposit_btn = QPushButton("➕ Deposit")
        deposit_btn.clicked.connect(self.show_deposit_dialog)
        deposit_btn.setMinimumHeight(35)
        actions_layout.addWidget(deposit_btn)

        withdraw_btn = QPushButton("➖ Withdraw")
        withdraw_btn.clicked.connect(self.show_withdraw_dialog)
        withdraw_btn.setMinimumHeight(35)
        actions_layout.addWidget(withdraw_btn)

        card_layout.addLayout(actions_layout, row, 1)

        layout.addWidget(bankroll_card)

        # Recommendations card
        reco_card = self.create_card("📋 Entry Recommendations")
        reco_layout = QVBoxLayout(reco_card)

        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setMaximumHeight(200)
        self.update_recommendations()
        reco_layout.addWidget(self.recommendations_text)

        layout.addWidget(reco_card)
        layout.addStretch()

        return widget

    def create_contest_history_tab(self):
        """Create contest history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Add contest button
        add_btn = QPushButton("➕ Add Contest Result")
        add_btn.setMinimumHeight(40)
        add_btn.clicked.connect(self.show_add_contest_dialog)
        layout.addWidget(add_btn)

        # Contest history table
        self.contest_table = QTableWidget()
        self.contest_table.setColumnCount(6)
        self.contest_table.setHorizontalHeaderLabels([
            "Date", "Type", "Entry Fee", "Winnings", "ROI", "Actions"
        ])
        self.contest_table.horizontalHeader().setStretchLastSection(True)

        self.refresh_contest_table()
        layout.addWidget(self.contest_table)

        # Statistics
        stats_card = self.create_card("📊 Contest Statistics")
        stats_layout = QGridLayout(stats_card)

        self.total_contests_label = QLabel()
        self.win_rate_label = QLabel()
        self.avg_roi_label = QLabel()
        self.best_win_label = QLabel()

        stats_layout.addWidget(QLabel("Total Contests:"), 0, 0)
        stats_layout.addWidget(self.total_contests_label, 0, 1)
        stats_layout.addWidget(QLabel("Win Rate:"), 1, 0)
        stats_layout.addWidget(self.win_rate_label, 1, 1)
        stats_layout.addWidget(QLabel("Average ROI:"), 2, 0)
        stats_layout.addWidget(self.avg_roi_label, 2, 1)
        stats_layout.addWidget(QLabel("Best Win:"), 3, 0)
        stats_layout.addWidget(self.best_win_label, 3, 1)

        self.update_contest_stats()
        layout.addWidget(stats_card)

        return widget

    def create_settings_tab(self):
        """Create settings tab with editable parameters"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Risk management settings
        risk_card = self.create_card("⚠️ Risk Management Settings")
        risk_layout = QFormLayout(risk_card)

        # Kelly multiplier
        self.kelly_mult_spin = QDoubleSpinBox()
        self.kelly_mult_spin.setRange(0.1, 1.0)
        self.kelly_mult_spin.setSingleStep(0.05)
        self.kelly_mult_spin.setValue(self.data['settings']['kelly_multiplier'])
        self.kelly_mult_spin.valueChanged.connect(lambda v: self.update_setting('kelly_multiplier', v))
        risk_layout.addRow("Kelly Multiplier:", self.kelly_mult_spin)

        # Max daily risk
        self.max_risk_spin = QDoubleSpinBox()
        self.max_risk_spin.setRange(0.01, 0.50)
        self.max_risk_spin.setSingleStep(0.01)
        self.max_risk_spin.setSuffix("%")
        self.max_risk_spin.setValue(self.data['settings']['max_daily_risk'] * 100)
        self.max_risk_spin.valueChanged.connect(lambda v: self.update_setting('max_daily_risk', v / 100))
        risk_layout.addRow("Max Daily Risk:", self.max_risk_spin)

        layout.addWidget(risk_card)

        # Contest allocation settings
        alloc_card = self.create_card("📊 Contest Allocation")
        alloc_layout = QFormLayout(alloc_card)

        # Cash game percentage
        self.cash_pct_spin = QDoubleSpinBox()
        self.cash_pct_spin.setRange(1, 20)
        self.cash_pct_spin.setSingleStep(1)
        self.cash_pct_spin.setSuffix("%")
        self.cash_pct_spin.setValue(self.data['settings']['cash_game_pct'] * 100)
        self.cash_pct_spin.valueChanged.connect(lambda v: self.update_setting('cash_game_pct', v / 100))
        alloc_layout.addRow("Cash Game %:", self.cash_pct_spin)

        # Small GPP percentage
        self.small_gpp_spin = QDoubleSpinBox()
        self.small_gpp_spin.setRange(0.5, 10)
        self.small_gpp_spin.setSingleStep(0.5)
        self.small_gpp_spin.setSuffix("%")
        self.small_gpp_spin.setValue(self.data['settings']['gpp_small_pct'] * 100)
        self.small_gpp_spin.valueChanged.connect(lambda v: self.update_setting('gpp_small_pct', v / 100))
        alloc_layout.addRow("Small GPP %:", self.small_gpp_spin)

        # Large GPP percentage
        self.large_gpp_spin = QDoubleSpinBox()
        self.large_gpp_spin.setRange(0.1, 5)
        self.large_gpp_spin.setSingleStep(0.1)
        self.large_gpp_spin.setSuffix("%")
        self.large_gpp_spin.setValue(self.data['settings']['gpp_large_pct'] * 100)
        self.large_gpp_spin.valueChanged.connect(lambda v: self.update_setting('gpp_large_pct', v / 100))
        alloc_layout.addRow("Large GPP %:", self.large_gpp_spin)

        layout.addWidget(alloc_card)

        # Save button
        save_btn = QPushButton("💾 Save All Settings")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_all_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

        return widget

    def create_calculator_tab(self):
        """Create calculators tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Kelly calculator
        kelly_card = self.create_card("🎲 Kelly Criterion Calculator")
        kelly_layout = QFormLayout(kelly_card)

        self.win_rate_input = QDoubleSpinBox()
        self.win_rate_input.setRange(0, 100)
        self.win_rate_input.setSuffix("%")
        self.win_rate_input.setValue(55)
        kelly_layout.addRow("Win Rate:", self.win_rate_input)

        self.avg_odds_input = QDoubleSpinBox()
        self.avg_odds_input.setRange(1.0, 10.0)
        self.avg_odds_input.setPrefix("x")
        self.avg_odds_input.setValue(1.8)
        self.avg_odds_input.setSingleStep(0.1)
        kelly_layout.addRow("Average Odds:", self.avg_odds_input)

        calc_btn = QPushButton("Calculate Optimal Bet Size")
        calc_btn.setMinimumHeight(35)
        calc_btn.clicked.connect(self.calculate_kelly)
        kelly_layout.addRow(calc_btn)

        self.kelly_result = QTextEdit()
        self.kelly_result.setMaximumHeight(100)
        self.kelly_result.setReadOnly(True)
        kelly_layout.addRow(self.kelly_result)

        layout.addWidget(kelly_card)

        # ROI calculator
        roi_card = self.create_card("📈 ROI Calculator")
        roi_layout = QFormLayout(roi_card)

        self.roi_invested = QDoubleSpinBox()
        self.roi_invested.setRange(0, 100000)
        self.roi_invested.setPrefix("$")
        roi_layout.addRow("Total Invested:", self.roi_invested)

        self.roi_returned = QDoubleSpinBox()
        self.roi_returned.setRange(0, 100000)
        self.roi_returned.setPrefix("$")
        roi_layout.addRow("Total Returned:", self.roi_returned)

        roi_calc_btn = QPushButton("Calculate ROI")
        roi_calc_btn.setMinimumHeight(35)
        roi_calc_btn.clicked.connect(self.calculate_roi)
        roi_layout.addRow(roi_calc_btn)

        self.roi_result = QLabel()
        roi_layout.addRow("ROI:", self.roi_result)

        layout.addWidget(roi_card)
        layout.addStretch()

        return widget

    def create_card(self, title):
        """Create a card widget"""
        card = QGroupBox(title)
        card.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 20px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
            }
        """)
        return card

    # Update methods
    def update_starting_bankroll(self, value):
        """Update starting bankroll"""
        self.data['bankroll']['starting'] = value
        self.update_profit_label()
        self.update_roi_label()
        self.update_recommendations()
        self.save_data()

    def update_current_bankroll(self, value):
        """Update current bankroll"""
        self.data['bankroll']['current'] = value
        self.update_profit_label()
        self.update_roi_label()
        self.update_recommendations()
        self.save_data()

    def update_profit_label(self):
        """Update profit/loss label"""
        profit = self.data['bankroll']['current'] - self.data['bankroll']['starting']
        if profit >= 0:
            self.profit_label.setText(f"<span style='color: #10b981;'>+${profit:,.2f}</span>")
        else:
            self.profit_label.setText(f"<span style='color: #ef4444;'>-${abs(profit):,.2f}</span>")

    def update_roi_label(self):
        """Update ROI label"""
        if self.data['bankroll']['starting'] > 0:
            roi = ((self.data['bankroll']['current'] - self.data['bankroll']['starting']) / 
                   self.data['bankroll']['starting']) * 100
            color = '#10b981' if roi >= 0 else '#ef4444'
            self.roi_label.setText(f"<span style='color: {color};'>{roi:.1f}%</span>")
        else:
            self.roi_label.setText("N/A")

    def update_recommendations(self):
        """Update entry recommendations"""
        current = self.data['bankroll']['current']

        reco_text = f"""
<b>Based on your current bankroll of ${current:,.2f}:</b><br><br>

<b>Cash Games (50/50):</b> ${current * 0.05:.0f} - ${current * 0.10:.0f} per entry<br>
<b>Small GPPs:</b> ${current * 0.01:.0f} - ${current * 0.03:.0f} per entry<br>
<b>Large GPPs:</b> ${current * 0.005:.0f} - ${current * 0.01:.0f} per entry<br>
<b>Total Daily Risk:</b> ${current * 0.10:.0f} - ${current * 0.20:.0f} maximum<br><br>

<i>These recommendations are based on standard bankroll management principles.</i>
"""
        self.recommendations_text.setHtml(reco_text)

    def update_setting(self, key, value):
        """Update a setting value"""
        self.data['settings'][key] = value
        self.save_data()

    def save_all_settings(self):
        """Save all settings and show confirmation"""
        self.save_data()
        QMessageBox.information(self, "Settings Saved", "All settings have been saved successfully!")

    # Dialog methods
    def show_deposit_dialog(self):
        """Show deposit dialog"""
        amount, ok = QInputDialog.getDouble(self, "Deposit", "Enter deposit amount:", 
                                           100, 0, 100000, 2)
        if ok and amount > 0:
            self.data['bankroll']['current'] += amount
            self.data['bankroll']['deposits'].append({
                'date': datetime.now().isoformat(),
                'amount': amount
            })
            self.current_bankroll_spin.setValue(self.data['bankroll']['current'])
            self.save_data()
            QMessageBox.information(self, "Success", f"Deposited ${amount:,.2f}")

    def show_withdraw_dialog(self):
        """Show withdrawal dialog"""
        max_withdraw = self.data['bankroll']['current']
        amount, ok = QInputDialog.getDouble(self, "Withdraw", "Enter withdrawal amount:", 
                                           100, 0, max_withdraw, 2)
        if ok and amount > 0:
            self.data['bankroll']['current'] -= amount
            self.data['bankroll']['withdrawals'].append({
                'date': datetime.now().isoformat(),
                'amount': amount
            })
            self.current_bankroll_spin.setValue(self.data['bankroll']['current'])
            self.save_data()
            QMessageBox.information(self, "Success", f"Withdrew ${amount:,.2f}")

    def show_add_contest_dialog(self):
        """Show add contest dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Contest Result")
        dialog.setMinimumWidth(400)

        layout = QFormLayout(dialog)

        # Contest type
        type_combo = QComboBox()
        type_combo.addItems(["Cash Game", "Small GPP", "Large GPP", "Head-to-Head", "Satellite"])
        layout.addRow("Contest Type:", type_combo)

        # Entry fee
        entry_spin = QDoubleSpinBox()
        entry_spin.setRange(0, 10000)
        entry_spin.setPrefix("$")
        layout.addRow("Entry Fee:", entry_spin)

        # Winnings
        winnings_spin = QDoubleSpinBox()
        winnings_spin.setRange(0, 100000)
        winnings_spin.setPrefix("$")
        layout.addRow("Winnings:", winnings_spin)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec_() == QDialog.Accepted:
            contest = {
                'date': datetime.now().isoformat(),
                'type': type_combo.currentText(),
                'entry': entry_spin.value(),
                'winnings': winnings_spin.value()
            }

            if 'contests' not in self.data:
                self.data['contests'] = []

            self.data['contests'].append(contest)

            # Update bankroll
            net = contest['winnings'] - contest['entry']
            self.data['bankroll']['current'] += net
            self.current_bankroll_spin.setValue(self.data['bankroll']['current'])

            self.save_data()
            self.refresh_contest_table()
            self.update_contest_stats()

    def refresh_contest_table(self):
        """Refresh the contest history table"""
        contests = self.data.get('contests', [])
        self.contest_table.setRowCount(len(contests))

        for i, contest in enumerate(contests):
            # Date
            date = datetime.fromisoformat(contest['date']).strftime('%Y-%m-%d')
            self.contest_table.setItem(i, 0, QTableWidgetItem(date))

            # Type
            self.contest_table.setItem(i, 1, QTableWidgetItem(contest['type']))

            # Entry fee
            self.contest_table.setItem(i, 2, QTableWidgetItem(f"${contest['entry']:.2f}"))

            # Winnings
            self.contest_table.setItem(i, 3, QTableWidgetItem(f"${contest['winnings']:.2f}"))

            # ROI
            if contest['entry'] > 0:
                roi = ((contest['winnings'] - contest['entry']) / contest['entry']) * 100
                roi_text = f"{roi:.1f}%"
                roi_item = QTableWidgetItem(roi_text)
                if roi >= 0:
                    roi_item.setForeground(QColor("#10b981"))
                else:
                    roi_item.setForeground(QColor("#ef4444"))
                self.contest_table.setItem(i, 4, roi_item)
            else:
                self.contest_table.setItem(i, 4, QTableWidgetItem("N/A"))

            # Delete button
            delete_btn = QPushButton("🗑️")
            delete_btn.clicked.connect(lambda checked, idx=i: self.delete_contest(idx))
            self.contest_table.setCellWidget(i, 5, delete_btn)

    def delete_contest(self, index):
        """Delete a contest"""
        reply = QMessageBox.question(self, "Delete Contest", 
                                   "Are you sure you want to delete this contest?",
                                   QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            contest = self.data['contests'][index]

            # Revert bankroll change
            net = contest['winnings'] - contest['entry']
            self.data['bankroll']['current'] -= net
            self.current_bankroll_spin.setValue(self.data['bankroll']['current'])

            # Remove contest
            del self.data['contests'][index]

            self.save_data()
            self.refresh_contest_table()
            self.update_contest_stats()

    def update_contest_stats(self):
        """Update contest statistics"""
        contests = self.data.get('contests', [])

        if not contests:
            self.total_contests_label.setText("0")
            self.win_rate_label.setText("N/A")
            self.avg_roi_label.setText("N/A")
            self.best_win_label.setText("N/A")
            return

        # Total contests
        self.total_contests_label.setText(str(len(contests)))

        # Win rate
        wins = sum(1 for c in contests if c['winnings'] > c['entry'])
        win_rate = (wins / len(contests)) * 100
        self.win_rate_label.setText(f"{win_rate:.1f}%")

        # Average ROI
        total_invested = sum(c['entry'] for c in contests)
        total_returned = sum(c['winnings'] for c in contests)
        if total_invested > 0:
            avg_roi = ((total_returned - total_invested) / total_invested) * 100
            self.avg_roi_label.setText(f"{avg_roi:.1f}%")
        else:
            self.avg_roi_label.setText("N/A")

        # Best win
        best_win = max((c['winnings'] - c['entry'] for c in contests), default=0)
        self.best_win_label.setText(f"${best_win:.2f}")

    def calculate_kelly(self):
        """Calculate Kelly criterion"""
        win_rate = self.win_rate_input.value() / 100
        odds = self.avg_odds_input.value()

        # Kelly formula
        q = 1 - win_rate
        kelly_pct = ((win_rate * odds - q) / odds) * 100

        # Apply safety factor
        safe_kelly = kelly_pct * self.data['settings']['kelly_multiplier']

        bankroll = self.data['bankroll']['current']
        bet_size = bankroll * (safe_kelly / 100)

        result_text = f"""
<b>Kelly Criterion Results:</b><br>
Full Kelly: {kelly_pct:.1f}% of bankroll<br>
Safe Kelly ({self.data['settings']['kelly_multiplier']:.0%}): {safe_kelly:.1f}% of bankroll<br>
<b>Recommended bet size: ${bet_size:.2f}</b><br>
<small>Based on ${bankroll:,.2f} bankroll</small>
"""
        self.kelly_result.setHtml(result_text)

    def calculate_roi(self):
        """Calculate ROI"""
        invested = self.roi_invested.value()
        returned = self.roi_returned.value()

        if invested > 0:
            roi = ((returned - invested) / invested) * 100
            color = '#10b981' if roi >= 0 else '#ef4444'
            self.roi_result.setText(f"<span style='color: {color}; font-size: 18px; font-weight: bold;'>{roi:.1f}%</span>")
        else:
            self.roi_result.setText("N/A")
