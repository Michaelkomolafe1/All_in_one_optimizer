#!/usr/bin/env python3
"""
BATTING ORDER & CORRELATION OPTIMIZATION SYSTEM
==============================================
Integrates batting order confirmation and stack correlation bonuses
Works seamlessly with existing DFS optimizer components
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BattingOrderEnricher:
    """
    Enriches players with confirmed batting order data
    Integrates with SmartConfirmationSystem for lineup data
    """

    def __init__(self, confirmation_system=None):
        """
        Initialize with existing confirmation system

        Args:
            confirmation_system: SmartConfirmationSystem instance
        """
        self.confirmation_system = confirmation_system

        # Batting order multipliers based on historical plate appearances
        # Data-driven from MLB averages
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
        Enrich players with batting order adjustments

        Args:
            players: List of player objects

        Returns:
            Number of players enriched with batting order
        """
        if not self.confirmation_system:
            print("⚠️ No confirmation system available for batting order")
            return 0

        enriched_count = 0

        print("🔢 Enriching players with batting order data...")

        # Get confirmed lineups from confirmation system
        confirmed_lineups = self.confirmation_system.confirmed_lineups

        if not confirmed_lineups:
            print("⚠️ No confirmed lineups available")
            return 0

        for player in players:
            try:
                # Skip pitchers
                if player.primary_position == 'P':
                    continue

                # Skip if not eligible
                if hasattr(player, 'is_eligible_for_selection'):
                    if not player.is_eligible_for_selection('bulletproof'):
                        continue

                # Get player's team lineup
                team = player.team
                if team not in confirmed_lineups:
                    continue

                # Find player in lineup
                team_lineup = confirmed_lineups[team]
                batting_order = None

                for lineup_player in team_lineup:
                    # Use confirmation system's name matching
                    if self.confirmation_system.data_system.match_player_names(
                            player.name, lineup_player.get('name', '')
                    ):
                        batting_order = lineup_player.get('order', lineup_player.get('batting_order'))
                        break

                if batting_order and batting_order > 0:
                    # Apply batting order adjustment
                    old_score = player.enhanced_score
                    multiplier = self.batting_order_multipliers.get(batting_order, 1.0)

                    # Apply adjustment
                    player.enhanced_score *= multiplier

                    # Store batting order info
                    player.batting_order = batting_order
                    player.batting_order_multiplier = multiplier

                    # Add to player status
                    if hasattr(player, 'confirmation_sources'):
                        player.confirmation_sources.append(f"batting_{batting_order}")

                    enriched_count += 1

                    # Log significant changes
                    if batting_order <= 2 or batting_order >= 8:
                        print(f"   {player.name} batting {batting_order}: "
                              f"{old_score:.1f} → {player.enhanced_score:.1f} "
                              f"({multiplier:.0%} adjustment)")

            except Exception as e:
                logger.debug(f"Error processing batting order for {player.name}: {e}")
                continue

        print(f"✅ Batting order applied to {enriched_count} players")
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
        Calculate correlation bonuses/penalties for a lineup

        Args:
            lineup: List of player objects
            vegas_data: Optional Vegas lines data

        Returns:
            Tuple of (correlation_score, correlation_details)
        """
        correlation_score = 0.0
        correlation_details = {
            'stacks': [],
            'bonuses': [],
            'penalties': [],
            'total_adjustment': 0.0
        }

        # Group players by team
        team_players = {}
        pitchers = []

        for player in lineup:
            if player.primary_position == 'P':
                pitchers.append(player)
            else:
                team = player.team
                if team not in team_players:
                    team_players[team] = []
                team_players[team].append(player)

        # Calculate stacking bonuses
        for team, players in team_players.items():
            stack_size = len(players)

            if stack_size >= 3:
                # Base stack bonus
                bonus = self.stack_bonuses.get(min(stack_size, 5), 0)
                correlation_score += bonus

                # Check if we have team's pitcher too
                has_team_pitcher = any(p.team == team for p in pitchers)
                if has_team_pitcher and stack_size >= 3:
                    pitcher_bonus = self.stack_bonuses['pitcher_stack']
                    correlation_score += pitcher_bonus
                    bonus += pitcher_bonus

                # Check game environment
                if vegas_data and team in vegas_data:
                    team_total = vegas_data[team].get('total', 9.0)

                    # Extra bonus for high-scoring games
                    if team_total > 10:
                        environment_bonus = 0.02
                        correlation_score += environment_bonus
                        bonus += environment_bonus
                    # Penalty for low-scoring games
                    elif team_total < 8:
                        environment_penalty = self.negative_correlations['low_total_game']
                        correlation_score += environment_penalty
                        correlation_details['penalties'].append({
                            'type': 'low_total_stack',
                            'team': team,
                            'penalty': environment_penalty
                        })

                correlation_details['stacks'].append({
                    'team': team,
                    'size': stack_size,
                    'players': [p.name for p in players],
                    'has_pitcher': has_team_pitcher,
                    'bonus': bonus
                })
                correlation_details['bonuses'].append({
                    'type': f'{stack_size}_player_stack',
                    'team': team,
                    'bonus': bonus
                })

        # Check negative correlations
        for pitcher in pitchers:
            # Check if we have opposing hitters
            opposing_hitters = []
            for team, players in team_players.items():
                # Need to check if team faces this pitcher
                # This would require game matchup data
                if self._teams_playing_against_each_other(pitcher.team, team, vegas_data):
                    opposing_hitters.extend(players)

            if opposing_hitters:
                penalty = self.negative_correlations['opposing_pitcher'] * len(opposing_hitters)
                correlation_score += penalty
                correlation_details['penalties'].append({
                    'type': 'opposing_pitcher',
                    'pitcher': pitcher.name,
                    'opposing_hitters': [h.name for h in opposing_hitters],
                    'penalty': penalty
                })

        correlation_details['total_adjustment'] = correlation_score

        return correlation_score, correlation_details

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
        Apply correlation adjustments to lineup players

        Args:
            lineup: List of player objects
            vegas_data: Optional Vegas lines data

        Returns:
            Adjusted lineup
        """
        correlation_score, details = self.calculate_lineup_correlation_score(lineup, vegas_data)

        if abs(correlation_score) < 0.01:
            return lineup

        # Apply correlation bonus to all players in lineup
        # This represents the synergy effect
        for player in lineup:
            if not hasattr(player, 'original_enhanced_score'):
                player.original_enhanced_score = player.enhanced_score

            # Apply correlation adjustment
            player.enhanced_score = player.original_enhanced_score * (1 + correlation_score)
            player.correlation_adjustment = correlation_score

        # Log significant correlations
        if details['stacks']:
            print(f"\n🔥 Stack Correlations Applied:")
            for stack in details['stacks']:
                print(f"   {stack['team']}: {stack['size']} players "
                      f"(+{stack['bonus']:.1%} bonus)")
                if stack['has_pitcher']:
                    print(f"      ⚾ Includes team pitcher")

        if details['penalties']:
            print(f"\n⚠️ Negative Correlations:")
            for penalty in details['penalties']:
                print(f"   {penalty['type']}: {penalty['penalty']:.1%}")

        return lineup

    def get_optimal_stacking_constraints(self, players: List, max_stack_size: int = 5) -> Dict:
        """
        Get stacking constraints for optimizer

        Args:
            players: List of available players
            max_stack_size: Maximum players from one team

        Returns:
            Dict of constraints for optimizer
        """
        # Group players by team
        team_players = {}
        for player in players:
            if player.team not in team_players:
                team_players[player.team] = []
            team_players[player.team].append(player)

        constraints = {
            'min_teams': 3,  # At least 3 different teams
            'max_from_team': max_stack_size,
            'preferred_stack_sizes': [3, 4],  # Optimal stack sizes
            'avoid_single_players': True  # Avoid 1 player from a team
        }

        # Find teams with enough players for good stacks
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