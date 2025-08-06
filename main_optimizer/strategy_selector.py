#!/usr/bin/env python3
"""
STRATEGY AUTO-SELECTOR V3 - UPDATED BASED ON TEST RESULTS
=========================================================
Updated with your winning strategies from comparison tests
Small slates: 2-4 games (as you specified)
"""

import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class StrategyAutoSelector:
    """Automatically selects optimal strategy based on slate characteristics"""

    def __init__(self):
        # UPDATED strategies based on your test results
        self.top_strategies = {
            'cash': {
                'small': 'pitcher_dominance',  # 80% win rate on small slates
                'medium': 'projection_monster',  # 72% win rate on medium
                'large': 'projection_monster'  # 74% win rate on large
            },
            'gpp': {
                'small': 'tournament_winner_gpp',  # Best GPP for small (-33% ROI vs -57%)
                'medium': 'tournament_winner_gpp',  # Best for medium (-51% ROI vs -66%)
                'large': 'correlation_value'  # Large slates favor correlation
            }
        }

        # Slate size thresholds - UPDATED per your request
        self.game_thresholds = {
            'small': (1, 4),  # 2-4 games as you specified
            'medium': (5, 9),  # 5-9 games
            'large': (10, 99)  # 10+ games
        }

        # Store last analysis for debugging
        self.last_analysis = None

        # Performance metrics from your tests
        self.strategy_performance = {
            'pitcher_dominance': {
                'small_cash_win_rate': 0.80,
                'medium_cash_win_rate': 0.66,
                'large_cash_win_rate': 0.64
            },
            'projection_monster': {
                'small_cash_win_rate': 0.74,
                'medium_cash_win_rate': 0.72,
                'large_cash_win_rate': 0.74
            },
            'tournament_winner_gpp': {
                'small_gpp_roi': -0.33,
                'medium_gpp_roi': -0.51,
                'large_gpp_roi': -0.52
            },
            'correlation_value': {
                'small_gpp_roi': -0.57,
                'medium_gpp_roi': -0.66,
                'large_gpp_roi': -0.53
            }
        }

    def analyze_slate_from_csv(self, players: List) -> Dict:
        """Analyze slate characteristics from player data"""

        # Detect unique games
        games = set()
        teams = set()
        game_info = defaultdict(lambda: {'teams': set(), 'total': 0})

        for player in players:
            if not hasattr(player, 'team'):
                continue

            # Extract game info
            if hasattr(player, 'game_info') and player.game_info:
                game_id = player.game_info
            elif hasattr(player, 'game_id'):
                game_id = player.game_id
            else:
                # Try to infer from team matchup
                game_id = f"{player.team}_game"

            games.add(game_id)
            teams.add(player.team)
            game_info[game_id]['teams'].add(player.team)

            # Get game total
            if hasattr(player, 'game_total') and player.game_total:
                game_info[game_id]['total'] = max(game_info[game_id]['total'], player.game_total)

        # Count actual games (should have 2 teams each)
        actual_game_count = len([g for g, info in game_info.items()
                                 if len(info['teams']) >= 2])

        # If we can't detect games properly, estimate from teams
        if actual_game_count == 0:
            estimated_games = len(teams) // 2
            actual_game_count = max(1, estimated_games)

        # Calculate average game total
        game_totals = [info['total'] for info in game_info.values() if info['total'] > 0]
        avg_game_total = sum(game_totals) / len(game_totals) if game_totals else 9.0

        # Count player statistics
        total_players = len(players)
        confirmed_count = sum(1 for p in players if getattr(p, 'confirmation', 0) > 0)

        # Determine slate size
        slate_size = self._determine_slate_size_by_games(actual_game_count)

        # Check if showdown
        positions = set(p.primary_position for p in players if hasattr(p, 'primary_position'))
        is_showdown = 'CPT' in positions or 'MVP' in positions

        analysis = {
            'game_count': actual_game_count,
            'slate_size': slate_size,
            'team_count': len(teams),
            'total_players': total_players,
            'confirmed_players': confirmed_count,
            'avg_game_total': avg_game_total,
            'is_showdown': is_showdown,
            'timestamp': datetime.now().isoformat()
        }

        self.last_analysis = analysis

        # Log analysis
        logger.info("=" * 60)
        logger.info("SLATE ANALYSIS:")
        logger.info(f"Games Detected: {actual_game_count}")
        logger.info(f"Slate Size: {slate_size.upper()}")
        logger.info(f"Total Players: {total_players}")
        logger.info(f"Confirmed: {confirmed_count}")
        logger.info(f"Avg Game Total: {avg_game_total:.1f}")
        logger.info("=" * 60)

        return analysis

    def _determine_slate_size_by_games(self, game_count: int) -> str:
        """Determine slate size based on number of games"""
        for size, (min_games, max_games) in self.game_thresholds.items():
            if min_games <= game_count <= max_games:
                return size
        return 'large'  # Default to large

    def select_strategy(self, slate_analysis: Dict, contest_type: str,
                        force_strategy: Optional[str] = None,
                        force_slate_size: Optional[str] = None) -> Tuple[str, str]:
        """
        Select the optimal strategy based on slate analysis and test results

        Returns:
            Tuple of (strategy_name, reason)
        """

        # Allow manual override
        if force_strategy:
            logger.info(f"Using manually selected strategy: {force_strategy}")
            return force_strategy, "Manually selected"

        # Use forced slate size if provided
        slate_size = force_slate_size or slate_analysis['slate_size']

        # Handle showdown
        if slate_analysis.get('is_showdown', False):
            return 'showdown_optimal', "Showdown slate detected"

        # Normalize contest type
        contest_type = contest_type.lower()
        if contest_type in ['50-50', '50/50', 'double-up', 'cash game']:
            contest_type = 'cash'
        elif contest_type not in ['cash', 'gpp']:
            contest_type = 'gpp'  # Default to GPP

        # Get the optimal strategy
        strategy = self.top_strategies[contest_type][slate_size]

        # Build detailed reason with performance metrics
        game_count = slate_analysis['game_count']

        if contest_type == 'cash':
            # Get win rate for this strategy/slate combo
            perf_key = f"{slate_size}_cash_win_rate"
            win_rate = self.strategy_performance.get(strategy, {}).get(perf_key, 0)
            metric = f"{win_rate:.0%} win rate"

            # Add comparison if relevant
            if slate_size == 'small' and strategy == 'pitcher_dominance':
                metric += " (vs 74% for projection_monster)"
        else:
            # Get ROI for GPP strategies
            perf_key = f"{slate_size}_gpp_roi"
            roi = self.strategy_performance.get(strategy, {}).get(perf_key, 0)
            metric = f"{roi:.0%} ROI"

            # Add note about tournament_winner performance
            if strategy == 'tournament_winner_gpp':
                metric += " (best tested strategy)"

        reason = f"{game_count} games = {slate_size} slate → {strategy} ({metric})"

        logger.info(f"Selected Strategy: {strategy}")
        logger.info(f"Reason: {reason}")

        return strategy, reason

    def get_all_strategies(self) -> Dict[str, List[str]]:
        """Get all available strategies organized by type"""
        return {
            'Auto-Select': ['auto'],
            'Cash Strategies': [
                'projection_monster',  # Best for medium/large
                'pitcher_dominance',  # Best for small
                'projection_monster_enhanced',  # If you have enhanced versions
                'pitcher_dominance_enhanced'
            ],
            'GPP Strategies': [
                'tournament_winner_gpp',  # Your new winning strategy!
                'correlation_value',  # Good for large slates
                'smart_stack',  # Legacy
                'matchup_leverage_stack',  # Legacy
                'truly_smart_stack'  # If you fixed the recursion
            ],
            'Experimental': [
                'elite_hybrid_gpp',
                'ultimate_cash_hybrid',
                'single_game_hammer'
            ]
        }

    def get_strategy_description(self, strategy: str) -> str:
        """Get description of what each strategy does"""
        descriptions = {
            'pitcher_dominance': "Prioritizes elite pitchers with high K upside. Best for small slates (80% win rate).",
            'projection_monster': "Maximizes raw projected points. Best for medium/large cash games (72-74% win rate).",
            'tournament_winner_gpp': "Uses patterns from actual GPP winners. Best overall GPP strategy (-33% to -52% ROI).",
            'correlation_value': "Focuses on correlated plays and stacking. Good for large GPP slates.",
            'smart_stack': "Builds smart team stacks with proper correlation.",
            'matchup_leverage_stack': "Targets favorable matchups with stacking.",
            'truly_smart_stack': "Advanced stacking with game theory considerations."
        }
        return descriptions.get(strategy, "Custom strategy")

    def get_performance_summary(self) -> str:
        """Get a summary of strategy performance from tests"""
        return """
STRATEGY PERFORMANCE SUMMARY (from your tests):

CASH GAMES:
• Small Slates (2-4 games):
  - pitcher_dominance: 80% win rate ⭐
  - projection_monster: 74% win rate

• Medium Slates (5-9 games):
  - projection_monster: 72% win rate ⭐
  - pitcher_dominance: 66% win rate

• Large Slates (10+ games):
  - projection_monster: 74% win rate ⭐
  - pitcher_dominance: 64% win rate

GPP TOURNAMENTS:
• Small Slates: tournament_winner_gpp (-33% ROI) ⭐
• Medium Slates: tournament_winner_gpp (-51% ROI) ⭐
• Large Slates: correlation_value (-53% ROI) ⭐

Note: GPP ROI negative in tests due to tough simulated competition.
Real-world results may vary.
"""


# For backwards compatibility
def auto_select_strategy(players: List, contest_type: str = 'gpp',
                         force_strategy: Optional[str] = None) -> Tuple[str, str]:
    """Legacy function for compatibility"""
    selector = StrategyAutoSelector()
    analysis = selector.analyze_slate_from_csv(players)
    return selector.select_strategy(analysis, contest_type, force_strategy)