#!/usr/bin/env python3
"""
Find DKSalaries5.csv and test optimization
==========================================
Searches common locations for the CSV file
"""

import os
import sys
from pathlib import Path


def find_dk_csv():
    """Search for DKSalaries5.csv in common locations"""

    search_locations = [
        # Current directory
        Path.cwd() / "DKSalaries5.csv",

        # Downloads folder
        Path.home() / "Downloads" / "DKSalaries5.csv",

        # Desktop
        Path.home() / "Desktop" / "DKSalaries5.csv",

        # Project directory
        Path("/home/michael/Desktop/All_in_one_optimizer") / "DKSalaries5.csv",

        # Documents
        Path.home() / "Documents" / "DKSalaries5.csv",
    ]

    print("🔍 Searching for DKSalaries5.csv...")

    for location in search_locations:
        if location.exists():
            print(f"✅ Found at: {location}")
            return str(location)

    print("❌ DKSalaries5.csv not found in common locations")
    print("\nSearched:")
    for loc in search_locations:
        print(f"  - {loc}")

    return None


def test_with_csv(csv_path):
    """Test optimization with the found CSV"""
    print(f"\n📊 Testing with: {csv_path}")
    print("=" * 60)

    try:
        # Try minimal optimizer first
        from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig
        from unified_player_model import UnifiedPlayer
        import pandas as pd

        # Load CSV
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} players")

        # Create players
        players = []
        for _, row in df.iterrows():
            player = UnifiedPlayer(
                id=str(row['ID']),
                name=row['Name'],
                team=row['TeamAbbrev'],
                salary=int(row['Salary']),
                primary_position=row['Position'],
                positions=[row['Position']],
                base_projection=float(row['AvgPointsPerGame'])
            )
            player.enhanced_score = player.base_projection
            players.append(player)

        # Optimize
        optimizer = UnifiedMILPOptimizer(OptimizationConfig())
        lineup, score = optimizer.optimize_lineup(players, strategy="all_players")

        if lineup:
            print(f"\n✅ OPTIMIZATION SUCCESSFUL!")
            print(f"Score: {score:.2f}")
            print("\nLineup:")
            for p in lineup:
                print(f"  {p.primary_position} {p.name} ({p.team}) - ${p.salary:,}")

            return True
        else:
            print("❌ Optimization failed")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("🎯 DKSalaries5.csv Finder and Tester")
    print("=" * 60)

    # Check if path provided as argument
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        if os.path.exists(csv_path):
            print(f"✅ Using provided path: {csv_path}")
        else:
            print(f"❌ Provided path not found: {csv_path}")
            csv_path = find_dk_csv()
    else:
        # Search for CSV
        csv_path = find_dk_csv()

    if csv_path:
        # Test optimization
        success = test_with_csv(csv_path)

        if success:
            print("\n" + "=" * 60)
            print("✅ Everything works!")
            print(f"\n💡 To use this file in the GUI:")
            print(f"   1. Copy to project: cp '{csv_path}' .")
            print(f"   2. Or use full path in GUI: {csv_path}")

            # Offer to copy
            print(f"\n📋 Copy command:")
            print(f"cp '{csv_path}' /home/michael/Desktop/All_in_one_optimizer/")
    else:
        print("\n💡 Download DKSalaries5.csv from DraftKings and save to Downloads folder")


if __name__ == "__main__":
    main()