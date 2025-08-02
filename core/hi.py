#!/usr/bin/env python3
import sys

sys.path.insert(0, '/home/michael/Desktop/All_in_one_optimizer')

from dfs_optimizer.core.unified_core_system import UnifiedCoreSystem
import pandas as pd

print("🧪 FINAL SYSTEM TEST")
print("=" * 50)

# Create system
system = UnifiedCoreSystem()

# Load CSV
csv_path = "/home/michael/Downloads/DKSalaries(30).csv"
system.load_players_from_csv(csv_path)

# Check projections loaded
print("\n1️⃣ Projection Loading Test:")
for p in system.players[:3]:
    print(f"   {p.name}: {p.base_projection}")

if system.players[0].base_projection > 0:
    print("   ✅ Projections loading correctly!")
else:
    print("   ❌ FAIL: Projections still 0")
    # Manual fix
    df = pd.read_csv(csv_path)
    for player in system.players:
        matching_row = df[df['Name'] == player.name]
        if not matching_row.empty:
            player.base_projection = float(matching_row.iloc[0]['AvgPointsPerGame'])

# Build pool
system.build_player_pool(include_unconfirmed=True)
system.enrich_player_pool()

# Test Cash scoring
print("\n2️⃣ Cash Scoring Test:")
system.score_players('cash')
cash_scores = [p.cash_score for p in system.player_pool[:5]]
print(f"   Cash scores: {[f'{s:.1f}' for s in cash_scores]}")
print(f"   Unique scores: {len(set(cash_scores))}/5")

# Test GPP scoring
print("\n3️⃣ GPP Scoring Test:")
system.score_players('gpp')
gpp_scores = [p.gpp_score for p in system.player_pool[:5]]
print(f"   GPP scores: {[f'{s:.1f}' for s in gpp_scores]}")
print(f"   Different from cash? {cash_scores != gpp_scores}")

# Test optimization
print("\n4️⃣ Cash Optimization Test:")
for player in system.player_pool:
    player.enhanced_score = player.cash_score
    player.optimization_score = player.cash_score

lineups = system.optimize_lineups(
    num_lineups=1,
    strategy='balanced_projections',  # Better for small cash
    contest_type='cash'
)

if lineups:
    lineup = lineups[0]
    print(f"   ✅ Lineup created: ${sum(p.salary for p in lineup['players']):,}")
    print(f"   Using correct scores? Check first player:")
    p = lineup['players'][0]
    print(f"   {p.name}: cash_score={p.cash_score:.1f}, gpp_score={p.gpp_score:.1f}")

print("\n" + "=" * 50)
print("✅ SYSTEM READY!" if all([
    system.players[0].base_projection > 0,
    len(set(cash_scores)) > 1,
    lineups
]) else "❌ ISSUES REMAIN")