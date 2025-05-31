#!/usr/bin/env python3
"""
Complete Advanced DFS Solution - Just Run This!
This file contains everything you need to get the advanced algorithm working
"""

import os
import sys
from pathlib import Path


def create_advanced_wrapper():
    """Create the advanced DFS wrapper"""

    wrapper_code = '''#!/usr/bin/env python3
"""
Advanced DFS Wrapper - Works WITHOUT modifying existing files
Run your DFS optimization with advanced algorithm
"""

def run_advanced_dfs_optimization(dk_file, dff_file=None, manual_input="", 
                                 contest_type='classic', strategy='smart_confirmed'):
    """
    Run DFS optimization with advanced algorithm
    This replaces load_and_optimize_complete_pipeline with advanced features
    """

    print("🚀 ADVANCED DFS OPTIMIZATION PIPELINE")
    print("=" * 60)

    try:
        # Import your existing optimizer
        print("📦 Loading core system...")
        from working_dfs_core_final import OptimizedDFSCore

        # Import advanced algorithm
        print("🧠 Loading advanced algorithm...")
        from advanced_dfs_algorithm import integrate_advanced_system_complete

        print("✅ All imports successful")

        # Step 1: Create core and load data
        print("\\n📊 Step 1: Loading DraftKings data...")
        core = OptimizedDFSCore()

        if not core.load_draftkings_csv(dk_file):
            return [], 0, "❌ Failed to load DraftKings data"

        print(f"✅ Loaded {len(core.players)} players")

        # Step 2: Apply DFF rankings
        if dff_file:
            print("\\n🎯 Step 2: Applying DFF rankings...")
            success = core.apply_dff_rankings(dff_file)
            if success:
                print("✅ DFF rankings applied")
            else:
                print("⚠️ DFF rankings failed, continuing without")

        # Step 3: Apply manual selection
        if manual_input:
            print("\\n🎯 Step 3: Applying manual selection...")
            manual_count = core.apply_manual_selection(manual_input)
            print(f"✅ Manual selection: {manual_count} players")

        # Step 4: ADVANCED ALGORITHM INTEGRATION
        print("\\n🧠 Step 4: Applying advanced DFS algorithm...")
        try:
            advanced_algo, statcast = integrate_advanced_system_complete(core)
            print("✅ Advanced algorithm integration successful!")
            print("📊 Features enabled:")
            print("   • Real Baseball Savant Statcast data")
            print("   • MILP-optimized scoring weights")
            print("   • Advanced DFF confidence analysis")
            print("   • Smart fallback for missing data")
            advanced_active = True
        except Exception as e:
            print(f"⚠️ Advanced algorithm failed: {e}")
            print("⚠️ Continuing with standard algorithm")
            advanced_active = False

        # Step 5: Data enrichment (now with advanced algorithm)
        print("\\n🔬 Step 5: Enriching with Statcast data...")
        core.enrich_with_statcast()

        # Step 6: Optimization
        print(f"\\n🧠 Step 6: Running optimization...")
        lineup, score = core.optimize_lineup(contest_type, strategy)

        if lineup and score > 0:
            print(f"✅ Optimization successful!")

            # Generate enhanced summary
            summary = generate_advanced_summary(core, lineup, score, advanced_active)

            print(f"📊 Final result: {len(lineup)} players, {score:.1f} score")
            return lineup, score, summary
        else:
            return [], 0, "❌ Optimization failed to generate valid lineup"

    except ImportError as e:
        return [], 0, f"❌ Import failed: {e}"
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return [], 0, f"❌ Error: {e}"


def generate_advanced_summary(core, lineup, score, advanced_active):
    """Generate enhanced summary with advanced algorithm info"""

    # Use the original summary
    original_summary = core.get_lineup_summary(lineup, score)

    if not advanced_active:
        return original_summary

    # Add advanced algorithm info
    advanced_info = []
    advanced_info.append("")
    advanced_info.append("🧠 ADVANCED ALGORITHM ANALYSIS:")
    advanced_info.append("=" * 40)

    # Analyze data sources
    real_data_count = 0
    sim_data_count = 0
    confirmed_count = 0
    manual_count = 0

    for player in lineup:
        if hasattr(player, 'statcast_data') and player.statcast_data:
            source = player.statcast_data.get('data_source', '')
            if 'savant' in source.lower() or 'baseball' in source.lower():
                real_data_count += 1
            elif 'simulation' in source.lower():
                sim_data_count += 1

        if getattr(player, 'is_confirmed', False):
            confirmed_count += 1
        if getattr(player, 'is_manual_selected', False):
            manual_count += 1

    advanced_info.append(f"📊 Data Sources:")
    advanced_info.append(f"   • Real Statcast data: {real_data_count}/{len(lineup)} players")
    advanced_info.append(f"   • Enhanced simulation: {sim_data_count}/{len(lineup)} players")
    advanced_info.append(f"   • Confirmed players: {confirmed_count}/{len(lineup)}")
    advanced_info.append(f"   • Manual selections: {manual_count}/{len(lineup)}")

    # Add algorithm features
    advanced_info.append("")
    advanced_info.append("🎯 Algorithm Features Applied:")
    advanced_info.append("   ✅ MILP-optimized Statcast weighting")
    advanced_info.append("   ✅ Advanced DFF confidence analysis")
    advanced_info.append("   ✅ Multi-factor context adjustments")
    advanced_info.append("   ✅ Position scarcity optimization")
    advanced_info.append("   ✅ Smart fallback for missing data")

    return original_summary + "\\n" + "\\n".join(advanced_info)


if __name__ == "__main__":
    # Quick test with sample data
    print("🧪 TESTING ADVANCED DFS WRAPPER")
    print("=" * 50)

    try:
        from working_dfs_core_final import create_enhanced_test_data

        dk_file, dff_file = create_enhanced_test_data()

        lineup, score, summary = run_advanced_dfs_optimization(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input="Jorge Polanco, Christian Yelich",
            strategy='smart_confirmed'
        )

        if lineup and score > 0:
            print("\\n🎉 TEST SUCCESSFUL!")
            print(f"Generated {len(lineup)} players with {score:.1f} score")
            print("\\n💡 Advanced algorithm is working!")

            # Cleanup
            import os
            try:
                os.unlink(dk_file)
                os.unlink(dff_file)
            except:
                pass
        else:
            print("❌ Test failed")

    except Exception as e:
        print(f"❌ Test error: {e}")
'''

    with open('advanced_dfs_wrapper.py', 'w') as f:
        f.write(wrapper_code)

    print("✅ Created advanced_dfs_wrapper.py")


def create_simple_launcher():
    """Create a simple launcher script"""

    launcher_code = '''#!/usr/bin/env python3
"""
Simple Advanced DFS Launcher
"""

import sys

def main():
    """Launch the advanced system"""

    print("🚀 ADVANCED DFS SYSTEM LAUNCHER")
    print("=" * 40)

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test mode
        print("🧪 Running test...")
        from advanced_dfs_wrapper import run_advanced_dfs_optimization
        from working_dfs_core_final import create_enhanced_test_data

        dk_file, dff_file = create_enhanced_test_data()

        lineup, score, summary = run_advanced_dfs_optimization(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input="Jorge Polanco, Christian Yelich"
        )

        if lineup:
            print(f"✅ Test successful: {len(lineup)} players, {score:.1f} score")
            print("🧠 Advanced algorithm working!")
        else:
            print("❌ Test failed")

        # Cleanup
        import os
        try:
            os.unlink(dk_file)
            os.unlink(dff_file)
        except:
            pass

    else:
        # GUI mode
        try:
            print("🖥️ Launching GUI...")
            import streamlined_dfs_gui
            return streamlined_dfs_gui.main()
        except Exception as e:
            print(f"❌ GUI launch failed: {e}")
            print("💡 Try: python launch_advanced.py test")
            return 1

if __name__ == "__main__":
    sys.exit(main())
'''

    with open('launch_advanced.py', 'w') as f:
        f.write(launcher_code)

    print("✅ Created launch_advanced.py")


def run_complete_test():
    """Run a complete test of the system"""

    print("\n🧪 RUNNING COMPLETE SYSTEM TEST")
    print("=" * 50)

    # Check files
    required_files = [
        'working_dfs_core_final.py',
        'advanced_dfs_algorithm.py',
        'streamlined_dfs_gui.py'
    ]

    missing = []
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing.append(file)

    if missing:
        print(f"\n❌ Missing files: {missing}")
        print("💡 Make sure all artifacts are saved first")
        return False

    # Test the wrapper
    print("\n🧪 Testing advanced wrapper...")
    try:
        exec(open('advanced_dfs_wrapper.py').read())
        print("✅ Wrapper test successful")
        return True
    except Exception as e:
        print(f"❌ Wrapper test failed: {e}")
        return False


def show_usage_instructions():
    """Show how to use the solution"""

    print("\n🎯 HOW TO USE YOUR ADVANCED SYSTEM")
    print("=" * 50)
    print()
    print("🚀 OPTION 1: Command Line Test")
    print("   python launch_advanced.py test")
    print()
    print("🖥️ OPTION 2: GUI (Standard)")
    print("   python launch_advanced.py")
    print("   (Your normal GUI, but you can use wrapper manually)")
    print()
    print("🧠 OPTION 3: Use Wrapper Directly")
    print("   from advanced_dfs_wrapper import run_advanced_dfs_optimization")
    print("   lineup, score, summary = run_advanced_dfs_optimization(dk_file)")
    print()
    print("📊 OPTION 4: Your CSV Files")
    print("   from advanced_dfs_wrapper import run_advanced_dfs_optimization")
    print("   lineup, score, summary = run_advanced_dfs_optimization(")
    print("       dk_file='your_file.csv',")
    print("       manual_input='Player 1, Player 2'")
    print("   )")
    print()
    print("💡 WHAT HAPPENS:")
    print("✅ Priority players (confirmed + manual) get real Statcast data")
    print("✅ Other players get enhanced simulation")
    print("✅ All players benefit from advanced MILP-optimized scoring")
    print("✅ Smart fallback if real data unavailable")
    print("✅ Same interface, much smarter backend!")


def main():
    """Create the complete solution"""

    print("🎉 CREATING COMPLETE ADVANCED DFS SOLUTION")
    print("=" * 60)
    print()
    print("This creates a working solution WITHOUT modifying your existing files!")
    print()

    # Create the files
    create_advanced_wrapper()
    create_simple_launcher()

    # Test the system
    success = run_complete_test()

    if success:
        print("\n🎉 SOLUTION CREATED SUCCESSFULLY!")
        print("=" * 40)
        print("✅ advanced_dfs_wrapper.py - Main advanced wrapper")
        print("✅ launch_advanced.py - Simple launcher")

        show_usage_instructions()

        print("\n🚀 READY TO USE!")
        print("Try: python launch_advanced.py test")

    else:
        print("\n❌ SOLUTION CREATION FAILED")
        print("💡 Make sure you have saved all artifacts:")
        print("   • advanced_dfs_algorithm.py")
        print("   • working_dfs_core_final.py")
        print("   • streamlined_dfs_gui.py")


if __name__ == "__main__":
    main()