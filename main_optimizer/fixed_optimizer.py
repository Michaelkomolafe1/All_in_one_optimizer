#!/usr/bin/env python3
"""Fixed optimizer with projection loading and contest type support"""

import pandas as pd
from unified_core_system import UnifiedCoreSystem
from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig

class FixedOptimizer:
    def __init__(self):
        self.system = UnifiedCoreSystem()
        self.optimizer = UnifiedMILPOptimizer(OptimizationConfig())
        
    def load_and_fix_projections(self, csv_path):
        """Load CSV and fix projections"""
        # Load players
        self.system.load_players_from_csv(csv_path)
        
        # Fix projections from CSV
        df = pd.read_csv(csv_path)
        for player in self.system.players:
            matching = df[df['Name'] == player.name]
            if not matching.empty:
                player.base_projection = float(matching.iloc[0].get('AvgPointsPerGame', 0))
                
        print(f"✅ Fixed projections for {len(self.system.players)} players")
        
    def build_enhanced_pool(self, include_unconfirmed=True):
        """Build pool with all enhancements"""
        # Build pool
        self.system.build_player_pool(include_unconfirmed=include_unconfirmed)
        
        # Apply ALL enhancements
        print("🎯 Applying enhancements...")
        self.system.enrich_player_pool()
        
        # Verify enhancements
        enhanced_count = 0
        for p in self.system.player_pool:
            has_enhancements = any([
                hasattr(p, 'park_factor') and p.park_factor and p.park_factor != 1.0,
                hasattr(p, 'implied_team_score') and p.implied_team_score and p.implied_team_score > 0,
                hasattr(p, 'batting_order') and p.batting_order and p.batting_order > 0,
                hasattr(p, 'recent_performance') and p.recent_performance is not None
            ])
            if has_enhancements:
                enhanced_count += 1
                
        print(f"✅ Enhanced {enhanced_count}/{len(self.system.player_pool)} players")
        
        # Show sample
        if self.system.player_pool:
            p = self.system.player_pool[0]
            print(f"\n📊 Sample player enhancements for {p.name}:")
            print(f"  Base projection: {p.base_projection}")
            print(f"  Park factor: {getattr(p, 'park_factor', 'Not set')}")
            print(f"  Vegas total: {getattr(p, 'implied_team_score', 'Not set')}")
            print(f"  Batting order: {getattr(p, 'batting_order', 'Not set')}")
            
    def optimize_with_contest_type(self, contest_type='gpp', strategy=None, num_lineups=1):
        """Optimize with proper contest type handling"""
        # Score players for contest type
        self.system.score_players(contest_type)
        
        # Set contest type in optimizer config
        self.optimizer.config.contest_type = contest_type
        
        # Get strategy if not provided
        if not strategy:
            from strategy_selector import StrategyAutoSelector
            selector = StrategyAutoSelector()
            slate_size = 'medium'  # You can calculate this properly
            strategy = selector.top_strategies[contest_type][slate_size]
            
        print(f"\n🎯 Optimizing {contest_type.upper()} with {strategy}...")
        
        # Call optimize WITHOUT contest_type parameter
        # The optimizer will use self.optimizer.config.contest_type
        results = []
        for i in range(num_lineups):
            result = self.optimizer.optimize(
                players=self.system.player_pool,
                strategy=strategy,
                manual_selections=[]
            )
            if result:
                results.append(result)
                
        return results

# Test it
if __name__ == "__main__":
    optimizer = FixedOptimizer()
    
    # Load and fix
    optimizer.load_and_fix_projections("/home/michael/Downloads/DKSalaries(34).csv")
    
    # Build enhanced pool
    optimizer.build_enhanced_pool()
    
    # Test both contest types
    print("\n=== CASH TEST ===")
    cash_results = optimizer.optimize_with_contest_type('cash', num_lineups=1)
    
    print("\n=== GPP TEST ===")
    gpp_results = optimizer.optimize_with_contest_type('gpp', num_lineups=1)
    
    if cash_results:
        print("\n✅ Cash optimization working!")
    if gpp_results:
        print("\n✅ GPP optimization working!")
