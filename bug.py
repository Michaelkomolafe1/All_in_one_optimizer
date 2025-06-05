#!/usr/bin/env python3
"""
REORGANIZE DFS OPTIMIZER PROJECT
================================
Automatically organize files into proper structure
"""

import os
import shutil
from pathlib import Path


def create_test_csv():
    """Create a test CSV file for testing"""
    csv_content = """Position,Name,Name,ID,Roster Position,Salary,Game Info,TeamAbbrev,AvgPointsPerGame
P,Gerrit Cole,Gerrit Cole,1001,P,10500,NYY@BOS 07:10PM ET,NYY,18.5
P,Shane Bieber,Shane Bieber,1002,P,9800,CLE@MIN 08:10PM ET,CLE,17.2
P,Dylan Cease,Dylan Cease,1003,P,8200,SD@LAD 10:10PM ET,SD,15.8
C,Will Smith,Will Smith,2001,C,4800,LAD@SD 10:10PM ET,LAD,9.5
C,Salvador Perez,Salvador Perez,2002,C,4200,KC@DET 07:10PM ET,KC,8.2
1B,Freddie Freeman,Freddie Freeman,3001,1B,5500,LAD@SD 10:10PM ET,LAD,11.2
1B,Vladimir Guerrero Jr.,Vladimir Guerrero Jr.,3002,1B,5200,TOR@TB 07:10PM ET,TOR,10.8
2B,Jose Altuve,Jose Altuve,4001,2B,5000,HOU@TEX 08:05PM ET,HOU,10.5
2B,Marcus Semien,Marcus Semien,4002,2B,4600,TEX@HOU 08:05PM ET,TEX,9.2
3B,Manny Machado,Manny Machado,5001,3B,5100,SD@LAD 10:10PM ET,SD,10.8
3B,Jose Ramirez,Jose Ramirez,5002,3B,5400,CLE@MIN 08:10PM ET,CLE,11.5
SS,Trea Turner,Trea Turner,6001,SS,5300,PHI@NYM 07:10PM ET,PHI,10.9
SS,Corey Seager,Corey Seager,6002,SS,5100,TEX@HOU 08:05PM ET,TEX,10.5
OF,Aaron Judge,Aaron Judge,7001,OF,6200,NYY@BOS 07:10PM ET,NYY,13.5
OF,Mike Trout,Mike Trout,7002,OF,5800,LAA@SEA 09:40PM ET,LAA,12.2
OF,Mookie Betts,Mookie Betts,7003,OF,5600,LAD@SD 10:10PM ET,LAD,11.8
OF,Ronald Acuna Jr.,Ronald Acuna Jr.,7004,OF,5900,ATL@MIA 06:40PM ET,ATL,12.5
OF,Juan Soto,Juan Soto,7005,OF,5400,SD@LAD 10:10PM ET,SD,11.2
OF,Shohei Ohtani,Shohei Ohtani,7006,OF,6000,LAA@SEA 09:40PM ET,LAA,12.8
OF,Yordan Alvarez,Yordan Alvarez,7007,OF,5200,HOU@TEX 08:05PM ET,HOU,10.9"""

    with open('DKSalaries_test.csv', 'w') as f:
        f.write(csv_content)
    print("✅ Created DKSalaries_test.csv for testing")


def reorganize_project():
    """Reorganize project files into proper structure"""
    print("🔧 REORGANIZING DFS OPTIMIZER PROJECT")
    print("=" * 50)

    # Create directory structure
    dirs_to_create = [
        'core',
        'data_sources',
        'gui',
        'tests',
        'data/cache',
        'data/vegas',
        'data/statcast_cache'
    ]

    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    print("✅ Created directory structure")

    # File mappings (source -> destination)
    file_moves = {
        # Core files
        'bulletproof_dfs_core.py': 'core/bulletproof_dfs_core.py',
        'optimal_lineup_optimizer.py': 'core/optimal_lineup_optimizer.py',
        'unified_data_system.py': 'core/unified_data_system.py',
        'unified_player_model.py': 'core/unified_player_model.py',
        'smart_confirmation_system.py': 'core/smart_confirmation_system.py',

        # Data source files
        'vegas_lines.py': 'data_sources/vegas_lines.py',
        'simple_statcast_fetcher.py': 'data_sources/simple_statcast_fetcher.py',
        'enhanced_stats_engine.py': 'data_sources/enhanced_stats_engine.py',
        'universal_csv_parser.py': 'data_sources/universal_csv_parser.py',

        # GUI files
        'enhanced_dfs_gui.py': 'gui/enhanced_dfs_gui.py',

        # Test files
        'test_optimizations.py': 'tests/test_optimizations.py',
        'test_new_optimizer.py': 'tests/test_new_optimizer.py'
    }

    # Copy files to new locations (don't move yet in case something goes wrong)
    copied = 0
    for src, dst in file_moves.items():
        if os.path.exists(src) and src != dst:
            try:
                shutil.copy2(src, dst)
                copied += 1
                print(f"  📄 Copied {src} → {dst}")
            except Exception as e:
                print(f"  ⚠️ Failed to copy {src}: {e}")

    print(f"\n✅ Copied {copied} files to new structure")

    # Create __init__.py files for packages
    init_files = [
        'core/__init__.py',
        'data_sources/__init__.py',
        'gui/__init__.py',
        'tests/__init__.py'
    ]

    for init_file in init_files:
        Path(init_file).touch()

    print("✅ Created __init__.py files")

    # Update imports in moved files
    update_imports_in_files()

    # Files to delete (old/redundant)
    files_to_delete = [
        'bug.py',
        'core_optimizations.txt',
        'position_flex_analyzer.py',
        'smart_lineup_validator.py',
        'migration_script.py'
    ]

    print("\n🗑️ Files marked for deletion:")
    for file in files_to_delete:
        if os.path.exists(file):
            print(f"  ❌ {file}")

    # Create test CSV
    create_test_csv()

    print("\n✅ REORGANIZATION COMPLETE!")
    print("\n📋 Next steps:")
    print("1. Review the new structure in core/, data_sources/, gui/, tests/")
    print("2. Test with: python tests/test_optimizations.py")
    print("3. If everything works, delete the original files")
    print("4. Delete files marked above with ❌")


def update_imports_in_files():
    """Update import statements in moved files"""
    print("\n🔄 Updating imports...")

    # Import updates needed
    import_updates = {
        'core/bulletproof_dfs_core.py': [
            ('from unified_data_system import', 'from core.unified_data_system import'),
            ('from optimal_lineup_optimizer import', 'from core.optimal_lineup_optimizer import'),
            ('from smart_confirmation_system import', 'from core.smart_confirmation_system import'),
            ('from unified_player_model import', 'from core.unified_player_model import'),
            ('from enhanced_stats_engine import', 'from data_sources.enhanced_stats_engine import'),
            ('from simple_statcast_fetcher import', 'from data_sources.simple_statcast_fetcher import'),
            ('from vegas_lines import', 'from data_sources.vegas_lines import')
        ],
        'gui/enhanced_dfs_gui.py': [
            ('from bulletproof_dfs_core import', 'from core.bulletproof_dfs_core import'),
            ('from unified_data_system import', 'from core.unified_data_system import'),
            ('from optimal_lineup_optimizer import', 'from core.optimal_lineup_optimizer import'),
            ('from smart_confirmation_system import', 'from core.smart_confirmation_system import')
        ]
    }

    for file_path, replacements in import_updates.items():
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                for old, new in replacements:
                    content = content.replace(old, new)

                with open(file_path, 'w') as f:
                    f.write(content)

                print(f"  ✅ Updated imports in {file_path}")
            except Exception as e:
                print(f"  ⚠️ Failed to update {file_path}: {e}")


def create_simple_test():
    """Create a simple test script that works with new structure"""
    test_content = '''#!/usr/bin/env python3
"""Simple test for reorganized DFS Optimizer"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.bulletproof_dfs_core import BulletproofDFSCore
from utils.profiler import profiler

def test_basic_optimization():
    """Test basic optimization flow"""
    print("🧪 TESTING REORGANIZED DFS OPTIMIZER")
    print("=" * 50)

    # Initialize
    core = BulletproofDFSCore()

    # Load test CSV
    if core.load_draftkings_csv("DKSalaries_test.csv"):
        print("✅ Loaded test data")

        # Add manual selections
        core.apply_manual_selection("Mike Trout, Shohei Ohtani")

        # Optimize
        lineup, score = core.optimize_lineup_with_mode()

        if lineup:
            print(f"\\n✅ Generated lineup with score: {score:.2f}")
            for player in lineup[:5]:  # Show first 5
                print(f"  - {player.name}")
        else:
            print("❌ No lineup generated")
    else:
        print("❌ Failed to load CSV")

if __name__ == "__main__":
    test_basic_optimization()
'''

    with open('tests/test_simple.py', 'w') as f:
        f.write(test_content)
    print("✅ Created tests/test_simple.py")


if __name__ == "__main__":
    import sys

    print("⚠️ This will reorganize your project structure.")
    print("   Original files will be COPIED (not moved) to new locations.")
    print("   You can delete originals after verifying everything works.")

    response = input("\nProceed? (y/n): ").lower()

    if response == 'y':
        reorganize_project()
        create_simple_test()
    else:
        print("Cancelled.")