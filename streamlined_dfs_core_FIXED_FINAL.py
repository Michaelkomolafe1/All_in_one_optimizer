#!/usr/bin/env python3
"""
Enhanced DFS Core System - REAL DATA ONLY
Advanced Statcast integration + DFF enhancement + Real confirmed lineups
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
    from bs4 import BeautifulSoup

    SCRAPING_AVAILABLE = True
    print("✅ Web scraping available - will fetch REAL confirmed lineups")
except ImportError:
    SCRAPING_AVAILABLE = False
    print("⚠️ Web scraping not available - confirmed lineups will be skipped")

try:
    from pybaseball import statcast_batter_exitvelo_barrels, statcast_pitcher_exitvelo_barrels

    PYBASEBALL_AVAILABLE = True
    print("✅ pybaseball available - will fetch REAL Statcast data")
except ImportError:
    PYBASEBALL_AVAILABLE = False
    print("⚠️ pybaseball not available - install with: pip install pybaseball")


class AdvancedPlayer:
    """Advanced player model with real Statcast data and enhanced DFF integration"""

    def __init__(self, player_data: Dict):
        # Core data
        self.id = int(player_data.get('id', 0))
        self.name = str(player_data.get('name', '')).strip()
        self.positions = self._parse_positions_enhanced(player_data.get('position', ''))
        self.primary_position = self.positions[0] if self.positions else 'UTIL'
        self.team = str(player_data.get('team', '')).strip().upper()

        # Financial data
        self.salary = self._parse_salary(player_data.get('salary', 3000))
        self.projection = self._parse_float(player_data.get('projection', 0))

        # Enhanced scoring
        self.base_score = self.projection if self.projection > 0 else (self.salary / 1000.0)
        self.enhanced_score = self.base_score

        # Status tracking
        self.is_confirmed = bool(player_data.get('is_confirmed', False))
        self.confirmed_order = player_data.get('confirmed_order')  # From DFF
        self.batting_order = player_data.get('batting_order')
        self.is_manual_selected = bool(player_data.get('is_manual_selected', False))

        # Enhanced DFF data integration
        self.dff_rank = player_data.get('dff_rank')
        self.dff_tier = player_data.get('dff_tier', 'C')
        self.dff_projection = player_data.get('dff_projection', 0)
        self.dff_value_projection = player_data.get('dff_value_projection', 0)
        self.dff_l5_avg = player_data.get('dff_l5_avg', 0)  # Recent form
        self.dff_l10_avg = player_data.get('dff_l10_avg', 0)

        # Vegas/Game context from DFF
        self.implied_team_score = player_data.get('implied_team_score', 4.5)
        self.over_under = player_data.get('over_under', 8.5)
        self.spread = player_data.get('spread', 0)
        self.pitcher_hand = player_data.get('pitcher_hand', 'R')

        # Advanced Statcast metrics
        self.statcast_data = player_data.get('statcast_data', {})
        self.advanced_metrics = {}

        # Game context
        self.game_info = str(player_data.get('game_info', ''))
        self.opponent = self._extract_opponent()
        self.is_home = self._determine_home_status()

        # Calculate final enhanced score with all data
        self._calculate_advanced_enhanced_score()

    def _parse_positions_enhanced(self, position_str: str) -> List[str]:
        """Enhanced position parsing with more formats"""
        if not position_str:
            return ['UTIL']

        position_str = str(position_str).strip().upper()

        # Handle various delimiters
        delimiters = ['/', ',', '-', '|', '+']
        positions = [position_str]

        for delimiter in delimiters:
            if delimiter in position_str:
                positions = [p.strip() for p in position_str.split(delimiter)]
                break

        # Enhanced mapping
        position_mapping = {
            'SP': 'P', 'RP': 'P', 'PITCHER': 'P', 'STARTING PITCHER': 'P',
            'CATCHER': 'C', 'CA': 'C',
            'FIRST': '1B', 'FIRSTBASE': '1B', '1ST': '1B',
            'SECOND': '2B', 'SECONDBASE': '2B', '2ND': '2B',
            'THIRD': '3B', 'THIRDBASE': '3B', '3RD': '3B',
            'SHORT': 'SS', 'SHORTSTOP': 'SS',
            'OUTFIELD': 'OF', 'OUTFIELDER': 'OF', 'LEFT FIELD': 'OF', 'CENTER FIELD': 'OF', 'RIGHT FIELD': 'OF',
            'LF': 'OF', 'CF': 'OF', 'RF': 'OF',
            'UTIL': 'UTIL', 'UTILITY': 'UTIL', 'DH': 'UTIL'
        }

        valid_positions = []
        for pos in positions:
            pos = pos.strip()
            if pos in position_mapping:
                mapped_pos = position_mapping[pos]
                if mapped_pos not in valid_positions:
                    valid_positions.append(mapped_pos)
            elif pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'UTIL']:
                if pos not in valid_positions:
                    valid_positions.append(pos)

        return valid_positions if valid_positions else ['UTIL']

    def _parse_salary(self, salary_input: Any) -> int:
        """Robust salary parsing"""
        try:
            if isinstance(salary_input, (int, float)):
                return max(1000, int(salary_input))

            cleaned = str(salary_input).replace('$', '').replace(',', '').strip()
            return max(1000, int(float(cleaned))) if cleaned and cleaned != 'nan' else 3000
        except (ValueError, TypeError):
            return 3000

    def _parse_float(self, value: Any) -> float:
        """Robust float parsing"""
        try:
            if isinstance(value, (int, float)):
                return max(0.0, float(value))

            cleaned = str(value).strip()
            return max(0.0, float(cleaned)) if cleaned and cleaned != 'nan' else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _extract_opponent(self) -> str:
        """Extract opponent from game info"""
        if '@' in self.game_info:
            parts = self.game_info.split('@')
            if len(parts) >= 2:
                return parts[1].split()[0] if parts[1] else ''
        elif 'vs' in self.game_info.lower():
            parts = self.game_info.lower().split('vs')
            if len(parts) >= 2:
                return parts[1].split()[0].upper() if parts[1] else ''
        return ''

    def _determine_home_status(self) -> bool:
        """Determine if player is playing at home"""
        if '@' in self.game_info:
            parts = self.game_info.split('@')
            if len(parts) >= 2:
                home_part = parts[1].split()[0] if parts[1] else ''
                return self.team == home_part
        return False

    def _calculate_advanced_enhanced_score(self):
        """ADVANCED: Calculate enhanced score with real Statcast + DFF data"""
        score = self.base_score

        # 1. DFF Enhancement (Strong weight - these are expert projections)
        if self.dff_projection > 0:
            # Use DFF projection as primary if available
            dff_boost = (self.dff_projection - self.projection) * 0.5  # 50% weight to DFF difference
            score += dff_boost

        if self.dff_value_projection > 0:
            # Value projection bonus (DFF's value calculation)
            if self.dff_value_projection >= 2.0:
                score += 2.5  # Excellent value
            elif self.dff_value_projection >= 1.8:
                score += 2.0  # Good value
            elif self.dff_value_projection >= 1.6:
                score += 1.5  # Decent value
            elif self.dff_value_projection <= 1.3:
                score -= 1.0  # Poor value

        # 2. Recent Form Analysis (L5 vs season average)
        if self.dff_l5_avg > 0 and self.projection > 0:
            recent_form_diff = self.dff_l5_avg - self.projection
            if recent_form_diff >= 3.0:
                score += 1.5  # Hot streak
            elif recent_form_diff >= 1.5:
                score += 1.0  # Good recent form
            elif recent_form_diff <= -3.0:
                score -= 1.5  # Cold streak
            elif recent_form_diff <= -1.5:
                score -= 1.0  # Poor recent form

        # 3. Confirmed Lineup Status (from DFF confirmed_order)
        if self.confirmed_order and self.confirmed_order.upper() == 'YES':
            self.is_confirmed = True
            score += 2.5  # Strong confirmed bonus

            # Batting order bonus if we have it
            if self.batting_order and isinstance(self.batting_order, (int, float)):
                if 1 <= self.batting_order <= 3:
                    score += 2.0  # Top of order
                elif 4 <= self.batting_order <= 6:
                    score += 1.0  # Middle order

        # 4. Manual Selection Bonus
        if self.is_manual_selected:
            score += 3.5  # Very strong manual preference
            print(f"   🎯 Manual boost applied to {self.name}: +3.5 points")

        # 5. Vegas/Game Context Enhancement
        if self.implied_team_score > 0:
            if self.primary_position == 'P':
                # For pitchers, look at opponent implied score (lower is better)
                opp_implied = self.over_under - self.implied_team_score if self.over_under > 0 else 4.5
                if opp_implied <= 3.5:
                    score += 2.5  # Great matchup
                elif opp_implied <= 4.0:
                    score += 1.5  # Good matchup
                elif opp_implied >= 5.5:
                    score -= 1.5  # Tough matchup
            else:
                # For hitters, higher team total is better
                if self.implied_team_score >= 5.5:
                    score += 2.5  # High-scoring game expected
                elif self.implied_team_score >= 5.0:
                    score += 2.0  # Good scoring environment
                elif self.implied_team_score >= 4.5:
                    score += 1.0  # Average
                elif self.implied_team_score <= 3.5:
                    score -= 1.5  # Low-scoring game expected

        # 6. Advanced Statcast Enhancement
        if self.statcast_data:
            score += self._calculate_statcast_boost()

        # 7. Handedness Matchup (if we have opposing pitcher hand)
        if self.pitcher_hand and self.primary_position != 'P':
            # Platoon advantages (simplified - would need batter handedness for full effect)
            if self.pitcher_hand == 'L':  # Lefty pitcher
                score += 0.5  # Slight boost for facing lefty (most batters are right-handed)

        self.enhanced_score = max(1.0, score)

    def _calculate_statcast_boost(self) -> float:
        """Calculate boost from advanced Statcast metrics"""
        boost = 0.0

        if self.primary_position == 'P':
            # Pitcher Statcast analysis
            hard_hit_against = self.statcast_data.get('Hard_Hit', 35.0)
            xwoba_against = self.statcast_data.get('xwOBA', 0.320)
            k_rate = self.statcast_data.get('K', 20.0)
            bb_rate = self.statcast_data.get('BB', 9.0)
            barrel_against = self.statcast_data.get('Barrel', 8.0)

            # Hard Hit Against (lower is better for pitchers)
            if hard_hit_against <= 30.0:
                boost += 3.0  # Elite contact suppression
            elif hard_hit_against <= 35.0:
                boost += 2.0  # Very good
            elif hard_hit_against <= 40.0:
                boost += 1.0  # Good
            elif hard_hit_against >= 50.0:
                boost -= 2.0  # Poor

            # xwOBA Against (lower is better for pitchers)
            if xwoba_against <= 0.280:
                boost += 2.5  # Dominant
            elif xwoba_against <= 0.300:
                boost += 1.5  # Very good
            elif xwoba_against <= 0.320:
                boost += 0.5  # Average
            elif xwoba_against >= 0.360:
                boost -= 2.0  # Poor

            # Strikeout Rate (higher is better for pitchers)
            if k_rate >= 30.0:
                boost += 2.5  # Elite strikeout rate
            elif k_rate >= 25.0:
                boost += 2.0  # Very good
            elif k_rate >= 22.0:
                boost += 1.0  # Good
            elif k_rate <= 18.0:
                boost -= 1.5  # Low strikeouts

            # Walk Rate (lower is better for pitchers)
            if bb_rate <= 6.0:
                boost += 1.5  # Excellent control
            elif bb_rate <= 8.0:
                boost += 1.0  # Good control
            elif bb_rate >= 12.0:
                boost -= 1.5  # Poor control

            # Barrel Rate Against (lower is better for pitchers)
            if barrel_against <= 5.0:
                boost += 1.5  # Great power suppression
            elif barrel_against >= 12.0:
                boost -= 1.5  # Allows too much power

        else:
            # Hitter Statcast analysis
            hard_hit = self.statcast_data.get('Hard_Hit', 35.0)
            xwoba = self.statcast_data.get('xwOBA', 0.320)
            barrel_rate = self.statcast_data.get('Barrel', 6.0)
            sprint_speed = self.statcast_data.get('Sprint', 27.0)
            k_rate = self.statcast_data.get('K', 22.0)
            bb_rate = self.statcast_data.get('BB', 8.5)
            sweet_spot = self.statcast_data.get('Sweet_Spot', 32.0)

            # Hard Hit Rate (higher is better for hitters)
            if hard_hit >= 50.0:
                boost += 3.0  # Elite contact (like Seiya Suzuki 51.0%)
            elif hard_hit >= 45.0:
                boost += 2.5  # Very good
            elif hard_hit >= 40.0:
                boost += 2.0  # Good
            elif hard_hit >= 35.0:
                boost += 1.0  # Average
            elif hard_hit <= 25.0:
                boost -= 1.5  # Poor contact

            # xwOBA (higher is better for hitters)
            if xwoba >= 0.400:
                boost += 3.0  # Elite (like Kyle Tucker .412)
            elif xwoba >= 0.370:
                boost += 2.5  # Very good
            elif xwoba >= 0.340:
                boost += 2.0  # Good
            elif xwoba >= 0.320:
                boost += 1.0  # Average
            elif xwoba <= 0.280:
                boost -= 2.0  # Poor

            # Barrel Rate (higher is better for hitters)
            if barrel_rate >= 20.0:
                boost += 3.0  # Elite power (like Will Benson 23.1%)
            elif barrel_rate >= 15.0:
                boost += 2.5  # Very good power
            elif barrel_rate >= 10.0:
                boost += 2.0  # Good power
            elif barrel_rate >= 8.0:
                boost += 1.0  # Decent power
            elif barrel_rate <= 3.0:
                boost -= 1.0  # Little power

            # Sprint Speed (speed creates extra value in DFS)
            if sprint_speed >= 29.5:
                boost += 2.0  # Elite speed (steals, extra bases)
            elif sprint_speed >= 28.5:
                boost += 1.5  # Very good speed
            elif sprint_speed >= 27.5:
                boost += 1.0  # Good speed
            elif sprint_speed <= 25.0:
                boost -= 0.5  # Slow

            # Plate Discipline
            if k_rate <= 15.0:
                boost += 1.5  # Excellent contact
            elif k_rate <= 20.0:
                boost += 1.0  # Good contact
            elif k_rate >= 30.0:
                boost -= 2.0  # High strikeout risk
            elif k_rate >= 25.0:
                boost -= 1.0  # Concerning strikeouts

            # Walk Rate (patience creates value)
            if bb_rate >= 12.0:
                boost += 1.5  # Excellent patience
            elif bb_rate >= 10.0:
                boost += 1.0  # Good patience
            elif bb_rate <= 5.0:
                boost -= 0.5  # Impatient

            # Sweet Spot % (launch angle 8-32 degrees)
            if sweet_spot >= 40.0:
                boost += 1.5  # Great launch angle approach
            elif sweet_spot >= 35.0:
                boost += 1.0  # Good approach
            elif sweet_spot <= 25.0:
                boost -= 1.0  # Poor launch angles

        return boost

    def can_play_position(self, position: str) -> bool:
        """Check if player can play specific position"""
        return position in self.positions or position == 'UTIL'

    def get_primary_position(self) -> str:
        """Get primary position for display/sorting"""
        return self.primary_position

    def get_position_flexibility(self) -> int:
        """Get number of positions this player can play"""
        return len(self.positions)

    def is_multi_position(self) -> bool:
        """Check if player has multi-position eligibility"""
        return len(self.positions) > 1

    def get_value_score(self) -> float:
        """Calculate value score (points per $1000 salary)"""
        return self.enhanced_score / (self.salary / 1000.0) if self.salary > 0 else 0

    def get_recent_form_indicator(self) -> str:
        """Get recent form indicator"""
        if self.dff_l5_avg > 0 and self.projection > 0:
            diff = self.dff_l5_avg - self.projection
            if diff >= 3.0:
                return "🔥 HOT"
            elif diff >= 1.5:
                return "📈 GOOD"
            elif diff <= -3.0:
                return "🧊 COLD"
            elif diff <= -1.5:
                return "📉 POOR"
        return "➡️ STEADY"

    def __repr__(self):
        pos_str = '/'.join(self.positions) if len(self.positions) > 1 else self.primary_position
        status = []

        if self.is_confirmed:
            status.append('CONF')
        if self.is_manual_selected:
            status.append('MANUAL')
        if self.dff_projection > 0:
            status.append(f'DFF:{self.dff_projection:.1f}')
        if self.dff_value_projection > 0:
            status.append(f'VAL:{self.dff_value_projection:.2f}')

        # Recent form
        form = self.get_recent_form_indicator()
        if form != "➡️ STEADY":
            status.append(form)

        status_str = f" [{','.join(status)}]" if status else ""
        return f"AdvancedPlayer({self.name}, {pos_str}, ${self.salary}, {self.enhanced_score:.1f}{status_str})"


class RealStatcastDataService:
    """Fetches REAL Statcast data from Baseball Savant - NO MOCK DATA"""

    def __init__(self):
        self.cache_dir = "data/statcast_cache"
        self.cache_expiry_hours = 6  # Cache for 6 hours
        self.current_year = datetime.now().year
        self.session_data = {}

        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)

        print("🔬 Real Statcast Data Service initialized")
        if not PYBASEBALL_AVAILABLE:
            print("⚠️ pybaseball not available - Statcast data will be skipped")

    def fetch_player_statcast_data(self, player_name: str, is_pitcher: bool = False) -> Dict:
        """Fetch real Statcast data for a player"""
        if not PYBASEBALL_AVAILABLE:
            print(f"⚠️ Skipping Statcast for {player_name} - pybaseball not available")
            return {}

        # Check cache first
        cache_key = f"{player_name.replace(' ', '_')}_{is_pitcher}_{self.current_year}"
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        if self._is_cache_valid(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                print(f"   📊 {player_name}: Using cached Statcast data")
                return cached_data
            except Exception:
                pass

        # Fetch real data
        try:
            print(f"   🌐 {player_name}: Fetching REAL Statcast data...")

            if is_pitcher:
                data = self._fetch_pitcher_statcast(player_name)
            else:
                data = self._fetch_hitter_statcast(player_name)

            # Cache the data
            if data:
                try:
                    with open(cache_file, 'w') as f:
                        json.dump(data, f)
                    print(f"   ✅ {player_name}: Real Statcast data cached")
                except Exception as e:
                    print(f"   ⚠️ Cache error for {player_name}: {e}")

            return data

        except Exception as e:
            print(f"   ⚠️ {player_name}: Statcast fetch failed - {e}")
            return {}

    def _fetch_hitter_statcast(self, player_name: str) -> Dict:
        """Fetch real hitter Statcast data"""
        try:
            # Get exit velocity and barrel data
            exitvelo_data = statcast_batter_exitvelo_barrels(self.current_year)

            # Find player in data
            player_row = self._find_player_in_data(player_name, exitvelo_data)

            if player_row is None:
                print(f"   ⚠️ {player_name}: Not found in Baseball Savant database")
                return {}

            # Extract advanced metrics
            statcast_metrics = {
                'data_source': 'Baseball Savant (Real)',
                'season': self.current_year,
                'fetch_time': datetime.now().isoformat(),

                # Core metrics
                'Hard_Hit': float(player_row.get('hard_hit_percent', 35.0)),
                'Barrel': float(player_row.get('barrel_batted_rate', 6.0)),
                'xwOBA': float(player_row.get('xwoba', 0.320)),
                'xBA': float(player_row.get('xba', 0.250)),
                'xSLG': float(player_row.get('xslg', 0.400)),

                # Exit velocity metrics
                'avg_exit_velocity': float(player_row.get('avg_hit_speed', 88.0)),
                'max_exit_velocity': float(player_row.get('max_hit_speed', 95.0)),
                'ev50': float(player_row.get('ev50', 88.0)),  # Top 50% exit velo

                # Launch angle
                'avg_launch_angle': float(player_row.get('avg_hit_angle', 12.0)),
                'Sweet_Spot': float(player_row.get('sweet_spot_percent', 32.0)),  # 8-32 degrees

                # Plate discipline (if available)
                'K': float(player_row.get('k_percent', 22.0)),
                'BB': float(player_row.get('bb_percent', 8.5)),
                'Chase': float(player_row.get('o_swing_percent', 25.0)),

                # Speed (if available)
                'Sprint': float(player_row.get('sprint_speed', 27.0)),

                # Batted ball profile
                'Pull': float(player_row.get('pull_percent', 35.0)),
                'GB': float(player_row.get('groundball_percent', 45.0)),
                'FB': float(player_row.get('flyball_percent', 35.0)),
                'LD': float(player_row.get('linedrive_percent', 20.0))
            }

            print(
                f"   ✅ {player_name}: Real hitter data - {statcast_metrics['Hard_Hit']:.1f}% HardHit, {statcast_metrics['xwOBA']:.3f} xwOBA")
            return statcast_metrics

        except Exception as e:
            print(f"   ❌ {player_name}: Hitter data fetch error - {e}")
            return {}

    def _fetch_pitcher_statcast(self, player_name: str) -> Dict:
        """Fetch real pitcher Statcast data"""
        try:
            # Get pitcher exit velocity data (what they allow)
            pitcher_data = statcast_pitcher_exitvelo_barrels(self.current_year)

            # Find player in data
            player_row = self._find_player_in_data(player_name, pitcher_data)

            if player_row is None:
                print(f"   ⚠️ {player_name}: Not found in Baseball Savant pitcher database")
                return {}

            # Extract pitcher metrics (what they allow to opposing hitters)
            statcast_metrics = {
                'data_source': 'Baseball Savant (Real)',
                'season': self.current_year,
                'fetch_time': datetime.now().isoformat(),

                # What pitcher allows (lower is better)
                'Hard_Hit': float(player_row.get('hard_hit_percent', 35.0)),  # Hard hit allowed
                'Barrel': float(player_row.get('barrel_batted_rate', 8.0)),  # Barrels allowed
                'xwOBA': float(player_row.get('xwoba', 0.320)),  # xwOBA against
                'xBA': float(player_row.get('xba', 0.250)),  # xBA against
                'xSLG': float(player_row.get('xslg', 0.400)),  # xSLG against

                # Pitcher performance
                'K': float(player_row.get('k_percent', 22.0)),  # Strikeout rate
                'BB': float(player_row.get('bb_percent', 9.0)),  # Walk rate
                'WHIP': float(player_row.get('whip', 1.25)),

                # What they allow
                'avg_exit_velocity_against': float(player_row.get('avg_hit_speed', 88.0)),
                'max_exit_velocity_against': float(player_row.get('max_hit_speed', 95.0)),

                # Pitch arsenal (if available)
                'avg_velocity': float(player_row.get('avg_velocity', 93.0)),
                'max_velocity': float(player_row.get('max_velocity', 97.0)),

                # Batted ball profile allowed
                'GB_against': float(player_row.get('groundball_percent', 45.0)),
                'FB_against': float(player_row.get('flyball_percent', 35.0)),
                'LD_against': float(player_row.get('linedrive_percent', 20.0))
            }

            print(
                f"   ✅ {player_name}: Real pitcher data - {statcast_metrics['K']:.1f}% K, {statcast_metrics['Hard_Hit']:.1f}% HardHit Against")
            return statcast_metrics

        except Exception as e:
            print(f"   ❌ {player_name}: Pitcher data fetch error -{e}")
            print(f"   ❌ {player_name}: Pitcher data fetch error - {e}")
            return {}

            def _find_player_in_data(self, player_name: str, dataframe) -> Optional[Dict]:
                """Find player in Baseball Savant dataframe with enhanced matching"""
                if dataframe is None or dataframe.empty:
                    return None

                # Normalize the search name
                search_name = self._normalize_name_for_search(player_name)

                # Baseball Savant uses 'last_name, first_name' format
                name_column = None
                if 'last_name, first_name' in dataframe.columns:
                    name_column = 'last_name, first_name'
                elif 'player_name' in dataframe.columns:
                    name_column = 'player_name'
                else:
                    print(f"   ⚠️ No name column found in Statcast data")
                    return None

                # Convert search name to Baseball Savant format
                if ' ' in search_name:
                    parts = search_name.split()
                    first_name = parts[0]
                    last_name = ' '.join(parts[1:])
                    savant_format = f"{last_name}, {first_name}"
                else:
                    savant_format = search_name

                # Try exact match
                exact_matches = dataframe[dataframe[name_column].str.upper() == savant_format.upper()]
                if not exact_matches.empty:
                    return exact_matches.iloc[0].to_dict()

                # Try partial match on last name
                if ',' in savant_format:
                    last_name_only = savant_format.split(',')[0].strip()
                    partial_matches = dataframe[
                        dataframe[name_column].str.upper().str.contains(last_name_only.upper(), na=False)
                    ]

                    if not partial_matches.empty:
                        # Look for best match
                        for _, row in partial_matches.iterrows():
                            if search_name.upper() in row[name_column].upper():
                                return row.to_dict()
                        # Return first partial match if no exact substring match
                        return partial_matches.iloc[0].to_dict()

                return None

            def _normalize_name_for_search(self, name: str) -> str:
                """Normalize name for Baseball Savant search"""
                # Remove common suffixes
                name = str(name).strip()
                suffixes = [' Jr.', ' Sr.', ' III', ' II', ' IV', ' Jr', ' Sr']
                for suffix in suffixes:
                    if name.endswith(suffix):
                        name = name[:-len(suffix)]

                return name.strip()

            def _is_cache_valid(self, cache_file: str) -> bool:
                """Check if cache file is still valid"""
                if not os.path.exists(cache_file):
                    return False

                try:
                    file_age_hours = (time.time() - os.path.getmtime(cache_file)) / 3600
                    return file_age_hours < self.cache_expiry_hours
                except:
                    return False

            def enrich_players_with_statcast(self, players: List[AdvancedPlayer]) -> List[AdvancedPlayer]:
                """Enrich all players with real Statcast data"""
                if not PYBASEBALL_AVAILABLE:
                    print("⚠️ Skipping Statcast enrichment - pybaseball not available")
                    return players

                print(f"🔬 Enriching {len(players)} players with REAL Statcast data...")
                print("   This may take 2-3 minutes for fresh data...")

                enriched_count = 0
                skipped_count = 0

                for i, player in enumerate(players):
                    try:
                        # Progress indicator
                        if i % 5 == 0 and i > 0:
                            print(f"   Progress: {i}/{len(players)} players processed...")

                        is_pitcher = player.primary_position == 'P'
                        statcast_data = self.fetch_player_statcast_data(player.name, is_pitcher)

                        if statcast_data:
                            player.statcast_data = statcast_data
                            player.advanced_metrics = statcast_data
                            # Recalculate enhanced score with new Statcast data
                            player._calculate_advanced_enhanced_score()
                            enriched_count += 1
                        else:
                            skipped_count += 1

                    except Exception as e:
                        print(f"   ⚠️ Error processing {player.name}: {e}")
                        skipped_count += 1
                        continue

                print(f"✅ Statcast enrichment complete: {enriched_count} enhanced, {skipped_count} skipped")
                return players

        class EnhancedDFFProcessor:
            """Process DFF cheat sheet data with all advanced fields"""

            def __init__(self):
                self.dff_data = {}
                self.name_matcher = EnhancedDFFMatcher()

            def load_dff_cheat_sheet(self, file_path: str) -> bool:
                """Load enhanced DFF cheat sheet with all fields"""
                try:
                    print(f"🎯 Loading enhanced DFF cheat sheet: {Path(file_path).name}")

                    # Read CSV with enhanced parsing
                    df = pd.read_csv(file_path)
                    print(f"📊 Found {len(df)} entries in DFF sheet")

                    # Show available columns
                    print(f"📋 Available columns: {list(df.columns)}")

                    processed_count = 0

                    for _, row in df.iterrows():
                        try:
                            # Extract player name
                            first_name = str(row.get('first_name', '')).strip()
                            last_name = str(row.get('last_name', '')).strip()

                            if not first_name or not last_name:
                                continue

                            full_name = f"{first_name} {last_name}"

                            # Extract all enhanced DFF data
                            dff_player_data = {
                                'name': full_name,
                                'position': str(row.get('position', '')).strip().upper(),
                                'team': str(row.get('team', '')).strip().upper(),
                                'opponent': str(row.get('opp', '')).strip().upper(),

                                # Confirmed lineup info
                                'confirmed_order': str(row.get('confirmed_order', '')).strip().upper(),
                                'starting_pitcher': str(row.get('starting_pitcher', '')).strip().upper(),

                                # Financial data
                                'salary': self._safe_int(row.get('salary', 0)),

                                # DFF projections and analysis
                                'ppg_projection': self._safe_float(row.get('ppg_projection', 0)),
                                'value_projection': self._safe_float(row.get('value_projection', 0)),
                                'l5_fppg_avg': self._safe_float(row.get('L5_fppg_avg', 0)),
                                'l10_fppg_avg': self._safe_float(row.get('L10_fppg_avg', 0)),
                                'szn_fppg_avg': self._safe_float(row.get('szn_fppg_avg', 0)),

                                # Vegas data
                                'implied_team_score': self._safe_float(row.get('implied_team_score', 4.5)),
                                'over_under': self._safe_float(row.get('over_under', 8.5)),
                                'spread': self._safe_float(row.get('spread', 0)),

                                # Pitcher info
                                'pitcher_hand': str(row.get('hand', 'R')).strip().upper(),

                                # Game context
                                'injury_status': str(row.get('injury_status', '')).strip(),
                                'game_date': str(row.get('game_date', '')).strip(),
                                'slate': str(row.get('slate', '')).strip()
                            }

                            self.dff_data[full_name] = dff_player_data
                            processed_count += 1

                        except Exception as e:
                            print(f"   ⚠️ Error processing DFF row: {e}")
                            continue

                    print(f"✅ Processed {processed_count} DFF entries")
                    return processed_count > 0

                except Exception as e:
                    print(f"❌ Error loading DFF cheat sheet: {e}")
                    return False

            def apply_dff_data_to_players(self, players: List[AdvancedPlayer]) -> int:
                """Apply enhanced DFF data to players with advanced matching"""
                if not self.dff_data:
                    print("⚠️ No DFF data loaded")
                    return 0

                print(f"🎯 Applying enhanced DFF data to {len(players)} players...")

                matches = 0
                match_details = []

                for dff_name, dff_info in self.dff_data.items():
                    # Find matching player
                    matched_player, confidence, method = self.name_matcher.match_player(
                        dff_name, players, dff_info.get('team')
                    )

                    if matched_player and confidence >= 70:
                        # Apply all DFF enhancements
                        matched_player.dff_projection = dff_info.get('ppg_projection', 0)
                        matched_player.dff_value_projection = dff_info.get('value_projection', 0)
                        matched_player.dff_l5_avg = dff_info.get('l5_fppg_avg', 0)
                        matched_player.dff_l10_avg = dff_info.get('l10_fppg_avg', 0)

                        # Vegas context
                        matched_player.implied_team_score = dff_info.get('implied_team_score', 4.5)
                        matched_player.over_under = dff_info.get('over_under', 8.5)
                        matched_player.spread = dff_info.get('spread', 0)
                        matched_player.pitcher_hand = dff_info.get('pitcher_hand', 'R')

                        # Confirmed status
                        matched_player.confirmed_order = dff_info.get('confirmed_order', '')

                        # Recalculate enhanced score with all new DFF data
                        matched_player._calculate_advanced_enhanced_score()

                        matches += 1

                        # Show key enhancements
                        enhancements = []
                        if dff_info.get('ppg_projection', 0) > 0:
                            enhancements.append(f"PROJ:{dff_info['ppg_projection']:.1f}")
                        if dff_info.get('value_projection', 0) > 0:
                            enhancements.append(f"VAL:{dff_info['value_projection']:.2f}")
                        if dff_info.get('confirmed_order', '') == 'YES':
                            enhancements.append("CONF")

                        match_details.append(
                            f"{matched_player.name} ↔ {dff_name} ({confidence:.0f}%) [{','.join(enhancements)}]")

                success_rate = (matches / len(self.dff_data) * 100) if self.dff_data else 0
                print(f"✅ DFF integration: {matches}/{len(self.dff_data)} matches ({success_rate:.1f}%)")

                if match_details:
                    print("🎯 Sample DFF enhancements:")
                    for detail in match_details[:5]:
                        print(f"   {detail}")
                    if len(match_details) > 5:
                        print(f"   ...and {len(match_details) - 5} more")

                if success_rate >= 85:
                    print("🎉 EXCELLENT! DFF integration working perfectly!")
                elif success_rate >= 70:
                    print("👍 Good DFF integration success rate")

                return matches

            def _safe_float(self, value: Any) -> float:
                """Safely convert to float"""
                try:
                    if isinstance(value, (int, float)):
                        return float(value)
                    cleaned = str(value).strip()
                    return float(cleaned) if cleaned and cleaned.lower() not in ['nan', '', 'none'] else 0.0
                except (ValueError, TypeError):
                    return 0.0

            def _safe_int(self, value: Any) -> int:
                """Safely convert to int"""
                try:
                    if isinstance(value, (int, float)):
                        return int(value)
                    cleaned = str(value).strip()
                    return int(float(cleaned)) if cleaned and cleaned.lower() not in ['nan', '', 'none'] else 0
                except (ValueError, TypeError):
                    return 0

        class EnhancedDFFMatcher:
            """Enhanced DFF name matching with multiple strategies"""

            @staticmethod
            def normalize_name(name: str) -> str:
                """Enhanced name normalization"""
                if not name:
                    return ""

                name = str(name).strip()

                # Handle "Last, First" format from DFF
                if ',' in name:
                    parts = name.split(',', 1)
                    if len(parts) == 2:
                        last = parts[0].strip()
                        first = parts[1].strip()
                        name = f"{first} {last}"

                # Clean up
                name = name.lower()
                name = ' '.join(name.split())

                # Remove suffixes and common variations
                suffixes = [' jr', ' sr', ' iii', ' ii', ' iv', ' jr.', ' sr.', '  jr', '  sr']
                for suffix in suffixes:
                    if name.endswith(suffix):
                        name = name[:-len(suffix)].strip()

                return name

            @staticmethod
            def match_player(dff_name: str, players: List[AdvancedPlayer], team_hint: str = None) -> Tuple[
                Optional[AdvancedPlayer], float, str]:
                """Enhanced player matching with multiple strategies"""
                best_match = None
                best_score = 0.0
                best_method = "no_match"

                dff_normalized = EnhancedDFFMatcher.normalize_name(dff_name)

                for player in players:
                    player_normalized = EnhancedDFFMatcher.normalize_name(player.name)

                    # Strategy 1: Exact match
                    if dff_normalized == player_normalized:
                        return player, 100.0, "exact_match"

                    # Strategy 2: Calculate similarity score
                    similarity = 0.0

                    dff_parts = dff_normalized.split()
                    player_parts = player_normalized.split()

                    if len(dff_parts) >= 2 and len(player_parts) >= 2:
                        # First and last name exact match
                        if dff_parts[0] == player_parts[0] and dff_parts[-1] == player_parts[-1]:
                            similarity = 95.0
                        # Last name and first initial match
                        elif (dff_parts[-1] == player_parts[-1] and
                              len(dff_parts[0]) > 0 and len(player_parts[0]) > 0 and
                              dff_parts[0][0] == player_parts[0][0]):
                            similarity = 85.0
                        # Last name only match
                        elif dff_parts[-1] == player_parts[-1]:
                            similarity = 75.0
                        # First name only match (less reliable)
                        elif dff_parts[0] == player_parts[0]:
                            similarity = 60.0

                    # Strategy 3: Partial string matching
                    if dff_normalized in player_normalized:
                        similarity = max(similarity, 80.0)
                    elif player_normalized in dff_normalized:
                        similarity = max(similarity, 80.0)

                    # Strategy 4: Fuzzy matching for similar names
                    if abs(len(dff_normalized) - len(player_normalized)) <= 3:
                        common_chars = sum(1 for a, b in zip(dff_normalized, player_normalized) if a == b)
                        char_similarity = (common_chars / max(len(dff_normalized), len(player_normalized))) * 100
                        if char_similarity >= 70:
                            similarity = max(similarity, char_similarity)

                    # Strategy 5: Team matching bonus
                    if team_hint and player.team and team_hint.upper() == player.team.upper():
                        similarity += 10.0  # Boost for team match

                    # Update best match
                    if similarity > best_score:
                        best_score = similarity
                        best_match = player
                        if similarity >= 95:
                            best_method = "exact_parts_match"
                        elif similarity >= 85:
                            best_method = "strong_match"
                        elif similarity >= 75:
                            best_method = "good_match"
                        else:
                            best_method = "partial_match"

                return best_match, best_score, best_method


class RealConfirmedLineupService:
    """Fetches REAL confirmed lineups ONLY - NO MOCK DATA EVER"""

    def __init__(self):
        self.confirmed_sources = [
            {
                'name': 'RotoWire MLB Lineups',
                'url': 'https://www.rotowire.com/baseball/daily-lineups.php',
                'parser': self._parse_rotowire
            },
            {
                'name': 'Baseball Press',
                'url': 'https://www.baseballpress.com/lineups',
                'parser': self._parse_baseball_press
            },
            {
                'name': 'MLB Starting Lineups',
                'url': 'https://www.mlb.com/starting-lineups',
                'parser': self._parse_mlb_lineups
            },
            {
                'name': 'DailyBaseballData',
                'url': 'https://www.dailybaseballdata.com/cgi-bin/lineups.pl',
                'parser': self._parse_daily_baseball_data
            }
        ]
        self.confirmed_data = {}
        self.fetch_attempts = 0
        self.successful_sources = []

    def fetch_confirmed_lineups(self) -> Dict[str, Dict[str, int]]:
        """Fetch confirmed lineups from REAL sources ONLY - never returns mock data"""

        if not SCRAPING_AVAILABLE:
            print("⚠️ Web scraping not available - confirmed lineups will be skipped")
            print("   Install beautifulsoup4 and requests for real confirmed lineup data")
            return {}

        print("🌐 Fetching REAL confirmed lineups from multiple sources...")
        print("   📋 POLICY: Only real data will be used - no mock/sample data")

        all_confirmed = {}
        self.fetch_attempts = len(self.confirmed_sources)
        self.successful_sources = []

        for source in self.confirmed_sources:
            try:
                print(f"\n   📡 Attempting {source['name']}...")

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }

                response = requests.get(source['url'], headers=headers, timeout=20)
                response.raise_for_status()

                if response.status_code == 200:
                    lineups = source['parser'](response.text)
                    if lineups:
                        all_confirmed.update(lineups)
                        self.successful_sources.append(source['name'])
                        print(f"   ✅ {source['name']}: Found {len(lineups)} team lineups")

                        # Show sample of what we found
                        for team, players in list(lineups.items())[:2]:
                            player_list = [f"{name}({order})" for name, order in players.items()]
                            print(f"      📋 {team}: {', '.join(player_list[:3])}...")
                    else:
                        print(f"   ⚠️ {source['name']}: No lineups found in response")
                else:
                    print(f"   ❌ {source['name']}: HTTP {response.status_code}")

            except requests.exceptions.Timeout:
                print(f"   ⏰ {source['name']}: Request timeout (site may be slow)")
            except requests.exceptions.ConnectionError:
                print(f"   🔌 {source['name']}: Connection error (site may be down)")
            except requests.exceptions.HTTPError as e:
                print(f"   🚫 {source['name']}: HTTP error {e}")
            except Exception as e:
                print(f"   ❌ {source['name']}: Unexpected error - {e}")
                continue

        # Final results
        if all_confirmed:
            self.confirmed_data = all_confirmed
            total_players = sum(len(lineup) for lineup in all_confirmed.values())
            print(f"\n✅ REAL confirmed lineups successfully fetched!")
            print(f"   📊 Teams: {len(all_confirmed)}")
            print(f"   👥 Total players: {total_players}")
            print(f"   🌐 Successful sources: {', '.join(self.successful_sources)}")

            # Show breakdown by team
            print(f"\n📋 Confirmed lineup summary:")
            for team, players in sorted(all_confirmed.items()):
                print(f"   {team}: {len(players)} players confirmed")

        else:
            print(f"\n⚠️ No real confirmed lineups found from any source")
            print(f"   📊 Attempted: {self.fetch_attempts} sources")
            print(f"   ✅ Successful: {len(self.successful_sources)} sources")
            print(f"   💡 This is normal if:")
            print(f"      • Games haven't been announced yet")
            print(f"      • It's early in the day")
            print(f"      • Lineups are released closer to game time")
            print(f"   🚫 NO MOCK DATA will be used - optimizer will work without confirmed lineups")

        return all_confirmed

    def _parse_rotowire(self, html_content: str) -> Dict[str, Dict[str, int]]:
        """Parse RotoWire MLB daily lineups"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            lineups = {}

            # Updated selectors for current RotoWire layout
            game_sections = soup.find_all('div', class_='lineup') or soup.find_all('div', {'data-sport': 'MLB'})

            for section in game_sections:
                try:
                    # Find team info
                    team_elem = (section.find('span', class_='team-name') or
                                 section.find('div', class_='team') or
                                 section.find('h3', class_='team-header'))

                    if not team_elem:
                        continue

                    team_name = team_elem.get_text().strip()
                    team_abbrev = self._normalize_team_name(team_name)

                    if not team_abbrev:
                        continue

                    # Find lineup players
                    player_elements = (section.find_all('div', class_='player') or
                                       section.find_all('li', class_='lineup-player') or
                                       section.find_all('tr', class_='player-row'))

                    team_lineup = {}

                    for i, elem in enumerate(player_elements[:9], 1):  # Top 9 batters
                        player_name_elem = (elem.find('a', class_='player-link') or
                                            elem.find('span', class_='player-name') or
                                            elem.find('td', class_='name'))

                        if player_name_elem:
                            player_name = player_name_elem.get_text().strip()
                            if player_name and len(player_name) > 2:
                                team_lineup[player_name] = i

                    # Look for pitcher separately
                    pitcher_section = section.find('div', class_='pitcher') or section.find('span',
                                                                                            class_='starting-pitcher')
                    if pitcher_section:
                        pitcher_elem = pitcher_section.find('a') or pitcher_section.find('span')
                        if pitcher_elem:
                            pitcher_name = pitcher_elem.get_text().strip()
                            if pitcher_name and len(pitcher_name) > 2:
                                team_lineup[pitcher_name] = 0  # Pitcher position

                    if team_lineup:
                        lineups[team_abbrev] = team_lineup

                except Exception as e:
                    continue

            return lineups

        except Exception as e:
            print(f"      RotoWire parsing error: {e}")
            return {}

    def _parse_mlb_lineups(self, html_content: str) -> Dict[str, Dict[str, int]]:
        """Parse MLB.com starting lineups"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            lineups = {}

            # Look for MLB lineup data structures
            game_cards = soup.find_all('div', class_='starting-lineups-card') or soup.find_all('article',
                                                                                               class_='game-preview')

            for card in game_cards:
                try:
                    team_sections = card.find_all('div', class_='team-lineup') or card.find_all('div',
                                                                                                class_='lineup-team')

                    for team_section in team_sections:
                        # Extract team name
                        team_elem = (team_section.find('h3', class_='team-name') or
                                     team_section.find('span', class_='team-abbrev') or
                                     team_section.find('div', class_='team-header'))

                        if not team_elem:
                            continue

                        team_name = team_elem.get_text().strip()
                        team_abbrev = self._normalize_team_name(team_name)

                        if not team_abbrev:
                            continue

                        # Extract batting order
                        lineup_items = team_section.find_all('li', class_='batter') or team_section.find_all('div',
                                                                                                             class_='lineup-slot')

                        team_lineup = {}
                        for item in lineup_items:
                            # Look for batting order number
                            order_elem = item.find('span', class_='batting-order') or item.find('div', class_='order')
                            player_elem = (item.find('a', class_='player-name') or
                                           item.find('span', class_='name') or
                                           item.find('div', class_='player'))

                            if order_elem and player_elem:
                                try:
                                    batting_order = int(order_elem.get_text().strip())
                                    player_name = player_elem.get_text().strip()

                                    if player_name and 1 <= batting_order <= 9:
                                        team_lineup[player_name] = batting_order
                                except (ValueError, TypeError):
                                    continue

                        # Look for starting pitcher
                        pitcher_elem = team_section.find('div', class_='starting-pitcher')
                        if pitcher_elem:
                            pitcher_name_elem = pitcher_elem.find('a') or pitcher_elem.find('span', class_='name')
                            if pitcher_name_elem:
                                pitcher_name = pitcher_name_elem.get_text().strip()
                                if pitcher_name:
                                    team_lineup[pitcher_name] = 0

                        if team_lineup:
                            lineups[team_abbrev] = team_lineup

                except Exception as e:
                    continue

            return lineups

        except Exception as e:
            print(f"      MLB.com parsing error: {e}")
            return {}

    def _parse_baseball_press(self, html_content: str) -> Dict[str, Dict[str, int]]:
        """Parse Baseball Press lineups"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            lineups = {}

            # Look for Baseball Press lineup structures
            lineup_tables = soup.find_all('table', class_='lineup-table') or soup.find_all('div', class_='game-lineups')

            for table in lineup_tables:
                try:
                    # Each table should have two teams
                    team_headers = table.find_all('th', class_='team-header') or table.find_all('h4')

                    for header in team_headers:
                        team_name = header.get_text().strip()
                        team_abbrev = self._normalize_team_name(team_name)

                        if not team_abbrev:
                            continue

                        # Find the lineup rows for this team
                        team_section = header.find_parent('table') or header.find_next_sibling('div')
                        if not team_section:
                            continue

                        player_rows = team_section.find_all('tr')[1:10]  # Skip header, take next 9

                        team_lineup = {}
                        for i, row in enumerate(player_rows, 1):
                            player_cell = row.find('td', class_='player-name') or row.find('td')
                            if player_cell:
                                player_name = player_cell.get_text().strip()
                                if player_name and len(player_name) > 2:
                                    team_lineup[player_name] = i

                        if team_lineup:
                            lineups[team_abbrev] = team_lineup

                except Exception as e:
                    continue

            return lineups

        except Exception as e:
            print(f"      Baseball Press parsing error: {e}")
            return {}

    def _parse_daily_baseball_data(self, html_content: str) -> Dict[str, Dict[str, int]]:
        """Parse DailyBaseballData lineups"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            lineups = {}

            # This site has a simpler structure
            lineup_sections = soup.find_all('div', class_='lineup') or soup.find_all('table')

            for section in lineup_sections:
                try:
                    # Look for team identifier
                    team_elem = section.find('b') or section.find('strong') or section.find('th')

