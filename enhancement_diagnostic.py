#!/usr/bin/env python3
"""
ENHANCEMENT DIAGNOSTIC TOOL
============================
Check if Statcast enhancements and optimized strategies are working properly
"""

import sys
sys.path.append('dfs_optimizer_v2')

from data_pipeline_v2 import DFSPipeline, Player
from strategies_v2 import StrategyManager


def test_enhancements():
    """Test if enhancements are working properly"""
    
    print("🔬 ENHANCEMENT DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Create test players with different Statcast profiles
    test_players = [
        # Elite pitcher (should get big boost)
        Player('Elite Pitcher', 'SP', 'LAD', 9000, 20.0),
        
        # Poor pitcher (should get penalty or no boost)
        Player('Poor Pitcher', 'SP', 'TEX', 9000, 20.0),
        
        # Elite hitter (should get boost)
        Player('Elite Hitter', 'OF', 'LAD', 5000, 10.0),
        
        # Poor hitter (should get penalty)
        Player('Poor Hitter', 'OF', 'TEX', 5000, 10.0),
        
        # Average player (should get minimal change)
        Player('Average Player', 'OF', 'BOS', 5000, 10.0)
    ]
    
    # Set Statcast attributes
    # Elite pitcher
    test_players[0].k_rate = 12.0  # Elite K-rate
    test_players[0].era = 2.80
    test_players[0].whip = 1.05
    
    # Poor pitcher  
    test_players[1].k_rate = 6.5   # Poor K-rate
    test_players[1].era = 5.20
    test_players[1].whip = 1.55
    
    # Elite hitter
    test_players[2].barrel_rate = 16.0  # Elite barrel rate
    test_players[2].xwoba = 0.370       # Elite xwOBA
    test_players[2].hard_hit_rate = 47.0
    
    # Poor hitter
    test_players[3].barrel_rate = 4.0   # Poor barrel rate
    test_players[3].xwoba = 0.290       # Poor xwOBA
    test_players[3].hard_hit_rate = 33.0
    
    # Average hitter
    test_players[4].barrel_rate = 8.5   # Average
    test_players[4].xwoba = 0.320       # Average
    test_players[4].hard_hit_rate = 40.0
    
    # Set other required attributes
    for player in test_players:
        player.optimization_score = player.projection
        player.implied_team_score = 5.0
        player.ownership = 12.0
        player.consistency_score = 75
        player.recent_form = 1.0
    
    # Test strategy application
    strategy_manager = StrategyManager()
    
    print("BEFORE strategy application:")
    print(f"{'Player':<15} {'Pos':<3} {'Proj':<5} {'Opt':<5} {'K-rate':<7} {'Barrel':<7} {'xwOBA':<6}")
    print("-" * 60)
    
    for player in test_players:
        k_rate = getattr(player, 'k_rate', 0)
        barrel = getattr(player, 'barrel_rate', 0)
        xwoba = getattr(player, 'xwoba', 0)
        print(f"{player.name:<15} {player.position:<3} {player.projection:<5.1f} "
              f"{player.optimization_score:<5.1f} {k_rate:<7.1f} {barrel:<7.1f} {xwoba:<6.3f}")
    
    # Apply optimized pitcher dominance strategy
    enhanced_players = strategy_manager._optimized_pitcher_dominance(test_players.copy())
    
    print("\nAFTER optimized pitcher dominance strategy:")
    print(f"{'Player':<15} {'Pos':<3} {'Proj':<5} {'Opt':<5} {'Boost':<6} {'Enhancement':<15}")
    print("-" * 70)
    
    for player in enhanced_players:
        boost = player.optimization_score / player.projection
        
        # Determine enhancement type
        if player.position in ['SP', 'P']:
            k_rate = getattr(player, 'k_rate', 0)
            if k_rate >= 10.5:
                enhancement = "Elite K-rate"
            elif k_rate >= 8.5:
                enhancement = "Good K-rate"
            else:
                enhancement = "Poor K-rate"
        else:
            barrel = getattr(player, 'barrel_rate', 0)
            xwoba = getattr(player, 'xwoba', 0)
            if barrel >= 15.0:
                enhancement = "Elite Barrel"
            elif xwoba >= 0.360:
                enhancement = "Elite xwOBA"
            elif barrel >= 10.0 or xwoba >= 0.330:
                enhancement = "Good Statcast"
            else:
                enhancement = "Poor Statcast"
        
        print(f"{player.name:<15} {player.position:<3} {player.projection:<5.1f} "
              f"{player.optimization_score:<5.1f} {boost:<6.3f} {enhancement:<15}")
    
    print("\n🎯 ENHANCEMENT ANALYSIS:")
    
    # Check if elite players got boosts
    elite_pitcher = enhanced_players[0]
    poor_pitcher = enhanced_players[1]
    elite_hitter = enhanced_players[2]
    poor_hitter = enhanced_players[3]
    
    elite_pitcher_boost = elite_pitcher.optimization_score / elite_pitcher.projection
    poor_pitcher_boost = poor_pitcher.optimization_score / poor_pitcher.projection
    elite_hitter_boost = elite_hitter.optimization_score / elite_hitter.projection
    poor_hitter_boost = poor_hitter.optimization_score / poor_hitter.projection
    
    print(f"Elite pitcher boost: {elite_pitcher_boost:.3f}x ({'✅ GOOD' if elite_pitcher_boost > 1.15 else '❌ LOW'})")
    print(f"Poor pitcher boost: {poor_pitcher_boost:.3f}x ({'✅ GOOD' if poor_pitcher_boost < 1.05 else '❌ HIGH'})")
    print(f"Elite hitter boost: {elite_hitter_boost:.3f}x ({'✅ GOOD' if elite_hitter_boost > 1.05 else '❌ LOW'})")
    print(f"Poor hitter boost: {poor_hitter_boost:.3f}x ({'✅ GOOD' if poor_hitter_boost < 1.05 else '❌ HIGH'})")
    
    print("\n💡 RECOMMENDATIONS:")
    
    if elite_pitcher_boost < 1.15:
        print("❌ Elite pitcher not getting enough boost - check K-rate thresholds")
    
    if poor_pitcher_boost > 1.05:
        print("❌ Poor pitcher getting too much boost - check penalty logic")
    
    if elite_hitter_boost < 1.05:
        print("❌ Elite hitter not getting boost - check Statcast thresholds")
    
    if poor_hitter_boost > 1.05:
        print("❌ Poor hitter getting boost - check penalty logic")
    
    if (elite_pitcher_boost > 1.15 and poor_pitcher_boost < 1.05 and 
        elite_hitter_boost > 1.05 and poor_hitter_boost < 1.05):
        print("✅ Enhancements working correctly!")
    
    return enhanced_players


if __name__ == "__main__":
    test_enhancements()
