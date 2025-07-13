#!/usr/bin/env python3
"""
UNIFIED DATA INTEGRATION SYSTEM
==============================
Handles all data sources with consistent team/name mapping
"""

import logging
import re
import unicodedata
from difflib import SequenceMatcher
from typing import List, Set

logger = logging.getLogger(__name__)


class UnifiedDataSystem:
    """Unified system for all data integration with consistent mapping"""

    def __init__(self):
        # Master team mapping - single source of truth
        self.TEAM_MAPPINGS = {
            # Primary mappings (DraftKings standard)
            "ARI": ["Arizona Diamondbacks", "Arizona", "Diamondbacks", "D-backs", "AZ"],
            "ATL": ["Atlanta Braves", "Atlanta", "Braves"],
            "BAL": ["Baltimore Orioles", "Baltimore", "Orioles", "O's"],
            "BOS": ["Boston Red Sox", "Boston", "Red Sox", "Sox"],
            "CHC": ["Chicago Cubs", "Cubs", "Chicago Cubs", "CHI Cubs"],
            "CWS": ["Chicago White Sox", "White Sox", "Chicago White Sox", "CHI White Sox", "CHW"],
            "CIN": ["Cincinnati Reds", "Cincinnati", "Reds"],
            "CLE": ["Cleveland Guardians", "Cleveland", "Guardians", "Indians"],
            "COL": ["Colorado Rockies", "Colorado", "Rockies"],
            "DET": ["Detroit Tigers", "Detroit", "Tigers"],
            "HOU": ["Houston Astros", "Houston", "Astros", "Stros"],
            "KC": ["Kansas City Royals", "Kansas City", "Royals", "KCR"],
            "LAA": ["Los Angeles Angels", "LA Angels", "Angels", "Anaheim"],
            "LAD": ["Los Angeles Dodgers", "LA Dodgers", "Dodgers"],
            "MIA": ["Miami Marlins", "Miami", "Marlins", "Florida"],
            "MIL": ["Milwaukee Brewers", "Milwaukee", "Brewers", "Brew Crew"],
            "MIN": ["Minnesota Twins", "Minnesota", "Twins"],
            "NYM": ["New York Mets", "NY Mets", "Mets"],
            "NYY": ["New York Yankees", "NY Yankees", "Yankees", "Yanks"],
            "OAK": ["Oakland Athletics", "Oakland", "Athletics", "A's"],
            "PHI": ["Philadelphia Phillies", "Philadelphia", "Phillies", "Phils"],
            "PIT": ["Pittsburgh Pirates", "Pittsburgh", "Pirates", "Bucs"],
            "SD": ["San Diego Padres", "San Diego", "Padres", "SDP"],
            "SF": ["San Francisco Giants", "San Francisco", "Giants", "SFG"],
            "SEA": ["Seattle Mariners", "Seattle", "Mariners", "M's"],
            "STL": ["St. Louis Cardinals", "St Louis", "Cardinals", "Cards"],
            "TB": ["Tampa Bay Rays", "Tampa Bay", "Rays", "TBR", "TAM"],
            "TEX": ["Texas Rangers", "Texas", "Rangers"],
            "TOR": ["Toronto Blue Jays", "Toronto", "Blue Jays", "Jays"],
            "WSH": ["Washington Nationals", "Washington", "Nationals", "Nats", "WAS"],
        }

        # Reverse mapping for quick lookups
        self.team_lookup = {}
        for abbrev, names in self.TEAM_MAPPINGS.items():
            for name in names:
                self.team_lookup[name.lower()] = abbrev
            self.team_lookup[abbrev.lower()] = abbrev

        # MLB API team ID mappings
        self.MLB_ID_MAPPINGS = {
            "109": "ARI",
            "144": "ATL",
            "110": "BAL",
            "111": "BOS",
            "112": "CHC",
            "145": "CWS",
            "113": "CIN",
            "114": "CLE",
            "115": "COL",
            "116": "DET",
            "117": "HOU",
            "118": "KC",
            "108": "LAA",
            "119": "LAD",
            "146": "MIA",
            "158": "MIL",
            "142": "MIN",
            "121": "NYM",
            "147": "NYY",
            "133": "OAK",
            "143": "PHI",
            "134": "PIT",
            "135": "SD",
            "137": "SF",
            "136": "SEA",
            "138": "STL",
            "139": "TB",
            "140": "TEX",
            "141": "TOR",
            "120": "WSH",
        }

        # Common nickname mappings
        self.NICKNAME_MAPPINGS = {
            # First name nicknames
            "bobby": "robert",
            "bob": "robert",
            "rob": "robert",
            "mike": "michael",
            "mick": "michael",
            "mickey": "michael",
            "dave": "david",
            "tony": "anthony",
            "ant": "anthony",
            "chris": "christopher",
            "matt": "matthew",
            "matty": "matthew",
            "joe": "joseph",
            "joey": "joseph",
            "josh": "joshua",
            "alex": "alexander",
            "andy": "andrew",
            "drew": "andrew",
            "danny": "daniel",
            "dan": "daniel",
            "tommy": "thomas",
            "tom": "thomas",
            "jimmy": "james",
            "jim": "james",
            "johnny": "john",
            "jon": "jonathan",
            "jake": "jacob",
            "nick": "nicholas",
            "nicky": "nicholas",
            "will": "william",
            "bill": "william",
            "billy": "william",
            "ken": "kenneth",
            "kenny": "kenneth",
            "ted": "theodore",
            "teddy": "theodore",
            "ricky": "richard",
            "rick": "richard",
            "dick": "richard",
            # Common baseball nicknames
            "aj": ["aaron", "anthony", "andrew"],
            "cj": ["charles", "christopher", "carl"],
            "dj": ["daniel", "david", "derek"],
            "tj": ["thomas", "timothy", "tyler"],
            "jj": ["joseph", "james", "john"],
            "jp": ["john", "james", "joseph"],
            "jd": ["john", "james", "joseph"],
            # Spanish nicknames
            "junior": "jr",
            "hijo": "jr",
        }

    def normalize_team(self, team_input: str) -> str:
        """
        Normalize any team input to standard 2-3 letter abbreviation

        Args:
            team_input: Team name, abbreviation, or ID

        Returns:
            Standard team abbreviation (e.g., 'NYY')
        """
        if not team_input:
            return ""

        team_input = str(team_input).strip()

        # Check if it's a numeric MLB ID
        if team_input.isdigit():
            return self.MLB_ID_MAPPINGS.get(team_input, team_input)

        # Check direct lookup
        team_lower = team_input.lower()
        if team_lower in self.team_lookup:
            return self.team_lookup[team_lower]

        # Check partial matches
        for full_name, abbrev in self.team_lookup.items():
            if team_lower in full_name or full_name in team_lower:
                return abbrev

        # Return original if no match (already abbreviated)
        return team_input.upper()[:3]

    def clean_player_name(self, name: str) -> str:
        """
        Clean and normalize player name

        Args:
            name: Player name to clean

        Returns:
            Cleaned name
        """
        if not name:
            return ""

        # Convert to lowercase and strip
        name = str(name).lower().strip()

        # Remove suffixes and punctuation
        name = re.sub(r"\b(jr\.?|sr\.?|iii?|iv|v)\b", "", name)
        name = re.sub(r"[^\w\s-]", " ", name)

        # Remove accents
        name = unicodedata.normalize("NFD", name)
        name = "".join(c for c in name if unicodedata.category(c) != "Mn")

        # Clean up whitespace
        name = " ".join(name.split())

        return name

    def match_player_names(self, dk_name: str, other_name: str, threshold: float = 0.80) -> bool:
        """Advanced name matching between DraftKings and other sources - MEMORY SAFE VERSION"""
        try:
            # Ensure we're working with strings
            dk_name = str(dk_name) if dk_name else ""
            other_name = str(other_name) if other_name else ""

            # Clean both names
            dk_clean = self.clean_player_name(dk_name)
            other_clean = self.clean_player_name(other_name)

            # Exact match
            if dk_clean == other_clean:
                return True

            # Quick length check to avoid unnecessary processing
            if abs(len(dk_clean) - len(other_clean)) > 10:
                return False

            # Split into parts
            dk_parts = dk_clean.split()
            other_parts = other_clean.split()

            if not dk_parts or not other_parts:
                return False

            # Get first and last names safely
            dk_first = dk_parts[0] if dk_parts else ""
            dk_last = dk_parts[-1] if dk_parts else ""
            other_first = other_parts[0] if other_parts else ""
            other_last = other_parts[-1] if other_parts else ""

            # Check if last names match
            if dk_last == other_last:
                # Check first names (exact or nickname)
                if dk_first == other_first:
                    return True

                # Check nickname mappings
                if dk_first in self.NICKNAME_MAPPINGS:
                    if isinstance(self.NICKNAME_MAPPINGS[dk_first], list):
                        if other_first in self.NICKNAME_MAPPINGS[dk_first]:
                            return True
                    elif other_first == self.NICKNAME_MAPPINGS[dk_first]:
                        return True

                # Check initials
                if len(dk_first) >= 1 and len(other_first) >= 1:
                    if dk_first[0] == other_first[0]:
                        return True

            # Skip fuzzy matching if strings are too different in length
            if abs(len(dk_clean) - len(other_clean)) > 5:
                return False

            # Use try-except for fuzzy matching
            try:
                similarity = SequenceMatcher(None, dk_clean, other_clean).ratio()
                return similarity >= threshold
            except:
                return False

        except Exception as e:
            print(f"❌ Name matching error: {e}")
            return False

    def get_teams_from_players(self, players: List) -> Set[str]:
        """
        Extract unique teams from player list

        Args:
            players: List of players

        Returns:
            Set of normalized team abbreviations
        """
        teams = set()

        for player in players:
            if hasattr(player, "team"):
                team = self.normalize_team(player.team)
            elif isinstance(player, dict):
                team = self.normalize_team(player.get("team", ""))
            elif isinstance(player, (list, tuple)) and len(player) > 3:
                team = self.normalize_team(player[3])
            else:
                continue

            if team:
                teams.add(team)

        return teams
