#!/usr/bin/env python3
"""
STATCAST VALUE ENGINE
====================
Enhanced value calculations using advanced Statcast metrics
Provides competitive edge through skill-based player evaluation
"""

import logging
from typing import List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StatcastThresholds:
    """Statcast metric thresholds for value calculations"""
    
    # Batter thresholds (percentile-based)
    barrel_rate_elite: float = 15.0      # Top 10%
    barrel_rate_good: float = 10.0       # Top 30%
    barrel_rate_poor: float = 5.0        # Bottom 30%
    
    xwoba_elite: float = 0.360           # Top 10%
    xwoba_good: float = 0.330            # Top 30%
    xwoba_poor: float = 0.300            # Bottom 30%
    
    hard_hit_elite: float = 45.0         # Top 10%
    hard_hit_poor: float = 35.0          # Bottom 30%
    
    exit_velo_elite: float = 91.0        # Top 10%
    exit_velo_poor: float = 86.0         # Bottom 30%
    
    # Pitcher thresholds (already ML-optimized)
    k_rate_elite: float = 10.5           # ML-optimized threshold
    k_rate_good: float = 8.5             # Good threshold
    k_rate_poor: float = 7.0             # Poor threshold
    
    era_elite: float = 3.00              # Elite ERA
    era_good: float = 3.75               # Good ERA
    era_poor: float = 5.00               # Poor ERA
    
    whip_elite: float = 1.10             # Elite WHIP
    whip_poor: float = 1.50              # Poor WHIP


class StatcastValueEngine:
    """Enhanced value calculations using Statcast metrics"""
    
    def __init__(self):
        self.thresholds = StatcastThresholds()
        
        # Value multipliers (conservative to start)
        self.multipliers = {
            # Batter multipliers
            'barrel_elite': 1.20,        # 20% boost for elite barrel rate
            'barrel_good': 1.10,         # 10% boost for good barrel rate
            'barrel_poor': 0.90,         # 10% penalty for poor barrel rate
            
            'xwoba_elite': 1.15,         # 15% boost for elite xwOBA
            'xwoba_good': 1.08,          # 8% boost for good xwOBA
            'xwoba_poor': 0.92,          # 8% penalty for poor xwOBA
            
            'hard_hit_elite': 1.08,      # 8% boost for elite hard hit
            'hard_hit_poor': 0.95,       # 5% penalty for poor hard hit
            
            'exit_velo_elite': 1.05,     # 5% boost for elite exit velo
            'exit_velo_poor': 0.97,      # 3% penalty for poor exit velo
            
            # Pitcher multipliers (using ML-optimized K-rate)
            'k_rate_elite': 1.25,        # ML-optimized (was 1.20)
            'k_rate_good': 1.10,         # Good K-rate
            'k_rate_poor': 0.85,         # Poor K-rate penalty
            
            'era_elite': 1.15,           # Elite run prevention
            'era_good': 1.05,            # Good run prevention
            'era_poor': 0.90,            # Poor run prevention
            
            'whip_elite': 1.10,          # Elite baserunner prevention
            'whip_poor': 0.92,           # Poor baserunner prevention
        }
    
    def calculate_statcast_value(self, player) -> float:
        """
        Calculate enhanced value using Statcast metrics
        
        Returns value per $1000 salary adjusted for skill level
        """
        
        # Base value (projection efficiency)
        if player.salary <= 0:
            return 0.0
            
        base_value = player.projection / (player.salary / 1000)
        
        # Apply Statcast multipliers based on position
        if player.position in ['P', 'SP', 'RP']:
            statcast_multiplier = self._get_pitcher_multiplier(player)
        else:
            statcast_multiplier = self._get_batter_multiplier(player)
        
        enhanced_value = base_value * statcast_multiplier
        
        # Log significant value adjustments
        if abs(statcast_multiplier - 1.0) > 0.15:  # >15% adjustment
            logger.debug(f"{player.name}: Base value {base_value:.2f} → "
                        f"Enhanced value {enhanced_value:.2f} "
                        f"(multiplier: {statcast_multiplier:.3f})")
        
        return enhanced_value
    
    def _get_batter_multiplier(self, player) -> float:
        """Calculate Statcast multiplier for batters"""
        
        multiplier = 1.0
        
        # Barrel rate (most predictive of power)
        barrel_rate = getattr(player, 'barrel_rate', 8.5)
        if barrel_rate >= self.thresholds.barrel_rate_elite:
            multiplier *= self.multipliers['barrel_elite']
        elif barrel_rate >= self.thresholds.barrel_rate_good:
            multiplier *= self.multipliers['barrel_good']
        elif barrel_rate <= self.thresholds.barrel_rate_poor:
            multiplier *= self.multipliers['barrel_poor']
        
        # xwOBA (most predictive of overall hitting)
        xwoba = getattr(player, 'xwoba', 0.320)
        if xwoba >= self.thresholds.xwoba_elite:
            multiplier *= self.multipliers['xwoba_elite']
        elif xwoba >= self.thresholds.xwoba_good:
            multiplier *= self.multipliers['xwoba_good']
        elif xwoba <= self.thresholds.xwoba_poor:
            multiplier *= self.multipliers['xwoba_poor']
        
        # Hard hit rate (consistency indicator)
        hard_hit_rate = getattr(player, 'hard_hit_rate', 40.0)
        if hard_hit_rate >= self.thresholds.hard_hit_elite:
            multiplier *= self.multipliers['hard_hit_elite']
        elif hard_hit_rate <= self.thresholds.hard_hit_poor:
            multiplier *= self.multipliers['hard_hit_poor']
        
        # Exit velocity (power indicator)
        exit_velo = getattr(player, 'avg_exit_velo', 88.0)
        if exit_velo >= self.thresholds.exit_velo_elite:
            multiplier *= self.multipliers['exit_velo_elite']
        elif exit_velo <= self.thresholds.exit_velo_poor:
            multiplier *= self.multipliers['exit_velo_poor']
        
        return multiplier
    
    def _get_pitcher_multiplier(self, player) -> float:
        """Calculate Statcast multiplier for pitchers"""
        
        multiplier = 1.0
        
        # K-rate (using ML-optimized thresholds)
        k_rate = getattr(player, 'k_rate', 8.0)
        if k_rate >= self.thresholds.k_rate_elite:
            multiplier *= self.multipliers['k_rate_elite']  # ML-optimized 1.25
        elif k_rate >= self.thresholds.k_rate_good:
            multiplier *= self.multipliers['k_rate_good']
        elif k_rate <= self.thresholds.k_rate_poor:
            multiplier *= self.multipliers['k_rate_poor']
        
        # ERA (run prevention)
        era = getattr(player, 'era', 4.00)
        if era <= self.thresholds.era_elite:
            multiplier *= self.multipliers['era_elite']
        elif era <= self.thresholds.era_good:
            multiplier *= self.multipliers['era_good']
        elif era >= self.thresholds.era_poor:
            multiplier *= self.multipliers['era_poor']
        
        # WHIP (baserunner prevention)
        whip = getattr(player, 'whip', 1.30)
        if whip <= self.thresholds.whip_elite:
            multiplier *= self.multipliers['whip_elite']
        elif whip >= self.thresholds.whip_poor:
            multiplier *= self.multipliers['whip_poor']
        
        return multiplier
    
    def get_traditional_value(self, player) -> float:
        """Get traditional projection-based value for comparison"""
        if player.salary <= 0:
            return 0.0
        return player.projection / (player.salary / 1000)
    
    def analyze_value_differences(self, players: List) -> dict:
        """Analyze differences between traditional and Statcast values"""
        
        analysis = {
            'total_players': len(players),
            'significant_upgrades': 0,    # >15% value increase
            'significant_downgrades': 0,  # >15% value decrease
            'avg_multiplier': 0.0,
            'max_upgrade': 0.0,
            'max_downgrade': 0.0,
            'examples': []
        }
        
        multipliers = []
        
        for player in players:
            traditional_value = self.get_traditional_value(player)
            statcast_value = self.calculate_statcast_value(player)
            
            if traditional_value > 0:
                multiplier = statcast_value / traditional_value
                multipliers.append(multiplier)
                
                # Track significant changes
                if multiplier >= 1.15:
                    analysis['significant_upgrades'] += 1
                    if multiplier > analysis['max_upgrade']:
                        analysis['max_upgrade'] = multiplier
                elif multiplier <= 0.85:
                    analysis['significant_downgrades'] += 1
                    if multiplier < analysis['max_downgrade'] or analysis['max_downgrade'] == 0:
                        analysis['max_downgrade'] = multiplier
                
                # Store examples of significant changes
                if abs(multiplier - 1.0) > 0.15:
                    analysis['examples'].append({
                        'name': player.name,
                        'position': player.position,
                        'traditional_value': traditional_value,
                        'statcast_value': statcast_value,
                        'multiplier': multiplier,
                        'barrel_rate': getattr(player, 'barrel_rate', 0),
                        'xwoba': getattr(player, 'xwoba', 0),
                        'k_rate': getattr(player, 'k_rate', 0)
                    })
        
        if multipliers:
            analysis['avg_multiplier'] = sum(multipliers) / len(multipliers)
        
        return analysis


# Test the Statcast value engine
if __name__ == "__main__":
    print("🔬 STATCAST VALUE ENGINE TEST")
    print("=" * 50)
    
    # Create test players
    class TestPlayer:
        def __init__(self, name, position, salary, projection, **stats):
            self.name = name
            self.position = position
            self.salary = salary
            self.projection = projection
            for stat, value in stats.items():
                setattr(self, stat, value)
    
    test_players = [
        TestPlayer("Elite Hitter", "OF", 5000, 13.0, 
                  barrel_rate=16.0, xwoba=0.370, hard_hit_rate=47.0),
        TestPlayer("Average Hitter", "OF", 5000, 13.0, 
                  barrel_rate=8.5, xwoba=0.320, hard_hit_rate=40.0),
        TestPlayer("Poor Hitter", "OF", 5000, 13.0, 
                  barrel_rate=4.0, xwoba=0.290, hard_hit_rate=33.0),
        TestPlayer("Elite Pitcher", "P", 10000, 25.0, 
                  k_rate=11.5, era=2.80, whip=1.05),
        TestPlayer("Average Pitcher", "P", 10000, 25.0, 
                  k_rate=8.5, era=4.00, whip=1.30),
    ]
    
    engine = StatcastValueEngine()
    
    print("Value Comparison:")
    for player in test_players:
        traditional = engine.get_traditional_value(player)
        statcast = engine.calculate_statcast_value(player)
        multiplier = statcast / traditional if traditional > 0 else 0
        
        print(f"{player.name:15} Traditional: {traditional:.2f} "
              f"Statcast: {statcast:.2f} (multiplier: {multiplier:.3f})")
    
    print("\n✅ Statcast Value Engine ready for implementation!")
