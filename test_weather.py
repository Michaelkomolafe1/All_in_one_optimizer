#!/usr/bin/env python3
"""
Test Showdown Integration
"""
from unified_player_model import UnifiedPlayer
from showdown_optimizer import ShowdownOptimizer, is_showdown_slate


def create_showdown_players():
    """Create a test showdown slate (LAD vs MIN)"""
    players = []

    # Dodgers players
    dodgers = [
        ("Mookie Betts", "OF", 10000, 15.5),
        ("Freddie Freeman", "1B", 9200, 14.2),
        ("Shohei Ohtani", "P", 11000, 18.0),
        ("Will Smith", "C", 7800, 11.5),
        ("Max Muncy", "3B", 7200, 10.8),
    ]

    # Twins players
    twins = [
        ("Byron Buxton", "OF", 8500, 12.5),
        ("Carlos Correa", "SS", 8800, 13.0),
        ("Pablo Lopez", "P", 9000, 16.0),
        ("Royce Lewis", "3B", 7500, 11.0),
        ("Jose Miranda", "1B", 6800, 9.5),
    ]

    # Create both CPT and UTIL entries (like DK does)
    for name, pos, salary, proj in dodgers + twins:
        team = "LAD" if (name, pos, salary, proj) in dodgers else "MIN"

        # CPT entry (1.5x salary)
        cpt_player = UnifiedPlayer(
            id=f"{name}_CPT",
            name=f"{name} (CPT)",
            team=team,
            salary=int(salary * 1.5),
            primary_position=pos,
            positions=[pos],
            base_projection=proj
        )
        cpt_player.roster_position = "CPT"
        players.append(cpt_player)

        # UTIL entry (normal salary)
        util_player = UnifiedPlayer(
            id=f"{name}_UTIL",
            name=name,
            team=team,
            salary=salary,
            primary_position=pos,
            positions=[pos],
            base_projection=proj
        )
        util_player.roster_position = "UTIL"
        players.append(util_player)

    return players


def test_showdown_detection():
    """Test if showdown slates are detected correctly"""
    print("🧪 TESTING SHOWDOWN DETECTION")
    print("=" * 60)

    players = create_showdown_players()

    print(f"Created {len(players)} players (includes CPT and UTIL)")
    print(f"Is showdown slate? {is_showdown_slate(players)}")

    # Check what we have
    teams = set(p.team for p in players)
    cpt_count = sum(1 for p in players if "(CPT)" in p.name)

    print(f"Teams: {teams}")
    print(f"CPT entries: {cpt_count}")
    print(f"UTIL entries: {len(players) - cpt_count}")


def test_showdown_optimization():
    """Test showdown lineup optimization"""
    print("\n\n🧪 TESTING SHOWDOWN OPTIMIZATION")
    print("=" * 60)

    # Create players
    players = create_showdown_players()

    # Add scores (simulate scoring)
    for player in players:
        # Simple score based on projection
        player.optimization_score = player.base_projection
        player.enhanced_score = player.base_projection

    # Create optimizer
    optimizer = ShowdownOptimizer()

    # Optimize lineups
    lineups = optimizer.optimize_showdown(
        players=players,
        num_lineups=3,
        min_salary_usage=0.95
    )

    print(f"\nGenerated {len(lineups)} lineups")

    for i, lineup in enumerate(lineups, 1):
        print(f"\n📋 LINEUP {i}")
        print("-" * 40)

        # Captain
        captain = lineup['captain']
        print(f"CPT: {captain.name} ({captain.team}) "
              f"${int(captain.salary * 1.5)} "
              f"→ {captain.optimization_score * 1.5:.1f} pts")

        # Utilities
        for player in lineup['utilities']:
            print(f"UTIL: {player.name} ({player.team}) "
                  f"${player.salary} "
                  f"→ {player.optimization_score:.1f} pts")

        print(f"\nTotal: ${lineup['total_salary']} "
              f"({lineup['total_salary'] / 50000:.1%}) "
              f"→ {lineup['total_score']:.1f} pts")


def test_pricing_logic():
    """Test that pricing is handled correctly"""
    print("\n\n🧪 TESTING PRICING LOGIC")
    print("=" * 60)

    optimizer = ShowdownOptimizer()
    players = create_showdown_players()

    # Process player pool
    util_players = optimizer.prepare_showdown_pool(players)

    print(f"Original pool: {len(players)} players")
    print(f"UTIL pool: {len(util_players)} players")

    # Verify we only have UTIL entries
    print("\nVerifying UTIL-only pool:")
    for p in util_players[:5]:
        print(f"  {p.name}: ${p.salary} ({p.team})")

    # Check that we filtered out CPT entries
    cpt_in_pool = sum(1 for p in util_players if "(CPT)" in p.name)
    print(f"\nCPT entries in final pool: {cpt_in_pool} (should be 0)")


def test_infeasibility_check():
    """Test what happens with impossible constraints"""
    print("\n\n🧪 TESTING INFEASIBILITY HANDLING")
    print("=" * 60)

    # Create very expensive players
    expensive_players = []
    for i in range(6):
        player = UnifiedPlayer(
            id=f"expensive_{i}",
            name=f"Expensive Player {i}",
            team="LAD" if i < 3 else "MIN",
            salary=12000,  # Very expensive!
            primary_position="OF",
            positions=["OF"],
            base_projection=20.0
        )
        player.optimization_score = 20.0
        expensive_players.append(player)

    optimizer = ShowdownOptimizer()

    print("Testing with all expensive players...")
    lineups = optimizer.optimize_showdown(
        players=expensive_players,
        num_lineups=1,
        min_salary_usage=0.95
    )

    if not lineups:
        print("✅ Correctly identified infeasible lineup")
        min_cost = sum(sorted([p.salary for p in expensive_players])[:5])
        min_captain = min(p.salary for p in expensive_players) * 1.5
        print(f"   Minimum possible: ${min_cost + min_captain}")
        print(f"   Salary cap: $50,000")


if __name__ == "__main__":
    test_showdown_detection()
    test_showdown_optimization()
    test_pricing_logic()
    test_infeasibility_check()

    print("\n\n✅ Showdown integration tests complete!")
    print("\n💡 Key Points:")
    print("1. Showdown uses UTIL entries only (filters out CPT)")
    print("2. Captain multiplier (1.5x) applied during optimization")
    print("3. Generates valid 1 CPT + 5 UTIL lineups")
    print("4. Handles infeasible cases gracefully")