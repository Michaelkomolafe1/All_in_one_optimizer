#!/usr/bin/env python3
"""
UNIFIED CORE SYSTEM V2
=====================
Clean rewrite using only the enhanced scoring engine
No old dependencies, no complex configurations
"""

import logging
from typing import List, Dict, Set, Optional
from pathlib import Path

# Core components
from unified_player_model import UnifiedPlayer
from unified_milp_optimizer import UnifiedMILPOptimizer
from enhanced_scoring_engine import EnhancedScoringEngine

# Data sources (all in data/ directory)
import sys
sys.path.append(str(Path(__file__).parent.parent))

from data.simple_statcast_fetcher import SimpleStatcastFetcher
from data.smart_confirmation_system import SmartConfirmationSystem
from data.vegas_lines import VegasLines
from data.ownership_calculator import OwnershipCalculator

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UnifiedCoreSystemV2:
    """
    Simplified DFS optimization system
    Uses ONLY the enhanced scoring engine for ALL contest types
    """
    
    def __init__(self):
        """Initialize with only what we need"""
        logger.info("🚀 Initializing Unified Core System V2...")
        
        # Player pools
        self.all_players: List[UnifiedPlayer] = []
        self.player_pool: List[UnifiedPlayer] = []
        
        # Core components
        self.scoring_engine = EnhancedScoringEngine()
        self.optimizer = UnifiedMILPOptimizer()
        
        # Data sources
        self.statcast = SimpleStatcastFetcher()
        self.confirmation = SmartConfirmationSystem()
        self.vegas = VegasLines()
        self.ownership_calc = OwnershipCalculator()
        
        logger.info("✅ System initialized with Enhanced Scoring Engine")
    
    def load_players_from_csv(self, csv_path: str, source: str = "dk"):
        """Load players from DraftKings/FanDuel CSV"""
        logger.info(f"📁 Loading players from {csv_path}")
        
        # This would use your existing CSV loading logic
        # For now, return empty list
        self.all_players = []
        return len(self.all_players)
    
    def set_player_pool(self, 
                       strategy: str = "all",
                       confirmed_only: bool = False,
                       include_doubtful: bool = False) -> int:
        """Set player pool based on strategy"""
        if strategy == "confirmed_only":
            self.player_pool = [p for p in self.all_players if p.is_confirmed]
        else:
            self.player_pool = self.all_players.copy()
            
        logger.info(f"📋 Player pool set: {len(self.player_pool)} players")
        return len(self.player_pool)
    
    def enrich_player_pool(self) -> int:
        """Enrich players with all data sources"""
        logger.info("🔄 Enriching player pool...")
        enriched = 0
        
        for player in self.player_pool:
            try:
                # 1. Get Vegas data
                vegas_data = self.vegas.get_player_vegas_data(player)
                if vegas_data:
                    player.implied_team_score = vegas_data.get('total', 4.5)
                    enriched += 1
                
                # 2. Get confirmation/batting order
                conf_data = self.confirmation.check_player_confirmation(player.name)
                if conf_data:
                    player.is_confirmed = conf_data.get('confirmed', False)
                    player.batting_order = conf_data.get('batting_order')
                
                # 3. Get recent performance
                if player.primary_position != 'P':
                    game_logs = self.statcast.fetch_recent_game_logs(player.name, 4)
                    if game_logs:
                        player.recent_game_logs = game_logs
                        player.recent_form_score = self.statcast.calculate_recent_form_score(game_logs)
                
                # 4. Get pitcher stats
                if player.primary_position == 'P':
                    pitcher_stats = self.statcast.fetch_pitcher_advanced_stats(player.name)
                    if pitcher_stats:
                        player.era = pitcher_stats.get('era', 4.50)
                        player.k9 = pitcher_stats.get('k9', 8.0)
                        player.whiff_rate = pitcher_stats.get('whiff_rate', 25.0)
                
                # 5. Calculate ownership
                player.projected_ownership = self.ownership_calc.calculate_ownership(player)
                player.ownership_leverage = self.ownership_calc.calculate_leverage_score(player)
                
            except Exception as e:
                logger.debug(f"Error enriching {player.name}: {e}")
                continue
        
        logger.info(f"✅ Enriched {enriched} players")
        return enriched
    
    def optimize_lineups(self, 
                        num_lineups: int = 20,
                        contest_type: str = "gpp") -> List[List[UnifiedPlayer]]:
        """
        Generate optimized lineups using enhanced scoring
        """
        logger.info(f"\n🎯 OPTIMIZING {num_lineups} {contest_type.upper()} LINEUPS")
        logger.info(f"{'='*60}")
        
        # 1. Score all players with enhanced engine
        logger.info("📊 Scoring players...")
        for player in self.player_pool:
            player.enhanced_score = self.scoring_engine.score_player(player, contest_type)
            
            # Store contest-specific scores
            player.gpp_score = self.scoring_engine.score_player_gpp(player)
            player.cash_score = self.scoring_engine.score_player_cash(player)
        
        # Show top scorers
        top_players = sorted(self.player_pool, key=lambda x: x.enhanced_score, reverse=True)[:5]
        logger.info("🌟 Top 5 Players:")
        for p in top_players:
            logger.info(f"   {p.name:<20} ${p.salary:<6} Score: {p.enhanced_score:.2f}")
        
        # 2. Set up optimization config
        config = {
            'stack_min': 3 if contest_type == 'gpp' else 0,
            'stack_max': 5 if contest_type == 'gpp' else 2,
            'max_exposure': 0.6 if contest_type == 'gpp' else 0.8,
            'min_salary': 48000,
            'max_salary': 50000
        }
        
        # 3. Generate lineups
        lineups = []
        for i in range(num_lineups):
            # Use MILP optimizer
            lineup = self.optimizer.optimize_single_lineup(
                self.player_pool,
                excluded_players=set(),  # Track used players if needed
                config=config
            )
            
            if lineup:
                lineups.append(lineup)
                logger.info(f"   Lineup {i+1}: {sum(p.salary for p in lineup)} salary, "
                          f"{sum(p.enhanced_score for p in lineup):.2f} points")
            else:
                logger.warning(f"   Failed to generate lineup {i+1}")
        
        logger.info(f"\n✅ Generated {len(lineups)} lineups")
        return lineups
    
    def display_lineup(self, lineup: List[UnifiedPlayer], contest_type: str = "gpp"):
        """Display a single lineup with scores"""
        total_salary = sum(p.salary for p in lineup)
        total_score = sum(p.enhanced_score for p in lineup)
        
        print(f"\n{'='*60}")
        print(f"LINEUP - {contest_type.upper()} - Salary: ${total_salary} - Proj: {total_score:.2f}")
        print(f"{'='*60}")
        print(f"{'Pos':<4} {'Player':<20} {'Team':<5} {'Salary':<7} {'Score':<7} {'Own%':<6}")
        print(f"{'-'*60}")
        
        for player in sorted(lineup, key=lambda x: ['P', 'C', '1B', '2B', '3B', 'SS', 'OF'].index(x.primary_position)):
            print(f"{player.primary_position:<4} {player.name:<20} {player.team:<5} "
                  f"${player.salary:<6} {player.enhanced_score:<7.2f} "
                  f"{getattr(player, 'projected_ownership', 0):<5.1f}%")


if __name__ == "__main__":
    # Test the system
    system = UnifiedCoreSystemV2()
    print("✅ Unified Core System V2 ready!")
    print("\n🎯 This system uses ONLY the enhanced scoring engine")
    print("   - GPP: Optimized parameters (-67.7 score)")
    print("   - Cash: Optimized parameters (86.2 score)")
    print("   - No complex configurations needed!")
