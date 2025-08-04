# test_2025_data.py
from datetime import datetime
from main_optimizer.real_data_enrichments import RealStatcastFetcher
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

print(f"Testing data fetch for current date: {datetime.now()}")
print("=" * 50)

fetcher = RealStatcastFetcher()

# Test more players with different profiles
players_to_test = [
    "Aaron Judge",
    "Shohei Ohtani",
    "Ronald Acuna Jr",  # Without ñ
    "Mookie Betts",
    "Jose Altuve",
    "Max Scherzer"  # Pitcher
]

for player in players_to_test:
    print(f"\nTesting {player}:")

    # Try different day ranges
    for days in [7, 14, 30]:
        stats = fetcher.get_recent_stats(player, days=days)
        games = stats.get('games_analyzed', 0)

        if games > 0:
            print(f"  Found {games} games in last {days} days")
            print(f"  Recent form: {stats.get('recent_form', 1.0):.3f}")

            if stats.get('batting_avg') is not None:
                print(f"  AVG: {stats.get('batting_avg'):.3f}")
                print(f"  Barrel%: {stats.get('barrel_rate', 0):.1f}%")
            elif stats.get('avg_velocity'):
                print(f"  Avg Velocity: {stats.get('avg_velocity'):.1f} mph")
                print(f"  Strike%: {stats.get('strike_rate', 0):.1f}%")
            break
    else:
        print(f"  No games found in last 30 days")