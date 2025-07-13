#!/usr/bin/env python3
"""
Recent Form Analyzer - ENHANCED with batch processing
===================================================
Efficient batch processing for faster analysis
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from pybaseball import playerid_lookup, statcast_batter

logger = logging.getLogger(__name__)


class RecentFormAnalyzer:
    """
    ENHANCED: Analyzes recent player form with efficient batch processing
    """

    def __init__(self, cache_manager=None, days_back: int = 7,
                 batch_size: int = 10, max_workers: int = 3):
        self.cache_manager = cache_manager
        self.days_back = days_back
        self.batch_size = batch_size
        self.max_workers = max_workers

        # Time windows
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=days_back)

        # Caches
        self._player_id_cache = {}
        self._game_data_cache = {}

        # Recency weights for scoring
        self.recency_weights = [1.0, 0.9, 0.8, 0.7, 0.6]  # Most recent games weighted higher

        logger.info(f"Form analyzer initialized: {days_back} days, batch size {batch_size}")

    def analyze_players_batch(self, players: List[Any],
                              use_cache: bool = True,
                              progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        ENHANCED: Analyze multiple players in parallel batches

        Args:
            players: List of players to analyze
            use_cache: Whether to use cached results
            progress_callback: Optional progress callback

        Returns:
            Dict mapping player ID to form data
        """
        results = {}
        total_players = len(players)

        print(f"\n📊 Batch analyzing {total_players} players...")
        print(f"   Batch size: {self.batch_size}")
        print(f"   Max parallel workers: {self.max_workers}")

        # Try to import progress tracker
        try:
            from progress_tracker import ProgressTracker
            tracker = ProgressTracker(total_players, "Analyzing form (batch)", show_eta=True)
        except:
            tracker = None

        # Process in batches
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit batches
            futures = []

            for i in range(0, total_players, self.batch_size):
                batch = players[i:i + self.batch_size]
                future = executor.submit(self._process_batch, batch, use_cache)
                futures.append((future, i))

            # Process results as they complete
            for future, batch_start in futures:
                try:
                    batch_results = future.result(timeout=30)
                    results.update(batch_results)

                    # Update progress
                    if tracker:
                        tracker.update(len(batch_results))
                    elif progress_callback:
                        progress_callback(len(results), total_players)

                except Exception as e:
                    logger.error(f"Batch processing error: {e}")

        if tracker:
            tracker.finish()

        # Apply results to players
        success_count = self._apply_batch_results_to_players(players, results)

        print(f"\n✅ Batch analysis complete: {success_count}/{total_players} successful")

        return results

    def _process_batch(self, players: List[Any], use_cache: bool) -> Dict[str, Any]:
        """Process a single batch of players"""
        batch_results = {}

        for player in players:
            try:
                # Check cache first
                if use_cache and self._has_cached_form_data(player):
                    cached_data = self._get_cached_form_data(player)
                    if cached_data:
                        batch_results[player.id] = cached_data
                        continue

                # Get player MLB ID
                player_id = self._get_player_mlb_id_cached(player.name)
                if not player_id:
                    batch_results[player.id] = self._get_default_form_data()
                    continue

                # Fetch game data
                game_data = self._fetch_game_data_cached(player_id)

                # Calculate metrics
                form_data = self._calculate_form_metrics(game_data, player)

                # Cache result
                if self.cache_manager and form_data:
                    cache_key = f"form_{player.id}_{self.days_back}d"
                    self.cache_manager.set(cache_key, form_data, ttl=3600)  # 1 hour cache

                batch_results[player.id] = form_data

            except Exception as e:
                logger.debug(f"Error processing {player.name}: {e}")
                batch_results[player.id] = self._get_default_form_data()

        return batch_results

    def _get_player_mlb_id_cached(self, player_name: str) -> Optional[int]:
        """Get player MLB ID with caching"""
        if player_name in self._player_id_cache:
            return self._player_id_cache[player_name]

        try:
            # Parse name
            parts = player_name.strip().split()
            if len(parts) < 2:
                return None

            first = parts[0]
            last = ' '.join(parts[1:])

            # Lookup player
            results = playerid_lookup(last, first)
            if not results.empty:
                # Get most recent player
                results = results.sort_values('mlb_played_last', ascending=False)
                player_id = int(results.iloc[0]['key_mlbam'])
                self._player_id_cache[player_name] = player_id
                return player_id

        except Exception as e:
            logger.debug(f"Player lookup failed for {player_name}: {e}")

        self._player_id_cache[player_name] = None
        return None

    def _fetch_game_data_cached(self, player_id: int) -> pd.DataFrame:
        """Fetch game data with caching"""
        cache_key = f"games_{player_id}_{self.start_date.strftime('%Y%m%d')}"

        if cache_key in self._game_data_cache:
            return self._game_data_cache[cache_key]

        try:
            # Fetch from Baseball Savant
            data = statcast_batter(
                start_dt=self.start_date.strftime('%Y-%m-%d'),
                end_dt=self.end_date.strftime('%Y-%m-%d'),
                player_id=player_id
            )

            self._game_data_cache[cache_key] = data
            return data

        except Exception as e:
            logger.debug(f"Failed to fetch data for player {player_id}: {e}")
            return pd.DataFrame()

    def _calculate_form_metrics(self, game_data: pd.DataFrame, player: Any) -> Dict[str, Any]:
        """Calculate form metrics from game data"""
        if game_data.empty:
            return self._get_default_form_data()

        try:
            # Basic counting stats
            games = len(game_data['game_date'].unique()) if 'game_date' in game_data else 0

            if games == 0:
                return self._get_default_form_data()

            # Event counts
            events = game_data['events'].value_counts() if 'events' in game_data else pd.Series()

            # Calculate hits
            hits = sum([
                events.get('single', 0),
                events.get('double', 0),
                events.get('triple', 0),
                events.get('home_run', 0)
            ])

            # At bats
            ab_events = ['single', 'double', 'triple', 'home_run', 'strikeout',
                         'field_out', 'grounded_into_double_play', 'force_out',
                         'fielders_choice', 'field_error']
            at_bats = sum(events.get(event, 0) for event in ab_events)

            # Calculate averages
            batting_avg = hits / at_bats if at_bats > 0 else 0.250

            # Advanced metrics
            walks = events.get('walk', 0)

            # OBP calculation
            plate_appearances = at_bats + walks + events.get('hit_by_pitch', 0)
            obp = (hits + walks) / plate_appearances if plate_appearances > 0 else 0.300

            # SLG calculation
            total_bases = (
                    events.get('single', 0) +
                    2 * events.get('double', 0) +
                    3 * events.get('triple', 0) +
                    4 * events.get('home_run', 0)
            )
            slg = total_bases / at_bats if at_bats > 0 else 0.400

            # Form score calculation
            form_score = self._calculate_form_score(
                batting_avg, obp + slg, games, player.base_projection
            )

            # Trend detection
            trend = self._detect_trend(game_data)

            # Hot streak detection
            hot_streak = batting_avg > 0.350 or events.get('home_run', 0) >= 2

            return {
                'form_score': form_score,
                'trend': trend,
                'hot_streak': hot_streak,
                'games_analyzed': games,
                'recent_avg': batting_avg,
                'recent_obp': obp,
                'recent_slg': slg,
                'recent_ops': obp + slg,
                'hits': int(hits),
                'homers': int(events.get('home_run', 0)),
                'rbis': int(events.get('rbi', 0)) if 'rbi' in events else 0,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return self._get_default_form_data()

    def _calculate_form_score(self, avg: float, ops: float, games: int,
                              base_projection: float) -> float:
        """Calculate form score multiplier"""
        if games < 3 or base_projection <= 0:
            return 1.0

        # Base multiplier on performance vs average
        if avg >= 0.300:
            base_mult = 1.10 + (avg - 0.300) * 0.5
        elif avg <= 0.200:
            base_mult = 0.90 - (0.200 - avg) * 0.5
        else:
            base_mult = 1.0

        # OPS adjustment
        if ops >= 0.900:
            ops_mult = 1.05
        elif ops <= 0.600:
            ops_mult = 0.95
        else:
            ops_mult = 1.0

        # Combine multipliers
        form_score = base_mult * ops_mult

        # Apply bounds
        return max(0.70, min(1.35, form_score))

    def _detect_trend(self, game_data: pd.DataFrame) -> str:
        """Detect performance trend"""
        if len(game_data) < 10:
            return 'stable'

        try:
            # Sort by date
            sorted_data = game_data.sort_values('game_date', ascending=False)

            # Split into halves
            mid_point = len(sorted_data) // 2
            recent_half = sorted_data.iloc[:mid_point]
            older_half = sorted_data.iloc[mid_point:]

            # Calculate batting averages
            def calc_avg(data):
                hits = len(data[data['events'].isin(['single', 'double', 'triple', 'home_run'])])
                abs = len(data[data['events'].notna()])
                return hits / abs if abs > 0 else 0

            recent_avg = calc_avg(recent_half)
            older_avg = calc_avg(older_half)

            # Determine trend
            if recent_avg > older_avg * 1.20:
                return 'hot'
            elif recent_avg < older_avg * 0.80:
                return 'cold'
            else:
                return 'stable'

        except Exception:
            return 'stable'

    def _apply_batch_results_to_players(self, players: List[Any],
                                        results: Dict[str, Any]) -> int:
        """Apply batch results back to player objects"""
        applied = 0

        for player in players:
            if player.id in results:
                form_data = results[player.id]

                # Apply to player
                player._recent_performance = form_data
                player.form_score = form_data['form_score']
                player.hot_streak = form_data.get('hot_streak', False)

                # Description
                if form_data['hot_streak']:
                    player.form_description = f"🔥 HOT: .{int(form_data['recent_avg'] * 1000)}"
                elif form_data['form_score'] < 0.9:
                    player.form_description = f"❄️ COLD: .{int(form_data['recent_avg'] * 1000)}"
                else:
                    player.form_description = f"AVG: .{int(form_data['recent_avg'] * 1000)}"

                applied += 1

        return applied

    def _has_cached_form_data(self, player: Any) -> bool:
        """Check if player has valid cached form data"""
        if not self.cache_manager:
            return False

        cache_key = f"form_{player.id}_{self.days_back}d"
        return self.cache_manager.exists(cache_key)

    def _get_cached_form_data(self, player: Any) -> Optional[Dict]:
        """Get cached form data"""
        if not self.cache_manager:
            return None

        cache_key = f"form_{player.id}_{self.days_back}d"
        return self.cache_manager.get(cache_key)

    def _get_default_form_data(self) -> Dict[str, Any]:
        """Get default form data when unavailable"""
        return {
            'form_score': 1.0,
            'trend': 'stable',
            'hot_streak': False,
            'games_analyzed': 0,
            'recent_avg': 0.250,
            'recent_obp': 0.320,
            'recent_slg': 0.400,
            'recent_ops': 0.720,
            'hits': 0,
            'homers': 0,
            'rbis': 0,
            'last_updated': datetime.now().isoformat()
        }

    # Keep original method for backward compatibility
    def analyze_player_form(self, player: Any) -> Optional[Dict[str, Any]]:
        """Analyze single player form (backward compatibility)"""
        results = self.analyze_players_batch([player], use_cache=True)
        return results.get(player.id)