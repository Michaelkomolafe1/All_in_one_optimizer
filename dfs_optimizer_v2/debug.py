#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM TEST WITH MOCK DATA
========================================
Tests all components with sufficient mock players
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_pipeline_v2 import DFSPipeline, Player


def create_mock_players():
    """Create enough mock players for testing"""
    players = [
        # Pitchers (need 2)
        Player("Gerrit Cole", "P", "NYY", 9000, 45.0),
        Player("Shane Bieber", "P", "CLE", 8500, 42.0),
        Player("Shohei Ohtani", "P", "LAD", 8000, 40.0),
        Player("Kyle Hendricks", "P", "LAA", 7000, 35.0),

        # Catchers (need 1)
        Player("J.T. Realmuto", "C", "PHI", 4500, 12.0),
        Player("Will Smith", "C", "LAD", 4200, 11.5),
        Player("Salvador Perez", "C", "KC", 4000, 11.0),

        # First Base (need 1)
        Player("Freddie Freeman", "1B", "LAD", 5500, 14.0),
        Player("Vladimir Guerrero Jr.", "1B", "TOR", 5300, 13.5),
        Player("Pete Alonso", "1B", "NYM", 5000, 13.0),

        # Second Base (need 1)
        Player("Mookie Betts", "2B", "LAD", 5800, 14.5),
        Player("Jose Altuve", "2B", "HOU", 5200, 13.0),
        Player("Marcus Semien", "2B", "TEX", 4800, 12.5),

        # Third Base (need 1)
        Player("Manny Machado", "3B", "SD", 5600, 14.2),
        Player("Rafael Devers", "3B", "BOS", 5400, 13.8),
        Player("Nolan Arenado", "3B", "STL", 5200, 13.5),

        # Shortstop (need 1)
        Player("Trea Turner", "SS", "LAD", 5700, 14.3),
        Player("Corey Seager", "SS", "TEX", 5500, 14.0),
        Player("Bo Bichette", "SS", "TOR", 5100, 13.2),

        # Outfield (need 3)
        Player("Mike Trout", "OF", "LAA", 6000, 15.0),
        Player("Ronald Acuna Jr.", "OF", "ATL", 6200, 15.5),
        Player("Aaron Judge", "OF", "NYY", 6100, 15.3),
        Player("Julio Rodriguez", "OF", "SEA", 5800, 14.8),
        Player("Kyle Tucker", "OF", "HOU", 5600, 14.5),
        Player("Juan Soto", "OF", "NYY", 5900, 15.1),
    ]

    # Add some metadata for testing
    for i, player in enumerate(players):
        player.player_id = str(100000 + i)  # Fake MLB ID
        player.optimization_score = player.projection
        player.confirmed = False  # Will be set by confirmation system
        player.batting_order = 0

    return players


def test_full_system():
    """Complete system test with debug output"""
    print("=" * 60)
    print("COMPREHENSIVE DFS OPTIMIZER TEST")
    print("=" * 60)

    # Initialize
    pipeline = DFSPipeline()

    # Test 1: Use mock data
    print("\n📁 TEST 1: Loading mock data...")
    pipeline.all_players = create_mock_players()
    pipeline.num_games = 8  # Simulate 8-game slate
    print(f"✅ Loaded {len(pipeline.all_players)} mock players")

    # Show position distribution
    from collections import defaultdict
    pos_counts = defaultdict(int)
    for p in pipeline.all_players:
        if p.position in ['P', 'SP', 'RP']:
            pos_counts['P'] += 1
        else:
            pos_counts[p.position] += 1

    print("\n📊 Position distribution:")
    for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
        print(f"   {pos}: {pos_counts[pos]} players")

    # Test 2: Simulate confirmations
    print("\n🔍 TEST 2: Simulating confirmations...")
    # Mark some players as confirmed (simulate API response)
    confirmed_count = 0
    for i, player in enumerate(pipeline.all_players):
        # Confirm most players to ensure we have enough
        if i % 4 != 3:  # Confirm 75% of players
            player.confirmed = True
            confirmed_count += 1
            if player.position not in ['P', 'SP', 'RP'] and i < 9:
                player.batting_order = (i % 9) + 1

    print(f"✅ Simulated {confirmed_count} confirmed players")

    # Test 3: Build pools
    print("\n🏊 TEST 3: Building player pools...")

    # Test confirmed only
    count = pipeline.build_player_pool(confirmed_only=True)
    print(f"✅ Confirmed pool: {count} players")

    # Show confirmed position counts
    conf_pos_counts = defaultdict(int)
    for p in pipeline.player_pool:
        if p.position in ['P', 'SP', 'RP']:
            conf_pos_counts['P'] += 1
        else:
            conf_pos_counts[p.position] += 1

    print("   Confirmed positions:")
    for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
        print(f"      {pos}: {conf_pos_counts[pos]} players")

    # Test all players
    count = pipeline.build_player_pool(confirmed_only=False)
    print(f"✅ Full pool: {count} players")

    # Test 4: Strategy application
    print("\n🎯 TEST 4: Applying strategies...")
    for contest in ['cash', 'gpp']:
        try:
            strategy = pipeline.apply_strategy(contest)
            print(f"✅ Applied {strategy} for {contest}")

            # Show score adjustments
            sample_player = pipeline.player_pool[0]
            print(f"   Sample: {sample_player.name}")
            print(f"   Base: {sample_player.projection:.1f}")
            print(f"   Optimized: {sample_player.optimization_score:.1f}")
        except Exception as e:
            print(f"⚠️ Strategy error: {e}")

    # Test 5: Data enrichment
    print("\n📊 TEST 5: Enriching player data...")
    try:
        stats = pipeline.enrich_players('balanced', 'cash')
        print(f"✅ Enrichment stats: {stats}")

        # Check if any players got enriched
        enriched = 0
        for p in pipeline.player_pool:
            if hasattr(p, 'barrel_rate') and p.barrel_rate > 0:
                enriched += 1
        print(f"   {enriched} players enriched with stats")
    except Exception as e:
        print(f"⚠️ Enrichment error: {e}")

    # Test 6: Optimization
    print("\n⚙️ TEST 6: Optimizing lineups...")
    for contest in ['cash', 'gpp']:
        try:
            # Use full pool to ensure enough players
            pipeline.build_player_pool(confirmed_only=False)

            lineups = pipeline.optimize_lineups(contest, 1)
            if lineups and len(lineups) > 0:
                lineup = lineups[0]
                print(f"\n✅ {contest.upper()}: Generated lineup")
                print(f"   Players: {len(lineup['players'])}")
                print(f"   Salary: ${lineup['salary']:,}")
                print(f"   Projection: {lineup['projection']:.1f}")

                # Show lineup composition
                print("   Lineup:")
                for p in lineup['players']:
                    print(f"      {p.position}: {p.name} (${p.salary:,}) - {p.optimization_score:.1f}")

                # Check stack
                from collections import Counter
                teams = Counter(p.team for p in lineup['players'])
                max_stack = max(teams.values())
                print(f"   Max stack: {max_stack} players from same team")
            else:
                print(f"❌ {contest.upper()}: Failed to generate lineup")

                # Debug: Check position availability
                from collections import defaultdict
                pos_available = defaultdict(int)
                for p in pipeline.player_pool:
                    if p.position in ['P', 'SP', 'RP']:
                        pos_available['P'] += 1
                    else:
                        pos_available[p.position] += 1

                print("   Debug - Positions available:")
                for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
                    req = 2 if pos == 'P' else 3 if pos == 'OF' else 1
                    avail = pos_available[pos]
                    status = "✓" if avail >= req else "✗"
                    print(f"      {pos}: {avail}/{req} {status}")

        except Exception as e:
            print(f"❌ {contest.upper()}: Optimization error - {e}")
            import traceback
            traceback.print_exc()

    # Test 7: Export functionality
    print("\n📤 TEST 7: Testing export...")
    if lineups and len(lineups) > 0:
        try:
            output_path = "/tmp/test_lineups.csv"
            success = pipeline.export_lineups(lineups, output_path)
            if success:
                print(f"✅ Exported to {output_path}")
                # Check file exists
                if os.path.exists(output_path):
                    with open(output_path, 'r') as f:
                        lines = f.readlines()
                    print(f"   File has {len(lines)} lines")
            else:
                print("❌ Export failed")
        except Exception as e:
            print(f"❌ Export error: {e}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

    # Return success status
    return len(lineups) > 0 if 'lineups' in locals() else False


if __name__ == "__main__":
    success = test_full_system()
    sys.exit(0 if success else 1)