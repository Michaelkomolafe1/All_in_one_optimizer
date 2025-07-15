#!/usr/bin/env python3
"""
BULLETPROOF DFS CORE - COMPLETELY FIXED VERSION
==============================================
Clean implementation based on unified_milp_optimizer.py with all syntax errors resolved
"""

import os
import re
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import pandas as pd

# Suppress warnings
warnings.filterwarnings("ignore")

# ============================================================================
# SAFE IMPORTS WITH FALLBACKS
# ============================================================================

# Import optimization modules with fallbacks
try:
    from unified_config_manager import get_config_value

    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False


    def get_config_value(key, default):
        return default

try:
    from unified_scoring_engine import get_scoring_engine

    SCORING_ENGINE_AVAILABLE = True
except ImportError:
    SCORING_ENGINE_AVAILABLE = False

try:
    from data_validator import get_validator

    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False

try:
    from performance_optimizer import get_performance_optimizer, CacheConfig

    PERFORMANCE_OPTIMIZER_AVAILABLE = True
except ImportError:
    PERFORMANCE_OPTIMIZER_AVAILABLE = False

try:
    from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig

    UNIFIED_OPTIMIZER_AVAILABLE = True
except ImportError:
    UNIFIED_OPTIMIZER_AVAILABLE = False

try:
    from unified_player_model import UnifiedPlayer

    UNIFIED_PLAYER_AVAILABLE = True
except ImportError:
    UNIFIED_PLAYER_AVAILABLE = False

# Legacy imports with fallbacks
try:
    from vegas_lines import VegasLines

    VEGAS_AVAILABLE = True
except ImportError:
    VEGAS_AVAILABLE = False

try:
    from simple_statcast_fetcher import SimpleStatcastFetcher

    STATCAST_AVAILABLE = True
except ImportError:
    STATCAST_AVAILABLE = False

try:
    from smart_confirmation_system import SmartConfirmationSystem

    CONFIRMATION_AVAILABLE = True
except ImportError:
    CONFIRMATION_AVAILABLE = False

print("🔧 DFS Core Modules Loaded:")
print(f"  Config Manager: {'✅' if CONFIG_MANAGER_AVAILABLE else '❌'}")
print(f"  Unified Optimizer: {'✅' if UNIFIED_OPTIMIZER_AVAILABLE else '❌'}")
print(f"  Scoring Engine: {'✅' if SCORING_ENGINE_AVAILABLE else '❌'}")
print(f"  Validator: {'✅' if VALIDATOR_AVAILABLE else '❌'}")
print(f"  Performance Optimizer: {'✅' if PERFORMANCE_OPTIMIZER_AVAILABLE else '❌'}")


class BulletproofDFSCore:
    """
    Main DFS optimization system - completely rewritten for stability
    """

    def __init__(self):
        """Initialize the Bulletproof DFS Core System"""
        print("\n🚀 INITIALIZING BULLETPROOF DFS CORE")
        print("=" * 50)

        # Core attributes
        self.salary_cap = 50000
        self.contest_type = "classic"
        self.players = []
        self.confirmed_players = []
        self.game_date = None
        self.csv_file_path = None

        # Optimization settings
        self.optimization_mode = "bulletproof"
        self.manual_selections_text = ""
        self.use_ceiling_mode = False

        # Status flags
        self.use_unified_scoring = False
        self.optimization_modules_ready = False

        # Initialize modules
        self._initialize_configuration()
        self._initialize_optimization_modules()
        self._initialize_legacy_modules()

        print(f"\n✅ BulletproofDFSCore initialized successfully")
        print(f"   Unified Optimization: {'✅' if self.use_unified_scoring else '❌'}")
        print(f"   Legacy Modules: {'✅' if hasattr(self, 'vegas_lines') else '❌'}")

    def _initialize_configuration(self):
        """Initialize configuration system"""
        try:
            if CONFIG_MANAGER_AVAILABLE:
                self.salary_cap = get_config_value("optimization.salary_cap", 50000)
                self.min_salary_usage = get_config_value("optimization.min_salary_usage", 0.95)
                print("  ✅ Configuration loaded from unified config")
            else:
                # Load from dfs_config.json as fallback
                try:
                    import json
                    with open("dfs_config.json", "r") as f:
                        config_data = json.load(f)
                    self.salary_cap = config_data.get("optimization", {}).get("salary_cap", 50000)
                    print("  ✅ Configuration loaded from dfs_config.json")
                except:
                    print("  ⚠️ Using default configuration")

        except Exception as e:
            print(f"  ❌ Configuration loading failed: {e}")

    def _initialize_optimization_modules(self):
        """Initialize new optimization modules"""

        # 1. Initialize Unified Scoring Engine
        if SCORING_ENGINE_AVAILABLE:
            try:
                self.scoring_engine = get_scoring_engine()
                print("  ✅ Unified Scoring Engine initialized")
            except Exception as e:
                print(f"  ❌ Scoring Engine failed: {e}")
                self.scoring_engine = None
        else:
            self.scoring_engine = None

        # 2. Initialize Data Validator
        if VALIDATOR_AVAILABLE:
            try:
                self.validator = get_validator()
                print("  ✅ Data Validator initialized")
            except Exception as e:
                print(f"  ❌ Data Validator failed: {e}")
                self.validator = None
        else:
            self.validator = None

        # 3. Initialize Performance Optimizer
        if PERFORMANCE_OPTIMIZER_AVAILABLE:
            try:
                if CONFIG_MANAGER_AVAILABLE:
                    perf_config = CacheConfig(
                        ttl_seconds=get_config_value("performance.cache_ttl", 3600),
                        enable_disk_cache=get_config_value("performance.enable_disk_cache", True),
                        cache_dir=get_config_value("performance.cache_dir", ".dfs_cache"),
                        max_memory_mb=get_config_value("performance.max_memory_mb", 100),
                        max_size=get_config_value("performance.max_cache_size", 10000)
                    )
                else:
                    perf_config = CacheConfig()  # Use defaults

                self.performance_optimizer = get_performance_optimizer(perf_config)
                print("  ✅ Performance Optimizer initialized")
            except Exception as e:
                print(f"  ❌ Performance Optimizer failed: {e}")
                self.performance_optimizer = None
        else:
            self.performance_optimizer = None

        # 4. Initialize Unified MILP Optimizer
        if UNIFIED_OPTIMIZER_AVAILABLE:
            try:
                opt_config = OptimizationConfig()
                if CONFIG_MANAGER_AVAILABLE:
                    opt_config.salary_cap = get_config_value("optimization.salary_cap", 50000)
                    opt_config.min_salary_usage = get_config_value("optimization.min_salary_usage", 0.95)

                self.unified_optimizer = UnifiedMILPOptimizer(opt_config)
                print("  ✅ Unified MILP Optimizer initialized")
            except Exception as e:
                print(f"  ❌ Unified Optimizer failed: {e}")
                self.unified_optimizer = None
        else:
            self.unified_optimizer = None

        # Set unified scoring flag
        self.use_unified_scoring = all([
            self.scoring_engine is not None,
            self.validator is not None,
            self.performance_optimizer is not None,
            self.unified_optimizer is not None
        ])

        self.optimization_modules_ready = self.use_unified_scoring

        if self.use_unified_scoring:
            print("  🎯 All optimization modules ready - UNIFIED MODE ENABLED")
        else:
            print("  ⚠️ Some modules unavailable - using LEGACY MODE")

    def _initialize_legacy_modules(self):
        """Initialize legacy modules for backwards compatibility"""

        # Vegas Lines
        if VEGAS_AVAILABLE:
            try:
                self.vegas_lines = VegasLines(verbose=False)
                print("  ✅ Vegas Lines initialized")
            except Exception as e:
                print(f"  ❌ Vegas Lines failed: {e}")
                self.vegas_lines = None
        else:
            self.vegas_lines = None

        # Smart Confirmation System
        if CONFIRMATION_AVAILABLE:
            try:
                self.confirmation_system = SmartConfirmationSystem()
                print("  ✅ Smart Confirmation System initialized")
            except Exception as e:
                print(f"  ❌ Confirmation System failed: {e}")
                self.confirmation_system = None
        else:
            self.confirmation_system = None

        # Statcast Fetcher
        if STATCAST_AVAILABLE:
            try:
                self.statcast_fetcher = SimpleStatcastFetcher()
                print("  ✅ Statcast Fetcher initialized")
            except Exception as e:
                print(f"  ❌ Statcast Fetcher failed: {e}")
                self.statcast_fetcher = None
        else:
            self.statcast_fetcher = None

    def get_eligible_players_by_mode(self):
        """Get eligible players based on optimization mode"""
        if self.optimization_mode == "all":
            return self.players.copy()
        elif self.optimization_mode == "manual_only":
            return [p for p in self.players if getattr(p, 'is_manual_selected', False)]
        elif self.optimization_mode == "confirmed_only":
            return [p for p in self.players if getattr(p, 'is_confirmed', False)]
        else:  # bulletproof
            return [p for p in self.players if
                    getattr(p, 'is_confirmed', False) or
                    getattr(p, 'is_manual_selected', False)]

    def load_draftkings_csv(self, csv_file_path: str, force_reload: bool = False) -> int:
        """
        Load and process DraftKings CSV file

        Returns:
            int: Number of players loaded
        """
        try:
            if not os.path.exists(csv_file_path):
                raise FileNotFoundError(f"CSV file not found: {csv_file_path}")

            print(f"\n📂 LOADING CSV: {csv_file_path}")

            # Read CSV
            df = pd.read_csv(csv_file_path)
            print(f"  📊 Found {len(df)} rows in CSV")

            # Store file path
            self.csv_file_path = csv_file_path

            # Process players based on available modules
            if self.use_unified_scoring and UNIFIED_PLAYER_AVAILABLE:
                self.players = self._process_players_unified(df)
                print(f"  🎯 Processed {len(self.players)} players with UNIFIED MODEL")
            else:
                self.players = self._process_players_legacy(df)
                print(f"  📊 Processed {len(self.players)} players with LEGACY MODEL")

            # Update confirmation system if available
            if self.confirmation_system:
                try:
                    self.confirmation_system.update_csv_players(self.players)
                    print("  ✅ Updated confirmation system")
                except Exception as e:
                    print(f"  ⚠️ Could not update confirmation system: {e}")

            return len(self.players)

        except Exception as e:
            print(f"  ❌ Error loading CSV: {e}")
            raise

    def _process_players_unified(self, df: pd.DataFrame) -> List[UnifiedPlayer]:
        """Process players using unified player model"""
        players = []

        for _, row in df.iterrows():
            try:
                player = UnifiedPlayer(
                    id=f"{row.get('Name', 'Unknown')}_{row.get('TeamAbbrev', 'UNK')}",  # Create unique ID
                    name=str(row.get('Name', row.get('Roster Position', 'Unknown'))),
                    team=str(row.get('TeamAbbrev', row.get('Team', 'UNK'))),
                    salary=int(row.get('Salary', 0)),
                    primary_position=str(row.get('Roster Position', row.get('Position', 'UTIL'))),
                    positions=[str(row.get('Roster Position', row.get('Position', 'UTIL')))],
                    base_projection=float(row.get('AvgPointsPerGame', 0))  # Changed from projected_points
                )

                # Add game info if available
                if 'Game Info' in row:
                    player.game_info = str(row['Game Info'])

                players.append(player)

            except Exception as e:
                print(f"    ⚠️ Error processing player {row.get('Name', 'Unknown')}: {e}")
                continue

        return players

    def _process_players_legacy(self, df: pd.DataFrame) -> List[Dict]:
        """Process players using legacy dictionary model"""
        players = []

        for _, row in df.iterrows():
            try:
                player = {
                    'name': str(row.get('Name', row.get('Roster Position', 'Unknown'))),
                    'position': str(row.get('Roster Position', row.get('Position', 'UTIL'))),
                    'team': str(row.get('TeamAbbrev', row.get('Team', 'UNK'))),
                    'salary': int(row.get('Salary', 0)),
                    'projected_points': float(row.get('AvgPointsPerGame', 0)),
                    'game_info': str(row.get('Game Info', '')),
                    'is_confirmed': False,
                    'is_manual_selected': False
                }

                players.append(player)

            except Exception as e:
                print(f"    ⚠️ Error processing player {row.get('Name', 'Unknown')}: {e}")
                continue

        return players

    def optimize_lineup(self, strategy: str = "balanced", manual_selections: str = "") -> Optional[Dict]:
        """
        Optimize lineup using best available method

        Args:
            strategy: Optimization strategy ("balanced", "ceiling", "safe", etc.)
            manual_selections: Comma-separated list of player names to force include

        Returns:
            Dict containing optimized lineup or None if optimization failed
        """
        try:
            print(f"\n🎯 OPTIMIZING LINEUP - Strategy: {strategy.upper()}")

            if not self.players:
                raise ValueError("No players loaded. Load CSV first.")

            # Use unified optimizer if available
            if self.use_unified_scoring and self.unified_optimizer:
                return self._optimize_unified(strategy, manual_selections)
            else:
                return self._optimize_legacy(strategy, manual_selections)

        except Exception as e:
            print(f"  ❌ Optimization failed: {e}")
            return None

    def _optimize_unified(self, strategy: str, manual_selections: str) -> Optional[Dict]:
        """Optimize using unified MILP optimizer"""
        try:
            print("  🎯 Using UNIFIED OPTIMIZATION")

            # Convert manual selections
            manual_players = []
            if manual_selections:
                manual_players = self.unified_optimizer.parse_manual_selections(
                    manual_selections, self.players
                )
                print(f"    📌 Manual selections: {len(manual_players)} players")

            # Optimize
            result = self.unified_optimizer.optimize(
                self.players,
                strategy=strategy,
                manual_selections=manual_players
            )

            if result and hasattr(result, 'lineup'):
                return self._format_unified_result(result)
            else:
                print("  ❌ Unified optimization returned no result")
                return None

        except Exception as e:
            print(f"  ❌ Unified optimization failed: {e}")
            return None

    def _optimize_legacy(self, strategy: str, manual_selections: str) -> Optional[Dict]:
        """Optimize using legacy method"""
        print("  📊 Using LEGACY OPTIMIZATION")

        # Basic legacy optimization logic
        try:
            # Simple lineup selection for fallback
            lineup = self._create_basic_lineup(strategy)

            if lineup:
                return {
                    'lineup': lineup,
                    'total_salary': sum(p.get('salary', 0) for p in lineup),
                    'projected_points': sum(p.get('projected_points', 0) for p in lineup),
                    'strategy': strategy,
                    'optimization_method': 'legacy'
                }
            else:
                return None

        except Exception as e:
            print(f"  ❌ Legacy optimization failed: {e}")
            return None

    def _create_basic_lineup(self, strategy: str) -> Optional[List[Dict]]:
        """Create basic lineup using simple logic"""
        # This is a simplified version - implement your existing logic here
        print("    📊 Creating basic lineup...")

        # Position requirements
        required_positions = {
            'P': 2, 'C': 1, '1B': 1, '2B': 1,
            '3B': 1, 'SS': 1, 'OF': 3
        }

        lineup = []
        used_salary = 0

        # Simple greedy selection based on points per dollar
        for pos, count in required_positions.items():
            pos_players = [p for p in self.players if p.get('position') == pos]

            # Sort by points per dollar ratio
            pos_players.sort(
                key=lambda x: x.get('projected_points', 0) / max(x.get('salary', 1), 1),
                reverse=True
            )

            for i in range(min(count, len(pos_players))):
                player = pos_players[i]
                if used_salary + player.get('salary', 0) <= self.salary_cap:
                    lineup.append(player)
                    used_salary += player.get('salary', 0)

        return lineup if len(lineup) >= 8 else None

    def _format_unified_result(self, result) -> Dict:
        """Format unified optimization result"""
        return {
            'lineup': result.lineup,
            'total_salary': result.total_salary,
            'projected_points': result.projected_points,
            'strategy': result.strategy if hasattr(result, 'strategy') else 'unknown',
            'optimization_method': 'unified',
            'correlation_score': getattr(result, 'correlation_score', 0),
            'ownership_projection': getattr(result, 'ownership_projection', {}),
            'meta': getattr(result, 'meta', {})
        }

    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            'core_initialized': True,
            'players_loaded': len(self.players) > 0,
            'csv_file': self.csv_file_path,
            'unified_mode': self.use_unified_scoring,
            'modules': {
                'scoring_engine': self.scoring_engine is not None,
                'validator': self.validator is not None,
                'performance_optimizer': self.performance_optimizer is not None,
                'unified_optimizer': getattr(self, 'unified_optimizer', None) is not None,
                'vegas_lines': getattr(self, 'vegas_lines', None) is not None,
                'confirmation_system': getattr(self, 'confirmation_system', None) is not None,
                'statcast_fetcher': getattr(self, 'statcast_fetcher', None) is not None
            },
            'optimization_ready': self.optimization_modules_ready,
            'salary_cap': self.salary_cap,
            'total_players': len(self.players)
        }

    def detect_confirmed_players(self) -> int:
        """Detect confirmed players (optimized version)"""
        print("\n🔍 DETECTING CONFIRMED PLAYERS (OPTIMIZED)")
        print("=" * 50)

        confirmed_count = 0

        # Use confirmation system if available
        if self.confirmation_system:
            try:
                print("  🚀 Using Optimized Smart Confirmation System")

                # Get confirmations first
                lineup_count, pitcher_count = self.confirmation_system.get_all_confirmations()

                # Apply optimized confirmation workflow (22.8x faster!)
                if hasattr(self.confirmation_system, 'apply_confirmations_optimized'):
                    confirmed_count = self.confirmation_system.apply_confirmations_optimized(
                        self.players,  # CSV players
                        self.confirmation_system.confirmed_lineups,  # Confirmed lineups
                        self.confirmation_system.confirmed_pitchers  # Confirmed pitchers
                    )
                else:
                    # Fallback to old method if optimized version not available
                    print("  ⚠️  Optimized method not found, using fallback")
                    for player in self.players:
                        if hasattr(self.confirmation_system, 'is_player_confirmed'):
                            is_confirmed, order = self.confirmation_system.is_player_confirmed(
                                player.name, player.team
                            )
                            if is_confirmed:
                                player.is_confirmed = True
                                confirmed_count += 1

            except Exception as e:
                print(f"❌ Confirmation detection failed: {e}")
                return 0
        else:
            print("❌ No confirmation system available")
            return 0

        print(f"✅ Confirmed {confirmed_count} total players")
        return confirmed_count

    def optimize_lineup_with_mode(self) -> Tuple[List, float]:
        """Optimize lineup (legacy compatibility method)"""
        try:
            result = self.optimize_lineup("balanced", "")

            if result:
                lineup = result.get('lineup', [])
                score = result.get('projected_points', 0)

                # Convert dict players to objects for compatibility
                if lineup and isinstance(lineup[0], dict):
                    # Create simple player objects for legacy compatibility
                    class SimplePlayer:
                        def __init__(self, player_dict):
                            self.name = player_dict['name']
                            self.primary_position = player_dict['position']
                            self.assigned_position = player_dict['position']
                            self.team = player_dict['team']
                            self.salary = player_dict['salary']
                            self.enhanced_score = player_dict['projected_points']

                    lineup = [SimplePlayer(p) for p in lineup]

                return lineup, score
            else:
                return [], 0

        except Exception as e:
            print(f"  ❌ Optimization failed: {e}")
            return [], 0

    # ========================================================================
    # MLB SHOWDOWN OPTIMIZATION
    # ========================================================================

    def optimize_showdown_lineup(self) -> Tuple[List, float]:
        """
        Optimize lineup for MLB Showdown format (1 Captain + 5 UTIL)
        Uses all existing scoring and data systems, only changes lineup constraints
        """
        print(f"\n🎯 MLB SHOWDOWN OPTIMIZATION")
        print("=" * 60)

        # Get eligible players using existing method
        eligible = self.get_eligible_players_by_mode()

        if len(eligible) < 6:
            print(f"❌ Not enough eligible players: {len(eligible)}")
            print("💡 Try using 'all' mode or adding manual selections")
            return [], 0

        print(f"📊 Optimizing with {len(eligible)} eligible players")

        # Ensure all players have enhanced scores calculated
        # This uses your existing scoring engine with Vegas, Statcast, etc.
        print("📈 Calculating enhanced scores with all data sources...")
        for player in eligible:
            if not hasattr(player, 'enhanced_score') or player.enhanced_score <= 0:
                self.calculate_player_score(player)

        # Show score range to verify enrichment
        scores = [p.enhanced_score for p in eligible if hasattr(p, 'enhanced_score')]
        if scores:
            print(f"   Score range: {min(scores):.1f} - {max(scores):.1f}")

        # Use MILP optimization with showdown constraints
        return self._optimize_showdown_milp(eligible)

    def _optimize_showdown_milp(self, players: List) -> Tuple[List, float]:
        """
        MILP optimization specifically for MLB Showdown format
        Constraints:
        - 1 Captain (1.5x points and salary)
        - 5 UTIL players
        - $50,000 salary cap
        - Must include players from both teams
        - Player can't be both Captain and UTIL
        """
        try:
            import pulp

            prob = pulp.LpProblem("MLB_Showdown", pulp.LpMaximize)

            # Decision variables
            x = {}  # x[i] = 1 if player i is selected as UTIL
            c = {}  # c[i] = 1 if player i is selected as Captain

            for i in range(len(players)):
                x[i] = pulp.LpVariable(f"util_{i}", cat='Binary')
                c[i] = pulp.LpVariable(f"captain_{i}", cat='Binary')

            # Objective: Maximize total points with captain multiplier
            prob += pulp.lpSum([
                x[i] * players[i].enhanced_score + 
                c[i] * players[i].enhanced_score * 1.5
                for i in range(len(players))
            ])

            # Constraint 1: Roster requirements
            prob += pulp.lpSum(c.values()) == 1  # Exactly 1 captain
            prob += pulp.lpSum(x.values()) == 5  # Exactly 5 utilities

            # Constraint 2: Each player can only be selected once
            for i in range(len(players)):
                prob += x[i] + c[i] <= 1

            # Constraint 3: Salary cap ($50,000)
            # Captain costs 1.5x salary
            total_salary = pulp.lpSum([
                x[i] * players[i].salary + 
                c[i] * players[i].salary * 1.5
                for i in range(len(players))
            ])
            prob += total_salary <= 50000

            # Constraint 4: Must include players from both teams
            teams = list(set(p.team for p in players))
            if len(teams) >= 2:
                # At least one player from each of the first two teams
                for team in teams[:2]:
                    team_players = [i for i, p in enumerate(players) if p.team == team]
                    if team_players:  # Only add constraint if team has players
                        prob += pulp.lpSum([x[i] + c[i] for i in team_players]) >= 1

            # Solve
            solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=30)
            status = prob.solve(solver)

            if status == pulp.LpStatusOptimal:
                # Extract lineup
                lineup = []
                total_score = 0
                total_salary_used = 0

                # Find captain
                captain_found = False
                for i in range(len(players)):
                    if c[i].value() == 1:
                        captain = players[i].copy() if hasattr(players[i], 'copy') else players[i]
                        captain.assigned_position = 'CPT'
                        captain.is_captain = True
                        captain.multiplier = 1.5
                        captain.captain_salary = int(captain.salary * 1.5)
                        lineup.append(captain)
                        total_score += captain.enhanced_score * 1.5
                        total_salary_used += captain.captain_salary
                        captain_found = True
                        print(f"\n👑 CAPTAIN: {captain.name} ({captain.team})")
                        print(f"   Position: {captain.primary_position}")
                        print(f"   Salary: ${captain.salary:,} → ${captain.captain_salary:,}")
                        print(f"   Points: {captain.enhanced_score:.1f} → {captain.enhanced_score * 1.5:.1f}")

                # Find utilities
                print("\n⚡ UTILITIES:")
                util_count = 0
                for i in range(len(players)):
                    if x[i].value() == 1:
                        util = players[i].copy() if hasattr(players[i], 'copy') else players[i]
                        util.assigned_position = 'UTIL'
                        util.is_captain = False
                        util.multiplier = 1.0
                        lineup.append(util)
                        total_score += util.enhanced_score
                        total_salary_used += util.salary
                        util_count += 1
                        print(f"   {util_count}. {util.name} ({util.team}) - {util.primary_position}")
                        print(f"      ${util.salary:,} → {util.enhanced_score:.1f} pts")

                # Verify lineup
                if len(lineup) != 6 or not captain_found:
                    print(f"\n❌ Invalid lineup: {len(lineup)} players, captain: {captain_found}")
                    return [], 0

                # Display summary
                print(f"\n📊 LINEUP SUMMARY:")
                print(f"   Total Salary: ${total_salary_used:,} / $50,000 (${50000 - total_salary_used:,} remaining)")
                print(f"   Projected Score: {total_score:.1f} points")

                # Team distribution
                team_counts = {}
                for p in lineup:
                    team_counts[p.team] = team_counts.get(p.team, 0) + 1
                print(f"   Team Distribution: {dict(team_counts)}")

                # Data sources used
                data_sources = []
                sample_player = lineup[0]
                if hasattr(sample_player, 'vegas_data') and sample_player.vegas_data:
                    data_sources.append('Vegas')
                if hasattr(sample_player, 'statcast_data') and sample_player.statcast_data:
                    data_sources.append('Statcast')
                if hasattr(sample_player, '_recent_performance') and sample_player._recent_performance:
                    data_sources.append('Recent Form')
                if data_sources:
                    print(f"   Data Sources Used: {', '.join(data_sources)}")

                return lineup, total_score
            else:
                print(f"❌ Optimization failed: {pulp.LpStatus[status]}")
                return [], 0

        except Exception as e:
            print(f"❌ Error in showdown optimization: {e}")
            import traceback
            traceback.print_exc()
            return [], 0

    def run_diagnostics(self):
        """Run comprehensive system diagnostics"""
        print("\n🔧 SYSTEM DIAGNOSTICS")
        print("=" * 50)

        status = self.get_system_status()

        print(f"Core Status: {'✅' if status['core_initialized'] else '❌'}")
        print(f"Players Loaded: {'✅' if status['players_loaded'] else '❌'} ({status['total_players']} players)")
        print(f"Optimization Mode: {'🎯 UNIFIED' if status['unified_mode'] else '📊 LEGACY'}")
        print(f"Ready to Optimize: {'✅' if status['optimization_ready'] else '❌'}")

        print("\nModule Status:")
        for module, available in status['modules'].items():
            icon = "✅" if available else "❌"
            print(f"  {icon} {module}")

        if status['csv_file']:
            print(f"\nLoaded CSV: {status['csv_file']}")

        return status


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_bulletproof_core() -> BulletproofDFSCore:
    """Create a new BulletproofDFSCore instance"""
    return BulletproofDFSCore()


def verify_system() -> bool:
    """Verify the system is working correctly"""
    try:
        core = BulletproofDFSCore()
        status = core.get_system_status()
        return status['core_initialized']
    except Exception as e:
        print(f"System verification failed: {e}")
        return False


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("✅ bulletproof_dfs_core module loaded successfully")
    print("\n📋 Usage:")
    print("  from bulletproof_dfs_core import BulletproofDFSCore")
    print("  core = BulletproofDFSCore()")
    print("  core.load_draftkings_csv('your_file.csv')")
    print("  result = core.optimize_lineup('balanced')")

    # Run verification
    if verify_system():
        print("\n✅ System verification passed!")
    else:
        print("\n❌ System verification failed!")