#!/usr/bin/env python3
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
    print("
🔄 Testing Integration")
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
    print("
🖥️ Testing GUI Compatibility")
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
    print("
🎯 Testing Strategies")
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
    print("
📊 TEST REPORT")
    print("=" * 60)

    # Component results
    print("🔧 Component Tests:")
    for component, result in component_results.items():
        print(f"  {component}: {result}")

    # Integration result
    print(f"
🔄 Integration Test: {all_results['integration']}")

    # GUI results
    print("
🖥️ GUI Compatibility:")
    for gui, result in gui_results.items():
        print(f"  {gui}: {result}")

    # Strategy results
    print("
🎯 Strategy Tests:")
    for strategy, result in strategy_results.items():
        print(f"  {strategy}: {result}")

    # Overall assessment
    component_passes = sum(1 for r in component_results.values() if r.startswith('✅'))
    strategy_passes = sum(1 for r in strategy_results.values() if r.startswith('✅'))

    print(f"
📈 SUMMARY:")
    print(f"  Components: {component_passes}/{len(component_results)} passed")
    print(f"  Integration: {'✅' if integration_success else '❌'}")
    print(f"  Strategies: {strategy_passes}/{len(strategy_results)} passed")

    if component_passes >= 2 and integration_success and strategy_passes >= 2:
        print("
🎉 INTEGRATION SUCCESSFUL!")
        print("✅ Your unified DFS system is working!")
        print("
💡 Next steps:")
        print("  1. Run: python launch_dfs_optimizer.py")
        print("  2. Test with real DraftKings CSV files")
        print("  3. Try different strategies in the GUI")
        return True
    else:
        print("
⚠️ SOME ISSUES FOUND")
        print("💡 Check the error messages above")
        print("💡 Make sure all 3 artifacts are saved correctly")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
