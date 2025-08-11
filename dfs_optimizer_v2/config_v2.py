#!/usr/bin/env python3
"""
UNIFIED CONFIGURATION V2
========================
All configuration in ONE place - no more sprawl
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DFSConfig:
    """Complete DFS configuration"""

    # =====================================
    # OPTIMIZER SETTINGS
    # =====================================

    # Salary constraints
    SALARY_CAP: int = 50000
    MIN_SALARY: Dict[str, int] = None

    # Position requirements (DraftKings)
    POSITION_REQUIREMENTS: Dict[str, int] = None

    # Team constraints
    MAX_PER_TEAM: Dict[str, int] = None

    # Solver settings
    SOLVER_TIMEOUT: int = 30
    MAX_LINEUPS: int = 150

    # =====================================
    # SCORING PARAMETERS
    # =====================================

    # GPP scoring thresholds
    GPP_HIGH_TOTAL: float = 5.0  # Teams scoring 5+ runs
    GPP_TEAM_BOOST: float = 1.15  # 15% boost
    GPP_ORDER_BOOST: float = 1.10  # Top of order boost
    GPP_LOW_OWN: int = 15  # Low ownership threshold
    GPP_OWN_BOOST: float = 1.10  # Ownership leverage
    GPP_K_THRESHOLD: float = 9.0  # K/9 for pitchers
    GPP_K_BOOST: float = 1.15  # High K boost

    # Cash scoring thresholds
    CASH_TEAM_THRESHOLD: float = 4.5  # More conservative
    CASH_TEAM_BOOST: float = 1.08  # Smaller boost
    CASH_ORDER_BOOST: float = 1.05  # Smaller boost
    CASH_CONSISTENCY: int = 70  # 70% consistency threshold
    CASH_CONSISTENCY_BOOST: float = 1.10
    CASH_RECENT_BOOST: float = 1.05

    # =====================================
    # STRATEGY SETTINGS
    # =====================================

    # Slate size thresholds
    SMALL_SLATE_MAX: int = 4  # 1-4 games
    MEDIUM_SLATE_MAX: int = 9  # 5-9 games

    # Strategy map
    STRATEGY_MAP: Dict[str, Dict[str, str]] = None

    # Strategy-specific adjustments
    TOURNAMENT_STACK_BOOST: float = 1.05
    VALUE_THRESHOLD: float = 3.0  # Points per $1000
    VALUE_BOOST: float = 1.08
    CONSISTENCY_PENALTY: float = 0.7  # For low projections
    ELITE_K_BOOST: float = 1.20  # 10+ K/9
    GOOD_K_BOOST: float = 1.10  # 8.5+ K/9
    LOW_K_PENALTY: float = 0.90  # < 8.5 K/9

    # =====================================
    # DATA ENRICHMENT
    # =====================================

    # API settings
    STATCAST_TIMEOUT: int = 10
    VEGAS_TIMEOUT: int = 5
    MLB_API_TIMEOUT: int = 10

    # Cache settings
    CACHE_EXPIRY_MINUTES: int = 60
    USE_CACHE: bool = True

    # Enrichment priorities
    STATCAST_PRIORITY_PLAYERS: int = 50  # Top N by salary
    OWNERSHIP_REQUIRED_GPP: bool = True
    OWNERSHIP_REQUIRED_CASH: bool = False

    # =====================================
    # GUI SETTINGS
    # =====================================

    # Display settings
    WINDOW_WIDTH: int = 1400
    WINDOW_HEIGHT: int = 900
    MAX_LOG_LINES: int = 100

    # Default values
    DEFAULT_LINEUPS_GPP: int = 20
    DEFAULT_LINEUPS_CASH: int = 3
    DEFAULT_CONFIRMED_ONLY: bool = False

    # =====================================
    # EXPORT SETTINGS
    # =====================================

    # DraftKings CSV format
    DK_POSITIONS: List[str] = None

    # File settings
    EXPORT_DIR: str = "exports"
    LINEUP_PREFIX: str = "lineup"

    def __post_init__(self):
        """Initialize defaults if not provided"""

        if self.MIN_SALARY is None:
            self.MIN_SALARY = {
                'gpp': 45000,  # 90% for GPP
                'cash': 47500  # 95% for cash
            }

        if self.POSITION_REQUIREMENTS is None:
            self.POSITION_REQUIREMENTS = {
                'P': 2,
                'C': 1,
                '1B': 1,
                '2B': 1,
                '3B': 1,
                'SS': 1,
                'OF': 3
            }

        if self.MAX_PER_TEAM is None:
            self.MAX_PER_TEAM = {
                'gpp': 5,  # Allow natural stacking
                'cash': 3  # Conservative
            }

        if self.STRATEGY_MAP is None:
            self.STRATEGY_MAP = {
                'cash': {
                    'small': 'pitcher_dominance',
                    'medium': 'projection_monster',
                    'large': 'projection_monster'
                },
                'gpp': {
                    'small': 'tournament_winner_gpp',
                    'medium': 'tournament_winner_gpp',
                    'large': 'correlation_value'
                }
            }

        if self.DK_POSITIONS is None:
            self.DK_POSITIONS = ['P1', 'P2', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3']

    def get_slate_size(self, num_games: int) -> str:
        """Determine slate size category"""
        if num_games <= self.SMALL_SLATE_MAX:
            return 'small'
        elif num_games <= self.MEDIUM_SLATE_MAX:
            return 'medium'
        else:
            return 'large'

    def get_optimal_strategy(self, num_games: int, contest_type: str) -> str:
        """Get optimal strategy for slate"""
        slate_size = self.get_slate_size(num_games)
        return self.STRATEGY_MAP[contest_type][slate_size]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }


# Singleton pattern for global config
_config_instance: Optional[DFSConfig] = None


def get_config() -> DFSConfig:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = DFSConfig()
    return _config_instance


def reset_config():
    """Reset configuration (mainly for testing)"""
    global _config_instance
    _config_instance = None


# Test
if __name__ == "__main__":
    print("Unified Configuration V2")
    print("=" * 50)

    config = get_config()

    print("\nKey Settings:")
    print(f"  Salary Cap: ${config.SALARY_CAP:,}")
    print(f"  Min Salary (GPP): ${config.MIN_SALARY['gpp']:,}")
    print(f"  Min Salary (Cash): ${config.MIN_SALARY['cash']:,}")
    print(f"  Max Per Team (GPP): {config.MAX_PER_TEAM['gpp']}")
    print(f"  Max Per Team (Cash): {config.MAX_PER_TEAM['cash']}")

    print("\nSlate Size Detection:")
    for games in [2, 6, 12]:
        size = config.get_slate_size(games)
        gpp_strat = config.get_optimal_strategy(games, 'gpp')
        cash_strat = config.get_optimal_strategy(games, 'cash')
        print(f"  {games} games = {size} slate")
        print(f"    GPP: {gpp_strat}")
        print(f"    Cash: {cash_strat}")

    print("\n✅ Configuration working correctly!")