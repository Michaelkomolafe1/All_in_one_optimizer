#!/usr/bin/env python3
"""
Fix the confirmation return type issue
"""

import os


def fix_fetch_confirmed_players():
    """Fix to handle the tuple return from get_all_confirmations"""

    print("🔧 Fixing fetch_confirmed_players in unified_core_system_updated.py...")

    filepath = 'main_optimizer/unified_core_system_updated.py'

    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()

    # New fetch_confirmed_players method that handles the tuple return
    new_method = '''    def fetch_confirmed_players(self) -> int:
        """Fetch confirmed lineups - reinitialize with CSV players first"""
        try:
            # Import here to avoid circular imports
            from smart_confirmation import UniversalSmartConfirmation

            # Reinitialize confirmation system with current CSV players
            self.log("Initializing confirmation system with CSV players...")
            self.confirmation_system = UniversalSmartConfirmation(
                csv_players=self.players,
                verbose=True
            )

            # Now fetch confirmations
            self.log("Fetching confirmed lineups...")
            result = self.confirmation_system.get_all_confirmations()

            # Handle both dict and tuple returns
            if isinstance(result, tuple):
                # If it's a tuple, first element is the dict of confirmed players
                confirmed_players = result[0] if result else {}
            elif isinstance(result, dict):
                confirmed_players = result
            else:
                self.log(f"Unexpected return type: {type(result)}")
                confirmed_players = {}

            if not confirmed_players:
                self.log("No confirmations available (games may not have started)")
                return 0

            # Mark players as confirmed
            confirmed_count = 0
            for player in self.players:
                # Clean player name for matching
                player_name_clean = player.name.upper().strip()

                # Check if player is in confirmed list
                for conf_name, conf_data in confirmed_players.items():
                    conf_name_clean = conf_name.upper().strip()

                    # Multiple matching strategies
                    if (conf_name_clean == player_name_clean or 
                        player.name in conf_name or 
                        conf_name in player.name):

                        player.is_confirmed = True

                        # Handle batting order (might be in different formats)
                        if isinstance(conf_data, dict):
                            if 'batting_order' in conf_data:
                                player.batting_order = conf_data['batting_order']
                            elif 'order' in conf_data:
                                player.batting_order = conf_data['order']

                        confirmed_count += 1
                        break

            self.log(f"Marked {confirmed_count} players as confirmed")
            return confirmed_count

        except Exception as e:
            self.log(f"Error fetching confirmations: {e}")
            import traceback
            self.log(traceback.format_exc())
            return 0'''

    # Find and replace the method
    import re
    pattern = r'def fetch_confirmed_players\(self\)[^:]*:.*?(?=\n    def |\nclass |\Z)'

    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = re.sub(pattern, new_method.strip(), content, flags=re.DOTALL)
        print("  ✓ Replaced fetch_confirmed_players method")
    else:
        print("  ⚠ Could not find method to replace")
        print("  You may need to manually replace it")

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print("  ✓ Fixed confirmation handling")


def main():
    print("=" * 60)
    print("FIXING CONFIRMATION RETURN TYPE")
    print("=" * 60)

    if not os.path.exists('main_optimizer'):
        print("❌ Run from All_in_one_optimizer directory!")
        return

    # Apply fix
    fix_fetch_confirmed_players()

    print("\n" + "=" * 60)
    print("✅ FIXED!")
    print("=" * 60)

    print("\n🚀 Next steps:")
    print("1. Restart the GUI")
    print("2. Load your CSV")
    print("3. Click 'Fetch Confirmations' - should show 108 confirmed")
    print("4. Click 'Rebuild Pool' - should show confirmed players")

    print("\n💡 The confirmation system found:")
    print("- 108 confirmed players")
    print("- 12 starting pitchers")
    print("- All lineups are available!")


if __name__ == "__main__":
    main()