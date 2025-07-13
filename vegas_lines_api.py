#!/usr/bin/env python3
"""Working Vegas lines integration using The Odds API"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

class VegasLinesAPI:
    """Vegas lines using The Odds API"""
    
    def __init__(self, api_key: str = "14b669db87ed65f1d0f3e70a90386707"):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.lines = {}
        
    def test_api(self):
        """Test if API key works"""
        url = f"{self.base_url}/sports"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                print("✅ API Key is valid!")
                print(f"Remaining requests: {response.headers.get('x-requests-remaining', 'N/A')}")
                return True
            else:
                print(f"❌ API Error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def get_mlb_totals(self) -> Dict:
        """Fetch MLB game totals"""
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
            print(f"API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                games = response.json()
                print(f"Found {len(games)} games")
                
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
                                            print(f"  {away_team} @ {home_team}: {total}")
                                            break
                                    break
                            break
                
                print(f"\n✅ Fetched {len(self.lines)} team totals")
                print(f"Remaining API calls: {response.headers.get('x-requests-remaining', 'N/A')}")
                return self.lines
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Error fetching odds: {e}")
            return {}
    
    def _normalize_team(self, team_name: str) -> str:
        """Convert API team names to DFS abbreviations"""
        team_map = {
            "Arizona Diamondbacks": "ARI",
            "Atlanta Braves": "ATL",
            "Baltimore Orioles": "BAL",
            "Boston Red Sox": "BOS",
            "Chicago Cubs": "CHC",
            "Chicago White Sox": "CWS",
            "Cincinnati Reds": "CIN",
            "Cleveland Guardians": "CLE",
            "Colorado Rockies": "COL",
            "Detroit Tigers": "DET",
            "Houston Astros": "HOU",
            "Kansas City Royals": "KC",
            "Los Angeles Angels": "LAA",
            "Los Angeles Dodgers": "LAD",
            "Miami Marlins": "MIA",
            "Milwaukee Brewers": "MIL",
            "Minnesota Twins": "MIN",
            "New York Mets": "NYM",
            "New York Yankees": "NYY",
            "Oakland Athletics": "OAK",
            "Philadelphia Phillies": "PHI",
            "Pittsburgh Pirates": "PIT",
            "San Diego Padres": "SD",
            "San Francisco Giants": "SF",
            "Seattle Mariners": "SEA",
            "St. Louis Cardinals": "STL",
            "Tampa Bay Rays": "TB",
            "Texas Rangers": "TEX",
            "Toronto Blue Jays": "TOR",
            "Washington Nationals": "WSH"
        }
        return team_map.get(team_name, team_name[:3].upper())
    
    def enrich_players(self, players: List) -> int:
        """Apply Vegas totals to players"""
        if not self.lines:
            self.get_mlb_totals()
        
        enriched = 0
        for player in players:
            if hasattr(player, 'team') and player.team in self.lines:
                game_info = self.lines[player.team]
                game_total = game_info['total']
                
                # Store Vegas data
                player.vegas_total = game_total
                player.vegas_opponent = game_info.get('opponent', 'UNK')
                
                # Apply boost based on game total
                if game_total >= 9.5:  # High scoring game
                    if hasattr(player, 'primary_position'):
                        if player.primary_position == 'P':
                            player.vegas_boost = 0.95  # Slight negative for pitchers
                        else:
                            player.vegas_boost = 1.05  # Positive for hitters
                elif game_total <= 7.5:  # Low scoring game  
                    if hasattr(player, 'primary_position'):
                        if player.primary_position == 'P':
                            player.vegas_boost = 1.05  # Positive for pitchers
                        else:
                            player.vegas_boost = 0.95  # Negative for hitters
                else:
                    player.vegas_boost = 1.0
                
                enriched += 1
                    
        print(f"\n🎰 Applied Vegas data to {enriched} players")
        return enriched

# Test function
def test_vegas_api():
    print("🎰 Testing Vegas Lines API...")
    print("="*50)
    
    vegas = VegasLinesAPI()
    
    # Test 1: Check API key
    print("\n1️⃣ Testing API Key...")
    if not vegas.test_api():
        return
    
    # Test 2: Get MLB totals
    print("\n2️⃣ Fetching MLB Game Totals...")
    totals = vegas.get_mlb_totals()
    
    if totals:
        print(f"\n✅ Success! Found totals for {len(totals)} teams")
        print("\nSample totals:")
        for team, info in list(totals.items())[:5]:
            print(f"  {team}: {info['total']} vs {info['opponent']}")
    else:
        print("❌ No totals found")

if __name__ == "__main__":
    test_vegas_api()
