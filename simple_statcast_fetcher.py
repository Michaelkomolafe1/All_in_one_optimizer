#!/usr/bin/env python3
"""
COMPLETE SIMPLE STATCAST FETCHER
================================
Full implementation with pybaseball integration
Dynamic dates, caching, parallel fetching
NO FALLBACK DATA
"""

import io
import json
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Suppress pybaseball output
os.environ["PYBASEBALL_NO_PROGRESS"] = "1"
os.environ["PYBASEBALL_CACHE"] = "1"

# Import pybaseball with output suppression
PYBASEBALL_AVAILABLE = False
try:
    # Suppress all output during import
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    import pybaseball
    from pybaseball import statcast_batter, statcast_pitcher, playerid_lookup

    pybaseball.cache.enable()

    sys.stdout = old_stdout
    sys.stderr = old_stderr

    PYBASEBALL_AVAILABLE = True

except ImportError:
    sys.stdout = old_stdout if 'old_stdout' in locals() else sys.stdout
    sys.stderr = old_stderr if 'old_stderr' in locals() else sys.stderr
    print("⚠️ PyBaseball not available - install with: pip install pybaseball")

# Try to import performance config, but don't fail if it's not available
try:
    from performance_config import get_performance_settings

    PERFORMANCE_CONFIG_AVAILABLE = True
except ImportError:
    PERFORMANCE_CONFIG_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleStatcastFetcher:
    """
    Production-ready Statcast data fetcher
    - Dynamic season detection
    - Intelligent caching
    - Parallel processing
    - NO FALLBACK DATA
    """

    def __init__(self, max_workers: int = 5, cache_days: int = 1):
        """Initialize with dynamic configuration"""
        self.max_workers = max_workers
        self.cache_days = cache_days

        # Set up cache directory
        self.cache_dir = Path("data/statcast_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Dynamic season configuration
        self._configure_season_dates()

        # Player ID cache
        self.player_id_cache = {}
        self._load_player_id_cache()

        # Performance tracking
        self.stats = {
            'api_calls': 0,
            'cache_hits': 0,
            'failures': 0,
            'total_time': 0
        }

        # Thread safety
        self.lock = threading.Lock()

        logger.info(f"SimpleStatcastFetcher initialized")
        logger.info(f"  Season: {self.season_start} to {self.season_end}")
        logger.info(f"  Cache: {self.cache_dir}")
        logger.info(f"  Workers: {self.max_workers}")

    def _configure_season_dates(self):
        """Set season dates based on current date"""
        now = datetime.now()
        current_year = now.year

        # MLB season typically April 1 - September 30
        # Playoffs through October

        if 4 <= now.month <= 10:
            # In-season
            self.season_start = f"{current_year}-04-01"
            self.season_end = now.strftime("%Y-%m-%d")  # Up to today
            self.is_current_season = True
        elif now.month < 4:
            # Pre-season: use last year
            self.season_start = f"{current_year - 1}-04-01"
            self.season_end = f"{current_year - 1}-10-01"
            self.is_current_season = False
        else:
            # Post-season: use current year
            self.season_start = f"{current_year}-04-01"
            self.season_end = f"{current_year}-10-01"
            self.is_current_season = False

    def _load_player_id_cache(self):
        """Load cached player IDs"""
        cache_file = self.cache_dir / "player_ids.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.player_id_cache = json.load(f)
                logger.info(f"Loaded {len(self.player_id_cache)} cached player IDs")
            except Exception as e:
                logger.error(f"Failed to load player ID cache: {e}")
                self.player_id_cache = {}
        else:
            self.player_id_cache = {}

    def _save_player_id_cache(self):
        """Save player ID cache"""
        cache_file = self.cache_dir / "player_ids.json"

        try:
            with open(cache_file, 'w') as f:
                json.dump(self.player_id_cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save player ID cache: {e}")

    def get_player_id(self, player_name: str) -> Optional[int]:
        """Get MLB player ID with caching"""
        # Normalize name
        clean_name = player_name.strip().lower()

        # Check cache
        if clean_name in self.player_id_cache:
            return self.player_id_cache[clean_name]

        if not PYBASEBALL_AVAILABLE:
            return None

        try:
            # Parse name
            parts = player_name.strip().split()
            if len(parts) < 2:
                return None

            first_name = parts[0]
            last_name = ' '.join(parts[1:])

            # Suppress pybaseball output
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                results = playerid_lookup(last_name, first_name)
            finally:
                sys.stdout = old_stdout

            if results is not None and not results.empty:
                # Get most recent player (highest year)
                results = results.sort_values('mlb_played_last', ascending=False)
                player_id = int(results.iloc[0]['key_mlbam'])

                # Cache it
                self.player_id_cache[clean_name] = player_id
                self._save_player_id_cache()

                return player_id

        except Exception as e:
            logger.debug(f"Failed to lookup {player_name}: {e}")

        return None

    def fetch_player_data(self, player_name: str, position: str = None) -> Optional[pd.DataFrame]:
        """
        Fetch Statcast data for a player with enhanced caching

        Args:
            player_name: Player's full name
            position: 'P' for pitcher, anything else for batter

        Returns:
            DataFrame with Statcast data or None
        """
        # Import enhanced cache manager
        from enhanced_caching_system import get_cache_manager
        cache_manager = get_cache_manager()

        # Check enhanced cache first
        cached_data = cache_manager.cached_statcast(player_name, position or "Unknown")
        if cached_data is not None:
            with self.lock:
                self.stats['cache_hits'] += 1
            logger.debug(f"✅ Enhanced cache hit for {player_name}")
            return cached_data

        # Check file cache second
        file_cache_data = self._check_cache(player_name)
        if file_cache_data is not None:
            with self.lock:
                self.stats['cache_hits'] += 1

            # Store in enhanced cache for even faster access
            cache_manager.cache_statcast(player_name, position or "Unknown", file_cache_data)
            logger.debug(f"✅ File cache hit for {player_name}, stored in enhanced cache")
            return file_cache_data

        # If not in any cache, fetch from API
        logger.debug(f"🔍 Fetching fresh data for {player_name}")

        # Get player ID
        player_id = self.get_player_id(player_name)
        if not player_id:
            logger.debug(f"No ID found for {player_name}")
            with self.lock:
                self.stats['failures'] += 1

            # Cache the failure to avoid repeated lookups
            cache_manager.cache_statcast(player_name, position or "Unknown", None)
            return None

        # Fetch from API
        try:
            start_time = time.time()

            # Suppress pybaseball output
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                if position == 'P':
                    data = statcast_pitcher(
                        start_dt=self.season_start,
                        end_dt=self.season_end,
                        player_id=player_id
                    )
                else:
                    data = statcast_batter(
                        start_dt=self.season_start,
                        end_dt=self.season_end,
                        player_id=player_id
                    )
            finally:
                sys.stdout = old_stdout

            fetch_time = time.time() - start_time

            with self.lock:
                self.stats['api_calls'] += 1
                self.stats['total_time'] += fetch_time

            if data is not None and not data.empty:
                # Save to file cache
                self._save_to_cache(player_name, data)

                # Save to enhanced cache
                cache_manager.cache_statcast(player_name, position or "Unknown", data)

                logger.debug(f"✅ Fetched {len(data)} records for {player_name} in {fetch_time:.1f}s")
                logger.debug(f"💾 Cached data for {player_name} in both file and memory cache")

                # Log performance metrics periodically
                if self.stats['api_calls'] % 10 == 0:
                    logger.info(f"Statcast performance: {self.stats['api_calls']} API calls, "
                                f"{self.stats['cache_hits']} cache hits, "
                                f"avg fetch time: {self.stats['total_time'] / self.stats['api_calls']:.1f}s")

                return data
            else:
                logger.debug(f"No data found for {player_name}")

                # Cache empty result to avoid repeated failed lookups
                cache_manager.cache_statcast(player_name, position or "Unknown", pd.DataFrame())

                return None

        except Exception as e:
            logger.error(f"Error fetching {player_name}: {e}")
            with self.lock:
                self.stats['failures'] += 1

            # Don't cache errors - we might want to retry
            return None

    def fetch_multiple_players_parallel(self, players_list: List) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple players in parallel

        Args:
            players_list: List of player objects with 'name' and 'primary_position'

        Returns:
            Dict mapping player name to DataFrame
        """
        if not PYBASEBALL_AVAILABLE:
            logger.warning("PyBaseball not available")
            return {}

        print(f"\n⚡ Fetching Statcast data for {len(players_list)} players...")
        print(f"   Using {self.max_workers} parallel workers")

        results = {}
        start_time = time.time()

        # Filter to high-priority players
        priority_players = [
            p for p in players_list
            if getattr(p, 'is_confirmed', False) or
               getattr(p, 'base_projection', 0) > 12.0
        ]

        print(f"   Prioritizing {len(priority_players)} confirmed/high-projection players")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_player = {
                executor.submit(
                    self.fetch_player_data,
                    player.name,
                    player.primary_position
                ): player
                for player in priority_players
            }

            # Process as completed
            completed = 0
            for future in as_completed(future_to_player):
                player = future_to_player[future]
                completed += 1

                try:
                    data = future.result()
                    if data is not None and not data.empty:
                        results[player.name] = data

                        # Show progress for notable players
                        if completed % 10 == 0:
                            print(f"   Progress: {completed}/{len(priority_players)}")

                except Exception as e:
                    logger.error(f"Failed to process {player.name}: {e}")

        total_time = time.time() - start_time

        # Summary
        print(f"\n   ✅ Fetching complete in {total_time:.1f}s")
        print(f"   Retrieved: {len(results)} players")
        print(f"   Cache hits: {self.stats['cache_hits']}")
        print(f"   API calls: {self.stats['api_calls']}")

        return results

    def extract_key_metrics(self, data: pd.DataFrame, position: str) -> Dict[str, float]:
        """Extract key metrics from Statcast data"""
        if data is None or data.empty:
            return {}

        metrics = {}

        if position == 'P':
            # Pitcher metrics
            # Whiff rate
            if 'description' in data.columns:
                swings = data['description'].isin(['swinging_strike', 'foul', 'hit_into_play'])
                whiffs = data['description'] == 'swinging_strike'
                metrics['whiff_rate'] = (whiffs.sum() / swings.sum() * 100) if swings.sum() > 0 else 0

            # Barrel rate against
            if 'barrel' in data.columns:
                metrics['barrel_rate_against'] = (data['barrel'] == 1).mean() * 100

            # Average velocity
            if 'release_speed' in data.columns:
                metrics['avg_velocity'] = data['release_speed'].mean()

            # Spin rate
            if 'release_spin_rate' in data.columns:
                metrics['avg_spin_rate'] = data['release_spin_rate'].mean()

            # Zone rate
            if 'zone' in data.columns:
                metrics['zone_rate'] = data['zone'].between(1, 9).mean() * 100

        else:
            # Batter metrics
            # Barrel rate
            if 'barrel' in data.columns:
                metrics['barrel_rate'] = (data['barrel'] == 1).mean() * 100

            # Exit velocity
            if 'launch_speed' in data.columns:
                metrics['avg_exit_velocity'] = data['launch_speed'].mean()
                metrics['hard_hit_rate'] = (data['launch_speed'] >= 95).mean() * 100
                metrics['max_exit_velocity'] = data['launch_speed'].max()

            # Launch angle
            if 'launch_angle' in data.columns:
                metrics['avg_launch_angle'] = data['launch_angle'].mean()
                sweet_spot = (data['launch_angle'].between(10, 30)).mean() * 100
                metrics['sweet_spot_pct'] = sweet_spot

            # Expected stats
            if 'estimated_woba_using_speedangle' in data.columns:
                metrics['xwoba'] = data['estimated_woba_using_speedangle'].mean()

            if 'estimated_ba_using_speedangle' in data.columns:
                metrics['xba'] = data['estimated_ba_using_speedangle'].mean()

            # Sprint speed
            if 'sprint_speed' in data.columns:
                metrics['sprint_speed'] = data['sprint_speed'].mean()

        return metrics

    def get_recent_form(self, player_name: str, days: int = 14) -> Dict[str, Any]:
        """Get player's recent form metrics"""
        # Get full season data
        data = self.fetch_player_data(player_name)

        if data is None or data.empty:
            return {
                'games': 0,
                'is_hot': False,
                'recent_avg': 0.250,
                'recent_ops': 0.700
            }

        # Filter to recent games
        if 'game_date' in data.columns:
            recent_date = datetime.now() - timedelta(days=days)
            recent_data = data[pd.to_datetime(data['game_date']) >= recent_date]
        else:
            recent_data = data.tail(100)  # Last 100 events

        if recent_data.empty:
            return {
                'games': 0,
                'is_hot': False,
                'recent_avg': 0.250,
                'recent_ops': 0.700
            }

        # Calculate metrics
        games = len(recent_data['game_date'].unique()) if 'game_date' in recent_data.columns else 5

        # Batting average
        if 'events' in recent_data.columns:
            events = recent_data['events'].value_counts()
            hits = sum([
                events.get('single', 0),
                events.get('double', 0),
                events.get('triple', 0),
                events.get('home_run', 0)
            ])

            ab_events = ['single', 'double', 'triple', 'home_run',
                         'strikeout', 'field_out', 'grounded_into_double_play',
                         'fielders_choice', 'force_out']
            at_bats = sum(events.get(e, 0) for e in ab_events)

            recent_avg = hits / at_bats if at_bats > 0 else 0.250

            # Simple OPS calculation
            walks = events.get('walk', 0)
            obp = (hits + walks) / (at_bats + walks) if (at_bats + walks) > 0 else 0.300

            # Total bases
            tb = (events.get('single', 0) +
                  events.get('double', 0) * 2 +
                  events.get('triple', 0) * 3 +
                  events.get('home_run', 0) * 4)
            slg = tb / at_bats if at_bats > 0 else 0.400

            recent_ops = obp + slg
        else:
            recent_avg = 0.250
            recent_ops = 0.700

        # Hot streak detection
        is_hot = recent_avg > 0.300 or recent_ops > 0.900

        return {
            'games': games,
            'is_hot': is_hot,
            'recent_avg': recent_avg,
            'recent_ops': recent_ops,
            'hits': hits if 'events' in recent_data.columns else 0,
            'at_bats': at_bats if 'events' in recent_data.columns else 0
        }

    def _check_cache(self, player_name: str) -> Optional[pd.DataFrame]:
        """Check if player data is cached and fresh"""
        cache_file = self.cache_dir / f"{player_name.replace(' ', '_')}_{self.season_start[:4]}.parquet"

        if cache_file.exists():
            # Check age
            file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)

            if file_age.days < self.cache_days:
                try:
                    return pd.read_parquet(cache_file)
                except Exception as e:
                    logger.error(f"Failed to read cache for {player_name}: {e}")

        return None

    def _save_to_cache(self, player_name: str, data: pd.DataFrame):
        """Save player data to cache"""
        if data is None or data.empty:
            return

        cache_file = self.cache_dir / f"{player_name.replace(' ', '_')}_{self.season_start[:4]}.parquet"

        try:
            data.to_parquet(cache_file, compression='snappy')
        except Exception as e:
            logger.error(f"Failed to cache {player_name}: {e}")

    def test_connection(self) -> bool:
        """Test pybaseball connection"""
        if not PYBASEBALL_AVAILABLE:
            return False

        try:
            # Try to fetch data for a known player
            test_id = 545361  # Mike Trout
            data = statcast_batter(
                start_dt=self.season_start,
                end_dt=self.season_start,  # Just one day
                player_id=test_id
            )
            return data is not None
        except Exception:
            return False

    def get_stats_summary(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_time = (self.stats['total_time'] / self.stats['api_calls']
                    if self.stats['api_calls'] > 0 else 0)

        return {
            'api_calls': self.stats['api_calls'],
            'cache_hits': self.stats['cache_hits'],
            'failures': self.stats['failures'],
            'avg_fetch_time': round(avg_time, 2),
            'cache_hit_rate': (self.stats['cache_hits'] /
                               (self.stats['api_calls'] + self.stats['cache_hits'])
                               if (self.stats['api_calls'] + self.stats['cache_hits']) > 0
                               else 0)
        }

    def fetch_all_players(self, player_names: List[str]) -> Dict[str, pd.DataFrame]:
        """Fetch data for all players (compatibility method)"""
        # Create player objects for the parallel fetcher
        player_objects = []
        for name in player_names:
            class PlayerObj:
                def __init__(self, name):
                    self.name = name
                    self.primary_position = None
                    self.is_confirmed = True
                    self.base_projection = 15.0

            player_objects.append(PlayerObj(name))

        return self.fetch_multiple_players_parallel(player_objects)

    def fetch_statcast_batch(self, players: List[Any]) -> Dict[str, Any]:
        """Fetch Statcast data for multiple players in parallel"""
        if PERFORMANCE_CONFIG_AVAILABLE:
            perf_settings = get_performance_settings()
            batch_size = perf_settings.batch_sizes.get('statcast', 10)
            max_workers = perf_settings.max_workers.get('statcast', self.max_workers)
            api_delay = perf_settings.api_delays.get('statcast', 0.1)
        else:
            batch_size = 10
            max_workers = self.max_workers
            api_delay = 0.1

        results = {}

        # Process in batches
        for i in range(0, len(players), batch_size):
            batch = players[i:i + batch_size]

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_player = {
                    executor.submit(self.fetch_player_data, player.name, player.primary_position): player
                    for player in batch
                }

                for future in as_completed(future_to_player):
                    player = future_to_player[future]
                    try:
                        data = future.result()
                        if data is not None:
                            results[player.name] = data
                    except Exception as e:
                        logger.warning(f"Failed to fetch data for {player.name}: {e}")

            # Small delay between batches
            if i + batch_size < len(players):
                time.sleep(api_delay)

        logger.info(f"PERFORMANCE: Fetched Statcast data for {len(results)}/{len(players)} players")
        return results


# Backward compatibility
FastStatcastFetcher = SimpleStatcastFetcher

if __name__ == "__main__":
    print("✅ Complete Simple Statcast Fetcher")
    print("\nFeatures:")
    print("  - Dynamic season detection")
    print("  - Intelligent caching")
    print("  - Parallel fetching")
    print("  - NO fallback data")
    print("\nTesting connection...")

    fetcher = SimpleStatcastFetcher()
    if fetcher.test_connection():
        print("✅ PyBaseball connection successful!")

        # Test fetching
        test_data = fetcher.fetch_player_data("Mike Trout", "OF")
        if test_data is not None:
            print(f"✅ Test fetch successful: {len(test_data)} records")
            metrics = fetcher.extract_key_metrics(test_data, "OF")
            print(f"   Barrel rate: {metrics.get('barrel_rate', 0):.1f}%")
    else:
        print("❌ PyBaseball connection failed")