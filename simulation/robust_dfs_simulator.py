#!/usr/bin/env python3
"""
COMPLETE ROBUST DFS SIMULATOR - FINAL VERSION
============================================
Incorporates all learnings, fixes, and optimizations from our analysis.
- Truly robust strategies that always build valid lineups
- Salary optimization
- Enhanced slate generation
- Intelligent fallback logic
- Parallel processing
- Comprehensive testing

Author: DFS Optimization System
Date: 2024
"""

import numpy as np
import random
import json
import time
import os
from collections import deque
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from typing import List, Dict, Optional, Tuple, Any
import multiprocessing as mp
from typing import List, Dict, Optional, Tuple, Any
import sys
from datetime import datetime
import os


class OutputLogger:
    """Captures all print output to both console and file"""

    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()  # Ensure immediate write

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def close(self):
        self.log.close()


# ========== PROGRESS DASHBOARD FUNCTIONS ==========

def clear_screen():
    """Clear console screen - safe version"""
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except:
        # If clear fails, just print some blank lines
        print('\n' * 5)


def draw_dashboard(current_slate, total_slates, results_count, failed_count, start_time, recent_activity):
    """Draw the status dashboard"""
    # Don't clear screen, just print divider
    print("\n" + "="*40 + "\n")  # Instead of clear_screen()

    # Calculate progress
    progress = current_slate / total_slates if total_slates > 0 else 0
    progress_pct = progress * 100

    # Calculate time metrics
    elapsed = time.time() - start_time
    elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

    if current_slate > 0 and elapsed > 0:
        rate = current_slate / elapsed
        eta = (total_slates - current_slate) / rate if rate > 0 else 0
        eta_str = f"{int(eta // 60)}m {int(eta % 60)}s"
    else:
        eta_str = "calculating..."

    # Create progress bar
    bar_width = 20
    filled = int(bar_width * progress)
    bar = "█" * filled + "░" * (bar_width - filled)

    # Draw dashboard
    print("╔═══════════════════════════════════════╗")
    print("║      DFS STRATEGY TEST PROGRESS       ║")
    print("╠═══════════════════════════════════════╣")
    print(f"║ Progress:  {bar}  {progress_pct:3.0f}%   ║")
    print(f"║ Slates:    {current_slate:,} / {total_slates:,}".ljust(39) + "║")
    print(f"║ Results:   {results_count:,}".ljust(39) + "║")
    print(f"║ Time:      {elapsed_str} (ETA: {eta_str})".ljust(39) + "║")
    if failed_count > 0:
        print(f"║ ⚠️  Failed:   {failed_count}".ljust(39) + "║")

    # Add event counter summary
    if hasattr(simulate_lineup_score, 'event_counter'):
        ec = simulate_lineup_score.event_counter
        total = ec.get('total_scored', 1)
        disasters = ec.get('disasters', 0)
        breakers = ec.get('breakers', 0)

        if total > 0:
            disaster_pct = (disasters / total) * 100
            breaker_pct = (breakers / total) * 100
            print("╠═══════════════════════════════════════╣")
            print(f"║ 💥 Breakers: {breakers:,} ({breaker_pct:.1f}%)".ljust(39) + "║")
            print(f"║ 💀 Disasters: {disasters:,} ({disaster_pct:.1f}%)".ljust(39) + "║")

    print("╚═══════════════════════════════════════╝")

    # Show recent activity
    print("\nRecent activity:")
    for activity in recent_activity:
        print(activity)
    print()  # Extra line for spacing

# ========== ADAPTIVE STRATEGY INFRASTRUCTURE ==========

class SlateAnalyzer:
    """Analyzes slate characteristics for adaptive thresholds"""

    def __init__(self, players):
        self.players = players
        self._analyze()

    def _analyze(self):
        """Pre-compute all slate metrics"""
        # Ownership distribution
        ownerships = sorted([p['ownership'] for p in self.players])
        self.ownership_percentiles = {
            10: self._get_percentile(ownerships, 10),
            20: self._get_percentile(ownerships, 20),
            25: self._get_percentile(ownerships, 25),
            30: self._get_percentile(ownerships, 30),
            40: self._get_percentile(ownerships, 40),
            50: self._get_percentile(ownerships, 50),
            60: self._get_percentile(ownerships, 60),
            70: self._get_percentile(ownerships, 70),
            75: self._get_percentile(ownerships, 75),
            80: self._get_percentile(ownerships, 80),
            90: self._get_percentile(ownerships, 90)
        }

        # Value distribution
        values = sorted([p['value_score'] for p in self.players])
        self.value_percentiles = {
            25: self._get_percentile(values, 25),
            50: self._get_percentile(values, 50),
            75: self._get_percentile(values, 75),
            90: self._get_percentile(values, 90)
        }

        # Floor distribution
        floors = sorted([p['floor'] for p in self.players])
        self.floor_percentiles = {
            25: self._get_percentile(floors, 25),
            50: self._get_percentile(floors, 50),
            70: self._get_percentile(floors, 70),
            75: self._get_percentile(floors, 75),
            90: self._get_percentile(floors, 90)
        }


        # Ceiling distribution
        ceilings = sorted([p['ceiling'] for p in self.players])
        self.ceiling_percentiles = {
            25: self._get_percentile(ceilings, 25),
            40: self._get_percentile(ceilings, 40),
            50: self._get_percentile(ceilings, 50),
            60: self._get_percentile(ceilings, 60),  # ADD THIS
            70: self._get_percentile(ceilings, 70),
            75: self._get_percentile(ceilings, 75),
            80: self._get_percentile(ceilings, 80),  # ADD THIS
            90: self._get_percentile(ceilings, 90)
        }

        # Salary by position
        self.position_salary_ranges = {}
        for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
            pos_salaries = sorted([p['salary'] for p in self.players if p['position'] == pos])
            if pos_salaries:
                self.position_salary_ranges[pos] = {
                    'min': pos_salaries[0],
                    'max': pos_salaries[-1],
                    'p25': self._get_percentile(pos_salaries, 25),
                    'p50': self._get_percentile(pos_salaries, 50),
                    'p75': self._get_percentile(pos_salaries, 75)
                }

        # Team and game metrics
        self.teams = list(set(p['team'] for p in self.players))
        self.num_teams = len(self.teams)
        self.games = list(set(p.get('game_id', 0) for p in self.players))
        self.num_games = len(self.games)

        # Players per team
        self.team_player_counts = defaultdict(int)
        self.team_hitter_counts = defaultdict(int)
        for p in self.players:
            self.team_player_counts[p['team']] += 1
            if p['position'] != 'P':
                self.team_hitter_counts[p['team']] += 1

        # Average metrics
        self.avg_ownership = np.mean([p['ownership'] for p in self.players])
        self.avg_salary = np.mean([p['salary'] for p in self.players])
        self.avg_projection = np.mean([p['projection'] for p in self.players])
        self.avg_value = np.mean([p['value_score'] for p in self.players])

    def get_adaptive_thresholds(self, strategy_type):
        """Get strategy-specific adaptive thresholds"""

        if strategy_type == 'game_theory_leverage':
            # Find natural breaks in ownership distribution
            ownerships = sorted([p['ownership'] for p in self.players])

            return {
                'contrarian_threshold': np.percentile(ownerships, 25),
                'low_owned_threshold': np.percentile(ownerships, 40),
                'max_allowed': np.percentile(ownerships, 50),
                'min_ceiling': np.percentile([p['ceiling'] for p in self.players], 60),
                'min_projection': self.avg_projection * 0.75
            }

        elif strategy_type == 'balanced_optimal':
            return {
                'min_value': np.percentile([p['value_score'] for p in self.players], 30),
                'target_ownership': [self.ownership_percentiles[30], self.ownership_percentiles[70]],
                'min_floor': np.percentile([p['floor'] for p in self.players], 25),
                'correlation_bonus': 1.15
            }

        elif strategy_type == 'smart_stack':
            # Analyze stackability
            team_counts = defaultdict(int)
            for p in self.players:
                if p['position'] != 'P':
                    team_counts[p['team']] += 1

            stackable_teams = sum(1 for count in team_counts.values() if count >= 4)

            return {
                'min_stack_size': 3 if stackable_teams < 3 else 4,
                'ideal_stack_size': 5 if stackable_teams >= 2 else 4,
                'stack_salary_limit': 28000 if self.avg_salary > 4000 else 25000,
                'allow_multi_stack': stackable_teams >= 3
            }

        # Add more as needed
        return {}

    def get_position_scarcity(self):
        """Analyze position scarcity for better building"""
        scarcity = {}
        requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        for pos, req in requirements.items():
            available = sum(1 for p in self.players if p['position'] == pos)
            scarcity[pos] = req / available if available > 0 else 999

        return scarcity

    def get_correlation_opportunities(self):
        """Find correlation opportunities in slate"""
        opportunities = {
            'team_stacks': [],
            'game_stacks': [],
            'mini_stacks': []
        }

        # Team stacks
        team_hitters = defaultdict(list)
        for p in self.players:
            if p['position'] != 'P':
                team_hitters[p['team']].append(p)

        for team, hitters in team_hitters.items():
            if len(hitters) >= 5:
                opportunities['team_stacks'].append({
                    'team': team,
                    'size': len(hitters),
                    'avg_projection': np.mean([p['projection'] for p in hitters]),
                    'avg_ownership': np.mean([p['ownership'] for p in hitters])
                })

            if len(hitters) >= 2:
                opportunities['mini_stacks'].append({
                    'team': team,
                    'size': min(3, len(hitters)),
                    'players': sorted(hitters, key=lambda x: x['projection'], reverse=True)[:3]
                })

        # Game stacks
        games = defaultdict(lambda: defaultdict(list))
        for p in self.players:
            if p['position'] != 'P':
                games[p.get('game_id', 0)][p['team']].append(p)

        for game_id, teams in games.items():
            if len(teams) >= 2:
                all_hitters = []
                for team_hitters in teams.values():
                    all_hitters.extend(team_hitters)

                if len(all_hitters) >= 4:
                    opportunities['game_stacks'].append({
                        'game_id': game_id,
                        'total_hitters': len(all_hitters),
                        'avg_ownership': np.mean([p['ownership'] for p in all_hitters]),
                        'game_total': all_hitters[0].get('game_total', 8.5) if all_hitters else 8.5
                    })

        return opportunities

    def get_nearest_ownership_percentile(self, target_percentile):
        """Get the nearest available ownership percentile"""
        if target_percentile <= 10:
            return self.ownership_percentiles[10]
        elif target_percentile >= 90:
            return self.ownership_percentiles[90]

        # Find nearest available percentile
        available = [10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90]
        nearest = min(available, key=lambda x: abs(x - target_percentile))
        return self.ownership_percentiles[nearest]

    def _get_percentile(self, sorted_list, percentile):
        """Get value at percentile"""
        if not sorted_list:
            return 0
        idx = int(len(sorted_list) * percentile / 100)
        return sorted_list[min(idx, len(sorted_list) - 1)]

    def get_ownership_tier(self, ownership, tier='chalk'):
        """Get ownership tier threshold"""
        if tier == 'chalk':
            return ownership >= self.ownership_percentiles[75]
        elif tier == 'mid':
            return self.ownership_percentiles[40] <= ownership < self.ownership_percentiles[75]
        elif tier == 'low':
            return ownership < self.ownership_percentiles[40]
        elif tier == 'contrarian':
            return ownership < self.ownership_percentiles[25]
        return False

    def get_value_tier(self, value_score, tier='good'):
        """Get value tier threshold"""
        if tier == 'elite':
            return value_score >= self.value_percentiles[90]
        elif tier == 'good':
            return value_score >= self.value_percentiles[75]
        elif tier == 'above_avg':
            return value_score >= self.value_percentiles[50]
        elif tier == 'value':
            return value_score >= self.value_percentiles[25]
        return False

    def get_stack_options(self, team):
        """Get available stack sizes for a team"""
        hitter_count = self.team_hitter_counts.get(team, 0)
        options = []
        if hitter_count >= 5:
            options.append(5)
        if hitter_count >= 4:
            options.append(4)
        if hitter_count >= 3:
            options.append(3)
        if hitter_count >= 2:
            options.append(2)
        return options


# ========== BUDGET ADVISOR ==========

class BudgetAdvisor:
    """Helps strategies manage salary cap like a human would"""

    def __init__(self, players, strategy_name, scoring_function):
        self.players = players
        self.strategy_name = strategy_name
        self.scoring_function = scoring_function
        self.salary_cap = 50000
        self.analyze_strategy_intent()

    def analyze_strategy_intent(self):
        """Figure out what the strategy wants based on scoring patterns"""

        # Score sample players to detect patterns
        sample_scores = {}
        team_scores = defaultdict(list)
        position_value_bias = {}

        for p in self.players[:50]:  # Sample first 50 players
            score = self.scoring_function(p, 0)
            sample_scores[p['id']] = score
            team_scores[p['team']].append(score)

            if p['position'] not in position_value_bias:
                position_value_bias[p['position']] = []
            position_value_bias[p['position']].append(score / (p['salary'] / 1000))

        # Detect stacking intent
        team_score_variance = {}
        for team, scores in team_scores.items():
            if len(scores) >= 3:
                avg_score = np.mean(scores)
                team_score_variance[team] = avg_score

        # Find if strategy heavily favors certain teams
        if team_score_variance:
            max_team_score = max(team_score_variance.values())
            avg_team_score = np.mean(list(team_score_variance.values()))

            # If some team scores 20%+ higher than average, it's a stacking strategy
            self.wants_stack = max_team_score > avg_team_score * 1.2
            self.preferred_teams = [team for team, score in team_score_variance.items()
                                    if score > avg_team_score * 1.15]
        else:
            self.wants_stack = False
            self.preferred_teams = []

        # Detect value bias (does strategy care about salary efficiency?)
        avg_value_correlation = np.mean([np.mean(scores) for scores in position_value_bias.values()])
        self.is_value_focused = avg_value_correlation > 1.5

        # Set budget strategy based on intent
        self._determine_budget_strategy()

    def get_target_salary(self):
        """Get strategy-specific target salary"""

        # Cash strategies should maximize
        cash_strategies = [
            'value_floor', 'chalk_plus', 'matchup_optimal', 'consistency_kings',
            'form_plus_matchup', 'woba_warriors', 'k_rate_safety', 'pitcher_dominance',
            'vegas_sharp', 'park_adjusted_value', 'game_stack_cash', 'balanced_sharp',
            'projection_monster', 'platoon_stackers', 'pitcher_matchup_fade',
            'weak_pitcher_target', 'matchup_value', 'hot_players_only', 'trending_up',
            'statcast_studs'
        ]

        # GPP strategies with natural salary ranges
        gpp_salary_targets = {
            # High salary GPP (stacks need $)
            'correlation_value': 49000,
            'ceiling_stack': 49000,
            'woba_explosion': 49000,
            'iso_power_stack': 49000,
            'perfect_storm': 49000,
            'vegas_explosion': 48500,
            'rising_team_stack': 48500,

            # Medium salary GPP
            'barrel_rate_correlation': 48000,
            'matchup_leverage_stack': 48000,
            'park_factor_max': 48000,
            'multi_stack_mayhem': 48000,
            'ownership_arbitrage': 47500,

            # Lower salary GPP (contrarian/leverage)
            'contrarian_correlation': 47000,
            'cold_player_leverage': 47000,
            'narrative_fade': 47000,
            'platoon_disadvantage_gpp': 47000,
            'high_k_pitcher_fade': 47000,
            'stars_and_scrubs_extreme': 46000,  # Lowest - by design
            'pitcher_stack_combo': 47500
        }

        # Return appropriate target
        if self.strategy_name in cash_strategies:
            return 49000  # Cash always maximizes
        else:
            return gpp_salary_targets.get(self.strategy_name, 48000)

    def _determine_budget_strategy(self):
        """Set budget allocation based on detected intent"""

        if 'smart_stack' in self.strategy_name or 'ceiling_stack' in self.strategy_name:
            self.budget_strategy = 'stack_focused'
            self.budget_plan = {
                'pitchers': 14000,  # Save on pitchers
                'stack': 25000,  # Reserve for stack
                'fillers': 11000,  # Remaining positions
                'target_salary': 49000  # Use most of cap
            }

        elif 'value' in self.strategy_name or 'floor' in self.strategy_name:
            self.budget_strategy = 'balanced_value'
            self.budget_plan = {
                'avg_per_player': 4900,
                'min_player_salary': 3500,  # No punts
                'max_player_salary': 7000,  # No huge spends
                'target_salary': 49000
            }

        elif 'leverage' in self.strategy_name or 'contrarian' in self.strategy_name:
            self.budget_strategy = 'stars_and_scrubs'
            self.budget_plan = {
                'stars': 24000,  # 2-3 expensive players
                'scrubs': 9000,  # 3 min salary
                'middle': 17000,  # Rest
                'target_salary': 48000  # Can be lower
            }

        else:  # Default balanced
            self.budget_strategy = 'balanced'
            self.budget_plan = {
                'avg_per_player': 5000,
                'variance_allowed': 2000,
                'target_salary': 49500
            }

    def should_take_player(self, player, current_lineup, current_salary, remaining_spots):
        """Advise whether to take a player based on budget strategy"""

        player_salary = player['salary']
        remaining_budget = self.salary_cap - current_salary
        avg_remaining_needed = remaining_budget / remaining_spots if remaining_spots > 0 else 0

        # Always allow if it's one of the last spots
        if remaining_spots <= 2:
            return True, "filling_roster"

        if self.budget_strategy == 'stack_focused':
            # Check if this is a stack player
            is_stack_player = player['team'] in self.preferred_teams[:2]

            # How many stack players do we have?
            current_stack_size = sum(1 for p in current_lineup
                                     if p['team'] in self.preferred_teams[:2]
                                     and p['position'] != 'P')

            if is_stack_player and current_stack_size < 5:
                # Allow stack players even if expensive
                return True, "stack_player"

            # For non-stack players, be cheap
            if player['position'] == 'P' and player_salary > 7500:
                return False, "pitcher_too_expensive_for_stack"

            if not is_stack_player and player_salary > avg_remaining_needed * 1.2:
                return False, "save_for_stack"

        elif self.budget_strategy == 'balanced_value':
            # Avoid extremes
            if player_salary < self.budget_plan['min_player_salary']:
                return False, "too_cheap_for_value"
            if player_salary > self.budget_plan['max_player_salary']:
                return False, "too_expensive_for_value"

        elif self.budget_strategy == 'stars_and_scrubs':
            # Count what we have
            stars = sum(1 for p in current_lineup if p['salary'] >= 7500)
            scrubs = sum(1 for p in current_lineup if p['salary'] <= 3500)

            # Need both stars and scrubs
            if stars < 2 and player_salary >= 7500:
                return True, "need_stars"
            if scrubs < 3 and player_salary <= 3500:
                return True, "need_scrubs"
            if stars >= 3 and player_salary >= 7500:
                return False, "enough_stars"

        # General budget check
        if player_salary > avg_remaining_needed * 1.5:
            return False, "too_expensive_for_remaining_budget"

        return True, "approved"

    def get_position_budget_priority(self, remaining_positions):
        """Suggest which positions to be cheap/expensive on"""

        priority = {}

        if self.budget_strategy == 'stack_focused':
            # Be cheap on these positions to afford stack
            priority['C'] = 'cheap'  # Punt catcher
            priority['2B'] = 'cheap'  # Punt second base
            priority['P'] = 'cheap'  # Cheap pitchers

        elif self.budget_strategy == 'balanced_value':
            # Spend evenly
            for pos in remaining_positions:
                priority[pos] = 'balanced'

        else:
            # Default: be cheaper on C and one P
            priority['C'] = 'cheap'
            priority['P'] = 'mixed'  # One cheap, one decent

        return priority


def build_adaptive_lineup(players, position_requirements, scoring_function,
                          strategy_name, constraints=None):
    """Universal adaptive lineup builder - CLEAN VERSION"""

    if constraints is None:
        constraints = {}

    # Initialize Budget Advisor
    budget_advisor = BudgetAdvisor(players, strategy_name, scoring_function)

    # Get strategy-specific target salary
    target_salary = budget_advisor.get_target_salary()

    # Analyze position scarcity
    position_availability = defaultdict(list)
    for p in players:
        position_availability[p['position']].append(p)

    position_scarcity = {}
    for pos, req in position_requirements.items():
        available = len(position_availability[pos])
        if available == 0:
            return None
        position_scarcity[pos] = req / available

    scarce_positions = sorted(position_scarcity.items(), key=lambda x: x[1], reverse=True)

    # Multiple attempts with relaxing constraints
    attempts = [
        {'relaxation': 0.0, 'min_salary': target_salary - 500},
        {'relaxation': 0.1, 'min_salary': target_salary - 1000},
        {'relaxation': 0.2, 'min_salary': target_salary - 1500},
        {'relaxation': 0.3, 'min_salary': target_salary - 2000}
    ]

    for attempt_num, attempt in enumerate(attempts):
        lineup = []
        salary = 0
        teams_used = defaultdict(int)
        positions_filled = defaultdict(int)

        # Phase 1: Fill scarce positions first
        for pos, scarcity_score in scarce_positions[:3]:
            if scarcity_score < 0.3:
                break

            needed = position_requirements[pos] - positions_filled.get(pos, 0)
            if needed <= 0:
                continue

            # Score and sort candidates
            candidates = []
            for p in position_availability[pos]:
                if p not in lineup:
                    try:
                        score = scoring_function(p, attempt['relaxation'])
                        candidates.append((score, p.get('id', 0), p))
                    except:
                        continue

            candidates.sort(key=lambda x: (-x[0], x[1]))

            # Fill positions
            for score, player_id, player in candidates:
                if positions_filled.get(pos, 0) >= position_requirements[pos]:
                    break

                new_salary = salary + player['salary']
                new_team_count = teams_used.get(player['team'], 0) + 1

                remaining_spots = sum(position_requirements.values()) - len(lineup) - 1
                min_remaining = remaining_spots * 2500

                if new_salary > 50000 - min_remaining or new_team_count > 5:
                    continue

                should_take, reason = budget_advisor.should_take_player(
                    player, lineup, salary, remaining_spots + 1
                )

                if not should_take and scarcity_score < 0.5:
                    continue

                lineup.append(player)
                salary = new_salary
                teams_used[player['team']] = new_team_count
                positions_filled[pos] = positions_filled.get(pos, 0) + 1

        # Phase 2: Fill remaining positions
        scored_players = []
        for p in players:
            if p in lineup or positions_filled.get(p['position'], 0) >= position_requirements.get(p['position'], 0):
                continue

            try:
                score = scoring_function(p, attempt['relaxation'])
                scored_players.append((score, p.get('id', 0), p))
            except:
                continue

        scored_players.sort(key=lambda x: (-x[0], x[1]))

        # Build lineup
        for score, player_id, player in scored_players:
            if len(lineup) >= sum(position_requirements.values()):
                break

            if positions_filled.get(player['position'], 0) >= position_requirements.get(player['position'], 0):
                continue

            new_salary = salary + player['salary']
            new_team_count = teams_used.get(player['team'], 0) + 1

            remaining_spots = sum(position_requirements.values()) - len(lineup)

            should_take, reason = budget_advisor.should_take_player(
                player, lineup, salary, remaining_spots
            )

            if not should_take:
                continue

            min_remaining = (remaining_spots - 1) * 2500
            if new_salary > 50000 - min_remaining or new_team_count > 5:
                continue

            if budget_advisor.wants_stack and new_team_count >= 4:
                if player['team'] not in budget_advisor.preferred_teams[:2]:
                    continue

            lineup.append(player)
            salary = new_salary
            teams_used[player['team']] = new_team_count
            positions_filled[player['position']] = positions_filled.get(player['position'], 0) + 1

        # Check if complete
        if len(lineup) == sum(position_requirements.values()):
            if salary >= attempt['min_salary']:
                lineup_dict = create_lineup_dict(lineup, strategy_name)
                lineup_dict['target_salary'] = target_salary
                return optimize_salary_usage_adaptive(lineup_dict, players, strategy_name)

    # Emergency fill attempt
    lineup = []
    salary = 0
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)

    for pos, _ in scarce_positions:
        needed = position_requirements[pos]
        candidates = position_availability[pos].copy()
        candidates.sort(key=lambda x: x['projection'] / (x['salary'] / 1000), reverse=True)

        added = 0
        for player in candidates:
            if (added < needed and
                    salary + player['salary'] <= 50000 - (10 - len(lineup) - 1) * 2500 and
                    teams_used.get(player['team'], 0) < 5):

                lineup.append(player)
                salary += player['salary']
                teams_used[player['team']] += 1
                positions_filled[pos] += 1
                added += 1

                if len(lineup) == 10:
                    break

    if len(lineup) == 10:
        lineup_dict = create_lineup_dict(lineup, strategy_name)
        lineup_dict['target_salary'] = target_salary
        return lineup_dict

    return None

def build_game_theory_leverage(players):
    """SIMPLE: Low ownership + high ceiling"""
    slate = SlateAnalyzer(players)

    # Core concept: Ceiling per ownership
    def leverage_score(player, relaxation=0):
        return player['ceiling'] / (player['ownership'] + 5)

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Just build best leverage lineup
    lineup = build_adaptive_lineup(
        players,
        position_requirements,
        leverage_score,
        'game_theory_leverage'
    )

    return lineup

    def leverage_scoring(player, relaxation=0):
        # Simple leverage calculation
        base_leverage = player['ceiling'] / (player['ownership'] + 5)

        # Ownership tiers - use actual distribution
        if player['ownership'] <= slate.ownership_percentiles[25]:
            ownership_mult = 1.3
        elif player['ownership'] <= slate.ownership_percentiles[40]:
            ownership_mult = 1.2
        elif player['ownership'] <= slate.ownership_percentiles[50]:
            ownership_mult = 1.1
        elif player['ownership'] <= slate.ownership_percentiles[70]:
            ownership_mult = 0.9 + (relaxation * 0.2)
        else:
            ownership_mult = 0.7 + (relaxation * 0.4)

        # Quality check - more lenient
        if player['projection'] >= slate.avg_projection * (0.7 - relaxation * 0.2):
            quality_mult = 1.0
        else:
            quality_mult = 0.8 + (relaxation * 0.2)

        # Ceiling check - use available percentiles
        if player['ceiling'] >= slate.ceiling_percentiles[70]:
            ceiling_mult = 1.2
        elif player['ceiling'] >= slate.ceiling_percentiles[50]:
            ceiling_mult = 1.1
        else:
            ceiling_mult = 0.95 + (relaxation * 0.1)

        return base_leverage * ownership_mult * quality_mult * ceiling_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Try different approaches
    lineup = None

    # Approach 1: Low owned players only
    low_owned = [p for p in players if p['ownership'] <= slate.ownership_percentiles[40]]
    if len(low_owned) >= 25:
        lineup = build_adaptive_lineup(
            low_owned,
            position_requirements,
            leverage_scoring,
            'game_theory_leverage'
        )
        parameters_used['approach'] = 'low_owned_only'

    # Approach 2: Below average ownership
    if not lineup:
        below_avg = [p for p in players if p['ownership'] <= slate.ownership_percentiles[60]]
        if len(below_avg) >= 20:
            lineup = build_adaptive_lineup(
                below_avg,
                position_requirements,
                leverage_scoring,
                'game_theory_leverage'
            )
            parameters_used['approach'] = 'below_average_owned'

    # Approach 3: All players with penalties
    if not lineup:
        lineup = build_adaptive_lineup(
            players,
            position_requirements,
            leverage_scoring,
            'game_theory_leverage'
        )
        parameters_used['approach'] = 'all_players_scored'

    # Approach 4: Emergency fallback - just low ownership
    if not lineup:
        def simple_leverage(player, relaxation=0):
            ownership_score = 100 - player['ownership']
            ceiling_score = player['ceiling']
            return ownership_score * 0.5 + ceiling_score * 0.5

        lineup = build_adaptive_lineup(
            players,
            position_requirements,
            simple_leverage,
            'game_theory_leverage'
        )
        parameters_used['approach'] = 'emergency_simple'

    # Salary optimization
    if lineup:
        if lineup['salary'] < 48000:
            lineup = aggressive_salary_upgrade_gpp(lineup, players, 48500)

        if lineup and lineup['salary'] < 47000:
            lineup = force_expensive_swaps_gpp(lineup, players)

    # Track parameters
    if lineup:
        lineup = track_strategy_parameters(lineup, 'game_theory_leverage', parameters_used)

    return lineup


# ========== STRATEGY TRACKING AND VALIDATION ==========

STRATEGY_DEFINITIONS = {
    'balanced_optimal': {
        'description': 'Balanced approach with mini-correlations',
        'core_identity': 'Mix of value, floor, and projection with team correlation',
        'fixed_rules': [
            'Prioritize balanced scoring (proj/floor/value)',
            'Prefer 2-3 mini-stacks',
            'Target median ownership',
            'Use 96%+ of salary cap'
        ]
    },
    'value_floor': {
        'description': 'High floor approach for cash games',
        'core_identity': 'Maximize floor with value efficiency',
        'fixed_rules': [
            'Prioritize floor/salary ratio',
            'Minimum floor requirements',
            'Prefer consistent players',
            'Avoid high variance'
        ]
    },
    'smart_stack': {
        'description': 'Flexible stacking with correlation',
        'core_identity': 'Find best available stack size',
        'fixed_rules': [
            'Prioritize largest viable stack',
            'Accept 3-5 player stacks',
            'Include bring-back when possible',
            'Maintain projection upside'
        ]
    },
    'game_theory_leverage': {
        'description': 'Low ownership with ceiling',
        'core_identity': 'Find underowned upside',
        'fixed_rules': [
            'Target bottom 30-40% ownership',
            'Prioritize ceiling over floor',
            'Avoid chalk plays',
            'Aggressive salary usage'
        ]
    },
    'contrarian_correlation': {
        'description': 'Low owned game stacks',
        'core_identity': 'Correlation from overlooked games',
        'fixed_rules': [
            'Target low-owned games',
            'Minimum 3-player correlation',
            'Prioritize ceiling in stacks',
            'Game stack over team stack'
        ]
    },
    'multi_stack': {
        'description': 'Multiple mini-stacks',
        'core_identity': '2-3 different team correlations',
        'fixed_rules': [
            'Minimum 2 different team stacks',
            '2-3 players per stack',
            'Spread across games',
            'Maintain value threshold'
        ]
    }
}





def track_strategy_parameters(lineup_dict, strategy_name, parameters_used):
    """Add parameter tracking to lineup"""
    if lineup_dict:
        lineup_dict['strategy_identity'] = STRATEGY_DEFINITIONS.get(strategy_name, {})
        lineup_dict['parameters_used'] = parameters_used
        lineup_dict['adaptive_success'] = True
    return lineup_dict


def validate_strategy_identity(lineup_dict, strategy_name, slate):
    """Validate lineup matches strategy identity"""
    if not lineup_dict:
        return False, {}

    players = lineup_dict['players']

    if strategy_name == 'game_theory_leverage':
        avg_own = np.mean([p['ownership'] for p in players])
        avg_ceiling = np.mean([p['ceiling'] for p in players])

        checks = {
            'low_ownership': avg_own < slate.avg_ownership * 0.8,
            'ceiling_focused': avg_ceiling > slate.avg_projection * 1.3,
            'salary_aggressive': lineup_dict['salary'] > 47000,
            'avoided_chalk': all(p['ownership'] < slate.ownership_percentiles[60] for p in players)
        }

    elif strategy_name == 'balanced_optimal':
        team_counts = defaultdict(int)
        for p in players:
            team_counts[p['team']] += 1

        has_correlation = any(count >= 2 for count in team_counts.values())

        checks = {
            'has_correlation': has_correlation,
            'balanced_ownership': slate.ownership_percentiles[30] < np.mean([p['ownership'] for p in players]) <
                                  slate.ownership_percentiles[70],
            'good_value': np.mean([p['value_score'] for p in players]) > slate.avg_value,
            'salary_optimal': lineup_dict['salary'] > 48000
        }

    elif strategy_name == 'smart_stack':
        team_counts = defaultdict(int)
        for p in players:
            team_counts[p['team']] += 1

        max_stack = max(team_counts.values()) if team_counts else 0

        checks = {
            'has_stack': max_stack >= 3,
            'stack_quality': max_stack >= 4 or lineup_dict.get('num_games', 0) == 1,
            'maintains_value': np.mean([p['value_score'] for p in players]) > slate.avg_value * 0.9,
            'salary_usage': lineup_dict['salary'] > 47000
        }

    else:
        # Generic validation
        checks = {
            'salary_usage': lineup_dict['salary'] > 47000,
            'projection_quality': lineup_dict['projection'] > slate.avg_projection * 9.5
        }

    return all(checks.values()), checks


def optimize_salary_usage_adaptive(lineup_dict, all_players, strategy_name):
    """Strategy-aware salary optimization - CLEAN VERSION"""

    if not lineup_dict:
        return lineup_dict

    target_salary = lineup_dict.get('target_salary', 49000)
    current_salary = lineup_dict['salary']

    # Silent operation - no debug output
    if current_salary >= target_salary:
        return lineup_dict

    lineup = lineup_dict['players'].copy()

    # Strategy-specific optimization rules
    strategy_rules = {
        'balanced_optimal': {'maintain_balance': True, 'prefer_correlation': True},
        'value_floor': {'maintain_floor': True, 'prefer_value': True},
        'smart_stack': {'maintain_stack': True, 'prefer_team': True},
        'game_theory_leverage': {'maintain_low_own': True, 'prefer_ceiling': True},
        'chalk_plus': {'maintain_ownership': True, 'prefer_chalk': True},
        'correlation_value': {'maintain_correlation': True, 'prefer_value': True},
        'contrarian_correlation': {'maintain_low_own': True, 'prefer_correlation': True},
        'ceiling_stack': {'maintain_ceiling': True, 'prefer_stack': True},
        'diversified_chalk': {'maintain_diversity': True, 'prefer_chalk': True},
        'safe_correlation': {'maintain_floor': True, 'prefer_correlation': True},
        'leverage_theory': {'maintain_leverage': True, 'prefer_low_own': True},
        'multi_stack': {'maintain_stacks': True, 'prefer_correlation': True},
        'stars_and_scrubs_extreme': {'maintain_extremes': True, 'avoid_middle': True},
        'cold_player_leverage': {'maintain_cold': True, 'prefer_leverage': True},
        'narrative_fade': {'maintain_contrarian': True, 'avoid_chalk': True}
    }

    rules = strategy_rules.get(strategy_name, {})

    # For strategies that intentionally use less salary, don't force optimization
    low_salary_strategies = [
        'stars_and_scrubs_extreme', 'cold_player_leverage', 'narrative_fade',
        'contrarian_correlation', 'platoon_disadvantage_gpp', 'high_k_pitcher_fade'
    ]

    if strategy_name in low_salary_strategies and current_salary >= target_salary - 1000:
      #  print(f"DEBUG: {strategy_name} is a low-salary strategy at ${current_salary} - not forcing higher")
        return lineup_dict

    # Attempt optimization
    improved = True
    iterations = 0

    while improved and iterations < 10 and current_salary < target_salary:
        improved = False
        iterations += 1

        # Sort lineup by salary to find upgrade candidates
        lineup_copy = lineup.copy()
        lineup_copy.sort(key=lambda x: x['salary'])

        for i, current_player in enumerate(lineup_copy):
            remaining = 50000 - current_salary

            # Find upgrades
            upgrades = [
                p for p in all_players
                if p['position'] == current_player['position']
                   and p['id'] != current_player['id']
                   and p not in lineup
                   and p['salary'] > current_player['salary']
                   and p['salary'] - current_player['salary'] <= remaining
            ]

            # Apply strategy-specific filters
            valid_upgrades = []
            for upgrade in upgrades:
                valid = True

                # Check strategy rules
                if rules.get('maintain_balance'):
                    if upgrade['value_score'] < current_player['value_score'] * 0.9:
                        valid = False

                if rules.get('maintain_floor'):
                    if upgrade['floor'] < current_player['floor'] * 0.95:
                        valid = False

                if rules.get('maintain_low_own'):
                    if upgrade['ownership'] > current_player['ownership'] * 1.5:
                        valid = False

                if rules.get('maintain_ownership'):
                    if abs(upgrade['ownership'] - current_player['ownership']) > 10:
                        valid = False

                if rules.get('maintain_ceiling'):
                    if upgrade['ceiling'] < current_player['ceiling'] * 0.95:
                        valid = False

                if rules.get('maintain_cold'):
                    if upgrade.get('form_rating', 50) > 40:  # Must stay cold
                        valid = False

                if rules.get('maintain_extremes'):
                    # For stars and scrubs, avoid mid-salary
                    if 3500 < upgrade['salary'] < 4800:
                        valid = False

                if rules.get('prefer_correlation'):
                    # Bonus for same team/game
                    teams_in_lineup = set(p['team'] for p in lineup if p != current_player)
                    if upgrade['team'] in teams_in_lineup:
                        upgrade['correlation_bonus'] = 1.1
                    else:
                        upgrade['correlation_bonus'] = 1.0

                if valid and upgrade['projection'] > current_player['projection'] * 0.95:
                    valid_upgrades.append(upgrade)

            if valid_upgrades:
                # Sort by value improvement
                for upgrade in valid_upgrades:
                    upgrade['improvement'] = (
                            (upgrade['projection'] - current_player['projection']) /
                            (upgrade['salary'] - current_player['salary'] + 1)
                    )
                    if hasattr(upgrade, 'correlation_bonus'):
                        upgrade['improvement'] *= upgrade['correlation_bonus']

                valid_upgrades.sort(key=lambda x: x['improvement'], reverse=True)

                # Try best upgrade
                best_upgrade = valid_upgrades[0]

                # Validate team constraint
                test_lineup = lineup.copy()
                idx = lineup.index(current_player)
                test_lineup[idx] = best_upgrade

                teams = defaultdict(int)
                for p in test_lineup:
                    teams[p['team']] += 1

                if max(teams.values()) <= 5:
                    lineup[idx] = best_upgrade
                    current_salary = sum(p['salary'] for p in lineup)
                    improved = True
                  #  print(
                       # f"DEBUG: Upgraded {current_player['position']} from ${current_player['salary']} to ${best_upgrade['salary']}")
                    break

    # Force salary usage if still too low (only for non-low-salary strategies)
    if current_salary < target_salary - 1000 and strategy_name not in low_salary_strategies:
       # print(f"DEBUG: Force upgrading for {strategy_name}")
        lineup = force_salary_to_minimum(lineup, all_players, target_salary - 500)
        current_salary = sum(p['salary'] for p in lineup)

   # print(f"DEBUG: Final optimized salary for {strategy_name}: ${current_salary}")
    return create_lineup_dict(lineup, strategy_name)

def force_salary_to_minimum(lineup, all_players, target_salary):
    """Force lineup to reach minimum salary"""
    current_salary = sum(p['salary'] for p in lineup)

    if current_salary >= target_salary:
        return lineup

    # Sort by salary to upgrade cheapest
    lineup.sort(key=lambda x: x['salary'])

    for i in range(len(lineup)):
        if current_salary >= target_salary:
            break

        current_player = lineup[i]
        needed = target_salary - current_salary

        # Find most expensive affordable upgrade
        upgrades = [
            p for p in all_players
            if p['position'] == current_player['position']
               and p['id'] != current_player['id']
               and p not in lineup
               and current_player['salary'] < p['salary'] <= current_player['salary'] + needed
               and p['projection'] >= current_player['projection'] * 0.9  # Don't sacrifice too much
        ]

        if upgrades:
            upgrades.sort(key=lambda x: x['salary'], reverse=True)

            for upgrade in upgrades[:3]:  # Try top 3
                # Validate
                test_lineup = lineup.copy()
                test_lineup[i] = upgrade

                teams = defaultdict(int)
                for p in test_lineup:
                    teams[p['team']] += 1

                if max(teams.values()) <= 5:
                    lineup[i] = upgrade
                    current_salary = sum(p['salary'] for p in lineup)
                    break

    return lineup


# ========== CONFIGURATION ==========

CLASSIC_CONFIG = {
    'positions': {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    },
    'salary_cap': 50000,
    'roster_size': 10,
    'max_players_per_team': 5,
    'min_salary_per_player': 2500,  # DFS minimum
    'cash_payout_threshold': 0.44,  # Top 44% cash
    'gpp_payout_structure': {
        0.01: 10.0,  # Top 1% = 10x
        0.05: 5.0,  # Top 5% = 5x
        0.10: 3.0,  # Top 10% = 3x
        0.20: 2.0,  # Top 20% = 2x
        0.30: 1.5,  # Top 30% = 1.5x
        0.40: 1.2  # Top 40% = 1.2x
    }
}

SHOWDOWN_CONFIG = {
    'roster_size': 6,
    'salary_cap': 50000,
    'captain_multiplier': 1.5,
    'positions': ['CPT', 'FLEX', 'FLEX', 'FLEX', 'FLEX', 'FLEX'],
    'cash_payout_threshold': 0.44,
    'gpp_payout_structure': CLASSIC_CONFIG['gpp_payout_structure']
}

MLB_SCORING = {
    'hitters': {
        'single': 3, 'double': 5, 'triple': 8, 'home_run': 10,
        'rbi': 2, 'run': 2, 'walk': 2, 'hbp': 2, 'stolen_base': 5
    },
    'pitchers': {
        'inning': 2.25, 'out': 0.75, 'strikeout': 2,
        'win': 4, 'earned_run': -2, 'hit': -0.6,
        'walk': -0.6, 'hbp': -0.6, 'complete_game': 2.5,
        'shutout': 2.5, 'no_hitter': 5
    }
}

# Define all classic strategies
ALL_CASH_STRATEGIES = {
    'balanced_optimal': {
        'name': 'Balanced Optimal',
        'type': 'balanced_optimal',
        'description': 'Balanced approach with optimization'
    },
    'value_floor': {
        'name': 'Value Floor',
        'type': 'value_floor',
        'description': 'High floor value plays'
    },
    'chalk_plus': {
        'name': 'Chalk Plus',
        'type': 'chalk_plus',
        'description': 'Popular plays with differentiation'
    },
    'correlation_value': {
        'name': 'Correlation Value',
        'type': 'correlation_value',
        'description': 'Value-based with game correlation'
    },
    'diversified_chalk': {
        'name': 'Diversified Chalk',
        'type': 'diversified_chalk',
        'description': 'Spread ownership with game distribution'
    },
    'safe_correlation': {
        'name': 'Safe Correlation',
        'type': 'safe_correlation',
        'description': 'Mini-stacks from multiple games'
    }
}

ALL_GPP_STRATEGIES = {
    'smart_stack': {
        'name': 'Smart Stack',
        'type': 'smart_stack',
        'description': 'Flexible stacking'
    },
    'game_theory_leverage': {
        'name': 'Game Theory Leverage',
        'type': 'game_theory_leverage',
        'description': 'Low owned high upside'
    },
    'contrarian_correlation': {
        'name': 'Contrarian Correlation',
        'type': 'contrarian_correlation',
        'description': 'Low owned game stacks'
    },
    'ceiling_stack': {
        'name': 'Ceiling Stack',
        'type': 'ceiling_stack',
        'description': 'Maximum upside correlation'
    },
    'leverage_theory': {
        'name': 'Leverage Theory',
        'type': 'leverage_theory',
        'description': 'Ownership arbitrage'
    },
    'multi_stack': {
        'name': 'Multi Stack',
        'type': 'multi_stack',
        'description': 'Multiple correlated groups'
    }
}

# Now use the same strategies for all slate sizes

ROBUST_STRATEGIES = {
    'classic': {
        'small': {
            'cash': {
                # Only the NEW successful cash strategies
                'value_floor': {'name': 'Value Floor', 'type': 'value_floor', 'description': 'High floor value plays'},
                'chalk_plus': {'name': 'Chalk Plus', 'type': 'chalk_plus', 'description': 'Popular plays with differentiation'},
                'matchup_optimal': {'name': 'Matchup Optimal', 'type': 'matchup_optimal', 'description': 'Best matchups'},
                'hot_players_only': {'name': 'Hot Players Only', 'type': 'hot_players_only', 'description': 'Recent form'},
                'woba_warriors': {'name': 'wOBA Warriors', 'type': 'woba_warriors', 'description': 'Advanced metrics'},
                'vegas_sharp': {'name': 'Vegas Sharp', 'type': 'vegas_sharp', 'description': 'Game totals'},
                'balanced_sharp': {'name': 'Balanced Sharp', 'type': 'balanced_sharp', 'description': 'Mix of all factors'}
            },
            'gpp': {
                # Only the NEW successful GPP strategies
                'correlation_value': {'name': 'Correlation Value', 'type': 'correlation_value', 'description': 'Value correlation'},
                'woba_explosion': {'name': 'wOBA Explosion', 'type': 'woba_explosion', 'description': 'Stack highest wOBA team'},
                'ownership_arbitrage': {'name': 'Ownership Arbitrage', 'type': 'ownership_arbitrage', 'description': 'Low owned hot players'},
                'high_k_pitcher_fade': {'name': 'High K Fade', 'type': 'high_k_pitcher_fade', 'description': 'Stack vs strikeout pitchers'},
                'narrative_fade': {'name': 'Narrative Fade', 'type': 'narrative_fade', 'description': 'Fade the field'},
                'vegas_explosion': {'name': 'Vegas Explosion', 'type': 'vegas_explosion', 'description': '11+ totals only'}
            }
        },
        'medium': {
            'cash': {
                # Same new strategies
                'value_floor': {'name': 'Value Floor', 'type': 'value_floor', 'description': 'High floor value plays'},
                'chalk_plus': {'name': 'Chalk Plus', 'type': 'chalk_plus', 'description': 'Popular plays with differentiation'},
                'matchup_optimal': {'name': 'Matchup Optimal', 'type': 'matchup_optimal', 'description': 'Best matchups'},
                'k_rate_safety': {'name': 'K-Rate Safety', 'type': 'k_rate_safety', 'description': 'Low K% hitters'},
                'pitcher_dominance': {'name': 'Pitcher Dominance', 'type': 'pitcher_dominance', 'description': 'Elite K/BB ratio'},
                'game_stack_cash': {'name': 'Game Stack Cash', 'type': 'game_stack_cash', 'description': 'Mini correlations'}
            },
            'gpp': {
                'ceiling_stack': {'name': 'Ceiling Stack', 'type': 'ceiling_stack', 'description': 'Maximum upside'},
                'rising_team_stack': {'name': 'Rising Team Stack', 'type': 'rising_team_stack', 'description': 'Trending up teams'},
                'perfect_storm': {'name': 'Perfect Storm', 'type': 'perfect_storm', 'description': 'All factors align'},
                'stars_and_scrubs_extreme': {'name': 'Stars and Scrubs', 'type': 'stars_and_scrubs_extreme', 'description': 'Extreme salary'},
                'barrel_rate_correlation': {'name': 'Barrel Rate', 'type': 'barrel_rate_correlation', 'description': 'Quality contact'},
                'multi_stack_mayhem': {'name': 'Multi Stack', 'type': 'multi_stack_mayhem', 'description': 'Multiple correlations'}
            }
        },
        'large': {
            'cash': {
                'value_floor': {'name': 'Value Floor', 'type': 'value_floor', 'description': 'High floor value plays'},
                'projection_monster': {'name': 'Projection Monster', 'type': 'projection_monster', 'description': 'Max projections'},
                'form_plus_matchup': {'name': 'Form + Matchup', 'type': 'form_plus_matchup', 'description': 'Hot + good matchup'},
                'trending_up': {'name': 'Trending Up', 'type': 'trending_up', 'description': 'Rising players only'},
                'park_adjusted_value': {'name': 'Park Adjusted', 'type': 'park_adjusted_value', 'description': 'Park factors'},
                'platoon_stackers': {'name': 'Platoon Stackers', 'type': 'platoon_stackers', 'description': 'Platoon advantage'}
            },
            'gpp': {
                'iso_power_stack': {'name': 'ISO Power Stack', 'type': 'iso_power_stack', 'description': 'Power hitters'},
                'pitcher_stack_combo': {'name': 'Pitcher Combo', 'type': 'pitcher_stack_combo', 'description': 'Ace + opposing stack'},
                'park_factor_max': {'name': 'Park Factor Max', 'type': 'park_factor_max', 'description': 'Coors or bust'},
                'cold_player_leverage': {'name': 'Cold Leverage', 'type': 'cold_player_leverage', 'description': 'Contrarian cold'},
                'platoon_disadvantage_gpp': {'name': 'Platoon Fade', 'type': 'platoon_disadvantage_gpp', 'description': 'Fade platoons'},
                'matchup_leverage_stack': {'name': 'Matchup Leverage', 'type': 'matchup_leverage_stack', 'description': 'Stack vs worst'}
            }
        }
    },
    'showdown': {
        'cash': {
            'balanced_showdown': {'name': 'Balanced Showdown', 'type': 'balanced_showdown', 'description': 'Optimal captain'}
        },
        'gpp': {
            'leverage_captain': {'name': 'Leverage Captain', 'type': 'leverage_captain', 'description': 'Low owned captain'}
        }
    }
}

# Add to ROBUST_STRATEGIES or create a new ELITE_STRATEGIES:
ELITE_STRATEGIES = {
    'classic': {
        'small': {
            'cash': {
                'matchup_optimal': {'name': 'Matchup Optimal', 'type': 'matchup_optimal'},
                'elite_cash': {'name': 'Elite Cash', 'type': 'elite_cash'},
                'improved_chalk_plus': {'name': 'Improved Chalk Plus', 'type': 'chalk_plus'},
                'value_floor': {'name': 'Value Floor', 'type': 'value_floor'},
                'balanced_sharp': {'name': 'Balanced Sharp', 'type': 'balanced_sharp'},
                'pitcher_dominance': {'name': 'Pitcher Dominance', 'type': 'pitcher_dominance'},
                'game_stack_cash': {'name': 'Game Stack Cash', 'type': 'game_stack_cash'},
                'projection_monster': {'name': 'Projection Monster', 'type': 'projection_monster'},
            },
            'gpp': {
                'stars_and_scrubs_extreme': {'name': 'Stars and Scrubs', 'type': 'stars_and_scrubs_extreme'},
                'cold_player_leverage': {'name': 'Cold Leverage', 'type': 'cold_player_leverage'},
                'woba_explosion': {'name': 'wOBA Explosion', 'type': 'woba_explosion'},
                'rising_team_stack': {'name': 'Rising Stack', 'type': 'rising_team_stack'},
                'iso_power_stack': {'name': 'ISO Power', 'type': 'iso_power_stack'},
                'leverage_theory': {'name': 'Leverage Theory', 'type': 'leverage_theory'},
                'smart_stack': {'name': 'Smart Stack', 'type': 'smart_stack'},
                'ceiling_stack': {'name': 'Ceiling Stack', 'type': 'ceiling_stack'},
                'correlation_value': {'name': 'Correlation Value', 'type': 'correlation_value'},
                'barrel_rate_correlation': {'name': 'Barrel Rate', 'type': 'barrel_rate_correlation'},
                'multi_stack_mayhem': {'name': 'Multi Stack', 'type': 'multi_stack_mayhem'},
                'matchup_leverage_stack': {'name': 'Matchup Leverage', 'type': 'matchup_leverage_stack'},
                'pitcher_stack_combo': {'name': 'Pitcher Combo', 'type': 'pitcher_stack_combo'},
                'vegas_explosion': {'name': 'Vegas Explosion', 'type': 'vegas_explosion'},
                'high_k_pitcher_fade': {'name': 'High K Fade', 'type': 'high_k_pitcher_fade'},
            }
        },
        'medium': {
            # SAME strategies as small
            'cash': {
                'matchup_optimal': {'name': 'Matchup Optimal', 'type': 'matchup_optimal'},
                'elite_cash': {'name': 'Elite Cash', 'type': 'elite_cash'},
                'improved_chalk_plus': {'name': 'Improved Chalk Plus', 'type': 'chalk_plus'},
                'value_floor': {'name': 'Value Floor', 'type': 'value_floor'},
                'balanced_sharp': {'name': 'Balanced Sharp', 'type': 'balanced_sharp'},
                'pitcher_dominance': {'name': 'Pitcher Dominance', 'type': 'pitcher_dominance'},
                'game_stack_cash': {'name': 'Game Stack Cash', 'type': 'game_stack_cash'},
                'projection_monster': {'name': 'Projection Monster', 'type': 'projection_monster'},
            },
            'gpp': {
                'stars_and_scrubs_extreme': {'name': 'Stars and Scrubs', 'type': 'stars_and_scrubs_extreme'},
                'cold_player_leverage': {'name': 'Cold Leverage', 'type': 'cold_player_leverage'},
                'woba_explosion': {'name': 'wOBA Explosion', 'type': 'woba_explosion'},
                'rising_team_stack': {'name': 'Rising Stack', 'type': 'rising_team_stack'},
                'iso_power_stack': {'name': 'ISO Power', 'type': 'iso_power_stack'},
                'leverage_theory': {'name': 'Leverage Theory', 'type': 'leverage_theory'},
                'smart_stack': {'name': 'Smart Stack', 'type': 'smart_stack'},
                'ceiling_stack': {'name': 'Ceiling Stack', 'type': 'ceiling_stack'},
                'correlation_value': {'name': 'Correlation Value', 'type': 'correlation_value'},
                'barrel_rate_correlation': {'name': 'Barrel Rate', 'type': 'barrel_rate_correlation'},
                'multi_stack_mayhem': {'name': 'Multi Stack', 'type': 'multi_stack_mayhem'},
                'matchup_leverage_stack': {'name': 'Matchup Leverage', 'type': 'matchup_leverage_stack'},
                'pitcher_stack_combo': {'name': 'Pitcher Combo', 'type': 'pitcher_stack_combo'},
                'vegas_explosion': {'name': 'Vegas Explosion', 'type': 'vegas_explosion'},
                'high_k_pitcher_fade': {'name': 'High K Fade', 'type': 'high_k_pitcher_fade'},
            }
        },
        'large': {
            # SAME strategies as small/medium
            'cash': {
                'matchup_optimal': {'name': 'Matchup Optimal', 'type': 'matchup_optimal'},
                'elite_cash': {'name': 'Elite Cash', 'type': 'elite_cash'},
                'improved_chalk_plus': {'name': 'Improved Chalk Plus', 'type': 'chalk_plus'},
                'value_floor': {'name': 'Value Floor', 'type': 'value_floor'},
                'balanced_sharp': {'name': 'Balanced Sharp', 'type': 'balanced_sharp'},
                'pitcher_dominance': {'name': 'Pitcher Dominance', 'type': 'pitcher_dominance'},
                'game_stack_cash': {'name': 'Game Stack Cash', 'type': 'game_stack_cash'},
                'projection_monster': {'name': 'Projection Monster', 'type': 'projection_monster'},
            },
            'gpp': {
                'stars_and_scrubs_extreme': {'name': 'Stars and Scrubs', 'type': 'stars_and_scrubs_extreme'},
                'cold_player_leverage': {'name': 'Cold Leverage', 'type': 'cold_player_leverage'},
                'woba_explosion': {'name': 'wOBA Explosion', 'type': 'woba_explosion'},
                'rising_team_stack': {'name': 'Rising Stack', 'type': 'rising_team_stack'},
                'iso_power_stack': {'name': 'ISO Power', 'type': 'iso_power_stack'},
                'leverage_theory': {'name': 'Leverage Theory', 'type': 'leverage_theory'},
                'smart_stack': {'name': 'Smart Stack', 'type': 'smart_stack'},
                'ceiling_stack': {'name': 'Ceiling Stack', 'type': 'ceiling_stack'},
                'correlation_value': {'name': 'Correlation Value', 'type': 'correlation_value'},
                'barrel_rate_correlation': {'name': 'Barrel Rate', 'type': 'barrel_rate_correlation'},
                'multi_stack_mayhem': {'name': 'Multi Stack', 'type': 'multi_stack_mayhem'},
                'matchup_leverage_stack': {'name': 'Matchup Leverage', 'type': 'matchup_leverage_stack'},
                'pitcher_stack_combo': {'name': 'Pitcher Combo', 'type': 'pitcher_stack_combo'},
                'vegas_explosion': {'name': 'Vegas Explosion', 'type': 'vegas_explosion'},
                'high_k_pitcher_fade': {'name': 'High K Fade', 'type': 'high_k_pitcher_fade'},
            }
        }
    },
    'showdown': {
        'cash': {
            'balanced_showdown': {'name': 'Balanced Captain', 'type': 'balanced_showdown'}
        },
        'gpp': {
            'leverage_captain': {'name': 'Leverage Captain', 'type': 'leverage_captain'}
        }
    }
}


def run_elite_strategies_test(num_slates=500):
    """Test all promising strategies with fixed field strength"""

    # SWAP FIRST - before any counting or printing
    global ROBUST_STRATEGIES
    original_strategies = ROBUST_STRATEGIES
    ROBUST_STRATEGIES = ELITE_STRATEGIES

    try:
        print("\n" + "=" * 80)
        print("COMPREHENSIVE ELITE STRATEGIES TEST")
        print("Testing all promising strategies (40%+ cash, positive GPP)")
        print("With realistic field strength")
        print("=" * 80)

        # Count strategies - accounting for slate size structure
        cash_count = len(ELITE_STRATEGIES['classic']['small']['cash'])  # Same for all sizes
        gpp_count = len(ELITE_STRATEGIES['classic']['small']['gpp'])  # Same for all sizes
        showdown_cash = len(ELITE_STRATEGIES['showdown']['cash'])
        showdown_gpp = len(ELITE_STRATEGIES['showdown']['gpp'])

        print(f"\nTesting:")
        print(f"- {cash_count} Cash strategies (including near-winners)")
        print(f"- {gpp_count} GPP strategies (all positive ROI + unknowns)")
        print(f"- {showdown_cash + showdown_gpp} Showdown strategies")
        print(f"Total: {cash_count + gpp_count + showdown_cash + showdown_gpp} strategies")

        # Show expected improvements
        print("\nExpected improvements with realistic field:")
        print("- Cash win rates: 30% → 48-52%")
        print("- matchup_optimal: 44% → 52%+")
        print("- balanced_sharp: 44% → 51%+")

        input("\nPress Enter to start comprehensive test...")

        # Run normal simulation - it will now use ELITE_STRATEGIES
        run_simulation(num_slates, parallel=True)

    finally:
        # ALWAYS restore original strategies, even if there's an error
        ROBUST_STRATEGIES = original_strategies

def build_with_mini_correlations(players, score_metric):
    """Build lineup with 2-player mini-stacks"""
    # Find all 2-player combos from same team
    mini_stacks = []

    for i, p1 in enumerate(players):
        for j, p2 in enumerate(players[i + 1:], i + 1):
            if (p1['team'] == p2['team'] and
                    p1['position'] != p2['position'] and
                    p1['position'] != 'P' and p2['position'] != 'P'):  # Prefer hitter stacks

                combined_score = p1.get(score_metric, 0) + p2.get(score_metric, 0)
                combined_salary = p1['salary'] + p2['salary']

                if combined_salary <= 12000:  # Reasonable for 2 players
                    mini_stacks.append({
                        'players': [p1, p2],
                        'score': combined_score,
                        'salary': combined_salary,
                        'team': p1['team']
                    })

    if not mini_stacks:
        return None

    # Sort by score
    mini_stacks.sort(key=lambda x: x['score'], reverse=True)

    # Try to build with 2-3 mini stacks
    lineup_players = []
    salary = 0
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)
    used_teams = set()

    # Add best mini-stacks
    for stack in mini_stacks[:20]:  # Check top 20
        if (len(used_teams) < 3 and  # Max 3 different teams with stacks
                stack['team'] not in used_teams and
                salary + stack['salary'] <= 35000):  # Leave room for other positions

            # Check if we can add both players
            can_add = True
            for p in stack['players']:
                if teams_used.get(p['team'], 0) + 1 > 4:  # Leave room for 5th
                    can_add = False
                    break

            if can_add:
                for p in stack['players']:
                    lineup_players.append(p)
                    salary += p['salary']
                    teams_used[p['team']] += 1
                    positions_filled[p['position']] = positions_filled.get(p['position'], 0) + 1

                used_teams.add(stack['team'])

                if len(used_teams) >= 2:  # At least 2 mini-stacks
                    break

    # Complete lineup
    remaining = [p for p in players if p not in lineup_players]
    remaining.sort(key=lambda x: x.get(score_metric, 0), reverse=True)

    if complete_lineup_with_requirements(lineup_players, remaining, salary, teams_used, positions_filled):
        if len(lineup_players) == 10:
            return create_lineup_dict(lineup_players, 'mini_correlation')

    return None


def force_salary_usage(lineup_dict, all_players):
    """Force lineup to use more salary by upgrading cheapest players"""
    if not lineup_dict or lineup_dict['salary'] >= 48000:
        return lineup_dict

    lineup = lineup_dict['players'].copy()
    current_salary = lineup_dict['salary']

    # Sort by salary to find cheapest
    lineup.sort(key=lambda x: x['salary'])

    # Try to upgrade bottom 3 players
    for i in range(min(3, len(lineup))):
        current_player = lineup[i]
        remaining = 50000 - current_salary

        # Find most expensive upgrade we can afford
        upgrades = [
            p for p in all_players
            if p['position'] == current_player['position']
               and p['id'] != current_player['id']
               and p not in lineup
               and p['salary'] > current_player['salary']
               and p['salary'] - current_player['salary'] <= remaining
        ]

        if upgrades:
            # Take most expensive that improves projection
            upgrades = [u for u in upgrades if u['projection'] > current_player['projection']]
            if upgrades:
                upgrades.sort(key=lambda x: x['salary'], reverse=True)
                upgrade = upgrades[0]

                # Validate team constraint
                teams = defaultdict(int)
                for p in lineup:
                    if p != current_player:
                        teams[p['team']] += 1
                teams[upgrade['team']] += 1

                if max(teams.values()) <= 5:
                    lineup[i] = upgrade
                    current_salary = sum(p['salary'] for p in lineup)

    return create_lineup_dict(lineup, lineup_dict['strategy'])
# ========== PLAYER GENERATION ==========
def generate_player(player_id, team, position, game_data, batting_order=0):
    """Generate a realistic player with all necessary attributes INCLUDING ADVANCED STATS"""

    player = {
        'id': player_id,
        'name': f"{position}_{team}_{player_id}",
        'team': team,
        'position': position,
        'game_id': game_data['game_id'],
        'batting_order': batting_order,
        'game_total': game_data.get('game_total', 8.5)
    }

    # Position-based salary and projections (existing code)
    if position == 'P':
        pitcher_type = random.choices(
            ['ace', 'solid', 'average', 'value'],
            weights=[0.15, 0.35, 0.35, 0.15]
        )[0]

        if pitcher_type == 'ace':
            player['salary'] = random.randint(9000, 11000)
            player['projection'] = random.uniform(18, 24)
            player['ownership'] = random.uniform(25, 40)

            # ADVANCED PITCHER METRICS
            player['k_rate'] = random.uniform(26, 32)  # K% - Aces have high K rates
            player['bb_rate'] = random.uniform(5, 7)  # BB% - Aces have good control
            player['whip'] = random.uniform(0.90, 1.10)
            player['era'] = random.uniform(2.50, 3.20)
            player['gb_rate'] = random.uniform(42, 50)  # Ground ball %
            player['hr_per_9'] = random.uniform(0.7, 1.0)
            player['k_per_9'] = random.uniform(9.5, 11.5)
            player['swstr_rate'] = random.uniform(11, 14)  # Swinging strike %

        elif pitcher_type == 'solid':
            player['salary'] = random.randint(7500, 8900)
            player['projection'] = random.uniform(14, 18)
            player['ownership'] = random.uniform(15, 25)

            # ADVANCED PITCHER METRICS
            player['k_rate'] = random.uniform(21, 26)
            player['bb_rate'] = random.uniform(6, 8)
            player['whip'] = random.uniform(1.10, 1.25)
            player['era'] = random.uniform(3.20, 3.80)
            player['gb_rate'] = random.uniform(40, 48)
            player['hr_per_9'] = random.uniform(1.0, 1.3)
            player['k_per_9'] = random.uniform(8.0, 9.5)
            player['swstr_rate'] = random.uniform(9, 11)

        elif pitcher_type == 'average':
            player['salary'] = random.randint(6000, 7400)
            player['projection'] = random.uniform(10, 14)
            player['ownership'] = random.uniform(8, 15)

            # ADVANCED PITCHER METRICS
            player['k_rate'] = random.uniform(18, 21)
            player['bb_rate'] = random.uniform(7, 9)
            player['whip'] = random.uniform(1.25, 1.40)
            player['era'] = random.uniform(3.80, 4.50)
            player['gb_rate'] = random.uniform(38, 45)
            player['hr_per_9'] = random.uniform(1.2, 1.5)
            player['k_per_9'] = random.uniform(7.0, 8.0)
            player['swstr_rate'] = random.uniform(8, 10)

        else:  # value
            player['salary'] = random.randint(4500, 5900)
            player['projection'] = random.uniform(6, 10)
            player['ownership'] = random.uniform(3, 10)

            # ADVANCED PITCHER METRICS
            player['k_rate'] = random.uniform(15, 19)
            player['bb_rate'] = random.uniform(8, 11)
            player['whip'] = random.uniform(1.35, 1.55)
            player['era'] = random.uniform(4.20, 5.20)
            player['gb_rate'] = random.uniform(35, 42)
            player['hr_per_9'] = random.uniform(1.4, 1.8)
            player['k_per_9'] = random.uniform(6.0, 7.5)
            player['swstr_rate'] = random.uniform(7, 9)

        # L/R SPLITS for pitchers
        if random.random() < 0.7:  # 70% are righties
            player['throws'] = 'R'
            player['vs_l_woba'] = player['whip'] * 0.29 + random.uniform(-0.02, 0.02)
            player['vs_r_woba'] = player['whip'] * 0.31 + random.uniform(-0.02, 0.02)
        else:
            player['throws'] = 'L'
            player['vs_l_woba'] = player['whip'] * 0.31 + random.uniform(-0.02, 0.02)
            player['vs_r_woba'] = player['whip'] * 0.28 + random.uniform(-0.02, 0.02)

    else:  # HITTERS
        # Batting order influences hitter quality
        if batting_order in [1, 2, 3, 4]:
            player['salary'] = random.randint(4200, 5800)
            player['projection'] = random.uniform(9, 13)
            player['ownership'] = random.uniform(15, 35)

            # ADVANCED HITTER METRICS
            player['woba'] = random.uniform(.340, .380)  # Weighted on-base average
            player['iso'] = random.uniform(.180, .250)  # Isolated power
            player['babip'] = random.uniform(.290, .320)  # Batting avg on balls in play
            player['k_rate'] = random.uniform(18, 22)  # Strikeout rate
            player['bb_rate'] = random.uniform(8, 12)  # Walk rate
            player['hr_per_ab'] = random.uniform(.040, .060)  # Home run rate
            player['sb_rate'] = random.uniform(0.10, 0.25) if batting_order <= 2 else random.uniform(0.05, 0.15)
            player['hard_hit_rate'] = random.uniform(38, 45)  # Statcast hard hit %
            player['barrel_rate'] = random.uniform(7, 11)  # Statcast barrel %
            player['xwoba'] = player['woba'] + random.uniform(-0.015, 0.015)  # Expected wOBA

        elif batting_order in [5, 6]:
            player['salary'] = random.randint(3500, 4200)
            player['projection'] = random.uniform(7, 10)
            player['ownership'] = random.uniform(10, 20)

            # ADVANCED HITTER METRICS
            player['woba'] = random.uniform(.315, .340)
            player['iso'] = random.uniform(.150, .190)
            player['babip'] = random.uniform(.280, .310)
            player['k_rate'] = random.uniform(20, 25)
            player['bb_rate'] = random.uniform(6, 10)
            player['hr_per_ab'] = random.uniform(.030, .045)
            player['sb_rate'] = random.uniform(0.05, 0.12)
            player['hard_hit_rate'] = random.uniform(34, 40)
            player['barrel_rate'] = random.uniform(5, 8)
            player['xwoba'] = player['woba'] + random.uniform(-0.015, 0.015)

        else:  # 7-9 hitters
            player['salary'] = random.randint(2800, 3500)
            player['projection'] = random.uniform(5, 8)
            player['ownership'] = random.uniform(5, 15)

            # ADVANCED HITTER METRICS
            player['woba'] = random.uniform(.280, .315)
            player['iso'] = random.uniform(.100, .150)
            player['babip'] = random.uniform(.270, .300)
            player['k_rate'] = random.uniform(22, 28)
            player['bb_rate'] = random.uniform(5, 8)
            player['hr_per_ab'] = random.uniform(.020, .035)
            player['sb_rate'] = random.uniform(0.02, 0.08)
            player['hard_hit_rate'] = random.uniform(30, 36)
            player['barrel_rate'] = random.uniform(3, 6)
            player['xwoba'] = player['woba'] + random.uniform(-0.015, 0.015)

        # BATTER HANDEDNESS
        if random.random() < 0.7:  # 70% are righties
            player['bats'] = 'R'
        else:
            player['bats'] = 'L'

        # RECENT FORM (last 7/14/30 days)
        # Hot/cold streaks
        form_modifier = random.choice([0.8, 0.9, 1.0, 1.1, 1.2])  # Cold to hot
        player['last_7_woba'] = player['woba'] * form_modifier
        player['last_14_woba'] = player['woba'] * (form_modifier * 0.9 + 0.1)  # Regress slightly
        player['last_30_woba'] = player['woba'] * (form_modifier * 0.8 + 0.2)  # Regress more

        # Recent power surge/slump
        power_trend = random.choice([0.7, 0.85, 1.0, 1.15, 1.3])
        player['last_7_iso'] = player['iso'] * power_trend
        player['last_14_iso'] = player['iso'] * (power_trend * 0.85 + 0.15)

    # Add matchup data
    if position != 'P':
        # Store opposing pitcher info (would be set during matchup phase)
        player['opp_pitcher_hand'] = 'R'  # Placeholder
        player['vs_hand_woba'] = player['woba'] + random.uniform(-0.030, 0.030)  # Platoon splits

    # Game total influence (existing code)
    if game_data.get('game_total', 8.5) > 9.5:
        player['projection'] *= random.uniform(1.05, 1.15)
        player['ownership'] *= 1.1
    elif game_data.get('game_total', 8.5) < 7.5:
        player['projection'] *= random.uniform(0.85, 0.95)
        player['ownership'] *= 0.9

    # Calculate derived metrics (existing)
    player['value_score'] = player['projection'] / (player['salary'] / 1000)
    player['floor'] = player['projection'] * random.uniform(0.4, 0.7)
    player['ceiling'] = player['projection'] * random.uniform(1.5, 2.5)

    # Special attributes for strategy calculations
    player['floor_score'] = player['floor'] / (player['salary'] / 1000)
    player['ceiling_score'] = player['ceiling'] / (player['salary'] / 1000)
    player['ownership_value'] = player['projection'] / (player['ownership'] + 5)

    # Add advanced metric scores
    if position == 'P':
        player['k_upside'] = player['k_rate'] / 20 * player['projection']  # K-rate adjusted projection
        player['safety_score'] = (50 - player['whip'] * 30) * (player['k_rate'] / 25)
    else:
        player['upside_score'] = player['iso'] * player['hard_hit_rate'] / 10
        player['consistency_score'] = player['woba'] * 100 * (1 - player['k_rate'] / 100)

    return player


def generate_slate(slate_id, format_type='classic', slate_size='small'):
    """Generate a realistic DFS slate with matchups and recent performance"""

    # Set random seed for reproducibility
    random.seed(slate_id)
    np.random.seed(slate_id)

    # Determine number of games
    if format_type == 'showdown':
        num_games = 1
    else:
        num_games = {'small': 3, 'medium': 7, 'large': 12}[slate_size]

    # Team pool
    all_teams = [
        'NYY', 'BOS', 'LAD', 'SF', 'CHC', 'STL', 'ATL', 'PHI',
        'HOU', 'OAK', 'SEA', 'TEX', 'MIN', 'CLE', 'TB', 'TOR',
        'MIA', 'NYM', 'WAS', 'SD', 'COL', 'ARI', 'MIL', 'CIN',
        'DET', 'KC', 'CWS', 'BAL', 'LAA', 'PIT'
    ]

    # Shuffle and select teams
    random.shuffle(all_teams)
    teams = all_teams[:num_games * 2]

    # Generate games
    games = []
    for i in range(num_games):
        home_team = teams[i * 2]
        away_team = teams[i * 2 + 1]

        # Realistic game total distribution
        base_total = np.random.normal(8.5, 1.2)
        game_total = np.clip(base_total, 6.0, 13.0)

        games.append({
            'game_id': i,
            'home_team': home_team,
            'away_team': away_team,
            'game_total': round(game_total, 1)
        })

    # Generate EXACTLY the confirmed starting lineup for each team
    players = []
    player_id = 0
    pitchers_by_team = {}  # Track pitchers for matchup assignment

    # First pass: Generate all players
    for game in games:
        for team in [game['home_team'], game['away_team']]:
            # STARTING PITCHER (1 per team)
            pitcher = generate_player(player_id, team, 'P', game, batting_order=0)

            # Store pitcher for matchup assignment
            pitchers_by_team[team] = pitcher

            players.append(pitcher)
            player_id += 1

            # STARTING LINEUP (exactly 9 hitters)
            # Realistic MLB batting order with DFS-compatible positions
            lineup_positions = [
                ('SS', 1),  # Leadoff - often speedy SS or CF
                ('2B', 2),  # 2-hole - contact hitter
                ('OF', 3),  # 3-hole - best hitter (often CF)
                ('1B', 4),  # Cleanup - power hitter
                ('3B', 5),  # 5-hole - RBI guy
                ('OF', 6),  # 6-hole - RF
                ('C', 7),  # 7-hole - catcher
                ('OF', 8),  # 8-hole - LF
                ('OF', 9)  # 9-hole - 4th OF or utility
            ]

            # Alternative: More variety in lineup construction
            if random.random() < 0.3:  # 30% chance of alternate lineup
                lineup_positions = [
                    ('OF', 1),  # Leadoff CF
                    ('SS', 2),  # 2-hole
                    ('1B', 3),  # 3-hole - 1B hitting third
                    ('OF', 4),  # Cleanup - Power OF
                    ('3B', 5),  # 5-hole
                    ('2B', 6),  # 6-hole
                    ('C', 7),  # 7-hole
                    ('OF', 8),  # 8-hole
                    ('1B', 9)  # 9-hole - backup 1B (platoon)
                ]

            # Generate each hitter
            for pos, batting_order in lineup_positions:
                player = generate_player(player_id, team, pos, game, batting_order)
                players.append(player)
                player_id += 1

    # Second pass: Assign matchups and recent performance
    for player in players:
        # MATCHUP ASSIGNMENT
        if player['position'] != 'P':  # For all hitters
            # Find opposing pitcher
            game_id = player['game_id']
            player_team = player['team']

            # Find the opposing team in this game
            game = games[game_id]
            if player_team == game['home_team']:
                opp_team = game['away_team']
            else:
                opp_team = game['home_team']

            # Assign opposing pitcher data
            opp_pitcher = pitchers_by_team[opp_team]
            player['opp_pitcher_id'] = opp_pitcher['id']
            player['opp_pitcher_hand'] = opp_pitcher['throws']
            player['opp_pitcher_k_rate'] = opp_pitcher['k_rate']
            player['opp_pitcher_whip'] = opp_pitcher['whip']
            player['opp_pitcher_era'] = opp_pitcher['era']

            # Calculate platoon advantage/disadvantage
            if player['bats'] == 'L' and opp_pitcher['throws'] == 'L':
                player['platoon_advantage'] = -0.030  # Lefty vs Lefty (bad)
            elif player['bats'] == 'R' and opp_pitcher['throws'] == 'R':
                player['platoon_advantage'] = -0.015  # Righty vs Righty (slightly bad)
            elif player['bats'] == 'L' and opp_pitcher['throws'] == 'R':
                player['platoon_advantage'] = 0.020  # Lefty vs Righty (good)
            else:  # R vs L
                player['platoon_advantage'] = 0.025  # Righty vs Lefty (good)

            # Adjust projection based on matchup
            matchup_factor = 1.0

            # Facing high K pitcher
            if opp_pitcher['k_rate'] > 26:
                matchup_factor *= 0.92  # Tough matchup
            elif opp_pitcher['k_rate'] < 18:
                matchup_factor *= 1.08  # Good matchup

            # Apply platoon advantage
            matchup_factor *= (1 + player['platoon_advantage'])

            # Update projection
            player['matchup_projection'] = player['projection'] * matchup_factor

        # RECENT PERFORMANCE DATA (Last 5 games)
        player['last_5_scores'] = []

        if player['position'] == 'P':
            # Generate pitcher's last 5 fantasy scores
            base_avg = player['projection']
            for i in range(5):
                # Simulate variance in pitcher performance
                game_score = base_avg * random.uniform(0.3, 1.8)
                player['last_5_scores'].append(round(game_score, 1))
        else:
            # Generate hitter's last 5 fantasy scores
            base_avg = player['projection']
            for i in range(5):
                # Hitters have less variance than pitchers
                game_score = base_avg * random.uniform(0.2, 2.0)
                player['last_5_scores'].append(round(game_score, 1))

        # Calculate recent performance metrics
        recent_avg = np.mean(player['last_5_scores'])
        player['recent_avg'] = recent_avg

        # Determine hot/cold status
        if recent_avg > player['projection'] * 1.15:
            player['recent_form'] = 'hot'
            player['form_rating'] = min(100, (recent_avg / player['projection'] - 1) * 200 + 50)
        elif recent_avg < player['projection'] * 0.85:
            player['recent_form'] = 'cold'
            player['form_rating'] = max(0, 50 - (1 - recent_avg / player['projection']) * 200)
        else:
            player['recent_form'] = 'neutral'
            player['form_rating'] = 50

        # Calculate consistency score (lower std dev = more consistent)
        player['consistency'] = 100 - min(100, np.std(player['last_5_scores']) * 10)

        # Additional recent trend
        if len(player['last_5_scores']) >= 3:
            # Compare last 2 games vs previous 3
            recent_2 = np.mean(player['last_5_scores'][:2])
            previous_3 = np.mean(player['last_5_scores'][2:])

            if recent_2 > previous_3 * 1.2:
                player['trend'] = 'rising'
            elif recent_2 < previous_3 * 0.8:
                player['trend'] = 'falling'
            else:
                player['trend'] = 'stable'

    # Third pass: Add park factors based on game location
    # (Simple implementation - you could expand this with real park data)
    park_factors = {
        'COL': 1.15,  # Coors Field
        'BOS': 1.08,  # Fenway
        'NYY': 1.05,  # Yankee Stadium
        'CIN': 1.05,  # Great American
        'TEX': 1.04,  # Globe Life
        'SF': 0.95,  # Oracle Park
        'SD': 0.93,  # Petco
        'SEA': 0.92,  # T-Mobile
        'MIA': 0.91,  # loanDepot
        'NYM': 0.98,  # Citi Field
        # Default for others
    }

    for player in players:
        game = games[player['game_id']]
        home_team = game['home_team']

        # Get park factor (default to 1.0 if not specified)
        park_factor = park_factors.get(home_team, 1.0)
        player['park_factor'] = park_factor

        # Adjust projections for park
        if player['position'] == 'P':
            # Pitchers benefit from pitcher parks
            player['park_adjusted_projection'] = player['projection'] * (2 - park_factor)
        else:
            # Hitters benefit from hitter parks
            player['park_adjusted_projection'] = player['projection'] * park_factor

    # Verify we have exactly 10 players per team
    team_counts = defaultdict(int)
    position_counts = defaultdict(lambda: defaultdict(int))

    for p in players:
        team_counts[p['team']] += 1
        position_counts[p['team']][p['position']] += 1

#    print(f"\nDEBUG: Slate generation complete")
    #print(f"Total players: {len(players)}")
   # print(f"Players per team: {dict(team_counts)}")

    # Validate each team has correct positions
    for team in teams:
        if team_counts[team] != 10:
            print(f"WARNING: {team} has {team_counts[team]} players instead of 10!")

        # Check position distribution
        team_positions = dict(position_counts[team])
    #    print(f"{team} positions: {team_positions}")

    # Summary of position availability across slate
    total_by_position = defaultdict(int)
    hot_players_count = 0
    cold_players_count = 0

    for p in players:
        total_by_position[p['position']] += 1
        if p.get('recent_form') == 'hot':
            hot_players_count += 1
        elif p.get('recent_form') == 'cold':
            cold_players_count += 1

    # print(f"\nTotal players by position across slate:")
    # for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
    #     print(f"  {pos}: {total_by_position.get(pos, 0)}")

  #  print(f"\nRecent form distribution:")
  #  print(f"  Hot: {hot_players_count} players")
   # print(f"  Cold: {cold_players_count} players")
   # print(f"  Neutral: {len(players) - hot_players_count - cold_players_count} players")

    return {
        'slate_id': slate_id,
        'format': format_type,
        'slate_size': slate_size,
        'num_games': num_games,
        'players': players,
        'games': games,
        'teams': teams
    }
# ========== LINEUP UTILITIES ==========

def create_lineup_dict(players_list, strategy_name):
    """Convert player list to lineup dictionary with all metrics"""
    if not players_list:
        return None

    # Calculate team stacks
    team_counts = defaultdict(int)
    game_counts = defaultdict(int)

    for p in players_list:
        team_counts[p['team']] += 1
        if 'game_id' in p:
            game_counts[p['game_id']] += 1

    max_stack = max(team_counts.values()) if team_counts else 0

    return {
        'players': players_list,
        'salary': sum(p['salary'] for p in players_list),
        'projection': sum(p['projection'] for p in players_list),
        'ownership': np.mean([p['ownership'] for p in players_list]),
        'strategy': strategy_name,
        'ceiling': sum(p['ceiling'] for p in players_list),
        'floor': sum(p['floor'] for p in players_list),
        'max_stack': max_stack,
        'num_games': len(set(p.get('game_id', 0) for p in players_list)),
        'team_distribution': dict(team_counts),
        'game_distribution': dict(game_counts)
    }


def validate_lineup(lineup):
    """Check if lineup meets all DFS requirements"""
    if len(lineup) != 10:
        return False

    positions = defaultdict(int)
    teams = defaultdict(int)
    salary = 0

    for p in lineup:
        positions[p['position']] += 1
        teams[p['team']] += 1
        salary += p['salary']

    # Check all requirements
    if salary > 50000:
        return False
    if positions['P'] != 2:
        return False
    if positions['C'] != 1:
        return False
    if positions['1B'] != 1:
        return False
    if positions['2B'] != 1:
        return False
    if positions['3B'] != 1:
        return False
    if positions['SS'] != 1:
        return False
    if positions['OF'] != 3:
        return False
    if max(teams.values()) > 5:
        return False

    return True


def optimize_salary_usage(lineup_dict, all_players, strategy_type):
    """Optimize salary usage without breaking strategy integrity"""
    if not lineup_dict:
        return lineup_dict

    lineup = lineup_dict['players'].copy()
    current_salary = lineup_dict['salary']

    # If already well-optimized, return
    if current_salary >= 48000:  # Changed from 49500 to 48000
        return lineup_dict

    remaining_salary = 50000 - current_salary

    # Strategies that shouldn't be optimized
    no_optimize_strategies = [
        'smart_stack', 'contrarian_correlation', 'leverage_theory',
        'leverage_captain', 'game_theory_leverage'
    ]

    if strategy_type in no_optimize_strategies:
        return lineup_dict

    # Try to upgrade each position
    improved = True
    iterations = 0
    max_iterations = 10

    while improved and iterations < max_iterations and current_salary < 48000:
        improved = False
        iterations += 1

        for i, current_player in enumerate(lineup):
            # Find upgrade candidates
            upgrade_candidates = [
                p for p in all_players
                if p['position'] == current_player['position']
                   and p['id'] != current_player['id']  # Use ID instead of object comparison
                   and p not in lineup
                   and p['salary'] > current_player['salary']
                   and p['salary'] - current_player['salary'] <= remaining_salary
                   and p['projection'] > current_player['projection']  # Must improve projection
            ]

            if upgrade_candidates:
                # Apply strategy-specific filters
                if 'value' in strategy_type or 'floor' in strategy_type:
                    upgrade_candidates = [
                        p for p in upgrade_candidates
                        if p.get('value_score', 0) >= current_player.get('value_score', 0) * 0.9
                    ]

                if 'ceiling' in strategy_type:
                    upgrade_candidates = [
                        p for p in upgrade_candidates
                        if p.get('ceiling', 0) >= current_player.get('ceiling', 0) * 0.95
                    ]

                if 'chalk' in strategy_type:
                    upgrade_candidates = [
                        p for p in upgrade_candidates
                        if p.get('ownership', 0) >= 15
                    ]

                if 'correlation' in strategy_type:
                    # Prefer players from same games/teams already in lineup
                    game_ids = set(p.get('game_id') for p in lineup if 'game_id' in p)
                    team_names = set(p['team'] for p in lineup)

                    correlated = [p for p in upgrade_candidates
                                  if p.get('game_id') in game_ids or p['team'] in team_names]
                    if correlated:
                        upgrade_candidates = correlated

                if upgrade_candidates:
                    # Sort by projection gain per dollar
                    for candidate in upgrade_candidates:
                        salary_diff = candidate['salary'] - current_player['salary']
                        proj_diff = candidate['projection'] - current_player['projection']
                        if salary_diff > 0:
                            candidate['upgrade_efficiency'] = proj_diff / salary_diff
                        else:
                            candidate['upgrade_efficiency'] = 0

                    upgrade_candidates.sort(key=lambda x: x['upgrade_efficiency'], reverse=True)

                    # Try best upgrade
                    for upgrade in upgrade_candidates[:3]:  # Try top 3 candidates
                        # Validate swap
                        test_lineup = lineup.copy()
                        test_lineup[i] = upgrade
                        test_salary = sum(p['salary'] for p in test_lineup)

                        if test_salary <= 50000:
                            # Check team exposure
                            teams = defaultdict(int)
                            for p in test_lineup:
                                teams[p['team']] += 1

                            if max(teams.values()) <= 5:
                                # This is an improvement
                                lineup = test_lineup.copy()
                                current_salary = test_salary
                                remaining_salary = 50000 - current_salary
                                improved = True
                                break

    # Final push to use remaining salary
    if current_salary < 48000:
        # Try to swap lowest salary player with higher one
        lineup.sort(key=lambda x: x['salary'])

        for i in range(min(3, len(lineup))):  # Try upgrading 3 cheapest players
            current_player = lineup[i]
            remaining = 50000 - current_salary

            final_upgrades = [
                p for p in all_players
                if p['position'] == current_player['position']
                   and p['id'] != current_player['id']
                   and p not in lineup
                   and current_player['salary'] < p['salary'] <= current_player['salary'] + remaining
                   and p['projection'] > current_player['projection']
            ]

            if final_upgrades:
                final_upgrades.sort(key=lambda x: x['projection'], reverse=True)
                upgrade = final_upgrades[0]

                # Validate
                test_lineup = lineup.copy()
                test_lineup[i] = upgrade
                test_salary = sum(p['salary'] for p in test_lineup)

                teams = defaultdict(int)
                for p in test_lineup:
                    teams[p['team']] += 1

                if test_salary <= 50000 and max(teams.values()) <= 5:
                    lineup = test_lineup
                    current_salary = test_salary

    return create_lineup_dict(lineup, strategy_type)

# ========== STRATEGY BUILDERS WITH ROBUST FALLBACKS ==========

def build_balanced_optimal(players):
    """EMERGENCY SIMPLE VERSION"""
    # Just take best value at each position
    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Sort by balanced metric
    for p in players:
        p['balanced_score'] = (
                p['projection'] * 0.4 +
                p['floor'] * 0.3 +
                p['value_score'] * 3 * 0.3
        )

    players_sorted = sorted(players, key=lambda x: x['balanced_score'], reverse=True)

    # Greedy fill
    for player in players_sorted:
        if (positions_filled.get(player['position'], 0) < position_requirements.get(player['position'], 0) and
                salary + player['salary'] <= 50000 - (10 - len(lineup) - 1) * 2500 and
                teams_used.get(player['team'], 0) < 5):

            lineup.append(player)
            salary += player['salary']
            positions_filled[player['position']] += 1
            teams_used[player['team']] += 1

            if len(lineup) == 10:
                return create_lineup_dict(lineup, 'balanced_optimal')

    return None


def build_value_floor(players):
    """High floor approach with adaptive thresholds"""
    slate = SlateAnalyzer(players)

    # Adaptive floor thresholds based on slate
    floor_distribution = sorted([p['floor'] for p in players])

    parameters_used = {
        'slate_avg_floor': np.mean(floor_distribution),
        'floor_p50': slate.floor_percentiles[50],
        'floor_p75': slate.floor_percentiles[75]
    }

    def adaptive_floor_scoring(player, relaxation=0):
        # Dynamic floor threshold
        min_floor = slate.floor_percentiles[50] * (1 - relaxation * 0.3)

        # Penalty for low floor
        if player['floor'] < min_floor:
            floor_penalty = 1 - (min_floor - player['floor']) / min_floor
            floor_penalty = max(0.3, floor_penalty)
        else:
            floor_penalty = 1.0

        # Core scoring
        floor_per_dollar = player['floor'] / (player['salary'] / 1000)
        floor_reliability = player['floor'] / player['projection'] if player['projection'] > 0 else 0.5

        # Adaptive weights based on slate
        if slate.avg_projection > 10:  # High scoring slate
            reliability_weight = 0.4
            floor_weight = 0.4
            value_weight = 0.2
        else:  # Low scoring slate
            reliability_weight = 0.3
            floor_weight = 0.5
            value_weight = 0.2

        score = (
                        floor_per_dollar * floor_weight +
                        floor_reliability * reliability_weight +
                        player['value_score'] * value_weight
                ) * floor_penalty

        return score

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Position-specific floor requirements
    position_floor_targets = {}
    for pos in position_requirements:
        pos_players = [p for p in players if p['position'] == pos]
        if pos_players:
            pos_floors = sorted([p['floor'] for p in pos_players])
            # Target 60th percentile floor for each position
            position_floor_targets[pos] = pos_floors[int(len(pos_floors) * 0.6)]

    parameters_used['position_floor_targets'] = position_floor_targets

    # Build with graduated attempts
    lineup = None

    # First attempt: Strict floor requirements
    high_floor_pool = [p for p in players if p['floor'] >= slate.floor_percentiles[50]]

    if len(high_floor_pool) >= 20:
        lineup = build_adaptive_lineup(
            high_floor_pool,
            position_requirements,
            adaptive_floor_scoring,
            'value_floor'
        )
        parameters_used['approach'] = 'high_floor_pool'

    # Second attempt: Relaxed requirements
    if not lineup:
        lineup = build_adaptive_lineup(
            players,
            position_requirements,
            adaptive_floor_scoring,
            'value_floor'
        )
        parameters_used['approach'] = 'full_pool_adaptive'

    # Ensure good salary usage
    if lineup and lineup['salary'] < 48000:
        lineup = optimize_salary_usage_adaptive(lineup, players, 'value_floor')

    # Track and validate
    if lineup:
        lineup = track_strategy_parameters(lineup, 'value_floor', parameters_used)

    return lineup

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Adaptive constraints based on slate
    constraints = {
        'min_floor': slate.floor_percentiles[50],
        'min_value': slate.value_percentiles[25]
    }

    return build_adaptive_lineup(
        players,
        position_requirements,
        floor_scoring,
        'value_floor',
        constraints
    )


def build_smart_stack(players):
    """SIMPLE: Find biggest stack possible - MORE FLEXIBLE VERSION"""
    if not players:
        return None

    slate = SlateAnalyzer(players)

    # Find teams with most players
    team_counts = defaultdict(int)
    team_players = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_counts[p['team']] += 1
            team_players[p['team']].append(p)

    # Check if we have any teams
    if not team_counts:
        print("DEBUG: smart_stack - No hitters found")
        return None

    # Get top 3 teams by player count
    sorted_teams = sorted(team_counts.items(), key=lambda x: x[1], reverse=True)
    top_teams = [team for team, count in sorted_teams[:3]]

    #print(f"DEBUG: smart_stack - Top teams: {sorted_teams[:3]}")

    # Build lineup with stack emphasis but not exclusive
    def stack_score(player, relaxation=0):
        # Base score
        base = player['projection']

        # Team bonuses (decreasing by relaxation)
        if player['team'] == top_teams[0]:
            team_mult = 1.5 - (relaxation * 0.3)  # 1.5 -> 1.2
        elif len(top_teams) > 1 and player['team'] == top_teams[1]:
            team_mult = 1.3 - (relaxation * 0.2)  # 1.3 -> 1.1
        elif len(top_teams) > 2 and player['team'] == top_teams[2]:
            team_mult = 1.2 - (relaxation * 0.1)  # 1.2 -> 1.1
        else:
            team_mult = 1.0 + (relaxation * 0.1)  # 1.0 -> 1.3

        return base * team_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    lineup = build_adaptive_lineup(
        players,
        position_requirements,
        stack_score,
        'smart_stack'
    )

    return lineup


def build_chalk_plus(players):
    """Popular plays with MORE CHALK - FIXED VERSION"""

    def chalk_scoring(player, relaxation=0):
        ownership = player.get('ownership', 15)

        # NEW: More aggressive chalk preference
        if ownership >= 35:
            ownership_mult = 1.5  # Love the mega-chalk
        elif ownership >= 25:
            ownership_mult = 1.3  # Like high owned
        elif ownership >= 20:
            ownership_mult = 1.1  # Okay with medium
        elif ownership >= 15:
            ownership_mult = 1.0  # Neutral
        else:
            ownership_mult = 0.7 + (relaxation * 0.3)  # Avoid low owned

        # Still need decent value
        value_mult = 1.0
        if player.get('value_score', 2) >= 2.5:
            value_mult = 1.1

        # Base score with ownership emphasis
        score = player['projection'] * ownership_mult * value_mult

        return score

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, chalk_scoring, 'chalk_plus'
    )


def build_elite_cash(players):
    """Combine matchup_optimal success with more chalk"""

    def elite_cash_scoring(player, relaxation=0):
        # Start with matchup scoring (it almost worked!)
        matchup_score = 0

        # Matchup factors (from matchup_optimal)
        if player['position'] == 'P':
            k_bb_ratio = player.get('k_bb_ratio', 2.5)
            if k_bb_ratio > 3.0:
                matchup_score += 20
            matchup_score += player['projection']
        else:
            # Platoon advantage
            if player.get('platoon_advantage', 0) > 0:
                matchup_score += 10
            # Batting order
            if player.get('batting_order', 5) <= 4:
                matchup_score += 5
            matchup_score += player['projection']

        # ADD chalk preference (missing piece!)
        ownership = player.get('ownership', 15)
        if ownership >= 30:
            chalk_mult = 1.3
        elif ownership >= 25:
            chalk_mult = 1.2
        elif ownership >= 20:
            chalk_mult = 1.1
        else:
            chalk_mult = 0.9

        # Combine both
        return matchup_score * chalk_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, elite_cash_scoring, 'elite_cash'
    )


def build_correlation_value(players):
    """Value-based approach with game correlation"""
    slate = SlateAnalyzer(players)

    # Find high-value games
    game_values = analyze_game_values(players, slate)

    if game_values:
        # Try to build from best value games
        for game_data in game_values[:3]:
            lineup = build_from_game_values(game_data, players, slate)
            if lineup:
                return lineup

    # Fallback to correlation with value focus
    def correlation_value_scoring(player, relaxation=0):
        # Must have good value
        if not slate.get_value_tier(player['value_score'], 'above_avg'):
            if relaxation < 0.2:
                return 0

        base_score = player['value_score'] * player['projection']

        # Bonus for high-total games
        if player.get('game_total', 8.5) > 9:
            base_score *= 1.2

        return base_score

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players,
        position_requirements,
        correlation_value_scoring,
        'correlation_value'
    )


def build_contrarian_correlation(players):
    """SIMPLE: Low owned players with some correlation"""
    if not players:
        print("DEBUG: contrarian_correlation - No players provided")
        return None

    print(f"DEBUG: contrarian_correlation - Building with {len(players)} players")

    slate = SlateAnalyzer(players)

    # Count team sizes
    team_counts = defaultdict(int)
    for p in players:
        if p['position'] != 'P':
            team_counts[p['team']] += 1

    print(f"DEBUG: contrarian_correlation - Team counts: {dict(team_counts)}")

    def contrarian_score(player, relaxation=0):
        # Low ownership is good
        ownership_score = max(0, 50 - player.get('ownership', 20))

        # Bonus for teams with multiple players
        team_size = team_counts.get(player['team'], 0)
        if team_size >= 3:
            team_bonus = 1.2
        else:
            team_bonus = 1.0

        score = player['projection'] * (ownership_score / 50) * team_bonus
        return score

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    print("DEBUG: contrarian_correlation - Calling build_adaptive_lineup")

    lineup = build_adaptive_lineup(
        players,
        position_requirements,
        contrarian_score,
        'contrarian_correlation'
    )

    if lineup:
        print(f"DEBUG: contrarian_correlation - Success! Salary: ${lineup['salary']}")
    else:
        print("DEBUG: contrarian_correlation - build_adaptive_lineup returned None")

    return lineup

def build_ceiling_stack(players):
    """Maximum upside correlation - adaptive stacking"""
    slate = SlateAnalyzer(players)

    # Find highest ceiling opportunities
    ceiling_options = find_ceiling_stacks(players, slate)

    if ceiling_options:
        for option in ceiling_options[:3]:
            lineup = build_ceiling_focused_lineup(
                option,
                players,
                slate,
                'ceiling_stack'
            )

            if lineup:
                return lineup

    # Fallback to high ceiling players
    def ceiling_scoring(player, relaxation=0):
        # Minimum ceiling threshold
        min_ceiling = slate.ceiling_percentiles[60] * (1 - relaxation * 0.3)

        if player['ceiling'] < min_ceiling:
            return player['ceiling'] * 0.5

        # Ceiling per dollar
        ceiling_value = player['ceiling'] / (player['salary'] / 1000)

        # Upside ratio
        upside = player['ceiling'] / player['projection'] if player['projection'] > 0 else 1

        score = ceiling_value * 0.6 + player['ceiling'] * 0.3 + upside * 0.1

        return score

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    constraints = {
        'min_ceiling': slate.ceiling_percentiles[50]
    }

    return build_adaptive_lineup(
        players,
        position_requirements,
        ceiling_scoring,
        'ceiling_stack',
        constraints
    )


def build_diversified_chalk(players):
    """Spread chalk across games - adaptive game distribution"""
    slate = SlateAnalyzer(players)

    # Get chalk players by game
    chalk_by_game = defaultdict(list)

    for p in players:
        if slate.get_ownership_tier(p['ownership'], 'chalk'):
            chalk_by_game[p.get('game_id', 0)].append(p)

    # Sort games by chalk quality
    game_chalk_quality = []
    for game_id, chalk_players in chalk_by_game.items():
        if chalk_players:
            avg_value = np.mean([p['value_score'] for p in chalk_players])
            total_proj = sum(p['projection'] for p in chalk_players)
            game_chalk_quality.append({
                'game_id': game_id,
                'players': chalk_players,
                'avg_value': avg_value,
                'total_proj': total_proj
            })

    game_chalk_quality.sort(key=lambda x: x['avg_value'], reverse=True)

    # Build with game diversity
    lineup_players = []
    salary = 0
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)
    games_used = defaultdict(int)

    # Target: No more than 3 from any game
    max_per_game = 3

    # First pass: Take best from each game
    for game_data in game_chalk_quality:
        game_players = game_data['players']
        game_players.sort(key=lambda x: x['value_score'], reverse=True)

        added_from_game = 0
        for p in game_players:
            if (added_from_game < 2 and  # First pass: max 2 per game
                    len(lineup_players) < 10 and
                    positions_filled.get(p['position'], 0) < get_position_limit(p['position']) and
                    salary + p['salary'] <= 50000 - (10 - len(lineup_players) - 1) * 3000 and
                    teams_used.get(p['team'], 0) < 4):
                lineup_players.append(p)
                salary += p['salary']
                teams_used[p['team']] += 1
                positions_filled[p['position']] = positions_filled.get(p['position'], 0) + 1
                games_used[game_data['game_id']] += 1
                added_from_game += 1

    # Complete lineup
    remaining = [p for p in players if p not in lineup_players]

    if complete_lineup_with_requirements(lineup_players, remaining, salary, teams_used, positions_filled):
        if len(lineup_players) == 10:
            lineup_dict = create_lineup_dict(lineup_players, 'diversified_chalk')
            return optimize_salary_usage_adaptive(lineup_dict, players, 'diversified_chalk')

    # Fallback to standard chalk approach
    return build_chalk_plus(players)


def build_safe_correlation(players):
    """Mini-stacks from multiple games - adaptive correlation"""
    slate = SlateAnalyzer(players)

    # Find all 2-3 player correlations
    correlations = find_mini_correlations(players, slate)

    # Score correlations
    for corr in correlations:
        avg_floor = np.mean([p['floor'] for p in corr['players']])
        avg_value = np.mean([p['value_score'] for p in corr['players']])
        corr['safety_score'] = avg_floor * 0.6 + avg_value * 5 * 0.4

    correlations.sort(key=lambda x: x['safety_score'], reverse=True)

    # Build with multiple mini-stacks
    lineup_players = []
    salary = 0
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)
    correlations_used = 0
    teams_with_correlation = set()

    # Target: 2-3 mini correlations
    for corr in correlations:
        if (correlations_used < 3 and
                corr['team'] not in teams_with_correlation and
                salary + corr['salary'] <= 40000):  # Leave room

            # Check if we can add all players
            can_add = True
            for p in corr['players']:
                if teams_used.get(p['team'], 0) + 1 > 4:
                    can_add = False
                    break

            if can_add:
                for p in corr['players']:
                    lineup_players.append(p)
                    salary += p['salary']
                    teams_used[p['team']] += 1
                    positions_filled[p['position']] = positions_filled.get(p['position'], 0) + 1

                correlations_used += 1
                teams_with_correlation.add(corr['team'])

    if correlations_used >= 2:
        # Complete lineup
        remaining = [p for p in players if p not in lineup_players]
        remaining.sort(key=lambda x: x['floor'], reverse=True)

        if complete_lineup_with_requirements(lineup_players, remaining, salary, teams_used, positions_filled):
            if len(lineup_players) == 10:
                lineup_dict = create_lineup_dict(lineup_players, 'safe_correlation')
                return optimize_salary_usage_adaptive(lineup_dict, players, 'safe_correlation')

    # Fallback to floor-based approach
    return build_value_floor(players)


def build_leverage_theory(players):
    """SIMPLE: Good players that are underowned - FIXED"""
    slate = SlateAnalyzer(players)

    # Core concept: Projection per ownership WITH salary consideration
    def leverage_score(player, relaxation=0):
        base_score = player['projection'] / (player['ownership'] + 10)

        # Add salary bonus to encourage expensive players
        salary_factor = player['salary'] / 5000  # Normalize around $5000

        # As relaxation increases, weight salary more
        return base_score * (1 + relaxation * salary_factor * 0.3)

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Build with higher minimum salary
    constraints = {
        'min_salary': 48000  # Force higher salary usage
    }

    lineup = build_adaptive_lineup(
        players,
        position_requirements,
        leverage_score,
        'leverage_theory',
        constraints
    )

    return lineup

    def leverage_scoring(player, relaxation=0):
        # Base score
        base_score = player['leverage_multiplier']

        # Leverage bonus
        if player['ownership_leverage'] > 5:
            leverage_mult = 1.3
        elif player['ownership_leverage'] > 0:
            leverage_mult = 1.15
        else:
            leverage_mult = 0.9 + (relaxation * 0.2)

        # Quality check
        if player['projection'] >= slate.avg_projection * (0.7 - relaxation * 0.2):
            quality_mult = 1.0
        else:
            quality_mult = 0.8 + (relaxation * 0.2)

        return base_score * leverage_mult * quality_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Just build with all players and leverage scoring
    lineup = build_adaptive_lineup(
        players,
        position_requirements,
        leverage_scoring,
        'leverage_theory'
    )
    parameters_used['approach'] = 'standard'

    # If that fails, try simpler approach
    if not lineup:
        def simple_leverage(player, relaxation=0):
            return player['projection'] / (player['ownership'] + 10)

        lineup = build_adaptive_lineup(
            players,
            position_requirements,
            simple_leverage,
            'leverage_theory'
        )
        parameters_used['approach'] = 'simplified'

    # Salary optimization
    if lineup and lineup['salary'] < 48000:
        lineup = aggressive_salary_upgrade_gpp(lineup, players, 48500)

    # Track parameters
    if lineup:
        lineup = track_strategy_parameters(lineup, 'leverage_theory', parameters_used)

    return lineup


def build_multi_stack(players):
    """SIMPLE: Bonus for teams with multiple good players"""
    if not players:
        return None

    slate = SlateAnalyzer(players)

    # Find teams with multiple good players
    team_quality = defaultdict(int)
    for p in players:
        if p['position'] != 'P' and p['projection'] > slate.avg_projection * 0.8:
            team_quality[p['team']] += 1

    def multi_stack_score(player, relaxation=0):
        # Bonus for being on a team with multiple good players
        quality_count = team_quality.get(player['team'], 0)
        if quality_count >= 3:
            team_bonus = 1.3
        elif quality_count >= 2:
            team_bonus = 1.15
        else:
            team_bonus = 1.0

        return player['projection'] * team_bonus

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    lineup = build_adaptive_lineup(
        players,
        position_requirements,
        multi_stack_score,
        'multi_stack'
    )

    return lineup
# ========== ADAPTIVE HELPER FUNCTIONS ==========

def force_expensive_swaps(lineup_dict, all_players):
    """Force more expensive players to reach salary target"""
    if not lineup_dict:
        return lineup_dict

    lineup = lineup_dict['players'].copy()
    current_salary = sum(p['salary'] for p in lineup)

    # Already at target
    if current_salary >= 48000:
        return lineup_dict

    # Sort by salary ascending
    lineup.sort(key=lambda x: x['salary'])

    # Replace bottom 40% of lineup with more expensive options
    num_to_replace = 4  # 40% of 10

    for i in range(num_to_replace):
        if current_salary >= 48000:
            break

        current_player = lineup[i]

        # Find most expensive valid replacement
        replacements = [
            p for p in all_players
            if p['position'] == current_player['position']
               and p['id'] != current_player['id']
               and p not in lineup
               and p['salary'] > current_player['salary']
               and p['salary'] <= current_player['salary'] + (50000 - current_salary)
        ]

        if replacements:
            # Sort by salary descending (most expensive first)
            replacements.sort(key=lambda x: x['salary'], reverse=True)

            # Try each until we find valid one
            for replacement in replacements[:5]:
                test_lineup = lineup.copy()
                test_lineup[i] = replacement

                # Check team constraint
                teams = defaultdict(int)
                for p in test_lineup:
                    teams[p['team']] += 1

                if max(teams.values()) <= 5:
                    # Additional check for strategy compliance
                    if lineup_dict.get('strategy') == 'game_theory_leverage':
                        # Don't add super high ownership
                        if replacement['ownership'] > 40:
                            continue

                    lineup = test_lineup
                    current_salary = sum(p['salary'] for p in lineup)
                    break

    return create_lineup_dict(lineup, lineup_dict.get('strategy', ''))


def force_expensive_swaps(lineup_dict, all_players):
    """Force more expensive players to reach salary target"""
    if not lineup_dict:
        return lineup_dict

    lineup = lineup_dict['players'].copy()
    current_salary = sum(p['salary'] for p in lineup)

    # Sort by salary ascending
    lineup.sort(key=lambda x: x['salary'])

    # Replace bottom 40% of lineup with more expensive options
    num_to_replace = 4  # 40% of 10

    for i in range(num_to_replace):
        if current_salary >= 48000:
            break

        current_player = lineup[i]

        # Find most expensive valid replacement
        replacements = [
            p for p in all_players
            if p['position'] == current_player['position']
               and p['id'] != current_player['id']
               and p not in lineup
               and p['salary'] > current_player['salary']
               and p['salary'] <= current_player['salary'] + (50000 - current_salary)
        ]

        if replacements:
            # Sort by salary descending (most expensive first)
            replacements.sort(key=lambda x: x['salary'], reverse=True)

            # Try each until we find valid one
            for replacement in replacements[:5]:
                test_lineup = lineup.copy()
                test_lineup[i] = replacement

                # Check team constraint
                teams = defaultdict(int)
                for p in test_lineup:
                    teams[p['team']] += 1

                if max(teams.values()) <= 5:
                    lineup = test_lineup
                    current_salary = sum(p['salary'] for p in lineup)
                    break

    return create_lineup_dict(lineup, lineup_dict['strategy'])



def get_position_limit(position):
    """Get position limit for classic"""
    limits = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }
    return limits.get(position, 1)


def find_all_stack_options(players, slate):
    """Find all viable stacking options"""
    stacks = []

    # Team stacks
    team_players = defaultdict(list)
    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    for team, team_list in team_players.items():
        stack_sizes = slate.get_stack_options(team)

        for size in stack_sizes:
            if size >= 3:  # Minimum 3 for a real stack
                team_list.sort(key=lambda x: x['projection'], reverse=True)
                stack_players = team_list[:size]

                stacks.append({
                    'players': stack_players,
                    'type': f'{size}-team',
                    'score': sum(p['projection'] for p in stack_players),
                    'salary': sum(p['salary'] for p in stack_players),
                    'team': team
                })

    # Game stacks
    games = defaultdict(lambda: defaultdict(list))
    for p in players:
        if p['position'] != 'P':
            games[p.get('game_id', 0)][p['team']].append(p)

    for game_id, teams in games.items():
        if len(teams) == 2:
            team_lists = list(teams.items())
            team1, players1 = team_lists[0]
            team2, players2 = team_lists[1]

            # Various game stack configurations
            configs = []
            if len(players1) >= 4 and len(players2) >= 1:
                configs.append((4, 1))
            if len(players1) >= 3 and len(players2) >= 2:
                configs.append((3, 2))
            if len(players1) >= 2 and len(players2) >= 2:
                configs.append((2, 2))

            for p1_count, p2_count in configs:
                players1_sorted = sorted(players1, key=lambda x: x['projection'], reverse=True)
                players2_sorted = sorted(players2, key=lambda x: x['projection'], reverse=True)

                stack_players = players1_sorted[:p1_count] + players2_sorted[:p2_count]

                stacks.append({
                    'players': stack_players,
                    'type': f'{p1_count}-{p2_count}-game',
                    'score': sum(p['projection'] for p in stack_players),
                    'salary': sum(p['salary'] for p in stack_players),
                    'team': f'{team1}/{team2}'
                })

    # Sort by score
    stacks.sort(key=lambda x: x['score'], reverse=True)

    return stacks


def build_lineup_from_stack_adaptive(stack, all_players, strategy_name, stack_type):
    """Build complete lineup from stack with adaptive completion"""
    lineup = stack.copy()
    salary = sum(p['salary'] for p in lineup)
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)

    for p in lineup:
        teams_used[p['team']] += 1
        positions_filled[p['position']] = positions_filled.get(p['position'], 0) + 1

    # Get remaining players
    remaining = [p for p in all_players if p not in lineup]

    # Smart pitcher selection based on stack type
    if '5-team' in stack_type or '4-team' in stack_type:
        # Get pitcher against the stack if possible
        stack_team = max(teams_used.items(), key=lambda x: x[1])[0]

        # Find opposing pitchers
        opp_pitchers = []
        for p in remaining:
            if p['position'] == 'P':
                # Check if pitcher is against our stack
                for stack_player in stack:
                    if (p.get('game_id') == stack_player.get('game_id') and
                            p['team'] != stack_player['team']):
                        opp_pitchers.append(p)
                        break

        if opp_pitchers:
            # Prioritize opposing pitchers
            opp_pitchers.sort(key=lambda x: x['projection'], reverse=True)
            remaining = opp_pitchers + [p for p in remaining if p not in opp_pitchers]

    # Complete lineup with requirements
    if complete_lineup_with_requirements(lineup, remaining, salary, teams_used, positions_filled):
        if len(lineup) == 10:
            lineup_dict = create_lineup_dict(lineup, strategy_name)
            return optimize_salary_usage_adaptive(lineup_dict, all_players, strategy_name)

    return None


def build_with_mini_correlations_adaptive(players, scoring_function, strategy_name):
    """Build with 2-player correlations using adaptive scoring"""
    slate = SlateAnalyzer(players)

    # Find mini-stacks
    mini_stacks = []

    for i, p1 in enumerate(players):
        for j, p2 in enumerate(players[i + 1:], i + 1):
            if (p1['team'] == p2['team'] and
                    p1['position'] != p2['position'] and
                    p1['position'] != 'P' and p2['position'] != 'P'):

                combined_score = scoring_function(p1, 0) + scoring_function(p2, 0)
                combined_salary = p1['salary'] + p2['salary']

                if combined_salary <= 13000:  # Slightly higher threshold
                    mini_stacks.append({
                        'players': [p1, p2],
                        'score': combined_score,
                        'salary': combined_salary,
                        'team': p1['team']
                    })

    if not mini_stacks:
        return None

    mini_stacks.sort(key=lambda x: x['score'], reverse=True)

    # Build lineup with mini-stacks
    lineup_players = []
    salary = 0
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)
    used_teams = set()

    # Add 2-3 mini-stacks
    for stack in mini_stacks[:30]:
        if (len(used_teams) < 3 and
                stack['team'] not in used_teams and
                salary + stack['salary'] <= 38000):

            can_add = True
            for p in stack['players']:
                if teams_used.get(p['team'], 0) + 1 > 4:
                    can_add = False
                    break

            if can_add:
                for p in stack['players']:
                    lineup_players.append(p)
                    salary += p['salary']
                    teams_used[p['team']] += 1
                    positions_filled[p['position']] = positions_filled.get(p['position'], 0) + 1

                used_teams.add(stack['team'])

                if len(used_teams) >= 2:
                    break

    # Complete lineup
    remaining = [p for p in players if p not in lineup_players]

    # Sort by scoring function
    scored_remaining = [(scoring_function(p, 0), p) for p in remaining]
    scored_remaining.sort(reverse=True)
    remaining = [p for score, p in scored_remaining]

    if complete_lineup_with_requirements(lineup_players, remaining, salary, teams_used, positions_filled):
        if len(lineup_players) == 10:
            lineup_dict = create_lineup_dict(lineup_players, strategy_name)
            return optimize_salary_usage_adaptive(lineup_dict, players, strategy_name)

    return None




def build_with_forced_correlation(players, correlation_opportunities, strategy_name):
    """Force correlation into lineup"""
    # Take best correlation
    if not correlation_opportunities:
        return None

    best_correlation = correlation_opportunities[0]

    lineup_players = []
    salary = 0
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)

    # Add correlation players
    correlation_players = best_correlation.get('players', [])[:3]

    for p in correlation_players:
        lineup_players.append(p)
        salary += p['salary']
        teams_used[p['team']] += 1
        positions_filled[p['position']] = positions_filled.get(p['position'], 0) + 1

    # Complete lineup
    remaining = [p for p in players if p not in lineup_players]
    remaining.sort(key=lambda x: x['value_score'], reverse=True)

    if complete_lineup_with_requirements(lineup_players, remaining, salary, teams_used, positions_filled):
        if len(lineup_players) == 10:
            return create_lineup_dict(lineup_players, strategy_name)

    return None




def build_lineup_from_multi_stack_adaptive(core_players, all_players, strategy_name):
    """Build lineup from multiple mini-stacks"""
    lineup = core_players.copy()
    salary = sum(p['salary'] for p in lineup)
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)

    for p in lineup:
        teams_used[p['team']] += 1
        positions_filled[p['position']] = positions_filled.get(p['position'], 0) + 1

    # Complete lineup
    remaining = [p for p in all_players if p not in lineup]
    remaining.sort(key=lambda x: x['value_score'], reverse=True)

    if complete_lineup_with_requirements(lineup, remaining, salary, teams_used, positions_filled):
        if len(lineup) == 10:
            lineup_dict = create_lineup_dict(lineup, strategy_name)
            return optimize_salary_usage_adaptive(lineup_dict, all_players, strategy_name)

    return None


def build_with_ownership_tiers(players, slate, strategy_name):
    """Build with ownership tier diversity"""
    # Define tiers
    chalk = [p for p in players if slate.get_ownership_tier(p['ownership'], 'chalk')]
    mid = [p for p in players if slate.get_ownership_tier(p['ownership'], 'mid')]
    low = [p for p in players if slate.get_ownership_tier(p['ownership'], 'low')]

    # Sort each tier by value
    for tier in [chalk, mid, low]:
        tier.sort(key=lambda x: x['value_score'], reverse=True)

    # Build with tier targets
    lineup_players = []
    salary = 0
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)

    # Tier targets
    targets = {
        'chalk': 5,
        'mid': 3,
        'low': 2
    }

    tier_counts = defaultdict(int)

    # First pass: Fill from each tier
    for tier_name, tier_list, target in [('chalk', chalk, 5), ('mid', mid, 3), ('low', low, 2)]:
        for p in tier_list:
            if (tier_counts[tier_name] < target and
                    len(lineup_players) < 10 and
                    positions_filled.get(p['position'], 0) < get_position_limit(p['position']) and
                    salary + p['salary'] <= 50000 - (10 - len(lineup_players) - 1) * 3000 and
                    teams_used.get(p['team'], 0) < 5):
                lineup_players.append(p)
                salary += p['salary']
                teams_used[p['team']] += 1
                positions_filled[p['position']] = positions_filled.get(p['position'], 0) + 1
                tier_counts[tier_name] += 1

    # Complete lineup
    remaining = [p for p in players if p not in lineup_players]

    if complete_lineup_with_requirements(lineup_players, remaining, salary, teams_used, positions_filled):
        if len(lineup_players) == 10:
            lineup_dict = create_lineup_dict(lineup_players, strategy_name)
            return optimize_salary_usage_adaptive(lineup_dict, players, strategy_name)

    return None


def analyze_game_values(players, slate):
    """Analyze games by value concentration"""
    games = defaultdict(list)

    for p in players:
        if slate.get_value_tier(p['value_score'], 'above_avg'):
            games[p.get('game_id', 0)].append(p)

    game_values = []
    for game_id, game_players in games.items():
        if len(game_players) >= 4:
            avg_value = np.mean([p['value_score'] for p in game_players])
            total_proj = sum(p['projection'] for p in game_players)

            game_values.append({
                'game_id': game_id,
                'players': game_players,
                'avg_value': avg_value,
                'total_proj': total_proj
            })

    game_values.sort(key=lambda x: x['avg_value'], reverse=True)

    return game_values


def build_from_game_values(game_data, all_players, slate):
    """Build lineup from high-value game"""
    lineup_players = []
    salary = 0
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)

    # Take best values from game
    game_players = game_data['players'].copy()
    game_players.sort(key=lambda x: x['value_score'], reverse=True)

    # Add up to 5 from this game
    for p in game_players[:5]:
        if (salary + p['salary'] <= 40000 and
                teams_used.get(p['team'], 0) < 4 and
                positions_filled.get(p['position'], 0) < get_position_limit(p['position'])):
            lineup_players.append(p)
            salary += p['salary']
            teams_used[p['team']] += 1
            positions_filled[p['position']] = positions_filled.get(p['position'], 0) + 1

    if len(lineup_players) >= 3:
        # Complete lineup
        remaining = [p for p in all_players if p not in lineup_players]
        remaining.sort(key=lambda x: x['value_score'], reverse=True)

        if complete_lineup_with_requirements(lineup_players, remaining, salary, teams_used, positions_filled):
            if len(lineup_players) == 10:
                lineup_dict = create_lineup_dict(lineup_players, 'correlation_value')
                return optimize_salary_usage_adaptive(lineup_dict, all_players, 'correlation_value')

    return None


def find_contrarian_games(players, slate):
    """Find games with low ownership"""
    games = defaultdict(lambda: defaultdict(list))

    for p in players:
        if p['position'] != 'P' and p['ownership'] < slate.ownership_percentiles[40]:
            games[p.get('game_id', 0)][p['team']].append(p)

    contrarian_games = []

    for game_id, teams in games.items():
        if len(teams) == 2:
            all_players = []
            for team_players in teams.values():
                all_players.extend(team_players)

            if len(all_players) >= 4:
                avg_ownership = np.mean([p['ownership'] for p in all_players])
                total_ceiling = sum(p['ceiling'] for p in all_players)

                contrarian_games.append({
                    'game_id': game_id,
                    'teams': teams,
                    'avg_ownership': avg_ownership,
                    'total_ceiling': total_ceiling
                })

    contrarian_games.sort(key=lambda x: x['total_ceiling'], reverse=True)

    return contrarian_games


def get_stack_configs_for_game(game_data, slate):
    """Get possible stack configurations for a game"""
    configs = []
    teams = game_data['teams']
    team_list = list(teams.items())

    if len(team_list) >= 2:
        team1, players1 = team_list[0]
        team2, players2 = team_list[1]

        # Different configurations
        if len(players1) >= 3 and len(players2) >= 2:
            configs.append({
                'type': '3-2',
                'players': sorted(players1, key=lambda x: x['ceiling'], reverse=True)[:3] +
                           sorted(players2, key=lambda x: x['ceiling'], reverse=True)[:2]
            })

        if len(players1) >= 2 and len(players2) >= 2:
            configs.append({
                'type': '2-2',
                'players': sorted(players1, key=lambda x: x['ceiling'], reverse=True)[:2] +
                           sorted(players2, key=lambda x: x['ceiling'], reverse=True)[:2]
            })

        if len(players1) >= 4 and len(players2) >= 1:
            configs.append({
                'type': '4-1',
                'players': sorted(players1, key=lambda x: x['ceiling'], reverse=True)[:4] +
                           sorted(players2, key=lambda x: x['ceiling'], reverse=True)[:1]
            })

    return configs


def build_game_stack_adaptive(config, all_players, strategy_name):
    """Build lineup from game stack configuration"""
    return build_lineup_from_stack_adaptive(
        config['players'],
        all_players,
        strategy_name,
        config['type']
    )


def find_ceiling_stacks(players, slate):
    """Find highest ceiling stacking opportunities"""
    options = []

    # Game stacks by ceiling
    games = defaultdict(list)
    for p in players:
        if p['ceiling'] > slate.ceiling_percentiles[50]:
            games[p.get('game_id', 0)].append(p)

    for game_id, game_players in games.items():
        if len(game_players) >= 5:
            total_ceiling = sum(p['ceiling'] for p in game_players)
            options.append({
                'type': 'game',
                'players': game_players,
                'total_ceiling': total_ceiling,
                'id': game_id
            })

    # Team stacks by ceiling
    teams = defaultdict(list)
    for p in players:
        if p['position'] != 'P' and p['ceiling'] > slate.ceiling_percentiles[50]:
            teams[p['team']].append(p)

    for team, team_players in teams.items():
        if len(team_players) >= 4:
            team_players.sort(key=lambda x: x['ceiling'], reverse=True)
            total_ceiling = sum(p['ceiling'] for p in team_players[:5])
            options.append({
                'type': 'team',
                'players': team_players[:5],
                'total_ceiling': total_ceiling,
                'id': team
            })

    options.sort(key=lambda x: x['total_ceiling'], reverse=True)

    return options


def build_ceiling_focused_lineup(option, all_players, slate, strategy_name):
    """Build lineup from ceiling option"""
    lineup_players = []
    salary = 0
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)

    # Add core ceiling players
    core_players = option['players'][:6]  # Take top 6 by ceiling

    for p in core_players:
        if (salary + p['salary'] <= 42000 and
                teams_used.get(p['team'], 0) < 4 and
                positions_filled.get(p['position'], 0) < get_position_limit(p['position'])):
            lineup_players.append(p)
            salary += p['salary']
            teams_used[p['team']] += 1
            positions_filled[p['position']] = positions_filled.get(p['position'], 0) + 1

    if len(lineup_players) >= 4:
        # Complete with high ceiling players
        remaining = [p for p in all_players if p not in lineup_players]
        remaining.sort(key=lambda x: x['ceiling'], reverse=True)

        if complete_lineup_with_requirements(lineup_players, remaining, salary, teams_used, positions_filled):
            if len(lineup_players) == 10:
                lineup_dict = create_lineup_dict(lineup_players, strategy_name)
                return optimize_salary_usage_adaptive(lineup_dict, all_players, strategy_name)

    return None


def find_mini_correlations(players, slate):
    """Find 2-3 player correlations for safe builds"""
    correlations = []

    # 2-player correlations
    team_players = defaultdict(list)
    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    for team, team_list in team_players.items():
        if len(team_list) >= 2:
            # Sort by floor for safety
            team_list.sort(key=lambda x: x['floor'], reverse=True)

            # Take best 2-3 by floor
            for size in [2, 3]:
                if len(team_list) >= size:
                    correlation_players = team_list[:size]

                    correlations.append({
                        'players': correlation_players,
                        'team': team,
                        'size': size,
                        'total_floor': sum(p['floor'] for p in correlation_players),
                        'salary': sum(p['salary'] for p in correlation_players)
                    })

    return correlations


def find_all_mini_stacks(players, slate):
    """Find all 2-3 player mini-stacks"""
    mini_stacks = []

    team_players = defaultdict(list)
    for p in players:
        if p['position'] != 'P':
            team_players[p['team']].append(p)

    for team, team_list in team_players.items():
        # Different size options
        for size in [2, 3]:
            if len(team_list) >= size:
                # Try different sorting methods
                by_projection = sorted(team_list, key=lambda x: x['projection'], reverse=True)[:size]
                by_value = sorted(team_list, key=lambda x: x['value_score'], reverse=True)[:size]

                # Add both options
                for stack_players in [by_projection, by_value]:
                    mini_stacks.append({
                        'players': stack_players,
                        'team': team,
                        'size': size
                    })

    # Remove duplicates
    unique_stacks = []
    seen = set()

    for stack in mini_stacks:
        player_ids = tuple(sorted([p['id'] for p in stack['players']]))
        if player_ids not in seen:
            seen.add(player_ids)
            unique_stacks.append(stack)

    return unique_stacks


def aggressive_salary_upgrade(lineup_dict, all_players, target_salary):
    """Aggressively upgrade to reach target salary"""
    if not lineup_dict or lineup_dict['salary'] >= target_salary:
        return lineup_dict

    lineup = lineup_dict['players'].copy()
    current_salary = lineup_dict['salary']

    # Multiple passes with increasing aggressiveness
    for pass_num in range(3):
        if current_salary >= target_salary:
            break

        # Sort by salary
        lineup.sort(key=lambda x: x['salary'])

        # Try to upgrade bottom players
        for i in range(min(4 + pass_num, len(lineup))):
            current_player = lineup[i]
            needed = target_salary - current_salary

            # Find upgrades
            upgrades = [
                p for p in all_players
                if p['position'] == current_player['position']
                   and p['id'] != current_player['id']
                   and p not in lineup
                   and p['salary'] > current_player['salary']
                   and p['salary'] - current_player['salary'] <= needed + (pass_num * 1000)
            ]

            # Relaxed requirements on later passes
            min_proj_ratio = 0.9 - (pass_num * 0.1)
            upgrades = [u for u in upgrades
                        if u['projection'] >= current_player['projection'] * min_proj_ratio]

            if upgrades:
                # Prefer expensive upgrades
                upgrades.sort(key=lambda x: x['salary'], reverse=True)

                for upgrade in upgrades[:5]:
                    # Test lineup
                    test_lineup = lineup.copy()
                    test_lineup[i] = upgrade

                    teams = defaultdict(int)
                    for p in test_lineup:
                        teams[p['team']] += 1

                    if max(teams.values()) <= 5:
                        lineup = test_lineup
                        current_salary = sum(p['salary'] for p in lineup)
                        break

    return create_lineup_dict(lineup, lineup_dict['strategy'])


def build_contrarian_correlation(players):
    """SIMPLE: Low owned players with team bonus"""
    if not players:
        return None

    slate = SlateAnalyzer(players)

    # Count team sizes
    team_counts = defaultdict(int)
    for p in players:
        if p['position'] != 'P':
            team_counts[p['team']] += 1

    def contrarian_score(player, relaxation=0):
        # Low ownership is good
        ownership_score = max(0, 50 - player['ownership'])

        # Bonus for teams with multiple players
        team_size = team_counts.get(player['team'], 0)
        if team_size >= 3:
            team_bonus = 1.2
        else:
            team_bonus = 1.0

        return player['projection'] * (ownership_score / 50) * team_bonus

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    lineup = build_adaptive_lineup(
        players,
        position_requirements,
        contrarian_score,
        'contrarian_correlation'
    )

    return lineup


# ========== SHOWDOWN STRATEGIES ==========

def build_balanced_showdown(players):
    """Optimal captain selection with balanced lineup"""

    # Calculate captain metrics
    for p in players:
        # Captain gets 1.5x points but costs 1.5x salary
        p['captain_projection'] = p['projection'] * 1.5
        p['captain_salary'] = int(p['salary'] * 1.5)
        p['captain_value'] = p['captain_projection'] / (p['captain_salary'] / 1000)
        # Efficiency score considering the multiplier
        p['captain_efficiency'] = (p['captain_projection'] - p['projection']) / (p['captain_salary'] - p['salary'])

    # Try top captain candidates
    captain_candidates = sorted(players, key=lambda x: x['captain_value'], reverse=True)[:8]

    for captain in captain_candidates:
        lineup = [captain]
        captain_salary = captain['captain_salary']
        remaining_budget = 50000 - captain_salary

        # Need 5 FLEX players
        remaining_players = [p for p in players if p['id'] != captain['id']]

        # Calculate value for remaining spots
        avg_remaining_salary = remaining_budget / 5

        # Prefer some correlation with captain
        same_team = [p for p in remaining_players if p['team'] == captain['team']]
        opp_team = [p for p in remaining_players if p['team'] != captain['team']]

        # Sort by value
        same_team.sort(key=lambda x: x['value_score'], reverse=True)
        opp_team.sort(key=lambda x: x['value_score'], reverse=True)

        # Build balanced lineup
        flex_players = []
        flex_salary = 0

        # Try to get 2-3 from captain's team
        same_team_count = 0
        for p in same_team:
            if (len(flex_players) < 5 and
                    same_team_count < 3 and
                    flex_salary + p['salary'] <= remaining_budget):
                flex_players.append(p)
                flex_salary += p['salary']
                same_team_count += 1

        # Fill with opposing team
        for p in opp_team:
            if (len(flex_players) < 5 and
                    flex_salary + p['salary'] <= remaining_budget):
                flex_players.append(p)
                flex_salary += p['salary']

        # If still need players, add best available
        if len(flex_players) < 5:
            all_remaining = [p for p in remaining_players if p not in flex_players]
            all_remaining.sort(key=lambda x: x['value_score'], reverse=True)

            for p in all_remaining:
                if (len(flex_players) < 5 and
                        flex_salary + p['salary'] <= remaining_budget):
                    flex_players.append(p)
                    flex_salary += p['salary']

        if len(flex_players) == 5:
            lineup.extend(flex_players)

            # Calculate total projection with captain bonus
            total_proj = captain['captain_projection'] + sum(p['projection'] for p in flex_players)
            total_salary = captain_salary + flex_salary

            return {
                'players': lineup,
                'salary': total_salary,
                'projection': total_proj,
                'ownership': np.mean([captain['ownership']] + [p['ownership'] for p in flex_players]),
                'strategy': 'balanced_showdown',
                'captain': captain['name'],
                'captain_multiplier': 1.5,
                'format': 'showdown'
            }

    return None


def build_leverage_captain(players):
    """Low owned captain with upside correlation"""

    # Find leverage captains
    for p in players:
        p['captain_leverage'] = (p['ceiling'] * 1.5) / (p['ownership'] + 10)
        p['captain_upside'] = p['ceiling'] * 1.5
        p['captain_salary'] = int(p['salary'] * 1.5)

    # Focus on low-owned players with upside
    captain_candidates = [p for p in players if p['ownership'] < 20 and p['ceiling'] > 10]

    if len(captain_candidates) < 3:
        # Expand criteria if needed
        captain_candidates = [p for p in players if p['ownership'] < 25]

    captain_candidates.sort(key=lambda x: x['captain_leverage'], reverse=True)

    for captain in captain_candidates[:8]:
        lineup = [captain]
        captain_salary = captain['captain_salary']
        remaining_budget = 50000 - captain_salary

        # Build correlated lineup
        remaining_players = [p for p in players if p['id'] != captain['id']]

        # Prioritize captain's team for correlation
        same_team = [p for p in remaining_players if p['team'] == captain['team']]
        opp_team = [p for p in remaining_players if p['team'] != captain['team']]

        # Sort by ceiling for GPP
        same_team.sort(key=lambda x: x['ceiling'], reverse=True)
        opp_team.sort(key=lambda x: x['ceiling'], reverse=True)

        flex_players = []
        flex_salary = 0

        # Heavy correlation - try for 3-4 from captain's team
        same_team_count = 0
        for p in same_team:
            if (len(flex_players) < 5 and
                    same_team_count < 4 and
                    flex_salary + p['salary'] <= remaining_budget):
                flex_players.append(p)
                flex_salary += p['salary']
                same_team_count += 1

        # Add 1-2 from opposing team
        for p in opp_team:
            if (len(flex_players) < 5 and
                    flex_salary + p['salary'] <= remaining_budget):
                flex_players.append(p)
                flex_salary += p['salary']

        # Fill remaining spots
        if len(flex_players) < 5:
            all_remaining = [p for p in remaining_players if p not in flex_players]
            all_remaining.sort(key=lambda x: x['ceiling'], reverse=True)

            for p in all_remaining:
                if (len(flex_players) < 5 and
                        flex_salary + p['salary'] <= remaining_budget):
                    flex_players.append(p)
                    flex_salary += p['salary']

        if len(flex_players) == 5:
            lineup.extend(flex_players)

            # Calculate projection with captain bonus
            total_proj = captain['captain_projection'] + sum(p['projection'] for p in flex_players)
            total_salary = captain_salary + flex_salary

            return {
                'players': lineup,
                'salary': total_salary,
                'projection': total_proj,
                'ownership': np.mean([captain['ownership']] + [p['ownership'] for p in flex_players]),
                'strategy': 'leverage_captain',
                'captain': captain['name'],
                'captain_multiplier': 1.5,
                'captain_ownership': captain['ownership'],
                'format': 'showdown'
            }

    return None

def build_leverage_captain(players):
    """Low owned captain with upside correlation"""

    # Find leverage captains
    for p in players:
        p['captain_leverage'] = (p['ceiling'] * 1.5) / (p['ownership'] + 10)
        p['captain_upside'] = p['ceiling'] * 1.5 - p['projection'] * 1.5

    # Focus on low-owned players with upside
    captain_candidates = [p for p in players if p['ownership'] < 15]

    if len(captain_candidates) < 3:
        captain_candidates = [p for p in players if p['ownership'] < 20]

    captain_candidates.sort(key=lambda x: x['captain_leverage'], reverse=True)

    for captain in captain_candidates[:5]:
        lineup = [captain]
        salary = captain['salary'] * 1.5

        # Build correlated lineup
        remaining = [p for p in players if p != captain]

        # Prioritize captain's team for correlation
        same_team = [p for p in remaining if p['team'] == captain['team']]
        opp_team = [p for p in remaining if p['team'] != captain['team']]

        # Sort by ceiling for GPP
        same_team.sort(key=lambda x: x['ceiling'], reverse=True)
        opp_team.sort(key=lambda x: x['ceiling'], reverse=True)

        flex_players = []

        # Heavy correlation - 3 from captain's team
        for p in same_team[:3]:
            if salary + p['salary'] <= 50000:
                flex_players.append(p)
                salary += p['salary']

        # 2 from opposing team
        for p in opp_team[:2]:
            if len(flex_players) < 5 and salary + p['salary'] <= 50000:
                flex_players.append(p)
                salary += p['salary']

        # Fill with best available
        all_remaining = [p for p in remaining if p not in flex_players]
        all_remaining.sort(key=lambda x: x['ceiling'], reverse=True)

        for p in all_remaining:
            if len(flex_players) < 5 and salary + p['salary'] <= 50000:
                flex_players.append(p)
                salary += p['salary']

        if len(flex_players) == 5:
            lineup.extend(flex_players)

            # Calculate projection with captain bonus
            total_proj = captain['projection'] * 1.5 + sum(p['projection'] for p in flex_players)

            return {
                'players': lineup,
                'salary': salary,
                'projection': total_proj,
                'ownership': np.mean([p['ownership'] for p in lineup]),
                'strategy': 'leverage_captain',
                'captain': captain['name'],
                'captain_multiplier': 1.5,
                'captain_ownership': captain['ownership']
            }

    return None


# ========== HELPER FUNCTIONS ==========


def aggressive_salary_upgrade_gpp(lineup_dict, all_players, target_salary):
    """More aggressive salary optimization for GPP strategies"""
    if not lineup_dict or lineup_dict['salary'] >= target_salary:
        return lineup_dict

    lineup = lineup_dict['players'].copy()
    current_salary = lineup_dict['salary']

    # Multiple aggressive passes
    for pass_num in range(4):  # More passes
        if current_salary >= target_salary:
            break

        # Sort by salary
        lineup.sort(key=lambda x: x['salary'])

        # Try to upgrade more players
        for i in range(min(5 + pass_num, len(lineup))):  # Upgrade more each pass
            current_player = lineup[i]
            needed = target_salary - current_salary

            # Find upgrades
            upgrades = [
                p for p in all_players
                if p['position'] == current_player['position']
                   and p['id'] != current_player['id']
                   and p not in lineup
                   and p['salary'] > current_player['salary']
                   and p['salary'] - current_player['salary'] <= needed + (pass_num * 2000)
            ]

            # For GPP, prioritize ceiling
            upgrades = [u for u in upgrades
                        if u['ceiling'] >= current_player['ceiling'] * (0.95 - pass_num * 0.05)]

            if upgrades:
                # Sort by salary for maximum usage
                upgrades.sort(key=lambda x: x['salary'], reverse=True)

                for upgrade in upgrades[:5]:
                    test_lineup = lineup.copy()
                    test_lineup[i] = upgrade

                    teams = defaultdict(int)
                    for p in test_lineup:
                        teams[p['team']] += 1

                    if max(teams.values()) <= 5:
                        lineup = test_lineup
                        current_salary = sum(p['salary'] for p in lineup)
                        break

    return create_lineup_dict(lineup, lineup_dict.get('strategy', ''))


def force_expensive_swaps_gpp(lineup_dict, all_players):
    """GPP-specific expensive swaps"""
    if not lineup_dict or lineup_dict['salary'] >= 48000:
        return lineup_dict

    lineup = lineup_dict['players'].copy()
    current_salary = sum(p['salary'] for p in lineup)

    # Find cheapest 40%
    lineup.sort(key=lambda x: x['salary'])
    num_to_replace = 4

    for i in range(num_to_replace):
        if current_salary >= 48000:
            break

        current_player = lineup[i]

        # Find expensive replacements with good ceiling
        replacements = [
            p for p in all_players
            if p['position'] == current_player['position']
               and p['id'] != current_player['id']
               and p not in lineup
               and p['salary'] > current_player['salary']
               and p['salary'] <= current_player['salary'] + (50000 - current_salary)
               and p['ceiling'] >= current_player['ceiling']  # Maintain ceiling
        ]

        if replacements:
            # Prioritize expensive with good ceiling
            replacements.sort(key=lambda x: (x['salary'], x['ceiling']), reverse=True)

            for replacement in replacements[:3]:
                test_lineup = lineup.copy()
                test_lineup[i] = replacement

                teams = defaultdict(int)
                for p in test_lineup:
                    teams[p['team']] += 1

                if max(teams.values()) <= 5:
                    lineup = test_lineup
                    current_salary = sum(p['salary'] for p in lineup)
                    break

    return create_lineup_dict(lineup, lineup_dict.get('strategy', ''))



def build_from_pool_with_requirements(pool, strategy_name):
    """Build valid lineup from player pool"""
    if len(pool) < 10:
        return None

    lineup = []
    salary = 0
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Make a copy to work with
    available_players = pool.copy()

    # Sort pool by value
    available_players.sort(key=lambda x: x.get('value_score', x['projection'] / (x['salary'] / 1000)), reverse=True)

    # Count available by position
    position_counts = defaultdict(int)
    for p in available_players:
        position_counts[p['position']] += 1

    # Check if we have enough players at each position
    for pos, req in position_requirements.items():
        if position_counts[pos] < req:
            return None  # Not enough players at this position

    # Fill scarce positions first
    position_scarcity = {}
    for pos, req in position_requirements.items():
        available = position_counts[pos]
        position_scarcity[pos] = available / req if req > 0 else float('inf')

    sorted_positions = sorted(position_requirements.items(),
                              key=lambda x: position_scarcity[x[0]])

    # Build lineup
    for pos, needed in sorted_positions:
        candidates = [p for p in available_players
                      if p['position'] == pos and p not in lineup]

        # Sort by value within position
        candidates.sort(key=lambda x: x.get('value_score', x['projection'] / (x['salary'] / 1000)), reverse=True)

        filled = 0
        for p in candidates:
            if filled < needed:
                # Check constraints
                test_salary = salary + p['salary']
                remaining_spots = 10 - len(lineup) - 1
                min_remaining_salary = remaining_spots * 2500  # Minimum salary per player

                if (test_salary <= 50000 - min_remaining_salary and
                        teams_used.get(p['team'], 0) < 5):
                    lineup.append(p)
                    salary = test_salary
                    teams_used[p['team']] = teams_used.get(p['team'], 0) + 1
                    positions_filled[pos] = positions_filled.get(pos, 0) + 1
                    filled += 1

        # If we couldn't fill this position, lineup is invalid
        if filled < needed:
            return None

    if len(lineup) == 10 and validate_lineup(lineup):
        result = create_lineup_dict(lineup, strategy_name)
        # Always try to optimize salary usage
        return optimize_salary_usage(result, pool, strategy_name)

    return None

def build_by_metric_with_requirements(players, metric, strategy_name):
    """Build lineup sorted by given metric"""
    players_copy = players.copy()
    players_copy.sort(key=lambda x: x.get(metric, 0), reverse=True)

    return build_from_pool_with_requirements(players_copy, strategy_name)


def complete_lineup_with_requirements(lineup, remaining_players, current_salary, teams_used, positions_filled):
    """Complete a partial lineup with valid players"""
    if not lineup:
        lineup = []

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Calculate what we still need
    positions_needed = {}
    for pos, req in position_requirements.items():
        current = positions_filled.get(pos, 0)
        if current < req:
            positions_needed[pos] = req - current

    # If lineup is already complete
    if not positions_needed and len(lineup) == 10:
        return True

    # Make a copy of remaining players
    available = [p for p in remaining_players if p not in lineup]

    # Sort by value score
    available.sort(key=lambda x: x.get('value_score', x['projection'] / (x['salary'] / 1000)), reverse=True)

    # Fill remaining positions
    for pos, needed in positions_needed.items():
        candidates = [p for p in available if p['position'] == pos]

        added = 0
        for player in candidates:
            if added < needed:
                # Check constraints
                new_salary = current_salary + player['salary']
                remaining_spots = 10 - len(lineup) - 1
                min_remaining = remaining_spots * 2500

                new_team_count = teams_used.get(player['team'], 0) + 1

                if (new_salary <= 50000 - min_remaining and
                        new_team_count <= 5):
                    lineup.append(player)
                    current_salary = new_salary
                    teams_used[player['team']] = new_team_count
                    positions_filled[pos] = positions_filled.get(pos, 0) + 1
                    available.remove(player)
                    added += 1

        # If we couldn't fill required positions, fail
        if added < needed:
            return False

    return len(lineup) == 10

def build_ownership_balanced(players):
    """Fallback: Build with balanced ownership"""
    # Create tiers
    high = [p for p in players if p['ownership'] >= 25]
    mid = [p for p in players if 15 <= p['ownership'] < 25]
    low = [p for p in players if p['ownership'] < 15]

    # Sort each by value
    for tier in [high, mid, low]:
        tier.sort(key=lambda x: x['value_score'], reverse=True)

    # Combine with weights
    pool = []
    pool.extend(high[:6])  # 6 high owned
    pool.extend(mid[:8])  # 3 mid owned
    pool.extend(low[:6])  # 1 low owned

    return build_from_pool_with_requirements(pool, 'ownership_balanced')


def build_by_balanced_metrics(players):
    """Build using balanced scoring metrics"""
    for p in players:
        p['balanced_metric'] = (
                p['projection'] * 0.4 +
                p['floor'] * 0.3 +
                p['value_score'] * 5 * 0.3
        )

    return build_by_metric_with_requirements(players, 'balanced_metric', 'balanced_optimal')


def build_value_position_priority(players):
    """Build prioritizing scarce positions with value"""
    # Group by position
    position_groups = defaultdict(list)
    for p in players:
        position_groups[p['position']].append(p)

    # Sort each group by value
    for pos, group in position_groups.items():
        group.sort(key=lambda x: x['value_score'], reverse=True)

    # Build lineup position by position
    lineup = []
    salary = 0
    teams_used = defaultdict(int)

    position_order = ['C', 'SS', '2B', '3B', '1B', 'P', 'P', 'OF', 'OF', 'OF']

    for pos in position_order:
        candidates = position_groups[pos]

        for p in candidates:
            if (p not in lineup and
                    salary + p['salary'] <= 50000 - (10 - len(lineup) - 1) * 2800 and
                    teams_used.get(p['team'], 0) < 5):
                lineup.append(p)
                salary += p['salary']
                teams_used[p['team']] = teams_used.get(p['team'], 0) + 1
                break

    if len(lineup) == 10:
        result = create_lineup_dict(lineup, 'value_position')
        return optimize_salary_usage(result, players, 'value_position')

    return None


def build_balanced_relaxed(players):
    """Final fallback with very relaxed constraints"""
    # Just get best available at each position
    lineup = []
    salary = 0
    teams_used = defaultdict(int)

    position_requirements = [
        ('P', 2), ('C', 1), ('1B', 1), ('2B', 1),
        ('3B', 1), ('SS', 1), ('OF', 3)
    ]

    for pos, needed in position_requirements:
        candidates = [p for p in players
                      if p['position'] == pos and p not in lineup]
        candidates.sort(key=lambda x: x['projection'], reverse=True)

        added = 0
        for p in candidates:
            if (added < needed and
                    salary + p['salary'] <= 50000 and
                    teams_used.get(p['team'], 0) < 5):
                lineup.append(p)
                salary += p['salary']
                teams_used[p['team']] = teams_used.get(p['team'], 0) + 1
                added += 1

    if len(lineup) == 10:
        result = create_lineup_dict(lineup, 'balanced_relaxed')
        return optimize_salary_usage(result, players, 'balanced_relaxed')

    return None




# ========== BASELINE STRATEGIES (Keep for comparison) ==========



def build_value_floor(players):
    """EXISTING - Baseline comparison"""

    def floor_score(player, relaxation=0):
        floor_weight = 0.6 - (relaxation * 0.1)
        value_weight = 0.4 + (relaxation * 0.1)

        return (player.get('floor', 5) * floor_weight +
                player.get('value_score', 2) * value_weight)

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, floor_score, 'value_floor'
    )


# ========== MATCHUP-BASED STRATEGIES ==========

def build_matchup_optimal(players):
    """Best matchups only - low K% pitchers, platoon advantage"""

    def matchup_score(player, relaxation=0):
        if player['position'] == 'P':
            # Pitchers: Just use projection
            return player['projection']
        else:
            # Hitters: Heavy matchup focus
            base_score = player.get('matchup_projection', player['projection'])

            # Bonus for good matchups
            if player.get('platoon_advantage', 0) > 0:
                platoon_bonus = 1.2
            else:
                platoon_bonus = 0.9 + (relaxation * 0.2)

            # Penalty for facing elite pitchers
            opp_k_rate = player.get('opp_pitcher_k_rate', 22)
            if opp_k_rate > 26:
                k_penalty = 0.8 + (relaxation * 0.3)
            elif opp_k_rate < 20:
                k_penalty = 1.2
            else:
                k_penalty = 1.0

            return base_score * platoon_bonus * k_penalty

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, matchup_score, 'matchup_optimal'
    )


def build_platoon_stackers(players):
    """Target hitters with platoon advantage + mini-stacks"""

    def platoon_stack_score(player, relaxation=0):
        if player['position'] == 'P':
            return player['projection']

        # Base score
        score = player['projection']

        # Big bonus for platoon advantage
        platoon_adv = player.get('platoon_advantage', 0)
        if platoon_adv > 0:
            score *= (1.3 + platoon_adv * 2)
        else:
            score *= (0.8 + relaxation * 0.3)

        # Team stacking bonus (will naturally create mini-stacks)
        # This will be handled by BudgetAdvisor correlation detection

        return score

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, platoon_stack_score, 'platoon_stackers'
    )


def build_pitcher_matchup_fade(players):
    """Avoid hitters vs elite pitchers (K% > 26)"""

    def fade_elite_score(player, relaxation=0):
        if player['position'] == 'P':
            # Prefer high K% pitchers
            k_bonus = player.get('k_rate', 20) / 20
            return player['projection'] * k_bonus
        else:
            # Heavily penalize facing elite pitchers
            opp_k_rate = player.get('opp_pitcher_k_rate', 22)

            if opp_k_rate > 26:
                return player['projection'] * (0.3 + relaxation * 0.5)
            elif opp_k_rate > 24:
                return player['projection'] * 0.8
            else:
                return player['projection'] * 1.1

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, fade_elite_score, 'pitcher_matchup_fade'
    )


def build_weak_pitcher_target(players):
    """Stack against pitchers with ERA > 4.5"""

    def weak_pitcher_score(player, relaxation=0):
        if player['position'] == 'P':
            return player['projection']

        # Target hitters facing bad pitchers
        opp_era = player.get('opp_pitcher_era', 3.8)
        opp_whip = player.get('opp_pitcher_whip', 1.2)

        if opp_era > 4.5:
            era_bonus = 1.5
        elif opp_era > 4.0:
            era_bonus = 1.2
        else:
            era_bonus = 0.9 + (relaxation * 0.2)

        if opp_whip > 1.4:
            whip_bonus = 1.3
        else:
            whip_bonus = 1.0

        return player['projection'] * era_bonus * whip_bonus

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, weak_pitcher_score, 'weak_pitcher_target'
    )


def build_matchup_value(players):
    """Best value plays with good matchups"""

    def matchup_value_score(player, relaxation=0):
        # Combine value with matchup
        value_base = player.get('value_score', 2)

        if player['position'] == 'P':
            return value_base * player['projection'] / 10
        else:
            # Matchup multiplier
            platoon_mult = 1.0 + player.get('platoon_advantage', 0)
            opp_k_rate = player.get('opp_pitcher_k_rate', 22)

            if opp_k_rate < 20:
                k_mult = 1.2
            elif opp_k_rate > 25:
                k_mult = 0.8 + (relaxation * 0.3)
            else:
                k_mult = 1.0

            return value_base * platoon_mult * k_mult * player['projection'] / 10

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, matchup_value_score, 'matchup_value'
    )


# ========== RECENT FORM STRATEGIES ==========

def build_hot_players_only(players):
    """Only players with form_rating > 70"""

    def hot_form_score(player, relaxation=0):
        form_threshold = 70 - (relaxation * 20)  # Relax to 50 if needed

        form_rating = player.get('form_rating', 50)
        if form_rating < form_threshold:
            return 0  # Exclude cold players

        # Score based on how hot they are
        form_multiplier = form_rating / 50  # 1.4x to 2.0x for hot players

        return player['projection'] * form_multiplier

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, hot_form_score, 'hot_players_only'
    )


def build_consistency_kings(players):
    """High consistency score (> 80) only"""

    def consistency_score(player, relaxation=0):
        consistency_threshold = 80 - (relaxation * 30)

        consistency = player.get('consistency', 50)
        if consistency < consistency_threshold:
            return player['projection'] * 0.5  # Penalize inconsistent

        # Bonus for consistency
        consistency_mult = 1.0 + (consistency - 50) / 100  # Up to 1.5x

        return player['projection'] * consistency_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, consistency_score, 'consistency_kings'
    )


def build_trending_up(players):
    """Players with 'rising' trend only"""

    def trending_score(player, relaxation=0):
        trend = player.get('trend', 'stable')

        if trend == 'rising':
            trend_mult = 1.4
        elif trend == 'stable':
            trend_mult = 1.0 + (relaxation * 0.2)
        else:  # falling
            trend_mult = 0.5 + (relaxation * 0.4)

        # Also consider recent average vs projection
        recent_avg = player.get('recent_avg', player['projection'])
        if recent_avg > player['projection']:
            outperform_mult = 1.2
        else:
            outperform_mult = 0.9

        return player['projection'] * trend_mult * outperform_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, trending_score, 'trending_up'
    )


def build_form_plus_matchup(players):
    """Hot players + good matchups combo"""

    def form_matchup_score(player, relaxation=0):
        # Form component
        form_rating = player.get('form_rating', 50)
        form_mult = form_rating / 50 if form_rating > 50 else 0.8

        # Matchup component
        if player['position'] == 'P':
            matchup_mult = 1.0
        else:
            platoon_mult = 1.0 + player.get('platoon_advantage', 0)
            opp_k_rate = player.get('opp_pitcher_k_rate', 22)
            k_mult = 1.2 if opp_k_rate < 20 else (0.8 if opp_k_rate > 26 else 1.0)
            matchup_mult = platoon_mult * k_mult

        return player['projection'] * form_mult * matchup_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, form_matchup_score, 'form_plus_matchup'
    )


# ========== ADVANCED METRICS STRATEGIES ==========

def build_woba_warriors(players):
    """Highest wOBA hitters + solid pitchers"""

    def woba_score(player, relaxation=0):
        if player['position'] == 'P':
            # For pitchers, use K-BB ratio
            k_bb_ratio = player.get('k_rate', 20) / (player.get('bb_rate', 8) + 1)
            return player['projection'] * (k_bb_ratio / 2.5)
        else:
            # For hitters, wOBA is king
            woba = player.get('woba', .320)
            woba_mult = woba / .320  # Normalize around average

            # Recent wOBA matters too
            recent_woba = player.get('last_7_woba', woba)
            if recent_woba > woba:
                recent_mult = 1.1
            else:
                recent_mult = 0.95

            return player['projection'] * woba_mult * recent_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, woba_score, 'woba_warriors'
    )


def build_k_rate_safety(players):
    """Low K% hitters + high K% pitchers"""

    def k_safety_score(player, relaxation=0):
        if player['position'] == 'P':
            # Want high K% pitchers
            k_rate = player.get('k_rate', 20)
            k_bonus = k_rate / 20  # 1.0x for average, 1.5x for elite
            return player['projection'] * k_bonus
        else:
            # Want low K% hitters for safety
            hitter_k_rate = player.get('k_rate', 22)

            if hitter_k_rate < 18:
                k_safety = 1.3
            elif hitter_k_rate < 22:
                k_safety = 1.1
            elif hitter_k_rate < 26:
                k_safety = 0.9
            else:
                k_safety = 0.7 + (relaxation * 0.3)

            return player['projection'] * k_safety

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, k_safety_score, 'k_rate_safety'
    )


def build_statcast_studs(players):
    """Hard hit rate + barrel rate focus"""

    def statcast_score(player, relaxation=0):
        if player['position'] == 'P':
            # For pitchers, use swinging strike rate
            swstr = player.get('swstr_rate', 10)
            return player['projection'] * (swstr / 10)
        else:
            # Statcast quality metrics
            hard_hit = player.get('hard_hit_rate', 35)
            barrel = player.get('barrel_rate', 7)

            # Quality of contact score
            quality_score = (hard_hit / 35) * (barrel / 7)

            # Expected vs actual
            xwoba = player.get('xwoba', player.get('woba', .320))
            woba = player.get('woba', .320)

            if xwoba > woba:  # Due for positive regression
                regression_mult = 1.1
            else:
                regression_mult = 0.95

            return player['projection'] * quality_score * regression_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, statcast_score, 'statcast_studs'
    )


def build_pitcher_dominance(players):
    """Elite K/BB ratio pitchers"""

    def pitcher_dom_score(player, relaxation=0):
        if player['position'] == 'P':
            # K/BB ratio is key
            k_rate = player.get('k_rate', 20)
            bb_rate = player.get('bb_rate', 8)
            k_bb_ratio = k_rate / (bb_rate + 1)

            # WHIP matters too
            whip = player.get('whip', 1.25)
            whip_mult = 2 - whip  # 1.0x for 1.00 WHIP, 0.5x for 1.50

            return player['projection'] * (k_bb_ratio / 2.5) * whip_mult
        else:
            # Just standard for hitters
            return player['projection'] * player.get('value_score', 2) / 2

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, pitcher_dom_score, 'pitcher_dominance'
    )


# ========== GAME ENVIRONMENT STRATEGIES ==========

def build_vegas_sharp(players):
    """High totals (9+) for hitters, low for pitchers"""

    def vegas_sharp_score(player, relaxation=0):
        game_total = player.get('game_total', 8.5)

        if player['position'] == 'P':
            # Pitchers want LOW totals
            if game_total < 7.5:
                total_mult = 1.4
            elif game_total < 8.5:
                total_mult = 1.2
            elif game_total > 9.5:
                total_mult = 0.7 + (relaxation * 0.3)
            else:
                total_mult = 1.0
        else:
            # Hitters want HIGH totals
            if game_total > 10:
                total_mult = 1.5
            elif game_total > 9:
                total_mult = 1.3
            elif game_total < 8:
                total_mult = 0.7 + (relaxation * 0.3)
            else:
                total_mult = 1.0

        return player['projection'] * total_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, vegas_sharp_score, 'vegas_sharp'
    )


def build_park_adjusted_value(players):
    """Best value using park-adjusted projections"""

    def park_value_score(player, relaxation=0):
        # Use park-adjusted projection
        park_proj = player.get('park_adjusted_projection', player['projection'])

        # Calculate park-adjusted value
        park_value = park_proj / (player['salary'] / 1000)

        # Extra bonus for extreme parks
        park_factor = player.get('park_factor', 1.0)
        if park_factor > 1.1:  # Hitter's park
            if player['position'] != 'P':
                park_value *= 1.1
        elif park_factor < 0.95:  # Pitcher's park
            if player['position'] == 'P':
                park_value *= 1.1

        return park_value * park_proj / 10

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, park_value_score, 'park_adjusted_value'
    )


def build_game_stack_cash(players):
    """2-3 players from highest total game"""
    # Analyze games to find highest total
    game_totals = {}
    game_players = defaultdict(list)

    for p in players:
        game_id = p.get('game_id', 0)
        game_total = p.get('game_total', 8.5)
        game_totals[game_id] = game_total
        if p['position'] != 'P':
            game_players[game_id].append(p)

    # Find highest total games
    if game_totals:
        max_total = max(game_totals.values())
        target_games = [gid for gid, total in game_totals.items()
                        if total >= max_total - 0.5]
    else:
        target_games = []

    def game_stack_score(player, relaxation=0):
        # Huge bonus for target games
        if player.get('game_id') in target_games:
            game_bonus = 1.4 - (relaxation * 0.2)
        else:
            game_bonus = 1.0

        # Still care about value for cash
        value_component = player.get('value_score', 2)

        return player['projection'] * game_bonus + value_component

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, game_stack_score, 'game_stack_cash'
    )


# ========== HYBRID STRATEGIES ==========

def build_balanced_sharp(players):
    """Mix of all factors with safe floor"""

    def balanced_sharp_score(player, relaxation=0):
        # Start with base projection
        score = player['projection']

        # Form factor (weight: 20%)
        form_rating = player.get('form_rating', 50)
        form_mult = 0.8 + (form_rating / 250)  # 0.8 to 1.2

        # Matchup factor (weight: 20%)
        if player['position'] != 'P':
            platoon = 1.0 + (player.get('platoon_advantage', 0) * 2)
            opp_k = 1.2 if player.get('opp_pitcher_k_rate', 22) < 20 else 1.0
            matchup_mult = (platoon + opp_k) / 2
        else:
            matchup_mult = 1.0

        # Advanced metrics (weight: 20%)
        if player['position'] == 'P':
            metric_mult = player.get('k_rate', 20) / 20
        else:
            woba_mult = player.get('woba', .320) / .320
            k_safety = 1.2 if player.get('k_rate', 22) < 20 else 1.0
            metric_mult = (woba_mult + k_safety) / 2

        # Floor safety (weight: 20%)
        floor_ratio = player.get('floor', 5) / player['projection']
        floor_mult = 0.8 + floor_ratio * 0.4  # Higher floor = higher mult

        # Value (weight: 20%)
        value_mult = min(1.2, player.get('value_score', 2) / 2)

        # Combine all factors
        total_mult = (form_mult + matchup_mult + metric_mult + floor_mult + value_mult) / 5

        return score * total_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, balanced_sharp_score, 'balanced_sharp'
    )


def build_projection_monster(players):
    """Simply maximize matchup_projection * park_factor"""

    def projection_monster_score(player, relaxation=0):
        # Use all adjusted projections
        base_proj = player.get('matchup_projection', player['projection'])
        park_adj = player.get('park_adjusted_projection', base_proj)

        # Average the two adjustments
        final_proj = (base_proj + park_adj) / 2

        # Small value component to ensure salary efficiency
        value_bonus = player.get('value_score', 2) * 0.5

        return final_proj + value_bonus

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, projection_monster_score, 'projection_monster'
    )


# ========== STRATEGY REGISTRY ==========

CASH_STRATEGIES = {
    # Baseline
    'chalk_plus': build_chalk_plus,
    'value_floor': build_value_floor,

    # Matchup-based
    'matchup_optimal': build_matchup_optimal,
    'platoon_stackers': build_platoon_stackers,
    'pitcher_matchup_fade': build_pitcher_matchup_fade,
    'weak_pitcher_target': build_weak_pitcher_target,
    'matchup_value': build_matchup_value,

    # Recent Form
    'hot_players_only': build_hot_players_only,
    'consistency_kings': build_consistency_kings,
    'trending_up': build_trending_up,
    'form_plus_matchup': build_form_plus_matchup,

    # Advanced Metrics
    'woba_warriors': build_woba_warriors,
    'k_rate_safety': build_k_rate_safety,
    'statcast_studs': build_statcast_studs,
    'pitcher_dominance': build_pitcher_dominance,

    # Game Environment
    'vegas_sharp': build_vegas_sharp,
    'park_adjusted_value': build_park_adjusted_value,
    'game_stack_cash': build_game_stack_cash,

    # Hybrid
    'balanced_sharp': build_balanced_sharp,
    'projection_monster': build_projection_monster
}


# ========== GPP STRATEGIES ==========

# Continue in the same file after cash strategies...

# EXISTING GPP STRATEGIES (Keep for baseline)

def build_correlation_value(players):
    """EXISTING - Keep winner for baseline"""

    def correlation_value_score(player, relaxation=0):
        # Implement existing logic
        value_score = player.get('value_score', 2)

        # Bonus for high-total games
        if player.get('game_total', 8.5) > 9:
            game_bonus = 1.2
        else:
            game_bonus = 1.0

        return value_score * player['projection'] * game_bonus / 10

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, correlation_value_score, 'correlation_value'
    )


def build_ceiling_stack(players):
    """EXISTING - Keep winner for baseline"""

    def ceiling_stack_score(player, relaxation=0):
        # Heavy ceiling focus
        ceiling = player.get('ceiling', player['projection'] * 1.5)

        # Team stacking bonus handled by BudgetAdvisor
        return ceiling

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, ceiling_stack_score, 'ceiling_stack'
    )


def build_contrarian_correlation(players):
    """EXISTING - Keep for diversity"""

    def contrarian_score(player, relaxation=0):
        # Low ownership is good
        ownership_score = max(0, 50 - player.get('ownership', 20))

        # Bonus for correlation potential
        return player['projection'] * (ownership_score / 50)

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, contrarian_score, 'contrarian_correlation'
    )


# NEW GPP STRATEGIES - LEVERAGE PLAYS

def build_cold_player_leverage(players):
    """Stack cold players (contrarian)"""

    def cold_leverage_score(player, relaxation=0):
        form_rating = player.get('form_rating', 50)

        # INVERSE - cold players get bonus
        if form_rating < 30:
            cold_bonus = 1.5
        elif form_rating < 40:
            cold_bonus = 1.3
        elif form_rating < 50:
            cold_bonus = 1.1
        else:
            cold_bonus = 0.7 + (relaxation * 0.3)

        # Still need ceiling
        ceiling = player.get('ceiling', player['projection'] * 1.5)

        return ceiling * cold_bonus

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, cold_leverage_score, 'cold_player_leverage'
    )


def build_platoon_disadvantage_gpp(players):
    """Fade conventional wisdom - play disadvantages"""

    def platoon_fade_score(player, relaxation=0):
        if player['position'] == 'P':
            return player['ceiling']

        # INVERSE platoon logic
        platoon_adv = player.get('platoon_advantage', 0)

        if platoon_adv < 0:  # Disadvantage = GPP leverage
            platoon_mult = 1.3
        else:
            platoon_mult = 0.8 + (relaxation * 0.3)

        # Need ownership to be low
        ownership = player.get('ownership', 20)
        if ownership < 15:
            own_mult = 1.2
        else:
            own_mult = 0.9

        return player['ceiling'] * platoon_mult * own_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, platoon_fade_score, 'platoon_disadvantage_gpp'
    )


def build_high_k_pitcher_fade(players):
    """Stack vs strikeout pitchers (contrarian)"""

    def k_pitcher_fade_score(player, relaxation=0):
        if player['position'] == 'P':
            return player['ceiling']

        # Target hitters facing HIGH K% pitchers
        opp_k_rate = player.get('opp_pitcher_k_rate', 22)

        if opp_k_rate > 28:
            k_fade_mult = 1.4  # Max contrarian
        elif opp_k_rate > 25:
            k_fade_mult = 1.2
        else:
            k_fade_mult = 0.8 + (relaxation * 0.3)

        # Must have upside
        ceiling_ratio = player['ceiling'] / player['projection']
        if ceiling_ratio > 2:
            upside_mult = 1.2
        else:
            upside_mult = 1.0

        return player['ceiling'] * k_fade_mult * upside_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, k_pitcher_fade_score, 'high_k_pitcher_fade'
    )


def build_ownership_arbitrage(players):
    """Low ownership + hot form (hidden gems)"""

    def arbitrage_score(player, relaxation=0):
        ownership = player.get('ownership', 20)
        form_rating = player.get('form_rating', 50)

        # Want hot players that are low owned
        if ownership < 10 and form_rating > 70:
            arbitrage_mult = 2.0
        elif ownership < 15 and form_rating > 60:
            arbitrage_mult = 1.5
        elif ownership < 20 and form_rating > 50:
            arbitrage_mult = 1.2
        else:
            arbitrage_mult = 0.7 + (relaxation * 0.4)

        return player['ceiling'] * arbitrage_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, arbitrage_score, 'ownership_arbitrage'
    )


def build_narrative_fade(players):
    """Opposite of popular narratives"""

    def narrative_fade_score(player, relaxation=0):
        # Fade: hot players, good matchups, high totals
        form_rating = player.get('form_rating', 50)
        game_total = player.get('game_total', 8.5)

        # Inverse form
        if form_rating > 70:
            form_fade = 0.7
        elif form_rating < 30:
            form_fade = 1.3
        else:
            form_fade = 1.0

        # Inverse game total
        if game_total > 9.5:
            total_fade = 0.8
        elif game_total < 7.5:
            total_fade = 1.2
        else:
            total_fade = 1.0

        # Must be low owned
        if player.get('ownership', 20) > 25:
            return 0

        return player['ceiling'] * form_fade * total_fade

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, narrative_fade_score, 'narrative_fade'
    )


# ADVANCED STACKS

def build_woba_explosion(players):
    """5-man stack highest team wOBA"""
    # Find team with highest average wOBA
    team_woba = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_woba[p['team']].append(p.get('woba', .320))

    team_avg_woba = {}
    for team, wobas in team_woba.items():
        if len(wobas) >= 5:
            team_avg_woba[team] = np.mean(wobas)

    if team_avg_woba:
        best_woba_team = max(team_avg_woba, key=team_avg_woba.get)
        target_teams = [best_woba_team]
    else:
        target_teams = []

    def woba_explosion_score(player, relaxation=0):
        if player['team'] in target_teams and player['position'] != 'P':
            team_bonus = 1.8 - (relaxation * 0.3)
            woba_mult = player.get('woba', .320) / .320
            return player['ceiling'] * team_bonus * woba_mult
        else:
            return player['ceiling'] * 0.8

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, woba_explosion_score, 'woba_explosion'
    )


def build_iso_power_stack(players):
    """Stack highest ISO team"""
    # Find team with highest average ISO
    team_iso = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_iso[p['team']].append(p.get('iso', .150))

    team_avg_iso = {}
    for team, isos in team_iso.items():
        if len(isos) >= 4:
            team_avg_iso[team] = np.mean(isos)

    if team_avg_iso:
        best_iso_team = max(team_avg_iso, key=team_avg_iso.get)
        target_teams = [best_iso_team]
    else:
        target_teams = []

    def iso_power_score(player, relaxation=0):
        if player['team'] in target_teams and player['position'] != 'P':
            team_bonus = 1.6
            iso_mult = player.get('iso', .150) / .150
            return player['ceiling'] * team_bonus * iso_mult
        else:
            return player['ceiling'] * 0.9

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, iso_power_score, 'iso_power_stack'
    )


def build_barrel_rate_correlation(players):
    """Team with best barrel rates"""
    # Find team with highest barrel rates
    team_barrels = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_barrels[p['team']].append(p.get('barrel_rate', 7))

    team_avg_barrel = {}
    for team, barrels in team_barrels.items():
        if len(barrels) >= 4:
            team_avg_barrel[team] = np.mean(barrels)

    if team_avg_barrel:
        best_barrel_team = max(team_avg_barrel, key=team_avg_barrel.get)
        target_teams = [best_barrel_team]
    else:
        target_teams = []

    def barrel_correlation_score(player, relaxation=0):
        if player['team'] in target_teams and player['position'] != 'P':
            team_bonus = 1.5
            barrel_mult = player.get('barrel_rate', 7) / 7
            hard_hit_mult = player.get('hard_hit_rate', 35) / 35
            return player['ceiling'] * team_bonus * barrel_mult * hard_hit_mult
        else:
            return player['ceiling']

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, barrel_correlation_score, 'barrel_rate_correlation'
    )


def build_rising_team_stack(players):
    """All players trending up from one team"""
    # Find teams with most "rising" players
    team_trends = defaultdict(list)

    for p in players:
        if p['position'] != 'P':
            team_trends[p['team']].append(p.get('trend', 'stable'))

    team_rising_counts = {}
    for team, trends in team_trends.items():
        rising_count = sum(1 for t in trends if t == 'rising')
        if rising_count >= 3:
            team_rising_counts[team] = rising_count

    if team_rising_counts:
        best_trending_team = max(team_rising_counts, key=team_rising_counts.get)
        target_teams = [best_trending_team]
    else:
        target_teams = []

    def rising_team_score(player, relaxation=0):
        if player['team'] in target_teams:
            if player.get('trend') == 'rising':
                trend_mult = 1.8
            else:
                trend_mult = 1.2  # Still stack team

            return player['ceiling'] * trend_mult
        else:
            return player['ceiling'] * 0.9

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, rising_team_score, 'rising_team_stack'
    )


def build_matchup_leverage_stack(players):
    """Stack vs worst pitcher"""
    # Find worst pitchers
    pitcher_quality = {}

    for p in players:
        if p['position'] == 'P':
            quality_score = (50 - p.get('era', 3.8) * 10) + (50 - p.get('whip', 1.25) * 30)
            pitcher_quality[p['id']] = {
                'score': quality_score,
                'team': p['team']
            }

    # Find opposing teams to worst pitchers
    target_teams = []
    if pitcher_quality:
        worst_pitchers = sorted(pitcher_quality.items(), key=lambda x: x[1]['score'])[:3]

        # Find opposing teams
        for pitcher_id, pitcher_info in worst_pitchers:
            pitcher_team = pitcher_info['team']
            # Find hitters facing this pitcher
            for p in players:
                if (p['position'] != 'P' and
                        p.get('opp_pitcher_id') == pitcher_id):
                    if p['team'] not in target_teams:
                        target_teams.append(p['team'])

    def matchup_leverage_score(player, relaxation=0):
        if player['team'] in target_teams and player['position'] != 'P':
            return player['ceiling'] * 1.8
        else:
            return player['ceiling'] * 0.9

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, matchup_leverage_score, 'matchup_leverage_stack'
    )


# ENVIRONMENTAL GPP

def build_park_factor_max(players):
    """Coors or bust strategy"""
    # Find highest park factor
    park_factors = set()
    for p in players:
        park_factors.add(p.get('park_factor', 1.0))

    if park_factors:
        max_park = max(park_factors)
        # Target games in best parks
        target_parks = [p for p in players if p.get('park_factor', 1.0) >= max_park - 0.05]
    else:
        target_parks = []

    def park_max_score(player, relaxation=0):
        park_factor = player.get('park_factor', 1.0)

        if park_factor >= 1.1:  # Extreme hitter's park
            if player['position'] != 'P':
                park_mult = 2.0
            else:
                park_mult = 0.5  # Avoid pitchers in hitter parks
        elif park_factor <= 0.95:  # Extreme pitcher's park
            if player['position'] == 'P':
                park_mult = 1.5
            else:
                park_mult = 0.7
        else:
            park_mult = 1.0

        return player['ceiling'] * park_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, park_max_score, 'park_factor_max'
    )


def build_vegas_explosion(players):
    """Only 11+ total games"""

    def vegas_explosion_score(player, relaxation=0):
        game_total = player.get('game_total', 8.5)

        if game_total >= 11:
            total_mult = 2.0
        elif game_total >= 10:
            total_mult = 1.5
        elif game_total >= 9:
            total_mult = 1.1 + (relaxation * 0.3)
        else:
            total_mult = 0.5 + (relaxation * 0.4)

        # Pitchers in high-total games are risky
        if player['position'] == 'P' and game_total > 10:
            total_mult *= 0.6

        return player['ceiling'] * total_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, vegas_explosion_score, 'vegas_explosion'
    )


def build_perfect_storm(players):
    """Hot team + good matchup + high total"""

    def perfect_storm_score(player, relaxation=0):
        # Multiple factors must align
        form_check = player.get('form_rating', 50) > 60
        total_check = player.get('game_total', 8.5) > 9

        if player['position'] != 'P':
            matchup_check = player.get('platoon_advantage', 0) > 0
            opp_pitcher_check = player.get('opp_pitcher_era', 3.8) > 4.0
        else:
            matchup_check = True
            opp_pitcher_check = True

        # Count positive factors
        factors = sum([form_check, total_check, matchup_check, opp_pitcher_check])

        if factors >= 3:
            storm_mult = 1.8
        elif factors >= 2:
            storm_mult = 1.3
        else:
            storm_mult = 0.7 + (relaxation * 0.4)

        return player['ceiling'] * storm_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, perfect_storm_score, 'perfect_storm'
    )


# UNIQUE BUILDS

def build_stars_and_scrubs_extreme(players):
    """3 studs + mins"""

    def stars_scrubs_score(player, relaxation=0):
        salary = player['salary']

        # Define stars and scrubs
        if salary >= 5000:  # Stars
            star_mult = 1.5
        elif salary <= 3200:  # Scrubs
            scrub_mult = 1.3
        else:  # Middle - avoid
            return player['ceiling'] * (0.4 + relaxation * 0.5)

        # Stars need ceiling
        if salary >= 5000:
            return player['ceiling'] * star_mult
        else:
            # Scrubs need some projection
            return player['projection'] * scrub_mult

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, stars_scrubs_score, 'stars_and_scrubs_extreme'
    )


def build_multi_stack_mayhem(players):
    """3 different 2-man stacks"""

    # This is handled by BudgetAdvisor detecting correlation patterns
    # We just need to encourage mini-correlations

    def multi_stack_score(player, relaxation=0):
        # Count team representation
        team_quality = 0

        # Bonus for teams with good hitters
        team_hitters = [p for p in players if p['team'] == player['team'] and p['position'] != 'P']
        if len(team_hitters) >= 2:
            avg_proj = np.mean([h['projection'] for h in team_hitters])
            if avg_proj > 8:
                team_quality = 1.3
            else:
                team_quality = 1.1
        else:
            team_quality = 0.8

        return player['ceiling'] * team_quality

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, multi_stack_score, 'multi_stack_mayhem'
    )


def build_pitcher_stack_combo(players):
    """Ace + opposing team stack"""
    # Find best pitchers
    top_pitchers = sorted([p for p in players if p['position'] == 'P'],
                          key=lambda x: x['projection'], reverse=True)[:5]

    if top_pitchers:
        # Get opposing teams
        target_teams = []
        for pitcher in top_pitchers:
            # Find hitters facing this pitcher
            for p in players:
                if (p['position'] != 'P' and
                        p.get('opp_pitcher_id') == pitcher['id']):
                    if p['team'] not in target_teams:
                        target_teams.append(p['team'])
    else:
        target_teams = []

    def pitcher_combo_score(player, relaxation=0):
        if player['position'] == 'P':
            # Favor top pitchers
            if player in top_pitchers:
                return player['projection'] * 1.5
            else:
                return player['projection'] * 0.8
        else:
            # Favor opposing team
            if player['team'] in target_teams:
                return player['ceiling'] * 1.4
            else:
                return player['ceiling'] * 0.9

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    return build_adaptive_lineup(
        players, position_requirements, pitcher_combo_score, 'pitcher_stack_combo'
    )


# ========== UPDATED STRATEGY REGISTRY ==========

GPP_STRATEGIES = {
    # Existing winners
    'correlation_value': build_correlation_value,
    'ceiling_stack': build_ceiling_stack,
    'contrarian_correlation': build_contrarian_correlation,

    # Leverage plays
    'cold_player_leverage': build_cold_player_leverage,
    'platoon_disadvantage_gpp': build_platoon_disadvantage_gpp,
    'high_k_pitcher_fade': build_high_k_pitcher_fade,
    'ownership_arbitrage': build_ownership_arbitrage,
    'narrative_fade': build_narrative_fade,

    # Advanced stacks
    'woba_explosion': build_woba_explosion,
    'iso_power_stack': build_iso_power_stack,
    'barrel_rate_correlation': build_barrel_rate_correlation,
    'rising_team_stack': build_rising_team_stack,
    'matchup_leverage_stack': build_matchup_leverage_stack,

    # Environmental
    'park_factor_max': build_park_factor_max,
    'vegas_explosion': build_vegas_explosion,
    'perfect_storm': build_perfect_storm,

    # Unique builds
    'stars_and_scrubs_extreme': build_stars_and_scrubs_extreme,
    'multi_stack_mayhem': build_multi_stack_mayhem,
    'pitcher_stack_combo': build_pitcher_stack_combo
}






# ========== LINEUP BUILDING DISPATCHER ==========
def build_lineup(players, strategy_config, format_type, slate_size):
    """Route to appropriate builder - ALL strategies available"""
    strategy_type = strategy_config.get('type', 'unknown')

    # ALL classic strategies for ELITE test
    all_classic_builders = {
        # CASH STRATEGIES from ELITE_STRATEGIES
        'matchup_optimal': build_matchup_optimal,
        'elite_cash': build_elite_cash,
        'chalk_plus': build_chalk_plus,
        'value_floor': build_value_floor,
        'balanced_sharp': build_balanced_sharp,
        'pitcher_dominance': build_pitcher_dominance,
        'game_stack_cash': build_game_stack_cash,
        'projection_monster': build_projection_monster,

        # GPP STRATEGIES from ELITE_STRATEGIES
        'stars_and_scrubs_extreme': build_stars_and_scrubs_extreme,
        'cold_player_leverage': build_cold_player_leverage,
        'woba_explosion': build_woba_explosion,
        'rising_team_stack': build_rising_team_stack,
        'iso_power_stack': build_iso_power_stack,
        'leverage_theory': build_leverage_theory,
        'smart_stack': build_smart_stack,
        'ceiling_stack': build_ceiling_stack,
        'correlation_value': build_correlation_value,
        'barrel_rate_correlation': build_barrel_rate_correlation,
        'multi_stack_mayhem': build_multi_stack_mayhem,
        'matchup_leverage_stack': build_matchup_leverage_stack,
        'pitcher_stack_combo': build_pitcher_stack_combo,
        'vegas_explosion': build_vegas_explosion,
        'high_k_pitcher_fade': build_high_k_pitcher_fade,

        # Also include these in case
        'balanced_optimal': build_balanced_optimal,
        'contrarian_correlation': build_contrarian_correlation,
        'diversified_chalk': build_diversified_chalk,
        'safe_correlation': build_safe_correlation,
        'multi_stack': build_multi_stack,
    }

    # Showdown strategies
    showdown_builders = {
        'balanced_showdown': build_balanced_showdown,
        'leverage_captain': build_leverage_captain
    }

    # Choose builders based on format
    if format_type == 'showdown':
        builders = showdown_builders
    else:  # classic
        builders = all_classic_builders

    builder = builders.get(strategy_type)
    if builder:
        try:
            lineup = builder(players)
            return lineup
        except Exception as e:
            print(f"Error in {strategy_type}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    print(f"Unknown strategy type: {strategy_type}")
    return None

def debug_single_strategy(strategy_name, slate_size='small'):
    """Debug a single strategy"""
    print(f"\n{'=' * 60}")
    print(f"Testing {strategy_name} on {slate_size} slate")
    print('=' * 60)

    # Generate test slate
    slate = generate_slate(1, 'classic', slate_size)

    # Get strategy config
    strategy_config = None
    for contest_type in ['cash', 'gpp']:
        if strategy_name in ROBUST_STRATEGIES['classic'].get(slate_size, {}).get(contest_type, {}):
            strategy_config = ROBUST_STRATEGIES['classic'][slate_size][contest_type][strategy_name]
            break

    if not strategy_config:
        print(f"Strategy {strategy_name} not found for {slate_size}")
        return

    # Try to build
    lineup = build_lineup(slate['players'], strategy_config, 'classic', slate_size)

    if lineup:
        print(f"\n✅ SUCCESS!")
        print(f"   Salary: ${lineup['salary']:,}")
        print(f"   Projection: {lineup['projection']:.1f}")
        print(f"   Players: {len(lineup['players'])}")
    else:
        print(f"\n❌ FAILED to build lineup")


# Run this at the bottom of your file
if __name__ == "__main__":
    print("Debugging strategies...")
    debug_single_strategy('balanced_optimal', 'small')
    debug_single_strategy('smart_stack', 'small')
    debug_single_strategy('contrarian_correlation', 'medium')
    debug_single_strategy('multi_stack', 'large')
# ========== FIELD GENERATION ==========
def generate_field(slate, field_size, contest_type):
    """Generate realistic field of opponents - COMPLETE FIXED VERSION"""
    field_lineups = []
    target_opponents = field_size - 1  # 99 for 100-person, 999 for 1000-person

    # Validate inputs
    if not slate or not slate.get('players'):
        print(f"ERROR: Invalid slate provided to generate_field")
        return []

    if field_size < 2:
        print(f"ERROR: Invalid field size: {field_size}")
        return []

  #  print(f"DEBUG: Generating {target_opponents} opponents for {contest_type} contest")

    try:
        # Realistic:
        if contest_type == 'cash':
            skill_distribution = {
                'sharp': 0.08,  # 8% (was 20%)
                'good': 0.27,  # 27% (was 50%)
                'average': 0.45,  # 45% (was 25%)
                'weak': 0.20  # 20% (was 5%)
            }
        else:  # GPP
            skill_distribution = {
                'sharp': 0.05,  # 5% sharp
                'good': 0.15,  # 15% good
                'average': 0.50,  # 50% average
                'weak': 0.30  # 30% weak
            }

        # Track generation stats
        generation_stats = {
            'attempted': 0,
            'successful': 0,
            'failed': 0,
            'simple_fallback': 0,
            'emergency': 0,
            'duplicates': 0
        }

        # Generate opponents by skill level
        for i in range(target_opponents):
            generation_stats['attempted'] += 1

            # Determine skill level
            rand = random.random()
            cumulative = 0
            skill_level = 'average'

            for level, pct in skill_distribution.items():
                cumulative += pct
                if rand < cumulative:
                    skill_level = level
                    break

            # Build opponent lineup based on skill
            lineup = None

            if skill_level == 'sharp':
                # Sharp players use sophisticated strategies
                if contest_type == 'cash':
                    strategies = ['balanced_optimal', 'value_floor', 'correlation_value']
                else:
                    strategies = ['smart_stack', 'ceiling_stack', 'leverage_theory']

                strategy = random.choice(strategies)
                strategy_config = {'type': strategy}

                # Try to build with error handling
                try:
                    lineup = build_lineup(slate['players'], strategy_config, slate['format'], slate['slate_size'])
                except Exception as e:
                    print(f"DEBUG: Sharp strategy {strategy} failed: {e}")
                    lineup = None

            elif skill_level == 'good':
                # Good players use decent strategies
                try:
                    lineup = build_good_opponent_lineup(slate['players'], contest_type)
                except Exception as e:
                    print(f"DEBUG: Good opponent lineup failed: {e}")
                    lineup = None

            elif skill_level == 'average':
                # Average players use basic strategies
                try:
                    lineup = build_average_opponent_lineup(slate['players'])
                except Exception as e:
                    print(f"DEBUG: Average opponent lineup failed: {e}")
                    lineup = None

            else:  # weak
                # Weak players make mistakes
                try:
                    lineup = build_weak_opponent_lineup(slate['players'])
                except Exception as e:
                    print(f"DEBUG: Weak opponent lineup failed: {e}")
                    lineup = None

            # If strategy failed, try simple builder
            if not lineup:
                generation_stats['failed'] += 1
                try:
                    lineup = build_simple_lineup(slate['players'])
                    if lineup:
                        generation_stats['simple_fallback'] += 1
                except Exception as e:
                    print(f"DEBUG: Simple lineup also failed: {e}")
                    lineup = None

            if lineup:
                # Adjust projection based on skill
                skill_multipliers = {
                    'sharp': random.uniform(1.02, 1.08),
                    'good': random.uniform(0.98, 1.02),
                    'average': random.uniform(0.92, 0.98),
                    'weak': random.uniform(0.75, 0.90)
                }

                lineup['projection'] *= skill_multipliers.get(skill_level, 1.0)
                lineup['skill_level'] = skill_level
                field_lineups.append(lineup)
                generation_stats['successful'] += 1

       # print(f"DEBUG: After main generation loop - have {len(field_lineups)}/{target_opponents} opponents")

        # PHASE 2: Fill remaining with simple lineups
        attempts = 0
        max_attempts = target_opponents * 2

        while len(field_lineups) < target_opponents and attempts < max_attempts:
            attempts += 1
            try:
                lineup = build_simple_lineup(slate['players'])
                if lineup:
                    lineup['projection'] *= random.uniform(0.85, 1.05)
                    lineup['skill_level'] = 'filler'
                    field_lineups.append(lineup)
                    generation_stats['emergency'] += 1
            except Exception as e:
                # print(f"DEBUG: Emergency lineup generation failed: {e}")
                pass  # <-- Add this line

        # PHASE 3: Last resort - duplicate existing lineups
        while len(field_lineups) < target_opponents:
            if field_lineups:
                try:
                    base_lineup = random.choice(field_lineups)
                    # Create a proper deep copy
                    new_lineup = {
                        'players': base_lineup['players'].copy(),
                        'salary': base_lineup['salary'],
                        'projection': base_lineup['projection'] * random.uniform(0.90, 1.10),
                        'ownership': base_lineup.get('ownership', 15),
                        'strategy': base_lineup.get('strategy', 'duplicate'),
                        'ceiling': base_lineup.get('ceiling', base_lineup['projection'] * 1.5),
                        'floor': base_lineup.get('floor', base_lineup['projection'] * 0.5),
                        'skill_level': 'duplicate',
                        'actual_score': 0  # Will be set during simulation
                    }
                    field_lineups.append(new_lineup)
                    generation_stats['duplicates'] += 1
                except Exception as e:
                    print(f"ERROR: Failed to duplicate lineup: {e}")
                    break
            else:
                print(f"CRITICAL ERROR: No lineups available to duplicate!")
                break

        # GUARANTEE we return exactly the right number
        if len(field_lineups) > target_opponents:
            # Too many? Trim
            field_lineups = field_lineups[:target_opponents]
        elif len(field_lineups) < target_opponents:
            print(f"WARNING: Only generated {len(field_lineups)}/{target_opponents} opponents")
            print(f"Stats: {generation_stats}")

    except Exception as e:
        print(f"CRITICAL ERROR in generate_field: {e}")
        import traceback
        traceback.print_exc()
        # Return what we have

    # Final validation
    if len(field_lineups) != target_opponents:
        print(f"WARNING: Returning {len(field_lineups)} opponents instead of {target_opponents}")

    # ALWAYS return a list (never None)
    return field_lineups


def build_simple_lineup(players):
    """Simple lineup builder that ALWAYS works - FIXED VERSION"""
    if not players:
        return None

    lineup = []
    salary = 0
    positions_filled = defaultdict(int)
    teams_used = defaultdict(int)

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Create position groups
    by_position = defaultdict(list)
    for p in players:
        if p.get('position'):
            by_position[p['position']].append(p)

    # Fill each position with best available
    for pos, req in position_requirements.items():
        candidates = by_position.get(pos, [])
        added = 0

        for player in candidates:
            if (added < req and
                    salary + player.get('salary', 5000) <= 50000 - (10 - len(lineup) - 1) * 2500 and
                    teams_used.get(player.get('team', 'UNK'), 0) < 5):

                lineup.append(player)
                salary += player.get('salary', 5000)
                positions_filled[pos] = positions_filled.get(pos, 0) + 1
                teams_used[player.get('team', 'UNK')] = teams_used.get(player.get('team', 'UNK'), 0) + 1
                added += 1

                if len(lineup) == 10:
                    return create_lineup_dict(lineup, 'simple_opponent')

    # EMERGENCY: If we don't have 10, force fill with any valid players
    if len(lineup) < 10:
        all_remaining = []
        for pos, players_list in by_position.items():
            for p in players_list:
                if p not in lineup and positions_filled.get(pos, 0) < position_requirements.get(pos, 0):
                    all_remaining.append(p)

        # Sort by salary (cheapest first) to ensure we can afford
        all_remaining.sort(key=lambda x: x.get('salary', 5000))

        for player in all_remaining:
            pos = player.get('position')
            if (len(lineup) < 10 and
                    positions_filled.get(pos, 0) < position_requirements.get(pos, 0) and
                    salary + player.get('salary', 5000) <= 50000):

                lineup.append(player)
                salary += player.get('salary', 5000)
                positions_filled[pos] = positions_filled.get(pos, 0) + 1

                if len(lineup) == 10:
                    break

    if len(lineup) < 10:
        # Only show warning if it's really a problem
        # print(f"WARNING: Simple lineup only has {len(lineup)} players")
        return None  # Don't return incomplete lineups

    return create_lineup_dict(lineup, 'simple_opponent')

def build_lineup_from_stack(stack, all_players, stack_type):
    """Complete lineup starting from stack"""
    lineup = stack.copy()
    salary = sum(p['salary'] for p in lineup)
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)

    for p in lineup:
        teams_used[p['team']] = teams_used.get(p['team'], 0) + 1
        positions_filled[p['position']] = positions_filled.get(p['position'], 0) + 1

    # Get remaining players
    remaining = [p for p in all_players if p not in lineup]

    # Smart pitcher selection based on stack type
    pitchers = [p for p in remaining if p['position'] == 'P']

    if stack_type == '5-man' or '5-team' in stack_type:
        # Prefer pitcher against the stack
        stack_team = max(teams_used.items(), key=lambda x: x[1])[0]
        opp_pitchers = [p for p in pitchers
                        if any(player['team'] == stack_team and
                               player.get('game_id') == p.get('game_id')
                               for player in stack)]
        if opp_pitchers:
            pitchers = opp_pitchers

    # Sort pitchers
    pitchers.sort(key=lambda x: x['projection'], reverse=True)

    # Add pitchers
    pitchers_needed = 2 - positions_filled.get('P', 0)
    for p in pitchers[:pitchers_needed]:
        if salary + p['salary'] <= 50000 - (10 - len(lineup) - 1) * 2800:
            lineup.append(p)
            salary += p['salary']
            positions_filled['P'] = positions_filled.get('P', 0) + 1
            teams_used[p['team']] = teams_used.get(p['team'], 0) + 1

    # Fill remaining positions
    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    remaining = [p for p in all_players if p not in lineup]
    remaining.sort(key=lambda x: x['value_score'], reverse=True)

    for pos, required in position_requirements.items():
        while positions_filled.get(pos, 0) < required:
            candidates = [p for p in remaining
                          if p['position'] == pos
                          and salary + p['salary'] <= 50000
                          and teams_used.get(p['team'], 0) < 5]

            if not candidates:
                return None

            player = candidates[0]
            lineup.append(player)
            salary += player['salary']
            positions_filled[pos] = positions_filled.get(pos, 0) + 1
            teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
            remaining.remove(player)

    if len(lineup) == 10 and validate_lineup(lineup):
        return create_lineup_dict(lineup, 'smart_stack')

    return None


def build_good_opponent_lineup(players, contest_type):
    """Build lineup for good opponent"""
    if contest_type == 'cash':
        # Good cash player - focuses on floor and value
        for p in players:
            p['good_cash_score'] = p['floor'] * 0.5 + p['value_score'] * 3 * 0.5

        return build_by_metric_with_requirements(players, 'good_cash_score', 'good_opponent')
    else:
        # Good GPP player - some correlation
        team_players = defaultdict(list)
        for p in players:
            if p['position'] != 'P':
                team_players[p['team']].append(p)

        # Find a decent stack
        for team, team_list in team_players.items():
            if len(team_list) >= 4:
                stack = sorted(team_list, key=lambda x: x['projection'], reverse=True)[:4]
                lineup = build_lineup_from_stack(stack, players, 'good_gpp')
                if lineup:
                    return lineup

        # Fallback
        return build_by_metric_with_requirements(players, 'projection', 'good_opponent')


def build_average_opponent_lineup(players):
    """Build lineup for average opponent"""
    # Simple projection-based with some randomness
    players_copy = players.copy()

    # Add some randomness
    for p in players_copy:
        p['random_factor'] = random.uniform(0.8, 1.2)
        p['avg_score'] = p['projection'] * p['random_factor']

    return build_by_metric_with_requirements(players_copy, 'avg_score', 'average_opponent')


def build_weak_opponent_lineup(players):
    """Build lineup for weak opponent - makes mistakes"""
    players_copy = players.copy()

    # Weak players overvalue names, make salary mistakes
    for p in players_copy:
        # Random poor decisions
        if random.random() < 0.3:  # 30% chance of bad evaluation
            p['weak_score'] = random.uniform(5, 15)  # Random score
        else:
            p['weak_score'] = p['projection'] * random.uniform(0.5, 0.9)

    # Might not optimize salary well
    lineup = []
    salary = 0
    teams_used = defaultdict(int)
    positions_filled = defaultdict(int)

    position_requirements = {
        'P': 2, 'C': 1, '1B': 1, '2B': 1,
        '3B': 1, 'SS': 1, 'OF': 3
    }

    # Randomly sort
    random.shuffle(players_copy)

    for pos, needed in position_requirements.items():
        candidates = [p for p in players_copy
                      if p['position'] == pos and p not in lineup]

        for i in range(needed):
            if candidates:
                # Weak players might pick randomly
                if random.random() < 0.5:
                    player = random.choice(candidates[:5]) if len(candidates) > 5 else candidates[0]
                else:
                    candidates.sort(key=lambda x: x['weak_score'], reverse=True)
                    player = candidates[0]

                if salary + player['salary'] <= 50000:
                    lineup.append(player)
                    salary += player['salary']
                    teams_used[player['team']] = teams_used.get(player['team'], 0) + 1
                    positions_filled[pos] = positions_filled.get(pos, 0) + 1
                    candidates.remove(player)

    if len(lineup) == 10:
        return create_lineup_dict(lineup, 'weak_opponent')

    return None


# ========== SCORING SIMULATION ==========

def simulate_lineup_score(lineup):
    """Simulate realistic score with variance - CLEAN VERSION WITH COUNTERS"""
    base_projection = lineup['projection']

    # Initialize counters if they don't exist
    if not hasattr(simulate_lineup_score, 'event_counter'):
        simulate_lineup_score.event_counter = {
            'disasters': 0,
            'breakers': 0,
            'total_scored': 0
        }

    # Track for diagnostic test
    simulate_lineup_score.last_was_disaster = False

    simulate_lineup_score.event_counter['total_scored'] += 1

    # Add "slate breaker" possibility for GPP
    if random.random() < 0.01:  # 1% chance
        simulate_lineup_score.event_counter['breakers'] += 1
        return base_projection * random.uniform(2.5, 3.5)

    # Add "disaster" possibility
    if random.random() < 0.03:  # 3% chance
        simulate_lineup_score.event_counter['disasters'] += 1
        simulate_lineup_score.last_was_disaster = True
        return base_projection * random.uniform(0.3, 0.6)

    # Normal variance calculation
    # Game flow variance (biggest factor)
    game_flow = np.random.normal(1.0, 0.15)

    # Individual player variance
    player_variance = 1.0
    for p in lineup['players']:
        # Each player has independent variance
        player_var = np.random.normal(1.0, 0.12)
        player_variance *= player_var

    # Average out extreme variance
    player_variance = player_variance ** (1 / len(lineup['players']))

    # Correlation bonuses
    correlation_multiplier = 1.0

    # Stack bonuses
    max_stack = lineup.get('max_stack', 0)
    if max_stack >= 5:
        # 5-man stacks can boom or bust together
        stack_variance = random.choice([0.7, 0.85, 0.95, 1.0, 1.05, 1.15, 1.3, 1.5])
        correlation_multiplier *= stack_variance
    elif max_stack >= 4:
        stack_variance = random.choice([0.8, 0.9, 1.0, 1.0, 1.1, 1.2])
        correlation_multiplier *= stack_variance
    elif max_stack >= 3:
        stack_variance = random.choice([0.9, 0.95, 1.0, 1.05, 1.1])
        correlation_multiplier *= stack_variance

    # Game stack bonuses
    if lineup.get('num_games', 0) == 1:
        # Single game stack - high variance
        game_variance = random.choice([0.6, 0.8, 1.0, 1.2, 1.4])
        correlation_multiplier *= game_variance

    # Calculate final score
    score = base_projection * game_flow * player_variance * correlation_multiplier

    # Add small random factor
    score += np.random.normal(0, 3)

    # Injury/late swap simulation (slightly more common)
    if random.random() < 0.04:  # 4% chance
        affected_players = random.randint(1, 2)
        score *= (1 - affected_players * 0.1)  # Each injured player reduces score

    # Ensure reasonable bounds
    min_score = base_projection * 0.2
    max_score = base_projection * 4.0  # Allow bigger upside

    return max(min_score, min(max_score, score))

# ========== CONTEST SIMULATION ==========
def simulate_contest(slate, strategy_name, strategy_config, contest_type, field_size):
    """Simulate a single DFS contest - COMPLETE FIXED VERSION"""

    # Validate inputs
    if not slate or not slate.get('players'):
        print(f"ERROR: Invalid slate in simulate_contest")
        return None

  #  print(f"DEBUG: Simulating {strategy_name} in {contest_type} ({field_size} players)")

    # Build our lineup
    try:
        our_lineup = build_lineup(
            slate['players'],
            strategy_config,
            slate['format'],
            slate['slate_size']
        )
    except Exception as e:
    #    print(f"ERROR: Failed to build lineup for {strategy_name}: {e}")
        return None

    if not our_lineup:
   #     print(f"DEBUG: Our lineup is None for {strategy_name}")
        return None

    # Generate field
    try:
        field_lineups = generate_field(slate, field_size, contest_type)
    except Exception as e:
     #   print(f"ERROR: generate_field threw exception: {e}")
        field_lineups = []

    # Validate field
    if field_lineups is None:
      #  print(f"ERROR: generate_field returned None for {contest_type}/{field_size}")
        field_lineups = []

    if not isinstance(field_lineups, list):
     #   print(f"ERROR: generate_field returned {type(field_lineups)} instead of list")
        field_lineups = []

    # Check if we have enough opponents
    expected_opponents = field_size - 1
    if len(field_lineups) < expected_opponents * 0.8:  # Allow up to 20% shortage
        print(f"WARNING: Only {len(field_lineups)}/{expected_opponents} opponents generated")
        # Try emergency generation
        print("Attempting emergency field generation...")
        for i in range(expected_opponents - len(field_lineups)):
            try:
                emergency_lineup = build_simple_lineup(slate['players'])
                if emergency_lineup:
                    emergency_lineup['skill_level'] = 'emergency'
                    field_lineups.append(emergency_lineup)
            except:
                pass

   # print(f"DEBUG: Proceeding with {len(field_lineups)} opponents")

    # Score all lineups
    try:
        our_score = simulate_lineup_score(our_lineup)
    except Exception as e:
        print(f"ERROR: Failed to score our lineup: {e}")
        our_score = our_lineup.get('projection', 100) * random.uniform(0.8, 1.2)

    field_scores = []
    for lineup in field_lineups:
        try:
            score = simulate_lineup_score(lineup)
            field_scores.append(score)
        except Exception as e:
            # Fallback scoring
            score = lineup.get('projection', 100) * random.uniform(0.8, 1.2)
            field_scores.append(score)

    # Calculate placement
    all_scores = field_scores + [our_score]
    all_scores.sort(reverse=True)

    try:
        our_rank = all_scores.index(our_score) + 1
    except ValueError:
        print(f"ERROR: Could not find our score in rankings")
        our_rank = len(all_scores)

    percentile = ((len(all_scores) - our_rank) / len(all_scores)) * 100

    # Calculate payout
    if slate['format'] == 'showdown':
        entry_fee = 5 if contest_type == 'cash' else 3
        config = SHOWDOWN_CONFIG
    else:
        entry_fee = 10 if contest_type == 'cash' else 3
        config = CLASSIC_CONFIG

    if contest_type == 'cash':
        # Cash line at 44th percentile (top 44% cash)
        cash_line_percentile = (1 - config['cash_payout_threshold']) * 100
        if percentile >= cash_line_percentile:
            payout = entry_fee * 2  # Double up
        else:
            payout = 0
    else:  # GPP
        payout = 0
        payout_pct = our_rank / len(all_scores)

        # Check each payout tier
        for threshold, multiplier in sorted(config['gpp_payout_structure'].items()):
            if payout_pct <= threshold:
                payout = entry_fee * multiplier
                break

    profit = payout - entry_fee
    roi = (profit / entry_fee) * 100

    # Additional metrics
    win = profit > 0
    top_10 = percentile >= 90
    top_1 = percentile >= 99

    return {
        'strategy': strategy_name,
        'contest_type': contest_type,
        'field_size': field_size,
        'format': slate['format'],
        'slate_size': slate['slate_size'],
        'rank': our_rank,
        'percentile': percentile,
        'score': our_score,
        'payout': payout,
        'profit': profit,
        'roi': roi,
        'ownership': our_lineup.get('ownership', 0),
        'projection': our_lineup.get('projection', 0),
        'actual_score': our_score,
        'win': win,
        'top_10': top_10,
        'top_1': top_1,
        'cash_line': all_scores[
            int(len(all_scores) * config['cash_payout_threshold'])] if contest_type == 'cash' and all_scores else None,
        'winning_score': all_scores[0] if all_scores else 0,
        'lineup_salary': our_lineup.get('salary', 0),
        'max_stack': our_lineup.get('max_stack', 0),
        'actual_field_size': len(field_lineups) + 1,  # Include ourselves
        'expected_field_size': field_size
    }
# ========== PARALLEL PROCESSING ==========
def process_batch(args):
    """Process a batch of simulations"""
    batch_id, slate_configs, contest_configs = args
    results = []

    for slate_id, format_type, slate_size in slate_configs:
        # Generate slate
        slate = generate_slate(slate_id, format_type, slate_size)

        if not slate or not slate.get('players'):
            print(f"Warning: Failed to generate slate {slate_id}")
            continue

        # Get strategies for this configuration - FIXED LOGIC
        if format_type == 'showdown':
            # ONLY showdown strategies for showdown slates
            strategies_to_test = {}
            for contest_type in ['cash', 'gpp']:
                if 'showdown' in ROBUST_STRATEGIES and contest_type in ROBUST_STRATEGIES['showdown']:
                    strategies_to_test.update(ROBUST_STRATEGIES['showdown'][contest_type])
        else:  # classic format
            # ONLY classic strategies for classic slates
            strategies_to_test = {}
            for contest_type in ['cash', 'gpp']:
                if 'classic' in ROBUST_STRATEGIES and slate_size in ROBUST_STRATEGIES['classic']:
                    if contest_type in ROBUST_STRATEGIES['classic'][slate_size]:
                        strategies_to_test.update(ROBUST_STRATEGIES['classic'][slate_size][contest_type])

        # Test each strategy in each contest type - USING strategies_to_test!
        for strategy_name, strategy_config in strategies_to_test.items():  # <- Changed variable name here!
            for contest_type, field_size in contest_configs:
                try:
                    result = simulate_contest(
                        slate,
                        strategy_name,
                        strategy_config,
                        contest_type,
                        field_size
                    )

                    if result:
                        results.append(result)

                except Exception as e:
                    print(f"Error in {strategy_name}/{contest_type}: {str(e)}")

    return batch_id, results

# ========== ANALYSIS ==========
def comprehensive_simulation_audit():
    """Run comprehensive checks on simulation components"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE SIMULATION AUDIT")
    print("=" * 60)

    # Test 1: Lineup generation success rates
    print("\n1. Testing lineup generation...")
    test_slate = generate_slate(1, 'classic', 'medium')

    strategies = ['balanced_optimal', 'value_floor', 'smart_stack', 'game_theory_leverage']
    for strategy in strategies:
        success_count = 0
        for i in range(10):
            lineup = build_lineup(test_slate['players'], {'type': strategy}, 'classic', 'medium')
            if lineup:
                success_count += 1
        print(f"   {strategy}: {success_count}/10 successful")

    print("\n✅ Audit complete!")


def analyze_results(results):
    """Comprehensive analysis of simulation results with enhanced metrics"""

    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f'simulation_results_{timestamp}.txt'

    # Start logging output
    output_logger = OutputLogger(output_filename)
    original_stdout = sys.stdout
    sys.stdout = output_logger

    try:
        print("\n" + "=" * 80)
        print("COMPLETE ROBUST DFS SIMULATOR - RESULTS ANALYSIS")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Calculate overall metrics
        total_slates = len(set(r.get('slate_id', 0) for r in results if r))
        total_contests = len(results)
        successful_builds = sum(1 for r in results if r and r.get('lineup_salary', 0) > 0)
        completion_rate = (successful_builds / total_contests * 100) if total_contests > 0 else 0

        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   Total Slates Tested: {total_slates}")
        print(f"   Total Contests: {total_contests}")
        print(f"   Successful Lineups: {successful_builds}")
        print(f"   Completion Rate: {completion_rate:.1f}%")

        # Calculate average scores across all contests
        all_scores = [r['score'] for r in results if r and 'score' in r]
        if all_scores:
            print(f"\n📈 SCORING STATISTICS:")
            print(f"   Average Score: {np.mean(all_scores):.1f}")
            print(f"   Median Score: {np.median(all_scores):.1f}")
            print(f"   Std Dev: {np.std(all_scores):.1f}")
            print(f"   Min Score: {min(all_scores):.1f}")
            print(f"   Max Score: {max(all_scores):.1f}")

        # Group results
        by_strategy = defaultdict(list)

        for r in results:
            if r:  # Check for None results
                key = f"{r['format']}_{r['slate_size']}_{r['contest_type']}_{r['strategy']}"
                by_strategy[key].append(r)

        # Analyze by slate size and contest type
        for slate_size in ['small', 'medium', 'large']:
            print(f"\n{'=' * 80}")
            print(f"CLASSIC - {slate_size.upper()} SLATES")
            print(f"{'=' * 80}")

            # Cash analysis
            print(f"\n📊 CASH GAMES (Double-Ups):")
            print(f"{'Strategy':<25} {'Win%':>8} {'ROI%':>8} {'Avg Score':>10} {'Avg Rank':>10} {'Build%':>8}")
            print("-" * 75)

            cash_results = []
            for strategy_name in ROBUST_STRATEGIES['classic'].get(slate_size, {}).get('cash', {}):
                key = f"classic_{slate_size}_cash_{strategy_name}"
                if key in by_strategy and by_strategy[key]:
                    results_list = by_strategy[key]

                    # Calculate metrics
                    wins = sum(1 for r in results_list if r['win'])
                    win_rate = (wins / len(results_list)) * 100
                    avg_roi = np.mean([r['roi'] for r in results_list])
                    avg_rank = np.mean([r['rank'] for r in results_list])
                    avg_score = np.mean([r['score'] for r in results_list])

                    # Build success rate (how many lineups were successfully built)
                    build_success = len(results_list)  # If it's in results, it was built

                    cash_results.append({
                        'strategy': strategy_name,
                        'win_rate': win_rate,
                        'roi': avg_roi,
                        'avg_rank': avg_rank,
                        'avg_score': avg_score,
                        'sample_size': len(results_list),
                        'build_rate': 100.0  # If we have results, it built successfully
                    })

            # Sort by win rate
            cash_results.sort(key=lambda x: x['win_rate'], reverse=True)

            for r in cash_results:
                if r['sample_size'] >= 10:  # Only show if enough samples
                    status = "🏆" if r['win_rate'] >= 50 else "✅" if r['win_rate'] >= 44 else "⚠️" if r[
                                                                                                         'win_rate'] >= 40 else "❌"
                    print(f"{r['strategy']:<25} {r['win_rate']:>7.1f}% {r['roi']:>+7.1f}% "
                          f"{r['avg_score']:>9.1f} {r['avg_rank']:>9.1f} {r['build_rate']:>7.0f}% {status}")

            # GPP analysis
            print(f"\n📊 TOURNAMENTS (GPPs):")
            print(f"{'Strategy':<25} {'ROI%':>8} {'Top 10%':>9} {'Avg Score':>10} {'Top 1%':>8} {'Build%':>8}")
            print("-" * 75)

            gpp_results = []
            for strategy_name in ROBUST_STRATEGIES['classic'].get(slate_size, {}).get('gpp', {}):
                key = f"classic_{slate_size}_gpp_{strategy_name}"
                if key in by_strategy and by_strategy[key]:
                    results_list = by_strategy[key]

                    avg_roi = np.mean([r['roi'] for r in results_list])
                    avg_score = np.mean([r['score'] for r in results_list])
                    top_10 = sum(1 for r in results_list if r['top_10']) / len(results_list) * 100
                    top_1 = sum(1 for r in results_list if r['top_1']) / len(results_list) * 100

                    gpp_results.append({
                        'strategy': strategy_name,
                        'roi': avg_roi,
                        'avg_score': avg_score,
                        'top_10': top_10,
                        'top_1': top_1,
                        'sample_size': len(results_list),
                        'build_rate': 100.0
                    })

            # Sort by ROI
            gpp_results.sort(key=lambda x: x['roi'], reverse=True)

            for r in gpp_results:
                if r['sample_size'] >= 10:
                    status = "🔥" if r['roi'] > 50 else "💰" if r['roi'] > 20 else "✅" if r['roi'] > 0 else "❌"
                    print(f"{r['strategy']:<25} {r['roi']:>+7.1f}% {r['top_10']:>8.1f}% "
                          f"{r['avg_score']:>9.1f} {r['top_1']:>7.1f}% {r['build_rate']:>7.0f}% {status}")

        # Add strategy-specific detailed breakdown
        print(f"\n{'=' * 80}")
        print("DETAILED STRATEGY PERFORMANCE")
        print(f"{'=' * 80}")

        # Get unique strategies
        all_strategies = set()
        for key in by_strategy.keys():
            parts = key.split('_')
            strategy = parts[-1]
            all_strategies.add(strategy)

        for strategy in sorted(all_strategies):
            strategy_results = []
            for key, results_list in by_strategy.items():
                if key.endswith(f'_{strategy}'):
                    strategy_results.extend(results_list)

            if strategy_results:
                print(f"\n📊 {strategy.upper()}:")
                scores = [r['score'] for r in strategy_results]
                rois = [r['roi'] for r in strategy_results]
                ranks = [r['rank'] for r in strategy_results]

                print(f"   Games Played: {len(strategy_results)}")
                print(f"   Avg Score: {np.mean(scores):.1f} (±{np.std(scores):.1f})")
                print(f"   Score Range: {min(scores):.1f} - {max(scores):.1f}")
                print(f"   Avg ROI: {np.mean(rois):+.1f}%")
                print(f"   Avg Rank: {np.mean(ranks):.1f}")
                print(f"   Best Finish: {min(ranks)}")
                print(f"   Worst Finish: {max(ranks)}")

        # Showdown analysis (if applicable)
        showdown_results = [r for r in results if r and r.get('format') == 'showdown']
        if showdown_results:
            print(f"\n{'=' * 80}")
            print("SHOWDOWN SLATES")
            print(f"{'=' * 80}")

            showdown_cash = [r for r in showdown_results if r['contest_type'] == 'cash']
            showdown_gpp = [r for r in showdown_results if r['contest_type'] == 'gpp']

            if showdown_cash:
                wins = sum(1 for r in showdown_cash if r['win'])
                win_rate = (wins / len(showdown_cash)) * 100
                avg_roi = np.mean([r['roi'] for r in showdown_cash])
                avg_score = np.mean([r['score'] for r in showdown_cash])
                print(f"\n📊 SHOWDOWN CASH:")
                print(f"   Win Rate: {win_rate:.1f}%")
                print(f"   Avg ROI: {avg_roi:+.1f}%")
                print(f"   Avg Score: {avg_score:.1f}")

            if showdown_gpp:
                avg_roi = np.mean([r['roi'] for r in showdown_gpp])
                avg_score = np.mean([r['score'] for r in showdown_gpp])
                top_10 = sum(1 for r in showdown_gpp if r['top_10']) / len(showdown_gpp) * 100
                print(f"\n📊 SHOWDOWN GPP:")
                print(f"   Avg ROI: {avg_roi:+.1f}%")
                print(f"   Top 10%: {top_10:.1f}%")
                print(f"   Avg Score: {avg_score:.1f}")

        # Summary statistics
        print(f"\n{'=' * 80}")
        print("SUMMARY STATISTICS")
        print(f"{'=' * 80}")

        print(f"\n✅ Simulation completed successfully!")
        print(f"📄 Results saved to: {output_filename}")

    finally:
        # Restore stdout and close logger
        sys.stdout = original_stdout
        output_logger.close()

        # Also print to console that file was saved
        print(f"\n💾 Full results saved to: {output_filename}")

# ========== MAIN SIMULATION ==========
def run_simulation(num_slates=100, parallel=False):
    """Run complete robust DFS simulation with enhanced tracking"""

    # Add tracking for completion rates
    slate_completion_tracker = defaultdict(int)
    slate_attempts_tracker = defaultdict(int)

    print("\n" + "=" * 80)
    print("COMPLETE ROBUST DFS SIMULATOR")
    print("=" * 80)
    print(f"\n📊 Configuration:")
    print(f"   • Slates per size: {num_slates}")
    print(f"   • Parallel processing: {parallel}")
    print(f"   • CPU cores: {mp.cpu_count()}")

    # Count strategies
    total_strategies = 0
    for format_strategies in ROBUST_STRATEGIES.values():
        if isinstance(format_strategies, dict):
            for size_strategies in format_strategies.values():
                if isinstance(size_strategies, dict):
                    for contest_strategies in size_strategies.values():
                        total_strategies += len(contest_strategies)

    print(f"   • Total strategies: {total_strategies}")

    input("\nPress Enter to start...")  # Give user a chance to see config

    start_time = time.time()

    # Create slate configurations
    slate_configs = []

    # Classic slates
    for slate_size in ['small', 'medium', 'large']:
        for i in range(num_slates):
            slate_id = (i * 1000 + abs(hash(slate_size))) % (2 ** 31 - 1)
            slate_configs.append((slate_id, 'classic', slate_size))

    # Showdown slates
    for i in range(num_slates):
        slate_id = (i * 2000) % (2 ** 31 - 1)
        slate_configs.append((slate_id, 'showdown', 'showdown'))

    # Contest configurations
    contest_configs = [
        ('cash', 100),  # 100-person double-up
        ('gpp', 1000),  # 1000-person tournament
    ]

    print(f"\n🎮 Running {len(slate_configs)} slates x {len(contest_configs)} contest types")
    print(f"   = {len(slate_configs) * len(contest_configs) * (total_strategies // 2)} total contests\n")

    all_results = []
    failed_count = 0

    # Track recent activity (last 10 lines)
    recent_activity = deque(maxlen=10)

    if not parallel:
        # Sequential processing with dashboard
        print("🔄 Processing sequentially with dashboard...")

        for i, (slate_id, format_type, slate_size) in enumerate(slate_configs):
            # Update dashboard every 5 slates (and always on first/last)
            if i % 5 == 0 or i == 0 or i == len(slate_configs) - 1:
                draw_dashboard(i, len(slate_configs), len(all_results), failed_count,
                               start_time, recent_activity)

            # Rest of your loop code continues here...
            recent_activity.append(f"✓ Generating {format_type} slate #{i + 1} ({slate_size})")

            # Generate slate
            slate = generate_slate(slate_id, format_type, slate_size)

            recent_activity.append(f"✓ Generating {format_type} slate #{i + 1} ({slate_size})")

            # Generate slate
            slate = generate_slate(slate_id, format_type, slate_size)

            if not slate or not slate.get('players'):
                failed_count += 1
                recent_activity.append(f"❌ Failed to generate slate {slate_id}")
                continue

            recent_activity.append(f"  → Generated {len(slate['players'])} players")

            # Get strategies for this configuration
            if format_type == 'showdown':
                all_strategies = {}
                for contest_type in ['cash', 'gpp']:
                    all_strategies.update(ROBUST_STRATEGIES['showdown'].get(contest_type, {}))
            else:
                all_strategies = {}
                for contest_type in ['cash', 'gpp']:
                    all_strategies.update(
                        ROBUST_STRATEGIES['classic'].get(slate_size, {}).get(contest_type, {})
                    )

            # Test each strategy in each contest type
            # Test each strategy in each contest type
            for strategy_name, strategy_config in all_strategies.items():
                for contest_type, field_size in contest_configs:
                    recent_activity.append(f"  → Testing {strategy_name} ({contest_type})")

                    # Update dashboard to show current strategy
                    # draw_dashboard(i, len(slate_configs), len(all_results), failed_count,
                    #               start_time, recent_activity)

                    try:
                        result = simulate_contest(
                            slate,
                            strategy_name,
                            strategy_config,
                            contest_type,
                            field_size
                        )

                        if result:
                            all_results.append(result)
                            recent_activity.append(
                                f"    ✓ {strategy_name}: Rank {result['rank']}/{field_size} ({result['percentile']:.0f}%ile)")
                    except Exception as e:
                        failed_count += 1
                        recent_activity.append(f"    ❌ {strategy_name} error: {str(e)[:40]}...")

            # Milestone notification every 10%
            if i > 0 and (i * 100 // len(slate_configs)) % 10 == 0:
                milestone_pct = (i * 100 // len(slate_configs))
                recent_activity.append(f"🎯 ═══ {milestone_pct}% MILESTONE REACHED! ═══")

    else:
        # Parallel processing (existing code)
        # ... (keep your existing parallel code, just add print statements)
        print("🚀 Processing in parallel (no live dashboard)...")

        # Create batches for parallel processing
        batch_size = 10
        batches = []

        for i in range(0, len(slate_configs), batch_size):
            batch = slate_configs[i:i + batch_size]
            batches.append((len(batches), batch, contest_configs))

        print(f"🚀 Processing {len(batches)} batches in parallel...\n")

        # Process in parallel
        with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
            futures = {executor.submit(process_batch, batch): batch[0] for batch in batches}

            completed = 0
            total = len(batches)

            for future in as_completed(futures):
                batch_id = futures[future]
                completed += 1

                try:
                    _, results = future.result()
                    all_results.extend(results)

                    # Progress update
                    pct = completed / total * 100
                    print(f"\r⚡ Progress: {completed}/{total} batches ({pct:.1f}%) "
                          f"| Results: {len(all_results):,}", end="")

                except Exception as e:
                    print(f"\n❌ Error in batch {batch_id}: {str(e)}")

    # Final dashboard update
    if not parallel:
        draw_dashboard(len(slate_configs), len(slate_configs), len(all_results),
                       failed_count, start_time, recent_activity)

    # Complete
    elapsed = time.time() - start_time
    print(f"\n\n✅ Simulation complete in {elapsed:.1f} seconds")
    print(f"📊 Total results: {len(all_results):,}")
    if failed_count > 0:
        print(f"⚠️  Failed tests: {failed_count}")

    # Analyze results
    if all_results:
        input("\nPress Enter to see results analysis...")
        analyze_results(all_results)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'robust_dfs_simulation_{timestamp}.json'

        # Prepare data for saving
        save_data = {
            'metadata': {
                'timestamp': timestamp,
                'duration_seconds': elapsed,
                'num_slates': num_slates,
                'total_results': len(all_results),
                'strategies_tested': total_strategies,
                'configuration': {
                    'classic_config': CLASSIC_CONFIG,
                    'showdown_config': SHOWDOWN_CONFIG,
                    'robust_strategies': ROBUST_STRATEGIES
                }
            },
            'results': all_results
        }

        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)

        print(f"\n💾 Results saved to: {filename}")
    else:
        print("\n⚠️ No results generated!")

# ========== TESTING FUNCTIONS ==========

def help_strategy_robustness():
    """Test that all strategies build valid lineups consistently"""
    print("\n" + "=" * 80)
    print("TESTING STRATEGY ROBUSTNESS")
    print("=" * 80)

    success_rates = {}

    # Test each strategy multiple times
    test_iterations = 10

    for format_type in ['classic', 'showdown']:
        if format_type == 'classic':
            slate_sizes = ['small', 'medium', 'large']
        else:
            slate_sizes = ['showdown']

        for slate_size in slate_sizes:
            print(f"\n📋 Testing {format_type} - {slate_size}:")

            # Generate multiple test slates
            test_slates = []
            for i in range(test_iterations):
                slate = generate_slate(i * 100, format_type, slate_size if format_type == 'classic' else 'showdown')
                if slate and slate.get('players'):
                    test_slates.append(slate)

            if not test_slates:
                print("   ❌ Failed to generate test slates")
                continue

            # Test each strategy
            if format_type == 'showdown':
                strategies_to_test = {}
                for ct in ['cash', 'gpp']:
                    strategies_to_test.update(ROBUST_STRATEGIES['showdown'].get(ct, {}))
            else:
                strategies_to_test = {}
                for ct in ['cash', 'gpp']:
                    strategies_to_test.update(
                        ROBUST_STRATEGIES['classic'].get(slate_size, {}).get(ct, {})
                    )

            for strategy_name, strategy_config in strategies_to_test.items():
                successes = 0
                total_salary = 0

                for slate in test_slates:
                    lineup = build_lineup(
                        slate['players'],
                        strategy_config,
                        format_type,
                        slate_size if format_type == 'classic' else 'showdown'
                    )

                    if lineup:
                        if format_type == 'showdown' or validate_lineup(lineup['players']):
                            successes += 1
                            total_salary += lineup['salary']

                success_rate = (successes / len(test_slates)) * 100
                avg_salary = total_salary / successes if successes > 0 else 0

                key = f"{format_type}_{slate_size}_{strategy_name}"
                success_rates[key] = success_rate

                status = "✅" if success_rate == 100 else "⚠️" if success_rate >= 90 else "❌"

                print(f"   {strategy_name:<25} Success: {success_rate:>5.1f}% "
                      f"Avg Salary: ${avg_salary:>7,.0f} {status}")

    # Summary
    print(f"\n{'=' * 80}")
    print("📊 ROBUSTNESS SUMMARY")
    print(f"{'=' * 80}")

    perfect_strategies = sum(1 for rate in success_rates.values() if rate == 100)
    good_strategies = sum(1 for rate in success_rates.values() if rate >= 90)
    total_strategies = len(success_rates)

    print(f"\n✅ Perfect (100%): {perfect_strategies}/{total_strategies}")
    print(f"👍 Good (90%+): {good_strategies}/{total_strategies}")
    print(f"📈 Average success rate: {np.mean(list(success_rates.values())):.1f}%")

    if perfect_strategies == total_strategies:
        print("\n🏆 ALL STRATEGIES ARE 100% ROBUST!")
    else:
        print(f"\n⚠️ {total_strategies - perfect_strategies} strategies need improvement")


def validate_simulation_integrity(results):
    """Check for potential issues in simulation results"""
    issues = []

    # Group by contest
    contest_groups = defaultdict(list)
    for r in results:
        key = f"{r['contest_type']}_{r['field_size']}"
        contest_groups[key].append(r)

    print("\n" + "=" * 60)
    print("SIMULATION INTEGRITY CHECK")
    print("=" * 60)

    # Check each contest type
    for contest_key, contest_results in contest_groups.items():
        contest_type, field_size = contest_key.split('_')
        field_size = int(field_size)

        # Check 1: Field sizes
        ranks = [r['rank'] for r in contest_results]
        max_rank = max(ranks) if ranks else 0

        if max_rank < field_size * 0.8:
            issues.append(f"❌ {contest_key}: Max rank {max_rank} < 80% of field size {field_size}")
        else:
            print(f"✅ {contest_key}: Field size integrity OK")

        # Check 2: Cash rates for cash games
        if contest_type == 'cash':
            win_rate = sum(1 for r in contest_results if r['win']) / len(contest_results) * 100

            # Cash games should have 44% cash rate on average
            if win_rate > 60:
                issues.append(f"⚠️  {contest_key}: Win rate {win_rate:.1f}% seems too high")
            elif win_rate < 30:
                issues.append(f"⚠️  {contest_key}: Win rate {win_rate:.1f}% seems too low")
            else:
                print(f"✅ {contest_key}: Win rate {win_rate:.1f}% seems reasonable")

        # Check 3: Score distributions
        scores = [r['score'] for r in contest_results]
        if scores:
            avg_score = np.mean(scores)
            std_score = np.std(scores)
            cv = std_score / avg_score if avg_score > 0 else 0

            if cv < 0.05:
                issues.append(f"⚠️  {contest_key}: Score variance too low (CV={cv:.3f})")
            else:
                print(f"✅ {contest_key}: Score distribution OK (CV={cv:.3f})")

    # Check 4: Lineup validity
    salary_issues = sum(1 for r in results if r.get('lineup_salary', 50000) > 50000)
    if salary_issues > 0:
        issues.append(f"❌ {salary_issues} lineups exceed salary cap!")

    # Report
    if issues:
        print("\n🚨 INTEGRITY ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
        print("\n⚠️  Results may not be reliable!")
    else:
        print("\n✅ All integrity checks passed!")

    return len(issues) == 0


# ========== CASH GAME DIAGNOSTIC TEST ==========

def run_cash_diagnostic_test(num_slates=100):
    """Comprehensive diagnostic test to identify cash game issues"""

    print("\n" + "=" * 80)
    print("CASH GAME DIAGNOSTIC TEST")
    print("Testing all theories to identify why cash strategies are failing")
    print("=" * 80)

    # Initialize tracking metrics
    metrics = {
        # Field strength metrics
        'cash_opponent_scores': [],
        'gpp_opponent_scores': [],
        'cash_winning_scores': [],
        'gpp_winning_scores': [],
        'cash_cash_lines': [],

        # Projection accuracy
        'projection_vs_actual': [],  # (projected, actual) tuples
        'projection_accuracy': [],  # actual/projected ratios

        # Ownership patterns
        'cash_lineup_ownership': [],
        'gpp_lineup_ownership': [],
        'cash_winner_ownership': [],
        'cash_chalk_counts': [],  # Number of 30%+ owned players

        # Salary usage
        'strategy_natural_salaries': defaultdict(list),
        'strategy_final_salaries': defaultdict(list),
        'winning_salaries': [],

        # Variance metrics
        'lineup_disasters': 0,
        'field_disasters': 0,
        'total_lineups_scored': 0,
        'score_variance_by_strategy': defaultdict(list),

        # Strategy performance
        'strategy_ranks': defaultdict(list),
        'strategy_scores': defaultdict(list),
    }

    # Test configurations
    test_strategies = {
        'cash': ['value_floor', 'chalk_plus', 'matchup_optimal'],
        'gpp': ['correlation_value', 'stars_and_scrubs_extreme', 'cold_player_leverage']
    }

    start_time = time.time()

    # Run slates
    for slate_num in range(num_slates):
        if slate_num % 10 == 0:
            print(f"\rProcessing slate {slate_num}/{num_slates}...", end="")

        # Generate slate
        slate_id = slate_num * 1000
        slate = generate_slate(slate_id, 'classic', 'medium')

        if not slate or not slate.get('players'):
            continue

        # Test both cash and GPP
        for contest_type in ['cash', 'gpp']:
            field_size = 100 if contest_type == 'cash' else 1000

            # Track field scores
            field_scores_for_contest = []

            # Test each strategy
            for strategy_name in test_strategies[contest_type]:
                strategy_config = {'type': strategy_name}

                # Build lineup WITHOUT salary optimization first
                lineup = build_lineup(
                    slate['players'],
                    strategy_config,
                    'classic',
                    'medium'
                )

                if not lineup:
                    continue

                # Track natural salary
                natural_salary = lineup['salary']
                metrics['strategy_natural_salaries'][strategy_name].append(natural_salary)

                # Track ownership
                avg_ownership = np.mean([p['ownership'] for p in lineup['players']])
                chalk_count = sum(1 for p in lineup['players'] if p['ownership'] >= 30)

                if contest_type == 'cash':
                    metrics['cash_lineup_ownership'].append(avg_ownership)
                    metrics['cash_chalk_counts'].append(chalk_count)
                else:
                    metrics['gpp_lineup_ownership'].append(avg_ownership)

                # Simulate contest
                result = simulate_contest_diagnostic(
                    slate, lineup, strategy_name, contest_type, field_size, metrics
                )

                if result:
                    # Track final salary after optimization
                    metrics['strategy_final_salaries'][strategy_name].append(result['final_salary'])

                    # Track performance
                    metrics['strategy_ranks'][strategy_name].append(result['rank'])
                    metrics['strategy_scores'][strategy_name].append(result['score'])

                    # Track projection accuracy
                    metrics['projection_vs_actual'].append((result['projection'], result['score']))
                    if result['projection'] > 0:
                        metrics['projection_accuracy'].append(result['score'] / result['projection'])

                    # Add to field scores
                    field_scores_for_contest.extend(result['field_scores'])

                    # Track winning lineup details
                    if contest_type == 'cash' and result['rank'] <= field_size * 0.44:
                        metrics['winning_salaries'].append(result['final_salary'])

            # Analyze field for this contest
            if field_scores_for_contest:
                if contest_type == 'cash':
                    metrics['cash_opponent_scores'].extend(field_scores_for_contest)
                    cash_line_idx = int(len(field_scores_for_contest) * 0.44)
                    if cash_line_idx < len(field_scores_for_contest):
                        sorted_scores = sorted(field_scores_for_contest, reverse=True)
                        metrics['cash_cash_lines'].append(sorted_scores[cash_line_idx])
                        metrics['cash_winning_scores'].append(sorted_scores[0])
                else:
                    metrics['gpp_opponent_scores'].extend(field_scores_for_contest)
                    if field_scores_for_contest:
                        metrics['gpp_winning_scores'].append(max(field_scores_for_contest))

    # Generate report
    print("\n\n" + "=" * 80)
    print("DIAGNOSTIC TEST COMPLETE")
    print("=" * 80)

    generate_diagnostic_report(metrics, num_slates)

    elapsed = time.time() - start_time
    print(f"\nTest completed in {elapsed:.1f} seconds")


def simulate_contest_diagnostic(slate, our_lineup, strategy_name, contest_type, field_size, metrics):
    """Modified contest simulation that tracks diagnostic metrics"""

    # Score our lineup
    our_score = simulate_lineup_score(our_lineup)

    # Track disasters
    if hasattr(simulate_lineup_score, 'last_was_disaster') and simulate_lineup_score.last_was_disaster:
        metrics['lineup_disasters'] += 1

    # Generate and score field
    field_lineups = generate_field(slate, field_size, contest_type)
    field_scores = []

    for opp_lineup in field_lineups:
        score = simulate_lineup_score(opp_lineup)
        field_scores.append(score)

        # Track field disasters
        if hasattr(simulate_lineup_score, 'last_was_disaster') and simulate_lineup_score.last_was_disaster:
            metrics['field_disasters'] += 1

    metrics['total_lineups_scored'] += len(field_lineups) + 1

    # Calculate rank
    all_scores = field_scores + [our_score]
    all_scores.sort(reverse=True)
    our_rank = all_scores.index(our_score) + 1

    # Track winner ownership if we have it
    if contest_type == 'cash' and field_lineups:
        # Get top 44% lineups
        top_44_percent = int(len(field_lineups) * 0.44)
        sorted_field = sorted(zip(field_scores, field_lineups), key=lambda x: x[0], reverse=True)

        if sorted_field and top_44_percent > 0:
            # Sample winner ownership
            winner_lineup = sorted_field[0][1]
            if 'players' in winner_lineup:
                winner_ownership = np.mean([p.get('ownership', 15) for p in winner_lineup['players']])
                metrics['cash_winner_ownership'].append(winner_ownership)

    return {
        'rank': our_rank,
        'score': our_score,
        'projection': our_lineup['projection'],
        'final_salary': our_lineup['salary'],
        'field_scores': field_scores,
        'percentile': ((len(all_scores) - our_rank) / len(all_scores)) * 100
    }


def generate_diagnostic_report(metrics, num_slates):
    """Generate comprehensive diagnostic report"""

    print("\n🔍 THEORY 1: FIELD STRENGTH")
    print("-" * 50)

    if metrics['cash_opponent_scores'] and metrics['gpp_opponent_scores']:
        cash_avg = np.mean(metrics['cash_opponent_scores'])
        gpp_avg = np.mean(metrics['gpp_opponent_scores'])
        difference = ((cash_avg - gpp_avg) / gpp_avg) * 100

        print(f"Cash opponent avg score: {cash_avg:.1f}")
        print(f"GPP opponent avg score: {gpp_avg:.1f}")
        print(f"Cash field is {difference:.1f}% stronger")

        if metrics['cash_cash_lines']:
            avg_cash_line = np.mean(metrics['cash_cash_lines'])
            print(f"Average cash line: {avg_cash_line:.1f} points")

        if difference > 5:
            print("❌ PROBLEM: Cash field is significantly stronger than GPP!")
        else:
            print("✓ Field strength differential seems normal")

    print("\n🔍 THEORY 2: PROJECTION ACCURACY")
    print("-" * 50)

    if metrics['projection_vs_actual']:
        projections, actuals = zip(*metrics['projection_vs_actual'])
        avg_proj = np.mean(projections)
        avg_actual = np.mean(actuals)
        accuracy = (avg_actual / avg_proj) * 100 if avg_proj > 0 else 0

        print(f"Average projected: {avg_proj:.1f}")
        print(f"Average actual: {avg_actual:.1f}")
        print(f"Accuracy: {accuracy:.1f}%")

        # Calculate correlation
        if len(projections) > 10:
            correlation = np.corrcoef(projections, actuals)[0, 1]
            print(f"Correlation: {correlation:.3f}")

        if accuracy < 90 or accuracy > 110:
            print("❌ PROBLEM: Projections are off by more than 10%!")
        else:
            print("✓ Projections are reasonably accurate")

    print("\n🔍 THEORY 3: OWNERSHIP PATTERNS")
    print("-" * 50)

    if metrics['cash_lineup_ownership']:
        your_avg_own = np.mean(metrics['cash_lineup_ownership'])
        your_chalk = np.mean(metrics['cash_chalk_counts'])

        print(f"Your cash lineup avg ownership: {your_avg_own:.1f}%")
        print(f"Your avg chalk players (30%+): {your_chalk:.1f}")

        if metrics['cash_winner_ownership']:
            winner_avg_own = np.mean(metrics['cash_winner_ownership'])
            print(f"Winning lineup avg ownership: {winner_avg_own:.1f}%")

            if winner_avg_own - your_avg_own > 5:
                print("❌ PROBLEM: You're not playing enough chalk!")
                print(f"   Gap: {winner_avg_own - your_avg_own:.1f}% ownership difference")
            else:
                print("✓ Ownership usage seems appropriate")

    print("\n🔍 THEORY 4: SALARY OPTIMIZATION")
    print("-" * 50)

    for strategy in ['value_floor', 'chalk_plus', 'matchup_optimal']:
        if strategy in metrics['strategy_natural_salaries']:
            natural = metrics['strategy_natural_salaries'][strategy]
            final = metrics['strategy_final_salaries'][strategy]

            if natural and final:
                avg_natural = np.mean(natural)
                avg_final = np.mean(final)
                forced_up = avg_final - avg_natural

                print(f"{strategy}:")
                print(f"  Natural salary: ${avg_natural:,.0f}")
                print(f"  Final salary: ${avg_final:,.0f}")
                print(f"  Forced up by: ${forced_up:,.0f}")

    if metrics['winning_salaries']:
        print(f"\nWinning lineup avg salary: ${np.mean(metrics['winning_salaries']):,.0f}")

    print("\n🔍 THEORY 5: VARIANCE/DISASTERS")
    print("-" * 50)

    if metrics['total_lineups_scored'] > 0:
        your_disaster_rate = (metrics['lineup_disasters'] / (num_slates * 6)) * 100  # 6 strategies tested
        field_disaster_rate = (metrics['field_disasters'] / metrics['total_lineups_scored']) * 100

        print(f"Your disaster rate: {your_disaster_rate:.1f}%")
        print(f"Field disaster rate: {field_disaster_rate:.1f}%")

        if abs(your_disaster_rate - 3.0) > 1:
            print("❌ PROBLEM: Unusual disaster rate!")
        else:
            print("✓ Variance seems normal")

    print("\n📊 STRATEGY PERFORMANCE SUMMARY")
    print("-" * 50)

    for strategy in ['value_floor', 'chalk_plus', 'matchup_optimal']:
        if strategy in metrics['strategy_ranks']:
            ranks = metrics['strategy_ranks'][strategy]
            if ranks:
                win_rate = sum(1 for r in ranks if r <= 44) / len(ranks) * 100
                avg_rank = np.mean(ranks)
                print(f"{strategy}: {win_rate:.1f}% win rate, avg rank {avg_rank:.1f}")


'''  # commented out
def test_broken_strategies():
    """Test previously broken strategies with new position-aware builder"""
    print("\nTesting Previously Broken Strategies with Position-Aware Builder")
    print("=" * 60)

    # Generate test slate
    slate = generate_slate(1, 'classic', 'medium')

    broken_strategies = [
        'balanced_optimal',
        'smart_stack',
        'multi_stack',
        'game_theory_leverage',
        'contrarian_correlation'
    ]

    for strategy_name in broken_strategies:
        print(f"\nTesting {strategy_name}...")

        # Find strategy config
        strategy_config = None
        for contest_type in ['cash', 'gpp']:
            if strategy_name in ROBUST_STRATEGIES['classic']['medium'].get(contest_type, {}):
                strategy_config = ROBUST_STRATEGIES['classic']['medium'][contest_type][strategy_name]
                break

        if not strategy_config:
            print(f"Strategy {strategy_name} not found")
            continue

        lineup = build_lineup(slate['players'], strategy_config, 'classic', 'medium')

        if lineup:
            print(f"✅ SUCCESS! Salary: ${lineup['salary']}, Players: {len(lineup['players'])}")
        else:
            print(f"❌ FAILED")

'''




# ========== ENTRY POINT ==========
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║        COMPLETE ROBUST DFS SIMULATOR - FINAL             ║
    ║                                                          ║
    ║  Features:                                               ║
    ║  • Status dashboard with progress tracking               ║
    ║  • All new strategies with advanced metrics              ║
    ║  • Realistic variance and scoring                        ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    print("\nSelect option:")
    print("1. Run Integrity Audit")
    print("2. Test Strategy Robustness")
    print("3. Quick Test (50 slates) - ~5 minutes")
    print("4. Basic Test (100 slates) - ~10 minutes")
    print("5. Standard Test (200 slates) - ~20 minutes")
    print("6. Thorough Test (500 slates) - ~45 minutes")
    print("7. Full Analysis (1000 slates) - ~90 minutes")
    print("8. Professional Test (2000 slates) - ~3 hours")
    print("9. Cash Diagnostic Test (100 slates) - ~10 minutes")  # NEW OPTION
    print("10. Custom number of slates")
    print("11. Elite Strategies Test (500 slates) - FINAL TEST")

    choice = input("\nEnter choice (1-10): ")  # Updated to 1-10

    if choice == '1':
        comprehensive_simulation_audit()
    elif choice == '2':
        help_strategy_robustness()
    elif choice == '3':
        run_simulation(50)
    elif choice == '4':
        run_simulation(100)
    elif choice == '5':
        run_simulation(200)
    elif choice == '6':
        run_simulation(500)
    elif choice == '7':
        run_simulation(1000)
    elif choice == '8':
        run_simulation(2000)
    elif choice == '9':
        run_cash_diagnostic_test(100)  # NEW DIAGNOSTIC TEST
    elif choice == '11':
        run_elite_strategies_test(500)
    elif choice == '10':
        custom = input("Enter number of slates: ")

        try:
            num_slates = int(custom)
            if 1 <= num_slates <= 5000:
                run_simulation(num_slates)
            else:
                print("Please enter a number between 1 and 5000")
                run_simulation(200)
        except:
            print("Invalid input, running standard test...")
            run_simulation(200)
    else:
        print("Invalid choice. Running standard test...")
        run_simulation(200)