#!/usr/bin/env python3
"""Test strategy integration"""

import sys
import os

# Fix paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_strategy_imports():
    """Test that strategies can be imported"""
    from strategies.cash_strategies import build_projection_monster
    from strategies.gpp_strategies import build_truly_smart_stack
    print("✅ Strategy imports successful!")
    assert build_projection_monster is not None
    assert build_truly_smart_stack is not None


def test_system_initialization():
    """Test that core system initializes"""
    from core.unified_core_system import UnifiedCoreSystem
    system = UnifiedCoreSystem()
    print("✅ System initialized!")
    assert system is not None


def test_strategy_application():
    """Test applying a strategy to mock players"""
    from strategies.gpp_strategies import build_truly_smart_stack
    from core.unified_player_model import UnifiedPlayer

    # Create mock players with required arguments
    mock_players = []
    for i in range(10):
        player = UnifiedPlayer(
            id=f"player_{i}",
            name=f"Player{i}",
            team="NYY" if i < 5 else "BOS",
            salary=5000 + (i * 100),
            primary_position="OF" if i % 2 == 0 else "1B",
            positions=["OF"] if i % 2 == 0 else ["1B"]
        )
        # Set additional attributes
        player.projection = 10 + i
        player.game_total = 9.5
        player.ceiling = player.projection * 1.5
        mock_players.append(player)

    # Apply strategy
    updated = build_truly_smart_stack(mock_players)
    print("✅ Strategy applied successfully!")
    assert len(updated) == len(mock_players)

    # Verify optimization scores were set
    for player in updated:
        assert hasattr(player, 'optimization_score')
        assert player.optimization_score > 0