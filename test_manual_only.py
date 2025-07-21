#!/usr/bin/env python3
"""
TEST WITH MANUAL SELECTIONS ONLY
=================================
Works even when no games/confirmations
"""

from pathlib import Path
from unified_core_system import UnifiedCoreSystem

print("\n🎮 TESTING WITH MANUAL SELECTIONS")
print("=" * 60)

# Initialize
system = UnifiedCoreSystem()

# Load CSV
csv_files = list(Path('.').glob('*.csv'))
if csv_files:
    system.load_csv(str(csv_files[0]))
    print(f"✅ Loaded {len(system.all_players)} players")

    # Try confirmations (might be 0)
    confirmed = system.fetch_confirmed_players()
    print(f"\nConfirmed players: {confirmed}")

    if confirmed == 0:
        print("\n📝 No games today - using manual selections!")

    # Add manual selections
    print("\n➕ Adding manual players...")

    star_players = [
        # Pitchers
        "Zack Wheeler", "Gerrit Cole", "Shane Bieber",
        "Jacob deGrom", "Spencer Strider",
        # Hitters
        "Shohei Ohtani", "Ronald Acuna Jr.", "Mookie Betts",
        "Freddie Freeman", "Juan Soto", "Aaron Judge",
        "Jose Altuve", "Trea Turner", "Corey Seager"
    ]

    added = 0
    for player in star_players:
        if system.add_manual_player(player):
            print(f"   ✅ {player}")
            added += 1

    print(f"\nAdded {added} manual players")

    # Build pool
    pool_size = system.build_player_pool()
    print(f"\n🏊 Pool size: {pool_size} players")

    # Enrich
    print("\n💎 Enriching player data...")
    system.enrich_player_pool()

    # Optimize
    print("\n🎯 Generating lineup...")
    lineups = system.optimize_lineups(num_lineups=1)

    if lineups:
        print("\n✅ SUCCESS! Generated lineup from manual selections")
        lineup = lineups[0]
        print(f"   Salary: ${lineup['total_salary']:,}")
        print(f"   Points: {lineup['total_projection']:.1f}")
else:
    print("❌ No CSV found")
