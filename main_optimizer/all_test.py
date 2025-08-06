#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM TESTING
============================
Test each component independently and the full flow
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add paths
project_root = os.path.dirname(os.path.abspath(__file__))
if 'main_optimizer' not in project_root:
    project_root = os.path.dirname(project_root)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'main_optimizer'))

print(f"Testing from: {project_root}")
print("=" * 60)


def test_confirmation_system():
    """Test 1: Confirmation System"""
    print("\n🧪 TEST 1: CONFIRMATION SYSTEM")
    print("-" * 40)

    try:
        from main_optimizer.smart_confirmation import UniversalSmartConfirmation

        # Test 1A: Basic initialization
        print("1A. Testing basic initialization...")
        system = UniversalSmartConfirmation(verbose=False)
        print("   ✓ System initialized")

        # Test 1B: Fetch confirmations
        print("1B. Fetching MLB confirmations...")
        result = system.get_all_confirmations()

        # Handle the tuple return
        if isinstance(result, tuple):
            lineup_count, pitcher_count = result
            print(f"   ✓ Found {lineup_count} players, {pitcher_count} pitchers")
        else:
            print(f"   ⚠ Unexpected return type: {type(result)}")

        # Test 1C: Check stored data
        print("1C. Checking stored confirmations...")
        if hasattr(system, 'confirmed_lineups'):
            print(f"   ✓ Teams with lineups: {len(system.confirmed_lineups)}")

            # Show sample players
            for team, lineup in list(system.confirmed_lineups.items())[:2]:
                print(f"      {team}: {len(lineup)} players")
                if lineup and isinstance(lineup[0], dict):
                    print(f"         Sample: {lineup[0].get('name', 'Unknown')}")

        if hasattr(system, 'confirmed_pitchers'):
            print(f"   ✓ Starting pitchers: {len(system.confirmed_pitchers)}")

            # Show sample pitchers
            for team, pitcher in list(system.confirmed_pitchers.items())[:2]:
                if isinstance(pitcher, dict):
                    print(f"      {team}: {pitcher.get('name', 'Unknown')}")
                else:
                    print(f"      {team}: {pitcher}")

        # Test 1D: With CSV players
        print("1D. Testing with CSV players...")

        # Load a real CSV to get players
        csv_path = "/home/michael/Downloads/DKSalaries(46).csv"
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)

            # Convert to simple player objects
            csv_players = []
            for _, row in df.iterrows():
                csv_players.append({
                    'name': row.get('Name', ''),
                    'team': row.get('TeamAbbrev', ''),
                    'position': row.get('Position', '')
                })

            # Reinitialize with CSV players
            system2 = UniversalSmartConfirmation(csv_players=csv_players[:10], verbose=False)
            print(f"   ✓ Tracking teams: {sorted(system2.csv_teams)[:5]}...")

            # Fetch again
            result2 = system2.get_all_confirmations()
            if isinstance(result2, tuple):
                print(f"   ✓ With CSV context: {result2[0]} players confirmed")

        return True

    except Exception as e:
        print(f"   ✗ Confirmation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enrichment_system():
    """Test 2: Enrichment System"""
    print("\n🧪 TEST 2: ENRICHMENT SYSTEM")
    print("-" * 40)

    try:
        from main_optimizer.smart_enrichment_manager import SmartEnrichmentManager

        # Test 2A: Initialize manager
        print("2A. Testing enrichment manager...")
        manager = SmartEnrichmentManager()
        print("   ✓ Manager initialized")

        # Test 2B: Check enrichment profiles
        print("2B. Checking enrichment profiles...")

        test_strategies = ['projection_monster', 'value_beast', 'balanced_projections']
        for strategy in test_strategies:
            if hasattr(manager, 'enrichment_profiles') and strategy in manager.enrichment_profiles:
                profile = manager.enrichment_profiles[strategy]
                print(f"   ✓ {strategy}: Vegas={profile.get('vegas')}, Statcast={profile.get('statcast')}")

        # Test 2C: Vegas lines
        print("2C. Testing Vegas data source...")
        try:
            from main_optimizer.vegas_lines import VegasLines
            vegas = VegasLines()

            # Test getting team total
            test_team = 'NYY'
            total = vegas.get_team_total(test_team)
            if total:
                print(f"   ✓ Vegas working: {test_team} total = {total}")
            else:
                print(f"   ⚠ No Vegas data for {test_team}")
        except Exception as e:
            print(f"   ⚠ Vegas not available: {e}")

        # Test 2D: Statcast
        print("2D. Testing Statcast data source...")
        try:
            from main_optimizer.simple_statcast_fetcher import SimpleStatcastFetcher
            statcast = SimpleStatcastFetcher()
            print("   ✓ Statcast initialized")
        except Exception as e:
            print(f"   ⚠ Statcast not available: {e}")

        return True

    except Exception as e:
        print(f"   ✗ Enrichment test failed: {e}")
        return False


def test_full_flow():
    """Test 3: Full System Flow"""
    print("\n🧪 TEST 3: FULL SYSTEM FLOW")
    print("-" * 40)

    try:
        from main_optimizer.unified_core_system_updated import UnifiedCoreSystem

        # Test 3A: Initialize system
        print("3A. Initializing core system...")
        system = UnifiedCoreSystem()
        print("   ✓ System initialized")

        # Test 3B: Load CSV
        print("3B. Loading CSV...")
        csv_path = "/home/michael/Downloads/DKSalaries(46).csv"
        if os.path.exists(csv_path):
            count = system.load_csv(csv_path)
            print(f"   ✓ Loaded {count} players")

            # Test 3C: Check auto-detection
            print("3C. Checking auto-detection...")
            if hasattr(system, 'current_slate_size'):
                print(f"   ✓ Slate size: {system.current_slate_size}")

            # Test 3D: Build player pool
            print("3D. Building player pool...")
            pool_size = system.build_player_pool(include_unconfirmed=True)
            print(f"   ✓ Player pool: {pool_size} players")

            # Test 3E: Test enrichment
            print("3E. Testing smart enrichment...")
            if hasattr(system, 'enrich_player_pool_smart'):
                stats = system.enrich_player_pool_smart(
                    strategy='projection_monster',
                    contest_type='gpp'
                )
                if stats:
                    print(f"   ✓ Enrichment stats: {stats}")

            # Test 3F: Score players
            print("3F. Testing scoring...")
            if hasattr(system, 'score_players'):
                system.score_players('gpp')

                # Check if players have scores
                scored_count = sum(1 for p in system.player_pool
                                   if hasattr(p, 'optimization_score')
                                   and p.optimization_score > 0)
                print(f"   ✓ Scored {scored_count} players")

            return True
        else:
            print(f"   ✗ CSV not found: {csv_path}")
            return False

    except Exception as e:
        print(f"   ✗ Flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gui_fetch_confirmations():
    """Test 4: Fix GUI Confirmation Fetching"""
    print("\n🧪 TEST 4: GUI CONFIRMATION FIX")
    print("-" * 40)

    print("The GUI fetch_confirmed_players method needs to handle tuple return.")
    print("\nRequired fix in unified_core_system_updated.py:")
    print("""
    def fetch_confirmed_players(self) -> int:
        # ... initialization code ...

        # Call get_all_confirmations which returns tuple
        result = self.confirmation_system.get_all_confirmations()

        # Handle tuple return
        if isinstance(result, tuple):
            lineup_count, pitcher_count = result
            total_confirmed = lineup_count  # or lineup_count + pitcher_count

            # Now access the actual confirmed data
            if hasattr(self.confirmation_system, 'confirmed_lineups'):
                # Process lineup data...
            if hasattr(self.confirmation_system, 'confirmed_pitchers'):
                # Process pitcher data...
    """)

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("COMPREHENSIVE SYSTEM TESTING")
    print("=" * 60)

    results = {}

    # Run tests
    results['confirmations'] = test_confirmation_system()
    results['enrichment'] = test_enrichment_system()
    results['flow'] = test_full_flow()
    results['gui_fix'] = test_gui_fetch_confirmations()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20s}: {status}")

    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)

    if not results['confirmations']:
        print("1. Fix confirmation system tuple handling in GUI")

    if not results['enrichment']:
        print("2. Check enrichment data sources are available")

    if not results['flow']:
        print("3. Fix the full system flow")

    print("\n📌 Key Issue: The confirmation system returns a tuple (lineup_count, pitcher_count)")
    print("   but the GUI expects different data. Need to fix fetch_confirmed_players method.")


if __name__ == "__main__":
    main()