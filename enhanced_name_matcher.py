#!/usr/bin/env python3
"""
ENHANCED NAME MATCHING SYSTEM
============================
Fixes issues with current system while keeping sophisticated matching
"""

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Set, List, Dict


class EnhancedNameMatcher:
    """
    Enhanced name matching that fixes issues with the current system
    - Better caching
    - Fixed nickname handling
    - Improved performance
    - Better edge case handling
    - More accurate thresholds
    """

    def __init__(self):
        # Enhanced nickname mappings (more complete)
        self.NICKNAME_MAPPINGS = {
            # Traditional nicknames
            'mike': 'michael', 'chris': 'christopher', 'alex': 'alexander',
            'matt': 'matthew', 'dave': 'david', 'steve': 'steven',
            'tom': 'thomas', 'bob': 'robert', 'bill': 'william',
            'dan': 'daniel', 'rob': 'robert', 'jim': 'james',
            'joe': 'joseph', 'tony': 'anthony', 'rick': 'richard',
            'tim': 'timothy', 'ben': 'benjamin', 'sam': 'samuel',
            'nick': 'nicholas', 'pat': 'patrick', 'ed': 'edward',

            # Baseball-specific nicknames
            'whit': 'whitney', 'chas': 'charles', 'xander': 'alexander',
            'buster': 'gerald', 'coco': 'covelli', 'trea': 'nelson',

            # Initials and abbreviations
            'dj': 'david', 'tj': 'thomas', 'aj': 'anthony', 'jd': 'john',
            'rj': 'ronald', 'cj': 'calvin', 'bj': 'bobby', 'mj': 'michael',

            # International variations
            'jose': 'josé', 'jesus': 'jesús', 'carlos': 'carlos',
            'luis': 'luís', 'angel': 'ángel', 'martin': 'martín'
        }

        # Build reverse mapping for efficiency
        self.reverse_nicknames = {}
        for nick, full in self.NICKNAME_MAPPINGS.items():
            if full not in self.reverse_nicknames:
                self.reverse_nicknames[full] = []
            self.reverse_nicknames[full].append(nick)

        # Caching for performance
        self._normalization_cache = {}
        self._matching_cache = {}

        # Team mappings for context
        self.TEAM_MAPPINGS = {
            'arizona': 'ARI', 'atlanta': 'ATL', 'baltimore': 'BAL', 'boston': 'BOS',
            'chicago cubs': 'CHC', 'cubs': 'CHC', 'chicago white sox': 'CWS', 'white sox': 'CWS',
            'cincinnati': 'CIN', 'cleveland': 'CLE', 'colorado': 'COL', 'detroit': 'DET',
            'houston': 'HOU', 'kansas city': 'KC', 'los angeles angels': 'LAA', 'angels': 'LAA',
            'los angeles dodgers': 'LAD', 'dodgers': 'LAD', 'miami': 'MIA', 'milwaukee': 'MIL',
            'minnesota': 'MIN', 'new york mets': 'NYM', 'mets': 'NYM', 'new york yankees': 'NYY',
            'yankees': 'NYY', 'oakland': 'OAK', 'philadelphia': 'PHI', 'pittsburgh': 'PIT',
            'san diego': 'SD', 'san francisco': 'SF', 'seattle': 'SEA', 'st louis': 'STL',
            'cardinals': 'STL', 'tampa bay': 'TB', 'rays': 'TB', 'texas': 'TEX', 'rangers': 'TEX',
            'toronto': 'TOR', 'blue jays': 'TOR', 'washington': 'WSH', 'nationals': 'WSH'
        }

    def normalize_team(self, team_name: str) -> str:
        """Enhanced team normalization"""
        if not team_name:
            return ""

        clean_name = team_name.lower().strip()

        # Direct lookup
        if clean_name in self.TEAM_MAPPINGS:
            return self.TEAM_MAPPINGS[clean_name]

        # Check if already an abbreviation
        if len(clean_name) <= 3 and clean_name.upper() in self.TEAM_MAPPINGS.values():
            return clean_name.upper()

        # Partial matching
        for key, abbrev in self.TEAM_MAPPINGS.items():
            if key in clean_name or clean_name in key:
                return abbrev

        return team_name.upper()[:3]

    def match_player_names(self, name1: str, name2: str, threshold: float = 0.80) -> bool:
        """
        Enhanced player name matching with better accuracy
        """
        if not name1 or not name2:
            return False

        # Convert to strings and basic validation
        name1 = str(name1).strip()
        name2 = str(name2).strip()

        if not name1 or not name2:
            return False

        # Check cache first
        cache_key = f"{name1.lower()}||{name2.lower()}"
        if cache_key in self._matching_cache:
            return self._matching_cache[cache_key]

        try:
            result = self._enhanced_name_matching(name1, name2, threshold)
            self._matching_cache[cache_key] = result
            return result
        except Exception as e:
            # Fallback to simple matching if anything breaks
            simple_result = name1.lower().strip() == name2.lower().strip()
            self._matching_cache[cache_key] = simple_result
            return simple_result

    def _enhanced_name_matching(self, name1: str, name2: str, threshold: float) -> bool:
        """Core enhanced matching logic"""

        # 1. EXACT MATCH (fastest check)
        if name1.lower() == name2.lower():
            return True

        # 2. NORMALIZE BOTH NAMES
        norm1 = self._normalize_name_enhanced(name1)
        norm2 = self._normalize_name_enhanced(name2)

        if norm1 == norm2:
            return True

        # 3. QUICK REJECTION FILTERS
        # If names are very different lengths, unlikely to match
        if abs(len(norm1) - len(norm2)) > 8:
            return False

        # If they share very few characters, unlikely to match
        chars1 = set(norm1.replace(' ', ''))
        chars2 = set(norm2.replace(' ', ''))
        shared_chars = len(chars1 & chars2)
        min_chars = min(len(chars1), len(chars2))
        if min_chars > 0 and shared_chars / min_chars < 0.4:
            return False

        # 4. SPLIT INTO PARTS AND ANALYZE
        parts1 = norm1.split()
        parts2 = norm2.split()

        if not parts1 or not parts2:
            return False

        # 5. SMART PART-BY-PART MATCHING
        if self._match_name_parts(parts1, parts2):
            return True

        # 6. FUZZY MATCHING (only for close cases)
        if abs(len(norm1) - len(norm2)) <= 4:
            try:
                similarity = SequenceMatcher(None, norm1, norm2).ratio()
                return similarity >= threshold
            except:
                return False

        return False

    def _normalize_name_enhanced(self, name: str) -> str:
        """Enhanced name normalization with caching"""
        if name in self._normalization_cache:
            return self._normalization_cache[name]

        # Convert to lowercase
        normalized = name.lower().strip()

        # Remove accents and diacritics
        normalized = unicodedata.normalize('NFD', normalized)
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')

        # Remove common suffixes (Jr, Sr, II, III, etc.)
        normalized = re.sub(r'\b(jr\.?|sr\.?|ii+|iii+|iv|v|2nd|3rd)\b', '', normalized)

        # Handle common punctuation patterns
        normalized = re.sub(r'([a-z])\.([a-z])', r'\1 \2', normalized)  # J.D. -> J D
        normalized = re.sub(r'[^\w\s]', ' ', normalized)  # Remove punctuation

        # Clean up whitespace
        normalized = ' '.join(normalized.split())

        # Cache result
        self._normalization_cache[name] = normalized
        return normalized

    def _match_name_parts(self, parts1: List[str], parts2: List[str]) -> bool:
        """Smart matching of name parts"""

        # If same number of parts, try direct matching
        if len(parts1) == len(parts2):
            matches = 0
            for p1, p2 in zip(parts1, parts2):
                if self._match_single_part(p1, p2):
                    matches += 1

            # Require at least 80% of parts to match
            return matches / len(parts1) >= 0.8

        # Different number of parts - try flexible matching
        # This handles cases like "Michael Trout" vs "Mike Trout Jr."

        shorter_parts = parts1 if len(parts1) < len(parts2) else parts2
        longer_parts = parts2 if len(parts1) < len(parts2) else parts1

        matched_shorter = 0
        for short_part in shorter_parts:
            for long_part in longer_parts:
                if self._match_single_part(short_part, long_part):
                    matched_shorter += 1
                    break

        # At least 80% of shorter name parts should match
        if len(shorter_parts) > 0:
            return matched_shorter / len(shorter_parts) >= 0.8

        return False

    def _match_single_part(self, part1: str, part2: str) -> bool:
        """Match individual name parts with nickname awareness"""

        # Exact match
        if part1 == part2:
            return True

        # One contains the other (handles partial names)
        if part1 in part2 or part2 in part1:
            return True

        # Nickname matching
        if self._check_nicknames(part1, part2):
            return True

        # Initial matching (for single letters)
        if len(part1) == 1 or len(part2) == 1:
            return part1[0] == part2[0]

        # Very short parts (2-3 chars) need exact match
        if len(part1) <= 3 and len(part2) <= 3:
            return part1 == part2

        # For longer parts, check character overlap
        if len(part1) >= 4 and len(part2) >= 4:
            chars1 = set(part1)
            chars2 = set(part2)
            overlap = len(chars1 & chars2)
            min_len = min(len(part1), len(part2))
            return overlap / min_len >= 0.75

        return False

    def _check_nicknames(self, name1: str, name2: str) -> bool:
        """Check if names are nickname variants"""

        # Direct nickname mapping
        if name1 in self.NICKNAME_MAPPINGS and self.NICKNAME_MAPPINGS[name1] == name2:
            return True
        if name2 in self.NICKNAME_MAPPINGS and self.NICKNAME_MAPPINGS[name2] == name1:
            return True

        # Reverse nickname mapping
        if name1 in self.reverse_nicknames and name2 in self.reverse_nicknames[name1]:
            return True
        if name2 in self.reverse_nicknames and name1 in self.reverse_nicknames[name2]:
            return True

        return False

    def get_teams_from_players(self, players: List) -> Set[str]:
        """Extract teams from player list"""
        teams = set()
        for player in players:
            if hasattr(player, 'team'):
                team = self.normalize_team(player.team)
            elif isinstance(player, dict):
                team = self.normalize_team(player.get('team', ''))
            else:
                continue

            if team:
                teams.add(team)

        return teams

    def clear_cache(self):
        """Clear all caches"""
        self._normalization_cache.clear()
        self._matching_cache.clear()

    def get_cache_stats(self) -> Dict:
        """Get cache performance stats"""
        return {
            'normalization_cache_size': len(self._normalization_cache),
            'matching_cache_size': len(self._matching_cache),
            'total_cache_entries': len(self._normalization_cache) + len(self._matching_cache)
        }


# Drop-in replacement for UnifiedDataSystem
class ImprovedUnifiedDataSystem(EnhancedNameMatcher):
    """
    Enhanced UnifiedDataSystem with better name matching
    Can replace your current UnifiedDataSystem
    """

    def __init__(self):
        super().__init__()
        # Keep any additional attributes from original system
        self.team_lookup = {}
        for team, abbrev in self.TEAM_MAPPINGS.items():
            self.team_lookup[team] = abbrev

        # Add abbreviations pointing to themselves
        for abbrev in self.TEAM_MAPPINGS.values():
            self.team_lookup[abbrev.lower()] = abbrev

    def clean_player_name(self, name: str) -> str:
        """Alias for normalize_name_enhanced"""
        return self._normalize_name_enhanced(name)


def test_enhanced_system():
    """Quick test of the enhanced system"""
    matcher = EnhancedNameMatcher()

    test_cases = [
        ("Mike Trout", "Michael Trout", True),
        ("J.D. Martinez", "JD Martinez", True),
        ("Vladimir Guerrero Jr.", "Vladimir Guerrero", True),
        ("José Altuve", "Jose Altuve", True),
        ("Chris Sale", "Christopher Sale", True),
        ("Mike Trout", "Mike Moustakas", False),
    ]

    print("🧪 Testing Enhanced Name Matching:")
    correct = 0
    for name1, name2, expected in test_cases:
        actual = matcher.match_player_names(name1, name2)
        status = "✅" if actual == expected else "❌"
        print(f"  {status} {name1} vs {name2}: {actual}")
        if actual == expected:
            correct += 1

    print(f"\n📊 Results: {correct}/{len(test_cases)} correct ({correct / len(test_cases) * 100:.1f}%)")
    print(f"📈 Cache stats: {matcher.get_cache_stats()}")


if __name__ == "__main__":
    test_enhanced_system()