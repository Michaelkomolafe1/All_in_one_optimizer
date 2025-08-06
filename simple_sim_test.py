#!/usr/bin/env python3
"""Simple test for simulation - no pytest needed"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir('/home/michael/Desktop/All_in_one_optimizer')

print("Testing simulation...")

try:
    from simulation.comprehensive_simulation_runner import ComprehensiveSimulationRunner
    print("✅ Import successful")

    # Try to create runner
    runner = ComprehensiveSimulationRunner()
    print("✅ Runner created")

    # Run minimal test
    print("\nRunning 5 quick simulations...")
    results = runner.run_comprehensive_test(
        num_simulations=5,
        contest_types=['cash'],
        slate_sizes=['small'],
        field_size=50
    )

    print("\n✅ Simulation completed!")

    # Check results
    for key, stats in results.items():
        if 'cash' in key:
            win_rate = stats.get('win_rate', 0)
            print(f"Cash win rate: {win_rate:.1f}%")
            if win_rate == 100:
                print("⚠️ WARNING: 100% win rate means something is still broken!")
            elif 40 <= win_rate <= 60:
                print("✅ Win rate looks realistic!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
