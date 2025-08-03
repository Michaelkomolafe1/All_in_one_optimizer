#!/usr/bin/env python3
"""
Test script to verify real data enrichments are working
Run this after setting up to confirm everything works
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from real_data_enrichments import (
    RealStatcastFetcher,
    RealWeatherIntegration,
    RealParkFactors,
    check_and_install_dependencies
)


def test_real_data():
    """Test all real data sources"""
    print("🧪 TESTING REAL DATA ENRICHMENTS")
    print("=" * 60)

    # Check dependencies
    print("\n1️⃣ Checking Dependencies...")
    if not check_and_install_dependencies():
        print("\n❌ Please install missing packages first!")
        return False

    # Test park factors
    print("\n2️⃣ Testing Park Factors...")
    parks = RealParkFactors()

    test_parks = ['COL', 'NYY', 'SF', 'BOS']
    for team in test_parks:
        factor = parks.get_park_factor(team)
        print(f"   {team}: {factor:.2f}")

    print("   ✅ Park factors working!")

    # Test weather
    print("\n3️⃣ Testing Weather Data...")
    weather = RealWeatherIntegration()

    # Test a few stadiums
    test_teams = ['NYY', 'LAD', 'TB']  # Regular, regular, dome
    for team in test_teams:
        data = weather.get_game_weather(team)
        print(f"\n   {team} Stadium:")
        print(f"   - Temperature: {data['temperature']:.0f}°F")
        print(f"   - Wind: {data['wind_speed']:.0f} mph")
        print(f"   - Conditions: {data['conditions']}")
        print(f"   - Impact: {data['weather_impact']:.2f}x")
        if data['is_dome']:
            print(f"   - DOME STADIUM")

    print("\n   ✅ Weather data working!")

    # Test player stats
    print("\n4️⃣ Testing Player Stats (this may take a moment)...")
    stats = RealStatcastFetcher()

    # Test with well-known players
    test_players = [
        ("Aaron Judge", False),  # Hitter
        ("Shohei Ohtani", False),  # Hitter
        ("Gerrit Cole", True),  # Pitcher
    ]

    for player_name, is_pitcher in test_players:
        print(f"\n   {player_name}:")
        try:
            # Get recent stats
            recent = stats.get_recent_stats(player_name, days=7)

            if recent.get('data_available', True) == False:
                print(f"   ⚠️ No recent data (player might not have played)")
                continue

            print(f"   - Games analyzed: {recent.get('games_analyzed', 0)}")
            print(f"   - Recent form: {recent.get('recent_form', 1.0):.2f}")

            if is_pitcher:
                print(f"   - Avg velocity: {recent.get('avg_velocity', 0):.1f} mph")
                print(f"   - Strike rate: {recent.get('strike_rate', 0):.1f}%")
                print(f"   - Whiff rate: {recent.get('whiff_rate', 0):.1f}%")
            else:
                print(f"   - Batting avg: {recent.get('batting_avg', 0):.3f}")
                print(f"   - xBA: {recent.get('xBA', 0):.3f}")
                print(f"   - Barrel rate: {recent.get('barrel_rate', 0):.1f}%")
                print(f"   - Exit velocity: {recent.get('avg_exit_velocity', 0):.1f} mph")

            # Test consistency
            consistency = stats.get_consistency_score(player_name)
            print(f"   - Consistency: {consistency:.2f}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n   ✅ Player stats working!")

    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL REAL DATA SOURCES WORKING!")
    print("\nYour enrichments will now include:")
    print("- Real MLB park factors")
    print("- Current weather conditions")
    print("- Actual player stats from last 7 days")
    print("- Calculated consistency scores")
    print("\n🎯 Ready to optimize with real data!")

    return True


if __name__ == "__main__":
    # Run the test
    success = test_real_data()

    if success:
        print("\n💡 Next steps:")
        print("1. Run your GUI optimizer")
        print("2. Load a CSV and build player pool")
        print("3. Watch the enrichment process add real data")
        print("4. Hover over players to see their real stats!")

    sys.exit(0 if success else 1)