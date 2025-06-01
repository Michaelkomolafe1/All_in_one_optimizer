#!/usr/bin/env python3
"""
UPGRADED DFS Core - Now with REAL Statcast Data
All your existing functionality + real Baseball Savant data integration
"""

# Import everything from your existing core
from optimized_dfs_core import *

# Import real Statcast integration
try:
    from working_real_statcast_fetcher import WorkingRealStatcastFetcher, RealStatcastFetcher
    from integrate_real_statcast import EnhancedStatcastService
    REAL_STATCAST_AVAILABLE = True
    print("🔬 UPGRADED: Real Statcast data integration enabled")
except ImportError:
    REAL_STATCAST_AVAILABLE = False
    print("⚠️ Real Statcast files not found - using existing simulation")


class UpgradedDFSCore(OptimizedDFSCore):
    """
    Upgraded version of your DFS core with real Statcast data
    All existing functionality preserved + real Baseball Savant data
    """

    def __init__(self):
        # Initialize with your existing logic
        super().__init__()

        # Add enhanced Statcast service
        if REAL_STATCAST_AVAILABLE:
            self.enhanced_statcast_service = EnhancedStatcastService(
                use_real_data=True,
                priority_only=True  # Real data for confirmed/manual players only
            )
            print("🚀 UpgradedDFSCore: Real Statcast integration active")
        else:
            self.enhanced_statcast_service = None
            print("⚡ UpgradedDFSCore: Using existing simulation")

    def enrich_with_statcast(self):
        """
        UPGRADED: Enhanced Statcast enrichment with real data
        This replaces your existing method but maintains compatibility
        """

        if self.enhanced_statcast_service and REAL_STATCAST_AVAILABLE:
            print("🔬 Using REAL Baseball Savant data for Statcast enrichment...")

            # Use real data service
            self.players = self.enhanced_statcast_service.enrich_players_with_statcast(self.players)

            # Show statistics
            real_count = sum(1 for p in self.players 
                           if hasattr(p, 'statcast_data') and 
                           'Baseball Savant' in p.statcast_data.get('data_source', ''))

            total_count = len(self.players)
            sim_count = total_count - real_count

            print(f"🎉 REAL STATCAST ENRICHMENT COMPLETE!")
            print(f"   🌐 Real Baseball Savant data: {real_count}/{total_count}")
            print(f"   ⚡ Enhanced simulation: {sim_count}/{total_count}")
            print(f"   📈 Real data coverage: {(real_count/total_count*100):.1f}%")

        else:
            # Fall back to your existing method
            print("⚡ Using existing Statcast simulation...")
            super().enrich_with_statcast()


def upgraded_pipeline_with_real_statcast(
    dk_file: str,
    dff_file: str = None,
    manual_input: str = "",
    contest_type: str = 'classic',
    strategy: str = 'smart_confirmed'
):
    """
    UPGRADED: Your existing pipeline now with real Statcast data
    Drop-in replacement for load_and_optimize_complete_pipeline
    """

    print("🚀 UPGRADED DFS PIPELINE WITH REAL STATCAST DATA")
    print("=" * 70)

    # Use upgraded core instead of original
    core = UpgradedDFSCore()

    # Step 1: Load DraftKings data (same as before)
    print("📊 Step 1: Loading DraftKings data...")
    if not core.load_draftkings_csv(dk_file):
        return [], 0, "Failed to load DraftKings data"

    # Step 2: Apply DFF rankings if provided (same as before)
    if dff_file:
        print("🎯 Step 2: Applying DFF rankings...")
        core.apply_dff_rankings(dff_file)

    # Step 3: Apply manual selection if provided (same as before)
    if manual_input:
        print("🎯 Step 3: Applying manual selection...")
        core.apply_manual_selection(manual_input)

    # Step 4: UPGRADED - Enhanced Statcast enrichment with REAL data
    print("🔬 Step 4: Enriching with REAL Statcast data...")
    core.enrich_with_statcast()  # Now uses real data!

    # Step 5: Optimize lineup (same as before)
    print("🧠 Step 5: Running optimization...")
    lineup, score = core.optimize_lineup(contest_type, strategy)

    if lineup:
        summary = core.get_lineup_summary(lineup, score)

        # Add upgrade info to summary
        if REAL_STATCAST_AVAILABLE:
            real_count = sum(1 for p in lineup 
                           if hasattr(p, 'statcast_data') and 
                           'Baseball Savant' in p.statcast_data.get('data_source', ''))

            upgrade_info = f"""

🔬 STATCAST DATA UPGRADE:
   🌐 Real Baseball Savant data: {real_count}/{len(lineup)} players
   ⚡ Enhanced simulation: {len(lineup) - real_count}/{len(lineup)} players
   🎉 Your optimizer now uses REAL MLB data!"""

            summary += upgrade_info

        print("✅ UPGRADED optimization complete with real Statcast data!")
        return lineup, score, summary
    else:
        return [], 0, "Optimization failed"


# Make the upgraded pipeline available as the default
load_and_optimize_complete_pipeline = upgraded_pipeline_with_real_statcast

if __name__ == "__main__":
    print("🔬 UPGRADED DFS CORE WITH REAL STATCAST DATA")
    print("=" * 60)
    print("✅ All existing functionality preserved")
    print("🔬 Added: Real Baseball Savant data integration")
    print("🎯 Smart: Real data for priority players, simulation for others")
    print("⚡ Fast: Cached data for subsequent runs")
