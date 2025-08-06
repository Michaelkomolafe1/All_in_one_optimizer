#!/usr/bin/env python3
"""
COMPREHENSIVE SIMULATION RUNNER - CORRECTLY FIXED IMPORTS
==========================================================
Fixed with your exact file structure
Save as: simulation/comprehensive_simulation_runner.py
"""

import sys
import os
import time
import json
import numpy as np
import pandas as pd
import random
from datetime import datetime
import multiprocessing as mp
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Add the correct paths based on your structure
# Assuming this file is in All_in_one_optimizer/simulation/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
main_optimizer_path = os.path.join(project_root, 'main_optimizer')
sys.path.insert(0, project_root)
sys.path.insert(0, main_optimizer_path)

print(f"Project root: {project_root}")
print(f"Main optimizer path: {main_optimizer_path}")
print(f"Python path: {sys.path[:2]}")

# Import YOUR system - using the EXACT file names from your structure
try:
    # Your file is named unified_core_system_updated.py
    from main_optimizer.unified_core_system_updated import UnifiedCoreSystem

    print("✓ Imported UnifiedCoreSystem")
except ImportError as e:
    print(f"❌ Could not import UnifiedCoreSystem: {e}")


    # Fallback
    class UnifiedCoreSystem:
        def __init__(self):
            self.players = []
            self.csv_loaded = False

        def generate_lineups(self, num_lineups=1, strategy='auto', contest_type='gpp'):
            return []

try:
    from main_optimizer.unified_player_model import UnifiedPlayer

    print("✓ Imported UnifiedPlayer")
except ImportError as e:
    print(f"❌ Could not import UnifiedPlayer: {e}")


    class UnifiedPlayer:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
            self.optimization_score = 0
            self.is_pitcher = self.primary_position == 'P' if hasattr(self, 'primary_position') else False

try:
    from main_optimizer.strategy_selector import StrategyAutoSelector

    print("✓ Imported StrategyAutoSelector")
except ImportError as e:
    print(f"❌ Could not import StrategyAutoSelector: {e}")


    class StrategyAutoSelector:
        def __init__(self):
            self.top_strategies = {
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

# Import from fixed_simulation_core (should be in same directory as this file)
try:
    # Try absolute import first
    from simulation.fixed_simulation_core import (
        generate_realistic_slate,
        build_opponent_lineup,
        simulate_contest,
        REALISTIC_PARAMS,
        OPTIMAL_STRATEGY_MAP,
        STRATEGY_PARAMS,
        get_slate_size,
        SimulatedPlayer
    )

    print("✓ Imported from fixed_simulation_core (absolute)")
except ImportError:
    try:
        # Try relative import if in same directory
        from fixed_simulation_core import (
            generate_realistic_slate,
            build_opponent_lineup,
            simulate_contest,
            REALISTIC_PARAMS,
            OPTIMAL_STRATEGY_MAP,
            STRATEGY_PARAMS,
            get_slate_size,
            SimulatedPlayer
        )

        print("✓ Imported from fixed_simulation_core (relative)")
    except ImportError as e:
        print(f"❌ ERROR: Could not import from fixed_simulation_core: {e}")
        print("Make sure fixed_simulation_core.py is in the simulation directory!")

        # Create minimal fallbacks
        REALISTIC_PARAMS = {
            'cash_field': {'sharp': 0.25, 'good': 0.35, 'average': 0.30, 'weak': 0.10},
            'gpp_field': {'elite': 0.05, 'sharp': 0.15, 'good': 0.30, 'average': 0.35, 'weak': 0.15}
        }
        OPTIMAL_STRATEGY_MAP = {
            'cash': {'small': 'pitcher_dominance', 'medium': 'projection_monster', 'large': 'projection_monster'},
            'gpp': {'small': 'tournament_winner_gpp', 'medium': 'tournament_winner_gpp', 'large': 'correlation_value'}
        }
        STRATEGY_PARAMS = {}


        def get_slate_size(num_games):
            if num_games <= 5:
                return 'small'
            elif num_games <= 10:
                return 'medium'
            else:
                return 'large'

# Import strategy functions from YOUR files
strategy_functions = {}

# Cash strategies from cash_strategies.py
try:
    from main_optimizer.cash_strategies import build_projection_monster

    strategy_functions['projection_monster'] = build_projection_monster
    print("✓ Imported build_projection_monster")
except ImportError as e:
    print(f"⚠️ Could not import build_projection_monster: {e}")

try:
    from main_optimizer.cash_strategies import build_pitcher_dominance

    strategy_functions['pitcher_dominance'] = build_pitcher_dominance
    print("✓ Imported build_pitcher_dominance")
except ImportError as e:
    print(f"⚠️ Could not import build_pitcher_dominance: {e}")

# GPP strategies from gpp_strategies.py
try:
    from main_optimizer.gpp_strategies import build_correlation_value

    strategy_functions['correlation_value'] = build_correlation_value
    print("✓ Imported build_correlation_value")
except ImportError as e:
    print(f"⚠️ Could not import build_correlation_value: {e}")

# Tournament winner from its own file
try:
    from main_optimizer.tournament_winner_gpp_strategy import build_tournament_winner_gpp

    strategy_functions['tournament_winner_gpp'] = build_tournament_winner_gpp
    print("✓ Imported build_tournament_winner_gpp")
except ImportError as e:
    print(f"⚠️ Could not import build_tournament_winner_gpp: {e}")

# Try to import other GPP strategies
try:
    from main_optimizer.gpp_strategies import (
        build_smart_stack,
        build_matchup_leverage_stack,
        build_truly_smart_stack
    )

    strategy_functions['smart_stack'] = build_smart_stack
    strategy_functions['matchup_leverage_stack'] = build_matchup_leverage_stack
    strategy_functions['truly_smart_stack'] = build_truly_smart_stack
    print("✓ Imported additional GPP strategies")
except ImportError:
    print("⚠️ Some GPP strategies not available")
    # Import fallback strategies
    from main_optimizer.gpp_strategies_fallback import *
    print("✅ Loaded fallback GPP strategies")


# Create simple fallback strategies if needed
if 'projection_monster' not in strategy_functions:
    def fallback_projection_monster(players, params=None):
        """Simple high projection strategy"""
        return sorted(players, key=lambda p: getattr(p, 'base_projection', 10), reverse=True)[:10]


    strategy_functions['projection_monster'] = fallback_projection_monster
    print("✓ Created fallback for projection_monster")

if 'tournament_winner_gpp' not in strategy_functions:
    def fallback_tournament_winner(players, params=None):
        """Simple low ownership leverage"""
        return sorted(players,
                      key=lambda p: getattr(p, 'base_projection', 10) / max(getattr(p, 'ownership_projection', 15), 1),
                      reverse=True)[:10]


    strategy_functions['tournament_winner_gpp'] = fallback_tournament_winner
    print("✓ Created fallback for tournament_winner_gpp")

print(f"\n{'=' * 60}")
print(f"✅ Initialization Complete")
print(f"Strategies loaded: {list(strategy_functions.keys())}")
print(f"{'=' * 60}\n")


class ComprehensiveSimulationRunner:
    """
    Runs comprehensive simulations of YOUR strategies vs realistic fields
    """

    def __init__(self, num_cores: int = None):
        self.num_cores = num_cores or max(1, mp.cpu_count() - 1)  # Leave one core free
        self.results = []
        self.summary_stats = {}

        print(f"🚀 Comprehensive Simulation Runner initialized")
        print(f"   CPU cores: {self.num_cores}")
        print(f"   Available strategies: {list(strategy_functions.keys())}")

    def convert_to_unified_players(self, sim_players: List) -> List[UnifiedPlayer]:
        """Convert simulated players to UnifiedPlayer objects"""
        unified_players = []

        for sp in sim_players:
            # Create UnifiedPlayer with required arguments
            player = UnifiedPlayer(
                id=str(hash(sp.name)),
                name=sp.name,
                team=sp.team,
                salary=sp.salary,
                primary_position=sp.position,
                positions=[sp.position]
            )

            # Set additional attributes
            player.AvgPointsPerGame = sp.projection
            player.base_projection = sp.projection
            player.dff_projection = sp.projection
            player.projection = sp.projection

            # Position info
            player.is_pitcher = (sp.position == 'P')
            player.position = sp.position

            # Batting order
            if sp.position != 'P':
                player.batting_order = getattr(sp, 'batting_order', 5)
            else:
                player.batting_order = None

            # Performance metrics
            player.recent_performance = getattr(sp, 'recent_performance', 1.0)
            player.consistency_score = getattr(sp, 'consistency_score', 0.7)
            player.matchup_score = getattr(sp, 'matchup_score', 1.0)
            player.floor = sp.projection * 0.7
            player.ceiling = sp.projection * 1.5

            # Vegas data
            player.vegas_total = getattr(sp, 'vegas_total', 8.5)
            player.game_total = getattr(sp, 'game_total', 8.5)
            player.team_total = getattr(sp, 'team_total', 4.25)
            player.implied_team_score = player.team_total

            # Ownership
            player.ownership_projection = getattr(sp, 'ownership', 15.0)
            player.projected_ownership = player.ownership_projection

            # Advanced stats
            player.park_factor = getattr(sp, 'park_factor', 1.0)
            player.weather_score = getattr(sp, 'weather_score', 1.0)
            player.barrel_rate = getattr(sp, 'barrel_rate', 8.0)
            player.hard_hit_rate = getattr(sp, 'hard_hit_rate', 35.0)
            player.xwoba = getattr(sp, 'xwoba', 0.320)

            # Correlation/Stack scores
            player.stack_score = 0.0
            player.correlation_score = 0.0
            player.game_stack_score = 0.0

            # Optimization scores
            player.optimization_score = sp.projection
            player.enhanced_score = sp.projection
            player.gpp_score = sp.projection
            player.cash_score = sp.projection

            # Other attributes
            player.value = sp.projection / (sp.salary / 1000) if sp.salary > 0 else 0
            player.points_per_dollar = player.value
            player.recent_scores = [sp.projection * 0.9, sp.projection * 1.1, sp.projection * 0.95]
            player.dff_l5_avg = sp.projection

            unified_players.append(player)

        return unified_players

    def build_your_lineup(self, slate: Dict, contest_type: str, strategy: str) -> Dict:
        """Build lineup using YOUR ACTUAL MILP OPTIMIZER with salary constraints"""

        try:
            # Convert to UnifiedPlayer objects
            unified_players = self.convert_to_unified_players(slate['players'])

            # CRITICAL: Use your ACTUAL optimizer system!
            from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
            from main_optimizer.unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig

            # Create system instance
            system = UnifiedCoreSystem()

            # Set up players
            system.players = unified_players
            system.player_pool = unified_players
            system.csv_loaded = True

            # Create optimizer with proper config
            config = OptimizationConfig(
                salary_cap=50000,  # DraftKings salary cap
                min_salary_usage=0.90,  # Use at least 90% of cap
                position_requirements={
                    "P": 2,
                    "C": 1,
                    "1B": 1,
                    "2B": 1,
                    "3B": 1,
                    "SS": 1,
                    "OF": 3
                }
            )

            optimizer = UnifiedMILPOptimizer(config)

            # Set contest type for proper scoring
            optimizer.config.contest_type = contest_type

            # Calculate scores using your scoring engine
            for player in unified_players:
                # Your system should have already scored these
                if not hasattr(player, 'optimization_score'):
                    player.optimization_score = getattr(player, 'projection', 10)

            # Run MILP optimization with salary constraints
            lineup_players, total_score = optimizer.optimize_lineup(
                players=unified_players,
                strategy=strategy,
                contest_type=contest_type
            )

            # Validate lineup
            if not lineup_players:
                print(f"❌ Optimizer returned no players for {strategy}")
                # Fallback to simple strategy
                return self.build_simple_lineup(unified_players, strategy)

            # Check salary
            total_salary = sum(p.salary for p in lineup_players)
            if total_salary > 50000:
                print(f"❌ ERROR: Lineup over cap: ${total_salary}")
                return None

            # Return proper format
            return {
                'players': lineup_players,
                'strategy': strategy,
                'contest_type': contest_type,
                'total_salary': total_salary,
                'total_projection': sum(getattr(p, 'projection', 10) for p in lineup_players),
                'optimization_score': total_score
            }

        except Exception as e:
            print(f"❌ Error using MILP optimizer: {e}")
            # Fallback to salary-constrained simple strategy
            return self.build_simple_lineup(unified_players, strategy)

    def run_single_slate_simulation(self, args: Tuple) -> Dict:
        """Run simulation for a single slate with REALISTIC competition"""

        slate_id, num_games, contest_type, field_size = args

        try:
            # Generate slate
            if 'generate_realistic_slate' in globals():
                slate = generate_realistic_slate(num_games, slate_id)
            else:
                slate = self._generate_simple_slate(num_games, slate_id)

            slate_size = get_slate_size(num_games)

            # Get optimal strategy for YOU
            strategy_name = OPTIMAL_STRATEGY_MAP[contest_type][slate_size]

            # Build YOUR lineup
            your_lineup = self.build_your_lineup(slate, contest_type, strategy_name)

            if not your_lineup:
                return {'error': 'Failed to build lineup', 'slate_id': slate_id}

            if 'players' not in your_lineup or not your_lineup['players']:
                return {'error': 'Lineup has no players', 'slate_id': slate_id}

            # CRITICAL FIX: Make opponents MUCH stronger
            # Generate field with SALARY CONSTRAINTS and REALISTIC VARIANCE
            field = []

            # Determine field distribution based on contest type
            if contest_type == 'cash':
                skill_distribution = [
                    ('elite', 0.15),  # 15% elite players
                    ('sharp', 0.30),  # 30% sharp players
                    ('average', 0.35),  # 35% average players
                    ('weak', 0.20)  # 20% weak players
                ]
            else:  # GPP
                skill_distribution = [
                    ('elite', 0.05),  # 5% elite
                    ('sharp', 0.15),  # 15% sharp
                    ('average', 0.30),  # 30% average
                    ('weak', 0.50)  # 50% weak
                ]

            # Build opponents for each skill level
            current_count = 0
            for skill_level, percentage in skill_distribution:
                num_opponents = int(field_size * percentage)

                # Ensure we fill exactly field_size
                if skill_level == skill_distribution[-1][0]:  # Last category
                    num_opponents = field_size - current_count

                for i in range(num_opponents):
                    opp_lineup = None

                    # Elite players - use optimizer with good projections
                    if skill_level == 'elite':
                        # 50% chance they use YOUR strategy, 50% use their own
                        if random.random() < 0.5 and contest_type == 'cash':
                            # Use your strategy but with slightly different projections
                            opp_lineup = self.build_opponent_with_optimizer(
                                slate['players'], contest_type, strategy_name,
                                projection_noise=0.05, min_salary=48000
                            )
                        else:
                            # Use different strategies
                            elite_strategy = random.choice([
                                'projection_monster', 'correlation_value', 'tournament_winner_gpp'
                            ])
                            opp_lineup = self.build_opponent_with_optimizer(
                                slate['players'], contest_type, elite_strategy,
                                projection_noise=0.08, min_salary=47500
                            )

                    # Sharp players - use optimizer with some variance
                    elif skill_level == 'sharp':
                        sharp_strategy = random.choice([
                            'balanced_60_40', 'projection_monster', 'game_stack_3_2'
                        ])
                        opp_lineup = self.build_opponent_with_optimizer(
                            slate['players'], contest_type, sharp_strategy,
                            projection_noise=0.12, min_salary=47000
                        )

                    # Average players - more mistakes
                    elif skill_level == 'average':
                        # Use simpler salary-constrained builder
                        opp_lineup = self.build_salary_constrained_lineup(
                            slate['players'], skill_level='average',
                            target_salary=46000, max_salary=50000
                        )

                    # Weak players - poor decisions but still salary compliant
                    else:  # weak
                        opp_lineup = self.build_salary_constrained_lineup(
                            slate['players'], skill_level='weak',
                            target_salary=44000, max_salary=50000
                        )

                    # Add to field if valid
                    if opp_lineup and self.validate_lineup(opp_lineup):
                        field.append(opp_lineup)
                    else:
                        # Fallback to simple valid lineup
                        fallback = self.build_salary_constrained_lineup(
                            slate['players'], skill_level=skill_level,
                            target_salary=45000, max_salary=50000
                        )
                        if fallback:
                            field.append(fallback)

                current_count += num_opponents

            # Shuffle field so it's not ordered by skill
            random.shuffle(field)

            # Debug output every 10th slate
            if slate_id % 10 == 0:
                your_proj = sum(getattr(p, 'projection', 10) for p in your_lineup['players'])
                your_salary = sum(getattr(p, 'salary', 0) for p in your_lineup['players'])

                # Sample field analysis
                field_salaries = []
                field_projs = []
                for opp in field[:10]:  # Check first 10
                    if isinstance(opp, dict) and 'players' in opp:
                        opp_salary = sum(getattr(p, 'salary', 0) for p in opp['players'])
                        opp_proj = sum(getattr(p, 'projection', 10) for p in opp['players'])
                        field_salaries.append(opp_salary)
                        field_projs.append(opp_proj)

                print(f"DEBUG Slate {slate_id} ({contest_type}):")
                print(f"  Your lineup: ${your_salary:,} salary, {your_proj:.1f} projection")
                if field_salaries:
                    print(
                        f"  Avg opponent: ${sum(field_salaries) // len(field_salaries):,} salary, {sum(field_projs) / len(field_projs):.1f} projection")
                    print(f"  Max opponent salary: ${max(field_salaries):,}")
                    if max(field_salaries) > 50000:
                        print(f"  ⚠️ WARNING: Opponent over salary cap!")

            # DEBUG: Check lineup strengths every 10th slate
            if slate_id % 10 == 0:
                your_proj = sum(getattr(p, 'projection', 10) for p in your_lineup['players'])

                # Calculate average opponent projection
                opp_projs = []
                for opp in field[:10]:  # Check first 10 opponents
                    if isinstance(opp, dict) and 'players' in opp:
                        opp_proj = sum(getattr(p, 'projection', 10) for p in opp['players'])
                        opp_projs.append(opp_proj)

                avg_opp = sum(opp_projs) / len(opp_projs) if opp_projs else 0

                print(f"DEBUG Slate {slate_id} ({contest_type}):")
                print(f"  Your projection: {your_proj:.1f}")
                print(f"  Avg opponent: {avg_opp:.1f}")
                print(f"  Your advantage: {(your_proj / avg_opp - 1) * 100:.1f}%" if avg_opp > 0 else "N/A")

            # Simulate contest with variance
            if 'simulate_contest' in globals():
                result = simulate_contest(your_lineup, field, contest_type)
            else:
                result = self._simulate_simple_contest(your_lineup, field, contest_type)

            # Add metadata
            result.update({
                'slate_id': slate_id,
                'num_games': num_games,
                'slate_size': slate_size,
                'contest_type': contest_type,
                'strategy': strategy_name,
                'field_size': len(field)
            })

            return result

        except Exception as e:
            import traceback
            print(f"Error in slate {slate_id}: {e}")
            traceback.print_exc()
            return {'error': str(e), 'slate_id': slate_id}

    def build_opponent_with_optimizer(self, players: List, contest_type: str,
                                      strategy: str, projection_noise: float = 0.1,
                                      min_salary: int = 45000) -> Dict:
        """Build opponent using optimizer with projection variance"""

        try:
            from main_optimizer.unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig

            # Create config with salary constraints
            config = OptimizationConfig(
                salary_cap=50000,
                min_salary_usage=min_salary / 50000,
                position_requirements={
                    "P": 2, "C": 1, "1B": 1, "2B": 1,
                    "3B": 1, "SS": 1, "OF": 3
                }
            )

            optimizer = UnifiedMILPOptimizer(config)
            optimizer.config.contest_type = contest_type

            # Apply projection noise to simulate different projection systems
            modified_players = []
            for player in players:
                p_copy = type('Player', (), {})()
                for attr in ['name', 'team', 'salary', 'position', 'primary_position', 'positions']:
                    if hasattr(player, attr):
                        setattr(p_copy, attr, getattr(player, attr))

                # Add noise to projection
                base_proj = getattr(player, 'projection', 10)
                p_copy.projection = base_proj * np.random.normal(1.0, projection_noise)
                p_copy.optimization_score = p_copy.projection
                p_copy.base_projection = p_copy.projection

                modified_players.append(p_copy)

            # Run optimization
            lineup_players, _ = optimizer.optimize_lineup(
                players=modified_players,
                strategy=strategy,
                contest_type=contest_type
            )

            if lineup_players:
                # Map back to original players
                final_lineup = []
                for selected in lineup_players:
                    original = next((p for p in players if p.name == selected.name), selected)
                    final_lineup.append(original)

                total_salary = sum(p.salary for p in final_lineup)

                return {
                    'players': final_lineup,
                    'skill_level': 'optimizer',
                    'strategy': strategy,
                    'total_salary': total_salary
                }
        except:
            pass

        return None

    def build_salary_constrained_lineup(self, players: List, skill_level: str,
                                        target_salary: int = 47000,
                                        max_salary: int = 50000) -> Dict:
        """Build lineup with salary constraints but no optimizer"""

        # Sort by value based on skill level
        if skill_level == 'average':
            # Decent value calculation
            for p in players:
                p.temp_value = p.projection / max(p.salary / 1000, 1)
            sorted_players = sorted(players, key=lambda p: p.temp_value * random.uniform(0.9, 1.1), reverse=True)
        else:  # weak
            # Poor player evaluation
            sorted_players = list(players)
            random.shuffle(sorted_players)

        # Build lineup respecting positions and salary
        lineup = []
        total_salary = 0
        positions_filled = {'P': 0, 'C': 0, '1B': 0, '2B': 0, '3B': 0, 'SS': 0, 'OF': 0}
        positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        for player in sorted_players:
            if len(lineup) >= 10:
                break

            pos = player.position if hasattr(player, 'position') else player.primary_position

            if pos in positions_needed and positions_filled[pos] < positions_needed[pos]:
                if total_salary + player.salary <= max_salary:
                    lineup.append(player)
                    total_salary += player.salary
                    positions_filled[pos] += 1

        # Fill remaining spots if needed
        if len(lineup) < 10:
            for player in sorted_players:
                if player not in lineup and total_salary + player.salary <= max_salary:
                    lineup.append(player)
                    total_salary += player.salary
                    if len(lineup) >= 10:
                        break

        if len(lineup) == 10 and total_salary <= max_salary:
            return {
                'players': lineup,
                'skill_level': skill_level,
                'total_salary': total_salary
            }

        return None

    def validate_lineup(self, lineup: Dict) -> bool:
        """Validate lineup has correct positions and salary"""

        if not lineup or 'players' not in lineup:
            return False

        players = lineup['players']

        # Check player count
        if len(players) != 10:
            return False

        # Check salary
        total_salary = sum(getattr(p, 'salary', 0) for p in players)
        if total_salary > 50000:
            return False

        # Check positions
        positions = {}
        for p in players:
            pos = p.position if hasattr(p, 'position') else p.primary_position
            positions[pos] = positions.get(pos, 0) + 1

        required = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        for pos, count in required.items():
            if positions.get(pos, 0) != count:
                return False

        return True

    def build_simple_lineup(self, players: List, strategy: str) -> Dict:
        """Fallback lineup builder WITH SALARY CONSTRAINTS"""

        # Sort by value (projection per dollar)
        for p in players:
            p.value = getattr(p, 'projection', 10) / max(p.salary / 1000, 1)

        players.sort(key=lambda p: p.value, reverse=True)

        # Build lineup respecting positions and salary
        lineup = []
        total_salary = 0
        positions_filled = {'P': 0, 'C': 0, '1B': 0, '2B': 0, '3B': 0, 'SS': 0, 'OF': 0}
        positions_needed = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        for player in players:
            pos = player.primary_position

            # Check if we need this position
            if pos in positions_needed and positions_filled[pos] < positions_needed[pos]:
                # Check salary constraint
                if total_salary + player.salary <= 50000:
                    lineup.append(player)
                    total_salary += player.salary
                    positions_filled[pos] += 1

                    # Check if lineup complete
                    if len(lineup) == 10:
                        break

        # Validate lineup
        if len(lineup) < 10:
            print(f"⚠️ Only built {len(lineup)} players within salary")

        return {
            'players': lineup,
            'total_salary': total_salary,
            'strategy': strategy
        }

    def _generate_simple_slate(self, num_games: int, slate_id: int) -> Dict:
        """Fallback slate generation"""
        players = []
        for i in range(num_games * 18):  # ~18 players per game
            players.append(type('Player', (), {
                'name': f'Player_{i}',
                'team': f'Team_{i % (num_games * 2)}',
                'position': ['P', 'C', '1B', '2B', '3B', 'SS', 'OF'][i % 7],
                'salary': 3000 + (i * 100) % 7000,
                'projection': 5 + (i * 0.5) % 20,
                'ownership': 5 + (i * 2) % 35
            })())

        return {'players': players, 'slate_id': slate_id, 'num_games': num_games}

    def _build_simple_opponent(self, players: List, skill_level: str) -> List:
        """Fallback opponent builder"""
        if skill_level in ['elite', 'sharp']:
            sorted_players = sorted(players, key=lambda p: p.projection, reverse=True)
        else:
            sorted_players = list(players)
            random.shuffle(sorted_players)

        return sorted_players[:10]

    def build_realistic_opponent(self, players: List, contest_type: str, skill_level: str) -> Dict:
        """Build opponent lineup with realistic variance - NOT everyone uses your exact system"""

        import random
        import numpy as np

        try:
            from main_optimizer.unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig

            # Create optimizer
            config = OptimizationConfig(
                salary_cap=50000,
                position_requirements={
                    "P": 2, "C": 1, "1B": 1, "2B": 1,
                    "3B": 1, "SS": 1, "OF": 3
                }
            )

            # CRITICAL: Vary the configuration based on skill level
            if skill_level == 'elite':
                # Elite players have good but DIFFERENT projections than you
                config.min_salary_usage = 0.95
                projection_variance = 0.05  # Small variance
                strategy_pool = ['projection_monster', 'correlation_value', 'tournament_winner_gpp']

            elif skill_level == 'sharp':
                # Sharp players use decent strategies with more variance
                config.min_salary_usage = 0.92
                projection_variance = 0.10
                strategy_pool = ['balanced_60_40', 'game_stack_3_2', 'projection_monster']

            elif skill_level == 'average':
                # Average players make more mistakes
                config.min_salary_usage = 0.88
                projection_variance = 0.15
                strategy_pool = ['balanced_50_50', 'balanced_60_40']

            else:  # weak
                # Weak players make poor decisions
                config.min_salary_usage = 0.85
                projection_variance = 0.25
                strategy_pool = ['balanced_50_50']  # Basic strategy only

            optimizer = UnifiedMILPOptimizer(config)
            optimizer.config.contest_type = contest_type

            # IMPORTANT: Give opponents DIFFERENT projections than you!
            # This simulates different data sources/models
            modified_players = []
            for player in players:
                # Create a copy to avoid modifying original
                p_copy = type('Player', (), {})()
                for attr in dir(player):
                    if not attr.startswith('_'):
                        try:
                            setattr(p_copy, attr, getattr(player, attr))
                        except:
                            pass

                # Apply projection variance based on skill level
                base_proj = getattr(player, 'projection', 10)

                if skill_level == 'elite':
                    # Elite players have good projections but different from yours
                    # Use different "model" - emphasize different factors
                    if player.position == 'P':
                        # Some elite players value pitchers differently
                        p_copy.projection = base_proj * np.random.normal(1.0, projection_variance)
                    else:
                        # Some emphasize recent form more, others matchups
                        emphasis = random.choice(['recent', 'matchup', 'vegas'])
                        if emphasis == 'recent':
                            p_copy.projection = base_proj * (0.7 + 0.3 * random.uniform(0.8, 1.2))
                        elif emphasis == 'matchup':
                            p_copy.projection = base_proj * (0.8 + 0.2 * random.uniform(0.7, 1.3))
                        else:  # vegas
                            p_copy.projection = base_proj * (0.9 + 0.1 * random.uniform(0.8, 1.2))

                else:
                    # Non-elite have noisier projections
                    p_copy.projection = base_proj * np.random.normal(1.0, projection_variance)

                p_copy.optimization_score = p_copy.projection
                modified_players.append(p_copy)

            # Choose strategy (different players prefer different strategies)
            if contest_type == 'cash':
                if skill_level == 'elite':
                    # Elite cash players might use different approaches
                    strategy = random.choice(['projection_monster', 'pitcher_dominance', 'floor_ceiling'])
                else:
                    strategy = random.choice(strategy_pool) if strategy_pool else 'balanced_50_50'
            else:  # GPP
                strategy = random.choice(strategy_pool) if strategy_pool else 'balanced_60_40'

            # Run optimization with modified projections
            lineup_players, total_score = optimizer.optimize_lineup(
                players=modified_players,
                strategy=strategy,
                contest_type=contest_type
            )

            if not lineup_players or len(lineup_players) < 10:
                # Fallback to simple method
                return self._build_simple_opponent(players, skill_level)

            # Validate salary
            total_salary = sum(p.salary for p in lineup_players)
            if total_salary > 50000:
                print(f"❌ Opponent over cap: ${total_salary}")
                return self._build_simple_opponent(players, skill_level)

            # Use original players (not modified copies) for the actual lineup
            final_lineup = []
            for selected in lineup_players:
                # Find the original player
                original = next((p for p in players if p.name == selected.name), selected)
                final_lineup.append(original)

            return {
                'players': final_lineup,
                'skill_level': skill_level,
                'strategy_used': strategy,
                'total_salary': total_salary,
                'total_projection': sum(getattr(p, 'projection', 10) for p in final_lineup)
            }

        except Exception as e:
            print(f"⚠️ Error building {skill_level} opponent: {e}")
            # Fallback to simple salary-constrained method
            return self._build_simple_opponent(players, skill_level)

    def _simulate_simple_contest(self, your_lineup: List, field: List, contest_type: str) -> Dict:
        """Realistic contest simulation with proper variance"""
        import numpy as np

        # Calculate YOUR score with realistic variance
        your_projection = sum(getattr(p, 'projection', 10) for p in your_lineup['players'])

        # Apply realistic variance (15% standard deviation)
        your_actual = your_projection * np.random.normal(1.0, 0.15)
        your_actual = max(0, your_actual)

        # Calculate FIELD scores with variance
        field_scores = []
        for opponent in field:
            opp_players = opponent['players'] if isinstance(opponent, dict) else opponent
            opp_projection = sum(getattr(p, 'projection', 10) for p in opp_players)

            # Apply variance based on skill level
            skill = opponent.get('skill_level', 'average') if isinstance(opponent, dict) else 'average'

            if skill == 'elite':
                # Elite players have less variance (more consistent)
                opp_actual = opp_projection * np.random.normal(1.0, 0.12)
            elif skill == 'sharp':
                opp_actual = opp_projection * np.random.normal(1.0, 0.15)
            elif skill == 'average':
                opp_actual = opp_projection * np.random.normal(1.0, 0.18)
            else:  # weak
                opp_actual = opp_projection * np.random.normal(1.0, 0.22)

            opp_actual = max(0, opp_actual)
            field_scores.append(opp_actual)

        # Calculate rank and percentile
        field_scores.sort(reverse=True)
        your_rank = sum(1 for score in field_scores if score > your_actual) + 1
        percentile = (len(field_scores) - your_rank + 1) / len(field_scores) * 100

        # Realistic payouts
        if contest_type == 'cash':
            # Top 45% win in cash games (realistic)
            cutoff = int(len(field_scores) * 0.45)
            won = your_rank <= cutoff
            roi = 80 if won else -100  # 0.8x payout
        else:
            # GPP payouts
            if your_rank == 1:
                roi = 500 + np.random.randint(0, 400)
            elif your_rank <= 3:
                roi = 200 + np.random.randint(0, 200)
            elif percentile >= 90:  # Top 10%
                roi = np.random.randint(-50, 50)
            elif percentile >= 80:  # Top 20%
                roi = -75
            else:
                roi = -100

        return {
            'your_score': your_actual,
            'your_rank': your_rank,
            'percentile': percentile,
            'won': roi > 0,
            'roi': roi
        }

    def run_comprehensive_test(self,
                               num_simulations: int = 1000,
                               contest_types: List[str] = None,
                               slate_sizes: List[str] = None,
                               field_size: int = 100):
        """Run comprehensive simulation test"""

        contest_types = contest_types or ['cash', 'gpp']
        slate_sizes = slate_sizes or ['small', 'medium', 'large']

        print(f"\n{'=' * 60}")
        print(f"🏁 STARTING COMPREHENSIVE SIMULATION")
        print(f"{'=' * 60}")
        print(f"Simulations per config: {num_simulations}")
        print(f"Contest types: {contest_types}")
        print(f"Slate sizes: {slate_sizes}")
        print(f"Field size: {field_size}")

        # Create tasks
        tasks = []
        slate_id = 1000

        game_counts = {
            'small': [3, 4, 5],
            'medium': [7, 8, 9],
            'large': [11, 12, 13]
        }

        for contest_type in contest_types:
            for slate_size in slate_sizes:
                for _ in range(num_simulations):
                    num_games = random.choice(game_counts[slate_size])
                    tasks.append((slate_id, num_games, contest_type, field_size))
                    slate_id += 1

        print(f"Running {len(tasks)} simulations on {self.num_cores} cores...")

        # Run simulations
        start_time = time.time()

        with mp.Pool(self.num_cores) as pool:
            results = []
            for i, result in enumerate(pool.imap_unordered(self.run_single_slate_simulation, tasks)):
                results.append(result)
                if (i + 1) % 50 == 0:
                    print(f"Progress: {i + 1}/{len(tasks)} ({(i + 1) / len(tasks) * 100:.1f}%)")

        self.results = results

        # Calculate and display results
        self.calculate_summary_stats()
        self.print_results()
        self.save_results()

        print(f"\n✅ Complete in {(time.time() - start_time) / 60:.1f} minutes")
        return self.summary_stats

    def calculate_summary_stats(self):
        """Calculate summary statistics"""
        valid_results = [r for r in self.results if 'error' not in r]

        if not valid_results:
            print("❌ No successful simulations!")
            return

        df = pd.DataFrame(valid_results)
        self.summary_stats = {}

        for (contest_type, slate_size, strategy), group in df.groupby(['contest_type', 'slate_size', 'strategy']):
            key = f"{contest_type}_{slate_size}_{strategy}"

            if contest_type == 'cash':
                self.summary_stats[key] = {
                    'win_rate': (group['won'].mean()) * 100,
                    'avg_roi': group['roi'].mean(),
                    'count': len(group)
                }
            else:
                self.summary_stats[key] = {
                    'avg_roi': group['roi'].mean(),
                    'top_10_rate': (group['percentile'] >= 90).mean() * 100,
                    'count': len(group)
                }

    def print_results(self):
        """Print results summary"""
        print(f"\n{'=' * 60}")
        print("📊 SIMULATION RESULTS")
        print(f"{'=' * 60}")

        # Cash results
        print("\n💵 CASH GAMES:")
        for key, stats in self.summary_stats.items():
            if 'cash' in key:
                parts = key.split('_')
                print(f"{parts[1]:8} {parts[2]:20} Win: {stats['win_rate']:.1f}% ROI: {stats['avg_roi']:.1f}%")

        # GPP results
        print("\n🏆 GPP TOURNAMENTS:")
        for key, stats in self.summary_stats.items():
            if 'gpp' in key:
                parts = key.split('_')
                print(
                    f"{parts[1]:8} {parts[2]:20} ROI: {stats['avg_roi']:.1f}% Top10: {stats.get('top_10_rate', 0):.1f}%")

    def save_results(self):
        """Save results to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        df = pd.DataFrame(self.results)
        df.to_csv(f'simulation_results_{timestamp}.csv', index=False)

        with open(f'simulation_summary_{timestamp}.json', 'w') as f:
            json.dump(self.summary_stats, f, indent=2)

        print(f"\n💾 Saved: simulation_results_{timestamp}.csv")


if __name__ == "__main__":
    runner = ComprehensiveSimulationRunner()

    print("\nSelect test type:")
    print("1. Quick (100 simulations)")
    print("2. Standard (500 simulations)")
    print("3. Full (1000 simulations)")

    choice = input("\nChoice (1-3): ")

    num_sims = {'1': 100, '2': 500, '3': 1000}.get(choice, 100)

    runner.run_comprehensive_test(
        num_simulations=num_sims // 6,
        contest_types=['cash', 'gpp'],
        slate_sizes=['small', 'medium', 'large'],
        field_size=100
    )