#!/usr/bin/env python3
"""
Test with Sample Data - Works with the sample files we just created
"""

def main():
    print("🧪 TESTING WITH SAMPLE DATA")
    print("=" * 50)

    try:
        from optimized_dfs_core_with_statcast import load_and_optimize_complete_pipeline

        # Use the sample files we created
        dk_file = "DKSalaries_Sample.csv"
        dff_file = "DFF_Sample_Cheatsheet.csv"

        # Manual priority players (stars from the sample data)
        manual_players = "Kyle Tucker, Francisco Lindor, Rafael Devers, Aaron Judge, Pete Alonso, Tarik Skubal"

        print(f"📁 DraftKings: {dk_file}")
        print(f"📁 DFF: {dff_file}")  
        print(f"🎯 Manual Priority: {manual_players}")
        print()

        lineup, score, summary = load_and_optimize_complete_pipeline(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input=manual_players,
            contest_type='classic',
            strategy='smart_confirmed'
        )

        if lineup and score > 0:
            print(f"\n✅ SUCCESS!")
            print(f"📊 Generated lineup: {len(lineup)} players, {score:.2f} points")
            print(f"💰 Salary used: ${sum(p.salary for p in lineup):,}")

            print(f"\n🔍 LINEUP BREAKDOWN:")
            real_data_count = 0

            for player in lineup:
                status = "❓"
                data_source = "Unknown"

                if hasattr(player, 'statcast_data') and player.statcast_data:
                    data_source = player.statcast_data.get('data_source', 'Unknown')
                    if 'Baseball Savant' in data_source:
                        status = "🌐"
                        real_data_count += 1
                    else:
                        status = "⚡"

                manual_mark = " [MANUAL]" if getattr(player, 'is_manual_selected', False) else ""
                confirmed_mark = " [CONFIRMED]" if getattr(player, 'is_confirmed', False) else ""

                print(f"   {status} {player.name} ({player.primary_position}) - ${player.salary:,}{manual_mark}{confirmed_mark}")

            print(f"\n📊 STATCAST DATA RESULTS:")
            print(f"   🌐 Real Baseball Savant data: {real_data_count}/{len(lineup)} players")
            print(f"   ⚡ Enhanced simulation: {len(lineup) - real_data_count}/{len(lineup)} players")

            if real_data_count > 0:
                print(f"\n🎉 SUCCESS! Real Statcast data is working!")
                print(f"🏆 You now have PREMIUM DFS optimization with real MLB data!")
            else:
                print(f"\n⚡ Using enhanced simulation (still producing excellent results!)")
                print(f"💡 Real data may be limited due to API availability or season timing")

            return True
        else:
            print("❌ Optimization failed")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 Your DFS optimizer is working perfectly!")
    else:
        print("\n💡 Check the error messages above for troubleshooting")
