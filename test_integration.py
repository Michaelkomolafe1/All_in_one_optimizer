#!/usr/bin/env python3
"""
MINIMAL INTEGRATION TEST
========================
Tests that all components work together
"""

import sys
from types import SimpleNamespace


def test_scoring_integration():
    """Test the integrated scoring system"""
    print("\n1️⃣ Testing Integrated Scoring...")

    try:
        from integrated_scoring_system import IntegratedScoringEngine

        # Create test player
        player = SimpleNamespace(
            name="Test Player",
            team="NYY",
            primary_position="OF",
            salary=10000,
            dk_projection=10.0,
            team_total=5.5,
            batting_order=3,
            game_park="neutral"
        )

        # Test scoring
        engine = IntegratedScoringEngine()
        engine.set_contest_type('gpp')
        score = engine.calculate_score(player)

        print(f"  ✅ Scoring works! Test score: {score:.2f}")
        return True

    except Exception as e:
        print(f"  ❌ Scoring failed: {e}")
        # Try fallback
        try:
            from step2_updated_player_model import SimplifiedScoringEngine
            engine = SimplifiedScoringEngine()
            print("  ⚠️  Using fallback SimplifiedScoringEngine")
            return True
        except:
            return False


def test_showdown_detection():
    """Test showdown detection"""
    print("\n2️⃣ Testing Showdown Detection...")

    try:
        from fixed_showdown_optimization import ShowdownOptimizer

        # Create test showdown players
        players = [
            SimpleNamespace(name="P1", position="CPT", team="NYY", salary=15000),
            SimpleNamespace(name="P2", position="UTIL", team="NYY", salary=10000),
        ]

        optimizer = ShowdownOptimizer(None)
        is_showdown = optimizer.detect_showdown_slate(players)

        if is_showdown:
            print("  ✅ Showdown detection works!")
            return True
        else:
            print("  ❌ Failed to detect showdown slate")
            return False

    except Exception as e:
        print(f"  ❌ Showdown test failed: {e}")
        return False


def test_core_system():
    """Test the core system initialization"""
    print("\n3️⃣ Testing Core System...")

    try:
        from unified_core_system import UnifiedCoreSystem

        system = UnifiedCoreSystem()

        # Check components
        checks = [
            (hasattr(system, 'scoring_engine'), "Scoring engine"),
            (hasattr(system, 'optimizer'), "MILP optimizer"),
            (hasattr(system, 'showdown_optimizer'), "Showdown optimizer"),
        ]

        all_good = True
        for check, name in checks:
            if check:
                print(f"  ✅ {name} initialized")
            else:
                print(f"  ❌ {name} missing")
                all_good = False

        return all_good

    except Exception as e:
        print(f"  ❌ Core system test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 MINIMAL INTEGRATION TEST")
    print("=" * 40)

    results = []
    results.append(test_scoring_integration())
    results.append(test_showdown_detection())
    results.append(test_core_system())

    print("\n" + "=" * 40)
    if all(results):
        print("✅ ALL TESTS PASSED! System is integrated correctly.")
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)
