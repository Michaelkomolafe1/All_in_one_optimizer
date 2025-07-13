#!/usr/bin/env python3
"""Minimal test to verify optimization is working"""

import sys

from bulletproof_dfs_core import BulletproofDFSCore


def quick_test():
    print("🚀 QUICK DFS OPTIMIZATION TEST")
    print("=" * 50)

    # Get CSV file
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = input("Enter DraftKings CSV path: ").strip()

    # Initialize
    print("\nInitializing optimizer...")
    core = BulletproofDFSCore()

    # Check what's available
    print("\nSystem status:")
    print(f"  Scoring engine: {'✅' if hasattr(core, 'scoring_engine') and core.scoring_engine else '❌'}")
    print(f"  Validator: {'✅' if hasattr(core, 'validator') and core.validator else '❌'}")
    print(
        f"  Performance optimizer: {'✅' if hasattr(core, 'performance_optimizer') and core.performance_optimizer else '❌'}")

    # Load CSV
    print(f"\nLoading {csv_file}...")
    if not core.load_draftkings_csv(csv_file):
        print("❌ Failed to load CSV")
        return

    print(f"✅ Loaded {len(core.players)} players")

    # Detect confirmed
    print("\nDetecting confirmed players...")
    core.detect_confirmed_players()
    confirmed = [p for p in core.players if p.is_confirmed]
    print(f"✅ Found {len(confirmed)} confirmed players")

    # Generate lineup
    print("\nGenerating optimal lineup...")
    import time
    start = time.time()

    lineup, score = core.optimize_lineup_with_mode()

    elapsed = time.time() - start

    if lineup:
        print(f"\n✅ OPTIMAL LINEUP (generated in {elapsed:.2f}s):")
        print("-" * 60)
        print(f"{'Pos':4s} {'Player':20s} {'Team':4s} {'Salary':>7s} {'Score':>6s}")
        print("-" * 60)

        total_salary = 0
        for player in lineup:
            pos = getattr(player, 'assigned_position', player.primary_position)
            print(f"{pos:4s} {player.name:20s} {player.team:4s} ${player.salary:6d} {player.enhanced_score:6.1f}")
            total_salary += player.salary

        print("-" * 60)
        print(f"{'Total:':35s} ${total_salary:6d} {score:6.1f}")
        print(f"Salary used: {total_salary / 500:.1f}%")

        # Check for score audit
        if hasattr(lineup[0], '_score_audit'):
            print("\n📊 Score calculation working correctly (audit trail available)")
        else:
            print("\n⚠️ No score audit found - using basic scoring")

    else:
        print("❌ No lineup generated")

    # Show cache stats if available
    if hasattr(core, 'scoring_engine') and core.scoring_engine:
        stats = core.scoring_engine.get_statistics()
        print(f"\n📈 Performance: {stats['calculations']} calculations, {stats['cache_hit_rate']:.1%} cache hit rate")


if __name__ == "__main__":
    quick_test()
