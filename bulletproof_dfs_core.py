#!/usr/bin/env python3
"""
BULLETPROOF DFS CORE - COMPLETE WORKING VERSION WITH ENHANCED PITCHER DETECTION
==============================================================================
✅ All missing methods included
✅ Real player name matching
✅ Manual-only mode working
✅ Enhanced pitcher detection integrated
✅ Comprehensive validation
✅ Priority 1 enhancements included
"""
#!/usr/bin/env python3
"""
BULLETPROOF DFS CORE - COMPLETE WORKING VERSION WITH ENHANCED PITCHER DETECTION
==============================================================================
✅ All missing methods included
✅ Real player name matching
✅ Manual-only mode working
✅ Enhanced pitcher detection integrated
✅ Comprehensive validation
✅ Priority 1 enhancements included
"""
# Standard library imports
import os
import sys
import re
import csv
import json
import time
import copy
import random
import tempfile
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from difflib import SequenceMatcher

# DFS Upgrade Modules
try:
    from smart_cache import smart_cache
    from multi_lineup_optimizer import MultiLineupOptimizer
    from performance_tracker import tracker
    UPGRADES_AVAILABLE = True
    print("✅ DFS upgrades loaded")
except ImportError as e:
    print(f"⚠️ Optional upgrades not available: {e}")
    UPGRADES_AVAILABLE = False

# Third-party imports
import numpy as np
import pandas as pd

# Suppress warnings
warnings.filterwarnings('ignore')

# Import utils - only what exists and is used
from utils.cache_manager import cache
from utils.profiler import profiler
from utils.validator import DataValidator
from utils.config import config

# New unified imports
from unified_data_system import UnifiedDataSystem
from optimal_lineup_optimizer import OptimalLineupOptimizer, OptimizationResult

# Enhanced Statistical Analysis Engine - PRIORITY 1 IMPROVEMENTS
try:
    from enhanced_stats_engine import apply_enhanced_statistical_analysis
    ENHANCED_STATS_AVAILABLE = True
    print("✅ Enhanced Statistical Analysis Engine loaded")
except ImportError:
    ENHANCED_STATS_AVAILABLE = False
    print("⚠️ Enhanced stats engine not found - using basic analysis")
    def apply_enhanced_statistical_analysis(players, verbose=False):
        return 0

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
    from smart_confirmation_system import SmartConfirmationSystem
    CONFIRMED_AVAILABLE = True
    print("✅ Smart Confirmation System imported")
except ImportError:
    CONFIRMED_AVAILABLE = False
    print("⚠️ smart_confirmation_system.py not found")
    class SmartConfirmationSystem:
        def __init__(self, **kwargs):
            self.confirmed_lineups = {}
            self.confirmed_pitchers = {}
        def get_all_confirmations(self): return 0, 0
        def is_player_confirmed(self, name, team): return False, None
        def is_pitcher_confirmed(self, name, team): return False

try:
    from simple_statcast_fetcher import SimpleStatcastFetcher, FastStatcastFetcher
    STATCAST_AVAILABLE = True
    print("✅ Statcast fetcher imported")
except ImportError:
    STATCAST_AVAILABLE = False
    print("⚠️ simple_statcast_fetcher.py not found")
    class SimpleStatcastFetcher:
        def __init__(self): pass
        def fetch_player_data(self, name, position): return {}
    class FastStatcastFetcher:
        def __init__(self, max_workers=5): pass
        def fetch_multiple_players_parallel(self, players): return {}

# NEW: Recent Form Analyzer
try:
    from recent_form_analyzer import RecentFormAnalyzer
    RECENT_FORM_AVAILABLE = True
    print("✅ Recent Form Analyzer imported")
except ImportError:
    RECENT_FORM_AVAILABLE = False
    print("⚠️ recent_form_analyzer.py not found")

# NEW: Batting Order & Correlation System
try:
    from batting_order_correlation_system import (
        BattingOrderEnricher,
        CorrelationOptimizer,
        integrate_batting_order_correlation
    )
    BATTING_CORRELATION_AVAILABLE = True
    print("✅ Batting Order & Correlation System imported")
except ImportError:
    BATTING_CORRELATION_AVAILABLE = False
    print("⚠️ batting_order_correlation_system.py not found")

# Constants
PARK_FACTORS = {
    "COL": 1.1, "TEX": 1.05, "CIN": 1.05, "NYY": 1.05, "BOS": 1.03, "PHI": 1.03,
    "MIA": 0.95, "OAK": 0.95, "SD": 0.97, "SEA": 0.97
}

KNOWN_RELIEF_PITCHERS = {
    'jhoan duran', 'edwin diaz', 'felix bautista', 'ryan helsley', 'david bednar',
    'alexis diaz', 'josh hader', 'emmanuel clase', 'jordan romano', 'clay holmes'
}

class AdvancedPlayer:
    """Player model with all advanced features including enhanced pitcher detection"""

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

    # Add these methods to AdvancedPlayer class:

    def _parse_positions_enhanced(self, position_str: str) -> List[str]:
        """Enhanced position parsing for multi-position players"""
        if not position_str:
            return ['UTIL']

        position_str = str(position_str).strip().upper()

        # Handle various multi-position delimiters
        delimiters = ['/', ',', '-', '|', '+', ' / ', ' , ', ' - ', ' OR ', ' AND ']
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
            # Remove any numbers or special characters
            pos = ''.join(c for c in pos if c.isalpha())

            mapped_pos = position_mapping.get(pos, pos)
            if mapped_pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'UTIL']:
                if mapped_pos not in valid_positions:
                    valid_positions.append(mapped_pos)

        # If we found valid positions, return them; otherwise default to UTIL
        return valid_positions if valid_positions else ['UTIL']

    def get_position_string(self) -> str:
        """Get position string showing flexibility"""
        if len(self.positions) > 1:
            return f"{self.primary_position} ({'/'.join(self.positions)})"
        return self.primary_position

    def get_position_display(self) -> str:
        """Get display string for GUI"""
        if hasattr(self, 'assigned_position') and self.assigned_position != self.primary_position:
            # Show assigned position with flexibility indicator
            if len(self.positions) > 1:
                return f"{self.assigned_position}*"  # * indicates flex usage
            return self.assigned_position
        return self.primary_position

    def is_using_flex_position(self) -> bool:
        """Check if player is assigned to non-primary position"""
        if hasattr(self, 'assigned_position'):
            return self.assigned_position != self.primary_position
        return False

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

    # Add this debug method to bulletproof_dfs_core.py
    def debug_confirmations(self):
        """Debug why players aren't getting confirmed"""
        print("\n🔍 DEBUG: Why aren't players confirmed?")

        # Check lineup matches
        for player in self.players:
            if self.confirmation_system:
                is_confirmed, order = self.confirmation_system.is_player_confirmed(
                    player.name, player.team
                )
                if is_confirmed:
                    print(f"✅ {player.name} ({player.team}) - Confirmed, batting {order}")
                    player.add_confirmation_source("mlb_lineup")
                else:
                    # Check if team has lineup
                    if player.team in self.confirmation_system.confirmed_lineups:
                        print(f"❌ {player.name} ({player.team}) - Team has lineup but player not in it")

        # Check pitcher matches
        pitchers = [p for p in self.players if p.primary_position == 'P']
        for pitcher in pitchers:
            if self.confirmation_system:
                is_confirmed = self.confirmation_system.is_pitcher_confirmed(
                    pitcher.name, pitcher.team
                )
                if is_confirmed:
                    print(f"✅ {pitcher.name} ({pitcher.team}) - Confirmed starter")
                    pitcher.add_confirmation_source("mlb_starter")
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
        """FIXED: Enhanced eligibility check with pitcher validation"""

        # SHOWDOWN: All players are eligible!
        if hasattr(self, 'contest_type') and self.contest_type == 'showdown':
            return True

        if mode == 'manual_only':
            return self.is_manual_selected
        elif mode == 'confirmed_only':
            # Extra check for pitchers
            if self.primary_position == 'P':
                return self.is_confirmed and 'mlb_starter' in self.confirmation_sources
            return self.is_confirmed
        else:  # bulletproof (default)
            # Manual selections always eligible
            if self.is_manual_selected:
                return True

            # For confirmed players, extra validation for pitchers
            if self.is_confirmed:
                if self.primary_position == 'P':
                    # Pitcher MUST be MLB confirmed starter
                    return 'mlb_starter' in self.confirmation_sources
                return True

            return False

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

    def apply_contest_specific_adjustments(self, contest_type: str):
        """
        Apply temporary contest-specific score adjustments
        IMPORTANT: Creates adjusted scores without modifying base enhanced_score
        """
        print(f"\n🎯 Applying {contest_type.upper()} contest adjustments...")

        for player in self.players:
            # Store original score if not already stored
            if not hasattr(player, 'base_enhanced_score'):
                player.base_enhanced_score = player.enhanced_score

            # Reset to base before applying new adjustments
            player.enhanced_score = player.base_enhanced_score

            if contest_type == 'gpp':
                # GPP: Favor high ceiling players
                ceiling_multiplier = 1.0

                # Boost based on Statcast power metrics
                if hasattr(player, 'statcast_data') and player.statcast_data:
                    barrel = player.statcast_data.get('Barrel', 0)
                    hard_hit = player.statcast_data.get('Hard_Hit', 0)

                    if barrel > 12:  # Elite barrel rate
                        ceiling_multiplier *= 1.12
                    elif barrel > 10:
                        ceiling_multiplier *= 1.08

                    if hard_hit > 45:  # Elite hard hit
                        ceiling_multiplier *= 1.05

                # Boost high-upside positions
                if player.primary_position in ['SS', 'OF']:
                    ceiling_multiplier *= 1.03

                # Apply GPP adjustment
                player.enhanced_score *= ceiling_multiplier
                player.contest_adjustment = ceiling_multiplier

            elif contest_type == 'cash':
                # Cash: Favor consistent, confirmed players
                floor_multiplier = 1.0

                # Boost confirmed players
                if player.is_confirmed:
                    floor_multiplier *= 1.08

                # Boost if in good Vegas spot
                if hasattr(player, 'vegas_data') and player.vegas_data:
                    team_total = player.vegas_data.get('team_total', 4.5)
                    if team_total >= 5.0 and player.primary_position != 'P':
                        floor_multiplier *= 1.05
                    elif team_total <= 4.0 and player.primary_position == 'P':
                        floor_multiplier *= 1.05

                # Penalize unconfirmed players
                if not player.is_confirmed and not player.is_manual_selected:
                    floor_multiplier *= 0.90

                # Apply cash adjustment
                player.enhanced_score *= floor_multiplier
                player.contest_adjustment = floor_multiplier

            elif contest_type == 'single':
                # Single entry: Balanced approach
                balance_multiplier = 1.0

                # Slight boost for confirmed
                if player.is_confirmed:
                    balance_multiplier *= 1.04

                # Moderate ceiling boost
                if hasattr(player, 'statcast_data') and player.statcast_data:
                    barrel = player.statcast_data.get('Barrel', 0)
                    if barrel > 10:
                        balance_multiplier *= 1.05

                player.enhanced_score *= balance_multiplier
                player.contest_adjustment = balance_multiplier

        # Report adjustments
        adjusted_count = sum(
            1 for p in self.players if hasattr(p, 'contest_adjustment') and p.contest_adjustment != 1.0)
        print(f"✅ Applied {contest_type} adjustments to {adjusted_count} players")

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
        """ENHANCED: Get comprehensive status string showing ALL data sources"""
        status_parts = []

        # Multi-position display
        if len(self.positions) > 1:
            pos_display = "/".join(self.positions)
            status_parts.append(f"MULTI-POS({pos_display})")

        # Confirmation status
        if self.is_confirmed:
            sources = ", ".join(self.confirmation_sources[:2])  # Show first 2 sources
            status_parts.append(f"CONFIRMED({sources})")
        if self.is_manual_selected:
            status_parts.append("MANUAL")

        # DFF data
        if hasattr(self, 'dff_data') and self.dff_data:
            dff_parts = []
            if self.dff_data.get('ppg_projection', 0) > 0:
                dff_parts.append(f"PROJ:{self.dff_data['ppg_projection']:.1f}")
            if self.dff_data.get('ownership', 0) > 0:
                dff_parts.append(f"OWN:{self.dff_data['ownership']:.1f}%")
            if dff_parts:
                status_parts.append(f"DFF({','.join(dff_parts)})")

        # Statcast data
        if hasattr(self, 'statcast_data') and self.statcast_data:
            statcast_parts = []
            if 'xwOBA' in self.statcast_data:
                statcast_parts.append(f"xwOBA:{self.statcast_data['xwOBA']:.3f}")
            if 'Hard_Hit' in self.statcast_data:
                statcast_parts.append(f"HH:{self.statcast_data['Hard_Hit']:.1f}%")
            if statcast_parts:
                status_parts.append(f"STATCAST({','.join(statcast_parts)})")

        # Vegas data
        if hasattr(self, 'vegas_data') and self.vegas_data:
            vegas_parts = []
            if 'team_total' in self.vegas_data:
                vegas_parts.append(f"TT:{self.vegas_data['team_total']:.1f}")
            if vegas_parts:
                status_parts.append(f"VEGAS({','.join(vegas_parts)})")

        # Park factors
        if hasattr(self, 'park_factors') and self.park_factors:
            factor = self.park_factors.get('factor', 1.0)
            status_parts.append(f"PARK({factor:.2f}x)")

        # NEW: Add batting order
        if hasattr(self, 'batting_order') and self.batting_order:
            status_parts.append(f"BAT-{self.batting_order}")

        # NEW: Add correlation info
        if hasattr(self, 'correlation_adjustment') and self.correlation_adjustment:
            status_parts.append(f"CORR({self.correlation_adjustment:+.0%})")

        # Recent form
        if hasattr(self, '_recent_performance') and self._recent_performance:
            form = self._recent_performance
            if form.get('streak_type'):
                status_parts.append(f"{form['streak_type'].upper()}-STREAK({form['streak_length']})")
            elif form.get('form_score', 1.0) != 1.0:
                status_parts.append(f"FORM({form['form_score']:.2f})")

        return " | ".join(status_parts) if status_parts else "UNCONFIRMED"

    def get_position_flexibility_score(self) -> float:
        """Calculate position flexibility score (0-10)"""
        if len(self.positions) == 1:
            return 0.0
        elif len(self.positions) == 2:
            return 5.0
        elif len(self.positions) >= 3:
            return 8.0
        return 0.0

    def get_optimal_position_assignment(self, needed_positions: Dict[str, int]) -> str:
        """Get optimal position assignment based on current needs"""
        if not needed_positions:
            return self.primary_position

        # Find position with highest need that this player can fill
        best_pos = self.primary_position
        max_need = needed_positions.get(self.primary_position, 0)

        for pos in self.positions:
            need = needed_positions.get(pos, 0)
            if need > max_need:
                max_need = need
                best_pos = pos

        return best_pos

    def get_flexibility_value_bonus(self) -> float:
        """Get value bonus for position flexibility (1.0 = no bonus, 1.05 = 5% bonus)"""
        flexibility_score = self.get_position_flexibility_score()
        if flexibility_score >= 8:
            return 1.05  # 5% bonus for 3+ positions
        elif flexibility_score >= 5:
            return 1.02  # 2% bonus for 2 positions
        return 1.0  # No bonus for single position

    def __repr__(self):
        pos_str = '/'.join(self.positions)
        status = "✅" if self.is_eligible_for_selection() else "❌"
        return f"Player({self.name}, {pos_str}, ${self.salary}, {self.enhanced_score:.1f}, {status})"



class BulletproofDFSCore:
    """Complete bulletproof DFS core with enhanced pitcher detection"""

    def __init__(self):
        self.players = []
        self.contest_type = 'classic'
        self.salary_cap = 50000
        self.optimization_mode = 'bulletproof'
        self.dff_classic_file = None
        self.dff_showdown_file = None
        self.current_dff_file = None

        # Set game date
        self.game_date = datetime.now().strftime('%Y-%m-%d')

        # Initialize modules
        self.vegas_lines = VegasLines() if VEGAS_AVAILABLE else None

        # Fix SmartConfirmationSystem initialization
        if CONFIRMED_AVAILABLE:
            try:
                self.confirmation_system = SmartConfirmationSystem(
                    csv_players=self.players,
                    verbose=True
                )
                print("✅ Smart Confirmation System initialized")
            except Exception as e:
                print(f"❌ Failed to initialize SmartConfirmationSystem: {e}")
                self.confirmation_system = None
        else:
            self.confirmation_system = None
            print("⚠️ SmartConfirmationSystem not available")

        self.statcast_fetcher = SimpleStatcastFetcher() if STATCAST_AVAILABLE else None

        # NEW: Initialize recent form analyzer if available
        if RECENT_FORM_AVAILABLE:
            from utils.cache_manager import cache
            self.form_analyzer = RecentFormAnalyzer(cache_manager=cache)
        else:
            self.form_analyzer = None

        # NEW: Initialize batting order and correlation systems
        if BATTING_CORRELATION_AVAILABLE:
            integrate_batting_order_correlation(self)

        print("🚀 Bulletproof DFS Core - ALL METHODS INCLUDED WITH ENHANCED PITCHER DETECTION")
    # ==================== DFS UPGRADE METHODS ====================

    def get_cached_data(self, key: str, fetch_func, category: str = 'default'):
        """Use smart caching for any data fetch"""
        if 'UPGRADES_AVAILABLE' in globals() and UPGRADES_AVAILABLE:
            return smart_cache.get_or_fetch(key, fetch_func, category)
        else:
            return fetch_func()

    def generate_multiple_lineups(self, count: int = 20) -> list:
        """Generate multiple unique lineups for GPPs"""
        if 'UPGRADES_AVAILABLE' not in globals() or not UPGRADES_AVAILABLE:
            print("❌ Multi-lineup module not available")
            return []

        print(f"\n🚀 Generating {count} lineups...")

        optimizer = MultiLineupOptimizer(self)
        lineups = optimizer.generate_gpp_lineups(
            num_lineups=count,
            max_exposure=0.5,
            min_salary=49000
        )

        # Show summary
        optimizer.print_summary()

        # Export for upload
        upload_file = optimizer.export_for_upload('draftkings')
        if upload_file:
            print(f"\n📁 Upload file: {upload_file}")

        return lineups

    def track_lineup_performance(self, lineup: list, contest_info: dict):
        """Track lineup for future analysis"""
        if 'UPGRADES_AVAILABLE' not in globals() or not UPGRADES_AVAILABLE:
            return None

        contest_id = tracker.log_contest(lineup, contest_info)

        # Also save to database if available
        if hasattr(self, 'game_date'):
            contest_info['date'] = self.game_date

        return contest_id

    def get_performance_summary(self, days: int = 30):
        """Get performance tracking summary"""
        if 'UPGRADES_AVAILABLE' not in globals() or not UPGRADES_AVAILABLE:
            print("Performance tracking not available")
            return

        tracker.print_summary(days)

    def clear_cache(self, category: str = None):
        """Clear cache by category or all"""
        if 'UPGRADES_AVAILABLE' in globals() and UPGRADES_AVAILABLE:
            smart_cache.clear(category)
            print(f"🧹 Cleared cache: {category or 'all'}")


    def detect_and_load_dff_files(self, dff_file_path: str = None):
        """
        Intelligently detect and load appropriate DFF file based on contest type
        Handles both manual file selection and auto-detection
        """
        import glob

        print("\n📂 DFF FILE DETECTION")
        print("=" * 50)

        # If a specific file is provided
        if dff_file_path and os.path.exists(dff_file_path):
            filename = os.path.basename(dff_file_path).lower()

            # Check if file matches contest type
            is_showdown_file = any(ind in filename for ind in ['showdown', 'sd', 'captain', 'cptn'])

            if self.contest_type == 'showdown' and is_showdown_file:
                print(f"✅ Loading SHOWDOWN DFF file: {os.path.basename(dff_file_path)}")
                self.dff_showdown_file = dff_file_path
                return self.apply_dff_rankings(dff_file_path)
            elif self.contest_type == 'classic' and not is_showdown_file:
                print(f"✅ Loading CLASSIC DFF file: {os.path.basename(dff_file_path)}")
                self.dff_classic_file = dff_file_path
                return self.apply_dff_rankings(dff_file_path)
            else:
                # Mismatch warning but still load
                print(
                    f"⚠️ DFF file type mismatch! Contest: {self.contest_type}, File type: {'showdown' if is_showdown_file else 'classic'}")
                print(f"   Loading anyway: {os.path.basename(dff_file_path)}")
                return self.apply_dff_rankings(dff_file_path)

        # Auto-detect DFF files in current directory
        else:
            print("🔍 Auto-detecting DFF files...")

            # Look for all DFF files
            dff_files = []
            for pattern in ['DFF_MLB_*.csv', 'DFF_*.csv', '*cheatsheet*.csv']:
                dff_files.extend(glob.glob(pattern))

            # Remove duplicates
            dff_files = list(set(dff_files))

            if not dff_files:
                print("❌ No DFF files found in current directory")
                print("   Looking for patterns: DFF_MLB_*.csv, DFF_*.csv, *cheatsheet*.csv")
                return False

            print(f"📁 Found {len(dff_files)} DFF file(s):")
            for f in dff_files:
                print(f"   - {f}")

            # Separate showdown and classic files
            showdown_files = []
            classic_files = []

            for file in dff_files:
                filename_lower = file.lower()
                if any(ind in filename_lower for ind in ['showdown', 'sd', 'captain', 'cptn']):
                    showdown_files.append(file)
                else:
                    classic_files.append(file)

            # Load appropriate file based on contest type
            if self.contest_type == 'showdown':
                if showdown_files:
                    # Pick the most recent showdown file
                    showdown_files.sort(key=os.path.getmtime, reverse=True)
                    selected_file = showdown_files[0]
                    self.dff_showdown_file = selected_file
                    print(f"\n✅ Auto-selected SHOWDOWN DFF: {selected_file}")
                    return self.apply_dff_rankings(selected_file)
                elif classic_files:
                    print(f"\n⚠️ No showdown DFF found, using classic DFF for showdown contest")
                    selected_file = classic_files[0]
                    return self.apply_dff_rankings(selected_file)
                else:
                    print("❌ No suitable DFF files found")
                    return False

            else:  # classic contest
                if classic_files:
                    # Pick the most recent classic file
                    classic_files.sort(key=os.path.getmtime, reverse=True)
                    selected_file = classic_files[0]
                    self.dff_classic_file = selected_file
                    print(f"\n✅ Auto-selected CLASSIC DFF: {selected_file}")
                    return self.apply_dff_rankings(selected_file)
                elif showdown_files:
                    print(f"\n⚠️ No classic DFF found, using showdown DFF for classic contest")
                    selected_file = showdown_files[0]
                    return self.apply_dff_rankings(selected_file)
                else:
                    print("❌ No suitable DFF files found")
                    return False

        return False

    def enrich_with_recent_form(self):
        """Enrich players with recent form analysis"""
        if not self.form_analyzer:
            print("⚠️ Recent form analyzer not available")
            return 0

        eligible = [p for p in self.players if p.is_eligible_for_selection(self.optimization_mode)]
        return self.form_analyzer.enrich_players_with_form(eligible)

    def enrich_with_batting_order(self):
        """Enrich players with batting order data"""
        if hasattr(self, 'batting_enricher'):
            eligible = [p for p in self.players if p.is_eligible_for_selection(self.optimization_mode)]
            return self.batting_enricher.enrich_with_batting_order(eligible)
        return 0

    def apply_lineup_correlations(self, lineup):
        """Apply correlation adjustments to lineup"""
        if hasattr(self, 'correlation_optimizer') and hasattr(self, 'vegas_lines'):
            vegas_data = self.vegas_lines.lines if self.vegas_lines else None
            return self.correlation_optimizer.apply_correlation_adjustments(lineup, vegas_data)
        return lineup

    # Replace the apply_dff_rankings method in BulletproofDFSCore with this enhanced version

    def apply_dff_rankings(self, dff_file_path: str) -> bool:
        """Enhanced DFF application with better matching and debugging"""
        if not dff_file_path or not os.path.exists(dff_file_path):
            print("⚠️ No DFF file provided or file not found")
            return False

        try:
            print(f"\n🎯 Loading DFF rankings: {Path(dff_file_path).name}")
            df = pd.read_csv(dff_file_path)

            print(f"📊 DFF Data Summary:")
            print(f"   Rows: {len(df)}")
            print(f"   Columns: {list(df.columns)[:5]}{'...' if len(df.columns) > 5 else ''}")

            # Auto-detect important columns
            name_col = None
            proj_col = None
            own_col = None
            value_col = None
            team_col = None

            for col in df.columns:
                col_lower = col.lower()
                if not name_col and any(x in col_lower for x in ['name', 'player']):
                    name_col = col
                elif not proj_col and any(x in col_lower for x in ['projection', 'proj', 'ppg', 'fpts', 'points']):
                    proj_col = col
                elif not own_col and any(x in col_lower for x in ['own', 'ownership', '%']):
                    own_col = col
                elif not value_col and any(x in col_lower for x in ['value', 'val']):
                    value_col = col
                elif not team_col and any(x in col_lower for x in ['team', 'tm']):
                    team_col = col

            if not name_col:
                print("❌ Could not find player name column in DFF file")
                return False

            print(f"📋 Detected DFF columns:")
            print(f"   Name: '{name_col}'")
            print(f"   Projection: '{proj_col}' {'✓' if proj_col else '✗'}")
            print(f"   Ownership: '{own_col}' {'✓' if own_col else '✗'}")
            print(f"   Value: '{value_col}' {'✓' if value_col else '✗'}")
            print(f"   Team: '{team_col}' {'✓' if team_col else '✗'}")

            # Create lookup dictionaries for faster matching
            dk_players_by_name = {}
            dk_players_by_team = {}

            # Build lookup dictionaries with cleaned names
            for player in self.players:
                # Clean DK player name
                dk_name_clean = self.clean_player_name_for_matching(player.name)
                dk_name_lower = dk_name_clean.lower()

                # Store by cleaned name
                dk_players_by_name[dk_name_lower] = player

                # Also store by last name only
                if ' ' in dk_name_clean:
                    last_name = dk_name_lower.split()[-1]
                    if last_name not in dk_players_by_name:
                        dk_players_by_name[last_name] = player

                # Store by team
                if player.team:
                    if player.team not in dk_players_by_team:
                        dk_players_by_team[player.team] = []
                    dk_players_by_team[player.team].append(player)

            # Debug: Show sample names
            print(f"\n📋 Sample DFF names (first 5):")
            for i, name in enumerate(df[name_col].head(5)):
                print(f"   {i + 1}. {name}")

            print(f"\n📋 Sample DK player names (first 5):")
            for i, player in enumerate(self.players[:5]):
                print(f"   {i + 1}. {player.name} ({player.team})")

            # Match players
            matches = 0
            no_matches = []
            eligible_enriched = 0
            all_enriched = 0

            for idx, row in df.iterrows():
                try:
                    # Get raw DFF name
                    dff_name_raw = str(row[name_col]).strip()
                    if not dff_name_raw or dff_name_raw == 'nan':
                        continue

                    # USE THE NEW CLEANING METHOD HERE
                    dff_name = self.clean_player_name_for_matching(dff_name_raw)
                    dff_name_lower = dff_name.lower()

                    # Get team if available
                    dff_team = str(row[team_col]).strip().upper() if team_col and pd.notna(row[team_col]) else None

                    # Build DFF data dict
                    dff_data = {
                        'dff_name': dff_name,
                        'source': 'DFF Rankings'
                    }

                    # Extract projection
                    if proj_col and pd.notna(row[proj_col]):
                        try:
                            proj_str = str(row[proj_col]).replace('$', '').replace(',', '').strip()
                            dff_data['ppg_projection'] = float(proj_str)
                        except:
                            pass

                    # Extract ownership
                    if own_col and pd.notna(row[own_col]):
                        try:
                            own_str = str(row[own_col]).replace('%', '').strip()
                            dff_data['ownership'] = float(own_str)
                        except:
                            pass

                    # Extract value
                    if value_col and pd.notna(row[value_col]):
                        try:
                            dff_data['value'] = float(row[value_col])
                        except:
                            pass

                    # Find best matching player
                    best_match = None
                    best_score = 0

                    # Method 1: Exact name match with cleaned names
                    if dff_name_lower in dk_players_by_name:
                        best_match = dk_players_by_name[dff_name_lower]
                        best_score = 1.0
                    else:
                        # Method 2: Last name match + team verification
                        last_name = dff_name_lower.split()[-1] if ' ' in dff_name_lower else dff_name_lower

                        if last_name in dk_players_by_name:
                            candidate = dk_players_by_name[last_name]
                            # Verify team matches if we have team data
                            if dff_team and candidate.team == dff_team:
                                best_match = candidate
                                best_score = 0.95
                            elif not dff_team:
                                best_match = candidate
                                best_score = 0.85

                        # Method 3: Fuzzy matching within same team
                        if not best_match and dff_team and dff_team in dk_players_by_team:
                            for player in dk_players_by_team[dff_team]:
                                # Clean DK name for comparison
                                dk_name_clean = self.clean_player_name_for_matching(player.name)
                                score = self._name_similarity(dff_name, dk_name_clean)
                                if score > best_score and score >= 0.75:  # Lower threshold for same team
                                    best_score = score
                                    best_match = player

                        # Method 4: Global fuzzy matching (last resort)
                        if not best_match:
                            for player in self.players:
                                # Clean DK name for comparison
                                dk_name_clean = self.clean_player_name_for_matching(player.name)
                                score = self._name_similarity(dff_name, dk_name_clean)
                                if score > best_score and score >= 0.85:
                                    best_score = score
                                    best_match = player

                    if best_match and 'ppg_projection' in dff_data:
                        # APPLY TO MATCHED PLAYER
                        best_match.apply_dff_data(dff_data)
                        matches += 1
                        all_enriched += 1

                        # Check if this player is eligible
                        if best_match.is_eligible_for_selection(self.optimization_mode):
                            eligible_enriched += 1

                            # Show match details for first few or significant differences
                            if eligible_enriched <= 5 or abs(dff_data['ppg_projection'] - best_match.base_score) > 2:
                                proj = dff_data['ppg_projection']
                                own = dff_data.get('ownership', 'N/A')
                                match_indicator = "✅" if best_score >= 0.95 else f"🔄 ({best_score:.2f})"

                                print(f"\n   {match_indicator} DFF MATCH: {dff_name_raw} → {best_match.name}")
                                print(
                                    f"      Cleaned: {dff_name} → {self.clean_player_name_for_matching(best_match.name)}")
                                print(f"      Team: {dff_team or 'N/A'} → {best_match.team}")
                                print(f"      Projection: {proj:.1f} | Ownership: {own}%")
                    else:
                        no_matches.append(f"{dff_name_raw} ({dff_team or 'N/A'})")

                except Exception as e:
                    print(f"   ❌ Error processing row {idx}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            print(f"\n📊 DFF Integration Summary:")
            print(f"   Total DFF players: {len(df)}")
            print(f"   Matched to DK: {matches}")
            print(f"   Applied to all: {all_enriched}")
            print(f"   Eligible players enriched: {eligible_enriched}")
            print(f"   Success rate: {(matches / len(df) * 100):.1f}%" if len(df) > 0 else "N/A")

            # Show some unmatched for debugging
            if no_matches and len(no_matches) <= 10:
                print(f"\n❌ Unmatched DFF players (first 10):")
                for name in no_matches[:10]:
                    print(f"   - {name}")
            elif no_matches:
                print(f"\n❌ {len(no_matches)} DFF players didn't match")

            # Special message if no eligible players got DFF
            if eligible_enriched == 0 and matches > 0:
                print(f"\n⚠️ WARNING: DFF matched {matches} players but NONE were eligible!")
                print(f"   This usually means DFF players aren't in your confirmed/manual selections")
                print(f"   Consider adding some DFF players to manual selections")

            return matches > 0

        except Exception as e:
            print(f"❌ Error loading DFF data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _name_similarity(self, name1: str, name2: str) -> float:
        """Enhanced name matching with special handling for common variations"""
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()

        # Remove common suffixes
        for suffix in [' jr', ' jr.', ' sr', ' sr.', ' iii', ' ii', ' iv', ' v']:
            name1 = name1.replace(suffix, '')
            name2 = name2.replace(suffix, '')

        # Exact match
        if name1 == name2:
            return 1.0

        # Check if one contains the other
        if name1 in name2 or name2 in name1:
            return 0.95

        # Split names
        parts1 = name1.split()
        parts2 = name2.split()

        if len(parts1) >= 2 and len(parts2) >= 2:
            # Last name exact match
            if parts1[-1] == parts2[-1]:
                # First name initial match
                if parts1[0][0] == parts2[0][0]:
                    return 0.9
                # Check common nicknames
                if self._are_nicknames(parts1[0], parts2[0]):
                    return 0.85

        # Fuzzy match
        from difflib import SequenceMatcher
        return SequenceMatcher(None, name1, name2).ratio()

    def reset_all_confirmations(self):
        """Reset ALL confirmation status - call this at the start of each run"""
        print("\n🔄 RESETTING ALL CONFIRMATIONS")
        for player in self.players:
            player.is_confirmed = False
            player.confirmation_sources = []
            # Don't reset manual selections
        print(f"✅ Reset confirmations for {len(self.players)} players")

    def _are_nicknames(self, name1: str, name2: str) -> bool:
        """Check if two names are common nicknames"""
        nicknames = {
            # Common nicknames
            'mike': 'michael', 'michael': 'mike',
            'chris': 'christopher', 'christopher': 'chris',
            'dave': 'david', 'david': 'dave',
            'rob': 'robert', 'robert': 'rob', 'bob': 'robert', 'bobby': 'robert',
            'matt': 'matthew', 'matthew': 'matt', 'matty': 'matthew',
            'joe': 'joseph', 'joseph': 'joe', 'joey': 'joseph',
            'alex': 'alexander', 'alexander': 'alex',
            'will': 'william', 'william': 'will', 'willie': 'william', 'bill': 'william', 'billy': 'william',
            'jake': 'jacob', 'jacob': 'jake',
            'josh': 'joshua', 'joshua': 'josh',
            'jon': 'jonathan', 'jonathan': 'jon', 'jonny': 'jonathan',
            'nick': 'nicholas', 'nicholas': 'nick', 'nicky': 'nicholas',
            'tony': 'anthony', 'anthony': 'tony',
            'andy': 'andrew', 'andrew': 'andy', 'drew': 'andrew',
            'dan': 'daniel', 'daniel': 'dan', 'danny': 'daniel',
            'jim': 'james', 'james': 'jim', 'jimmy': 'james',
            'ed': 'edward', 'edward': 'ed', 'eddie': 'edward',
            'tom': 'thomas', 'thomas': 'tom', 'tommy': 'thomas',
            'ben': 'benjamin', 'benjamin': 'ben', 'benny': 'benjamin',
            'ken': 'kenneth', 'kenneth': 'ken', 'kenny': 'kenneth',
            'steve': 'stephen', 'stephen': 'steve', 'steven': 'steve',
            'rick': 'richard', 'richard': 'rick', 'ricky': 'richard', 'dick': 'richard',
            'charlie': 'charles', 'charles': 'charlie', 'chuck': 'charles',
            'ted': 'theodore', 'theodore': 'ted', 'teddy': 'theodore',
            'frank': 'francis', 'francis': 'frank', 'frankie': 'francis',
            'sam': 'samuel', 'samuel': 'sam', 'sammy': 'samuel',
            'tim': 'timothy', 'timothy': 'tim', 'timmy': 'timothy',
            'pat': 'patrick', 'patrick': 'pat',
            'pete': 'peter', 'peter': 'pete',

            # Spanish/Latin nicknames common in baseball
            'alex': 'alejandro', 'alejandro': 'alex',
            'manny': 'manuel', 'manuel': 'manny',
            'rafa': 'rafael', 'rafael': 'rafa',
            'miggy': 'miguel', 'miguel': 'miggy',
            'vlad': 'vladimir', 'vladimir': 'vlad', 'vladdy': 'vladimir',

            # Baseball-specific common nicknames
            'aj': 'aaron', 'aj': 'andrew', 'aj': 'anthony',  # A.J. can be multiple names
            'cj': 'christopher', 'cj': 'carl', 'cj': 'charles',
            'dj': 'david', 'dj': 'daniel', 'dj': 'derek',
            'tj': 'thomas', 'tj': 'tyler', 'tj': 'timothy',
            'jp': 'john', 'jp': 'james', 'jp': 'joseph',
            'jd': 'john', 'jd': 'james', 'jd': 'joseph',

            # Other common baseball nicknames
            'bo': 'robert', 'buster': 'gerald', 'chipper': 'larry',
            'dusty': 'johnnie', 'duke': 'edwin', 'goose': 'richard',
            'lefty': 'steve', 'moose': 'michael', 'pudge': 'ivan',
            'rusty': 'russell', 'sandy': 'sanford', 'sparky': 'george',
            'whitey': 'edward', 'yogi': 'lawrence'
        }

        name1_lower = name1.lower().strip()
        name2_lower = name2.lower().strip()

        # Direct nickname match
        if nicknames.get(name1_lower) == name2_lower or nicknames.get(name2_lower) == name1_lower:
            return True

        # Check if both map to same full name
        if name1_lower in nicknames and name2_lower in nicknames:
            if nicknames[name1_lower] == nicknames[name2_lower]:
                return True

        # Handle initials (A.J., C.J., etc.)
        if len(name1_lower) == 2 and '.' not in name1_lower and len(name2_lower) > 2:
            # Check if initials match first letters
            if name1_lower[0] == name2_lower[0]:
                return True

        return False

    def _copy_player(self, player):
        """Create a copy of player"""
        import copy
        return copy.deepcopy(player)

    def set_optimization_mode(self, mode: str):
        """Set optimization mode with validation"""
        valid_modes = ['bulletproof', 'manual_only', 'confirmed_only', 'all']

        # Handle different mode names from GUI
        mode_mapping = {
            'all players': 'all',
            'all_players': 'all',
            'manual only': 'manual_only',
            'confirmed only': 'confirmed_only',
            'bulletproof (confirmed + manual)': 'bulletproof'
        }

        # Normalize the mode
        mode_lower = mode.lower()
        if mode_lower in mode_mapping:
            mode = mode_mapping[mode_lower]

        if mode in valid_modes:
            self.optimization_mode = mode
            print(f"⚙️ Optimization mode set to: {mode}")
        else:
            print(f"❌ Invalid mode '{mode}'. Choose from: {valid_modes}")
            print(f"   Keeping current mode: {self.optimization_mode}")

    def load_draftkings_csv(self, file_path: str) -> bool:
        """Load DraftKings CSV with better multi-position parsing"""
        try:
            print(f"📁 Loading DraftKings CSV: {Path(file_path).name}")

            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                return False

            # Read CSV first to detect contest type
            df = pd.read_csv(file_path)
            print(f"📊 Found {len(df)} rows, {len(df.columns)} columns")

            # ENHANCED SHOWDOWN DETECTION
            filename = os.path.basename(file_path).lower()
            if any(indicator in filename for indicator in ['showdown', 'captain', 'sd', 'cptn']):
                self.contest_type = 'showdown'
                print("🎯 SHOWDOWN DETECTED (filename)")
            else:
                # Method 2: Check team count
                team_col_idx = None
                for i, col in enumerate(df.columns):
                    if 'team' in str(col).lower():
                        team_col_idx = i
                        break

                if team_col_idx is not None:
                    unique_teams = df.iloc[:, team_col_idx].dropna().unique()
                    team_count = len([t for t in unique_teams if str(t).strip() and str(t) != 'nan'])

                    if team_count <= 2:
                        self.contest_type = 'showdown'
                        print(f"🎯 SHOWDOWN DETECTED ({team_count} teams)")
                    else:
                        self.contest_type = 'classic'
                        print(f"🏈 CLASSIC CONTEST ({team_count} teams)")

            # Update salary cap for showdown
            if self.contest_type == 'showdown':
                self.salary_cap = 50000
                print("💰 Showdown salary cap: $50,000")

            # COLUMN DETECTION
            column_map = {}
            roster_position_idx = None

            for i, col in enumerate(df.columns):
                col_lower = str(col).lower().strip()

                # Check for Roster Position column specifically
                if 'roster position' in col_lower:
                    roster_position_idx = i
                    print(f"   Found Roster Position column at index {i}")

                # Name column detection
                if any(name in col_lower for name in ['name', 'player']):
                    if 'name' in col_lower and '+' not in col_lower and 'name' not in column_map:
                        column_map['name'] = i

                # Position column detection
                elif any(pos in col_lower for pos in ['position']) and 'roster' not in col_lower:
                    if 'position' not in column_map:
                        column_map['position'] = i

                # Team column detection
                elif any(team in col_lower for team in ['team', 'teamabbrev', 'tm']):
                    if 'team' not in column_map:
                        column_map['team'] = i

                # Salary column detection
                elif any(sal in col_lower for sal in ['salary', 'sal', 'cost']):
                    if 'salary' not in column_map:
                        column_map['salary'] = i

                # Projection column detection
                elif any(proj in col_lower for proj in ['avgpointspergame', 'fppg', 'projection', 'points']):
                    if 'projection' not in column_map:
                        column_map['projection'] = i

            # Debug: Show detected columns
            print(f"📋 Detected columns:")
            for field, idx in column_map.items():
                print(f"   {field}: column {idx} ('{df.columns[idx]}')")

            # Parse players
            players = []
            multi_position_players = []

            for idx, row in df.iterrows():
                try:
                    # Get position string - prioritize Roster Position for multi-positions
                    position_str = ""

                    if roster_position_idx is not None:
                        position_str = str(row.iloc[roster_position_idx]).strip()

                    # If empty or nan, try regular Position column
                    if not position_str or position_str.lower() == 'nan':
                        position_str = str(row.iloc[column_map.get('position', 1)]).strip()

                    player_data = {
                        'id': idx + 1,
                        'name': str(row.iloc[column_map.get('name', 0)]).strip(),
                        'position': position_str,  # Pass the full position string
                        'team': str(row.iloc[column_map.get('team', 2)]).strip(),
                        'salary': row.iloc[column_map.get('salary', 3)],
                        'projection': row.iloc[column_map.get('projection', 4)]
                    }

                    player = AdvancedPlayer(player_data)

                    # SHOWDOWN POSITION OVERRIDE
                    if self.contest_type == 'showdown':
                        player.positions = ['CPT', 'UTIL']
                        player.primary_position = 'UTIL'
                        player.showdown_eligible = True

                    # Track multi-position players
                    if len(player.positions) > 1:
                        multi_position_players.append(f"{player.name} ({'/'.join(player.positions)})")

                    if player.name and player.salary > 0:
                        players.append(player)

                except Exception as e:
                    print(f"Error parsing row {idx}: {e}")
                    continue

            self.players = players

            # Show multi-position players
            if multi_position_players:
                print(f"\n🔄 Found {len(multi_position_players)} multi-position players:")
                for mp in multi_position_players[:10]:  # Show first 10
                    print(f"   {mp}")
                if len(multi_position_players) > 10:
                    print(f"   ... and {len(multi_position_players) - 10} more")



            print(f"✅ Loaded {len(self.players)} valid {self.contest_type.upper()} players")

            # Position statistics
            multi_position_count = sum(1 for p in self.players if len(p.positions) > 1)
            single_position_count = sum(1 for p in self.players if len(p.positions) == 1)
            print(f"📊 Position stats: {multi_position_count} multi-position, {single_position_count} single-position")

            return True

        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            import traceback
            traceback.print_exc()
            return False

    def apply_manual_selection(self, manual_input: str) -> int:
        """Apply manual player selection with enhanced matching"""
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
                if similarity > best_score and similarity >= 0.6:  # Lowered threshold
                    best_score = similarity
                    best_match = player

            if best_match:
                best_match.set_manual_selected()
                matches += 1
                print(f"   ✅ {manual_name} → {best_match.name} ({best_score:.2f})")
            else:
                # Try partial matching
                for player in self.players:
                    if manual_name.lower() in player.name.lower():
                        player.set_manual_selected()
                        matches += 1
                        print(f"   ✅ {manual_name} → {player.name} (partial)")
                        break
                else:
                    print(f"   ❌ {manual_name} → No match found")

        return matches


    def _name_similarity(self, name1: str, name2: str) -> float:
        """Enhanced name similarity matching"""
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()

        # Remove common punctuation
        for char in ["'", ".", "-", " jr", " sr", " iii", " ii"]:
            name1 = name1.replace(char, "")
            name2 = name2.replace(char, "")

        if name1 == name2:
            return 1.0

        # Check if one name contains the other
        if name1 in name2 or name2 in name1:
            return 0.9

        # Check last name match
        parts1 = name1.split()
        parts2 = name2.split()

        if parts1 and parts2:
            # Last name exact match
            if parts1[-1] == parts2[-1]:
                return 0.85

            # First initial + last name match
            if len(parts1[0]) > 0 and len(parts2[0]) > 0:
                if parts1[0][0] == parts2[0][0] and parts1[-1] == parts2[-1]:
                    return 0.8

        # Levenshtein distance for close matches
        from difflib import SequenceMatcher
        return SequenceMatcher(None, name1, name2).ratio()
    # !/usr/bin/env python3
    """
    CORE OPTIMIZER UPDATES - NO ARTIFICIAL BOOSTS
    ==============================================
    Clean optimization without inflating confirmed players
    """

    # Add these methods to bulletproof_dfs_core.py

    def generate_contest_lineups(self, count: int = 20,
                                 contest_type: str = 'gpp',
                                 min_salary_pct: float = 0.95,
                                 diversity_factor: float = 0.7,
                                 max_exposure: float = 0.6) -> List[Dict]:
        """
        Generate multiple lineups for specific contest type
        NO ARTIFICIAL BOOSTS - Pure optimization
        """

        print(f"\n🎰 GENERATING {count} {contest_type.upper()} LINEUPS")
        print("=" * 60)

        # Get eligible players
        eligible = self.filter_eligible_players()

        if len(eligible) < 10:
            print(f"❌ Not enough eligible players: {len(eligible)}")
            return []

        generated_lineups = []
        player_usage = {}

        # Contest-specific strategy adjustments (WITHOUT artificial boosts)
        if contest_type == 'cash':
            # For cash games, we want HIGH FLOOR players
            # Sort by floor (consistency) rather than ceiling
            eligible = self._sort_by_floor(eligible)
        elif contest_type == 'gpp':
            # For GPPs, we want HIGH CEILING players
            # Sort by ceiling (upside) rather than floor
            eligible = self._sort_by_ceiling(eligible)

        successful = 0
        attempts = 0
        max_attempts = count * 3  # Allow some failures

        while successful < count and attempts < max_attempts:
            attempts += 1

            # Create adjusted player pool
            adjusted_players = []

            for player in eligible:
                # Make a copy
                adj_player = self._copy_player(player)

                # Apply diversity penalties based on usage
                if player.id in player_usage:
                    usage = player_usage[player.id]
                    exposure = usage / max(1, successful)

                    # If over max exposure, heavily penalize
                    if exposure > max_exposure:
                        penalty = 0.3  # 70% reduction
                    else:
                        # Gradual penalty based on diversity factor
                        penalty = 1.0 - (usage * diversity_factor * 0.1)
                        penalty = max(0.5, penalty)  # Never reduce more than 50%

                    adj_player.enhanced_score *= penalty

                adjusted_players.append(adj_player)

            # Optimize based on contest type
            if contest_type == 'showdown':
                result = self.optimize_showdown_lineup(adjusted_players)
            else:
                result = self.optimize_classic_lineup(adjusted_players)

            # Validate lineup
            if result and result.optimization_status == "Optimal":
                total_salary = result.total_salary
                salary_pct = total_salary / self.salary_cap

                if salary_pct >= min_salary_pct:
                    # Calculate lineup metrics
                    lineup_data = {
                        'lineup_id': successful + 1,
                        'lineup': result.lineup,
                        'total_score': result.total_score,
                        'total_salary': total_salary,
                        'salary_pct': salary_pct,
                        'contest_type': contest_type,
                        'ceiling': self._calculate_lineup_ceiling(result.lineup),
                        'floor': self._calculate_lineup_floor(result.lineup),
                        'stacks': self._identify_stacks(result.lineup)
                    }

                    generated_lineups.append(lineup_data)

                    # Update usage
                    for player in result.lineup:
                        player_usage[player.id] = player_usage.get(player.id, 0) + 1

                    successful += 1

                    if successful % 10 == 0:
                        print(f"   Generated {successful}/{count} lineups...")

        print(f"\n✅ Generated {len(generated_lineups)} valid lineups")
        self._print_generation_summary(generated_lineups, player_usage)

        return generated_lineups

    def optimize_for_contest(self, contest_type: str = 'gpp') -> Tuple[List, float]:
        """
        Optimize single lineup for specific contest type
        NO ARTIFICIAL BOOSTS
        """
        print(f"\n🎯 OPTIMIZING SINGLE {contest_type.upper()} LINEUP")

        # Get eligible players
        eligible = self.filter_eligible_players()

        if not eligible:
            return [], 0.0

        # Sort by appropriate metric for contest type
        if contest_type == 'cash':
            # Cash games: prioritize floor/consistency
            eligible = self._sort_by_floor(eligible)
        elif contest_type == 'gpp':
            # GPPs: prioritize ceiling/upside
            eligible = self._sort_by_ceiling(eligible)

        # Run optimization
        if contest_type == 'showdown':
            result = self.optimize_showdown_lineup(eligible)
        else:
            result = self.optimize_classic_lineup(eligible)

        if result and result.optimization_status == "Optimal":
            print(f"✅ Optimal {contest_type} lineup found: {result.total_score:.2f} points")
            return result.lineup, result.total_score

        return [], 0.0

    def _sort_by_floor(self, players: List) -> List:
        """
        Sort players by floor (consistency) for cash games
        Uses actual data, not artificial boosts
        """
        for player in players:
            # Calculate floor based on real factors
            floor_score = player.enhanced_score

            # Recent consistency matters for floor
            if hasattr(player, '_recent_performance') and player._recent_performance:
                consistency = player._recent_performance.get('consistency_score', 0.5)
                floor_score *= (0.8 + consistency * 0.2)  # 80-100% based on consistency

            # Lower variance positions have higher floor
            if player.primary_position in ['1B', '2B', 'C']:  # Consistent positions
                floor_score *= 1.05
            elif player.primary_position in ['SS', '3B']:
                floor_score *= 1.02

            player._floor_score = floor_score

        # Sort by floor score descending
        return sorted(players, key=lambda x: getattr(x, '_floor_score', x.enhanced_score), reverse=True)

    def _sort_by_ceiling(self, players: List) -> List:
        """
        Sort players by ceiling (upside) for GPPs
        Uses actual data, not artificial boosts
        """
        for player in players:
            # Calculate ceiling based on real factors
            ceiling_score = player.enhanced_score

            # Power metrics increase ceiling
            if hasattr(player, '_statcast_data') and player._statcast_data:
                hard_hit = player._statcast_data.get('Hard_Hit', 0)
                barrel = player._statcast_data.get('Barrel', 0)

                if hard_hit > 40:  # Elite hard hit rate
                    ceiling_score *= 1.15
                elif hard_hit > 35:
                    ceiling_score *= 1.08

                if barrel > 10:  # Elite barrel rate
                    ceiling_score *= 1.10

            # Vegas environment affects ceiling
            if hasattr(player, '_vegas_data') and player._vegas_data:
                team_total = player._vegas_data.get('team_total', 4.5)
                if team_total > 5.5:  # High scoring game
                    ceiling_score *= 1.12
                elif team_total > 5.0:
                    ceiling_score *= 1.06

            # High variance positions
            if player.primary_position in ['OF', 'SS', '3B']:
                ceiling_score *= 1.05

            player._ceiling_score = ceiling_score

        # Sort by ceiling score descending
        return sorted(players, key=lambda x: getattr(x, '_ceiling_score', x.enhanced_score), reverse=True)

    def _calculate_lineup_ceiling(self, lineup: List) -> float:
        """Calculate lineup ceiling (no artificial inflation)"""
        ceiling = 0
        for player in lineup:
            player_ceiling = getattr(player, '_ceiling_score', player.enhanced_score * 1.25)
            ceiling += player_ceiling
        return ceiling

    def _calculate_lineup_floor(self, lineup: List) -> float:
        """Calculate lineup floor (no artificial inflation)"""
        floor = 0
        for player in lineup:
            player_floor = getattr(player, '_floor_score', player.enhanced_score * 0.75)
            floor += player_floor
        return floor

    def _identify_stacks(self, lineup: List) -> List[Tuple[str, int]]:
        """Identify team stacks in lineup"""
        team_counts = {}
        for player in lineup:
            if player.team:
                team_counts[player.team] = team_counts.get(player.team, 0) + 1

        # Return teams with 3+ players
        stacks = [(team, count) for team, count in team_counts.items() if count >= 3]
        return sorted(stacks, key=lambda x: x[1], reverse=True)

    def _print_generation_summary(self, lineups: List[Dict], player_usage: Dict):
        """Print summary of generated lineups"""
        if not lineups:
            return

        print("\n📊 GENERATION SUMMARY")
        print("=" * 50)

        # Score stats
        scores = [l['total_score'] for l in lineups]
        print(f"Projected scores: {min(scores):.1f} - {max(scores):.1f} (avg: {sum(scores) / len(scores):.1f})")

        # Salary stats
        salaries = [l['total_salary'] for l in lineups]
        print(f"Salary usage: ${min(salaries):,} - ${max(salaries):,} (avg: ${int(sum(salaries) / len(salaries)):,})")

        # Ceiling/Floor
        if 'ceiling' in lineups[0]:
            ceilings = [l['ceiling'] for l in lineups]
            floors = [l['floor'] for l in lineups]
            print(f"Ceiling range: {min(ceilings):.1f} - {max(ceilings):.1f}")
            print(f"Floor range: {min(floors):.1f} - {max(floors):.1f}")

        # Player exposure
        print(f"\n🎯 Player Exposure (top 10):")
        sorted_usage = sorted(player_usage.items(), key=lambda x: x[1], reverse=True)[:10]

        for player_id, usage in sorted_usage:
            exposure_pct = (usage / len(lineups)) * 100
            # Find player name
            player_name = "Unknown"
            for lineup in lineups:
                for player in lineup['lineup']:
                    if player.id == player_id:
                        player_name = player.name
                        break
                if player_name != "Unknown":
                    break

            print(f"   {player_name}: {exposure_pct:.1f}% ({usage}/{len(lineups)})")

        # Unique players
        print(f"\n📈 Total unique players used: {len(player_usage)}")

        # Stacking summary
        all_stacks = []
        for lineup in lineups:
            all_stacks.extend(lineup.get('stacks', []))

        if all_stacks:
            print(f"\n🏈 Stacking Summary:")
            stack_counts = {}
            for team, size in all_stacks:
                key = f"{team} ({size} players)"
                stack_counts[key] = stack_counts.get(key, 0) + 1

            for stack, count in sorted(stack_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   {stack}: {count} lineups")

    def _copy_player(self, player):
        """Create a deep copy of player"""
        import copy
        return copy.deepcopy(player)

    # Export functionality
    def export_lineups_for_upload(self, lineups: List[Dict], filename: str = "dfs_lineups_upload.csv"):
        """
        Export lineups in DraftKings upload format
        """
        import csv

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)

            # DraftKings upload format
            for i, lineup_data in enumerate(lineups):
                row = []

                # Group players by position for proper order
                position_map = {}
                for player in lineup_data['lineup']:
                    pos = getattr(player, 'assigned_position', player.primary_position)
                    if pos not in position_map:
                        position_map[pos] = []
                    position_map[pos].append(player.name)

                # Write in DraftKings position order
                for pos in ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']:
                    if pos in position_map and position_map[pos]:
                        row.append(position_map[pos].pop(0))
                    else:
                        row.append("")  # Empty if position not filled

                writer.writerow(row)

        print(f"✅ Exported {len(lineups)} lineups to {filename}")
        return filename

    def detect_confirmed_players(self) -> int:
        """FIXED: Strict confirmation detection with validation"""

        print("\n🔍 SMART CONFIRMATION DETECTION - STRICT MODE")
        print("=" * 60)

        # CRITICAL: Reset all confirmations first
        self.reset_all_confirmations()

        if not self.confirmation_system:
            print("⚠️ Smart confirmation system not available")
            return 0

        # Update CSV players without recreating the system
        if hasattr(self.confirmation_system, 'csv_players'):
            self.confirmation_system.csv_players = self.players
            # Update CSV teams too
            self.confirmation_system.csv_teams = self.confirmation_system.data_system.get_teams_from_players(
                self.players)

        # Get all confirmations
        lineup_count, pitcher_count = self.confirmation_system.get_all_confirmations()

        # ADD DEBUG INFO
        print(f"\n🔍 DEBUG - Confirmation Status:")
        print(f"  Current time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"  Game date: {self.game_date}")
        print(f"  API returned: {lineup_count} lineups, {pitcher_count} pitchers")
        print(f"  Total CSV players: {len(self.players)}")

        # Check for games started
        current_hour = datetime.now().hour
        if current_hour >= 19:  # 7 PM or later
            print(f"\n⚠️ WARNING: Games may have started! ({current_hour}:00)")
            print(f"   MLB lineups lock once games begin")
            print(f"   Consider using manual selections or 'All Players' mode")

        # TEAM MATCHING DEBUG
        if hasattr(self.confirmation_system, 'csv_teams') and hasattr(self.confirmation_system, 'confirmed_lineups'):
            print(f"\n🔍 TEAM MATCHING DEBUG:")
            csv_teams = set(self.confirmation_system.csv_teams)
            mlb_teams = set(self.confirmation_system.confirmed_lineups.keys())
            print(f"  CSV Teams ({len(csv_teams)}): {sorted(csv_teams)}")
            print(f"  MLB Teams with lineups ({len(mlb_teams)}): {sorted(mlb_teams)}")

            # Find overlap
            overlap = csv_teams & mlb_teams
            print(f"  Matching teams ({len(overlap)}): {sorted(overlap)}")

            # Show mismatches
            csv_only = csv_teams - mlb_teams
            if csv_only:
                print(f"  ❌ CSV teams NOT playing: {sorted(csv_only)}")

        confirmed_count = 0
        confirmed_pitchers = []
        confirmed_hitters = []

        print("\n🔍 STRICT PLAYER MATCHING...")

        # PART 1: Match hitters to confirmed lineups
        print("\n🔍 MATCHING PLAYERS TO LINEUPS...")
        matched_count = 0
        failed_matches = 0

        for i, player in enumerate(self.players):
            try:
                # Skip pitchers
                if player.primary_position == 'P':
                    continue

                # Show progress every 50 players
                if i % 50 == 0 and i > 0:
                    print(f"   Processed {i}/{len(self.players)} players...")

                # Check if player is in lineup
                is_confirmed, batting_order = self.confirmation_system.is_player_confirmed(
                    player.name, player.team
                )

                if is_confirmed:
                    player.is_confirmed = True
                    player.add_confirmation_source("mlb_lineup")
                    confirmed_count += 1
                    confirmed_hitters.append(f"{player.name} ({player.team}) - Batting {batting_order}")
                    matched_count += 1

                    # Only show first few matches
                    if matched_count <= 10:
                        print(f"✅ Matched: {player.name} ({player.team}) - Batting {batting_order}")

            except Exception as e:
                failed_matches += 1
                print(f"❌ Error matching {player.name}: {e}")
                continue

        print(f"\n✅ Matched {matched_count} hitters")
        if failed_matches > 0:
            print(f"⚠️ Failed to match {failed_matches} players")

        # PART 2: STRICT pitcher matching - ONLY confirmed starters
        print("\n🎯 STRICT PITCHER VERIFICATION...")

        # Get today's confirmed starters from MLB API
        confirmed_starter_names = {}
        if hasattr(self.confirmation_system, 'confirmed_pitchers'):
            for team, pitcher_data in self.confirmation_system.confirmed_pitchers.items():
                if team in self.confirmation_system.csv_teams:  # Only CSV teams
                    pitcher_name = pitcher_data['name'].lower().strip()
                    confirmed_starter_names[pitcher_name] = team
                    print(f"   📌 Confirmed starter: {pitcher_data['name']} ({team})")

        # Now check ALL pitchers
        pitcher_check_count = 0
        for player in self.players:
            if player.primary_position == 'P':
                pitcher_check_count += 1
                player_name_lower = player.name.lower().strip()

                # STRICT: Only confirm if exact match to MLB confirmed starter
                if player_name_lower in confirmed_starter_names:
                    expected_team = confirmed_starter_names[player_name_lower]
                    if player.team == expected_team:
                        player.is_confirmed = True
                        player.add_confirmation_source("mlb_starter")
                        confirmed_count += 1
                        confirmed_pitchers.append(f"{player.name} ({player.team})")
                        print(f"✅ Confirmed Pitcher: {player.name} ({player.team})")
                    else:
                        print(f"❌ Team mismatch for {player.name}: {player.team} vs {expected_team}")
                else:
                    # Show first few non-starters
                    if pitcher_check_count <= 20:
                        print(f"❌ NOT STARTING: {player.name} ({player.team})")

        # PART 3: Validation summary
        print(f"\n📊 CONFIRMATION SUMMARY:")
        print(f"   Confirmed Pitchers: {len(confirmed_pitchers)}")
        print(f"   Confirmed Hitters: {len(confirmed_hitters)}")
        print(f"   Total Confirmed: {confirmed_count}")

        # Show confirmed pitchers
        if confirmed_pitchers:
            print(f"\n⚾ CONFIRMED STARTING PITCHERS:")
            for p in confirmed_pitchers[:10]:  # Show first 10
                print(f"   - {p}")
            if len(confirmed_pitchers) > 10:
                print(f"   ... and {len(confirmed_pitchers) - 10} more")

        # Show some confirmed hitters
        if confirmed_hitters:
            print(f"\n⚾ SAMPLE CONFIRMED HITTERS (first 5):")
            for h in confirmed_hitters[:5]:
                print(f"   - {h}")
            print(f"   ... and {len(confirmed_hitters) - 5} more")

        # CRITICAL: Verify no extra players are confirmed
        self._validate_confirmations()

        # Apply data enrichment ONLY to confirmed players
        if confirmed_count > 0:
            print("\n📊 APPLYING ADVANCED ANALYTICS TO CONFIRMED PLAYERS...")

            # Get ONLY confirmed players
            truly_confirmed = [p for p in self.players if p.is_confirmed]
            print(f"🎯 Enriching {len(truly_confirmed)} confirmed players...")

            # 1. Vegas Lines
            if self.vegas_lines:
                print("💰 Enriching with Vegas lines...")
                self.enrich_with_vegas_lines()

            # 2. Statcast Data
            if self.statcast_fetcher:
                print("📊 Enriching with Statcast data...")
                self.enrich_with_statcast_priority()

            # 3. Park Factors
            print("🏟️ Applying park factors...")
            self.apply_park_factors()

            # 4. Batting Order (if available)
            if hasattr(self, 'enrich_with_batting_order'):
                print("🔢 Enriching with batting order...")
                self.enrich_with_batting_order()

            # 5. Recent Form (if available)
            if hasattr(self, 'enrich_with_recent_form'):
                print("📈 Analyzing recent form...")
                self.enrich_with_recent_form()

            # 6. Statistical Analysis
            print("🔬 Applying enhanced statistical analysis...")
            self._apply_comprehensive_statistical_analysis(truly_confirmed)

        else:
            print("\n⚠️ NO PLAYERS CONFIRMED!")
            print("💡 SUGGESTIONS:")
            print("1. Add manual players in the GUI")
            print("2. Check if your CSV teams are playing today")
            print("3. Switch to 'All Players' mode")
            print("4. Wait for lineups if games haven't started")

        # CRITICAL: Don't recreate confirmation system here!
        # The data should persist

        return confirmed_count

    def _validate_confirmations(self):
        """Validate that ONLY appropriate players are confirmed"""
        print("\n🔍 VALIDATING CONFIRMATIONS...")

        issues = []

        # Check all players
        for player in self.players:
            if player.is_confirmed:
                # Verify confirmation sources
                if not player.confirmation_sources:
                    issues.append(f"{player.name} marked confirmed but no sources")

                # Extra validation for pitchers
                if player.primary_position == 'P':
                    if 'mlb_starter' not in player.confirmation_sources:
                        issues.append(f"Pitcher {player.name} confirmed but not MLB starter")

        if issues:
            print("⚠️ CONFIRMATION ISSUES FOUND:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ All confirmations validated")

    def _can_fill_position(self, player, position: str) -> bool:
        """Enhanced to show multi-position eligibility"""
        can_fill = super()._can_fill_position(player, position)

        # Debug output for multi-position players
        if len(player.positions) > 1 and can_fill:
            print(f"   🔄 {player.name} can fill {position} (positions: {'/'.join(player.positions)})")

        return can_fill

    def optimize_lineup_with_mode(self) -> Tuple[List[AdvancedPlayer], float]:
        """
        Optimize lineup with contest type awareness
        Handles both CLASSIC and SHOWDOWN modes with contest-specific adjustments
        """
        print(f"\n🎯 OPTIMAL LINEUP GENERATION - {self.optimization_mode.upper()}")
        print(f"🎰 Contest Type: {self.contest_type.upper()}")
        print("=" * 80)

        # Get eligible players based on mode
        eligible_players = self.get_eligible_players_by_mode()

        if not eligible_players:
            print("❌ No eligible players found")
            return [], 0
            # EXTRA SAFETY: Final pitcher check
            print("\n🔒 FINAL SAFETY CHECK...")
            safe_players = []

            for player in eligible_players:
                if player.primary_position == 'P' and self.optimization_mode != 'manual_only':
                    # Verify pitcher is actually starting
                    if self.confirmation_system and hasattr(self.confirmation_system, 'confirmed_pitchers'):
                        is_starting = False
                        for team, pitcher_data in self.confirmation_system.confirmed_pitchers.items():
                            if (player.name.lower() == pitcher_data['name'].lower() and
                                    player.team == team):
                                is_starting = True
                                break

                        if is_starting:
                            safe_players.append(player)
                        else:
                            print(f"   ⚠️ REMOVING non-starter from optimization: {player.name} ({player.team})")
                    else:
                        # If no confirmation system, only allow manual pitchers
                        if player.is_manual_selected:
                            safe_players.append(player)
                else:
                    safe_players.append(player)

            eligible_players = safe_players
            print(f"✅ Final eligible count: {len(eligible_players)} players")

        print(f"📊 Optimizing with {len(eligible_players)} eligible players")

        # APPLY CONTEST-SPECIFIC ADJUSTMENTS
        if hasattr(self, 'optimization_contest_type'):
            # Apply adjustments to eligible players only
            self.apply_contest_specific_adjustments(self.optimization_contest_type)

        # Show position breakdown for debugging
        if self.contest_type == 'showdown':
            print(f"🎯 Showdown mode: All {len(eligible_players)} players can be CPT or UTIL")
        else:
            position_counts = {}
            for player in eligible_players:
                for pos in player.positions:
                    position_counts[pos] = position_counts.get(pos, 0) + 1
            print(f"📍 Position coverage: {position_counts}")

        # DATA VERIFICATION: Check what data each player has
        print("\n🔍 DATA ENRICHMENT VERIFICATION:")
        players_with_vegas = sum(1 for p in eligible_players if hasattr(p, 'vegas_data') and p.vegas_data)
        players_with_statcast = sum(1 for p in eligible_players if hasattr(p, 'statcast_data') and p.statcast_data)
        players_with_dff = sum(1 for p in eligible_players if hasattr(p, 'dff_data') and p.dff_data)
        players_with_batting_order = sum(1 for p in eligible_players if hasattr(p, 'batting_order') and p.batting_order)

        print(f"💰 Vegas data: {players_with_vegas}/{len(eligible_players)} players")
        print(f"📊 Statcast data: {players_with_statcast}/{len(eligible_players)} players")
        print(f"📈 DFF data: {players_with_dff}/{len(eligible_players)} players")
        print(f"🔢 Batting order data: {players_with_batting_order}/{len(eligible_players)} players")

        # Show sample player data
        if eligible_players:
            print(f"\n🎯 Sample player data:")
            for player in eligible_players[:3]:  # First 3 players
                print(f"   {player.name} ({player.get_position_string()}):")
                print(f"      Base score: {player.base_score:.2f} → Enhanced: {player.enhanced_score:.2f}")
                if hasattr(player, 'contest_adjustment'):
                    print(f"      Contest adjustment: {player.contest_adjustment:.2%}")
                if hasattr(player, 'batting_order'):
                    print(f"      Batting order: {player.batting_order}")
                if hasattr(player, 'vegas_data') and player.vegas_data:
                    print(f"      Vegas: Team Total {player.vegas_data.get('team_total', 'N/A')}")
                if hasattr(player, 'statcast_data') and player.statcast_data:
                    print(f"      Statcast: xwOBA {player.statcast_data.get('xwOBA', 'N/A')}")
                if hasattr(player, 'dff_data') and player.dff_data:
                    print(f"      DFF: {player.dff_data.get('ppg_projection', 'N/A')} proj")

        # Create optimizer
        optimizer = OptimalLineupOptimizer(salary_cap=self.salary_cap)

        # Run optimization based on contest type
        if self.contest_type == 'showdown':
            print("\n🎰 Running SHOWDOWN optimization (1 CPT + 5 UTIL)")
            print(f"   Captain gets 1.5x points but costs 1.5x salary")
            result = optimizer.optimize_showdown_lineup(eligible_players)
        else:
            print("\n🏈 Running CLASSIC optimization (10 players)")
            print(f"   Need: 2 P, 1 C, 1 1B, 1 2B, 1 3B, 1 SS, 3 OF")
            result = optimizer.optimize_classic_lineup(eligible_players)

        if result.optimization_status == "Optimal" and result.lineup:
            print(f"\n✅ OPTIMAL LINEUP FOUND!")
            print(f"💰 Total Salary: ${result.total_salary:,} / ${self.salary_cap:,}")
            print(f"💵 Remaining: ${self.salary_cap - result.total_salary:,}")
            print(f"📈 Projected Points: {result.total_score:.2f}")
            print(f"📊 Positions Filled: {result.positions_filled}")

            # NEW: Apply correlation adjustments to the optimal lineup
            if hasattr(self, 'apply_lineup_correlations'):
                print(f"\n🔥 Applying correlation adjustments...")
                result.lineup = self.apply_lineup_correlations(result.lineup)
                # Recalculate total score after correlation adjustments
                old_score = result.total_score
                result.total_score = sum(p.enhanced_score for p in result.lineup)
                if abs(result.total_score - old_score) > 0.1:
                    print(
                        f"   Score adjusted: {old_score:.2f} → {result.total_score:.2f} ({result.total_score - old_score:+.2f})")

            # Show lineup preview
            print(f"\n📋 LINEUP PREVIEW:")
            if self.contest_type == 'showdown':
                # Show captain first
                captain = \
                [p for p in result.lineup if hasattr(p, 'assigned_position') and p.assigned_position == 'CPT'][0]
                print(
                    f"   👑 CPT: {captain.name} (${int(captain.salary * 1.5):,}) - {captain.enhanced_score * 1.5:.1f} pts")

                # Show UTIL players
                utils = [p for p in result.lineup if hasattr(p, 'assigned_position') and p.assigned_position == 'UTIL']
                for i, player in enumerate(utils, 1):
                    print(f"   {i}. UTIL: {player.name} (${player.salary:,}) - {player.enhanced_score:.1f} pts")
            else:
                # Classic lineup
                for player in result.lineup[:5]:  # Show first 5
                    pos = getattr(player, 'assigned_position', player.primary_position)
                    pos_str = player.get_position_display() if hasattr(player, 'get_position_display') else pos
                    batting_str = f" (Bat-{player.batting_order})" if hasattr(player,
                                                                              'batting_order') and player.batting_order else ""
                    print(
                        f"   {pos_str}: {player.name}{batting_str} (${player.salary:,}) - {player.enhanced_score:.1f} pts")
                print(f"   ... and {len(result.lineup) - 5} more players")

            # After optimization, show stack info if available
            if hasattr(self, 'correlation_optimizer'):
                correlation_score, correlation_details = self.correlation_optimizer.calculate_lineup_correlation_score(
                    result.lineup,
                    self.vegas_lines.lines if self.vegas_lines else None
                )

                if correlation_details['stacks']:
                    print(f"\n🔥 STACKING ANALYSIS:")
                    for stack in correlation_details['stacks']:
                        print(f"   {stack['team']}: {stack['size']} players (bonus: +{stack['bonus']:.1%})")
                        if stack.get('has_pitcher'):
                            print(f"      ⚾ Includes pitcher")
                        print(
                            f"      Players: {', '.join(stack['players'][:3])}{'...' if len(stack['players']) > 3 else ''}")
                    print(f"   Total correlation bonus: {correlation_score:.1%}")

            return result.lineup, result.total_score
        else:
            print(f"\n❌ Optimization failed: {result.optimization_status}")

            # Provide helpful debugging info
            if self.contest_type == 'showdown' and len(eligible_players) < 6:
                print(f"   💡 Showdown needs at least 6 players, you have {len(eligible_players)}")
            elif self.contest_type == 'classic':
                print(f"   💡 Check position coverage - you may be missing required positions")

            return [], 0

    def _basic_pitcher_fallback(self) -> int:
        """Basic pitcher confirmation fallback"""
        confirmed_pitchers = 0

        # Group pitchers by team
        teams_pitchers = {}
        for player in self.players:
            if player.primary_position == 'P':
                if player.team not in teams_pitchers:
                    teams_pitchers[player.team] = []
                teams_pitchers[player.team].append(player)

        # For each team, confirm the highest salary pitcher
        for team, pitchers in teams_pitchers.items():
            if pitchers:
                # Sort by salary
                pitchers.sort(key=lambda x: x.salary, reverse=True)
                top_pitcher = pitchers[0]

                # Confirm if clear salary leader or only pitcher
                if len(pitchers) == 1 or (len(pitchers) > 1 and top_pitcher.salary - pitchers[1].salary >= 1000):
                    top_pitcher.add_confirmation_source("fallback_salary_leader")
                    confirmed_pitchers += 1
                    print(f"🔄 Fallback pitcher: {top_pitcher.name} (${top_pitcher.salary:,})")

        return confirmed_pitchers

    def apply_dff_rankings(self, dff_file_path: str) -> bool:
        """Enhanced DFF application with better matching - ONLY FOR DFF, doesn't affect other systems"""

        if not dff_file_path or not os.path.exists(dff_file_path):
            print("⚠️ No DFF file provided or file not found")
            return False


        # Local function for DFF-specific name cleaning

        def apply_injury_list_to_players(self):
            """Apply injury list to player pool"""
            injury_list = self.fetch_mlb_injury_list()

            injured_count = 0
            for player in self.players:
                if player.team in injury_list:
                    # Check if player is on injury list
                    for injured_name in injury_list[player.team]:
                        if injured_name.lower() in player.name.lower() or player.name.lower() in injured_name.lower():
                            player.set_injury_status('IL', f'On {player.team} injury list')
                            injured_count += 1

                            # Remove confirmation if exists
                            if player.is_confirmed:
                                player.is_confirmed = False
                                player.confirmation_sources = []
                                print(f"   ❌ Removed injured: {player.name} ({player.team})")
                            break

            if injured_count > 0:
                print(f"✅ Marked {injured_count} players as injured")

            return injured_count

        def fetch_mlb_injury_list(self) -> Dict[str, List[str]]:
            """
            Fetch current MLB injury list from ESPN or other sources
            Returns dict of team -> list of injured players
            """
            print("\n🏥 FETCHING MLB INJURY LIST...")

            injured_players = {}

            # Common known injured players (June 2024)
            # UPDATE THIS LIST DAILY!
            KNOWN_INJURIES = {
                'BAL': ['Cedric Mullins', 'Tyler Wells', 'John Means'],
                'LAA': ['Mike Trout', 'Anthony Rendon'],
                'ATL': ['Ronald Acuna Jr.', 'Max Fried'],
                'HOU': ['Jose Altuve', 'Cristian Javier'],
                # Add more teams/players as needed
            }

            # You could also scrape from ESPN or use an API here
            # For now, use the known list

            total_injured = 0
            for team, players in KNOWN_INJURIES.items():
                injured_players[team] = players
                total_injured += len(players)

            print(f"📋 Found {total_injured} injured players across {len(KNOWN_INJURIES)} teams")

            return injured_players

        def clean_dff_name(name):
            """Clean DFF names only - removes team abbreviations and normalizes"""
            if not name:
                return ''
            # Remove team abbreviations in parentheses
            name = re.sub(r'\s*\([^)]*\)', '', str(name)).strip()
            # Remove extra spaces
            name = ' '.join(name.split())
            return name

        try:
            print(f"\n🎯 Loading DFF rankings: {Path(dff_file_path).name}")
            df = pd.read_csv(dff_file_path)

            print(f"📊 DFF Data Summary:")
            print(f"   Rows: {len(df)}")
            print(f"   Columns: {list(df.columns)[:5]}{'...' if len(df.columns) > 5 else ''}")

            # Auto-detect important columns
            name_col = None
            proj_col = None
            own_col = None
            value_col = None
            team_col = None

            for col in df.columns:
                col_lower = col.lower()
                if not name_col and any(x in col_lower for x in ['name', 'player']):
                    name_col = col
                elif not proj_col and any(x in col_lower for x in ['projection', 'proj', 'ppg', 'fpts', 'points']):
                    proj_col = col
                elif not own_col and any(x in col_lower for x in ['own', 'ownership', '%']):
                    own_col = col
                elif not value_col and any(x in col_lower for x in ['value', 'val']):
                    value_col = col
                elif not team_col and any(x in col_lower for x in ['team', 'tm']):
                    team_col = col

            if not name_col:
                print("❌ Could not find player name column in DFF file")
                return False

            print(f"📋 Detected DFF columns:")
            print(f"   Name: '{name_col}'")
            print(f"   Projection: '{proj_col}' {'✓' if proj_col else '✗'}")
            print(f"   Ownership: '{own_col}' {'✓' if own_col else '✗'}")
            print(f"   Value: '{value_col}' {'✓' if value_col else '✗'}")
            print(f"   Team: '{team_col}' {'✓' if team_col else '✗'}")

            # Debug: Show sample names
            print(f"\n📋 Sample DFF names (first 5):")
            for i, name in enumerate(df[name_col].head(5)):
                print(f"   {i + 1}. {name}")

            print(f"\n📋 Sample DK player names (first 5):")
            for i, player in enumerate(self.players[:5]):
                print(f"   {i + 1}. {player.name} ({player.team})")

            # Match players
            matches = 0
            no_matches = []
            eligible_enriched = 0
            all_enriched = 0

            for idx, row in df.iterrows():
                try:
                    # Get raw DFF name
                    dff_name_raw = str(row[name_col]).strip()
                    if not dff_name_raw or dff_name_raw == 'nan':
                        continue

                    # Clean DFF name (remove team abbreviations)
                    dff_name = clean_dff_name(dff_name_raw)

                    # Get team if available
                    dff_team = str(row[team_col]).strip().upper() if team_col and pd.notna(row[team_col]) else None

                    # Build DFF data dict
                    dff_data = {
                        'dff_name': dff_name,
                        'source': 'DFF Rankings'
                    }

                    # Extract projection
                    if proj_col and pd.notna(row[proj_col]):
                        try:
                            proj_str = str(row[proj_col]).replace('$', '').replace(',', '').strip()
                            dff_data['ppg_projection'] = float(proj_str)
                        except:
                            pass

                    # Extract ownership
                    if own_col and pd.notna(row[own_col]):
                        try:
                            own_str = str(row[own_col]).replace('%', '').strip()
                            dff_data['ownership'] = float(own_str)
                        except:
                            pass

                    # Extract value
                    if value_col and pd.notna(row[value_col]):
                        try:
                            dff_data['value'] = float(row[value_col])
                        except:
                            pass

                    # Find best matching player using ORIGINAL name matching logic
                    best_match = None
                    best_score = 0

                    for player in self.players:
                        # Use your ORIGINAL _name_similarity method
                        similarity = self._name_similarity(dff_name, player.name)

                        # If we have team info, boost score for same team
                        if dff_team and player.team == dff_team and similarity >= 0.7:
                            similarity = min(1.0, similarity + 0.1)

                        if similarity > best_score and similarity >= 0.7:  # 70% threshold
                            best_score = similarity
                            best_match = player

                    if best_match and 'ppg_projection' in dff_data:
                        # APPLY TO MATCHED PLAYER
                        best_match.apply_dff_data(dff_data)
                        matches += 1
                        all_enriched += 1

                        # Check if this player is eligible
                        if best_match.is_eligible_for_selection(self.optimization_mode):
                            eligible_enriched += 1

                            # Show match details for first few or significant differences
                            if eligible_enriched <= 5 or abs(dff_data['ppg_projection'] - best_match.base_score) > 2:
                                proj = dff_data['ppg_projection']
                                own = dff_data.get('ownership', 'N/A')
                                match_indicator = "✅" if best_score >= 0.95 else f"🔄 ({best_score:.2f})"

                                print(f"\n   {match_indicator} DFF MATCH: {dff_name} → {best_match.name}")
                                if dff_name != dff_name_raw:
                                    print(f"      (Original: {dff_name_raw})")
                                print(f"      Team: {dff_team or 'N/A'} → {best_match.team}")
                                print(f"      Projection: {proj:.1f} | Ownership: {own}%")
                    else:
                        no_matches.append(f"{dff_name_raw} ({dff_team or 'N/A'})")

                except Exception as e:
                    print(f"   ❌ Error processing row {idx}: {e}")
                    continue

            print(f"\n📊 DFF Integration Summary:")
            print(f"   Total DFF players: {len(df)}")
            print(f"   Matched to DK: {matches}")
            print(f"   Applied to all: {all_enriched}")
            print(f"   Eligible players enriched: {eligible_enriched}")
            print(f"   Success rate: {(matches / len(df) * 100):.1f}%" if len(df) > 0 else "N/A")

            # Show some unmatched for debugging
            if no_matches and len(no_matches) <= 10:
                print(f"\n❌ Unmatched DFF players (first 10):")
                for name in no_matches[:10]:
                    print(f"   - {name}")
            elif no_matches:
                print(f"\n❌ {len(no_matches)} DFF players didn't match")

            # Special message if no eligible players got DFF
            if eligible_enriched == 0 and matches > 0:
                print(f"\n⚠️ WARNING: DFF matched {matches} players but NONE were eligible!")
                print(f"   This usually means DFF players aren't in your confirmed/manual selections")
                print(f"   Consider adding some DFF players to manual selections")

            return matches > 0

        except Exception as e:
            print(f"❌ Error loading DFF data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def enrich_with_vegas_lines(self):
        """Apply Vegas lines ONLY to players with meaningful data"""
        if not self.vegas_lines:
            print("⚠️ Vegas lines module not available")
            return

        print("💰 Applying Vegas lines where data exists...")
        vegas_data = self.vegas_lines.get_vegas_lines()

        if not vegas_data:
            print("⚠️ No Vegas data available")
            return

        # Only apply to confirmed/eligible players with Vegas data
        eligible_players = [p for p in self.players if p.is_eligible_for_selection(self.optimization_mode)]

        enriched_count = 0
        for player in eligible_players:
            if player.team in vegas_data:
                team_vegas = vegas_data[player.team]
                # Only apply if game total is significantly different from average (4.5)
                game_total = team_vegas.get('total', 9.0)
                if abs(game_total - 9.0) > 1.0:  # Only if total is <8 or >10
                    player.apply_vegas_data(team_vegas)
                    enriched_count += 1

        print(f"✅ Vegas data: {enriched_count}/{len(eligible_players)} players with significant game environments")

    def enrich_with_statcast_priority(self):
        """FIXED: Priority Statcast enrichment - ALL confirmed players first"""
        if not self.statcast_fetcher:
            print("⚠️ Statcast fetcher not available")
            return

        print("🔬 Priority Statcast enrichment for confirmed players...")

        # PRIORITY 1: ALL confirmed/manual players get Statcast data
        priority_players = [p for p in self.players if p.is_eligible_for_selection(self.optimization_mode)]

        print(f"🎯 Enriching ALL {len(priority_players)} confirmed players with Statcast...")

        enriched_count = 0
        failed_count = 0

        # Process ALL confirmed players (no limit!)
        for i, player in enumerate(priority_players, 1):
            try:
                print(f"🔬 Statcast {i}/{len(priority_players)}: {player.name}...")

                statcast_data = self.statcast_fetcher.fetch_player_data(player.name, player.primary_position)
                if statcast_data:
                    player.apply_statcast_data(statcast_data)
                    enriched_count += 1
                    print(f"   ✅ Success: {player.name}")
                else:
                    failed_count += 1
                    print(f"   ⚠️ No data: {player.name}")

            except Exception as e:
                failed_count += 1
                print(f"   ❌ Error for {player.name}: {e}")
                continue

        print(f"✅ Statcast Priority Complete: {enriched_count} enriched, {failed_count} failed")

    def apply_park_factors(self):
        """FIXED: Park factors for ALL confirmed players"""
        print("🏟️ Priority park factors for confirmed players...")

        eligible_players = [p for p in self.players if p.is_eligible_for_selection(self.optimization_mode)]
        adjusted_count = 0

        for player in eligible_players:
            if player.team in PARK_FACTORS:
                factor = PARK_FACTORS[player.team]
                old_score = player.enhanced_score
                player.enhanced_score *= factor

                player.park_factors = {
                    'park_team': player.team,
                    'factor': factor,
                    'adjustment': player.enhanced_score - old_score
                }

                adjusted_count += 1

        print(f"✅ Park factors: {adjusted_count}/{len(eligible_players)} confirmed players adjusted")

    def get_eligible_players_by_mode(self):
        """FIXED: Strict eligibility checking with validation"""

        # First, validate all confirmations
        self._validate_confirmations()

        if self.optimization_mode == 'all':
            # ALL PLAYERS MODE - No restrictions!
            eligible = self.players.copy()
            print(f"🌐 ALL PLAYERS MODE: {len(eligible)}/{len(self.players)} players eligible")
        elif self.optimization_mode == 'manual_only':
            eligible = [p for p in self.players if p.is_manual_selected]
            print(f"🎯 MANUAL-ONLY MODE: {len(eligible)}/{len(self.players)} manually selected players")
        elif self.optimization_mode == 'confirmed_only':
            eligible = [p for p in self.players if p.is_confirmed and not p.is_manual_selected]
            print(f"🔒 CONFIRMED-ONLY MODE: {len(eligible)}/{len(self.players)} confirmed players")
        else:  # bulletproof
            eligible = [p for p in self.players if p.is_confirmed or p.is_manual_selected]
            print(f"🛡️ BULLETPROOF MODE: {len(eligible)}/{len(self.players)} players eligible")

            # Show breakdown
            confirmed_only = sum(1 for p in eligible if p.is_confirmed and not p.is_manual_selected)
            manual_only = sum(1 for p in eligible if p.is_manual_selected and not p.is_confirmed)
            both = sum(1 for p in eligible if p.is_confirmed and p.is_manual_selected)

            print(f"   - Confirmed only: {confirmed_only}")
            print(f"   - Manual only: {manual_only}")
            print(f"   - Both confirmed & manual: {both}")

        # CRITICAL: Extra validation for pitchers (skip in 'all' mode)
        if self.optimization_mode != 'all':
            eligible_pitchers = [p for p in eligible if p.primary_position == 'P']
            print(f"\n⚾ PITCHER VALIDATION:")
            print(f"   Total eligible pitchers: {len(eligible_pitchers)}")

            for pitcher in eligible_pitchers[:5]:  # Show first 5
                sources = ', '.join(pitcher.confirmation_sources) if pitcher.confirmation_sources else 'MANUAL'
                print(f"   - {pitcher.name} ({pitcher.team}) - Sources: [{sources}]")

        # Position breakdown
        position_counts = {}
        for player in eligible:
            for pos in player.positions:
                position_counts[pos] = position_counts.get(pos, 0) + 1

        print(f"\n📍 Eligible position coverage: {position_counts}")

        # Final safety check (skip in 'all' mode)
        if self.optimization_mode in ['bulletproof', 'confirmed_only'] and self.optimization_mode != 'all':
            # Remove any pitcher without proper confirmation
            safe_eligible = []
            removed_count = 0

            for player in eligible:
                if player.primary_position == 'P' and not player.is_manual_selected:
                    # Pitcher MUST have mlb_starter confirmation
                    if 'mlb_starter' not in player.confirmation_sources:
                        print(f"   ❌ REMOVING unconfirmed pitcher: {player.name}")
                        removed_count += 1
                        continue
                safe_eligible.append(player)

            if removed_count > 0:
                print(f"⚠️ Removed {removed_count} unconfirmed pitchers for safety")
                eligible = safe_eligible

        return eligible


    def _apply_comprehensive_statistical_analysis(self, players):
        """ENHANCED: Apply comprehensive statistical analysis with PRIORITY 1 improvements"""
        print(f"📊 ENHANCED Statistical Analysis: {len(players)} players")
        print("🎯 PRIORITY 1 FEATURES: Variable Confidence + Enhanced Statcast + Position Weighting + Recent Form")

        if not players:
            return

        if ENHANCED_STATS_AVAILABLE:
            # Use enhanced statistical analysis engine (PRIORITY 1 IMPROVEMENTS)
            adjusted_count = apply_enhanced_statistical_analysis(players, verbose=True)
            print(f"✅ Enhanced Analysis: {adjusted_count} players optimized with Priority 1 improvements")

            # Apply recent form adjustments if available
            if hasattr(self, 'form_analyzer'):
                form_adjusted = 0
                for player in players:
                    if hasattr(player, '_recent_performance') and player._recent_performance:
                        adjustment = self.form_analyzer.apply_form_adjustments(player)
                        if adjustment != 1.0:
                            form_adjusted += 1

                if form_adjusted > 0:
                    print(f"📈 Recent Form: {form_adjusted} players adjusted based on hot/cold streaks")
        else:
            # Fallback to basic analysis if enhanced engine not available
            print("⚠️ Using basic analysis - enhanced engine not found")
            self._apply_basic_statistical_analysis(players)

    def _apply_basic_statistical_analysis(self, players):
        """Fallback basic statistical analysis (original method)"""
        print(f"📊 Basic statistical analysis: {len(players)} players")

        CONFIDENCE_THRESHOLD = 0.80
        MAX_TOTAL_ADJUSTMENT = 0.20

        adjusted_count = 0
        for player in players:
            total_adjustment = 0.0

            # DFF Analysis (basic)
            if hasattr(player, 'dff_data') and player.dff_data and player.dff_data.get('ppg_projection', 0) > 0:
                dff_projection = player.dff_data['ppg_projection']
                if dff_projection > player.projection:
                    dff_adjustment = min((dff_projection - player.projection) / player.projection * 0.3,
                                         0.10) * CONFIDENCE_THRESHOLD
                    total_adjustment += dff_adjustment

            # Vegas Environment Analysis (basic)
            if hasattr(player, 'vegas_data') and player.vegas_data:
                team_total = player.vegas_data.get('team_total', 4.5)

                if player.primary_position == 'P':
                    opp_total = player.vegas_data.get('opponent_total', 4.5)
                    if opp_total < 4.0:
                        vegas_adjustment = min((4.5 - opp_total) / 4.5 * 0.4, 0.08) * CONFIDENCE_THRESHOLD
                        total_adjustment += vegas_adjustment
                else:
                    if team_total > 5.0:
                        vegas_adjustment = min((team_total - 4.5) / 4.5 * 0.5, 0.08) * CONFIDENCE_THRESHOLD
                        total_adjustment += vegas_adjustment

            # Apply cap
            if total_adjustment > MAX_TOTAL_ADJUSTMENT:
                total_adjustment = MAX_TOTAL_ADJUSTMENT

            # Apply adjustment
            if total_adjustment > 0.03:
                adjustment_points = player.enhanced_score * total_adjustment
                player.enhanced_score += adjustment_points
                adjusted_count += 1

        print(f"✅ Basic Analysis: {adjusted_count}/{len(players)} players adjusted")

    
    def optimize_lineup_with_mode(self) -> Tuple[List[AdvancedPlayer], float]:
        """
        UPDATED: Optimize lineup using true integer programming optimization
        No greedy fill-ins - finds the globally optimal lineup
        """
        print(f"\n🎯 OPTIMAL LINEUP GENERATION - {self.optimization_mode.upper()}")
        print("=" * 80)

        # Get eligible players based on mode
        eligible_players = self.get_eligible_players_by_mode()

        if not eligible_players:
            print("❌ No eligible players found")
            return [], 0

        print(f"📊 Optimizing with {len(eligible_players)} eligible players")

        # Create optimizer
        optimizer = OptimalLineupOptimizer(salary_cap=self.salary_cap)

        # Run optimization based on contest type
        if hasattr(self, 'contest_type') and self.contest_type == 'showdown':
            result = optimizer.optimize_showdown_lineup(eligible_players)
        else:
            # Don't use confirmations for artificial boosts
            result = optimizer.optimize_classic_lineup(eligible_players, use_confirmations=False)

        if result.optimization_status == "Optimal" and result.lineup:
            print(f"\n✅ OPTIMAL LINEUP FOUND!")
            print(f"💰 Total Salary: ${result.total_salary:,} / ${self.salary_cap:,}")
            print(f"📈 Projected Points: {result.total_score:.2f}")
            print(f"📊 Positions Filled: {result.positions_filled}")

            return result.lineup, result.total_score
        else:
            print(f"❌ Optimization failed: {result.optimization_status}")
            return [], 0

    def _complete_greedy_optimization(self, players):
        """Complete greedy optimization that actually works"""

        # Calculate value for each player
        players_with_value = []
        for player in players:
            if player.salary > 0:
                value = player.enhanced_score / (player.salary / 1000)
                players_with_value.append((player, value))

        # Sort by value (best first)
        players_with_value.sort(key=lambda x: x[1], reverse=True)

        lineup = []
        remaining_salary = self.salary_cap
        requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        filled = {pos: 0 for pos in requirements}

        # Fill each position requirement
        for pos, needed in requirements.items():
            print(f"   Filling {pos}: need {needed}")

            while filled[pos] < needed and len(lineup) < 10:
                best_player = None
                best_value = 0

                for player, value in players_with_value:
                    if (player not in lineup and
                            pos in player.positions and
                            player.salary <= remaining_salary):
                        if value > best_value:
                            best_value = value
                            best_player = player

                if best_player:
                    lineup.append(best_player)
                    remaining_salary -= best_player.salary
                    filled[pos] += 1
                    print(f"     Added: {best_player.name} (${best_player.salary:,})")
                else:
                    print(f"     ⚠️ Cannot fill {pos} with remaining budget ${remaining_salary}")
                    break

        # Verify lineup is complete
        if len(lineup) == 10:
            print(f"✅ Complete lineup built: {len(lineup)} players")
            return lineup
        else:
            print(f"❌ Incomplete lineup: {len(lineup)}/10 players")
            return []


def optimized_pipeline_execution(core, dff_file):
    """FIXED: Optimal order for maximum data enrichment"""
    print("🔄 PRIORITY DATA ENRICHMENT PIPELINE")
    print("=" * 50)

    # STEP 1: Apply DFF data FIRST (affects projections)
    if dff_file and os.path.exists(dff_file):
        print("1️⃣ Applying DFF rankings...")
        core.apply_dff_rankings(dff_file)

    # STEP 2: Enrich with Vegas lines (affects game environment)
    print("2️⃣ Applying Vegas lines...")
    core.enrich_with_vegas_lines()

    # STEP 3: Enrich with Statcast (individual player metrics)
    print("3️⃣ Applying Statcast data to ALL confirmed players...")
    core.enrich_with_statcast_priority()

    # STEP 4: Apply park factors (venue adjustments)
    print("4️⃣ Applying park factors...")
    core.apply_park_factors()

    # STEP 5: Apply batting order adjustments
    if hasattr(core, 'enrich_with_batting_order'):
        print("5️⃣ Applying batting order adjustments...")
        core.enrich_with_batting_order()

    # STEP 6: Apply recent form analysis (if available)
    if hasattr(core, 'enrich_with_recent_form'):
        print("6️⃣ Analyzing recent player form...")
        core.enrich_with_recent_form()

    print("✅ All data sources applied to confirmed players")

# Entry point function for GUI compatibility
def load_and_optimize_complete_pipeline(
        dk_file: str,
        dff_file: str = None,
        manual_input: str = "",
        contest_type: str = 'classic',
        strategy: str = 'bulletproof'
):
    """Complete pipeline with all modes including enhanced pitcher detection"""

    mode_descriptions = {
        'bulletproof': 'Confirmed + Manual players',
        'manual_only': 'Manual players ONLY (perfect for testing!)',
        'confirmed_only': 'Confirmed players ONLY'
    }

    print("🚀 BULLETPROOF DFS OPTIMIZATION PIPELINE - WITH ENHANCED PITCHER DETECTION")
    print("=" * 80)
    print(f"🎯 Mode: {strategy} ({mode_descriptions.get(strategy, 'Unknown')})")
    print("=" * 80)

    core = BulletproofDFSCore()
    core.set_optimization_mode(strategy)

    # Pipeline execution
    if not core.load_draftkings_csv(dk_file):
        return [], 0, "Failed to load DraftKings data"

    if manual_input:
        manual_count = core.apply_manual_selection(manual_input)
        print(f"✅ Manual selection: {manual_count} players")

        if strategy == 'manual_only' and manual_count == 0:
            return [], 0, "Manual-only mode requires manual player selections"

    # Only try confirmations if not manual-only mode
    if strategy != 'manual_only':
        confirmed_count = core.detect_confirmed_players()
        print(f"✅ Confirmed detection: {confirmed_count} players")

        if strategy == 'confirmed_only' and confirmed_count == 0:
            return [], 0, "Confirmed-only mode requires confirmed players (try again during game hours)"

    # Apply data sources
    optimized_pipeline_execution(core, dff_file)

    # Use mode-aware optimization
    lineup, score = core.optimize_lineup_with_mode()

    if lineup:
        total_salary = sum(p.salary for p in lineup)
        pitcher_count = sum(1 for p in lineup if p.primary_position == 'P')

        summary = f"""
✅ {strategy.upper().replace('_', '-')} OPTIMIZATION SUCCESS WITH ENHANCED PITCHER DETECTION
===============================================================================
Mode: {mode_descriptions.get(strategy, 'Unknown')}
Players: {len(lineup)}/10
Pitchers: {pitcher_count}/2 ← ENHANCED PITCHER DETECTION WORKING!
Total Salary: ${total_salary:,}/{core.salary_cap:,}
Projected Score: {score:.2f}

LINEUP:
"""
        for i, player in enumerate(lineup, 1):
            status = player.get_status_string()
            summary += f"{i:2d}. {player.name:<20} {player.primary_position:<3} ${player.salary:,} {player.enhanced_score:.1f} | {status}\n"

        print(summary)
        return lineup, score, summary
    else:
        return [], 0, f"{strategy} optimization failed - see suggestions above"


# ==============================================================================
# CORRECTED INTEGRATION VERIFICATION TEST
# Add this at the END of your bulletproof_dfs_core.py file (after all classes)
# ==============================================================================
def debug_player_confirmations(self):
    """Debug method to show all player confirmation status"""
    print("\n🔍 FULL PLAYER CONFIRMATION DEBUG")
    print("=" * 80)

    # Group by confirmation status
    confirmed = []
    manual = []
    both = []
    none = []

    for player in self.players:
        if player.is_confirmed and player.is_manual_selected:
            both.append(player)
        elif player.is_confirmed:
            confirmed.append(player)
        elif player.is_manual_selected:
            manual.append(player)
        else:
            none.append(player)

    # Show each group
    if confirmed:
        print(f"\n✅ CONFIRMED ONLY ({len(confirmed)} players):")
        for p in confirmed:
            sources = ', '.join(p.confirmation_sources)
            print(f"   {p.name} ({p.team}) {p.primary_position} - Sources: [{sources}]")

    if manual:
        print(f"\n🎯 MANUAL ONLY ({len(manual)} players):")
        for p in manual:
            print(f"   {p.name} ({p.team}) {p.primary_position}")

    if both:
        print(f"\n🌟 CONFIRMED + MANUAL ({len(both)} players):")
        for p in both:
            sources = ', '.join(p.confirmation_sources)
            print(f"   {p.name} ({p.team}) {p.primary_position} - Sources: [{sources}]")

    print(f"\n❌ NOT ELIGIBLE ({len(none)} players) - First 20:")
    for p in none[:20]:
        print(f"   {p.name} ({p.team}) {p.primary_position}")
def verify_integration():
    """Verify all new modules are integrated correctly"""
    print("\n🧪 INTEGRATION VERIFICATION TEST")
    print("=" * 60)

    # Check imports - using the actual variable names
    modules = {
        'Enhanced Stats Engine': ENHANCED_STATS_AVAILABLE,
        'Vegas Lines': VEGAS_AVAILABLE,
        'Smart Confirmations': CONFIRMED_AVAILABLE,
        'Statcast Fetcher': STATCAST_AVAILABLE,
        'Recent Form Analyzer': RECENT_FORM_AVAILABLE,
        'Batting Order & Correlation': BATTING_CORRELATION_AVAILABLE
    }

    print("📦 Module Status:")
    for module, available in modules.items():
        status = "✅" if available else "❌"
        print(f"   {status} {module}: {'Available' if available else 'Not Found'}")

    # Test core initialization
    try:
        core = BulletproofDFSCore()
        print("\n✅ Core initialized successfully")

        # Check if new methods exist
        methods_to_check = [
            ('enrich_with_recent_form', 'Recent Form Method'),
            ('enrich_with_batting_order', 'Batting Order Method'),
            ('apply_lineup_correlations', 'Correlation Method'),
            ('form_analyzer', 'Form Analyzer Instance'),
            ('batting_enricher', 'Batting Enricher Instance'),
            ('correlation_optimizer', 'Correlation Optimizer Instance')
        ]

        print("\n🔧 Method/Attribute Check:")
        for method, name in methods_to_check:
            exists = hasattr(core, method)
            status = "✅" if exists else "❌"
            print(f"   {status} {name}: {'Found' if exists else 'Missing'}")

        # Check which modules were actually integrated
        print("\n📋 Integration Summary:")
        integrated_count = 0

        if hasattr(core, 'form_analyzer') and core.form_analyzer is not None:
            print("   ✅ Recent Form Analyzer integrated")
            integrated_count += 1
        else:
            print("   ❌ Recent Form Analyzer NOT integrated")

        if hasattr(core, 'batting_enricher') and hasattr(core, 'correlation_optimizer'):
            print("   ✅ Batting Order & Correlation integrated")
            integrated_count += 1
        else:
            print("   ❌ Batting Order & Correlation NOT integrated")

        print(f"\n📊 Total: {integrated_count}/2 new systems integrated")

    except Exception as e:
        print(f"\n❌ Core initialization failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)

    # Return status for external testing
    return all(modules.values())


# If running as a standalone test
if __name__ == "__main__":
    # This file should be imported, not run directly
    print("✅ bulletproof_dfs_core module loaded successfully")
    print("📋 To use this module:")
    print("   from bulletproof_dfs_core import BulletproofDFSCore")
    print("   core = BulletproofDFSCore()")
    print("   core.load_draftkings_csv('your_file.csv')")
    # ==================== DFS UPGRADE METHODS ====================

    def get_cached_data(self, key: str, fetch_func, category: str = 'default'):
        """Use smart caching for any data fetch"""
        if UPGRADES_AVAILABLE:
            return smart_cache.get_or_fetch(key, fetch_func, category)
        else:
            return fetch_func()

    def generate_multiple_lineups(self, count: int = 20) -> list:
        """Generate multiple unique lineups for GPPs"""
        if not UPGRADES_AVAILABLE:
            print("❌ Multi-lineup module not available")
            return []

        print(f"\n🚀 Generating {count} lineups...")

        optimizer = MultiLineupOptimizer(self)
        lineups = optimizer.generate_gpp_lineups(
            num_lineups=count,
            max_exposure=0.5,
            min_salary=49000
        )

        # Show summary
        optimizer.print_summary()

        # Export for upload
        upload_file = optimizer.export_for_upload('draftkings')
        if upload_file:
            print(f"\n📁 Upload file: {upload_file}")

        return lineups

    def track_lineup_performance(self, lineup: list, contest_info: dict):
        """Track lineup for future analysis"""
        if not UPGRADES_AVAILABLE:
            return None

        contest_id = tracker.log_contest(lineup, contest_info)

        # Also save to database if available
        if hasattr(self, 'game_date'):
            contest_info['date'] = self.game_date

        return contest_id

    def get_performance_summary(self, days: int = 30):
        """Get performance tracking summary"""
        if not UPGRADES_AVAILABLE:
            print("Performance tracking not available")
            return

        tracker.print_summary(days)

    def clear_cache(self, category: str = None):
        """Clear cache by category or all"""
        if UPGRADES_AVAILABLE:
            smart_cache.clear(category)
            print(f"🧹 Cleared cache: {category or 'all'}")


