#!/usr/bin/env python3
"""
FIXED DEBUG SCRIPT - Shows actual confirmations
"""

from bulletproof_dfs_core import BulletproofDFSCore


def debug_confirmations():
    print("🔍 DEBUGGING CONFIRMATIONS")
    print("=" * 80)

    core = BulletproofDFSCore()

    # Load CSV
    if not core.load_draftkings_csv("DKSalaries_good.csv"):
        return

    # Get confirmations
    confirmed_count = core.detect_confirmed_players()

    # Now manually check each player
    print("\n📋 PLAYER BY PLAYER CONFIRMATION CHECK:")

    confirmed_players = []
    for player in core.players:
        if core.confirmation_system:
            # Check lineup
            is_in_lineup, batting_order = core.confirmation_system.is_player_confirmed(
                player.name, player.team
            )

            # Check if pitcher
            is_starting_pitcher = False
            if player.primary_position == 'P':
                is_starting_pitcher = core.confirmation_system.is_pitcher_confirmed(
                    player.name, player.team
                )

            if is_in_lineup or is_starting_pitcher:
                player.add_confirmation_source("mlb_confirmed")
                confirmed_players.append(player)

                status = "Starting Pitcher" if is_starting_pitcher else f"Batting {batting_order}"
                print(f"✅ {player.name} ({player.team}) - {status}")

    print(f"\n📊 Total confirmed: {len(confirmed_players)}")

    # Now apply analytics to confirmed only
    if confirmed_players:
        print("\n🔬 APPLYING ANALYTICS TO CONFIRMED PLAYERS ONLY...")

        # Vegas
        if core.vegas_lines:
            print("💰 Applying Vegas to confirmed players...")
            core.vegas_lines.apply_to_players(confirmed_players)

        # Statcast (with parallel processing)
        if core.statcast_fetcher:
            print("📊 Applying Statcast to confirmed players (parallel)...")

            # This should use your parallel fetcher
            from simple_statcast_fetcher import FastStatcastFetcher
            fetcher = FastStatcastFetcher(max_workers=5)

            # Fetch all confirmed players in parallel
            statcast_data = fetcher.fetch_multiple_players_parallel(confirmed_players)

            # Apply the data
            for player in confirmed_players:
                if player.name in statcast_data:
                    player.apply_statcast_data(statcast_data[player.name])
                    print(f"   ✅ Statcast applied to {player.name}")

        # Statistical analysis
        from enhanced_stats_engine import apply_enhanced_statistical_analysis
        apply_enhanced_statistical_analysis(confirmed_players, verbose=True)

        print(f"\n✅ Analytics applied to {len(confirmed_players)} confirmed players")

    # Try optimization with confirmed players
    print("\n🎯 OPTIMIZING WITH CONFIRMED PLAYERS...")
    core.set_optimization_mode('confirmed_only')
    lineup, score = core.optimize_lineup_with_mode()

    if lineup:
        print(f"✅ SUCCESS! Score: {score:.2f}")
        for player in lineup:
            print(f"   {player.name} ({player.primary_position}) - ${player.salary}")
    else:
        print("❌ Optimization failed - checking why...")

        # Show position coverage
        positions = {}
        for p in confirmed_players:
            positions[p.primary_position] = positions.get(p.primary_position, 0) + 1
        print(f"Confirmed player positions: {positions}")


if __name__ == "__main__":
    debug_confirmations()