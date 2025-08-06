#!/usr/bin/env python3
import sys
sys.path.insert(0, 'main_optimizer')
sys.path.insert(0, 'simulation')
from comprehensive_simulation_runner import ComprehensiveSimulationRunner
runner = ComprehensiveSimulationRunner()
runner.run_comprehensive_test(num_simulations=100, contest_types=['cash', 'gpp'], slate_sizes=['small', 'medium', 'large'], field_size=100)
