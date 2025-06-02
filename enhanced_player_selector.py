#!/usr/bin/env python3
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
        items = re.split(r'[,;\n|]+', manual_input.lower())
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
            r'^all\s+(\w+)(?:\s+(?:hitters?|team|lineup))?$',
            r'^(\w+)\s+(?:hitters?|team|lineup)$',
            r'^(\w+)\s+(?:batters?|offense)$'
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
            r'^(?:add|get|need)\s+(\d+)?\s*(\w+)$',
            r'^(\d+)\s+(\w+)$'
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
