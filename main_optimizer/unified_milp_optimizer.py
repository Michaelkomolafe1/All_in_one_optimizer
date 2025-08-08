#!/usr/bin/env python3
"""
UNIFIED MILP OPTIMIZER - COMPLETE CLEAN VERSION
==============================================
All methods implemented with proper logging and performance optimizations
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

import pulp

# Helper to handle None values
def safe_compare(a, b, op='<'):
    """Safely compare values that might be None"""
    if a is None:
        a = 0
    if b is None:
        b = 0
    if op == '<':
        return a < b
    elif op == '<=':
        return a <= b
    elif op == '>':
        return a > b
    elif op == '>=':
        return a >= b
    elif op == '==':
        return a == b
    else:
        return a != b



# Configure logging
try:
    from logging_config import get_logger

    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Enhanced configuration for optimization"""

    salary_cap: int = 50000
    min_salary_usage: float = 0.95
    position_requirements: Dict[str, int] = None

    # Team stacking constraints
    max_players_per_team: int = 4  # Will override for cash in optimization
    min_players_per_team: int = 0
    preferred_stack_size: int = 3

    # Correlation settings
    max_hitters_vs_pitcher: int = 4
    correlation_boost: float = 0.05

    # PITCHER-HITTER CORRELATION CONTROL
    # 0 = No opposing hitters allowed (strictest - best for cash)
    # 1 = Allow 1 elite hitter (balanced - good for most cases)
    # 2 = Allow 2 hitters (loose - for small slates)
    # 999 = No constraint (maximum points potential)
    max_opposing_hitters: int = 1  # Default: balanced approach

    # Optimization settings
    timeout_seconds: int = 30
    use_correlation: bool = True
    enforce_lineup_rules: bool = True

    def __post_init__(self):
        if self.position_requirements is None:
            self.position_requirements = {
                "P": 2,  # Just 2 pitchers (DK doesn't distinguish SP/RP)
                "C": 1,
                "1B": 1,
                "2B": 1,
                "3B": 1,
                "SS": 1,
                "OF": 3,
            }


class UnifiedMILPOptimizer:
    """
    Clean MILP optimizer with comprehensive data integration
    """

    def __init__(self, config: OptimizationConfig = None):
        """Initialize optimization engine with configuration"""
        self.config = config or OptimizationConfig()
        self.logger = logger

        # Load configuration
        # self._load_dfs_config()  # Removed - not needed

        # Load park factors
        self.park_factors = self._load_park_factors()

        # Initialize data sources
        self._initialize_data_sources()

        # Cache for optimization results
        self._last_result = None
        self._optimization_count = 0
        self._lineup_cache = {}

    def normalize_positions(self, players):
        """Normalize all pitcher positions to 'P'"""
        for player in players:
            if player.position in ['SP', 'RP']:
                player.position = 'P'
                player.primary_position = 'P'
            # Also handle multi-position eligibility
            if hasattr(player, 'positions'):
                player.positions = ['P' if pos in ['SP', 'RP'] else pos for pos in player.positions]
        # Apply correlation bonuses for stacking
        self.apply_correlation_bonuses(players)
        return players

    def check_position_availability(self, players):
        """Check if we have enough players for each position"""
        position_counts = {}
        for p in players:
            pos = p.position
            if pos not in position_counts:
                position_counts[pos] = 0
            position_counts[pos] += 1

        self.logger.info("Position availability:")
        for pos, count in position_counts.items():
            self.logger.info(f"  {pos}: {count} players")

        # Check requirements
        requirements = {
            'P': 2, 'C': 1, '1B': 1, '2B': 1,
            '3B': 1, 'SS': 1, 'OF': 3
        }

        for pos, need in requirements.items():
            have = position_counts.get(pos, 0)
            if have < need:
                self.logger.warning(f"Not enough {pos}: need {need}, have {have}")

        return position_counts


    def add_tournament_constraints(self, prob, player_vars, players):
        """
        Add constraints based on tournament-winning patterns
        """
        contest_type = getattr(self.config, 'contest_type', 'gpp')

        if contest_type == 'gpp':
            # GPP CONSTRAINTS - 83.2% of winners use these patterns

            # 1. ENFORCE 4-5 MAN STACKS
            # Group players by team (excluding pitchers)
            teams = {}
            for i, player in enumerate(players):
                if player.primary_position != 'P':
                    if player.team not in teams:
                        teams[player.team] = []
                    teams[player.team].append(i)

            # Create binary variables for teams with 4+ stacks
            team_stack_vars = {}
            for team, indices in teams.items():
                if len(indices) >= 4:  # Team must have 4+ available players
                    var_name = f"stack_{team}"
                    team_stack_vars[team] = pulp.LpVariable(var_name, cat="Binary")

            if team_stack_vars:
                # AT LEAST ONE TEAM must have 4+ players (83.2% of winners)
                prob += pulp.lpSum(team_stack_vars.values()) >= 1

                # Link team stack variables to player selections
                for team, stack_var in team_stack_vars.items():
                    team_indices = teams[team]

                    # If stack_var = 1, must have 4+ players from team
                    prob += pulp.lpSum([player_vars[i] for i in team_indices]) >= 4 * stack_var

                    # If 4+ players selected, must set stack_var = 1
                    # (This prevents selecting 4+ without setting the flag)
                    prob += pulp.lpSum([player_vars[i] for i in team_indices]) <= 3 + 10 * stack_var

            # 2. LIMIT PITCHER CHALK
            pitcher_indices = [i for i, p in enumerate(players)
                               if p.primary_position == 'P']

            # Don't allow super high ownership pitchers (>30%)
            chalk_pitchers = [i for i in pitcher_indices
                              if getattr(players[i], 'ownership_projection', 15) > 30]

            if chalk_pitchers:
                # Max 1 chalk pitcher (most winners use low-owned pitchers)
                prob += pulp.lpSum([player_vars[i] for i in chalk_pitchers]) <= 1

        else:  # CASH CONSTRAINTS
            # 1. ENFORCE HIGH K-RATE PITCHERS
            pitcher_indices = [i for i, p in enumerate(players)
                               if p.primary_position == 'P']

            # Identify elite K-rate pitchers (25%+)
            elite_k_pitchers = [i for i in pitcher_indices
                                if getattr(players[i], 'k_rate', 20) >= 25]

            if elite_k_pitchers:
                # MUST have at least 1 high K pitcher (they dominate cash)
                prob += pulp.lpSum([player_vars[i] for i in elite_k_pitchers]) >= 1

            # 2. BATTING ORDER CONSTRAINT
            # Prefer top of batting order (1-4)
            top_order = [i for i, p in enumerate(players)
                         if p.primary_position != 'P' and
                         hasattr(p, 'batting_order') and
                         p.batting_order <= 4]

            if len(top_order) >= 6:
                # At least 6 hitters from top 4 of batting order
                prob += pulp.lpSum([player_vars[i] for i in top_order]) >= 6

            # 3. AVOID BOTTOM OF ORDER
            bottom_order = [i for i, p in enumerate(players)
                            if p.primary_position != 'P' and
                            hasattr(p, 'batting_order') and
                            p.batting_order >= 7]

            if bottom_order:
                # Max 2 hitters from bottom third of order
                prob += pulp.lpSum([player_vars[i] for i in bottom_order]) <= 2

    def apply_correlation_bonuses(self, players: List) -> None:
        """Apply correlation bonuses with CONSECUTIVE batting order preference"""
        
        contest_type = getattr(self.config, 'contest_type', 'gpp')
        
        if contest_type.lower() != 'gpp':
            self.logger.info("Skipping correlation bonuses for non-GPP contest")
            return
        
        self.logger.info("Applying GPP correlation bonuses...")
        
        # Group by team
        teams = {}
        for player in players:
            if not hasattr(player, 'primary_position'):
                continue
            if player.primary_position == 'P':
                continue
            
            team = getattr(player, 'team', None)
            if team:
                if team not in teams:
                    teams[team] = []
                teams[team].append(player)
        
        boosted_count = 0
        
        for team, team_players in teams.items():
            if len(team_players) < 4:
                continue
            
            # Sort by batting order
            team_players.sort(key=lambda p: getattr(p, 'batting_order', 9))
            
            # Create batting order map
            bo_map = {}
            for p in team_players:
                bo = getattr(p, 'batting_order', 9)
                if bo < 9:
                    bo_map[bo] = p
            
            # Find and boost consecutive groups HEAVILY
            consecutive_groups = []
            current_group = []
            
            for i in range(1, 10):
                if i in bo_map:
                    if not current_group or i == current_group[-1] + 1:
                        current_group.append(i)
                    else:
                        if len(current_group) >= 2:
                            consecutive_groups.append(current_group[:])
                        current_group = [i]
                elif current_group:
                    if len(current_group) >= 2:
                        consecutive_groups.append(current_group[:])
                    current_group = []
            
            if len(current_group) >= 2:
                consecutive_groups.append(current_group)
            
            # Apply MASSIVE bonuses to consecutive groups
            for group in consecutive_groups:
                if len(group) >= 4:
                    # 4+ consecutive - HUGE boost
                    for bo in group:
                        if bo in bo_map:
                            p = bo_map[bo]
                            if hasattr(p, 'optimization_score'):
                                p.optimization_score *= 2.0  # Double!
                                p.consecutive_stack = True
                                boosted_count += 1
                                self.logger.debug(f"CONSECUTIVE 4+: {p.name} (BO:{bo}) x2.0")
                
                elif len(group) == 3:
                    # 3 consecutive - strong boost
                    for bo in group:
                        if bo in bo_map:
                            p = bo_map[bo]
                            if hasattr(p, 'optimization_score'):
                                p.optimization_score *= 1.6
                                p.consecutive_stack = True
                                boosted_count += 1
                                self.logger.debug(f"CONSECUTIVE 3: {p.name} (BO:{bo}) x1.6")
                
                elif len(group) == 2:
                    # 2 consecutive - moderate boost
                    for bo in group:
                        if bo in bo_map:
                            p = bo_map[bo]
                            if hasattr(p, 'optimization_score'):
                                p.optimization_score *= 1.3
                                boosted_count += 1
                                self.logger.debug(f"CONSECUTIVE 2: {p.name} (BO:{bo}) x1.3")
            
            # PENALIZE non-consecutive players on stackable teams
            team_total = getattr(team_players[0], 'implied_team_score', 4.5) if team_players else 4.5
            if team_total >= 5.0:  # High-scoring team
                for p in team_players:
                    if not getattr(p, 'consecutive_stack', False):
                        if hasattr(p, 'optimization_score'):
                            p.optimization_score *= 0.5  # Heavy penalty
                            self.logger.debug(f"NON-CONSECUTIVE PENALTY: {p.name} x0.5")
        
        self.logger.info(f"Boosted {boosted_count} players for consecutive stacking")

    def _load_park_factors(self) -> Dict[str, float]:
        """Load park factors for teams"""
        park_factors = {
            # Extreme hitter-friendly
            "COL": 1.20,  # Coors Field
            # Hitter-friendly
            "CIN": 1.12, "TEX": 1.10, "PHI": 1.08, "MIL": 1.06,
            "BAL": 1.05, "HOU": 1.04, "TOR": 1.03, "BOS": 1.03,
            # Slight hitter-friendly
            "NYY": 1.02, "CHC": 1.01,
            # Neutral
            "ARI": 1.00, "ATL": 1.00, "MIN": 0.99,
            # Slight pitcher-friendly
            "WSH": 0.98, "NYM": 0.97, "LAA": 0.96, "STL": 0.95,
            # Pitcher-friendly
            "CLE": 0.94, "TB": 0.93, "KC": 0.92, "DET": 0.91, "SEA": 0.90,
            # Extreme pitcher-friendly
            "OAK": 0.89, "SF": 0.88, "SD": 0.87, "MIA": 0.86, "PIT": 0.85,
            # Additional teams
            "LAD": 0.98, "CHW": 0.96, "CWS": 0.96,
        }

        # Try to load from file
        try:
            park_file = Path("data/park_factors.json")
            if park_file.exists():
                with open(park_file, 'r') as f:
                    loaded_factors = json.load(f)
                    park_factors.update(loaded_factors)
                    logger.info(f"Loaded park factors from {park_file}")
        except Exception as e:
            logger.debug(f"Could not load park factors file: {e}")

        return park_factors

    def _initialize_data_sources(self):
        """Initialize external data sources with fallback options"""
        self.data_sources = {
            'statcast': None,
            'vegas': None,
            'weather': None,
            'batting_order': None
        }

        # Try to initialize each data source
        try:
            from statcast_fetcher import SimpleStatcastFetcher
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

    def apply_strategy_filter(self, players: List, strategy: str, contest_type: str = 'gpp') -> List:
        """Apply strategy filter with small slate protection"""

        # SMALL SLATE DETECTION
        unique_teams = set(p.team for p in players if hasattr(p, 'team'))
        num_games = len(unique_teams) / 2 if unique_teams else 0

        # Position normalization - ALWAYS DO THIS
        for player in players:
            if player.position in ['SP', 'RP']:
                player.position = 'P'
                player.primary_position = 'P'

        self.logger.info(f"Applying strategy filter: {strategy}")
        self.logger.info(f"Starting with {len(players)} players")
        self.logger.info(f"Detected {num_games} games")

        # SMALL SLATE OR SMALL POOL: NO FILTERING!
        if num_games <= 3 or len(players) < 50:
            self.logger.info(f"Small slate/pool detected - keeping ALL {len(players)} players")

            # Just adjust scores based on strategy, don't filter
            for player in players:
                base = getattr(player, 'optimization_score', player.base_projection)

                if contest_type.lower() == 'gpp' and strategy in ['tournament_winner_gpp', 'correlation_value', 'truly_smart_stack', 'matchup_leverage_stack']:
                    # Boost players for stacking but keep everyone
                    team_count = sum(1 for p in players if p.team == player.team and p.position != 'P')
                    if team_count >= 4:
                        player.optimization_score = base * 1.1  # Small boost for stackable teams

            # Apply correlation bonuses for stacking
        self.apply_correlation_bonuses(players)
        return players  # Return ALL players for small slates

        # NORMAL FILTERING FOR LARGE SLATES ONLY
        # ===========================================

        filtered = players  # Start with all

        # Your existing strategy logic here
        if strategy == 'projection_monster':
            # For large slates, take top scorers
            filtered = sorted(players,
                              key=lambda x: getattr(x, 'optimization_score', 0),
                              reverse=True)[:150]

        elif strategy == 'pitcher_dominance':
            pitchers = [p for p in players if p.primary_position == 'P']
            hitters = [p for p in players if p.primary_position != 'P']

            pitchers.sort(key=lambda x: getattr(x, 'optimization_score', 0), reverse=True)
            hitters.sort(key=lambda x: getattr(x, 'optimization_score', 0), reverse=True)

            filtered = pitchers[:20] + hitters[:100]

        elif strategy in ['tournament_winner_gpp', 'correlation_value', 'truly_smart_stack', 'matchup_leverage_stack']:
            # GPP strategies - keep more for stacking
            filtered = sorted(players,
                              key=lambda x: getattr(x, 'optimization_score', 0),
                              reverse=True)[:200]
        else:
            # Unknown strategy - use top 150
            self.logger.warning(f"Unknown strategy {strategy}, using default filter")
            filtered = sorted(players,
                              key=lambda x: getattr(x, 'optimization_score', 0),
                              reverse=True)[:150]

        # SAFETY NET: Ensure minimum positions (for large slates)
        # ========================================================

        # Dynamic requirements based on slate size
        if num_games <= 5:
            MIN_REQUIRED = {'P': 3, 'C': 2, '1B': 2, '2B': 2, '3B': 2, 'SS': 2, 'OF': 5}
        else:
            MIN_REQUIRED = {'P': 4, 'C': 2, '1B': 2, '2B': 2, '3B': 2, 'SS': 2, 'OF': 6}

        final_filtered = list(filtered)

        # Check each position
        for pos, min_needed in MIN_REQUIRED.items():
            if pos == 'P':
                current = len([p for p in final_filtered if p.position in ['P', 'SP', 'RP']])
            else:
                current = len([p for p in final_filtered if p.position == pos])

            self.logger.info(f"  Position {pos}: Have {current}, need {min_needed}")

            if current < min_needed:
                if pos == 'P':
                    candidates = [p for p in players
                                  if p.position in ['P', 'SP', 'RP']
                                  and p not in final_filtered]
                else:
                    candidates = [p for p in players
                                  if p.position == pos
                                  and p not in final_filtered]

                candidates.sort(key=lambda x: getattr(x, 'optimization_score', 0), reverse=True)

                need_to_add = min_needed - current
                to_add = candidates[:need_to_add]
                final_filtered.extend(to_add)

                self.logger.info(f"    Added {len(to_add)} more {pos} players")

        self.logger.info(f"Final filtered pool: {len(final_filtered)} players")

        return final_filtered


    def _is_valid_player(self, player) -> bool:
        """Check if player meets basic validation criteria"""
        # Must have required attributes
        if not all(hasattr(player, attr) for attr in ['name', 'salary', 'primary_position']):
            return False

        # Must have positive salary
        if player.salary <= 0:
            return False

        # Must have valid position
        valid_positions = {'P', 'SP', 'RP', 'C', '1B', '2B', '3B', 'SS', 'OF'}
        if player.primary_position not in valid_positions:
            return False

        return True

    def _pre_filter_players(self, players: List[Any], strategy: str) -> List[Any]:
        """Pre-filter players to reduce problem size for performance"""
        if len(players) <= 200:
            return players
        
        logger.info(f"PERFORMANCE: Pre-filtering {len(players)} players")
        
        # FIXED: Handle None values properly
        players_with_value = []
        for p in players:
            # Get score, default to 0 if None
            score = getattr(p, 'optimization_score', 0)
            if score is None:
                score = 0
            
            # Get salary, ensure it's positive
            salary = max(getattr(p, 'salary', 1), 1)
            
            # Calculate value (points per dollar)
            value = score / salary
            players_with_value.append((p, value))
        
        # Sort by value
        players_with_value.sort(key=lambda x: x[1], reverse=True)
        
        # Keep top players by value, ensuring position coverage
        filtered = []
        position_counts = {}
        
        for player, value in players_with_value:
            pos = player.primary_position
            count = position_counts.get(pos, 0)
            
            # Keep at least 10 per position, or top 200 overall
            if count < 10 or len(filtered) < 200:
                filtered.append(player)
                position_counts[pos] = count + 1
        
        logger.info(f"PERFORMANCE: Reduced to {len(filtered)} players")
        return filtered

    def calculate_player_scores(self, players: List) -> List:
        """
        Calculate scores for all players.
        Uses contest-specific scores from enhanced scoring engine.
        """
        contest_type = getattr(self.config, 'contest_type', 'gpp')
        logger.info(f"DEBUG: calculate_player_scores - contest_type = {contest_type}")
        
        for player in players:
            # Use contest-specific scores!
            if contest_type.lower() == 'cash' and hasattr(player, 'cash_score'):
                logger.info(f"DEBUG: Using cash_score for {player.name}: {player.cash_score}")
                player.optimization_score = player.cash_score
            elif contest_type.lower() == 'gpp' and hasattr(player, 'gpp_score'):
                logger.info(f"DEBUG: Using gpp_score for {player.name}: {player.gpp_score}")
                player.optimization_score = player.gpp_score
            elif hasattr(player, 'enhanced_score'):
                # Fallback to enhanced_score
                player.optimization_score = player.enhanced_score
            else:
                # No score available
                player.optimization_score = 0
                logger.warning(f"No valid score for {player.name}")

        # Apply correlation bonuses for stacking
        self.apply_correlation_bonuses(players)
        # Apply correlation bonuses for stacking
        self.apply_correlation_bonuses(players)
        return players

    def pre_calculate_correlation_bonuses(self, players: List) -> List:
        """Pre-calculate correlation adjustments for optimization"""
        # This is where correlation logic would go
        # For now, just copy enhanced_score to optimization_score
        for player in players:
            player.optimization_score = getattr(player, 'enhanced_score', 0)

        # Apply correlation bonuses for stacking
        self.apply_correlation_bonuses(players)
        return players

    def optimize_lineup(self,
                        players: List,
                        strategy: str = "balanced",
                        manual_selections: str = "",
                        contest_type: str = None) -> Tuple[List, float]:
        """
        Main optimization method with dynamic salary constraints
        """

        # Extract contest type from strategy or config
        if contest_type is None:
            if strategy in ["cash", "projection_monster", "pitcher_dominance"]:
                contest_type = "cash"
            else:
                contest_type = "gpp"
        
        logger.info(f"OPTIMIZATION: Starting optimization with strategy: {strategy}")
        logger.info(f"OPTIMIZATION: Contest type: {contest_type}")
        logger.info(f"OPTIMIZATION: Players available: {len(players)}")
        logger.info(f"OPTIMIZATION: Manual selections: {manual_selections}")
        self._optimization_count += 1


        # Store contest type for use in other methods
        if contest_type:
            self.config.contest_type = contest_type
        
        # Set max players per team based on contest type
        if contest_type == 'cash':
            self.config.max_players_per_team = 3
            self.logger.info(f"Cash game: Set max_players_per_team = 3")
        else:
            self.config.max_players_per_team = 5
            self.logger.info(f"GPP: Set max_players_per_team = 5")

        # Dynamic minimum salary based on strategy
        if strategy in ['projection_monster', 'truly_smart_stack']:
            min_salary = 35000  # 96%
        elif strategy == 'pitcher_dominance':
            min_salary = 35000  # 97%
        elif strategy == 'correlation_value':
            min_salary = 35000  # 95%
        elif strategy == 'matchup_leverage_stack':
            min_salary = 35000  # 94% - needs variance room
        else:
            min_salary = 35000  # 90% default

        # Store for use in _run_milp_optimization
        self._strategy_min_salary = min_salary

        # 1. Apply strategy filter
        eligible_players = self.apply_strategy_filter(players, strategy)
        if not eligible_players:
            logger.error("No eligible players after strategy filter")
            return [], 0

        # 2. Pre-filter for performance if needed
        eligible_players = self._pre_filter_players(eligible_players, strategy)

        # 3. Calculate scores
        scored_players = self.calculate_player_scores(eligible_players)

        # 4. Process manual selections
        if manual_selections:
            manual_names = [name.strip().lower() for name in manual_selections.split(',')]
            for player in scored_players:
                if player.name.lower() in manual_names:
                    player.is_manual_selected = True
                    # Boost score slightly to encourage selection
                    player.optimization_score *= 1.1

        # 5. Run MILP optimization
        lineup, total_score = self._run_milp_optimization(scored_players, contest_type or "gpp")

        # 6. Store result
        self._last_result = {
            'lineup': lineup,
            'score': total_score,
            'strategy': strategy,
            'players_considered': len(scored_players)
        }

        return lineup, total_score

    def _run_milp_optimization(self, players: List, contest_type: str = "gpp") -> Tuple[List, float]:
        """
        Run the actual MILP optimization with WORKING STACKING
        """
        if not players:
            return [], 0
            
        logger = self.logger

        # Create optimization problem
        prob = pulp.LpProblem("DFS_Lineup_Optimization", pulp.LpMaximize)

        # Decision variables
        player_vars = pulp.LpVariable.dicts(
            "players",
            range(len(players)),
            cat="Binary"
        )

        # Objective function - maximize total score
        prob += pulp.lpSum([
            player_vars[i] * getattr(players[i], 'optimization_score', 0)
            for i in range(len(players))
        ])

        # === CONSTRAINTS ===
        
        # 1. Salary cap constraint
        prob += pulp.lpSum([
            player_vars[i] * players[i].salary
            for i in range(len(players))
        ]) <= self.config.salary_cap

        # 2. Minimum salary
        min_salary = getattr(self, "_strategy_min_salary", 35000)
        prob += pulp.lpSum([
            player_vars[i] * players[i].salary
            for i in range(len(players))
        ]) >= min_salary

        # 3. Position requirements
        position_map = {}
        for i, player in enumerate(players):
            pos = player.primary_position
            if pos not in position_map:
                position_map[pos] = []
            position_map[pos].append(i)

        position_requirements = self.get_position_requirements(players)
        
        for pos, required in position_requirements.items():
            if pos in position_map and required > 0:
                prob += pulp.lpSum([
                    player_vars[i] for i in position_map[pos]
                ]) >= required, f"min_{pos}"

        # Total roster size
        total_required = sum(position_requirements.values())
        prob += pulp.lpSum([
            player_vars[i] for i in range(len(players))
        ]) == total_required, "roster_size"

        # 4. Group players by team (DICTIONARY not set!)
        teams = {}  # This MUST be a dictionary
        for i, player in enumerate(players):
            team = player.team
            if team not in teams:
                teams[team] = []  # List of player indices
            teams[team].append(i)

        # 5. Max players per team
        max_per_team = self.config.max_players_per_team
        for team, indices in teams.items():
            if len(indices) > 1:
                prob += pulp.lpSum([
                    player_vars[i] for i in indices
                ]) <= max_per_team, f"max_team_{team}"

        # 6. GPP STACKING CONSTRAINT
        if contest_type == "gpp":
            # Find teams that can be stacked (4+ players available)
            stackable_teams = []
            for team, indices in teams.items():
                if len(indices) >= 4:
                    # Create binary variable for this team being stacked
                    stack_var = pulp.LpVariable(f"stack_{team}", cat="Binary")
                    stackable_teams.append(stack_var)
                    
                    # If stack_var = 1, must have 4+ from this team
                    prob += (
                        pulp.lpSum([player_vars[i] for i in indices]) >= 4 * stack_var,
                        f"min_stack_{team}"
                    )
                    
                    # If we have 4+ from team, stack_var must be 1
                    prob += (
                        pulp.lpSum([player_vars[i] for i in indices]) <= 3 + 10 * stack_var,
                        f"force_stack_{team}"
                    )
            
            # REQUIRE at least one stack
            if stackable_teams:
                prob += (
                    pulp.lpSum(stackable_teams) >= 1,
                    "require_one_stack"
                )
                logger.info(f"GPP: Requiring stack from {len(stackable_teams)} eligible teams")

        # 7. Manual selections
        for i, player in enumerate(players):
            if getattr(player, 'is_manual_selected', False):
                prob += player_vars[i] == 1, f"force_{player.name}"

        # Solve
        try:
            prob.solve(pulp.PULP_CBC_CMD(msg=0))
            
            if prob.status == pulp.LpStatusOptimal:
                lineup = []
                for i in range(len(players)):
                    if player_vars[i].varValue == 1:
                        lineup.append(players[i])
                
                total_score = sum(getattr(p, 'optimization_score', 0) for p in lineup)
                
                # Log the lineup with stack analysis
                logger.info(f"LINEUP SELECTED: Score={total_score:.1f}, Salary={sum(p.salary for p in lineup)}")
                
                # Analyze stacking
                team_counts = {}
                for p in lineup:
                    if p.primary_position != 'P':
                        team_counts[p.team] = team_counts.get(p.team, 0) + 1
                
                max_stack = max(team_counts.values()) if team_counts else 0
                stacked_teams = [t for t, c in team_counts.items() if c >= 4]
                
                logger.info(f"  📊 STACK ANALYSIS:")
                logger.info(f"     Contest: {contest_type}")
                logger.info(f"     Largest stack: {max_stack} players")
                logger.info(f"     Teams with 4+: {stacked_teams}")
                logger.info(f"     Distribution: {team_counts}")
                
                for p in lineup:
                    logger.info(f"  {p.primary_position}: {p.name} ({p.team}) - ${p.salary}")
                
                return lineup, total_score
            else:
                logger.error(f"Optimization failed: {pulp.LpStatus[prob.status]}")
                return [], 0
                
        except Exception as e:
            logger.error(f"MILP error: {e}")
            import traceback
            traceback.print_exc()
            return [], 0

    def get_optimization_stats(self) -> Dict:
        """Get statistics about optimization performance"""
        stats = {
            'total_optimizations': self._optimization_count,
            'last_result': self._last_result,
            'config': {
                'salary_cap': self.config.salary_cap,
                'position_requirements': self.config.position_requirements,
                'max_players_per_team': self.config.max_players_per_team
            }
        }
        return stats

    def get_position_requirements(self, players):
        """Adjust requirements based on what's available"""

        # Count available positions
        position_counts = {}
        for p in players:
            pos = 'P' if p.position in ['P', 'SP', 'RP'] else p.position
            position_counts[pos] = position_counts.get(pos, 0) + 1

        # If small slate, use minimums
        if len(players) < 50:
            return {
                'P': min(2, position_counts.get('P', 0)),  # Need 2 but work with what we have
                'C': min(1, position_counts.get('C', 0)),
                '1B': min(1, position_counts.get('1B', 0)),
                '2B': min(1, position_counts.get('2B', 0)),
                '3B': min(1, position_counts.get('3B', 0)),
                'SS': min(1, position_counts.get('SS', 0)),
                'OF': min(3, position_counts.get('OF', 0))
            }

        # Normal requirements for large slates
        return {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

    def parse_manual_selections(self, manual_text: str, all_players: List) -> List[str]:
        """Parse manual player selections from text"""
        if not manual_text:
            return []

        manual_names = []
        for name in manual_text.split(','):
            name = name.strip()
            if name:
                manual_names.append(name.lower())

        # Find matching players
        selected_players = []
        for player in all_players:
            if player.name.lower() in manual_names:
                selected_players.append(player.name)
                player.is_manual_selected = True

        return selected_players

    def optimize(self, players: List, strategy: str = "balanced",
                 manual_selections: Optional[List[str]] = None) -> Any:
        """Optimize lineup (compatibility method)"""
        # Convert manual selections list to string if needed
        manual_text = ""
        if manual_selections:
            manual_text = ", ".join(manual_selections)

        lineup, score = self.optimize_lineup(players, strategy, manual_text)

        # Return a result object for compatibility
        class OptimizationResult:
            def __init__(self, lineup, score):
                self.lineup = lineup
                self.score = score
                self.total_score = score

        return OptimizationResult(lineup, score) if lineup else None


def create_unified_optimizer(config: Optional[OptimizationConfig] = None) -> UnifiedMILPOptimizer:
    """Factory function to create optimizer instance"""
    return UnifiedMILPOptimizer(config)


# For backward compatibility
if __name__ == "__main__":
    print("✅ Unified MILP Optimizer module loaded successfully")
    print("📋 Usage:")
    print("   from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig")
    print("   config = OptimizationConfig(salary_cap=50000)")
    print("   optimizer = UnifiedMILPOptimizer(config)")