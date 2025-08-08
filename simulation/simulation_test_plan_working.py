#!/usr/bin/env python3
"""
WORKING SIMULATION TEST
========================
Handles the actual return type from optimize_lineup
"""

import sys
import os
import json
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
from main_optimizer.unified_player_model import UnifiedPlayer
from realistic_dfs_simulator import (
    RealisticDFSSimulator,
    generate_realistic_slate,
    analyze_contest_results
)

class StrategyTester:
    def __init__(self):
        self.system = UnifiedCoreSystem()
    
    def test_strategy(self, strategy_name: str, contest_type: str, num_contests: int = 30):
        """Test a strategy against realistic competition"""
        
        print(f"\n🎯 Testing {strategy_name} ({contest_type.upper()})")
        print(f"   Running {num_contests} contests...")
        
        wins = 0
        top10s = 0
        total_roi = 0
        all_placements = []
        stack_sizes = []
        
        for contest_num in range(num_contests):
            if contest_num % 10 == 0:
                print(f"   Progress: {contest_num}/{num_contests}")
            
            # Generate slate
            slate = generate_realistic_slate(200, 'medium')
            
            # Convert to your format
            your_players = []
            for sp in slate:
                player = UnifiedPlayer(
                    name=sp.name,
                    position=sp.position,
                    team=sp.team,
                    salary=sp.salary,
                    opponent='OPP',
                    player_id=sp.name,
                    base_projection=sp.projection
                )
                player.ownership = sp.ownership * 100
                player.batting_order = getattr(sp, 'batting_order', 0)
                player.projection = sp.projection
                player.primary_position = sp.position
                your_players.append(player)
            
            # Generate YOUR lineup
            self.system.player_pool = your_players
            
            try:
                # optimize_lineup returns a LIST of players!
                lineup_result = self.system.optimize_lineup(
                    strategy=strategy_name,
                    contest_type=contest_type
                )
                
                if not lineup_result:
                    continue
                
                # Handle different return types
                if isinstance(lineup_result, list):
                    # It's a list of players
                    lineup_players = lineup_result
                elif isinstance(lineup_result, dict) and 'players' in lineup_result:
                    # It's a dict with players key
                    lineup_players = lineup_result['players']
                else:
                    # Try to extract players some other way
                    if hasattr(lineup_result, 'players'):
                        lineup_players = lineup_result.players
                    else:
                        print(f"   Unknown lineup format: {type(lineup_result)}")
                        continue
                
                # Make sure we have 10 players
                if len(lineup_players) != 10:
                    print(f"   Invalid lineup size: {len(lineup_players)}")
                    continue
                    
            except Exception as e:
                print(f"   Error generating lineup: {e}")
                continue
            
            # Check stack size
            teams = defaultdict(int)
            for p in lineup_players:
                if hasattr(p, 'position') and p.position != 'P':
                    teams[p.team] += 1
            
            max_stack = max(teams.values()) if teams else 0
            stack_sizes.append(max_stack)
            
            # Convert lineup to sim format for contest
            sim_players = []
            for lp in lineup_players:
                # Find matching sim player
                for sp in slate:
                    if sp.name == lp.name:
                        sim_players.append(sp)
                        break
            
            if len(sim_players) != 10:
                continue  # Couldn't match all players
            
            # Create entry for contest
            your_entry = {
                'players': sim_players,
                'stack_pattern': f'{max_stack}-man' if max_stack >= 2 else 'no_stack',
                'total_salary': sum(p.salary for p in sim_players),
                'is_valid': True
            }
            
            # Create contest
            sim = RealisticDFSSimulator(100, 'medium')
            field = sim.generate_realistic_field(slate)
            field.append(your_entry)
            
            # Simulate
            scored = sim.simulate_scoring(field)
            results = sim.calculate_payouts(scored)
            
            # Find your placement
            for i, result in enumerate(results):
                if result['lineup'] == your_entry:
                    placement = result['rank']
                    roi = result['roi']
                    
                    all_placements.append(placement)
                    total_roi += roi
                    
                    if placement == 1:
                        wins += 1
                    if placement <= 10:
                        top10s += 1
                    break
        
        # Print results
        if all_placements:
            n = len(all_placements)
            avg_placement = sum(all_placements) / n
            win_rate = (wins / n) * 100
            top10_rate = (top10s / n) * 100
            avg_roi = total_roi / n
            avg_stack = sum(stack_sizes) / len(stack_sizes) if stack_sizes else 0
            
            print(f"\n📊 {strategy_name} Results:")
            print(f"   Valid contests: {n}/{num_contests}")
            print(f"   Avg placement: {avg_placement:.1f}/100")
            print(f"   Win rate: {win_rate:.1f}%")
            print(f"   Top 10 rate: {top10_rate:.1f}%")
            print(f"   Avg ROI: {avg_roi:+.1f}%")
            
            if contest_type == 'gpp':
                print(f"   Avg stack size: {avg_stack:.1f} players")
                stacks_4plus = sum(1 for s in stack_sizes if s >= 4)
                stack_rate = (stacks_4plus / len(stack_sizes)) * 100 if stack_sizes else 0
                print(f"   4+ player stacks: {stack_rate:.0f}%")
                
                if stack_rate < 80:
                    print(f"   ⚠️ WARNING: Need more stacking! (Winners use 83%)")
                else:
                    print(f"   ✅ Good stacking!")
            
            return {
                'strategy': strategy_name,
                'win_rate': win_rate,
                'top10_rate': top10_rate,
                'avg_roi': avg_roi,
                'avg_stack': avg_stack
            }
        
        return None

def main():
    print("="*60)
    print("🚀 TESTING YOUR STRATEGIES")
    print("="*60)
    print("\nAgainst REALISTIC competition:")
    print("• 1.3% of players win 91% of profits")
    print("• 83% of winners use 4-5 player stacks")
    
    tester = StrategyTester()
    
    # Quick test - just 20 contests each
    strategies = [
        ('tournament_winner_gpp', 'gpp'),
        ('cash', 'cash'),
    ]
    
    for strategy, contest_type in strategies:
        tester.test_strategy(strategy, contest_type, num_contests=20)
    
    print("\n" + "="*60)
    print("✅ Test complete!")
    print("\nKey Questions:")
    print("1. Are GPP strategies using 4+ stacks 80%+ of the time?")
    print("2. Is ROI better than -50% against sharks?")
    print("3. Are cash strategies avoiding heavy stacks?")

if __name__ == "__main__":
    main()
