#!/usr/bin/env python3
"""
Minimal test for enrichment fixes
"""

import sys
sys.path.append('.')

def test_enrichment_fixes():
    """Test the specific fixes"""

    print("🧪 TESTING ENRICHMENT FIXES")
    print("=" * 30)

    try:
        from data_pipeline_v2 import DFSPipeline, Player

        # Create pipeline
        pipeline = DFSPipeline()

        # Create test player
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
        stats = pipeline.enrich_players("pitcher_dominance", "cash")

        print(f"📊 Stats returned: {stats}")
        print(f"📊 Stats type: {type(stats)}")

        # Check barrel rate specifically
        barrel_rate = getattr(test_player, 'barrel_rate', 'NOT SET')
        print(f"🎯 Barrel Rate: {barrel_rate}")

        if isinstance(stats, dict):
            print("✅ Method returns proper stats dictionary!")
        else:
            print("❌ Method still returning wrong type")

        if barrel_rate != 'NOT SET':
            print("✅ Barrel rate is being set!")
        else:
            print("❌ Barrel rate still not set")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_enrichment_fixes()
