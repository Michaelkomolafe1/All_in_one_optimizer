#!/usr/bin/env python3
# test_showdown.py

import os
from bulletproof_dfs_core import BulletproofDFSCore

# Find the CSV file
csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'DK' in f]
print(f"Found CSV files: {csv_files}")

if csv_files:
    core = BulletproofDFSCore()
    core.load_draftkings_csv(csv_files[0])  # Use first found CSV

    # Set some players as eligible for testing
    for player in core.players[:18]:
        player.is_confirmed = True
        player.confirmation_sources = ['test']

    core.set_optimization_mode('bulletproof')

    # Run the debug
    structure = core.debug_showdown_csv_structure()
else:
    print("No CSV files found")