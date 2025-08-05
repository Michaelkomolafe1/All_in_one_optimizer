#!/usr/bin/env python3
"""
STRATEGY AUTO-SELECTOR V2
========================
Auto-detects slate size based on GAMES, not player count
Selects #1 strategy for each slate/contest combination
"""

import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class StrategyAutoSelector:
    """Automatically selects optimal strategy based on slate characteristics"""

    def __init__(self):
        # Define #1 strategies based on test results
        self.strategies = {
            'cash': {
                'small': 'projection_monster_enhanced',  # Enhanced version
                'medium': 'pitcher_dominance_enhanced',  # Enhanced version
                'large': 'pitcher_dominance_enhanced'  # Enhanced version
            },
            'gpp': {
                'small': 'tournament_winner_gpp',  # NEW strategy!
                'medium': 'tournament_winner_gpp',  # NEW strategy!
                'large': 'tournament_winner_gpp'  # NEW strategy!
            }
        }

        # Slate size thresholds based on GAMES
        self.game_thresholds = {
            'small': (1, 4),  # 1-4 games (afternoon slate, small evening)
            'medium': (5, 9),  # 5-9 games (main slate on light days)
            'large': (10, 99)  # 10+ games (full evening slate)
        }

        # Store last analysis for GUI
        self.last_analysis = None

    def analyze_slate_from_csv(self, players: List) -> Dict:
        """Analyze slate characteristics from player data"""

        # Detect unique games
        games = set()
        teams = set()
        game_info = defaultdict(lambda: {'teams': set(), 'total': 0})

        for player in players:
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

        # Determine slate size based on games
        slate_size = self._determine_slate_size_by_games(actual_game_count)

        # Get additional metrics
        total_players = len(players)
        confirmed_count = len([p for p in players if getattr(p, 'is_confirmed', False)])
        pitchers = [p for p in players if p.primary_position == 'P']

        # Calculate averages
        avg_game_total = 0
        if game_info:
            totals = [info['total'] for info in game_info.values() if info['total'] > 0]
            avg_game_total = sum(totals) / len(totals) if totals else 9.0

        # Check if showdown
        is_showdown = False
        positions = {p.primary_position for p in players}
        if 'CPT' in positions or ('UTIL' in positions and len(positions) <= 2):
            is_showdown = True
            slate_size = 'showdown'

        analysis = {
            'slate_size': slate_size,
            'game_count': actual_game_count,
            'total_players': total_players,
            'confirmed_players': confirmed_count,
            'pitcher_count': len(pitchers),
            'team_count': len(teams),
            'avg_game_total': avg_game_total,
            'is_showdown': is_showdown,
            'high_total_games': len([t for t in game_info.values() if t['total'] > 10])
        }

        # Store for GUI access
        self.last_analysis = analysis

        # Log analysis
        logger.info("=" * 60)
        logger.info("SLATE ANALYSIS COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Format: {'SHOWDOWN' if is_showdown else 'CLASSIC'}")
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
        Select the #1 strategy based on slate analysis

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
            strategy = self.top_strategies['showdown']['all']
            reason = f"Showdown detected - using {strategy}"
            logger.info(reason)
            return strategy, reason

        # Normalize contest type
        contest_type = contest_type.lower()
        if contest_type in ['50-50', '50/50', 'double-up', 'cash game']:
            contest_type = 'cash'
        elif contest_type not in ['cash', 'gpp']:
            contest_type = 'gpp'  # Default to GPP

        # Get the #1 strategy
        strategy = self.top_strategies[contest_type][slate_size]

        # Build reason
        game_count = slate_analysis['game_count']
        if contest_type == 'cash':
            win_rates = {
                'projection_monster': '54.0%',
                'pitcher_dominance': '55-57%'
            }
            metric = f"{win_rates.get(strategy, 'High')} win rate"
        else:
            roi_values = {
                'correlation_value': '+24.7%',
                'smart_stack': '+23.7%',
                'matchup_leverage_stack': '+40.1%'
            }
            metric = f"{roi_values.get(strategy, 'High')} ROI"

        reason = f"{game_count} games = {slate_size} slate → {strategy} ({metric})"

        logger.info(f"Selected Strategy: {strategy}")
        logger.info(f"Reason: {reason}")

        return strategy, reason

    def get_all_strategies(self) -> Dict[str, List[str]]:
        """Get all available strategies organized by type"""
        return {
            'Auto-Select': ['auto'],
            'Cash Strategies': [
                'projection_monster',
                'pitcher_dominance',
                'elite_cash',
                'value_floor',
                'balanced_sharp'
            ],
            'GPP Strategies': [
                'correlation_value',
                'smart_stack',
                'matchup_leverage_stack',
                'ceiling_stack',
                'stars_and_scrubs_extreme'
            ],
            'Experimental': [
                'elite_hybrid_gpp',
                'ultimate_cash_hybrid',
                'single_game_hammer'
            ]
        }