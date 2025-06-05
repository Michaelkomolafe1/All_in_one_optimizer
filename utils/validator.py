#!/usr/bin/env python3
"""Data Validator for DFS Optimizer"""

from typing import List, Dict, Tuple

class DataValidator:
    @staticmethod
    def validate_players(players: List) -> Tuple[bool, List[str]]:
        """Validate player data integrity"""
        errors = []

        for i, player in enumerate(players):
            # Check required fields
            if not hasattr(player, 'name') or not player.name:
                errors.append(f"Player {i}: Missing name")

            if not hasattr(player, 'salary') or player.salary <= 0:
                errors.append(f"Player {i}: Invalid salary")

            if not hasattr(player, 'primary_position'):
                errors.append(f"Player {i}: Missing position")

            # Check data ranges
            if hasattr(player, 'enhanced_score'):
                if player.enhanced_score < 0 or player.enhanced_score > 100:
                    errors.append(f"Player {player.name}: Invalid score {player.enhanced_score}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_lineup(lineup: List, requirements: Dict) -> Tuple[bool, List[str]]:
        """Validate lineup meets requirements"""
        errors = []

        if not lineup:
            errors.append("Empty lineup")
            return False, errors

        # Check salary cap
        total_salary = sum(p.salary for p in lineup)
        if total_salary > 50000:
            errors.append(f"Over salary cap: ${total_salary:,}")

        # Check positions
        positions_filled = {}
        for player in lineup:
            pos = getattr(player, 'assigned_position', player.primary_position)
            positions_filled[pos] = positions_filled.get(pos, 0) + 1

        for pos, required in requirements.items():
            filled = positions_filled.get(pos, 0)
            if filled < required:
                errors.append(f"Missing {required - filled} {pos}")

        # Check for duplicates
        player_names = [p.name for p in lineup]
        if len(player_names) != len(set(player_names)):
            errors.append("Duplicate players in lineup")

        return len(errors) == 0, errors
