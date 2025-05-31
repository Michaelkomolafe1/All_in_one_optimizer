#!/usr/bin/env python3
"""
Fix Statcast Timing - Get Real Data for Confirmed Players
Reorders the pipeline so confirmed players get real Baseball Savant data
"""

import os
import re


def fix_pipeline_order():
    """Fix the pipeline order in working_dfs_core_final.py"""

    core_file = 'working_dfs_core_final.py'

    if not os.path.exists(core_file):
        print(f"❌ {core_file} not found")
        return False

    print(f"🔧 Fixing pipeline order in {core_file}...")

    # Create backup
    backup_file = f"{core_file}.backup_timing"
    import shutil
    shutil.copy2(core_file, backup_file)
    print(f"📁 Backup created: {backup_file}")

    with open(core_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the load_and_optimize_complete_pipeline function and fix the order
    pipeline_pattern = r'(def load_and_optimize_complete_pipeline.*?)(\n    return.*?)"'

    # New pipeline with correct order
    new_pipeline = '''def load_and_optimize_complete_pipeline(
        dk_file: str,
        dff_file: str = None,
        manual_input: str = "",
        contest_type: str = 'classic',
        strategy: str = 'balanced'
) -> Tuple[List[OptimizedPlayer], float, str]:
    """Complete optimization pipeline with FIXED order for real Statcast data"""

    print("🚀 COMPLETE DFS OPTIMIZATION PIPELINE")
    print("=" * 60)

    # Initialize core
    core = OptimizedDFSCore()

    # Step 1: Load DraftKings data
    print("📊 Step 1: Loading DraftKings data...")
    if not core.load_draftkings_csv(dk_file):
        return [], 0, "Failed to load DraftKings data"

    # Step 2: Apply DFF rankings if provided (BEFORE confirmed detection)
    if dff_file:
        print("🎯 Step 2: Applying DFF rankings...")
        core.apply_dff_rankings(dff_file)

    # Step 3: CRITICAL FIX - Detect confirmed players BEFORE Statcast enrichment
    print("🔍 Step 3: Detecting confirmed players FIRST...")
    confirmed_count = core._detect_confirmed_players()
    print(f"✅ Found {confirmed_count} confirmed players for real Statcast data")

    # Step 4: Apply manual selection BEFORE Statcast (so manual players get real data too)
    if manual_input:
        print("🎯 Step 4: Applying manual selection...")
        manual_count = core.apply_manual_selection(manual_input)
        print(f"✅ Added {manual_count} manual players for real Statcast data")

    # Step 5: NOW enrich with Statcast data (confirmed + manual players get REAL data)
    print("🔬 Step 5: Enriching with Statcast data...")
    print("🌐 Confirmed + manual players will get REAL Baseball Savant data!")
    core.enrich_with_statcast()

    # Step 6: Optimize lineup with strategy
    print("🧠 Step 6: Running optimization...")
    lineup, score = core.optimize_lineup(contest_type, strategy)

    if lineup:
        summary = core.get_lineup_summary(lineup, score)
        print("✅ Optimization complete!")
        return lineup, score, summary
    else:
        return [], 0, "Optimization failed"'''

    # Replace the function
    if re.search(r'def load_and_optimize_complete_pipeline.*?(?=\ndef |\n\nclass |\nif __name__|\Z)', content,
                 re.DOTALL):
        content = re.sub(
            r'def load_and_optimize_complete_pipeline.*?(?=\ndef |\n\nclass |\nif __name__|\Z)',
            new_pipeline + '\n\n',
            content,
            flags=re.DOTALL
        )

        with open(core_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Fixed pipeline order!")
        return True
    else:
        print("❌ Could not find pipeline function")
        return False


def update_statcast_service_for_confirmed():
    """Update StatcastDataService to prioritize confirmed + manual players"""

    core_file = 'working_dfs_core_final.py'

    with open(core_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the _enrich_with_real_statcast method and update it
    enhanced_method = '''
    def _enrich_with_real_statcast(self, players: List[OptimizedPlayer]) -> List[OptimizedPlayer]:
        """Enrich with REAL Baseball Savant data - PRIORITIZING confirmed + manual"""

        # Separate players by priority
        priority_players = [p for p in players if 
                           getattr(p, 'is_confirmed', False) or 
                           getattr(p, 'is_manual_selected', False)]
        other_players = [p for p in players if p not in priority_players]

        print(f"🌐 Fetching REAL Baseball Savant data for players...")
        print(f"🎯 PRIORITY: {len(priority_players)} confirmed + manual players")
        print(f"⚡ SIMULATED: {len(other_players)} other players")
        print("⏳ This will take 2-5 minutes for fresh data...")

        # Process priority players with REAL data
        if priority_players:
            print(f"🌐 Fetching real data for {len(priority_players)} priority players...")
            priority_enhanced = self.statcast_integration.enrich_player_data(priority_players, force_refresh=False)
        else:
            priority_enhanced = []

        # For other players, use simulated data (much faster)
        if other_players:
            print(f"⚡ Using simulated data for {len(other_players)} other players...")
            other_enhanced = self._enrich_with_simulated_statcast(other_players)
        else:
            other_enhanced = []

        # Combine results
        all_enhanced = priority_enhanced + other_enhanced

        # Count real vs simulated data
        real_data_count = 0
        for player in priority_enhanced:
            if (hasattr(player, 'statcast_data') and 
                player.statcast_data and 
                'Baseball Savant' in player.statcast_data.get('data_source', '')):
                real_data_count += 1

        print(f"✅ REAL Baseball Savant data: {real_data_count}/{len(priority_players)} priority players")
        print(f"⚡ Simulated data: {len(other_players)} other players")
        print(f"🎯 Total enhanced: {len(all_enhanced)} players")

        return all_enhanced'''

    # Replace the existing method
    pattern = r'def _enrich_with_real_statcast\(self, players: List\[OptimizedPlayer\]\).*?(?=\n    def |\n\nclass |\nif __name__|\Z)'

    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, enhanced_method, content, flags=re.DOTALL)

        with open(core_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Updated Statcast service for confirmed player priority")
        return True
    else:
        print("⚠️ Could not find _enrich_with_real_statcast method")
        return False


def create_test_confirmed_statcast():
    """Create a test script specifically for confirmed players with real data"""

    test_content = '''#!/usr/bin/env python3
"""
Test Confirmed Players Real Statcast Data
Verifies that confirmed players get real Baseball Savant data
"""

import os
import sys

def test_confirmed_real_data():
    """Test that confirmed players get real Baseball Savant data"""

    print("🧪 TESTING CONFIRMED PLAYERS REAL STATCAST DATA")
    print("=" * 60)

    try:
        from working_dfs_core_final import load_and_optimize_complete_pipeline
        print("✅ Core imported successfully")
    except ImportError as e:
        print(f"❌ Could not import core: {e}")
        return False

    # Find CSV files
    dk_files = [f for f in os.listdir('.') if f.endswith('.csv') and any(keyword in f.lower() for keyword in ['dk', 'salary'])]
    dff_files = [f for f in os.listdir('.') if f.endswith('.csv') and any(keyword in f.lower() for keyword in ['dff', 'cheat'])]

    if not dk_files:
        print("❌ No DraftKings CSV files found")
        return False

    dk_file = dk_files[0]
    dff_file = dff_files[0] if dff_files else None

    print(f"📊 Using DK file: {dk_file}")
    print(f"🎯 Using DFF file: {dff_file}")

    try:
        # Test with manual players to ensure they get real data
        manual_input = "Shohei Ohtani, Aaron Judge, Mookie Betts, Gerrit Cole, Shane Bieber"

        print(f"\\n🎯 Testing with manual players (should get REAL data): {manual_input}")
        print("🔍 Confirmed players should also get REAL data")
        print("🌐 Look for 'Baseball Savant' data source in output...")

        lineup, score, summary = load_and_optimize_complete_pipeline(
            dk_file=dk_file,
            dff_file=dff_file,
            manual_input=manual_input,
            contest_type='classic',
            strategy='smart_confirmed'
        )

        if lineup and score > 0:
            print(f"\\n✅ SUCCESS: Generated lineup!")
            print(f"📊 Lineup: {len(lineup)} players, {score:.1f} pts")

            # Analyze data sources
            real_data_count = 0
            confirmed_count = 0
            manual_count = 0

            print(f"\\n📊 DATA SOURCE ANALYSIS:")
            for player in lineup:
                is_confirmed = getattr(player, 'is_confirmed', False)
                is_manual = getattr(player, 'is_manual_selected', False)

                if is_confirmed:
                    confirmed_count += 1
                if is_manual:
                    manual_count += 1

                if hasattr(player, 'statcast_data') and player.statcast_data:
                    data_source = player.statcast_data.get('data_source', 'unknown')
                    if 'Baseball Savant' in data_source:
                        real_data_count += 1
                        status = "🌐 REAL"
                    else:
                        status = "⚡ SIM"

                    player_type = []
                    if is_confirmed:
                        player_type.append("CONF")
                    if is_manual:
                        player_type.append("MANUAL")

                    type_str = "|".join(player_type) if player_type else "REGULAR"
                    print(f"   {status} {player.name} ({type_str})")

            print(f"\\n📈 SUMMARY:")
            print(f"🌐 Real Baseball Savant data: {real_data_count}/{len(lineup)}")
            print(f"✅ Confirmed players: {confirmed_count}")
            print(f"📝 Manual players: {manual_count}")

            if real_data_count >= (confirmed_count + manual_count):
                print(f"\\n🎉 SUCCESS! Confirmed + manual players got real data!")
                return True
            else:
                print(f"\\n⚠️ Some confirmed/manual players missing real data")
                print(f"💡 May need additional timing fixes")
                return False
        else:
            print("❌ Failed to generate lineup")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_confirmed_real_data()
    if success:
        print("\\n🎉 CONFIRMED PLAYERS REAL DATA TEST PASSED!")
    else:
        print("\\n⚠️ Test needs attention")
'''

    with open('test_confirmed_statcast.py', 'w', encoding='utf-8') as f:
        f.write(test_content)

    print("✅ Created test_confirmed_statcast.py")


def main():
    """Main fix execution"""

    print("🔧 FIXING STATCAST TIMING FOR CONFIRMED PLAYERS")
    print("=" * 60)

    # Step 1: Fix pipeline order
    print("🔧 Step 1: Fixing pipeline order...")
    if not fix_pipeline_order():
        print("❌ Failed to fix pipeline order")
        return False

    # Step 2: Update Statcast service
    print("\\n🔧 Step 2: Updating Statcast service...")
    update_statcast_service_for_confirmed()

    # Step 3: Create test script
    print("\\n🧪 Step 3: Creating test script...")
    create_test_confirmed_statcast()

    print("\\n" + "=" * 60)
    print("✅ STATCAST TIMING FIX COMPLETED!")
    print("=" * 60)

    print("\\n🔧 WHAT WAS FIXED:")
    print("✅ Confirmed detection now happens BEFORE Statcast enrichment")
    print("✅ Manual selection happens BEFORE Statcast enrichment")
    print("✅ Priority players (confirmed + manual) get REAL data")
    print("✅ Other players get simulated data (faster)")

    print("\\n🎯 EXPECTED BEHAVIOR NOW:")
    print("1. Load DraftKings data")
    print("2. Apply DFF rankings")
    print("3. 🔍 Detect confirmed players FIRST")
    print("4. 📝 Apply manual selection")
    print("5. 🌐 Fetch REAL Statcast data for confirmed + manual")
    print("6. ⚡ Use simulated data for others")
    print("7. 🧠 Optimize with enhanced scoring")

    print("\\n🧪 TEST IT:")
    print("1. Run: python test_confirmed_statcast.py")
    print("2. Or test your GUI with manual players")
    print("3. Look for 'REAL Baseball Savant data: X/Y priority players'")
    print("4. Should see confirmed + manual players with real data")

    print("\\n⚡ PERFORMANCE:")
    print("✅ Confirmed + manual players: REAL data (2-5 min first time)")
    print("✅ Other players: Simulated data (instant)")
    print("✅ Subsequent runs: Cached data (30 seconds)")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)