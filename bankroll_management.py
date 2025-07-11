#!/usr/bin/env python3
"""
BANKROLL MANAGEMENT AND CONTEST RECOMMENDATION SYSTEM
=====================================================
Professional bankroll analytics and recommendations
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class BankrollManager:
    """Core bankroll management logic"""

    def __init__(self):
        self.data_file = "bankroll_history.json"
        # Initialize data with defaults FIRST - this is crucial
        self.data = {
            'starting_bankroll': 1000,
            'current_bankroll': 1000,
            'transactions': [],
            'contest_history': [],
            'settings': {
                'risk_tolerance': 'moderate',
                'max_daily_risk': 0.10,  # 10% of bankroll
                'kelly_multiplier': 0.25  # Conservative Kelly
            }
        }
        # Then try to load from file
        self.load_data()

    def load_data(self):
        """Load bankroll history"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    loaded_data = json.load(f)
                    # Update existing data with loaded data
                    if isinstance(loaded_data, dict):
                        # Ensure all required keys exist
                        for key in ['starting_bankroll', 'current_bankroll', 'transactions', 
                                   'contest_history', 'settings']:
                            if key in loaded_data:
                                self.data[key] = loaded_data[key]
        except Exception as e:
            print(f"Warning: Could not load bankroll data: {e}")
            # Data already initialized with defaults in __init__

    def save_data(self):
        """Save bankroll data"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save bankroll data: {e}")

    def get_recommendations(self, slate_info: Dict = None) -> Dict:
        """Get contest recommendations based on bankroll"""
        if slate_info is None:
            slate_info = {}

        bankroll = self.data.get('current_bankroll', 1000)
        risk_tolerance = self.data.get('settings', {}).get('risk_tolerance', 'moderate')

        recommendations = {
            'daily_budget': self._calculate_daily_budget(bankroll, risk_tolerance),
            'contest_allocation': self._get_contest_allocation(bankroll, risk_tolerance),
            'specific_contests': self._recommend_specific_contests(bankroll, slate_info),
            'lineup_distribution': self._get_lineup_distribution(bankroll),
            'warnings': self._get_warnings(bankroll)
        }

        return recommendations

    def _calculate_daily_budget(self, bankroll: float, risk_tolerance: str) -> Dict:
        """Calculate recommended daily budget"""
        risk_multipliers = {
            'conservative': 0.05,  # 5% daily
            'moderate': 0.10,  # 10% daily
            'aggressive': 0.15,  # 15% daily
            'very_aggressive': 0.20  # 20% daily
        }

        multiplier = risk_multipliers.get(risk_tolerance, 0.10)
        daily_amount = bankroll * multiplier

        return {
            'total': daily_amount,
            'min': daily_amount * 0.8,
            'max': daily_amount * 1.2,
            'percentage': multiplier * 100
        }

    def _get_contest_allocation(self, bankroll: float, risk_tolerance: str) -> Dict:
        """Recommend how to split budget across contest types"""

        allocations = {
            'conservative': {
                'cash': 0.80,  # 80% in cash games
                'single_gpp': 0.15,  # 15% in single entry GPPs
                'multi_gpp': 0.05  # 5% in multi-entry GPPs
            },
            'moderate': {
                'cash': 0.60,  # 60% in cash games
                'single_gpp': 0.25,  # 25% in single entry GPPs
                'multi_gpp': 0.15  # 15% in multi-entry GPPs
            },
            'aggressive': {
                'cash': 0.30,  # 30% in cash games
                'single_gpp': 0.30,  # 30% in single entry GPPs
                'multi_gpp': 0.40  # 40% in multi-entry GPPs
            },
            'very_aggressive': {
                'cash': 0.10,  # 10% in cash games
                'single_gpp': 0.20,  # 20% in single entry GPPs
                'multi_gpp': 0.70  # 70% in multi-entry GPPs
            }
        }

        allocation = allocations.get(risk_tolerance, allocations['moderate'])
        daily_budget = self._calculate_daily_budget(bankroll, risk_tolerance)['total']

        return {
            'cash_games': {
                'percentage': allocation['cash'] * 100,
                'amount': daily_budget * allocation['cash']
            },
            'single_entry_gpp': {
                'percentage': allocation['single_gpp'] * 100,
                'amount': daily_budget * allocation['single_gpp']
            },
            'multi_entry_gpp': {
                'percentage': allocation['multi_gpp'] * 100,
                'amount': daily_budget * allocation['multi_gpp']
            }
        }

    def _recommend_specific_contests(self, bankroll: float, slate_info: Dict) -> List[Dict]:
        """Recommend specific contests to enter"""
        recommendations = []
        risk_tolerance = self.data.get('settings', {}).get('risk_tolerance', 'moderate')
        daily_budget = self._calculate_daily_budget(bankroll, risk_tolerance)['total']

        # Cash game recommendations
        cash_budget = daily_budget * 0.6  # 60% for moderate risk

        if cash_budget >= 50:
            recommendations.append({
                'type': 'Cash - Double Up',
                'buy_in': 50,
                'entries': int(cash_budget * 0.3 / 50),
                'reason': 'Large field double-ups have consistent payout structure'
            })

        if cash_budget >= 10:
            recommendations.append({
                'type': 'Cash - 50/50',
                'buy_in': 10,
                'entries': int(cash_budget * 0.4 / 10),
                'reason': 'Good for building bankroll steadily'
            })

        if cash_budget >= 5:
            recommendations.append({
                'type': 'Cash - Head to Head',
                'buy_in': 5,
                'entries': int(cash_budget * 0.3 / 5),
                'reason': 'Lower rake, good win rate with solid lineups'
            })

        # GPP recommendations
        gpp_budget = daily_budget * 0.4  # 40% for moderate risk

        if gpp_budget >= 20:
            recommendations.append({
                'type': 'Single Entry GPP',
                'buy_in': 20,
                'entries': 1,
                'reason': 'Best ROI potential, levels playing field'
            })

        if gpp_budget >= 3:
            recommendations.append({
                'type': 'Multi Entry GPP',
                'buy_in': 3,
                'entries': min(20, int(gpp_budget * 0.5 / 3)),
                'reason': 'Good for testing multiple lineup constructions'
            })

        return recommendations

    def _get_lineup_distribution(self, bankroll: float) -> Dict:
        """Recommend how many unique lineups to create"""

        if bankroll < 100:
            return {
                'cash_lineups': 1,
                'gpp_lineups': 2,
                'total_lineups': 3,
                'reasoning': 'Small bankroll - focus on quality over quantity'
            }
        elif bankroll < 500:
            return {
                'cash_lineups': 2,
                'gpp_lineups': 5,
                'total_lineups': 7,
                'reasoning': 'Build slowly with limited lineup diversity'
            }
        elif bankroll < 1000:
            return {
                'cash_lineups': 3,
                'gpp_lineups': 10,
                'total_lineups': 13,
                'reasoning': 'Moderate diversity while maintaining quality'
            }
        else:
            return {
                'cash_lineups': 5,
                'gpp_lineups': 20,
                'total_lineups': 25,
                'reasoning': 'Full lineup diversity for maximum coverage'
            }

    def _get_warnings(self, bankroll: float) -> List[str]:
        """Generate warnings based on bankroll status"""
        warnings = []

        if bankroll < 100:
            warnings.append("⚠️ Low bankroll - consider minimum buy-in contests only")

        starting = self.data.get('starting_bankroll', 1000)
        if bankroll < starting * 0.5:
            warnings.append("⚠️ Down 50% from starting bankroll - consider reducing stakes")

        # Check recent performance
        recent_contests = self.data.get('contest_history', [])[-10:]
        if recent_contests:
            total_entry = sum(c.get('entry_fee', 0) for c in recent_contests)
            total_profit = sum(c.get('profit', 0) for c in recent_contests)
            if total_entry > 0:
                recent_roi = total_profit / total_entry
                if recent_roi < -0.2:
                    warnings.append("⚠️ Recent ROI below -20% - review strategy")

        return warnings

    def calculate_kelly_criterion(self, win_rate: float, avg_odds: float) -> float:
        """Calculate Kelly Criterion for optimal bet sizing"""
        if win_rate <= 0 or win_rate >= 1:
            return 0

        # Kelly formula: f = (p * b - q) / b
        # where p = win probability, q = loss probability, b = odds
        q = 1 - win_rate
        kelly = (win_rate * avg_odds - q) / avg_odds

        # Apply safety multiplier
        kelly_multiplier = self.data.get('settings', {}).get('kelly_multiplier', 0.25)
        safe_kelly = kelly * kelly_multiplier

        return max(0, min(0.25, safe_kelly))  # Cap at 25% of bankroll


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
        self.manager.load_data()  # Reload data
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


# Continue with BankrollManagementWidget...

class BankrollManagementWidget(QWidget):
    """Bankroll management GUI widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.manager = BankrollManager()
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        """Create the UI"""
        layout = QVBoxLayout(self)

        # Create tab widget for different sections
        self.tabs = QTabWidget()

        self.tabs.addTab(self.create_overview_tab(), "📊 Overview")
        self.tabs.addTab(self.create_recommendations_tab(), "🎯 Recommendations")
        self.tabs.addTab(self.create_calculator_tab(), "🧮 Calculators")
        self.tabs.addTab(self.create_history_tab(), "📈 History")
        self.tabs.addTab(self.create_settings_tab(), "⚙️ Settings")

        layout.addWidget(self.tabs)

    def create_overview_tab(self):
        """Create overview tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Current bankroll card
        bankroll_card = self.create_card("💰 Current Bankroll")
        bankroll_layout = QVBoxLayout(bankroll_card)

        self.bankroll_label = QLabel(f"${self.manager.data['current_bankroll']:,.2f}")
        self.bankroll_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #10b981;
        """)
        self.bankroll_label.setAlignment(Qt.AlignCenter)

        # Stats grid
        stats_grid = QGridLayout()

        starting = self.manager.data['starting_bankroll']
        current = self.manager.data['current_bankroll']
        profit = current - starting
        roi = (profit / starting * 100) if starting > 0 else 0

        stats = [
            ("Starting", f"${starting:,.2f}"),
            ("Profit/Loss", f"${profit:+,.2f}"),
            ("ROI", f"{roi:+.1f}%"),
            ("Risk Level", self.manager.data['settings']['risk_tolerance'].title())
        ]

        for i, (label, value) in enumerate(stats):
            label_widget = QLabel(label)
            label_widget.setStyleSheet("color: #6b7280; font-size: 12px;")
            value_widget = QLabel(value)
            value_widget.setStyleSheet("font-size: 16px; font-weight: bold;")

            stats_grid.addWidget(label_widget, i // 2, (i % 2) * 2)
            stats_grid.addWidget(value_widget, i // 2, (i % 2) * 2 + 1)

        bankroll_layout.addWidget(self.bankroll_label)
        bankroll_layout.addLayout(stats_grid)

        layout.addWidget(bankroll_card)

        # Daily budget card
        budget_card = self.create_card("📅 Today's Budget")
        budget_layout = QVBoxLayout(budget_card)

        daily_budget = self.manager._calculate_daily_budget(
            current,
            self.manager.data['settings']['risk_tolerance']
        )

        self.budget_label = QLabel(f"${daily_budget['total']:.2f}")
        self.budget_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #3b82f6;")
        self.budget_label.setAlignment(Qt.AlignCenter)

        budget_info = QLabel(f"{daily_budget['percentage']:.1f}% of bankroll")
        budget_info.setStyleSheet("color: #6b7280;")
        budget_info.setAlignment(Qt.AlignCenter)

        budget_layout.addWidget(self.budget_label)
        budget_layout.addWidget(budget_info)

        # Allocation pie chart (simplified)
        allocation = self.manager._get_contest_allocation(
            current,
            self.manager.data['settings']['risk_tolerance']
        )

        allocation_text = f"""
        <b>Recommended Allocation:</b><br>
        Cash Games: ${allocation['cash_games']['amount']:.2f} ({allocation['cash_games']['percentage']:.0f}%)<br>
        Single Entry GPP: ${allocation['single_entry_gpp']['amount']:.2f} ({allocation['single_entry_gpp']['percentage']:.0f}%)<br>
        Multi Entry GPP: ${allocation['multi_entry_gpp']['amount']:.2f} ({allocation['multi_entry_gpp']['percentage']:.0f}%)
        """

        allocation_label = QLabel(allocation_text)
        allocation_label.setWordWrap(True)
        budget_layout.addWidget(allocation_label)

        layout.addWidget(budget_card)

        # Warnings
        warnings = self.manager._get_warnings(current)
        if warnings:
            warning_card = self.create_card("⚠️ Warnings", "#fef3c7")
            warning_layout = QVBoxLayout(warning_card)

            for warning in warnings:
                warning_label = QLabel(warning)
                warning_label.setWordWrap(True)
                warning_label.setStyleSheet("color: #92400e; margin: 5px 0;")
                warning_layout.addWidget(warning_label)

            layout.addWidget(warning_card)

        layout.addStretch()
        return widget

    def create_recommendations_tab(self):
        """Create recommendations tab with auto-updating"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Add the smart recommendation widget
        self.smart_reco = SmartContestRecommendation(self)
        layout.addWidget(self.smart_reco)

        # Manual refresh button
        refresh_btn = QPushButton("🔄 Refresh Recommendations")
        refresh_btn.clicked.connect(self.smart_reco.update_recommendations)
        layout.addWidget(refresh_btn)

        layout.addStretch()
        return widget

    def create_calculator_tab(self):
        """Create calculators tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Kelly Criterion Calculator
        kelly_card = self.create_card("🎲 Kelly Criterion Calculator")
        kelly_layout = QFormLayout(kelly_card)

        self.win_rate_input = QDoubleSpinBox()
        self.win_rate_input.setRange(0, 100)
        self.win_rate_input.setValue(55)
        self.win_rate_input.setSuffix("%")

        self.avg_odds_input = QDoubleSpinBox()
        self.avg_odds_input.setRange(1.0, 10.0)
        self.avg_odds_input.setValue(1.8)
        self.avg_odds_input.setPrefix("x")

        kelly_layout.addRow("Win Rate:", self.win_rate_input)
        kelly_layout.addRow("Average Odds:", self.avg_odds_input)

        calculate_kelly_btn = QPushButton("Calculate Optimal Bet Size")
        calculate_kelly_btn.clicked.connect(self.calculate_kelly)
        kelly_layout.addRow(calculate_kelly_btn)

        self.kelly_result = QLabel("")
        self.kelly_result.setWordWrap(True)
        self.kelly_result.setStyleSheet("""
            padding: 10px;
            background-color: #f0f9ff;
            border-radius: 6px;
            margin-top: 10px;
        """)
        kelly_layout.addRow(self.kelly_result)

        layout.addWidget(kelly_card)

        # ROI Calculator
        roi_card = self.create_card("📊 ROI Calculator")
        roi_layout = QFormLayout(roi_card)

        self.total_entry_input = QDoubleSpinBox()
        self.total_entry_input.setRange(0, 10000)
        self.total_entry_input.setValue(100)
        self.total_entry_input.setPrefix("$")

        self.total_return_input = QDoubleSpinBox()
        self.total_return_input.setRange(0, 10000)
        self.total_return_input.setValue(120)
        self.total_return_input.setPrefix("$")

        roi_layout.addRow("Total Entry Fees:", self.total_entry_input)
        roi_layout.addRow("Total Returns:", self.total_return_input)

        calculate_roi_btn = QPushButton("Calculate ROI")
        calculate_roi_btn.clicked.connect(self.calculate_roi)
        roi_layout.addRow(calculate_roi_btn)

        self.roi_result = QLabel("")
        self.roi_result.setWordWrap(True)
        self.roi_result.setStyleSheet("""
            padding: 10px;
            background-color: #f0f9ff;
            border-radius: 6px;
            margin-top: 10px;
        """)
        roi_layout.addRow(self.roi_result)

        layout.addWidget(roi_card)

        layout.addStretch()
        return widget

    def create_history_tab(self):
        """Create history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Add transaction form
        add_card = self.create_card("➕ Add Transaction")
        add_layout = QFormLayout(add_card)

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(-10000, 10000)
        self.amount_input.setPrefix("$")

        self.transaction_type = QComboBox()
        self.transaction_type.addItems(["Deposit", "Withdrawal", "Contest Entry", "Contest Win"])

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Optional notes...")

        add_layout.addRow("Amount:", self.amount_input)
        add_layout.addRow("Type:", self.transaction_type)
        add_layout.addRow("Notes:", self.notes_input)

        add_btn = QPushButton("Add Transaction")
        add_btn.clicked.connect(self.add_transaction)
        add_layout.addRow(add_btn)

        layout.addWidget(add_card)

        # Transaction history
        history_card = self.create_card("📜 Transaction History")
        history_layout = QVBoxLayout(history_card)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Date", "Type", "Amount", "Notes"])

        history_layout.addWidget(self.history_table)
        layout.addWidget(history_card)

        self.refresh_history()

        return widget

    def create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Risk settings
        risk_card = self.create_card("⚙️ Risk Settings")
        risk_layout = QFormLayout(risk_card)

        self.risk_combo = QComboBox()
        self.risk_combo.addItems(["conservative", "moderate", "aggressive", "very_aggressive"])
        self.risk_combo.setCurrentText(self.manager.data['settings']['risk_tolerance'])

        self.max_daily_risk = QDoubleSpinBox()
        self.max_daily_risk.setRange(1, 30)
        self.max_daily_risk.setValue(self.manager.data['settings']['max_daily_risk'] * 100)
        self.max_daily_risk.setSuffix("%")

        self.kelly_mult = QDoubleSpinBox()
        self.kelly_mult.setRange(0.1, 1.0)
        self.kelly_mult.setValue(self.manager.data['settings']['kelly_multiplier'])
        self.kelly_mult.setSingleStep(0.05)

        risk_layout.addRow("Risk Tolerance:", self.risk_combo)
        risk_layout.addRow("Max Daily Risk:", self.max_daily_risk)
        risk_layout.addRow("Kelly Multiplier:", self.kelly_mult)

        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        risk_layout.addRow(save_btn)

        layout.addWidget(risk_card)

        # Bankroll settings
        bankroll_card = self.create_card("💰 Bankroll Settings")
        bankroll_layout = QFormLayout(bankroll_card)

        # Current starting bankroll display
        current_starting = QLabel(f"Current Starting Bankroll: ${self.manager.data['starting_bankroll']:,.2f}")
        current_starting.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        bankroll_layout.addRow(current_starting)

        # New starting bankroll input
        self.new_starting_bankroll = QDoubleSpinBox()
        self.new_starting_bankroll.setRange(100, 100000)
        self.new_starting_bankroll.setValue(self.manager.data['starting_bankroll'])
        self.new_starting_bankroll.setPrefix("$")
        self.new_starting_bankroll.setSingleStep(100)

        bankroll_layout.addRow("New Starting Bankroll:", self.new_starting_bankroll)

        # Option to adjust current bankroll too
        self.adjust_current = QCheckBox("Also set current bankroll to this amount")
        self.adjust_current.setChecked(True)
        bankroll_layout.addRow("", self.adjust_current)

        update_bankroll_btn = QPushButton("Update Starting Bankroll")
        update_bankroll_btn.clicked.connect(self.update_starting_bankroll)
        bankroll_layout.addRow(update_bankroll_btn)

        layout.addWidget(bankroll_card)

        # Bankroll reset
        reset_card = self.create_card("🔄 Reset Bankroll")
        reset_layout = QVBoxLayout(reset_card)

        reset_info = QLabel("⚠️ This will reset your bankroll to starting amount and clear history")
        reset_info.setWordWrap(True)
        reset_info.setStyleSheet("color: #dc2626; margin-bottom: 10px;")
        reset_layout.addWidget(reset_info)

        reset_btn = QPushButton("Reset Bankroll")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)
        reset_btn.clicked.connect(self.reset_bankroll)
        reset_layout.addWidget(reset_btn)

        layout.addWidget(reset_card)

        layout.addStretch()
        return widget

    def create_card(self, title, bg_color="#ffffff"):
        """Create a styled card widget"""
        card = QGroupBox(title)
        card.setStyleSheet(f"""
            QGroupBox {{
                background-color: {bg_color};
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px;
            }}
        """)
        return card

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
            self.refresh_data()
            self.refresh_history()

            QMessageBox.information(
                self, "Success",
                f"Starting bankroll updated to ${new_starting:,.2f}"
            )

            # Refresh the current starting bankroll display
            self.tabs.widget(4).findChildren(QLabel)[0].setText(
                f"Current Starting Bankroll: ${new_starting:,.2f}"
            )

    def generate_lineups(self, contest_type, count):
        """Generate lineups based on recommendations"""
        if hasattr(self.parent, 'quick_generate'):
            self.parent.quick_generate(count, contest_type)
        else:
            QMessageBox.information(
                self, "Generate Lineups",
                f"Would generate {count} {contest_type} lineups\n"
                "Connect to main optimizer to use this feature"
            )

    def calculate_kelly(self):
        """Calculate Kelly Criterion"""
        win_rate = self.win_rate_input.value() / 100
        odds = self.avg_odds_input.value()

        kelly = self.manager.calculate_kelly_criterion(win_rate, odds)

        bankroll = self.manager.data['current_bankroll']
        bet_size = bankroll * kelly

        self.kelly_result.setText(f"""
        <b>Kelly Criterion Results:</b><br>
        Optimal bet percentage: {kelly * 100:.1f}%<br>
        Recommended bet size: ${bet_size:.2f}<br>
        <br>
        <small>This includes a {self.manager.data['settings']['kelly_multiplier']}x safety factor</small>
        """)

    def calculate_roi(self):
        """Calculate ROI"""
        entry = self.total_entry_input.value()
        returns = self.total_return_input.value()

        if entry > 0:
            profit = returns - entry
            roi = (profit / entry) * 100

            color = "#10b981" if roi > 0 else "#dc2626"

            self.roi_result.setText(f"""
            <b>ROI Calculation:</b><br>
            Profit/Loss: <span style="color: {color};">${profit:+.2f}</span><br>
            ROI: <span style="color: {color};">{roi:+.1f}%</span><br>
            <br>
            <small>Positive ROI = Profitable</small>
            """)
        else:
            self.roi_result.setText("Enter valid entry fees")

    def add_transaction(self):
        """Add a new transaction"""
        amount = self.amount_input.value()
        trans_type = self.transaction_type.currentText()
        notes = self.notes_input.text()

        # Update bankroll
        if trans_type in ["Deposit", "Contest Win"]:
            self.manager.data['current_bankroll'] += amount
        else:
            self.manager.data['current_bankroll'] -= abs(amount)

        # Add to history
        transaction = {
            'date': datetime.now().isoformat(),
            'type': trans_type,
            'amount': amount,
            'notes': notes,
            'balance': self.manager.data['current_bankroll']
        }

        self.manager.data['transactions'].append(transaction)
        self.manager.save_data()

        # Refresh displays
        self.refresh_data()
        self.refresh_history()

        # Clear inputs
        self.amount_input.setValue(0)
        self.notes_input.clear()

        QMessageBox.information(self, "Success", "Transaction added successfully")

    def refresh_history(self):
        """Refresh transaction history table"""
        transactions = self.manager.data.get('transactions', [])
        self.history_table.setRowCount(len(transactions))

        for i, trans in enumerate(reversed(transactions[-50:])):  # Show last 50
            date = datetime.fromisoformat(trans['date']).strftime('%Y-%m-%d %H:%M')
            self.history_table.setItem(i, 0, QTableWidgetItem(date))
            self.history_table.setItem(i, 1, QTableWidgetItem(trans['type']))

            amount_item = QTableWidgetItem(f"${trans['amount']:+.2f}")
            if trans['amount'] > 0:
                amount_item.setForeground(QColor(16, 185, 129))
            else:
                amount_item.setForeground(QColor(220, 38, 38))
            self.history_table.setItem(i, 2, amount_item)

            self.history_table.setItem(i, 3, QTableWidgetItem(trans.get('notes', '')))

    def save_settings(self):
        """Save risk settings"""
        self.manager.data['settings']['risk_tolerance'] = self.risk_combo.currentText()
        self.manager.data['settings']['max_daily_risk'] = self.max_daily_risk.value() / 100
        self.manager.data['settings']['kelly_multiplier'] = self.kelly_mult.value()

        self.manager.save_data()
        self.refresh_data()

        QMessageBox.information(self, "Success", "Settings saved successfully")

    def reset_bankroll(self):
        """Reset bankroll to starting amount"""
        reply = QMessageBox.question(
            self, "Confirm Reset",
            "Are you sure you want to reset your bankroll?\nThis will clear all history.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            starting = self.manager.data['starting_bankroll']
            self.manager.data['current_bankroll'] = starting
            self.manager.data['transactions'] = []
            self.manager.data['contest_history'] = []

            self.manager.save_data()
            self.refresh_data()
            self.refresh_history()

            QMessageBox.information(self, "Reset Complete", f"Bankroll reset to ${starting:.2f}")

    def refresh_data(self):
        """Refresh all displayed data"""
        # Update overview tab
        current = self.manager.data['current_bankroll']
        self.bankroll_label.setText(f"${current:,.2f}")

        daily_budget = self.manager._calculate_daily_budget(
            current,
            self.manager.data['settings']['risk_tolerance']
        )
        self.budget_label.setText(f"${daily_budget['total']:.2f}")


def update_clean_gui_with_bankroll(gui_class):
    """Add bankroll management to the clean GUI"""

    # Add to the create_analytics_tab method
    original_create_analytics = gui_class.create_analytics_tab

    def new_create_analytics_tab(self):
        """Enhanced analytics tab with bankroll management"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Add bankroll management widget
        self.bankroll_widget = BankrollManagementWidget(self)
        layout.addWidget(self.bankroll_widget)

        return widget

    gui_class.create_analytics_tab = new_create_analytics_tab

    # Also update the contest type dropdown to be clearer
    original_create_settings = gui_class.create_settings_tab

    def new_create_settings_tab(self):
        widget = original_create_settings(self)

        # Find and update contest type combo
        if hasattr(self, 'contest_type'):
            self.contest_type.clear()
            self.contest_type.addItems([
                "Cash - 50/50 (Top 50% win)",
                "Cash - Double Up (Top 45% win)",
                "Cash - Head to Head (1v1)",
                "GPP - Multi Entry (Tournament)",
                "GPP - Single Entry (Tournament, 1 lineup max)",
                "Showdown - Captain Mode"
            ])

        return widget

    gui_class.create_settings_tab = new_create_settings_tab
