#!/usr/bin/env python3
"""
DEBUG CONFIRMATION SYSTEMS
==========================
Find out why no games are being detected
"""

import requests
from datetime import datetime
from bs4 import BeautifulSoup
import json


def debug_mlb_api():
    """Debug MLB API to see what's happening"""
    print("\n🔍 DEBUGGING MLB API")
    print("=" * 60)

    # Try different date formats
    today = datetime.now().strftime('%Y-%m-%d')

    print(f"Today's date: {today}")
    print(f"Current time: {datetime.now().strftime('%H:%M:%S')}")

    # MLB API URL
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"

    print(f"\nTrying URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # Check dates
            dates = data.get('dates', [])
            print(f"\nDates in response: {len(dates)}")

            if dates:
                date_entry = dates[0]
                games = date_entry.get('games', [])
                print(f"Games found: {len(games)}")

                # Show game details
                for i, game in enumerate(games[:3]):  # First 3 games
                    print(f"\nGame {i + 1}:")
                    print(f"  Status: {game.get('status', {}).get('detailedState', 'Unknown')}")

                    # Teams
                    away = game.get('teams', {}).get('away', {}).get('team', {}).get('name', 'Unknown')
                    home = game.get('teams', {}).get('home', {}).get('team', {}).get('name', 'Unknown')
                    print(f"  {away} @ {home}")

                    # Game time
                    game_date = game.get('gameDate', '')
                    print(f"  Time: {game_date}")

                    # Check for lineups
                    if 'lineups' in game:
                        print("  ✅ Has lineups data")
                    else:
                        print("  ❌ No lineups data")

            else:
                print("❌ No dates in response")

            # Try with hydrate parameter
            print("\n\nTrying with hydrate parameter...")
            url2 = f"{url}&hydrate=lineups,probablePitcher"
            response2 = requests.get(url2, timeout=10)

            if response2.status_code == 200:
                data2 = response2.json()
                dates2 = data2.get('dates', [])
                if dates2:
                    games2 = dates2[0].get('games', [])
                    print(f"Games with hydrate: {len(games2)}")

                    # Check first game
                    if games2:
                        game = games2[0]
                        away_lineup = game.get('lineups', {}).get('awayPlayers', [])
                        home_lineup = game.get('lineups', {}).get('homePlayers', [])
                        print(f"Away lineup players: {len(away_lineup)}")
                        print(f"Home lineup players: {len(home_lineup)}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def debug_rotowire():
    """Debug Rotowire to see what's happening"""
    print("\n\n🔍 DEBUGGING ROTOWIRE")
    print("=" * 60)

    url = "https://www.rotowire.com/baseball/daily-lineups.php"

    print(f"URL: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        print(f"Response status: {response.status_code}")
        print(f"Response length: {len(response.text)} bytes")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Debug: Save HTML to file for inspection
            with open('rotowire_debug.html', 'w') as f:
                f.write(response.text)
            print("✅ Saved HTML to rotowire_debug.html for inspection")

            # Try different selectors
            selectors_to_try = [
                ('div', 'lineup__game'),
                ('div', 'lineup-card'),
                ('div', 'lineups-container'),
                ('div', 'game-box'),
                ('div', {'class': lambda x: x and 'lineup' in x}),
                ('div', {'class': lambda x: x and 'game' in x})
            ]

            for tag, selector in selectors_to_try:
                if isinstance(selector, dict):
                    elements = soup.find_all(tag, selector)
                else:
                    elements = soup.find_all(tag, class_=selector)

                if elements:
                    print(f"\n✅ Found {len(elements)} elements with {tag}.{selector}")
                    # Show first element
                    first = elements[0]
                    text = first.get_text(strip=True)[:100]
                    print(f"   Sample text: {text}...")

            # Look for any game-related text
            game_texts = soup.find_all(
                text=lambda t: t and any(word in t.lower() for word in ['game', 'lineup', 'pitcher', '@', 'vs']))
            print(f"\nFound {len(game_texts)} game-related text elements")

            if not game_texts:
                # Check if there's a "no games" message
                no_games = soup.find_all(text=lambda t: t and 'no games' in t.lower())
                if no_games:
                    print("⚠️  Found 'no games' message on page")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def check_dfs_slate_times():
    """Check if this is a late slate issue"""
    print("\n\n🕐 CHECKING SLATE TIMING")
    print("=" * 60)

    current_time = datetime.now()
    print(f"Current time: {current_time.strftime('%I:%M %p')}")
    print(f"Current date: {current_time.strftime('%A, %B %d, %Y')}")

    print("\n💡 Possible issues:")
    print("1. Late slate games might not have lineups posted yet")
    print("2. Some sites only post lineups 2-3 hours before first pitch")
    print("3. API might be filtering out late games")
    print("4. Could be using wrong timezone")

    print("\n📝 For DFS slates:")
    print("• Main slate: Usually has lineups by 4-5 PM ET")
    print("• Late slate: Lineups often not until 7-8 PM ET")
    print("• Night slate: Sometimes lineups very late")


def manual_lineup_entry():
    """Show how to manually enter known lineups"""
    print("\n\n💡 MANUAL LINEUP ENTRY")
    print("=" * 60)

    print("Since confirmations aren't working, you can:")
    print("\n1. Create a manual confirmation file:")

    manual_confirmations = {
        "teams": {
            "LAD": {
                "lineup": [
                    "Mookie Betts",
                    "Shohei Ohtani",
                    "Freddie Freeman",
                    "Will Smith",
                    "Max Muncy",
                    "Teoscar Hernandez",
                    "Chris Taylor",
                    "Miguel Rojas",
                    "James Outman"
                ],
                "pitcher": "Tyler Glasnow"
            },
            # Add more teams...
        }
    }

    print(json.dumps(manual_confirmations, indent=2))

    print("\n2. Or just use manual player selection in the GUI")
    print("3. Or wait until closer to game time for lineups")


def main():
    """Run all debug checks"""
    print("🔧 DEBUGGING CONFIRMATION SYSTEMS")
    print("=" * 70)

    # Debug MLB API
    debug_mlb_api()

    # Debug Rotowire
    debug_rotowire()

    # Check timing
    check_dfs_slate_times()

    # Show manual option
    manual_lineup_entry()

    print("\n\n📊 SUMMARY")
    print("=" * 70)
    print("Run this script to see what data is available")
    print("Check rotowire_debug.html to see the actual page")
    print("If it's a late slate, lineups might not be posted yet")


if __name__ == "__main__":
    main()