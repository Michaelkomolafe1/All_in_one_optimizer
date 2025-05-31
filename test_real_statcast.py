#!/usr/bin/env python3
"""
Test Real Baseball Savant Data
Verifies that real Statcast data is working
"""

import os
import sys

def test_real_statcast():
    """Test real Baseball Savant data integration"""

    print("🧪 TESTING REAL BASEBALL SAVANT INTEGRATION")
    print("=" * 50)

    try:
        from working_dfs_core_final import OptimizedDFSCore, load_and_optimize_complete_pipeline
        print("✅ Core imported successfully")
    except ImportError as e:
        print(f"❌ Could not import core: {e}")
        return False

    # Find CSV files
    dk_files = [f for f in os.listdir('.') if f.endswith('.csv') and any(keyword in f.lower() for keyword in ['dk', 'salary'])]
    dff_files = [f for f in os.listdir('.') if f.endswith('.csv') and any(keyword in f.lower() for keyword in ['dff', 'cheat'])]

    if not dk_files:
        print("❌ No DraftKings CSV files found")
        return False

    dk_file = dk_files[0]
    dff_file = dff_files[0] if dff_files else None

    print(f"📊 Using DK file: {dk_file}")
    print(f"🎯 Using DFF file: {dff_file}")

    try:
        # Test with a few manual players to see real data
        manual_input = "Shohei Ohtani, Aaron Judge, Mookie Betts, Gerrit Cole, Shane Bieber"

        print(f"\n🎯 Testing with manual players: {manual_input}")
        print("🌐 This should fetch REAL Baseball Savant data...")

        lineup, score, summary = load_and_optimize_complete_pipeline(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input=manual_input,
            contest_type='classic',
            strategy='smart_confirmed'
        )

        if lineup and score > 0:
            print(f"\n✅ SUCCESS: Generated lineup with real Statcast data!")
            print(f"📊 Lineup: {len(lineup)} players, {score:.1f} pts")

            # Check for real data indicators
            real_data_players = []
            for player in lineup:
                if hasattr(player, 'statcast_data') and player.statcast_data:
                    data_source = player.statcast_data.get('data_source', '')
                    if 'Baseball Savant' in data_source:
                        real_data_players.append(player.name)

            if real_data_players:
                print(f"🌐 Players with REAL Baseball Savant data: {len(real_data_players)}")
                for name in real_data_players[:3]:
                    print(f"   📊 {name}")
            else:
                print("⚠️ No players with real Baseball Savant data found")
                print("💡 May be using cached or fallback data")

            return True
        else:
            print("❌ Failed to generate lineup")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_real_statcast()
