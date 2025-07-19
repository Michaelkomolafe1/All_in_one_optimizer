#!/usr/bin/env python3
"""
AUTO TEST ENRICHMENTS
====================
Automatically finds your latest DK CSV and tests enrichments
"""

import os
import glob
from datetime import datetime
from bulletproof_dfs_core import BulletproofDFSCore


def find_latest_dk_csv():
    """Find the most recent DraftKings CSV"""
    # Look in Downloads folder
    downloads = os.path.expanduser("~/Downloads")

    # Find all DK CSV files
    patterns = [
        f"{downloads}/DKSalaries*.csv",
        f"{downloads}/DKSalaries*.CSV",
        f"{downloads}/dk*.csv",
        f"{downloads}/draftkings*.csv"
    ]

    all_files = []
    for pattern in patterns:
        all_files.extend(glob.glob(pattern))

    if not all_files:
        return None

    # Get the most recent file
    latest_file = max(all_files, key=os.path.getmtime)
    return latest_file


def test_enrichments_auto():
    """Test enrichments with auto-found CSV"""
    print("🔍 AUTO ENRICHMENT TESTER")
    print("=" * 60)

    # Initialize core
    core = BulletproofDFSCore()
    print("✅ Core system loaded\n")

    # Find CSV automatically
    csv_path = find_latest_dk_csv()

    if not csv_path:
        print("❌ No DraftKings CSV found in Downloads folder")
        print("\n💡 Looking for ANY CSV in Downloads...")

        all_csvs = glob.glob(os.path.expanduser("~/Downloads/*.csv"))
        if all_csvs:
            print(f"\nFound {len(all_csvs)} CSV files:")
            for i, csv in enumerate(all_csvs[-5:], 1):  # Show last 5
                print(f"  {i}. {os.path.basename(csv)}")
        return

    print(f"📄 Found CSV: {os.path.basename(csv_path)}")
    print(f"   Full path: {csv_path}")

    # Get file info
    stat = os.stat(csv_path)
    mod_time = datetime.fromtimestamp(stat.st_mtime)
    print(f"   Modified: {mod_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Size: {stat.st_size / 1024:.1f} KB")

    # Load CSV
    print(f"\n📂 Loading CSV...")
    if not core.load_draftkings_csv(csv_path):
        print("❌ Failed to load CSV")
        return

    print(f"✅ Loaded {len(core.players)} players")

    # Show contest type
    if any(hasattr(p, 'roster_position') and 'CPT' in str(p.roster_position) for p in core.players):
        print("📋 Contest Type: SHOWDOWN")
        contest_type = "showdown"
    else:
        print("📋 Contest Type: CLASSIC")
        contest_type = "classic"

    # Show sample players
    print(f"\n👥 Sample players:")
    for i, player in enumerate(core.players[:5]):
        print(f"  {i + 1}. {player.name} ({player.team}) - ${player.salary:,}")

    # Test enrichments
    print("\n📊 TESTING ENRICHMENT SYSTEMS:")
    print("-" * 40)

    # 1. Vegas
    print("\n🎰 Vegas Lines:", end=" ")
    if hasattr(core, 'vegas_lines') and core.vegas_lines:
        print("✅ Available")
        try:
            lines = core.vegas_lines.get_vegas_lines()
            if lines:
                print(f"   ✅ Working - {len(lines)} teams with data")
            else:
                print("   ⚠️ No data (need API key)")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}...")
    else:
        print("❌ Not found")

    # 2. Statcast
    print("\n⚾ Statcast:", end=" ")
    if hasattr(core, 'statcast_fetcher') and core.statcast_fetcher:
        print("✅ Available")
        try:
            # Test with first player
            test_player = core.players[0]
            if hasattr(core.statcast_fetcher, 'get_hitter_stats'):
                data = core.statcast_fetcher.get_hitter_stats(test_player.name)
                if data:
                    print(f"   ✅ Working - got data for {test_player.name}")
                else:
                    print(f"   ⚠️ No data for {test_player.name}")
            else:
                print("   ⚠️ Missing get_hitter_stats method")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}...")
    else:
        print("❌ Not found")

    # 3. Enrichment Bridge
    print("\n🌉 Enrichment Bridge:", end=" ")
    if hasattr(core, 'enrichment_bridge') and core.enrichment_bridge:
        print("✅ Available")
    else:
        print("❌ Not found")

    # 4. Test actual enrichment
    print("\n\n🧪 APPLYING ENRICHMENTS:")
    print("-" * 40)

    if hasattr(core, 'enrichment_bridge') and core.enrichment_bridge:
        try:
            print("Applying enrichments...")
            core.enrichment_bridge.apply_enrichments_to_core(core)
            print("✅ Enrichments applied!")

            # Check results
            enhanced_count = 0
            total_improvement = 0

            print(f"\n📊 Results for first 10 players:")
            for player in core.players[:10]:
                base = getattr(player, 'projection', 0)
                enhanced = getattr(player, 'enhanced_score', base)

                if enhanced != base and base > 0:
                    enhanced_count += 1
                    improvement = ((enhanced / base) - 1) * 100
                    total_improvement += improvement
                    print(f"  ✅ {player.name}: {base:.1f} → {enhanced:.1f} (+{improvement:.1f}%)")
                else:
                    print(f"  ⚠️ {player.name}: No enhancement")

            if enhanced_count > 0:
                avg_improvement = total_improvement / enhanced_count
                print(f"\n📈 Average improvement: +{avg_improvement:.1f}%")
                print(f"✅ Enriched {enhanced_count}/10 players")
            else:
                print(f"\n⚠️ No players were enhanced - check enrichment systems")

        except Exception as e:
            print(f"❌ Enrichment error: {e}")

    # Test optimization
    print("\n\n🎯 TESTING OPTIMIZATION:")
    print("-" * 40)

    try:
        if contest_type == "showdown":
            print("Running showdown optimization...")
            lineup, score = core.optimize_showdown_lineup()
        else:
            print("Running classic optimization...")
            lineup = core.optimize_lineup()
            score = sum(p.enhanced_score for p in lineup) if lineup else 0

        if lineup:
            print(f"✅ Generated lineup with {len(lineup)} players")
            print(f"📈 Total score: {score:.1f}")

            # Show if using enhanced scores
            if lineup and hasattr(lineup[0], 'enhanced_score'):
                base_total = sum(getattr(p, 'projection', 0) for p in lineup)
                enhanced_total = sum(getattr(p, 'enhanced_score', 0) for p in lineup)
                if enhanced_total > base_total:
                    print(f"🚀 Using enhanced scores! (+{((enhanced_total / base_total) - 1) * 100:.1f}%)")
        else:
            print("❌ Failed to generate lineup")

    except Exception as e:
        print(f"❌ Optimization error: {e}")

    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_enrichments_auto()