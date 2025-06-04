#!/usr/bin/env python3
"""
POSITION FLEXIBILITY ANALYZER
============================
Analyze position flexibility in any DraftKings CSV
"""

import pandas as pd
import sys
from pathlib import Path

def analyze_csv_flexibility(csv_path: str):
    """Analyze position flexibility in a CSV file"""

    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        return

    print(f"🔍 ANALYZING POSITION FLEXIBILITY: {Path(csv_path).name}")
    print("=" * 60)

    try:
        df = pd.read_csv(csv_path)

        # Find position column
        position_col = None
        for col in df.columns:
            if any(term in col.lower() for term in ['position', 'pos']):
                position_col = col
                break

        if not position_col:
            print("❌ Could not find position column")
            return

        # Analyze positions
        total_players = len(df)
        multi_pos_players = []
        single_pos_players = []
        position_counts = {}

        for _, row in df.iterrows():
            position_str = str(row[position_col]).strip()
            name = str(row.get('Name', row.iloc[1])).strip()
            salary = row.get('Salary', 0)

            # Parse positions
            if '/' in position_str:
                positions = [p.strip() for p in position_str.split('/')]
                multi_pos_players.append({
                    'name': name,
                    'positions': positions,
                    'salary': salary,
                    'position_str': position_str
                })
            else:
                single_pos_players.append({
                    'name': name,
                    'position': position_str,
                    'salary': salary
                })

            # Count position availability
            positions = position_str.split('/') if '/' in position_str else [position_str]
            for pos in positions:
                pos = pos.strip()
                position_counts[pos] = position_counts.get(pos, 0) + 1

        # Display results
        print(f"📊 FLEXIBILITY OVERVIEW:")
        print(f"   Total players: {total_players}")
        print(f"   Multi-position: {len(multi_pos_players)} ({len(multi_pos_players)/total_players*100:.1f}%)")
        print(f"   Single-position: {len(single_pos_players)} ({len(single_pos_players)/total_players*100:.1f}%)")

        if multi_pos_players:
            print(f"\n🔄 TOP MULTI-POSITION PLAYERS:")
            # Sort by salary (proxy for quality)
            multi_pos_players.sort(key=lambda x: x['salary'], reverse=True)

            for i, player in enumerate(multi_pos_players[:15], 1):
                pos_str = "/".join(player['positions'])
                print(f"   {i:2d}. {player['name']:<25} {pos_str:<12} ${player['salary']:,}")

        print(f"\n📍 POSITION DEPTH ANALYSIS:")
        position_requirements = {'P': 2, 'SP': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        for pos, required in position_requirements.items():
            available = position_counts.get(pos, 0)
            status = "✅" if available >= required else "❌"
            print(f"   {status} {pos}: {available} available, need {required}")

        # Flexibility hotspots
        print(f"\n🎯 FLEXIBILITY HOTSPOTS:")
        flex_combos = {}
        for player in multi_pos_players:
            combo = "/".join(sorted(player['positions']))
            flex_combos[combo] = flex_combos.get(combo, 0) + 1

        for combo, count in sorted(flex_combos.items(), key=lambda x: x[1], reverse=True):
            print(f"   {combo}: {count} players")

        print(f"\n💡 OPTIMIZATION OPPORTUNITIES:")
        high_flex_players = [p for p in multi_pos_players if len(p['positions']) >= 2]
        if len(high_flex_players) >= 3:
            print("   ✅ Excellent flexibility - can build multiple lineup configurations")
        elif len(high_flex_players) >= 1:
            print("   🟡 Moderate flexibility - some optimization opportunities")
        else:
            print("   🔴 Limited flexibility - mostly single-position players")

    except Exception as e:
        print(f"❌ Error analyzing CSV: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_csv_flexibility(sys.argv[1])
    else:
        # Look for CSV files in current directory
        csv_files = list(Path(".").glob("*.csv"))
        dk_files = [f for f in csv_files if 'dk' in f.name.lower() or 'salary' in f.name.lower()]

        if dk_files:
            print("📁 Found DraftKings CSV files:")
            for i, file in enumerate(dk_files, 1):
                print(f"   {i}. {file.name}")

            choice = input("\nSelect file number (or press Enter for first): ").strip()

            if choice.isdigit() and 1 <= int(choice) <= len(dk_files):
                selected_file = dk_files[int(choice) - 1]
            else:
                selected_file = dk_files[0]

            analyze_csv_flexibility(str(selected_file))
        else:
            print("❌ No CSV files found. Usage: python position_flex_analyzer.py <csv_file>")
