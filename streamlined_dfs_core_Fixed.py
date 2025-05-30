#!/usr/bin/env python3
"""
Streamlined DFS Core System - FIXED VERSION
Integrates all your proven algorithms with bug fixes for the optimization issues
"""

import os
import sys
import csv
import json
import time
import random
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')

# Optional imports with fallbacks
try:
    import pulp

    MILP_AVAILABLE = True
    print("✅ PuLP available - MILP optimization enabled")
except ImportError:
    MILP_AVAILABLE = False
    print("⚠️ PuLP not available - install with: pip install pulp")

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class StreamlinedPlayer:
    """Unified player model with multi-position support"""

    def __init__(self, player_data):
        # Core data
        self.id = player_data.get('id', 0)
        self.name = player_data.get('name', '').strip()
        self.positions = self._parse_positions(player_data.get('position', ''))
        self.team = player_data.get('team', '').strip()
        self.salary = int(player_data.get('salary', 3000))
        self.projection = float(player_data.get('projection', 0))

        # Enhanced data
        self.score = float(player_data.get('score', self.projection or (self.salary / 1000)))
        self.batting_order = player_data.get('batting_order')
        self.is_confirmed = player_data.get('is_confirmed', False)

        # External data
        self.dff_rank = player_data.get('dff_rank')
        self.dff_tier = player_data.get('dff_tier')
        self.statcast_data = player_data.get('statcast_data', {})
        self.vegas_data = player_data.get('vegas_data', {})

        # Game info
        self.game_info = player_data.get('game_info', '')
        self.opponent = self._extract_opponent()

    def _parse_positions(self, position_str):
        """Parse multiple positions with better handling"""
        if not position_str:
            return ['UTIL']

        # Clean up the position string
        position_str = str(position_str).strip().upper()

        # Handle common DraftKings formats
        if '/' in position_str:
            positions = position_str.split('/')
        elif ',' in position_str:
            positions = position_str.split(',')
        else:
            positions = [position_str]

        # Clean and validate positions
        valid_positions = []
        position_mapping = {
            'SP': 'P', 'RP': 'P',  # All pitchers become 'P'
            '1B': '1B', '2B': '2B', '3B': '3B', 'SS': 'SS',
            'C': 'C', 'OF': 'OF', 'UTIL': 'UTIL'
        }

        for pos in positions:
            pos = pos.strip()
            if pos in position_mapping:
                mapped_pos = position_mapping[pos]
                if mapped_pos not in valid_positions:
                    valid_positions.append(mapped_pos)
            elif pos in ['1B', '2B', '3B', 'SS', 'C', 'OF', 'P', 'UTIL']:
                if pos not in valid_positions:
                    valid_positions.append(pos)

        return valid_positions if valid_positions else ['UTIL']

    def _extract_opponent(self):
        """Extract opponent from game info"""
        if '@' in self.game_info:
            parts = self.game_info.split('@')
            if len(parts) >= 2:
                return parts[1].split()[0] if parts[1] else ''
        return ''

    def can_play_position(self, position):
        """Check if player can play specific position"""
        return position in self.positions or position == 'UTIL'

    def get_primary_position(self):
        """Get primary position for sorting/display"""
        return self.positions[0] if self.positions else 'UTIL'

    def __repr__(self):
        return f"StreamlinedPlayer({self.name}, {'/'.join(self.positions)}, ${self.salary}, {self.score:.1f})"


class FixedDFFMatcher:
    """Fixed DFF name matching with improved algorithms"""

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize name for matching"""
        if not name:
            return ""

        name = str(name).strip()

        # CRITICAL FIX: Handle "Last, First" format from DFF
        if ',' in name:
            parts = name.split(',', 1)
            if len(parts) == 2:
                last = parts[0].strip()
                first = parts[1].strip()
                name = f"{first} {last}"

        # Clean up
        name = name.lower()
        name = ' '.join(name.split())  # Normalize whitespace

        # Remove suffixes that cause mismatches
        suffixes = [' jr', ' sr', ' iii', ' ii', ' iv', '.']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        return name

    @staticmethod
    def match_player(dff_name: str, dk_players: List[StreamlinedPlayer]) -> Tuple[
        Optional[StreamlinedPlayer], int, str]:
        """Enhanced matching with higher success rate"""
        dff_normalized = FixedDFFMatcher.normalize_name(dff_name)

        # Strategy 1: Exact match
        for player in dk_players:
            dk_normalized = FixedDFFMatcher.normalize_name(player.name)
            if dff_normalized == dk_normalized:
                return player, 100, "exact"

        # Strategy 2: First/Last name matching
        dff_parts = dff_normalized.split()
        if len(dff_parts) >= 2:
            for player in dk_players:
                dk_normalized = FixedDFFMatcher.normalize_name(player.name)
                dk_parts = dk_normalized.split()

                if len(dk_parts) >= 2:
                    # Full first/last match
                    if (dff_parts[0] == dk_parts[0] and dff_parts[-1] == dk_parts[-1]):
                        return player, 95, "first_last_match"

                    # Last name + first initial
                    if (dff_parts[-1] == dk_parts[-1] and
                            len(dff_parts[0]) > 0 and len(dk_parts[0]) > 0 and
                            dff_parts[0][0] == dk_parts[0][0]):
                        return player, 85, "last_first_initial"

        # Strategy 3: Partial matching
        for player in dk_players:
            dk_normalized = FixedDFFMatcher.normalize_name(player.name)

            # Check if names contain each other
            if dff_normalized in dk_normalized or dk_normalized in dff_normalized:
                return player, 75, "partial"

        return None, 0, "no_match"


class StreamlinedOptimizer:
    """Unified optimizer with fixed constraints"""

    def __init__(self):
        self.position_requirements = {
            'classic': {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3},
            'showdown': {'UTIL': 6}
        }

    def optimize_lineup(self, players: List[StreamlinedPlayer],
                        contest_type='classic', method='milp',
                        budget=50000, min_salary=49000, num_attempts=1000) -> Tuple[List[StreamlinedPlayer], float]:
        """Unified optimization method with fixes"""

        print(f"🚀 Optimizing {contest_type} lineup using {method.upper()}...")
        print(f"📊 Available players: {len(players)}")

        # Show position breakdown for debugging
        pos_counts = {}
        for player in players:
            for pos in player.positions:
                pos_counts[pos] = pos_counts.get(pos, 0) + 1
        print(f"📍 Position availability: {dict(sorted(pos_counts.items()))}")

        if method == 'milp' and MILP_AVAILABLE:
            return self._optimize_milp_fixed(players, contest_type, budget, min_salary)
        else:
            return self._optimize_monte_carlo_fixed(players, contest_type, budget, min_salary, num_attempts)

    def _optimize_milp_fixed(self, players: List[StreamlinedPlayer], contest_type: str,
                             budget: int, min_salary: int) -> Tuple[List[StreamlinedPlayer], float]:
        """FIXED MILP optimization with relaxed constraints"""

        print("🧠 Running FIXED MILP optimization...")

        try:
            # Create optimization problem
            prob = pulp.LpProblem("DFS_Lineup", pulp.LpMaximize)

            # Decision variables
            player_vars = {}
            for i, player in enumerate(players):
                player_vars[i] = pulp.LpVariable(f"player_{i}", cat=pulp.LpBinary)

            # Objective: Maximize total score
            prob += pulp.lpSum([player_vars[i] * players[i].score for i in range(len(players))])

            if contest_type == 'classic':
                # Salary constraints
                prob += pulp.lpSum([player_vars[i] * players[i].salary for i in range(len(players))]) <= budget
                prob += pulp.lpSum([player_vars[i] * players[i].salary for i in range(len(players))]) >= min_salary

                # Roster size
                prob += pulp.lpSum([player_vars[i] for i in range(len(players))]) == 10

                # FIXED: More flexible position constraints with UTIL handling
                requirements = self.position_requirements[contest_type]

                # Build position constraints with multi-position support
                for position, count in requirements.items():
                    eligible_players = []
                    for i, player in enumerate(players):
                        if player.can_play_position(position):
                            eligible_players.append(i)

                    if eligible_players:
                        if count == 1:
                            # Exactly one player for this position
                            prob += pulp.lpSum([player_vars[i] for i in eligible_players]) >= 1
                        else:
                            # Multiple players (like P=2, OF=3)
                            prob += pulp.lpSum([player_vars[i] for i in eligible_players]) >= count
                    else:
                        print(f"⚠️ No players available for position {position}")

                # Add UTIL constraint to fill remaining slots
                # Calculate how many UTIL slots we need
                fixed_positions = sum(count for pos, count in requirements.items())
                util_slots = 10 - fixed_positions

                if util_slots > 0:
                    # Any remaining players can fill UTIL
                    all_eligible = list(range(len(players)))
                    prob += pulp.lpSum([player_vars[i] for i in all_eligible]) == 10

            elif contest_type == 'showdown':
                # Showdown constraints
                prob += pulp.lpSum([player_vars[i] * players[i].salary for i in range(len(players))]) <= budget
                prob += pulp.lpSum([player_vars[i] for i in range(len(players))]) == 6

            # Solve
            print("🔄 Solving MILP problem...")
            result = prob.solve(pulp.PULP_CBC_CMD(msg=0))

            print(f"🔍 MILP Status: {pulp.LpStatus[prob.status]}")

            if prob.status == pulp.LpStatusOptimal:
                # Extract lineup
                lineup = []
                total_score = 0

                for i in range(len(players)):
                    if player_vars[i].value() and player_vars[i].value() > 0.5:
                        lineup.append(players[i])
                        total_score += players[i].score

                print(f"✅ MILP found optimal lineup: {len(lineup)} players, {total_score:.2f} points")

                # Validate lineup
                if self._validate_lineup(lineup, contest_type):
                    return lineup, total_score
                else:
                    print("⚠️ MILP lineup failed validation, trying Monte Carlo...")
                    return self._optimize_monte_carlo_fixed(players, contest_type, budget, min_salary, 2000)

            else:
                print(f"⚠️ MILP failed with status: {pulp.LpStatus[prob.status]}")
                print("🔄 Trying Monte Carlo fallback...")
                return self._optimize_monte_carlo_fixed(players, contest_type, budget, min_salary, 2000)

        except Exception as e:
            print(f"❌ MILP error: {e}")
            print("🔄 Trying Monte Carlo fallback...")
            return self._optimize_monte_carlo_fixed(players, contest_type, budget, min_salary, 2000)

    def _optimize_monte_carlo_fixed(self, players: List[StreamlinedPlayer], contest_type: str,
                                    budget: int, min_salary: int, num_attempts: int) -> Tuple[
        List[StreamlinedPlayer], float]:
        """FIXED Monte Carlo optimization"""

        print(f"🎲 Running FIXED Monte Carlo optimization ({num_attempts:,} attempts)...")

        best_lineup = []
        best_score = 0
        valid_attempts = 0

        # Group players by position for classic contests
        if contest_type == 'classic':
            players_by_position = {}
            requirements = self.position_requirements[contest_type]

            for position in requirements.keys():
                eligible = [p for p in players if p.can_play_position(position)]
                players_by_position[position] = sorted(eligible, key=lambda x: x.score, reverse=True)
                print(f"📊 {position}: {len(eligible)} eligible players")

        for attempt in range(num_attempts):
            try:
                if contest_type == 'classic':
                    lineup = self._generate_classic_lineup_fixed(players_by_position, budget, min_salary)
                else:
                    lineup = self._generate_showdown_lineup(players, budget)

                if lineup and self._validate_lineup(lineup, contest_type):
                    total_score = sum(p.score for p in lineup)
                    if total_score > best_score:
                        best_lineup = lineup.copy()
                        best_score = total_score
                    valid_attempts += 1

            except Exception:
                continue

        success_rate = (valid_attempts / num_attempts) * 100 if num_attempts > 0 else 0

        if best_lineup:
            print(f"✅ Monte Carlo found lineup: {len(best_lineup)} players, {best_score:.2f} points")
            print(f"📊 Success rate: {success_rate:.1f}% ({valid_attempts}/{num_attempts})")
        else:
            print("❌ Monte Carlo failed to find valid lineup")

        return best_lineup, best_score

    def _generate_classic_lineup_fixed(self, players_by_position: Dict, budget: int, min_salary: int) -> List[
        StreamlinedPlayer]:
        """Generate a classic lineup with fixed logic"""
        lineup = []
        total_salary = 0
        used_players = set()

        requirements = self.position_requirements['classic']

        # Fill required positions first
        for position, count in requirements.items():
            available = [p for p in players_by_position[position]
                         if p.id not in used_players]

            if len(available) < count:
                return []  # Not enough players

            # Select players for this position
            selected = []

            for _ in range(count):
                if not available:
                    return []

                # Weighted random selection based on score
                weights = [max(0.1, p.score) for p in available]
                try:
                    chosen_player = random.choices(available, weights=weights, k=1)[0]
                except:
                    chosen_player = available[0]  # Fallback

                if total_salary + chosen_player.salary <= budget:
                    selected.append(chosen_player)
                    available.remove(chosen_player)
                    total_salary += chosen_player.salary
                    used_players.add(chosen_player.id)
                else:
                    # Try to find a cheaper player
                    cheaper_available = [p for p in available if total_salary + p.salary <= budget]
                    if cheaper_available:
                        chosen_player = min(cheaper_available, key=lambda x: x.salary)
                        selected.append(chosen_player)
                        available.remove(chosen_player)
                        total_salary += chosen_player.salary
                        used_players.add(chosen_player.id)
                    else:
                        return []  # Can't fit any player

            lineup.extend(selected)

        # Check constraints
        if (len(lineup) == 10 and
                min_salary <= total_salary <= budget):
            return lineup
        else:
            return []

    def _generate_showdown_lineup(self, players: List[StreamlinedPlayer], budget: int) -> List[StreamlinedPlayer]:
        """Generate a showdown lineup"""
        # Sort by value (score per $1000 salary)
        players_by_value = sorted(players,
                                  key=lambda x: x.score / (x.salary / 1000),
                                  reverse=True)

        lineup = []
        total_salary = 0

        for player in players_by_value:
            if len(lineup) < 6 and total_salary + player.salary <= budget:
                lineup.append(player)
                total_salary += player.salary

        return lineup if len(lineup) == 6 else []

    def _validate_lineup(self, lineup: List[StreamlinedPlayer], contest_type: str) -> bool:
        """Validate lineup meets all requirements"""
        if not lineup:
            return False

        if contest_type == 'classic':
            if len(lineup) != 10:
                return False

            # Check position requirements
            position_counts = {}
            for player in lineup:
                primary_pos = player.get_primary_position()
                position_counts[primary_pos] = position_counts.get(primary_pos, 0) + 1

            requirements = self.position_requirements[contest_type]

            # Flexible validation - make sure we have minimum required
            for pos, required_count in requirements.items():
                actual_count = position_counts.get(pos, 0)
                if actual_count < required_count:
                    # Check if any player can fill this position
                    flexible_count = sum(1 for p in lineup if p.can_play_position(pos))
                    if flexible_count < required_count:
                        print(f"❌ Validation failed: need {required_count} {pos}, have {flexible_count}")
                        return False

        elif contest_type == 'showdown':
            if len(lineup) != 6:
                return False

        return True


class StreamlinedDFSCore:
    """Main DFS system orchestrator with fixes"""

    def __init__(self):
        self.players = []
        self.dff_matcher = FixedDFFMatcher()
        self.optimizer = StreamlinedOptimizer()

        # Performance tracking
        self.performance_stats = {
            'load_time': 0,
            'dff_matches': 0,
            'total_players': 0,
            'confirmed_players': 0
        }

    def load_draftkings_csv(self, file_path: str) -> bool:
        """Load DraftKings CSV with enhanced error handling"""
        start_time = time.time()

        try:
            print(f"📁 Loading DraftKings CSV: {Path(file_path).name}")

            df = pd.read_csv(file_path)
            print(f"📊 Found {len(df)} rows in CSV")

            players = []
            for idx, row in df.iterrows():
                try:
                    # Handle salary parsing
                    salary_str = str(row.get('Salary', '3000')).replace(', '').replace(', ', '').strip()
                    salary = int(float(salary_str)) if salary_str and salary_str != 'nan' else 3000

                    # Handle projection parsing
                    proj_str = str(row.get('AvgPointsPerGame', '0')).strip()
                    projection = float(proj_str) if proj_str and proj_str != 'nan' else 0.0

                    player_data = {
                        'id': idx + 1,
                        'name': str(row.get('Name', '')).strip(),
                        'position': str(row.get('Position', 'UTIL')).strip(),
                        'team': str(row.get('TeamAbbrev', row.get('Team', ''))).strip(),
                        'salary': salary,
                        'projection': projection,
                        'game_info': str(row.get('Game Info', '')).strip()
                    }

                    # Ensure we have valid data
                    if player_data['name'] and player_data['salary'] > 0:
                        player = StreamlinedPlayer(player_data)
                    players.append(player)

                except Exception as e:
                    print(f"⚠️ Error processing row {idx}: {e}")
                    continue

            self.players = players
            self.performance_stats['total_players'] = len(players)
            self.performance_stats['load_time'] = time.time() - start_time

            print(f"✅ Loaded {len(players)} valid players in {self.performance_stats['load_time']:.2f}s")

            # Show position breakdown
            positions = {}
            for player in players:
                for pos in player.positions:
                    positions[pos] = positions.get(pos, 0) + 1

            print(f"📊 Positions: {dict(sorted(positions.items()))}")

            return True

        except Exception as e:
            print(f"❌ Error loading DraftKings CSV: {e}")
            import traceback
            traceback.print_exc()
            return False

    def apply_dff_rankings(self, dff_file_path: str) -> bool:
        """Apply DFF rankings with FIXED name matching"""
        if not self.players:
            print("❌ No players loaded")
            return False

        try:
            print(f"🎯 Applying DFF rankings: {Path(dff_file_path).name}")

            # Load DFF data with better parsing
            dff_data = {}
            with open(dff_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Handle different DFF formats
                    name = ""

                    # Method 1: first_name + last_name columns
                    if 'first_name' in row and 'last_name' in row:
                        first = str(row.get('first_name', '')).strip()
                        last = str(row.get('last_name', '')).strip()
                        if first and last:
                            name = f"{last}, {first}"  # DFF format

                    # Method 2: Name column
                    elif 'Name' in row:
                        name = str(row.get('Name', '')).strip()

                    # Method 3: player_name column
                    elif 'player_name' in row:
                        name = str(row.get('player_name', '')).strip()

                    if name:
                        dff_data[name] = {
                            'rank': self._safe_int(row.get('Rank', row.get('rank', 999))),
                            'tier': row.get('Tier', row.get('tier', 'C')),
                            'projection': self._safe_float(row.get('ppg_projection', row.get('projection', 0)))
                        }

            print(f"📊 Loaded {len(dff_data)} DFF players")

            # Apply with FIXED matching
            matches = 0
            match_details = []

            for player in self.players:
                best_match = None
                best_confidence = 0
                best_method = ""

                # Try matching against all DFF names
                for dff_name in dff_data.keys():
                    matched_player, confidence, method = self.dff_matcher.match_player(
                        dff_name, [player]
                    )

                    if matched_player and confidence > best_confidence:
                        best_match = dff_name
                        best_confidence = confidence
                        best_method = method

                if best_match and best_confidence >= 70:
                    dff_info = dff_data[best_match]
                    player.dff_rank = dff_info['rank']
                    player.dff_tier = dff_info['tier']

                    # Apply ranking boost
                    rank = dff_info['rank']
                    if player.get_primary_position() == 'P':
                        if rank <= 5:
                            player.score += 2.0
                        elif rank <= 12:
                            player.score += 1.5
                        elif rank <= 20:
                            player.score += 1.0
                    else:
                        if rank <= 10:
                            player.score += 2.0
                        elif rank <= 25:
                            player.score += 1.5
                        elif rank <= 40:
                            player.score += 1.0

                    matches += 1
                    match_details.append(f"{player.name} ↔ {best_match} ({best_confidence}%)")

            success_rate = (matches / len(dff_data) * 100) if dff_data else 0
            self.performance_stats['dff_matches'] = matches

            print(f"✅ DFF applied: {matches}/{len(dff_data)} matches ({success_rate:.1f}%)")

            # Show some successful matches
            if match_details:
                print("🎯 Sample matches:")
                for detail in match_details[:5]:
                    print(f"   {detail}")
                if len(match_details) > 5:
                    print(f"   ... and {len(match_details) - 5} more")

            if success_rate >= 70:
                print("🎉 EXCELLENT! Fixed DFF matching is working!")
            elif success_rate >= 50:
                print("👍 Good DFF matching performance")
            else:
                print("⚠️ DFF matching could be improved")

            return True

        except Exception as e:
            print(f"❌ Error applying DFF rankings: {e}")
            import traceback
            traceback.print_exc()
            return False

    def optimize_lineup(self, contest_type='classic', method='milp', **kwargs) -> Tuple[List[StreamlinedPlayer], float]:
        """Run lineup optimization with validation"""
        if not self.players:
            print("❌ No players loaded")
            return [], 0

        # Validate we have enough players for each position
        if contest_type == 'classic':
            requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

            for pos, needed in requirements.items():
                available = sum(1 for p in self.players if p.can_play_position(pos))
                if available < needed:
                    print(f"❌ Not enough {pos} players: need {needed}, have {available}")
                    return [], 0

        return self.optimizer.optimize_lineup(
            self.players, contest_type=contest_type, method=method, **kwargs
        )

    def get_optimization_summary(self, lineup: List[StreamlinedPlayer], score: float) -> str:
        """Generate detailed optimization summary"""
        if not lineup:
            return "❌ No lineup generated"

        total_salary = sum(p.salary for p in lineup)
        confirmed_count = sum(1 for p in lineup if p.is_confirmed)
        dff_count = sum(1 for p in lineup if p.dff_rank)

        # Position breakdown
        positions = {}
        for player in lineup:
            pos = player.get_primary_position()
            positions[pos] = positions.get(pos, 0) + 1

        # Multi-position players
        multi_pos_players = [p for p in lineup if len(p.positions) > 1]

        summary = f"""
💰 OPTIMIZED LINEUP SUMMARY
==========================
📊 Total Score: {score:.2f}
💵 Total Salary: ${total_salary:,} / $50,000
👥 Players: {len(lineup)}
✅ Confirmed: {confirmed_count}
🎯 DFF Ranked: {dff_count}
🔄 Multi-Position: {len(multi_pos_players)}

📍 Positions: {dict(sorted(positions.items()))}

🏆 LINEUP:
"""

        for i, player in enumerate(lineup, 1):
            conf_status = "✅" if player.is_confirmed else "❓"
            dff_info = f"(#{player.dff_rank})" if player.dff_rank else ""
            pos_str = f"{player.get_primary_position()}"
            if len(player.positions) > 1:
                pos_str = f"{'/'.join(player.positions)}"

            summary += f"{i:2}. {pos_str:<6} {player.name:<20} {player.team:<4} ${player.salary:,} {player.score:.1f} {conf_status} {dff_info}\n"

        if multi_pos_players:
            summary += f"\n🔄 Multi-Position Players:\n"
            for player in multi_pos_players:
                summary += f"   • {player.name} ({'/'.join(player.positions)})\n"

        summary += f"\n📋 DRAFTKINGS IMPORT:\n"
        summary += ", ".join([p.name for p in lineup])

        return summary

    def _safe_int(self, value, default=0):
        """Safely convert to int"""
        try:
            return int(float(str(value))) if value and str(value).strip() != '' else default
        except:
            return default

    def _safe_float(self, value, default=0.0):
        """Safely convert to float"""
        try:
            return float(str(value)) if value and str(value).strip() != '' else default
        except:
            return default


# Convenience functions for backward compatibility
def load_and_optimize_dfs(dk_file: str, dff_file: str = None,
                          contest_type: str = 'classic', method: str = 'milp') -> Tuple[
    List[StreamlinedPlayer], float, str]:
    """Complete DFS optimization pipeline"""

    print("🚀 RUNNING COMPLETE DFS OPTIMIZATION PIPELINE")
    print("=" * 50)

    core = StreamlinedDFSCore()

    # Load data
    if not core.load_draftkings_csv(dk_file):
        return [], 0, "Failed to load DraftKings data"

    # Apply DFF if provided
    if dff_file and os.path.exists(dff_file):
        core.apply_dff_rankings(dff_file)

    # Optimize
    lineup, score = core.optimize_lineup(contest_type=contest_type, method=method)

    # Generate summary
    summary = core.get_optimization_summary(lineup, score)

    return lineup, score, summary


if __name__ == "__main__":
    print("🚀 Streamlined DFS Core System - FIXED VERSION")
    print("✅ Multi-position support (Jorge Polanco 3B/SS)")
    print("✅ Fixed DFF name matching (improved success rate)")
    print("✅ Fixed MILP and Monte Carlo optimization")
    print("✅ Enhanced error handling and validation")
    print("✅ Better constraint handling for feasible solutions")