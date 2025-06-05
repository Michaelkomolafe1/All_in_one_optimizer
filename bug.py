#!/usr/bin/env python3
"""
CONTEST RECOMMENDATION ENGINE
=============================
Tells you exactly which contests to enter based on your bankroll
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
import os
from datetime import datetime


class ContestRecommendationWidget(QWidget):
    """Widget that recommends specific contests based on bankroll"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_gui = parent
        self.load_settings()
        self.setup_ui()

    def load_settings(self):
        """Load user settings and bankroll data"""
        # Load bankroll data
        self.bankroll_data = {'current': 1000}
        if os.path.exists('dfs_analytics_data.json'):
            try:
                with open('dfs_analytics_data.json', 'r') as f:
                    data = json.load(f)
                    self.bankroll_data = data.get('bankroll', {'current': 1000})
            except:
                pass

        # Common DraftKings contest types with typical buy-ins
        self.contest_types = {
            'cash_games': {
                'name': 'Cash Games (50/50, Double-Ups)',
                'risk': 'Low',
                'buy_ins': [1, 3, 5, 10, 20, 25, 50, 100, 200, 500, 1000],
                'bankroll_pct': (0.05, 0.10),  # 5-10% per contest
                'daily_limit_pct': 0.25,  # Max 25% of bankroll in cash games per day
                'description': 'Win money if you finish in top 50%. Best for consistent profits.'
            },
            'single_entry': {
                'name': 'Single Entry Tournaments',
                'risk': 'Medium',
                'buy_ins': [1, 3, 5, 10, 20, 25, 50, 100, 200],
                'bankroll_pct': (0.02, 0.05),  # 2-5% per contest
                'daily_limit_pct': 0.15,  # Max 15% of bankroll
                'description': 'Everyone limited to 1 entry. More balanced competition.'
            },
            'small_gpp': {
                'name': 'Small GPPs (< 10K entries)',
                'risk': 'Medium-High',
                'buy_ins': [1, 3, 5, 10, 20, 25, 50],
                'bankroll_pct': (0.01, 0.03),  # 1-3% per contest
                'daily_limit_pct': 0.20,  # Max 20% of bankroll
                'description': 'Smaller tournaments with better odds than large GPPs.'
            },
            'large_gpp': {
                'name': 'Large GPPs (Millionaire Maker, etc)',
                'risk': 'High',
                'buy_ins': [3, 5, 10, 20, 25, 50, 100, 200],
                'bankroll_pct': (0.005, 0.01),  # 0.5-1% per contest
                'daily_limit_pct': 0.10,  # Max 10% of bankroll
                'description': 'Massive tournaments with life-changing prizes but low odds.'
            },
            'satellites': {
                'name': 'Satellites & Qualifiers',
                'risk': 'Medium',
                'buy_ins': [1, 3, 5, 10, 20],
                'bankroll_pct': (0.01, 0.02),  # 1-2% per contest
                'daily_limit_pct': 0.05,  # Max 5% of bankroll
                'description': 'Win tickets to bigger contests.'
            },
            'showdown': {
                'name': 'Showdown (Single Game)',
                'risk': 'Medium',
                'buy_ins': [1, 3, 5, 10, 20, 25, 50, 100],
                'bankroll_pct': (0.02, 0.04),  # 2-4% per contest
                'daily_limit_pct': 0.15,  # Max 15% of bankroll
                'description': 'Captain mode contests for single games.'
            }
        }

    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("🎯 Contest Recommendations")
        header.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            padding: 10px;
            background-color: #1e40af;
            color: white;
            border-radius: 8px;
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Bankroll info card
        bankroll_card = self.create_card("💰 Your Bankroll")
        bankroll_layout = QHBoxLayout(bankroll_card)

        self.bankroll_label = QLabel(f"Current Bankroll: ${self.bankroll_data['current']:,.2f}")
        self.bankroll_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        bankroll_layout.addWidget(self.bankroll_label)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_bankroll)
        bankroll_layout.addWidget(refresh_btn)

        layout.addWidget(bankroll_card)

        # Risk tolerance selector
        risk_card = self.create_card("⚖️ Risk Tolerance")
        risk_layout = QVBoxLayout(risk_card)

        self.risk_combo = QComboBox()
        self.risk_combo.addItems([
            "Conservative (Mostly Cash Games)",
            "Balanced (Mix of Cash and GPPs)",
            "Aggressive (Mostly GPPs)",
            "Custom"
        ])
        self.risk_combo.currentIndexChanged.connect(self.update_recommendations)
        risk_layout.addWidget(self.risk_combo)

        layout.addWidget(risk_card)

        # Daily budget card
        budget_card = self.create_card("💵 Daily Budget")
        budget_layout = QFormLayout(budget_card)

        self.daily_budget_spin = QDoubleSpinBox()
        self.daily_budget_spin.setRange(0, self.bankroll_data['current'] * 0.5)
        self.daily_budget_spin.setPrefix("$")
        self.daily_budget_spin.setValue(self.bankroll_data['current'] * 0.15)  # Default 15%
        self.daily_budget_spin.valueChanged.connect(self.update_recommendations)
        budget_layout.addRow("Max Daily Spend:", self.daily_budget_spin)

        self.budget_pct_label = QLabel()
        self.update_budget_percentage()
        budget_layout.addRow("% of Bankroll:", self.budget_pct_label)

        layout.addWidget(budget_card)

        # Recommendations area
        self.recommendations_scroll = QScrollArea()
        self.recommendations_widget = QWidget()
        self.recommendations_layout = QVBoxLayout(self.recommendations_widget)
        self.recommendations_scroll.setWidget(self.recommendations_widget)
        self.recommendations_scroll.setWidgetResizable(True)
        self.recommendations_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f3f4f6;
            }
        """)

        layout.addWidget(QLabel("📋 Recommended Contest Lineup:"))
        layout.addWidget(self.recommendations_scroll, 1)

        # Generate button
        generate_btn = QPushButton("🎯 Generate Today's Contest Lineup")
        generate_btn.setMinimumHeight(50)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        generate_btn.clicked.connect(self.generate_full_recommendations)
        layout.addWidget(generate_btn)

        # Initial recommendations
        self.update_recommendations()

    def create_card(self, title):
        """Create a card widget"""
        card = QGroupBox(title)
        card.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 10px;
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

    def refresh_bankroll(self):
        """Refresh bankroll from saved data"""
        self.load_settings()
        self.bankroll_label.setText(f"Current Bankroll: ${self.bankroll_data['current']:,.2f}")
        self.daily_budget_spin.setMaximum(self.bankroll_data['current'] * 0.5)
        self.update_recommendations()

    def update_budget_percentage(self):
        """Update budget percentage label"""
        if self.bankroll_data['current'] > 0:
            pct = (self.daily_budget_spin.value() / self.bankroll_data['current']) * 100
            color = '#10b981' if pct <= 20 else '#f59e0b' if pct <= 30 else '#ef4444'
            self.budget_pct_label.setText(f"<span style='color: {color}; font-weight: bold;'>{pct:.1f}%</span>")

    def get_risk_allocation(self):
        """Get contest allocation based on risk tolerance"""
        risk_profiles = {
            0: {  # Conservative
                'cash_games': 0.70,
                'single_entry': 0.20,
                'small_gpp': 0.10,
                'large_gpp': 0.00,
                'satellites': 0.00,
                'showdown': 0.00
            },
            1: {  # Balanced
                'cash_games': 0.40,
                'single_entry': 0.25,
                'small_gpp': 0.20,
                'large_gpp': 0.05,
                'satellites': 0.05,
                'showdown': 0.05
            },
            2: {  # Aggressive
                'cash_games': 0.20,
                'single_entry': 0.20,
                'small_gpp': 0.30,
                'large_gpp': 0.20,
                'satellites': 0.05,
                'showdown': 0.05
            },
            3: {  # Custom (default balanced for now)
                'cash_games': 0.40,
                'single_entry': 0.25,
                'small_gpp': 0.20,
                'large_gpp': 0.05,
                'satellites': 0.05,
                'showdown': 0.05
            }
        }

        return risk_profiles[self.risk_combo.currentIndex()]

    def update_recommendations(self):
        """Update contest recommendations"""
        # Clear existing recommendations
        for i in reversed(range(self.recommendations_layout.count())):
            self.recommendations_layout.itemAt(i).widget().setParent(None)

        daily_budget = self.daily_budget_spin.value()
        self.update_budget_percentage()

        if daily_budget <= 0:
            no_budget_label = QLabel("Set a daily budget to see recommendations")
            no_budget_label.setAlignment(Qt.AlignCenter)
            no_budget_label.setStyleSheet("color: #6b7280; padding: 20px;")
            self.recommendations_layout.addWidget(no_budget_label)
            return

        allocations = self.get_risk_allocation()
        total_allocated = 0

        for contest_type, allocation_pct in allocations.items():
            if allocation_pct > 0:
                contest_budget = daily_budget * allocation_pct
                if contest_budget >= 1:  # Minimum $1 to show
                    self.add_contest_recommendation(
                        contest_type,
                        contest_budget,
                        total_allocated
                    )
                    total_allocated += contest_budget

        # Summary card
        summary_card = self.create_card("📊 Daily Summary")
        summary_layout = QVBoxLayout(summary_card)

        summary_text = f"""
        <b>Total Allocated:</b> ${total_allocated:.2f}<br>
        <b>Remaining Budget:</b> ${daily_budget - total_allocated:.2f}<br>
        <b>Number of Contests:</b> {self.recommendations_layout.count() - 1}<br>
        <b>Risk Profile:</b> {self.risk_combo.currentText()}
        """

        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet("padding: 10px;")
        summary_layout.addWidget(summary_label)

        self.recommendations_layout.addWidget(summary_card)
        self.recommendations_layout.addStretch()

    def add_contest_recommendation(self, contest_type, budget, running_total):
        """Add a specific contest recommendation"""
        contest_info = self.contest_types[contest_type]

        # Create recommendation card
        card = QGroupBox(contest_info['name'])
        card.setStyleSheet("""
            QGroupBox {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                margin: 5px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #1f2937;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(card)

        # Risk indicator
        risk_colors = {'Low': '#10b981', 'Medium': '#f59e0b', 'Medium-High': '#f97316', 'High': '#ef4444'}
        risk_label = QLabel(f"Risk: {contest_info['risk']}")
        risk_label.setStyleSheet(f"color: {risk_colors.get(contest_info['risk'], '#000')}; font-weight: bold;")
        layout.addWidget(risk_label)

        # Budget allocation
        budget_label = QLabel(f"Budget: ${budget:.2f}")
        budget_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(budget_label)

        # Find best contest matches
        recommended_contests = self.find_best_contests(contest_type, budget)

        if recommended_contests:
            contests_label = QLabel("<b>Recommended Entries:</b>")
            layout.addWidget(contests_label)

            for contest in recommended_contests:
                contest_text = f"• ${contest['buy_in']} entry "
                if contest['count'] > 1:
                    contest_text += f"(enter {contest['count']}x = ${contest['total']:.2f})"
                else:
                    contest_text += f"(${contest['total']:.2f})"

                contest_item = QLabel(contest_text)
                contest_item.setStyleSheet("margin-left: 10px; color: #374151;")
                layout.addWidget(contest_item)

        # Description
        desc_label = QLabel(contest_info['description'])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #6b7280; font-size: 12px; margin-top: 5px;")
        layout.addWidget(desc_label)

        self.recommendations_layout.addWidget(card)

    def find_best_contests(self, contest_type, budget):
        """Find the best contest entries for a given budget"""
        contest_info = self.contest_types[contest_type]
        buy_ins = contest_info['buy_ins']
        min_pct, max_pct = contest_info['bankroll_pct']

        recommendations = []
        remaining = budget

        # First, try to find single entries that fit
        max_single_entry = self.bankroll_data['current'] * max_pct

        for buy_in in reversed(buy_ins):  # Start with highest buy-ins
            if buy_in <= remaining and buy_in <= max_single_entry:
                # See how many we can enter
                max_entries = int(remaining / buy_in)

                # Limit based on bankroll percentage
                max_allowed = int(max_single_entry / buy_in)
                entries = min(max_entries, max_allowed, 3)  # Cap at 3 entries per buy-in level

                if entries > 0:
                    recommendations.append({
                        'buy_in': buy_in,
                        'count': entries,
                        'total': buy_in * entries
                    })
                    remaining -= buy_in * entries

            if remaining < min(buy_ins):
                break

        return recommendations

    def generate_full_recommendations(self):
        """Generate detailed contest recommendations"""
        # Create a detailed report
        report = QDialog(self)
        report.setWindowTitle("📋 Today's DFS Contest Plan")
        report.setMinimumSize(600, 700)

        layout = QVBoxLayout(report)

        # Header
        header = QLabel(f"🎯 Optimal Contest Selection for ${self.bankroll_data['current']:,.2f} Bankroll")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            padding: 15px;
            background-color: #1e40af;
            color: white;
            border-radius: 8px;
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Report content
        report_text = QTextEdit()
        report_text.setReadOnly(True)

        daily_budget = self.daily_budget_spin.value()
        allocations = self.get_risk_allocation()

        html_content = f"""
        <h2>Daily Contest Plan - {datetime.now().strftime('%Y-%m-%d')}</h2>

        <h3>📊 Overview</h3>
        <ul>
            <li><b>Current Bankroll:</b> ${self.bankroll_data['current']:,.2f}</li>
            <li><b>Daily Budget:</b> ${daily_budget:.2f} ({(daily_budget / self.bankroll_data['current'] * 100):.1f}% of bankroll)</li>
            <li><b>Risk Profile:</b> {self.risk_combo.currentText()}</li>
        </ul>

        <h3>🎮 Specific Contest Recommendations</h3>
        """

        total_contests = 0
        total_spent = 0

        for contest_type, allocation_pct in allocations.items():
            if allocation_pct > 0:
                contest_budget = daily_budget * allocation_pct
                if contest_budget >= 1:
                    contest_info = self.contest_types[contest_type]
                    recommended = self.find_best_contests(contest_type, contest_budget)

                    if recommended:
                        html_content += f"<h4>{contest_info['name']}</h4>"
                        html_content += f"<p><i>{contest_info['description']}</i></p>"
                        html_content += "<ul>"

                        for rec in recommended:
                            total_contests += rec['count']
                            total_spent += rec['total']

                            html_content += f"<li><b>${rec['buy_in']} buy-in:</b> Enter {rec['count']} contest"
                            if rec['count'] > 1:
                                html_content += "s"
                            html_content += f" (${rec['total']:.2f} total)</li>"

                        html_content += "</ul>"

        html_content += f"""
        <h3>💰 Summary</h3>
        <ul>
            <li><b>Total Contests:</b> {total_contests}</li>
            <li><b>Total Investment:</b> ${total_spent:.2f}</li>
            <li><b>Remaining Budget:</b> ${daily_budget - total_spent:.2f}</li>
        </ul>

        <h3>📈 Expected Outcomes</h3>
        <ul>
            <li><b>Cash Games:</b> Expect to win 55-60% (profit: ${total_spent * allocations.get('cash_games', 0) * 0.1:.2f})</li>
            <li><b>GPPs:</b> High variance, but potential for big scores</li>
            <li><b>Break-even point:</b> Win {(1 / (1 + 0.1)):.1%} of contests</li>
        </ul>

        <h3>⚠️ Important Reminders</h3>
        <ul>
            <li>Never exceed your daily budget</li>
            <li>Track all results in the Contest History tab</li>
            <li>Adjust strategy based on performance</li>
            <li>Consider late-swap opportunities</li>
        </ul>
        """

        report_text.setHtml(html_content)
        layout.addWidget(report_text)

        # Action buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Save Plan")
        save_btn.clicked.connect(lambda: self.save_plan(html_content))
        button_layout.addWidget(save_btn)

        copy_btn = QPushButton("📋 Copy Summary")
        copy_btn.clicked.connect(lambda: self.copy_summary(total_contests, total_spent))
        button_layout.addWidget(copy_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(report.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        report.exec_()

    def save_plan(self, content):
        """Save the contest plan"""
        filename = f"contest_plan_{datetime.now().strftime('%Y%m%d')}.html"
        with open(filename, 'w') as f:
            f.write(f"<html><body>{content}</body></html>")
        QMessageBox.information(self, "Saved", f"Contest plan saved to {filename}")

    def copy_summary(self, contests, spent):
        """Copy summary to clipboard"""
        summary = f"DFS Plan: {contests} contests, ${spent:.2f} total"
        QApplication.clipboard().setText(summary)
        QMessageBox.information(self, "Copied", "Summary copied to clipboard!")


def integrate_contest_recommendations():
    """Add contest recommendations to the main GUI"""

    print("🔧 Adding contest recommendations to GUI...")

    # Update enhanced_dfs_gui.py
    with open('enhanced_dfs_gui.py', 'r') as f:
        content = f.read()

    # Add import
    import_location = content.find('from functional_analytics_widget import')
    if import_location > 0:
        end_line = content.find('\n', import_location)
        new_import = '''
try:
    from contest_recommendation_engine import ContestRecommendationWidget
    CONTEST_RECOMMENDATIONS_AVAILABLE = True
except ImportError:
    CONTEST_RECOMMENDATIONS_AVAILABLE = False
'''
        content = content[:end_line] + new_import + content[end_line:]

    # Add new tab in create_optimize_tab
    tab_location = content.find('layout.addWidget(self.tab_widget)')
    if tab_location > 0:
        # Find where tabs are added
        analytics_tab = content.find('self.tab_widget.addTab(self.analytics_widget')
        if analytics_tab > 0:
            end_line = content.find('\n', analytics_tab)
            new_tab = '''

        # Add contest recommendations tab
        if CONTEST_RECOMMENDATIONS_AVAILABLE:
            self.contest_widget = ContestRecommendationWidget(self)
            self.tab_widget.addTab(self.contest_widget, "🎯 Contest Selection")
'''
            content = content[:end_line] + new_tab + content[end_line:]

    with open('enhanced_dfs_gui.py', 'w') as f:
        f.write(content)

    print("✅ Contest recommendations integrated!")


if __name__ == "__main__":
    # Create the widget file
    print("🎯 Creating Contest Recommendation Engine...")

    # Also integrate it
    integrate_contest_recommendations()

    print("\n✅ Contest Recommendation Engine Created!")
    print("\nWhat it does:")
    print("1. 🎯 Recommends SPECIFIC contests based on your bankroll")
    print("2. 💰 Tells you exact buy-in amounts and how many to enter")
    print("3. ⚖️ Adjusts based on your risk tolerance")
    print("4. 📊 Provides expected outcomes for each contest type")
    print("5. 📋 Generates a complete daily contest plan")
    print("\nExample recommendations:")
    print("- With $1000 bankroll: 'Enter 2x $20 cash games, 3x $5 GPPs, 1x $10 single-entry'")
    print("- With $5000 bankroll: 'Enter 1x $100 cash, 2x $50 cash, 5x $20 GPPs'")