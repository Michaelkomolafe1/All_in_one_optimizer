#!/usr/bin/env python3
"""
GUI DEBUG INTERCEPTOR SCRIPT
============================
This script hooks into your GUI and shows exactly what's happening
with the data enrichment workflow in real-time.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path


class GUIDebugInterceptor:
    """Intercepts and debugs GUI workflow calls"""

    def __init__(self):
        self.debug_log = []
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = f"gui_debug_{self.session_id}.log"

        print("🔍 GUI DEBUG INTERCEPTOR INITIALIZED")
        print(f"📝 Logging to: {self.log_file}")
        print("=" * 60)

    def log_debug(self, message, level="INFO"):
        """Log debug message with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        log_entry = f"[{timestamp}] {level}: {message}"

        print(log_entry)
        self.debug_log.append(log_entry)

        # Write to file immediately
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')

    def intercept_optimization_thread(self, original_run_method):
        """Intercept the optimization thread run method"""

        def debug_run(self_thread):
            interceptor.log_debug("🚀 OPTIMIZATION THREAD STARTED", "THREAD")
            interceptor.log_debug(f"   DK File: {self_thread.dk_file}", "THREAD")
            interceptor.log_debug(f"   DFF File: {self_thread.dff_file}", "THREAD")
            interceptor.log_debug(
                f"   DFF Exists: {os.path.exists(self_thread.dff_file) if self_thread.dff_file else False}", "THREAD")
            interceptor.log_debug(f"   Manual Input: '{self_thread.manual_input}'", "THREAD")
            interceptor.log_debug(f"   Contest Type: {self_thread.contest_type}", "THREAD")
            interceptor.log_debug(f"   Mode: {self_thread.optimization_mode}", "THREAD")

            # Check if DFF file is actually readable
            if self_thread.dff_file:
                try:
                    import pandas as pd
                    df = pd.read_csv(self_thread.dff_file)
                    interceptor.log_debug(f"   DFF File Readable: ✅ {len(df)} rows, {len(df.columns)} columns",
                                          "THREAD")
                    interceptor.log_debug(f"   DFF Columns: {list(df.columns)}", "THREAD")
                except Exception as e:
                    interceptor.log_debug(f"   DFF File Error: ❌ {e}", "THREAD")

            # Call original method
            try:
                result = original_run_method(self_thread)
                interceptor.log_debug("✅ OPTIMIZATION THREAD COMPLETED", "THREAD")
                return result
            except Exception as e:
                interceptor.log_debug(f"❌ OPTIMIZATION THREAD FAILED: {e}", "THREAD")
                raise

        return debug_run

    def intercept_pipeline_function(self, original_pipeline):
        """Intercept the main pipeline function"""

        def debug_pipeline(dk_file, dff_file=None, manual_input="", contest_type='classic', strategy='bulletproof'):
            interceptor.log_debug("🔄 PIPELINE FUNCTION CALLED", "PIPELINE")
            interceptor.log_debug(f"   dk_file parameter: {dk_file}", "PIPELINE")
            interceptor.log_debug(f"   dff_file parameter: {dff_file}", "PIPELINE")
            interceptor.log_debug(f"   manual_input parameter: '{manual_input}'", "PIPELINE")
            interceptor.log_debug(f"   contest_type parameter: {contest_type}", "PIPELINE")
            interceptor.log_debug(f"   strategy parameter: {strategy}", "PIPELINE")

            # File existence checks
            interceptor.log_debug(f"   DK file exists: {os.path.exists(dk_file) if dk_file else False}", "PIPELINE")
            interceptor.log_debug(f"   DFF file exists: {os.path.exists(dff_file) if dff_file else False}", "PIPELINE")

            # Call original pipeline
            try:
                lineup, score, summary = original_pipeline(dk_file, dff_file, manual_input, contest_type, strategy)
                interceptor.log_debug(f"✅ PIPELINE COMPLETED: {len(lineup)} players, score {score}", "PIPELINE")
                return lineup, score, summary
            except Exception as e:
                interceptor.log_debug(f"❌ PIPELINE FAILED: {e}", "PIPELINE")
                raise

        return debug_pipeline

    def intercept_core_methods(self, core_instance):
        """Intercept core DFS methods for debugging"""

        # Intercept apply_dff_rankings
        original_dff = core_instance.apply_dff_rankings

        def debug_dff(dff_file_path):
            interceptor.log_debug("📈 DFF RANKINGS METHOD CALLED", "CORE")
            interceptor.log_debug(f"   DFF file path: {dff_file_path}", "CORE")
            interceptor.log_debug(f"   DFF file exists: {os.path.exists(dff_file_path) if dff_file_path else False}",
                                  "CORE")

            if dff_file_path and os.path.exists(dff_file_path):
                interceptor.log_debug(f"   DFF file size: {os.path.getsize(dff_file_path)} bytes", "CORE")

            result = original_dff(dff_file_path)
            interceptor.log_debug(f"   DFF application result: {result}", "CORE")

            # Check how many players got DFF data
            dff_players = [p for p in core_instance.players if hasattr(p, 'dff_data') and p.dff_data]
            interceptor.log_debug(f"   Players with DFF data: {len(dff_players)}", "CORE")

            return result

        core_instance.apply_dff_rankings = debug_dff

        # Intercept statcast enrichment
        original_statcast = core_instance.enrich_with_statcast_priority

        def debug_statcast():
            interceptor.log_debug("🔬 STATCAST ENRICHMENT CALLED", "CORE")
            result = original_statcast()

            statcast_players = [p for p in core_instance.players if hasattr(p, 'statcast_data') and p.statcast_data]
            interceptor.log_debug(f"   Players with Statcast data: {len(statcast_players)}", "CORE")

            return result

        core_instance.enrich_with_statcast_priority = debug_statcast

        # Intercept vegas enrichment
        original_vegas = core_instance.enrich_with_vegas_lines

        def debug_vegas():
            interceptor.log_debug("💰 VEGAS LINES ENRICHMENT CALLED", "CORE")
            result = original_vegas()

            vegas_players = [p for p in core_instance.players if hasattr(p, 'vegas_data') and p.vegas_data]
            interceptor.log_debug(f"   Players with Vegas data: {len(vegas_players)}", "CORE")

            return result

        core_instance.enrich_with_vegas_lines = debug_vegas

        # Intercept manual selection
        original_manual = core_instance.apply_manual_selection

        def debug_manual(manual_input):
            interceptor.log_debug("🎯 MANUAL SELECTION CALLED", "CORE")
            interceptor.log_debug(f"   Manual input: '{manual_input}'", "CORE")

            result = original_manual(manual_input)
            interceptor.log_debug(f"   Manual matches: {result}", "CORE")

            manual_players = [p for p in core_instance.players if p.is_manual_selected]
            interceptor.log_debug(f"   Manual players found: {len(manual_players)}", "CORE")
            for player in manual_players:
                interceptor.log_debug(f"      ✅ {player.name}", "CORE")

            return result

        core_instance.apply_manual_selection = debug_manual

    def generate_final_report(self):
        """Generate final debug report"""
        report = f"""
GUI DEBUG REPORT - Session {self.session_id}
{'=' * 60}

Total log entries: {len(self.debug_log)}
Log file: {self.log_file}

SUMMARY:
- Check if DFF files are being passed from GUI
- Check if manual selections are working
- Check if enrichment methods are being called
- Look for any error messages

{'=' * 60}
Full log saved to: {self.log_file}
"""
        print(report)

        with open(self.log_file, 'a') as f:
            f.write(report)


# Global interceptor instance
interceptor = GUIDebugInterceptor()


def install_gui_debug_hooks():
    """Install debug hooks into the GUI system"""
    interceptor.log_debug("🔧 INSTALLING GUI DEBUG HOOKS", "SETUP")

    try:
        # Hook into the GUI optimization thread
        from enhanced_dfs_gui import OptimizationThread

        # Store original run method
        original_run = OptimizationThread.run

        # Replace with debug version
        OptimizationThread.run = interceptor.intercept_optimization_thread(original_run)
        interceptor.log_debug("✅ Optimization thread hooked", "SETUP")

    except ImportError as e:
        interceptor.log_debug(f"⚠️ Could not hook OptimizationThread: {e}", "SETUP")

    try:
        # Hook into the core pipeline
        from bulletproof_dfs_core import load_and_optimize_complete_pipeline

        # We'll need to replace this in the module
        import bulletproof_dfs_core
        original_pipeline = bulletproof_dfs_core.load_and_optimize_complete_pipeline
        bulletproof_dfs_core.load_and_optimize_complete_pipeline = interceptor.intercept_pipeline_function(
            original_pipeline)
        interceptor.log_debug("✅ Pipeline function hooked", "SETUP")

    except ImportError as e:
        interceptor.log_debug(f"⚠️ Could not hook pipeline: {e}", "SETUP")

    # Hook into core class creation
    try:
        from bulletproof_dfs_core import BulletproofDFSCore

        original_init = BulletproofDFSCore.__init__

        def debug_init(self):
            result = original_init(self)
            interceptor.log_debug("🚀 BulletproofDFSCore instance created", "CORE")
            interceptor.intercept_core_methods(self)
            return result

        BulletproofDFSCore.__init__ = debug_init
        interceptor.log_debug("✅ Core class hooked", "SETUP")

    except ImportError as e:
        interceptor.log_debug(f"⚠️ Could not hook core class: {e}", "SETUP")


def run_gui_with_debug():
    """Run the GUI with debug hooks installed"""
    interceptor.log_debug("🚀 STARTING GUI WITH DEBUG HOOKS", "MAIN")

    # Install hooks
    install_gui_debug_hooks()

    try:
        # Import and run the GUI
        from enhanced_dfs_gui import main as gui_main

        interceptor.log_debug("🖥️ LAUNCHING GUI", "MAIN")

        # Run the GUI
        result = gui_main()

        interceptor.log_debug("✅ GUI CLOSED", "MAIN")
        return result

    except Exception as e:
        interceptor.log_debug(f"❌ GUI ERROR: {e}", "MAIN")
        raise
    finally:
        # Generate final report
        interceptor.generate_final_report()


def run_direct_test():
    """Run a direct test without GUI to compare"""
    interceptor.log_debug("🧪 RUNNING DIRECT TEST FOR COMPARISON", "TEST")

    try:
        from bulletproof_dfs_core import load_and_optimize_complete_pipeline, create_enhanced_test_data

        # Create test data
        dk_file, _ = create_enhanced_test_data()

        # Create test DFF file
        import tempfile
        import csv

        dff_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        dff_data = [
            ['Name', 'Team', 'Position', 'Salary', 'Projection', 'Ownership'],
            ['Francisco Lindor', 'NYM', 'SS', 4300, 8.23, 12.1],
            ['Juan Soto', 'NYY', 'OF', 5000, 9.87, 18.3],
            ['Hunter Brown', 'HOU', 'SP', 9800, 24.56, 8.5]
        ]

        writer = csv.writer(dff_file)
        writer.writerows(dff_data)
        dff_file.close()

        interceptor.log_debug(f"📁 Test files created: DK={dk_file}, DFF={dff_file.name}", "TEST")

        # Run pipeline directly
        lineup, score, summary = load_and_optimize_complete_pipeline(
            dk_file=dk_file,
            dff_file=dff_file.name,
            manual_input="Francisco Lindor, Juan Soto",
            strategy='manual_only'
        )

        interceptor.log_debug(f"🎯 Direct test result: {len(lineup)} players, score {score}", "TEST")

        if lineup:
            for player in lineup:
                has_dff = hasattr(player, 'dff_data') and player.dff_data
                has_statcast = hasattr(player, 'statcast_data') and player.statcast_data
                interceptor.log_debug(f"   {player.name}: DFF={has_dff}, Statcast={has_statcast}", "TEST")

        # Cleanup
        os.unlink(dk_file)
        os.unlink(dff_file.name)

        return True

    except Exception as e:
        interceptor.log_debug(f"❌ Direct test failed: {e}", "TEST")
        return False


if __name__ == "__main__":
    print("🔍 GUI DEBUG INTERCEPTOR")
    print("=" * 60)
    print("Choose debug mode:")
    print("1. Run GUI with debug hooks (recommended)")
    print("2. Run direct test only")
    print("3. Run both")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == "1":
        run_gui_with_debug()
    elif choice == "2":
        run_direct_test()
    elif choice == "3":
        run_direct_test()
        print("\n" + "=" * 60)
        print("Now running GUI with debug hooks...")
        run_gui_with_debug()
    else:
        print("Invalid choice. Running GUI with debug hooks...")
        run_gui_with_debug()

    print(f"\n🎉 Debug session complete! Check {interceptor.log_file} for full details.")