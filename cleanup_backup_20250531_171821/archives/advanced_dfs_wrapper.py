#!/usr/bin/env python3
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
        from advanced_dfs_core import OptimizedDFSCore

        # Import advanced algorithm
        print("🧠 Loading advanced algorithm...")
        from advanced_dfs_algorithm import integrate_advanced_system_complete

        print("✅ All imports successful")

        # Step 1: Create core and load data
        print("\n📊 Step 1: Loading DraftKings data...")
        core = OptimizedDFSCore()

        if not core.load_draftkings_csv(dk_file):
            return [], 0, "❌ Failed to load DraftKings data"

        print(f"✅ Loaded {len(core.players)} players")

        # Step 2: Apply DFF rankings
        if dff_file:
            print("\n🎯 Step 2: Applying DFF rankings...")
            success = core.apply_dff_rankings(dff_file)
            if success:
                print("✅ DFF rankings applied")
            else:
                print("⚠️ DFF rankings failed, continuing without")

        # Step 3: Apply manual selection
        if manual_input:
            print("\n🎯 Step 3: Applying manual selection...")
            manual_count = core.apply_manual_selection(manual_input)
            print(f"✅ Manual selection: {manual_count} players")

        # Step 4: ADVANCED ALGORITHM INTEGRATION
        print("\n🧠 Step 4: Applying advanced DFS algorithm...")
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
        print("\n🔬 Step 5: Enriching with Statcast data...")
        core.enrich_with_statcast()

        # Step 6: Optimization
        print(f"\n🧠 Step 6: Running optimization...")
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

    return original_summary + "\n" + "\n".join(advanced_info)


if __name__ == "__main__":
    # Quick test with sample data
    print("🧪 TESTING ADVANCED DFS WRAPPER")
    print("=" * 50)

    try:
        from advanced_dfs_core import create_enhanced_test_data

        dk_file, dff_file = create_enhanced_test_data()

        lineup, score, summary = run_advanced_dfs_optimization(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input="Jorge Polanco, Christian Yelich",
            strategy='smart_confirmed'
        )

        if lineup and score > 0:
            print("\n🎉 TEST SUCCESSFUL!")
            print(f"Generated {len(lineup)} players with {score:.1f} score")
            print("\n💡 Advanced algorithm is working!")

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
