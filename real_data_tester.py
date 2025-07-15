#!/usr/bin/env python3
"""
REAL DATA TESTING
=================
Test name matching with your actual CSV and confirmation data
"""

import pandas as pd
from unified_data_system import UnifiedDataSystem
from enhanced_name_matcher import EnhancedNameMatcher


def test_with_real_csv(csv_path: str):
    """Test name matching with your real CSV data"""

    print("🔍 TESTING WITH REAL CSV DATA")
    print("=" * 50)

    # Load your CSV
    try:
        df = pd.read_csv(csv_path)
        print(f"📄 Loaded {len(df)} players from {csv_path}")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return

    # Get player names from CSV
    name_column = None
    for col in df.columns:
        if 'name' in col.lower():
            name_column = col
            break

    if not name_column:
        print("❌ Could not find name column in CSV")
        return

    player_names = df[name_column].tolist()
    print(f"📊 Found {len(player_names)} player names")

    # Initialize both systems
    current_system = UnifiedDataSystem()
    enhanced_system = EnhancedNameMatcher()

    # Test common name variations that cause problems
    test_variations = []
    for name in player_names[:20]:  # Test first 20 players
        if ' ' in name:
            parts = name.split()
            if len(parts) >= 2:
                # Create test variations
                first, last = parts[0], parts[-1]

                # Add common variations
                test_variations.append((name, f"{first} {last}", True))  # Original

                # Nickname variations
                nicknames = {
                    'Michael': 'Mike', 'Christopher': 'Chris', 'Alexander': 'Alex',
                    'Matthew': 'Matt', 'David': 'Dave', 'Steven': 'Steve'
                }
                for full, nick in nicknames.items():
                    if first == full:
                        test_variations.append((name, f"{nick} {last}", True))
                    elif first == nick:
                        test_variations.append((name, f"{full} {last}", True))

                # Jr./Sr. variations
                if 'Jr.' not in name:
                    test_variations.append((name, f"{name} Jr.", True))

                # Punctuation variations
                if '.' not in name:
                    if len(first) <= 3:  # Likely initial
                        test_variations.append((name, f"{first}. {last}", True))

    if not test_variations:
        print("⚠️ Could not create test variations from CSV data")
        return

    print(f"🧪 Testing {len(test_variations)} name variations...")

    # Test both systems
    current_correct = 0
    enhanced_correct = 0

    for original, variation, expected in test_variations:
        try:
            current_result = current_system.match_player_names(original, variation)
            enhanced_result = enhanced_system.match_player_names(original, variation)

            if current_result == expected:
                current_correct += 1
            if enhanced_result == expected:
                enhanced_correct += 1

            if current_result != enhanced_result:
                status_curr = "✅" if current_result == expected else "❌"
                status_enh = "✅" if enhanced_result == expected else "❌"
                print(f"  DIFF: {original} vs {variation}")
                print(f"    Current: {current_result} {status_curr}")
                print(f"    Enhanced: {enhanced_result} {status_enh}")

        except Exception as e:
            print(f"  ERROR testing {original} vs {variation}: {e}")

    # Results
    print(f"\n📊 REAL DATA TEST RESULTS:")
    print(
        f"Current System:  {current_correct}/{len(test_variations)} ({current_correct / len(test_variations) * 100:.1f}%)")
    print(
        f"Enhanced System: {enhanced_correct}/{len(test_variations)} ({enhanced_correct / len(test_variations) * 100:.1f}%)")

    improvement = enhanced_correct - current_correct
    if improvement > 0:
        print(f"🚀 Enhanced system is {improvement} matches better!")
        return True
    elif improvement == 0:
        print("➡️ Both systems perform the same on your data")
        return None
    else:
        print(f"⚠️ Current system is {abs(improvement)} matches better")
        return False


def test_confirmation_matching():
    """Test how well systems match your CSV names to MLB API names"""
    print("\n🔍 TESTING CONFIRMATION MATCHING")
    print("=" * 40)

    # Simulate some common CSV vs MLB API name differences
    csv_to_mlb_cases = [
        # Format: (CSV_name, MLB_API_name, should_match)
        ("Mike Trout", "Michael Nelson Trout", True),
        ("J.D. Martinez", "Julio Daniel Martinez", True),
        ("Mookie Betts", "Markus Lynn Betts", True),
        ("Xander Bogaerts", "Alexander Bogaerts", True),
        ("Whit Merrifield", "Whitney Merrifield", True),
        ("Chas McCormick", "Charles McCormick", True),
        ("Vladimir Guerrero Jr.", "Vladimir Guerrero", True),
        ("Luis Robert Jr.", "Luis Robert", True),
    ]

    current_system = UnifiedDataSystem()
    enhanced_system = EnhancedNameMatcher()

    current_correct = 0
    enhanced_correct = 0

    print("Testing CSV names vs MLB API names:")
    for csv_name, mlb_name, expected in csv_to_mlb_cases:
        current_result = current_system.match_player_names(csv_name, mlb_name)
        enhanced_result = enhanced_system.match_player_names(csv_name, mlb_name)

        if current_result == expected:
            current_correct += 1
        if enhanced_result == expected:
            enhanced_correct += 1

        curr_status = "✅" if current_result == expected else "❌"
        enh_status = "✅" if enhanced_result == expected else "❌"

        print(f"  {csv_name} → {mlb_name}")
        print(f"    Current: {current_result} {curr_status}")
        print(f"    Enhanced: {enhanced_result} {enh_status}")

    print(f"\n📊 CONFIRMATION MATCHING RESULTS:")
    print(
        f"Current System:  {current_correct}/{len(csv_to_mlb_cases)} ({current_correct / len(csv_to_mlb_cases) * 100:.1f}%)")
    print(
        f"Enhanced System: {enhanced_correct}/{len(csv_to_mlb_cases)} ({enhanced_correct / len(csv_to_mlb_cases) * 100:.1f}%)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        result = test_with_real_csv(csv_path)
        test_confirmation_matching()

        if result is True:
            print(f"\n🎯 RECOMMENDATION: Enhanced system performs better!")
            print(f"To use it:")
            print(f"1. Backup your current unified_data_system.py")
            print(f"2. Replace the match_player_names method with enhanced version")
            print(f"3. Test with real confirmations")
        elif result is False:
            print(f"\n🎯 RECOMMENDATION: Keep your current system")
        else:
            print(f"\n🎯 RECOMMENDATION: Both systems are equivalent")
    else:
        print("Usage: python real_data_tester.py your_file.csv")