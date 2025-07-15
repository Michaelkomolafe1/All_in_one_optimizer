#!/usr/bin/env python3
"""
NAME MATCHING TEST FRAMEWORK
============================
Test your current system vs improved version with real examples
"""

import time
from typing import List, Tuple, Dict
from unified_data_system import UnifiedDataSystem


class NameMatchingTester:
    """Test framework to compare name matching systems"""

    def __init__(self):
        self.current_system = UnifiedDataSystem()

        # Common name matching problems in DFS
        self.test_cases = [
            # Format: (CSV_name, MLB_API_name, should_match)

            # Exact matches (should work)
            ("Mike Trout", "Mike Trout", True),
            ("Aaron Judge", "Aaron Judge", True),

            # Nickname variations (common issue)
            ("Mike Trout", "Michael Trout", True),
            ("Chris Sale", "Christopher Sale", True),
            ("Alex Bregman", "Alexander Bregman", True),
            ("Matt Olson", "Matthew Olson", True),
            ("DJ LeMahieu", "David LeMahieu", True),

            # Jr/Sr variations
            ("Vladimir Guerrero Jr.", "Vladimir Guerrero", True),
            ("Fernando Tatis Jr.", "Fernando Tatis", True),
            ("Ken Griffey Jr.", "Ken Griffey", True),

            # Punctuation differences
            ("J.D. Martinez", "JD Martinez", True),
            ("A.J. Pollock", "AJ Pollock", True),
            ("T.J. McFarland", "TJ McFarland", True),

            # Accent/special characters
            ("José Altuve", "Jose Altuve", True),
            ("Martín Maldonado", "Martin Maldonado", True),
            ("Yoán Moncada", "Yoan Moncada", True),

            # Should NOT match (different people)
            ("Mike Trout", "Mike Moustakas", False),
            ("Aaron Judge", "Aaron Nola", False),
            ("Chris Sale", "Chris Taylor", False),

            # Tricky cases
            ("Michael Harris II", "Michael Harris", True),
            ("Chas McCormick", "Charles McCormick", True),
            ("Ke'Bryan Hayes", "KeBryan Hayes", True),

            # Common DFS mismatches
            ("Luis Robert Jr.", "Luis Robert", True),
            ("Julio Rodriguez", "Julio Rodríguez", True),
            ("Andres Gimenez", "Andrés Giménez", True),

            # Edge cases that might fail
            ("Whit Merrifield", "Whitney Merrifield", True),
            ("Xander Bogaerts", "Alexander Bogaerts", True),
            ("Betts", "Mookie Betts", False),  # Too short
        ]

    def test_current_system(self) -> Dict:
        """Test the current UnifiedDataSystem"""
        print("🧪 Testing Current UnifiedDataSystem...")

        results = {
            'correct': 0,
            'incorrect': 0,
            'total': len(self.test_cases),
            'errors': [],
            'slow_matches': [],
            'failed_cases': []
        }

        for i, (name1, name2, expected) in enumerate(self.test_cases):
            try:
                start_time = time.time()
                actual = self.current_system.match_player_names(name1, name2)
                match_time = time.time() - start_time

                if match_time > 0.01:  # Flag slow matches (>10ms)
                    results['slow_matches'].append((name1, name2, match_time))

                if actual == expected:
                    results['correct'] += 1
                    status = "✅"
                else:
                    results['incorrect'] += 1
                    results['failed_cases'].append((name1, name2, expected, actual))
                    status = "❌"

                print(f"  {status} {name1} vs {name2}: {actual} (expected {expected})")

            except Exception as e:
                results['errors'].append((name1, name2, str(e)))
                results['incorrect'] += 1
                print(f"  ❌ ERROR: {name1} vs {name2}: {e}")

        return results

    def test_improved_system(self) -> Dict:
        """Test an improved name matching system"""
        print("\n🚀 Testing Improved Name Matching...")

        improved_system = ImprovedNameMatcher()

        results = {
            'correct': 0,
            'incorrect': 0,
            'total': len(self.test_cases),
            'errors': [],
            'slow_matches': [],
            'failed_cases': []
        }

        for i, (name1, name2, expected) in enumerate(self.test_cases):
            try:
                start_time = time.time()
                actual = improved_system.match_names(name1, name2)
                match_time = time.time() - start_time

                if match_time > 0.01:
                    results['slow_matches'].append((name1, name2, match_time))

                if actual == expected:
                    results['correct'] += 1
                    status = "✅"
                else:
                    results['incorrect'] += 1
                    results['failed_cases'].append((name1, name2, expected, actual))
                    status = "❌"

                print(f"  {status} {name1} vs {name2}: {actual} (expected {expected})")

            except Exception as e:
                results['errors'].append((name1, name2, str(e)))
                results['incorrect'] += 1
                print(f"  ❌ ERROR: {name1} vs {name2}: {e}")

        return results

    def compare_systems(self):
        """Compare current vs improved systems"""
        print("⚔️  NAME MATCHING SYSTEM COMPARISON")
        print("=" * 60)

        current_results = self.test_current_system()
        improved_results = self.test_improved_system()

        print("\n📊 COMPARISON RESULTS")
        print("=" * 40)

        print(f"Current System:")
        print(
            f"  ✅ Correct: {current_results['correct']}/{current_results['total']} ({current_results['correct'] / current_results['total'] * 100:.1f}%)")
        print(f"  ❌ Failed: {current_results['incorrect']}")
        print(f"  🐌 Slow matches: {len(current_results['slow_matches'])}")
        print(f"  💥 Errors: {len(current_results['errors'])}")

        print(f"\nImproved System:")
        print(
            f"  ✅ Correct: {improved_results['correct']}/{improved_results['total']} ({improved_results['correct'] / improved_results['total'] * 100:.1f}%)")
        print(f"  ❌ Failed: {improved_results['incorrect']}")
        print(f"  🐌 Slow matches: {len(improved_results['slow_matches'])}")
        print(f"  💥 Errors: {len(improved_results['errors'])}")

        # Show improvement
        improvement = improved_results['correct'] - current_results['correct']
        if improvement > 0:
            print(f"\n🚀 Improvement: +{improvement} more correct matches!")
        elif improvement < 0:
            print(f"\n⚠️  Regression: {abs(improvement)} fewer correct matches")
        else:
            print(f"\n➡️  Same accuracy")

        # Show failed cases for current system
        if current_results['failed_cases']:
            print(f"\n❌ Current System Failed Cases:")
            for name1, name2, expected, actual in current_results['failed_cases'][:5]:
                print(f"   {name1} vs {name2}: got {actual}, expected {expected}")

        # Show failed cases for improved system
        if improved_results['failed_cases']:
            print(f"\n❌ Improved System Failed Cases:")
            for name1, name2, expected, actual in improved_results['failed_cases'][:5]:
                print(f"   {name1} vs {name2}: got {actual}, expected {expected}")

        return current_results, improved_results


class ImprovedNameMatcher:
    """Improved name matching system - keeps good parts, fixes problems"""

    def __init__(self):
        # Enhanced nickname mapping
        self.nicknames = {
            'mike': ['michael'], 'chris': ['christopher'], 'alex': ['alexander'],
            'matt': ['matthew'], 'dave': ['david'], 'steve': ['steven'],
            'tom': ['thomas'], 'bob': ['robert'], 'bill': ['william'],
            'dan': ['daniel'], 'rob': ['robert'], 'jim': ['james'],
            'joe': ['joseph'], 'tony': ['anthony'], 'rick': ['richard'],
            'tim': ['timothy'], 'ben': ['benjamin'], 'sam': ['samuel'],
            'nick': ['nicholas'], 'pat': ['patrick'], 'ed': ['edward'],
            'whit': ['whitney'], 'chas': ['charles'], 'dj': ['david'],
            'tj': ['thomas'], 'aj': ['anthony', 'andrew'], 'jd': ['john', 'james'],
            'xander': ['alexander']
        }

        # Build reverse mapping
        self.nickname_reverse = {}
        for nick, fulls in self.nicknames.items():
            for full in fulls:
                if full not in self.nickname_reverse:
                    self.nickname_reverse[full] = []
                self.nickname_reverse[full].append(nick)

        # Cache for performance
        self._cache = {}

    def match_names(self, name1: str, name2: str) -> bool:
        """Improved name matching with better logic"""
        if not name1 or not name2:
            return False

        # Check cache
        cache_key = f"{name1.lower()}|{name2.lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Normalize names
        norm1 = self._normalize_name(name1)
        norm2 = self._normalize_name(name2)

        result = self._match_normalized_names(norm1, norm2)

        # Cache result
        self._cache[cache_key] = result
        return result

    def _normalize_name(self, name: str) -> str:
        """Clean and normalize name"""
        import re
        import unicodedata

        name = str(name).lower().strip()

        # Remove accents
        name = unicodedata.normalize('NFD', name)
        name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')

        # Remove Jr/Sr/II/III
        name = re.sub(r'\b(jr\.?|sr\.?|ii+|iii+|iv|v)\b', '', name)

        # Remove punctuation but keep spaces and hyphens
        name = re.sub(r'[^\w\s\-]', ' ', name)

        # Clean up spaces
        name = ' '.join(name.split())

        return name

    def _match_normalized_names(self, name1: str, name2: str) -> bool:
        """Match two normalized names"""
        # Exact match
        if name1 == name2:
            return True

        # Split into parts
        parts1 = name1.split()
        parts2 = name2.split()

        # Need at least one part each
        if not parts1 or not parts2:
            return False

        # If one name is much longer, check if shorter is contained
        if len(parts1) != len(parts2):
            shorter = parts1 if len(parts1) < len(parts2) else parts2
            longer = parts2 if len(parts1) < len(parts2) else parts1

            # Check if all parts of shorter name appear in longer name
            matches = 0
            for short_part in shorter:
                for long_part in longer:
                    if self._match_name_parts(short_part, long_part):
                        matches += 1
                        break

            # At least 80% of shorter name parts should match
            if len(shorter) > 0 and matches / len(shorter) >= 0.8:
                return True

        # Same number of parts - check each position
        if len(parts1) == len(parts2):
            matches = 0
            for p1, p2 in zip(parts1, parts2):
                if self._match_name_parts(p1, p2):
                    matches += 1

            # At least 80% of parts should match
            if len(parts1) > 0 and matches / len(parts1) >= 0.8:
                return True

        return False

    def _match_name_parts(self, part1: str, part2: str) -> bool:
        """Match individual name parts"""
        # Exact match
        if part1 == part2:
            return True

        # One contains the other
        if part1 in part2 or part2 in part1:
            return True

        # Check nicknames
        if part1 in self.nicknames and part2 in self.nicknames.get(part1, []):
            return True
        if part2 in self.nicknames and part1 in self.nicknames.get(part2, []):
            return True

        # Check reverse nicknames
        if part1 in self.nickname_reverse and part2 in self.nickname_reverse.get(part1, []):
            return True
        if part2 in self.nickname_reverse and part1 in self.nickname_reverse.get(part2, []):
            return True

        # Initial matching (for very short names)
        if len(part1) == 1 or len(part2) == 1:
            return part1[0] == part2[0]

        # Similar length and high similarity
        if abs(len(part1) - len(part2)) <= 2:
            # Simple character overlap check
            common_chars = set(part1) & set(part2)
            min_len = min(len(part1), len(part2))
            if min_len > 0 and len(common_chars) / min_len >= 0.8:
                return True

        return False


def main():
    """Run the name matching comparison"""
    tester = NameMatchingTester()
    current_results, improved_results = tester.compare_systems()

    print("\n🎯 RECOMMENDATION:")
    if improved_results['correct'] > current_results['correct']:
        print("✅ The improved system is better - recommend switching!")
    elif improved_results['correct'] == current_results['correct']:
        if len(improved_results['slow_matches']) < len(current_results['slow_matches']):
            print("⚡ Same accuracy but faster - recommend switching!")
        else:
            print("➡️  Both systems perform similarly")
    else:
        print("⚠️  Current system is still better - keep using it")

    print(f"\nTo use the improved system:")
    print(f"1. Replace UnifiedDataSystem.match_player_names() method")
    print(f"2. Or use ImprovedNameMatcher as a drop-in replacement")


if __name__ == "__main__":
    main()