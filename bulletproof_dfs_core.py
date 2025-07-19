#!/usr/bin/env python3
"""
BULLETPROOF DFS CORE V2 - WITH SHOWDOWN MODE
============================================
Enhanced DFS optimization system with showdown support
"""

# Standard library imports
import csv
import json
import logging
import random
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
# Core imports
from unified_player_model import UnifiedPlayer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import scoring engine if available
try:
    from unified_scoring_engine import get_scoring_engine, ScoringEngineConfig

    SCORING_ENGINE_AVAILABLE = True
except ImportError:
    logger.warning("Scoring engine not available")
    SCORING_ENGINE_AVAILABLE = False

# Import validator if available
try:
    from data_validator import get_validator, ValidationConfig

    VALIDATOR_AVAILABLE = True
except ImportError:
    logger.warning("Data validator not available")
    VALIDATOR_AVAILABLE = False

# Import unified optimizer
try:
    from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig

    UNIFIED_OPTIMIZER_AVAILABLE = True
except ImportError:
    logger.error("CRITICAL: Unified MILP optimizer not available!")
    UNIFIED_OPTIMIZER_AVAILABLE = False

# Import data sources
try:
    from simple_statcast_fetcher import FastStatcastFetcher
except ImportError:
    FastStatcastFetcher = None

try:
    from smart_confirmation_system import SmartConfirmationSystem
except ImportError:
    SmartConfirmationSystem = None

try:
    from vegas_lines import VegasLines
except ImportError:
    VegasLines = None

# Import performance optimizer
try:
    from performance_optimizer import get_performance_optimizer, CacheConfig

    PERFORMANCE_OPTIMIZER_AVAILABLE = True
except ImportError:
    logger.warning("Performance optimizer not available")
    PERFORMANCE_OPTIMIZER_AVAILABLE = False

# Check for performance config
try:
    from performance_config import get_performance_settings

    PERFORMANCE_CONFIG_AVAILABLE = True
except ImportError:
    PERFORMANCE_CONFIG_AVAILABLE = False

# Module availability tracking
MODULES = {
    'scoring_engine': {'module': 'unified_scoring_engine', 'available': SCORING_ENGINE_AVAILABLE},
    'validator': {'module': 'data_validator', 'available': VALIDATOR_AVAILABLE},
    'unified_optimizer': {'module': 'unified_milp_optimizer', 'available': UNIFIED_OPTIMIZER_AVAILABLE},
    'statcast': {'module': 'simple_statcast_fetcher', 'available': FastStatcastFetcher is not None},
    'confirmation': {'module': 'smart_confirmation_system', 'available': SmartConfirmationSystem is not None},
    'vegas_lines': {'module': 'vegas_lines', 'available': VegasLines is not None},
    'performance_optimizer': {'module': 'performance_optimizer', 'available': PERFORMANCE_OPTIMIZER_AVAILABLE}
}


class BulletproofDFSCore:
    """
    Enhanced DFS optimization system with showdown support
    """

    def __init__(self, mode: str = "production", contest_type: str = "classic"):
        """
        Initialize the core system

        Args:
            mode: 'production' or 'test' mode
            contest_type: 'classic' or 'showdown'
        """
        self.mode = mode
        self.logger = logger
        self.contest_type = contest_type

        # Display initialization header
        self._display_init_header()

        # Core attributes
        self.salary_cap = 50000
        self.min_salary_usage = 0.95
        self.players = []
        self.csv_file_path = None

        # Caching
        self._lineup_cache = {}
        self._score_cache = {}

        # Optimization settings
        self.optimization_mode = "balanced"
        self.manual_selections = []

        # Status flags
        self.unified_mode = False
        self.modules_status = {}

        # Initialize all components
        self._initialize_all()

        # Display status
        self._display_init_summary()

    def _display_init_header(self):
        """Display initialization header"""
        print("\n" + "=" * 60)
        print("🚀 BULLETPROOF DFS CORE V2 - INITIALIZATION")
        print("=" * 60)
        print(f"Mode: {self.mode.upper()}")
        print(f"Contest Type: {self.contest_type.upper()}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)

    def _initialize_all(self):
        """Initialize all system components"""
        # 1. Load configuration
        self._load_configuration()

        # 2. Initialize core modules
        self._initialize_core_modules()

        # 3. Initialize data sources
        self._initialize_data_sources()

        # 4. Check unified mode
        self.unified_mode = self._check_unified_mode()

    def _load_configuration(self):
        """Load system configuration"""
        print("\n📋 Loading Configuration...")

        # Set defaults based on contest type
        if self.contest_type == "showdown":
            self.salary_cap = 50000  # Same cap for showdown
            self.min_salary_usage = 0.90  # Slightly lower for showdown flexibility
        else:
            self.salary_cap = 50000
            self.min_salary_usage = 0.95

        print(f"  ✅ Salary Cap: ${self.salary_cap:,}")
        print(f"  ✅ Min Usage: {self.min_salary_usage:.0%}")
        print(f"  ✅ Contest Type: {self.contest_type}")

    def _initialize_core_modules(self):
        """Initialize core optimization modules"""
        print("\n🔧 Initializing Core Modules...")

        # Scoring Engine
        if SCORING_ENGINE_AVAILABLE:
            try:
                config = ScoringEngineConfig(cache_ttl=300)
                self.scoring_engine = get_scoring_engine(config)
                self.modules_status['scoring_engine'] = True
                print("  ✅ Scoring Engine")
            except Exception as e:
                logger.error(f"Scoring engine initialization failed: {e}")
                self.scoring_engine = None
                self.modules_status['scoring_engine'] = False

        # Data Validator
        if VALIDATOR_AVAILABLE:
            try:
                val_config = ValidationConfig(strict_mode=False)
                self.validator = get_validator(val_config)
                self.modules_status['validator'] = True
                print("  ✅ Data Validator")
            except Exception as e:
                logger.error(f"Validator initialization failed: {e}")
                self.validator = None
                self.modules_status['validator'] = False

        # MILP Optimizer
        if UNIFIED_OPTIMIZER_AVAILABLE:
            try:
                opt_config = OptimizationConfig(
                    salary_cap=self.salary_cap,
                    min_salary_usage=self.min_salary_usage
                )
                self.optimizer = UnifiedMILPOptimizer(opt_config)
                self.modules_status['unified_optimizer'] = True
                print("  ✅ MILP Optimizer")
            except Exception as e:
                logger.error(f"MILP optimizer initialization failed: {e}")
                self.optimizer = None
                self.modules_status['unified_optimizer'] = False

    def _initialize_data_sources(self):
        """Initialize external data sources"""
        print("\n📊 Initializing Data Sources...")

        # Vegas Lines
        if MODULES['vegas_lines']['available']:
            try:
                self.vegas_lines = VegasLines(verbose=False)
                self.modules_status['vegas_lines'] = True
                print("  ✅ Vegas Lines")
            except Exception as e:
                logger.error(f"Vegas lines initialization failed: {e}")
                self.vegas_lines = None
                self.modules_status['vegas_lines'] = False

        # Statcast
        if MODULES['statcast']['available']:
            try:
                self.statcast_fetcher = FastStatcastFetcher(max_workers=5)
                self.modules_status['statcast'] = True
                print("  ✅ Statcast Fetcher")
            except Exception as e:
                logger.error(f"Statcast initialization failed: {e}")
                self.statcast_fetcher = None
                self.modules_status['statcast'] = False

        # Confirmation System
        if MODULES['confirmation']['available']:
            try:
                self.confirmation_system = SmartConfirmationSystem(verbose=False)
                self.modules_status['confirmation'] = True
                print("  ✅ Confirmation System")
            except Exception as e:
                logger.error(f"Confirmation system initialization failed: {e}")
                self.confirmation_system = None
                self.modules_status['confirmation'] = False

    def _check_unified_mode(self) -> bool:
        """Check if all unified components are available"""
        required = ['unified_optimizer', 'scoring_engine']
        return all(self.modules_status.get(module, False) for module in required)

    def _display_init_summary(self):
        """Display initialization summary"""
        print("\n📊 INITIALIZATION SUMMARY")
        print("=" * 60)

        # Count available modules
        available = sum(1 for status in self.modules_status.values() if status)
        total = len(self.modules_status)

        print(f"✅ Modules Loaded: {available}/{total}")
        print(f"🎯 Unified Mode: {'ENABLED' if self.unified_mode else 'DISABLED'}")
        print(f"🏆 Contest Type: {self.contest_type.upper()}")

        if available < total:
            print("\n⚠️  Some modules failed to load. Core functionality available.")

        print("=" * 60)

    def set_contest_type(self, contest_type: str):
        """Set contest type (classic or showdown)"""
        if contest_type.lower() in ['classic', 'showdown']:
            self.contest_type = contest_type.lower()
            self._load_configuration()  # Reload config for new contest type
            logger.info(f"Contest type set to: {self.contest_type}")
            print(f"✅ Contest type changed to: {self.contest_type}")
        else:
            logger.error(f"Invalid contest type: {contest_type}")
            print(f"❌ Invalid contest type. Use 'classic' or 'showdown'")

    def load_draftkings_csv(self, file_path: str) -> int:
        """Load players from DraftKings CSV file"""
        print(f"\n📂 Loading CSV: {file_path}")
        self.csv_file_path = file_path
        self.players = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Track unique players for showdown deduplication
                unique_players = {}

                for row in reader:
                    try:
                        # Create player from CSV data
                        player = self._create_player_from_csv(row)

                        if player:
                            if self.contest_type == "showdown":
                                # For showdown, only keep UTIL entries
                                roster_position = row.get('Roster Position', '')
                                if roster_position != 'CPT':
                                    # Store by name to avoid duplicates
                                    unique_players[player.name] = player
                            else:
                                # For classic, add all players
                                self.players.append(player)

                    except Exception as e:
                        logger.error(f"Error creating player from row: {e}")
                        continue

                # For showdown, add unique players
                if self.contest_type == "showdown":
                    self.players = list(unique_players.values())

            # Validate loaded data
            if self.validator and self.modules_status.get('validator'):
                validation_result = self.validator.validate_players(self.players)
                if not validation_result.is_valid:
                    print(f"  ⚠️  Validation warnings: {len(validation_result.warnings)}")

            print(f"✅ Loaded {len(self.players)} players")
            print(f"  Contest Type: {self.contest_type}")

            if self.contest_type == "showdown":
                print(f"  ℹ️  Using UTIL entries only (CPT entries filtered out)")

            # Clear caches when new data is loaded
            self.clear_cache()

            return len(self.players)

        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            print(f"❌ Error loading CSV: {e}")
            return 0

    def _create_player_from_csv(self, row: Dict[str, str]) -> Optional[UnifiedPlayer]:
        """Create UnifiedPlayer from CSV row"""
        try:
            # Extract basic info
            name = row.get('Name', '').strip()
            if not name:
                return None

            # Get positions
            position_str = row.get('Position', '')
            positions = position_str.split('/') if position_str else []

            # Handle roster position for showdown
            roster_position = row.get('Roster Position', position_str)
            if self.contest_type == "showdown" and roster_position == 'CPT':
                # Skip captain entries for showdown
                return None

            # Create player
            player = UnifiedPlayer(
                name=name,
                team=row.get('TeamAbbrev', row.get('Team', '')),
                opponent=row.get('Opp', ''),
                salary=int(float(row.get('Salary', 0))),
                positions=positions,
                game_info=row.get('Game Info', ''),
                slate_id=row.get('Slate ID', ''),
                player_id=row.get('ID', f"{name}_{row.get('Team', '')}")
            )

            # Set primary position
            player.primary_position = roster_position if roster_position != 'FLEX' else positions[0]

            # Set base projection
            player.base_projection = float(row.get('AvgPointsPerGame', row.get('Projection', 0)))

            # Extract additional data
            if row.get('Confirmed') == 'Yes':
                player.is_confirmed = True

            return player

        except Exception as e:
            logger.error(f"Error creating player {row.get('Name', 'Unknown')}: {e}")
            return None

    def enrich_player_data(self) -> int:
        """Enrich player data with external sources - for ALL contest types"""
        print(f"\n🔄 Enriching Player Data for {self.contest_type.upper()} mode...")

        if not self.players:
            print("  ❌ No players to enrich")
            return 0

        enriched_count = 0
        start_time = time.time()

        # 1. Vegas data enrichment (for both classic and showdown)
        if self.vegas_lines and self.modules_status.get('vegas_lines'):
            try:
                print("  📊 Fetching Vegas lines...")
                unique_teams = set(p.team for p in self.players if p.team)
                vegas_count = 0
                for team in unique_teams:
                    vegas_data = self.vegas_lines.get_team_data(team)
                    if vegas_data:
                        # Apply to all players on that team
                        for player in self.players:
                            if player.team == team:
                                player.vegas_data = vegas_data
                                player._vegas_data = vegas_data  # For scoring engine
                                vegas_count += 1
                print(f"     ✓ Applied Vegas data to {vegas_count} players")
                enriched_count += vegas_count
            except Exception as e:
                logger.error(f"Vegas enrichment failed: {e}")

        # 2. Statcast enrichment (valuable for showdown captain selection)
        if self.statcast_fetcher and self.modules_status.get('statcast'):
            try:
                print("  ⚾ Fetching Statcast data...")
                # For showdown, prioritize high-projection players
                if self.contest_type == "showdown":
                    # Get top players by base projection for Statcast data
                    top_players = sorted(self.players, key=lambda p: p.base_projection, reverse=True)[:20]
                    player_names = [p.name for p in top_players]
                else:
                    player_names = [p.name for p in self.players]

                statcast_data = self.statcast_fetcher.fetch_all_players(player_names)
                statcast_count = 0
                for player in self.players:
                    if player.name in statcast_data:
                        player.statcast_data = statcast_data[player.name]
                        player._statcast_data = statcast_data[player.name]  # For scoring engine
                        statcast_count += 1
                print(f"     ✓ Applied Statcast data to {statcast_count} players")
                enriched_count += statcast_count
            except Exception as e:
                logger.error(f"Statcast enrichment failed: {e}")

        # 3. Advanced score calculation - CRITICAL for both modes
        if self.scoring_engine and self.modules_status.get('scoring_engine'):
            try:
                print("  💯 Calculating enhanced scores with advanced metrics...")
                scored_count = 0
                high_value_players = []

                for player in self.players:
                    # Calculate advanced score using all available data
                    score = self.scoring_engine.calculate_score(player)
                    player.enhanced_score = score
                    player.optimization_score = score  # Used by optimizer

                    if score > 0:
                        scored_count += 1

                        # Track high-value players for showdown captain consideration
                        if score > player.base_projection * 1.15:
                            boost_pct = ((score / player.base_projection) - 1) * 100
                            high_value_players.append((player, boost_pct))

                # Report high-value findings
                if high_value_players and self.contest_type == "showdown":
                    print(f"\n  🎯 Top Captain Candidates (based on advanced metrics):")
                    for player, boost in sorted(high_value_players, key=lambda x: x[1], reverse=True)[:5]:
                        print(f"     {player.name}: +{boost:.0f}% vs base projection")

                print(f"     ✓ Calculated advanced scores for {scored_count} players")
            except Exception as e:
                logger.error(f"Score calculation failed: {e}")
                # Fallback to base projections only if scoring engine fails
                print("  ⚠️  Using base projections as fallback")
                for player in self.players:
                    if not hasattr(player, 'optimization_score') or player.optimization_score == 0:
                        player.optimization_score = player.base_projection

        elapsed = time.time() - start_time
        print(f"\n✅ Enrichment complete: {enriched_count} data points added in {elapsed:.1f}s")
        print(f"   Contest Type: {self.contest_type.upper()}")
        print(
            f"   Players with enhanced scores: {sum(1 for p in self.players if getattr(p, 'optimization_score', 0) > 0)}")

        return enriched_count

    def optimize_lineup(self, manual_selections: str = "") -> Tuple[List[UnifiedPlayer], float]:
        """Optimize lineup based on contest type"""
        if self.contest_type == "showdown":
            return self.optimize_showdown_lineup(manual_selections)
        else:
            return self.optimize_classic_lineup(manual_selections)

    def optimize_classic_lineup(self, manual_selections: str = "") -> Tuple[List[UnifiedPlayer], float]:
        """Optimize classic lineup"""
        print(f"\n🎯 OPTIMIZING CLASSIC LINEUP")
        print(f"Strategy: {self.optimization_mode}")
        print("=" * 60)

        if not self.players:
            print("❌ No players loaded!")
            return [], 0

        # Parse manual selections
        manual_players = []
        if manual_selections:
            manual_names = [name.strip().lower() for name in manual_selections.split(',')]
            for player in self.players:
                if player.name.lower() in manual_names:
                    player.is_manual_selected = True
                    manual_players.append(player.name)

        print(f"  📌 Manual selections: {len(manual_players)}")

        # Run optimization
        result = self._optimize_unified(self.optimization_mode, manual_players)

        if result and result['lineup']:
            lineup = result['lineup']
            score = result['total_projection']

            # Display results
            self._display_lineup_results(lineup, score, result)

            return lineup, score
        else:
            print("❌ Optimization failed!")
            return [], 0

    def optimize_showdown_lineup(self, manual_selections: str = "") -> Tuple[List[UnifiedPlayer], float]:
        """Optimize showdown lineup with proper captain selection"""
        print(f"\n🎰 OPTIMIZING SHOWDOWN LINEUP")
        print("=" * 60)

        if len(self.players) < 6:
            print(f"❌ Not enough players for showdown: {len(self.players)} (need 6)")
            return [], 0

        # Create the showdown-specific optimizer
        if not self.optimizer:
            print("❌ Optimizer not available!")
            return [], 0

        try:
            # Use a showdown-specific optimization
            prob = self._create_showdown_problem()

            if prob is None:
                print("❌ Failed to create showdown problem")
                return [], 0

            # Solve the problem
            prob.solve()

            if prob.status == 1:  # Optimal solution found
                lineup = self._extract_showdown_lineup(prob)
                total_score = sum(p.optimization_score * getattr(p, 'multiplier', 1.0) for p in lineup)

                # Display results
                print("\n✅ SHOWDOWN LINEUP OPTIMIZED")
                print("=" * 60)

                for player in lineup:
                    position = getattr(player, 'assigned_position', 'UTIL')
                    multiplier = getattr(player, 'multiplier', 1.0)
                    adjusted_salary = int(player.salary * multiplier) if position == 'CPT' else player.salary
                    adjusted_score = player.optimization_score * multiplier

                    print(f"{position:4} | {player.name:20} | {player.team:3} | "
                          f"${adjusted_salary:,} | {adjusted_score:.1f} pts")

                total_salary = sum(
                    int(p.salary * getattr(p, 'multiplier', 1.0)) if getattr(p, 'assigned_position', '') == 'CPT'
                    else p.salary for p in lineup
                )

                print("-" * 60)
                print(f"Total Salary: ${total_salary:,} / ${self.salary_cap:,}")
                print(f"Total Score: {total_score:.1f}")

                return lineup, total_score
            else:
                print("❌ No optimal showdown lineup found")
                return self._greedy_showdown_fallback(manual_selections)

        except Exception as e:
            logger.error(f"Showdown optimization error: {e}")
            print(f"❌ Showdown optimization failed: {e}")
            return self._greedy_showdown_fallback(manual_selections)

    def _create_showdown_problem(self):
        """Create MILP problem for showdown optimization"""
        try:
            import pulp

            # Create problem
            prob = pulp.LpProblem("DFS_Showdown", pulp.LpMaximize)

            # Decision variables
            # x[i,j] = 1 if player i is selected for role j (0=captain, 1=utility)
            x = {}
            for i, player in enumerate(self.players):
                x[i, 0] = pulp.LpVariable(f"captain_{i}", cat="Binary")
                x[i, 1] = pulp.LpVariable(f"util_{i}", cat="Binary")

                # Store the variables on the player for extraction
                player._captain_var = x[i, 0]
                player._util_var = x[i, 1]
                player._index = i

            # Objective: Maximize total score (captain gets 1.5x) using ENHANCED scores
            prob += pulp.lpSum([
                x[i, 0] * getattr(self.players[i], 'optimization_score',
                                  self.players[i].base_projection) * 1.5 +  # Captain score
                x[i, 1] * getattr(self.players[i], 'optimization_score', self.players[i].base_projection)
                # Utility score
                for i in range(len(self.players))
            ])

            # Constraint 1: Exactly 1 captain
            prob += pulp.lpSum([x[i, 0] for i in range(len(self.players))]) == 1

            # Constraint 2: Exactly 5 utility players
            prob += pulp.lpSum([x[i, 1] for i in range(len(self.players))]) == 5

            # Constraint 3: Each player can only be selected once (as captain OR utility)
            for i in range(len(self.players)):
                prob += x[i, 0] + x[i, 1] <= 1

            # Constraint 4: Salary cap (captain costs 1.5x)
            prob += pulp.lpSum([
                x[i, 0] * self.players[i].salary * 1.5 +  # Captain salary
                x[i, 1] * self.players[i].salary  # Utility salary
                for i in range(len(self.players))
            ]) <= self.salary_cap

            # Constraint 5: Must have players from both teams (if multiple teams)
            teams = list(set(p.team for p in self.players if p.team))
            if len(teams) >= 2:
                for team in teams[:2]:  # Ensure at least one from each team
                    team_indices = [i for i, p in enumerate(self.players) if p.team == team]
                    if team_indices:
                        prob += pulp.lpSum([x[i, 0] + x[i, 1] for i in team_indices]) >= 1

            return prob

        except Exception as e:
            logger.error(f"Failed to create showdown problem: {e}")
            return None

    def _extract_showdown_lineup(self, prob):
        """Extract lineup from solved showdown problem"""
        lineup = []

        for player in self.players:
            if hasattr(player, '_captain_var') and player._captain_var.varValue == 1:
                # Captain
                player.assigned_position = 'CPT'
                player.multiplier = 1.5
                lineup.append(player)
            elif hasattr(player, '_util_var') and player._util_var.varValue == 1:
                # Utility
                player.assigned_position = 'UTIL'
                player.multiplier = 1.0
                lineup.append(player)

        # Sort: Captain first, then utilities
        lineup.sort(key=lambda p: 0 if p.assigned_position == 'CPT' else 1)

        return lineup

    def _greedy_showdown_fallback(self, manual_selections: str = "") -> Tuple[List[UnifiedPlayer], float]:
        """Greedy fallback for showdown lineup"""
        print("  🔄 Using greedy showdown fallback...")

        # Sort players by value using ENHANCED scores (points per dollar)
        players_by_value = sorted(
            self.players,
            key=lambda p: getattr(p, 'optimization_score', p.base_projection) / max(p.salary, 1),
            reverse=True
        )

        best_lineup = []
        best_score = 0

        # Try each player as captain
        for captain in players_by_value[:20]:  # Only try top 20 as captain
            if captain.salary * 1.5 > self.salary_cap:
                continue

            lineup = []
            remaining_salary = self.salary_cap - int(captain.salary * 1.5)
            used_names = {captain.name}

            # Add captain
            captain_copy = UnifiedPlayer(
                name=captain.name,
                team=captain.team,
                opponent=captain.opponent,
                salary=captain.salary,
                positions=captain.positions
            )
            captain_copy.optimization_score = getattr(captain, 'optimization_score', captain.base_projection)
            captain_copy.enhanced_score = getattr(captain, 'enhanced_score', captain.base_projection)
            captain_copy.assigned_position = 'CPT'
            captain_copy.multiplier = 1.5
            lineup.append(captain_copy)

            # Add best fitting utilities
            for player in players_by_value:
                if len(lineup) >= 6:
                    break

                if player.name in used_names or player.salary > remaining_salary:
                    continue

                util_copy = UnifiedPlayer(
                    name=player.name,
                    team=player.team,
                    opponent=player.opponent,
                    salary=player.salary,
                    positions=player.positions
                )
                util_copy.optimization_score = getattr(player, 'optimization_score', player.base_projection)
                util_copy.enhanced_score = getattr(player, 'enhanced_score', player.base_projection)
                util_copy.assigned_position = 'UTIL'
                util_copy.multiplier = 1.0
                lineup.append(util_copy)
                remaining_salary -= player.salary
                used_names.add(player.name)

            if len(lineup) == 6:
                total_score = sum(p.optimization_score * p.multiplier for p in lineup)
                if total_score > best_score:
                    best_score = total_score
                    best_lineup = lineup

        return best_lineup, best_score

    def _optimize_unified(self, strategy: str, manual_players: List[str]) -> Optional[Dict]:
        """Optimize using unified MILP optimizer"""
        print("  🎯 Using UNIFIED optimization")

        try:
            # Run optimization
            lineup, score = self.optimizer.optimize_lineup(
                self.players,
                strategy=strategy,
                manual_selections=','.join(manual_players)
            )

            if not lineup:
                return None

            # Calculate totals
            total_salary = sum(p.salary for p in lineup)
            total_projection = sum(getattr(p, 'optimization_score', p.base_projection) for p in lineup)

            return {
                'lineup': lineup,
                'total_salary': total_salary,
                'total_projection': total_projection,
                'salary_used': total_salary / self.salary_cap,
                'strategy': strategy,
                'optimization_method': 'unified',
                'player_count': len(lineup)
            }

        except Exception as e:
            logger.error(f"Unified optimization error: {e}")
            print(f"  ⚠️  Unified optimization failed: {e}")
            return None

    def _display_lineup_results(self, lineup: List[UnifiedPlayer], score: float, result: Dict):
        """Display lineup results"""
        print("\n✅ LINEUP OPTIMIZED")
        print("=" * 60)

        # Display players
        for player in lineup:
            proj = getattr(player, 'optimization_score', player.base_projection)
            value = proj / (player.salary / 1000) if player.salary > 0 else 0

            print(f"{player.primary_position:3} | {player.name:20} | "
                  f"{player.team:3} | ${player.salary:,} | "
                  f"{proj:.1f} pts | {value:.2f} val")

        print("-" * 60)
        print(f"Total Salary: ${result['total_salary']:,} / ${self.salary_cap:,} "
              f"({result['salary_used']:.1%})")
        print(f"Total Projection: {result['total_projection']:.1f} pts")
        print(f"Strategy: {result['strategy']}")
        print(f"Method: {result['optimization_method']}")
        print("=" * 60)

    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            'initialized': True,
            'mode': self.mode,
            'contest_type': self.contest_type,
            'unified_mode': self.unified_mode,
            'modules': self.modules_status,
            'players_loaded': len(self.players),
            'players_scored': sum(1 for p in self.players if getattr(p, 'optimization_score', 0) > 0),
            'confirmed_players': sum(1 for p in self.players if getattr(p, 'is_confirmed', False)),
            'stats': {
                'total_players': len(self.players),
                'manual_selections': sum(1 for p in self.players if getattr(p, 'is_manual_selected', False))
            }
        }

    def clear_cache(self):
        """Clear all caches"""
        self._lineup_cache.clear()
        self._score_cache.clear()
        logger.info("All caches cleared")
        print("✅ Caches cleared")


# Factory function
def create_bulletproof_core(mode: str = "production", contest_type: str = "classic") -> BulletproofDFSCore:
    """Create a new BulletproofDFSCore instance"""
    return BulletproofDFSCore(mode=mode, contest_type=contest_type)


if __name__ == "__main__":
    print("✅ BulletproofDFSCore V2 with Showdown Mode loaded successfully")