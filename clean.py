#!/usr/bin/env python3
"""
DIAGNOSE WHY MILP IS FAILING
"""

import sys

sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

from main_optimizer.unified_milp_optimizer import UnifiedMILPOptimizer
from main_optimizer.unified_player_model import UnifiedPlayer
from main_optimizer.correlation_scoring_config import CorrelationScoringConfig
import pulp


def diagnose_constraints():
    """Check if basic constraints are feasible"""

    print("\n" + "=" * 60)
    print("DIAGNOSING MILP CONSTRAINTS")
    print("=" * 60)

    # Create minimal test case
    players = []

    # Create exactly what we need
    # 2 Pitchers
    for i in range(4):
        p = UnifiedPlayer(f"P{i}", "P", f"TM{i % 2}", 8000 + i * 500, f"OPP{i % 2}", f"p{i}", 15.0)
        p.primary_position = 'P'
        p.optimization_score = 15.0
        players.append(p)

    # Create hitters for positions (need minimum for each)
    positions = ['C', 'C', '1B', '1B', '2B', '2B', '3B', '3B', 'SS', 'SS', 'OF', 'OF', 'OF', 'OF', 'OF', 'OF']

    for i, pos in enumerate(positions):
        p = UnifiedPlayer(f"{pos}{i}", pos, f"TM{i % 3}", 3500 + i * 100, f"OPP", f"{pos}{i}", 8.0 + i * 0.5)
        p.primary_position = pos
        p.optimization_score = 8.0 + i * 0.5
        players.append(p)

    print(f"Created {len(players)} players")

    # Count positions
    pos_counts = {}
    for p in players:
        pos = p.primary_position
        pos_counts[pos] = pos_counts.get(pos, 0) + 1
    print(f"Positions: {pos_counts}")

    # Test SIMPLE optimization
    print("\n" + "-" * 40)
    print("TEST 1: SIMPLE CONSTRAINTS ONLY")
    print("-" * 40)

    prob = pulp.LpProblem("Test", pulp.LpMaximize)
    player_vars = pulp.LpVariable.dicts("p", range(len(players)), cat="Binary")

    # Objective
    prob += pulp.lpSum([players[i].optimization_score * player_vars[i] for i in range(len(players))])

    # Basic constraints
    prob += pulp.lpSum(player_vars.values()) == 10, "roster_size"
    prob += pulp.lpSum([players[i].salary * player_vars[i] for i in range(len(players))]) <= 50000, "salary"

    # Position constraints
    prob += pulp.lpSum([player_vars[i] for i in range(len(players)) if players[i].primary_position == 'P']) == 2
    prob += pulp.lpSum([player_vars[i] for i in range(len(players)) if players[i].primary_position == 'C']) >= 1
    prob += pulp.lpSum([player_vars[i] for i in range(len(players)) if players[i].primary_position == '1B']) >= 1
    prob += pulp.lpSum([player_vars[i] for i in range(len(players)) if players[i].primary_position == '2B']) >= 1
    prob += pulp.lpSum([player_vars[i] for i in range(len(players)) if players[i].primary_position == '3B']) >= 1
    prob += pulp.lpSum([player_vars[i] for i in range(len(players)) if players[i].primary_position == 'SS']) >= 1
    prob += pulp.lpSum([player_vars[i] for i in range(len(players)) if players[i].primary_position == 'OF']) >= 3

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    if prob.status == pulp.LpStatusOptimal:
        print("✅ BASIC CONSTRAINTS WORK!")
        lineup = [players[i] for i in range(len(players)) if player_vars[i].varValue == 1]
        print(f"Found lineup with {len(lineup)} players")
        total_sal = sum(p.salary for p in lineup)
        print(f"Total salary: ${total_sal}")
    else:
        print(f"❌ FAILED: {pulp.LpStatus[prob.status]}")

    # Test with stacking
    print("\n" + "-" * 40)
    print("TEST 2: WITH TEAM LIMITS")
    print("-" * 40)

    prob2 = pulp.LpProblem("Test2", pulp.LpMaximize)
    player_vars2 = pulp.LpVariable.dicts("p", range(len(players)), cat="Binary")

    # Same basic constraints
    prob2 += pulp.lpSum([players[i].optimization_score * player_vars2[i] for i in range(len(players))])
    prob2 += pulp.lpSum(player_vars2.values()) == 10
    prob2 += pulp.lpSum([players[i].salary * player_vars2[i] for i in range(len(players))]) <= 50000

    # Positions
    prob2 += pulp.lpSum([player_vars2[i] for i in range(len(players)) if players[i].primary_position == 'P']) == 2
    prob2 += pulp.lpSum([player_vars2[i] for i in range(len(players)) if players[i].primary_position == 'C']) >= 1
    prob2 += pulp.lpSum([player_vars2[i] for i in range(len(players)) if players[i].primary_position == '1B']) >= 1
    prob2 += pulp.lpSum([player_vars2[i] for i in range(len(players)) if players[i].primary_position == '2B']) >= 1
    prob2 += pulp.lpSum([player_vars2[i] for i in range(len(players)) if players[i].primary_position == '3B']) >= 1
    prob2 += pulp.lpSum([player_vars2[i] for i in range(len(players)) if players[i].primary_position == 'SS']) >= 1
    prob2 += pulp.lpSum([player_vars2[i] for i in range(len(players)) if players[i].primary_position == 'OF']) >= 3

    # Add team limits
    teams = {}
    for i, p in enumerate(players):
        if p.team not in teams:
            teams[p.team] = []
        teams[p.team].append(i)

    for team, indices in teams.items():
        hitters = [i for i in indices if players[i].primary_position != 'P']
        if hitters:
            prob2 += pulp.lpSum([player_vars2[i] for i in hitters]) <= 5, f"max_{team}"

    prob2.solve(pulp.PULP_CBC_CMD(msg=0))

    if prob2.status == pulp.LpStatusOptimal:
        print("✅ TEAM CONSTRAINTS WORK!")
        lineup = [players[i] for i in range(len(players)) if player_vars2[i].varValue == 1]

        team_counts = {}
        for p in lineup:
            if p.primary_position != 'P':
                team_counts[p.team] = team_counts.get(p.team, 0) + 1

        print(f"Team distribution: {team_counts}")
        max_stack = max(team_counts.values()) if team_counts else 0
        print(f"Max stack: {max_stack}")
    else:
        print(f"❌ FAILED: {pulp.LpStatus[prob2.status]}")

    # Now test with your actual optimizer
    print("\n" + "-" * 40)
    print("TEST 3: YOUR OPTIMIZER")
    print("-" * 40)

    config = CorrelationScoringConfig()
    config.salary_cap = 50000
    optimizer = UnifiedMILPOptimizer(config)

    # Boost some players to encourage stacking
    for p in players:
        if p.team == 'TM0' and p.primary_position != 'P':
            p.optimization_score *= 2.0  # Boost to encourage stacking

    lineup, score = optimizer._run_milp_optimization(players, 'gpp')

    if lineup:
        print(f"✅ YOUR OPTIMIZER WORKS!")
        print(f"Score: {score:.1f}")

        team_counts = {}
        for p in lineup:
            if p.primary_position != 'P':
                team_counts[p.team] = team_counts.get(p.team, 0) + 1

        print(f"Team distribution: {team_counts}")
    else:
        print("❌ YOUR OPTIMIZER FAILED")
        print("This means the constraints are too complex or conflicting")

    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    diagnose_constraints()