#!/usr/bin/env python3
"""
FIX GUI NOW - Make Game Info Work
=================================
Direct fix for the GUI to pass game_info
"""

import os
import shutil
from datetime import datetime


def fix_optimization_worker():
    """Fix the OptimizationWorker in complete_dfs_gui_debug.py"""
    print("\n🔧 FIXING OPTIMIZATION WORKER IN GUI")
    print("=" * 60)

    gui_file = 'complete_dfs_gui_debug.py'

    if not os.path.exists(gui_file):
        print(f"❌ {gui_file} not found!")
        return False

    # Backup
    backup = f"{gui_file}.backup_gameinfo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(gui_file, backup)
    print(f"✅ Created backup: {backup}")

    # Read file
    with open(gui_file, 'r') as f:
        lines = f.readlines()

    # Find where UnifiedPlayer is created
    modified = False
    for i in range(len(lines)):
        # Look for where player is created
        if 'player = UnifiedPlayer(' in lines[i]:
            # Find the closing parenthesis
            j = i
            while j < len(lines) and ')' not in lines[j]:
                j += 1

            # Now find where additional attributes are set
            k = j + 1
            while k < len(lines) and 'players.append(player)' not in lines[k]:
                # Check if we're setting display_position
                if 'player.display_position' in lines[k]:
                    # Insert game_info before display_position
                    indent = '                '  # Match the indentation
                    new_lines = [
                        f"{indent}# Store additional data INCLUDING GAME INFO!\n",
                        f"{indent}player.opponent = row.get('Opponent', 'UNK')\n",
                        f"{indent}player.game_info = row.get('Game Info', '')  # CRITICAL FOR SLATE DETECTION!\n"
                    ]

                    # Insert before display_position line
                    lines[k:k] = new_lines
                    modified = True
                    print("✅ Added game_info assignment to OptimizationWorker")
                    break
                k += 1

            if modified:
                break

    if not modified:
        print("⚠️  Could not find exact location, trying alternative approach...")

        # Alternative: Find any mention of display_position and add game_info before it
        for i in range(len(lines)):
            if 'player.display_position = ' in lines[i] and 'player.game_info' not in ''.join(
                    lines[max(0, i - 5):i + 5]):
                indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
                new_lines = [
                    f"{indent}player.opponent = row.get('Opponent', 'UNK')\n",
                    f"{indent}player.game_info = row.get('Game Info', '')  # CRITICAL!\n"
                ]
                lines[i:i] = new_lines
                modified = True
                print("✅ Added game_info assignment (alternative method)")
                break

    if modified:
        # Write back
        with open(gui_file, 'w') as f:
            f.writelines(lines)
        print("✅ GUI fixed!")
        return True
    else:
        print("❌ Could not automatically fix - manual fix needed")
        return False


def show_manual_fix():
    """Show manual fix instructions"""
    print("\n📝 MANUAL FIX INSTRUCTIONS")
    print("=" * 60)

    print("\nIn complete_dfs_gui_debug.py, find where UnifiedPlayer is created")
    print("in the OptimizationWorker class.")

    print("\nLook for this section:")
    print("""
    player = UnifiedPlayer(
        id=str(row.get('ID', f"{row['Name']}_{idx}")),
        name=row['Name'],
        team=row.get('TeamAbbrev', 'UNK'),
        salary=int(row['Salary']),
        primary_position=primary,
        positions=positions,
        base_projection=float(row.get('AvgPointsPerGame', 0))
    )

    player.display_position = pos_str
""")

    print("\nChange it to:")
    print("""
    player = UnifiedPlayer(
        id=str(row.get('ID', f"{row['Name']}_{idx}")),
        name=row['Name'],
        team=row.get('TeamAbbrev', 'UNK'),
        salary=int(row['Salary']),
        primary_position=primary,
        positions=positions,
        base_projection=float(row.get('AvgPointsPerGame', 0))
    )

    # Store additional data INCLUDING GAME INFO!
    player.opponent = row.get('Opponent', 'UNK')
    player.game_info = row.get('Game Info', '')  # CRITICAL FOR SLATE DETECTION!
    player.display_position = pos_str
""")


def verify_csv_format():
    """Check CSV format to understand the issue"""
    print("\n🔍 CHECKING CSV FORMAT")
    print("=" * 60)

    import pandas as pd

    # Try to load the CSV mentioned in logs
    csv_path = "/home/michael/Downloads/DKSalaries(13).csv"

    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded CSV: {csv_path}")

        print(f"\n📊 CSV Info:")
        print(f"Rows: {len(df)}")
        print(f"Columns: {list(df.columns)}")

        # Check for Game Info
        if 'Game Info' in df.columns:
            games = df['Game Info'].dropna().unique()
            print(f"\n🎮 Found {len(games)} unique games")

            print("\nFirst 5 games:")
            for i, game in enumerate(games[:5]):
                print(f"  {i + 1}. '{game}'")

            # Check format
            if games.size > 0:
                sample = str(games[0])
                print(f"\n📝 Game format analysis:")
                print(f"Sample: '{sample}'")
                print(f"Has @: {'@' in sample}")
                print(f"Has time: {any(x in sample for x in ['AM', 'PM', 'am', 'pm'])}")
                print(f"Has ET: {'ET' in sample}")

        else:
            print("\n❌ No 'Game Info' column found!")
            print("Available columns:")
            for col in df.columns:
                if 'game' in col.lower():
                    print(f"  • {col}")

    except Exception as e:
        print(f"❌ Could not load CSV: {e}")


def create_test_script():
    """Create a test script"""
    test_code = '''#!/usr/bin/env python3
"""Test if game info is working"""

from unified_core_system import UnifiedCoreSystem

system = UnifiedCoreSystem()
system.load_csv("/home/michael/Downloads/DKSalaries(13).csv")

# Check first 5 players
print("\\nChecking if players have game_info:")
for i, (name, player) in enumerate(system.all_players.items()):
    if i < 5:
        game_info = getattr(player, 'game_info', 'MISSING')
        print(f"{name}: game_info = '{game_info}'")

# Count how many have game_info
count = sum(1 for p in system.all_players.values() if hasattr(p, 'game_info') and p.game_info)
print(f"\\nTotal with game_info: {count}/{len(system.all_players)}")
'''

    with open('test_game_info.py', 'w') as f:
        f.write(test_code)
    print("\n✅ Created test_game_info.py")


def main():
    """Main fix function"""
    print("\n🚀 FIXING GAME INFO IN GUI")
    print("=" * 70)

    # Try to fix automatically
    if fix_optimization_worker():
        print("\n✅ SUCCESS! GUI should now pass game_info")
        print("\n🎯 Next steps:")
        print("1. Close and restart your GUI")
        print("2. Load your CSV again")
        print("3. The system should now detect slate games!")
    else:
        print("\n❌ Automatic fix failed")
        show_manual_fix()

    # Check CSV format
    verify_csv_format()

    # Create test
    create_test_script()

    print("\n\n📋 TO VERIFY THE FIX:")
    print("python test_game_info.py")

    print("\n💡 EXPECTED RESULT:")
    print("• Players should have game_info values")
    print("• System should identify slate games")
    print("• No more '0 games in slate'!")


if __name__ == "__main__":
    main()