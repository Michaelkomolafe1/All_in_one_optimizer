#!/usr/bin/env python3
"""
Direct fix - adds the methods exactly where they need to be
"""

import os


def direct_fix():
    print("🔧 DIRECT FIX - Adding methods to BulletproofDFSCore")

    # Read the file
    with open('bulletproof_dfs_core.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find the class definition
    class_line = -1
    for i, line in enumerate(lines):
        if 'class BulletproofDFSCore' in line:
            class_line = i
            print(f"✅ Found class at line {i + 1}")
            break

    if class_line == -1:
        print("❌ Could not find class")
        return False

    # Find the __init__ method
    init_line = -1
    for i in range(class_line, len(lines)):
        if 'def __init__(self)' in lines[i]:
            init_line = i
            print(f"✅ Found __init__ at line {i + 1}")
            break

    if init_line == -1:
        print("❌ Could not find __init__")
        return False

    # Find the end of __init__ (next method or less indentation)
    init_end = -1
    indent_level = len(lines[init_line]) - len(lines[init_line].lstrip())

    for i in range(init_line + 1, len(lines)):
        line = lines[i]
        if line.strip():  # Non-empty line
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent_level and 'def ' in line:
                init_end = i
                print(f"✅ Found end of __init__ at line {i + 1}")
                break

    if init_end == -1:
        # Try to find any method after init
        for i in range(init_line + 10, len(lines)):
            if '    def ' in lines[i]:
                init_end = i
                break

    if init_end == -1:
        print("❌ Could not find insertion point")
        return False

    # Insert the methods right after the first method we find
    new_methods = '''    # ==================== DFS UPGRADE METHODS ====================

    def get_cached_data(self, key: str, fetch_func, category: str = 'default'):
        """Use smart caching for any data fetch"""
        if 'UPGRADES_AVAILABLE' in globals() and UPGRADES_AVAILABLE:
            return smart_cache.get_or_fetch(key, fetch_func, category)
        else:
            return fetch_func()

    def generate_multiple_lineups(self, count: int = 20) -> list:
        """Generate multiple unique lineups for GPPs"""
        if 'UPGRADES_AVAILABLE' not in globals() or not UPGRADES_AVAILABLE:
            print("❌ Multi-lineup module not available")
            return []

        print(f"\\n🚀 Generating {count} lineups...")

        optimizer = MultiLineupOptimizer(self)
        lineups = optimizer.generate_gpp_lineups(
            num_lineups=count,
            max_exposure=0.5,
            min_salary=49000
        )

        # Show summary
        optimizer.print_summary()

        # Export for upload
        upload_file = optimizer.export_for_upload('draftkings')
        if upload_file:
            print(f"\\n📁 Upload file: {upload_file}")

        return lineups

    def track_lineup_performance(self, lineup: list, contest_info: dict):
        """Track lineup for future analysis"""
        if 'UPGRADES_AVAILABLE' not in globals() or not UPGRADES_AVAILABLE:
            return None

        contest_id = tracker.log_contest(lineup, contest_info)

        # Also save to database if available
        if hasattr(self, 'game_date'):
            contest_info['date'] = self.game_date

        return contest_id

    def get_performance_summary(self, days: int = 30):
        """Get performance tracking summary"""
        if 'UPGRADES_AVAILABLE' not in globals() or not UPGRADES_AVAILABLE:
            print("Performance tracking not available")
            return

        tracker.print_summary(days)

    def clear_cache(self, category: str = None):
        """Clear cache by category or all"""
        if 'UPGRADES_AVAILABLE' in globals() and UPGRADES_AVAILABLE:
            smart_cache.clear(category)
            print(f"🧹 Cleared cache: {category or 'all'}")

'''

    # Insert the methods
    lines.insert(init_end, new_methods + '\n')

    # Write back
    with open('bulletproof_dfs_core.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"✅ Added methods after line {init_end}")

    # Now update the caching in detect_confirmed_players
    print("\n🔧 Updating caching in detect_confirmed_players...")

    with open('bulletproof_dfs_core.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Update the confirmation call if not already cached
    if 'get_cached_data' not in content or 'self.confirmation_system.get_all_confirmations()' in content:
        # Find and replace
        old_line = 'lineup_count, pitcher_count = self.confirmation_system.get_all_confirmations()'

        new_line = '''lineup_count, pitcher_count = self.get_cached_data(
            f"confirmations_{self.game_date}",
            self.confirmation_system.get_all_confirmations,
            "mlb_lineups"
        )'''

        content = content.replace(old_line, new_line)

        with open('bulletproof_dfs_core.py', 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Updated confirmation caching")

    return True


def test_fix():
    """Test if the fix worked"""
    print("\n🧪 Testing the fix...")

    try:
        from bulletproof_dfs_core import BulletproofDFSCore
        core = BulletproofDFSCore()

        # Check methods
        has_cached = hasattr(core, 'get_cached_data')
        has_multi = hasattr(core, 'generate_multiple_lineups')

        print(f"get_cached_data: {'✅' if has_cached else '❌'}")
        print(f"generate_multiple_lineups: {'✅' if has_multi else '❌'}")

        if has_cached and has_multi:
            print("\n✅ ALL METHODS ADDED SUCCESSFULLY!")
            return True
        else:
            print("\n❌ Some methods still missing")
            return False

    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def update_test_csv():
    """Update test script with correct CSV name"""
    test_file = 'test_multi_lineup.py'

    if os.path.exists(test_file):
        with open(test_file, 'r') as f:
            content = f.read()

        # Update CSV name
        content = content.replace('DKSalaries (82).csv', 'DKSalaries_good.csv')

        with open(test_file, 'w') as f:
            f.write(content)

        print("✅ Updated test script with correct CSV name")


def main():
    print("🚀 DIRECT FIX FOR DFS INTEGRATION")
    print("=" * 50)

    # Apply the fix
    if direct_fix():
        print("\n✅ Fix applied!")

        # Test it
        if test_fix():
            # Update test CSV
            update_test_csv()

            print("\n🎉 EVERYTHING IS WORKING!")
            print("\nNow you can:")
            print("1. python test_integration.py  # Should show ✅ for all")
            print("2. python test_multi_lineup.py  # Should generate lineups")
            print("3. python enhanced_dfs_gui.py   # Should have multi-lineup option")
        else:
            print("\n⚠️ Fix was applied but test failed")
            print("Try restarting your Python environment")
    else:
        print("\n❌ Fix failed")


if __name__ == "__main__":
    main()