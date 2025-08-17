#!/usr/bin/env python3
"""
Real Statcast Fetcher - Gets actual Baseball Savant data
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import time

logger = logging.getLogger(__name__)

try:
    from pybaseball import statcast_batter, statcast_pitcher, playerid_lookup
    PYBASEBALL_AVAILABLE = True
    logger.info("✅ PyBaseball available - real Statcast data enabled")
except ImportError:
    PYBASEBALL_AVAILABLE = False
    logger.warning("⚠️ PyBaseball not available - using default stats")


class SimpleStatcastFetcher:
    """Real Statcast fetcher using pybaseball"""

    def __init__(self):
        """Initialize fetcher"""
        self.enabled = PYBASEBALL_AVAILABLE
        self.player_cache = {}
        self.last_fetch_time = {}
        self.rate_limit_delay = 0.5  # Seconds between API calls (reduced for faster processing)

        if self.enabled:
            logger.info("SimpleStatcastFetcher initialized (REAL DATA MODE)")
        else:
            logger.info("SimpleStatcastFetcher initialized (fallback mode)")

    def get_batter_stats(self, player_name: str) -> Dict:
        """Get real batter stats from Statcast"""
        if not self.enabled:
            return self._get_default_batter_stats()

        try:
            # Check cache first
            cache_key = f"batter_{player_name}"
            if cache_key in self.player_cache:
                cached_time = self.last_fetch_time.get(cache_key, 0)
                if time.time() - cached_time < 3600:  # Cache for 1 hour
                    return self.player_cache[cache_key]

            # Rate limiting
            self._rate_limit()

            # Get player ID
            player_id = self._get_player_id(player_name)
            if not player_id:
                logger.debug(f"No player ID found for {player_name}")
                return self._get_default_batter_stats()

            # Get recent stats (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            logger.debug(f"Fetching Statcast data for {player_name} ({player_id})")

            # Fetch batter data
            data = statcast_batter(
                start_dt=start_date.strftime('%Y-%m-%d'),
                end_dt=end_date.strftime('%Y-%m-%d'),
                player_id=player_id
            )

            if data.empty:
                logger.debug(f"No recent Statcast data for {player_name}")
                return self._get_default_batter_stats()

            # Calculate stats
            stats = self._calculate_batter_stats(data)

            # Cache results
            self.player_cache[cache_key] = stats
            self.last_fetch_time[cache_key] = time.time()

            logger.debug(f"✅ Got real Statcast data for {player_name}: {stats}")
            return stats

        except Exception as e:
            logger.warning(f"Statcast fetch failed for {player_name}: {e}")
            return self._get_default_batter_stats()

    def get_player_stats(self, player_name: str) -> Dict:
        """Alias for get_batter_stats for compatibility"""
        return self.get_batter_stats(player_name)

    def get_recent_performance(self, player_name: str, days: int = 7) -> float:
        """Get recent performance multiplier"""
        if not self.enabled:
            return 1.0

        try:
            stats = self.get_batter_stats(player_name)

            # Use xwOBA as performance indicator
            xwoba = stats.get('xwoba', 0.320)

            # Convert to multiplier (league average xwOBA ~0.320)
            if xwoba > 0.380:
                return 1.15  # Excellent
            elif xwoba > 0.350:
                return 1.08  # Good
            elif xwoba > 0.290:
                return 1.0   # Average
            else:
                return 0.92  # Below average

        except Exception as e:
            logger.debug(f"Performance calc failed for {player_name}: {e}")
            return 1.0

    def get_pitcher_stats(self, player_name: str) -> Dict:
        """Get real pitcher stats from Statcast"""
        if not self.enabled:
            return self._get_default_pitcher_stats()

        try:
            # Check cache first
            cache_key = f"pitcher_{player_name}"
            if cache_key in self.player_cache:
                cached_time = self.last_fetch_time.get(cache_key, 0)
                if time.time() - cached_time < 3600:  # Cache for 1 hour
                    return self.player_cache[cache_key]

            # Rate limiting
            self._rate_limit()

            # Get player ID
            player_id = self._get_player_id(player_name)
            if not player_id:
                logger.debug(f"No player ID found for pitcher {player_name}")
                return self._get_default_pitcher_stats()

            # Get recent stats (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            logger.debug(f"Fetching pitcher Statcast data for {player_name} ({player_id})")

            # Fetch pitcher data
            data = statcast_pitcher(
                start_dt=start_date.strftime('%Y-%m-%d'),
                end_dt=end_date.strftime('%Y-%m-%d'),
                player_id=player_id
            )

            if data.empty:
                logger.debug(f"No recent pitcher Statcast data for {player_name}")
                return self._get_default_pitcher_stats()

            # Calculate pitcher stats
            stats = self._calculate_pitcher_stats(data)

            # Cache results
            self.player_cache[cache_key] = stats
            self.last_fetch_time[cache_key] = time.time()

            logger.debug(f"✅ Got real pitcher Statcast data for {player_name}: {stats}")
            return stats

        except Exception as e:
            logger.warning(f"Pitcher Statcast fetch failed for {player_name}: {e}")
            return self._get_default_pitcher_stats()

    def get_pitcher_stats(self, player_name: str) -> Dict:
        """Get real pitcher stats from Statcast"""
        if not self.enabled:
            return self._get_default_pitcher_stats()

        try:
            # Check cache first
            cache_key = f"pitcher_{player_name}"
            if cache_key in self.player_cache:
                cached_time = self.last_fetch_time.get(cache_key, 0)
                if time.time() - cached_time < 3600:  # Cache for 1 hour
                    return self.player_cache[cache_key]

            # Rate limiting
            self._rate_limit()

            # Get player ID
            player_id = self._get_player_id(player_name)
            if not player_id:
                logger.debug(f"No player ID found for pitcher {player_name}")
                return self._get_default_pitcher_stats()

            # Get recent stats (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            logger.debug(f"Fetching pitcher Statcast data for {player_name} ({player_id})")

            # Fetch pitcher data
            data = statcast_pitcher(
                start_dt=start_date.strftime('%Y-%m-%d'),
                end_dt=end_date.strftime('%Y-%m-%d'),
                player_id=player_id
            )

            if data.empty:
                logger.debug(f"No recent pitcher Statcast data for {player_name}")
                return self._get_default_pitcher_stats()

            # Calculate real pitcher stats from Statcast data
            stats = self._calculate_pitcher_stats_from_data(data, player_name)

            if len(data) > 0:
                stats['has_recent_data'] = True
                logger.debug(f"✅ Found recent pitcher data for {player_name}: K/9 {stats.get('k_rate', 8.0):.1f}")
            else:
                stats['has_recent_data'] = False

            # Cache results
            self.player_cache[cache_key] = stats
            self.last_fetch_time[cache_key] = time.time()

            return stats

        except Exception as e:
            logger.warning(f"Pitcher Statcast fetch failed for {player_name}: {e}")
            return self._get_default_pitcher_stats()

    def _calculate_pitcher_stats_from_data(self, data: pd.DataFrame, player_name: str) -> Dict:
        """Calculate real K/9 and other pitcher stats from Statcast data"""
        try:
            if data.empty:
                return self._get_default_pitcher_stats()

            # Try to get real K/9 from recent games
            # Method 1: Use playerid_lookup to get season stats
            try:
                from pybaseball import playerid_lookup, pitching_stats

                # Get player ID for season stats
                name_parts = player_name.split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = name_parts[-1]

                    # Look up player
                    player_lookup = playerid_lookup(last_name, first_name)
                    if not player_lookup.empty:
                        player_id = player_lookup.iloc[0]['key_mlbam']

                        # Get 2024 season stats
                        season_stats = pitching_stats(2024, 2024, qual=1)
                        player_stats = season_stats[season_stats['IDfg'] == player_id]

                        if not player_stats.empty:
                            # Get real K/9
                            k9 = player_stats.iloc[0].get('K/9', 8.0)
                            era = player_stats.iloc[0].get('ERA', 4.00)
                            whip = player_stats.iloc[0].get('WHIP', 1.30)

                            logger.debug(f"✅ Real season stats for {player_name}: K/9 {k9:.1f}, ERA {era:.2f}")

                            return {
                                'k_rate': float(k9),
                                'era': float(era),
                                'whip': float(whip),
                                'quality_score': 1.15 if k9 >= 10.0 else 1.05 if k9 >= 8.5 else 1.0,
                                'has_recent_data': True
                            }

            except Exception as e:
                logger.debug(f"Season stats lookup failed for {player_name}: {e}")

            # Method 2: Estimate from Statcast data
            if 'events' in data.columns:
                total_batters = len(data)
                strikeouts = len(data[data['events'] == 'strikeout'])

                if total_batters > 10:  # Need reasonable sample
                    # Rough K/9 estimate: (K / BF) * 27 (outs per game) / 3 (outs per inning)
                    k_rate = (strikeouts / total_batters) * 9
                    k_rate = min(max(k_rate, 4.0), 15.0)  # Cap between 4-15

                    return {
                        'k_rate': k_rate,
                        'era': 4.00,  # Default
                        'whip': 1.30,  # Default
                        'quality_score': 1.15 if k_rate >= 10.0 else 1.05 if k_rate >= 8.5 else 1.0,
                        'has_recent_data': True
                    }

            # Fallback to defaults
            return self._get_default_pitcher_stats()

        except Exception as e:
            logger.debug(f"Pitcher stats calculation failed for {player_name}: {e}")
            return self._get_default_pitcher_stats()

    def _get_default_pitcher_stats(self) -> Dict:
        """Return default pitcher stats when real data unavailable"""
        return {
            'k_rate': 8.0,
            'era': 4.00,
            'whip': 1.30,
            'quality_score': 1.0,
            'has_recent_data': False
        }

    def get_barrel_rate(self, player_name: str) -> float:
        """Get barrel rate"""
        stats = self.get_batter_stats(player_name)
        return stats.get('barrel%', 0.0)

    def _get_player_id(self, player_name: str) -> Optional[int]:
        """Get MLB player ID from name"""
        try:
            # Split name
            parts = player_name.strip().split()
            if len(parts) < 2:
                return None

            first_name = parts[0]
            last_name = parts[-1]

            # Look up player
            lookup = playerid_lookup(last_name, first_name)

            if lookup.empty:
                return None

            # Get most recent player (in case of duplicates)
            lookup = lookup.sort_values('mlb_played_last', ascending=False)

            return lookup.iloc[0]['key_mlbam']

        except Exception as e:
            logger.debug(f"Player ID lookup failed for {player_name}: {e}")
            return None

    def _calculate_batter_stats(self, data: pd.DataFrame) -> Dict:
        """Calculate key stats from Statcast data"""
        try:
            stats = {}

            # Barrel rate
            if 'launch_speed' in data.columns and 'launch_angle' in data.columns:
                # Barrel definition: 98+ mph exit velo with optimal launch angle
                barrels = data[
                    (data['launch_speed'] >= 98) &
                    (data['launch_angle'] >= 26) &
                    (data['launch_angle'] <= 30)
                ]
                total_batted_balls = len(data[data['launch_speed'].notna()])

                if total_batted_balls > 0:
                    stats['barrel%'] = (len(barrels) / total_batted_balls) * 100
                else:
                    stats['barrel%'] = 8.5
            else:
                stats['barrel%'] = 8.5

            # xwOBA
            if 'estimated_woba_using_speedangle' in data.columns:
                xwoba_values = data['estimated_woba_using_speedangle'].dropna()
                if len(xwoba_values) > 0:
                    stats['xwoba'] = xwoba_values.mean()
                else:
                    stats['xwoba'] = 0.320
            else:
                stats['xwoba'] = 0.320

            # Hard hit rate (95+ mph)
            if 'launch_speed' in data.columns:
                hard_hits = data[data['launch_speed'] >= 95]
                total_batted_balls = len(data[data['launch_speed'].notna()])

                if total_batted_balls > 0:
                    stats['hard_hit%'] = (len(hard_hits) / total_batted_balls) * 100
                else:
                    stats['hard_hit%'] = 40.0
            else:
                stats['hard_hit%'] = 40.0

            # Average exit velocity
            if 'launch_speed' in data.columns:
                exit_velos = data['launch_speed'].dropna()
                if len(exit_velos) > 0:
                    stats['avg_exit_velo'] = exit_velos.mean()
                else:
                    stats['avg_exit_velo'] = 88.0
            else:
                stats['avg_exit_velo'] = 88.0

            return stats

        except Exception as e:
            logger.warning(f"Stats calculation failed: {e}")
            return self._get_default_batter_stats()

    def _calculate_pitcher_stats(self, data: pd.DataFrame) -> Dict:
        """Calculate key pitcher stats from Statcast data"""
        try:
            stats = {}

            # Strikeout rate (K/9)
            if 'events' in data.columns:
                total_batters = len(data)
                strikeouts = len(data[data['events'] == 'strikeout'])

                if total_batters > 0:
                    # Estimate K/9 (rough calculation)
                    k_rate = (strikeouts / total_batters) * 27 / 3  # Rough K/9 estimate
                    stats['k_rate'] = min(k_rate, 15.0)  # Cap at 15 K/9
                else:
                    stats['k_rate'] = 8.0
            else:
                stats['k_rate'] = 8.0

            # Exit velocity allowed
            if 'launch_speed' in data.columns:
                exit_velos = data['launch_speed'].dropna()
                if len(exit_velos) > 0:
                    avg_exit_velo_allowed = exit_velos.mean()
                    stats['avg_exit_velo_allowed'] = avg_exit_velo_allowed

                    # Lower exit velo allowed = better pitcher
                    if avg_exit_velo_allowed < 87:
                        stats['quality_score'] = 1.15  # Elite
                    elif avg_exit_velo_allowed < 90:
                        stats['quality_score'] = 1.05  # Good
                    else:
                        stats['quality_score'] = 0.95  # Below average
                else:
                    stats['avg_exit_velo_allowed'] = 89.0
                    stats['quality_score'] = 1.0
            else:
                stats['avg_exit_velo_allowed'] = 89.0
                stats['quality_score'] = 1.0

            # Hard contact rate allowed
            if 'launch_speed' in data.columns:
                hard_contact = data[data['launch_speed'] >= 95]
                total_contact = len(data[data['launch_speed'].notna()])

                if total_contact > 0:
                    hard_contact_rate = (len(hard_contact) / total_contact) * 100
                    stats['hard_contact_allowed%'] = hard_contact_rate
                else:
                    stats['hard_contact_allowed%'] = 35.0
            else:
                stats['hard_contact_allowed%'] = 35.0

            return stats

        except Exception as e:
            logger.warning(f"Pitcher stats calculation failed: {e}")
            return self._get_default_pitcher_stats()

    def _get_default_batter_stats(self) -> Dict:
        """Return default stats when real data unavailable"""
        return {
            'barrel%': 8.5,
            'xwoba': 0.320,
            'hard_hit%': 40.0,
            'avg_exit_velo': 88.0
        }

    def _get_default_pitcher_stats(self) -> Dict:
        """Return default pitcher stats when real data unavailable"""
        return {
            'k_rate': 8.0,
            'avg_exit_velo_allowed': 89.0,
            'hard_contact_allowed%': 35.0,
            'quality_score': 1.0
        }

    def _rate_limit(self):
        """Simple rate limiting to avoid overwhelming APIs"""
        current_time = time.time()
        last_call = getattr(self, '_last_api_call', 0)

        time_since_last = current_time - last_call
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)

        self._last_api_call = time.time()
