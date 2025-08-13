#!/usr/bin/env python3
"""
DATA SOURCE CHECKER
===================
Checks which data sources are actually available and working
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_all_data_sources():
    """Check availability of all data sources"""
    print("=" * 60)
    print("🔍 DATA SOURCE AVAILABILITY CHECK")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    results = {}

    # 1. MLB Confirmations
    print("\n1️⃣ MLB CONFIRMATIONS (smart_confirmation.py)")
    try:
        from smart_confirmation import UniversalSmartConfirmation
        system = UniversalSmartConfirmation(verbose=False)
        lineup_count, pitcher_count = system.get_all_confirmations()
        print(f"   ✅ WORKING - {lineup_count} players, {pitcher_count} pitchers")
        print(f"   Teams with lineups: {list(system.confirmed_lineups.keys())[:5]}")
        results['confirmations'] = True
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results['confirmations'] = False

    # 2. Vegas Lines
    print("\n2️⃣ VEGAS LINES (vegas_lines.py)")
    try:
        from vegas_lines import VegasLines
        vegas = VegasLines()
        lines = vegas.get_all_lines()
        if lines:
            print(f"   ✅ WORKING - {len(lines)} teams with totals")
            # Show sample
            for team, data in list(lines.items())[:3]:
                total = data.get('total', 'N/A')
                print(f"      {team}: O/U {total}")
        else:
            print("   ⚠️ No data returned (may be too early)")
        results['vegas'] = True
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results['vegas'] = False

    # 3. Weather Integration
    print("\n3️⃣ WEATHER DATA (weather_integration.py)")
    try:
        from weather_integration import WeatherIntegration
        weather = WeatherIntegration()
        weather_data = weather.get_all_weather()
        if weather_data:
            print(f"   ✅ WORKING - {len(weather_data)} games")
            for game, data in list(weather_data.items())[:2]:
                print(f"      {game}: {data.get('temp')}°F, Wind: {data.get('wind_speed')}mph")
        else:
            print("   ⚠️ No weather data available")
        results['weather'] = True
    except ImportError:
        print("   ❌ Module not found - weather_integration.py doesn't exist")
        results['weather'] = False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results['weather'] = False

    # 4. Ownership Calculator
    print("\n4️⃣ OWNERSHIP PROJECTIONS (ownership_calculator.py)")
    try:
        from ownership_calculator import OwnershipCalculator
        calc = OwnershipCalculator()
        # Test with fake player
        test_own = calc.get_ownership("Mike Trout", "OF", 6000, "LAA")
        print(f"   ✅ WORKING - Test ownership: {test_own:.1f}%")
        results['ownership'] = True
    except ImportError:
        print("   ❌ Module not found - ownership_calculator.py doesn't exist")
        results['ownership'] = False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results['ownership'] = False

    # 5. Statcast Data
    print("\n5️⃣ STATCAST DATA (simple_statcast_fetcher.py)")
    try:
        from simple_statcast_fetcher import SimpleStatcastFetcher
        fetcher = SimpleStatcastFetcher()
        # Test with known player
        stats = fetcher.get_batter_stats("Mike Trout")
        if stats:
            print(f"   ✅ WORKING - Mike Trout stats:")
            print(f"      Barrel%: {stats.get('barrel%', 0):.1f}")
            print(f"      xwOBA: {stats.get('xwoba', 0):.3f}")
        else:
            print("   ⚠️ No stats returned (API may be down)")
        results['statcast'] = True
    except ImportError:
        print("   ❌ Module not found - simple_statcast_fetcher.py doesn't exist")
        results['statcast'] = False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results['statcast'] = False

    # 6. Check for other expected files
    print("\n6️⃣ OTHER EXPECTED FILES")
    expected_files = [
        'strategies_v2.py',
        'optimizer_v2.py',
        'data_pipeline_v2.py',
        'gui_v2.py'
    ]

    for file in expected_files:
        if os.path.exists(file):
            print(f"   ✅ {file} exists")
        else:
            print(f"   ❌ {file} NOT FOUND")

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    working = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\n✅ Working: {working}/{total} data sources")
    print(f"❌ Not working: {total - working}/{total} data sources")

    if results['confirmations']:
        print("\n✅ MLB Confirmations are working - you can get real lineups!")
    else:
        print("\n❌ MLB Confirmations not working - check internet connection")

    if not results['weather']:
        print("\n💡 Weather module missing - not critical for basic operation")

    if not results['ownership']:
        print("\n💡 Ownership module missing - using default 15% for all players")

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)

    if working < total:
        print("\nTo get missing data sources working:")

        if not results['weather']:
            print("\n1. Weather: Create weather_integration.py or ignore (not critical)")

        if not results['ownership']:
            print("\n2. Ownership: Create ownership_calculator.py with basic projections")

        if not results['statcast']:
            print("\n3. Statcast: Check simple_statcast_fetcher.py exists and API is up")
    else:
        print("\n🎉 All data sources are working!")

    return results


if __name__ == "__main__":
    results = check_all_data_sources()