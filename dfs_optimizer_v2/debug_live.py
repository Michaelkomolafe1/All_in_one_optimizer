#!/usr/bin/env python3
"""
REAL LIVE DATA TEST
===================
Fetches actual MLB data, Vegas lines, weather, and ownership
"""

import sys
import os
import glob
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_pipeline_v2 import DFSPipeline


def find_latest_csv():
    """Find the most recent DraftKings CSV file"""
    # Search common locations
    search_paths = [
        "/home/michael/Desktop/*.csv",
        "/home/michael/Downloads/*.csv",
        "/home/michael/Desktop/All_in_one_optimizer/*.csv",
        "/home/michael/Desktop/All_in_one_optimizer/dfs_optimizer_v2/*.csv",
    ]

    all_csvs = []
    for pattern in search_paths:
        all_csvs.extend(glob.glob(pattern))

    if all_csvs:
        # Sort by modification time
        all_csvs.sort(key=os.path.getmtime, reverse=True)
        return all_csvs[0]
    return None


def test_real_data():
    """Test with REAL MLB data"""
    print("=" * 60)
    print("🔴 LIVE DATA TEST - REAL MLB DATA")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Initialize pipeline
    pipeline = DFSPipeline()

    # TEST 1: Load real CSV
    print("\n📁 TEST 1: Loading REAL DraftKings CSV...")
    csv_path = find_latest_csv()

    if csv_path:
        print(f"   Found CSV: {csv_path}")
        count, games = pipeline.load_csv(csv_path)
        print(f"✅ Loaded {count} real players from {games} games")

        # Show teams in slate
        teams = set()
        for p in pipeline.all_players:
            teams.add(p.team)
        print(f"   Teams in slate: {sorted(teams)}")
    else:
        print("❌ No CSV found! Please download a DraftKings CSV")
        print("   Download from: https://www.draftkings.com")
        return False

    # TEST 2: Fetch REAL MLB confirmations
    print("\n🔍 TEST 2: Fetching REAL MLB confirmations...")
    print("   Connecting to MLB Stats API...")

    confirmed = pipeline.fetch_confirmations()
    print(f"✅ {confirmed} players confirmed from MLB API")

    # Show confirmed players
    confirmed_players = [p for p in pipeline.all_players if p.confirmed]
    if confirmed_players:
        print("\n   Sample confirmed players:")
        for p in confirmed_players[:5]:
            order = f"#{p.batting_order}" if p.batting_order > 0 else "SP" if p.position == "P" else ""
            print(f"      {p.name} ({p.team}) {p.position} {order}")

    # TEST 3: Check data sources
    print("\n📊 TEST 3: Testing live data sources...")

    # Vegas Lines
    print("\n   🎰 Vegas Lines:")
    try:
        from vegas_lines import VegasLines
        vegas = VegasLines()
        lines = vegas.get_all_lines()
        if lines:
            print(f"      ✅ Connected! {len(lines)} teams with totals")
            for team, data in list(lines.items())[:3]:
                print(f"         {team}: {data.get('total', 0)} runs")
        else:
            print("      ⚠️ No lines available (may be too early)")
    except Exception as e:
        print(f"      ❌ Error: {e}")

    # Weather Data
    print("\n   🌤️ Weather Data:")
    try:
        from weather_integration import WeatherIntegration
        weather = WeatherIntegration()
        weather_data = weather.get_all_weather()
        if weather_data:
            print(f"      ✅ Connected! {len(weather_data)} games with weather")
            for game_id, data in list(weather_data.items())[:2]:
                print(f"         {game_id}: {data.get('temp', 0)}°F, Wind: {data.get('wind_speed', 0)}mph")
        else:
            print("      ⚠️ No weather data available")
    except Exception as e:
        print(f"      ❌ Not available: {e}")

    # Ownership Projections
    print("\n   📈 Ownership Projections:")
    try:
        from ownership_calculator import OwnershipCalculator
        ownership = OwnershipCalculator()
        # Test with a real player
        if pipeline.all_players:
            test_player = pipeline.all_players[0]
            own_pct = ownership.get_ownership(
                test_player.name,
                test_player.position,
                test_player.salary,
                test_player.team
            )
            print(f"      ✅ Connected! Sample: {test_player.name} = {own_pct:.1f}%")
        else:
            print("      ⚠️ No players to test")
    except Exception as e:
        print(f"      ❌ Not available: {e}")

    # Statcast Data
    print("\n   ⚾ Statcast Data:")
    try:
        from simple_statcast_fetcher import SimpleStatcastFetcher
        statcast = SimpleStatcastFetcher()
        # Test with a real player
        if pipeline.all_players:
            # Find a batter
            batters = [p for p in pipeline.all_players if p.position != 'P']
            if batters:
                test_batter = batters[0]
                stats = statcast.get_batter_stats(test_batter.name)
                if stats:
                    print(f"      ✅ Connected! {test_batter.name}:")
                    print(f"         Barrel%: {stats.get('barrel%', 0):.1f}")
                    print(f"         xwOBA: {stats.get('xwoba', 0):.3f}")
                else:
                    print("      ⚠️ No stats found (player may not have recent data)")
        else:
            print("      ⚠️ No players to test")
    except Exception as e:
        print(f"      ❌ Not available: {e}")

    # TEST 4: Build and enrich pool
    print("\n🏊 TEST 4: Building player pools...")

    # Try confirmed only first
    confirmed_count = pipeline.build_player_pool(confirmed_only=True)
    print(f"   Confirmed only: {confirmed_count} players")

    # If not enough confirmed, use all
    if confirmed_count < 50:
        print(f"   ⚠️ Not enough confirmed players, using full pool")
        all_count = pipeline.build_player_pool(confirmed_only=False)
        print(f"   Full pool: {all_count} players")

    # Apply strategy and enrich
    print("\n🎯 TEST 5: Enriching with real data...")
    strategy = pipeline.apply_strategy('gpp')
    stats = pipeline.enrich_players(strategy, 'gpp')

    print(f"✅ Enrichment complete:")
    for key, value in stats.items():
        print(f"   {key}: {value} players enriched")

    # Check actual enrichment
    enriched_sample = []
    for p in pipeline.player_pool[:5]:
        enriched_data = []
        if hasattr(p, 'batting_order') and p.batting_order > 0:
            enriched_data.append(f"#{p.batting_order}")
        if hasattr(p, 'barrel_rate') and p.barrel_rate > 0:
            enriched_data.append(f"Barrel:{p.barrel_rate:.1f}%")
        if hasattr(p, 'ownership') and p.ownership != 15.0:
            enriched_data.append(f"Own:{p.ownership:.1f}%")

        if enriched_data:
            print(f"   {p.name}: {', '.join(enriched_data)}")

    # TEST 6: Generate lineups with real data
    print("\n⚙️ TEST 6: Generating lineups with REAL data...")

    for contest in ['cash', 'gpp']:
        print(f"\n   {contest.upper()} Contest:")

        # Make sure we have enough players
        if len(pipeline.player_pool) < 10:
            print(f"      ❌ Not enough players in pool ({len(pipeline.player_pool)})")
            continue

        lineups = pipeline.optimize_lineups(contest, 1)

        if lineups and len(lineups) > 0:
            lineup = lineups[0]
            print(f"      ✅ Generated lineup!")
            print(f"      Salary: ${lineup['salary']:,} / $50,000")
            print(f"      Projection: {lineup['projection']:.1f} points")

            # Show the actual lineup
            print(f"\n      Lineup:")
            for p in lineup['players']:
                conf = "✓" if p.confirmed else ""
                print(f"         {p.position}: {p.name} ({p.team}) ${p.salary:,} {conf}")

            # Show stack info
            from collections import Counter
            teams = Counter(p.team for p in lineup['players'])
            if teams:
                max_team = max(teams, key=teams.get)
                print(f"\n      Stack: {teams[max_team]} players from {max_team}")
        else:
            print(f"      ❌ Failed to generate lineup")

            # Debug why
            from collections import defaultdict
            pos_counts = defaultdict(int)
            for p in pipeline.player_pool:
                if p.position in ['P', 'SP', 'RP']:
                    pos_counts['P'] += 1
                else:
                    pos_counts[p.position] += 1

            print(f"      Debug - Available positions:")
            for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
                need = 2 if pos == 'P' else 3 if pos == 'OF' else 1
                have = pos_counts[pos]
                status = "✓" if have >= need else "✗"
                print(f"         {pos}: {have}/{need} {status}")

    print("\n" + "=" * 60)
    print("LIVE DATA TEST COMPLETE")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = test_real_data()
    if not success:
        print("\n⚠️ Please download a DraftKings CSV to test with real data")
        print("1. Go to https://www.draftkings.com")
        print("2. Navigate to an MLB contest")
        print("3. Click 'Download Players List'")
        print("4. Save the CSV and run this test again")