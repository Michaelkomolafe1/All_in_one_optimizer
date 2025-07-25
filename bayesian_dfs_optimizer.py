#!/usr/bin/env python3
"""
ULTIMATE BAYESIAN DFS OPTIMIZER
===============================
Incorporates all learnings from previous tests:
- Starts near proven winning parameters
- Tests synergies between multiple features
- Uses improved scoring system
- Enforces max 5 batters per team stack (DFS platform limit)
- Fast parallel processing with progress tracking
"""

import json
import multiprocessing as mp
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
from skopt import gp_minimize
from skopt.space import Categorical, Integer, Real
from skopt.utils import use_named_args

sys.path.append('/home/michael/Desktop/All_in_one_optimizer')
from fixed_complete_dfs_sim import *


# ----------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------
def _jsonify(obj: Any) -> Any:
    """Make numpy objects JSON-serializable."""
    if isinstance(obj, dict):
        return {k: _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonify(i) for i in obj]
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def _banner(text: str) -> None:
    print("\n" + "=" * 70)
    print(text.center(70))
    print("=" * 70)


def format_time(seconds):
    """Convert seconds to readable format"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes"
    else:
        return f"{seconds / 3600:.1f} hours"


# =============================================================================
# ENHANCED GPP PARAMETER SPACE
# Based on stacks_only winner + additional high-impact features
# =============================================================================

# Starting points for GPP optimization (proven good values)
GPP_X0 = [
    6.0,  # threshold_high (stacks_only winner used 6.0)
    5.5,  # threshold_med (stacks_only winner used 5.5)
    5.0,  # threshold_low (stacks_only winner used 5.0)
    1.30,  # mult_high (stacks_only winner used 1.30)
    1.20,  # mult_med
    1.10,  # mult_low
    0.80,  # mult_none
    4,  # stack_min
    5,  # stack_max (platform limit)
    5,  # stack_preferred (platform limit)
    1.11,  # batting_boost
    5,  # batting_positions
    1.18,  # ownership_low_boost
    0.85,  # ownership_high_penalty
    20,  # ownership_threshold
    1.13,  # pitcher_bad_boost
    0.87,  # pitcher_ace_penalty
    4.2,  # era_threshold
    10.0,  # barrel_rate_threshold
    1.20,  # barrel_rate_boost
    90.5,  # exit_velo_threshold
    1.10,  # exit_velo_boost
    0.025,  # xwoba_diff_threshold
    1.18,  # undervalued_boost
    10.0,  # min_k9_threshold
    1.18,  # high_k9_boost
    0.24,  # opp_k_rate_threshold
    1.14,  # high_opp_k_boost
    'any',  # correlation_type
]

ENHANCED_GPP_SPACE = [
    # CORE STACKING PARAMETERS (from winning stacks_only)
    # Starting points based on the 195.7% ROI winner
    Real(5.7, 6.5, name='threshold_high'),  # Winner used 6.0
    Real(5.2, 6.0, name='threshold_med'),  # Winner used 5.5
    Real(4.7, 5.5, name='threshold_low'),  # Winner used 5.0

    # Multipliers start near winning values but can explore
    Real(1.25, 1.35, name='mult_high'),  # Winner used 1.30
    Real(1.15, 1.25, name='mult_med'),  # Winner used 1.20
    Real(1.08, 1.15, name='mult_low'),  # Winner used 1.10
    Real(0.75, 0.85, name='mult_none'),  # Winner used 0.80

    # STACKING CONFIGURATION (max 5 batters per team)
    Integer(3, 5, name='stack_min'),  # Test 3-5 range
    Integer(4, 5, name='stack_max'),  # Max 5 batters allowed
    Integer(4, 5, name='stack_preferred'),  # Prefer 4-5 batters

    # BATTING ORDER (proven important)
    Real(1.08, 1.15, name='batting_boost'),  # Winner used 1.10
    Integer(4, 6, name='batting_positions'),  # Top 4-6 spots

    # NEW HIGH-IMPACT FEATURES TO TEST
    # These weren't in stacks_only but could enhance it

    # OWNERSHIP LEVERAGE (game theory)
    Real(1.10, 1.30, name='ownership_low_boost'),
    Real(0.75, 0.90, name='ownership_high_penalty'),
    Integer(10, 25, name='ownership_threshold'),

    # PITCHER MATCHUP QUALITY
    Real(1.08, 1.20, name='pitcher_bad_boost'),
    Real(0.80, 0.92, name='pitcher_ace_penalty'),
    Real(3.5, 4.5, name='era_threshold'),

    # STATCAST POWER METRICS
    Real(8.0, 12.0, name='barrel_rate_threshold'),
    Real(1.10, 1.30, name='barrel_rate_boost'),
    Real(88.0, 92.0, name='exit_velo_threshold'),
    Real(1.05, 1.15, name='exit_velo_boost'),

    # xSTATS DIFFERENTIAL (undervalued players)
    Real(0.015, 0.040, name='xwoba_diff_threshold'),
    Real(1.10, 1.25, name='undervalued_boost'),

    # PITCHER STRIKEOUT UPSIDE
    Real(8.5, 11.0, name='min_k9_threshold'),
    Real(1.12, 1.25, name='high_k9_boost'),
    Real(0.20, 0.28, name='opp_k_rate_threshold'),
    Real(1.08, 1.20, name='high_opp_k_boost'),

    # CORRELATION TYPE
    Categorical(['any', 'sequential', 'weighted'], name='correlation_type'),
]

# =============================================================================
# ENHANCED CASH PARAMETER SPACE
# Based on historical_optimized winner + enhancements
# =============================================================================

# Starting points for cash optimization
CASH_X0 = [
    0.40,  # weight_projection (historical_optimized used 0.40)
    0.35,  # weight_recent (historical_optimized used 0.35)
    0.25,  # weight_season (historical_optimized used 0.25)
    0.20,  # consistency_weight
    'std_dev',  # consistency_method
    5,  # recent_games_window
    1,  # use_platoon
    1.08,  # platoon_advantage_boost
    1,  # use_streaks
    1.10,  # streak_hot_boost
    0.90,  # streak_cold_penalty
    5,  # streak_window
    0.65,  # floor_weight
    0,  # use_opponent_quality
    0.90,  # vs_ace_penalty
    1.10,  # vs_bad_pitcher_boost
]

ENHANCED_CASH_SPACE = [
    # WEIGHT DISTRIBUTION (winner used 0.40/0.35/0.25)
    Real(0.30, 0.50, name='weight_projection'),  # Test around 0.40
    Real(0.25, 0.45, name='weight_recent'),  # Test around 0.35
    Real(0.15, 0.35, name='weight_season'),  # Test around 0.25

    # CONSISTENCY/CEILING BALANCE
    Real(0.10, 0.40, name='consistency_weight'),
    Categorical(['std_dev', 'floor_percentage', 'both'], name='consistency_method'),

    # RECENT FORM WINDOW
    Integer(3, 7, name='recent_games_window'),  # Winner used 5

    # NEW FEATURES FOR CASH
    # Platoon advantage
    Integer(0, 1, name='use_platoon'),
    Real(1.03, 1.12, name='platoon_advantage_boost'),

    # Hot/cold streaks
    Integer(0, 1, name='use_streaks'),
    Real(1.05, 1.15, name='streak_hot_boost'),
    Real(0.85, 0.95, name='streak_cold_penalty'),
    Integer(3, 7, name='streak_window'),

    # Floor/ceiling balance
    Real(0.5, 0.8, name='floor_weight'),

    # Opponent quality
    Integer(0, 1, name='use_opponent_quality'),
    Real(0.85, 0.95, name='vs_ace_penalty'),
    Real(1.05, 1.15, name='vs_bad_pitcher_boost'),
]


# =============================================================================
# ENHANCED SCORING SYSTEM (FAST PARALLEL)
# =============================================================================

def _run_single_gpp_enhanced(cfg: Dict[str, Any]) -> float:
    """Enhanced GPP scoring with better non-cashing differentiation"""
    try:
        sim = ComprehensiveValidatedSimulation(verbose=False)
        strategy = _make_enhanced_gpp_strategy(cfg)
        sim.strategies = {'test_strategy': strategy}
        slate = sim.contest_configs[0]

        players, games = sim.generate_realistic_slate(slate)
        res = sim.simulate_contest(players, games, strategy, 'gpp', slate)

        if not res:
            return -100.0

        roi = res.get('roi', -1.0) * 100

        # Enhanced scoring for non-cashing lineups
        if roi == -100.0:
            percentile = res.get('percentile', 0)
            rank = res.get('rank', 1000)
            field_size = res.get('field_size', 1000)

            # More nuanced scoring
            # Base: -100 to -50 based on percentile
            base_score = -100 + (percentile * 0.5)

            # Bonus for top 20% finishes (even if not cashing)
            if percentile > 80:
                base_score += 5

            # Small bonus for very large fields
            if field_size > 5000:
                base_score += 2

            return base_score
        else:
            # Cashed - return actual ROI with small bonuses
            if res.get('top_10_pct', False):
                roi += 10  # Bonus for top 10%
            if res.get('top_1_pct', False):
                roi += 20  # Additional bonus for winning

            return roi

    except Exception as e:
        return -100.0


def _run_single_cash_enhanced(cfg: Dict[str, Any]) -> float:
    """Enhanced cash game scoring"""
    try:
        sim = ComprehensiveValidatedSimulation(verbose=False)
        strategy = _make_enhanced_cash_strategy(cfg)
        sim.strategies = {'test_strategy': strategy}
        slate = sim.contest_configs[0]

        players, games = sim.generate_realistic_slate(slate)
        res = sim.simulate_contest(players, games, strategy, 'cash', slate)

        if not res:
            return 0.0

        # Multi-factor scoring for cash games
        base_score = 0.0

        # Primary factor: did we cash?
        if res.get('cashed', False):
            base_score = 70.0  # Base for cashing

            # Bonus for how far above cash line
            percentile = res.get('percentile', 50)
            if percentile > 60:
                base_score += (percentile - 60) * 0.3  # Up to +12 points
        else:
            # Didn't cash - score based on how close
            percentile = res.get('percentile', 0)
            if percentile > 45:  # Close to cash line
                base_score = 40 + (percentile - 45) * 2  # 40-50 points
            else:
                base_score = percentile * 0.8  # 0-36 points

        # Secondary factor: consistency (lower score variance is better)
        score = res.get('score', 0)
        if score > 0 and 'lineup' in res:
            # Rough consistency metric
            expected_score = sum(p.dk_projection for p in res['lineup'])
            if expected_score > 0:
                consistency = 1 - abs(score - expected_score) / expected_score
                base_score += consistency * 10  # Up to +10 for consistency

        return base_score

    except Exception as e:
        return 0.0


# =============================================================================
# ENHANCED STRATEGY BUILDERS
# =============================================================================

def _make_enhanced_gpp_strategy(params: Dict[str, Any]) -> 'BaseStrategy':
    """Build GPP strategy incorporating all learnings"""

    class EnhancedGPPStrategy(BaseStrategy):
        def __init__(self, cfg):
            super().__init__('enhanced_gpp')
            self.cfg = cfg
            self.uses_correlation = True

        def score_player(self, player, slate_context=None):
            score = player.dk_projection

            # CORE STACKING BOOST (proven winner)
            t, m = self.cfg['thresholds'], self.cfg['multipliers']
            if player.team_total > t[0]:
                score *= m[0]
            elif player.team_total > t[1]:
                score *= m[1]
            elif player.team_total > t[2]:
                score *= m[2]
            else:
                score *= m[3]

            # FEATURES APPLIED TO ALL POSITIONS
            feats = self.cfg.get('features', {})

            # Ownership leverage
            if 'ownership' in feats and hasattr(player, 'ownership_projection'):
                own = feats['ownership']
                if player.ownership_projection < own['threshold']:
                    score *= own['low_owned_boost']
                elif player.ownership_projection > own['threshold'] * 2:
                    score *= own['high_owned_penalty']

            # POSITION-SPECIFIC FEATURES
            if player.position != 'P':
                # HITTERS
                # Batting order (proven important)
                bat = self.cfg.get('batting_config', {})
                if hasattr(player, 'batting_order'):
                    if player.batting_order in bat.get('positions', []):
                        score *= bat.get('boost', 1.10)

                # Statcast power metrics
                if 'hitter_statcast' in feats:
                    hsc = feats['hitter_statcast']

                    if hasattr(player, 'barrel_rate') and player.barrel_rate >= hsc['barrel_rate_threshold']:
                        score *= hsc['barrel_rate_boost']

                    if hasattr(player, 'exit_velocity') and player.exit_velocity >= hsc['exit_velo_threshold']:
                        score *= hsc['exit_velo_boost']

                # xStats differential (find undervalued)
                if 'xwoba_diff' in feats and hasattr(player, 'xwoba') and hasattr(player, 'woba'):
                    xd = feats['xwoba_diff']
                    diff = player.xwoba - player.woba
                    if diff > xd['threshold']:
                        score *= xd['undervalued_boost']

                # Pitcher matchup
                if 'pitcher_quality' in feats and hasattr(player, 'opponent_pitcher_era'):
                    pq = feats['pitcher_quality']
                    if player.opponent_pitcher_era > pq.get('era_threshold', 4.2):
                        score *= pq['vs_bad_boost']
                    elif player.opponent_pitcher_era < 3.2:
                        score *= pq['vs_ace_penalty']

            else:
                # PITCHERS
                if 'pitcher_stats' in feats:
                    ps = feats['pitcher_stats']

                    # K upside
                    if hasattr(player, 'k9') and player.k9 >= ps['min_k9']:
                        score *= ps['k9_boost']

                    # Opponent K rate
                    if hasattr(player, 'opp_k_rate') and player.opp_k_rate >= ps['opp_k_threshold']:
                        score *= ps['opp_k_boost']

            return score

        def get_stacking_rules(self):
            sc = self.cfg['stack_config']
            return {
                'min_stack': min(sc['min'], 5),  # Enforce max 5
                'max_stack': min(sc['max'], 5),  # Enforce max 5
                'preferred_stack': min(sc['preferred'], 5),  # Enforce max 5
                'stack_teams': [],
                'avoid_teams': [],
                'correlation_type': self.cfg.get('correlation_type', 'any')
            }

    return EnhancedGPPStrategy(params)


def _make_enhanced_cash_strategy(params: Dict[str, Any]) -> 'BaseStrategy':
    """Build cash strategy based on historical_optimized winner"""

    class EnhancedCashStrategy(BaseStrategy):
        def __init__(self, cfg):
            super().__init__('enhanced_cash')
            self.cfg = cfg

        def score_player(self, player, slate_context=None):
            # Weight normalization
            w = self.cfg['weights']
            total = w['projection'] + w['recent'] + w['season']
            w = {k: v / total for k, v in w.items()}

            # Base scoring from historical_optimized
            if not hasattr(player, 'historical') or not player.historical:
                score = player.dk_projection
            else:
                window = self.cfg.get('recent_window', 5)
                recent = np.mean(player.historical.last_10_games[-window:]) \
                    if len(player.historical.last_10_games) >= window else player.dk_projection

                score = (player.dk_projection * w['projection'] +
                         recent * w['recent'] +
                         player.historical.season_avg * w['season'])

                # Consistency adjustment
                cons = self.cfg['consistency']
                if cons['method'] == 'std_dev':
                    score *= (0.9 + player.historical.consistency_score * cons['weight'])
                elif cons['method'] == 'floor_percentage':
                    score *= (0.9 + player.historical.floor_percentile * cons['weight'])
                else:  # both
                    score *= (0.9 + (player.historical.consistency_score +
                                     player.historical.floor_percentile) / 2 * cons['weight'])

            # Additional features
            feats = self.cfg.get('features', {})

            # Platoon splits
            if 'platoon' in feats and hasattr(player, 'platoon_advantage'):
                if player.platoon_advantage:
                    score *= feats['platoon']['advantage_boost']

            # Hot/cold streaks
            if 'streaks' in feats and hasattr(player, 'historical'):
                streak = feats['streaks']
                recent_games = player.historical.last_10_games[-streak['window']:]
                if len(recent_games) >= streak['window']:
                    recent_avg = np.mean(recent_games)
                    season_avg = player.historical.season_avg

                    if recent_avg > season_avg * 1.2:  # Hot
                        score *= streak['hot_boost']
                    elif recent_avg < season_avg * 0.8:  # Cold
                        score *= streak['cold_penalty']

            # Opponent quality
            if 'opponent' in feats and hasattr(player, 'opponent_pitcher_era'):
                opp = feats['opponent']
                if player.position != 'P':
                    # Hitters vs pitchers
                    if player.opponent_pitcher_era > 4.5:
                        score *= opp['vs_bad_boost']
                    elif player.opponent_pitcher_era < 3.2:
                        score *= opp['vs_ace_penalty']

            # Floor/ceiling balance
            if hasattr(player, 'historical'):
                floor_w = self.cfg['floor_ceiling']['floor_weight']
                ceil_w = self.cfg['floor_ceiling']['ceiling_weight']

                floor_adj = player.historical.floor_percentile * floor_w
                ceil_adj = player.historical.ceiling_percentile * ceil_w

                score *= (0.8 + floor_adj + ceil_adj)

            return score

    return EnhancedCashStrategy(params)


# =============================================================================
# OPTIMIZER CLASS WITH PARALLEL PROCESSING
# =============================================================================

class UltimateBayesianOptimizer:
    def __init__(self):
        self.cores = min(mp.cpu_count() - 1, 12)
        print(f"🖥️  Using {self.cores} CPU cores for parallel processing")
        print(f"📊 Enhanced optimizer incorporating all learnings")
        print(f"🏆 Starting from proven winning parameters")
        print(f"⚡ Max 5 batters per team stack (platform limit)")

        # Track optimization history
        self.gpp_history = []
        self.cash_history = []

    @staticmethod
    def _params_to_gpp_config(p):
        """Convert parameter array to GPP configuration dict"""
        cfg = {
            'thresholds': sorted([p['threshold_high'], p['threshold_med'], p['threshold_low']], reverse=True),
            'multipliers': sorted([p['mult_high'], p['mult_med'], p['mult_low'], p['mult_none']], reverse=True),
            'stack_config': {
                'min': int(p['stack_min']),
                'max': min(int(p['stack_max']), 5),  # Enforce limit
                'preferred': min(int(p['stack_preferred']), 5)  # Enforce limit
            },
            'batting_config': {
                'positions': list(range(1, int(p['batting_positions']) + 1)),
                'boost': float(p['batting_boost'])
            },
            'correlation_type': p.get('correlation_type', 'any'),
            'features': {}
        }

        # Add ownership features
        cfg['features']['ownership'] = {
            'low_owned_boost': float(p['ownership_low_boost']),
            'high_owned_penalty': float(p['ownership_high_penalty']),
            'threshold': int(p['ownership_threshold'])
        }

        # Add pitcher quality
        cfg['features']['pitcher_quality'] = {
            'vs_bad_boost': float(p['pitcher_bad_boost']),
            'vs_ace_penalty': float(p['pitcher_ace_penalty']),
            'era_threshold': float(p.get('era_threshold', 4.2))
        }

        # Add hitter statcast
        cfg['features']['hitter_statcast'] = {
            'barrel_rate_threshold': float(p['barrel_rate_threshold']),
            'barrel_rate_boost': float(p['barrel_rate_boost']),
            'exit_velo_threshold': float(p['exit_velo_threshold']),
            'exit_velo_boost': float(p['exit_velo_boost'])
        }

        # Add xwOBA differential
        cfg['features']['xwoba_diff'] = {
            'threshold': float(p['xwoba_diff_threshold']),
            'undervalued_boost': float(p['undervalued_boost'])
        }

        # Add pitcher stats
        cfg['features']['pitcher_stats'] = {
            'min_k9': float(p['min_k9_threshold']),
            'k9_boost': float(p['high_k9_boost']),
            'opp_k_threshold': float(p['opp_k_rate_threshold']),
            'opp_k_boost': float(p['high_opp_k_boost'])
        }

        return cfg

    @staticmethod
    def _params_to_cash_config(p):
        """Convert parameter array to cash configuration dict"""
        # Normalize weights
        w_proj = float(p['weight_projection'])
        w_rec = float(p['weight_recent'])
        w_sea = float(p['weight_season'])

        cfg = {
            'weights': {
                'projection': w_proj,
                'recent': w_rec,
                'season': w_sea
            },
            'consistency': {
                'method': str(p['consistency_method']),
                'weight': float(p['consistency_weight'])
            },
            'recent_window': int(p['recent_games_window']),
            'floor_ceiling': {
                'floor_weight': float(p['floor_weight']),
                'ceiling_weight': 1 - float(p['floor_weight'])
            },
            'features': {}
        }

        # Add optional features
        if p.get('use_platoon', 0):
            cfg['features']['platoon'] = {
                'advantage_boost': float(p['platoon_advantage_boost'])
            }

        if p.get('use_streaks', 0):
            cfg['features']['streaks'] = {
                'hot_boost': float(p['streak_hot_boost']),
                'cold_penalty': float(p['streak_cold_penalty']),
                'window': int(p['streak_window'])
            }

        if p.get('use_opponent_quality', 0):
            cfg['features']['opponent'] = {
                'vs_ace_penalty': float(p['vs_ace_penalty']),
                'vs_bad_boost': float(p['vs_bad_pitcher_boost'])
            }

        return cfg

    def optimize_gpp(self, n_calls=100):
        """Optimize GPP parameters with Bayesian optimization"""
        _banner("🎯 OPTIMIZING GPP STRATEGY")
        print(f"Starting from proven parameters (stacks_only winner - 195.7% ROI)")
        print(f"Testing {len(ENHANCED_GPP_SPACE)} parameters with {n_calls} iterations")
        print(f"Running 30 simulations per iteration ({n_calls * 30} total)")
        print("-" * 70)

        best_score = [-float('inf')]
        best_params = [None]
        iteration = [0]
        start_time = time.time()
        improvements = []

        @use_named_args(ENHANCED_GPP_SPACE)
        def objective(**params):
            iteration[0] += 1
            current_time = time.time()
            elapsed = current_time - start_time

            # Progress tracking
            if iteration[0] % 10 == 1:
                print(f"\n{'Iter':>4} | {'Score':>7} | {'Best':>7} | {'Time':>8} | {'ETA':>8} | Status")
                print("-" * 60)

            cfg = self._params_to_gpp_config(params)

            # Run parallel simulations
            with ProcessPoolExecutor(max_workers=self.cores) as ex:
                scores = list(ex.map(_run_single_gpp_enhanced, [cfg] * 30))

            avg_score = np.mean([s for s in scores if s is not None])

            # Track history
            self.gpp_history.append({
                'iteration': iteration[0],
                'score': avg_score,
                'params': params.copy()
            })

            # Calculate ETA
            rate = iteration[0] / elapsed if elapsed > 0 else 1
            remaining = (n_calls - iteration[0]) / rate
            eta = format_time(remaining)

            # Update display
            status = ""
            if avg_score > best_score[0]:
                improvement = avg_score - best_score[0]
                improvements.append(improvement)
                best_score[0], best_params[0] = avg_score, params
                status = f"🎉 +{improvement:.1f}!"

            if iteration[0] % 5 == 0 or status:
                print(f"{iteration[0]:4d} | {avg_score:6.1f} | {best_score[0]:6.1f} | "
                      f"{format_time(elapsed):>8} | {eta:>8} | {status}")

            return -avg_score

        # Run optimization with good starting point
        result = gp_minimize(
            objective,
            ENHANCED_GPP_SPACE,
            n_calls=n_calls,
            n_initial_points=15,
            x0=GPP_X0,  # Start from proven parameters
            acq_func='EI',
            random_state=42
        )

        total_time = time.time() - start_time
        print(f"\n✅ GPP Optimization complete in {format_time(total_time)}")

        best_score = -result.fun
        best_params = dict(zip([d.name for d in ENHANCED_GPP_SPACE], result.x))

        # Calculate insights
        self._analyze_gpp_results(best_params, best_score, improvements)

        return best_params, best_score

    def optimize_cash(self, n_calls=80):
        """Optimize cash game parameters"""
        _banner("💵 OPTIMIZING CASH STRATEGY")
        print(f"Starting from historical_optimized winner (82% win rate)")
        print(f"Testing {len(ENHANCED_CASH_SPACE)} parameters with {n_calls} iterations")
        print(f"Running 25 simulations per iteration ({n_calls * 25} total)")
        print("-" * 70)

        best_score = [-float('inf')]
        best_params = [None]
        iteration = [0]
        start_time = time.time()
        improvements = []

        @use_named_args(ENHANCED_CASH_SPACE)
        def objective(**params):
            iteration[0] += 1
            current_time = time.time()
            elapsed = current_time - start_time

            # Progress tracking
            if iteration[0] % 10 == 1:
                print(f"\n{'Iter':>4} | {'Score':>7} | {'Best':>7} | {'Time':>8} | {'ETA':>8} | Status")
                print("-" * 60)

            cfg = self._params_to_cash_config(params)

            # Run parallel simulations
            with ProcessPoolExecutor(max_workers=self.cores) as ex:
                scores = list(ex.map(_run_single_cash_enhanced, [cfg] * 25))

            avg_score = np.mean([s for s in scores if s is not None])

            # Track history
            self.cash_history.append({
                'iteration': iteration[0],
                'score': avg_score,
                'params': params.copy()
            })

            # Calculate ETA
            rate = iteration[0] / elapsed if elapsed > 0 else 1
            remaining = (n_calls - iteration[0]) / rate
            eta = format_time(remaining)

            # Update display
            status = ""
            if avg_score > best_score[0]:
                improvement = avg_score - best_score[0]
                improvements.append(improvement)
                best_score[0], best_params[0] = avg_score, params
                status = f"🎉 +{improvement:.1f}!"

            if iteration[0] % 5 == 0 or status:
                print(f"{iteration[0]:4d} | {avg_score:6.1f} | {best_score[0]:6.1f} | "
                      f"{format_time(elapsed):>8} | {eta:>8} | {status}")

            return -avg_score

        # Run optimization
        result = gp_minimize(
            objective,
            ENHANCED_CASH_SPACE,
            n_calls=n_calls,
            n_initial_points=12,
            x0=CASH_X0,
            acq_func='EI',
            random_state=42
        )

        total_time = time.time() - start_time
        print(f"\n✅ Cash Optimization complete in {format_time(total_time)}")

        best_score = -result.fun
        best_params = dict(zip([d.name for d in ENHANCED_CASH_SPACE], result.x))

        # Calculate insights
        self._analyze_cash_results(best_params, best_score, improvements)

        return best_params, best_score

    def _analyze_gpp_results(self, params, score, improvements):
        """Analyze and print GPP optimization insights"""
        _banner("🏆 OPTIMIZED GPP PARAMETERS & INSIGHTS")

        cfg = self._params_to_gpp_config(params)

        print(f"\n📈 Final Score: {score:.1f}")
        if score > 0:
            print("   💰 POSITIVE EXPECTED VALUE!")

        # Compare to starting point
        starting_cfg = self._params_to_gpp_config(dict(zip([d.name for d in ENHANCED_GPP_SPACE], GPP_X0)))

        print("\n🔍 KEY INSIGHTS FROM OPTIMIZATION:")

        # 1. Team total changes
        print("\n1️⃣ Team Total Thresholds (vs stacks_only winner):")
        for i, (new, old) in enumerate(zip(cfg['thresholds'], [6.0, 5.5, 5.0])):
            diff = new - old
            if abs(diff) > 0.1:
                print(f"   Threshold {i + 1}: {old:.1f} → {new:.1f} ({diff:+.1f})")
            else:
                print(f"   Threshold {i + 1}: {new:.1f} (unchanged)")

        # 2. Multiplier changes
        print("\n2️⃣ Multipliers (vs stacks_only winner):")
        for i, (new, old) in enumerate(zip(cfg['multipliers'], [1.30, 1.20, 1.10, 0.80])):
            diff = new - old
            if abs(diff) > 0.02:
                print(f"   Multiplier {i + 1}: {old:.2f} → {new:.2f} ({diff:+.2f})")
            else:
                print(f"   Multiplier {i + 1}: {new:.2f} (unchanged)")

        # 3. New features impact
        print("\n3️⃣ Additional Features Impact:")
        if cfg['features']['ownership']['low_owned_boost'] > 1.20:
            print("   ⭐ Low ownership leverage is VERY important!")
        if cfg['features']['hitter_statcast']['barrel_rate_boost'] > 1.20:
            print("   ⭐ Barrel rate is a KEY predictor!")
        if cfg['features']['xwoba_diff']['undervalued_boost'] > 1.18:
            print("   ⭐ xStats differentials find hidden value!")

        # 4. Optimization journey
        print(f"\n4️⃣ Optimization Journey:")
        print(f"   Total improvements: {len(improvements)}")
        if improvements:
            print(f"   Average improvement: {np.mean(improvements):.2f} points")
            print(f"   Biggest jump: {max(improvements):.2f} points")

        # 5. Final configuration
        print("\n5️⃣ Complete Configuration:")
        print(f"   Stack Sizes: {cfg['stack_config']['min']}-{cfg['stack_config']['max']} "
              f"(prefer {cfg['stack_config']['preferred']})")
        print(f"   Batting Order: Top {len(cfg['batting_config']['positions'])} get "
              f"{cfg['batting_config']['boost']:.2f}x boost")
        print(f"   Correlation Type: {cfg.get('correlation_type', 'any')}")

        print("\n💡 RECOMMENDATION:")
        if score > -20:
            print("   ✅ These parameters show strong potential!")
            print("   📊 Expected to outperform baseline strategies")
        else:
            print("   ⚠️  Consider running more iterations")
            print("   📊 Current parameters need refinement")

    def _analyze_cash_results(self, params, score, improvements):
        """Analyze and print cash optimization insights"""
        _banner("🏆 OPTIMIZED CASH PARAMETERS & INSIGHTS")

        cfg = self._params_to_cash_config(params)

        # Estimate win rate from score
        estimated_win_rate = min(95, max(40, 50 + (score - 50) * 0.8))

        print(f"\n📈 Final Score: {score:.1f}")
        print(f"   Estimated Win Rate: {estimated_win_rate:.1f}%")
        if estimated_win_rate > 55.6:
            print("   💰 PROFITABLE! (above 55.6% threshold)")

        print("\n🔍 KEY INSIGHTS FROM OPTIMIZATION:")

        # 1. Weight distribution
        print("\n1️⃣ Weight Distribution (vs historical_optimized):")
        w = cfg['weights']
        total = sum(w.values())
        norm_w = {k: v / total for k, v in w.items()}

        old_weights = {'projection': 0.40, 'recent': 0.35, 'season': 0.25}
        for key in ['projection', 'recent', 'season']:
            diff = norm_w[key] - old_weights[key]
            if abs(diff) > 0.05:
                print(f"   {key.capitalize()}: {old_weights[key]:.0%} → {norm_w[key]:.0%} ({diff:+.0%})")
            else:
                print(f"   {key.capitalize()}: {norm_w[key]:.0%} (unchanged)")

        # 2. Feature importance
        print("\n2️⃣ Feature Analysis:")
        active_features = []
        if 'platoon' in cfg['features']:
            active_features.append("Platoon Advantage")
        if 'streaks' in cfg['features']:
            active_features.append("Hot/Cold Streaks")
        if 'opponent' in cfg['features']:
            active_features.append("Opponent Quality")

        if active_features:
            print(f"   Active features: {', '.join(active_features)}")
        else:
            print("   No additional features improved performance")

        # 3. Consistency method
        print(f"\n3️⃣ Consistency Method: {cfg['consistency']['method']}")
        print(f"   Weight: {cfg['consistency']['weight']:.0%}")

        # 4. Optimization insights
        print(f"\n4️⃣ Optimization Journey:")
        print(f"   Total improvements: {len(improvements)}")
        if improvements:
            print(f"   Average improvement: {np.mean(improvements):.2f} points")

        print("\n💡 RECOMMENDATION:")
        if estimated_win_rate > 60:
            print("   ✅ Excellent cash game configuration!")
            print("   📊 Should be highly profitable long-term")
        elif estimated_win_rate > 55.6:
            print("   ✅ Profitable configuration")
            print("   📊 Positive expected value")
        else:
            print("   ⚠️  Near break-even - needs refinement")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("🚀 ULTIMATE BAYESIAN DFS OPTIMIZER")
    print("=" * 70)
    print("Incorporating all learnings from previous tests:")
    print("- Starting from 195.7% ROI stacks_only parameters")
    print("- Testing synergies with additional features")
    print("- Fast parallel processing on multiple cores")
    print("- Enforcing max 5 batters per team stack")
    print("=" * 70)

    optimizer = UltimateBayesianOptimizer()

    choice = input("\n1) GPP  2) Cash  3) Both → ").strip()

    start_total = time.time()

    results = {}

    if choice in ('1', '3'):
        gpp_params, gpp_score = optimizer.optimize_gpp(n_calls=100)
        results['gpp'] = {
            'parameters': _jsonify(gpp_params),
            'expected_score': gpp_score,
            'config': optimizer._params_to_gpp_config(gpp_params)
        }

        # Save GPP results
        with open('optimized_gpp_params.json', 'w') as f:
            json.dump(results['gpp'], f, indent=2)

    if choice in ('2', '3'):
        cash_params, cash_score = optimizer.optimize_cash(n_calls=80)
        results['cash'] = {
            'parameters': _jsonify(cash_params),
            'expected_score': cash_score,
            'config': optimizer._params_to_cash_config(cash_params)
        }

        # Save cash results
        with open('optimized_cash_params.json', 'w') as f:
            json.dump(results['cash'], f, indent=2)

    # Final summary
    total_runtime = time.time() - start_total
    _banner(f"🎉 OPTIMIZATION COMPLETE in {format_time(total_runtime)}")

    if 'gpp' in results:
        print(f"\n🎯 GPP Score: {results['gpp']['expected_score']:.1f}")
    if 'cash' in results:
        print(f"💵 Cash Score: {results['cash']['expected_score']:.1f}")

    print("\n💾 Results saved to JSON files")
    print("🚀 Ready to dominate DFS with optimized parameters!")


if __name__ == '__main__':
    main()