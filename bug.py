#!/usr/bin/env python3
"""
FIX OPTIMIZER ERRORS
====================
Fixes the indentation and duplicate line errors in unified_milp_optimizer.py
"""

import os
import shutil
from datetime import datetime


def fix_unified_milp_optimizer():
    """Fix the errors in unified_milp_optimizer.py"""

    print("🔧 FIXING UNIFIED MILP OPTIMIZER ERRORS")
    print("=" * 50)

    # Backup the file first
    backup_name = f"unified_milp_optimizer_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy2('unified_milp_optimizer.py', backup_name)
    print(f"✅ Created backup: {backup_name}")

    # Read the content
    with open('unified_milp_optimizer.py', 'r') as f:
        lines = f.readlines()

    # Fix the specific issues
    fixed_lines = []
    i = 0
    skip_next = False

    while i < len(lines):
        line = lines[i]

        # Skip duplicate logging lines
        if skip_next:
            skip_next = False
            i += 1
            continue

        # Fix the indentation error around position constraints
        if 'logger.warning(f"Not enough players for position {pos}")' in line:
            fixed_lines.append(line)
            i += 1

            # Check if next line is the duplicate logging line
            if i < len(lines) and 'logger.info(f"OPTIMIZATION: Position constraint failed' in lines[i]:
                # Fix the indentation and merge properly
                fixed_lines.append(
                    '                logger.info(f"OPTIMIZATION: Position constraint failed - {pos} needs {required}, have {len(eligible_indices)}")\n')
                i += 1

                # Skip the "return [], 0" with wrong indentation
                if i < len(lines) and 'return [], 0' in lines[i] and lines[i].startswith('                 '):
                    fixed_lines.append('                return [], 0\n')
                    i += 1
                    continue

        # Skip duplicate "Log the final lineup" sections
        elif 'Log the final lineup' in line and i > 0 and 'Log the final lineup' in lines[i - 5:i]:
            # This is a duplicate, skip it and the next 3 lines
            skip_lines = 4
            while skip_lines > 0 and i < len(lines):
                i += 1
                skip_lines -= 1
            continue

        # Fix the position of _pre_filter_players method
        elif 'def _pre_filter_players(self, players: List[Any], strategy: str) -> List[Any]:' in line:
            # This method should be inside the class, not at the end
            # Skip this method definition at the wrong place
            if i > 400:  # If it's near the end of file, skip it
                while i < len(lines) and not (
                        lines[i].startswith('def ') or lines[i].startswith('class ') or lines[i].strip() == ''):
                    i += 1
                continue
            else:
                fixed_lines.append(line)

        else:
            fixed_lines.append(line)

        i += 1

    # Now write the fixed content
    with open('unified_milp_optimizer.py', 'w') as f:
        f.writelines(fixed_lines)

    print("✅ Fixed indentation and duplicate lines")

    # Verify the fix
    try:
        import ast
        with open('unified_milp_optimizer.py', 'r') as f:
            ast.parse(f.read())
        print("✅ Python syntax verification passed!")
    except SyntaxError as e:
        print(f"⚠️  Syntax error still present: {e}")
        print("   Manual review may be needed")


def create_clean_optimizer():
    """Create a clean version of the optimizer from scratch"""

    clean_content = '''#!/usr/bin/env python3
"""
UNIFIED MILP OPTIMIZER - CLEAN VERSION
=====================================
Fixed version with proper indentation and no duplicates
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pulp

# Configure logging
from logging_config import get_logger
logger = get_logger(__name__)


@dataclass
class OptimizationConfig:
    """Enhanced configuration for optimization"""

    salary_cap: int = 50000
    min_salary_usage: float = 0.95
    position_requirements: Dict[str, int] = None

    # Team stacking constraints
    max_players_per_team: int = 4
    min_players_per_team: int = 0
    preferred_stack_size: int = 3

    # Correlation settings
    max_hitters_vs_pitcher: int = 4
    correlation_boost: float = 0.05

    # Optimization settings
    timeout_seconds: int = 30
    use_correlation: bool = True
    enforce_lineup_rules: bool = True

    def __post_init__(self):
        if self.position_requirements is None:
            self.position_requirements = {
                "P": 2,
                "C": 1,
                "1B": 1,
                "2B": 1,
                "3B": 1,
                "SS": 1,
                "OF": 3,
            }


class UnifiedMILPOptimizer:
    """Clean MILP optimizer with comprehensive data integration"""

    def __init__(self, config: OptimizationConfig = None):
        """Initialize optimization engine with configuration"""
        self.config = config or OptimizationConfig()
        self.logger = logger

        # Load configuration
        self._load_dfs_config()

        # Load park factors
        self.park_factors = self._load_park_factors()

        # Initialize data sources
        self._initialize_data_sources()

        # Cache for optimization results
        self._last_result = None
        self._optimization_count = 0

    def _load_dfs_config(self):
        """Load configuration from unified config system or JSON file"""
        try:
            # Try unified config manager first
            from unified_config_manager import get_config_value

            self.config.salary_cap = get_config_value("optimization.salary_cap", 50000)
            self.config.min_salary_usage = get_config_value("optimization.min_salary_usage", 0.95)

            logger.info("Configuration loaded from unified config manager")

        except ImportError:
            logger.debug("Config manager not available, using defaults")

    def _load_park_factors(self) -> Dict[str, float]:
        """Load park factors for teams"""
        park_factors = {
            "COL": 1.20, "CIN": 1.12, "TEX": 1.10, "PHI": 1.08,
            "MIL": 1.06, "BAL": 1.05, "HOU": 1.04, "TOR": 1.03,
            "BOS": 1.03, "NYY": 1.02, "CHC": 1.01, "ARI": 1.00,
            "ATL": 1.00, "MIN": 0.99, "WSH": 0.98, "NYM": 0.97,
            "LAA": 0.96, "STL": 0.95, "CLE": 0.94, "TB": 0.93,
            "KC": 0.92, "DET": 0.91, "SEA": 0.90, "OAK": 0.89,
            "SF": 0.88, "SD": 0.87, "MIA": 0.86, "PIT": 0.85,
            "LAD": 0.98, "CHW": 0.96, "CWS": 0.96,
        }
        return park_factors

    def _initialize_data_sources(self):
        """Initialize external data sources"""
        self.data_sources = {}

        try:
            from simple_statcast_fetcher import SimpleStatcastFetcher
            self.data_sources['statcast'] = SimpleStatcastFetcher()
            logger.info("Statcast data source initialized")
        except ImportError:
            logger.debug("Statcast module not available")

        try:
            from vegas_lines import VegasLines
            self.data_sources['vegas'] = VegasLines()
            logger.info("Vegas lines data source initialized")
        except ImportError:
            logger.debug("Vegas lines module not available")

    def apply_strategy_filter(self, players: List, strategy: str) -> List:
        """Apply strategy-based filtering to player pool"""
        if strategy == "all_players":
            eligible = [p for p in players if self._is_valid_player(p)]
        elif strategy == "confirmed_only":
            eligible = [p for p in players if getattr(p, 'is_confirmed', False)]
        elif strategy == "confirmed_plus_manual":
            eligible = [
                p for p in players
                if getattr(p, 'is_confirmed', False) or getattr(p, 'is_manual_selected', False)
            ]
        elif strategy == "manual_only":
            eligible = [p for p in players if getattr(p, 'is_manual_selected', False)]
        elif strategy == "balanced":
            confirmed = [p for p in players if getattr(p, 'is_confirmed', False)]
            if len(confirmed) < 20:
                non_confirmed = [p for p in players if not getattr(p, 'is_confirmed', False)]
                non_confirmed.sort(key=lambda x: getattr(x, 'base_projection', 0), reverse=True)
                eligible = confirmed + non_confirmed[:30]
            else:
                eligible = confirmed
        else:
            eligible = [p for p in players if self._is_valid_player(p)]

        logger.info(f"Strategy '{strategy}' resulted in {len(eligible)} eligible players")
        return eligible

    def _is_valid_player(self, player) -> bool:
        """Check if player meets basic validation criteria"""
        if not all(hasattr(player, attr) for attr in ['name', 'salary', 'primary_position']):
            return False
        if player.salary <= 0:
            return False
        valid_positions = {'P', 'C', '1B', '2B', '3B', 'SS', 'OF'}
        if player.primary_position not in valid_positions:
            return False
        return True

    def _pre_filter_players(self, players: List[Any], strategy: str) -> List[Any]:
        """Pre-filter players to reduce problem size"""
        if len(players) <= 200:
            return players

        logger.info(f"PERFORMANCE: Pre-filtering {len(players)} players")

        # Sort by value (points per dollar)
        players_with_value = [
            (p, getattr(p, 'optimization_score', 0) / max(p.salary, 1))
            for p in players
        ]
        players_with_value.sort(key=lambda x: x[1], reverse=True)

        # Keep top players by value, ensuring position coverage
        filtered = []
        position_counts = {}

        for player, value in players_with_value:
            pos = player.primary_position
            count = position_counts.get(pos, 0)

            if count < 10 or len(filtered) < 200:
                filtered.append(player)
                position_counts[pos] = count + 1

        logger.info(f"PERFORMANCE: Reduced to {len(filtered)} players")
        return filtered

    def calculate_player_scores(self, players: List) -> List:
        """Calculate enhanced scores for all players"""
        for player in players:
            base_score = getattr(player, 'enhanced_score', None)
            if base_score is None:
                base_score = getattr(player, 'base_projection', 0)

            # Apply park factor if available
            if hasattr(player, 'team') and player.team in self.park_factors:
                park_factor = self.park_factors[player.team]
                if player.primary_position != 'P':
                    base_score *= park_factor
                else:
                    base_score *= (2.0 - park_factor)

            player.enhanced_score = base_score

        return players

    def pre_calculate_correlation_bonuses(self, players: List) -> List:
        """Pre-calculate correlation adjustments"""
        for player in players:
            player.optimization_score = getattr(player, 'enhanced_score', 0)
        return players

    def optimize_lineup(self, players: List, strategy: str = "balanced", manual_selections: str = "") -> Tuple[List, float]:
        """Main optimization method"""
        logger.info(f"OPTIMIZATION: Starting optimization with strategy: {strategy}")
        logger.info(f"OPTIMIZATION: Players available: {len(players)}")
        logger.info(f"OPTIMIZATION: Manual selections: {manual_selections}")
        self._optimization_count += 1

        # 1. Apply strategy filter
        eligible_players = self.apply_strategy_filter(players, strategy)
        if not eligible_players:
            logger.error("No eligible players after strategy filter")
            return [], 0

        # 2. Pre-filter if needed
        eligible_players = self._pre_filter_players(eligible_players, strategy)

        # 3. Calculate scores
        scored_players = self.calculate_player_scores(eligible_players)

        # 4. Apply correlation bonuses
        final_players = self.pre_calculate_correlation_bonuses(scored_players)

        # 5. Process manual selections
        if manual_selections:
            manual_names = [name.strip().lower() for name in manual_selections.split(',')]
            for player in final_players:
                if player.name.lower() in manual_names:
                    player.is_manual_selected = True
                    player.optimization_score *= 1.1

        # 6. Run MILP optimization
        lineup, total_score = self._run_milp_optimization(final_players)

        # 7. Store result
        self._last_result = {
            'lineup': lineup,
            'score': total_score,
            'strategy': strategy,
            'players_considered': len(final_players)
        }

        return lineup, total_score

    def _run_milp_optimization(self, players: List) -> Tuple[List, float]:
        """Run the actual MILP optimization"""
        if not players:
            return [], 0

        # Create optimization problem
        prob = pulp.LpProblem("DFS_Lineup_Optimization", pulp.LpMaximize)

        # Decision variables
        player_vars = pulp.LpVariable.dicts("players", range(len(players)), cat="Binary")

        # Objective function
        prob += pulp.lpSum([
            player_vars[i] * getattr(players[i], 'optimization_score', 0)
            for i in range(len(players))
        ])

        # Constraints

        # 1. Salary cap
        prob += pulp.lpSum([
            player_vars[i] * players[i].salary
            for i in range(len(players))
        ]) <= self.config.salary_cap

        # 2. Minimum salary usage
        prob += pulp.lpSum([
            player_vars[i] * players[i].salary
            for i in range(len(players))
        ]) >= self.config.salary_cap * self.config.min_salary_usage

        # 3. Position requirements
        for pos, required in self.config.position_requirements.items():
            eligible_indices = [
                i for i in range(len(players))
                if players[i].primary_position == pos or pos in getattr(players[i], 'positions', [])
            ]

            if len(eligible_indices) < required:
                logger.warning(f"Not enough players for position {pos}")
                logger.info(f"OPTIMIZATION: Position constraint failed - {pos} needs {required}, have {len(eligible_indices)}")
                return [], 0

            prob += pulp.lpSum([player_vars[i] for i in eligible_indices]) == required

        # 4. Total roster size
        total_required = sum(self.config.position_requirements.values())
        prob += pulp.lpSum(player_vars) == total_required

        # 5. Max players per team
        teams = set(p.team for p in players if hasattr(p, 'team'))
        for team in teams:
            team_indices = [i for i in range(len(players)) if getattr(players[i], 'team', None) == team]
            if team_indices:
                prob += pulp.lpSum([player_vars[i] for i in team_indices]) <= self.config.max_players_per_team

        # 6. Force manual selections
        for i, player in enumerate(players):
            if getattr(player, 'is_manual_selected', False):
                prob += player_vars[i] == 1

        # Solve
        try:
            # Use optimized solver settings
            solver_options = pulp.PULP_CBC_CMD(
                timeLimit=30,  # 30 second timeout
                threads=4,     # Use 4 threads
                options=['preprocess=on', 'cuts=on', 'heuristics=on']
            )
            solver.solve(solver_options)

            if prob.status == pulp.LpStatusOptimal:
                lineup = []
                total_score = 0

                for i in range(len(players)):
                    if player_vars[i].varValue == 1:
                        lineup.append(players[i])
                        total_score += getattr(players[i], 'optimization_score', 0)

                # Sort lineup by position
                position_order = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']
                lineup.sort(key=lambda p: (
                    position_order.index(p.primary_position) if p.primary_position in position_order else 99
                ))

                logger.info(f"Optimization successful: {len(lineup)} players, score: {total_score:.2f}")
                logger.info(f"LINEUP SELECTED: Total score = {total_score:.1f}, Total salary = {sum(p.salary for p in lineup)}")
                for p in lineup:
                    logger.info(f"  LINEUP: {p.primary_position} - {p.name} - ${p.salary} - {p.optimization_score:.1f} pts")

                return lineup, total_score
            else:
                logger.error(f"Optimization failed with status: {pulp.LpStatus[prob.status]}")
                return [], 0

        except Exception as e:
            logger.error(f"MILP optimization error: {e}")
            return [], 0

    def get_optimization_stats(self) -> Dict:
        """Get statistics about optimization performance"""
        return {
            'total_optimizations': self._optimization_count,
            'last_result': self._last_result,
            'config': {
                'salary_cap': self.config.salary_cap,
                'position_requirements': self.config.position_requirements,
                'max_players_per_team': self.config.max_players_per_team
            }
        }


def create_unified_optimizer(config: Optional[OptimizationConfig] = None) -> UnifiedMILPOptimizer:
    """Factory function to create optimizer instance"""
    return UnifiedMILPOptimizer(config)


if __name__ == "__main__":
    print("✅ Unified MILP Optimizer module loaded successfully")
'''

    # Save the clean version
    with open('unified_milp_optimizer_clean.py', 'w') as f:
        f.write(clean_content)

    print("\n✅ Created unified_milp_optimizer_clean.py as a clean reference")


def main():
    """Fix the optimizer errors"""
    print("🚀 FIXING OPTIMIZER ERRORS")
    print("This will fix the indentation and duplicate line errors")
    print()

    # First try to fix the existing file
    fix_unified_milp_optimizer()

    # Also create a clean version
    create_clean_optimizer()

    print("\n📝 NEXT STEPS:")
    print("1. Try running your GUI again")
    print("2. If it still has errors, replace unified_milp_optimizer.py with unified_milp_optimizer_clean.py:")
    print("   cp unified_milp_optimizer_clean.py unified_milp_optimizer.py")
    print("3. Check the logs to see the performance improvements in action!")

    print("\n✅ Fix complete!")


if __name__ == "__main__":
    main()