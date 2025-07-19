#!/usr/bin/env python3
"""
ADVANCED DFS CORE
=================
Complete DFS optimization system with advanced analytics
"""

# Standard imports
import csv
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Core imports
from unified_player_model import UnifiedPlayer
from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig

# Import scoring engine
from advanced_scoring_engine import AdvancedScoringEngine, AdvancedScoringConfig

# Import data pipeline
from pure_data_pipeline import create_pure_data_pipeline

# Data source imports
from simple_statcast_fetcher import FastStatcastFetcher
from smart_confirmation_system import SmartConfirmationSystem
from vegas_lines import VegasLines

logger = logging.getLogger(__name__)


class AdvancedDFSCore:
    """
    Complete DFS optimization system with advanced analytics
    Pure data-driven approach with zero fallbacks
    """

    def __init__(self, mode: str = "production"):
        """
        Initialize the advanced DFS core

        Args:
            mode: 'production' for live data, 'test' for testing
        """
        self.mode = mode
        self.players: List[UnifiedPlayer] = []
        self.optimization_mode = "all"
        self.salary_cap = 50000

        # Initialize components
        self._initialize_components()

        # System state
        self.last_optimization_result = None
        self.system_stats = {
            'csv_loads': 0,
            'optimizations_run': 0,
            'data_enrichments': 0,
            'last_update': None
        }

        logger.info(f"Advanced DFS Core initialized in {mode} mode")

    def _initialize_components(self):
        """Initialize all system components"""
        print("\n🚀 INITIALIZING ADVANCED DFS CORE")
        print("=" * 60)

        # 1. Advanced Scoring Engine - CREATE INSTANCE DIRECTLY
        scoring_config = AdvancedScoringConfig()
        self.scoring_engine = AdvancedScoringEngine(scoring_config)
        print("✅ Advanced Scoring Engine loaded (80+ metrics)")

        # Rest of initialization continues...

        # 2. Pure Data Pipeline
        self.data_pipeline = create_pure_data_pipeline(max_workers=10)
        print("✅ Pure Data Pipeline initialized")

        # 3. Data Sources
        self.statcast_fetcher = FastStatcastFetcher(max_workers=5)
        self.confirmation_system = SmartConfirmationSystem(verbose=False)
        self.vegas_client = VegasLines(cache_ttl=300)

        # Connect data sources
        self.data_pipeline.set_data_sources(
            statcast_fetcher=self.statcast_fetcher,
            confirmation_system=self.confirmation_system,
            vegas_client=self.vegas_client
        )

        self.scoring_engine.set_data_sources(
            statcast_fetcher=self.statcast_fetcher,
            vegas_client=self.vegas_client,
            confirmation_system=self.confirmation_system
        )

        print("✅ Data sources connected")

        # 4. MILP Optimizer
        optimizer_config = OptimizationConfig(
            salary_cap=self.salary_cap,
            min_salary_usage=0.95,
            max_players_per_team=4,
            use_correlation=True
        )
        self.optimizer = UnifiedMILPOptimizer(optimizer_config)
        print("✅ MILP Optimizer configured")

        print("=" * 60)
        print("✅ SYSTEM READY - Pure data approach, no fallbacks\n")

    def load_draftkings_csv(self, filepath: str) -> int:
        """
        Load DraftKings CSV and create UnifiedPlayer objects

        Returns:
            Number of players loaded
        """
        print(f"\n📄 Loading DraftKings CSV: {filepath}")

        self.players.clear()
        loaded_count = 0

        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    try:
                        # Create UnifiedPlayer
                        player = UnifiedPlayer(
                            id=row.get('ID', f"{row.get('Name', 'Unknown')}_{loaded_count}"),
                            name=row.get('Name', '').strip(),
                            team=row.get('TeamAbbrev', '').strip().upper(),
                            salary=int(row.get('Salary', 0)),
                            primary_position=row.get('Position', '').strip().upper(),
                            positions=row.get('Position', '').strip().upper().split('/'),
                            base_projection=float(row.get('AvgPointsPerGame', 0))
                        )

                        # Additional fields from CSV
                        player.game_info = row.get('Game Info', '')
                        player.roster_position = row.get('Roster Position', '')

                        # Validate minimum requirements
                        if player.salary > 0 and player.name and player.primary_position:
                            self.players.append(player)
                            loaded_count += 1

                    except Exception as e:
                        logger.debug(f"Failed to parse player row: {e}")
                        continue

            # Update stats
            self.system_stats['csv_loads'] += 1
            self.system_stats['last_update'] = datetime.now()

            print(f"✅ Loaded {loaded_count} players from CSV")

            # Quick summary by position
            position_counts = {}
            for p in self.players:
                position_counts[p.primary_position] = position_counts.get(p.primary_position, 0) + 1

            print("\nPosition breakdown:")
            for pos, count in sorted(position_counts.items()):
                print(f"  {pos}: {count}")

            return loaded_count

        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            print(f"❌ Error loading CSV: {e}")
            return 0

    def enrich_player_data(self) -> int:
        """
        Enrich all players with real-time data
        Uses pure data pipeline with no fallbacks

        Returns:
            Number of players enriched
        """
        if not self.players:
            print("❌ No players loaded")
            return 0

        print(f"\n🔄 Enriching {len(self.players)} players with real data...")

        # Run enrichment pipeline
        enriched_players, stats = self.data_pipeline.enrich_players_parallel(self.players)

        # Update system stats
        self.system_stats['data_enrichments'] += 1

        # Calculate scores using advanced engine
        print("\n💯 Calculating advanced scores...")
        scored_count = 0

        for player in self.players:
            try:
                # Calculate advanced score
                score = self.scoring_engine.calculate_score(player)
                player.enhanced_score = score
                player.optimization_score = score  # For optimizer

                if score > 0:
                    scored_count += 1

                    # Log high-value players
                    if score > player.base_projection * 1.15:
                        print(
                            f"   📈 {player.name}: {score:.1f} pts (+{(score / player.base_projection - 1) * 100:.0f}%)")

            except Exception as e:
                logger.debug(f"Failed to score {player.name}: {e}")
                player.enhanced_score = 0
                player.optimization_score = 0

        print(f"\n✅ Scored {scored_count} players with advanced analytics")

        return stats['enriched_count']

    def set_optimization_mode(self, mode: str):
        """Set optimization strategy mode"""
        valid_modes = ['all', 'confirmed_only', 'manual_only', 'confirmed_plus_manual', 'balanced']

        if mode in valid_modes:
            self.optimization_mode = mode
            print(f"✅ Optimization mode set to: {mode}")
        else:
            print(f"❌ Invalid mode. Valid modes: {valid_modes}")

    def optimize_lineup(self, manual_selections: str = "") -> Tuple[List[UnifiedPlayer], float]:
        """
        Run advanced lineup optimization

        Args:
            manual_selections: Comma-separated player names to force include

        Returns:
            (lineup, total_score)
        """
        print(f"\n🎯 RUNNING ADVANCED OPTIMIZATION")
        print(f"Mode: {self.optimization_mode}")
        print("=" * 60)

        # Ensure data is enriched
        eligible_players = [p for p in self.players if p.enhanced_score > 0]

        if len(eligible_players) < 10:
            print(f"❌ Not enough scored players: {len(eligible_players)}")
            print("   Run enrich_player_data() first")
            return [], 0

        # Map optimization mode to strategy
        strategy_map = {
            'all': 'all_players',
            'confirmed_only': 'confirmed_only',
            'manual_only': 'manual_only',
            'confirmed_plus_manual': 'confirmed_plus_manual',
            'balanced': 'balanced'
        }

        strategy = strategy_map.get(self.optimization_mode, 'all_players')

        # Run optimization
        start_time = datetime.now()
        lineup, score = self.optimizer.optimize_lineup(
            self.players,
            strategy=strategy,
            manual_selections=manual_selections
        )

        optimization_time = (datetime.now() - start_time).seconds

        if lineup:
            print(f"\n✅ OPTIMIZATION SUCCESSFUL!")
            print(f"⏱️  Time: {optimization_time}s")
            print(f"💰 Salary: ${sum(p.salary for p in lineup):,} / ${self.salary_cap:,}")
            print(f"📈 Score: {score:.2f} points")

            # Show lineup
            print("\n📋 OPTIMAL LINEUP:")
            print("-" * 70)
            print(f"{'Pos':>3} {'Player':<20} {'Team':>4} {'Salary':>7} {'Base':>6} {'Score':>6} {'Δ':>5}")
            print("-" * 70)

            for player in lineup:
                delta = ((player.enhanced_score / player.base_projection - 1) * 100
                         if player.base_projection > 0 else 0)

                # Mark confirmed/manual
                marker = ""
                if getattr(player, 'is_confirmed', False):
                    marker = "✓"
                if getattr(player, 'is_manual_selected', False):
                    marker = "M"

                print(f"{player.primary_position:>3} {player.name:<20} "
                      f"{player.team:>4} ${player.salary:>6,} "
                      f"{player.base_projection:>6.1f} {player.enhanced_score:>6.1f} "
                      f"{delta:>+5.0f}% {marker}")

            # Show score breakdown for best player
            best_player = max(lineup, key=lambda p: p.enhanced_score)
            print(f"\n🌟 Top Performer: {best_player.name}")
            breakdown = self.scoring_engine.get_score_breakdown(best_player)
            print(f"   Base: {breakdown['base_projection']:.1f}")
            for component, value in breakdown['components'].items():
                if value != breakdown['base_projection']:
                    print(f"   {component.title()}: {value:.1f}")

            # Update stats
            self.system_stats['optimizations_run'] += 1
            self.last_optimization_result = {
                'lineup': lineup,
                'score': score,
                'timestamp': datetime.now(),
                'mode': self.optimization_mode,
                'strategy': strategy
            }

        else:
            print("❌ Optimization failed - no valid lineup found")
            print("   Try different settings or check player pool")

        return lineup, score

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'core_initialized': True,
            'mode': self.mode,
            'players_loaded': len(self.players),
            'players_scored': sum(1 for p in self.players if getattr(p, 'enhanced_score', 0) > 0),
            'confirmed_players': sum(1 for p in self.players if getattr(p, 'is_confirmed', False)),
            'modules': {
                'scoring_engine': self.scoring_engine is not None,
                'data_pipeline': self.data_pipeline is not None,
                'optimizer': self.optimizer is not None,
                'statcast': self.statcast_fetcher is not None,
                'confirmations': self.confirmation_system is not None,
                'vegas': self.vegas_client is not None
            },
            'stats': self.system_stats,
            'optimization_ready': len(self.players) > 0 and any(p.enhanced_score > 0 for p in self.players)
        }

        return status

    def export_lineup(self, lineup: List[UnifiedPlayer], filepath: str = None) -> str:
        """Export lineup to CSV"""
        if not lineup:
            print("❌ No lineup to export")
            return ""

        if not filepath:
            filepath = f"lineup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Position', 'Player', 'Team', 'Salary', 'Projection', 'Score', 'Value'])

                for player in lineup:
                    writer.writerow([
                        player.primary_position,
                        player.name,
                        player.team,
                        player.salary,
                        player.base_projection,
                        player.enhanced_score,
                        player.enhanced_score / player.salary * 1000
                    ])

            print(f"✅ Lineup exported to: {filepath}")
            return filepath

        except Exception as e:
            print(f"❌ Export failed: {e}")
            return ""


# Convenience functions for backward compatibility
def create_advanced_dfs_core() -> AdvancedDFSCore:
    """Create production instance"""
    return AdvancedDFSCore(mode="production")


# Make it work as drop-in replacement
BulletproofDFSCore = AdvancedDFSCore

if __name__ == "__main__":
    print("✅ Advanced DFS Core System")
    print("\n📊 Features:")
    print("  - 80+ Baseball Savant metrics")
    print("  - Pure data approach (no fallbacks)")
    print("  - Advanced scoring algorithms")
    print("  - Parallel data enrichment")
    print("  - Confirmed lineup integration")
    print("  - Vegas lines integration")
    print("  - MILP optimization")
    print("\n🚀 Ready for production use!")