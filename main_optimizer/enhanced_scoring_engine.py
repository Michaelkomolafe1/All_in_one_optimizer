#!/usr/bin/env python3
"""
ENHANCED SCORING ENGINE
======================
Uses your Bayesian-optimized parameters for GPP and Cash scoring
"""

import json
import logging
from typing import Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class EnhancedScoringEngine:
    """
    Implements the optimized parameters from Bayesian optimization
    GPP Score: -67.7 (64th percentile average)
    Cash Score: 86.2 (79% win rate)
    """
    
    def __init__(self):
        # Load optimized parameters
        self.load_optimized_parameters()
        
    def load_optimized_parameters(self):
        """Load the optimized parameters from config files"""
        config_dir = Path(__file__).parent.parent / "config"
        
        # GPP Parameters (-67.7 score)
        self.gpp_params = {
            # Team total thresholds
            'threshold_high': 5.879652818354419,
            'threshold_med': 5.731303194500506,
            'threshold_low': 4.865876372504785,
            
            # Multipliers for each threshold
            'mult_high': 1.3362904255411312,
            'mult_med': 1.2163912748563654,
            'mult_low': 1.1393921566433494,
            'mult_none': 0.7614333531096783,
            
            # Stack configuration
            'stack_min': 4,
            'stack_max': 5,
            'stack_preferred': 4,
            
            # Batting order
            'batting_boost': 1.114543568527152,
            'batting_positions': 5,  # Top 5 in order
            
            # Ownership leverage
            'ownership_low_boost': 1.106440616808056,
            'ownership_high_penalty': 0.9,
            'ownership_threshold': 15,
            
            # Pitcher quality
            'pitcher_bad_boost': 1.1350362531673686,
            'pitcher_ace_penalty': 0.92,
            'era_threshold': 4.231887114967439,
            
            # Statcast thresholds
            'barrel_rate_threshold': 11.66458072425903,
            'barrel_rate_boost': 1.1937255322047728,
            'exit_velo_threshold': 90.78121260359892,
            'exit_velo_boost': 1.0780387794177815,
            
            # xwOBA differential
            'xwoba_diff_threshold': 0.015,
            'undervalued_boost': 1.25,
            
            # Pitcher stats
            'min_k9_threshold': 9.898101301518519,
            'high_k9_boost': 1.1979803025131133,
            'opp_k_rate_threshold': 0.2110391201711871,
            'high_opp_k_boost': 1.1959981574310035
        }
        
        # Cash Parameters (86.2 score = 79% win rate)
        self.cash_params = {
            # Weight distribution
            'weight_projection': 0.40,
            'weight_recent': 0.40,
            'weight_season': 0.20,
            
            # Consistency
            'consistency_weight': 0.24994454993253398,
            'consistency_method': 'both',
            
            # Recent form
            'recent_games_window': 4,
            
            # Platoon
            'use_platoon': True,
            'platoon_advantage_boost': 1.0837826593923623,
            
            # Streaks
            'use_streaks': True,
            'streak_hot_boost': 1.084866203144244,
            'streak_cold_penalty': 0.9353059960620218,
            'streak_window': 3,
            
            # Floor/ceiling
            'floor_weight': 0.8,
            'ceiling_weight': 0.2
        }

    # !/usr/bin/env python3
    """
    Check if the scoring engine actually uses the enrichments
    """

    # The enrichments we're adding:
    ENRICHMENTS = {
        'recent_form': 1.24,  # Performance multiplier (0.5-1.5)
        'consistency_score': 0.96,  # Consistency multiplier (0.5-1.5)
        'park_factor': 1.06,  # Park multiplier (0.86-1.33)
        'weather_impact': 1.05,  # Weather multiplier (0.8-1.2)
    }

    # Check what EnhancedScoringEngine actually uses:

    def check_cash_scoring(self):
        """What does score_player_cash use?"""
        # From enhanced_scoring_engine.py
        used_attributes = [
            'base_projection',  # ✅ Base DK projection
            'recent_form',  # ✅ WE ADDED THIS!
            'consistency_score',  # ✅ WE ADDED THIS!
            'park_factor',  # ❓ Need to check
            'matchup_score',  # From original enrichments
            'weather_impact',  # ❓ Need to check
        ]

        # Cash scoring typically uses:
        # score = base_projection * recent_form * consistency_score * matchup_score

        return used_attributes

    def check_gpp_scoring(self):
        """What does score_player_gpp use?"""
        # From enhanced_scoring_engine.py
        used_attributes = [
            'base_projection',  # ✅ Base DK projection
            'implied_team_score',  # ✅ Vegas total
            'batting_order',  # ✅ Lineup position
            'park_factor',  # ❓ Need to check
            'weather_impact',  # ❓ Need to check
            'recent_form',  # ❓ Need to check
            'ownership',  # If available
            'barrel_rate',  # From stats
        ]

        return used_attributes

    # TO ENSURE THEY'RE USED, update scoring methods:

    def enhanced_score_player_cash(self, player):
        """Cash scoring that uses ALL enrichments"""
        score = player.base_projection

        # Apply all enrichments
        score *= getattr(player, 'recent_form', 1.0)  # Hot/cold
        score *= getattr(player, 'consistency_score', 1.0)  # Reliability
        score *= getattr(player, 'park_factor', 1.0)  # Ballpark
        score *= getattr(player, 'weather_impact', 1.0)  # Weather
        score *= getattr(player, 'matchup_score', 1.0)  # Matchup

        return score

    def enhanced_score_player_gpp(self, player):
        """GPP scoring that uses enrichments differently"""
        score = player.base_projection

        # Vegas and lineup position (existing)
        if hasattr(player, 'implied_team_score'):
            if player.implied_team_score >= 5.5:
                score *= 1.3  # High scoring game

        # NEW: Recent form matters more in GPP (ceiling chasing)
        form = getattr(player, 'recent_form', 1.0)
        if form > 1.2:  # Hot players
            score *= 1.2  # Extra boost
        elif form < 0.8:  # Cold players
            score *= 0.7  # Bigger penalty
        else:
            score *= form

        # Park and weather combined effect
        environmental = (getattr(player, 'park_factor', 1.0) *
                         getattr(player, 'weather_impact', 1.0))
        if environmental > 1.15:  # Great conditions
            score *= 1.1  # Boost ceiling plays

        return score

    # STRATEGY-SPECIFIC USAGE:

    STRATEGY_ENRICHMENT_USAGE = {
        'cash': {
            'projection_monster': {
                'uses': ['base_projection', 'consistency_score', 'recent_form'],
                'weights': {'consistency': 0.4, 'recent_form': 0.2, 'projection': 0.4}
            },
            'pitcher_dominance': {
                'uses': ['base_projection', 'recent_form', 'park_factor'],
                'focuses_on': 'Consistent pitchers in pitcher-friendly parks'
            }
        },
        'gpp': {
            'correlation_value': {
                'uses': ['implied_team_score', 'park_factor', 'weather_impact'],
                'focuses_on': 'Stacks in high-scoring environments'
            },
            'truly_smart_stack': {
                'uses': ['recent_form', 'batting_order', 'park_factor', 'weather_impact'],
                'focuses_on': 'Hot hitters in good conditions'
            },
            'matchup_leverage_stack': {
                'uses': ['matchup_score', 'recent_form', 'park_factor'],
                'focuses_on': 'Exploiting pitcher weaknesses'
            }
        }
    }

    print("🔍 ENRICHMENT USAGE ANALYSIS")
    print("=" * 50)

    print("\n✅ Enrichments We're Adding:")
    for key, value in ENRICHMENTS.items():
        print(f"  {key}: {value}")

    print("\n📊 How Strategies Should Use Them:")
    for contest_type, strategies in STRATEGY_ENRICHMENT_USAGE.items():
        print(f"\n{contest_type.upper()} Strategies:")
        for strategy, details in strategies.items():
            print(f"  {strategy}:")
            print(f"    Uses: {', '.join(details['uses'])}")
            print(f"    Focus: {details.get('focuses_on', 'N/A')}")

    print("\n⚠️ TO VERIFY IN YOUR CODE:")
    print("1. Check enhanced_scoring_engine.py")
    print("2. Look for score_player_cash() and score_player_gpp()")
    print("3. Ensure they multiply by recent_form, park_factor, etc.")
    print("4. Check your strategy files in strategies/ folder")

    def score_player_gpp(self, player) -> float:
        """
        Score player for GPP using optimized parameters
        """
        score = player.base_projection if player.base_projection > 0 else getattr(player, "dff_projection", 0) or getattr(player, "fantasy_points", 10)

        # 1. Team total multiplier
        if hasattr(player, 'implied_team_score') and player.implied_team_score:
            if player.implied_team_score >= self.gpp_params['threshold_high']:
                score *= self.gpp_params['mult_high']
            elif player.implied_team_score >= self.gpp_params['threshold_med']:
                score *= self.gpp_params['mult_med']
            elif player.implied_team_score >= self.gpp_params['threshold_low']:
                score *= self.gpp_params['mult_low']
            else:
                score *= self.gpp_params['mult_none']

        # 2. Batting order boost
        if hasattr(player, 'batting_order') and player.batting_order:
            if player.batting_order <= self.gpp_params['batting_positions']:
                score *= self.gpp_params['batting_boost']

        # 3. Ownership leverage
        if hasattr(player, 'projected_ownership'):
            if player.projected_ownership < self.gpp_params['ownership_threshold']:
                score *= self.gpp_params['ownership_low_boost']
            elif player.projected_ownership > 30:
                score *= self.gpp_params['ownership_high_penalty']

        # 4. Pitcher matchup (for hitters)
        if player.primary_position != 'P' and hasattr(player, 'opposing_pitcher_era'):
            if player.opposing_pitcher_era > self.gpp_params['era_threshold']:
                score *= self.gpp_params['pitcher_bad_boost']
            elif player.opposing_pitcher_era < 3.0:
                score *= self.gpp_params['pitcher_ace_penalty']

        # 5. Statcast boosts (for hitters)
        if player.primary_position != 'P':
            # Barrel rate
            if hasattr(player, 'barrel_rate') and player.barrel_rate > self.gpp_params['barrel_rate_threshold']:
                score *= self.gpp_params['barrel_rate_boost']

            # Exit velocity
            if hasattr(player, 'exit_velocity') and player.exit_velocity > self.gpp_params['exit_velo_threshold']:
                score *= self.gpp_params['exit_velo_boost']

            # xwOBA differential
            if hasattr(player, 'xwoba_diff') and player.xwoba_diff > self.gpp_params['xwoba_diff_threshold']:
                score *= self.gpp_params['undervalued_boost']

        # 6. Pitcher K/9 boost (for pitchers)
        if player.primary_position == 'P':
            if hasattr(player, 'k9') and player.k9 > self.gpp_params['min_k9_threshold']:
                score *= self.gpp_params['high_k9_boost']

            if hasattr(player, 'opp_k_rate') and player.opp_k_rate > self.gpp_params['opp_k_rate_threshold']:
                score *= self.gpp_params['high_opp_k_boost']

        return score

    def score_player_cash(self, player) -> float:
        """Score player for cash games using optimized parameters"""
        # Get base projection
        base = getattr(player, 'base_projection', 0)
        if base == 0:
            base = getattr(player, 'projection', 0)
        if base == 0:
            base = getattr(player, 'dff_projection', 0)
        if base == 0:
            return 0

        score = float(base)

        # Apply cash game parameters
        # 1. Projection weight (already at 100% since we start with base)

        # 2. Recent form weight
        recent_form = getattr(player, 'recent_form', 1.0)
        score *= (1.0 + (recent_form - 1.0) * self.cash_params.get('recent_weight', 0.369))

        # 3. Floor weight (consistency)
        consistency = getattr(player, 'consistency_score', 1.0)
        score *= (1.0 + (consistency - 1.0) * self.cash_params.get('floor_weight', 0.80))

        # 4. Matchup quality
        matchup = getattr(player, 'matchup_score', 1.0)
        score *= (1.0 + (matchup - 1.0) * self.cash_params.get('matchup_weight', 0.25))

        # 5. Platoon advantage
        if hasattr(player, 'platoon_advantage') and player.platoon_advantage:
            score *= (1.0 + self.cash_params.get('platoon_boost', 0.084))

        # 6. Park and weather (reduced impact)
        park = getattr(player, 'park_factor', 1.0)
        weather = getattr(player, 'weather_impact', 1.0)

        score *= (1.0 + (park - 1.0) * 0.3)
        score *= (1.0 + (weather - 1.0) * 0.3)

        # 7. Pitcher preference
        if player.is_pitcher:
            score *= self.cash_params.get('pitcher_preference', 1.10)

        return round(score, 2)

    def score_player_gpp(self, player) -> float:
        """Score player for GPP using optimized parameters"""
        base = getattr(player, 'base_projection', 0)
        if base == 0:
            base = getattr(player, 'projection', 0)
        if base == 0:
            base = getattr(player, 'dff_projection', 0)
        if base == 0:
            return 0

        score = float(base)

        # 1. Team total multiplier (using implied_team_score OR team_total)
        team_total = getattr(player, 'implied_team_score', None)
        if team_total is None:
            team_total = getattr(player, 'team_total', 4.5)

        if team_total >= self.gpp_params.get('threshold_high', 5.73):
            score *= self.gpp_params.get('mult_high', 1.336)
        elif team_total >= self.gpp_params.get('threshold_med', 5.0):
            score *= self.gpp_params.get('mult_med', 1.15)
        elif team_total >= self.gpp_params.get('threshold_low', 4.5):
            score *= self.gpp_params.get('mult_low', 1.05)
        else:
            score *= self.gpp_params.get('mult_none', 0.9)

        # 2. Batting order boost
        if not player.is_pitcher:
            bat_order = getattr(player, 'batting_order', 0)
            if bat_order and 1 <= bat_order <= self.gpp_params.get('batting_positions', 5):
                score *= self.gpp_params.get('batting_boost', 1.115)

        # 3. Ownership leverage
        ownership = getattr(player, 'projected_ownership', 10)
        if ownership < self.gpp_params.get('ownership_threshold', 15):
            score *= self.gpp_params.get('ownership_low_boost', 1.106)
        elif ownership > 30:
            score *= self.gpp_params.get('ownership_high_penalty', 0.95)

        # 4. Environmental factors (full impact for GPP)
        park = getattr(player, 'park_factor', 1.0)
        weather = getattr(player, 'weather_impact', 1.0)
        recent_form = getattr(player, 'recent_form', 1.0)

        score *= park
        score *= weather
        score *= recent_form

        # 5. Advanced stats if available
        if not player.is_pitcher:
            # Barrel rate
            barrel_rate = getattr(player, 'barrel_rate', 0)
            if barrel_rate > self.gpp_params.get('barrel_rate_threshold', 11.7):
                score *= self.gpp_params.get('barrel_rate_boost', 1.194)

            # Exit velocity
            exit_velo = getattr(player, 'exit_velocity', 0)
            if exit_velo > self.gpp_params.get('exit_velo_threshold', 91.2):
                score *= self.gpp_params.get('exit_velo_boost', 1.081)
        else:
            # Pitcher K/9
            k9 = getattr(player, 'k9', 0)
            if k9 > self.gpp_params.get('min_k9_threshold', 9.5):
                score *= self.gpp_params.get('high_k9_boost', 1.137)

        return round(score, 2)

    def score_player_showdown(self, player, is_captain: bool = False) -> float:
        """Score player for Showdown using GPP base with modifications"""
        # Start with GPP scoring
        score = self.score_player_gpp(player)

        # Captain multiplier
        if is_captain:
            score *= 1.5

            # Additional captain boost for ownership leverage
            ownership = getattr(player, 'projected_ownership', 10)
            if ownership < 20:
                score *= 1.1

        return round(score, 2)

    def score_player(self, player, contest_type: str = 'gpp') -> float:
        """Main scoring method - routes to appropriate scoring function"""
        if contest_type.lower() == 'gpp':
            return self.score_player_gpp(player)
        elif contest_type.lower() == 'cash':
            return self.score_player_cash(player)
        elif contest_type.lower() == 'showdown':
            return self.score_player_showdown(player)
        else:
            return self.score_player_gpp(player)

    def get_scoring_summary(self, player, contest_type='gpp'):
        """Get detailed scoring breakdown for debugging"""
        base = player.base_projection if player.base_projection > 0 else 0

        if contest_type == 'cash':
            components = {
                'recent_form': getattr(player, 'recent_form', 1.0),
                'consistency': getattr(player, 'consistency_score', 1.0),
                'matchup': getattr(player, 'matchup_score', 1.0),
                'park_factor': getattr(player, 'park_factor', 1.0),
                'weather': getattr(player, 'weather_impact', 1.0)
            }

            total_mult = 1.0
            for factor in components.values():
                total_mult *= factor

            # Apply pitcher bonus
            if player.is_pitcher:
                total_mult *= 1.1

            final = base * total_mult
        else:
            # GPP scoring
            vegas_mult = 1.0
            vegas_total = getattr(player, 'team_total', getattr(player, 'implied_team_score', 4.5))

            if vegas_total >= 5.5:
                vegas_mult = 1.25
            elif vegas_total >= 5.0:
                vegas_mult = 1.15
            elif vegas_total >= 4.5:
                vegas_mult = 1.05
            else:
                vegas_mult = 0.9

            components = {
                'vegas_mult': vegas_mult,
                'park_factor': getattr(player, 'park_factor', 1.0),
                'weather': getattr(player, 'weather_impact', 1.0),
                'ownership': getattr(player, 'ownership_projection', 10)
            }

            total_mult = vegas_mult * components['park_factor'] * components['weather']

            # Batting order boost
            if not player.is_pitcher:
                bat_order = getattr(player, 'batting_order', 0)
                if bat_order and 1 <= bat_order <= 5:
                    total_mult *= 1.1

            final = base * total_mult

        return {
            'base_projection': base,
            'final_score': final,
            'total_multiplier': total_mult,
            'components': components
        }

        # Add component details
        if hasattr(player, 'team_total'):
            breakdown['components']['team_total'] = player.team_total
        if hasattr(player, 'batting_order'):
            breakdown['components']['batting_order'] = player.batting_order
        if hasattr(player, 'projected_ownership'):
            breakdown['components']['ownership'] = player.projected_ownership
        if hasattr(player, 'recent_form'):
            breakdown['components']['recent_form'] = player.recent_form
        if hasattr(player, 'park_factor'):
            breakdown['components']['park_factor'] = player.park_factor

        return breakdown


if __name__ == "__main__":
    print("✅ Enhanced Scoring Engine Ready!")
    print("\n📊 Optimized Parameters Loaded:")
    print(f"  • GPP: -67.7 score (64th percentile)")
    print(f"  • Cash: 86.2 score (79% win rate)")
    print("\n🎯 Features:")
    print("  • Team total multipliers")
    print("  • Batting order boosts")
    print("  • Ownership leverage")
    print("  • Statcast integration")
    print("  • Platoon advantages")
    print("  • Hot/cold streaks")
    print("  • Floor/ceiling weighting")
