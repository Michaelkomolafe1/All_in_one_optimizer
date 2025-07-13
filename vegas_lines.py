#!/usr/bin/env python3
"""Vegas lines integration with The Odds API"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
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
    
    def get_vegas_lines(self, force_refresh: bool = False, **kwargs) -> Dict:
        """Get MLB game totals - compatible method name"""
        if self.lines and not force_refresh:
            return self.lines
            
        url = f"{self.base_url}/sports/baseball_mlb/odds"
        
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'totals',
            'oddsFormat': 'american',
            'dateFormat': 'iso'
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                games = response.json()
                self.verbose_print(f"🎰 Found {len(games)} games from Vegas API")
                
                for game in games:
                    home_team = self._normalize_team(game['home_team'])
                    away_team = self._normalize_team(game['away_team'])
                    
                    # Get total from first bookmaker
                    if game.get('bookmakers'):
                        for bookmaker in game['bookmakers']:
                            for market in bookmaker.get('markets', []):
                                if market['key'] == 'totals':
                                    for outcome in market['outcomes']:
                                        if outcome['name'] == 'Over':
                                            total = outcome['point']
                                            self.lines[home_team] = {
                                                'total': total, 
                                                'home': True,
                                                'opponent': away_team
                                            }
                                            self.lines[away_team] = {
                                                'total': total, 
                                                'home': False,
                                                'opponent': home_team
                                            }
                                            break
                                    break
                            break
                
                self.verbose_print(f"✅ Loaded Vegas totals for {len(self.lines)} teams")
                self.verbose_print(f"📊 API calls remaining: {response.headers.get('x-requests-remaining', 'N/A')}")
                return self.lines
            else:
                self.verbose_print(f"❌ Vegas API Error: {response.status_code}")
                return {}
                
        except Exception as e:
            self.verbose_print(f"❌ Error fetching Vegas odds: {e}")
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
    
    def enrich_players(self, players: List) -> int:
        """Apply Vegas totals to players"""
        if not self.lines:
            self.get_vegas_lines()
        
        enriched = 0
        for player in players:
            if hasattr(player, 'team') and player.team in self.lines:
                game_info = self.lines[player.team]
                game_total = game_info['total']
                
                # Store Vegas data on player
                player.vegas_total = game_total
                player.vegas_opponent = game_info.get('opponent', 'UNK')
                
                # Apply scoring adjustments
                if hasattr(player, 'primary_position'):
                    if player.primary_position == 'P':
                        # Pitchers benefit from low totals
                        if game_total <= 7.5:
                            player.vegas_boost = 1.10
                        elif game_total >= 9.5:
                            player.vegas_boost = 0.90
                        else:
                            player.vegas_boost = 1.0
                    else:
                        # Hitters benefit from high totals
                        if game_total >= 9.5:
                            player.vegas_boost = 1.08
                        elif game_total <= 7.5:
                            player.vegas_boost = 0.92
                        else:
                            player.vegas_boost = 1.0
                else:
                    player.vegas_boost = 1.0
                
                enriched += 1
                    
        self.verbose_print(f"🎰 Enriched {enriched} players with Vegas data")
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
