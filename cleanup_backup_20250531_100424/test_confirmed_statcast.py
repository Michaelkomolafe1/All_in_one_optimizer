#!/usr/bin/env python3
"""
Test Confirmed Players Real Statcast Data
Verifies that confirmed players get real Baseball Savant data
"""

import os
import sys

def test_confirmed_real_data():
    """Test that confirmed players get real Baseball Savant data"""

    print("🧪 TESTING CONFIRMED PLAYERS REAL STATCAST DATA")
    print("=" * 60)

    try:
        from working_dfs_core_final import load_and_optimize_complete_pipeline
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
        # Test with manual players to ensure they get real data
        manual_input = "Shohei Ohtani, Aaron Judge, Mookie Betts, Gerrit Cole, Shane Bieber"

        print(f"\n🎯 Testing with manual players (should get REAL data): {manual_input}")
        print("🔍 Confirmed players should also get REAL data")
        print("🌐 Look for 'Baseball Savant' data source in output...")

        lineup, score, summary = load_and_optimize_complete_pipeline(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input=manual_input,
            contest_type='classic',
            strategy='smart_confirmed'
        )

        if lineup and score > 0:
            print(f"\n✅ SUCCESS: Generated lineup!")
            print(f"📊 Lineup: {len(lineup)} players, {score:.1f} pts")

            # Analyze data sources
            real_data_count = 0
            confirmed_count = 0
            manual_count = 0

            print(f"\n📊 DATA SOURCE ANALYSIS:")
            for player in lineup:
                is_confirmed = getattr(player, 'is_confirmed', False)
                is_manual = getattr(player, 'is_manual_selected', False)

                if is_confirmed:
                    confirmed_count += 1
                if is_manual:
                    manual_count += 1

                if hasattr(player, 'statcast_data') and player.statcast_data:
                    data_source = player.statcast_data.get('data_source', 'unknown')
                    if 'Baseball Savant' in data_source:
                        real_data_count += 1
                        status = "🌐 REAL"
                    else:
                        status = "⚡ SIM"

                    player_type = []
                    if is_confirmed:
                        player_type.append("CONF")
                    if is_manual:
                        player_type.append("MANUAL")

                    type_str = "|".join(player_type) if player_type else "REGULAR"
                    print(f"   {status} {player.name} ({type_str})")

            print(f"\n📈 SUMMARY:")
            print(f"🌐 Real Baseball Savant data: {real_data_count}/{len(lineup)}")
            print(f"✅ Confirmed players: {confirmed_count}")
            print(f"📝 Manual players: {manual_count}")

            if real_data_count >= (confirmed_count + manual_count):
                print(f"\n🎉 SUCCESS! Confirmed + manual players got real data!")
                return True
            else:
                print(f"\n⚠️ Some confirmed/manual players missing real data")
                print(f"💡 May need additional timing fixes")
                return False
        else:
            print("❌ Failed to generate lineup")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_confirmed_real_data()
    if success:
        print("\n🎉 CONFIRMED PLAYERS REAL DATA TEST PASSED!")
    else:
        print("\n⚠️ Test needs attention")
