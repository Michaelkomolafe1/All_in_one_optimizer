#!/usr/bin/env python3
"""
Unified Player Model - Consolidates all your best features
This replaces the multiple Player classes across your files
"""

import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime


class UnifiedPlayer:
    """
    Consolidated player model that combines all features from your various implementations
    - Multi-position support from working_dfs_core_final.py
    - Enhanced scoring from dfs_data_enhanced.py
    - Async compatibility from async_data_manager.py
    - Clean API from streamlined_dfs_optimizer.py
    """

    def __init__(self, data: Dict[str, Any]):
        # Core DraftKings data
        self.id = int(data.get('id', 0))
        self.name = str(data.get('name', '')).strip()
        self.positions = self._parse_positions(data.get('position', ''))
        self.primary_position = self.positions[0] if self.positions else 'UTIL'
        self.team = str(data.get('team', '')).strip().upper()
        self.salary = self._parse_salary(data.get('salary', 3000))
        self.projection = self._parse_float(data.get('projection', 0))
        self.game_info = str(data.get('game_info', ''))

        # Enhanced data sources (populated by integrations)
        self.dff_data = {}
        self.statcast_data = {}
        self.vegas_data = {}
        self.confirmed_data = {}

        # Status tracking
        self.is_confirmed = bool(data.get('is_confirmed', False))
        self.is_manual_selected = bool(data.get('is_manual_selected', False))
        self.batting_order = data.get('batting_order')

        # DFF specific fields
        self.dff_projection = self._parse_float(data.get('dff_projection', 0))
        self.dff_value_projection = self._parse_float(data.get('dff_value_projection', 0))
        self.dff_l5_avg = self._parse_float(data.get('dff_l5_avg', 0))
        self.dff_rank = data.get('dff_rank')
        self.confirmed_order = data.get('confirmed_order', '')

        # Vegas context
        self.implied_team_score = self._parse_float(data.get('implied_team_score', 4.5))
        self.over_under = self._parse_float(data.get('over_under', 8.5))

        # Performance tracking
        self.cache_timestamp = datetime.now()
        self.data_sources = []

        # Calculate scores
        self.base_score = self.projection if self.projection > 0 else (self.salary / 1000.0)
        self.enhanced_score = self.base_score
        self._calculate_enhanced_score()

    def _parse_positions(self, position_str: str) -> List[str]:
        """Parse multi-position strings like '3B/SS' or '1B/3B'"""
        if not position_str:
            return ['UTIL']

        position_str = str(position_str).strip().upper()

        # Handle multiple position formats
        for delimiter in ['/', ',', '-', '|', '+']:
            if delimiter in position_str:
                positions = [p.strip() for p in position_str.split(delimiter)]
                break
        else:
            positions = [position_str]

        # Validate and clean positions
        valid_positions = []
        valid_pos_set = {'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'DH', 'UTIL'}

        for pos in positions:
            pos = pos.strip()
            if pos in valid_pos_set:
                if pos not in valid_positions:
                    valid_positions.append(pos)

        return valid_positions if valid_positions else ['UTIL']

    def _parse_salary(self, salary_input: Any) -> int:
        """Parse salary from various input formats"""
        try:
            if isinstance(salary_input, (int, float)):
                return max(1000, int(salary_input))

            cleaned = str(salary_input).replace('$', '').replace(',', '').strip()
            return max(1000, int(float(cleaned))) if cleaned and cleaned != 'nan' else 3000
        except (ValueError, TypeError):
            return 3000

    def _parse_float(self, value: Any) -> float:
        """Parse float from various input formats"""
        try:
            if isinstance(value, (int, float)):
                return max(0.0, float(value))

            cleaned = str(value).strip()
            return max(0.0, float(cleaned)) if cleaned and cleaned not in ['nan', '', 'None'] else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _calculate_enhanced_score(self):
        """
        Calculate enhanced score using all available data sources
        Combines logic from all your optimizer implementations
        """
        score = self.base_score

        # DFF Enhancement (from dfs_data_enhanced.py logic)
        if self.dff_projection > 0:
            dff_boost = (self.dff_projection - self.projection) * 0.4
            score += dff_boost

        if self.dff_value_projection > 0:
            if self.dff_value_projection >= 2.0:
                score += 2.5
            elif self.dff_value_projection >= 1.8:
                score += 2.0
            elif self.dff_value_projection >= 1.6:
                score += 1.5

        # Recent form analysis
        if self.dff_l5_avg > 0 and self.projection > 0:
            recent_form_diff = self.dff_l5_avg - self.projection
            if recent_form_diff >= 3.0:
                score += 1.5
            elif recent_form_diff >= 1.5:
                score += 1.0
            elif recent_form_diff <= -1.5:
                score -= 1.0

        # Confirmed Status Bonus (from working_dfs_core_final.py)
        if self.confirmed_order and self.confirmed_order.upper() == 'YES':
            self.is_confirmed = True
            score += 2.5

            if self.batting_order and isinstance(self.batting_order, (int, float)):
                if 1 <= self.batting_order <= 3:
                    score += 2.0  # Top of order
                elif 4 <= self.batting_order <= 6:
                    score += 1.0  # Middle order

        # Manual Selection Bonus
        if self.is_manual_selected:
            score += 3.5

        # Vegas Context Enhancement
        if self.implied_team_score > 0:
            if self.primary_position == 'P':
                # For pitchers, lower opponent total is better
                opp_implied = self.over_under - self.implied_team_score if self.over_under > 0 else 4.5
                if opp_implied <= 3.5:
                    score += 2.5
                elif opp_implied <= 4.0:
                    score += 1.5
                elif opp_implied >= 5.5:
                    score -= 1.5
            else:
                # For hitters, higher team total is better
                if self.implied_team_score >= 5.5:
                    score += 2.5
                elif self.implied_team_score >= 5.0:
                    score += 2.0
                elif self.implied_team_score >= 4.5:
                    score += 1.0
                elif self.implied_team_score <= 3.5:
                    score -= 1.5

        # Statcast Enhancement
        if self.statcast_data:
            score += self._calculate_statcast_boost()

        # Ensure minimum score
        self.enhanced_score = max(1.0, score)

    def _calculate_statcast_boost(self) -> float:
        """Calculate boost from Statcast metrics"""
        boost = 0.0

        if self.primary_position == 'P':
            # Pitcher metrics
            hard_hit_against = self.statcast_data.get('Hard_Hit', 35.0)
            xwoba_against = self.statcast_data.get('xwOBA', 0.320)
            k_rate = self.statcast_data.get('K', 20.0)

            # Lower hard hit rate is better for pitchers
            if hard_hit_against <= 30.0:
                boost += 2.0
            elif hard_hit_against >= 50.0:
                boost -= 1.5

            # Lower xwOBA against is better for pitchers
            if xwoba_against <= 0.280:
                boost += 2.5
            elif xwoba_against >= 0.360:
                boost -= 2.0

            # Higher K rate is better for pitchers
            if k_rate >= 30.0:
                boost += 2.5
            elif k_rate >= 25.0:
                boost += 1.5
        else:
            # Hitter metrics
            hard_hit = self.statcast_data.get('Hard_Hit', 35.0)
            xwoba = self.statcast_data.get('xwOBA', 0.320)
            barrel_rate = self.statcast_data.get('Barrel', 6.0)

            # Higher hard hit rate is better for hitters
            if hard_hit >= 50.0:
                boost += 3.0
            elif hard_hit >= 45.0:
                boost += 2.0
            elif hard_hit <= 25.0:
                boost -= 1.5

            # Higher xwOBA is better for hitters
            if xwoba >= 0.400:
                boost += 3.0
            elif xwoba >= 0.370:
                boost += 2.5
            elif xwoba <= 0.280:
                boost -= 2.0

            # Higher barrel rate is better for hitters
            if barrel_rate >= 20.0:
                boost += 2.5
            elif barrel_rate >= 15.0:
                boost += 2.0

        return boost

    # Multi-position support methods
    def can_play_position(self, position: str) -> bool:
        """Check if player can play specific position"""
        return position in self.positions or position == 'UTIL'

    def is_multi_position(self) -> bool:
        """Check if player has multi-position eligibility"""
        return len(self.positions) > 1

    def get_position_flexibility(self) -> int:
        """Get number of positions player can play"""
        return len(self.positions)

    # Data integration methods
    def apply_dff_data(self, dff_data: Dict[str, Any]):
        """Apply DFF expert data"""
        self.dff_data = dff_data
        self.dff_projection = dff_data.get('ppg_projection', 0)
        self.dff_value_projection = dff_data.get('value_projection', 0)
        self.dff_l5_avg = dff_data.get('l5_fppg_avg', 0)
        self.dff_rank = dff_data.get('rank', 999)
        self.confirmed_order = dff_data.get('confirmed_order', '')
        self.implied_team_score = dff_data.get('implied_team_score', 4.5)
        self.over_under = dff_data.get('over_under', 8.5)

        self.data_sources.append('DFF')
        self._calculate_enhanced_score()

    def apply_statcast_data(self, statcast_data: Dict[str, Any]):
        """Apply Statcast/Baseball Savant data"""
        self.statcast_data = statcast_data
        self.data_sources.append('Statcast')
        self._calculate_enhanced_score()

    def apply_vegas_data(self, vegas_data: Dict[str, Any]):
        """Apply Vegas lines data"""
        self.vegas_data = vegas_data
        self.implied_team_score = vegas_data.get('implied_total', 4.5)
        self.over_under = vegas_data.get('over_under', 8.5)

        self.data_sources.append('Vegas')
        self._calculate_enhanced_score()

    def apply_confirmed_status(self, batting_order: Optional[int] = None):
        """Mark player as confirmed starter"""
        self.is_confirmed = True
        if batting_order is not None:
            self.batting_order = batting_order

        self.data_sources.append('Confirmed')
        self._calculate_enhanced_score()

    def apply_manual_selection(self):
        """Mark player as manually selected"""
        self.is_manual_selected = True
        self.data_sources.append('Manual')
        self._calculate_enhanced_score()

    # Utility methods
    def get_value_score(self) -> float:
        """Get points per $1000 salary"""
        return (self.enhanced_score / (self.salary / 1000.0)) if self.salary > 0 else 0.0

    def get_status_string(self) -> str:
        """Get human-readable status"""
        status_parts = []

        if self.is_confirmed:
            status_parts.append("CONFIRMED")
        if self.is_manual_selected:
            status_parts.append("MANUAL")
        if self.dff_projection > 0:
            status_parts.append(f"DFF:{self.dff_projection:.1f}")
        if 'Statcast' in self.data_sources:
            status_parts.append("STATCAST")
        if 'Vegas' in self.data_sources:
            status_parts.append("VEGAS")

        return " | ".join(status_parts) if status_parts else "BASIC"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'positions': self.positions,
            'primary_position': self.primary_position,
            'team': self.team,
            'salary': self.salary,
            'projection': self.projection,
            'enhanced_score': self.enhanced_score,
            'is_confirmed': self.is_confirmed,
            'is_manual_selected': self.is_manual_selected,
            'batting_order': self.batting_order,
            'dff_projection': self.dff_projection,
            'dff_value_projection': self.dff_value_projection,
            'implied_team_score': self.implied_team_score,
            'data_sources': self.data_sources,
            'status': self.get_status_string()
        }

    def __repr__(self):
        """String representation"""
        pos_str = '/'.join(self.positions) if len(self.positions) > 1 else self.primary_position
        status_str = f" [{self.get_status_string()}]" if self.data_sources else ""

        return (f"UnifiedPlayer({self.name}, {pos_str}, {self.team}, "
                f"${self.salary}, {self.enhanced_score:.1f}{status_str})")

    def __eq__(self, other):
        """Equality comparison"""
        if not isinstance(other, UnifiedPlayer):
            return False
        return self.id == other.id and self.name == other.name

    def __hash__(self):
        """Hash for use in sets/dicts"""
        return hash((self.id, self.name, self.team))


# Factory function to convert from existing player formats
def create_unified_player(existing_player) -> UnifiedPlayer:
    """
    Convert from any of your existing player formats to UnifiedPlayer
    Works with list format from working_dfs_core_final.py or dict format
    """
    if isinstance(existing_player, list):
        # Convert from list format [id, name, position, team, salary, projection, score, ...]
        data = {
            'id': existing_player[0] if len(existing_player) > 0 else 0,
            'name': existing_player[1] if len(existing_player) > 1 else '',
            'position': existing_player[2] if len(existing_player) > 2 else '',
            'team': existing_player[3] if len(existing_player) > 3 else '',
            'salary': existing_player[4] if len(existing_player) > 4 else 3000,
            'projection': existing_player[5] if len(existing_player) > 5 else 0,
            'batting_order': existing_player[7] if len(existing_player) > 7 else None,
        }

        # Check for extended data
        if len(existing_player) > 14 and existing_player[14]:
            data['statcast_data'] = existing_player[14]
        if len(existing_player) > 15 and existing_player[15]:
            data['vegas_data'] = existing_player[15]

    elif hasattr(existing_player, '__dict__'):
        # Convert from object format
        data = existing_player.__dict__.copy()
    else:
        # Assume it's already a dict
        data = existing_player

    return UnifiedPlayer(data)


# Example usage and testing
if __name__ == "__main__":
    # Test the unified player model
    test_data = {
        'id': 1,
        'name': 'Jorge Polanco',
        'position': '3B/SS',  # Multi-position
        'team': 'SEA',
        'salary': 4500,
        'projection': 7.9
    }

    player = UnifiedPlayer(test_data)
    print(f"Created: {player}")
    print(f"Can play 3B: {player.can_play_position('3B')}")
    print(f"Can play SS: {player.can_play_position('SS')}")
    print(f"Is multi-position: {player.is_multi_position()}")
    print(f"Position flexibility: {player.get_position_flexibility()}")

    # Test DFF integration
    dff_data = {
        'ppg_projection': 8.5,
        'value_projection': 1.8,
        'confirmed_order': 'YES'
    }

    player.apply_dff_data(dff_data)
    print(f"After DFF: {player}")
    print(f"Enhanced score: {player.enhanced_score:.2f}")
    print(f"Status: {player.get_status_string()}")