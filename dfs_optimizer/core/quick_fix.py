#!/usr/bin/env python3
"""
FIX PROJECTIONS - FINAL SOLUTION
================================
The CSV has AvgPointsPerGame! Just need to read it correctly.
"""

import sys
import pandas as pd

sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem
from dfs_optimizer.strategies.strategy_selector import StrategyAutoSelector

print("=" * 80)
print("🔧 FIXING PROJECTIONS - FINAL SOLUTION")
print("=" * 80)

CSV_PATH = "/home/michael/Downloads/DKSalaries(29).csv"

# First, let's verify the issue
print("\n1️⃣ Checking current load behavior:")
system = UnifiedCoreSystem()
system.load_players_from_csv(CSV_PATH)

print("First 5 players AS LOADED:")
for p in system.players[:5]:
    print(f"  {p.name}: base_projection={p.base_projection}")

# Now let's check what's in the CSV directly
print("\n2️⃣ What's actually in the CSV:")
df = pd.read_csv(CSV_PATH)
print("First 5 rows of CSV:")
for i, row in df.head().iterrows():
    print(f"  {row['Name']}: AvgPointsPerGame={row['AvgPointsPerGame']}")

# The issue is in load_players_from_csv - it's looking for the wrong column!
print("\n3️⃣ Creating a simple fix:")

# Let's manually fix all loaded players
for player in system.players:
    # Find the matching row in the dataframe
    matching_row = df[df['Name'] == player.name]
    if not matching_row.empty:
        player.base_projection = float(matching_row.iloc[0]['AvgPointsPerGame'])
    player.is_pitcher = player.primary_position in ['P', 'SP', 'RP']

print("\nAfter manual fix:")
for p in system.players[:5]:
    print(f"  {p.name}: base_projection={p.base_projection}")

# Now test the full pipeline
print("\n4️⃣ Testing full pipeline with fixed projections:")

system.build_player_pool(include_unconfirmed=True)
system.enrich_player_pool()

# Test both contest types
for contest_type in ['cash', 'gpp']:
    print(f"\n{'=' * 60}")
    print(f"Testing {contest_type.upper()} optimization:")

    system.score_players(contest_type)

    # Check score variety
    scores = []
    names_scores = []
    for p in system.player_pool[:30]:
        score = getattr(p, 'enhanced_score', 0)
        scores.append(score)
        if len(names_scores) < 5:
            names_scores.append((p.name, p.base_projection, score))

    print(f"\nScore variety check:")
    print(f"  Unique scores: {len(set(scores))}")
    print(f"  Score range: {min(scores):.1f} - {max(scores):.1f}")

    print(f"\nSample players:")
    for name, base, enhanced in names_scores:
        print(f"  {name}: base={base:.1f}, enhanced={enhanced:.1f}")

    # Optimize
    selector = StrategyAutoSelector()
    strategy = selector.top_strategies[contest_type]['medium']

    lineups = system.optimize_lineups(
        num_lineups=1,
        strategy=strategy,
        contest_type=contest_type
    )

    if lineups:
        lineup = lineups[0]
        print(f"\n✅ Optimized {contest_type.upper()} lineup:")
        print(f"  Salary: ${sum(p.salary for p in lineup['players']):,}")
        print(f"  Projected: {lineup.get('total_score', 0):.1f}")
        print("  Players:")
        for p in lineup['players']:
            print(f"    {p.primary_position}: {p.name} - {getattr(p, 'enhanced_score', 0):.1f} pts")

# Create a permanent fix script
print("\n5️⃣ Creating permanent solution:")

fix_script = '''#!/usr/bin/env python3
"""
WORKING DFS OPTIMIZER WITH PROJECTION FIX
"""
import sys
import pandas as pd
sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem
from dfs_optimizer.strategies.strategy_selector import StrategyAutoSelector

# Settings
CSV_PATH = "/home/michael/Downloads/DKSalaries(29).csv"
CONTEST_TYPE = "gpp"  # or "cash"

# Load system
system = UnifiedCoreSystem()
system.load_players_from_csv(CSV_PATH)

# Fix projections from CSV
df = pd.read_csv(CSV_PATH)
for player in system.players:
    matching_row = df[df['Name'] == player.name]
    if not matching_row.empty:
        player.base_projection = float(matching_row.iloc[0]['AvgPointsPerGame'])
    player.is_pitcher = player.primary_position in ['P', 'SP', 'RP']

# Build and optimize
system.build_player_pool(include_unconfirmed=True)
system.enrich_player_pool()
system.score_players(CONTEST_TYPE)

selector = StrategyAutoSelector()
strategy = selector.top_strategies[CONTEST_TYPE]['medium']

lineups = system.optimize_lineups(
    num_lineups=1,
    strategy=strategy,
    contest_type=CONTEST_TYPE
)

# Display
if lineups:
    lineup = lineups[0]
    print(f"\\nOptimized {CONTEST_TYPE.upper()} Lineup:")
    print(f"Salary: ${sum(p.salary for p in lineup['players']):,}/50,000")
    print(f"Projected: {lineup.get('total_score', 0):.1f} points\\n")

    for p in lineup['players']:
        score = getattr(p, 'enhanced_score', 0)
        print(f"{p.primary_position}: {p.name} (${p.salary:,}) - {score:.1f} pts")
'''

with open('optimizer_with_projections_fixed.py', 'w') as f:
    f.write(fix_script)

print("✅ Created optimizer_with_projections_fixed.py")

print("\n" + "=" * 80)
print("💡 PERMANENT FIX NEEDED")
print("=" * 80)
print("""
The issue is in UnifiedCoreSystem.load_players_from_csv()

It's using:
  base_projection=float(row.get('AvgPointsPerGame', 0))

But this returns 0 if the column doesn't match exactly. 
The permanent fix is to update that method to properly read the column.

For now, use optimizer_with_projections_fixed.py which manually fixes the projections!
""")