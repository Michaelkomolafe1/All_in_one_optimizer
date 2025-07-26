import re

# Read the file
with open('core/unified_core_system.py', 'r') as f:
    content = f.read()

# Fix the imports
replacements = [
    # Remove old scoring imports
    (r'from integrated_scoring_system import.*\n', ''),
    (r'from step2_updated_player_model import.*\n', ''),
    (r'from cash_optimization_config import.*\n', ''),
    (r'from fixed_showdown_optimization import.*\n', ''),
    
    # Add data/ prefix to data source imports
    (r'from simple_statcast_fetcher import', 'from data.simple_statcast_fetcher import'),
    (r'from smart_confirmation_system import', 'from data.smart_confirmation_system import'),
    (r'from vegas_lines import', 'from data.vegas_lines import'),
    (r'from weather_integration import', 'from data.weather_integration import'),
    
    # Fix the class name
    (r'FastStatcastFetcher', 'SimpleStatcastFetcher'),
]

for old, new in replacements:
    content = re.sub(old, new, content)

# Write back
with open('core/unified_core_system.py', 'w') as f:
    f.write(content)

print("✅ Imports fixed!")
