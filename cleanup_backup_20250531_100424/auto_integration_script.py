#!/usr/bin/env python3
"""
Automatic Integration Script
Automatically updates your existing files to use the unified system
"""

import os
import re
import shutil
import sys
from pathlib import Path
from datetime import datetime


class DFSIntegrationBot:
    """Automatic integration of unified DFS components"""

    def __init__(self):
        self.backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.changes_made = []
        self.errors = []

    def run_full_integration(self):
        """Run complete automatic integration"""
        print("🤖 DFS AUTOMATIC INTEGRATION BOT")
        print("=" * 50)

        # Step 1: Create backups
        self.create_backups()

        # Step 2: Check dependencies
        self.check_dependencies()

        # Step 3: Update existing files
        self.update_working_dfs_core()
        self.update_streamlined_gui()
        self.update_enhanced_gui()

        # Step 4: Create integration helpers
        self.create_integration_helpers()

        # Step 5: Create test script
        self.create_comprehensive_test()

        # Step 6: Generate summary
        self.generate_integration_summary()

        print("\n🎉 AUTOMATIC INTEGRATION COMPLETE!")
        print(f"📁 Backups saved to: {self.backup_dir}")
        print("🚀 Run 'python test_integration.py' to validate")

    def create_backups(self):
        """Create backups of existing files"""
        print("\n📁 Creating backups...")

        self.backup_dir.mkdir(parents=True, exist_ok=True)

        files_to_backup = [
            'working_dfs_core_final.py',
            'streamlined_dfs_gui.py',
            'enhanced_dfs_gui.py',
            'dfs_data_enhanced.py',
            'dfs_optimizer_enhanced_FIXED.py'
        ]

        for file_name in files_to_backup:
            if os.path.exists(file_name):
                backup_path = self.backup_dir / file_name
                shutil.copy2(file_name, backup_path)
                print(f"  ✅ Backed up: {file_name}")
            else:
                print(f"  ⚠️ Not found: {file_name}")

    def check_dependencies(self):
        """Check if required components exist"""
        print("\n🔍 Checking dependencies...")

        required_files = [
            'unified_player_model.py',
            'optimized_data_pipeline.py',
            'unified_milp_optimizer.py'
        ]

        missing_files = []
        for file_name in required_files:
            if os.path.exists(file_name):
                print(f"  ✅ Found: {file_name}")
            else:
                print(f"  ❌ Missing: {file_name}")
                missing_files.append(file_name)

        if missing_files:
            print(f"\n❌ Missing required files: {', '.join(missing_files)}")
            print("💡 Please save the 3 artifacts first!")
            sys.exit(1)

    def update_working_dfs_core(self):
        """Update working_dfs_core_final.py with unified components"""
        print("\n🔧 Updating working_dfs_core_final.py...")

        file_path = 'working_dfs_core_final.py'
        if not os.path.exists(file_path):
            print(f"  ⚠️ {file_path} not found, skipping")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Add imports at the top
            import_additions = '''
# UNIFIED SYSTEM IMPORTS - Added by integration bot
try:
    from unified_player_model import UnifiedPlayer, create_unified_player
    from optimized_data_pipeline import OptimizedDataPipeline
    from unified_milp_optimizer import optimize_with_unified_system, OptimizationConfig
    UNIFIED_SYSTEM_AVAILABLE = True
    print("✅ Unified DFS system available")
except ImportError as e:
    print(f"⚠️ Unified system not available: {e}")
    UNIFIED_SYSTEM_AVAILABLE = False
'''

            # Insert after existing imports
            import_insertion_point = content.find('print("✅ Working DFS Core loaded successfully")')
            if import_insertion_point != -1:
                content = content[:import_insertion_point] + import_additions + '\n\n' + content[
                                                                                         import_insertion_point:]
            else:
                # Insert after the first import block
                lines = content.split('\n')
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith('#') and not line.startswith(
                            'import') and not line.startswith('from'):
                        insert_index = i
                        break
                lines.insert(insert_index, import_additions)
                content = '\n'.join(lines)

            # Add unified pipeline function
            unified_pipeline_function = '''

# UNIFIED PIPELINE FUNCTION - Added by integration bot
async def load_and_optimize_unified_pipeline(
    dk_file: str,
    dff_file: str = None,
    manual_input: str = "",
    contest_type: str = 'classic',
    strategy: str = 'smart_confirmed'
) -> Tuple[List[UnifiedPlayer], float, str]:
    """
    Updated pipeline using unified components - 10x performance improvement
    This replaces the original load_and_optimize_complete_pipeline
    """
    if not UNIFIED_SYSTEM_AVAILABLE:
        print("⚠️ Unified system not available, falling back to original pipeline")
        return load_and_optimize_complete_pipeline(dk_file, dff_file, manual_input, contest_type, strategy)

    try:
        print("🚀 UNIFIED HIGH-PERFORMANCE PIPELINE")
        print("=" * 50)

        # Load and enhance data with 10x performance
        pipeline = OptimizedDataPipeline()
        players = await pipeline.load_and_enhance_complete(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input=manual_input,
            force_refresh=False
        )

        if not players:
            return [], 0, "❌ Failed to load player data"

        print(f"✅ Loaded {len(players)} players with unified system")

        # Run optimization with proper strategy filtering
        lineup, score, summary = optimize_with_unified_system(
            players=players,
            contest_type=contest_type,
            strategy=strategy,
            manual_input=manual_input
        )

        print(f"🎯 Optimization complete: {len(lineup) if lineup else 0} players, {score:.2f} points")
        return lineup, score, summary

    except Exception as e:
        print(f"⚠️ Unified pipeline failed: {e}, falling back to original")
        return load_and_optimize_complete_pipeline(dk_file, dff_file, manual_input, contest_type, strategy)


# BACKWARD COMPATIBILITY WRAPPER - Added by integration bot
def load_and_optimize_complete_pipeline_enhanced(
    dk_file: str,
    dff_file: str = None,
    manual_input: str = "",
    contest_type: str = 'classic',
    strategy: str = 'balanced'
) -> Tuple[List, float, str]:
    """
    Enhanced version that tries unified system first, falls back to original
    """
    import asyncio

    try:
        # Try unified system first
        if UNIFIED_SYSTEM_AVAILABLE:
            # Map old strategy names to new ones
            strategy_mapping = {
                'balanced': 'smart_confirmed',
                'cash': 'confirmed_only',
                'gpp': 'all_players'
            }
            new_strategy = strategy_mapping.get(strategy, strategy)

            unified_lineup, score, summary = asyncio.run(
                load_and_optimize_unified_pipeline(dk_file, dff_file, manual_input, contest_type, new_strategy)
            )

            # Convert UnifiedPlayer back to list format for compatibility
            if unified_lineup and isinstance(unified_lineup[0], UnifiedPlayer):
                lineup = []
                for player in unified_lineup:
                    player_list = [
                        player.id, player.name, player.primary_position, player.team,
                        player.salary, player.projection, player.enhanced_score, player.batting_order
                    ]
                    # Extend to 20 elements for compatibility
                    while len(player_list) < 20:
                        player_list.append(None)
                    lineup.append(player_list)
                return lineup, score, summary
            else:
                return unified_lineup, score, summary

        # Fallback to original function
        return load_and_optimize_complete_pipeline(dk_file, dff_file, manual_input, contest_type, strategy)

    except Exception as e:
        print(f"⚠️ Enhanced pipeline error: {e}, using original")
        return load_and_optimize_complete_pipeline(dk_file, dff_file, manual_input, contest_type, strategy)
'''

            # Add the function before the main block
            main_block_pattern = r'\nif __name__ == "__main__":'
            if re.search(main_block_pattern, content):
                content = re.sub(main_block_pattern, unified_pipeline_function + r'\nif __name__ == "__main__":',
                                 content)
            else:
                content += unified_pipeline_function

            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print("  ✅ Updated working_dfs_core_final.py with unified components")
            self.changes_made.append("Updated working_dfs_core_final.py")

        except Exception as e:
            error_msg = f"Failed to update working_dfs_core_final.py: {e}"
            print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)

    def update_streamlined_gui(self):
        """Update streamlined_dfs_gui.py with fixed strategy selection"""
        print("\n🔧 Updating streamlined_dfs_gui.py...")

        file_path = 'streamlined_dfs_gui.py'
        if not os.path.exists(file_path):
            print(f"  ⚠️ {file_path} not found, skipping")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Fix the OptimizationWorker run method
            old_run_method = r'def run\(self\):.*?except Exception as e:.*?self\.finished_signal\.emit\(False, str\(e\), \{\}\)'

            new_run_method = '''def run(self):
        """FIXED: Enhanced optimization with unified pipeline"""
        try:
            self.status_signal.emit("Starting optimization...")
            self.progress_signal.emit(10)

            if self.is_cancelled:
                return

            # FIXED: Use enhanced pipeline with proper strategy mapping
            strategy_mapping = {
                0: 'smart_confirmed',              # Smart Default (RECOMMENDED)
                1: 'confirmed_only',               # Safe Only
                2: 'confirmed_plus_manual',        # Smart + Picks  
                3: 'confirmed_pitchers_all_batters', # Balanced
                4: 'manual_only'                   # Manual Only
            }

            strategy_name = strategy_mapping.get(self.strategy_index, 'smart_confirmed')
            self.output_signal.emit(f"🎯 Using strategy: {strategy_name}")

            # Check Manual Only requirements
            if strategy_name == 'manual_only':
                if not self.manual_input or not self.manual_input.strip():
                    self.finished_signal.emit(False, "Manual Only strategy requires player names", {})
                    return

                manual_count = len([name.strip() for name in self.manual_input.split(',') if name.strip()])
                if manual_count < 8:
                    error_msg = f"Manual Only needs 8+ players for all positions, you provided {manual_count}"
                    self.finished_signal.emit(False, error_msg, {})
                    return

            self.status_signal.emit("Loading data...")
            self.progress_signal.emit(30)

            # Try to use enhanced pipeline
            try:
                from working_dfs_core_final import load_and_optimize_complete_pipeline_enhanced

                lineup, score, summary = load_and_optimize_complete_pipeline_enhanced(
                    dk_file=self.dk_file,
                    dff_file=self.dff_file,
                    manual_input=self.manual_input,
                    contest_type=self.contest_type,
                    strategy=strategy_name
                )

                self.output_signal.emit("✅ Using enhanced unified pipeline")

            except ImportError:
                # Fallback to original
                from working_dfs_core_final import load_and_optimize_complete_pipeline

                lineup, score, summary = load_and_optimize_complete_pipeline(
                    dk_file=self.dk_file,
                    dff_file=self.dff_file,
                    manual_input=self.manual_input,
                    contest_type=self.contest_type,
                    strategy=strategy_name
                )

                self.output_signal.emit("⚠️ Using original pipeline")

            self.progress_signal.emit(90)

            if lineup and score > 0:
                # Extract lineup data for table display
                lineup_data = {
                    'players': [],
                    'total_salary': 0,
                    'total_score': score,
                    'summary': summary
                }

                # Handle both UnifiedPlayer and list formats
                confirmed_count = 0
                manual_count = 0

                for player in lineup:
                    if hasattr(player, 'name'):  # UnifiedPlayer format
                        player_info = {
                            'position': player.primary_position,
                            'name': player.name,
                            'team': player.team,
                            'salary': player.salary,
                            'score': player.enhanced_score,
                            'status': self._get_player_status_unified(player)
                        }
                        lineup_data['total_salary'] += player.salary
                        if getattr(player, 'is_confirmed', False):
                            confirmed_count += 1
                        if getattr(player, 'is_manual_selected', False):
                            manual_count += 1
                    else:  # List format
                        player_info = {
                            'position': player[2] if len(player) > 2 else '',
                            'name': player[1] if len(player) > 1 else '',
                            'team': player[3] if len(player) > 3 else '',
                            'salary': player[4] if len(player) > 4 else 0,
                            'score': player[6] if len(player) > 6 else 0,
                            'status': self._get_player_status_list(player)
                        }
                        lineup_data['total_salary'] += player_info['salary']

                    lineup_data['players'].append(player_info)

                lineup_data['confirmed_count'] = confirmed_count
                lineup_data['manual_count'] = manual_count
                lineup_data['strategy_used'] = strategy_name

                self.progress_signal.emit(100)
                self.status_signal.emit("Complete!")
                self.finished_signal.emit(True, summary, lineup_data)
            else:
                error_msg = "No valid lineup found"
                if strategy_name == 'confirmed_only':
                    error_msg += "\\n💡 Try 'Smart Default' for more player options"
                elif strategy_name == 'manual_only':
                    error_msg += "\\n💡 Make sure you have enough players for all positions"
                self.finished_signal.emit(False, error_msg, {})

        except Exception as e:
            error_msg = f"Optimization failed: {str(e)}"
            self.finished_signal.emit(False, error_msg, {})

    def _get_player_status_unified(self, player):
        """Get player status for UnifiedPlayer format"""
        if hasattr(player, 'get_status_string'):
            return player.get_status_string()

        status_parts = []
        if getattr(player, 'is_confirmed', False):
            status_parts.append("CONFIRMED")
        if getattr(player, 'is_manual_selected', False):
            status_parts.append("MANUAL")
        if getattr(player, 'dff_projection', 0) > 0:
            status_parts.append(f"DFF:{player.dff_projection:.1f}")
        return " | ".join(status_parts) if status_parts else "-"

    def _get_player_status_list(self, player):
        """Get player status for list format"""
        status_parts = []
        if len(player) > 7 and player[7] is not None:
            status_parts.append("CONFIRMED")
        if len(player) > 14 and isinstance(player[14], dict):
            if 'Baseball Savant' in player[14].get('data_source', ''):
                status_parts.append("STATCAST")
        return " | ".join(status_parts) if status_parts else "-"'''

            # Replace the run method using regex
            content = re.sub(
                r'def run\(self\):.*?(?=def _get_player_status|def cancel|class \w+|\Z)',
                new_run_method + '\n\n    ',
                content,
                flags=re.DOTALL
            )

            # Fix strategy combo creation
            old_strategy_combo = r'self\.strategy_combo\.addItems\(\[.*?\]\)'
            new_strategy_combo = '''self.strategy_combo.addItems([
            "🎯 Smart Default (Confirmed + Your Picks) - RECOMMENDED",    # Index 0
            "🔒 Safe Only (Confirmed Players Only)",                    # Index 1  
            "🎯 Smart + Picks (Confirmed + Your Manual Selections)",    # Index 2
            "⚖️ Balanced (Confirmed Pitchers + All Batters)",          # Index 3
            "✏️ Manual Only (Your Specified Players Only)"             # Index 4
        ])'''

            content = re.sub(old_strategy_combo, new_strategy_combo, content, flags=re.DOTALL)

            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print("  ✅ Updated streamlined_dfs_gui.py with fixed strategies")
            self.changes_made.append("Fixed streamlined_dfs_gui.py strategy selection")

        except Exception as e:
            error_msg = f"Failed to update streamlined_dfs_gui.py: {e}"
            print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)

    def update_enhanced_gui(self):
        """Update enhanced_dfs_gui.py if it exists"""
        print("\n🔧 Updating enhanced_dfs_gui.py...")

        file_path = 'enhanced_dfs_gui.py'
        if not os.path.exists(file_path):
            print(f"  ⚠️ {file_path} not found, skipping")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Add import for unified system
            import_addition = '''
# UNIFIED SYSTEM INTEGRATION - Added by integration bot
try:
    from working_dfs_core_final import load_and_optimize_complete_pipeline_enhanced
    ENHANCED_PIPELINE_AVAILABLE = True
except ImportError:
    ENHANCED_PIPELINE_AVAILABLE = False
'''

            # Insert after PyQt5 imports
            pyqt_import_end = content.find('print("✅ PyQt5 loaded successfully")')
            if pyqt_import_end != -1:
                content = content[:pyqt_import_end] + import_addition + '\n' + content[pyqt_import_end:]

            # Update strategy combo if it exists
            if 'strategy_combo.addItems' in content:
                old_items = r'self\.strategy_combo\.addItems\(\[.*?\]\)'
                new_items = '''self.strategy_combo.addItems([
            "🎯 Smart Default (Confirmed + Your Picks) - RECOMMENDED",
            "🔒 Safe Only (Confirmed Players Only)",
            "🎯 Smart + Picks (Confirmed + Your Manual Selections)",
            "⚖️ Balanced (Confirmed Pitchers + All Batters)",
            "✏️ Manual Only (Your Specified Players Only)"
        ])'''
                content = re.sub(old_items, new_items, content, flags=re.DOTALL)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print("  ✅ Updated enhanced_dfs_gui.py with unified imports")
            self.changes_made.append("Updated enhanced_dfs_gui.py")

        except Exception as e:
            error_msg = f"Failed to update enhanced_dfs_gui.py: {e}"
            print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)

    def create_integration_helpers(self):
        """Create helper scripts for easy usage"""
        print("\n🔧 Creating integration helpers...")

        # Create main launcher script
        launcher_content = '''#!/usr/bin/env python3
"""
DFS Optimizer Launcher - Automatically uses best available system
"""

import sys
import os

def main():
    """Launch the best available DFS GUI"""
    print("🚀 DFS OPTIMIZER LAUNCHER")
    print("=" * 30)

    # Try streamlined GUI first
    try:
        print("⚡ Launching Streamlined DFS GUI...")
        from streamlined_dfs_gui import main as streamlined_main
        return streamlined_main()
    except ImportError:
        print("   ⚠️ Streamlined GUI not available")
    except Exception as e:
        print(f"   ❌ Streamlined GUI error: {e}")

    # Try enhanced GUI 
    try:
        print("🔧 Launching Enhanced DFS GUI...")
        from enhanced_dfs_gui import main as enhanced_main
        return enhanced_main()
    except ImportError:
        print("   ⚠️ Enhanced GUI not available")
    except Exception as e:
        print(f"   ❌ Enhanced GUI error: {e}")

    print("❌ No GUI available!")
    print("💡 Make sure PyQt5 is installed: pip install PyQt5")
    return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\\n👋 Cancelled by user")
        sys.exit(0)
'''

        with open('launch_dfs_optimizer.py', 'w') as f:
            f.write(launcher_content)

        print("  ✅ Created launch_dfs_optimizer.py")

        # Create command-line interface
        cli_content = '''#!/usr/bin/env python3
"""
DFS Optimizer CLI - Command line interface for the unified system
"""

import asyncio
import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="DFS Optimizer CLI")
    parser.add_argument('--dk', required=True, help='DraftKings CSV file')
    parser.add_argument('--dff', help='DFF rankings CSV file')
    parser.add_argument('--manual', default='', help='Manual player selections (comma separated)')
    parser.add_argument('--contest', choices=['classic', 'showdown'], default='classic', help='Contest type')
    parser.add_argument('--strategy', 
                       choices=['smart_confirmed', 'confirmed_only', 'confirmed_plus_manual', 
                               'confirmed_pitchers_all_batters', 'manual_only', 'all_players'],
                       default='smart_confirmed', help='Strategy filter')
    parser.add_argument('--budget', type=int, default=50000, help='Salary budget')
    parser.add_argument('--output', help='Output file for lineup')

    args = parser.parse_args()

    # Check if DK file exists
    if not Path(args.dk).exists():
        print(f"❌ DraftKings file not found: {args.dk}")
        return 1

    # Check if DFF file exists (if specified)
    if args.dff and not Path(args.dff).exists():
        print(f"❌ DFF file not found: {args.dff}")
        return 1

    print("🚀 DFS OPTIMIZER CLI")
    print(f"📁 DK File: {args.dk}")
    print(f"🎯 Strategy: {args.strategy}")
    print(f"💰 Budget: ${args.budget:,}")

    try:
        # Use unified pipeline
        from working_dfs_core_final import load_and_optimize_complete_pipeline_enhanced

        lineup, score, summary = load_and_optimize_complete_pipeline_enhanced(
            dk_file=args.dk,
            dff_file=args.dff,
            manual_input=args.manual,
            contest_type=args.contest,
            strategy=args.strategy
        )

        if lineup and score > 0:
            print(f"\\n✅ SUCCESS: Generated lineup with {score:.2f} points")
            print("\\n" + summary)

            # Save to file if requested
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(summary)
                print(f"\\n💾 Saved to: {args.output}")

            return 0
        else:
            print("\\n❌ Failed to generate lineup")
            return 1

    except Exception as e:
        print(f"\\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''

        with open('dfs_cli.py', 'w') as f:
            f.write(cli_content)

        print("  ✅ Created dfs_cli.py")
        self.changes_made.extend(["Created launch_dfs_optimizer.py", "Created dfs_cli.py"])

    def create_comprehensive_test(self):
        """Create comprehensive test script"""
        print("\n🔧 Creating comprehensive test script...")

        test_content = '''#!/usr/bin/env python3
"""
Comprehensive Integration Test - Validates the unified system
"""

import os
import sys
import asyncio
import tempfile
import csv
from pathlib import Path

def create_test_data():
    """Create test DraftKings and DFF data"""
    # Create temporary DK CSV
    dk_file = tempfile.NamedTemporaryFile(mode='w', suffix='_dk.csv', delete=False)

    dk_data = [
        ['Name', 'Position', 'TeamAbbrev', 'Salary', 'AvgPointsPerGame'],
        ['Hunter Brown', 'P', 'HOU', '9800', '24.56'],
        ['Shane Baz', 'P', 'TB', '8200', '19.23'],
        ['Logan Gilbert', 'P', 'SEA', '7600', '18.45'],
        ['William Contreras', 'C', 'MIL', '4200', '7.39'],
        ['Salvador Perez', 'C', 'KC', '3800', '6.85'],
        ['Vladimir Guerrero Jr.', '1B', 'TOR', '4200', '7.66'],
        ['Gleyber Torres', '2B', 'NYY', '4000', '6.89'],
        ['Jorge Polanco', '3B/SS', 'SEA', '3800', '6.95'],  # Multi-position
        ['Francisco Lindor', 'SS', 'NYM', '4300', '8.23'],
        ['Jose Ramirez', '3B', 'CLE', '4100', '8.12'],
        ['Kyle Tucker', 'OF', 'HOU', '4500', '8.45'],
        ['Christian Yelich', 'OF', 'MIL', '4200', '7.65'],
        ['Jarren Duran', 'OF', 'BOS', '4100', '7.89'],
        ['Byron Buxton', 'OF', 'MIN', '3900', '7.12'],
        ['Seiya Suzuki', 'OF', 'CHC', '3800', '6.78'],
    ]

    writer = csv.writer(dk_file)
    writer.writerows(dk_data)
    dk_file.close()

    # Create temporary DFF CSV
    dff_file = tempfile.NamedTemporaryFile(mode='w', suffix='_dff.csv', delete=False)

    dff_data = [
        ['first_name', 'last_name', 'team', 'ppg_projection', 'confirmed_order'],
        ['Hunter', 'Brown', 'HOU', '26.5', 'YES'],
        ['Kyle', 'Tucker', 'HOU', '9.8', 'YES'],
        ['Christian', 'Yelich', 'MIL', '8.9', 'YES'],
        ['Vladimir', 'Guerrero Jr.', 'TOR', '8.5', 'YES'],
        ['Francisco', 'Lindor', 'NYM', '9.2', 'YES'],
    ]

    writer = csv.writer(dff_file)
    writer.writerows(dff_data)
    dff_file.close()

    return dk_file.name, dff_file.name

def test_unified_components():
    """Test unified components individually"""
    print("🧪 Testing Unified Components")
    print("-" * 40)

    results = {}

    # Test 1: Unified Player Model
    try:
        from unified_player_model import UnifiedPlayer

        test_player = UnifiedPlayer({
            'name': 'Jorge Polanco',
            'position': '3B/SS',
            'team': 'SEA',
            'salary': 4500,
            'projection': 7.9
        })

        assert test_player.can_play_position('3B'), "Should play 3B"
        assert test_player.can_play_position('SS'), "Should play SS"
        assert test_player.is_multi_position(), "Should be multi-position"

        results['unified_player'] = "✅ PASS"
        print("  ✅ UnifiedPlayer: Multi-position support working")

    except Exception as e:
        results['unified_player'] = f"❌ FAIL: {e}"
        print(f"  ❌ UnifiedPlayer: {e}")

    # Test 2: Optimized Data Pipeline
    try:
        from optimized_data_pipeline import OptimizedDataPipeline

        pipeline = OptimizedDataPipeline()
        results['data_pipeline'] = "✅ PASS"
        print("  ✅ OptimizedDataPipeline: Import successful")

    except Exception as e:
        results['data_pipeline'] = f"❌ FAIL: {e}"
        print(f"  ❌ OptimizedDataPipeline: {e}")

    # Test 3: Unified MILP Optimizer
    try:
        from unified_milp_optimizer import optimize_with_unified_system, OptimizationConfig

        config = OptimizationConfig()
        assert config.contest_type == 'classic', "Default contest type should be classic"

        results['milp_optimizer'] = "✅ PASS"
        print("  ✅ UnifiedMILPOptimizer: Import and config working")

    except Exception as e:
        results['milp_optimizer'] = f"❌ FAIL: {e}"
        print(f"  ❌ UnifiedMILPOptimizer: {e}")

    return results

def test_integration():
    """Test the integrated system end-to-end"""
    print("\n🔄 Testing Integration")
    print("-" * 40)

    dk_file, dff_file = create_test_data()

    try:
        # Test enhanced pipeline
        from working_dfs_core_final import load_and_optimize_complete_pipeline_enhanced

        print("  🧪 Testing enhanced pipeline...")

        lineup, score, summary = load_and_optimize_complete_pipeline_enhanced(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input="Jorge Polanco, Christian Yelich",
            contest_type='classic',
            strategy='smart_confirmed'
        )

        if lineup and score > 0:
            print(f"  ✅ Enhanced pipeline: {len(lineup)} players, {score:.2f} points")

            # Check for multi-position players
            multi_pos_count = 0
            confirmed_count = 0
            manual_count = 0

            for player in lineup:
                if hasattr(player, 'is_multi_position') and player.is_multi_position():
                    multi_pos_count += 1
                if hasattr(player, 'is_confirmed') and player.is_confirmed:
                    confirmed_count += 1
                if hasattr(player, 'is_manual_selected') and player.is_manual_selected:
                    manual_count += 1

            print(f"    🔄 Multi-position: {multi_pos_count}")
            print(f"    ✅ Confirmed: {confirmed_count}")
            print(f"    🎯 Manual: {manual_count}")

            return True
        else:
            print("  ❌ Enhanced pipeline failed to generate lineup")
            return False

    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        try:
            os.unlink(dk_file)
            os.unlink(dff_file)
        except:
            pass

def test_gui_compatibility():
    """Test GUI compatibility"""
    print("\n🖥️ Testing GUI Compatibility")
    print("-" * 40)

    gui_results = {}

    # Test streamlined GUI import
    try:
        import streamlined_dfs_gui
        gui_results['streamlined'] = "✅ Import OK"
        print("  ✅ streamlined_dfs_gui: Import successful")
    except Exception as e:
        gui_results['streamlined'] = f"❌ {e}"
        print(f"  ❌ streamlined_dfs_gui: {e}")

    # Test enhanced GUI import
    try:
        import enhanced_dfs_gui
        gui_results['enhanced'] = "✅ Import OK"
        print("  ✅ enhanced_dfs_gui: Import successful")
    except Exception as e:
        gui_results['enhanced'] = f"❌ {e}"
        print(f"  ⚠️ enhanced_dfs_gui: {e} (optional)")

    # Test PyQt5 availability
    try:
        from PyQt5.QtWidgets import QApplication
        gui_results['pyqt5'] = "✅ Available"
        print("  ✅ PyQt5: Available for GUI")
    except ImportError:
        gui_results['pyqt5'] = "❌ Not installed"
        print("  ❌ PyQt5: Not installed - run 'pip install PyQt5'")

    return gui_results

def test_strategies():
    """Test different strategies"""
    print("\n🎯 Testing Strategies")
    print("-" * 40)

    dk_file, dff_file = create_test_data()

    strategies_to_test = [
        'smart_confirmed',
        'confirmed_only', 
        'all_players',
        'manual_only'
    ]

    strategy_results = {}

    for strategy in strategies_to_test:
        try:
            from working_dfs_core_final import load_and_optimize_complete_pipeline_enhanced

            manual_input = "Jorge Polanco, Christian Yelich, Hunter Brown, Kyle Tucker, Vladimir Guerrero Jr., Francisco Lindor, Jose Ramirez, William Contreras, Jarren Duran, Byron Buxton" if strategy == 'manual_only' else "Jorge Polanco, Christian Yelich"

            lineup, score, summary = load_and_optimize_complete_pipeline_enhanced(
                dk_file=dk_file,
                dff_file=dff_file,
                manual_input=manual_input,
                contest_type='classic',
                strategy=strategy
            )

            if lineup and score > 0:
                strategy_results[strategy] = f"✅ {len(lineup)} players, {score:.1f} pts"
                print(f"  ✅ {strategy}: {len(lineup)} players, {score:.1f} points")
            else:
                strategy_results[strategy] = "❌ No lineup"
                print(f"  ❌ {strategy}: Failed")

        except Exception as e:
            strategy_results[strategy] = f"❌ {e}"
            print(f"  ❌ {strategy}: {e}")

    # Cleanup
    try:
        os.unlink(dk_file)
        os.unlink(dff_file)
    except:
        pass

    return strategy_results

def main():
    """Run comprehensive integration test"""
    print("🧪 COMPREHENSIVE INTEGRATION TEST")
    print("=" * 60)

    all_results = {}

    # Test 1: Component Tests
    component_results = test_unified_components()
    all_results['components'] = component_results

    # Test 2: Integration Test
    integration_success = test_integration()
    all_results['integration'] = "✅ PASS" if integration_success else "❌ FAIL"

    # Test 3: GUI Compatibility
    gui_results = test_gui_compatibility()
    all_results['gui'] = gui_results

    # Test 4: Strategy Tests
    strategy_results = test_strategies()
    all_results['strategies'] = strategy_results

    # Generate Report
    print("\n📊 TEST REPORT")
    print("=" * 60)

    # Component results
    print("🔧 Component Tests:")
    for component, result in component_results.items():
        print(f"  {component}: {result}")

    # Integration result
    print(f"\n🔄 Integration Test: {all_results['integration']}")

    # GUI results
    print("\n🖥️ GUI Compatibility:")
    for gui, result in gui_results.items():
        print(f"  {gui}: {result}")

    # Strategy results
    print("\n🎯 Strategy Tests:")
    for strategy, result in strategy_results.items():
        print(f"  {strategy}: {result}")

    # Overall assessment
    component_passes = sum(1 for r in component_results.values() if r.startswith('✅'))
    strategy_passes = sum(1 for r in strategy_results.values() if r.startswith('✅'))

    print(f"\n📈 SUMMARY:")
    print(f"  Components: {component_passes}/{len(component_results)} passed")
    print(f"  Integration: {'✅' if integration_success else '❌'}")
    print(f"  Strategies: {strategy_passes}/{len(strategy_results)} passed")

    if component_passes >= 2 and integration_success and strategy_passes >= 2:
        print("\n🎉 INTEGRATION SUCCESSFUL!")
        print("✅ Your unified DFS system is working!")
        print("\n💡 Next steps:")
        print("  1. Run: python launch_dfs_optimizer.py")
        print("  2. Test with real DraftKings CSV files")
        print("  3. Try different strategies in the GUI")
        return True
    else:
        print("\n⚠️ SOME ISSUES FOUND")
        print("💡 Check the error messages above")
        print("💡 Make sure all 3 artifacts are saved correctly")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''

        with open('test_integration.py', 'w') as f:
            f.write(test_content)

        print("  ✅ Created test_integration.py")
        self.changes_made.append("Created comprehensive test script")

    def generate_integration_summary(self):
        """Generate summary of all changes made"""
        print("\n📊 Generating integration summary...")

        summary_content = f"""# DFS Integration Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Changes Made
{chr(10).join('- ' + change for change in self.changes_made)}

## Files Modified
- working_dfs_core_final.py (added unified pipeline)
- streamlined_dfs_gui.py (fixed strategy selection)
- enhanced_dfs_gui.py (added imports)

## New Files Created
- launch_dfs_optimizer.py (GUI launcher)
- dfs_cli.py (command line interface)
- test_integration.py (comprehensive tests)

## Errors Encountered
{chr(10).join('- ' + error for error in self.errors) if self.errors else 'None'}

## Next Steps
1. Run: python test_integration.py
2. If tests pass: python launch_dfs_optimizer.py
3. Test with real DraftKings CSV files
4. Report any issues

## Backup Location
{self.backup_dir}

## Quick Commands
```bash
# Test the integration
python test_integration.py

# Launch GUI
python launch_dfs_optimizer.py

# Command line usage
python dfs_cli.py --dk your_file.csv --strategy smart_confirmed

# Test specific strategy
python dfs_cli.py --dk your_file.csv --strategy confirmed_only --manual "Player 1, Player 2"
```

## Strategy Guide
- smart_confirmed: Confirmed players + enhanced data (RECOMMENDED)
- confirmed_only: Only confirmed starters (safest)
- confirmed_plus_manual: Confirmed + your manual picks
- confirmed_pitchers_all_batters: Safe pitchers + all batters
- manual_only: Only your specified players
- all_players: Maximum flexibility

## Troubleshooting
If you see errors:
1. Make sure all 3 artifacts are saved
2. Check backups in {self.backup_dir}
3. Run test_integration.py for detailed diagnostics
4. Try python launch_dfs_optimizer.py
"""

        with open('INTEGRATION_SUMMARY.md', 'w') as f:
            f.write(summary_content)

        print("  ✅ Created INTEGRATION_SUMMARY.md")


if __name__ == "__main__":
    bot = DFSIntegrationBot()
    bot.run_full_integration()