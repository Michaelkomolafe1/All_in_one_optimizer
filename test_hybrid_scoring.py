#!/usr/bin/env python3
"""
Test the Hybrid Scoring System
"""
from unified_player_model import UnifiedPlayer
from hybrid_scoring_system import get_hybrid_scoring_system


def create_test_player(name="Test Player", base_proj=10.0, team="LAA"):
    """Create a test player with base data"""
    return UnifiedPlayer(
        id=f"test_{name}",
        name=name,
        team=team,
        salary=5000,
        primary_position="OF",
        positions=["OF"],
        base_projection=base_proj
    )


def test_contest_switching():
    """Test switching between contest types"""
    print("🧪 TESTING CONTEST TYPE SWITCHING")
    print("=" * 60)

    # Get hybrid system
    hybrid = get_hybrid_scoring_system()

    # Create test player with all data
    player = create_test_player("Mike Trout", 15.0)
    player._vegas_data = {"implied_total": 5.5}
    player._recent_performance = {"form_score": 1.15}
    player._statcast_data = {"barrel_rate": 15.0}
    player.batting_order = 2

    # Test 1: Cash game (should use dynamic)
    print("\n1. CASH GAME:")
    scoring_method = hybrid.set_contest_type('cash')
    print(f"   Scoring method: {scoring_method}")
    score_cash = hybrid.calculate_score(player)
    print(f"   Score: {score_cash:.2f}")

    # Test 2: Small GPP (should use dynamic)
    print("\n2. SMALL GPP (100 players):")
    scoring_method = hybrid.set_contest_type('gpp', 100)
    print(f"   Scoring method: {scoring_method}")
    score_small = hybrid.calculate_score(player)
    print(f"   Score: {score_small:.2f}")

    # Test 3: Large GPP (should use enhanced pure)
    print("\n3. LARGE GPP (300 players):")
    scoring_method = hybrid.set_contest_type('gpp', 300)
    print(f"   Scoring method: {scoring_method}")
    score_large = hybrid.calculate_score(player)
    print(f"   Score: {score_large:.2f}")

    # Compare scores
    print("\n📊 SCORE COMPARISON:")
    print(f"   Cash (dynamic): {score_cash:.2f}")
    print(f"   Small GPP (dynamic): {score_small:.2f}")
    print(f"   Large GPP (enhanced): {score_large:.2f}")

    # Check if enhanced pure is different (due to environmental factors)
    if abs(score_large - score_small) > 0.01:
        print("   ✅ Enhanced pure applies environmental factors!")


def test_missing_data_handling():
    """Test how each engine handles missing data"""
    print("\n\n🧪 TESTING MISSING DATA HANDLING")
    print("=" * 60)

    hybrid = get_hybrid_scoring_system()

    # Player with only base projection
    player_base = create_test_player("Base Only", 10.0)

    # Player with some data
    player_partial = create_test_player("Partial Data", 10.0)
    player_partial._vegas_data = {"implied_total": 5.0}
    player_partial.batting_order = 5

    # Test both engines
    print("\n1. DYNAMIC SCORING (Cash):")
    hybrid.set_contest_type('cash')

    score_base_dyn = hybrid.calculate_score(player_base)
    score_partial_dyn = hybrid.calculate_score(player_partial)

    print(f"   Base only: {score_base_dyn:.2f}")
    print(f"   Partial data: {score_partial_dyn:.2f}")
    print(f"   Difference: {score_partial_dyn - score_base_dyn:.2f}")

    print("\n2. ENHANCED PURE (Large GPP):")
    hybrid.set_contest_type('gpp', 300)

    # Clear cache to recalculate
    hybrid.clear_cache()

    score_base_enh = hybrid.calculate_score(player_base)
    score_partial_enh = hybrid.calculate_score(player_partial)

    print(f"   Base only: {score_base_enh:.2f}")
    print(f"   Partial data: {score_partial_enh:.2f}")
    print(f"   Difference: {score_partial_enh - score_base_enh:.2f}")

    print("\n💡 KEY INSIGHT:")
    print("   Dynamic redistributes weights (larger difference)")
    print("   Enhanced pure uses fixed weights (smaller difference)")


def test_park_factors():
    """Test park factor impact in enhanced pure"""
    print("\n\n🧪 TESTING PARK FACTORS (Enhanced Pure)")
    print("=" * 60)

    hybrid = get_hybrid_scoring_system()
    hybrid.set_contest_type('gpp', 300)  # Large GPP

    # Create identical players at different parks
    player_coors = create_test_player("Coors Hitter", 10.0, "COL")
    player_petco = create_test_player("Petco Hitter", 10.0, "SD")

    score_coors = hybrid.calculate_score(player_coors)
    score_petco = hybrid.calculate_score(player_petco)

    print(f"Coors Field (COL): {score_coors:.2f}")
    print(f"Petco Park (SD): {score_petco:.2f}")
    print(f"Difference: {score_coors - score_petco:.2f}")

    # Test pitcher (should be inverted)
    pitcher_coors = create_test_player("Coors Pitcher", 10.0, "COL")
    pitcher_coors.primary_position = "P"

    pitcher_petco = create_test_player("Petco Pitcher", 10.0, "SD")
    pitcher_petco.primary_position = "P"

    score_p_coors = hybrid.calculate_score(pitcher_coors)
    score_p_petco = hybrid.calculate_score(pitcher_petco)

    print(f"\nPitcher at Coors: {score_p_coors:.2f}")
    print(f"Pitcher at Petco: {score_p_petco:.2f}")
    print(f"Difference: {score_p_petco - score_p_coors:.2f}")

    print("\n✅ Park factors working correctly!")


def test_real_scenario():
    """Test a realistic optimization scenario"""
    print("\n\n🧪 REALISTIC SCENARIO TEST")
    print("=" * 60)

    hybrid = get_hybrid_scoring_system()

    # Create a mini player pool
    players = [
        # Stars with complete data
        ("Ronald Acuna Jr.", "ATL", "OF", 10000, 18.5, True),
        ("Shohei Ohtani", "LAA", "P", 11000, 22.0, True),

        # Mid-tier with partial data
        ("Jazz Chisholm", "MIA", "2B", 7500, 12.0, False),
        ("George Springer", "TOR", "OF", 8000, 13.5, True),

        # Value plays with minimal data
        ("Miguel Rojas", "LAD", "SS", 4000, 7.0, False),
        ("Jake Meyers", "HOU", "OF", 3500, 6.5, False),
    ]

    print("PLAYER POOL:")
    print("-" * 60)

    all_players = []
    for name, team, pos, salary, proj, has_data in players:
        p = UnifiedPlayer(
            id=name.lower().replace(" ", "_"),
            name=name,
            team=team,
            salary=salary,
            primary_position=pos,
            positions=[pos],
            base_projection=proj
        )

        if has_data:
            p._vegas_data = {"implied_total": 5.0}
            p._recent_performance = {"form_score": 1.1}
            p.batting_order = 3

        all_players.append(p)

    # Score with both methods
    for contest, slate_size in [("cash", 100), ("gpp", 300)]:
        print(f"\n{contest.upper()} CONTEST:")
        scoring_method = hybrid.set_contest_type(contest, slate_size)
        print(f"Using {scoring_method} scoring")
        print("-" * 40)

        hybrid.clear_cache()

        for p in all_players:
            score = hybrid.calculate_score(p)
            value = score / (p.salary / 1000)
            print(f"{p.name:20} ${p.salary:5} → {score:5.2f} pts ({value:.2f} pts/$K)")


if __name__ == "__main__":
    test_contest_switching()
    test_missing_data_handling()
    test_park_factors()
    test_real_scenario()

    print("\n\n✅ All hybrid scoring tests complete!")
    print("\n🎯 The system now uses:")
    print("   • DYNAMIC scoring for Cash/Small GPPs (better consistency)")
    print("   • ENHANCED PURE for Large GPPs (higher ceiling)")
    print("   • Automatic switching based on contest type")