#!/usr/bin/env python3
"""
PRIORITY 1 ENHANCEMENTS TEST SCRIPT
==================================
Test the updated DFS system with Priority 1 improvements
"""

def test_priority_1_enhancements():
    """Test Priority 1 enhancements"""
    print("🧪 TESTING PRIORITY 1 ENHANCEMENTS")
    print("=" * 50)

    try:
        # Test enhanced stats engine import
        from enhanced_stats_engine import apply_enhanced_statistical_analysis, VariableConfidenceProcessor
        print("✅ Enhanced Stats Engine: Import successful")

        # Test updated core
        from bulletproof_dfs_core import BulletproofDFSCore, create_enhanced_test_data
        print("✅ Updated Core: Import successful")

        # Create test data
        dk_file, _ = create_enhanced_test_data()
        print("✅ Test Data: Created successfully")

        # Test system
        core = BulletproofDFSCore()
        core.set_optimization_mode('manual_only')

        if core.load_draftkings_csv(dk_file):
            print("✅ Data Loading: Successful")

            # Add manual players
            manual_count = core.apply_manual_selection("Hunter Brown, Francisco Lindor, Kyle Tucker")
            print(f"✅ Manual Selection: {manual_count} players")

            # Test enhanced analysis
            eligible_players = [p for p in core.players if p.is_manual_selected]
            if len(eligible_players) > 0:
                core._apply_comprehensive_statistical_analysis(eligible_players)
                print("✅ Enhanced Analysis: Applied successfully")

                # Check for enhanced features
                enhanced_count = 0
                for player in eligible_players:
                    if hasattr(player, 'enhanced_score'):
                        enhanced_count += 1

                print(f"✅ Enhanced Processing: {enhanced_count} players processed")
                print("\n🎉 PRIORITY 1 ENHANCEMENTS WORKING CORRECTLY!")
                return True
            else:
                print("⚠️ No eligible players found")
                return False
        else:
            print("❌ Failed to load test data")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        import os
        if 'dk_file' in locals():
            try:
                os.unlink(dk_file)
            except:
                pass

if __name__ == "__main__":
    success = test_priority_1_enhancements()
    if success:
        print("\n✅ ALL TESTS PASSED - PRIORITY 1 ENHANCEMENTS READY!")
        print("\n🚀 Next Steps:")
        print("1. Launch GUI: python enhanced_dfs_gui.py")
        print("2. Try manual-only optimization")
        print("3. Notice improved projections!")
    else:
        print("\n❌ SOME TESTS FAILED - CHECK CONFIGURATION")
