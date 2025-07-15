#!/usr/bin/env python3
"""
DFS Optimizer Diagnostic Script
==============================
Diagnose issues with CSV loading and lineup generation
"""

import os
import pandas as pd
import traceback
from pathlib import Path


def diagnose_csv(csv_path="DKSalaries5.csv"):
    """Diagnose issues with CSV loading"""
    print("🔍 DFS OPTIMIZER DIAGNOSTIC")
    print("=" * 60)

    # 1. Check if CSV exists
    print("\n1️⃣ Checking CSV file...")
    if not os.path.exists(csv_path):
        print(f"❌ CSV not found: {csv_path}")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Files in directory: {list(Path('.').glob('*.csv'))}")
        return

    print(f"✅ Found CSV: {csv_path}")

    # 2. Load and inspect CSV
    print("\n2️⃣ Loading CSV...")
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} players")
        print(f"   Columns: {list(df.columns)}")

        # Show sample data
        print("\n📊 Sample data (first 5 rows):")
        print(df.head())

        # Check for required columns
        print("\n3️⃣ Checking required columns...")
        required = ['Name', 'Salary', 'TeamAbbrev', 'Position']
        missing = [col for col in required if col not in df.columns]

        if missing:
            print(f"❌ Missing columns: {missing}")
        else:
            print("✅ All required columns present")

        # Analyze data
        print("\n4️⃣ Data analysis:")
        print(f"   Teams: {df['TeamAbbrev'].nunique()} unique teams")
        print(f"   Salary range: ${df['Salary'].min():,} - ${df['Salary'].max():,}")
        print(f"   Avg projection: {df['AvgPointsPerGame'].mean():.2f}")

        # Position breakdown
        print("\n   Position breakdown:")
        for pos, count in df['Position'].value_counts().items():
            print(f"     {pos}: {count} players")

    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        traceback.print_exc()
        return

    # 3. Test with bulletproof core
    print("\n5️⃣ Testing with bulletproof_dfs_core...")
    try:
        from bulletproof_dfs_core import BulletproofDFSCore

        core = BulletproofDFSCore()
        print("✅ Core initialized")

        # Load CSV
        success = core.load_draftkings_csv(csv_path)
        if success:
            print(f"✅ Loaded {len(core.players)} players into core")

            # Show eligible players
            print("\n6️⃣ Checking player eligibility...")
            print(f"   Total players: {len(core.players)}")

            # Test different modes
            for mode in ["bulletproof", "all"]:
                core.set_optimization_mode(mode)
                eligible = core.get_eligible_players_by_mode()
                print(f"   {mode} mode: {len(eligible)} eligible players")

            # Try to optimize
            print("\n7️⃣ Testing optimization...")
            core.set_optimization_mode("all")  # Use all players for testing

            try:
                lineup, score = core.optimize_lineup_with_mode()
                if lineup:
                    print(f"✅ Generated lineup! Score: {score:.2f}")
                    print("\nLineup:")
                    for p in lineup[:5]:  # Show first 5
                        print(f"   {p.name} - ${p.salary:,}")
                else:
                    print("❌ No lineup generated")
            except Exception as e:
                print(f"❌ Optimization error: {e}")
                traceback.print_exc()
        else:
            print("❌ Failed to load CSV into core")

    except ImportError:
        print("❌ Could not import bulletproof_dfs_core")
        print("   Trying modern_dfs_core instead...")

        try:
            from modern_dfs_core import ModernDFSCore

            core = ModernDFSCore()
            print("✅ Modern core initialized")

            if core.load_draftkings_csv(csv_path):
                print(f"✅ Loaded {len(core.players)} players")

                # Try optimization
                core.set_optimization_mode("all")
                lineup, score = core.optimize_lineup()

                if lineup:
                    print(f"✅ Generated lineup! Score: {score:.2f}")
                else:
                    print("❌ No lineup generated")

        except Exception as e:
            print(f"❌ Error with modern core: {e}")
            traceback.print_exc()

    # 4. Check GUI integration
    print("\n8️⃣ Checking GUI availability...")
    try:
        import streamlit as st
        print("✅ Streamlit available")
    except ImportError:
        print("❌ Streamlit not installed - run: pip install streamlit")

    try:
        from enhanced_dfs_gui import DFSOptimizerGUI
        print("✅ Enhanced GUI available")
    except ImportError:
        print("❌ Could not import enhanced_dfs_gui")

    print("\n" + "=" * 60)
    print("📋 DIAGNOSTIC COMPLETE")


def quick_fix_test():
    """Quick test to see if we can generate any lineup"""
    print("\n🚀 QUICK FIX TEST")
    print("=" * 60)

    try:
        # Try to create a minimal working example
        from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig
        from unified_player_model import UnifiedPlayer

        print("✅ Unified components available")

        # Load CSV and create players
        df = pd.read_csv("DKSalaries5.csv")

        players = []
        for _, row in df.iterrows():
            player = UnifiedPlayer(
                id=str(row['ID']),
                name=row['Name'],
                team=row['TeamAbbrev'],
                salary=int(row['Salary']),
                primary_position=row['Position'],
                positions=[row['Position']],
                base_projection=float(row['AvgPointsPerGame'])
            )
            players.append(player)

        print(f"✅ Created {len(players)} UnifiedPlayer objects")

        # Try optimization
        config = OptimizationConfig()
        optimizer = UnifiedMILPOptimizer(config)

        # Calculate scores
        for p in players:
            p.enhanced_score = p.base_projection

        lineup, score = optimizer.optimize_lineup(players, strategy="all_players")

        if lineup:
            print(f"✅ SUCCESS! Generated lineup with score: {score:.2f}")
            print("\nLineup:")
            for p in lineup:
                print(f"   {p.primary_position} {p.name} ({p.team}) - ${p.salary:,} → {p.enhanced_score:.1f}")
        else:
            print("❌ Could not generate lineup")

    except Exception as e:
        print(f"❌ Quick fix failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    csv_file = sys.argv[1] if len(sys.argv) > 1 else "DKSalaries5.csv"

    # Run diagnostic
    diagnose_csv(csv_file)

    # Try quick fix
    quick_fix_test()