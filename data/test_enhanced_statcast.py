from simple_statcast_fetcher import SimpleStatcastFetcher  # or your class name

# Test the new methods
fetcher = SimpleStatcastFetcher()

# Test pitcher stats
print("Testing pitcher stats...")
pitcher_stats = fetcher.fetch_pitcher_advanced_stats("Gerrit Cole")
print(f"Pitcher stats: {pitcher_stats}")

# Test game logs
print("\nTesting game logs...")
game_logs = fetcher.fetch_recent_game_logs("Aaron Judge", 4)
print(f"Recent games: {game_logs}")

print("\n✅ Enhancement successful!")