#!/usr/bin/env python3
"""
DIRECT METHOD FIX
================
Directly restore the detect_confirmed_players method
"""


def direct_fix():
    """Direct surgical fix"""

    print("🔧 DIRECT SURGICAL FIX")
    print("=" * 40)

    try:
        with open('bulletproof_dfs_core.py', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ File not found!")
        return False

    # Create backup
    with open('bulletproof_dfs_core_backup.py', 'w') as f:
        f.write(content)
    print("✅ Backup created: bulletproof_dfs_core_backup.py")

    # Add the enhanced pitcher import if missing
    if "from enhanced_pitcher_detection import integrate_with_csv_players" not in content:
        import_addition = '''
# Enhanced Pitcher Detection Import - ADDED
try:
    from enhanced_pitcher_detection import integrate_with_csv_players
    ENHANCED_PITCHER_AVAILABLE = True
    print("✅ Enhanced Pitcher Detection integration loaded")
except ImportError:
    ENHANCED_PITCHER_AVAILABLE = False
    def integrate_with_csv_players(players): return {}
    print("⚠️ Enhanced Pitcher Detection not available")
'''

        # Find a good place to insert (after the other imports)
        if "STATCAST_AVAILABLE = False" in content:
            insert_point = content.find("STATCAST_AVAILABLE = False") + len("STATCAST_AVAILABLE = False")
            content = content[:insert_point] + import_addition + content[insert_point:]

    # The working method to add
    working_method = '''    def detect_confirmed_players(self) -> int:
        """FIXED: Pass loaded CSV data to confirmations system with enhanced pitchers"""

        if not self.confirmed_lineups:
            print("⚠️ Confirmed lineups module not available")
            return 0

        print("🔍 Detecting confirmed players using loaded CSV data...")

        # NEW: Pass our already-loaded player data to confirmations
        if hasattr(self.confirmed_lineups, 'set_players_data'):
            self.confirmed_lineups.set_players_data(self.players)

        # Ensure data is loaded
        if hasattr(self.confirmed_lineups, 'ensure_data_loaded'):
            self.confirmed_lineups.ensure_data_loaded(max_wait_seconds=15)

        confirmed_count = 0

        # Process all players for confirmations
        for player in self.players:
            # Check lineup confirmations for position players
            if player.primary_position != 'P':
                is_confirmed, batting_order = self.confirmed_lineups.is_player_confirmed(
                    player.name, player.team
                )
                if is_confirmed:
                    player.add_confirmation_source("integrated_lineup")
                    confirmed_count += 1

            # Check pitcher confirmations
            else:
                if player.name.lower() not in KNOWN_RELIEF_PITCHERS:
                    is_starting = self.confirmed_lineups.is_pitcher_starting(
                        player.name, player.team
                    )
                    if is_starting:
                        player.add_confirmation_source("integrated_starter")
                        confirmed_count += 1

        print(f"✅ Basic confirmed detection: {confirmed_count} players")

        # ENHANCED PITCHER DETECTION
        enhanced_pitcher_count = 0
        if ENHANCED_PITCHER_AVAILABLE:
            try:
                print("🎯 Applying enhanced pitcher detection...")
                confirmed_pitchers = integrate_with_csv_players(self.players)

                for team, pitcher_info in confirmed_pitchers.items():
                    pitcher_name = pitcher_info['name']

                    # Find matching pitcher in our CSV
                    for player in self.players:
                        if (player.primary_position == 'P' and 
                            self._name_similarity(pitcher_name, player.name) >= 0.65):

                            if not player.is_confirmed:  # Don't double-confirm
                                source = f"enhanced_pitcher_{pitcher_info['source']}"
                                player.add_confirmation_source(source)
                                confirmed_count += 1
                                enhanced_pitcher_count += 1
                            break

                print(f"✅ Enhanced pitcher detection: {enhanced_pitcher_count} additional pitchers")

            except Exception as e:
                print(f"⚠️ Enhanced pitcher detection error: {e}")

        print(f"✅ Total confirmed detection: {confirmed_count} players")
        return confirmed_count

'''

    # Find the BulletproofDFSCore class
    class_start = content.find("class BulletproofDFSCore:")
    if class_start == -1:
        print("❌ Could not find BulletproofDFSCore class")
        return False

    # Look for an existing detect_confirmed_players method and remove it
    method_start = content.find("def detect_confirmed_players(self) -> int:", class_start)
    if method_start != -1:
        print("🔍 Found existing broken method, removing...")

        # Find the end of the method
        lines = content[method_start:].split('\n')
        method_lines = []
        in_method = True

        for i, line in enumerate(lines):
            if i == 0:  # First line (method definition)
                method_lines.append(line)
                continue

            # If we hit another method or class at the same indentation level, we're done
            if line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                break
            elif line.strip() and line.startswith('    def ') and not line.startswith('        '):
                # Another method at class level
                break
            else:
                method_lines.append(line)

        method_end = method_start + len('\n'.join(method_lines))

        # Remove the broken method
        content = content[:method_start] + content[method_end:]

    # Find a good place to insert the new method (after __init__)
    init_pattern = "print(\"🚀 Bulletproof DFS Core - ALL METHODS INCLUDED\")"
    init_end = content.find(init_pattern, class_start)

    if init_end != -1:
        # Find the end of the __init__ method
        init_end += len(init_pattern)
        lines = content[init_end:].split('\n')

        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                # Found end of class or next top-level item
                insertion_point = init_end + len('\n'.join(lines[:i]))
                break
            elif line.strip() and line.startswith('    def ') and not line.startswith('        '):
                # Found next method
                insertion_point = init_end + len('\n'.join(lines[:i]))
                break
        else:
            # Couldn't find a good spot, insert at end of what we found
            insertion_point = init_end + len('\n'.join(lines))

        # Insert the working method
        content = content[:insertion_point] + '\n' + working_method + '\n' + content[insertion_point:]
        print("✅ Inserted working method")

    else:
        print("❌ Could not find good insertion point")
        return False

    # Write the fixed content
    with open('bulletproof_dfs_core.py', 'w') as f:
        f.write(content)

    print("✅ File updated")

    # Test the fix
    try:
        from bulletproof_dfs_core import BulletproofDFSCore
        core = BulletproofDFSCore()

        if hasattr(core, 'detect_confirmed_players'):
            print("✅ Method successfully restored!")
            return True
        else:
            print("❌ Method still missing")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("🔧 DIRECT METHOD RESTORATION")
    print("=" * 50)

    success = direct_fix()

    if success:
        print(f"\n🎉 SUCCESS!")
        print(f"=" * 20)
        print(f"✅ Method restored")
        print(f"✅ Enhanced pitcher detection integrated")
        print(f"✅ System should work now")
        print(f"")
        print(f"🚀 TRY NOW:")
        print(f"python enhanced_dfs_gui.py")
    else:
        print(f"\n❌ FAILED!")
        print(f"Backup saved as: bulletproof_dfs_core_backup.py")
        print(f"You can restore with:")
        print(f"cp bulletproof_dfs_core_backup.py bulletproof_dfs_core.py")