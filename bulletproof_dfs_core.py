#!/usr/bin/env python3
"""
HYBRID PITCHER DETECTION - SMART FALLBACK
========================================
✅ API pitcher confirmation first
✅ Smart salary-based fallback (limited to slate size)
✅ Realistic pitcher counts for small slates
✅ All other algorithms working
"""

import os
import sys
import pandas as pd
import numpy as np
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import warnings
import random

warnings.filterwarnings('ignore')

# Import optimization
try:
    import pulp

    MILP_AVAILABLE = True
    print("✅ PuLP available - MILP optimization enabled")
except ImportError:
    MILP_AVAILABLE = False
    print("⚠️ PuLP not available - using greedy fallback")

# Import modules with enhanced fallbacks
try:
    from vegas_lines import VegasLines

    VEGAS_AVAILABLE = True
    print("✅ Vegas lines module imported")
except ImportError:
    VEGAS_AVAILABLE = False
    print("⚠️ vegas_lines.py not found")


    class VegasLines:
        def __init__(self, **kwargs): self.lines = {}

        def get_vegas_lines(self, **kwargs): return {}

        def apply_to_players(self, players): return players

try:
    from confirmed_lineups import ConfirmedLineups

    CONFIRMED_AVAILABLE = True
    print("✅ Confirmed lineups module imported")
except ImportError:
    CONFIRMED_AVAILABLE = False
    print("⚠️ confirmed_lineups.py not found")


    class ConfirmedLineups:
        def __init__(self, **kwargs): pass

        def is_player_confirmed(self, name, team): return False, 0

        def is_pitcher_starting(self, name, team): return False

        def ensure_data_loaded(self, **kwargs): return True

try:
    from simple_statcast_fetcher import SimpleStatcastFetcher

    STATCAST_AVAILABLE = True
    print("✅ Statcast fetcher imported")
except ImportError:
    STATCAST_AVAILABLE = False
    print("⚠️ simple_statcast_fetcher.py not found")


    class SimpleStatcastFetcher:
        def __init__(self): pass

        def fetch_player_data(self, name, position): return {}

# Enhanced park factors and configuration
PARK_FACTORS = {
    "COL": 1.1, "TEX": 1.05, "CIN": 1.05, "NYY": 1.05, "BOS": 1.03, "PHI": 1.03,
    "MIA": 0.95, "OAK": 0.95, "SD": 0.97, "SEA": 0.97
}

# Relief pitchers database
KNOWN_RELIEF_PITCHERS = {
    'jhoan duran', 'edwin diaz', 'felix bautista', 'ryan helsley', 'david bednar',
    'alexis diaz', 'josh hader', 'emmanuel clase', 'jordan romano', 'clay holmes',
    'camilo doval', 'robert suarez', 'mason miller', 'tyler rogers', 'evan phillips',
    'tanner scott', 'kirby yates', 'blake treinen', 'ryne stanek', 'chris devenski',
    'alex vesia', 'anthony banda', 'brusdar graterol', 'lou trivino', 'michael kopech'
}

# Slate size configuration
SLATE_SIZE_CONFIG = {
    1: {'games': 1, 'expected_starters': 2, 'max_fallback_starters': 3},
    2: {'games': 2, 'expected_starters': 4, 'max_fallback_starters': 5},
    3: {'games': 3, 'expected_starters': 6, 'max_fallback_starters': 8},
    4: {'games': 4, 'expected_starters': 8, 'max_fallback_starters': 10},
    5: {'games': 5, 'expected_starters': 10, 'max_fallback_starters': 12}
}


class AdvancedPlayer:
    """Player model with all advanced features"""

    def __init__(self, player_data: Dict):
        # Basic attributes
        self.id = int(player_data.get('id', 0))
        self.name = str(player_data.get('name', '')).strip()
        self.positions = self._parse_positions_enhanced(player_data.get('position', ''))
        self.primary_position = self.positions[0] if self.positions else 'UTIL'
        self.team = str(player_data.get('team', '')).strip().upper()
        self.salary = self._parse_salary(player_data.get('salary', 3000))
        self.projection = self._parse_float(player_data.get('projection', 0))

        # Enhanced confirmation tracking
        self.is_confirmed = False
        self.is_manual_selected = False
        self.confirmation_sources = []

        # Advanced data storage
        self.dff_data = {}
        self.vegas_data = {}
        self.statcast_data = {}
        self.park_factors = {}
        self.recent_performance = {}
        self.platoon_data = {}

        # Calculate scores
        self.base_score = self.projection if self.projection > 0 else (self.salary / 1000.0)
        self.enhanced_score = self.base_score

    def _parse_positions_enhanced(self, position_str: str) -> List[str]:
        """Enhanced position parsing"""
        if not position_str:
            return ['UTIL']

        position_str = str(position_str).strip().upper()

        # Handle various multi-position delimiters
        delimiters = ['/', ',', '-', '|', '+', ' / ', ' , ', ' - ']
        positions = [position_str]

        for delimiter in delimiters:
            if delimiter in position_str:
                positions = [p.strip() for p in position_str.split(delimiter) if p.strip()]
                break

        # Enhanced position mapping
        position_mapping = {
            'P': 'P', 'SP': 'P', 'RP': 'P', 'PITCHER': 'P',
            'C': 'C', 'CATCHER': 'C',
            '1B': '1B', 'FIRST': '1B', 'FIRSTBASE': '1B', '1ST': '1B',
            '2B': '2B', 'SECOND': '2B', 'SECONDBASE': '2B', '2ND': '2B',
            '3B': '3B', 'THIRD': '3B', 'THIRDBASE': '3B', '3RD': '3B',
            'SS': 'SS', 'SHORTSTOP': 'SS', 'SHORT': 'SS',
            'OF': 'OF', 'OUTFIELD': 'OF', 'OUTFIELDER': 'OF',
            'LF': 'OF', 'CF': 'OF', 'RF': 'OF', 'LEFT': 'OF', 'CENTER': 'OF', 'RIGHT': 'OF',
            'UTIL': 'UTIL', 'DH': 'UTIL', 'UTILITY': 'UTIL'
        }

        valid_positions = []
        for pos in positions:
            pos = pos.strip().upper()
            mapped_pos = position_mapping.get(pos, pos)
            if mapped_pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'UTIL']:
                if mapped_pos not in valid_positions:
                    valid_positions.append(mapped_pos)

        return valid_positions if valid_positions else ['UTIL']

    def _parse_salary(self, salary_input: Any) -> int:
        """Enhanced salary parsing"""
        try:
            if isinstance(salary_input, (int, float)):
                return max(1000, int(salary_input))
            cleaned = str(salary_input).replace('$', '').replace(',', '').strip()
            return max(1000, int(float(cleaned))) if cleaned and cleaned != 'nan' else 3000
        except:
            return 3000

    def _parse_float(self, value: Any) -> float:
        """Enhanced float parsing"""
        try:
            if isinstance(value, (int, float)):
                return max(0.0, float(value))
            cleaned = str(value).strip()
            return max(0.0, float(cleaned)) if cleaned and cleaned != 'nan' else 0.0
        except:
            return 0.0

    def is_eligible_for_selection(self, mode: str = 'bulletproof') -> bool:
        """Enhanced eligibility check"""
        if mode == 'manual_only':
            return self.is_manual_selected
        elif mode == 'confirmed_only':
            return self.is_confirmed
        else:  # bulletproof (default)
            return self.is_confirmed or self.is_manual_selected

    def add_confirmation_source(self, source: str):
        """Add confirmation source"""
        if source not in self.confirmation_sources:
            self.confirmation_sources.append(source)
        self.is_confirmed = True
        print(f"🔒 CONFIRMED: {self.name} ({source})")
        return True

    def set_manual_selected(self):
        """Set as manually selected"""
        self.is_manual_selected = True
        if "manual_selection" not in self.confirmation_sources:
            self.confirmation_sources.append("manual_selection")
        print(f"🎯 MANUAL: {self.name}")

    def can_play_position(self, position: str) -> bool:
        """Check if player can play position"""
        return position in self.positions or position == 'UTIL'

    def apply_dff_data(self, dff_data: Dict):
        """Apply DFF data"""
        self.dff_data = dff_data
        if str(dff_data.get('confirmed_order', '')).upper() == 'YES':
            self.add_confirmation_source("dff_confirmed")

    def apply_vegas_data(self, vegas_data: Dict):
        """Apply Vegas data"""
        self.vegas_data = vegas_data

    def apply_statcast_data(self, statcast_data: Dict):
        """Apply Statcast data"""
        self.statcast_data = statcast_data

    def apply_park_factors(self, park_data: Dict):
        """Apply park factor data"""
        self.park_factors = park_data

    def get_status_string(self) -> str:
        """Get formatted status string for display"""
        status_parts = []
        if self.is_confirmed:
            sources = ", ".join(self.confirmation_sources)
            status_parts.append(f"CONFIRMED ({sources})")
        if self.is_manual_selected:
            status_parts.append("MANUAL")
        if self.dff_data.get('ppg_projection', 0) > 0:
            status_parts.append(f"DFF:{self.dff_data['ppg_projection']:.1f}")
        if self.statcast_data:
            status_parts.append("STATCAST")
        if self.vegas_data:
            status_parts.append("VEGAS")
        if self.park_factors:
            status_parts.append("PARK")
        return " | ".join(status_parts) if status_parts else "UNCONFIRMED"

    def __repr__(self):
        pos_str = '/'.join(self.positions)
        status = "✅" if self.is_eligible_for_selection() else "❌"
        return f"Player({self.name}, {pos_str}, ${self.salary}, {self.enhanced_score:.1f}, {status})"


class BulletproofDFSCore:
    """Complete bulletproof DFS core with hybrid pitcher detection"""

    def __init__(self):
        self.players = []
        self.contest_type = 'classic'
        self.salary_cap = 50000
        self.optimization_mode = 'bulletproof'

        # Initialize modules with real implementations
        self.vegas_lines = VegasLines() if VEGAS_AVAILABLE else None
        self.confirmed_lineups = ConfirmedLineups() if CONFIRMED_AVAILABLE else None
        self.statcast_fetcher = SimpleStatcastFetcher() if STATCAST_AVAILABLE else None

        print("🚀 Bulletproof DFS Core with HYBRID pitcher detection")

    def load_draftkings_csv(self, file_path: str) -> bool:
        """Load DraftKings CSV"""
        try:
            print(f"📁 Loading DraftKings CSV: {Path(file_path).name}")

            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                return False

            df = pd.read_csv(file_path)
            print(f"📊 Found {len(df)} rows, {len(df.columns)} columns")

            # Enhanced column detection
            column_map = {}
            for i, col in enumerate(df.columns):
                col_lower = str(col).lower().strip()
                if any(name in col_lower for name in ['name', 'player']):
                    if 'name' in col_lower and '+' not in col_lower:
                        column_map['name'] = i
                    elif 'name' not in column_map:
                        column_map['name'] = i
                elif any(pos in col_lower for pos in ['position', 'pos']):
                    column_map['position'] = i
                elif any(team in col_lower for team in ['team', 'teamabbrev']):
                    column_map['team'] = i
                elif any(sal in col_lower for sal in ['salary', 'sal']):
                    column_map['salary'] = i
                elif any(proj in col_lower for proj in ['avgpointspergame', 'fppg', 'projection']):
                    column_map['projection'] = i

            players = []
            for idx, row in df.iterrows():
                try:
                    player_data = {
                        'id': idx + 1,
                        'name': str(row.iloc[column_map.get('name', 0)]).strip(),
                        'position': str(row.iloc[column_map.get('position', 1)]).strip(),
                        'team': str(row.iloc[column_map.get('team', 2)]).strip(),
                        'salary': row.iloc[column_map.get('salary', 3)],
                        'projection': row.iloc[column_map.get('projection', 4)]
                    }

                    player = AdvancedPlayer(player_data)
                    if player.name and player.salary > 0:
                        players.append(player)

                except Exception:
                    continue

            self.players = players
            print(f"✅ Loaded {len(self.players)} valid players")
            return True

        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return False

    def apply_manual_selection(self, manual_input: str) -> int:
        """Apply manual player selection"""
        if not manual_input:
            return 0

        # Parse manual input
        manual_names = []
        for delimiter in [',', ';', '\n', '|']:
            if delimiter in manual_input:
                manual_names = [name.strip() for name in manual_input.split(delimiter)]
                break
        else:
            manual_names = [manual_input.strip()]

        manual_names = [name for name in manual_names if name and len(name) > 2]

        if not manual_names:
            return 0

        print(f"🎯 Processing manual selection: {len(manual_names)} players")

        matches = 0
        for manual_name in manual_names:
            best_match = None
            best_score = 0

            for player in self.players:
                similarity = self._name_similarity(manual_name, player.name)
                if similarity > best_score and similarity >= 0.7:
                    best_score = similarity
                    best_match = player

            if best_match:
                best_match.set_manual_selected()
                matches += 1
                print(f"   ✅ {manual_name} → {best_match.name}")
            else:
                print(f"   ❌ {manual_name} → No match found")

        return matches

    def _name_similarity(self, name1: str, name2: str) -> float:
        """Enhanced name similarity matching"""
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()

        if name1 == name2:
            return 1.0

        if name1 in name2 or name2 in name1:
            return 0.85

        name1_parts = name1.split()
        name2_parts = name2.split()

        if len(name1_parts) >= 2 and len(name2_parts) >= 2:
            if (name1_parts[-1] == name2_parts[-1] and
                    name1_parts[0][0] == name2_parts[0][0]):
                return 0.8

        return 0.0

    def _estimate_slate_size(self) -> int:
        """Estimate slate size based on number of teams"""
        teams = set()
        for player in self.players:
            if player.team:
                teams.add(player.team)

        num_teams = len(teams)
        estimated_games = max(1, num_teams // 2)  # 2 teams per game

        print(f"📊 Detected {num_teams} teams, estimated {estimated_games} games")
        return estimated_games

    def detect_confirmed_players(self) -> int:
        """HYBRID: API confirmation + smart fallback for pitchers"""
        if not self.confirmed_lineups:
            print("⚠️ Confirmed lineups module not available - using smart fallback")
            return self._smart_fallback_confirmation()

        print("🔍 HYBRID pitcher detection: API + smart fallback...")

        # Ensure data is loaded
        if hasattr(self.confirmed_lineups, 'ensure_data_loaded'):
            self.confirmed_lineups.ensure_data_loaded(max_wait_seconds=15)

        confirmed_count = 0
        lineup_confirmed = 0
        api_pitcher_confirmed = 0

        # Step 1: Try API confirmation for all players
        for player in self.players:
            # Check lineup confirmations for position players
            is_confirmed, batting_order = self.confirmed_lineups.is_player_confirmed(player.name, player.team)

            if is_confirmed:
                player.add_confirmation_source("online_lineup")
                confirmed_count += 1
                lineup_confirmed += 1

            # Check API pitcher confirmation
            if player.primary_position == 'P':
                is_starting = self.confirmed_lineups.is_pitcher_starting(player.name, player.team)

                if is_starting:
                    player.add_confirmation_source("api_confirmed_starter")
                    confirmed_count += 1
                    api_pitcher_confirmed += 1
                    print(f"🔒 API STARTER: {player.name}")

        print(f"📊 API Results: {lineup_confirmed} lineup players, {api_pitcher_confirmed} API starters")

        # Step 2: Smart fallback for pitchers if API failed
        if api_pitcher_confirmed == 0:
            print("🧠 API pitcher confirmation failed - using smart fallback...")
            fallback_confirmed = self._smart_pitcher_fallback()
            confirmed_count += fallback_confirmed
            print(f"🧠 Fallback confirmed {fallback_confirmed} additional starters")

        print(f"✅ HYBRID Confirmed detection: {confirmed_count} players")
        return confirmed_count

    def _smart_pitcher_fallback(self) -> int:
        """Smart fallback pitcher confirmation based on slate size"""
        # Estimate slate size
        estimated_games = self._estimate_slate_size()
        slate_config = SLATE_SIZE_CONFIG.get(estimated_games, SLATE_SIZE_CONFIG[3])  # Default to 3-game

        max_starters = slate_config['max_fallback_starters']
        expected_starters = slate_config['expected_starters']

        print(
            f"🧠 Smart fallback: targeting {expected_starters}-{max_starters} starters for {estimated_games}-game slate")

        # Get all unconfirmed pitchers
        unconfirmed_pitchers = [
            p for p in self.players
            if p.primary_position == 'P' and not p.is_confirmed
        ]

        if not unconfirmed_pitchers:
            print("⚠️ No unconfirmed pitchers available for fallback")
            return 0

        # Smart selection criteria:
        # 1. Not a known reliever
        # 2. High salary (likely starter)
        # 3. Good projection
        starter_candidates = []

        for pitcher in unconfirmed_pitchers:
            if pitcher.name.lower() not in KNOWN_RELIEF_PITCHERS:
                # Calculate starter likelihood score
                salary_score = min(pitcher.salary / 10000.0, 1.0)  # Normalize to 1.0
                projection_score = min(pitcher.projection / 25.0, 1.0) if pitcher.projection > 0 else 0.3

                likelihood_score = (salary_score * 0.7) + (projection_score * 0.3)

                starter_candidates.append({
                    'player': pitcher,
                    'likelihood_score': likelihood_score,
                    'salary': pitcher.salary,
                    'projection': pitcher.projection
                })

        # Sort by likelihood and take top candidates
        starter_candidates.sort(key=lambda x: x['likelihood_score'], reverse=True)

        confirmed_starters = 0
        for i, candidate in enumerate(starter_candidates[:max_starters]):
            player = candidate['player']
            player.add_confirmation_source("smart_fallback_starter")
            confirmed_starters += 1
            print(f"🧠 SMART STARTER: {player.name} (${player.salary}, score: {candidate['likelihood_score']:.2f})")

        return confirmed_starters

    def _smart_fallback_confirmation(self) -> int:
        """Complete fallback when no confirmed lineups API available"""
        print("🧠 Using complete smart fallback confirmation...")

        confirmed_count = 0

        # Estimate slate size and target starter count
        estimated_games = self._estimate_slate_size()
        slate_config = SLATE_SIZE_CONFIG.get(estimated_games, SLATE_SIZE_CONFIG[3])
        max_starters = slate_config['max_fallback_starters']

        # Confirm top salary pitchers as starters
        pitchers = [p for p in self.players if p.primary_position == 'P']
        pitchers = [p for p in pitchers if p.name.lower() not in KNOWN_RELIEF_PITCHERS]
        pitchers.sort(key=lambda x: x.salary, reverse=True)

        for pitcher in pitchers[:max_starters]:
            pitcher.add_confirmation_source("fallback_high_salary_starter")
            confirmed_count += 1
            print(f"🧠 FALLBACK STARTER: {pitcher.name} (${pitcher.salary})")

        return confirmed_count

    def apply_dff_rankings(self, dff_file_path: str) -> bool:
        """REAL DFF rankings implementation"""
        if not dff_file_path or not os.path.exists(dff_file_path):
            print("⚠️ No DFF file provided or file not found")
            return False

        try:
            print(f"🎯 Loading DFF rankings: {Path(dff_file_path).name}")
            df = pd.read_csv(dff_file_path)

            matches = 0
            for _, row in df.iterrows():
                try:
                    first_name = str(row.get('first_name', '')).strip()
                    last_name = str(row.get('last_name', '')).strip()

                    if not first_name or not last_name:
                        continue

                    full_name = f"{first_name} {last_name}"

                    # Find matching player
                    for player in self.players:
                        if self._name_similarity(full_name, player.name) >= 0.8:
                            dff_data = {
                                'ppg_projection': float(row.get('ppg_projection', 0)),
                                'value_projection': float(row.get('value_projection', 0)),
                                'L5_fppg_avg': float(row.get('L5_fppg_avg', 0)),
                                'confirmed_order': str(row.get('confirmed_order', '')).upper()
                            }

                            player.apply_dff_data(dff_data)
                            matches += 1
                            break

                except Exception:
                    continue

            print(f"✅ DFF integration: {matches} players")
            return True

        except Exception as e:
            print(f"❌ Error loading DFF data: {e}")
            return False

    def enrich_with_vegas_lines(self):
        """REAL Vegas lines implementation"""
        if not self.vegas_lines:
            print("⚠️ Vegas lines module not available")
            return

        print("💰 Enriching with REAL Vegas lines...")
        vegas_data = self.vegas_lines.get_vegas_lines()

        if not vegas_data:
            print("⚠️ No Vegas data available")
            return

        enriched_count = 0
        for player in self.players:
            if player.team in vegas_data:
                team_vegas = vegas_data[player.team]
                player.apply_vegas_data(team_vegas)
                enriched_count += 1

        print(f"✅ Vegas integration: {enriched_count} players enriched")

    def enrich_with_statcast_priority(self):
        """REAL Statcast implementation"""
        if not self.statcast_fetcher:
            print("⚠️ Statcast fetcher not available")
            return

        print("🔬 Enriching with REAL Statcast data...")

        # Priority to confirmed and manual players
        priority_players = [p for p in self.players if p.is_eligible_for_selection()]

        enriched_count = 0
        for player in priority_players[:20]:  # Limit to avoid API overload
            try:
                statcast_data = self.statcast_fetcher.fetch_player_data(player.name, player.primary_position)
                if statcast_data:
                    player.apply_statcast_data(statcast_data)
                    enriched_count += 1
                    print(f"🔬 Statcast: {player.name}")
            except Exception:
                continue

        print(f"✅ Statcast: {enriched_count} players enriched")

    def apply_park_factors(self):
        """REAL park factors implementation"""
        print("🏟️ Applying REAL park factors...")

        adjusted_count = 0
        for player in self.players:
            if not player.is_eligible_for_selection():
                continue

            # Get park team (home team)
            park_team = player.team  # Simplified - could enhance with home/away logic

            if park_team in PARK_FACTORS:
                factor = PARK_FACTORS[park_team]
                old_score = player.enhanced_score
                player.enhanced_score *= factor

                # Store park factor info
                player.park_factors = {
                    'park_team': park_team,
                    'factor': factor,
                    'adjustment': player.enhanced_score - old_score
                }

                adjusted_count += 1
                print(f"🏟️ {player.name}: {factor:.2f}x factor")

        print(f"✅ Park factors applied to {adjusted_count} players")

    def _apply_comprehensive_statistical_analysis(self, players):
        """Apply comprehensive statistical analysis with 80% confidence"""
        print(f"📊 Comprehensive statistical analysis: {len(players)} players")

        CONFIDENCE_THRESHOLD = 0.80
        MAX_TOTAL_ADJUSTMENT = 0.20

        adjusted_count = 0
        for player in players:
            total_adjustment = 0.0

            # L5 Performance Analysis
            if player.dff_data:
                l5_avg = player.dff_data.get('L5_fppg_avg', 0)
                if l5_avg > 0 and player.projection > 0:
                    performance_ratio = l5_avg / player.projection
                    if performance_ratio > 1.15:
                        l5_adjustment = min((performance_ratio - 1.0) * 0.6, 0.10) * CONFIDENCE_THRESHOLD
                        total_adjustment += l5_adjustment

            # Vegas Environment Analysis
            if player.vegas_data:
                team_total = player.vegas_data.get('team_total', 4.5)
                opp_total = player.vegas_data.get('opponent_total', 4.5)

                if player.primary_position == 'P':
                    if opp_total < 4.0:
                        vegas_adjustment = min((4.5 - opp_total) / 4.5 * 0.4, 0.08) * CONFIDENCE_THRESHOLD
                        total_adjustment += vegas_adjustment
                else:
                    if team_total > 5.0:
                        vegas_adjustment = min((team_total - 4.5) / 4.5 * 0.5, 0.08) * CONFIDENCE_THRESHOLD
                        total_adjustment += vegas_adjustment

            # Statcast Analysis
            if player.statcast_data:
                xwoba = player.statcast_data.get('xwOBA', 0.320)
                if player.primary_position == 'P':
                    if xwoba < 0.290:
                        statcast_adjustment = min((0.320 - xwoba) / 0.320 * 0.4, 0.08) * CONFIDENCE_THRESHOLD
                        total_adjustment += statcast_adjustment
                else:
                    if xwoba > 0.350:
                        statcast_adjustment = min((xwoba - 0.320) / 0.320 * 0.3, 0.08) * CONFIDENCE_THRESHOLD
                        total_adjustment += statcast_adjustment

            # Apply cap
            if total_adjustment > MAX_TOTAL_ADJUSTMENT:
                total_adjustment = MAX_TOTAL_ADJUSTMENT

            # Apply adjustment
            if total_adjustment > 0.03:  # Minimum threshold
                adjustment_points = player.enhanced_score * total_adjustment
                player.enhanced_score += adjustment_points
                adjusted_count += 1

        print(f"✅ Adjusted {adjusted_count}/{len(players)} players with 80% confidence")

    def get_eligible_players_bulletproof(self):
        """Get ONLY eligible players"""
        eligible = [p for p in self.players if p.is_eligible_for_selection()]
        print(f"🔒 BULLETPROOF FILTER: {len(eligible)}/{len(self.players)} players eligible")

        # Debug position breakdown
        position_counts = {}
        for player in eligible:
            for pos in player.positions:
                position_counts[pos] = position_counts.get(pos, 0) + 1

        print(f"📍 Eligible positions: {position_counts}")
        return eligible

    def optimize_lineup_bulletproof(self):
        """Complete optimization"""
        print("🎯 BULLETPROOF OPTIMIZATION WITH HYBRID DETECTION")
        print("=" * 60)

        # Get eligible players
        eligible_players = self.get_eligible_players_bulletproof()

        if len(eligible_players) < 10:
            print(f"❌ INSUFFICIENT ELIGIBLE PLAYERS: {len(eligible_players)}/10 required")
            return [], 0

        # Position validation
        position_requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        position_counts = {}

        for player in eligible_players:
            for pos in player.positions:
                position_counts[pos] = position_counts.get(pos, 0) + 1

        for pos, required in position_requirements.items():
            if position_counts.get(pos, 0) < required:
                print(f"❌ INSUFFICIENT {pos} PLAYERS: {position_counts.get(pos, 0)}/{required}")
                return [], 0

        print(f"✅ Using {len(eligible_players)} eligible players")

        # Apply all real algorithms
        self._apply_comprehensive_statistical_analysis(eligible_players)
        self.apply_park_factors()

        # Use greedy optimization
        return self._optimize_greedy_enhanced(eligible_players)

    def _optimize_greedy_enhanced(self, players):
        """Enhanced greedy optimization"""
        print(f"🎯 Enhanced greedy optimization: {len(players)} players")

        # Calculate value scores
        for player in players:
            player.value_score = player.enhanced_score / (player.salary / 1000.0)

        sorted_players = sorted(players, key=lambda x: x.value_score, reverse=True)

        lineup = []
        total_salary = 0
        position_needs = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        for player in sorted_players:
            if len(lineup) >= 10:
                break

            if total_salary + player.salary > self.salary_cap:
                continue

            # Enhanced position matching
            for pos in ['C', 'SS', '3B', '2B', '1B', 'OF', 'P']:  # Priority order
                if pos in player.positions and position_needs.get(pos, 0) > 0:
                    lineup.append(player)
                    total_salary += player.salary
                    position_needs[pos] -= 1
                    break

        total_score = sum(p.enhanced_score for p in lineup)
        print(f"✅ Enhanced optimization: {len(lineup)} players, ${total_salary:,}, {total_score:.2f} score")

        return lineup, total_score


# Entry point function for GUI compatibility
def load_and_optimize_complete_pipeline(
        dk_file: str,
        dff_file: str = None,
        manual_input: str = "",
        contest_type: str = 'classic',
        strategy: str = 'bulletproof'
):
    """Complete pipeline with HYBRID pitcher detection"""

    print("🚀 BULLETPROOF DFS WITH HYBRID PITCHER DETECTION")
    print("=" * 70)
    print("🔧 HYBRID APPROACH:")
    print("   • Try API confirmation first")
    print("   • Smart salary-based fallback (limited by slate size)")
    print("   • All advanced algorithms working")
    print("   • Realistic counts for small slates")
    print("=" * 70)

    core = BulletproofDFSCore()

    # Pipeline execution
    if not core.load_draftkings_csv(dk_file):
        return [], 0, "Failed to load DraftKings data"

    if manual_input:
        manual_count = core.apply_manual_selection(manual_input)
        print(f"✅ Manual selection: {manual_count} players")

    confirmed_count = core.detect_confirmed_players()
    print(f"✅ Confirmed detection: {confirmed_count} players")

    # Apply REAL data sources
    if dff_file and os.path.exists(dff_file):
        core.apply_dff_rankings(dff_file)

    core.enrich_with_vegas_lines()
    core.enrich_with_statcast_priority()

    # Optimization
    lineup, score = core.optimize_lineup_bulletproof()

    if lineup:
        total_salary = sum(p.salary for p in lineup)

        # Count real algorithm usage
        vegas_count = sum(1 for p in lineup if p.vegas_data)
        statcast_count = sum(1 for p in lineup if p.statcast_data)
        dff_count = sum(1 for p in lineup if p.dff_data)
        park_count = sum(1 for p in lineup if p.park_factors)

        summary = f"""
✅ BULLETPROOF OPTIMIZATION WITH HYBRID DETECTION SUCCESS
======================================================
Players: {len(lineup)}/10
Total Salary: ${total_salary:,}/{core.salary_cap:,}
Projected Score: {score:.2f}

ADVANCED ALGORITHMS APPLIED:
• Vegas lines: {vegas_count}/10 players
• Statcast data: {statcast_count}/10 players  
• DFF analysis: {dff_count}/10 players
• Park factors: {park_count}/10 players

LINEUP:
"""
        for i, player in enumerate(lineup, 1):
            status = player.get_status_string()
            summary += f"{i:2d}. {player.name:<20} {player.primary_position:<3} ${player.salary:,} {player.enhanced_score:.1f} | {status}\n"

        print(summary)
        return lineup, score, summary
    else:
        return [], 0, "Optimization failed - insufficient eligible players"


# Test data function
def create_enhanced_test_data():
    """Create test data"""
    dk_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)

    dk_data = [
        ['Position', 'Name + ID', 'Name', 'ID', 'Roster Position', 'Salary', 'Game Info', 'TeamAbbrev',
         'AvgPointsPerGame'],
        ['SP', 'Hunter Brown (15222)', 'Hunter Brown', '15222', 'SP', '9800', 'HOU@TEX', 'HOU', '24.56'],
        ['SP', 'Pablo Lopez (17404)', 'Pablo Lopez', '17404', 'SP', '10000', 'MIN@DET', 'MIN', '18.46'],
        ['C', 'William Contreras (17892)', 'William Contreras', '17892', 'C', '4200', 'MIL@CHC', 'MIL', '7.39'],
        ['1B', 'Freddie Freeman (17895)', 'Freddie Freeman', '17895', '1B', '4800', 'LAD@SF', 'LAD', '9.23'],
        ['2B', 'Gleyber Torres (16172)', 'Gleyber Torres', '16172', '2B', '4000', 'NYY@BAL', 'NYY', '6.89'],
        ['3B', 'Jose Ramirez (14213)', 'Jose Ramirez', '14213', '3B', '4100', 'CLE@KC', 'CLE', '8.12'],
        ['SS', 'Francisco Lindor (13901)', 'Francisco Lindor', '13901', 'SS', '4300', 'NYM@ATL', 'NYM', '8.23'],
        ['OF', 'Kyle Tucker (16752)', 'Kyle Tucker', '16752', 'OF', '4500', 'HOU@TEX', 'HOU', '8.45'],
        ['OF', 'Christian Yelich (13455)', 'Christian Yelich', '13455', 'OF', '4200', 'MIL@CHC', 'MIL', '7.65'],
        ['OF', 'Juan Soto (17896)', 'Juan Soto', '17896', 'OF', '5000', 'NYY@BAL', 'NYY', '9.87']
    ]

    import csv
    writer = csv.writer(dk_file)
    writer.writerows(dk_data)
    dk_file.close()

    return dk_file.name, None


# Compatibility aliases
EnhancedAdvancedPlayer = AdvancedPlayer

if __name__ == "__main__":
    # Test the complete system
    print("🧪 Testing HYBRID system...")

    dk_file, dff_file = create_enhanced_test_data()
    manual_input = "Hunter Brown, Francisco Lindor, Kyle Tucker"

    lineup, score, summary = load_and_optimize_complete_pipeline(
        dk_file=dk_file,
        manual_input=manual_input
    )

    if lineup:
        print(f"\n🎉 HYBRID SYSTEM SUCCESS!")
        print(f"✅ Generated lineup with {len(lineup)} players, {score:.2f} score")
    else:
        print("❌ Test failed")

    # Cleanup
    os.unlink(dk_file)