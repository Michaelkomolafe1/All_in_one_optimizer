#!/usr/bin/env python3
"""DFS Optimizer Diagnostic Tool"""

from bulletproof_dfs_core import BulletproofDFSCore


def run_diagnostic(csv_file, dff_file=None):
    """Run complete diagnostic on your DFS setup"""
    print("\n🔍 DFS OPTIMIZER DIAGNOSTIC")
    print("=" * 80)

    # Initialize
    core = BulletproofDFSCore()
    core.load_draftkings_csv(csv_file)

    if dff_file:
        core.load_dff_rankings(dff_file)

    # Detect players
    core.detect_confirmed_players()

    # Get eligible players
    eligible = [p for p in core.players if p.is_eligible_for_selection(core.optimization_mode)]

    print(f"\n📊 PLAYER POOL:")
    print(f"   Total loaded: {len(core.players)}")
    print(f"   Eligible: {len(eligible)}")

    # Check data sources
    print(f"\n📈 DATA SOURCES:")

    # Check each enhancement
    for player in eligible[:5]:  # Sample first 5
        print(f"\n   {player.name} ({player.team}):")
        print(f"      Base score: {player.original_projection:.1f}")
        print(f"      Enhanced: {player.enhanced_score:.1f}")

        if hasattr(player, "recent_form") and player.recent_form:
            print(
                f"      Recent form: {player.recent_form['status']} ({player.recent_form['multiplier']:.2f}x)"
            )
        else:
            print(f"      Recent form: None")

        if hasattr(player, "batting_order"):
            print(f"      Batting order: {player.batting_order}")

        if hasattr(player, "park_factors"):
            print(f"      Park factor: {player.park_factors.get('factor', 1.0):.2f}x")


if __name__ == "__main__":
    # Run with your files
    run_diagnostic("your_dk_file.csv", "your_dff_file.csv")
