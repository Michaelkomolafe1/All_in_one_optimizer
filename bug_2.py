#!/usr/bin/env python3
"""
COMPLETE ARCHITECTURE FIX FOR DFS OPTIMIZER
===========================================
Fixes all issues based on your actual code structure
"""

import os
import shutil
from datetime import datetime


def apply_architecture_fix():
    """Apply the complete fix based on actual architecture"""
    print("🏗️ DFS OPTIMIZER ARCHITECTURE FIX")
    print("=" * 60)

    gui_file = 'complete_dfs_gui_debug.py'

    if not os.path.exists(gui_file):
        print(f"❌ {gui_file} not found!")
        return False

    # Backup
    backup_file = f"{gui_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(gui_file, backup_file)
    print(f"✅ Created backup: {backup_file}")

    print("\n📚 YOUR ACTUAL ARCHITECTURE:")
    print("=" * 60)
    print("1. UnifiedPlayer - Data model with specific parameters:")
    print("   • id (required)")
    print("   • primary_position (not 'position')")
    print("   • positions (list, not string)")
    print("   • base_projection")
    print("\n2. BulletproofDFSCore - Coordinator that:")
    print("   • ✅ Has enrich_player_data()")
    print("   • ❌ Does NOT have load_players()")
    print("   • ❌ Does NOT have optimize()")
    print("\n3. UnifiedMILPOptimizer - The actual optimizer:")
    print("   • Takes list of UnifiedPlayer objects")
    print("   • Returns optimized lineup")
    print("\n4. Unified Scoring Engine - Calculates scores")

    # Read file
    with open(gui_file, 'r') as f:
        content = f.read()

    # Find OptimizationWorker class
    import re

    # Pattern to find the entire OptimizationWorker class
    pattern = r'class OptimizationWorker\(QThread\):.*?(?=\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        print("\n❌ Could not find OptimizationWorker class")
        return False

    # Replace with corrected version
    new_worker_class = get_corrected_worker_class()

    content = content[:match.start()] + new_worker_class + content[match.end():]

    # Ensure pandas is imported
    if 'import pandas as pd' not in content:
        # Add after other imports
        import_pattern = r'(from PyQt5.*?\n)'
        content = re.sub(import_pattern, r'\1import pandas as pd\n', content)

    # Write fixed file
    with open(gui_file, 'w') as f:
        f.write(content)

    print("\n✅ Applied architecture fixes!")
    print("\n🎯 WHAT THIS FIXES:")
    print("1. Uses correct UnifiedPlayer parameters")
    print("2. Creates players with id, primary_position, positions (list)")
    print("3. Uses UnifiedMILPOptimizer directly")
    print("4. Handles SP/RP positions correctly")
    print("5. Optional enrichment via BulletproofDFSCore")

    return True


def get_corrected_worker_class():
    """Get the corrected OptimizationWorker class"""
    return '''class OptimizationWorker(QThread):
    """Worker thread that correctly uses the DFS architecture"""

    progress = pyqtSignal(int, str)
    log = pyqtSignal(str, str)
    result = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, players_df, settings, csv_filename=None):
        super().__init__()
        self.players_df = players_df
        self.settings = settings
        self.csv_filename = csv_filename

    def run(self):
        """Run optimization using correct architecture"""
        try:
            self.progress.emit(10, "Initializing optimization...")
            self.log.emit("Using unified optimization system", "INFO")

            # Import modules
            try:
                from unified_player_model import UnifiedPlayer
                from unified_milp_optimizer import UnifiedMILPOptimizer
                from bulletproof_dfs_core import BulletproofDFSCore

                self.log.emit("✓ Modules loaded", "SUCCESS")
            except ImportError as e:
                self.log.emit(f"Module error: {e}", "ERROR")
                self.run_simple_fallback()
                return

            # Convert DataFrame to UnifiedPlayer objects
            self.progress.emit(25, "Creating player objects...")
            players = []

            for idx, row in self.players_df.iterrows():
                # Parse positions
                pos_str = str(row.get('Position', ''))
                positions = pos_str.split('/') if '/' in pos_str else [pos_str]
                primary = positions[0]

                # Create player with CORRECT parameters
                player = UnifiedPlayer(
                    id=str(row.get('ID', f"{row['Name']}_{idx}")),
                    name=row['Name'],
                    team=row.get('TeamAbbrev', 'UNK'),
                    salary=int(row['Salary']),
                    primary_position=primary,
                    positions=positions,
                    base_projection=float(row.get('AvgPointsPerGame', 0))
                )

                # Store display position
                player.display_position = pos_str
                players.append(player)

            self.log.emit(f"✓ Created {len(players)} players", "SUCCESS")

            # Optional enrichment
            self.progress.emit(40, "Enriching data...")
            try:
                core = BulletproofDFSCore(mode="optimization")
                core.players = players
                enriched = core.enrich_player_data()
                self.log.emit(f"✓ Enriched {enriched} players", "SUCCESS")
                players = core.players
            except:
                self.log.emit("Using base projections", "INFO")

            # Initialize optimizer
            self.progress.emit(60, "Running optimization...")
            optimizer = UnifiedMILPOptimizer()

            lineups = []
            for i in range(self.settings['num_lineups']):
                self.progress.emit(60 + 30 * i // self.settings['num_lineups'], 
                                 f"Lineup {i+1}/{self.settings['num_lineups']}...")

                try:
                    lineup_players, score = optimizer.optimize_lineup(
                        players,
                        strategy=self.settings['strategy'],
                        min_salary_pct=self.settings['min_salary'] / 100
                    )

                    if lineup_players:
                        lineup_data = {
                            'players': [],
                            'total_salary': 0,
                            'projected_points': score
                        }

                        # Convert to display format
                        for p in lineup_players:
                            lineup_data['players'].append({
                                'position': getattr(p, 'display_position', p.primary_position),
                                'name': p.name,
                                'salary': p.salary,
                                'team': p.team,
                                'points': getattr(p, 'enhanced_score', p.base_projection)
                            })
                            lineup_data['total_salary'] += p.salary

                        lineups.append(lineup_data)
                        self.log.emit(f"✓ Lineup {i+1}: {score:.1f} pts", "SUCCESS")
                except Exception as e:
                    self.log.emit(f"Lineup error: {e}", "ERROR")

            if lineups:
                self.progress.emit(100, "Complete!")
                self.result.emit(lineups)
            else:
                self.run_simple_fallback()

        except Exception as e:
            self.log.emit(f"Error: {str(e)}", "ERROR")
            self.error.emit(str(e))

    def run_simple_fallback(self):
        """Fallback optimization"""
        self.log.emit("Using fallback optimization", "INFO")
        lineups = []

        for i in range(self.settings['num_lineups']):
            lineup = self.generate_simple_lineup(i)
            if lineup:
                lineups.append(lineup)

        if lineups:
            self.progress.emit(100, "Complete!")
            self.result.emit(lineups)
        else:
            self.error.emit("Failed to generate lineups")

    def generate_simple_lineup(self, num):
        """Simple lineup for MLB with SP/RP"""
        positions = [
            {'need': 'P', 'accept': ['SP', 'RP']},
            {'need': 'P', 'accept': ['SP', 'RP']},
            {'need': 'C', 'accept': ['C', 'C/1B', '1B/C']},
            {'need': '1B', 'accept': ['1B', '1B/3B', '1B/C', '1B/OF', 'C/1B']},
            {'need': '2B', 'accept': ['2B', '2B/SS', '2B/3B', '2B/OF']},
            {'need': '3B', 'accept': ['3B', '1B/3B', '2B/3B', '3B/SS']},
            {'need': 'SS', 'accept': ['SS', '2B/SS', '3B/SS']},
            {'need': 'OF', 'accept': ['OF', '1B/OF', '2B/OF']},
            {'need': 'OF', 'accept': ['OF', '1B/OF', '2B/OF']},
            {'need': 'OF', 'accept': ['OF', '1B/OF', '2B/OF']}
        ]

        lineup = []
        used = set()
        total = 0

        # Add variety
        if num > 0:
            skip = self.players_df.nlargest(num * 2, 'Salary')['Name'].tolist()
            used.update(skip[:num])

        for pos in positions:
            mask = self.players_df['Position'].isin(pos['accept'])
            for p in pos['accept']:
                mask |= self.players_df['Position'].str.contains(p, na=False)

            available = self.players_df[mask & (~self.players_df['Name'].isin(used))]

            if not available.empty:
                if 'AvgPointsPerGame' in available.columns:
                    available = available.copy()
                    available['value'] = available['AvgPointsPerGame'] / available['Salary'] * 1000
                    player = available.nlargest(3, 'value').sample(1).iloc[0]
                else:
                    player = available.sample(1).iloc[0]

                lineup.append({
                    'position': pos['need'],
                    'name': player['Name'],
                    'salary': player['Salary'],
                    'team': player.get('TeamAbbrev', 'N/A'),
                    'points': player.get('AvgPointsPerGame', 0)
                })
                total += player['Salary']
                used.add(player['Name'])

        if len(lineup) >= 9:
            return {
                'players': lineup,
                'total_salary': total,
                'projected_points': sum(p['points'] for p in lineup)
            }
        return None


'''


def create_test_script():
    """Create a test script to verify the fix"""
    test_script = '''#!/usr/bin/env python3
"""Test the fixed architecture"""

import pandas as pd

# Test creating UnifiedPlayer correctly
print("🧪 TESTING UNIFIED PLAYER CREATION")
print("=" * 60)

try:
    from unified_player_model import UnifiedPlayer

    # Create test player with CORRECT parameters
    player = UnifiedPlayer(
        id="test123",
        name="Mike Trout",
        team="LAA",
        salary=10000,
        primary_position="OF",  # NOT 'position'
        positions=["OF"],       # List, not string
        base_projection=12.5
    )

    print("✅ UnifiedPlayer created successfully!")
    print(f"   Name: {player.name}")
    print(f"   Primary Position: {player.primary_position}")
    print(f"   Positions: {player.positions}")
    print(f"   Salary: ${player.salary}")

except Exception as e:
    print(f"❌ Error: {e}")

# Test BulletproofDFSCore methods
print("\\n🧪 TESTING BULLETPROOF DFS CORE")
print("=" * 60)

try:
    from bulletproof_dfs_core import BulletproofDFSCore

    core = BulletproofDFSCore(mode="test")

    print("Available methods:")
    methods = ['load_players', 'optimize', 'enrich_player_data', 'run_confirmation_analysis']
    for method in methods:
        if hasattr(core, method):
            print(f"  ✅ {method}")
        else:
            print(f"  ❌ {method} (not found)")

except Exception as e:
    print(f"❌ Error: {e}")

print("\\n✅ Test complete!")
print("\\nNow run: python complete_dfs_gui_debug.py")
'''

    with open('test_architecture.py', 'w') as f:
        f.write(test_script)

    print("\n✅ Created test_architecture.py")


def main():
    """Main function"""
    print("🚀 DFS OPTIMIZER COMPLETE ARCHITECTURE FIX")
    print("=" * 60)

    # Apply the fix
    if apply_architecture_fix():
        create_test_script()

        print("\n" + "=" * 60)
        print("✅ ARCHITECTURE FIX COMPLETE!")

        print("\n📋 SUMMARY OF CHANGES:")
        print("1. UnifiedPlayer now created with correct parameters:")
        print("   • id, primary_position, positions (list)")
        print("2. Uses UnifiedMILPOptimizer directly for optimization")
        print("3. Optional enrichment via BulletproofDFSCore")
        print("4. Handles SP/RP positions correctly")
        print("5. Falls back to simple generation if needed")

        print("\n🎯 NEXT STEPS:")
        print("1. Test the architecture: python test_architecture.py")
        print("2. Run your GUI: python complete_dfs_gui_debug.py")
        print("3. Load your CSV and optimize!")

    else:
        print("\n❌ Fix failed - apply manually")
        print("Replace OptimizationWorker class in your GUI")


if __name__ == "__main__":
    main()