#!/usr/bin/env python3
"""
SYSTEM COMPARISON TEST
======================
Direct comparison between old projection-based and new Statcast-enhanced systems
"""

import sys
import os
sys.path.append('dfs_optimizer_v2')

from data_pipeline_v2 import Player
from strategies_v2 import StrategyManager
from statcast_value_engine import StatcastValueEngine


class SystemComparison:
    """Compare old vs new value calculation systems"""
    
    def __init__(self):
        self.strategy_manager = StrategyManager()
        self.statcast_engine = StatcastValueEngine()
    
    def create_test_players(self):
        """Create realistic test players with varying Statcast profiles"""
        
        players = [
            # Elite Statcast players (underpriced studs)
            Player('Elite Hitter A', 'OF', 'LAD', 4500, 12.0),
            Player('Elite Hitter B', 'OF', 'NYY', 5000, 13.5),
            Player('Elite Pitcher A', 'P', 'LAD', 8000, 22.0),
            
            # Poor Statcast players (overpriced)
            Player('Poor Hitter A', 'OF', 'TEX', 4500, 12.0),
            Player('Poor Hitter B', 'OF', 'BAL', 5000, 13.5),
            Player('Poor Pitcher A', 'P', 'TEX', 8000, 22.0),
            
            # Average Statcast players (fairly priced)
            Player('Average Hitter A', 'OF', 'BOS', 4500, 12.0),
            Player('Average Hitter B', 'OF', 'HOU', 5000, 13.5),
            Player('Average Pitcher A', 'P', 'BOS', 8000, 22.0),
        ]
        
        # Set Statcast attributes
        # Elite players
        for i in [0, 1]:  # Elite hitters
            players[i].barrel_rate = 16.0
            players[i].xwoba = 0.370
            players[i].hard_hit_rate = 47.0
            players[i].avg_exit_velo = 92.0
        
        players[2].k_rate = 11.5  # Elite pitcher
        players[2].era = 2.80
        players[2].whip = 1.05
        
        # Poor players
        for i in [3, 4]:  # Poor hitters
            players[i].barrel_rate = 4.0
            players[i].xwoba = 0.290
            players[i].hard_hit_rate = 33.0
            players[i].avg_exit_velo = 85.0
        
        players[5].k_rate = 6.5  # Poor pitcher
        players[5].era = 5.20
        players[5].whip = 1.55
        
        # Average players
        for i in [6, 7]:  # Average hitters
            players[i].barrel_rate = 8.5
            players[i].xwoba = 0.320
            players[i].hard_hit_rate = 40.0
            players[i].avg_exit_velo = 88.0
        
        players[8].k_rate = 8.5  # Average pitcher
        players[8].era = 4.00
        players[8].whip = 1.30
        
        # Set common attributes
        for player in players:
            player.optimization_score = player.projection
            player.implied_team_score = 5.0
            player.ownership = 12.0
            player.consistency_score = 75
        
        return players
    
    def calculate_traditional_value(self, player):
        """Calculate old projection-based value"""
        if player.salary <= 0:
            return 0.0
        return player.projection / (player.salary / 1000)
    
    def run_comparison(self):
        """Run comprehensive comparison between systems"""
        
        print("🔍 OLD vs NEW SYSTEM COMPARISON")
        print("=" * 80)
        
        players = self.create_test_players()
        
        print("📊 VALUE CALCULATION COMPARISON:")
        print("-" * 80)
        print(f"{'Player':<20} {'Traditional':<12} {'Statcast':<12} {'Difference':<12} {'% Change':<10}")
        print("-" * 80)
        
        total_traditional = 0
        total_statcast = 0
        significant_changes = 0
        
        for player in players:
            traditional_value = self.calculate_traditional_value(player)
            statcast_value = self.statcast_engine.calculate_statcast_value(player)
            
            difference = statcast_value - traditional_value
            pct_change = (difference / traditional_value * 100) if traditional_value > 0 else 0
            
            total_traditional += traditional_value
            total_statcast += statcast_value
            
            if abs(pct_change) > 15:  # Significant change
                significant_changes += 1
            
            print(f"{player.name:<20} {traditional_value:<12.2f} {statcast_value:<12.2f} "
                  f"{difference:<12.2f} {pct_change:<10.1f}%")
        
        print("-" * 80)
        print(f"{'TOTALS':<20} {total_traditional:<12.2f} {total_statcast:<12.2f} "
              f"{total_statcast - total_traditional:<12.2f} "
              f"{(total_statcast - total_traditional) / total_traditional * 100:<10.1f}%")
        
        print(f"\nSignificant changes (>15%): {significant_changes}/{len(players)} players")
        
        # Strategy application comparison
        print("\n🎯 STRATEGY APPLICATION COMPARISON:")
        print("-" * 80)
        
        # Test correlation value strategy
        print("\nCorrelation Value Strategy Results:")
        print(f"{'Player':<20} {'Old Boost':<10} {'New Boost':<10} {'Value Play':<12}")
        print("-" * 60)
        
        # Old system simulation (traditional value)
        old_results = []
        for player in players:
            if player.position not in ['P', 'SP', 'RP']:
                traditional_value = self.calculate_traditional_value(player)
                team_total = getattr(player, 'implied_team_score', 4.5)
                
                if traditional_value >= 3.5 and team_total >= 5.0:
                    boost = 1.08
                    value_play = True
                elif team_total >= 5.0:
                    boost = 1.06
                    value_play = False
                else:
                    boost = 1.00
                    value_play = False
                
                old_results.append((player.name, boost, value_play))
        
        # New system (Statcast value)
        new_players = [p for p in players.copy()]
        for player in new_players:
            player.optimization_score = player.projection
        
        enhanced_players = self.strategy_manager._optimized_correlation_value(new_players)
        
        # Compare results
        old_idx = 0
        for player in enhanced_players:
            if player.position not in ['P', 'SP', 'RP']:
                new_boost = player.optimization_score / player.projection
                new_value_play = getattr(player, 'value_play', False)
                
                if old_idx < len(old_results):
                    old_name, old_boost, old_value_play = old_results[old_idx]
                    print(f"{player.name:<20} {old_boost:<10.3f} {new_boost:<10.3f} "
                          f"Old: {old_value_play}, New: {new_value_play}")
                    old_idx += 1
        
        return self.generate_comparison_summary(players)
    
    def generate_comparison_summary(self, players):
        """Generate comprehensive comparison summary"""
        
        print("\n" + "=" * 80)
        print("📈 SYSTEM COMPARISON SUMMARY")
        print("=" * 80)
        
        # Calculate metrics
        elite_players = players[:3]  # First 3 are elite
        poor_players = players[3:6]  # Next 3 are poor
        avg_players = players[6:]    # Last 3 are average
        
        print("\n🎯 VALUE IDENTIFICATION ACCURACY:")
        print("-" * 50)
        
        # Elite players should get higher values
        elite_improvements = []
        for player in elite_players:
            traditional = self.calculate_traditional_value(player)
            statcast = self.statcast_engine.calculate_statcast_value(player)
            improvement = (statcast - traditional) / traditional * 100
            elite_improvements.append(improvement)
        
        # Poor players should get lower values
        poor_penalties = []
        for player in poor_players:
            traditional = self.calculate_traditional_value(player)
            statcast = self.statcast_engine.calculate_statcast_value(player)
            penalty = (traditional - statcast) / traditional * 100
            poor_penalties.append(penalty)
        
        avg_elite_improvement = sum(elite_improvements) / len(elite_improvements)
        avg_poor_penalty = sum(poor_penalties) / len(poor_penalties)
        
        print(f"Elite players value increase: {avg_elite_improvement:.1f}% average")
        print(f"Poor players value decrease: {avg_poor_penalty:.1f}% average")
        
        print("\n✅ OLD SYSTEM ADVANTAGES:")
        print("- Simple and straightforward")
        print("- No dependency on Statcast data quality")
        print("- Consistent baseline performance")
        print("- Less complex to maintain")
        
        print("\n🚀 NEW SYSTEM ADVANTAGES:")
        print(f"- {avg_elite_improvement:.1f}% better identification of elite players")
        print(f"- {avg_poor_penalty:.1f}% better avoidance of poor players")
        print("- Uses available competitive data")
        print("- Aligns with your DFS research (barrel rate → home runs)")
        print("- Market inefficiency exploitation")
        
        print("\n⚠️ OLD SYSTEM DISADVANTAGES:")
        print("- Circular logic (projection often based on salary)")
        print("- No skill differentiation (same salary = same value)")
        print("- Misses underpriced elite talent")
        print("- Doesn't avoid overpriced poor players")
        print("- Ignores available competitive advantage")
        
        print("\n⚠️ NEW SYSTEM DISADVANTAGES:")
        print("- More complex implementation")
        print("- Dependency on Statcast data quality")
        print("- Requires threshold tuning")
        print("- Potential over-optimization risk")
        
        print("\n🎯 RECOMMENDATION:")
        if avg_elite_improvement > 20 and avg_poor_penalty > 10:
            print("✅ NEW SYSTEM RECOMMENDED")
            print(f"Significant edge from better player evaluation")
            print(f"Elite player identification: +{avg_elite_improvement:.1f}%")
            print(f"Poor player avoidance: +{avg_poor_penalty:.1f}%")
        elif avg_elite_improvement > 10:
            print("✅ NEW SYSTEM RECOMMENDED (with monitoring)")
            print("Moderate improvement with manageable complexity")
        else:
            print("⚠️ STICK WITH OLD SYSTEM")
            print("Improvements not significant enough to justify complexity")
        
        return {
            'elite_improvement': avg_elite_improvement,
            'poor_penalty': avg_poor_penalty,
            'recommendation': 'new' if avg_elite_improvement > 15 else 'old'
        }


if __name__ == "__main__":
    comparison = SystemComparison()
    results = comparison.run_comparison()
    
    print(f"\n🎉 COMPARISON COMPLETE!")
    print(f"Elite player improvement: {results['elite_improvement']:.1f}%")
    print(f"Poor player penalty: {results['poor_penalty']:.1f}%")
    print(f"Recommendation: {results['recommendation'].upper()} system")
