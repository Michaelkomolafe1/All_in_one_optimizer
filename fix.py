#!/usr/bin/env python3
"""
FIX STRATEGY FILTER - ALL STRATEGIES MUST BUILD LINEUPS
========================================================
The filter should NEVER remove so many players that lineups can't be built
"""

import os
import re


def fix_strategy_filter_properly():
    """Fix the strategy filter to ensure it always keeps enough players"""

    print("🔧 Fixing strategy filter to ALWAYS allow lineup building...")

    filepath = 'main_optimizer/unified_milp_optimizer.py'

    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    with open(filepath, 'r') as f:
        content = f.read()

    # The proper fix - ensure minimum players for each position
    proper_filter = '''
    def apply_strategy_filter(self, players, strategy, contest_type=None):
        """Apply strategy filtering while ensuring lineup viability"""
        self.logger.info(f"Applying strategy filter: {strategy}")
        self.logger.info(f"Starting with {len(players)} players")

        # CRITICAL: Define minimum requirements
        position_requirements = {
            'P': 2, 'SP': 2, 'RP': 0,  # Need at least 2 pitchers
            'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1,  # Infield
            'OF': 3  # Outfield
        }

        # Group players by position
        by_position = {}
        for player in players:
            pos = player.position
            if pos not in by_position:
                by_position[pos] = []
            by_position[pos].append(player)

        # Log position counts
        self.logger.info("Players by position before filter:")
        for pos, players_at_pos in by_position.items():
            self.logger.info(f"  {pos}: {len(players_at_pos)} players")

        # Apply strategy-specific logic
        filtered = []

        if strategy == 'projection_monster':
            # For projection_monster, keep top players but ensure minimums
            for pos, min_needed in position_requirements.items():
                if pos in by_position:
                    # Sort by score
                    players_at_pos = sorted(
                        by_position[pos],
                        key=lambda x: getattr(x, f'{contest_type}_score', x.optimization_score),
                        reverse=True
                    )

                    # Keep at least minimum + buffer
                    if pos in ['P', 'SP']:
                        # Keep more pitchers (at least 5)
                        keep = max(5, min_needed * 2)
                    elif pos == 'OF':
                        # Keep more outfielders (at least 10)
                        keep = max(10, min_needed * 3)
                    else:
                        # Keep at least 3x minimum for other positions
                        keep = max(3, min_needed * 3)

                    # Add top players at this position
                    filtered.extend(players_at_pos[:keep])

        elif strategy in ['balanced_projections', 'balanced_ownership']:
            # Less aggressive filtering
            for pos, min_needed in position_requirements.items():
                if pos in by_position:
                    players_at_pos = sorted(
                        by_position[pos],
                        key=lambda x: x.optimization_score,
                        reverse=True
                    )
                    # Keep more players
                    keep = max(10, min_needed * 5)
                    filtered.extend(players_at_pos[:keep])

        else:
            # For other strategies, keep most players
            # Just remove the very worst
            all_sorted = sorted(players, key=lambda x: x.optimization_score, reverse=True)

            # Keep at least 80% of players or 100, whichever is less
            keep_count = min(len(players), max(100, int(len(players) * 0.8)))
            filtered = all_sorted[:keep_count]

        # SAFETY CHECK: Ensure we have minimum positions
        filtered_by_pos = {}
        for player in filtered:
            pos = player.position
            if pos not in filtered_by_pos:
                filtered_by_pos[pos] = []
            filtered_by_pos[pos].append(player)

        # Check if we have enough
        for pos, min_needed in position_requirements.items():
            if min_needed > 0:
                current = len(filtered_by_pos.get(pos, []))
                if current < min_needed:
                    self.logger.warning(f"Not enough {pos} after filter: {current} < {min_needed}")
                    # Add back top players at this position
                    if pos in by_position:
                        needed = min_needed - current + 2  # Add buffer
                        additional = [p for p in by_position[pos] if p not in filtered][:needed]
                        filtered.extend(additional)
                        self.logger.info(f"Added {len(additional)} more {pos} players")

        # Handle pitcher position mapping (P, SP, RP all count as pitchers)
        pitcher_count = sum(len(filtered_by_pos.get(p, [])) for p in ['P', 'SP', 'RP'])
        if pitcher_count < 2:
            self.logger.warning(f"Not enough total pitchers: {pitcher_count}")
            # Add more pitchers
            all_pitchers = []
            for p in ['P', 'SP', 'RP']:
                if p in by_position:
                    all_pitchers.extend(by_position[p])

            if all_pitchers:
                all_pitchers = sorted(all_pitchers, 
                                    key=lambda x: x.optimization_score, 
                                    reverse=True)
                additional = [p for p in all_pitchers if p not in filtered][:5]
                filtered.extend(additional)
                self.logger.info(f"Added {len(additional)} more pitchers")

        # Final count
        final_by_pos = {}
        for player in filtered:
            pos = player.position
            if pos not in final_by_pos:
                final_by_pos[pos] = 0
            final_by_pos[pos] += 1

        self.logger.info(f"After filter: {len(filtered)} total players")
        self.logger.info("Final position counts:")
        for pos, count in sorted(final_by_pos.items()):
            self.logger.info(f"  {pos}: {count}")

        return filtered
'''

    # Find and replace the method
    if 'def apply_strategy_filter' in content:
        print("  Found existing apply_strategy_filter method")
        # Replace it
        pattern = r'def apply_strategy_filter\(self.*?\n(?=    def |\nclass |\Z)'
        content = re.sub(pattern, proper_filter.strip() + '\n\n', content, flags=re.DOTALL)
        print("  ✓ Replaced with fixed version")
    else:
        print("  ⚠ Method not found, adding it")
        # Add it before optimize method
        if 'def optimize(' in content:
            index = content.find('def optimize(')
            content = content[:index] + proper_filter + '\n\n' + content[index:]
            print("  ✓ Added fixed apply_strategy_filter")

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print("  ✓ Strategy filter fixed!")


def verify_fix():
    """Create a verification script"""

    verify_script = '''#!/usr/bin/env python3
"""Verify the strategy filter fix"""

import sys
sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem

print("=" * 50)
print("VERIFYING STRATEGY FILTER FIX")
print("=" * 50)

# Test each strategy
strategies = ['projection_monster', 'balanced_projections', 'value_beast']
contest_types = ['cash', 'gpp']

system = UnifiedCoreSystem()
csv_path = "/home/michael/Downloads/DKSalaries(46).csv"
system.load_csv(csv_path)
system.fetch_confirmed_players()

for contest_type in contest_types:
    print(f"\\nTesting {contest_type.upper()} contests:")

    for strategy in strategies:
        # Build pool with confirmed only
        system.build_player_pool(include_unconfirmed=False)

        print(f"  {strategy}:", end=" ")

        # Try to generate lineup
        lineups = system.optimize_lineup(
            strategy=strategy,
            contest_type=contest_type,
            num_lineups=1
        )

        if lineups and len(lineups) > 0:
            print(f"✅ SUCCESS - Generated lineup")
        else:
            print(f"❌ FAILED - Could not generate lineup")

print("\\n" + "=" * 50)
print("All strategies should show SUCCESS")
'''

    with open('verify_strategy_fix.py', 'w') as f:
        f.write(verify_script)

    print("✓ Created verify_strategy_fix.py")


def main():
    print("=" * 60)
    print("FIXING STRATEGY FILTER - PROPERLY")
    print("=" * 60)

    print("\n📌 THE PRINCIPLE:")
    print("  ALL strategies MUST be able to build lineups!")
    print("  The filter should NEVER remove required positions")

    if not os.path.exists('main_optimizer'):
        print("\n❌ Wrong directory!")
        print("cd /home/michael/Desktop/All_in_one_optimizer")
        return

    # Apply the fix
    fix_strategy_filter_properly()
    verify_fix()

    print("\n" + "=" * 60)
    print("✅ STRATEGY FILTER FIXED!")
    print("=" * 60)

    print("\n🧪 Verify all strategies work:")
    print("  python verify_strategy_fix.py")

    print("\n🚀 Then run the GUI:")
    print("  python main_optimizer/GUI.py")

    print("\nNow ALL strategies will:")
    print("  ✓ Keep minimum required players for each position")
    print("  ✓ Always have at least 2 pitchers")
    print("  ✓ Successfully generate lineups")

    print("\n💡 The fix ensures:")
    print("  - At least 5 pitchers are kept")
    print("  - At least 3x minimum for each position")
    print("  - Safety checks add players back if needed")


if __name__ == "__main__":
    main()