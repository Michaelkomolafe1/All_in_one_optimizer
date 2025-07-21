#!/usr/bin/env python3
"""
QUICK CHECK - What Games Are Actually Available?
================================================
"""

import requests
from datetime import datetime
import pandas as pd
from pathlib import Path


def quick_check():
    """Quick check of what's happening"""
    print("\n🔍 QUICK GAME CHECK")
    print("=" * 60)

    # Current time
    now = datetime.now()
    print(f"Current time: {now.strftime('%I:%M %p ET')}")
    print(f"Date: {now.strftime('%A, %B %d, %Y')}")

    # Check your CSV for game info
    print("\n📄 CHECKING YOUR CSV...")
    csv_files = list(Path('.').glob('*.csv'))

    if csv_files:
        df = pd.read_csv(csv_files[0])

        # Look at Game Info column
        if 'Game Info' in df.columns:
            unique_games = df['Game Info'].dropna().unique()
            print(f"\nGames in your CSV: {len(unique_games)}")

            for game in unique_games[:5]:
                print(f"  • {game}")

            # Extract game times
            print("\n⏰ Game times:")
            for game in unique_games:
                if '@' in game and 'ET' in game:
                    parts = game.split()
                    if len(parts) >= 2:
                        time = parts[1]
                        print(f"  • {parts[0]} at {time}")

    # Quick MLB API check
    print("\n🌐 MLB API CHECK...")
    today = now.strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"

    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            dates = data.get('dates', [])
            if dates:
                games = dates[0].get('games', [])
                print(f"MLB API shows: {len(games)} games")

                for g in games[:3]:
                    status = g.get('status', {}).get('detailedState', 'Unknown')
                    print(f"  • Game status: {status}")

    except:
        print("  ❌ MLB API timeout/error")

    print("\n💡 WHAT THIS MEANS:")
    if "07:" in str(unique_games) or "08:" in str(unique_games) or "09:" in str(unique_games) or "10:" in str(
            unique_games):
        print("• You have evening games (7-10 PM starts)")
        print("• Lineups often not posted until 1-2 hours before")
        print("• This is NORMAL for evening slates")

    print("\n✅ SOLUTION: Use manual mode for now!")
    print("The system works perfectly with manual selections")


if __name__ == "__main__":
    quick_check()

    print("\n" + "=" * 60)
    print("🎯 RUN THIS TO USE YOUR SYSTEM NOW:")
    print("python force_manual_mode.py")