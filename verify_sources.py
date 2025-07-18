#!/usr/bin/env python3
"""
Test various lineup sources to see which ones actually have lineups posted
Run this to verify which sources work before implementing
"""

import requests
from datetime import datetime
from bs4 import BeautifulSoup
import json
import re


def test_source(name, test_func):
    """Test a source and report results"""
    print(f"\n{'=' * 60}")
    print(f"🔍 Testing: {name}")
    print('=' * 60)

    try:
        result = test_func()
        if result['success']:
            print(f"✅ SUCCESS: {result['message']}")
            if result.get('sample'):
                print(f"📋 Sample data: {result['sample']}")
        else:
            print(f"❌ FAILED: {result['message']}")
        return result
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {'success': False, 'message': str(e)}


def test_mlb_api():
    """Test MLB API for lineups"""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=lineups,probablePitcher"

    response = requests.get(url, timeout=10)
    data = response.json()

    lineup_count = 0
    pitcher_count = 0
    sample_lineups = []

    for date_entry in data.get('dates', []):
        for game in date_entry.get('games', []):
            for side in ['home', 'away']:
                team_data = game.get('teams', {}).get(side, {})

                # Check lineups
                lineups = team_data.get('lineups', [])
                if lineups:
                    lineup_count += len(lineups)
                    if len(sample_lineups) < 2:
                        team = team_data.get('team', {}).get('abbreviation', 'UNK')
                        sample_lineups.append(f"{team}: {len(lineups)} players")

                # Check pitcher
                pitcher = team_data.get('probablePitcher')
                if pitcher:
                    pitcher_count += 1

    return {
        'success': lineup_count > 0 or pitcher_count > 0,
        'message': f"Found {lineup_count} lineup spots, {pitcher_count} pitchers",
        'sample': sample_lineups[:2] if sample_lineups else None
    }


def test_rotowire():
    """Test RotoWire lineups"""
    url = "https://www.rotowire.com/baseball/daily-lineups.php"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        return {'success': False, 'message': f"HTTP {response.status_code}"}

    # Check for lineup indicators
    text = response.text.lower()
    has_lineups = 'lineup' in text and ('confirmed' in text or 'expected' in text)

    # Try to find specific lineup data
    soup = BeautifulSoup(response.text, 'html.parser')
    lineup_divs = soup.find_all('div', class_=re.compile('lineup|roster', re.I))

    return {
        'success': has_lineups and len(lineup_divs) > 0,
        'message': f"Found {len(lineup_divs)} lineup sections",
        'sample': f"Page has lineup content: {has_lineups}"
    }


def test_baseball_reference():
    """Test Baseball Reference for today's games"""
    today = datetime.now()
    url = f"https://www.baseball-reference.com/previews/{today.year}/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        return {'success': False, 'message': f"HTTP {response.status_code}"}

    soup = BeautifulSoup(response.text, 'html.parser')
    game_links = soup.find_all('a', href=re.compile(f'/previews/{today.year}/'))

    return {
        'success': len(game_links) > 0,
        'message': f"Found {len(game_links)} game preview links",
        'sample': f"Games scheduled today"
    }


def test_dailybaseballdata():
    """Test DailyBaseballData lineups"""
    url = "https://dailybaseballdata.com/cgi-bin/dailyhit.pl"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        return {'success': False, 'message': f"HTTP {response.status_code}"}

    # Check for lineup data
    text = response.text
    has_lineups = 'Batting Order' in text or 'lineup' in text.lower()

    # Count player entries (they usually have a specific format)
    player_pattern = r'\d+\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+'
    players_found = len(re.findall(player_pattern, text))

    return {
        'success': has_lineups and players_found > 0,
        'message': f"Found {players_found} potential player entries",
        'sample': f"Has lineup content: {has_lineups}"
    }


def test_fantasylabs():
    """Test FantasyLabs MLB lineups"""
    url = "https://www.fantasylabs.com/mlb/lineups/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        return {'success': False, 'message': f"HTTP {response.status_code}"}

    # Check for lineup indicators
    has_content = 'lineup' in response.text.lower()

    return {
        'success': has_content,
        'message': "Page accessible, may require login for full data",
        'sample': f"Has lineup content: {has_content}"
    }


def test_numberfire():
    """Test NumberFire daily lineups"""
    url = "https://www.numberfire.com/mlb/daily-fantasy/daily-baseball-lineups"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return {'success': False, 'message': f"HTTP {response.status_code}"}

        has_lineups = 'lineup' in response.text.lower()

        return {
            'success': has_lineups,
            'message': "Page accessible",
            'sample': f"Has lineup content: {has_lineups}"
        }
    except:
        return {'success': False, 'message': "Site may be down or blocked"}


def test_espn():
    """Test ESPN for game data"""
    today = datetime.now().strftime('%Y%m%d')
    url = f"https://www.espn.com/mlb/schedule/_/date/{today}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        return {'success': False, 'message': f"HTTP {response.status_code}"}

    # ESPN usually has game data but not always lineups
    has_games = 'game' in response.text.lower()

    return {
        'success': has_games,
        'message': "Has game data, lineups may not be available",
        'sample': "ESPN schedule page accessible"
    }


def main():
    """Test all sources"""
    print("🏥 LINEUP SOURCE VERIFICATION")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nTesting available lineup sources...")

    sources = [
        ("MLB Official API", test_mlb_api),
        ("RotoWire", test_rotowire),
        ("Baseball Reference", test_baseball_reference),
        ("DailyBaseballData", test_dailybaseballdata),
        ("FantasyLabs", test_fantasylabs),
        ("NumberFire", test_numberfire),
        ("ESPN", test_espn)
    ]

    results = []
    for name, test_func in sources:
        result = test_source(name, test_func)
        results.append((name, result))

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY OF WORKING SOURCES")
    print("=" * 60)

    working_sources = [(name, res) for name, res in results if res['success']]

    if working_sources:
        print("\n✅ WORKING SOURCES:")
        for name, res in working_sources:
            print(f"   • {name}: {res['message']}")
    else:
        print("\n❌ No sources with lineups currently available")

    print("\n💡 RECOMMENDATIONS:")
    if any('pitcher' in str(res.get('message', '')).lower() for _, res in results):
        print("   • Some sources have pitchers but no position player lineups")
        print("   • Lineups typically post 1-2 hours before game time")
        print("   • Try again closer to game time")

    # Check if we at least have pitchers from MLB API
    mlb_result = next((res for name, res in results if name == "MLB Official API"), None)
    if mlb_result and 'pitcher' in mlb_result.get('message', ''):
        print("\n🎯 MLB API has starting pitchers - you can use those for now")
        print("   Add manual position player confirmations as lineups post")


if __name__ == "__main__":
    main()