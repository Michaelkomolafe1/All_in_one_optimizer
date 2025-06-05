#!/usr/bin/env python3
"""
API VERIFICATION SCRIPT
======================
Tests all MLB API endpoints to ensure they're working
"""

import requests
import json
from datetime import datetime


def test_mlb_api():
    """Test MLB Stats API endpoints"""
    print("🔍 TESTING MLB STATS API")
    print("=" * 60)

    # Test 1: Basic schedule endpoint
    today = datetime.now().strftime('%Y-%m-%d')

    print(f"\n1️⃣ Testing basic schedule for {today}...")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"

    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            games = sum(len(date.get('games', [])) for date in data.get('dates', []))
            print(f"   ✅ Success! Found {games} games")
        else:
            print(f"   ❌ Failed with status {response.status_code}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 2: Schedule with lineups
    print(f"\n2️⃣ Testing schedule with lineups...")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=lineups,probablePitcher"

    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # Check for lineups and pitchers
            lineups_found = 0
            pitchers_found = 0

            for date in data.get('dates', []):
                for game in date.get('games', []):
                    if 'lineups' in game:
                        lineups_found += 1
                    if 'probablePitchers' in game:
                        pitchers_found += 1

            print(f"   ✅ Found {lineups_found} games with lineups")
            print(f"   ✅ Found {pitchers_found} games with probable pitchers")

            # Show sample game data
            if data.get('dates') and data['dates'][0].get('games'):
                game = data['dates'][0]['games'][0]
                away = game.get('teams', {}).get('away', {}).get('team', {}).get('name', 'Unknown')
                home = game.get('teams', {}).get('home', {}).get('team', {}).get('name', 'Unknown')
                print(f"\n   Sample game: {away} @ {home}")

                # Check for pitcher info
                if 'probablePitchers' in game:
                    if 'away' in game['probablePitchers']:
                        away_pitcher = game['probablePitchers']['away'].get('fullName', 'TBD')
                        print(f"   Away pitcher: {away_pitcher}")
                    if 'home' in game['probablePitchers']:
                        home_pitcher = game['probablePitchers']['home'].get('fullName', 'TBD')
                        print(f"   Home pitcher: {home_pitcher}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Alternative endpoint for live data
    print(f"\n3️⃣ Testing live scoreboard endpoint...")
    url = "https://statsapi.mlb.com/api/v1.1/game/scoreboard"

    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print(f"   ✅ Live scoreboard endpoint working!")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_alternative_sources():
    """Test alternative data sources"""
    print(f"\n\n🔍 TESTING ALTERNATIVE SOURCES")
    print("=" * 60)

    # Test ESPN API (unofficial)
    print(f"\n4️⃣ Testing ESPN endpoint...")
    url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"

    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            events = len(data.get('events', []))
            print(f"   ✅ ESPN API working! Found {events} games")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def check_lineup_availability():
    """Check when lineups are typically available"""
    print(f"\n\n📅 LINEUP AVAILABILITY INFO")
    print("=" * 60)

    current_time = datetime.now()
    print(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n⏰ Typical lineup posting times:")
    print("   • 1:00 PM games: Lineups by 12:00 PM")
    print("   • 3:00 PM games: Lineups by 2:00 PM")
    print("   • 7:00 PM games: Lineups by 6:00 PM")
    print("   • 10:00 PM games: Lineups by 9:00 PM")
    print(f"\n💡 Note: Lineups are usually posted 30-60 minutes before first pitch")


if __name__ == "__main__":
    print("🧪 MLB API VERIFICATION TOOL")
    print("=" * 60)

    # Run all tests
    test_mlb_api()
    test_alternative_sources()
    check_lineup_availability()

    print(f"\n\n✅ VERIFICATION COMPLETE!")
    print("\nIf lineups aren't showing, it's likely because:")
    print("1. Games haven't started yet (lineups post ~1 hour before)")
    print("2. It's an off day with no games")
    print("3. The specific teams in your CSV aren't playing today")