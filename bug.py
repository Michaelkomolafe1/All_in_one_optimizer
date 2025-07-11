# test_statcast.py
from simple_statcast_fetcher import FastStatcastFetcher

# Test with a known player
fetcher = FastStatcastFetcher()

# Test a few confirmed players from your lineup
test_players = [
    ("Spencer Strider", "P"),
    ("Ketel Marte", "2B"),
    ("Corey Seager", "SS")
]

for name, pos in test_players:
    print(f"\nTesting {name} ({pos}):")

    # Try to get player ID
    player_id = fetcher.get_player_id(name)
    print(f"  Player ID: {player_id}")

    # Try to fetch data
    try:
        data = fetcher.fetch_player_data(name, pos)
        if data:
            print(f"  Data source: {data.get('data_source', 'Unknown')}")
            print(f"  xwOBA: {data.get('xwOBA', 'N/A')}")
        else:
            print("  No data returned")
    except Exception as e:
        print(f"  Error: {e}")