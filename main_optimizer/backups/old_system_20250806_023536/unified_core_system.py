#!/usr/bin/env python3
"""
UNIFIED CORE SYSTEM - ENHANCED VERSION
=====================================
Complete unified DFS system with new optimized scoring
"""

import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Set, Optional
import pandas as pd
# At the very top of unified_core_system.py
import sys
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fix Python path to find modules in different directories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Add data directory to path
data_dir = os.path.join(parent_dir, 'data')
if data_dir not in sys.path:
    sys.path.insert(0, data_dir)

# Add main_optimizer directory to path (if needed)
main_optimizer_dir = os.path.join(parent_dir, 'main_optimizer')
if os.path.exists(main_optimizer_dir) and main_optimizer_dir not in sys.path:
    sys.path.insert(0, main_optimizer_dir)

# Core imports (these should always work)
from unified_player_model import UnifiedPlayer
from unified_milp_optimizer import UnifiedMILPOptimizer
from enhanced_scoring_engine import EnhancedScoringEngine

# Data enrichment imports with error handling
try:
    from real_data_enrichments import RealStatcastFetcher as SimpleStatcastFetcher
    STATCAST_AVAILABLE = True
    logger.info("✅ Statcast initialized via RealStatcastFetcher")
except ImportError:
    logger.warning("Statcast not available - stats enrichment disabled")
    STATCAST_AVAILABLE = False
    SimpleStatcastFetcher = None

try:
    from smart_confirmation import SmartConfirmationSystem

    CONFIRMATION_AVAILABLE = True
except ImportError:
    logger.warning("Smart confirmation not available")
    CONFIRMATION_AVAILABLE = False
    SmartConfirmationSystem = None

try:
    from vegas_lines import VegasLines

    VEGAS_AVAILABLE = True
except ImportError:
    logger.warning("Vegas lines not available")
    VEGAS_AVAILABLE = False
    VegasLines = None

try:
    from strategy_selector import StrategyAutoSelector

    STRATEGY_AVAILABLE = True
except ImportError:
    logger.warning("Strategy selector not available")
    STRATEGY_AVAILABLE = False
    StrategyAutoSelector = None

try:
    from park_factors import get_park_factor_adjustment
    PARK_FACTORS_AVAILABLE = True
    # Create a wrapper class
    class ParkFactors:
        def get_park_factor(self, team):
            return get_park_factor_adjustment(team)
except ImportError:
    logger.warning("Park factors not available")
    PARK_FACTORS_AVAILABLE = False
    ParkFactors = None

# Optional weather integration
try:
    from weather_integration import WeatherIntegration

    WEATHER_AVAILABLE = True
except ImportError:
    WEATHER_AVAILABLE = False
    WeatherIntegration = None
    logger.warning("Weather integration not available")

# Real data enrichments (if using the advanced version)
try:
    from real_data_enrichments import RealStatcastFetcher, RealWeatherIntegration, RealParkFactors

    REAL_DATA_AVAILABLE = True
except ImportError:
    REAL_DATA_AVAILABLE = False
    RealStatcastFetcher = None
    RealWeatherIntegration = None
    RealParkFactors = None
    logger.warning("Real data enrichments not available")

# Performance tracking
try:
    from performance_tracker import PerformanceTracker

    TRACKING_AVAILABLE = True
except ImportError:
    TRACKING_AVAILABLE = False
    TRACKING_AVAILABLE = False
    PerformanceTracker = None
    logger.warning("Performance tracker not available")

# Showdown optimizer
try:
    from fixed_showdown_optimization import ShowdownOptimizer

    SHOWDOWN_AVAILABLE = True
except ImportError:
    SHOWDOWN_AVAILABLE = False
    ShowdownOptimizer = None
    logger.warning("Showdown optimizer not available - using standard optimizer")


class UnifiedCoreSystem:
    """Main system that coordinates everything"""

    def __init__(self):
        self.players = []
        self.player_pool = []
        self.manual_selections = set()  # ADD THIS LINE
        self.optimizer = UnifiedMILPOptimizer()
        self.scoring_engine = EnhancedScoringEngine()
        self.enrichments_applied = False

        # Initialize optional components
        self.statcast = SimpleStatcastFetcher() if STATCAST_AVAILABLE else None
        self.confirmation_system = SmartConfirmationSystem(verbose=False) if CONFIRMATION_AVAILABLE else None
        self.vegas_lines = VegasLines() if VEGAS_AVAILABLE else None
        self.strategy_selector = StrategyAutoSelector() if STRATEGY_AVAILABLE else None
        self.park_factors = ParkFactors() if PARK_FACTORS_AVAILABLE else None
        self.weather = WeatherIntegration() if WEATHER_AVAILABLE else None
        self.tracker = PerformanceTracker() if TRACKING_AVAILABLE else None

        logger.info(f"UnifiedCoreSystem initialized with:")
        logger.info(f"  - Statcast: {'✓' if STATCAST_AVAILABLE else '✗'}")
        logger.info(f"  - Vegas: {'✓' if VEGAS_AVAILABLE else '✗'}")
        logger.info(f"  - Weather: {'✓' if WEATHER_AVAILABLE else '✗'}")
        logger.info(f"  - Park Factors: {'✓' if PARK_FACTORS_AVAILABLE else '✗'}")
        logger.info(f"  - Confirmations: {'✓' if CONFIRMATION_AVAILABLE else '✗'}")

    def score_player_cash(self, player):
        """Score player for cash games with proper enrichments"""
        # Get base projection
        base = getattr(player, 'base_projection', 0)
        if base == 0:
            base = getattr(player, 'AvgPointsPerGame', 0)

        if base == 0:
            return 0

        # Start with base
        score = base

        # Apply multipliers (ensure they're never 0)
        recent_form = getattr(player, 'recent_form', 1.0)
        consistency = getattr(player, 'consistency_score', 1.0)
        matchup = getattr(player, 'matchup_score', 1.0)

        # Ensure multipliers are reasonable
        recent_form = max(0.8, min(1.2, recent_form))
        consistency = max(0.8, min(1.2, consistency))

        score *= recent_form
        score *= consistency
        score *= matchup

        # Park and weather with reduced impact
        park = getattr(player, 'park_factor', 1.0)
        weather = getattr(player, 'weather_impact', 1.0)

        score *= (1.0 + (park - 1.0) * 0.3)
        score *= (1.0 + (weather - 1.0) * 0.3)

        # Pitcher boost
        if player.is_pitcher and score > 0:
            score *= 1.1

        return round(score, 2)

    def set_manual_selections(self, selections: Set[str]):
        """Set manual player selections"""
        self.manual_selections = selections
        self.log(f"Set {len(selections)} manual selections")

    def log(self, message, level="info"):
        """Unified logging method"""
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)

    def _extract_home_team(self, player):
        """Extract home team from game info like 'KC@BOS'"""
        if hasattr(player, 'game_info') and player.game_info:
            if '@' in player.game_info:
                # Format is AWAY@HOME
                parts = player.game_info.split('@')
                if len(parts) >= 2:
                    return parts[1].split()[0]
        return None

    def enrich_player_pool_with_real_data(self):
        """Enhanced enrichment using REAL data sources with priority filtering"""



        if not self.player_pool:
            return {}

        self.log("🔬 Starting REAL data enrichment...")

        # CHANGE 1: Use the new pybaseball fetcher
        try:
            from real_data_enrichments import RealStatcastFetcher
            self.statcast_fetcher = RealStatcastFetcher()
            self.log("✅ Using pybaseball for real MLB stats", "info")
        except ImportError:
            self.log("❌ real_data_enrichments.py not found!", "error")
            self.statcast_fetcher = None

        # CHANGE 2: Filter to priority players only
        priority_players = []
        default_players = []

        for player in self.player_pool:
            # Priority: confirmed, manual selection, or high salary
            if (getattr(player, 'is_confirmed', False) or
                    player.name in getattr(self, 'manual_selections', set()) or
                    player.salary >= 8000):
                priority_players.append(player)
            else:
                default_players.append(player)

        self.log(
            f"📊 Enriching {len(priority_players)} priority players (skipping {len(default_players)} bench players)")

        # Initialize other data sources
        from vegas_lines import VegasLines
        from weather_integration import WeatherIntegration
        from park_factors import PARK_FACTORS

        self.vegas_fetcher = VegasLines()
        self.weather_fetcher = WeatherIntegration()
        self.park_factors = ParkFactors()

        # Track enrichment results
        enrichment_stats = {
            'vegas': 0,
            'weather': 0,
            'park': 0,
            'stats': 0,
            'consistency': 0,
            'total': len(self.player_pool)
        }

        # CHANGE 3: Process priority players with real data
        for i, player in enumerate(priority_players):
            if i % 10 == 0:
                self.log(f"Processing player {i + 1}/{len(priority_players)}...")

            try:
                # Vegas enrichment
                if self.vegas_fetcher:
                    self.vegas_fetcher.enrich_player(player)
                    if hasattr(player, 'team_total') and player.team_total > 0:
                        enrichment_stats['vegas'] += 1

                # Weather enrichment
                if self.weather_fetcher:
                    weather_data = self.weather_fetcher.get_game_weather(player.team)
                    player.weather_impact = weather_data.get('weather_impact', 1.0)
                    player.game_temperature = weather_data.get('temperature', 72)
                    player.game_wind = weather_data.get('wind_speed', 0)
                    player.is_dome = weather_data.get('is_dome', False)
                    if player.weather_impact != 1.0:
                        enrichment_stats['weather'] += 1

                # Park factors
                if self.park_factors:
                    player.park_factor = self.park_factors.get_park_factor(player.team)
                    if player.park_factor != 1.0:
                        enrichment_stats['park'] += 1

                # CHANGE 4: Real statcast data with proper error handling
                if self.statcast_fetcher and not player.is_pitcher:  # Focus on hitters first
                    try:
                        # Try different day ranges for better coverage
                        recent_stats = None
                        for days in [7, 14, 30]:
                            stats = self.statcast_fetcher.get_recent_stats(player.name, days=days)
                            if stats.get('games_analyzed', 0) > 0:
                                recent_stats = stats
                                break

                        if recent_stats and recent_stats.get('games_analyzed', 0) > 0:
                            # Apply real stats
                            player.recent_form = recent_stats.get('recent_form', 1.0)
                            player.recent_avg = recent_stats.get('batting_avg', 0)
                            player.recent_xba = recent_stats.get('xBA', 0)
                            player.recent_barrel_rate = recent_stats.get('barrel_rate', 0)
                            player.recent_exit_velo = recent_stats.get('avg_exit_velocity', 0)
                            enrichment_stats['stats'] += 1

                            # Also get consistency
                            consistency = self.statcast_fetcher.get_consistency_score(player.name)
                            player.consistency_score = consistency
                            enrichment_stats['consistency'] += 1
                        else:
                            # No recent games - use defaults
                            player.recent_form = 1.0
                            player.consistency_score = 1.0

                    except Exception as e:
                        self.log(f"Stats error for {player.name}: {str(e)}", "debug")
                        player.recent_form = 1.0
                        player.consistency_score = 1.0
                else:
                    # Default for pitchers or if no fetcher
                    player.recent_form = 1.0
                    player.consistency_score = 1.0

            except Exception as e:
                self.log(f"Enrichment error for {player.name}: {str(e)}", "error")
                # Set defaults on error
                player.team_total = 4.5
                player.park_factor = 1.0
                player.weather_impact = 1.0
                player.recent_form = 1.0
                player.consistency_score = 1.0

        # CHANGE 5: Give defaults to non-priority players
        for player in default_players:
            player.team_total = 4.5  # MLB average
            player.park_factor = 1.0
            player.weather_impact = 1.0
            player.recent_form = 1.0
            player.consistency_score = 1.0
            player.ownership_projection = 5.0  # Low ownership for bench players

        # CHANGE 6: Add basic ownership projections
        self._calculate_ownership_projections()

        # Log results
        self.log(f"\n📊 Enrichment Complete:")
        self.log(f"  Priority players enriched: {len(priority_players)}")
        self.log(f"  Vegas data: {enrichment_stats['vegas']}")
        self.log(f"  Weather data: {enrichment_stats['weather']}")
        self.log(f"  Park factors: {enrichment_stats['park']}")
        self.log(f"  Real stats: {enrichment_stats['stats']}")
        self.log(f"  Consistency scores: {enrichment_stats['consistency']}")

        return enrichment_stats



    def debug_ownership_projections(self, top_n=10):
        """Debug method to see ownership projections"""
        if not self.player_pool:
            return

        print("\n=== OWNERSHIP PROJECTIONS ===")
        print(f"{'Player':<20} {'Pos':<4} {'Salary':<8} {'Proj':<6} {'Own%':<6}")
        print("-" * 50)

        # Sort by ownership
        by_ownership = sorted(self.player_pool,
                              key=lambda p: getattr(p, 'ownership_projection', 0),
                              reverse=True)

        for player in by_ownership[:top_n]:
            own = getattr(player, 'ownership_projection', 0)
            print(f"{player.name:<20} {player.primary_position:<4} "
                  f"${player.salary:<7,} {player.base_projection:<6.1f} {own:<5.1f}%")
    # Add your other methods here...
    # (load_players_from_csv, build_player_pool, score_players, optimize_lineups, etc.)

    """
    FIX FOR score_players METHOD
    ============================
    Add this to unified_core_system.py to fix scoring
    """

    def score_players(self, contest_type='gpp'):
        """Score all players using enhanced scoring engine"""
        logger.info(f"Scoring players for {contest_type.upper()}")
        
        # Ensure enrichment has run
        if not self.enrichments_applied:
            logger.info("Running enrichments first...")
            self.enrich_player_pool()
        
        # Use enhanced scoring engine for ALL scoring
        scored_count = 0
        for player in self.player_pool:
            try:
                # Calculate both scores using enhanced engine
                player.cash_score = self.scoring_engine.score_player_cash(player)
                player.gpp_score = self.scoring_engine.score_player_gpp(player)
                
                # DO NOT SET optimization_score HERE!
                # The optimizer will use the appropriate score
                
                scored_count += 1
            except Exception as e:
                logger.error(f"Error scoring {player.name}: {e}")
                player.cash_score = 0
                player.gpp_score = 0
        
        logger.info(f"✅ Scored {scored_count}/{len(self.player_pool)} players successfully")

    def load_players_from_csv(self, csv_path: str):
        """Load players from DraftKings CSV"""
        logger.info(f"Loading players from {csv_path}")

        try:
            df = pd.read_csv(csv_path)

            # DEBUG: Print first row to see actual column names
            if not df.empty:
                print("CSV Columns:", list(df.columns))
                print("First row:", df.iloc[0].to_dict())

            for idx, row in df.iterrows():
                # Extract basic info from CSV
                name = row['Name']
                team = row['TeamAbbrev']
                position = row['Position']
                salary = int(row['Salary'])
                game_info = row.get('Game Info', '')

                # Generate unique ID
                player_id = f"{name.replace(' ', '_')}_{team}".lower()

                # Parse positions (handle multi-position)
                positions = position.split('/')
                primary_position = positions[0]

                # Map pitcher positions to 'P' for optimizer
                if primary_position in ['SP', 'RP']:
                    primary_position = 'P'
                    positions = ['P'] + [p for p in positions if p not in ['SP', 'RP']]

                # Create player object with required parameters including primary_position
                player = UnifiedPlayer(
                    id=player_id,
                    name=name,
                    team=team,
                    positions=positions,
                    salary=salary,
                    primary_position=primary_position  # This is required!
                )

                # Set additional attributes AFTER creation
                player.is_pitcher = (primary_position == 'P')
                player.game_info = game_info

                # Set projections
                base_projection = float(row.get('AvgPointsPerGame', 0))
                player.dff_projection = base_projection
                player.dk_projection = base_projection
                player.projection = base_projection

                # Extract opponent from game info
                if ' ' in game_info:
                    teams_in_game = game_info.split(' ')
                    if team == teams_in_game[0]:
                        player.opponent = teams_in_game[1] if len(teams_in_game) > 1 else 'UNK'
                    else:
                        player.opponent = teams_in_game[0]
                else:
                    player.opponent = 'UNK'

                self.players.append(player)

            # Update teams in confirmation system
            if self.confirmation_system:
                teams = list(set([p.team for p in self.players]))
                self.confirmation_system.teams = teams
                logger.info(f"Updated confirmation system with teams: {teams}")

            self.csv_loaded = True
            logger.info(f"✅ Loaded {len(self.players)} players from CSV")

        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise

    def load_csv(self, csv_path: str) -> List[UnifiedPlayer]:
        """Alias for load_players_from_csv for compatibility"""
        return self.load_players_from_csv(csv_path)

    def fetch_confirmed_players(self) -> Set[str]:
        """Fetch confirmed starting lineups"""
        logger.info("Fetching confirmed players...")

        try:
            # Call get_all_confirmations to fetch data
            self.confirmation_system.get_all_confirmations()

            # Now extract the actual player names
            all_names = []

            # Get pitcher names
            for team, pitcher_info in self.confirmation_system.confirmed_pitchers.items():
                if isinstance(pitcher_info, dict) and 'name' in pitcher_info:
                    all_names.append(pitcher_info['name'])

            # Get position player names
            for team, lineup in self.confirmation_system.confirmed_lineups.items():
                if isinstance(lineup, list):
                    for player in lineup:
                        if isinstance(player, dict) and 'name' in player:
                            all_names.append(player['name'])

            self.confirmed_players = set(all_names)
            logger.info(f"✅ Found {len(self.confirmed_players)} confirmed players")

            if self.confirmed_players and self.csv_loaded:
                # Debug: Show some confirmed names
                logger.info(f"Sample confirmed: {list(self.confirmed_players)[:3]}")

            self.confirmations_fetched = True
            return self.confirmed_players

        except Exception as e:
            logger.warning(f"Could not fetch confirmations: {e}")
            self.confirmed_players = set()
            return self.confirmed_players

    def set_manual_selections(self, player_names: List[str]):
        """Set manual player selections"""
        self.manual_selections = set(player_names)
        logger.info(f"Set {len(self.manual_selections)} manual selections")

    def build_player_pool(self, include_unconfirmed=False):
        """Build the player pool based on confirmations and filters"""
        self.player_pool = []

        if not self.players:
            self.log("No players loaded!", "error")
            return

        # Get confirmed players if available
        confirmed_players = set()
        if self.confirmation_system and hasattr(self, 'confirmed_players'):
            confirmed_players = self.confirmed_players

        for player in self.players:
            # Always include manual selections
            if player.name in self.manual_selections:
                self.player_pool.append(player)
                continue

            # Check confirmation status
            if include_unconfirmed:
                # GPP mode - include all
                self.player_pool.append(player)
            else:
                # Cash mode - only confirmed
                if player.name in confirmed_players:
                    self.player_pool.append(player)

        self.log(f"Built player pool: {len(self.player_pool)} players")

        # Add any missing manual selections
        manual_names = {p.name for p in self.player_pool}
        missing_manual = self.manual_selections - manual_names
        if missing_manual:
            self.log(f"Warning: {len(missing_manual)} manual selections not found in player list", "warning")

    def _calculate_consistency_score(self, player):
        """Calculate consistency score based on player attributes"""
        if player.is_pitcher:
            if player.salary >= 9500:
                return 1.20  # Elite aces
            elif player.salary >= 8000:
                return 1.10  # Quality starters
            elif player.salary >= 6500:
                return 1.00  # Mid-tier
            else:
                return 0.85  # Back-end starters
        else:
            # Hitters
            consistency = 1.0

            # Batting order adjustment
            if hasattr(player, 'batting_order') and player.batting_order:
                if player.batting_order <= 3:
                    consistency *= 1.10
                elif player.batting_order <= 5:
                    consistency *= 1.05
                elif player.batting_order >= 8:
                    consistency *= 0.90

            # Salary adjustment
            if player.salary >= 5000:
                consistency *= 1.05
            elif player.salary <= 3000:
                consistency *= 0.90

            return round(consistency, 2)

    def debug_player_matching(self):
        """Debug method to show why players aren't matching"""
        print("\n" + "=" * 60)
        print("PLAYER MATCHING DEBUG")
        print("=" * 60)

        print(f"\nConfirmed players from API ({len(self.confirmed_players)}):")
        for i, name in enumerate(list(self.confirmed_players)[:10]):
            print(f"  {i + 1}. '{name}'")

        print(f"\nCSV players ({len(self.players)}):")
        for i, player in enumerate(self.players[:10]):
            print(f"  {i + 1}. '{player.name}' - {player.team} - ${player.salary}")

        # Try to find why they don't match
        if self.confirmed_players and self.players:
            conf_name = list(self.confirmed_players)[0]
            csv_name = self.players[0].name

            print(f"\nComparing first entries:")
            print(f"  Confirmed: '{conf_name}' (length: {len(conf_name)})")
            print(f"  CSV:       '{csv_name}' (length: {len(csv_name)})")
            print(f"  Equal: {conf_name == csv_name}")
            print(f"  Equal (lower): {conf_name.lower() == csv_name.lower()}")

            # Check for hidden characters
            print(f"\nChecking for hidden characters:")
            print(f"  Confirmed bytes: {conf_name.encode('utf-8')}")
            print(f"  CSV bytes:       {csv_name.encode('utf-8')}")

    """
    BEST FIX - ADD TO unified_core_system.py
    =========================================
    This preserves your sophisticated scoring system
    """

    """
    COMPLETE FIX FOR SCORING ENGINE
    ===============================
    Add this to unified_core_system.py
    """

    """
    COMPLETE FIX FOR SCORING ENGINE
    ===============================
    Add this to unified_core_system.py
    """

    def enrich_player_pool(self):
        """Enhanced player pool enrichment - uses correct API methods and data structures"""
        if not self.player_pool:
            self.log("No players in pool to enrich")
            return {}

        self.log(f"🔬 Enriching ALL {len(self.player_pool)} players in pool...")

        # Initialize data sources with CORRECT imports
        vegas_fetcher = None
        weather_fetcher = None
        park_factors_fetcher = None
        stats_fetcher = None

        try:
            from vegas_lines import VegasLines
            vegas_fetcher = VegasLines()
            self.log("✅ Vegas module loaded")
        except Exception as e:
            self.log(f"⚠️ Vegas not available: {e}")

        try:
            from real_data_enrichments import RealWeatherIntegration
            weather_fetcher = RealWeatherIntegration()
            self.log("✅ Weather module loaded")
        except Exception as e:
            self.log(f"⚠️ Weather not available: {e}")

        try:
            from park_factors import ParkFactors
            park_factors_fetcher = ParkFactors()
            self.log("✅ Park factors module loaded")
        except Exception as e:
            self.log(f"⚠️ Park factors not available: {e}")

        try:
            from real_data_enrichments import RealStatcastFetcher
            stats_fetcher = RealStatcastFetcher()
            self.log("✅ Statcast module loaded")
        except Exception as e:
            self.log(f"⚠️ Statcast not available: {e}")

        # Track enrichment results
        enrichment_stats = {
            'vegas': 0,
            'weather': 0,
            'park': 0,
            'stats': 0,
            'consistency': 0,
            'total': len(self.player_pool)
        }

        # VEGAS - Handle the dict structure correctly
        if vegas_fetcher:
            try:
                lines = vegas_fetcher.get_vegas_lines()

                if lines and isinstance(lines, dict):
                    for player in self.player_pool:
                        # Set defaults first
                        player.team_total = 4.5
                        player.implied_team_score = 4.5

                        # Check if player's team has data
                        team_data = lines.get(player.team)
                        if team_data and isinstance(team_data, dict):
                            total = team_data.get('total', 4.5)
                            player.team_total = float(total)
                            # Implied team score is roughly half the total
                            player.implied_team_score = float(total) / 2

                            if player.team_total != 4.5:
                                enrichment_stats['vegas'] += 1

            except Exception as e:
                self.log(f"Vegas enrichment error: {e}")
                # Set defaults for all players on error
                for player in self.player_pool:
                    player.team_total = 4.5
                    player.implied_team_score = 4.5

        # Process each player for other enrichments
        for i, player in enumerate(self.player_pool):
            if i % 10 == 0 and i > 0:
                self.log(f"Progress: {i}/{len(self.player_pool)} players enriched...")

            # Ensure defaults are set
            if not hasattr(player, 'implied_team_score'):
                player.implied_team_score = 4.5
            player.weather_impact = 1.0
            player.park_factor = 1.0
            player.recent_form = 1.0
            player.consistency_score = 1.0
            player.matchup_score = 1.0

            # Ensure is_pitcher
            if not hasattr(player, 'is_pitcher'):
                player.is_pitcher = (player.primary_position == 'P')

            try:
                # WEATHER - Use the pre-calculated impact
                if weather_fetcher:
                    try:
                        weather_data = weather_fetcher.get_game_weather(player.team)
                        if weather_data and isinstance(weather_data, dict):
                            # The weather_impact is ALREADY CALCULATED in the data
                            impact = weather_data.get('weather_impact', 1.0)
                            player.weather_impact = float(impact)

                            # Also store other weather data for reference
                            player.game_temperature = weather_data.get('temperature', 72)
                            player.game_wind = weather_data.get('wind_speed', 0)
                            player.is_dome = weather_data.get('is_dome', False)

                            if player.weather_impact != 1.0:
                                enrichment_stats['weather'] += 1
                    except Exception as e:
                        # Silent fail - keep default
                        pass

                # PARK FACTORS
                if park_factors_fetcher:
                    try:
                        factor = park_factors_fetcher.get_park_factor(player.team)
                        if factor and factor != 1.0:
                            player.park_factor = float(factor)
                            enrichment_stats['park'] += 1
                    except:
                        pass

                # CONSISTENCY SCORE
                if hasattr(self, '_calculate_consistency_score'):
                    player.consistency_score = self._calculate_consistency_score(player)
                else:
                    # Simple consistency based on salary
                    if player.is_pitcher:
                        player.consistency_score = 1.1 if player.salary >= 8000 else 0.95
                    else:
                        player.consistency_score = 1.05 if player.salary >= 4500 else 0.90

                if player.consistency_score != 1.0:
                    enrichment_stats['consistency'] += 1

                # BATTING ORDER (for hitters)
                if not player.is_pitcher and not hasattr(player, 'batting_order'):
                    if player.salary >= 5000:
                        player.batting_order = 3
                    elif player.salary >= 4000:
                        player.batting_order = 5
                    elif player.salary >= 3000:
                        player.batting_order = 7
                    else:
                        player.batting_order = 9

            except Exception as e:
                self.log(f"Error enriching {player.name}: {str(e)}")

        # HYBRID RECENT FORM - Real data for stars, estimates for others
        # HYBRID RECENT FORM - Real data for stars, estimates for others
        self.log("Applying hybrid recent form (statcast for top 50%, salary for bottom 50%)...")

        # Sort players by salary to find median
        sorted_players = sorted(self.player_pool, key=lambda p: p.salary, reverse=True)
        median_index = len(sorted_players) // 2
        median_salary = sorted_players[median_index].salary

        self.log(f"Pool size: {len(self.player_pool)} players")
        self.log(f"Median salary: ${median_salary}")
        self.log(f"Getting real stats for players above ${median_salary}")

        # Count for each method
        statcast_count = 0
        salary_based_count = 0
        statcast_attempts = 0

        # PHASE 1: Try statcast for HIGH SALARY players (top 50%)
        for player in sorted_players[:median_index]:  # Top half by salary
            if stats_fetcher and not player.is_pitcher:  # Focus on hitters
                try:
                    statcast_attempts += 1
                    self.log(f"  Fetching stats for {player.name} (${player.salary})...")

                    # NO TIMEOUT - just get the data (7 days only)
                    stats = stats_fetcher.get_recent_stats(player.name, days=7)

                    if stats and stats.get('games_analyzed', 0) > 0:
                        # Apply real stats
                        avg = stats.get('batting_avg', stats.get('avg', 0))
                        ops = stats.get('ops', 0)

                        # More nuanced scoring for premium players
                        if avg > 0.300 or ops > 0.900:
                            player.recent_form = 1.15
                        elif avg > 0.270 or ops > 0.800:
                            player.recent_form = 1.10
                        elif avg > 0.250 or ops > 0.750:
                            player.recent_form = 1.05
                        elif avg < 0.200 or ops < 0.650:
                            player.recent_form = 0.90
                        else:
                            player.recent_form = 1.00

                        statcast_count += 1
                        enrichment_stats['stats'] += 1
                        self.log(f"    ✅ Got stats: AVG={avg:.3f}, Form={player.recent_form}")
                        continue
                    else:
                        # No data returned - use salary fallback
                        self.log(f"    ❌ No stats found, using salary-based")

                except Exception as e:
                    self.log(f"    ❌ Error: {str(e)}, using salary-based")

            # FALLBACK: If statcast failed or no data, use salary-based
            if not hasattr(player, 'recent_form') or player.recent_form == 1.0:
                if player.is_pitcher:
                    player.recent_form = 1.05 if player.salary >= 9000 else 1.02
                else:
                    # High salary hitter without stats
                    if player.salary >= 6000:
                        player.recent_form = 1.08
                    elif player.salary >= 5000:
                        player.recent_form = 1.06
                    else:
                        player.recent_form = 1.04
                salary_based_count += 1
                enrichment_stats['stats'] += 1

        # PHASE 2: Salary-based for LOWER SALARY players (bottom 50%)
        self.log(f"\nApplying salary-based form for players below ${median_salary}...")

        for player in self.player_pool:
            if not hasattr(player, 'recent_form') or player.recent_form == 1.0:
                if not player.is_pitcher:
                    # Value hitters
                    if player.salary >= 4500:
                        player.recent_form = 1.03
                    elif player.salary >= 3500:
                        player.recent_form = 1.00
                    elif player.salary >= 3000:
                        player.recent_form = 0.97
                    else:
                        player.recent_form = 0.92  # Punt plays
                else:
                    # Value pitchers
                    if player.salary >= 6500:
                        player.recent_form = 1.00
                    else:
                        player.recent_form = 0.95

                salary_based_count += 1
                enrichment_stats['stats'] += 1

        # VERIFICATION: Ensure everyone has recent form
        for player in self.player_pool:
            if not hasattr(player, 'recent_form'):
                player.recent_form = 1.0
                self.log(f"⚠️ Missing form for {player.name}, set to 1.0")

        # Summary
        self.log(f"\n📊 Recent Form Summary:")
        self.log(f"  Statcast attempts: {statcast_attempts}")
        self.log(f"  Statcast success: {statcast_count}")
        self.log(f"  Salary-based: {salary_based_count}")
        self.log(f"  Total enriched: {statcast_count + salary_based_count}/{len(self.player_pool)}")
        # Calculate ownership projections if method exists
        if hasattr(self, '_calculate_ownership_projections'):
            self._calculate_ownership_projections()

        # Find value plays
        value_plays = [p for p in self.player_pool
                       if p.salary <= 3500 and p.base_projection > 0
                       and p.base_projection / (p.salary / 1000) > 2.0]

        if value_plays:
            # Show Coors Field players
            coors_players = [p for p in self.player_pool
                             if p.team in ['COL'] or (hasattr(p, 'opponent') and p.opponent == 'COL')]
            for p in sorted(coors_players, key=lambda x: x.salary, reverse=True):
                self.log(f"🏔️ Coors chalk: {p.name}")

            # Show top value plays
            for p in sorted(value_plays, key=lambda x: x.base_projection, reverse=True)[:3]:
                value = p.base_projection / (p.salary / 1000)
                self.log(f"💰 Value chalk: {p.name} (${p.salary}, {p.base_projection} proj)")

        # Mark enrichments as applied
        self.enrichments_applied = True

        # Log final results
        self.log(f"\n✅ Enrichment Complete:")
        self.log(f"  Total players: {len(self.player_pool)}")
        self.log(f"  Vegas data: {enrichment_stats['vegas']}")
        self.log(f"  Weather data: {enrichment_stats['weather']}")
        self.log(f"  Park factors: {enrichment_stats['park']}")
        self.log(f"  Recent stats: {enrichment_stats['stats']}")
        self.log(f"  Consistency: {enrichment_stats['consistency']}")

        # Show sample enriched player
        if self.player_pool:
            sample = self.player_pool[0]
            self.log(f"\n📊 Sample - {sample.name}:")
            self.log(f"  Vegas: {getattr(sample, 'implied_team_score', 'N/A')}")
            self.log(f"  Weather: {getattr(sample, 'weather_impact', 'N/A')}")
            self.log(f"  Park: {getattr(sample, 'park_factor', 'N/A')}")

        return enrichment_stats



    def _calculate_ownership_projections(self):
        """Add basic ownership projections with narrative boosts for GPP strategy use"""
        if not self.player_pool:
            return

        # Sort by salary for percentile calculation
        sorted_by_salary = sorted(self.player_pool, key=lambda p: p.salary, reverse=True)
        salary_percentiles = {p.name: i / len(sorted_by_salary) for i, p in enumerate(sorted_by_salary)}

        # Sort by projection for percentile calculation
        sorted_by_proj = sorted(self.player_pool,
                                key=lambda p: getattr(p, 'base_projection', 0),
                                reverse=True)
        proj_percentiles = {p.name: i / len(sorted_by_proj) for i, p in enumerate(sorted_by_proj)}

        for player in self.player_pool:
            # Basic ownership formula
            sal_pct = salary_percentiles.get(player.name, 0.5)
            proj_pct = proj_percentiles.get(player.name, 0.5)

            # High salary + high projection = high ownership
            base_own = (1 - sal_pct) * 0.5 + (1 - proj_pct) * 0.5

            # Convert to percentage (0-40% range)
            ownership = base_own * 30  # Base is 0-30%

            # === NARRATIVE BOOSTS (The "Without Complexity" Part) ===

            # 1. Extreme Value Plays (biggest ownership driver)
            if player.salary <= 3500 and getattr(player, 'base_projection', 0) >= 7:
                ownership += 15  # These ALWAYS get mega-owned
                self.log(f"💰 Value chalk: {player.name} (${player.salary}, {player.base_projection:.1f} proj)", "debug")
            elif player.salary <= 4000 and getattr(player, 'base_projection', 0) >= 8:
                ownership += 10

            # 2. Pitcher Narratives
            if player.is_pitcher:
                # Aces in great spots
                if player.salary >= 10000:
                    opponent_total = getattr(player, 'opponent_implied_total', 4.5)
                    if opponent_total <= 3.5:
                        ownership += 8  # Ace vs bad team
                        self.log(f"⚾ Ace chalk: {player.name} vs {opponent_total:.1f} implied runs", "debug")

                # Cheap pitchers in good spots
                elif player.salary <= 7000:
                    opponent_total = getattr(player, 'opponent_implied_total', 4.5)
                    if opponent_total <= 3.5:
                        ownership += 12  # Value pitcher in great spot

                # Facing terrible teams
                bad_offenses = {'DET', 'MIA', 'OAK', 'PIT', 'WSH'}
                if any(team in str(getattr(player, 'game_info', '')) for team in bad_offenses):
                    ownership += 5

            else:  # Hitters
                # 3. Coors Field Effect
                if player.team == 'COL' or (hasattr(player, 'game_info') and '@COL' in str(player.game_info)):
                    ownership += 10  # Coors always popular
                    self.log(f"🏔️ Coors chalk: {player.name}", "debug")

                # 4. Elite Stacks
                team_total = getattr(player, 'team_total', getattr(player, 'implied_team_score', 4.5))
                if team_total >= 5.5 and getattr(player, 'batting_order', 0) in [1, 2, 3, 4, 5]:
                    ownership += 8  # Core of high-scoring lineup

                # 5. Cheap speed
                if player.salary <= 4000 and player.primary_position in ['OF', '2B', 'SS']:
                    if getattr(player, 'batting_order', 0) in [1, 2]:  # Leadoff value
                        ownership += 7

            # 6. Recency Bias (if we have last game data)
            last_game_pts = getattr(player, 'last_game_points', 0)
            if last_game_pts >= 30:  # Monster recent game
                ownership += 5
            elif last_game_pts >= 20:
                ownership += 3

            # 7. Team Popularity Multiplier
            chalk_teams = {'NYY', 'LAD', 'HOU', 'BOS', 'ATL', 'TOR', 'SD'}
            if player.team in chalk_teams:
                ownership *= 1.2  # 20% boost for popular teams

            contrarian_teams = {'KC', 'CIN', 'PIT', 'MIA', 'OAK'}
            if player.team in contrarian_teams:
                ownership *= 0.8  # 20% reduction for unpopular teams

            # 8. Multi-position eligibility boost
            if hasattr(player, 'position') and '/' in str(player.position):
                ownership += 2  # Flexible players get played more

            # Cap ownership at realistic levels
            player.ownership_projection = min(40, max(1, ownership))

            # Special cases that break the model
            if player.name in ['Shohei Ohtani', 'Ronald Acuna Jr.', 'Aaron Judge']:
                if player.salary <= 6000:  # If they're ever cheap
                    player.ownership_projection = 40  # Mega chalk


    def ensure_all_attributes(self, player):
        """Ensure player has all required attributes with defaults"""
        # Base attributes - check 'projection' field first
        if not hasattr(player, 'base_projection') or player.base_projection == 0:
            player.base_projection = (
                    getattr(player, 'projection', 0) or  # Your CSV field
                    getattr(player, 'AvgPointsPerGame', 0) or
                    getattr(player, 'ppg', 0) or
                    getattr(player, 'points', 0) or
                    (15.0 if player.is_pitcher else 8.0)  # Defaults
            )

    def enrich_player_pool_with_real_data(self):
        """Enhanced enrichment with salary-based variations and adjustments"""
        self.log("🔬 Starting enhanced enrichment with variations...")

        # First, do the base enrichment
        base_results = self.enrich_player_pool()

        # Ensure all attributes exist
        for player in self.player_pool:
            self.ensure_all_attributes(player)

        # Track enhanced enrichments
        enhanced_count = 0

        # Add variation based on player characteristics
        for player in self.player_pool:
            try:
                # PITCHER ADJUSTMENTS - Using better classification
                if player.is_pitcher:
                    pitcher_tier = self.classify_pitcher_tier(player)

                    if pitcher_tier == 'elite':
                        player.recent_form *= 1.08
                        player.consistency_score = 1.10
                        player.matchup_score *= 1.05
                    elif pitcher_tier == 'value_ace':
                        # Hidden gems get bigger boost
                        player.recent_form *= 1.10
                        player.consistency_score = 1.05
                        player.matchup_score *= 1.08
                    elif pitcher_tier == 'good':
                        player.recent_form *= 1.04
                        player.consistency_score = 1.05
                        player.matchup_score *= 1.02
                    else:  # standard
                        player.recent_form *= 0.95
                        player.consistency_score = 0.90
                        player.matchup_score *= 0.95

                # HITTER ADJUSTMENTS
                else:
                    if player.salary >= 5500:
                        # Elite hitters
                        player.recent_form *= 1.06
                        player.consistency_score = 1.04
                        # Batting order boost
                        if getattr(player, 'batting_order', 0) in [1, 2, 3, 4]:
                            player.recent_form *= 1.02
                    elif player.salary >= 4500:
                        # Mid-tier hitters
                        player.recent_form *= 1.02
                        player.consistency_score = 1.0
                    else:
                        # Value hitters - more volatile
                        player.recent_form *= 0.98
                        player.consistency_score = 0.95

                # ENHANCED WEATHER WITH DOME HANDLING
                dome_stadiums = {'TB', 'TOR', 'MIA', 'HOU', 'ARI', 'TEX', 'MIL'}

                if player.team in dome_stadiums:
                    player.weather_impact = 1.0  # Always neutral in dome
                    player.is_dome = True
                else:
                    player.is_dome = False

                    # Use Vegas total as weather proxy
                    if hasattr(player, 'team_total'):
                        if player.team_total >= 5.5:
                            # Special Coors handling
                            if player.team == 'COL' or (hasattr(player, 'opponent') and player.opponent == 'COL'):
                                player.weather_impact = 1.15  # Coors boost is real
                            else:
                                player.weather_impact = max(player.weather_impact, 1.08)
                        elif player.team_total >= 4.5:
                            player.weather_impact = max(player.weather_impact, 1.02)
                        elif player.team_total <= 3.5:
                            player.weather_impact = min(player.weather_impact, 0.94)
                        else:
                            player.weather_impact = 1.0

                    # Seasonal adjustments (summer = more offense)
                    import datetime
                    month = datetime.datetime.now().month
                    if month in [6, 7, 8]:  # June, July, August
                        player.weather_impact *= 1.03  # Summer boost
                    elif month in [4, 10]:  # April, October
                        player.weather_impact *= 0.97  # Cold months

                # PARK FACTOR ADJUSTMENTS (if not already set)
                if not hasattr(player, 'park_factor') or player.park_factor == 1.0:
                    team_park_factors = {
                        'COL': 1.33, 'CIN': 1.14, 'TEX': 1.12, 'BAL': 1.10,
                        'BOS': 1.06, 'PHI': 1.04, 'MIN': 1.03, 'NYY': 0.99,
                        'SD': 0.94, 'SF': 0.86, 'SEA': 0.88, 'DET': 0.91,
                        'MIA': 0.92, 'OAK': 0.90, 'STL': 0.94, 'LAD': 0.98
                    }
                    player.park_factor = team_park_factors.get(player.team, 1.0)

                # WEATHER REFINEMENTS (based on Vegas proxy)
                if hasattr(player, 'team_total'):
                    if player.team_total >= 5.5:
                        player.weather_impact = max(player.weather_impact, 1.08)
                    elif player.team_total >= 4.5:
                        player.weather_impact = max(player.weather_impact, 1.02)
                    elif player.team_total <= 3.5:
                        player.weather_impact = min(player.weather_impact, 0.94)

                # VALUE PLAY ADJUSTMENTS
                value_score = player.base_projection / (player.salary / 1000) if player.salary > 0 else 0
                if value_score >= 5.0:  # Great value
                    player.matchup_score *= 1.08
                    player.consistency_score *= 1.05

                # CAP ADJUSTMENTS (prevent extreme values)
                player.recent_form = max(0.8, min(1.3, player.recent_form))
                player.consistency_score = max(0.8, min(1.2, player.consistency_score))
                player.matchup_score = max(0.9, min(1.15, player.matchup_score))
                player.weather_impact = max(0.9, min(1.15, player.weather_impact))

                enhanced_count += 1

            except Exception as e:
                self.log(f"Error enhancing {player.name}: {e}")

        # Final ownership recalculation with enhanced data
        self._calculate_ownership_projections()

        self.log(f"✅ Enhanced enrichment complete: {enhanced_count} players enhanced")

        # Log sample to verify
        if self.player_pool:
            sample = self.player_pool[0]
            self.log(f"Sample - {sample.name}: form={sample.recent_form:.2f}, "
                     f"park={sample.park_factor:.2f}, weather={sample.weather_impact:.2f}, "
                     f"consistency={sample.consistency_score:.2f}")

        return {
            'total': len(self.player_pool),
            'enhanced': enhanced_count,
            'base_enrichments': base_results
        }

    def classify_pitcher_tier(self, player):
        """More accurate pitcher classification considering Coors and other factors"""
        # Coors Field pitchers always discounted
        if player.team == 'COL':
            if player.salary >= 8500:
                return 'elite'  # Still elite despite Coors discount
            elif player.salary >= 7000:
                return 'good'
            else:
                return 'standard'

        # Normal classification
        if player.salary >= 10000:
            return 'elite'
        elif player.salary >= 8500 and player.base_projection >= 18:
            return 'elite'  # Underpriced ace
        elif player.salary >= 8000:
            return 'good'
        elif player.base_projection >= 16 and player.salary < 8000:
            return 'value_ace'  # Hidden gem
        else:
            return 'standard'

    def _extract_home_team(self, player):
        """Extract home team from game info like 'KC@BOS'"""
        if hasattr(player, 'game_info') and player.game_info:
            if '@' in player.game_info:
                # Format is AWAY@HOME
                return player.game_info.split('@')[1].split()[0]
        return None


    def set_confirmed_players(self, confirmed_list: List[str]):
        """Manually set confirmed players (for testing)"""
        self.confirmed_players = set(confirmed_list)
        self.confirmations_fetched = True
        logger.info(f"Manually set {len(self.confirmed_players)} confirmed players")

    def detect_showdown_slate(self) -> bool:
        """Detect if this is a showdown slate"""
        if not self.player_pool:
            return False

        # Check if any player has CPT or UTIL position
        positions = {p.primary_position for p in self.player_pool}
        return 'CPT' in positions or 'UTIL' in positions

    def optimize_showdown_lineups(
            self,
            num_lineups: int = 20,
            strategy: str = "balanced",
            min_unique_players: int = 3,
            contest_type: str = "gpp"
    ) -> List[Dict]:
        """Optimize showdown lineups using fixed implementation"""
        if not self.player_pool:
            logger.error("No players in pool!")
            return []

        # Use the fixed showdown optimizer
        showdown_opt = ShowdownOptimizer(self.optimizer)

        # Filter to UTIL players only (ignore CPT entries)
        util_players = [p for p in self.player_pool if p.primary_position != 'CPT']

        logger.info(f"Showdown optimization with {len(util_players)} UTIL players")

        # Generate lineups
        return showdown_opt.generate_diverse_lineups(
            util_players,
            num_lineups
        )

    def optimize_lineups(self,
                         num_lineups: int = 1,
                         strategy: str = "balanced",
                         contest_type: str = "gpp",
                         min_unique_players: int = 3) -> List[Dict]:
        """Generate optimized lineups"""
        logger.info(f"\n🎯 Optimizing {num_lineups} lineups...")
        logger.info(f"   Strategy: {strategy}")
        logger.info(f"   Contest Type: {contest_type}")
        logger.info(f"   Pool size: {len(self.player_pool)} players")

        # Contest type configuration
        if contest_type.lower() == 'cash':
            logger.info("📋 Contest Configuration: CASH")
            logger.info("   Strategy: Conservative optimization")
            logger.info("   Parameters: Floor-focused, consistency weighted")
            logger.info("   Target: 86.2 score (79% win rate)")
        else:
            logger.info("📋 Contest Configuration: GPP")
            logger.info("   Strategy: Tournament optimization")
            logger.info("   Parameters: Stack correlation, ownership leverage")
            logger.info("   Target: -67.7 score (64th percentile)")

        # Always score players before optimization
        logger.info(f"Scoring players for {contest_type}...")
        self.score_players(contest_type)

        self._last_contest_type = contest_type

        # Log sample scores for verification
        logger.info("📊 Calculating player scores...")
        logger.info("   Sample scores:")
        sample_players = self.player_pool[:3] if len(self.player_pool) >= 3 else self.player_pool
        for p in sample_players:
            # Use safe attribute access
            score = getattr(p, 'optimization_score', None)
            if score is not None:
                logger.info(f"   {p.name}: {score:.2f} ({contest_type})")
            else:
                logger.info(f"   {p.name}: No score - using base projection")
                # Set a default score if missing
                p.optimization_score = getattr(p, 'dff_projection', 10.0)

        # Generate lineups
        lineups = []
        used_players = set()

        for i in range(num_lineups):
            logger.info(f"\n   Lineup {i + 1}/{num_lineups}...")

            # Apply diversity penalty if needed
            if i > 0 and min_unique_players > 0:
                self._apply_diversity_penalty(used_players, penalty=0.8)

            # Initialize variables
            lineup_players = None
            total_score = 0

            try:
                # Set contest type in optimizer config BEFORE calling optimize
                if hasattr(self.optimizer, 'config'):
                    self.optimizer.config.contest_type = contest_type

                # Optimize single lineup WITHOUT contest_type parameter
                result = self.optimizer.optimize(
                    strategy=strategy,
                    players=self.player_pool,
                    manual_selections=list(self.manual_selections)
                )

                # Handle the result - check for object with attributes
                if result:
                    if hasattr(result, 'lineup') and hasattr(result, 'score'):
                        # Result is an object
                        lineup_players = result.lineup
                        total_score = result.score
                    elif hasattr(result, 'total_score'):
                        # Alternative object format
                        lineup_players = result.lineup if hasattr(result, 'lineup') else None
                        total_score = result.total_score
                    elif isinstance(result, tuple) and len(result) == 2:
                        # Tuple format
                        lineup_players, total_score = result
                    elif isinstance(result, list):
                        # List format
                        lineup_players = result
                        total_score = sum(p.fantasy_points for p in lineup_players) if lineup_players else 0
                    else:
                        logger.warning(f"Unknown result format: {type(result)}")
                        lineup_players = None
                        total_score = 0

            except Exception as e:
                logger.error(f"Optimization failed: {e}")
                lineup_players = None
                total_score = 0

            # Only process if we got a valid lineup
            if lineup_players is not None and len(lineup_players) > 0:
                # Track used players
                for player in lineup_players:
                    used_players.add(player.name)

                # Calculate projected points
                projected_points = sum(
                    getattr(p, 'dff_projection', 0) for p in lineup_players
                )

                # Create lineup dictionary
                lineup_dict = {
                    'players': lineup_players,
                    'total_salary': sum(p.salary for p in lineup_players),
                    'total_score': total_score,
                    'total_projection': projected_points,
                    'strategy': strategy,
                    'contest_type': contest_type
                }

                # Add slate info if available
                if hasattr(self, 'slate_info'):
                    lineup_dict['slate_info'] = self.slate_info

                # Add to lineups list
                lineups.append(lineup_dict)

                # Log lineup summary
                self._log_lineup_summary(lineup_dict, i + 1)
            else:
                logger.warning(f"   ✗ Failed to generate lineup {i + 1}")

            # Restore original scores
            if i > 0:
                self._restore_original_scores()

        logger.info(f"\n✅ Generated {len(lineups)} optimized lineups")
        return lineups

    def _apply_diversity_penalty(self, used_players: Set[str], penalty: float = 0.8):
        """Apply penalty to previously used players"""
        for player in self.player_pool:
            if player.name in used_players:
                player.temp_score = player.optimization_score
                player.optimization_score *= penalty

    def _restore_original_scores(self):
        """Restore original optimization scores"""
        for player in self.player_pool:
            if hasattr(player, 'temp_score'):
                player.optimization_score = player.temp_score
                delattr(player, 'temp_score')

    def _log_lineup_summary(self, lineup: Dict, lineup_num: int):
        """Log a summary of the lineup"""
        total_salary = lineup['total_salary']
        total_score = lineup['total_score']
        total_projection = lineup.get('total_projection', 0)

        logger.info(
            f"   ✓ Lineup {lineup_num}: ${total_salary:,} salary, {total_score:.1f} optimizer score, {total_projection:.1f} projected points")

        # Count stacks
        team_counts = {}
        for player in lineup['players']:
            team = player.team
            team_counts[team] = team_counts.get(team, 0) + 1

        stacks = [(team, count) for team, count in team_counts.items() if count >= 2]
        if stacks:
            stack_str = ", ".join([f"{team}({count})" for team, count in stacks])
            logger.info(f"   ✓ Stacks: {stack_str}")


    def export_lineups(self, lineups: List[Dict], filename: str = None):
        """Export lineups to CSV"""
        if not lineups:
            logger.warning("No lineups to export")
            return

        if filename is None:
            filename = f"lineups_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Convert to DataFrame format
        rows = []
        for i, lineup in enumerate(lineups):
            row = {'Lineup': i + 1}

            # Add players by position
            positions = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
            pos_counts = {}

            for pos in positions:
                for player in lineup['players']:
                    if player.primary_position == pos or pos in player.primary_position:
                        col_name = f"{pos}{pos_counts.get(pos, 1)}" if pos_counts.get(pos, 0) > 0 else pos
                        row[col_name] = player.name
                        pos_counts[pos] = pos_counts.get(pos, 0) + 1
                        break

            row['Salary'] = lineup['total_salary']
            row['Projection'] = lineup['total_score']
            rows.append(row)

        # Save to CSV
        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False)
        logger.info(f"✅ Exported {len(lineups)} lineups to {filename}")

        return filename


# Example usage
if __name__ == "__main__":
    # Test the system
    system = UnifiedCoreSystem()

    # Example workflow
    print("Unified Core System initialized successfully!")
    print("\nExample usage:")
    print("1. system.load_players_from_csv('DKSalaries.csv')")
    print("2. system.fetch_confirmed_players()")
    # ===== ADD THIS DEBUG CODE HERE =====
    print("\n🔍 STEP 1: DEBUGGING CONFIRMATION DATA")
    print("=" * 60)

    # Check what get_all_confirmations actually returns
    try:
        raw_confirmations = system.confirmation_system.get_all_confirmations()
        print(f"Type of confirmation data: {type(raw_confirmations)}")
        print(f"Number of items: {len(raw_confirmations) if hasattr(raw_confirmations, '__len__') else 'N/A'}")

        # Show first few items
        if isinstance(raw_confirmations, list):
            print("\nFirst 5 items:")
            for i, item in enumerate(raw_confirmations[:5]):
                print(f"  {i}: {item} (type: {type(item)})")
        elif isinstance(raw_confirmations, dict):
            print("\nFirst 5 key-value pairs:")
            for i, (key, value) in enumerate(list(raw_confirmations.items())[:5]):
                print(f"  {key}: {value} (type: {type(value)})")
        else:
            print(f"Unexpected type: {raw_confirmations}")

    except Exception as e:
        print(f"ERROR getting confirmations: {e}")

    print("\n" + "-" * 60)
    print("3. system.build_player_pool()")
    print("4. system.enrich_player_pool()")
    print("5. lineups = system.optimize_lineups(num_lineups=20, contest_type='gpp')")
    print("6. system.export_lineups(lineups)")