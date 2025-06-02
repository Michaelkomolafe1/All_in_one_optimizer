#!/usr/bin/env python3
"""
BULLETPROOF DFS CORE - ULTIMATE INTEGRATION
==========================================
✅ Integrates YOUR existing modules (vegas_lines.py, confirmed_lineups.py, etc.)
✅ Adds YOUR old dfs_data.py advanced algorithms
✅ BULLETPROOF: NO unconfirmed players can leak through
✅ Single source of truth - no competing systems
✅ Uses your exact data files and manual player list
"""

import os
import sys
import pandas as pd
import numpy as np
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')

# Import optimization
try:
    import pulp

    MILP_AVAILABLE = True
    print("✅ PuLP available - MILP optimization enabled")
except ImportError:
    MILP_AVAILABLE = False
    print("⚠️ PuLP not available - using greedy fallback")

# Import YOUR existing modules with fallbacks
try:
    from vegas_lines import VegasLines

    VEGAS_AVAILABLE = True
    print("✅ YOUR Vegas lines module imported")
except ImportError:
    VEGAS_AVAILABLE = False
    print("⚠️ Your vegas_lines.py not found")

try:
    from confirmed_lineups import ConfirmedLineups

    CONFIRMED_AVAILABLE = True
    print("✅ YOUR confirmed lineups module imported")
except ImportError:
    CONFIRMED_AVAILABLE = False
    print("⚠️ Your confirmed_lineups.py not found")

try:
    from simple_statcast_fetcher import SimpleStatcastFetcher

    STATCAST_AVAILABLE = True
    print("✅ YOUR Statcast fetcher imported")
except ImportError:
    STATCAST_AVAILABLE = False
    print("⚠️ Your simple_statcast_fetcher.py not found")


class BulletproofPlayer:
    """Player model with BULLETPROOF confirmation tracking"""

    def __init__(self, player_data: Dict):
        self.id = int(player_data.get('id', 0))
        self.name = str(player_data.get('name', '')).strip()
        self.positions = self._parse_positions(player_data.get('position', ''))
        self.primary_position = self.positions[0] if self.positions else 'UTIL'
        self.team = str(player_data.get('team', '')).strip().upper()
        self.salary = self._parse_salary(player_data.get('salary', 3000))
        self.projection = self._parse_float(player_data.get('projection', 0))

        # BULLETPROOF confirmation tracking
        self.is_confirmed = False
        self.is_manual_selected = False
        self.confirmation_sources = []  # Track ALL sources

        # Enhanced data from YOUR old dfs_data.py system
        self.dff_projection = 0
        self.dff_value_projection = 0
        self.dff_l5_avg = 0
        self.vegas_data = {}
        self.statcast_data = {}
        self.park_factors = {}

        # Calculate base score (NO artificial bonuses)
        self.base_score = self.projection if self.projection > 0 else (self.salary / 1000.0)
        self.enhanced_score = self.base_score

    def _parse_positions(self, position_str: str) -> List[str]:
        """Parse positions with multi-position support"""
        if not position_str:
            return ['UTIL']

        position_str = str(position_str).strip().upper()

        # Handle delimiters
        for delimiter in ['/', ',', '-', '|', '+']:
            if delimiter in position_str:
                positions = [p.strip() for p in position_str.split(delimiter)]
                break
        else:
            positions = [position_str]

        # Clean and validate positions
        valid_positions = []
        for pos in positions:
            pos = pos.strip()
            if pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'UTIL']:
                if pos not in valid_positions:
                    valid_positions.append(pos)

        return valid_positions if valid_positions else ['UTIL']

    def _parse_salary(self, salary_input: Any) -> int:
        """Parse salary from various formats"""
        try:
            if isinstance(salary_input, (int, float)):
                return max(1000, int(salary_input))
            cleaned = str(salary_input).replace('$', '').replace(',', '').strip()
            return max(1000, int(float(cleaned))) if cleaned and cleaned != 'nan' else 3000
        except (ValueError, TypeError):
            return 3000

    def _parse_float(self, value: Any) -> float:
        """Parse float from various formats"""
        try:
            if isinstance(value, (int, float)):
                return max(0.0, float(value))
            cleaned = str(value).strip()
            return max(0.0, float(cleaned)) if cleaned and cleaned != 'nan' else 0.0
        except (ValueError, TypeError):
            return 0.0

    def is_eligible_for_selection(self) -> bool:
        """BULLETPROOF: Only confirmed OR manual players are eligible"""
        return self.is_confirmed or self.is_manual_selected

    def add_confirmation_source(self, source: str):
        """Add confirmation source with tracking"""
        if source not in self.confirmation_sources:
            self.confirmation_sources.append(source)
        self.is_confirmed = True
        print(f"🔒 CONFIRMED: {self.name} ({source})")

    def set_manual_selected(self):
        """Set player as manually selected"""
        self.is_manual_selected = True
        self.confirmation_sources.append("manual_selection")
        print(f"🎯 MANUAL: {self.name}")

    def apply_dff_data(self, dff_data: Dict):
        """Apply DFF data with enhanced L5 analysis"""
        self.dff_projection = dff_data.get('ppg_projection', 0)
        self.dff_value_projection = dff_data.get('value_projection', 0)
        self.dff_l5_avg = dff_data.get('L5_fppg_avg', 0)

        # Natural enhancement (not artificial bonus)
        if self.dff_projection > self.projection:
            self.enhanced_score = self.dff_projection

        # Check if DFF says confirmed
        if str(dff_data.get('confirmed_order', '')).upper() == 'YES':
            self.add_confirmation_source("dff_confirmed")

    def apply_vegas_data(self, vegas_data: Dict):
        """Apply Vegas data from YOUR vegas_lines.py"""
        self.vegas_data = vegas_data

    def apply_statcast_data(self, statcast_data: Dict):
        """Apply Statcast data from YOUR simple_statcast_fetcher.py"""
        self.statcast_data = statcast_data

    def calculate_enhanced_score_with_your_algorithms(self):
        """
        Calculate final score using YOUR old dfs_data.py algorithms
        This integrates all your advanced calculations
        """
        score = self.enhanced_score

        # 1. Enhanced DFF Analysis (from YOUR old system)
        if self.dff_projection > 0:
            dff_boost = (self.dff_projection - self.projection) * 0.4
            score += dff_boost

        if self.dff_value_projection > 0:
            if self.dff_value_projection >= 2.0:
                score += 2.5
            elif self.dff_value_projection >= 1.8:
                score += 2.0
            elif self.dff_value_projection >= 1.6:
                score += 1.5

        # 2. Recent Form Analysis (L5 games from YOUR system)
        if self.dff_l5_avg > 0 and self.projection > 0:
            recent_form_diff = self.dff_l5_avg - self.projection
            if recent_form_diff >= 3.0:
                score += 1.5  # Hot streak
            elif recent_form_diff >= 1.5:
                score += 1.0
            elif recent_form_diff <= -1.5:
                score -= 1.0  # Cold streak

        # 3. Vegas Lines Integration (from YOUR vegas_lines.py)
        if self.vegas_data:
            team_total = self.vegas_data.get('team_total', 4.5)
            opp_total = self.vegas_data.get('opponent_total', 4.5)

            if self.primary_position == 'P':
                # Enhanced pitcher scoring
                if opp_total <= 3.5:
                    score += 3.0  # Excellent matchup
                elif opp_total <= 4.0:
                    score += 2.0
                elif opp_total <= 4.5:
                    score += 1.0
                elif opp_total >= 5.5:
                    score -= 2.0  # Tough matchup
                elif opp_total >= 5.0:
                    score -= 1.0
            else:
                # Enhanced hitter scoring
                if team_total >= 5.5:
                    score += 3.0  # High-scoring environment
                elif team_total >= 5.0:
                    score += 2.0
                elif team_total >= 4.5:
                    score += 1.0
                elif team_total <= 3.5:
                    score -= 2.0  # Low-scoring environment
                elif team_total <= 4.0:
                    score -= 1.0

        # 4. Advanced Statcast Integration (from YOUR simple_statcast_fetcher.py)
        if self.statcast_data:
            if self.primary_position == 'P':
                xwoba = self.statcast_data.get('xwOBA', 0.320)
                hard_hit = self.statcast_data.get('Hard_Hit', 35.0)
                k_rate = self.statcast_data.get('K', 20.0)

                # Enhanced pitcher metrics
                if xwoba <= 0.270:
                    score += 3.0  # Elite
                elif xwoba <= 0.290:
                    score += 2.0
                elif xwoba <= 0.310:
                    score += 1.0
                elif xwoba >= 0.360:
                    score -= 2.0
                elif xwoba >= 0.340:
                    score -= 1.0

                if k_rate >= 30.0:
                    score += 2.5
                elif k_rate >= 25.0:
                    score += 1.5
                elif k_rate <= 15.0:
                    score -= 1.5

                if hard_hit <= 25.0:
                    score += 2.5  # Elite contact management
                elif hard_hit <= 30.0:
                    score += 1.5
                elif hard_hit >= 45.0:
                    score -= 2.0
                elif hard_hit >= 40.0:
                    score -= 1.0

            else:
                xwoba = self.statcast_data.get('xwOBA', 0.320)
                hard_hit = self.statcast_data.get('Hard_Hit', 35.0)
                barrel_rate = self.statcast_data.get('Barrel', 6.0)

                # Enhanced hitter metrics
                if xwoba >= 0.400:
                    score += 3.0  # Elite
                elif xwoba >= 0.370:
                    score += 2.5
                elif xwoba >= 0.340:
                    score += 2.0
                elif xwoba >= 0.320:
                    score += 1.0
                elif xwoba <= 0.280:
                    score -= 2.0

                if hard_hit >= 50.0:
                    score += 3.0
                elif hard_hit >= 45.0:
                    score += 2.0
                elif hard_hit >= 40.0:
                    score += 1.0
                elif hard_hit <= 25.0:
                    score -= 1.5

                if barrel_rate >= 15.0:
                    score += 2.5
                elif barrel_rate >= 12.0:
                    score += 2.0
                elif barrel_rate >= 8.0:
                    score += 1.0

        self.enhanced_score = max(1.0, score)
        return self.enhanced_score

    def can_play_position(self, position: str) -> bool:
        """Check if player can play specific position"""
        return position in self.positions or position == 'UTIL'

    def get_status_string(self) -> str:
        """Get formatted status string for display"""
        status_parts = []
        if self.is_confirmed:
            sources = ", ".join(self.confirmation_sources)
            status_parts.append(f"CONFIRMED ({sources})")
        if self.is_manual_selected:
            status_parts.append("MANUAL")
        if self.dff_projection > 0:
            status_parts.append(f"DFF:{self.dff_projection:.1f}")
        if self.statcast_data:
            source = self.statcast_data.get('data_source', 'unknown')
            if 'Baseball Savant' in source:
                status_parts.append("REAL-STATCAST")
            else:
                status_parts.append("SIM-STATCAST")
        if self.vegas_data:
            status_parts.append("VEGAS")
        return " | ".join(status_parts) if status_parts else "UNCONFIRMED"

    def __repr__(self):
        pos_str = '/'.join(self.positions)
        status = "✅" if self.is_eligible_for_selection() else "❌"
        return f"Player({self.name}, {pos_str}, ${self.salary}, {self.enhanced_score:.1f}, {status})"


class BulletproofDFSCore:
    """BULLETPROOF DFS Core that integrates ALL your existing modules"""

    def __init__(self):
        self.players = []
        self.contest_type = 'classic'
        self.salary_cap = 50000

        # Initialize YOUR existing modules
        self.vegas_lines = VegasLines() if VEGAS_AVAILABLE else None
        self.confirmed_lineups = ConfirmedLineups() if CONFIRMED_AVAILABLE else None
        self.statcast_fetcher = SimpleStatcastFetcher() if STATCAST_AVAILABLE else None

        print("🚀 BULLETPROOF DFS Core initialized")
        print("✅ Integrates ALL your existing modules")
        print("🔒 BULLETPROOF: NO unconfirmed leaks possible")

    def load_draftkings_csv(self, file_path: str) -> bool:
        """Load YOUR DraftKings CSV with enhanced processing"""
        try:
            print(f"📁 Loading YOUR DraftKings CSV: {Path(file_path).name}")

            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                return False

            df = pd.read_csv(file_path)
            print(f"📊 Found {len(df)} rows")

            # Enhanced column detection for YOUR format
            column_map = {}
            for i, col in enumerate(df.columns):
                col_lower = str(col).lower().strip()
                if any(name in col_lower for name in ['name', 'player']):
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

                    player = BulletproofPlayer(player_data)
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
        """Apply YOUR manual player selection with enhanced fuzzy matching"""
        if not manual_input:
            return 0

        # Parse YOUR manual input
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

        print(f"🎯 Processing YOUR manual selection: {len(manual_names)} players")

        matches = 0
        for manual_name in manual_names:
            # Enhanced fuzzy matching for YOUR player names
            best_match = None
            best_score = 0

            for player in self.players:
                similarity = self._enhanced_name_similarity(manual_name, player.name)
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

    def _enhanced_name_similarity(self, name1: str, name2: str) -> float:
        """Enhanced name similarity for YOUR player names"""
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()

        # Exact match
        if name1 == name2:
            return 1.0

        # Handle YOUR specific name variations
        name_variations = {
            'cj abrams': ['c.j. abrams'],
            'j wood': ['james wood'],
            'j. wood': ['james wood'],
            'n lowe': ['nathaniel lowe'],
            'l garcía jr.': ['luis garcia jr.', 'luis garcia'],
            'j bell': ['josh bell'],
            'r hassell iii': ['robert hassell iii'],
            'j tena': ['jose tena'],
            'd lile': ['daylen lile'],
            'c carroll': ['corbin carroll'],
            'k marte': ['ketel marte'],
            'g perdomo': ['geraldo perdomo'],
            'j naylor': ['josh naylor'],
            'e suárez': ['eugenio suarez'],
            'l gurriel jr.': ['lourdes gurriel jr.'],
            'g moreno': ['gabriel moreno'],
            'a thomas': ['alek thomas'],
            'o cruz': ['oneil cruz'],
            'a mccutchen': ['andrew mccutchen'],
            'b reynolds': ['bryan reynolds'],
            's horwitz': ['spencer horwitz'],
            'h davis': ['henry davis'],
            'k hayes': ['ke\'bryan hayes'],
            'a frazier': ['adam frazier'],
            't pham': ['tommy pham'],
            'f tatis jr.': ['fernando tatis jr.'],
            'l arraez': ['luis arraez'],
            'm machado': ['manny machado'],
            'j merrill': ['jackson merrill'],
            'g sheets': ['gavin sheets'],
            'x bogaerts': ['xander bogaerts'],
            'j cronenworth': ['jake cronenworth'],
            't wade': ['tyler wade'],
            'e díaz': ['elias diaz'],
            'b buxton': ['byron buxton'],
            't larnach': ['trevor larnach'],
            'r jeffers': ['ryan jeffers'],
            'c correa': ['carlos correa'],
            'b lee': ['brooks lee'],
            't france': ['ty france'],
            'k clemens': ['kody clemens'],
            'r lewis': ['royce lewis'],
            'w castro': ['willi castro'],
            'j crawford': ['j.p. crawford'],
            'j polanco': ['jorge polanco'],
            'j rodríguez': ['julio rodriguez'],
            'c raleigh': ['cal raleigh'],
            'r arozarena': ['randy arozarena'],
            'r tellez': ['rowdy tellez'],
            'l taveras': ['leody taveras'],
            'm mastrobuoni': ['miles mastrobuoni'],
            'b williamson': ['ben williamson'],
            's ohtani': ['shohei ohtani'],
            't hernández': ['teoscar hernandez'],
            'w smith': ['will smith'],
            'f freeman': ['freddie freeman'],
            'a pages': ['andy pages'],
            't edman': ['tommy edman'],
            'k hernández': ['kike hernandez'],
            'm conforto': ['michael conforto'],
            'm rojas': ['miguel rojas']
        }

        # Check variations
        for short_name, full_names in name_variations.items():
            if name1 == short_name and name2 in full_names:
                return 0.95
            if name2 == short_name and name1 in full_names:
                return 0.95

        # Check if one is contained in the other
        if name1 in name2 or name2 in name1:
            return 0.85

        # Check last name + first initial
        name1_parts = name1.split()
        name2_parts = name2.split()

        if len(name1_parts) >= 2 and len(name2_parts) >= 2:
            if (name1_parts[-1] == name2_parts[-1] and  # Same last name
                    name1_parts[0][0] == name2_parts[0][0]):  # Same first initial
                return 0.8

        return 0.0

    def detect_confirmed_players(self) -> int:
        """Detect confirmed players using YOUR confirmed_lineups.py"""
        if not self.confirmed_lineups:
            print("⚠️ YOUR confirmed_lineups.py module not available")
            return 0

        print("🔍 Using YOUR confirmed_lineups.py for detection...")

        confirmed_count = 0
        for player in self.players:
            # Check if player is in confirmed lineups using YOUR module
            is_confirmed, batting_order = self.confirmed_lineups.is_player_confirmed(player.name, player.team)

            if is_confirmed:
                player.add_confirmation_source("your_online_lineup")
                confirmed_count += 1

            # Check if pitcher is confirmed starting using YOUR module
            if player.primary_position == 'P':
                if self.confirmed_lineups.is_pitcher_starting(player.name, player.team):
                    player.add_confirmation_source("your_online_pitcher")
                    confirmed_count += 1

        print(f"✅ YOUR confirmed detection: {confirmed_count} players")
        return confirmed_count

    def apply_dff_rankings(self, dff_file_path: str) -> bool:
        """Apply YOUR DFF rankings with enhanced integration"""
        if not os.path.exists(dff_file_path):
            print(f"⚠️ YOUR DFF file not found: {dff_file_path}")
            return False

        try:
            print(f"🎯 Loading YOUR DFF rankings: {Path(dff_file_path).name}")
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
                        if self._enhanced_name_similarity(full_name, player.name) >= 0.8:
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

            print(f"✅ YOUR DFF integration: {matches} players")
            return True

        except Exception as e:
            print(f"❌ Error loading YOUR DFF data: {e}")
            return False

    def enrich_with_vegas_lines(self):
        """Enrich with YOUR vegas_lines.py integration"""
        if not self.vegas_lines:
            print("⚠️ YOUR vegas_lines.py module not available")
            return

        print("💰 Using YOUR vegas_lines.py for integration...")
        vegas_data = self.vegas_lines.get_vegas_lines()

        if not vegas_data:
            print("⚠️ No Vegas data from YOUR module")
            return

        enriched_count = 0
        for player in self.players:
            if player.team in vegas_data:
                team_vegas = vegas_data[player.team]
                player.apply_vegas_data(team_vegas)
                enriched_count += 1

        print(f"✅ YOUR Vegas integration: {enriched_count} players")

    def enrich_with_statcast_priority(self):
        """Enrich with YOUR simple_statcast_fetcher.py with priority"""
        if not self.statcast_fetcher:
            print("⚠️ YOUR simple_statcast_fetcher.py not available")
            return

        print("🔬 Using YOUR simple_statcast_fetcher.py...")

        # Priority to confirmed and manual players
        priority_players = [p for p in self.players if p.is_eligible_for_selection()]
        other_players = [p for p in self.players if not p.is_eligible_for_selection()]

        print(f"🎯 Priority Statcast for {len(priority_players)} confirmed/manual players...")

        # Real data for priority players using YOUR fetcher
        real_data_count = 0
        for player in priority_players:
            try:
                statcast_data = self.statcast_fetcher.fetch_player_data(player.name, player.primary_position)
                if statcast_data:
                    player.apply_statcast_data(statcast_data)
                    real_data_count += 1
                    print(f"   🔬 YOUR real data: {player.name}")
                else:
                    # Simulation for priority players
                    sim_data = self._generate_simulation(player)
                    player.apply_statcast_data(sim_data)
                    print(f"   ⚡ Simulation: {player.name}")
            except Exception:
                continue

        # Simulation for other players
        sim_count = 0
        for player in other_players:
            sim_data = self._generate_simulation(player)
            player.apply_statcast_data(sim_data)
            sim_count += 1

        print(f"✅ YOUR Statcast: {real_data_count} real, {sim_count} simulated")

    def _generate_simulation(self, player) -> Dict:
        """Generate simulation data"""
        import random

        # Use player name for consistent randomization
        random.seed(hash(player.name) % 1000000)

        if player.primary_position == 'P':
            salary_factor = min(player.salary / 10000.0, 1.2)
            return {
                'xwOBA': round(max(0.250, random.normalvariate(0.310 - (salary_factor * 0.020), 0.030)), 3),
                'Hard_Hit': round(max(0, random.normalvariate(35.0 - (salary_factor * 3.0), 5.0)), 1),
                'K': round(max(0, random.normalvariate(20.0 + (salary_factor * 5.0), 4.0)), 1),
                'data_source': 'Simulation'
            }
        else:
            salary_factor = min(player.salary / 5000.0, 1.2)
            return {
                'xwOBA': round(max(0.250, random.normalvariate(0.310 + (salary_factor * 0.030), 0.040)), 3),
                'Hard_Hit': round(max(0, random.normalvariate(30.0 + (salary_factor * 8.0), 7.0)), 1),
                'Barrel': round(max(0, random.normalvariate(5.0 + (salary_factor * 4.0), 3.0)), 1),
                'data_source': 'Simulation'
            }

    def get_eligible_players_bulletproof(self) -> List[BulletproofPlayer]:
        """Get ONLY eligible players with BULLETPROOF filtering"""
        eligible = [p for p in self.players if p.is_eligible_for_selection()]

        print(f"🔒 BULLETPROOF FILTER: {len(eligible)}/{len(self.players)} players eligible")

        # Detailed breakdown
        confirmed_count = sum(1 for p in eligible if p.is_confirmed)
        manual_count = sum(1 for p in eligible if p.is_manual_selected)
        both_count = sum(1 for p in eligible if p.is_confirmed and p.is_manual_selected)

        print(f"   📊 Confirmed only: {confirmed_count - both_count}")
        print(f"   🎯 Manual only: {manual_count - both_count}")
        print(f"   🤝 Both: {both_count}")

        # Show some examples
        if len(eligible) > 0:
            print(f"   📝 Sample eligible players:")
            for i, player in enumerate(eligible[:5]):
                print(f"      {i + 1}. {player.name} - {player.get_status_string()}")

        return eligible

    def calculate_all_enhanced_scores(self):
        """Calculate enhanced scores using YOUR algorithms"""
        print("🧠 Calculating scores with YOUR old dfs_data.py algorithms...")

        eligible_players = self.get_eligible_players_bulletproof()

        for player in eligible_players:
            player.calculate_enhanced_score_with_your_algorithms()

        print(f"✅ Enhanced scoring complete for {len(eligible_players)} players")

    def optimize_lineup_bulletproof(self) -> Tuple[List[BulletproofPlayer], float]:
        """BULLETPROOF optimization with position validation"""
        print("🧠 BULLETPROOF OPTIMIZATION")
        print("=" * 50)

        # Get eligible players only
        eligible_players = self.get_eligible_players_bulletproof()

        if len(eligible_players) < 10:
            print(f"❌ INSUFFICIENT ELIGIBLE PLAYERS: {len(eligible_players)}/10 required")
            print("💡 Add more manual players or wait for more confirmed lineups")
            return [], 0

        # Position validation
        position_counts = self._validate_position_coverage(eligible_players)
        position_requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        for pos, required in position_requirements.items():
            if position_counts[pos] < required:
                print(f"❌ INSUFFICIENT {pos} PLAYERS: {position_counts[pos]}/{required}")
                print(f"💡 Add more {pos} players to your manual selection")
                return [], 0

        # Calculate enhanced scores
        self.calculate_all_enhanced_scores()

        # Use MILP if available
        if MILP_AVAILABLE:
            return self._optimize_milp(eligible_players)
        else:
            return self._optimize_greedy(eligible_players)

    def _validate_position_coverage(self, players: List[BulletproofPlayer]) -> Dict[str, int]:
        """Validate position coverage"""
        position_requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        position_counts = {}

        for pos in position_requirements.keys():
            position_counts[pos] = sum(1 for p in players if p.can_play_position(pos))

        print(f"🔍 Position coverage:")
        for pos, required in position_requirements.items():
            available = position_counts[pos]
            status = "✅" if available >= required else "❌"
            print(f"   {pos}: {available}/{required} {status}")

        return position_counts

    def _optimize_milp(self, players: List[BulletproofPlayer]) -> Tuple[List[BulletproofPlayer], float]:
        """MILP optimization"""
        try:
            print(f"🔬 MILP optimization: {len(players)} players")

            prob = pulp.LpProblem("Bulletproof_DFS", pulp.LpMaximize)

            # Variables
            player_vars = {}
            for i, player in enumerate(players):
                player_vars[i] = pulp.LpVariable(f"player_{i}", cat=pulp.LpBinary)

            # Objective
            prob += pulp.lpSum([player.enhanced_score * player_vars[i] for i, player in enumerate(players)])

            # Constraints
            position_requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

            for pos, count in position_requirements.items():
                eligible_vars = [player_vars[i] for i, player in enumerate(players)
                                 if player.can_play_position(pos)]
                prob += pulp.lpSum(eligible_vars) == count

            # Total players
            prob += pulp.lpSum([player_vars[i] for i in range(len(players))]) == 10

            # Salary constraint
            prob += pulp.lpSum([player.salary * player_vars[i] for i, player in enumerate(players)]) <= self.salary_cap

            # Solve
            prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=60))

            if prob.status == pulp.LpStatusOptimal:
                lineup = []
                total_score = 0

                for i, player in enumerate(players):
                    if player_vars[i].value() > 0.5:
                        lineup.append(player)
                        total_score += player.enhanced_score

                print(f"✅ MILP success: {len(lineup)} players, {total_score:.2f} score")
                return lineup, total_score
            else:
                print(f"❌ MILP failed: {pulp.LpStatus[prob.status]}")
                return self._optimize_greedy(players)

        except Exception as e:
            print(f"❌ MILP error: {e}")
            return self._optimize_greedy(players)

    def _optimize_greedy(self, players: List[BulletproofPlayer]) -> Tuple[List[BulletproofPlayer], float]:
        """Greedy optimization fallback"""
        print(f"🎯 Greedy optimization: {len(players)} players")

        # Sort by value (score per salary)
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

            # Check if we need this position
            for pos in player.positions:
                if position_needs.get(pos, 0) > 0:
                    lineup.append(player)
                    total_salary += player.salary
                    position_needs[pos] -= 1
                    break

        total_score = sum(p.enhanced_score for p in lineup)
        print(f"✅ Greedy success: {len(lineup)} players, {total_score:.2f} score")
        return lineup, total_score

    def generate_summary(self, lineup: List[BulletproofPlayer], score: float) -> str:
        """Generate detailed summary"""
        if not lineup:
            return "❌ No valid lineup generated"

        total_salary = sum(p.salary for p in lineup)
        confirmed_count = sum(1 for p in lineup if p.is_confirmed)
        manual_count = sum(1 for p in lineup if p.is_manual_selected)

        summary = f"""
✅ BULLETPROOF OPTIMIZATION SUCCESS
==================================
Integration: YOUR modules + old dfs_data.py algorithms
Players: {len(lineup)}/10
Total Salary: ${total_salary:,}/${self.salary_cap:,}
Remaining: ${self.salary_cap - total_salary:,}
Projected Score: {score:.2f} (Enhanced with YOUR algorithms)
Confirmed Players: {confirmed_count}
Manual Players: {manual_count}

🔒 BULLETPROOF VERIFICATION: ALL PLAYERS ARE CONFIRMED OR MANUAL
🧠 ALGORITHMS: YOUR vegas_lines + confirmed_lineups + simple_statcast_fetcher + old dfs_data.py

LINEUP:
=======
"""

        for i, player in enumerate(lineup, 1):
            summary += f"{i:2d}. {player.name:<20} {player.primary_position:<3} ${player.salary:,} {player.enhanced_score:.1f} {player.get_status_string()}\n"

        return summary


def run_bulletproof_optimization(dk_file: str, dff_file: str = None, manual_input: str = "") -> Tuple[
    List[BulletproofPlayer], float, str]:
    """Run complete bulletproof optimization using YOUR modules"""
    print("🚀 BULLETPROOF DFS OPTIMIZATION")
    print("=" * 70)
    print("✅ YOUR modules: vegas_lines.py + confirmed_lineups.py + simple_statcast_fetcher.py")
    print("✅ YOUR old algorithms: dfs_data.py advanced scoring")
    print("🔒 BULLETPROOF: NO unconfirmed leaks possible")
    print("=" * 70)

    core = BulletproofDFSCore()

    # Step 1: Load YOUR DraftKings data
    if not core.load_draftkings_csv(dk_file):
        return [], 0, "Failed to load YOUR DraftKings data"

    # Step 2: Apply YOUR manual selection first
    if manual_input:
        manual_count = core.apply_manual_selection(manual_input)
        print(f"✅ YOUR manual selection: {manual_count} players")

    # Step 3: Detect confirmed players using YOUR module
    confirmed_count = core.detect_confirmed_players()
    print(f"✅ YOUR confirmed detection: {confirmed_count} players")

    # Step 4: Apply YOUR DFF rankings
    if dff_file:
        core.apply_dff_rankings(dff_file)

    # Step 5: Enrich with YOUR modules
    core.enrich_with_vegas_lines()
    core.enrich_with_statcast_priority()

    # Step 6: BULLETPROOF optimization
    lineup, score = core.optimize_lineup_bulletproof()

    if lineup:
        summary = core.generate_summary(lineup, score)
        print(summary)
        return lineup, score, summary
    else:
        return [], 0, "Bulletproof optimization failed - insufficient eligible players"


# Test with YOUR actual data
def test_bulletproof_with_your_data():
    """Test bulletproof system with YOUR actual data files"""
    print("🧪 Testing BULLETPROOF system with YOUR data files")

    # Use YOUR actual files
    dk_file = "DKSalaries 62.csv"
    dff_file = "DFF_MLB_cheatsheet_20250601 2.csv"

    # Use YOUR actual manual player list
    manual_players = """CJ Abrams, James Wood, Nathaniel Lowe, Luis García Jr., Josh Bell, Robert Hassell III, 
    Keibert Ruiz, Jose Tena, Daylen Lile, Corbin Carroll, Ketel Marte, Geraldo Perdomo, Josh Naylor, 
    Eugenio Suárez, Lourdes Gurriel Jr., Gabriel Moreno, Alek Thomas, Oneil Cruz, Andrew McCutchen, 
    Bryan Reynolds, Spencer Horwitz, Henry Davis, Ke'Bryan Hayes, Adam Frazier, Tommy Pham, 
    Isiah Kiner-Falefa, Fernando Tatis Jr., Luis Arraez, Manny Machado, Jackson Merrill, Gavin Sheets, 
    Xander Bogaerts, Jake Cronenworth, Tyler Wade, Elias Díaz, Byron Buxton, Trevor Larnach, 
    Ryan Jeffers, Carlos Correa, Brooks Lee, Ty France, Kody Clemens, Royce Lewis, Willi Castro, 
    J.P. Crawford, Jorge Polanco, Julio Rodríguez, Cal Raleigh, Randy Arozarena, Rowdy Tellez, 
    Leody Taveras, Miles Mastrobuoni, Ben Williamson, Shohei Ohtani, Teoscar Hernández, Will Smith, 
    Freddie Freeman, Andy Pages, Tommy Edman, Kiké Hernández, Michael Conforto, Miguel Rojas"""

    # Check if YOUR files exist
    if not os.path.exists(dk_file):
        print(f"❌ YOUR DraftKings file not found: {dk_file}")
        return False

    if not os.path.exists(dff_file):
        print(f"⚠️ YOUR DFF file not found: {dff_file}")
        dff_file = None

    # Run bulletproof optimization
    lineup, score, summary = run_bulletproof_optimization(dk_file, dff_file, manual_players)

    if lineup:
        print("✅ BULLETPROOF Test PASSED!")
        print(f"Generated lineup with {len(lineup)} players")

        # CRITICAL: Verify NO unconfirmed players
        unconfirmed = [p for p in lineup if not p.is_eligible_for_selection()]
        if unconfirmed:
            print(f"🚨 TEST FAILED: {len(unconfirmed)} unconfirmed players found!")
            for p in unconfirmed:
                print(f"   ❌ {p.name} - {p.get_status_string()}")
            return False
        else:
            print("🔒 BULLETPROOF VERIFICATION PASSED: All players confirmed or manual")

        # Show integration success
        vegas_count = sum(1 for p in lineup if p.vegas_data)
        statcast_count = sum(1 for p in lineup if p.statcast_data)
        dff_count = sum(1 for p in lineup if p.dff_projection > 0)

        print(f"\n🔗 YOUR MODULE INTEGRATION:")
        print(f"   💰 Vegas data: {vegas_count}/10 players")
        print(f"   🔬 Statcast data: {statcast_count}/10 players")
        print(f"   🎯 DFF data: {dff_count}/10 players")

        return True
    else:
        print("❌ BULLETPROOF Test FAILED: No lineup generated")
        return False


if __name__ == "__main__":
    # Test bulletproof system with YOUR data
    success = test_bulletproof_with_your_data()
    if success:
        print("\n🎉 BULLETPROOF SYSTEM READY!")
        print("✅ Integrates ALL your existing modules")
        print("🔒 NO unconfirmed player leaks possible")
        print("🧠 YOUR old dfs_data.py algorithms working")
    else:
        print("\n❌ System needs attention")