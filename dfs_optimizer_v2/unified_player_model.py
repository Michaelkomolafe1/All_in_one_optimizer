#!/usr/bin/env python3
"""
Unified Player Model - Clean Working Version
"""

from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class UnifiedPlayer:
    """Unified player model for DFS optimization"""

    def __init__(self, name: str, position: str, team: str, salary: int,
                 opponent: str = '', player_id: str = '', base_projection: float = 0.0):
        """Initialize a unified player"""
        # Core attributes
        self.name = name
        self.position = position
        # Normalize pitcher positions for optimizer
        if position in ['SP', 'RP']:
            self.primary_position = 'P'  # Normalize for MILP
            self.original_position = position  # Keep original
        else:
            self.primary_position = position.split('/')[0] if '/' in position else position
            self.original_position = position

        # Also set position attribute
        self.position = position  # Keep original for display
        self.team = team
        self.opponent = opponent
        self.salary = max(salary, 1)  # Avoid zero salary
        self.player_id = player_id or f"{name}_{team}".lower().replace(' ', '_')

        # Projections and scoring
        self.base_projection = float(base_projection) if base_projection else 0.0
        self.projection = self.base_projection
        self.optimization_score = self.base_projection
        self.enhanced_score = self.base_projection

        # Status flags
        # Position type flag
        self.is_pitcher = position in ['P', 'SP', 'RP'] if position else False

        self.is_confirmed = False
        self.is_manual_selected = False
        self.in_lineup = False

        # Additional data
        self.batting_order = 0
        self.ownership_projection = 0.0
        self.implied_team_score = 0.0
        self.recent_form = 0.0
        self.consistency_score = 0.0
        self.statcast_metrics = {}

        # Calculate initial scores
        self.calculate_data_quality()

    @classmethod
    def from_csv_row(cls, row: Dict) -> 'UnifiedPlayer':
        """Create UnifiedPlayer from DraftKings CSV row"""
        # Extract basic info
        name = row.get('Name', row.get('name', ''))
        position = row.get('Position', row.get('Pos', ''))
        team = row.get('TeamAbbrev', row.get('Team', ''))

        # Handle salary
        salary = 0
        salary_str = row.get('Salary', '0')
        if salary_str:
            try:
                salary = int(str(salary_str).replace('$', '').replace(',', ''))
            except:
                salary = 5000  # Default salary

        # Parse opponent from game info
        opponent = ''
        game_info = row.get('Game Info', row.get('GameInfo', ''))
        if game_info and '@' in game_info:
            teams = game_info.split('@')
            if team == teams[0].strip():
                opponent = teams[1].strip().split()[0]
            else:
                opponent = teams[0].strip()

        # Get projection - try multiple field names
        base_projection = 0.0
        projection_fields = ['AvgPointsPerGame', 'projection', 'Projection',
                             'avg_points', 'points', 'fantasy_points']

        for field in projection_fields:
            if field in row and row[field]:
                try:
                    val = float(row[field])
                    if val > 0:
                        base_projection = val
                        break
                except:
                    continue

        # Create player ID
        player_id = row.get('ID', f"{name}_{team}".lower().replace(' ', '_'))

        # Create player
        return cls(
            name=name,
            position=position,
            team=team,
            salary=salary,
            opponent=opponent,
            player_id=player_id,
            base_projection=base_projection
        )

    def calculate_data_quality(self):
        """Calculate data quality score"""
        self.data_quality = 0

        if self.base_projection > 0:
            self.data_quality += 1
        if self.batting_order > 0:
            self.data_quality += 1
        if self.implied_team_score > 0:
            self.data_quality += 1
        if self.recent_form != 0:
            self.data_quality += 1
        if self.statcast_metrics:
            self.data_quality += 1

    def calculate_optimization_score(self, contest_type: str = 'gpp'):
        """Calculate optimization score based on contest type"""
        # Ensure we have valid base values
        if self.base_projection is None or self.base_projection == 0:
            self.optimization_score = 0.0
            return

        # Start with base projection
        score = self.base_projection

        # Apply contest-specific adjustments
        if contest_type == 'cash':
            # Cash game - emphasize floor and consistency
            if self.consistency_score > 0:
                score *= (1 + self.consistency_score * 0.1)
            if self.batting_order > 0 and self.batting_order <= 5:
                score *= 1.05
        else:
            # GPP - emphasize ceiling and leverage
            if self.ownership_projection > 0 and self.ownership_projection < 15:
                score *= 1.1
            if self.implied_team_score > 5.0:
                score *= 1.15

        self.optimization_score = score

    def calculate_enhanced_score(self):
        """Calculate enhanced score with all factors"""
        # Safety check
        if self.optimization_score is None:
            self.optimization_score = self.base_projection or 0.0

        # Start with optimization score
        score = self.optimization_score

        # Apply enhancements
        if self.is_confirmed:
            score *= 1.05
        if self.batting_order > 0:
            order_boost = max(0, (10 - self.batting_order) * 0.02)
            score *= (1 + order_boost)
        if self.recent_form > 0:
            score *= (1 + self.recent_form * 0.05)

        self.enhanced_score = score

    @property
    def value(self) -> float:
        """Points per thousand dollars"""
        if self.salary <= 0:
            return 0.0
        return (self.base_projection / self.salary) * 1000

    @property
    def display_name(self) -> str:
        """Display name with team"""
        return f"{self.name} ({self.team})"

    def __str__(self) -> str:
        return f"{self.name} {self.position} ${self.salary} ({self.base_projection:.1f} pts)"

    def __repr__(self) -> str:
        return f"UnifiedPlayer('{self.name}', '{self.position}', ${self.salary})"

    @property
    def safe_optimization_score(self):
        """Never return None - always return a valid score"""
        if self.optimization_score is not None:
            return self.optimization_score
        if hasattr(self, 'gpp_score') and self.gpp_score is not None:
            return self.gpp_score
        if hasattr(self, 'cash_score') and self.cash_score is not None:
            return self.cash_score
        if self.base_projection is not None:
            return self.base_projection
        if hasattr(self, 'projection') and self.projection is not None:
            return self.projection
        return 10.0  # Last resort

    @property
    def safe_base_projection(self):
        """Safe getter for base projection"""
        if self.base_projection is not None:
            return self.base_projection
        if hasattr(self, 'projection') and self.projection is not None:
            return self.projection
        # Position-based defaults
        pos_defaults = {
            'P': 15.0, 'C': 8.0, '1B': 10.0,
            '2B': 9.0, '3B': 9.0, 'SS': 9.0, 'OF': 9.0
        }
        return pos_defaults.get(self.position, 8.0)

    @property
    def safe_salary(self):
        """Safe getter for salary"""
        if self.salary is not None and self.salary > 0:
            return self.salary
        return 3000  # Minimum DK salary