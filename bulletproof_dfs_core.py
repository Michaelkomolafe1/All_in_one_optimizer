#!/usr/bin/env python3
"""
BULLETPROOF DFS CORE V2 - COMPLETE REWRITE
==========================================
Enhanced version with better error handling, performance, and integration
"""

import os
import warnings
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

import pandas as pd

# Suppress warnings
warnings.filterwarnings("ignore")

# ============================================================================
# LOGGING SETUP
# ============================================================================
try:
    from logging_config import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# ============================================================================
# IMPORTS WITH INTELLIGENT FALLBACKS
# ============================================================================

# Configuration
try:
    from unified_config_manager import get_config_value

    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False


    def get_config_value(key, default):
        return default

# Performance
try:
    from performance_config import get_performance_settings

    PERFORMANCE_CONFIG_AVAILABLE = True
except ImportError:
    PERFORMANCE_CONFIG_AVAILABLE = False

# Core modules
MODULES = {
    'scoring_engine': {
        'available': False,
        'import': 'from unified_scoring_engine import get_scoring_engine',
        'instance': None
    },
    'validator': {
        'available': False,
        'import': 'from data_validator import get_validator',
        'instance': None
    },
    'performance_optimizer': {
        'available': False,
        'import': 'from performance_optimizer import get_performance_optimizer, CacheConfig',
        'instance': None
    },
    'unified_optimizer': {
        'available': False,
        'import': 'from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig',
        'instance': None
    },
    'unified_player': {
        'available': False,
        'import': 'from unified_player_model import UnifiedPlayer',
        'instance': None
    },
    'vegas_lines': {
        'available': False,
        'import': 'from vegas_lines import VegasLines',
        'instance': None
    },
    'statcast': {
        'available': False,
        'import': 'from simple_statcast_fetcher import SimpleStatcastFetcher',
        'instance': None
    },
    'confirmation': {
        'available': False,
        'import': 'from smart_confirmation_system import SmartConfirmationSystem',
        'instance': None
    }
}

# Dynamic imports
for module_name, module_info in MODULES.items():
    try:
        exec(module_info['import'])
        module_info['available'] = True
    except ImportError:
        module_info['available'] = False

# Extract availability flags for convenience
UNIFIED_OPTIMIZER_AVAILABLE = MODULES['unified_optimizer']['available']
UNIFIED_PLAYER_AVAILABLE = MODULES['unified_player']['available']
SCORING_ENGINE_AVAILABLE = MODULES['scoring_engine']['available']
VALIDATOR_AVAILABLE = MODULES['validator']['available']
PERFORMANCE_OPTIMIZER_AVAILABLE = MODULES['performance_optimizer']['available']


class BulletproofDFSCore:
    """
    Enhanced DFS optimization system with improved error handling and performance
    """

    def __init__(self, mode: str = "production"):
        """
        Initialize the core system

        Args:
            mode: 'production' or 'test' mode
        """
        self.mode = mode
        self.logger = logger

        # Display initialization header
        self._display_init_header()

        # Core attributes
        self.salary_cap = 50000
        self.min_salary_usage = 0.95
        self.contest_type = "classic"
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

        # 4. Set unified mode flag
        self.unified_mode = all([
            self.modules_status.get('scoring_engine', False),
            self.modules_status.get('unified_optimizer', False),
            self.modules_status.get('validator', False)
        ])

    def _load_configuration(self):
        """Load system configuration"""
        print("\n📋 Loading Configuration...")

        if CONFIG_AVAILABLE:
            try:
                self.salary_cap = get_config_value("optimization.salary_cap", 50000)
                self.min_salary_usage = get_config_value("optimization.min_salary_usage", 0.95)
                self.contest_type = get_config_value("contest.type", "classic")
                print("  ✅ Configuration loaded from unified config manager")
            except Exception as e:
                logger.warning(f"Config manager error: {e}, using defaults")
                print("  ⚠️  Using default configuration")
        else:
            # Try JSON fallback
            try:
                import json
                with open("dfs_config.json", "r") as f:
                    config = json.load(f)
                    self.salary_cap = config.get("optimization", {}).get("salary_cap", 50000)
                    print("  ✅ Configuration loaded from dfs_config.json")
            except:
                print("  ℹ️  Using default configuration")

    def _initialize_core_modules(self):
        """Initialize core optimization modules"""
        print("\n🔧 Initializing Core Modules...")

        # Scoring Engine
        if SCORING_ENGINE_AVAILABLE:
            try:
                self.scoring_engine = get_scoring_engine()
                self.modules_status['scoring_engine'] = True
                print("  ✅ Unified Scoring Engine")
            except Exception as e:
                logger.error(f"Scoring engine initialization failed: {e}")
                self.scoring_engine = None
                self.modules_status['scoring_engine'] = False
                print(f"  ❌ Scoring Engine: {str(e)[:50]}...")

        # Data Validator
        if VALIDATOR_AVAILABLE:
            try:
                self.validator = get_validator()
                self.modules_status['validator'] = True
                print("  ✅ Data Validator")
            except Exception as e:
                logger.error(f"Validator initialization failed: {e}")
                self.validator = None
                self.modules_status['validator'] = False
                print(f"  ❌ Validator: {str(e)[:50]}...")

        # Performance Optimizer
        if PERFORMANCE_OPTIMIZER_AVAILABLE:
            try:
                if PERFORMANCE_CONFIG_AVAILABLE:
                    perf_settings = get_performance_settings()
                    cache_config = CacheConfig(
                        max_size=perf_settings.cache_settings['memory_cache_size'],
                        enable_disk_cache=perf_settings.cache_settings['disk_cache_enabled']
                    )
                else:
                    cache_config = CacheConfig()

                self.performance_optimizer = get_performance_optimizer(cache_config)
                self.modules_status['performance_optimizer'] = True
                print("  ✅ Performance Optimizer")
            except Exception as e:
                logger.error(f"Performance optimizer initialization failed: {e}")
                self.performance_optimizer = None
                self.modules_status['performance_optimizer'] = False
                print(f"  ❌ Performance Optimizer: {str(e)[:50]}...")

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
                print(f"  ❌ MILP Optimizer: {str(e)[:50]}...")

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
                print(f"  ❌ Vegas Lines: {str(e)[:50]}...")

        # Confirmation System
        if MODULES['confirmation']['available']:
            try:
                self.confirmation_system = SmartConfirmationSystem()
                self.modules_status['confirmation'] = True
                print("  ✅ Confirmation System")
            except Exception as e:
                logger.error(f"Confirmation system initialization failed: {e}")
                self.confirmation_system = None
                self.modules_status['confirmation'] = False
                print(f"  ❌ Confirmation System: {str(e)[:50]}...")

        # Statcast
        if MODULES['statcast']['available']:
            try:
                self.statcast_fetcher = SimpleStatcastFetcher()
                self.modules_status['statcast'] = True
                print("  ✅ Statcast Fetcher")
            except Exception as e:
                logger.error(f"Statcast initialization failed: {e}")
                self.statcast_fetcher = None
                self.modules_status['statcast'] = False
                print(f"  ❌ Statcast: {str(e)[:50]}...")

    def _display_init_summary(self):
        """Display initialization summary"""
        print("\n" + "=" * 60)
        print("📈 INITIALIZATION COMPLETE")
        print("-" * 60)
        print(f"Mode: {'🎯 UNIFIED' if self.unified_mode else '📊 HYBRID'}")
        print(f"Salary Cap: ${self.salary_cap:,}")
        print(f"Min Salary: {self.min_salary_usage:.0%}")

        active_modules = sum(1 for v in self.modules_status.values() if v)
        total_modules = len(self.modules_status)
        print(f"Modules: {active_modules}/{total_modules} active")
        print("=" * 60 + "\n")

    def load_draftkings_csv(self, filepath: str, force_reload: bool = False) -> int:
        """
        Load and process DraftKings CSV file

        Args:
            filepath: Path to CSV file
            force_reload: Force reload even if already loaded

        Returns:
            Number of players loaded
        """
        # Check if already loaded
        if not force_reload and self.csv_file_path == filepath and self.players:
            logger.info(f"Using cached CSV data for {filepath}")
            return len(self.players)

        print(f"\n📂 Loading CSV: {os.path.basename(filepath)}")
        logger.info(f"Loading CSV file: {filepath}")

        try:
            # Validate file exists
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"CSV file not found: {filepath}")

            # Read CSV with error handling
            try:
                df = pd.read_csv(filepath, encoding='utf-8-sig')
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding='latin-1')

            if df.empty:
                raise ValueError("CSV file is empty")

            print(f"  📊 Found {len(df)} rows")

            # Clear existing data
            self.players.clear()
            self._lineup_cache.clear()
            self._score_cache.clear()

            # Process players
            if self.unified_mode and UNIFIED_PLAYER_AVAILABLE:
                self._process_players_unified(df)
            else:
                self._process_players_hybrid(df)

            # Store filepath
            self.csv_file_path = filepath

            # Update external systems
            self._update_external_systems()

            print(f"  ✅ Loaded {len(self.players)} valid players")
            logger.info(f"Successfully loaded {len(self.players)} players")

            return len(self.players)

        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            print(f"  ❌ Error: {e}")
            return 0
        except pd.errors.EmptyDataError:
            logger.error("CSV file is empty")
            print("  ❌ Error: CSV file is empty")
            return 0
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            print(f"  ❌ Error: {e}")
            return 0

    def _process_players_unified(self, df: pd.DataFrame):
        """Process players using unified player model"""
        print("  🎯 Using UNIFIED player model")

        for idx, row in df.iterrows():
            try:
                # Create unified player
                player = UnifiedPlayer(
                    id=f"{row.get('ID', f'player_{idx}')}",
                    name=str(row.get('Name', 'Unknown')).strip(),
                    team=str(row.get('TeamAbbrev', 'UNK')).strip().upper(),
                    salary=int(row.get('Salary', 0)),
                    primary_position=str(row.get('Position', 'UTIL')).strip().upper(),
                    positions=str(row.get('Position', 'UTIL')).strip().upper().split('/'),
                    base_projection=float(row.get('AvgPointsPerGame', 0))
                )

                # Add additional data
                if 'Game Info' in row:
                    player.game_info = str(row['Game Info'])

                # Validate if validator available
                if self.validator:
                    result = self.validator.validate_player(player)
                    if not result.is_valid:
                        logger.debug(f"Player {player.name} failed validation: {result.errors}")
                        continue

                self.players.append(player)
                logger.debug(f"Loaded player: {player.name} - ${player.salary} - {player.base_projection:.1f} pts")

            except Exception as e:
                logger.warning(f"Error processing player at row {idx}: {e}")
                continue

    def _process_players_hybrid(self, df: pd.DataFrame):
        """Process players using hybrid approach"""
        print("  📊 Using HYBRID player model")

        # Create wrapper class for compatibility
        class HybridPlayer:
            def __init__(self, data: dict):
                self.name = data['name']
                self.team = data['team']
                self.salary = data['salary']
                self.primary_position = data['position']
                self.positions = [data['position']]
                self.base_projection = data['projected_points']
                self.enhanced_score = data['projected_points']
                self.optimization_score = data['projected_points']
                self.is_confirmed = False
                self.is_manual_selected = False
                self._data = data

            def __getattr__(self, name):
                return self._data.get(name)

        for idx, row in df.iterrows():
            try:
                player_data = {
                    'name': str(row.get('Name', 'Unknown')).strip(),
                    'team': str(row.get('TeamAbbrev', 'UNK')).strip().upper(),
                    'salary': int(row.get('Salary', 0)),
                    'position': str(row.get('Position', 'UTIL')).strip().upper(),
                    'projected_points': float(row.get('AvgPointsPerGame', 0)),
                    'game_info': str(row.get('Game Info', ''))
                }

                # Basic validation
                if player_data['salary'] <= 0 or player_data['projected_points'] < 0:
                    continue

                player = HybridPlayer(player_data)
                self.players.append(player)

            except Exception as e:
                logger.warning(f"Error processing player at row {idx}: {e}")
                continue

    def _update_external_systems(self):
        """Update external systems with loaded players"""
        # Update confirmation system
        if hasattr(self, 'confirmation_system') and self.confirmation_system:
            try:
                self.confirmation_system.update_csv_players(self.players)
                print("  ✅ Updated confirmation system")
            except Exception as e:
                logger.warning(f"Could not update confirmation system: {e}")

        # Update validator
        if hasattr(self, 'validator') and self.validator:
            try:
                self.validator.update_salary_range_from_players(self.players)
                print("  ✅ Updated validator salary ranges")
            except Exception as e:
                logger.warning(f"Could not update validator: {e}")

    def optimize_lineup(self,
                        strategy: str = "balanced",
                        manual_selections: str = "",
                        use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Optimize lineup with given strategy

        Args:
            strategy: Optimization strategy
            manual_selections: Comma-separated player names
            use_cache: Whether to use cached results

        Returns:
            Optimization result dictionary or None
        """
        print(f"\n🎯 OPTIMIZING LINEUP")
        print(f"Strategy: {strategy.upper()}")
        print(f"Manual Selections: {manual_selections if manual_selections else 'None'}")

        logger.info(f"OPTIMIZATION: Starting with strategy: {strategy}")
        logger.info(f"OPTIMIZATION: Players available: {len(self.players)}")
        logger.info(f"OPTIMIZATION: Manual selections: {manual_selections}")

        # Validate inputs
        if not self.players:
            logger.error("No players loaded")
            print("  ❌ Error: No players loaded. Load CSV first.")
            return None

        # Check cache
        cache_key = (strategy, manual_selections, len(self.players))
        if use_cache and cache_key in self._lineup_cache:
            cached_result, cache_time = self._lineup_cache[cache_key]
            if (datetime.now() - cache_time).seconds < 300:  # 5 min cache
                logger.info("PERFORMANCE: Using cached lineup result")
                print("  ⚡ Using cached result")
                return cached_result

        try:
            # Process manual selections
            manual_players = self._process_manual_selections(manual_selections)

            # Choose optimization method
            if self.unified_mode and hasattr(self, 'optimizer'):
                result = self._optimize_unified(strategy, manual_players)
            else:
                result = self._optimize_fallback(strategy, manual_players)

            # Cache result
            if result and use_cache:
                self._lineup_cache[cache_key] = (result, datetime.now())

            # Display result summary
            if result:
                self._display_optimization_summary(result)

            return result

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            print(f"  ❌ Optimization failed: {e}")
            return None

    def _process_manual_selections(self, manual_selections: str) -> List[str]:
        """Process manual selection string"""
        if not manual_selections:
            return []

        manual_names = []
        for name in manual_selections.split(','):
            name = name.strip()
            if name:
                manual_names.append(name.lower())

        # Mark selected players
        selected_count = 0
        for player in self.players:
            if player.name.lower() in manual_names:
                player.is_manual_selected = True
                selected_count += 1
            else:
                player.is_manual_selected = False

        if selected_count > 0:
            print(f"  📌 Marked {selected_count} manual selections")

        return manual_names

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
            return self._optimize_fallback(strategy, manual_players)

    def _optimize_fallback(self, strategy: str, manual_players: List[str]) -> Optional[Dict]:
        """Fallback optimization method"""
        print("  📊 Using FALLBACK optimization")

        try:
            # Simple greedy algorithm
            position_requirements = {
                'P': 2, 'C': 1, '1B': 1, '2B': 1,
                '3B': 1, 'SS': 1, 'OF': 3
            }

            lineup = []
            used_salary = 0
            positions_filled = {pos: 0 for pos in position_requirements}

            # Sort players by value (points per dollar)
            sorted_players = sorted(
                self.players,
                key=lambda p: getattr(p, 'base_projection', 0) / max(p.salary, 1),
                reverse=True
            )

            # First, add manual selections
            for player in sorted_players:
                if getattr(player, 'is_manual_selected', False):
                    pos = player.primary_position
                    if pos in positions_filled and positions_filled[pos] < position_requirements.get(pos, 0):
                        if used_salary + player.salary <= self.salary_cap:
                            lineup.append(player)
                            used_salary += player.salary
                            positions_filled[pos] += 1

            # Then fill remaining positions
            for player in sorted_players:
                if player in lineup:
                    continue

                pos = player.primary_position
                if pos in positions_filled and positions_filled[pos] < position_requirements.get(pos, 0):
                    if used_salary + player.salary <= self.salary_cap * 0.98:  # Leave some buffer
                        lineup.append(player)
                        used_salary += player.salary
                        positions_filled[pos] += 1

            # Check if valid lineup
            total_required = sum(position_requirements.values())
            if len(lineup) < total_required:
                logger.warning(f"Could only create lineup with {len(lineup)} players")
                return None

            total_projection = sum(getattr(p, 'base_projection', 0) for p in lineup)

            return {
                'lineup': lineup,
                'total_salary': used_salary,
                'total_projection': total_projection,
                'salary_used': used_salary / self.salary_cap,
                'strategy': strategy,
                'optimization_method': 'fallback',
                'player_count': len(lineup)
            }

        except Exception as e:
            logger.error(f"Fallback optimization error: {e}")
            return None

    def _display_optimization_summary(self, result: Dict):
        """Display optimization result summary"""
        print(f"\n✅ OPTIMIZATION COMPLETE")
        print(f"  Method: {result['optimization_method'].upper()}")
        print(f"  Players: {result['player_count']}")
        print(f"  Salary: ${result['total_salary']:,} ({result['salary_used']:.1%} used)")
        print(f"  Projection: {result['total_projection']:.1f} points")

        # Log lineup details
        logger.info(f"LINEUP SELECTED: Score={result['total_projection']:.1f}, Salary=${result['total_salary']:,}")
        for player in result['lineup']:
            score = getattr(player, 'optimization_score', player.base_projection)
            logger.info(f"  LINEUP: {player.primary_position} - {player.name} - ${player.salary} - {score:.1f} pts")

    def detect_confirmed_players(self) -> int:
        """Detect and mark confirmed players"""
        if not hasattr(self, 'confirmation_system') or not self.confirmation_system:
            logger.warning("No confirmation system available")
            return 0

        print("\n🔍 Detecting Confirmed Players...")

        try:
            confirmed_count = 0

            for player in self.players:
                if player.primary_position == 'P':
                    is_confirmed, source = self.confirmation_system.is_pitcher_confirmed(
                        player.name, player.team
                    )
                else:
                    is_confirmed, batting_order = self.confirmation_system.is_player_confirmed(
                        player.name, player.team
                    )
                    if is_confirmed and batting_order:
                        player.batting_order = batting_order

                if is_confirmed:
                    player.is_confirmed = True
                    confirmed_count += 1

            print(f"  ✅ Confirmed {confirmed_count} players")
            return confirmed_count

        except Exception as e:
            logger.error(f"Error detecting confirmed players: {e}")
            print(f"  ❌ Error: {e}")
            return 0

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'initialized': True,
            'mode': self.mode,
            'unified_mode': self.unified_mode,
            'players_loaded': len(self.players),
            'csv_file': self.csv_file_path,
            'salary_cap': self.salary_cap,
            'modules': self.modules_status,
            'cache_size': len(self._lineup_cache),
            'stats': {
                'total_players': len(self.players),
                'confirmed_players': sum(1 for p in self.players if getattr(p, 'is_confirmed', False)),
                'manual_selections': sum(1 for p in self.players if getattr(p, 'is_manual_selected', False))
            }
        }

    def clear_cache(self):
        """Clear all caches"""
        self._lineup_cache.clear()
        self._score_cache.clear()
        logger.info("All caches cleared")
        print("✅ Caches cleared")


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_bulletproof_core(mode: str = "production") -> BulletproofDFSCore:
    """Create a new BulletproofDFSCore instance"""
    return BulletproofDFSCore(mode=mode)


def verify_system() -> bool:
    """Verify system functionality"""
    try:
        core = BulletproofDFSCore(mode="test")
        status = core.get_system_status()

        print("\n🔍 SYSTEM VERIFICATION")
        print("=" * 60)
        print(f"Status: {'✅ OPERATIONAL' if status['initialized'] else '❌ FAILED'}")
        print(f"Mode: {status['mode']}")
        print(f"Unified: {'Yes' if status['unified_mode'] else 'No'}")
        print(f"Modules: {sum(1 for v in status['modules'].values() if v)}/{len(status['modules'])}")
        print("=" * 60)

        return status['initialized']

    except Exception as e:
        print(f"❌ System verification failed: {e}")
        return False


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("✅ BulletproofDFSCore V2 module loaded successfully")
    print("\n📚 Quick Start:")
    print("  from bulletproof_dfs_core import BulletproofDFSCore")
    print("  core = BulletproofDFSCore()")
    print("  core.load_draftkings_csv('your_file.csv')")
    print("  result = core.optimize_lineup('balanced')")

    # Run verification
    print("\nRunning system verification...")
    if verify_system():
        print("\n✅ All systems operational!")
    else:
        print("\n⚠️  Some systems need attention")