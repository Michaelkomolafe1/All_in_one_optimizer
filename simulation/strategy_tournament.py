#!/usr/bin/env python3
"""
STRATEGY TOURNAMENT FRAMEWORK
=============================
Test your exact DFS strategies against realistic competition
Uses your actual MILP optimizer and strategies from dfs_optimizer_v2
"""

import sys
import os
import json
import time
import multiprocessing as mp
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import numpy as np

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your actual DFS system
sys.path.append('dfs_optimizer_v2')
from data_pipeline_v2 import DFSPipeline, Player
from strategies_v2 import StrategyManager

# Import simulation components
from realistic_simulation_core import (
    generate_realistic_slate, 
    process_single_simulation,
    REALISTIC_PARAMS
)


class StrategyTournament:
    """Test your strategies against realistic competition"""
    
    def __init__(self):
        self.pipeline = DFSPipeline()
        self.strategy_manager = StrategyManager()
        
        # Your actual strategies to test
        self.your_strategies = {
            'cash': {
                'small': 'pitcher_dominance',     # 80% win rate
                'medium': 'projection_monster',   # 72% win rate  
                'large': 'projection_monster'     # 74% win rate
            },
            'gpp': {
                'small': 'tournament_winner_gpp',
                'medium': 'tournament_winner_gpp', 
                'large': 'correlation_value'
            }
        }
        
    def convert_sim_players_to_your_format(self, sim_players: List) -> List[Player]:
        """Convert simulation players to your Player format"""
        your_players = []
        
        for sim_player in sim_players:
            # Create Player object with your exact format
            # Ensure salary is never 0 to prevent division by zero
            salary = max(sim_player.salary, 2500)  # Minimum $2500 salary

            player = Player(
                name=sim_player.name,
                position=sim_player.position,
                team=sim_player.team,
                salary=salary,
                projection=sim_player.projection
            )
            
            # Set additional attributes that your strategies use (ALL SIMULATED)
            player.confirmed = True  # Assume all sim players are confirmed
            player.k_rate = getattr(sim_player, 'k_rate', 8.0)
            player.implied_team_score = getattr(sim_player, 'team_total', 4.5)
            player.ownership = getattr(sim_player, 'ownership', 15.0)
            player.consistency_score = getattr(sim_player, 'consistency_score', 50.0)
            player.batting_order = getattr(sim_player, 'batting_order', 5)

            # Set all other attributes to simulated defaults (no real data)
            player.barrel_rate = getattr(sim_player, 'barrel_rate', 8.5)
            player.xwoba = 0.320  # Simulated default
            player.hard_hit_rate = 40.0  # Simulated default
            player.avg_exit_velo = 88.0  # Simulated default
            player.era = 4.00  # Simulated default
            player.whip = 1.30  # Simulated default
            player.recent_form = 1.0  # Simulated default
            player.weather_score = 1.0  # Simulated default
            player.park_factor = 1.0  # Simulated default

            # Add attributes for your DFS insights
            player.hr_rate = getattr(sim_player, 'hr_rate', 0.03)  # HR rate for power targeting
            player.win_probability = getattr(sim_player, 'win_probability', 0.5)  # Win prob for pitchers
            
            your_players.append(player)
            
        return your_players
    
    def generate_your_lineup(self, slate_players: List, strategy_name: str, 
                           contest_type: str) -> Optional[List]:
        """Generate lineup using your exact optimizer and strategy"""
        try:
            # Convert simulation players to your format
            your_players = self.convert_sim_players_to_your_format(slate_players)

            # Validate and fix all players have valid salaries and projections
            for player in your_players:
                if player.salary <= 0:
                    player.salary = 2500  # Fix invalid salary
                if player.projection <= 0:
                    player.projection = 5.0  # Fix invalid projection
                if not hasattr(player, 'optimization_score'):
                    player.optimization_score = player.projection

            # Load into your pipeline
            self.pipeline.all_players = your_players
            self.pipeline.num_games = len(set(p.team for p in your_players)) // 2

            # Build player pool (use all players for simulation)
            self.pipeline.build_player_pool(confirmed_only=False)

            # Apply your exact strategy with error handling
            try:
                self.strategy_manager.apply_strategy(self.pipeline.player_pool, strategy_name)
            except Exception as e:
                # If strategy fails, continue with base optimization scores
                print(f"Strategy application failed: {e}")
                for player in self.pipeline.player_pool:
                    if not hasattr(player, 'optimization_score'):
                        player.optimization_score = player.projection

            # Use SIMULATION MODE (no real API calls - all simulated data)
            # Skip enrichment entirely to avoid any real data calls
            # All player attributes are already set to simulated values above

            # Apply your scoring engine (uses only simulated player attributes)
            self.pipeline.score_players(contest_type)

            # Generate lineup using your MILP optimizer
            lineups = self.pipeline.optimize_lineups(contest_type, 1)
            
            if lineups and len(lineups) > 0:
                # Convert back to simulation format
                lineup_players = []
                for player in lineups[0]['players']:
                    # Find corresponding sim player
                    for sim_player in slate_players:
                        if (sim_player.name == player.name and 
                            sim_player.position == player.position):
                            lineup_players.append(sim_player)
                            break
                
                return lineup_players
            
            return None
            
        except Exception as e:
            print(f"Error generating lineup with {strategy_name}: {e}")
            return None
    
    def run_strategy_test(self, strategy_name: str, contest_type: str, 
                         slate_size: str, num_simulations: int = 1000) -> Dict:
        """Test a single strategy across multiple simulations"""
        
        print(f"\n🎯 Testing {strategy_name} ({contest_type}, {slate_size} slate)")
        print(f"   Running {num_simulations} simulations...")
        
        # Determine number of games based on slate size
        if slate_size == 'small':
            num_games = 4
        elif slate_size == 'medium':
            num_games = 8
        else:  # large
            num_games = 12
            
        # Determine field size based on contest type
        if contest_type == 'cash':
            field_size = 20  # Smaller cash games
        else:
            field_size = 100  # Larger GPP fields
        
        results = []
        successful_sims = 0
        
        for sim_id in range(num_simulations):
            if sim_id % 100 == 0:
                print(f"   Progress: {sim_id}/{num_simulations}")
            
            try:
                # Generate realistic slate
                slate = generate_realistic_slate(num_games, sim_id)
                
                # Generate your lineup using exact strategy
                your_lineup = self.generate_your_lineup(
                    slate['players'], strategy_name, contest_type
                )
                
                if your_lineup and len(your_lineup) == 10:
                    # Run simulation
                    args = (sim_id, num_games, contest_type, strategy_name, 
                           your_lineup, field_size)
                    result = process_single_simulation(args)
                    results.append(result)
                    successful_sims += 1
                    
            except Exception as e:
                print(f"   Simulation {sim_id} failed: {e}")
                continue
        
        print(f"   Completed: {successful_sims}/{num_simulations} successful simulations")
        
        # Analyze results
        if results:
            scores = [r['your_score'] for r in results]
            ranks = [r['your_rank'] for r in results]
            wins = [r['won'] for r in results]
            rois = [r['roi'] for r in results]
            
            analysis = {
                'strategy': strategy_name,
                'contest_type': contest_type,
                'slate_size': slate_size,
                'simulations': len(results),
                'avg_score': np.mean(scores),
                'avg_rank': np.mean(ranks),
                'win_rate': np.mean(wins) * 100,
                'avg_roi': np.mean(rois) * 100,
                'score_std': np.std(scores),
                'top_10_rate': sum(1 for r in ranks if r <= 10) / len(ranks) * 100,
                'top_25_rate': sum(1 for r in ranks if r <= 25) / len(ranks) * 100,
                'median_rank': np.median(ranks),
                'best_score': max(scores),
                'worst_score': min(scores)
            }
            
            return analysis
        
        return None
    
    def run_tournament(self, contest_types: List[str] = ['cash', 'gpp'],
                      slate_sizes: List[str] = ['small', 'medium', 'large'],
                      num_simulations: int = 1000) -> Dict:
        """Run complete tournament across all strategy combinations"""
        
        print("\n" + "=" * 60)
        print("🏆 STRATEGY TOURNAMENT")
        print("Testing your exact strategies against realistic competition")
        print("=" * 60)
        
        tournament_results = {}
        
        for contest_type in contest_types:
            tournament_results[contest_type] = {}
            
            for slate_size in slate_sizes:
                # Get your strategy for this combination
                strategy_name = self.your_strategies[contest_type][slate_size]
                
                # Test the strategy
                result = self.run_strategy_test(
                    strategy_name, contest_type, slate_size, num_simulations
                )
                
                if result:
                    tournament_results[contest_type][slate_size] = result
                    
                    # Print immediate results
                    print(f"\n📊 {strategy_name} ({contest_type}, {slate_size}):")
                    print(f"   Win Rate: {result['win_rate']:.1f}%")
                    print(f"   Avg ROI: {result['avg_roi']:+.1f}%")
                    print(f"   Avg Score: {result['avg_score']:.1f}")
                    print(f"   Avg Rank: {result['avg_rank']:.1f}")
                    print(f"   Top 10%: {result['top_10_rate']:.1f}%")
        
        return tournament_results
    
    def save_results(self, results: Dict, filename: str = None):
        """Save tournament results to JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation/tournament_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")
        
    def print_tournament_summary(self, results: Dict):
        """Print comprehensive tournament summary"""
        
        print("\n" + "=" * 80)
        print("🏆 TOURNAMENT RESULTS SUMMARY")
        print("=" * 80)
        
        for contest_type in ['cash', 'gpp']:
            if contest_type in results:
                print(f"\n📈 {contest_type.upper()} RESULTS:")
                print("-" * 50)
                
                for slate_size in ['small', 'medium', 'large']:
                    if slate_size in results[contest_type]:
                        r = results[contest_type][slate_size]
                        
                        print(f"\n{slate_size.title()} Slate - {r['strategy']}:")
                        print(f"  Win Rate: {r['win_rate']:.1f}% (Target: 70%+)")
                        print(f"  ROI: {r['avg_roi']:+.1f}% (Target: +20%+)")
                        print(f"  Avg Score: {r['avg_score']:.1f} ± {r['score_std']:.1f}")
                        print(f"  Avg Rank: {r['avg_rank']:.1f} / {r.get('field_size', 100)}")
                        print(f"  Top 10%: {r['top_10_rate']:.1f}%")
                        print(f"  Simulations: {r['simulations']:,}")
                        
                        # Performance assessment
                        if contest_type == 'cash':
                            if r['win_rate'] >= 70:
                                print("  ✅ EXCELLENT performance")
                            elif r['win_rate'] >= 60:
                                print("  ✅ GOOD performance") 
                            elif r['win_rate'] >= 50:
                                print("  ⚠️ AVERAGE performance")
                            else:
                                print("  ❌ POOR performance")
                        else:  # GPP
                            if r['top_10_rate'] >= 15:
                                print("  ✅ EXCELLENT GPP performance")
                            elif r['top_10_rate'] >= 10:
                                print("  ✅ GOOD GPP performance")
                            elif r['top_10_rate'] >= 5:
                                print("  ⚠️ AVERAGE GPP performance") 
                            else:
                                print("  ❌ POOR GPP performance")


if __name__ == "__main__":
    # Quick test
    tournament = StrategyTournament()
    print("✅ Strategy Tournament framework loaded!")
    print(f"Your strategies: {tournament.your_strategies}")
