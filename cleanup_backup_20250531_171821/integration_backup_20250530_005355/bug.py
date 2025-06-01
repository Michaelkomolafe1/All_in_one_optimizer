#!/usr/bin/env python3
"""
Automatic Data Flow Patcher
Fixes the confirmed → enrich → optimize pipeline automatically
"""

import os
import shutil
import re
from datetime import datetime


def create_dataflow_patcher():
    """Create automatic patcher for data flow"""

    patcher_code = '''#!/usr/bin/env python3
"""
Auto Data Flow Patcher - Run this to fix your GUI automatically
"""

import os
import shutil
import re
from datetime import datetime

def patch_gui_dataflow():
    """Patch the GUI with correct data flow"""

    gui_file = 'enhanced_dfs_gui.py'

    # Check if file exists
    if not os.path.exists(gui_file):
        print("❌ enhanced_dfs_gui.py not found!")
        return False

    # Create backup
    backup_name = f"enhanced_dfs_gui_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy2(gui_file, backup_name)
    print(f"💾 Backed up GUI to: {backup_name}")

    # Read current content
    with open(gui_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add the fixed run method
    fixed_run_method = """
    def run(self):
        \"\"\"FIXED: Proper confirmed → enrich → optimize data flow\"\"\"
        try:
            self.output_signal.emit("🚀 Starting CONFIRMED → ENRICH → OPTIMIZE pipeline...")
            self.status_signal.emit("Loading...")
            self.progress_signal.emit(5)

            if not self.gui.dk_file or not os.path.exists(self.gui.dk_file):
                self.finished_signal.emit(False, "No DraftKings file selected", {})
                return

            # STEP 1: Load all players
            self.output_signal.emit("📁 STEP 1: Loading all DraftKings players...")
            all_players = self._load_data_robust()
            if not all_players:
                self.finished_signal.emit(False, "Failed to load data", {})
                return
            self.output_signal.emit(f"✅ Loaded {len(all_players)} total players")
            self.progress_signal.emit(20)

            # STEP 2: Filter to confirmed players  
            self.output_signal.emit("🔍 STEP 2: Filtering to confirmed starters...")
            confirmed_players = self._filter_to_confirmed_only(all_players)
            if len(confirmed_players) < 15:
                self.output_signal.emit(f"⚠️ Only {len(confirmed_players)} confirmed - using top projected players")
                confirmed_players = self._get_top_projected_players(all_players, 30)

            self.output_signal.emit(f"✅ Using {len(confirmed_players)} confirmed/top players")
            self.progress_signal.emit(40)

            # STEP 3: Enrich with Statcast (if available)
            try:
                from statcast_integration import StatcastIntegration
                self.output_signal.emit("⚾ STEP 3: Enriching with Statcast data...")
                statcast = StatcastIntegration()
                enriched_players = statcast.enrich_player_data(confirmed_players)
                self.output_signal.emit("✅ Statcast enrichment complete")
                confirmed_players = enriched_players
            except:
                self.output_signal.emit("⚠️ Statcast not available - skipping")

            self.progress_signal.emit(60)

            # STEP 4: Enrich with Vegas (if available)  
            try:
                from vegas_lines import VegasLines
                self.output_signal.emit("💰 STEP 4: Enriching with Vegas lines...")
                vegas = VegasLines()
                vegas_lines = vegas.get_vegas_lines()
                if vegas_lines:
                    confirmed_players = vegas.apply_to_players(confirmed_players)
                    self.output_signal.emit("✅ Vegas enrichment complete")
                else:
                    self.output_signal.emit("⚠️ No Vegas data available")
            except:
                self.output_signal.emit("⚠️ Vegas not available - skipping")

            self.progress_signal.emit(75)

            # STEP 5: Apply DFF if available
            if hasattr(self.gui, 'dff_file') and self.gui.dff_file:
                self.output_signal.emit("🎯 STEP 5: Applying DFF rankings...")
                confirmed_players = self._apply_dff_data(confirmed_players)

            # STEP 6: Optimize using confirmed enhanced players
            self.output_signal.emit("🧠 STEP 6: Optimizing confirmed enhanced players...")
            lineup, score = self._optimize_confirmed_players(confirmed_players)

            if lineup:
                result_text = self._format_results_robust(lineup, score)
                lineup_data = self._extract_lineup_data_robust(lineup)
                self.progress_signal.emit(100)
                self.output_signal.emit("✅ PIPELINE SUCCESS: Confirmed → Enhanced → Optimized!")
                self.finished_signal.emit(True, result_text, lineup_data)
            else:
                self.finished_signal.emit(False, "No valid lineup from confirmed players", {})

        except Exception as e:
            import traceback
            self.output_signal.emit(f"❌ Pipeline error: {str(e)}")
            self.output_signal.emit(f"Debug: {traceback.format_exc()}")
            self.finished_signal.emit(False, str(e), {})

    def _filter_to_confirmed_only(self, all_players):
        \"\"\"Filter to only confirmed starting players\"\"\"
        confirmed = []

        # Look for players with batting order set
        for player in all_players:
            if len(player) > 7 and player[7] is not None:
                try:
                    if 1 <= int(player[7]) <= 9:
                        confirmed.append(player)
                        continue
                except:
                    pass

            # For pitchers, take highest projected per team as probable starter
            if len(player) > 2 and player[2] == 'P':
                proj = player[5] if len(player) > 5 else 0
                if proj > 8.0:  # High projection suggests starter
                    confirmed.append(player)

        return confirmed

    def _get_top_projected_players(self, all_players, count):
        \"\"\"Get top projected players ensuring position coverage\"\"\"
        # Sort by projection/score
        sorted_players = sorted(all_players, 
                              key=lambda x: x[6] if len(x) > 6 else x[5] if len(x) > 5 else 0, 
                              reverse=True)

        selected = []
        position_counts = {}
        required = {'P': 3, 'C': 2, '1B': 2, '2B': 2, '3B': 2, 'SS': 2, 'OF': 5}

        for player in sorted_players:
            pos = player[2] if len(player) > 2 else "UTIL"
            current = position_counts.get(pos, 0)
            needed = required.get(pos, 1)

            if current < needed or len(selected) < count:
                selected.append(player)
                position_counts[pos] = current + 1

                if len(selected) >= count:
                    break

        return selected

    def _optimize_confirmed_players(self, players):
        \"\"\"Optimize using confirmed player pool\"\"\"
        try:
            # Try enhanced MILP first
            from dfs_optimizer_enhanced import optimize_lineup_milp
            budget = getattr(self.gui, 'budget_spin', type('', (), {'value': lambda: 50000})).value()
            return optimize_lineup_milp(players, budget=budget)
        except:
            # Fallback to greedy with smaller pool
            return self._greedy_optimization(players, 50000)
"""

    # Insert the fixed method into the OptimizationThread class
    # Find the class definition
    class_match = re.search(r'class OptimizationThread.*?:', content, re.DOTALL)
    if not class_match:
        print("❌ Could not find OptimizationThread class")
        return False

    # Find the run method and replace it
    run_pattern = r'(def run\(self\):.*?)(?=\n    def |\nclass |\Z)'

    if re.search(run_pattern, content, re.DOTALL):
        content = re.sub(run_pattern, fixed_run_method.strip(), content, flags=re.DOTALL)
        print("✅ Replaced existing run method")
    else:
        # Add the method to the class
        insert_pos = content.find('class OptimizationThread')
        if insert_pos != -1:
            # Find end of __init__ method to insert after it
            init_end = content.find('def ', content.find('def __init__', insert_pos) + 1)
            if init_end != -1:
                content = content[:init_end] + fixed_run_method + '\\n\\n    ' + content[init_end:]
                print("✅ Added fixed run method")

    # Write back the modified content
    with open(gui_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ GUI patched with correct data flow!")
    print("🎯 Now your optimizer will: Load → Filter Confirmed → Enrich → Optimize")
    return True

if __name__ == "__main__":
    print("🤖 Auto Data Flow Patcher")
    print("=" * 30)

    success = patch_gui_dataflow()
    if success:
        print("\\n✅ SUCCESS! Your GUI now uses the correct data flow.")
        print("\\n🚀 Test it:")
        print("python main_enhanced_performance.py")
    else:
        print("\\n❌ Patching failed. Try manual fix instead.")
'''

    # Write the patcher script
    with open('auto_fix_dataflow.py', 'w') as f:
        f.write(patcher_code)

    print("✅ Created auto_fix_dataflow.py")
    return True


if __name__ == "__main__":
    create_dataflow_patcher()
    print("\\n🤖 Automatic patcher created!")
    print("\\nRun it with:")
    print("python auto_fix_dataflow.py")