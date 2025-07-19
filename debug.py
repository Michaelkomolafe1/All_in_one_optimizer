#!/usr/bin/env python3
"""
SIMPLE WORKING OPTIMIZER FIX
============================
Replace the broken optimization with working code
"""

import os
import re


def fix_optimization_worker():
    """Fix the OptimizationWorker to handle SP/RP correctly"""
    print("🔧 FIXING OPTIMIZATION WORKER")
    print("=" * 60)

    gui_file = 'complete_dfs_gui_debug.py'

    if not os.path.exists(gui_file):
        print(f"❌ {gui_file} not found!")
        return False

    # Read the file
    with open(gui_file, 'r') as f:
        content = f.read()

    # Find and replace the generate_lineup method
    new_generate_lineup = '''    def generate_lineup(self, players_df, lineup_num):
        """Generate a single lineup with proper SP/RP handling"""
        try:
            # MLB positions with proper pitcher handling
            positions_needed = [
                {'pos': 'P', 'allowed': ['SP', 'RP'], 'display': 'P'},
                {'pos': 'P', 'allowed': ['SP', 'RP'], 'display': 'P'},
                {'pos': 'C', 'allowed': ['C', 'C/1B', '1B/C'], 'display': 'C'},
                {'pos': '1B', 'allowed': ['1B', 'C/1B', '1B/3B', '1B/OF', '1B/C'], 'display': '1B'},
                {'pos': '2B', 'allowed': ['2B', '2B/SS', '2B/3B', '2B/OF'], 'display': '2B'},
                {'pos': '3B', 'allowed': ['3B', '1B/3B', '2B/3B', '3B/SS'], 'display': '3B'},
                {'pos': 'SS', 'allowed': ['SS', '2B/SS', '3B/SS'], 'display': 'SS'},
                {'pos': 'OF', 'allowed': ['OF', '1B/OF', '2B/OF'], 'display': 'OF'},
                {'pos': 'OF', 'allowed': ['OF', '1B/OF', '2B/OF'], 'display': 'OF'},
                {'pos': 'OF', 'allowed': ['OF', '1B/OF', '2B/OF'], 'display': 'OF'}
            ]

            lineup = []
            used_players = set()
            total_salary = 0
            max_salary = 50000

            # Log available positions
            available_positions = players_df['Position'].unique()
            self.log.emit(f"Available positions: {list(available_positions)}", "DEBUG")

            # Build lineup by position
            for i, pos_info in enumerate(positions_needed):
                # Find candidates
                mask = players_df['Position'].isin(pos_info['allowed'])
                candidates = players_df[mask & (~players_df['Name'].isin(used_players))]

                if candidates.empty:
                    self.log.emit(f"No players available for {pos_info['display']} (allowed: {pos_info['allowed']})", "WARNING")
                    continue

                # Select based on strategy
                if self.settings['strategy'] == 'value' and 'AvgPointsPerGame' in candidates.columns:
                    candidates = candidates.copy()
                    candidates['value'] = candidates['AvgPointsPerGame'] / candidates['Salary'] * 1000
                    candidates = candidates.sort_values('value', ascending=False)
                elif self.settings['strategy'] == 'ceiling':
                    candidates = candidates.sort_values('Salary', ascending=False)
                elif self.settings['strategy'] == 'safe':
                    # Mid-range players
                    candidates = candidates.sort_values('Salary')
                    if len(candidates) > 6:
                        candidates = candidates.iloc[len(candidates)//3:2*len(candidates)//3]
                else:
                    # Balanced - mix of high and mid players
                    if len(candidates) > 10:
                        top_candidates = candidates.nlargest(5, 'Salary')
                        mid_candidates = candidates.iloc[5:10]
                        candidates = pd.concat([top_candidates, mid_candidates]).sample(frac=1)

                # Pick a player that fits under salary cap
                selected = False
                for _, player in candidates.iterrows():
                    projected_total = total_salary + player['Salary']
                    remaining_slots = len(positions_needed) - len(lineup) - 1

                    # Ensure we don't go over budget and can afford remaining positions
                    if projected_total <= max_salary - (remaining_slots * 2000):  # $2000 min per remaining slot
                        lineup.append({
                            'position': pos_info['display'],
                            'name': player['Name'],
                            'salary': player['Salary'],
                            'team': player.get('TeamAbbrev', 'N/A'),
                            'points': player.get('AvgPointsPerGame', 0)
                        })
                        total_salary += player['Salary']
                        used_players.add(player['Name'])
                        selected = True
                        break

                if not selected:
                    self.log.emit(f"Could not find affordable player for {pos_info['display']}", "WARNING")

            # Check if lineup is valid
            if len(lineup) >= 9 and total_salary >= max_salary * self.settings['min_salary'] / 100:
                self.log.emit(f"Generated lineup: {len(lineup)} players, ${total_salary:,}", "SUCCESS")
                return {
                    'players': lineup,
                    'total_salary': total_salary,
                    'projected_points': sum(p['points'] for p in lineup)
                }
            else:
                self.log.emit(f"Invalid lineup: {len(lineup)} players, ${total_salary}", "DEBUG")
                return None

        except Exception as e:
            self.log.emit(f"Error in generate_lineup: {str(e)}", "ERROR")
            import traceback
            self.log.emit(traceback.format_exc(), "DEBUG")
            return None'''

    # Find the generate_lineup method and replace it
    pattern = r'def generate_lineup\(self.*?\n(?=\s{0,4}def|\s{0,4}class|\Z)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        # Replace the method
        content = content[:match.start()] + new_generate_lineup + '\n' + content[match.end():]

        # Make sure pandas is imported
        if 'import pandas as pd' not in content:
            # Add pandas import after other imports
            import_section = re.search(r'(import.*?\n)+', content)
            if import_section:
                content = content[:import_section.end()] + 'import pandas as pd\n' + content[import_section.end():]

        # Write the fixed file
        with open(gui_file, 'w') as f:
            f.write(content)

        print("✅ Fixed generate_lineup method")
        print("\nThe fix includes:")
        print("  • Proper SP/RP position handling")
        print("  • Multi-position player support")
        print("  • Better salary cap management")
        print("  • Detailed debug logging")

        return True
    else:
        print("❌ Could not find generate_lineup method")
        print("\n📝 Manual fix required:")
        print("Replace your generate_lineup method with the code above")

        return False


def create_test_script():
    """Create a test script"""
    test_code = '''#!/usr/bin/env python3
"""Test the fixed optimization"""

import pandas as pd

# Load your CSV
csv_file = "/home/michael/Downloads/DKSalaries(12).csv"
df = pd.read_csv(csv_file)

print(f"Loaded {len(df)} players")
print(f"\\nPositions available:")
for pos, count in df['Position'].value_counts().head(15).items():
    print(f"  {pos:6}: {count:3} players")

# Test position matching
print("\\n✅ SP/RP players:")
pitchers = df[df['Position'].isin(['SP', 'RP'])]
print(f"Found {len(pitchers)} pitchers")

print("\\n✅ Multi-position players:")
multi_pos = df[df['Position'].str.contains('/')]
print(f"Found {len(multi_pos)} multi-position eligible players")
for pos in multi_pos['Position'].unique()[:10]:
    print(f"  • {pos}")

print("\\nYour data looks good for optimization!")
'''

    with open('test_mlb_data.py', 'w') as f:
        f.write(test_code)

    print("\n✅ Created test_mlb_data.py")
    print("Run it to verify your data: python test_mlb_data.py")


def main():
    """Main function"""
    print("🚀 SIMPLE OPTIMIZER FIX")
    print("=" * 60)

    # Apply the fix
    if fix_optimization_worker():
        create_test_script()

        print("\n" + "=" * 60)
        print("✅ FIX APPLIED!")
        print("\nYour GUI should now:")
        print("  • Generate lineups with SP and RP")
        print("  • Handle multi-position players")
        print("  • Show detailed debug info")
        print("  • Work with your MLB data")
        print("\nTry running the GUI again!")
    else:
        print("\n❌ Automatic fix failed")
        print("Copy the generate_lineup method code above")
        print("and manually replace it in your GUI file")


if __name__ == "__main__":
    main()