#!/usr/bin/env python3
"""Debug why optimization is failing"""

import sys
sys.path.insert(0, 'main_optimizer')

from unified_core_system_updated import UnifiedCoreSystem

system = UnifiedCoreSystem()

# Load data
csv_path = "/home/michael/Downloads/DKSalaries(48).csv"
system.load_csv(csv_path)
system.build_player_pool(include_unconfirmed=True)

print("=" * 60)
print("DEBUGGING OPTIMIZATION FAILURE")
print("=" * 60)

# Check player pool
print(f"\n1. Player Pool Size: {len(system.player_pool)}")

# Check by position
positions = {}
for p in system.player_pool:
    pos = p.position if p.position != 'SP' and p.position != 'RP' else 'P'
    positions[pos] = positions.get(pos, 0) + 1

print("\n2. Players by Position:")
for pos, count in sorted(positions.items()):
    print(f"   {pos}: {count} players")

# Check scoring
scored_players = [p for p in system.player_pool if hasattr(p, 'cash_score') and p.cash_score > 0]
print(f"\n3. Players with scores: {len(scored_players)}")

# Try single lineup first
print("\n4. Testing SINGLE lineup:")
lineups = system.optimize_lineup('projection_monster', 'cash', 1)
if lineups:
    print(f"   ✅ Single lineup works! Score: {lineups[0]['score']:.1f}")
else:
    print(f"   ❌ Even single lineup fails!")

# Try multiple with less diversity
print("\n5. Testing 3 lineups:")
lineups = system.optimize_lineup('projection_monster', 'cash', 3)
print(f"   Generated: {len(lineups)} lineups")

# Check filtered pool
from unified_milp_optimizer import UnifiedMILPOptimizer
optimizer = UnifiedMILPOptimizer()

filtered = optimizer.apply_strategy_filter(
    system.player_pool,
    'projection_monster',
    'cash'
)

print(f"\n6. After strategy filter: {len(filtered)} players")

# Check minimum requirements
print("\n7. Position requirements check:")
min_required = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
total_needed = sum(min_required.values())
print(f"   Need {total_needed} players minimum")

# Check salary distribution
high_salary = [p for p in system.player_pool if p.salary > 8000]
low_salary = [p for p in system.player_pool if p.salary < 4000]
print(f"\n8. Salary distribution:")
print(f"   High (>$8000): {len(high_salary)}")
print(f"   Low (<$4000): {len(low_salary)}")