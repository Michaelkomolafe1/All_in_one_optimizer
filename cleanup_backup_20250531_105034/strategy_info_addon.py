#!/usr/bin/env python3
"""
Strategy Info Addon
Add this to your GUI to show helpful strategy information
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class StrategyInfoWidget(QWidget):
    """Widget that displays information about the selected strategy"""

    def __init__(self, strategy_combo):
        super().__init__()
        self.strategy_combo = strategy_combo
        self.setup_ui()

        # Connect to strategy changes
        self.strategy_combo.currentIndexChanged.connect(self.update_info)
        self.update_info()  # Set initial info

    def setup_ui(self):
        """Setup the info widget UI"""
        layout = QVBoxLayout(self)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("""
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            margin: 5px 0;
            font-size: 13px;
            line-height: 1.4;
        """)

        layout.addWidget(self.info_label)

    def update_info(self):
        """Update info based on selected strategy"""
        index = self.strategy_combo.currentIndex()

        info_texts = [
            """🎯 <b>Smart Default (RECOMMENDED)</b><br>
            • Starts with 61 confirmed players (guaranteed starters)<br>
            • Adds 40 best players with enhanced data<br>
            • Uses DFF, Statcast, Vegas data for scoring<br>
            • Includes your manual picks with bonus<br>
            • <b>Pool size:</b> ~100 quality players<br>
            • <b>Best for:</b> Most users, balanced safety + opportunity""",

            """🔒 <b>Safe Only (MOST CONSERVATIVE)</b><br>
            • Uses only confirmed starting lineup players<br>
            • Includes your manual picks<br>
            • Maximum safety - no lineup risk<br>
            • <b>Pool size:</b> ~70 players<br>
            • <b>Best for:</b> Cash games where safety matters most""",

            """🎯 <b>Smart + Picks (ENHANCED)</b><br>
            • All confirmed players (61)<br>
            • All your manual selections<br>
            • Perfect hybrid of safety + your insights<br>
            • <b>Pool size:</b> 65-80 players<br>
            • <b>Best for:</b> When you have strong player opinions""",

            """⚖️ <b>Balanced (SAFE PITCHERS)</b><br>
            • Only confirmed starting pitchers (safer)<br>
            • All available batters (more flexibility)<br>
            • Reduces pitcher risk while keeping batter options<br>
            • <b>Pool size:</b> ~200 players<br>
            • <b>Best for:</b> Tournaments with pitcher safety""",

            """✏️ <b>Manual Only (EXPERT MODE)</b><br>
            • Uses ONLY the players you specify<br>
            • Complete control over player pool<br>
            • Requires 15+ players for all positions<br>
            • <b>Pool size:</b> Your choice<br>
            • <b>Best for:</b> Experts who know exactly who they want"""
        ]

        if index < len(info_texts):
            self.info_label.setText(info_texts[index])


def add_strategy_info_to_gui(gui_instance, strategy_card_layout):
    """
    Add strategy info widget to your existing GUI

    Usage in your GUI:
    # After creating your strategy card
    from strategy_info_addon import add_strategy_info_to_gui
    add_strategy_info_to_gui(self, strategy_card.content_layout)
    """

    info_widget = StrategyInfoWidget(gui_instance.strategy_combo)
    strategy_card_layout.addWidget(info_widget)

    return info_widget


if __name__ == "__main__":
    print("Strategy Info Addon created!")
    print("Import this in your GUI to add helpful strategy descriptions.")
