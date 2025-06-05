#!/usr/bin/env python3
"""Simple test for reorganized DFS Optimizer"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.bulletproof_dfs_core import BulletproofDFSCore
from utils.profiler import profiler

def test_basic_optimization():
    """Test basic optimization flow"""
    print("🧪 TESTING REORGANIZED DFS OPTIMIZER")
    print("=" * 50)

    # Initialize
    core = BulletproofDFSCore()

    # Load test CSV
    if core.load_draftkings_csv("DKSalaries_test.csv"):
        print("✅ Loaded test data")

        # Add manual selections
        core.apply_manual_selection("Mike Trout, Shohei Ohtani")

        # Optimize
        lineup, score = core.optimize_lineup_with_mode()

        if lineup:
            print(f"\n✅ Generated lineup with score: {score:.2f}")
            for player in lineup[:5]:  # Show first 5
                print(f"  - {player.name}")
        else:
            print("❌ No lineup generated")
    else:
        print("❌ Failed to load CSV")

if __name__ == "__main__":
    test_basic_optimization()
