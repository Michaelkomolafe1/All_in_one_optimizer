#!/usr/bin/env python3
"""
FIX UNIFIEDPLAYER INITIALIZATION ERROR
=======================================
The UnifiedPlayer expects specific arguments, not a dictionary
"""

import os


def fix_convert_to_unified_players():
    """Fix the UnifiedPlayer initialization in comprehensive_simulation_runner.py"""

    print("🔧 Fixing UnifiedPlayer initialization...")

    # The CORRECT way to create UnifiedPlayer objects
    correct_method = '''def convert_to_unified_players(self, sim_players: List) -> List[UnifiedPlayer]:
    """Convert simulated players to UnifiedPlayer objects"""
    unified_players = []

    for sp in sim_players:
        # UnifiedPlayer expects these exact arguments in order
        player = UnifiedPlayer(
            id=str(hash(sp.name)),
            name=sp.name,
            team=sp.team,
            salary=sp.salary,
            primary_position=sp.position,
            positions=[sp.position]
        )

        # Now set additional attributes
        player.AvgPointsPerGame = sp.projection
        player.base_projection = sp.projection
        player.dff_projection = sp.projection
        player.projection = sp.projection

        # Position info
        player.is_pitcher = (sp.position == 'P')
        player.position = sp.position

        # Batting order - NEVER None for position players
        if sp.position != 'P':
            player.batting_order = getattr(sp, 'batting_order', 5)
        else:
            player.batting_order = None

        # Performance metrics - ALWAYS have values
        player.recent_performance = getattr(sp, 'recent_performance', 1.0)
        player.consistency_score = getattr(sp, 'consistency_score', 0.7)
        player.matchup_score = getattr(sp, 'matchup_score', 1.0)
        player.floor = sp.projection * 0.7
        player.ceiling = sp.projection * 1.5

        # Vegas data - ALWAYS have values
        player.vegas_total = getattr(sp, 'vegas_total', 8.5)
        player.game_total = getattr(sp, 'game_total', 8.5)
        player.team_total = getattr(sp, 'team_total', 4.25)
        player.implied_team_score = player.team_total

        # Ownership - ALWAYS have value
        player.ownership_projection = getattr(sp, 'ownership', 15.0)
        player.projected_ownership = player.ownership_projection

        # Advanced stats - ALWAYS have values
        player.park_factor = getattr(sp, 'park_factor', 1.0)
        player.weather_score = getattr(sp, 'weather_score', 1.0)
        player.barrel_rate = getattr(sp, 'barrel_rate', 8.0)
        player.hard_hit_rate = getattr(sp, 'hard_hit_rate', 35.0)
        player.xwoba = getattr(sp, 'xwoba', 0.320)

        # Correlation/Stack scores
        player.stack_score = 0.0
        player.correlation_score = 0.0
        player.game_stack_score = 0.0

        # Optimization scores
        player.optimization_score = sp.projection
        player.enhanced_score = sp.projection
        player.gpp_score = sp.projection
        player.cash_score = sp.projection

        # Other required attributes
        player.value = sp.projection / (sp.salary / 1000) if sp.salary > 0 else 0
        player.points_per_dollar = player.value
        player.recent_scores = [sp.projection * 0.9, sp.projection * 1.1, sp.projection * 0.95]
        player.dff_l5_avg = sp.projection

        unified_players.append(player)

    return unified_players'''

    # Write to a file you can copy from
    with open('fixed_convert_method.py', 'w') as f:
        f.write(correct_method)

    print("✅ Created fixed_convert_method.py")
    print("\n📋 Manual fix instructions:")
    print("1. Open simulation/comprehensive_simulation_runner.py")
    print("2. Find the convert_to_unified_players method")
    print("3. Replace it with the content from fixed_convert_method.py")
    print("\nKey change: UnifiedPlayer(name=name, ...) instead of UnifiedPlayer(up_data)")


def create_working_test():
    """Create a test that will work after the fix"""

    test_code = '''#!/usr/bin/env python3
"""Test UnifiedPlayer creation directly"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_optimizer.unified_player_model import UnifiedPlayer

print("Testing UnifiedPlayer creation...")

# Test 1: Create with correct arguments
try:
    player = UnifiedPlayer(
        id="1",
        name="Test Player",
        team="NYY",
        salary=10000,
        primary_position="OF",
        positions=["OF"]
    )
    print("✅ UnifiedPlayer created successfully!")
    print(f"   Name: {player.name}")
    print(f"   Team: {player.team}")
    print(f"   Salary: {player.salary}")

    # Set additional attributes
    player.base_projection = 15.0
    player.batting_order = 3
    player.recent_performance = 1.2
    print(f"   Projection: {player.base_projection}")

except Exception as e:
    print(f"❌ Failed: {e}")

    # Try alternate method if first fails
    print("\\nTrying with dictionary...")
    try:
        data = {
            'Name': 'Test Player',
            'Team': 'NYY', 
            'Salary': 10000,
            'Position': 'OF'
        }
        player = UnifiedPlayer(data)
        print("✅ Dictionary method works!")
    except Exception as e2:
        print(f"❌ Dictionary method also failed: {e2}")

print("\\n📋 The correct format for UnifiedPlayer is:")
print("UnifiedPlayer(id, name, team, salary, primary_position, positions)")
'''

    with open('test_player_creation.py', 'w') as f:
        f.write(test_code)

    print("✅ Created test_player_creation.py")


def quick_patch_simulation():
    """Apply a quick patch to the simulation file"""

    print("\n🩹 Attempting quick patch...")

    filepath = 'simulation/comprehensive_simulation_runner.py'

    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()

        # Replace the incorrect initialization
        old_pattern = '''player = UnifiedPlayer(up_data)'''
        new_pattern = '''# Create UnifiedPlayer with required arguments
        player = UnifiedPlayer(
            id=up_data['id'],
            name=up_data['name'],
            team=up_data['team'],
            salary=up_data['salary'],
            primary_position=up_data['primary_position'],
            positions=up_data['positions']
        )

        # Set AvgPointsPerGame separately
        player.AvgPointsPerGame = up_data['AvgPointsPerGame']'''

        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)

            with open(filepath, 'w') as f:
                f.write(content)

            print("✅ Applied quick patch!")
            return True
        else:
            print("⚠️ Could not find pattern to patch")
            print("   You'll need to manually fix the convert_to_unified_players method")
            return False


def main():
    print("=" * 60)
    print("FIXING UNIFIEDPLAYER INITIALIZATION")
    print("=" * 60)

    # Create the fixed method
    fix_convert_to_unified_players()

    # Create test
    create_working_test()

    # Try quick patch
    if quick_patch_simulation():
        print("\n✅ Quick patch applied! Test now:")
        print("python simple_sim_test.py")
    else:
        print("\n⚠️ Manual fix needed:")
        print("1. Copy the method from fixed_convert_method.py")
        print("2. Replace convert_to_unified_players in comprehensive_simulation_runner.py")

    print("\n📋 Test player creation:")
    print("python test_player_creation.py")


if __name__ == "__main__":
    main()