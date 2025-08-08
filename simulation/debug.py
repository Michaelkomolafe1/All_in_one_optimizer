cd /home/michael/Desktop/All_in_one_optimizer

# Debug what optimize_lineup actually returns
python << 'EOF'
import sys
sys.path.insert(0, '.')

from main_optimizer.unified_core_system_updated import UnifiedCoreSystem
from main_optimizer.unified_player_model import UnifiedPlayer

# Create simple test players
players = []
positions = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF'] * 5
teams = ['TM1', 'TM2'] * 25

for i in range(50):
    player = UnifiedPlayer(
        name=f"Player{i}",
        position=positions[i % len(positions)],
        team=teams[i % len(teams)],
        salary=3000 + (i * 100),
        opponent='OPP',
        player_id=f"P{i}",
        base_projection=8.0 + (i * 0.2)
    )
    player.projection = player.base_projection
    player.primary_position = player.position
    players.append(player)

system = UnifiedCoreSystem()
system.player_pool = players

print("🔍 Testing optimize_lineup return type...")

# Call optimize_lineup
result = system.optimize_lineup(
    strategy='cash',
    contest_type='cash'
)

print(f"\n📊 Result type: {type(result)}")
print(f"   Result length: {len(result) if hasattr(result, '__len__') else 'N/A'}")

if isinstance(result, list):
    print(f"   First item type: {type(result[0]) if result else 'Empty'}")
    if result and hasattr(result[0], 'name'):
        print(f"   First player: {result[0].name}")
        print(f"   Total players: {len(result)}")
    elif result and isinstance(result[0], dict):
        print(f"   First item keys: {result[0].keys()}")
    elif result and isinstance(result[0], list):
        print(f"   Nested list length: {len(result[0])}")
        if result[0] and hasattr(result[0][0], 'name'):
            print(f"   First player in nested: {result[0][0].name}")
elif isinstance(result, dict):
    print(f"   Dict keys: {result.keys()}")
    if 'players' in result:
        print(f"   Players count: {len(result['players'])}")

print("\n✅ Now we know the format!")
EOF
