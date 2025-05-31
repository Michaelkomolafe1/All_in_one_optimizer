#!/usr/bin/env python3
"""
Enhanced Baseball Savant Integration
Fetches REAL MLB data with intelligent caching and confirmed player priority
"""

import os
import json
import time
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore')

# Import pybaseball with proper error handling
try:
    from pybaseball import (
        statcast_batter_exitvelo_barrels,
        statcast_pitcher_exitvelo_barrels,
        statcast_batter_expected_stats,
        statcast_pitcher_expected_stats,
        cache
    )
    PYBASEBALL_AVAILABLE = True
    # Enable caching to reduce API calls
    cache.enable()
    print("🌐 pybaseball loaded - will fetch REAL Baseball Savant data")
except ImportError:
    PYBASEBALL_AVAILABLE = False
    print("❌ pybaseball not available - install with: pip install pybaseball")


class StatcastIntegration:
    """REAL Baseball Savant integration with confirmed player priority"""

    def __init__(self, cache_dir="data/statcast"):
        self.cache_dir = cache_dir
        self.cache_expiry_hours = 4  # 4 hours cache for current data
        self.current_year = datetime.now().year
        self.today = datetime.now().date()

        # Rate limiting settings - be respectful to Baseball Savant
        self.api_calls_made = 0
        self.last_api_call = None
        self.min_delay = 1.5  # 1.5 seconds between API calls

        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)

        # Load cached data
        self.batter_data_cache = {}
        self.pitcher_data_cache = {}
        self._load_cache()

        # Pre-load season data for faster lookups
        self.season_batter_data = None
        self.season_pitcher_data = None
        self.season_expected_batters = None
        self.season_expected_pitchers = None
        self.data_loaded = False

        print(f"🔬 Real Statcast integration initialized")
        if not PYBASEBALL_AVAILABLE:
            print("⚠️ pybaseball not available - will use fallback data")

    def _load_cache(self):
        """Load cached data from disk"""
        try:
            batter_cache_file = os.path.join(self.cache_dir, "batter_cache.json")
            pitcher_cache_file = os.path.join(self.cache_dir, "pitcher_cache.json")

            if os.path.exists(batter_cache_file):
                with open(batter_cache_file, 'r') as f:
                    self.batter_data_cache = json.load(f)

            if os.path.exists(pitcher_cache_file):
                with open(pitcher_cache_file, 'r') as f:
                    self.pitcher_data_cache = json.load(f)

            total_cached = len(self.batter_data_cache) + len(self.pitcher_data_cache)
            if total_cached > 0:
                print(f"💾 Loaded cache: {len(self.batter_data_cache)} batters, {len(self.pitcher_data_cache)} pitchers")
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}")
            self.batter_data_cache = {}
            self.pitcher_data_cache = {}

    def _save_cache(self):
        """Save cached data to disk"""
        try:
            batter_cache_file = os.path.join(self.cache_dir, "batter_cache.json")
            pitcher_cache_file = os.path.join(self.cache_dir, "pitcher_cache.json")

            with open(batter_cache_file, 'w') as f:
                json.dump(self.batter_data_cache, f, indent=2)

            with open(pitcher_cache_file, 'w') as f:
                json.dump(self.pitcher_data_cache, f, indent=2)

        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")

    def _rate_limit(self):
        """Implement rate limiting for API calls"""
        if self.last_api_call:
            elapsed = time.time() - self.last_api_call
            if elapsed < self.min_delay:
                sleep_time = self.min_delay - elapsed
                time.sleep(sleep_time)

        self.last_api_call = time.time()
        self.api_calls_made += 1

    def _is_cache_stale(self, player_name, is_pitcher=False):
        """Check if cached data is stale"""
        cache = self.pitcher_data_cache if is_pitcher else self.batter_data_cache

        if player_name not in cache:
            return True

        cache_time = cache[player_name].get('cache_timestamp')
        if not cache_time:
            return True

        try:
            cache_datetime = datetime.fromisoformat(cache_time)
            age_hours = (datetime.now() - cache_datetime).total_seconds() / 3600
            return age_hours > self.cache_expiry_hours
        except:
            return True

    def _load_season_data(self):
        """Load full season data for faster player lookups"""
        if self.data_loaded or not PYBASEBALL_AVAILABLE:
            return

        print("🌐 Loading current season data from Baseball Savant...")
        print("⏳ This may take 30-90 seconds for fresh data...")

        try:
            # Load batter data
            print("📊 Fetching batter exit velocity data...")
            self._rate_limit()
            self.season_batter_data = statcast_batter_exitvelo_barrels(self.current_year)

            print("📊 Fetching batter expected stats...")
            self._rate_limit()
            self.season_expected_batters = statcast_batter_expected_stats(self.current_year)

            print("📊 Fetching pitcher data...")
            self._rate_limit()
            self.season_pitcher_data = statcast_pitcher_exitvelo_barrels(self.current_year)

            print("📊 Fetching pitcher expected stats...")
            self._rate_limit()
            self.season_expected_pitchers = statcast_pitcher_expected_stats(self.current_year)

            self.data_loaded = True
            print("✅ Season data loaded successfully!")

        except Exception as e:
            print(f"⚠️ Error loading season data: {e}")
            print("Will use cached data or fallback to simulated...")
            self.data_loaded = False

    def _find_player_in_data(self, player_name, data_frame):
        """Find a player in a DataFrame using proper name matching"""
        if data_frame is None or data_frame.empty:
            return None

        # Baseball Savant uses 'last_name, first_name' format
        name_column = None
        if 'last_name, first_name' in data_frame.columns:
            name_column = 'last_name, first_name'
        elif 'player_name' in data_frame.columns:
            name_column = 'player_name'
        else:
            return None

        # Convert "Mookie Betts" to "Betts, Mookie" for matching
        if ' ' in player_name:
            parts = player_name.split()
            first_name = parts[0]
            last_name = ' '.join(parts[1:])
            savant_format = f"{last_name}, {first_name}"
        else:
            savant_format = player_name

        # Try exact match with converted format
        exact_matches = data_frame[data_frame[name_column] == savant_format]
        if not exact_matches.empty:
            return exact_matches.iloc[0]

        # Try case-insensitive exact match
        exact_matches_ci = data_frame[data_frame[name_column].str.upper() == savant_format.upper()]
        if not exact_matches_ci.empty:
            return exact_matches_ci.iloc[0]

        # Try partial match on last name
        if ',' in savant_format:
            last_name_only = savant_format.split(',')[0].strip()
            last_name_matches = data_frame[
                data_frame[name_column].str.contains(last_name_only, case=False, na=False)
            ]
            if not last_name_matches.empty:
                # Try to find best match
                for _, row in last_name_matches.iterrows():
                    if savant_format.upper() in row[name_column].upper():
                        return row
                # Return first match if no exact substring match
                return last_name_matches.iloc[0]

        return None

    def fetch_real_player_metrics(self, player_name, is_pitcher=False):
        """Fetch real metrics for a player from Baseball Savant"""

        if not PYBASEBALL_AVAILABLE:
            return self._generate_fallback_metrics(player_name, is_pitcher)

        # Check cache first
        if not self._is_cache_stale(player_name, is_pitcher):
            cache = self.pitcher_data_cache if is_pitcher else self.batter_data_cache
            cached_data = cache[player_name].copy()
            cached_data['data_source'] += ' (cached)'
            return cached_data

        # Load season data if not already loaded
        if not self.data_loaded:
            self._load_season_data()

        try:
            if is_pitcher:
                return self._fetch_real_pitcher_data(player_name)
            else:
                return self._fetch_real_batter_data(player_name)
        except Exception as e:
            print(f"⚠️ Error fetching real data for {player_name}: {e}")
            return self._generate_fallback_metrics(player_name, is_pitcher)

    def _fetch_real_batter_data(self, player_name):
        """Fetch real batter data from Baseball Savant"""
        try:
            # Find player in batter data
            batter_row = self._find_player_in_data(player_name, self.season_batter_data)
            expected_row = self._find_player_in_data(player_name, self.season_expected_batters)

            if batter_row is None and expected_row is None:
                return self._generate_fallback_metrics(player_name, False)

            # Extract metrics
            metrics = {
                'name': player_name,
                'data_source': 'Baseball Savant API',
                'fetch_timestamp': datetime.now().isoformat(),
                'cache_timestamp': datetime.now().isoformat(),
            }

            # Extract exit velocity metrics
            if batter_row is not None:
                ev_mapping = {
                    'hard_hit_percent': 'Hard_Hit',
                    'barrel_batted_rate': 'Barrel',
                    'avg_hit_speed': 'avg_exit_velocity',
                    'max_hit_speed': 'max_exit_velocity',
                    'avg_distance': 'avg_distance'
                }

                for savant_col, our_col in ev_mapping.items():
                    if savant_col in batter_row and pd.notna(batter_row[savant_col]):
                        metrics[our_col] = float(batter_row[savant_col])

            # Extract expected stats
            if expected_row is not None:
                exp_mapping = {
                    'xwoba': 'xwOBA',
                    'xba': 'xBA',
                    'xslg': 'xSLG',
                    'xiso': 'xISO'
                }

                for savant_col, our_col in exp_mapping.items():
                    if savant_col in expected_row and pd.notna(expected_row[savant_col]):
                        metrics[our_col] = float(expected_row[savant_col])

            # Fill in defaults for missing values
            defaults = {
                'Hard_Hit': 35.0,
                'Barrel': 6.0,
                'xwOBA': 0.320,
                'xBA': 0.250,
                'xSLG': 0.400,
                'avg_exit_velocity': 88.0,
                'K': 22.0,
                'BB': 8.5,
                'Pull': 38.0
            }

            for key, default_val in defaults.items():
                if key not in metrics:
                    metrics[key] = default_val

            # Cache the result
            self.batter_data_cache[player_name] = metrics
            self._save_cache()

            print(f"✅ Real Baseball Savant data fetched for batter: {player_name}")
            return metrics

        except Exception as e:
            print(f"⚠️ Error fetching real batter data for {player_name}: {e}")
            return self._generate_fallback_metrics(player_name, False)

    def _fetch_real_pitcher_data(self, player_name):
        """Fetch real pitcher data from Baseball Savant"""
        try:
            # Find player in pitcher data
            pitcher_row = self._find_player_in_data(player_name, self.season_pitcher_data)
            expected_row = self._find_player_in_data(player_name, self.season_expected_pitchers)

            if pitcher_row is None and expected_row is None:
                return self._generate_fallback_metrics(player_name, True)

            # Extract metrics
            metrics = {
                'name': player_name,
                'data_source': 'Baseball Savant API',
                'fetch_timestamp': datetime.now().isoformat(),
                'cache_timestamp': datetime.now().isoformat(),
            }

            # Extract pitcher metrics
            if pitcher_row is not None:
                pitcher_mapping = {
                    'hard_hit_percent': 'Hard_Hit',
                    'barrel_batted_rate': 'Barrel',
                    'avg_hit_speed': 'avg_exit_velocity'
                }

                for savant_col, our_col in pitcher_mapping.items():
                    if savant_col in pitcher_row and pd.notna(pitcher_row[savant_col]):
                        metrics[our_col] = float(pitcher_row[savant_col])

            # Extract expected stats for pitchers
            if expected_row is not None:
                exp_mapping = {
                    'xwoba': 'xwOBA',
                    'xera': 'xERA'
                }

                for savant_col, our_col in exp_mapping.items():
                    if savant_col in expected_row and pd.notna(expected_row[savant_col]):
                        metrics[our_col] = float(expected_row[savant_col])

            # Fill in defaults
            defaults = {
                'Hard_Hit': 33.0,
                'Barrel': 6.5,
                'xwOBA': 0.310,
                'xERA': 4.00,
                'avg_velocity': 93.0,
                'Whiff': 25.0,
                'K': 23.0,
                'BB': 8.0,
                'GB': 45.0
            }

            for key, default_val in defaults.items():
                if key not in metrics:
                    metrics[key] = default_val

            # Cache the result
            self.pitcher_data_cache[player_name] = metrics
            self._save_cache()

            print(f"✅ Real Baseball Savant data fetched for pitcher: {player_name}")
            return metrics

        except Exception as e:
            print(f"⚠️ Error fetching real pitcher data for {player_name}: {e}")
            return self._generate_fallback_metrics(player_name, True)

    def _generate_fallback_metrics(self, player_name, is_pitcher=False):
        """Generate fallback metrics when real data isn't available"""
        random.seed(hash(player_name) % 1000000)

        if is_pitcher:
            metrics = {
                'name': player_name,
                'data_source': 'fallback estimate',
                'fetch_timestamp': datetime.now().isoformat(),
                'cache_timestamp': datetime.now().isoformat(),
                'xwOBA': round(random.normalvariate(0.310, 0.030), 3),
                'Hard_Hit': round(random.normalvariate(33.0, 5.0), 1),
                'Barrel': round(random.normalvariate(6.5, 2.0), 1),
                'K': round(random.normalvariate(23.0, 4.0), 1),
                'BB': round(random.normalvariate(8.0, 2.0), 1),
                'GB': round(random.normalvariate(45.0, 6.0), 1),
                'Whiff': round(random.normalvariate(25.0, 5.0), 1),
                'avg_velocity': round(random.normalvariate(93.0, 3.0), 1)
            }
        else:
            metrics = {
                'name': player_name,
                'data_source': 'fallback estimate',
                'fetch_timestamp': datetime.now().isoformat(),
                'cache_timestamp': datetime.now().isoformat(),
                'xwOBA': round(random.normalvariate(0.320, 0.040), 3),
                'Hard_Hit': round(random.normalvariate(35.0, 7.0), 1),
                'Barrel': round(random.normalvariate(6.0, 3.0), 1),
                'K': round(random.normalvariate(22.0, 5.0), 1),
                'BB': round(random.normalvariate(8.5, 2.5), 1),
                'GB': round(random.normalvariate(42.0, 6.0), 1),
                'Pull': round(random.normalvariate(38.0, 7.0), 1),
                'avg_exit_velocity': round(random.normalvariate(88.0, 3.5), 1)
            }

        random.seed()
        return metrics

    def enrich_player_data(self, players, force_refresh=False):
        """Enrich player data with REAL Statcast metrics"""
        print(f"🌐 FETCHING REAL BASEBALL SAVANT DATA for {len(players)} players...")

        if PYBASEBALL_AVAILABLE:
            print("⏳ This will take 2-5 minutes for fresh data from Baseball Savant...")
            print("🔬 Loading current season statistics...")
        else:
            print("❌ pybaseball not available - using fallback estimates")

        enhanced_players = []
        start_time = time.time()
        real_data_count = 0
        fallback_count = 0
        cached_count = 0

        # Pre-load season data once for all players
        if PYBASEBALL_AVAILABLE and not self.data_loaded:
            self._load_season_data()

        for i, player in enumerate(players):
            player_name = player.name
            position = player.primary_position
            is_pitcher = position == "P"

            # Progress reporting
            if i % 5 == 0 and i > 0:
                elapsed = time.time() - start_time
                remaining_players = len(players) - i
                eta = (elapsed / i) * remaining_players if i > 0 else 0
                print(f"📊 Progress: {i}/{len(players)} ({real_data_count} real, {cached_count} cached) - ETA: {eta:.0f}s")

            # Create enhanced player data
            enhanced_player = player  # Use the actual OptimizedPlayer object

            # Fetch metrics (real data!)
            metrics = self.fetch_real_player_metrics(player_name, is_pitcher)

            # Count data sources
            data_source = metrics.get('data_source', '')
            if 'Baseball Savant API' in data_source:
                if 'cached' in data_source:
                    cached_count += 1
                else:
                    real_data_count += 1
            else:
                fallback_count += 1

            # Apply metrics to player
            enhanced_player.statcast_data = metrics
            enhanced_player._calculate_enhanced_score()

            enhanced_players.append(enhanced_player)

        elapsed = time.time() - start_time

        print(f"\n✅ REAL BASEBALL SAVANT DATA FETCH COMPLETED!")
        print(f"📊 Enhanced {len(enhanced_players)} players in {elapsed:.1f} seconds")
        print(f"🌐 Fresh Baseball Savant data: {real_data_count} players")
        print(f"💾 Cached Baseball Savant data: {cached_count} players")
        print(f"📊 Fallback estimates: {fallback_count} players")

        if self.api_calls_made > 0:
            print(f"🔥 API calls made this session: {self.api_calls_made}")

        total_real = real_data_count + cached_count
        if total_real > 0:
            print(f"🎯 Success rate: {total_real}/{len(players)} ({(total_real / len(players)) * 100:.1f}%) real Baseball Savant data")

        return enhanced_players
