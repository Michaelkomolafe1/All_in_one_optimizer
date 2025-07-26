from simple_statcast_fetcher import SimpleStatcastFetcher
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

fetcher = SimpleStatcastFetcher()

# Test different pitcher names
pitchers = [
    "Gerrit Cole",
    "Shohei Ohtani",
    "Spencer Strider", 
    "Max Scherzer",
    "Jacob deGrom"
]

print("🔍 TESTING PITCHER STATS FETCHING")
print("=" * 60)

for pitcher_name in pitchers:
    print(f"\nTesting: {pitcher_name}")
    
    # First check if we can get player ID
    player_id = fetcher._get_player_id(pitcher_name, "pitcher")
    print(f"  Player ID: {player_id}")
    
    if player_id:
        # Try the API directly
        import requests
        from datetime import datetime
        
        season = datetime.now().year
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&season={season}&group=pitching"
        print(f"  API URL: {url}")
        
        try:
            response = requests.get(url, timeout=5)
            print(f"  Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('stats') and data['stats']:
                    print(f"  Stats found: Yes")
                    if data['stats'][0].get('splits'):
                        print(f"  Splits: {len(data['stats'][0]['splits'])}")
                    else:
                        print(f"  No splits found")
                else:
                    print(f"  No stats in response")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    # Now try the method
    stats = fetcher.fetch_pitcher_advanced_stats(pitcher_name)
    if stats:
        print(f"  ✅ Stats retrieved: ERA={stats['era']}, K/9={stats['k9']}")
    else:
        print(f"  ❌ No stats returned")

print("\n" + "=" * 60)
print("💡 If all returned None, it might be:")
print("  1. Off-season (no 2025 stats yet)")
print("  2. Player name mismatch")
print("  3. API issue")
