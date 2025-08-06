#!/usr/bin/env python3
"""Test that simulation works after fixes"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.comprehensive_simulation_runner import ComprehensiveSimulationRunner

print("Testing simulation with fixed attributes...")

runner = ComprehensiveSimulationRunner()

# Run a quick test
print("\nRunning 10 quick simulations...")
results = runner.run_comprehensive_test(
    num_simulations=10,
    contest_types=['cash', 'gpp'],
    slate_sizes=['small'],
    field_size=50
)

print("\n✅ Simulation completed without errors!")
print("\nCheck results:")
print("- Cash win rates should be 40-60% (not 100%)")
print("- GPP ROI should be -50% to +100% (not 900%)")
