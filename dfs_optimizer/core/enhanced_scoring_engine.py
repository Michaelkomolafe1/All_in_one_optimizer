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
    
    def score_player_gpp(self, player) -> float:
        """
        Score player for GPP using optimized parameters
        """
        score = player.base_projection
        
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
        """
        Score player for Cash games using optimized parameters
        """
        # Get component scores
        projection_score = player.base_projection
        
        # Recent form score
        recent_score = player.recent_form_score if hasattr(player, 'recent_form_score') else projection_score
        
        # Season average (simplified - would need full season stats)
        season_score = projection_score  # Use full projection for cash
        
        # Weighted combination
        base_score = (
            projection_score * self.cash_params['weight_projection'] +
            recent_score * self.cash_params['weight_recent'] +
            season_score * self.cash_params['weight_season']
        )
        
        # Consistency adjustment
        if self.cash_params['consistency_method'] == 'both':
            # Reduce variance for cash games
            consistency_factor = 1.0 - (self.cash_params['consistency_weight'] * 0.05)  # Reduce by up to 5%
            base_score *= consistency_factor
        
        # Platoon advantage
        if self.cash_params['use_platoon'] and hasattr(player, 'platoon_advantage'):
            if player.platoon_advantage:
                base_score *= self.cash_params['platoon_advantage_boost']
        
        # Hot/cold streaks
        if self.cash_params['use_streaks'] and hasattr(player, 'recent_form_score'):
            if player.recent_form_score > 15:  # Hot
                base_score *= self.cash_params['streak_hot_boost']
            elif player.recent_form_score < 5:  # Cold
                base_score *= self.cash_params['streak_cold_penalty']
        
        # Floor/ceiling weighting
        floor = base_score * 0.9  # Conservative floor estimate
        ceiling = base_score * 1.3  # Upside estimate
        
        final_score = (
            floor * self.cash_params['floor_weight'] +
            ceiling * self.cash_params['ceiling_weight']
        )
        
        return final_score
    
    def score_player_showdown(self, player, is_captain: bool = False) -> float:
        """
        Score player for Showdown using GPP base with modifications
        """
        # Start with GPP scoring
        score = self.score_player_gpp(player)
        
        # Captain multiplier (scoring only, not salary)
        if is_captain:
            score *= 1.5
            
            # Additional captain boost for ownership leverage
            if hasattr(player, 'projected_ownership') and player.projected_ownership < 20:
                score *= 1.1  # Low-owned captain bonus
        
        return score
    
    def score_player(self, player, contest_type: str = 'gpp') -> float:
        """
        Main scoring method - routes to appropriate scoring function
        """
        if contest_type.lower() == 'gpp':
            return self.score_player_gpp(player)
        elif contest_type.lower() == 'cash':
            return self.score_player_cash(player)
        elif contest_type.lower() == 'showdown':
            return self.score_player_showdown(player)
        else:
            # Default to GPP
            return self.score_player_gpp(player)
    
    def get_scoring_summary(self, player, contest_type: str = 'gpp') -> Dict:
        """
        Get detailed scoring breakdown for transparency
        """
        base = player.base_projection
        final = self.score_player(player, contest_type)
        multiplier = final / base if base > 0 else 1.0
        
        breakdown = {
            'player': player.name,
            'contest_type': contest_type,
            'base_projection': base,
            'final_score': final,
            'total_multiplier': multiplier,
            'components': {}
        }
        
        # Add component details based on what affected the score
        if hasattr(player, 'implied_team_score'):
            breakdown['components']['team_total'] = player.implied_team_score
        if hasattr(player, 'batting_order'):
            breakdown['components']['batting_order'] = player.batting_order
        if hasattr(player, 'projected_ownership'):
            breakdown['components']['ownership'] = player.projected_ownership
            
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
