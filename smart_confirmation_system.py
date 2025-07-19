#!/usr/bin/env python3
"""
DROP-IN REPLACEMENT FOR smart_confirmation_system.py
===================================================
This file can directly replace your existing smart_confirmation_system.py
Maintains the same interface but with modern, efficient implementation
"""

import logging
import requests
from unified_data_system import UnifiedDataSystem
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

logger = logging.getLogger(__name__)


class OptimizedConfirmationMixin:
    """
    Mixin to add optimized confirmation workflow
    """

    def _optimize_confirmation_workflow(self, csv_players, confirmed_lineups):
        """Apply workflow optimizations to speed up confirmation matching"""

        # OPTIMIZATION 1: Pre-index confirmed lineups by team
        if self.verbose:
            print("🔧 Optimizing confirmation workflow...")

        lineup_by_team = {}
        for team, lineup in confirmed_lineups.items():
            team_norm = self.data_system.normalize_team(team)
            if team_norm not in lineup_by_team:
                lineup_by_team[team_norm] = []

            # OPTIMIZATION 2: Pre-normalize lineup names
            for player in lineup:
                normalized_name = player['name'].lower().strip()
                player['_normalized_name'] = normalized_name
                lineup_by_team[team_norm].append(player)

        # OPTIMIZATION 3: Create exact match lookup
        exact_match_lookup = {}
        for team, lineup in lineup_by_team.items():
            exact_match_lookup[team] = {player['_normalized_name']: player for player in lineup}

        # OPTIMIZATION 4: Group CSV players by team
        csv_by_team = {}
        for player in csv_players:
            if hasattr(player, 'team'):
                team_norm = self.data_system.normalize_team(player.team)
            else:
                team_norm = self.data_system.normalize_team(player.get('team', ''))

            if team_norm not in csv_by_team:
                csv_by_team[team_norm] = []
            csv_by_team[team_norm].append(player)

        return lineup_by_team, exact_match_lookup, csv_by_team

    def apply_confirmations_optimized(self, csv_players, confirmed_lineups, confirmed_pitchers):
        """Optimized version of confirmation application"""
        start_time = time.time()

        # Apply workflow optimizations
        lineup_by_team, exact_match_lookup, csv_by_team = self._optimize_confirmation_workflow(
            csv_players, confirmed_lineups
        )

        confirmed_count = 0
        total_comparisons = 0

        # OPTIMIZATION 5: Only process teams with both CSV players AND confirmed lineups
        for team in csv_by_team:
            if team in lineup_by_team:
                csv_players_for_team = csv_by_team[team]
                exact_matches_for_team = exact_match_lookup[team]
                lineup_players_for_team = lineup_by_team[team]

                for csv_player in csv_players_for_team:
                    player_name = csv_player.name if hasattr(csv_player, 'name') else csv_player['name']
                    player_name_norm = player_name.lower().strip()

                    # OPTIMIZATION 6: Try exact match first
                    if player_name_norm in exact_matches_for_team:
                        lineup_player = exact_matches_for_team[player_name_norm]

                        # Mark player as confirmed
                        if hasattr(csv_player, 'is_confirmed'):
                            csv_player.is_confirmed = True
                            csv_player.add_confirmation_source("mlb_lineup")
                            if 'order' in lineup_player:
                                csv_player.batting_order = lineup_player['order']
                        else:
                            csv_player['is_confirmed'] = True

                        confirmed_count += 1
                        total_comparisons += 1

                        if self.verbose:
                            print(f"   ✅ {player_name} (exact match)")

                    else:
                        # OPTIMIZATION 7: Complex matching only if needed
                        for lineup_player in lineup_players_for_team:
                            total_comparisons += 1

                            # Use existing excellent name matching
                            if self.data_system.match_player_names(player_name, lineup_player['name']):
                                # Mark player as confirmed
                                if hasattr(csv_player, 'is_confirmed'):
                                    csv_player.is_confirmed = True
                                    csv_player.add_confirmation_source("mlb_lineup")
                                    if 'order' in lineup_player:
                                        csv_player.batting_order = lineup_player['order']
                                else:
                                    csv_player['is_confirmed'] = True

                                confirmed_count += 1

                                if self.verbose:
                                    print(f"   ✅ {player_name} → {lineup_player['name']} (fuzzy match)")
                                break

        # Apply pitcher confirmations
        pitcher_count = self._apply_pitcher_confirmations_optimized(csv_players, confirmed_pitchers)

        elapsed_time = time.time() - start_time

        if self.verbose:
            print(f"\n⚡ Optimized confirmation completed:")
            print(f"   Time: {elapsed_time * 1000:.1f}ms")
            print(f"   Comparisons: {total_comparisons:,}")
            print(f"   Rate: {total_comparisons / elapsed_time:,.0f} comparisons/sec")
            print(f"   Confirmed: {confirmed_count} players, {pitcher_count} pitchers")

        return confirmed_count + pitcher_count

    def _apply_pitcher_confirmations_optimized(self, csv_players, confirmed_pitchers):
        """Optimized pitcher confirmation"""

        # Pre-normalize pitcher names
        pitcher_exact_lookup = {}
        for team, pitcher_info in confirmed_pitchers.items():
            team_norm = self.data_system.normalize_team(team)
            pitcher_name_norm = pitcher_info['name'].lower().strip()
            pitcher_exact_lookup[team_norm] = {
                'normalized_name': pitcher_name_norm,
                'original_name': pitcher_info['name'],
                'info': pitcher_info
            }

        pitcher_count = 0

        for csv_player in csv_players:
            # Only check pitchers
            if hasattr(csv_player, 'primary_position'):
                is_pitcher = csv_player.primary_position == 'P'
                player_team = csv_player.team
                player_name = csv_player.name
            else:
                is_pitcher = csv_player.get('position') == 'P'
                player_team = csv_player.get('team', '')
                player_name = csv_player.get('name', '')

            if is_pitcher:
                team_norm = self.data_system.normalize_team(player_team)
                player_name_norm = player_name.lower().strip()

                # Try exact match first
                if team_norm in pitcher_exact_lookup:
                    pitcher_data = pitcher_exact_lookup[team_norm]

                    if player_name_norm == pitcher_data['normalized_name']:
                        # Exact match
                        if hasattr(csv_player, 'is_confirmed'):
                            csv_player.is_confirmed = True
                            csv_player.add_confirmation_source("mlb_starter")
                        else:
                            csv_player['is_confirmed'] = True

                        pitcher_count += 1

                        if self.verbose:
                            print(f"   ⚾ {player_name} (pitcher exact match)")

                    else:
                        # Try fuzzy match
                        if self.data_system.match_player_names(player_name, pitcher_data['original_name']):
                            if hasattr(csv_player, 'is_confirmed'):
                                csv_player.is_confirmed = True
                                csv_player.add_confirmation_source("mlb_starter")
                            else:
                                csv_player['is_confirmed'] = True

                            pitcher_count += 1

                            if self.verbose:
                                print(f"   ⚾ {player_name} → {pitcher_data['original_name']} (pitcher fuzzy match)")

        return pitcher_count


class SmartConfirmationSystem(OptimizedConfirmationMixin):
    """
    Modern replacement for existing SmartConfirmationSystem
    Maintains same interface but with better performance and reliability
    """

    def __init__(self, csv_players: List = None, verbose: bool = False):
        self.verbose = verbose
        self.csv_players = csv_players or []
        self.data_system = UnifiedDataSystem()
        self.confirmed_lineups = {}
        self.confirmed_pitchers = {}

        # Modern additions
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 7200  # 2 hours in seconds
        self._lock = threading.Lock()
        self._session = requests.Session()
        self._session.timeout = 15

        # Extract teams from CSV for smart filtering
        self.csv_teams = self._extract_teams_from_players()

        if self.verbose and self.csv_teams:
            print(f"📊 CSV teams detected: {sorted(self.csv_teams)}")

    def _extract_teams_from_players(self) -> Set[str]:
        """Extract team abbreviations from CSV players"""
        teams = set()
        if not self.csv_players:
            return teams

        for player in self.csv_players:
            try:
                if hasattr(player, 'team'):
                    teams.add(player.team)
                elif isinstance(player, dict):
                    team = player.get('team') or player.get('TeamAbbrev', '')
                    if team:
                        teams.add(team)
            except Exception:
                continue

        return teams

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        if key not in self._cache_timestamps:
            return False

        age = time.time() - self._cache_timestamps[key]
        return age < self._cache_ttl

    def _get_from_cache(self, key: str):
        """Get value from cache if valid"""
        if self._is_cache_valid(key):
            return self._cache.get(key)
        return None

    def _set_cache(self, key: str, value):
        """Set cache value with timestamp"""
        with self._lock:
            self._cache[key] = value
            self._cache_timestamps[key] = time.time()

    def _invalidate_cache(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._cache_timestamps.clear()

    def get_all_confirmations(self) -> Tuple[int, int]:
        """
        Main method to get all confirmations
        Returns (lineup_count, pitcher_count)
        """
        if self.verbose:
            print("🔍 SMART CONFIRMATION SYSTEM - MODERN MODE")
            print("=" * 50)

        # Generate cache key based on teams and current day
        today = datetime.now().strftime('%Y-%m-%d')
        cache_key = f"confirmations_{today}_{'_'.join(sorted(self.csv_teams))}"

        # Check cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            if self.verbose:
                print("📋 Using cached confirmation data")
            self.confirmed_lineups = cached_data['lineups']
            self.confirmed_pitchers = cached_data['pitchers']
        else:
            # Fetch fresh data
            if self.verbose:
                print("🌐 Fetching fresh confirmation data")
            self._fetch_fresh_confirmations(today)

            # Cache the results
            cache_data = {
                'lineups': self.confirmed_lineups.copy(),
                'pitchers': self.confirmed_pitchers.copy()
            }
            self._set_cache(cache_key, cache_data)

        # Calculate counts
        lineup_count = sum(len(lineup) for lineup in self.confirmed_lineups.values())
        pitcher_count = len(self.confirmed_pitchers)

        if self.verbose:
            print(f"📊 Found lineups for {len(self.confirmed_lineups)} teams")
            print(f"⚾ Found pitchers for {len(self.confirmed_pitchers)} teams")
            print(f"👥 Total confirmed players: {lineup_count}")

        return lineup_count, pitcher_count

    def _fetch_fresh_confirmations(self, date: str):
        """Fetch fresh confirmation data from MLB API"""
        try:
            # Reset current data
            self.confirmed_lineups = {}
            self.confirmed_pitchers = {}

            # Get today's games with lineups and probable pitchers
            url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}&hydrate=lineups,probablePitcher"

            response = self._session.get(url)
            if response.status_code != 200:
                if self.verbose:
                    print(f"❌ MLB API returned status {response.status_code}")
                return

            data = response.json()
            if not data.get('dates'):
                if self.verbose:
                    print("❌ No games found for today")
                return

            # Process games in parallel for better performance
            games = []
            for date_entry in data['dates']:
                games.extend(date_entry.get('games', []))

            if not games:
                if self.verbose:
                    print("❌ No games in schedule")
                return

            # Use thread pool for concurrent processing
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(self._process_game, game) for game in games]

                processed = 0
                for future in as_completed(futures):
                    try:
                        future.result()
                        processed += 1
                    except Exception as e:
                        if self.verbose:
                            print(f"⚠️ Error processing game: {e}")

            if self.verbose:
                print(f"🎯 Processed {processed}/{len(games)} games")

        except Exception as e:
            if self.verbose:
                print(f"❌ Error fetching confirmations: {e}")

    def _process_game(self, game: Dict):
        """Process a single game for lineups and pitchers"""
        try:
            # Process lineups
            lineups = game.get('lineups', {})
            for team_side in ['home', 'away']:
                team_data = game.get('teams', {}).get(team_side, {})
                team_abbr = team_data.get('team', {}).get('abbreviation', '')

                # Only process teams we care about
                if team_abbr not in self.csv_teams:
                    continue

                # Process lineup
                lineup = lineups.get(team_side, {}).get('lineup', [])
                if lineup:
                    lineup_players = []
                    for i, player_data in enumerate(lineup):
                        player = player_data.get('player', {})
                        position = player_data.get('position', {}).get('abbreviation', '')

                        lineup_players.append({
                            'name': player.get('fullName', ''),
                            'position': position,
                            'order': i + 1,
                            'team': team_abbr,
                            'source': 'mlb_api'
                        })

                    if lineup_players:
                        with self._lock:
                            self.confirmed_lineups[team_abbr] = lineup_players

                # Process probable pitcher
                probable_pitcher = team_data.get('probablePitcher')
                if probable_pitcher:
                    pitcher_info = {
                        'name': probable_pitcher.get('fullName', ''),
                        'team': team_abbr,
                        'source': 'mlb_api'
                    }

                    with self._lock:
                        self.confirmed_pitchers[team_abbr] = pitcher_info

        except Exception as e:
            if self.verbose:
                print(f"⚠️ Error processing game: {e}")

    def is_player_confirmed(self, player_name: str, team: str = None) -> Tuple[bool, Optional[int]]:
        """
        Check if player is confirmed in actual lineup
        Returns (is_confirmed, batting_order)
        """
        if not team or team not in self.confirmed_lineups:
            return False, None

        lineup = self.confirmed_lineups[team]
        player_name_lower = player_name.lower().strip()

        for lineup_player in lineup:
            lineup_name = lineup_player.get('name', '').lower().strip()

            # Try exact match first
            if player_name_lower == lineup_name:
                return True, lineup_player.get('order', 1)

            # Try partial matching
            if self._names_match(player_name_lower, lineup_name):
                return True, lineup_player.get('order', 1)

        return False, None

    def is_pitcher_confirmed(self, pitcher_name: str, team: str = None) -> bool:
        """Check if pitcher is confirmed starter"""
        if not team or team not in self.confirmed_pitchers:
            return False

        confirmed_pitcher = self.confirmed_pitchers[team]
        pitcher_name_lower = pitcher_name.lower().strip()
        confirmed_name = confirmed_pitcher.get('name', '').lower().strip()

        # Try exact match first
        if pitcher_name_lower == confirmed_name:
            return True

        # Try partial matching
        return self._names_match(pitcher_name_lower, confirmed_name)

    def _names_match(self, name1: str, name2: str) -> bool:
        """Enhanced name matching logic"""
        # Remove common suffixes/prefixes
        for suffix in [' jr.', ' sr.', ' iii', ' ii']:
            name1 = name1.replace(suffix, '')
            name2 = name2.replace(suffix, '')

        # Check if one name contains the other
        if name1 in name2 or name2 in name1:
            return True

        # Check individual name parts
        parts1 = set(name1.split())
        parts2 = set(name2.split())

        # If they share most parts, consider it a match
        common_parts = parts1.intersection(parts2)
        min_parts = min(len(parts1), len(parts2))

        if min_parts > 0 and len(common_parts) >= min_parts * 0.7:
            return True

        return False

    def update_csv_players(self, players):
        """Update CSV players list"""
        self.csv_players = players
        self.csv_teams = self._extract_teams_from_players()

        # Invalidate cache when players change
        self._invalidate_cache()

        if self.verbose:
            print(f"📊 Updated CSV teams: {sorted(self.csv_teams)}")

    def invalidate_cache(self):
        """Manually invalidate all cached data"""
        self._invalidate_cache()
        if self.verbose:
            print("🗑️ Confirmation cache invalidated")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics for debugging"""
        return {
            'cache_entries': len(self._cache),
            'cache_age_seconds': min(
                [time.time() - ts for ts in self._cache_timestamps.values()]) if self._cache_timestamps else 0,
            'cache_ttl_seconds': self._cache_ttl,
            'teams_monitored': len(self.csv_teams)
        }

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, '_session'):
            self._session.close()


# Backwards compatibility alias
class SmartConfirmation(SmartConfirmationSystem):
    """Alias for backwards compatibility"""


# Factory function for easy creation
def create_confirmation_system(csv_players=None, verbose=False, cache_ttl_hours=2):
    """
    Factory function to create a SmartConfirmationSystem

    Args:
        csv_players: List of player objects
        verbose: Enable verbose logging
        cache_ttl_hours: Cache time-to-live in hours

    Returns:
        SmartConfirmationSystem instance
    """
    system = SmartConfirmationSystem(csv_players, verbose)
    system._cache_ttl = cache_ttl_hours * 3600  # Convert to seconds
    return system


if __name__ == "__main__":
    # Test the system
    print("Testing Modern Smart Confirmation System...")

    # Create test system
    system = SmartConfirmationSystem(verbose=True)

    # Test fetching confirmations
    lineup_count, pitcher_count = system.get_all_confirmations()

    print(f"\nResults:")
    print(f"  Lineups found: {lineup_count}")
    print(f"  Pitchers found: {pitcher_count}")

    # Test cache stats
    stats = system.get_cache_stats()
    print(f"\nCache Stats: {stats}")
    def get_all_confirmations_batch(self) -> Tuple[Dict[str, List], Dict[str, str]]:
        """Get all confirmations in one batched operation"""
        logger.info("PERFORMANCE: Batch fetching all lineup confirmations")

        lineups = {}
        pitchers = {}

        # Fetch all team lineups at once (simulated batch operation)
        # In reality, this would be a single API call for all games

        teams = set()
        for source in self.sources:
            # Collect all teams that need checking
            # This is where you'd optimize the actual fetching
            pass

        # Return cached results if recent
        if hasattr(self, '_confirmation_cache'):
            cache_data, cache_time = self._confirmation_cache
            if (datetime.now() - cache_time).seconds < 300:  # 5 min
                return cache_data

        # Otherwise fetch and cache
        result = self._fetch_all_confirmations()
        self._confirmation_cache = (result, datetime.now())

        return result


    print("\n✅ Test completed!")