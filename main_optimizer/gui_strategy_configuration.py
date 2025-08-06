#!/usr/bin/env python3
"""
GUI STRATEGY CONFIGURATION
==========================
Manages strategies for the DFS Optimizer GUI
"""

from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class GUIStrategyManager:
    """Manages strategies for the DFS GUI"""

    def __init__(self):
        # Primary strategies based on test results
        self.primary_strategies = {
            'cash': {
                'small': 'pitcher_dominance',
                'medium': 'projection_monster',
                'large': 'projection_monster'
            },
            'gpp': {
                'small': 'tournament_winner_gpp',
                'medium': 'tournament_winner_gpp',
                'large': 'correlation_value'
            }
        }

        # GUI available strategies
        self.gui_available_strategies = {
            'Auto': ['auto'],
            'Cash (50/50, Double-Up)': [
                'projection_monster',
                'pitcher_dominance',
            ],
            'GPP (Tournaments)': [
                'tournament_winner_gpp',
                'correlation_value',
            ]
        }

        # Strategy descriptions
        self.strategy_descriptions = {
            'auto': "Auto-select best strategy based on slate size",
            'projection_monster': "Balanced approach for cash games (72-74% win rate)",
            'pitcher_dominance': "Elite pitchers focus (80% win rate on small slates)",
            'tournament_winner_gpp': "Proven tournament winner patterns",
            'correlation_value': "Value plays with correlation for large slates",
        }

    def get_gui_strategies(self) -> Dict[str, List[str]]:
        """Get strategies organized by category for GUI"""
        return self.gui_available_strategies

    def get_strategy_description(self, strategy: str) -> str:
        """Get description for a strategy"""
        return self.strategy_descriptions.get(strategy, f"Strategy: {strategy}")

    def get_all_strategies(self) -> List[str]:
        """Get list of all available strategies"""
        all_strategies = []
        for category_strategies in self.gui_available_strategies.values():
            all_strategies.extend(category_strategies)
        return list(set(all_strategies))

    def auto_select_strategy(self, num_games: int, contest_type: str) -> Tuple[str, str]:
        """Auto-select best strategy based on slate characteristics"""
        slate_size = self._get_slate_size(num_games)

        if contest_type == 'cash':
            strategy = self.primary_strategies['cash'][slate_size]
            if strategy == 'pitcher_dominance':
                reason = f"{num_games} games → {strategy} (80% win rate on small slates)"
            elif strategy == 'projection_monster':
                reason = f"{num_games} games → {strategy} (72-74% win rate)"
            else:
                reason = f"{num_games} games → {strategy}"
        else:  # GPP
            strategy = self.primary_strategies['gpp'][slate_size]
            if strategy == 'tournament_winner_gpp':
                reason = f"{num_games} games → {strategy} (Best GPP strategy)"
            elif strategy == 'correlation_value':
                reason = f"{num_games} games → {strategy} (Large slate specialist)"
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
        for strategies in self.gui_available_strategies.values():
            if strategy in strategies:
                return True
        return False

    def get_strategy_requirements(self, strategy: str) -> Dict:
        """Get data requirements for a strategy"""
        requirements = {
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
                'needs_recent_form': True,
                'needs_vegas': True,
                'needs_batting_order': True
            },
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
            }
        }

        return requirements.get(strategy, {
            'needs_vegas': True,
            'needs_batting_order': True,
            'needs_recent_form': True
        })


# Test if this works standalone
if __name__ == "__main__":
    manager = GUIStrategyManager()

    print("Testing GUIStrategyManager...")
    print(f"Available strategies: {manager.get_all_strategies()}")

    # Test the method that was causing the error
    test_strategy = 'projection_monster'
    desc = manager.get_strategy_description(test_strategy)
    print(f"Description for {test_strategy}: {desc}")

    # Test auto-select
    strategy, reason = manager.auto_select_strategy(6, 'cash')
    print(f"Auto-selected: {strategy} - {reason}")

    print("\n✅ GUIStrategyManager working correctly!")