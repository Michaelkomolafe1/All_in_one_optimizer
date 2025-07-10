#!/usr/bin/env python3
"""
Enhanced DFS Core with Vegas Lines and Team Stacking
✅ Integrates your vegas_lines.py system
✅ Adds configurable team stacking for cash games
✅ Enhanced Statcast data usage
✅ All original optimization features preserved
"""

import os
import sys
import pulp
import pandas as pd
import numpy as np
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')

# Import your vegas lines system
try:
    from vegas_lines import VegasLines

    VEGAS_AVAILABLE = True
    print("✅ Vegas Lines integration available")
except ImportError:
    VEGAS_AVAILABLE = False
    print("⚠️ Vegas Lines not available - install requests: pip install requests")

# Import the base system
try:
    from optimized_dfs_core_with_statcast import (
        OptimizedPlayer,
        EnhancedDFFMatcher,
        EnhancedDFFProcessor,
        ManualPlayerSelector,
        StatcastDataService
    )

    BASE_CORE_AVAILABLE = True
    print("✅ Base DFS core imported successfully")
except ImportError:
    BASE_CORE_AVAILABLE = False
    print("❌ Base DFS core not available")

# MILP availability
try:
    import pulp

    MILP_AVAILABLE = True
    print("✅ PuLP available - MILP optimization enabled")
except ImportError:
    MILP_AVAILABLE = False
    print("⚠️ PuLP not available - using greedy fallback")


class StackingConfig:
    """Configuration for team stacking strategies"""

    def __init__(self):
        # Cash game stacking settings (conservative)
        self.enable_stacking = True
        self.min_stack_size = 2  # Minimum players from same team
        self.max_stack_size = 4  # Maximum for cash games (conservative)
        self.preferred_stack_size = 3  # Sweet spot for cash

        # Stack composition rules
        self.allow_pitcher_stacking = False  # Generally avoid in cash
        self.require_top_order_in_stack = True  # 1-6 batting order
        self.max_bottom_order = 1  # Max players from 7-9 batting order

        # Team selection criteria
        self.min_implied_total = 4.5  # Only stack teams with good offenses
        self.preferred_implied_total = 5.0  # Prefer high-scoring teams

        # Advanced stack types
        self.enable_mini_stacks = True  # 2-player mini stacks
        self.enable_game_stacks = False  # Both teams from same game (risky)

    def to_dict(self):
        return {
            'enable_stacking': self.enable_stacking,
            'min_stack_size': self.min_stack_size,
            'max_stack_size': self.max_stack_size,
            'preferred_stack_size': self.preferred_stack_size,
            'min_implied_total': self.min_implied_total
        }


class EnhancedVegasIntegration:
    """Enhanced Vegas lines integration with your existing system"""

    def __init__(self, verbose=False):
        self.vegas_lines = VegasLines(verbose=verbose) if VEGAS_AVAILABLE else None
        self.lines_data = {}
        self.verbose = verbose

    def fetch_and_cache_lines(self, force_refresh=False):
        """Fetch Vegas lines and cache them"""
        if not self.vegas_lines:
            print("⚠️ Vegas lines not available")
            return {}

        self.lines_data = self.vegas_lines.get_vegas_lines(force_refresh=force_refresh)
        return self.lines_data

    def enrich_players_with_vegas(self, players: List[OptimizedPlayer]) -> List[OptimizedPlayer]:
        """Enrich players with Vegas lines data"""
        if not self.lines_data:
            self.fetch_and_cache_lines()

        if not self.lines_data:
            print("⚠️ No Vegas data available")
            return players

        enriched_count = 0

        for player in players:
            team_code = player.team
            if team_code in self.lines_data:
                vegas_data = self.lines_data[team_code]

                # Apply Vegas data using your player's apply_vegas_data method
                if hasattr(player, 'apply_vegas_data'):
                    player.apply_vegas_data(vegas_data)
                else:
                    # Fallback: manually set Vegas attributes
                    player.implied_team_score = vegas_data.get('team_total', 4.5)
                    player.over_under = vegas_data.get('total', 8.5)

                # Recalculate enhanced score with Vegas boost
                player._calculate_enhanced_score()
                enriched_count += 1

        print(f"✅ Applied Vegas data to {enriched_count} players")
        return players

    def get_team_implied_totals(self) -> Dict[str, float]:
        """Get implied totals for all teams"""
        if not self.lines_data:
            return {}

        return {team: data.get('team_total', 4.5)
                for team, data in self.lines_data.items()}


class TeamStackAnalyzer:
    """Analyze and optimize team stacking opportunities"""

    def __init__(self, config: StackingConfig):
        self.config = config

    def analyze_stacking_opportunities(self, players: List[OptimizedPlayer],
                                       vegas_integration: EnhancedVegasIntegration) -> Dict[str, Any]:
        """Analyze which teams offer the best stacking opportunities"""

        team_analysis = {}
        implied_totals = vegas_integration.get_team_implied_totals()

        # Group players by team
        teams = {}
        for player in players:
            team = player.team
            if team not in teams:
                teams[team] = []
            teams[team].append(player)

        for team, team_players in teams.items():
            # Skip teams with insufficient players
            if len(team_players) < self.config.min_stack_size:
                continue

            # Get team context
            implied_total = implied_totals.get(team, 4.5)

            # Skip low-scoring teams
            if implied_total < self.config.min_implied_total:
                continue

            # Analyze batting order composition
            top_order_players = [p for p in team_players
                                 if hasattr(p, 'batting_order') and
                                 p.batting_order and 1 <= p.batting_order <= 6]

            confirmed_players = [p for p in team_players if p.is_confirmed]

            # Calculate stack quality metrics
            avg_score = np.mean([p.enhanced_score for p in team_players])
            total_salary = sum(p.salary for p in team_players)

            # Stack recommendations
            stack_options = self._generate_stack_combinations(team_players)

            team_analysis[team] = {
                'team': team,
                'implied_total': implied_total,
                'player_count': len(team_players),
                'top_order_count': len(top_order_players),
                'confirmed_count': len(confirmed_players),
                'avg_score': avg_score,
                'total_salary': total_salary,
                'stack_options': stack_options,
                'recommendation': self._rate_team_for_stacking(team, team_players, implied_total)
            }

        return team_analysis

    def _generate_stack_combinations(self, team_players: List[OptimizedPlayer]) -> List[Dict]:
        """Generate potential stack combinations for a team"""
        options = []

        # Sort players by batting order and enhanced score
        sorted_players = sorted(team_players,
                                key=lambda x: (x.batting_order or 9, -x.enhanced_score))

        # Generate stacks of different sizes
        for stack_size in range(self.config.min_stack_size,
                                min(self.config.max_stack_size + 1, len(sorted_players) + 1)):
            # Take top players for this stack size
            stack_players = sorted_players[:stack_size]

            option = {
                'size': stack_size,
                'players': [p.name for p in stack_players],
                'total_salary': sum(p.salary for p in stack_players),
                'total_score': sum(p.enhanced_score for p in stack_players),
                'avg_batting_order': np.mean([p.batting_order or 9 for p in stack_players]),
                'has_leadoff': any(p.batting_order == 1 for p in stack_players if p.batting_order)
            }

            options.append(option)

        return options

    def _rate_team_for_stacking(self, team: str, players: List[OptimizedPlayer],
                                implied_total: float) -> str:
        """Rate a team's stacking potential"""

        score = 0

        # Vegas context (40% of rating)
        if implied_total >= 5.5:
            score += 40
        elif implied_total >= 5.0:
            score += 30
        elif implied_total >= 4.5:
            score += 20
        else:
            score += 10

        # Player quality (30% of rating)
        avg_score = np.mean([p.enhanced_score for p in players])
        if avg_score >= 8.0:
            score += 30
        elif avg_score >= 7.0:
            score += 20
        elif avg_score >= 6.0:
            score += 15
        else:
            score += 10

        # Confirmed players (20% of rating)
        confirmed_pct = sum(1 for p in players if p.is_confirmed) / len(players)
        score += confirmed_pct * 20

        # Batting order coverage (10% of rating)
        top_order_count = sum(1 for p in players
                              if hasattr(p, 'batting_order') and p.batting_order and
                              1 <= p.batting_order <= 6)
        if top_order_count >= 4:
            score += 10
        elif top_order_count >= 2:
            score += 5

        # Convert to rating
        if score >= 80:
            return "EXCELLENT"
        elif score >= 60:
            return "GOOD"
        elif score >= 40:
            return "FAIR"
        else:
            return "POOR"


class EnhancedStatcastAnalyzer:
    """Enhanced analysis of Statcast data for better DFS optimization"""

    @staticmethod
    def get_key_metrics_for_position(position: str) -> List[str]:
        """Get the most important Statcast metrics for each position"""
        if position == 'P':
            return ['xwOBA', 'Hard_Hit', 'K', 'Whiff', 'Barrel_Against']
        else:
            return ['xwOBA', 'Hard_Hit', 'Barrel', 'avg_exit_velocity', 'K', 'BB']

    @staticmethod
    def calculate_statcast_percentile_boost(player: OptimizedPlayer) -> float:
        """Calculate boost based on Statcast percentiles rather than raw values"""
        if not player.statcast_data:
            return 0.0

        boost = 0.0
        position = player.primary_position

        if position == 'P':
            # For pitchers, lower is better for most metrics
            xwoba = player.statcast_data.get('xwOBA', 0.320)
            hard_hit = player.statcast_data.get('Hard_Hit', 35.0)
            k_rate = player.statcast_data.get('K', 20.0)

            # xwOBA against (lower is better for pitchers)
            if xwoba <= 0.270:  # Elite (90th percentile)
                boost += 3.0
            elif xwoba <= 0.290:  # Very good (75th percentile)
                boost += 2.0
            elif xwoba <= 0.310:  # Above average (50th percentile)
                boost += 1.0
            elif xwoba >= 0.350:  # Poor (25th percentile)
                boost -= 2.0

            # Hard hit rate against (lower is better for pitchers)
            if hard_hit <= 28.0:  # Elite
                boost += 2.5
            elif hard_hit <= 32.0:  # Very good
                boost += 1.5
            elif hard_hit >= 42.0:  # Poor
                boost -= 2.0

            # Strikeout rate (higher is better for pitchers)
            if k_rate >= 28.0:  # Elite
                boost += 2.5
            elif k_rate >= 24.0:  # Above average
                boost += 1.5
            elif k_rate <= 18.0:  # Poor
                boost -= 1.5

        else:
            # For hitters, higher is generally better
            xwoba = player.statcast_data.get('xwOBA', 0.320)
            hard_hit = player.statcast_data.get('Hard_Hit', 35.0)
            barrel = player.statcast_data.get('Barrel', 6.0)

            # xwOBA (higher is better for hitters)
            if xwoba >= 0.400:  # Elite (90th percentile)
                boost += 3.0
            elif xwoba >= 0.370:  # Very good (75th percentile)
                boost += 2.0
            elif xwoba >= 0.340:  # Above average (50th percentile)
                boost += 1.0
            elif xwoba <= 0.290:  # Poor (25th percentile)
                boost -= 2.0

            # Hard hit rate (higher is better for hitters)
            if hard_hit >= 50.0:  # Elite
                boost += 2.5
            elif hard_hit >= 42.0:  # Very good
                boost += 1.5
            elif hard_hit <= 28.0:  # Poor
                boost -= 2.0

            # Barrel rate (higher is better for hitters)
            if barrel >= 15.0:  # Elite
                boost += 2.0
            elif barrel >= 10.0:  # Very good
                boost += 1.5
            elif barrel <= 3.0:  # Poor
                boost -= 1.0

        return boost

    @staticmethod
    def get_statcast_summary(player: OptimizedPlayer) -> str:
        """Get a human-readable summary of player's Statcast profile"""
        if not player.statcast_data:
            return "No Statcast data"

        metrics = []
        position = player.primary_position

        if position == 'P':
            xwoba = player.statcast_data.get('xwOBA', 0.320)
            k_rate = player.statcast_data.get('K', 20.0)

            if xwoba <= 0.290:
                metrics.append("Elite Contact Suppression")
            if k_rate >= 26.0:
                metrics.append("High Strikeout Rate")

        else:
            xwoba = player.statcast_data.get('xwOBA', 0.320)
            hard_hit = player.statcast_data.get('Hard_Hit', 35.0)
            barrel = player.statcast_data.get('Barrel', 6.0)

            if xwoba >= 0.370:
                metrics.append("Elite Contact Quality")
            if hard_hit >= 45.0:
                metrics.append("Elite Hard Contact")
            if barrel >= 12.0:
                metrics.append("Elite Barrel Rate")

        return " | ".join(metrics) if metrics else "Average Metrics"


class EnhancedDFSCore:
    """Enhanced DFS Core with Vegas lines and team stacking"""

    def __init__(self, stacking_config: StackingConfig = None, enable_vegas=True):
        # Initialize base components
        if not BASE_CORE_AVAILABLE:
            raise ImportError("Base DFS core not available")

        self.players = []
        self.dff_processor = EnhancedDFFProcessor()
        self.statcast_service = StatcastDataService()
        self.manual_selector = ManualPlayerSelector()

        # Enhanced components
        self.stacking_config = stacking_config or StackingConfig()
        self.vegas_integration = EnhancedVegasIntegration() if enable_vegas else None
        self.stack_analyzer = TeamStackAnalyzer(self.stacking_config)

        # Contest settings
        self.contest_type = 'classic'
        self.salary_cap = 50000

        print("🚀 Enhanced DFS Core initialized")
        print(f"✅ Team stacking: {'enabled' if self.stacking_config.enable_stacking else 'disabled'}")
        print(f"✅ Vegas integration: {'enabled' if self.vegas_integration else 'disabled'}")

    def load_and_enrich_complete(self, dk_file: str, dff_file: str = None,
                                 manual_input: str = "") -> bool:
        """Complete data loading and enrichment pipeline"""

        print("🚀 ENHANCED DFS PIPELINE - Vegas + Stacking + Statcast")
        print("=" * 60)

        # Step 1: Load DraftKings CSV
        print("📊 Step 1: Loading DraftKings data...")
        if not self._load_draftkings_csv(dk_file):
            return False

        # Step 2: Apply DFF rankings
        if dff_file and os.path.exists(dff_file):
            print("🎯 Step 2: Applying DFF rankings...")
            self.dff_processor.load_dff_cheat_sheet(dff_file)
            self.dff_processor.apply_dff_data_to_players(self.players)

        # Step 3: Enrich with Vegas lines
        if self.vegas_integration:
            print("💰 Step 3: Enriching with Vegas lines...")
            self.players = self.vegas_integration.enrich_players_with_vegas(self.players)

        # Step 4: Enrich with Statcast
        print("🔬 Step 4: Enriching with enhanced Statcast analysis...")
        self.players = self.statcast_service.enrich_players_with_statcast(self.players)

        # Step 5: Apply enhanced Statcast analysis
        for player in self.players:
            additional_boost = EnhancedStatcastAnalyzer.calculate_statcast_percentile_boost(player)
            player.enhanced_score += additional_boost

        # Step 6: Apply manual selections
        if manual_input:
            print("🎯 Step 6: Applying manual selections...")
            self.manual_selector.apply_manual_selection(self.players, manual_input)

        # Step 7: Analyze stacking opportunities
        if self.stacking_config.enable_stacking:
            print("📊 Step 7: Analyzing team stacking opportunities...")
            stack_analysis = self.stack_analyzer.analyze_stacking_opportunities(
                self.players, self.vegas_integration or EnhancedVegasIntegration()
            )
            self._print_stacking_analysis(stack_analysis)

        print(f"✅ Enhanced pipeline complete: {len(self.players)} players ready")
        return True

    def optimize_lineup_with_stacking(self, contest_type: str = 'classic',
                                      strategy: str = 'smart_confirmed') -> Tuple[List[OptimizedPlayer], float]:
        """Optimize lineup with optional team stacking"""

        print(f"🧠 Optimizing {contest_type} lineup with enhanced features")
        print(f"📊 Strategy: {strategy}")
        print(f"🏆 Stacking: {'enabled' if self.stacking_config.enable_stacking else 'disabled'}")

        # Apply strategy filter
        filtered_players = self._apply_strategy_filter(strategy)

        if MILP_AVAILABLE:
            print("🔬 Using enhanced MILP optimization")
            return self._optimize_milp_with_stacking(filtered_players)
        else:
            print("🔧 Using enhanced greedy optimization")
            return self._optimize_greedy_with_stacking(filtered_players)

    def _optimize_milp_with_stacking(self, players: List[OptimizedPlayer]) -> Tuple[List[OptimizedPlayer], float]:
        """MILP optimization with team stacking constraints"""

        try:
            print(f"🔬 MILP with stacking: {len(players)} players")

            # Create problem
            prob = pulp.LpProblem("DFS_Lineup_Stacking", pulp.LpMaximize)

            # Variables
            player_vars = {}
            for i, player in enumerate(players):
                player_vars[i] = pulp.LpVariable(f"player_{i}", cat=pulp.LpBinary)

            # Objective
            objective = pulp.lpSum([
                player_vars[i] * players[i].enhanced_score
                for i in range(len(players))
            ])
            prob += objective

            # Standard constraints
            # Roster size
            prob += pulp.lpSum([player_vars[i] for i in range(len(players))]) == 10

            # Salary cap
            prob += pulp.lpSum([
                player_vars[i] * players[i].salary for i in range(len(players))
            ]) <= self.salary_cap

            # Position requirements
            position_requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

            for position, required_count in position_requirements.items():
                eligible_players = [
                    i for i, player in enumerate(players)
                    if player.can_play_position(position)
                ]
                if eligible_players:
                    prob += pulp.lpSum([
                        player_vars[i] for i in eligible_players
                    ]) == required_count

            # STACKING CONSTRAINTS
            if self.stacking_config.enable_stacking:
                print("🏆 Adding team stacking constraints...")

                # Group players by team
                teams = {}
                for i, player in enumerate(players):
                    team = player.team
                    if team not in teams:
                        teams[team] = []
                    teams[team].append(i)

                # Team stacking constraints
                for team, team_player_indices in teams.items():
                    team_vars = [player_vars[i] for i in team_player_indices]
                    team_sum = pulp.lpSum(team_vars)

                    # If any players from this team are selected, ensure minimum stack size
                    if len(team_player_indices) >= self.stacking_config.min_stack_size:
                        # This creates a constraint: if sum >= 1, then sum >= min_stack_size
                        # We implement this as: sum == 0 OR sum >= min_stack_size
                        # Using: sum <= M * y and sum >= min_stack_size * y where y is binary
                        y = pulp.LpVariable(f"team_{team}_selected", cat=pulp.LpBinary)

                        # If team is selected (y=1), must have at least min_stack_size players
                        prob += team_sum >= self.stacking_config.min_stack_size * y

                        # If any player from team is selected, y must be 1
                        prob += team_sum <= len(team_player_indices) * y

                        # Maximum stack size
                        prob += team_sum <= self.stacking_config.max_stack_size

            # Solve
            print("🔬 Solving enhanced MILP...")
            solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=300)
            prob.solve(solver)

            if prob.status == pulp.LpStatusOptimal:
                # Extract solution
                lineup = []
                total_salary = 0
                total_score = 0
                team_counts = {}

                for i, player in enumerate(players):
                    if player_vars[i].value() > 0.5:
                        lineup.append(player)
                        total_salary += player.salary
                        total_score += player.enhanced_score

                        team = player.team
                        team_counts[team] = team_counts.get(team, 0) + 1

                print(f"✅ Enhanced MILP success: {len(lineup)} players, {total_score:.2f} score")
                print(f"💰 Salary: ${total_salary:,}")

                # Show stacking results
                if self.stacking_config.enable_stacking:
                    stacks = {team: count for team, count in team_counts.items() if count >= 2}
                    if stacks:
                        print(f"🏆 Team stacks: {stacks}")
                    else:
                        print("🏆 No team stacks in optimal lineup")

                return lineup, total_score
            else:
                print(f"❌ MILP failed: {pulp.LpStatus[prob.status]}")
                return self._optimize_greedy_with_stacking(players)

        except Exception as e:
            print(f"❌ MILP error: {e}")
            return self._optimize_greedy_with_stacking(players)

    def _optimize_greedy_with_stacking(self, players: List[OptimizedPlayer]) -> Tuple[List[OptimizedPlayer], float]:
        """Greedy optimization with stacking preference"""

        print(f"🔧 Greedy with stacking preference: {len(players)} players")

        # If stacking is enabled, try to build around best stack opportunity
        if self.stacking_config.enable_stacking and self.vegas_integration:
            stack_analysis = self.stack_analyzer.analyze_stacking_opportunities(
                players, self.vegas_integration
            )

            # Find best stack opportunity
            best_stack_team = None
            best_stack_rating = 0

            for team, analysis in stack_analysis.items():
                if analysis['recommendation'] in ['EXCELLENT', 'GOOD']:
                    rating_score = {'EXCELLENT': 3, 'GOOD': 2, 'FAIR': 1}.get(analysis['recommendation'], 0)
                    if rating_score > best_stack_rating:
                        best_stack_rating = rating_score
                        best_stack_team = team

            if best_stack_team:
                print(f"🏆 Building around {best_stack_team} stack")
                return self._build_lineup_with_stack(players, best_stack_team)

        # Fallback to regular greedy optimization
        return self._optimize_greedy_standard(players)

    def _build_lineup_with_stack(self, players: List[OptimizedPlayer], stack_team: str) -> Tuple[
        List[OptimizedPlayer], float]:
        """Build lineup around a specific team stack"""

        # Separate stack team players from others
        stack_players = [p for p in players if p.team == stack_team]
        other_players = [p for p in players if p.team != stack_team]

        # Sort stack players by value
        stack_players.sort(key=lambda x: x.enhanced_score / (x.salary / 1000.0), reverse=True)

        # Build position requirements
        position_requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        lineup = []
        total_salary = 0
        used_positions = {pos: 0 for pos in position_requirements.keys()}

        # First, add stack players (aim for 3-4 players)
        stack_count = 0
        target_stack_size = min(self.stacking_config.preferred_stack_size, len(stack_players))

        for player in stack_players:
            if stack_count >= target_stack_size:
                break

            # Find a position this player can fill
            for position in player.positions:
                if (position in used_positions and
                        used_positions[position] < position_requirements[position] and
                        total_salary + player.salary <= self.salary_cap):
                    lineup.append(player)
                    total_salary += player.salary
                    used_positions[position] += 1
                    stack_count += 1
                    print(f"🏆 Stack: {player.name} ({position}) - ${player.salary:,}")
                    break

        # Fill remaining positions with best available players
        all_remaining = other_players + [p for p in stack_players if p not in lineup]
        all_remaining.sort(key=lambda x: x.enhanced_score / (x.salary / 1000.0), reverse=True)

        for position, required in position_requirements.items():
            while used_positions[position] < required:
                best_player = None
                best_value = 0

                for player in all_remaining:
                    if (player not in lineup and
                            player.can_play_position(position) and
                            total_salary + player.salary <= self.salary_cap):

                        value = player.enhanced_score / (player.salary / 1000.0)
                        if value > best_value:
                            best_value = value
                            best_player = player

                if best_player:
                    lineup.append(best_player)
                    total_salary += best_player.salary
                    used_positions[position] += 1
                    print(f"🔧 Fill: {best_player.name} ({position}) - ${best_player.salary:,}")
                else:
                    print(f"❌ Couldn't fill {position}")
                    return [], 0

        if len(lineup) == 10:
            total_score = sum(p.enhanced_score for p in lineup)
            print(f"✅ Stack lineup complete: {stack_count} from {stack_team}")
            return lineup, total_score
        else:
            print(f"❌ Stack lineup failed: {len(lineup)} players")
            return [], 0

    def _optimize_greedy_standard(self, players: List[OptimizedPlayer]) -> Tuple[List[OptimizedPlayer], float]:
        """Standard greedy optimization without stacking"""

        # Implementation similar to your original greedy method
        position_requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        lineup = []
        total_salary = 0
        used_players = set()

        # Group players by position
        players_by_position = {}
        for pos in position_requirements.keys():
            players_by_position[pos] = [
                p for p in players if p.can_play_position(pos)
            ]
            players_by_position[pos].sort(
                key=lambda x: x.enhanced_score / (x.salary / 1000.0), reverse=True
            )

        # Fill positions
        for position, required_count in position_requirements.items():
            available_players = [
                p for p in players_by_position[position]
                if p not in used_players
            ]

            selected_count = 0
            for player in available_players:
                if (selected_count < required_count and
                        total_salary + player.salary <= self.salary_cap):
                    lineup.append(player)
                    used_players.add(player)
                    total_salary += player.salary
                    selected_count += 1

            if selected_count < required_count:
                print(f"❌ Couldn't fill {position}: {selected_count}/{required_count}")
                return [], 0

        if len(lineup) == 10:
            total_score = sum(p.enhanced_score for p in lineup)
            return lineup, total_score
        else:
            return [], 0

    def _load_draftkings_csv(self, file_path: str) -> bool:
        """Load DraftKings CSV (simplified version)"""
        try:
            df = pd.read_csv(file_path)

            players = []
            for idx, row in df.iterrows():
                player_data = {
                    'id': idx + 1,
                    'name': str(row.get('Name', '')).strip(),
                    'position': str(row.get('Position', '')).strip(),
                    'team': str(row.get('TeamAbbrev', row.get('Team', ''))).strip(),
                    'salary': row.get('Salary', 3000),
                    'projection': row.get('AvgPointsPerGame', 0)
                }

                player = OptimizedPlayer(player_data)
                if player.name and player.salary > 0:
                    players.append(player)

            self.players = players
            print(f"✅ Loaded {len(self.players)} players")
            return True

        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return False

    def _apply_strategy_filter(self, strategy: str) -> List[OptimizedPlayer]:
        """Apply strategy filtering (simplified)"""
        # Use your existing strategy filtering logic
        confirmed_players = [p for p in self.players if getattr(p, 'is_confirmed', False)]
        manual_players = [p for p in self.players if getattr(p, 'is_manual_selected', False)]

        if strategy == 'smart_confirmed':
            selected_players = list(confirmed_players)
            for manual in manual_players:
                if manual not in selected_players:
                    selected_players.append(manual)
            return selected_players
        else:
            return self.players

    def _print_stacking_analysis(self, stack_analysis: Dict[str, Any]):
        """Print team stacking analysis"""
        if not stack_analysis:
            print("📊 No stacking opportunities found")
            return

        print("\n📊 TEAM STACKING ANALYSIS:")
        print("=" * 50)

        # Sort teams by implied total
        sorted_teams = sorted(stack_analysis.items(),
                              key=lambda x: x[1]['implied_total'], reverse=True)

        for team, analysis in sorted_teams[:5]:  # Show top 5
            rating = analysis['recommendation']
            implied = analysis['implied_total']
            player_count = analysis['player_count']
            confirmed = analysis['confirmed_count']

            print(f"{team:4} | {rating:9} | {implied:4.1f} total | "
                  f"{player_count:2} players | {confirmed:2} confirmed")

        print("=" * 50)

    def get_enhanced_lineup_summary(self, lineup: List[OptimizedPlayer], score: float) -> str:
        """Generate enhanced lineup summary with Vegas and Statcast info"""
        if not lineup:
            return "❌ No valid lineup found"

        output = []
        output.append(f"💰 ENHANCED LINEUP (Score: {score:.2f})")
        output.append("=" * 60)

        total_salary = sum(p.salary for p in lineup)
        output.append(f"Total Salary: ${total_salary:,} / ${self.salary_cap:,}")
        output.append(f"Remaining: ${self.salary_cap - total_salary:,}")
        output.append("")

        # Enhanced features summary
        vegas_count = sum(1 for p in lineup if p.implied_team_score > 4.5)
        statcast_count = sum(1 for p in lineup if p.statcast_data)
        confirmed_count = sum(1 for p in lineup if p.is_confirmed)

        output.append("🚀 ENHANCED FEATURES:")
        output.append(f"💰 Vegas integration: {vegas_count} players with data")
        output.append(f"🔬 Statcast analysis: {statcast_count} players with data")
        output.append(f"✅ Confirmed starters: {confirmed_count} players")

        # Team stacking analysis
        team_counts = {}
        for player in lineup:
            team = player.team
            team_counts[team] = team_counts.get(team, 0) + 1

        stacks = {team: count for team, count in team_counts.items() if count >= 2}
        if stacks:
            output.append(f"🏆 Team stacks: {stacks}")
        else:
            output.append("🏆 No team stacks (diversified approach)")

        output.append("")

        # Player details
        output.append(f"{'POS':<4} {'PLAYER':<20} {'TEAM':<4} {'SALARY':<8} {'SCORE':<6} {'VEGAS':<5} {'STATCAST'}")
        output.append("-" * 80)

        sorted_lineup = sorted(lineup, key=lambda x: x.primary_position)

        for player in sorted_lineup:
            vegas_info = f"{player.implied_team_score:.1f}" if player.implied_team_score > 0 else "-"
            statcast_info = EnhancedStatcastAnalyzer.get_statcast_summary(player)[:15]

            output.append(f"{player.primary_position:<4} {player.name[:19]:<20} {player.team:<4} "
                          f"${player.salary:<7,} {player.enhanced_score:<6.1f} {vegas_info:<5} {statcast_info}")

        # DraftKings import
        output.append("")
        output.append("📋 DRAFTKINGS IMPORT:")
        player_names = [player.name for player in sorted_lineup]
        output.append(", ".join(player_names))

        return "\n".join(output)


# Integration functions for your existing system
def create_enhanced_test_data() -> Tuple[str, str]:
    """Create test data (reuse your existing function)"""
    # Use your existing create_enhanced_test_data function
    from optimized_dfs_core_with_statcast import create_enhanced_test_data as base_create_test_data
    return base_create_test_data()


def load_and_optimize_with_enhanced_features(
        dk_file: str,
        dff_file: str = None,
        manual_input: str = "",
        contest_type: str = 'classic',
        strategy: str = 'smart_confirmed',
        enable_stacking: bool = True,
        enable_vegas: bool = True,
        stack_config: StackingConfig = None
) -> Tuple[List[OptimizedPlayer], float, str]:
    """Complete pipeline with enhanced features"""

    print("🚀 ENHANCED DFS OPTIMIZATION PIPELINE")
    print("=" * 60)

    # Configure stacking
    if stack_config is None:
        stack_config = StackingConfig()
        stack_config.enable_stacking = enable_stacking

    # Initialize enhanced core
    core = EnhancedDFSCore(stacking_config=stack_config, enable_vegas=enable_vegas)

    # Load and enrich data
    if not core.load_and_enrich_complete(dk_file, dff_file, manual_input):
        return [], 0, "Failed to load and enrich data"

    # Optimize lineup
    lineup, score = core.optimize_lineup_with_stacking(contest_type, strategy)

    if lineup:
        summary = core.get_enhanced_lineup_summary(lineup, score)
        return lineup, score, summary
    else:
        return [], 0, "Optimization failed"


# For backwards compatibility with your existing system
def load_and_optimize_complete_pipeline(*args, **kwargs):
    """Backwards compatibility wrapper"""
    return load_and_optimize_with_enhanced_features(*args, **kwargs)


if __name__ == "__main__":
    # Test the enhanced system
    print("🧪 Testing Enhanced DFS System")

    try:
        dk_file, dff_file = create_enhanced_test_data()

        # Test with stacking enabled
        lineup, score, summary = load_and_optimize_with_enhanced_features(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input="Kyle Tucker, Jorge Polanco",
            contest_type='classic',
            strategy='smart_confirmed',
            enable_stacking=True,
            enable_vegas=True
        )

        if lineup and score > 0:
            print("✅ Enhanced system test PASSED!")
            print(f"📊 Generated lineup: {len(lineup)} players, {score:.2f} score")
            print("\n" + summary)
        else:
            print("❌ Enhanced system test FAILED!")

    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback

        traceback.print_exc()