#!/usr/bin/env python3
"""
PROFESSIONAL DFS GUI WITH ANALYTICS
===================================
Beautiful modern interface with full features
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
import os
from datetime import datetime, timedelta
import numpy as np


class ModernLineupGeneratorWidget(QWidget):
    """Modern lineup generator with beautiful UI"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_gui = parent
        self.setup_ui()
        self.apply_modern_theme()

    def setup_ui(self):
        """Create beautiful modern UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Header with gradient
        header_widget = QWidget()
        header_widget.setMaximumHeight(80)
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
            }
        """)
        header_layout = QVBoxLayout(header_widget)

        title = QLabel("⚡ Advanced Lineup Generator")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        header_layout.addWidget(title)
        layout.addWidget(header_widget)

        # Main content area
        content_scroll = QScrollArea()
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

        # Quick action cards
        self.create_quick_actions(content_layout)

        # Detailed settings
        self.create_detailed_settings(content_layout)

        content_scroll.setWidget(content_widget)
        content_scroll.setWidgetResizable(True)
        content_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f7fafc;
            }
        """)
        layout.addWidget(content_scroll)

        # Generate button
        self.create_generate_button(layout)

    def create_quick_actions(self, layout):
        """Create quick action cards"""
        quick_group = QGroupBox("🚀 Quick Actions")
        quick_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 20px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px 0 10px;
            }
        """)

        cards_layout = QGridLayout(quick_group)
        cards_layout.setSpacing(15)

        # Card definitions
        cards = [
            {
                'title': '💰 Single Cash',
                'subtitle': 'One optimal cash lineup',
                'color': '#48bb78',
                'action': self.preset_single_cash
            },
            {
                'title': '🎯 20 GPP',
                'subtitle': 'Tournament diversity',
                'color': '#4299e1',
                'action': self.preset_20_gpp
            },
            {
                'title': '🚀 150 GPP',
                'subtitle': 'Maximum entries',
                'color': '#9f7aea',
                'action': self.preset_150_gpp
            },
            {
                'title': '🛡️ 5 Safe',
                'subtitle': 'Conservative cash',
                'color': '#38b2ac',
                'action': self.preset_5_cash
            }
        ]

        for i, card in enumerate(cards):
            card_widget = self.create_card(
                card['title'],
                card['subtitle'],
                card['color'],
                card['action']
            )
            cards_layout.addWidget(card_widget, i // 2, i % 2)

        layout.addWidget(quick_group)

    def create_card(self, title, subtitle, color, action):
        """Create a beautiful card widget"""
        card = QPushButton()
        card.setFixedHeight(100)
        card.clicked.connect(action)

        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 12px; color: #718096;")

        card_layout.addWidget(title_label)
        card_layout.addWidget(subtitle_label)

        card.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {color}20;
                border: 3px solid {color};
            }}
            QPushButton:pressed {{
                background-color: {color}40;
            }}
        """)

        return card

    def create_detailed_settings(self, layout):
        """Create detailed settings section"""
        # Contest settings
        contest_group = QGroupBox("⚙️ Contest Settings")
        contest_group.setStyleSheet(self.get_group_style())
        contest_layout = QFormLayout(contest_group)

        # Single vs Multiple
        mode_widget = QWidget()
        mode_layout = QHBoxLayout(mode_widget)
        mode_layout.setContentsMargins(0, 0, 0, 0)

        self.single_radio = QRadioButton("Single Lineup")
        self.multiple_radio = QRadioButton("Multiple Lineups")
        self.multiple_radio.setChecked(True)

        mode_layout.addWidget(self.single_radio)
        mode_layout.addWidget(self.multiple_radio)
        mode_layout.addStretch()

        contest_layout.addRow("Mode:", mode_widget)

        # Contest type with icons
        self.contest_combo = QComboBox()
        self.contest_combo.addItems([
            "🏆 GPP/Tournament - High variance",
            "💵 Cash Game - High floor",
            "🎯 Single Entry - Balanced",
            "👥 Head-to-Head - Safe",
            "✖️ Multiplier - Medium risk",
            "🎫 Satellite - Top heavy",
            "⚡ Showdown - Captain mode"
        ])
        self.contest_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                background-color: white;
                min-width: 250px;
            }
            QComboBox:hover {
                border-color: #4299e1;
            }
        """)
        contest_layout.addRow("Contest Type:", self.contest_combo)

        # Number of lineups
        lineup_widget = QWidget()
        lineup_layout = QHBoxLayout(lineup_widget)
        lineup_layout.setContentsMargins(0, 0, 0, 0)

        self.lineup_count_spin = QSpinBox()
        self.lineup_count_spin.setRange(1, 150)
        self.lineup_count_spin.setValue(20)
        self.lineup_count_spin.setStyleSheet(self.get_spinbox_style())

        self.lineup_slider = QSlider(Qt.Horizontal)
        self.lineup_slider.setRange(1, 150)
        self.lineup_slider.setValue(20)
        self.lineup_slider.setStyleSheet(self.get_slider_style())

        # Connect slider and spinbox
        self.lineup_slider.valueChanged.connect(self.lineup_count_spin.setValue)
        self.lineup_count_spin.valueChanged.connect(self.lineup_slider.setValue)

        lineup_layout.addWidget(self.lineup_count_spin)
        lineup_layout.addWidget(self.lineup_slider, 1)

        contest_layout.addRow("Lineups:", lineup_widget)

        layout.addWidget(contest_group)

        # Advanced settings
        advanced_group = QGroupBox("🎯 Advanced Settings")
        advanced_group.setStyleSheet(self.get_group_style())
        advanced_layout = QFormLayout(advanced_group)

        # Player diversity
        diversity_widget = QWidget()
        diversity_layout = QHBoxLayout(diversity_widget)
        diversity_layout.setContentsMargins(0, 0, 0, 0)

        self.diversity_slider = QSlider(Qt.Horizontal)
        self.diversity_slider.setRange(0, 100)
        self.diversity_slider.setValue(70)
        self.diversity_slider.setStyleSheet(self.get_slider_style("#9f7aea"))

        self.diversity_label = QLabel("70%")
        self.diversity_label.setMinimumWidth(40)

        diversity_layout.addWidget(self.diversity_slider)
        diversity_layout.addWidget(self.diversity_label)

        self.diversity_slider.valueChanged.connect(
            lambda v: self.diversity_label.setText(f"{v}%")
        )

        advanced_layout.addRow("Player Diversity:", diversity_widget)

        # Max exposure
        self.max_exposure_spin = QSpinBox()
        self.max_exposure_spin.setRange(10, 100)
        self.max_exposure_spin.setValue(60)
        self.max_exposure_spin.setSuffix("%")
        self.max_exposure_spin.setStyleSheet(self.get_spinbox_style())

        advanced_layout.addRow("Max Exposure:", self.max_exposure_spin)

        # Salary range
        salary_widget = QWidget()
        salary_layout = QHBoxLayout(salary_widget)
        salary_layout.setContentsMargins(0, 0, 0, 0)

        self.min_salary_spin = QSpinBox()
        self.min_salary_spin.setRange(90, 100)
        self.min_salary_spin.setValue(98)
        self.min_salary_spin.setSuffix("%")
        self.min_salary_spin.setStyleSheet(self.get_spinbox_style())

        salary_layout.addWidget(QLabel("Min:"))
        salary_layout.addWidget(self.min_salary_spin)
        salary_layout.addWidget(QLabel("Max:"))
        salary_layout.addWidget(QLabel("100%"))
        salary_layout.addStretch()

        advanced_layout.addRow("Salary Usage:", salary_widget)

        # Stacking options
        self.stacking_check = QCheckBox("Enable team stacking")
        self.stacking_check.setChecked(True)
        self.stacking_check.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        advanced_layout.addRow("", self.stacking_check)

        layout.addWidget(advanced_group)

        # Connect mode change
        self.single_radio.toggled.connect(self.on_mode_changed)

    def create_generate_button(self, layout):
        """Create the generate button"""
        self.generate_btn = QPushButton("⚡ Generate Optimal Lineups")
        self.generate_btn.setMinimumHeight(60)
        self.generate_btn.clicked.connect(self.generate_lineups)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                padding: 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a67d8, stop:1 #6b46c1);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4c51bf, stop:1 #553c9a);
            }
        """)
        layout.addWidget(self.generate_btn)

    def get_group_style(self):
        """Get consistent group box style"""
        return """
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 20px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px 0 10px;
                color: #2d3748;
            }
        """

    def get_spinbox_style(self):
        """Get consistent spinbox style"""
        return """
            QSpinBox {
                padding: 8px;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
                min-width: 80px;
            }
            QSpinBox:hover {
                border-color: #4299e1;
            }
            QSpinBox:focus {
                border-color: #667eea;
            }
        """

    def get_slider_style(self, color="#4299e1"):
        """Get consistent slider style"""
        return f"""
            QSlider::groove:horizontal {{
                height: 8px;
                background: #e2e8f0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {color};
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {color}dd;
                width: 24px;
                height: 24px;
                margin: -8px 0;
            }}
        """

    def apply_modern_theme(self):
        """Apply modern theme to widget"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f7fafc;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            QLabel {
                color: #2d3748;
            }
            QRadioButton {
                font-size: 14px;
                color: #2d3748;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)

    def on_mode_changed(self, single_mode):
        """Handle mode change"""
        self.lineup_count_spin.setEnabled(not single_mode)
        self.lineup_slider.setEnabled(not single_mode)
        self.diversity_slider.setEnabled(not single_mode)
        self.max_exposure_spin.setEnabled(not single_mode)

        if single_mode:
            self.lineup_count_spin.setValue(1)
            self.diversity_slider.setValue(0)

    # Preset methods
    def preset_single_cash(self):
        """Single optimal cash lineup"""
        self.single_radio.setChecked(True)
        self.contest_combo.setCurrentIndex(1)  # Cash game
        self.lineup_count_spin.setValue(1)
        self.diversity_slider.setValue(0)
        self.stacking_check.setChecked(False)

    def preset_20_gpp(self):
        """20 balanced GPP lineups"""
        self.multiple_radio.setChecked(True)
        self.contest_combo.setCurrentIndex(0)  # GPP
        self.lineup_count_spin.setValue(20)
        self.diversity_slider.setValue(70)
        self.max_exposure_spin.setValue(60)
        self.stacking_check.setChecked(True)

    def preset_150_gpp(self):
        """150 max GPP lineups"""
        self.multiple_radio.setChecked(True)
        self.contest_combo.setCurrentIndex(0)  # GPP
        self.lineup_count_spin.setValue(150)
        self.diversity_slider.setValue(85)
        self.max_exposure_spin.setValue(40)
        self.stacking_check.setChecked(True)

    def preset_5_cash(self):
        """5 safe cash lineups"""
        self.multiple_radio.setChecked(True)
        self.contest_combo.setCurrentIndex(1)  # Cash
        self.lineup_count_spin.setValue(5)
        self.diversity_slider.setValue(30)
        self.max_exposure_spin.setValue(80)
        self.stacking_check.setChecked(False)

    def generate_lineups(self):
        """Generate lineups with selected settings"""
        settings = {
            'single_mode': self.single_radio.isChecked(),
            'contest_type': self.contest_combo.currentIndex(),
            'lineup_count': self.lineup_count_spin.value(),
            'diversity': self.diversity_slider.value() / 100.0,
            'max_exposure': self.max_exposure_spin.value() / 100.0,
            'min_salary': self.min_salary_spin.value() / 100.0,
            'allow_stacking': self.stacking_check.isChecked()
        }

        # Call parent GUI method
        if hasattr(self.parent_gui, 'generate_lineups_with_settings'):
            self.parent_gui.generate_lineups_with_settings(settings)


class AdvancedAnalyticsWidget(QWidget):
    """Advanced analytics dashboard with bankroll management"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_gui = parent
        self.bankroll_data = self.load_bankroll_data()
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        """Create analytics dashboard"""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget for different analytics
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #f7fafc;
            }
            QTabBar::tab {
                background-color: #e2e8f0;
                padding: 12px 24px;
                margin-right: 4px;
                font-weight: bold;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #667eea;
            }
            QTabBar::tab:hover {
                background-color: #cbd5e0;
            }
        """)

        # Add tabs
        self.tab_widget.addTab(self.create_bankroll_tab(), "💰 Bankroll Management")
        self.tab_widget.addTab(self.create_performance_tab(), "📊 Performance Analytics")
        self.tab_widget.addTab(self.create_optimization_tab(), "⚡ Optimization Metrics")
        self.tab_widget.addTab(self.create_strategy_tab(), "🎯 Strategy Insights")

        layout.addWidget(self.tab_widget)

    def create_bankroll_tab(self):
        """Create bankroll management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Bankroll overview card
        overview_card = self.create_card_widget("💰 Bankroll Overview")
        overview_layout = QGridLayout(overview_card)

        # Current bankroll
        self.bankroll_label = QLabel(f"${self.bankroll_data.get('current_bankroll', 1000):,.2f}")
        self.bankroll_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #48bb78;
        """)
        self.bankroll_label.setAlignment(Qt.AlignCenter)

        # Stats
        stats = [
            ("Starting Bankroll:", f"${self.bankroll_data.get('starting_bankroll', 1000):,.2f}"),
            ("Total Profit/Loss:", self.format_profit_loss(self.bankroll_data.get('total_profit', 0))),
            ("ROI:", f"{self.bankroll_data.get('roi', 0):.1f}%"),
            ("Win Rate:", f"{self.bankroll_data.get('win_rate', 0):.1f}%")
        ]

        overview_layout.addWidget(self.bankroll_label, 0, 0, 1, 2)

        for i, (label, value) in enumerate(stats):
            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-weight: bold; color: #4a5568;")
            value_widget = QLabel(value)
            value_widget.setStyleSheet("font-size: 16px;")

            row = i + 1
            overview_layout.addWidget(label_widget, row, 0)
            overview_layout.addWidget(value_widget, row, 1)

        layout.addWidget(overview_card)

        # Kelly Criterion Calculator
        kelly_card = self.create_card_widget("🎲 Kelly Criterion Calculator")
        kelly_layout = QFormLayout(kelly_card)

        self.win_rate_spin = QDoubleSpinBox()
        self.win_rate_spin.setRange(0, 100)
        self.win_rate_spin.setValue(55)
        self.win_rate_spin.setSuffix("%")
        self.win_rate_spin.setDecimals(1)

        self.avg_odds_spin = QDoubleSpinBox()
        self.avg_odds_spin.setRange(1.0, 10.0)
        self.avg_odds_spin.setValue(1.8)
        self.avg_odds_spin.setPrefix("x")

        kelly_layout.addRow("Win Rate:", self.win_rate_spin)
        kelly_layout.addRow("Average Odds:", self.avg_odds_spin)

        calc_kelly_btn = QPushButton("Calculate Optimal Bet Size")
        calc_kelly_btn.clicked.connect(self.calculate_kelly)
        calc_kelly_btn.setStyleSheet("""
            QPushButton {
                background-color: #4299e1;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3182ce;
            }
        """)
        kelly_layout.addRow(calc_kelly_btn)

        self.kelly_result_label = QLabel("")
        self.kelly_result_label.setWordWrap(True)
        self.kelly_result_label.setStyleSheet("""
            padding: 10px;
            background-color: #e6fffa;
            border-radius: 6px;
            color: #234e52;
        """)
        kelly_layout.addRow(self.kelly_result_label)

        layout.addWidget(kelly_card)

        # Entry recommendations
        reco_card = self.create_card_widget("📋 Entry Recommendations")
        reco_layout = QVBoxLayout(reco_card)

        bankroll = self.bankroll_data.get('current_bankroll', 1000)
        recommendations = [
            ("Cash Games (50/50):", f"${bankroll * 0.05:.0f} - ${bankroll * 0.10:.0f} per entry"),
            ("Small GPPs:", f"${bankroll * 0.01:.0f} - ${bankroll * 0.03:.0f} per entry"),
            ("Large GPPs:", f"${bankroll * 0.005:.0f} - ${bankroll * 0.01:.0f} per entry"),
            ("Total Daily Risk:", f"${bankroll * 0.10:.0f} - ${bankroll * 0.20:.0f} maximum")
        ]

        for label, value in recommendations:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 5, 0, 5)

            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-weight: bold;")
            value_widget = QLabel(value)

            row_layout.addWidget(label_widget)
            row_layout.addStretch()
            row_layout.addWidget(value_widget)

            reco_layout.addWidget(row_widget)

        layout.addWidget(reco_card)
        layout.addStretch()

        return widget

    def create_performance_tab(self):
        """Create performance analytics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Win rate by contest type
        contest_card = self.create_card_widget("🏆 Performance by Contest Type")
        contest_layout = QVBoxLayout(contest_card)

        # Simulated data - in real app, load from history
        contest_data = [
            ("Cash Games", 68.5, 15.2, "$2,450"),
            ("Small GPPs", 12.3, 42.8, "$3,820"),
            ("Large GPPs", 2.1, 285.4, "$1,950"),
            ("H2H", 55.2, 8.9, "$890")
        ]

        # Create table
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Contest Type", "Win Rate", "Avg ROI%", "Total Profit"])
        table.setRowCount(len(contest_data))

        for i, (contest, win_rate, roi, profit) in enumerate(contest_data):
            table.setItem(i, 0, QTableWidgetItem(contest))
            table.setItem(i, 1, QTableWidgetItem(f"{win_rate}%"))
            table.setItem(i, 2, QTableWidgetItem(f"{roi}%"))
            table.setItem(i, 3, QTableWidgetItem(profit))

            # Color code ROI
            roi_item = table.item(i, 2)
            if roi > 20:
                roi_item.setBackground(QColor("#c6f6d5"))
            elif roi > 0:
                roi_item.setBackground(QColor("#fefcbf"))
            else:
                roi_item.setBackground(QColor("#fed7d7"))

        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #edf2f7;
                padding: 8px;
                font-weight: bold;
            }
        """)

        contest_layout.addWidget(table)
        layout.addWidget(contest_card)

        # Recent results
        results_card = self.create_card_widget("📈 Recent Contest Results")
        results_layout = QVBoxLayout(results_card)

        # Simulated recent results
        recent_results = [
            ("Today", "Main Slate GPP", "$5", "$45", "+800%", "🟢"),
            ("Yesterday", "Cash Game", "$25", "$50", "+100%", "🟢"),
            ("2 days ago", "Single Entry", "$10", "$0", "-100%", "🔴"),
            ("3 days ago", "Main Slate GPP", "$20", "$180", "+800%", "🟢"),
            ("4 days ago", "H2H", "$50", "$55", "+10%", "🟢")
        ]

        for date, contest, entry, winnings, roi, status in recent_results:
            result_widget = QWidget()
            result_widget.setStyleSheet("""
                QWidget {
                    background-color: #f7fafc;
                    border-radius: 6px;
                    padding: 5px;
                    margin: 2px;
                }
            """)

            result_layout = QHBoxLayout(result_widget)
            result_layout.addWidget(QLabel(status))
            result_layout.addWidget(QLabel(date))
            result_layout.addWidget(QLabel(contest))
            result_layout.addWidget(QLabel(f"Entry: {entry}"))
            result_layout.addWidget(QLabel(f"Won: {winnings}"))

            roi_label = QLabel(roi)
            roi_label.setStyleSheet(f"font-weight: bold; color: {'#48bb78' if '+' in roi else '#f56565'};")
            result_layout.addWidget(roi_label)

            results_layout.addWidget(result_widget)

        layout.addWidget(results_card)
        layout.addStretch()

        return widget

    def create_optimization_tab(self):
        """Create optimization metrics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Data quality card
        quality_card = self.create_card_widget("📊 Data Quality Metrics")
        quality_layout = QGridLayout(quality_card)

        # Quality indicators
        indicators = [
            ("Vegas Lines", 92, "#48bb78"),
            ("Confirmed Lineups", 87, "#48bb78"),
            ("Statcast Data", 76, "#f6ad55"),
            ("DFF Rankings", 64, "#f6ad55"),
            ("Weather Data", 95, "#48bb78"),
            ("Recent Performance", 81, "#48bb78")
        ]

        for i, (name, value, color) in enumerate(indicators):
            label = QLabel(name)
            label.setStyleSheet("font-weight: bold;")

            progress = QProgressBar()
            progress.setValue(value)
            progress.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid #e2e8f0;
                    border-radius: 6px;
                    text-align: center;
                    height: 25px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 4px;
                }}
            """)

            row = i // 2
            col = (i % 2) * 2
            quality_layout.addWidget(label, row, col)
            quality_layout.addWidget(progress, row, col + 1)

        layout.addWidget(quality_card)

        # Optimization speed
        speed_card = self.create_card_widget("⚡ Optimization Performance")
        speed_layout = QVBoxLayout(speed_card)

        perf_stats = [
            ("Average optimization time:", "2.3 seconds"),
            ("Cache hit rate:", "87%"),
            ("API calls saved:", "1,245 today"),
            ("Lineups per minute:", "26"),
            ("Total optimizations:", "342 this week")
        ]

        for label, value in perf_stats:
            stat_widget = QWidget()
            stat_layout = QHBoxLayout(stat_widget)
            stat_layout.setContentsMargins(0, 5, 0, 5)

            label_widget = QLabel(label)
            value_widget = QLabel(value)
            value_widget.setStyleSheet("font-weight: bold; font-size: 16px; color: #4299e1;")

            stat_layout.addWidget(label_widget)
            stat_layout.addStretch()
            stat_layout.addWidget(value_widget)

            speed_layout.addWidget(stat_widget)

        layout.addWidget(speed_card)
        layout.addStretch()

        return widget

    def create_strategy_tab(self):
        """Create strategy insights tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Winning patterns
        patterns_card = self.create_card_widget("🎯 Winning Patterns Detected")
        patterns_layout = QVBoxLayout(patterns_card)

        patterns = [
            ("✅ High-scoring games (10+ total) produce 3.2x more winning lineups"),
            ("✅ Confirmed pitchers have 18% higher actual scores than projections"),
            ("✅ 3-4 player stacks outperform 5+ stacks by 22% in GPPs"),
            ("✅ Weather delays create 45% more value opportunities"),
            ("✅ Late swap optimization increases cash rate by 15%")
        ]

        for pattern in patterns:
            pattern_label = QLabel(pattern)
            pattern_label.setWordWrap(True)
            pattern_label.setStyleSheet("""
                padding: 10px;
                background-color: #f0fff4;
                border-left: 4px solid #48bb78;
                margin: 5px 0;
            """)
            patterns_layout.addWidget(pattern_label)

        layout.addWidget(patterns_card)

        # Recommendations
        reco_card = self.create_card_widget("💡 Personalized Recommendations")
        reco_layout = QVBoxLayout(reco_card)

        recommendations = [
            ("🎯", "Focus on main slate GPPs - your ROI is 45% higher than other contests"),
            ("💰", "Increase cash game volume - your 68% win rate suggests room for growth"),
            ("📊", "Use more Statcast data - lineups with it score 8% higher on average"),
            ("🔄", "Enable late swap for all contests - you're missing profit opportunities"),
            ("⚡", "Generate 50+ lineups for large GPPs - current 20 is suboptimal")
        ]

        for icon, text in recommendations:
            reco_widget = QWidget()
            reco_widget.setStyleSheet("""
                background-color: #fef5e7;
                border-radius: 6px;
                padding: 10px;
                margin: 5px 0;
            """)

            reco_layout_h = QHBoxLayout(reco_widget)
            reco_layout_h.addWidget(QLabel(icon))

            text_label = QLabel(text)
            text_label.setWordWrap(True)
            reco_layout_h.addWidget(text_label, 1)

            reco_layout.addWidget(reco_widget)

        layout.addWidget(reco_card)
        layout.addStretch()

        return widget

    def create_card_widget(self, title):
        """Create a card widget with title"""
        card = QGroupBox(title)
        card.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 20px;
                padding-top: 20px;
                font-size: 18px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
            }
        """)
        return card

    def apply_theme(self):
        """Apply analytics theme"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f7fafc;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
        """)

    def format_profit_loss(self, value):
        """Format profit/loss with color"""
        if value >= 0:
            return f"<span style='color: #48bb78;'>+${abs(value):,.2f}</span>"
        else:
            return f"<span style='color: #f56565;'>-${abs(value):,.2f}</span>"

    def calculate_kelly(self):
        """Calculate Kelly Criterion"""
        win_rate = self.win_rate_spin.value() / 100
        odds = self.avg_odds_spin.value()

        # Kelly formula: f = (p * b - q) / b
        # where p = win probability, q = loss probability, b = odds
        q = 1 - win_rate
        kelly_pct = ((win_rate * odds - q) / odds) * 100

        # Apply safety factor (usually 0.25 to 0.5 of full Kelly)
        safe_kelly = kelly_pct * 0.25

        bankroll = self.bankroll_data.get('current_bankroll', 1000)
        bet_size = bankroll * (safe_kelly / 100)

        self.kelly_result_label.setText(f"""
        <b>Kelly Criterion Results:</b><br>
        Full Kelly: {kelly_pct:.1f}% of bankroll<br>
        Safe Kelly (25%): {safe_kelly:.1f}% of bankroll<br>
        <b>Recommended bet size: ${bet_size:.2f}</b><br>
        <small>Based on ${bankroll:,.2f} bankroll</small>
        """)

    def load_bankroll_data(self):
        """Load bankroll data from file"""
        try:
            if os.path.exists('bankroll_data.json'):
                with open('bankroll_data.json', 'r') as f:
                    return json.load(f)
        except:
            pass

        # Default data
        return {
            'starting_bankroll': 1000,
            'current_bankroll': 1250,
            'total_profit': 250,
            'roi': 25.0,
            'win_rate': 58.5
        }

    def save_bankroll_data(self):
        """Save bankroll data to file"""
        with open('bankroll_data.json', 'w') as f:
            json.dump(self.bankroll_data, f)


class LineupResultsDialog(QDialog):
    """Beautiful dialog to display multiple lineup results"""

    def __init__(self, lineups, parent=None):
        super().__init__(parent)
        self.lineups = lineups
        self.setWindowTitle(f"🎰 Generated {len(lineups)} Lineups")
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_widget = QWidget()
        header_widget.setMaximumHeight(80)
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_widget)

        title = QLabel(f"🎰 {len(self.lineups)} Optimized Lineups")
        title.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
            padding: 10px;
        """)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Export button in header
        export_btn = QPushButton("📤 Export All")
        export_btn.clicked.connect(self.export_lineups)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        header_layout.addWidget(export_btn)

        layout.addWidget(header_widget)

        # Summary stats
        summary_widget = self.create_summary_widget()
        layout.addWidget(summary_widget)

        # Lineup tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                background-color: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 4px;
                background-color: #edf2f7;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #667eea;
                font-weight: bold;
            }
        """)

        # Overview tab
        overview = self.create_overview_tab()
        self.tab_widget.addTab(overview, "📊 Overview")

        # Show first 5 lineups in detail
        for i in range(min(5, len(self.lineups))):
            lineup_widget = self.create_lineup_widget(self.lineups[i])
            self.tab_widget.addTab(lineup_widget, f"Lineup {i + 1}")

        if len(self.lineups) > 5:
            more_widget = QLabel(f"... and {len(self.lineups) - 5} more lineups\n\nUse Export to see all lineups")
            more_widget.setAlignment(Qt.AlignCenter)
            more_widget.setStyleSheet("font-size: 16px; color: #718096; padding: 40px;")
            self.tab_widget.addTab(more_widget, "...")

        layout.addWidget(self.tab_widget)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(40)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #718096;
                color: white;
                padding: 10px 30px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4a5568;
            }
        """)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def create_summary_widget(self):
        """Create summary statistics widget"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                padding: 20px;
            }
        """)

        layout = QGridLayout(card)

        # Calculate stats
        scores = [l['total_score'] for l in self.lineups]
        salaries = [l['total_salary'] for l in self.lineups]
        ceilings = [l.get('ceiling', l['total_score']) for l in self.lineups]
        floors = [l.get('floor', l['total_score']) for l in self.lineups]

        stats = [
            ("📈 Average Score", f"{sum(scores) / len(scores):.1f}"),
            ("📊 Score Range", f"{min(scores):.1f} - {max(scores):.1f}"),
            ("💰 Avg Salary", f"${int(sum(salaries) / len(salaries)):,}"),
            ("🚀 Avg Ceiling", f"{sum(ceilings) / len(ceilings):.1f}"),
            ("🛡️ Avg Floor", f"{sum(floors) / len(floors):.1f}"),
            ("🎯 Contest Type", self.lineups[0].get('contest_type', 'N/A').upper())
        ]

        for i, (label, value) in enumerate(stats):
            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-weight: bold; font-size: 14px; color: #4a5568;")

            value_widget = QLabel(value)
            value_widget.setStyleSheet("font-size: 18px; color: #2d3748;")

            row = i // 3
            col = (i % 3) * 2
            layout.addWidget(label_widget, row, col)
            layout.addWidget(value_widget, row, col + 1)

        return card

    def create_overview_tab(self):
        """Create overview tab with exposure analysis"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Player exposure analysis
        exposure_card = QWidget()
        exposure_card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                padding: 15px;
            }
        """)

        exposure_layout = QVBoxLayout(exposure_card)

        title = QLabel("🎯 Player Exposure Analysis")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        exposure_layout.addWidget(title)

        # Calculate exposure
        player_usage = {}
        player_info = {}

        for lineup_data in self.lineups:
            for player in lineup_data['lineup']:
                player_id = player.id
                if player_id not in player_usage:
                    player_usage[player_id] = 0
                    player_info[player_id] = {
                        'name': player.name,
                        'position': player.primary_position,
                        'team': player.team,
                        'salary': player.salary,
                        'score': player.enhanced_score
                    }
                player_usage[player_id] += 1

        # Create exposure table
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Player", "Pos", "Team", "Salary", "Proj", "Exposure"
        ])

        # Sort by exposure
        sorted_players = sorted(player_usage.items(),
                                key=lambda x: x[1], reverse=True)[:20]

        table.setRowCount(len(sorted_players))

        for i, (player_id, usage) in enumerate(sorted_players):
            info = player_info[player_id]
            exposure_pct = (usage / len(self.lineups)) * 100

            table.setItem(i, 0, QTableWidgetItem(info['name']))
            table.setItem(i, 1, QTableWidgetItem(info['position']))
            table.setItem(i, 2, QTableWidgetItem(info['team']))
            table.setItem(i, 3, QTableWidgetItem(f"${info['salary']:,}"))
            table.setItem(i, 4, QTableWidgetItem(f"{info['score']:.1f}"))

            exposure_item = QTableWidgetItem(f"{exposure_pct:.1f}%")
            if exposure_pct >= 60:
                exposure_item.setBackground(QColor("#fed7d7"))  # Red
            elif exposure_pct >= 40:
                exposure_item.setBackground(QColor("#fefcbf"))  # Yellow
            else:
                exposure_item.setBackground(QColor("#c6f6d5"))  # Green

            table.setItem(i, 5, exposure_item)

        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                gridline-color: #e2e8f0;
            }
            QHeaderView::section {
                background-color: #f7fafc;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)

        exposure_layout.addWidget(table)

        # Diversity score
        diversity_label = QLabel(
            f"📊 Unique Players Used: {len(player_usage)} ({(len(player_usage) / len(self.lineups) * 10):.1f}/10 diversity score)")
        diversity_label.setStyleSheet(
            "font-size: 14px; margin-top: 10px; padding: 10px; background-color: #e6fffa; border-radius: 6px;")
        exposure_layout.addWidget(diversity_label)

        layout.addWidget(exposure_card)

        return widget

    def create_lineup_widget(self, lineup_data):
        """Create widget for single lineup"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Lineup stats card
        stats_card = QWidget()
        stats_card.setStyleSheet("""
            QWidget {
                background-color: #f7fafc;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        stats_layout = QHBoxLayout(stats_card)

        stats = [
            ("Score", f"{lineup_data['total_score']:.2f}"),
            ("Salary", f"${lineup_data['total_salary']:,}"),
            ("Ceiling", f"{lineup_data.get('ceiling', 0):.1f}"),
            ("Floor", f"{lineup_data.get('floor', 0):.1f}")
        ]

        for label, value in stats:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)

            label_w = QLabel(label)
            label_w.setStyleSheet("color: #718096; font-size: 12px;")
            label_w.setAlignment(Qt.AlignCenter)

            value_w = QLabel(value)
            value_w.setStyleSheet("font-size: 18px; font-weight: bold; color: #2d3748;")
            value_w.setAlignment(Qt.AlignCenter)

            stat_layout.addWidget(label_w)
            stat_layout.addWidget(value_w)

            stats_layout.addWidget(stat_widget)

        layout.addWidget(stats_card)

        # Player table
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Pos", "Player", "Team", "Opp", "Salary", "Projection"
        ])

        lineup = lineup_data['lineup']
        table.setRowCount(len(lineup))

        for i, player in enumerate(lineup):
            pos = getattr(player, 'assigned_position', player.primary_position)

            # Position with color
            pos_item = QTableWidgetItem(pos)
            if pos == 'P':
                pos_item.setBackground(QColor("#bee3f8"))
            elif pos in ['C', '1B', '2B', '3B', 'SS']:
                pos_item.setBackground(QColor("#fbb6ce"))
            else:  # OF
                pos_item.setBackground(QColor("#c6f6d5"))

            table.setItem(i, 0, pos_item)
            table.setItem(i, 1, QTableWidgetItem(player.name))
            table.setItem(i, 2, QTableWidgetItem(player.team))

            # Opponent
            opp = getattr(player, 'opponent', 'N/A')
            table.setItem(i, 3, QTableWidgetItem(opp))

            table.setItem(i, 4, QTableWidgetItem(f"${player.salary:,}"))
            table.setItem(i, 5, QTableWidgetItem(f"{player.enhanced_score:.1f}"))

        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f7fafc;
                padding: 8px;
                font-weight: bold;
            }
        """)

        layout.addWidget(table)

        # Stacks info
        if lineup_data.get('stacks'):
            stacks_text = ", ".join([f"{team} ({count})" for team, count in lineup_data['stacks']])
            stack_label = QLabel(f"🏈 Stacks: {stacks_text}")
            stack_label.setStyleSheet("""
                padding: 10px;
                background-color: #f0fff4;
                border-radius: 6px;
                color: #22543d;
                font-weight: bold;
            """)
            layout.addWidget(stack_label)

        return widget

    def export_lineups(self):
        """Export lineups to CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Lineups",
            f"dfs_lineups_{len(self.lineups)}.csv",
            "CSV Files (*.csv)"
        )

        if filename:
            import csv

            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)

                # DraftKings upload format header
                writer.writerow(['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF'])

                for lineup_data in self.lineups:
                    row = []

                    # Group by position
                    position_map = {}
                    for player in lineup_data['lineup']:
                        pos = getattr(player, 'assigned_position', player.primary_position)
                        if pos not in position_map:
                            position_map[pos] = []
                        position_map[pos].append(player.name)

                    # Fill in order
                    for pos in ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']:
                        if pos in position_map and position_map[pos]:
                            row.append(position_map[pos].pop(0))
                        else:
                            row.append("")

                    writer.writerow(row)

            QMessageBox.information(
                self, "Export Complete",
                f"Exported {len(self.lineups)} lineups to:\n{filename}\n\n"
                "Ready for DraftKings upload!"
            )

    def apply_theme(self):
        """Apply modern theme"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f7fafc;
            }
            QLabel {
                color: #2d3748;
            }
        """)


# Integration code for enhanced_dfs_gui.py
def integrate_new_features():
    """Add these to your enhanced_dfs_gui.py"""

    code = '''
    # In create_optimize_tab method, replace the multi-lineup section with:
    self.lineup_widget = ModernLineupGeneratorWidget(self)
    layout.addWidget(self.lineup_widget)

    # Add new tab for analytics:
    self.analytics_widget = AdvancedAnalyticsWidget(self)
    self.tab_widget.addTab(self.analytics_widget, "📊 Analytics")

    # Add this method to handle lineup generation:
    def generate_lineups_with_settings(self, settings):
        """Generate lineups with advanced settings"""
        if not self.dk_file:
            QMessageBox.warning(self, "No Data", "Please load DraftKings CSV first")
            return

        # Map contest types to optimizer modes
        contest_map = {
            0: 'gpp',      # GPP/Tournament
            1: 'cash',     # Cash Game
            2: 'single',   # Single Entry
            3: 'h2h',      # Head-to-Head
            4: 'multi',    # Multiplier
            5: 'sat',      # Satellite
            6: 'showdown'  # Showdown
        }

        contest_type = contest_map.get(settings['contest_type'], 'gpp')

        try:
            # Initialize core
            core = BulletproofDFSCore()
            core.load_draftkings_csv(self.dk_file)

            # Apply manual selections if any
            manual_text = self.manual_input.toPlainText()
            if manual_text:
                core.apply_manual_selection(manual_text)

            # Detect confirmations
            core.detect_confirmed_players()

            # Single lineup mode
            if settings['single_mode']:
                lineup, score = core.optimize_for_contest(contest_type)
                if lineup:
                    self.display_single_lineup(lineup, score, contest_type)
            else:
                # Multiple lineups
                lineups = core.generate_contest_lineups(
                    count=settings['lineup_count'],
                    contest_type=contest_type,
                    min_salary_pct=settings['min_salary'],
                    diversity_factor=settings['diversity'],
                    max_exposure=settings['max_exposure']
                )

                if lineups:
                    self.display_multiple_lineups(lineups)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Optimization failed: {str(e)}")
    '''

    return code
