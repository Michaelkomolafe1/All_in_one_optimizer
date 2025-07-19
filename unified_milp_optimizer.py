#!/usr/bin/env python3
"""
UNIFIED MILP OPTIMIZER - FIXED COMPLETE VERSION
==============================================
Clean implementation with all optimizations included
"""

import copy
from unified_config_manager import get_config_value
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pulp

# Import unified player model
from unified_player_model import UnifiedPlayer

# Import new optimization modules

try:
    from performance_optimizer import get_performance_optimizer
    from unified_scoring_engine import get_scoring_engine

    OPTIMIZATION_MODULES_AVAILABLE = True
except ImportError:
    OPTIMIZATION_MODULES_AVAILABLE = False
    print("⚠️ New optimization modules not available, using fallback")

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
                "P": 2,
                "C": 1,
                "1B": 1,
                "2B": 1,
                "3B": 1,
                "SS": 1,
                "OF": 3,
            }


class UnifiedMILPOptimizer:
    def __init__(self, config: OptimizationConfig = None):
        """
        Initializes the optimization engine with configuration and data sources.
        """
        self.config = config or OptimizationConfig()
        self.logger = logger

        # FIXED: Call the configuration loading method
        self._load_dfs_config()

        # Load park factors if available
        self.park_factors = self._load_park_factors()

        # Load real data sources
        self._initialize_data_sources()

    def _load_dfs_config(self):
        """
        FIXED: Load configuration from unified config system or fallback.
        This method is now a properly-defined method of the class.
        """
        config_loaded = False

        # Try to load from unified config system first
        try:
            # Assumes get_config_value is defined elsewhere
            self.config.salary_cap = get_config_value("optimization.salary_cap", 50000)
            self.config.min_salary_usage = get_config_value("optimization.min_salary_usage", 0.95)
            self.config.max_players_per_team = get_config_value("optimization.max_players_per_team", 4)
            self.max_form_analysis_players = get_config_value("optimization.max_form_analysis_players", 100)

            self.logger.info("✅ Loaded configuration from unified config system")
            config_loaded = True
        except Exception as e:
            self.logger.warning(f"Could not load unified config: {e}")
            # Keep defaults

        # Fallback to dfs_config.json if unified config failed to load
        if not config_loaded:
            try:
                import json
                with open("dfs_config.json", "r") as f:
                    config_data = json.load(f)

                self.config.salary_cap = config_data.get("optimization", {}).get("salary_cap", 50000)
                self.config.min_salary_usage = config_data.get("optimization", {}).get("min_salary_usage", 0.95)
                self.config.max_players_per_team = config_data.get("optimization", {}).get("max_players_per_team", 4)
                self.max_form_analysis_players = config_data.get("optimization", {}).get("max_form_analysis_players", 100)

                self.logger.info("✅ Loaded configuration from dfs_config.json")
            except Exception as e:
                self.logger.warning(f"Could not load dfs_config.json: {e}")
                # Use defaults


    def _load_park_factors(self) -> Dict[str, float]:
        """Load park factors from file or use defaults"""
        try:
            with open("park_factors.json", "r") as f:
                return json.load(f)
        except:
            # Default park factors for major parks
            return {
                "COL": 1.15,  # Coors Field
                "BOS": 1.08,  # Fenway
                "TEX": 1.06,  # Globe Life
                "CIN": 1.05,  # Great American
                "MIL": 1.04,  # Miller Park
                "SF": 0.92,  # Oracle Park
                "SD": 0.93,  # Petco
                "NYM": 0.95,  # Citi Field
                "SEA": 0.96,  # T-Mobile
                "MIA": 0.97,  # Marlins Park
            }

        from dataclasses import dataclass

        @dataclass
        class OptimizationResult:
            lineup: list
            total_salary: int
            projected_points: float
            strategy: str

        required = self.config.position_requirements
        pos_map = {p.primary_position: [] for pos in required} # <- Error line is likely here or nearby
        for p in players:

        try:
            from dataclasses import dataclass

            @dataclass
            class OptimizationResult:
                lineup: list
                total_salary: int
                projected_points: float
                strategy: str

            # Convert UnifiedPlayer objects to dict format for basic optimization
            player_dicts = []
            for player in players:
                player_dict = {
                    'name': player.name,
                    'position': player.primary_position,
                    'team': player.team,
                    'salary': player.salary,
                    'projected_points': player.base_projection,
                    'enhanced_score': getattr(player, 'enhanced_score', player.base_projection)
                }
                player_dicts.append(player_dict)

            # Position requirements for DraftKings
            position_needs = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

            # Simple greedy optimization for now
            lineup = []
            used_salary = 0

            for pos, count in position_needs.items():
                pos_players = [p for p in player_dicts if p['position'] == pos and p['projected_points'] > 0]
                pos_players.sort(key=lambda x: x['projected_points'], reverse=True)

                added = 0
                for player in pos_players:
                    if added < count and used_salary + player['salary'] <= self.config.salary_cap:
                        lineup.append(player)
                        used_salary += player['salary']
                        added += 1

            total_points = sum(p['projected_points'] for p in lineup)

            return OptimizationResult(
                lineup=lineup,
                total_salary=used_salary,
                projected_points=total_points,
                strategy=strategy
            )

        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            return None

    def _load_dfs_config(self):
        """Load configuration from unified config system"""
        config_loaded = False

        try:
            # Use unified config
            self.config.salary_cap = get_config_value("optimization.salary_cap", 50000)
            self.config.min_salary_usage = get_config_value("optimization.min_salary_usage", 0.95)
            self.config.max_players_per_team = get_config_value("optimization.max_players_per_team", 4)
            self.max_form_analysis_players = get_config_value("optimization.max_form_analysis_players", 100)

            self.logger.info("✅ Loaded configuration from unified config system")
            config_loaded = True
        except Exception as e:
            self.logger.warning(f"Could not load unified config: {e}")

        # Fallback to dfs_config.json
        if not config_loaded:
            try:
                import json
                with open("dfs_config.json", "r") as f:
                    config_data = json.load(f)

                self.config.salary_cap = config_data.get("optimization", {}).get("salary_cap", 50000)
                self.config.min_salary_usage = config_data.get("optimization", {}).get("min_salary_usage", 0.95)
                self.config.max_players_per_team = config_data.get("optimization", {}).get("max_players_per_team", 4)
                self.max_form_analysis_players = config_data.get("optimization", {}).get("max_form_analysis_players",
                                                                                         100)

                self.logger.info("✅ Loaded configuration from dfs_config.json")
            except Exception as e:
                self.logger.warning(f"Could not load dfs_config.json: {e}")

    def _load_park_factors(self):
        """Load park factors if available"""
        return {}

    def _initialize_data_sources(self):
        """Initialize data sources"""
        pass



    def _initialize_data_sources(self):
        """Initialize connections to real data sources"""
        # This is a placeholder - implement based on your data sources

    def get_optimization_score(self, player: UnifiedPlayer) -> float:
        """
        Get the player's score for optimization (includes pre-calculated bonuses)
        This is the score that MILP will use.
        """
        # Check if player has optimization-specific score
        if hasattr(player, "optimization_score"):
            return player.optimization_score

        # Otherwise use enhanced score
        return player.enhanced_score

    def prepare_players_for_optimization(self, players: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """
        Pre-calculate all bonuses and penalties before optimization.
        This avoids quadratic terms in MILP.
        """
        # Calculate correlation bonuses if enabled
        if self.config.use_correlation:
            # Group players by team for stacking bonuses
            team_groups = {}
            for player in players:
                if player.team not in team_groups:
                    team_groups[player.team] = []
                team_groups[player.team].append(player)

            # Apply stacking bonuses
            for team, team_players in team_groups.items():
                if len(team_players) >= 3:  # Potential stack
                    # Find best stack candidates (e.g., 1-3-5 batting order)
                    stack_candidates = sorted(
                        team_players, key=lambda p: getattr(p, "batting_order", None) or 999
                    )[:5]

                    # Apply small bonus to encourage stacking
                    for player in stack_candidates:
                        if hasattr(player, "batting_order") and player.batting_order in [1, 3, 5]:
                            # Add 5% bonus for stack candidates
                            player.optimization_score = player.enhanced_score * 1.05
                        else:
                            player.optimization_score = player.enhanced_score
                else:
                    # No stacking bonus for teams with few players
                    for player in team_players:
                        player.optimization_score = player.enhanced_score
        else:
            # No correlation - just use enhanced score
            for player in players:
                player.optimization_score = player.enhanced_score

        return players

    def calculate_player_scores(self, players: List[UnifiedPlayer]) -> List[UnifiedPlayer]:
        """
        Calculate enhanced scores for all players using available data
        """
        if OPTIMIZATION_MODULES_AVAILABLE:
            # Use new scoring system
            scoring_engine = get_scoring_engine()
            perf_opt = get_performance_optimizer()

            # Use score_player method
            score_player = scoring_engine.calculate_score

            # Process in batches
            scores = perf_opt.batch_process(players, score_player, batch_size=50, max_workers=4)

            # Apply scores
            for player, score in zip(players, scores):
                if score is not None:
                    player.enhanced_score = score
                    player._score_calculated = True

            self.logger.info(f"Calculated scores for {len(players)} players")

        else:
            # Fallback to original calculation method
            self.logger.info("Using fallback score calculation")

            # Count how many are already enriched
            already_enriched = sum(
                1 for p in players if hasattr(p, "_is_enriched") and p._is_enriched
            )
            if already_enriched > 0:
                print(f"ℹ️ Skipping {already_enriched}/{len(players)} already enriched players")

            # Determine how many players to analyze for form
            getattr(self, "max_form_analysis_players", None)

            # Sort players by base projection for prioritization
            sorted_players = sorted(
                players, key=lambda p: getattr(p, "base_projection", 0), reverse=True
            )

            for i, player in enumerate(sorted_players):
                # Skip if already enriched
                if hasattr(player, "_is_enriched") and player._is_enriched:
                    continue

                # Use existing calculate_enhanced_score method
                if hasattr(player, "calculate_enhanced_score"):
                    player.calculate_enhanced_score()
                else:
                    # Fallback - just use base projection
                    player.enhanced_score = getattr(player, "base_projection", 0)

        return players

    def optimize_lineup(
        self, players: List[UnifiedPlayer], strategy: str = "balanced", manual_selections: str = ""
    ) -> Tuple[List[UnifiedPlayer], float]:
        """
        Main optimization method
        1. Apply strategy filter to create player pool
        2. Calculate scores using real data
        3. Pre-calculate correlation bonuses (NEW)
        4. Run MILP optimization
        """
        # Step 1: Create player pool based on strategy
        strategy_filter = StrategyFilter()
        player_pool = strategy_filter.apply_strategy_filter(players, strategy, manual_selections)

        self.logger.info(f"Strategy '{strategy}' created pool of {len(player_pool)} players")

        # Step 2: Calculate enhanced scores using real data
        player_pool = self.calculate_player_scores(player_pool)

        # Step 3: Pre-calculate correlation bonuses (NEW)
        player_pool = self.prepare_players_for_optimization(player_pool)

        # Step 4: Run MILP optimization
        try:
            return self._optimize_milp(player_pool)
        except Exception as e:
            self.logger.error(f"MILP optimization failed: {e}")
            return [], 0

    def optimize(self, players, strategy="balanced", manual_selections=None):
        """
        REAL STRATEGY IMPLEMENTATION - Each strategy produces different lineups
        """
        try:
            from dataclasses import dataclass
            import random

            @dataclass
            class OptimizationResult:
                lineup: list
                total_salary: int
                projected_points: float
                strategy: str
                meta: dict = None

            self.logger.info(f"🎯 Optimizing with strategy: {strategy.upper()}")

            # Parse manual selections
            manual_players = self.parse_manual_selections(manual_selections or "", players)
            manual_names = [p.get('name', p.name if hasattr(p, 'name') else '') for p in manual_players]

            # Convert players to consistent format
            player_dicts = []
            for player in players:
                if hasattr(player, 'name'):  # UnifiedPlayer object
                    player_dict = {
                        'name': player.name,
                        'position': player.primary_position,
                        'team': player.team,
                        'salary': player.salary,
                        'projected_points': getattr(player, 'enhanced_score', player.base_projection),
                        'ownership': getattr(player, 'ownership_projection', 10.0),  # Default 10%
                        'ceiling': getattr(player, 'ceiling_score', player.base_projection * 1.3),
                        'floor': getattr(player, 'enhanced_score', player.base_projection) * 0.7,
                        'is_confirmed': getattr(player, 'is_confirmed', False),
                        'recent_form': getattr(player, 'recent_form', 1.0),
                        'vegas_total': getattr(player, 'implied_team_score', 4.5),
                        'original_player': player
                    }
                else:  # Dictionary
                    player_dict = {
                        'name': player.get('name', 'Unknown'),
                        'position': player.get('position', 'UTIL'),
                        'team': player.get('team', 'UNK'),
                        'salary': player.get('salary', 0),
                        'projected_points': player.get('projected_points', 0),
                        'ownership': player.get('ownership', 10.0),
                        'ceiling': player.get('projected_points', 0) * 1.3,
                        'floor': player.get('projected_points', 0) * 0.7,
                        'is_confirmed': player.get('is_confirmed', False),
                        'recent_form': 1.0,
                        'vegas_total': 4.5,
                        'original_player': player
                    }
                player_dicts.append(player_dict)

            # Apply strategy-specific transformations
            if strategy == "ceiling":
                return self._optimize_ceiling_strategy(player_dicts, manual_names)
            elif strategy == "safe":
                return self._optimize_safe_strategy(player_dicts, manual_names)
            elif strategy == "value":
                return self._optimize_value_strategy(player_dicts, manual_names)
            elif strategy == "contrarian":
                return self._optimize_contrarian_strategy(player_dicts, manual_names)
            else:  # balanced
                return self._optimize_balanced_strategy(player_dicts, manual_names)

        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            return None

    def _optimize_ceiling_strategy(self, players, manual_names):
        """CEILING: Maximize upside potential, accept higher variance"""
        self.logger.info("🚀 CEILING STRATEGY: Maximizing upside potential")

        # Transform scores for ceiling optimization
        for player in players:
            base_score = player['projected_points']
            ceiling_score = base_score

            # 1. Boost based on recent form
            if player['recent_form'] > 1.1:  # Hot players
                ceiling_score *= 1.25

            # 2. Boost high-ceiling positions
            if player['position'] in ['P', 'OF']:  # Volatile positions
                ceiling_score *= 1.15

            # 3. Boost players in high-scoring games
            if player['vegas_total'] > 5.0:
                ceiling_score *= 1.1

            # 4. Boost lower-owned players (GPP theory)
            if player['ownership'] < 8.0:
                ceiling_score *= 1.12

            # 5. Reduce safer, high-floor players
            floor_ratio = player['floor'] / max(base_score, 0.1)
            if floor_ratio > 0.85:  # Very safe players
                ceiling_score *= 0.95

            player['opt_score'] = ceiling_score

        return self._build_optimal_lineup(players, manual_names, "ceiling")

    def _optimize_safe_strategy(self, players, manual_names):
        """SAFE: Minimize variance, prioritize high floor"""
        self.logger.info("🛡️ SAFE STRATEGY: Minimizing variance")

        for player in players:
            base_score = player['projected_points']
            safe_score = base_score

            # 1. Heavily weight floor performance
            floor_weight = player['floor'] / max(base_score, 0.1)
            safe_score *= (0.7 + 0.6 * floor_weight)  # 0.7-1.3x multiplier

            # 2. Boost confirmed players (known quantities)
            if player['is_confirmed']:
                safe_score *= 1.15

            # 3. Boost consistent positions
            if player['position'] in ['1B', 'C']:  # Lower variance positions
                safe_score *= 1.08

            # 4. Penalize highly volatile players
            if player['ownership'] < 5.0:  # Contrarian = risky
                safe_score *= 0.92

            # 5. Prefer moderate pricing (avoid min/max salary players)
            if 3000 <= player['salary'] <= 8000:
                safe_score *= 1.05

            player['opt_score'] = safe_score

        return self._build_optimal_lineup(players, manual_names, "safe")

    def _optimize_value_strategy(self, players, manual_names):
        """VALUE: Maximize points per dollar"""
        self.logger.info("💰 VALUE STRATEGY: Maximizing points per dollar")

        for player in players:
            base_score = player['projected_points']

            # Calculate value score (points per $1000)
            if player['salary'] > 0:
                value_ratio = base_score / (player['salary'] / 1000)
            else:
                value_ratio = 0

            # Transform to create value-focused optimization
            value_score = value_ratio * 10  # Scale up for optimization

            # 1. Extra boost for extreme value plays
            if value_ratio > 3.5:  # Exceptional value
                value_score *= 1.3
            elif value_ratio > 3.0:  # Good value
                value_score *= 1.15

            # 2. Slight penalty for expensive players (forces value hunting)
            if player['salary'] > 8000:
                value_score *= 0.95

            # 3. Boost mid-tier players (often best value)
            if 4000 <= player['salary'] <= 6500:
                value_score *= 1.1

            player['opt_score'] = value_score

        return self._build_optimal_lineup(players, manual_names, "value")

    def _optimize_contrarian_strategy(self, players, manual_names):
        """CONTRARIAN: Target low-ownership players for GPPs"""
        self.logger.info("🎭 CONTRARIAN STRATEGY: Targeting low-ownership plays")

        for player in players:
            base_score = player['projected_points']
            contrarian_score = base_score

            # 1. Heavily boost low-ownership players
            ownership = player['ownership']
            if ownership < 3.0:  # Very low owned
                contrarian_score *= 1.4
            elif ownership < 6.0:  # Low owned
                contrarian_score *= 1.25
            elif ownership < 10.0:  # Medium-low owned
                contrarian_score *= 1.1
            elif ownership > 20.0:  # Highly owned
                contrarian_score *= 0.8  # Penalize chalk

            # 2. Boost players with upside despite low ownership
            ceiling_ratio = player['ceiling'] / max(base_score, 0.1)
            if ceiling_ratio > 1.4 and ownership < 8.0:
                contrarian_score *= 1.2

            # 3. Target players from lower-total games (overlooked)
            if player['vegas_total'] < 4.3:
                contrarian_score *= 1.15

            # 4. Avoid confirmed players (too obvious)
            if player['is_confirmed'] and ownership > 15.0:
                contrarian_score *= 0.85

            player['opt_score'] = contrarian_score

        return self._build_optimal_lineup(players, manual_names, "contrarian")

    def _optimize_balanced_strategy(self, players, manual_names):
        """BALANCED: Optimal mix of safety, upside, and value"""
        self.logger.info("⚖️ BALANCED STRATEGY: Optimizing all factors")

        for player in players:
            base_score = player['projected_points']

            # Multi-factor balanced scoring
            balanced_score = base_score

            # 1. Value component (30% weight)
            if player['salary'] > 0:
                value_ratio = base_score / (player['salary'] / 1000)
                value_factor = min(1.2, 0.9 + (value_ratio - 2.5) * 0.1)  # 0.9-1.2x
                balanced_score *= (0.7 + 0.3 * value_factor)

            # 2. Safety component (25% weight)
            floor_ratio = player['floor'] / max(base_score, 0.1)
            safety_factor = 0.9 + 0.2 * floor_ratio  # 0.9-1.1x
            balanced_score *= (0.75 + 0.25 * safety_factor)

            # 3. Upside component (25% weight)
            ceiling_ratio = player['ceiling'] / max(base_score, 0.1)
            upside_factor = min(1.15, 0.95 + (ceiling_ratio - 1.2) * 0.2)
            balanced_score *= (0.75 + 0.25 * upside_factor)

            # 4. Confirmation bonus (20% weight)
            if player['is_confirmed']:
                balanced_score *= 1.05

            player['opt_score'] = balanced_score

        return self._build_optimal_lineup(players, manual_names, "balanced")

    def _build_optimal_lineup(self, players, manual_names, strategy):
        """Build lineup using strategy-optimized scores"""

        # Position requirements
        position_needs = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        lineup = []
        used_salary = 0
        used_players = set()

        # 1. Force include manual selections
        for name in manual_names:
            for player in players:
                if player['name'].lower() == name.lower() and player['name'] not in used_players:
                    pos = player['position']
                    if position_needs.get(pos, 0) > 0:
                        lineup.append(player['original_player'])
                        used_salary += player['salary']
                        used_players.add(player['name'])
                        position_needs[pos] -= 1
                        self.logger.info(f"👤 Manual: {player['name']} ({pos})")
                    break

        # 2. Fill remaining positions with optimized players
        for pos, count in position_needs.items():
            if count <= 0:
                continue

            # Get available players for this position
            pos_players = [
                p for p in players
                if p['position'] == pos
                   and p['name'] not in used_players
                   and p['salary'] > 0
                   and p['projected_points'] > 0
            ]

            # Sort by strategy-optimized score
            pos_players.sort(key=lambda x: x['opt_score'], reverse=True)

            # Select best players that fit salary
            for player in pos_players:
                if count <= 0:
                    break

                if used_salary + player['salary'] <= self.config.salary_cap:
                    lineup.append(player['original_player'])
                    used_salary += player['salary']
                    used_players.add(player['name'])
                    count -= 1

                    self.logger.info(
                        f"⚡ {strategy.upper()}: {player['name']} ({pos}) - Score: {player['opt_score']:.1f}")

        # Calculate final metrics
        total_points = sum(p.get('projected_points', 0) if hasattr(p, 'get') else
                           getattr(p, 'enhanced_score', getattr(p, 'base_projection', 0))
                           for p in lineup)

        # Create meta information
        meta = {
            'strategy': strategy,
            'manual_count': len(manual_names),
            'confirmed_count': sum(1 for p in lineup if getattr(p, 'is_confirmed', False)),
            'avg_ownership': sum(getattr(p, 'ownership_projection', 10.0) for p in lineup) / max(len(lineup), 1),
            'optimization_method': 'unified_strategies'
        }

        from dataclasses import dataclass

        @dataclass
        class OptimizationResult:
            lineup: list
            total_salary: int
            projected_points: float
            strategy: str
            meta: dict = None

        return OptimizationResult(
            lineup=lineup,
            total_salary=used_salary,
            projected_points=total_points,
            strategy=strategy,
            meta=meta
        )

    def parse_manual_selections(self, manual_input, all_players):
        """Parse manual selections from input string"""
        if not manual_input or not manual_input.strip():
            return []

        selections = []
        names = [name.strip() for name in manual_input.split(",") if name.strip()]

        for name in names:
            for player in all_players:
                player_name = player.get('name', player.name if hasattr(player, 'name') else '')
                if name.lower() in player_name.lower():
                    selections.append(player)
                    break

        return selections


class StrategyFilter:
    """
    Creates player pools based on strategy WITHOUT modifying scores
    """

    def __init__(self):
        self.logger = logger

    def apply_strategy_filter(
        self, players: List[UnifiedPlayer], strategy: str, manual_input: str = ""
    ) -> List[UnifiedPlayer]:
        """
        Creates player pools WITHOUT modifying scores
        """

        # Parse manual selections
        manual_players = self._parse_manual_selections(players, manual_input)

        # Get confirmed players
        confirmed_players = [p for p in players if p.is_confirmed]

        # Build pool based on strategy
        if strategy == "confirmed_plus_manual":
            base_pool = list(set(confirmed_players + manual_players))

            if len(base_pool) < 40:
                remaining = [p for p in players if p not in base_pool]
                remaining.sort(key=lambda x: (x.enhanced_score if x.enhanced_score is not None else 0), reverse=True)
                base_pool.extend(remaining[: 40 - len(base_pool)])

            return base_pool

        elif strategy == "manual_only":
            return manual_players

        elif strategy == "top_value":
            players_with_value = [
                (p, p.enhanced_score / (p.salary / 1000)) for p in players if p.salary > 0
            ]
            players_with_value.sort(key=lambda x: x[1], reverse=True)
            cutoff = max(20, len(players) // 2)
            return [p for p, _ in players_with_value[:cutoff]]

        elif strategy == "high_ceiling":
            ceiling_players = []

            for player in players:
                # Must have real performance data
                pass

                # Check recent form
                if hasattr(player, "_recent_performance") and player._recent_performance:
                    form = player._recent_performance.get("form_score", 1.0)
                    if form > 1.15:  # Hot streak
                        player.enhanced_score * 1.2
                        ceiling_players.append(player)
                        continue

                # Check high upside stats
                if hasattr(player, "statcast_data") and player.statcast_data:
                    data = player.statcast_data
                    if data.get("barrel_rate", 0) > 10 or data.get("hard_hit_rate", 0) > 45:
                        player.enhanced_score * 1.15
                        ceiling_players.append(player)

            # Sort by ceiling potential
            ceiling_players.sort(key=lambda x: (x.enhanced_score if x.enhanced_score is not None else 0), reverse=True)
            return ceiling_players[: max(30, len(players) // 3)]

        elif strategy == "balanced":
            # Mix of confirmed, high-value, and top-projected
            pool = set(confirmed_players + manual_players)

            # Add some high-value plays
            values = [
                (p, p.enhanced_score / (p.salary / 1000))
                for p in players
                if p.salary > 0 and p not in pool
            ]
            values.sort(key=lambda x: x[1], reverse=True)
            pool.update([p for p, _ in values[:10]])

            # Add top projections
            remaining = [p for p in players if p not in pool]
            remaining.sort(key=lambda x: (x.enhanced_score if x.enhanced_score is not None else 0), reverse=True)
            pool.update(remaining[:20])

            return list(pool)

        else:  # 'all_players' or unknown
            return players

    def _parse_manual_selections(
        self, all_players: List[UnifiedPlayer], manual_input: str
    ) -> List[UnifiedPlayer]:
        """Parse manual player selections from input string"""
        if not manual_input or not manual_input.strip():
            return []

        selected = []
        names = [name.strip() for name in manual_input.split(",") if name.strip()]

        for name in names:
            # Find best match
            best_match = None
            best_score = 0

            for player in all_players:
                # Calculate similarity
                score = self._name_similarity(name.lower(), player.name.lower())
                if score > best_score and score > 0.7:  # 70% threshold
                    best_score = score
                    best_match = player

            if best_match:
                # Mark as manually selected
                best_match.is_manual_selected = True
                selected.append(best_match)
                self.logger.info(f"Manual selection: {best_match.name} matched for '{name}'")
            else:
                self.logger.warning(f"No match found for manual selection: '{name}'")

        return selected

    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity score"""
        # Direct match
        if name1 == name2:
            return 1.0

        # Partial match
        if name1 in name2 or name2 in name1:
            return 0.9

        # Last name match
        parts1 = name1.split()
        parts2 = name2.split()
        if parts1 and parts2 and parts1[-1] == parts2[-1]:
            return 0.8

        # Character-based similarity
        from difflib import SequenceMatcher

        return SequenceMatcher(None, name1, name2).ratio()


# Convenience function for backwards compatibility
def create_unified_optimizer(config: OptimizationConfig = None) -> UnifiedMILPOptimizer:
    """Create a unified MILP optimizer instance"""
    return UnifiedMILPOptimizer(config)


if __name__ == "__main__":
    # Test basic functionality
    print("Unified MILP Optimizer module loaded successfully")
    optimizer = UnifiedMILPOptimizer()
    print(f"Salary cap: ${optimizer.config.salary_cap}")
    print(f"Position requirements: {optimizer.config.position_requirements}")
