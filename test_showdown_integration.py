#!/usr/bin/env python3
"""Test MLB Showdown Integration"""

from bulletproof_dfs_core import BulletproofDFSCore
import os

def test_showdown():
    print("🧪 Testing MLB Showdown Integration")
    print("=" * 60)

    # Initialize core
    core = BulletproofDFSCore()

    # Load CSV
    csv_path = "~/Downloads/DKSalaries(5).csv"
    csv_path = os.path.expanduser(csv_path)

    if not os.path.exists(csv_path):
        csv_path = input("Enter path to All-Star CSV: ")

    if core.load_draftkings_csv(csv_path):
        print(f"\n✅ Loaded {len(core.players)} players")

        # Set mode to use all players
        core.optimization_mode = "all"

        # Run showdown optimization
        lineup, score = core.optimize_showdown_lineup()

        if lineup:
            print(f"\n✅ SHOWDOWN LINEUP GENERATED!")
            print(f"Final Score: {score:.1f}")

            # Verify it's using enriched data
            captain = [p for p in lineup if getattr(p, 'is_captain', False)][0]
            print(f"\n🔍 Data Check for Captain ({captain.name}):")
            print(f"   Base Projection: {captain.base_projection:.1f}")
            print(f"   Enhanced Score: {captain.enhanced_score:.1f}")
            if captain.enhanced_score > captain.base_projection:
                print(f"   ✅ Using enriched scores!")
        else:
            print("\n❌ Failed to generate lineup")
    else:
        print("❌ Failed to load CSV")

if __name__ == "__main__":
    test_showdown()
