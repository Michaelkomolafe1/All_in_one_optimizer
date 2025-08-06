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
            # Create UnifiedPlayer with required attributes
            up_data = {
                'id': str(hash(sp.name)),
                'name': sp.name,
                'team': sp.team,
                'salary': sp.salary,
                'primary_position': sp.position,
                'positions': [sp.position],
                'base_projection': sp.projection
            }

            up = UnifiedPlayer(**up_data)

            # Add additional attributes
            up.is_pitcher = (sp.position == 'P')
            up.ownership_projection = getattr(sp, 'ownership', 15)
            up.park_adjusted_projection = sp.projection * getattr(sp, 'park_factor', 1.0)

            # Copy all attributes from simulated player
            for attr in dir(sp):
                if not attr.startswith('_') and not callable(getattr(sp, attr)):
                    if not hasattr(up, attr):
                        setattr(up, attr, getattr(sp, attr))

            up.optimization_score = 0
            unified_players.append(up)

        return unified_players

    def build_your_lineup(self, slate: Dict, contest_type: str, strategy_name: str) -> Optional[List]:
        """Build YOUR lineup using YOUR strategies"""

        # Convert players
        unified_players = self.convert_to_unified_players(slate['players'])

        # Get strategy function
        strategy_func = strategy_functions.get(strategy_name)

        if not strategy_func:
            print(f"⚠️ Strategy {strategy_name} not found, using projection sort")
            lineup_players = sorted(unified_players, key=lambda p: p.base_projection, reverse=True)[:10]
        else:
            try:
                # Get parameters if available
                params = STRATEGY_PARAMS.get(strategy_name, {})

                # Call strategy
                result = strategy_func(unified_players,
                                       params) if 'params' in strategy_func.__code__.co_varnames else strategy_func(
                    unified_players)

                # Handle different return types
                if isinstance(result, list):
                    lineup_players = result[:10]
                elif hasattr(result, 'players'):
                    lineup_players = result.players[:10]
                else:
                    print(f"⚠️ Unexpected return type from {strategy_name}")
                    lineup_players = sorted(unified_players, key=lambda p: p.base_projection, reverse=True)[:10]

            except Exception as e:
                print(f"⚠️ Error in {strategy_name}: {e}")
                lineup_players = sorted(unified_players, key=lambda p: p.base_projection, reverse=True)[:10]

        # Convert back to simulated players
        sim_lineup = []
        for up in lineup_players:
            for sp in slate['players']:
                if sp.name == up.name:
                    sim_lineup.append(sp)
                    break

        return sim_lineup if len(sim_lineup) == 10 else None

    def run_single_slate_simulation(self, args: Tuple) -> Dict:
        """Run simulation for a single slate"""

        slate_id, num_games, contest_type, field_size = args

        try:
            # Generate slate
            if 'generate_realistic_slate' in globals():
                slate = generate_realistic_slate(num_games, slate_id)
            else:
                # Fallback slate generation
                print("Using fallback slate generation")
                slate = self._generate_simple_slate(num_games, slate_id)

            slate_size = get_slate_size(num_games)

            # Get optimal strategy
            strategy_name = OPTIMAL_STRATEGY_MAP[contest_type][slate_size]

            # Build lineup
            your_lineup = self.build_your_lineup(slate, contest_type, strategy_name)

            if not your_lineup:
                return {'error': 'Failed to build lineup', 'slate_id': slate_id}

            # Generate field
            field = []
            distribution = REALISTIC_PARAMS[f'{contest_type}_field']

            for skill_level, percentage in distribution.items():
                num_lineups = max(1, int(field_size * percentage))
                for _ in range(num_lineups):
                    if 'build_opponent_lineup' in globals():
                        opp_lineup = build_opponent_lineup(slate['players'], skill_level, contest_type)
                    else:
                        opp_lineup = self._build_simple_opponent(slate['players'], skill_level)

                    if opp_lineup:
                        field.append({'players': opp_lineup, 'skill_level': skill_level})

            # Simulate contest
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
            return {'error': str(e), 'slate_id': slate_id}

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

    def _simulate_simple_contest(self, your_lineup: List, field: List, contest_type: str) -> Dict:
        """Fallback contest simulation"""
        your_score = sum(p.projection * random.uniform(0.8, 1.2) for p in your_lineup)
        field_scores = [sum(p.projection * random.uniform(0.8, 1.2) for p in opp['players']) for opp in field]

        rank = sum(1 for s in field_scores if s > your_score) + 1
        percentile = (len(field_scores) - rank + 1) / len(field_scores) * 100

        if contest_type == 'cash':
            won = rank <= len(field_scores) // 2
            roi = 100 if won else -100
        else:
            if rank == 1:
                roi = 900
            elif rank <= 3:
                roi = 400
            elif percentile >= 90:
                roi = 100
            else:
                roi = -100

        return {
            'your_score': your_score,
            'your_rank': rank,
            'percentile': percentile,
            'roi': roi,
            'won': roi > 0
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