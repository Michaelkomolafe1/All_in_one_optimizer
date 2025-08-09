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

    def verify_position_availability(self, players, position_groups):
        """Verify we have enough players for each position"""
        requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        self.logger.info("\n📊 POSITION AVAILABILITY CHECK:")
        self.logger.info("-" * 40)

        all_good = True
        for pos, required in requirements.items():
            available = len(position_groups.get(pos, []))
            status = "✅" if available >= required else "❌"
            self.logger.info(f"{pos}: Need {required}, Have {available} {status}")

            if available < required:
                all_good = False
                self.logger.warning(f"  ⚠️ Not enough {pos} players!")

        if not all_good:
            self.logger.error("CRITICAL: Cannot create valid lineup with current player pool!")
            return False
        return True

    def add_tournament_constraints(self, prob, player_vars, players):
        """
        Add constraints based on tournament-winning patterns
        Data: 83.2% of GPP winners use 4-5 player stacks
        """
        contest_type = getattr(self.config, 'contest_type', 'gpp')

        if contest_type == 'gpp':
            # GPP CONSTRAINTS - 83.2% of winners use these patterns

            # Group players by team (excluding pitchers)
            teams = {}
            for i, player in enumerate(players):
                if player.primary_position not in ['P', 'SP', 'RP']:
                    if player.team not in teams:
                        teams[player.team] = []
                    teams[player.team].append(i)

            # 1. ENFORCE MAXIMUM PLAYERS PER TEAM (allow stacking)
            for team, indices in teams.items():
                if len(indices) >= 4:  # Only constrain teams that CAN stack
                    # Allow up to 5 players from same team (56.7% of winners use 5-man stacks)
                    prob += pulp.lpSum([player_vars[i] for i in indices]) <= 5, f"max_5_from_{team}"
                elif len(indices) > 0:
                    # For teams with fewer players, limit to what's available
                    prob += pulp.lpSum([player_vars[i] for i in indices]) <= len(indices), f"max_available_{team}"

            # 2. LIMIT PITCHER CHALK (optional but helps GPP)
            pitcher_indices = [i for i, p in enumerate(players)
                               if p.primary_position in ['P', 'SP', 'RP']]

            # Identify high-ownership pitchers (if ownership data exists)
            chalk_pitchers = []
            for i in pitcher_indices:
                if hasattr(players[i], 'projected_ownership'):
                    if players[i].projected_ownership > 30:
                        chalk_pitchers.append(i)

            if chalk_pitchers:
                # Max 1 chalk pitcher (encourages differentiation)
                prob += pulp.lpSum([player_vars[i] for i in chalk_pitchers]) <= 1, "limit_chalk_pitchers"

            # 3. ENSURE LINEUP DIVERSITY (prevent 8 different teams)
            # Most winners use 3-5 different teams total
            # We don't need to enforce this explicitly because stacking bonuses handle it

        else:  # CASH CONSTRAINTS
            # Different constraints for cash games

            # 1. LIMIT PLAYERS PER TEAM (more conservative for cash)
            teams = {}
            for i, player in enumerate(players):
                if player.primary_position not in ['P', 'SP', 'RP']:
                    if player.team not in teams:
                        teams[player.team] = []
                    teams[player.team].append(i)

            for team, indices in teams.items():
                if indices:
                    # Max 3 from same team in cash (avoid over-correlation)
                    prob += pulp.lpSum([player_vars[i] for i in indices]) <= 3, f"cash_max_3_{team}"

            # 2. ENFORCE HIGH K-RATE PITCHERS (if data available)
            pitcher_indices = [i for i, p in enumerate(players)
                               if p.primary_position in ['P', 'SP', 'RP']]

            elite_k_pitchers = []
            for i in pitcher_indices:
                if hasattr(players[i], 'k_rate'):
                    if players[i].k_rate >= 25:
                        elite_k_pitchers.append(i)

            if len(elite_k_pitchers) >= 2:
                # Try to get at least 1 high-K pitcher
                prob += pulp.lpSum([player_vars[i] for i in elite_k_pitchers]) >= 1, "min_1_elite_k_pitcher"

            # 3. BATTING ORDER PREFERENCE (if data available)
            top_order_hitters = []
            bottom_order_hitters = []

            for i, p in enumerate(players):
                if p.primary_position not in ['P', 'SP', 'RP']:
                    if hasattr(p, 'batting_order') and p.batting_order:
                        if p.batting_order <= 5:
                            top_order_hitters.append(i)
                        elif p.batting_order >= 7:
                            bottom_order_hitters.append(i)

            if len(top_order_hitters) >= 6:
                # Prefer at least 6 hitters from top of order
                prob += pulp.lpSum([player_vars[i] for i in top_order_hitters]) >= 6, "prefer_top_order"

            if bottom_order_hitters:
                # Limit bottom of order hitters
                prob += pulp.lpSum([player_vars[i] for i in bottom_order_hitters]) <= 2, "limit_bottom_order"

    def apply_correlation_bonuses(self, players):
        """
        Apply correlation bonuses for GPP stacking
        Based on data: 83.2% of GPP winners use 4-5 player stacks
        """
        # Only apply for GPP
        contest_type = getattr(self.config, 'contest_type', 'gpp')
        if contest_type != 'gpp':
            return

        logger.info("\n🎯 APPLYING GPP STACKING BONUSES (83.2% of winners use 4-5 stacks)")

        # Analyze teams for stacking potential
        team_analysis = {}
        for p in players:
            if p.primary_position not in ['P', 'SP', 'RP']:
                if p.team not in team_analysis:
                    team_analysis[p.team] = {
                        'players': [],
                        'total_proj': 0,
                        'batting_orders': [],
                        'team_total': getattr(p, 'implied_team_score', 4.5)
                    }

                team_analysis[p.team]['players'].append(p)
                team_analysis[p.team]['total_proj'] += p.base_projection

                if hasattr(p, 'batting_order') and p.batting_order:
                    team_analysis[p.team]['batting_orders'].append(p.batting_order)

        # Score teams for stacking
        stack_candidates = []
        for team, data in team_analysis.items():
            if len(data['players']) >= 4:  # Need at least 4 for a stack
                # Calculate stack score
                top_5_avg = sum(sorted([p.base_projection for p in data['players']], reverse=True)[:5]) / 5

                # Bonus for consecutive batting orders (highest correlation)
                consecutive_bonus = 0
                if data['batting_orders']:
                    sorted_orders = sorted(data['batting_orders'])
                    for i in range(len(sorted_orders) - 1):
                        if sorted_orders[i + 1] - sorted_orders[i] == 1:
                            consecutive_bonus += 0.2  # 20% bonus per consecutive pair

                # Team total bonus (5+ runs is elite)
                total_bonus = 1.0
                if data['team_total'] >= 5.5:
                    total_bonus = 1.5
                elif data['team_total'] >= 5.0:
                    total_bonus = 1.3
                elif data['team_total'] >= 4.5:
                    total_bonus = 1.15

                stack_score = top_5_avg * total_bonus * (1 + consecutive_bonus)
                stack_candidates.append((team, stack_score, len(data['players'])))

        # Sort by stack score
        stack_candidates.sort(key=lambda x: x[1], reverse=True)

        if stack_candidates:
            # Apply bonuses to top 3 stacking teams
            for rank, (team, score, count) in enumerate(stack_candidates[:3]):
                if rank == 0:
                    # Primary stack - aim for 5 players (56.7% of winners)
                    multiplier = 2.0
                    logger.info(f"  Primary stack: {team} ({count} players) - 2.0x boost")
                elif rank == 1:
                    # Secondary stack option
                    multiplier = 1.5
                    logger.info(f"  Secondary: {team} ({count} players) - 1.5x boost")
                else:
                    multiplier = 1.25
                    logger.info(f"  Tertiary: {team} ({count} players) - 1.25x boost")

                # Apply bonuses with batting order consideration
                for p in team_analysis[team]['players']:
                    old_score = p.optimization_score

                    # Extra bonus for consecutive lineup spots (1-2-3-4-5)
                    order_bonus = 1.0
                    if hasattr(p, 'batting_order') and p.batting_order:
                        if 1 <= p.batting_order <= 5:
                            order_bonus = 1.2  # Top 5 hitters
                        elif p.batting_order >= 7:
                            order_bonus = 0.9  # Discount bottom of order

                    p.optimization_score = p.base_projection * multiplier * order_bonus

                    logger.debug(f"    {p.name}: {old_score:.1f} -> {p.optimization_score:.1f}")


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

    def apply_strategy_filter(self, players: List, strategy: str) -> List:
        """
        Apply strategy-specific filtering and scoring to players
        CRITICAL: Prepares players for stacking in GPP
        """
        if not players:
            return []

        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"APPLYING STRATEGY FILTER: {strategy}")
        self.logger.info(f"{'=' * 60}")
        self.logger.info(f"Input players: {len(players)}")

        # First normalize all positions
        for player in players:
            # Normalize SP/RP to P
            if player.position in ['SP', 'RP']:
                player.position = 'P'
                player.primary_position = 'P'
            # Handle multi-position eligibility
            if hasattr(player, 'positions'):
                player.positions = ['P' if pos in ['SP', 'RP'] else pos for pos in player.positions]

        # Count games/teams for slate size detection
        unique_teams = set(p.team for p in players if hasattr(p, 'team'))
        num_games = len(unique_teams) // 2  # Approximate

        self.logger.info(f"Detected {num_games} games, {len(unique_teams)} teams")

        # SMALL SLATE HANDLING - Keep all players
        if num_games <= 3 or len(players) < 50:
            self.logger.info(f"Small slate/pool detected - keeping ALL {len(players)} players")

            # Just adjust scores based on strategy, don't filter
            for player in players:
                base = getattr(player, 'base_projection', 10.0) or 10.0

                if strategy in ['tournament_winner_gpp', 'correlation_value']:
                    # Boost players on high-scoring teams for stacking
                    team_total = getattr(player, 'implied_team_score', 4.5)
                    if team_total >= 5.0 and player.primary_position != 'P':
                        player.optimization_score = base * 1.3  # Boost for stacking
                    else:
                        player.optimization_score = base
                else:
                    player.optimization_score = base

            return players

        # NORMAL FILTERING FOR LARGER SLATES
        # =====================================

        filtered = []

        if strategy == 'tournament_winner_gpp':
            # GPP: Focus on stacking and ceiling plays
            pitchers = [p for p in players if p.primary_position == 'P']
            hitters = [p for p in players if p.primary_position != 'P']

            # Score players for GPP
            for p in players:
                base = getattr(p, 'base_projection', 10.0) or 10.0

                if p.primary_position == 'P':
                    # Pitchers: K upside and ownership leverage
                    k_rate = getattr(p, 'k_rate', 20)
                    ownership = getattr(p, 'ownership_projection', 15)

                    multiplier = 1.0
                    if k_rate >= 28:
                        multiplier *= 1.25
                    if ownership < 20:
                        multiplier *= 1.15

                    p.optimization_score = base * multiplier

                else:  # Hitters
                    # Focus on team stacks and power
                    team_total = getattr(p, 'implied_team_score', 4.5)
                    batting_order = getattr(p, 'batting_order', 9)
                    ownership = getattr(p, 'ownership_projection', 15)

                    multiplier = 1.0

                    # CRITICAL: Boost stackable teams
                    if team_total >= 5.5:
                        multiplier *= 1.5  # Big boost for high-scoring teams
                    elif team_total >= 5.0:
                        multiplier *= 1.3

                    # Batting order matters for stacking
                    if batting_order <= 5:
                        multiplier *= 1.2
                    elif batting_order <= 7:
                        multiplier *= 1.1
                    else:
                        multiplier *= 0.8  # Penalize bottom of order

                    # Ownership leverage
                    if ownership < 10:
                        multiplier *= 1.2
                    elif ownership > 25:
                        multiplier *= 0.9

                    p.optimization_score = base * multiplier
                    p.stack_eligible = (team_total >= 5.0 and batting_order <= 6)

            # Sort and take top players
            pitchers.sort(key=lambda x: getattr(x, 'optimization_score', 0), reverse=True)
            hitters.sort(key=lambda x: getattr(x, 'optimization_score', 0), reverse=True)

            # Take more hitters to ensure stacking is possible
            filtered = pitchers[:20] + hitters[:120]

        elif strategy == 'correlation_value':
            # Similar to tournament_winner but focus on value
            for p in players:
                base = getattr(p, 'base_projection', 10.0) or 10.0
                value = (base / max(p.salary, 1)) * 1000

                if p.primary_position != 'P':
                    team_total = getattr(p, 'implied_team_score', 4.5)
                    if team_total >= 5.0 and value >= 3.0:
                        p.optimization_score = base * 1.4  # Value in good spots
                    else:
                        p.optimization_score = base
                else:
                    p.optimization_score = base

            filtered = sorted(players, key=lambda x: getattr(x, 'optimization_score', 0), reverse=True)[:140]

        elif strategy == 'projection_monster':
            # Cash: Pure projections with consistency
            for p in players:
                base = getattr(p, 'base_projection', 10.0) or 10.0
                consistency = getattr(p, 'consistency_score', 50)
                recent = getattr(p, 'recent_form', 50)

                # Weight towards consistent players
                p.optimization_score = base * (1 + consistency / 200) * (1 + recent / 200)

            filtered = sorted(players, key=lambda x: getattr(x, 'optimization_score', 0), reverse=True)[:120]

        elif strategy == 'pitcher_dominance':
            # Cash: Elite pitchers + value bats
            pitchers = [p for p in players if p.primary_position == 'P']
            hitters = [p for p in players if p.primary_position != 'P']

            # Score pitchers heavily
            for p in pitchers:
                base = getattr(p, 'base_projection', 15.0) or 15.0
                k_rate = getattr(p, 'k_rate', 20)

                if k_rate >= 25:
                    p.optimization_score = base * 1.3
                else:
                    p.optimization_score = base

            # Score hitters by value
            for h in hitters:
                base = getattr(h, 'base_projection', 10.0) or 10.0
                value = (base / max(h.salary, 1)) * 1000
                h.optimization_score = base * (1 + max(0, value - 3) * 0.1)

            pitchers.sort(key=lambda x: getattr(x, 'optimization_score', 0), reverse=True)
            hitters.sort(key=lambda x: getattr(x, 'optimization_score', 0), reverse=True)

            filtered = pitchers[:15] + hitters[:100]

        else:
            # Default: just use base projections
            for p in players:
                p.optimization_score = getattr(p, 'base_projection', 10.0) or 10.0
            filtered = players[:150]

        # CRITICAL: Ensure minimum positions are available
        self.logger.info(f"\nFiltered to {len(filtered)} players")

        # Check position availability
        position_counts = {}
        for p in filtered:
            pos = p.primary_position
            position_counts[pos] = position_counts.get(pos, 0) + 1

        # Minimum requirements
        min_needed = {'P': 4, 'C': 2, '1B': 2, '2B': 2, '3B': 2, 'SS': 2, 'OF': 6}

        for pos, needed in min_needed.items():
            current = position_counts.get(pos, 0)
            if current < needed:
                self.logger.warning(f"Position {pos}: Only {current}, need {needed} - adding more")

                # Find more players for this position
                candidates = [p for p in players if p.primary_position == pos and p not in filtered]
                candidates.sort(key=lambda x: getattr(x, 'base_projection', 0), reverse=True)

                to_add = needed - current
                filtered.extend(candidates[:to_add])

        # For GPP, ensure we have stackable teams
        if strategy in ['tournament_winner_gpp', 'correlation_value']:
            team_counts = {}
            for p in filtered:
                if p.primary_position != 'P':
                    team_counts[p.team] = team_counts.get(p.team, 0) + 1

            stackable = [t for t, c in team_counts.items() if c >= 4]
            self.logger.info(f"Stackable teams (4+ hitters): {stackable}")

            if not stackable:
                self.logger.warning("No stackable teams! Adding more hitters...")
                # Add more hitters from high-scoring teams
                high_scoring_teams = []
                for p in players:
                    if p.primary_position != 'P' and p not in filtered:
                        team_total = getattr(p, 'implied_team_score', 4.5)
                        if team_total >= 5.0:
                            filtered.append(p)
                            high_scoring_teams.append(p.team)

                self.logger.info(f"Added hitters from teams: {set(high_scoring_teams)}")

        self.logger.info(f"Final filtered pool: {len(filtered)} players")

        # Final position check
        final_pos_counts = {}
        for p in filtered:
            pos = p.primary_position
            final_pos_counts[pos] = final_pos_counts.get(pos, 0) + 1

        self.logger.info("Final position counts:")
        for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
            count = final_pos_counts.get(pos, 0)
            status = "✅" if count >= min_needed.get(pos, 0) else "⚠️"
            self.logger.info(f"  {pos}: {count} {status}")

        return filtered


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

    def calculate_player_scores(self, players):
        """Calculate optimization scores based on strategy"""
        # Get contest type
        contest_type = getattr(self.config, 'contest_type', 'gpp')

        if contest_type == 'cash':
            # CASH: Focus on floor and consistency
            for player in players:
                if player.primary_position in ['P', 'SP', 'RP']:
                    # Pitchers: K-rate and win probability
                    score = player.base_projection

                    # K-rate bonus
                    if hasattr(player, 'k_rate'):
                        if player.k_rate >= 25:
                            score *= 1.2
                        elif player.k_rate < 20:
                            score *= 0.9

                    # Win probability
                    if hasattr(player, 'win_odds'):
                        if player.win_odds >= 0.6:
                            score *= 1.15

                    # Use floor for cash games
                    if hasattr(player, 'floor'):
                        score = player.floor * 0.7 + score * 0.3

                    player.optimization_score = score
                else:
                    # Hitters: Consistency and batting order
                    score = player.base_projection

                    # Batting order bonus
                    if hasattr(player, 'batting_order') and player.batting_order:
                        if player.batting_order <= 3:
                            score *= 1.2
                        elif player.batting_order <= 5:
                            score *= 1.1
                        elif player.batting_order >= 7:
                            score *= 0.85

                    # Consistency bonus
                    if hasattr(player, 'consistency_score'):
                        score *= (0.8 + player.consistency_score * 0.4)

                    player.optimization_score = score
        else:
            # GPP: Start with base projections
            for player in players:
                player.optimization_score = getattr(player, 'enhanced_score', player.base_projection)

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
        SIMPLIFIED WORKING VERSION - with proper multi-position handling
        """
        if not players:
            logger.error("No players to optimize")
            return [], 0

        logger.info(f"\n{'=' * 60}")
        logger.info(f"MILP OPTIMIZATION - {contest_type.upper()}")
        logger.info(f"{'=' * 60}")
        logger.info(f"Players in pool: {len(players)}")

        # Create optimization problem
        prob = pulp.LpProblem("DFS_Optimizer", pulp.LpMaximize)

        # Decision variables for players
        player_vars = pulp.LpVariable.dicts(
            "players",
            range(len(players)),
            cat="Binary"
        )

        # OBJECTIVE: Maximize optimization score
        prob += pulp.lpSum([
            players[i].optimization_score * player_vars[i]
            for i in range(len(players))
        ])

        # ============================================
        # BASIC CONSTRAINTS
        # ============================================

        # 1. Salary constraint
        prob += pulp.lpSum([
            players[i].salary * player_vars[i]
            for i in range(len(players))
        ]) <= self.config.salary_cap, "max_salary"

        prob += pulp.lpSum([
            players[i].salary * player_vars[i]
            for i in range(len(players))
        ]) >= self.config.salary_cap * 0.90, "min_salary"

        # 2. Roster size = 10 players
        prob += pulp.lpSum(player_vars.values()) == 10, "roster_size"

        # 3. Position requirements - NEW APPROACH FOR MULTI-POSITION

        # First, identify single-position and multi-position players
        single_position_players = {
            'P': [], 'C': [], '1B': [], '2B': [],
            '3B': [], 'SS': [], 'OF': []
        }

        multi_position_players = []  # List of (player_index, [positions])

        for i, player in enumerate(players):
            positions_str = player.position

            # Normalize pitcher positions
            if positions_str in ['SP', 'RP', 'P']:
                positions_str = 'P'

            if '/' in positions_str:
                # Multi-position player
                positions = []
                for pos in positions_str.split('/'):
                    if pos in ['SP', 'RP']:
                        pos = 'P'
                    if pos in single_position_players:
                        positions.append(pos)
                multi_position_players.append((i, positions))
                print(f"DEBUG: Player {i} ({player.name}) is multi-position: {positions}")
            else:
                # Single position player
                pos = positions_str
                if pos in ['SP', 'RP']:
                    pos = 'P'
                if pos in single_position_players:
                    single_position_players[pos].append(i)

        print(f"DEBUG: Single position players: {[(k, len(v)) for k, v in single_position_players.items()]}")
        print(f"DEBUG: Multi-position players: {len(multi_position_players)}")

        # Create position assignment variables for multi-position players
        position_assignments = {}
        for player_idx, positions in multi_position_players:
            for pos in positions:
                var_name = f"assign_{player_idx}_to_{pos}"
                position_assignments[var_name] = pulp.LpVariable(var_name, cat="Binary")
                print(f"DEBUG: Created variable {var_name}")

        # Constraint: Multi-position player can only be assigned to one position
        for player_idx, positions in multi_position_players:
            assignment_vars = []
            for pos in positions:
                var_name = f"assign_{player_idx}_to_{pos}"
                assignment_vars.append(position_assignments[var_name])

            # If player is selected, they must be assigned to exactly one position
            # If not selected, they can't be assigned to any position
            prob += pulp.lpSum(assignment_vars) == player_vars[player_idx], f"one_position_for_player_{player_idx}"

        # Position requirements
        requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        for pos, required in requirements.items():
            # Count players for this position
            position_sum = []

            # Add single-position players
            for player_idx in single_position_players[pos]:
                position_sum.append(player_vars[player_idx])

            # Add multi-position players who can fill this position
            for player_idx, positions in multi_position_players:
                if pos in positions:
                    var_name = f"assign_{player_idx}_to_{pos}"
                    position_sum.append(position_assignments[var_name])

            # Must have exactly the required number
            if position_sum:  # Only add constraint if there are players for this position
                prob += pulp.lpSum(position_sum) == required, f"exactly_{required}_{pos}"
                print(f"DEBUG: Added constraint for {pos}: need {required}, have {len(position_sum)} eligible")

        # Each player can only be selected once (already handled by Binary variables)

        print("DEBUG: About to solve")

        try:
            # Solve with timeout
            solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=10)
            prob.solve(solver)

            print(f"DEBUG: Solver returned status: {prob.status} = {pulp.LpStatus[prob.status]}")

            if prob.status == pulp.LpStatusOptimal:
                print("DEBUG: Solution is optimal, building lineup")
                lineup = []
                for i in range(len(players)):
                    if player_vars[i].varValue == 1:
                        lineup.append(players[i])

                        # Check position assignment for multi-position players
                        is_multi = False
                        for player_idx, positions in multi_position_players:
                            if player_idx == i:
                                is_multi = True
                                for pos in positions:
                                    var_name = f"assign_{player_idx}_to_{pos}"
                                    if position_assignments[var_name].varValue == 1:
                                        print(f"  Player {i} ({players[i].name}) assigned to {pos}")
                                break

                        if not is_multi:
                            print(f"  Player {i} ({players[i].name}) at {players[i].position}")

                print(f"DEBUG: Built lineup with {len(lineup)} players")

                if len(lineup) != 10:
                    logger.error(f"Invalid lineup size: {len(lineup)}")
                    return [], 0

                total_score = sum(getattr(p, 'optimization_score', 0) for p in lineup)
                total_salary = sum(p.salary for p in lineup)

                logger.info(f"✅ LINEUP FOUND - Score: {total_score:.1f}, Salary: ${total_salary}")

                return lineup, total_score

            else:
                print(f"DEBUG: Solver failed with status {prob.status}")
                return [], 0

        except Exception as e:
            print(f"DEBUG: EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            return [], 0

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