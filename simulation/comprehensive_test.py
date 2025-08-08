#!/usr/bin/env python3
"""
WORKING OPTIMIZER TEST
Using the CORRECT class name: UnifiedCoreSystem
"""

import sys
import os
import numpy as np
from collections import defaultdict

# Setup paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
# CRITICAL: Add main_optimizer to path so the direct imports work
sys.path.insert(0, os.path.join(project_root, 'main_optimizer'))

print("Importing your optimizer with CORRECT class name...")

# This is the correct import based on your setup
try:
    # Import from main_optimizer with the directory in path
    from unified_core_system_updated import UnifiedCoreSystem

    print("✅ Successfully imported UnifiedCoreSystem!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"Project root: {project_root}")
    print(f"Sys path: {sys.path[:3]}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Import the realistic simulator for testing
try:
    from unified_player_model import UnifiedPlayer

    print("✅ Successfully imported UnifiedPlayer!")
except ImportError:
    print("⚠️ UnifiedPlayer not found, using simplified test data")


    # Fallback test data generator
    class UnifiedPlayer:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


def analyze_lineup(lineup, contest_type):
    """Analyze a single lineup for key metrics"""
    # Handle both dict and object formats
    if lineup and isinstance(lineup[0], dict):
        # Lineup is a list of dicts
        analysis = {
            'total_salary': sum(p['salary'] for p in lineup),
            'total_projection': sum(p.get('projection', 0) for p in lineup),
            'teams': defaultdict(list),
            'positions': defaultdict(int),
            'avg_ownership': sum(p.get('ownership_projection', p.get('ownership', 0)) for p in lineup) / len(
                lineup) if lineup else 0
        }

        # Group by team
        for player in lineup:
            analysis['teams'][player['team']].append(player)
            analysis['positions'][player['position']] += 1

        # Find largest stack
        max_stack_size = max(len(players) for players in analysis['teams'].values()) if analysis['teams'] else 0
        analysis['max_stack_size'] = max_stack_size
        analysis['max_stack_team'] = max(analysis['teams'].items(), key=lambda x: len(x[1]))[0] if analysis[
            'teams'] else None

        # Check consecutive batting orders in largest stack
        if analysis['max_stack_team']:
            stack_players = analysis['teams'][analysis['max_stack_team']]
            batting_orders = sorted([p.get('batting_order') for p in stack_players
                                     if p['position'] != 'P' and p.get('batting_order') and p.get('batting_order') > 0])

            consecutive = False
            if len(batting_orders) >= 2:
                consecutive_count = 1
                for i in range(1, len(batting_orders)):
                    if batting_orders[i] == batting_orders[i - 1] + 1:
                        consecutive_count += 1
                    else:
                        consecutive_count = 1
                    if consecutive_count >= 3:
                        consecutive = True
                        break

            analysis['has_consecutive_stack'] = consecutive
            analysis['batting_orders'] = batting_orders
    else:
        # Lineup is a list of objects
        analysis = {
            'total_salary': sum(p.salary for p in lineup),
            'total_projection': sum(getattr(p, 'projection', 0) for p in lineup),
            'teams': defaultdict(list),
            'positions': defaultdict(int),
            'avg_ownership': sum(getattr(p, 'ownership_projection', getattr(p, 'ownership', 0)) for p in lineup) / len(
                lineup) if lineup else 0
        }

        # Group by team
        for player in lineup:
            analysis['teams'][player.team].append(player)
            analysis['positions'][player.position] += 1

        # Find largest stack
        max_stack_size = max(len(players) for players in analysis['teams'].values()) if analysis['teams'] else 0
        analysis['max_stack_size'] = max_stack_size
        analysis['max_stack_team'] = max(analysis['teams'].items(), key=lambda x: len(x[1]))[0] if analysis[
            'teams'] else None

        # Check consecutive batting orders in largest stack
        if analysis['max_stack_team']:
            stack_players = analysis['teams'][analysis['max_stack_team']]
            batting_orders = sorted([getattr(p, 'batting_order', None) for p in stack_players
                                     if hasattr(p,
                                                'batting_order') and p.position != 'P' and p.batting_order and p.batting_order > 0])

            consecutive = False
            if len(batting_orders) >= 2:
                consecutive_count = 1
                for i in range(1, len(batting_orders)):
                    if batting_orders[i] == batting_orders[i - 1] + 1:
                        consecutive_count += 1
                    else:
                        consecutive_count = 1
                    if consecutive_count >= 3:
                        consecutive = True
                        break

            analysis['has_consecutive_stack'] = consecutive
            analysis['batting_orders'] = batting_orders

    return analysis


def run_comprehensive_test():
    """Run full analysis of your optimizer"""
    print("=" * 80)
    print("COMPREHENSIVE OPTIMIZER ANALYSIS")
    print("=" * 80)

    # Initialize system
    print("\n📋 Initializing your optimizer...")
    system = UnifiedCoreSystem()
    print("✅ System initialized")

    # Create and load test slate
    print("🎲 Creating test slate with enough players for all positions...")

    # Import your UnifiedPlayer class
    from unified_player_model import UnifiedPlayer

    # Create test players using YOUR UnifiedPlayer format
    test_players = []
    teams = ['NYY', 'BOS', 'HOU', 'LAD', 'ATL', 'SD', 'TB', 'TOR']

    # CRITICAL: Create enough players for each position
    # Need: 2P, 1C, 1-1B, 1-2B, 1-3B, 1-SS, 3-OF minimum per lineup

    for team_idx, team in enumerate(teams):
        opponent = teams[(team_idx + 1) % len(teams)]

        # Create 3 pitchers per team (need options)
        for p_idx in range(3):
            pitcher = UnifiedPlayer(
                name=f"{team}_P{p_idx}",
                position='P',
                team=team,
                salary=np.random.randint(7000, 11000),
                opponent=opponent,
                player_id=f"{team}_P{p_idx}_id",
                base_projection=np.random.uniform(15, 25)
            )
            pitcher.ownership = np.random.uniform(10, 45)
            pitcher.k_rate = np.random.uniform(20, 35)
            pitcher.confirmed = False
            pitcher.manual_exposure = 0
            test_players.append(pitcher)

        # Create 2 catchers per team
        for c_idx in range(2):
            catcher = UnifiedPlayer(
                name=f"{team}_C{c_idx}",
                position='C',
                team=team,
                salary=np.random.randint(2500, 4500),
                opponent=opponent,
                player_id=f"{team}_C{c_idx}_id",
                base_projection=np.random.uniform(5, 12)
            )
            catcher.ownership = np.random.uniform(5, 25)
            catcher.batting_order = 7 + c_idx
            catcher.confirmed = False
            catcher.manual_exposure = 0
            test_players.append(catcher)

        # Create infielders (2 of each position per team)
        for pos in ['1B', '2B', '3B', 'SS']:
            for idx in range(2):
                infielder = UnifiedPlayer(
                    name=f"{team}_{pos}{idx}",
                    position=pos,
                    team=team,
                    salary=np.random.randint(3000, 5500),
                    opponent=opponent,
                    player_id=f"{team}_{pos}{idx}_id",
                    base_projection=np.random.uniform(6, 15)
                )
                infielder.ownership = np.random.uniform(5, 35)
                infielder.batting_order = idx + 1 if idx < 5 else idx + 4
                infielder.confirmed = False
                infielder.manual_exposure = 0
                test_players.append(infielder)

        # Create 5 outfielders per team (need at least 3)
        for of_idx in range(5):
            outfielder = UnifiedPlayer(
                name=f"{team}_OF{of_idx}",
                position='OF',
                team=team,
                salary=np.random.randint(2800, 5800),
                opponent=opponent,
                player_id=f"{team}_OF{of_idx}_id",
                base_projection=np.random.uniform(7, 16)
            )
            outfielder.ownership = np.random.uniform(5, 40)
            outfielder.batting_order = of_idx + 1 if of_idx < 5 else of_idx + 4
            outfielder.confirmed = False
            outfielder.manual_exposure = 0
            test_players.append(outfielder)

    print(f"✅ Created {len(test_players)} test players")

    # Count by position
    position_counts = {}
    for p in test_players:
        position_counts[p.position] = position_counts.get(p.position, 0) + 1
    print(f"   Position distribution: {position_counts}")

    # Load players - use BOTH methods since direct assignment works
    print("📥 Loading players into system...")

    # Method 1: build_player_pool (might not work)
    system.build_player_pool(test_players)

    # Method 2: Direct assignment (this works!)
    system.players = test_players
    system.player_pool = test_players

    # Verify loading
    pool_size = len(system.player_pool) if hasattr(system, 'player_pool') and system.player_pool else 0
    players_size = len(system.players) if hasattr(system, 'players') and system.players else 0
    print(f"✅ Loaded: player_pool={pool_size}, players={players_size}")

    # Test GPP lineups
    print("\n" + "=" * 60)
    print("GPP LINEUP ANALYSIS (5 lineups)")
    print("=" * 60)

    gpp_analyses = []
    for i in range(5):
        try:
            print(f"\nGenerating GPP lineup {i + 1}...")
            result = system.optimize_lineup('gpp')

            # Handle your specific format: list with dict containing 'players'
            lineup = None
            if result:
                if isinstance(result, list) and len(result) > 0:
                    # Your format: [{'players': [...], 'score': ...}]
                    lineup = result[0].get('players', [])
                elif isinstance(result, dict):
                    lineup = result.get('players', result.get('lineup', result))
                else:
                    lineup = result

            if lineup:
                analysis = analyze_lineup(lineup, 'gpp')
                gpp_analyses.append(analysis)

                print(f"📊 GPP Lineup {i + 1}:")
                print(f"  💰 Salary: ${analysis['total_salary']:,}")
                print(f"  📈 Projection: {analysis['total_projection']:.1f}")
                print(f"  🎯 Max Stack: {analysis['max_stack_size']} players from {analysis['max_stack_team']}")
                print(f"  🔢 Consecutive: {'YES ✅' if analysis.get('has_consecutive_stack') else 'NO ❌'}")
                if analysis.get('batting_orders'):
                    print(f"  📋 Batting Orders: {analysis['batting_orders']}")
                print(f"  👥 Avg Ownership: {analysis['avg_ownership']:.1f}%")
        except Exception as e:
            print(f"❌ Error generating GPP lineup {i + 1}: {e}")
            import traceback
            traceback.print_exc()

    # Test Cash lineups
    print("\n" + "=" * 60)
    print("CASH LINEUP ANALYSIS (5 lineups)")
    print("=" * 60)

    cash_analyses = []
    for i in range(5):
        try:
            print(f"\nGenerating Cash lineup {i + 1}...")
            result = system.optimize_lineup('cash')

            # Handle your specific format: list with dict containing 'players'
            lineup = None
            if result:
                if isinstance(result, list) and len(result) > 0:
                    # Your format: [{'players': [...], 'score': ...}]
                    lineup = result[0].get('players', [])
                elif isinstance(result, dict):
                    lineup = result.get('players', result.get('lineup', result))
                else:
                    lineup = result

            if lineup:
                analysis = analyze_lineup(lineup, 'cash')
                cash_analyses.append(analysis)

                print(f"💵 Cash Lineup {i + 1}:")
                print(f"  💰 Salary: ${analysis['total_salary']:,}")
                print(f"  📈 Projection: {analysis['total_projection']:.1f}")
                print(f"  🎯 Max Team Exposure: {analysis['max_stack_size']} players")
                print(f"  👥 Avg Ownership: {analysis['avg_ownership']:.1f}%")
        except Exception as e:
            print(f"❌ Error generating Cash lineup {i + 1}: {e}")
            import traceback
            traceback.print_exc()

    # Summary Statistics
    print("\n" + "=" * 80)
    print("📊 SUMMARY STATISTICS")
    print("=" * 80)

    if gpp_analyses:
        print("\n🎯 GPP Performance:")
        stack_sizes = [a['max_stack_size'] for a in gpp_analyses]
        print(f"  • Average stack size: {sum(stack_sizes) / len(stack_sizes):.1f}")
        print(
            f"  • Lineups with 4+ stacks: {sum(1 for s in stack_sizes if s >= 4)}/{len(stack_sizes)} ({sum(1 for s in stack_sizes if s >= 4) / len(stack_sizes) * 100:.0f}%)")
        print(
            f"  • Lineups with consecutive stacks: {sum(1 for a in gpp_analyses if a.get('has_consecutive_stack'))}/{len(gpp_analyses)} ({sum(1 for a in gpp_analyses if a.get('has_consecutive_stack')) / len(gpp_analyses) * 100:.0f}%)")
        avg_salary = sum(a['total_salary'] for a in gpp_analyses) / len(gpp_analyses)
        print(f"  • Average salary used: ${avg_salary:,.0f} ({avg_salary / 500:.1f}%)")

    if cash_analyses:
        print("\n💰 Cash Performance:")
        exposures = [a['max_stack_size'] for a in cash_analyses]
        print(f"  • Average max team exposure: {sum(exposures) / len(exposures):.1f}")
        print(
            f"  • Lineups with 4+ from same team: {sum(1 for e in exposures if e >= 4)}/{len(exposures)} ({sum(1 for e in exposures if e >= 4) / len(exposures) * 100:.0f}%)")
        avg_salary = sum(a['total_salary'] for a in cash_analyses) / len(cash_analyses)
        print(f"  • Average salary used: ${avg_salary:,.0f} ({avg_salary / 500:.1f}%)")

    # Recommendations
    print("\n" + "=" * 80)
    print("🔧 RECOMMENDATIONS BASED ON ANALYSIS")
    print("=" * 80)

    issues = []

    if gpp_analyses:
        stack_sizes = [a['max_stack_size'] for a in gpp_analyses]
        # Check GPP stacking
        stack_pct = sum(1 for s in stack_sizes if s >= 4) / len(stack_sizes) * 100
        if stack_pct < 80:
            issues.append(f"❌ GPP stacking too low ({stack_pct:.0f}% vs 80% target)")
            issues.append("   FIX: Increase correlation bonuses in apply_correlation_bonuses()")

        # Check consecutive batting
        consec_pct = sum(1 for a in gpp_analyses if a.get('has_consecutive_stack')) / len(gpp_analyses) * 100
        if consec_pct < 75:
            issues.append(f"❌ Consecutive batting order too low ({consec_pct:.0f}% vs 75% target)")
            issues.append("   FIX: Add consecutive batting order constraint to MILP")

    if cash_analyses:
        exposures = [a['max_stack_size'] for a in cash_analyses]
        # Check cash correlation
        over_exposed = sum(1 for e in exposures if e >= 4) / len(exposures) * 100
        if over_exposed > 20:
            issues.append(f"❌ Cash over-correlation ({over_exposed:.0f}% have 4+ from same team)")
            issues.append("   FIX: Set max_players_per_team = 3 for cash games")

    if issues:
        print("\n🔴 Issues Found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ Optimizer performing well! Consider fine-tuning:")
        print("  • Experiment with ownership thresholds")
        print("  • Adjust projection weights")
        print("  • Test different correlation strategies")

    return gpp_analyses, cash_analyses


if __name__ == "__main__":
    try:
        gpp_results, cash_results = run_comprehensive_test()

        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE!")
        print("=" * 80)
        print("\nBased on these results, you should:")
        print("1. Fix any ❌ issues identified above")
        print("2. Re-run this test after making changes")
        print("3. Compare before/after metrics")
        print("\nSave this output for comparison!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()