#!/usr/bin/env python3
"""
DFS Diagnostic and Fix Tool
Analyzes why MILP is failing and fixes the optimization
"""

import tempfile
import csv
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple

# Import our classes (assuming they're available)
try:
    from working_dfs_core_final import OptimizedPlayer, OptimizedDFSCore, create_enhanced_test_data

    print("✅ Successfully imported from working_dfs_core_final")
except ImportError:
    print("❌ Could not import from working_dfs_core_final")
    print("💡 Make sure working_dfs_core_final.py is in the same directory")
    exit(1)

try:
    import pulp

    MILP_AVAILABLE = True
except ImportError:
    MILP_AVAILABLE = False


def analyze_player_pool():
    """Analyze the test player pool for potential issues"""
    print("🔍 ANALYZING PLAYER POOL FOR OPTIMIZATION ISSUES")
    print("=" * 60)

    # Create test data
    dk_file, dff_file = create_enhanced_test_data()

    # Load players
    core = OptimizedDFSCore()
    core.load_draftkings_csv(dk_file)
    core.apply_dff_rankings(dff_file)
    core.enrich_with_statcast()

    players = core.players

    print(f"📊 Total players: {len(players)}")

    # Analyze by position
    print("\n📋 POSITION ANALYSIS:")
    position_analysis = {}

    for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
        eligible_players = [p for p in players if p.can_play_position(pos)]
        if eligible_players:
            salaries = [p.salary for p in eligible_players]
            scores = [p.enhanced_score for p in eligible_players]

            position_analysis[pos] = {
                'count': len(eligible_players),
                'min_salary': min(salaries),
                'max_salary': max(salaries),
                'avg_salary': sum(salaries) / len(salaries),
                'min_score': min(scores),
                'max_score': max(scores),
                'players': eligible_players
            }

            print(f"  {pos:>3}: {len(eligible_players):>2} players, "
                  f"${min(salaries):>5,}-${max(salaries):>5,} "
                  f"(avg: ${sum(salaries) / len(salaries):>5,.0f})")

    # Calculate minimum possible lineup cost
    print("\n💰 MINIMUM LINEUP COST ANALYSIS:")
    min_cost_lineup = []
    min_total_cost = 0

    requirements = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

    for pos, needed in requirements.items():
        if pos in position_analysis:
            # Get cheapest players for this position
            pos_players = position_analysis[pos]['players']
            cheapest = sorted(pos_players, key=lambda x: x.salary)[:needed]

            pos_cost = sum(p.salary for p in cheapest)
            min_total_cost += pos_cost
            min_cost_lineup.extend(cheapest)

            print(f"  {pos:>3}: {needed} × cheapest = ${pos_cost:>6,} "
                  f"({', '.join(f'${p.salary:,}' for p in cheapest)})")

    print(f"\n💡 Minimum possible lineup cost: ${min_total_cost:,}")
    print(f"💡 Budget available: $50,000")
    print(f"💡 Feasible: {'✅ YES' if min_total_cost <= 50000 else '❌ NO'}")

    if min_total_cost > 50000:
        print(f"🚨 PROBLEM: Minimum cost ({min_total_cost:,}) exceeds budget!")
        print("🔧 SOLUTION: Need to adjust test data salaries")
        return False

    # Check multi-position conflicts
    print("\n🔄 MULTI-POSITION ANALYSIS:")
    multi_pos_players = [p for p in players if p.is_multi_position()]
    print(f"  Multi-position players: {len(multi_pos_players)}")

    for player in multi_pos_players:
        positions = '/'.join(player.positions)
        print(f"    {player.name}: {positions} (${player.salary:,})")

    # Cleanup
    import os
    try:
        os.unlink(dk_file)
        os.unlink(dff_file)
    except:
        pass

    return True


def create_fixed_test_data() -> Tuple[str, str]:
    """Create test data with realistic salary ranges that ensure feasibility"""

    print("🔧 Creating FIXED test data with realistic salaries...")

    # Create temporary DraftKings CSV with LOWER salaries
    dk_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)

    # FIXED: Much lower salaries to ensure feasibility
    dk_data = [
        ['Name', 'Position', 'TeamAbbrev', 'Salary', 'AvgPointsPerGame', 'Game Info'],

        # Pitchers: $7000-$10000 range (was $8600-$11400)
        ['Hunter Brown', 'P', 'HOU', '9800', '24.56', 'HOU@TEX'],
        ['Shane Baz', 'P', 'TB', '8200', '19.23', 'TB@BOS'],
        ['Logan Gilbert', 'P', 'SEA', '7600', '18.45', 'SEA@LAA'],
        ['Freddy Peralta', 'P', 'MIL', '8800', '21.78', 'MIL@CHC'],
        ['Ronel Blanco', 'P', 'HOU', '7000', '16.89', 'HOU@TEX'],

        # Catchers: $3200-$4200 range (was $4200-$4700)
        ['William Contreras', 'C', 'MIL', '4200', '7.39', 'MIL@CHC'],
        ['Salvador Perez', 'C', 'KC', '3800', '6.85', 'KC@CLE'],
        ['Tyler Stephenson', 'C', 'CIN', '3200', '6.12', 'CIN@PIT'],

        # 1B: $3400-$4200 range (was $4000-$4800)
        ['Vladimir Guerrero Jr.', '1B', 'TOR', '4200', '7.66', 'TOR@NYY'],
        ['Pete Alonso', '1B', 'NYM', '4000', '7.23', 'NYM@ATL'],
        ['Josh Bell', '1B', 'MIA', '3600', '6.45', 'MIA@WSH'],
        ['Spencer Torkelson', '1B', 'DET', '3400', '5.89', 'DET@MIN'],
        ['Yandy Diaz', '1B/3B', 'TB', '3800', '6.78', 'TB@BOS'],  # Multi-position

        # 2B: $3600-$4000 range (was $4300-$4600)
        ['Gleyber Torres', '2B', 'NYY', '4000', '6.89', 'TOR@NYY'],
        ['Jose Altuve', '2B', 'HOU', '3900', '7.12', 'HOU@TEX'],
        ['Andres Gimenez', '2B', 'CLE', '3600', '6.34', 'KC@CLE'],

        # 3B: $3800-$4200 range (was $4600-$4800)
        ['Manny Machado', '3B', 'SD', '4200', '7.45', 'SD@LAD'],
        ['Jose Ramirez', '3B', 'CLE', '4100', '8.12', 'KC@CLE'],
        ['Alex Bregman', '3B', 'HOU', '4000', '7.23', 'HOU@TEX'],
        ['Jorge Polanco', '3B/SS', 'SEA', '3800', '6.95', 'SEA@LAA'],  # Multi-position
        ['Rafael Devers', '3B', 'BOS', '3900', '7.55', 'TB@BOS'],

        # SS: $3700-$4300 range (was $4400-$4900)
        ['Francisco Lindor', 'SS', 'NYM', '4300', '8.23', 'NYM@ATL'],
        ['Trea Turner', 'SS', 'PHI', '4100', '7.89', 'PHI@WAS'],
        ['Bo Bichette', 'SS', 'TOR', '3700', '6.67', 'TOR@NYY'],
        ['Corey Seager', 'SS', 'TEX', '4000', '7.34', 'HOU@TEX'],
        ['Xander Bogaerts', 'SS', 'SD', '3900', '7.12', 'SD@LAD'],

        # OF: $3300-$4500 range (was $4000-$5000)
        ['Kyle Tucker', 'OF', 'HOU', '4500', '8.45', 'HOU@TEX'],
        ['Christian Yelich', 'OF', 'MIL', '4200', '7.65', 'MIL@CHC'],
        ['Jarren Duran', 'OF', 'BOS', '4100', '7.89', 'TB@BOS'],
        ['Byron Buxton', 'OF', 'MIN', '3900', '7.12', 'DET@MIN'],
        ['Seiya Suzuki', 'OF', 'CHC', '3800', '6.78', 'MIL@CHC'],
        ['Jesse Winker', 'OF', 'NYM', '3600', '6.23', 'NYM@ATL'],
        ['Wilyer Abreu', 'OF', 'BOS', '3500', '6.45', 'TB@BOS'],
        ['Jackson Chourio', 'OF', 'MIL', '3400', '5.89', 'MIL@CHC'],
        ['Lane Thomas', 'OF', 'CLE', '3300', '5.67', 'KC@CLE']
    ]

    writer = csv.writer(dk_file)
    writer.writerows(dk_data)
    dk_file.close()

    # Create matching DFF CSV
    dff_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)

    dff_data = [
        ['first_name', 'last_name', 'team', 'position', 'ppg_projection', 'value_projection',
         'L5_fppg_avg', 'confirmed_order', 'implied_team_score', 'over_under'],
        ['Hunter', 'Brown', 'HOU', 'P', '26.5', '2.32', '28.2', 'YES', '5.2', '9.5'],
        ['Shane', 'Baz', 'TB', 'P', '21.8', '2.22', '19.1', 'YES', '4.8', '8.5'],
        ['Logan', 'Gilbert', 'SEA', 'P', '20.2', '2.15', '18.9', 'YES', '4.6', '8.0'],
        ['Kyle', 'Tucker', 'HOU', 'OF', '9.8', '1.96', '10.2', 'YES', '5.2', '9.5'],
        ['Christian', 'Yelich', 'MIL', 'OF', '8.9', '1.93', '9.4', 'YES', '4.9', '9.0'],
        ['Vladimir', 'Guerrero Jr.', 'TOR', '1B', '8.5', '1.77', '7.8', 'YES', '4.7', '8.5'],
        ['Francisco', 'Lindor', 'NYM', 'SS', '9.2', '1.88', '8.9', 'YES', '4.8', '8.5'],
        ['Jose', 'Ramirez', 'CLE', '3B', '9.1', '1.90', '9.8', 'YES', '4.5', '8.0'],
        ['Jorge', 'Polanco', 'SEA', '3B', '7.8', '1.73', '7.2', 'YES', '4.6', '8.0'],
        ['Jarren', 'Duran', 'BOS', 'OF', '8.7', '1.81', '9.1', 'YES', '4.8', '8.5'],
        ['William', 'Contreras', 'MIL', 'C', '8.2', '1.75', '7.9', 'YES', '4.9', '9.0'],
        ['Gleyber', 'Torres', 'NYY', '2B', '7.6', '1.69', '7.1', 'YES', '5.1', '9.0'],
        ['Yandy', 'Diaz', 'TB', '1B', '7.4', '1.72', '6.8', 'YES', '4.8', '8.5']
    ]

    writer = csv.writer(dff_file)
    writer.writerows(dff_data)
    dff_file.close()

    print("✅ Fixed test data created with realistic salary ranges")
    return dk_file.name, dff_file.name


def test_with_fixed_data():
    """Test the system with fixed, realistic data"""
    print("\n🧪 TESTING WITH FIXED DATA")
    print("=" * 50)

    dk_file, dff_file = create_fixed_test_data()

    try:
        # Import the pipeline function
        from working_dfs_core_final import load_and_optimize_complete_pipeline

        lineup, score, summary = load_and_optimize_complete_pipeline(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input="Jorge Polanco, Christian Yelich",
            contest_type='classic',
            strategy='balanced'
        )

        if lineup and score > 0:
            print(f"\n✅ SUCCESS: {len(lineup)} players, {score:.2f} score")
            print(summary)

            # Verify lineup structure
            total_salary = sum(p.salary for p in lineup)
            print(f"\n💰 Total salary: ${total_salary:,} (under $50,000: {'✅' if total_salary <= 50000 else '❌'})")

            # Position verification
            positions = {}
            for player in lineup:
                pos = player.primary_position
                positions[pos] = positions.get(pos, 0) + 1

            print(f"📊 Position distribution: {positions}")

            # Multi-position verification
            multi_pos_players = [p for p in lineup if p.is_multi_position()]
            if multi_pos_players:
                print(f"🔄 Multi-position players used: {len(multi_pos_players)}")
                for player in multi_pos_players:
                    print(f"   {player.name}: {'/'.join(player.positions)}")

            return True
        else:
            print("❌ Test failed - no lineup generated")
            return False

    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        import os
        try:
            os.unlink(dk_file)
            os.unlink(dff_file)
        except:
            pass


def create_final_fixed_core():
    """Generate the final fixed version of the core file"""
    print("\n🔧 GENERATING FINAL FIXED CORE")
    print("=" * 40)

    print("💡 The issue is that the test data has salaries that are too high.")
    print("💡 The minimum possible lineup costs more than $50,000.")
    print("")
    print("🔧 SOLUTION: Update the create_enhanced_test_data function")
    print("   to use the salary ranges from create_fixed_test_data")
    print("")
    print("📝 TO FIX:")
    print("   1. In your working_dfs_core_final.py file")
    print("   2. Replace the create_enhanced_test_data function")
    print("   3. Use the salary ranges from create_fixed_test_data above")
    print("   4. This will make the MILP feasible and greedy algorithm work")


def main():
    """Main diagnostic and testing"""
    print("🔍 DFS DIAGNOSTIC AND FIX TOOL")
    print("=" * 40)

    # Step 1: Analyze current player pool
    if not analyze_player_pool():
        print("\n🔧 Player pool has issues - testing with fixed data...")

    # Step 2: Test with fixed data
    success = test_with_fixed_data()

    if success:
        print("\n🎉 SUCCESS! Fixed data works perfectly!")
        print("💡 Update your working_dfs_core_final.py with the fixed salary ranges")
    else:
        print("\n❌ Still having issues - need deeper investigation")

    # Step 3: Provide fix instructions
    create_final_fixed_core()


if __name__ == "__main__":
    main()