# find_strategies.py
# Run this from your project root to find where your strategies are

import os
import ast


def find_function_in_files(function_name, search_dirs):
    """Find which file contains a function definition"""
    found_in = []

    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue

        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                            if f"def {function_name}" in content:
                                found_in.append(filepath)
                    except:
                        pass

    return found_in


# Functions to search for
strategies_to_find = [
    'build_balanced_optimal',
    'build_smart_stack',
    'build_truly_smart_stack',
    'build_game_stack_4_2',
    'build_game_stack_3_2',
    'build_projection_monster',
    'build_pitcher_dominance'
]

# Directories to search
search_dirs = [
    'strategies',
    'simulation',
    'config',
    'config/simulation_test',
    'internal/config/simulation_test',
    '.'
]

print("🔍 Searching for your strategy functions...")
print("=" * 60)

for strategy in strategies_to_find:
    locations = find_function_in_files(strategy, search_dirs)
    if locations:
        print(f"\n✅ {strategy}:")
        for loc in locations:
            print(f"   Found in: {loc}")
    else:
        print(f"\n❌ {strategy}: NOT FOUND")

print("\n" + "=" * 60)
print("💡 Now you know where your strategies are!")