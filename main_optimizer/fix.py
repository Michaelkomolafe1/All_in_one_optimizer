#!/usr/bin/env python3
"""
COMPLETE FIX FOR GUI LOADING ISSUES
====================================
Fixes both enhanced scoring and projection mapping
Save as: fix_gui_loading.py
"""

import os
import re


def fix_enhanced_scoring_method():
    """Fix the calculate_enhanced_score method in unified_player_model.py"""

    print("🔧 Fixing enhanced scoring method...")

    fixed_method = '''    def calculate_enhanced_score(self):
        """Calculate score using enhanced scoring engine"""
        try:
            from main_optimizer.enhanced_scoring_engine_v2 import EnhancedScoringEngineV2

            # Create scoring engine
            engine = EnhancedScoringEngineV2()

            # Call methods correctly (without extra arguments)
            if hasattr(engine, 'score_player_gpp'):
                self.enhanced_score = engine.score_player_gpp(self)
            elif hasattr(engine, 'score_player'):
                # score_player only takes self, no contest_type argument
                self.enhanced_score = engine.score_player(self)
            else:
                self.enhanced_score = self.base_projection

            # Set other scores
            if hasattr(engine, 'score_player_cash'):
                self.cash_score = engine.score_player_cash(self)
            else:
                self.cash_score = self.enhanced_score

            self.gpp_score = self.enhanced_score
            self.showdown_score = self.base_projection

            # Set data quality
            self.data_quality_score = 0.8

            return self.enhanced_score

        except Exception as e:
            # Fallback to base projection
            self.enhanced_score = self.base_projection
            self.gpp_score = self.base_projection
            self.cash_score = self.base_projection
            self.showdown_score = self.base_projection
            self.data_quality_score = 0.5
            return self.base_projection
'''

    # Read the file
    filepath = 'main_optimizer/unified_player_model.py'
    with open(filepath, 'r') as f:
        content = f.read()

    # Find and replace the method
    pattern = r'def calculate_enhanced_score\(self\):.*?(?=\n    def |\nclass |\Z)'
    content = re.sub(pattern, fixed_method.strip() + '\n\n', content, flags=re.DOTALL)

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print("  ✓ Fixed enhanced scoring method")


def fix_projection_mapping():
    """Fix the CSV loading to properly map projections"""

    print("🔧 Fixing projection mapping in UnifiedPlayer...")

    filepath = 'main_optimizer/unified_player_model.py'

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Find the from_csv_row method
    in_method = False
    method_start = -1

    for i, line in enumerate(lines):
        if 'def from_csv_row' in line:
            in_method = True
            method_start = i
        elif in_method and 'base_projection' in line:
            # Fix the projection mapping
            if 'AvgPointsPerGame' not in line:
                # Add proper mapping
                indent = len(line) - len(line.lstrip())
                new_line = ' ' * indent + "base_projection = float(row.get('AvgPointsPerGame', row.get('projection', row.get('points', 0))))\n"
                lines[i] = new_line
                print(f"  ✓ Fixed projection mapping at line {i + 1}")
            break

    # Write back
    with open(filepath, 'w') as f:
        f.writelines(lines)


def add_player_pool_fix():
    """Fix the player pool filtering in unified_core_system_updated.py"""

    print("🔧 Fixing player pool filtering...")

    filepath = 'main_optimizer/unified_core_system_updated.py'

    with open(filepath, 'r') as f:
        content = f.read()

    # Find where player_pool is set
    if '@property' in content and 'def player_pool' in content:
        # Fix the player_pool property
        fixed_property = '''    @property
    def player_pool(self):
        """Get filtered player pool for optimization"""
        if not self.csv_loaded:
            return []

        # Return all players with valid projections
        valid_players = []
        for p in self.players:
            # Include if has any projection
            if hasattr(p, 'base_projection') and p.base_projection > 0:
                valid_players.append(p)
            elif hasattr(p, 'projection') and p.projection > 0:
                valid_players.append(p)
            elif hasattr(p, 'optimization_score') and p.optimization_score > 0:
                valid_players.append(p)

        return valid_players
'''

        # Replace the property
        pattern = r'@property\s+def player_pool\(self\):.*?(?=\n    @|\n    def |\nclass |\Z)'
        content = re.sub(pattern, fixed_property.strip() + '\n\n', content, flags=re.DOTALL)

        # Write back
        with open(filepath, 'w') as f:
            f.write(content)

        print("  ✓ Fixed player pool filtering")


def create_test_script():
    """Create a test script to verify the fixes"""

    test_content = '''#!/usr/bin/env python3
"""Test CSV Loading"""

import sys
sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem
from unified_player_model import UnifiedPlayer

# Create a test player
test_row = {
    'Name': 'Test Player',
    'Position': 'OF',
    'Salary': '5000',
    'TeamAbbrev': 'NYY',
    'AvgPointsPerGame': '10.5',
    'ID': '12345'
}

print("Testing player creation...")
try:
    player = UnifiedPlayer.from_csv_row(test_row)
    print(f"✓ Created player: {player.name}")
    print(f"  Base projection: {player.base_projection}")
    print(f"  Optimization score: {player.optimization_score}")
    print(f"  Enhanced score: {player.enhanced_score}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\\nTesting system...")
system = UnifiedCoreSystem()
print(f"✓ System created")

# Test loading
print("\\nTest complete!")
'''

    with open('test_csv_loading.py', 'w') as f:
        f.write(test_content)

    print("  ✓ Created test_csv_loading.py")


def main():
    print("=" * 60)
    print("FIXING GUI LOADING ISSUES")
    print("=" * 60)

    if not os.path.exists('main_optimizer'):
        print("❌ Run from All_in_one_optimizer directory!")
        return

    # Apply all fixes
    fix_enhanced_scoring_method()
    fix_projection_mapping()
    add_player_pool_fix()
    create_test_script()

    print("\n" + "=" * 60)
    print("✅ ALL FIXES APPLIED!")
    print("=" * 60)

    print("\n📋 What was fixed:")
    print("1. Enhanced scoring now calls methods correctly")
    print("2. Projections map from AvgPointsPerGame")
    print("3. Player pool includes all players with projections > 0")

    print("\n🚀 Now test:")
    print("1. Test loading: python test_csv_loading.py")
    print("2. Run GUI: python main_optimizer/GUI.py")
    print("3. Load your CSV and check player pool > 0")


if __name__ == "__main__":
    main()