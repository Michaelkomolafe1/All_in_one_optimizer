#!/usr/bin/env python3
"""
UNIVERSAL CSV PARSER
===================
Automatically detects and parses any DraftKings CSV format
"""

import pandas as pd
import re
from typing import Dict, List, Optional, Tuple

class UniversalCSVParser:
    """Universal parser for any DraftKings CSV format"""

    def __init__(self):
        # Common column name patterns
        self.column_patterns = {
            'name': ['name', 'player', 'full_name', 'player_name'],
            'position': ['position', 'pos', 'roster_position', 'roster position'],
            'team': ['team', 'teamabbrev', 'team_abbrev', 'tm'],
            'salary': ['salary', 'sal', 'cost', 'price'],
            'projection': ['avgpointspergame', 'fppg', 'projection', 'proj', 'points', 'pts'],
            'id': ['id', 'player_id', 'playerid']
        }

    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Automatically detect column mappings"""
        column_map = {}

        for field, patterns in self.column_patterns.items():
            for col in df.columns:
                col_lower = str(col).lower().strip()

                # Remove special characters for matching
                col_clean = re.sub(r'[^a-z0-9]', '', col_lower)

                for pattern in patterns:
                    pattern_clean = re.sub(r'[^a-z0-9]', '', pattern)

                    if pattern_clean in col_clean or col_clean in pattern_clean:
                        if field not in column_map:  # Take first match
                            column_map[field] = col
                        break

        return column_map

    def parse_positions(self, position_str: str) -> List[str]:
        """Parse position string into list of positions"""
        if not position_str or pd.isna(position_str):
            return ['UTIL']

        position_str = str(position_str).strip().upper()

        # Handle various delimiters
        delimiters = ['/', ',', '-', '|', '+', ' / ', ' , ', ' - ']
        positions = [position_str]

        for delimiter in delimiters:
            if delimiter in position_str:
                positions = [p.strip() for p in position_str.split(delimiter) if p.strip()]
                break

        # Standardize position names
        position_mapping = {
            'P': 'P', 'SP': 'P', 'RP': 'P', 'PITCHER': 'P',
            'C': 'C', 'CATCHER': 'C',
            '1B': '1B', 'FIRST': '1B', 'FIRSTBASE': '1B', '1ST': '1B',
            '2B': '2B', 'SECOND': '2B', 'SECONDBASE': '2B', '2ND': '2B',
            '3B': '3B', 'THIRD': '3B', 'THIRDBASE': '3B', '3RD': '3B',
            'SS': 'SS', 'SHORTSTOP': 'SS', 'SHORT': 'SS',
            'OF': 'OF', 'OUTFIELD': 'OF', 'OUTFIELDER': 'OF',
            'LF': 'OF', 'CF': 'OF', 'RF': 'OF', 'LEFT': 'OF', 'CENTER': 'OF', 'RIGHT': 'OF',
            'UTIL': 'UTIL', 'DH': 'UTIL', 'UTILITY': 'UTIL'
        }

        valid_positions = []
        for pos in positions:
            pos = pos.strip().upper()
            mapped_pos = position_mapping.get(pos, pos)
            if mapped_pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'UTIL']:
                if mapped_pos not in valid_positions:
                    valid_positions.append(mapped_pos)

        return valid_positions if valid_positions else ['UTIL']

    def parse_csv(self, csv_path: str) -> Tuple[List[Dict], Dict]:
        """Parse any CSV format and return standardized player data"""
        try:
            df = pd.read_csv(csv_path)

            # Detect columns
            column_map = self.detect_columns(df)

            # Validate required columns
            if 'name' not in column_map:
                raise ValueError("Could not detect player name column")

            players = []
            stats = {
                'total_players': len(df),
                'multi_position': 0,
                'single_position': 0,
                'column_map': column_map
            }

            for idx, row in df.iterrows():
                try:
                    # Extract basic data
                    name = str(row[column_map['name']]).strip()
                    if not name or name.lower() in ['nan', 'none']:
                        continue

                    # Parse positions
                    position_str = str(row[column_map.get('position', df.columns[0])]).strip()
                    positions = self.parse_positions(position_str)

                    # Track multi-position stats
                    if len(positions) > 1:
                        stats['multi_position'] += 1
                    else:
                        stats['single_position'] += 1

                    # Extract other fields with defaults
                    team = str(row[column_map.get('team', df.columns[-2])]).strip().upper()

                    # Parse salary
                    salary_raw = row[column_map.get('salary', df.columns[-3])]
                    try:
                        salary = int(float(str(salary_raw).replace('$', '').replace(',', '')))
                    except:
                        salary = 3000

                    # Parse projection
                    proj_raw = row[column_map.get('projection', df.columns[-1])]
                    try:
                        projection = float(str(proj_raw).replace(',', ''))
                    except:
                        projection = salary / 1000.0  # Default based on salary

                    player_data = {
                        'id': idx + 1,
                        'name': name,
                        'positions': positions,
                        'primary_position': positions[0],
                        'team': team,
                        'salary': salary,
                        'projection': projection,
                        'raw_position': position_str
                    }

                    players.append(player_data)

                except Exception as e:
                    print(f"⚠️ Error parsing row {idx}: {e}")
                    continue

            stats['parsed_players'] = len(players)

            return players, stats

        except Exception as e:
            raise ValueError(f"Error parsing CSV: {e}")

def test_parser(csv_path: str):
    """Test the universal parser"""
    parser = UniversalCSVParser()

    try:
        players, stats = parser.parse_csv(csv_path)

        print(f"🔍 UNIVERSAL CSV PARSER TEST")
        print(f"=" * 40)
        print(f"📁 File: {csv_path}")
        print(f"📊 Total rows: {stats['total_players']}")
        print(f"✅ Parsed players: {stats['parsed_players']}")
        print(f"🔄 Multi-position: {stats['multi_position']}")
        print(f"📍 Single-position: {stats['single_position']}")

        print(f"\n🗂️ Column mapping:")
        for field, column in stats['column_map'].items():
            print(f"   {field}: {column}")

        if players:
            print(f"\n👥 Sample players:")
            for i, player in enumerate(players[:5], 1):
                pos_str = "/".join(player['positions'])
                print(f"   {i}. {player['name']:<20} {pos_str:<8} ${player['salary']:,} {player['projection']:.1f}pts")

        return True

    except Exception as e:
        print(f"❌ Parser test failed: {e}")
        return False

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_parser(sys.argv[1])
    else:
        print("Usage: python universal_csv_parser.py <csv_file>")
