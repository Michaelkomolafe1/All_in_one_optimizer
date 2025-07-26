from enhanced_scoring_engine import EnhancedScoringEngine
from unified_player_model import UnifiedPlayer

# Create test pitcher
pitcher = UnifiedPlayer(
    id="test_p",
    name="Gerrit Cole",
    team="NYY",
    salary=9500,
    primary_position="P",
    positions=["P"],
    base_projection=18.5
)

# Add pitcher-specific attributes
pitcher.k9 = 11.2  # Above threshold (9.9)
pitcher.era = 3.2
pitcher.opp_k_rate = 0.25  # Above threshold (0.211)
pitcher.implied_team_score = 4.8  # Pitchers benefit from lower totals
pitcher.projected_ownership = 22

# Test scoring
engine = EnhancedScoringEngine()

print("⚾ PITCHER SCORING TEST")
print("=" * 50)
print(f"Player: {pitcher.name}")
print(f"Base Projection: {pitcher.base_projection}")
print(f"\nPitcher Stats:")
print(f"  K/9: {pitcher.k9} (threshold: 9.9)")
print(f"  Opp K-Rate: {pitcher.opp_k_rate} (threshold: 0.211)")
print(f"  Team Total: {pitcher.implied_team_score}")
print(f"\nScores:")
print(f"  GPP Score: {engine.score_player_gpp(pitcher):.2f}")
print(f"  Cash Score: {engine.score_player_cash(pitcher):.2f}")
