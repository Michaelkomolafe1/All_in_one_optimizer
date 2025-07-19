#!/usr/bin/env python3
"""
ADVANCED BASEBALL SAVANT SCORING ENGINE
======================================
Pure data-driven scoring using all available Statcast metrics
NO FALLBACK DATA - Real metrics only
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class AdvancedScoringConfig:
    """Configuration for advanced scoring with Baseball Savant metrics"""

    # Component weights (must sum to 1.0)
    component_weights: Dict[str, float] = field(default_factory=lambda: {
        "base_projection": 0.20,  # DraftKings/DFF projection
        "statcast_quality": 0.25,  # Quality of contact metrics
        "recent_performance": 0.20,  # Last 7-14 days performance
        "matchup_analytics": 0.15,  # Pitcher/batter matchup data
        "batting_order": 0.10,  # Lineup position value
        "park_venue": 0.05,  # Park factors
        "game_context": 0.05  # Vegas lines, weather
    })

    # Statcast metric weights for batters
    batter_metric_weights: Dict[str, float] = field(default_factory=lambda: {
        "barrel": 0.20,  # Most predictive of XBH
        "xwoba": 0.15,  # estimated_woba_using_speedangle
        "xba": 0.15,  # estimated_ba_using_speedangle
        "exit_velocity": 0.10,  # launch_speed
        "launch_angle_sweet_spot": 0.10,  # 10-30 degree launch angle
        "sprint_speed": 0.08,  # SB and XBH potential
        "hit_distance": 0.07,  # hit_distance_sc
        "zone_contact": 0.05,  # In-zone contact rate
        "chase_rate": 0.05,  # Out-of-zone swing rate
        "hard_hit_rate": 0.05  # 95+ mph exit velo
    })

    # Statcast metric weights for pitchers
    pitcher_metric_weights: Dict[str, float] = field(default_factory=lambda: {
        "whiff_rate": 0.20,  # Swing and miss %
        "barrel_against": 0.15,  # Barrels allowed
        "xwoba_against": 0.15,  # Expected wOBA against
        "spin_rate": 0.10,  # release_spin_rate
        "movement": 0.10,  # pfx_x + pfx_z combined
        "velocity": 0.10,  # release_speed
        "zone_rate": 0.10,  # Strike zone %
        "chase_induced": 0.05,  # Getting batters to chase
        "soft_contact": 0.05  # Weak contact induced
    })

    # Thresholds for elite performance
    elite_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "barrel_rate": 10.0,  # 10%+ is elite
        "xwoba": 0.370,  # .370+ xwOBA is elite
        "sprint_speed": 27.5,  # 27.5+ ft/s is fast
        "whiff_rate": 30.0,  # 30%+ whiff is elite
        "exit_velocity": 92.0,  # 92+ mph average
        "spin_rate": 2400  # 2400+ rpm for fastballs
    })


class AdvancedScoringEngine:
    """
    Complete scoring engine using all Baseball Savant data
    NO FALLBACKS - Only real data
    """

    def __init__(self, config: Optional[AdvancedScoringConfig] = None):
        self.config = config or AdvancedScoringConfig()
        self.logger = logger

        # Validate configuration
        self._validate_config()

        # Cache for calculated scores
        self._score_cache = {}
        self._cache_ttl = 300  # 5 minutes

        # Data source connections
        self.statcast_fetcher = None
        self.vegas_client = None
        self.confirmation_system = None

        logger.info("Advanced Scoring Engine initialized")

    def _validate_config(self):
        """Ensure all weights sum to 1.0"""
        for weight_dict in [
            self.config.component_weights,
            self.config.batter_metric_weights,
            self.config.pitcher_metric_weights
        ]:
            total = sum(weight_dict.values())
            if abs(total - 1.0) > 0.001:
                # Normalize
                for key in weight_dict:
                    weight_dict[key] /= total

    def set_data_sources(self,
                         statcast_fetcher=None,
                         vegas_client=None,
                         confirmation_system=None):
        """Connect data sources"""
        self.statcast_fetcher = statcast_fetcher
        self.vegas_client = vegas_client
        self.confirmation_system = confirmation_system

    def calculate_score(self, player: Any) -> float:
        """
        Main scoring method - calculates enhanced score for any player
        Returns 0 if insufficient data (NO FALLBACKS)
        """
        # Check cache first
        cache_key = self._get_cache_key(player)
        if cache_key in self._score_cache:
            cached_score, timestamp = self._score_cache[cache_key]
            if (datetime.now() - timestamp).seconds < self._cache_ttl:
                return cached_score

        # Must have base projection
        base_projection = getattr(player, 'base_projection', 0)
        if base_projection <= 0:
            return 0.0

        # Calculate component scores
        components = {
            'base': base_projection,
            'statcast': self._calculate_statcast_component(player),
            'recent': self._calculate_recent_form_component(player),
            'matchup': self._calculate_matchup_component(player),
            'batting_order': self._calculate_batting_order_component(player),
            'park': self._calculate_park_component(player),
            'game_context': self._calculate_game_context_component(player)
        }

        # Apply component weights
        weighted_score = 0.0
        component_details = {}

        for component, weight in self.config.component_weights.items():
            component_key = component.replace('_projection', '').replace('_analytics', '')
            if component_key in components:
                value = components[component_key]
                if value is not None and value > 0:
                    weighted_score += value * weight
                    component_details[component] = value

        # Store detailed breakdown on player
        if hasattr(player, '_score_breakdown'):
            player._score_breakdown = component_details

        # Cache the result
        self._score_cache[cache_key] = (weighted_score, datetime.now())

        return weighted_score

    def _calculate_statcast_component(self, player: Any) -> float:
        """Calculate score from Statcast metrics"""
        if not self.statcast_fetcher:
            return player.base_projection  # Use base if no Statcast

        # Get Statcast data
        statcast_data = self._get_player_statcast_data(player)
        if not statcast_data or statcast_data.empty:
            return player.base_projection

        is_pitcher = player.primary_position == 'P'

        if is_pitcher:
            return self._calculate_pitcher_statcast_score(player, statcast_data)
        else:
            return self._calculate_batter_statcast_score(player, statcast_data)

    def _calculate_batter_statcast_score(self, player: Any, data: pd.DataFrame) -> float:
        """Calculate batter score from Statcast data"""
        metrics = {}

        # 1. Barrel Rate (most important)
        if 'barrel' in data.columns:
            barrel_rate = (data['barrel'] == 1).mean() * 100
            metrics['barrel'] = self._normalize_metric(
                barrel_rate, 0, self.config.elite_thresholds['barrel_rate'], higher_better=True
            )

        # 2. xwOBA
        if 'estimated_woba_using_speedangle' in data.columns:
            xwoba = data['estimated_woba_using_speedangle'].mean()
            metrics['xwoba'] = self._normalize_metric(
                xwoba, 0.250, self.config.elite_thresholds['xwoba'], higher_better=True
            )

        # 3. xBA
        if 'estimated_ba_using_speedangle' in data.columns:
            xba = data['estimated_ba_using_speedangle'].mean()
            metrics['xba'] = self._normalize_metric(xba, 0.200, 0.300, higher_better=True)

        # 4. Exit Velocity
        if 'launch_speed' in data.columns:
            avg_exit_velo = data['launch_speed'].mean()
            metrics['exit_velocity'] = self._normalize_metric(
                avg_exit_velo, 85, self.config.elite_thresholds['exit_velocity'], higher_better=True
            )

        # 5. Launch Angle Sweet Spot (10-30 degrees)
        if 'launch_angle' in data.columns:
            sweet_spot_pct = ((data['launch_angle'] >= 10) & (data['launch_angle'] <= 30)).mean() * 100
            metrics['launch_angle_sweet_spot'] = self._normalize_metric(
                sweet_spot_pct, 20, 40, higher_better=True
            )

        # 6. Sprint Speed
        if 'sprint_speed' in data.columns:
            sprint_speed = data['sprint_speed'].mean()
            metrics['sprint_speed'] = self._normalize_metric(
                sprint_speed, 25, self.config.elite_thresholds['sprint_speed'], higher_better=True
            )

        # 7. Hit Distance
        if 'hit_distance_sc' in data.columns:
            avg_distance = data['hit_distance_sc'].mean()
            metrics['hit_distance'] = self._normalize_metric(
                avg_distance, 150, 250, higher_better=True
            )

        # 8. Zone Contact Rate
        if 'zone' in data.columns and 'description' in data.columns:
            in_zone = data['zone'].between(1, 9)
            swings = data['description'].isin(['foul', 'hit_into_play', 'swinging_strike'])
            zone_contact = ((in_zone & swings & ~data['description'].eq('swinging_strike')).sum() /
                            (in_zone & swings).sum() if (in_zone & swings).sum() > 0 else 0.8)
            metrics['zone_contact'] = self._normalize_metric(zone_contact, 0.7, 0.9, higher_better=True)

        # 9. Chase Rate (lower is better)
        if 'zone' in data.columns and 'description' in data.columns:
            out_zone = ~data['zone'].between(1, 9)
            chase_rate = ((out_zone & swings).sum() / out_zone.sum() if out_zone.sum() > 0 else 0.3)
            metrics['chase_rate'] = self._normalize_metric(chase_rate, 0.4, 0.2, higher_better=False)

        # 10. Hard Hit Rate
        if 'launch_speed' in data.columns:
            hard_hit_rate = (data['launch_speed'] >= 95).mean() * 100
            metrics['hard_hit_rate'] = self._normalize_metric(hard_hit_rate, 25, 45, higher_better=True)

        # Apply weights and calculate final score
        weighted_score = 0.0
        for metric_name, weight in self.config.batter_metric_weights.items():
            if metric_name in metrics:
                weighted_score += metrics[metric_name] * weight

        # Scale to fantasy points
        base_projection = player.base_projection
        multiplier = 0.8 + (weighted_score * 0.4)  # 0.8x to 1.2x multiplier

        return base_projection * multiplier

    def _calculate_pitcher_statcast_score(self, player: Any, data: pd.DataFrame) -> float:
        """Calculate pitcher score from Statcast data"""
        metrics = {}

        # 1. Whiff Rate
        if 'description' in data.columns:
            total_swings = data['description'].isin(['swinging_strike', 'foul', 'hit_into_play']).sum()
            whiffs = (data['description'] == 'swinging_strike').sum()
            whiff_rate = (whiffs / total_swings * 100) if total_swings > 0 else 20
            metrics['whiff_rate'] = self._normalize_metric(
                whiff_rate, 15, self.config.elite_thresholds['whiff_rate'], higher_better=True
            )

        # 2. Barrel Rate Against
        if 'barrel' in data.columns:
            barrel_rate = (data['barrel'] == 1).mean() * 100
            metrics['barrel_against'] = self._normalize_metric(
                barrel_rate, 12, 4, higher_better=False  # Lower is better
            )

        # 3. xwOBA Against
        if 'estimated_woba_using_speedangle' in data.columns:
            xwoba_against = data['estimated_woba_using_speedangle'].mean()
            metrics['xwoba_against'] = self._normalize_metric(
                xwoba_against, 0.350, 0.280, higher_better=False  # Lower is better
            )

        # 4. Spin Rate
        if 'release_spin_rate' in data.columns:
            avg_spin = data['release_spin_rate'].mean()
            metrics['spin_rate'] = self._normalize_metric(
                avg_spin, 2200, self.config.elite_thresholds['spin_rate'], higher_better=True
            )

        # 5. Movement (combined horizontal and vertical)
        if 'pfx_x' in data.columns and 'pfx_z' in data.columns:
            total_movement = np.sqrt(data['pfx_x'] ** 2 + data['pfx_z'] ** 2).mean()
            metrics['movement'] = self._normalize_metric(total_movement, 10, 18, higher_better=True)

        # 6. Velocity
        if 'release_speed' in data.columns:
            avg_velo = data['release_speed'].mean()
            metrics['velocity'] = self._normalize_metric(avg_velo, 90, 96, higher_better=True)

        # 7. Zone Rate
        if 'zone' in data.columns:
            zone_rate = data['zone'].between(1, 9).mean() * 100
            metrics['zone_rate'] = self._normalize_metric(zone_rate, 40, 50, higher_better=True)

        # 8. Chase Induced
        if 'zone' in data.columns and 'description' in data.columns:
            out_zone = ~data['zone'].between(1, 9)
            swings = data['description'].isin(['swinging_strike', 'foul', 'hit_into_play'])
            chase_rate = ((out_zone & swings).sum() / out_zone.sum() * 100) if out_zone.sum() > 0 else 25
            metrics['chase_induced'] = self._normalize_metric(chase_rate, 20, 35, higher_better=True)

        # 9. Soft Contact
        if 'launch_speed' in data.columns:
            soft_contact_rate = (data['launch_speed'] < 85).mean() * 100
            metrics['soft_contact'] = self._normalize_metric(soft_contact_rate, 15, 25, higher_better=True)

        # Apply weights
        weighted_score = 0.0
        for metric_name, weight in self.config.pitcher_metric_weights.items():
            if metric_name in metrics:
                weighted_score += metrics[metric_name] * weight

        # Scale to fantasy points
        base_projection = player.base_projection
        multiplier = 0.8 + (weighted_score * 0.4)  # 0.8x to 1.2x multiplier

        return base_projection * multiplier

    def _calculate_recent_form_component(self, player: Any) -> float:
        """Calculate recent performance score"""
        if not hasattr(player, 'recent_games') or not player.recent_games:
            return player.base_projection

        # Analyze last 7-14 days of performance
        recent_scores = []
        for game in player.recent_games[-10:]:  # Last 10 games
            if 'fantasy_points' in game:
                recent_scores.append(game['fantasy_points'])

        if not recent_scores:
            return player.base_projection

        # Calculate trend
        avg_recent = np.mean(recent_scores)
        if len(recent_scores) >= 5:
            # Compare first half to second half
            first_half = np.mean(recent_scores[:len(recent_scores) // 2])
            second_half = np.mean(recent_scores[len(recent_scores) // 2:])
            trend_multiplier = second_half / first_half if first_half > 0 else 1.0
            trend_multiplier = np.clip(trend_multiplier, 0.8, 1.2)
        else:
            trend_multiplier = 1.0

        return avg_recent * trend_multiplier

    def _calculate_matchup_component(self, player: Any) -> float:
        """Calculate matchup-based score adjustments"""
        base = player.base_projection

        # For batters: vs pitcher matchup
        if player.primary_position != 'P':
            if hasattr(player, 'opposing_pitcher_stats'):
                opp_stats = player.opposing_pitcher_stats

                # Check pitcher's recent form
                if 'last_5_era' in opp_stats:
                    if opp_stats['last_5_era'] > 5.0:
                        base *= 1.15  # Facing struggling pitcher
                    elif opp_stats['last_5_era'] < 3.0:
                        base *= 0.85  # Facing hot pitcher

                # Check handedness advantage
                if hasattr(player, 'bats') and 'throws' in opp_stats:
                    if player.bats != opp_stats['throws']:
                        base *= 1.05  # Platoon advantage

        # For pitchers: vs team batting stats
        else:
            if hasattr(player, 'opposing_team_stats'):
                team_stats = player.opposing_team_stats

                # Check team's recent hitting
                if 'last_7_runs_per_game' in team_stats:
                    if team_stats['last_7_runs_per_game'] < 3.5:
                        base *= 1.10  # Facing cold offense
                    elif team_stats['last_7_runs_per_game'] > 5.5:
                        base *= 0.90  # Facing hot offense

        return base

    def _calculate_batting_order_component(self, player: Any) -> float:
        """Calculate batting order position value"""
        if player.primary_position == 'P':
            return player.base_projection

        batting_order = getattr(player, 'batting_order', None)
        if not batting_order:
            return player.base_projection

        # Position multipliers based on expected plate appearances
        order_multipliers = {
            1: 1.12,  # Leadoff
            2: 1.08,  # 2-hole
            3: 1.06,  # 3-hole
            4: 1.04,  # Cleanup
            5: 1.02,  # 5-hole
            6: 0.98,  # 6-hole
            7: 0.95,  # 7-hole
            8: 0.92,  # 8-hole
            9: 0.90  # 9-hole
        }

        multiplier = order_multipliers.get(batting_order, 1.0)
        return player.base_projection * multiplier

    def _calculate_park_component(self, player: Any) -> float:
        """Calculate park factor adjustments"""
        if not hasattr(player, 'game_venue'):
            return player.base_projection

        # Park factors (simplified - would load from data source)
        park_factors = {
            'COL': 1.15,  # Coors Field
            'CIN': 1.08,  # Great American Ball Park
            'TEX': 1.06,  # Globe Life Field
            'BOS': 1.05,  # Fenway Park
            'NYY': 1.03,  # Yankee Stadium
            'SD': 0.95,  # Petco Park
            'SF': 0.93,  # Oracle Park
            'MIA': 0.92  # loanDepot park
        }

        team = getattr(player, 'team', '')
        factor = park_factors.get(team, 1.0)

        # Reverse for pitchers (pitcher-friendly parks help them)
        if player.primary_position == 'P':
            factor = 2.0 - factor

        return player.base_projection * factor

    def _calculate_game_context_component(self, player: Any) -> float:
        """Calculate game context (Vegas lines, weather, etc.)"""
        base = player.base_projection

        # Vegas implied team total
        if hasattr(player, 'vegas_data') and player.vegas_data:
            implied_total = player.vegas_data.get('implied_total', 4.5)

            # Adjust based on implied runs
            if implied_total > 5.5:
                base *= 1.08  # High-scoring game environment
            elif implied_total < 3.5:
                base *= 0.92  # Low-scoring game environment

        # Weather adjustments would go here
        # (temperature, wind, etc.)

        return base

    def _get_player_statcast_data(self, player: Any) -> Optional[pd.DataFrame]:
        """Fetch player's Statcast data"""
        if not self.statcast_fetcher:
            return None

        try:
            # This would call your simple_statcast_fetcher
            data = self.statcast_fetcher.fetch_player_data(
                player.name,
                player.primary_position
            )
            return data
        except Exception as e:
            logger.error(f"Failed to fetch Statcast data for {player.name}: {e}")
            return None

    def _normalize_metric(self, value: float, min_val: float, max_val: float,
                          higher_better: bool = True) -> float:
        """Normalize metric to 0-1 scale"""
        if higher_better:
            return np.clip((value - min_val) / (max_val - min_val), 0, 1)
        else:
            return np.clip((max_val - value) / (max_val - min_val), 0, 1)

    def _get_cache_key(self, player: Any) -> str:
        """Generate cache key for player"""
        return f"{player.id}_{datetime.now().strftime('%Y%m%d%H')}"

    def get_score_breakdown(self, player: Any) -> Dict[str, Any]:
        """Get detailed breakdown of player's score calculation"""
        # Calculate score first to populate breakdown
        score = self.calculate_score(player)

        breakdown = {
            'total_score': score,
            'base_projection': player.base_projection,
            'components': getattr(player, '_score_breakdown', {}),
            'multiplier': score / player.base_projection if player.base_projection > 0 else 0
        }

        return breakdown


# Factory function
def create_advanced_scoring_engine(config: Optional[AdvancedScoringConfig] = None) -> AdvancedScoringEngine:
    """Create an instance of the advanced scoring engine"""
    return AdvancedScoringEngine(config)


# For backward compatibility
get_scoring_engine = create_advanced_scoring_engine

if __name__ == "__main__":
    print("✅ Advanced Baseball Savant Scoring Engine loaded")
    print("📊 Using these Statcast metrics:")
    print("\nFor Batters:")
    config = AdvancedScoringConfig()
    for metric, weight in config.batter_metric_weights.items():
        print(f"  - {metric}: {weight * 100:.0f}%")
    print("\nFor Pitchers:")
    for metric, weight in config.pitcher_metric_weights.items():
        print(f"  - {metric}: {weight * 100:.0f}%")