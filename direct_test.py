#!/usr/bin/env python3
"""
Direct Command Line Test for DFS Optimizer
=========================================
Test optimization directly without GUI
"""

import sys
import pandas as pd
from pathlib import Path


def test_optimization(csv_file="DKSalaries5.csv"):
    """Direct test of optimization pipeline"""
    print("🎯 DIRECT DFS OPTIMIZATION TEST")
    print("=" * 60)

    # Step 1: Check CSV
    print(f"\n1️⃣ Checking CSV: {csv_file}")
    if not Path(csv_file).exists():
        print(f"❌ File not found!")
        print(f"   Files in directory: {list(Path('.').glob('*.csv'))}")
        return

    # Step 2: Quick CSV inspection
    df = pd.read_csv(csv_file)
    print(f"✅ CSV loaded: {len(df)} players")
    print(f"   Columns: {', '.join(df.columns)}")

    # Step 3: Try modern core first
    print("\n2️⃣ Testing Modern DFS Core...")
    try:
        from modern_dfs_core import ModernDFSCore

        core = ModernDFSCore()
        core.load_draftkings_csv(csv_file)

        # Use all players mode
        core.set_optimization_mode("all")

        lineup, score = core.optimize_lineup()

        if lineup:
            print(f"✅ SUCCESS with Modern Core! Score: {score:.2f}")
            display_lineup(lineup, score)
            return True
    except Exception as e:
        print(f"❌ Modern core failed: {e}")

    # Step 4: Try bulletproof core
    print("\n3️⃣ Testing Bulletproof DFS Core...")
    try:
        from bulletproof_dfs_core import BulletproofDFSCore

        core = BulletproofDFSCore()
        core.load_draftkings_csv(csv_file)

        # Use all players mode
        core.set_optimization_mode("all")

        # Try different optimization methods
        lineup = None
        score = 0

        methods = [
            'optimize_lineup_with_mode',
            'optimize_lineup_clean',
            'optimize_lineup'
        ]

        for method in methods:
            if hasattr(core, method):
                print(f"   Trying {method}...")
                try:
                    result = getattr(core, method)()
                    if isinstance(result, tuple) and len(result) == 2:
                        lineup, score = result
                        if lineup:
                            break
                except Exception as e:
                    print(f"   ❌ {method} failed: {e}")

        if lineup:
            print(f"✅ SUCCESS with Bulletproof Core! Score: {score:.2f}")
            display_lineup(lineup, score)
            return True
        else:
            print("❌ All optimization methods failed")

    except Exception as e:
        print(f"❌ Bulletproof core failed: {e}")

    # Step 5: Try direct unified optimizer
    print("\n4️⃣ Testing Direct Unified Optimizer...")
    try:
        from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig
        from unified_player_model import UnifiedPlayer

        # Create players from CSV
        players = []
        for _, row in df.iterrows():
            player = UnifiedPlayer(
                id=f"{row['ID']}",
                name=row['Name'],
                team=row['TeamAbbrev'],
                salary=int(row['Salary']),
                primary_position=row['Position'],
                positions=[row['Position']],
                base_projection=float(row['AvgPointsPerGame'])
            )
            player.enhanced_score = player.base_projection
            players.append(player)

        print(f"   Created {len(players)} players")

        # Optimize
        optimizer = UnifiedMILPOptimizer(OptimizationConfig())
        lineup, score = optimizer.optimize_lineup(players, strategy="all_players")

        if lineup:
            print(f"✅ SUCCESS with Direct Optimizer! Score: {score:.2f}")
            display_lineup(lineup, score)
            return True
        else:
            print("❌ Direct optimization failed")

    except Exception as e:
        print(f"❌ Direct optimizer failed: {e}")
        import traceback
        traceback.print_exc()

    return False


def display_lineup(lineup, score):
    """Display the optimized lineup"""
    print("\n📋 OPTIMIZED LINEUP")
    print("-" * 60)

    total_salary = 0
    for i, player in enumerate(lineup, 1):
        pos = getattr(player, 'assigned_position', player.primary_position)
        salary = player.salary
        total_salary += salary
        points = getattr(player, 'enhanced_score', player.base_projection)

        print(f"{i:2d}. {pos:4s} {player.name:20s} {player.team:3s} "
              f"${salary:6,} → {points:6.1f} pts")

    print("-" * 60)
    print(f"Total Salary: ${total_salary:,} / $50,000")
    print(f"Projected Score: {score:.1f} points")


def check_dependencies():
    """Check if all required packages are installed"""
    print("\n5️⃣ Checking Dependencies...")

    required = {
        'pandas': 'Data handling',
        'numpy': 'Numerical operations',
        'pulp': 'Optimization engine',
        'streamlit': 'GUI framework'
    }

    missing = []
    for package, purpose in required.items():
        try:
            __import__(package)
            print(f"✅ {package:10s} - {purpose}")
        except ImportError:
            print(f"❌ {package:10s} - {purpose}")
            missing.append(package)

    if missing:
        print(f"\n⚠️  Install missing packages:")
        print(f"   pip install {' '.join(missing)}")

    return len(missing) == 0


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "DKSalaries5.csv"

    # Run test
    success = test_optimization(csv_file)

    if not success:
        print("\n" + "=" * 60)
        check_dependencies()

    print("\n✅ Test complete!")