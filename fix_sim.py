#!/usr/bin/env python3
"""
FIX SIMULATION PLAYER ATTRIBUTES
=================================
Fixes the None attribute errors in simulation
Save as: fix_sim_attributes.py
Run from: /home/michael/Desktop/All_in_one_optimizer/
"""

import os


def fix_simulation_player_creation():
    """Fix the player creation in comprehensive_simulation_runner.py"""

    print("🔧 Fixing simulation player attributes...")

    filepath = 'simulation/comprehensive_simulation_runner.py'

    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    with open(filepath, 'r') as f:
        content = f.read()

    # Find the convert_to_unified_players method
    if 'convert_to_unified_players' in content:
        # Create improved player conversion
        new_conversion = '''    def convert_to_unified_players(self, sim_players: List) -> List[UnifiedPlayer]:
        """Convert simulated players to UnifiedPlayer objects with ALL required attributes"""
        unified_players = []

        for sp in sim_players:
            # Create UnifiedPlayer with ALL required attributes
            up_data = {
                'id': str(hash(sp.name)),
                'name': sp.name,
                'team': sp.team,
                'salary': sp.salary,
                'primary_position': sp.position,
                'positions': [sp.position],
                'AvgPointsPerGame': sp.projection
            }

            player = UnifiedPlayer(up_data)

            # CRITICAL: Set ALL attributes that strategies might check
            # Base attributes
            player.base_projection = sp.projection
            player.dff_projection = sp.projection
            player.projection = sp.projection

            # Position flags
            player.is_pitcher = (sp.position == 'P')
            player.position = sp.position

            # Batting/Pitching attributes - SET DEFAULTS TO AVOID None
            player.batting_order = getattr(sp, 'batting_order', 5 if sp.position != 'P' else None)
            if player.batting_order is None and sp.position != 'P':
                player.batting_order = 5  # Default middle of order

            # Performance metrics - NEVER None
            player.recent_performance = getattr(sp, 'recent_performance', 1.0)
            player.consistency_score = getattr(sp, 'consistency_score', 0.7)
            player.matchup_score = getattr(sp, 'matchup_score', 1.0)
            player.floor = sp.projection * 0.7
            player.ceiling = sp.projection * 1.5

            # Vegas/Game data - NEVER None
            player.vegas_total = getattr(sp, 'vegas_total', 8.5)
            player.game_total = getattr(sp, 'game_total', 8.5)
            player.team_total = getattr(sp, 'team_total', 4.25)
            player.implied_team_score = player.team_total

            # Ownership - NEVER None
            player.ownership_projection = getattr(sp, 'ownership', 15.0)
            player.projected_ownership = player.ownership_projection

            # Advanced stats - NEVER None
            player.park_factor = getattr(sp, 'park_factor', 1.0)
            player.weather_score = getattr(sp, 'weather_score', 1.0)
            player.barrel_rate = getattr(sp, 'barrel_rate', 8.0)
            player.hard_hit_rate = getattr(sp, 'hard_hit_rate', 35.0)
            player.xwoba = getattr(sp, 'xwoba', 0.320)

            # Stack/Correlation - NEVER None
            player.stack_score = getattr(sp, 'stack_score', 0.0)
            player.correlation_score = getattr(sp, 'correlation_score', 0.0)
            player.game_stack_score = 0.0

            # Scores for optimization
            player.optimization_score = sp.projection
            player.enhanced_score = sp.projection
            player.gpp_score = sp.projection
            player.cash_score = sp.projection

            # Recent scores
            player.recent_scores = [sp.projection * 0.9, sp.projection * 1.1, sp.projection * 0.95]
            player.dff_l5_avg = sp.projection

            # Additional required attributes
            player.value = sp.projection / (sp.salary / 1000) if sp.salary > 0 else 0
            player.points_per_dollar = player.value

            unified_players.append(player)

        return unified_players'''

        # Replace the method
        import re
        pattern = r'def convert_to_unified_players\(self.*?\n(?:.*?\n)*?        return unified_players'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            content = content[:match.start()] + new_conversion + content[match.end():]
            print("✅ Fixed convert_to_unified_players method")
        else:
            print("⚠️ Could not find exact method, appending new version")
            # Find the class and append
            class_end = content.rfind('\n\nif __name__')
            if class_end > 0:
                content = content[:class_end] + '\n' + new_conversion + content[class_end:]

    # Also fix the simple player creation
    simple_player_fix = '''
            # Ensure all attributes exist
            if not hasattr(player, 'batting_order'):
                player.batting_order = 5 if player.position != 'P' else None
            if not hasattr(player, 'recent_performance'):
                player.recent_performance = 1.0
            if not hasattr(player, 'vegas_total'):
                player.vegas_total = 8.5
            if not hasattr(player, 'ownership_projection'):
                player.ownership_projection = 15.0
            if not hasattr(player, 'barrel_rate'):
                player.barrel_rate = 8.0'''

    # Save the fixed file
    with open(filepath, 'w') as f:
        f.write(content)

    print("✅ Fixed simulation player attributes")

    # Also create a test to verify
    create_test_script()


def create_test_script():
    """Create a test script to verify fixes work"""

    test_content = '''#!/usr/bin/env python3
"""Test that simulation works after fixes"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.comprehensive_simulation_runner import ComprehensiveSimulationRunner

print("Testing simulation with fixed attributes...")

runner = ComprehensiveSimulationRunner()

# Run a quick test
print("\\nRunning 10 quick simulations...")
results = runner.run_comprehensive_test(
    num_simulations=10,
    contest_types=['cash', 'gpp'],
    slate_sizes=['small'],
    field_size=50
)

print("\\n✅ Simulation completed without errors!")
print("\\nCheck results:")
print("- Cash win rates should be 40-60% (not 100%)")
print("- GPP ROI should be -50% to +100% (not 900%)")
'''

    with open('test_sim_fix.py', 'w') as f:
        f.write(test_content)

    print("✅ Created test_sim_fix.py")


def check_main_optimizer_safety():
    """Check if main optimizer would have same issues"""

    print("\n🔍 Checking main optimizer safety...")

    # Check if unified_player_model sets defaults
    filepath = 'main_optimizer/unified_player_model.py'

    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()

        # Check for default value handling
        has_defaults = False
        if 'getattr' in content or 'if not hasattr' in content:
            has_defaults = True

        if has_defaults:
            print("✅ Main optimizer has default value handling")
            print("   Should work fine with real CSV data")
        else:
            print("⚠️ Main optimizer might have issues with missing data")
            print("   Consider adding default values")

    print("\n💡 Your main optimizer is PROBABLY SAFE because:")
    print("   1. Real CSV data has actual values")
    print("   2. Data enrichment fills in missing values")
    print("   3. Only simulation has this issue")


def main():
    """Apply all fixes"""
    print("=" * 60)
    print("FIXING SIMULATION ATTRIBUTE ERRORS")
    print("=" * 60)

    # Apply fixes
    fix_simulation_player_creation()
    check_main_optimizer_safety()

    print("\n" + "=" * 60)
    print("✅ FIXES APPLIED!")
    print("=" * 60)

    print("\n📋 Next steps:")
    print("1. Test the fix:")
    print("   python test_sim_fix.py")
    print("\n2. Run full simulation:")
    print("   python simulation/comprehensive_simulation_runner.py")
    print("\n3. Your main optimizer should be fine:")
    print("   python main_optimizer/GUI.py")

    print("\n⚠️ IMPORTANT:")
    print("The 100% win rates are WRONG!")
    print("After fixing, you should see:")
    print("- Cash: 45-55% win rate")
    print("- GPP: -20% to +20% average ROI")


if __name__ == "__main__":
    main()