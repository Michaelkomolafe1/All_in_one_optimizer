#!/usr/bin/env python3
"""
ROTOWIRE PITCHER CONFIRMATION SYSTEM
====================================
Fetches confirmed starting pitchers from Rotowire
Works when MLB API fails to provide pitcher data
"""

import requests
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import re
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)


class RotowirePitcherSystem:
    """
    Dedicated system for fetching starting pitcher confirmations from Rotowire
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.confirmed_pitchers = {}
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_rotowire_pitchers(self) -> Dict[str, Dict]:
        """
        Fetch confirmed starting pitchers from Rotowire

        Returns:
            Dict mapping team abbreviation to pitcher info
        """
        if self.verbose:
            print("\n📰 Fetching Rotowire Starting Pitchers...")

        self.confirmed_pitchers.clear()

        try:
            # Rotowire MLB lineups page
            url = "https://www.rotowire.com/baseball/daily-lineups.php"

            response = self._session.get(url, timeout=10)
            if response.status_code != 200:
                if self.verbose:
                    print(f"❌ Rotowire returned status {response.status_code}")
                return self.confirmed_pitchers

            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Debug: Check page content
            if self.verbose and len(response.text) < 1000:
                print(f"   ⚠️  Page seems too short: {len(response.text)} bytes")

            # Try multiple selectors for games
            games = soup.find_all('div', class_='lineup__game')
            if not games:
                # Try alternative selector
                games = soup.find_all('div', class_='lineup-card')
                if self.verbose and not games:
                    print("   ⚠️  No games found with standard selectors")
                    # Check if there's a "no games" message
                    no_games = soup.find(text=re.compile('no games', re.I))
                    if no_games:
                        print("   ℹ️  No games scheduled today")

            if self.verbose:
                print(f"   Found {len(games)} games")

            for game in games:
                try:
                    # Extract teams
                    teams = game.find_all('div', class_='lineup__team-name')
                    if len(teams) != 2:
                        continue

                    away_team = self._extract_team_abbr(teams[0].text.strip())
                    home_team = self._extract_team_abbr(teams[1].text.strip())

                    # Extract pitchers
                    pitchers = game.find_all('div', class_='lineup__player--pitcher')

                    if len(pitchers) >= 2:
                        # Away pitcher
                        away_pitcher_elem = pitchers[0].find('a')
                        if away_pitcher_elem:
                            away_pitcher_name = away_pitcher_elem.text.strip()
                            self.confirmed_pitchers[away_team] = {
                                'name': away_pitcher_name,
                                'team': away_team,
                                'opponent': home_team,
                                'source': 'rotowire',
                                'home': False
                            }

                        # Home pitcher
                        home_pitcher_elem = pitchers[1].find('a')
                        if home_pitcher_elem:
                            home_pitcher_name = home_pitcher_elem.text.strip()
                            self.confirmed_pitchers[home_team] = {
                                'name': home_pitcher_name,
                                'team': home_team,
                                'opponent': away_team,
                                'source': 'rotowire',
                                'home': True
                            }

                except Exception as e:
                    if self.verbose:
                        print(f"   ⚠️ Error parsing game: {e}")
                    continue

            if self.verbose:
                print(f"   ✅ Found {len(self.confirmed_pitchers)} starting pitchers")

                # Show sample pitchers
                if self.confirmed_pitchers:
                    print("\n   Sample confirmed pitchers:")
                    for team, info in list(self.confirmed_pitchers.items())[:5]:
                        print(f"     {team}: {info['name']} vs {info['opponent']}")

        except Exception as e:
            if self.verbose:
                print(f"❌ Rotowire fetch error: {e}")
                import traceback
                traceback.print_exc()

        return self.confirmed_pitchers

    def _extract_team_abbr(self, team_text: str) -> str:
        """Extract team abbreviation from team text"""
        # Common team name to abbreviation mapping
        team_map = {
            'Diamondbacks': 'ARI', 'D-backs': 'ARI',
            'Braves': 'ATL',
            'Orioles': 'BAL',
            'Red Sox': 'BOS',
            'Cubs': 'CHC',
            'White Sox': 'CWS',
            'Reds': 'CIN',
            'Guardians': 'CLE', 'Indians': 'CLE',
            'Rockies': 'COL',
            'Tigers': 'DET',
            'Astros': 'HOU',
            'Royals': 'KC',
            'Angels': 'LAA',
            'Dodgers': 'LAD',
            'Marlins': 'MIA',
            'Brewers': 'MIL',
            'Twins': 'MIN',
            'Yankees': 'NYY',
            'Mets': 'NYM',
            'Athletics': 'OAK', 'A\'s': 'OAK',
            'Phillies': 'PHI',
            'Pirates': 'PIT',
            'Padres': 'SD',
            'Giants': 'SF',
            'Mariners': 'SEA',
            'Cardinals': 'STL',
            'Rays': 'TB',
            'Rangers': 'TEX',
            'Blue Jays': 'TOR',
            'Nationals': 'WSH'
        }

        # Try to match team name
        for name, abbr in team_map.items():
            if name.lower() in team_text.lower():
                return abbr

        # If no match, try to extract 2-3 letter abbreviation
        abbr_match = re.search(r'\b([A-Z]{2,3})\b', team_text)
        if abbr_match:
            return abbr_match.group(1)

        return team_text[:3].upper()  # Fallback

    def get_pitcher_for_team(self, team: str) -> Optional[Dict]:
        """Get confirmed pitcher for a specific team"""
        return self.confirmed_pitchers.get(team)

    def is_pitcher_confirmed(self, pitcher_name: str, team: str = None) -> bool:
        """Check if a pitcher is confirmed as starter"""
        pitcher_lower = pitcher_name.lower().strip()

        if team:
            # Check specific team
            team_pitcher = self.confirmed_pitchers.get(team)
            if team_pitcher:
                confirmed_name = team_pitcher['name'].lower().strip()
                return self._names_match(pitcher_lower, confirmed_name)
        else:
            # Check all teams
            for team_info in self.confirmed_pitchers.values():
                confirmed_name = team_info['name'].lower().strip()
                if self._names_match(pitcher_lower, confirmed_name):
                    return True

        return False

    def _names_match(self, name1: str, name2: str) -> bool:
        """Fuzzy name matching"""
        # Exact match
        if name1 == name2:
            return True

        # Remove common suffixes
        for suffix in [' jr.', ' sr.', ' jr', ' sr', ' iii', ' ii']:
            name1 = name1.replace(suffix, '')
            name2 = name2.replace(suffix, '')

        # Check if one name contains the other
        if name1 in name2 or name2 in name1:
            return True

        # Last name match (assuming format "First Last")
        parts1 = name1.split()
        parts2 = name2.split()

        if len(parts1) >= 2 and len(parts2) >= 2:
            if parts1[-1] == parts2[-1]:  # Last names match
                # Check if first names start with same letter
                if parts1[0][0] == parts2[0][0]:
                    return True

        return False


# Enhanced Smart Confirmation System that uses BOTH sources
class EnhancedConfirmationSystem:
    """
    Combines MLB API and Rotowire for comprehensive confirmations
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

        # Initialize both systems
        from smart_confirmation_system import SmartConfirmationSystem
        self.mlb_system = SmartConfirmationSystem(verbose=False)
        self.rotowire_system = RotowirePitcherSystem(verbose=verbose)

        # Combined results
        self.all_pitchers = {}
        self.all_lineups = {}

    def fetch_all_confirmations(self) -> Tuple[Dict, Dict]:
        """
        Fetch confirmations from both MLB API and Rotowire

        Returns:
            (lineups_dict, pitchers_dict)
        """
        if self.verbose:
            print("\n🎯 ENHANCED CONFIRMATION SYSTEM")
            print("=" * 60)

        # 1. Try MLB API first
        if self.verbose:
            print("\n1️⃣ Checking MLB API...")

        lineup_count, pitcher_count = self.mlb_system.get_all_confirmations()
        self.all_lineups = self.mlb_system.confirmed_lineups.copy()
        mlb_pitchers = self.mlb_system.confirmed_pitchers.copy()

        if self.verbose:
            print(f"   MLB API: {lineup_count} lineup players, {pitcher_count} pitchers")

        # 2. Get Rotowire pitchers
        if self.verbose:
            print("\n2️⃣ Checking Rotowire...")

        rotowire_pitchers = self.rotowire_system.fetch_rotowire_pitchers()

        # 3. Merge pitcher data (Rotowire takes precedence if MLB failed)
        if pitcher_count == 0 and rotowire_pitchers:
            # MLB API failed, use Rotowire
            self.all_pitchers = rotowire_pitchers
            if self.verbose:
                print(f"   ✅ Using Rotowire pitchers: {len(rotowire_pitchers)}")
        else:
            # Merge both sources
            self.all_pitchers = mlb_pitchers.copy()

            # Add any missing pitchers from Rotowire
            for team, pitcher_info in rotowire_pitchers.items():
                if team not in self.all_pitchers:
                    self.all_pitchers[team] = pitcher_info

            if self.verbose:
                print(f"   ✅ Combined pitchers: {len(self.all_pitchers)}")

        # Summary
        if self.verbose:
            print(f"\n📊 FINAL CONFIRMATION TOTALS:")
            print(f"   Lineups: {lineup_count} players")
            print(f"   Pitchers: {len(self.all_pitchers)} starters")

        return self.all_lineups, self.all_pitchers

    def is_pitcher_confirmed(self, pitcher_name: str, team: str = None) -> bool:
        """Check if pitcher is confirmed in either system"""
        # Check merged results
        if team and team in self.all_pitchers:
            pitcher_info = self.all_pitchers[team]
            return self.rotowire_system._names_match(
                pitcher_name.lower().strip(),
                pitcher_info['name'].lower().strip()
            )

        # Check all teams
        for pitcher_info in self.all_pitchers.values():
            if self.rotowire_system._names_match(
                    pitcher_name.lower().strip(),
                    pitcher_info['name'].lower().strip()
            ):
                return True

        return False


if __name__ == "__main__":
    print("🧪 TESTING PITCHER CONFIRMATION SYSTEMS")
    print("=" * 60)

    # Test Rotowire
    print("\n1️⃣ Testing Rotowire System...")
    rotowire = RotowirePitcherSystem()
    pitchers = rotowire.fetch_rotowire_pitchers()
    print(f"   Found {len(pitchers)} pitchers")

    # Test Enhanced System
    print("\n2️⃣ Testing Enhanced System...")
    enhanced = EnhancedConfirmationSystem()
    lineups, all_pitchers = enhanced.fetch_all_confirmations()

    print(f"\n✅ Enhanced system found {len(all_pitchers)} total pitchers")