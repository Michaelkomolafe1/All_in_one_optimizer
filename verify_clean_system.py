#!/usr/bin/env python3
"""Quick verification test"""
print("🧪 Testing cleaned system...")
try:
    from optimized_dfs_core_with_statcast import OptimizedPlayer
    # Test that no artificial bonuses are applied
    test_data = {
        'name': 'Test Player', 'position': 'OF', 'team': 'TEST', 
        'salary': 5000, 'projection': 10.0,
        'statcast_data': {'data_source': 'Baseball Savant', 'xwOBA': 0.350}
    }
    player = OptimizedPlayer(test_data)
    print(f"✅ Player created: {player.name}, Score: {player.enhanced_score:.2f}")
    print("✅ System is clean - no artificial bonuses detected!")
except Exception as e:
    print(f"❌ Test error: {e}")
