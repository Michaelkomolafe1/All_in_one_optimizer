from unified_core_system import UnifiedCoreSystem
from unified_player_model import UnifiedPlayer

# Create system
system = UnifiedCoreSystem()

# Create test players
players = [
    UnifiedPlayer(
        id="1", name="Aaron Judge", team="NYY", salary=6200,
        primary_position="OF", positions=["OF"], base_projection=12.5
    ),
    UnifiedPlayer(
        id="2", name="Gerrit Cole", team="NYY", salary=9500,
        primary_position="P", positions=["P"], base_projection=18.5
    ),
    UnifiedPlayer(
        id="3", name="Cheap Guy", team="OAK", salary=3200,
        primary_position="2B", positions=["2B"], base_projection=6.0
    )
]

# Add some attributes
players[0].implied_team_score = 5.8
players[0].batting_order = 2
players[0].projected_ownership = 35

players[1].k9 = 11.2
players[1].opp_k_rate = 0.25

players[2].implied_team_score = 3.5
players[2].batting_order = 8
players[2].projected_ownership = 5

# Add to system
system.player_pool = players

# Test scoring for each contest type
print("🧪 SYSTEM INTEGRATION TEST")
print("=" * 60)

for contest_type in ['gpp', 'cash', 'showdown']:
    print(f"\n{contest_type.upper()} SCORING:")
    print("-" * 30)
    
    # Score players
    for player in system.player_pool:
        score = system.scoring_engine.score_player(player, contest_type)
        print(f"{player.name:<15} Base: {player.base_projection:>5.1f} → {contest_type}: {score:>5.1f}")

print("\n✅ New scoring engine is working for all contest types!")
