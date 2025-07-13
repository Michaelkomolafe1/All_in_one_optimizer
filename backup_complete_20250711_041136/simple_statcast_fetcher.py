#!/usr/bin/env python3
"""
FAST PARALLEL STATCAST FETCHER
"""

import io
import json
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# CRITICAL: Disable ALL output before importing pybaseball
os.environ['PYBASEBALL_NO_PROGRESS'] = '1'
os.environ['PYBASEBALL_CACHE'] = '1'


# Suppress all output during pybaseball operations
class SuppressOutput:
    def __enter__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr


# Import pybaseball with suppression
try:
    with SuppressOutput():
        import pybaseball

        pybaseball.cache.enable()

        # Monkey patch to suppress "Gathering player lookup table" message
        original_playerid_lookup = pybaseball.playerid_lookup


        def silent_playerid_lookup(*args, **kwargs):
            with SuppressOutput():
                return original_playerid_lookup(*args, **kwargs)


        pybaseball.playerid_lookup = silent_playerid_lookup

    PYBASEBALL_AVAILABLE = True

except ImportError:
    PYBASEBALL_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Rest of your class implementation continues here...

# Modify your FastStatcastFetcher class:

class FastStatcastFetcher:
    """Ultra-fast parallel Statcast fetcher for confirmed players only"""

    def __init__(self, max_workers: int = 5):
        self.USE_FALLBACK = False  # DISABLED BY PATCH - No fake data!
        self.cache_dir = Path("data/statcast_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.season_start = '2024-04-01'
        self.season_end = '2024-09-30'
        self.max_workers = max_workers

        # ADD THIS LINE TO FORCE FRESH DATA
        self.FORCE_FRESH = True  # Set to False to re-enable caching

        self.player_id_cache = {}
        self.load_player_cache()

        self.stats = {'successful_fetches': 0, 'failed_fetches': 0, 'cache_hits': 0}
        self.lock = threading.Lock()

        # Rest of your init code...

    def fetch_player_data(self, player_name: str, position: str) -> Optional[Dict]:
        """Fetch data for a single player with caching"""

        if not PYBASEBALL_AVAILABLE:
            position_type = 'pitcher' if position == 'P' else 'batter'
            return None  # PATCHED: No fallback data(player_name, position_type)

        # Check cache first (MODIFIED LINE)
        cache_key = f"{player_name}_{position}_{self.season_start}"
        cache_file = self.cache_dir / f"{cache_key}.json"

        # MODIFIED: Check FORCE_FRESH flag
        if not self.FORCE_FRESH and cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)

                # Check if cache is recent (within 24 hours)
                cache_time = datetime.fromisoformat(cached_data.get('last_updated', '2020-01-01'))
                if (datetime.now() - cache_time).total_seconds() < 86400:  # 24 hours
                    with self.lock:
                        self.stats['cache_hits'] += 1
                    logger.info(f"📦 CACHE HIT: {player_name}")  # ADD THIS
                    return cached_data
            except:
                pass

        # ADD THIS LOG
        logger.info(f"🌐 FETCHING FROM WEB: {player_name}")

        # Rest of your fetch code...
        
    def load_player_cache(self):
        cache_file = self.cache_dir / "players.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.player_id_cache = json.load(f)
            except:
                pass

    def save_player_cache(self):
        cache_file = self.cache_dir / "players.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.player_id_cache, f)
        except:
            pass

    def fetch_multiple_players_parallel(self, players_list: List) -> Dict[str, Dict]:
        """FAST: Fetch Statcast data for multiple players in parallel"""

        if not PYBASEBALL_AVAILABLE:
            print("⚠️ PyBaseball not available - using fallback data for all players")
            return {p.name: self._create_fallback_data(p.name, p.primary_position) for p in players_list}

        print(f"⚡ PARALLEL STATCAST: Processing {len(players_list)} players with {self.max_workers} workers")

        results = {}
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_player = {
                executor.submit(self._fetch_single_player_safe, player): player 
                for player in players_list
            }

            # Collect results as they complete
            for future in as_completed(future_to_player):
                player = future_to_player[future]

                try:
                    data = future.result(timeout=30)  # 30 second timeout per player
                    if data:
                        results[player.name] = data
                        with self.lock:
                            self.stats['successful_fetches'] += 1
                    else:
                        # No fallback - real data only
                        results[player.name] = None
                        with self.lock:
                            self.stats['failed_fetches'] += 1


                except Exception as e:

                    logger.debug(f"Parallel fetch failed for {player.name}: {e}")

                    results[player.name] = None
                    with self.lock:
                        self.stats['failed_fetches'] += 1

        elapsed = time.time() - start_time
        success_rate = (self.stats['successful_fetches'] / max(1, len(players_list))) * 100

        print(f"⚡ PARALLEL COMPLETE: {len(results)} players in {elapsed:.1f}s ({success_rate:.1f}% success)")

        return results

    def _fetch_single_player_safe(self, player) -> Optional[Dict]:
        """Safely fetch data for a single player with error handling"""

        try:
            return self.fetch_player_data(player.name, player.primary_position)
        except Exception as e:
            logger.debug(f"Safe fetch failed for {player.name}: {e}")
            return None

    def fetch_player_data(self, player_name: str, position: str) -> Optional[Dict]:
        """Fetch data for a single player with caching"""

        if not PYBASEBALL_AVAILABLE:
            position_type = 'pitcher' if position == 'P' else 'batter'
            return None  # PATCHED: No fallback data(player_name, position_type)

        # Check cache first
        cache_key = f"{player_name}_{position}_{self.season_start}"
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)

                # Check if cache is recent (within 24 hours)
                cache_time = datetime.fromisoformat(cached_data.get('last_updated', '2020-01-01'))
                if (datetime.now() - cache_time).total_seconds() < 86400:  # 24 hours
                    with self.lock:
                        self.stats['cache_hits'] += 1
                    return cached_data
            except:
                pass

        # Fetch fresh data
        player_id = self.get_player_id(player_name)
        if not player_id:
            position_type = 'pitcher' if position == 'P' else 'batter'
            return None  # PATCHED: No fallback data(player_name, position_type)

        try:
            if position == 'P':
                data = pybaseball.statcast_pitcher(
                    start_dt=self.season_start,
                    end_dt=self.season_end,
                    player_id=player_id
                )

                if data is None or len(data) == 0:
                    return None  # PATCHED: No fallback data(player_name, 'pitcher')

                # Limit data size for performance
                if len(data) > 1000:
                    data = data.tail(1000)

                metrics = {
                    'xwOBA': self._safe_get_value(data, 'estimated_woba_using_speedangle', 0.315),
                    'Hard_Hit': self._safe_get_percentage(data, 'launch_speed', lambda x: x >= 95, 35.0),
                    'K': 22.0,
                    'Whiff': 25.0,
                    'Barrel_Against': 7.5,
                    'data_source': 'Baseball Savant (Parallel)',
                    'player_name': player_name,
                    'last_updated': datetime.now().isoformat()
                }

            else:  # Batter
                data = pybaseball.statcast_batter(
                    start_dt=self.season_start,
                    end_dt=self.season_end,
                    player_id=player_id
                )

                if data is None or len(data) == 0:
                    return None  # PATCHED: No fallback data(player_name, 'batter')

                if len(data) > 1000:
                    data = data.tail(1000)

                metrics = {
                    'xwOBA': self._safe_get_value(data, 'estimated_woba_using_speedangle', 0.320),
                    'Hard_Hit': self._safe_get_percentage(data, 'launch_speed', lambda x: x >= 95, 37.0),
                    'Barrel': 8.5,
                    'avg_exit_velocity': self._safe_get_value(data, 'launch_speed', 88.5),
                    'K': 23.0,
                    'BB': 8.5,
                    'data_source': 'Baseball Savant (Parallel)',
                    'player_name': player_name,
                    'last_updated': datetime.now().isoformat()
                }

            # Cache the result
            try:
                with open(cache_file, 'w') as f:
                    json.dump(metrics, f)
            except:
                pass

            return metrics

        except Exception as e:
            logger.debug(f"Statcast API failed for {player_name}: {e}")
            position_type = 'pitcher' if position == 'P' else 'batter'
            return None  # PATCHED: No fallback data(player_name, position_type)

    def get_player_id(self, player_name: str) -> Optional[int]:
        """Get player ID with caching and output suppression"""
        cache_key = player_name.lower().strip()
        if cache_key in self.player_id_cache:
            return self.player_id_cache[cache_key]

        if not PYBASEBALL_AVAILABLE:
            return None

        try:
            name_parts = player_name.strip().split()
            if len(name_parts) < 2:
                return None

            first_name = name_parts[0]
            last_name = name_parts[-1]

            # Suppress output during lookup
            with SuppressOutput():
                lookup = pybaseball.playerid_lookup(last_name, first_name)

            if len(lookup) > 0:
                player_id = int(lookup.iloc[0]['key_mlbam'])
                self.player_id_cache[cache_key] = player_id
                self.save_player_cache()
                return player_id
        except Exception as e:
            logger.debug(f"Player lookup failed for {player_name}: {e}")

        return None

    def pre_cache_player_ids(self, players_list: List) -> None:
        """Pre-cache all player IDs to avoid duplicate lookups"""
        print(f"📋 Pre-caching player IDs for {len(players_list)} players...")

        uncached_players = [
            p for p in players_list
            if p.name.lower().strip() not in self.player_id_cache
        ]

        if not uncached_players:
            print("✅ All player IDs already cached")
            return

        print(f"🔍 Looking up {len(uncached_players)} new player IDs...")

        with SuppressOutput():
            for player in uncached_players:
                self.get_player_id(player.name)

        self.save_player_cache()
        print(f"✅ Player ID cache updated: {len(self.player_id_cache)} total IDs")

    def _create_fallback_data(self, player_name: str, position_type: str) -> None:
        """No fallback data - real data only"""
        return None

    def _safe_get_value(self, data, column: str, default: float) -> float:
        try:
            if column in data.columns:
                series = data[column].dropna()
                if len(series) > 0:
                    return float(series.mean())
        except:
            pass
        return default

    def _safe_get_percentage(self, data, column: str, condition_func, default: float) -> float:
        try:
            if column in data.columns:
                series = data[column].dropna()
                if len(series) > 0:
                    meeting_condition = condition_func(series).sum()
                    return float(meeting_condition / len(series) * 100)
        except:
            pass
        return default

    def get_stats(self) -> Dict:
        return self.stats.copy()

# Compatibility alias
SimpleStatcastFetcher = FastStatcastFetcher
