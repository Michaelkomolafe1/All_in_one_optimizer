#!/usr/bin/env python3
"""
Test why components aren't contributing
"""

from pure_data_scoring_engine import get_pure_scoring_engine
from unified_player_model import UnifiedPlayer


def test_component_contributions():
    """Test each component's contribution"""
    print("TESTING COMPONENT CONTRIBUTIONS")
    print("=" * 60)

    # Create player
    player = UnifiedPlayer(
        id="test1",
        name="Mike Trout",
        team="LAA",
        salary=5500,
        primary_position="OF",
        positions=["OF"],
        base_projection=12.0
    )

    # Get engine for manual testing
    engine = get_pure_scoring_engine()

    # Test 1: Base only
    print("\n1. BASE ONLY:")
    score1 = engine.calculate_score(player)
    print(f"   Score: {score1:.2f}")
    print_audit(player)

    # Test 2: Add Vegas
    print("\n2. ADD VEGAS (5.5 implied total):")
    player._vegas_data = {"implied_total": 5.5}
    engine.clear_cache()
    score2 = engine.calculate_score(player)
    print(f"   Score: {score2:.2f} (change: +{score2 - score1:.2f})")
    print_audit(player)

    # Test 3: Add batting order
    print("\n3. ADD BATTING ORDER (3rd):")
    player.batting_order = 3
    engine.clear_cache()
    score3 = engine.calculate_score(player)
    print(f"   Score: {score3:.2f} (change: +{score3 - score2:.2f})")
    print_audit(player)

    # Test 4: Add recent form
    print("\n4. ADD RECENT FORM (1.20 multiplier):")
    player._recent_performance = {"form_score": 1.20}
    engine.clear_cache()
    score4 = engine.calculate_score(player)
    print(f"   Score: {score4:.2f} (change: +{score4 - score3:.2f})")
    print_audit(player)

    # Test 5: Add statcast
    print("\n5. ADD STATCAST (15% barrel rate):")
    player._statcast_data = {"barrel_rate": 15.0}
    engine.clear_cache()
    score5 = engine.calculate_score(player)
    print(f"   Score: {score5:.2f} (change: +{score5 - score4:.2f})")
    print_audit(player)

    # Summary
    print("\n" + "=" * 60)
    print("COMPONENT BREAKDOWN:")
    print(f"Base contribution: {score1:.2f}")
    print(f"Vegas contribution: {score2 - score1:.2f}")
    print(f"Batting order contribution: {score3 - score2:.2f}")
    print(f"Recent form contribution: {score4 - score3:.2f}")
    print(f"Statcast contribution: {score5 - score4:.2f}")
    print(f"TOTAL: {score5:.2f}")

    # Expected calculation
    print("\nEXPECTED CALCULATION:")
    print(f"Base: 12.0 × 0.35 = {12.0 * 0.35:.2f}")
    print(f"If all multipliers were 1.10x:")
    print(f"  Vegas: 12.0 × 1.10 × 0.20 = {12.0 * 1.10 * 0.20:.2f}")
    print(f"  Recent: 12.0 × 1.20 × 0.25 = {12.0 * 1.20 * 0.25:.2f}")
    print(f"  Matchup: 12.0 × 1.10 × 0.15 = {12.0 * 1.10 * 0.15:.2f}")
    print(f"  Order: 12.0 × 1.08 × 0.05 = {12.0 * 1.08 * 0.05:.2f}")


def print_audit(player):
    """Print audit details if available"""
    if hasattr(player, '_score_audit'):
        audit = player._score_audit
        if 'components' in audit and isinstance(audit['components'], dict):
            components = []
            for name, data in audit['components'].items():
                if isinstance(data, dict) and 'multiplier' in data:
                    mult = data['multiplier']
                    weight = data.get('weight', 0)
                    contrib = data.get('contribution', 0)
                    components.append(f"{name}({mult:.2f}×{weight:.0%}={contrib:.2f})")
                else:
                    components.append(f"{name}(?)")
            print(f"   Components: {' + '.join(components)}")
        if 'data_completeness' in audit:
            print(f"   Data completeness: {audit['data_completeness']:.0%}")


if __name__ == "__main__":
    test_component_contributions()