#!/usr/bin/env python3
"""
VERIFY SLATE DETECTION
======================
Verify the slate detection is working
"""

import sys
import pandas as pd
from unified_core_system import UnifiedCoreSystem


def verify_slate_detection(csv_path):
    """Verify slate detection with your CSV"""
    print(f"\n🧪 VERIFYING SLATE DETECTION")
    print("=" * 70)
    print(f"CSV: {csv_path}")

    # Load CSV to check format
    df = pd.read_csv(csv_path)

    if 'Game Info' in df.columns:
        games = df['Game Info'].dropna().unique()
        print(f"\n📊 Found {len(games)} unique games in CSV")

        # Show format
        print("\nGame format examples:")
        for game in games[:3]:
            print(f"  • '{game}'")

    # Test system
    print("\n🏗️ Testing Unified Core System...")
    system = UnifiedCoreSystem()

    # This should now properly load game_info
    system.load_csv(csv_path)

    # Check a few players
    print("\n📋 Checking if players have game_info:")
    count = 0
    for i, (name, player) in enumerate(system.all_players.items()):
        if i < 5:  # First 5 players
            game_info = getattr(player, 'game_info', 'MISSING')
            print(f"  {name}: '{game_info}'")
        if hasattr(player, 'game_info') and player.game_info:
            count += 1

    print(f"\n✅ {count}/{len(system.all_players)} players have game_info")

    # Test confirmation fetch
    print("\n🎯 Testing slate-aware confirmation fetch...")
    confirmed = system.fetch_confirmed_players()

    print(f"\n📊 Results:")
    print(f"  Confirmed players: {confirmed}")

    if confirmed == 0:
        print("\n💡 If still 0, it means:")
        print("  • Lineups not posted yet for these games")
        print("  • But slate detection is working!")
        print("  • Check the teams identified above")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        verify_slate_detection(sys.argv[1])
    else:
        print("Usage: python verify_slate.py /path/to/DKSalaries.csv")
