#!/usr/bin/env python3
"""
BATTING ORDER & CORRELATION OPTIMIZATION SYSTEM
==============================================
FIXED VERSION: No multiplicative adjustments
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BattingOrderEnricher:
    """
    Enriches players with confirmed batting order data
    FIXED: Stores data only, no multiplication
    """

    def __init__(self, confirmation_system=None):
        """
        Initialize with existing confirmation system

        Args:
            confirmation_system: SmartConfirmationSystem instance
        """
        self.confirmation_system = confirmation_system

        # Batting order multipliers for REFERENCE ONLY - NOT APPLIED HERE
        self.batting_order_multipliers = {
            1: 1.15,  # Leadoff: ~15% more PAs than average
            2: 1.10,  # 2-hole: ~10% more PAs
            3: 1.08,  # 3-hole: High RBI opportunities
            4: 1.05,  # Cleanup: RBI opportunities balance fewer PAs
            5: 1.02,  # 5-hole: Slightly above average
            6: 0.98,  # 6-hole: Slightly below average
            7: 0.95,  # 7-hole: ~5% fewer PAs
            8: 0.92,  # 8-hole: ~8% fewer PAs
            9: 0.90  # 9-hole: ~10% fewer PAs (NL) or worst hitter (AL)
        }

        # Cache for batting orders
        self.batting_order_cache = {}

    def enrich_with_batting_order(self, players: List) -> int:
        """
        FIXED: Enrich players with batting order data that WILL be used by scoring engine
        """
        if not self.confirmation_system:
            print("⚠️ No confirmation system available for batting order data")
            return 0

        print("🔢 Enriching with batting order data...")
        enriched_count = 0

        for player in players:
            if player.primary_position == 'P':
                continue  # Skip pitchers

            try:
                # Get confirmed lineup info
                team_lineup = None
                if hasattr(self.confirmation_system, 'confirmed_lineups'):
                    for lineup_data in self.confirmation_system.confirmed_lineups.values():
                        if player.team == lineup_data.get('team'):
                            team_lineup = lineup_data
                            break

                if not team_lineup:
                    continue

                # Find player in lineup
                batting_order = None
                lineup_list = team_lineup.get('lineup', [])

                for idx, lineup_player in enumerate(lineup_list, 1):
                    if self._fuzzy_match_player(player.name, lineup_player):
                        batting_order = idx
                        break

                if batting_order:
                    # FIXED: Set batting order on player - scoring engine will use this
                    player.batting_order = batting_order

                    # NO LONGER storing multiplier - let scoring engine calculate it
                    # This was the bug - we were storing but not using it

                    # Add to confirmation sources for tracking
                    if hasattr(player, 'confirmation_sources'):
                        player.confirmation_sources.append(f"batting_{batting_order}")

                    enriched_count += 1

                    # Log significant batting positions
                    if batting_order <= 3:
                        print(f"   🔥 {player.name} batting {batting_order} (top of order)")
                    elif batting_order >= 7:
                        print(f"   ❄️ {player.name} batting {batting_order} (bottom of order)")

            except Exception as e:
                logger.debug(f"Error processing batting order for {player.name}: {e}")
                continue

        print(f"✅ Batting order data set for {enriched_count} players")
        print("   Scoring engine will apply appropriate multipliers")
        return enriched_count

    def get_batting_position(self, player) -> Optional[int]:
        """Get player's batting position if available"""
        if hasattr(player, 'batting_order'):
            return player.batting_order
        return None


class CorrelationOptimizer:
    """
    Optimizes lineup correlations for stacking and game theory
    Integrates with OptimalLineupOptimizer for MILP constraints
    """

    def __init__(self):
        """Initialize correlation optimizer"""

        # Stack bonus multipliers (data-driven from historical correlation)
        self.stack_bonuses = {
            3: 0.05,  # 3 hitters: 5% bonus
            4: 0.08,  # 4 hitters: 8% bonus
            5: 0.12,  # 5+ hitters: 12% bonus
            'pitcher_stack': 0.03  # Additional 3% for pitcher + hitters
        }

        # Negative correlation penalties
        self.negative_correlations = {
            'opposing_pitcher': -0.10,  # Your hitters vs your pitcher
            'low_total_game': -0.05  # Stacking in low O/U games
        }

    def calculate_lineup_correlation_score(self, lineup: List, vegas_data: Dict = None) -> Tuple[float, Dict]:
        """
        FIXED: Calculate correlation bonuses using actual batting order data

        Returns:
            Tuple of (correlation_multiplier, details_dict)
        """
        correlation_score = 1.0
        details = {
            'stacks': [],
            'correlations': [],
            'penalties': []
        }

        # Group players by team
        team_groups = {}
        for player in lineup:
            if player.primary_position != 'P' and player.team:
                if player.team not in team_groups:
                    team_groups[player.team] = []
                team_groups[player.team].append(player)

        # Check each team group
        for team, players in team_groups.items():
            if len(players) >= 3:
                # This is a stack - check for batting order correlation
                batting_orders = []
                for p in players:
                    if hasattr(p, 'batting_order') and p.batting_order:
                        batting_orders.append((p.batting_order, p))

                if len(batting_orders) >= 2:
                    # Sort by batting order
                    batting_orders.sort(key=lambda x: x[0])

                    # Check for consecutive batters
                    consecutive_count = 1
                    max_consecutive = 1

                    for i in range(1, len(batting_orders)):
                        if batting_orders[i][0] - batting_orders[i - 1][0] == 1:
                            consecutive_count += 1
                            max_consecutive = max(max_consecutive, consecutive_count)
                        else:
                            consecutive_count = 1

                    # Apply correlation bonus based on consecutive batters
                    if max_consecutive >= 3:
                        bonus = self.stack_bonuses.get(3, 0.05)
                        correlation_score *= (1 + bonus)
                        details['stacks'].append({
                            'team': team,
                            'size': len(players),
                            'consecutive': max_consecutive,
                            'bonus': bonus,
                            'players': [p.name for _, p in batting_orders]
                        })
                        print(f"   ⚡ {team} stack: {max_consecutive} consecutive batters (+{bonus * 100:.0f}%)")
                    elif max_consecutive >= 2:
                        bonus = 0.03  # Smaller bonus for 2 consecutive
                        correlation_score *= (1 + bonus)
                        details['stacks'].append({
                            'team': team,
                            'size': len(players),
                            'consecutive': max_consecutive,
                            'bonus': bonus,
                            'players': [p.name for _, p in batting_orders]
                        })
                    else:
                        # Non-consecutive stack gets smaller bonus
                        bonus = 0.02
                        correlation_score *= (1 + bonus)
                        details['stacks'].append({
                            'team': team,
                            'size': len(players),
                            'consecutive': 0,
                            'bonus': bonus,
                            'players': [p.name for p in players]
                        })

        # Check for negative correlations
        pitchers = [p for p in lineup if p.primary_position == 'P']
        hitters = [p for p in lineup if p.primary_position != 'P']

        for pitcher in pitchers:
            if pitcher.opponent:
                # Count opposing hitters
                opp_hitters = [h for h in hitters if h.team == pitcher.opponent]
                if opp_hitters:
                    penalty = self.negative_correlations['opposing_pitcher']
                    correlation_score *= (1 + penalty)  # penalty is negative
                    details['penalties'].append({
                        'type': 'opposing_pitcher',
                        'pitcher': pitcher.name,
                        'opposing_hitters': [h.name for h in opp_hitters],
                        'penalty': penalty
                    })
                    print(f"   ⚠️ {pitcher.name} facing {len(opp_hitters)} own hitters ({penalty * 100:.0f}%)")

        # Low total game penalty
        if vegas_data:
            for team, players in team_groups.items():
                if len(players) >= 3:  # Stack in low-total game
                    team_vegas = vegas_data.get(team, {})
                    game_total = team_vegas.get('game_total', 9.0)

                    if game_total < 8.0:
                        penalty = self.negative_correlations['low_total_game']
                        correlation_score *= (1 + penalty)
                        details['penalties'].append({
                            'type': 'low_total_stack',
                            'team': team,
                            'game_total': game_total,
                            'penalty': penalty
                        })
                        print(f"   ⚠️ {team} stack in low total game ({game_total}) ({penalty * 100:.0f}%)")

        return correlation_score, details

    def _teams_playing_against_each_other(self, team1: str, team2: str, vegas_data: Dict) -> bool:
        """Check if two teams are playing against each other"""
        if not vegas_data:
            return False

        # Check if teams are opponents in Vegas data
        if team1 in vegas_data and team2 in vegas_data:
            team1_opponent = vegas_data[team1].get('opponent', '')
            team2_opponent = vegas_data[team2].get('opponent', '')

            return team1_opponent == team2 or team2_opponent == team1

        return False

    def apply_correlation_adjustments(self, lineup: List, vegas_data: Dict = None) -> List:
        """
        Apply correlation-based adjustments to lineup scores
        NOTE: This modifies scores for display/ranking only, not optimization

        Args:
            lineup: List of players in the lineup
            vegas_data: Vegas lines data

        Returns:
            Lineup with adjusted correlation scores
        """
        # Calculate correlation score
        correlation_mult, details = self.calculate_lineup_correlation_score(lineup, vegas_data)

        # Apply to each player for display purposes
        for player in lineup:
            if hasattr(player, 'enhanced_score'):
                # Store original score
                if not hasattr(player, '_pre_correlation_score'):
                    player._pre_correlation_score = player.enhanced_score

                # Apply correlation multiplier
                player.correlation_adjusted_score = player.enhanced_score * correlation_mult

                # Add correlation details
                player._correlation_details = details

        # Log correlation summary
        if correlation_mult != 1.0:
            print(f"\n📊 Lineup correlation multiplier: {correlation_mult:.3f}")
            if details['stacks']:
                print("   Stacks:")
                for stack in details['stacks']:
                    print(f"     - {stack['team']}: {stack['size']} players, "
                          f"{stack['consecutive']} consecutive (+{stack['bonus'] * 100:.1f}%)")
            if details['penalties']:
                print("   Penalties:")
                for penalty in details['penalties']:
                    print(f"     - {penalty['type']}: {penalty['penalty'] * 100:.1f}%")

        return lineup

    def get_stacking_constraints(self, players: List) -> Dict:
        """
        Get stacking constraints for optimizer

        Args:
            players: List of available players

        Returns:
            Dictionary of stacking constraints
        """
        constraints = {
            'min_stack_size': 3,
            'max_stacks': 2,
            'pitcher_stack_allowed': True,
            'avoid_low_total_games': True
        }

        # Identify teams with enough players for stacking
        team_players = {}
        for player in players:
            if player.primary_position != 'P' and hasattr(player, 'is_eligible_for_selection'):
                if player.is_eligible_for_selection('bulletproof'):
                    team = player.team
                    if team not in team_players:
                        team_players[team] = []
                    team_players[team].append(player)

        # Find teams with good stacking potential
        good_stack_teams = []
        for team, team_players_list in team_players.items():
            hitter_count = sum(1 for p in team_players_list if p.primary_position != 'P')
            if hitter_count >= 3:
                good_stack_teams.append(team)

        constraints['good_stack_teams'] = good_stack_teams

        return constraints


def integrate_batting_order_correlation(core_instance):
    """
    Integrate batting order and correlation systems into BulletproofDFSCore

    Args:
        core_instance: Instance of BulletproofDFSCore
    """
    # Create instances
    if hasattr(core_instance, 'confirmation_system') and core_instance.confirmation_system:
        batting_enricher = BattingOrderEnricher(core_instance.confirmation_system)
    else:
        batting_enricher = BattingOrderEnricher()

    correlation_optimizer = CorrelationOptimizer()

    # Add to core
    core_instance.batting_enricher = batting_enricher
    core_instance.correlation_optimizer = correlation_optimizer

    # Add enrichment method
    def enrich_with_batting_order(self):
        """Enrich players with batting order data"""
        if hasattr(self, 'batting_enricher'):
            eligible = [p for p in self.players if p.is_eligible_for_selection(self.optimization_mode)]
            return self.batting_enricher.enrich_with_batting_order(eligible)
        return 0

    # Add correlation method
    def apply_lineup_correlations(self, lineup):
        """Apply correlation adjustments to lineup"""
        if hasattr(self, 'correlation_optimizer') and hasattr(self, 'vegas_lines'):
            vegas_data = self.vegas_lines.lines if self.vegas_lines else None
            return self.correlation_optimizer.apply_correlation_adjustments(lineup, vegas_data)
        return lineup

    # Bind methods
    import types
    core_instance.enrich_with_batting_order = types.MethodType(enrich_with_batting_order, core_instance)
    core_instance.apply_lineup_correlations = types.MethodType(apply_lineup_correlations, core_instance)

    print("✅ Batting Order & Correlation Systems integrated")


# Export main components
__all__ = ['BattingOrderEnricher', 'CorrelationOptimizer', 'integrate_batting_order_correlation']