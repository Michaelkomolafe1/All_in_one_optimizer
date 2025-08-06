#!/usr/bin/env python3
"""
SMART ENRICHMENT MANAGER
========================
Enriches players based on:
1. Slate size (small/medium/large)
2. Strategy being used
3. Contest type (cash/gpp)

This ensures we only fetch and calculate what's actually needed!
"""

import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentProfile:
    """Defines what enrichments a strategy needs"""
    name: str
    needs_vegas: bool = True
    needs_statcast: bool = False
    needs_ownership: bool = False
    needs_weather: bool = False
    needs_batting_order: bool = True
    needs_recent_form: bool = True
    needs_consistency: bool = False
    needs_matchup: bool = True
    needs_park_factors: bool = True
    statcast_priority_players: int = 0  # How many top players to get stats for

    # Specific stat requirements
    needs_barrel_rate: bool = False
    needs_k_rate: bool = False
    needs_xwoba: bool = False
    needs_hard_hit: bool = False


class SmartEnrichmentManager:
    """
    Manages slate and strategy-specific enrichment
    Only enriches what's needed for the current optimization
    """

    def __init__(self):
        # Define enrichment profiles for each strategy
        self.strategy_profiles = self._build_strategy_profiles()

        # Track what's been enriched
        self.enrichment_cache = {
            'slate_id': None,
            'enriched_players': set(),
            'enrichment_types': set()
        }

        # Available enrichment sources
        self.enrichment_sources = {
            'vegas': None,
            'statcast': None,
            'weather': None,
            'ownership': None,
            'confirmations': None
        }

    def _build_strategy_profiles(self) -> Dict[str, EnrichmentProfile]:
        """Define what each strategy needs - MATCHED TO YOUR ACTUAL STRATEGIES"""

        profiles = {
            # ==========================
            # YOUR PRIMARY CASH STRATEGIES (from strategy_selector.py)
            # ==========================
            'pitcher_dominance': EnrichmentProfile(
                name='pitcher_dominance',
                needs_statcast=True,  # Need K-rates for pitchers
                needs_k_rate=True,
                needs_consistency=True,
                needs_ownership=False,  # Don't care about ownership in cash
                statcast_priority_players=20  # Only top pitchers
            ),

            'projection_monster': EnrichmentProfile(
                name='projection_monster',
                needs_consistency=True,
                needs_recent_form=True,
                needs_statcast=False,  # Just use projections
                needs_ownership=False
            ),

            # ==========================
            # YOUR SIMULATION CASH STRATEGIES (from robust_dfs_simulator.py)
            # ==========================
            'value_floor': EnrichmentProfile(
                name='value_floor',
                needs_consistency=True,
                needs_recent_form=True,
                needs_matchup=True,
                needs_statcast=False,
                needs_ownership=False
            ),

            'chalk_plus': EnrichmentProfile(
                name='chalk_plus',
                needs_ownership=True,  # Needs to know who's chalk
                needs_recent_form=True,
                needs_consistency=True,
                needs_statcast=False
            ),

            'matchup_optimal': EnrichmentProfile(
                name='matchup_optimal',
                needs_matchup=True,  # Core requirement
                needs_vegas=True,
                needs_park_factors=True,
                needs_weather=True,
                needs_statcast=True,
                statcast_priority_players=30
            ),

            'hot_players_only': EnrichmentProfile(
                name='hot_players_only',
                needs_recent_form=True,  # Critical
                needs_statcast=True,
                statcast_priority_players=50,  # Need recent stats
                needs_consistency=False
            ),

            'woba_warriors': EnrichmentProfile(
                name='woba_warriors',
                needs_statcast=True,
                needs_xwoba=True,  # Core metric
                statcast_priority_players=60,
                needs_barrel_rate=True
            ),

            'vegas_sharp': EnrichmentProfile(
                name='vegas_sharp',
                needs_vegas=True,  # Primary focus
                needs_batting_order=True,
                needs_ownership=False,
                needs_statcast=False
            ),

            'balanced_sharp': EnrichmentProfile(
                name='balanced_sharp',
                needs_vegas=True,
                needs_statcast=True,
                needs_recent_form=True,
                needs_consistency=True,
                statcast_priority_players=40
            ),

            # ==========================
            # YOUR PRIMARY GPP STRATEGIES (from strategy_selector.py)
            # ==========================
            'tournament_winner_gpp': EnrichmentProfile(
                name='tournament_winner_gpp',
                needs_ownership=True,  # Critical for GPP
                needs_statcast=True,
                needs_barrel_rate=True,  # Upside metrics
                needs_hard_hit=True,
                needs_consistency=False,  # Don't care about floor
                statcast_priority_players=50
            ),

            'correlation_value': EnrichmentProfile(
                name='correlation_value',
                needs_vegas=True,  # Team totals critical
                needs_batting_order=True,  # Stack positions
                needs_ownership=True,
                needs_statcast=True,
                needs_barrel_rate=True,
                statcast_priority_players=40
            ),

            'smart_stack': EnrichmentProfile(
                name='smart_stack',
                needs_vegas=True,
                needs_batting_order=True,
                needs_ownership=True,
                needs_weather=True,  # Weather affects stacks
                needs_statcast=False  # Focus on correlation
            ),

            'matchup_leverage_stack': EnrichmentProfile(
                name='matchup_leverage_stack',
                needs_matchup=True,
                needs_vegas=True,
                needs_batting_order=True,
                needs_statcast=True,
                needs_k_rate=True,  # Opposing pitcher K-rate
                statcast_priority_players=30
            ),

            'truly_smart_stack': EnrichmentProfile(
                name='truly_smart_stack',
                needs_vegas=True,
                needs_batting_order=True,
                needs_ownership=True,
                needs_weather=True,
                needs_statcast=True,
                needs_barrel_rate=True,
                needs_xwoba=True,
                statcast_priority_players=60  # Comprehensive
            ),

            # ==========================
            # YOUR SIMULATION GPP STRATEGIES (from robust_dfs_simulator.py)
            # ==========================
            'stars_and_scrubs_extreme': EnrichmentProfile(
                name='stars_and_scrubs_extreme',
                needs_ownership=True,
                needs_vegas=True,
                needs_statcast=False,
                needs_consistency=False
            ),

            'cold_player_leverage': EnrichmentProfile(
                name='cold_player_leverage',
                needs_recent_form=True,  # To find cold players
                needs_ownership=True,  # Low owned
                needs_statcast=True,
                statcast_priority_players=30
            ),

            'woba_explosion': EnrichmentProfile(
                name='woba_explosion',
                needs_statcast=True,
                needs_xwoba=True,
                needs_barrel_rate=True,
                statcast_priority_players=80  # Need lots of stats
            ),

            'rising_team_stack': EnrichmentProfile(
                name='rising_team_stack',
                needs_vegas=True,
                needs_recent_form=True,
                needs_batting_order=True,
                needs_statcast=True,
                statcast_priority_players=40
            ),

            'iso_power_stack': EnrichmentProfile(
                name='iso_power_stack',
                needs_statcast=True,
                needs_hard_hit=True,
                needs_barrel_rate=True,
                statcast_priority_players=50
            ),

            'leverage_theory': EnrichmentProfile(
                name='leverage_theory',
                needs_ownership=True,  # Core requirement
                needs_vegas=True,
                needs_statcast=False
            ),

            'ceiling_stack': EnrichmentProfile(
                name='ceiling_stack',
                needs_vegas=True,
                needs_batting_order=True,
                needs_weather=True,
                needs_park_factors=True,
                needs_statcast=True,
                needs_barrel_rate=True,
                statcast_priority_players=60
            ),

            'barrel_rate_correlation': EnrichmentProfile(
                name='barrel_rate_correlation',
                needs_statcast=True,
                needs_barrel_rate=True,  # Primary focus
                needs_batting_order=True,
                statcast_priority_players=70
            ),

            'multi_stack_mayhem': EnrichmentProfile(
                name='multi_stack_mayhem',
                needs_vegas=True,
                needs_batting_order=True,
                needs_ownership=True,
                needs_statcast=False  # Focus on stacks not stats
            ),

            'pitcher_stack_combo': EnrichmentProfile(
                name='pitcher_stack_combo',
                needs_vegas=True,
                needs_batting_order=True,
                needs_k_rate=True,  # For pitcher
                needs_statcast=True,
                statcast_priority_players=30
            ),

            'vegas_explosion': EnrichmentProfile(
                name='vegas_explosion',
                needs_vegas=True,  # Primary requirement
                needs_batting_order=True,
                needs_weather=True,
                needs_statcast=False
            ),

            'high_k_pitcher_fade': EnrichmentProfile(
                name='high_k_pitcher_fade',
                needs_k_rate=True,  # To identify high-K pitchers
                needs_ownership=True,  # Fade popular ones
                needs_statcast=True,
                statcast_priority_players=20
            ),

            # ==========================
            # OTHER STRATEGIES FROM YOUR CODE
            # ==========================
            'multi_stack': EnrichmentProfile(
                name='multi_stack',
                needs_vegas=True,
                needs_batting_order=True,
                needs_ownership=False,
                needs_statcast=False
            ),

            'game_theory_leverage': EnrichmentProfile(
                name='game_theory_leverage',
                needs_ownership=True,
                needs_vegas=True,
                needs_statcast=False
            ),

            'contrarian_correlation': EnrichmentProfile(
                name='contrarian_correlation',
                needs_ownership=True,  # Find low-owned
                needs_vegas=True,
                needs_batting_order=True,
                needs_statcast=False
            )
        }  # ADD THIS CLOSING BRACE!

        return profiles

    def get_enrichment_requirements(self,
                                    slate_size: str,
                                    strategy: str,
                                    contest_type: str) -> EnrichmentProfile:
        """
        Get enrichment requirements based on slate and strategy

        Args:
            slate_size: 'small', 'medium', or 'large'
            strategy: Strategy name
            contest_type: 'cash' or 'gpp'

        Returns:
            EnrichmentProfile with requirements
        """
        # Get base profile for strategy
        profile = self.strategy_profiles.get(strategy)

        if not profile:
            # Default profile if strategy not defined
            logger.warning(f"No profile for strategy '{strategy}', using intelligent defaults")

            # Create smart defaults based on strategy name and contest type
            if contest_type == 'cash':
                # Cash defaults: focus on consistency
                profile = EnrichmentProfile(
                    name=strategy,
                    needs_vegas=True,
                    needs_batting_order=True,
                    needs_recent_form=True,
                    needs_consistency=True,
                    needs_matchup=True,
                    needs_ownership=False,  # Don't need ownership for cash
                    needs_statcast=False,  # Usually not critical for cash
                    statcast_priority_players=20
                )
            else:  # GPP
                # GPP defaults: focus on upside and ownership
                profile = EnrichmentProfile(
                    name=strategy,
                    needs_vegas=True,
                    needs_batting_order=True,
                    needs_ownership=True,  # Always need ownership for GPP
                    needs_recent_form=True,
                    needs_statcast=True,  # Usually want stats for GPP
                    needs_barrel_rate=True,
                    needs_consistency=False,
                    statcast_priority_players=40
                )

            logger.info(f"Created default {contest_type} profile for '{strategy}'")

        # Adjust based on slate size
        profile = self._adjust_for_slate_size(profile, slate_size, contest_type)

        return profile

    def _adjust_for_slate_size(self,
                               profile: EnrichmentProfile,
                               slate_size: str,
                               contest_type: str) -> EnrichmentProfile:
        """Adjust enrichment based on slate size"""

        if slate_size == 'small':
            # Small slates (2-4 games)
            # - Less data needed (fewer players)
            # - Matchups matter more
            # - Weather less important (fewer parks)
            profile.needs_weather = False
            if profile.statcast_priority_players > 0:
                profile.statcast_priority_players = min(20, profile.statcast_priority_players)

            # In small slates, individual matchups critical
            profile.needs_matchup = True

        elif slate_size == 'medium':
            # Medium slates (5-9 games)
            # - Balanced approach
            # - All data useful
            pass  # Use defaults

        else:  # large
            # Large slates (10+ games)
            # - Need more data to differentiate
            # - Ownership crucial for GPP
            # - More stats needed
            if contest_type == 'gpp':
                profile.needs_ownership = True
                profile.needs_statcast = True
                if profile.statcast_priority_players > 0:
                    profile.statcast_priority_players = min(80, profile.statcast_priority_players * 2)

            # Weather matters more with more parks
            profile.needs_weather = True

        return profile

    def enrich_players(self,
                       players: List,
                       slate_size: str,
                       strategy: str,
                       contest_type: str) -> List:
        """
        Main enrichment method - only enriches what's needed

        Args:
            players: List of UnifiedPlayer objects
            slate_size: 'small', 'medium', or 'large'
            strategy: Strategy name
            contest_type: 'cash' or 'gpp'

        Returns:
            List of enriched players
        """
        logger.info(f"=== SMART ENRICHMENT ===")
        logger.info(f"Slate: {slate_size}, Strategy: {strategy}, Contest: {contest_type}")

        # Get requirements for this optimization
        profile = self.get_enrichment_requirements(slate_size, strategy, contest_type)

        logger.info(f"Enrichment profile for {strategy}:")
        logger.info(f"  Vegas: {profile.needs_vegas}")
        logger.info(f"  Statcast: {profile.needs_statcast} (top {profile.statcast_priority_players})")
        logger.info(f"  Ownership: {profile.needs_ownership}")
        logger.info(f"  Weather: {profile.needs_weather}")

        enrichment_stats = {
            'vegas': 0,
            'statcast': 0,
            'ownership': 0,
            'weather': 0,
            'batting_order': 0,
            'recent_form': 0
        }

        # Sort players by salary for prioritization
        sorted_players = sorted(players, key=lambda p: p.salary, reverse=True)

        # ENRICHMENT PHASE 1: Vegas Data
        if profile.needs_vegas and self.enrichment_sources['vegas']:
            logger.info("Enriching with Vegas data...")
            for player in players:
                if self._enrich_vegas(player):
                    enrichment_stats['vegas'] += 1

        # ENRICHMENT PHASE 2: Batting Order
        if profile.needs_batting_order and self.enrichment_sources['confirmations']:
            logger.info("Enriching with batting orders...")
            for player in players:
                if self._enrich_batting_order(player):
                    enrichment_stats['batting_order'] += 1

        # ENRICHMENT PHASE 3: Statcast (only for priority players)
        if profile.needs_statcast and self.enrichment_sources['statcast']:
            logger.info(f"Enriching top {profile.statcast_priority_players} with Statcast...")

            # Only get stats for top N players by salary
            priority_players = sorted_players[:profile.statcast_priority_players]

            for player in priority_players:
                if self._enrich_statcast(player, profile):
                    enrichment_stats['statcast'] += 1

        # ENRICHMENT PHASE 4: Ownership
        if profile.needs_ownership and self.enrichment_sources['ownership']:
            logger.info("Enriching with ownership projections...")
            for player in players:
                if self._enrich_ownership(player):
                    enrichment_stats['ownership'] += 1

        # ENRICHMENT PHASE 5: Weather
        if profile.needs_weather and self.enrichment_sources['weather']:
            logger.info("Enriching with weather data...")
            for player in players:
                if self._enrich_weather(player):
                    enrichment_stats['weather'] += 1

        # ENRICHMENT PHASE 6: Recent Form
        if profile.needs_recent_form:
            logger.info("Calculating recent form...")
            self._calculate_recent_form(players, profile, contest_type)
            enrichment_stats['recent_form'] = len(players)

        # ENRICHMENT PHASE 7: Consistency
        if profile.needs_consistency:
            logger.info("Calculating consistency scores...")
            self._calculate_consistency(players, contest_type)

        # Log enrichment summary
        logger.info("=== ENRICHMENT COMPLETE ===")
        for key, count in enrichment_stats.items():
            if count > 0:
                logger.info(f"  {key}: {count} players")

        return players

    def _enrich_vegas(self, player) -> bool:
        """Enrich with Vegas data"""
        try:
            vegas_data = self.enrichment_sources['vegas'].get_data(player.team)
            if vegas_data:
                player.implied_team_score = vegas_data.get('implied_total', 4.5)
                player.game_total = vegas_data.get('game_total', 9.0)
                player.team_total = player.implied_team_score
                return True
        except:
            pass
        return False

    def _enrich_batting_order(self, player) -> bool:
        """Enrich with batting order"""
        try:
            confirmations = self.enrichment_sources['confirmations']
            order = confirmations.get_batting_order(player.name, player.team)
            if order:
                player.batting_order = order
                return True
        except:
            pass
        return False

    def _enrich_statcast(self, player, profile: EnrichmentProfile) -> bool:
        """Enrich with Statcast data based on what's needed"""
        try:
            statcast = self.enrichment_sources['statcast']
            stats = statcast.get_stats(player.name)

            if stats:
                # Only get the stats this strategy needs
                if profile.needs_barrel_rate:
                    player.barrel_rate = stats.get('barrel_rate', 0)

                if profile.needs_k_rate:
                    if player.is_pitcher:
                        player.k_rate = stats.get('k_rate', 20)
                    else:
                        player.k_rate = stats.get('k_rate', 20)

                if profile.needs_xwoba:
                    player.xwoba = stats.get('xwoba', 0.320)
                    player.woba = stats.get('woba', 0.320)
                    player.xwoba_diff = player.xwoba - player.woba

                if profile.needs_hard_hit:
                    player.hard_hit_rate = stats.get('hard_hit_rate', 40)

                return True
        except:
            pass
        return False

    def _enrich_ownership(self, player) -> bool:
        """Enrich with ownership projections"""
        try:
            ownership = self.enrichment_sources['ownership'].get_projection(player.name)
            if ownership:
                player.projected_ownership = ownership
                player.ownership_projection = ownership
                return True
        except:
            pass

        # Default ownership
        if player.salary > 9000:
            player.projected_ownership = 20
        elif player.salary > 7000:
            player.projected_ownership = 15
        elif player.salary > 5000:
            player.projected_ownership = 10
        else:
            player.projected_ownership = 5

        return True

    def _enrich_weather(self, player) -> bool:
        """Enrich with weather data"""
        try:
            weather = self.enrichment_sources['weather'].get_weather(player.team)
            if weather:
                player.weather_impact = weather.get('impact', 1.0)
                player.wind_speed = weather.get('wind_speed', 5)
                player.temperature = weather.get('temperature', 72)
                return True
        except:
            pass
        return False

    def _calculate_recent_form(self, players: List, profile: EnrichmentProfile, contest_type: str):
        """Calculate recent form based on strategy needs"""
        for player in players:
            # For players we got statcast data for
            if hasattr(player, 'recent_stats'):
                # Use actual recent performance
                player.recent_form = player.recent_stats.get('form_score', 1.0)
            else:
                # Estimate based on salary and position
                if contest_type == 'cash':
                    # Cash: Prefer consistent players
                    if player.salary >= 8000:
                        player.recent_form = 1.10  # Expensive = usually consistent
                    elif player.salary >= 5000:
                        player.recent_form = 1.05
                    else:
                        player.recent_form = 0.95  # Cheap = risky
                else:
                    # GPP: Look for hot streaks
                    if player.salary >= 4000 and player.salary <= 6000:
                        player.recent_form = 1.15  # Mid-range upside
                    else:
                        player.recent_form = 1.00

    def _calculate_consistency(self, players: List, contest_type: str):
        """Calculate consistency scores for cash games"""
        for player in players:
            if hasattr(player, 'consistency_stats'):
                # Use actual consistency data
                player.consistency_score = player.consistency_stats.get('score', 1.0)
            else:
                # Estimate based on position and salary
                if player.is_pitcher:
                    # Pitchers: High-priced = consistent
                    if player.salary >= 9000:
                        player.consistency_score = 1.20
                    elif player.salary >= 7000:
                        player.consistency_score = 1.10
                    else:
                        player.consistency_score = 0.90
                else:
                    # Hitters: Batting order matters
                    order = getattr(player, 'batting_order', 9)
                    if order <= 3:
                        player.consistency_score = 1.15
                    elif order <= 5:
                        player.consistency_score = 1.05
                    else:
                        player.consistency_score = 0.95

    def set_enrichment_source(self, source_type: str, source_object):
        """Set an enrichment source"""
        if source_type in self.enrichment_sources:
            self.enrichment_sources[source_type] = source_object
            logger.info(f"Set enrichment source: {source_type}")
        else:
            logger.warning(f"Unknown enrichment source type: {source_type}")

    def clear_cache(self):
        """Clear enrichment cache when slate changes"""
        self.enrichment_cache = {
            'slate_id': None,
            'enriched_players': set(),
            'enrichment_types': set()
        }
        logger.info("Enrichment cache cleared")


# Usage example
def demonstrate_smart_enrichment():
    """Show how smart enrichment works"""

    manager = SmartEnrichmentManager()

    # Example 1: Small slate, cash game, pitcher_dominance
    print("\n=== EXAMPLE 1: Small Cash Slate ===")
    profile = manager.get_enrichment_requirements(
        slate_size='small',
        strategy='pitcher_dominance',
        contest_type='cash'
    )
    print(f"Needs Statcast: {profile.needs_statcast}")
    print(f"Needs K-rates: {profile.needs_k_rate}")
    print(f"Priority players: {profile.statcast_priority_players}")
    print(f"Needs ownership: {profile.needs_ownership}")

    # Example 2: Large slate, GPP, correlation_value
    print("\n=== EXAMPLE 2: Large GPP Slate ===")
    profile = manager.get_enrichment_requirements(
        slate_size='large',
        strategy='correlation_value',
        contest_type='gpp'
    )
    print(f"Needs Vegas: {profile.needs_vegas}")
    print(f"Needs ownership: {profile.needs_ownership}")
    print(f"Needs barrel rate: {profile.needs_barrel_rate}")
    print(f"Priority players: {profile.statcast_priority_players}")

    # Example 3: Medium slate, cash, projection_monster
    print("\n=== EXAMPLE 3: Medium Cash Slate ===")
    profile = manager.get_enrichment_requirements(
        slate_size='medium',
        strategy='projection_monster',
        contest_type='cash'
    )
    print(f"Needs consistency: {profile.needs_consistency}")
    print(f"Needs recent form: {profile.needs_recent_form}")
    print(f"Needs Statcast: {profile.needs_statcast}")
    print(f"Needs ownership: {profile.needs_ownership}")


if __name__ == "__main__":
    demonstrate_smart_enrichment()