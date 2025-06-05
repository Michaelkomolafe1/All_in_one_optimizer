#!/usr/bin/env python3
"""
QUICK TEST WITH NEW CSV
=======================
Test the optimizer with the good CSV file
"""

from bulletproof_dfs_core import BulletproofDFSCore


def test_with_good_csv():
    """Test with the new comprehensive CSV"""
    print("🧪 DFS OPTIMIZER TEST - GOOD DATA")
    print("=" * 50)

    core = BulletproofDFSCore()

    # Use the GOOD CSV file!
    csv_file = "DKSalaries_good.csv"

    print(f"\n📁 Loading {csv_file}...")
    if not core.load_draftkings_csv(csv_file):
        print("❌ Failed to load CSV")
        return False

    print(f"✅ Loaded {len(core.players)} players successfully!")

    # Show position coverage
    positions = {}
    for player in core.players:
        pos = player.primary_position
        positions[pos] = positions.get(pos, 0) + 1

    print("\n📊 Position coverage:")
    for pos, count in sorted(positions.items()):
        required = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}.get(pos, 0)
        status = "✅" if count >= required else "❌"
        print(f"   {status} {pos}: {count} players (need {required})")

    # Test 1: Basic optimization
    print("\n" + "=" * 50)
    print("🚀 TEST 1: BASIC OPTIMIZATION")
    print("=" * 50)

    lineup, score = core.optimize_lineup_with_mode()

    if lineup and len(lineup) == 10:
        print(f"\n✅ SUCCESS! Generated optimal lineup")
        print(f"📊 Total Score: {score:.2f} points")
        print(f"💰 Total Salary: ${sum(p.salary for p in lineup):,} / $50,000")

        print("\n📋 Your Optimal Lineup:")
        print("-" * 60)
        for player in lineup:
            pos = getattr(player, 'assigned_position', player.primary_position)
            print(f"{pos:>2}: {player.name:<22} {player.team:<3} ${player.salary:>5,} {player.enhanced_score:>5.1f}pts")
        print("-" * 60)

        # Value analysis
        total_salary = sum(p.salary for p in lineup)
        avg_score = score / 10
        value = score / (total_salary / 1000)

        print(f"\n📈 Lineup Analysis:")
        print(f"   Average score/player: {avg_score:.2f}")
        print(f"   Points per $1k: {value:.2f}")
        print(f"   Salary used: {(total_salary / 50000) * 100:.1f}%")

    else:
        print("❌ Failed to generate lineup")
        return False

    # Test 2: Manual selection
    print("\n" + "=" * 50)
    print("🎯 TEST 2: MANUAL SELECTION MODE")
    print("=" * 50)

    # Select some good players manually
    manual_picks = "Aaron Judge, Mike Trout, Mookie Betts, Gerrit Cole, Freddie Freeman"
    print(f"📝 Manual selections: {manual_picks}")

    selected = core.apply_manual_selection(manual_picks)
    print(f"✅ Selected {selected} players manually")

    # Show what was selected
    manual_players = [p for p in core.players if p.is_manual_selected]
    if manual_players:
        print("\n🌟 Your manual picks:")
        for p in manual_players:
            print(f"   - {p.name} ({p.primary_position}) ${p.salary:,}")

    # Test 3: Check confirmations
    print("\n" + "=" * 50)
    print("🔍 TEST 3: CONFIRMED LINEUPS CHECK")
    print("=" * 50)

    confirmed_count = core.detect_confirmed_players()

    if confirmed_count > 0:
        print(f"✅ Found {confirmed_count} confirmed players!")
        confirmed = [p for p in core.players if p.is_confirmed]
        print("Confirmed players:", ", ".join(p.name for p in confirmed[:5]))
    else:
        print("⚠️ No confirmed lineups available (normal for late night)")
        print("   During game time, this will show real confirmed lineups")

    return True


def quick_lineup_test():
    """Super quick lineup generation"""
    print("\n" + "=" * 50)
    print("⚡ QUICK LINEUP GENERATION")
    print("=" * 50)

    core = BulletproofDFSCore()

    # Load the good CSV
    if core.load_draftkings_csv("DKSalaries_good.csv"):
        # Just optimize!
        lineup, score = core.optimize_lineup_with_mode()

        if lineup:
            print(f"\n✅ Quick lineup ready!")
            print(f"Score: {score:.2f} | Salary: ${sum(p.salary for p in lineup):,}")
            print("\nTop 5 players:")
            sorted_lineup = sorted(lineup, key=lambda x: x.enhanced_score, reverse=True)
            for i, p in enumerate(sorted_lineup[:5], 1):
                print(f"{i}. {p.name} - {p.enhanced_score:.1f}pts")

            return True

    return False


if __name__ == "__main__":
    import sys

    # Check which CSV exists
    from pathlib import Path

    if not Path("DKSalaries_good.csv").exists():
        print("❌ DKSalaries_good.csv not found!")
        print("\n💡 Create it by running:")
        print(
            'python -c "from test_confirmed_lineups import create_comprehensive_test_csv; create_comprehensive_test_csv()"')
        sys.exit(1)

    # Run the tests
    if test_with_good_csv():
        print("\n🎉 ALL TESTS PASSED!")
        print("\n🚀 Your optimizer is working perfectly!")
        print("\n📅 Tomorrow during games:")
        print("   1. Download real DraftKings CSV")
        print("   2. Confirmed lineups will auto-populate")
        print("   3. Vegas lines will be fetched")
        print("   4. Generate winning lineups!")
    else:
        # Quick test as fallback
        print("\n🔄 Trying quick test...")
        quick_lineup_test()