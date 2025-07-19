#!/usr/bin/env python3
"""
PURE DATA PIPELINE - Baseball Savant Integration
===============================================
Fetches all required Statcast data with ZERO fallbacks
Optimized for performance with parallel processing
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class PureDataPipeline:
    """
    Data pipeline that ONLY uses real data sources
    NO FALLBACKS - if data isn't available, score is 0
    """

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.statcast_fetcher = None
        self.confirmation_system = None
        self.vegas_client = None

        # Cache settings
        self.cache_ttl_minutes = 60  # 1 hour cache
        self.data_cache = {}

        # Dynamic date ranges based on current date
        now = datetime.now()
        current_year = now.year

        # Determine if we're in-season or off-season
        if now.month >= 4 and now.month <= 10:
            # In-season: use current year
            self.season_start = datetime(current_year, 4, 1)
            self.season_end = datetime(current_year, 10, 1)
        elif now.month < 4:
            # Early in year: use previous season
            self.season_start = datetime(current_year - 1, 4, 1)
            self.season_end = datetime(current_year - 1, 10, 1)
        else:
            # Late in year: use current year's completed season
            self.season_start = datetime(current_year, 4, 1)
            self.season_end = datetime(current_year, 10, 1)

        # For recent form, always use last N days from today
        self.recent_days = 14  # Last 14 days for form
        self.recent_cutoff = now - timedelta(days=self.recent_days)

        logger.info(f"Pure Data Pipeline initialized with {max_workers} workers")
        logger.info(f"Season range: {self.season_start.date()} to {self.season_end.date()}")
        logger.info(f"Recent form cutoff: {self.recent_cutoff.date()}")

    def set_data_sources(self, statcast_fetcher=None, confirmation_system=None, vegas_client=None):
        """Connect external data sources"""
        self.statcast_fetcher = statcast_fetcher
        self.confirmation_system = confirmation_system
        self.vegas_client = vegas_client

    def enrich_players_parallel(self, players: List[Any]) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Enrich all players with real data in parallel
        Returns: (enriched_players, enrichment_stats)
        """
        start_time = datetime.now()
        stats = {
            'total_players': len(players),
            'enriched_count': 0,
            'statcast_found': 0,
            'lineup_confirmed': 0,
            'vegas_data_found': 0,
            'failed_enrichments': 0,
            'processing_time': 0
        }

        print(f"\n🚀 ENRICHING {len(players)} PLAYERS WITH PURE DATA")
        print("=" * 60)

        # Step 1: Get confirmed lineups and batting orders
        if self.confirmation_system:
            self._enrich_confirmed_lineups(players, stats)

        # Step 2: Get Vegas data for all games
        if self.vegas_client:
            self._enrich_vegas_data(players, stats)

        # Step 3: Parallel Statcast enrichment
        if self.statcast_fetcher:
            self._enrich_statcast_parallel(players, stats)

        # Step 4: Calculate recent form
        self._calculate_recent_form(players, stats)

        # Step 5: Get matchup data
        self._enrich_matchup_data(players, stats)

        # Final stats
        stats['processing_time'] = (datetime.now() - start_time).seconds
        stats['enriched_count'] = sum(1 for p in players if hasattr(p, '_is_enriched'))

        self._print_enrichment_summary(stats)

        return players, stats

    def _enrich_confirmed_lineups(self, players: List[Any], stats: Dict):
        """Enrich players with confirmed lineup data"""
        print("\n📋 Step 1: Confirming Lineups and Batting Orders...")

        confirmed_count = 0
        for player in players:
            if player.primary_position == 'P':
                # Check if pitcher is confirmed starter
                is_confirmed, source = self.confirmation_system.is_pitcher_confirmed(
                    player.name, player.team
                )
                if is_confirmed:
                    player.is_confirmed = True
                    player.confirmation_source = source
                    confirmed_count += 1
            else:
                # Check if hitter is in confirmed lineup
                is_confirmed, batting_order = self.confirmation_system.is_player_confirmed(
                    player.name, player.team
                )
                if is_confirmed:
                    player.is_confirmed = True
                    player.batting_order = batting_order
                    confirmed_count += 1

                    # Log top of order
                    if batting_order and batting_order <= 3:
                        print(f"   🔥 {player.name} batting {batting_order} for {player.team}")

        stats['lineup_confirmed'] = confirmed_count
        print(f"   ✅ Confirmed {confirmed_count} players in starting lineups")

    def _enrich_vegas_data(self, players: List[Any], stats: Dict):
        """Enrich players with Vegas lines data"""
        print("\n💰 Step 2: Fetching Vegas Lines...")

        # Get unique teams
        teams = set(p.team for p in players if p.team)
        vegas_data = {}

        for team in teams:
            try:
                team_vegas = self.vegas_client.get_team_vegas_data(team)
                if team_vegas:
                    vegas_data[team] = team_vegas
            except Exception as e:
                logger.debug(f"Failed to get Vegas data for {team}: {e}")

        # Apply to players
        vegas_count = 0
        for player in players:
            if player.team in vegas_data:
                player.vegas_data = vegas_data[player.team]
                vegas_count += 1

        stats['vegas_data_found'] = vegas_count
        print(f"   ✅ Applied Vegas data to {vegas_count} players")

    def _enrich_statcast_parallel(self, players: List[Any], stats: Dict):
        """Enrich players with Statcast data in parallel"""
        print(f"\n📊 Step 3: Fetching Statcast Data (Parallel with {self.max_workers} workers)...")

        # Only fetch for confirmed players or high-projection players
        players_to_fetch = [
            p for p in players
            if getattr(p, 'is_confirmed', False) or
               getattr(p, 'base_projection', 0) > 15.0
        ]

        print(f"   Fetching Statcast for {len(players_to_fetch)} priority players")

        statcast_count = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_player = {
                executor.submit(self._fetch_statcast_safe, player): player
                for player in players_to_fetch
            }

            # Process results as they complete
            for future in as_completed(future_to_player):
                player = future_to_player[future]
                try:
                    statcast_data = future.result()
                    if statcast_data is not None and not statcast_data.empty:
                        player.statcast_data = statcast_data
                        player.statcast_metrics = self._extract_key_metrics(player, statcast_data)
                        statcast_count += 1

                        # Log elite performers
                        if player.primary_position != 'P':
                            if 'barrel_rate' in player.statcast_metrics:
                                if player.statcast_metrics['barrel_rate'] > 10.0:
                                    print(
                                        f"   🎯 {player.name}: {player.statcast_metrics['barrel_rate']:.1f}% barrel rate!")
                except Exception as e:
                    logger.debug(f"Failed to get Statcast for {player.name}: {e}")
                    stats['failed_enrichments'] += 1

        stats['statcast_found'] = statcast_count
        print(f"   ✅ Enriched {statcast_count} players with Statcast data")

    def _fetch_statcast_safe(self, player: Any) -> Optional[pd.DataFrame]:
        """Safely fetch Statcast data for a player"""
        try:
            return self.statcast_fetcher.fetch_player_data(
                player.name,
                player.primary_position
            )
        except Exception as e:
            logger.debug(f"Statcast fetch failed for {player.name}: {e}")
            return None

    def _extract_key_metrics(self, player: Any, data: pd.DataFrame) -> Dict[str, float]:
        """Extract key metrics from Statcast data"""
        metrics = {}

        if player.primary_position == 'P':
            # Pitcher metrics
            if 'description' in data.columns:
                total_swings = data['description'].isin(['swinging_strike', 'foul', 'hit_into_play']).sum()
                whiffs = (data['description'] == 'swinging_strike').sum()
                metrics['whiff_rate'] = (whiffs / total_swings * 100) if total_swings > 0 else 0

            if 'barrel' in data.columns:
                metrics['barrel_rate_against'] = (data['barrel'] == 1).mean() * 100

            if 'release_spin_rate' in data.columns:
                metrics['avg_spin_rate'] = data['release_spin_rate'].mean()

            if 'release_speed' in data.columns:
                metrics['avg_velocity'] = data['release_speed'].mean()

        else:
            # Batter metrics
            if 'barrel' in data.columns:
                metrics['barrel_rate'] = (data['barrel'] == 1).mean() * 100

            if 'launch_speed' in data.columns:
                metrics['avg_exit_velocity'] = data['launch_speed'].mean()
                metrics['hard_hit_rate'] = (data['launch_speed'] >= 95).mean() * 100

            if 'estimated_woba_using_speedangle' in data.columns:
                metrics['xwoba'] = data['estimated_woba_using_speedangle'].mean()

            if 'sprint_speed' in data.columns:
                metrics['sprint_speed'] = data['sprint_speed'].mean()

            if 'launch_angle' in data.columns:
                sweet_spot = ((data['launch_angle'] >= 10) & (data['launch_angle'] <= 30)).mean() * 100
                metrics['sweet_spot_pct'] = sweet_spot

        return metrics

    def _calculate_recent_form(self, players: List[Any], stats: Dict):
        """Calculate recent performance metrics"""
        print("\n📈 Step 4: Calculating Recent Form...")

        # Use the dynamic recent cutoff date
        form_count = 0
        for player in players:
            if hasattr(player, 'statcast_data') and player.statcast_data is not None:
                recent_data = player.statcast_data[
                    pd.to_datetime(player.statcast_data['game_date']) >= self.recent_cutoff
                    ]

                if not recent_data.empty:
                    # Calculate recent performance
                    player.recent_games = len(recent_data['game_date'].unique())

                    # Recent batting average for hitters
                    if player.primary_position != 'P':
                        events = recent_data['events'].value_counts()
                        hits = sum([
                            events.get('single', 0),
                            events.get('double', 0),
                            events.get('triple', 0),
                            events.get('home_run', 0)
                        ])
                        at_bats = len(recent_data[recent_data['events'].notna()])
                        player.recent_avg = hits / at_bats if at_bats > 0 else 0

                        # Trend analysis
                        if player.recent_games >= 5:
                            player.is_hot = player.recent_avg > 0.300
                            if player.is_hot:
                                print(
                                    f"   🔥 {player.name} is HOT: .{int(player.recent_avg * 1000)} last {player.recent_games} games")

                    form_count += 1

        print(f"   ✅ Calculated recent form for {form_count} players")

    def _enrich_matchup_data(self, players: List[Any], stats: Dict):
        """Enrich players with matchup-specific data"""
        print("\n🆚 Step 5: Analyzing Matchups...")

        # This would include:
        # - Batter vs Pitcher historical matchups
        # - Team vs Team trends
        # - Platoon advantages
        # - Pitcher vs Team lineup history

        # For now, basic platoon analysis
        matchup_count = 0
        for player in players:
            if hasattr(player, 'bats') and hasattr(player, 'opposing_pitcher'):
                # Check for platoon advantage
                opp_throws = getattr(player.opposing_pitcher, 'throws', None)
                if opp_throws and player.bats != opp_throws:
                    player.has_platoon_advantage = True
                    matchup_count += 1

        print(f"   ✅ Analyzed matchups for {matchup_count} players")

    def _print_enrichment_summary(self, stats: Dict):
        """Print summary of enrichment process"""
        print("\n" + "=" * 60)
        print("📊 ENRICHMENT SUMMARY")
        print("=" * 60)
        print(f"Total Players:        {stats['total_players']}")
        print(
            f"Confirmed Lineups:    {stats['lineup_confirmed']} ({stats['lineup_confirmed'] / stats['total_players'] * 100:.1f}%)")
        print(
            f"Statcast Data:        {stats['statcast_found']} ({stats['statcast_found'] / stats['total_players'] * 100:.1f}%)")
        print(
            f"Vegas Data:           {stats['vegas_data_found']} ({stats['vegas_data_found'] / stats['total_players'] * 100:.1f}%)")
        print(f"Failed Enrichments:   {stats['failed_enrichments']}")
        print(f"Processing Time:      {stats['processing_time']}s")
        print(f"Success Rate:         {stats['enriched_count'] / stats['total_players'] * 100:.1f}%")
        print("=" * 60)

    def validate_player_data(self, player: Any) -> Tuple[bool, List[str]]:
        """
        Validate that player has minimum required data
        Returns: (is_valid, missing_data_list)
        """
        required_fields = {
            'base_projection': 'Base projection from DraftKings',
            'name': 'Player name',
            'team': 'Team abbreviation',
            'salary': 'Salary',
            'primary_position': 'Position'
        }

        missing = []
        for field, description in required_fields.items():
            if not hasattr(player, field) or getattr(player, field) is None:
                missing.append(description)

        # Check for enrichment data
        enrichment_fields = {
            'is_confirmed': 'Lineup confirmation',
            'statcast_data': 'Statcast metrics',
            'vegas_data': 'Vegas lines'
        }

        has_any_enrichment = any(
            hasattr(player, field) and getattr(player, field) is not None
            for field in enrichment_fields
        )

        if not has_any_enrichment:
            missing.append('No enrichment data (Statcast/Vegas/Lineup)')

        return (len(missing) == 0, missing)


# Integration function
def create_pure_data_pipeline(max_workers: int = 10) -> PureDataPipeline:
    """Create an instance of the pure data pipeline"""
    return PureDataPipeline(max_workers)


if __name__ == "__main__":
    print("✅ Pure Data Pipeline loaded")
    print("📊 This pipeline fetches:")
    print("  - Confirmed lineups and batting orders")
    print("  - Vegas lines and implied totals")
    print("  - Full Statcast data (80+ metrics)")
    print("  - Recent form analysis")
    print("  - Matchup data")
    print("\n❌ NO FALLBACK DATA - Real metrics only!")