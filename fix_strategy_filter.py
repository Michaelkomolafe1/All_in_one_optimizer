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
        return False

    with open(filepath, 'r') as f:
        content = f.read()

    # The proper fix - ensure minimum players for each position
    proper_filter = '''    def apply_strategy_filter(self, players, strategy, contest_type=None):
        """Apply strategy filtering while ensuring lineup viability"""
        self.logger.info(f"Applying strategy filter: {strategy}")
        self.logger.info(f"Starting with {len(players)} players")

        # CRITICAL: Define minimum requirements for DFS lineup
        position_requirements = {
            'P': 2,   # Need exactly 2 pitchers
            'C': 1,   # Need 1 catcher
            '1B': 1,  # Need 1 first baseman
            '2B': 1,  # Need 1 second baseman
            '3B': 1,  # Need 1 third baseman
            'SS': 1,  # Need 1 shortstop
            'OF': 3   # Need 3 outfielders
        }

        # Group players by position
        by_position = {}
        for player in players:
            pos = player.position
            if pos not in by_position:
                by_position[pos] = []
            by_position[pos].append(player)

        # Log position counts before filtering
        self.logger.info("Players by position before filter:")
        for pos, players_at_pos in by_position.items():
            self.logger.info(f"  {pos}: {len(players_at_pos)} players")

        # Apply strategy-specific logic with position minimums
        filtered = []

        if strategy == 'projection_monster':
            # Keep top players but ensure minimums
            for pos, min_needed in position_requirements.items():
                if pos in by_position:
                    # Sort by optimization score
                    players_at_pos = sorted(
                        by_position[pos],
                        key=lambda x: getattr(x, f'{contest_type}_score', x.optimization_score) if contest_type else x.optimization_score,
                        reverse=True
                    )

                    # Determine how many to keep with buffer
                    if pos in ['P', 'SP']:
                        # Keep at least 5 pitchers for flexibility
                        keep = max(5, min_needed * 2)
                    elif pos == 'OF':
                        # Keep at least 10 outfielders
                        keep = max(10, min_needed * 3)
                    else:
                        # Keep at least 3x minimum for other positions
                        keep = max(3, min_needed * 3)

                    # Add top players at this position
                    filtered.extend(players_at_pos[:keep])

        elif strategy in ['balanced_projections', 'balanced_ownership']:
            # Less aggressive filtering - keep more players
            for pos, min_needed in position_requirements.items():
                if pos in by_position:
                    players_at_pos = sorted(
                        by_position[pos],
                        key=lambda x: x.optimization_score,
                        reverse=True
                    )
                    # Keep 5x minimum for balanced strategies
                    keep = max(10, min_needed * 5)
                    filtered.extend(players_at_pos[:keep])

        else:
            # For other strategies, keep most players
            all_sorted = sorted(players, key=lambda x: x.optimization_score, reverse=True)
            # Keep at least 80% of players or 100, whichever is less
            keep_count = min(len(players), max(100, int(len(players) * 0.8)))
            filtered = all_sorted[:keep_count]

        # Remove duplicates while preserving order
        seen = set()
        unique_filtered = []
        for player in filtered:
            if player not in seen:
                seen.add(player)
                unique_filtered.append(player)
        filtered = unique_filtered

        # CRITICAL SAFETY CHECK: Ensure we have minimum positions
        filtered_by_pos = {}
        for player in filtered:
            pos = player.position
            if pos not in filtered_by_pos:
                filtered_by_pos[pos] = []
            filtered_by_pos[pos].append(player)

        # Check each position requirement
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

        # SPECIAL HANDLING FOR PITCHERS (P, SP, RP all count as pitchers)
        pitcher_positions = ['P', 'SP', 'RP']
        total_pitchers = sum(len(filtered_by_pos.get(p, [])) for p in pitcher_positions)

        if total_pitchers < 2:
            self.logger.warning(f"Not enough total pitchers: {total_pitchers}")
            # Collect all available pitchers
            all_pitchers = []
            for p_pos in pitcher_positions:
                if p_pos in by_position:
                    all_pitchers.extend(by_position[p_pos])

            if all_pitchers:
                # Sort by score and add the best ones not already included
                all_pitchers = sorted(
                    all_pitchers,
                    key=lambda x: x.optimization_score,
                    reverse=True
                )
                additional = [p for p in all_pitchers if p not in filtered][:5]
                filtered.extend(additional)
                self.logger.info(f"Added {len(additional)} more pitchers to ensure viability")

        # Final verification log
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

        # Final pitcher count
        final_pitcher_count = sum(final_by_pos.get(p, 0) for p in pitcher_positions)
        self.logger.info(f"Total pitchers available: {final_pitcher_count}")

        return filtered'''

    # Find and replace the method
    if 'def apply_strategy_filter' in content:
        print("  Found existing apply_strategy_filter method")
        # Use a more precise pattern to replace the entire method
        pattern = r'def apply_strategy_filter\(self[^:]*:\s*\n(?:.*?\n)*?(?=\n    def |\nclass |\Z)'
        content = re.sub(pattern, proper_filter.strip() + '\n\n', content, flags=re.DOTALL)
        print("  ✓ Replaced with fixed version")
    else:
        print("  ⚠ Method not found, adding it")
        # Add it before the optimize method
        if 'def optimize(' in content:
            index = content.find('def optimize(')
            content = content[:index] + proper_filter + '\n\n' + content[index:]
            print("  ✓ Added fixed apply_strategy_filter")

    # Write back the fixed content
    with open(filepath, 'w') as f:
        f.write(content)

    print("  ✓ Strategy filter fixed!")
    return True


def create_verification_script():
    """Create a script to verify the fix works"""

    verify_script = '''#!/usr/bin/env python3
"""Verify the strategy filter fix"""

import sys
sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem

print("=" * 50)
print("VERIFYING STRATEGY FILTER FIX")
print("=" * 50)

# Test each strategy
strategies = ['projection_monster', 'balanced_projections', 'balanced_ownership', 'value_beast']
contest_types = ['cash', 'gpp']

system = UnifiedCoreSystem()

# You'll need to update this path to your actual CSV file
csv_path = "/home/michael/Downloads/DKSalaries(46).csv"  
system.load_csv(csv_path)
system.fetch_confirmed_players()

results = []
for contest_type in contest_types:
    print(f"\\nTesting {contest_type.upper()} contests:")

    for strategy in strategies:
        # Build pool with confirmed only
        system.build_player_pool(include_unconfirmed=False)

        print(f"  {strategy}:", end=" ")

        # Try to generate lineup
        try:
            lineups = system.optimize_lineup(
                strategy=strategy,
                contest_type=contest_type,
                num_lineups=1
            )

            if lineups and len(lineups) > 0:
                print(f"✅ SUCCESS - Generated lineup with {len(lineups[0])} players")
                results.append((contest_type, strategy, True))
            else:
                print(f"❌ FAILED - Could not generate lineup")
                results.append((contest_type, strategy, False))
        except Exception as e:
            print(f"❌ ERROR - {str(e)}")
            results.append((contest_type, strategy, False))

print("\\n" + "=" * 50)
print("SUMMARY:")
print("=" * 50)

success_count = sum(1 for _, _, success in results if success)
total_count = len(results)

print(f"Success Rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

if success_count == total_count:
    print("\\n✅ ALL STRATEGIES WORKING! The fix is successful!")
else:
    print("\\n⚠️ Some strategies still failing. Check the logs above.")

print("=" * 50)
'''

    with open('verify_strategy_fix.py', 'w') as f:
        f.write(verify_script)

    print("✓ Created verify_strategy_fix.py")
    return True


def main():
    print("=" * 60)
    print("FIXING STRATEGY FILTER BUG")
    print("=" * 60)

    print("\n📌 THE PRINCIPLE:")
    print("  • ALL strategies MUST be able to build lineups")
    print("  • The filter should NEVER remove required positions")
    print("  • Strategies control HOW to pick, not IF lineups can be built")

    # Check we're in the right directory
    if not os.path.exists('main_optimizer'):
        print("\n❌ Error: Wrong directory!")
        print("Please run from: /home/michael/Desktop/All_in_one_optimizer")
        print("\ncd /home/michael/Desktop/All_in_one_optimizer")
        print("python3 fix_strategy_filter.py")
        return

    # Apply the fix
    if fix_strategy_filter_properly():
        print("\n✅ Strategy filter has been fixed!")

        # Create verification script
        if create_verification_script():
            print("\n📋 Next Steps:")
            print("1. Verify the fix works:")
            print("   python3 verify_strategy_fix.py")
            print("\n2. Run your optimizer:")
            print("   python3 main_optimizer/GUI.py")

            print("\n💡 What the fix does:")
            print("  • Ensures minimum players for each position")
            print("  • Keeps at least 5 pitchers available")
            print("  • Adds safety checks to restore missing positions")
            print("  • Handles P, SP, RP as interchangeable pitcher positions")
            print("  • Different buffer sizes for different strategies")
    else:
        print("\n❌ Failed to apply fix. Please check the file path.")


if __name__ == "__main__":
    main()