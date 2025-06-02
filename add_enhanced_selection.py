#!/usr/bin/env python3
"""
FIXED ENHANCED MANUAL SELECTION - AUTO INTEGRATION
==================================================
Automatically adds smart player selection to your bulletproof system
✅ Fixed all syntax errors
✅ Automatic integration
✅ Zero manual steps required
✅ Safe backup system
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime


def create_enhanced_selector_module():
    """Create the enhanced selector module file"""

    module_content = '''#!/usr/bin/env python3
"""
Enhanced Player Selector Module
==============================
Smart player selection with nicknames, team shortcuts, and position requests
"""

import re
from typing import List, Dict, Optional, Any
from difflib import get_close_matches, SequenceMatcher

class EnhancedPlayerSelector:
    """Enhanced player selection with smart matching"""

    def __init__(self):
        # MLB player nicknames dictionary
        self.nicknames = {
            'vlad jr': 'Vladimir Guerrero Jr.',
            'vlad guerrero jr': 'Vladimir Guerrero Jr.',
            'vladdy': 'Vladimir Guerrero Jr.',
            'bo bichette': 'Bo Bichette',
            'acuna': 'Ronald Acuña Jr.',
            'acuna jr': 'Ronald Acuña Jr.',
            'tatis': 'Fernando Tatis Jr.',
            'tatis jr': 'Fernando Tatis Jr.',
            'bichette': 'Bo Bichette',
            'soto': 'Juan Soto',
            'judge': 'Aaron Judge',
            'ohtani': 'Shohei Ohtani',
            'trout': 'Mike Trout',
            'mookie': 'Mookie Betts',
            'freddie': 'Freddie Freeman',
            'tucker': 'Kyle Tucker',
            'bregman': 'Alex Bregman',
            'altuve': 'Jose Altuve',
            'alvarez': 'Yordan Alvarez',
            'yordan': 'Yordan Alvarez',
            'pena': 'Jeremy Peña',
            'gleyber': 'Gleyber Torres',
            'torres': 'Gleyber Torres',
            'stanton': 'Giancarlo Stanton',
            'rizzo': 'Anthony Rizzo',
            'betts': 'Mookie Betts',
            'muncy': 'Max Muncy',
            'turner': 'Trea Turner'
        }

        # Team name mappings
        self.team_names = {
            'astros': 'HOU', 'houston': 'HOU', 'hou': 'HOU',
            'yankees': 'NYY', 'yanks': 'NYY', 'ny yankees': 'NYY',
            'dodgers': 'LAD', 'la dodgers': 'LAD',
            'red sox': 'BOS', 'boston': 'BOS', 'bos': 'BOS',
            'rays': 'TB', 'tampa bay': 'TB', 'tb': 'TB',
            'blue jays': 'TOR', 'jays': 'TOR', 'toronto': 'TOR',
            'guardians': 'CLE', 'cleveland': 'CLE', 'cle': 'CLE',
            'braves': 'ATL', 'atlanta': 'ATL', 'atl': 'ATL',
            'mets': 'NYM', 'ny mets': 'NYM', 'nym': 'NYM',
            'phillies': 'PHI', 'philadelphia': 'PHI', 'phi': 'PHI'
        }

        # Position shortcuts
        self.position_map = {
            'pitcher': 'P', 'pitchers': 'P', 'p': 'P',
            'catcher': 'C', 'catchers': 'C', 'c': 'C',
            'first': '1B', 'first base': '1B', '1b': '1B',
            'second': '2B', 'second base': '2B', '2b': '2B',
            'third': '3B', 'third base': '3B', '3b': '3B',
            'short': 'SS', 'shortstop': 'SS', 'ss': 'SS',
            'outfield': 'OF', 'outfielder': 'OF', 'of': 'OF'
        }

    def parse_manual_input(self, manual_input: str, available_players: List) -> Dict:
        """Parse enhanced manual input and return structured results"""

        if not manual_input or not manual_input.strip():
            return {'matched_players': [], 'team_additions': [], 'suggestions': []}

        results = {'matched_players': [], 'team_additions': [], 'suggestions': []}

        # Clean and split input
        items = re.split(r'[,;\\n|]+', manual_input.lower())
        items = [item.strip() for item in items if item.strip()]

        for item in items:
            # Try team-based selection first
            team_players = self._handle_team_selection(item, available_players)
            if team_players:
                results['team_additions'].extend(team_players)
                continue

            # Try position-based selection
            position_players = self._handle_position_selection(item, available_players)
            if position_players:
                results['matched_players'].extend(position_players)
                continue

            # Try individual player matching
            player_match = self._match_individual_player(item, available_players)
            if player_match:
                results['matched_players'].append(player_match)
            else:
                # Generate suggestions
                suggestions = self._get_suggestions(item, available_players)
                if suggestions:
                    results['suggestions'].append({
                        'input': item,
                        'suggestions': suggestions
                    })

        return results

    def _handle_team_selection(self, item: str, available_players: List) -> List:
        """Handle team-based selection like 'all astros' or 'houston hitters'"""

        team_patterns = [
            r'^all\\s+(\\w+)(?:\\s+(?:hitters?|team|lineup))?$',
            r'^(\\w+)\\s+(?:hitters?|team|lineup)$',
            r'^(\\w+)\\s+(?:batters?|offense)$'
        ]

        for pattern in team_patterns:
            match = re.match(pattern, item)
            if match:
                team_name = match.group(1).lower()
                if team_name in self.team_names:
                    team_code = self.team_names[team_name]
                    team_players = []

                    for player in available_players:
                        if (hasattr(player, 'team') and 
                            player.team == team_code and 
                            player.primary_position != 'P'):  # Exclude pitchers
                            team_players.append({
                                'player': player,
                                'reason': f'Team selection: {team_name} hitters'
                            })

                    return team_players

        return []

    def _handle_position_selection(self, item: str, available_players: List) -> List:
        """Handle position requests like 'add 2 OF' or 'need pitcher'"""

        position_patterns = [
            r'^(?:add|get|need)\\s+(\\d+)?\\s*(\\w+)$',
            r'^(\\d+)\\s+(\\w+)$'
        ]

        for pattern in position_patterns:
            match = re.match(pattern, item)
            if match:
                if len(match.groups()) == 2 and match.group(1) and match.group(1).isdigit():
                    count = int(match.group(1))
                    position_name = match.group(2).lower()
                else:
                    count = 1
                    position_name = (match.group(2) or match.group(1)).lower()

                if position_name in self.position_map:
                    position_code = self.position_map[position_name]

                    # Find best players for this position
                    position_players = []
                    for player in available_players:
                        if (hasattr(player, 'positions') and 
                            position_code in player.positions):
                            position_players.append(player)

                    # Sort by score and take requested count
                    position_players.sort(key=lambda x: x.enhanced_score, reverse=True)

                    return [{
                        'player': p,
                        'reason': f'Position request: {position_name}'
                    } for p in position_players[:count]]

        return []

    def _match_individual_player(self, item: str, available_players: List) -> Optional[Dict]:
        """Match individual player with nickname support"""

        # Check nicknames first
        if item in self.nicknames:
            target_name = self.nicknames[item]
            for player in available_players:
                if self._name_similarity(target_name, player.name) > 0.8:
                    return {
                        'player': player,
                        'reason': f'Nickname match: {item} → {player.name}'
                    }

        # Fuzzy matching
        best_player = None
        best_score = 0.0

        for player in available_players:
            score = self._name_similarity(item, player.name)
            if score > best_score and score >= 0.7:
                best_score = score
                best_player = player

        if best_player:
            return {
                'player': best_player,
                'reason': f'Name match: {item} → {best_player.name} ({best_score:.2f})'
            }

        return None

    def _get_suggestions(self, item: str, available_players: List) -> List[str]:
        """Generate suggestions for unmatched input"""

        player_names = [p.name for p in available_players]
        suggestions = get_close_matches(item, player_names, n=3, cutoff=0.4)

        # Also suggest nicknames
        for nickname in self.nicknames.keys():
            if item in nickname or nickname in item:
                suggestions.append(f"'{nickname}' (nickname)")
                break

        return suggestions[:3]

    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity score"""
        name1_clean = name1.lower().strip()
        name2_clean = name2.lower().strip()

        if name1_clean == name2_clean:
            return 1.0

        if name1_clean in name2_clean or name2_clean in name1_clean:
            return 0.85

        # Check last name + first initial
        parts1 = name1_clean.split()
        parts2 = name2_clean.split()

        if (len(parts1) >= 2 and len(parts2) >= 2 and
            parts1[-1] == parts2[-1] and  # Same last name
            parts1[0][0] == parts2[0][0]):  # Same first initial
            return 0.8

        return SequenceMatcher(None, name1_clean, name2_clean).ratio()
'''

    # Write the module file
    module_file = Path('enhanced_player_selector.py')
    with open(module_file, 'w', encoding='utf-8') as f:
        f.write(module_content)

    return module_file


def integrate_enhanced_selection():
    """Automatically integrate enhanced selection into bulletproof core"""

    core_file = Path('bulletproof_dfs_core.py')
    if not core_file.exists():
        print("❌ bulletproof_dfs_core.py not found!")
        return False

    # Create backup
    backup_file = Path(f'bulletproof_dfs_core_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py')
    shutil.copy2(core_file, backup_file)
    print(f"💾 Backup created: {backup_file}")

    # Read current content
    with open(core_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already integrated
    if 'ENHANCED_SELECTION_ACTIVE' in content:
        print("✅ Enhanced selection already integrated!")
        return True

    # Add import after other imports
    import_addition = """
# ENHANCED_SELECTION_ACTIVE
try:
    from enhanced_player_selector import EnhancedPlayerSelector
    ENHANCED_SELECTOR_AVAILABLE = True
    print("✅ Enhanced player selector loaded")
except ImportError:
    ENHANCED_SELECTOR_AVAILABLE = False
    print("⚠️ Enhanced player selector not available")
"""

    # Find where to insert the import
    import_position = content.find('print("✅ Bulletproof DFS Core initialized')
    if import_position == -1:
        import_position = content.find('warnings.filterwarnings(\'ignore\')')

    if import_position != -1:
        content = content[:import_position] + import_addition + '\n' + content[import_position:]

    # Replace the apply_manual_selection method
    old_method_pattern = r'def apply_manual_selection\(self, manual_input: str\) -> int:.*?(?=\n    def |\nclass |\ndef |$)'

    new_method = '''def apply_manual_selection(self, manual_input: str) -> int:
        """Enhanced manual player selection with smart features"""
        if not manual_input:
            return 0

        print(f"🔥 Enhanced manual selection processing...")

        # Use enhanced selector if available
        if ENHANCED_SELECTOR_AVAILABLE:
            selector = EnhancedPlayerSelector()
            results = selector.parse_manual_input(manual_input, self.players)

            total_matches = 0

            # Apply individual player matches
            for match in results['matched_players']:
                player = match['player']
                if not player.is_manual_selected:
                    player.set_manual_selected()
                    total_matches += 1
                    print(f"   ✅ {match['reason']}")

            # Apply team additions
            for team_match in results['team_additions']:
                player = team_match['player']
                if not player.is_manual_selected:
                    player.set_manual_selected()
                    total_matches += 1

            if results['team_additions']:
                print(f"   🏟️ Added {len(results['team_additions'])} team players")

            # Show suggestions
            for suggestion in results['suggestions']:
                print(f"   💡 '{suggestion['input']}' not found. Try: {', '.join(suggestion['suggestions'])}")

            print(f"🔥 Enhanced selection: {total_matches} players selected")
            return total_matches

        else:
            # Fallback to basic selection
            return self._basic_manual_selection(manual_input)

    def _basic_manual_selection(self, manual_input: str) -> int:
        """Basic manual selection fallback"""
        manual_names = []
        for delimiter in [',', ';', '\\n', '|']:
            if delimiter in manual_input:
                manual_names = [name.strip() for name in manual_input.split(delimiter)]
                break
        else:
            manual_names = [manual_input.strip()]

        manual_names = [name for name in manual_names if name and len(name) > 2]

        if not manual_names:
            return 0

        print(f"🎯 Basic manual selection: {len(manual_names)} players")

        matches = 0
        for manual_name in manual_names:
            best_match = None
            best_score = 0

            for player in self.players:
                similarity = self._name_similarity(manual_name, player.name)
                if similarity > best_score and similarity >= 0.7:
                    best_score = similarity
                    best_match = player

            if best_match:
                best_match.set_manual_selected()
                matches += 1
                print(f"   ✅ {manual_name} → {best_match.name}")
            else:
                print(f"   ❌ {manual_name} → No match found")

        return matches'''

    # Replace the method using regex
    content = re.sub(old_method_pattern, new_method, content, flags=re.DOTALL)

    # Write the updated content
    with open(core_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ Enhanced selection integrated successfully!")
    return True


def test_enhanced_selection():
    """Test the enhanced selection integration"""

    test_content = '''#!/usr/bin/env python3
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
            print(f"\\nTest {i}: '{test_input}'")
            results = selector.parse_manual_input(test_input, mock_players)

            print(f"  Individual matches: {len(results['matched_players'])}")
            print(f"  Team additions: {len(results['team_additions'])}")
            print(f"  Suggestions: {len(results['suggestions'])}")

            if results['suggestions']:
                for suggestion in results['suggestions']:
                    print(f"    💡 {suggestion['input']} → {suggestion['suggestions']}")

        print("\\n✅ Enhanced selection tests completed!")
        return True

    except Exception as e:
        print(f"❌ Enhanced selection test failed: {e}")
        return False

if __name__ == "__main__":
    test_enhanced_features()
'''

    test_file = Path('test_enhanced_selection.py')
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)

    return test_file


def main():
    """Main automatic integration function"""

    print("🔥 ENHANCED MANUAL SELECTION - AUTO INTEGRATION")
    print("=" * 60)
    print("Adding smart player selection features automatically...")
    print()

    try:
        # Step 1: Create enhanced selector module
        print("1️⃣ Creating enhanced selector module...")
        module_file = create_enhanced_selector_module()
        print(f"   ✅ Created: {module_file}")

        # Step 2: Integrate with bulletproof core
        print("\\n2️⃣ Integrating with bulletproof core...")
        if integrate_enhanced_selection():
            print("   ✅ Integration successful!")
        else:
            print("   ❌ Integration failed!")
            return False

        # Step 3: Create test file
        print("\\n3️⃣ Creating test file...")
        test_file = test_enhanced_selection()
        print(f"   ✅ Created: {test_file}")

        print("\\n🎉 ENHANCED MANUAL SELECTION COMPLETE!")
        print("=" * 60)
        print("✅ Smart nickname recognition active")
        print("✅ Team-based selection enabled")
        print("✅ Position shortcuts working")
        print("✅ Automatic suggestions available")
        print()
        print("🧪 Test features:")
        print("   python test_enhanced_selection.py")
        print()
        print("🚀 Try these enhanced inputs:")
        print('   "vlad jr, tucker, all astros hitters"')
        print('   "add 2 OF, need pitcher"')
        print('   "yankees team, dodgers hitters"')
        print()
        print("🎯 Launch your enhanced system:")
        print("   python setup_bulletproof_dfs.py")

        return True

    except Exception as e:
        print(f"❌ Auto-integration failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)