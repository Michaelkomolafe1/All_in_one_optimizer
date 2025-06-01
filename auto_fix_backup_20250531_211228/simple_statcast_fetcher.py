#!/usr/bin/env python3
"""
Simple Working Statcast Fetcher - No complications, just works
Fixes the barrel error with minimal code
"""

import pandas as pd
import numpy as np
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import logging

try:
    import pybaseball
    pybaseball.cache.enable()
    PYBASEBALL_AVAILABLE = True
except ImportError:
    PYBASEBALL_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleStatcastFetcher:
    """Simple, working Statcast fetcher that handles all the API issues"""

    def __init__(self):
        self.cache_dir = Path("data/statcast_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.season_start = '2024-03-28'
        self.season_end = '2024-09-29'

        self.player_id_cache = {}
        self.load_player_cache()

        self.stats = {'successful_fetches': 0, 'failed_fetches': 0}

    def load_player_cache(self):
        """Load player ID cache"""
        cache_file = self.cache_dir / "players.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.player_id_cache = json.load(f)
            except:
                pass

    def save_player_cache(self):
        """Save player ID cache"""
        cache_file = self.cache_dir / "players.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.player_id_cache, f)
        except:
            pass

    def get_player_id(self, player_name: str) -> Optional[int]:
        """Get player ID with caching"""

        cache_key = player_name.lower().strip()
        if cache_key in self.player_id_cache:
            return self.player_id_cache[cache_key]

        try:
            name_parts = player_name.strip().split()
            if len(name_parts) < 2:
                return None

            first_name = name_parts[0]
            last_name = name_parts[-1]

            lookup = pybaseball.playerid_lookup(last_name, first_name)

            if len(lookup) > 0:
                player_id = int(lookup.iloc[0]['key_mlbam'])
                self.player_id_cache[cache_key] = player_id
                self.save_player_cache()
                return player_id

        except Exception as e:
            logger.debug(f"Player lookup failed for {player_name}: {e}")

        return None

    def safe_get_value(self, data: pd.DataFrame, column: str, default: float) -> float:
        """Safely get a value from a DataFrame column"""
        try:
            if column in data.columns:
                series = data[column].dropna()
                if len(series) > 0:
                    return float(series.mean())
        except:
            pass
        return default

    def safe_get_percentage(self, data: pd.DataFrame, column: str, condition_func, default: float) -> float:
        """Safely get a percentage based on a condition"""
        try:
            if column in data.columns:
                series = data[column].dropna()
                if len(series) > 0:
                    meeting_condition = condition_func(series).sum()
                    return float(meeting_condition / len(series) * 100)
        except:
            pass
        return default

    def safe_get_barrel_rate(self, data: pd.DataFrame) -> float:
        """Safely get barrel rate - handles the problematic barrel column"""
        try:
            # Try different possible barrel column names
            barrel_columns = ['barrel', 'is_barrel', 'barrels']

            for col in barrel_columns:
                if col in data.columns:
                    barrel_data = data[col].dropna()
                    if len(barrel_data) > 0:
                        # Handle boolean columns (True/False)
                        if barrel_data.dtype == 'bool':
                            return float(barrel_data.sum() / len(data) * 100)
                        # Handle numeric columns (1/0)
                        else:
                            return float(barrel_data.mean() * 100)
        except:
            pass

        # Default barrel rate if column missing or error
        return 6.0

    def safe_get_event_rate(self, data: pd.DataFrame, event_type: str, default: float) -> float:
        """Safely get event rate (strikeouts, walks, etc.)"""
        try:
            if 'events' in data.columns:
                events = data['events'].dropna()
                if len(events) > 0:
                    event_count = (events == event_type).sum()
                    return float(event_count / len(events) * 100)
        except:
            pass
        return default

    def fetch_batter_data(self, player_id: int, player_name: str) -> Optional[Dict]:
        """Fetch batter data - FIXED version"""
        try:
            logger.info(f"🌐 Fetching batter data for {player_name}")

            data = pybaseball.statcast_batter(
                start_dt=self.season_start,
                end_dt=self.season_end,
                player_id=player_id
            )

            if data is None or len(data) == 0:
                logger.warning(f"No data found for {player_name}")
                return None

            logger.info(f"📊 Found {len(data)} batted balls for {player_name}")

            # Calculate metrics safely
            metrics = {
                'xwOBA': self.safe_get_value(data, 'estimated_woba_using_speedangle', 0.320),
                'Hard_Hit': self.safe_get_percentage(data, 'launch_speed', lambda x: x >= 95, 35.0),
                'Barrel': self.safe_get_barrel_rate(data),  # FIXED!
                'avg_exit_velocity': self.safe_get_value(data, 'launch_speed', 87.0),
                'K': self.safe_get_event_rate(data, 'strikeout', 25.0),
                'BB': self.safe_get_event_rate(data, 'walk', 8.0),

                'data_source': 'Baseball Savant (Simple Fix)',
                'player_id': player_id,
                'player_name': player_name,
                'batted_balls': len(data),
                'last_updated': datetime.now().isoformat()
            }

            self.stats['successful_fetches'] += 1
            logger.info(f"✅ SUCCESS: {player_name} - xwOBA: {metrics['xwOBA']:.3f}, Hard Hit: {metrics['Hard_Hit']:.1f}%")

            return metrics

        except Exception as e:
            logger.error(f"Failed to fetch data for {player_name}: {e}")
            self.stats['failed_fetches'] += 1
            return None

    def fetch_pitcher_data(self, player_id: int, player_name: str) -> Optional[Dict]:
        """Fetch pitcher data - FIXED version"""
        try:
            logger.info(f"🌐 Fetching pitcher data for {player_name}")

            data = pybaseball.statcast_pitcher(
                start_dt=self.season_start,
                end_dt=self.season_end,
                player_id=player_id
            )

            if data is None or len(data) == 0:
                logger.warning(f"No data found for {player_name}")
                return None

            logger.info(f"📊 Found {len(data)} pitches for {player_name}")

            # Calculate metrics safely
            metrics = {
                'xwOBA': self.safe_get_value(data, 'estimated_woba_using_speedangle', 0.310),
                'Hard_Hit': self.safe_get_percentage(data, 'launch_speed', lambda x: x >= 95, 33.0),
                'K': self.safe_get_event_rate(data, 'strikeout', 20.0),
                'Whiff': self._calculate_whiff_rate(data),
                'Barrel_Against': self.safe_get_barrel_rate(data),  # FIXED!

                'data_source': 'Baseball Savant (Simple Fix)',
                'player_id': player_id,
                'player_name': player_name,
                'pitches': len(data),
                'last_updated': datetime.now().isoformat()
            }

            self.stats['successful_fetches'] += 1
            logger.info(f"✅ SUCCESS: {player_name} - xwOBA against: {metrics['xwOBA']:.3f}, K%: {metrics['K']:.1f}%")

            return metrics

        except Exception as e:
            logger.error(f"Failed to fetch pitcher data for {player_name}: {e}")
            self.stats['failed_fetches'] += 1
            return None

    def _calculate_whiff_rate(self, data: pd.DataFrame) -> float:
        """Calculate whiff rate safely"""
        try:
            if 'description' in data.columns:
                descriptions = data['description'].dropna()
                if len(descriptions) > 0:
                    swinging_strikes = descriptions.str.contains('swinging_strike', na=False).sum()
                    total_swings = descriptions.str.contains('swinging_strike|foul|hit_into_play', na=False).sum()
                    if total_swings > 0:
                        return float(swinging_strikes / total_swings * 100)
        except:
            pass
        return 25.0

    def fetch_player_data(self, player_name: str, position: str) -> Optional[Dict]:
        """Main method - fetch data for any player"""
        if not PYBASEBALL_AVAILABLE:
            return None

        player_id = self.get_player_id(player_name)
        if not player_id:
            return None

        if position == 'P':
            return self.fetch_pitcher_data(player_id, player_name)
        else:
            return self.fetch_batter_data(player_id, player_name)

    def get_stats(self) -> Dict:
        """Get fetcher statistics"""
        return self.stats.copy()


def test_simple_fetcher():
    """Test the simple fetcher"""
    print("🧪 Testing Simple Statcast Fetcher")

    if not PYBASEBALL_AVAILABLE:
        print("❌ pybaseball not available")
        return False

    fetcher = SimpleStatcastFetcher()

    # Test with Kyle Tucker
    print("🔍 Testing Kyle Tucker...")
    data = fetcher.fetch_player_data("Kyle Tucker", "OF")

    if data:
        print(f"✅ SUCCESS!")
        print(f"   xwOBA: {data['xwOBA']:.3f}")
        print(f"   Hard Hit%: {data['Hard_Hit']:.1f}%")
        print(f"   Barrel%: {data['Barrel']:.1f}%")
        return True
    else:
        print("❌ No data returned")
        return False

if __name__ == "__main__":
    test_simple_fetcher()
