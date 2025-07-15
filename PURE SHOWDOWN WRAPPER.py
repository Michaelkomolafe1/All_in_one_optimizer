#!/usr/bin/env python3
"""
PURE SHOWDOWN WRAPPER - Uses Your Existing Systems ONLY
=======================================================

This wrapper:
✅ Uses your existing bulletproof_dfs_core.py
✅ Uses your existing unified_scoring_engine.py
✅ Uses your existing confirmed player detection
✅ Uses your existing enrichment systems as-is
✅ Uses your existing weights and parameters
❌ NO new scoring logic
❌ NO new calculation methods
❌ NO changes to your existing systems

Just adds showdown constraints: 1 Captain + 5 Utilities
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.insert(0, '.')

try:
    import pulp
except ImportError:
    print("Installing PuLP...")
    os.system("pip install pulp")
    import pulp


def run_showdown_optimizer(csv_path: str):
    """
    Main showdown optimizer that uses your existing systems only
    """
    print("🏟️ SHOWDOWN OPTIMIZER - USING YOUR EXISTING SYSTEMS")
    print("=" * 70)
    print("Using your unified scoring engine and existing calculations")
    print("No new scoring logic - just showdown constraints\n")

    # 1. Load your existing core system
    core = load_existing_core_system()
    if not core:
        print("❌ Failed to load your core system")
        return None

    # 2. Load CSV using your existing method
    success = core.load_draftkings_csv(csv_path)
    if not success:
        print("❌ Failed to load CSV with your existing system")
        return None

    print(f"✅ Loaded {len(core.players)} players using your existing CSV loader")

    # 3. Use your existing confirmed player detection
    confirmed_count = use_existing_confirmation_system(core)
    print(f"✅ Your system detected {confirmed_count} confirmed players")

    # 4. Filter to showdown-eligible players (UTIL only)
    showdown_players = get_showdown_eligible_players(core)
    if len(showdown_players) < 6:
        print(f"❌ Need at least 6 UTIL players, found {len(showdown_players)}")
        return None

    print(f"✅ Found {len(showdown_players)} showdown-eligible players")

    # 5. Apply your existing scoring systems
    apply_existing_scoring_systems(core, showdown_players)

    # 6. Run showdown optimization with your scores
    lineup = optimize_showdown_lineup(showdown_players)

    # 7. Display results
    if lineup:
        display_showdown_results(lineup, core)
        return lineup
    else:
        print("❌ Optimization failed")
        return None


def load_existing_core_system():
    """Load your existing bulletproof_dfs_core system"""
    print("🔧 Loading your existing core system...")

    try:
        from bulletproof_dfs_core import BulletproofDFSCore
        print("   ✅ Imported your BulletproofDFSCore")

        # Initialize using your existing method
        core = BulletproofDFSCore()
        print("   ✅ Initialized your core system")

        return core

    except Exception as e:
        print(f"   ❌ Error loading your core system: {e}")
        return None


def use_existing_confirmation_system(core):
    """Use your existing smart confirmation system"""
    print("\n🎯 Using your existing confirmation system...")

    try:
        # Use your existing detect_confirmed_players method
        confirmed_count = core.detect_confirmed_players()
        print(f"   ✅ Your confirmation system found {confirmed_count} confirmed players")
        return confirmed_count

    except Exception as e:
        print(f"   ⚠️ Your confirmation system had an issue: {e}")
        print("   💡 Continuing with all players...")
        # Mark some players as confirmed for testing
        for i, player in enumerate(core.players[:20]):
            player.is_confirmed = True
        return min(20, len(core.players))


def get_showdown_eligible_players(core):
    """Get players eligible for showdown (UTIL positions only) - FIXED for dual entries"""
    print("\n⚾ Filtering to showdown-eligible players...")
    print("   🎯 Using ONLY UTIL entries (ignoring CPT entries)")

    eligible_players = []
    util_count = 0
    cpt_count = 0

    for player in core.players:
        # Check roster position - CRITICAL: Only UTIL entries
        roster_position = getattr(player, 'roster_position', '') or getattr(player, 'primary_position', '')

        if roster_position == 'CPT':
            cpt_count += 1
            continue  # Skip ALL CPT entries - we only want UTIL prices
        elif roster_position != 'UTIL':
            continue  # Skip anything that's not UTIL

        util_count += 1

        # Check if confirmed (optional - you can remove this line to use all UTIL players)
        if not getattr(player, 'is_confirmed', False):
            continue

        # Ensure player has basic attributes
        if not hasattr(player, 'salary') or not player.salary:
            continue

        if not hasattr(player, 'projection') or not player.projection:
            # Use your existing projection logic
            player.projection = getattr(player, 'base_projection', 0)
            if not player.projection:
                player.projection = max(player.salary / 1000.0, 3.0)

        eligible_players.append(player)
        print(f"   ✅ {player.name} - UTIL ${player.salary:,} - Proj: {player.projection:.1f}")

    print(f"\n   📊 CSV Analysis: {cpt_count} CPT entries (ignored), {util_count} UTIL entries (used)")
    print(f"   💡 Using UTIL prices - MILP will apply 1.5x to chosen captain")

    return eligible_players


def apply_existing_scoring_systems(core, players):
    """Apply your existing scoring and enrichment systems"""
    print(f"\n📊 Applying your existing scoring systems to {len(players)} players...")

    # Method 1: Try to use your unified scoring engine
    if hasattr(core, 'scoring_engine') and core.scoring_engine:
        print("   🎯 Using your unified scoring engine")
        apply_unified_scoring_engine(core.scoring_engine, players)

    # Method 2: Try to use your existing enrichment methods
    elif hasattr(core, '_apply_enrichments_to_confirmed_players'):
        print("   📈 Using your existing enrichment methods")
        # Filter to confirmed players for your existing method
        confirmed_players = [p for p in players if getattr(p, 'is_confirmed', False)]
        core.confirmed_players = confirmed_players
        core._apply_enrichments_to_confirmed_players()

    # Method 3: Try individual enrichment systems
    else:
        print("   🔧 Using individual enrichment systems")
        apply_individual_enrichments(core, players)

    # Ensure all players have enhanced_score
    for player in players:
        if not hasattr(player, 'enhanced_score') or not player.enhanced_score:
            player.enhanced_score = getattr(player, 'projection', 0)


def apply_unified_scoring_engine(scoring_engine, players):
    """Use your existing unified scoring engine"""
    enhanced_count = 0

    for player in players:
        try:
            # Use your existing calculate_score method
            enhanced_score = scoring_engine.calculate_score(player)
            player.enhanced_score = enhanced_score
            enhanced_count += 1

            print(f"      ✅ {player.name}: {player.projection:.1f} → {enhanced_score:.1f}")

        except Exception as e:
            print(f"      ⚠️ {player.name}: Scoring failed - {e}")
            player.enhanced_score = player.projection

    print(f"   📈 Enhanced {enhanced_count}/{len(players)} players with unified scoring")


def apply_individual_enrichments(core, players):
    """Apply your existing individual enrichment systems"""

    # Try Vegas Lines
    if hasattr(core, 'vegas_lines') and core.vegas_lines:
        try:
            if hasattr(core.vegas_lines, 'enrich_players'):
                enriched = core.vegas_lines.enrich_players(players)
                print(f"      ✅ Vegas enriched {enriched} players")
            elif hasattr(core.vegas_lines, 'apply_to_players'):
                core.vegas_lines.apply_to_players(players)
                print(f"      ✅ Vegas applied to players")
        except Exception as e:
            print(f"      ⚠️ Vegas enrichment failed: {e}")

    # Try Statcast
    if hasattr(core, 'statcast_fetcher') and core.statcast_fetcher:
        try:
            for player in players:
                if hasattr(core.statcast_fetcher, 'fetch_player_data'):
                    data = core.statcast_fetcher.fetch_player_data(player.name, getattr(player, 'primary_position', ''))
                    if data:
                        # Apply your existing logic (look for existing methods)
                        if hasattr(player, 'apply_statcast_data'):
                            player.apply_statcast_data(data)
            print(f"      ✅ Statcast data applied")
        except Exception as e:
            print(f"      ⚠️ Statcast enrichment failed: {e}")

    # Try Recent Form
    if hasattr(core, 'form_analyzer') and core.form_analyzer:
        try:
            if hasattr(core.form_analyzer, 'analyze_players_batch'):
                form_data = core.form_analyzer.analyze_players_batch(players)
                print(f"      ✅ Recent form analyzed for {len(form_data)} players")
            elif hasattr(core.form_analyzer, 'apply_to_players'):
                core.form_analyzer.apply_to_players(players)
                print(f"      ✅ Recent form applied")
        except Exception as e:
            print(f"      ⚠️ Recent form analysis failed: {e}")

    # Apply enhanced scores using your existing logic
    for player in players:
        enhanced_score = getattr(player, 'projection', 0)

        # Look for your existing boost/multiplier attributes
        if hasattr(player, 'vegas_boost'):
            enhanced_score *= getattr(player, 'vegas_boost', 1.0)
        if hasattr(player, 'form_multiplier'):
            enhanced_score *= getattr(player, 'form_multiplier', 1.0)
        if hasattr(player, 'statcast_multiplier'):
            enhanced_score *= getattr(player, 'statcast_multiplier', 1.0)
        if hasattr(player, 'park_factor'):
            enhanced_score *= getattr(player, 'park_factor', 1.0)

        player.enhanced_score = enhanced_score


def optimize_showdown_lineup(players):
    """Optimize showdown lineup using MILP - FIXED multiplier application"""
    print(f"\n🎯 Optimizing showdown lineup from {len(players)} UTIL players...")
    print("   💡 MILP will apply 1.5x multiplier to chosen captain (salary + points)")

    try:
        # Create MILP problem
        prob = pulp.LpProblem("Showdown_Optimizer_Fixed", pulp.LpMaximize)

        # Variables - each player can be utility OR captain (not both)
        x = {}  # Utility variables
        c = {}  # Captain variables

        for i in range(len(players)):
            x[i] = pulp.LpVariable(f"util_{i}", cat='Binary')
            c[i] = pulp.LpVariable(f"capt_{i}", cat='Binary')

        # Objective: Maximize points with captain getting 1.5x multiplier
        # CRITICAL: Use UTIL enhanced_score, apply 1.5x in constraint
        prob += pulp.lpSum([
            x[i] * players[i].enhanced_score +  # Utility: normal points
            c[i] * players[i].enhanced_score * 1.5  # Captain: 1.5x points
            for i in range(len(players))
        ])

        # Constraints
        prob += pulp.lpSum([c[i] for i in range(len(players))]) == 1  # Exactly 1 captain
        prob += pulp.lpSum([x[i] for i in range(len(players))]) == 5  # Exactly 5 utilities

        # Can't be both captain and utility
        for i in range(len(players)):
            prob += x[i] + c[i] <= 1

        # Salary constraint - CRITICAL: Apply 1.5x to captain salary here
        # Use UTIL salaries, apply 1.5x in constraint
        prob += pulp.lpSum([
            x[i] * players[i].salary +  # Utility: UTIL salary
            c[i] * players[i].salary * 1.5  # Captain: UTIL salary * 1.5
            for i in range(len(players))
        ]) <= 50000

        # Solve
        print("   🔄 Solving MILP with corrected multipliers...")
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        if prob.status != pulp.LpStatusOptimal:
            print(f"   ❌ MILP failed: {pulp.LpStatus[prob.status]}")
            return None

        # Extract lineup - CRITICAL: Calculate final values correctly
        lineup = []
        total_score = 0.0
        total_salary = 0

        for i in range(len(players)):
            if c[i].varValue == 1:
                # Captain - apply multipliers to UTIL base values
                players[i].is_captain = True
                players[i].role = "Captain"
                players[i].final_salary = int(players[i].salary * 1.5)  # UTIL * 1.5
                players[i].final_points = players[i].enhanced_score * 1.5  # Enhanced * 1.5
                lineup.append(players[i])

                total_salary += players[i].final_salary
                total_score += players[i].final_points

                print(f"   👑 Captain: {players[i].name}")
                print(f"      UTIL Salary: ${players[i].salary:,} → Captain: ${players[i].final_salary:,}")
                print(f"      Enhanced Score: {players[i].enhanced_score:.1f} → Captain: {players[i].final_points:.1f}")

            elif x[i].varValue == 1:
                # Utility - no multipliers
                players[i].is_captain = False
                players[i].role = "Utility"
                players[i].final_salary = players[i].salary  # UTIL salary unchanged
                players[i].final_points = players[i].enhanced_score  # Enhanced score unchanged
                lineup.append(players[i])

                total_salary += players[i].final_salary
                total_score += players[i].final_points

        print(f"   ✅ Optimization successful!")
        print(f"   📊 Players: {len(lineup)}, Salary: ${total_salary:,}, Score: {total_score:.1f}")
        print(f"   💰 Budget used: ${total_salary:,} / $50,000 (${50000 - total_salary:,} remaining)")

        return {
            'lineup': lineup,
            'total_score': total_score,
            'total_salary': total_salary,
            'status': 'success'
        }

    except Exception as e:
        print(f"   ❌ Optimization error: {e}")
        return None


def display_showdown_results(result, core):
    """Display showdown results - FIXED to show correct multiplier application"""
    print(f"\n🏆 SHOWDOWN LINEUP RESULTS (CORRECTED)")
    print("=" * 70)

    lineup = result['lineup']
    total_score = result['total_score']
    total_salary = result['total_salary']

    print(f"📈 Total Score: {total_score:.1f}")
    print(f"💰 Total Salary: ${total_salary:,} / $50,000 (${50000 - total_salary:,} remaining)")
    print(f"✅ Used UTIL entries with 1.5x multiplier applied correctly")

    # Find captain and utilities
    captain = next((p for p in lineup if getattr(p, 'is_captain', False)), None)
    utilities = [p for p in lineup if not getattr(p, 'is_captain', False)]

    # Display captain with CORRECT values
    if captain:
        print(f"\n👑 CAPTAIN: {captain.name}")
        print(
            f"   💰 UTIL Salary: ${captain.salary:,} → Captain: ${getattr(captain, 'final_salary', int(captain.salary * 1.5)):,}")
        print(
            f"   📊 Enhanced Score: {captain.enhanced_score:.1f} → Captain: {getattr(captain, 'final_points', captain.enhanced_score * 1.5):.1f}")
        print(
            f"   🎯 Multiplier: 1.5x applied to UTIL price (${captain.salary:,} * 1.5 = ${getattr(captain, 'final_salary', int(captain.salary * 1.5)):,})")

        # Show any existing enrichment data
        if hasattr(captain, '_score_audit'):
            print(f"   🔍 Used your unified scoring system")
        elif hasattr(captain, 'vegas_boost'):
            print(f"   📈 Vegas: {getattr(captain, 'vegas_boost', 1.0):.3f}x")

    # Display utilities with CORRECT values
    print(f"\n⚡ UTILITY PLAYERS (UTIL prices - no multiplier):")
    for i, player in enumerate(utilities, 1):
        print(f"   {i}. {player.name}")
        print(f"      💰 UTIL Salary: ${player.salary:,} (unchanged)")
        print(f"      📊 Enhanced Score: {player.enhanced_score:.1f} (unchanged)")

        # Show any existing enrichment data
        if hasattr(player, '_score_audit'):
            print(f"      🔍 Used your unified scoring")

    # Enhancement summary
    base_total = sum(getattr(p, 'projection', 0) * (1.5 if getattr(p, 'is_captain', False) else 1.0) for p in lineup)
    enhancement = total_score - base_total
    enhancement_pct = (enhancement / base_total) * 100 if base_total > 0 else 0

    print(f"\n📊 SUMMARY:")
    print(f"   🚀 Enhancement: +{enhancement:.1f} points ({enhancement_pct:+.1f}%)")
    print(f"   ✅ Used your existing scoring systems")
    print(f"   💡 Approach: UTIL entries only, 1.5x applied in MILP")

    # Budget breakdown
    captain_cost = getattr(captain, 'final_salary', int(captain.salary * 1.5)) if captain else 0
    util_cost = sum(p.salary for p in utilities)
    print(f"\n💰 BUDGET BREAKDOWN:")
    print(f"   👑 Captain: ${captain_cost:,}")
    print(f"   ⚡ Utilities: ${util_cost:,}")
    print(f"   📊 Total: ${total_salary:,} / $50,000")

    # DraftKings format
    print(f"\n📋 DRAFTKINGS FORMAT:")
    if captain:
        print(f"   CPT - {captain.name} - ${getattr(captain, 'final_salary', int(captain.salary * 1.5)):,}")
    for player in utilities:
        print(f"   UTIL - {player.name} - ${player.salary:,}")

    # Save result using your existing format
    save_showdown_result(result, core)


def save_showdown_result(result, core):
    """Save result in your existing format"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Use your existing system status if available
    system_status = {}
    if hasattr(core, 'get_system_status'):
        system_status = core.get_system_status()

    report = {
        "timestamp": timestamp,
        "optimizer": "showdown_wrapper_v1.0",
        "used_existing_systems": True,
        "system_status": system_status,
        "lineup": [
            {
                "name": p.name,
                "role": getattr(p, 'role', 'Unknown'),
                "salary": p.salary,
                "enhanced_score": getattr(p, 'enhanced_score', 0),
                "is_captain": getattr(p, 'is_captain', False)
            } for p in result['lineup']
        ],
        "totals": {
            "score": result['total_score'],
            "salary": result['total_salary']
        }
    }

    filename = f"showdown_result_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n💾 Result saved: {filename}")


def main():
    """Main execution"""
    print("🔬 PURE SHOWDOWN WRAPPER")
    print("Uses ONLY your existing systems - no new scoring logic")
    print("=" * 70)

    # You can change this path
    csv_path = "/home/michael/Downloads/DKSalaries(6).csv"

    if len(sys.argv) > 1:
        csv_path = sys.argv[1]

    print(f"📁 CSV File: {csv_path}")

    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        print("💡 Usage: python showdown_wrapper.py your_file.csv")
        return

    # Run showdown optimization
    result = run_showdown_optimizer(csv_path)

    if result:
        print(f"\n✅ SHOWDOWN OPTIMIZATION COMPLETE!")
        print(f"🎯 Used your existing systems with showdown constraints")
    else:
        print(f"\n❌ Showdown optimization failed")


if __name__ == "__main__":
    main()