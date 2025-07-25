# Save this as data/test_combined_pitcher_stats.py
from simple_statcast_fetcher import SimpleStatcastFetcher

fetcher = SimpleStatcastFetcher()

# Test with a known good pitcher
pitcher = "Shohei Ohtani"

print(f"🔍 Testing Combined Pitcher Stats for {pitcher}")
print("=" * 60)

# Get the enhanced stats
stats = fetcher.fetch_pitcher_advanced_stats(pitcher)

if stats:
    print("\n📊 Traditional Stats (MLB API):")
    print(f"  ERA: {stats.get('era', 'N/A')}")
    print(f"  K/9: {stats.get('k9', 'N/A')}")
    print(f"  WHIP: {stats.get('whip', 'N/A')}")
    print(f"  K-Rate: {stats.get('k_rate', 'N/A'):.3f}")

    print("\n📈 Advanced Stats (Baseball Savant):")
    print(f"  xERA: {stats.get('xera', 'N/A')}")
    print(f"  Whiff Rate: {stats.get('whiff_rate', 'N/A')}%")
    print(f"  Barrel Rate Against: {stats.get('barrel_rate_against', 'N/A')}%")
    print(f"  Hard Hit Rate Against: {stats.get('hard_hit_rate_against', 'N/A')}%")

    print("\n✅ Combined data retrieved successfully!")
else:
    print("❌ No stats found")

# Also test that hitter data still works
print("\n" + "=" * 60)
print("📊 Testing Hitter Data (Baseball Savant)")
hitter_data = fetcher.fetch_player_data("Aaron Judge", "B")
if hitter_data is not None:
    print("✅ Hitter data still working")
    print(f"  Sample stats: BA={hitter_data.get('ba', 'N/A')}, Barrel%={hitter_data.get('barrel_batted_rate', 'N/A')}")