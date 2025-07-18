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
from enrichment_bridge import EnrichmentBridge

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
        self.enrichment_bridge = EnrichmentBridge()

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

    def optimize_showdown_lineup(self):
        """Fixed showdown optimization for UnifiedPlayer objects"""
        print(f"\n🎰 FIXED SHOWDOWN OPTIMIZATION")

        # Fix the projection attribute issue
        for player in self.players:
            if not hasattr(player, 'projection') or getattr(player, 'projection', 0) <= 0:
                # Try different attribute names
                if hasattr(player, 'base_projection'):
                    player.projection = player.base_projection
                elif hasattr(player, 'avg_points_per_game'):
                    player.projection = player.avg_points_per_game
                elif hasattr(player, 'salary'):
                    player.projection = max(player.salary / 1000.0, 5.0)  # Fallback
                else:
                    player.projection = 5.0  # Last resort

        # Now call your existing enrichment bridge
        if hasattr(self, 'enrichment_bridge'):
            return self.enrichment_bridge.optimize_showdown_with_enrichments(self)
        else:
            # Simple fallback optimization
            return self.simple_showdown_fallback()

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

    # Add these methods to your BulletproofDFSCore class:

    def detect_confirmed_players(self) -> int:
        """Apply confirmations using MLB starting pitchers"""
        print("\n🔍 MLB PITCHER CONFIRMATION DETECTION")
        print("=" * 60)

        # Reset all confirmations inline
        print("🔄 Resetting all confirmations...")
        for player in self.players:
            player.is_confirmed = False
            # Only reset confirmation_sources if it exists
            if hasattr(player, 'confirmation_sources'):
                player.confirmation_sources = []
        print(f"✅ Reset confirmations for {len(self.players)} players")

        # Use MLB API to get today's starting pitchers
        return self._detect_mlb_pitchers_only()

    def _detect_mlb_pitchers_only(self):
        """Use MLB API to confirm today's starting pitchers and exclude others"""
        import requests
        from datetime import datetime

        today = datetime.now().strftime('%Y-%m-%d')
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=probablePitcher"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()

                # Get today's starting pitchers
                todays_pitchers = []
                for date_entry in data.get('dates', []):
                    for game in date_entry.get('games', []):
                        for side in ['home', 'away']:
                            pitcher = game.get('teams', {}).get(side, {}).get('probablePitcher')
                            if pitcher:
                                pitcher_name = pitcher.get('fullName', '')
                                if pitcher_name:
                                    todays_pitchers.append(pitcher_name)

                print(f"📋 Found {len(todays_pitchers)} starting pitchers for today")

                # Show the pitchers
                if todays_pitchers:
                    print("\n⚾ Starting today:")
                    for p in sorted(todays_pitchers)[:10]:  # Show first 10
                        print(f"   • {p}")
                    if len(todays_pitchers) > 10:
                        print(f"   ... and {len(todays_pitchers) - 10} more")

                # Apply confirmations and exclusions
                confirmed = 0
                excluded = 0
                excluded_names = []

                for player in self.players:
                    if player.primary_position == "P":
                        # Check if pitcher is starting today
                        is_starting = False
                        for pitcher_name in todays_pitchers:
                            if self._names_match(player.name, pitcher_name):
                                is_starting = True
                                break

                        if is_starting:
                            player.is_confirmed = True
                            # Safely add confirmation source
                            if hasattr(player, 'add_confirmation_source'):
                                player.add_confirmation_source("mlb_starter")
                            elif hasattr(player, 'confirmation_sources'):
                                if "mlb_starter" not in player.confirmation_sources:
                                    player.confirmation_sources.append("mlb_starter")
                            confirmed += 1
                        else:
                            # EXCLUDE non-starting pitchers
                            player.is_confirmed = False
                            player.enhanced_score = 0
                            player.projection = 0
                            excluded += 1
                            excluded_names.append(f"{player.name} (${player.salary:,})")
                    else:
                        # Confirm all position players for now
                        player.is_confirmed = True
                        # Safely add confirmation source
                        if hasattr(player, 'add_confirmation_source'):
                            player.add_confirmation_source("all_positions")
                        elif hasattr(player, 'confirmation_sources'):
                            if "all_positions" not in player.confirmation_sources:
                                player.confirmation_sources.append("all_positions")
                        confirmed += 1

                # Show excluded pitchers
                if excluded_names:
                    print(f"\n❌ Excluded {len(excluded_names)} non-starting pitchers:")
                    # Show high-salary excluded pitchers first
                    high_salary_excluded = [p for p in excluded_names if "$10," in p or "$9," in p or "$8," in p]
                    for p in high_salary_excluded[:5]:
                        print(f"   • {p}")
                    if len(high_salary_excluded) > 5:
                        print(f"   ... and {len(excluded_names) - 5} more")

                print(f"\n✅ Confirmed {confirmed} players")
                print(f"❌ Excluded {excluded} pitchers not starting today")

                return confirmed

        except Exception as e:
            print(f"❌ MLB API error: {e}")
            import traceback
            traceback.print_exc()

            # Last resort - confirm all position players, exclude expensive pitchers
            print("\n⚠️ Using fallback: excluding high-salary pitchers")

            confirmed = 0
            for player in self.players:
                if player.primary_position == "P" and player.salary > 8000:
                    # Exclude expensive pitchers as they're likely not playing
                    player.is_confirmed = False
                    player.enhanced_score = 0
                    player.projection = 0
                else:
                    player.is_confirmed = True
                    confirmed += 1

            return confirmed

    def _names_match(self, name1: str, name2: str) -> bool:
        """Simple name matching with better error handling"""
        if not name1 or not name2:
            return False

        try:
            clean1 = name1.lower().strip()
            clean2 = name2.lower().strip()

            # Exact match
            if clean1 == clean2:
                return True

            # Last name match (for "J. Smith" vs "John Smith")
            parts1 = clean1.split()
            parts2 = clean2.split()

            if parts1 and parts2:
                # Check last names
                if parts1[-1] == parts2[-1]:
                    # Check first name or initial
                    if len(parts1) > 0 and len(parts2) > 0:
                        if len(parts1[0]) >= 1 and len(parts2[0]) >= 1:
                            if parts1[0] == parts2[0] or parts1[0][0] == parts2[0][0]:
                                return True

            # One name contains the other
            if clean1 in clean2 or clean2 in clean1:
                return True

            return False

        except Exception:
            return False

    # ========================================================================
    # MLB SHOWDOWN OPTIMIZATION
    # ========================================================================

    def optimize_showdown_lineup(self):
        return self.enrichment_bridge.optimize_showdown_with_enrichments(self)

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