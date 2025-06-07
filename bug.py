import requests
import time

# Test MLB API endpoints
urls = [
    "https://baseballsavant.mlb.com",
    "https://statsapi.mlb.com/api/v1/teams",
    "https://baseballsavant.mlb.com/player/660271"  # Ohtani
]

for url in urls:
    try:
        start = time.time()
        r = requests.get(url, timeout=10)
        print(f"✅ {url}: {r.status_code} in {time.time()-start:.2f}s")
        print(f"   Got {len(r.content):,} bytes")
    except Exception as e:
        print(f"❌ {url}: {e}")