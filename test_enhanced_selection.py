#!/usr/bin/env python3
"""
Test Enhanced Selection Features
===============================
"""

def test_enhanced_features():
    """Test enhanced manual selection features"""
    print("🧪 Testing Enhanced Manual Selection Features")
    print("=" * 50)

    try:
        from enhanced_player_selector import EnhancedPlayerSelector

        # Create mock players for testing
        class MockPlayer:
            def __init__(self, name, team, position):
                self.name = name
                self.team = team
                self.primary_position = position
                self.positions = [position]
                self.enhanced_score = 10.0
                self.is_manual_selected = False

            def set_manual_selected(self):
                self.is_manual_selected = True

        mock_players = [
            MockPlayer("Kyle Tucker", "HOU", "OF"),
            MockPlayer("Vladimir Guerrero Jr.", "TOR", "1B"),
            MockPlayer("Jose Altuve", "HOU", "2B"),
            MockPlayer("Alex Bregman", "HOU", "3B"),
            MockPlayer("Jeremy Peña", "HOU", "SS"),
            MockPlayer("Hunter Brown", "HOU", "P"),
            MockPlayer("Aaron Judge", "NYY", "OF"),
            MockPlayer("Juan Soto", "NYY", "OF")
        ]

        selector = EnhancedPlayerSelector()

        # Test cases
        test_cases = [
            "vlad jr, tucker",  # Nickname test
            "all astros hitters",  # Team selection
            "add 2 OF",  # Position request
            "kyle tuck"  # Partial name
        ]

        for i, test_input in enumerate(test_cases, 1):
            print(f"\nTest {i}: '{test_input}'")
            results = selector.parse_manual_input(test_input, mock_players)

            print(f"  Individual matches: {len(results['matched_players'])}")
            print(f"  Team additions: {len(results['team_additions'])}")
            print(f"  Suggestions: {len(results['suggestions'])}")

            if results['suggestions']:
                for suggestion in results['suggestions']:
                    print(f"    💡 {suggestion['input']} → {suggestion['suggestions']}")

        print("\n✅ Enhanced selection tests completed!")
        return True

    except Exception as e:
        print(f"❌ Enhanced selection test failed: {e}")
        return False

if __name__ == "__main__":
    test_enhanced_features()
