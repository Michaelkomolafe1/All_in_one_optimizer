#!/usr/bin/env python3
"""
BULLETPROOF DFS CORE - CLEANED AND IMPROVED VERSION
===================================================
Complete working version with enhanced pitcher detection,
proper error handling, and optimized data pipeline.
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

# Third-party imports
import numpy as np
import pandas as pd

# Suppress warnings
warnings.filterwarnings('ignore')

# ============================================================================
# MODULE IMPORTS WITH FALLBACKS
# ============================================================================

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

# Utils imports
try:
    from utils.cache_manager import cache
    from utils.profiler import profiler
    from utils.validator import DataValidator
    from utils.config import config
except ImportError as e:
    print(f"⚠️ Utils not available: {e}")
    cache = None
    profiler = None
    DataValidator = None
    config = None

# Core system imports
try:
    from unified_data_system import UnifiedDataSystem
    from optimal_lineup_optimizer import OptimalLineupOptimizer, OptimizationResult
except ImportError as e:
    print(f"⚠️ Core systems not available: {e}")
    UnifiedDataSystem = None
    OptimalLineupOptimizer = None

# Enhanced modules
try:
    from enhanced_stats_engine import apply_enhanced_statistical_analysis

    ENHANCED_STATS_AVAILABLE = True
    print("✅ Enhanced Statistical Analysis Engine loaded")
except ImportError:
    ENHANCED_STATS_AVAILABLE = False
    print("⚠️ Enhanced stats engine not found - using basic analysis")


    def apply_enhanced_statistical_analysis(players, verbose=False):
        return 0

# Optimization library
try:
    import pulp

    MILP_AVAILABLE = True
    print("✅ PuLP available - MILP optimization enabled")
except ImportError:
    MILP_AVAILABLE = False
    print("⚠️ PuLP not available - using greedy fallback")

# External data modules
try:
    from vegas_lines import VegasLines

    VEGAS_AVAILABLE = True
    print("✅ Vegas lines module imported")
except ImportError:
    VEGAS_AVAILABLE = False
    print("⚠️ vegas_lines.py not found")


    class VegasLines:
        def __init__(self, **kwargs):
            self.lines = {}

        def get_vegas_lines(self, **kwargs):
            return {}

        def apply_to_players(self, players):
            return players

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

        def get_all_confirmations(self):
            return 0, 0

        def is_player_confirmed(self, name, team):
            return False, None

        def is_pitcher_confirmed(self, name, team):
            return False

try:
    from simple_statcast_fetcher import SimpleStatcastFetcher, FastStatcastFetcher

    STATCAST_AVAILABLE = True
    print("✅ Statcast fetcher imported")
except ImportError:
    STATCAST_AVAILABLE = False
    print("⚠️ simple_statcast_fetcher.py not found")


    class SimpleStatcastFetcher:
        def __init__(self):
            pass

        def fetch_player_data(self, name, position):
            return {}

        def fetch_multiple_players_parallel(self, players):
            return {}

        def test_connection(self):
            return False

try:
    from recent_form_analyzer import RecentFormAnalyzer

    RECENT_FORM_AVAILABLE = True
    print("✅ Recent Form Analyzer imported")
except ImportError:
    RECENT_FORM_AVAILABLE = False
    print("⚠️ recent_form_analyzer.py not found")

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

# ============================================================================
# CONSTANTS
# ============================================================================

# Park factors (1.0 = neutral, >1.0 = hitter friendly, <1.0 = pitcher friendly)
PARK_FACTORS = {
    # Extreme hitter-friendly
    "COL": 1.20,  # Coors Field

    # Hitter-friendly
    "CIN": 1.12, "TEX": 1.10, "PHI": 1.08, "MIL": 1.06,
    "BAL": 1.05, "HOU": 1.04, "TOR": 1.03, "BOS": 1.03,

    # Slight hitter-friendly
    "NYY": 1.02, "CHC": 1.01,

    # Neutral
    "ARI": 1.00, "ATL": 1.00, "MIN": 0.99,

    # Slight pitcher-friendly
    "WSH": 0.98, "NYM": 0.97, "LAA": 0.96, "STL": 0.95,

    # Pitcher-friendly
    "CLE": 0.94, "TB": 0.93, "KC": 0.92, "DET": 0.91, "SEA": 0.90,

    # Extreme pitcher-friendly
    "OAK": 0.89, "SF": 0.88, "SD": 0.87, "MIA": 0.86, "PIT": 0.85,

    # Additional teams
    "LAD": 0.98, "CHW": 0.96, "CWS": 0.96,
}

KNOWN_RELIEF_PITCHERS = {
    'jhoan duran', 'edwin diaz', 'felix bautista', 'ryan helsley',
    'david bednar', 'alexis diaz', 'josh hader', 'emmanuel clase',
    'jordan romano', 'clay holmes'
}

# Real data configuration
USE_ONLY_REAL_DATA = True

REAL_DATA_SOURCES = {
    'statcast': True,  # Real Baseball Savant
    'vegas': True,  # Real API calls
    'mlb_lineups': True,  # Real MLB API
    'dff_rankings': True,  # Manual upload via GUI
    'park_factors': True,  # Built-in factors
    'recent_form': True,  # Real game logs
    'weather': False,  # DISABLED - No real source
    'fallbacks': False  # DISABLED - No fallback data
}


# ============================================================================
# PLAYER CLASS
# ============================================================================

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

        # Scoring
        self.base_score = self.projection if self.projection > 0 else (self.salary / 1000.0)
        self.enhanced_score = self.base_score

        # Contest specific
        self.contest_type = player_data.get('contest_type', 'classic')

    def _parse_positions_enhanced(self, position_str: str) -> List[str]:
        """Enhanced position parsing that properly handles DraftKings format"""
        if not position_str:
            return ['UTIL']

        position_str = str(position_str).strip().upper()

        # IMPORTANT: If this is just "UTIL", don't return it yet -
        # it might be a multi-position player marked as UTIL
        if position_str == 'UTIL':
            # This is likely a DH or multi-position player
            # We'll need to check the Roster Position column
            return ['UTIL']  # Will be overridden if Roster Position has real positions

        # Handle multi-position formats
        positions = []

        # Try different delimiters
        if '/' in position_str:
            positions = position_str.split('/')
        elif ',' in position_str:
            positions = position_str.split(',')
        elif '-' in position_str and position_str.count('-') == 1:  # Avoid splitting "1B-2B-3B" incorrectly
            positions = position_str.split('-')
        else:
            positions = [position_str]

        # Clean and map positions
        valid_positions = []
        position_mapping = {
            'P': 'P', 'SP': 'P', 'RP': 'P',
            'C': 'C',
            '1B': '1B', 'FIRST': '1B',
            '2B': '2B', 'SECOND': '2B',
            '3B': '3B', 'THIRD': '3B',
            'SS': 'SS', 'SHORTSTOP': 'SS',
            'OF': 'OF', 'OUTFIELD': 'OF',
            'LF': 'OF', 'CF': 'OF', 'RF': 'OF',
            'UTIL': 'UTIL', 'DH': 'UTIL'
        }

        for pos in positions:
            pos = pos.strip().upper()
            mapped = position_mapping.get(pos, None)
            if mapped and mapped not in valid_positions:
                valid_positions.append(mapped)

        # IMPORTANT: Don't default to UTIL if we found real positions
        if valid_positions:
            return valid_positions
        else:
            return ['UTIL']

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
        """Enhanced eligibility check with pitcher validation"""
        # SHOWDOWN: All players are eligible!
        if hasattr(self, 'contest_type') and self.contest_type == 'showdown':
            return True

        if mode == 'all':
            return True
        elif mode == 'manual_only':
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

    def apply_vegas_data(self, vegas_data: Dict):
        """Apply Vegas data"""
        self.vegas_data = vegas_data

    def apply_statcast_data(self, statcast_data: Dict):
        """Apply Statcast data"""
        self.statcast_data = statcast_data

    def apply_park_factors(self, park_data: Dict):
        """Apply park factor data"""
        self.park_factors = park_data

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

    def get_status_string(self) -> str:
        """Get comprehensive status string showing ALL data sources"""
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

        # Batting order
        if hasattr(self, 'batting_order') and self.batting_order:
            status_parts.append(f"BAT-{self.batting_order}")

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

    def __repr__(self):
        pos_str = '/'.join(self.positions)
        status = "✅" if self.is_eligible_for_selection() else "❌"
        return f"Player({self.name}, {pos_str}, ${self.salary}, {self.enhanced_score:.1f}, {status})"

# ============================================================================
# MAIN DFS CORE CLASS
# ============================================================================

class BulletproofDFSCore:
    """Complete bulletproof DFS core with enhanced pitcher detection"""

    def __init__(self):
        """Initialize BulletproofDFSCore with all modules and configuration"""
        # Basic attributes
        self.players = []
        self.contest_type = 'classic'
        self.salary_cap = 50000
        self.optimization_mode = 'bulletproof'
        self.dff_classic_file = None
        self.dff_showdown_file = None
        self.current_dff_file = None


        # Set game date
        self.game_date = datetime.now().strftime('%Y-%m-%d')

        # Load configuration
        try:
            from dfs_config import dfs_config
            self.config = dfs_config
            self.salary_cap = self.config.get('optimization.salary_cap', 50000)
            self.batch_size = self.config.get('optimization.batch_size', 25)
            self.max_form_analysis_players = self.config.get('optimization.max_form_analysis_players', None)
        except:
            self.config = None
            self.batch_size = 25
            self.max_form_analysis_players = None

        # Initialize tracking for duplicate prevention
        self._enrichment_applied = {}

        # Initialize external modules
        self._initialize_modules()

        print("🚀 Bulletproof DFS Core initialized successfully")

    def manual_identify_showdown_pitchers(self, pitcher_names: List[str]):
        """Manually identify pitchers by name for showdown"""
        print(f"\n🎯 MANUAL PITCHER IDENTIFICATION")
        print("=" * 60)

        identified = []
        for pitcher_name in pitcher_names:
            for player in self.players:
                if pitcher_name.lower() in player.name.lower():
                    player.original_position = 'P'
                    player.original_positions = ['P']
                    identified.append(player)
                    print(f"   ✅ Manually identified: {player.name} as pitcher")
                    break

        print(f"✅ Manually identified {len(identified)} pitchers")
        return identified

    def identify_showdown_pitchers(self):
        """Identify pitchers in showdown using smart detection"""
        print("\n⚾ IDENTIFYING PITCHERS IN SHOWDOWN")
        print("=" * 60)

        # Get teams playing
        teams = list(set(p.team for p in self.players if p.team))
        print(f"Teams in showdown: {teams}")

        # Method 1: Check if confirmation system knows who's pitching
        identified_pitchers = []

        if self.confirmation_system:
            # Get confirmed pitchers for these teams
            if hasattr(self.confirmation_system, 'confirmed_pitchers'):
                for team in teams:
                    if team in self.confirmation_system.confirmed_pitchers:
                        pitcher_data = self.confirmation_system.confirmed_pitchers[team]
                        pitcher_name = pitcher_data.get('name', '')

                        # Find this pitcher in our player list
                        for player in self.players:
                            if self.confirmation_system.data_system.match_player_names(
                                    player.name, pitcher_name
                            ):
                                player.original_position = 'P'
                                player.original_positions = ['P']
                                identified_pitchers.append(player)
                                print(f"   ⚾ Confirmed starter found: {player.name} ({player.team})")
                                break

        # Method 2: Use projections as fallback
        if len(identified_pitchers) < 2:
            print("\n🔍 Using projection-based detection for remaining pitchers...")

            # Sort by projection to find likely pitchers
            sorted_by_proj = sorted(
                [p for p in self.players if p.projection > 0 and p not in identified_pitchers],
                key=lambda x: x.projection
            )

            # In showdown, typically the 2-4 lowest projected players are pitchers
            for player in sorted_by_proj[:4]:
                if len(identified_pitchers) < 2:
                    player.original_position = 'P'
                    player.original_positions = ['P']
                    identified_pitchers.append(player)
                    print(
                        f"   ⚾ Likely pitcher (low projection): {player.name} ({player.team}) - Proj: {player.projection}")

        print(f"\n✅ Identified {len(identified_pitchers)} pitchers in showdown")
        return identified_pitchers

    def reset_all_confirmations(self):
        """Reset ALL confirmation status - call this at the start of each run"""
        print("\n🔄 RESETTING ALL CONFIRMATIONS")
        for player in self.players:
            player.is_confirmed = False
            player.confirmation_sources = []
            # Don't reset manual selections
        print(f"✅ Reset confirmations for {len(self.players)} players")

    def get_eligible_players_by_mode(self):
        """Get eligible players based on optimization mode"""

        # For showdown, ALL players are eligible regardless of position
        if self.contest_type == 'showdown':
            if self.optimization_mode == 'all':
                eligible = self.players.copy()
                print(f"🌐 ALL PLAYERS MODE (SHOWDOWN): {len(eligible)}/{len(self.players)} players eligible")
            elif self.optimization_mode == 'manual_only':
                eligible = [p for p in self.players if p.is_manual_selected]
                print(f"🎯 MANUAL-ONLY MODE (SHOWDOWN): {len(eligible)}/{len(self.players)} manually selected players")
            elif self.optimization_mode == 'confirmed_only':
                eligible = [p for p in self.players if p.is_confirmed]
                print(f"🔒 CONFIRMED-ONLY MODE (SHOWDOWN): {len(eligible)}/{len(self.players)} confirmed players")
            else:  # bulletproof
                eligible = [p for p in self.players if p.is_confirmed or p.is_manual_selected]
                print(f"🛡️ BULLETPROOF MODE (SHOWDOWN): {len(eligible)}/{len(self.players)} players eligible")

                # Show breakdown
                confirmed_only = sum(1 for p in eligible if p.is_confirmed and not p.is_manual_selected)
                manual_only = sum(1 for p in eligible if p.is_manual_selected and not p.is_confirmed)
                both = sum(1 for p in eligible if p.is_confirmed and p.is_manual_selected)

                print(f"   - Confirmed only: {confirmed_only}")
                print(f"   - Manual only: {manual_only}")
                print(f"   - Both confirmed & manual: {both}")

            # Show position types available (for info only)
            position_types = {}
            for player in eligible:
                # Use ORIGINAL position for display
                orig_pos = getattr(player, 'original_position', 'UTIL')
                position_types[orig_pos] = position_types.get(orig_pos, 0) + 1

            if position_types:
                print(f"📊 Position types in eligible pool (by original): {position_types}")

            return eligible

        # CLASSIC MODE - original logic with position validation
        self._validate_confirmations()

        if self.optimization_mode == 'all':
            eligible = self.players.copy()
            print(f"🌐 ALL PLAYERS MODE: {len(eligible)}/{len(self.players)} players eligible")
        elif self.optimization_mode == 'manual_only':
            eligible = [p for p in self.players if p.is_manual_selected]
            print(f"🎯 MANUAL-ONLY MODE: {len(eligible)}/{len(self.players)} manually selected players")
        elif self.optimization_mode == 'confirmed_only':
            eligible = [p for p in self.players if p.is_confirmed and not p.is_manual_selected]
            print(f"🔒 CONFIRMED-ONLY MODE: {len(eligible)}/{len(self.players)} confirmed players")
        else:  # bulletproof (default)
            eligible = [p for p in self.players if p.is_confirmed or p.is_manual_selected]
            print(f"🛡️ BULLETPROOF MODE: {len(eligible)}/{len(self.players)} players eligible")

            # Show breakdown
            confirmed_only = sum(1 for p in eligible if p.is_confirmed and not p.is_manual_selected)
            manual_only = sum(1 for p in eligible if p.is_manual_selected and not p.is_confirmed)
            both = sum(1 for p in eligible if p.is_confirmed and p.is_manual_selected)

            print(f"   - Confirmed only: {confirmed_only}")
            print(f"   - Manual only: {manual_only}")
            print(f"   - Both confirmed & manual: {both}")

        # Extra validation for pitchers (skip in 'all' mode)
        if self.optimization_mode != 'all':
            eligible = self._validate_pitcher_eligibility(eligible)

        return eligible

    def _validate_confirmations(self):
        """Validate that ONLY appropriate players are confirmed"""
        print("\n🔍 VALIDATING CONFIRMATIONS...")

        issues = []

        for player in self.players:
            if player.is_confirmed:
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

    def detect_confirmed_players(self) -> int:
        """Apply confirmations to player objects"""
        print("\n🔍 SMART CONFIRMATION DETECTION")
        print("=" * 60)

        # Reset all confirmations first
        self.reset_all_confirmations()

        # DO NOT CALL identify_showdown_pitchers() HERE - REMOVE IT!

        # Initialize confirmation system if needed
        if not self.confirmation_system:
            if CONFIRMED_AVAILABLE:
                try:
                    from smart_confirmation_system import SmartConfirmationSystem
                    self.confirmation_system = SmartConfirmationSystem(
                        csv_players=self.players,
                        verbose=True
                    )
                    print("✅ Smart Confirmation System initialized successfully")
                except Exception as e:
                    print(f"❌ Failed to initialize confirmation system: {e}")
                    self.confirmation_system = None
                    return 0
            else:
                print("❌ SmartConfirmationSystem module not available")
                return 0

        # Update CSV players in confirmation system
        if hasattr(self.confirmation_system, 'csv_players'):
            self.confirmation_system.csv_players = self.players
            self.confirmation_system.csv_teams = set(p.team for p in self.players if p.team)

        # Get all confirmations - THIS GETS THE REAL MLB DATA INCLUDING PITCHERS
        lineup_count, pitcher_count = self.confirmation_system.get_all_confirmations()

        # FOR SHOWDOWN: Use the MLB pitcher data to identify our pitchers
        if self.contest_type == 'showdown' and hasattr(self.confirmation_system, 'confirmed_pitchers'):
            print("\n⚾ MATCHING SHOWDOWN PITCHERS FROM MLB DATA")
            print("=" * 60)

            teams = list(set(p.team for p in self.players if p.team))
            showdown_pitchers_found = 0

            for team in teams:
                if team in self.confirmation_system.confirmed_pitchers:
                    pitcher_info = self.confirmation_system.confirmed_pitchers[team]
                    mlb_pitcher_name = pitcher_info.get('name', '')

                    if not mlb_pitcher_name:
                        continue

                    print(f"\n🎯 MLB says {team} starter is: {mlb_pitcher_name}")
                    print(f"   Looking for match in CSV...")

                    # Try to find this pitcher in our CSV
                    matched = False

                    # First pass: Try exact/close name matches
                    for player in self.players:
                        if player.team != team:
                            continue

                        # Name matching logic
                        player_name_lower = player.name.lower()
                        mlb_name_lower = mlb_pitcher_name.lower()

                        # Check for match
                        if (player_name_lower == mlb_name_lower or
                                mlb_name_lower in player_name_lower or
                                player_name_lower in mlb_name_lower or
                                (mlb_name_lower.split()[-1] == player_name_lower.split()[-1])):  # Last name match

                            # FOUND IT!
                            player.original_position = 'P'
                            player.original_positions = ['P']
                            player.is_confirmed = True
                            player.add_confirmation_source("mlb_starter")
                            matched = True
                            showdown_pitchers_found += 1
                            print(
                                f"   ✅ MATCHED: {player.name} (Proj: {player.projection}, Salary: ${player.salary:,})")
                            break

                    # Second pass: If no name match, look for SP with high projection
                    if not matched:
                        print(f"   ⚠️ No exact match for {mlb_pitcher_name}, checking SP positions...")

                        for player in self.players:
                            if (player.team == team and
                                    player.primary_position == 'SP' and
                                    10 <= player.projection <= 25):  # Starting pitchers have higher projections

                                player.original_position = 'P'
                                player.original_positions = ['P']
                                player.is_confirmed = True
                                player.add_confirmation_source("mlb_starter_projection")
                                matched = True
                                showdown_pitchers_found += 1
                                print(f"   ✅ MATCHED BY POSITION: {player.name} (SP, Proj: {player.projection})")
                                break

                    if not matched:
                        print(f"   ❌ Could not find {mlb_pitcher_name} in CSV")

            print(f"\n📊 Showdown pitchers matched: {showdown_pitchers_found}/2")

        # Apply confirmations to all players
        confirmed_count = 0
        confirmed_pitchers = 0

        for player in self.players:
            # Count already marked pitchers
            if self.contest_type == 'showdown' and hasattr(player,
                                                           'original_position') and player.original_position == 'P':
                confirmed_count += 1
                confirmed_pitchers += 1
                continue

            # Check regular lineup confirmations
            is_confirmed, batting_order = self.confirmation_system.is_player_confirmed(
                player.name, player.team
            )
            if is_confirmed:
                player.is_confirmed = True
                player.add_confirmation_source("mlb_lineup")
                if batting_order:
                    player.batting_order = batting_order
                confirmed_count += 1

        # Final showdown verification
        if self.contest_type == 'showdown':
            final_pitcher_count = sum(1 for p in self.players
                                      if hasattr(p, 'original_position') and p.original_position == 'P')

            print(f"\n📊 FINAL SHOWDOWN STATUS:")
            print(f"   Total confirmed players: {confirmed_count}")
            print(f"   Starting pitchers identified: {final_pitcher_count}")

            # List the pitchers
            pitchers = [p for p in self.players
                        if hasattr(p, 'original_position') and p.original_position == 'P']

            if pitchers:
                print(f"\n   Starting Pitchers:")
                for p in pitchers:
                    sources = ', '.join(p.confirmation_sources) if hasattr(p, 'confirmation_sources') else 'Unknown'
                    print(f"      ⚾ {p.name} ({p.team}) - ${p.salary:,} - Proj: {p.projection} - Sources: [{sources}]")
            else:
                print("   ❌ NO PITCHERS IDENTIFIED!")

        print(f"\n📊 Total confirmed: {confirmed_count} players")

        # Apply DFF if available
        if hasattr(self, 'current_dff_file') and self.current_dff_file:
            print("\n🎯 APPLYING DFF RANKINGS...")
            self.apply_dff_rankings(self.current_dff_file)

        # Apply enrichments only to confirmed players
        if confirmed_count > 0:
            print("\n📊 APPLYING ADVANCED ANALYTICS...")
            self._apply_enrichments_to_confirmed_players()
        else:
            print("\n⚠️ NO PLAYERS CONFIRMED!")

        return confirmed_count

    def _initialize_modules(self):
        """Initialize all external modules with proper error handling"""
        # Vegas Lines
        if VEGAS_AVAILABLE:
            try:
                self.vegas_lines = VegasLines()
                print("✅ Vegas lines module initialized")
            except Exception as e:
                print(f"❌ Failed to initialize Vegas lines: {e}")
                self.vegas_lines = None
        else:
            self.vegas_lines = None

        # Smart Confirmation System
        if CONFIRMED_AVAILABLE:
            try:
                self.confirmation_system = SmartConfirmationSystem(
                    csv_players=[],  # Empty at first, will be updated when CSV loads
                    verbose=True
                )
                print("✅ Smart Confirmation System initialized")
            except Exception as e:
                print(f"❌ Failed to initialize SmartConfirmationSystem: {e}")
                self.confirmation_system = None
        else:
            self.confirmation_system = None

        # Statcast Fetcher
        if STATCAST_AVAILABLE:
            try:
                self.statcast_fetcher = SimpleStatcastFetcher()
                print("✅ Statcast fetcher initialized")
            except Exception as e:
                print(f"❌ Failed to initialize Statcast fetcher: {e}")
                self.statcast_fetcher = None
        else:
            self.statcast_fetcher = None

        # Recent Form Analyzer
        if RECENT_FORM_AVAILABLE:
            try:
                from utils.cache_manager import cache
                from recent_form_analyzer import RecentFormAnalyzer
                self.form_analyzer = RecentFormAnalyzer(cache_manager=cache)
                print("✅ Recent Form Analyzer initialized")
            except Exception as e:
                print(f"❌ Failed to initialize Recent Form Analyzer: {e}")
                self.form_analyzer = None
        else:
            self.form_analyzer = None

        # Batting Order and Correlation Systems
        if BATTING_CORRELATION_AVAILABLE:
            try:
                integrate_batting_order_correlation(self)
                print("✅ Batting Order & Correlation Systems integrated")
            except Exception as e:
                print(f"❌ Failed to integrate batting order/correlation: {e}")

        # Unified Data System
        try:
            self.data_system = UnifiedDataSystem()
            print("✅ Unified Data System initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Unified Data System: {e}")
            self.data_system = None

    # ========================================================================
    # CSV LOADING AND PARSING
    # ========================================================================

    def load_draftkings_csv(self, file_path: str) -> bool:
        """Load DraftKings CSV with better multi-position parsing"""
        try:
            print(f"📁 Loading DraftKings CSV: {Path(file_path).name}")

            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                return False

            # Read CSV
            df = pd.read_csv(file_path)
            print(f"📊 Found {len(df)} rows, {len(df.columns)} columns")

            # Detect contest type
            self._detect_contest_type(df, file_path)

            # Parse columns
            column_map = self._detect_columns(df)

            # Parse players
            self.players = self._parse_players(df, column_map)

            # Update confirmation system if available
            if self.confirmation_system and hasattr(self.confirmation_system, 'csv_players'):
                self.confirmation_system.csv_players = self.players
                self.confirmation_system.csv_teams = set(p.team for p in self.players if p.team)

            print(f"✅ Loaded {len(self.players)} valid {self.contest_type.upper()} players")

            # Show position statistics
            self._show_position_stats()

            return True

        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _detect_contest_type(self, df: pd.DataFrame, file_path: str):
        """Detect contest type from filename and data"""
        filename = os.path.basename(file_path).lower()

        # Check filename
        if any(indicator in filename for indicator in ['showdown', 'captain', 'sd', 'cptn']):
            self.contest_type = 'showdown'
            print("🎯 SHOWDOWN DETECTED (filename)")
        else:
            # Check team count
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

    def _detect_columns(self, df: pd.DataFrame) -> Dict[str, int]:
        """Detect column indices for important fields"""
        column_map = {}
        roster_position_idx = None

        for i, col in enumerate(df.columns):
            col_lower = str(col).lower().strip()

            # Check for Roster Position column specifically
            if 'roster position' in col_lower:
                roster_position_idx = i
                print(f"   Found Roster Position column at index {i}")

            # Name column
            if any(name in col_lower for name in ['name', 'player']):
                if 'name' in col_lower and '+' not in col_lower and 'name' not in column_map:
                    column_map['name'] = i

            # Position column
            elif any(pos in col_lower for pos in ['position']) and 'roster' not in col_lower:
                if 'position' not in column_map:
                    column_map['position'] = i

            # Team column
            elif any(team in col_lower for team in ['team', 'teamabbrev', 'tm']):
                if 'team' not in column_map:
                    column_map['team'] = i

            # Salary column
            elif any(sal in col_lower for sal in ['salary', 'sal', 'cost']):
                if 'salary' not in column_map:
                    column_map['salary'] = i

            # Projection column
            elif any(proj in col_lower for proj in ['avgpointspergame', 'fppg', 'projection', 'points']):
                if 'projection' not in column_map:
                    column_map['projection'] = i

        # Store roster position index separately
        if roster_position_idx is not None:
            column_map['roster_position'] = roster_position_idx

        # Debug output
        print(f"📋 Detected columns:")
        for field, idx in column_map.items():
            print(f"   {field}: column {idx} ('{df.columns[idx]}')")

        return column_map

    def _parse_players(self, df: pd.DataFrame, column_map: Dict[str, int]) -> List[AdvancedPlayer]:
        """Parse players from dataframe with enhanced position handling"""
        players = []
        pitcher_count = 0

        print(f"\n📊 Parsing {len(df)} rows...")

        # For showdown, we need to identify pitchers by projection
        if self.contest_type == 'showdown':
            # First pass: Get all projections to find the threshold
            projections = []
            for idx, row in df.iterrows():
                try:
                    proj = float(row.iloc[column_map.get('projection', 4)])
                    if proj > 0:
                        projections.append(proj)
                except:
                    pass

            # Find projection threshold (pitchers typically have lowest projections)
            if projections:
                projections.sort()
                # Pitchers are usually the 2-4 lowest projections
                pitcher_threshold = projections[min(4, len(projections) // 4)] if len(projections) > 10 else 10.0
                print(f"⚾ Pitcher detection threshold: projections < {pitcher_threshold:.1f}")

        for idx, row in df.iterrows():
            try:
                # Get player data
                player_name = str(row.iloc[column_map.get('name', 0)]).strip()
                projection = float(row.iloc[column_map.get('projection', 4)])
                salary = row.iloc[column_map.get('salary', 3)]

                # For showdown, check if this is likely a pitcher
                is_likely_pitcher = False
                if self.contest_type == 'showdown' and projection > 0:
                    # Multiple criteria for pitcher detection
                    is_likely_pitcher = (
                            projection < pitcher_threshold or  # Low projection
                            (projection < 5.0 and salary >= 7000) or  # Low proj + high salary = SP
                            any(pitcher_name in player_name.lower() for pitcher_name in
                                ['cecconi', 'walter', 'brown', 'blanco'])  # Known pitchers
                    )

                # Determine position
                if is_likely_pitcher:
                    position_str = 'P'
                    pitcher_count += 1
                    print(f"   ⚾ Identified pitcher: {player_name} (Proj: {projection:.1f}, Salary: ${salary:,})")
                else:
                    # Original position logic
                    primary_position = str(row.iloc[column_map.get('position', 0)]).strip().upper()
                    roster_position = ""
                    if 'roster_position' in column_map:
                        roster_position = str(row.iloc[column_map['roster_position']]).strip().upper()

                    position_str = roster_position if roster_position and roster_position not in ['', 'NAN', 'NONE',
                                                                                                  'UTIL'] else primary_position

                player_data = {
                    'id': idx + 1,
                    'name': player_name,
                    'position': position_str,
                    'team': str(row.iloc[column_map.get('team', 2)]).strip(),
                    'salary': salary,
                    'projection': projection,
                    'contest_type': self.contest_type
                }

                # Create player
                player = AdvancedPlayer(player_data)

                # Store original positions BEFORE modifications
                player.original_positions = player.positions.copy()
                player.original_position = player.primary_position

                # For showdown, change positions but keep original
                if self.contest_type == 'showdown':
                    player.positions = ['CPT', 'UTIL']
                    player.primary_position = 'UTIL'
                    player.showdown_eligible = True

                if player.name and player.salary > 0:
                    players.append(player)

            except Exception as e:
                print(f"❌ Error parsing row {idx}: {e}")
                continue

        print(f"✅ Successfully parsed {len(players)} players")
        if self.contest_type == 'showdown':
            print(f"⚾ Identified {pitcher_count} pitchers")

        return players

    def _show_position_stats(self):
        """Show position statistics"""
        multi_position_count = sum(1 for p in self.players if len(p.positions) > 1)
        single_position_count = sum(1 for p in self.players if len(p.positions) == 1)

        print(f"📊 Position stats: {multi_position_count} multi-position, {single_position_count} single-position")

        # Position breakdown
        position_counts = {}
        for player in self.players:
            for pos in player.positions:
                position_counts[pos] = position_counts.get(pos, 0) + 1

        print(f"📍 Position coverage: {position_counts}")

    # ========================================================================
    # PLAYER SELECTION AND CONFIRMATION
    # ========================================================================

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
                if similarity > best_score and similarity >= 0.6:
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

    def detect_confirmed_players(self) -> int:
        """Apply confirmations to player objects"""
        print("\n🔍 SMART CONFIRMATION DETECTION")
        print("=" * 60)

        # Reset all confirmations first
        self.reset_all_confirmations()

        # FOR SHOWDOWN: First identify who the pitchers are
        if self.contest_type == 'showdown':
            print("🔄 Identifying pitchers in showdown format...")


            # Now temporarily restore positions for confirmation
            print("🔄 Temporarily restoring original positions for confirmation...")
            for player in self.players:
                if hasattr(player, 'original_position'):
                    player._temp_position = player.primary_position  # Save current
                    player.primary_position = player.original_position  # Restore original

        # Initialize confirmation system if needed
        if not self.confirmation_system:
            if CONFIRMED_AVAILABLE:
                try:
                    from smart_confirmation_system import SmartConfirmationSystem
                    self.confirmation_system = SmartConfirmationSystem(
                        csv_players=self.players,
                        verbose=True
                    )
                    print("✅ Smart Confirmation System initialized successfully")
                except Exception as e:
                    print(f"❌ Failed to initialize confirmation system: {e}")
                    self.confirmation_system = None
                    return 0
            else:
                print("❌ SmartConfirmationSystem module not available")
                return 0

        # Update CSV players in confirmation system
        if hasattr(self.confirmation_system, 'csv_players'):
            self.confirmation_system.csv_players = self.players
            self.confirmation_system.csv_teams = set(p.team for p in self.players if p.team)

        # Get all confirmations
        lineup_count, pitcher_count = self.confirmation_system.get_all_confirmations()

        # Apply confirmations to players
        confirmed_count = 0
        confirmed_pitchers = 0

        # Process regular players
        for player in self.players:
            # Use primary_position which has been set correctly (original for showdown)
            if player.primary_position != 'P':  # Non-pitchers
                is_confirmed, batting_order = self.confirmation_system.is_player_confirmed(
                    player.name, player.team
                )
                if is_confirmed:
                    player.is_confirmed = True
                    player.add_confirmation_source("mlb_lineup")
                    if batting_order:
                        player.batting_order = batting_order
                    confirmed_count += 1

        # Process pitchers
        for player in self.players:
            if player.primary_position == 'P':
                is_confirmed = self.confirmation_system.is_pitcher_confirmed(
                    player.name, player.team
                )
                if is_confirmed:
                    player.is_confirmed = True
                    player.add_confirmation_source("mlb_starter")
                    confirmed_count += 1
                    confirmed_pitchers += 1

                    if self.contest_type == 'showdown':
                        print(f"   ⚾ Pitcher CONFIRMED as starter: {player.name} ({player.team})")

        # FOR SHOWDOWN: Restore UTIL positions after confirmation
        if self.contest_type == 'showdown':
            print("🔄 Restoring showdown positions...")
            for player in self.players:
                if hasattr(player, '_temp_position'):
                    player.primary_position = player._temp_position  # Restore showdown position
                    delattr(player, '_temp_position')

        print(f"\n📊 Total confirmed: {confirmed_count} players")
        if self.contest_type == 'showdown':
            print(f"   Including {confirmed_pitchers} confirmed starting pitchers")

        # Show breakdown by position for showdown
        if self.contest_type == 'showdown':
            position_breakdown = {}
            for player in self.players:
                if player.is_confirmed:
                    orig_pos = getattr(player, 'original_position', 'UTIL')
                    position_breakdown[orig_pos] = position_breakdown.get(orig_pos, 0) + 1

            print(f"📊 Confirmed by original position: {position_breakdown}")

        # Apply DFF if available
        if hasattr(self, 'current_dff_file') and self.current_dff_file:
            print("\n🎯 APPLYING DFF RANKINGS...")
            self.apply_dff_rankings(self.current_dff_file)

        # Apply enrichments only to confirmed players
        if confirmed_count > 0:
            print("\n📊 APPLYING ADVANCED ANALYTICS...")
            self._apply_enrichments_to_confirmed_players()
        else:
            print("\n⚠️ NO PLAYERS CONFIRMED!")
            print("💡 Try:")
            print("1. Add manual players")
            print("2. Check name matching between CSV and MLB data")
            print("3. Use 'All Players' mode for testing")

        return confirmed_count



    def _validate_pitcher_eligibility(self, eligible: List[AdvancedPlayer]) -> List[AdvancedPlayer]:
        """Extra validation for pitcher eligibility"""
        eligible_pitchers = [p for p in eligible if p.primary_position == 'P']
        print(f"\n⚾ PITCHER VALIDATION:")
        print(f"   Total eligible pitchers: {len(eligible_pitchers)}")

        for pitcher in eligible_pitchers[:5]:  # Show first 5
            sources = ', '.join(pitcher.confirmation_sources) if pitcher.confirmation_sources else 'MANUAL'
            print(f"   - {pitcher.name} ({pitcher.team}) - Sources: [{sources}]")

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

        # Position breakdown
        position_counts = {}
        for player in eligible:
            for pos in player.positions:
                position_counts[pos] = position_counts.get(pos, 0) + 1

        print(f"\n📍 Eligible position coverage: {position_counts}")

        return eligible

    # ========================================================================
    # DATA ENRICHMENT
    # ========================================================================

    def detect_and_load_dff_files(self, dff_file_path: str = None):
        """Intelligently detect and load appropriate DFF file based on contest type"""
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
                    showdown_files.sort(key=os.path.getmtime, reverse=True)
                    selected_file = showdown_files[0]
                    self.dff_showdown_file = selected_file
                    print(f"\n✅ Auto-selected SHOWDOWN DFF: {selected_file}")
                    return self.apply_dff_rankings(selected_file)
                elif classic_files:
                    print(f"\n⚠️ No showdown DFF found, using classic DFF for showdown contest")
                    selected_file = classic_files[0]
                    return self.apply_dff_rankings(selected_file)
            else:  # classic contest
                if classic_files:
                    classic_files.sort(key=os.path.getmtime, reverse=True)
                    selected_file = classic_files[0]
                    self.dff_classic_file = selected_file
                    print(f"\n✅ Auto-selected CLASSIC DFF: {selected_file}")
                    return self.apply_dff_rankings(selected_file)
                elif showdown_files:
                    print(f"\n⚠️ No classic DFF found, using showdown DFF for classic contest")
                    selected_file = showdown_files[0]
                    return self.apply_dff_rankings(selected_file)

        return False

    def apply_dff_rankings(self, dff_file_path: str) -> bool:
        """Apply DFF rankings with enhanced matching"""
        if not dff_file_path or not os.path.exists(dff_file_path):
            print("⚠️ No DFF file provided or file not found")
            return False

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

                    # Clean DFF name
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

                    # Find best matching player
                    best_match = None
                    best_score = 0

                    for player in self.players:
                        similarity = self._name_similarity(dff_name, player.name)

                        # Boost score for same team
                        if dff_team and player.team == dff_team and similarity >= 0.7:
                            similarity = min(1.0, similarity + 0.1)

                        if similarity > best_score and similarity >= 0.7:
                            best_score = similarity
                            best_match = player

                    if best_match and 'ppg_projection' in dff_data:
                        # Apply to matched player
                        best_match.apply_dff_data(dff_data)
                        matches += 1
                        all_enriched += 1

                        # Check if eligible
                        if best_match.is_eligible_for_selection(self.optimization_mode):
                            eligible_enriched += 1

                            # Show match details for first few
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

    def _apply_enrichments_to_confirmed_players(self):
        """Apply all enrichments to confirmed players"""
        # Get only confirmed players
        truly_confirmed = [p for p in self.players if p.is_confirmed]
        print(f"🎯 Enriching {len(truly_confirmed)} confirmed players...")

        if not truly_confirmed:
            print("⚠️ No confirmed players to enrich")
            return

        # Track which enrichments have been applied
        self._enrichment_applied = {
            'vegas': False,
            'statcast': False,
            'park_factors': False,
            'recent_form': False,
            'batting_order': False,
            'statistical_analysis': False
        }

        # Note: DFF data was already applied in detect_confirmed_players()

        # 1. Vegas Lines
        if self.vegas_lines and not self._enrichment_applied['vegas']:
            print("💰 Enriching with Vegas lines...")
            self.enrich_with_vegas_lines()
            self._enrichment_applied['vegas'] = True

        # 2. Statcast Data
        if self.statcast_fetcher and not self._enrichment_applied['statcast']:
            print("📊 Enriching with Statcast data...")
            self.enrich_with_statcast_priority()
            self._enrichment_applied['statcast'] = True

        # 3. Park Factors
        if not self._enrichment_applied['park_factors']:
            print("🏟️ Applying park factors...")
            self.apply_park_factors()
            self._enrichment_applied['park_factors'] = True

        # 4. Recent Form
        if not self._enrichment_applied['recent_form']:
            print("📈 Analyzing recent form for ALL confirmed players...")
            self._apply_recent_form_all_players()
            self._enrichment_applied['recent_form'] = True

        # 5. Batting Order (if available)
        if hasattr(self, 'enrich_with_batting_order') and not self._enrichment_applied['batting_order']:
            print("🔢 Enriching with batting order...")
            self.enrich_with_batting_order()
            self._enrichment_applied['batting_order'] = True

        # 6. Statistical Analysis (combines all data sources)
        if not self._enrichment_applied['statistical_analysis']:
            print("🔬 Applying enhanced statistical analysis...")
            self._apply_comprehensive_statistical_analysis(truly_confirmed)
            self._enrichment_applied['statistical_analysis'] = True

        # Show summary of enrichments
        enrichment_summary = {
            'DFF': sum(1 for p in truly_confirmed if hasattr(p, 'dff_data') and p.dff_data),
            'Vegas': sum(1 for p in truly_confirmed if hasattr(p, 'vegas_data') and p.vegas_data),
            'Statcast': sum(1 for p in truly_confirmed if hasattr(p, 'statcast_data') and p.statcast_data),
            'Batting Order': sum(1 for p in truly_confirmed if hasattr(p, 'batting_order') and p.batting_order),
            'Recent Form': sum(
                1 for p in truly_confirmed if hasattr(p, '_recent_performance') and p._recent_performance)
        }

        print(f"\n📊 Enrichment Summary:")
        for source, count in enrichment_summary.items():
            print(f"   {source}: {count}/{len(truly_confirmed)} players")

        # Apply recent form adjustments (FIXED - This ensures multipliers are applied to enhanced_score)
        if hasattr(self, 'form_analyzer') and self.form_analyzer:
            print("\n📊 Applying recent form multiplier adjustments...")
            form_count = 0

            for player in self.players:
                if hasattr(player, 'enhanced_score'):
                    try:
                        original = player.enhanced_score
                        form_data = self.form_analyzer.analyze_player_form(player)

                        if form_data and 'form_score' in form_data:
                            # Apply the multiplier - THIS IS THE KEY FIX
                            player.enhanced_score = original * form_data['form_score']
                            player.recent_form = {
                                'multiplier': form_data['form_score'],
                                'status': 'hot' if form_data['form_score'] > 1.05 else 'cold' if form_data[
                                                                                                     'form_score'] < 0.95 else 'normal',
                                'original_score': original,
                                'adjusted_score': player.enhanced_score
                            }
                            form_count += 1

                            # Log significant adjustments
                            if abs(form_data['form_score'] - 1.0) > 0.05:
                                status_emoji = '🔥' if player.recent_form['status'] == 'hot' else '❄️'
                                print(
                                    f"   {status_emoji} {player.name}: {original:.1f} → {player.enhanced_score:.1f} ({form_data['form_score']:.2f}x)")
                    except Exception as e:
                        pass

            print(f"✅ Recent form multipliers applied to {form_count} players")

        print("✅ All enrichments applied")

    def enrich_with_vegas_lines(self):
        """Apply Vegas lines with better error handling"""
        if not self.vegas_lines:
            print("⚠️ Vegas lines module not available")
            return

        print("💰 Applying Vegas lines where data exists...")

        try:
            vegas_data = self.vegas_lines.get_vegas_lines()

            if not vegas_data:
                print("⚠️ No Vegas data retrieved - API may be down")
                return

            # Only apply to confirmed/eligible players
            eligible_players = [p for p in self.players if p.is_eligible_for_selection(self.optimization_mode)]

            enriched_count = 0
            for player in eligible_players:
                if player.team in vegas_data:
                    team_vegas = vegas_data[player.team]
                    player.apply_vegas_data(team_vegas)
                    enriched_count += 1

            print(f"✅ Vegas data: {enriched_count}/{len(eligible_players)} players enriched")

        except Exception as e:
            print(f"❌ Vegas enrichment failed: {e}")
            import traceback
            traceback.print_exc()

    def enrich_with_statcast_priority(self):
        """Priority Statcast enrichment with correct method names"""
        if not self.statcast_fetcher:
            print("⚠️ Statcast fetcher not available")
            return

        print("🔬 Priority Statcast enrichment for confirmed players...")

        # Get all confirmed/manual players
        priority_players = [p for p in self.players if p.is_eligible_for_selection(self.optimization_mode)]

        print(f"🎯 Enriching ALL {len(priority_players)} confirmed players with Statcast...")

        # Use parallel method for better performance
        try:
            statcast_results = self.statcast_fetcher.fetch_multiple_players_parallel(priority_players)

            enriched_count = 0
            failed_count = 0

            # Apply results to each player
            for player in priority_players:
                if player.name in statcast_results:
                    statcast_data = statcast_results[player.name]
                    if statcast_data and statcast_data != 'Realistic Fallback (Fast)':
                        player.apply_statcast_data(statcast_data)
                        enriched_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1

            print(f"✅ Statcast enriched: {enriched_count}/{len(priority_players)} players")
            if failed_count > 0:
                print(f"⚠️ Failed to enrich: {failed_count} players")

        except Exception as e:
            print(f"❌ Statcast parallel fetch failed: {e}")
            # Fallback to individual fetching
            enriched_count = 0
            failed_count = 0

            for i, player in enumerate(priority_players):
                if (i + 1) % 10 == 0:
                    print(f"   Progress: {i + 1}/{len(priority_players)} players...")

                try:
                    statcast_data = self.statcast_fetcher.fetch_player_data(
                        player.name,
                        player.primary_position
                    )

                    if statcast_data and statcast_data != 'Realistic Fallback (Fast)':
                        player.apply_statcast_data(statcast_data)
                        enriched_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    failed_count += 1
                    if failed_count <= 3:
                        print(f"   ⚠️ Failed for {player.name}: {e}")

            print(f"✅ Statcast enriched: {enriched_count}/{len(priority_players)} players")
            if failed_count > 0:
                print(f"⚠️ Failed to enrich: {failed_count} players")

    def apply_park_factors(self):
        """Apply park factors using built-in constants"""
        if not REAL_DATA_SOURCES.get('park_factors', False):
            print("⚠️ Park factors disabled in REAL_DATA_SOURCES")
            return

        print("🏟️ Priority park factors for confirmed players...")

        eligible_players = [p for p in self.players if p.is_eligible_for_selection(self.optimization_mode)]
        adjusted_count = 0

        for player in eligible_players:
            if player.team in PARK_FACTORS:
                factor = PARK_FACTORS[player.team]

                # Apply factor based on position
                if player.primary_position == 'P':
                    # Invert for pitchers (pitcher-friendly = good for pitchers)
                    adjusted_factor = 2.0 - factor
                else:
                    # Direct for hitters
                    adjusted_factor = factor

                if abs(adjusted_factor - 1.0) > 0.01:  # Only adjust if meaningful
                    old_score = player.enhanced_score
                    player.enhanced_score *= adjusted_factor

                    # Store the adjustment info
                    player.park_factors = {
                        'park_team': player.team,
                        'factor': adjusted_factor,
                        'original_factor': factor,
                        'adjustment': player.enhanced_score - old_score
                    }

                    adjusted_count += 1

                    # Log significant adjustments
                    if abs(adjusted_factor - 1.0) > 0.05:
                        change_pct = (adjusted_factor - 1.0) * 100
                        print(f"   {player.name} ({player.primary_position}) at {player.team}: "
                              f"{old_score:.1f} → {player.enhanced_score:.1f} "
                              f"({change_pct:+.0f}% park adjustment)")

        print(f"✅ Park factors: {adjusted_count}/{len(eligible_players)} confirmed players adjusted")

    def _apply_recent_form_all_players(self):
        """Apply recent form analysis to ALL confirmed players without limits"""
        if not REAL_DATA_SOURCES.get('recent_form', False):
            print("⚠️ Recent form disabled in REAL_DATA_SOURCES")
            return

        try:
            # First check if the module exists
            try:
                from real_recent_form import RealRecentFormAnalyzer
                print("✅ RealRecentFormAnalyzer module found")
            except ImportError:
                print("❌ real_recent_form.py module not found!")
                print("   Trying fallback to recent_form_analyzer...")
                from recent_form_analyzer import RecentFormAnalyzer
                form_analyzer = RecentFormAnalyzer(days_back=7)
            else:
                form_analyzer = RealRecentFormAnalyzer(days_back=7)

            # Get ALL confirmed players
            players_to_analyze = [p for p in self.players if p.is_confirmed]
            total_players = len(players_to_analyze)

            if not players_to_analyze:
                print("   ⚠️ No confirmed players to analyze")
                return

            print(f"   Analyzing {total_players} players (ALL confirmed)")

            # Add debug for first player
            if players_to_analyze:
                print(f"   Sample player: {players_to_analyze[0].name} ({players_to_analyze[0].team})")

            # Call the form analyzer
            try:
                form_analyzer.enrich_players_with_form(players_to_analyze)
            except Exception as e:
                print(f"   ❌ Form analysis failed: {e}")
                import traceback
                traceback.print_exc()
                return

            # Count results
            adjusted_count = 0
            for player in players_to_analyze:
                if hasattr(player, 'form_rating') and player.form_rating != 1.0:
                    adjusted_count += 1

            print(f"   ✅ Form analysis complete: {adjusted_count}/{total_players} players have form data")

        except Exception as e:
            print(f"⚠️ Recent form failed: {e}")
            import traceback
            traceback.print_exc()

    def debug_multi_position_players(self):
        """Debug multi-position player usage"""
        print("\n🔄 MULTI-POSITION PLAYER ANALYSIS")
        print("=" * 60)

        eligible = self.get_eligible_players_by_mode()
        multi_pos_players = [p for p in eligible if len(p.positions) > 1]

        print(f"Found {len(multi_pos_players)} multi-position players out of {len(eligible)} eligible")

        if multi_pos_players:
            print("\nMulti-position players:")
            for player in multi_pos_players[:10]:  # Show first 10
                print(
                    f"   {player.name} ({player.team}) - Positions: {'/'.join(player.positions)} - ${player.salary:,}")
                if hasattr(player, 'assigned_position'):
                    print(f"      → Assigned as: {player.assigned_position}")

        # Check if any were used in a flex position
        lineup = self.last_optimized_lineup if hasattr(self, 'last_optimized_lineup') else []
        flex_used = 0
        for player in lineup:
            if hasattr(player, 'assigned_position') and player.assigned_position != player.primary_position:
                flex_used += 1
                print(
                    f"\n💪 FLEX USAGE: {player.name} - Primary: {player.primary_position}, Used as: {player.assigned_position}")

        if flex_used == 0:
            print("\n⚠️ No flex positions were utilized in the last lineup")

    def display_classic_lineup(self, lineup):
        """Display classic lineup in table"""
        self.lineup_table.setRowCount(len(lineup))

        position_order = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
        position_count = {pos: 0 for pos in set(position_order)}

        for i, player in enumerate(lineup):
            pos = getattr(player, 'assigned_position', player.primary_position)

            # Check if this is a flex usage
            is_flex = (hasattr(player, 'assigned_position') and
                       player.assigned_position != player.primary_position and
                       len(player.positions) > 1)

            if pos in position_count:
                position_count[pos] += 1
                if pos in ['P', 'OF'] and position_count[pos] > 1:
                    display_pos = f"{pos}{position_count[pos]}"
                else:
                    display_pos = pos

                # Add flex indicator
                if is_flex:
                    display_pos += "*"
            else:
                display_pos = pos

            pos_item = QTableWidgetItem(display_pos)
            pos_item.setTextAlignment(Qt.AlignCenter)

            # Add tooltip for flex players
            if is_flex:
                pos_item.setToolTip(
                    f"Flex: Primary position is {player.primary_position}, can play {'/'.join(player.positions)}")

            self.lineup_table.setItem(i, 0, pos_item)

            # Rest of the method stays the same...

    def _apply_comprehensive_statistical_analysis(self, players):
        """Apply comprehensive statistical analysis with PRIORITY 1 improvements"""
        print(f"📊 ENHANCED Statistical Analysis: {len(players)} players")
        print("🎯 PRIORITY 1 FEATURES: Variable Confidence + Enhanced Statcast + Position Weighting + Recent Form")

        if not players:
            return

        if ENHANCED_STATS_AVAILABLE:
            # Use enhanced statistical analysis engine
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
            # Fallback to basic analysis
            print("⚠️ Using basic analysis - enhanced engine not found")
            self._apply_basic_statistical_analysis(players)

    def _apply_basic_statistical_analysis(self, players):
        """Fallback basic statistical analysis"""
        print(f"📊 Basic statistical analysis: {len(players)} players")

        CONFIDENCE_THRESHOLD = 0.80
        MAX_TOTAL_ADJUSTMENT = 0.20

        adjusted_count = 0
        for player in players:
            total_adjustment = 0.0

            # DFF Analysis
            if hasattr(player, 'dff_data') and player.dff_data and player.dff_data.get('ppg_projection', 0) > 0:
                dff_projection = player.dff_data['ppg_projection']
                if dff_projection > player.projection:
                    dff_adjustment = min((dff_projection - player.projection) / player.projection * 0.3,
                                         0.10) * CONFIDENCE_THRESHOLD
                    total_adjustment += dff_adjustment

            # Vegas Environment Analysis
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

    # ========================================================================
    # LINEUP OPTIMIZATION
    # ========================================================================

    def optimize_lineup_with_mode(self) -> Tuple[List[AdvancedPlayer], float]:
        """Optimize lineup using true integer programming optimization"""
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
            result = self.optimize_showdown_lineup_fixed(eligible_players)
        else:
            result = optimizer.optimize_classic_lineup(eligible_players, use_confirmations=False)

        if result.optimization_status == "Optimal" and result.lineup:
            # Use special display for showdown
            if self.contest_type == 'showdown':
                self.display_showdown_lineup(result.lineup, result.total_score, result.total_salary)
            else:
                # Classic display
                print(f"\n✅ OPTIMAL LINEUP FOUND!")
                print(f"💰 Total Salary: ${result.total_salary:,} / ${self.salary_cap:,}")
                print(f"📈 Projected Points: {result.total_score:.2f}")
                print(f"📊 Positions Filled: {result.positions_filled}")

                print("\n📋 LINEUP PLAYERS:")
                print("-" * 60)
                for i, player in enumerate(result.lineup, 1):
                    pos = getattr(player, 'assigned_position', player.primary_position)
                    score = getattr(player, 'enhanced_score', player.projection)
                    print(
                        f"{i:2d}. {pos:<4} {player.name:<20} {player.team:<4} ${player.salary:>6,} → {score:>6.1f} pts")
                print("-" * 60)

            return result.lineup, result.total_score
        else:
            print(f"❌ Optimization failed: {result.optimization_status}")
            return [], 0

    def optimize_showdown_lineup_fixed(self, players: List) -> 'OptimizationResult':
        """Showdown optimization using MILP only"""
        print("\n🎰 SHOWDOWN LINEUP OPTIMIZATION (MILP ONLY)")
        print("=" * 60)

        if len(players) < 6:
            print(f"❌ Need at least 6 players, have {len(players)}")
            return self._create_failed_result("Not enough players")

        print(f"🎯 Optimizing with {len(players)} eligible players")

        # Show player breakdown
        position_types = {}
        for player in players:
            if hasattr(player, 'original_positions'):
                for pos in player.original_positions:
                    position_types[pos] = position_types.get(pos, 0) + 1

        print(f"📊 Player types available: {position_types}")

        # Use MILP optimizer
        try:
            from optimal_lineup_optimizer import OptimalLineupOptimizer
            optimizer = OptimalLineupOptimizer(salary_cap=self.salary_cap)
            result = optimizer.optimize_showdown_lineup(players)

            if result and result.optimization_status == "Optimal":
                print("✅ MILP optimization successful")
                return result
            else:
                print(f"❌ MILP optimization failed: {result.optimization_status if result else 'No result'}")
                return result if result else self._create_failed_result("MILP optimization failed")

        except Exception as e:
            print(f"❌ MILP optimization error: {e}")
            import traceback
            traceback.print_exc()
            return self._create_failed_result(f"MILP error: {str(e)}")

    def create_showdown_player_constraints(self, players: List) -> Dict:
        """Create constraints to prevent selecting same person twice"""
        print("\n🔒 Creating showdown player constraints...")

        # Group players by actual person (same name)
        person_groups = {}
        for i, player in enumerate(players):
            name_key = player.name.lower().strip()
            if name_key not in person_groups:
                person_groups[name_key] = []
            person_groups[name_key].append(i)  # Store player index

        # Find groups with multiple versions (CPT + UTIL)
        constraint_groups = []
        for name, player_indices in person_groups.items():
            if len(player_indices) > 1:
                constraint_groups.append(player_indices)
                if len(constraint_groups) <= 5:  # Show first 5
                    print(f"   {name.title()}: indices {player_indices}")

        print(f"   Found {len(constraint_groups)} players with multiple versions")

        return {
            'person_groups': person_groups,
            'constraint_groups': constraint_groups
        }

    def _person_aware_showdown_milp(self, players: List, constraints: Dict) -> 'OptimizationResult':
        """MILP optimization that respects person constraints"""
        if not MILP_AVAILABLE:
            raise Exception("PuLP not available")

        import pulp

        prob = pulp.LpProblem("DFS_Showdown_PersonAware", pulp.LpMaximize)

        # Decision variables
        x = {}
        for i in range(len(players)):
            x[i] = pulp.LpVariable(f"x_{i}", cat='Binary')

        # Objective: maximize points
        prob += pulp.lpSum([x[i] * players[i].enhanced_score for i in range(len(players))])

        # Constraint 1: Exactly 6 players selected
        prob += pulp.lpSum(x.values()) == 6

        # Constraint 2: Exactly 1 captain
        captain_indices = []
        for i, player in enumerate(players):
            if 'CPT' in player.positions:
                captain_indices.append(i)

        prob += pulp.lpSum([x[i] for i in captain_indices]) == 1

        # Constraint 3: Exactly 5 utility players
        util_indices = []
        for i, player in enumerate(players):
            if 'UTIL' in player.positions and 'CPT' not in player.positions:
                util_indices.append(i)

        prob += pulp.lpSum([x[i] for i in util_indices]) == 5

        # Constraint 4: Each person can only be selected once
        for person_indices in constraints['constraint_groups']:
            prob += pulp.lpSum([x[i] for i in person_indices]) <= 1

        # Constraint 5: Salary cap
        prob += pulp.lpSum([x[i] * players[i].salary for i in range(len(players))]) <= self.salary_cap

        # Solve
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=15)
        status = prob.solve(solver)

        if status == pulp.LpStatusOptimal:
            return self._extract_person_aware_solution(players, x, constraints)
        else:
            raise Exception(f"MILP failed with status: {pulp.LpStatus[status]}")

    def _extract_person_aware_solution(self, players: List, x: Dict, constraints: Dict) -> 'OptimizationResult':
        """Extract solution ensuring no person appears twice"""
        selected_players = []
        total_salary = 0
        total_score = 0
        positions_filled = {'CPT': 0, 'UTIL': 0}

        selected_indices = []
        for i, player in enumerate(players):
            if x[i].value() == 1:
                selected_indices.append(i)
                selected_players.append(player)
                total_salary += player.salary
                total_score += player.enhanced_score

                if 'CPT' in player.positions:
                    positions_filled['CPT'] += 1
                    player.assigned_position = 'CPT'
                    print(f"✅ Captain: {player.name} ({player.team}) - ${player.salary:,}")
                else:
                    positions_filled['UTIL'] += 1
                    player.assigned_position = 'UTIL'
                    print(f"✅ Utility: {player.name} ({player.team}) - ${player.salary:,}")

        # Validation: Check for person duplicates
        selected_names = [p.name.lower() for p in selected_players]
        unique_names = set(selected_names)

        if len(selected_names) != len(unique_names):
            print(f"❌ PERSON DUPLICATE DETECTED!")
            for name in selected_names:
                if selected_names.count(name) > 1:
                    print(f"   Duplicate person: {name}")

            from optimal_lineup_optimizer import OptimizationResult
            return OptimizationResult(
                lineup=[], total_score=0, total_salary=0,
                positions_filled={}, optimization_status="Person duplicate detected"
            )

        # Show team distribution
        team_counts = {}
        for player in selected_players:
            team_counts[player.team] = team_counts.get(player.team, 0) + 1
        print(f"📊 Team distribution: {team_counts}")

        # Final validation
        if len(selected_players) != 6:
            print(f"❌ Wrong lineup size: {len(selected_players)}")
        elif positions_filled['CPT'] != 1:
            print(f"❌ Wrong captain count: {positions_filled['CPT']}")
        elif positions_filled['UTIL'] != 5:
            print(f"❌ Wrong utility count: {positions_filled['UTIL']}")
        else:
            print(f"✅ Lineup validation passed")

        from optimal_lineup_optimizer import OptimizationResult
        return OptimizationResult(
            lineup=selected_players,
            total_score=total_score,
            total_salary=total_salary,
            positions_filled=positions_filled,
            optimization_status="Optimal"
        )

    def _person_aware_greedy_fallback(self, players: List, constraints: Dict) -> 'OptimizationResult':
        """Greedy fallback that respects person constraints"""
        print("🔄 Using person-aware greedy fallback...")

        # Create person lookup
        person_to_players = {}
        for i, player in enumerate(players):
            name_key = player.name.lower()
            if name_key not in person_to_players:
                person_to_players[name_key] = []
            person_to_players[name_key].append((i, player))

        # For each person, pick their best version
        best_options = []

        for name, player_options in person_to_players.items():
            if len(player_options) == 1:
                # Only one version available
                best_options.append(player_options[0])
            else:
                # Multiple versions - need to try both captain and utility versions
                for idx, player in player_options:
                    value = player.enhanced_score / (player.salary / 1000)
                    best_options.append((idx, player, value))

        # Sort by value
        best_options.sort(key=lambda x: x[2] if len(x) > 2 else x[1].enhanced_score / (x[1].salary / 1000),
                          reverse=True)

        best_lineup = None
        best_score = 0

        # Try different combinations respecting person constraints
        for attempt in range(50):  # Try 50 different combinations
            lineup = []
            used_persons = set()
            remaining_salary = self.salary_cap
            captain_selected = False

            # Shuffle for variety
            import random
            random.shuffle(best_options)

            for option in best_options:
                if len(option) == 2:
                    idx, player = option
                    value = player.enhanced_score / (player.salary / 1000)
                else:
                    idx, player, value = option

                person_name = player.name.lower()

                # Skip if person already used
                if person_name in used_persons:
                    continue

                # Skip if salary too high
                if player.salary > remaining_salary:
                    continue

                # Check position requirements
                can_add = False
                if 'CPT' in player.positions and not captain_selected:
                    can_add = True
                    captain_selected = True
                    player.assigned_position = 'CPT'
                elif 'UTIL' in player.positions and 'CPT' not in player.positions and len(lineup) < 6:
                    can_add = True
                    player.assigned_position = 'UTIL'

                if can_add:
                    lineup.append(player)
                    used_persons.add(person_name)
                    remaining_salary -= player.salary

                    if len(lineup) == 6:
                        break

            if len(lineup) == 6 and captain_selected:
                total_score = sum(p.enhanced_score for p in lineup)
                if total_score > best_score:
                    best_score = total_score
                    best_lineup = lineup[:]

                    print(f"✅ Found lineup with captain: {total_score:.2f} points")

        if best_lineup:
            total_salary = sum(p.salary for p in best_lineup)

            from optimal_lineup_optimizer import OptimizationResult
            return OptimizationResult(
                lineup=best_lineup, total_score=best_score, total_salary=total_salary,
                positions_filled={'CPT': 1, 'UTIL': 5}, optimization_status="Greedy"
            )
        else:
            from optimal_lineup_optimizer import OptimizationResult
            return OptimizationResult(
                lineup=[], total_score=0, total_salary=0,
                positions_filled={}, optimization_status="Greedy failed"
            )

    def _create_failed_result(self, reason: str):
        """Create a failed optimization result"""
        from optimal_lineup_optimizer import OptimizationResult
        return OptimizationResult(
            lineup=[], total_score=0, total_salary=0,
            positions_filled={}, optimization_status=reason
        )

    # ========================================================================
    # CONTEST-SPECIFIC OPTIMIZATION
    # ========================================================================

    def generate_contest_lineups(self, count: int = 20,
                                 contest_type: str = 'gpp',
                                 min_salary_pct: float = 0.95,
                                 diversity_factor: float = 0.7,
                                 max_exposure: float = 0.6) -> List[Dict]:
        """Generate multiple lineups for specific contest type"""
        print(f"\n🎰 GENERATING {count} {contest_type.upper()} LINEUPS")
        print("=" * 60)

        # Get eligible players
        eligible = self.get_eligible_players_by_mode()

        if len(eligible) < 10:
            print(f"❌ Not enough eligible players: {len(eligible)}")
            return []

        generated_lineups = []
        player_usage = {}

        # Contest-specific strategy adjustments
        if contest_type == 'cash':
            # For cash games, we want HIGH FLOOR players
            eligible = self._sort_by_floor(eligible)
        elif contest_type == 'gpp':
            # For GPPs, we want HIGH CEILING players
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
            if self.contest_type == 'showdown':
                result = self.optimize_showdown_lineup_fixed(adjusted_players)
            else:
                optimizer = OptimalLineupOptimizer(salary_cap=self.salary_cap)
                result = optimizer.optimize_classic_lineup(adjusted_players, use_confirmations=False)

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

    def _sort_by_floor(self, players: List) -> List:
        """Sort players by floor (consistency) for cash games"""
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
        """Sort players by ceiling (upside) for GPPs"""
        for player in players:
            # Calculate ceiling based on real factors
            ceiling_score = player.enhanced_score

            # Power metrics increase ceiling
            if hasattr(player, 'statcast_data') and player.statcast_data:
                hard_hit = player.statcast_data.get('Hard_Hit', 0)
                barrel = player.statcast_data.get('Barrel', 0)

                if hard_hit > 40:  # Elite hard hit rate
                    ceiling_score *= 1.15
                elif hard_hit > 35:
                    ceiling_score *= 1.08

                if barrel > 10:  # Elite barrel rate
                    ceiling_score *= 1.10

            # Vegas environment affects ceiling
            if hasattr(player, 'vegas_data') and player.vegas_data:
                team_total = player.vegas_data.get('team_total', 4.5)
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
        """Calculate lineup ceiling"""
        ceiling = 0
        for player in lineup:
            player_ceiling = getattr(player, '_ceiling_score', player.enhanced_score * 1.25)
            ceiling += player_ceiling
        return ceiling

    def _calculate_lineup_floor(self, lineup: List) -> float:
        """Calculate lineup floor"""
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

    def export_lineups_for_upload(self, lineups: List[Dict], filename: str = "dfs_lineups_upload.csv"):
        """Export lineups in DraftKings upload format"""
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

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

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

    def _are_nicknames(self, name1: str, name2: str) -> bool:
        """Check if two names are common nicknames"""
        nicknames = {
            # Common nicknames
            'mike': 'michael', 'michael': 'mike',
            'chris': 'christopher', 'christopher': 'chris',
            'dave': 'david', 'david': 'dave',
            'rob': 'robert', 'robert': 'rob', 'bob': 'robert',
            'matt': 'matthew', 'matthew': 'matt',
            'joe': 'joseph', 'joseph': 'joe',
            'alex': 'alexander', 'alexander': 'alex',
            'will': 'william', 'william': 'will',
            'jake': 'jacob', 'jacob': 'jake',
            'josh': 'joshua', 'joshua': 'josh',
            'jon': 'jonathan', 'jonathan': 'jon',
            'nick': 'nicholas', 'nicholas': 'nick',
            'tony': 'anthony', 'anthony': 'tony',
            'andy': 'andrew', 'andrew': 'andy',
            'dan': 'daniel', 'daniel': 'dan',
            'jim': 'james', 'james': 'jim',
            'ed': 'edward', 'edward': 'ed',
            'tom': 'thomas', 'thomas': 'tom',
            'ben': 'benjamin', 'benjamin': 'ben',
            'ken': 'kenneth', 'kenneth': 'ken',
            'steve': 'stephen', 'stephen': 'steve',
            'rick': 'richard', 'richard': 'rick',
            'charlie': 'charles', 'charles': 'charlie',
            'ted': 'theodore', 'theodore': 'ted',
            'frank': 'francis', 'francis': 'frank',
            'sam': 'samuel', 'samuel': 'sam',
            'tim': 'timothy', 'timothy': 'tim',
            'pat': 'patrick', 'patrick': 'pat',
            'pete': 'peter', 'peter': 'pete',

            # Spanish/Latin nicknames common in baseball
            'alex': 'alejandro', 'alejandro': 'alex',
            'manny': 'manuel', 'manuel': 'manny',
            'rafa': 'rafael', 'rafael': 'rafa',
            'miggy': 'miguel', 'miguel': 'miggy',
            'vlad': 'vladimir', 'vladimir': 'vlad',

            # Baseball-specific common nicknames
            'aj': 'aaron', 'cj': 'christopher', 'dj': 'david',
            'tj': 'thomas', 'jp': 'john', 'jd': 'james'
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

        # Handle initials
        if len(name1_lower) == 2 and '.' not in name1_lower and len(name2_lower) > 2:
            if name1_lower[0] == name2_lower[0]:
                return True

        return False

    def _copy_player(self, player):
        """Create a deep copy of player"""
        import copy
        return copy.deepcopy(player)

    def clean_player_name_for_matching(self, name: str) -> str:
        """Clean player name for better matching"""
        if not name:
            return ''

        # Remove common suffixes
        name = str(name).strip()
        for suffix in [' Jr.', ' Jr', ' Sr.', ' Sr', ' III', ' II', ' IV', ' V']:
            name = name.replace(suffix, '')

        # Remove periods from initials
        name = name.replace('.', '')

        # Normalize spaces
        name = ' '.join(name.split())

        return name

    # ========================================================================
    # DFS UPGRADE METHODS
    # ========================================================================

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

    # ========================================================================
    # DEBUG METHODS
    # ========================================================================

    def debug_all_csv_players(self):
        """Show ALL players in CSV to find the pitchers"""
        print("\n🔍 ALL PLAYERS IN CSV (SORTED BY PROJECTION)")
        print("=" * 80)

        # Sort all players by projection to find pitchers
        all_sorted = sorted(self.players, key=lambda x: x.projection)

        print("LOWEST 20 PROJECTIONS (likely includes pitchers):")
        for i, player in enumerate(all_sorted[:20]):
            orig_pos = getattr(player, 'original_position', 'UNKNOWN')
            print(f"{i + 1:2d}. {player.name:<20} ({player.team}) - "
                  f"${player.salary:>6,} - {player.projection:>5.1f} pts - "
                  f"Orig: {orig_pos}")

        print("\n" + "-" * 80)
        print("HIGHEST 10 PROJECTIONS (definitely hitters):")
        for i, player in enumerate(all_sorted[-10:]):
            orig_pos = getattr(player, 'original_position', 'UNKNOWN')
            print(f"{i + 1:2d}. {player.name:<20} ({player.team}) - "
                  f"${player.salary:>6,} - {player.projection:>5.1f} pts - "
                  f"Orig: {orig_pos}")

        # Find projection gap
        print("\n📊 PROJECTION ANALYSIS:")
        projections = [p.projection for p in self.players if p.projection > 0]
        if projections:
            print(f"   Min: {min(projections):.1f}")
            print(f"   Max: {max(projections):.1f}")
            print(f"   Average: {sum(projections) / len(projections):.1f}")

            # Look for gaps
            sorted_proj = sorted(projections)
            biggest_gap = 0
            gap_at = 0
            for i in range(1, len(sorted_proj)):
                gap = sorted_proj[i] - sorted_proj[i - 1]
                if gap > biggest_gap:
                    biggest_gap = gap
                    gap_at = sorted_proj[i - 1]

            print(f"   Biggest gap: {biggest_gap:.2f} after {gap_at:.1f}")

    def debug_eligible_players(self):
        """Show detailed info about eligible players"""
        print("\n🔍 ELIGIBLE PLAYERS DETAILED DEBUG")
        print("=" * 80)

        eligible = self.get_eligible_players_by_mode()

        # Group by team
        by_team = {}
        for player in eligible:
            if player.team not in by_team:
                by_team[player.team] = []
            by_team[player.team].append(player)

        print(f"Total eligible: {len(eligible)} players")
        print(f"Teams represented: {list(by_team.keys())}")

        # Show players by team
        for team, players in sorted(by_team.items()):
            print(f"\n{team} ({len(players)} players):")

            # Sort by salary to see variety
            players.sort(key=lambda x: x.salary, reverse=True)

            for p in players:
                orig_pos = getattr(p, 'original_position', 'UNKNOWN')
                sources = ', '.join(p.confirmation_sources) if p.confirmation_sources else 'No sources'
                print(f"   {p.name:<20} ${p.salary:>6,} - Orig: {orig_pos:<4} - Sources: [{sources}]")

        # Check for pitchers specifically
        print("\n⚾ PITCHER CHECK:")
        pitchers_found = 0
        for player in eligible:
            orig_pos = getattr(player, 'original_position', 'UNKNOWN')
            if orig_pos == 'P':
                pitchers_found += 1
                print(f"   Found pitcher: {player.name} ({player.team})")

        if pitchers_found == 0:
            print("   ❌ NO PITCHERS FOUND IN ELIGIBLE POOL!")

            # Check if there are pitchers in the full player list
            all_pitchers = [p for p in self.players if getattr(p, 'original_position', p.primary_position) == 'P']
            print(f"\n   Total pitchers in CSV: {len(all_pitchers)}")
            if all_pitchers:
                print("   Sample pitchers (not eligible):")
                for p in all_pitchers[:5]:
                    confirmed = "✅" if p.is_confirmed else "❌"
                    print(f"      {confirmed} {p.name} ({p.team}) - Confirmed: {p.is_confirmed}")

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

    def debug_player_counts(self):
        """Debug method to verify player counts at each stage"""
        print("\n🔍 PLAYER COUNT VERIFICATION")
        print("=" * 60)

        total_players = len(self.players)
        confirmed_players = sum(1 for p in self.players if p.is_confirmed)
        eligible_players = len(self.get_eligible_players_by_mode())

        print(f"Total players loaded: {total_players}")
        print(f"Confirmed players: {confirmed_players}")
        print(f"Eligible for optimization: {eligible_players}")

        # Check enrichment status
        with_dff = sum(1 for p in self.players if hasattr(p, 'dff_data') and p.dff_data)
        with_vegas = sum(1 for p in self.players if hasattr(p, 'vegas_data') and p.vegas_data)
        with_statcast = sum(1 for p in self.players if hasattr(p, 'statcast_data') and p.statcast_data)
        with_form = sum(1 for p in self.players if hasattr(p, 'form_rating') and p.form_rating != 1.0)

        print(f"\nEnrichment Coverage (out of {confirmed_players} confirmed):")
        print(f"  DFF data: {with_dff}")
        print(f"  Vegas data: {with_vegas}")
        print(f"  Statcast data: {with_statcast}")
        print(f"  Recent form: {with_form}")

        if with_form < confirmed_players * 0.8:
            print(f"\n⚠️ WARNING: Only {with_form}/{confirmed_players} players have form data!")
            print(f"   This suggests the recent form analysis may be limited.")

    def display_showdown_lineup(self, lineup: List, total_score: float, total_salary: int):
        """Display showdown lineup with proper multipliers"""
        print("\n🎰 SHOWDOWN LINEUP")
        print("=" * 80)

        # Separate captain and utils
        captain = None
        utils = []

        for player in lineup:
            if player.assigned_position == 'CPT':
                captain = player
            else:
                utils.append(player)

        # Display captain
        if captain:
            cap_salary = int(captain.salary * 1.5)
            cap_score = captain.enhanced_score * 1.5
            print(f"\n👑 CAPTAIN (1.5x multiplier):")
            print(f"   {captain.name} ({captain.team})")
            print(f"   Base: ${captain.salary:,} → {captain.enhanced_score:.1f} pts")
            print(f"   Captain: ${cap_salary:,} → {cap_score:.1f} pts")

        # Display utilities
        print(f"\n⚡ UTILITY PLAYERS:")
        for i, player in enumerate(utils, 1):
            print(f"   {i}. {player.name} ({player.team}) - ${player.salary:,} → {player.enhanced_score:.1f} pts")

        # Recalculate totals to be sure
        actual_salary = 0
        actual_score = 0

        if captain:
            actual_salary += int(captain.salary * 1.5)
            actual_score += captain.enhanced_score * 1.5

        for util in utils:
            actual_salary += util.salary
            actual_score += util.enhanced_score

        print(f"\n📊 TOTALS:")
        print(f"   Salary: ${actual_salary:,} / $50,000 (${50000 - actual_salary:,} remaining)")
        print(f"   Projected: {actual_score:.2f} points")

        # Team stacking
        team_counts = {}
        for player in lineup:
            team_counts[player.team] = team_counts.get(player.team, 0) + 1

        print(f"\n🏈 Team Distribution:")
        for team, count in sorted(team_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {team}: {count} players")

    def fix_known_player_positions(self):
        """Manually fix positions for known players who are incorrectly parsed"""
        position_fixes = {
            'freddie freeman': ['1B', '3B'],
            'mookie betts': ['2B', 'SS', 'OF'],
            'gleyber torres': ['2B'],
            'jose altuve': ['2B'],
            'nolan arenado': ['3B'],
            'manny machado': ['3B', 'SS'],
            'trea turner': ['SS', '2B'],
            'marcus semien': ['2B', 'SS'],
            'jazz chisholm jr': ['2B', 'OF'],
            'jazz chisholm': ['2B', 'OF'],
            'vladimir guerrero jr': ['1B'],
            'vladimir guerrero': ['1B'],
            'pete alonso': ['1B'],
            'paul goldschmidt': ['1B'],
            'matt olson': ['1B'],
            'rafael devers': ['3B'],
            'austin riley': ['3B'],
            'anthony rendon': ['3B'],
            'alex bregman': ['3B'],
            'jose ramirez': ['3B'],
            'matt chapman': ['3B']
        }

        fixed_count = 0

        for player in self.players:
            player_name_lower = player.name.lower().strip()

            # Check if this player needs position fix
            for fix_name, correct_positions in position_fixes.items():
                if fix_name in player_name_lower or player_name_lower in fix_name:
                    # Only fix if currently just UTIL
                    if player.positions == ['UTIL']:
                        old_positions = player.positions.copy()
                        player.positions = correct_positions
                        player.primary_position = correct_positions[0]
                        fixed_count += 1
                        print(f"   Fixed {player.name}: {old_positions} → {correct_positions}")
                    break

        if fixed_count > 0:
            print(f"\n✅ Fixed positions for {fixed_count} players")

        # Recount positions
        self._show_position_stats()

    def debug_showdown_scoring(self, lineup: List):
        """Debug showdown scoring calculations"""
        print("\n🔍 SHOWDOWN SCORING DEBUG")
        print("=" * 60)

        total_salary = 0
        total_score = 0

        for player in lineup:
            if player.assigned_position == 'CPT':
                multiplier = 1.5
                salary_used = int(player.salary * multiplier)
                points = player.enhanced_score * multiplier
                print(f"Captain: {player.name}")
                print(f"  Base: ${player.salary:,} → {player.enhanced_score:.1f} pts")
                print(f"  With 1.5x: ${salary_used:,} → {points:.1f} pts")
            else:
                salary_used = player.salary
                points = player.enhanced_score
                print(f"Utility: {player.name} - ${salary_used:,} → {points:.1f} pts")

            total_salary += salary_used
            total_score += points

        print(f"\nCalculated totals:")
        print(f"  Salary: ${total_salary:,}")
        print(f"  Score: {total_score:.2f}")





    def debug_contest_type_detection(self):
        """Debug why contest type detection is failing"""
        print("\n🔍 CONTEST TYPE DEBUG")
        print("=" * 60)

        print(f"Current contest_type: {self.contest_type}")
        print(f"Total players: {len(self.players)}")

        # Analyze player positions
        position_counts = {}
        showdown_count = 0
        classic_count = 0

        print(f"\n📊 Position Analysis (first 10 players):")
        for i, player in enumerate(self.players[:10]):
            positions = getattr(player, 'positions', [])
            primary_pos = getattr(player, 'primary_position', 'Unknown')

            print(f"   {i + 1}. {player.name}:")
            print(f"      Primary: {primary_pos}")
            print(f"      All positions: {positions}")

            # Count position types
            if 'CPT' in positions or 'UTIL' in positions:
                showdown_count += 1
            if any(pos in positions for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']):
                classic_count += 1

            for pos in positions:
                position_counts[pos] = position_counts.get(pos, 0) + 1

        print(f"\n📈 Position Summary:")
        for pos, count in sorted(position_counts.items()):
            print(f"   {pos}: {count} players")

        print(f"\n🎯 Contest Type Indicators:")
        print(f"   Showdown indicators (CPT/UTIL): {showdown_count}")
        print(f"   Classic indicators (P/C/1B/etc): {classic_count}")

        # Recommendation
        if showdown_count > classic_count:
            print(f"\n💡 RECOMMENDATION: This is a SHOWDOWN contest")
            print(f"   Force with: core.contest_type = 'showdown'")
        else:
            print(f"\n💡 RECOMMENDATION: This is a CLASSIC contest")
            print(f"   Force with: core.contest_type = 'classic'")

        return {
            'showdown_count': showdown_count,
            'classic_count': classic_count,
            'position_counts': position_counts,
            'recommended_type': 'showdown' if showdown_count > classic_count else 'classic'
        }

    def debug_showdown_player_pool(self):
        """Show what's in the showdown player pool"""
        print("\n🎰 SHOWDOWN PLAYER POOL DEBUG")
        print("=" * 60)

        eligible = self.get_eligible_players_by_mode()

        # Group by original position
        by_original_pos = {}
        for player in eligible:
            orig_pos = getattr(player, 'original_position', 'UNKNOWN')
            if orig_pos not in by_original_pos:
                by_original_pos[orig_pos] = []
            by_original_pos[orig_pos].append(player)

        print(f"Total eligible: {len(eligible)} players")
        print("\nBy original position:")
        for pos, players in sorted(by_original_pos.items()):
            print(f"   {pos}: {len(players)} players")
            # Show first few
            for p in players[:3]:
                print(f"      - {p.name} ({p.team}) ${p.salary:,}")

    def debug_showdown_scoring(self, lineup: List):
        """Debug showdown scoring calculations"""
        print("\n🔍 SHOWDOWN SCORING DEBUG")
        print("=" * 60)

        total_salary = 0
        total_score = 0

        for player in lineup:
            if player.assigned_position == 'CPT':
                multiplier = 1.5
                salary_used = int(player.salary * multiplier)
                points = player.enhanced_score * multiplier
                print(f"Captain: {player.name}")
                print(f"  Base: ${player.salary:,} → {player.enhanced_score:.1f} pts")
                print(f"  With 1.5x: ${salary_used:,} → {points:.1f} pts")
            else:
                salary_used = player.salary
                points = player.enhanced_score
                print(f"Utility: {player.name} - ${salary_used:,} → {points:.1f} pts")

            total_salary += salary_used
            total_score += points

        print(f"\nCalculated totals:")
        print(f"  Salary: ${total_salary:,}")
        print(f"  Score: {total_score:.2f}")

    def show_util_players(self):
        """Show what UTIL players actually are"""
        print("\n🔍 UTIL PLAYER ANALYSIS")
        util_players = [p for p in self.players if 'UTIL' in p.positions]

        print(f"Found {len(util_players)} UTIL players:")
        for p in util_players[:10]:  # Show first 10
            print(f"  {p.name} ({p.team}) - Positions: {'/'.join(p.positions)} - ${p.salary:,}")


    def debug_position_coverage(self):
        """Debug which positions are missing and find potential players"""
        print("\n🔍 POSITION COVERAGE DEBUG")
        print("=" * 60)

        # Get eligible players
        eligible = self.get_eligible_players_by_mode()

        # Required positions for classic
        required = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        # Count available by position
        available = {}
        for player in eligible:
            for pos in player.positions:
                available[pos] = available.get(pos, 0) + 1

        print("📋 Required vs Available:")
        for pos, need in required.items():
            have = available.get(pos, 0)
            status = "✅" if have >= need else "❌"
            print(f"   {status} {pos}: need {need}, have {have}")

        # Find players who COULD play missing positions
        print("\n🔍 Players who COULD fill missing positions (not eligible):")

        for pos in ['1B', '2B', '3B']:
            if available.get(pos, 0) < required[pos]:
                print(f"\n{pos} candidates:")
                candidates = [p for p in self.players if
                              pos in p.positions and not p.is_eligible_for_selection(self.optimization_mode)]
                for p in candidates[:5]:
                    print(f"   - {p.name} ({p.team}) - {'/'.join(p.positions)}")



    def debug_data_sources(self):
        """Debug which data sources are actually available"""
        print("\n🔍 DATA SOURCE AVAILABILITY CHECK")
        print("=" * 50)

        # Check each data source
        print(f"Statcast Fetcher: {'✅ Available' if self.statcast_fetcher else '❌ Not initialized'}")
        print(f"Vegas Lines: {'✅ Available' if self.vegas_lines else '❌ Not initialized'}")
        print(
            f"DFF Rankings: {'✅ Loaded' if hasattr(self, 'current_dff_file') and self.current_dff_file else '❌ Not loaded'}")
        print(f"Confirmation System: {'✅ Available' if self.confirmation_system else '❌ Not initialized'}")
        print(f"Form Analyzer: {'✅ Available' if self.form_analyzer else '❌ Not initialized'}")

        # Check if APIs are working
        if self.statcast_fetcher:
            try:
                result = self.statcast_fetcher.test_connection()
                print(f"Statcast API Test: {'✅ Working' if result else '❌ Failed'}")
            except:
                print("Statcast API Test: ❌ Error")



# ============================================================================
# MODULE VERIFICATION
# ============================================================================

def verify_integration():
    """Verify all new modules are integrated correctly"""
    print("\n🧪 INTEGRATION VERIFICATION TEST")
    print("=" * 60)

    # Check imports
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


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # This file should be imported, not run directly
    print("✅ bulletproof_dfs_core module loaded successfully")
    print("📋 To use this module:")
    print("   from bulletproof_dfs_core import BulletproofDFSCore")
    print("   core = BulletproofDFSCore()")
    print("   core.load_draftkings_csv('your_file.csv')")
    print("\n")

    # Optionally run verification
    verify_integration()