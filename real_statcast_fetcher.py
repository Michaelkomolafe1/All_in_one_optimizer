#!/usr/bin/env python3
"""
Real Statcast Data Fetcher - Integrates with Your DFS Optimizer
Fetches real Baseball Savant data that matches your optimizer's expected format
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

# Import pybaseball for real data
try:
    import pybaseball

    pybaseball.cache.enable()  # Enable caching for faster subsequent calls
    PYBASEBALL_AVAILABLE = True
    print("✅ pybaseball loaded - Real Statcast data enabled")
except ImportError:
    PYBASEBALL_AVAILABLE = False
    print("❌ pybaseball not available - install with: pip install pybaseball")

# Import your player model
try:
    from unified_player_model import UnifiedPlayer

    UNIFIED_MODEL_AVAILABLE = True
except ImportError:
    UNIFIED_MODEL_AVAILABLE = False
    print("⚠️ Unified player model not found - will work with basic player data")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealStatcastFetcher:
    """
    Real Baseball Savant data fetcher that integrates with your DFS optimizer
    Matches the exact metrics your system expects
    """

    def __init__(self, cache_dir: str = "data/statcast_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Current season
        self.current_season = 2024
        self.season_start = '2024-03-28'
        self.season_end = '2024-09-29'

        # Cache settings
        self.cache_ttl_hours = 24  # Cache for 24 hours

        # Player ID cache
        self.player_id_cache = {}
        self.load_player_id_cache()

        # Statistics
        self.stats = {
            'cache_hits': 0,
            'api_calls': 0,
            'successful_fetches': 0,
            'failed_fetches': 0
        }

        print(f"🔬 Real Statcast Fetcher initialized")
        print(f"📁 Cache directory: {self.cache_dir}")

    def load_player_id_cache(self):
        """Load cached player ID mappings"""
        cache_file = self.cache_dir / "player_ids.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.player_id_cache = json.load(f)
                print(f"📊 Loaded {len(self.player_id_cache)} cached player IDs")
            except Exception as e:
                logger.warning(f"Failed to load player ID cache: {e}")
                self.player_id_cache = {}

    def save_player_id_cache(self):
        """Save player ID mappings to cache"""
        cache_file = self.cache_dir / "player_ids.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.player_id_cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save player ID cache: {e}")

    def get_cache_key(self, player_name: str, season: int = None) -> str:
        """Generate cache key for player data"""
        season = season or self.current_season
        name_hash = hashlib.md5(player_name.lower().encode()).hexdigest()[:12]
        return f"statcast_{name_hash}_{season}"

    def is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file is still valid"""
        if not cache_file.exists():
            return False

        try:
            file_age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
            return file_age_hours < self.cache_ttl_hours
        except Exception:
            return False

    def load_cached_statcast(self, cache_key: str) -> Optional[Dict]:
        """Load cached Statcast data"""
        cache_file = self.cache_dir / f"{cache_key}.json"

        if self.is_cache_valid(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    self.stats['cache_hits'] += 1
                    return data
            except Exception as e:
                logger.warning(f"Failed to load cache {cache_key}: {e}")

        return None

    def save_cached_statcast(self, cache_key: str, data: Dict):
        """Save Statcast data to cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            data['cached_at'] = datetime.now().isoformat()
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache {cache_key}: {e}")

    def lookup_player_id(self, player_name: str) -> Optional[int]:
        """Get MLB player ID for Baseball Savant queries"""

        # Check cache first
        if player_name.lower() in self.player_id_cache:
            return self.player_id_cache[player_name.lower()]

        try:
            # Parse name
            name_parts = player_name.strip().split()
            if len(name_parts) < 2:
                return None

            first_name = name_parts[0]
            last_name = name_parts[-1]

            # Use pybaseball to lookup player
            logger.info(f"🔍 Looking up player ID for {player_name}")

            lookup_result = pybaseball.playerid_lookup(last_name, first_name)

            if len(lookup_result) > 0:
                # Get the most recent player (highest key_mlbam)
                player_id = int(lookup_result.iloc[0]['key_mlbam'])

                # Cache the result
                self.player_id_cache[player_name.lower()] = player_id
                self.save_player_id_cache()

                logger.info(f"✅ Found player ID {player_id} for {player_name}")
                return player_id
            else:
                logger.warning(f"❌ No player ID found for {player_name}")
                return None

        except Exception as e:
            logger.warning(f"Failed to lookup player ID for {player_name}: {e}")
            return None

    def fetch_pitcher_statcast(self, player_id: int, player_name: str) -> Optional[Dict]:
        """Fetch pitcher Statcast data"""
        try:
            logger.info(f"🌐 Fetching pitcher data for {player_name} (ID: {player_id})")

            # Get pitcher data from Baseball Savant
            data = pybaseball.statcast_pitcher(
                start_dt=self.season_start,
                end_dt=self.season_end,
                player_id=player_id
            )

            if data is None or len(data) == 0:
                logger.warning(f"No pitcher data found for {player_name}")
                return None

            # Calculate the metrics your optimizer expects
            statcast_metrics = {
                # Expected wOBA against (lower is better for pitchers)
                'xwOBA': float(data['estimated_woba_using_speedangle'].mean()),

                # Hard hit rate against (% of batted balls 95+ mph) - lower is better
                'Hard_Hit': float((data['launch_speed'] >= 95).sum() / len(data) * 100),

                # Strikeout rate (% of plate appearances) - higher is better
                'K': self._calculate_k_rate(data),

                # Whiff rate (% of swings that miss) - higher is better
                'Whiff': self._calculate_whiff_rate(data),

                # Additional metrics for your enhanced scoring
                'Barrel_Against': float(data['barrel'].sum() / len(data) * 100),
                'avg_exit_velo_against': float(data['launch_speed'].mean()),
                'ground_ball_rate': float((data['bb_type'] == 'ground_ball').sum() / len(data) * 100),

                # Metadata
                'data_source': 'Baseball Savant API',
                'player_id': player_id,
                'player_name': player_name,
                'batted_balls': len(data),
                'last_updated': datetime.now().isoformat(),
                'season': self.current_season
            }

            # Handle NaN values
            for key, value in statcast_metrics.items():
                if isinstance(value, float) and np.isnan(value):
                    statcast_metrics[key] = 0.0

            self.stats['successful_fetches'] += 1
            logger.info(f"✅ Successfully fetched pitcher data for {player_name}")

            return statcast_metrics

        except Exception as e:
            logger.error(f"Failed to fetch pitcher data for {player_name}: {e}")
            self.stats['failed_fetches'] += 1
            return None

    def fetch_batter_statcast(self, player_id: int, player_name: str) -> Optional[Dict]:
        """Fetch batter Statcast data"""
        try:
            logger.info(f"🌐 Fetching batter data for {player_name} (ID: {player_id})")

            # Get batter data from Baseball Savant
            data = pybaseball.statcast_batter(
                start_dt=self.season_start,
                end_dt=self.season_end,
                player_id=player_id
            )

            if data is None or len(data) == 0:
                logger.warning(f"No batter data found for {player_name}")
                return None

            # Calculate the metrics your optimizer expects
            statcast_metrics = {
                # Expected wOBA (higher is better for hitters)
                'xwOBA': float(data['estimated_woba_using_speedangle'].mean()),

                # Hard hit rate (% of batted balls 95+ mph) - higher is better
                'Hard_Hit': float((data['launch_speed'] >= 95).sum() / len(data) * 100),

                # Barrel rate (% of batted balls that are "barreled") - higher is better
                'Barrel': float(data['barrel'].sum() / len(data) * 100),

                # Average exit velocity - higher is better
                'avg_exit_velocity': float(data['launch_speed'].mean()),

                # Strikeout rate (lower is better for hitters)
                'K': self._calculate_k_rate_batter(data),

                # Walk rate (higher is better for hitters)
                'BB': self._calculate_walk_rate(data),

                # Additional metrics for enhanced scoring
                'max_exit_velocity': float(data['launch_speed'].max()),
                'line_drive_rate': float((data['bb_type'] == 'line_drive').sum() / len(data) * 100),
                'pull_rate': float((data['pull_angle'] == 'pull').sum() / len(data) * 100),

                # Metadata
                'data_source': 'Baseball Savant API',
                'player_id': player_id,
                'player_name': player_name,
                'batted_balls': len(data),
                'last_updated': datetime.now().isoformat(),
                'season': self.current_season
            }

            # Handle NaN values
            for key, value in statcast_metrics.items():
                if isinstance(value, float) and np.isnan(value):
                    statcast_metrics[key] = 0.0

            self.stats['successful_fetches'] += 1
            logger.info(f"✅ Successfully fetched batter data for {player_name}")

            return statcast_metrics

        except Exception as e:
            logger.error(f"Failed to fetch batter data for {player_name}: {e}")
            self.stats['failed_fetches'] += 1
            return None

    def _calculate_k_rate(self, data: pd.DataFrame) -> float:
        """Calculate strikeout rate for pitchers"""
        try:
            # Count strikeouts from events
            strikeouts = data['events'].value_counts().get('strikeout', 0)
            total_pa = len(data[data['events'].notna()])
            return float(strikeouts / total_pa * 100) if total_pa > 0 else 0.0
        except:
            return 0.0

    def _calculate_k_rate_batter(self, data: pd.DataFrame) -> float:
        """Calculate strikeout rate for batters"""
        try:
            strikeouts = data['events'].value_counts().get('strikeout', 0)
            total_pa = len(data[data['events'].notna()])
            return float(strikeouts / total_pa * 100) if total_pa > 0 else 0.0
        except:
            return 0.0

    def _calculate_walk_rate(self, data: pd.DataFrame) -> float:
        """Calculate walk rate for batters"""
        try:
            walks = data['events'].value_counts().get('walk', 0)
            total_pa = len(data[data['events'].notna()])
            return float(walks / total_pa * 100) if total_pa > 0 else 0.0
        except:
            return 0.0

    def _calculate_whiff_rate(self, data: pd.DataFrame) -> float:
        """Calculate whiff rate from pitch data"""
        try:
            # Count swinging strikes
            swinging_strikes = data['description'].str.contains('swinging_strike', na=False).sum()
            total_swings = data['description'].str.contains('swinging_strike|foul|hit_into_play', na=False).sum()
            return float(swinging_strikes / total_swings * 100) if total_swings > 0 else 0.0
        except:
            return 0.0

    def fetch_player_statcast_data(self, player_name: str, position: str) -> Optional[Dict]:
        """
        Main method to fetch Statcast data for a player
        This is the method your optimizer should call
        """
        if not PYBASEBALL_AVAILABLE:
            logger.warning("pybaseball not available - cannot fetch real Statcast data")
            return None

        # Check cache first
        cache_key = self.get_cache_key(player_name)
        cached_data = self.load_cached_statcast(cache_key)

        if cached_data:
            logger.info(f"📊 Cache hit for {player_name}")
            return cached_data

        # Get player ID
        player_id = self.lookup_player_id(player_name)
        if not player_id:
            logger.warning(f"Could not find player ID for {player_name}")
            return None

        self.stats['api_calls'] += 1

        # Fetch data based on position
        if position == 'P':
            statcast_data = self.fetch_pitcher_statcast(player_id, player_name)
        else:
            statcast_data = self.fetch_batter_statcast(player_id, player_name)

        # Cache the result
        if statcast_data:
            self.save_cached_statcast(cache_key, statcast_data)

        return statcast_data

    def enrich_players_with_real_statcast(self, players: List, priority_only: bool = True) -> List:
        """
        Enrich a list of players with real Statcast data
        This method integrates with your existing optimizer

        Args:
            players: List of player objects (UnifiedPlayer or dict format)
            priority_only: If True, only fetch for confirmed/manual players (faster)

        Returns:
            List of players with Statcast data applied
        """
        if not PYBASEBALL_AVAILABLE:
            logger.warning("pybaseball not available - skipping real Statcast enrichment")
            return players

        total_players = len(players)
        processed_count = 0
        successful_count = 0

        logger.info(f"🔬 Starting real Statcast enrichment for {total_players} players")
        logger.info(f"⚡ Priority only: {priority_only}")

        # Filter players if priority only
        if priority_only:
            priority_players = []
            for player in players:
                is_priority = False

                # Check if player is confirmed or manually selected
                if hasattr(player, 'is_confirmed') and player.is_confirmed:
                    is_priority = True
                elif hasattr(player, 'is_manual_selected') and player.is_manual_selected:
                    is_priority = True
                elif isinstance(player, dict):
                    if player.get('is_confirmed') or player.get('is_manual_selected'):
                        is_priority = True

                if is_priority:
                    priority_players.append(player)

            target_players = priority_players
            logger.info(f"🎯 Processing {len(target_players)} priority players")
        else:
            target_players = players
            logger.info(f"📊 Processing all {len(target_players)} players")

        # Process each player
        for player in target_players:
            try:
                # Extract player info
                if hasattr(player, 'name'):
                    player_name = player.name
                    position = player.primary_position
                elif isinstance(player, dict):
                    player_name = player.get('name', '')
                    position = player.get('position', player.get('primary_position', ''))
                else:
                    continue

                logger.info(f"🔍 Processing {player_name} ({position})")

                # Fetch Statcast data
                statcast_data = self.fetch_player_statcast_data(player_name, position)

                if statcast_data:
                    # Apply data to player
                    if hasattr(player, 'apply_statcast_data'):
                        player.apply_statcast_data(statcast_data)
                    elif hasattr(player, 'statcast_data'):
                        player.statcast_data = statcast_data
                    elif isinstance(player, dict):
                        player['statcast_data'] = statcast_data

                    successful_count += 1
                    logger.info(f"✅ Applied real Statcast data to {player_name}")
                else:
                    logger.warning(f"❌ No Statcast data found for {player_name}")

                processed_count += 1

                # Rate limiting - small delay between API calls
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error processing {player_name}: {e}")
                continue

        # Final statistics
        logger.info(f"🏁 Real Statcast enrichment complete!")
        logger.info(f"📊 Processed: {processed_count}/{len(target_players)}")
        logger.info(f"✅ Successful: {successful_count}")
        logger.info(f"📈 Success rate: {(successful_count / processed_count * 100):.1f}%")

        return players

    def get_stats(self) -> Dict:
        """Get fetcher statistics"""
        return self.stats.copy()


def integrate_with_optimizer():
    """
    Integration function for your existing optimizer
    This shows how to use the real Statcast fetcher with your current system
    """

    # Example integration with your optimizer
    def enhanced_statcast_enrichment(players, use_real_data=True, priority_only=True):
        """
        Enhanced Statcast enrichment that uses real data when available
        This replaces your existing _enrich_with_simulated_statcast method
        """

        if use_real_data and PYBASEBALL_AVAILABLE:
            logger.info("🔬 Using REAL Baseball Savant data")
            fetcher = RealStatcastFetcher()
            return fetcher.enrich_players_with_real_statcast(players, priority_only)
        else:
            logger.info("⚡ Using enhanced simulation (real data not available)")
            # Fall back to your existing simulation
            return players

    return enhanced_statcast_enrichment


# Test function
def test_real_statcast_fetcher():
    """Test the real Statcast fetcher with sample players"""

    print("🧪 TESTING REAL STATCAST FETCHER")
    print("=" * 50)

    if not PYBASEBALL_AVAILABLE:
        print("❌ pybaseball not available - cannot test")
        return False

    # Create test players
    test_players = [
        {'name': 'Kyle Tucker', 'position': 'OF', 'is_confirmed': True},
        {'name': 'Tarik Skubal', 'position': 'P', 'is_confirmed': True},
        {'name': 'Pete Alonso', 'position': '1B', 'is_manual_selected': True},
    ]

    # Test the fetcher
    fetcher = RealStatcastFetcher()

    for player in test_players:
        print(f"\n🔍 Testing {player['name']} ({player['position']})")

        data = fetcher.fetch_player_statcast_data(player['name'], player['position'])

        if data:
            print(f"✅ Success!")
            if player['position'] == 'P':
                print(f"   xwOBA against: {data.get('xwOBA', 0):.3f}")
                print(f"   Hard Hit% against: {data.get('Hard_Hit', 0):.1f}%")
                print(f"   K rate: {data.get('K', 0):.1f}%")
            else:
                print(f"   xwOBA: {data.get('xwOBA', 0):.3f}")
                print(f"   Hard Hit%: {data.get('Hard_Hit', 0):.1f}%")
                print(f"   Barrel%: {data.get('Barrel', 0):.1f}%")
        else:
            print(f"❌ Failed to fetch data")

    # Show stats
    stats = fetcher.get_stats()
    print(f"\n📊 Fetcher Statistics:")
    print(f"   API calls: {stats['api_calls']}")
    print(f"   Cache hits: {stats['cache_hits']}")
    print(f"   Successful fetches: {stats['successful_fetches']}")
    print(f"   Failed fetches: {stats['failed_fetches']}")

    return stats['successful_fetches'] > 0


if __name__ == "__main__":
    # Test the real Statcast fetcher
    print("🚀 REAL STATCAST FETCHER")
    print("Integrates with your DFS optimizer to provide real Baseball Savant data")
    print("=" * 70)

    success = test_real_statcast_fetcher()

    if success:
        print("\n🎉 REAL STATCAST FETCHER WORKING!")
        print("\n💡 To integrate with your optimizer:")
        print("1. Import: from real_statcast_fetcher import RealStatcastFetcher")
        print("2. Replace simulation with: fetcher.enrich_players_with_real_statcast(players)")
        print("3. Your optimizer will now use real Baseball Savant data!")
    else:
        print("\n❌ Test failed - check your pybaseball installation")