#!/usr/bin/env python3
"""Test stacking with correlation bonuses"""

import sys
import pandas as pd

sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

from main_optimizer.unified_milp_optimizer import UnifiedMILPOptimizer
from main_optimizer.unified_player_model import UnifiedPlayer
from main_optimizer.correlation_scoring_config import CorrelationScoringConfig


def test_forced_stacking():
    """Test with forced stacking bonuses"""

    print("\n" + "=" * 60)
    print("TESTING FORCED STACKING")
    print("=" * 60)

    csv_path = "/home/michael/Downloads/DKSalaries(51).csv"

    df = pd.read_csv(csv_path)

    # Convert to UnifiedPlayer objects
    all_players = []
    for _, row in df.iterrows():
        try:
            player = UnifiedPlayer(
                row.get('Name', ''),
                row.get('Position', ''),
                row.get('TeamAbbrev', ''),
                int(row.get('Salary', 0)),
                row.get('Game Info', '').split('@')[-1] if '@' in str(row.get('Game Info', '')) else '',
                row.get('ID', str(len(all_players))),
                float(row.get('AvgPointsPerGame', 0))
            )
            player.primary_position = player.position.split('/')[0]
            player.base_projection = player.projection if hasattr(player, 'projection') else 10.0
            player.optimization_score = player.base_projection
            all_players.append(player)
        except:
            continue

    # Find teams with the most high-scoring players (good for stacking)
    team_scores = {}
    for p in all_players:
        if p.primary_position not in ['P', 'SP', 'RP']:
            if p.team not in team_scores:
                team_scores[p.team] = []
            team_scores[p.team].append(p.base_projection)

    # Find best stacking teams
    best_teams = []
    for team, scores in team_scores.items():
        if len(scores) >= 5:  # Need at least 5 hitters
            avg_score = sum(sorted(scores, reverse=True)[:5]) / 5
            best_teams.append((team, avg_score, len(scores)))

    best_teams.sort(key=lambda x: x[1], reverse=True)

    print("\nTop 5 teams for stacking:")
    for team, avg, count in best_teams[:5]:
        print(f"  {team}: {count} hitters, top-5 avg: {avg:.1f}")

    if best_teams:
        target_team = best_teams[0][0]
        print(f"\n🎯 Forcing stack on {target_team}")

        # MASSIVELY boost players from target team
        for p in all_players:
            if p.team == target_team and p.primary_position not in ['P', 'SP', 'RP']:
                # Give huge bonus to force stacking
                p.optimization_score = p.base_projection * 5.0  # 5x multiplier!
                print(f"  Boosted {p.name}: {p.base_projection:.1f} -> {p.optimization_score:.1f}")

    # Build smart player pool
    position_pools = {
        'P': [], 'SP': [], 'RP': [],
        'C': [], '1B': [], '2B': [],
        '3B': [], 'SS': [], 'OF': []
    }

    for p in all_players:
        if '/' not in p.position:
            pos = p.position
            if pos in position_pools:
                position_pools[pos].append(p)

    # Sort each position
    for pos in position_pools:
        position_pools[pos].sort(key=lambda x: x.optimization_score, reverse=True)

    # Build test pool
    test_players = []

    # Get pitchers
    all_pitchers = position_pools['P'] + position_pools['SP'] + position_pools['RP']
    all_pitchers.sort(key=lambda x: x.optimization_score, reverse=True)
    test_players.extend(all_pitchers[:10])

    # Get position players (more from target team)
    for pos in ['C', '1B', '2B', '3B', 'SS', 'OF']:
        # Take top players, ensuring we get target team players
        pos_players = position_pools[pos][:10]
        test_players.extend(pos_players)

    print(f"\nTest pool: {len(test_players)} players")

    # Count target team players
    target_count = sum(1 for p in test_players if p.team == target_team)
    print(f"Players from {target_team}: {target_count}")

    # Run GPP optimization
    config = CorrelationScoringConfig()
    config.salary_cap = 50000
    optimizer = UnifiedMILPOptimizer(config)

    # TEMPORARILY remove team constraints to see if that helps
    print("\n" + "-" * 40)
    print("TESTING GPP WITH STACKING BONUSES")
    print("-" * 40)

    lineup, score = optimizer._run_milp_optimization(test_players, 'gpp')

    if lineup:
        print(f"\n✅ OPTIMIZATION SUCCESSFUL!")
        print(f"Score: {score:.1f}")
        print(f"Salary: ${sum(p.salary for p in lineup)}")

        # Check stacking
        team_counts = {}
        for p in lineup:
            if p.primary_position not in ['P', 'SP', 'RP']:
                team_counts[p.team] = team_counts.get(p.team, 0) + 1

        print(f"\n📊 STACK ANALYSIS:")
        for team, count in sorted(team_counts.items(), key=lambda x: x[1], reverse=True):
            indicator = "🔥" if team == target_team else ""
            print(f"  {team}: {count} players {'⭐' * count} {indicator}")

        max_stack = max(team_counts.values()) if team_counts else 0

        if max_stack >= 4:
            print(f"\n🎯 SUCCESS! {max_stack}-player stack!")
        else:
            print(f"\n⚠️ Still only {max_stack}-player stack despite bonuses")
            print("\nThis suggests the team constraints are preventing stacking")
            print("Check the GPP team constraints in _run_milp_optimization")

        print("\nLineup:")
        for p in lineup:
            boost = "🔥" if p.team == target_team else ""
            print(f"  {p.position:7s}: {p.name:20s} ({p.team:3s}) ${p.salary:5d} {boost}")
    else:
        print("\n❌ OPTIMIZATION FAILED")


if __name__ == "__main__":
    test_forced_stacking()