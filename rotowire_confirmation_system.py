#!/usr/bin/env python3
"""
Enhanced confirmation system that uses RotoWire for lineups
Since RotoWire has 682 lineup sections, we'll parse those!
"""

import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Tuple, Optional


class EnhancedConfirmationSystem:
    """Get confirmations from MLB API (pitchers) and RotoWire (lineups)"""

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.confirmed_lineups = {}
        self.confirmed_pitchers = {}
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_all_confirmations(self) -> Tuple[int, int]:
        """Get confirmations from all sources"""
        if self.verbose:
            print("🔍 ENHANCED CONFIRMATION SYSTEM")
            print("=" * 60)

        # 1. Get pitchers from MLB API (we know this works)
        mlb_pitchers = self._fetch_mlb_pitchers()

        # 2. Get lineups from RotoWire (has 682 sections!)
        rotowire_lineups = self._fetch_rotowire_lineups()

        # Calculate totals
        lineup_count = sum(len(lineup) for lineup in self.confirmed_lineups.values())
        pitcher_count = len(self.confirmed_pitchers)

        if self.verbose:
            print(f"\n📊 TOTAL CONFIRMATIONS:")
            print(f"   Players in lineups: {lineup_count}")
            print(f"   Starting pitchers: {pitcher_count}")
            print(f"   Teams with data: {len(self.confirmed_lineups)}")

        return lineup_count, pitcher_count

    def _fetch_mlb_pitchers(self) -> int:
        """Get today's starting pitchers from MLB API"""
        if self.verbose:
            print("\n📡 Fetching MLB starting pitchers...")

        today = datetime.now().strftime('%Y-%m-%d')
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=probablePitcher"

        try:
            response = self._session.get(url, timeout=10)
            if response.status_code != 200:
                return 0

            data = response.json()
            count = 0

            for date_entry in data.get('dates', []):
                for game in date_entry.get('games', []):
                    for side in ['home', 'away']:
                        team_data = game.get('teams', {}).get(side, {})
                        team_abbr = team_data.get('team', {}).get('abbreviation', '')

                        pitcher = team_data.get('probablePitcher')
                        if pitcher and team_abbr:
                            self.confirmed_pitchers[team_abbr] = {
                                'name': pitcher.get('fullName', ''),
                                'team': team_abbr,
                                'source': 'mlb_api'
                            }
                            count += 1

            if self.verbose:
                print(f"   ✅ Found {count} starting pitchers")

            return count

        except Exception as e:
            if self.verbose:
                print(f"   ❌ MLB API error: {e}")
            return 0

    def _fetch_rotowire_lineups(self) -> int:
        """Parse lineups from RotoWire"""
        if self.verbose:
            print("\n📡 Fetching RotoWire lineups...")

        url = "https://www.rotowire.com/baseball/daily-lineups.php"

        try:
            response = self._session.get(url, timeout=15)
            if response.status_code != 200:
                return 0

            soup = BeautifulSoup(response.text, 'html.parser')
            count = 0

            # RotoWire uses different class names, let's find the right structure
            # Look for lineup containers
            lineup_containers = soup.find_all(['div', 'section'], class_=re.compile('lineup|game', re.I))

            if self.verbose:
                print(f"   Found {len(lineup_containers)} potential lineup containers")

            # Also try to find by common patterns
            for container in lineup_containers:
                # Look for team names
                team_elements = container.find_all(text=re.compile(
                    r'(Yankees|Red Sox|Dodgers|Giants|Phillies|Padres|Nationals|Cubs|White Sox|Pirates)', re.I))

                if team_elements:
                    # Try to extract lineup data
                    players = []

                    # Look for player names (usually in specific patterns)
                    player_links = container.find_all('a', href=re.compile('/baseball/player/'))

                    for link in player_links[:9]:  # Max 9 players per lineup
                        player_name = link.get_text(strip=True)
                        if player_name and len(player_name) > 3:  # Valid name
                            players.append({
                                'name': player_name,
                                'order': len(players) + 1
                            })

                    if players:
                        # Try to determine team
                        team_abbr = self._extract_team_from_container(container)
                        if team_abbr:
                            self.confirmed_lineups[team_abbr] = players
                            count += len(players)

            # Alternative parsing method - look for specific lineup structure
            if count == 0:
                # Try finding by lineup class patterns
                lineup_divs = soup.find_all('div', class_=['lineup__list', 'lineup-list', 'lineups__lineup'])

                for lineup_div in lineup_divs:
                    players = self._parse_lineup_from_div(lineup_div)
                    if players:
                        team_abbr = self._find_team_for_lineup(lineup_div)
                        if team_abbr:
                            self.confirmed_lineups[team_abbr] = players
                            count += len(players)

            if self.verbose:
                print(f"   ✅ Parsed {count} player entries from {len(self.confirmed_lineups)} teams")

                # Show sample lineups
                if self.confirmed_lineups:
                    sample_team = list(self.confirmed_lineups.keys())[0]
                    sample_lineup = self.confirmed_lineups[sample_team]
                    print(f"\n   📋 Sample lineup for {sample_team}:")
                    for player in sample_lineup[:3]:
                        print(f"      {player['order']}. {player['name']}")
                    if len(sample_lineup) > 3:
                        print(f"      ... and {len(sample_lineup) - 3} more")

            return count

        except Exception as e:
            if self.verbose:
                print(f"   ❌ RotoWire error: {e}")
            return 0

    def _extract_team_from_container(self, container) -> Optional[str]:
        """Extract team abbreviation from container"""
        # Common team name to abbreviation mapping
        team_map = {
            'phillies': 'PHI', 'philadelphia': 'PHI',
            'padres': 'SD', 'san diego': 'SD',
            'nationals': 'WSH', 'washington': 'WSH',
            'yankees': 'NYY', 'new york yankees': 'NYY',
            'mets': 'NYM', 'new york mets': 'NYM',
            'red sox': 'BOS', 'boston': 'BOS',
            'dodgers': 'LAD', 'los angeles dodgers': 'LAD',
            'angels': 'LAA', 'los angeles angels': 'LAA',
            # Add more as needed
        }

        container_text = container.get_text().lower()

        for team_name, abbr in team_map.items():
            if team_name in container_text:
                return abbr

        return None

    def _parse_lineup_from_div(self, div) -> List[Dict]:
        """Parse player lineup from a div element"""
        players = []

        # Look for player elements
        player_elements = div.find_all(['a', 'span', 'div'], class_=re.compile('player|name', re.I))

        for elem in player_elements[:9]:  # Max 9 players
            name = elem.get_text(strip=True)
            if name and len(name) > 3 and not name.isdigit():
                players.append({
                    'name': name,
                    'order': len(players) + 1
                })

        return players

    def _find_team_for_lineup(self, lineup_div) -> Optional[str]:
        """Find team abbreviation for a lineup div"""
        # Look in parent elements for team info
        parent = lineup_div.parent
        if parent:
            return self._extract_team_from_container(parent)
        return None

    def apply_to_dfs_players(self, players) -> int:
        """Apply confirmations to DFS player objects"""
        confirmed_count = 0

        for player in players:
            player_name = player.name
            player_team = player.team

            # Check if player is in lineup
            if player_team in self.confirmed_lineups:
                for lineup_player in self.confirmed_lineups[player_team]:
                    if self._names_match(player_name, lineup_player['name']):
                        player.is_confirmed = True
                        player.add_confirmation_source('rotowire_lineup')
                        player.batting_order = lineup_player.get('order', 1)
                        confirmed_count += 1
                        break

            # Check if pitcher
            if player.primary_position == 'P' and player_team in self.confirmed_pitchers:
                pitcher_info = self.confirmed_pitchers[player_team]
                if self._names_match(player_name, pitcher_info['name']):
                    player.is_confirmed = True
                    player.add_confirmation_source('mlb_starter')
                    confirmed_count += 1

        return confirmed_count

    def _names_match(self, name1: str, name2: str) -> bool:
        """Flexible name matching"""
        clean1 = name1.lower().strip()
        clean2 = name2.lower().strip()

        # Exact match
        if clean1 == clean2:
            return True

        # Last name match
        parts1 = clean1.split()
        parts2 = clean2.split()

        if parts1 and parts2:
            if parts1[-1] == parts2[-1]:  # Last names match
                # Check first name or initial
                if len(parts1[0]) >= 1 and len(parts2[0]) >= 1:
                    if parts1[0][0] == parts2[0][0]:  # First initial matches
                        return True

        # One contains the other
        if clean1 in clean2 or clean2 in clean1:
            return True

        return False


# Integration function for your existing system
def enhance_confirmation_system(core_instance):
    """Enhance the existing confirmation system with RotoWire data"""
    print("\n🚀 ENHANCING CONFIRMATION SYSTEM")

    # Create enhanced system
    enhanced = EnhancedConfirmationSystem(verbose=True)

    # Get all confirmations
    lineup_count, pitcher_count = enhanced.get_all_confirmations()

    if lineup_count > 0 or pitcher_count > 0:
        # Apply to players
        confirmed_count = enhanced.apply_to_dfs_players(core_instance.players)
        print(f"\n✅ Enhanced confirmations applied to {confirmed_count} players")

        # Also exclude pitchers not starting
        excluded = 0
        for player in core_instance.players:
            if player.primary_position == 'P' and not player.is_confirmed:
                player.enhanced_score = 0
                player.projection = 0
                excluded += 1

        print(f"❌ Excluded {excluded} pitchers not starting today")

        return confirmed_count
    else:
        print("⚠️ No enhanced confirmations available")
        return 0


if __name__ == "__main__":
    # Test the system
    system = EnhancedConfirmationSystem(verbose=True)
    lineup_count, pitcher_count = system.get_all_confirmations()

    print(f"\n✅ Test complete: {lineup_count} lineup spots, {pitcher_count} pitchers")