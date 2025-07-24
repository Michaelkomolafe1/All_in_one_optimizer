#!/usr/bin/env python3
"""Diagnose why lineups are failing"""

import sys
sys.path.append('/home/michael/Desktop/All_in_one_optimizer')
from fixed_complete_dfs_sim import *

# Create simulation
sim = ComprehensiveValidatedSimulation(verbose=False)

# Generate a slate
print("🔍 Generating test slate...")
slate_config = sim.contest_configs[0]  # Main slate
players, games = sim.generate_realistic_slate(slate_config)

print(f"\n📊 Slate Analysis:")
print(f"Total players: {len(players)}")

# Count by position
pos_counts = {}
salary_by_pos = {}
for p in players:
    if p.position not in pos_counts:
        pos_counts[p.position] = 0
        salary_by_pos[p.position] = []
    pos_counts[p.position] += 1
    salary_by_pos[p.position].append(p.salary)

print(f"\n🎯 Players by position:")
for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
    if pos in pos_counts:
        avg_sal = sum(salary_by_pos[pos]) / len(salary_by_pos[pos])
        min_sal = min(salary_by_pos[pos])
        max_sal = max(salary_by_pos[pos])
        print(f"{pos}: {pos_counts[pos]} players, "
              f"Salary: ${min_sal}-${max_sal} (avg: ${avg_sal:.0f})")

# Try to build cheapest possible lineup
print(f"\n💰 Attempting cheapest lineup:")
position_needs = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
cheapest = []
total_salary = 0

for pos, need in position_needs.items():
    pos_players = sorted([p for p in players if p.position == pos],
                        key=lambda x: x.salary)
    if len(pos_players) >= need:
        for i in range(need):
            cheapest.append(pos_players[i])
            total_salary += pos_players[i].salary
            print(f"  {pos}: ${pos_players[i].salary} - {pos_players[i].name}")
    else:
        print(f"  ERROR: Not enough {pos} players!")

print(f"\nCheapest possible: ${total_salary} (Cap: $50,000)")
print(f"Min required: $40,000 (your current setting)")

if total_salary > 50000:
    print("\n❌ PROBLEM: Even cheapest lineup exceeds cap!")
elif total_salary > 40000:
    print("\n⚠️  ISSUE: Cheapest lineup exceeds your minimum salary requirement!")
else:
    print("\n✅ Salaries seem OK, issue must be in lineup building logic")

# Test lineup building
print(f"\n🔧 Testing lineup building...")
strategy = sim.strategies['pure_projections']
result = sim.build_optimized_lineup(players, strategy, {'contest_type': 'gpp'})
if result:
    print("✅ Lineup built successfully!")
else:
    print("❌ Lineup building failed!")