#!/usr/bin/env python3
"""Test script for DFS Optimizer optimizations"""

import time
from bulletproof_dfs_core import BulletproofDFSCore
from utils.profiler import profiler
from utils.config import config

def test_optimizations():
    """Test the optimized system"""
    print("🧪 TESTING DFS OPTIMIZER OPTIMIZATIONS")
    print("=" * 50)

    # Initialize core
    core = BulletproofDFSCore()

    # Test configuration
    print(f"\n📊 Configuration:")
    print(f"   Salary Cap: ${config.get('salary_cap'):,}")
    print(f"   Max Workers: {config.get('max_workers')}")
    print(f"   Cache Expiry (Vegas): {config.get('cache_expiry_hours.vegas')}h")

    # Load test data
    print(f"\n📁 Loading CSV...")
    start = time.time()

    # Look for CSV file
    import glob
    csv_files = glob.glob("*DKSalaries*.csv") + glob.glob("*dk*.csv")

    if csv_files:
        csv_file = csv_files[0]
        print(f"   Using: {csv_file}")

        if core.load_draftkings_csv(csv_file):
            load_time = time.time() - start
            print(f"   Load time: {load_time:.2f}s")

            # Test enrichment
            print(f"\n🔄 Testing enrichment...")
            enrich_start = time.time()

            # Apply some manual selections
            core.apply_manual_selection("Mike Trout, Shohei Ohtani")

            # Detect confirmations
            core.detect_confirmed_players()

            # Run enrichment
            if hasattr(core, 'enrich_players_optimized'):
                core.enrich_players_optimized()
            else:
                core.enrich_with_statcast_priority()

            enrich_time = time.time() - enrich_start
            print(f"   Enrichment time: {enrich_time:.2f}s")

            # Test optimization
            print(f"\n⚡ Testing optimization...")
            opt_start = time.time()

            lineup, score = core.optimize_lineup_with_mode()

            opt_time = time.time() - opt_start
            print(f"   Optimization time: {opt_time:.2f}s")

            if lineup:
                print(f"\n✅ Optimization successful!")
                print(f"   Score: {score:.2f}")
                print(f"   Players: {len(lineup)}")
                print(f"   Total time: {time.time() - start:.2f}s")

            # Show profiler report
            if hasattr(profiler, 'get_report'):
                print(f"\n📊 Performance Profile:")
                report = profiler.get_report()
                for func, stats in report.items():
                    print(f"   {func}: {stats['calls']} calls, {stats['average']:.3f}s avg")

    else:
        print("❌ No CSV files found. Please add a DraftKings CSV file.")

if __name__ == "__main__":
    test_optimizations()
