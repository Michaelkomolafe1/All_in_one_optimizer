from unified_core_system import UnifiedCoreSystem
import logging

logging.basicConfig(level=logging.INFO)


def test_slate(csv_path):
    """Test optimization for any slate type"""
    system = UnifiedCoreSystem()

    # Load CSV
    system.load_players_from_csv(csv_path)

    # Check slate type
    positions = {p.primary_position for p in system.players}
    is_showdown = 'CPT' in positions or 'UTIL' in positions

    print(f"\n{'=' * 60}")
    print(f"SLATE TYPE: {'SHOWDOWN' if is_showdown else 'CLASSIC'}")
    print(f"Total players in CSV: {len(system.players)}")

    if is_showdown:
        cpt_count = len([p for p in system.players if p.primary_position == 'CPT'])
        util_count = len([p for p in system.players if p.primary_position == 'UTIL'])
        print(f"  CPT entries: {cpt_count}")
        print(f"  UTIL entries: {util_count}")

    # Fetch confirmations (works for both)
    confirmed = system.fetch_confirmed_players()
    print(f"\nConfirmed players: {len(confirmed)}")

    # Build pool - will automatically filter CPT for showdown
    system.build_player_pool(include_unconfirmed=True)
    print(f"Player pool size: {len(system.player_pool)}")

    if is_showdown:
        # Verify no CPT in pool
        cpt_in_pool = [p for p in system.player_pool if p.primary_position == 'CPT']
        print(f"CPT entries in pool: {len(cpt_in_pool)} (should be 0)")

    # Optimize - will auto-detect format
    lineups = system.optimize_lineups(num_lineups=1, contest_type="gpp")

    if lineups:
        print(f"\n✅ Generated {len(lineups)} lineups!")
        lineup = lineups[0]

        if is_showdown and 'captain' in lineup:
            print(f"Captain: {lineup['captain'].name} (${lineup['captain'].salary * 1.5})")
            print("Utilities:")
            for p in lineup.get('utilities', []):
                print(f"  {p.name} (${p.salary})")
        else:
            print("Players:")
            for p in lineup['players']:
                print(f"  {p.primary_position}: {p.name} (${p.salary})")

        print(f"\nTotal Salary: ${lineup['total_salary']}")


# Test with your CSV
test_slate("/home/michael/Downloads/DKSalaries(27).csv")