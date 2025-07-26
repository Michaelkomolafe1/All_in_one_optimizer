from enhanced_scoring_engine import EnhancedScoringEngine
from unified_player_model import UnifiedPlayer

# Create test player
player = UnifiedPlayer(
    id="test",
    name="Aaron Judge",
    team="NYY",
    salary=6200,
    primary_position="OF",
    positions=["OF"],
    base_projection=12.5
)

# Add some test attributes
player.implied_team_score = 5.8
player.batting_order = 2
player.projected_ownership = 35
player.barrel_rate = 15.2
player.recent_form_score = 18

# Test scoring
engine = EnhancedScoringEngine()

print("🧪 SCORING ENGINE TEST")
print("=" * 50)
print(f"Player: {player.name}")
print(f"Base Projection: {player.base_projection}")
print(f"\nAttributes:")
print(f"  Team Total: {player.implied_team_score}")
print(f"  Batting Order: {player.batting_order}")
print(f"  Ownership: {player.projected_ownership}%")
print(f"\nScores:")
print(f"  GPP Score: {engine.score_player_gpp(player):.2f}")
print(f"  Cash Score: {engine.score_player_cash(player):.2f}")
print(f"\nBreakdown:")
print(engine.get_scoring_summary(player, 'gpp'))
