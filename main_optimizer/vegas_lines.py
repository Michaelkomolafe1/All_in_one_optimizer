#!/usr/bin/env python3
"""Vegas lines integration with The Odds API"""
from datetime import datetime
from enhanced_caching_system import get_cache_manager
from datetime import datetime
import requests
from functools import lru_cache
from typing import Any, Dict, List, Optional
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class VegasLines:
    """Vegas lines using The Odds API - Compatible with bulletproof_dfs_core"""
    
    def __init__(self, api_key: str = "14b669db87ed65f1d0f3e70a90386707", verbose: bool = True):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.lines = {}
        self.verbose = verbose
        
    def verbose_print(self, message: str):
        """Print if verbose mode is on"""
        if self.verbose:
            print(message)

    def get_player_vegas_data(self, player) -> Optional[Dict]:
        """
        Get Vegas data for a single player
        Used by the performance optimizer for cached enrichment
        """
        if not hasattr(player, "team") or not player.team:
            return None

        # Get team data from our lines
        team_data = self.lines.get(player.team)
        if not team_data:
            return None

        # Convert to expected format
        vegas_data = {
            'total': team_data.get('total', 9.0),
            'home': team_data.get('home', True),
            'opponent': team_data.get('opponent', 'OPP'),
            'vegas_multiplier': self._calculate_vegas_multiplier(player, team_data)
        }

        # Log high-value games
        for team, data in vegas_data.items():
            if data.get('implied_total', 0) > 5.5:
                logger.info(f"VEGAS: High-scoring game alert - {team} implied total: {data['implied_total']}")

        return vegas_data

    def _calculate_vegas_multiplier(self, player, team_data) -> float:
        """Calculate Vegas multiplier based on game total and player position"""
        game_total = team_data.get('total', 9.0)

        if getattr(player, 'primary_position', '') == 'P':
            # Pitchers benefit from low totals
            if game_total <= 8.0:
                return 1.08
            elif game_total >= 10.0:
                return 0.94
            else:
                return 1.02
        else:
            # Hitters benefit from high totals
            if game_total >= 9.5:
                return 1.10
            elif game_total <= 7.5:
                return 0.92
            else:
                return 1.0

    def get_vegas_lines(self):
        """Get Vegas lines with better cache handling"""
        # Debug info
        self.verbose_print(f"📁 Cache file: {self.cache_file}")
        self.verbose_print(f"⏱️ Cache duration: {self.cache_duration / 3600:.1f} hours")

        # Try to load from cache
        cached_data = self.load_from_cache()

        if cached_data and isinstance(cached_data, dict) and len(cached_data) > 0:
            self.verbose_print(f"✅ Using cached Vegas data ({len(cached_data)} games)")
            self.lines = cached_data
            return cached_data

        # Cache miss - fetch fresh
        self.verbose_print("🎰 Fetching fresh Vegas lines from API...")

        try:
            response = requests.get(
                f"{self.base_url}/v1/odds",
                headers={"x-api-key": self.api_key},
                params={
                    "sport": "baseball_mlb",
                    "markets": "totals",
                    "dateFormat": "iso"
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                processed_lines = self._process_odds_data(data)

                # Cache the processed data
                if processed_lines:
                    self.save_to_cache(processed_lines)
                    self.lines = processed_lines

                return processed_lines
            else:
                self.verbose_print(f"❌ API error: {response.status_code}")
                return {}

        except Exception as e:
            self.verbose_print(f"❌ Error fetching Vegas: {e}")
            return {}
    
    def _normalize_team(self, team_name: str) -> str:
        """Convert API team names to DFS abbreviations"""
        team_map = {
            "Arizona Diamondbacks": "ARI", "Atlanta Braves": "ATL",
            "Baltimore Orioles": "BAL", "Boston Red Sox": "BOS",
            "Chicago Cubs": "CHC", "Chicago White Sox": "CWS",
            "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE",
            "Colorado Rockies": "COL", "Detroit Tigers": "DET",
            "Houston Astros": "HOU", "Kansas City Royals": "KC",
            "Los Angeles Angels": "LAA", "Los Angeles Dodgers": "LAD",
            "Miami Marlins": "MIA", "Milwaukee Brewers": "MIL",
            "Minnesota Twins": "MIN", "New York Mets": "NYM",
            "New York Yankees": "NYY", "Oakland Athletics": "OAK",
            "Philadelphia Phillies": "PHI", "Pittsburgh Pirates": "PIT",
            "San Diego Padres": "SD", "San Francisco Giants": "SF",
            "Seattle Mariners": "SEA", "St. Louis Cardinals": "STL",
            "Tampa Bay Rays": "TB", "Texas Rangers": "TEX",
            "Toronto Blue Jays": "TOR", "Washington Nationals": "WSH"
        }
        return team_map.get(team_name, team_name[:3].upper())

    def enrich_players(self, players) -> int:
        """Enrich players with Vegas data"""
        if not self.lines:
            self.get_vegas_lines()

        enriched = 0
        for player in players:
            vegas_data = self.get_player_vegas_data(player)
            if vegas_data:
                # Apply vegas multiplier or boost
                vegas_mult = vegas_data.get('vegas_multiplier', 1.0)
                if hasattr(player, 'apply_vegas_multiplier'):
                    player.apply_vegas_multiplier(vegas_mult)
                else:
                    # Fallback - set vegas boost attribute
                    player.vegas_boost = vegas_mult

                enriched += 1

        return enriched
    
    def apply_to_players(self, players: List) -> List:
        """Legacy method for compatibility"""
        self.enrich_players(players)
        return players
    
    def get_high_total_teams(self, threshold: float = 9.0) -> List[str]:
        """Get teams in high-scoring games"""
        if not self.lines:
            self.get_vegas_lines()
        return [team for team, info in self.lines.items() if info['total'] >= threshold]
    
    def get_low_total_teams(self, threshold: float = 8.0) -> List[str]:
        """Get teams in low-scoring games"""
        if not self.lines:
            self.get_vegas_lines()
        return [team for team, info in self.lines.items() if info['total'] <= threshold]
    
    def print_summary(self):
        """Print Vegas lines summary"""
        if not self.lines:
            self.get_vegas_lines()
            
        print("\n🎰 VEGAS LINES SUMMARY")
        print("=" * 40)
        
        # Group by game
        games = {}
        for team, info in self.lines.items():
            if info['home']:
                games[team] = (team, info['opponent'], info['total'])
        
        # Sort by total
        for home, away, total in sorted(games.values(), key=lambda x: x[2], reverse=True):
            print(f"{away} @ {home}: {total}")
            
        print(f"\nHigh totals (9.5+): {len(self.get_high_total_teams(9.5))}")
        print(f"Low totals (7.5-): {len(self.get_low_total_teams(7.5))}")
    def get_all_vegas_data(self, teams: List[str]) -> Dict[str, Any]:
        """Fetch Vegas data for all teams at once"""
        # Check if we already have recent data for all games
        cache_key = f"all_vegas_{datetime.now().strftime('%Y%m%d_%H')}"

        if hasattr(self, '_all_vegas_cache'):
            cached_data, cached_time = self._all_vegas_cache
            if (datetime.now() - cached_time).seconds < 600:  # 10 min cache
                logger.info("PERFORMANCE: Using cached Vegas data for all teams")
                return cached_data

        # Fetch all game data in one request
        all_data = {}
        try:
            # This would be your actual API call to get all games
            # For now, simulate batch processing
            for team in teams:
                data = self.get_team_vegas_data(team)
                if data:
                    all_data[team] = data

            # Cache the results
            self._all_vegas_cache = (all_data, datetime.now())

        except Exception as e:
            logger.error(f"Failed to fetch Vegas data: {e}")

        return all_data


# Test if module loads correctly
if __name__ == "__main__":
    print("Testing Vegas Lines module...")
    vegas = VegasLines()
    lines = vegas.get_vegas_lines()
    if lines:
        print("✅ Module working correctly!")
        vegas.print_summary()
    else:
        print("❌ Failed to fetch lines")
