#!/usr/bin/env python3
"""
RECENT FORM ANALYZER
====================
Analyzes player recent performance and hot/cold streaks
Integrates seamlessly with existing DFS optimizer system
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import numpy as np

# Try to import pybaseball for game logs
try:
    import pybaseball

    PYBASEBALL_AVAILABLE = True
except ImportError:
    PYBASEBALL_AVAILABLE = False

logger = logging.getLogger(__name__)


class RecentFormAnalyzer:
    """
    Analyzes recent player performance for hot/cold streak detection
    Integrates with existing cache system and player model
    """

    def __init__(self, cache_manager=None, days_window: int = 14):
        """
        Initialize Recent Form Analyzer

        Args:
            cache_manager: Existing cache manager from utils.cache_manager
            days_window: Number of days to analyze (default 14)
        """
        self.cache_manager = cache_manager
        self.days_window = days_window
        self.cache_duration = 12  # hours

        # Performance thresholds based on statistical analysis
        self.hot_threshold = 1.25  # 25% above average
        self.cold_threshold = 0.75  # 25% below average

        # Weighted decay for recent games (more recent = higher weight)
        self.recency_weights = self._calculate_recency_weights()

    def _calculate_recency_weights(self) -> List[float]:
        """Calculate exponential decay weights for recent games"""
        weights = []
        for i in range(self.days_window):
            # Exponential decay: recent games weighted more
            weight = np.exp(-0.1 * i)
            weights.append(weight)

        # Normalize weights to sum to 1
        total = sum(weights)
        return [w / total for w in weights]

    def analyze_player_form(self, player) -> Dict[str, Any]:
        """
        Analyze recent form for a player

        Args:
            player: Player object (AdvancedPlayer instance)

        Returns:
            Dict with form analysis
        """
        # Check cache first if available
        cache_key = f"{player.name}_{player.team}_form"

        if self.cache_manager:
            cached_data = self.cache_manager.get('recent_form', cache_key)
            if cached_data and not cached_data.get('_cache_expired', True):
                player._recent_performance = cached_data
                return cached_data

        # Fetch recent game data
        recent_stats = self._fetch_recent_stats(player)

        if not recent_stats:
            # Return neutral form if no data
            default_form = {
                'form_score': 1.0,
                'trend': 'stable',
                'streak_type': None,
                'streak_length': 0,
                'consistency_score': 0.5,
                'games_analyzed': 0,
                'last_updated': datetime.now().isoformat()
            }
            player._recent_performance = default_form
            return default_form

        # Calculate form metrics
        form_analysis = self._calculate_form_metrics(recent_stats, player.primary_position)

        # Cache the results
        if self.cache_manager:
            self.cache_manager.set('recent_form', cache_key, form_analysis)

        # Apply to player object (seamless integration)
        player._recent_performance = form_analysis

        return form_analysis

    def _fetch_recent_stats(self, player) -> List[Dict]:
        """
        Fetch recent game stats for player

        Returns:
            List of game stats dictionaries
        """
        if not PYBASEBALL_AVAILABLE:
            # Generate realistic mock data if pybaseball not available
            return self._generate_mock_recent_stats(player)

        try:
            # Get player ID if needed
            if not hasattr(player, 'mlb_id'):
                player_id = self._get_player_id(player.name)
                if not player_id:
                    return []
            else:
                player_id = player.mlb_id

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.days_window)

            # Fetch game logs
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
            logger.debug(f"Error fetching recent stats for {player.name}: {e}")

        return []

    def _generate_mock_recent_stats(self, player) -> List[Dict]:
        """Generate realistic mock data for testing"""
        games = []
        base_performance = player.enhanced_score / 3  # Approximate per-game

        for i in range(min(10, self.days_window)):
            # Add some variance
            variance = np.random.normal(0, 0.3)
            game_score = max(0, base_performance * (1 + variance))

            game = {
                'game_date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                'fantasy_points': game_score,
                'hits': int(np.random.poisson(1.2)) if player.primary_position != 'P' else 0,
                'home_runs': 1 if np.random.random() < 0.1 else 0,
                'rbi': int(np.random.poisson(0.8)) if player.primary_position != 'P' else 0,
                'strikeouts': int(np.random.poisson(7)) if player.primary_position == 'P' else 0,
                'earned_runs': int(np.random.poisson(2)) if player.primary_position == 'P' else 0,
            }
            games.append(game)

        return games

    def _calculate_form_metrics(self, recent_stats: List[Dict], position: str) -> Dict:
        """
        Calculate comprehensive form metrics

        Returns:
            Dict with form analysis
        """
        if not recent_stats:
            return {}

        # Extract fantasy points or calculate from stats
        game_scores = []
        for game in recent_stats:
            if 'fantasy_points' in game:
                score = game['fantasy_points']
            else:
                # Calculate fantasy points from raw stats
                score = self._calculate_fantasy_points(game, position)
            game_scores.append(score)

        # Apply recency weights
        weighted_scores = []
        for i, score in enumerate(game_scores):
            if i < len(self.recency_weights):
                weighted_scores.append(score * self.recency_weights[i])

        # Calculate metrics
        avg_score = np.mean(game_scores) if game_scores else 0
        weighted_avg = sum(weighted_scores) if weighted_scores else 0

        # Form score: weighted average vs overall average
        form_score = weighted_avg / avg_score if avg_score > 0 else 1.0

        # Trend analysis (last 3 vs previous 3)
        if len(game_scores) >= 6:
            recent_3 = np.mean(game_scores[:3])
            previous_3 = np.mean(game_scores[3:6])
            trend_ratio = recent_3 / previous_3 if previous_3 > 0 else 1.0

            if trend_ratio > 1.15:
                trend = 'hot'
            elif trend_ratio < 0.85:
                trend = 'cold'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
            trend_ratio = 1.0

        # Streak detection
        streak_type, streak_length = self._detect_streak(game_scores, avg_score)

        # Consistency score (lower std dev = more consistent)
        if len(game_scores) > 1:
            std_dev = np.std(game_scores)
            consistency_score = 1 / (1 + std_dev / avg_score) if avg_score > 0 else 0.5
        else:
            consistency_score = 0.5

        return {
            'form_score': round(form_score, 3),
            'trend': trend,
            'trend_ratio': round(trend_ratio, 3),
            'streak_type': streak_type,
            'streak_length': streak_length,
            'consistency_score': round(consistency_score, 3),
            'avg_recent_score': round(avg_score, 2),
            'weighted_recent_score': round(weighted_avg, 2),
            'games_analyzed': len(game_scores),
            'last_updated': datetime.now().isoformat()
        }

    def _detect_streak(self, scores: List[float], avg: float) -> Tuple[Optional[str], int]:
        """Detect hot/cold streaks"""
        if not scores or avg == 0:
            return None, 0

        streak_type = None
        streak_length = 0

        for score in scores:
            if score > avg * self.hot_threshold:
                if streak_type == 'hot':
                    streak_length += 1
                else:
                    streak_type = 'hot'
                    streak_length = 1
            elif score < avg * self.cold_threshold:
                if streak_type == 'cold':
                    streak_length += 1
                else:
                    streak_type = 'cold'
                    streak_length = 1
            else:
                break  # Streak ended

        # Only count as streak if 3+ games
        if streak_length < 3:
            return None, 0

        return streak_type, streak_length

    def _calculate_fantasy_points(self, game_stats: Dict, position: str) -> float:
        """Calculate DraftKings fantasy points from game stats"""
        points = 0.0

        if position == 'P':
            # Pitcher scoring
            points += game_stats.get('strikeouts', 0) * 2
            points += game_stats.get('wins', 0) * 4
            points += game_stats.get('earned_runs', 0) * -2
            points += game_stats.get('hits_allowed', 0) * -0.6
            points += game_stats.get('walks_allowed', 0) * -0.6
            points += game_stats.get('hit_batters', 0) * -0.6
            points += game_stats.get('complete_game', 0) * 2.5
            points += game_stats.get('shutout', 0) * 2.5
            points += game_stats.get('no_hitter', 0) * 5
        else:
            # Hitter scoring
            points += game_stats.get('singles', 0) * 3
            points += game_stats.get('doubles', 0) * 5
            points += game_stats.get('triples', 0) * 8
            points += game_stats.get('home_runs', 0) * 10
            points += game_stats.get('rbi', 0) * 2
            points += game_stats.get('runs', 0) * 2
            points += game_stats.get('walks', 0) * 2
            points += game_stats.get('hbp', 0) * 2
            points += game_stats.get('stolen_bases', 0) * 5
            points += game_stats.get('caught_stealing', 0) * -2

        return points

    def _get_player_id(self, player_name: str) -> Optional[int]:
        """Get MLB player ID from name"""
        try:
            # Use existing player ID cache if available
            name_parts = player_name.strip().split()
            if len(name_parts) >= 2:
                first = name_parts[0]
                last = name_parts[-1]

                lookup = pybaseball.playerid_lookup(last, first)
                if len(lookup) > 0:
                    return int(lookup.iloc[0]['key_mlbam'])
        except:
            pass

        return None

    def apply_form_adjustments(self, player) -> float:
        """
        Apply form-based adjustments to player score

        Args:
            player: Player object with recent_performance data

        Returns:
            Adjustment multiplier (1.0 = no change)
        """
        if not hasattr(player, '_recent_performance') or not player._recent_performance:
            return 1.0

        form_data = player._recent_performance
        form_score = form_data.get('form_score', 1.0)
        consistency = form_data.get('consistency_score', 0.5)
        streak_type = form_data.get('streak_type')
        streak_length = form_data.get('streak_length', 0)

        # Base adjustment from form score
        base_adjustment = form_score

        # Streak bonus/penalty
        if streak_type == 'hot' and streak_length >= 3:
            streak_bonus = 1 + (0.02 * min(streak_length, 7))  # Cap at 7 games
            base_adjustment *= streak_bonus
        elif streak_type == 'cold' and streak_length >= 3:
            streak_penalty = 1 - (0.02 * min(streak_length, 7))
            base_adjustment *= streak_penalty

        # Consistency bonus for cash games
        # High consistency (>0.7) gets up to 5% bonus
        consistency_bonus = 1 + (consistency - 0.5) * 0.1

        # Combine adjustments
        final_adjustment = base_adjustment * consistency_bonus

        # Cap total adjustment at +/- 20%
        return np.clip(final_adjustment, 0.80, 1.20)

    def enrich_players_with_form(self, players: List) -> int:
        """
        Enrich multiple players with recent form data

        Args:
            players: List of player objects

        Returns:
            Number of players enriched
        """
        enriched = 0

        print(f"📈 Analyzing recent form for {len(players)} players...")

        for i, player in enumerate(players):
            try:
                # Only analyze eligible players to save API calls
                if hasattr(player, 'is_eligible_for_selection'):
                    if not player.is_eligible_for_selection('bulletproof'):
                        continue

                # Analyze form
                form_data = self.analyze_player_form(player)

                if form_data and form_data.get('games_analyzed', 0) > 0:
                    enriched += 1

                    # Apply adjustment to enhanced score
                    adjustment = self.apply_form_adjustments(player)
                    if adjustment != 1.0:
                        old_score = player.enhanced_score
                        player.enhanced_score *= adjustment

                        # Show significant changes
                        if abs(adjustment - 1.0) > 0.1:
                            streak_info = ""
                            if form_data.get('streak_type'):
                                streak_info = f" ({form_data['streak_type']} streak: {form_data['streak_length']} games)"

                            print(f"   {player.name}: {old_score:.1f} → {player.enhanced_score:.1f} "
                                  f"(form: {form_data['form_score']:.2f}{streak_info})")

                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"   Processed {i + 1}/{len(players)} players...")

            except Exception as e:
                logger.debug(f"Error analyzing form for {player.name}: {e}")
                continue

        print(f"✅ Recent form analysis complete: {enriched} players enriched")

        return enriched


def integrate_recent_form_analyzer(core_instance):
    """
    Integrate RecentFormAnalyzer into existing BulletproofDFSCore

    Args:
        core_instance: Instance of BulletproofDFSCore
    """
    # Import cache manager
    try:
        from utils.cache_manager import cache
        cache_manager = cache
    except ImportError:
        cache_manager = None

    # Create analyzer instance
    analyzer = RecentFormAnalyzer(cache_manager=cache_manager)

    # Add to core instance
    core_instance.form_analyzer = analyzer

    # Add method to core
    def enrich_with_recent_form(self):
        """Enrich players with recent form analysis"""
        if hasattr(self, 'form_analyzer'):
            eligible = [p for p in self.players if p.is_eligible_for_selection(self.optimization_mode)]
            return self.form_analyzer.enrich_players_with_form(eligible)
        return 0

    # Bind method to instance
    import types
    core_instance.enrich_with_recent_form = types.MethodType(enrich_with_recent_form, core_instance)

    print("✅ Recent Form Analyzer integrated successfully")


# Export main components
__all__ = ['RecentFormAnalyzer', 'integrate_recent_form_analyzer']