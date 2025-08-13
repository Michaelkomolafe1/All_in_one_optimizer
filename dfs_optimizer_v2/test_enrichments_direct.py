#!/usr/bin/env python3
"""
Simple test to check if enrichments are actually working
"""

import sys
sys.path.append('.')

def test_enrichments_directly():
    """Test enrichments directly without GUI"""

    print("🧪 DIRECT ENRICHMENT TEST")
    print("=" * 30)

    try:
        from data_pipeline_v2 import DFSPipeline

        # Create pipeline  
        pipeline = DFSPipeline()

        # Create test player
        from data_pipeline_v2 import Player
        test_player = Player(
            name="Test Player",
            position="OF", 
            team="LAD",
            salary=5000,
            projection=12.0
        )

        pipeline.all_players = [test_player]
        pipeline.player_pool = [test_player]

        print(f"✅ Created test player: {test_player.name}")

        # Test enrichment
        print("\n🔄 Running enrichment...")
        stats = pipeline.enrich_players("pitcher_dominance", "cash")
        print(f"Enrichment stats: {stats}")

        # Check enrichment results
        print(f"\n📊 ENRICHMENT RESULTS:")
        print(f"Name: {test_player.name}")
        print(f"Team Total: {getattr(test_player, 'implied_team_score', 'NOT SET')}")
        print(f"Game Total: {getattr(test_player, 'game_total', 'NOT SET')}")
        print(f"Confirmed: {getattr(test_player, 'confirmed', 'NOT SET')}")
        print(f"Barrel Rate: {getattr(test_player, 'barrel_rate', 'NOT SET')}")
        print(f"Consistency: {getattr(test_player, 'consistency_score', 'NOT SET')}")
        print(f"Optimization Score: {getattr(test_player, 'optimization_score', 'NOT SET')}")

        # Check if enrichments changed the score
        if hasattr(test_player, 'optimization_score'):
            if test_player.optimization_score != test_player.projection:
                print("✅ Enrichments ARE affecting scores!")
            else:
                print("⚠️ Enrichments may NOT be affecting scores")

        return True

    except Exception as e:
        print(f"❌ Direct test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_enrichments_directly()
