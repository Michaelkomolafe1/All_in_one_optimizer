#!/usr/bin/env python3
"""
Manual Priority Test - Force priority players for real Statcast data
"""

def test_with_manual_priority():
    """Test with manually specified priority players"""

    print("🧪 TESTING WITH MANUAL PRIORITY PLAYERS")
    print("=" * 60)

    try:
        from optimized_dfs_core_with_statcast import load_and_optimize_complete_pipeline

        # Test with high-value manual players
        manual_players = "Francisco Lindor, Pete Alonso, Christian Yelich, Rafael Devers, Robbie Ray, Kodai Senga"

        print(f"🎯 Manual players: {manual_players}")

        lineup, score, summary = load_and_optimize_complete_pipeline(
            dk_file="DKSalaries (58).csv",
            dff_file="DFF_MLB_cheatsheet_2025-05-31.csv", 
            manual_input=manual_players,  # Force these as priority
            contest_type='classic',
            strategy='smart_confirmed'
        )

        if lineup and score > 0:
            print(f"\n✅ Test completed!")
            print(f"📊 Lineup: {len(lineup)} players, {score:.2f} score")

            # Check which players got real data
            real_data_players = []
            for player in lineup:
                if hasattr(player, 'statcast_data') and player.statcast_data:
                    data_source = player.statcast_data.get('data_source', '')
                    if 'Baseball Savant' in data_source:
                        real_data_players.append(player.name)

            print(f"🌐 Players with real Statcast data: {len(real_data_players)}")
            for player_name in real_data_players:
                print(f"   ✅ {player_name}")

            if len(real_data_players) == 0:
                print("❌ Still no real Statcast data")
                print("💡 The issue is in the fetcher itself, not priority detection")

            return len(real_data_players) > 0
        else:
            print("❌ Test failed")
            return False

    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    test_with_manual_priority()
