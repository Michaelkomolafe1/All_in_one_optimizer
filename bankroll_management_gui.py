#!/usr/bin/env python3
"""
STANDALONE BANKROLL MANAGEMENT GUI
===================================
Separate application for bankroll management and stake sizing
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QLabel, QLineEdit, QComboBox,
                            QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit,
                            QGroupBox, QGridLayout, QSpinBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

# Add path for bankroll manager
sys.path.append('dfs_optimizer_v2')
from bankroll_manager import BankrollManager, RiskLevel, ContestInfo


class BankrollManagementGUI(QMainWindow):
    """Standalone bankroll management application"""
    
    def __init__(self):
        super().__init__()
        self.bankroll_manager = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        
        self.setWindowTitle("DFS Bankroll Management System")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("🏦 DFS BANKROLL MANAGEMENT SYSTEM")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tabs
        self.create_setup_tab()
        self.create_stake_calculator_tab()
        self.create_slate_analyzer_tab()
        self.create_simulation_tab()
        
    def create_setup_tab(self):
        """Create bankroll setup tab"""
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Bankroll setup group
        setup_group = QGroupBox("Bankroll Setup")
        setup_layout = QGridLayout(setup_group)
        
        # Current bankroll
        setup_layout.addWidget(QLabel("Current Bankroll ($):"), 0, 0)
        self.bankroll_input = QDoubleSpinBox()
        self.bankroll_input.setRange(10.0, 1000000.0)
        self.bankroll_input.setValue(1000.0)
        self.bankroll_input.setDecimals(2)
        setup_layout.addWidget(self.bankroll_input, 0, 1)
        
        # Risk level
        setup_layout.addWidget(QLabel("Risk Level:"), 1, 0)
        self.risk_combo = QComboBox()
        self.risk_combo.addItems(["Conservative", "Moderate", "Aggressive"])
        self.risk_combo.setCurrentText("Moderate")
        setup_layout.addWidget(self.risk_combo, 1, 1)
        
        # Initialize button
        init_button = QPushButton("Initialize Bankroll Manager")
        init_button.clicked.connect(self.initialize_bankroll_manager)
        setup_layout.addWidget(init_button, 2, 0, 1, 2)
        
        layout.addWidget(setup_group)
        
        # Status display
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(200)
        self.status_text.setPlainText("Enter your bankroll and risk level, then click Initialize.")
        layout.addWidget(self.status_text)
        
        self.tabs.addTab(tab, "Setup")
        
    def create_stake_calculator_tab(self):
        """Create stake calculator tab"""
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Contest input group
        contest_group = QGroupBox("Contest Information")
        contest_layout = QGridLayout(contest_group)
        
        # Contest details
        contest_layout.addWidget(QLabel("Contest Name:"), 0, 0)
        self.contest_name = QLineEdit("$5 Double Up")
        contest_layout.addWidget(self.contest_name, 0, 1)
        
        contest_layout.addWidget(QLabel("Entry Fee ($):"), 1, 0)
        self.entry_fee = QDoubleSpinBox()
        self.entry_fee.setRange(0.25, 10000.0)
        self.entry_fee.setValue(5.0)
        contest_layout.addWidget(self.entry_fee, 1, 1)
        
        contest_layout.addWidget(QLabel("Max Entries:"), 2, 0)
        self.max_entries = QSpinBox()
        self.max_entries.setRange(1, 150)
        self.max_entries.setValue(1)
        contest_layout.addWidget(self.max_entries, 2, 1)
        
        contest_layout.addWidget(QLabel("Contest Type:"), 3, 0)
        self.contest_type = QComboBox()
        self.contest_type.addItems(["cash", "gpp", "satellite"])
        contest_layout.addWidget(self.contest_type, 3, 1)
        
        contest_layout.addWidget(QLabel("Slate Size:"), 4, 0)
        self.slate_size = QComboBox()
        self.slate_size.addItems(["small", "medium", "large"])
        self.slate_size.setCurrentText("medium")
        contest_layout.addWidget(self.slate_size, 4, 1)
        
        contest_layout.addWidget(QLabel("Strategy:"), 5, 0)
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "optimized_correlation_value",
            "optimized_pitcher_dominance", 
            "optimized_tournament_winner_gpp",
            "projection_monster",
            "tournament_winner_gpp"
        ])
        contest_layout.addWidget(self.strategy_combo, 5, 1)
        
        # Calculate button
        calc_button = QPushButton("Calculate Optimal Stake")
        calc_button.clicked.connect(self.calculate_stake)
        contest_layout.addWidget(calc_button, 6, 0, 1, 2)
        
        layout.addWidget(contest_group)
        
        # Results display
        self.stake_results = QTextEdit()
        self.stake_results.setMaximumHeight(300)
        layout.addWidget(self.stake_results)
        
        self.tabs.addTab(tab, "Stake Calculator")
        
    def create_slate_analyzer_tab(self):
        """Create slate analyzer tab"""
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        instructions = QLabel("Add contests to analyze the entire slate:")
        layout.addWidget(instructions)
        
        # Contest table
        self.contest_table = QTableWidget()
        self.contest_table.setColumnCount(6)
        self.contest_table.setHorizontalHeaderLabels([
            "Contest", "Entry Fee", "Type", "Slate Size", "Expected Profit", "Recommended"
        ])
        layout.addWidget(self.contest_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_contest_btn = QPushButton("Add Sample Contests")
        add_contest_btn.clicked.connect(self.add_sample_contests)
        button_layout.addWidget(add_contest_btn)
        
        analyze_btn = QPushButton("Analyze Slate")
        analyze_btn.clicked.connect(self.analyze_slate)
        button_layout.addWidget(analyze_btn)
        
        clear_btn = QPushButton("Clear Contests")
        clear_btn.clicked.connect(self.clear_contests)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        
        self.tabs.addTab(tab, "Slate Analyzer")
        
    def create_simulation_tab(self):
        """Create bankroll simulation tab"""
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Simulation parameters
        sim_group = QGroupBox("Simulation Parameters")
        sim_layout = QGridLayout(sim_group)
        
        sim_layout.addWidget(QLabel("Daily Stake ($):"), 0, 0)
        self.daily_stake = QDoubleSpinBox()
        self.daily_stake.setRange(1.0, 10000.0)
        self.daily_stake.setValue(50.0)
        sim_layout.addWidget(self.daily_stake, 0, 1)
        
        sim_layout.addWidget(QLabel("Simulation Days:"), 1, 0)
        self.sim_days = QSpinBox()
        self.sim_days.setRange(1, 365)
        self.sim_days.setValue(30)
        sim_layout.addWidget(self.sim_days, 1, 1)
        
        sim_layout.addWidget(QLabel("Strategy:"), 2, 0)
        self.sim_strategy = QComboBox()
        self.sim_strategy.addItems([
            "optimized_correlation_value",
            "optimized_pitcher_dominance", 
            "optimized_tournament_winner_gpp"
        ])
        sim_layout.addWidget(self.sim_strategy, 2, 1)
        
        simulate_btn = QPushButton("Run Simulation")
        simulate_btn.clicked.connect(self.run_simulation)
        sim_layout.addWidget(simulate_btn, 3, 0, 1, 2)
        
        layout.addWidget(sim_group)
        
        # Simulation results
        self.sim_results = QTextEdit()
        layout.addWidget(self.sim_results)
        
        self.tabs.addTab(tab, "Simulation")
        
    def initialize_bankroll_manager(self):
        """Initialize the bankroll manager"""
        
        bankroll = self.bankroll_input.value()
        risk_text = self.risk_combo.currentText().lower()
        risk_level = RiskLevel(risk_text)
        
        self.bankroll_manager = BankrollManager(bankroll, risk_level)
        
        # Display status
        summary = self.bankroll_manager.get_bankroll_summary()
        
        status_text = f"""
✅ BANKROLL MANAGER INITIALIZED

💰 Bankroll Status:
   Current Bankroll: ${summary['current_bankroll']:,.2f}
   Risk Level: {summary['risk_level'].title()}
   Risk Status: {summary['risk_status']}

📊 Recommendations:
   Max Single Stake: ${summary['max_single_stake']:.2f} (5% of bankroll)
   Daily Limit: ${summary['recommended_daily_limit']:.2f} (20% of bankroll)

🎯 Strategy Performance Data Loaded:
   • Optimized Correlation Value: 57.4% win rate, 14.77% avg ROI
   • Optimized Pitcher Dominance: 56.5% win rate, 12.90% avg ROI  
   • Optimized Tournament Winner: 59.3% win rate, 18.52% avg ROI
   • Projection Monster: 45.0% win rate, 116.94% avg ROI
   • Tournament Winner GPP: 42.5% win rate, 90.14% avg ROI

Ready to calculate optimal stakes!
        """
        
        self.status_text.setPlainText(status_text)
        
    def calculate_stake(self):
        """Calculate optimal stake for entered contest"""
        
        if not self.bankroll_manager:
            self.stake_results.setPlainText("❌ Please initialize bankroll manager first!")
            return
        
        # Create contest info
        contest = ContestInfo(
            name=self.contest_name.text(),
            entry_fee=self.entry_fee.value(),
            max_entries=self.max_entries.value(),
            total_entries=1000,  # Default
            prize_pool=1000 * self.entry_fee.value() * 0.9,  # Estimate
            contest_type=self.contest_type.currentText(),
            slate_size=self.slate_size.currentText()
        )
        
        strategy = self.strategy_combo.currentText()
        
        # Calculate stake
        stake_info = self.bankroll_manager.get_optimal_stake(contest, strategy)
        
        # Display results
        results_text = f"""
🎯 OPTIMAL STAKE CALCULATION

📊 Contest: {contest.name}
   Entry Fee: ${contest.entry_fee:.2f}
   Contest Type: {contest.contest_type.title()}
   Slate Size: {contest.slate_size.title()}
   Strategy: {strategy}

💰 RECOMMENDATIONS:
   Recommended Entries: {stake_info['recommended_entries']}
   Total Stake: ${stake_info['actual_stake']:.2f}
   Bankroll Percentage: {stake_info['bankroll_percentage']:.1f}%

📈 EXPECTED PERFORMANCE:
   Win Rate: {stake_info['win_rate']:.1f}%
   Average ROI: {stake_info['avg_roi']:.1f}%
   Expected Return: ${stake_info['expected_return']:.2f}
   Expected Profit: ${stake_info['expected_profit']:.2f}

🔬 KELLY ANALYSIS:
   Kelly Fraction: {stake_info['kelly_fraction']:.3f}
   Risk-Adjusted: {stake_info['adjusted_fraction']:.3f}
   Risk Level: {stake_info['risk_level'].title()}

{'✅ RECOMMENDED' if stake_info['expected_profit'] > 0 else '⚠️ NOT RECOMMENDED'}
        """
        
        self.stake_results.setPlainText(results_text)
        
    def add_sample_contests(self):
        """Add sample contests to the table"""
        
        from bankroll_manager import SAMPLE_CONTESTS
        
        self.contest_table.setRowCount(len(SAMPLE_CONTESTS))
        
        for i, contest in enumerate(SAMPLE_CONTESTS):
            self.contest_table.setItem(i, 0, QTableWidgetItem(contest.name))
            self.contest_table.setItem(i, 1, QTableWidgetItem(f"${contest.entry_fee:.2f}"))
            self.contest_table.setItem(i, 2, QTableWidgetItem(contest.contest_type))
            self.contest_table.setItem(i, 3, QTableWidgetItem(contest.slate_size))
            self.contest_table.setItem(i, 4, QTableWidgetItem("Click Analyze"))
            self.contest_table.setItem(i, 5, QTableWidgetItem(""))
            
    def analyze_slate(self):
        """Analyze all contests in the slate"""
        
        if not self.bankroll_manager:
            return
        
        from bankroll_manager import SAMPLE_CONTESTS
        strategy = "optimized_correlation_value"  # Default
        
        opportunities = self.bankroll_manager.analyze_slate_opportunities(
            SAMPLE_CONTESTS, strategy
        )
        
        # Update table with results
        for i, opp in enumerate(opportunities):
            if i < self.contest_table.rowCount():
                self.contest_table.setItem(i, 4, QTableWidgetItem(f"${opp['expected_profit']:.2f}"))
                recommendation = "✅ YES" if opp['expected_profit'] > 5 else "⚠️ MAYBE" if opp['expected_profit'] > 0 else "❌ NO"
                self.contest_table.setItem(i, 5, QTableWidgetItem(recommendation))
        
    def clear_contests(self):
        """Clear the contest table"""
        self.contest_table.setRowCount(0)
        
    def run_simulation(self):
        """Run bankroll simulation"""
        
        if not self.bankroll_manager:
            self.sim_results.setPlainText("❌ Please initialize bankroll manager first!")
            return
        
        daily_stake = self.daily_stake.value()
        days = self.sim_days.value()
        strategy = self.sim_strategy.currentText()
        
        # Run simulation
        sim_result = self.bankroll_manager.simulate_bankroll_growth(
            [daily_stake], strategy, days
        )
        
        if 'error' in sim_result:
            self.sim_results.setPlainText(f"❌ {sim_result['error']}")
            return
        
        # Display results
        results_text = f"""
📈 BANKROLL SIMULATION RESULTS

🎯 Parameters:
   Strategy: {strategy}
   Daily Stake: ${daily_stake:.2f}
   Simulation Days: {days}

💰 Results:
   Starting Bankroll: ${sim_result['initial_bankroll']:,.2f}
   Ending Bankroll: ${sim_result['final_bankroll']:,.2f}
   Total Profit: ${sim_result['total_profit']:,.2f}
   Growth Rate: {sim_result['growth_rate']:.1f}%

📊 Performance:
   {'✅ PROFITABLE' if sim_result['total_profit'] > 0 else '❌ LOSING'}
   {'🚀 EXCELLENT GROWTH' if sim_result['growth_rate'] > 20 else '📈 GOOD GROWTH' if sim_result['growth_rate'] > 0 else '📉 NEEDS IMPROVEMENT'}

⚠️ Note: This is a simulation based on historical performance.
Real results may vary due to variance and changing conditions.
        """
        
        self.sim_results.setPlainText(results_text)


def main():
    """Run the standalone bankroll management GUI"""
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("DFS Bankroll Manager")
    app.setApplicationVersion("1.0")
    
    # Create and show the main window
    window = BankrollManagementGUI()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
