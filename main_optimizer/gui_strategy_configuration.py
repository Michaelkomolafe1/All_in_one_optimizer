#!/usr/bin/env python3
"""
GUI STRATEGY CONFIGURATION
==========================
Defines ONLY the production-ready strategies for your main DFS GUI
Based on your actual test results and proven winners
"""

from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class GUIStrategyManager:
    """
    Manages strategies for the main DFS GUI
    Only includes PROVEN strategies, not experimental/simulation ones
    """

    def __init__(self):
        # ======================================
        # PRIMARY STRATEGIES (Your Winners!)
        # ======================================
        self.primary_strategies = {
            'cash': {
                'small': 'pitcher_dominance',  # 80% win rate
                'medium': 'projection_monster',  # 72% win rate
                'large': 'projection_monster'  # 74% win rate
            },
            'gpp': {
                'small': 'tournament_winner_gpp',  # -33% ROI (best)
                'medium': 'tournament_winner_gpp',  # -51% ROI (best)
                'large': 'correlation_value'  # Best for large
            }
        }

        # ======================================
        # GUI DROPDOWN OPTIONS
        # Only strategies you want users to select
        # ======================================
        self.gui_available_strategies = {
            'Auto': [
                'auto'  # Let system pick based on slate
            ],
            'Cash (50/50, Double-Up)': [
                'projection_monster',  # Your best overall cash
                'pitcher_dominance',  # Best for small slates
            ],
            'GPP (Tournaments)': [
                'tournament_winner_gpp',  # Your BEST GPP strategy
                'correlation_value',  # Good for large slates
                'smart_stack',  # If you want legacy option
                'matchup_leverage_stack',  # If you want legacy option
                'truly_smart_stack'  # Advanced option
            ]
        }

        # ======================================
        # STRATEGY DESCRIPTIONS FOR GUI
        # ======================================
        self.strategy_descriptions = {
            'auto': "🤖 Auto-select best strategy based on slate size",

            # Cash
            'projection_monster': "📊 Maximum projected points (72-74% win rate)",
            'pitcher_dominance': "⚾ Elite pitchers focus (80% win rate on small slates)",

            # GPP
            'tournament_winner_gpp': "🏆 Proven tournament winner patterns (BEST GPP)",
            'correlation_value': "🔗 Value plays with correlation (large slates)",
            'smart_stack': "📚 Intelligent team stacking",
            'matchup_leverage_stack': "🎯 Exploit favorable matchups",
            'truly_smart_stack': "🧠 Advanced game theory stacking"
        }

        # ======================================
        # SLATE SIZE THRESHOLDS
        # ======================================
        self.slate_thresholds = {
            'small': (1, 4),  # 1-4 games
            'medium': (5, 9),  # 5-9 games
            'large': (10, 99)  # 10+ games
        }

    def get_gui_strategies(self) -> Dict[str, List[str]]:
        """
        Get strategies for GUI dropdown
        ONLY returns production-ready strategies
        """
        return self.gui_available_strategies

    def get_strategy_description(self, strategy: str) -> str:
        """Get user-friendly description for GUI tooltip"""
        return self.strategy_descriptions.get(
            strategy,
            "Custom strategy"
        )

    def auto_select_strategy(self,
                             num_games: int,
                             contest_type: str,
                             override: Optional[str] = None) -> Tuple[str, str]:
        """
        Auto-select best strategy for slate

        Args:
            num_games: Number of games in slate
            contest_type: 'cash' or 'gpp'
            override: Manual strategy override

        Returns:
            (strategy_name, reason)
        """
        # Allow manual override
        if override and override != 'auto':
            return override, f"Manual selection: {override}"

        # Determine slate size
        slate_size = self._get_slate_size(num_games)

        # Get best strategy for this combo
        strategy = self.primary_strategies[contest_type.lower()][slate_size]

        # Build reason with performance
        if contest_type.lower() == 'cash':
            if strategy == 'pitcher_dominance' and slate_size == 'small':
                reason = f"{num_games} games → {strategy} (80% win rate)"
            elif strategy == 'projection_monster':
                if slate_size == 'medium':
                    reason = f"{num_games} games → {strategy} (72% win rate)"
                else:
                    reason = f"{num_games} games → {strategy} (74% win rate)"
            else:
                reason = f"{num_games} games → {strategy}"
        else:  # GPP
            if strategy == 'tournament_winner_gpp':
                reason = f"{num_games} games → {strategy} (BEST GPP)"
            elif strategy == 'correlation_value':
                reason = f"{num_games} games → {strategy} (large slate specialist)"
            else:
                reason = f"{num_games} games → {strategy}"

        logger.info(f"Auto-selected: {strategy} - {reason}")
        return strategy, reason

    def _get_slate_size(self, num_games: int) -> str:
        """Determine slate size category"""
        if num_games <= 4:
            return 'small'
        elif num_games <= 9:
            return 'medium'
        else:
            return 'large'

    def validate_strategy(self, strategy: str) -> bool:
        """Check if strategy is valid for GUI"""
        # Check all available strategies
        for category, strategies in self.gui_available_strategies.items():
            if strategy in strategies:
                return True

        # Also check primary strategies
        for contest_type in self.primary_strategies.values():
            if strategy in contest_type.values():
                return True

        return False

    def get_strategy_requirements(self, strategy: str) -> Dict:
        """
        Get data requirements for a strategy
        (For integration with SmartEnrichmentManager)
        """
        requirements = {
            # Cash strategies
            'projection_monster': {
                'needs_consistency': True,
                'needs_recent_form': True,
                'needs_vegas': True,
                'needs_statcast': False,
                'needs_ownership': False
            },
            'pitcher_dominance': {
                'needs_k_rate': True,
                'needs_consistency': True,
                'needs_matchup': True,
                'needs_statcast': True,
                'needs_ownership': False
            },

            # GPP strategies
            'tournament_winner_gpp': {
                'needs_ownership': True,
                'needs_statcast': True,
                'needs_barrel_rate': True,
                'needs_vegas': True,
                'needs_batting_order': True
            },
            'correlation_value': {
                'needs_vegas': True,
                'needs_batting_order': True,
                'needs_ownership': True,
                'needs_statcast': True
            },
            'smart_stack': {
                'needs_vegas': True,
                'needs_batting_order': True,
                'needs_ownership': True,
                'needs_weather': True
            },
            'matchup_leverage_stack': {
                'needs_matchup': True,
                'needs_vegas': True,
                'needs_batting_order': True,
                'needs_statcast': True
            },
            'truly_smart_stack': {
                'needs_vegas': True,
                'needs_batting_order': True,
                'needs_ownership': True,
                'needs_statcast': True,
                'needs_weather': True
            }
        }

        return requirements.get(strategy, {
            'needs_vegas': True,
            'needs_batting_order': True,
            'needs_recent_form': True
        })


# ======================================
# GUI INTEGRATION EXAMPLE
# ======================================
class YourDFSGUI:
    """
    Example of how to use in your GUI
    """

    def __init__(self):
        # Initialize strategy manager
        self.strategy_manager = GUIStrategyManager()

        # Other GUI initialization...
        self.setup_ui()

    def setup_ui(self):
        """Setup GUI elements"""
        # ... your existing GUI setup ...

        # Setup strategy dropdown
        self.setup_strategy_dropdown()

    def setup_strategy_dropdown(self):
        """
        Setup strategy dropdown with ONLY production strategies
        """
        # Get available strategies for GUI
        strategies = self.strategy_manager.get_gui_strategies()

        # Clear existing items
        self.strategy_combo.clear()

        # Add strategies by category
        for category, strategy_list in strategies.items():
            # Add category as disabled item (separator)
            self.strategy_combo.addItem(f"──── {category} ────")
            item_count = self.strategy_combo.count() - 1
            self.strategy_combo.model().item(item_count).setEnabled(False)

            # Add strategies in category
            for strategy in strategy_list:
                description = self.strategy_manager.get_strategy_description(strategy)
                self.strategy_combo.addItem(f"  {strategy}", strategy)

                # Set tooltip
                item_count = self.strategy_combo.count() - 1
                self.strategy_combo.setItemData(
                    item_count,
                    description,
                    Qt.ToolTipRole
                )

    def on_optimize_clicked(self):
        """When optimize button is clicked"""
        # Get current selections
        contest_type = self.contest_type.currentText().lower()
        strategy_selection = self.strategy_combo.currentData()  # Gets the strategy key

        # Auto-select if needed
        if strategy_selection == 'auto' or not strategy_selection:
            strategy, reason = self.strategy_manager.auto_select_strategy(
                num_games=self.detected_games,
                contest_type=contest_type
            )
            self.update_status(f"Auto-selected: {reason}")
        else:
            # Validate manual selection
            if not self.strategy_manager.validate_strategy(strategy_selection):
                self.show_error(f"Invalid strategy: {strategy_selection}")
                return
            strategy = strategy_selection

        # Now optimize with the selected strategy
        self.run_optimization(strategy, contest_type)

    def run_optimization(self, strategy: str, contest_type: str):
        """Run optimization with selected strategy"""
        # This is where you'd call your optimizer
        logger.info(f"Optimizing with {strategy} for {contest_type}")

        # Get requirements for enrichment
        requirements = self.strategy_manager.get_strategy_requirements(strategy)

        # Run your optimization pipeline...
        # self.system.optimize(strategy, contest_type, requirements)


# ======================================
# SIMPLE FUNCTION FOR BACKWARDS COMPATIBILITY
# ======================================
def get_gui_strategy_list() -> List[str]:
    """
    Simple function to get list of all GUI strategies
    For backwards compatibility with existing code
    """
    manager = GUIStrategyManager()
    all_strategies = []

    for category, strategies in manager.get_gui_strategies().items():
        all_strategies.extend(strategies)

    # Remove 'auto' and return unique list
    all_strategies = [s for s in all_strategies if s != 'auto']
    return list(set(all_strategies))


if __name__ == "__main__":
    # Test the configuration
    manager = GUIStrategyManager()

    print("=" * 60)
    print("GUI STRATEGY CONFIGURATION")
    print("=" * 60)

    print("\n📋 Available GUI Strategies:")
    for category, strategies in manager.get_gui_strategies().items():
        print(f"\n{category}:")
        for strategy in strategies:
            desc = manager.get_strategy_description(strategy)
            print(f"  • {strategy}: {desc}")

    print("\n🎯 Auto-Selection Examples:")
    test_cases = [
        (3, 'cash'),  # Small cash
        (7, 'cash'),  # Medium cash
        (12, 'cash'),  # Large cash
        (3, 'gpp'),  # Small GPP
        (7, 'gpp'),  # Medium GPP
        (12, 'gpp'),  # Large GPP
    ]

    for num_games, contest in test_cases:
        strategy, reason = manager.auto_select_strategy(num_games, contest)
        print(f"  {num_games} games, {contest}: {reason}")

    print("\n✅ Configuration ready for GUI integration!")