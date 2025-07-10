#!/usr/bin/env python3
"""
RECENT FORM ANALYZER - UPDATED FOR NO FALLBACKS
Only returns real data - no fake/mock data generation
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# Check for pybaseball availability
try:
    import pybaseball

    PYBASEBALL_AVAILABLE = True
except ImportError:
    PYBASEBALL_AVAILABLE = False
    print("⚠️ pybaseball not available - recent form will be limited")

logger = logging.getLogger(__name__)


class RecentFormAnalyzer:
    """
    Analyzes recent player performance using REAL data only
    NO fallback/mock data - returns None if data unavailable
    """

    def __init__(self, cache_manager=None, days_back: int = 7):
        self.cache_manager = cache_manager
        self.days_back = days_back
        self.days_window = days_back + 3  # Buffer for data availability

        # Recency weights for weighted average
        self.recency_weights = [0.35, 0.25, 0.20, 0.12, 0.08]

    def analyze_player_form(self, player) -> Optional[Dict]:
        """
        Analyze player's recent form using REAL data only

        Returns:
            Dict with form analysis or None if no data available
        """
        # Check cache first
        cache_key = f"form_{player.name}_{player.team}_{self.days_back}"
        if self.cache_manager:
            cached_data = self.cache_manager.get('recent_form', cache_key)
            if cached_data and not cached_data.get('_cache_expired', True):
                return cached_data

        # Fetch real recent stats
        recent_stats = self._fetch_recent_stats(player)

        if not recent_stats:
            # NO FALLBACK - return None if no real data
            logger.debug(f"No recent stats available for {player.name}")
            return None

        # Calculate form metrics from real data
        form_analysis = self._calculate_form_metrics(recent_stats, player.primary_position)

        # Cache the results
        if self.cache_manager and form_analysis:
            self.cache_manager.set('recent_form', cache_key, form_analysis)

        return form_analysis

    def _fetch_recent_stats(self, player) -> Optional[List[Dict]]:
        """
        Fetch recent game stats for player - REAL DATA ONLY

        Returns:
            List of game stats or None if unavailable
        """
        if not PYBASEBALL_AVAILABLE:
            # No pybaseball = no data (NO FALLBACK)
            return None

        try:
            # Get player ID
            player_id = self._get_player_id(player.name)
            if not player_id:
                return None

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.days_window)

            # Fetch real game logs
            if player.primary_position == 'P':
                game_logs = pybaseball.statcast_pitcher_game_logs(
                    player_id,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
            else:
                game_logs = pybaseball.statcast_batter_game_logs(
                    player_id,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )

            # Convert to list of dicts
            if game_logs is not None and len(game_logs) > 0:
                return game_logs.to_dict('records')

        except Exception as e:
            logger.debug(f"Error fetching stats for {player.name}: {e}")

        return None

    def _get_player_id(self, player_name: str) -> Optional[int]:
        """Get player ID from pybaseball"""
        try:
            parts = player_name.split()
            if len(parts) >= 2:
                first = parts[0]
                last = ' '.join(parts[1:])

                # Look up player
                player_data = pybaseball.playerid_lookup(last, first)
                if not player_data.empty:
                    # Get most recent player (active)
                    return int(player_data.iloc[0]['key_mlbam'])
        except Exception as e:
            logger.debug(f"Could not find player ID for {player_name}: {e}")

        return None

    def _calculate_form_metrics(self, recent_stats: List[Dict], position: str) -> Dict:
        """
        Calculate form metrics from REAL game data

        Returns:
            Dict with form analysis
        """
        if not recent_stats:
            return None

        # Extract fantasy points
        game_scores = []
        for game in recent_stats:
            if 'fantasy_points_dk' in game:
                score = game['fantasy_points_dk']
            elif 'fantasy_points' in game:
                score = game['fantasy_points']
            else:
                # Calculate from stats if needed
                score = self._calculate_dk_points(game, position)

            if score is not None and score >= 0:
                game_scores.append(score)

        if not game_scores:
            return None

        # Calculate weighted recent average
        weighted_scores = []
        weights_used = []

        for i, score in enumerate(game_scores[:5]):  # Last 5 games
            if i < len(self.recency_weights):
                weighted_scores.append(score * self.recency_weights[i])
                weights_used.append(self.recency_weights[i])

        if not weights_used:
            return None

        recent_avg = sum(weighted_scores) / sum(weights_used)

        # Calculate trend
        if len(game_scores) >= 3:
            recent_3 = sum(game_scores[:3]) / 3
            older_3 = sum(game_scores[3:6]) / min(3, len(game_scores[3:6])) if len(game_scores) > 3 else recent_3

            if recent_3 > older_3 * 1.15:
                trend = 'hot'
            elif recent_3 < older_3 * 0.85:
                trend = 'cold'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'

        # Calculate streaks
        streak_type, streak_length = self._calculate_streaks(game_scores)

        # Calculate consistency
        if len(game_scores) >= 3:
            import numpy as np
            consistency = 1.0 - (np.std(game_scores) / (np.mean(game_scores) + 1))
            consistency = max(0, min(1, consistency))
        else:
            consistency = 0.5

        # Calculate form score (multiplier)
        if hasattr(player, 'base_projection') and player.base_projection > 0:
            form_score = recent_avg / player.base_projection
            form_score = max(0.7, min(1.3, form_score))  # Cap between 0.7-1.3
        else:
            form_score = 1.0

        return {
            'form_score': form_score,
            'trend': trend,
            'streak_type': streak_type,
            'streak_length': streak_length,
            'consistency_score': consistency,
            'recent_avg': recent_avg,
            'games_analyzed': len(game_scores),
            'last_updated': datetime.now().isoformat()
        }

    def _calculate_dk_points(self, game_stats: Dict, position: str) -> Optional[float]:
        """
        Calculate DraftKings points from raw stats
        Only if we have the necessary stats
        """
        try:
            if position == 'P':
                # Pitcher scoring
                points = 0

                # Required stats for calculation
                if 'innings_pitched' not in game_stats:
                    return None

                ip = game_stats.get('innings_pitched', 0)
                points += ip * 2.25  # IP
                points += game_stats.get('strikeouts', 0) * 2  # K
                points += game_stats.get('wins', 0) * 4  # W
                points -= game_stats.get('earned_runs', 0) * 2  # ER
                points -= game_stats.get('hits_allowed', 0) * 0.6  # H
                points -= game_stats.get('walks', 0) * 0.6  # BB
                points -= game_stats.get('hit_batters', 0) * 0.6  # HBP

                # Bonuses
                if ip >= 6 and game_stats.get('earned_runs', 99) == 0:
                    points += 2.5  # CG SO
                elif game_stats.get('earned_runs', 99) == 0:
                    points += 2  # No hitter

                return points
            else:
                # Hitter scoring
                points = 0

                # Singles
                hits = game_stats.get('hits', 0)
                doubles = game_stats.get('doubles', 0)
                triples = game_stats.get('triples', 0)
                homers = game_stats.get('home_runs', 0)
                singles = hits - doubles - triples - homers

                points += singles * 3
                points += doubles * 5
                points += triples * 8
                points += homers * 10
                points += game_stats.get('rbi', 0) * 2
                points += game_stats.get('runs', 0) * 2
                points += game_stats.get('walks', 0) * 2
                points += game_stats.get('stolen_bases', 0) * 5

                return points

        except Exception as e:
            logger.debug(f"Error calculating DK points: {e}")

        return None

    def _calculate_streaks(self, scores: List[float]) -> Tuple[Optional[str], int]:
        """Calculate current streak type and length"""
        if len(scores) < 2:
            return None, 0

        # Define thresholds
        hot_threshold = 15.0  # DK points
        cold_threshold = 5.0

        streak_type = None
        streak_length = 0

        for score in scores:
            if score >= hot_threshold:
                if streak_type == 'hot':
                    streak_length += 1
                else:
                    streak_type = 'hot'
                    streak_length = 1
            elif score <= cold_threshold:
                if streak_type == 'cold':
                    streak_length += 1
                else:
                    streak_type = 'cold'
                    streak_length = 1
            else:
                # Streak broken
                break

        return streak_type, streak_length


# Integration function for bulletproof_dfs_core
def enrich_players_with_recent_form(players: List,
                                    form_analyzer: RecentFormAnalyzer,
                                    max_players: Optional[int] = None) -> int:
    """
    Enrich players with recent form data

    Args:
        players: List of players to analyze
        form_analyzer: RecentFormAnalyzer instance
        max_players: Maximum players to analyze (None = all)

    Returns:
        Number of players successfully enriched
    """
    enriched_count = 0

    # Determine how many to process
    if max_players and max_players > 0:
        players_to_analyze = players[:max_players]
    else:
        players_to_analyze = players

    logger.info(f"Analyzing recent form for {len(players_to_analyze)} players")

    for i, player in enumerate(players_to_analyze):
        if (i + 1) % 10 == 0:
            logger.info(f"Progress: {i + 1}/{len(players_to_analyze)}")

        try:
            form_data = form_analyzer.analyze_player_form(player)

            if form_data:
                # Apply to player
                player.apply_recent_form(form_data)
                enriched_count += 1

        except Exception as e:
            logger.debug(f"Error analyzing form for {player.name}: {e}")

    logger.info(f"Successfully enriched {enriched_count}/{len(players_to_analyze)} players with recent form")

    return enriched_count


# Example usage
if __name__ == "__main__":
    # Test with a player
    from unified_player_model import UnifiedPlayer

    player = UnifiedPlayer(
        id="1",
        name="Shohei Ohtani",
        team="LAD",
        salary=6000,
        primary_position="DH",
        positions=["DH"],
        base_projection=12.0
    )

    analyzer = RecentFormAnalyzer(days_back=7)
    form_data = analyzer.analyze_player_form(player)

    if form_data:
        print(f"Form analysis for {player.name}:")
        print(f"  Form score: {form_data['form_score']:.2f}x")
        print(f"  Trend: {form_data['trend']}")
        print(f"  Games analyzed: {form_data['games_analyzed']}")
    else:
        print(f"No recent form data available for {player.name}")