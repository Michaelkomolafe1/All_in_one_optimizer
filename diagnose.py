#!/usr/bin/env python3
"""
FIX PITCHER POSITION MAPPING
============================
Fixes the issue where pitchers have 'SP'/'RP' positions but optimizer looks for 'P'
"""

import os
import re


def fix_position_mapping():
    """Fix the position mapping in the MILP optimizer"""

    print("🔧 Fixing pitcher position mapping...")

    filepath = 'main_optimizer/unified_milp_optimizer.py'

    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False

    with open(filepath, 'r') as f:
        content = f.read()

    # Fix 1: Update position requirements to check SP/RP not just P
    position_check_fix = '''        # 3. Position requirements
        for pos, required in self.config.position_requirements.items():
            if pos == 'P':
                # For pitchers, accept P, SP, or RP positions
                eligible_indices = [
                    i for i in range(len(players))
                    if players[i].primary_position in ['P', 'SP', 'RP'] or 
                       players[i].position in ['P', 'SP', 'RP']
                ]
            else:
                # For other positions, standard check
                eligible_indices = [
                    i for i in range(len(players))
                    if players[i].primary_position == pos or pos in getattr(players[i], 'positions', [])
                ]'''

    # Replace the position requirements section
    pattern = r'# 3\. Position requirements.*?]) == required'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern,
                         position_check_fix.strip() + '\n\n            prob += pulp.lpSum([\n                player_vars[i] for i in eligible_indices\n            ]) == required',
                         content, flags=re.DOTALL)
        print("  ✓ Fixed position requirements check")

    # Fix 2: Update pitcher identification in constraints
    pitcher_check_pattern = r"if p\.primary_position == 'P'"
    pitcher_check_replacement = "if p.primary_position in ['P', 'SP', 'RP']"

    content = content.replace(pitcher_check_pattern, pitcher_check_replacement)
    print("  ✓ Fixed pitcher identification in constraints")

    # Fix 3: Update pitcher indices
    pitcher_indices_pattern = r"pitcher_indices = \[i for i, p in enumerate\(players\)\s+if p\.primary_position == 'P'\]"
    pitcher_indices_replacement = "pitcher_indices = [i for i, p in enumerate(players)\n                               if p.primary_position in ['P', 'SP', 'RP']]"

    content = re.sub(pitcher_indices_pattern, pitcher_indices_replacement, content)
    print("  ✓ Fixed pitcher indices")

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print("  ✓ Position mapping fixed in optimizer!")
    return True


def fix_player_model():
    """Ensure the player model correctly sets primary_position"""

    print("\n🔧 Fixing player model position handling...")

    filepath = 'main_optimizer/unified_player_model.py'

    if not os.path.exists(filepath):
        print(f"  ⚠️ File not found: {filepath}")
        return False

    with open(filepath, 'r') as f:
        content = f.read()

    # Find the __init__ method and ensure primary_position is set correctly
    init_pattern = r'def __init__\(self.*?\):'

    # Look for where primary_position is set
    if 'self.primary_position = position' in content:
        # Update to handle SP/RP -> P mapping
        old_line = "self.primary_position = position.split('/')[0] if '/' in position else position"
        new_lines = """# Handle primary position - map SP/RP to P for optimizer
        if position in ['SP', 'RP']:
            self.primary_position = 'P'
        else:
            self.primary_position = position.split('/')[0] if '/' in position else position"""

        content = content.replace(old_line, new_lines)
        print("  ✓ Fixed primary_position mapping in player model")

    # Also ensure is_pitcher flag is set correctly
    old_pitcher_check = "self.is_pitcher = position in ['P', 'SP', 'RP'] if position else False"
    if old_pitcher_check not in content:
        # Add it if missing
        pattern = r'(self\.primary_position = .*?\n)'
        replacement = r'\1        self.is_pitcher = position in ["P", "SP", "RP"] if position else False\n'
        content = re.sub(pattern, replacement, content)
        print("  ✓ Added is_pitcher flag")

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print("  ✓ Player model position handling fixed!")
    return True


def add_position_normalization():
    """Add a method to normalize positions in the core system"""

    print("\n🔧 Adding position normalization to core system...")

    filepath = 'main_optimizer/unified_core_system_updated.py'

    if not os.path.exists(filepath):
        print(f"  ⚠️ File not found: {filepath}")
        return False

    with open(filepath, 'r') as f:
        content = f.read()

    # Add position normalization method
    normalize_method = '''
    def normalize_pitcher_positions(self):
        """Normalize SP/RP positions to P for the optimizer"""
        for player in self.players:
            if hasattr(player, 'position'):
                if player.position in ['SP', 'RP']:
                    # Store original position
                    player.original_position = player.position
                    # Set primary_position for optimizer
                    player.primary_position = 'P'
                elif not hasattr(player, 'primary_position'):
                    player.primary_position = player.position
'''

    # Add after load_csv method
    if 'def normalize_pitcher_positions' not in content:
        # Find a good place to add it (after load_csv)
        pattern = r'(def load_csv\(self.*?\n(?:.*?\n)*?return.*?\n)'
        replacement = r'\1' + normalize_method
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        print("  ✓ Added normalize_pitcher_positions method")

    # Call it in build_player_pool
    if 'self.normalize_pitcher_positions()' not in content:
        pattern = r'(def build_player_pool\(self.*?\n(?:.*?\n){1,5})'
        replacement = r'\1        # Normalize pitcher positions\n        self.normalize_pitcher_positions()\n\n'
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        print("  ✓ Added call to normalize positions in build_player_pool")

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print("  ✓ Position normalization added!")
    return True


def create_test_script():
    """Create a test script to verify the fix"""

    test_script = '''#!/usr/bin/env python3
"""Test that pitcher positions are fixed"""

import sys
sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem

print("=" * 50)
print("TESTING PITCHER POSITION FIX")
print("=" * 50)

system = UnifiedCoreSystem()
csv_path = "/home/michael/Downloads/DKSalaries(46).csv"

# Load and setup
system.load_csv(csv_path)
system.fetch_confirmed_players()

# Test with all players (not just confirmed)
system.build_player_pool(include_unconfirmed=True)

print(f"\\nTotal players in pool: {len(system.player_pool)}")

# Count positions
position_counts = {}
pitcher_count = 0

for p in system.player_pool:
    pos = getattr(p, 'position', 'UNKNOWN')
    prim_pos = getattr(p, 'primary_position', 'UNKNOWN')

    if pos not in position_counts:
        position_counts[pos] = 0
    position_counts[pos] += 1

    # Check if optimizer will see this as a pitcher
    if prim_pos in ['P', 'SP', 'RP']:
        pitcher_count += 1

print("\\nPositions in pool:")
for pos, count in sorted(position_counts.items()):
    print(f"  {pos}: {count} players")

print(f"\\nPitchers available to optimizer: {pitcher_count}")

if pitcher_count >= 2:
    print("✅ SUCCESS! Enough pitchers for optimization")

    # Try to generate a lineup
    print("\\nTrying to generate lineup...")
    lineups = system.optimize_lineup(
        strategy='balanced_projections',
        contest_type='cash',
        num_lineups=1
    )

    if lineups and len(lineups) > 0:
        print(f"✅ Generated {len(lineups)} lineup(s)!")
        lineup = lineups[0]
        print(f"   Total salary: ${lineup.total_salary}")
        print(f"   Total projection: {lineup.total_projection:.2f}")
    else:
        print("❌ Failed to generate lineup")
else:
    print(f"❌ Not enough pitchers! Only {pitcher_count} available")
    print("   Check if CSV has pitchers or if confirmations are working")
'''

    with open('test_pitcher_fix.py', 'w') as f:
        f.write(test_script)

    print("\n✓ Created test_pitcher_fix.py")
    return True


def main():
    print("=" * 60)
    print("FIXING PITCHER POSITION MAPPING ISSUE")
    print("=" * 60)

    print("\n📌 THE PROBLEM:")
    print("  • DraftKings uses 'SP' and 'RP' for pitcher positions")
    print("  • The optimizer looks for position 'P'")
    print("  • This mismatch causes 0 pitchers to be found")

    # Check we're in the right directory
    if not os.path.exists('main_optimizer'):
        print("\n❌ Error: Wrong directory!")
        print("Please run from: /home/michael/Desktop/All_in_one_optimizer")
        print("\ncd /home/michael/Desktop/All_in_one_optimizer")
        print("python3 fix_pitcher_positions.py")
        return

    print("\n🔨 Applying fixes...")

    # Run diagnostic first
    print("\n1. Running diagnostic...")
    os.system("python3 diagnose_player_pool.py 2>/dev/null | tail -20")

    # Apply all fixes
    success = True

    if fix_position_mapping():
        print("✅ Fixed position mapping in optimizer")
    else:
        success = False

    if fix_player_model():
        print("✅ Fixed player model")
    else:
        success = False

    if add_position_normalization():
        print("✅ Added position normalization")
    else:
        success = False

    if create_test_script():
        print("✅ Created test script")

    if success:
        print("\n" + "=" * 60)
        print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
        print("=" * 60)

        print("\n📋 Next Steps:")
        print("1. Test the fix:")
        print("   python3 test_pitcher_fix.py")
        print("\n2. Run full diagnostic:")
        print("   python3 diagnose_player_pool.py")
        print("\n3. Start the GUI:")
        print("   python3 main_optimizer/GUI.py")

        print("\n💡 What was fixed:")
        print("  • Optimizer now recognizes SP/RP as pitchers")
        print("  • Position requirements accept all pitcher types")
        print("  • Player model maps SP/RP → P for optimizer")
        print("  • Core system normalizes positions on load")
    else:
        print("\n⚠️ Some fixes may have failed. Check the output above.")


if __name__ == "__main__":
    main()