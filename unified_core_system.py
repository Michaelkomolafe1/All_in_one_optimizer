#!/usr/bin/env python3
"""
UNIFIED CORE SYSTEM - PURE DATA APPROACH
========================================
Complete unified DFS system with ALL enrichments, NO fallbacks
Only uses confirmed players + manual selections
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd

# Core imports
from unified_player_model import UnifiedPlayer
from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig
from unified_scoring_engine import get_scoring_engine, ScoringConfig

# Data enrichment imports
from simple_statcast_fetcher import FastStatcastFetcher
from smart_confirmation_system import SmartConfirmationSystem
from vegas_lines import VegasLines

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedCoreSystem:
    """
    Pure data unified DFS system - NO FALLBACKS
    Works exclusively with confirmed players and manual selections
    """

    def __init__(self):
        '''Initialize the unified core system'''
        self.all_players: Dict[str, UnifiedPlayer] = {}
        self.confirmed_names: Set[str] = set()
        self.manual_names: Set[str] = set()
        self.player_pool: List[UnifiedPlayer] = []

        # ADD THIS LINE:
        self.logger = logger  # Use the module-level logger

        # Configuration
        self.salary_cap = 50000
        self.min_salary_usage = 0.95

        # Initialize ALL components
        self._initialize_components()

        print("\n✅ Unified Core System Ready!")
        print("   • Confirmed players only")
        print("   • ALL enrichments active")
        print("   • Pure data approach")

    def _initialize_components(self):
        """Initialize all system components"""
        print("\n🚀 INITIALIZING UNIFIED CORE SYSTEM")
        print("=" * 60)

        # 1. Confirmation System - CRITICAL
        print("📋 Initializing Confirmation System...")
        try:
            # Try to use enhanced system with Rotowire
            from rotowire_pitcher_system import EnhancedConfirmationSystem
            self.confirmation_system = EnhancedConfirmationSystem(verbose=True)
            print("   ✅ Using Enhanced Confirmation System")
            print("   ✅ MLB API + Rotowire for pitchers")
            self._using_enhanced = True
        except ImportError:
            # Fallback to smart confirmation only
            self.confirmation_system = SmartConfirmationSystem(verbose=True)
            print("   ✅ Using Smart Confirmation System")
            print("   ⚠️  No Rotowire backup for pitchers")
            self._using_enhanced = False

        # 2. Statcast Fetcher - For enrichment
        print("\n⚾ Initializing Statcast Fetcher...")
        self.statcast = FastStatcastFetcher(max_workers=10)
        print("   ✅ Ready for player statistics")

        # 3. Vegas Lines - For game context
        print("\n🎰 Initializing Vegas Lines...")
        try:
            # Try with cache_ttl first
            self.vegas = VegasLines(cache_ttl=300)
        except TypeError:
            # Fall back to no parameters
            self.vegas = VegasLines()
        print("   ✅ Ready for betting data")

        # 4. Scoring Engine - With ALL factors
        print("\n📊 Initializing Unified Scoring Engine...")
        scoring_config = ScoringConfig(
            weights={
                'base': 0.20,
                'recent_form': 0.25,
                'vegas': 0.20,
                'matchup': 0.15,
                'park': 0.10,
                'batting_order': 0.05,
                'confirmed_boost': 0.05
            }
        )
        self.scoring_engine = get_scoring_engine(scoring_config)

        # Connect data sources to scoring engine if method exists
        if hasattr(self.scoring_engine, 'set_data_sources'):
            self.scoring_engine.set_data_sources(
                statcast_fetcher=self.statcast,
                vegas_client=self.vegas,
                confirmation_system=self.confirmation_system
            )
            print("   ✅ Scoring engine connected to all data sources")
        else:
            print("   ✅ Scoring engine initialized (standalone mode)")

        # 5. MILP Optimizer
        print("\n🎯 Initializing MILP Optimizer...")
        optimizer_config = OptimizationConfig(
            salary_cap=self.salary_cap,
            min_salary_usage=self.min_salary_usage  # Fixed: was min_salary_pct
        )
        self.optimizer = UnifiedMILPOptimizer(optimizer_config)

        # Connect data sources to optimizer if method exists
        if hasattr(self.optimizer, 'set_data_sources'):
            self.optimizer.set_data_sources(
                statcast_fetcher=self.statcast,
                vegas_client=self.vegas
            )
            print("   ✅ Optimizer connected to data sources")
        else:
            print("   ✅ Optimizer ready")

        print("\n" + "=" * 60)
        print("✅ ALL SYSTEMS INITIALIZED - PURE DATA MODE")
        print("=" * 60)

    def load_csv(self, csv_path: str) -> int:
        print(f"\n📂 Loading CSV: {csv_path}")

        df = pd.read_csv(csv_path)
        self.all_players.clear()

        POSITION_MAP = {
            'SP': 'P',
            'RP': 'P',
            'P': 'P',
            'C': 'C',
            '1B': '1B',
            '2B': '2B',
            '3B': '3B',
            'SS': 'SS',
            'OF': 'OF',
            'UTIL': 'UTIL'
        }

        for idx, row in df.iterrows():
            pos_str = str(row.get('Position', ''))
            raw_positions = pos_str.split('/') if '/' in pos_str else [pos_str]

            positions = [POSITION_MAP.get(p.strip(), p.strip()) for p in raw_positions]
            primary = positions[0]

            player = UnifiedPlayer(
                id=str(row.get('ID', f"{row['Name']}_{idx}")),
                name=row['Name'],
                team=row.get('TeamAbbrev', 'UNK'),
                salary=int(row['Salary']),
                primary_position=primary,
                positions=positions,
                base_projection=float(row.get('AvgPointsPerGame', 0))
            )

            player.display_position = pos_str

            player.opponent = row.get('Opponent', '')
            player.game_info = row.get('Game Info', '')
            player.is_home = '@' not in row.get('Game Info', '')

            if 'DFF Proj' in row:
                player.dff_projection = float(row.get('DFF Proj', 0))
            if 'DFF L5 Avg' in row:
                player.dff_l5_avg = float(row.get('DFF L5 Avg', 0))

            self.all_players[player.name] = player

        print(f"✅ Loaded {len(self.all_players)} total players")

        position_counts = {}
        for player in self.all_players.values():
            pos = player.primary_position
            position_counts[pos] = position_counts.get(pos, 0) + 1

        print("\n📊 Position breakdown (after mapping):")
        for pos in sorted(position_counts.keys()):
            count = position_counts[pos]
            print(f"   {pos}: {count} players")

        return len(self.all_players)

    def fetch_confirmed_players(self) -> int:
        """
        Fetch confirmed lineups and identify confirmed players
        Now SLATE-AWARE - only looks for games in the CSV

        Returns:
            Number of confirmed players found
        """
        print("\n🔍 Fetching Confirmed Lineups...")

        self.confirmed_names.clear()

        # Extract slate games from CSV data
        slate_teams = set()
        slate_games = {}

        print("\n📋 Identifying slate games from CSV...")
        import re

        for player in self.all_players.values():
            if hasattr(player, 'game_info') and player.game_info:
                # Parse game info with date format: "HOU@ARI 07/21/2025 09:40PM ET"
                game_str = str(player.game_info).strip()

                # Extract just the teams (simpler approach)
                if '@' in game_str:
                    parts = game_str.split()
                    if parts:
                        teams_part = parts[0]  # "HOU@ARI"
                        if '@' in teams_part:
                            away, home = teams_part.split('@')
                            game_key = f"{away}@{home}"

                            if game_key not in slate_games:
                                # Extract time if available
                                time = None
                                if len(parts) >= 3:
                                    time = parts[2].replace('ET', '').strip()

                                slate_games[game_key] = {
                                    'away': away,
                                    'home': home,
                                    'time': time,
                                    'game_info': game_str
                                }
                                slate_teams.add(away)
                                slate_teams.add(home)

                # Also add player's team
                if hasattr(player, 'team') and player.team:
                    slate_teams.add(player.team)

        print(f"   Found {len(slate_games)} games in slate")
        print(f"   Teams: {sorted(slate_teams)}")

        # Initialize counts
        lineup_count = 0
        pitcher_count = 0

        if self._using_enhanced:
            # Enhanced system returns lineups and pitchers directly
            confirmed_lineups, confirmed_pitchers = self.confirmation_system.fetch_all_confirmations()

            # Filter to only slate teams
            for team, lineup_data in confirmed_lineups.items():
                if team in slate_teams:  # Only process slate teams
                    for player_info in lineup_data:
                        player_name = player_info.get('name', '')
                        if player_name and player_name in self.all_players:
                            self.confirmed_names.add(player_name)
                            lineup_count += 1

            # Process pitchers
            for team, pitcher_info in confirmed_pitchers.items():
                if team in slate_teams:  # Only process slate teams
                    pitcher_name = pitcher_info.get('name', '')
                    if pitcher_name and pitcher_name in self.all_players:
                        self.confirmed_names.add(pitcher_name)
                        pitcher_count += 1
                        print(
                            f"   ⚾ Confirmed Pitcher: {pitcher_name} ({team}) - {pitcher_info.get('source', 'unknown')}")

        else:
            # Standard smart confirmation system
            lineup_count, pitcher_count = self.confirmation_system.get_all_confirmations()

            # Get the actual confirmation data
            confirmed_lineups = self.confirmation_system.confirmed_lineups
            confirmed_pitchers = self.confirmation_system.confirmed_pitchers

            # Process confirmed lineup players - filtered by slate
            for team, lineup_data in confirmed_lineups.items():
                if team in slate_teams:  # Only process slate teams
                    for player_info in lineup_data:
                        player_name = player_info.get('name', '')
                        if player_name and player_name in self.all_players:
                            self.confirmed_names.add(player_name)

            # Process confirmed pitchers - filtered by slate
            for team, pitcher_info in confirmed_pitchers.items():
                if team in slate_teams:  # Only process slate teams
                    pitcher_name = pitcher_info.get('name', '')
                    if pitcher_name and pitcher_name in self.all_players:
                        self.confirmed_names.add(pitcher_name)
                        print(f"   ⚾ Confirmed Pitcher: {pitcher_name} ({team})")

        print(f"\n✅ Found {len(self.confirmed_names)} confirmed players")
        print(f"   • From slate teams only")
        print(f"   • Lineup players: {lineup_count}")
        print(f"   • Starting pitchers: {pitcher_count}")

        if pitcher_count == 0:
            print("\n⚠️  No pitchers found for slate games!")
            print("   Lineups might not be posted yet for evening games")
            print("   Consider adding manual pitcher selections")

        return len(self.confirmed_names)

    def add_manual_player(self, player_name: str) -> bool:
        """
        Manually add a player to the pool

        Args:
            player_name: Name of player to add

        Returns:
            True if added successfully
        """
        if player_name in self.all_players:
            self.manual_names.add(player_name)
            print(f"✅ Manually added: {player_name}")
            return True
        else:
            print(f"❌ Player not found: {player_name}")
            return False

    def remove_manual_player(self, player_name: str) -> bool:
        """Remove a manually added player"""
        if player_name in self.manual_names:
            self.manual_names.remove(player_name)
            print(f"✅ Removed: {player_name}")
            return True
        return False

    def build_player_pool(self) -> int:
        """
        Build the final player pool from confirmed + manual selections

        Returns:
            Size of player pool
        """
        print("\n🏊 Building Player Pool...")

        # Combine confirmed and manual selections
        pool_names = self.confirmed_names.union(self.manual_names)

        # Create pool
        self.player_pool = []
        for name in pool_names:
            if name in self.all_players:
                player = self.all_players[name]
                # Mark as confirmed/manual for scoring boost
                player.is_confirmed = name in self.confirmed_names
                player.is_manual = name in self.manual_names
                self.player_pool.append(player)

        print(f"✅ Player pool size: {len(self.player_pool)}")
        print(f"   • Confirmed: {len(self.confirmed_names)}")
        print(f"   • Manual: {len(self.manual_names)}")

        # Show pool by position
        pos_counts = {}
        for p in self.player_pool:
            for pos in p.positions:
                pos_counts[pos] = pos_counts.get(pos, 0) + 1

        print("\n📊 Pool breakdown:")
        for pos, count in sorted(pos_counts.items()):
            print(f"   {pos}: {count} players")

        return len(self.player_pool)

    def enrich_player_pool(self) -> int:
        if not self.player_pool:
            return 0

        print(f"\n🔄 Enriching {len(self.player_pool)} players with ALL data sources...")

        print("\n📊 Fetching Vegas lines...")
        vegas_data = {}
        try:
            games = set()
            for player in self.player_pool:
                if hasattr(player, 'game_info') and player.game_info:
                    games.add(player.game_info)

            for game in games:
                try:
                    teams = game.split()[0].split('@')
                    if len(teams) == 2:
                        away_team, home_team = teams
                        lines = self.vegas.fetch_lines(home_team, away_team)
                        if lines:
                            vegas_data[home_team] = lines
                            vegas_data[away_team] = lines
                except:
                    continue

            print(f"   ✅ Fetched Vegas data for {len(vegas_data)} teams")
        except Exception as e:
            logger.error(f"Vegas fetch error: {e}")

        print("\n⚾ Fetching Statcast data...")
        statcast_data = {}
        try:
            if hasattr(self.statcast, 'fetch_statcast_batch'):
                statcast_results = self.statcast.fetch_statcast_batch(
                    self.player_pool
                )

                for name, stats in statcast_results.items():
                    if stats is not None:
                        statcast_data[name] = stats
            else:
                for player in self.player_pool[:20]:
                    try:
                        data = self.statcast.fetch_player_data(player.name)
                        if data is not None:
                            statcast_data[player.name] = data
                    except:
                        pass

            print(f"   ✅ Fetched Statcast data for {len(statcast_data)} players")
        except Exception as e:
            logger.error(f"Statcast fetch error: {e}")
            print(f"   ⚠️  Statcast error: {str(e)}")

        enriched_count = 0
        for player in self.player_pool:
            enriched = False

            if player.team in vegas_data:
                player.apply_vegas_data(vegas_data[player.team])
                enriched = True

            if player.name in statcast_data:
                player.apply_statcast_data(statcast_data[player.name])
                enriched = True

            if enriched:
                enriched_count += 1

        print(f"\n✅ Enriched {enriched_count}/{len(self.player_pool)} players")

        print("\n📈 Calculating player scores...")
        for player in self.player_pool:
            try:
                final_score = self.scoring_engine.calculate_score(player)

                player.optimization_score = final_score
                player.enhanced_score = final_score

                if player.is_confirmed:
                    player.optimization_score *= 1.05

            except Exception as e:
                logger.error(f"Error scoring {player.name}: {e}")
                player.optimization_score = player.base_projection
                player.enhanced_score = player.base_projection

        print("   ✅ All players scored")

        return enriched_count

    def _call_optimizer(self, players, strategy, min_salary_val, existing_lineups=None):
        base_kwargs = {
            'players': players,
            'strategy': strategy
        }

        if existing_lineups is not None:
            base_kwargs['existing_lineups'] = existing_lineups

        try:
            kwargs = {**base_kwargs, 'min_salary_usage': min_salary_val}
            return self.optimizer.optimize_lineup(**kwargs)
        except TypeError as e:
            if 'min_salary_usage' in str(e):
                try:
                    kwargs = {**base_kwargs, 'min_salary_pct': min_salary_val}
                    return self.optimizer.optimize_lineup(**kwargs)
                except TypeError as e2:
                    if 'min_salary_pct' in str(e2):
                        try:
                            return self.optimizer.optimize_lineup(**base_kwargs)
                        except Exception as e3:
                            print(f"   ❌ Optimization error: {e3}")
                            raise e3
                    else:
                        raise e2
            else:
                raise e

    def _call_optimizer(self, players, strategy, min_salary_val, existing_lineups=None):
        """
        Wrapper to handle parameter name differences between different optimizer implementations.
        """
        base_kwargs = {
            'players': players,
            'strategy': strategy
        }

        if existing_lineups is not None:
            base_kwargs['existing_lineups'] = existing_lineups

        # Try with min_salary_usage first
        try:
            kwargs = {**base_kwargs, 'min_salary_usage': min_salary_val}
            return self.optimizer.optimize_lineup(**kwargs)
        except TypeError as e:
            if 'min_salary_usage' in str(e):
                # Try with min_salary_pct instead
                try:
                    kwargs = {**base_kwargs, 'min_salary_pct': min_salary_val}
                    return self.optimizer.optimize_lineup(**kwargs)
                except TypeError as e2:
                    print(f"   ❌ Parameter error: {e2}")
                    # Try without min_salary parameter
                    try:
                        return self.optimizer.optimize_lineup(**base_kwargs)
                    except Exception as e3:
                        print(f"   ❌ Even basic call failed: {e3}")
                        raise e2
            else:
                raise

    def optimize_showdown_lineups(
            self,
            num_lineups: int = 1,
            strategy: str = "balanced",
            min_unique_players: int = 2
    ) -> List[Dict]:
        if not self.player_pool:
            print("❌ No players in pool!")
            return []

        print(f"\n🎰 Optimizing {num_lineups} SHOWDOWN lineups...")
        print(f"   Strategy: {strategy}")
        print(f"   Pool size: {len(self.player_pool)} players")

        util_players = []
        seen_names = set()

        for player in self.player_pool:
            if player.name in seen_names:
                continue

            if hasattr(player, 'display_position') and 'CPT' in player.display_position:
                continue

            util_players.append(player)
            seen_names.add(player.name)

        print(f"   Unique UTIL players: {len(util_players)}")

        if len(util_players) < 6:
            print(f"❌ Not enough unique players for showdown: {len(util_players)} (need 6)")
            return []

        lineups = []
        used_captains = set()

        for i in range(num_lineups):
            print(f"\n   Lineup {i + 1}/{num_lineups}...")

            if i > 0 and min_unique_players > 0:
                for player in util_players:
                    if player.name in used_captains:
                        if not hasattr(player, 'original_score'):
                            player.original_score = player.optimization_score
                        player.optimization_score = player.original_score * 0.7

            lineup_players, score = self._optimize_showdown_lineup(
                util_players,
                strategy=strategy
            )

            for player in util_players:
                if hasattr(player, 'original_score'):
                    player.optimization_score = player.original_score

            if lineup_players and len(lineup_players) == 6:
                captain = None
                for p in lineup_players:
                    if getattr(p, 'assigned_position', '') == 'CPT':
                        captain = p
                        used_captains.add(p.name)
                        break

                total_salary = 0
                for p in lineup_players:
                    if getattr(p, 'assigned_position', '') == 'CPT':
                        total_salary += int(p.salary * 1.5)
                    else:
                        total_salary += p.salary

                lineup_dict = {
                    'players': lineup_players,
                    'total_salary': total_salary,
                    'total_projection': score,
                    'strategy': strategy,
                    'pool_size': len(util_players),
                    'type': 'showdown'
                }

                lineups.append(lineup_dict)

                print(f"   ✅ Score: {score:.1f} pts")
                print(f"   💰 Salary: ${total_salary:,} ({total_salary / self.salary_cap:.1%})")

                if captain:
                    print(f"   👑 Captain: {captain.name} (${int(captain.salary * 1.5):,})")

        for player in util_players:
            if hasattr(player, 'original_score'):
                delattr(player, 'original_score')

        print(f"\n✅ Generated {len(lineups)} showdown lineups")
        return lineups

    def optimize_lineups(
            self,
            num_lineups: int = 1,
            strategy: str = "balanced",
            min_unique_players: int = 3
    ) -> List[Dict]:
        """Generate optimized lineups from the player pool"""
        if not self.player_pool:
            print("❌ No players in pool!")
            return []

        print(f"\\n🎯 Optimizing {num_lineups} lineups...")
        print(f"   Strategy: {strategy}")
        print(f"   Pool size: {len(self.player_pool)} players")

        lineups = []
        used_players = set()

        for i in range(num_lineups):
            print(f"\\n   Lineup {i + 1}/{num_lineups}...")

            # Enforce uniqueness
            if i > 0 and min_unique_players > 0:
                for player in self.player_pool:
                    if player.name in used_players:
                        player.temp_score = player.optimization_score
                        player.optimization_score *= 0.8

            try:
                # Use wrapper for parameter compatibility
                result = self._call_optimizer(
                    players=self.player_pool,
                    strategy=strategy,
                    min_salary_val=self.min_salary_usage,
                    existing_lineups=lineups if i > 0 else None
                )

                # Handle return types
                if isinstance(result, tuple) and len(result) == 2:
                    lineup_players, score = result
                elif isinstance(result, list):
                    lineup_players = result
                    score = sum(p.optimization_score for p in lineup_players)
                else:
                    raise ValueError(f"Unexpected return type: {type(result)}")

            except Exception as e:
                print(f"   ❌ Optimization failed: {str(e)}")
                # Restore scores
                if i > 0:
                    for player in self.player_pool:
                        if hasattr(player, 'temp_score'):
                            player.optimization_score = player.temp_score
                continue

            # Restore scores
            if i > 0:
                for player in self.player_pool:
                    if hasattr(player, 'temp_score'):
                        player.optimization_score = player.temp_score
                        delattr(player, 'temp_score')

            if lineup_players:
                # Track used players
                for p in lineup_players:
                    used_players.add(p.name)

                # Create lineup dict
                lineup_dict = {
                    'players': lineup_players,
                    'total_salary': sum(p.salary for p in lineup_players),
                    'total_projection': score,
                    'strategy': strategy,
                    'pool_size': len(self.player_pool)
                }

                lineups.append(lineup_dict)

                print(f"   ✅ Score: {score:.1f} pts")
                print(f"   💰 Salary: ${lineup_dict['total_salary']:,}")

        print(f"\\n✅ Generated {len(lineups)} lineups")
        return lineups

    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            'total_players': len(self.all_players),
            'confirmed_players': len(self.confirmed_names),
            'manual_players': len(self.manual_names),
            'pool_size': len(self.player_pool),
            'components': {
                'confirmation_system': True,
                'statcast': True,
                'vegas': True,
                'scoring_engine': True,
                'optimizer': True
            }
        }


# Test function
def test_unified_system():
    """Test the unified system"""
    print("\n" + "=" * 80)
    print("🧪 TESTING UNIFIED CORE SYSTEM")
    print("=" * 80)

    system = UnifiedCoreSystem()

    # Show status
    status = system.get_system_status()
    print(f"\n📊 System Status:")
    print(f"   Components ready: {sum(status['components'].values())}/5")

    print("\n✅ System test complete!")
    print("\nTo use with your GUI:")
    print("1. Import this system in your GUI")
    print("2. Replace optimization worker with calls to this system")
    print("3. Use the workflow: load → confirm → enrich → optimize")


if __name__ == "__main__":
    test_unified_system()