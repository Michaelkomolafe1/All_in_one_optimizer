#!/usr/bin/env python3
"""
IMPROVED TEST SCRIPT FOR DFS OPTIMIZER
======================================
Tests all optimization modes and features
"""

import time
import sys
from pathlib import Path

# Add parent to path if running from tests folder
if Path(__file__).parent.name == 'tests':
    sys.path.append(str(Path(__file__).parent.parent))

from bulletproof_dfs_core import BulletproofDFSCore
from utils.profiler import profiler
from utils.config import config
from utils.cache_manager import cache


def test_optimization_modes():
    """Test different optimization modes"""
    print("🧪 COMPREHENSIVE DFS OPTIMIZER TEST")
    print("=" * 60)

    # Initialize
    core = BulletproofDFSCore()

    # Load test CSV
    csv_file = "DKSalaries_test.csv"
    if not Path(csv_file).exists():
        print("❌ Test CSV not found. Creating one...")
        create_test_csv()

    print(f"\n📁 Loading {csv_file}...")
    if not core.load_draftkings_csv(csv_file):
        print("❌ Failed to load CSV")
        return

    # Test 1: Basic optimization (all players eligible)
    print("\n" + "=" * 60)
    print("TEST 1: BASIC OPTIMIZATION (All Players)")
    print("=" * 60)

    core.set_optimization_mode('bulletproof')

    # Don't apply manual selections first - let it use all players
    lineup1, score1 = core.optimize_lineup_with_mode()

    if lineup1:
        print(f"✅ Generated lineup with {len(lineup1)} players")
        print(f"📊 Score: {score1:.2f}")
        print(f"💰 Total Salary: ${sum(p.salary for p in lineup1):,}")
        print("\n📋 Lineup:")
        for player in lineup1:
            pos = getattr(player, 'assigned_position', player.primary_position)
            print(f"  {pos:>2}: {player.name:<20} ${player.salary:>6,} {player.enhanced_score:>5.1f}pts")
    else:
        print("❌ Failed to generate lineup")

    # Test 2: Manual-only mode
    print("\n" + "=" * 60)
    print("TEST 2: MANUAL-ONLY MODE")
    print("=" * 60)

    # Reset and reload
    core = BulletproofDFSCore()
    core.load_draftkings_csv(csv_file)

    # Apply enough manual selections for a full lineup
    manual_players = [
        "Gerrit Cole", "Shane Bieber",  # Pitchers
        "Will Smith",  # Catcher
        "Freddie Freeman",  # 1B
        "Jose Altuve",  # 2B
        "Manny Machado",  # 3B
        "Trea Turner",  # SS
        "Aaron Judge", "Mike Trout", "Mookie Betts"  # OF
    ]

    manual_string = ", ".join(manual_players)
    print(f"📝 Selecting {len(manual_players)} manual players...")

    selected = core.apply_manual_selection(manual_string)
    print(f"✅ Successfully selected {selected} players")

    core.set_optimization_mode('manual_only')
    lineup2, score2 = core.optimize_lineup_with_mode()

    if lineup2:
        print(f"\n✅ Manual lineup generated!")
        print(f"📊 Score: {score2:.2f}")
        print(f"💰 Total Salary: ${sum(p.salary for p in lineup2):,}")
    else:
        print("❌ Failed to generate manual lineup")

    # Test 3: Multi-lineup generation
    print("\n" + "=" * 60)
    print("TEST 3: MULTI-LINEUP GENERATION")
    print("=" * 60)

    # Use fresh core
    core = BulletproofDFSCore()
    core.load_draftkings_csv(csv_file)

    print("🎲 Generating 5 diverse lineups...")

    # If the method exists, use it
    if hasattr(core, 'generate_multiple_lineups'):
        lineups = core.generate_multiple_lineups(count=5, strategy='balanced')
        print(f"✅ Generated {len(lineups)} lineups")

        for i, lineup_result in enumerate(lineups, 1):
            print(f"\nLineup {i}: Score {lineup_result.total_score:.2f}, Salary ${lineup_result.total_salary:,}")
    else:
        # Fallback to generating lineups manually
        lineups = []
        for i in range(3):
            lineup, score = core.optimize_lineup_with_mode()
            if lineup:
                lineups.append((lineup, score))
                print(f"  Lineup {i + 1}: Score {score:.2f}")

        if lineups:
            # Show player diversity
            all_players = set()
            for lineup, _ in lineups:
                for player in lineup:
                    all_players.add(player.name)
            print(f"\n📊 Player diversity: {len(all_players)} unique players used")

    # Test 4: Performance metrics
    print("\n" + "=" * 60)
    print("TEST 4: PERFORMANCE METRICS")
    print("=" * 60)

    # Cache stats
    cache_stats = cache.get_stats()
    print(f"\n📦 Cache Statistics:")
    print(f"  Total files: {cache_stats['total_files']}")
    print(f"  Total size: {cache_stats['total_size_mb']:.2f} MB")
    print(f"  Categories: {cache_stats['categories']}")

    # Profiler stats
    if hasattr(profiler, 'get_report'):
        profile_report = profiler.get_report()
        if profile_report:
            print(f"\n⏱️ Performance Profile:")
            for func, stats in list(profile_report.items())[:5]:  # Top 5
                print(f"  {func}: {stats['calls']} calls, {stats['average']:.3f}s avg")

    # Configuration
    print(f"\n⚙️ Configuration:")
    print(f"  Salary Cap: ${config.get('salary_cap'):,}")
    print(f"  Min Projection: {config.get('optimization.min_projection')}")
    print(f"  Diversity Factor: {config.get('optimization.diversity_factor')}")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE!")
    print("=" * 60)


def create_test_csv():
    """Create a comprehensive test CSV"""
    csv_content = """Position,Name,Name,ID,Roster Position,Salary,Game Info,TeamAbbrev,AvgPointsPerGame
P,Gerrit Cole,Gerrit Cole,1001,P,10500,NYY@BOS 07:10PM ET,NYY,18.5
P,Shane Bieber,Shane Bieber,1002,P,9800,CLE@MIN 08:10PM ET,CLE,17.2
P,Dylan Cease,Dylan Cease,1003,P,8200,SD@LAD 10:10PM ET,SD,15.8
P,Walker Buehler,Walker Buehler,1004,P,7500,LAD@SD 10:10PM ET,LAD,14.2
P,Logan Webb,Logan Webb,1005,P,7000,SF@COL 08:40PM ET,SF,13.5
C,Will Smith,Will Smith,2001,C,4800,LAD@SD 10:10PM ET,LAD,9.5
C,Salvador Perez,Salvador Perez,2002,C,4200,KC@DET 07:10PM ET,KC,8.2
C,J.T. Realmuto,J.T. Realmuto,2003,C,4500,PHI@NYM 07:10PM ET,PHI,8.8
1B,Freddie Freeman,Freddie Freeman,3001,1B,5500,LAD@SD 10:10PM ET,LAD,11.2
1B,Vladimir Guerrero Jr.,Vladimir Guerrero Jr.,3002,1B,5200,TOR@TB 07:10PM ET,TOR,10.8
1B,Pete Alonso,Pete Alonso,3003,1B,4900,NYM@PHI 07:10PM ET,NYM,10.2
2B,Jose Altuve,Jose Altuve,4001,2B,5000,HOU@TEX 08:05PM ET,HOU,10.5
2B,Marcus Semien,Marcus Semien,4002,2B,4600,TEX@HOU 08:05PM ET,TEX,9.2
2B,Gleyber Torres,Gleyber Torres,4003,2B,4300,NYY@BOS 07:10PM ET,NYY,8.7
3B,Manny Machado,Manny Machado,5001,3B,5100,SD@LAD 10:10PM ET,SD,10.8
3B,Jose Ramirez,Jose Ramirez,5002,3B,5400,CLE@MIN 08:10PM ET,CLE,11.5
3B,Rafael Devers,Rafael Devers,5003,3B,4800,BOS@NYY 07:10PM ET,BOS,10.0
SS,Trea Turner,Trea Turner,6001,SS,5300,PHI@NYM 07:10PM ET,PHI,10.9
SS,Corey Seager,Corey Seager,6002,SS,5100,TEX@HOU 08:05PM ET,TEX,10.5
SS,Bo Bichette,Bo Bichette,6003,SS,4700,TOR@TB 07:10PM ET,TOR,9.5
OF,Aaron Judge,Aaron Judge,7001,OF,6200,NYY@BOS 07:10PM ET,NYY,13.5
OF,Mike Trout,Mike Trout,7002,OF,5800,LAA@SEA 09:40PM ET,LAA,12.2
OF,Mookie Betts,Mookie Betts,7003,OF,5600,LAD@SD 10:10PM ET,LAD,11.8
OF,Ronald Acuna Jr.,Ronald Acuna Jr.,7004,OF,5900,ATL@MIA 06:40PM ET,ATL,12.5
OF,Juan Soto,Juan Soto,7005,OF,5400,SD@LAD 10:10PM ET,SD,11.2
OF,Shohei Ohtani,Shohei Ohtani,7006,OF,6000,LAA@SEA 09:40PM ET,LAA,12.8
OF,Yordan Alvarez,Yordan Alvarez,7007,OF,5200,HOU@TEX 08:05PM ET,HOU,10.9
OF,Kyle Tucker,Kyle Tucker,7008,OF,4900,HOU@TEX 08:05PM ET,HOU,10.2
OF,Randy Arozarena,Randy Arozarena,7009,OF,4600,TB@TOR 07:10PM ET,TB,9.5
OF,Julio Rodriguez,Julio Rodriguez,7010,OF,4800,SEA@LAA 09:40PM ET,SEA,9.8"""

    with open('DKSalaries_test.csv', 'w') as f:
        f.write(csv_content)
    print("✅ Created comprehensive test CSV with 30 players")


def quick_test():
    """Quick test to verify system is working"""
    print("🚀 QUICK DFS OPTIMIZER TEST")
    print("=" * 40)

    core = BulletproofDFSCore()

    # Create test CSV if needed
    if not Path("DKSalaries_test.csv").exists():
        create_test_csv()

    if core.load_draftkings_csv("DKSalaries_test.csv"):
        print("✅ CSV loaded successfully")
        print(f"📊 Total players: {len(core.players)}")

        # Test basic optimization
        lineup, score = core.optimize_lineup_with_mode()

        if lineup:
            print(f"\n✅ OPTIMIZATION SUCCESSFUL!")
            print(f"Score: {score:.2f} points")
            print(f"Players: {len(lineup)}")
            print(f"Salary: ${sum(p.salary for p in lineup):,}")

            # Show lineup
            print("\n📋 Quick Lineup Preview:")
            for i, player in enumerate(lineup[:5]):
                print(f"  {player.name} - ${player.salary:,}")
            if len(lineup) > 5:
                print(f"  ... and {len(lineup) - 5} more players")
        else:
            print("\n❌ Optimization failed - this is likely due to not enough eligible players")
            print("💡 Try running the full test with: python test_optimizations.py --full")
    else:
        print("❌ Failed to load CSV")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        test_optimization_modes()
    else:
        quick_test()
        print("\n💡 Run with --full flag for comprehensive testing:")
        print("   python test_optimizations.py --full")