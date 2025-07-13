#!/usr/bin/env python3
"""
UNIFIED MILP OPTIMIZER - COMPREHENSIVE CLEAN IMPLEMENTATION
=====================================================
No bonuses for confirmed/manual players - pure performance-based optimization
Integrates all existing data systems with NO fake fallbacks
"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pulp

# Import your existing models and systems
from unified_player_model import UnifiedPlayer

logger = logging.getLogger(__name__)


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
    correlation_boost: float = 0.05  # Small boost for correlated plays

    # Optimization settings
    timeout_seconds: int = 30
    use_correlation: bool = True
    enforce_lineup_rules: bool = True

    def __post_init__(self):
        if self.position_requirements is None:
            self.position_requirements = {
                'P': 2, 'C': 1, '1B': 1, '2B': 1,
                '3B': 1, 'SS': 1, 'OF': 3
            }


class UnifiedMILPOptimizer:
    """
    Clean MILP optimizer with comprehensive data integration
    NO artificial bonuses - pure performance-based optimization
    """

    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.logger = logger

        # Load DFS configuration
        self._load_dfs_config()

        # Load real data sources
        self._initialize_data_sources()

    def get_optimization_score(self, player):
        """Get the score to use for optimization (temporary or enhanced)"""
        return getattr(player, '_temp_optimization_score', player.enhanced_score)

    def _load_dfs_config(self):
        """Load configuration from dfs_config.json"""
        try:
            # Try to load existing dfs_config system
            from dfs_config import dfs_config

            # Update optimization config from file
            self.config.salary_cap = dfs_config.get('optimization.salary_cap', 50000)
            self.config.min_salary_usage = dfs_config.get('optimization.min_salary_usage', 0.95)
            self.config.timeout_seconds = dfs_config.get('api_limits.timeout', 30)

            # Form analysis settings
            self.max_form_analysis_players = dfs_config.get('optimization.max_form_analysis_players')

            self.logger.info("✅ Loaded configuration from dfs_config.json")
        except:
            # Fallback to reading JSON directly
            try:
                import json
                with open('dfs_config.json', 'r') as f:
                    config_data = json.load(f)

                self.config.salary_cap = config_data.get('optimization', {}).get('salary_cap', 50000)
                self.config.min_salary_usage = config_data.get('optimization', {}).get('min_salary_usage', 0.95)
                self.max_form_analysis_players = config_data.get('optimization', {}).get('max_form_analysis_players')

                self.logger.info("✅ Loaded configuration from dfs_config.json (direct)")
            except:
                self.logger.warning("⚠️ Using default configuration")

    def _initialize_data_sources(self):
        """Initialize connections to real data sources"""
        # Park factors - try multiple sources
        self.park_factors = {}

        # First try park_factors.json
        try:
            with open('park_factors.json', 'r') as f:
                self.park_factors = json.load(f)
            self.logger.info("✅ Loaded park factors from park_factors.json")
        except:
            # Try loading from bulletproof_dfs_core PARK_FACTORS constant
            try:
                from bulletproof_dfs_core import PARK_FACTORS
                self.park_factors = {team: {'overall': factor} for team, factor in PARK_FACTORS.items()}
                self.logger.info("✅ Loaded park factors from bulletproof_dfs_core")
            except:
                self.logger.warning("⚠️ Park factors not available")

        # Recent form analyzer
        try:
            from recent_form_analyzer import RecentFormAnalyzer
            from utils.cache_manager import cache
            self.form_analyzer = RecentFormAnalyzer(cache_manager=cache)
            self.logger.info("✅ Recent form analyzer initialized")
        except:
            try:
                # Try without cache
                from recent_form_analyzer import RecentFormAnalyzer
                self.form_analyzer = RecentFormAnalyzer()
                self.logger.info("✅ Recent form analyzer initialized (no cache)")
            except:
                self.form_analyzer = None
                self.logger.warning("⚠️ Recent form analyzer not available")

        # Statcast connection
        try:
            from simple_statcast_fetcher import SimpleStatcastFetcher
            self.statcast = SimpleStatcastFetcher()
            self.logger.info("✅ Statcast fetcher initialized")
        except:
            self.statcast = None
            self.logger.warning("⚠️ Statcast fetcher not available")

        # Vegas lines
        try:
            from vegas_lines import VegasLines
            self.vegas_lines = VegasLines()
            self.logger.info("✅ Vegas lines initialized")
        except:
            self.vegas_lines = None
            self.logger.warning("⚠️ Vegas lines not available")

    def calculate_player_scores(self, players: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """
        Calculate enhanced scores using ONLY real data
        Skip players that are already enriched
        """
        # Count how many are already enriched
        already_enriched = sum(1 for p in players if hasattr(p, '_is_enriched') and p._is_enriched)
        if already_enriched > 0:
            print(f"ℹ️ Skipping {already_enriched}/{len(players)} already enriched players")

        # Determine how many players to analyze for form
        form_limit = getattr(self, 'max_form_analysis_players', None)

        # Sort players by base projection for prioritization
        sorted_players = sorted(players, key=lambda p: getattr(p, 'base_projection', 0), reverse=True)

        for i, player in enumerate(sorted_players):
            # SKIP IF ALREADY ENRICHED (from confirmation phase)
            if hasattr(player, '_is_enriched') and player._is_enriched:
                continue

            # Define base_score at the beginning of the loop
            base_score = getattr(player, 'base_projection', 0)
            if base_score <= 0:
                base_score = getattr(player, 'projection', 0)

            # Skip if no base score
            if base_score == 0:
                player.enhanced_score = 0
                continue

            # Only apply adjustments if we have REAL data
            multipliers = []

            # 1. Recent Performance (15% weight - reduced from 40%)
            if form_limit is None or i < form_limit:
                # Try form analyzer first
                if self.form_analyzer and hasattr(player, 'name'):
                    try:
                        form_data = self.form_analyzer.analyze_player_form(player)
                        if form_data:
                            player.apply_recent_form(form_data)
                    except Exception as e:
                        self.logger.debug(f"Form analysis failed for {player.name}: {e}")

                # Check if we have form data
                if hasattr(player, '_recent_performance') and player._recent_performance:
                    form_mult = player._recent_performance.get('form_score', 1.0)
                    multipliers.append(('recent_form', form_mult, 0.15))
                elif hasattr(player, 'dff_l5_avg') and player.dff_l5_avg is not None and player.dff_l5_avg > 0:
                    # Use DFF L5 average as recent form
                    if base_score > 0:
                        form_mult = player.dff_l5_avg / base_score
                        form_mult = max(0.7, min(1.3, form_mult))  # Cap between 0.7-1.3
                        multipliers.append(('dff_l5', form_mult, 0.15))

            # 2. Vegas Environment (20% weight)
            if self.vegas_lines and hasattr(player, 'name') and hasattr(player, 'team'):
                try:
                    vegas_data = self.vegas_lines.get_player_odds(player.name, player.team)
                    if vegas_data:
                        player.apply_vegas_data(vegas_data)
                except:
                    pass

            vegas_mult = self._calculate_vegas_multiplier(player)
            if vegas_mult is not None:
                multipliers.append(('vegas', vegas_mult, 0.20))

            # 3. Park Factors (5% weight - minor factor)
            if self.park_factors and player.team:
                player._park_factors = self.park_factors

            park_mult = self._calculate_park_multiplier(player)
            if park_mult is not None:
                multipliers.append(('park', park_mult, 0.05))

            # 4. Statcast/Matchup Quality (25% weight - increased for data quality)
            if self.statcast and hasattr(player, 'name'):
                try:
                    statcast_data = self.statcast.fetch_player_data(
                        player.name,
                        player.primary_position
                    )
                    if statcast_data and isinstance(statcast_data, dict):
                        player.apply_statcast_data(statcast_data)
                except:
                    pass

            matchup_mult = self._calculate_matchup_multiplier(player)
            if matchup_mult is not None:
                multipliers.append(('matchup', matchup_mult, 0.25))

            # Apply weighted multipliers ONLY if we have real data
            if multipliers:
                # Normalize weights
                total_weight = sum(weight for _, _, weight in multipliers)

                # Base projection gets remaining weight (35-40%)
                base_weight = max(0.35, 1.0 - total_weight)

                # Calculate final score
                final_score = base_score * base_weight

                for name, mult, weight in multipliers:
                    final_score += base_score * (mult - 1.0) * weight

                player.enhanced_score = final_score

                # Store components for debugging
                player._score_components = {
                    'base': base_score,
                    'base_weight': base_weight,
                    'multipliers': [(n, m, w) for n, m, w in multipliers],
                    'final': final_score
                }

                self.logger.debug(f"{player.name}: base={base_score:.1f} ({base_weight:.0%}), "
                                  f"adjustments={[(n, f'{(m - 1) * 100:+.0f}%', f'{w:.0%}') for n, m, w in multipliers]}, "
                                  f"final={player.enhanced_score:.1f}")
            else:
                # No real data available - use base projection only
                player.enhanced_score = base_score

        return players

    def _calculate_vegas_multiplier(self, player: UnifiedPlayer) -> Optional[float]:
        """Calculate Vegas-based multiplier using REAL data only"""
        if not hasattr(player, '_vegas_data') or not player._vegas_data:
            return None

        vegas = player._vegas_data

        # Must have implied team total
        if 'implied_total' not in vegas or vegas['implied_total'] <= 0:
            return None

        implied_total = vegas['implied_total']

        if player.primary_position == 'P':
            # For pitchers: opponent's implied total matters
            if 'opponent_total' in vegas:
                opp_total = vegas['opponent_total']
                if opp_total < 3.0:
                    return 1.30
                elif opp_total < 3.5:
                    return 1.20
                elif opp_total < 4.0:
                    return 1.10
                elif opp_total < 4.5:
                    return 1.00
                elif opp_total < 5.0:
                    return 0.90
                else:
                    return 0.80
        else:
            # For hitters: team's implied total
            if implied_total > 5.5:
                mult = 1.30
            elif implied_total > 5.0:
                mult = 1.20
            elif implied_total > 4.5:
                mult = 1.10
            elif implied_total > 4.0:
                mult = 1.00
            elif implied_total > 3.5:
                mult = 0.90
            else:
                mult = 0.80

            # Adjust for game total if available
            if 'game_total' in vegas:
                if vegas['game_total'] > 11:
                    mult *= 1.05
                elif vegas['game_total'] < 7.5:
                    mult *= 0.95

            return mult

        return None

    def _calculate_park_multiplier(self, player: UnifiedPlayer) -> Optional[float]:
        """Calculate park factor multiplier using REAL data only"""
        if not self.park_factors or not player.team:
            return None

        # Get park factor for player's team
        park_data = self.park_factors.get(player.team)

        if park_data is None:
            return None

        # Handle different park factor formats
        if isinstance(park_data, dict):
            # Dictionary format with specific factors
            if player.primary_position == 'P':
                # Pitchers benefit from pitcher-friendly parks
                factor = park_data.get('pitcher_factor')
                if factor is None and 'overall' in park_data:
                    # Invert overall factor for pitchers
                    factor = 2.0 - park_data['overall']
            else:
                # Hitters benefit from hitter-friendly parks
                factor = park_data.get('hitter_factor')
                if factor is None:
                    factor = park_data.get('overall')
        else:
            # Simple numeric factor (assume hitter-oriented)
            try:
                factor = float(park_data)
                if player.primary_position == 'P':
                    # Invert for pitchers (lower is better)
                    factor = 2.0 - factor
            except:
                return None

        if factor is None:
            return None

        # Ensure reasonable bounds
        return max(0.85, min(factor, 1.15))

    def _calculate_matchup_multiplier(self, player: UnifiedPlayer) -> Optional[float]:
        """Calculate matchup quality using REAL data only"""
        mult = 1.0
        adjustments = 0

        # Check Statcast matchup data if available
        if hasattr(player, '_statcast_data') and player._statcast_data:
            statcast = player._statcast_data

            if player.primary_position == 'P':
                # For pitchers: K rate and opponent quality
                if 'k_rate' in statcast:
                    k_rate = statcast['k_rate']
                    if k_rate > 28:
                        mult *= 1.10
                        adjustments += 1
                    elif k_rate > 25:
                        mult *= 1.05
                        adjustments += 1
                    elif k_rate < 20:
                        mult *= 0.95
                        adjustments += 1

                if 'opponent_ops' in statcast:
                    opp_ops = statcast['opponent_ops']
                    if opp_ops < 0.700:
                        mult *= 1.08
                        adjustments += 1
                    elif opp_ops > 0.800:
                        mult *= 0.92
                        adjustments += 1
            else:
                # For hitters: barrel rate and pitcher matchup
                if 'barrel_rate' in statcast:
                    barrel = statcast['barrel_rate']
                    if barrel > 12:
                        mult *= 1.10
                        adjustments += 1
                    elif barrel > 10:
                        mult *= 1.05
                        adjustments += 1
                    elif barrel < 6:
                        mult *= 0.95
                        adjustments += 1

                if 'opposing_pitcher_era' in statcast:
                    era = statcast['opposing_pitcher_era']
                    if era > 5.0:
                        mult *= 1.12
                        adjustments += 1
                    elif era < 3.0:
                        mult *= 0.88
                        adjustments += 1

        # Only return if we made adjustments based on real data
        return mult if adjustments > 0 else None

    def optimize_lineup(self, players: List[UnifiedPlayer],
                        strategy: str = 'balanced',
                        manual_selections: str = "") -> Tuple[List[UnifiedPlayer], float]:
        """
        Main optimization method
        1. Apply strategy filter to create player pool
        2. Calculate scores using real data
        3. Run MILP optimization
        """

        # Step 1: Create player pool based on strategy
        strategy_filter = StrategyFilter()
        player_pool = strategy_filter.apply_strategy_filter(players, strategy, manual_selections)

        self.logger.info(f"Strategy '{strategy}' created pool of {len(player_pool)} players")

        # Step 2: Calculate enhanced scores using real data
        player_pool = self.calculate_player_scores(player_pool)

        # Step 3: Run MILP optimization
        try:
            return self._optimize_milp(player_pool)
        except Exception as e:
            self.logger.error(f"MILP optimization failed: {e}")
            # NO FALLBACK - return empty if optimization fails
            return [], 0

    def _optimize_milp(self, players: List[UnifiedPlayer]) -> Tuple[List[UnifiedPlayer], float]:
        """
        Pure MILP optimization with correlation constraints
        """
        self.logger.info(f"🔬 MILP: Optimizing {len(players)} players")

        # Create problem
        prob = pulp.LpProblem("DFS_Clean_Optimizer", pulp.LpMaximize)

        # Decision variables
        player_vars = {}
        for i, player in enumerate(players):
            player_vars[i] = pulp.LpVariable(f"x_{i}", cat='Binary')

        # Position assignment variables
        position_vars = {}
        for i, player in enumerate(players):
            for pos in player.positions:
                if pos in self.config.position_requirements:
                    position_vars[(i, pos)] = pulp.LpVariable(
                        f"y_{i}_{pos}", cat='Binary'
                    )

        # OBJECTIVE: Pure enhanced scores (no bonuses)
        # OBJECTIVE: Use temporary score if exists (for diversity), otherwise enhanced score
        # OBJECTIVE: Use optimization score (accounts for diversity penalties)
        objective = pulp.lpSum([
            player_vars[i] * self.get_optimization_score(players[i])
            for i in range(len(players))
        ])

        # Add small correlation bonus if enabled
        if self.config.use_correlation:
            correlation_bonus = self._calculate_correlation_bonus(
                players, player_vars, position_vars
            )
            if correlation_bonus:
                objective += correlation_bonus

        prob += objective

        # CONSTRAINTS

        # 1. Exactly 10 players (or as specified)
        total_players = sum(self.config.position_requirements.values())
        prob += pulp.lpSum(player_vars.values()) == total_players

        # 2. Salary cap constraint
        prob += pulp.lpSum([
            player_vars[i] * players[i].salary
            for i in range(len(players))
        ]) <= self.config.salary_cap

        # 3. Minimum salary usage
        prob += pulp.lpSum([
            player_vars[i] * players[i].salary
            for i in range(len(players))
        ]) >= self.config.salary_cap * self.config.min_salary_usage

        # 4. Position requirements
        for pos, required in self.config.position_requirements.items():
            prob += pulp.lpSum([
                position_vars.get((i, pos), 0)
                for i in range(len(players))
            ]) == required

        # 5. Player can only be assigned to one position
        for i in range(len(players)):
            prob += pulp.lpSum([
                position_vars.get((i, pos), 0)
                for pos in players[i].positions
                if pos in self.config.position_requirements
            ]) <= player_vars[i]

        # 6. Player must be selected if assigned to position
        for i, pos in position_vars:
            prob += position_vars[(i, pos)] <= player_vars[i]

        # 7. Team stacking constraints
        teams = list(set(p.team for p in players if p.team))
        for team in teams:
            team_indices = [i for i, p in enumerate(players) if p.team == team]
            if team_indices:
                # Max players per team
                prob += pulp.lpSum([
                    player_vars[i] for i in team_indices
                ]) <= self.config.max_players_per_team

        # 8. Pitcher vs opposing hitters constraint
        if self.config.enforce_lineup_rules:
            self._add_pitcher_hitter_constraints(prob, players, player_vars)

        # Solve
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=self.config.timeout_seconds)
        prob.solve(solver)

        if prob.status == pulp.LpStatusOptimal:
            return self._extract_solution(players, player_vars, position_vars)
        else:
            raise Exception(f"Optimization failed: {pulp.LpStatus[prob.status]}")

    def _calculate_correlation_bonus(self, players: List[UnifiedPlayer],
                                     player_vars: Dict,
                                     position_vars: Dict) -> Optional[pulp.LpAffineExpression]:
        """
        Calculate small correlation bonuses for stacks
        Based on REAL batting order data only
        """
        if not self.config.use_correlation:
            return None

        correlation_terms = []

        # Group players by team
        team_players = {}
        for i, player in enumerate(players):
            if player.team and player.primary_position != 'P':
                if player.team not in team_players:
                    team_players[player.team] = []
                team_players[player.team].append(i)

        # Create correlation bonuses for consecutive batting order
        for team, indices in team_players.items():
            # Only if we have batting order data
            team_with_order = []
            for idx in indices:
                player = players[idx]
                if hasattr(player, 'batting_order') and player.batting_order:
                    team_with_order.append((idx, player.batting_order))

            if len(team_with_order) >= 2:
                # Sort by batting order
                team_with_order.sort(key=lambda x: x[1])

                # Add small bonus for consecutive batters
                for i in range(len(team_with_order) - 1):
                    idx1, order1 = team_with_order[i]
                    idx2, order2 = team_with_order[i + 1]

                    if order2 - order1 == 1:  # Consecutive
                        # Small bonus for selecting both
                        bonus = self.config.correlation_boost * min(
                            players[idx1].enhanced_score,
                            players[idx2].enhanced_score
                        )

                        # Binary variable for both selected
                        correlation_terms.append(
                            bonus * player_vars[idx1] * player_vars[idx2]
                        )

        return pulp.lpSum(correlation_terms) if correlation_terms else None

    def _add_pitcher_hitter_constraints(self, prob: pulp.LpProblem,
                                        players: List[UnifiedPlayer],
                                        player_vars: Dict):
        """Add constraints limiting hitters against selected pitcher"""
        # Find all pitchers
        pitcher_indices = [i for i, p in enumerate(players)
                           if p.primary_position == 'P']

        for p_idx in pitcher_indices:
            pitcher = players[p_idx]

            # Find opposing team (from game info)
            opp_team = self._get_opposing_team(pitcher)
            if not opp_team:
                continue

            # Find opposing hitters
            opp_hitters = [i for i, p in enumerate(players)
                           if p.team == opp_team and p.primary_position != 'P']

            if opp_hitters:
                # If pitcher selected, limit opposing hitters
                prob += pulp.lpSum([
                    player_vars[h_idx] for h_idx in opp_hitters
                ]) <= self.config.max_hitters_vs_pitcher + \
                        10 * (1 - player_vars[p_idx])

    def _get_opposing_team(self, player: UnifiedPlayer) -> Optional[str]:
        """Extract opposing team from game info"""
        if hasattr(player, 'game_info') and player.game_info:
            # Parse game info (e.g., "NYY@BOS" or "LAD vs SF")
            import re
            match = re.search(r'(\w+)[@vs]+(\w+)', player.game_info)
            if match:
                team1, team2 = match.groups()
                return team2 if team1 == player.team else team1
        return None

    def _extract_solution(self, players: List[UnifiedPlayer],
                          player_vars: Dict,
                          position_vars: Dict) -> Tuple[List[UnifiedPlayer], float]:
        """Extract lineup from solved MILP"""
        lineup = []
        total_score = 0

        for i, player in enumerate(players):
            if player_vars[i].value() == 1:
                # Find assigned position
                assigned_pos = None
                for pos in player.positions:
                    if (i, pos) in position_vars and position_vars[(i, pos)].value() == 1:
                        assigned_pos = pos
                        break

                # Create player copy with assigned position
                player_copy = player.copy()
                player_copy.assigned_position = assigned_pos
                lineup.append(player_copy)
                # Use the same score that was used in optimization
                total_score += self.get_optimization_score(player)

        return lineup, total_score


class StrategyFilter:
    """
    Creates player pools based on strategy WITHOUT modifying scores
    """

    def __init__(self):
        self.logger = logger

    def apply_strategy_filter(self, players: List[UnifiedPlayer],
                              strategy: str, manual_input: str = "") -> List[UnifiedPlayer]:
        """
        Creates player pools WITHOUT modifying scores
        """

        # Parse manual selections
        manual_players = self._parse_manual_selections(players, manual_input)

        # Get confirmed players
        confirmed_players = [p for p in players if p.is_confirmed]

        # Build pool based on strategy
        if strategy == 'confirmed_plus_manual':
            base_pool = list(set(confirmed_players + manual_players))

            if len(base_pool) < 40:
                remaining = [p for p in players if p not in base_pool]
                remaining.sort(key=lambda x: x.enhanced_score, reverse=True)
                base_pool.extend(remaining[:40 - len(base_pool)])

            return base_pool

        elif strategy == 'manual_only':
            return manual_players

        elif strategy == 'top_value':
            players_with_value = [(p, p.enhanced_score / (p.salary / 1000))
                                  for p in players if p.salary > 0]
            players_with_value.sort(key=lambda x: x[1], reverse=True)
            cutoff = max(20, len(players) // 2)
            return [p for p, _ in players_with_value[:cutoff]]

        elif strategy == 'high_ceiling':
            ceiling_players = []

            for player in players:
                # Must have real performance data
                ceiling_score = 0

                # Check recent form
                if hasattr(player, '_recent_performance') and player._recent_performance:
                    form = player._recent_performance.get('form_score', 1.0)
                    if form > 1.15:
                        ceiling_score += 2
                    elif form > 1.10:
                        ceiling_score += 1

                # Check Vegas data
                if hasattr(player, '_vegas_data') and player._vegas_data:
                    implied = player._vegas_data.get('implied_total', 0)
                    if implied > 5.0:
                        ceiling_score += 2
                    elif implied > 4.5:
                        ceiling_score += 1

                # Check recent hot streak
                if hasattr(player, 'dff_l5_avg') and player.base_projection > 0:
                    if player.dff_l5_avg / player.base_projection > 1.20:
                        ceiling_score += 2

                if ceiling_score >= 2:  # Multiple positive indicators
                    ceiling_players.append(player)

            # Ensure minimum pool size
            if len(ceiling_players) < 30:
                remaining = [p for p in players if p not in ceiling_players]
                remaining.sort(key=lambda x: x.enhanced_score, reverse=True)
                ceiling_players.extend(remaining[:30 - len(ceiling_players)])

            return ceiling_players

        elif strategy == 'balanced':
            base_set = set(confirmed_players + manual_players)

            # Add high-value players
            value_players = sorted(players,
                                   key=lambda x: x.enhanced_score / (x.salary / 1000) if x.salary > 0 else 0,
                                   reverse=True)

            for player in value_players:
                if player not in base_set:
                    base_set.add(player)
                    if len(base_set) >= 60:
                        break

            return list(base_set)

        else:  # 'all_players' or default
            return players

    def _parse_manual_selections(self, players: List[UnifiedPlayer],
                                 manual_input: str) -> List[UnifiedPlayer]:
        """Parse manual player selections"""
        if not manual_input:
            return []

        manual_players = []
        manual_names = []

        # Try different delimiters
        for delimiter in [',', ';', '\n', '|']:
            if delimiter in manual_input:
                manual_names = [n.strip() for n in manual_input.split(delimiter) if n.strip()]
                break
        else:
            if manual_input.strip():
                manual_names = [manual_input.strip()]

        # Match players
        for manual_name in manual_names:
            manual_lower = manual_name.lower()
            matched = False

            for player in players:
                player_lower = player.name.lower()

                # Check full name or last name match
                if (manual_lower in player_lower or
                        (len(manual_lower.split()) == 1 and
                         manual_lower in player_lower.split()[-1].lower())):
                    manual_players.append(player)
                    player.is_manual_selected = True
                    matched = True
                    self.logger.info(f"✓ Manual selection matched: {player.name}")
                    break

            if not matched:
                self.logger.warning(f"⚠️ Manual selection not found: {manual_name}")

        return manual_players


# Example usage and testing
if __name__ == "__main__":
    # Test configuration
    config = OptimizationConfig(
        salary_cap=50000,
        min_salary_usage=0.95,
        use_correlation=True,
        max_hitters_vs_pitcher=2
    )

    optimizer = UnifiedMILPOptimizer(config)

    print("✅ Unified MILP Optimizer initialized")
    print("📊 Using real data sources only (no fake fallbacks)")
    print("🎯 Clean optimization with no manual/confirmed bonuses")
