#!/usr/bin/env python3
"""
CLEAN SCORING INTEGRATION
========================
Uses your existing unified scoring engine with NO fallbacks
Only real data and projections are used
"""

from bulletproof_dfs_core import BulletproofDFSCore
import os


def use_existing_scoring_only():
    """Use the existing unified scoring system without any fallbacks"""
    print("🎯 USING EXISTING SCORING SYSTEM ONLY")
    print("=" * 60)
    print("NO fallback data - only real projections and enrichments\n")

    # Initialize core
    core = BulletproofDFSCore()

    # Load CSV
    csv_path = "/home/michael/Downloads/DKSalaries(9).csv"
    if not core.load_draftkings_csv(csv_path):
        print("❌ Failed to load CSV")
        return

    print(f"✅ Loaded {len(core.players)} players")

    # Check if unified scoring engine is available
    if not hasattr(core, 'scoring_engine') or not core.scoring_engine:
        print("❌ Unified scoring engine not available")
        return

    print("✅ Unified scoring engine available")

    # Process players with REAL scoring only
    scored_players = []
    skipped_players = []

    print("\n📊 SCORING PLAYERS WITH REAL DATA ONLY:")
    print("-" * 50)

    for i, player in enumerate(core.players):
        # Check if player has base_projection (required for scoring)
        if not hasattr(player, 'base_projection') or player.base_projection <= 0:
            skipped_players.append(player)
            if i < 10:  # Show first 10 skipped
                print(f"  ⏭️ Skipping {player.name} - no base projection")
            continue

        try:
            # Use the unified scoring engine
            score = core.scoring_engine.calculate_score(player)

            # Only accept if score is valid (not a fallback)
            if score > 0 and score != player.base_projection:
                # Score was enhanced with real data
                player.enhanced_score = score
                scored_players.append(player)

                if len(scored_players) <= 5:  # Show first 5
                    improvement = ((score / player.base_projection) - 1) * 100
                    print(f"  ✅ {player.name}: {player.base_projection:.1f} → {score:.1f} (+{improvement:.1f}%)")
            else:
                # No real enrichment data available
                player.enhanced_score = player.base_projection
                scored_players.append(player)

                if len(scored_players) <= 5:
                    print(f"  ⚠️ {player.name}: {player.base_projection:.1f} (no enrichments)")

        except Exception as e:
            print(f"  ❌ Error scoring {player.name}: {e}")
            skipped_players.append(player)

    print(f"\n📊 SCORING SUMMARY:")
    print(f"  ✅ Scored: {len(scored_players)} players")
    print(f"  ⏭️ Skipped: {len(skipped_players)} players (no projections)")

    # Only optimize if we have enough players
    if len(scored_players) < 10:
        print("\n❌ Not enough players with valid scores for optimization")
        return

    # Run MILP optimization with REAL scores only
    print("\n🎯 RUNNING MILP OPTIMIZATION WITH REAL SCORES:")
    print("-" * 50)

    if hasattr(core, 'unified_optimizer') and core.unified_optimizer:
        try:
            # For showdown
            if any(hasattr(p, 'roster_position') and 'CPT' in str(p.roster_position) for p in scored_players):
                print("Running SHOWDOWN optimization...")
                lineup = core.unified_optimizer.optimize_showdown(scored_players)
            else:
                print("Running CLASSIC optimization...")
                lineup = core.unified_optimizer.optimize_classic(scored_players)

            if lineup:
                display_real_lineup(lineup)
            else:
                print("❌ Optimization failed")

        except Exception as e:
            print(f"❌ Optimization error: {e}")
    else:
        print("❌ Unified optimizer not available")


def display_real_lineup(lineup):
    """Display lineup with REAL scores only"""
    print(f"\n🏆 OPTIMIZED LINEUP (REAL DATA ONLY)")
    print("=" * 60)

    total_salary = 0
    total_score = 0

    for i, player in enumerate(lineup):
        # Determine if captain (showdown)
        is_captain = getattr(player, 'is_captain', False)
        multiplier = 1.5 if is_captain else 1.0

        player_salary = player.salary * multiplier if is_captain else player.salary
        player_score = player.enhanced_score * multiplier

        total_salary += player_salary
        total_score += player_score

        role = "CPT" if is_captain else f"UTIL{i}"

        print(f"{role}: {player.name} ({player.team})")
        print(f"     Salary: ${int(player_salary):,}")
        print(f"     Score: {player_score:.1f} pts")

        # Show if score was enhanced
        if hasattr(player, 'base_projection'):
            base_score = player.base_projection * multiplier
            if player_score > base_score:
                improvement = ((player_score / base_score) - 1) * 100
                print(f"     Enhanced: +{improvement:.1f}%")

    print(f"\n📊 TOTALS:")
    print(f"   Salary: ${int(total_salary):,} / $50,000")
    print(f"   Score: {total_score:.1f} pts")


def fix_projection_attribute():
    """Quick fix to add projection property to UnifiedPlayer"""
    try:
        from unified_player_model import UnifiedPlayer

        # Check if already has projection
        test_player = UnifiedPlayer(
            id="test", name="Test", team="TEST",
            salary=5000, primary_position="OF",
            positions=["OF"], base_projection=10.0
        )

        if not hasattr(test_player, 'projection'):
            # Add projection property
            UnifiedPlayer.projection = property(
                lambda self: self.base_projection,
                lambda self, value: setattr(self, 'base_projection', value)
            )
            print("✅ Added projection property to UnifiedPlayer")
        else:
            print("✅ UnifiedPlayer already has projection property")

    except Exception as e:
        print(f"⚠️ Could not patch UnifiedPlayer: {e}")


if __name__ == "__main__":
    # Try to fix projection attribute first
    fix_projection_attribute()

    # Run the clean scoring
    use_existing_scoring_only()